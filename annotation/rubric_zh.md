# 标注规则：ASR 错误的语义失真

## 1. 标注对象

每一条是**一个错误 span**：ASR 输出与参考转写不一致的一段连续区域（相邻的替换、删除、插入已合并为一个 span）。

每条你会看到：
- 会议上下文：前 3 句、后 1 句，带说话人编号，取自参考转写；
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

## 2. 要回答的问题

**这个错误在多大程度上改变、丢失或凭空添加了原话所表达的信息？**

可以借助前后的对话来理解原话的意思，但**不要**考虑这条信息对整场会议有多重要。

## 3. 严重度（1–5）

| 分数 | 定义 |
|---|---|
| **1 — 可忽略** | 意思基本没变，只有拼写、语法、语气词或流畅度上的差别。 |
| **2 — 轻微** | 意思有少许改变或丢失，主要信息完整保留。 |
| **3 — 中等** | 有一部分有意义的信息被改变或丢失，但这句话的主要意思还在。 |
| **4 — 严重** | 主要信息被明显改变或丢失，包括主要内容已经无法理解的情况。 |
| **5 — 关键** | ASR 输出表达的信息与原话的主要意思相反，或直接矛盾。 |

## 4. 内容类型

选**一个**最主要的、受错误影响的内容类型。

| 类型 | 定义 |
|---|---|
| `disfluency` | 语气词、重复、口吃、说了一半放弃的话、附加问句（"isn't it"）、附和词 |
| `function_word` | 冠词、介词、代词、助动词、连词 |
| `content_word` | 有实际意思的普通词或短语（名词、动词、形容词、副词） |
| `named_entity` | 人名、地名、机构名、产品名 |
| `number` | 数量、时间、金额、日期 |
| `negation` | 真正表示否定的成分（一句话是真是假取决于它） |
| `other` | 不属于以上任何一类，或者涉及多个类型、分不出哪个是主要的 |

内容类型描述的是错误**影响了什么内容**，**不决定**严重度：每种类型都可能出现在任何一个分数上。

## 5. 原则

1. **只评被标出的这一个 span**，假设其他 ASR 错误都已纠正。
2. **意思优先。** 不要根据字母差了几个、词性、错误有多长、ASR 输出是不是真实存在的词来决定分数，而是根据被改变、丢失或添加的意思来决定。
3. **区分丢失和矛盾。** 信息丢失或变成乱码，**最高 4 分**。只有当 ASR 输出说出了与原话主要意思不相容的内容时，才给 **5 分**：命题被反转，或者主要信息被换成了另一个不相容的数值或实体。
4. **上下文只用来理解原意。** 用上下文理解说话人想表达什么。不要用它来判断这条信息对整场会议是否重要，也不要因为别的发言重复或弥补了这条信息就降低分数。
5. **原文里有不认识的词，就去查。** 按这个词的实际意思来判断，不要按你自己熟不熟悉它来判断。
6. **如果这一条明显有歧义**，给出你认为最合理的整数分数，并加上 `uncertain` 标记。

## 6. 校准示例

分数取决于给出的上下文，不是按词的类别来定的。同一种内容类型会有意出现在不同的分数上。

### 1 — 可忽略
| 原文 → ASR（带上下文） | 内容类型 | 理由 |
|---|---|---|
| `so [[um → ∅]] we have to decide` | disfluency | 意思没有变化 |
| `a sweater [[is → his]] on top or it is behind a plant` | function_word | 语法不通，但仍然表达毛衣在上面 |
| `it is more idiot proof [[is not it → isn]]` | disfluency | 附加问句被破坏，陈述本身没变（这里的 "not" 不是真正的否定） |
| `now we are developing a remote control which you [[probably → probly]] already know` | content_word | 只是拼写错误 |
| `we need to agree on the [[timeline → schedule]]` | content_word | 在这个语境里基本同义 |

### 2 — 轻微
| 原文 → ASR（带上下文） | 内容类型 | 理由 |
|---|---|---|
| `it would be [[very → ∅]] expensive` | content_word | 程度减弱，说法本身没变 |
| `we are focusing on a sort of mid range [[∅ → approach]]` | content_word | 插入的词让说法稍有变化 |
| `we can have you know all [[animals → animal]] shapes` | content_word | 丢了复数，意思保留 |
| `if we [[are → were]] doing the kinetic thing` | function_word | 时态稍有变化，要点不变 |
| `the [[telewest → tally west]] remote controls are silver plastic` | named_entity | 品牌名拼错了，但大概率仍能认出来 |

### 3 — 中等
| 原文 → ASR（带上下文） | 内容类型 | 理由 |
|---|---|---|
| `when it sees the amplified [[mo morse code → mormorscot]] signal then it will know what action it has to do` | content_word | 信号的类型丢了，但主要关系（看到信号 → 做出动作）还在 |
| `i have got to write down a few of [[its → his]] characteristics` | function_word | 代词从指画的那个动物变成了指一个人 |
| `so we are supposed to [[evaluate it → b evaluated]] right now` | content_word | 可能把"谁评估、谁被评估"颠倒了。这是有意保留的边界样本（3 或 4），拿不准就加 `uncertain` |

### 4 — 严重
| 原文 → ASR（带上下文） | 内容类型 | 理由 |
|---|---|---|
| `i would go for [[4 too → for to]]`（回答 "between four or five"） | number | 选中的数值，也就是对问题的回答，丢了 |
| `but we can like think of [[56 designs → fisextrasens]]` | number | 数量和对象都丢了 |
| `[[capture we do not have → keptorydon tes]] to do anything with` | content_word | 主要陈述变成乱码；否定是丢了，不是反转了 |
| `yeah [[pen → ben]] is here on the table` | content_word | 一件物品变成了一个人 |
| `[[yeah i → you have]] forgot that actually` | function_word | 忘了事的人变了 |

### 5 — 关键
| 原文 → ASR（带上下文） | 内容类型 | 理由 |
|---|---|---|
| `i kinda doubt just that it would [[ever → never]] be done` | negation | 立场被反转 |
| `so it is just kind of does [[not → ∅]] really do anything` | negation | 删掉 "not"，陈述变成了相反的意思 |
| `so yeah that is less [[crude → great]]` | content_word | 评价被反转 |
| `it is split over [[22 → 2]] different layers` | number | 主要数值被换成了一个不相容的数值 |
| `we should [[cancel → continue]] the launch` | content_word | 行动被反转 |

## 7. 字段

| 字段 | 取值 |
|---|---|
| `severity` | **必填**，整数 1–5 |
| `content_type` | **必填**，从第 4 节的类型中选一个 |
| `flag` | 选填；多个值用 `;` 分隔 · `ref_issue`：参考转写本身看起来有错或无法读懂，ASR 可能才是对的，例如 `[[on a val of → out of all]] 76` · `crosstalk`：ASR 转写的是其他说话人的声音 · `uncertain`：这一条明显有歧义 · `multi_issue`：这个 span 合并了几个相互独立的错误 |
| `note` | 选填，自由填写，例如在哪两个分数之间犹豫、为什么 |

## 8. 人工标注须知

**独立标注**；两人都标完之前，不要和对方讨论具体条目。只填 `severity`、`content_type`、`flag` 和 `note`，其他列不要改动。保留原始标注：讨论之后如果要修改，改在单独的副本里，不要覆盖原始结果。
