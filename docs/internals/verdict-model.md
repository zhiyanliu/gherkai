# 判定的计算路径：从单次投票到退出码

> 本文讲**判定如何被计算**（机制），不讨论为什么这样设计：设计决策与理由在各 ADR，本文只给指针；与代码或 ADR 不一致时以它们为准。一个 run 的「结论」要经过四层归约、两根正交的轴、七个状态，以及各命令语义不同的退出码。单个 ADR 各只覆盖其中一片（0014 投票、0031 状态与 severity、0034 脱离后的退出码等），本文是这些切片合成的全景视图。

姊妹页分工，本文不越界：worker 如何被启动、事件如何送到 core、超时计时由谁负责、四种组合的推进链 → [执行与推进模型导览](./execution-and-reconciliation.md)；`status` / `error_type` / `votes` 在 `--json` 里的**字段名、类型、出现条件** → [CLI `--json` 字段契约](./cli-json-contract.md)（本文不重复它的表）；每步证据的读法 → [artifacts-and-evidence](./artifacts-and-evidence.md)；确定性 step 的写法与派发 → [deterministic-step-lifecycle](./deterministic-step-lifecycle.md)；判定与运行态落在哪张表、哪个桶 → [cloud-backend-carriers](./cloud-backend-carriers.md)。

## 1. 四层归约：票 → step → scenario → job → run

判定由**逐层归约**产生，每层都有一个明确的真值符号。core 不重算票、不重判 step，上层只做归约。

| 层 | 结论的判定规则 | 真值符号 |
|---|---|---|
| **票**（单次投票） | 一次布尔 AI 调用的返回值 | Nova：`act_get(instruction, BOOL_SCHEMA)` → `bool(r.matches_schema and r.parsed_response)`；Midscene：`agent.aiBoolean(instr)` |
| **step** | AI 断言（`Then`）：`yes > N/2` → `passed`/`failed`，事件带 `votes={yes,total}`。确定性注册表命中：`AssertionError`→`failed`、其它异常→`error`。引号内 URL 的导航步 / `When`·`Given` 动作步：正常返回→`passed`、抛异常→`error` | `_run_step`（Nova）/ `runStep`（Midscene） |
| **scenario** | 任一 step `error`→`error`；任一 `failed`→`failed`；否则 `passed`。**被短路跳过的 step 不进入该列表** | worker 侧 `_aggregate` / `aggregate`；结论经 `scenario_done` 事件上报 |
| **job**（= scope） | 同步 `run`：事件流正常 EOF **且**出现过 `scope_done` → 各 scenario 归约；否则按中止来源分流（§3c 图）。无状态批量运行：「两件都要」谓词（内容完整 ∧ 进程干净终止） | `schedule._Worker._run_once` / `project._job_status` |
| **run** | 任一 job `error`→`error`；任一 `failed`→`failed`；否则 `passed`。**入口先滤掉非判定状态** | `project._aggregate`（唯一实现，`schedule._aggregate` 是它的别名） |

几点补充：

- **N 的来源**：`Job.assertion_votes`（CLI `--assertion-votes`，默认值见 `--help`）。阈值是多数票 `yes > N/2`，两个引擎各自实现同一式子。`total == 1` 时，`run` 的人读输出（实时事件行与终态汇总，`render.py` 的 `format_event` / `render_text`）与报告 `index.html` 的 step 行都以 `total > 1` 为显示条件，不显示 tally；`explain` 的逐步视图**有意**不设这道闸，`votes 1/1` 照常显示——`votes` 字段本身就是「这是 AI 断言」的标记，供 agent 分辨（ADR 0042 决策四）。机读层（`--json` / evidence）始终给出完整 `votes`。
- **core 只转录、不判定**：`project.reduce_event` 把 `StepDone` 的 `status`/`votes`/`error_type`/`message`/`report_refs` 原样写入 `StepResult`；scenario 判定**只**由 `ScenarioDone` 事件写入 `scenario_status`，`step_done` 分支不修改它。
- **同步与无状态两条路共用同一份归约**：`reduce_event`（单事件归约）和 `_aggregate`（终态聚合）都定义在 `core/gherkai_core/project.py`，`schedule` 委派给它。同步 run 沿事件流实时输入，reconciler 从持久事件全量重放输入，两条路径收敛到同一终值。

