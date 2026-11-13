# Context-aware semantic error profiling for ASR (11-751 project)

We split ASR errors into spans, have an LLM (the **teacher**, DeepSeek-V4.1-Flash) score how much each
error changes the meaning (severity 1–5, rubric in `annotation/rubric.md`), and then train a small model
(the **student**, DistilBERT) to predict the same severity. Severity also gives a severity-weighted WER
(Semantic-WER).

**Status (Nov 13):** all data below is labeled by the teacher and pushed. Next: train and evaluate the
student (section 3).

---

## 1. Data

### Where things are
| what | path | in git? |
|---|---|---|
| utterance lists (audio id, meeting, speaker, times, raw + normalized reference) | `data/eval_subset.jsonl` (test), `data/subset_{test_extra,dev,train}.jsonl` | yes |
| ASR outputs | `outputs/hyp_{whisper-large-v3,wav2vec2-large}[_<subset>].jsonl` | yes |
| **error spans** (one line per error, with context) | `outputs/errors.jsonl` (test), `outputs/errors_{test_extra,dev,train}.jsonl` | yes |
| **teacher labels** (one line per error) | `outputs/llm_annotations_deepseek-v4-1-flash_v2.4.jsonl` | yes |
| **fixed splits for the student** (one error_id per line) | `data/splits/*.txt`, summary `data/splits/manifest.json` | yes |
| human labels on 50 pilot errors (two annotators) | `annotation/human_pilot_{A,B}.xlsx` | yes |
| audio (only needed to re-run ASR) | `/work/hdd/bjdh/dwang30/semwer/data/*.parquet` on Delta | no |
| HuggingFace cache | `/work/hdd/bjdh/dwang30/semwer/hf_cache` (override with `SEMWER_WORK`) | no |

Join errors and labels on `error_id` (`<system>|<audio_id>|<k>`). In Python:
```python
from common import load_errors          # src/common.py: all error spans, keyed by error_id
errors = load_errors()
labels = {r["error_id"]: r for r in map(json.loads, open("outputs/llm_annotations_deepseek-v4-1-flash_v2.4.jsonl"))}
```

Useful fields of an **error** record: `system`, `subset`, `meeting_id`, `ref` (normalized reference),
`hyp` (full ASR output), `ref_marked` (reference with the error marked as `[[ref words → asr words]]`,
`∅` = nothing), `context_before` (previous 3 utterances, all speakers), `context_after` (next one),
`ref_start/ref_end/hyp_span`. The "ASR sentence with only this error" that the teacher saw is
`common.single_error_hyp(e)`.

Useful fields of a **label** record: `severity` (1–5), `content_type`, `error_form`, `flag`
(`ref_issue`, `crosstalk`, `uncertain`, `multi_issue`), `rationale`.

### What the data is
AMI meeting corpus (IHM, oracle segmentation, utterances with ≥ 5 words), official AMI splits, so train /
dev / test never share a meeting. Both ASR systems (Whisper large-v3, wav2vec2-large-960h-lv60-self)
decode the same utterances; every error span is labeled.

| subset | AMI split | utterances | Whisper errors | wav2vec2 errors |
|---|---|---|---|---|
| train | train (29 meetings) | 6,000 | 7,030 | 11,754 |
| dev | validation (18 meetings) | 700 | 655 | 1,180 |
| test (`test` + `test_extra`) | test (16 meetings) | 700 | 614 | 1,159 |

WER / Semantic-WER per subset: `outputs/semwer_summary_{train,dev,test+test_extra}.json`.

### Splits for the student (`data/splits/`, built by `src/make_splits.py`, seed 751)
Spans flagged `ref_issue` (the reference transcript itself is wrong) and the 50 pilot items are removed.
Samples are stratified by meeting and **nested** (1K ⊂ 2.5K ⊂ 5K ⊂ 10K; Whisper-5K and wav2vec2-5K are the two
halves of Mixed-10K). Same number of errors per system, so the student does not just see more wav2vec2.

| file | size | use |
|---|---|---|
| `train_whisper_5k` | 5,000 Whisper | train |
| `train_wav2vec2_5k` | 5,000 wav2vec2 | train |
| `train_mixed_5k` | 2,500 + 2,500 | train |
| `train_mixed_10k` | 5,000 + 5,000 | train |
| `train_mixed_1k`, `train_mixed_2.5k` | 500+500, 1,250+1,250 | learning curve |
| `train_all` | 6,805 + 11,581 | only if 10K is clearly not enough |
| `dev_balanced` | 500 + 500 | early stopping, hyper-parameters |
| `dev_all` | 641 + 1,167 | optional |
| `test_balanced` | 500 + 500 | **main test** (teacher labels) |
| `test_all` | 574 + 1,122 | test, natural distribution |
| `pilot_human` | 50 | test against **human** labels (mean of A and B) |

