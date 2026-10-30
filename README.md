# Context-aware semantic error profiling for ASR (11-751 project)

Delta setup: environment via `pixi` (manifest in this directory); large files live in
`/work/hdd/bjdh/dwang30/semwer` (AMI parquet, HF cache). GPU jobs use account `bjdh-delta-gpu`.

## Pipeline

| step | command | output |
|---|---|---|
| 1. eval subset (500 utts, oracle segmentation, 16 AMI IHM test meetings) | `pixi run python src/prepare_ami.py` | `data/eval_subset.{parquet,jsonl}` |
| 2. ASR (Whisper large-v3, wav2vec2-large-960h-lv60-self) | `sbatch slurm/asr.sbatch` | `outputs/hyp_*.jsonl` |
| 3. normalize + align + error spans | `pixi run python src/align.py` | `outputs/wer_summary.json`, `outputs/errors.jsonl` |
| 4. sample human pilot / LLM sets | `pixi run python src/make_sets.py` | `annotation/human_pilot_{A,B}.csv`, `outputs/*_ids.txt` |
| 5. LLM annotation (Azure; key `AZURE_API_KEY` in `.env`) | `pixi run python src/annotate_llm.py --ids all --model gpt-4o` (or `--model gpt-5.4-mini`) | `outputs/llm_annotations_<model>.jsonl` |
| 6. **humans**: fill `severity`/`category` in the two pilot CSVs independently | — | |
| 7. agreement (human-human, LLM-human) | `pixi run python src/agreement.py` | `outputs/agreement.csv` |
| 8. Semantic-WER + figures + cases | `pixi run python src/semwer.py` | `outputs/semwer_summary.json`, `outputs/fig_*.png`, `outputs/cases.md` |
| 9. DistilBERT severity predictor | `sbatch slurm/train.sbatch` | `outputs/severity_model_<tag>.json` |

Project docs: `docs/plan.md`, `docs/progress.md`, `docs/todo.md`.

The annotation rubric is `annotation/rubric.md`; it is inserted verbatim into the LLM prompt.

## Design decisions (for the Experimental Setup section)
- Oracle AMI segmentation; utterances with < 5 normalized words excluded (backchannels).
- Refs and hyps normalized with Whisper's `EnglishTextNormalizer`.
- Adjacent S/D/I alignment chunks merged into one error span; severity is judged per span.
- Context = 3 previous + 1 following utterance from the full meeting reference (all speakers).
- Whisper: beam 5, fp16, language=en. wav2vec2: greedy CTC.

## Setup for teammates
```bash
git clone <repo> && cd <repo>
pixi install                                   # creates the env from pixi.lock
echo "AZURE_API_KEY=..." > .env && chmod 600 .env   # never commit this
```
Eval audio is not in git: on Delta it is read from `/work/hdd/bjdh/dwang30/semwer`; elsewhere, rerun
`src/prepare_ami.py` (downloads AMI IHM test from HuggingFace, ~1.3 GB).
