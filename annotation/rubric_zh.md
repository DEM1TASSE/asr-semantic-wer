# ASR Semantic Distortion — Annotation Rubric

## 1. Severity Rubric

标注目标： 评估单个 ASR 错误在多大程度上改变、丢失或添加了当前话语所表达的语义信息。

| Score | Level      | 评分标准                                          |
| ----- | ---------- | --------------------------------------------- |
| 1     | Negligible | 语义没有任何变化。 只有拼写、语法、重复或流畅度差异，所表达的意思没有改变。 |
| 2     | Minor      | 轻微语义变化。 意思有小的变化（例如程度略有减弱），但主要意思和具体信息均保留。 |
| 3     | Moderate   | 局部信息失真。 有意义的具体信息发生变化或丢失，而原句的整体含义仍大体保留。 |
| 4     | Major      | 主要信息失真。 原句的主要意思被明显改变、丢失或变得无法理解。 |
| 5     | Critical   | 主要意思反转。 核心命题的方向被反转，例如肯定与否定、接受与拒绝、取消与继续。 |

### Decision Guide

按顺序判断：

1. 意思有没有任何变化，哪怕很轻微？
   - 没有 → 1
2. 核心命题的方向是否被反转？
   - 是 → 5
3. 原句的主要意思是否被明显改变、丢失或变得无法理解？
   - 是 → 4
4. 是否有有意义的具体信息发生变化或丢失，而整体含义仍大体保留？
   - 是 → 3
   - 否，只有轻微的意思变化 → 2

### 评分原则

- 只评价标记的错误 span：假设同一句中的其他 ASR 错误都已纠正。
- 上下文用于理解语义：可以参考前后发言理解指代和省略，但不评价信息对整场会议的重要性，也不利用其他发言补偿错误。
- 语义优先于形式：不根据单复数、时态、词序、编辑距离、错误长度或是否为非词直接决定分数。原文里有不认识的词，先查一下。
- 识别错的词（拼写错误、非词、读音相近的词）按同一套标准打分，见第 2 节的“识别错的词”。
- 不流畅：删掉或改动不增加任何意思的重复、填充词、放弃的开头，给 **1**。但不能只看表面就自动给 1：要看原话完整的意思，如果受影响的词其实有意义，按意义打分。
- 自我修正：说话人放弃一个说法并重新开口时，被放弃的部分算不流畅，但改口后的部分是说话人真正的意思。改口部分的错误按普通内容打分。
- 插入：按插入的词给**这句话**增加或改变了什么意思来打分，包括很可能来自其他说话人的词（同时标 `crosstalk`）。
- 不同的数值不一定严重：看意思改变了多少。`a few → several` 几乎不改变意思，而 `22 → 2` 给出了明显错误的数量。
- 区分失真与反转：信息丢失、乱码或错误最高为 4；5 只给核心命题方向反转的情况。
- 不确定时：仍给出最合理的整数分数，并标记 `uncertain`。

## 2. Calibration Examples

记号：`[[reference → ASR]]`，其中 `∅` 表示空文本。

这些示例用于说明评分边界，不代表同类错误必须得到相同分数。

### 1 — Negligible

| Reference → ASR                    | 理由              |
| ---------------------------------- | --------------- |
| `i gave it [[a → ∅]] one`          | 冠词省略，意思不变       |
| `all [[animals → animal]] shapes`  | 名词修饰语形式变化，不影响含义 |
| `i [[am i → ∅]] was a bit worried` | 删除已放弃的口语开头      |

### 2 — Minor

| Reference → ASR                      | 理由           |
| ------------------------------------ | ------------ |
| `it would be [[very → ∅]] expensive` | 程度减弱，但主要判断不变 |

### 3 — Moderate

| Reference → ASR                                    | 理由                  |
| -------------------------------------------------- | ------------------- |
| `let us use the [[blue → ∅]] pen for the logo`     | 笔的属性丢失，使用笔的计划仍在     |

### 4 — Major

| Reference → ASR                                                   | 理由       |
| ----------------------------------------------------------------- | -------- |
| `i would go for [[4 too → for to]]`（前文问 four or five）             | 主要回答丢失   |
| `it is split over [[22 → 2]] different layers`                    | 层数是这句话的要点，被明显改变 |
| `[[capture we do not have → keptorydon tes]] to do anything with` | 主要陈述无法理解 |

### 5 — Critical

