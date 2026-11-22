# Semantic baselines and five-system comparison (Nov 21, late)

Adds Qwen3-ASR 1.7B (fifth ASR system) and two training-free semantic baselines, BERTScore and SemDist.
Student = frozen ordinal DistilBERT (All-3-9K, seed 751, dev-selected), the same checkpoint for every system.

## 1. Span level: which score tracks error severity?

Each error span is scored on (reference, single-error ASR sentence), the same pair the teacher and student judge.
BERTScore = 1 − F1 (roberta-large, rescaled); SemDist = 1 − cosine (all-mpnet-base-v2); span length = number of
word edits (what WER counts). Baselines are mapped to 1–5 by isotonic regression fit on `dev_balanced` (for QWK / MAE);
Spearman uses the raw scores.

| scorer | Spearman vs teacher, test_balanced (n=1,200) | Spearman vs teacher, test_all (n=2,128) | Spearman vs human mean, pilot (n=50) | QWK vs human, pilot |
|---|---:|---:|---:|---:|
| span length (WER) | 0.29 | 0.35 | 0.30 | 0.28 |
| BERTScore | 0.45 | 0.47 | 0.63 | 0.58 |
| SemDist | 0.57 | 0.58 | **0.78** | 0.64 |
| **student** | **0.71** | **0.72** | 0.76 | **0.80** |
| teacher (reference) | — | — | 0.81 | 0.77 |

Per system (Spearman vs teacher, test_balanced): Whisper 0.06 / 0.29 / 0.50 / **0.63** (span length / BERTScore /
SemDist / student), wav2vec2 0.49 / 0.54 / 0.60 / **0.73**, Parakeet 0.30 / 0.45 / 0.57 / **0.72**. The gap is largest
on Whisper, whose errors are mostly dropped disfluencies and repetitions.

Caveats: the comparison against teacher labels favours the student (it was trained on them); the human comparison is
only 50 items, and those items informed the rubric and teacher choice. Full numbers: `outputs/baselines/span_metrics.json`.

## 2. System level: 700 AMI test utterances, five ASR systems

Percent, lower is better; 95% CI by bootstrap over utterances (2,000 resamples, paired across systems).
WER uses 9,347 reference words. BERTScore / SemDist here are on the full normalized hypothesis vs reference.

| ASR | WER | CER | SemWER hard | SemWER lin | SemWER max | BERTScore dist | SemDist |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3-ASR 1.7B | **7.40** [6.66, 8.20] | 4.21 | **1.45** [1.15, 1.81] | **2.64** | **8.83** | **10.92** | **6.47** |
| Parakeet-TDT 0.6B v2 | 7.56 [6.72, 8.45] | **4.02** | 1.67 [1.30, 2.08] | 2.85 | 8.88 | 11.20 | 6.92 |
| Qwen3-ASR 0.6B | 8.21 [7.43, 9.05] | 4.74 | 1.68 [1.34, 2.05] | 2.99 | 10.38 | 12.42 | 7.53 |
| Whisper large-v3 | 11.62 [10.63, 12.69] | 7.58 | 1.75 [1.40, 2.14] | 3.72 | 9.34 | 14.53 | 7.76 |
| wav2vec2-large | 22.50 [21.11, 23.93] | 11.57 | 7.41 [6.61, 8.27] | 10.43 | 30.04 | 35.70 | 24.99 |

Paired bootstrap (share of resamples where the first system is lower):

| comparison | WER | SemWER hard | BERTScore | SemDist |
|---|---:|---:|---:|---:|
| Parakeet < Whisper | 1.00 | 0.66 | 1.00 | 0.96 |
| Qwen 0.6B < Whisper | 1.00 | 0.64 | 1.00 | 0.69 |
| Parakeet < Qwen 0.6B | 0.97 | 0.55 | 0.99 | 0.90 |
| Qwen 1.7B < Parakeet | 0.69 | 0.92 | 0.69 | 0.85 |
| Qwen 1.7B < Qwen 0.6B | 1.00 | 0.99 | 1.00 | 1.00 |

Findings
- WER and BERTScore separate Whisper clearly from Parakeet and Qwen 0.6B; severity-weighted Semantic-WER does not:
  Whisper's extra errors are low-severity (dropped fillers and repetitions).
- Qwen 1.7B vs 0.6B: the larger model mainly removes meaning-changing errors (SemWER hard 1.68 → 1.45).
- Qwen 1.7B and Parakeet are not separable at 95% on any metric.
- Ranking: Qwen3-ASR 1.7B ≈ Parakeet-TDT 0.6B > Qwen3-ASR 0.6B ≈ Whisper large-v3 (semantically) ≫ wav2vec2-large.

Qwen severities come only from the student (no teacher or human labels for Qwen spans).
Qwen 1.7B was decoded locally (BF16 MLX conversion, greedy, English hint, 256-token limit), like 0.6B.

## Reproduce
```sh
HF_HOME=<hf cache> python src/semantic_baselines.py --student outputs/nov21/student_predictions_five_systems.jsonl
HF_HOME=<hf cache> python src/system_baselines.py --qwen-dir outputs/nov21 \
  --spans outputs/nov21/spans_five_systems.jsonl --student outputs/nov21/student_predictions_five_systems.jsonl
```
`outputs/nov21/spans_five_systems.jsonl` holds the aligned error spans of all five systems on the 700 utterances;
`outputs/baselines/system_utterances.jsonl` caches the per-utterance BERTScore / SemDist.
