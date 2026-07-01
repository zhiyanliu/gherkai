# 执行架构：核心库（窄腰）+ Run 数据模型 + 留好状态存储的口子

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
- **两个引擎都子进程**（而非一个引擎进程内）：两个 `Engine` adapter 形状**完全一致**（spawn worker + 讲同一套 JSON 协议），核心不碰任一引擎 API，AgentCore 会话生命周期留在各自 worker（即现 `generic.steps.ts` Before/After、`nova_ctx` fixture 已跑通处）。这才是对称 `Engine` port 最干净的形态；一个引擎进程内会让 adapter 出现两种形状、核心 venv 被引擎依赖树绑死。
- **核心语言 = Python**：两个引擎都子进程后，核心是无重型引擎依赖的薄编排层，语言成为低风险自由选择；选 Python 因 boto3 生态成熟（便于未来云 adapter）+ 官方 `gherkin-official` 解析。
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

- **RunResult** = 机器可读汇总判定（退出码 / CI / WebUI 状态）= **definition（`run_meta`）+ 判定（`jobs`）的显式合成**（见下「三层切分」）。字段构成：`run_meta` + status 三态 + 各 job 结果 + `total_tokens`/`total_time_worked_s` 两个原生量各自跨 scope 合计 + `duration_ms` 总墙钟。其下 `JobResult` → `ScenarioResult` → `StepResult` 三层结果（core 保留 step 级粒度），各级带 `duration_ms` 墙钟时长（性能指标，与成本的 `time_worked_s` **正交**，见 [0024](./0024-worker-core-protocol.md)）。
- **RunReport** = 人看的归集报告（把两个引擎割裂的 Midscene html / Nova trajectory 归到一处）。**这是原 M5「报告统一」的归宿**——**v1.0 已实现（[0027](./0027-runreport-aggregation-index.md)）**：定为**跨引擎归集索引**（`manifest.json` 机器可读 + `index.html` 人可导航入口），**只索引/链接原生产物、不解析融合其内容**；新引擎报任意 `kind` 零改 core。由 `ReportStore` 从 `RunResult` 一次归集（cli 每次 run **默认生成**，`--no-report` 跳过）。

### 三层切分：definition / 控制面运行态 / 数据面判定（数据流向不从结果反推）

一次 run 的数据按**何时产生、谁拥有**切成三层，对应三种类型与三个 store：

| 层 | 内容 | 何时 | 类型 | store |
|---|---|---|---|---|
| **definition（前置身份）** | run_id + created_at + 跑哪些 job（完整 `Job`：scope/engine/scenarios/steps，"要跑什么"） | **执行前**确定（plan 产出 + 组合根生成 run_id） | `RunMeta`（持有 `tuple[Job,...]`，不另造 JobMeta） | `RunStore`（控制面） |
| **控制面运行态** | 总 status / 各 job status / 会话血缘 sessionId / 起止 | **执行后**产生（实时写下随进度增量刷，[0030](./0030-realtime-persistence-seam.md)） | `RunState`（`jobs: Map<scope_id, JobState>`，按 scope_id 定位单 job 实时刷；落盘 JSON 仍 list） | `RunStore`（控制面） |
| **数据面判定明细** | 每 scenario/step 的 pass-fail、投票、cost、报告指针 | **执行后**产生 | `JobResult`→`ScenarioResult`→`StepResult` | `ResultStore`（数据面，判定真值唯一权威） |

