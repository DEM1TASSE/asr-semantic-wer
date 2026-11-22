# Student training on CPU (Nov 19-20)

`run.sh` trains the three objectives (MSE, cross-entropy, ordinal) on `train_all3_9k`, seed 751, with
`src/train_severity_cpu.py` (run with `--train-split train_all3_9k --objective <obj>`). `summarize.py`
prints the table in `outputs/nov21/student_cpu_objectives.json`. The ordinal run is the checkpoint used
everywhere else in the project.
