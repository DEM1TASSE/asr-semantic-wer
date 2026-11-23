"""Sample utterance pairs for a blind pairwise human check of WER vs Semantic-WER.

For a pair of systems (A = Whisper, B = Parakeet or Qwen3-ASR 0.6B) on the same utterance, keep utterances
where the two metrics disagree: A has MORE word errors than B, but a LOWER teacher-weighted Semantic-WER
(sum of n_word_errors * (s-1)/4) ("opposite"). Such utterances are few, so each pair is filled up to 25 with
utterances where A has at least 2 more word errors but the SAME Semantic-WER ("tie": WER prefers B,
Semantic-WER sees no difference; a human "same" supports Semantic-WER). Annotators see the reference and the two outputs as X / Y in random order
and answer only: which output preserves the meaning of the reference better (X / Y / same)? No rubric.
Outputs: annotation/pairwise_{A,B}.xlsx (identical blank sheets), outputs/pairwise_key.csv (hidden key).
"""
import json
from collections import defaultdict

import numpy as np
import pandas as pd

from common import OUT, ROOT, load_errors

SEED, PER_PAIR = 751, 25
PAIRS = [("whisper-large-v3", "parakeet-tdt-0.6b-v2"), ("whisper-large-v3", "qwen3-asr-0.6b")]
TAG = "deepseek-v4-1-flash_v2.4"


def main():
    rng = np.random.default_rng(SEED)
    errors = load_errors(["test", "test_extra"])
    labels = {r["error_id"]: r for r in map(json.loads, open(OUT / f"llm_annotations_{TAG}.jsonl"))}
    edits, sem, hyp, ref, ctx = defaultdict(int), defaultdict(float), {}, {}, {}
    for i, e in errors.items():
        k = (e["system"], e["audio_id"])
        lab = labels[i]
        edits[k] += e["n_word_errors"]
        sem[k] += e["n_word_errors"] * (lab["severity"] - 1) / 4 * ("ref_issue" not in lab["flag"])
        hyp[k], ref[e["audio_id"]], ctx[e["audio_id"]] = e["hyp_raw"], e["ref_raw"], e["context_before"]
    rows, used = [], set()
    for a, b in PAIRS:
        cand = sorted(aid for aid in ref if aid not in used
                      and edits[(a, aid)] > edits[(b, aid)] and sem[(a, aid)] < sem[(b, aid)]
                      and (b, aid) in hyp and hyp.get((a, aid)) != hyp[(b, aid)])
        ties = sorted(aid for aid in ref if aid not in used and aid not in cand
                      and edits[(a, aid)] >= edits[(b, aid)] + 2 and abs(sem[(a, aid)] - sem[(b, aid)]) < 1e-9
                      and (b, aid) in hyp and hyp.get((a, aid)) != hyp[(b, aid)])
        pick = [cand[j] for j in rng.permutation(len(cand))[:PER_PAIR]]
        pick += [ties[j] for j in rng.permutation(len(ties))[:PER_PAIR - len(pick)]]
        used |= set(pick)
        print(f"{a} vs {b}: {len(cand)} opposite, {len(ties)} tie candidates; picked {len(pick)}")
        for aid in pick:
            flip = rng.random() < 0.5
            x, y = (b, a) if flip else (a, b)
            rows.append({"audio_id": aid, "pair": f"{a} vs {b}", "X_system": x, "Y_system": y,
                         "X": hyp[(x, aid)], "Y": hyp[(y, aid)],
                         "wer_prefers": "X" if edits[(x, aid)] < edits[(y, aid)] else "Y",
                         "semwer_prefers": ("same" if abs(sem[(x, aid)] - sem[(y, aid)]) < 1e-9
                                           else "X" if sem[(x, aid)] < sem[(y, aid)] else "Y"),
                         "type": "opposite" if aid in cand else "tie",
                         "X_edits": edits[(x, aid)], "Y_edits": edits[(y, aid)],
                         "X_semwer_weighted": round(sem[(x, aid)], 2), "Y_semwer_weighted": round(sem[(y, aid)], 2)})
    key = pd.DataFrame(rows).sample(frac=1, random_state=SEED).reset_index(drop=True)
    key.insert(0, "#", range(1, len(key) + 1))
    key.to_csv(OUT / "pairwise_key.csv", index=False)

    sheet = pd.DataFrame({"#": key["#"],
                          "context (previous utterances)": ["\n".join(ctx[a]) for a in key.audio_id],
                          "reference (what was said)": [ref[a] for a in key.audio_id],
                          "X": key.X, "Y": key.Y, "which keeps the meaning better? (X / Y / same)": "", "note": ""})
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation
    widths = [4, 40, 45, 45, 45, 16, 30]
    for who in "AB":
        p = ROOT / "annotation" / f"pairwise_{who}.xlsx"
        if p.exists():
            print(f"skip {p} (exists)")
            continue
        with pd.ExcelWriter(p, engine="openpyxl") as xw:
            sheet.to_excel(xw, index=False, sheet_name="compare")
            ws = xw.sheets["compare"]
            for j, w in enumerate(widths):
                ws.column_dimensions["ABCDEFG"[j]].width = w
            for row in ws.iter_rows():
                for c in row:
                    c.alignment = Alignment(wrap_text=True, vertical="top")
            for c in ws[1]:
                c.font = Font(bold=True)
            fill = PatternFill("solid", fgColor="FFF2CC")
            for r in range(1, len(sheet) + 2):
                ws[f"F{r}"].fill = fill
                ws[f"G{r}"].fill = fill
            dv = DataValidation(type="list", formula1='"X,Y,same"', allow_blank=True)
            ws.add_data_validation(dv)
            dv.add(f"F2:F{len(sheet) + 1}")
            ws.freeze_panes = "B2"
    print(f"{len(key)} pairs; key in {OUT / 'pairwise_key.csv'}")


if __name__ == "__main__":
    main()
