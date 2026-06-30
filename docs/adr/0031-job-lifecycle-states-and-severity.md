# job 生命周期态：skipped / aborted + severity 数值序

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
  本地构造 `JobResult` 时赋。故**它们只活在 job 级（scope 级），永不出现在 StepDone/ScenarioDone.status**。

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

## 决定二：severity 数值序，两层分清

severity **只用于终态**（passed/failed/error/skipped/aborted）的排序/着色/聚合；前置态 pending/running 不在此表（见决定一·补）。
`Status` 是字符串，按字母序比大小是**错的**（`'error' < 'failed' < 'passed'` 字母序与严重度**正好反**）。
故定义一张 severity 数值表，比较/单调升级一律用它、绝不拿字符串比：

`Status` 是字符串，按字母序比大小是**错的**（`'error' < 'failed' < 'passed'` 字母序与严重度**正好反**）。
故定义一张 severity 数值表，比较/单调升级一律用它、绝不拿字符串比：

```
job 级（排序 / 着色 / 单调升级用）：
   skipped = -1  <  passed = 0  <  failed = 1  <  error = 2  <  aborted = 3
   （skipped 最轻——没执行最该被无视；aborted 最重——有现场最该被人看）

run 级（聚合用）：
   只比 {passed=0, failed=1, error=2} 三态取 max
```

**为何 run 级不含 skipped/aborted**（验证过的关键洞察）：skipped/aborted **只在 fail-fast 路径产生**，
而 fail-fast 的唯一触发条件是「某 job 已经 `error`」——那个 error job 在 run 级聚合里已把 run 顶成 `error`。
所以无论 skipped/aborted 怎么算，run 必为 error，它俩**根本不需要进 run 级比较**。它们是 job 级、单写者
（fail-fast 主线程 / worker 自己一次写定终态）、**不参与 run 级单调升级**。

## 决定三：`_aggregate` 入口过滤 skipped/aborted（把正确性钉进函数，不靠外部不变量）

run 级聚合（`schedule._aggregate`）改成：**入口先滤掉 skipped/aborted，再走原三态 max 逻辑**。

```python
# 入口过滤名单：终态判定之外的态（skipped/aborted 派生态 + pending/running 前置态）都不进 run 级聚合
_NON_VERDICT = (Status.SKIPPED, Status.ABORTED, Status.PENDING, Status.RUNNING)

def _aggregate(statuses):
    statuses = [s for s in statuses if s not in _NON_VERDICT]  # run 级只看真正出了判定的 job
    if any(s == Status.ERROR for s in statuses): return Status.ERROR
    if any(s == Status.FAILED for s in statuses): return Status.FAILED
    return Status.PASSED
```

- 过滤名单**含 pending/running**（决定一·补）：是**前向口子**——当前 RunState.status 不做增量聚合（见下），
  但 `_NON_VERDICT` 含前置态，为未来「实时增量聚合 run 级 status」（WebUI 轮询面）预留正确性兜底：届时一个还在
  `running` 的 job 不会污染 run 级 status。
- 不改也「碰巧正确」（有 skipped/aborted 必有 error 同批短路），但 `else: return PASSED` 是脆弱兜底——
  一旦未来引入**非-fail-fast 的 skip**（如主动 `--skip`），「全 skipped 无 error」的 run 会被误判 `passed`。
  入口过滤把正确性钉死在 `_aggregate` 内、不依赖「skipped 必伴随 error」这个外部假设。
- **scenario 内归约路径不改**（喂进去的全是 worker 三态，永不含 skipped/aborted）。
- **当前 run 级 status 只算一次**：`_aggregate` 仅被 schedule 在归约 `RunResult` 时调一次；落库的 `RunState.status`
  由 `finalize` 从那个已算好的 `result.status` 一次写定（之前一直停在 `pending`，[0030](./0030-realtime-persistence-seam.md)）——
  **没有「实时增量聚合 RunState.status / severity 单调升级」的运行路径**。`_NON_VERDICT` 含前置态、与未来增量聚合
  共用同一过滤名单/severity 表收敛到同一终值，是为那条尚未实现的路径留的口子（见上）。

## 决定四：[0024](./0024-worker-core-protocol.md) 线协议不改，只补一句澄清

