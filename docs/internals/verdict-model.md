# 判定的计算路径：从单次投票到退出码

> 本文讲**判定如何被计算**（机制），不讨论为什么这样设计：设计决策与理由在各 ADR，本文只给指针；与代码或 ADR 不一致时以它们为准。一个 run 的「结论」要经过四层归约、两根正交的轴、七个状态，以及各命令语义不同的退出码。单个 ADR 各只覆盖其中一片（0014 投票、0031 状态与 severity、0034 脱离后的退出码等），本文是这些切片合成的全景视图。

姊妹页分工，本文不越界：worker 如何被启动、事件如何送到 core、超时计时由谁负责、四种组合的推进链见[执行与推进模型导览](./execution-and-reconciliation.md)；`status` / `error_type` / `votes` 在 `--json` 里的**字段名、类型、出现条件**见 [CLI `--json` 字段契约](./cli-json-contract.md)（本文不重复它的表）；每步证据的读法见 [artifacts-and-evidence](./artifacts-and-evidence.md)；确定性 step 的写法与派发见 [deterministic-step-lifecycle](./deterministic-step-lifecycle.md)；判定与运行态落在哪张表、哪个桶见 [cloud-backend-carriers](./cloud-backend-carriers.md)。

## 1. 四层归约：票 → step → scenario → job → run

判定由**逐层归约**产生，每层都有一个明确的真值符号。core 不重算票、不重判 step，上层只做归约。

| 层 | 结论的判定规则 | 真值符号 |
|---|---|---|
| **票**（单次投票） | 一次布尔 AI 调用的返回值 | Nova：`act_get(instruction, BOOL_SCHEMA)` → `bool(r.matches_schema and r.parsed_response)`；Midscene：`agent.aiBoolean(instr)` |
| **step** | AI 断言（`Then`）：`yes > N/2` → `passed`/`failed`，事件带 `votes={yes,total}`。确定性注册表命中（含内建导航）：`AssertionError`→`failed`、其它异常→`error`。`When`·`Given` 的 AI 动作步：正常返回→`passed`、抛异常→`error` | `_run_step`（Nova）/ `runStep`（Midscene） |
| **scenario** | 任一 step `error`→`error`；任一 `failed`→`failed`；否则 `passed`。**被短路跳过的 step 不进入该列表** | worker 侧 `_aggregate` / `aggregate`；结论经 `scenario_done` 事件上报 |
| **job**（即 scope） | 同步 `run` 与无状态批量运行共用一个终结函数与真值表（ADR 0034 机制二）：按行序取第一个命中——推进器首次仲裁落定的停止原因（timeout / abort，只约束内容不完整的 job）→ 退出码非零或未知 → 干净退出无 `scope_done` → `scope_done` 带 scope 级 error → scenario 判定集为空 → 各 scenario 归约；会话未确认停止时，非零退出、scope 级 error 与正常归约三处的归因改 `release_failed`、其余行只追加提示（§3c 图画的是同步路径的事件收场） | `project.finalize_job`（`schedule._Worker._run_once` 与 `project._reduce_scope` 只准备输入） |
| **run** | 任一 job `error`→`error`；任一 `failed`→`failed`；否则 `passed`。**入口先滤掉非判定状态** | `project._aggregate`（唯一实现，`schedule._aggregate` 是它的别名） |

几点补充：