![票 → step → scenario 在 worker 侧逐层汇总，跨进程上报后由 core 归约出 job 与 run 的判定](../diagrams/verdict-model-reduction-layers.svg)

> 图注：图给出层次、方向与 worker / core 的分界；每层规则见上表。三处不走这条链的旁路见 §3a（短路 step）、§3c 图（job 被中止）、§4（run 归约入口过滤）。

> 权威：[ADR 0014](../adr/0014-ai-first-assertions.md)（AI 断言与投票纪律）、[ADR 0024](../adr/0024-worker-core-protocol.md)（事件协议、三态、投票 tally 字段）、[ADR 0026](../adr/0026-schedule-module.md)（三级归约）、[ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md) 决定三（`_aggregate` 入口过滤）；code：`core/gherkai_core/model.py`、`project.py`、`schedule.py`、`engines/novaact/gherkai_worker_novaact/run_scope.py`、`engines/midscene/src/worker/run-scope.mts`。

## 2. 七个状态：含义与处置

`Status`（`core/gherkai_core/model.py`）共七个值：**五个终态** + **两个前置态**。`TERMINAL_STATUSES` 是终态的单一真源，且**取补而非正列**（`frozenset(Status) - _PRE_TERMINAL`），所以新增终态自动进入该集合。

| 状态 | 赋值方与位置 | 出现在哪几级 | 含义 | 处置 |
|---|---|---|---|---|
| `passed` | worker 上报 / core 归约 | step·scenario·job·run | 断言全部通过 | — |
| `failed` | worker 上报（未过多数票 / 确定性 `AssertionError`） | step·scenario·job·run | **测试发现了问题** | 先看现场、不要直接重新运行：`gherkai explain <run_id>` 逐步查看向 AI 提出的断言与 AI 的观察；报告中有引擎原生 report / trajectory |
| `error` | worker 上报（act 抛异常）/ core 派生（各条收场判据见 §3c 图） | step·scenario·job·run | **测试未能执行完成** | 先按 `error_type` + `message` 归因（§3b）：`timeout`/`network_error` 多数可原样重新运行；`engine_error`/`guardrail` 先查 worker 日志 |
| `skipped` | **core 本地赋值**（两处，见 §3a / §3c 图） | job（fail-fast 下 worker 从未 spawn）· step（scope 内短路） | 该单元未执行 | job 级：未执行、未产生费用，可直接重新运行（但整批必然伴随另一个 job 的 `error`，根因在别处）。step 级：根因是其上游的 `error` step |
| `aborted` | **core 本地赋值**（`schedule` 的 fail-fast 分支） | job | 已启动，运行中被终止 | **不宜直接重新运行**：会话已被操作过、可能留下副作用；先查现场（`session_id` 已保留，可对上 worker 日志与轨迹） |
| `pending` | `create_run` 写初始态 | job（`JobState`）·run（`RunState`） | 尚未启动 | 等待；提交较久而**所有** job 仍为 pending 时，`status` 会提示用 `--wait` 接力推进 |
| `running` | 收到 `scope_started` 后写入 / 无状态路径 CAS claim | job·run | 执行中 | 等待 / `status --wait` |

两条边界容易读错：

- **worker 只上报三态**。`wire.py` 的 `event_from_json` 只对 `step_done`/`scenario_done` 调 `Status(d["status"])`，wire 上能出现的只有 `passed`/`failed`/`error`；`scope_done` 没有 `status` 字段，仅作「内容完整」信号（job 判定由 core 归约，见 §1）。其余四态全是 **core 内态**：`skipped`/`aborted` 由 `schedule` 在 job 未启动或被终止时本地构造，`pending`/`running` 由实时写入落库。
- **前置态绝不进入判定真值**。`JobResult.status` 只会是五个终态之一；强制点在 `project.project_full`：收尾聚合时任一 job 仍非终态即抛 `NonTerminalSnapshot`，该轮 tick 不落任何判定，`running` 因此不会混进 `jobs/*.json`。同步 run 路径的归约器只产出终态。前置态同样不在 severity 表内（§4）。

