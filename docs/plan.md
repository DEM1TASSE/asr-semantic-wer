# Plan

**Project:** Context-aware semantic error profiling for ASR (11-751 / 18-781, Fall 2026)
**Team:** Demi Wang, Yixiang Dai

## Research questions
1. Can an LLM judge (teacher) score the semantic severity of individual ASR errors about as consistently as
   humans do, under a fixed rubric?
2. Can a small encoder (DistilBERT, student) distilled from the teacher's labels reproduce those judgments,
   and does it generalize across ASR systems?
3. Does a severity-weighted WER (Semantic-WER) profile ASR systems differently from plain WER?

## Deliverables
- **Midterm checkpoint (due Nov 13, 11:59 PM ET):** intro + related work, method, data and setup, first
  results: ASR baselines, rubric and human pilot agreement, teacher selection, Semantic-WER on the test set,
  and this experiment plan.
- **Final report:** everything below.

## Data (AMI IHM, oracle segmentation, utterances with ≥ 5 words)
Splits follow the official AMI partition, so train / dev / test never share a meeting.

| subset | AMI source | utterances | sampled per meeting | labels |
|---|---|---|---|---|
| train | 8 of 42 train shards: 29 meetings, 50 speakers | 6,000 | 51–270 | DeepSeek |
| dev | validation: 18 meetings | 700 | 38–41 | DeepSeek |
| test | test: 16 meetings | 500 (original) + 200 (`test_extra`) | ~44 | DeepSeek; 200 also human |

Same procedure for every subset: both ASR systems decode the **same** utterances and **every** error span is
kept and labeled. Balanced subsets are drawn afterwards.

**Two fair comparisons, two normalizations** (a system that makes more errors yields more spans):
- **Learning severity (student training / evaluation): equal number of errors per system.** Train: 5,000 +
  5,000 drawn from the train spans, stratified by meeting; dev / weak-label test: 500 + 500. This keeps the
  student from simply seeing more wav2vec2 errors.
- **Comparing ASR systems (WER, Semantic-WER, severity profile): equal utterances, all errors.** Rates are per
  reference word on identical audio, so a different number of errors is the result, not a confound.

Whisper makes ~0.9 error spans per utterance and wav2vec2 ~1.7, so 6,000 train utterances give roughly
5,000+ Whisper and ~10,000 wav2vec2 spans.

**Provenance.** Each error record (`outputs/errors*.jsonl`) stores: error_id (`system|audio_id|k`), subset, AMI
split, system and HF model id, meeting, speaker, begin/end time, raw and normalized reference, raw and
normalized ASR output, span indices, the marked span, and the context. Each LLM label stores the model,
rubric file and SHA, prompt SHA, decoding settings, timestamp, and token usage. Subsample memberships
(5K / 2.5K / 1K, balanced test) are written as id lists with their seed.

- The 50 pilot items were used to tune the rubric, prompt, and teacher choice: they are **dev**, excluded from
  the human test and from the weak-label test.
- Teacher: DeepSeek v4.1 flash, rubric v2.4 (frozen, tag `rubric-v2.4`), single-error prompt,
  `max_tokens 2000`. ~20k spans × ~$0.0015 ≈ **$30**.

## Student training
DistilBERT (`distilbert-base-uncased`), input = context + reference with the error marked
`[[ref → hyp]]` + the single-error ASR sentence; target = teacher severity. Main loss: regression (report also
rounded predictions). Early stopping and hyperparameters on dev only. 3 seeds per configuration; report mean
± std.

| configuration | train data | question |
|---|---|---|
| Whisper-5K | 5,000 Whisper | in-domain vs cross-ASR |
| wav2vec2-5K | 5,000 wav2vec2 | in-domain vs cross-ASR |
| Mixed-5K | 2,500 + 2,500 | composition at fixed size (vs single-ASR 5K) |
| Mixed-10K | 5,000 + 5,000 | scale (vs Mixed-5K) |
| learning curve | Mixed 1K, 2.5K (+ 5K, 10K above) | does more data still help? |

Notes:
- Mixed-5K vs single-ASR-5K compares training-data **composition**, not a clean causal effect of diversity:
  it also halves each system's share, and the two systems have different severity distributions (Whisper is
  dominated by harmless disfluency deletions).
- Baselines: majority class; per-content-type mean; embedding similarity of reference vs single-error ASR
  sentence (SemDist-style, Sentence-BERT) mapped to 1–5 by isotonic regression fitted on train.

## Evaluation
**A. Weak-label test** (teacher labels; does the student learn the teacher?): balanced 500 + 500 and all test
spans; Whisper, wav2vec2, combined;
QWK, Spearman, MAE, within-1.

**B. Human test** (ground truth): 200 new errors from AMI test, **100 per ASR**, from many meetings, none from
the pilot. Both annotators label all 200 independently (rubric v2.4), then adjudicate gaps ≥ 2. Report
human–human, DeepSeek–human, DistilBERT–human, and gpt-4o–human (second LLM, only on these 200), with
bootstrap 95% CIs.
- Sampling: ~70% random + ~30% targeted by **surface features** (digits/negation words, long spans ≥ 3 word
  errors, substitutions), as in the pilot. **Not** stratified by DeepSeek labels: selecting items by the
  teacher's own predictions biases the teacher–human and student–human comparison. Report results on the
  random part alone (natural distribution) as well.
- 200 items support approximate agreement estimates and clear model differences, not small ones
  (e.g. 0.02 κ); per-ASR (100) and per-severity-level results are indicative only.

**C. System-level analysis** on all test errors: WER vs Semantic-WER (lin / hard / max), severity
distribution, high-severity (≥ 4) error rate, error profiles by content_type and error_form, cases.

**Optional (final, if time):** sentence-level human meaning-preservation ratings (100–150 utts) to correlate
WER / Semantic-WER / embedding similarity with humans; teacher self-consistency (re-run on the human test).

## Not doing
- More ASR systems or more teacher LLMs: two ASR systems with very different error profiles are enough for
  the question; teachers were compared on the pilot (gpt-5.4-mini, gpt-4o, DeepSeek).

## Design decisions
| decision | choice | why |
|---|---|---|
| ASR | Whisper large-v3 (beam 5) vs wav2vec2-large-960h-lv60-self (greedy CTC) | different architectures and error behaviour |
| normalization | Whisper EnglishTextNormalizer + AMI fixes | unfixed normalization inflated Whisper WER by ~2 points |
| error unit | adjacent S/D/I merged into one span; context = 3 prev + 1 next utt (reference transcript) | severity is a property of a phrase |
| rubric | `annotation/rubric.md` v2.4, frozen; notes in `docs/rubric_notes.md` | severity = semantic distortion 1–5 + content_type + flags |
| teacher | DeepSeek v4.1 flash on Azure | on the pilot ≈ human–human agreement, fast, no rate limits; gpt-4o similar but rate-limited |

## Shared resources
- Delta allocation: `bjdh-delta-gpu` / `bjdh-delta-cpu`
- Large files (AMI parquet, HF cache, audio): `/work/hdd/bjdh/dwang30/semwer`