- **N 的来源**：`Job.assertion_votes`（CLI `--assertion-votes`，默认值见 `--help`）。阈值是多数票 `yes > N/2`，两个引擎各自实现同一式子。`total == 1` 时，`run` 的人读输出（实时事件行与终态汇总，`render.py` 的 `format_event` / `render_text`）与报告 `index.html` 的 step 行都以 `total > 1` 为显示条件，不显示 tally；`explain` 的逐步视图**有意**不设这道闸，`votes 1/1` 照常显示——`votes` 字段本身就是「这是 AI 断言」的标记，供 agent 分辨（ADR 0042 决策四）。机读层（`--json` / evidence）始终给出完整 `votes`。
- **core 只转录、不判定**：`project.reduce_event` 把 `StepDone` 的 `status`/`votes`/`error_type`/`message`/`report_refs` 原样写入 `StepResult`；scenario 判定**只**由 `ScenarioDone` 事件写入 `scenario_status`，`step_done` 分支不修改它。
- **同步与无状态两条路共用同一份归约**：`reduce_event`（单事件归约）和 `_aggregate`（终态聚合）都定义在 `core/gherkai_core/project.py`，`schedule` 委派给它。同步 run 沿事件流实时输入，reconciler 从持久事件全量重放输入，两条路径收敛到同一终值。

![票 → step → scenario 在 worker 侧逐层汇总，跨进程上报后由 core 归约出 job 与 run 的判定](../diagrams/verdict-model-reduction-layers.svg)

> 图注：图给出层次、方向与 worker / core 的分界；每层规则见上表。三处不走这条链的旁路见 §3a（短路 step）、§3c 图（job 收场判据）、§4（run 归约入口过滤）。

> 权威：[ADR 0014](../adr/0014-ai-first-assertions.md)（AI 断言与投票纪律）、[ADR 0024](../adr/0024-worker-core-protocol.md)（事件协议、三态、投票 tally 字段）、[ADR 0026](../adr/0026-schedule-module.md)（三级归约）、[ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md) 决定三（`_aggregate` 入口过滤）；code：`core/gherkai_core/model.py`、`project.py`、`schedule.py`、`engines/novaact/gherkai_worker_novaact/run_scope.py`、`engines/midscene/src/worker/run-scope.mts`。

## 2. 七个状态：含义与处置

`Status`（`core/gherkai_core/model.py`）共七个值：**五个终态** + **两个前置态**。`TERMINAL_STATUSES` 是终态的单一真源，且**取补而非正列**（`frozenset(Status) - _PRE_TERMINAL`），所以新增终态自动进入该集合。

| 状态 | 赋值方与位置 | 出现在哪几级 | 含义 | 处置 |
|---|---|---|---|---|
| `passed` | worker 上报 / core 归约 | step·scenario·job·run | 断言全部通过 | — |
| `failed` | worker 上报（未过多数票 / 确定性 `AssertionError`） | step·scenario·job·run | **测试发现了问题** | 先看现场、不要直接重新运行：`gherkai explain <run_id>` 逐步查看向 AI 提出的断言与 AI 的观察；报告中有引擎原生 report / trajectory |
| `error` | worker 上报（act 抛异常）/ core 派生（各条收场判据见 §3c 图） | step·scenario·job·run | **测试未能执行完成** | 先按 `error_type` + `message` 归因（§3b）：`timeout`/`network_error` 多数可原样重新运行；`engine_error`/`guardrail` 先查 worker 日志 |
| `skipped` | **core 本地赋值**（三处，见 §3a / §3c 图） | job（fail-fast 下 worker 从未 spawn）· scenario 与其 step（scope 级 error 后对无事件的 scenario 合成）· step（scope 内短路） | 该单元未执行 | job 级：未执行、未产生费用，可直接重新运行（但整个 run 里必然伴随另一个 job 的 `error`，根因在别处）。scenario 级：根因是 job 级的 scope 级 error，看 job 的 `error_type` 与 `message`。step 级：根因是其上游的 `error` step，或所属 scenario 整条未执行 |
| `aborted` | **core 本地赋值**（终结函数：停止原因为 fail-fast 中止、且内容不完整） | job | 已启动，运行中被终止 | **不宜直接重新运行**：会话已被操作过、可能留下副作用；先查现场（`session_id` 已保留，可对上 worker 日志；Nova Act 的轨迹目录按日志里对应的另一种会话 id 找） |
| `pending` | `create_run` 写初始态 | job（`JobState`）·run（`RunState`） | 尚未启动 | 等待；提交较久而**所有** job 仍为 pending 时，`status` 会提示用 `--wait` 接力推进 |
| `running` | 收到 `scope_started` 或 `origin` 不是 `attempted` 的 `session_opened`（取设备期间）后写入，只有 `attempted` 的 `session_opened` 时仍为 `pending` / 无状态路径 CAS claim | job·run | 执行中 | 等待 / `status --wait` |

