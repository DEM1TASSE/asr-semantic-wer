# Context-aware semantic error profiling for ASR (11-751 project)

We split ASR errors into spans, have an LLM (the **teacher**, DeepSeek-V4.1-Flash) score how much each
error changes the meaning (severity 1–5, rubric in `annotation/rubric.md`), and then train a small model
(the **student**, DistilBERT) to predict the same severity. Severity also gives a severity-weighted WER
(Semantic-WER).

**Status (Nov 17):** all data for three ASR systems is labeled by the teacher and in git; fixed splits are
ready. Next: train and evaluate the student (section 3) and annotate the 200-error human test set.

---

## November 21 checkpoint

[Experiment results and project slides](docs/experiment_update_2026-11-21.md) cover the local DistilBERT objective comparison, four-system AMI evaluation, and LibriSpeech spot check.

## 1. Data

### How the data was made (short; full details in `docs/data.md`)
1. **Utterances:** random utterances (≥ 5 words) from the AMI meeting corpus, spread evenly over meetings,
   using the official AMI train / dev / test split (no meeting appears in two splits).
2. **ASR:** three systems with different architectures transcribe the *same* utterances:
   Whisper large-v3 (encoder–decoder), wav2vec2-large (CTC), Parakeet-TDT-0.6b-v2 (transducer).
3. **Error spans:** each ASR output is aligned to the reference; neighbouring wrong words are merged into
   one error span (e.g. `[[agenda → hegender]]`).
4. **Teacher labels:** DeepSeek scores every span (severity 1–5) with the rubric `annotation/rubric.md`.
5. **Splits:** fixed id lists for training / tuning / testing the student (see "Splits" below).

| subset | AMI split | utterances | Whisper errors | wav2vec2 errors | Parakeet errors |
|---|---|---|---|---|---|
| train | train (29 meetings) | 6,000 | 7,030 | 11,754 | 5,246 |
| dev | validation (18 meetings) | 700 | 655 | 1,180 | 484 |
| test | test (16 meetings) | 700 (= 500 `test` + 200 `test_extra`) | 614 | 1,159 | 444 |

28,566 error spans in total, every one with a teacher label.

WER and Semantic-WER (%, same utterances for all systems; from `outputs/semwer_summary_*.json`):

| subset | system | WER | SemWER-lin | SemWER-hard | SemWER-max |
|---|---|---|---|---|---|
| test | Parakeet-TDT | 7.6 | 2.7 | 1.6 | 8.6 |
| | Whisper | 11.6 | 3.4 | 1.4 | 8.8 |
| | wav2vec2 | 22.5 | 10.3 | 7.3 | 30.5 |
| dev | Parakeet-TDT | 8.8 | 3.8 | 2.6 | 11.5 |
| | Whisper | 12.7 | 4.6 | 2.7 | 11.1 |
| | wav2vec2 | 23.9 | 11.2 | 8.1 | 30.9 |
| train | Parakeet-TDT | 10.3 | 3.7 | 2.2 | 11.8 |
| | Whisper | 15.3 | 4.8 | 2.3 | 12.1 |
| | wav2vec2 | 28.1 | 13.2 | 9.6 | 36.6 |

Parakeet has a third less WER than Whisper, but about the same severity-weighted error (SemWER-hard):
Whisper's extra errors are mostly harmless deletions of fillers and repetitions.

### What each file is for
**You only need the bold rows to train and evaluate the student.**

