# 执行架构：核心库（窄腰）+ Run 数据模型 + 留好状态存储的口子

界定 v0.x/v1.0 起、并向云端无缝演进的执行架构。本 ADR 是多轮形态讨论的总成，约束 lib 的设计，确保本地与云端、CLI 与 WebUI 不埋返工雷。

## 分层：核心库是窄腰，CLI/WebUI 是可替换前端

```
  CLI(人/CI/skill)   WebUI 后端        ← 前端「皮」（薄）；都直接调核心，平级
        └──────┬──────┘
          执行核心库 core/（窄腰：解析 .feature → 分组 scope → 调度 → 收集结果；零引擎依赖）
                │  Engine port：runScope(scope) → JSON 结果
        ┌───────┴───────┐                ← 两个 adapter 形状一致，平级对标
   MidsceneEngine   NovaActEngine         spawn 各自语言的 worker 子进程，讲同一套 JSON 协议
   spawn Node worker  spawn Python worker
        │                 │
   AgentCore 会话A    AgentCore 会话B      ← 会话生命周期在 worker 内（已验证）
```

- **窄腰是「核心库」`core/`，不是 CLI**（早先措辞修正）。CLI 是核心的第一个、最薄的前端；WebUI 是另一个前端，**直接调核心、不 shell-out CLI**（后者才是"难集成"的错误做法）。
- CI / AI-skill 通过 CLI 这个皮间接用核心；都契合"调命令→等结果→看退出码"。
- **阻塞 vs 非阻塞是调用方的选择，不是核心的属性**：CLI 可轮询到完成（像阻塞）；WebUI 提交即返回 runId、之后轮询。同一核心两种皮都满足。

### 核心语言 & 两腿都子进程（见 [0023](./0023-novaact-acting-python-locked-no-ts-core.md)）

两个引擎各自语言锁死（Midscene 锁 TS、Nova Act acting 锁 Python，[0023](./0023-novaact-acting-python-locked-no-ts-core.md) 证伪了「全 TS 核心」），故**无论核心用哪个语言，必有一腿跨进程**——这是「双语言裂缝」（[0006](./0006-form-a-two-subprojects-no-orchestrator.md)）的必然。

**决定：两腿都作为子进程 worker，核心不 import 任何引擎；核心语言选 Python。**
- **两腿都子进程**（而非一腿进程内）：两个 `Engine` adapter 形状**完全一致**（spawn worker + 讲同一套 JSON 协议），核心不碰任一引擎 API，AgentCore 会话生命周期留在各自 worker（即现 `generic.steps.ts` Before/After、`nova_ctx` fixture 已跑通处）。这才是对称 `Engine` port 最干净的形态；一腿进程内会让 adapter 出现两种形状、核心 venv 被引擎依赖树绑死。
- **核心语言 = Python**：两腿都子进程后，核心是无重型引擎依赖的薄编排层，语言成为低风险自由选择；选 Python 因 boto3 生态成熟（便于未来云 adapter）+ 官方 `gherkin-official` 解析。
- **核心自解析 Gherkin + 薄 worker（B1）**：核心拥有解析（单一事实源），worker 只派发 step → act/assert，**退役 cucumber 补丁与 pytest-bdd 路由 hack**。详见 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)。

## 数据模型（现在钉死；耐久，决定 DDB 表 / WebUI / 报告）

| 概念 | 是什么 | 产出 |
|---|---|---|
| **Scenario** | Gherkin 单个 `Scenario:` | pass/fail、A/B 断言、抖动数据（投票）、原生报告引用 |
| **Feature**（`.feature`） | 含 1..N scenario | **组织轴**（正交，非执行单元） |
| **Scope**（session scope） | 共享操作上下文的 scenario 分组 | **执行单元**：scope 内串行、scope 间并行；语义层配置（用例的上下文依赖在此显式表达） |
| **Job** | 提交给执行面的单元 | **= Scope**（被 session-scope 语义强制：若 job=scenario，有依赖的 scenario 会被拆到不同 microVM 无法共享会话） |
| **Run** | 一次执行，封装多个 job | `runId`、总状态、起止、**RunResult**、**RunReport** |