> 权威：[ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md) 决定一 / 决定一·补（两组派生态的定义、行动含义、`TERMINAL_STATUSES` 取补）、[ADR 0024](../adr/0024-worker-core-protocol.md)（wire 三态）、[ADR 0030](../adr/0030-realtime-persistence-seam.md)（pending/running 何时被写）。

## 3. 两根正交的轴与 `error_type` 类别集

### 3a. `status` × `shortcircuited`

`StepResult` 有两个独立维度：`status` 表示执行得出的结论，`shortcircuited: bool` 表示 `skipped` 的原因。

一个 scenario 内某 step 报 `error` 后，worker **不再对后续 step 调 AI**（既省去费用，也避免在已损坏的环境上产生误导性的 `failed`），改为给每个被跳过的 step 发一条独立事件 `step_skipped`（与 `step_done` 平行，无 `status`/`votes`/`cost` 字段——「该步未执行」是执行事实、不是判定结论，因此不纳入三态）。core 收到该事件后就地构造 `StepResult(status=SKIPPED, shortcircuited=True, duration_ms=None)`。

**该事件绝不污染上层。** `reduce_event` 的 `StepSkipped` 分支只把 `StepResult` 暂存、待挂载到所属 scenario，**不写 `scenario_status`**，因此完全不参与 scenario 归约（`_aggregate` 的 `_NON_VERDICT` 过滤是第二层保险）。scenario 与 job 的判定由上游那个 `error` step 决定，与其后短路了几步无关。渲染层的连锁失败旁注读 `shortcircuited` 这个布尔（`render.py`：`⚠ 因前置 step error 被跳过（未执行）`），不依赖按 `status` 顺序推测。

短路判据是 `status == error`（不看 `error_type`），两引擎对称；短路只作用于**本 scenario**，跨 job 的中止由 fail-fast 负责，两者正交。

**两级 `skipped` 判据不同，不可混同**：

| | 被 skip 的对象 | 是否有 `StepResult` | 是否已计费 |
|---|---|---|---|
| **job 级**（fail-fast） | 整个 job 从未 spawn | 无（`JobResult.scenarios=[]`） | 否，`session_id` 必为 `None` |
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

`skipped`/`aborted` 的 `error_type` 恒为 `None`——这两种状态下未产出判定的原因只写在 `message` 里，因此人读渲染在无分类时仍显示 `message`，否则输出只剩一个状态值。

### 3c. job 收场态与 `error_type`：归因的优先级

同步 `run` 中一个 job 的收场态由一串**有序短路**的判据决定：先看它是否启动，再看是否被主动中止，最后才看事件流如何结束。

![四问构成一串有序短路：fail-fast 中止 → worker 能否启动 → 是否被主动中止 → 事件流如何结束；任一条件命中即记录收场态，全部未命中才做 scenario 归约](../diagrams/verdict-model-job-outcome.svg)

> 图注：本图只画同步 `run`；「事件流如何收场」在图上拆成两问——先识别网络专用退出码，其余非零退出与内容不完整归入 `engine_error`。图上另有**一处例外**：worker 以非零码异常退出时不再复查中止与超时（即便中止已发起、墙钟已过），一律记 `error · engine_error`。无状态批量运行走另一条链，退出记录落库后，在收敛时确定终态：`skipped` / `aborted` 不出现（该路径没有 fail-fast），超时一路的归因与本图一致，其余非零退出与启动 task 失败只落 `error`、job 级不细分 `error_type`（诊断信息在 `message` 与 worker 日志）。与姊妹页[执行与推进模型导览](./execution-and-reconciliation.md) §6 那张图的分工：那张讲**如何把 worker 停下来**，本图讲**停下来之后记什么状态**。

几处判据的由来与边界：

