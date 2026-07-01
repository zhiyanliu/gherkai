# 网络/SSL 瞬时错误的鲁棒性：两层重试 + network_error 分类（务实加固，非 enterprise resilience）

实测中 worker 建连（开 AgentCore 会话 / SigV4 握手 / CDP 连接）常遇 `ssl.SSLEOFError`（UNEXPECTED_EOF）
等**网络瞬时故障**——一次抖动就让烧了钱的 job 直接废（worker returncode=1 → core 记 engine_error，零重试）。
本 ADR 加两层重试 + 一个 `network_error` 分类止血。**定位:对齐 [0015](./0015-v1-positioning-smoke-not-regression.md) 本地 smoke
的务实加固,不是 enterprise 级 resilience**——act 级故障恢复、持续性网络故障的指数退避风暴都不在范围。

## 决定:两层重试

| 层 | 谁重试 | 重试什么 | 默认 |
|---|---|---|---|
| **① worker 内** | 两个引擎 worker 自己 | **仅建连/开会话段**（幂等、未产生副作用） | 开（4 次尝试） |
| **② core/schedule** | schedule 对整个 job | 仅 `network_error` 且「会话未起」的 job 重新 spawn worker | **关**（`network_retry=0`） |

两层职责分离:worker 层扛「单进程内的瞬时抖动」（最近故障点、最省）；core 层扛「worker 进程级失败」
（spawn 后整体没起来）。乘积上界 = worker 4 × core(1+network_retry)，靠**小常量封顶**——
诚实说明:失败域分层只对**单进程瞬时抖动**成立;**持续性网络故障下乘积会真实打满**（连续多次打 AWS），
这是靠小 K/M 封顶的已接受代价,不是「几乎不会发生」。

## 硬约束:只重试建连,**绝不重试 act**

`act`/`act_get` **不幂等**（可能已点击/已部分执行）、**烧钱**、重试会重复副作用。所以:

- 重试域的物理边界 = **`scope_started` 事件 emit 之前**。一旦 emit（会话已起、act 即将跑），
  worker 内 `started=True`（Nova）/ 跳出建连循环（Midscene），core 侧 `saw_step=True`（见过 `step_done`）——
  **任何一方越过此点都永久退出重试域**。这是**结构性保证**,不靠「小心编码」。
- 幂等性依据:建连段每个操作都可安全重放——`StartBrowserSession`（新会话）、`cdp_session`/SigV4 握手
  （无状态签名）、`connectOverCDP`（新连接）、`ensure_workflow_definition`（create-if-not-exists 幂等,[0004](./0004-novaact-iam-auth-via-workflow.md)）。

## network_error 分类:白名单具体瞬时类型

`ErrorType` 加 `network_error`（[0024](./0024-worker-core-protocol.md) errorType 既有口子的兑现）。
worker **按白名单匹配具体瞬时异常类型**,不用宽基类兜底:

- **Python（Nova）**:`ssl.SSLError`（含 `SSLEOFError`）、`ConnectionError`、`TimeoutError`、`socket.timeout`、
  botocore `EndpointConnectionError`/`ConnectionClosedError`、urllib3 `ProtocolError`。
  **明确排除 `socket.gaierror`（DNS 永久错）**——它与 `ssl.SSLError` 都继承 `OSError`,用宽 `OSError`
  兜底会把永久错也当瞬时重试,故只匹配具体类型。
- **Node（Midscene）**:error code `ECONNRESET`/`ECONNREFUSED`/`ETIMEDOUT`/`EPIPE`/`EAI_AGAIN`/`ECONNABORTED`
  + TLS/握手类 message 匹配。**排除 `ENOTFOUND`（DNS 永久）**。
- **拿不准 → 不归 network_error**（归 engine_error、不重试）。明确非 network 的:鉴权失败、4xx、配置错、DNS 永久失败。