两条边界容易读错：

- **worker 只上报三态**。`wire.py` 的 `event_from_json` 对 `step_done`/`scenario_done` 调 `Status(d["status"])`，对 `scope_done` 只接受可选的 `status: "error"`（与 `error_type` / `message` 同进同出，是 scope 级 error 的载体；不带它们的 `scope_done` 仅作「内容完整」信号），wire 上能出现的只有 `passed`/`failed`/`error`。其余四态全是 **core 内态**：`skipped` 与 `aborted` 由 core 本地构造：job 未启动时由 `schedule._Worker._run_once` 记 `skipped`，被终止时由终结函数记 `aborted`，scope 级 error 后的合成与 scope 内短路由 `reduce_event` 记 `skipped`，`pending`/`running` 由实时写入落库。
- **前置态绝不进入判定真值**。`JobResult.status` 只会是五个终态之一；强制点在 `project.project_full`：收尾聚合时任一 job 仍非终态即抛 `NonTerminalSnapshot`，该轮 tick 不落任何判定，`running` 因此不会混进 `jobs/*.json`。同步 run 路径的归约器只产出终态。前置态同样不在 severity 表内（§4）。

> 权威：[ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md) 决定一 / 决定一·补（两组派生态的定义、行动含义、`TERMINAL_STATUSES` 取补）、[ADR 0024](../adr/0024-worker-core-protocol.md)（wire 三态）、[ADR 0030](../adr/0030-realtime-persistence-seam.md)（pending/running 何时被写）。

## 3. 两根正交的轴与 `error_type` 类别集

### 3a. `status` × `shortcircuited`

`StepResult` 有两个独立维度：`status` 表示执行得出的结论，`shortcircuited: bool` 表示 `skipped` 的原因。

一个 scenario 内某 step 报 `error` 后，worker **不再对后续 step 调 AI**（既省去费用，也避免在已损坏的环境上产生误导性的 `failed`），改为给每个被跳过的 step 发一条独立事件 `step_skipped`（与 `step_done` 平行，无 `status`/`votes`/`cost` 字段——「该步未执行」是执行事实、不是判定结论，因此不纳入三态）。core 收到该事件后就地构造 `StepResult(status=SKIPPED, shortcircuited=True, duration_ms=None)`。

**该事件绝不污染上层。** `reduce_event` 的 `StepSkipped` 分支只把 `StepResult` 暂存、待挂载到所属 scenario，**不写 `scenario_status`**，因此完全不参与 scenario 归约（`_aggregate` 的 `_NON_VERDICT` 过滤是第二层保险）。scenario 与 job 的判定由上游那个 `error` step 决定，与其后短路了几步无关。渲染层的连锁失败旁注读 `shortcircuited` 这个布尔（`render.py`：`⚠ 因前置 step error 被跳过（未执行）`），不依赖按 `status` 顺序推测。

短路判据是 `status == error`（不看 `error_type`），两引擎对称；短路只作用于**本 scenario**，跨 job 的中止由 fail-fast 负责，两者正交。

**三级 `skipped` 判据不同，不可混同**：

| | 被 skip 的对象 | 是否有 `StepResult` | 是否已计费 |
|---|---|---|---|
| **job 级**（fail-fast） | 整个 job 从未 spawn | 无（`JobResult.scenarios=[]`） | 否，`session_id` 必为 `None` |
| **scenario 级**（scope 级 error 后合成） | definition 里没有任何事件的 scenario 及其全部 step | 有（scenario 记 `skipped`，各 step `shortcircuited=False`、文本旁注「未执行（scope 级错误，原因见 job 判定）」） | 视情形：执行前失败未建会话则否；执行中途会话丢失则是 |
| **step 级**（scope 内短路） | job 已启动，上游 error 之后的各 step | 有（`shortcircuited=True`） | 是，会话已建立、前面的 step 已计费 |

