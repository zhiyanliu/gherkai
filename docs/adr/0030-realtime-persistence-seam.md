# 实时写存储接缝：per-job 完成回调 + RunPersistence 应用服务 + RunStore 增量 port

把「一次 run 的判定/状态**随进度实时落库**」做成正交接缝：执行编排（`schedule`，[0026](./0026-schedule-module.md)）只管跑、
不碰存储；存储编排（新 `core/persist.py` 的 `RunPersistence`）依赖 Store ports、由组合根注入具体 adapter。
这是 v1.1 云端（DDB/S3）的前置：先在 local adapter 上把「实时写 + commit-point 写序」跑通，DDB 仅作新 adapter 接入。

**定位**：本 ADR 解决「**怎么把实时落库接进来而不污染 reducer / 不让每个组合根各写一遍**」。
job 生命周期态（`skipped`/`aborted`/`pending`/`running`/severity）见 [0031](./0031-job-lifecycle-states-and-severity.md)；
DDB 的并发一致性（Map<scope_id> 按 key 定位、条件更新）见未来 DDB adapter ADR。

> **本文出现的 `pending`/`running`/`skipped`/`aborted` 这些状态值，定义与 severity 归属全在 [0031](./0031-job-lifecycle-states-and-severity.md)**；本篇只用它们描述时序，不定义。

## 背景：v1.0 是「跑完一次性写」，零实时

当前（[0016](./0016-execution-architecture-core-lib-run-model.md) 三层切分）：`schedule` 跑完返回完整 `RunResult` →
cli 单进程顺序写三层（RunStore→ResultStore→ReportStore）。`schedule` 是**纯 reducer**：每 worker 一线程把事件流
归约成 `JobResult`，主线程 `as_completed` 收齐、聚合成 `RunResult`，**全程不碰任何 store**（[0026](./0026-schedule-module.md)
刻意：为 fake-clock 可确定性单测 + 引擎/存储无关）。`sink` 只透传原始事件给进度显示。

v1.1 要「边跑边落库」（WebUI 提交即返回 runId、之后轮询看进度，[0027](./0027-runreport-aggregation-index.md)）。
难点不在写 DDB，在**怎么接这条实时写而不破坏上面两条纪律**。

## 决定一：接线用 per-job 完成回调（方案 C），不是「持久化 sink」也不是「给 schedule 注入 store」

| 方案 | 做法 | 致命问题 |
|---|---|---|
| A. 持久化 sink | cli 的 sink 收原始事件、自己落库 | sink 拿的是**原始 Event**、不是 `JobResult`；落 ResultStore 得在组合根**重写一遍** `schedule` 内部的「事件→JobResult 归约」（cost 累加/duration 时间戳/状态机），**必然漂移**，连 duration 都算不准 |
| B. 给 schedule 注入 store | `schedule(..., run_store=, result_store=)` | 把「几个 store / 数据面先于控制面的写序 / 写一半失败怎么办」这类 **I/O 编排职责**塞进 reducer，破坏 [0026](./0026-schedule-module.md)「只收 sink 回调、不碰 store」。port 可注入 fake ≠ 该注入——争议不在能否 fake，在 reducer 该不该承担编排 |
| **C. 完成回调（采纳）** | `schedule` 加 `on_job_complete(JobResult)`，在 `as_completed` 拿到**已归约好**的 `jr` 时 fire | 复用 schedule 内部成品 JobResult、**零重复归约**；schedule 仍不知道 store/写序/失败编排；与现有 `sink` 同性质（都是回调、可注入 no-op） |

`on_job_complete` 是 [0026](./0026-schedule-module.md)「注入 sink、schedule 不决定结果存哪」原则从「跑完一次性」
**推广到 per-job 粒度**——同一条纪律，不是新范式。

### 回调的形态：`default=None` 是逃生舱，不是常态

```python
# core/ports.py
class JobSink(Protocol):
    def __call__(self, job: JobResult) -> None: ...   # 收已归约的 JobResult（非原始 Event）

# core/schedule.py
def schedule(run_meta, engines, sink, opts=None, on_job_complete: JobSink | None = None) -> RunResult: ...
```