- **RunResult** = 机器可读汇总判定（退出码 / CI / WebUI 状态）。**已实现**：`core/model.py` 的 `RunResult`（status 三态 + 各 job 结果 + `total_cost_usd` 跨 scope 成本汇总）。
- **RunReport** = 人看的归集报告（把两腿割裂的 Midscene html / Nova trajectory 归到一处）。**这是原 M5「报告统一」的归宿**——**v1.0 当前未实现（deferred）**：决定「先散着」（见下「版本切分」），等输出/消费要求清晰再定形态。

**已定 = 概念/层级（上表）+ 协议层字段（[0024](./0024-worker-core-protocol.md)）**：每 scenario 判定（status 三态）、抖动投票 tally、规范化 errorType、cost 信封、报告产物指针（reportRefs）等 **scenario/scope 级字段已由 worker↔core 协议钉死**——它们是 RunResult/RunReport 的字段来源。**仍未定 = 持久化层 Run/Job 级字段**（runId / jobId(scopeId) / 会话血缘 sessionId / 起止时间 / DDB 表结构 / WebUI 读取面）：有意留到 v1.0 真实跑批逼出（"报告要展示什么、CI 要读什么"届时自然浮现），避免现在纸上列错。（原计划在 v0.x 逼出，但 v0.x 判「方向已证」未做真实用例验收，顺延 v1.0，见下「版本切分」。）

## 引擎选择 & 并发（已定）

- 用例可配"用哪条腿"（默认单腿），经 `@engine:` tag 选腿（ADR 0019）。**双腿交叉验证 v1.0 不做**（价值可疑、复杂度高，见 ADR 0019）；未来若需，在跑批层展开两次独立运行。
- 并发：**scope 内串行**（上下文依赖），**scope 间并行**（互相独立）。

## 留口子：Ports & Adapters（六边形架构），组合根注入

可替换的外部依赖不散落成 `runScope` 的一堆参数，而是收成一个 **ports 层**（类比 DAO 层）：导出稳定接口，核心只依赖接口、不知实现是谁。

**按关注点拆成独立 port（不揉成上帝 module）**：
- `Engine` —— 真正跑一个 scope 的地方（早先名 `ExecutionBackend`，现**重命名为 `Engine`** 对齐 CONTEXT 「引擎」术语）。v1.0 的 adapter = `MidsceneEngine` / `NovaActEngine`，各 spawn 对应语言的 worker 子进程、讲同一套 JSON 协议（[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)）。两 adapter 形状一致。
- `RunStore` —— **控制面**：run/job 的状态、status、起止时间、会话血缘 sessionId（频繁读写：轮询/续跑/WebUI 进度）。**这才是未来 DynamoDB 真正要存的东西**（可恢复、可轮询）。
- `ResultStore` —— **数据面**：每 scenario 的 pass/fail、投票抖动、原生报告指针（追加为主；RunReport 归集与 CI 读判定靠它）。
- `ReportStore` —— 存归集报告产物（local FS → S3）。
- （其余按需，如凭证源；保持各自独立、生命周期不同）

> **`RunStore` 从原 `ResultStore` 拆出（对本 ADR 早先单一 `ResultStore` 的修正）**：控制面（状态/血缘，频繁读写、撑轮询续跑）与数据面（结果落地，追加为主）访问模式与生命周期不同，拆成两个 port 更内聚——也让「DDB 存什么」清晰（DDB 主要服务 `RunStore`）。

**adapters 按 port 分子目录**（不按后端分）：

```
core/
├── ports.py                 ← 接口定义（Engine / RunStore / ResultStore / ReportStore）
└── adapters/
    ├── engine/{midscene.py, novaact.py}   ← spawn 各自 worker、讲协议
    ├── run_store/local.py                 ← 控制面；（未来 ddb.py）
    ├── result_store/local.py              ← 数据面；（未来对象存储）
    └── report_store/local.py              ← 归集报告；（未来 s3.py）
```

**选实现 = 组合根注入，不是 module 自选**（关键，避开本会话踩过的坑）：
- 接口定义在 `ports`；**具体 adapter 由调用方（CLI 的 main / WebUI 的 bootstrap = 组合根）在启动时注入**给核心。核心只认接口。
- **禁止** ports module 内部用全局单例 + `env`-sniff 自选实现——那正是本项目踩过的 Midscene `GlobalConfigManager` 反模式（import 时缓存 env、运行时改不动、难测）。注入式可测、无隐藏全局。

**rule-of-three 克制**：接口现在定（廉价，还逼清边界），但**只写 local adapter**；DDB/S3/Fargate adapter 等云端真需要时再填。

