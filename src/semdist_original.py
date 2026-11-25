"""SemDist as in the original paper (Kim et al., 2021): 1 - cosine of mean-pooled RoBERTa embeddings.

Same inputs as the other scorers: reference vs. single-error ASR sentence. Mean over the last-layer token
embeddings (special tokens and padding excluded); no fine-tuning, no scaling (scaling does not change any
metric below). Mapped to 1-5 by isotonic regression on dev_balanced (teacher labels), like the other baselines.

Evaluated against: the teacher on test_balanced, the human mean on the 50 pilot spans and on the 100-span
human test. Prints the SBERT-dist numbers from the same run for comparison.

The paper names RoBERTa but describes a BERT-base configuration, so run both:
  python src/semdist_original.py --model roberta-large
  python src/semdist_original.py --model bert-base-uncased
Outputs: outputs/baselines/semdist_<model>_scores.jsonl, outputs/baselines/semdist_<model>_metrics.json
"""
import argparse
import json

import numpy as np
import pandas as pd
import torch
from sklearn.isotonic import IsotonicRegression
from transformers import AutoModel, AutoTokenizer

from common import OUT, load_errors, single_error_hyp
from semantic_baselines import human_pilot, metrics, semdist, split_ids

TEACHER = OUT / "llm_annotations_deepseek-v4-1-flash_v2.4.jsonl"


@torch.no_grad()
def embed(texts, tok, model, device, bs):
    out = []
    for i in range(0, len(texts), bs):
        enc = tok(texts[i:i + bs], padding=True, truncation=True, max_length=256,
                  return_tensors="pt", return_special_tokens_mask=True).to(device)
        special = enc.pop("special_tokens_mask")
        h = model(**enc).last_hidden_state
        m = (enc["attention_mask"] * (1 - special)).unsqueeze(-1).float()
        e = (h * m).sum(1) / m.sum(1).clamp(min=1)
        out.append(torch.nn.functional.normalize(e, dim=-1).cpu())
    return torch.cat(out).numpy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="roberta-large")
    ap.add_argument("--bs", type=int, default=64)
    args = ap.parse_args()

    errors = load_errors(["test", "test_extra", "dev"])
    teacher = {r["error_id"]: r for r in map(json.loads, open(TEACHER))}
    sets = {n: split_ids(n) for n in ["dev_balanced", "test_balanced", "pilot_human", "human_test"]}
    ids = sorted(set().union(*sets.values()))
    refs = [errors[i]["ref"] for i in ids]
    hyps = [single_error_hyp(errors[i]) for i in ids]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModel.from_pretrained(args.model).to(device).eval()
    a, b = embed(refs, tok, model, device, args.bs), embed(hyps, tok, model, device, args.bs)
    rob = 1.0 - (a * b).sum(1)
    sb = semdist(refs, hyps, args.bs)  # SBERT-dist (all-mpnet-base-v2), recomputed for a like-for-like comparison

    rows = {}
    with open(OUT / "baselines" / f"semdist_{args.model.split('/')[-1]}_scores.jsonl", "w") as f:
        for k, i in enumerate(ids):
            t = teacher.get(i)
            rows[i] = {"error_id": i, "system": errors[i]["system"], "semdist_roberta": float(rob[k]),
                       "sbert_dist": float(sb[k]),
                       "teacher": t["severity"] if t and "ref_issue" not in (t.get("flag") or []) else None}
            f.write(json.dumps(rows[i]) + "\n")

    scorers = ["semdist_roberta", "sbert_dist"]
    dev = [rows[i] for i in sets["dev_balanced"] if rows[i]["teacher"] is not None]
    iso = {s: IsotonicRegression(y_min=1, y_max=5, increasing=True, out_of_bounds="clip")
           .fit([r[s] for r in dev], [r["teacher"] for r in dev]) for s in scorers}

    hp = human_pilot()
    ht = pd.read_csv(OUT / "human_test_items.csv").set_index("error_id").human_mean
    gold = {"test_balanced vs teacher": (sets["test_balanced"], lambda i: rows[i]["teacher"]),
            "pilot (50) vs human mean": (sets["pilot_human"], lambda i: hp.get(i)),
            "human test (100) vs human mean": (sets["human_test"], lambda i: ht.get(i))}
    res = {"model": args.model}
    for name, (lst, g) in gold.items():
        sel = [i for i in lst if g(i) is not None and not np.isnan(g(i))]
        y = [g(i) for i in sel]
        res[name] = {s: metrics([rows[i][s] for i in sel], y, iso[s].predict([rows[i][s] for i in sel]))
                     for s in scorers}
        for s in scorers:
            m = res[name][s]
            print(f"{name:32s} {s:16s} n={m['n']:4d} QWK={m['qwk']:.2f} rho={m['spearman']:.2f} MAE={m['mae']:.2f}")
    json.dump(res, open(OUT / "baselines" / f"semdist_{args.model.split('/')[-1]}_metrics.json", "w"), indent=1)


if __name__ == "__main__":
    main()
