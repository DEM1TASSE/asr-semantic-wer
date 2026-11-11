# 标注规则：ASR 错误的语义影响

## 1. 标注对象

每一条是**一个错误 span**：ASR 输出与参考转写不一致的一段连续区域（相邻的替换、删除、插入已合并为一个 span）。

每条你会看到：
- 会议上下文：前 3 句、后 1 句，带说话人编号，取自**参考转写**；
- 参考句，错误处标成 `[[原文 → ASR]]`；
- 这句话完整的 ASR 输出；
- `edit_operation`（substitution / deletion / insertion / mixed）：由对齐自动生成，**不需要标**。

### 1.1 记号说明

错误统一写成 **`[[原文 → ASR]]`**：
- **箭头左边是原文**，即说话人实际说的内容（人工转写）；
- **箭头右边是 ASR 的输出**；
- **`∅` 表示这一边什么都没有。**

| 写法 | 含义 | 例子 | 解释 |
|---|---|---|---|
| `[[A → ∅]]` | 删除 | `the [[the the → ∅]] week` | 说话人说了 "the the the week"，ASR 只输出了 "the week" |
| `[[∅ → B]]` | 插入 | `flying animal [[∅ → ha ha ha]]` | 说话人没说 "ha ha ha"，ASR 多输出了这几个词 |
| `[[A → B]]` | 替换 | `[[pen → ben]] is here` | 说话人说的是 "pen"，ASR 输出了 "ben" |

`[[ ]]` 外面的词都识别正确。

## 2. 要打哪些分

每条打**两个独立的分数**：

| 分数 | 问题 | 范围 |
|---|---|---|
| **失真度（D）** | 这个错误让说话人原话的意思改变或丢失了多少？ | 1–5 |
| **重要性（I）** | 被这个错误影响的原始信息，在这段对话里有多重要？ | 1–3（D = 1 时留空） |

两个分数**各自独立判断**：D 不管这部分内容对会议重不重要；I 不管这部分内容被破坏得有多厉害。

**评分单位：只评这一个错误。** 假设同一句里的其他识别错误都已经纠正。

**不评可读性。** ASR 输出是否通顺好读、读者容不容易发现这个错误，都不影响这两个分数。

## 3. 失真度（D，1–5）

**说话人原话的意思被改变或丢失了多少？**

- 看**意思**，不看字面差了多少。意思不变的同义词不算失真（*a [[big → large]] screen*）；只改一个词也可能把意思完全反过来（*the budget was [[approved → rejected]]*）。
- **信息丢失**（内容被删掉或变成乱码）和**错误信息**（内容被换成了别的内容）都算失真。*We should [[cancel → ∅]] the launch* 丢掉了行动；*we should [[cancel → continue]] the launch* 把行动反过来了。
- 如果**从错误的词本身**就能认出原词（比如拼写相近的 `[[concepts → consepts]]`），丢失的意思就很少。
- **上下文可以用来理解说话人想说什么，但不能用来抵消错误。** 不要因为正确的信息在对话别处重复出现或者能推断出来，就降低 D。
- **这里不考虑重要性。** 同样是把一个数字识别错，不管是预算还是顺带提到的数字，D 都一样。

| D | 等级 | 定义 | 例子 |
|---|---|---|---|
| **1** | 无 | 意思完全相同。 | 重复和说了一半的话 `i [[am i → ∅]] was a bit worried`、`the [[the the → ∅]] week`、`dogs can [[som → ∅]] sometimes`；语气词和附和词 `[[yeah → ∅]] i have got one at home`、`75 [[i mean → ∅]]`；不增加意思的插入 `[[∅ → ha ha ha]]`、`[[∅ → like]]`；同义词 `a [[big → large]] screen` |
| **2** | 轻微 | 意思基本保留，只改变了一点细微含义，或者拼错的词仍然认得出来。 | 拼写相近的非词 `[[concepts → consepts]]`、`[[probably → probly]]`、`in [[euros → uros]]`；词形变化 `all [[animals → animal]] shapes`、`different [[kind → kinds]]`；冠词和介词 `with [[the → a]] touch screen`；不改变要点的时态 `we [[are → were]] doing the kinetic thing`；程度词 `it would be [[very → ∅]] expensive`；信息量低的词变成乱码，但实词保留了下来 `[[okay that is → g let us he]] good timing` |
| **3** | 部分 | 这句话的次要部分被改变或丢失，但主要意思还在。 | 代词指代的对象变了 `write down a few of [[its → his]] characteristics`；多出一点内容，但不改变主要意思 `no [[∅ → well maybe there is]]` |
| **4** | 重大 | 这句话的主要部分（主要动作、关键对象、数值、身份）被替换或丢失；或者整句变成乱码；或者加入了说话人没说过的内容。 | `so if you want to have less [[buttons → pitence]]`、`for the [[whole → horror]] of the language`、`[[pen → ben]] is here on the table`、`[[yeah i → you have]] forgot that actually`、`it is split over [[22 → 2]] different layers`、`as you already know i am [[betty → betsy]]`、`[[is it 12 point fif → at 125th]] was it 12.50`、`then that [[is going to be kind of fun → cannow becanaphone]]`、`so basically [[∅ → a person will]] not point or click` |
| **5** | 反转 | 这句话现在表达的意思与原话相反或矛盾。 | 极性反转 `i kinda doubt just that it would [[ever → never]] be done`、`there are a few but in general [[not → now]]`、`so it is just kind of does [[not → ∅]] really do anything`；评价或决策反转 `so yeah that is less [[crude → great]]`、`we should [[cancel → continue]] the launch` |

