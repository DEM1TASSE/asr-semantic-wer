# Annotation Guideline: Semantic Impact of ASR Errors

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

## 2. What you score

You give **two separate scores**:

| Score | Question | Scale |
|---|---|---|
| **Distortion (D)** | How much does this error change or remove the meaning of what the speaker said? | 1–5 |
| **Importance (I)** | How important is the original information affected by this error, in this conversation? | 1–3 (leave empty when D = 1) |

Score the two **independently**: D does not depend on whether the content matters for the meeting, and I does not depend on how badly the content was damaged.

**Unit: one error alone.** Judge the target error **alone**: assume every other recognition error in the same sentence has been corrected.

**Do not score readability.** How fluent or readable the ASR output is, and how easily a reader would notice the error, do not affect either score.

## 3. Distortion (D, 1–5)

**How much of the meaning of the speaker's utterance is changed or lost?**

- Judge the **meaning**, not how different the words look. A synonym that preserves the meaning is no distortion (*a [[big → large]] screen*); a one-word change can reverse a statement (*the budget was [[approved → rejected]]*).
- Both **information loss** (content deleted or turned into nonsense) and **misinformation** (content replaced by different content) count. *We should [[cancel → ∅]] the launch* loses the action; *we should [[cancel → continue]] the launch* reverses it.
- If the intended word is still identifiable **from the erroneous word itself** (a near-miss spelling such as `[[concepts → consepts]]`), little meaning is lost.
- **Use the context to understand what the speaker meant, but not to excuse the error.** Do not lower D because the correct information is repeated or could be reconstructed elsewhere in the conversation.
- **Do not consider importance here.** Changing a number gets the same D whether it is the budget or a number mentioned in passing.

| D | Level | Definition | Examples |
|---|---|---|---|
| **1** | none | The meaning is identical. | repetitions and false starts `i [[am i → ∅]] was a bit worried`, `the [[the the → ∅]] week`, `dogs can [[som → ∅]] sometimes`; fillers and backchannels `[[yeah → ∅]] i have got one at home`, `75 [[i mean → ∅]]`; insertions adding no meaning `[[∅ → ha ha ha]]`, `[[∅ → like]]`; synonyms `a [[big → large]] screen` |
| **2** | slight | The meaning is essentially preserved; only a nuance changes, or a misspelled word is still identifiable. | near-miss nonwords `[[concepts → consepts]]`, `[[probably → probly]]`, `in [[euros → uros]]`; inflection `all [[animals → animal]] shapes`, `different [[kind → kinds]]`; articles and prepositions `with [[the → a]] touch screen`; tense that does not change the point `we [[are → were]] doing the kinetic thing`; degree words `it would be [[very → ∅]] expensive`; low-content words garbled while the content words survive `[[okay that is → g let us he]] good timing` |
| **3** | partial | A secondary part of the statement is changed or lost, but the main statement survives. | changed pronoun referent `write down a few of [[its → his]] characteristics`; a small addition that does not change the main point `no [[∅ → well maybe there is]]` |
| **4** | major | A main part of the statement (main action, key argument, value, identity) is replaced or lost; or the whole statement is garbled; or content the speaker never said is added. | `so if you want to have less [[buttons → pitence]]`, `for the [[whole → horror]] of the language`, `[[pen → ben]] is here on the table`, `[[yeah i → you have]] forgot that actually`, `it is split over [[22 → 2]] different layers`, `as you already know i am [[betty → betsy]]`, `[[is it 12 point fif → at 125th]] was it 12.50`, `then that [[is going to be kind of fun → cannow becanaphone]]`, `so basically [[∅ → a person will]] not point or click` |
| **5** | reversed | The statement now says the opposite of, or contradicts, the original. | polarity `i kinda doubt just that it would [[ever → never]] be done`, `there are a few but in general [[not → now]]`, `so it is just kind of does [[not → ∅]] really do anything`; reversed evaluation or decision `so yeah that is less [[crude → great]]`, `we should [[cancel → continue]] the launch` |

## 4. Importance (I, 1–3)

**How important is the original information that this error affects, in this conversation?**

- Rate the **original content** that was changed or lost (the left side of the arrow, in its sentence), not the error and not the whole sentence.
- Use the context to decide what the conversation is about and what role this content plays.
- Content type does not decide importance: a number mentioned in passing can be 1; a pronoun saying who is responsible can be 3.
- **Leave I empty when D = 1.**

| I | Level | Definition | Examples |
|---|---|---|---|
| **1** | background | Social talk, discourse filler, side remarks, or detail with no role in the discussion. | `okay that is good timing` (reply to "five minutes okay"); `yeah pen is here on the table`; `then that is going to be kind of fun` |
| **2** | supporting | Details, reasons, examples, or descriptions that support the discussion but are not themselves the core fact or outcome. | `write down a few of its characteristics`; `for the whole of the language`; `it would be very expensive` |
| **3** | core | A core fact, decision, action, responsible person, key quantity, or the speaker's stance on the topic under discussion. | a design parameter `it is split over 22 different layers`; a price under discussion `is it 12 point fif`; self-introduction `i am betty`; a stance on feasibility `i kinda doubt just that it would ever be done`; a decision `we should cancel the launch` |

## 5. Additional rules

1. **Negation means propositional polarity.** Treat an error as a polarity reversal (D = 5) only when it changes whether a statement is true or false. An interjection or backchannel "no" (`otherwise it goes oh [[no → ∅]]`) is a discourse marker: D = 1–2.
2. **Garbled spans:** D reflects how much meaning the garbled span destroys, and I reflects the most important content it destroys. Do not count words.
3. **When torn between two adjacent scores, choose the lower one** and explain why in `note`.

## 6. Fields

| Field | Who fills it | Values |
|---|---|---|
| `distortion` | human and LLM | integer 1–5; always fill it, even for flagged items |
| `importance` | human and LLM | integer 1–3; leave empty when `distortion` = 1 |
| `flag` | human and LLM (optional; several values separated by `;`) | `ref_issue`: the reference itself looks wrong or unreadable, and the ASR may be right, e.g. `[[on a val of → out of all]] 76`, `[[nlssd → this is the]]` · `crosstalk`: the ASR transcribed another speaker's voice · `uncertain`: a score cannot be judged reliably from the text (e.g. the meaning or role of the utterance is unclear) · `multi_issue`: the span merges several independent errors |
| `note` | human and LLM (optional for humans) | free text: why you hesitated, which scores you were torn between |
| `content_type` | **LLM only** | the kind of content affected: `disfluency` (fillers, repetitions, stutters, discourse markers, backchannels) · `function_word` (articles, prepositions, pronouns, auxiliaries, conjunctions) · `content_word` (nouns, verbs, adjectives, adverbs with lexical meaning) · `named_entity` · `number` (numbers, prices, times, dates) · `negation` (propositional polarity) · `other`. Choose the type that drives the distortion; if several contribute equally, take the first in the order negation > number > named_entity > content_word > function_word > disfluency > other. |
| `error_form` | **LLM only** | `morph_variant` (another form of the same word) · `nonword` (not a real word) · `real_word` (a different real word, including homophones) · `garbled` (several words turned into nonsense) · `other`; empty for pure deletions and pure insertions; for `mixed` spans, describe the substituted part |

## 7. Procedure for human annotators

Annotate **independently**. Do not discuss items with the other annotator until both of you have finished. Fill only `distortion`, `importance`, `flag`, and (optionally) `note`; do not edit the other columns.
