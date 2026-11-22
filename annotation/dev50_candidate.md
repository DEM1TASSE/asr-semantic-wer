# Dev 50 candidate (pending team confirmation)

The upstream repository has no official 50-item ID list as of 2026-11-09. This is a proposed subset of the legacy 80, not a team-confirmed split. Keep legacy files and annotations. Both annotators should use identical IDs after agreeing on this manifest. The final 200-item test set is not selected here.

25 per ASR system; stratified by alignment operation (not severity or LLM error-form labels). Fixed seed 751; exact selection is recorded in dev50_candidate_manifest.json. All 50 retain the existing Chinese helper translations.

| Dev row | Legacy 80 row | Reference span | ASR span | error_id |
|---|---|---|---|---|
| 1 | 2 | our | her | `whisper-large-v3|AMI_TS3003d_H03_MTD012ME_0098258_0098523|0` |
| 2 | 3 | f | m | `wav2vec2-large|AMI_TS3003b_H01_MTD011UID_0056775_0057117|0` |
| 3 | 4 | ∅ | and | `wav2vec2-large|AMI_ES2004b_H02_MEE014_0024903_0025738|0` |
| 4 | 6 | i | ∅ | `whisper-large-v3|AMI_IS1009d_H03_FIO089_0141252_0141534|0` |
| 5 | 9 | generat to the | ∅ | `whisper-large-v3|AMI_IS1009d_H00_FIE088_0019852_0022001|3` |
| 6 | 10 | the | ∅ | `whisper-large-v3|AMI_TS3003c_H00_MTD009PM_0143794_0144768|0` |
| 7 | 11 | t | ∅ | `wav2vec2-large|AMI_IS1009b_H02_FIO084_0063941_0066293|1` |
| 8 | 13 | you | ∅ | `wav2vec2-large|AMI_EN2002d_H01_FEO072_0189484_0190231|1` |
| 9 | 15 | characteristic | ∅ | `whisper-large-v3|AMI_TS3003a_H00_MTD009PM_0070024_0070319|1` |
| 10 | 17 | it is | ∅ | `wav2vec2-large|AMI_TS3003a_H00_MTD009PM_0070024_0070319|0` |
| 11 | 18 | that | ∅ | `whisper-large-v3|AMI_ES2004a_H03_FEE016_0089871_0090564|0` |
| 12 | 19 | cover | cofer | `wav2vec2-large|AMI_TS3003b_H00_MTD009PM_0196452_0197489|1` |
| 13 | 22 | triple a | tripola | `wav2vec2-large|AMI_ES2004c_H02_MEE014_0048454_0049370|1` |
| 14 | 23 | teletext | telly text | `wav2vec2-large|AMI_ES2004c_H01_FEE013_0012602_0013372|2` |
| 15 | 24 | ok | omy | `wav2vec2-large|AMI_IS1009a_H00_FIE088_0060567_0060957|0` |
| 16 | 25 | would definitely be | definitelyb | `wav2vec2-large|AMI_TS3003b_H03_MTD012ME_0146664_0146971|0` |
| 17 | 26 | y | ∅ | `wav2vec2-large|AMI_IS1009b_H02_FIO084_0177728_0179020|0` |
| 18 | 27 | i | you | `whisper-large-v3|AMI_IS1009b_H01_FIO087_0121036_0121146|0` |
| 19 | 29 | yeah | and | `whisper-large-v3|AMI_TS3003b_H01_MTD011UID_0086683_0086961|1` |
| 20 | 30 | th | ∅ | `whisper-large-v3|AMI_ES2004b_H02_MEE014_0024903_0025738|0` |
| 21 | 32 | trend | trand | `wav2vec2-large|AMI_TS3003c_H03_MTD012ME_0022728_0023525|0` |
| 22 | 35 | c it might you might | ∅ | `whisper-large-v3|AMI_ES2004d_H02_MEE014_0140518_0141065|0` |
| 23 | 36 | instru | ∅ | `whisper-large-v3|AMI_ES2004b_H02_MEE014_0181639_0182014|0` |
| 24 | 38 | ah | ∅ | `whisper-large-v3|AMI_IS1009d_H03_FIO089_0085663_0086259|0` |
| 25 | 40 | satellite | satellites | `wav2vec2-large|AMI_IS1009c_H01_FIO087_0058505_0059282|1` |
| 26 | 42 | what | or | `wav2vec2-large|AMI_ES2004a_H01_FEE013_0081235_0081365|0` |
| 27 | 43 | that | ∅ | `whisper-large-v3|AMI_TS3003a_H00_MTD009PM_0132568_0133401|0` |
| 28 | 44 | the | ∅ | `whisper-large-v3|AMI_ES2004b_H01_FEE013_0146158_0146540|0` |
| 29 | 45 | tv | t b | `wav2vec2-large|AMI_ES2004b_H01_FEE013_0160942_0161612|1` |
| 30 | 47 | a | ∅ | `whisper-large-v3|AMI_IS1009d_H03_FIO089_0147227_0147341|0` |
| 31 | 48 | satellite | satellites | `whisper-large-v3|AMI_IS1009c_H01_FIO087_0058505_0059282|0` |
| 32 | 51 | watch trend | ∅ | `whisper-large-v3|AMI_TS3003c_H03_MTD012ME_0022728_0023525|0` |
| 33 | 52 | yeah | here | `wav2vec2-large|AMI_TS3003d_H00_MTD009PM_0252939_0253373|0` |
| 34 | 55 | ∅ | we | `whisper-large-v3|AMI_ES2004b_H00_MEO015_0066741_0067462|1` |
| 35 | 56 | this | punchin these | `wav2vec2-large|AMI_ES2004b_H00_MEO015_0066741_0067462|2` |
| 36 | 57 | multi function | multifunction | `wav2vec2-large|AMI_ES2004b_H03_FEE016_0117240_0117928|2` |
| 37 | 62 | just i will | ∅ | `whisper-large-v3|AMI_ES2004a_H03_FEE016_0045400_0045694|0` |
| 38 | 63 | our d | r are the | `wav2vec2-large|AMI_TS3003c_H02_MTD0010ID_0154060_0154699|0` |
| 39 | 64 | that | it | `wav2vec2-large|AMI_ES2004d_H03_FEE016_0137735_0138224|3` |
| 40 | 65 | the yeah the | ∅ | `whisper-large-v3|AMI_IS1009c_H01_FIO087_0052189_0052811|1` |
| 41 | 66 | user interface designer is | us int face designers | `wav2vec2-large|AMI_TS3003a_H00_MTD009PM_0030124_0031102|0` |
| 42 | 67 | good | get | `wav2vec2-large|AMI_EN2002c_H02_MEE071_0204803_0204956|1` |
| 43 | 69 | and | an | `wav2vec2-large|AMI_TS3003b_H00_MTD009PM_0109601_0110069|0` |
| 44 | 70 | to to | ∅ | `whisper-large-v3|AMI_IS1009d_H00_FIE088_0019852_0022001|4` |
| 45 | 71 | yep | yeah | `whisper-large-v3|AMI_IS1009d_H03_FIO089_0080981_0081579|0` |
| 46 | 72 | b | ∅ | `whisper-large-v3|AMI_IS1009c_H02_FIO084_0125076_0126004|0` |
| 47 | 73 | shock proof | shockproof | `whisper-large-v3|AMI_ES2004b_H00_MEO015_0069351_0070654|3` |
| 48 | 75 | de | ∅ | `whisper-large-v3|AMI_IS1009a_H02_FIO084_0070461_0070773|0` |
| 49 | 76 | trendy | any | `wav2vec2-large|AMI_IS1009c_H00_FIE088_0165479_0165739|0` |
| 50 | 79 | mo morse code | mormorscot | `wav2vec2-large|AMI_IS1009c_H02_FIO084_0106914_0107871|0` |
