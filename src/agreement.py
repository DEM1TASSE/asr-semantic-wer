"""Inter-annotator agreement on the human pilot, and LLM-vs-human agreement.

Reads annotation/human_pilot_{A,B}.xlsx and any outputs/llm_annotations_*.jsonl. Reports severity
agreement (quadratic weighted kappa, ordinal alpha, Spearman, exact, within-1, MAE) and content_type
agreement (nominal alpha, exact, confusion matrix), on all items and without items any human flagged
`uncertain`.
"""
import json

import krippendorff
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import cohen_kappa_score

from common import OUT, ROOT


def severity_stats(a, b):
    m = a.notna() & b.notna()
    a, b = a[m], b[m]
    if len(a) < 3:
        return {"n": int(m.sum())}
    out = {"n": int(m.sum()), "spearman": spearmanr(a, b).statistic,
           "within1": float(((a - b).abs() <= 1).mean()), "mae": float((a - b).abs().mean())}
    if (a % 1 == 0).all() and (b % 1 == 0).all():  # integer raters; human_mean is not
        a, b = a.astype(int), b.astype(int)
        out["qwk"] = cohen_kappa_score(a, b, weights="quadratic")
        out["alpha_ordinal"] = (krippendorff.alpha(np.vstack([a, b]), level_of_measurement="ordinal")
                                if len(set(a) | set(b)) > 1 else np.nan)
        out["exact"] = float((a == b).mean())
    return out


def category_stats(x, y):
    m = x.notna() & y.notna() & (x != "") & (y != "")
    x, y = x[m], y[m]
    out = {"n": int(m.sum()), "exact": float((x == y).mean()) if len(x) else np.nan}
    cats = {c: i for i, c in enumerate(sorted(set(x) | set(y)))}
    out["alpha_nominal"] = (krippendorff.alpha(np.vstack([x.map(cats), y.map(cats)]).astype(float),
                                               level_of_measurement="nominal")
                            if len(x) >= 2 and len(cats) >= 2 else np.nan)
    return out


def load_raters():
    raters, flags = {}, {}
    for who in "AB":
        p = ROOT / "annotation" / f"human_pilot_{who}.xlsx"
        d = pd.read_excel(p).set_index("error_id")
        if pd.to_numeric(d.severity, errors="coerce").notna().sum() == 0:
            print(f"{p.name}: not annotated yet")
            continue
        raters[who] = d
        flags[who] = d.flag.fillna("").astype(str)
    for p in sorted(OUT.glob("llm_annotations_*.jsonl")):
        d = pd.DataFrame([json.loads(l) for l in open(p)]).set_index("error_id")
        raters["llm:" + p.stem.removeprefix("llm_annotations_")] = d
    for d in raters.values():
        d["severity"] = pd.to_numeric(d.severity, errors="coerce")
        d["content_type"] = d.content_type.fillna("").astype(str).str.strip()
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
    sev_rows, cat_rows = [], []
    for subset, ids in subsets:
        S = pd.DataFrame({k: raters[k].severity.reindex(ids) for k in names})
        C = pd.DataFrame({k: raters[k].content_type.reindex(ids) for k in names})
        for i, x in enumerate(names):
            for y in names[i + 1:]:
                sev_rows.append({"subset": subset, "pair": f"{x} vs {y}", **severity_stats(S[x], S[y])})
                cat_rows.append({"subset": subset, "pair": f"{x} vs {y}", **category_stats(C[x], C[y])})
        if {"A", "B"} <= set(names):
            mean = S[["A", "B"]].mean(axis=1)
            for k in names:
                if k.startswith("llm:"):
                    sev_rows.append({"subset": subset, "pair": f"{k} vs human_mean",
                                     **severity_stats(S[k], mean)})

    fmt = lambda v: f"{v:.3f}"
    sev = pd.DataFrame(sev_rows)
    sev = sev[[c for c in ["subset", "pair", "n", "qwk", "alpha_ordinal", "spearman", "exact", "within1", "mae"]
               if c in sev]]
    print("== severity ==")
    print(sev.to_string(index=False, float_format=fmt, na_rep="-"))
    cat = pd.DataFrame(cat_rows)
    print("\n== content_type ==")
    print(cat.to_string(index=False, float_format=fmt, na_rep="-"))
    sev.assign(score="severity").to_csv(OUT / "agreement.csv", index=False)
    cat.to_csv(OUT / "agreement_content_type.csv", index=False)

    if {"A", "B"} <= set(names):
        A, B = raters["A"].reindex(all_ids), raters["B"].reindex(all_ids)
        print("\n== content_type confusion (rows A, columns B) ==")
        print(pd.crosstab(A.content_type, B.content_type))
        big = (A.severity - B.severity).abs() >= 2
        print(f"\n{int(big.sum())} items where A and B differ by >= 2 in severity (discuss these):")
        for i in all_ids[big.values]:
            print(f"  {i}  A={A.severity[i]:.0f} ({A.content_type[i]})  B={B.severity[i]:.0f} ({B.content_type[i]})")


if __name__ == "__main__":
    main()