**What "balanced" means:** the same number of errors from each **ASR system** (e.g. `test_balanced` =
500 Whisper + 500 wav2vec2). It is *not* balanced by severity. Why: on the same utterances wav2vec2
makes about twice as many errors as Whisper, so pooling all errors would let wav2vec2 dominate both
training and the "all" test score. The `*_all` files keep the natural distribution; report them too.

**Severity is not balanced** (natural distribution, so test scores reflect reality): in
`train_mixed_10k` 1/2/3/4/5 = 6,058 / 1,347 / 1,659 / 880 / 56. If the model rarely predicts 4–5,
re-weight or over-sample high severities **in training only**; never change the dev / test sets.

---

## 2. Setup on Delta
```bash
git clone https://github.com/DEM1TASSE/asr-semantic-wer.git && cd asr-semantic-wer
pixi install                       # environment from pixi.lock (torch, transformers, sklearn, ...)
pixi run python -c "import sys; sys.path.insert(0,'src'); from common import load_errors; print(len(load_errors()))"   # 22392
```
GPU account: `bjdh-delta-gpu`. Our fair-share is low, so normal partitions can queue for hours; the
`*-interactive` partitions (max 1 h, 2 jobs per user each) usually start within minutes.
No API key is needed for the student experiments (the teacher labels are already in git).

---

## 3. Experiments to run (student)

**Model:** `distilbert-base-uncased`, one regression output (severity 1–5, MSE), predictions clipped to [1, 5].
**Input:** reference with the error marked (`ref_marked`) + the ASR sentence with only this error
(`single_error_hyp`) + previous context (`context_before`). Max length 256 is enough.
**Model selection:** pick the epoch / learning rate on `dev_balanced` only. Never look at test for decisions.
**Seeds:** 3 seeds per configuration; report mean ± std.
Start with the 5K / 10K sets; add `train_all` only if Mixed-10K is clearly better than Mixed-5K.

### 3.1 Main runs (required)
| # | train on | question it answers |
|---|---|---|
| 1 | `train_whisper_5k` | in-domain vs cross-ASR (test on both systems) |
| 2 | `train_wav2vec2_5k` | in-domain vs cross-ASR |
| 3 | `train_mixed_5k` | mixing both systems at the same size |
| 4 | `train_mixed_10k` | more data (vs #3) |
| 5 | `train_mixed_1k` | learning curve |
| 6 | `train_mixed_2.5k` | learning curve |

### 3.2 Baselines (required, no training)
- **Majority:** always predict the most frequent train severity (= 1).
- **Mean:** always predict the train mean severity.
- (optional) **Embedding similarity:** cosine similarity of Sentence-BERT embeddings of `ref` vs
  `single_error_hyp`, mapped to 1–5 with isotonic regression fit on train.

### 3.3 Evaluate every model on
- `test_balanced` and `test_all`, against teacher severity, **separately for Whisper, wav2vec2, and all**;
- `pilot_human`, against the human mean (and report teacher vs human on the same 50 for reference).

Metrics: **QWK** (quadratic weighted kappa on rounded predictions), **Spearman**, **MAE**, **within-1**
(|pred − gold| ≤ 1), exact match.

### 3.4 Result tables to fill
Table A (main): rows = baselines + runs 1–4; columns = QWK / Spearman / MAE on test_balanced for
Whisper, wav2vec2, all. Table B (learning curve): 1K, 2.5K, 5K, 10K (mixed) → QWK on test_balanced.
Table C: student vs human and teacher vs human on `pilot_human`.

Please save per-error predictions (`error_id`, `pred`) for every test set, so we can compute
Semantic-WER from student scores and do error analysis.

### Later (not now)
- 200-item human test set (100 per ASR, from AMI test, no pilot items); both of us annotate it.
- Semantic-WER with student scores vs teacher scores, per system.

---

## Pipeline that produced the data (for reference)
| step | command |
|---|---|
| sample utterances | `pixi run python src/prepare_ami.py --subset {test,test_extra,dev,train}` |
| ASR | `sbatch slurm/asr.sbatch <subset>` or `slurm/asr_shard.sbatch <subset> <k> <n>` |
| align + error spans | `pixi run python src/align.py --subset <subset>` |
| teacher labels (needs `AZURE_API_KEY` in `.env`, never commit it) | `pixi run python src/annotate_llm.py --backend azure_v1 --model deepseek-v4-1-flash --ids subset:<subset> --tag deepseek-v4-1-flash_v2.4 --workers 8` |
| Semantic-WER, figures | `pixi run python src/semwer.py --subset <subset> [<subset> ...]` |
| student splits | `pixi run python src/make_splits.py` |

Design choices: Whisper beam 5 / fp16; wav2vec2 greedy CTC; references and hypotheses normalized with
Whisper's `EnglishTextNormalizer` plus AMI fixes; adjacent S/D/I merged into one span; context = 3 previous
+ 1 next utterance. Docs: `docs/plan.md` (full plan), `annotation/rubric.md` (rubric; `rubric_zh.md` is
the Chinese translation).
