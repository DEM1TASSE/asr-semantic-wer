"""Shared paths and text normalization."""
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = Path(os.environ.get("SEMWER_WORK", "/work/hdd/bjdh/dwang30/semwer"))
AMI_DIR = WORK / "data" / "ami" / "ihm"
DATA = ROOT / "data"
OUT = ROOT / "outputs"
EVAL_AUDIO = WORK / "data" / "eval_subset.parquet"  # audio stays out of git, on shared Delta storage
SUBSETS = ["test", "test_extra", "dev", "train"]  # AMI test, test (more utts), validation, train; meetings never overlap across splits


def subset_paths(name):
    """Files for one subset. 'test' keeps the original names so existing annotations stay valid."""
    sfx = "" if name == "test" else f"_{name}"
    return {"meta": DATA / ("eval_subset.jsonl" if name == "test" else f"subset_{name}.jsonl"),
            "audio": EVAL_AUDIO if name == "test" else WORK / "data" / f"subset_{name}.parquet",
            "hyp": lambda model: OUT / f"hyp_{model}{sfx}.jsonl",
            "errors": OUT / f"errors{sfx}.jsonl",
            "wer": OUT / f"wer_summary{sfx}.json"}


def load_errors(subsets=None):
    """All error spans of the given subsets (default: every subset that has been aligned), keyed by error_id."""
    import json
    out = {}
    for s in subsets or SUBSETS:
        p = subset_paths(s)["errors"]
        if p.exists():
            out.update({e["error_id"]: e for e in map(json.loads, open(p))})
    return out


for d in (DATA, OUT):
    d.mkdir(exist_ok=True)

os.environ.setdefault("HF_HOME", str(WORK / "hf_cache"))

_normalizer = None


def normalize(text: str) -> str:
    """Whisper English normalizer, applied identically to refs and hyps."""
    global _normalizer
    if _normalizer is None:
        from transformers.models.whisper.english_normalizer import EnglishTextNormalizer
        from transformers.models.whisper.tokenization_whisper import WhisperTokenizer
        tok = WhisperTokenizer.from_pretrained("openai/whisper-small")
        _normalizer = EnglishTextNormalizer(tok.english_spelling_normalizer)
    text = text.lower()
    # AMI spells acronyms as dotted letters ("t. v.", "r. s. i."); Whisper writes "tv", "rsi".
    text = re.sub(r"\b(?:[a-z]\. ?){2,}", lambda m: m.group(0).replace(".", "").replace(" ", "") + " ", text)
    # The Whisper number normalizer reads "oh"/"o" as zero ("oh no" -> "0 no", "ten o'clock" -> "100 clock").
    text = re.sub(r"\bo(h)?\b(?!')", "ohh", text).replace("o'clock", "oclock")
    # The number normalizer also merges adjacent digit words into one number ("two two different" -> "22",
    # "five six designs" -> "56", "eight eight pm" -> "88 pm"). Normalize such runs word by word instead.
    words, segs = text.split(), [[]]
    for i, w in enumerate(words):
        if i and _DIGIT_WORD.fullmatch(w) and _DIGIT_WORD.fullmatch(words[i - 1]):
            segs.append([])
        segs[-1].append(w)
    out = " ".join(_normalizer(" ".join(seg)) for seg in segs)
    out = re.sub(r"([€£$])\s?(\d[\d.,]*)", r"\2 \1", out)  # "€12.5" -> "12.5 €"
    for sym, word in (("€", " euro "), ("£", " pound "), ("$", " dollar "), ("%", " percent ")):
        out = out.replace(sym, word)
    # Drop stray punctuation the normalizer keeps (e.g. "."), but keep decimal points.
    out = re.sub(r"(?!(?<=\d)\.(?=\d))[^\w\s']", " ", out)
    out = " ".join(_EXTRA.get(w, w) for w in out.split())
    return re.sub(r"\s+", " ", out).strip()


_DIGIT_WORD = re.compile(r"(zero|one|two|three|four|five|six|seven|eight|nine)[.,!?]?")

# Spelling variants that differ between AMI references and ASR output but are not recognition errors.
_EXTRA = {"cause": "because", "'cause": "because", "kinda": "kind of", "alright": "all right",
          "onto": "on to", "aaa": "triple a", "aa": "double a", "okay": "ok", "dunno": "do not know",
          "ohh": "oh", "oclock": "o'clock"}


def single_error_hyp(e):
    """The reference with only this span replaced by the ASR output: what the ASR sentence would be if
    every other recognition error in the utterance were corrected."""
    ref_w = e["ref"].split()
    out = ref_w[:e["ref_start"]] + e["hyp_span"].split() + ref_w[e["ref_end"]:]
    return " ".join(out) or "∅"