- **数据流向单向、不从结果反推**：`features → plan → Job[] → 组合根生成 run_id → RunMeta → schedule(run_meta) → RunResult`。`RunMeta`（definition）是 schedule 的**输入**、不是从 `RunResult` 反抽——run 的身份执行前就定了。`schedule` 把 `run_meta` 原样放进 `RunResult`（合成），并归约出判定。`RunState` 由 `run_state_from_result(result)` 投影（投影**运行态**字段 status/session_id，非反推 definition 身份——scope_id 取自 `jr.job`，本就在 definition 里）。
- **`RunResult` = `RunMeta` + 判定的显式合成**：`JobResult` **持有 `Job`**（definition）而非重复抄它的 scope_id/scope_name/engine——消除「抄字段抄漏」（旧版抄了 engine 漏了 scope_name），存储唯一、读法经 property 稳定。
- **status 不进 `RunMeta`**：status 是判定派生（执行后），属控制面运行态/数据面，不是 definition。
- **「执行中实时更新状态」靠 schedule 的旁路注入点（`on_event`/`on_job_complete`）让组合根落库，不靠 schedule 持有 store**：schedule 保持纯归约、不依赖任何 store；落库编排收在组合根注入的 `RunPersistence`（[0030](./0030-realtime-persistence-seam.md)）。**已落地**——cli 经此实时写 RunState（RUNNING 中间态）+ ResultStore（每 job 判定），WebUI 轮询面可直接复用。（早期设计曾设想让落库走 sink，已被 [0030](./0030-realtime-persistence-seam.md) 否决——sink 被 sink_lock 串行化、只留给进度显示，落库走独立的 on_event/on_job_complete。）

**已定 = 概念/层级（上表 + 三层切分）+ 协议层字段（[0024](./0024-worker-core-protocol.md)）**：每 scenario 判定（status 三态）、抖动投票 tally、规范化 errorType、cost 信封、报告产物指针（reportRefs）等 **scenario/scope 级字段已由 worker↔core 协议钉死**——它们是 RunResult/RunReport 的字段来源。**仍未定 = 持久化层 Run/Job 级字段**（runId / jobId(scopeId) / 会话血缘 sessionId / 起止时间 / DDB 表结构 / WebUI 读取面）：有意留到 v1.0 真实跑批逼出（"报告要展示什么、CI 要读什么"届时自然浮现），避免现在纸上列错。（原计划在 v0.x 逼出，但 v0.x 判「方向已证」未做真实用例验收，顺延 v1.0，见下「版本切分」。）

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
> - **worker 模式**（subprocess：产物落本地、报 `file://` ref / 未来 Fargate：产物**由 worker 自己上传 S3**、报 `s3://` ref，[0029](./0029-fargate-engine-artifacts-to-s3.md)）——**产物怎么持久化是 per-worker by-design 的事，不归 store**。
> - **store adapter**（Local/DDB/S3）——只持久化 **core 自己的序列化数据**（RunMeta/RunState/JobResult/RunReport），并**不透明搬运** worker 报的 `ref`（`ResourceUri`，[0027](./0027-runreport-aggregation-index.md)）。store **不上传 worker 产物**。
> - 二者是**矩阵不是绑定**：如 Local store + Fargate worker 合法（core 数据落本地、worker 产物在 S3）。`ReportStore.write(materialize=...)` 决定「要不要把 worker 产物拉进 report 自包含」——与 worker 把产物放哪正交（materialize 语义见 [0027](./0027-runreport-aggregation-index.md)）。

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

**当前实装**：四个 port 的 local adapter **均已建**（`subprocess_engine.py` / `run_store/` / `result_store/` / `report_store/`，方法签名以代码与上「按关注点拆 port」节的契约描述为准）。判定结果不再仅在内存，cli 跑完落 `<report-dir>/<run_id>/`（`run_meta.json` + `run_state.json` + `jobs/` + RunReport）。**克制**：store adapter 只忠实持久化已成形的 `RunMeta`/`RunState`/`JobResult`（复用 `serialize` 单一序列化真理源），**未发明** jobId/DDB 表/轮询续跑读取面那些字段——它们仍 defer，待真实续跑/轮询/WebUI 需求逼出（见上「数据模型」节字段级 schema 顺延）。云端再填 DDB/S3/Fargate。

**选实现 = 组合根注入，不是 module 自选**（关键，避开本会话踩过的坑）：
- 接口定义在 `ports`；**具体 adapter 由调用方（CLI 的 main / WebUI 的 bootstrap = 组合根）在启动时注入**给核心。核心只认接口。
- **禁止** ports module 内部用全局单例 + `env`-sniff 自选实现——那正是本项目踩过的 Midscene `GlobalConfigManager` 反模式（import 时缓存 env、运行时改不动、难测）。注入式可测、无隐藏全局。

