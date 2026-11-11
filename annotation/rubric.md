# Annotation Guideline: Semantic Severity of ASR Errors

## 1. What you annotate

Each item is **one error span**: a contiguous stretch where the ASR output differs from the reference transcript (adjacent substitutions, deletions, and insertions are merged into one span).

For each item you see:
- the meeting context: 3 utterances before and 1 after, with speaker IDs, taken from the **reference transcript**;
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

**How much information would a reader lose or misunderstand because of this one error?**

### 2.1 The reader

The reader is **an offline reader reviewing an ASR-generated meeting transcript** after the meeting (for example, someone reading the notes). The reader has no audio, but can read the surrounding transcript shown with the item, **including the following utterance**.

### 2.2 Unit: the counterfactual impact of a single error

For the target error, **assume every other part of the transcript is correct**: the other recognition errors in the same sentence have been corrected, and the context utterances are exactly as shown. Severity measures the impact of **this error alone**. Do not consider the joint impact of several errors in one sentence; that is studied separately.

### 2.3 Two factors decide severity

1. **Importance in this conversation.** Does the affected content carry a core fact, a decision, an action, who is responsible, a key quantity, or the speaker's stance? Or is it background detail or social filler?
2. **Recoverability.** Could the reader **reliably** recover the intended meaning, i.e. guess the original word or meaning with high confidence from the sentence and the shown context?

Errors affect meaning in two ways, and both count:
- **Information loss**: content is deleted or becomes unreadable (nonwords, garbled text). The reader usually notices that something is wrong but cannot tell what was said.
- **Misinformation**: content is replaced by fluent but different content. The reader is misled without any warning.

A visibly corrupted error is **not** necessarily minor: losing an essential decision or action can be as serious as replacing it with a wrong one. For example, *we should [[cancel → ∅]] the launch* and *we should [[cancel → continue]] the launch* can both deserve 4–5. Fluency and recoverability inform the score, but **never override the importance of the affected content**.

### 2.4 Judge meaning, not word identity or word type

Score the **semantic consequence**, not how different the words look and not what type of word is affected.
- A synonym or paraphrase that fully preserves the intended meaning receives 1, even for a content word: *a [[big → large]] screen*.
- A one-word change can receive 5 when it reverses a consequential proposition: *the budget was [[approved → rejected]]*.
- Numbers, names, and negation are **high-risk content types**: errors in them are often severe, but they are **never automatically 5**. Every content type is scored by the two factors above. For example, `as you already know i am [[betty → betsy]]` changes the speaker's self-introduction → 5, while a wrong name for a person mentioned in passing, who plays no role in the discussion, may be only 3. Likewise, `it is split over [[22 → 2]] different layers` changes a design parameter under discussion → 5, while a wrong number mentioned in passing that affects no conclusion may be 3–4.

## 3. Severity scale (1–5)

The examples below show typical cases. The principles in Section 2 take precedence: the same surface pattern can deserve a different score in a different context.

### 1 = No impact: meaning is exactly the same with or without the error
- **Repetitions, stutter fragments, abandoned false starts**, even when several words long: `i [[am i → ∅]] was a bit worried`, `the [[the the → ∅]] week`, `dogs can [[som → ∅]] sometimes`, `[[the sort of → ∅]] i had a quick look`
- **Fillers, discourse markers, backchannels**: `[[yeah → ∅]] i have got one at home`, `75 [[i mean → ∅]]`, `a 5 actually [[cause → ∅]]` (unfinished trailing word)
- **Insertions that add no meaning**: laughter `[[∅ → ha ha ha]]`, a single function word `[[∅ → the]]`, `[[∅ → like]]`
- **Synonyms or paraphrases with identical meaning**; **spelling or formatting variants**

### 2 = Minor: reads awkwardly, but the reader can **reliably** recover the intended meaning
- **Nonwords whose intended word is obvious**: `[[concepts → consepts]]`, `[[probably → probly]]`, `[[thing → ting]]`, `in [[euros → uros]]`, `[[sony → soni]]`
- **Inflection changes**: `all [[animals → animal]] shapes`, `double [[curved → curves]]`, `different [[kind → kinds]]`
- **Article or preposition swaps; tense changes that do not alter the point**: `with [[the → a]] touch screen`, `we [[are → were]] doing the kinetic thing`
- **Word merges or splits**: `[[i was → iwas]]`

### 3 = Moderate: local information is lost or blurred and the reader must guess, **possibly wrongly**; or the changed content is unimportant
- **Nonwords whose intended word cannot be recognized, where the lost word is not central**: `less [[buttons → pitence]]` (context partly suggests it)
- **Low-information phrases turned into garbage**: `[[okay that is → g let us he]] good timing`
- **Lost modifiers or degree words**: `it would be [[very → ∅]] expensive`
- **Pronoun changes where context still identifies the referent**: `[[its → his]] characteristics`
- **Fluent but harmless insertions** that make it look as if the speaker said more (often crosstalk): `no [[∅ → well maybe there is]]`
- **High-risk content type, but the content is unimportant in this conversation**, e.g. a minor name or a number mentioned in passing replaced by another one