- **`default=None` 的语义是「逃生舱」**：正常路径（产品 / 组合根）**永远接** persistence；只有「单测 / `--no-report` 显式弃权 / 纯内存实验」才不接。None 让纯 reducer 不被一个正交关注点绑死——`test_schedule.py` 20+ 用例、`--no-report` 路径都不必造 no-op 传进去。
- **不是 keyword-only**（普通参数 + 默认 None），但**调用点用关键字写** `on_job_complete=...` 保自说明。
- fire 在主线程 `as_completed` 循环里**串行**（非 worker 线程），故回调实现**无需自己加锁**——这点比「回调要线程安全」更准。

## 决定二：落库编排收进 `core/persist.py` 的 `RunPersistence` 应用服务，组合根只注入 adapter

「实时写怎么落」（commit-point 写序、RUNNING 中间态、severity 增量聚合）**对 cli / WebUI / 未来 cron 完全一致，只有注入的 store adapter 不同**。
让每个组合根各写一遍 → 必漂移。故收成一处 core 应用服务（依赖 Store **ports**、不含具体 adapter、不含 reducer 逻辑）：

```python
# core/persist.py —— 编排 Store ports；不在 schedule 里、不碰执行 reducer
class RunPersistence:
    def __init__(self, run_store, result_store, report_store=None): ...
    def begin(self, run_meta, *, started_at): ...        # create_run(meta, 初始全 PENDING 的 RunState)
    def sink(self, inner_sink): ...                       # 装饰：转发进度 sink + 收 ScopeStarted→刷 RUNNING+血缘
    def on_job_complete(self, jr): ...                    # 每 job：先 save_job_result，后 update_job_state（severity 增量）
    def finalize(self, result, *, ended_at): ...          # commit point：finalize_run → ReportStore.write
```

组合根（任意皮）就只剩注入 + 三调用，**逻辑零重复、只换 adapter**：

```python
persistence = RunPersistence(run_store, result_store, report_store)   # ← 唯一差异：哪套 adapter
persistence.begin(run_meta, started_at=now)
result = schedule(run_meta, resolver, persistence.sink(progress_sink), opts,
                  on_job_complete=persistence.on_job_complete)
persistence.finalize(result, ended_at=now)
```

**架构对位**：`schedule` 编排**执行**（Engine port），`RunPersistence` 编排**存储**（Store ports），两者平级、都在 core、由组合根组合。
schedule 仍一行不碰 store。这兑现「调 adapter 落库是默认行为、不是每个 client 自己拼」。

## 决定三：commit-point 写序——数据面先、控制面摘要后

实时写时序（一次 run）：

```
run 开始（schedule 之前）:
  RunPersistence.begin → RunStore.create_run(meta, 初始 RunState[所有 job=PENDING, 总=PENDING, started_at=now])
       └ definition 先落，满足「提交即返回 runId」（[0027](./0027-runreport-aggregation-index.md)）

每个 job 完成（on_job_complete 串行 fire 已归约的 jr）:
  ① ResultStore.save_job_result(run_id, jr)             ← 数据面判定真值【先】写
  ② RunStore.update_job_state(run_id, job_state)         ← 控制面 job 态【后】刷（severity 单调，[0031](./0031-job-lifecycle-states-and-severity.md)）

job 进行中（sink 收 ScopeStarted，worker 线程、sink_lock 串行）:
  RunStore.update_job_state(run_id, JobState(scope_id, RUNNING, session_id))  ← RUNNING 中间态 + 血缘随首事件即落

run 结束（schedule 返回后）:
  RunStore.finalize_run(run_id, result.status, ended_at)  ← commit point：它一落=判定已就绪
  ReportStore.write(...)                                  ← 派生视图永远最后、从终值 RunResult 派生
```

**commit point 的意义**：数据面（ResultStore 各 job）先逐个落 → 最后才写 RunStore 终态 status。
「看到 RunStore 终态」即**保证**「所有 job 判定真值已落」。这修正了 v1.0 cli 现在的反序（先写控制面摘要、后写数据面，
中途崩会留下「说 passed 但详细结果没齐」的假象）。

