#!/bin/bash
#SBATCH --job-name=qwen-cpu
#SBATCH --account=bjdh-delta-cpu
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=24G
#SBATCH --time=01:00:00
#SBATCH --output=logs/%x-%j.log
set -euo pipefail
cd /work/hdd/bjdh/ydai8/semwer/qwen-eval
export HF_HOME="$PWD/models"
export HF_HUB_OFFLINE=1
export PYTHONPATH="$PWD/deps"
export OMP_NUM_THREADS=16
export MKL_NUM_THREADS=16
/work/hdd/bjdh/ydai8/semwer/student-env/bin/python -u delta_qwen_cpu.py --splits ami-test ami-test-extra test-clean
