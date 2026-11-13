# Representative cases

## High-severity single-word errors

- **whisper-large-v3** sev=5 [negation/real_word] `but yeah but but actually if you if you imagine [[not → the]] entire the completely same task given to us but us said ok`  
  _Replacing the negator 'not' with 'the' turns 'not entirely the same task' into an assertion that the task was the same, reversing the core proposition._
- **whisper-large-v3** sev=5 [negation/real_word] `it is [[about → not]] the best thing`  
  _Replacing "about" with "not" reverses the polarity of the assertion, turning a strong positive evaluation into a negative one._
- **whisper-large-v3** sev=5 [negation/nan] `there is no need to spend money on research and development but this does [[∅ → not]] mean the need for microphones in the`  
  _Inserting 'not' reverses the proposition from 'this does mean the need for microphones' to 'this does not mean the need for microphones', flipping the core assertion._
- **whisper-large-v3** sev=5 [negation/nan] `how can [[t → ∅]] product evaluation does not that come after actually seen`  
  _Deleting the clitic 't' changes 'can't' to 'can', reversing the negation of the proposition._
- **whisper-large-v3** sev=5 [negation/nan] `and the other question is if we do [[∅ → not]] include them are we really in a position to evaluate that market`  
  _Inserting 'not' reverses the conditional from 'if we do include them' to 'if we do not include them', flipping the core proposition._
- **whisper-large-v3** sev=5 [negation/nan] `actually you can [[t → ∅]] perhaps just just`  
  _The deleted "t" is the negating clitic of "can't", so removing it turns the negative "you can't" into the affirmative "you can", reversing the core proposition._

## Multi-word errors judged harmless

- **whisper-large-v3** sev=1 [disfluency/nan] `so if we have the 3 presentations and then if you have anything [[to kind of → ∅]] that you know you are going to want to discuss`  
  _The deleted span 'to kind of' is a filler/hedge that adds no substantive meaning, so removing it leaves the utterance's meaning unchanged._
- **whisper-large-v3** sev=1 [disfluency/nan] `[[what did → ∅]] how did we leave it with speech recognition now`  
  _The deleted "what did" is an abandoned false start that the speaker immediately repairs with "how did we leave it", so removing it does not change the meaning._
- **whisper-large-v3** sev=1 [disfluency/nan] `oh i should also point out that the [[you know the kind of → ∅]] final objective of this meeting is to reach a decision on the concepts of the product`  
  _The deleted span 'you know the kind of' is a filler/hedge that adds no substantive meaning, so the proposition is unchanged._
- **whisper-large-v3** sev=1 [disfluency/real_word] `and and then [[sorta g → sort of]] go through some of the way that i have dealt with that information`  
  _The reference 'sorta g' is a filler plus an abandoned false start of 'go'; the ASR's 'sort of' preserves the same (non-)meaning, so no semantic change occurs._
- **whisper-large-v3** sev=1 [disfluency/nan] `and then sort of bring us all together into it to see [[sorta see → ∅]] how this fits in with the overall vision`  
  _The deleted span 'sorta see' is a repeated, disfluent restatement of 'see' and adds no meaning, so removing it leaves the utterance unchanged._
- **whisper-large-v3** sev=1 [disfluency/morph_variant] `and then initiate a kind of discussion on design options so that it [[sorta → sort of]] helps us to to narrow in on on aspects that will inform other other elements of the of the project`  
  _The ASR renders the informal hedge 'sorta' as the equivalent 'sort of', leaving the meaning of the utterance completely unchanged._

## Utterances with the largest WER vs Semantic-WER gap

- **wav2vec2-large** WER=2.00 SemWER=0.00: `yeah you know → nded te sights pretty good one on` (1); `the → other you know` (1)
- **wav2vec2-large** WER=1.50 SemWER=0.00: `yeah → ha ha ha ha ha ha ha ha yes` (1)
- **whisper-large-v3** WER=2.40 SemWER=1.05: `∅ → you know that there are no errors` (4); `∅ → it is` (1); `∅ → yeah i see` (1)
- **whisper-large-v3** WER=0.29 SemWER=0.29: `you still → used to` (5)
- **whisper-large-v3** WER=0.17 SemWER=0.17: `about → not` (5)
- **whisper-large-v3** WER=0.05 SemWER=0.05: `∅ → not` (5)
