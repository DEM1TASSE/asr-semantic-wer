"""Fine-tune a small encoder (DistilBERT by default) to predict error severity from LLM labels.

Input text: "<context> [SEP] <ref with [[ref → hyp]] marked>". Regression on severity (1-5).
Split by meeting to avoid context leakage; human-pilot items are never trained on and are
evaluated against human labels if available.
"""
import argparse
import json

import numpy as np
import pandas as pd
import torch
from scipy.stats import spearmanr
from torch.utils.data import DataLoader
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

from common import OUT, ROOT


def text_of(e):
    ctx = " ".join(e["context_before"][-2:])
    return ctx, e["ref_marked"]


def evaluate(model, tok, df, device, bs=64):
    model.eval(); preds = []
    with torch.no_grad():
        for i in range(0, len(df), bs):
            b = df.iloc[i:i + bs]
            enc = tok(list(b.ctx), list(b.tgt), truncation=True, max_length=256, padding=True,
                      return_tensors="pt").to(device)
            preds += model(**enc).logits.squeeze(-1).clamp(1, 5).tolist()
    return np.array(preds)


def metrics(pred, gold):
    return {"n": len(gold), "spearman": spearmanr(pred, gold).statistic,
            "mae": float(np.abs(pred - gold).mean()),
            "acc_rounded": float((np.rint(pred) == gold).mean())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="gpt-4o")
    ap.add_argument("--model", default="distilbert-base-uncased")
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--lr", type=float, default=3e-5)
    ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--seed", type=int, default=751)
    args = ap.parse_args()
    torch.manual_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    err = pd.DataFrame([json.loads(l) for l in open(OUT / "errors.jsonl")])
    ann = pd.DataFrame([json.loads(l) for l in open(OUT / f"llm_annotations_{args.tag}.jsonl")])
    df = err.merge(ann[["error_id", "severity", "flag"]], on="error_id")
    # Reference errors have no reliable ground truth: never train or evaluate on them.
    is_ref = df.flag.map(lambda f: "ref_issue" in (f if isinstance(f, list) else str(f).split(";")))
    print(f"excluding {is_ref.sum()} ref_issue spans")
    df = df[~is_ref].reset_index(drop=True)
    df[["ctx", "tgt"]] = df.apply(lambda r: pd.Series(text_of(r)), axis=1)
    pilot = set(pd.read_csv(OUT / "pilot_ids.txt", header=None)[0])
    meetings = sorted(df.meeting_id.unique())
    rng = np.random.default_rng(args.seed)
    test_m = set(rng.choice(meetings, size=max(1, len(meetings) // 5), replace=False))
    is_pilot = df.error_id.isin(pilot)
    train = df[~is_pilot & ~df.meeting_id.isin(test_m)].reset_index(drop=True)
    test = df[~is_pilot & df.meeting_id.isin(test_m)].reset_index(drop=True)
    print(f"train {len(train)} | test(LLM labels, held-out meetings {sorted(test_m)}) {len(test)} | "
          f"pilot {is_pilot.sum()}")

    tok = AutoTokenizer.from_pretrained(args.model)
    for t in ["[[", "]]", "→", "∅"]:
        if tok.tokenize(t) == [tok.unk_token]:
            tok.add_tokens([t])
    model = AutoModelForSequenceClassification.from_pretrained(args.model, num_labels=1).to(device)
    model.resize_token_embeddings(len(tok))
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    steps = args.epochs * ((len(train) + args.bs - 1) // args.bs)
    sched = get_linear_schedule_with_warmup(opt, int(0.1 * steps), steps)

    for ep in range(args.epochs):
        model.train(); losses = []
        for idx in DataLoader(range(len(train)), batch_size=args.bs, shuffle=True):
            b = train.iloc[idx.numpy()]
            enc = tok(list(b.ctx), list(b.tgt), truncation=True, max_length=256, padding=True,
                      return_tensors="pt").to(device)
            y = torch.tensor(b.severity.values, dtype=torch.float, device=device)
            loss = torch.nn.functional.mse_loss(model(**enc).logits.squeeze(-1), y)
            loss.backward(); opt.step(); sched.step(); opt.zero_grad(); losses.append(loss.item())
        m = metrics(evaluate(model, tok, test, device), test.severity.values) if len(test) else {}
        print(f"epoch {ep+1} train_mse {np.mean(losses):.3f} test {m}")

    results = {"test_vs_llm": metrics(evaluate(model, tok, test, device), test.severity.values)}
    # Majority-class baseline on the same test split
    maj = train.severity.mode()[0]
    results["majority_baseline_vs_llm"] = metrics(np.full(len(test), float(maj)), test.severity.values)
    P = df[is_pilot].reset_index(drop=True)
    pred_p = evaluate(model, tok, P, device)
    results["pilot_vs_llm"] = metrics(pred_p, P.severity.values)
    hs = []
    for who in "AB":
        p = ROOT / "annotation" / f"human_pilot_{who}.xlsx"
        h = pd.read_excel(p).set_index("error_id").severity
        hs.append(pd.to_numeric(h, errors="coerce"))
    human = pd.concat(hs, axis=1).mean(axis=1).reindex(P.error_id)
    if human.notna().sum() > 5:
        m = human.notna().values
        results["pilot_vs_human_mean"] = metrics(pred_p[m], human.values[m])
        results["llm_vs_human_mean"] = metrics(P.severity.values[m].astype(float), human.values[m])
    print(json.dumps(results, indent=2))
    json.dump(results, open(OUT / f"severity_model_{args.tag}.json", "w"), indent=2)


if __name__ == "__main__":
    main()
