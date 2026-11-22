import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

import jiwer

from transcribe import ROOT, SOURCE, SPLITS, SYSTEM, normalize
from align import MODEL_IDS, SYSTEMS, extract_spans


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def indexed(rows, key):
    by_key = {row[key]: row for row in rows}
    if len(by_key) != len(rows):
        raise ValueError(f"Duplicate {key}")
    return by_key


def write_jsonl(path, rows):
    with path.open("w") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")


def evaluate(systems, delta_qwen_dir=None):
    rows = defaultdict(list)
    all_spans = []
    raw_counts = defaultdict(lambda: {"empty_normalized_hypotheses": 0, "n_error_spans": 0})
    for subset, manifest in SPLITS.items():
        refs_by_id = indexed(read_jsonl(SOURCE / "data" / f"{manifest}.jsonl"), "audio_id")
        ids = list(refs_by_id)
        refs = [normalize(refs_by_id[aid]["ref"]) for aid in ids]
        for system in systems:
            suffix = "" if subset == "test" else f"_{subset}"
            path = SOURCE / "outputs" / f"hyp_{system}{suffix}.jsonl"
            if system.startswith("qwen3-asr-"):
                if delta_qwen_dir is None:
                    path = ROOT / f"hyp_{system}_{subset}.jsonl"
                else:
                    delta_subset = "ami-test" if subset == "test" else "ami-test-extra"
                    path = delta_qwen_dir / f"hyp_{system}_{delta_subset}.jsonl"
            hypotheses = indexed(read_jsonl(path), "audio_id")
            if set(hypotheses) != set(ids):
                raise ValueError(f"{system} {subset}: expected {len(ids)} utterances, got {len(hypotheses)}")
            hyps = [normalize(hypotheses[aid]["hyp"]) for aid in ids]
            words = jiwer.process_words(refs, hyps)
            for index, aid in enumerate(ids):
                meta = refs_by_id[aid]
                record = hypotheses[aid]
                spans = extract_spans(words.references[index], words.hypotheses[index], words.alignments[index])
                raw_counts[system]["empty_normalized_hypotheses"] += int(not hyps[index])
                raw_counts[system]["n_error_spans"] += len(spans)
                all_spans.extend({
                    "error_id": f"{system}|{aid}|{j}", "subset": subset, "system": system,
                    "model_id": record.get("model_id", MODEL_IDS.get(system)), "audio_id": aid, "meeting_id": meta["meeting_id"],
                    "speaker_id": meta.get("speaker_id"), "ref": refs[index], "hyp": hyps[index],
                    "ref_raw": meta.get("ref_raw", meta["ref"]), "hyp_raw": record["hyp"],
                    "context_before": meta["context_before"], "context_after": meta["context_after"],
                    **span,
                } for j, span in enumerate(spans))
                rows[system].append((refs[index], hyps[index]))
    summary = {}
    for system, pairs in rows.items():
        ref, hyp = map(list, zip(*pairs))
        words = jiwer.process_words(ref, hyp)
        chars = jiwer.process_characters([x.replace(" ", "") for x in ref], [x.replace(" ", "") for x in hyp])
        summary[system] = {
            "n_utts": len(ref), "n_ref_words": sum(len(x.split()) for x in ref),
            "n_ref_chars_excluding_spaces": sum(len(x.replace(" ", "")) for x in ref),
            "word_substitutions": words.substitutions, "word_deletions": words.deletions,
            "word_insertions": words.insertions, "wer": words.wer, "cer": chars.cer, **raw_counts[system],
        }
        assert math.isclose(words.wer, (words.substitutions + words.deletions + words.insertions) / summary[system]["n_ref_words"])
        assert sum(e["n_word_errors"] for e in all_spans if e["system"] == system) == (words.substitutions + words.deletions + words.insertions)
    return summary, all_spans


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baselines", action="store_true")
    parser.add_argument("--include-1.7b", action="store_true", dest="include_large")
    parser.add_argument("--delta-qwen-dir", type=Path)
    args = parser.parse_args()
    systems = SYSTEMS if args.baselines else [*SYSTEMS, SYSTEM]
    if args.include_large:
        systems = [*systems, "qwen3-asr-1.7b"]
    summary, spans = evaluate(systems, args.delta_qwen_dir)
    name = "five_systems" if args.include_large else "baselines" if args.baselines else "four_systems"
    (ROOT / f"asr_{name}.json").write_text(json.dumps(summary, indent=2) + "\n")
    write_jsonl(ROOT / f"spans_{name}.jsonl", spans)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
