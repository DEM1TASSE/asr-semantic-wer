# How the data was made (details)

Short version and file guide: `README.md`, section 1. This file records the exact procedure so the data
can be described in the report and reproduced.

## 1. Utterances (`src/prepare_ami.py`)
- Corpus: AMI meeting corpus, individual headset microphones (IHM), HuggingFace `edinburghcstr/ami`,
  config `ihm`, with the corpus' own utterance segmentation (oracle segmentation).
- Official AMI partition: train / validation (our "dev") / test. No meeting is in two splits.
- Kept utterances with ≥ 5 words after normalization (drops backchannels like "yeah okay").
- Sampling, seed 751: shuffle all eligible utterances, then take up to `n / #meetings` per meeting, so
  every meeting contributes; if this gives fewer than `n`, the rest is filled at random.

| subset | source | utterances | meetings | per meeting |
|---|---|---|---|---|
| `test` | AMI test | 500 | 16 | ~31 |
| `test_extra` | AMI test, excluding the 500 above | 200 | 16 | 12–14 |
| `dev` | AMI validation | 700 | 18 | 38–41 |
| `train` | AMI train, 8 of the 42 HuggingFace shards (29 meetings, 50 speakers) | 6,000 | 29 | 51–270 |

- Context for each utterance: the previous 3 and the next 1 utterance of the same meeting (all speakers,
  reference transcripts, ordered by start time).
- Recorded per utterance: audio id, meeting, speaker, begin/end time, raw and normalized reference,
  AMI split, seed.

## 2. ASR (`src/run_asr.py`)
| system | HuggingFace model | decoding |
|---|---|---|
| Whisper | `openai/whisper-large-v3` | beam 5, fp16, language English |
| wav2vec2 | `facebook/wav2vec2-large-960h-lv60-self` | greedy CTC |
| Parakeet-TDT | `nvidia/parakeet-tdt-0.6b-v2` (NeMo) | greedy TDT; CUDA-graph decoder disabled (it crashed on train) |

All systems transcribe exactly the same utterances. Run on Delta A40 / A100 GPUs. Parakeet was added on
Nov 16 after TA feedback (a third architecture: encoder–decoder, CTC, transducer); it runs in a separate
NeMo environment `/work/hdd/bjdh/dwang30/semwer/venv_nemo`. Adding it did not change any existing
Whisper / wav2vec2 error span or id (checked).

| subset | Whisper WER / errors | wav2vec2 WER / errors | Parakeet WER / errors |
|---|---|---|---|
| test (500) | 11.7% / 447 | 22.2% / 840 | 7.6% / 324 |
| test_extra (200) | 11.5% / 167 | 23.2% / 319 | 7.6% / 120 |
| dev (700) | 12.7% / 655 | 23.9% / 1,180 | 8.8% / 484 |
| train (6,000) | 15.3% / 7,030 | 28.1% / 11,754 | 10.3% / 5,246 |

## 3. Normalization, alignment, error spans (`src/align.py`, `src/common.py`)
- References and ASR outputs get the same normalization: Whisper's `EnglishTextNormalizer`, plus fixes
  for AMI conventions (dotted acronyms "t. v." → "tv"; "oh"/"o" not turned into the digit 0; currency and
  percent symbols spelled out). Without these fixes Whisper's WER was ~2 points too high.
- Word alignment with `jiwer`; WER = (S + D + I) / reference words.
- **Error span** = a run of adjacent substitutions / deletions / insertions merged into one unit (meaning
  is a property of a phrase, not of single words). Each span gets an `error_id`
  `<system>|<audio_id>|<k>`, deterministic, so re-running gives the same ids.
- `ref_marked` shows the span in the reference as `[[ref words → asr words]]` (`∅` = nothing).
- **Single-error sentence** (`common.single_error_hyp`): the reference with only this span replaced by
  the ASR output, i.e. the ASR sentence as if every other error were fixed. The teacher compares the
  reference with this sentence, so other errors in the same utterance do not affect the score.

