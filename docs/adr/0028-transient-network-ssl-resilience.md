# 网络/SSL 瞬时错误的鲁棒性：两层重试 + network_error 分类（务实加固，非 enterprise resilience）

> **Status:** Accepted

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
  botocore `EndpointConnectionError`/`ConnectionClosedError`/**`ConnectTimeoutError`/`ReadTimeoutError`**、urllib3 `ProtocolError`。
  **`socket.gaierror` 按 errno 细分（不整类当永久）**——`EAI_AGAIN`（DNS 临时抖动）判瞬时/可重试
  （对齐 Midscene 的 `EAI_AGAIN` 白名单，保两个引擎对 DNS 临时故障恢复力对称），其余 errno（`EAI_NONAME` 等永久）否决。
  不用宽 `OSError` 兜底（它与 `ssl.SSLError` 同继承 `OSError`、会把永久错也当瞬时），只匹配具体类型 + gaierror 按 errno 判。
- **botocore `ClientError`（服务端瞬时故障，按错误码/HTTP 状态码细分，非整类）**:AgentCore 起会话
  （`start_browser_session`）是 boto3 调用,服务端瞬时不可用/限流时抛 `ClientError`——它**直接继承 `Exception`、
  混着永久错**（`ValidationException`/`AccessDenied`）,**不能整类当瞬时**,须按码细分:
  - 读 `e.response["Error"]["Code"]` ∈ **瞬时码集**（`RequestTimeout`/`RequestTimeoutException`/`PriorRequestNotComplete`）
    **或节流码集**（`Throttling`/`ThrottlingException`/`ThrottledException`/`TooManyRequestsException`/`RequestLimitExceeded`/
    `SlowDown`/`ServiceUnavailable` 等）→ 瞬时;
  - 或读 `e.response["ResponseMetadata"]["HTTPStatusCode"]` ∈ **{500,502,503,504}** → 瞬时;
  - 其余 `ClientError`（4xx 客户端错、`ValidationException`/`AccessDeniedException` 等永久错）→ **不归 network_error**。
  - **码集对齐 botocore 权威常量**（`TransientRetryableChecker._TRANSIENT_ERROR_CODES`/`_TRANSIENT_STATUS_CODES`
    + `ThrottledRetryableChecker._THROTTLED_ERROR_CODES`）——**借判据、不借 API**:不硬构造 botocore 内部
    `RetryContext` 去调它的 `is_retryable()`（那要 http_response/parsed_response 等请求栈内部对象、跨版本脆，
    且我们 catch 到的是被 Nova SDK 包了两层的异常、根本没有 RetryContext）,而是把它那张稳定的码/状态码表**内联**成
    自己的白名单,判定对齐、无内部 API 依赖。**注意 SIGTERM 穿透仍靠我们的手写退避**（见上「worker 层退避」）——
    只借 botocore 的分类判据,绝不借它的重试执行（`time.sleep` 吞信号）。
- **穿透 Nova SDK 的两层包装靠异常链遍历（纠正旧猜测）**:AgentCore 会话建立失败时,底层 exc 被 Nova SDK
  包成 `BrowserAuthError(...) from exc`、再包成 `StartFailed(...) from e`（`agentcore_session_provider.py`/
  `nova_act.py`,**每层都带 `from`**）。故**不需要识别 `BrowserAuthError`/`StartFailed` 类本身**——
  `_is_transient_network` 遍历 `__cause__/__context__` 链能穿透到底层 exc 命中白名单。**真正的盲区是底层 exc 的
  类型/码没被白名单覆盖**（boto `ClientError` 节流/5xx、`ConnectTimeoutError`/`ReadTimeoutError`）,本 ADR 补齐。
- **建连阶段的「下游症状」异常按阶段判瞬时（真跑暴露的盲点补充）**：上一条"异常链能穿透到底层网络 exc"的假设**对一类真实故障不成立**——当 AgentCore 云端浏览器的 CDP/websocket 连接因网络断掉（如 `keepalive ping timeout`），**Playwright 内部把底层 socket 故障吞掉、只抛出一个"干净"的 `TargetClosedError`**（`CDPSession.send: Target page, context or browser has been closed`），它**不继承 `OSError`/`ConnectionError`、`__cause__`/`__context__` 均为 `None`**——异常链遍历穿透到底命中的就是这个不带任何网络语义的下游症状异常，白名单无从匹配 → 误判 `engine_error`、不重试（真跑 r2 复现：会话已 `start_browser_session` 成功，`with NovaAct.__enter__` 内 `CDPSession.send` 撞网络断 → `StartFailed`→`BrowserAuthError`，退 1 而非 80）。
  - **判据：`TargetClosedError` 语义模糊**（网络断 / 会话被正常关 / 浏览器真崩，都报同一句），整类当瞬时会违背下面「拿不准→不归 network」铁律。**故按阶段收窄**：只在**建连阶段**（`scope_started` 未 emit、`started=False`、act 无副作用——即已有的重试域物理边界）把 `TargetClosedError` 判瞬时；越过 `scope_started` 后（act 中途分类 `_classify_act_error`）**不认**它。依据：建连阶段 target 被关几乎必是建连期网络/连接故障（正常关闭/SIGTERM 走的是别的路径，且此阶段本就无 act 副作用、重试安全）。实现：`_is_transient_network(e, *, connecting=False)` 加阶段参数，仅建连域调用点传 `connecting=True`。这是**利用已有结构性保证（重试域=scope_started 之前）做精确收窄，不是宽兜底**，不违背「绝不重试 act」红线。
- **Node（Midscene）**:error code `ECONNRESET`/`ECONNREFUSED`/`ETIMEDOUT`/`EPIPE`/`EAI_AGAIN`/`ECONNABORTED`
  + TLS/握手类 message 匹配;**AWS SDK v3 服务端瞬时**——`error.name` ∈ 节流集（`ThrottlingException`/
  `TooManyRequestsException`/`ServiceUnavailable` 等）或 `error.$metadata?.httpStatusCode` ∈ **{500,502,503,504}**
  或 `error.$retryable?.throttling===true`。**排除 `ENOTFOUND`（DNS 永久）**、4xx 客户端错。
- **拿不准 → 不归 network_error**（归 engine_error、不重试）。明确非 network 的:鉴权失败、4xx、配置错、DNS 永久失败、`ValidationException`。

> **已知欠账：两个引擎对"导航 SSL 失败"的分类不对称**（真跑暴露、defer 不改）。同一瞬时 SSL 故障（如握手被 `UNEXPECTED_EOF` 打断）：**Nova** 引擎 `go_to_url` 抛异常，异常链底层含 `ssl.SSLError`/`SSLEOFError`，`_is_transient_network` 遍历 `__cause__/__context__` 命中 → `network_error`（准）。**Midscene** 引擎 `page.goto` 抛的是 Chromium 的 `net::ERR_CERT_*`（如 `ERR_CERT_AUTHORITY_INVALID`），其 message 文案**不含** `isTransientNetwork` 的 message 正则关键词（`ssl/tls/handshake/UNEXPECTED_EOF`）、也无对应 error code → 落 `engine_error`。**不盲改** Midscene 分类：因为 Chromium 把"瞬时握手中断"与"真证书错（过期/自签/域名不符，永久）"**都归成同一个 `net::ERR_CERT_*`、丢了区分**——盲目把 `ERR_CERT_*` 当瞬时会误判真证书错为可重试、无意义重试 N 次。**要真修需先用真 Midscene SSL 样本**（访问自签/过期证书站点真跑）确认 Chromium 到底报什么 code/message、能否区分瞬时 vs 真证书错，再决定分类。**注意**：这条分类不对称**不影响 step 短路**（[0031](./0031-job-lifecycle-states-and-severity.md) 决定六，现已实现）——短路判据锁 `status==error`（不看 error_type），两个引擎 error 都触发、行为对称；分类不对称只影响用户看到的 errorType 文案。

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
  内部 retry**:① 停止信号要能穿透退避;② 重试面可审计、有界。
- **停止信号穿透退避的机制**（随 [0024](./0024-worker-core-protocol.md) flag-only 中断模型更新）:退避用 `_stop.wait(backoff)`（`threading.Event.wait` 带超时）而非 `time.sleep(backoff)`——SIGTERM/SIGINT handler `set` 标志后 `wait` **立即返回**（实测 flag-only 下 `time.sleep` 不被打断、`Event.wait` 0.3s 内醒；PEP 475）。**被拒**：旧机制靠「`time.sleep` 被信号 handler 的 raise 打断」——已随 handler 去 raise 废弃（handler 不再 raise，`time.sleep` 会跑满，见 [0024](./0024-worker-core-protocol.md) 被拒方案）。
- 每次 attempt 用**全新**建连对象:Nova 新 `provider`+`cdp_session`+`NovaAct`（with `__exit__` 清掉本次部分会话）;
  Midscene 每次 attempt 失败先 `cleanup()` 释放本次可能已建的会话 + 重置 `browser`/`sessionId`。

## 会话泄漏防护（退出前清理）

- **Nova**:重试耗尽 → 置局部 `network_exhausted` 标志 + `break` → **正常退出三层 `with`**（`__exit__` 释放可能已建的会话，`@contextmanager` finally 正常/异常退出同样触发）→ main `return EX_WORKER_NETWORK`。**被拒**：旧用 `raise _NetworkExhausted(BaseException)` 穿透 `__exit__`——随 [0024](./0024-worker-core-protocol.md) flag-only 改造废弃（异常穿透对释放会话本非 load-bearing，`with` 正常退出即触发 `__exit__`；BaseException 穿透反引入 greenlet 撞车风险）。禁止 `with` 内裸 `sys.exit`（跳过 `__exit__`）不变。
- **Midscene**:退 80 前先 `await cleanup()`（`StartBrowserSession` 成功而 `connectOverCDP` 失败时会话已建）;
  **`cleanupFailed`（会话释放失败、可能泄漏）退 1 优先级高于退 80**——泄漏可观测性压过网络分类。
- **SIGTERM/SIGINT 竞态**:停止信号期间正在退避 → 不重试。**Nova（随 [0024](./0024-worker-core-protocol.md) flag-only 改造）**:handler 只 `set` 标志;重试循环顶 `if _stop.is_set(): break`、退避 `_stop.wait(backoff)` 被唤醒后同样 `break` → 不再重连、协作式退出释放会话。**被拒**：Nova 旧靠 `except _Terminated: raise` 在 transient 检查前抢先冒泡——随 flag-only 改造废弃（不再抢占，改协作式检测）。**Midscene（现状不改）**:handler 无条件 `process.exit` 抢占任何挂起的退避——Node 无 greenlet、`process.exit` 不撞 Nova 那种卡死，现状已满足契约（见 [0024](./0024-worker-core-protocol.md) 终止契约「Midscene worker（现状，不改为 flag-only）」）。

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
- **静默 worker 超时根治（真跑暴露）**:worker 卡在**单次操作内**（如 Nova act 内部反复重试 ~10 分钟、fd3 零新事件）时，schedule 的 `job_timeout` 曾**形同虚设**——deadline 检查只在 `for event in events` 循环体内跑，静默 worker 让该循环永久阻塞在读上，超时拖到被外层进程级杀（实测 300s 超时拖到 ~620s）。根治放在 **schedule 层**而非各 adapter：`_heartbeat_wrap` 把 adapter 的纯 `Iterator[Event]` 包成「事件 + 存活心跳」流——内层迭代搬到一个**后台 reader 线程**塞 `queue`，主侧 `queue.get(timeout=heartbeat_interval_s)` 超时没拿到（worker 静默）就 yield 一个 schedule 私有哨兵 `_HEARTBEAT`，让事件循环醒来查 `deadline`/`abort_flag`；拿到事件就转发、拿到内层异常就重抛（保 `WorkerNetworkError`/`ValueError` 分类不变）。**为何在 schedule 层做一次**：心跳是「持有 deadline 的消费方对任何慢/静默流的通用兜底」，与引擎无关——写一次对子进程/未来 Fargate/内存假实现全适用，`Engine` port **保持纯 `Iterator[Event]`**（不把轮询细节渗进契约、不必每个 adapter 各写一遍）。`_HEARTBEAT` 不是领域事件、不进 model/ports/wire、不归约、不 emit。事件正常流动时 `queue.get` 即时返回、永不注入心跳，故 fake-clock 单测的 clock 读取序列不变（reader 线程只搬事件、绝不读 clock）；无 `job_timeout` 时 `_heartbeat_wrap` 退化为直接转发、不起线程。
- **会话血缘随首事件回传**:`session_id` 原仅由 `scope_done` 携带——worker 被超时/SIGTERM 中途打断时 `scope_done` 从不 emit，core 侧 `run_state` 该 job 的 `session_id=null`，**会话明明已起却记不到血缘**（诊断/计费断线，正是上面静默超时场景的伴生缺口）。修复：worker 在 **`scope_started`** 即带 `sessionId` 回传（会话一起就报），schedule 的 `_reduce` 在 `ScopeStarted` 分支也捕获它；`scope_done` 仍带（冗余兜底）。`ScopeStarted` 协议加 optional `session_id` 字段。
  - **残留缺口：「会话已起 ⟷ `scope_started` 已 emit」之间仍有窗口（真跑暴露，defer 记录）**——上面「提前到 `scope_started`」的修复**假设这个时间差可忽略，但对 Nova 建连崩溃不成立**。Nova 的 `session_id` 由 `nova.get_session_id()` 取，而它**要 `with NovaAct.__enter__` 成功后才拿得到**；会话却在 `__enter__` **内部**（`start_browser_session` 成功）就已建立、开始计费。若崩在 `__enter__` 内（如 `CDPSession.send` 撞网络断 → `StartFailed`，即上「建连阶段的下游症状异常」条的 `TargetClosedError` 场景），worker **连 `get_session_id()` 都没执行到、更没 emit `scope_started`** → core 侧 `session_id=null`。**实测**：Nova 日志明写 `AgentCore browser session started: session=…`（会话真起、真计费），但 `run_state` 该 job `session_id=null`——**花了钱的会话血缘丢失**，排查/审计找不到它。
    - **为何「建连阶段识别 TargetClosedError」那条修复不连带解决它**：那条让此类故障归 `network_error` 并触发建连重试，但**重试耗尽后仍崩在 `__enter__` 内**——每个 attempt 都拿不到 id，最终血缘照样 null（那条修的是分类/重试，不是血缘回传，两者正交）。
    - **未来方向（要动协议，defer）**：真修需让 worker 在会话建立成功的更早点 out-of-band 上报 session_id（不等 `scope_done`）——现已提前到 `scope_started`（见上），进一步可走早于 `scope_started` 的带外信号（`session_opened` 事件 / 类似退出码 80）。**血缘回传越早、未来若做主动 reaper 能兜的窗口越大**——但不做 reaper（泄漏靠 AgentCore session TTL 兜底，见 [0024](./0024-worker-core-protocol.md)「已接受代价」），故此增强也 defer。
      - **SDK 硬限制（不因决策改变的事实）**：`get_session_id()` 与 `__enter__` 内已建立、已计费的时序见上。故 worker 层**拿不到「`__enter__` 内部那一刻」的 id**（SDK 私有）——血缘上报只能提前到 `__enter__` 返回后，**能缩小、但无法消除**「会话已计费而血缘 null」的窗口。真正消除需 SDK 暴露 early hook 或 core 侧从 CloudWatch 捞——超本 ADR 范围。
- **Midscene SIGTERM 会话泄漏两窗口已根治**:
  - **重试放大的 in-flight 会话窗口**:会话跟踪从「单一 `sessionId` 快照」重构为**待清理会话集**——每次 `StartBrowserSession` 成功即把 id 入集（含被重试丢弃的中间 attempt 会话），cleanup 遍历集逐个 Stop。彻底解决「重试时 sessionId 被后一 attempt 覆盖/置空 → handler 只能 Stop 当前快照、漏掉在途/已弃会话」。剩余仅「Start 已发 RPC 但 id 未返回」一瞬，由一个在途标记 + 短暂兜底等待覆盖。
  - **`StopBrowserSession` 超 `grace_period`**:每个 Stop 套超时预算（挂死即放弃、记 `cleanupFailed` 让泄漏可观测，不被 SIGKILL 打断到一半）；cleanup **并行** Stop（`Promise.all` 而非串行）——否则重试积累的 N 个泄漏会话串行会把 cleanup 拖过 grace 被 SIGKILL 截断（正是本修复要防的泄漏）。并行后最坏 cleanup 墙钟与会话数无关、< cli 默认 grace。常量值与算术见 `run-scope.ts`（代码为准，ADR 不复制以免漂移）。
  - **Nova 引擎不对称（不动，SDK 限制）**:Nova 无 in-flight 窗口（建连在 `with cdp_session` 内、`__exit__` 结构性清理）；但其 `StopBrowserSession` **在 Nova SDK 的 `AgentCoreBrowserSessionProvider.cdp_session().__exit__` 内部**，是 SDK 黑盒——**无法在 worker 层套超时预算**（不像 Midscene 是自己 `cp.send(StopBrowserSessionCommand)`）。硬加 worker 级看门狗 `os._exit` 会跳过 SDK 剩余清理、反而可能更多泄漏。故 Nova 侧依赖 schedule 的 `grace_period` 给足释放时间，不强加超时。
    - **grace 值随 [0024](./0024-worker-core-protocol.md) flag-only + act timeout 改造上调（连带硬约束）**:旧值 cli 默认 10s（当时只需够 SDK maxAttempts=3 的释放）。改 flag-only 软停后，SIGTERM 到达长 act 中途时须**等 in-flight act 到安全点返回**才能协作式退出释放会话（act 有界返回靠 per-act `timeout=ACT_TIMEOUT_S`，见 [0024](./0024-worker-core-protocol.md)）——故 `grace ≥ ACT_TIMEOUT_S + 单 step 最坏耗时 + 会话释放耗时 + 余量`。若 grace < act_timeout，SIGKILL 必先于 `__exit__` 到 → 会话泄漏、软停白做。具体 grace/act_timeout 值真跑标定（此前 10s 远小于任何合理 act_timeout）。放大的泄漏窗口由 **AgentCore 原生 session TTL** 兜底（`sessionTimeoutSeconds`，默认 1h、可收紧；不做 core reaper，见 [0024](./0024-worker-core-protocol.md)「已接受代价」）。
- **scope 内 step 级短路（已实现，[0031](./0031-job-lifecycle-states-and-severity.md) 决定六）**：上游 step error 后，下游 step 在损坏环境上跑出误导性假失败（真跑复现）。原现象：scope 内 step 串行执行（Nova `run_scope.py` / Midscene `run-scope.ts`，**两个引擎曾均无短路**），一个 step 因网络/环境故障 error（如导航 SSL 失败）后，**同 scenario 后续 step 仍无条件执行**——在损坏环境（如 SSL 错误页）上跑，AI 断言忠实报告"页面没有预期内容"→ `failed`(`assertion_failed`)。这个 failed 是**上游故障的连锁果、非业务结论**，却与 `error` 并列呈现，读者/agent 易误读成两件独立的事。**这不是 core 的 bug**（core 忠实并列记录、纯 reducer [0026](./0026-schedule-module.md) 物理上看不到跨 step 因果、不该臆断），修复归 **worker**（因果信息只存在于 worker 的串行循环）。
  - **执行修复（现已实现）**：worker 层 scope 内 step 短路——上游 step `status==error` 后，**不再对后续 step 调 AI**（省钱、报告干净），为每个被跳过的 step 发独立 `step_skipped` 事件（[0024](./0024-worker-core-protocol.md) wire 加此事件）；core 据此本地构造 `StepResult(status=SKIPPED, shortcircuited=True)`。**判据锁 `status==error`（不看 error_type）**——无论哪个引擎、network_error 还是 engine_error 都触发短路，两个引擎对称，也回避了下面记的"两个引擎 SSL 分类不对称"欠账对短路的影响。承载/不变量（独立事件而非 status 第 4 态、SKIPPED 只在 StepResult 层不进 wire、绝不写 scenario_status）详见 [0031](./0031-job-lifecycle-states-and-severity.md) 决定六。
  - **渲染层旁注同步升级**：cli 文本汇总 + RunReport index.html 的连锁失败旁注**判据从「error 后 failed」迁到读 `shortcircuited`**——被短路的 step 直接显 skipped 态 + "因上游故障跳过"旁注，比原「按 status 顺序猜」更精确、判据单一。仍不改判定/severity（守 [0026](./0026-schedule-module.md) 纯 reducer 红线）。
  - **仍留的口子**：若 scenario 内有**无依赖** step，短路会误伤（它本可独立跑）——可给 scenario 级逃生标签（如 `@no-shortcircuit`）豁免，真遇到需求再加。
- **留口子不实现**:
  - **act 中途的瞬时恢复**（长任务执行中 CDP 闪断 → 涉及会话状态恢复,复杂且有副作用风险）——明确 defer。
  - **`ensure_workflow_definition` 自身的 SSL 故障**:它在重试循环外（单次廉价 boto3 调用,SSL 失败面远小于 CDP/websocket 握手——后者才是实测崩的点）。若它 SSL 失败 → 仍归 engine_error。已知小缺陷,可随真实失败样本扩充。
  - **成功重试对 RunResult 完全透明——「本轮抖了多少」不可观测（已知边界，真跑暴露）**：worker 层建连重试**成功**后（如实测 r1 连撞 3 次瞬时故障、第 4 次成功），最终 `JobResult` 就是干净的 `passed`——**重试次数、每次失败原因都只在 worker 的 stderr 日志里，不进 RunResult/RunReport**（成功重试=不记 error，是本 ADR 开头「务实止血、非 enterprise resilience」定位的有意取舍）。两个衍生的不可观测面：
    - **重试次数**：「本轮环境抖了几次自愈」这个环境健康度信号丢失。跨 run 统计「近期建连失败率」需另抓 stderr、无结构化出口。
    - **重试/建连耗时**：`JobResult.duration_ms` 是 `scope_started→scope_done` 墙钟（[0024](./0024-worker-core-protocol.md)），**建连+重试全发生在 `scope_started` 之前**，故这段耗时既不进任何 scope 墙钟、也不单列——只隐没在 `RunResult.duration_ms`（run 总墙钟）里。实测：r1 3 次重试（光 attempt 1 的 CDP 超时就 30s）+ Nova 会话建立固有延迟（~40s）使总墙钟 249s 远大于两 scope 墙钟之和 67s，读者看「跑了 4 分钟但 scope 才 1 分钟」会困惑，却无处解释这 ~182s 去哪了。
    - **不影响正确性**（判定/成本正确；**血缘在此「成功重试」语境下也对**——会话最终成功建立、`scope_started` 已 emit、id 已回传。注意区别于上「会话血缘残留缺口」：那是**建连崩溃**场景，`scope_started` 从未 emit、id 才丢），纯可观测性缺口。**增强方向**（真需要时做）：worker 经 `scope_started` 自报 `connectAttempts`（重试次数，可选字段）+ core 用「首个 worker 事件到达 − worker spawn」测「建连墙钟」落进 `JobResult`（新增 optional 字段，与 scope 墙钟正交）；两者都进 RunResult → RunReport 可展示「本轮 N 次自愈重试、建连耗时 Xs」。重议闸门见下。
  - core job 重试时 trajectory 覆盖（run_id 不换,同一引擎重试可能覆盖上次 trajectory）——M 小、重试罕见,接受为已知小缺陷。
  - **SIGKILL 硬杀中断的 act 的卡死现场 trajectory 不自动归集进 RunReport**（随 [0024](./0024-worker-core-protocol.md) flag-only 改造收窄）：**flag-only 软停下大部分中断 act 的轨迹能归集**——SIGTERM 只置标志，in-flight act 靠 per-act `timeout=ACT_TIMEOUT_S` 有界返回（正常完成，或抛**可 catch 的** `ActTimeoutError`，[0024](./0024-worker-core-protocol.md) act 有界返回），worker 在 act 边界安全点**有机会**跑 `_collect_traj` 抢传该 act 轨迹、经 `step_done.reportRefs` 正常归集（act 边界抢传经中断实测预演证实有效：最严酷的 SIGKILL 卡死场景下仍零丢失，因每步轨迹在 act 边界即抢传、不依赖优雅停或 scope 末 flush）。故孤儿收窄到 **grace 超时被 SIGKILL 硬杀**（grace < act_timeout，或 act 卡到 grace 耗尽）：此时 act 从未返回、worker 到不了安全点、`_collect_traj` 没机会跑 → 该 act trajectory 进不了 `report_refs`。它**可能留在** `nova-trajectories/<session_id>/`（SDK 在中断清理时 flush 的 `.html`）、**且可能不完整**（配套 `_trajectory.json`/`session_summary.json` 往往没来得及写——实测 SIGKILL scope 只剩孤零 `.html`）。唯一能自动捞回它的途径是**扫盘**，但不值当为此破 [0027](./0027-runreport-aggregation-index.md)「`report_refs` 是唯一真值、ReportStore 永不 stat/fetch/扫盘」铁律。靠上「会话血缘随首事件回传」条已落到 core 的 `session_id` 可手动定位该目录查看（前提是会话起后 `scope_started` 已 emit；若崩在建连中途则见该条的「残留缺口」）。**若未来「看卡死现场」成高频需求** → 按已论证的通用解法实现：**worker 经 `scope_started` 自报 `artifactsDir`（产物落点契约，可选字段）+ 执行 adapter 的中断收尾扫盘**——孤儿恢复属 **Engine adapter 的收尾职责**（本地扫目录 / 未来 Fargate 查 S3，因执行基底而异），**不放 ReportStore（不破铁律）、不放 worker 的中断路径（不碰会话清理）**。**⚠️ 但 Fargate 侧此路已被 [0032](./0032-fargate-execution-environment.md)「重议」孤儿 reaper 条否决——物理不成立**：Fargate 容器盘停即销毁，没传 S3 的残余随盘没了、「查 S3」只能确认已传的、捞不回没传的。故上述「Fargate 查 S3」的通用解法**仅在** worker 产物落点改为持久卷/实时流式（残余不随盘销毁）时才成立；当前容器盘模型下是伪需求。本条的 subprocess「本地扫目录」路径不受此否决影响（残余真留本地盘），但 subprocess 残余本就「留盘可手动找、不算丢」、同样不值当自动化。

## 重议

- 若持续性网络故障频发、乘积打满成真实痛点 → 引 circuit-breaker / 全局退避。
- 若 act 中途断连成为高频场景 → 另立 ADR 设计会话状态恢复。
- **若「环境抖动率/建连耗时」成为需要跨 run 监控的运维信号**（如 CI 里频繁自愈重试拖慢批次、或需按环境健康度告警）→ 兑现上面「成功重试对 RunResult 透明」条记的增强：`connectAttempts` + 建连墙钟进 RunResult/RunReport。当前只单点真跑暴露、无监控需求，defer。
