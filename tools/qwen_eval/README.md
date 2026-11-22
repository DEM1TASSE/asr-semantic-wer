# Qwen3-ASR decoding and frozen-student scoring (as run locally, Nov 21)

These are the scripts that produced `outputs/nov21/hyp_qwen3-asr-*`, `asr_five_systems.json`,
`spans_five_systems.jsonl` and `student_predictions_five_systems.jsonl`. They are kept as run, so paths
point to the original working folders (`~/semwer-qwen-eval`, `~/semwer-local-cpu`, a Delta work directory)
and must be adjusted before reuse.

| script | role |
|---|---|
| `transcribe.py` | Qwen3-ASR 0.6B / 1.7B decoding with MLX Audio (BF16, greedy, English hint, 256-token limit) |
| `run_local_eval.py`, `local_memory.py` | serial runner with a memory-pressure guard for laptop runs |
| `evaluate_asr.py` | WER / CER and aligned error spans for all systems on the 700 AMI test utterances |
| `score_student.py` | scores every span with the frozen ordinal DistilBERT student (All-3-9K, seed 751) |
| `finish_eval.py` | writes the summary report |
| `evaluate_librispeech.py`, `score_delta_librispeech.py` | LibriSpeech test-clean spot check (not in the final slides) |
| `delta_qwen*.py`, `delta_qwen*.sbatch` | earlier attempt to decode on Delta |

The student checkpoint itself is on Hugging Face (see the top-level README).
