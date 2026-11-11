"""Inter-annotator agreement on the human pilot, and LLM-vs-human agreement.

Reads annotation/human_pilot_{A,B}.xlsx and any outputs/llm_annotations_*.jsonl.
"""
import json

import krippendorff
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import cohen_kappa_score

from common import OUT, ROOT


def pair_stats(a, b):
    m = a.notna() & b.notna()
    a, b = a[m].astype(int), b[m].astype(int)
    return {"n": int(m.sum()),
            "qwk": cohen_kappa_score(a, b, weights="quadratic"),
            "alpha_ordinal": krippendorff.alpha(np.vstack([a, b]), level_of_measurement="ordinal"),
            "spearman": spearmanr(a, b).statistic,
            "exact": float((a == b).mean()),
            "within1": float(((a - b).abs() <= 1).mean()),
            "mae": float((a - b).abs().mean())}


def nominal_alpha(x, y):
    m = x.notna() & y.notna() & (x != "") & (y != "")
    if m.sum() < 2:
        return np.nan
    cats = {c: i for i, c in enumerate(sorted(set(x[m]) | set(y[m])))}
    if len(cats) < 2:  # alpha is undefined when everyone used a single category
        return np.nan
    return krippendorff.alpha(np.vstack([x[m].map(cats), y[m].map(cats)]).astype(float),
                              level_of_measurement="nominal")


def main():
    sev, cat, form, flags = {}, {}, {}, {}
    for who in "AB":
        p = ROOT / "annotation" / f"human_pilot_{who}.xlsx"
        d = pd.read_excel(p).set_index("error_id")
        d["severity"] = pd.to_numeric(d.severity, errors="coerce")
        if d.severity.notna().sum() == 0:
            print(f"{p.name}: not annotated yet")
            continue
        sev[who], cat[who], form[who] = d.severity, d.content_type, d.error_form
        flags[who] = d.flag.fillna("").astype(str)
    for p in sorted(OUT.glob("llm_annotations_*.jsonl")):
        d = pd.DataFrame([json.loads(l) for l in open(p)]).set_index("error_id")
        tag = "llm:" + p.stem.removeprefix("llm_annotations_")
        sev[tag], cat[tag], form[tag] = d.severity, d.content_type, d.error_form
    if "A" in sev and "B" in sev:
        sev["human_mean"] = (sev["A"] + sev["B"]) / 2

    all_ids = pd.read_csv(OUT / "pilot_ids.txt", header=None)[0]
    uncertain = set()
    for f in flags.values():
        uncertain |= set(f[f.str.contains("uncertain")].index)
    rows = []
    subsets = [("all", all_ids)]
    if uncertain:
        subsets.append(("no_uncertain", all_ids[~all_ids.isin(uncertain)]))
    for subset, ids in subsets:
        S = pd.DataFrame({k: v.reindex(ids) for k, v in sev.items()})
        C = pd.DataFrame({k: v.reindex(ids) for k, v in cat.items()})
        F = pd.DataFrame({k: v.reindex(ids) for k, v in form.items()})
        names = [k for k in S if k != "human_mean"]
        for i, x in enumerate(names):
            for y in names[i + 1:]:
                r = {"subset": subset, "pair": f"{x} vs {y}", **pair_stats(S[x], S[y])}
                r["content_type_alpha"] = nominal_alpha(C[x], C[y])
                r["error_form_alpha"] = nominal_alpha(F[x], F[y])
                rows.append(r)
        if "human_mean" in S:
            for k in names:
                if k.startswith("llm:"):
                    m = S[k].notna()
                    rows.append({"subset": subset, "pair": f"{k} vs human_mean", "n": int(m.sum()),
                                 "spearman": spearmanr(S[k][m], S.human_mean[m]).statistic})
    res = pd.DataFrame(rows)
    print(res.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    res.to_csv(OUT / "agreement.csv", index=False)
    S = pd.DataFrame({k: v.reindex(all_ids) for k, v in sev.items()})
    if {"A", "B"} <= set(S):
        diff = S[(S.A - S.B).abs() >= 2].index
        print(f"\n{len(diff)} items where A and B differ by >= 2 (discuss these):")
        for i in diff:
            print(f"  {i}  A={S.A[i]:.0f} B={S.B[i]:.0f}")


if __name__ == "__main__":
    main()