> **已知欠账：两腿对"导航 SSL 失败"的分类不对称**（真跑暴露、本轮 defer 不改）。同一瞬时 SSL 故障（如握手被 `UNEXPECTED_EOF` 打断）：**Nova** 腿 `go_to_url` 抛异常，异常链底层含 `ssl.SSLError`/`SSLEOFError`，`_is_transient_network` 遍历 `__cause__/__context__` 命中 → `network_error`（准）。**Midscene** 腿 `page.goto` 抛的是 Chromium 的 `net::ERR_CERT_*`（如 `ERR_CERT_AUTHORITY_INVALID`），其 message 文案**不含** `isTransientNetwork` 的 message 正则关键词（`ssl/tls/handshake/UNEXPECTED_EOF`）、也无对应 error code → 落 `engine_error`。**本轮不盲改** Midscene 分类：因为 Chromium 把"瞬时握手中断"与"真证书错（过期/自签/域名不符，永久）"**都归成同一个 `net::ERR_CERT_*`、丢了区分**——盲目把 `ERR_CERT_*` 当瞬时会误判真证书错为可重试、无意义重试 N 次。**要真修需先用真 Midscene SSL 样本**（访问自签/过期证书站点真跑）确认 Chromium 到底报什么 code/message、能否区分瞬时 vs 真证书错，再决定分类。**注意**：这条分类不对称**不影响**上面记的 step 短路 defer——短路判据锁 `status==error`（不看 error_type），两腿 error 都触发、行为对称；分类不对称只影响用户看到的 errorType 文案。

## 关键不变量:退出码携带 network 信号

建连失败**发生在任何事件 emit 之前**（`scope_started` 都没发,fd3 零事件）——worker 无法走事件通道告诉 core。
故用**专用退出码**作 out-of-band 信号:

- **`EX_WORKER_NETWORK = 80`**（避开 POSIX sysexits 64-78 / shell 保留 126-128+n / 信号区）。
  **两个引擎 worker 必须用同一值**（各自硬编码 80）;core 的 `subprocess_engine.EX_WORKER_NETWORK = 80` 是单一来源的注释锚点。
- worker 建连重试耗尽 + `scope_started` 未 emit → 退出 `80`。
- `subprocess_engine._read_events` 把 returncode 80 翻成 `core.errors.WorkerNetworkError`（类型化）;
  `schedule._Worker._run_once` 在 generic `except` **之前**加 `except WorkerNetworkError` → 记 `error_type="network_error"`。
- **`WorkerNetworkError` 定义在 `core/errors.py`,不在 adapter**——否则 schedule 反依赖 adapter（违反 ports 六边形）。
- 会话已起后的瞬时网络错（罕见）仍走 `step_done`/`scope_done` 的 `errorType` 字段,不用退出码。**已兑现**：act 中途失败时两个引擎 worker 复用 `_is_transient_network`/`isTransientNetwork` 判定，网络瞬时 → 标 `network_error`（否则 `engine_error`）——**仅诊断分类、不触发重试/恢复**（act 不幂等；且 `saw_step=True` + 走 step_done 非退出码 80，schedule 双条件 AND 天然不重试）。"act 中途恢复"仍 defer（见下）。

## worker 层退避

- **手写指数退避**（`[0.5, 1, 2]s`,4 次尝试,总 ~3.5s < schedule 默认 grace 5s）——**不用 botocore/urllib3
  内部 retry**:① SIGTERM 要能穿透退避（Python `time.sleep` 被 raise 的信号 handler 打断;botocore 可能 sleep 在 C 里吞信号）;② 重试面可审计、有界。
- 每次 attempt 用**全新**建连对象:Nova 新 `provider`+`cdp_session`+`NovaAct`（with `__exit__` 清掉本次部分会话）;
  Midscene 每次 attempt 失败先 `cleanup()` 释放本次可能已建的会话 + 重置 `browser`/`sessionId`。

## 会话泄漏防护（退出前清理）

- **Nova**:重试耗尽 → `raise _NetworkExhausted(BaseException)` → 穿透三层 `with __exit__`（释放可能已建的会话）
  → main 顶层 `except _NetworkExhausted` → `return EX_WORKER_NETWORK`。禁止 `with` 内裸 `sys.exit`。
