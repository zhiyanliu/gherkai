# 执行架构：核心库（窄腰）+ Run 数据模型 + 留好状态存储的口子

> **Status:** Partially-superseded-by 0034 ——（本 ADR 亦与 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md) 一并部分取代 [0006](./0006-form-a-two-subprojects-no-orchestrator.md)：反转其「不设统一编排入口/两套 runner 各自加载」操作立场。）核心架构（窄腰/注入/数据模型/三层切分）及 (a) 类后端替换「加 adapter+换注入、核心不动」仍成立（[0033](./0033-iac-aws-backend-and-composition-wiring.md) 已证）；仅「无状态化=核心不动」对**无状态跑批**的前瞻断言被 [0034](./0034-detached-batch-reconciler.md) 纠正为分层两真值（详见下「这样上云…」处的 ⚠️ 分层注；版本切分 v1.1 行与「现在不做」条回指该注）。

界定 v0.x/v1.0 起、并向云端无缝演进的执行架构。本 ADR 是多轮形态讨论的总成，约束 lib 的设计，确保本地与云端、CLI 与 WebUI 不埋返工雷。

## 分层：核心库是窄腰，CLI/WebUI 是可替换前端

```
  CLI(人/CI/skill)   WebUI 后端        ← 前端「皮」（薄）；都直接调核心，平级
        └──────┬──────┘
          执行核心库 core/（窄腰：解析 .feature → 分组 scope → 调度 → 收集结果；零引擎依赖）
                │  Engine port：run_scope(job) → 0024 事件流
        ┌───────┴───────┐                ← 同一个 SubprocessEngine，两个引擎只是 cmd 不同（形状本就一致）
   spawn Node worker  spawn Python worker   按 job.engine 经 EngineResolver 选 cmd，讲同一套 0024 协议
   (midscene 引擎)       (novaact 引擎)
        │                 │
   AgentCore 会话A    AgentCore 会话B      ← 会话生命周期在 worker 内（已验证）
```

- **窄腰是「核心库」`core/`，不是 CLI**。CLI 是核心的第一个、最薄的前端；WebUI 是另一个前端，**直接调核心、不 shell-out CLI**（后者才是"难集成"的错误做法）。
- CI / AI-skill 通过 CLI 这个皮间接用核心；都契合"调命令→等结果→看退出码"。
- **阻塞 vs 非阻塞是调用方的选择，不是核心的属性**：CLI 可轮询到完成（像阻塞）；WebUI 提交即返回 runId、之后轮询。同一核心两种皮都满足。

### 核心语言 & 两个引擎都子进程（见 [0023](./0023-novaact-acting-python-locked-no-ts-core.md)）

两个引擎各自语言锁死（Midscene 锁 TS、Nova Act acting 锁 Python，[0023](./0023-novaact-acting-python-locked-no-ts-core.md) 证伪了「全 TS 核心」），故**无论核心用哪个语言，必有一个引擎跨进程**——这是「双语言裂缝」（[0006](./0006-form-a-two-subprojects-no-orchestrator.md)）的必然。

**决定：两个引擎都作为子进程 worker，核心不 import 任何引擎；核心语言选 Python。**
- **两个引擎都子进程**（而非一个引擎进程内）：两个 `Engine` adapter 形状**完全一致**（spawn worker + 讲同一套 JSON 协议），核心不碰任一引擎 API，AgentCore 会话生命周期留在各自 worker（现 `engines/novaact/worker/run_scope.py` 三层 `with NovaAct/cdp_session/workflow` / `engines/midscene/worker/run-scope.ts`；早期在 BDD 的 `generic.steps.ts` Before/After、`nova_ctx` fixture 验证过，BDD 直跑层已由 0022 退役）。这才是对称 `Engine` port 最干净的形态；一个引擎进程内会让 adapter 出现两种形状、核心 venv 被引擎依赖树绑死。
- **核心语言 = Python**：两个引擎都子进程后，核心是无重型引擎依赖的薄编排层，语言成为低风险自由选择；选 Python 因 boto3 生态成熟（便于未来云 adapter）+ 官方 `gherkin-official` 解析。
- **核心自解析 Gherkin + 薄 worker（B1）**：核心拥有解析（单一事实源），worker 只派发 step → act/assert，**退役 cucumber 补丁与 pytest-bdd 路由 hack**。详见 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)。

## 数据模型（现在钉死；耐久，决定 DDB 表 / WebUI / 报告）

| 概念 | 是什么 | 产出 |
|---|---|---|
| **Step** | scenario 内单步 | pass/fail/error（+ scope 内短路的 `skipped`，带正交 `shortcircuited` 标记，见 [0031](./0031-job-lifecycle-states-and-severity.md) 决定六）、投票 tally、墙钟时长（`StepResult`，core 首次保留 step 级粒度） |
| **Scenario** | Gherkin 单个 `Scenario:` | pass/fail、A/B 断言、抖动数据（投票）、原生报告引用、墙钟时长 |
| **Feature**（`.feature`） | 含 1..N scenario | **组织轴**（正交，非执行单元） |
| **Scope**（session scope） | 共享操作上下文的 scenario 分组 | **执行单元**：scope 内串行、scope 间并行；产出原生量成本合计 + 墙钟时长 |
| **Job** | 提交给执行面的单元 | **= Scope**（被 session-scope 语义强制：若 job=scenario，有依赖的 scenario 会被拆到不同 microVM 无法共享会话） |
| **Run** | 一次执行，封装多个 job | `runId`、总状态、起止、墙钟时长、**RunResult**、**RunReport** |

- **RunResult** = 机器可读汇总判定（退出码 / CI / WebUI 状态）= **definition（`run_meta`）+ 判定（`jobs`）的显式合成**（见下「三层切分」）。字段构成：`run_meta` + status 三态 + 各 job 结果 + `total_tokens`/`total_time_worked_s` 两个原生量各自跨 scope 合计 + `duration_ms` 总墙钟。其下 `JobResult` → `ScenarioResult` → `StepResult` 三层结果（core 保留 step 级粒度），各级带 `duration_ms` 墙钟时长（性能指标，与成本的 `time_worked_s` **正交**，见 [0024](./0024-worker-core-protocol.md)）。
- **RunReport** = 人看的归集报告（把两个引擎割裂的 Midscene html / Nova trajectory 归到一处）。**这是原 M5「报告统一」的归宿**——**v1.0 已实现（[0027](./0027-runreport-aggregation-index.md)）**：定为**跨引擎归集索引**（`manifest.json` 机器可读 + `index.html` 人可导航入口），**只索引/链接原生产物、不解析融合其内容**；新引擎报任意 `kind` 零改 core。由 `ReportStore` 从 `RunResult` 一次归集（cli 每次 run **默认生成**，`--no-report` 跳过）。

### 三层切分：definition / 控制面运行态 / 数据面判定（数据流向不从结果反推）

一次 run 的数据按**何时产生、谁拥有**切成三层，对应三种类型与三个 store：

