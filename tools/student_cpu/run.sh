#!/bin/bash
set -u
cd "$(dirname "$0")"
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=6
export VECLIB_MAXIMUM_THREADS=6
export HF_HOME="$PWD/model-cache"
export HF_HUB_DISABLE_XET=1
python=.venv/bin/python
mkdir -p logs
echo "Started at $(date)"
for objective in mse ce ordinal; do
    output="runs/$objective/seed_751"
    [[ ! -s "$output/results.json" ]] || continue
    if [[ -e "$output" ]]; then mv "$output" "$output.incomplete.$(date +%s)"; fi
    echo "$(date) Starting $objective on CPU"
    "$python" -u src/train_severity.py --train-split train_all3_9k --objective "$objective" \
        --seed 751 --epochs 10 --min-epochs 5 --patience 3 --output-dir "$output" \
        > "logs/$objective.log" 2>&1
    status=$?
    echo "$(date) $objective exited $status"
    "$python" summarize.py > summary.txt.tmp && mv summary.txt.tmp summary.txt
done
echo "Finished at $(date)"
