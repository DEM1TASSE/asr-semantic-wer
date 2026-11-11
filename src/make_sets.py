"""Sample the human pilot set and the LLM annotation set from outputs/errors.jsonl.

- human pilot (default 50): ~70% random (stratified by system) + ~30% targeted (digits/negation,
  long spans, substitutions); written as blank CSVs for annotators A and B. The sampling type is saved
  to outputs/pilot_sampling.csv, never shown to annotators. Never sample by LLM labels.
- LLM set (default 500): includes all pilot items (for LLM-human agreement) plus a random remainder.
"""
import argparse
import json

import re

import pandas as pd

from common import OUT, ROOT


def fmt_context(e):
    return "\n".join(e["context_before"] + ["[TARGET] " + e["ref"]] + e["context_after"])


NEG = re.compile(r"\b(?:not|no|never|nothing|none|nobody|neither|nor|cannot|can't|won't|don't|n't)\b")


def targeted_pool(df):
    """Rare but high-risk error shapes that random sampling under-represents."""
    spans = df.ref_span + " " + df.hyp_span
    return {
        "digit_or_negation": df[spans.str.contains(r"\d") | spans.str.contains(NEG)],
        "long_span": df[df.n_word_errors >= 3],
        "substitution": df[df.op == "substitution"],
    }


CONTENT_TYPES = ["disfluency", "function_word", "content_word", "named_entity", "number", "negation", "other"]
FLAGS = ["ref_issue", "crosstalk", "uncertain", "multi_issue"]
WIDTHS = {"#": 4, "context (reference transcript)": 45, "error in reference: [[reference → ASR]]": 45,
          "reference said": 16, "ASR output": 16, "edit_operation": 12, "full ASR sentence": 35,
          "severity": 9, "content_type": 15, "flag": 14, "note": 30}


def write_sheet(sheet, path):
    """Annotation workbook: wrapped text, frozen header, dropdowns on the label columns."""
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation

    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        sheet.to_excel(xw, index=False, sheet_name="annotate")
        ws = xw.sheets["annotate"]
        col = {name: get_column_letter(i + 1) for i, name in enumerate(sheet.columns)}
        n = len(sheet) + 1
        for name, letter in col.items():
            ws.column_dimensions[letter].width = WIDTHS.get(name, 10)
            if name not in WIDTHS:
                ws.column_dimensions[letter].hidden = True  # ids and alignment indices
        for row in ws.iter_rows(min_row=1, max_row=n):
            for c in row:
                c.alignment = Alignment(wrap_text=True, vertical="top")
        fill = PatternFill("solid", fgColor="FFF2CC")
        for name in ["severity", "content_type", "flag", "note"]:
            ws[f"{col[name]}1"].fill = fill
            for r in range(2, n + 1):
                ws[f"{col[name]}{r}"].fill = fill
        for c in ws[1]:
            c.font = Font(bold=True)
        ws.freeze_panes = "C2"

        def dropdown(name, values, strict=True):
            dv = DataValidation(type="list", formula1='"' + ",".join(values) + '"', allow_blank=True,
                                showErrorMessage=strict)
            ws.add_data_validation(dv)
            dv.add(f"{col[name]}2:{col[name]}{n}")
        dropdown("severity", ["1", "2", "3", "4", "5"])
        dropdown("content_type", CONTENT_TYPES)
        dropdown("flag", FLAGS, strict=False)  # several values allowed: type e.g. "ref_issue;crosstalk"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n_pilot", type=int, default=50)
    ap.add_argument("--frac_targeted", type=float, default=0.3)
    ap.add_argument("--n_llm", type=int, default=500)
    ap.add_argument("--seed", type=int, default=751)
    args = ap.parse_args()

    df = pd.DataFrame([json.loads(l) for l in open(OUT / "errors.jsonl")])
    n_tgt = round(args.n_pilot * args.frac_targeted)
    n_rand = args.n_pilot - n_tgt
    per_sys = n_rand // df.system.nunique()
    rand = df.groupby("system").sample(n=per_sys, random_state=args.seed)
    rand = pd.concat([rand, df.drop(rand.index).sample(n_rand - len(rand), random_state=args.seed)])
    picks, kinds = [rand], ["random"] * len(rand)
    pools = targeted_pool(df.drop(rand.index))
    used = set(rand.index)
    for i, (kind, pool) in enumerate(pools.items()):
        k = n_tgt // len(pools) + (1 if i < n_tgt % len(pools) else 0)
        pick = pool.drop([j for j in pool.index if j in used]).sample(k, random_state=args.seed)
        used |= set(pick.index)
        picks.append(pick); kinds += [kind] * len(pick)
    pilot = pd.concat(picks).assign(sampling=kinds)
    pilot = pilot.sample(frac=1, random_state=args.seed)  # shuffle so systems and sampling types are interleaved
    pilot[["error_id", "system", "sampling"]].to_csv(OUT / "pilot_sampling.csv", index=False)
    rest = df.drop(pilot.index).sample(n=min(len(df) - len(pilot), args.n_llm - len(pilot)),
                                       random_state=args.seed)
    llm = pd.concat([pilot, rest])

    sheet = pd.DataFrame({
        "#": range(1, len(pilot) + 1),
        "context (reference transcript)": pilot.apply(fmt_context, axis=1).values,
        "error in reference: [[reference → ASR]]": pilot.ref_marked.values,
        "reference said": pilot.ref_span.replace("", "∅").values,
        "ASR output": pilot.hyp_span.replace("", "∅").values,
        "edit_operation": pilot.op.values,
        "full ASR sentence": pilot.hyp.values,
        "severity": "", "content_type": "", "flag": "", "note": "",
        "error_id": pilot.error_id.values,
        # alignment word indices (normalized ref/hyp), to trace spans if alignment changes
        "ref_start": pilot.ref_start.values, "ref_end": pilot.ref_end.values,
        "hyp_start": pilot.hyp_start.values, "hyp_end": pilot.hyp_end.values,
    })
    for who in "AB":
        p = ROOT / "annotation" / f"human_pilot_{who}.xlsx"
        if p.exists():
            print(f"skip {p} (exists, not overwriting annotations)")
            continue
        write_sheet(sheet, p)
    llm.error_id.to_csv(OUT / "llm_set_ids.txt", index=False, header=False)
    pilot.error_id.to_csv(OUT / "pilot_ids.txt", index=False, header=False)
    print(f"errors {len(df)} | pilot {len(pilot)} {pilot.sampling.value_counts().to_dict()} | llm set {len(llm)}")


if __name__ == "__main__":
    main()
