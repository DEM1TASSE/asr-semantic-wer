"""Compute severity-weighted WER from span severities and compare with plain WER.

Semantic-WER variants (N = # reference words; each span s has n_s word errors, severity v_s in 1..5):
  semwer_lin  = sum_s n_s * v_s / 5       / N   (every error counts, scaled by severity)
  semwer_hard = sum_s n_s * (v_s - 1) / 4 / N   (severity-1 errors cost nothing)
  semwer_max  = mean over utts of max_s (v_s - 1) / 4  (utterance-level "worst error" score)
Only utterances whose spans are all annotated are scored; coverage is reported.
Outputs: outputs/semwer_summary.json, outputs/utt_scores.csv, outputs/cases.md, outputs/fig_*.png
"""
import argparse
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from common import OUT, SUBSETS, normalize, subset_paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="deepseek-v4-1-flash_v2.4")
    ap.add_argument("--subset", nargs="+", default=["test"], choices=SUBSETS,
                    help="one or more subsets, pooled (e.g. test test_extra)")
    args = ap.parse_args()

    sfx = "" if args.subset == ["test"] else "_" + "+".join(args.subset)
    P = [subset_paths(s) for s in args.subset]
    err = pd.DataFrame([json.loads(l) for q in P for l in open(q["errors"])])
    ann = pd.DataFrame([json.loads(l) for l in open(OUT / f"llm_annotations_{args.tag}.jsonl")])
    err = err.merge(ann[["error_id", "severity", "content_type", "error_form", "flag", "rationale"]],
                    on="error_id", how="left")
    # Reference problems are not ASR errors: drop them from both WER and Semantic-WER counts.
    is_ref = err.flag.map(lambda f: "ref_issue" in (f if isinstance(f, list) else str(f).split(";")))
    n_flag = is_ref.sum()
    err_all = err
    err = err[~is_ref]
    print(f"excluded {n_flag} ref_issue spans")
    wer = {k: v for q in P for k, v in json.load(open(q["wer"])).items()}  # system names only
    utts = pd.DataFrame([json.loads(l) for q in P for l in open(q["meta"])])

    rows = []
    for sysname in wer:
        e = err[err.system == sysname]
        for _, u in utts.iterrows():
            es = e[e.audio_id == u.audio_id]
            n = len(normalize(u.ref).split())
            covered = es.severity.notna().all()
            rows.append({"system": sysname, "audio_id": u.audio_id, "n_ref": n, "covered": covered,
                         "word_errors": es.n_word_errors.sum(),
                         "word_errors_all": err_all[(err_all.system == sysname) & (err_all.audio_id == u.audio_id)].n_word_errors.sum(),
                         "w_lin": (es.n_word_errors * es.severity / 5).sum(),
                         "w_hard": (es.n_word_errors * (es.severity - 1) / 4).sum(),
                         "max_sev": es.severity.max() if len(es) else 1.0})
    U = pd.DataFrame(rows)
    U.to_csv(OUT / f"utt_scores{sfx}.csv", index=False)

    summary = {}
    for sysname, g in U.groupby("system"):
        c = g[g.covered]
        N = c.n_ref.sum()
        N_all = g.n_ref.sum()
        g = g.assign(word_errors_all=g.word_errors_all)
        summary[sysname] = {
            "subsets": "+".join(args.subset),
            "coverage_utts": f"{len(c)}/{len(g)}",
            "wer_on_covered": c.word_errors.sum() / N,
            "semwer_lin": c.w_lin.sum() / N,
            "semwer_hard": c.w_hard.sum() / N,
            "semwer_max": ((c.max_sev - 1) / 4).mean(),
            "wer_full": g.word_errors_all.sum() / N_all,
        }
    json.dump(summary, open(OUT / f"semwer_summary{sfx}.json", "w"), indent=2)
    print(pd.DataFrame(summary).T.to_string(float_format=lambda v: f"{v:.3f}"))

    a = err[err.severity.notna()]
    # Severity distribution per system
    pd.crosstab(a.system, a.severity.astype(int), normalize="index").T.plot.bar(figsize=(6, 3.5), rot=0)
    plt.xlabel("severity"); plt.ylabel("fraction of error spans"); plt.tight_layout()
    plt.savefig(OUT / f"fig_severity_dist{sfx}.png", dpi=200); plt.close()
    # Category x system counts and mean severity
    cat = a.groupby(["content_type", "system"]).severity.agg(["count", "mean"]).unstack("system")
    cat.to_csv(OUT / f"category_by_system{sfx}.csv")
    print("\n", cat.to_string(float_format=lambda v: f"{v:.2f}"))
    pd.crosstab(a.error_form, a.system).to_csv(OUT / f"error_form_by_system{sfx}.csv")
    print("\n", pd.crosstab(a.error_form, a.system).to_string())
    pd.crosstab(a.content_type, a.system).plot.barh(figsize=(6, 4))
    plt.xlabel("# error spans"); plt.tight_layout()
    plt.savefig(OUT / f"fig_category_counts{sfx}.png", dpi=200); plt.close()
    # Utterance-level WER vs Semantic-WER scatter
    c = U[U.covered & (U.word_errors > 0)]
    fig, ax = plt.subplots(figsize=(4.5, 4))
    for s, g in c.groupby("system"):
        ax.scatter(g.word_errors / g.n_ref, g.w_hard / g.n_ref, s=8, alpha=.5, label=s)
    ax.plot([0, 1], [0, 1], "k--", lw=.8); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xlabel("utterance WER"); ax.set_ylabel("utterance Semantic-WER (hard)"); ax.legend(fontsize=7)
    plt.tight_layout(); plt.savefig(OUT / f"fig_wer_vs_semwer{sfx}.png", dpi=200); plt.close()

    # Representative cases: same/low WER but very different severity
    with open(OUT / f"cases{sfx}.md", "w") as f:
        f.write("# Representative cases\n\n")
        for title, q in [("High-severity single-word errors", (a.n_word_errors == 1) & (a.severity >= 5)),
                         ("Multi-word errors judged harmless", (a.n_word_errors >= 2) & (a.severity == 1))]:
            f.write(f"## {title}\n\n")
            for _, r in a[q].head(6).iterrows():
                f.write(f"- **{r.system}** sev={int(r.severity)} [{r.content_type}/{r.error_form}] `{r.ref_marked}`  \n"
                        f"  _{r.rationale}_\n")
            f.write("\n")
        f.write("## Utterances with the largest WER vs Semantic-WER gap\n\n")
        c = c.assign(gap=c.word_errors / c.n_ref - c.w_hard / c.n_ref)
        for _, r in pd.concat([c.nlargest(3, "gap"), c.nsmallest(3, "gap")]).iterrows():
            spans = a[(a.system == r.system) & (a.audio_id == r.audio_id)]
            f.write(f"- **{r.system}** WER={r.word_errors/r.n_ref:.2f} SemWER={r.w_hard/r.n_ref:.2f}: "
                    + "; ".join(f"`{s.ref_span or '∅'} → {s.hyp_span or '∅'}` ({int(s.severity)})"
                                for _, s in spans.iterrows()) + "\n")
    print(f"\nwrote figures, category_by_system.csv, cases.md to {OUT}")


if __name__ == "__main__":
    main()
