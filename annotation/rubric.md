# ASR Semantic Distortion — Annotation Rubric

## 1. Severity Rubric

**Objective:** Evaluate how much an individual ASR error changes, removes, or introduces semantic information in the current utterance.

| Score | Level | Criteria |
|---|---|---|
| **1** | Negligible | **No semantic change.** Only differences in spelling, grammar, repetition, or fluency; nothing the speaker said is altered. |
| **2** | Minor | **Slight semantic change.** A small change in meaning (e.g., a slightly weaker degree), while the main meaning and specific factual information remain intact. |
| **3** | Moderate | **Partial information distortion.** Meaningful specific information is changed or lost, while the overall meaning of the utterance remains largely preserved. |
| **4** | Major | **Major information distortion.** The main meaning of the utterance is substantially changed, lost, or rendered unintelligible. |
| **5** | Critical | **Reversal of the main meaning.** The direction of the core proposition is reversed, e.g., affirmative vs. negative, accept vs. reject, cancel vs. continue. |

### Decision Guide

Apply the following questions in order:

1. **Is there any change in meaning at all, even a slight one?**
   - No → **1**
2. **Is the direction of the core proposition reversed?**
   - Yes → **5**
3. **Is the main meaning of the utterance substantially changed, lost, or rendered unintelligible?**
   - Yes → **4**
4. **Is meaningful specific information changed or lost, while the overall meaning remains largely preserved?**
   - Yes → **3**
   - No, there is only a slight change in meaning → **2**

### Scoring Principles

- **Evaluate only the marked error span.** Assume all other ASR errors in the same utterance have been corrected.
- **Use context to interpret meaning.** Previous and following utterances may help resolve references and ellipsis, but do not judge how important the information is to the overall meeting or use other utterances to compensate for the target error.
- **Meaning takes precedence over surface form.** Do not assign severity based solely on singular/plural forms, tense, word order, edit distance, error length, or whether the output is a nonword. If you do not know a word in the reference, look it up.
- **A different value is not automatically severe.** Judge how much the meaning changes: `a few → several` barely changes it, while `22 → 2` states a clearly wrong quantity.
- **Distinguish distortion from reversal.** Missing, garbled, or wrong information can receive at most **4**; reserve **5** for reversing the direction of the core proposition.
- **When uncertain**, assign the most reasonable integer score and add the `uncertain` flag.

## 2. Calibration Examples

Notation: `[[reference → ASR]]`, where `∅` indicates an empty string.

These examples illustrate the scoring boundaries. They are not fixed rules for all errors of the same type.

### 1 — Negligible

| Reference → ASR | Rationale |
|---|---|
| `i gave it [[a → ∅]] one` | Removing the article does not change the meaning. |
| `all [[animals → animal]] shapes` | The grammatical form changes, but the intended meaning remains the same. |
| `i [[am i → ∅]] was a bit worried` | The ASR removes an abandoned false start. |

### 2 — Minor

| Reference → ASR | Rationale |
|---|---|
| `it would be [[very → ∅]] expensive` | The degree of expense is weakened, but the main judgment remains unchanged. |

### 3 — Moderate

| Reference → ASR | Rationale |
|---|---|
| `the amplified [[morse code → mormorscot]] signal` | The specific signal type becomes unclear, but the overall meaning (it sees a signal, then acts) remains. |
| `let us use the [[blue → ∅]] pen for the logo` | The pen's color is lost, but the plan to use a pen remains intact. |

### 4 — Major

| Reference → ASR | Rationale |
|---|---|
| `i would go for [[4 too → for to]]` (previous context: “between four or five”) | The speaker's answer is lost. |
| `it is split over [[22 → 2]] different layers` | The number of layers, the main point of the utterance, is substantially changed. |
| `[[capture we do not have → keptorydon tes]] to do anything with` | A major part of the proposition becomes unintelligible. |

### 5 — Critical

| Reference → ASR | Rationale |
|---|---|
| `it does [[not → ∅]] really do anything` | A negative assertion becomes affirmative. |
| `we should [[cancel → continue]] the launch` | The intended action is reversed. |
| `the budget was [[approved → rejected]]` | The stated outcome is reversed. |

## 3. Content Type

Select **one primary content type** affected by the error. Content type does not determine severity.

| Label | Definition |
|---|---|
| `disfluency` | Fillers, repetitions, stuttering, abandoned false starts, tag questions, backchannels |
| `function_word` | Articles, prepositions, pronouns, auxiliary verbs, conjunctions |
| `content_word` | Ordinary content words or phrases, including nouns, verbs, adjectives, and adverbs |
| `named_entity` | Person names, locations, organizations, product names |
| `number` | Quantities, dates, times, monetary amounts |
| `negation` | Expressions that determine whether a proposition is affirmative or negative |
| `other` | Other cases, or errors involving multiple types without a clear primary category |

## 4. Annotation Instructions

### Annotation Unit

Each sample contains one contiguous ASR error span. Adjacent substitutions, deletions, and insertions have already been merged during preprocessing.

For each sample, you will see:

- The reference utterance and the complete ASR hypothesis.
- The preceding three and following one meeting utterances, with speaker IDs.
- The target error marked as `[[reference → ASR]]`.
- An automatically generated `edit_operation`, which does not require manual annotation.

### Required Fields

| Field | Value |
|---|---|
| `severity` | Integer from 1 to 5 |
| `content_type` | One category from Section 3 |

### Optional Fields

| Field | Value |
|---|---|
| `flag` | `ref_issue` / `crosstalk` / `uncertain` / `multi_issue`; multiple flags allowed |
| `note` | Brief explanation of ambiguity or reasoning |

Flag definitions:

- `ref_issue`: The reference transcription may be incorrect or unusable.
- `crosstalk`: The ASR may have transcribed speech from another speaker.
- `uncertain`: The available context is insufficient for a reliable judgment.
- `multi_issue`: The error span combines multiple independent errors.