- **两条中止路径分开归因的原因**：超时与 fail-fast **两条路径都会主动停 worker**（被停的 worker 随后可能以网络码退出），因此图上那道分叉的判据取 `abort_flag`（只有 fail-fast 落 `aborted`）、不看「是否被自己停过」这类笼统标志；无状态路径口径相同——`TaskExited.timed_out` → `ERROR`，归因由 `_reduce_scope` 覆盖为 `timeout`，因为该次 stop 本就由超时处置发起。这样切分的理由见 [ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md) 决定一的注（「aborted 只认 fail-fast」）。
- **`skipped` 不覆盖建连失败的原因**：建连失败的 job 已经建立过会话、已经计费，`saw_step == False` 只表示「可安全重试（无 act 副作用）」、不表示「未产生费用」，因此它照常进入 run 级聚合，`skipped` 的边界严格停在「worker 从未 spawn」。现状补充：`ScheduleOpts.network_retry` 默认 0 且 CLI 未暴露该参数，所以当前 `run` **不做** job 级整批重新运行；生效的只有 worker 自身的建连退避（`_CONNECT_ATTEMPTS` / `_BACKOFF_S`，只包裹幂等的建连段），重试耗尽即以网络专用退出码退出。
- 另一条边界：worker 收到停止信号时**不为未执行完的单元生成判定**——Nova 在投票循环与 step 循环开头检查停止标志，票数未投满就不 emit 带判定的 `step_done`、也不发 `step_skipped`；Midscene 执行 SIGTERM 收尾序列（释放会话 → 安全点提前上传 → 排空队列）。两侧都把未完成的单元交由 core 按派生态处理，区别只在停止的处置形态。

> 权威：[ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md) 决定六（`step_skipped` 事件 + `shortcircuited` 正交布尔 + 「绝不写 `scenario_status`」不变量）、决定一（skipped/aborted 边界）、[ADR 0028](../adr/0028-transient-network-ssl-resilience.md)（两层重试、`network_error` 白名单、「绝不重试 act」、core 层 job 重试门槛）、[ADR 0024](../adr/0024-worker-core-protocol.md)（协作式停止、退出码 out-of-band 通道）；code：`model.py` 的 `ErrorType`/`StepSkipped`/`StepResult.shortcircuited`、`project.reduce_event`、`schedule._Worker._run_once`、两个 worker 的 `_classify_act_error` / `isTransientNetwork`。

## 4. severity：数值序而非字母序；run 级为何不含 skipped/aborted

`_STATUS_SEVERITY`（`model.py`）给**终态**定义了一套数值序：

```
skipped = -1  <  passed = 0  <  failed = 1  <  error = 2  <  aborted = 3
（skipped 最轻：未执行，可忽略；aborted 最重：有现场，需人工查看）
```

两点约束：

1. **不得直接比较 `Status` 字符串的大小**。字母序 `'error' < 'failed' < 'passed'` 与严重度**完全相反**；比较须查表或调用 `severity()`。前置态查表会抛 `KeyError`（它们不是判定结论，无 severity）。
2. **这张表当前的角色是约定，不是计算引擎**。`_aggregate` 用显式 `any(...)` 实现三态归约（在三个判定状态上与「取 severity 最大值」等价）；报告配色是按同一序**手工映射**的另一张表（`core/gherkai_core/adapters/report_store/local.py` 的 `_STATUS_COLOR`：passed 绿 / failed 红 / error 琥珀 / skipped 弱化灰 / aborted 紫 / pending·running 蓝——每态各一色，均不落默认灰，否则 aborted 的严重度无法辨识）；`severity()` 本身当前只被单测引用（`core/tests/test_lifecycle_states.py` 有一行断言了完整的严重度序）。**新增终态时 `_STATUS_SEVERITY` 与 `_STATUS_COLOR` 两处须同时修改。**

两个相邻但**判据不同**的集合不可混用（二者在 skipped/aborted 上有意重叠）：