## 4. 重要性（I，1–3）

**被这个错误影响的原始信息，在这段对话里有多重要？**

- 评的是被改变或丢失的**原文内容**（箭头左边那部分，结合它所在的句子），不是评这个错误本身，也不是评整句话。
- 用上下文判断对话在讨论什么，以及这部分内容起什么作用。
- 内容类型不决定重要性：顺带提到的数字可以是 1；说明谁负责的代词可以是 3。
- **D = 1 时，I 留空。**

| I | 等级 | 定义 | 例子 |
|---|---|---|---|
| **1** | 背景 | 闲聊、话语填充、题外话，或者在讨论中不起作用的细节。 | `okay that is good timing`（回应"还剩五分钟"）；`yeah pen is here on the table`；`then that is going to be kind of fun` |
| **2** | 支撑 | 支撑讨论的细节、理由、例子或描述，但本身不是核心事实或结论。 | `write down a few of its characteristics`；`for the whole of the language`；`it would be very expensive` |
| **3** | 核心 | 正在讨论的话题中的核心事实、决策、行动、责任人、关键数量，或者说话人的立场。 | 设计参数 `it is split over 22 different layers`；正在讨论的价格 `is it 12 point fif`；自我介绍 `i am betty`；对可行性的态度 `i kinda doubt just that it would ever be done`；决策 `we should cancel the launch` |

## 5. 补充规则

1. **否定指命题的极性。** 只有当错误改变了一句话的真假时，才算极性反转（D = 5）。感叹或附和用的 "no"（`otherwise it goes oh [[no → ∅]]`）属于话语标记：D = 1–2。
2. **乱码 span：** D 看这段乱码破坏了多少意思，I 看它破坏的内容里最重要的那部分有多重要。不按词数计。
3. **在两个相邻分数之间拿不准时，选较低的那个**，并在 `note` 里写明原因。

## 6. 字段

| 字段 | 谁填 | 取值 |
|---|---|---|
| `distortion` | 人工和 LLM | 整数 1–5；一定要填，带 flag 的条目也要填 |
| `importance` | 人工和 LLM | 整数 1–3；`distortion` = 1 时留空 |
| `flag` | 人工和 LLM（选填；多个值用 `;` 分隔） | `ref_issue`：参考转写本身看起来有错或无法读懂，ASR 可能才是对的，例如 `[[on a val of → out of all]] 76`、`[[nlssd → this is the]]` · `crosstalk`：ASR 转写的是其他说话人的声音 · `uncertain`：无法仅凭文字可靠地打分（例如这句话的意思或作用不清楚）· `multi_issue`：这个 span 合并了几个相互独立的错误 |
| `note` | 人工和 LLM（人工选填） | 自由填写：为什么犹豫，在哪两个分数之间拿不准 |
| `content_type` | **只由 LLM 填** | 受影响内容的类型：`disfluency`（语气词、重复、口吃、话语标记、附和词）· `function_word`（冠词、介词、代词、助动词、连词）· `content_word`（有实际意义的名词、动词、形容词、副词）· `named_entity` · `number`（数字、价格、时间、日期）· `negation`（命题极性）· `other`。选决定失真程度的那一类；几类影响一样大时，按 negation > number > named_entity > content_word > function_word > disfluency > other 的顺序取最靠前的 |
| `error_form` | **只由 LLM 填** | `morph_variant`（同一个词的另一种形式）· `nonword`（不是真实存在的词）· `real_word`（另一个真词，包括同音词）· `garbled`（多个词变成无意义的内容）· `other`；纯删除和纯插入留空；`mixed` 类型的 span 按其中被替换的部分填 |

## 7. 人工标注须知

**独立标注**。两人都标完之前，不要和对方讨论具体条目。只填 `distortion`、`importance`、`flag`，`note` 选填；其他列不要改动。
