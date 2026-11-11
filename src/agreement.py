"""Inter-annotator agreement on the human pilot, and LLM-vs-human agreement.

Reads annotation/human_pilot_{A,B}.xlsx and any outputs/llm_annotations_*.jsonl. Reports agreement on
distortion (D, 1-5), importance (I, 1-3; only items where both raters gave one) and the derived
severity S = combine_severity(D, I), on all items and without items any human flagged `uncertain`.
"""
import json

import krippendorff
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import cohen_kappa_score

from common import OUT, ROOT, combine_severity

SCORES = ["distortion", "importance", "severity"]


def pair_stats(a, b, ordinal=True):
    m = a.notna() & b.notna()
    a, b = a[m], b[m]
    if len(a) < 3:
        return {"n": int(m.sum())}
    out = {"n": int(m.sum()), "spearman": spearmanr(a, b).statistic,
           "mae": float((a - b).abs().mean()), "within1": float(((a - b).abs() <= 1).mean())}
    if ordinal:  # integer scales (D, I); S is continuous
        a, b = a.astype(int), b.astype(int)
        out["qwk"] = cohen_kappa_score(a, b, weights="quadratic")
        out["alpha_ordinal"] = (krippendorff.alpha(np.vstack([a, b]), level_of_measurement="ordinal")
                                if len(set(a) | set(b)) > 1 else np.nan)
        out["exact"] = float((a == b).mean())
    else:
        out["alpha_interval"] = krippendorff.alpha(np.vstack([a, b]), level_of_measurement="interval")
    return out


def load_raters():
    raters, flags = {}, {}
    for who in "AB":
        p = ROOT / "annotation" / f"human_pilot_{who}.xlsx"
        d = pd.read_excel(p).set_index("error_id")
        if pd.to_numeric(d.distortion, errors="coerce").notna().sum() == 0:
            print(f"{p.name}: not annotated yet")
            continue
        raters[who] = d
        flags[who] = d.flag.fillna("").astype(str)
    for p in sorted(OUT.glob("llm_annotations_*.jsonl")):
        d = pd.DataFrame([json.loads(l) for l in open(p)]).set_index("error_id")
        raters["llm:" + p.stem.removeprefix("llm_annotations_")] = d
    for d in raters.values():
        d["distortion"] = pd.to_numeric(d.distortion, errors="coerce")
        d["importance"] = pd.to_numeric(d.importance, errors="coerce")
        d["severity"] = combine_severity(d.distortion, d.importance)
    return raters, flags


def main():
    raters, flags = load_raters()
    all_ids = pd.read_csv(OUT / "pilot_ids.txt", header=None)[0]
    uncertain = set()
    for f in flags.values():
        uncertain |= set(f[f.str.contains("uncertain")].index)
    subsets = [("all", all_ids)]
    if uncertain:
        subsets.append(("no_uncertain", all_ids[~all_ids.isin(uncertain)]))

    names = list(raters)
    rows = []
    for subset, ids in subsets:
        for score in SCORES:
            X = pd.DataFrame({k: raters[k][score].reindex(ids) for k in names})
            for i, x in enumerate(names):
                for y in names[i + 1:]:
                    rows.append({"subset": subset, "score": score, "pair": f"{x} vs {y}",
                                 **pair_stats(X[x], X[y], ordinal=score != "severity")})
            if {"A", "B"} <= set(names):
                mean = X[["A", "B"]].mean(axis=1)
                for k in names:
                    if k.startswith("llm:"):
                        rows.append({"subset": subset, "score": score, "pair": f"{k} vs human_mean",
                                     **pair_stats(X[k], mean, ordinal=False)})
    res = pd.DataFrame(rows)
    cols = ["subset", "score", "pair", "n", "qwk", "alpha_ordinal", "alpha_interval", "spearman",
            "exact", "within1", "mae"]
    res = res[[c for c in cols if c in res]]
    print(res.to_string(index=False, float_format=lambda v: f"{v:.3f}", na_rep="-"))
    res.to_csv(OUT / "agreement.csv", index=False)

    if {"A", "B"} <= set(names):
        A, B = raters["A"].reindex(all_ids), raters["B"].reindex(all_ids)
        print("\nItems to discuss (D differs by >= 2, or I differs by 2):")
        big = ((A.distortion - B.distortion).abs() >= 2) | ((A.importance - B.importance).abs() >= 2)
        # D = 1 vs D > 1 also means one rater saw no change at all
        big |= (A.distortion == 1) != (B.distortion == 1)
        for i in all_ids[big.values]:
            print(f"  {i}  A: D={A.distortion[i]:.0f} I={A.importance[i]}   "
                  f"B: D={B.distortion[i]:.0f} I={B.importance[i]}")


if __name__ == "__main__":
    main()
