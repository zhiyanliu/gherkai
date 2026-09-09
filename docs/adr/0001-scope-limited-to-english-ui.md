# UI 语言支持范围：按引擎划分（Midscene 不限；Nova Act 限英文）

> **Status:** Accepted（2026-09-09 修订：范围从「框架限英文 UI」改为按引擎划分——Midscene 不限 UI 语言，Nova Act 的支持范围仍是英文 UI；据中文维基 5 次真跑、两引擎各 130 票的量化结果，见「非英文的真实边界」）。

## 决策

- **Midscene 引擎不限被测 UI 语言**。中文 UI 上动作与 AI 断言的可靠性已量化到与英文基线同级（[0010](./0010-spike-as-apples-to-apples-benchmark.md)/[0014](./0014-ai-first-assertions.md) 的英文基线 = AI 断言 ×10 零抖动；中文见下表）。
- **Nova Act 引擎的支持范围 = 英文 UI**。非英文 UI 上它的动作与页面级语义断言可用，但**正文中的词语包含类断言系统性判否**（下表 0/45），且 AWS 的语言声明只覆盖英文。
- **非英文应用的路由建议**：`@engine:midscene`（[0019](./0019-feature-tags-scope-and-engine.md) 的 tag 路由）；若必须用 Nova Act，断言只写页面级语义（「当前是 X 的词条页」），文本包含类检查改走确定性 step（[0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md)/[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)）。
- 这是**支持范围与证据边界**的划分，不是「非英文跑不起来」的技术断言——两引擎在中文页面上都能导航、能读中文按钮与标题（见下）。

## 为什么这样划（按证据强度排）

1. **支持契约（Nova Act 独有，最硬）**：AWS 对 Nova Act 的语言声明只有一句「Note: Nova Act supports English.」（GitHub repo README 的 *Pre-requisites* 节，与 OS/Python 版本并列；2026-09-09 复核措辞未变）。非英文落在 AWS 声明的支持范围之外：模型迭代若在非英文上退化，我们没有立场主张 AWS 有义务修。Midscene 的大脑是 Bedrock 上的 Qwen3-VL（[0003](./0003-midscene-grounding-qwen3vl-bedrock.md)），多语种模型、无此声明。
2. **实测（两引擎都有）**：Midscene 在中文 UI 上 125 票一致且正确；Nova Act 的中文词语包含类断言 0/45 系统性假阴性。**功能性可跑 ≠ 同等可靠**（[CLAUDE.md](../../CLAUDE.md)「绿≠对」的分流判据）——Nova 的中文动作能跑，断言不可靠。
3. **AI 断言的语义面**：`Then` 走 AI 判定（[0014](./0014-ai-first-assertions.md)/[0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md)），断言文本与页面文本的语言组合会放大抖动面。中文实测显示这条对 Midscene 的直白断言不成立（零抖动），只在刻意刁难的边缘题上出现（见下「边缘题」）。

## 非英文的真实边界（实测与官方声明的精确形态）

**官方声明的边界**：Nova Act 那句是**无 "only"、无宾语**的肯定式支持声明——未界定管的是 `act()` 指令语言还是被测 UI 语言，且**不在** README 的 *Known limitations* 节（该节列的是：不能操作非浏览器应用、不能操作浏览器窗口/模态框、屏幕分辨率范围）。逐个核对 AWS User Guide 全部页面、AI Service Card、repo FAQ、boto3 API reference、产品页：**零处**语言约束，API 无 language/locale 参数；SDK 源码无 `English` 字样、`act()` 无语言校验、浏览器 context 不设 locale/Accept-Language（不强制英文环境）。对照旁证：同族 Canvas/Reel 明写 "Supported Languages: English"、Sonic 列举五种语言——**AWS 要约束语言时会发正式语言表，Nova Act 没有**。故「supports English」应读作"声明/测试/支持的范围"，非"非英文会被拒绝"。

**视觉定位的语言弱项属大脑、不属框架**：Midscene 官方把「非拉丁文字/小字定位偏弱」列为 **GPT-5 系的 per-model 注意事项**（原文 "GPT-5 may still struggle with non-Latin text and with text that is too small in the image."），Qwen 各行无此警告——与 [0002](./0002-midscene-not-driven-by-gpt55.md) 排除 GPT-5.5 的理由同源。故换大脑即换该弱项（[0003](./0003-midscene-grounding-qwen3vl-bedrock.md) 现用 Qwen3-VL）。

**中文 UI 首次实测**（纯中文页面 + 中文 step，经隧道打本机应用，[0035](./0035-local-app-testing-via-tunnel.md)）：

