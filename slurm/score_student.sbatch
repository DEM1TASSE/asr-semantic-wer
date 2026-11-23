#!/bin/bash
#SBATCH --job-name=semwer-student
#SBATCH --account=bjdh-delta-gpu
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=00:20:00
#SBATCH --output=/u/dwang30/project/logs/%x-%j.out
# Score error spans with the trained student, then compare systems. usage: sbatch -p <partition> slurm/score_student.sbatch
set -euo pipefail
cd /u/dwang30/project/src
export HF_HOME=/work/hdd/bjdh/dwang30/semwer/hf_cache
pixi run -q --manifest-path ../pixi.toml python score_student.py --subsets test test_extra
pixi run -q --manifest-path ../pixi.toml python system_compare.py
