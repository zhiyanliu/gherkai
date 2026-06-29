# schedule 模块：job 间并发调度 + 失败隔离 + 优雅终止

核心库把 plan 产出的 **job 列表**（[0025](./0025-plan-module-feature-to-jobs.md)）实际跑起来的模块：决定哪些 job 并行、控并发、起 worker、收流式事件、隔离失败、超时兜底。它兑现 [0016](./0016-execution-architecture-core-lib-run-model.md)/[0019](./0019-feature-tags-scope-and-engine.md) 留给核心库的「scope 串/并行调度、会话共享」。它是 v1.0 核心三模块的最后一块（协议 [0024](./0024-worker-core-protocol.md) → plan [0025](./0025-plan-module-feature-to-jobs.md) → schedule 本 ADR）。

## 接口（深模块，小）

```
schedule(jobs: Job[], engines: EngineResolver, sink: (event) -> void, run_id: str, opts) -> RunResult
   // EngineResolver: (engineName) -> Engine —— 按 job.engine 解析 Engine，schedule 对腿数/腿名无知
   // sink: 接收 0024 原始流式事件的回调（pass-through，供进度/落地）
   // run_id: 一次 run 的标识，组合根 mint 后传入、schedule 透传进 RunResult（不自己生成；ADR 0027）

opts = {                 // 时间单位统一为秒；代码字段名带 _s 后缀（job_timeout_s/grace_period_s）
  maxConcurrency = 4,    // 同时在跑的 worker 上限
  failFast = false,      // 任一 job 崩是否中止整批
  jobTimeout = null,     // per-job 墙钟超时（秒；null=不超时；超时记 status:error + errorType:timeout）
  gracePeriod = 5,       // 停止请求后等 worker 优雅退出的宽限秒，超期强杀
  clock,                 // 时间源（可注入 fake clock 单测超时/grace 路径；默认 monotonic，抗系统时钟回拨）
}
```
（上为语言中立伪代码；实际实现为 dataclass `ScheduleOpts`，字段 snake_case：`max_concurrency`/`fail_fast`/`job_timeout_s`/`grace_period_s`/`clock`/`network_retry`（默认 0）/`retry_sleep`（[0028](./0028-transient-network-ssl-resilience.md)）。）

- **注入 `engines`（`EngineResolver`：按 `job.engine` 解析 Engine）而非自己 spawn** → 可测（skill：accept dependencies, don't create them）：测试注入假 Engine（吐预设 JSON Lines，[0024](./0024-worker-core-protocol.md)）即可验调度逻辑，无需真起子进程/真连 AgentCore。**schedule 对腿数/腿名无知**——焊死 `{midscene, novaact}` 会让第三个引擎到来即改接口；用 resolver 则只动组合根注入。
- **注入 `sink`**（`(event) -> void` 回调，收流式事件的去处：实时落 ResultStore / CLI 打印进度）→ schedule 边收边转，不自己决定结果存哪（[0016](./0016-execution-architecture-core-lib-run-model.md) ports）。（RunReport **不**走 sink——它由 `ReportStore.write` 从归约后的 `RunResult` 派生，[0027](./0027-runreport-aggregation-index.md)。）
- **`sink` vs `RunResult` 边界（不是两次独立判定）**：`sink` 收的是 [0024](./0024-worker-core-protocol.md) **原始流式事件**（pass-through，供实时进度/逐条落地）；`RunResult` 是 schedule 对**同一事件流的归约终值**（权威汇总判定，给退出码/CI）。同一份事实的两个视图——流式过程 vs 终态归约，非两套判定来源。
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

### 网络瞬时故障的 job 级重试（[0028](./0028-transient-network-ssl-resilience.md)）

- worker 建连失败、重试耗尽 → 以专用退出码退出 → adapter 抛 `WorkerNetworkError` → schedule 记 `error_type="network_error"`。
- schedule 对这类 job **选择性整体重试**（重新 spawn worker），门槛双条件 AND：① `network_error` ② 「会话未起」= 本次零 `step_done`（证明 act 没跑、无副作用——绝不重试可能已点击的 act）。**fail_fast/timeout 优先级更高**（已主动中止的不重跑）。
- `ScheduleOpts` 加 `network_retry: int = 0`（默认关,本地 smoke 不需要;CI/抖动环境可开,同「注入参数+保守默认」原则）+ `retry_sleep`（注入,单测传 no-op 保 fake-clock 纯净）。`job_timeout` deadline 跨 attempt 不重置。

### 优雅终止（schedule 只下逻辑「停」指令，机制归 adapter）

