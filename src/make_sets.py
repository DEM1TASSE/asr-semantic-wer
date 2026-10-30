"""Sample the human pilot set and the LLM annotation set from outputs/errors.jsonl.

- human pilot (default 80): stratified by system; written as blank CSVs for annotators A and B.
- LLM set (default 500): includes all pilot items (for LLM-human agreement) plus a random remainder.
"""
import argparse
import json

import pandas as pd

from common import OUT, ROOT


def fmt_context(e):
    return "\n".join(e["context_before"] + ["[TARGET] " + e["ref"]] + e["context_after"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n_pilot", type=int, default=80)
    ap.add_argument("--n_llm", type=int, default=500)
    ap.add_argument("--seed", type=int, default=751)
    args = ap.parse_args()

    df = pd.DataFrame([json.loads(l) for l in open(OUT / "errors.jsonl")])
    pilot = df.groupby("system").sample(n=args.n_pilot // df.system.nunique(), random_state=args.seed)
    pilot = pilot.sample(frac=1, random_state=args.seed)  # shuffle so systems are interleaved
    rest = df.drop(pilot.index).sample(n=min(len(df) - len(pilot), args.n_llm - len(pilot)),
                                       random_state=args.seed)
    llm = pd.concat([pilot, rest])

    sheet = pd.DataFrame({
        "error_id": pilot.error_id,
        "context": pilot.apply(fmt_context, axis=1),
        "原文_said": pilot.ref_span.replace("", "∅"),
        "ASR_output": pilot.hyp_span.replace("", "∅"),
        "原文整句_[[原文→ASR]]": pilot.ref_marked,
        "ASR整句": pilot.hyp,
        "severity": "", "content_type": "", "error_form": "", "flag": "", "note": "",
    })
    for who in "AB":
        p = ROOT / "annotation" / f"human_pilot_{who}.csv"
        if p.exists():
            print(f"skip {p} (exists, not overwriting annotations)")
            continue
        sheet.to_csv(p, index=False)
    llm.error_id.to_csv(OUT / "llm_set_ids.txt", index=False, header=False)
    pilot.error_id.to_csv(OUT / "pilot_ids.txt", index=False, header=False)
    print(f"errors {len(df)} | pilot {len(pilot)} | llm set {len(llm)}")


if __name__ == "__main__":
    main()
