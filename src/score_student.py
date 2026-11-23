"""Score error spans with the trained student (ordinal DistilBERT from Hugging Face).

Same input as in training (src/train_severity_cpu.py: text_of). Writes one line per span with the
student severity and, where available, the teacher severity (ref_issue spans get teacher_severity null).
Usage: pixi run python src/score_student.py --subsets test test_extra
Output: outputs/student_predictions_<subsets>.jsonl
"""
import argparse
import json

import pandas as pd
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from common import OUT, load_errors
from train_severity_cpu import evaluate, text_of

MODEL = "yixiang666/asr-semantic-severity-distilbert"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subsets", nargs="+", default=["test", "test_extra"])
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--tag", default="deepseek-v4-1-flash_v2.4")
    args = ap.parse_args()

    errors = list(load_errors(args.subsets).values())
    labels = {r["error_id"]: r for r in map(json.loads, open(OUT / f"llm_annotations_{args.tag}.jsonl"))}
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSequenceClassification.from_pretrained(args.model)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    frame = pd.DataFrame([text_of(e) for e in errors], columns=["ctx", "tgt"])
    scores = evaluate(model, tok, frame, device, 64, "ordinal")
    out = OUT / f"student_predictions_{'+'.join(args.subsets)}.jsonl"
    with open(out, "w") as f:
        for e, s in zip(errors, scores):
            lab = labels.get(e["error_id"])
            teacher = lab["severity"] if lab and "ref_issue" not in lab["flag"] else None
            f.write(json.dumps({"error_id": e["error_id"], "system": e["system"], "audio_id": e["audio_id"],
                                "severity": float(s), "teacher_severity": teacher}) + "\n")
    print(f"wrote {len(errors)} predictions to {out}")


if __name__ == "__main__":
    main()
