"""Run the same AMI and LibriSpeech inputs on Delta CPU when the GPU is queued."""
import argparse
from pathlib import Path

import torch

import delta_qwen as qwen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", choices=("0.6B", "1.7B"), default="1.7B")
    parser.add_argument("--splits", nargs="+", choices=tuple(qwen.SPLITS), required=True)
    args = parser.parse_args()

    # Keep the CPU checkpoint files independent of the GPU job.
    root = Path(__file__).resolve().parent
    cpu_root = root / "cpu-run"
    cpu_root.mkdir(exist_ok=True)
    libri = cpu_root / "librispeech"
    if not libri.exists():
        libri.symlink_to(root / "librispeech", target_is_directory=True)
    qwen.ROOT = cpu_root
    (cpu_root / "outputs").mkdir(exist_ok=True)

    model = qwen.Qwen3ASRModel.from_pretrained(
        f"Qwen/Qwen3-ASR-{args.size}", dtype=torch.float32, device_map="cpu",
        attn_implementation="sdpa", max_inference_batch_size=8, max_new_tokens=1024)
    ami_done = set()
    for split in args.splits:
        qwen.transcribe(model, qwen.examples(split), split, args.size, 8)
        if split.startswith("ami-"):
            ami_done.add(split)
            if ami_done == {"ami-test", "ami-test-extra"}:
                qwen.score_ami(args.size)
        else:
            qwen.score_librispeech(split, args.size)


if __name__ == "__main__":
    main()
