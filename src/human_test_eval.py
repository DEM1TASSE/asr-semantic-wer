"""100-error human test: rater agreement and automatic scorers vs the human labels.

Rater A final = the 57 relabeled display-affected items (human_test_A_relabel57_filled.xlsx) + the 43
unaffected items from human_test_A_filled.xlsx. Rater B = human_test_B_filled.xlsx.
Gold = mean of A and B. Scorers: DeepSeek teacher, DistilBERT student, BERTScore, SemDist, span length
(baselines mapped to 1-5 by the isotonic fit on dev_balanced, as in semantic_baselines.py).
Reported on all 100 items and without the items rater B flagged ref_issue.

Usage: HF_HOME=/work/hdd/bjdh/dwang30/semwer/hf_cache pixi run python src/human_test_eval.py
Outputs: outputs/human_test_eval.json, outputs/human_test_items.csv, outputs/baselines/human_test_scores.jsonl
"""
import json

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression

from agreement import severity_stats
from common import OUT, ROOT, load_errors, single_error_hyp
from semantic_baselines import SCORERS, bertscore, metrics, semdist, split_ids

SUB = ROOT / "annotation" / "submissions"
TEACHER = OUT / "llm_annotations_deepseek-v4-1-flash_v2.4.jsonl"
STUDENT = OUT / "student_predictions_test+test_extra.jsonl"
SPAN_CACHE = OUT / "baselines" / "span_scores.jsonl"
HT_CACHE = OUT / "baselines" / "human_test_scores.jsonl"
SYSTEMS = ["whisper-large-v3", "wav2vec2-large", "parakeet-tdt-0.6b-v2", "qwen3-asr-0.6b", "qwen3-asr-1.7b"]


def raters():
    a = pd.read_excel(SUB / "human_test_A_filled.xlsx").set_index("#")
    r = pd.read_excel(SUB / "human_test_A_relabel57_filled.xlsx").set_index("#")
    b = pd.read_excel(SUB / "human_test_B_filled.xlsx").set_index("#")
    assert (a.error_id == b.error_id).all() and (r.error_id == a.loc[r.index, "error_id"]).all()
    df = pd.DataFrame({"error_id": a.error_id, "A_old": a.severity, "B": b.severity,
                       "B_flag": b.flag.fillna(""), "B_note": b.note.fillna("")})
    df["affected"] = df.index.isin(r.index)
    df["A"] = df.A_old
    df.loc[r.index, "A"] = r.severity
    for c in ["A", "A_old", "B"]:
        df[c] = pd.to_numeric(df[c]).astype(int)
    return df


def baseline_scores(ids, errors):
    rows = {r["error_id"]: r for r in map(json.loads, open(SPAN_CACHE))}
    if HT_CACHE.exists():
        rows.update({r["error_id"]: r for r in map(json.loads, open(HT_CACHE))})
    todo = [i for i in ids if i not in rows]
    if todo:
        refs = [errors[i]["ref"] for i in todo]
        hyps = [single_error_hyp(errors[i]) for i in todo]
        bsc, sd = bertscore(refs, hyps, 16), semdist(refs, hyps, 16)
        with open(HT_CACHE, "a") as f:
            for k, i in enumerate(todo):
                rows[i] = {"error_id": i, "system": errors[i]["system"], "ref": refs[k], "single_error_hyp": hyps[k],
                           "bertscore": float(bsc[k]), "semdist": float(sd[k]),
                           "span_len": int(errors[i]["n_word_errors"])}
                f.write(json.dumps(rows[i], ensure_ascii=False) + "\n")
    return rows


def main():
    df = raters()
    errors = load_errors(["test", "test_extra", "dev"])
    teacher = {r["error_id"]: r for r in map(json.loads, open(TEACHER))}
    student = {r["error_id"]: r["severity"] for r in map(json.loads, open(STUDENT))}
    rows = baseline_scores(list(df.error_id), errors)

    dev = [rows[i] for i in split_ids("dev_balanced")]
    iso = {s: IsotonicRegression(y_min=1, y_max=5, increasing=True, out_of_bounds="clip")
           .fit([r[s] for r in dev], [r["teacher"] for r in dev]) for s in SCORERS}

    df["system"] = [errors[i]["system"] for i in df.error_id]
    df["ref_marked"] = [errors[i]["ref_marked"] for i in df.error_id]
    df["teacher"] = [teacher[i]["severity"] for i in df.error_id]
    df["teacher_flag"] = [",".join(teacher[i].get("flag") or []) for i in df.error_id]
    df["student"] = [student[i] for i in df.error_id]
    for s in SCORERS:
        df[s] = [rows[i][s] for i in df.error_id]
        df[s + "_mapped"] = iso[s].predict(df[s])
    df["human_mean"] = (df.A + df.B) / 2

    def block(d):
        out = {"n": len(d),
               "A_vs_B": severity_stats(d.A.astype(float), d.B.astype(float)),
               "A_vs_B_before_relabel": severity_stats(d.A_old.astype(float), d.B.astype(float)),
               "vs_human_mean": {"teacher": metrics(d.teacher, d.human_mean, d.teacher),
                                 "student": metrics(d.student, d.human_mean, d.student),
                                 **{s: metrics(d[s], d.human_mean, d[s + "_mapped"]) for s in SCORERS}},
               "teacher_vs_A": severity_stats(d.teacher.astype(float), d.A.astype(float)),
               "teacher_vs_B": severity_stats(d.teacher.astype(float), d.B.astype(float)),
               "label_dist_A": d.A.value_counts().sort_index().to_dict(),
               "label_dist_B": d.B.value_counts().sort_index().to_dict(),
               "label_dist_teacher": d.teacher.value_counts().sort_index().to_dict()}
        return out

    no_ref = df[~df.B_flag.str.contains("ref_issue")]
    res = {"all": block(df), "without_B_ref_issue": block(no_ref),
           "affected_57": block(df[df.affected]), "unaffected_43": block(df[~df.affected]),
           "per_system": {s: block(df[df.system == s]) for s in SYSTEMS},
           "adjudicate_abs_diff_ge_2": df.index[(df.A - df.B).abs() >= 2].tolist()}
    json.dump(res, open(OUT / "human_test_eval.json", "w"), indent=1, default=float)
    df.to_csv(OUT / "human_test_items.csv")

    def fmt(m):
        return " ".join(f"{k}={v:.2f}" if isinstance(v, float) else f"{k}={v}" for k, v in m.items())
    for k in ["all", "without_B_ref_issue", "affected_57", "unaffected_43"]:
        print(f"== {k} (n={res[k]['n']})")
        print("  A vs B          ", fmt(res[k]["A_vs_B"]))
        print("  A(old) vs B     ", fmt(res[k]["A_vs_B_before_relabel"]))
        for s, m in res[k]["vs_human_mean"].items():
            print(f"  {s:10s} vs mean", fmt(m))
    for s in SYSTEMS:
        p = res["per_system"][s]
        print(s, "A-B qwk %.2f" % p["A_vs_B"].get("qwk", np.nan),
              "teacher %.2f student %.2f" % (p["vs_human_mean"]["teacher"]["qwk"], p["vs_human_mean"]["student"]["qwk"]))
    print("dist A", res["all"]["label_dist_A"], "B", res["all"]["label_dist_B"], "T", res["all"]["label_dist_teacher"])
    print("adjudicate:")
    print(df.loc[res["adjudicate_abs_diff_ge_2"], ["system", "ref_marked", "A", "B", "teacher", "student"]].to_string())


if __name__ == "__main__":
    main()
