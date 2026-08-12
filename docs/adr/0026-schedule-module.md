# schedule 模块：job 间并发调度 + 失败隔离 + 优雅终止

> **Status:** Partially-superseded-by 0034 —— 纯 reducer 红线仍守（副作用仍在 adapter/组合根、core 不 import boto3）、同步 `run` 路径的 schedule 驱动循环不变；仅「上云只换 adapter、schedule 一行不改」对**异步 submit（CLI 脱离）路径**不成立、被 [0034](./0034-detached-batch-reconciler.md) 纠正（见下「优雅终止」段与「现在做 / 留口子」段的 ⚠️ 注）：该路径把同步驱动循环解体为无状态事件驱动 reconciler、抽出纯 `project`/`plan_next`。

核心库把 plan 产出的 **job 列表**（[0025](./0025-plan-module-feature-to-jobs.md)）实际跑起来的模块：决定哪些 job 并行、控并发、起 worker、收流式事件、隔离失败、超时兜底。它兑现 [0016](./0016-execution-architecture-core-lib-run-model.md)/[0019](./0019-feature-tags-scope-and-engine.md) 留给核心库的「scope 串/并行调度、会话共享」。它是 v1.0 核心三模块的最后一块（协议 [0024](./0024-worker-core-protocol.md) → plan [0025](./0025-plan-module-feature-to-jobs.md) → schedule 本 ADR）。

## 接口（深模块，小）

```
schedule(run_meta: RunMeta, engines: EngineResolver, sink: (event) -> void, opts,
         on_job_complete?: (JobResult) -> void, on_event?: (event) -> void) -> RunResult
   // RunMeta: 一次 run 的 definition（run_id + created_at + jobs: Job[]），组合根执行前生成/组装（ADR 0016/0027）
   //          schedule 把 run_meta 原样放进 RunResult（合成）+ 归约判定，不自己生成 run_id
   // EngineResolver: (engineName) -> Engine —— 按 job.engine 解析 Engine，schedule 对引擎数/引擎名无知
   // sink: 接收 0024 原始流式事件的回调（pass-through，仅供进度显示；被 sink_lock 串行化）
   // on_job_complete/on_event: 实时写接缝的两个旁路注入点（默认空），落库走它们、不走 sink（ADR 0030）

opts = {                 // 时间单位统一为秒；代码字段名带 _s 后缀（job_timeout_s/grace_period_s）
  maxConcurrency = 4,    // 同时在跑的 worker 上限
  failFast = false,      // 任一 job 崩是否中止整批
  jobTimeout = null,     // per-job 墙钟超时（秒；null=不超时；超时记 status:error + errorType:timeout）
  gracePeriod = 5,       // 停止请求后等 worker 优雅退出的宽限秒，超期强杀
  clock,                 // 时间源（可注入 fake clock 单测超时/grace 路径；默认 monotonic，抗系统时钟回拨）
}
```
（上为语言中立伪代码；实际实现为 dataclass `ScheduleOpts`，字段 snake_case：`max_concurrency`/`fail_fast`/`job_timeout_s`/`grace_period_s`/`min_grace_s`（默认 0.0，grace 下限，引擎无关纯数、组合根按引擎算好传入，schedule enforce `grace ≥ min_grace_s`，见 [0024](./0024-worker-core-protocol.md) grace 硬约束）/`clock`/`network_retry`（默认 0）/`retry_sleep`/`heartbeat_interval_s`（默认 0.5，静默 worker 超时兜底轮询间隔，见下「静默 worker 的超时如何触发」）（[0028](./0028-transient-network-ssl-resilience.md)）。）

- **注入 `engines`（`EngineResolver`：按 `job.engine` 解析 Engine）而非自己 spawn** → 可测（skill：accept dependencies, don't create them）：测试注入假 Engine（吐预设 JSON Lines，[0024](./0024-worker-core-protocol.md)）即可验调度逻辑，无需真起子进程/真连 AgentCore。**schedule 对引擎数/引擎名无知**——焊死 `{midscene, novaact}` 会让第三个引擎到来即改接口；用 resolver 则只动组合根注入。
- **注入 `sink`**（`(event) -> void` 回调，仅供 CLI 打印进度）→ schedule 边收边转，不自己决定结果存哪（[0016](./0016-execution-architecture-core-lib-run-model.md) ports）。**实时落库不走 sink**——走 `on_event`（事件旁路，在 sink_lock 外刷 RUNNING 中间态）/ `on_job_complete`（job 完成落判定真值），由组合根的 `RunPersistence` 编排（[0030](./0030-realtime-persistence-seam.md)）。（RunReport 也不走 sink——它由 `ReportStore.write` 从归约后的 `RunResult` 派生，[0027](./0027-runreport-aggregation-index.md)。）
- **`sink` vs `RunResult` 边界（不是两次独立判定）**：`sink` 收的是 [0024](./0024-worker-core-protocol.md) **原始流式事件**（pass-through，供实时进度）；`RunResult` 是 schedule 对**同一事件流的归约终值**（权威汇总判定，给退出码/CI）。同一份事实的两个视图——流式过程 vs 终态归约，非两套判定来源。
- **注入 `clock`**（时间源）→ 超时杀 / grace→kill 这两条 schedule 独有难逻辑可用 fake clock 确定性单测，不靠真实墙钟等待。
- **返回 `RunResult`**（机器可读汇总判定，给退出码/CI，[0016](./0016-execution-architecture-core-lib-run-model.md)）。
- **删除测试**：删掉本模块，「并发控制 + worker 生命周期 + 失败隔离 + 超时兜底」会散进 CLI/WebUI 各写一遍 → 它在挣钱。

