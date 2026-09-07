# job 生命周期态：skipped / aborted + severity 数值序

> **Status:** Partially-superseded-by 0034 —— 生命周期态/severity/短路语义等**结论均不变**；变的是两处实现细节立场：① 决定五「退出码读内存 `RunResult` 终值」对**异步 submit（CLI 脱离）路径**不适用（脱离后无内存终值，判定退出码由 `status --wait` 读回终态 `RunState` 给出），见下决定五数据源的 ⚠️ 注；② 决定三的「`_aggregate` 只算一次 / 前置态过滤只是前向口子」被反转——无状态投影每轮 tick 全量重放调 `_aggregate`，前置态过滤在该路径**已承重**（决定三的**决策**本身反被印证、非被推翻）。两处均见 [0034](./0034-detached-batch-reconciler.md)。

给 `Status` 加两个 **core 派生态**——`skipped`（排队没起）与 `aborted`（跑一半被掐）——并定义一套
**severity 数值序**，解决「`'error' < 'failed'` 字母序与严重度反向」的坑、并把 fail-fast 中止的 job 从
被误记成 `error` 区分出来。

**定位**：本 ADR 是判定**数据模型**的扩展，是 [0024](./0024-worker-core-protocol.md)「status 三态」的延伸。
它怎么被实时落库（`update_job_state` / severity 单调聚合）见 [0030](./0030-realtime-persistence-seam.md)。

## 背景：三态不够用，fail-fast 把两类「没跑成」都污染成 error

当前 `Status` 三态：`passed`（断言过）/ `failed`（断言没过=测试发现问题）/ `error`（引擎抛异常=没能跑完）。
fail-fast（[0026](./0026-schedule-module.md)：任一 job error → 中止整批）下，`schedule` 给两类 job 都记了 `error`：

- **排队还没起**的 job（`abort_flag` 已 set、worker 未启动）→ 记 error/engine_error/"批次已中止，未启动"。
- **跑到一半被 stop**的 job（事件循环中被掐断）→ 记 error/engine_error/"其他 job 失败，本 job 被中止"。

问题：这俩都**不是该 job 自己出错**，记成 `error` 会让跨 run 统计 / CI 归因把「被牵连」误算成「自身崩」。
而且两者对使用者的**行动含义不同**：前者没执行、没花钱、可无脑重跑；后者动过、有副作用、有现场可查。
代码里这俩分支本就分开（连 message 都已区分），只差一个名正言顺的状态。

## 决定一：加 `skipped` / `aborted` 进 `Status` enum，作 core 派生态

```python
class Status(str, Enum):
    PASSED = "passed"; FAILED = "failed"; ERROR = "error"
    SKIPPED = "skipped"    # core 派生：fail-fast 下 worker 从未 spawn。没执行/没花钱/可无脑重跑。session_id 必 None
    ABORTED = "aborted"    # core 派生：fail-fast 下跑一半被掐。有副作用/有现场可查。session_id 保留不清
```

| 态 | 含义 | 对使用者 | 产生处（schedule） |
|---|---|---|---|
| `skipped` | **worker 从未 spawn**（`abort_flag` 已 set 时排队中的 job） | 没花钱，可无脑重跑 | 起 worker 前的 `abort_flag` 已 set 分支 |
| `aborted` | 已 spawn、跑一半被 **fail-fast** 掐断 | 动过、有副作用、先看现场再重跑 | 事件循环中因 `abort_flag` 被 stop + 其「被主动停后以网络码退出」的竞态回填 |

