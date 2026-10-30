# ASR 错误语义严重度标注规则 v1

> 本文件由人工阅读约 200 条真实错误样本（AMI IHM test；Whisper large-v3 + wav2vec2，随机 120 条 + 数字/实体/否定/插入/长 span 定向抽样）后制定，所有例子都来自这批数据。
> 本文件会原样放进 LLM prompt（`src/annotate_llm.py`），改规则只改这里。

## 标注对象

每条样本是**一个错误 span**：参考文本里一段连续的识别错误（替换、删除、插入相邻的已合并）。
你会看到会议上下文（前 3 句、后 1 句）、参考句（错误标成 `[[参考 → 识别结果]]`，`∅` 表示空）、ASR 整句输出。

### 记号说明（重要）

错误统一写成 **`[[原文 → ASR]]`**：

- **箭头左边是原文**，即人实际说的话（人工转写的参考文本）
- **箭头右边是 ASR 的识别结果**
- **`∅` 表示"这一边什么都没有"**

| 写法 | 含义 | 例子 | 解释 |
|---|---|---|---|
| `[[A → ∅]]` | **删除** | `the [[the the → ∅]] week` | 人说了 "the the the week"，ASR 只输出了 "the week" |
| `[[∅ → B]]` | **插入** | `flying animal [[∅ → ha ha ha]]` | 人没说 "ha ha ha"，ASR 多输出了 |
| `[[A → B]]` | **替换** | `[[pen → ben]] is here` | 人说的是 "pen"，ASR 识别成了 "ben" |

`[[ ]]` 外面的部分是原文中识别正确的词。

**核心问题：一个只读 ASR 转写稿（没听录音）的人，会因为这一个错误误解或丢失多少信息？**

- **只评被标出的这一个 span**，同一句里的其他错误另有标注，当作不存在。
- 关注两件事：**丢失或改变的内容有多重要**，以及**读者能不能看出来这里有错**。看得出的错（乱码、非词）读者会去猜或跳过；看不出的错（通顺但意思不同）会直接误导读者。后者更严重。

## 严重度（1–5）

### 1 = 无影响：去掉或改掉后意思完全不变
- **重复、口吃片段、自我修正前的半截话**，多词也算 1：`i [[am i → ∅]] was a bit worried`、`the [[the the → ∅]] week`、`dogs can [[som → ∅]] sometimes`、`[[the sort of → ∅]] i had a quick look`
- **语气词、话语标记、附和词**：`[[yeah → ∅]] i have got one at home`、`75 [[i mean → ∅]]`、`a 5 actually [[cause → ∅]]`（句末未完成）
- **不改变意思的插入**：笑声 `[[∅ → ha ha ha]]`、单个虚词 `[[∅ → the]]`、`[[∅ → like]]`
- **拼写或格式变体**（规范化没覆盖到的）

### 2 = 轻微：读着别扭，但能**确定地**还原原意
- **能一眼看出原词的非词错误**：`[[concepts → consepts]]`、`[[probably → probly]]`、`[[thing → ting]]`、`in [[euros → uros]]`、`[[sony → soni]]`
- **形态变化**：`all [[animals → animal]] shapes`、`double [[curved → curves]]`、`different [[kind → kinds]]`
- **冠词、介词互换，不影响意思的时态变化**：`with [[the → a]] touch screen`、`we [[are → were]] doing the kinetic thing`
- **合成词或分词错误**：`[[i was → iwas]]`

### 3 = 中等：局部信息丢失或模糊，读者要猜，**可能猜错**
- **看不出原词的非词错误，但丢的词不是句子的核心**：`less [[buttons → pitence]]`（上下文能部分推测出来）
- **低信息量短语变成乱码**：`[[okay that is → g let us he]] good timing`
- **丢失修饰、限定或程度信息**：`i would say it [[is it → ∅]]` 不算（属于 1）；`it would be [[very → ∅]] expensive` 算 3
- **代词变化，但指代对象仍能从上下文判断**：`[[its → his]] characteristics`
- **无害的流畅插入**，可能让人以为说话人多说了一句（常见于串音）：`no [[∅ → well maybe there is]]`

### 4 = 严重：关键内容丢失，或者读者得到**错误但看起来合理**的信息
- **真词替换后句子仍然通顺，但意思变了**：`for the [[whole → horror]] of the language`、`take some [[notes → not]]`、`[[pen → ben]] is here on the table`（笔变成了人）
- **指代对象改变（谁做的、对谁说的）**：`[[yeah i → you have]] forgot that actually`、`so [[you → he]] would not be pressing`
- **句子核心命题变成乱码**：`then that [[is going to be kind of fun → cannow becanaphone]]`、`[[i kinda doubt just that → commondor she said]] it would ever be done`（丢了说话人的态度，还多出一个"她说"）
- **流畅的幻觉插入，加入了原话没有的内容**：`so basically [[∅ → a person will]] not point or click`

### 5 = 关键：改变了会议依赖的事实或结论，且**上下文无法纠正**
- **数值改变**：`split over [[22 → 2]] different layers`、`think of [[56 → physics]] designs`
- **名字变成另一个名字**：`i am [[betty → betsy]]`、`with [[pernilla → penelope]]`
- **极性、否定反转**（命题的真假变了）：`it would [[ever → never]] be done`、`in general [[not → now]]`、`does [[not → ∅]] really do anything`
- **评价或决策反转**：`that is less [[crude → great]]`

## 调整规则

1. **上下文冗余，降 1 级。** 如果被改掉的信息在前后句里原样出现（例如价格被重复说了一遍），就降一级。例：`[[is it 12 point fif → at 125th]] was it 12.50`，后半句又说了 12.50，所以给 4，不给 5。
2. **否定只看命题。** 只有当命题的真假改变时才算 negation，给 5。感叹语或附和语里的 "no"（`it goes oh [[no → ∅]]`）按话语标记处理，给 1–2。
3. **乱码 span 按其中最重要的那部分内容打分**，不按词数累加。
4. **实体或数字的非词近似**，如果读者大概率认得出原词（`teletext → teletex`、`pernilla → penila`），给 2–3；变成**另一个真实存在的**名字或数字，给 5。
5. **拿不准的时候**，在两个分数之间选**更低**的，并在 note 里写明原因。

## 标注字段

| 字段 | 取值 |
|---|---|
| `severity` | 1–5 |
| `content_type`：**受影响的内容是什么** | `disfluency`（语气词、重复、口吃、话语标记、附和）· `function_word` · `content_word` · `named_entity` · `number`（数字、价格、时间、日期）· `negation`（命题极性）· `other` |
| `error_form`：**错误长什么样** | `deletion` · `insertion` · `morph_variant`（同词的不同形式）· `nonword`（拼不出真词）· `real_word`（换成了另一个真词，含同音词）· `garbled`（多词变成乱码）|
| `flag`（可空） | `ref_issue`：参考文本本身有错或不可读，ASR 可能才是对的，例如 `[[on a val of → out of all]] 76`、`[[nlssd → this is the]]` · `crosstalk`：ASR 转写的是旁边其他说话人的声音 |

带 `flag` 的条目仍然要打分，但分析时会单独统计或排除。

## 人工标注流程

1. 两人**独立**标注 `annotation/human_pilot_A.csv` 和 `human_pilot_B.csv`（同一批 80 条），不要讨论。
2. 跑 `pixi run python src/agreement.py`，查看一致性（quadratic weighted κ、Krippendorff α）和分歧最大的条目。
3. 如果 α < 0.6：讨论分歧条目，修改本文件（加例子或规则），再标一轮**新的**样本。
