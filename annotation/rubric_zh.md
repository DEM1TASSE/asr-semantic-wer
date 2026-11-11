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

**读者会因为这一个错误，丢失或误解多少信息？**

### 2.1 读者是谁

读者是**会后阅读 ASR 生成的会议转写稿的人**，比如看会议记录的人。读者听不到音频，但能读到这条样本给出的上下文，**包括后一句**。

### 2.2 评分单位：单个错误的反事实影响

对目标错误，**假设转写稿的其他部分都是正确的**：同一句里的其他识别错误都已纠正，上下文就是给出的样子。严重度只衡量**这一个错误单独存在时**的影响。一句话里多个错误同时出现的整体影响不在这里考虑，这部分会单独研究。

### 2.3 决定严重度的两个因素

1. **在这段对话里的重要性。** 受影响的内容是不是核心事实、决策、行动、责任人、关键数量，或说话人的立场？还是背景细节、客套话？
2. **可恢复性。** 读者能不能**可靠地**恢复原意？"可靠"指能凭这句话和给出的上下文，以很高的把握猜出原词或原意。

错误影响意思的方式有两种，两种都要算：
- **信息丢失**：内容被删掉，或者变得读不懂（非词、乱码）。读者通常能察觉到这里有问题，但不知道原来说的是什么。
- **错误信息**：内容被换成了通顺但不同的内容。读者会在毫无提示的情况下被误导。

一看就错的错误**不一定**轻微：丢掉一个关键决策或行动，可能和把它换成错误的内容一样严重。比如 *we should [[cancel → ∅]] the launch* 和 *we should [[cancel → continue]] the launch* 都可能给 4–5。通顺程度和可恢复性会影响打分，但**不能盖过受影响内容本身的重要性**。

### 2.4 看意思，不看字面差异或词的类型

打分依据是**语义后果**，不是字面上差了多少，也不是错在哪类词上。
- 同义词或改写，只要意思完全不变，就给 1，即使是实词：*a [[big → large]] screen*。
- 只改一个词，如果反转了一个关键命题，也可以给 5：*the budget was [[approved → rejected]]*。
- 数字、人名、否定属于**高风险内容类型**：这类内容出错时往往很严重，但**绝不自动给 5**。所有内容类型都按上面两个因素来打分。例如，`as you already know i am [[betty → betsy]]` 改掉的是说话人的自我介绍，给 5；如果是一个与讨论无关、只被顺带提到的人名被识别错，可能只给 3。同样，`it is split over [[22 → 2]] different layers` 改掉的是正在讨论的设计参数，给 5；如果是顺带一提、不影响任何结论的数字被改，可能给 3–4。

## 3. 严重度（1–5）

下面列的是典型情况。第 2 节的原则优先：同样的错误形式，放在不同上下文里，分数可以不同。

### 1 = 无影响：有没有这个错误，意思完全一样
- **重复、口吃片段、说了一半放弃的话**，即使有好几个词：`i [[am i → ∅]] was a bit worried`、`the [[the the → ∅]] week`、`dogs can [[som → ∅]] sometimes`、`[[the sort of → ∅]] i had a quick look`
- **语气词、话语标记、附和词**：`[[yeah → ∅]] i have got one at home`、`75 [[i mean → ∅]]`、`a 5 actually [[cause → ∅]]`（句末没说完的词）
- **不增加任何意思的插入**：笑声 `[[∅ → ha ha ha]]`、单个虚词 `[[∅ → the]]`、`[[∅ → like]]`
- **意思完全相同的同义词或改写**；**拼写或格式上的变体**

### 2 = 轻微：读起来别扭，但读者能**可靠地**恢复原意
- **一眼就能看出原词的非词**：`[[concepts → consepts]]`、`[[probably → probly]]`、`[[thing → ting]]`、`in [[euros → uros]]`、`[[sony → soni]]`
- **词形变化**：`all [[animals → animal]] shapes`、`double [[curved → curves]]`、`different [[kind → kinds]]`
- **冠词或介词互换；不影响要点的时态变化**：`with [[the → a]] touch screen`、`we [[are → were]] doing the kinetic thing`
- **词被合并或拆开**：`[[i was → iwas]]`

### 3 = 中等：局部信息丢失或变模糊，读者需要猜，**可能猜错**；或者被改的内容不重要
- **认不出原词的非词，但丢掉的词不是核心**：`less [[buttons → pitence]]`（上下文能部分推测出来）
- **信息量低的短语变成乱码**：`[[okay that is → g let us he]] good timing`
- **丢了修饰词或程度词**：`it would be [[very → ∅]] expensive`
- **代词变了，但上下文仍能确定指代对象**：`[[its → his]] characteristics`
- **通顺但无害的插入**，看起来像说话人多说了一句（常见于串音）：`no [[∅ → well maybe there is]]`
- **属于高风险内容类型，但内容在这段对话里不重要**，比如次要的人名或顺带提到的数字被换成了另一个

