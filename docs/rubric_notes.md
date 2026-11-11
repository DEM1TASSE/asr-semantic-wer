# Rubric notes (for the team, not for annotators)

The guideline itself is `annotation/rubric.md` (English) with a Chinese translation in
`annotation/rubric_zh.md`. This file records everything about the guideline that annotators and the
LLM do not need to see: provenance, design decisions, analysis policy, and the changelog.

## Maintenance
- `rubric.md` is inserted verbatim into the LLM prompt (`src/annotate_llm.py`), so it must contain only
  annotation instructions: no provenance, version history, or analysis plans.
- **English is authoritative.** Edit `rubric.md` first, then mirror the change in `rubric_zh.md`.
- After the human pilot starts, change the rubric **only** in response to observed disagreements, not
  by adding rules from intuition. Record each change below with the items that motivated it.

## Provenance
Built from a manual reading of ~200 real error spans (AMI IHM test; Whisper large-v3 and wav2vec2):
120 random spans plus targeted samples of numbers, entities, negation, insertions, and long spans.

Examples that do **not** come from the data (constructed to illustrate a rule):
- `we should [[cancel → ∅ / continue]] the launch` (loss vs. misinformation)
- `a [[big → large]] screen`, `the budget was [[approved → rejected]]` (meaning vs. word identity)
- `it would be [[very → ∅]] expensive` (lost modifier)
- a wrong name mentioned in passing → 3; a wrong number mentioned in passing → 3–4 (high-risk types)
- context says 12 but ASR wrote 20 (conflicting context)
- `[[we cannot buy 12 → we can buy 20]] units` (content_type tie-break)

All other examples are real spans from our eval subset.

## Design decisions
- **Reader setting:** an offline reader of the ASR transcript after the meeting, allowed to use the
  following utterance.
- **Oracle-context severity.** Context utterances come from the reference transcript, and other errors
  in the same sentence are assumed corrected. This matches the counterfactual single-error unit. It
  means we measure the impact of one error in an otherwise correct transcript, **not** its impact in a
  fully noisy ASR transcript. State this in the paper. (A noisy-context variant would require ASR
  output for the neighbouring utterances, which we do not currently have.)
- **content_type tie-break order** (negation > number > named_entity > content_word > function_word >
  disfluency > other) exists only for label consistency; it must not influence severity.
- **Category independence.** Numbers, entities, and negation are high-risk but never automatically 5.
  Otherwise a severity model could learn "number/negation ⇒ 5" instead of contextual impact, which
  would undercut the claim that context-aware scoring beats fixed category weighting.

## Analysis policy for flags
- `ref_issue`: keep the provisional label, but **exclude** from Semantic-WER error counts, from severity
  model training, and from evaluation. Report how many there are.
- `uncertain`: keep; report human agreement both with and without these items; may be dropped as
  low-confidence weak labels.
- `multi_issue`: keep; use for sensitivity analysis (results with and without).
- `crosstalk`: keep; report counts per system.

## Human pilot
- 50 items, both annotators label all items independently.
- Sampling: ~70% random (stratified by ASR system) + ~30% targeted (spans with digits or negation words,
  long spans of ≥3 word errors, and substitutions). The sampling type of each item is recorded in
  `outputs/pilot_sampling.csv`, **not** shown in the annotation sheets. Never sample by LLM labels.
- Agreement (`src/agreement.py`): severity quadratic weighted κ, Krippendorff's α (ordinal), exact,
  within-1, MAE; nominal α for content_type and error_form; list of items differing by ≥ 2.
  Look at all of them together. Rough trigger for another round: α < 0.6 or within-1 < 85%.
- Then discuss large disagreements, revise the rubric, and annotate a **new** batch if needed.

## Changelog
- **v1.2**: information loss and misinformation both count, and fluency never overrides importance;
  reader fixed as an offline transcript reader with oracle (reference) context, allowed to use the
  following utterance; "judge meaning, not word identity or type" rule with synonym/one-word-reversal
  examples; content_type tie-break order; `flag` gains `multi_issue`, severity is always filled for
  flagged items; meta-information (provenance, changelog, analysis policy) moved out of the rubric
  into this file.
- **v1.1**: numbers, entities, and negation are high-risk types but never automatically 5, with one
  shared severity standard; the "reduce by one level if redundant" rule became a recoverability
  re-judgment, with a rule for conflicting context; counterfactual single-error unit stated;
  `edit_operation` produced by alignment, `error_form` describes only the form; `flag` gains
  `uncertain` and allows multiple values; agreement judged on several metrics.
- **v1**: built from ~200 real samples; nonword rules, recoverability principle, `content_type`,
  `error_form`, and `flag` fields.
- **v0**: first draft with invented examples, not checked against data (discarded).
