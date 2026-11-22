# 11 月 19 日 TA discussion 准备

核对日期为 2026-11-18。依据包括线上 checkpoint.tex、最新仓库 b915869、TA 回复截图，以及 Delta 上三个已完成任务的实际 results.json。本文是讨论准备，实验提议与已完成结果分别注明。

## 1. 开场要讲清楚的问题

我们研究会议字幕里一处识别错误造成多少语义变化。比如漏掉一个无意义的“呃”和漏掉否定词，WER 都各计一处，读者理解受到的影响却很不同。我们的输出包括每个错误片段的严重度，以及聚合后的系统错误分布和 Semantic-WER。

我们提出三个可检验的问题：

1. 两个人能否按明确规则一致地评价错误对意思的影响？LLM 的判断与人是否一致？
2. 能否用大模型标签训练一个较便宜的 DistilBERT 评分器？它面对没见过的 ASR 系统所产生的错误还能判准吗？
3. 按语义影响评价，会如何改变我们对 ASR 系统差距的理解？如果要进一步说指标更符合人的理解，还需要独立人工验证。

这里有两类模型。Whisper、wav2vec 2.0、Parakeet 听录音并生成字幕。DeepSeek 与 DistilBERT 读取文本、给已有错误评分。DistilBERT 的训练目标是严重度 1–5。

## 2. 方法怎样运行

同一批 AMI 多人会议录音 → 各 ASR 生成英文字幕 → 与人工参考对齐 → 相邻错误合成一个片段 → 给每个片段构造只包含这一处错误的句子 → 结合上下文给严重度 → 训练评分器并聚合成指标。

假设参考是 `We um finetune BERT on downstream tasks`，机器同时漏了 `um`、把 `BERT` 写成 `birds`。评 `BERT → birds` 时比较：

- 参考 `We um finetune BERT on downstream tasks`
- 对照 `We um finetune birds on downstream tasks`

其他部分保持相同，判断目标错误单独造成的语义变化。这个构造衡量隔离后的影响。真实字幕里多处错误可能增强或抵消彼此的影响，聚合分数需要另行验证。

Teacher 输入包含前三句与后一句参考上下文。当前已跑的 student 用前三句上下文、带错误标记的参考句、single-error hypothesis。解释时应把各自输入说准确。

## 3. 从 midterm 到现在的实际进展

| 项目 | Midterm | 11 月 18 日核实状态 |
|---|---|---|
| ASR 系统 | Whisper、wav2vec 2.0 | 新增 Parakeet-TDT-0.6b-v2，三种架构 |
| 主分析测试录音 | 原始 500 句 | 扩成 700 句，来自相同 16 个 test meetings |
| Teacher 标注 | 当时报告 22,392 个片段 | 最新仓库共 28,566 个片段，三系统全部有标签 |
| Student | 报告里列为下一步 | 旧双系统方案六配置 × 三种子，18 次训练全部完成 |
| 最新主实验 | 单系统 5K、混合 5K/10K | 改为三系统 All-3 9K 与三组 leave-one-out 9K，划分已准备 |
| 200 条人工测试 | 两系统各 100 条的计划 | 已抽样成 67/67/66，仓库两份表各 200 行，severity 都未填写 |
| Sentence-BERT、小 teacher | 待补充 | 最新计划已写入，尚未核实到实验结果 |

最新仓库的训练脚本警告指的是远端 main 仍保留的旧模板。我们实际在 Delta 跑的是本地改过的版本，读取固定划分，使用 single-error 输入，按 dev MAE 选 checkpoint。服务器目前还没有三系统 train_all3 划分，因此这 18 次结果属于旧双系统设置。

### 新增 Parakeet 后的系统结果

同一批 700 句。原始 WER 使用全部对齐错误。校正 WER 与 Semantic-WER 排除 teacher 标为 ref_issue 的片段，参考词总数不变。

| 系统 | 原始 WER % | 排除 ref_issue 后 WER % | Semantic-WER-hard % |
|---|---:|---:|---:|
| Parakeet-TDT | 7.56 | 7.26 | 1.56 |
| Whisper | 11.62 | 11.20 | 1.42 |
| wav2vec 2.0 | 22.50 | 22.33 | 7.32 |

可讲的观察是 Parakeet 字面错误更少，语义加权后与 Whisper 的分数接近。尚不能凭 1.42 与 1.56 的小差距判定哪个更符合人的理解。报告中的旧 500 句结果与这里的 700 句要注明各自样本范围。

