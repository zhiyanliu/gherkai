# job 与 run 的状态：skipped / aborted、severity 数值序，run 的状态只由 job 的终态算出

> **Status:** Partially-superseded-by 0034, 0051 —— [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 4 引入 scope 级 error 后做五处加法：决定一加 scenario 级合成 SKIPPED 与在途明细的显式规则，决定一·补加「非 attempted 的 `session_opened` 也刷 running」，决定三加「合成的 scenario 级 SKIPPED 不进 `_aggregate`」，决定四加 `scope_done` 携带的 scope 级 `status`，决定六加 `shortcircuited=False` 的 step 级 SKIPPED。[0034](./0034-detached-batch-reconciler.md) 的无状态批量运行使有记录的 run 的退出码读记录里的 run 状态（决定五）。这一篇描述的设计有一部分尚未实装，code 跟上之前，实际行为以 code 为准。

给 `Status` 加两个 **core 派生态**——`skipped`（排队没起）与 `aborted`（跑一半被掐）——并定义一套
**severity 数值序**，解决「`'error' < 'failed'` 字母序与严重度反向」的坑、并把 fail-fast 中止的 job 从
被误记成 `error` 区分出来。run 的状态不单独定：它只由各 job 的终态按一条取法算出，一个仍有未结束 job 的 run 只经结束写成为终态（决定三）；退出码取自 run 的状态（决定五）。

**定位**：本 ADR 是判定**数据模型**的扩展，是 [0024](./0024-worker-core-protocol.md)「status 三态」的延伸。
它怎么被实时落库（终态写 `commit_job_states`，job 的终态只写一次）见 [0030](./0030-realtime-persistence-seam.md)；detached 路径防态倒退用的是生命周期推进序（`project._lifecycle_rank`，pending<running<终态），见 [0034](./0034-detached-batch-reconciler.md)。

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
    PASSED = "passed"; FAILED = "failed"; ERROR = "error"  # ERROR 另有一个 core 来源：运行定义不可用或 run 由别的格式写出时，结束写的 error 变体把未结束的 job 记 error（决定三「结束写」）
    SKIPPED = "skipped"    # core 派生。job 级：从未认领、因而没有启动的 job，在 run 被结束写结束时记它（决定三「结束写」），没执行/没花钱/可无脑重跑，session_id 必 None；step 级与 scenario 级见决定六、决定一
    ABORTED = "aborted"    # core 派生：已启动的 job 被主动中止（fail-fast、使用方中断）或被 run 的期限截断而内容不完整，以及结束写里已认领而没有结果的 job。有副作用/有现场可查。session_id 保留不清；run 级也可取它，见决定三的取法
```

| 态 | 含义 | 对使用者 | 产生处 |
|---|---|---|---|
| `skipped` | **从未认领、worker 从未 spawn**：run 被结束写结束时仍是 `pending` 的 job（执行方自己到期、fail-fast、使用方中断、处置、云端后端到期） | 没花钱，可无脑重跑 | 结束写把运行态里是 `pending` 的 job 记 `skipped`，说明按来路取（决定三「结束写」） |
| `aborted` | 已认领而没有得出完整结果：已 spawn、跑一半被**主动中止**掐断（fail-fast，或使用方中断同步 run：SIGINT / SIGTERM，[0024](./0024-worker-core-protocol.md) 终止契约），或被 **run 的期限**截断；run 被结束写结束时仍是 `running` 的 job 也记它 | 动过、有副作用、先看现场再重跑 | 前两种：作出停止决定时首次仲裁落定 `stop_reason`（主动中止为 `abort`，到点为 `timeout`），内容不完整时由终结函数判出（[0034](./0034-detached-batch-reconciler.md) 机制二「终结函数与真值表」）；fail-fast、使用方中断与发现 run 已被别处结束经同一个 `abort_flag`，说明取最先成立的来源。第三种：结束写把运行态里是 `running` 的 job 记 `aborted`（决定三「结束写」） |

发现 run 已被别处记为已结束时，执行中的 job 同样被停下，但记录这时已是终态，它们的结果不写进记录（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五），记录里它们的状态是那次结束写给的。

> **aborted 来自主动中止与 run 的期限，不来自 job 自己的预算**（实装关键，别踩）：到点与主动中止**两条路径都会主动停 worker**，被停的 worker
> 随后可能以网络故障退出码退出。判定条件要按来源拆开——看停止决定那一刻落定的 `stop_reason`（到点与主动中止同时成立取 timeout），不看终结时刻的 `abort_flag`、也不看「是否被自己停过」这类笼统标志：后者会把到点和主动中止两类语义不同的中止混成一类、丢掉 timeout 分类；前者在先判 timeout、收尾期间别的 job 才触发 fail-fast（或使用方才中断）时已置位，按它判定会改写已落定的原因。
>
> - `stop_reason = abort`（fail-fast、使用方中断，以及发现 run 已被别处结束、结果不写进记录的那一种）且内容不完整：`aborted`。
> - `stop_reason = timeout` 按起作用的截止时刻分开：用完自己预算的 job 是 `error` + `errorType=timeout`（[0026](./0026-schedule-module.md)/[0028](./0028-transient-network-ssl-resilience.md)）；被 run 的期限截断的 job 记 `aborted`，说明是「这个 run 已超过允许运行的时间，job 被中止」，没有归因——run 的时间用完不是这个 job 自己出错（理由同本篇背景）。判定只看起作用的截止时刻是预算还是期限，截止时刻由记录算出（算法见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二第 2 条），不看说明（见下「状态是一切计算的唯一依据」条）；终结函数里两种到点各占一行（[0034](./0034-detached-batch-reconciler.md) 机制二「终结函数与真值表」）。
> - 内容完整的 job 不改判（[0034](./0034-detached-batch-reconciler.md) 机制二「内容完整后不再仲裁」）。
>
> **network 重试耗尽的 job 也不是 skipped**：[0028](./0028-transient-network-ssl-resilience.md) 的 core 层 network 重试门槛是
> 「network_error 且 `saw_step=False`」，耗尽后该 job 记 `error`。它同样 `saw_step=False`，但**已经开过会话/建连尝试（已计费）**——
> `saw_step=False` 只表「可安全重试」、不表「没花钱/没起」。故它仍是 `error`、**正常参与 run 状态的取法**（决定三），不归 skipped/aborted。
> job 级 skipped 的边界严格是「worker 从未 spawn」。

- **加进同一个 `Status` enum**（而非新开 enum）：`Status` 是 scenario/step/job/run **一切判定状态的统一承载**，
  `serialize` 全靠 `Status(d["status"])` round-trip、`index.html`/`render` 全靠 `status.value` 渲染——单点扩 enum
  即全链路自然识别。新开 enum 会让 `JobResult.status` 变 `Union`，serialize/render/html 全要分两套分支，破坏「status 单一类型」的深模块性质。
- **状态是一切计算的唯一依据，run 与 job 的说明只是描述**：run 与 job 上的说明文字不参与任何计算：状态、退出码、是否超时、是否可以处置都不看说明。理由：一旦对内容有要求，就需要对未来的任何描述都保持这种要求，这本身是坏味道。
- **它们是 core 派生态，不是 worker 上报态**：worker 只在 `step_done` / `scenario_done` 事件报三态
  （`passed`/`failed`/`error`，[0024](./0024-worker-core-protocol.md)）；job 级 skipped 由结束写记下，job 级 aborted 由终结函数（主动中止、期限截断）或结束写记下，都在 core 一侧、worker 没起 / 已被掐时赋值。故 aborted 出现在 job 级（scope 级）与 run 级（决定三的取法）；skipped 在 job 级之外另出现在 step 级（scope 内短路，见决定六）与 scenario 级（见下「scenario 级 SKIPPED」条），run 级不取 skipped（决定三）。
  各级的 SKIPPED **都由 core 本地构造、永不经 `StepDone.status` / `ScenarioDone.status` 上报**（`step_skipped` 是独立事件、非 step_done 的 status 值）。
- **scenario 级 SKIPPED**：只由 core 在收到 `scope_done.status = error` 后，对 definition 中没有任何事件的 scenario 合成（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 4，job 判定归 [0034](./0034-detached-batch-reconciler.md) 机制二「终结函数与真值表」）。含义是「scope 未就绪或会话丢失，该 scenario 未执行」；它所在的 job 的判定按真值表给出，一般为 `error`，之后到达主动中止（fail-fast、使用方中断或发现 run 已被别处记为已结束）或被 run 的期限截断、且内容不完整时为 `aborted`。合成只依据已收到的完成事实，之后到达的超时、主动中止或非零退出至多改变 job 判定与归因，不撤销已合成的明细；没有收到 `scope_done` 时不合成；在途 scenario（有 `scenario_started` 无 `scenario_done`）内尚未开始的 step 也不合成。
- **在途明细的显式规则**：有 `step_started` 无 `step_done` 的 step、有 `scenario_started` 无 `scenario_done` 的 scenario，**不合成任何记录**，判定真值里保持缺记录状态；`explain` 从事件流补取在途 scenario 里已完成的 step（`record_source: events`，所属 scenario 标 `unfinished`），只发过 `step_started` 的 step 与补取不到的 step 仍以 `record_missing` 表示「有现场可查」（[0042](./0042-step-evidence-and-explain.md) 决策七）。理由：这类明细已经开始执行、可能留下副作用，合成 SKIPPED 会把「执行过、结论未知」误写成「未执行」；job 级的 aborted 已经承载「被中止、先看现场」这一层含义，明细层不另立态。

## 决定一·补：`pending` / `running` —— 生命周期前置态，非判定状态

实时写（[0030](./0030-realtime-persistence-seam.md)）需要两个**前置态**表示「还没出判定」：`pending`（run 开始时 `create_run` 把每个 job 摆这态；没有启动的 job 一直停在这态，直到 run 被结束写结束时记 `skipped`，决定三「结束写」）
/ `running`（认领时写下，前台与后台都先认领再起 worker；前台在收到 `scope_started` 后再刷一次、带上血缘；在此之前收到非 attempted 的 `session_opened` 即刷（桌面与设备 job 都在 `scope_started` 之前发它），[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 4）。它们是 job 与 run 的生命周期前置态（`JobState.status` / 进而 `RunState`）、
绝不进 `JobResult.status`（JobResult 是终态判定，只会是 passed/failed/error/skipped/aborted）、绝不进 wire。**不变量的强制点在保存一个 job 的明细之前**（逐 job 写序见 [0030](./0030-realtime-persistence-seam.md) 决定三）：要保存的 JobResult 仍非终态即抛，这个 job 不写明细也不写终态（归约中间态用 JobResult 作载体不算违背——只有落库/上 wire 的那份受约束）；同步 run 路径由 schedule 的归约器天然只产终态。没有启动的 job 不产出 JobResult，由结束写结束、没有明细（决定三「结束写」）。

**承载方式**：加进同一个 `Status` enum（`PENDING="pending"` / `RUNNING="running"`），理由同 skipped/aborted（统一类型、serialize/render 单点识别）。
但与判定状态有**本质区别**——它们是**生命周期前置态、不是判定结论**：

- **不进 severity 表、不参与任何 severity 比较**（severity 只给终态排序用，见决定二）。
- **run 级按决定三的取法对待它们**：有 job 未结束时 run 是前置态，前置态不参与终态之间的取舍。
- **job 的状态只前进，终态只写一次**：job 生命周期是 `pending → running → 终态(passed/failed/error/…)` 的**单向推进**；终态只写一次，迟到的结果（终态之后才到的退出记录与事件）不被采用。存储怎样保证见 [0034](./0034-detached-batch-reconciler.md) 机制三②；执行中的写同样不改写已是终态的 job（[0030](./0030-realtime-persistence-seam.md) 决定四）。
  这条「只前进」是**生命周期推进**意义上的，与决定二的 severity 数值序是**两套不同的序**，不可混用。
- `_STATUS_COLOR` / index.html 给 pending/running 上「进行中」色（两者**共用同一个蓝**、报告里无需区分——pending 当前到不了 report，只为未来 RunState 视图兜底），别走兜底灰。
- **「终态」有正向真源、定义取补：`core.model.TERMINAL_STATUSES = frozenset(Status) - {PENDING, RUNNING}`**。
  凡「等到终态 / 是否已终态」的消费方（CLI `status --wait` 轮询、`status` 退出码判定、`explain` 的「判定明细尚未落地」判断、隧道守护进程的退出判据、云端推进器 Lambda 的「已收尾 run 不再推演」跳过判据（`lambdas/reconciler.py`）、worker 清理 pass 的「未终态 run 仍引用」检查、`status` 文本输出只在终态打印产物位置、`explain` 的「run 仍在运行，以下为已完成部分」提示、保存明细之前的非终态即抛（见上「不变量的强制点」）——真值集即 `grep -rn TERMINAL_STATUSES`）一律引它，
  **不各自正列白名单**——正向白名单散写多份时，新增终态漏改哪份、那份就永远判不到终态（`--wait` 无限轮询、
  隧道守护进程要等到运行期限加 300 秒才关闭隧道，均曾真实存在两份逐字副本）。取补而非正列即为此：新增终态自动入集。运行态里 run 与 job 的状态取值集合（含两个前置态）属跨版本不变的约定、不新增（[0037](./0037-distribution-and-packaging.md) 决策 7「跨版本不变的约定」），新增的只会是 step 或 scenario 级的判定状态（判定明细里的状态值，加值要给 run 记录格式版本加号，0037 决策 7「加号的纪律」第 6 问）。`TERMINAL_STATUSES` 恒等于 `_STATUS_SEVERITY` 的键集（决定二：severity 只给终态定义）。

## 决定二：severity 数值序，两层分清

severity **只用于终态**（passed/failed/error/skipped/aborted）的排序/着色/比较；前置态 pending/running 不在此表（见决定一·补）。
`Status` 是字符串，按字母序比大小是**错的**（`'error' < 'failed' < 'passed'` 字母序与严重度**正好反**）。
故定义一张 severity 数值表，比较/单调升级一律用它、绝不拿字符串比：

```
job 级（排序 / 着色 / 单调升级用）：
   skipped = -1  <  passed = 0  <  failed = 1  <  error = 2  <  aborted = 3
   （skipped 最轻——没执行最该被无视；aborted 最重——有现场最该被人看）

run 级：不按 severity 比较，按决定三的取法
```

**视觉映射（severity 序在报告着色上的落法）**：每个终态各配一个可区分的颜色、**别走兜底灰**——`aborted` 要**比 error 更扎眼**（severity 最高、有现场最该被人看），且**别和兜底灰混**；`skipped` 用**弱化灰**（最轻、最该被无视），但须与兜底灰可分。否则新态全走兜底灰、aborted 看不出严重。（前置态 pending/running 另配「进行中」视觉，见决定一·补；落点符号见下「touch points」的 `_STATUS_COLOR`。）

**run 级为何不按 severity 取 max**：job 级把 aborted 排在最重，是为了让有现场的 job 最先被人看；run 级回答的是这个 run 的结论，次序见决定三的取法。两层在两处不同：fail-fast 的唯一触发条件是「某 job 已经 `error`」，它产生的 skipped/aborted 必伴随这个 error，这个 run 的结论是 error 而不是 aborted；有 job 没有执行完的 run，已执行的 job 全部通过也不是 passed，job 级最轻的 skipped 在 run 级不能被略过。scenario 级与 step 级的合成 SKIPPED（决定一、决定六）只出现在收到 `scope_done.status = error` 的 job 里，该 job 判为 error 或 aborted，不另参与 run 级的取法。

## 决定三：run 的状态只由 job 的终态算出

run 的状态若与 job 的状态分开写——在某一刻汇总、单独写一次，或在 job 之外直接结束 run（到期、处置、读不到运行定义）——记录里就会出现「run 已结束而 job 仍是 `pending` 或 `running`」「job 全部通过而 run 是 `error`」，只能靠 run 级说明解释记录。所以 run 的状态只由 job 的状态算出；一个仍有未结束 job 的 run 要结束，由结束写先把这些 job 写成终态（下「结束写」小节）。

**取法**：有 job 未结束时，全部是 `pending` 为 `pending`，否则为 `running`；全部结束时按序取第一条成立的：有 `error` 则 `error`；否则有 `failed` 则 `failed`；否则有 `aborted` 或 `skipped` 则 `aborted`（这个 run 没有执行完）；否则 `passed`。run 是终态当且仅当全部 job 是终态。没有零个 job 的 run：建 run 的入口（`RunStore.create_run`）拒绝没有 job 的运行定义，命令行在这之前已以退出码 2 拒绝零个 scenario 的批次（[0041](./0041-agent-facing-cli-affordances.md) 决策一）。理由：run 的终态只由 job 的终态写与结束写带出，没有 job 的 run 没有任何一次写能使它结束，建得出来就会一直停在未结束；取法对空清单给出的 `passed` 因此不对应任何记录。

- **run 的状态字段没有自己的写入逻辑**：每次改变 job 状态的写在同一次写里按取法写 run 状态（云端连同状态分组），使 run 成为终态的那次写同时写下结束时刻。这些写入口见 [0030](./0030-realtime-persistence-seam.md) 决定四（结束写的 error 变体不经取法的计算：它把未结束的 job 都记 `error`，run 级直接写 `error`，与取法的结果相同，下「结束写」小节）；取法要看全部 job，各写入口怎样在同一次写里按取法写出 run 状态见 [0034](./0034-detached-batch-reconciler.md) 机制三②。run 到终态之后运行态的任何写都不成立，规则、理由与依赖方见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五。
- **scenario 判定到 job 判定的归约是另一条路径**：终结函数内容完整那一行按 scenario 判定取最重（任一 `error` 为 `error`，否则任一 `failed` 为 `failed`，否则 `passed`，即 `_aggregate`），喂进去的全是 worker 三态，永不含 skipped/aborted；scenario 判定集为空的情形由终结函数先判 error，见 [0034](./0034-detached-batch-reconciler.md) 机制二。
- **合成的 scenario 级 SKIPPED 不喂给 `_aggregate`**（决定一）：它只进 JobResult 的明细，不进 scenario 判定集；该 job 的判定来自 [0034](./0034-detached-batch-reconciler.md) 机制二「终结函数与真值表」（`scope_done.status = error` 在无主动停止、退出码 0 时判 ERROR，归因见真值表），不经 scenario 归约。保证是「压根不喂进去」，与决定六对 step 级 SKIPPED 的处理同一取向。
- **被拒方案**：①处置只写 run 级、job 保持原样；②到期时未启动的 job 保持 `pending`、run 级另记 `error` 加说明；③按原因区分到期与中断的 run 级优先序；④run 级在 job 之外单独写一次终态。四者都让 run 与 job 的终态分开写，记录要另靠说明解释，正是本决定开头的问题。

### 结束写：结束一个未结束的 run

结束一个仍有未结束 job 的 run 只经结束写；job 都由执行结果结束时，run 在最后一个 job 的终态写里随之成为终态（见上「run 的状态字段没有自己的写入逻辑」条）。

- **结束写**是一次条件写：run 未结束时，把每个未结束的 job 写成终态并各带一句说明，run 状态随之成为终态，run 级写下结束的原因与结束时刻（结束时刻由调用方给）。判断只看运行态，不读事件。结束写有两种做法，各是一个写入口，按来路取其一、不混用（两个入口为什么分开见 [0030](./0030-realtime-persistence-seam.md) 决定四「error 变体是另一个写入口」条）；云端的存储有这两个入口，本机的存储只有前一个：
  - **按本格式的模型算出的结束写**，端口入口是 `RunStore.end_run`（[0030](./0030-realtime-persistence-seam.md) 决定四）：读整份运行态，按本格式的模型算出各 job 的终态，运行态里是 `pending` 的（从未认领，因而没有启动）记 `skipped`，是 `running` 的（已认领而没有结果）记 `aborted`，run 状态按上面的取法给出；整体替换 `jobs`，读到的条目里不认识的属性并进要写下的条目（[0030](./0030-realtime-persistence-seam.md) 决定四「改写运行态时原样保留不认识的部分」条）。只对与本方 run 记录格式版本相同的 run 用：本格式的模型读别的格式的运行态可能读错，并回不认识的键还会在记录里留下新旧两套状态（[0037](./0037-distribution-and-packaging.md) 被拒方案「跨格式时用本格式的读写方读写别的格式的运行态」）。下「来路」各条都用它。
  - **error 变体**：只写运行态的公共部分的结束写，是另一个入口，只在云端的存储（DDB adapter）上、不在 `RunStore` 端口上：只有云端推进器用它，本机没有用到它的来路（下「运行定义不可用、或 run 由别的格式写出时」条末）。运行定义不可用与别的数据版本写出的 run 用它，写法见同一条。
  - 两种做法的条件相同：run 未结束，云端另要求写入序号等于读到的值，写不成即重读、再判一次（[0034](./0034-detached-batch-reconciler.md) 机制三②）。两者在存储一侧各自的步骤见 [0030](./0030-realtime-persistence-seam.md) 决定六「两个写入口的步骤」。
- **来路**（按本格式的模型算出的结束写）：各来路的条件写在各自的定义处。
  - 执行方自己到期（条件见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二第 3 条）。
  - 前台的 fail-fast 与使用方中断：执行中的 job 停下、各自得出结果之后，余下没有启动的（[0026](./0026-schedule-module.md)「失败隔离」、[0024](./0024-worker-core-protocol.md) 终止契约「使用方中断」条）。使用方中断含落在建 run 之后、开始执行之前的那一种：已启动的 job 数为零、全部 job 仍是 `pending`，与执行期间被中断是同一种情形；前台 `run` 的进程这时已持有生命期锁、就是推进器，由它自己做这次结束写，取说明表里同一行（这一出口的退出码与说明见 [0035](./0035-local-app-testing-via-tunnel.md) 决策 3「三种组合的宿主与次序」里「前台 `run`」一条，理由与被拒方案也在那里）。
  - 处置（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策六、七）。
  - 云端后端到期（怎样结束见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九第 1 条，含前提）。
  - 以后的取消（条件在取消的设计里定）。
- **运行定义不可用、或 run 由别的格式写出时**（云端推进器读不到可用的运行定义，或提交记录头里的 run 记录格式版本不是后端的；各分支见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九「落实时」一段），结束写取它的 **error 变体**：每个未结束的 job 记 `error`，这些 job 不是被中途结束，是没法执行；run 随之为 `error`。error 变体只写运行态的公共部分（各个 run 记录格式版本都按同一形态写的那几项，[0037](./0037-distribution-and-packaging.md) 决策 7），不按本格式的模型解读运行态，也不经按模型算出各 job 终态的那一步：一次条件写，条件同上（run 级状态仍为 `pending` 或 `running`、写入序号等于读到的值）；写下 run 级的 `status` 与 `status_group` 为 `error`、`ended_at` 为调用方给的结束时刻、`message` 为原因，写入序号加一；`jobs` 取读到的原值，只把状态为 `pending` 或 `running` 的条目的 `status` 记为 `error`、`message` 各写同一句原因，条目里其余属性原样复制；运行态的其余属性不动。它不按本格式的模型重建记录，所以不需要并回不认识的键，同格式与别的格式写出的 run 都走这一个入口；写不成时与另一种做法一样重读、再判一次（[0034](./0034-detached-batch-reconciler.md) 机制三②）。原因的几句见本节说明表下；结果由 0054 实测项 23 核对，只改公共部分、其余属性不变由 0054 实测项 21 核对。本机没有这种情形：本机的两个宿主（前台 `run` 的进程、后台推进进程）都是自己生成运行定义、自己建 run，推进时用内存里的那一份、不从记录读回，推进它的就是建它的那个发行版本，读到的永远是自己的格式（记录格式版本与它不同的处置方给出 `other_version`，0054 决策八）；运行定义照旧写进 run 目录，供 `status`、`explain`、报告与处置方读。不读回的理由与被拒方案（本机后台推进进程从记录读回运行定义再推进）见 [0034](./0034-detached-batch-reconciler.md)「端到端流程」里 local 一节。
- **结束写不写判定明细、不点名**：由结束写结束的 job 没有执行结果，状态与说明只在运行态里（明细与点名见 [0030](./0030-realtime-persistence-seam.md) 决定三）。`explain` 怎样给出这类 job 见 [0042](./0042-step-evidence-and-explain.md) 决策四、决策七，报告怎样显示见 [0027](./0027-runreport-aggregation-index.md)「index.html 形态」。

说明文字按来路取：

| 来路 | run 级 | `skipped` | `aborted` |
|---|---|---|---|
| 执行方自己到期 | 已超过允许运行的时间 | 这个 run 已超过允许运行的时间，job 没有启动 | 不出现 |
| fail-fast | 有 job 出错，余下的 job 不再启动（fail-fast） | fail-fast：其他 job 出错，本 job 没有启动 | 不出现 |
| 使用方中断 | 收到中断信号，余下的 job 不再启动 | 收到中断信号，本 job 没有启动 | 不出现 |
| 处置：锁拿到了 | 执行这个 run 的 gherkai 进程已退出 | 执行这个 run 的 gherkai 进程已退出，job 没有启动 | 执行这个 run 的 gherkai 进程已退出，job 没有结果 |
| 处置：已过期限加 300 秒（含云端后端到期） | 已超过允许运行的时间 | 这个 run 已超过允许运行的时间，job 没有启动 | 这个 run 已超过允许运行的时间，job 没有结果 |
| 运行定义不可用 | 后端不再执行它的原因（本表下的几句） | 未结束的 job 都记 `error`，说明同 run 级 | 同左 |

处置的各句末尾另加「（已记为已结束）」；两个条件同时成立的处置取「锁拿到了」那一行。说明表的各句在 core 里只有一处：按本格式的模型算出的结束写各条来路的那一行在 `run_status.RUN_ENDINGS`；运行定义不可用那一行（run 由别的格式写出时同用这一行）只有一句原因，由调用方从下面四句里选取、交给 error 变体的入口。原因有四句，同样只在 core 的 `run_status` 一处，由云端推进器按 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九「落实时」一段的分支选取：记录格式版本不合（「这个 run 的记录格式版本是 2（由 gherkai 1.5.3 写出），后端执行的是 3，后端不再执行它。」）、worker 协议版本不合（「这个 run 记下的 worker 协议版本是 2，后端是 3，后端不再执行它。」）、「提交记录不完整或形态不对，后端不再执行它。」、「提交记录没有记下 worker 镜像，后端不再执行它。」（引号里是样例，数字与版本取自记录）。四句只陈述事实，不说该升级哪一边、不给命令（[0037](./0037-distribution-and-packaging.md) 决策 7）；句里取自记录的值（写出版本、记录格式版本数、协议版本数）都按字节截断，整句长度有上界（[0034](./0034-detached-batch-reconciler.md) 机制三「条目大小」）。说明只是描述（决定一「状态是一切计算的唯一依据」条）：结束写成立与否、job 与 run 记成什么，都不看说明有没有、是什么。参数形态的校验不在此列：说明表一行构造时核对哪几格带说明，与它的结构字段相符（`run_status.RunEnding`），这是对参数的约束，不改变任何判定。

- **一次结束写只带一行说明，多条来路先后成立时取最先成立的那条**：例如前台已因 fail-fast 中止、或先收到使用方中断，之后又过了停止启动的时刻，结束写取 fail-fast 或使用方中断那一行。理由：最先成立的来路已经使余下的 job 不再启动，之后成立的来路不改变哪些 job 没有启动；这与中止的说明取最先成立的来源（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二「一次前台执行可能因三种原因停下」一段）是同一条原则。处置的两个条件在同一次判断里成立、没有先后，按上一段取「锁拿到了」那一行。先后按登记：停止启动的时刻在第一次被检查观察到时登记，fail-fast 与使用方中断在 run 的中止标志第一次登记来源时登记（0054 决策二），两者登记在同一处、只记第一次（[0026](./0026-schedule-module.md)「起 worker 与重试之前的检查」）。
- **执行方自己到期、fail-fast、使用方中断这三条来路不结束执行中的 job，结束写另以没有 `running` 的 job 为条件**：这三条来路的条件本来就要求执行中的 job 都已结束（执行方自己到期见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二第 3 条；fail-fast 与使用方中断是执行中的 job 停下、各自得出结果之后），说明表里它们的 `aborted` 一格因此不出现，也不为表里不出现的情形另造说明。条件按结束写写下时的运行态判断：写下时仍是 `running` 的 job（例如读运行态之后才落下、还没有结果的认领）不会被这次结束写记成 `aborted`，云端重叠推进时这样的 run 按继续推进处理（0054 决策二后台推进条「收尾与报告」）；条件不成立时结束写不写、返回未写成。理由：条件要在写下的那一刻成立，而调用方不经手写入序号（[0030](./0030-realtime-persistence-seam.md) 决定六「STATE item 带写入序号」条），所以条件随这次写一起判断。结束不结束执行中的 job 是说明表里按本格式的模型算出的各行的结构属性，在 core 里是 `run_status.RunEnding.ends_running_jobs`，与说明分开：结束写成立与否不看哪一句说明给没给出。处置的两行与 error 变体结束执行中的 job，不带这个条件。
- **理由**：所有来路都经结束写，「run 已结束」与「每个 job 都已结束」同时成立；两种做法只在怎样读运行态、怎样定出各 job 的终态上不同，都不留未结束的 job。
- **被拒方案：到期时把未启动的 job 记 `error`**：run 的时间用完不是这些 job 的原因。`error` 表示 job 自己没能执行完，记它会让跨 run 统计与 CI 归因把被牵连的 job 算成自身出错（本篇背景）；借用启动失败的补偿来记，错误类型与说明也都对不上。没有启动的 job 记 `skipped`：没执行、没花钱、可以直接重跑。error 变体记 `error` 不在此列：那些 job 是没法执行，不是没轮到。

## 决定四：[0024](./0024-worker-core-protocol.md) 线协议对 step 与 scenario 的判定保持三态，scope 级 error 另有载体

worker↔core 的 JSON 线协议对 step / scenario 的判定**保持三态**（worker 永远只报 passed/failed/error；skipped/aborted 时 worker 根本没起或已被掐、
不可能也不需要上报）。skipped/aborted 与线协议**正交**。[0024](./0024-worker-core-protocol.md) 的「`status` 三态」条已带这句澄清：
skipped/aborted（连同前置态 pending/running）是 core 内态、非 worker 上报态、不进 wire。

- **`scope_done` 可带 `status: error` 与 `errorType` / `message`**（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 4，三个可选字段同进同出）：它是 **scope 级判定**的载体，用于 `scope_started` 之前的执行前失败与执行中的会话丢失，`status` 只允许 `error`；它**不是 step 的第 4 态**，worker 对 step 仍只报三态。core 收到它后才合成决定一的 scenario 级 SKIPPED 与决定六的 `shortcircuited=False` step 级 SKIPPED，这些合成态同样不进 wire。

## 决定五：退出码取自 run 的状态

`run`、`status --wait` 与 `status` 的退出码取自 run 的状态：`passed` 为 0，其余终态为 1；各命令的细则如下。

- **数据源**：有记录时读记录里的 run 状态，与输出里的状态出自同一处（状态的权威是运行态，[0030](./0030-realtime-persistence-seam.md) 决定三）；`run --no-report` 不写记录，按决定三的取法在内存里算。
- **`run`**：按记录里的 run 状态，`passed` 为 0、其余为 1；处理过使用方中断时按信号取 130（SIGINT）或 143（SIGTERM）；run 在本次执行结束之前已被别处结束时为 1（不输出汇总与 `--json`，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五），同时处理过中断时仍按信号取；运行期读写记录失败时非零（不输出汇总，[0030](./0030-realtime-persistence-seam.md) 决定七），同时处理过中断时同样按信号取。
- **`status --wait`**：一到终态即返回，`passed` 为 0、其余终态为 1（自己处置的同样，处置见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策八）；这个 run 的记录格式版本与本机不同时，在开始等待之前以 2 结束（[0037](./0037-distribution-and-packaging.md) 决策 7）；等待与处置期间读写记录失败为 2（run 目录不过边界检查见下「退出码 2」一条）；运行态读不出为 2；既没有锁可凭、也没有期限可等时为 2，不等待（只在等得到头时等待，0054 决策八）：本机是锁不可用而期限也读不出，云端没有锁，期限读不出（提交记录不存在而运行态在、提交记录内容不合法）即为 2；云端的报告前缀与后端所用的不一致为 2，不处置（run 未结束时在开始等待或写下处置之前比对，已结束的 run 不比对，0054 决策八「云端处置方的报告前缀」一条）；提交记录不合法的 run 只在本机可以被本命令处置（期限读不出、只凭生命期锁，0054 决策六），其中提交记录的头不合法的，处置之后显示时与不带 `--wait` 的 `status` 一样为 2；被中断时按信号取（SIGINT 为 130、SIGTERM 为 143），本命令处置之前与之后被打断各怎样说明见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策八。
- **`status`**（不带 `--wait`）：未结束或 `passed` 为 0、其余终态为 1；这个 run 的记录格式版本与本机不同（[0037](./0037-distribution-and-packaging.md) 决策 7）、提交记录的头不合法（不是合法内容，或读不出记录格式版本）、运行态读不出（内容解析不了）或读写记录失败为 2，以一句说明结束、不显示这个 run；显示只读提交记录的头，头之外的定义违约不影响显示。运行态读不出时不取 `list-runs` 的做法（标一行「无法读取」、以 0 结束）：清单的 0 表示读到了清单，单个 run 的查询却给不出它要的那个 run 的任何状态，0 会被读作查询成功、run 未结束。
- **`submit`**：退出码表示提交成功与否、不表示判定：已提交（run_id 已返回）为 0；判定由 `status --wait` 给出。数据版本比不上为 2，不写任何记录：云端是云端后端接口版本、run 记录格式版本与所选变体在各个用到的引擎上的镜像的 worker 协议版本，本机是本机 worker 的 worker 协议版本（[0037](./0037-distribution-and-packaging.md) 决策 7）。等待提交结果时被 Ctrl-C 打断为 130，stdout 不输出 run 标识（标准输出与退出码的做法见 [0035](./0035-local-app-testing-via-tunnel.md) 决策 3「`submit` 的标准输出与退出码」一条）：本机 `submit` 等后台推进进程的回报时；云端 `submit` 等隧道守护进程的回报时，以及从开始建 run 到交出 run 标识之前（给不给 `--expose-local` 都是）。这时 run 可能已经建成，说明里给出找到它的命令；各情形下 run 是否已经建成、之后怎样，见 [0035](./0035-local-app-testing-via-tunnel.md) 决策 3「三种组合的宿主与次序」。
- **`settle-runs`**：执行完成为 0（含一个都没处理），跳过（含记录格式版本与本机不同的 run 与清理暂存目录时的各种跳过，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策八）不改变退出码；用法错误、后端不可达、给出的 run 不存在、报告目录不过边界检查（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策四）为 2；云端的报告前缀与后端所用的不一致为 2，不处置（在第一个要处置的 run 写下处置之前比对，0054 决策八「云端处置方的报告前缀」一条）；读写记录失败为 2，就此停止；被中断而没有做完时按信号取（SIGINT 为 130、SIGTERM 为 143）；报告前缀不一致、读写记录失败与被中断这三种都先输出已处理的部分（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策八）。
- **退出码 2**：开始执行之前的问题与查不到 run（落库一侧的几种，含本机建 run 时写记录失败与 run 标识重复（run 已存在，[0030](./0030-realtime-persistence-seam.md) 决定四），见 [0030](./0030-realtime-persistence-seam.md) 决定七「失败退出码分层」）。另有六类，各在定义处写全：数据版本比不上或读不到（云端各命令的开头、云端 `submit`、按 run 的查看与等待、本机执行之前与 worker 的比对，以及 `deploy` 的数据版本检查不通过而不改动账户的几种，[0037](./0037-distribution-and-packaging.md) 决策 7；`deploy` 在 cdk 之后的三步（[0038](./0038-worker-image-delivery.md) 四步里的后三步）比不上时账户已改动，按 0038「四步的失败语义」为 1）；边界检查不过（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策四「边界检查」一条，含 `run` 与本机 `submit` 在前置检查里对报告目录的那一次；本机 `submit` 的情形见 [0035](./0035-local-app-testing-via-tunnel.md) 决策 3「三种组合的宿主与次序」里「本机 `submit`」一条，`settle-runs` 的见上「`settle-runs`」一条）；锁不可用、暂存目录连续被占用（只对建 run 的一方，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策三；本机 `submit` 的情形见该决策「谁在何时拿」）；本机后台推进进程在回报之前退出（由 `submit` 给出，[0035](./0035-local-app-testing-via-tunnel.md) 决策 3「后台推进进程在回报之前退出」一条）；本机后端的报告目录路径太长，或路径里有一层名字太长（各命令在入口检查，规则与适用的命令见 [0030](./0030-realtime-persistence-seam.md) 决定四「报告目录的路径长度」条）；`run` 给出云端后端（[0016](./0016-execution-architecture-core-lib-run-model.md) 决策 A）。
- 非 `passed` 的终态都以 1 结束：fail-fast 下 run 必为 `error`（aborted 有副作用、skipped 因别人崩才没跑，整批确实失败，CI 红）；记 `aborted` 的 run 没有执行完（决定三）。两者都不是可以放行的结论。

## 决定六：step 级短路——SKIPPED 下探到 step 级 + 正交 `shortcircuited` 布尔

[0028](./0028-transient-network-ssl-resilience.md) 记过一个真跑暴露的空白：scope 内 step 串行，**上游 step `error` 不短路下游** →
下游在损坏环境（如 SSL 错误页）上跑出误导性 `failed`。本决定兑现 [0028](./0028-transient-network-ssl-resilience.md)「scope 内 step 级短路」条记的执行修复方向：**worker 在 scope 内短路**——
上游 step `status==error` 后，不再对后续 step 调 AI（省钱、报告干净），而是为每个被跳过的 step 发一个 `step_skipped` 事件。

**这引出一个新问题：被短路的 step 用什么态？** 定下如下承载方式（三条硬约束，别踩）：

- **载体是独立 `step_skipped` 事件，不是 `step_done` 的第 4 个 status 值**。理由：wire 严格三态（决定四），
  worker 报判定只能是 passed/failed/error。「这步没跑」不是判定结论、是执行事实，故走**平行于 step_done 的独立事件**
  （`{type:"step_skipped", scenarioId, stepIndex}`，无 status/votes/cost 字段），[0024](./0024-worker-core-protocol.md) wire 相应加此事件。
- **core 收到 `step_skipped` → 本地构造 `StepResult(status=Status.SKIPPED, shortcircuited=True)`**。复用既有 `Status.SKIPPED`
  枚举值（它已在 severity 表 = -1）——**在 StepResult 层，SKIPPED 直观表达「这步没跑」**，
  人/AI 一眼可读。**但它由 core 本地赋、不经 wire**（同 job 级 skipped/aborted 的性质：core 派生态、非 worker 上报态）。
- **`shortcircuited: bool` 是与判定轴正交的第二维**：status 轴回答「跑出什么结论」（passed/failed/error/skipped），
  shortcircuited 轴回答「为什么 skipped」（True 表示因上游短路而被跳过，False 见下「scope 级 error 后合成的 step 级 SKIPPED」条）。渲染层的连锁失败旁注**改读 shortcircuited**
  （见 [0028](./0028-transient-network-ssl-resilience.md) 从「error 后 failed」迁到「被短路的 step」），比原「按 status 顺序猜」更精确、判据单一。

**关键不变量：step 级 SKIPPED 绝不写进 `scenario_status`**（守 severity/`_aggregate` 零污染）。`_reduce` 处理 `step_skipped`
时只把 StepResult 暂存待挂（同 step_done 的暂存路径），**不碰 scenario_status**——故它不参与 scenario 归约、不进 `_aggregate`
（保证是「压根不喂进去」）。scenario/job 的判定状态由「上游那个 error step」
决定，与「后面短路了几个 step」无关。

**scope 级 error 后合成的 step 级 SKIPPED**（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 4 的加法）：`StepResult(status=SKIPPED, shortcircuited=False)` **只出现在 job 处于 scope 级 error 时**（收到 `scope_done.status = error`），含义是「scope 未就绪或会话丢失，这步未执行」。它由 core 对无事件的 scenario 内的全部 step 合成，不经 wire（在途 scenario 内尚未开始的 step 不合成）；同样不写 `scenario_status`、不进 `_aggregate`。有 `step_started` 无 `step_done` 的在途 step 不合成（决定一「在途明细的显式规则」）。

**判定结果读端对三个明细键的缺省**：`job_result_from_dict` 重建 `StepResult` 时，`shortcircuited` 缺键取 False，`message` 缺键取 None，step 的 `report_refs` 缺键按空列表读（`message` 归 [0042](./0042-step-evidence-and-explain.md) 决策三，step 级 `report_refs` 归 [0027](./0027-runreport-aggregation-index.md) 与 0042 决策一）；三者都与 `StepResult` 的内存默认值一致，写端对这三个键始终写出。本条只定这三个键的缺省，不推广成「判定结果一律宽容读」：判定轴的键（job 与 scenario 的 `status`、job 的 `scenarios`、scenario 的 `scenario_id`、step 的 `index` 与 `status`）缺了即读失败，`scenarios` 缺席不读成零个 scenario。依据是判定明细归 run 记录格式版本，按 [0037](./0037-distribution-and-packaging.md) 决策 7 的基线与登记管：判定轴的键是必有键，这三个键是登记了缺席含义的可省键，缺席含义就是本条的缺省。必有键缺席即违约，防的是读方按缺键的缺省值静默改变判定或派发（运行定义里同理，如把设备 job 当成桌面 job）；判定结果的这三个键缺失时，缺省值表达的正是「这一步没有这项明细」（无失败原因、无 step 级产物、不是被短路），只影响明细的展示（如连锁失败旁注），不改变 step、scenario、job 任何一级的判定。同一 JobResult 的 `sessions` 与设备计量两键在写端按「无值省键」写出（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 4、7），同是可省键，读端缺席读作没有值。**不以兼容旧落盘为理由**：1.5 之前写出的文件在更早的一步就被拒绝——单 job 文件（自包含形态）先经 `job_from_dict` 按必有键重建内嵌的 definition，缺 `target` 等键即抛 `DefinitionContractError`；整 run 的聚合形态先经 `run_meta_from_dict` 对记录格式版本的核对（1.5 之前写出的记录没有这个值，读作 0，与本机不同）。把这几处缺省写成兼容旧落盘，会让读者以为判定明细为 1.4 的落盘留有一条兼容路径，而这条路径并不存在。**被拒方案：把这三个键改成必有键**——同一函数的明细键会分成这三个键必有、`sessions` 等其余明细键可省的两种读法，这条分界在判定上没有依据，又防不住任何误判：判定轴的键已经必读，明细键缺失不会让一个判定变成另一个。

**job 级 skipped（决定一）与 step 级 shortcircuited 是两个不同层次，别混**：

| | 谁 skip | 有 StepResult 吗 | 承载 |
|---|---|---|---|
| **job 级 skipped**（决定一） | 整个 job 从未认领、worker 从未 spawn | **无**（没有判定明细，由结束写结束，决定三「结束写」） | 运行态里 job 的状态为 `skipped`（session_id 必 None、没花钱） |
| **step 级短路**（本决定） | job 起了、scope 内上游 error 后跳过后续 step | **有**（worker 发 step_skipped、core 建 StepResult） | `StepResult(status=SKIPPED, shortcircuited=True)`（会话已起、花过钱） |
| **scope 级 error 后合成**（决定一、本决定） | job 起了、收到 `scope_done.status = error`，未执行的 scenario / step | **有**（core 合成，worker 不发事件） | scenario 级 SKIPPED 与 `StepResult(status=SKIPPED, shortcircuited=False)`（job 判为 `error` 或 `aborted`，可能已产生会话费用） |

各级都复用 `Status.SKIPPED` 表「没跑」，语义一致、只是层级与成因不同。

**判据锁 `status==error`（不看 error_type）**：无论哪个引擎、network_error 还是 engine_error 都触发短路，两个引擎对称——
这也回避了 [0028](./0028-transient-network-ssl-resilience.md) 记的「两个引擎 SSL 分类不对称」欠账对短路的影响（那只影响 errorType 文案、不影响 error 这个 status）。
短路是 **scope 内**行为（上游 error 只短路**同 scenario/同 scope**的后续 step，不跨 job——跨 job 是 fail-fast 的职责，两者正交）。

## touch points（落点指针）

- `core/gherkai_core/model.py`：`Status` 的 SKIPPED/ABORTED（判定派生态）+ PENDING/RUNNING（前置态；注释标明 core 内态、非 wire）；`_STATUS_SEVERITY`（仅终态）+ `severity()` 比较辅助；`TERMINAL_STATUSES`（终态真源，取补于 `_PRE_TERMINAL`，决定一·补末条）；`StepSkipped` 事件（frozen dataclass `scenario_id`/`step_index`，无 status/votes/cost）入 `Event` Union + `StepResult.shortcircuited`（正交布尔，决定六）。
- `core/gherkai_core/schedule.py`：job 级的赋态点——起 worker 前已过停止启动的时刻、已发现 run 被别处结束，或 `abort_flag` 已因 fail-fast 或使用方中断置位 → 不启动，job 留在 pending，由结束写结束（决定三「结束写」；发现 run 已被别处结束时记录已是终态、不写）；余下的 job 不再启动的来源登记在一处、只记第一次，随返回的 `Execution.stopped_by` 交给落库服务，作结束写的来路（决定三「结束写」小节「一次结束写只带一行说明」条）；事件循环中因 `abort_flag` 作出停止决定 → 首次仲裁落定 `stop_reason = abort`，再调 `project.finalize_job` 按真值表在内容不完整时判 ABORTED（不论退出形态；`abort_flag` 只记下第一次登记的来源 fail-fast / interrupt / ended-elsewhere，它决定消息措辞）；到点分支落定 `stop_reason = timeout`，终结函数按起作用的截止时刻判：预算为 `error`+`errorType=timeout`，期限为 `aborted`（判定看该 job 停止决定那一刻落定的 `stop_reason`，判据与理由见决定一「aborted 来自主动中止与 run 的期限，不来自 job 自己的预算」注）。
- `core/gherkai_core/run_status.py`：`run_status_of`（run 状态的取法，决定三）；`RunEnding` 与 `RUN_ENDINGS`（按本格式的模型算出的结束写的说明表，决定三「结束写」小节），后端不再执行一个 run 的四句原因：记录格式版本不合、worker 协议版本不合、提交记录不完整或形态不对、没有记下 worker 镜像（error 变体的说明，同一小节说明表下）；`ending_applied` 与 `commit_applied`（按本格式的模型算出的结束写与带结果的 job 终态写对运行态的作用，两个 RunStore adapter 共用，端口入口 `RunStore.end_run` 与 `RunStore.commit_job_states`，[0030](./0030-realtime-persistence-seam.md) 决定四）。error 变体不经这两个函数，是 DDB adapter 上另一个入口、不在 RunStore 端口上，只写运行态的公共部分（决定三「结束写」小节，0030 决定四「error 变体是另一个写入口」条）。`model.JobState.message` 是 job 级说明，只由结束写写下。
- `core/gherkai_core/project.py`：`finalize_job`（终结函数：`stop_reason = abort` 且内容不完整 → ABORTED，`stop_reason = timeout` 且内容不完整按起作用的截止时刻分两行，[0034](./0034-detached-batch-reconciler.md) 机制二）；`_aggregate`（scenario 判定到 job 判定的三态取最重，只在终结函数内容完整那一行用，决定三）；`reduce_event` 的 `StepSkipped` 分支 → 暂存 `StepResult(status=SKIPPED, shortcircuited=True)`，**绝不写 `scenario_status`**（被短路 step 无 `step_started`，`duration_ms` 恒 None——没跑=无墙钟）；收到 `scope_done.status = error` 后合成 scenario 级 SKIPPED 与 `shortcircuited=False` 的 step 级 SKIPPED（决定一、决定六，合成态不进 `_aggregate`）。
- `core/gherkai_core/wire.py`：`event_from_json` 的 `step_skipped` 分支（加法，不碰 step_done 三态解析）；`step_done` 与 `scenario_done` 的 `status` 只接受 `passed` / `failed` / `error` 三态（决定四），其余取值与缺键按 worker 违约抛 `ValueError`；`scope_done` 的可选 `status` / `errorType` / `message`（决定四，`status` 只接受 `error`）。
- `core/gherkai_core/serialize.py`：JobResult 链路靠 `Status(str,Enum)` 天然 round-trip 新值（RunResult 的序列化只是输出，不往返）；StepResult to/from_dict 的 `shortcircuited`（写端始终写出；读端缺键取 False，与 `message`、step 的 `report_refs` 同一读法，依据与边界见决定六「判定结果读端对三个明细键的缺省」条）。（**注**：`RunState` 链路的 `run_state_to/from_dict` 归 [0030](./0030-realtime-persistence-seam.md) 决定五的落点清单，非本 enum 的落点。）
- `core/gherkai_core/adapters/report_store/local.py`：`_STATUS_COLOR`（每态各一色 + 兜底灰 `#57606a`；着色意图见决定二「视觉映射」）；index.html 的连锁失败旁注读 `shortcircuited`。
- `cli/gherkai_cli/render.py`：文本汇总的连锁失败旁注同读 `shortcircuited`（被短路 step 显 skipped 态 + 旁注）。
- `cli/gherkai_cli/__main__.py`：`run` 与 `status` 的退出码读记录里的 run 状态，`run --no-report` 按决定三的取法在内存里算（决定五数据源）；`status`/`--wait` 与 `explain` 的终态判定引 `TERMINAL_STATUSES`。
- `engines/novaact/gherkai_worker_novaact/run_scope.py` + `engines/midscene/src/worker/run-scope.mts`：scope 内上游 `status==error` 后短路后续 step、发 `step_skipped`（不调 AI）。
- 交叉指针落在：[0024](./0024-worker-core-protocol.md)（「`status` 三态」条的 core 内态澄清 + wire 的 `step_skipped` 事件段）/ [0026](./0026-schedule-module.md)（「status 归约」段的 job 级派生态）/ [0016](./0016-execution-architecture-core-lib-run-model.md)（数据模型表 Step 行的 skipped+`shortcircuited`）/ [0028](./0028-transient-network-ssl-resilience.md)（scope 内短路条：defer 转实现，判据/承载）。

## 重议 / 留口子

- **主动 skip 的退出码语义待定**：本 ADR 的 job 级 skipped 来自结束写（执行方到期、fail-fast、使用方中断、处置等，退出码见决定五）。
  若未来引入**用户主动 skip 某 scope**（不属于上述来路），「有 skipped、无 error 与 failed」的 run 退 0 还是非 0
  取决于「批次不完整算不算失败」——这需真实需求才好定，届时单独定。现状：全部 skipped、或部分 skipped 其余 passed 的 run 都按决定三的取法记 `aborted`，以 1 退出（决定五），即按「算失败」处理。若要让主动 skip 不算失败，须在 run 状态的取法或退出码映射上显式另定——要不要这样定，正是本条待议的问题。
- severity 序若随新态/新引擎扩充，序本身只改 `_STATUS_SEVERITY` 一处。新态只可能出在 step 或 scenario 级：运行态里 run 与 job 的状态取值集合属跨版本不变的约定、不新增（[0037](./0037-distribution-and-packaging.md) 决策 7「跨版本不变的约定」，决定一·补末条）。新增的若是终态，另须同批给报告页 `_STATUS_COLOR` 与终端 `STATUS_STYLE`（`runtime/gherkai_runtime/textui.py`，[0047](./0047-cli-human-readable-tables-with-rich.md)）各配一色，否则落兜底色（决定二「视觉映射」）。
