import argparse
import io
import json
import os
import sys
import time
from pathlib import Path

import pyarrow.parquet as pq
import soundfile as sf

from local_memory import check_memory, configure_mlx

ROOT = Path(__file__).resolve().parent
SOURCE = Path(os.environ.get("SEMWER_EVAL_SOURCE", "/tmp/asr-semwer-ta-20261118"))
os.environ.setdefault("HF_HOME", str(Path.home() / ".cache/huggingface"))
sys.path.insert(0, str(SOURCE / "src"))
from common import normalize

MODEL = "mlx-community/Qwen3-ASR-0.6B-bf16"
SYSTEM = "qwen3-asr-0.6b"
SPLITS = {"test": "eval_subset", "test_extra": "subset_test_extra"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int)
    parser.add_argument("--size", choices=("0.6b", "1.7b"), default="0.6b")
    parser.add_argument("--protected", action="store_true")
    args = parser.parse_args()
    if args.protected:
        configure_mlx(args.size)
    model_id = f"mlx-community/Qwen3-ASR-{args.size.upper()}-bf16"
    system = f"qwen3-asr-{args.size}"
    batches = {}
    for subset, filename in SPLITS.items():
        rows = pq.read_table(ROOT / "audio" / f"{filename}.parquet", columns=["audio_id", "audio"]).to_pylist()
        ids = [row["audio_id"] for row in rows]
        manifest = [json.loads(line)["audio_id"] for line in (SOURCE / "data" / f"{filename}.jsonl").read_text().splitlines()]
        if len(ids) != len(set(ids)) or set(ids) != set(manifest):
            raise ValueError(f"Audio IDs do not match manifest for {subset}")
        batches[subset] = rows
    if set(row["audio_id"] for row in batches["test"]) & set(row["audio_id"] for row in batches["test_extra"]):
        raise ValueError("Test subsets overlap")
    normalize("warm up")
    from mlx_audio.stt.utils import load

    model = load(model_id)
    if args.protected:
        check_memory()
    for subset, rows in batches.items():
        path = ROOT / f"hyp_{system}_{subset}.jsonl"
        completed = set()
        if path.exists():
            completed = {json.loads(line)["audio_id"] for line in path.read_text().splitlines()}
        start = time.monotonic()
        with path.open("a", buffering=1) as stream:
            for i, row in enumerate(rows[:args.limit]):
                if row["audio_id"] in completed:
                    continue
                if args.protected:
                    check_memory()
                audio, rate = sf.read(io.BytesIO(row["audio"]["bytes"]), dtype="float32")
                if audio.ndim > 1:
                    audio = audio.mean(axis=1)
                if rate != 16000:
                    import librosa
                    audio = librosa.resample(audio, orig_sr=rate, target_sr=16000)
                result = model.generate(audio, language="English", max_tokens=256, temperature=0.0)
                hypothesis = result.text.strip()
                stream.write(json.dumps({"audio_id": row["audio_id"], "system": system,
                                         "model_id": model_id, "hyp": hypothesis, "hyp_norm": normalize(hypothesis)}) + "\n")
                if args.protected:
                    time.sleep(0.05)
                if i < 2 or (i + 1) % 25 == 0 or i + 1 == len(rows):
                    print(f"{subset} {i + 1}/{len(rows)} elapsed={time.monotonic() - start:.1f}s", flush=True)

if __name__ == "__main__":
    main()
