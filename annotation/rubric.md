# Annotation Guideline: Semantic Distortion of ASR Errors

## 1. What you annotate

Each item is **one error span**: a contiguous stretch where the ASR output differs from the reference transcript (adjacent substitutions, deletions, and insertions are merged into one span).

For each item you see:
- the meeting context: 3 utterances before and 1 after, with speaker IDs, taken from the reference transcript;
- the reference sentence with the error marked as `[[reference → ASR]]`;
- the full ASR output for the sentence;
- `edit_operation` (substitution / deletion / insertion / mixed), generated automatically by the alignment. **Do not annotate it.**

### 1.1 Notation

An error is always written **`[[reference → ASR]]`**:
- **left of the arrow = the reference**, i.e. what the speaker actually said (human transcript);
- **right of the arrow = what the ASR system output**;
- **`∅` = nothing on that side.**

| Written as | Meaning | Example | Explanation |
|---|---|---|---|
| `[[A → ∅]]` | deletion | `the [[the the → ∅]] week` | the speaker said "the the the week"; the ASR output only "the week" |
| `[[∅ → B]]` | insertion | `flying animal [[∅ → ha ha ha]]` | the speaker did not say "ha ha ha"; the ASR added it |
| `[[A → B]]` | substitution | `[[pen → ben]] is here` | the speaker said "pen"; the ASR output "ben" |

Words outside `[[ ]]` were recognized correctly.

## 2. The question you answer

**How much does this error change, remove, or add to the information expressed in what the speaker said?**

Use the surrounding utterances to understand what the speaker meant. Do **not** consider how important the information is for the meeting as a whole.

## 3. Severity (1–5)

| Score | Definition |
|---|---|
| **1 — Negligible** | The meaning is essentially unchanged. Only spelling, grammar, fillers, or fluency differ. |
| **2 — Minor** | A slight change or loss of meaning; the main information is fully preserved. |
| **3 — Moderate** | Some meaningful information is changed or lost, but the main meaning of the utterance survives. |
| **4 — Major** | The main information is clearly changed or lost, including when the main content can no longer be understood. |
| **5 — Critical** | The ASR output expresses information that is the opposite of, or directly contradicts, the main meaning of the original. |

## 4. Content type

Choose the **one** main type of content the error affects.

| Type | Definition |
|---|---|
| `disfluency` | fillers, repetitions, stutters, false starts, tag questions ("isn't it"), backchannels |
| `function_word` | articles, prepositions, pronouns, auxiliaries, conjunctions |
| `content_word` | ordinary words or phrases with lexical meaning (nouns, verbs, adjectives, adverbs) |
| `named_entity` | names of people, places, organizations, products |
| `number` | quantities, times, amounts of money, dates |
| `negation` | expressions with real negative meaning (the truth of a statement depends on them) |
| `other` | none of the above, or several types with no clear main one |

Content type describes **what** the error affects. It does **not** determine severity: every type can occur at every severity level.

## 5. Principles

1. **Judge only the marked span**, assuming every other ASR error has been corrected.
2. **Meaning first.** Do not decide the score from edit distance, part of speech, error length, or whether the ASR output is a real word. Decide it from the meaning that is changed, lost, or added.
3. **Loss vs. contradiction.** Information that is lost or garbled scores **at most 4**. Score **5** only when the ASR output asserts something incompatible with the original's main meaning: a reversed proposition, or the main information replaced by a different, incompatible value or entity.
4. **Context is for understanding.** Use the context to understand what the speaker meant. Do not use it to judge importance for the whole meeting, and do not lower the score because other utterances repeat or compensate for the information.
5. **If you do not know a word** in the reference, look it up. Judge the meaning of the word, not how familiar it is to you.
6. **If the item is clearly ambiguous**, give the most reasonable integer score and add the flag `uncertain`.

## 6. Calibration examples

Scores depend on the given context; they are not assigned by word category. Content types appear at several levels on purpose.

