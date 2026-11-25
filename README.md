# When ASR Errors Change Meaning: Context-Aware Semantic Error Profiling for ASR

Course project for 11-751 / 18-781 Speech Recognition and Understanding (CMU, Fall 2026).
Demi Wang, Yixiang Dai; TA: Chin-Jou Li.

Word error rate (WER) counts every wrong word the same, although dropping a repeated "the" changes nothing
and dropping a "not" reverses the speaker. We cut ASR errors into spans, score how much each span changes
the meaning (severity 1–5, judged in meeting context), and use the scores for a severity-weighted WER,
**SemWER** (to distinguish it from the entity-weighted Semantic-WER of Roy, 2021). An LLM (**teacher**, DeepSeek-V4.1-Flash) labels 29.6k error spans from five ASR systems
on the AMI meeting corpus, and a fine-tuned DistilBERT (**student**) reproduces the labels cheaply and
without any API.

| | |
|---|---|
| **Report** | [`docs/final_report.pdf`](docs/final_report.pdf) |
| **Trained model** | [huggingface.co/yixiang666/asr-semantic-severity-distilbert](https://huggingface.co/yixiang666/asr-semantic-severity-distilbert) |
| **Rubric** | [`annotation/rubric.md`](annotation/rubric.md) (Chinese version: [`rubric_zh.md`](annotation/rubric_zh.md)) |
| **Teacher prompt** | `SYSTEM` and `USER` in [`src/annotate_llm.py`](src/annotate_llm.py) |
| **How the data was made** | [`docs/data.md`](docs/data.md) |

## Main results

**Five ASR systems on 700 AMI test utterances (9,355 reference words), %.** SemWER
$= \sum_j n_j\,(v_j-1)/4 \,/\, N$ for error spans $j$ with $n_j$ word edits and severity $v_j$;
R = SemWER / WER = average severity weight per edited word. Source: `outputs/system_compare.json`.

| System | WER | CER | SemWER (teacher) | SemWER (student) | R (teacher) |
|---|---|---|---|---|---|
| Qwen3-ASR 1.7B | 7.39 | 4.21 | 1.34 | 1.27 | 0.18 |
| Parakeet-TDT 0.6B v2 | 7.57 | 4.02 | 1.56 | 1.58 | 0.21 |
| Qwen3-ASR 0.6B | 8.19 | 4.74 | 1.58 | 1.54 | 0.19 |
| Whisper large-v3 | 11.63 | 7.58 | 1.42 | 1.54 | 0.12 |
| wav2vec2-large-960h-lv60-self | 22.49 | 11.57 | 7.32 | 7.34 | 0.33 |

Whisper has 4 points more WER than Parakeet but about the same SemWER: its extra errors are almost all
deletions of repetitions, fillers and false starts that the AMI references keep (6.0 deleted disfluent words
per 100 reference words, vs. 1.0 for Parakeet).

**Scorers against two human annotators on 100 new test spans** (20 per system; never used for development).
Source: `outputs/human_test_eval.json`.

| Scorer | QWK | Spearman | MAE |
|---|---|---|---|
| Human A vs. human B | 0.85 | 0.79 | 0.32 |
| Teacher (DeepSeek-V4.1-Flash) | 0.84 | 0.82 | 0.37 |
| Student (DistilBERT, ordinal) | 0.82 | 0.83 | 0.39 |
| Sentence-BERT cosine distance (all-mpnet-base-v2) | 0.65 | 0.68 | 0.53 |
| SemDist (RoBERTa-large mean pooling) | 0.54 | 0.62 | 0.62 |
| SemDist (BERT-base mean pooling) | 0.63 | 0.62 | 0.60 |
| BERTScore | 0.59 | 0.61 | 0.60 |
| Span length (what WER uses) | 0.33 | 0.31 | 0.73 |

The student was trained on Whisper, wav2vec2 and Parakeet only; on the two Qwen3-ASR systems it is
equally good (QWK 0.77–0.82 against the teacher).

**Blind pairwise test** (60 utterances, two raters choose which of two outputs keeps the meaning better, or
Same). A choice agrees with a metric if it is the output the metric prefers, or Same when the metric scores a
tie. Human choices agree with SemWER vs. WER 42% vs. 16% where the metrics prefer different outputs,
82% vs. 16% where only WER sees a difference, and 70% vs. 40% on random utterances.

## What is in this repository

Everything is joined on `error_id` = `<system>|<audio_id>|<k>`. Files without a suffix are the 500-utterance
`test` subset; `_test_extra`, `_dev`, `_train` are the other subsets (test = `test` + `test_extra`).
System names: `whisper-large-v3`, `wav2vec2-large`, `parakeet-tdt-0.6b-v2`, `qwen3-asr-0.6b`, `qwen3-asr-1.7b`.

### Data

| Path | Content |
|---|---|
| `data/eval_subset.jsonl`, `data/subset_{test_extra,dev,train}.jsonl` | sampled AMI utterances: id, meeting, speaker, times, reference, context |
| `outputs/hyp_<system>[_subset].jsonl` | raw ASR output per utterance |
| `outputs/errors[_subset].jsonl` | one line per error span: marked reference `[[ref → asr]]`, edit type, context |
| `outputs/llm_annotations_deepseek-v4-1-flash_v2.4.jsonl` | **teacher labels** for all 29,568 spans: severity, content type, flags, rationale |
| `data/splits/*.txt`, `manifest.json` | fixed train / dev / test id lists for the student (meeting-disjoint) |
| `outputs/wer_summary*.json`, `outputs/semwer_summary*.json` | WER and SemWER per subset |

| Subset | AMI split | Utterances | Whisper | wav2vec2 | Parakeet | Qwen 0.6B | Qwen 1.7B |
|---|---|---|---|---|---|---|---|
| train | train (29 meetings) | 6,000 | 7,030 | 11,754 | 5,246 | – | – |
| dev | validation (18) | 700 | 655 | 1,180 | 484 | – | – |
| test | test (16) | 700 | 614 | 1,159 | 444 | 522 | 480 |

Numbers per system are error spans. Audio is not included; it comes from the Hugging Face dataset
[`edinburghcstr/ami`](https://huggingface.co/datasets/edinburghcstr/ami) (config `ihm`) and is re-created by
`src/prepare_ami.py`. AMI is released under CC BY 4.0.

### Human annotations

| Path | Content |
|---|---|
| `annotation/human_pilot_{A,B}.xlsx` | 50-span pilot, two annotators (used to develop the rubric and choose the teacher) |
| `outputs/human_test_items.csv` | **100-span human test**, final labels of both annotators per span, with teacher, student and baseline scores |
| `annotation/submissions/human_test_*_filled.xlsx` | raw sheets for the human test (annotator A relabeled 57 spans after a display fix, `*_relabel57_filled.xlsx`) |
| `annotation/submissions/pairwise_rater{1,2}_filled.xlsx`, `outputs/pairwise_key.csv` | blind pairwise test and the hidden key (which system is A/B, what each metric prefers) |

### Model and predictions

| Path | Content |
|---|---|
| [Hugging Face model](https://huggingface.co/yixiang666/asr-semantic-severity-distilbert) | DistilBERT with an ordinal head (4 cumulative logits; severity = 1 + Σ sigmoid), trained on `train_all3_9k` |
| `outputs/student_predictions_test+test_extra.jsonl` | student severity for every test span of all five systems |
| `outputs/baselines/` | BERTScore / SemDist / Sentence-BERT distance / span-length scores and metrics (`src/semantic_baselines.py`, `src/semdist_original.py`) |
| `outputs/system_compare.json` | the five-system table above, with bootstrap intervals |

## Quick start

```bash
git clone https://github.com/DEM1TASSE/asr-semantic-wer.git && cd asr-semantic-wer
pixi install          # or: pip install torch transformers pandas scikit-learn scipy jiwer openpyxl krippendorff
```

Read errors and teacher labels:
```python
import json, sys; sys.path.insert(0, "src")
from common import load_errors, single_error_hyp
errors = load_errors(["test", "test_extra"])            # error_id -> span
labels = {r["error_id"]: r for r in map(json.loads, open("outputs/llm_annotations_deepseek-v4-1-flash_v2.4.jsonl"))}
e = next(iter(errors.values()))
print(e["ref_marked"], "|", single_error_hyp(e), "|", labels[e["error_id"]]["severity"])
```
`single_error_hyp(e)` is the reference with only this span replaced by the ASR output; the teacher and the
student judge this sentence, so other errors in the utterance do not affect the score.

Score spans with the student and compare systems (about 11 s for 3,219 spans on one GPU):
```bash
python src/score_student.py --subsets test test_extra   # -> outputs/student_predictions_test+test_extra.jsonl
python src/system_compare.py                            # -> outputs/system_compare.json
```

To score a new ASR system: write its output as `outputs/hyp_<system>.jsonl` (`audio_id`, `hyp`), add it to
`SYSTEMS` in `src/common.py`, run `python src/align.py --subset test`, then the two commands above.

## Reproducing everything

| Step | Command |
|---|---|
| sample utterances | `python src/prepare_ami.py --subset {test,test_extra,dev,train}` |
| ASR | `python src/run_asr.py --model <system> --subset <subset>` (Slurm wrappers in `slurm/`; Parakeet needs NeMo) |
| align, error spans | `python src/align.py --subset <subset>` |
| teacher labels (needs `AZURE_API_KEY` in `.env`) | `python src/annotate_llm.py --backend azure_v1 --model deepseek-v4-1-flash --ids subset:<subset> --tag deepseek-v4-1-flash_v2.4` |
| SemWER, figures | `python src/semwer.py --subset <subset>` |
| student splits | `python src/make_splits.py` |
| train the student | `python src/train_severity_cpu.py --train-split train_all3_9k --objective ordinal --epochs 10 --patience 3 --lr 3e-5 --bs 16` |
| baselines | `python src/semantic_baselines.py --student outputs/student_predictions_test+test_extra.jsonl` |
| human test, pairwise sheets | `python src/make_human_test.py`, `python src/make_pairwise.py` |
| human test evaluation | `python src/human_test_eval.py` |

On the NCSA Delta cluster the code reads audio and the model cache from `SEMWER_WORK`
(default `/work/hdd/bjdh/dwang30/semwer`); elsewhere only the audio steps need it.

Other documents in `docs/` are working notes from the project (plan, meeting notes, intermediate results);
numbers there may be older than the report.
