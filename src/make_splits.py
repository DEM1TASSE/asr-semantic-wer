"""Build the fixed train / dev / test id lists for the severity student (DistilBERT).

All lists live in data/splits/*.txt (one error_id per line) plus data/splits/manifest.json
(counts, severity distribution, seed). Rules:
  * spans flagged ref_issue by the teacher are dropped everywhere (the reference itself is wrong);
  * the 50 human-pilot items are dropped from train / dev / test (they are a separate eval set);
  * three ASR systems (Whisper, wav2vec2, Parakeet-TDT); "balanced" = equal number of errors per system;
  * main training sets all have 9,000 errors: All-3 (3 x 3,000) and leave-one-system-out (2 x 4,500);
  * samples are stratified by meeting and NESTED (1.5k ⊂ 3k ⊂ 6k ⊂ 9k for All-3; only-<system> 4.5k ⊂
    the leave-one-out sets that contain that system), so larger sets only add data.
Run: pixi run python src/make_splits.py
"""
import json
from collections import Counter

import numpy as np

from common import DATA, OUT, load_errors

SEED = 751
TAG = "deepseek-v4-1-flash_v2.4"
SYSTEMS = {"whisper": "whisper-large-v3", "wav2vec2": "wav2vec2-large", "parakeet": "parakeet-tdt-0.6b-v2"}
TRAIN_TOTAL = 9000   # every main training set has 9,000 errors: All-3 = 3 x 3,000, leave-one-out = 2 x 4,500
EVAL_PER_SYSTEM = 400  # Parakeet has only ~440 test and ~480 dev errors


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
    take = lambda part, sysname, n: order[(part, sysname)][:n]
    for part, need in [("train", TRAIN_TOTAL // 2), ("dev", EVAL_PER_SYSTEM), ("test", EVAL_PER_SYSTEM)]:
        for sname in SYSTEMS:
            assert len(order[(part, sname)]) >= need, f"{part}/{sname}: only {len(order[(part, sname)])} < {need}"
    per3, per2 = TRAIN_TOTAL // 3, TRAIN_TOTAL // 2
    k = lambda n: f"{n / 1000:g}k"
    splits = {}
    # --- main: all three systems, equal share ---
    splits[f"train_all3_{k(TRAIN_TOTAL)}"] = [i for s in SYSTEMS for i in take("train", s, per3)]
    # --- leave-one-system-out: same total size, held-out system never seen in training ---
    for held in SYSTEMS:
        splits[f"train_loo_no_{held}_{k(TRAIN_TOTAL)}"] = [i for s in SYSTEMS if s != held for i in take("train", s, per2)]
    # --- learning curve (All-3, nested in the 9k set) ---
    for n in (500, 1000, 2000):
        splits[f"train_all3_{k(3 * n)}"] = [i for s in SYSTEMS for i in take("train", s, n)]
    # --- optional: one system only (subset of the leave-one-out sets) ---
    for s in SYSTEMS:
        splits[f"train_only_{s}_{k(per2)}"] = take("train", s, per2)
    # --- only if more data is needed: every usable train error (unbalanced) ---
    splits["train_all"] = [i for s in SYSTEMS for i in order[("train", s)]]
    # --- model selection: dev only ---
    splits["dev_balanced"] = [i for s in SYSTEMS for i in take("dev", s, EVAL_PER_SYSTEM)]
    splits["dev_all"] = [i for s in SYSTEMS for i in order[("dev", s)]]
    # --- final evaluation against teacher labels ---
    splits["test_balanced"] = [i for s in SYSTEMS for i in take("test", s, EVAL_PER_SYSTEM)]
    splits["test_all"] = [i for s in SYSTEMS for i in order[("test", s)]]
    # --- 50 human-labelled pilot errors (Whisper + wav2vec2 only) ---
    splits["pilot_human"] = sorted(i for i in pilot if i in errors)
    out = DATA / "splits"
    out.mkdir(exist_ok=True)
    for old in out.glob("*.txt"):
        if old.stem != "human_test":  # written by make_human_test.py
            old.unlink()
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
