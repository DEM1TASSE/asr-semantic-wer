"""System-level comparison of ASR systems on the 700 AMI test utterances (test + test_extra).

Per system: WER, student Semantic-WER (hard / lin / max), and training-free sentence-level semantic
metrics on the full normalized hypothesis vs the normalized reference:
  * BERTScore distance : mean of 1 - F1 (roberta-large, rescaled)
  * SemDist            : mean of 1 - cosine (all-mpnet-base-v2)
95% CIs by bootstrap over utterances (same resampled utterances for every system, so ranks are paired).

Usage:
  HF_HOME=~/semwer-local-cpu/model-cache python src/system_baselines.py \
      --qwen-dir ~/semwer-qwen-eval --spans ~/semwer-qwen-eval/spans_five_systems.jsonl \
      --student ~/semwer-qwen-eval/student_predictions_five_systems.jsonl
Outputs: outputs/baselines/system_utterances.jsonl, outputs/baselines/system_metrics.json
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, OUT, normalize  # noqa: E402
from semantic_baselines import bertscore, semdist  # noqa: E402

BASE = OUT / "baselines"
REPO_SYSTEMS = ["parakeet-tdt-0.6b-v2", "whisper-large-v3", "wav2vec2-large"]


def read_jsonl(p):
    return [json.loads(l) for l in open(p)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qwen-dir", type=Path, required=True)
    ap.add_argument("--qwen", nargs="+", default=["qwen3-asr-0.6b", "qwen3-asr-1.7b"])
    ap.add_argument("--spans", type=Path, required=True, help="aligned spans for all systems (error_id, n_word_errors)")
    ap.add_argument("--student", type=Path, required=True, help="student predictions (error_id, severity)")
    ap.add_argument("--bs", type=int, default=32)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--recompute", action="store_true")
    args = ap.parse_args()
    BASE.mkdir(exist_ok=True)

    # Normalize raw text here with common.normalize, exactly as the WER / span alignment did
    # (the stored ref_norm / hyp_norm fields predate the final normalization fixes).
    refs = {}
    for f in ["eval_subset.jsonl", "subset_test_extra.jsonl"]:
        refs.update({r["audio_id"]: normalize(r["ref"]) for r in read_jsonl(DATA / f)})
    ids = sorted(refs)
    hyps = {}
    for s in REPO_SYSTEMS:
        for sfx in ["", "_test_extra"]:
            for r in read_jsonl(OUT / f"hyp_{s}{sfx}.jsonl"):
                hyps[(s, r["audio_id"])] = normalize(r["hyp"])
    for s in args.qwen:
        for sub in ["test", "test_extra"]:
            for r in read_jsonl(args.qwen_dir / f"hyp_{s}_{sub}.jsonl"):
                hyps[(s, r["audio_id"])] = normalize(r["hyp"])
    systems = REPO_SYSTEMS + args.qwen
    for s in systems:
        n = sum((s, a) in hyps for a in ids)
        assert n == len(ids), f"{s}: {n}/{len(ids)} hypotheses"

    cache = BASE / "system_utterances.jsonl"
    cached = {(r["system"], r["audio_id"]): r for r in read_jsonl(cache)} if cache.exists() and not args.recompute else {}
    todo = [(s, a) for s in systems for a in ids if (s, a) not in cached]
    if todo:
        R = [refs[a] for _, a in todo]
        H = [hyps[k] or "∅" for k in todo]
        b, d = bertscore(R, H, args.bs), semdist(R, H, args.bs)
        for k, (s, a) in enumerate(todo):
            cached[(s, a)] = {"system": s, "audio_id": a, "ref": refs[a], "hyp": hyps[(s, a)],
                              "bertscore": float(b[k]), "semdist": float(d[k])}
        with open(cache, "w") as f:
            for k in sorted(cached):
                f.write(json.dumps(cached[k], ensure_ascii=False) + "\n")

    # per-utterance edit counts and severity-weighted edits from the student
    sev = {r["error_id"]: r["severity"] for r in read_jsonl(args.student)}
    per = defaultdict(lambda: {"edits": 0, "hard": 0.0, "lin": 0.0, "worst": 0.0})
    for e in read_jsonl(args.spans):
        s, a, n = e["system"], e["audio_id"], e["n_word_errors"]
        if s not in systems:
            continue
        x = sev[e["error_id"]]
        u = per[(s, a)]
        u["edits"] += n
        u["hard"] += n * (x - 1) / 4
        u["lin"] += n * x / 5
        u["worst"] = max(u["worst"], (x - 1) / 4)

    nref = np.array([len(refs[a].split()) for a in ids], float)
    M = {}
    for s in systems:
        g = lambda f: np.array([per[(s, a)][f] for a in ids], float)  # noqa: E731
        M[s] = {"edits": g("edits"), "hard": g("hard"), "lin": g("lin"), "worst": g("worst"),
                "bertscore": np.array([cached[(s, a)]["bertscore"] for a in ids]),
                "semdist": np.array([cached[(s, a)]["semdist"] for a in ids])}

    def stats(m, idx):
        return {"wer": m["edits"][idx].sum() / nref[idx].sum(),
                "semwer_hard": m["hard"][idx].sum() / nref[idx].sum(),
                "semwer_lin": m["lin"][idx].sum() / nref[idx].sum(),
                "semwer_max": m["worst"][idx].mean(),
                "bertscore_dist": m["bertscore"][idx].mean(),
                "semdist": m["semdist"][idx].mean()}

    full = np.arange(len(ids))
    point = {s: stats(M[s], full) for s in systems}
    rng = np.random.default_rng(751)
    boots = defaultdict(list)
    for _ in range(args.boot):
        idx = rng.integers(0, len(ids), len(ids))
        for s in systems:
            for k, v in stats(M[s], idx).items():
                boots[(s, k)].append(v)
    keys = list(point[systems[0]])
    out = {"n_utts": len(ids), "n_ref_words": int(nref.sum()), "bootstrap": args.boot, "systems": {}, "ranks": {}}
    for s in systems:
        out["systems"][s] = {k: {"value": float(point[s][k]),
                                 "ci95": [float(np.percentile(boots[(s, k)], 2.5)), float(np.percentile(boots[(s, k)], 97.5))]}
                             for k in keys}
    for k in keys:
        out["ranks"][k] = sorted(systems, key=lambda s: point[s][k])
    # paired bootstrap: fraction of resamples where system A is better (lower) than B, per metric
    pairs = {}
    for k in keys:
        for i, a in enumerate(systems):
            for b in systems[i + 1:]:
                pa, pb = np.array(boots[(a, k)]), np.array(boots[(b, k)])
                pairs[f"{k}: {a} < {b}"] = float((pa < pb).mean())
    out["paired_bootstrap_p_lower"] = pairs
    (BASE / "system_metrics.json").write_text(json.dumps(out, indent=2) + "\n")

    hdr = f"{'system':22s}" + "".join(f"{k:>24s}" for k in keys)
    print(hdr)
    for s in systems:
        row = out["systems"][s]
        print(f"{s:22s}" + "".join(f"{100*row[k]['value']:8.2f} [{100*row[k]['ci95'][0]:5.2f},{100*row[k]['ci95'][1]:5.2f}]" for k in keys))
    print("\nranks (best first):")
    for k, r in out["ranks"].items():
        print(f"  {k:15s} " + " < ".join(r))


if __name__ == "__main__":
    main()