| Reference → ASR                              | 理由     |
| -------------------------------------------- | ------ |
| `it does [[not → ∅]] really do anything`     | 否定变肯定  |
| `we should [[cancel → continue]] the launch` | 行动方向反转 |
| `the budget was [[approved → rejected]]`     | 结果反转   |

### 识别错的词

用于拼写错误、非词、读音相近的词。

先不看原文，以一个英语流利、了解会议主题的读者的视角只读 ASR 那句话，判断原本的意思还能恢复多少，然后按正常的 1–5 档打分。不要仅凭拼写是否相近、是否是词典里的词来决定分数。

| 原文 → ASR | ASR 句子（读者看到的） | 只读 ASR 句子时 | 分数 |
|---|---|---|---|
| `[[probably → probly]]` | *now we are developing a remote control which you probly already know* | 意思能恢复 | 1 |
| `[[concepts → consepts]]` | *we have to come to a decision on remote control consepts* | 意思能恢复 | 1 |
| `[[mo morse code → mormorscot]]` | *when it sees the amplified mormorscot signal then it will know what action it has to do* | 丢了次要信息（哪种信号） | 3 |
| `[[56 designs → fisextrasens]]` | *but we can like think of fisextrasens* | 丢了主要信息（能想出什么） | 4 |
| `[[small → smart]]`（虚构） | *we need a smart screen for the remote* | 次要信息被改（什么样的屏幕） | 3 |
| `[[speaker → sticker]]`（虚构） | *the remote should have a sticker* | 主要意思被改（遥控器上要有什么） | 4 |
| `[[can → can't]]`（虚构） | *we can't finish it today* | 意思反了 | 5 |

## 3. Content Type

选择错误影响的一个主要内容类型。Content type 不决定 severity。

**按顺序**回答下面的问题，选**第一个**符合的类型。看受影响的词**在这句话里起什么作用**，而不是它属于哪类词。

| 顺序 | Label | 问题 |
|---|---|---|
| 1 | `disfluency` | 是否为填充词、重复、放弃的开头、无实质意义的附和或话语标记，**不提供任何有意义的信息**？ |
| 2 | `negation` | 是否决定一个命题是肯定还是否定（例如 *not*、*never*、*can't*）？ |
| 3 | `number` | 是否为数量、日期、时间或金额？ |
| 4 | `named_entity` | 是否为人名、地名、机构名或产品名？ |
| 5 | `function_word` | 是否为冠词、介词、代词、助动词或连词？ |
| 6 | `content_word` | 是否为其他有意义的词或短语（名词、动词、形容词、副词）？ |
| 7 | `other` | 以上都不是。 |

- **disfluency 只用于不增加任何意思的词。** *I think*、*yes*、附加问句等**不会**自动归为 disfluency：如果它们表达了判断、回答、同意或请求确认，就按这个作用选类型（例如表达说话人看法的 *I think* → `content_word`；作为真正回答的 *yes* → `other`）。只表示"在听"的 *yes*、*mm-hmm* 属于 `disfluency`。
- **重复一律算 disfluency，即使重复的是虚词或实词**：`the [[the the → ∅]] week`、`bright colorful trendy [[trendy → ∅]] design`。
- **合并的 span 涉及多个类型时**：按上面的顺序作为统一约定（例如 `[[not five → ∅]]` → `negation`）。如果这个 span 由几个相互独立的错误组成、分不出主要类型，选 `other`，并加上 `multi_issue`。

## 4. Annotation Instructions

### 标注单位

每条样本是一个连续的 ASR error span，相邻的 substitution、deletion、insertion 已由预处理合并。

标注时会看到：

- 当前参考句，以及**只含这一个错误**的 ASR 句子（这句话里的其他识别错误都已纠正）。比较这两句话。
- 前 3 句、后 1 句会议上下文，包含说话人编号。
- 目标错误：`[[reference → ASR]]`。
- 自动生成的 `edit_operation`，无需人工修改。

### Required Fields

| Field          | Value       |
| -------------- | ----------- |
| `severity`     | 整数 1–5      |
| `content_type` | 第 3 节中的一个类别 |

### Optional Fields

| Field  | Value                                                       |
| ------ | ----------------------------------------------------------- |
| `flag` | `ref_issue` / `crosstalk` / `uncertain` / `multi_issue`，可多选 |
| `note` | 简短说明难以判断的原因                                                 |

Flag 说明：

- `ref_issue`：参考转写可能有误或无法使用。
- `crosstalk`：ASR 可能识别了其他说话人的声音。
- `uncertain`：上下文不足以可靠判断。
- `multi_issue`：一个 span 合并了多个独立错误。