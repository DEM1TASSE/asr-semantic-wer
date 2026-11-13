# TODO

Owner: **D** = Demi, **Y** = Yixiang, **C** = Claude (agent). Tick when done; move results to `progress.md`.
Experiment design: `docs/plan.md`.

## Done
- [x] Rubric v1 → v2.4 (frozen, tag `rubric-v2.4`)
- [x] Human pilot, 50 items, both annotators; agreement α 0.79; adjudication of gaps ≥ 2
- [x] Teacher comparison on the pilot (gpt-5.4-mini, gpt-4o, DeepSeek) → DeepSeek

## Before checkpoint (Nov 13)
- [ ] **C** DeepSeek labels for all current test spans (1,287); Semantic-WER table, figures, cases
- [ ] **C** Checkpoint report draft in `11751-project-report` (same template as the proposal), prompt in appendix
- [ ] **D+Y** Review and submit on Gradescope

## Before final
- [ ] **C** Sample train (~6,000 utts) / dev (~600) / extra test (~200) utterances; run both ASR systems
- [ ] **C** DeepSeek labels for train 10K, dev 1K, all test spans (~$20)
- [ ] **C** Sample the 200-item human test (100 per ASR; random + surface-feature targeted; no pilot items)
- [ ] **D+Y** Annotate the 200-item human test independently; adjudicate gaps ≥ 2
- [ ] **C** Train DistilBERT: Whisper-5K, wav2vec2-5K, Mixed-5K, Mixed-10K, Mixed 1K/2.5K; 3 seeds
- [ ] **C** Evaluate: weak-label test, human test (+ gpt-4o on the human test), system-level Semantic-WER
- [ ] (optional) sentence-level meaning-preservation ratings; teacher self-consistency
