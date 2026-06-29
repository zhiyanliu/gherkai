# 执行架构：核心库（窄腰）+ Run 数据模型 + 留好状态存储的口子

界定 v0.x/v1.0 起、并向云端无缝演进的执行架构。本 ADR 是多轮形态讨论的总成，约束 lib 的设计，确保本地与云端、CLI 与 WebUI 不埋返工雷。

## 分层：核心库是窄腰，CLI/WebUI 是可替换前端

```
  CLI(人/CI/skill)   WebUI 后端        ← 前端「皮」（薄）；都直接调核心，平级
        └──────┬──────┘
          执行核心库 core/（窄腰：解析 .feature → 分组 scope → 调度 → 收集结果；零引擎依赖）
                │  Engine port：run_scope(job) → 0024 事件流
        ┌───────┴───────┐                ← 同一个 SubprocessEngine，两腿只是 cmd 不同（形状本就一致）
   spawn Node worker  spawn Python worker   按 job.engine 经 EngineResolver 选 cmd，讲同一套 0024 协议
   (midscene 腿)       (novaact 腿)
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
| **Step** | scenario 内单步 | pass/fail/error、投票 tally、墙钟时长（`StepResult`，core 首次保留 step 级粒度） |
| **Scenario** | Gherkin 单个 `Scenario:` | pass/fail、A/B 断言、抖动数据（投票）、原生报告引用、墙钟时长 |
| **Feature**（`.feature`） | 含 1..N scenario | **组织轴**（正交，非执行单元） |
| **Scope**（session scope） | 共享操作上下文的 scenario 分组 | **执行单元**：scope 内串行、scope 间并行；产出原生量成本合计 + 墙钟时长 |
| **Job** | 提交给执行面的单元 | **= Scope**（被 session-scope 语义强制：若 job=scenario，有依赖的 scenario 会被拆到不同 microVM 无法共享会话） |
| **Run** | 一次执行，封装多个 job | `runId`、总状态、起止、墙钟时长、**RunResult**、**RunReport** |

- **RunResult** = 机器可读汇总判定（退出码 / CI / WebUI 状态）= **definition（`run_meta`）+ 判定（`jobs`）的显式合成**（见下「三层切分」）。**已实现**：`core/model.py` 的 `RunResult`（`run_meta: RunMeta` + status 三态 + 各 job 结果 + `total_tokens`/`total_time_worked_s` 两个原生量各自跨 scope 合计 + `duration_ms` 总墙钟时长；`run_id` 经 property delegate 给 `run_meta`）。其下 `JobResult`（**持有它的 `Job`(definition)**，scope_id/scope_name/engine 经 property 取，不再重复抄存）→ `ScenarioResult` → `StepResult` 三层结果（core 保留 step 级粒度），各级带 `duration_ms` 墙钟时长（性能指标，与成本的 `time_worked_s` 正交，见 [0024](./0024-worker-core-protocol.md)）。
- **RunReport** = 人看的归集报告（把两腿割裂的 Midscene html / Nova trajectory 归到一处）。**这是原 M5「报告统一」的归宿**——**v1.0 已实现（[0027](./0027-runreport-aggregation-index.md)）**：定为**跨腿归集索引**（`manifest.json` 机器可读 + `index.html` 人可导航入口），**只索引/链接原生产物、不解析融合其内容**；新引擎报任意 `kind` 零改 core。由 `ReportStore` 从 `RunResult` 一次归集（cli 每次 run **默认生成**，`--no-report` 跳过）。

### 三层切分：definition / 控制面运行态 / 数据面判定（数据流向不从结果反推）

一次 run 的数据按**何时产生、谁拥有**切成三层，对应三种类型与三个 store：

| 层 | 内容 | 何时 | 类型 | store |
|---|---|---|---|---|
| **definition（前置身份）** | run_id + created_at + 跑哪些 job（完整 `Job`：scope/engine/scenarios/steps，"要跑什么"） | **执行前**确定（plan 产出 + 组合根生成 run_id） | `RunMeta`（持有 `tuple[Job,...]`，不另造 JobMeta） | `RunStore`（控制面） |
| **控制面运行态** | 总 status / 各 job status / 会话血缘 sessionId / 起止 | **执行后**产生 | `RunState`（+ `JobState`） | `RunStore`（控制面） |
| **数据面判定明细** | 每 scenario/step 的 pass-fail、投票、cost、报告指针 | **执行后**产生 | `JobResult`→`ScenarioResult`→`StepResult` | `ResultStore`（数据面，判定真值唯一权威） |

- **数据流向单向、不从结果反推**：`features → plan → Job[] → 组合根生成 run_id → RunMeta → schedule(run_meta) → RunResult`。`RunMeta`（definition）是 schedule 的**输入**、不是从 `RunResult` 反抽——run 的身份执行前就定了。`schedule` 把 `run_meta` 原样放进 `RunResult`（合成），并归约出判定。`RunState` 由 `run_state_from_result(result)` 投影（投影**运行态**字段 status/session_id，非反推 definition 身份——scope_id 取自 `jr.job`，本就在 definition 里）。
- **`RunResult` = `RunMeta` + 判定的显式合成**：`JobResult` **持有 `Job`**（definition）而非重复抄它的 scope_id/scope_name/engine——消除「抄字段抄漏」（旧版抄了 engine 漏了 scope_name），存储唯一、读法经 property 稳定。
- **status 不进 `RunMeta`**：status 是判定派生（执行后），属控制面运行态/数据面，不是 definition。
- **「执行中实时更新状态」靠 sink 消费 event，不靠 schedule 持有 store**（ADR 0026「sink 与 RunResult 是同一事件流的两个视图」）：schedule 保持纯归约、不依赖任何 store；要实时进度的消费者（WebUI）挂一个消费 0024 事件、写状态的 sink 即可——本地/云端同机制，与部署无关。本轮不写该 status-sink（本地同步 cli 无轮询消费者），机制（sink）已在、零阻碍。

**已定 = 概念/层级（上表 + 三层切分）+ 协议层字段（[0024](./0024-worker-core-protocol.md)）**：每 scenario 判定（status 三态）、抖动投票 tally、规范化 errorType、cost 信封、报告产物指针（reportRefs）等 **scenario/scope 级字段已由 worker↔core 协议钉死**——它们是 RunResult/RunReport 的字段来源。**仍未定 = 持久化层 Run/Job 级字段**（runId / jobId(scopeId) / 会话血缘 sessionId / 起止时间 / DDB 表结构 / WebUI 读取面）：有意留到 v1.0 真实跑批逼出（"报告要展示什么、CI 要读什么"届时自然浮现），避免现在纸上列错。（原计划在 v0.x 逼出，但 v0.x 判「方向已证」未做真实用例验收，顺延 v1.0，见下「版本切分」。）

## 引擎选择 & 并发（已定）

- 用例可配"用哪条腿"（默认单腿），经 `@engine:` tag 选腿（ADR 0019）。**双腿交叉验证 v1.0 不做**（价值可疑、复杂度高，见 ADR 0019）；未来若需，在跑批层展开两次独立运行。
- 并发：**scope 内串行**（上下文依赖），**scope 间并行**（互相独立）。

## 留口子：Ports & Adapters（六边形架构），组合根注入

可替换的外部依赖不散落成 `run_scope` 的一堆参数，而是收成一个 **ports 层**（类比 DAO 层）：导出稳定接口，核心只依赖接口、不知实现是谁。

**按关注点拆成独立 port（不揉成上帝 module）**：
- `Engine` —— 真正跑一个 scope 的地方（名 `Engine`，对齐 CONTEXT 「引擎」术语）。**实装收敛为单个参数化 adapter `SubprocessEngine`**（`core/core/adapters/subprocess_engine.py`）：以 `cmd`/`cwd`/`env` 参数化,既能 spawn Node worker 也能 spawn Python worker——因两腿"spawn 子进程 + 讲同一套 0024 协议"的形状本就完全一致（[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)），无需 `MidsceneEngine`/`NovaActEngine` 两个类。哪条腿由组合根传不同 `cmd` 决定（`EngineResolver` 按 `job.engine` 选）。
- `RunStore` —— **控制面**：持 **definition（`RunMeta`，执行前确定的身份 + `Job[]`）+ 运行态（`RunState`：status、起止、会话血缘 sessionId）**（频繁读写：轮询/续跑/WebUI 进度）。`save_run(meta, state)` 分别落、`load_run_meta`/`load_run_state` 分别读（definition 与运行态生命周期不同：前者执行前定、后者执行后产，见上「三层切分」）。**这才是未来 DynamoDB 真正要存的东西**（可恢复、可轮询）。
- `ResultStore` —— **数据面**：每 scenario 的 pass/fail、投票抖动、原生报告指针（追加为主；CI 读判定真值靠它）。`save_job_result`/`load_job_result`/`load_all` 按 job 粒度读写（判定真值唯一权威）。
- `ReportStore` —— 把 `RunResult` 归集成 RunReport（manifest + index，派生只读导航视图；local FS → S3）。**已实装** `LocalReportStore`（[0027](./0027-runreport-aggregation-index.md)）。
- （其余按需，如凭证源；保持各自独立、生命周期不同）

> **`RunStore` 从原 `ResultStore` 拆出（对本 ADR 早先单一 `ResultStore` 的修正）**：控制面（状态/血缘，频繁读写、撑轮询续跑）与数据面（结果落地，追加为主）访问模式与生命周期不同，拆成两个 port 更内聚——也让「DDB 存什么」清晰（DDB 主要服务 `RunStore`）。

**adapters 按 port 分子目录的目标布局**（多后端时不按后端混放）——下为**目标态**，当前实装更扁平（见图后说明）：

```
core/
├── ports.py                 ← 接口定义（Engine / WorkerHandle / EngineResolver / Sink / RunStore / ResultStore / ReportStore）
└── adapters/
    ├── subprocess_engine.py              ← Engine 实装：单个参数化 adapter（spawn node / python 皆可）✅ 已建
    ├── report_store/local.py             ← RunReport 归集（manifest+index；未来 s3.py）✅ 已建（0027）
    ├── run_store/local.py                ← 控制面；（未来 ddb.py）        ✅ 已建
    └── result_store/local.py             ← 数据面；（未来对象存储）        ✅ 已建
