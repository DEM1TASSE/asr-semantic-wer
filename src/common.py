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
    out = _normalizer(text)
    out = re.sub(r"([€£$])\s?(\d[\d.,]*)", r"\2 \1", out)  # "€12.5" -> "12.5 €"
    for sym, word in (("€", " euro "), ("£", " pound "), ("$", " dollar "), ("%", " percent ")):
        out = out.replace(sym, word)
    # Drop stray punctuation the normalizer keeps (e.g. "."), but keep decimal points.
    out = re.sub(r"(?!(?<=\d)\.(?=\d))[^\w\s']", " ", out)
    out = " ".join(_EXTRA.get(w, w) for w in out.split())
    return re.sub(r"\s+", " ", out).strip()


# Spelling variants that differ between AMI references and ASR output but are not recognition errors.
_EXTRA = {"cause": "because", "'cause": "because", "kinda": "kind of", "alright": "all right",
          "onto": "on to", "aaa": "triple a", "aa": "double a", "okay": "ok", "dunno": "do not know",
          "ohh": "oh", "oclock": "o'clock"}