| 集合 | 切分维度 | 含 skipped/aborted？ | 引用方 |
|---|---|---|---|
| `TERMINAL_STATUSES` | 生命周期（状态是否还会变） | 含 | `--wait` 轮询、`status` 退出码判定与仅在终态打印的产物位置、`explain` 的「run 仍在运行」提示、`project_full` 的不变量检查、云端推进器 Lambda 的「已收尾的 run 不再推演」跳过判据（`deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py`：读到终态即 no-op，见 [`execution-and-reconciliation.md`](./execution-and-reconciliation.md)「已终态 run 在两个后端的重入」）、隧道守护的拆除判据（`runtime/gherkai_runtime/tunnel_host.py`：读到终态即提前拆除，否则等满 TTL）；另有一处**取补**用法——revision 清理的运行中 run 引用检查，判断是否仍有未达终态的 run 引用（`deploy_aws/gherkai_deploy_aws/workers.py`）。跨栈护栏要求消费方全部引用这一份、不各自维护白名单 |
| `_NON_VERDICT` | run 级判定（是否算作结论） | 含（**另含** pending/running） | `_aggregate` 入口过滤 |

**run 级永不出现 skipped/aborted**：`_aggregate` 在入口就把它们连同两个前置态滤掉，因此 `RunResult.status` ∈ {`passed`,`failed`,`error`}。这条过滤在无状态投影路径上是**承重**的：`project` 每轮 tick 全量重放，`jobs_state` 确实含 pending/running 的 job 并原样传入；同步 run 路径传入的全是终态，过滤为 no-op。

控制面的 `RunState.status` 多两个可能取值：执行期间为 `pending`/`running`（同步 `run` 路径全程保持 `pending`，由 `finalize` 一次落终态；无状态路径每轮投影写按 `projected_run_status` 钳在 pending/running）。run 级终态是 `finalize` 这个提交点的专属，提前落终态会使 run 永不 finalize。

> 权威：[ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md) 决定二（severity 序、视觉映射、「run 级为何不含 skipped/aborted」的洞察）与决定三（入口过滤）、[ADR 0034](../adr/0034-detached-batch-reconciler.md) 机制三（投影写钳制）、[ADR 0030](../adr/0030-realtime-persistence-seam.md)（提交点）。

## 5. 退出码：各命令的语义不同

| 命令 | 退出码的语义 | `0` | `1` | `2` |
|---|---|---|---|---|
| `run` | **判定** | run 级 `passed` | 其余终态（`failed`/`error`，含伴随 error 的 skipped/aborted 批次）；另有一种情形：cloud 后端运行中落库不可达 | 开始执行前的配置或可达性问题 |
| `status`（不带 `--wait`） | 查询是否成功（读到终态时才同时表达判定） | 已查到，**含未达终态**（查询本身成功） | 读到的终态非 `passed` | run 不存在 / 云端不可达 / 版本不匹配 |
| `status --wait` | **判定** | 轮询到终态且为 `passed` | 轮询到终态但非 `passed` | 同上，另加「接力 Lambda 不存在（`--prefix` 配错或后端未部署）」 |
| `submit` | 提交是否成功（≠ 判定） | 已提交、`run_id` 已打印 | — | 配置或可达性问题 |
| `plan` | 该批次能否运行（零 AWS、零副作用） | 可运行 | — | 配置错、写法错、使用方 steps 加载失败 |
| `explain` | 证据是否读出（**从不表达判定**） | 已渲染——**run 判定为 failed 同样退 0**；判定明细尚未落地也退 0 | — | 参数写错（如 `--step` 没同时给 `--scenario`）、run/scope 查不到、云端读不到 |
| `doctor` | 必修项是否全部通过 | 全部通过 | — | 任一 `required` 项 fail（可选能力缺失只标 `-`，不影响退码） |
| `list-deterministic` | 该引擎有哪些确定性 step（纯本地、零 AWS） | 已列出 | — | `--steps-dir`（或 env）不是目录 / worker 定位不到 / 使用方 steps 加载失败 / 该引擎自述失败 |
| `list-engines` | 本机的引擎环境状况 | **恒 0**（某引擎未安装正是要展示的信息，不算命令失败；判断某引擎是否已安装需看对应那一行，或用 `run`/`list-deterministic` 的退 2） | — | — |
| `skill install` | agent skill 是否安装成功 | 已安装（`--print` 则已打印正文） | — | `--dir` 不是目录 / 目标目录里已有非本命令安装的内容（无安装标记且非空，或同名路径是文件） / 包内 agent skill 缺失 / 写入失败（含指令文件那一行） |

