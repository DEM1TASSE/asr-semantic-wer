"""Select an evaluation subset of AMI IHM test with oracle segmentation and meeting context.

Output: data/eval_subset.parquet (with audio bytes) and data/eval_subset.jsonl (metadata + context).
"""
import argparse
import json

import pandas as pd
import pyarrow.parquet as pq

from common import AMI_DIR, DATA, EVAL_AUDIO, normalize


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--min_words", type=int, default=5)
    ap.add_argument("--ctx_before", type=int, default=3)
    ap.add_argument("--ctx_after", type=int, default=1)
    ap.add_argument("--seed", type=int, default=751)
    args = ap.parse_args()

    files = sorted(AMI_DIR.glob("test-*.parquet"))
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
    # Stratify across meetings so no single meeting dominates.
    per = max(1, args.n // pool.meeting_id.nunique())
    sel = pool.groupby("meeting_id").sample(n=per, random_state=args.seed)
    if len(sel) < args.n:
        rest = pool.drop(sel.index).sample(args.n - len(sel), random_state=args.seed)
        sel = pd.concat([sel, rest])
    sel = sel.sort_values(["meeting_id", "begin_time"])
    keep = set(sel.audio_id)

    full = pq.read_table(files).to_pandas()
    full = full[full.audio_id.isin(keep)].set_index("audio_id").loc[sel.audio_id].reset_index()
    full["ref_norm"] = sel.ref_norm.values
    full.to_parquet(EVAL_AUDIO)

    with open(DATA / "eval_subset.jsonl", "w") as f:
        for r in sel.to_dict("records"):
            f.write(json.dumps({
                "audio_id": r["audio_id"], "meeting_id": r["meeting_id"], "speaker_id": r["speaker_id"],
                "begin_time": r["begin_time"], "end_time": r["end_time"],
                "ref": r["text"].lower(), "ref_norm": r["ref_norm"], **ctx[r["audio_id"]],
            }) + "\n")
    dur = (sel.end_time - sel.begin_time).sum() / 60
    print(f"selected {len(sel)} utts from {sel.meeting_id.nunique()} meetings, "
          f"{sel.n_words.sum()} ref words, {dur:.1f} min audio")


if __name__ == "__main__":
    main()