**rule-of-three 克制**：接口 v1.0 先定（廉价，还逼清边界）、只写 local adapter；v1.1 云端真需要时填云端 adapter——**store 层（RunStore→DDB、Result/ReportStore→S3）已填**（第五刀，[0030](./0030-realtime-persistence-seam.md) 决定六），执行面 Fargate adapter 仍待填。

这样无状态化、上云、WebUI 接入都成了"加 adapter + 组合根换注入"，核心与接口不动。

### cli `--backend {local,cloud}`：组合根按开关注入两套 store（兑现「换 adapter 核心不动」）

云端 store adapter（DDB/S3，[0030](./0030-realtime-persistence-seam.md) 决定六）落地后，cli 加 `--backend {local,cloud}`（默认 `local`，仅 `run` 子命令——`plan` 纯本地不落库）在组合根按开关选注入哪套 adapter。`RunPersistence`/`schedule` 只认 Store **port**，local↔cloud 切换**零改** core——这正是本 ADR「选实现=组合根注入」的第一次真实兑现。

**单一开关换齐三层、第一版不开混搭**：cloud 一次把 RunStore→DDB、ResultStore/ReportStore→S3（+ 挂 offloader）全换。理由：三层后端不对等（上文已证不存在 `S3RunStore`/`DDBReportStore`），无有意义的混搭矩阵；「Local store + Fargate worker」是 **store⊥worker 正交轴**（上文「worker 产物 ⊥ store」）、非 store 层内部混搭，不需要 `--run-backend`/`--result-backend` 拆开（那是提前盖机器 + 组合爆炸测试负担）。

**装配落点分裂（被测试护栏逼出的务实取舍，非纯度选择）**：
- **local 分支留在 `__main__`**：直接 new 模块级 `LocalRunStore/LocalResultStore/LocalReportStore`（签名 `(root)→store`）。这三个名字是既定的**测试注入点**（cli 测试 `monkeypatch m.Local*` 注入 fake 验实时写序）；若把 local 分支挪进 `compose`，闭包绑到 compose 自己的 import、patch 打不中，且 `__main__`→`compose` 反向引用成循环依赖。
- **cloud 分支下沉 `compose.build_cloud_stores`**：`import boto3` 惰性收在函数体内（cli 主依赖不含 boto3，走 `cli[aws]→core[aws]` extra；纯 local 路径绝不触发 import）。造 boto3 句柄抽成可 patch 的小钩子，cli 测试**只验接线层**（backend=cloud 构造了正确 adapter + 参数正确 + offloader 已挂），不引 moto——adapter 行为已由 core 包 moto 全覆盖，cli 再测是重复且破窄腰。
- **注入点约定**：local patch `m.Local*`、cloud patch `compose` 的 boto3 钩子——两皮各测各的注入点。
- **两种 boto3 句柄别混**（静默出错高危）：`DynamoDBRunStore` 吃 `resource.Table`（内部 `self._table.put_item`/`.meta.client`），三个 S3 件套（ResultStore/ReportStore/offloader）**共享一个** `client`。喂错句柄类型运行时才 AttributeError、moto/cli 都测不到。
- **trade-off**：local 分支不能迁进 compose（否则失 monkeypatch 命中）牺牲了「组合根装配全在 compose」的语义纯度，换零回归——接受。