三层各司其职，「怎么停」的具体机制**不在 schedule**：
- **schedule → WorkerHandle**：只调逻辑指令 `handle.stop(gracePeriod)`（「请停这个 worker」）。`handle` 由 `engine.run_scope(job)` 返回、schedule 持有；`Engine` port **只有 `run_scope`、不挂 stop**（句柄自己知道怎么停）。schedule **不懂** SIGTERM/进程/StopTask——只知道「下停止指令、等归约」。
- **WorkerHandle（adapter 内）→ worker**：把逻辑「停」翻成具体机制——**子进程 handle**：`SIGTERM` → 等 `gracePeriod`（默认 5s）→ 未退则 `SIGKILL` 兜底；**未来 Fargate**：翻成 `StopTask`。这是 adapter 该藏的「进程/云」知识（[0016](./0016-execution-architecture-core-lib-run-model.md) ports&adapters），**故「上云只换 adapter」成立**（见下「留口子」），schedule 一行不改。
- **worker 内部**：收到 `SIGTERM` 做会话清理，两腿机制不同、殊途同归（详见 [0024](./0024-worker-core-protocol.md) 终止契约）——**Nova**：handler `raise` `BaseException` 子类 → 三层 `with` 的 `__exit__` 解栈、由 `with browser_session` 间接释放会话（不 `sys.exit`，那会跳过 `__exit__` 泄漏会话，是已修的真实 bug）；**Midscene**：有序显式 cleanup（先 `StopBrowserSession` 再 `browser.close` 套超时；Stop 失败 → 非 0 退出可观测）。
- **会话清理归 worker，schedule/adapter 不碰 AgentCore**：schedule 下逻辑指令、adapter 发机制信号——**StopBrowserSession 只由 worker 调**（Nova 经 `with browser_session` 间接、Midscene 显式调），schedule/adapter 保持对 AgentCore 无知。

> **进程拓扑（澄清「几个地方」）**：实际是 **2 进程 + 1 远程 + 1 seam**——①core/schedule 进程；②`Engine` adapter（在 core 进程内，但它是通向「进程/云」世界的 seam，「怎么停」知识归这里）；③worker 子进程（engine SDK 是**进程内的库**、非独立进程）；④远程 AgentCore 浏览器会话（云端、worker 经 CDP 连）。engine SDK 拆除 + 会话停止都在 worker 进程内完成。

### 事件归集（status + 原生量成本 + 墙钟时长 三级归约）

- 边收 worker 的流式事件（[0024](./0024-worker-core-protocol.md) JSON Lines，六类：`scope_started`/`scenario_started`/`step_started`/`step_done`/`scenario_done`/`scope_done`）边转给 `sink`；归约成 `RunResult`。
- 多 worker 并行 → 多路事件流交错，schedule 按 `scopeId`/`scenarioId` 归位（[0024](./0024-worker-core-protocol.md) 标识键）。
- **status 归约**：scenario → job（任一 error→error / 任一 failed→failed / 全 passed→passed）→ run（同规则跨 job）。
- **成本归约**：core 只各自合计 engine 报的**原生量**——累加 `step_done.cost` 的 `tokens`/`time_worked_s` 成 `JobResult.total_tokens`/`total_time_worked_s`（scope 级），再跨 job 求和成 `RunResult.total_tokens`/`total_time_worked_s`（run 级）。**core 不折美元**（交消费者），无任何腿报某量则该量 None、不假装 0（cost 信封见 [0024](./0024-worker-core-protocol.md)）。
- **墙钟时长归约**（性能指标，与成本正交）：core 用注入的 `clock` 在事件到达时打时间戳，按各级 `*_started`→`*_done` 算 `duration_ms`——step（`StepResult.duration_ms`）、scenario、scope（`JobResult.duration_ms`）、run（`RunResult.duration_ms`，schedule 整体包住、含并发）。core 首次保留 step 级粒度（`StepResult` 层）。

## 治理旋钮 = 注入参数 + 保守默认（贯穿原则）

`maxConcurrency` / `failFast` / `jobTimeout` / `gracePeriod` / `clock` 全部是 `opts`/参数注入、带保守默认，**不写死在实现里**——同 [0016](./0016-execution-architecture-core-lib-run-model.md) 组合根注入精神：策略由调用方（CLI/未来 WebUI）定，核心只认参数。

## 现在做 / 留口子

- **现在做（v1.0）**：上述接口、job 间并发（上限+排队）、失败隔离（默认隔离/可配 fail-fast）、超时兜底、优雅终止（schedule 调 `handle.stop(grace)`；子进程 handle 内 SIGTERM+宽限+SIGKILL）、事件归集成 RunResult（status + 原生量成本 + 墙钟时长 三级归约）。
- **留口子不实现**：core→worker 控制流（暂停/取消单 scenario/动态调度，等真需求，见 [0024](./0024-worker-core-protocol.md) 终止契约节）；跨 job 的智能调度（按成本/优先级排序，现 FIFO 排队即可）；云端分布式调度（v1.1 Fargate，[0017](./0017-cloud-execution-fargate-over-runtime.md)，那时「起 worker」从 spawn 子进程换成提交 Fargate task、`handle.stop` 从发信号换成 StopTask，**均在 Engine adapter / WorkerHandle 内部，schedule 接口/旋钮不变**）。

## 重议

- 若并发/超时的保守默认在真实跑批中被证明不合适 → 调默认值（参数本就可配，不动接口）。
- 若出现「停」之外的控制需求 → 引入控制流通道（[0024](./0024-worker-core-protocol.md)），schedule 据此扩展。
