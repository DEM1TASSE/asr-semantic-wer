# When ASR Errors Change Meaning: Context-Aware Semantic Error Profiling for ASR

**11-751 / 18-781 course project, Fall 2026** · Demi Wang and Yixiang Dai

This is the complete project write-up in one file. It is meant as the single source for the final
presentation and for any web page built from it. Every number here comes from a file in this repository;
the source is given under each table. Slides:
[Google Slides deck](https://docs.google.com/presentation/d/1fPxfRMS1ULUFOe_jX2wZrmvL5IRw7Z4gVzmCTKqzP2c/edit).

---

## TL;DR

- **Problem.** Word error rate (WER) counts every wrong word the same. Dropping a repeated "can" and
  dropping a "not" both cost one word, but only one of them reverses the meaning.
- **What we built.** A pipeline that cuts ASR output into individual error spans, has an LLM (the
  *teacher*, DeepSeek-V4.1-Flash) score how much each error changes the meaning on a 1–5 rubric, and
  distils those labels into a small DistilBERT model (the *student*). Severity gives a severity-weighted
  WER, **Semantic-WER**.
- **Question 1: can we score errors by meaning better than existing metrics?** Yes. Against human labels
  the student reaches QWK 0.80, versus 0.58 for BERTScore and 0.64 for SemDist. On rank correlation with
  humans, SemDist is comparable (Spearman 0.78 vs. 0.76).
- **Question 2: does it change how we rank ASR systems?** Yes. On 700 AMI meeting utterances, Whisper
  large-v3 has a much higher WER than Parakeet-TDT and Qwen3-ASR 0.6B (11.6% vs. 7.6% / 8.2%, significant),
  but the same Semantic-WER (1.75% vs. 1.67% / 1.68%, not significant). Whisper's extra errors are almost
  all negligible: dropped repetitions, fillers and false starts.
- **Limits.** Qwen errors are scored by the student only; human labels cover 50 error spans; every student
  result is a single training seed.

---

## 1. Motivation

| | Reference | ASR output | WER | Meaning |
|---|---|---|---|---|
| Repeated word | We can **can** ship today. | We can ship today. | 20% | unchanged |
| Negation | We can **not** ship today. | We can ship today. | 20% | decision reversed |

Both examples lose one of five words, so WER scores them the same. A user of a meeting transcript would
not. We want an evaluation that weighs each error by how much it changes what the speaker meant, and we
want to know whether that weighting changes conclusions about which ASR system is better.

## 2. Research questions

1. **Scorer.** Can we score individual ASR errors by meaning more accurately than existing semantic
   metrics (BERTScore, SemDist)?
2. **Benchmark.** Does weighting errors by meaning change how we compare and rank ASR systems?

## 3. Related work

| Work | Idea | Difference from ours |
|---|---|---|
| SemDist (Kim et al., Interspeech 2021) | Distance between sentence embeddings of reference and hypothesis | One score per sentence; no per-error severity; no rubric |
| Semantic-WER (Roy, 2021; arXiv 2106.02016) | Puts semantic information into word-error evaluation | We weight each aligned error span by a learned severity |
| LASER (Parulekar and Jyothi, EMNLP 2025) | LLM rubric scores edits; a smaller model learns edit penalties | Closest to ours; we use meeting context, a 5-level meaning rubric, human agreement checks, and compare against BERTScore / SemDist |
| BERTScore (Zhang et al., ICLR 2020) | Token-level similarity of contextual embeddings | Used here as a training-free baseline |

## 4. Data

**Corpus.** AMI meeting corpus, individual headset microphones (IHM), oracle utterance segmentation
(HuggingFace `edinburghcstr/ami`, config `ihm`). Utterances with at least 5 words after normalization.
The official AMI partition is kept, so train, dev and test never share a meeting.

| Subset | AMI split | Meetings | Utterances | Use |
|---|---|---:|---:|---|
| train | train (8 of 42 shards) | 29 | 6,000 | student training |
| dev | validation | 18 | 700 | checkpoint selection, baseline calibration |
| test | test (500 `test` + 200 `test_extra`) | 16 | 700 | all reported results |

Each utterance also stores its context: the previous 3 and next 1 utterances of the same meeting.

**Two evaluation units answer the two questions.**
- *Recognizer benchmark* (question 2): the same 700 test utterances for every ASR system.
- *Severity scorer* (question 1): error spans, balanced by ASR system so that wav2vec2 (which makes about
  twice as many errors) does not dominate.

| Student split | Whisper + wav2vec2 + Parakeet | Purpose |
|---|---|---|
| `train_all3_9k` | 3,000 + 3,000 + 3,000 | training |
| `dev_balanced` | 400 + 400 + 400 | checkpoint selection (by MAE), isotonic calibration of baselines |
| `test_balanced` | 400 + 400 + 400 | main test against the teacher |
| `test_all` | 574 + 1,122 + 432 | all usable test spans (natural mix) |
| `pilot_human` | 21 + 29 + 0 | test against human labels |

Spans the teacher flagged `ref_issue` (the reference transcript itself is wrong) and the 50 pilot spans
are excluded from training, dev and test. Severity in `train_all3_9k` is skewed toward harmless errors:
levels 1/2/3/4/5 = 5,490 / 1,326 / 1,419 / 705 / 60.

Sources: `docs/data.md`, `data/splits/manifest.json`, `src/prepare_ami.py`, `src/make_splits.py`.

## 5. ASR systems

| System | Architecture | Model | Decoding |
|---|---|---|---|
| Whisper large-v3 | encoder–decoder | `openai/whisper-large-v3` | beam 5, English |
| wav2vec2-large | CTC | `facebook/wav2vec2-large-960h-lv60-self` | greedy CTC |
| Parakeet-TDT 0.6B v2 | transducer | `nvidia/parakeet-tdt-0.6b-v2` (NeMo) | greedy TDT |
| Qwen3-ASR 0.6B | LLM-based | BF16 MLX conversion of `Qwen/Qwen3-ASR-0.6B` | greedy, English hint |
| Qwen3-ASR 1.7B | LLM-based | BF16 MLX conversion of `Qwen/Qwen3-ASR-1.7B` | greedy, English hint, 256-token limit |

Whisper, wav2vec2 and Parakeet ran on Delta GPUs; both Qwen models ran locally on Apple silicon (MLX).
All five transcribe the same 700 test utterances. Only Whisper, wav2vec2 and Parakeet errors were labeled
by the teacher and used to train the student; the Qwen models are scored by the student only.

## 6. Method

### 6.1 Normalization and error spans
- References and hypotheses get the same normalization: Whisper's `EnglishTextNormalizer` plus AMI fixes
  (dotted acronyms "t. v." → "tv"; "oh" not turned into 0; currency and percent spelled out). Without
  these fixes Whisper's WER was about 2 points too high.
- Word alignment with `jiwer`; WER = (substitutions + deletions + insertions) / reference words.
- **Error span:** a run of adjacent substitutions, deletions and insertions, merged into one unit,
  because meaning belongs to phrases, not single words. Shown as `[[reference words → ASR words]]`
  (`∅` = nothing).
- **Single-error sentence:** the reference with only this span replaced by the ASR output, as if every
  other error were fixed. Each error is judged on its own.

Example (meeting context: "The deadline moved earlier. Can the team still ship on time?"):

| | Sentence |
|---|---|
| Reference | We **cannot** ship before **Friday**. |
| ASR output | We **can** ship before **Thursday**. |
| Single-error sentence for the negation span | We **can** ship before **Friday**. |

Source: `src/common.py`, `src/align.py`.

### 6.2 Severity rubric (v2.4, frozen)

| Level | Name | Criterion | Example |
|---|---|---|---|
| 1 | Negligible | No change in meaning (spelling, grammar, repetition, fluency) | a repeated word disappears |
| 2 | Minor | Slight change; main meaning and specific facts intact | "very expensive" → "expensive" |
| 3 | Moderate | Specific information changed or lost; overall meaning preserved | "22 units" → "2 units" (as a detail) |
| 4 | Major | Main meaning substantially changed, lost, or unintelligible | the requested action becomes unintelligible |
| 5 | Critical | Direction of the core proposition reversed | "cannot ship" → "can ship" |

Decision order: any change at all? → reversal? → main meaning lost? → specific information lost?
Meaning takes precedence over surface form; context resolves references but is not used to compensate
for the error. Each label also has a content type (disfluency, negation, number, named entity, function
word, content word, other) and optional flags (`ref_issue`, `crosstalk`, `uncertain`, `multi_issue`).

The rubric went through several versions (v1 → v2.4, frozen as git tag `rubric-v2.4`), refined from
about 200 manually read errors and the human pilot. Full text: `annotation/rubric.md` (Chinese: `annotation/rubric_zh.md`); design notes:
`docs/rubric_notes.md`.

### 6.3 Human pilot
Both authors labeled the same 50 test error spans independently (35 random, 15 targeted: digits or
negation, long spans, substitutions).

| Agreement, rater A vs. rater B | Value |
|---|---:|
| Krippendorff's α (ordinal) | 0.789 |
| Quadratic weighted κ | 0.837 |
| Spearman | 0.831 |
| Exact match | 64% |
| Within one level | 96% |

One data-entry error was corrected; the three items that differed by 2 or more levels were discussed
(`docs/pilot_adjudication.md`). Most remaining disagreement is on misspellings, which one rater scores a
level higher. These 50 items were also used to refine the rubric and choose the teacher, so they are
kept out of every training and test split.

Source: `docs/progress.md`, `outputs/agreement.csv`, `annotation/human_pilot_{A,B}.xlsx`.

### 6.4 Teacher: LLM labels
The full rubric is the system prompt; the user message gives the meeting context, the marked span, the
reference and the single-error sentence. Temperature 0, JSON output. Candidate teachers on the 50 pilot
items:

| Model | α vs. rater A | α vs. rater B | Spearman vs. human mean | n |
|---|---:|---:|---:|---:|
| DeepSeek-V4.1-Flash | 0.745 | 0.720 | 0.763 | 50 |
| GPT-4o | 0.767 | 0.772 | 0.826 | 46 (4 rate-limit failures) |
| GPT-5.4-mini | 0.615 | 0.507 | 0.578 | 50 |

DeepSeek was chosen: close to human–human agreement (α 0.789), and fast with no rate limits. GPT-4o was
similar but rate-limited. These numbers are optimistic because the same items guided the prompt.

DeepSeek then labeled **all 28,566 error spans** of Whisper, wav2vec2 and Parakeet across train, dev and
test (one rubric and prompt hash for all), for about $48. A spot check found one systematic bias:
over-scoring an inserted "not" that does not really flip the meaning (e.g. tag questions).

Source: `src/annotate_llm.py`, `outputs/llm_annotations_deepseek-v4-1-flash_v2.4.jsonl`.

### 6.5 Student: DistilBERT
- Model: `distilbert-base-uncased`, max length 256.
- Input: preceding meeting context + reference with the error marked + single-error sentence.
- Output: severity 1–5.
- Training: `train_all3_9k`, learning rate 3e-5, batch 16, up to 10 epochs, early stopping on
  `dev_balanced` MAE (patience 3), seed 751, CPU.

Three training objectives, evaluated against the teacher on `test_balanced` (1,200 spans):

| Objective | Best epoch | QWK | MAE | Spearman |
|---|---:|---:|---:|---:|
| Mean squared error (regression) | 8 | 0.752 | 0.370 | 0.698 |
| Cross-entropy (5 classes) | 10 | 0.748 | 0.329 | 0.701 |
| **Ordinal thresholds** (4 cumulative logits) | 10 | **0.768** | 0.333 | **0.711** |
| Majority class (always 1) | — | 0.000 | 0.655 | — |

We use the ordinal model everywhere below. The objectives differ only slightly, and each was run with one
seed.

Source: `src/train_severity_cpu.py`, `outputs/nov21/student_cpu_objectives.json`.

### 6.6 Semantic-WER
Each error span with `n` word edits and severity `s` contributes a weighted edit:

| Variant | Weight per word edit | Aggregation |
|---|---|---|
| **Hard** (main) | (s − 1) / 4 → 0, 0.25, 0.5, 0.75, 1 | sum over spans / reference words |
| Linear | s / 5 | sum over spans / reference words |
| Max | worst (s − 1) / 4 in the utterance | mean over utterances |

With hard weights, a level-1 error costs nothing and a level-5 error costs as much as in WER. Every
system is scored with the same frozen student, so differences come from the ASR output only.

Source: `src/semwer.py`, `src/system_baselines.py`.

### 6.7 Baselines for the scorer
Both baselines see exactly the same pair as the student: reference vs. single-error sentence.

| Baseline | Score |
|---|---|
| Span length | number of word edits (what WER implicitly uses) |
| BERTScore | 1 − F1 (roberta-large, rescaled with the official baseline) |
| SemDist | 1 − cosine similarity of sentence embeddings (all-mpnet-base-v2) |

Spearman uses raw scores. For QWK and MAE each baseline is mapped to 1–5 by isotonic regression fit on
`dev_balanced` teacher labels; the student needs no mapping.

Source: `src/semantic_baselines.py`.

### 6.8 Statistics
System-level 95% confidence intervals and pairwise tests use a paired bootstrap over the 700 test
utterances: 2,000 resamples (seed 751), the same resample for every system. A difference counts as
significant when the same system is better in at least 97.5% of resamples (two-sided 95%).

---

## 7. Results

### 7.1 Question 1: the student scores severity better than BERTScore and SemDist

**Against the teacher**, Spearman on `test_balanced` (1,200 spans):

| Scorer | Whisper | wav2vec2 | Parakeet | All | QWK, all | MAE, all |
|---|---:|---:|---:|---:|---:|---:|
| Span length | 0.06 | 0.49 | 0.30 | 0.29 | 0.28 | 0.79 |
| BERTScore | 0.29 | 0.54 | 0.45 | 0.45 | 0.45 | 0.67 |
| SemDist | 0.50 | 0.60 | 0.57 | 0.57 | 0.60 | 0.56 |
| **Student** | **0.63** | **0.73** | **0.72** | **0.71** | **0.77** | **0.33** |

On all 2,128 usable test spans (`test_all`) the picture is the same: Spearman 0.35 / 0.47 / 0.58 / 0.72.

**Against humans**, mean of the two raters on the 50 pilot spans:

| Scorer | Spearman | QWK | MAE |
|---|---:|---:|---:|
| Span length | 0.30 | 0.28 | 0.85 |
| BERTScore | 0.63 | 0.58 | 0.68 |
| SemDist | **0.78** | 0.64 | 0.60 |
| **Student** | 0.76 | **0.80** | **0.42** |
| Teacher (reference) | 0.81 | 0.77 | 0.44 |
| Human A vs. human B | 0.83 | 0.84 | 0.40 |

Reading the results:
- Span length is nearly useless for Whisper (0.06): most Whisper errors are long deletions of
  repetitions that change nothing, so "more words wrong" does not mean "worse".
- BERTScore is the weakest semantic metric; it mostly measures word overlap, so dropping a "not" looks
  like a small change.
- The comparison against the teacher favours the student, which was trained on teacher labels. The
  fairer test is against humans: there SemDist ranks errors about as well as the student (0.78 vs. 0.76),
  but the student is much better at giving the right level on the 1–5 scale (QWK 0.80 vs. 0.64) and is
  close to human–human agreement.
- The human comparison has only 50 items, which also guided the rubric and teacher choice.

Source: `outputs/baselines/span_metrics.json`. Human-side QWK uses the human mean rounded half up; the
student has a prediction for 49 of the 50 items.

### 7.2 Question 2: WER and Semantic-WER for five systems

700 AMI test utterances, 9,347 reference words. Percent, lower is better; 95% bootstrap CI in brackets.

| ASR | WER | CER | Hard SemWER | Linear SemWER | Max SemWER | BERTScore dist. | SemDist |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3-ASR 1.7B | **7.40** [6.66, 8.20] | 4.21 | **1.45** [1.15, 1.81] | **2.64** | **8.83** | **10.92** | **6.47** |
| Parakeet-TDT 0.6B v2 | 7.56 [6.72, 8.45] | **4.02** | 1.67 [1.30, 2.08] | 2.85 | 8.88 | 11.20 | 6.92 |
| Qwen3-ASR 0.6B | 8.21 [7.43, 9.05] | 4.74 | 1.68 [1.34, 2.05] | 2.99 | 10.38 | 12.42 | 7.53 |
| Whisper large-v3 | 11.62 [10.63, 12.69] | 7.58 | 1.75 [1.40, 2.14] | 3.72 | 9.34 | 14.53 | 7.76 |
| wav2vec2-large | 22.50 [21.11, 23.93] | 11.57 | 7.41 [6.61, 8.27] | 10.43 | 30.04 | 35.70 | 24.99 |

Word edits behind the WER:

| ASR | Substitutions | Deletions | Insertions | Error spans |
|---|---:|---:|---:|---:|
| Qwen3-ASR 1.7B | 263 | 350 | 79 | 480 |
| Parakeet-TDT 0.6B v2 | 340 | 237 | 130 | 444 |
| Qwen3-ASR 0.6B | 310 | 377 | 80 | 522 |
| Whisper large-v3 | 268 | 737 | 81 | 614 |
| wav2vec2-large | 1,135 | 723 | 245 | 1,159 |

**Key finding.** Whisper's WER is 3.41 points above Qwen 0.6B and 4.06 above Parakeet, but its hard
Semantic-WER is only 0.07 and 0.08 points higher. Whisper makes about three times as many deletions as
Parakeet.

Source: `outputs/baselines/system_metrics.json`, `outputs/nov21/asr_five_systems.json`.

### 7.3 Why: severity distribution per system

Error spans by student severity (rounded to the nearest level) on the 700 test utterances:

| ASR | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 | Total | Level 3–5 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3-ASR 1.7B | 306 | 95 | 62 | 17 | 0 | 480 | 79 |
| Parakeet-TDT 0.6B v2 | 278 | 78 | 68 | 19 | 1 | 444 | 88 |
| Qwen3-ASR 0.6B | 333 | 85 | 81 | 22 | 1 | 522 | 104 |
| Whisper large-v3 | 437 | 97 | 61 | 19 | 0 | 614 | 80 |
| wav2vec2-large | 582 | 200 | 259 | 115 | 3 | 1,159 | 377 |

Share of level 1: Whisper 71%, Qwen 0.6B and 1.7B 64%, Parakeet 63%, wav2vec2 50%.

- The top four systems differ by up to 170 spans in total (444 to 614), but only by 25 spans at level 3
  or above (79 to 104). **Error counts vary; serious errors do not.**
- Whisper has 159 more level-1 spans than Parakeet but 8 fewer at level 3 or above (80 vs. 88). It
  "cleans up" disfluencies: repetitions, fillers and false starts that the AMI reference keeps.
- wav2vec2 errors are dominated by nonwords and garbled spans, which often destroy meaning.

The teacher's labels on the same test spans (three labeled systems) show the same pattern: level 1 is
73% of Whisper spans, 66% of Parakeet and 53% of wav2vec2. With teacher labels (excluding `ref_issue`
spans), hard Semantic-WER is Whisper 1.42%, Parakeet 1.56%, wav2vec2 7.32%; the student gives 1.75%,
1.67% and 7.41%. The student slightly reverses the order of Whisper and Parakeet, but both agree that
they are close.

Source: `outputs/nov21/spans_five_systems.jsonl`, `outputs/nov21/student_predictions_five_systems.jsonl`,
`outputs/semwer_summary_test+test_extra.json`.

### 7.4 Which differences are real?

Paired bootstrap, two-sided 95% (Yes = significant):

| Comparison | WER | BERTScore | SemDist | Hard SemWER |
|---|:---:|:---:|:---:|:---:|
| Parakeet vs. Whisper | Yes | Yes | No | **No** |
| Qwen 0.6B vs. Whisper | Yes | Yes | No | **No** |
| Parakeet vs. Qwen 0.6B | No | Yes | No | No |
| Qwen 1.7B vs. Parakeet | No | No | No | No |
| Qwen 1.7B vs. Qwen 0.6B | Yes | Yes | Yes | Yes |

Share of resamples in which the first system is lower:

| Comparison | WER | Hard SemWER | BERTScore | SemDist |
|---|---:|---:|---:|---:|
| Parakeet < Whisper | 1.00 | 0.66 | 1.00 | 0.96 |
| Qwen 0.6B < Whisper | 1.00 | 0.64 | 1.00 | 0.69 |
| Parakeet < Qwen 0.6B | 0.97 | 0.55 | 0.99 | 0.90 |
| Qwen 1.7B < Parakeet | 0.69 | 0.92 | 0.69 | 0.85 |
| Qwen 1.7B < Qwen 0.6B | 1.00 | 0.99 | 1.00 | 1.00 |
| Qwen 1.7B < Whisper | 1.00 | 0.97 | 1.00 | 1.00 |

- Two of the three significant WER gaps among the top four systems disappear under Semantic-WER.
- The larger Qwen model mainly removes meaning-changing errors (hard SemWER 1.68 → 1.45), and that gap is
  significant on every metric.
- Qwen 1.7B vs. Whisper on hard SemWER is close (0.97) but just below the 0.975 threshold.
- wav2vec2 is significantly worse than every other system on every metric (omitted from the table).

Source: `outputs/baselines/system_metrics.json` (`paired_bootstrap_p_lower`).

### 7.5 Final ranking

Ordered by hard Semantic-WER, then WER:

| Rank | ASR | WER | Hard SemWER | Comment |
|---:|---|---:|---:|---|
| 1 | Qwen3-ASR 1.7B | 7.40% | 1.45% | Lowest WER and Semantic-WER; not separable from Parakeet |
| 2 | Parakeet-TDT 0.6B v2 | 7.56% | 1.67% | Ties for first with a smaller model; lowest CER |
| 3 | Qwen3-ASR 0.6B | 8.21% | 1.68% | Fewer word errors than Whisper, same meaning loss |
| 4 | Whisper large-v3 | 11.62% | 1.75% | 71% of its error spans are negligible |
| 5 | wav2vec2-large | 22.50% | 7.41% | Four to five times the meaning loss of the others |

On hard Semantic-WER, only Qwen 1.7B vs. Qwen 0.6B and wav2vec2 vs. each other system differ
significantly, so ranks 1–4 are best read as one group with Qwen 1.7B slightly ahead.

---

## 8. Conclusion

**Word error counts can hide changes in meaning.**

| | Finding |
|---|---|
| Scorer (Q1) | A distilled DistilBERT student scores error severity more accurately than BERTScore and SemDist, and agrees with humans almost as well as humans agree with each other (QWK 0.80; human–human 0.84). |
| Benchmark (Q2) | Parakeet, Qwen 0.6B and Whisper tie on meaning but not on WER. WER penalizes Whisper for removing disfluencies that carry no meaning. |
| Limits | Qwen spans have no teacher or human labels; human labels cover only the 50 pilot spans; one training seed. |

## 9. Limitations and what we did not do

- **Small human evaluation.** Human labels exist for 50 spans (Whisper and wav2vec2 only), which also
  informed the rubric and teacher choice. A separate 200-span human test set was sampled
  (`data/splits/human_test.txt`) but not annotated.
- **Teacher bias.** The student learns DeepSeek's judgments, including its known tendency to over-score
  inserted negations.
- **Qwen.** Qwen errors are scored by the student only, with no teacher or human labels, so student
  accuracy on Qwen is not measured.
- **Single seed.** Every student result uses seed 751; small differences between objectives may not be
  stable.
- **Not run:** leave-one-system-out generalization, learning curves, multiple seeds, a second LLM teacher,
  and sentence-level human ratings (which would be needed to claim that Semantic-WER is a better system
  metric than WER, rather than only a different one).
- **Domain.** One corpus (AMI headset meetings) with oracle segmentation.

## 10. Reproducing the results

| Step | Command |
|---|---|
| Sample utterances | `python src/prepare_ami.py --subset {test,test_extra,dev,train}` |
| ASR (Whisper, wav2vec2, Parakeet) | `slurm/asr.sbatch`, `slurm/asr_parakeet.sbatch` on Delta |
| Align and cut error spans | `python src/align.py --subset <subset>` |
| Teacher labels | `python src/annotate_llm.py --backend azure_v1 --model deepseek-v4-1-flash --ids subset:<subset> --tag deepseek-v4-1-flash_v2.4` |
| Student splits | `python src/make_splits.py` |
| Train the student | `python src/train_severity_cpu.py --train-split train_all3_9k --objective ordinal --seed 751 --epochs 10 --bs 16 --lr 3e-5 --patience 3 --min-epochs 5 --output-dir runs/ordinal/seed_751` |
| Span-level baselines | `python src/semantic_baselines.py --student outputs/nov21/student_predictions_five_systems.jsonl` |
| System-level metrics and bootstrap | `python src/system_baselines.py --qwen-dir outputs/nov21 --spans outputs/nov21/spans_five_systems.jsonl --student outputs/nov21/student_predictions_five_systems.jsonl` |

Set `HF_HOME` to a local Hugging Face cache for the model-based steps. The teacher step needs an Azure
API key in `.env` (never committed).

## Appendix A. Key files

| File | Content |
|---|---|
| `annotation/rubric.md` | Severity rubric v2.4 |
| `annotation/human_pilot_{A,B}.xlsx` | Human labels for the 50 pilot spans |
| `outputs/errors*.jsonl` | All error spans with context |
| `outputs/llm_annotations_deepseek-v4-1-flash_v2.4.jsonl` | Teacher labels for 28,566 spans |
| `data/splits/*.txt` | Student train / dev / test id lists |
| `outputs/nov21/student_cpu_objectives.json` | Student training runs and metrics |
| `outputs/nov21/spans_five_systems.jsonl` | Error spans of all five systems on the 700 test utterances |
| `outputs/nov21/student_predictions_five_systems.jsonl` | Student severity per span |
| `outputs/nov21/asr_five_systems.json` | WER, CER and edit counts |
| `outputs/baselines/span_metrics.json` | Scorer comparison (student vs. baselines) |
| `outputs/baselines/system_metrics.json` | System metrics, CIs and paired bootstrap |
| `docs/data.md` | Full data procedure |

## Appendix B. Qwen decoding sanity check

To check that the local MLX decoding of Qwen3-ASR 0.6B behaves like the official model, we ran it on part
of LibriSpeech `test-clean`: 2.40% WER on the first 1,389 clips of a duration-ordered run (362 edits /
15,060 words), versus 2.11% reported on the full set in the official model card. The subset skews toward
shorter clips. Source: `outputs/nov21/metrics_0.6b_test-clean_partial_1389.json`.