**cloud 配置来源 + 落点语义**：
- 表/桶经参数注入（`--ddb-table` 兜底 `AWS_DDB_TABLE`、`--s3-bucket` 兜底 `AWS_S3_BUCKET`）；region/凭证/profile **代码零介入**，走 boto3 默认解析链（组合根不持 IAM 知识、不硬编码凭证；约束已定 us-east-1 + default profile）。adapter 假定表/桶已存在（建表建桶归 IaC）。（`AWS_DDB_TABLE`/`AWS_S3_BUCKET` 与集成测试 `tests/README.md` 用的同名——语义一致「哪张表/哪个桶」、不同进程不冲突。）
- **单 S3 桶 + `--report-dir` 复用为 key 前缀**：Result(`jobs/`)、Report(`index.html`)、offloader(`args/`) 三者 key 前缀天然不撞，共用一个桶最简；不新增 `--s3-prefix`——local 的 `<report-dir>/<run_id>/…` 与 cloud 的 `s3://bucket/<report-dir>/<run_id>/…` 布局工整对应。**分隔符规范化**：`--report-dir` 默认 `reports`（无尾 `/`），组合根在传给 S3 adapter 前补 `/`（非空且不以 `/` 结尾则补），否则 `S3*Store` 拼 `f"{prefix}{run_id}"` 会静默生成粘连 key `reports<run_id>/…`。真需分桶（report 公开 serve vs result 私有的生命周期策略）再拆，加法不返工。
- **`--backend cloud --no-report` 合法**：`--no-report` 既有语义=零落盘裸跑、与 backend 正交；所有云端校验/import/异常 gated 在 `need_cloud = do_report and cloud`，此组合跳过一切云端检查（保「三个 store 一次不构造」的逃生舱）。

**artifacts 落点指针按 backend 分支组装、全 URI 化（不硬编码本地路径「说谎」）**：`--json` 的 `artifacts` dict（`report_index`/`run_meta`/`run_state`/`jobs_dir`）现状硬编码本地文件路径，cloud 下这些数据落 DDB/S3、本地路径不存在——必须按 backend 分支：
- local：四项均 `file://` 完整路径（从裸路径升级为 URI，与 cloud 同形工整）。
- cloud：`report_index`（取 `finalize()` 返回值）/`jobs_dir` = `s3://…`；`run_meta`/`run_state` = 自造 `ddb://<table>/<run_id>#META|#STATE` 诊断指针（与 s3:// 同形、纯展示、不被任何代码解析）。
- 指针由 `compose.build_cloud_stores` 连同三个 store 实例一起返回（已知 table/bucket/prefix），`_cmd_run` 直接填——**不给 Store port 加 `describe_artifacts`**（凭空扩接口面、6 个 adapter 全要实现，过度设计）。
- `finalize()` 返回 None（`S3ReportStore.write` 失败被 `RunPersistence` 隔离，[0030](./0030-realtime-persistence-seam.md) 决定三）时 `report_index` 键不放裸 `'None'`——省略该键、可选把 `_report_error` 打一行 stderr。

## 工程布局：core / cli / engines 三者平级对标

**当前实装态（v1.0 进行中）**标在各行右侧 ✅/⬜：core/ 已建、cli/ 已建、engines/ 已迁、两个引擎 worker 已落地。

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
  - **实际达成**：用**骨架用例**（wikipedia / example.com，见 CONTEXT「骨架验证用例」）覆盖了单步/多步复合/开放动作/AI 布尔·否定·取数·取串断言/主观判定/tag 路由，**全程 QA 零代码**，两个引擎都跑通——可行性**方向已证**。
  - **决定（边界，务必读）**：**v0.1.0 判「方向已证」，不补真实用例即进 v1.0.0**。理由——① 团队当前**拿不到真实业务用例**（站点登录态等不可得），强等是空等；② 没有真实用例 → 破例无从触发 → **「破例清单」这条验收无法在 v0.x 执行**。故把「真实业务用例验收 + 破例记录」**顺延并入 v1.0.0**：待有真实用例时在 v1.0 里跑出破例、据以校验「QA 零代码」承诺。**已知风险**：v1.0 架构基于「骨架用例都很顺」的乐观假设设计，真实用例的破例（登录 / HITL / 动态内容 flaky）可能反过来要求调整 v1.0 架构——接受此返工风险，因前置条件（真实用例）确实不具备。
  - **报告**：v0.x 原目标含「报告能看」，当时**决定先「散着」**（手动查目录够用），归集形态待要求清晰再定。**v1.0 已落地为 RunReport 归集索引**（[0027](./0027-runreport-aggregation-index.md)）：不重渲染原生产物、只归集成统一清单 + 导航入口——回答了「先散着」时悬而未决的形态问题（索引而非融合）。
