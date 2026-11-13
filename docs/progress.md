# Progress log

Newest first. Record what was done, the numbers, and anything surprising.

## 2026-11-12
**Pilot agreement (rubric v2.3, 50 items) and adjudication of the items with a gap of 2 or more.**

- A's #1 was an entry error (1 → 5, confirmed by Demi); corrected in `human_pilot_A.xlsx` with a note.
  The original export stays in `annotation/raw/human_pilot_A_original.csv`.
- Human A vs B, severity: α (ordinal) 0.789, QWK 0.837, Spearman 0.831, exact 64%, within-1 96%, MAE 0.40.
  Mean severity A 1.94, B 2.14; B is higher on 14 items, A on 4. Most of the gap is recognizable misspellings
  (`trend → trand`, `cover → cofer`), which B scores one point higher.
- content_type A vs B: exact 62%, nominal α 0.49. Mostly disfluency / function_word / content_word on
  repetitions and false starts; the ordered content_type rules in the v2.4 draft address these.
- Adjudication (`docs/pilot_adjudication.md`): #1 = 5; #31 = 4 + crosstalk; #6 (`scroll → scrawl`) kept as a
  legitimate subjective disagreement (A 1, B 3; single label 2 + uncertain). Gaps of 1 are not adjudicated.
- LLMs with the single-error prompt (dev set: the same 50 items were used to choose the prompt and model, so these
  numbers are optimistic):

| model | α vs A | α vs B | Spearman vs human mean | within-1 vs human mean | n |
|---|---|---|---|---|---|
| deepseek-v4-1-flash | 0.745 | 0.720 | 0.763 | 88% | 50 |
| gpt-4o | 0.767 | 0.772 | 0.826 | 83% | 46 (4 rate-limit failures) |
| gpt-5.4-mini | 0.615 | 0.507 | 0.578 | 78% | 50 |

- Decisions for v2.4: misspellings are scored 1–3 by how much they interfere with understanding (no fixed
  "clear = 1 / effortful = 2" cut-off); repetitions and abandoned starts are 1, but not automatically: judge the
  full meaning of the original (e.g. #43); in a self-repair the repaired part is content; inserted speech from
  another speaker is scored by what it adds to this utterance, and flagged `crosstalk`.

## 2026-11-11
**Yixiang completed all 50 official human-pilot items independently under rubric v2.3.**

- Exported the browser's completed annotations to `annotation/human_pilot_B.xlsx`; this submission uses B for Yixiang. Annotator A's file is unchanged.
- Preserved the original JSON export (including separate legacy backups) in `annotation/submissions/yixiang_pilot_v23_2026-11-11.json`.
- Verified all 50 IDs and their order against `outputs/pilot_ids.txt`; severity and content_type are complete, and severity, content_type, flags, and notes match the JSON export exactly.
- Severity counts: 1 = 20, 2 = 12, 3 = 10, 4 = 7, 5 = 1. These are the original independent ratings, with no post-discussion edits. Inter-annotator agreement has not been computed for this submission.

## 2026-10-29
**Pipeline built and run end-to-end through alignment.**

ASR baselines (500 utts, 6.9k ref words):

| system | WER | S | D | I | error spans |
|---|---|---|---|---|---|
| Whisper large-v3 | 11.7 | 2.8 | 8.0 | 0.8 | 447 |
| wav2vec2-large | 22.2 | 11.7 | 7.7 | 2.8 | 840 |

Findings
- Normalization bugs inflated Whisper WER from 11.7 → 13.4: AMI vs ASR spelling variants (`cause`/`because`,
  `t. v.`/`tv`, `alright`), Whisper normalizer reading "oh" as 0 and "ten o'clock" as "100 clock",
  currency symbols being dropped. Fixed in `src/common.py`.
- Over half of Whisper's errors are deletions of repetitions / false starts (it "cleans up" disfluencies),
  which WER counts as errors but barely change meaning.
- wav2vec2 errors are dominated by nonword misspellings and garbled spans.
- Some AMI references are themselves wrong (e.g. `on a val of 76` where Whisper's `out of all 76` is right) → `flag=ref_issue`.

LLM annotation v0 (rubric v0, gpt-5.4-mini, before normalization fixes; archived, not used):
Semantic-WER (hard) Whisper 3.1% vs wav2vec2 10.2% — the gap widens from 1.7× (WER) to 3.3×.
Labels were inconsistent on nonwords (1–5 for similar cases) and misread normalization artifacts →
rubric rewritten as v1 from ~200 manually read samples.
