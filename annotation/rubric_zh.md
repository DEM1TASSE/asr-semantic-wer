# 标注规则：ASR 错误的语义严重度

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

## 2. 要回答的问题

**这个 ASR 错误让说话人原话的意思改变或丢失了多少？这部分信息在这段对话里有多重要？**

### 2.1 评分单位：单个错误的影响

只评这**一个**错误：假设同一句里的其他识别错误都已经纠正。一句话里多个错误同时出现时的整体影响不在这里考虑，后面会单独研究。

### 2.2 决定严重度的两个因素

1. **语义失真。** ASR 输出把原话的意思改变或丢失了多少？
   - 看**意思**，不看字面差了多少。意思不变的同义词不算失真（*a [[big → large]] screen*）；只改一个词也可能把一句话的意思完全反过来（*the budget was [[approved → rejected]]*）。
   - 如果**从错误的词本身**就能认出原词（比如拼写相近的 `[[concepts → consepts]]`），丢失的意思就很少。
2. **受影响的信息在这段对话里有多重要。** 它是不是核心事实、决策、行动、责任人、关键数量，或者说话人的立场？还是背景细节、客套话？

**信息丢失**（内容被删掉或变成乱码）和**错误信息**（内容被换成了别的内容，可能还读得很通顺）都要算。打分看的是有多少重要的意思被改变或丢失，**不是**读者容不容易发现这个错误。例如，*we should [[cancel → ∅]] the launch* 和 *we should [[cancel → continue]] the launch* 都可能给 4–5。

### 2.3 上下文怎么用

**上下文用来判断重要性，但不能抵消错误。**
- **要用**上下文（包括后一句）来理解说话人想表达什么，以及受影响的信息有多重要。
- **不要**因为正确的信息在对话别处重复出现、被确认过、或者能从别处推断出来，就降低严重度。例：即使下一句又正确地说了一遍预算，这一句里把预算识别错了，仍然是严重错误。

### 2.4 内容类型不决定严重度

数字、人名、否定属于**高风险内容类型**：这类内容出错时往往很严重，但**绝不自动给 5**。所有内容类型都按上面两个因素来打分。例如，`as you already know i am [[betty → betsy]]` 改掉的是说话人的自我介绍，给 5；如果是一个与讨论无关、只是顺带提到的人名被识别错，可能只给 3。同样，`it is split over [[22 → 2]] different layers` 改掉的是正在讨论的设计参数，给 5；如果是顺带一提、不影响任何结论的数字被识别错，可能给 3。

## 3. 严重度（1–5）

下面列的是典型情况。第 2 节的原则优先：同样的错误形式，放在不同的上下文里，分数可以不同。

### 1 = 意思没有改变
- **重复、口吃片段、说了一半放弃的话**，即使有好几个词：`i [[am i → ∅]] was a bit worried`、`the [[the the → ∅]] week`、`dogs can [[som → ∅]] sometimes`、`[[the sort of → ∅]] i had a quick look`
- **语气词、话语标记、附和词**：`[[yeah → ∅]] i have got one at home`、`75 [[i mean → ∅]]`、`a 5 actually [[cause → ∅]]`（句末没说完的词）
- **不增加任何意思的插入**：笑声 `[[∅ → ha ha ha]]`、单个虚词 `[[∅ → the]]`、`[[∅ → like]]`
- **意思完全相同的同义词或改写**；**拼写或格式上的变体**

### 2 = 轻微失真：意思基本保留，只有少量信息丢失或改变
- **拼写相近、从词本身就能认出原词的非词**：`[[concepts → consepts]]`、`[[probably → probly]]`、`[[thing → ting]]`、`in [[euros → uros]]`、`[[sony → soni]]`
- **词形变化**：`all [[animals → animal]] shapes`、`double [[curved → curves]]`、`different [[kind → kinds]]`
- **冠词或介词互换；不影响要点的时态变化**：`with [[the → a]] touch screen`、`we [[are → were]] doing the kinetic thing`
- **词被合并或拆开**：`[[i was → iwas]]`

### 3 = 中等：部分意思被改变或丢失，但受影响的信息重要性有限
- **信息量低的短语丢失或变成乱码**：`[[okay that is → g let us he]] good timing`
- **丢了修饰词或程度词**：`it would be [[very → ∅]] expensive`
- **代词变了，但指代的是次要对象**：`and i have got to write down a few of [[its → his]] characteristics`
- **插入了少量内容，但不改变主要意思**（常见于串音）：`no [[∅ → well maybe there is]]`
- **属于高风险内容类型，但内容在这段对话里不重要**，比如次要的人名或顺带提到的数字被换成了另一个