### 1 — Negligible
| Reference → ASR (in context) | Content type | Why |
|---|---|---|
| `so [[um → ∅]] we have to decide` | disfluency | no change in meaning |
| `a sweater [[is → his]] on top or it is behind a plant` | function_word | ungrammatical, but it still says the sweater is on top |
| `it is more idiot proof [[is not it → isn]]` | disfluency | the tag question is damaged; the statement itself is unchanged (the "not" here is not a real negation) |
| `now we are developing a remote control which you [[probably → probly]] already know` | content_word | misspelling only |
| `we need to agree on the [[timeline → schedule]]` | content_word | practically synonymous in this context |

### 2 — Minor
| Reference → ASR (in context) | Content type | Why |
|---|---|---|
| `it would be [[very → ∅]] expensive` | content_word | degree is weakened; the claim is the same |
| `we are focusing on a sort of mid range [[∅ → approach]]` | content_word | the insertion slightly reframes the phrase |
| `we can have you know all [[animals → animal]] shapes` | content_word | plural lost; meaning preserved |
| `if we [[are → were]] doing the kinetic thing` | function_word | tense shifts slightly; the point is the same |
| `the [[telewest → tally west]] remote controls are silver plastic` | named_entity | the brand name is misspelled; it is probably still identifiable |

### 3 — Moderate
| Reference → ASR (in context) | Content type | Why |
|---|---|---|
| `when it sees the amplified [[mo morse code → mormorscot]] signal then it will know what action it has to do` | content_word | the signal type is lost; the main relation (sees signal → acts) survives |
| `i have got to write down a few of [[its → his]] characteristics` | function_word | the pronoun now refers to a person instead of the drawn animal |
| `so we are supposed to [[evaluate it → b evaluated]] right now` | content_word | may swap who evaluates and who is evaluated; deliberately borderline (3 or 4), add `uncertain` if unsure |

### 4 — Major
| Reference → ASR (in context) | Content type | Why |
|---|---|---|
| `i would go for [[4 too → for to]]` (answering "between four or five") | number | the chosen value, the answer to the question, is lost |
| `but we can like think of [[56 designs → fisextrasens]]` | number | the quantity and the object are lost |
| `[[capture we do not have → keptorydon tes]] to do anything with` | content_word | the main statement is garbled; the negation is lost, not reversed |
| `yeah [[pen → ben]] is here on the table` | content_word | the object becomes a person |
| `[[yeah i → you have]] forgot that actually` | function_word | the person who forgot changes |

### 5 — Critical
| Reference → ASR (in context) | Content type | Why |
|---|---|---|
| `i kinda doubt just that it would [[ever → never]] be done` | negation | the stance is reversed |
| `so it is just kind of does [[not → ∅]] really do anything` | negation | deleting "not" turns the statement into its opposite |
| `so yeah that is less [[crude → great]]` | content_word | the evaluation is reversed |
| `it is split over [[22 → 2]] different layers` | number | the main value is replaced by an incompatible one |
| `we should [[cancel → continue]] the launch` | content_word | the action is reversed |

## 7. Fields

| Field | Values |
|---|---|
| `severity` | **required**, integer 1–5 |
| `content_type` | **required**, one of the types in Section 4 |
| `flag` | optional; several values separated by `;` · `ref_issue`: the reference itself looks wrong or unreadable, and the ASR may be right, e.g. `[[on a val of → out of all]] 76` · `crosstalk`: the ASR transcribed another speaker's voice · `uncertain`: the item is clearly ambiguous · `multi_issue`: the span merges several independent errors |
| `note` | optional free text, e.g. which scores you were torn between and why |

## 8. Procedure for human annotators

Annotate **independently**; do not discuss items with the other annotator until both of you have finished. Fill only `severity`, `content_type`, `flag`, and `note`; do not edit the other columns. Keep your original annotations: after discussion, record changes in a separate copy instead of overwriting them.