## 核心职责

### job 间并行（scope 内串行已被 worker 消化）

- **job = scope = 会话边界**（[0016](./0016-execution-architecture-core-lib-run-model.md)）。「scope 内串行」由 worker 自己完成（一个 worker 顺序跑完该 scope 全部 scenario、共享一个会话，[0024](./0024-worker-core-protocol.md)）。
- 故 schedule 层面 = **job 之间并行**：每个 job 经 `engines(job.engine)` 解析出 Engine、起一个 worker，彼此独立。

### 并发上限（保护真实 AWS 成本/配额）

- `maxConcurrency` 默认 **4**（保守）：每个并行 worker = 一个 AgentCore 会话 + 持续模型调用，**真实烧钱**（[0024](./0024-worker-core-protocol.md) cost）。超出上限的 job 排队，有 worker 退出腾出槽位再起下一个。
- 是**注入参数 + 保守默认**，不写死——本地全量可调高、配额紧可调低。

### 失败隔离（默认隔离，可配 fail-fast）

- **默认 `failFast = false`（隔离）**：一个 worker 崩（异常退出 / 超时）→ 该 job 记 `error`（区别于 scenario 级 `failed`，[0024](./0024-worker-core-protocol.md) status 语义），**其余独立 job 照跑**。一轮拿到最大限度结果，不因一个 flaky job 重跑整批。
- **可配 `failFast = true`**：任一 job 崩 → 立即优雅终止所有在跑 worker、中止整批。CI 门禁省钱省时（早停）。
- 两种诉求相反（全量跑批要隔离 / CI 要早停），故做成旋钮、不二选一焊死。

### 超时兜底

- `jobTimeout`（per-job 墙钟，可配，默认 null=不超时）：防一个 job 卡死（AI 死循环 / 网络挂）永久占用并发槽位 + 烧钱。超时 → 优雅终止该 worker（走下文终止契约：停止请求→宽限→强杀）、记 `status:error` + `errorType:timeout`（[0024](./0024-worker-core-protocol.md) status 三态 + 规范化 errorType）。
- 引擎 SDK 各自也有超时（Midscene/Nova Act 都有），但那只覆盖「引擎调用内」卡住；**进程层面卡死（非引擎调用内）只有 schedule 能兜**，故 schedule 这层超时是必要的外层保险。
- **静默 worker 的超时如何触发**：超时检查在「每收一个事件后」做。worker 完全静默（卡在单次操作内、事件通道零输出）时，事件循环会阻塞在读上、检查永不触发（曾致 300s 超时拖到 ~620s）。故 schedule 用 `_heartbeat_wrap`（后台 reader 线程把 adapter 的纯 `Iterator[Event]` 喂进队列，主侧 `queue.get(timeout=heartbeat_interval_s)` 超时即注入存活心跳）让循环周期性醒来查超时——**心跳在 schedule 层做一次、对所有 adapter 通用，Engine port 保持纯 `Iterator[Event]`**（机制细节见 [0028](./0028-transient-network-ssl-resilience.md)）。

### 网络瞬时故障的 job 级重试（[0028](./0028-transient-network-ssl-resilience.md)）

- worker 建连失败、重试耗尽 → 以专用退出码退出 → adapter 抛 `WorkerNetworkError` → schedule 记 `error_type="network_error"`。
- schedule 对这类 job **选择性整体重试**（重新 spawn worker），门槛双条件 AND：① `network_error` ② 「会话未起」= 本次零 `step_done`（证明 act 没跑、无副作用——绝不重试可能已点击的 act）。**fail_fast/timeout 优先级更高**（已主动中止的不重跑）。
- `ScheduleOpts` 加 `network_retry: int = 0`（默认关,本地 smoke 不需要;CI/抖动环境可开,同「注入参数+保守默认」原则）+ `retry_sleep`（注入,单测传 no-op 保 fake-clock 纯净）。`job_timeout` deadline 跨 attempt 不重置。