### 4 = 严重：关键内容丢失，或读者得到**错误但看似合理**的信息
- **换成另一个真词，句子仍然通顺，但意思变了**：`for the [[whole → horror]] of the language`、`take some [[notes → not]]`、`[[pen → ben]] is here on the table`（一件物品变成了一个人）
- **指代对象变了（谁做的、在对谁说）**：`[[yeah i → you have]] forgot that actually`、`so [[you → he]] would not be pressing`
- **整句的核心命题丢失或变成乱码**：`then that [[is going to be kind of fun → cannow becanaphone]]`；`[[i kinda doubt just that → commondor she said]] it would ever be done`（说话人的态度丢了，还多出一个错误的 "she said"）
- **通顺的幻觉插入，加入了说话人没说过的内容**：`so basically [[∅ → a person will]] not point or click`

### 5 = 关键：改变或丢失了对话所依赖的**核心事实、决策、行动、责任人或关键数量**，且上下文无法纠正
- **正在讨论的数值被改**：`it is split over [[22 → 2]] different layers`（在讨论设计参数）、`we can like think of [[56 → physics]] designs`
- **身份或责任人被改**：`as you already know i am [[betty → betsy]]`（自我介绍）
- **命题的极性反转**：`i kinda doubt just that it would [[ever → never]] be done`、`there are a few but in general [[not → now]]`、`so it is just kind of does [[not → ∅]] really do anything`
- **评价或决策被反转或丢失**：`so yeah that is less [[crude → great]]`

## 4. 调整规则

1. **上下文可恢复性。** 如果给出的上下文**明确**提供了正确信息，就按读者能否可靠恢复原意来**重新判断**严重度。**不要**固定降一级：能完全恢复的，可以从 5 降到 2；只能部分恢复的，降得少一些。
   - 例：`[[is it 12 point fif → at 125th]] was it 12.50`。说话人紧接着又说了一遍 "12.50"，读者大概率能恢复出价格，给 3。
   - 如果转写稿里出现**互相矛盾**的信息（例如上下文说 12，ASR 写成 20），**不能**假设读者知道哪个是对的，按不可恢复处理。
2. **否定指的是命题的极性。** 只有当错误改变了一句话的真假时，才标 `negation`，并按极性反转来判断。感叹或附和用的 "no"（`otherwise it goes oh [[no → ∅]]`）属于话语标记：严重度 1–2，`content_type = disfluency`。
3. **乱码 span 按它破坏的最重要的内容打分**，不按词数计。
4. **实体或数字被识别成相近的非词。** 如果读者能可靠认出原来的实体或数字（`teletext → teletex`、`pernilla → penila`），通常给 2–3。如果变成了**另一个真实存在的实体或数值**，按这条信息对理解会议的重要性给 3–5；只有改变了核心事实、决策、责任人或关键数量，并且上下文无法纠正时，才给 5。
5. **在两个相邻分数之间拿不准时，选较低的那个**，并在 `note` 里写明原因。

## 5. 字段

| 字段 | 取值 |
|---|---|
| `severity` | 整数 1–5。一定要填，带 flag 的条目也要填（给出你的暂定分数）。 |
| `content_type`：**受影响的是哪类内容** | `disfluency`（语气词、重复、口吃、话语标记、附和词）· `function_word` · `content_word` · `named_entity` · `number`（数字、价格、时间、日期）· `negation`（命题极性）· `other` |
| `error_form`：**错误长什么样** | `morph_variant`（同一个词的另一种形式）· `nonword`（不是真实存在的词）· `real_word`（另一个真词，包括同音词）· `garbled`（多个词变成无意义的内容）· `other`。**纯删除和纯插入留空。** `mixed` 类型的 span 按其中被替换的部分填。 |
| `flag`（选填；多个值用 `;` 分隔） | `ref_issue`：参考转写本身看起来有错或无法读懂，ASR 可能才是对的，例如 `[[on a val of → out of all]] 76`、`[[nlssd → this is the]]` · `crosstalk`：ASR 转写的是其他说话人的声音 · `uncertain`：无法仅凭文字可靠判断严重度（例如缺少上下文、指代不明）· `multi_issue`：这个 span 合并了几个相互独立的错误 |
| `note`（选填） | 自由填写：为什么犹豫，在哪两个分数之间拿不准 |

### 5.1 `content_type` 只选一个

只选**一个**主要内容类型，即决定严重度分数的那一类。如果几类内容对分数的影响**一样大**，按下面的顺序取最靠前的：

**negation > number > named_entity > content_word > function_word > disfluency > other**

这个顺序只是为了让类别标签保持一致，不影响严重度。例：`[[we cannot buy 12 → we can buy 20]] units` 既反转了极性，又改了数字，两者都导致 5 分，所以 `content_type = negation`。

## 6. 人工标注须知

**独立标注**。两人都标完之前，不要和对方讨论具体条目。只填 `severity`、`content_type`、`error_form`、`flag`，`note` 选填；其他列不要改动。
