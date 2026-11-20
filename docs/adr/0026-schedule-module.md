# schedule 模块：job 间并发调度 + 失败隔离 + 优雅终止

> **Status:** Partially-superseded-by 0034, 0051 —— 纯 reducer 红线仍守（副作用仍在 adapter/组合根、core 不 import boto3），同步 `run` 路径仍用 schedule 的驱动循环；「上云只换 adapter、schedule 一行不改」对**异步 submit（CLI 脱离）路径**不成立、被 [0034](./0034-detached-batch-reconciler.md) 纠正（见下「优雅终止」段与「现在做 / 留口子」段的 ⚠️ 注）：该路径把同步驱动循环解体为无状态事件驱动 reconciler、抽出纯 `project`/`plan_next`。[0051](./0051-device-session-lifecycle-and-app-distribution.md) 改写本篇复述的三处，均已原位改写：未见 `scope_done` 时的判定收进两条归约路径共用的终结函数（[0034](./0034-detached-batch-reconciler.md) 机制二「终结函数与真值表」；「job 级乐观归约的内容完整前置」条的内容完整前置与拒绝假绿不变）；事件集加 `session_opened` / `session_closed`；job 级网络重试门槛由双条件改为三条件（加「job 目标不是设备」，见 [0028](./0028-transient-network-ssl-resilience.md)）。其余条文不变。这一篇描述的设计有一部分尚未实装，code 跟上之前，实际行为以 code 为准。

核心库把 plan 产出的 **job 列表**（[0025](./0025-plan-module-feature-to-jobs.md)）实际跑起来的模块：决定哪些 job 并行、控并发、起 worker、收流式事件、隔离失败、超时兜底。它兑现 [0016](./0016-execution-architecture-core-lib-run-model.md)/[0019](./0019-feature-tags-scope-and-engine.md) 留给核心库的「scope 串/并行调度、会话共享」。它是 v1.0 核心三模块的最后一块（协议 [0024](./0024-worker-core-protocol.md) → plan [0025](./0025-plan-module-feature-to-jobs.md) → schedule 本 ADR）。

## 接口（深模块，小）

