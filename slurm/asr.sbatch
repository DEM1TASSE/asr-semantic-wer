#!/bin/bash
#SBATCH --job-name=semwer-asr
#SBATCH --account=bjdh-delta-gpu
#SBATCH --partition=gpuA40x4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:30:00
#SBATCH --output=/u/dwang30/project/logs/%x-%j.out
# usage: sbatch slurm/asr.sbatch <subset> [<subset> ...]   (default: test)
set -euo pipefail
cd /u/dwang30/project/src
nvidia-smi --query-gpu=name,driver_version --format=csv
for s in "${@:-test}"; do
  for m in whisper-large-v3 wav2vec2-large; do
    pixi run -q --manifest-path ../pixi.toml python run_asr.py --model "$m" --subset "$s"
  done
done