### 已完成 student 的三随机种子结果

测试为旧双系统 test_balanced，Whisper/wav2vec2 各 500 条，目标为 DeepSeek 严重度。表内为三种子均值 ± 样本标准差。

| 配置 | QWK ↑ | MAE ↓ |
|---|---:|---:|
| Whisper-only 5K | 0.677 ± 0.009 | 0.448 ± 0.011 |
| wav2vec2-only 5K | 0.686 ± 0.022 | 0.474 ± 0.029 |
| Mixed 5K | 0.717 ± 0.016 | 0.434 ± 0.014 |
| Mixed 10K | 0.754 ± 0.023 | 0.388 ± 0.017 |
| Mixed 1K | 0.557 ± 0.017 | 0.535 ± 0.018 |
| Mixed 2.5K | 0.690 ± 0.012 | 0.449 ± 0.020 |

始终预测 severity 1 的基线 MAE 为 0.648，Mixed-10K 平均误差相对降低约 40%。这是对 teacher 标签的拟合效果。

同一测试系统上比较不同训练来源，更能说明迁移问题。Whisper 错误上的 QWK 从 Whisper-only 的 0.678 降到 wav2vec2-only 的 0.597；wav2vec2 错误上的 QWK 从 wav2vec2-only 的 0.712 降到 Whisper-only 的 0.637。混合 5K 在 wav2vec2 上约 0.715，在 Whisper 上约 0.669，因此固定 5K 混合并未在每个系统上都提升。Mixed-10K 同时增加了样本量，提升不能全部归因于数据来源更丰富。

这些结果支持继续研究来源迁移，但人工 200 条测试还要验证 teacher/student 是否按人认可的标准判断。

## 4. TA 五条反馈逐条怎么回答

### A. 五级怎么定？3/4 和 4/5 是否模糊？

当前团队记录显示，规则从约 200 个真实错误片段的人工查看开始，包含随机与有针对性的样本，再经过练习标注、50 条独立 pilot 的分歧分析修订。Pilot 使用 v2.3，随后 v2.4 根据分歧澄清用法。五级由团队设计，记录里没有实验证据说明“五级一定优于三级或四级”。

| 分数 | 评什么 | 例子（示意，依具体上下文判断） |
|---|---|---|
| 1 | 意思没变 | 删除无意义的重复或“呃” |
| 2 | 语气或程度稍变，主要意思和具体事实保留 | `very expensive → expensive` |
| 3 | 局部具体信息丢失，整句主要意思仍在 | `use the blue pen → use the pen` |
| 4 | 主要意思变了、丢了或无法理解 | 在“四号还是五号”之后，答案 `four too → for to` |
| 5 | 核心判断方向反转 | `should cancel → should continue` |

3/4 的边界取决于丢失信息在这句话里是不是主要命题。4/5 按“主要信息失真”与“明确反向命题”划分。5 被专门留给反转，因此它是对反转敏感的等级设计，最严重的大段丢失也可能是 4。All-3 9K 中仅 60 条 teacher 标签为 5，独立人工测试可能不足以稳定估计这一类。

回应 TA 可以说：我们同意边界仍有主观性，现有 α≈0.79 是整体一致性证据；接下来会看独立 200 条的 3↔4、4↔5 混淆、分歧实例与不确定标记，而不只报一个总体分数。可请 TA 判断是否需要把 4/5 合并后做一次敏感性分析。

### B. 加入不同结构的 ASR

已完成 Parakeet 的转写、对齐与 teacher 标注。现在包含 encoder–decoder、CTC、transducer。Qwen-ASR 尚未核实到实验数据。

可请 TA 确认，课程项目目前是否以这三种架构为足够的范围，把剩余时间优先用于独立人工验证与评分器实验。

### C. 合并数据并做 leave-one-out

已按这个意见准备新划分。每个主实验都用 9,000 个训练错误：

| 模型 | Whisper | wav2vec2 | Parakeet |
|---|---:|---:|---:|
| All-3 | 3,000 | 3,000 | 3,000 |
| 留出 Whisper | 0 | 4,500 | 4,500 |
| 留出 wav2vec2 | 4,500 | 0 | 4,500 |
| 留出 Parakeet | 4,500 | 4,500 | 0 |

评测时每个模型都测三个系统。比如比较 All-3 与“留出 Parakeet”在同一批 Parakeet 测试错误上的表现。训练总量相同，考察缺少该来源时的变化。各来源的训练分配也随之改变，应把结果解释为来源分布变化下的泛化，不把差异全归因于 ASR 架构。