```
schedule(run_meta: RunMeta, engines: EngineResolver, sink: (event) -> void, opts,
         on_job_complete?: (JobResult) -> void, on_event?: (event) -> void) -> Execution
   // RunMeta: 一次 run 的 definition（run_id + created_at + jobs: Job[] + 运行期限 deadline_at），组合根执行前生成/组装（ADR 0016/0027/0054）
   //          schedule 把 run_meta 原样放进 Execution，不自己生成 run_id
   // Execution: 这次执行观察到的事实——判出结果的 job（JobResult，按运行定义的次序；没有启动的 job，以及重试之前发现 run 已被
   //          别处结束而不采用的结果，不在其中；落库服务得知 run 已结束之后拒收的结果仍可能在其中，有记录时以记录为准）、
   //          余下的 job 不再启动的来源（最先登记的那一条）、整体墙钟时长；run 与 job 的状态不在其中，
   //          有记录时取运行态，没有记录时按同一套规则在内存里算出（ADR 0030 决定二）
   // EngineResolver: (engineName) -> Engine —— 按 job.engine 解析 Engine，schedule 对引擎数/引擎名无知
   // sink: 接收 0024 原始流式事件的回调（pass-through，仅供进度显示；被 sink_lock 串行化）
   // on_job_complete/on_event: 实时写接缝的两个旁路注入点（默认空），落库走它们、不走 sink（ADR 0030）

opts = {                 // 时间单位统一为秒；代码字段名带 _s 后缀（grace_period_s/heartbeat_interval_s）
  maxConcurrency = 4,    // 同时在跑的 worker 上限
  failFast = false,      // 任一 job 崩是否中止整批
  gracePeriod = 5,       // 停止请求后等 worker 优雅退出的宽限秒，超期强杀
  clock,                 // 单调时钟：只管不进记录的时长（停止请求时刻与排空上界、各级时长）；默认 monotonic，可注入 fake clock
  wallClock,             // 墙钟：认领时刻、job 的截止时刻、停止启动的时刻都按它比较（ADR 0054 决策二）；组合根注入，默认系统墙钟
  record,                // 这次 run 的记录：认领、重试之前的读、停手信号三项能力（ADR 0054 决策五）；不注入即没有记录的执行（--no-report）
  interrupt,             // 使用方中断的轮询回调（返回 0 / 1 / 2：无 / 协作停止 / 强制），不注入则不轮询（0024 终止契约）
  onInterrupt,           // 级别首次升高时的通知回调，供组合根提示使用方
  interruptPoll = 0.5,   // 使用方中断与停手信号的轮询间隔秒（两者同一节拍）
}
```
（上为语言中立伪代码；实际实现为 dataclass `ScheduleOpts`，字段 snake_case：`max_concurrency`/`fail_fast`/`grace_period_s`/`min_grace_s`（默认 0.0，grace 下限，引擎无关纯数、组合根按引擎向 worker 查自报值后传入，schedule enforce `grace ≥ min_grace_s`，见 [0024](./0024-worker-core-protocol.md) grace 硬约束）/`clock`/`wall_clock`（默认 `run_deadline.system_wall_clock`）/`record`（默认 None，类型是 `ports.RunRecord`，落库服务 `RunPersistence` 实现它）/`network_retry`（默认 0）/`retry_sleep`/`heartbeat_interval_s`（默认 0.5，静默 worker 超时兜底轮询间隔，见下「静默 worker 的超时如何触发」）（[0028](./0028-transient-network-ssl-resilience.md)）/`interrupt`（默认 None，中断级别轮询回调）/`on_interrupt`（默认 None，级别首次升高时的通知回调）/`interrupt_poll_s`（默认 0.5，注入了 `interrupt` 或 `record` 时生效））。

**per-job 墙钟预算不在 `opts`**——载体是 definition 的 `Job.timeout_s`（`@timeout:N` tag / CLI `--default-job-timeout` 在组合根解析定值，见 [0019](./0019-feature-tags-scope-and-engine.md)/[0034](./0034-detached-batch-reconciler.md)），schedule 认领 job 时据它与运行期限算截止时刻（`run_deadline.job_cutoff`）；`opts` 只留并发/隔离/grace/重试/心跳这些策略旋钮与组合根注入的能力。

**`record` 放进 `opts`、不另设位置参数**，schedule 据它是否为空分支；形态与理由见 [0030](./0030-realtime-persistence-seam.md) 决定一「服从记录的三项能力」。