这样无状态化、上云、WebUI 接入都成了"加 adapter + 组合根换注入"，核心与接口不动。

## 工程布局：core / cli / engines 三者平级对标

下为**目标态**。**当前实装态（v1.0 进行中）**标在各行右侧 ✅/⬜：core/ 已建；engines/ 迁移与 cli/ 待接 Midscene 那轮做，现 Nova worker 在顶层 `novaact/worker/`、组合根用 `core/run_e2e.py`（CLI 雏形）。

```
yaozhou/
├── core/                ← 窄腰：纯编排，零引擎依赖                          ✅ 已建
│   ├── model.py · parse.py · scope.py · schedule.py · wire.py · ports.py    ✅（协议序列化文件名是 wire.py）
│   ├── adapters/        ← 按 port 分；现有 subprocess_engine.py（单 adapter 参数化，非 midscene.py/novaact.py 两文件）✅
│   └── run_e2e.py       ← 组合根 / CLI 雏形                                ✅（暂代下方 cli/main.py）
├── cli/                 ← 最薄前端 = 组合根（在此 new 出具体 adapter 注入给 core）  ⬜ 待建（现由 core/run_e2e.py 暂代）
│   └── main.py
└── engines/             ← 两个可插拔引擎，与 core 平级对标                  ⬜ 待迁移（现 midscene/、novaact/ 仍在顶层）
    ├── midscene/        ← 整个 TS 子工程                                  ⬜ 未接 worker（Midscene 腿下一轮）
    │   └── lib/agentcore-sigv4.mts
    └── novaact/         ← 整个 Python 子工程                              ✅ worker 已落地（现位于顶层 novaact/worker/run_scope.py）
        ├── worker/run_scope.py                                          ✅（确定性注册表/ai_steps 拆分留口子，见 0022）
        └── lib/workflow_setup.py
```

- **`engines/{midscene,novaact}` 提升为与 `core/` 平级**（不再各藏一个 `worker/` 子目录）：引擎子工程必须连同其依赖环境（`node_modules`+`agentcore-sigv4.mts` / `.venv`+`workflow_setup.py`）整体存在，故**整体**移到 `engines/` 下，既对称又不把代码与依赖环境拆开。
- **目录名用 `engine` 而非 `worker`**：对齐 CONTEXT 「引擎」与 `Engine` port；worker 是运行时角色（被 spawn 的进程），engine 是领域概念——`engines/midscene/` 内**含**一个 worker 入口。
- **窄腰目录名 `core`、不叫 `lib`**：`lib` 已被各引擎子级占用（`midscene/lib`、`novaact/lib` 放引擎内共享模块），复用会混淆。散文里称「核心库 / core 包」无妨（它确是 cli/未来 WebUI 依赖的可导入库），但**目录**是 `core`。

## 版本切分（按完成线，非时间；版本号用 SemVer）

> 版本号语义：`0.x` = 内部验证、API 不稳；`1.0.0` = 团队日常可用的第一个稳定承诺；云端化是**非破坏增量**（加 adapter、核心 API 不动），故为 minor bump `1.1.0` 而非 major——这本身印证了「留口子」设计对。

- **spike — ✅ 已完成**：技术链路全通，由 `spike-validated` tag 封存。
- **v0.1.0（核心假设验证）— ✅ 方向已证，正式验收顺延 v1.0.0（见下决定）**：糙、小范围、本地执行。
  - **核心假设（可证伪）**：QA **只写 `.feature`、零 step 代码**，靠通用 step（`When {自然语言} → aiAct`）即可跑通用例。
  - **原验收标准**：≥3 个**真实业务用例**（含不同动作类型）全部 QA 零 step 代码跑通；每处破例写代码记为反证；破例过多 → 假设不成立。
  - **实际达成**：用**骨架用例**（wikipedia / example.com，见 CONTEXT「骨架验证用例」）覆盖了单步/多步复合/开放动作/AI 布尔·否定·取数·取串断言/主观判定/tag 路由，**全程 QA 零代码**，两腿都跑通——可行性**方向已证**。
  - **决定（边界，务必读）**：**v0.1.0 判「方向已证」，不补真实用例即进 v1.0.0**。理由——① 团队当前**拿不到真实业务用例**（站点登录态等不可得），强等是空等；② 没有真实用例 → 破例无从触发 → **「破例清单」这条验收无法在 v0.x 执行**。故把「真实业务用例验收 + 破例记录」**顺延并入 v1.0.0**：待有真实用例时在 v1.0 里跑出破例、据以校验「QA 零代码」承诺。**已知风险**：v1.0 架构基于「骨架用例都很顺」的乐观假设设计，真实用例的破例（登录 / HITL / 动态内容 flaky）可能反过来要求调整 v1.0 架构——接受此返工风险，因前置条件（真实用例）确实不具备。
  - **报告**：v0.x 原目标含「报告能看」。**决定先「散着」**——两腿原生产物（Midscene html / Nova trajectory，落点见 CONTEXT「报告产物模型」）暂不归集，手动查目录够用。RunReport 归集形态**等输出/消费要求（报告要展示什么、CI/WebUI 要读什么）清晰后再定**，与「字段级 schema 留到真实跑批逼出」同一克制。