“评分标准与系统无关”是我们的目标定义。模型仍可能因训练中见到的错误形式、长度、内容分布不同而出现迁移差距。这个 distinction 可以直接回应 TA 的意见。

### D. 为什么不直接用 BERT embedding？

计划加入预训练 Sentence-BERT（例如 all-MiniLM-L6-v2）。分别编码参考句与 single-error 句，计算余弦相似度，再仅在 dev 上把相似度标定成 1–5，测试时与 DistilBERT 比较。Encoder 保持冻结，标定层会使用 dev 标签，因此应准确称为“预训练 embedding + dev calibration”。

如果它与微调评分器效果接近，说明这种便宜方法已足够。如果微调更好，要看优势落在哪些内容上，例如否定、数字、局部具体信息变化。相似度是否能识别这些变化应交给实验回答。

### E. 大 teacher 是否过大？

现有大 teacher 用来生成训练标签。可以选一个较小的开源模型（计划里举例 Qwen3 4B/8B），在固定的人类测试名单上使用同一规则和输入。比较人类一致性、平均耗时和资源开销。

若要从多种小 teacher 中选最好者，模型与提示选择应在 pilot/dev 完成，再冻结后测 200 条。由 TA 帮忙确认课程范围内需要测试多少种小模型。

## 5. 现有工作的关系怎么说

SWER 已经按错误严重度加权 WER。LASER 已经使用 LLM rubric，并微调较小 Llama 3 从词对预测错误惩罚。因此我们应把已有思路交代清楚，把研究问题落在会议对话里的逐片段评估、隔离单个错误、以及没见过的识别系统上的泛化。

隔离单错误比完整 hypothesis 更可靠目前仍需消融实验验证。独立人工测试既用于检验评分器，也可以帮助定位哪些边界最容易分歧。

- SWER https://aclanthology.org/2024.findings-emnlp.776/
- LASER https://aclanthology.org/2025.emnlp-main.1257/

## 6. 明天希望 TA 帮忙定下来的三件事

1. 五级保留，并在 200 条上报告边界混淆与实例，是否足以回应 rubric 的主观性？需要补四级合并分析吗？
2. 三系统 All-3/leave-one-out、Sentence-BERT baseline、小 teacher 对照、独立 200 条人工评测，哪些是 final 最优先的项目？
3. 要声称“Semantic-WER 更符合人的理解”，是否需要额外给完整字幕句子打 meaning-preservation 分？我们计划的可选验证是 100–150 句，将 WER、embedding similarity 与片段聚合分数对比人工整体判断。

第三项验证聚合指标，与 200 条片段评分回答不同的问题。时间有限时请 TA 帮忙确定贡献与范围。

## 7. 可直接口头讲的英文开场

Our project evaluates how much individual recognition errors change meaning in meeting transcripts. We isolate one error at a time by applying it to the reference sentence, and use a five-level rubric to score the resulting meaning change. Since the checkpoint, we have added Parakeet as a third recognizer and completed the earlier two-system DistilBERT experiments with three random seeds. The mixed 10K model reaches a mean QWK of about 0.754 against teacher labels, but independent human validation is still pending. Following your feedback, our updated main experiment uses 9K errors from all three recognizers, plus three leave-one-recognizer-out runs at the same training size. We would especially like your advice on the severity boundaries and on which validation experiments to prioritize for the final report.

## 8. 核对范围与证据

- 最新远端 commit 为 b915869，2026-11-18 已 fetch。主工作区 src/train_severity.py 有本地训练修改，直接 pull 因冲突中止。最新版本在隔离 worktree `/tmp/asr-semwer-ta-20261118` 读取。
- Overleaf checkpoint.tex 已重读，其 Next steps 仍是双系统 5K 方案，保留 checkpoint 时点的内容。本准备稿另行说明后续变化。
- Delta 三任务 23899163、23899503、23899504 均 COMPLETED、ExitCode 0:0，耗时分别 12:31、14:01、11:22。
- 三种子汇总从 18 个实际 results.json 计算，标准差采用样本标准差。未以测试结果调整模型选择。
- 系统指标来自最新 `outputs/semwer_summary_test+test_extra.json`。
- 200 条完成情况仅核实到 git 内 human_test_A.xlsx/B.xlsx 的 severity 均为空，用户在浏览器或别处的未导出标注无法据此判断。
- 本次仅整理与核查，三系统新实验尚未在该 Delta 工作目录部署运行。