worker↔core 的 JSON 线协议**保持三态**（worker 永远只报 passed/failed/error；skipped/aborted 时 worker 根本没起或已被掐、
不可能也不需要上报）。skipped/aborted 与线协议**正交**。仅需在 [0024](./0024-worker-core-protocol.md) 的「status 三态」处
补一句指针：「skipped/aborted 是 core fail-fast 派生态、非 worker 上报态、不进 wire（见 [0031](./0031-job-lifecycle-states-and-severity.md)）」。

## 决定五：退出码改基于 run 级 severity

cli 退出码从「`status.value == 'passed'` 才 0」改为**基于 run 级 severity**（`run.status == PASSED → 0，否则 1`）。

- **数据源**：退出码读 **schedule 返回的 `RunResult.status`（内存终值，必是终态）**，不回读 RunStore 落库态（后者实时写下可能停在 pending/running，且 `--no-report` 时根本没落库）。
- 当前结果不变：含 aborted/skipped 的 run 必伴随 error → run=error → 退 1（CI 红）。aborted 有副作用、skipped 因别人崩才没跑，整批确实失败，退非 0 正确。
- 改成基于 severity 而非字符串相等，**对未来新态更稳健、可读性更好**（判断点收敛到一处）。

## touch points（实装清单）

- `core/model.py`：`Status` 加 SKIPPED/ABORTED（判定派生态）+ PENDING/RUNNING（生命周期前置态），注释标明 core 内态、非 wire；新增 `_STATUS_SEVERITY` 表（仅终态）+ `_NON_VERDICT` 过滤名单 + 比较辅助。
- `core/schedule.py`：
  - 起 worker 前 `abort_flag` 已 set 分支 → SKIPPED（worker 从未 spawn）；
  - 事件循环中因 `abort_flag` 被 stop 分支 + 其 WorkerNetworkError 竞态回填 → ABORTED；
  - **超时（deadline）分支维持 `error`+`errorType=timeout`，不归 aborted**——回填判断看 `abort_flag` 而非笼统 `self_stopped`（`self_stopped` 被 timeout 与 fail-fast 共用）；
  - `_aggregate` 入口过滤 `_NON_VERDICT`。
- `core/serialize.py`：JobResult/RunResult 链路 round-trip 自动支持新值（`Status(str,Enum)` 接受新字符串），补单测覆盖 skipped/aborted。（**注**：`RunState` 链路的 `run_state_to/from_dict` 因 Map 形状还要改，见 [0030](./0030-realtime-persistence-seam.md) touch points，非本 enum 改动。）
- `core/adapters/report_store/local.py`：`_STATUS_COLOR` 现含 passed(绿`#1a7f37`)/failed(红`#cf222e`)/error(琥珀`#9a6700`)、其余走兜底灰`#57606a`。新增：skipped（弱化灰）、aborted（比 error 更扎眼，如紫/深红，别和兜底灰混）、pending/running（「进行中」灰/蓝）。否则新态全走兜底灰、aborted 看不出严重。
- `cli/cli/__main__.py`：退出码改基于 severity，读 `RunResult.status`（见决定五数据源）。
- `docs/adr/0024`：「status 三态」处补澄清指针（决定四）。
- `docs/adr/0026`：line 75「status 归约 scenario→job→run 同规则」段补指针——job 级判定态扩为含 skipped/aborted、run 级 `_aggregate` 入口过滤 `_NON_VERDICT` 再取三态 max（见本 ADR 决定二/三）。
- `docs/adr/0016`：协议/RunResult 字段处「status 三态」措辞补「job 级另有 core 派生态 skipped/aborted + 前置态 pending/running，见 0031」指针。

## 重议 / 留口子

- **主动 skip 的退出码语义待定**：本 ADR 的 skipped 是 fail-fast 派生态（必伴随 error → 退非 0）。
  若未来引入**用户主动 skip 某 scope**（非 fail-fast），「全 skipped、无 error」的 run 退 0 还是非 0
  取决于「批次不完整算不算失败」——这需真实需求才好定，届时单独定（决定三的 `_aggregate` 入口过滤已为此留好正确性兜底）。
- severity 序若随新态/新引擎扩充，集中改 `_STATUS_SEVERITY` 一处即可。
