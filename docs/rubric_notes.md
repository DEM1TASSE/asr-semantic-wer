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
- **Calibration examples must never be pilot or test items.** Before adding one, check that its
  `[[reference → ASR]]` pair does not match any span listed in `outputs/pilot_ids.txt` (or the test set).

## Provenance
Built from a manual reading of ~200 real error spans (AMI IHM test; Whisper large-v3 and wav2vec2):
120 random spans plus targeted samples of numbers, entities, negation, insertions, and long spans;
then calibrated on a 10-item practice set annotated by Demi (outside the pilot set).

Calibration examples that do **not** come from the data (constructed):
- `so [[um → ∅]] we have to decide` (fillers are removed by normalization, so this never occurs as a span)
- `we need to agree on the [[timeline → schedule]]`
- `it would be [[very → ∅]] expensive`
- `we should [[cancel → continue]] the launch`

All other examples are real spans from our eval subset, outside the 50-item pilot.

## Design decisions
- **Severity = semantic distortion (v2.2).** How much the error changes, removes, or adds to the
  information in the utterance. Context is used only to understand what the speaker meant.
  - **Importance dropped.** In the 10-item practice round, importance could not be judged from a
    3-before/1-after window (e.g. whether "4" in `4 too → for to` was a key decision or a casual rating).
    Forcing it would push annotators and the LLM back to category guessing ("numbers matter"). A meeting
    summary (AMI has abstractive summaries) could make importance judgeable later.
  - **Loss vs. contradiction:** lost or garbled information is at most 4; 5 requires the ASR output to
    assert something incompatible with the original (reversed proposition, or the main information
    replaced by an incompatible value/entity, e.g. `22 → 2`). In practice, the main 4/5 disagreement was
    garbled spans containing a negation or number (`capture we do not have → keptorydon tes`,
    `56 designs → fisextrasens`), which are now 4.
  - **No mechanical rules.** An automatic near-miss rule (edit distance + dictionary) was considered and
    rejected: a 1–2 letter change can alter meaning, and a very different string can still be
    recognizable. Annotators judge meaning; they may look up unknown words. Expect some disagreement on
    nonwords and measure it.
  - Content types are spread across severity levels in the examples on purpose, so the label is not
    learned as a proxy for severity.
- **Oracle context.** Context utterances come from the reference transcript, and other errors in the same
  sentence are assumed corrected. We measure the impact of one error in an otherwise correct transcript,
  **not** its impact in a fully noisy ASR transcript. State this in the paper.
- **Sentence-level human judgments** (final report) must use an independent question matching what the
  metric claims, e.g. "how much of the original utterance's meaning is changed or lost in the ASR
  output?", not "what severity would you give".

## Analysis policy for flags
- `ref_issue`: keep the provisional label, but **exclude** from Semantic-WER error counts, from severity
  model training, and from evaluation. Report how many there are.
- `uncertain`: keep; report agreement both with and without these items; may be dropped as
  low-confidence weak labels.
- `multi_issue`: keep; use for sensitivity analysis (results with and without).
- `crosstalk`: keep; report counts per system.

## Human pilot
- 50 items, both annotators label `severity` and `content_type` for all items independently.
  `error_form` is LLM-only (humans may spot-check); `edit_operation` comes from the alignment.
- Sampling: ~70% random (stratified by ASR system) + ~30% targeted (spans with digits or negation words,
  long spans of ≥3 word errors, and substitutions). The sampling type of each item is recorded in
  `outputs/pilot_sampling.csv`, **not** shown in the annotation sheets. Never sample by LLM labels.
- Agreement (`src/agreement.py`): severity: quadratic weighted κ, Krippendorff's α (ordinal), Spearman,
  exact, within-1, MAE; content_type: exact agreement, nominal α, confusion matrix (A vs. B); list of items
  whose severity differs by ≥ 2. Report with and without `uncertain` items. Look at all metrics
  together; rough trigger for another round: α < 0.6 or within-1 < 85%.
- Keep the original independent annotations; record post-discussion changes in a separate copy.

## Changelog
- **v2.2**: severity redefined as semantic distortion only; importance (I) dropped after the practice
  round; 5 reserved for contradiction, loss capped at 4; no mechanical (edit-distance / word-type) rules;
  "look up unknown words" rule; humans label `severity` + `content_type` (+ `flag`, `note`);
  calibration examples per level (≤ 5 each, content types spread across levels), checked to exclude
  pilot items (`pernilla → penila` and `∅ → well maybe there is` were removed for overlapping);
  agreement metrics moved out of the rubric.
- **v2.0**: severity split into distortion D (1–5) and importance I (1–3), combined as
  S = 1 + (D − 1)·I/3. Superseded by v2.2.
- **v1.3**: severity = semantic distortion weighted by contextual importance; context-recoverability
  adjustment removed (context sets importance but never lowers severity).
- **v1.2**: information loss and misinformation both count; offline reader with oracle context; "judge
  meaning, not word identity or type"; content_type tie-break order; `multi_issue` flag; meta-information
  moved out of the rubric.
- **v1.1**: numbers, entities, and negation never automatically 5; recoverability re-judgment instead of
  "reduce by one level"; counterfactual single-error unit; `edit_operation` from alignment; `uncertain`
  flag; several agreement metrics.
- **v1**: built from ~200 real samples; nonword rules, recoverability principle, `content_type`,
  `error_form`, and `flag` fields.
- **v0**: first draft with invented examples, not checked against data (discarded).