> **aborted 只认 fail-fast，不认 timeout**（实装关键，别踩）：代码里 `self_stopped` 这个布尔被 **timeout 与 fail-fast 两条路径共用**
> 地 set。本 ADR 的 aborted **仅对应 fail-fast 中止**（`abort_flag` 触发）；**超时杀的 job 维持 `error` + `errorType=timeout`**
> （[0026](./0026-schedule-module.md)/[0028](./0028-transient-network-ssl-resilience.md)），**不归 aborted**。回填条件要按来源拆开——
> 看 `abort_flag` 而非笼统的 `self_stopped`，否则会把超时和 fail-fast 两类语义不同的中止混成一类、丢掉 timeout 分类。
>
> **network 重试耗尽的 job 也不是 skipped**：[0028](./0028-transient-network-ssl-resilience.md) 的 core 层 network 重试门槛是
> 「network_error 且 `saw_step=False`」，耗尽后该 job 记 `error`。它同样 `saw_step=False`，但**已经开过会话/建连尝试（烧过钱）**——
> `saw_step=False` 只表「可安全重试」、不表「没花钱/没起」。故它仍是 `error`、**正常进 run 级聚合**，不归 skipped/aborted。
> skipped 的边界严格是「worker 从未 spawn」。

- **加进同一个 `Status` enum**（而非新开 enum）：`Status` 是 scenario/step/job/run **一切判定态的统一承载**，
  `serialize` 全靠 `Status(d["status"])` round-trip、`index.html`/`render` 全靠 `status.value` 渲染——单点扩 enum
  即全链路自然识别。新开 enum 会让 `JobResult.status` 变 `Union`，serialize/render/html 全要分两套分支，破坏「status 单一类型」的深模块性质。
- **它们是 core 在 fail-fast 路径派生赋的 job 级态，不是 worker 上报态**：worker 只在 `*_done` 事件报三态
  （`passed`/`failed`/`error`，[0024](./0024-worker-core-protocol.md)）；skipped/aborted 由 `schedule` 在 worker 没起 / 已被掐时
  本地构造 `JobResult` 时赋。故 aborted **只活在 job 级（scope 级）**；**skipped 后来下探到 step 级**（scope 内短路，见决定六），
  但两级的 SKIPPED **都由 core 本地构造、永不经 `StepDone.status` 上报**（`step_skipped` 是独立事件、非 step_done 的 status 值）。

## 决定一·补：`pending` / `running` —— 生命周期前置态，非判定态

实时写（[0030](./0030-realtime-persistence-seam.md)）需要两个**前置态**表示「还没出判定」：`pending`（run 开始时 `create_run` 把每个 job 摆这态）
/ `running`（worker 起了、收到 `scope_started` 后刷这态）。它们和 skipped/aborted 一样**只活在 job 级（`JobState.status` / 进而 `RunState`）**、
绝不进 `JobResult.status`（JobResult 是终态判定，只会是 passed/failed/error/skipped/aborted）、绝不进 wire。

**承载方式**：加进同一个 `Status` enum（`PENDING="pending"` / `RUNNING="running"`），理由同 skipped/aborted（统一类型、serialize/render 单点识别）。
但与判定态有**本质区别**——它们是**生命周期前置态、不是判定结论**：

- **不进 severity 表、不参与任何 severity 比较**（severity 只给终态排序/聚合用，见决定二）。
- **不进 run 级聚合**：`_aggregate` 的过滤名单除 skipped/aborted 外**也要含 pending/running**（决定三）——否则一个还在 `running` 的 job 会污染 run 级 status。
- **状态机推进 ≠ severity 升级**：job 生命周期是 `pending → running → 终态(passed/failed/error/…)` 的**单向推进**（终态一旦落定不回退）；
  这条「单调」是**生命周期推进**意义上的，与决定二 run 级的「severity max 单调只升」是**两套不同的序**，不可混用。
