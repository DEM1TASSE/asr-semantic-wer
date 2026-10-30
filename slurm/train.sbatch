#!/bin/bash
#SBATCH --job-name=semwer-train
#SBATCH --account=bjdh-delta-gpu
#SBATCH --partition=gpuA40x4
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=00:45:00
#SBATCH --output=/u/dwang30/project/logs/%x-%j.out
set -euo pipefail
cd /u/dwang30/project/src
pixi run -q --manifest-path ../pixi.toml python train_severity.py "$@"
