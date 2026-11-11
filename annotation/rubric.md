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

**How much does this ASR error change or remove the meaning of what the speaker said, weighted by how important the affected information is in this conversation?**

### 2.1 Unit: the impact of a single error

Judge the target error **alone**: assume every other recognition error in the same sentence has been corrected. Do not consider the joint impact of several errors in one sentence; that is studied separately.

### 2.2 Two factors decide severity

1. **Semantic distortion.** How much of the meaning of the original words is changed or lost in the ASR output?
   - Judge the **meaning**, not how different the words look. A synonym that preserves the meaning is no distortion (*a [[big → large]] screen*); a one-word change can reverse a statement (*the budget was [[approved → rejected]]*).
   - If the intended word is still identifiable **from the erroneous word itself** (a near-miss spelling such as `[[concepts → consepts]]`), little meaning is lost.
2. **Importance of the affected information in this conversation.** Does it carry a core fact, a decision, an action, who is responsible, a key quantity, or the speaker's stance? Or is it background detail or social filler?

Both **information loss** (content deleted or turned into nonsense) and **misinformation** (content replaced by different, possibly fluent, content) count. Score how much important meaning is changed or lost, **not** how easily a reader would notice the error. For example, *we should [[cancel → ∅]] the launch* and *we should [[cancel → continue]] the launch* can both deserve 4–5.

### 2.3 How to use the context

**Context determines importance, but does not erase an error.**
- **Use** the context (including the following utterance) to understand what the speaker meant and how important the affected information is.
- **Do not** lower the severity because the correct information is repeated, confirmed, or could be reconstructed elsewhere in the conversation. Example: if the budget is said again correctly in the next utterance, changing it in this utterance is still a severe error.

### 2.4 Content type does not determine severity

Numbers, names, and negation are **high-risk content types**: errors in them are often severe, but they are **never automatically 5**. Every content type is scored by the two factors above. For example, `as you already know i am [[betty → betsy]]` changes the speaker's self-introduction → 5, while a wrong name for a person mentioned in passing, who plays no role in the discussion, may be only 3. Likewise, `it is split over [[22 → 2]] different layers` changes a design parameter under discussion → 5, while a wrong number mentioned in passing that affects no conclusion may be 3.

## 3. Severity scale (1–5)

The examples below show typical cases. The principles in Section 2 take precedence: the same surface pattern can deserve a different score in a different context.

### 1 = No change in meaning
- **Repetitions, stutter fragments, abandoned false starts**, even when several words long: `i [[am i → ∅]] was a bit worried`, `the [[the the → ∅]] week`, `dogs can [[som → ∅]] sometimes`, `[[the sort of → ∅]] i had a quick look`
- **Fillers, discourse markers, backchannels**: `[[yeah → ∅]] i have got one at home`, `75 [[i mean → ∅]]`, `a 5 actually [[cause → ∅]]` (unfinished trailing word)
- **Insertions that add no meaning**: laughter `[[∅ → ha ha ha]]`, a single function word `[[∅ → the]]`, `[[∅ → like]]`
- **Synonyms or paraphrases with identical meaning**; **spelling or formatting variants**

### 2 = Minor distortion: the meaning is largely preserved, with only a small loss or alteration
- **Near-miss nonwords whose intended word is identifiable from the word itself**: `[[concepts → consepts]]`, `[[probably → probly]]`, `[[thing → ting]]`, `in [[euros → uros]]`, `[[sony → soni]]`
- **Inflection changes**: `all [[animals → animal]] shapes`, `double [[curved → curves]]`, `different [[kind → kinds]]`
- **Article or preposition swaps; tense changes that do not alter the point**: `with [[the → a]] touch screen`, `we [[are → were]] doing the kinetic thing`
- **Word merges or splits**: `[[i was → iwas]]`

### 3 = Moderate: part of the meaning is changed or lost, but the affected information is of limited importance
- **Low-information phrases lost or turned into nonsense**: `[[okay that is → g let us he]] good timing`
- **Lost modifiers or degree words**: `it would be [[very → ∅]] expensive`
- **Pronoun changes affecting a peripheral referent**: `and i have got to write down a few of [[its → his]] characteristics`
- **Insertions that add a little content without changing the main point** (often crosstalk): `no [[∅ → well maybe there is]]`
- **High-risk content type, but the content is unimportant in this conversation**, e.g. a minor name or a number mentioned in passing replaced by another one

