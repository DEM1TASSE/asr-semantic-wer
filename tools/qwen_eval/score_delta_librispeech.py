import json
from pathlib import Path

import jiwer
from transformers.models.whisper.english_normalizer import EnglishTextNormalizer
from transformers.models.whisper.tokenization_whisper import WhisperTokenizer

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "librispeech/LibriSpeech"
PREDICTIONS = ROOT / "delta-results"
SPLITS = {"test-clean": 2620, "test-other": 2939}
CARD = {"0.6b": {"test-clean": 2.11, "test-other": 4.55},
        "1.7b": {"test-clean": 1.63, "test-other": 3.38}}
HF_CARD = {"0.6b": {"test-clean": 1.69, "test-other": 3.97},
           "1.7b": {"test-clean": 1.24, "test-other": 2.92}}


def main():
    tokenizer = WhisperTokenizer.from_pretrained("openai/whisper-small")
    normalize = EnglishTextNormalizer(tokenizer.english_spelling_normalizer)
    summary = {}
    for split, count in SPLITS.items():
        lines = [line for transcript in (DATA / split).rglob("*.trans.txt") for line in transcript.read_text().splitlines()]
        refs = dict(line.split(" ", 1) for line in lines)
        if len(refs) != len(lines) or len(refs) != count:
            raise ValueError(f"LibriSpeech references are incomplete: {split}")
        refs_normalized = [normalize(text) for text in refs.values()]
        for size in CARD:
            path = PREDICTIONS / f"hyp_qwen3-asr-{size}_{split}.jsonl"
            if not path.exists():
                continue
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            hyp = {row["audio_id"]: row["hyp"] for row in rows}
            if len(rows) != len(hyp):
                raise ValueError(f"Repeated predictions: {path.name}")
            if hyp.keys() != refs.keys():
                print(f"{path.name}: {len(hyp)}/{len(refs)}; awaiting full split")
                continue
            edits = jiwer.process_words(refs_normalized, [normalize(hyp[aid]) for aid in refs])
            wer = edits.wer * 100
            summary[f"{size}/{split}"] = {
                "n_utts": len(refs), "n_ref_words": sum(len(text.split()) for text in refs_normalized),
                "measured_wer_pct": wer, "qwen_original_model_card_pct": CARD[size][split],
                "qwen_hf_model_card_pct": HF_CARD[size][split],
                "delta_vs_original_card_pp": wer - CARD[size][split],
                "delta_vs_hf_card_pp": wer - HF_CARD[size][split],
            }
    (ROOT / "librispeech/delta_benchmark_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