- **Midscene**:退 80 前先 `await cleanup()`（`StartBrowserSession` 成功而 `connectOverCDP` 失败时会话已建）;
  **`cleanupFailed`（会话释放失败、可能泄漏）退 1 优先级高于退 80**——泄漏可观测性压过网络分类。
- **SIGTERM 竞态**:停止请求（SIGTERM）期间正在退避 → 不重试。Nova:`except _Terminated: raise` 在 transient 检查**之前**,
  且 `time.sleep` 被信号 handler 的 raise 打断 → `_Terminated` 冒泡（永不到 `return 80`）。Midscene:SIGTERM handler
  无条件 `process.exit`,抢占任何挂起的退避。

## core 层 job 重试

- `ScheduleOpts` 加 `network_retry: int = 0`（默认关,本地 smoke 不需要;CI/抖动环境可开）+
  `retry_sleep: Callable[[float], None] = time.sleep`（**注入**,单测传 no-op 保 fake-clock 纯净）。
- core 层退避公式：第 N 次重试前 sleep `min(2.0 × attempt, 4.0)` 秒（attempt 1→2s、2→4s、3+→封顶 4s），
  与 worker 层退避（`[0.5,1,2]s`,见上）相互独立、各管各层。退避秒数硬编码在调用点（固定 core 行为,非可配项;
  仅 `retry_sleep` 本身可注入以便单测）。
- 重试门槛**双条件 AND**:`error_type == "network_error"` AND **本次零 `step_done`**（`saw_step=False`,证明会话未起、act 没跑、无副作用）。
- **fail_fast / timeout 优先级高于 network 重试**:它们已主动中止 job,不再重跑。
- `schedule._Worker.run` 包重试循环,`_run_once` 返回 `(JobResult, is_network, saw_step)`;对 schedule 主循环透明（先跑完所有 attempt 得终值,再交 fail_fast 判定）。
- `job_timeout` deadline **跨 attempt 不重置**（覆盖所有 attempt 之和,否则重试绕过超时）。设了 timeout 的 CI 须满足 `job_timeout > (network_retry+1) × (worker 退避预算 + 单次建连时间)`。

## 现在做 / 留口子

