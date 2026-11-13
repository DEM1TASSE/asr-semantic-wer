"""Select a subset of AMI IHM utterances with oracle segmentation and meeting context.

--subset test|dev|train reads the AMI test|validation|train split (meetings never overlap across splits).
Output: audio parquet on /work and a metadata jsonl with context (paths: common.subset_paths).
"""
import argparse
import json

import pandas as pd
import pyarrow.parquet as pq

from common import AMI_DIR, SUBSETS, normalize, subset_paths

HF_SPLIT = {"test": "test", "test_extra": "test", "dev": "validation", "train": "train"}
EXCLUDE = {"test_extra": ["test"]}  # added utterances never repeat an existing subset


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subset", choices=SUBSETS, default="test")
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--min_words", type=int, default=5)
    ap.add_argument("--ctx_before", type=int, default=3)
    ap.add_argument("--ctx_after", type=int, default=1)
    ap.add_argument("--seed", type=int, default=751)
    args = ap.parse_args()

    paths = subset_paths(args.subset)
    files = sorted(AMI_DIR.glob(f"{HF_SPLIT[args.subset]}-*.parquet"))  # train: only the downloaded shards
    meta_cols = ["meeting_id", "audio_id", "text", "begin_time", "end_time", "speaker_id"]
    meta = pq.read_table(files, columns=meta_cols).to_pandas()
    meta = meta.sort_values(["meeting_id", "begin_time"]).reset_index(drop=True)

    # Meeting context comes from the full reference transcript (all speakers, time-ordered).
    ctx = {}
    for mid, g in meta.groupby("meeting_id", sort=False):
        rows = g.to_dict("records")
        for i, r in enumerate(rows):
            before = rows[max(0, i - args.ctx_before):i]
            after = rows[i + 1:i + 1 + args.ctx_after]
            ctx[r["audio_id"]] = {
                "context_before": [f"{b['speaker_id']}: {b['text'].lower()}" for b in before],
                "context_after": [f"{a['speaker_id']}: {a['text'].lower()}" for a in after],
            }

    meta["ref_norm"] = meta.text.map(normalize)
    meta["n_words"] = meta.ref_norm.str.split().str.len()
    pool = meta[meta.n_words >= args.min_words]
    for other in EXCLUDE.get(args.subset, []):
        taken = {json.loads(l)["audio_id"] for l in open(subset_paths(other)["meta"])}
        pool = pool[~pool.audio_id.isin(taken)]
    # Stratify across meetings so no single meeting dominates.
    per = max(1, args.n // pool.meeting_id.nunique())
    # Up to `per` per meeting (some meetings are small); the shuffle makes head() a random sample.
    sel = pool.sample(frac=1, random_state=args.seed).groupby("meeting_id").head(per)
    if len(sel) < args.n:
        rest = pool.drop(sel.index).sample(args.n - len(sel), random_state=args.seed)
        sel = pd.concat([sel, rest])
    sel = sel.sort_values(["meeting_id", "begin_time"])
    keep = set(sel.audio_id)

    full = pq.read_table(files).to_pandas()
    full = full[full.audio_id.isin(keep)].set_index("audio_id").loc[sel.audio_id].reset_index()
    full["ref_norm"] = sel.ref_norm.values
    full.to_parquet(paths["audio"])

    with open(paths["meta"], "w") as f:
        for r in sel.to_dict("records"):
            f.write(json.dumps({
                "audio_id": r["audio_id"], "subset": args.subset, "ami_split": HF_SPLIT[args.subset],
                "meeting_id": r["meeting_id"], "speaker_id": r["speaker_id"],
                "begin_time": r["begin_time"], "end_time": r["end_time"],
                "ref": r["text"].lower(), "ref_raw": r["text"], "ref_norm": r["ref_norm"], "seed": args.seed,
                **ctx[r["audio_id"]],
            }) + "\n")
    dur = (sel.end_time - sel.begin_time).sum() / 60
    print(f"selected {len(sel)} utts from {sel.meeting_id.nunique()} meetings, "
          f"{sel.n_words.sum()} ref words, {dur:.1f} min audio")


if __name__ == "__main__":
    main()