## 4. Teacher labels (`src/annotate_llm.py`)
- Model: DeepSeek-V4.1-Flash on Azure; temperature 0; max output 16,000 tokens (it reasons before
  answering); JSON output.
- Prompt: system message = the full rubric `annotation/rubric.md` + output format; user message =
  context, marked span, edit operation, reference sentence, single-error ASR sentence. The prompt text is
  in `src/annotate_llm.py` (`SYSTEM`, `USER`) and in the checkpoint report appendix.
- Output per span: `severity` 1–5 (how much meaning is changed, lost, or added), `content_type`,
  `error_form`, `flag` (`ref_issue`, `crosstalk`, `uncertain`, `multi_issue`), one-sentence `rationale`.
- Every label also stores: model, rubric file and hash, prompt hash, decoding settings, timestamp, token
  usage. All 28,566 labels share the same rubric and prompt hash.
- Rate-limited (HTTP 429) requests were retried until every span had a label; duplicate or corrupted
  lines from parallel writes were removed, leaving exactly one label per span.
- Cost: ~83M input + ~19M output tokens, about $48 in total (third-party price estimate).
- Spot check (30 random train labels, 6 per severity, plus all severity-5 labels): consistent with the
  rubric; the main bias is over-scoring an inserted "not" that does not really flip the meaning (e.g. tag
  questions "are we → are not we"). Not corrected; the human test will measure teacher error.

## 5. Human pilot (50 errors; `annotation/human_pilot_{A,B}.xlsx`)
- 50 test errors: 35 random + 15 targeted (5 with digits or negation, 5 long spans, 5 substitutions);
  list in `outputs/pilot_sampling.csv`.
- Both of us labeled all 50 independently with the rubric. Agreement: Krippendorff's α (ordinal) 0.79,
  quadratic weighted κ 0.84, Spearman 0.83, exact 64%, within one point 96%.
- One entry error by annotator A was corrected (item 1: 1 → 5); the original is in `annotation/raw/`.
  Items with a gap ≥ 2 were discussed (`docs/pilot_adjudication.md`); labels were otherwise not changed.
- These 50 errors were used to choose the rubric wording, the prompt and the teacher model, so they are
  excluded from all train / dev / test splits and reported separately.

## 6. Student splits (`src/make_splits.py`, seed 751)
- Pool: every labeled span, minus `ref_issue` spans and the 50 pilot errors.
- Per split and system, spans are put in a random order in which every prefix is proportional to meeting
  size; sets are prefixes of this order, so they are stratified by meeting and nested.
- "Balanced" = equal number of errors per ASR system (not per severity).
- Main training sets all have 9,000 errors: All-3 = 3 × 3,000; leave-one-system-out = 2 × 4,500 (so the
  held-out system is the only difference). Learning curve: All-3 1.5k / 3k / 6k. Optional single-system
  sets: 4,500 (inside the leave-one-out sets). Dev and test balanced sets: 400 per system (Parakeet has
  only ~440–480 usable errors there).
- The script checks that train, dev and test share no meeting. Counts per split: `data/splits/manifest.json`.

## 7. Human test set (`src/make_human_test.py`, seed 751)
- 200 errors from AMI test meetings only (subsets `test` + `test_extra`), so no overlap with train or dev;
  the 50 pilot errors are excluded; if two systems made the identical error on the same utterance only
  one copy can be drawn.
- 67 Whisper / 67 wav2vec2 / 66 Parakeet; per system ~70% random + ~30% targeted by surface features
  (7 digits/negation, 7 long spans ≥ 3 words, 6 substitutions). Never selected by teacher labels.
  200 items from all 16 test meetings. Sampling type per item: `outputs/human_test_sampling.csv`.
- Sheets `annotation/human_test_{A,B}.xlsx` (same layout as the pilot; ids in `data/splits/human_test.txt`).