| 层 | 内容 | 何时 | 类型 | store |
|---|---|---|---|---|
| **definition（前置身份）** | run_id + created_at + 跑哪些 job（完整 `Job`：scope/engine/scenarios/steps + 投票次数 `assertion_votes` + job 墙钟预算 `timeout_s`，"要跑什么"，[0019](./0019-feature-tags-scope-and-engine.md)/[0034](./0034-detached-batch-reconciler.md)「job timeout」节）+ run 级 `extra_http_headers`（隧道等 context 级请求头，[0035](./0035-local-app-testing-via-tunnel.md)；core 只搬运不消费语义） | **执行前**确定（plan 产出 + 组合根生成 run_id） | `RunMeta`（持有 `tuple[Job,...]`，不另造 JobMeta） | `RunStore`（控制面） |
| **控制面运行态** | 总 status / 各 job status / 会话血缘 sessionId / 起止 | **执行后**产生（实时写下随进度增量刷，[0030](./0030-realtime-persistence-seam.md)） | `RunState`（`jobs: Map<scope_id, JobState>`，按 scope_id 定位单 job 实时刷；落盘 JSON 仍 list） | `RunStore`（控制面） |
| **数据面判定明细** | 每 scenario/step 的 pass-fail、投票、cost、报告指针 | **执行后**产生 | `JobResult`→`ScenarioResult`→`StepResult` | `ResultStore`（数据面，判定真值唯一权威） |

- **数据流向单向、不从结果反推**：`features → plan → Job[] → 组合根生成 run_id → RunMeta → schedule(run_meta) → RunResult`。`RunMeta`（definition）是 schedule 的**输入**、不是从 `RunResult` 反抽——run 的身份执行前就定了。`schedule` 把 `run_meta` 原样放进 `RunResult`（合成），并归约出判定。`RunState` 概念上是 `RunResult` 的**运行态投影**（status/session_id，非反推 definition 身份——scope_id 取自 `jr.job`，本就在 definition 里）；`run_state_from_result` 是该投影的具名实现（现主要供测试便利构造 + 潜在 WebUI 轮询面复用）。**生产 RunState 不走一次性投影、而是 `RunPersistence` 增量写**（begin/on_job_complete/finalize 逐步落 status/时间戳，ADR 0030）——投影语义仍成立、只是落库路径改为增量。
- **`RunResult` = `RunMeta` + 判定的显式合成**：`JobResult` **持有 `Job`**（definition）而非重复抄它的 scope_id/scope_name/engine——消除「抄字段抄漏」（旧版抄了 engine 漏了 scope_name），存储唯一、读法经 property 稳定。
- **status 不进 `RunMeta`**：status 是判定派生（执行后），属控制面运行态/数据面，不是 definition。
- **「执行中实时更新状态」靠 schedule 的旁路注入点（`on_event`/`on_job_complete`）让组合根落库，不靠 schedule 持有 store**：schedule 保持纯归约、不依赖任何 store；落库编排收在组合根注入的 `RunPersistence`（[0030](./0030-realtime-persistence-seam.md)）。**已落地**——cli 经此实时写 RunState（RUNNING 中间态）+ ResultStore（每 job 判定），WebUI 轮询面可直接复用。（早期设计曾设想让落库走 sink，已被 [0030](./0030-realtime-persistence-seam.md) 否决——sink 被 sink_lock 串行化、只留给进度显示，落库走独立的 on_event/on_job_complete。）

**已定 = 概念/层级（上表 + 三层切分）+ 协议层字段（[0024](./0024-worker-core-protocol.md)）**：每 scenario 判定（status 三态）、抖动投票 tally、规范化 errorType、cost 信封、报告产物指针（reportRefs）等 **scenario/scope 级字段已由 worker↔core 协议钉死**——它们是 RunResult/RunReport 的字段来源。**仍未定 = 持久化层 Run/Job 级字段**（runId / jobId(scopeId) / 会话血缘 sessionId / 起止时间 / DDB 表结构 / WebUI 读取面）：有意留到 v1.0 真实跑批逼出（"报告要展示什么、CI 要读什么"届时自然浮现），避免现在纸上列错。（原计划在 v0.x 逼出，但 v0.x 判「方向已证」未做真实用例验收，顺延 v1.0，见下「版本切分」。）**其中「轮询读取面」+ `RunState` 的 `high_water_mark` 由 v1.2 无状态跑批逼出并定型**（[0034](./0034-detached-batch-reconciler.md)：`status` 命令只读 `RunState`、reconciler 从 events 全量重放推演、HWM 挡并发 stale 覆盖；退出码取值——cloud 由退出观察者从 ECS STOPPED 事件 payload 读 `exitCode` 写 `task_exited`、local 由 per-run 进程 `proc.wait()` 读，非靠 `DescribeTasks` 轮询）——印证「留到真跑逼出」的克制。

## 引擎选择 & 并发（已定）

- 用例可配"用哪个引擎"（默认单引擎），经 `@engine:` tag 选引擎（ADR 0019）。**双引擎交叉验证 v1.0 不做**（价值可疑、复杂度高，见 ADR 0019）；未来若需，在跑批层展开两次独立运行。
- 并发：**scope 内串行**（上下文依赖），**scope 间并行**（互相独立）。

## 留口子：Ports & Adapters（六边形架构），组合根注入

可替换的外部依赖不散落成 `run_scope` 的一堆参数，而是收成一个 **ports 层**（类比 DAO 层）：导出稳定接口，核心只依赖接口、不知实现是谁。

**按关注点拆成独立 port（不揉成上帝 module）**：
- `Engine` —— 真正跑一个 scope 的地方（名 `Engine`，对齐 CONTEXT 「引擎」术语）。**实装收敛为单个参数化 adapter `SubprocessEngine`**（`core/core/adapters/subprocess_engine.py`）：以 `cmd`/`cwd`/`env` 参数化,既能 spawn Node worker 也能 spawn Python worker——因两个引擎"spawn 子进程 + 讲同一套 0024 协议"的形状本就完全一致（[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)），无需 `MidsceneEngine`/`NovaActEngine` 两个类。哪个引擎由组合根传不同 `cmd` 决定（`EngineResolver` 按 `job.engine` 选）。
- `RunStore` —— **控制面**：持 **definition（`RunMeta`，执行前确定的身份 + `Job[]`）+ 运行态（`RunState`：status、起止、会话血缘 sessionId）**（频繁读写：轮询/续跑/WebUI 进度）。读写两套接口：①一次性 `save_run(meta, state)` + `load_run_meta`/`load_run_state`；②实时写三段（[0030](./0030-realtime-persistence-seam.md)）`create_run`（开始：写 definition + 初始全 pending）→ `update_job_state`（按 scope_id 增量刷单 job）→ `finalize_run`（commit point：写总 status + ended_at）。definition 与运行态生命周期不同（前者执行前定、后者执行后产/随进度刷，见上「三层切分」）。**这才是未来 DynamoDB 真正要存的东西**（可恢复、可轮询）。
- `ResultStore` —— **数据面**：每 scenario 的 pass/fail、投票抖动、原生报告指针（追加为主；CI 读判定真值靠它）。`save_job_result`/`load_job_result`/`load_all` 按 job 粒度读写（判定真值唯一权威）。云端后端 **S3**（每 job 一对象，赌 CI 按键取判定，见下三层 store 选型 + [0030](./0030-realtime-persistence-seam.md) 第五刀）。
- `ReportStore` —— 把 `RunResult` 归集成 RunReport（manifest + index，派生只读导航视图；文件型 → 云端 **S3**）。**已实装** `LocalReportStore`（[0027](./0027-runreport-aggregation-index.md)）。
- （其余按需，如凭证源；保持各自独立、生命周期不同）

> **`RunStore` 与 `ResultStore` 分立的理由**：控制面（状态/血缘，频繁读写、撑轮询续跑）与数据面（结果落地，追加为主）访问模式与生命周期不同，拆成两个 port 更内聚——也让「DDB 存什么」清晰（DDB 主要服务 `RunStore`）。