### 4 = Serious: important information is changed or lost
- **A content word that matters to the discussion is replaced or lost**: `so if you want to have less [[buttons → pitence]]`, `for the [[whole → horror]] of the language`, `take some [[notes → not]]`, `[[pen → ben]] is here on the table` (an object becomes a person)
- **Changed referent (who did it / who is addressed)**: `[[yeah i → you have]] forgot that actually`, `so [[you → he]] would not be pressing`
- **The core proposition of the sentence is lost or garbled**: `then that [[is going to be kind of fun → cannow becanaphone]]`; `[[i kinda doubt just that → commondor she said]] it would ever be done` (the speaker's stance is lost and a false "she said" is added)
- **Hallucinated insertions that add content the speaker never said**: `so basically [[∅ → a person will]] not point or click`

### 5 = Critical: a **core fact, decision, action, responsible person, or key quantity** is changed or lost
- **A value under discussion is changed or lost**: `it is split over [[22 → 2]] different layers` (a design parameter under discussion), `we can like think of [[56 → physics]] designs`, `[[is it 12 point fif → at 125th]] was it 12.50` (the price under discussion)
- **An identity or responsible person is changed**: `as you already know i am [[betty → betsy]]` (self-introduction)
- **The polarity of a proposition is reversed**: `i kinda doubt just that it would [[ever → never]] be done`, `there are a few but in general [[not → now]]`, `so it is just kind of does [[not → ∅]] really do anything`
- **An evaluation or decision is reversed or lost**: `so yeah that is less [[crude → great]]`

## 4. Additional rules

1. **Negation means propositional polarity.** Use `negation` (and judge it as a polarity change) only when the error changes whether a statement is true or false. An interjection or backchannel "no" (`otherwise it goes oh [[no → ∅]]`) is a discourse marker: severity 1–2, `content_type = disfluency`.
2. **Garbled spans are scored by the most important content they destroy**, not by the number of words.
3. **Near-miss nonwords of entities or numbers.** If the intended entity or number is identifiable from the erroneous word itself (`teletext → teletex`, `pernilla → penila`), usually 2. If it becomes **a different real entity or value**, give 3–5 depending on how important that information is in the conversation.
4. **When torn between two adjacent scores, choose the lower one** and explain why in `note`.

## 5. Fields

| Field | Values |
|---|---|
| `severity` | integer 1–5. Always fill it, even for flagged items (give your best provisional score). |
| `content_type`: **what kind of content is affected** | `disfluency` (fillers, repetitions, stutters, discourse markers, backchannels) · `function_word` · `content_word` · `named_entity` · `number` (numbers, prices, times, dates) · `negation` (propositional polarity) · `other` |
| `error_form`: **what the error looks like** | `morph_variant` (another form of the same word) · `nonword` (not a real word) · `real_word` (a different real word, including homophones) · `garbled` (several words turned into nonsense) · `other`. **Leave empty for pure deletions and pure insertions.** For `mixed` spans, describe the substituted part. |
| `flag` (optional; several values separated by `;`) | `ref_issue`: the reference itself looks wrong or unreadable, and the ASR may be right, e.g. `[[on a val of → out of all]] 76`, `[[nlssd → this is the]]` · `crosstalk`: the ASR transcribed another speaker's voice · `uncertain`: severity cannot be judged reliably from the text (e.g. the meaning or importance of the utterance is unclear) · `multi_issue`: the span merges several independent errors |
| `note` (optional) | free text: why you hesitated, which scores you were torn between |

### 5.1 Choosing one `content_type`

Choose **one** primary content type: the one that drives the severity score. If several content types contribute **equally**, take the first in this order:

**negation > number > named_entity > content_word > function_word > disfluency > other**

This order only makes the category label consistent; it does not affect severity. Example: `[[we cannot buy 12 → we can buy 20]] units` reverses polarity and changes a number; both drive a score of 5, so `content_type = negation`.

## 6. Procedure for human annotators

Annotate **independently**. Do not discuss items with the other annotator until both of you have finished. Fill only `severity`, `content_type`, `error_form`, `flag`, and (optionally) `note`; do not edit the other columns.
