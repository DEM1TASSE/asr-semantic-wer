import argparse
import json
import time

from pathlib import Path

import jiwer
import soundfile as sf
from mlx_audio.lm.sample_utils import make_sampler
from mlx_audio.stt.utils import load
from transformers.models.whisper.english_normalizer import EnglishTextNormalizer
from transformers.models.whisper.tokenization_whisper import WhisperTokenizer

from local_memory import check_memory, configure_mlx
from transcribe import ROOT

DATA = ROOT / "librispeech" / "LibriSpeech"
COUNTS = {"test-clean": 2620, "test-other": 2939}
OFFICIAL_WER = {"0.6b": {"test-clean": 2.11, "test-other": 4.55},
                "1.7b": {"test-clean": 1.63, "test-other": 3.38}}


def corpus(split):
    rows = []
    for file in sorted((DATA / split).rglob("*.trans.txt")):
        for line in file.read_text().splitlines():
            utterance_id, reference = line.split(" ", 1)
            audio = file.parent / f"{utterance_id}.flac"
            info = sf.info(audio)
            if info.samplerate != 16000 or info.channels != 1:
                raise ValueError(f"Unexpected format for {audio}")
            rows.append((utterance_id, reference, audio, info.frames))
    if len(rows) != COUNTS[split] or len({row[0] for row in rows}) != len(rows):
        raise ValueError(f"Unexpected dataset coverage for {split}")
    return rows


def decode(model, rows):
    samples = [sf.read(row[2], dtype="float32")[0] for row in rows]
    if len(samples) == 1:
        result = model.generate(samples[0], max_tokens=1024, temperature=0.0, language=None)
        return [result.text.strip()]
    texts, _, _, processed = model._generate_chunks_batched(
        [(sample, 0.0) for sample in samples], max_tokens=1024,
        sampler=make_sampler(0.0), logits_processors=None, language=None,
        system_prompt=None, batch_size=len(samples), verbose=False,
    )
    if not all(processed):
        raise ValueError("Missing batched result")
    return [model.extract_language(text)[1].strip() for text in texts]


def evaluate(split, size, model, batch_size, normalize):
    rows = corpus(split)
    rows.sort(key=lambda row: row[3])
    path = ROOT / "librispeech" / f"hyp_{size}_{split}.jsonl"
    completed = {}
    if path.exists():
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if row["id"] in completed or row["batch_size"] != batch_size:
                raise ValueError(f"Inconsistent resumed output in {path}")
            completed[row["id"]] = row["hyp"]
    if not completed.keys() <= {row[0] for row in rows}:
        raise ValueError("Unexpected saved IDs")
    start = time.monotonic()
    with path.open("a", buffering=1) as stream:
        for offset in range(0, len(rows), batch_size):
            group = rows[offset:offset + batch_size]
            if all(row[0] in completed for row in group):
                continue
            check_memory()
            texts = decode(model, group)
            time.sleep(0.05)
            for (utterance_id, _, _, _), text in zip(group, texts, strict=True):
                if utterance_id in completed:
                    continue
                stream.write(json.dumps({"id": utterance_id, "hyp": text, "batch_size": batch_size}) + "\n")
                completed[utterance_id] = text
            if offset % (batch_size * 16) == 0 or len(completed) == len(rows):
                print(f"{size} {split}: {len(completed)}/{len(rows)} elapsed={time.monotonic() - start:.1f}s", flush=True)
    refs = [normalize(row[1]) for row in rows]
    hyps = [normalize(completed[row[0]]) for row in rows]
    edits = jiwer.process_words(refs, hyps)
    official = OFFICIAL_WER[size][split]
    result = {"n_utts": len(rows), "n_ref_words": sum(len(ref.split()) for ref in refs),
              "wer_pct": 100 * edits.wer, "official_wer_pct": official,
              "delta_pp": 100 * edits.wer - official,
              "scorer": "Whisper EnglishTextNormalizer", "batch_size": batch_size}
    output = ROOT / "librispeech" / f"metrics_{size}_{split}.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(split, size, result, flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", choices=tuple(OFFICIAL_WER), required=True)
    parser.add_argument("--splits", nargs="+", choices=tuple(COUNTS), default=list(COUNTS))
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--check-batch", action="store_true")
    args = parser.parse_args()
    if args.batch_size <= 0:
        raise ValueError("Batch size must be positive")
    tokenizer = WhisperTokenizer.from_pretrained("openai/whisper-small")
    normalize = EnglishTextNormalizer(tokenizer.english_spelling_normalizer)
    configure_mlx(args.size)
    model = load(f"mlx-community/Qwen3-ASR-{args.size.upper()}-bf16")
    check_memory()
    if args.check_batch:
        rows = sorted(corpus("test-clean"), key=lambda row: row[3])
        middle = len(rows) // 2
        group = rows[middle:middle + args.batch_size]
        batch = decode(model, group)
        single = [decode(model, [row])[0] for row in group]
        matches = sum(normalize(x) == normalize(y) for x, y in zip(batch, single))
        print(f"Batched/sequential sanity check: {matches}/{len(group)} normalized matches", flush=True)
        if matches != len(group):
            raise ValueError("Batched decoding diverged on the sanity group")
    for split in args.splits:
        evaluate(split, args.size, model, args.batch_size, normalize)


if __name__ == "__main__":
    main()