> **三层 store 后端不对等——按访问模式各选、不建全网格**（v1.1 云端选型的定调）：三个 store 存的数据性质不同，天然后端也不同，**不是**每层都配 Local/DDB/S3 三个 adapter 的笛卡尔网格。
> - **`RunStore`（记录型：小、频繁更新 pending→running→终态、要轮询/查询）→ DDB**。不会有 `S3RunStore`（S3 不适合频繁更新的小记录）。
> - **`ReportStore`（文件型：manifest + `index.html`，给人看/serve/下载）→ S3**（静态托管 / presigned URL）。不会有 `DDBReportStore`（DDB 存 HTML 页荒谬）。
> - **`ResultStore`（每 scope 的 `JobResult` JSON）→ S3**（第五刀已定，[0030](./0030-realtime-persistence-seam.md)）：它两可——既像「记录」（`run_id`+`scope_id` 键）又像「文件」（自包含 JSON blob）。**赌 CI 按 `run_id`+`scope_id` 键取判定**（key=`<run_id>/jobs/<quote(scope_id)>.json`）→ S3 对象足够；将来若真需要「跨 scope 查询/过滤」（列出某 run 所有 failed scope 等）→ **加一个 DDB 索引层**，是加法不返工。
> 即云端 adapter 是「Run→DDB、Report→S3、Result 两选一」，而非九宫格。

> **worker 产物持久化 ⊥ store（两条正交轴，别混）**：
> - **worker 产物落点**：由**组合根注入的 S3 落点配置**驱动（有→worker 上传 S3 报 `s3://`、无→报 `file://`），落点由**注入驱动、不跟"worker 在哪跑"走**（[0029](./0029-engine-artifacts-to-s3.md)）——用户侧 `--backend cloud`=Fargate 强制注入（上传）、`--backend local`=subprocess 不注入（报 `file://`）；`subprocess + 注入 S3 落点` 也上传（**内部预演路径 / e2e_harness，Fargate 忠实预演**，非用户档，见下决策 B）。**产物怎么持久化是 per-worker by-design 的事，不归 store**。
> - **store adapter**（Local/DDB/S3）——只持久化 **core 自己的序列化数据**（RunMeta/RunState/JobResult/RunReport），并**不透明搬运** worker 报的 `ref`（`ResourceUri`，[0027](./0027-runreport-aggregation-index.md)）。store **不上传 worker 产物**。
> - 二者是**矩阵不是绑定**：如 Local store + Fargate worker 合法（core 数据落本地、worker 产物在 S3）。**注意这是组合根内部/e2e 可拼的矩阵、非用户 CLI 旋钮**——面向用户 `--backend` 一个开关同时定 store 与执行（决策 A：cloud⇒Fargate 执行+云存储），不把这层正交暴露成用户旋钮。报告的自包含/可移植由 `index.html` 的 `href` 相对化达成（不拷贝产物；产物拷贝式 materialize 已否决，见 [0027](./0027-runreport-aggregation-index.md)「被拒方案」）——与 worker 把产物放哪正交。

**adapters 按 port 分子目录的目标布局**（多后端时不按后端混放）——下为**目标态**，当前实装更扁平（见图后说明）：

```
core/
├── ports.py                 ← 接口定义（Engine / WorkerHandle / EngineResolver / Sink / JobSink（0030）/ RunStore / ResultStore / ReportStore）
└── adapters/
    ├── subprocess_engine.py              ← Engine 实装：单个参数化 adapter（spawn node / python 皆可）✅ 已建
    ├── fargate_engine.py                 ← Engine 云端实装（job-in 走 S3、events-out 走 DDB events 表）✅ 已建（0024/0032/0033）
    ├── report_store/{local.py, s3.py}    ← RunReport 归集（manifest+index）✅ 已建（0027；s3 见 0030）
    ├── run_store/{local.py, ddb.py, arg_offload.py}  ← 控制面（ddb=DynamoDBRunStore、arg_offload=S3StepArgumentOffloader）✅ 已建（0030）
    ├── result_store/{local.py, s3.py}    ← 数据面（s3=S3ResultStore）✅ 已建（0030）
    ├── event_log/{sqlite.py, ddb.py}     ← EventLog port（无状态跑批的写模型：local SQLite / cloud DDB events 表）✅ 已建（0034）
    ├── cloud_launcher.py                 ← Launcher port cloud 实装（ECS RunTask；对位 gherkai/detached.py 的 SubprocessLauncher）✅ 已建（0034）
    └── _boto.py                          ← 云端 adapter 共享的 boto3 依赖守卫（非 port 实装，冗余兜底：主拦截在组合根）✅ 已建
```

**`EventLog` / `Launcher` 两个 port 定义在 `core/reconcile.py`、不在 `ports.py`**（[0034](./0034-detached-batch-reconciler.md)）：它们只服务无状态推进路径（reconciler 读全量 events 重放 / CAS 抢占成功后起一个 job），与 `ports.py` 那批「同步 `run` 也用」的口生命周期不同；实装各两个（`SqliteEventLog`/`DdbEventLog`、`SubprocessLauncher`（在 `gherkai/detached.py`）/`CloudLauncher`），同样组合根注入。

**当前实装**：四个 port 的 local adapter **均已建**（`subprocess_engine.py` / `run_store/` / `result_store/` / `report_store/`，方法签名以代码与上「按关注点拆 port」节的契约描述为准）。判定结果不再仅在内存，cli 跑完落 `<report-dir>/<run_id>/`（`run_meta.json` + `run_state.json` + `jobs/` + RunReport）。**克制**：store adapter 只忠实持久化已成形的 `RunMeta`/`RunState`/`JobResult`（复用 `serialize` 单一序列化真理源），**未发明** jobId/DDB 表/轮询续跑读取面那些字段——它们仍 defer，待真实续跑/轮询/WebUI 需求逼出（见上「数据模型」节字段级 schema 顺延）。云端再填 DDB/S3/Fargate。

**选实现 = 组合根注入，不是 module 自选**（关键，避开 env-sniff 全局单例反模式——见下 `GlobalConfigManager` 条）：
- 接口定义在 `ports`；**具体 adapter 由调用方（CLI 的 main / WebUI 的 bootstrap = 组合根）在启动时注入**给核心。核心只认接口。
- **禁止** ports module 内部用全局单例 + `env`-sniff 自选实现——那正是本项目踩过的 Midscene `GlobalConfigManager` 反模式（import 时缓存 env、运行时改不动、难测）。注入式可测、无隐藏全局。

**rule-of-three 克制**：接口 v1.0 先定（廉价，还逼清边界）、只写 local adapter；v1.1 云端真需要时填云端 adapter——**云端 adapter 现已填齐**：store 层（RunStore→DDB、Result/ReportStore→S3，第五刀，[0030](./0030-realtime-persistence-seam.md) 决定六）+ 执行面 `FargateEngine` 与组合根接线/建资源的 IaC（[0032](./0032-fargate-execution-environment.md)/[0033](./0033-iac-aws-backend-and-composition-wiring.md)，真部署真跑）——`--backend cloud` 现已绑定 Fargate 执行（见下「决策 A」）。

这样上云、WebUI 接入都成了"加 adapter + 组合根换注入"，核心与接口不动。**⚠️ 但「无状态化」是例外、须分层看**（[0034](./0034-detached-batch-reconciler.md) 纠正）：**(a) store/engine 后端替换**（local↔DDB/S3、subprocess↔Fargate）= 注入、核心不动（[0033](./0033-iac-aws-backend-and-composition-wiring.md) 已证）；**(b) 无状态提交-收集**（CLI 提交即走、事件驱动 reconciler）= **驱动模型演进**（同步 ThreadPool 循环解体为无状态 tick、抽纯 `project`/`plan_next`、FargateEngine 增出 `start_scope` fire-and-forget 形状、严格并发从进程内线程池迁到 store CAS）——**核心与接口要动**，非「只加 adapter」。已作为 v1.2 实装真跑通（[0034](./0034-detached-batch-reconciler.md)，见下版本切分 v1.2.0）。