### 3b. `error_type`：赋值方与取值

类别集的单一事实源是 `model.ErrorType`（一个 `Literal`，**有意不用作字段注解**——wire 必须容忍 worker 上报的未知类别，因此各 `error_type` 字段的类型都是 `str | None`）。

| `error_type` | 伴随 status | 赋值方与位置 |
|---|---|---|
| `assertion_failed` | `failed` | worker：AI 断言未过多数票（message 带 `yes/N` 与断言文）/ 确定性 `AssertionError` |
| `timeout` | `error` | ① core：job 墙钟预算到点（判据与无状态路径口径见 §3c 图）② Nova worker：单次 act 到点（`_classify_act_error` 识别 `ActTimeoutError`） |
| `guardrail` | `error` | Nova worker：SDK 护栏异常（`ActGuardrailsError`/`ActStateGuardrailError`）。Midscene 侧无此细分 |
| `network_error` | `error` | 两侧 worker：act 执行中的瞬时网络故障（**仅分类、不触发重试**，因为 act 不幂等）；core：worker 以网络专用退出码退出（判据见 §3c 图） |
| `engine_error` | `error` | 默认类别：worker 其余未细分的异常；core 侧各条收场判据见 §3c 图 |
| `navigation_error` | （`error`） | **协议中已声明、当前无生产者**：两引擎的导航失败按异常性质归入 `network_error` 或 `engine_error` |
| `precheck_failed` | `error` | worker（scope 级，经 `scope_done{status: error}`）：执行前判定这次执行无法开始、重试不会变（建会话前的自检不过：job 行结构版本不符、目标不受支持、墙钟预算超过会话上限；会话预热被拒，或后端未传递会话预热地址；设备目标另有零候选、应用缺失或启动即自退等情形，完整清单见 ADR 0051 决策 4） |
| `acquire_timeout` | `error` | worker（scope 级）：获取设备超过预算 |
| `session_lost` | `error` | worker：会话在执行中途被外部停止或到期（当前 step 的 `step_done` 与随后的 `scope_done` 都带它） |
| `capability_unavailable` | `error` | worker（step 级）：这一步需要的能力当前目标不提供、重试不会变 |
| `release_failed` | `error` | core：终结函数从会话事件配对推出有会话未确认停止时改写归因（worker 不直接报）；原归因的消息保留，其后追加按目标给出的提示（桌面目标指向 Amazon Bedrock AgentCore 控制台，设备目标指向设备控制台）与未确认停止的会话名 |

`skipped`/`aborted` 的 `error_type` 恒为 `None`——这两种状态下未产出判定的原因只写在 `message` 里，因此人读渲染在无分类时仍显示 `message`，否则输出只剩一个状态值。

### 3c. job 收场态与 `error_type`：归因的优先级

同步 `run` 中一个 job 的收场态由一串**有序短路**的判据决定：先看它是否在启动前就被 fail-fast 中止，再看是否被主动中止，最后才看事件流如何结束（起不来也算一种结束：退出码未知）。

![四问构成一串有序短路：fail-fast 中止 → 起 worker（起不来按退出码未知进后面的判据）→ 是否被主动中止 → 退出是否干净、内容是否完整 → 有无 scope 级 error；任一条件命中即记录收场态，全部未命中才做 scenario 归约](../diagrams/verdict-model-job-outcome.svg)

