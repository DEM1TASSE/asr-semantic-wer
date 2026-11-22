#!/bin/bash
#SBATCH --job-name=semwer-qwen
#SBATCH --account=bjdh-delta-gpu
#SBATCH --partition=gpuA40x4-preempt,gpuA100x4-preempt
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --cpus-per-task=6
#SBATCH --mem=32G
#SBATCH --time=01:30:00
#SBATCH --output=logs/%x-%j.log
set -euo pipefail
cd /work/hdd/bjdh/ydai8/semwer/qwen-eval
export HF_HOME="$PWD/models"
export HF_HUB_OFFLINE=1
export PYTHONPATH="$PWD/deps"
export OMP_NUM_THREADS=4
student_python=/work/hdd/bjdh/ydai8/semwer/student-env/bin/python
"$student_python" -u delta_qwen.py --size 1.7B --splits ami-test ami-test-extra test-clean test-other
"$student_python" -u delta_qwen.py --size 0.6B --splits ami-test ami-test-extra test-clean test-other