归纳：**表达判定的只有 `run` 与 `status`，也只有它们会退 1**；`submit`/`plan`/`explain`/`doctor`/`list-deterministic`/`skill install` 都是 0/2 的「成功 / 失败」；`list-engines` 恒 0（理由见表）。

部署方命令 `deploy`/`destroy` 不在本表口径内，但 `2` 与本表同源。`0` 为成功；`2` 是它们自身的前置或校验失败：缺 Node 或找不到 cdk、`--vpc` 缺值或取值不符、容器引擎名不被识别、`push-worker` 的架构与 skew 拦截，都在变更账户资源之前拦下；唯一例外是 `push-worker` 推送途中的 AWS 调用失败，也归 `2`，但那时镜像与 revision 可能已写入账户。`1` 有两种来源：cdk 自身失败（cdk CLI 报错多为 1，原样透传），或 cdk 已成功而其后的 worker 镜像步骤失败；两者都意味账户可能已被改动，重新运行 `gherkai deploy` 幂等收敛。其余退出码同样是 cdk CLI 返回值的原样透传，均不按判定码解读。给使用者的口径见 `docs/user-guide/cloud-backend.md`「退出码与常见错误」。

`run` 的判定码取 `schedule` 返回的内存 `RunResult.status`（必为终态，不回读可能停在 pending 的落库态）；`status` 的判定码取读回的落库 `RunState`。两路 `status`（local/cloud）共用同一个 `_render_status`，行为一致。

**CI 应接哪一条**：

- **前台阻塞**：`gherkai run …` 一条命令即得到判定码。
- **后台运行**：`gherkai submit …` 取得 `run_id`（退 0 只表示提交成功），再由 `gherkai status <run_id> --wait` 取得判定码。CLI 脱离后不存在内存中的 `RunResult` 终值，判定只能来自读回的终态 `RunState`。
- `explain` 不能作判定门，它只渲染证据；不带 `--wait` 的 `status` 也不能作判定门，未达终态时它退 0。
- 分界线是**是否已真正开始执行**：开始执行前的全部问题（feature 读不到、写法或参数不合法、worker 定位不到、凭证/region/资源/版本不对）退 `2`；开始执行之后的结论退 `0`/`1`。给使用者的口径见 `docs/user-guide/running-and-results.md`「退出码」；`--json` 下**先按退出码分流再解析** stdout。

> 权威：[ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md) 决定五（退出码基于 run 级判定 + 数据源）、[ADR 0034](../adr/0034-detached-batch-reconciler.md)「命令形态」（退出码语义分层：submit=提交、判定归 `status --wait`）、[ADR 0041](../adr/0041-agent-facing-cli-affordances.md) 决策四（`doctor` 只看必修项的 0/2）、[ADR 0042](../adr/0042-step-evidence-and-explain.md) 决策四（`explain` 只 0/2、不重复表判定）；code：`cli/gherkai_cli/__main__.py` 各 `_cmd_*` 的 return 与 `_render_status`。

## 6. 延伸阅读

| 延伸主题 | 出处 |
|---|---|
| 状态机与 severity 的全部决策、被拒方案、预留项（含「主动 skip 的退出码语义待定」） | [ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md) |
| AI 断言为主的取向、投票纪律、N 的缺省与阈值尚未确定的原因 | [ADR 0014](../adr/0014-ai-first-assertions.md) |
| 事件协议、三态、成本可观测性、协作式停止、退出码通道 | [ADR 0024](../adr/0024-worker-core-protocol.md) |
| 并发/失败隔离/fail-fast/心跳/优雅终止 | [ADR 0026](../adr/0026-schedule-module.md) |
| 网络瞬时故障的两层重试与分类白名单 | [ADR 0028](../adr/0028-transient-network-ssl-resilience.md) |
| 脱离式批量运行的「两件都要」谓词、投影写、job timeout 归因链 | [ADR 0034](../adr/0034-detached-batch-reconciler.md) |
| step 级证据与 `explain` | [ADR 0042](../adr/0042-step-evidence-and-explain.md) ·[artifacts-and-evidence](./artifacts-and-evidence.md) |