> **两条写 RunStore 的路径必须共享同一把锁**（实装关键）：RUNNING 中间态刷在 **worker 线程**（经 sink，靠 `sink_lock` 串行）；
> job 终态刷 + finalize 在 **主线程**（经 on_job_complete，as_completed 串行）。这是**两个不同线程经两套不同串行机制**写同一个
> RunStore（local adapter 是「读 run_state→改→写回」的整文件 read-modify-write，**非自身线程安全**）。若各跑各的，一个 worker 正刷某 scope 的
> RUNNING、主线程同时刷另一 scope 的终态，整文件 RMW 会互相覆盖、丢更新。**不变量：所有 `update_job_state`/`create_run`/`finalize_run`
> 经同一把 store 锁**（`RunPersistence` 内持一把锁，RUNNING 路径与 on_job_complete 路径都走它，而非依赖 sink_lock 与主线程「碰巧不撞」）。

> **写序的失败语义（残留风险，本地接受）**：若 `save_job_result` 成功但 `update_job_state` 失败，
> run_state 落后于 jobs/——但 **jobs/*.json 是判定唯一权威、run_state 是可重建摘要**（依据 [0016](./0016-execution-architecture-core-lib-run-model.md)
> 三层切分=数据面是判定真值唯一权威；该「以 jobs 为准、可由 load_all 重建」的失败语义现写在 `run_store/local.py` 顶部注释），
> 消费端读判定走 `ResultStore.load_all` 兜底。`finalize_run` 没落 = run 未提交、可由 load_all 重建。
> 真事务（DDB `TransactWriteItems`）**不用**——规模化跑批会撞它的 100 项/4MB 上限，commit-point 写序把原子性需求降到 DDB 天然原子的单 item。

## 决定四：RunStore 新增三个 additive 方法，`save_run` 保留

```python
class RunStore(Protocol):
    # —— 新增（实时写）——
    def create_run(self, meta: RunMeta, initial_state: RunState) -> None: ...      # run 开始：写 definition + 初始全 PENDING 态
    def update_job_state(self, run_id: str, job_state: JobState) -> None: ...       # 单 job 实时刷（按 scope_id 定位）
    def finalize_run(self, run_id: str, status: Status, ended_at: str) -> None: ... # commit point：写聚合 status + ended_at
    # —— 保留（一次性写便捷方法）——
    def save_run(self, meta: RunMeta, state: RunState) -> None: ...                 # 仍被 test_stores 的 save/load 往返用例护住；可由 create_run+finalize 组合
    def load_run_meta(...); def load_run_state(...)                                 # 不变
```

- **新增三方法是 additive**：`save_run` 不删（`test_stores.py` 中 3 个 RunStore save/load 往返用例——`test_run_store_save_load` / `test_run_state_timestamps_round_trip` / `test_run_state_omits_null_timestamps`——仍用它；一次性写场景也仍用）。新方法只是把它的职责按生命周期拆成「开始/逐 job/结束」三段。
- `update_job_state` 按 **scope_id 定位单个 job**：local adapter 是「读 run_state→改该 scope_id→写回」的 read-modify-write（**非自身线程安全**，靠 `RunPersistence` 的单一 store 锁串行，见决定三的并发不变量）；DDB adapter 用 `SET jobs.#sid=:js`（Map 按 key 路径，见未来 DDB ADR）。这要求 `RunState.jobs` 用 **Map<scope_id> 形状**（见决定五）。

## 决定五：`RunState.jobs` 改 Map<scope_id> 形状（core model 一次到位）

`RunState.jobs` 从 `tuple[JobState, ...]` 改为 **`dict[scope_id, JobState]`**（`scope_id → JobState`）。
理由：实时按单个 job 刷状态需要「按 scope_id 定位某个 job」，list 只能按下标定位（DDB 更是无法按属性值定位 list 元素）。
Map 形状下 `update_job_state` 各 scope 互不干扰、天然支持单元素更新。

- **现在就改 core model**（不留到 DDB 阶段），改动点（含两个会**静默出错**的陷阱，务必逐一改）：
  - `model.RunState.jobs`：`tuple[JobState,...]` → `dict[str, JobState]`。
  - `serialize.run_state_to_dict`：现在是 `for js in state.jobs`——dict 化后若不改成 **`state.jobs.values()`**，会静默迭代 dict 的 **key（字符串）**、`js.scope_id` 直接 AttributeError。
  - `serialize.run_state_from_dict`：决定**落盘 JSON 形状**——本 ADR 选 **JSON 仍落 `list[{scope_id,status,session_id}]`、仅内存模型是 Map**（读回时 `{js.scope_id: js}` 重建），保 `run_state.json` 向后兼容、不动既有文件格式；DDB adapter 才在落库层用真 map item。
  - `run_state_from_result`：投影出 dict 而非 tuple。
  - **`core/tests/test_stores.py`**：现用**位置下标** `state.jobs[0].scope_id` / `state.jobs[1].status`（dict 不支持整数下标，会 TypeError）——改成按 scope_id 取（如 `state.jobs["features/wiki.feature:6"]`）。
  - （**澄清**：`report_store/local.py` 的 index.html 渲染的是 `RunResult.jobs`、cli 也只 `run_state_from_result` **写**、从不**读** `RunState.jobs`——故那两处不是 RunState 消费点，真正会被打破的是上面的 serialize 迭代与 test_stores 下标。）
- skipped 的 job 也要进 Map（它是 definition 的一部分，缺了会让 RunState 的 job 集与 RunMeta.jobs 对不齐）。各新态的 `session_id` 取值规则见 [0031](./0031-job-lifecycle-states-and-severity.md) 决定一；aborted 留 `session_id`（有现场可查）正是 Map 形状的受益场景。

## 现在做 / 留口子

- **现在做（cli-first 第一阶段，本批）**：`JobSink` port + `schedule.on_job_complete`（default=None）；`core/persist.py` 的
  `RunPersistence`（持单一 store 锁，见决定三并发不变量）；RunStore 三新方法的 **local adapter** 实现；`RunState.jobs` 改 Map（含决定五列的 serialize/test 改动点）；cli 接 `RunPersistence`（含 RUNNING 中间态）。
  用 fake store 单测断言调用序（create_run 先于所有 save_job_result；每 save_job_result 早于 finalize；finalize 是最后一个 RunStore 调用 = commit point；save_job_result 与 ScopeStarted 交错 = 流式非批量）。
  **同步更新 [0016](./0016-execution-architecture-core-lib-run-model.md)**：RunStore 契约段补 create_run/update_job_state/finalize_run 三 additive 方法 + commit-point 写序指针；三层切分表里 `RunState.jobs` 形态注明改为 Map<scope_id, JobState>（与 [0031](./0031-job-lifecycle-states-and-severity.md) 补 0024/0026 对称）。
- **下一阶段（DDB adapter）**：`DdbRunStore`/`DdbResultStore`（`SET jobs.#sid` Map 定位 + finalize 条件更新单调 severity）；
  **RunMeta definition 深树里的 step `StepArgument`（docString/dataTable）offload S3**——DDB 只存指针，adapter 内 `to_dict` 前 / `from_dict` 后钩子，不碰 serialize/model；**local 不 offload**（无 400KB 限）。
  > 注意此 offload 的对象是 **RunMeta definition 深树里的 step 参数**（控制面 definition 写 DDB 的 size 规避），与「引擎产物（trajectory/report.html）上传 S3、报 `s3://` 进 `report_refs`」是**两类不同对象、不同路径**（后者是数据面产物、属未来 Fargate 远程执行模式的事），别混。
  用 moto 测嵌套 map 单元素更新 + 部分完成态可读。
- **留口子不做**：多写者 owner/lease（当前 run_id 由组合根独立生成、提交即新，单写者，无并发同 run 写）；续跑/部分重跑的 attempt 维度（save_job_result 整行覆盖，未来在 SK/属性引入 version）。

## 重议

- 若未来「编排进程外的写者」出现（远程 worker/task 自己直写 DDB，而非把事件流回传编排进程）——当前拓扑是 worker 把事件流回传、`schedule`+`RunPersistence` 始终在单个编排进程内、单写者；若改成 task 直写，则 `update_job_state` 进入真多写者，需 owner/lease + 条件更新，另立 ADR。