### cli `--backend {local,cloud}`：组合根按开关注入 store + 执行引擎（兑现「换 adapter 核心不动」）

云端 store adapter（DDB/S3，[0030](./0030-realtime-persistence-seam.md) 决定六）落地后，cli 加 `--backend {local,cloud}`（默认 `local`；`run`/`submit`/`status` 三个子命令都有——`submit` 与 `status` 的 backend 须一致，见 [0034](./0034-detached-batch-reconciler.md)；`plan` 纯本地不落库、不加）在组合根按开关选注入哪套 adapter。`RunPersistence`/`schedule` 只认 Store **port**，local↔cloud 切换**零改** core——这正是本 ADR「选实现=组合根注入」的第一次真实兑现。

**单一开关换齐存储三层 + 执行引擎、第一版不开混搭**：`--backend cloud` 一次把 RunStore→DDB、ResultStore/ReportStore→S3（+ 挂 offloader）三层存储全换，**并把执行引擎从 `SubprocessEngine` 换成 `FargateEngine`**（见下「决策 A：`--backend cloud` = 存储上云 + Fargate 执行（单旋钮）」）。理由：三层存储后端不对等（上文已证不存在 `S3RunStore`/`DDBReportStore`），无有意义的混搭矩阵；「Local store + Fargate worker」是 **store⊥worker 正交轴**（上文「worker 产物 ⊥ store」）、是**组合根内部/e2e 可拼的矩阵、非用户 CLI 旋钮**，不需要 `--run-backend`/`--result-backend` 拆开（那是提前盖机器 + 组合爆炸测试负担）。

#### 决策 A：`--backend cloud` = 存储上云 + Fargate 执行（单旋钮，不暴露正交）

**面向用户，`--backend cloud` 是一个旋钮，同时定存储（DDB/S3）与执行（Fargate）**——不把「执行环境（subprocess/fargate）」与「存储 backend（local/cloud）」拆成两个正交旋钮暴露给用户。用户档只有两档：

- **`--backend local`** = subprocess 执行 + 本地盘存储（`Local*Store`）；
- **`--backend cloud`** = Fargate 执行（`FargateEngine`）+ 云存储（DDB/S3）。

**为何不暴露正交**：技术上执行环境与存储确实正交（组合根内部/e2e 能任意拼，见上 store⊥worker 与下决策 B），但把四象限（subprocess/fargate × local/cloud）全摆给用户会**参数爆炸、增加理解负担**，且用户实际只需要「本地跑 / 云上跑」两个心智档。故 CLI 只暴露 `--backend` 一个旋钮，`cloud ⇒ Fargate 执行 + 云存储`绑定。

> **被拒方案护栏（防未来重复进坑）**：曾考虑让**执行环境 ⊥ 存储 backend 完全正交**、用户可任意组合（如 `subprocess + cloud`、`fargate + local` 都作为面向用户的 CLI 档）。**否决**——参数爆炸 + 用户困惑，收益（灵活性）用户实际不需要。**内部矩阵仍正交**（组合根/e2e 可拼），只是 CLI 不把这层正交暴露成用户旋钮。若未来有人再提「为什么不让用户自由组合执行×存储」——答案在此：不是技术做不到，是用户体验刻意收窄。

#### 决策 B：`subprocess + 注入云存储` 降为内部预演/测试手段（非用户档）

`subprocess worker + 注入 S3 落点/DDB events`（旧称「subprocess+cloud」）**不再是面向用户的 CLI 档**（决策 A 下 `--backend cloud` = Fargate），而是**内部预演/测试手段**——即 `tools/e2e_harness.py` 与开发验证用的路径：本地 subprocess worker 注入云存储落点，真跑验证上传链/events 链/S3 key 等，为 Fargate 忠实预演，不必等真容器。

**关键：这只是重定位「谁来用、是不是用户档」，不删预演的价值论证**——「上传/抢传能力提前在 subprocess 环境建好并验证、为 Fargate 铺路」这套论证（见 [0029](./0029-engine-artifacts-to-s3.md)/[0032](./0032-fargate-execution-environment.md)）完全成立、一字不动，只是承载它的 `subprocess + 注入云存储` 从「CLI 用户可选一档」标注为「e2e_harness/开发预演手段」。

**承载机制 = `tools/e2e_harness.py` 自拼 worker env，不由 `compose.build_engines` 暴露形参**：`build_engines` 曾留一个 `artifact_s3=(bucket, prefix)` 形参做这件事，决策 A 落地后它**零生产/工具调用点**（cloud 档恒走 `build_fargate_engines` 自算落点、local 档恒不注入、e2e_harness 自己拼 `ARTIFACT_S3_*` 后 Popen），且其 docstring 反过来声称「跟 `--backend cloud` 走、由组合根注入」——与决策 A 相反的长期漂移源，故删。**护栏（防未来重复进坑）**：上面「内部矩阵仍正交（组合根/e2e 可拼）」不变——真要从组合根再拼这一档时，重加形参是加法、不返工；但**别把它当「cloud 档的注入点」复活**（那是 `build_fargate_engines` 的职责，两处都注入即双真源）。

#### 决策 C：Fargate 执行配置走 CLI 参数注入（对称 `--ddb-table`/`--s3-bucket`）

Fargate 执行环境配置（cluster / task-def / subnet / security-group / events 表名 / container-name 等）**走 CLI 参数注入 `FargateEngine` 构造**，与 `--ddb-table`/`--s3-bucket`/`--region`/`--profile` 同一「组合根注入、非 adapter sniff env」模式（见下「cloud 配置来源」补充 + 注入红线）。**不走 adapter 内部读 env**——那是本 ADR「禁止 ports module 内部 env-sniff」红线点名的反模式。（决策 C 的「注入、非 env-sniff」内核本就是本 ADR 注入红线 + [0024](./0024-worker-core-protocol.md)「run_id 注入 worker」的既有决策，`FargateEngine` 构造签名已兑现；此处只补齐「Fargate 那批参数也走 `--xxx` CLI 面、对称 `--table`」这个面向用户的接口决策。）

**`--region`/`--profile` 必须真正贯通到 worker（不止 store 侧）——但 region 与 profile 是「正确的非对称」，不是机械对称**：worker 侧建 boto3/aws-sdk client（EventSink DDB / JobSource S3 / ArtifactUploader / Nova `Workflow`+`AgentCoreBrowserSessionProvider`）都靠 `AWS_REGION`/boto 默认凭证链（读 `AWS_PROFILE`）解析 region/凭证。**旧接线断裂**：`--region`/`--profile` 此前只喂给 `build_cloud_stores`（core 侧 store 显式 `Session(profile_name=…, region_name=…)`），而 subprocess worker 靠 `env={**os.environ}` **裸继承**父进程 env、Fargate worker 更无继承——于是 `--region us-west-2` 但 shell `AWS_REGION=us-east-1` 时 **store 与 worker 分叉**（core 落 west、worker 走 east），`--profile` 同理。

**决策（region 与 profile 分开处理，因两者的 worker 环境本质不同）**：

