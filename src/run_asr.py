"""Run a pretrained ASR model on the eval subset (oracle segmentation).

Output: outputs/hyp_<name>.jsonl with raw and normalized hypotheses.
"""
import argparse
import io
import json

import librosa
import numpy as np
import pandas as pd
import soundfile as sf
import torch
from tqdm import tqdm

from common import SUBSETS, normalize, subset_paths

MODELS = {
    "whisper-large-v3": ("whisper", "openai/whisper-large-v3"),
    "wav2vec2-large": ("ctc", "facebook/wav2vec2-large-960h-lv60-self"),
    # Transducer (FastConformer-TDT); needs NeMo: run with /work/.../venv_nemo/bin/python
    "parakeet-tdt-0.6b-v2": ("nemo", "nvidia/parakeet-tdt-0.6b-v2"),
}


def load_audio(b):
    wav, sr = sf.read(io.BytesIO(b["bytes"]), dtype="float32")
    if wav.ndim > 1:
        wav = wav.mean(1)
    if sr != 16000:
        wav = librosa.resample(wav, orig_sr=sr, target_sr=16000)
    return wav


@torch.inference_mode()
def run_whisper(model_id, audios, bs, device):
    from transformers import WhisperForConditionalGeneration, WhisperProcessor
    proc = WhisperProcessor.from_pretrained(model_id)
    model = WhisperForConditionalGeneration.from_pretrained(model_id, torch_dtype=torch.float16).to(device).eval()
    outs = []
    for i in tqdm(range(0, len(audios), bs)):
        feats = proc(audios[i:i + bs], sampling_rate=16000, return_tensors="pt").input_features
        ids = model.generate(feats.to(device, torch.float16), language="en", task="transcribe",
                             num_beams=5, max_new_tokens=200)
        outs += proc.batch_decode(ids, skip_special_tokens=True)
    return outs


@torch.inference_mode()
def run_ctc(model_id, audios, bs, device):
    from transformers import AutoModelForCTC, AutoProcessor
    proc = AutoProcessor.from_pretrained(model_id)
    model = AutoModelForCTC.from_pretrained(model_id).to(device).eval()
    outs = []
    for i in tqdm(range(0, len(audios), bs)):
        inp = proc(audios[i:i + bs], sampling_rate=16000, return_tensors="pt", padding=True)
        logits = model(inp.input_values.to(device), attention_mask=inp.attention_mask.to(device)).logits
        outs += proc.batch_decode(logits.argmax(-1))
    return outs


@torch.inference_mode()
def run_nemo(model_id, audios, bs, device):
    import nemo.collections.asr as nemo_asr
    from omegaconf import open_dict
    model = nemo_asr.models.ASRModel.from_pretrained(model_id).to(device).eval()  # greedy TDT decoding
    # The CUDA-graph greedy decoder crashed (illegal memory access) on the train subset; the plain loop
    # gives the same greedy output.
    dec = model.cfg.decoding
    with open_dict(dec):
        dec.greedy.use_cuda_graph_decoder = False
    model.change_decoding_strategy(dec)
    outs = []
    for i in tqdm(range(0, len(audios), bs)):
        res = model.transcribe(audios[i:i + bs], batch_size=bs, verbose=False)
        res = res[0] if isinstance(res, tuple) else res
        outs += [r.text if hasattr(r, "text") else r for r in res]
    return outs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=MODELS)
    ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--subset", choices=SUBSETS, default="test")
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1, help="split a subset into short jobs; merge with merge_shards")
    args = ap.parse_args()
    kind, model_id = MODELS[args.model]
    device = "cuda" if torch.cuda.is_available() else "cpu"

    paths = subset_paths(args.subset)
    df = pd.read_parquet(paths["audio"])
    if args.nshards > 1:
        df = df.iloc[args.shard::args.nshards].reset_index(drop=True)
    audios = [load_audio(a) for a in df.audio]
    # Sort by length for efficient batching, then restore order.
    order = np.argsort([len(a) for a in audios])
    fn = {"whisper": run_whisper, "ctc": run_ctc, "nemo": run_nemo}[kind]
    hyps_sorted = fn(model_id, [audios[j] for j in order], args.bs, device)
    hyps = [None] * len(audios)
    for j, h in zip(order, hyps_sorted):
        hyps[j] = h.strip()

    out = paths["hyp"](args.model)
    if args.nshards > 1:
        out = out.with_suffix(f".part{args.shard}of{args.nshards}")
    with open(out, "w") as f:
        for aid, h in zip(df.audio_id, hyps):
            f.write(json.dumps({"audio_id": aid, "system": args.model, "model_id": model_id, "hyp": h,
                                "hyp_norm": normalize(h)}) + "\n")
    print(f"wrote {len(hyps)} hyps for {args.model} ({model_id})")


if __name__ == "__main__":
    main()
