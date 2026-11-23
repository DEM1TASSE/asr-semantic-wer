"""Sample the 100-error human test set and write blank annotation sheets for annotators A and B.

- Source: AMI test only (subsets test + test_extra), so it never overlaps train or dev meetings.
- Excludes the 50 pilot errors (used to tune the rubric / prompt / teacher).
- Equal per ASR system (100 / 5 systems -> 20 each: Whisper, wav2vec2, Parakeet, Qwen3-ASR 0.6B / 1.7B), ~70% random + ~30% targeted by SURFACE features
  (digits/negation words, long spans, substitutions), as in the pilot. Never selected by LLM labels.
- If two systems made the identical error on the same utterance, only one copy can be picked.
Outputs: annotation/human_test_{A,B}.xlsx (never overwritten), data/splits/human_test.txt,
         outputs/human_test_sampling.csv (sampling type per item; not shown to annotators)
"""
import argparse

import pandas as pd

from common import DATA, OUT, ROOT, load_errors, single_error_hyp
from make_sets import fmt_context, targeted_pool, write_sheet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--frac_targeted", type=float, default=0.3)
    ap.add_argument("--seed", type=int, default=751)
    args = ap.parse_args()

    df = pd.DataFrame(load_errors(["test", "test_extra"]).values())
    pilot = {l.strip() for l in open(OUT / "pilot_ids.txt") if l.strip()}
    df = df[~df.error_id.isin(pilot)]
    df = df.sample(frac=1, random_state=args.seed)
    df = df.drop_duplicates(["audio_id", "ref_start", "ref_end", "hyp_span"]).reset_index(drop=True)
    systems = sorted(df.system.unique())
    quota = {s: args.n // len(systems) + (1 if i < args.n % len(systems) else 0) for i, s in enumerate(systems)}

    picks = []
    for s in systems:
        d = df[df.system == s]
        n_tgt = round(quota[s] * args.frac_targeted)
        rand = d.sample(quota[s] - n_tgt, random_state=args.seed)
        picks.append(rand.assign(sampling="random"))
        used = set(rand.index)
        pools = targeted_pool(d.drop(rand.index))
        for i, (kind, pool) in enumerate(pools.items()):
            k = n_tgt // len(pools) + (1 if i < n_tgt % len(pools) else 0)
            pick = pool.drop([j for j in pool.index if j in used]).sample(k, random_state=args.seed)
            used |= set(pick.index)
            picks.append(pick.assign(sampling=kind))
    ht = pd.concat(picks).sample(frac=1, random_state=args.seed)  # interleave systems and sampling types
    assert ht.error_id.is_unique and len(ht) == args.n

    ht[["error_id", "system", "subset", "meeting_id", "sampling"]].to_csv(OUT / "human_test_sampling.csv", index=False)
    (DATA / "splits" / "human_test.txt").write_text("\n".join(ht.error_id) + "\n")
    sheet = pd.DataFrame({
        "#": range(1, len(ht) + 1),
        "context (reference transcript)": ht.apply(fmt_context, axis=1).values,
        "error in reference: [[reference → ASR]]": ht.ref_marked.values,
        "reference said": ht.ref_span.replace("", "∅").values,
        "ASR output": ht.hyp_span.replace("", "∅").values,
        "edit_operation": ht.op.values,
        "ASR sentence with only this error": ht.apply(single_error_hyp, axis=1).values,
        "severity": "", "content_type": "", "flag": "", "note": "",
        "error_id": ht.error_id.values,
    })
    for who in "AB":
        p = ROOT / "annotation" / f"human_test_{who}.xlsx"
        if p.exists():
            print(f"skip {p} (exists, not overwriting annotations)")
            continue
        write_sheet(sheet, p)
    print(ht.groupby(["system", "sampling"]).size().unstack(fill_value=0))
    print(f"{len(ht)} items from {ht.meeting_id.nunique()} meetings")


if __name__ == "__main__":
    main()
