"""Training-free semantic baselines (BERTScore, SemDist) vs the DistilBERT student.

Span level: each error span is scored by comparing the reference with the single-error ASR sentence
(`common.single_error_hyp`), so the baselines see exactly what the teacher and the student judge.
  * BERTScore  : 1 - F1(ref, single_error_hyp), roberta-large, rescaled with the official baseline.
  * SemDist    : 1 - cosine(SBERT(ref), SBERT(single_error_hyp)), all-mpnet-base-v2.
  * span length: number of word edits in the span (what plain WER implicitly uses).
Raw scores are compared by Spearman (no fitting). For QWK / MAE / within-1 each baseline is mapped to the
1-5 scale by isotonic regression fit on dev_balanced (teacher labels); the student needs no mapping.

Usage:
  HF_HOME=~/semwer-local-cpu/model-cache python src/semantic_baselines.py \
      --student ~/semwer-qwen-eval/student_predictions_four_systems.jsonl
Outputs: outputs/baselines/span_scores.jsonl, outputs/baselines/span_metrics.json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import cohen_kappa_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, OUT, ROOT, load_errors, single_error_hyp  # noqa: E402

TEACHER = OUT / "llm_annotations_deepseek-v4-1-flash_v2.4.jsonl"
BASE = OUT / "baselines"
SYSTEMS = ["whisper-large-v3", "wav2vec2-large", "parakeet-tdt-0.6b-v2"]
SCORERS = ["bertscore", "semdist", "span_len"]


def split_ids(name):
    return [l.strip() for l in open(DATA / "splits" / f"{name}.txt") if l.strip()]


def bertscore(refs, hyps, bs):
    from bert_score import score
    _, _, f1 = score(hyps, refs, lang="en", model_type="roberta-large", rescale_with_baseline=True,
                     batch_size=bs, verbose=True)
    return 1.0 - f1.numpy()


def semdist(refs, hyps, bs):
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer("sentence-transformers/all-mpnet-base-v2", device="cpu")
    a = m.encode(refs, batch_size=bs, normalize_embeddings=True, show_progress_bar=True)
    b = m.encode(hyps, batch_size=bs, normalize_embeddings=True, show_progress_bar=True)
    return 1.0 - (a * b).sum(1)


def metrics(pred, gold, mapped=None):
    pred, gold = np.asarray(pred, float), np.asarray(gold, float)
    out = {"n": int(len(gold)), "spearman": float(spearmanr(pred, gold).statistic)}
    p = pred if mapped is None else np.asarray(mapped, float)
    if p is not None:
        r = np.clip(np.floor(p + 0.5), 1, 5).astype(int)
        g = np.floor(gold + 0.5).astype(int)  # human mean can be x.5: round half up
        out.update(qwk=float(cohen_kappa_score(g, r, weights="quadratic", labels=[1, 2, 3, 4, 5])),
                   mae=float(np.abs(p - gold).mean()), within_1=float((np.abs(r - g) <= 1).mean()),
                   exact=float((r == g).mean()))
    return out


def human_pilot():
    sev = []
    for who in "AB":
        d = pd.read_excel(ROOT / "annotation" / f"human_pilot_{who}.xlsx").set_index("error_id")
        sev.append(pd.to_numeric(d.severity, errors="coerce"))
    return pd.concat(sev, axis=1).mean(axis=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--student", required=True, type=Path, help="jsonl with error_id, severity (student)")
    ap.add_argument("--bs", type=int, default=32)
    ap.add_argument("--recompute", action="store_true")
    args = ap.parse_args()
    BASE.mkdir(exist_ok=True)

    errors = load_errors(["test", "test_extra", "dev"])
    teacher = {r["error_id"]: r["severity"] for r in map(json.loads, open(TEACHER))}
    # The student file re-aligned the hypotheses; keep a prediction only when its span matched the repo span
    # (score_student.py sets teacher_severity to None otherwise, and for ref_issue spans).
    student = {r["error_id"]: r["severity"] for r in map(json.loads, open(args.student))
               if r.get("teacher_severity") is not None}
    splits = {n: split_ids(n) for n in ["dev_balanced", "test_balanced", "test_all", "pilot_human"]}
    ids = sorted(set().union(*splits.values()))
    missing = [i for i in ids if i not in errors]
    assert not missing, f"{len(missing)} split ids not in error files, e.g. {missing[:3]}"

    cache = BASE / "span_scores.jsonl"
    if cache.exists() and not args.recompute:
        rows = {r["error_id"]: r for r in map(json.loads, open(cache))}
    else:
        refs = [errors[i]["ref"] for i in ids]
        hyps = [single_error_hyp(errors[i]) for i in ids]
        bsc, sd = bertscore(refs, hyps, args.bs), semdist(refs, hyps, args.bs)
        rows = {}
        for k, i in enumerate(ids):
            e = errors[i]
            rows[i] = {"error_id": i, "system": e["system"], "ref": refs[k], "single_error_hyp": hyps[k],
                       "bertscore": float(bsc[k]), "semdist": float(sd[k]), "span_len": int(e["n_word_errors"]),
                       "teacher": teacher.get(i), "student": student.get(i)}
        with open(cache, "w") as f:
            for i in ids:
                f.write(json.dumps(rows[i], ensure_ascii=False) + "\n")

    for i, r in rows.items():
        r["student"] = student.get(i)

    # isotonic maps (baseline score -> teacher severity), fit on dev only
    dev = [rows[i] for i in splits["dev_balanced"]]
    iso = {s: IsotonicRegression(y_min=1, y_max=5, increasing=True, out_of_bounds="clip")
           .fit([r[s] for r in dev], [r["teacher"] for r in dev]) for s in SCORERS}

    def evaluate(id_list, gold_of):
        res = {}
        for group in SYSTEMS + ["all"]:
            sel = [rows[i] for i in id_list if group == "all" or rows[i]["system"] == group]
            sel = [r for r in sel if gold_of(r) is not None and not np.isnan(gold_of(r))]
            if not sel:
                continue
            gold = [gold_of(r) for r in sel]
            res[group] = {s: metrics([r[s] for r in sel], gold, iso[s].predict([r[s] for r in sel])) for s in SCORERS}
            stu = [r for r in sel if r["student"] is not None]
            if stu:
                res[group]["student"] = metrics([r["student"] for r in stu], [gold_of(r) for r in stu])
        return res

    out = {"note": "gold = DeepSeek teacher severity unless stated; baselines mapped to 1-5 by isotonic fit on dev_balanced",
           "test_balanced": evaluate(splits["test_balanced"], lambda r: r["teacher"]),
           "test_all": evaluate(splits["test_all"], lambda r: r["teacher"])}
    hp = human_pilot()
    for i in splits["pilot_human"]:
        rows[i]["human_mean"] = float(hp.get(i, np.nan))
    pilot = evaluate(splits["pilot_human"], lambda r: r["human_mean"])
    pilot_teacher = [r for r in (rows[i] for i in splits["pilot_human"]) if r["teacher"] is not None]
    pilot["all"]["teacher"] = metrics([r["teacher"] for r in pilot_teacher], [r["human_mean"] for r in pilot_teacher])
    out["pilot_human_vs_human_mean"] = pilot
    (BASE / "span_metrics.json").write_text(json.dumps(out, indent=2) + "\n")

    for name in ["test_balanced", "test_all", "pilot_human_vs_human_mean"]:
        print(f"\n== {name} (all systems) ==")
        for scorer, m in out[name]["all"].items():
            print(f"{scorer:10s} " + "  ".join(f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}" for k, v in m.items()))


if __name__ == "__main__":
    main()