- **注入 `engines`（`EngineResolver`：按 `job.engine` 解析 Engine）而非自己 spawn** → 可测（skill：accept dependencies, don't create them）：测试注入假 Engine（吐预设 JSON Lines，[0024](./0024-worker-core-protocol.md)）即可验调度逻辑，无需真起子进程/真连 AgentCore。**schedule 对引擎数/引擎名无知**——焊死 `{midscene, novaact}` 会让第三个引擎到来即改接口；用 resolver 则只动组合根注入。
- **注入 `sink`**（`(event) -> void` 回调，仅供 CLI 打印进度）→ schedule 边收边转，不自己决定结果存哪（[0016](./0016-execution-architecture-core-lib-run-model.md) ports）。**实时落库不走 sink**——走 `on_event`（事件旁路，在 sink_lock 外刷 RUNNING 中间态）/ `on_job_complete`（job 完成落判定真值），由组合根的 `RunPersistence` 编排（[0030](./0030-realtime-persistence-seam.md)）。（RunReport 也不走 sink，它由谁、从什么生成见 [0027](./0027-runreport-aggregation-index.md)「ReportStore 接口：整 run 一次写」节。）
- **`sink` vs `Execution` 边界（不是两次独立判定）**：`sink` 收的是 [0024](./0024-worker-core-protocol.md) **原始流式事件**（pass-through，供实时进度）；`Execution` 是 schedule 对**同一事件流的归约终值**（各 job 的判定与余下的 job 不再启动的来源；job 与 run 的状态以运行态为准，[0030](./0030-realtime-persistence-seam.md) 决定三）。同一份事实的两个视图——流式过程 vs 终态归约，非两套判定来源。
- **注入两个时钟**（`clock` 与 `wallClock`）→ 超时杀 / grace→kill / 期限这几条 schedule 独有难逻辑可用假时间确定性单测，不靠真实等待；schedule 自己不另取时钟。job 的截止时刻按墙钟计、不进记录的时长按单调时钟计（理由与代价见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二「检查用墙钟」一段）。
- **返回执行事实 `Execution`，不返回 run 的汇总**：run 与 job 的状态以运行态为准（[0030](./0030-realtime-persistence-seam.md) 决定三），没有启动的 job 由落库服务的结束写结束、来路取最先成立的那一条（[0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节）；汇总 `RunResult`（给退出码/CI，[0016](./0016-execution-architecture-core-lib-run-model.md)）由落库服务从运行态组装，`run --no-report` 按同一套规则在内存里组装（[0027](./0027-runreport-aggregation-index.md)「ReportStore 接口：整 run 一次写」节「RunResult 的组装只有一处」条）。理由：汇总由 schedule 给出时，有记录的执行同时有两份 run 状态，读者要分辨以哪份为准；来路写进汇总，汇总就带上一项只对前台执行有意义、读记录得不到的字段。
- **删除测试**：删掉本模块，「并发控制 + worker 生命周期 + 失败隔离 + 超时兜底」会散进 CLI/WebUI 各写一遍 → 它在挣钱。

## 核心职责

### job 间并行（scope 内串行已被 worker 消化）

- **job = scope = 会话边界**（[0016](./0016-execution-architecture-core-lib-run-model.md)）。「scope 内串行」由 worker 自己完成（一个 worker 顺序跑完该 scope 全部 scenario、共享一个会话，[0024](./0024-worker-core-protocol.md)）。
- 故 schedule 层面 = **job 之间并行**：每个 job 经 `engines(job.engine)` 解析出 Engine、起一个 worker，彼此独立。

### 并发上限（保护 AWS 配额与峰值消耗）

- `maxConcurrency` 默认 **4**（保守）：每个并行 worker = 一个远程会话（桌面为 AgentCore 浏览器会话、设备为 Device Farm 远程访问会话）+ 持续模型调用；并发越高，同时在线的会话和并行的模型调用越多，占用配额、抬高单位时间的消耗。总费用由 job 数与各 job 的原生用量决定，不随并发变化（见本节「CLI 默认值须与此对齐」条的实测；[0024](./0024-worker-core-protocol.md) cost）；例外是 fail-fast 早停时，并发越高，被中止前已产生的费用越多。超出上限的 job 排队，有 worker 退出腾出槽位再起下一个。
- 是**注入参数 + 保守默认**，不写死——本地全量可调高、配额紧可调低。
- **CLI 默认值须与此对齐**：CLI 曾把 `--max-concurrency` 默认写成 1（「护成本」直觉），但并发不改 job 数与模型调用量、只改墙钟——演示项目 20 个 job 经云端后端实测，串行 1756 秒、并发 4 时 443 秒，每个 job 的墙钟不变。现 `run` / `submit` 的缺省都取 4；本机后台推进进程的并发恒取自 `submit` 交来的输入（即 `submit` 解析出的值），不存在缺值时的回落（cloud 推进器取 definition 值与部署侧 cap 的较小者、definition 缺值按 1，见 [0034](./0034-detached-batch-reconciler.md) 机制四）。

### 失败隔离（默认隔离，可配 fail-fast）

- **默认 `failFast = false`（隔离）**：一个 worker 崩（异常退出 / 超时）→ 该 job 记 `error`（区别于 scenario 级 `failed`，[0024](./0024-worker-core-protocol.md) status 语义），**其余独立 job 照跑**。一轮拿到最大限度结果，不因一个 flaky job 重跑整批。
- **可配 `failFast = true`**：任一 job 崩 → 立即优雅终止所有在跑 worker、中止整批：在跑的 job 停下、各自得出结果（内容不完整记 `aborted`，[0031](./0031-job-lifecycle-states-and-severity.md) 决定一），余下没有启动的 job 在它们都结束之后由结束写记 `skipped`（[0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节）。CI 门禁省钱省时（早停）。
- 两种诉求相反（全量跑批要隔离 / CI 要早停），故做成旋钮、不二选一焊死。

### 超时兜底

- `Job.timeout_s`（per-job 墙钟预算，由 `@timeout:N` tag / `--default-job-timeout` 声明，见 [0019](./0019-feature-tags-scope-and-engine.md)/[0034](./0034-detached-batch-reconciler.md)；恒为有限正数，每个 job 都有截止时刻，没有「不超时」，见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策十）：防一个 job 卡死（AI 死循环 / 网络挂）永久占用并发槽位 + 持续计费。超时 → 优雅终止该 worker（走下文终止契约：停止请求→宽限→强杀）、记 `status:error` + `errorType:timeout`（[0024](./0024-worker-core-protocol.md) status 三态 + 规范化 errorType）。
- **截止时刻与运行期限**：job 的截止时刻由认领时刻、`Job.timeout_s` 与 `RunMeta.deadline_at` 按墙钟算出（`run_deadline.job_cutoff`，算法见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二第 2 条）；到点的 job 记什么见 [0031](./0031-job-lifecycle-states-and-severity.md) 决定一（由前台与后台共用的终结函数给出）。过了停止启动的时刻（0054 决策二第 1 条）就不再启动 job、也不再重试；到期后的首次仲裁与「内容完整不改判」和 job 自己的预算到点时相同（0034 机制二）。
- 引擎 SDK 各自也有超时（Midscene/Nova Act 都有），但那只覆盖「引擎调用内」卡住；**进程层面卡死（非引擎调用内）只有 schedule 能兜**，故 schedule 这层超时是必要的外层保险。

### 起 worker 与重试之前的检查：服从运行期限与这次 run 的记录（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二、五）

- **起 worker 之前按序检查**：已过停止启动的时刻、已发现 run 被别处记为已结束、run 已因 fail-fast 或使用方中断而中止，任一条成立即不启动、不产出判定（不回调 `on_job_complete`），这个 job 在记录里记什么、由谁记，因命中的是哪一条而不同，见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二「一次前台执行可能因三种原因停下」一段；都不成立才取墙钟作认领时刻、经 `record.claim` 认领并起 worker（认领紧贴起 worker；认领被拒即发现 run 已被别处结束）。没有记录（`record` 为空）时跳过认领，期限的检查照常。
- **重试之前**同一次序，最后一步换成读一次 run 级状态（`record.still_open`，重试不再认领）；命中即不再重试：已过停止启动的时刻、或已因 fail-fast 或使用方中断而中止时，把上一次的结果作为终态写下并注明最先命中的原因；发现 run 已被别处结束（含这次读到终态）时不写、不存明细（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）。不读存储的几项在退避之前也查一次。
- **第三种中止来源**：认领被拒、重试之前读到终态、写 job 状态时得知 run 级已结束，三处的发现汇成停手信号（`record.ended_elsewhere`）。前两处由 worker 线程当场记下；第三处由调度循环在那次落库回调（`on_event`、`on_job_complete`）返回之后、在同一个线程里当场读进来；等待循环另与使用方中断同一节拍地读，同一次轮询里先读停手信号、再处理中断。成立即像 fail-fast 一样对运行中的 worker 当场落定、发停止请求，此后不存明细、不写终态（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）。三种中止来源都登记在 run 的中止标志上，只有第一次登记的来源被记下，中止的说明取它（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二）。认领或读取本身失败按运行期落库失败处理，与回调抛异常相同。
- **停止启动不撤销**：任何一次检查观察到已过停止启动的时刻即记下，此后起 worker 之前与重试之前的检查都按已过处理，判断是否做到期的结束写也用这个记下的事实、不重读墙钟。
- **余下的 job 不再启动的来源只登记一处**：停止启动的时刻在第一次被检查观察到时登记，三种中止来源在中止标志第一次登记来源时登记，只记第一次；它随 `Execution` 交给落库服务，作结束写的来路。停止启动不并进中止标志：中止标志一经置位，执行中的 worker 就被停下，而停止启动只拦启动、不停执行中的 job。
- **run 级**：run 的状态只由各 job 的终态算出（[0031](./0031-job-lifecycle-states-and-severity.md) 决定三）；schedule 返回之后仍有未结束的 job 时，由落库服务以 `Execution` 交来的来路做结束写（[0030](./0030-realtime-persistence-seam.md) 决定三）。
- **静默 worker 的超时如何触发**：超时检查在「每收一个事件后」做。worker 完全静默（卡在单次操作内、事件通道零输出）时，事件循环会阻塞在读上、检查永不触发（曾致 300s 超时拖到 ~620s）。故 schedule 用 `_heartbeat_wrap`（后台 reader 线程把 adapter 的纯 `Iterator[Event]` 喂进队列，主侧 `queue.get(timeout=heartbeat_interval_s)` 超时即注入存活心跳）让循环周期性醒来查超时——**心跳在 schedule 层做一次、对所有 adapter 通用，Engine port 保持纯 `Iterator[Event]`**（机制细节见 [0028](./0028-transient-network-ssl-resilience.md)）。

### 网络瞬时故障的 job 级重试（[0028](./0028-transient-network-ssl-resilience.md)）

- worker 建连失败、重试耗尽 → 以专用退出码退出 → adapter 抛 `WorkerNetworkError` → schedule 记 `error_type="network_error"`。
- schedule 对这类 job **选择性整体重试**（重新 spawn worker），门槛三条件 AND：① `network_error` ② 「会话未起」= 本次零 `step_done`（证明 act 没跑、无副作用——绝不重试可能已点击的 act）③ job 目标不是设备（远程访问会话的建连失败不做 job 级重试，[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 2）。**fail_fast/timeout 优先级更高**（已主动中止的不重跑）；过了门槛还要过重试之前的检查（见上「起 worker 与重试之前的检查」）。
- `ScheduleOpts` 加 `network_retry: int = 0`（默认关,本地 smoke 不需要,同「注入参数+保守默认」原则；现状组合根不传、CLI 不暴露，`run` 下恒为 0，后台 `submit` 路径没有这个循环，见 [0028](./0028-transient-network-ssl-resilience.md)「core 层 job 重试」）+ `retry_sleep`（注入,单测传 no-op 保 fake-clock 纯净）。job 的截止时刻在认领时算出、跨 attempt 共享、不重置。

### 优雅终止（schedule 只下逻辑「停」指令，机制归 adapter）

「怎么停」的具体机制**不在 schedule**——本模块只负责下逻辑指令，机制/会话清理归 adapter 与 worker（三层完整机制见 [0024](./0024-worker-core-protocol.md) 终止契约节，此处只钉本模块边界，不复述以免漂移）：
- **schedule → WorkerHandle**（本模块职责）：只调逻辑指令 `handle.stop(gracePeriod)`（「请停这个 worker」）。`handle` 由 `engine.run_scope(job)` 返回、schedule 持有；`Engine` port **只有 `run_scope`、不挂 stop**（句柄自己知道怎么停）。schedule **不懂** SIGTERM/进程——只知道「下停止指令、等归约」。
- **机制层与会话清理**（转指针）：adapter 把逻辑「停」翻成具体机制（子进程 SIGTERM+宽限+SIGKILL）、会话清理（桌面 `StopBrowserSession`、设备 `StopRemoteAccessSession`）归 worker——**故换停止机制只换 adapter**，schedule 一行不改。机制细节 + 两引擎会话释放见 [0024](./0024-worker-core-protocol.md) 终止契约 + [0028](./0028-transient-network-ssl-resilience.md) Midscene 会话集清理。（**⚠️ 此处「一行不改」限于「停止机制」这一层**——驱动循环整体的演进是另一回事、非「换 adapter」能覆盖，见下「留口子」段 ⚠️ 注。）（SIGKILL 硬杀致会话释放落空的低频泄漏，桌面会话由 AgentCore session TTL 兜底、设备会话由 Device Farm 150 分钟上限封顶，**均不引入 core reaper**，见 [0024](./0024-worker-core-protocol.md) 终止契约「已接受代价」与 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 6——schedule/core 纯度不变。）
- **停止后的等待预算**（取法与理由见 [0034](./0034-detached-batch-reconciler.md) 机制二「停止后继续有界消费完整事件流」条）：发出停止请求后 schedule 仍消费事件流，直到 EOF 或排空上界（等待预算加余量）。等待预算是调用方愿意为该引擎等到事件流结束的时长，不是平台保证。同步 `run` 只有本机后端（[0016](./0016-execution-architecture-core-lib-run-model.md) 决策 A），本机 handle 用 grace 等 worker 退出、到期整组 SIGKILL，所以等待预算就是 grace，`ScheduleOpts` 不另设等待预算。超出预算仍未到达的收尾事件不计入，会话记未确认、退出码记未知。

> **进程拓扑（澄清「几个地方」）**：实际是 **2 进程 + 1 远程 + 1 seam**——①core/schedule 进程；②`Engine` adapter（在 core 进程内，但它是通向「进程/云」世界的 seam，「怎么停」知识归这里）；③worker 子进程（engine SDK 是**进程内的库**、非独立进程）；④远程会话（桌面目标为 AgentCore 浏览器会话、worker 经 CDP 连；设备目标为 Device Farm 远程访问会话、worker 经 Appium 连，见 [0051](./0051-device-session-lifecycle-and-app-distribution.md)/[0052](./0052-appium-interface-adapter-and-platform-differences.md)）。engine SDK 拆除 + 会话停止都在 worker 进程内完成。

### 事件归集（status + 原生量成本 + 墙钟时长 三级归约）

- 边收 worker 的流式事件（[0024](./0024-worker-core-protocol.md) JSON Lines，九类：`scope_started`/`scenario_started`/`step_started`/`step_done`/`step_skipped`/`scenario_done`/`scope_done`/`session_opened`/`session_closed`（后两类是会话血缘事件，桌面与设备 worker 都成对发出，见 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 4）；`step_skipped` = scope 内短路，见下 status 归约与 [0031](./0031-job-lifecycle-states-and-severity.md) 决定六）边转给 `sink`；归约成各 job 的 `JobResult`（逐个交给 `on_job_complete`，并随 `Execution` 返回）。
- 多 worker 并行 → 多路事件流交错，schedule 按 `scopeId`/`scenarioId` 归位（[0024](./0024-worker-core-protocol.md) 标识键）。
- **status 归约**：scenario → job（任一 error→error / 任一 failed→failed / 全 passed→passed；这只是终结函数 `core.project.finalize_job` 里内容完整那一行——`scope_done.status = error` 取 scope 级判定、零 scenario 判定记 engine_error、有会话未确认停止时改判 error + `release_failed`，真值表见 [0034](./0034-detached-batch-reconciler.md) 机制二与 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 4）→ run（取法见 [0031](./0031-job-lifecycle-states-and-severity.md) 决定三）。job 级除 worker 三态外，core 还派生 `aborted`（跑一半被掐：fail-fast、使用方中断或被 run 的期限截断，[0031](./0031-job-lifecycle-states-and-severity.md) 决定一）；没有启动的 job 不产出判定，由结束写记 `skipped`（0031 决定三「结束写」小节）；发现 run 已被别处结束时被停下的 job，结果不写进记录（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）。
- **job 级乐观归约的内容完整前置（[0024](./0024-worker-core-protocol.md)「事件流内容完整与进程终止是两件事、都要」在同步路径的落点；首轮 code-health 对抗验证逼出）**：事件流正常 EOF 后，job 落「scenario 归约终态」**须以见到 `scope_done` 为前提**——worker 被协作停（fail-fast/超时的 `handle.stop`）后按契约**不吐 in-flight 的 scenario_done/scope_done、干净退出**（exit 0），事件流自然 EOF；若不校验内容完整就直落归约，部分完成的 job 会拿「已完成的那几个 scenario」聚合出 PASSED（假绿——判定失真+ABORTED 现场丢失，探针复现：`--default-job-timeout 0` 时任意关停时序 100% 假绿、心跳只在特定时序偶然救回）。**未见 scope_done 时不落乐观终态**：判定由同步与无状态两路共用的终结函数 `core.project.finalize_job` 给出（[0034](./0034-detached-batch-reconciler.md) 机制二「终结函数与真值表」），依据首次仲裁落定的 `stop_reason`：作出停止决定那一刻截止时刻已过即为到点（即使 fail-fast 标志也已置位），起作用的是 job 自己的预算取 error+timeout、是 run 的期限取 ABORTED，否则主动中止（fail-fast、使用方中断或发现 run 已被别处记为已结束）取 ABORTED（[0031](./0031-job-lifecycle-states-and-severity.md) 决定一）；没被主动停止、干净退出却没有 scope_done 的取 error+engine_error（进程报告成功而内容没发完，两者矛盾）。（本篇曾在 EOF 分支先判 `abort_flag` 再判 deadline，与事件分支的次序相反，已由 0034 机制二的首次仲裁规则统一。）
- **`step_skipped` 归约（scope 内短路，不臆断因果的守法方式，[0031](./0031-job-lifecycle-states-and-severity.md) 决定六）**：worker 上游 step `error` 后短路后续 step、为每个发 `step_skipped`；core 归约成 `StepResult(status=skipped, shortcircuited=True)` 记进 step 明细，**但绝不把它写进 scenario 判定累加器**——scenario/job/run 判定只由那个上游 `error` step 决定，与"后面短路了几步"无关（step 级 skipped 零污染 scenario 归约/severity）。因果（"谁因谁短路"）只存在于 worker 的串行循环，core 作为纯 reducer 物理上看不到、也不臆断——它只忠实归约 worker 发来的 `step_skipped`，把"某步没跑"如实记进 `StepResult`。
- **成本归约**：core 只各自合计 engine 报的**原生量**——累加 `step_done.cost` 的 `tokens`/`time_worked_s` 成 `JobResult.total_tokens`/`total_time_worked_s`（scope 级）；run 级的 `RunResult.total_tokens`/`total_time_worked_s` 在组装 RunResult 时由各份判定明细求和（[0027](./0027-runreport-aggregation-index.md)「RunResult 的组装只有一处」条）。**core 不折美元**（交消费者），无任何引擎报某量则该量 None、不假装 0（cost 信封见 [0024](./0024-worker-core-protocol.md)）。设备 job 另把 `session_closed.observedS` 合计成 job 与 run 级的 `device_observed_s`，`observedS` 缺失的会话计入 `device_observed_missing`（结果未知的创建尝试两者都不计）；两键只按 job 目标是否为设备给出，桌面 job 有会话事件也不出现（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 7）。
- **墙钟时长归约**（性能指标，与成本正交）：core 用注入的单调时钟 `clock` 在事件到达时打时间戳，按各级 `*_started`→`*_done` 算 `duration_ms`——step（`StepResult.duration_ms`）、scenario、scope（`JobResult.duration_ms`）、run（schedule 整体包住、含并发，随 `Execution.duration_ms` 交出，组装后即 `RunResult.duration_ms`）。

## 治理旋钮 = 注入参数 + 保守默认（贯穿原则）

`maxConcurrency` / `failFast` / `gracePeriod` / `clock` / `wallClock` 全部是 `opts`/参数注入、带保守默认，**不写死在实现里**——同 [0016](./0016-execution-architecture-core-lib-run-model.md) 组合根注入精神：策略由调用方（CLI/未来 WebUI）定，核心只认参数。（job 墙钟预算同守此精神、只是载体不同：由组合根按 tag/CLI 缺省解析定值后随 definition 进来，见上「超时兜底」。）

## 现在做 / 留口子

- **现在做（v1.0）**：上述接口、job 间并发（上限+排队）、失败隔离（默认隔离/可配 fail-fast）、超时兜底、优雅终止（schedule 调 `handle.stop(grace)`；子进程 handle 内 SIGTERM+宽限+SIGKILL）、事件归集成各 job 的判定（status + 原生量成本 + 墙钟时长 三级归约）；1.5 起加使用方中断：等待 job 完成的循环按短间隔轮询组合根注入的 `interrupt()`，首次走 `_stop_all` 协作停止、再次对运行中 worker 调 `handle.stop(0)` 强制，余下没有启动的 job 由结束写记 skipped，run 的状态按 [0031](./0031-job-lifecycle-states-and-severity.md) 决定三的取法得出（见上「status 归约」条，机制与提示语见 [0024](./0024-worker-core-protocol.md) 终止契约）；此后又加上遵守运行期限与这次 run 的记录（见上「起 worker 与重试之前的检查」，[0054](./0054-run-deadline-lifetime-lock-and-settling.md)）。
- **留口子不实现**：core→worker 控制流（暂停/取消单 scenario/动态调度，等真需求，见 [0024](./0024-worker-core-protocol.md) 终止契约节）；跨 job 的智能调度（按成本/优先级排序，现 FIFO 排队即可）；云端分布式调度不经 schedule（v1.1 Fargate，[0017](./0017-cloud-execution-fargate-over-runtime.md)）：云端后端只支持 `submit`（[0016](./0016-execution-architecture-core-lib-run-model.md) 决策 A），云端的 run 由 [0034](./0034-detached-batch-reconciler.md) 的推进器推进，schedule 只驱动本机后端的 worker。**⚠️「schedule 一行不改」只覆盖「执行 adapter 替换」、未预见「CLI 脱离」这一步**（[0034](./0034-detached-batch-reconciler.md) v1.2 纠正）：无状态 `submit`（提交即走）要求把 schedule 当前的**同步驱动循环本身**（`ThreadPoolExecutor` 起全部 worker 线程 + `wait(FIRST_COMPLETED)` 收集完成结果 + `abort_flag`/fail-fast `_stop_all` 进程内并发闸）解体——因为 CLI 一退，这个循环没人驱动了。异步路径把它换成**无状态事件驱动 reconciler**（被事件唤醒、读全量 events 重放、CAS 推进），并从 schedule 抽出纯 `project`/`plan_next`（签名见 [0034](./0034-detached-batch-reconciler.md)）供 Lambda 与本机后台推进进程两种宿主复用。**存活的是纯归约器、消失的是同步驱动循环**；纯 reducer 红线仍守（CAS/RunTask/PutItem 副作用仍在 adapter/组合根、core 不 import boto3）。同步 `run` 路径仍用现驱动循环——两种驱动模型按命令并存。故「schedule 一行不改」对无状态批量运行**不成立**，见 [0034](./0034-detached-batch-reconciler.md)。

## 重议

- 若并发/超时的保守默认在真实跑批中被证明不合适 → 调默认值（参数本就可配，不动接口）。
- 若出现「停」之外的控制需求 → 引入控制流通道（[0024](./0024-worker-core-protocol.md)），schedule 据此扩展。