### 4 = Serious: key content is lost, or the reader receives **wrong but plausible** information
- **Real-word substitutions that keep the sentence fluent but change its meaning**: `for the [[whole → horror]] of the language`, `take some [[notes → not]]`, `[[pen → ben]] is here on the table` (an object becomes a person)
- **Changed referent (who did it / who is addressed)**: `[[yeah i → you have]] forgot that actually`, `so [[you → he]] would not be pressing`
- **The core proposition of the sentence is lost or garbled**: `then that [[is going to be kind of fun → cannow becanaphone]]`; `[[i kinda doubt just that → commondor she said]] it would ever be done` (the speaker's stance is lost and a false "she said" is added)
- **Fluent hallucinated insertions that add content the speaker never said**: `so basically [[∅ → a person will]] not point or click`

### 5 = Critical: changes or destroys a **core fact, decision, action, responsible person, or key quantity** that the conversation depends on, and the context cannot correct it
- **A value under discussion is changed**: `it is split over [[22 → 2]] different layers` (discussing a design parameter), `we can like think of [[56 → physics]] designs`
- **An identity or responsible person is changed**: `as you already know i am [[betty → betsy]]` (self-introduction)
- **The polarity of a proposition is reversed**: `i kinda doubt just that it would [[ever → never]] be done`, `there are a few but in general [[not → now]]`, `so it is just kind of does [[not → ∅]] really do anything`
- **An evaluation or decision is reversed or lost**: `so yeah that is less [[crude → great]]`

## 4. Adjustment rules

1. **Context recoverability.** If the shown context **explicitly** provides the correct information, re-judge severity by whether the reader can reliably recover the meaning. Do **not** apply a fixed one-level reduction: a fully recoverable error may drop from 5 to 2; a partly recoverable one drops less.
   - Example: `[[is it 12 point fif → at 125th]] was it 12.50`. The speaker repeats "12.50" right after, so the reader can most likely recover the price → 3.
   - If the transcript contains **conflicting** information (e.g. the context says 12 but the ASR wrote 20), do **not** assume the reader knows which one is correct; treat the error as unrecoverable.
2. **Negation means propositional polarity.** Use `negation` (and judge it as a polarity change) only when the error changes whether a statement is true or false. An interjection or backchannel "no" (`otherwise it goes oh [[no → ∅]]`) is a discourse marker: severity 1–2, `content_type = disfluency`.
3. **Garbled spans are scored by the most important content they destroy**, not by the number of words.
4. **Near-miss nonwords of entities or numbers.** If the reader can reliably recognize the intended entity or number (`teletext → teletex`, `pernilla → penila`), usually 2–3. If it becomes **a different real entity or value**, give 3–5 depending on how important that information is for understanding the meeting; give 5 only if it changes a core fact, decision, responsible person, or key quantity and the context cannot correct it.
5. **When torn between two adjacent scores, choose the lower one** and explain why in `note`.

## 5. Fields

| Field | Values |
|---|---|
| `severity` | integer 1–5. Always fill it, even for flagged items (give your best provisional score). |
| `content_type`: **what kind of content is affected** | `disfluency` (fillers, repetitions, stutters, discourse markers, backchannels) · `function_word` · `content_word` · `named_entity` · `number` (numbers, prices, times, dates) · `negation` (propositional polarity) · `other` |
| `error_form`: **what the error looks like** | `morph_variant` (another form of the same word) · `nonword` (not a real word) · `real_word` (a different real word, including homophones) · `garbled` (several words turned into nonsense) · `other`. **Leave empty for pure deletions and pure insertions.** For `mixed` spans, describe the substituted part. |
| `flag` (optional; several values separated by `;`) | `ref_issue`: the reference itself looks wrong or unreadable, and the ASR may be right, e.g. `[[on a val of → out of all]] 76`, `[[nlssd → this is the]]` · `crosstalk`: the ASR transcribed another speaker's voice · `uncertain`: severity cannot be judged reliably from the text (e.g. missing context, unclear referent) · `multi_issue`: the span merges several independent errors |
| `note` (optional) | free text: why you hesitated, which scores you were torn between |

### 5.1 Choosing one `content_type`

Choose **one** primary content type: the one that drives the severity score. If several content types contribute **equally**, take the first in this order:

**negation > number > named_entity > content_word > function_word > disfluency > other**

This order only makes the category label consistent; it does not affect severity. Example: `[[we cannot buy 12 → we can buy 20]] units` reverses polarity and changes a number; both drive a score of 5, so `content_type = negation`.

## 6. Procedure for human annotators

Annotate **independently**. Do not discuss items with the other annotator until both of you have finished. Fill only `severity`, `content_type`, `error_form`, `flag`, and (optionally) `note`; do not edit the other columns.
