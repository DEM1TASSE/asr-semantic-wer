"""Summarize completed three-system severity experiments from their saved metrics."""
import json
import statistics
from pathlib import Path


def main():
    print("DistilBERT All-3 9K. Test metrics compare with DeepSeek labels.")
    print("Method   Seed   Epochs  Best  Dev MAE (first -> best)  Test MAE  Test QWK  Minutes")
    for method in ("mse", "ce", "ordinal"):
        completed = []
        for seed in (751, 752, 753):
            directory = Path(f"runs/{method}/seed_{seed}")
            if not (directory / "results.json").exists():
                print(f"{method:8} {seed}    awaiting results")
                continue
            result = json.loads((directory / "results.json").read_text())
            history = json.loads((directory / "history.json").read_text())
            metrics = result["evaluations"]["test_balanced"]["student_vs_teacher"]["all"]
            best = result["best_epoch"]
            before = history[0]["dev"]["mae"]
            after = history[best - 1]["dev"]["mae"]
            print(f"{method:8} {seed}    {len(history):>2}     {best:>2}      "
                  f"{before:.4f} -> {after:.4f}        {metrics['mae']:.4f}    "
                  f"{metrics['qwk']:.4f}    {result['elapsed_seconds'] / 60:.1f}")
            completed.append(metrics)
        if len(completed) == 3:
            stats = []
            for key in ("mae", "qwk"):
                values = [row[key] for row in completed]
                stats.append(f"{key.upper()} {statistics.mean(values):.4f} ± {statistics.stdev(values):.4f}")
            print("  Three seeds: " + ", ".join(stats))


if __name__ == "__main__":
    main()