### 4 = 严重：重要信息被改变或丢失
- **对讨论有意义的实词被换掉或丢失**：`so if you want to have less [[buttons → pitence]]`、`for the [[whole → horror]] of the language`、`take some [[notes → not]]`、`[[pen → ben]] is here on the table`（一件物品变成了一个人）
- **指代对象变了（谁做的、在对谁说）**：`[[yeah i → you have]] forgot that actually`、`so [[you → he]] would not be pressing`
- **整句的核心命题丢失或变成乱码**：`then that [[is going to be kind of fun → cannow becanaphone]]`；`[[i kinda doubt just that → commondor she said]] it would ever be done`（说话人的态度丢了，还多出一个错误的 "she said"）
- **幻觉插入，加入了说话人没说过的内容**：`so basically [[∅ → a person will]] not point or click`

### 5 = 关键：**核心事实、决策、行动、责任人或关键数量**被改变或丢失
- **正在讨论的数值被改变或丢失**：`it is split over [[22 → 2]] different layers`（正在讨论的设计参数）、`we can like think of [[56 → physics]] designs`、`[[is it 12 point fif → at 125th]] was it 12.50`（正在讨论的价格）
- **身份或责任人被改**：`as you already know i am [[betty → betsy]]`（自我介绍）
- **命题的极性反转**：`i kinda doubt just that it would [[ever → never]] be done`、`there are a few but in general [[not → now]]`、`so it is just kind of does [[not → ∅]] really do anything`
- **评价或决策被反转或丢失**：`so yeah that is less [[crude → great]]`

## 4. 补充规则

1. **否定指的是命题的极性。** 只有当错误改变了一句话的真假时，才标 `negation`，并按极性反转来判断。感叹或附和用的 "no"（`otherwise it goes oh [[no → ∅]]`）属于话语标记：严重度 1–2，`content_type = disfluency`。
2. **乱码 span 按它破坏的最重要的内容打分**，不按词数计。
3. **实体或数字被识别成相近的非词。** 如果从错误的词本身就能认出原来的实体或数字（`teletext → teletex`、`pernilla → penila`），通常给 2。如果变成了**另一个真实存在的实体或数值**，按这条信息在对话中的重要性给 3–5。
4. **在两个相邻分数之间拿不准时，选较低的那个**，并在 `note` 里写明原因。

## 5. 字段

| 字段 | 取值 |
|---|---|
| `severity` | 整数 1–5。一定要填，带 flag 的条目也要填（给出你的暂定分数）。 |
| `content_type`：**受影响的是哪类内容** | `disfluency`（语气词、重复、口吃、话语标记、附和词）· `function_word` · `content_word` · `named_entity` · `number`（数字、价格、时间、日期）· `negation`（命题极性）· `other` |
| `error_form`：**错误长什么样** | `morph_variant`（同一个词的另一种形式）· `nonword`（不是真实存在的词）· `real_word`（另一个真词，包括同音词）· `garbled`（多个词变成无意义的内容）· `other`。**纯删除和纯插入留空。** `mixed` 类型的 span 按其中被替换的部分填。 |
| `flag`（选填；多个值用 `;` 分隔） | `ref_issue`：参考转写本身看起来有错或无法读懂，ASR 可能才是对的，例如 `[[on a val of → out of all]] 76`、`[[nlssd → this is the]]` · `crosstalk`：ASR 转写的是其他说话人的声音 · `uncertain`：无法仅凭文字可靠判断严重度（例如这句话的意思或重要性不清楚）· `multi_issue`：这个 span 合并了几个相互独立的错误 |
| `note`（选填） | 自由填写：为什么犹豫，在哪两个分数之间拿不准 |

### 5.1 `content_type` 只选一个

只选**一个**主要内容类型，即决定严重度分数的那一类。如果几类内容对分数的影响**一样大**，按下面的顺序取最靠前的：

**negation > number > named_entity > content_word > function_word > disfluency > other**

这个顺序只是为了让类别标签保持一致，不影响严重度。例：`[[we cannot buy 12 → we can buy 20]] units` 既反转了极性，又改了数字，两者都导致 5 分，所以 `content_type = negation`。

## 6. 人工标注须知

**独立标注**。两人都标完之前，不要和对方讨论具体条目。只填 `severity`、`content_type`、`error_form`、`flag`，`note` 选填；其他列不要改动。