- **region — 组合根落实成具体字符串、两路（subprocess + FargateEngine）都注入**：解析链 `--region` 显式 > `AWS_REGION` > `AWS_DEFAULT_REGION` > **`boto3.Session(profile_name=<解析 profile>).region_name`（profile config 兜底）**。**最后这一环是关键**：Nova worker 的 `AgentCoreBrowserSessionProvider`/`BrowserClient.__init__` 调 `validate_region(region)`，**要求显式合法 region 字符串、根本不查 boto 默认链/profile config**——若组合根只解析到 env（不回落 profile config）、profile-only 用户下 worker region=None 会直接 `InvalidRegionError` 崩（每个 run 必经 AgentCore 建连）。故组合根必须把「profile config 里的 region」在**注入前**解析成具体字符串（用 boto3 Session），使 store 与 worker 真正同区、AgentCore 拿到合法 region。解析出的 region 非 None 时写进 subprocess 的 env 与 FargateEngine 的 overrides；仍可为 **None＝真无 region（无 --region/env/profile-region）→ 不写入 → worker fail-loud（`NoRegionError`/`InvalidRegionError`），不硬编码 east**（对齐 store 的宽容边界）。
- **profile — 仅 subprocess 注入，Fargate 绝不注入**：解析 `--profile` 显式 > `AWS_PROFILE`。**subprocess worker 继承本机 `~/.aws`、profile 名合法** → 注入 `AWS_PROFILE` 让 `--profile` 真覆盖。**但 Fargate 容器没有 `~/.aws`、用 task role 凭证链**——注入一个容器内不存在的 profile 名会让 boto3 在 **client 创建期**直接抛 `ProfileNotFound`（真跑证实，非「无害忽略」），且 `ProfileNotFound` **盖过 task role 凭证链**（profile 优先级高于 `AWS_CONTAINER_CREDENTIALS_RELATIVE_URI`）→ worker 起不来。故 **FargateEngine 不接收、不注入 profile**——这不是遗漏，是 subprocess 与容器凭证环境本质不同的**正确非对称**：region 两路都要（容器也需显式 region），profile 只 subprocess 要（容器用 task role、profile 是本机概念）。
- **证据边界（绿≠对）：profile-only 端到端已真验 ✅**。上面 region 解析链的「profile config 回落」那一环（前三级 env 全 miss 时用 `boto3.Session(profile).region_name`）此前只由 `resolve_region` 单测锁逻辑（fake Session），真跑走的都是显式 region 注入路径、没走过这条——是「AgentCore `validate_region` 不吃 profile config、回落失败即每个 run 崩」的关键机制却未真验。**已补真验（profile-only cloud run）**：`--profile default`（region=us-east-1 只在 profile config、非 --region/env）+ **env `AWS_REGION`/`AWS_DEFAULT_REGION` 均 unset** + 不给 `--region`，跑 `--backend cloud` 两引擎 ×（确定性+AI）**全 passed、零 `InvalidRegionError`/`NoRegionError`**——证明 region 真从 profile config 经 `boto3.Session` 解析出、全链路贯通到 Fargate worker、**Nova AgentCore `validate_region` 收到合法 region 字符串没崩**（r2 真起会话+AI act）。mock 之外的真实行为（真 boto3 读真 `~/.aws/config` + 贯通真 worker）已验，边界闭合。

- **worker 侧「Nova region 去硬编码」（配合上面 region 落实）**：Nova worker 曾用 `REGION = os.environ.get("AWS_REGION", "us-east-1")` 的**硬编码 `us-east-1` 兜底**——会在 profile-only 时抢在 profile config 前跑错区（与 store 不一致）。改为 `os.environ.get("AWS_REGION")`（可为 None）：组合根已把 profile-region 落实进 `AWS_REGION` 注入，故正常路径 worker 拿到具体 region；真无 region 时 None→fail-loud（`NoRegionError`，或 AgentCore 那条路径的 `InvalidRegionError`——**AgentCore `validate_region` 不吃 profile config、要求显式 region 字符串**，这正是组合根须在注入前落实 region 的原因）。**代价**：裸跑（无 env 无 profile region）不再兜 east、fail-loud——对齐 store，别静默跑错区。

**装配两个后端都下沉 compose（对称、可复用）**：`build_local_stores` + `build_cloud_stores` 都放 `compose.py`——组合根装配是任何前端（cli / 未来 WebUI）都要的逻辑，收在 compose 让两个后端都能被复用（cli 只是第一个调用者，WebUI 直接复用同两个函数、不经 cli）。这兑现「compose = 可复用组合根」的定位。
- **`build_local_stores(*, report_dir) -> (run_store, result_store, report_store, make_artifacts)`**：new 三个 `Local*Store(root)`，返回三 store + `make_artifacts` 工厂函数（见下第四返回值说明）。
- **`build_cloud_stores(*, table, bucket, prefix, region=None, profile=None, detached=False) -> (run_store, result_store, report_store, make_artifacts)`**：`detached` 是行为开关不是可选装饰——**仅 `submit` 传 `True`**（`create_run` 写的 STATE 带 detached 标记 → 触发 cloud kicker 冷启动），同步 `run` 不传（否则双开推进器，[0034](./0034-detached-batch-reconciler.md)）。`import boto3` 惰性收在函数体内（cli 主依赖不含 boto3，走 `cli[aws]→core[aws]` extra；纯 local 路径绝不触发 import）。造 boto3 句柄抽成可 patch 的小钩子。返回三 store + cloud 的 `make_artifacts` 工厂。
- **两种 boto3 句柄别混**（静默出错高危）：`DynamoDBRunStore` 吃 `resource.Table`（内部 `self._table.put_item`/`.meta.client`），三个 S3 件套（ResultStore/ReportStore/offloader）**共享一个** `client`。喂错句柄类型运行时才 AttributeError、moto/cli 都测不到。
- **测试注入点随之迁移**：原 cli 测试 `monkeypatch m.LocalRunStore/...`（模块级名字）改为 patch `compose.build_local_stores`（或其内部构造钩子）——注入点从「__main__ 模块级 Local* 名字」迁到「compose 的 build 函数」，验的东西不变（写序 / --no-report 不构造 / running→final），只换注入锚。cloud 同理 patch `compose` 的 boto3 钩子。cli 测试**只验接线层**（backend 选对了、构造了正确 adapter + 参数对 + offloader 挂了），不引 moto——adapter 行为已由 core 包 moto 全覆盖，cli 再测是重复且破窄腰。
- **trade-off**：把 local 装配从 `__main__` 迁进 `compose` 要改现有 3 个 `monkeypatch m.Local*` 测试的注入点——换来 compose 两后端对称可复用（WebUI 两路都能直接复用），值得。

