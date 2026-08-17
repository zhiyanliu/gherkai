# 框架范围限定为英文 UI

> **Status:** Accepted —— 范围限定有效；两引擎在非英文 UI 上的实际表现已实测（见「非英文的真实边界」），据此定了扩范围路径。

被测系统的 UI 假定为**纯英文**。这是一条**支持范围与证据边界**的假设——不是"非英文跑不起来"的技术断言（两引擎实际都能处理中文，见下）。

## 为什么限定（按证据强度排）

1. **支持契约风险（最硬）**：AWS 对 Nova Act 的语言声明只有一句「Nova Act supports English.」（GitHub repo README 的 *Pre-requisites* 节，与 OS/Python 版本并列）。非英文因此**落在 AWS 声明的支持范围之外**：模型迭代若在非英文上退化，我们没有立场主张 AWS 有义务修。这是产品承诺层的风险，与"当前能不能跑"无关。
2. **可靠性证据只覆盖英文**：[0010](./0010-spike-as-apples-to-apples-benchmark.md)/[0014](./0014-ai-first-assertions.md) 的抖动量化（两引擎各 10 次零抖动）用英文 prompt 测得；非英文无 N 次抖动数据，而单次中文实测已见 Nova 侧判定不一致（见下）。**功能性可跑 ≠ 同等可靠**（[CLAUDE.md](../../CLAUDE.md)「绿≠对」的分流判据）。
3. **AI 断言的语义面更宽**：`Then` 走 AI 判定（[0014](./0014-ai-first-assertions.md)/[0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md)），断言文本与页面文本的语言组合会放大抖动面。限定英文把这条不确定性挡在范围外。

## 非英文的真实边界（实测与官方声明的精确形态）

**官方声明的边界**：Nova Act 那句是**无 "only"、无宾语**的肯定式支持声明——未界定管的是 `act()` 指令语言还是被测 UI 语言，且**不在** README 的 *Known limitations* 节（该节列的是：不能操作非浏览器应用、不能操作浏览器窗口/模态框、屏幕分辨率范围）。逐个核对 AWS User Guide 全部页面、AI Service Card、repo FAQ、boto3 API reference、产品页：**零处**语言约束，API 无 language/locale 参数；SDK 源码无 `English` 字样、`act()` 无语言校验、浏览器 context 不设 locale/Accept-Language（不强制英文环境）。对照旁证：同族 Canvas/Reel 明写 "Supported Languages: English"、Sonic 列举五种语言——**AWS 要约束语言时会发正式语言表，Nova Act 没有**。故「supports English」应读作"声明/测试/支持的范围"，非"非英文会被拒绝"。

**视觉定位的语言弱项属大脑、不属框架**：Midscene 官方把「非拉丁文字/小字定位偏弱」列为 **GPT-5 系的 per-model 注意事项**（原文 "GPT-5 may still struggle with non-Latin text and with text that is too small in the image."），Qwen 各行无此警告——与 [0002](./0002-midscene-not-driven-by-gpt55.md) 排除 GPT-5.5 的理由同源。故换大脑即换该弱项（[0003](./0003-midscene-grounding-qwen3vl-bedrock.md) 现用 Qwen3-VL）。

**中文 UI 实测**（纯中文页面 + 中文 step，经隧道打本机应用，[0035](./0035-local-app-testing-via-tunnel.md)）：

| 引擎 | 结果 |
|---|---|
| Midscene（Qwen3-VL） | 三步全过——中文按钮视觉定位 + 中文文本断言均成立 |
| Nova Act | 动作成功、布尔断言失败 |

Nova 的失败形态**不是读不出中文**：动作步的推理明确读出「提交订单」「取消」两个中文按钮并区分、还主动确认结果文本「订单提交成功」已显示；紧接着的 `act_get` 布尔断言在同一页面却判定"看不到该文本"→ false。即**中文理解够用，短板在独立 act 调用间的观察一致性**（动作路径与断言路径的观察时机不同）。另见形近字错读（「格希凯」读成「格希列」）。

结论：两引擎都不存在"非英文不可用"的硬墙；短板集中在 **Nova 侧的判定稳定性** 与 **非英文缺抖动量化** 这一证据缺口。

## 扩到非英文 UI 的路径（不需重设计架构）

1. 非英文用例做 N 次抖动测量（对齐 [0010](./0010-spike-as-apples-to-apples-benchmark.md)/[0014](./0014-ai-first-assertions.md) 的英文基线），量化两引擎差距；
2. 若 Nova 的 `act_get` 布尔断言在非英文上系统性不稳：先提高 `--assertion-votes`（[0014](./0014-ai-first-assertions.md) 的抖动治理本为此设计），再考虑对该引擎缩小断言职责；
3. 视觉定位成为瓶颈时换大脑——**不需重设计架构**，但也不是纯配置：改 worker 侧模型常量（`agentcore-sigv4.mts` 的 `MODEL` + family 开关）＋改 IaC 里 `bedrock:InvokeModel` 的模型 ARN pin 并重新部署（[0003](./0003-midscene-grounding-qwen3vl-bedrock.md)「待观察（上游代际）」段同口径），受 [0009](./0009-maximize-aws-hard-constraint.md)「AWS 内托管」约束限于 Bedrock 可用模型。

届时**修订本 ADR**（补范围与证据），无需另立取代 ADR。
