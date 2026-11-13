"""Align hypotheses to references, report WER/S/D/I, and extract error spans.

Adjacent non-equal alignment chunks are merged into one error span, so e.g. a
substitution followed by a deletion is judged as a single semantic error.
Outputs per subset (common.subset_paths): wer_summary*.json, errors*.jsonl
"""
import argparse
import json

import jiwer

from common import SUBSETS, normalize, subset_paths

SYSTEMS = ["whisper-large-v3", "wav2vec2-large"]
MODEL_IDS = {"whisper-large-v3": "openai/whisper-large-v3",
             "wav2vec2-large": "facebook/wav2vec2-large-960h-lv60-self"}


def load_jsonl(p):
    return [json.loads(l) for l in open(p)]


def extract_spans(ref_w, hyp_w, chunks):
    spans, cur = [], None
    for c in chunks:
        if c.type == "equal":
            if cur:
                spans.append(cur)
                cur = None
            continue
        if cur is None:
            cur = {"ref_start": c.ref_start_idx, "hyp_start": c.hyp_start_idx, "S": 0, "D": 0, "I": 0}
        cur["ref_end"], cur["hyp_end"] = c.ref_end_idx, c.hyp_end_idx
        n = max(c.ref_end_idx - c.ref_start_idx, c.hyp_end_idx - c.hyp_start_idx)
        cur[{"substitute": "S", "delete": "D", "insert": "I"}[c.type]] += n
    if cur:
        spans.append(cur)
    for s in spans:
        s["ref_span"] = " ".join(ref_w[s["ref_start"]:s["ref_end"]])
        s["hyp_span"] = " ".join(hyp_w[s["hyp_start"]:s["hyp_end"]])
        s["n_word_errors"] = s["S"] + s["D"] + s["I"]
        ops = [k for k in "SDI" if s[k]]
        s["op"] = {"S": "substitution", "D": "deletion", "I": "insertion"}[ops[0]] if len(ops) == 1 else "mixed"
        # Reference with the error marked inline, used as model/annotator input.
        left, right = ref_w[:s["ref_start"]], ref_w[s["ref_end"]:]
        s["ref_marked"] = " ".join(left + [f"[[{s['ref_span'] or '∅'} → {s['hyp_span'] or '∅'}]]"] + right)
    return spans


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subset", choices=SUBSETS, default="test")
    args = ap.parse_args()
    paths = subset_paths(args.subset)
    utts = {u["audio_id"]: u for u in load_jsonl(paths["meta"])}
    summary, errors = {}, []
    for sysname in SYSTEMS:
        hyps = {h["audio_id"]: h for h in load_jsonl(paths["hyp"](sysname))}
        ids = [a for a in utts if a in hyps]
        # Re-normalize here so normalization fixes apply without re-sampling or re-running ASR.
        refs = [normalize(utts[a]["ref"]) for a in ids]
        hs = [normalize(hyps[a]["hyp"]) for a in ids]
        # jiwer refuses empty strings; an empty hyp is all deletions.
        hs_safe = [h if h else "<empty>" for h in hs]
        out = jiwer.process_words(refs, hs_safe)
        n_ref = sum(len(r.split()) for r in refs)
        summary[sysname] = {"n_utts": len(ids), "n_ref_words": n_ref, "wer": out.wer,
                            "sub": out.substitutions / n_ref, "del": out.deletions / n_ref,
                            "ins": out.insertions / n_ref}
        n_spans = 0
        for k, a in enumerate(ids):
            ref_w, hyp_w = out.references[k], out.hypotheses[k]
            for j, s in enumerate(extract_spans(ref_w, hyp_w, out.alignments[k])):
                u = utts[a]
                errors.append({"error_id": f"{sysname}|{a}|{j}", "subset": args.subset,
                               "ami_split": u.get("ami_split", "test"), "system": sysname,
                               "model_id": hyps[a].get("model_id", MODEL_IDS[sysname]), "audio_id": a,
                               "meeting_id": u["meeting_id"], "speaker_id": u.get("speaker_id"),
                               "begin_time": u.get("begin_time"), "end_time": u.get("end_time"),
                               "ref_raw": u.get("ref_raw", u["ref"]), "hyp_raw": hyps[a]["hyp"],
                               "ref": refs[k], "hyp": hs[k],
                               "context_before": u["context_before"], "context_after": u["context_after"],
                               "utt_n_ref_words": len(ref_w), **s})
                n_spans += 1
        summary[sysname]["n_error_spans"] = n_spans
    json.dump(summary, open(paths["wer"], "w"), indent=2)
    with open(paths["errors"], "w") as f:
        for e in errors:
            f.write(json.dumps(e) + "\n")
    for s, v in summary.items():
        print(f"{s:20s} WER {v['wer']*100:5.1f}  S {v['sub']*100:4.1f} D {v['del']*100:4.1f} "
              f"I {v['ins']*100:4.1f}  spans {v['n_error_spans']}")


if __name__ == "__main__":
    main()
