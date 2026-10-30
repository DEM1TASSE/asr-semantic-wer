# TODO

Owner: **D** = Demi, **Y** = Yixiang, **C** = Claude (agent). Tick when done; move results to `progress.md`.

## Before checkpoint (Nov 13)
- [ ] **D+Y** Review `annotation/rubric.md` v1, edit anything that feels wrong
- [ ] **C** Re-annotate all 1,287 spans with gpt-5.4-mini under rubric v1; report cost
- [ ] **C** Regenerate human sets as 50 dev + 200 stratified test
- [ ] **D+Y** Independently annotate the 50-item dev set (`annotation/human_pilot_{A,B}.csv`)
- [ ] **C** `agreement.py`: human-human α, LLM-human; list disagreements → rubric v2 if α < 0.6
- [ ] **C** `semwer.py`: Semantic-WER table, figures, cases
- [ ] **C** Smoke-test DistilBERT training on Delta
- [ ] **D+Y** Write Experimental Setup + Benchmark Results sections; submit

## Before final
- [ ] **D+Y** Annotate the 200-item test set
- [ ] **D+Y** Sentence-level meaning-preservation ratings (100–150 utts)
- [ ] **C** DistilBERT vs DeBERTa-v3 severity predictor, evaluate vs humans
- [ ] **C** Metric correlation: WER / Semantic-WER variants / BERTScore vs sentence ratings
- [ ] (optional) third ASR system: OWSM-CTC (ESPnet)