```

**当前实装**：四个 port 的 local adapter **均已建**——`subprocess_engine.py`（Engine）、`run_store/local.py`（`LocalRunStore`：`save_run(meta, state)` 落 `run_meta.json`(definition) + `run_state.json`(运行态)，`load_run_meta`/`load_run_state` 读回）、`result_store/local.py`（`LocalResultStore`：每 job 判定落 `jobs/<编码 scope_id>.json`）、`report_store/local.py`（`LocalReportStore`，归集 RunReport，[0027](./0027-runreport-aggregation-index.md)）。判定结果不再仅在内存，cli 跑完落 `<report-dir>/<run_id>/`。**克制**：store adapter 只忠实持久化已成形的 `RunMeta`/`RunState`/`JobResult`（复用 `serialize.to_dict/from_dict` 单一序列化真理源），**未发明** jobId/DDB 表/轮询续跑读取面那些字段——它们仍 defer，待真实续跑/轮询/WebUI 需求逼出（见上「数据模型」节字段级 schema 顺延）。云端再填 DDB/S3/Fargate。

**选实现 = 组合根注入，不是 module 自选**（关键，避开本会话踩过的坑）：
- 接口定义在 `ports`；**具体 adapter 由调用方（CLI 的 main / WebUI 的 bootstrap = 组合根）在启动时注入**给核心。核心只认接口。
- **禁止** ports module 内部用全局单例 + `env`-sniff 自选实现——那正是本项目踩过的 Midscene `GlobalConfigManager` 反模式（import 时缓存 env、运行时改不动、难测）。注入式可测、无隐藏全局。

**rule-of-three 克制**：接口现在定（廉价，还逼清边界），但**只写 local adapter**；DDB/S3/Fargate adapter 等云端真需要时再填。

这样无状态化、上云、WebUI 接入都成了"加 adapter + 组合根换注入"，核心与接口不动。

## 工程布局：core / cli / engines 三者平级对标

**当前实装态（v1.0 进行中）**标在各行右侧 ✅/⬜：core/ 已建、cli/ 已建、engines/ 已迁、两腿 worker 已落地（曾用 `core/run_e2e.py` 作组合根雏形，cli/ 落地后退役）。

```
yaozhou/
├── core/                ← 窄腰：纯编排，零引擎依赖                          ✅ 已建
│   ├── model.py · parse.py · scope.py · schedule.py · wire.py · serialize.py · ports.py · errors.py  ✅
│   │     （wire.py=worker 协议单向序列化；serialize.py=领域模型双向持久化的单一真理源，二者分工不同）
│   └── adapters/        ← 按 port 分；现有 subprocess_engine.py（单 adapter 参数化，非 midscene.py/novaact.py 两文件）✅
├── cli/                 ← 最薄前端 = 组合根（在此 new 出具体 adapter 注入给 core）  ✅ 已建（独立子工程，core 作 path 依赖）
│   └── cli/{__main__.py（argparse 皮）· compose.py（组合根/引擎注册表，WebUI 复用）· render.py（事件/RunResult 渲染）}
└── engines/             ← 两个可插拔引擎，与 core 平级对标                  ✅ 已迁
    ├── midscene/        ← 整个 TS 子工程                                  ✅ worker：engines/midscene/worker/run-scope.ts
    │   ├── worker/run-scope.ts · lib/agentcore-sigv4.mts
    │   └── （node_modules / spikes / cucumber 等整体随迁）
    └── novaact/         ← 整个 Python 子工程                              ✅ worker：engines/novaact/worker/run_scope.py
        ├── worker/run_scope.py                                          ✅（确定性注册表/ai_steps 拆分留口子，见 0022）
        └── lib/workflow_setup.py · .venv（整体随迁）