> 图注：本图只画同步 `run`。起 worker 失败不单独定案：按退出码未知进后面的判据——已过 deadline 或已被 fail-fast 中止的照常按停止原因记，否则落在「非零退出或不全」记 `engine_error`。「被主动中止」那道分叉的判据是推进器**首次仲裁**落定的停止原因（ADR 0034 机制二）：作出停止决定的那一刻 deadline 已过就记超时，否则记 fail-fast 中止；这个原因一经落定，worker 之后以什么退出码退出、内容是否完整都不改写它。「非零退出或不全」一问合并了退出码非零、退出码未知与干净退出却没发 `scope_done` 三种情形，其中只有网络专用退出码记 `network_error`。`scope_done` 自带 error 时取 worker 报的归因，这一问排在空判定集检查之前，因此 worker 在执行前报的失败保留自己的归因；没有任何 scenario 判定时记 `engine_error`（图上写在归约框里）。图上未画的两条贯穿规则：远程访问会话未确认停止时，非零退出、scope 级 error 与正常归约三处的归因都改为 `release_failed`（原因消息保留）；内容已完整（干净退出且发了 `scope_done`）的 job 不受「被主动中止」一问约束——收尾拖过预算时推进器只催停，判定按后面几问给出。停止决定之后同步路径继续读完 worker 的收尾事件（最多到停止宽限加余量，从停止请求时刻起算），再调终结函数。无状态批量运行走另一条链，退出记录落库后在收敛时调同一个终结函数：`skipped` / `aborted` 不出现（该路径没有 fail-fast），超时由退出记录的 `timed_out` 给出，非零退出按退出码细分（网络故障退出码为 `network_error`、其余 `engine_error`），启动 task 失败落平台侧哨兵退出码。与姊妹页[执行与推进模型导览](./execution-and-reconciliation.md) §6 那张图的分工：那张讲**如何把 worker 停下来**，本图讲**停下来之后记什么状态**。

几处判据的由来与边界：

- **判据不看「是否被自己停过」**：超时与 fail-fast 两条路径都会主动停 worker，被停的 worker 随后可能以网络故障退出码退出，所以那道分叉只取图注所说的首次仲裁结果（`stop_reason`），不看笼统的「被停过」标志。`abort_flag` 只负责传播 fail-fast 请求，排队中的 job 起 worker 前看到它即记 `skipped`，它不作归因依据。无状态路径的 `TaskExited.timed_out` 对应 `stop_reason = timeout`，因为该次停止本就由超时处置发起。这样切分的理由见 [ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md) 决定一的注（「aborted 只认 fail-fast」）。
- **`skipped` 不覆盖建连失败的原因**：建连失败的 job 已经建立过会话、已经计费，`saw_step == False` 只表示「可安全重试（无 act 副作用）」、不表示「未产生费用」，因此它照常进入 run 级聚合，`skipped` 的边界严格停在「worker 从未 spawn」。现状补充：`ScheduleOpts.network_retry` 默认 0 且 CLI 未暴露该参数，所以当前 `run` **不做**整个 job 的重新运行；生效的只有 worker 自身的建连退避（`_CONNECT_ATTEMPTS` / `_BACKOFF_S`，只包裹幂等的建连段），重试耗尽即以网络专用退出码退出。
- 另一条边界：worker 收到停止信号时**不为未执行完的单元生成判定**——Nova 在投票循环与 step 循环开头检查停止标志，票数未投满就不 emit 带判定的 `step_done`、也不发 `step_skipped`；Midscene 执行 SIGTERM 收尾序列（释放会话 → 安全点提前上传 → 排空队列）。两侧都把未完成的单元交由 core 按派生态处理，区别只在停止的处置形态。

> 权威：[ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md) 决定六（`step_skipped` 事件 + `shortcircuited` 正交布尔 + 「绝不写 `scenario_status`」不变量）、决定一（skipped/aborted 边界）、[ADR 0028](../adr/0028-transient-network-ssl-resilience.md)（两层重试、`network_error` 白名单、「绝不重试 act」、core 层 job 重试门槛）、[ADR 0024](../adr/0024-worker-core-protocol.md)（协作式停止、退出码 out-of-band 通道）、[ADR 0051](../adr/0051-device-session-lifecycle-and-app-distribution.md) 决策 4（scope 级 error、后五个归因类别与 `release_failed` 的推出）；code：`model.py` 的 `ErrorType`/`StepSkipped`/`StepResult.shortcircuited`、`project.reduce_event`、`schedule._Worker._run_once`、两个 worker 的 `_classify_act_error` / `isTransientNetwork`。