### 优雅终止（schedule 只下逻辑「停」指令，机制归 adapter）

「怎么停」的具体机制**不在 schedule**——本模块只负责下逻辑指令，机制/会话清理归 adapter 与 worker（三层完整机制见 [0024](./0024-worker-core-protocol.md) 终止契约节，此处只钉本模块边界，不复述以免漂移）：
- **schedule → WorkerHandle**（本模块职责）：只调逻辑指令 `handle.stop(gracePeriod)`（「请停这个 worker」）。`handle` 由 `engine.run_scope(job)` 返回、schedule 持有；`Engine` port **只有 `run_scope`、不挂 stop**（句柄自己知道怎么停）。schedule **不懂** SIGTERM/进程/StopTask——只知道「下停止指令、等归约」。
- **机制层与会话清理**（转指针）：adapter 把逻辑「停」翻成具体机制（子进程 SIGTERM+宽限+SIGKILL / 未来 Fargate `StopTask`）、会话清理（`StopBrowserSession`）归 worker——**故「停止机制上云只换 adapter」成立**（见下「留口子」），schedule 一行不改。机制细节 + 两引擎会话释放见 [0024](./0024-worker-core-protocol.md) 终止契约 + [0028](./0028-transient-network-ssl-resilience.md) Midscene 会话集清理。（**⚠️ 此处「一行不改」限于「停止机制」这一层**——驱动循环整体的演进是另一回事、非「换 adapter」能覆盖，见下「留口子」段 ⚠️ 注。）（SIGKILL 硬杀致会话释放落空的低频泄漏由 AgentCore session TTL 兜底、**不引入 core reaper**，见 [0024](./0024-worker-core-protocol.md) 终止契约「已接受代价」——schedule/core 纯度不变。）

> **进程拓扑（澄清「几个地方」）**：实际是 **2 进程 + 1 远程 + 1 seam**——①core/schedule 进程；②`Engine` adapter（在 core 进程内，但它是通向「进程/云」世界的 seam，「怎么停」知识归这里）；③worker 子进程（engine SDK 是**进程内的库**、非独立进程）；④远程 AgentCore 浏览器会话（云端、worker 经 CDP 连）。engine SDK 拆除 + 会话停止都在 worker 进程内完成。

### 事件归集（status + 原生量成本 + 墙钟时长 三级归约）

- 边收 worker 的流式事件（[0024](./0024-worker-core-protocol.md) JSON Lines，七类：`scope_started`/`scenario_started`/`step_started`/`step_done`/`step_skipped`/`scenario_done`/`scope_done`；`step_skipped` = scope 内短路，见下 status 归约与 [0031](./0031-job-lifecycle-states-and-severity.md) 决定六）边转给 `sink`；归约成 `RunResult`。
- 多 worker 并行 → 多路事件流交错，schedule 按 `scopeId`/`scenarioId` 归位（[0024](./0024-worker-core-protocol.md) 标识键）。
- **status 归约**：scenario → job（任一 error→error / 任一 failed→failed / 全 passed→passed）→ run（同规则跨 job，但**入口先滤掉非终态判定** skipped/aborted/pending/running，即 `_NON_VERDICT`，run 级只看真正出了判定的 job，见 [0031](./0031-job-lifecycle-states-and-severity.md) 决定三）。job 级除 worker 三态外，core 在 fail-fast 时还会派生 `skipped`（排队没起）/`aborted`（跑一半被掐）终态（[0031](./0031-job-lifecycle-states-and-severity.md)）。
- **job 级乐观归约的内容完整前置（[0024](./0024-worker-core-protocol.md)「事件流内容完整与进程终止是两件事、都要」在同步路径的落点；首轮 code-health 对抗验证逼出）**：事件流正常 EOF 后，job 落「scenario 归约终态」**须以见到 `scope_done` 为前提**——worker 被协作停（fail-fast/超时的 `handle.stop`）后按契约**不吐 in-flight 的 scenario_done/scope_done、干净退出**（exit 0），事件流自然 EOF；若不校验内容完整就直落归约，部分完成的 job 会拿「已完成的那几个 scenario」聚合出 PASSED（假绿——判定失真+ABORTED 现场丢失，探针复现：`--timeout 0` 时任意关停时序 100% 假绿、心跳只在特定时序偶然救回）。**未见 scope_done 时按来源分流**（对齐 `core.project._job_status` 的「干净退出无 scope_done → ERROR」口径、消同步/无状态两路判定分叉）：`abort_flag` 已置位 → ABORTED（fail-fast 掐停，[0031](./0031-job-lifecycle-states-and-severity.md) 决定一）；已超 deadline → error+timeout；其余 → error+engine_error（进程说成功、内容没发完=矛盾）。
- **`step_skipped` 归约（scope 内短路，不臆断因果的守法方式，[0031](./0031-job-lifecycle-states-and-severity.md) 决定六）**：worker 上游 step `error` 后短路后续 step、为每个发 `step_skipped`；core 归约成 `StepResult(status=skipped, shortcircuited=True)` 记进 step 明细，**但绝不把它写进 scenario 判定累加器**——scenario/job/run 判定只由那个上游 `error` step 决定，与"后面短路了几步"无关（step 级 skipped 零污染 scenario 归约/severity）。因果（"谁因谁短路"）只存在于 worker 的串行循环，core 作为纯 reducer 物理上看不到、也不臆断——它只忠实归约 worker 发来的 `step_skipped`，把"某步没跑"如实记进 `StepResult`。
- **成本归约**：core 只各自合计 engine 报的**原生量**——累加 `step_done.cost` 的 `tokens`/`time_worked_s` 成 `JobResult.total_tokens`/`total_time_worked_s`（scope 级），再跨 job 求和成 `RunResult.total_tokens`/`total_time_worked_s`（run 级）。**core 不折美元**（交消费者），无任何引擎报某量则该量 None、不假装 0（cost 信封见 [0024](./0024-worker-core-protocol.md)）。
- **墙钟时长归约**（性能指标，与成本正交）：core 用注入的 `clock` 在事件到达时打时间戳，按各级 `*_started`→`*_done` 算 `duration_ms`——step（`StepResult.duration_ms`）、scenario、scope（`JobResult.duration_ms`）、run（`RunResult.duration_ms`，schedule 整体包住、含并发）。core 首次保留 step 级粒度（`StepResult` 层）。