| file | what it is | needed for the student? |
|---|---|---|
| **`data/splits/*.txt`** | which errors go into train / dev / test (one `error_id` per line) | **yes** |
| **`outputs/errors*.jsonl`** | one line per error: the error, its sentence, context | **yes** (model input) |
| **`outputs/llm_annotations_deepseek-v4-1-flash_v2.4.jsonl`** | one line per error: teacher severity 1–5 + type + rationale | **yes** (target) |
| **`annotation/human_pilot_{A,B}.xlsx`** | our two human labels for 50 errors (Whisper + wav2vec2) | **yes** (human eval) |
| `annotation/human_test_{A,B}.xlsx` | blank sheets for the 200-error human test set (to be annotated) | later |
| `data/splits/manifest.json` | size, systems, severity counts of every split | for checking |
| `data/eval_subset.jsonl`, `data/subset_*.jsonl` | the sampled utterances (meeting, speaker, time, reference text) | no |
| `outputs/hyp_*.jsonl` | raw ASR output per utterance and system | no |
| `outputs/wer_summary*.json`, `outputs/semwer_summary*.json` | WER and Semantic-WER per subset | no (results) |
| `outputs/fig_*.png`, `cases*.md`, `category_by_system*.csv`, `error_form_by_system*.csv` | figures, example errors, error-type tables | no (analysis) |
| `outputs/human_test_sampling.csv` | how each human-test error was sampled (not shown to annotators) | no |
| `outputs/agreement*.csv`, `pilot_ids.txt`, `pilot_sampling.csv` | agreement on the 50 pilot errors | no |
| other `outputs/llm_annotations_*.jsonl`, `outputs/rubric_snapshots/` | earlier LLM / rubric comparisons on the 50 pilot errors | **no, ignore** |
| `annotation/rubric.md` (`rubric_zh.md` = Chinese) | the severity rubric | to understand the labels |

File names: no suffix = the original 500-utterance test set; `_test_extra`, `_dev`, `_train` = the other
subsets. System names in the data: `whisper-large-v3`, `wav2vec2-large`, `parakeet-tdt-0.6b-v2`.

**Paths on Delta** (not in git; only needed to re-run ASR):
- audio: `/work/hdd/bjdh/dwang30/semwer/data/eval_subset.parquet` (test) and
  `/work/hdd/bjdh/dwang30/semwer/data/subset_{test_extra,dev,train}.parquet`
- HuggingFace cache: `/work/hdd/bjdh/dwang30/semwer/hf_cache` (override the root with `SEMWER_WORK`)
- NeMo environment for Parakeet: `/work/hdd/bjdh/dwang30/semwer/venv_nemo`

### Reading the data
Errors and labels are joined on `error_id` (`<system>|<audio_id>|<k>`):
```python
import json, sys; sys.path.insert(0, "src")
from common import load_errors, single_error_hyp
errors = load_errors()                                   # all 28,566 error spans, keyed by error_id
labels = {r["error_id"]: r for r in map(json.loads, open("outputs/llm_annotations_deepseek-v4-1-flash_v2.4.jsonl"))}
train_ids = open("data/splits/train_all3_9k.txt").read().split()
e, y = errors[train_ids[0]], labels[train_ids[0]]["severity"]
```
Error fields you need: `ref_marked` (reference with the error marked `[[ref words → asr words]]`, `∅` =
nothing), `single_error_hyp(e)` (the ASR sentence with only this error, what the teacher compared),
`context_before` (previous 3 utterances), `system`, `meeting_id`.
Label fields: `severity` (1–5), `content_type`, `flag`, `rationale`.

### Splits for the student (`data/splits/`)
**How they were made** (`src/make_splits.py`, seed 751):
- Dropped: errors the teacher flagged `ref_issue` (the reference transcript itself is wrong), and the 50
  human-pilot errors (they are only used in `pilot_human`).
- **"Balanced" = the same number of errors from each ASR system**, drawn at random. It is *not* balanced
  by severity. Why: on the same utterances wav2vec2 makes ~2× more errors than Whisper and ~2.5× more
  than Parakeet; pooling all errors would let wav2vec2 dominate training and the "all" score. The `*_all`
  files keep every error (natural mix); report them too.
- **All main training sets have the same size (9,000)**, so All-3 and leave-one-out are comparable.
- Sampling is spread over meetings in proportion to their size, and **nested**: All-3 1.5k ⊂ 3k ⊂ 6k ⊂ 9k;
  `train_only_<system>_4.5k` is inside both leave-one-out sets that contain that system.

