# Representative cases

## High-severity single-word errors

- **whisper-large-v3** sev=5 [negation/real_word] `excuse me am [[i → not]] allowed to say that`  
  _Replacing the question word 'i' with 'not' turns the speaker's request for permission ('am I allowed to say that?') into the opposite assertion that they are not allowed, reversing the core proposition._
- **whisper-large-v3** sev=5 [content_word/real_word] `[[keep → give]] this office for reception people`  
  _The verb changes from retaining the office ('keep') to handing it over ('give'), reversing the direction of the core proposition._
- **wav2vec2-large** sev=5 [content_word/real_word] `but it is it is a movie quite [[surrealistic → realistic]] i mean there are some part that are like coming from dreams and`  
  _Substituting the antonym 'realistic' for 'surrealistic' reverses the core description of the movie, contradicting the following clause about dream-like parts._
- **wav2vec2-large** sev=5 [negation/nan] `yeah but you can not choo you can [[not → ∅]] choose it when you buy it`  
  _Deleting the second 'not' turns the assertion 'you can not choose it when you buy it' into 'you can choose it', reversing the core proposition._
- **parakeet-tdt-0.6b-v2** sev=5 [negation/real_word] `it is weird because it kind of is [[and → not]] kind of is not`  
  _Substituting "and" with "not" flips the first clause from affirmative ("kind of is") to negative ("kind of is not"), reversing the polarity of the core proposition._
- **parakeet-tdt-0.6b-v2** sev=5 [negation/real_word] `suggestion if possible we could move me and yalina to the office where andrei and nancy are [[now → not]]`  
  _Replacing "now" with "not" negates the location clause, reversing the proposition from the office where Andrei and Nancy currently are to one where they are not._

## Multi-word errors judged harmless

- **whisper-large-v3** sev=1 [content_word/morph_variant] `so we are going to try out our [[white board → whiteboard]]`  
  _Merging 'white board' into 'whiteboard' is only a spelling/compound-form difference; the meaning is unchanged._
- **whisper-large-v3** sev=1 [disfluency/nan] `sorry can you just say [[that what is the → ∅]] what are our price goals again`  
  _The deleted span 'that what is the' is an abandoned false start that the speaker immediately repairs into 'what are our price goals again', so removing it leaves the meaning unchanged._
- **whisper-large-v3** sev=1 [content_word/morph_variant] `i do not know what these mean because i did not actually make the [[slide show → slideshow]]`  
  _The compound is written as one word instead of two, but the meaning ('slide show') is completely unchanged._
- **whisper-large-v3** sev=1 [disfluency/nan] `i do not know [[but someth → ∅]] because it is usually under the sofa`  
  _The deleted span 'but someth' is an abandoned false start with a truncated word, adding no substantive meaning, so removing it leaves the utterance's meaning unchanged._
- **whisper-large-v3** sev=1 [disfluency/nan] `or like [[or like → ∅]] a light thing`  
  _The deleted 'or like' is a repeated filler phrase; removing the repetition leaves the meaning unchanged._
- **whisper-large-v3** sev=1 [disfluency/nan] `because i do not know if it is [[i think it is e → ∅]] expensive if you have if you use the telly screen because the telly is already a screen`  
  _The deleted span is an abandoned false start ('i think it is e') that the speaker immediately repairs into 'expensive', so removing it leaves the meaning unchanged._

## Utterances with the largest WER vs Semantic-WER gap

- **whisper-large-v3** WER=2.20 SemWER=1.10: `∅ → we have got some time we have got some time now` (3)
- **wav2vec2-large** WER=1.17 SemWER=0.17: `ah that is → thas` (1); `∅ → wher dos the to` (2)
- **parakeet-tdt-0.6b-v2** WER=1.00 SemWER=0.11: `no → i know` (2); `∅ → the` (1); `b → ba it is` (1); `surname → name` (2)
- **whisper-large-v3** WER=0.17 SemWER=0.17: `keep → give` (5)
- **whisper-large-v3** WER=0.83 SemWER=0.83: `or how how → no no no there is no terrace in that building` (5)
- **wav2vec2-large** WER=1.00 SemWER=1.00: `it is quite horrible actually → its great oribishing` (5)
