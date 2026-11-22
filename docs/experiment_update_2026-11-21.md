# November 21 project checkpoint

[Project presentation](https://docs.google.com/presentation/d/1fPxfRMS1ULUFOe_jX2wZrmvL5IRw7Z4gVzmCTKqzP2c/edit) (Google Drive access applies).

## DistilBERT severity prediction

The CPU experiment uses 9,000 DeepSeek-labeled training error spans from Whisper, wav2vec2, and Parakeet (3,000 each). It selects checkpoints by development MAE on 1,200 spans and evaluates them against DeepSeek on a separate balanced test of 1,200 spans. The student takes preceding meeting context, the marked reference, and the single-error hypothesis as text input. Its output estimates severity on the 1–5 scale.

| Objective | Best epoch | Balanced test MAE | Balanced test QWK |
| --- | ---: | ---: | ---: |
| Mean squared error | 8 | 0.3701 | 0.7516 |
| Five-class cross-entropy | 10 | 0.3287 | 0.7476 |
| Ordinal thresholds | 10 | 0.3332 | 0.7680 |

These are single-seed experiments (751). The ordinal checkpoint was used for the four-system comparison below. The 50-item human pilot measured ordinal Krippendorff’s α of 0.789 between annotators and informed the rubric. Results on the independent 200-item human test remain pending.

The [CPU runner](../src/train_severity_cpu.py) uses the current fixed split manifests. In an environment with the project’s Python dependencies, validate data first, then run the selected objective. **Set `HF_HOME` to a local Hugging Face cache** and use a new output directory for each run.

```sh
HF_HOME="$HOME/.cache/huggingface" python src/train_severity_cpu.py --validate-only
HF_HOME="$HOME/.cache/huggingface" python src/train_severity_cpu.py \
  --train-split train_all3_9k --objective ordinal --seed 751 --epochs 10 \
  --bs 16 --lr 3e-5 --patience 3 --min-epochs 5 --output-dir runs/ordinal/seed_751
```

[Exact run configurations, histories, and metrics](../outputs/nov21/student_cpu_objectives.json)

## Four-system evaluation on AMI

All systems use the same 700 presegmented utterances from 16 AMI test meetings. WER and CER use the same English normalization across models. CER excludes spaces. Hard Semantic-WER weights each word edit in a span by `(severity − 1) / 4` using the same frozen ordinal student for all four systems.

| ASR | WER | CER | Hard Semantic-WER |
| --- | ---: | ---: | ---: |
| Parakeet-TDT 0.6B v2 | 7.56% | 4.02% | 1.67% |
| Qwen3-ASR 0.6B | 8.21% | 4.74% | 1.68% |
| Whisper large-v3 | 11.62% | 7.58% | 1.75% |
| wav2vec2-large | 22.50% | 11.57% | 7.41% |

Qwen and Whisper differ by 3.41 percentage points in WER and 0.07 in student-weighted hard Semantic-WER. Qwen was decoded locally with the [BF16 MLX conversion](https://huggingface.co/mlx-community/Qwen3-ASR-0.6B-bf16), greedy decoding, and an English language hint. The student scored 522 Qwen error spans. Estimating severity agreement on Qwen requires independent teacher or human labels.

[WER/CER and edit totals](../outputs/nov21/asr_four_systems.json) · [Student-weighted metrics](../outputs/nov21/student_four_systems.json) · [Qwen hypotheses, original 500](../outputs/nov21/hyp_qwen3-asr-0.6b_test.jsonl) · [Qwen hypotheses, extra 200](../outputs/nov21/hyp_qwen3-asr-0.6b_test_extra.jsonl)

## Qwen spot checks

On the first 1,389 completed clips in a duration-ordered run of LibriSpeech `test-clean`, Qwen3-ASR 0.6B recorded **2.40% WER** (362 edits / 15,060 reference words). The subset skews toward shorter clips. The [official model card](https://huggingface.co/Qwen/Qwen3-ASR-0.6B#evaluation) reports **2.11%** on all 2,620 clips using vLLM. The local run used BF16 MLX, greedy decoding, and automatic language detection.

The 1.7B AMI trial covered 126 utterances. On those same clips, WER was 10.04% for 1.7B and 11.58% for 0.6B. Full 1.7B AMI evaluation is pending.

[LibriSpeech counts and scored IDs](../outputs/nov21/metrics_0.6b_test-clean_partial_1389.json) · [Paired 126-item AMI trial](../outputs/nov21/ami_local_prefix_preview.json)
