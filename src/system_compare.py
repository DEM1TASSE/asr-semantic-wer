"""Compare ASR systems by WER and Semantic-WER (teacher and student severities) with a paired bootstrap.

All metrics are corpus-level over the same test utterances (subsets test + test_extra):
  WER          = sum of word edits / reference words
  SemWER-hard  = sum over spans of n_word_errors * (s - 1) / 4 / reference words
  R            = SemWER-hard / WER   (mean semantic severity of an edited word; 0 = all harmless, 1 = all level 5)
Spans the teacher flagged ref_issue (the reference itself is wrong) get weight 0 in SemWER, as in semwer.py.
Paired bootstrap: resample utterances (same resample for every system), 2000 times, seed 751.
Output: outputs/system_compare.json
"""
import json
from collections import defaultdict

import numpy as np

from common import OUT, load_errors, subset_paths

SUBSETS = ["test", "test_extra"]
SYSTEMS = ["qwen3-asr-1.7b", "parakeet-tdt-0.6b-v2", "qwen3-asr-0.6b", "whisper-large-v3", "wav2vec2-large"]
TAG = "deepseek-v4-1-flash_v2.4"


def main():
    errors = load_errors(SUBSETS)
    labels = {r["error_id"]: r for r in map(json.loads, open(OUT / f"llm_annotations_{TAG}.jsonl"))}
    student = {r["error_id"]: r["severity"] for r in map(json.loads, open(OUT / "student_predictions_test+test_extra.jsonl"))}
    utts = [json.loads(l) for s in SUBSETS for l in open(subset_paths(s)["meta"])]
    from common import normalize
    nref = {u["audio_id"]: len(normalize(u["ref"]).split()) for u in utts}
    aids = sorted(nref)
    idx = {a: i for i, a in enumerate(aids)}
    # per-utterance counts: [ref words, edits, teacher-weighted, student-weighted]
    M = {s: np.zeros((len(aids), 4)) for s in SYSTEMS}
    for s in SYSTEMS:
        M[s][:, 0] = [nref[a] for a in aids]
    missing = defaultdict(int)
    for i, e in errors.items():
        if e["system"] not in M:
            continue
        r, n = idx[e["audio_id"]], e["n_word_errors"]
        lab = labels.get(i)
        if lab is None or i not in student:
            missing[e["system"]] += 1
            continue
        ok = "ref_issue" not in lab["flag"]
        M[e["system"]][r, 1] += n
        M[e["system"]][r, 2] += n * (lab["severity"] - 1) / 4 * ok
        M[e["system"]][r, 3] += n * (min(5, max(1, student[i])) - 1) / 4 * ok
    assert not missing, f"spans without teacher or student score: {dict(missing)}"

    def metrics(m):
        N = m[:, 0].sum()
        wer, t, st = m[:, 1].sum() / N, m[:, 2].sum() / N, m[:, 3].sum() / N
        return {"wer": wer, "semwer_hard_teacher": t, "semwer_hard_student": st,
                "R_teacher": t / wer, "R_student": st / wer}

    rng = np.random.default_rng(751)
    boots = [rng.integers(0, len(aids), len(aids)) for _ in range(2000)]
    keys = list(metrics(M[SYSTEMS[0]]))
    B = {s: {k: np.array([metrics(M[s][b])[k] for b in boots]) for k in keys} for s in SYSTEMS}
    res = {"n_utts": len(aids), "n_ref_words": int(M[SYSTEMS[0]][:, 0].sum()), "systems": {}, "paired_p_lower": {}}
    for s in SYSTEMS:
        res["systems"][s] = {k: {"value": v, "ci95": [float(np.percentile(B[s][k], 2.5)), float(np.percentile(B[s][k], 97.5))]}
                             for k, v in metrics(M[s]).items()}
    for a in SYSTEMS:
        for b in SYSTEMS:
            if a < b:
                res["paired_p_lower"][f"{a} < {b}"] = {k: float(np.mean(B[a][k] < B[b][k])) for k in keys}
    json.dump(res, open(OUT / "system_compare.json", "w"), indent=2)

    print(f"{res['n_utts']} utterances, {res['n_ref_words']} reference words (percent)")
    print(f"{'system':22s} {'WER':>14s} {'SemWER teacher':>18s} {'SemWER student':>18s} {'R_t':>5s} {'R_s':>5s}")
    for s in SYSTEMS:
        v = res["systems"][s]
        f = lambda k: f"{100*v[k]['value']:5.2f} [{100*v[k]['ci95'][0]:.2f},{100*v[k]['ci95'][1]:.2f}]"
        print(f"{s:22s} {f('wer'):>14s} {f('semwer_hard_teacher'):>18s} {f('semwer_hard_student'):>18s} "
              f"{v['R_teacher']['value']:5.2f} {v['R_student']['value']:5.2f}")
    print("\nshare of resamples where first system is lower (significant if >= 0.975 or <= 0.025)")
    for pair, p in res["paired_p_lower"].items():
        if "wav2vec2" in pair:
            continue
        print(f"{pair:48s} WER {p['wer']:.3f}  teacher {p['semwer_hard_teacher']:.3f}  student {p['semwer_hard_student']:.3f}")


if __name__ == "__main__":
    main()
