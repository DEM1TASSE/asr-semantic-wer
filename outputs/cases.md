# Representative cases

## High-severity single-word errors

- **whisper-large-v3** sev=5 [negation/real_word] `i kind of doubt just that it would [[ever → never]] be done`  
  _Changing 'ever' to 'never' reverses the proposition: 'I doubt it would ever be done' (it won't happen) becomes 'I doubt it would never be done' (it will happen)._
- **whisper-large-v3** sev=5 [content_word/real_word] `so yeah that is less [[crude → great]] is not it`  
  _The evaluative adjective is replaced by its opposite polarity: 'less crude' (a positive, more-refined assessment) becomes 'less great' (a negative assessment), reversing the direction of the speaker's core judgment._
- **wav2vec2-large** sev=5 [negation/real_word] `i kind of doubt just that it would [[ever → never]] be done`  
  _Changing 'ever' to 'never' reverses the proposition: doubting it would ever be done becomes doubting it would never be done, i.e., implying it will be done._
- **wav2vec2-large** sev=5 [negation/nan] `so it is just kind of does [[not → ∅]] really do anything`  
  _Deleting 'not' turns the negative assertion 'does not really do anything' into the affirmative 'does really do anything', reversing the core proposition._

## Multi-word errors judged harmless

- **whisper-large-v3** sev=1 [disfluency/nan] `yeah because otherwise it will [[the it will → ∅]] increase the amount of data we need by a lot will not it`  
  _The deleted span 'the it will' is an abandoned false start/repetition that adds no meaning, so removing it leaves the proposition unchanged._
- **whisper-large-v3** sev=1 [disfluency/nan] `i [[am i → ∅]] was a bit worried about when well when he talked about this with the file messing around with files`  
  _The deleted span 'am i' is an abandoned false start that the speaker immediately repairs to 'i was', so removing it leaves the meaning unchanged._
- **whisper-large-v3** sev=1 [disfluency/nan] `i am i was a bit worried about [[when well → ∅]] when he talked about this with the file messing around with files`  
  _The deleted span 'when well' is an abandoned false start immediately restarted as 'when he talked about this', so removing it leaves the meaning unchanged._
- **whisper-large-v3** sev=1 [disfluency/nan] `the [[the the → ∅]] week as it as is rather than the proper week do you know what i mean`  
  _The deleted span is a repeated article, a disfluency that adds no meaning, so the utterance's meaning is unchanged._
- **whisper-large-v3** sev=1 [disfluency/nan] `the the the week [[as it → ∅]] as is rather than the proper week do you know what i mean`  
  _The deleted "as it" is an abandoned false start that the speaker immediately repairs with "as is", so removing it leaves the meaning unchanged._
- **whisper-large-v3** sev=1 [disfluency/nan] `yeah that is [[it is → ∅]] quite impressive actually`  
  _The deleted "it is" is a repeated/abandoned false start; removing it leaves the meaning "that is quite impressive" unchanged._

## Utterances with the largest WER vs Semantic-WER gap

- **whisper-large-v3** WER=0.88 SemWER=0.00: `you ha you have t yeah y → ∅` (1)
- **wav2vec2-large** WER=1.33 SemWER=0.54: `so basically → sophysically a person di` (3); `point → pint` (3); `∅ → ot the ears` (2)
- **wav2vec2-large** WER=0.78 SemWER=0.00: `yeah → a` (1); `yeah → m` (1); `it is a yeah yeah → a sit e he` (1)
- **whisper-large-v3** WER=0.11 SemWER=0.11: `crude → great` (5)
- **wav2vec2-large** WER=0.07 SemWER=0.05: `notes → not` (4)
- **whisper-large-v3** WER=0.04 SemWER=0.02: `elderly → other` (3)