## 4. severity：数值序而非字母序；run 级为何不含 skipped/aborted

`_STATUS_SEVERITY`（`model.py`）给**终态**定义了一套数值序：

```
skipped = -1  <  passed = 0  <  failed = 1  <  error = 2  <  aborted = 3
（skipped 最轻：未执行，可忽略；aborted 最重：有现场，需人工查看）
```

两点约束：

1. **不得直接比较 `Status` 字符串的大小**。字母序 `'error' < 'failed' < 'passed'` 与严重度**完全相反**；比较须查表或调用 `severity()`。前置态查表会抛 `KeyError`（它们不是判定结论，无 severity）。
2. **这张表当前的角色是约定，不是计算引擎**。`_aggregate` 用显式 `any(...)` 实现三态归约（在三个判定状态上与「取 severity 最大值」等价）；报告配色是按同一序**手工映射**的另一张表（`core/gherkai_core/adapters/report_store/local.py` 的 `_STATUS_COLOR`：passed 绿 / failed 红 / error 琥珀 / skipped 弱化灰 / aborted 紫 / pending·running 蓝——每态各一色，均不落默认灰，否则 aborted 的严重度无法辨识）；`severity()` 本身当前只被单测引用（`core/tests/test_lifecycle_states.py` 有一行断言了完整的严重度序）。**新增终态时 `_STATUS_SEVERITY`、`_STATUS_COLOR` 与终端配色 `STATUS_STYLE`（`runtime/gherkai_runtime/textui.py`，ADR 0047）三处须同时修改。**

两个相邻但**判据不同**的集合不可混用（二者在 skipped/aborted 上有意重叠）：

| 集合 | 切分维度 | 含 skipped/aborted？ | 引用方 |
|---|---|---|---|
| `TERMINAL_STATUSES` | 生命周期（状态是否还会变） | 含 | `--wait` 轮询、`status` 退出码判定与仅在终态打印的产物位置、`explain` 的「run 仍在运行」提示与「判定明细尚未落地」提示、`project_full` 的不变量检查、云端推进器 Lambda 的「已收尾的 run 不再推演」跳过判据（`deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`：读到终态即 no-op，见 [`execution-and-reconciliation.md`](./execution-and-reconciliation.md)「已终态 run 在两个后端的重入」）、隧道守护的拆除判据（`runtime/gherkai_runtime/tunnel_host.py`：读到终态即提前拆除，否则等满 TTL）；另有一处**取补**用法——revision 清理的运行中 run 引用检查，判断是否仍有未达终态的 run 引用（`deploy_aws/gherkai_deploy_aws/workers.py`）。跨栈护栏要求消费方全部引用这一份、不各自维护白名单 |
| `_NON_VERDICT` | run 级判定（是否算作结论） | 含（**另含** pending/running） | `_aggregate` 入口过滤 |

**run 级永不出现 skipped/aborted**：`_aggregate` 在入口就把它们连同两个前置态滤掉，因此 `RunResult.status` 只会是 `passed`、`failed`、`error` 三者之一。这条过滤在无状态投影路径上是**承重**的：`project` 每轮 tick 全量重放，`jobs_state` 确实含 pending/running 的 job 并原样传入；同步 run 路径传入的全是终态，过滤为 no-op。

控制面的 `RunState.status` 多两个可能取值：执行期间为 `pending`/`running`（同步 `run` 路径全程保持 `pending`，由 `finalize` 一次落终态；无状态路径每轮投影写按 `projected_run_status` 钳在 pending/running）。run 级终态是 `finalize` 这个提交点的专属，提前落终态会使 run 永不 finalize。

> 权威：[ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md) 决定二（severity 序、视觉映射、「run 级为何不含 skipped/aborted」的洞察）与决定三（入口过滤）、[ADR 0034](../adr/0034-detached-batch-reconciler.md) 机制三（投影写钳制）、[ADR 0030](../adr/0030-realtime-persistence-seam.md)（提交点）。