**cloud 配置来源 + 落点语义**：
- 表/桶经参数注入（`--ddb-table` 兜底 `AWS_DDB_TABLE`、`--s3-bucket` 兜底 `AWS_S3_BUCKET`）；adapter 假定表/桶已存在（建表建桶归 IaC）。（`AWS_DDB_TABLE`/`AWS_S3_BUCKET` 与集成测试 `tests/README.md` 用的同名——语义一致「哪张表/哪个桶」、不同进程不冲突。）
- **Fargate 执行配置也走 CLI 参数注入（决策 C，与表/桶同模式）**：`--backend cloud` 换 `FargateEngine` 后，其执行环境配置（ECS cluster / task-def / subnet(s) / security-group(s) / assign-public-ip / events 表名 / container-name 等）同样经 CLI 参数注入 `FargateEngine` 构造，**与 `--ddb-table`/`--s3-bucket` 是同一注入模式**（组合根注入、adapter 不 sniff env）。这批参数具体形状（哪些必填、默认值、兜底 env）随 Fargate adapter 接线落地时定、以 code 为准，不在此焊死以免漂移；**接线点在 `compose.build_fargate_engines`**（新增函数、对称只产 SubprocessEngine 的 `build_engines`，`--backend cloud` 用它替代）——组合根在 `new_run_id()` 后把 run_id + 这批 task 配置一起传进 `FargateEngine()`（run_id 是拼 events 表 PK 所需，对称 artifact 落点注入）。adapter 假定 cluster/task-def/events 表已存在（建表建 task-def 归 IaC）。
- **`--region`/`--profile` 可选**：都传给 `boto3.session.Session(profile_name=..., region_name=...)`（都为 None = 默认行为，不显式介入）。**凭证仍不硬编码**——profile/region 是运维配置（选哪个 AWS 账户/区域），不是把 access key 写进代码，不违背「组合根不持 IAM 知识」。region 解析链：`--region` 显式 > `AWS_REGION`/`AWS_DEFAULT_REGION` > profile 的 config `region` 字段——故**给了 `--profile` 但该 profile 没配 region 时仍需 `--region`**（否则 `NoRegionError`）；两者都可选、各自独立兜底。
- **单 S3 桶 + `--report-dir` 复用为 key 前缀**：Result(`jobs/`)、Report(`index.html`)、offloader(`args/`) 三者 key 前缀天然不撞，共用一个桶最简；不新增 `--s3-prefix`——local 的 `<report-dir>/<run_id>/…` 与 cloud 的 `s3://bucket/<report-dir>/<run_id>/…` 布局工整对应。**分隔符规范化**：`--report-dir` 默认 `reports`（无尾 `/`），组合根在传给 S3 adapter 前补 `/`（非空且不以 `/` 结尾则补），否则 `S3*Store` 拼 `f"{prefix}{run_id}"` 会静默生成粘连 key `reports<run_id>/…`。真需分桶（report 公开 serve vs result 私有的生命周期策略）再拆，加法不返工。
- **`--backend cloud --no-report` 合法**：`--no-report` 既有语义=零落盘裸跑、与 backend 正交；所有云端校验/import/异常 gated 在 `need_cloud = do_report and cloud`，此组合跳过一切云端检查（保「三个 store 一次不构造」的逃生舱）。

**artifacts 落点指针按 backend 分支组装、全 URI 化（不硬编码本地路径「说谎」）**：`--json` 的 `artifacts` dict（`report_index`/`run_meta`/`run_state`/`jobs_dir`）现状硬编码本地文件路径，cloud 下这些数据落 DDB/S3、本地路径不存在——必须按 backend 分支：
- local：四项均 `file://` 完整路径（从裸路径升级为 URI，与 cloud 同形工整）。
- cloud：`report_index`（取 `finalize()` 返回值）/`jobs_dir` = `s3://…`；`run_meta`/`run_state` = 自造 `ddb://<table>/<run_id>#META|#STATE` 诊断指针（与 s3:// 同形、纯展示、不被任何代码解析）。
- 第四返回值是 **`make_artifacts(run_id, report_index) -> dict` 工厂函数**（非现成 descriptor）——须在 finalize 拿到 `run_id` 与 `report_index` 后才能组装（`report_index` 可能因 write 失败被隔离而为 None，此时省略 `report_index` 键）；由 `build_local_stores`/`build_cloud_stores` 各自返回（各自最懂按 backend URI 化组装落点/前缀），`_cmd_run` 调它填 artifacts——**不给 Store port 加 `describe_artifacts`**（凭空扩接口面、6 个 adapter 全要实现，过度设计）。
- `finalize()` 返回 None（`ReportStore.write` 失败被 `RunPersistence` 隔离，[0030](./0030-realtime-persistence-seam.md) 决定三）时 `report_index` 键不放裸 `'None'`——省略该键。（曾设 `_report_error` 字段留 traceback 供 cli 可选打 stderr，但 cli 从不消费、已删该悬空字段——写失败被静默隔离、报告可从 RunResult 重建。）

## 工程布局：core / gherkai / cli / engines 平级对标

**当前实装态**标在各行右侧 ✅（本树各行皆已建，无未建项）：core/ 已建、gherkai/ 已抽出（见下「演进」节）、cli/ 已建、engines/ 已迁、两个引擎 worker 已落地。

```
./
├── core/                ← 窄腰：纯编排，零引擎依赖                          ✅ 已建
│   ├── model.py · parse.py · scope.py · schedule.py · project.py · reconcile.py · persist.py · wire.py · serialize.py · ports.py · errors.py  ✅
│   │     （wire.py=worker 协议单向序列化；serialize.py=领域模型双向持久化的单一真理源，二者分工不同）
│   │     （project.py=events→RunState/JobResult 的纯归约投影 · reconcile.py=无状态推进 tick（含 EventLog/Launcher 两 port）· persist.py=实时写编排 RunPersistence；见 0030/0034）
│   └── adapters/        ← 按 port 分（清单见上「adapters 按 port 分子目录」）：subprocess_engine.py（单 adapter 参数化，非 midscene.py/novaact.py 两文件）· fargate_engine.py · cloud_launcher.py · event_log/ · run_store/ · result_store/ · report_store/ · _boto.py ✅
├── gherkai/             ← 产品本体 = 组合根共享层（见下「演进」节；cli/Lambda/WebUI 的共同地基）
│   └── gherkai/{compose.py（组合根/引擎注册表 + `resolve_cloud_target` 云目标解析）· detached.py（local 无状态跑批宿主）· names.py（资源命名真源）· tunnel.py（`--expose-local` 隧道 provider，0035）· tunnel_host.py（隧道宿主编排 + 守护 TTL，0035）}
├── cli/                 ← 纯皮：argparse + 渲染（独立子工程，gherkai/core 作 path 依赖）
│   └── cli/{__main__.py（argparse 皮）· render.py（事件/RunResult/RunState 渲染）}
└── engines/             ← 两个可插拔引擎，与 core 平级对标                  ✅ 已迁
    ├── midscene/        ← 整个 TS 子工程                                  ✅ worker：engines/midscene/worker/run-scope.ts
    │   ├── worker/run-scope.ts · worker/deterministic.ts · worker/deterministic.steps.ts · lib/agentcore-sigv4.mts
    │   └── （node_modules / spikes / cucumber 等整体随迁）
    └── novaact/         ← 整个 Python 子工程                              ✅ worker：engines/novaact/worker/run_scope.py
        ├── worker/run_scope.py · worker/deterministic.py · worker/deterministic_steps.py  ✅（确定性注册表已拆出：deterministic.py=注册表+匹配、deterministic_steps.py=脚手架锚点，两引擎对称，见 0022/0036；仅 ai_steps 的进一步拆分仍是留口子）
        └── lib/workflow_setup.py · .venv（整体随迁）
```

- **`engines/{midscene,novaact}` 提升为与 `core/` 平级**（不再各藏一个 `worker/` 子目录）：引擎子工程必须连同其依赖环境（`node_modules`+`agentcore-sigv4.mts` / `.venv`+`workflow_setup.py`）整体存在，故**整体**移到 `engines/` 下，既对称又不把代码与依赖环境拆开。
- **目录名用 `engine` 而非 `worker`**：对齐 CONTEXT 「引擎」与 `Engine` port；worker 是运行时角色（被 spawn 的进程），engine 是领域概念——`engines/midscene/` 内**含**一个 worker 入口。
- **窄腰目录名 `core`、不叫 `lib`**：`lib` 已被各引擎子级占用（`engines/midscene/lib`、`engines/novaact/lib` 放引擎内共享模块），复用会混淆。散文里称「核心库 / core 包」无妨（它确是 cli/未来 WebUI 依赖的可导入库），但**目录**是 `core`。

