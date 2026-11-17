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
Three ASR systems with different architectures decode the **same** utterances; **every** error span is
labeled by the teacher. Details: `docs/data.md`.

| subset | AMI source | utterances | Whisper | wav2vec2 | Parakeet-TDT |
|---|---|---|---|---|---|
| train | 8 of 42 train shards: 29 meetings | 6,000 | 7,030 | 11,754 | 5,246 |
| dev | validation: 18 meetings | 700 | 655 | 1,180 | 484 |
| test | test: 16 meetings (500 + 200 `test_extra`) | 700 | 614 | 1,159 | 444 |

Systems: Whisper large-v3 (encoder-decoder), wav2vec2-large-960h-lv60-self (CTC),
Parakeet-TDT-0.6b-v2 (transducer; added after TA feedback, Nov 16).

**Two fair comparisons:**
- **Learning severity (student):** equal number of errors per system ("balanced").
- **Comparing ASR systems (WER, Semantic-WER):** same utterances, all errors.

Teacher: DeepSeek-V4.1-Flash, final rubric (frozen), single-error prompt, temperature 0. ~$38 for the
first 22k spans, ~$10 more for Parakeet.

## Student training
DistilBERT (`distilbert-base-uncased`), input = context + reference with the error marked
`[[ref → hyp]]` + the single-error ASR sentence; target = teacher severity (regression). Early stopping and
hyper-parameters on dev only. 3 seeds per configuration; mean ± std.

Because the label (meaning change) does not depend on which ASR made the error, we do not train every
combination of systems (TA feedback). All main training sets have the **same size (9,000 errors)**:

| configuration | train data | question |
|---|---|---|
| All-3 | 3,000 per system | main model |
| Leave-one-out (×3) | 4,500 from each of the other two systems | does it generalize to an unseen ASR system? (compare with All-3 on the held-out system) |
| Learning curve | All-3 at 1.5K / 3K / 6K (+ 9K) | does more data help? |
| (if time) Single-system (×3) | 4,500 from one system | test on the other two |

Baselines: majority class; train mean; **off-the-shelf Sentence-BERT** cosine similarity of reference vs
single-error ASR sentence, mapped to 1–5 on dev (isotonic regression).

## Evaluation
**A. Weak-label test** (teacher labels; does the student learn the teacher?): balanced 400 per system and all test
spans; per system (Whisper, wav2vec2, Parakeet) and combined;
QWK, Spearman, MAE, within-1.

**B. Human test** (ground truth): 200 new errors from AMI test (never train / dev meetings), **~67 per ASR
system**, none from the pilot. Both annotators label all 200 independently, then adjudicate gaps ≥ 2.
Report human–human, DeepSeek–human, DistilBERT–human, and **small open LLM teachers (e.g. Qwen3 4B / 8B,
same prompt, served with vLLM on Delta)**–human, with bootstrap 95% CIs.
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
- Training every combination of ASR systems: leave-one-out answers the generalization question.
- More than three ASR systems (e.g. an LLM-based ASR) unless time allows.

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
