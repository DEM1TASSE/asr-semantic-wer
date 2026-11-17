#!/bin/bash
#SBATCH --job-name=semwer-parakeet
#SBATCH --account=bjdh-delta-gpu
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=00:55:00
#SBATCH --output=/u/dwang30/project/logs/%x-%j.out
# Parakeet-TDT (NeMo) on the given subsets. usage: sbatch -p <partition> slurm/asr_parakeet.sbatch test test_extra dev
#        sharded: sbatch -p <partition> slurm/asr_parakeet.sbatch train:<k>:<n>
set -euo pipefail
cd /u/dwang30/project/src
PY=/work/hdd/bjdh/dwang30/semwer/venv_nemo/bin/python
export HF_HOME=/work/hdd/bjdh/dwang30/semwer/hf_cache
nvidia-smi --query-gpu=name --format=csv,noheader
for spec in "$@"; do
  IFS=: read -r s k n <<< "$spec"
  $PY run_asr.py --model parakeet-tdt-0.6b-v2 --subset "$s" --shard "${k:-0}" --nshards "${n:-1}" --bs 16
done