- `_STATUS_COLOR` / index.html 给 pending/running 各配一个「进行中」视觉（灰/蓝），别走兜底色。
- **「终态」有正向真源、定义取补：`core.model.TERMINAL_STATUSES = frozenset(Status) - {PENDING, RUNNING}`**。
  凡「等到终态 / 是否已终态」的消费方（`status --wait` 轮询、隧道守护的拆除判据、`status` 退出码判定）一律引它，
  **不各自正列白名单**——正向白名单散写多份时，新增终态漏改哪份、那份就永远判不到终态（`--wait` 无限轮询、
  隧道守护只能等满 TTL 才拆，均曾真实存在两份逐字副本）。取补而非正列即为此：新增终态自动入集，只有新增**前置态**
  才需动（届时 `_NON_VERDICT` 同批要改）。**与 `_NON_VERDICT` 是两把不同的刀**：本集按生命周期切（含 skipped/aborted），
  `_NON_VERDICT` 按 run 级判定切（skipped/aborted 是终态但不算判定结论），两集在这两态上有意重叠；
  `TERMINAL_STATUSES` 恒等于 `_STATUS_SEVERITY` 的键集（决定二：severity 只给终态定义）。

## 决定二：severity 数值序，两层分清

severity **只用于终态**（passed/failed/error/skipped/aborted）的排序/着色/聚合；前置态 pending/running 不在此表（见决定一·补）。
`Status` 是字符串，按字母序比大小是**错的**（`'error' < 'failed' < 'passed'` 字母序与严重度**正好反**）。
故定义一张 severity 数值表，比较/单调升级一律用它、绝不拿字符串比：

```
job 级（排序 / 着色 / 单调升级用）：
   skipped = -1  <  passed = 0  <  failed = 1  <  error = 2  <  aborted = 3
   （skipped 最轻——没执行最该被无视；aborted 最重——有现场最该被人看）

run 级（聚合用）：
   只比 {passed=0, failed=1, error=2} 三态取 max
```

**视觉映射（severity 序在报告着色上的落法）**：每个终态各配一个可区分的颜色、**别走兜底灰**——`aborted` 要**比 error 更扎眼**（severity 最高、有现场最该被人看），且**别和兜底灰混**；`skipped` 用**弱化灰**（最轻、最该被无视），但须与兜底灰可分。否则新态全走兜底灰、aborted 看不出严重。（前置态 pending/running 另配「进行中」视觉，见决定一·补；落点符号见下「touch points」的 `_STATUS_COLOR`。）

**为何 run 级不含 skipped/aborted**（验证过的关键洞察）：skipped/aborted **只在 fail-fast 路径产生**，
而 fail-fast 的唯一触发条件是「某 job 已经 `error`」——那个 error job 在 run 级聚合里已把 run 顶成 `error`。
所以无论 skipped/aborted 怎么算，run 必为 error，它俩**根本不需要进 run 级比较**。它们是 job 级、单写者
（fail-fast 主线程 / worker 自己一次写定终态）、**不参与 run 级单调升级**。

## 决定三：`_aggregate` 入口过滤 skipped/aborted（把正确性钉进函数，不靠外部不变量）

run 级聚合（`schedule._aggregate`——真源现居 `core.project._aggregate`、schedule 侧为别名，同步/无状态两路共用一份）改成：**入口先滤掉 skipped/aborted，再走原三态 max 逻辑**。

```python
# 入口过滤名单：终态判定之外的态（skipped/aborted 派生态 + pending/running 前置态）都不进 run 级聚合
_NON_VERDICT = (Status.SKIPPED, Status.ABORTED, Status.PENDING, Status.RUNNING)

def _aggregate(statuses):
    statuses = [s for s in statuses if s not in _NON_VERDICT]  # run 级只看真正出了判定的 job
    if any(s == Status.ERROR for s in statuses): return Status.ERROR
    if any(s == Status.FAILED for s in statuses): return Status.FAILED
    return Status.PASSED
```

- 过滤名单**含 pending/running**（决定一·补）：在 [0034](./0034-detached-batch-reconciler.md) 的无状态投影路径上**已承重**（曾是「为未来增量聚合预留」的前向口子，
  该未来已到）——`project` 每轮 tick 全量重放推演 `RunState`，`jobs_state` 真实含未起（`pending`）/ 在跑（`running`）
  的 job 并原样喂进 `_aggregate`；缺这条过滤，前置态会直接污染 run 级 status。
