# 采用形态 A（两个独立子工程并列），暂不上统一编排器

> **Status:** Partially-superseded-by 0016/0022 —— 「两子工程并列 + 双语言裂缝物理约束」核心结论仍成立；「不设统一编排入口 / 两套 runner 各自加载」操作立场已被 v1.0 反转（详见下文「演进」）。

monorepo（单个 git 仓库根）下并列两个引擎子工程：`engines/novaact/`（Python）+ `engines/midscene/`（TS），根级放共享的 `features/`；可丢弃的 spike 分置各引擎子工程内（`engines/*/spikes/`）。两套 Gherkin runner（`pytest-bdd` / `cucumber-js`）各自加载根级 `.feature`、各出报告。**不**设统一编排入口。

**为什么不是「一个统一入口」（读者最可能问的）**：两个引擎的 SDK 语言不同且不可换——Nova Act 是 Python（pip `nova-act`），Midscene 是 TS（npm `@midscene/web`）。step definition 必须调引擎 API、因而必须跟着分语言；没有任何单一 Gherkin runner 能在同一进程里既跑 Python step 又跑 TS step（两个解释器/运行时）。这是「双语言裂缝」，物理约束，非设计选择。

> **演进（v1.0，「何时重议」已触发）**：下面「暂不上统一编排入口 / 两套 runner 各自加载各出报告」这一**操作性立场已被取代**——v1.0 引入根级窄腰核心 `core/`（自解析 `.feature`→分组 scope→调度）+ CLI 统一入口（[0016](./0016-execution-architecture-core-lib-run-model.md)），并退役两套 BDD runner、改核心自解析 + 薄 worker（[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)）。**但「两子工程并列 + 双语言裂缝物理约束」的核心结论仍成立**（core 只 spawn worker、不 import 引擎，裂缝仍在、只是被窄腰隔离）。下述原决策脉络保留。

**决定**：
- 工程形态 = 形态 A（两子工程并列），不是合成一个引擎、也不是单进程统一 runner。
- 暂不上形态 B 的统一编排器（Strands / 自写 orchestrator）。原型阶段它复杂度不对等、收益不明，且统一报告/编排取决于尚未验证的东西（断言哲学、链路是否全绿）。

**已知备用路径（存档，暂不走；2026-06 核实补充）**：将来若要消除裂缝（上形态 B），有非 Python 入口可探：
- **开源 pip 包 `nova-act`（本地 Playwright 浏览器自动化 SDK，`nova.act(...)`）确实是 Python-only**——这正是 Nova Act 引擎当前要用的执行能力。
- **但「Nova Act」还是一个托管 AWS REST 服务**（`endpointPrefix nova-act`、SigV4、apiVersion 2025-08-22），有官方多语言 SDK：TS/JS `@aws-sdk/client-nova-act`（scoped 名）、Go `aws-sdk-go-v2/service/novaact`、Java。理论上 TS 可驱动这个托管服务。
- **✅ 已实查证伪（2026-06，高置信，见 [0023](./0023-novaact-acting-python-locked-no-ts-core.md)）**：REST 服务（`InvokeActStep` 等）是「客户端驱动的工具调用循环」——服务端发 `browser.*` 指令、客户端自己执行；浏览器驱动胶水只有 Python SDK 有。Strands TS 也无 Nova Act 浏览器 tool。**结论 = NO-STILL-NEEDS-PYTHON**：acting 锁 Python，此备用路径关闭（除非自造 TS 客户端引擎，不值）。

**何时重议**：当团队需要「一键跑全部用例并看统一结果」成为硬需求时，再引入根级协调入口或形态 B 编排器，另立 ADR。
