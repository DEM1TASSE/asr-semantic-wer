"""Train the severity student on fixed AMI splits, selecting checkpoints on dev only."""
import argparse
import json
import random
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.stats import spearmanr
from sklearn.metrics import cohen_kappa_score
from torch.utils.data import DataLoader
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

from common import DATA, OUT, ROOT, load_errors, single_error_hyp


def text_of(error):
    context = " ".join(error["context_before"])
    target = error["ref_marked"] + " [SEP] " + single_error_hyp(error)
    return context, target


def metrics(pred, gold):
    rounded = np.rint(pred).clip(1, 5)
    rho = float(spearmanr(pred, gold).statistic) if len(set(pred)) > 1 and len(set(gold)) > 1 else None
    qwk = float(cohen_kappa_score(np.rint(gold), rounded, labels=[1, 2, 3, 4, 5], weights="quadratic"))
    return {"n": len(gold), "qwk": qwk if np.isfinite(qwk) else None,
            "spearman": rho, "mae": float(np.abs(pred - gold).mean()),
            "within_1": float((np.abs(pred - gold) <= 1).mean()),
            "acc_rounded": float((rounded == gold).mean())}


def ordinal_logits(raw):
    # Each successive threshold has a lower logit for P(Y > threshold).
    gaps = torch.nn.functional.softplus(raw[:, 1:]).cumsum(dim=1)
    return torch.cat((raw[:, :1], raw[:, :1] - gaps), dim=1)


def severity_loss(raw, gold, objective):
    if objective == "mse":
        return torch.nn.functional.mse_loss(raw.squeeze(-1), gold)
    if objective == "ce":
        return torch.nn.functional.cross_entropy(raw, gold.long() - 1)
    thresholds = torch.arange(1, 5, device=gold.device)
    targets = (gold[:, None] > thresholds).to(raw.dtype)
    return torch.nn.functional.binary_cross_entropy_with_logits(ordinal_logits(raw), targets)


def severity_score(raw, objective):
    if objective == "mse":
        return raw.squeeze(-1).clamp(1, 5)
    if objective == "ce":
        levels = torch.arange(1, 6, device=raw.device, dtype=raw.dtype)
        return raw.softmax(dim=-1) @ levels
    return 1 + ordinal_logits(raw).sigmoid().sum(dim=-1)


def evaluate(model, tokenizer, frame, device, batch_size, objective):
    model.eval()
    predictions = []
    with torch.no_grad():
        for start in range(0, len(frame), batch_size):
            batch = frame.iloc[start:start + batch_size]
            encoded = tokenizer(list(batch.ctx), list(batch.tgt), truncation=True,
                                max_length=256, padding=True, return_tensors="pt").to(device)
            predictions.extend(severity_score(model(**encoded).logits, objective).cpu().tolist())
    return np.array(predictions)


def by_system(frame, pred, gold):
    results = {"all": metrics(pred, gold)}
    for system in sorted(frame.system.unique()):
        mask = frame.system.to_numpy() == system
        results[system] = metrics(pred[mask], gold[mask])
    return results