- **v1.0.0（团队 QA 日常可用）— ⏳ 架构设计中（本 ADR + 0022/0023）**：多用例组织、跑批入口（CLI 阻塞跑一批）、scope 调度、抖动治理（投票）落地；本地执行。**承接 v0.x 顺延项**：真实业务用例验收 + 破例清单、RunReport 归集（待输出要求清晰）。
- **v1.1.0（云端执行）— ⬜ 留口子不实现**：CLI 提交 → Fargate 跑 → 轮询收集，**job = scope** 粒度（上云时坐实，见 [0017](./0017-cloud-execution-fargate-over-runtime.md)）；外置状态存储（DDB，主要服务 `RunStore`）+ 无状态核心。**= 加 adapter + 组合根换注入，核心不动**（「留口子不实现」= 接口现在定、实现等真需要时填）。
- **v2.0.0（规模化）— ⬜ 留口子不实现**：WebUI 前端（直接调核心）。

## G1/G2 解析前置（声明语法已定，调度实现待 v1.0）

G1/G2 是 v1.0 核心库 `.feature` 解析的前置——其声明语法**现已定（ADR 0019）**：

- **G1 — session scope 声明**：✅ `@scope:<name>` tag（相同值同 scope、串行共享会话；不同值并行；未标各自独立）。tag 两腿可读已验证。
- **G2 — 引擎选择**：✅ `@engine:<x>` tag 选腿（scope 级属性、容错缺省、冲突报错）；v1.0 只选腿不交叉。两腿路由已验证。
- 声明语法已定，但**调度实现**（scope 串/并行、会话共享、冲突校验）仍待 v1.0 核心库。

## 现在做 / 现在不做

- **现在做（v1.0）**：核心库 `core/` 可被调用（逻辑不焊死在 CLI main 里）；钉死上面数据模型；定义 ports 接口（`Engine`/`RunStore`/`ResultStore`/`ReportStore`）+ 组合根注入；核心自解析 Gherkin + 薄 worker（[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)）。模块设计：worker↔core 协议见 [0024](./0024-worker-core-protocol.md)；plan 模块见 [0025](./0025-plan-module-feature-to-jobs.md)；schedule 模块见 [0026](./0026-schedule-module.md)。
  - **ports 落地状态（v1.0 当前）**：`Engine` port 的 local adapter **已建**（`core/adapters/subprocess_engine.py`，子进程起 worker）；`RunStore`/`ResultStore`/`ReportStore` **仅定义了接口 Protocol、local adapter 尚未建**（结果现仅在内存 `RunResult`，未持久化）——待真实跑批逼出字段后填（与上「数据模型」节的字段级 schema 顺延一致）。Nova 腿 worker 已落地；Midscene 腿 worker 待下一轮。
- **现在不做**：DynamoDB / S3 / Fargate adapter / 无状态机制 / WebUI ——接口已留好，等云端真需要时填 adapter + 组合根换注入。**避免为想象中的云端预先盖机器。**
- **G1/G2 声明语法已定**（ADR 0019）；其**调度实现**（scope 串/并行、会话共享、engine 冲突校验）由 v1.0 核心库落地。
- **多用例组织**（feature 分目录/命名约定、跑批入口、跑批层选择 feature/tag）同样由 v1.0 核心库落地——它依赖核心库的调度层，在 bdd 直跑层做是临时的、核心库会重做。当前 `features/` 下多个文件仅是 v0.x 打磨产物，未做有意组织。（旧的 cucumber `--tags` 选子集约定随 BDD runner 一并退役，见 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)；选子集改由核心调度层据 tag 实现。）
