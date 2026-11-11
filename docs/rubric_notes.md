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
- `[[we cannot buy 12 → we can buy 20]] units` (content_type tie-break)

All other examples are real spans from our eval subset.

## Design decisions
- **Two scores instead of one (v2.0).** Annotators give distortion D (1–5: how much of the utterance's
  meaning is changed or lost) and importance I (1–3: how important the affected original information is
  in the conversation; empty when D = 1). Readability is not scored. One mixed severity score had to
  carry two concepts, which made the rules hard to keep consistent.
  - **Combination:** severity `S = 1 + (D − 1) · I / 3` ∈ [1, 5]; D = 1 ⇒ S = 1 (`common.combine_severity`).
    This is an initial heuristic. Annotators never see it, so they cannot tune D or I toward a target S.
  - **Ablation this enables:** WER vs. distortion-only Semantic-WER vs. D×I Semantic-WER vs. LLM vs.
    DistilBERT. Research question: *does contextual importance improve alignment with human judgments
    beyond semantic distortion alone?*
  - **Avoid circular validation:** sentence-level human judgments must be collected with an independent
    question (e.g. "how much of the original utterance's meaning is changed or lost?" or "how much does
    the ASR output misrepresent the important information?"), never by asking for the combined S.
    Choose the question to match what the final metric claims to measure.
  - Humans label only D, I, flag, note; `content_type` and `error_form` are LLM-only (error profiles).
- **What severity measures (v1.3): semantic distortion weighted by contextual importance**, i.e. how
  much an ASR error changes or removes the meaning of the original utterance, weighted by how important
  the affected information is in the conversation. Principle: *context determines importance, but does
  not erase an ASR error.* Context is used to interpret meaning and judge importance, never to lower
  severity because the information is repeated or recoverable elsewhere.
  - Rejected alternative: reader-oriented residual information loss (what a reader still misunderstands
    after using the context). Reasons: we evaluate ASR fidelity, not reading comprehension; it makes
    annotators simulate a reader's inference (less reliable); and per-error scores that already absorb
    context redundancy are hard to sum in Semantic-WER.
  - Still allowed: if the intended word is identifiable **from the erroneous word itself** (near-miss
    spellings such as `consepts`), little meaning is lost (severity 2). This is about the error's form,
    not about recovery from context.
  - Possible ablation (only if time allows): LLM scores the same items under both definitions; compare
    against sentence-level human judgments. Those judgments must ask the matching question (e.g. "how much
    of the original meaning does the ASR sentence preserve?"), otherwise the comparison is unfair.
- **Oracle context.** Context utterances come from the reference transcript, and other errors in the same
  sentence are assumed corrected. We measure the impact of one error in an otherwise correct transcript,
  **not** its impact in a fully noisy ASR transcript. State this in the paper.
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
- Agreement (`src/agreement.py`): for D and I, quadratic weighted κ, Krippendorff's α (ordinal), exact,
  within-1, MAE; for the derived S, interval α, Spearman, MAE; items to discuss = D differs by ≥ 2,
  I differs by 2, or one rater gave D = 1 and the other did not.
  Look at all of them together. Rough trigger for another round: α < 0.6 or within-1 < 85%.
- Then discuss large disagreements, revise the rubric, and annotate a **new** batch if needed.

## Changelog
- **v2.0**: severity split into distortion D (1–5) and importance I (1–3, empty when D = 1), combined
  in code as S = 1 + (D − 1)·I/3; D levels defined without reference to importance (1 none, 2 slight,
  3 partial, 4 major, 5 reversed) and I levels as background / supporting / core; readability explicitly
  not scored; humans label D, I, flag, note only (content_type and error_form are LLM-only);
  `okay that is → g let us he` moved to D = 2, I = 1.
- **v1.3**: severity redefined as semantic distortion weighted by contextual importance; the
  context-recoverability adjustment is removed (context sets importance but never lowers severity);
  levels 2–5 reworded without "can the reader recover it"; examples moved accordingly
  (`buttons → pitence` 3→4, `12 point fif → 125th` now 5; `its → his` stays 3 as a peripheral referent);
  "detectability" no longer affects the score.
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