def load_frames(tag, train_split):
    errors = load_errors()
    annotations = {row["error_id"]: row for row in map(json.loads, open(OUT / ("llm_annotations_" + tag + ".jsonl")))}
    frames = {}
    for name in [train_split, "dev_balanced", "test_balanced", "test_all", "pilot_human"]:
        ids = (DATA / "splits" / (name + ".txt")).read_text().splitlines()
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate IDs in " + name)
        rows = []
        for error_id in ids:
            error, annotation = errors[error_id], annotations[error_id]
            if name != "pilot_human" and "ref_issue" in annotation.get("flag", []):
                raise ValueError("ref_issue in " + name + ": " + error_id)
            severity = annotation["severity"]
            if severity not in [1, 2, 3, 4, 5]:
                raise ValueError("Invalid severity for " + error_id)
            context, target = text_of(error)
            rows.append({"error_id": error_id, "meeting_id": error["meeting_id"],
                         "system": error["system"], "ctx": context, "tgt": target, "y": float(severity)})
        frames[name] = pd.DataFrame(rows)
    for left, right in [(train_split, "dev_balanced"), (train_split, "test_all"),
                        ("dev_balanced", "test_all")]:
        if set(frames[left].meeting_id) & set(frames[right].meeting_id):
            raise ValueError("Meeting leakage between " + left + " and " + right)
    for name in [train_split, "dev_balanced", "test_all"]:
        if set(frames[name].error_id) & set(frames["pilot_human"].error_id):
            raise ValueError("Pilot leakage in " + name)
    return frames


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="deepseek-v4-1-flash_v2.4")
    parser.add_argument("--train-split", default="train_all3_9k")
    parser.add_argument("--model", default="distilbert-base-uncased")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--lr", type=float, default=3e-5)
    parser.add_argument("--bs", type=int, default=16)
    parser.add_argument("--seed", type=int, default=751)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--smoke", action="store_true", help="One epoch on 32 train/dev rows; skips test evaluation")
    parser.add_argument("--objective", choices=["mse", "ce", "ordinal"], default="mse")
    parser.add_argument("--patience", type=int, default=0, help="Stop after this many epochs without dev MAE improvement")
    parser.add_argument("--min-epochs", type=int, default=5)
    args = parser.parse_args()
    if not args.train_split.startswith("train_"):
        parser.error("--train-split must name a training ID list")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    frames = load_frames(args.tag, args.train_split)
    print(json.dumps({name: {"n": len(frame), "systems": frame.system.value_counts().to_dict()}
                      for name, frame in frames.items()}), flush=True)
    if args.validate_only:
        return
    output = args.output_dir or OUT / "students" / args.tag / args.train_split / args.objective / ("seed_" + str(args.seed) + ("_smoke" if args.smoke else ""))
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    config = vars(args).copy()
    config["output_dir"] = str(output)
    (output / "config.json").write_text(json.dumps(config, indent=2))
    train, dev = frames[args.train_split], frames["dev_balanced"]
    epochs = args.epochs
    if args.smoke:
        train, dev, epochs = train.iloc[:32], dev.iloc[:32], 1
    device = "cpu"
    torch.set_num_threads(6)
    torch.set_num_interop_threads(1)
    print("device", device, flush=True)
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    num_labels = {"mse": 1, "ce": 5, "ordinal": 4}[args.objective]
    model = AutoModelForSequenceClassification.from_pretrained(args.model, num_labels=num_labels).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    steps = epochs * ((len(train) + args.bs - 1) // args.bs)
    scheduler = get_linear_schedule_with_warmup(optimizer, int(0.1 * steps), steps)
    best_mae = float("inf")
    history = []
    for epoch in range(epochs):
        epoch_started = time.monotonic()
        model.train()
        losses = []
        train_loader = DataLoader(range(len(train)), batch_size=args.bs, shuffle=True)
        for indices in train_loader:
            batch = train.iloc[indices.numpy()]
            encoded = tokenizer(list(batch.ctx), list(batch.tgt), truncation=True,
                                max_length=256, padding=True, return_tensors="pt").to(device)
            gold = torch.tensor(batch.y.values, dtype=torch.float, device=device)
            optimizer.zero_grad()
            loss = severity_loss(model(**encoded).logits, gold, args.objective)
            if not torch.isfinite(loss):
                raise RuntimeError("Non-finite training loss")
            loss.backward()
            optimizer.step()
            scheduler.step()
            losses.append(loss.item())
            if len(losses) in (1, 10, 30) or len(losses) % 100 == 0:
                elapsed = time.monotonic() - epoch_started
                print(f"CPU epoch {epoch+1} step {len(losses)}/{len(train_loader)} "
                      f"loss={loss.item():.4f} elapsed={elapsed:.1f}s", flush=True)
        dev_scores = metrics(evaluate(model, tokenizer, dev, device, args.bs, args.objective), dev.y.values)
        record = {"epoch": epoch + 1, "train_loss": float(np.mean(losses)), "dev": dev_scores,
                  "seconds": time.monotonic() - epoch_started}
        if args.objective == "mse":
            record["train_mse"] = record["train_loss"]
        history.append(record)
        print(json.dumps(record), flush=True)
        (output / "history.json").write_text(json.dumps(history, indent=2))
        if dev_scores["mae"] < best_mae:
            best_mae = dev_scores["mae"]
            best_epoch = epoch + 1
            model.save_pretrained(output / "best")
            tokenizer.save_pretrained(output / "best")
        if args.patience and epoch + 1 >= args.min_epochs and epoch + 1 - best_epoch >= args.patience:
            break
    if args.smoke:
        (output / "smoke_complete.json").write_text(json.dumps(history[-1], indent=2))
        return
    model = AutoModelForSequenceClassification.from_pretrained(output / "best").to(device)
    results = {"best_epoch": best_epoch, "selection_metric": "dev_balanced MAE", "evaluations": {}}
    for name in ["test_balanced", "test_all", "pilot_human"]:
        frame = frames[name]
        pred = evaluate(model, tokenizer, frame, device, args.bs, args.objective)
        gold = frame.y.values
        result = {"student_vs_teacher": by_system(frame, pred, gold)}
        result["mean_baseline"] = by_system(frame, np.full(len(frame), train.y.mean()), gold)
        result["majority_baseline"] = by_system(frame, np.full(len(frame), train.y.mode()[0]), gold)
        saved = frame[["error_id", "system"]].copy()
        saved["pred"], saved["teacher"] = pred, gold
        if name == "pilot_human":
            human = []
            for who in "AB":
                table = pd.read_excel(ROOT / "annotation" / ("human_pilot_" + who + ".xlsx"))
                human.append(pd.to_numeric(table.set_index("error_id").severity, errors="coerce"))
            human_gold = pd.concat(human, axis=1).mean(axis=1).reindex(frame.error_id).to_numpy()
            mask = np.isfinite(human_gold)
            if mask.any():
                result["student_vs_human_mean"] = by_system(frame.loc[mask], pred[mask], human_gold[mask])
                result["teacher_vs_human_mean"] = by_system(frame.loc[mask], gold[mask], human_gold[mask])
            saved["human_mean"] = human_gold
        saved.to_csv(output / (name + "_predictions.csv"), index=False)
        results["evaluations"][name] = result
    results.update(objective=args.objective, epochs_run=len(history), elapsed_seconds=time.monotonic() - started)
    (output / "results.json").write_text(json.dumps(results, indent=2, allow_nan=False))
    print(json.dumps(results, indent=2), flush=True)


if __name__ == "__main__":
    main()
