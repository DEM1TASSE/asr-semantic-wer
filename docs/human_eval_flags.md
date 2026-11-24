# Human evaluation: issues to fix before reporting (Nov 24)

Review sheet with every flagged item: `annotation/submissions/human_test_review.xlsx` (flagged rows highlighted;
columns `A relabel (fill)` and `adjudicated (fill)` are for the fixes).

## 1. Display bug: rater A saw the full ASR sentence on 57 of 100 items (must fix)
The eval site first showed the complete ASR output (`hyp`) instead of the single-error sentence
(`single_error_hyp`); fixed in commit 8ac3334. Rater A (`human_test_A_filled.xlsx`, commit 01cf55a) labeled
before the fix, rater B after it. On the 43 items with only one error in the utterance the two displays are
identical; on the other **57** rater A saw the target error together with other recognition errors.

| items | A vs B QWK | A vs B alpha | teacher vs A QWK | teacher vs B QWK |
|---|---|---|---|---|
| affected (57) | 0.71 | 0.70 | 0.71 | 0.83 |
| not affected (43) | 0.84 | 0.79 | 0.75 | 0.88 |

Agreement drops exactly on the affected items, as in the pilot, where showing the full hypothesis lowered
agreement. **Fix:** rater A relabels the 57 affected items on the fixed site (column `A relabel`), without
looking at the old labels or at B's. Keep the old labels as a record. Report agreement only after relabeling.

## 2. Items to discuss (|A - B| >= 2, or a level-5 label)
| # | system | error | A | B | teacher | note |
|---|---|---|---|---|---|---|
| 8 | Qwen 1.7B | is it [[12 point fif → 12.5]] | 3 | 1 | 1 | not display-affected; formatting of a number (student also over-scores it) |
| 43 | Parakeet | ...8 8 pm [[then he → and you]] can set the time | 1 | 3 | 2 | display-affected |
| 56 | Qwen 0.6B | got [[not → night]] right attributes | 5 | 3 | 4 | display-affected; negation lost: reversal (5) or meaning lost (4)? |
| 40 | Qwen 0.6B | [[i i we can not do it → it it becomes]] | 5 | 4 | 4 | "can not" deleted, not reversed: rubric says 4 |
| 96 | Parakeet | [[i i we can not do it → yeah]] | 5 | 4 | 4 | same question as #40 |

## 3. `ref_issue` flags by rater B (6 items: #3, 19, 24, 31, 75, 91)
The teacher flagged only #24. Several look like ordinary errors rather than wrong references (e.g. #19
`[[a → ∅]]`; #75 note asks what "start up" means). Decide per item; spans that stay `ref_issue` are excluded
from the agreement numbers (as in all other evaluations), so this changes n.

## 4. Pairwise sheets
Both raters answered all 60 items on the same items and order (checked against `outputs/pairwise_key.csv`).
Open question: commit 01cf55a added word-diff highlighting to the pairwise view in the same commit as rater
1's labels, so rater 1 may have labeled without highlighting and rater 2 with it. Confirm with rater 1.
The pairwise view intentionally shows full outputs, so the display bug above does not apply.
Raw agreement between raters: 62% (Same is the most common answer for both).
