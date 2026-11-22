#!/bin/bash
#SBATCH --job-name=semwer-student
#SBATCH --account=bjdh-delta-gpu
#SBATCH --partition=gpuA40x4-interactive
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=logs/student-%j.out
set -euo pipefail
cd "${SLURM_SUBMIT_DIR}"
export SEMWER_WORK="${SEMWER_WORK:-/work/hdd/bjdh/ydai8/semwer}"
export HF_HOME="${SEMWER_WORK}/hf_cache"
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=8
PYTHON="${STUDENT_PYTHON:-${SEMWER_WORK}/student-env/bin/python}"
SEED="${1:-751}"
"$PYTHON" -u -c 'import torch; assert torch.cuda.is_available(), "CUDA unavailable"; print(torch.cuda.get_device_name(0))'
if [ "$SEED" = 751 ]; then
    "$PYTHON" -u src/train_severity.py --smoke --seed "$SEED"
fi
for SPLIT in train_whisper_5k train_wav2vec2_5k train_mixed_5k train_mixed_10k train_mixed_1k train_mixed_2.5k; do
    RESULT="outputs/students/deepseek-v4-1-flash_v2.4/${SPLIT}/seed_${SEED}"
    if [ -f "$RESULT/results.json" ]; then
        continue
    fi
    "$PYTHON" -u src/train_severity.py --train-split "$SPLIT" --seed "$SEED"
done