- **现在做（v1.0）**:上述两层重试、`network_error` 分类、退出码约定、白名单识别、会话泄漏防护、core job 重试（默认关）、单测。
- **静默 worker 超时根治（后续轮，真跑暴露）**:worker 卡在**单次操作内**（如 Nova act 内部反复重试 ~10 分钟、fd3 零新事件）时，schedule 的 `job_timeout` 曾**形同虚设**——deadline 检查只在 `for event in events` 循环体内跑，静默 worker 让该循环永久阻塞在读上，超时拖到被外层进程级杀（实测 300s 超时拖到 ~620s）。根治放在 **schedule 层**而非各 adapter：`_heartbeat_wrap` 把 adapter 的纯 `Iterator[Event]` 包成「事件 + 存活心跳」流——内层迭代搬到一个**后台 reader 线程**塞 `queue`，主侧 `queue.get(timeout=heartbeat_interval_s)` 超时没拿到（worker 静默）就 yield 一个 schedule 私有哨兵 `_HEARTBEAT`，让事件循环醒来查 `deadline`/`abort_flag`；拿到事件就转发、拿到内层异常就重抛（保 `WorkerNetworkError`/`ValueError` 分类不变）。**为何在 schedule 层做一次**：心跳是「持有 deadline 的消费方对任何慢/静默流的通用兜底」，与引擎无关——写一次对子进程/未来 Fargate/内存假实现全适用，`Engine` port **保持纯 `Iterator[Event]`**（不把轮询细节渗进契约、不必每个 adapter 各写一遍）。`_HEARTBEAT` 不是领域事件、不进 model/ports/wire、不归约、不 emit。事件正常流动时 `queue.get` 即时返回、永不注入心跳，故 fake-clock 单测的 clock 读取序列不变（reader 线程只搬事件、绝不读 clock）；无 `job_timeout` 时 `_heartbeat_wrap` 退化为直接转发、不起线程。
- **会话血缘随首事件回传（同轮）**:`session_id` 原仅由 `scope_done` 携带——worker 被超时/SIGTERM 中途打断时 `scope_done` 从不 emit，core 侧 `run_state` 该 job 的 `session_id=null`，**会话明明已起却记不到血缘**（诊断/计费断线，正是上面静默超时场景的伴生缺口）。修复：worker 在 **`scope_started`** 即带 `sessionId` 回传（会话一起就报），schedule 的 `_reduce` 在 `ScopeStarted` 分支也捕获它；`scope_done` 仍带（冗余兜底）。`ScopeStarted` 协议加 optional `session_id` 字段。
- **Midscene SIGTERM 会话泄漏两窗口已根治（后续轮）**:
  - **重试放大的 in-flight 会话窗口**:会话跟踪从「单一 `sessionId` 快照」重构为**待清理会话集**——每次 `StartBrowserSession` 成功即把 id 入集（含被重试丢弃的中间 attempt 会话），cleanup 遍历集逐个 Stop。彻底解决「重试时 sessionId 被后一 attempt 覆盖/置空 → handler 只能 Stop 当前快照、漏掉在途/已弃会话」。剩余仅「Start 已发 RPC 但 id 未返回」一瞬，由一个在途标记 + 短暂兜底等待覆盖。
  - **`StopBrowserSession` 超 `grace_period`**:每个 Stop 套超时预算（挂死即放弃、记 `cleanupFailed` 让泄漏可观测，不被 SIGKILL 打断到一半）；cleanup **并行** Stop（`Promise.all` 而非串行）——否则重试积累的 N 个泄漏会话串行会把 cleanup 拖过 grace 被 SIGKILL 截断（正是本修复要防的泄漏）。并行后最坏 cleanup 墙钟与会话数无关、< cli 默认 grace。常量值与算术见 `run-scope.ts`（代码为准，ADR 不复制以免漂移）。
  - **Nova 引擎不对称（不动，SDK 限制）**:Nova 无 in-flight 窗口（建连在 `with cdp_session` 内、`__exit__` 结构性清理）；但其 `StopBrowserSession` **在 Nova SDK 的 `AgentCoreBrowserSessionProvider.cdp_session().__exit__` 内部**，是 SDK 黑盒——**无法在 worker 层套超时预算**（不像 Midscene 是自己 `cp.send(StopBrowserSessionCommand)`）。硬加 worker 级看门狗 `os._exit` 会跳过 SDK 剩余清理、反而可能更多泄漏。故 Nova 侧依赖 schedule 的 `grace_period`（cli 默认 10s，够 SDK maxAttempts=3）给足释放时间，不强加超时。