| file | Whisper + wav2vec2 + Parakeet | use |
|---|---|---|
| `train_all3_9k` | 3,000 + 3,000 + 3,000 | **main model** |
| `train_loo_no_whisper_9k` | 0 + 4,500 + 4,500 | leave Whisper out |
| `train_loo_no_wav2vec2_9k` | 4,500 + 0 + 4,500 | leave wav2vec2 out |
| `train_loo_no_parakeet_9k` | 4,500 + 4,500 + 0 | leave Parakeet out |
| `train_all3_1.5k`, `_3k`, `_6k` | 500 / 1,000 / 2,000 each | learning curve |
| `train_only_{whisper,wav2vec2,parakeet}_4.5k` | 4,500 of one system | optional (if time) |
| `train_all` | 6,805 + 11,581 + 5,024 | only if 9k is clearly not enough |
| `dev_balanced` | 400 + 400 + 400 | early stopping, hyper-parameters |
| `dev_all` | 641 + 1,167 + 467 | optional |
| `test_balanced` | 400 + 400 + 400 | **main test** (teacher labels) |
| `test_all` | 574 + 1,122 + 432 | test, natural mix |
| `pilot_human` | 21 + 29 + 0 | test against **human** labels (mean of A and B) |
| `human_test` | 67 + 67 + 66 | human test set (labels coming; see section 4) |

**Severity is not balanced** (natural distribution, so test scores reflect reality): in `train_all3_9k`
severity 1/2/3/4/5 = 5,490 / 1,326 / 1,419 / 705 / 60. If the model rarely predicts 4–5, re-weight or
over-sample high severities **in training only**; never change dev / test.

---

## 2. Setup on Delta
```bash
git clone https://github.com/DEM1TASSE/asr-semantic-wer.git && cd asr-semantic-wer
pixi install                       # environment from pixi.lock (torch, transformers, sklearn, ...)
pixi run python -c "import sys; sys.path.insert(0,'src'); from common import load_errors; print(len(load_errors()))"   # 28566
```
GPU account: `bjdh-delta-gpu`. Our fair-share is low, so normal partitions can queue for hours; the
`*-interactive` partitions (max 1 h) usually start within minutes (`sbatch -p gpuA100x4-interactive ...`).
No API key is needed for the student experiments (the teacher labels are already in git).
For Sentence-BERT: `pixi add --pypi sentence-transformers`.

---

## 3. Experiments to run (student)

> **There is no ready-to-use training script yet; please write your own following this section.**
> `src/train_severity.py` is an **old version, do not use it**: it reads only the first 500-utterance
> test set, makes its own random split, and ignores `data/splits/`, Parakeet, and the single-error
> sentence. Load data as in "Reading the data" (section 1) and use the split files below.

**Model:** `distilbert-base-uncased`, one regression output (severity 1–5, MSE), predictions clipped to [1, 5].
**Input:** reference with the error marked (`ref_marked`) + the ASR sentence with only this error
(`single_error_hyp`) + previous context (`context_before`). Max length 256 is enough.
**Model selection:** pick the epoch / learning rate on `dev_balanced` only. Never use test for decisions.
**Seeds:** 3 seeds per configuration; report mean ± std.

Severity measures how much the *meaning* changes, which does not depend on which ASR system made the error.
So we do not train every combination of systems; we train on all three, and leave one system out to test
generalization to an unseen ASR system.

