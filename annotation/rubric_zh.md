# ASR Semantic Distortion — Annotation Rubric

## 1. Severity Rubric

标注目标： 评估单个 ASR 错误在多大程度上改变、丢失或添加了当前话语所表达的语义信息。

| Score | Level      | 评分标准                                          |
| ----- | ---------- | --------------------------------------------- |
| 1     | Negligible | 语义没有任何变化。 只有拼写、语法、重复或流畅度差异，说话人说的内容没有改变。 |
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
| `the amplified [[morse code → mormorscot]] signal` | 具体信号类型变得不清楚，但整体意思（看到信号就行动）仍在 |
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

## 3. Content Type

选择错误影响的一个主要内容类型。Content type 不决定 severity。

| Label           | Definition               |
| --------------- | ------------------------ |
| `disfluency`    | 填充词、重复、口吃、放弃的开头、附加问句、附和词 |
| `function_word` | 冠词、介词、代词、助动词、连词          |
| `content_word`  | 普通实义词或短语                 |
| `named_entity`  | 人名、地名、机构名、产品名            |
| `number`        | 数量、日期、时间、金额              |
| `negation`      | 影响命题肯定或否定的成分             |
| `other`         | 其他，或多个类型无法区分主要类别         |

## 4. Annotation Instructions

### 标注单位

每条样本是一个连续的 ASR error span，相邻的 substitution、deletion、insertion 已由预处理合并。

标注时会看到：

- 当前参考句及完整 ASR 输出。
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