| 引擎 | 结果 |
|---|---|
| Midscene（Qwen3-VL） | 三步全过——中文按钮视觉定位 + 中文文本断言均成立 |
| Nova Act | 动作成功、布尔断言失败 |

Nova 的失败形态**不是读不出中文**：动作步的推理明确读出「提交订单」「取消」两个中文按钮并区分、还主动确认结果文本「订单提交成功」已显示；紧接着的 `act_get` 布尔断言在同一页面却判定"看不到该文本"→ false。另见形近字错读（「格希凯」读成「格希列」）。

**中文 UI 量化实测**（2026-09-09，cloud 档、v1.4.0 基底镜像；夹具 = `features/wikipedia_zh.feature`：zh.wikipedia.org 首页 → 中文搜索「人工智能」→ 三条中文 AI 断言，两引擎步骤完全相同；`--assertion-votes 10`、独立跑 3 次）：

| 断言（页面事实） | Midscene | Nova Act |
|---|---|---|
| 「页面没有出现服务器错误」（真） | 10/10 ×3 | 10/10 ×3 |
| 中文搜索动作「在搜索框输入 人工智能 并提交搜索」 | 3/3 成功 | 3/3 成功 |
| 「当前页面是关于人工智能的维基百科词条页」（真） | 10/10 ×3 | 10/10 ×3 |
| 「词条首段提到了计算机或机器」（真：首段含「计算机」） | 10/10 ×3 | **0/10 ×3** |

诊断（同页直开词条、各 5 票、两引擎同题）把 Nova 的失败形态拆开：

| 断言 | 页面事实 | Midscene | Nova Act |
|---|---|---|---|
| 「词条首段提到了计算机」 | 真（第一段） | 5/5 | **0/5** |
| 「词条首段提到了智慧」 | 真（第一段） | 5/5 | **0/5** |
| 「词条首段提到了机器」 | 第一段无、第二段「聊天机器人」 | 5/5（按导语整段读） | 0/5 |
| 「词条首段提到了火星」 | 假 | 0/5（真阴性） | 0/5（真阴性） |
| 「词条首段包含英文 artificial intelligence」 | 真 | 5/5 | 5/5 |
| 「词条首段给出了 artificial intelligence 的缩写 AI」 | 真 | 5/5 | 5/5 |
| 「词条第一段（不含后续段落）提到了机器」（边缘题） | 假 | **3/5**（抖动） | 0/5 |

结论：

- **Nova Act**：中文动作、中文页面级语义断言、真阴性、英文词包含都对；**凡「正文里是否出现某个中文词」一律判否**（0/45），词就在第一段、还是超链接高亮也判不到。短板精确到「中文词语级文本匹配」，不是语言理解、不是抖动（30/30 一致）。这与首次实测「读得出中文按钮、断言却判否」同形态。
- **Midscene**：直白的中文断言 125 票一致且正确（含真阴性）；「首段」被按导语整段解读是合理歧义。**边缘题**（段落范围排除 + 子串语义）出现 3/5 抖动——这是断言措辞问题、与语言无关：feature 作者写直白的语义陈述即可，别把段落边界与子串规则塞进 AI 断言（那是确定性 step 的活）。
- 两引擎都不存在"非英文不可用"的硬墙；差别在断言可靠性，且 Nova 的差别是系统性的，投票治不了（[0014](./0014-ai-first-assertions.md) 的投票只压随机抖动）。

## Nova Act 解除英文限定的条件（重议闸门）

- AWS 语言声明变更（发正式语言表含目标语言），**或** 模型迭代后用 `features/wikipedia_zh.feature` 以 `--assertion-votes 10` 独立跑 3 次，「词条首段提到了计算机或机器」≥ 9/10 且三次一致——两者任一成立即修订本 ADR，无需另立取代 ADR。
- 视觉定位成为瓶颈时换大脑——**不需重设计架构**，但也不是纯配置：改 worker 侧模型常量（`agentcore-sigv4.mts` 的 `MODEL` + family 开关）＋改 IaC 里 `bedrock:InvokeModel` 的模型 ARN pin 并重新部署（[0003](./0003-midscene-grounding-qwen3vl-bedrock.md)「待观察（上游代际）」段同口径），受 [0009](./0009-maximize-aws-hard-constraint.md)「AWS 内托管」约束限于 Bedrock 可用模型。

## 影响

- README 架构速览的范围句与「怎么写 `.feature`」节按引擎写语言支持与路由建议；两个引擎包的 README 各带一句语言支持说明（使用者向、不带本 ADR 编号）。
- CONTEXT.md「骨架验证用例」词条：选站标准去掉「英文」，英文与中文探针各一组。
- `features/wikipedia_zh.feature` 是本 ADR 的测量夹具与重议闸门的复测入口，与英文探针同构、不进日常 QA 流。
