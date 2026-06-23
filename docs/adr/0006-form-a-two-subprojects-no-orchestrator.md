# 采用形态 A（两个独立子工程并列），暂不上统一编排器

monorepo（git 根在 `yaozhou/`）下并列两个引擎子工程：`novaact/`（Python）+ `midscene/`（TS），根级放共享的 `features/` 与可丢弃的 `spikes/`。两套 Gherkin runner（`pytest-bdd` / `cucumber-js`）各自加载根级 `.feature`、各出报告。**不**设统一编排入口。

**为什么不是「一个统一入口」（读者最可能问的）**：两个引擎的 SDK 语言不同且不可换——Nova Act 是 Python（pip `nova-act`），Midscene 是 TS（npm `@midscene/web`）。step definition 必须调引擎 API、因而必须跟着分语言；没有任何单一 Gherkin runner 能在同一进程里既跑 Python step 又跑 TS step（两个解释器/运行时）。这是「双语言裂缝」，物理约束，非设计选择。

**决定**：
- 工程形态 = 形态 A（两子工程并列），不是合成一个引擎、也不是单进程统一 runner。
- 暂不上形态 B 的统一编排器（Strands / 自写 orchestrator）。原型阶段它复杂度不对等、收益不明，且统一报告/编排取决于尚未验证的东西（断言哲学、链路是否全绿）。

**已知备用路径（存档，暂不走；2026-06 核实补充）**：将来若要消除裂缝（上形态 B），有非 Python 入口可探：
- **开源 pip 包 `nova-act`（本地 Playwright 浏览器自动化 SDK，`nova.act(...)`）确实是 Python-only**——这正是 Nova Act 腿当前要用的执行能力。
- **但「Nova Act」还是一个托管 AWS REST 服务**（`endpointPrefix nova-act`、SigV4、apiVersion 2025-08-22），有官方多语言 SDK：TS/JS `@aws-sdk/client-nova-act`（scoped 名）、Go `aws-sdk-go-v2/service/novaact`、Java。理论上 TS 可驱动这个托管服务。
- ⚠️ **重要不确定性（核实置信度 medium）**：该 REST 服务的能力是否等同于本地 SDK 的 `nova.act()` 自然语言浏览器自动化，**未验证**——很可能是不同抽象层。不要据此认为「TS 能直接平替 Python 版 Nova Act 引擎」。`strands-agents` 已作为依赖在工程内（另一条 MCP/Strands 路径，亦未独立验证）。

**何时重议**：当团队需要「一键跑全部用例并看统一结果」成为硬需求时，再引入根级协调入口或形态 B 编排器，另立 ADR。