- **v1.0.0（团队 QA 日常可用）— ⏳ 架构设计中（本 ADR + 0022/0023）**：多用例组织、跑批入口（CLI 阻塞跑一批）、scope 调度、抖动治理（投票）落地；本地执行。**承接 v0.x 顺延项**：真实业务用例验收 + 破例清单（RunReport 归集已落地，[0027](./0027-runreport-aggregation-index.md)）。
- **v1.1.0（云端执行）— 🚧 进行中**：CLI 提交 → Fargate 跑 → 轮询收集，**job = scope** 粒度（上云时坐实，见 [0017](./0017-cloud-execution-fargate-over-runtime.md)）；外置状态存储（DDB，主要服务 `RunStore`）+ 无状态核心。**= 加 adapter + 组合根换注入，核心不动**。**已落地**：实时写存储接缝（schedule 的 on_event/on_job_complete 旁路 + `RunPersistence` 编排 + RunStore 三增量方法，[0030](./0030-realtime-persistence-seam.md)）+ job 生命周期态/severity（[0031](./0031-job-lifecycle-states-and-severity.md)）+ **云端 store adapter（DynamoDBRunStore + S3ResultStore + S3ReportStore + StepArgument offload，moto 单测对拍 local，[0030](./0030-realtime-persistence-seam.md) 决定六）**——坐实了「换 adapter 核心不动」。**待做**：把云端 adapter 接进组合根（cli `--backend` 分片）+ Fargate 执行 adapter + 无状态跑批。
- **v2.0.0（规模化）— ⬜ 留口子不实现**：WebUI 前端（直接调核心）。

## G1/G2 解析前置（声明语法已定，调度实现待 v1.0）

G1/G2 是 v1.0 核心库 `.feature` 解析的前置——其声明语法**现已定（ADR 0019）**：

- **G1 — session scope 声明**：✅ `@scope:<name>` tag（相同值同 scope、串行共享会话；不同值并行；未标各自独立）。tag 两个引擎可读已验证。
- **G2 — 引擎选择**：✅ `@engine:<x>` tag 选引擎（scope 级属性、容错缺省、冲突报错）；v1.0 只选引擎不交叉。两个引擎路由已验证。
- 声明语法已定，但**调度实现**（scope 串/并行、会话共享、冲突校验）仍待 v1.0 核心库。

## 现在做 / 现在不做

- **现在做（v1.0）**：核心库 `core/` 可被调用（逻辑不焊死在 CLI main 里）；钉死上面数据模型；定义 ports 接口（`Engine`/`RunStore`/`ResultStore`/`ReportStore`）+ 组合根注入；核心自解析 Gherkin + 薄 worker（[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)）。模块设计：worker↔core 协议见 [0024](./0024-worker-core-protocol.md)；plan 模块见 [0025](./0025-plan-module-feature-to-jobs.md)；schedule 模块见 [0026](./0026-schedule-module.md)。
  - **ports 落地状态**：四个 port 的 local adapter 均已建（详见上「留口子：Ports & Adapters」节）。**两个引擎 worker 均已落地**（`engines/{novaact,midscene}/worker/`），两个引擎对称、同讲 0024 协议。
- **现在不做**：Fargate 执行 adapter / 无状态机制 / WebUI ——接口已留好，等云端真需要时填 adapter + 组合根换注入。**避免为想象中的云端预先盖机器。**（**已越过**：DynamoDB/S3 store adapter 在 v1.1 第五刀已填，[0030](./0030-realtime-persistence-seam.md) 决定六。）
- **G1/G2 声明语法已定**（ADR 0019）；其**调度实现**（scope 串/并行、会话共享、engine 冲突校验）由 v1.0 核心库落地。
- **多用例组织**（feature 分目录/命名约定、跑批入口、跑批层选择 feature/tag）同样由 v1.0 核心库落地——它依赖核心库的调度层，在 bdd 直跑层做是临时的、核心库会重做。当前 `features/` 下多个文件仅是 v0.x 打磨产物，未做有意组织。（旧的 cucumber `--tags` 选子集约定随 BDD runner 一并退役，见 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)；选子集改由核心调度层据 tag 实现。）
