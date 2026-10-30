# Progress log

Newest first. Record what was done, the numbers, and anything surprising.

## 2026-10-29
**Pipeline built and run end-to-end through alignment.**

ASR baselines (500 utts, 6.9k ref words):

| system | WER | S | D | I | error spans |
|---|---|---|---|---|---|
| Whisper large-v3 | 11.7 | 2.8 | 8.0 | 0.8 | 447 |
| wav2vec2-large | 22.2 | 11.7 | 7.7 | 2.8 | 840 |

Findings
- Normalization bugs inflated Whisper WER from 11.7 → 13.4: AMI vs ASR spelling variants (`cause`/`because`,
  `t. v.`/`tv`, `alright`), Whisper normalizer reading "oh" as 0 and "ten o'clock" as "100 clock",
  currency symbols being dropped. Fixed in `src/common.py`.
- Over half of Whisper's errors are deletions of repetitions / false starts (it "cleans up" disfluencies),
  which WER counts as errors but barely change meaning.
- wav2vec2 errors are dominated by nonword misspellings and garbled spans.
- Some AMI references are themselves wrong (e.g. `on a val of 76` where Whisper's `out of all 76` is right) → `flag=ref_issue`.

LLM annotation v0 (rubric v0, gpt-5.4-mini, before normalization fixes; archived, not used):
Semantic-WER (hard) Whisper 3.1% vs wav2vec2 10.2% — the gap widens from 1.7× (WER) to 3.3×.
Labels were inconsistent on nonwords (1–5 for similar cases) and misread normalization artifacts →
rubric rewritten as v1 from ~200 manually read samples.
