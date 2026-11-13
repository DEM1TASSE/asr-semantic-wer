#!/bin/bash
#SBATCH --job-name=semwer-asr-shard
#SBATCH --account=bjdh-delta-gpu
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=00:20:00
#SBATCH --output=/u/dwang30/project/logs/%x-%j.out
# usage: sbatch -p <partition> slurm/asr_shard.sbatch <subset> <shard> <nshards>
set -euo pipefail
cd /u/dwang30/project/src
for m in whisper-large-v3 wav2vec2-large; do
  pixi run -q --manifest-path ../pixi.toml python run_asr.py --model "$m" --subset "$1" --shard "$2" --nshards "$3"
done
