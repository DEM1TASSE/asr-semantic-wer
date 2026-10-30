"""Inter-annotator agreement on the human pilot, and LLM-vs-human agreement.

Reads annotation/human_pilot_{A,B}.csv and any outputs/llm_annotations_*.jsonl.
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
            "within1": float(((a - b).abs() <= 1).mean())}


def main():
    sev, cat = {}, {}
    for who in "AB":
        p = ROOT / "annotation" / f"human_pilot_{who}.csv"
        d = pd.read_csv(p).set_index("error_id")
        d["severity"] = pd.to_numeric(d.severity, errors="coerce")
        if d.severity.notna().sum() == 0:
            print(f"{p.name}: not annotated yet")
            continue
        sev[who], cat[who] = d.severity, d.content_type
    for p in sorted(OUT.glob("llm_annotations_*.jsonl")):
        d = pd.DataFrame([json.loads(l) for l in open(p)]).set_index("error_id")
        tag = "llm:" + p.stem.removeprefix("llm_annotations_")
        sev[tag], cat[tag] = d.severity, d.content_type
    if "A" in sev and "B" in sev:
        sev["human_mean"] = (sev["A"] + sev["B"]) / 2

    ids = pd.read_csv(OUT / "pilot_ids.txt", header=None)[0]
    S = pd.DataFrame({k: v.reindex(ids) for k, v in sev.items()})
    C = pd.DataFrame({k: v.reindex(ids) for k, v in cat.items()})
    rows = []
    names = [k for k in S if k != "human_mean"]
    for i, x in enumerate(names):
        for y in names[i + 1:]:
            r = {"pair": f"{x} vs {y}", **pair_stats(S[x], S[y])}
            m = C[x].notna() & C[y].notna()
            r["content_type_kappa"] = cohen_kappa_score(C[x][m], C[y][m]) if m.any() else np.nan
            rows.append(r)
    if "human_mean" in S:
        for k in names:
            if k.startswith("llm:"):
                m = S[k].notna()
                rows.append({"pair": f"{k} vs human_mean", "n": int(m.sum()),
                             "spearman": spearmanr(S[k][m], S.human_mean[m]).statistic})
    res = pd.DataFrame(rows)
    print(res.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    res.to_csv(OUT / "agreement.csv", index=False)
    if {"A", "B"} <= set(S):
        diff = S[(S.A - S.B).abs() >= 2].index
        print(f"\n{len(diff)} items where A and B differ by >= 2 (discuss these):")
        for i in diff:
            print(f"  {i}  A={S.A[i]:.0f} B={S.B[i]:.0f}")


if __name__ == "__main__":
    main()