### 演进：组合根共享层抽为平级产品本体包 `gherkai/`（v1.2 后布局重构）

初版把 `compose.py`（组合根/引擎注册表）放在 `cli/` 包内、以「WebUI 复用 cli.compose」的方式共享——**该安置已被三个非-CLI 消费者的真实代价证伪**：① `lambdas/reconciler.py` 直接 `from cli import compose`，Lambda zip 被迫打包整个 cli 包（含它永远不用的 argparse/render）；② `iac_aws_backend/names.py` 因「CDK 独立工程、不能 import cli」被迫**复刻**命名函数（双写 + ADR 0033 护栏测试防漂移的持续成本）；③ lambda handler 的测试因 `lambdas/` 无依赖闭包而寄居 `cli/tests/`。按本 ADR 自己的 rule-of-three：消费者已 3 个、WebUI 是可预见的第 4 个——到线。

**解法 = 抽平级工程 `gherkai/`（产品本体包，与产品/CLI 同名）**：`compose.py`（引擎注册表/装配）+ `detached.py`（local 无状态跑批宿主）+ `names.py`（资源命名纯函数，从 compose 拆出、零依赖——供 iac 轻依赖消复刻）移入；`cli/` 退成纯皮（argparse + render）。此后新增的产品本体知识按同一归属直接落在此层——`tunnel.py`（`--expose-local` 的隧道 provider，[0035](./0035-local-app-testing-via-tunnel.md)）即例：隧道生命周期是产品的事、不是 CLI 皮的事。分层语义随之更诚实：**`gherkai/` 知道产品的一切（引擎、云资源、run 生命周期），cli/Lambda/WebUI 只是它的入口皮**。依赖方向：`皮 → gherkai → core`（窄腰红线不动——引擎知识仍不进 core，只是从「寄居 cli」升为「产品本体」）。**命名护栏**：不叫 `composer`（PHP 生态撞名）、不叫 `engine_worker`（与 0024 的 worker 术语撞车且语义反——本层是 worker 的装配者非 worker 本身；且层内一半内容与 engine 无关）。

**归属清算（同一判据的第二轮应用）**：初版抽包只搬了 `compose`/`detached`/`names`，隧道编排与云目标解析仍住 cli 皮内——按上面判据是错位（未来 WebUI/Lambda 两张皮得各复刻一遍，正是抽包时被三个非-CLI 消费者证伪的那个安置模式）。已按同一判据归位：

- **云目标解析** → `compose.resolve_cloud_target(...) -> CloudTarget`（吃入口皮已解析的 flag，吐 prefix + 表/桶/cluster/三 Lambda 的**终名** + region/profile），cli 里三处逐行同形的「flag or env or `default_name(prefix, 基名)`」解析块随之消失；`compose` 的 `_BASE_*` 私有别名（抽 `names.py` 时为「保既有引用不动」留的兼容残留，却被皮当公共面消费）一并删掉，命名真源只余 `gherkai.names.BASE_*` 一处。
- **隧道宿主编排** → 新 `tunnel_host.py`：起隧道 + 映射 definition + 隧道模式恒注入的额外请求头，以及 cloud 守护进程的轮询循环与其 TTL 算法（[0035](./0035-local-app-testing-via-tunnel.md) 决策 3）。**命名同上护栏**：叫 host（宿主，取自 0035 决策 3 的表头术语），不叫 worker——0024 的 worker 专指被 spawn 跑 scope 的引擎进程。
- **产物空壳清理 / 云错误归类** → `compose.prune_empty_dirs`（本地落点是组合根算出来的，[0029](./0029-engine-artifacts-to-s3.md)）、`compose.is_botocore_error`。
- **反向也校准**：`render_run_state`（`status` 的 RunState 人读渲染）从 `gherkai/detached.py` 移回 `cli/render.py`——**渲染是皮的事**；这条判据两个方向都得用，否则「下沉」会退化成「往 gherkai 里倒东西」。

结果：**可复用的产品知识**（云资源定位/隧道生命周期/落点清理/云错误归类）全在 gherkai，cli 皮保留 argparse 声明 + 打印/渲染 + 退出码映射，以及**装配编排的调用序**（解析 → 调 compose/detached 各 build → 注入 core——每张皮都要自己走一遍这个序，序本身不是可下沉的共享物；`_tunnel_watch` 这类隐藏子命令同理，argparse 入口必须在皮里、下沉的是循环体）。

## 版本切分（按完成线，非时间；版本号用 SemVer）

> 版本号语义：`0.x` = 内部验证、API 不稳；`1.0.0` = 团队日常可用的第一个稳定承诺；云端化是**非破坏增量**（加 adapter、核心 API 不动），故为 minor bump `1.1.0` 而非 major——这本身印证了「留口子」设计对。

- **spike — ✅ 已完成**：技术链路全通，由 `spike-validated` tag 封存。
- **v0.1.0（核心假设验证）— ✅ 方向已证，正式验收顺延 v1.0.0（见下决定）**：糙、小范围、本地执行。
  - **核心假设（可证伪）**：QA **只写 `.feature`、零 step 代码**，靠通用 step（`When {自然语言} → aiAct`）即可跑通用例。
  - **原验收标准**：≥3 个**真实业务用例**（含不同动作类型）全部 QA 零 step 代码跑通；每处破例写代码记为反证；破例过多 → 假设不成立。
  - **实际达成**：用**骨架用例**（wikipedia / example.com，见 CONTEXT「骨架验证用例」）覆盖了单步/多步复合/开放动作/AI 布尔·否定·取数·取串断言/主观判定/tag 路由，**全程 QA 零代码**，两个引擎都跑通——可行性**方向已证**。
  - **决定（边界，务必读）**：**v0.1.0 判「方向已证」，不补真实用例即进 v1.0.0**。理由——① 团队当前**拿不到真实业务用例**（站点登录态等不可得），强等是空等；② 没有真实用例 → 破例无从触发 → **「破例清单」这条验收无法在 v0.x 执行**。故把「真实业务用例验收 + 破例记录」**顺延并入 v1.0.0**：待有真实用例时在 v1.0 里跑出破例、据以校验「QA 零代码」承诺。**已知风险**：v1.0 架构基于「骨架用例都很顺」的乐观假设设计，真实用例的破例（登录 / HITL / 动态内容 flaky）可能反过来要求调整 v1.0 架构——接受此返工风险，因前置条件（真实用例）确实不具备。
  - **报告**：v0.x 原目标含「报告能看」，当时**决定先「散着」**（手动查目录够用），归集形态待要求清晰再定。**v1.0 已落地为 RunReport 归集索引**（[0027](./0027-runreport-aggregation-index.md)）：不重渲染原生产物、只归集成统一清单 + 导航入口——回答了「先散着」时悬而未决的形态问题（索引而非融合）。