```

- **`engines/{midscene,novaact}` 提升为与 `core/` 平级**（不再各藏一个 `worker/` 子目录）：引擎子工程必须连同其依赖环境（`node_modules`+`agentcore-sigv4.mts` / `.venv`+`workflow_setup.py`）整体存在，故**整体**移到 `engines/` 下，既对称又不把代码与依赖环境拆开。
- **目录名用 `engine` 而非 `worker`**：对齐 CONTEXT 「引擎」与 `Engine` port；worker 是运行时角色（被 spawn 的进程），engine 是领域概念——`engines/midscene/` 内**含**一个 worker 入口。
- **窄腰目录名 `core`、不叫 `lib`**：`lib` 已被各引擎子级占用（`engines/midscene/lib`、`engines/novaact/lib` 放引擎内共享模块），复用会混淆。散文里称「核心库 / core 包」无妨（它确是 cli/未来 WebUI 依赖的可导入库），但**目录**是 `core`。

## 版本切分（按完成线，非时间；版本号用 SemVer）

> 版本号语义：`0.x` = 内部验证、API 不稳；`1.0.0` = 团队日常可用的第一个稳定承诺；云端化是**非破坏增量**（加 adapter、核心 API 不动），故为 minor bump `1.1.0` 而非 major——这本身印证了「留口子」设计对。

- **spike — ✅ 已完成**：技术链路全通，由 `spike-validated` tag 封存。
- **v0.1.0（核心假设验证）— ✅ 方向已证，正式验收顺延 v1.0.0（见下决定）**：糙、小范围、本地执行。
  - **核心假设（可证伪）**：QA **只写 `.feature`、零 step 代码**，靠通用 step（`When {自然语言} → aiAct`）即可跑通用例。
  - **原验收标准**：≥3 个**真实业务用例**（含不同动作类型）全部 QA 零 step 代码跑通；每处破例写代码记为反证；破例过多 → 假设不成立。
  - **实际达成**：用**骨架用例**（wikipedia / example.com，见 CONTEXT「骨架验证用例」）覆盖了单步/多步复合/开放动作/AI 布尔·否定·取数·取串断言/主观判定/tag 路由，**全程 QA 零代码**，两腿都跑通——可行性**方向已证**。
  - **决定（边界，务必读）**：**v0.1.0 判「方向已证」，不补真实用例即进 v1.0.0**。理由——① 团队当前**拿不到真实业务用例**（站点登录态等不可得），强等是空等；② 没有真实用例 → 破例无从触发 → **「破例清单」这条验收无法在 v0.x 执行**。故把「真实业务用例验收 + 破例记录」**顺延并入 v1.0.0**：待有真实用例时在 v1.0 里跑出破例、据以校验「QA 零代码」承诺。**已知风险**：v1.0 架构基于「骨架用例都很顺」的乐观假设设计，真实用例的破例（登录 / HITL / 动态内容 flaky）可能反过来要求调整 v1.0 架构——接受此返工风险，因前置条件（真实用例）确实不具备。
  - **报告**：v0.x 原目标含「报告能看」，当时**决定先「散着」**（手动查目录够用），归集形态待要求清晰再定。**v1.0 已落地为 RunReport 归集索引**（[0027](./0027-runreport-aggregation-index.md)）：不重渲染原生产物、只归集成统一清单 + 导航入口——回答了「先散着」时悬而未决的形态问题（索引而非融合）。
- **v1.0.0（团队 QA 日常可用）— ⏳ 架构设计中（本 ADR + 0022/0023）**：多用例组织、跑批入口（CLI 阻塞跑一批）、scope 调度、抖动治理（投票）落地；本地执行。**承接 v0.x 顺延项**：真实业务用例验收 + 破例清单（RunReport 归集已落地，[0027](./0027-runreport-aggregation-index.md)）。
- **v1.1.0（云端执行）— ⬜ 留口子不实现**：CLI 提交 → Fargate 跑 → 轮询收集，**job = scope** 粒度（上云时坐实，见 [0017](./0017-cloud-execution-fargate-over-runtime.md)）；外置状态存储（DDB，主要服务 `RunStore`）+ 无状态核心。**= 加 adapter + 组合根换注入，核心不动**（「留口子不实现」= 接口现在定、实现等真需要时填）。
- **v2.0.0（规模化）— ⬜ 留口子不实现**：WebUI 前端（直接调核心）。

## G1/G2 解析前置（声明语法已定，调度实现待 v1.0）

G1/G2 是 v1.0 核心库 `.feature` 解析的前置——其声明语法**现已定（ADR 0019）**：

- **G1 — session scope 声明**：✅ `@scope:<name>` tag（相同值同 scope、串行共享会话；不同值并行；未标各自独立）。tag 两腿可读已验证。
- **G2 — 引擎选择**：✅ `@engine:<x>` tag 选腿（scope 级属性、容错缺省、冲突报错）；v1.0 只选腿不交叉。两腿路由已验证。
- 声明语法已定，但**调度实现**（scope 串/并行、会话共享、冲突校验）仍待 v1.0 核心库。

## 现在做 / 现在不做

- **现在做（v1.0）**：核心库 `core/` 可被调用（逻辑不焊死在 CLI main 里）；钉死上面数据模型；定义 ports 接口（`Engine`/`RunStore`/`ResultStore`/`ReportStore`）+ 组合根注入；核心自解析 Gherkin + 薄 worker（[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)）。模块设计：worker↔core 协议见 [0024](./0024-worker-core-protocol.md)；plan 模块见 [0025](./0025-plan-module-feature-to-jobs.md)；schedule 模块见 [0026](./0026-schedule-module.md)。
  - **ports 落地状态（v1.0 当前）**：四个 port 的 local adapter **均已建**——`Engine`（`subprocess_engine.py`，子进程起 worker）、`RunStore`（`run_store/local.py`，`save_run(meta,state)` 落 run_meta.json + run_state.json，`load_run_meta`/`load_run_state` 读回）、`ResultStore`（`result_store/local.py`，每 job 判定落盘 + `load_all` 读回）、`ReportStore`（`report_store/local.py`，归集 RunReport）。store adapter 只持久化已成形的 RunMeta/RunState/JobResult、**未发明 ADR 有意 defer 的字段**（jobId/DDB 表/续跑读取面待真实需求逼出，与「数据模型」节字段级 schema 顺延一致）。**两腿 worker 均已落地**（`engines/novaact/worker/run_scope.py` + `engines/midscene/worker/run-scope.ts`），两腿对称、同讲 0024 协议。
- **现在不做**：DynamoDB / S3 / Fargate adapter / 无状态机制 / WebUI ——接口已留好，等云端真需要时填 adapter + 组合根换注入。**避免为想象中的云端预先盖机器。**
- **G1/G2 声明语法已定**（ADR 0019）；其**调度实现**（scope 串/并行、会话共享、engine 冲突校验）由 v1.0 核心库落地。
- **多用例组织**（feature 分目录/命名约定、跑批入口、跑批层选择 feature/tag）同样由 v1.0 核心库落地——它依赖核心库的调度层，在 bdd 直跑层做是临时的、核心库会重做。当前 `features/` 下多个文件仅是 v0.x 打磨产物，未做有意组织。（旧的 cucumber `--tags` 选子集约定随 BDD runner 一并退役，见 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)；选子集改由核心调度层据 tag 实现。）
