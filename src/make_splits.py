"""Build the fixed train / dev / test id lists for the severity student (DistilBERT).

All lists live in data/splits/*.txt (one error_id per line) plus data/splits/manifest.json
(counts, severity distribution, seed). Rules:
  * spans flagged ref_issue by the teacher are dropped everywhere (the reference itself is wrong);
  * the 50 human-pilot items are dropped from train / dev / test (they are a separate eval set);
  * samples are stratified by meeting and NESTED: Mixed-1K ⊂ Mixed-2.5K ⊂ Mixed-5K ⊂ Mixed-10K, and
    Whisper-5K / wav2vec2-5K are the two halves of Mixed-10K. So larger sets only add data.
Run: pixi run python src/make_splits.py
"""
import json
from collections import Counter

import numpy as np

from common import DATA, OUT, load_errors

SEED = 751
TAG = "deepseek-v4-1-flash_v2.4"
SYSTEMS = {"whisper": "whisper-large-v3", "wav2vec2": "wav2vec2-large"}


def stratified_order(ids, errors, rng):
    """A random order of ids in which every prefix is (approximately) proportional to meeting size."""
    by_m = {}
    for i in ids:
        by_m.setdefault(errors[i]["meeting_id"], []).append(i)
    keyed = []
    for m, lst in by_m.items():
        lst = [lst[k] for k in rng.permutation(len(lst))]
        keyed += [((k + rng.random()) / len(lst), i) for k, i in enumerate(lst)]
    return [i for _, i in sorted(keyed)]


def main():
    rng = np.random.default_rng(SEED)
    errors = load_errors()
    labels = {r["error_id"]: r for r in map(json.loads, open(OUT / f"llm_annotations_{TAG}.jsonl"))}
    pilot = {l.strip() for l in open(OUT / "pilot_ids.txt") if l.strip()}
    usable = {i for i, e in errors.items()
              if i in labels and "ref_issue" not in labels[i]["flag"] and i not in pilot}

    def pool(subsets, system):
        return sorted(i for i in usable if errors[i].get("subset", "test") in subsets
                      and errors[i]["system"] == SYSTEMS[system])

    order = {(part, s): stratified_order(pool(subs, s), errors, rng)
             for part, subs in [("train", {"train"}), ("dev", {"dev"}), ("test", {"test", "test_extra"})]
             for s in SYSTEMS}
    W, V = (lambda part, n: order[(part, "whisper")][:n]), (lambda part, n: order[(part, "wav2vec2")][:n])

    splits = {
        # --- training sets (main experiments) ---
        "train_whisper_5k": W("train", 5000),
        "train_wav2vec2_5k": V("train", 5000),
        "train_mixed_5k": W("train", 2500) + V("train", 2500),
        "train_mixed_10k": W("train", 5000) + V("train", 5000),
        # --- learning curve ---
        "train_mixed_1k": W("train", 500) + V("train", 500),
        "train_mixed_2.5k": W("train", 1250) + V("train", 1250),
        # --- only if 10K is not enough: every usable train span (unbalanced, more wav2vec2) ---
        "train_all": order[("train", "whisper")] + order[("train", "wav2vec2")],
        # --- model selection (early stopping, hyper-parameters): dev only ---
        "dev_balanced": W("dev", 500) + V("dev", 500),
        "dev_all": order[("dev", "whisper")] + order[("dev", "wav2vec2")],
        # --- final evaluation against teacher labels: never used for any decision ---
        "test_balanced": W("test", 500) + V("test", 500),
        "test_all": order[("test", "whisper")] + order[("test", "wav2vec2")],
        # --- 50 human-labelled pilot items (evaluate against human labels) ---
        "pilot_human": sorted(i for i in pilot if i in errors),
    }
    out = DATA / "splits"
    out.mkdir(exist_ok=True)
    manifest = {"seed": SEED, "labels": f"outputs/llm_annotations_{TAG}.jsonl",
                "excluded": "teacher flag ref_issue; the 50 pilot items (except in pilot_human)", "splits": {}}
    for name, ids in splits.items():
        (out / f"{name}.txt").write_text("\n".join(ids) + "\n")
        sysc = Counter(errors[i]["system"] for i in ids)
        sev = Counter(labels[i]["severity"] for i in ids)
        manifest["splits"][name] = {"n": len(ids), "by_system": dict(sysc),
                                    "meetings": len({errors[i]["meeting_id"] for i in ids}),
                                    "severity": {k: sev[k] for k in range(1, 6)}}
        print(f"{name:18s} {len(ids):6d}  {dict(sysc)}  sev {[sev[k] for k in range(1, 6)]}")
    # sanity: no meeting is shared between train / dev / test
    mt = lambda n: {errors[i]["meeting_id"] for i in splits[n]}
    assert not (mt("train_all") & mt("dev_all")) and not (mt("train_all") & mt("test_all"))
    assert not (mt("dev_all") & mt("test_all"))
    json.dump(manifest, open(out / "manifest.json", "w"), indent=2)


if __name__ == "__main__":
    main()