- **v1.0.0（团队 QA 日常可用）— ✅ 完成（架构与实现均已落地，本 ADR + 0022/0023）**：跑批入口（CLI 阻塞跑一批）、scope 调度、抖动治理（投票）落地；本地执行。**唯一未结项 = 承接 v0.x 顺延的「真实业务用例验收 + 破例清单」**——前置条件（可得的真实业务用例）仍不具备，见上 v0.1.0「决定（边界）」条及其已知返工风险；同顺延项里的 RunReport 归集已落地（[0027](./0027-runreport-aggregation-index.md)）。（「多用例组织」中的**按 tag 选子集仍未实现**，见下「现在做 / 现在不做」节。）
- **v1.1.0（云端执行）— ✅ 完成**：CLI 提交 → Fargate 跑 → 轮询收集，**job = scope** 粒度（上云时坐实，见 [0017](./0017-cloud-execution-fargate-over-runtime.md)）；外置状态存储（DDB，主要服务 `RunStore`）+ 无状态核心。**存储/执行后端替换=加 adapter+换注入、核心不动**（已证）；**但无状态提交-收集是驱动模型演进、核心要动**（[0034](./0034-detached-batch-reconciler.md) 纠正，见上「这样上云…」处的 ⚠️ 分层注）。**决策 A：`--backend cloud` = 存储上云 + Fargate 执行绑定**（单旋钮、不暴露 subprocess×cloud 等正交用户档，见上「cli backend 选择」节）。**已落地**（清单以各权威 ADR 为准）：实时写存储接缝 + 云端 store adapter（[0030](./0030-realtime-persistence-seam.md) 决定六）+ job 生命周期态/severity（[0031](./0031-job-lifecycle-states-and-severity.md)）+ `FargateEngine` 执行 adapter 与 Fargate 特有韧性校准（[0024](./0024-worker-core-protocol.md)/[0032](./0032-fargate-execution-environment.md)，4 次真跑标定）+ 组合根接线与 `iac_aws_backend` CDK 工程（[0033](./0033-iac-aws-backend-and-composition-wiring.md)，真部署真跑）——坐实了「换 adapter 核心不动」，真跑通 local↔cloud 端到端。曾是唯一剩项的**无状态跑批（CLI submit → 事件驱动推进 → 轮询收集，job = scope 粒度）已作为 v1.2 完成、真部署真跑通**（见下 v1.2.0 行 + [0034](./0034-detached-batch-reconciler.md)）。
- **v1.2.0（无状态跑批）— ✅ 完成**：**「CLI 提交完就走、异步收集」**（`submit` 提交即返回 run_id、`status [--wait]` 轮询/接力收集；同步 `run` 保留不变）——CQRS + 无状态事件驱动 reconciler，[0034](./0034-detached-batch-reconciler.md)。**驱动模型演进、非只换 adapter**（见上「这样上云…」处 ⚠️ 分层注的 (b)）：抽纯 `project`/`plan_next`（core，local/cloud 共用）+ `reconcile.tick`（幂等、多触发源、CAS/HWM 条件写）。local=per-run 进程（`setsid` 脱离）+ SQLite events sink；cloud=三 Lambda 事件驱动链（kicker 冷启动 / reconciler 主推进 / 退出观察者）+ DDB Stream + EventBridge（[0033](./0033-iac-aws-backend-and-composition-wiring.md) IaC 扩展）。**真部署真跑通**（真实 AWS 账户 us-east-1：local+cloud 两路 submit→推进→passed，含卡死救活真验）。演进 0016/0024/0026/0031（Partially-superseded-by 0034）+ 0030（重议条落地）。
- **v1.3.0（本地应用测试 + 能力可发现）— ✅ 完成**：`--expose-local` 经隧道把开发机上的被测应用暴露给云端浏览器（[0035](./0035-local-app-testing-via-tunnel.md)：URL 映射在组合根做、worker/引擎对隧道无知；新增 `gherkai/tunnel.py`+`tunnel_host.py` + `RunMeta.extra_http_headers` 搬运 context 级请求头）；确定性能力暴露（[0036](./0036-deterministic-capability-discovery.md)：注册即暴露——`@deterministic` 的 description/example 必填，worker 两个自述入口 `--list-deterministic`/`--match-steps`，CLI `list-deterministic --engine` + `plan` 的派发标注与冲突预检；匹配语义仍 100% 在 worker，不复刻进 core/CLI）。
- **v2.0.0（规模化）— ⬜ 留口子不实现**：WebUI 前端（直接调核心）。

## G1/G2 解析前置（声明语法已定，调度实现已落地）

G1/G2 是 v1.0 核心库 `.feature` 解析的前置——其声明语法**现已定（ADR 0019）**：

- **G1 — session scope 声明**：✅ `@scope:<name>` tag（相同值同 scope、串行共享会话；不同值并行；未标各自独立）。tag 两个引擎可读已验证。
- **G2 — 引擎选择**：✅ `@engine:<x>` tag 选引擎（scope 级属性、容错缺省、冲突报错）；v1.0 只选引擎不交叉。两个引擎路由已验证。
- 声明语法（[0019](./0019-feature-tags-scope-and-engine.md)）与**调度实现**（scope 串/并行、会话共享、冲突校验）均已落地：scope 分组 + engine/timeout 冲突校验见 [0025](./0025-plan-module-feature-to-jobs.md)（多值直接 `PlanError`），job 间并发/失败隔离/超时兜底见 [0026](./0026-schedule-module.md)；scope 内串行由 worker 消化。

## 现在做 / 现在不做

- **现在做（v1.0）**：核心库 `core/` 可被调用（逻辑不焊死在 CLI main 里）；钉死上面数据模型；定义 ports 接口（`Engine`/`RunStore`/`ResultStore`/`ReportStore`）+ 组合根注入；核心自解析 Gherkin + 薄 worker（[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)）。模块设计：worker↔core 协议见 [0024](./0024-worker-core-protocol.md)；plan 模块见 [0025](./0025-plan-module-feature-to-jobs.md)；schedule 模块见 [0026](./0026-schedule-module.md)。
  - **ports 落地状态**：四个 port 的 local adapter 均已建（详见上「留口子：Ports & Adapters」节）。**两个引擎 worker 均已落地**（`engines/{novaact,midscene}/worker/`），两个引擎对称、同讲 0024 协议。
- **现在不做**：无状态机制 / WebUI ——接口已留好，等云端真需要时填 adapter + 组合根换注入。**避免为想象中的云端预先盖机器。**（**已越过**：云端 store/执行 adapter + 组合根接线 + IaC 在 v1.1 填齐、**无状态跑批机制 v1.2 已实装真跑通**——清单见上「版本切分」的 v1.1.0/v1.2.0 行；但无状态跑批**不止「填 adapter」**、是驱动模型演进，故当初「等填 adapter」的乐观预期对它不成立，见上「这样上云…」处的 ⚠️ 分层注。）
- **G1/G2 声明语法已定**（ADR 0019）；其**调度实现**（scope 串/并行、会话共享、engine 冲突校验）已由核心库落地（[0025](./0025-plan-module-feature-to-jobs.md)/[0026](./0026-schedule-module.md)，见上「G1/G2 解析前置」节）。
- **多用例组织**：跑批入口（CLI 按路径跑一批）已落地；**按 tag 选子集仍未实现**——旧的 cucumber `--tags` 选子集约定随 BDD runner 一并退役（见 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)），核心调度层的 tag 过滤至今是留口子（`plan` 只接 feature 路径、无过滤参数；真需要时加 CLI 选择面 + plan 入口过滤，是加法）。**当初把它整体推给核心库的理由仍成立**：选子集依赖核心库的调度层，在（已退役的）bdd 直跑层做只是临时件、核心库终究会重做。`features/` 目前是 v0.x 打磨用例 + v1.0 起补的手工真跑验证夹具（并发/scope 共享、确定性锚点），仍未做目录/命名的有意组织。