- 不改也「碰巧正确」（有 skipped/aborted 必有 error 同批短路），但 `else: return PASSED` 是脆弱兜底——
  一旦未来引入**非-fail-fast 的 skip**（如主动 `--skip`），「全 skipped 无 error」的 run 会被误判 `passed`。
  入口过滤把正确性钉死在 `_aggregate` 内、不依赖「skipped 必伴随 error」这个外部假设。
- **scenario 内归约路径不改**（喂进去的全是 worker 三态，永不含 skipped/aborted）。
- **两路调用者、两种喂入**（[0034](./0034-detached-batch-reconciler.md) 落地后的现状）：`_aggregate` 被 ① 同步 `schedule` 归约 `RunResult` 时调一次
  （喂进的全是终态、前置态过滤是 no-op）② 无状态投影 `project`/`project_full` 调（`project` 每轮 tick 调、真实喂入前置态）
  两路复用**同一份**——同一过滤名单/severity 表使两路收敛到同一终值（这正是当年留口子的意图）。落库的 `RunState.status`
  也不再「由 `finalize` 一次写定」：无状态路径下每轮投影写都落 run 级 status（钳在 `pending`/`running`——run 级终态是
  `finalize` 这个 commit point 的专属，[0030](./0030-realtime-persistence-seam.md) / [0034](./0034-detached-batch-reconciler.md) 机制三），终态仍由 `finalize` 一次落定。

## 决定四：[0024](./0024-worker-core-protocol.md) 线协议不改，只补一句澄清

worker↔core 的 JSON 线协议**保持三态**（worker 永远只报 passed/failed/error；skipped/aborted 时 worker 根本没起或已被掐、
不可能也不需要上报）。skipped/aborted 与线协议**正交**。[0024](./0024-worker-core-protocol.md) 的「`status` 三态」条已带这句澄清：
skipped/aborted（连同前置态 pending/running）是 core 内态、非 worker 上报态、不进 wire。

## 决定五：退出码改基于 run 级 severity

cli 退出码从「`status.value == 'passed'` 才 0」改为**基于 run 级 severity**（`run.status == PASSED → 0，否则 1`）。

- **数据源**：退出码读 **schedule 返回的 `RunResult.status`（内存终值，必是终态）**，不回读 RunStore 落库态（后者实时写下可能停在 pending/running，且 `--no-report` 时根本没落库）。**⚠️ 此「读内存终值」限同步 `run` 路径**：[0034](./0034-detached-batch-reconciler.md) 无状态跑批下 CLI 脱离、不再有「schedule 返回的内存 RunResult」——`submit` 退出码=**提交成功与否**（0=已提交、run_id 已返回），判定退出码由 `status --wait` **读回 `RunState`** 给出。这不违背本条「不回读实时落库态」的初衷：`status --wait` 读的是**轮询到终态后**的 `RunState`（reconciler 已 finalize、必是终态），非本条所拒的「实时写下可能停在 pending/running 的落库态」。退出码语义分层详见 [0034](./0034-detached-batch-reconciler.md)「命令形态」。
- 当前结果不变：含 aborted/skipped 的 run 必伴随 error → run=error → 退 1（CI 红）。aborted 有副作用、skipped 因别人崩才没跑，整批确实失败，退非 0 正确。
- 改成基于 severity 而非字符串相等，**对未来新态更稳健、可读性更好**（判断点收敛到一处）。

## 决定六：step 级短路——SKIPPED 下探到 step 级 + 正交 `shortcircuited` 布尔

[0028](./0028-transient-network-ssl-resilience.md) 记过一个真跑暴露的空白：scope 内 step 串行，**上游 step `error` 不短路下游** →
下游在损坏环境（如 SSL 错误页）上跑出误导性 `failed`。本决定兑现 0028 记的「首选路线」：**worker 在 scope 内短路**——
上游 step `status==error` 后，不再对后续 step 调 AI（省钱、报告干净），而是为每个被跳过的 step 发一个 `step_skipped` 事件。

