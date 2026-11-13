# Pilot 讨论：A、B 相差 ≥ 2 分的条目

50 条中原有 3 条相差 2 分及以上。其余分歧都是 1 分，可以接受，不逐条统一。

讨论后的结果另存，不改 `human_pilot_A/B.xlsx`。唯一例外是 #1：A 确认原分数是**录入错误**（本意是 5），
已在 `human_pilot_A.xlsx` 里改成 5，并在 note 中注明；原始导出保留在 `annotation/raw/human_pilot_A_original.csv`。

## 结论（2026-11-12）

| # | 统一标签 | content_type | flag | 说明 |
|---|---|---|---|---|
| 1 | **5** | content_word | | A 录入错误，已更正为 5；与 B 一致。改口后的 "I think it is true" 被 ASR 换成 "nothing is true"，与原肯定判断冲突 |
| 6 | 保留 A=1、B=3；需要单一标签时用均值 **2** | content_word | uncertain | 能否把 scrawl 读成 scroll 因人而异，属于合理的主观差异，不强行统一，也不为此改 rubric |
| 31 | **4** | other | crosstalk | 插入的话来自下一位说话人（FIE088），让当前说话人看起来提出了另一种可能，改变了立场和说话人归属；原否定仍在，未反转，所以不是 5 |

本轮 adjudication 到此结束，相差 1 分的条目不再逐条统一。

---

## #1 自我修正：丢掉了改口后的内容（wav2vec2）

**上下文**
```
FEO070: like just like yeah
FEO072: i don't think it's gonna take long to to produce anyway
FEO070: no
[TARGET] no no i do not think that is i think it is true
FEO072: it's just another um i mean these meetings are not endlessly long ...
```

| | |
|---|---|
| 错误 | `no no i do not think that is [[i think it → nothing]] is true` |
| 参考句 | no no i do not think that is **i think it** is true |
| 只含这个错误的 ASR 句 | no no i do not think that is **nothing** is true |
| A | **1**, disfluency |
| B | **5**, content_word |
| DeepSeek / gpt-4o | 4 / 4, content_word |

**要讨论的：** 说话人先说 "i do not think that is"，没说完就改口成 "i think it is true"。
- 如果 "i think it" 是**改口后的内容**，它是说话人真正的意思，丢掉就不能给 1。
- ASR 句子读起来是 "I don't think that… nothing is true"：主要命题是丢了（4），还是反了（5）？

**决定：** severity 5, content_type content_word（A 录入错误，已更正）

---

## #6 识别成了另一个真实的词：scroll → scrawl（wav2vec2）

**上下文**
```
MTD009PM: okay but then you you can push uh some other button as well
MTD012ME: but yeah
[TARGET] you could just not scroll for a half a 2nd
MTD009PM: yeah
```

| | |
|---|---|
| 错误 | `you could just not [[scroll → scrawl]] for a half a 2nd` |
| 参考句 | you could just not **scroll** for a half a 2nd |
| 只含这个错误的 ASR 句 | you could just not **scrawl** for a half a 2nd |
| A | **1**, content_word |
| B | **3**, content_word |
| DeepSeek / gpt-4o | 3 / 3, content_word |

**要讨论的：** 拼写错误按干扰理解的程度给 1–3。
- 在讨论遥控器按键的上下文里，读者会不会自然读成 scroll？会的话给 1。
- 还是 scrawl（乱涂乱写）把动作变成了别的意思？那样是 2–3。

**决定：** 保留 A=1、B=3；统一标签 2 + `uncertain`

---

## #31 串音：插入了另一个人说的话（Whisper）

**上下文**
```
FIO089: and in that case we could probabl moulded plastic isn't all that expensive is it
FIO089: um you as an industrial person
FIO084: uh no
[TARGET] i i i do not think no
FIE088: well maybe there's there's an idea you know t the new for example new portable phones
```

| | |
|---|---|
| 错误 | `i i i do not think no [[∅ → well maybe there is]]` |
| 参考句 | i i i do not think no |
| 只含这个错误的 ASR 句 | i i i do not think no **well maybe there is** |
| A | **4**, other |
| B | **2**, content_word |
| DeepSeek / gpt-4o | 4 / 4（content_word / other） |
| flag | 两人都没标 |

**要讨论的：** 下一句是 FIE088 说的 "well maybe there's…"，基本可以确定是串音，应该标 `crosstalk`。
- 打分只看多出来的话给**这句话**增加了什么意思，不管是谁说的。
- "I don't think so, no" 后面加上 "well maybe there is"：是削弱了原来的否定（3），还是把原意改了大半（4）？

**决定：** severity 4, content_type other, flag crosstalk