## 治理旋钮 = 注入参数 + 保守默认（贯穿原则）

`maxConcurrency` / `failFast` / `jobTimeout` / `gracePeriod` / `clock` 全部是 `opts`/参数注入、带保守默认，**不写死在实现里**——同 [0016](./0016-execution-architecture-core-lib-run-model.md) 组合根注入精神：策略由调用方（CLI/未来 WebUI）定，核心只认参数。

## 现在做 / 留口子

- **现在做（v1.0）**：上述接口、job 间并发（上限+排队）、失败隔离（默认隔离/可配 fail-fast）、超时兜底、优雅终止（schedule 调 `handle.stop(grace)`；子进程 handle 内 SIGTERM+宽限+SIGKILL）、事件归集成 RunResult（status + 原生量成本 + 墙钟时长 三级归约）。
- **留口子不实现**：core→worker 控制流（暂停/取消单 scenario/动态调度，等真需求，见 [0024](./0024-worker-core-protocol.md) 终止契约节）；跨 job 的智能调度（按成本/优先级排序，现 FIFO 排队即可）；云端分布式调度（v1.1 Fargate，[0017](./0017-cloud-execution-fargate-over-runtime.md)，那时「起 worker」从 spawn 子进程换成提交 Fargate task、`handle.stop` 从发信号换成 StopTask，**均在 Engine adapter / WorkerHandle 内部，schedule 接口/旋钮不变**——**这一层已由 [0033](./0033-iac-aws-backend-and-composition-wiring.md) FargateEngine 真部署真跑证实**）。**⚠️ 但「schedule 一行不改」只覆盖「执行 adapter 替换」、未预见「CLI 脱离」这一步**（[0034](./0034-detached-batch-reconciler.md) v1.2 纠正）：无状态 `submit`（提交即走）要求把 schedule 当前的**同步驱动循环本身**（`ThreadPoolExecutor` 起全部 worker 线程 + `as_completed` 收敛 + `abort_flag`/fail-fast `_stop_all` 进程内并发闸）解体——因为 CLI 一退，这个循环没人驱动了。异步路径把它换成**无状态事件驱动 reconciler**（被事件唤醒、读全量 events 重放、CAS 推进），并从 schedule 抽出纯 `project(events)→RunState`/`plan_next(RunState)→actions` 供 Lambda/per-run 两宿主复用。**存活的是纯归约器、消失的是同步驱动循环**；纯 reducer 红线仍守（CAS/RunTask/PutItem 副作用仍在 adapter/组合根、core 不 import boto3）。同步 `run` 路径仍用现驱动循环——两种驱动模型按命令并存。故此条「schedule 接口/旋钮不变」对无状态跑批**不成立**，见 [0034](./0034-detached-batch-reconciler.md)。

## 重议

- 若并发/超时的保守默认在真实跑批中被证明不合适 → 调默认值（参数本就可配，不动接口）。
- 若出现「停」之外的控制需求 → 引入控制流通道（[0024](./0024-worker-core-protocol.md)），schedule 据此扩展。