## 5. 退出码：各命令的语义不同

各命令每个退出码的含义见 [`running-and-results.md`](../user-guide/running-and-results.md)「退出码」，部署方命令 `deploy` / `destroy` 见 [`cloud-backend.md`](../user-guide/cloud-backend.md)「退出码与常见错误」；本节只讲判定从哪里来、CI 应接哪一条。

归纳：**表达判定的只有 `run` 与 `status`，也只有它们会以退出码 1 结束**；`submit`/`plan`/`explain`/`doctor`/`list-deterministic`/`skill install` 都是 0/2 的「成功 / 失败」；`list-engines` 恒 0（某个引擎未安装正是它要展示的信息）。

`run` 表判定的退出码取 `schedule` 返回的内存 `RunResult.status`（必为终态，不回读可能停在 pending 的落库态）；`status` 的则取读回的落库 `RunState`。两路 `status`（local/cloud）共用同一个 `_render_status`，行为一致。

**CI 应接哪一条**：

- **前台阻塞**：`gherkai run …` 一条命令即得到表判定的退出码。
- **后台运行**：`gherkai submit …` 取得 `run_id`（退出码 0 只表示提交成功），再由 `gherkai status <run_id> --wait` 取得表判定的退出码。CLI 脱离后不存在内存中的 `RunResult` 终值，判定只能来自读回的终态 `RunState`。
- `explain` 不能作判定门，它只渲染证据；不带 `--wait` 的 `status` 也不能作判定门，未达终态时它的退出码是 0。
- 分界线是**是否已真正开始执行**：开始执行前的全部问题（feature 读不到、写法或参数不合法、worker 定位不到、凭证/region/资源/版本不对）以退出码 `2` 结束；开始执行之后的结论用退出码 `0` 或 `1` 表达。给使用者的口径见 `docs/user-guide/running-and-results.md`「退出码」；`--json` 下**先按退出码分流再解析** stdout。

> 权威：[ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md) 决定五（退出码基于 run 级判定 + 数据源）、[ADR 0034](../adr/0034-detached-batch-reconciler.md)「命令形态」（退出码语义分层：`submit` 表提交、判定归 `status --wait`）、[ADR 0041](../adr/0041-agent-facing-cli-affordances.md) 决策四（`doctor` 只看必修项的 0/2）、[ADR 0042](../adr/0042-step-evidence-and-explain.md) 决策四（`explain` 只 0/2、不重复表判定）；code：`cli/gherkai_cli/__main__.py` 各 `_cmd_*` 的 return 与 `_render_status`。

## 6. 延伸阅读

| 延伸主题 | 出处 |
|---|---|
| 状态机与 severity 的全部决策、被拒方案、预留项（含「主动 skip 的退出码语义待定」） | [ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md) |
| AI 断言为主的取向、投票纪律、N 的缺省与阈值尚未确定的原因 | [ADR 0014](../adr/0014-ai-first-assertions.md) |
| 事件协议、三态、成本可观测性、协作式停止、退出码通道 | [ADR 0024](../adr/0024-worker-core-protocol.md) |
| 并发/失败隔离/fail-fast/心跳/优雅终止 | [ADR 0026](../adr/0026-schedule-module.md) |
| 网络瞬时故障的两层重试与分类白名单 | [ADR 0028](../adr/0028-transient-network-ssl-resilience.md) |
| 脱离式批量运行的推进模型、两条路径共用的终结函数与真值表、投影写、job timeout 归因链 | [ADR 0034](../adr/0034-detached-batch-reconciler.md) |
| step 级证据与 `explain` | [ADR 0042](../adr/0042-step-evidence-and-explain.md) ·[artifacts-and-evidence](./artifacts-and-evidence.md) |
| 远程访问会话的事件契约、scope 级 error 与新增归因类别 | [ADR 0051](../adr/0051-device-session-lifecycle-and-app-distribution.md) |
