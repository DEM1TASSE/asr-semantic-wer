"""Sample utterances for a blind pairwise human check of WER vs Semantic-WER (60 items, no rubric).

Systems: Whisper, Parakeet-TDT, Qwen3-ASR 0.6B, Qwen3-ASR 1.7B (wav2vec2 is left out: it is clearly worse on
every metric). For a pair of systems on the same utterance, per-utterance scores are
  edits  = word errors (what WER counts)
  sem    = sum over spans of n_word_errors * (s - 1) / 4 with teacher severity s (ref_issue spans count 0)
Three item types, reported separately (types 1 and 2 are over-sampled on purpose):
  opposite (25): WER and Semantic-WER prefer different systems; from the three Whisper pairs.
  wer_only (25): different word-error counts, same Semantic-WER (WER prefers one, Semantic-WER sees a tie);
                 spread over all six pairs.
  random   (10): any utterance where the two outputs differ; all six pairs.
Each utterance is used at most once; identical outputs are skipped. Output order A/B is random.
Annotators see context, reference, output A and output B, and choose A / B / Same: which output keeps the
meaning of the reference better?
Outputs: annotation/pairwise_rater{1,2}.xlsx (identical blank sheets), outputs/pairwise_key.csv (hidden key).
"""
import itertools
import json
from collections import defaultdict

import numpy as np
import pandas as pd

from common import OUT, ROOT, load_errors, normalize, subset_paths

SEED = 751
SYSTEMS = ["whisper-large-v3", "parakeet-tdt-0.6b-v2", "qwen3-asr-0.6b", "qwen3-asr-1.7b"]
N = {"opposite": 25, "wer_only": 25, "random": 10}
TAG = "deepseek-v4-1-flash_v2.4"


def main():
    rng = np.random.default_rng(SEED)
    subsets = ["test", "test_extra"]
    meta = {u["audio_id"]: u for s in subsets for u in map(json.loads, open(subset_paths(s)["meta"]))}
    hyp = {}  # (system, audio_id) -> raw ASR output, for every utterance (also error-free ones)
    for s in subsets:
        for sysname in SYSTEMS:
            for h in map(json.loads, open(subset_paths(s)["hyp"](sysname))):
                hyp[(sysname, h["audio_id"])] = h["hyp"]
    labels = {r["error_id"]: r for r in map(json.loads, open(OUT / f"llm_annotations_{TAG}.jsonl"))}
    edits, sem = defaultdict(int), defaultdict(float)
    for i, e in load_errors(subsets).items():
        if e["system"] in SYSTEMS:
            lab = labels[i]
            edits[(e["system"], e["audio_id"])] += e["n_word_errors"]
            sem[(e["system"], e["audio_id"])] += (e["n_word_errors"] * (lab["severity"] - 1) / 4
                                                  * ("ref_issue" not in lab["flag"]))

    def kind(a, b, u):
        if normalize(hyp[(a, u)]) == normalize(hyp[(b, u)]):
            return None
        de, ds = edits[(a, u)] - edits[(b, u)], sem[(a, u)] - sem[(b, u)]
        if abs(ds) < 1e-9:
            ds = 0
        if de * ds < 0:
            return "opposite"
        if de != 0 and ds == 0:
            return "wer_only"
        return "other"

    pairs = list(itertools.combinations(SYSTEMS, 2))
    cand = defaultdict(list)  # type -> [(pair, utterance)]
    for a, b in pairs:
        for u in sorted(meta):
            k = kind(a, b, u)
            if k:
                cand["any"].append(((a, b), u))
                if k in ("opposite", "wer_only"):
                    cand[k].append(((a, b), u))
    used, picks = set(), []

    def take(pool, n, typ):
        order = [pool[j] for j in rng.permutation(len(pool))]
        got = []
        for p, u in order:
            if len(got) == n:
                break
            if u not in used:
                used.add(u)
                got.append((p, u, typ))
        return got

    opp = [c for c in cand["opposite"] if "whisper-large-v3" in c[0]]
    picks += take(opp, N["opposite"], "opposite")
    # wer_only: spread evenly over the six pairs
    per = [N["wer_only"] // len(pairs) + (1 if i < N["wer_only"] % len(pairs) else 0) for i in range(len(pairs))]
    for (pair, n) in zip(pairs, per):
        picks += take([c for c in cand["wer_only"] if c[0] == pair], n, "wer_only")
    picks += take(cand["any"], N["random"], "random")

    rows = []
    for (a, b), u, typ in picks:
        x, y = (b, a) if rng.random() < 0.5 else (a, b)
        pref = lambda vx, vy: "Same" if abs(vx - vy) < 1e-9 else ("A" if vx < vy else "B")
        rows.append({"type": typ, "pair": f"{a} vs {b}", "audio_id": u, "A_system": x, "B_system": y,
                     "A": hyp[(x, u)], "B": hyp[(y, u)],
                     "wer_prefers": pref(edits[(x, u)], edits[(y, u)]),
                     "semwer_prefers": pref(sem[(x, u)], sem[(y, u)]),
                     "A_edits": edits[(x, u)], "B_edits": edits[(y, u)],
                     "A_sem": round(sem[(x, u)], 2), "B_sem": round(sem[(y, u)], 2)})
    key = pd.DataFrame(rows).sample(frac=1, random_state=SEED).reset_index(drop=True)
    key.insert(0, "#", range(1, len(key) + 1))
    key.to_csv(OUT / "pairwise_key.csv", index=False)
    print(key.groupby(["type", "pair"]).size().to_string())
    print(f"{len(key)} items; candidates: opposite (Whisper pairs) {len(opp)}, wer_only {len(cand['wer_only'])}, "
          f"differing outputs {len(cand['any'])}")

    sheet = pd.DataFrame({"#": key["#"],
                          "context (previous utterances)": ["\n".join(meta[u]["context_before"]) for u in key.audio_id],
                          "reference (what was said)": [meta[u].get("ref_raw", meta[u]["ref"]) for u in key.audio_id],
                          "output A": key.A, "output B": key.B,
                          "which keeps the meaning better?": "", "note": ""})
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation
    for who in ("rater1", "rater2"):
        p = ROOT / "annotation" / f"pairwise_{who}.xlsx"
        if p.exists():
            print(f"skip {p} (exists, not overwriting)")
            continue
        with pd.ExcelWriter(p, engine="openpyxl") as xw:
            sheet.to_excel(xw, index=False, sheet_name="compare")
            ws = xw.sheets["compare"]
            for col, w in zip("ABCDEFG", [4, 40, 45, 45, 45, 18, 30]):
                ws.column_dimensions[col].width = w
            for row in ws.iter_rows():
                for c in row:
                    c.alignment = Alignment(wrap_text=True, vertical="top")
            for c in ws[1]:
                c.font = Font(bold=True)
            fill = PatternFill("solid", fgColor="FFF2CC")
            for r in range(1, len(sheet) + 2):
                ws[f"F{r}"].fill = fill
                ws[f"G{r}"].fill = fill
            dv = DataValidation(type="list", formula1='"A,B,Same"', allow_blank=True, showErrorMessage=True,
                                errorTitle="Choose A, B or Same", error="Please pick A, B or Same from the list.")
            dv.prompt, dv.promptTitle, dv.showInputMessage = "A, B or Same", "Which output keeps the meaning better?", True
            ws.add_data_validation(dv)
            dv.add(f"F2:F{len(sheet) + 1}")
            ws.freeze_panes = "B2"


if __name__ == "__main__":
    main()