**这引出一个新问题：被短路的 step 用什么态？** 定下如下承载方式（三条硬约束，别踩）：

- **载体是独立 `step_skipped` 事件，不是 `step_done` 的第 4 个 status 值**。理由：wire 严格三态（决定四），
  worker 报判定只能是 passed/failed/error。「这步没跑」不是判定结论、是执行事实，故走**平行于 step_done 的独立事件**
  （`{type:"step_skipped", scenarioId, stepIndex}`，无 status/votes/cost 字段），[0024](./0024-worker-core-protocol.md) wire 相应加此事件。
- **core 收到 `step_skipped` → 本地构造 `StepResult(status=Status.SKIPPED, shortcircuited=True)`**。复用既有 `Status.SKIPPED`
  枚举值（它已在 severity 表 = -1、已被 `_NON_VERDICT` 覆盖）——**在 StepResult 层，SKIPPED 直观表达「这步没跑」**，
  人/AI 一眼可读。**但它由 core 本地赋、不经 wire**（同 job 级 skipped/aborted 的性质：core 派生态、非 worker 上报态）。
- **`shortcircuited: bool` 是与判定轴正交的第二维**：status 轴回答「跑出什么结论」（passed/failed/error/skipped），
  shortcircuited 轴回答「为什么 skipped」（True=因上游短路而被跳过）。渲染层的连锁失败旁注**改读 shortcircuited**
  （见 [0028](./0028-transient-network-ssl-resilience.md) 从「error 后 failed」迁到「被短路的 step」），比原「按 status 顺序猜」更精确、判据单一。

**关键不变量：step 级 SKIPPED 绝不写进 `scenario_status`**（守 severity/`_aggregate` 零污染）。`_reduce` 处理 `step_skipped`
时只把 StepResult 暂存待挂（同 step_done 的暂存路径），**不碰 scenario_status**——故它不参与 scenario 归约、不进 `_aggregate`
（决定三的 `_NON_VERDICT` 已含 SKIPPED，是双重保险；但真正的保证是「压根不喂进去」）。scenario/job 的判定态由「上游那个 error step」
决定，与「后面短路了几个 step」无关。

**job 级 skipped（决定一）与 step 级 shortcircuited 是两个不同层次，别混**：

| | 谁 skip | 有 StepResult 吗 | 承载 |
|---|---|---|---|
| **job 级 fail-fast skip**（决定一） | 整个 job 从未 spawn | **无**（`JobResult.scenarios=[]`） | `JobResult.status = SKIPPED`（session_id 必 None、没花钱） |
| **step 级短路**（本决定） | job 起了、scope 内上游 error 后跳过后续 step | **有**（worker 发 step_skipped、core 建 StepResult） | `StepResult(status=SKIPPED, shortcircuited=True)`（会话已起、花过钱） |

两级都复用 `Status.SKIPPED` 表「没跑」，语义一致、只是层级不同；`shortcircuited` 布尔进一步标出 step 级「为什么没跑」。

**判据锁 `status==error`（不看 error_type）**：无论哪个引擎、network_error 还是 engine_error 都触发短路，两个引擎对称——
这也回避了 [0028](./0028-transient-network-ssl-resilience.md) 记的「两个引擎 SSL 分类不对称」欠账对短路的影响（那只影响 errorType 文案、不影响 error 这个 status）。
短路是 **scope 内**行为（上游 error 只短路**同 scenario/同 scope**的后续 step，不跨 job——跨 job 是 fail-fast 的职责，两者正交）。

## touch points（落点指针）

