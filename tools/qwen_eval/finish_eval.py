import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = Path("/tmp/asr-semwer-ta-20261118")
SYSTEM = "qwen3-asr-0.6b"
SYSTEM_NAMES = {
    "parakeet-tdt-0.6b-v2": "Parakeet-TDT 0.6B v2",
    SYSTEM: "Qwen3-ASR 0.6B",
    "whisper-large-v3": "Whisper large-v3",
    "wav2vec2-large": "wav2vec2-large",
}


def main():
    asr = json.loads((ROOT / "asr_four_systems.json").read_text())
    student = json.loads((ROOT / "student_four_systems.json").read_text())
    teacher = json.loads((SOURCE / "outputs/semwer_summary_test+test_extra.json").read_text())
    manifest = json.loads((ROOT / "eval_manifest.json").read_text())
    assert set(asr) == set(student) == set(SYSTEM_NAMES)
    assert all(r["n_utts"] == manifest["n_utts"] for r in asr.values())
    assert len({r["n_ref_words"] for r in asr.values()}) == 1
    assert len({r["n_ref_chars_excluding_spaces"] for r in asr.values()}) == 1
    assert all(asr[system]["wer"] == row["wer_full"] for system, row in teacher.items())
    assert all(v["student_semwer_hard"] <= asr[s]["wer"] for s, v in student.items())
    def percent(value):
        return f"{100 * value:.2f}%"

    table = [
        "| ASR system | WER | CER | Student SemWER linear | Student SemWER hard | Student SemWER max | Teacher SemWER hard | Error spans |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for system, name in SYSTEM_NAMES.items():
        a, s = asr[system], student[system]
        t = percent(teacher[system]["semwer_hard"]) if system in teacher else "Pending"
        values = [name, percent(a["wer"]), percent(a["cer"]), percent(s["student_semwer_lin"]),
                  percent(s["student_semwer_hard"]), percent(s["student_semwer_max"]), t, str(a["n_error_spans"])]
        table.append("| " + " | ".join(values) + " |")

    report = """# Four-system ASR evaluation on AMI

All four systems were evaluated on the same 700 presegmented headset-microphone utterances from 16 meetings in the AMI test split. We pooled the repository's original 500 utterances and 200 supplementary utterances. Their audio IDs are unique, and their meetings do not overlap with the development or training meetings. The repository manifest and the Delta audio SHA-256 hashes are recorded in `eval_manifest.json`.

"""
    report += "\n".join(table) + "\n\n"
    report += """WER and CER use the repository's English normalization, 9,347 reference words, and 36,076 non-space reference characters. Both include all utterances and all edits. The same frozen ordinal DistilBERT checkpoint (All-3-9K, seed 751, dev-selected) scored all four systems. Its continuous 1–5 predictions were used for the student SemWER columns. The previously recorded teacher column uses DeepSeek-V4.1-Flash and excludes error spans it flags as possible reference errors.

Qwen was decoded locally using the BF16 MLX conversion of Qwen3-ASR-0.6B, with the English hint, greedy generation, and a 256-token limit. Model snapshot `eae2b51f96265328f1e7beced788adb0e4536f92`. MLX Audio source commit `b973a6cc9954318f0f732943de121ac8919961b8`. The other three systems use the stored hypotheses at repository commit `b915869`.

The frozen student can produce severity scores for Qwen's errors. Measuring its agreement on Qwen requires independent severity labels, which are pending. The existing 1,200-span balanced test set evaluates the student against DeepSeek, with 400 spans from each of the original three ASRs. The 200-span human evaluation is an additional label source. The 700-utterance set scores the recognizers.

## Attached data

- `asr_four_systems.json` has all four WER/CER results and word-edit counts.
- `student_four_systems.json` has student-weighted results. For three systems it also reports agreement with existing teacher labels on identical aligned spans, excluding reference-issue flags.
- `hyp_qwen3-asr-0.6b_test.jsonl` and `hyp_qwen3-asr-0.6b_test_extra.jsonl` contain all Qwen hypotheses.
- `spans_four_systems.jsonl` and `student_predictions_four_systems.jsonl` contain aligned errors and frozen-student scores.
- `teacher_batch` contains the isolated Qwen error spans and the original rubric and annotation runner. The project's Azure deployment credential is required to generate Qwen teacher labels.
"""
    (ROOT / "REPORT.md").write_text(report)
    batch = ROOT / "teacher_batch"
    for dirname in ("src", "outputs", "annotation"):
        (batch / dirname).mkdir(parents=True, exist_ok=True)
    for relative in ("src/common.py", "src/annotate_llm.py", "annotation/rubric.md"):
        shutil.copyfile(SOURCE / relative, batch / relative)
    grouped = {"test": [], "test_extra": []}
    for line in (ROOT / "spans_four_systems.jsonl").read_text().splitlines():
        span = json.loads(line)
        if span["system"] == SYSTEM:
            grouped[span["subset"]].append(line)
    assert sum(map(len, grouped.values())) == asr[SYSTEM]["n_error_spans"]
    for subset, name in (("test", "errors.jsonl"), ("test_extra", "errors_test_extra.jsonl")):
        (batch / "outputs" / name).write_text("\n".join(grouped[subset]) + "\n")
    print("\n".join(table))


if __name__ == "__main__":
    main()