### 3.1 Required, in this order
| # | train on | evaluate on | question |
|---|---|---|---|
| 1 | `train_all3_9k` | `test_balanced`, `test_all`, `pilot_human` | main result |
| 2 | `train_loo_no_whisper_9k` | same | can it score errors of an ASR system it never saw? |
| 3 | `train_loo_no_wav2vec2_9k` | same | (compare the held-out system's score with run 1) |
| 4 | `train_loo_no_parakeet_9k` | same | |
| 5 | `train_all3_1.5k`, `_3k`, `_6k` | `test_balanced` | learning curve (with run 1 as 9k) |

Leave-one-out is read like this: for run 2, compare its score **on Whisper errors** with run 1's score on
Whisper errors. Same training size, so the only difference is whether Whisper errors were seen.

### 3.2 Baselines (required, no fine-tuning)
- **Majority:** always predict the most frequent train severity (= 1).
- **Mean:** always predict the train mean severity.
- **Sentence-BERT (off-the-shelf):** cosine similarity between `ref` (reference) and `single_error_hyp`
  with a pretrained Sentence-BERT model (e.g. `all-MiniLM-L6-v2`), mapped to 1–5 by isotonic regression fit
  on `dev_balanced`.

### 3.3 Optional (if time)
- `train_only_{whisper,wav2vec2,parakeet}_4.5k`: train on one system, test on the other two.
- `train_all` if run 1's learning curve is still rising at 9k.

### 3.4 Metrics and outputs
Report on every test set **separately for Whisper, wav2vec2, Parakeet, and all**:
**QWK** (quadratic weighted kappa on rounded predictions), **Spearman**, **MAE**, **within-1**
(|pred − gold| ≤ 1), exact match. Against the teacher on `test_*`; against the human mean on `pilot_human`
(and later `human_test`), also reporting teacher vs human on the same items.

Please save per-error predictions (`error_id`, `pred`) for every test set and run, so we can compute
Semantic-WER from student scores and do error analysis.

Result tables to fill:
- **A (main):** rows = baselines + run 1; columns = QWK / Spearman / MAE on `test_balanced` per system + all.
- **B (leave-one-out):** rows = runs 1–4; columns = QWK on each system; mark the held-out cell.
- **C (learning curve):** 1.5k, 3k, 6k, 9k → QWK on `test_balanced`.
- **D (humans):** student vs human, teacher vs human on `pilot_human` (later `human_test`).

---

## 4. Other work in progress
- **Human test set (200 errors):** `annotation/human_test_{A,B}.xlsx`, ids in `data/splits/human_test.txt`.
  From AMI test meetings only (no overlap with train / dev), no pilot errors, 67 / 67 / 66 per system,
  ~70% random + ~30% chosen by surface features (digits / negation words, long spans, substitutions),
  never by the teacher's labels. Both annotators fill it independently, then discuss gaps ≥ 2.
- **Smaller teacher LLMs:** run e.g. Qwen3-4B / 8B with the same prompt (vLLM on Delta) on the human test
  set and compare their agreement with humans to DeepSeek's.
- **(Optional, not started) sentence-level check:** no separate sentence-level model is planned, since a
  sentence score is aggregated from span scores. If time allows, rate 100–150 utterances (1–5, meaning
  preserved) by hand and test whether span-aggregated scores match them better than WER and Sentence-BERT
  similarity. Details in `docs/plan.md`.

---

## Pipeline that produced the data (for reference)
| step | command |
|---|---|
| sample utterances | `pixi run python src/prepare_ami.py --subset {test,test_extra,dev,train}` |
| ASR: Whisper, wav2vec2 | `sbatch slurm/asr.sbatch <subset>` or `slurm/asr_shard.sbatch <subset> <k> <n>` |
| ASR: Parakeet (NeMo env) | `sbatch -p <partition> slurm/asr_parakeet.sbatch <subset> [<subset>:<k>:<n> ...]` |
| align + error spans | `pixi run python src/align.py --subset <subset>` |
| teacher labels (needs `AZURE_API_KEY` in `.env`, never commit it) | `pixi run python src/annotate_llm.py --backend azure_v1 --model deepseek-v4-1-flash --ids subset:<subset> --tag deepseek-v4-1-flash_v2.4 --workers 8` |
| Semantic-WER, figures | `pixi run python src/semwer.py --subset <subset> [<subset> ...]` |
| student splits | `pixi run python src/make_splits.py` |
| human test sheets | `pixi run python src/make_human_test.py` |

Docs: `docs/plan.md` (full plan), `docs/data.md` (how the data was made), `annotation/rubric.md` (rubric).