- **留口子不实现**:
  - **act 中途的瞬时恢复**（长任务执行中 CDP 闪断 → 涉及会话状态恢复,复杂且有副作用风险）——明确 defer。
  - **scope 内 step 级无短路：上游 step error 后，下游 step 在损坏环境上跑出误导性假失败**（真跑复现）——明确 defer，记边界。现象：scope 内 step 串行执行（Nova `run_scope.py` 列表推导 / Midscene `run-scope.ts` for 循环，**两腿对称、均无短路**），当一个 step 因网络/环境故障 error（如导航 SSL 失败），**同 scenario 后续 step 仍无条件执行**——它们在损坏环境（如 SSL 错误页）上跑，AI 断言忠实报告"页面没有预期内容"→ `failed`(`assertion_failed`)。这个 failed 是**上游故障的连锁果、非业务结论**，却与上游的 `error` 并列呈现，读者/agent 易误读成两件独立的事。**这不是 bug**（core 忠实并列记录、worker 无条件跑完，均符合各自契约；因果信息只存在于 worker 的串行循环，core 作为纯 reducer [0026](./0026-schedule-module.md) 物理上看不到跨 step 因果、也不该臆断），而是**此前从未被设计过的空白**——本 ADR 的 act-恢复 defer 只覆盖"让 error step 自己恢复"，未触及"error step 之后的下游 step 怎么办"。
    - **本轮只做渲染层缓解**（不碰执行逻辑）：cli 文本汇总 + RunReport index.html 对"同 scenario 内、`error` step 之后的 `failed` step"加视觉旁注（"前置 step 已 error，此判定可能不可信"）。**判据锁死"同 scenario 内上一 step `status==error` 之后"、只读既有 status 字段、不看 error_type、不改判定/severity、不下沉 core**（守 [0026](./0026-schedule-module.md) 纯 reducer 红线：这是对"error 之后的 failed"这个**可观测顺序事实**的排版，非 core 推断因果）。
    - **将来真做执行修复时的首选路线**（本轮不实现，记成本锚点）：worker 层 scope 内 step 短路——上游 step `status==error` 后，短路后续 step、标"因上游故障跳过"。**判据用 `status==error`（不看 error_type）**——这样无论哪腿、无论 network_error 还是 engine_error 都触发短路，两腿对称，也回避了下面记的"两腿 SSL 分类不对称"欠账对短路的影响。载体**首选独立 `step_skipped` 事件**（不进 `StepDone.status`），以回避 [0031](./0031-job-lifecycle-states-and-severity.md) 的 skipped 三硬约束（定死 job 级 / 不进 wire / "没花钱"，且 `session_id 必 None` 而 step 级发生在会话已起时）+ [0024](./0024-worker-core-protocol.md) wire 三态——不要以为能顺手复用 `Status.SKIPPED`。短路省钱（不烧后续 AI 断言）、报告干净；若 scenario 内有无依赖 step 会误伤，可给 scenario 级逃生标签（如 `@no-shortcircuit`）。**重议闸门复用下面 #「act 中途断连成高频」的同款判据**：单点手动复现尚不够，真成高频再实现。
  - **`ensure_workflow_definition` 自身的 SSL 故障**:它在重试循环外（单次廉价 boto3 调用,SSL 失败面远小于 CDP/websocket 握手——后者才是实测崩的点）。若它 SSL 失败 → 仍归 engine_error。已知小缺陷,可随真实失败样本扩充。
  - core job 重试时 trajectory 覆盖（run_id 不换,同一引擎重试可能覆盖上次 trajectory）——M 小、重试罕见,接受为已知小缺陷。
  - **超时/中止被杀 scope 的卡死现场 trajectory 不自动归集进 RunReport**：被杀那个 act **从未返回**，worker 经 `_collect_traj` 拿不到它的路径（`_Terminated` 是 `BaseException`、穿透 step 级 `except Exception`，`_collect_traj` 没机会跑），故它进不了 `report_refs`。该 act 的 trajectory **可能留在** `nova-trajectories/<session_id>/`（SDK 在中断清理时 flush 的 `.html`），**且可能不完整**（被中断，配套的 `_trajectory.json`/`session_summary.json` 往往没来得及写——实测被杀 scope 只剩孤零 `.html`）。唯一能自动捞回它的途径是**扫盘**，但不值当为此破 [0027](./0027-runreport-aggregation-index.md)「`report_refs` 是唯一真值、ReportStore 永不 stat/fetch/扫盘」铁律。靠 #2 已记下的 `session_id` 可手动定位该目录查看。**若未来「看卡死现场」成高频需求** → 按已论证的通用解法实现：**worker 经 `scope_started` 自报 `artifactsDir`（产物落点契约，可选字段）+ 执行 adapter 的中断收尾扫盘**——孤儿恢复属 **Engine adapter 的收尾职责**（本地扫目录 / 未来 Fargate 查 S3，因执行基底而异），**不放 ReportStore（不破铁律）、不放 worker 的 SIGTERM 路径（不碰会话清理）**。

## 重议

- 若持续性网络故障频发、乘积打满成真实痛点 → 引 circuit-breaker / 全局退避。
- 若 act 中途断连成为高频场景 → 另立 ADR 设计会话状态恢复。
