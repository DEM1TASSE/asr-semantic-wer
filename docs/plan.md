# Plan

**Project:** Context-aware semantic error profiling for ASR (11-751 / 18-781, Fall 2026)
**Team:** Demi Wang, Yixiang Dai

## Research question
Does a severity-weighted WER (Semantic-WER), built from context-aware per-error severity judgments,
track human judgments of transcript quality better than plain WER or embedding similarity?

## Deliverables
- **Midterm checkpoint (due Nov 13, 11:59 PM ET):** add Experimental Setup + Benchmark Results to the proposal.
  - ASR baselines (WER, S/D/I) on the AMI subset
  - LLM annotation of all error spans + a small human pilot (agreement)
  - Preliminary Semantic-WER vs WER, error profiles, representative cases
- **Final report:**
  - Human test set (200 spans, double-annotated) → human-human, LLM-human agreement
  - Distilled severity predictor (DistilBERT, DeBERTa-v3) evaluated against humans
  - Sentence-level human ratings (100–150 utts) → correlation of WER / Semantic-WER / BERTScore with humans
  - Aggregation ablations; cross-ASR semantic error profiles

## Design decisions
| decision | choice | why |
|---|---|---|
| data | AMI IHM test, 500 utts, oracle segmentation, 16 meetings, ≥5 words | TA recommended AMI; IHM keeps WER moderate; oracle segments avoid segmentation confounds |
| ASR | Whisper large-v3 (beam 5) vs wav2vec2-large-960h-lv60-self (greedy CTC) | different architectures and error behaviour |
| normalization | Whisper EnglishTextNormalizer + AMI fixes (acronyms, oh/o'clock, cause, kinda, currency) | unfixed normalization inflated Whisper WER by ~2 points |
| error unit | adjacent S/D/I merged into one span; context = 3 prev + 1 next utt | severity is a property of a phrase, not a single word |
| rubric | `annotation/rubric.md` v1, built from ~200 real samples | severity 1–5 + content_type + error_form + flag |
| LLM judge | Azure gpt-5.4-mini (gpt-4o dropped: rate limits) | key in `.env` (not committed) |
| human set | 50 dev (rubric iteration) + 200 test, both annotators label all | needed for agreement; stratify by system/error form, never by LLM label |

## Shared resources
- Delta allocation: `bjdh-delta-gpu` / `bjdh-delta-cpu`
- Large files (AMI parquet, HF cache, eval audio): `/work/hdd/bjdh/dwang30/semwer`
