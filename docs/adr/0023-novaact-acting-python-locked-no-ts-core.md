# Nova Act 的 acting 锁死在 Python：全 TS 核心被证伪，核心语言不为「对称」而赌

> **Status:** Accepted

为核心库（v1.0）选语言时，曾设想：若 Nova Act 也能用 TypeScript 驱动，则核心可全 TS、两个引擎在进程内对称（最工整的理想形态）。本 ADR 记录对这条路径的**实查证伪**，关闭它，免得后人重走。它直接闭合 [0006](./0006-form-a-two-subprojects-no-orchestrator.md) 与 [0013](./0013-cross-engine-sharing-boundary.md) 当年留下的「medium 置信、未验证」备用路径。

## 候选路径

`@aws-sdk/client-nova-act`（Nova Act 的官方 TS REST 客户端）+ Strands Agents（TS）—— 设想用它们在 TypeScript 里重建 `nova.act("自然语言")` 的**浏览器 acting** 能力，替代 Python-only 的 `nova-act` pip SDK。

## 实查结论（2026-06，AWS 官方 API 文档，文档发布日 2026-06-24；高置信）

**关键认知翻转——Nova Act 的 REST API 是「客户端驱动的工具调用循环」：服务端是大脑，客户端是手。**

- `InvokeActStep` **不是**服务端帮你操作浏览器。它返回一串 `calls`（`browser.{action}` / `tool.{name}`），即「模型想执行的下一步动作」；**真正的点击/输入要靠客户端自己执行**，再把 `CallResult` 回传。`CreateAct.status` 枚举里赫然有 `PENDING_CLIENT_ACTION`——据此状态机语义可推断服务端会**阻塞等客户端**把动作做完（推断，文档未直用 "block" 字样）。
- 自然语言指令在 `CreateAct` 的 `task` 字段（1–10000 字符）+ 客户端提供的 `toolSpecs`，**不在** `InvokeActStep`。
- 全部 16 个 REST operation **没有一个**是「启动浏览器/导航/截图/点击」；`CreateSession` 的 body 只有 `clientToken`，**完全没有浏览器/AgentCore 相关参数**。REST 服务自身根本不持有浏览器概念。
- **Python `nova-act` SDK 的真正价值，不是大脑（大脑在服务端、语言无关），而是它内置的那套 Playwright/CDP 客户端循环**——把服务端发的 `browser.*` 指令落到真实浏览器（含 AgentCore Browser）上。这套「手」的胶水，只有 Python SDK 有（仓库语言占比来自先前调查、本 ADR 未复验：约 98.6% Python，零 TS/JS）。
- **Strands Agents（TS）填不上这个洞**：TS SDK（`strands-agents/sdk-typescript`，已 archived，迁到 `harness-sdk`）只带 Notebook / File / HTTP 三个 tool，**没有 Nova Act 浏览器 tool**，也没有自然语言浏览器 acting 能力。它只做 LLM/工具编排。

## 裁决：`NO-STILL-NEEDS-PYTHON`（高置信）

- **要现成的 TS 等价物替代 Python acting → 不存在。** 没有任何一方提供 TS 版 `nova.act()`。
- **自己用 TS 重建那套客户端循环 → 理论可行，但 = 自造一个 TS 版 Nova Act 客户端引擎。** 要在 TS 里实现 `CreateAct(task,toolSpecs) → 循环 InvokeActStep → 把每个 browser.* 落到 TS Playwright/CDP → 回传 CallResult` 的整个循环。这正是本项目一路在砍的那种过度复杂度，且附带两个实锤风险：
  1. **`CallResultContent` 联合类型文档里只有 `text` 成员**，没有 image/screenshot。Nova Act 命门是「看截图+DOM 来操作」——若 REST 回传通道真只能回文本，视觉 grounding 会比 Python SDK 弱（中置信：文档没写≠一定没有，但是红灯）。
  2. `@aws-sdk/client-nova-act` 本 ADR 未独立核实成（npm 403、AWS v3 文档页空壳）；其存在记录于 [0006](./0006-form-a-two-subprojects-no-orchestrator.md)（含 `apiVersion 2025-08-22`、`endpointPrefix nova-act`），不是本 ADR 抓到的页面。

**为「两个引擎对称」这个美学收益，去赌一条未验证的 TS-acting 链路 + 自造引擎工作量 + 视觉降级风险——不值。**

## 由此定下的核心语言原则（落地见 [0016](./0016-execution-architecture-core-lib-run-model.md)）

两个引擎各自语言锁死（Midscene 锁 TS、Nova Act 锁 Python）是**物理约束**。无论核心用哪个语言，**必有一个引擎跨进程**——这是「双语言裂缝」（[0006](./0006-form-a-two-subprojects-no-orchestrator.md)）的必然。本可让另一个引擎进程内（核心挨着它），但此处决定**两个引擎都子进程**（见下），刻意消除这种不对称。

**决定：两个引擎都作为子进程 worker，核心不 import 任何引擎。** 这让「核心语言」从「必须挨着某个引擎」的被迫选择，变成**低风险的自由选择**（核心是无重型引擎依赖的薄编排层）。核心选 **Python**（boto3 生态成熟，便于未来云端 adapter；Gherkin 解析有官方 `gherkin-official`）。详见 [0016](./0016-execution-architecture-core-lib-run-model.md)。

## 重议

- 若 AWS 将来发布**官方 TS Nova Act acting SDK**（真能 `act("自然语言")` 驱动 AgentCore 浏览器），或 `CallResultContent` 明确支持图像回传、并有端到端 TS 配方——届时可重新评估「全 TS 核心」。在那之前，Nova Act acting 锁 Python 是既定事实，不据未验证链路下注。
