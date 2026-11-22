import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

ROOT = Path(__file__).resolve().parent
SOURCE = Path("/tmp/asr-semwer-ta-20261118")
STUDENT = Path.home() / "semwer-local-cpu"
sys.path.insert(0, str(STUDENT / "src"))
from train_severity import evaluate, metrics, text_of


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def main():
    key = sys.argv[1] if len(sys.argv) > 1 else "four_systems"
    systems = json.loads((ROOT / f"asr_{key}.json").read_text())
    spans = read_jsonl(ROOT / f"spans_{key}.jsonl")
    checkpoint = STUDENT / "runs/ordinal/seed_751/best"
    model = AutoModelForSequenceClassification.from_pretrained(checkpoint)
    tokenizer = AutoTokenizer.from_pretrained(checkpoint)
    torch.set_num_threads(6)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = model.to(device)
    pairs = pd.DataFrame([text_of(error) for error in spans], columns=["ctx", "tgt"])
    scores = evaluate(model, tokenizer, pairs, torch.device(device), 32, "ordinal")
    assertions = np.isfinite(scores).all() and (scores >= 1).all() and (scores <= 5).all()
    if len(scores) != len(spans) or not assertions:
        raise ValueError("Invalid checkpoint predictions")
    annotations = {row["error_id"]: row for row in read_jsonl(SOURCE / "outputs/llm_annotations_deepseek-v4-1-flash_v2.4.jsonl")}
    original = {
        row["error_id"]: row
        for filename in ("errors.jsonl", "errors_test_extra.jsonl")
        for row in read_jsonl(SOURCE / "outputs" / filename)
    }
    pairs_by_system = defaultdict(list)
    predictions = defaultdict(list)
    rounded_counts = defaultdict(Counter)
    with (ROOT / f"student_predictions_{key}.jsonl").open("w") as stream:
        for error, score in zip(spans, scores):
            system, aid, eid = error["system"], error["audio_id"], error["error_id"]
            n_errors = error["n_word_errors"]
            predictions[system].append((aid, n_errors, score))
            rounded_counts[system][round(score)] += 1
            label = annotations.get(eid, {})
            old = original.get(eid, {})
            same_span = all(old.get(field) == error[field] for field in ("ref", "hyp", "ref_marked", "ref_start", "ref_end", "hyp_span"))
            teacher = label.get("severity") if same_span and "ref_issue" not in (label.get("flag") or []) else None
            if teacher is not None:
                pairs_by_system[system].append((score, teacher))
            stream.write(json.dumps({"system": system, "audio_id": aid, "error_id": eid,
                                     "severity": score, "teacher_severity": teacher}) + "\n")
    result = {}
    for system, asr in systems.items():
        entries = predictions[system]
        worst = defaultdict(float)
        for aid, _, score in entries:
            worst[aid] = max(worst[aid], (score - 1) / 4)
        result[system] = {
            "student_semwer_lin": sum(n * score / 5 for _, n, score in entries) / asr["n_ref_words"],
            "student_semwer_hard": sum(n * (score - 1) / 4 for _, n, score in entries) / asr["n_ref_words"],
            "student_semwer_max": sum(worst.values()) / asr["n_utts"],
            "rounded_severity_counts": dict(sorted(rounded_counts[system].items())),
        }
        if pairs_by_system[system]:
            pred, gold = np.asarray(pairs_by_system[system]).T
            result[system]["teacher_agreement_on_matching_spans"] = metrics(pred, gold)
    (ROOT / f"student_{key}.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
