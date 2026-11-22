import argparse
import io
import json
import time
from pathlib import Path

import jiwer
import pyarrow.parquet as pq
import soundfile as sf
import torch
from qwen_asr import Qwen3ASRModel
from transformers.models.whisper.english_normalizer import EnglishTextNormalizer
from transformers.models.whisper.tokenization_whisper import WhisperTokenizer

ROOT = Path(__file__).resolve().parent
AMI = Path("/work/hdd/bjdh/dwang30/semwer/data")
SPLITS = {"ami-test": ("eval_subset.parquet", 500),
          "ami-test-extra": ("subset_test_extra.parquet", 200),
          "test-clean": (None, 2620), "test-other": (None, 2939)}


def examples(split):
    filename, count = SPLITS[split]
    if filename:
        table = pq.read_table(AMI / filename, columns=["audio_id", "audio"])
        rows = [(row["audio_id"], row["audio"]["bytes"]) for row in table.to_pylist()]
        rows.sort(key=lambda row: len(row[1]))
    else:
        directory = ROOT / "librispeech/LibriSpeech" / split
        rows = [(p.stem, p) for p in directory.rglob("*.flac")]
        rows.sort(key=lambda row: sf.info(row[1]).frames)
    if len(rows) != count or len({r[0] for r in rows}) != count:
        raise ValueError(f"Unexpected dataset coverage for {split}: {len(rows)}/{count}")
    return rows


def load_audio(source):
    audio, rate = sf.read(io.BytesIO(source) if isinstance(source, bytes) else source, dtype="float32")
    if rate != 16000 or audio.ndim != 1:
        raise ValueError("Expected mono 16 kHz audio")
    return audio, rate


def transcribe(model, rows, split, size, batch_size):
    system = f"qwen3-asr-{size.lower()}"
    model_id = f"Qwen/Qwen3-ASR-{size}"
    path = ROOT / "outputs" / f"hyp_{system}_{split}.jsonl"
    completed = {}
    if path.exists():
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if row["audio_id"] in completed or row["model_id"] != model_id:
                raise ValueError(f"Invalid checkpoint data in {path}")
            completed[row["audio_id"]] = row["hyp"]
    if not completed.keys() <= {row[0] for row in rows}:
        raise ValueError(f"Unexpected saved IDs in {path}")
    pending = [row for row in rows if row[0] not in completed]
    start = time.monotonic()
    with path.open("a", buffering=1) as stream, torch.inference_mode():
        for pos in range(0, len(pending), batch_size):
            batch = pending[pos:pos + batch_size]
            result = model.transcribe(audio=[load_audio(row[1]) for row in batch],
                                      language="English" if split.startswith("ami-") else None)
            for (aid, _), hyp in zip(batch, result, strict=True):
                stream.write(json.dumps({"audio_id": aid, "system": system, "model_id": model_id,
                                         "hyp": hyp.text.strip()}) + "\n")
            if pos % (batch_size * 8) == 0 or pos + len(batch) == len(pending):
                print(f"{system} {split}: {len(completed) + pos + len(batch)}/{len(rows)} "
                      f"elapsed={time.monotonic() - start:.1f}s", flush=True)


def score_ami(size):
    from ami_eval_normalize import normalize

    directory = Path(__file__).resolve().parent / "ami_manifests"
    system = f"qwen3-asr-{size.lower()}"
    refs, hyps = [], []
    for split, stem in (("ami-test", "eval_subset"), ("ami-test-extra", "subset_test_extra")):
        records = [json.loads(line) for line in (directory / f"{stem}.jsonl").read_text().splitlines()]
        path = ROOT / "outputs" / f"hyp_{system}_{split}.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        by_id = {row["audio_id"]: row["hyp"] for row in rows}
        if len(rows) != len(by_id) or by_id.keys() != {row["audio_id"] for row in records}:
            raise ValueError(f"AMI ID mismatch for {system} {split}")
        refs.extend(normalize(row["ref"]) for row in records)
        hyps.extend(normalize(by_id[row["audio_id"]]) for row in records)
    words = jiwer.process_words(refs, hyps)
    chars = jiwer.process_characters([ref.replace(" ", "") for ref in refs],
                                    [hyp.replace(" ", "") for hyp in hyps])
    result = {"n_utts": len(refs), "wer_pct": 100 * words.wer, "cer_pct": 100 * chars.cer,
              "substitutions": words.substitutions, "deletions": words.deletions, "insertions": words.insertions}
    (ROOT / "outputs" / f"metrics_{system}_ami_700.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"RESULTS {system} AMI 700: {result}", flush=True)


def score_librispeech(split, size):
    directory = ROOT / "librispeech/LibriSpeech" / split
    ref_items = [line.split(" ", 1) for file in directory.rglob("*.trans.txt")
                 for line in file.read_text().splitlines()]
    refs = dict(ref_items)
    key = f"qwen3-asr-{size.lower()}_{split}"
    rows = [json.loads(line) for line in (ROOT / "outputs" / f"hyp_{key}.jsonl").read_text().splitlines()]
    hyp = {row["audio_id"]: row["hyp"] for row in rows}
    if len(ref_items) != len(refs) or refs.keys() != hyp.keys() or len(hyp) != len(rows):
        raise ValueError(f"ID mismatch for {key}")
    tokenizer = WhisperTokenizer.from_pretrained("openai/whisper-small")
    normalize = EnglishTextNormalizer(tokenizer.english_spelling_normalizer)
    score = jiwer.wer([normalize(refs[aid]) for aid in refs], [normalize(hyp[aid]) for aid in refs])
    result = {"n_utts": len(refs), "measured_wer_pct": 100 * score}
    (ROOT / "outputs" / f"metrics_{key}.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"RESULTS {key}: {result}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", required=True, choices=("0.6B", "1.7B"))
    parser.add_argument("--splits", nargs="+", choices=tuple(SPLITS), required=True)
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()
    model = Qwen3ASRModel.from_pretrained(
        f"Qwen/Qwen3-ASR-{args.size}", dtype=torch.bfloat16, device_map="cuda:0",
        attn_implementation="sdpa", max_inference_batch_size=args.batch_size, max_new_tokens=1024)
    (ROOT / "outputs").mkdir(exist_ok=True)
    ami_done = set()
    for split in args.splits:
        transcribe(model, examples(split), split, args.size, args.batch_size)
        if split.startswith("ami-"):
            ami_done.add(split)
            if ami_done == {"ami-test", "ami-test-extra"}:
                score_ami(args.size)
        else:
            score_librispeech(split, args.size)


if __name__ == "__main__":
    main()