- `core/gherkai_core/model.py`：`Status` 的 SKIPPED/ABORTED（判定派生态）+ PENDING/RUNNING（前置态；注释标明 core 内态、非 wire）；`_STATUS_SEVERITY`（仅终态）+ `severity()` 比较辅助；`_NON_VERDICT` 过滤名单；`TERMINAL_STATUSES`（终态真源，取补于 `_PRE_TERMINAL`，决定一·补末条）；`StepSkipped` 事件（frozen dataclass `scenario_id`/`step_index`，无 status/votes/cost）入 `Event` Union + `StepResult.shortcircuited`（正交布尔，决定六）。
- `core/gherkai_core/schedule.py`：job 级 SKIPPED/ABORTED 的赋态点——起 worker 前 `abort_flag` 已 set → SKIPPED（worker 从未 spawn）；事件循环中因 `abort_flag` 被 stop + 其 WorkerNetworkError 竞态回填 → ABORTED；**超时（deadline）分支维持 `error`+`errorType=timeout`、不归 aborted**（回填判断看 `abort_flag` 而非笼统 `self_stopped`——后者被 timeout 与 fail-fast 共用）。
- `core/gherkai_core/project.py`：`_aggregate`（入口过滤 `_NON_VERDICT`；两路共用的真源，`schedule._aggregate` 为其别名，决定三）；`reduce_event` 的 `StepSkipped` 分支 → 暂存 `StepResult(status=SKIPPED, shortcircuited=True)`，**绝不写 `scenario_status`**（被短路 step 无 `step_started`，`duration_ms` 恒 None——没跑=无墙钟）。
- `core/gherkai_core/wire.py`：`event_from_json` 的 `step_skipped` 分支（加法，不碰 step_done 三态解析）。
- `core/gherkai_core/serialize.py`：JobResult/RunResult 链路靠 `Status(str,Enum)` 天然 round-trip 新值（单测覆盖 skipped/aborted）；StepResult to/from_dict 的 `shortcircuited`（`.get` 默认 False，向后兼容旧落盘）。（**注**：`RunState` 链路的 `run_state_to/from_dict` 归 [0030](./0030-realtime-persistence-seam.md) touch points，非本 enum 的落点。）
- `core/gherkai_core/adapters/report_store/local.py`：`_STATUS_COLOR`（每态各一色 + 兜底灰 `#57606a`；着色意图见决定二「视觉映射」）；index.html 的连锁失败旁注读 `shortcircuited`。
- `cli/gherkai_cli/render.py`：文本汇总的连锁失败旁注同读 `shortcircuited`（被短路 step 显 skipped 态 + 旁注）。
- `cli/gherkai_cli/__main__.py`：同步 `run` 的退出码读内存 `RunResult.status`（决定五数据源）；`status`/`--wait` 的终态判定引 `TERMINAL_STATUSES`。
- `engines/novaact/gherkai_worker_novaact/run_scope.py` + `engines/midscene/src/worker/run-scope.mts`：scope 内上游 `status==error` 后短路后续 step、发 `step_skipped`（不调 AI）。
- 交叉指针落在：[0024](./0024-worker-core-protocol.md)（「`status` 三态」条的 core 内态澄清 + wire 的 `step_skipped` 事件段）/ [0026](./0026-schedule-module.md)（「status 归约」段的 `_NON_VERDICT` 入口过滤与 job 级派生态）/ [0016](./0016-execution-architecture-core-lib-run-model.md)（数据模型表 Step 行的 skipped+`shortcircuited`）/ [0028](./0028-transient-network-ssl-resilience.md)（scope 内短路条：defer 转实现，判据/承载）。

## 重议 / 留口子

- **主动 skip 的退出码语义待定**：本 ADR 的 skipped 是 fail-fast 派生态（必伴随 error → 退非 0）。
  若未来引入**用户主动 skip 某 scope**（非 fail-fast），「全 skipped、无 error」的 run 退 0 还是非 0
  取决于「批次不完整算不算失败」——这需真实需求才好定，届时单独定（决定三的 `_aggregate` 入口过滤已为此留好正确性兜底）。
- severity 序若随新态/新引擎扩充，集中改 `_STATUS_SEVERITY` 一处即可。
