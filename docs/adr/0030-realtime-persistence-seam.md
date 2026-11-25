# 实时写存储接缝：per-job 完成回调 + RunPersistence 应用服务 + RunStore 增量 port

> **Status:** Partially-superseded-by 0051 —— [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 4 以加法扩展改写决定二、三里 `on_event` 的触发事件与血缘规则：收到 origin 不是 `attempted` 的 `session_opened` 即把 job 刷成 RUNNING 并带 session_id，`scope_started` 到达时改写为执行会话的 id，任何写入（含终态写）都不以 None 覆盖已有的 session_id；接缝形态、写序、单一 store 锁不变。本 ADR「重议」条预告的「编排进程外的多写者 → 需 owner/lease + 条件更新、另立 ADR」已由 [0034](./0034-detached-batch-reconciler.md)（无状态批量运行，reconciler 直写 RunState）落地：`RunState` 的写带条件，不用租约（见下「重议」条反向链）。这一篇描述的设计有一部分尚未实装，code 跟上之前，实际行为以 code 为准。

把「一次 run 的判定/状态**随进度实时落库**」做成正交接缝：执行编排（`schedule`，[0026](./0026-schedule-module.md)）只管跑、
不碰存储；存储编排（新 `core/gherkai_core/persist.py` 的 `RunPersistence`）依赖 Store ports、由组合根注入具体 adapter。
这是云端（DDB/S3）落库的前置（见决定六）。

**定位**：本 ADR 解决「**怎么把实时落库接进来而不污染 reducer / 不让每个组合根各写一遍**」，以及落库按什么写序提交、状态以哪份记录为准（决定三）。
job 生命周期态（`skipped`/`aborted`/`pending`/`running`）的定义与 severity 归属、run 状态的取法与结束写全在 [0031](./0031-job-lifecycle-states-and-severity.md)（决定一、决定三），本篇只用它们描述时序；
DDB 的并发一致性（Map<scope_id> 按 key 定位、条件更新）见下「决定六」（云端 adapter 落库形态），重叠推进下各记录的先后见 [0034](./0034-detached-batch-reconciler.md) 机制三。

## 背景：v1.0 是「跑完一次性写」，零实时

v1.0 时（[0016](./0016-execution-architecture-core-lib-run-model.md) 三层切分）：`schedule` 跑完返回完整 `RunResult` →
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
| **C. 完成回调（采纳）** | `schedule` 加 `on_job_complete(JobResult)`，在主线程等待 job 完成的循环收到**已归约好**的 `jr` 时 fire | 复用 schedule 内部成品 JobResult、**零重复归约**；schedule 仍不知道 store/写序/失败编排；与现有 `sink` 同性质（都是回调、可注入 no-op） |

`on_job_complete` 是 [0026](./0026-schedule-module.md)「注入 sink、schedule 不决定结果存哪」原则从「跑完一次性」
**推广到 per-job 粒度**——同一条纪律，不是新范式。

### 回调的形态：`default=None` 是逃生舱，不是常态

```python
# core/gherkai_core/ports.py
class JobSink(Protocol):
    def __call__(self, job: JobResult) -> None: ...   # 收已归约的 JobResult（非原始 Event）

# core/gherkai_core/schedule.py —— 两个旁路注入点，都默认 None
def schedule(run_meta, engines, sink, opts=None,
             on_job_complete: JobSink | None = None,   # job 完成 fire 已归约 JobResult（主线程串行）
             on_event: Sink | None = None) -> Execution: ...  # 每事件 fire（sink_lock 之外，实时刷 RUNNING 用）；返回执行事实（ADR 0026「接口」）
```

- **`default=None` 的语义是「逃生舱」**：正常路径（产品 / 组合根）**永远接** persistence；只有「单测 / `--no-report` 显式弃权 / 纯内存实验」才不接。None 让纯 reducer 不被一个正交关注点绑死——`test_schedule.py` 用例、`--no-report` 路径都不必造 no-op 传进去。
- **不是 keyword-only**（普通参数 + 默认 None），但**调用点用关键字写** `on_job_complete=...`/`on_event=...` 保自说明。
- on_job_complete fire 在主线程等待 job 完成的循环（`wait(FIRST_COMPLETED)`）里串行；on_event 在 worker 线程、`sink_lock` **之外** fire（与 sink 分离，见决定三并发不变量）——两者写 store 都经 `RunPersistence` 的单一锁串行。得知 run 已被别处结束的那次存储操作（认领、重试之前的读、两种 job 状态写）与停手信号的发布在这把锁内完成，on_job_complete 在同一把锁内先看信号、再存明细：信号发布之后才取到锁的回调不再存明细（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）。没有启动的 job 不回调 on_job_complete，它们由结束写结束（[0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节）。

### 服从记录的三项能力：`ScheduleOpts.record`，不是给 schedule 注入 store

前台执行先认领再起 worker、重试之前读一次 run 级状态、发现 run 已被别处记为已结束就停手（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）。这三项要碰存储，仍不进 schedule：组合根把落库服务作为 `ScheduleOpts.record` 注入，schedule 只调用、只轮询。

```python
# core/gherkai_core/ports.py
class RunRecord(Protocol):
    def claim(self, scope_id: str, claimed_at: datetime) -> bool: ...  # 起 worker 之前认领；被拒 = run 已被别处结束
    def still_open(self) -> bool: ...                                  # 重试重新起 worker 之前读一次 run 级状态
    def ended_elsewhere(self) -> bool: ...                             # 停手信号：三处发现汇在这里，只读进程内标记
```

- **与方案 B 的区别**：schedule 拿到的是三个语义动作，不是 store；写序、几个 store、写失败怎么办仍全在 `RunPersistence`。认领时刻由 schedule 从注入的墙钟取、交给 `claim`，同一个值既写进记录、又算 job 的截止时刻。
- **放进 `opts` 而不另设参数**：三项要么一起有（有记录的执行）、要么一起没有（`--no-report`、单测），合成一个可为空的注入对象；与 `interrupt` 同类（组合根注入、schedule 轮询），已有两个回调的签名不变。
- **失败语义**：认领或读取本身失败（存储不可达）照常抛出，按运行期落库失败处理（与回调抛异常同一条止血路径，见决定三「回调异常的停机止血」）。

## 决定二：落库编排收进 `core/gherkai_core/persist.py` 的 `RunPersistence` 应用服务，组合根只注入 adapter

「实时写怎么落」（逐 job 的提交点、RUNNING 中间态、按 scope_id 增量刷 job 态）**对 cli / WebUI / 未来 cron 完全一致，只有注入的 store adapter 不同**。
让每个组合根各写一遍 → 必漂移。故收成一处 core 应用服务（依赖 Store **ports**、不含具体 adapter、不含 reducer 逻辑）：

```python
# core/gherkai_core/persist.py —— 编排 Store ports；不在 schedule 里、不碰执行 reducer
class RunPersistence:
    def __init__(self, run_id, run_store, result_store, report_store=None, *, clock=system_wall_clock): ...  # 结束时刻经 clock 取
    def begin(self, run_meta, *, started_at): ...        # create_run(meta, 初始全 PENDING 的 RunState)
    def claim(self, scope_id, claimed_at): ...            # RunRecord：try_claim_job 带认领时刻，记住它；被拒即发停手信号
    def still_open(self): ...                             # RunRecord：重试之前读一次 run 级状态；终态即发停手信号
    def ended_elsewhere(self): ...                        # RunRecord：停手信号
    def on_event(self, event): ...                        # 注入 schedule.on_event：收 ScopeStarted / SessionOpened→刷 RUNNING+血缘+认领时刻（sink_lock 外）
    def on_job_complete(self, jr): ...                    # 每 job：生成标识、先 save_job_result 存下这一份，再 commit_job_states 写该 job 终态并点名它（带认领时刻）
    def finalize(self, execution): ...                    # 有未结束的 job 时按 execution 交来的来路做结束写；本进程的写使 run 成为终态时，读一次运行态、
                                                          # 按其中点名的标识从判定存储读回各 job 的明细、组装 RunResult，从记录生成报告（ReportStore.write）；
                                                          # 返回 RunResult 与报告位置
```

- **`clock` 是组合根注入的墙钟**，可选、缺省取系统墙钟；组合根注入调度循环用的同一个读取点（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二「各执行方的落实」）。终态写与结束写要写下结束时刻（决定四「结束时刻由调用方给」条），而 `on_job_complete` 的签名里没有时刻，所以由落库服务自己经它取。
- **没有记录的执行（`run --no-report`）不经落库服务**：`persist.result_without_record(execution, ended_at=…)` 从全部 `pending` 的初始运行态出发，按终态写与结束写对运行态的作用（`run_status.commit_applied`、`ending_applied`，决定四「按模型使 job 成为终态的两个写入口」条）在内存里算出运行态，明细取本次的执行结果，经同一处组装成 RunResult（[0027](./0027-runreport-aggregation-index.md)「RunResult 的组装只有一处」条）；这条路径不存明细，终态也不点名。理由：内存路径与两个 adapter 用同一组作用函数，没有记录的执行与有记录的执行在同样的经过下得出同样的状态（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二「第 3、4 条的结果按同一套规则在内存里给出」，[0031](./0031-job-lifecycle-states-and-severity.md) 决定五「数据源」条）。

组合根（任意皮）就只剩注入 + 三调用，**逻辑零重复、只换 adapter**：

```python
persistence = RunPersistence(run_id, run_store, result_store, report_store, clock=compose.now)   # ← 唯一差异：哪套 adapter
persistence.begin(run_meta, started_at=now)
execution = schedule(run_meta, resolver, progress_sink, ScheduleOpts(..., wall_clock=compose.now, record=persistence),
                     on_job_complete=persistence.on_job_complete,   # job 完成落终态（主线程）
                     on_event=persistence.on_event)                 # 收 ScopeStarted / SessionOpened 刷 RUNNING（旁路观察者，sink_lock 外）
finalized = persistence.finalize(execution)   # 汇总、--json、退出码与报告都出自 finalized 里的 RunResult
```

> **注**：sink（进度显示）与 on_event（实时落 RUNNING）是**两个独立注入点**，persistence 不装饰 sink——
> 理由是并发不变量，见决定三「为何 RUNNING 走 on_event 而非装饰 sink」注。

**架构对位**：`schedule` 编排**执行**（Engine port），`RunPersistence` 编排**存储**（Store ports），两者平级、都在 core、由组合根组合。
schedule 仍一行不碰 store。这兑现「调 adapter 落库是默认行为、不是每个 client 自己拼」。

## 决定三：逐 job 的提交点：明细先存、终态写点名它，状态以运行态为准

落库按 job 逐个提交。由执行结果结束的 job 先存判定明细、再写终态，终态写在这个 job 的记录里点名那一份明细；run 的状态在同一次写里随之写下（取法见 [0031](./0031-job-lifecycle-states-and-severity.md) 决定三），run 一到终态，运行态的任何写都不成立（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）。run 要结束而仍有未结束的 job 时，由结束写结束（各来路见 [0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节）。job 与 run 的状态以运行态为准，判定明细对 scenario、step 与归因负责。前台执行者与后台推进同守这一写序；别处写它时引用本节，不另写概括。

实时写时序（一次前台 run）：

```
run 开始（schedule 之前）:
  RunPersistence.begin → RunStore.create_run(meta, 初始 RunState[所有 job=PENDING, run=PENDING, started_at=now])
       └ definition 先落，满足「提交即返回 runId」（[0027](./0027-runreport-aggregation-index.md)）
       └ 只在这个 run 还不存在时成立，已存在即抛 RunAlreadyExists、不改任何东西；本机在暂存目录上取生命期锁、
         写好两个文件，再原子改名成 run 标识（决定四）

每个 job 第一次起 worker 之前（RunRecord.claim；worker 线程，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）:
  RunStore.try_claim_job(run_id, scope_id, claimed_at=认领时刻)  ← 只在 run 未结束、job 仍 pending 时成立；认领时刻记在落库服务里
       └ 被拒 = run 已被别处结束 → 停手信号；job 不启动
  重试重新起 worker 之前（RunRecord.still_open）: RunStore.load_run_state → 读到终态同样发停手信号

job 进行中（on_event 收 ScopeStarted，或 origin 不是 attempted 的 SessionOpened（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 4 的加法扩展）；worker 线程、**sink_lock 之外**）:
  RunStore.update_job_state(run_id, JobState(scope_id, RUNNING, session_id, claimed_at))  ← RUNNING 中间态 + 血缘随首事件即落（session_id 按代表会话规则：scope_started 的值一经取到即锁定，此前取最近一条非 attempted 的 session_opened；任何写入都不以 None 覆盖已有值，终态写也守此规则）

每个由执行结果结束的 job（on_job_complete 串行 fire 已归约的 jr；jr 不是终态即抛，[0031](./0031-job-lifecycle-states-and-severity.md) 决定一·补的强制点）:
  （停手信号已成立 → 下面两步都不做：不存明细、不写终态，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）
  ① 生成一个随机标识，ResultStore.save_job_result 存下带这个标识的一份明细   ← 明细【先】存；失败见下「保存明细失败」
  ② RunStore.commit_job_states(run_id, [终态 JobState，带认领时刻与这个标识], ended_at=…)  ← 终态【后】写，并点名那一份明细

  （两种 job 态写都在同一次写里按 [0031](./0031-job-lifecycle-states-and-severity.md) 决定三的取法写 run 状态，库中已是终态的
   job 都不被它们改写；执行中的写整项替换，落库服务带上记住的认领时刻与代表会话，不让它们被抹掉；终态写与库中的条目按字段合并，
   会话与认领时刻不被空值覆盖；返回 run 已结束即 run 已被别处结束，发停手信号；终态写返回 ENDED_RUN 即本进程这次写使 run 成为
   终态，决定四）

run 结束（schedule 返回后，RunPersistence.finalize(execution)）:
  本进程的终态写已使 run 成为终态（返回 ENDED_RUN）→ 不再写
  否则仍有未结束的 job（到期、fail-fast 或使用方中断时没有启动的）→ 结束写，来路取 schedule 交来的那一条（Execution，
       [0026](./0026-schedule-module.md)「起 worker 与重试之前的检查」；说明表见 [0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节）
  使 run 成为终态的那次写是本进程写成的 → 读一次运行态，按其中点名的标识从判定存储读回各 job 的明细（下「点名」条的读法），
       组装 RunResult（汇总、--json、退出码与报告都出自它，[0027](./0027-runreport-aggregation-index.md)「RunResult 的组装只有一处」条）
       → ReportStore.write（生成方与时机见 [0027](./0027-runreport-aggregation-index.md)「ReportStore 接口：整 run 一次写」节）
       └ **ReportStore.write 的失败被隔离、不击穿已到终态的 run**
  （本次执行结束之前别处已把 run 结束：不覆盖、不生成报告，抛 RunAlreadyEnded，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）
```

> **ReportStore.write 失败隔离**：使 run 成为终态的那次写一落，各 job 的状态与被点名的明细都已在记录里；其后的
> ReportStore.write（派生只读视图）若抛异常（磁盘满等），**不冒泡、不反向击穿已到终态的 run**——finalize 吞掉它、
> 返回的报告位置为 None。否则一个派生视图写失败会让整个 run 裸 traceback 退出、CI 拿不到判定输出。终态写与结束写本身**不**在
> 隔离范围内（控制面没落是真问题，必须冒泡；run 已被别处结束时的 `RunAlreadyEnded` 同样冒泡，由调用方说明）。
> 为组装而读运行态与被点名明细的那一次同样不在隔离范围内：前台的输出与退出码取自它（[0031](./0031-job-lifecycle-states-and-severity.md) 决定五），
> 这次读失败（含被点名的那一份读不到，下「点名」条）按运行期落库失败处理（决定七）、不生成报告；后台推进与处置只为生成报告而读，
> 那一次在隔离之内（[0034](./0034-detached-batch-reconciler.md) 机制三④）。

**commit point 的意义**：由执行结果结束的 job，保存明细成功之后才写终态，所以读到这类 job 的终态时它点名的明细已在。依赖方：`explain` 与报告。执行方在存明细与写终态之间中断时，留下的那一份没被点名、不被读（下「点名」条）。由结束写结束的 job 没有执行结果，结束写不写明细、不点名（[0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节）；`explain` 怎样给出这类 job 见 [0042](./0042-step-evidence-and-explain.md) 决策四、决策七。

**状态的权威是运行态，输出里的状态就是记录里的状态**：`run` 的汇总与 `--json`、`status`、`list-runs`、`explain`、报告里 job 与 run 的状态都取运行态，不在读取时另派生；判定明细对 scenario、step 与归因负责，由执行结果结束的 job 的说明也在明细里。明细不是状态的来源与判定接口，给脚本读状态的入口是 `status --json`（[0041](./0041-agent-facing-cli-affordances.md) 决策三）。理由：job 的终态只在运行态里写一次，由结束写结束的 job 没有明细，明细的写又不带条件（下「点名」条），只有运行态对每个 job 都有且分出了先后。被拒：**读取时派生状态**（停在 `pending`、`running` 的 job 加说明另给一个状态）：输出与记录各一套，每个读者都要复刻同一条派生。

**点名：job 的终态点名它的那一份明细**。每次保存明细，写入方生成一个随机的标识，明细存成带这个标识的一份，同一个 job 可以有多份、互不覆盖，本机推进器对同一次保存的重试（下「保存明细失败」条）用同一个标识。记下 job 终态的那次条件写（条件见 [0034](./0034-detached-batch-reconciler.md) 机制三②）在这个 job 的记录里同时写下这个标识（`JobState.result_id`），即点名，点名随终态只写一次、此后的写原样保留；由结束写结束的 job 不点名。读者只认被点名的那一份：`explain`、报告与其余读回明细的各处都经同一处读法（下「读法」一项），先从运行态取 job 的清单与各自点名的标识，再读那一份，不列举目录或前缀；没被点名的明细不读、不列、不清理。`status --json` 怎样带这个标识、机器读结果的入口见 [0041](./0041-agent-facing-cli-affordances.md) 决策三；明细的落点本机见下「local 三个写面」框，S3 见决定六。理由：明细的写不带条件、可能有多份，只有记下终态的那次写分出了先后，由它点名，输出与记录一致就延伸到 scenario、step 与归因，明细的写也不必另带条件。代价：读明细的一方要先读运行态（跨用户的读者读不到运行态，分不出哪一份被点名，见下「读取权限」）；每个被点名的 job 条目多出标识的长度（约 25 字节），已计入一个 run 的 job 数上限的推算（[0025](./0025-plan-module-feature-to-jobs.md)「一个 run 的规模上限」；条目大小的实测见 [0034](./0034-detached-batch-reconciler.md) 机制三②）。

- **标识**：16 个小写十六进制字符（64 位随机数，`named_details.new_result_id`），一次保存一个，写入方在第一次保存之前生成：前台在 `on_job_complete` 里看过停手信号之后，后台在推进步骤第 3 步为每个已有结果的 job 各生成一个（[0034](./0034-detached-batch-reconciler.md) 机制三「收尾各步的先后与之后会不会变」）。理由：标识只需在同一个 run 的各次保存之间不重复（键里已有 run_id），64 位在单个 run 的保存次数下碰撞的概率可以忽略（10⁵ 次以内约 10⁻¹⁰）；标识的长度计入每个被点名的 job 条目（上「点名」条的代价），越短，一个 run 的 job 数上限之内的余量越大；只用小写十六进制，是因为本机文件名可能落在不区分大小写的文件系统上（macOS 默认的 APFS 即如此），大小写不同的两个标识会落成同一个文件。被拒：**标识里编码 scope_id 或时刻**：读者从运行态取 scope，标识只需唯一；**128 位**（32 个字符，`uuid4().hex` 的惯例）：唯一性只需在一个 run 之内，多出的 16 字节只让每个条目变大、上限之内的余量变小。
- **端口**：`ResultStore` 只有 `save_job_result(run_id, result_id, job)`（存下带这个标识的一份，原子写，不带条件；同一个标识再存一次即覆盖，只发生在同一次保存的重试上，内容相同）、`load_job_result(run_id, result_id) -> JobResult | None`（这个标识下没有明细时为 None）与 `preflight()`，不提供列举。理由同决定四「端口上有的方法生产 code 就能调」：列举入口在端口上，读者就能绕过点名去读没被采用的明细。明细的内容里不写标识，键本身就是标识。
- **读法**：读者共用一处（`named_details.load_named_details`）：只读运行态里带标识的 job，按标识取那一份，读回之后核对它的 scope_id 与运行态里这个 job 的相同；分辨由执行结果结束与由结束写结束只看这个 job 有没有标识，不看说明、不看存储里有没有明细。这一分辨成立，是因为有记录的执行里每个由执行结果结束的 job 都被点名：前台落库服务与推进步骤都必带判定存储，终态写总带上这次保存的标识；只有没有记录的执行（`run --no-report`，决定二）在内存里写下不点名的终态，那里不读明细、直接用执行结果。前台收尾同样按标识读回（上时序块「run 结束」一段，理由见 [0027](./0027-runreport-aggregation-index.md)「RunResult 的组装只有一处」条），后台报告与 `explain` 也经这一处。被点名而读不到（这个标识下没有明细，或读到的那一份不属于这个 job）按记录残缺处理，不当作没有明细：前台按决定七运行期落库失败里「记录已是终态」的那一种说明结束，后台的报告在失败隔离之内不生成，`explain` 以退出码 2 结束并说明那一份读不到（[0042](./0042-step-evidence-and-explain.md) 决策四「退出码」段）。理由：正常写序下被点名的那一份必已存下、属于这个 job，读不到或对不上只会是存放处或运行态被绕过端口改动；当作没有明细会把由执行结果结束的 job 显示成由结束写结束的样子，照常附上会把别的 job 的结果当成这个 job 的判定。内容不是完整的 JSON 时不另兜，照常抛出（[0042](./0042-step-evidence-and-explain.md) 决策四「数据来源」段末的「有意不加兜底」）。运行态被改成指向同一个 job 的另一份时不识别：这只能出自绕过端口的改动，与 [0034](./0034-detached-batch-reconciler.md) K1 的前提相同。

- 被拒：**接受明细与终态不对应**（明细每个 job 一份、后写的覆盖先写的）：由执行结果结束的 job，只在云端重叠时 `explain` 与报告配的明细可能出自没写成终态的那一次；由结束写结束的 job，残留明细里的 scenario 与 step 照样当作它的判定列出（如 `aborted` 配全部通过的 step），而不是标为取自事件流。
- 被拒：**为由结束写结束的 job 补写明细**（写成结束写的一方补写一份只有状态与说明的明细）：补写在结束写之后，run 已是终态、运行态的任何写都不成立（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五），这份明细无从被点名，读者不认。

**被点名的那一份就是写成终态的那一方存的**：job 的终态至多写成一次（[0031](./0031-job-lifecycle-states-and-severity.md) 决定一·补），写成的一方点名的是自己存下的那一份，与终态出自同一个执行结果（写不成而重读再算时沿用这一份，改用别的结果先另存一份）；云端两次调用重叠、本机期限加 300 秒的 run 处置抢先、推进器恢复之后迟落下的保存，都只多出没被点名的明细（执行方得知 run 已结束之后不存明细，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）。依赖方：`explain` 与报告不把没被采用的结果当成结果展示。由此**报告里的判定由记录确定**：run 到终态之后运行态与被点名的明细都不变，报告里的状态、scenario、step 与归因不随生成的时机变化。依赖方：只由一方生成一次的报告（[0027](./0027-runreport-aggregation-index.md)「ReportStore 接口：整 run 一次写」节）与 `status`、`explain` 一致。

**保存明细失败**：保存失败时这个 job 这次不写终态。云端由流的重试或之后的触发再做；本机两种推进器（前台的 `run` 进程与后台推进进程）按指数退避重试 3 次（间隔 1、2、4 秒，同一个标识），仍失败即放弃，推进器退出（前台 `run` 走决定七「失败退出码分层」里运行期落库失败的出口；后台推进进程在它的日志里留一句产品语言的说明（发生了什么、记录在哪里），不打回溯，以非零退出码结束；两者的说明都给出把这个 run 记为已结束的 `settle-runs` 整条命令，再请使用者重新执行或重新提交，见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策八「管它的进程退出而 run 未结束的出口」一条），执行中的 job（含同一轮已存下明细的）留在 `running`，run 被处置时记为「执行这个 run 的 gherkai 进程已退出」那一句（说明表在 [0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节，处置见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策七）：描述属实，只是没有说明为什么退出（前台终端里另有存储错误），结果丢失。一时的失败（重试成功之前没有被处置）照常记下，三种组合相同（[0054](./0054-run-deadline-lifetime-lock-and-settling.md)「边界与已知局限」的「三种组合的对照」表）。

- **重试的层与形态**：重试由本机推进器的组合根装配：本机的判定存储外面套一层退避重试（`adapters.result_store.retrying.RetryingResultStore`，装配入口 `compose.local_result_store`），云端的组合根不套，推进步骤与落库服务本身没有等待。只对 `OSError` 重试（本机文件存储的写入失败都表现为 `OSError`），别的异常是 code 的缺陷，原样抛出。首次保存失败之后依次等 1、2、4 秒各再保存一次，共四次尝试，每次重试之前在日志里留一句产品语言的警告，第四次仍失败即原样抛出、由推进器的出口说明交代那个异常。标识由调用方给出，四次都用它，后一次覆盖前一次写下的同名文件，「同一次保存的重试用同一个标识」由签名本身保证。被拒：**放进推进步骤或 S3 adapter**：两者都由云端共用，云端的再做靠流的重试或之后的触发，进程内的等待在那里关不掉；**给推进步骤与落库服务各注入一份重试策略**：两个调用方各有一个重试循环，云端共用的推进步骤上多出一个只有本机才传的参数。
- **前台在锁内重试**：前台的保存连同重试都在落库服务的进程内锁里进行（下「两条写 RunStore 的路径」注）：停手信号的发布与「先看信号、再存明细」仍在同一把锁内，得知 run 已结束之后不存明细（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）照旧成立。代价：重试期间别的 worker 线程的认领与执行中的写、调度循环对期限与中断的处置都要等重试结束。重试写成时它们推迟最多约 7 秒：被锁挡住的 job 的认领时刻在取锁之前已经取好，它的预算因此少拿最多约 7 秒；第二次中断的「立即强制结束」同样推迟。重试用尽时保存失败的异常经下「回调异常的停机止血」注冒出 schedule，执行中的 worker 照样被停下，而重试期间到达的中断不再被处置：不打中断提示，退出码按决定七「失败退出码分层」里运行期落库失败的出口取、不按信号取（[0031](./0031-job-lifecycle-states-and-severity.md) 决定五只在中断处理过时按信号取）。这些只在判定存储写不进时出现。被拒：**在锁外重试**：削弱「得知之后不存明细」，还要另加一次锁内复查。
- 被拒：**保存明细失败时一直重试**（直到写成，或 run 被处置、推进器读到终态停手）：存储一直写不进时不保证 run 结束：执行中的 job 留在 `running`（执行方自己到期的条件因此不成立，见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二第 3 条），推进器仍持锁（前台即 `run` 不退出），只剩期限加 300 秒的 run 处置（条件见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策六；磁盘满时它的写同样写不进），而本机没有常驻的处置方（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策八）。
- 被拒：**保存明细失败即退出、不重试**：一次临时的写入失败就丢掉已经得出的结果（重试用完之后的情形），云端同一情形由流的重试记下真实结果。

**后台推进同守**（[0034](./0034-detached-batch-reconciler.md)）：本机后台推进进程与云端 Lambda 同样逐 job 先存明细、再写终态并点名（一次写可记多个 job，各点名各自的一份），明细与终态出自这一轮读到的同一份事件快照（本机的快照不变量见 0034 local 一节）。后台的结束写只在它的来路成立时做（本机后台推进进程只有执行方自己到期一条，云端推进器另有运行定义不可用，[0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节），报告的生成方与前台相同（[0027](./0027-runreport-aggregation-index.md)）。明细写在终态之前还因为：终态之前的失败让这个 job 这次不写终态，云端由流的重试或之后的触发再做，本机按上「保存明细失败」条处理；终态之后的失败无人重试——job 的终态只写一次，此后到达的结果不被采用（[0031](./0031-job-lifecycle-states-and-severity.md) 决定一·补），缺的明细就永久缺失。

> **两条写 RunStore 的路径并发写同一个 run**（实装关键）：认领与 RUNNING 中间态刷在 **worker 线程**（认领在起 worker 之前；RUNNING 经 `on_event`，在
> `sink_lock` **之外**调）；job 终态刷在 **主线程**（经 on_job_complete，在主线程等待 job 完成的循环里串行），结束写在 schedule 返回之后。这是**两个不同
> 线程**写同一个 RunStore；local adapter 的写是「读 run_state→改→写回」的整文件 read-modify-write，两次读改写不互斥就会互相覆盖、丢更新。
> **不变量：RunStore 的每个写入口对并发的别的写入方都是安全的，正确性不靠调用方串行**（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五：
> run 到终态之后运行态的任何写都不成立，端口不假定同一个 run 只有一个写入方）。local adapter 建 run 之后的各写入口（`update_job_state`、
> `commit_job_states`、`try_claim_job`、`project_state`、结束写 `end_run`；结束写的 error 变体只在 DDB adapter 上，决定四）在 run 目录下同一把 `flock` 短锁（`.runstate.lock`）内读改写，按锁内读到的整份运行态计算，跨进程与进程内多线程都互斥；
> `create_run` 不取这把短锁，建 run 的互斥由暂存目录与改名给出（决定四）。
> 这把短锁同样要求报告目录在本机文件系统上（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策四）。DDB adapter 的每一次写都带条件（决定六；重叠推进下各写的条件见
> [0034](./0034-detached-batch-reconciler.md) 机制三）。这不是事务保证：云端的 `create_run` 依次写 jobs 对象、提交记录的头与运行态（决定六「云端提交记录」条），DDB 的
> `project_state` 先写标量、再逐 job 写；中间态对读的一方可见，中途失败时已写成的部分留在库里。本机的 `create_run` 先把两个文件写进暂存目录，
> 写完才原子改名成 run 标识，列举与按标识的读写都不认以点开头的名字（决定四）；中途写失败即删去暂存目录，进程被强杀时暂存目录留在原处
> （掉电与内核崩溃不在其内，见下「两条被接受的代价」①）。
> `RunPersistence` 另持一把进程内锁，认领、on_event 与 on_job_complete 路径都走它，
> 用处是护住进程内记下的代表会话与认领时刻（`_session`、`_claimed_at`，读改写跨线程），并让同一进程里的写按调用次序依次落库；
> 停手信号是线程安全的事件标志，读它不取锁。
>
> **为何 RUNNING 走 on_event 而非装饰 sink**：sink 被 schedule 的 `sink_lock` 串行化（保进度显示有序）。若让 persistence
> 装饰 sink，RUNNING 的整文件磁盘 RMW 会被串进 `sink_lock` 临界区——一个 worker 刷 RUNNING 期间，全体 worker 的进度
> 显示都堵在 `sink_lock` 后。故 schedule 另开一个 `on_event` 旁路观察者、在 `sink_lock` 之外 fire；落库的互斥由 store 写入口
> 自身与 `RunPersistence` 的锁保证，与进度显示解耦。
>
> **进程内锁只护一个进程**：本机的 run 任何时刻至多一个推进器（[0034](./0034-detached-batch-reconciler.md)「推进器与触发源」），跨进程的互斥靠上面的文件锁；云端允许多次 Lambda 调用重叠推进同一个 run（DDB Stream 按 PK 分片触发多实例，实测并发度 2），进程内锁对它们不起作用，重叠下各写的先后由条件写给出（[0034](./0034-detached-batch-reconciler.md) 机制三）。这是本 ADR「重议」条预告的落地（见下）。

> **回调异常的停机止血**（实装关键）：on_job_complete 在主线程 fire，若它抛异常（如落库磁盘满，保存明细按上「保存明细失败」重试用尽之后），schedule **在异常
> 冒泡前先 stop 所有在跑 worker**（`_stop_all()`：置 `abort_flag`，先对在跑 worker 全部落定停止原因，再各起线程并行发停止请求）再重抛。否则异常跳出 `with ThreadPoolExecutor`，
> `shutdown(wait=True)` 会等所有在跑 worker 自然跑完——真 AgentCore 会话持续计费。异常仍冒泡（落库失败=真问题、要暴露），
> 只是先掐掉在跑会话。
> `on_event` 的运行期异常走同一条止血路径、不产生判定：它在 worker 线程里抛出时，该 worker 不调终结函数（以免把落库失败归因成
> `engine_error` 写进结果），先停掉本 worker 再原样重抛；异常在主线程取该 job 结果（`future.result()`）时再次抛出，与 on_job_complete
> 共用同一个 `except BaseException`，同样先 `_stop_all()` 再重抛。

> **写序的失败语义**：保存明细成功而写终态失败时，这个 job 没有终态，存下的那一份没被点名、不被读（上「点名」条）；写终态的失败照常抛出，
> 按上「回调异常的停机止血」先停掉在跑的 worker。运行态是 job 与 run 状态的权威，不能由明细或事件重建：被采用的结果只有写进运行态的终态
> （[0031](./0031-job-lifecycle-states-and-severity.md) 决定一·补），明细只认被点名的那一份，由结束写结束的 job 没有明细。
> 真事务（DDB `TransactWriteItems`）**不用**——规模化跑批会撞它的 100 项/4MB 上限，逐 job 的提交点把原子性需求降到 DDB 天然原子的单 item：
> 明细的写不带条件，用哪一份由终态写点名。

> **local 三个写面一律原子写**（同目录 tmp + `os.replace`，共享助手 `core/gherkai_core/adapters/_atomic.py`）：
> 控制面 `run_meta.json` / `run_state.json`、数据面判定明细（`jobs/` 下各文件）、报告面 `manifest.json` + `index.html`。
> 三面各有**设计内的**跨进程并发读者（无锁读 run_state 的 `status`、`list-runs` 与处置方；run 跑到一半读已完成 job 的
> `explain`，[0042](./0042-step-evidence-and-explain.md) 决策四；报告写成后即读它的人/CI），
> 而 `write_text` 是 truncate 再写——两步之间的读者会拿到空文件或前半截、`json.loads` 直接炸。
> **本机判定明细的落点**：`<report-dir>/<run_id>/jobs/<result_id>.json`，每次保存一个文件，标识按不透明标识符的惯例编码成一段
> （`quote(result_id, safe="")`，生成的十六进制标识编码后不变），文件名里不带 scope_id（上「点名」条）；它的存放形态对使用者不是约定
> （[0041](./0041-agent-facing-cli-affordances.md) 决策三），判定明细在 run 位置之内的键归 run 记录格式版本（[0037](./0037-distribution-and-packaging.md) 决策 7）。理由：读者按运行态里的标识取，不需要从文件名认出 scope；文件名长度与 scope_id 无关，
> 长 scope_id（编码后超过 250 个字符，例如 28 个以上汉字的 `@scope` 值）不会因文件名过长而保存失败。被拒：**编码后的 scope_id 再接标识**：
> 长度随 scope_id 增长，比只用 scope_id 更早撞上文件名的长度上限。
> 权限**按面显式声明、不随环境 umask 漂移**：控制面 0600（只本机同 uid 的进程消费），数据面与报告 0644
> （消费者是 CI / 人 / 静态 server，产物可读性是契约的一部分）。
> **读取权限**：`status` 先读提交记录的头、核这个 run 的记录格式版本（[0037](./0037-distribution-and-packaging.md) 决策 7），本机运行定义（含隧道访问令牌，
> [0035](./0035-local-app-testing-via-tunnel.md) 决策 5、[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 13）与运行态都是 `0600`、明细是 `0644`，
> 所以以别的用户身份读报告目录的 CI 只能以同一用户执行 `status --json`，放宽要连运行定义一起、令牌随之可读。云端要有 runs 表的读权限：令牌与额外请求头在提交记录的头里，同在这张表上；产物桶里的 jobs 对象不带它们（决定六「云端提交记录」条）。
> **两条被接受的代价**：① **不做 fsync**——本层防的是并发读者看到中间态，不是掉电后的持久性（那要 fsync
> 文件 + 目录，成本进每一次写）；② **写面无跨进程互斥**——靠原子替换而非锁：明细每次保存是带标识的另一个文件，
> 同一个 job 的多份互不覆盖、用哪一份由终态点名（上「点名」条）；报告只由使 run 成为终态的那次写的写入方写一次
> （[0027](./0027-runreport-aggregation-index.md)），它写在终态之后，原子替换让读到终态即去读报告的读者不会读到写了一半的文件。文件锁只护控制面：建 run 之后
> `run_state.json` 的每一次读改写（建 run 之后的各写入口，见上并发不变量）；建 run 时 `run_meta.json`、`run_state.json` 写在暂存目录里，
> 互斥由暂存目录与改名给出（决定四）。

**实测项**（实装时以真实进程或环境核）：

1. 保存失败：本机两种推进器各注入一次明细写入失败，重试之后照常记下、点名的是重试所用的标识、进程不退出；一直注入失败时重试 3 次之后进程退出，执行中的 job 留在 `running`，`status --wait` 按说明表（[0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节）「锁拿到了」一行处置。
2. 点名：云端两次调用重叠、各存一份同一个 job 的明细时，`explain` 与报告取到的是写成终态那一方的；本机两种推进器各在存下明细之后、写下终态之前被 SIGKILL，随后被处置时，`explain` 与报告不出现那份明细，`explain` 从事件流补取已执行的 step。
3. 报告目录的路径长度（决定四「报告目录的路径长度」条）：解析之后恰好 470 字节的报告目录上，经命令的 `run` 与本机 `submit` 走通，事件库与报告都写成；471 字节、一层 256 个单字节字符的名字（含它位于一层还不存在的上级之下）时，`run`、`submit`、`status`、`explain`、`list-runs`、`settle-runs` 都以退出码 2 与对应的一句结束、不建任何目录、没有回溯；经符号链接指定的报告目录按解析之后的长度判断；一层 100 个汉字（300 字节）的名字在 macOS 的 APFS 上放行、在 Linux 的 `ext4` 上被拒（macOS 与 Linux 各一次）。Linux 上 uv 装的 Python 与发行版自带的 Python 各打开 504、505 字节的库文件路径（WAL 与回滚日志两种）。报告目录取 470 字节附近时，真实的两个引擎（含设备目标）在产物子目录之下的证据、轨迹与报告都写成，报告里的链接完整。
    - 已核：macOS 的 APFS 上 470 字节时经命令的 `run` 与本机 `submit` 走通（事件库路径 504 字节）；471 字节、一层 256 字节的名字（含位于还不存在的上级之下）时各命令都以退出码 2 与对应的一句结束、不建目录、没有回溯；经符号链接指定、解析之后超长的被拒；一层 100 个汉字的名字在 APFS 上放行，在 Linux 的 `ext4` 上 `status` 与 `run` 以一层名字太长的那一句被拒。Linux 上 470 字节时真实的 Nova 引擎（确定性步骤与 AI 步骤各一次）与本机 `submit` 走通，事件库路径 504 字节，证据与轨迹写成（产物子目录之下最长的路径比报告目录长 187 字节），报告里的相对链接都指向存在的文件；471 字节的 `run` 与 472 字节的本机 `submit` 被拒。库文件路径 504 字节能打开、505 字节不能：Linux 上 uv 装的 Python 3.13（SQLite 3.50.4）与发行版自带的 Python 3.12（SQLite 3.45.1），WAL 与回滚日志两种都是。
    - 尚未核：Midscene 引擎与设备目标在 470 字节附近。

## 决定四：RunStore 按生命周期分写入口：建 run、逐 job（执行中与终态）、结束写

```python
class RunStore(Protocol):
    # —— 生命周期写入口 ——
    def create_run(self, meta: RunMeta, initial_state: RunState) -> None: ...      # run 开始：写 definition + 初始全 PENDING 态；只在 run 不存在时成立，已存在抛 RunAlreadyExists、不改任何东西
    def update_job_state(self, run_id: str, job_state: JobState) -> bool: ...       # 单 job 执行中的写（按 scope_id 定位）：认领之后的 running 与血缘；run 已结束时写不成；返回 run 在这次写时是否仍未结束
    def commit_job_states(self, run_id: str, job_states: Sequence[JobState], *,
                          ended_at: str) -> CommitOutcome: ...                      # 带结果的 job 终态写：一次写可记多个 job（终态带点名的标识）；终态只写一次；同一次写按取法写 run 状态；返回 OPEN / ENDED_RUN / ALREADY_ENDED
    def end_run(self, run_id: str, ending: RunEnding, *, ended_at: str) -> bool: ... # 按本格式的模型算出的结束写（语义见 0031 决定三「结束写」小节）：只在 run 未结束时写成，返回是否写成
    # 结束写的 error 变体不在端口上：它是 DDB adapter 上的另一个结束写入口，只写运行态的公共部分（下「error 变体是另一个写入口」条）
    def load_run_meta(...); def load_run_state(...)                                 # 读回
```

**接口真值以 `core/gherkai_core/ports.py` 为准**——上块只列生命周期写入口与读回，不是 `RunStore` 的完整现状：另有 `preflight`（探活，见下决定七）、认领 `try_claim_job`（后台推进与前台执行共用，前台经 `RunPersistence.claim`，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）与后台推进用的投影 `project_state`（两者的条件见 [0034](./0034-detached-batch-reconciler.md) 机制三）、只取 run 记录格式版本、写端版本与期限的 `peek_definition_header`（[0037](./0037-distribution-and-packaging.md) 决策 7），以及按状态列出 run、每项返回 `RunListing` 的只读 `list_runs`（[0041](./0041-agent-facing-cli-affordances.md) 决策七）。`commit_job_states` 由前台执行者与后台推进共用；`end_run` 由前台执行者、后台推进与处置方共用：前台在 schedule 返回后仍有未结束的 job 时做（决定三），各来路见 [0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节；run 级说明（结束的原因）随它写下。error 变体的入口不在端口上，只在 DDB adapter 上、只由云端推进器调用（下「error 变体是另一个写入口」条）。运行态里的认领计数只作诊断键（[0034](./0034-detached-batch-reconciler.md) 机制三「run 级状态只进不退」条①）；云端记下 job 终态的写与结束写以写入序号为条件（[0034](./0034-detached-batch-reconciler.md) 机制三②，属性见决定六）。

- **端口不提供整份重写与无条件改写终态的入口**：一次性写完整态的入口对已有的 run 再调用即回到初始状态或任意状态，无条件写终态的入口覆盖已有的终态，两者都与 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五的终态不可变不相容。测试需要的初始状态经 `create_run` 加各条件写得到。被拒：在端口上提供它们作测试便捷方法——端口上有的方法生产 code 就能调，终态不可变就只剩调用约定在守。
- `create_run` 只在这个 run 还不存在时成立（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）。local adapter 先在报告目录里建一个暂存目录（名字是 `.gherkai-creating-` 加 16 个小写十六进制字符的随机尾，清理方按同一形态认它，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策三；这一命名形态属跨版本不变的约定，[0037](./0037-distribution-and-packaging.md) 决策 7），以只读方式打开它、在这次打开上取生命期锁（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策三），把 `run_meta.json`、`run_state.json` 写进去，写完才把它原子改名成 run 标识；两处边界检查（对报告目录、对暂存目录的描述符）、锁不可用与暂存目录被别的进程持有时怎样做，见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策三、决策四。写两个文件失败时删去暂存目录，按写记录失败原样报出。改名的目标已是非空目录（`ENOTEMPTY` 或 `EEXIST`）即抛 `RunAlreadyExists`，删去暂存目录、不改任何东西；目标是文件、符号链接或挂载点时改名以别的错误失败（实测：文件与符号链接在 macOS 与 Linux 上都是 `ENOTDIR`，挂载点在 macOS 上是 `EXDEV`、在 Linux 上是 `EBUSY`），按写记录失败原样报出（错误码不变，文件名换成 run 目录的路径），暂存目录同样删去（各处失败时删去暂存目录都是尽力而为，删不掉的留给清理方，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策三「删去自己的暂存目录只凭自己那次打开」一条）；目标是空目录时被替换，这是 POSIX `rename` 的语义，空目录不带记录，不另防。建 run 不取运行态的短锁：按 run 标识读写的各入口不认以点开头的名字（下「run 标识即 run 目录的名字」条），碰不到暂存目录，「已存在」只由改名给出。「这个 run 已存在」两个 adapter 都只以专门的异常 `RunAlreadyExists`（`FileExistsError` 的子类）报出，调用方只按这个类型判断，不按 `FileExistsError` 或别的 `OSError` 一概而论：改名的目标被文件、符号链接或挂载点占着是写记录失败、不是 run 已存在，两者对使用者的处理办法不同（决定七「失败退出码分层」）。DDB adapter 见决定六。
  - **run 标识即 run 目录的名字**：local adapter 拒绝空的、以点开头的、含路径分隔符的、按文件系统编码超过 255 字节的标识（`ValueError`，什么都不建），以点开头的名字留给暂存目录（属跨版本不变的约定，[0037](./0037-distribution-and-packaging.md) 决策 7）；长度取 255 字节：Linux 清单里的类型以 255 字节为限，APFS 以 255 个 UTF-16 代码单元为限（实测 APFS：255 个汉字（765 字节）的一层建得出、256 个建不出，127 个 emoji 建得出、128 个建不出，256 个单字节字符的得到「文件名太长」）；一个字符的 UTF-8 字节数不少于它的 UTF-16 代码单元数，所以 255 字节之内的名字在两个平台上都建得出，两个平台认同一组标识；按标识读写的各入口收到不合规则的标识，按 run 不存在处理；列举跳过名字以点开头的目录（[0041](./0041-agent-facing-cli-affordances.md) 决策七「本机实现」）。读写两侧用同一条名字规则；生成 run 标识的一方不产出以点开头的标识（[0027](./0027-runreport-aggregation-index.md)「run_id：归集索引的主键」节）。
  - **报告目录的路径长度**：本机后端的报告目录按解析之后的绝对路径（解析其中的符号链接，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策四「边界检查」一条）判断两项，任一不过即在入口以一句说明、退出码 2 结束，什么都不建，不做让超长路径也能用的处理。①总长：按文件系统编码不超过 `compose.REPORT_DIR_MAX_BYTES` 字节（现值 470，推导见下），只看字符串。②每一层名字不另定字节数，由文件系统回答：入口先找到报告目录最近一层已存在的上级（沿路径向上，越过打开时得到「不存在」与「名字太长」的各层：超长的一层紧接在已存在的上级之下时，打开整条路径得到的就是「名字太长」；向上找时遇到别的打开失败即放行，交给随后各步按各自的说法报出），再对它之下每一层还不存在的名字各问一次：把这一层名字直接接在那个上级之下查这个名字本身（不跟随符号链接），系统答「名字太长」（`ENAMETOOLONG`）即拒绝、不按写记录失败报出，别的回答（「不存在」、恰好已有同名的条目）都说明这一层的名字可用。不跟随符号链接，是因为那个上级之下恰好同名的条目与报告目录无关：它是指向超长名字的符号链接时，跟随之后得到的「名字太长」说的是链接的目标（实测这样的报告目录被误拒）。还不存在的各层建出来时与那个上级在同一个文件系统上，所以问到的就是它们将来的回答，这一问什么都不建；只打开整条路径不够，内核逐层查找，遇到第一层不存在的名字即答「不存在」，看不到它后面更长的那一层（实测 macOS 的 APFS）。总长已在内核的整条路径上限之内，这一回答只会出自某一层名字。两项的说明分开（路径太长；路径里有一层名字太长），都写明出了什么问题与怎么办（换一个路径较短的报告目录，经选项或配置文件给出）。先核①、再做②。生效的命令：`run`（生成记录时）与本机 `submit` 在前置检查里、判断报告目录所在的文件系统之前（超长路径的打开会得到「名字太长」，不先查就会按边界检查里「别的打开失败」报成写记录失败）；本机的 `status`（含 `--wait`）、`explain`、`list-runs`、`settle-runs` 在第一次访问报告目录之前。云端后端（报告落点是键前缀，不是路径）与 `run --no-report` 不查；后台推进进程收到的是提交进程已检查过的同一个路径，不再查。
    - **总长的上限怎样推出**：取报告目录之下产品构造的最长路径，对各项上限里最紧的一项推出（R 为报告目录的字节数，产品生成的 run 标识 23 字节）。内核的整条路径：macOS 为 1023 字节（`PATH_MAX` 1024 含结尾的空字符），Linux 为 4095 字节；最长的是判定明细的临时文件 `/<run_id>/jobs/<16 位标识>.json.<8 位随机串>.tmp`（1+23+6+16+6+8+4，共 64 字节；暂存目录里运行态的临时文件 63 字节，其余更短），要求 R 不超过 959（macOS）、4031（Linux）。SQLite 按缺省构建时库文件路径的上限是 504 字节（`adapters.event_log.sqlite.DB_PATH_MAX_BYTES`；`-journal`、`-wal`、`-shm` 文件由 SQLite 在它自己的上限里核），事件库 `/<run_id>/events.db` 共 34 字节，要求 R 不超过 470。最紧的是 SQLite 这一项，上限因此是 504 − 34，两个平台同一个数；code 由生成的 run 标识的长度与事件库的文件名算出它，标识的形态变了上限随之变，测试守住它与内核上限的关系。前提：所用 Python 链接的 SQLite 按缺省构建、库文件路径上限不小于 504 字节；上限随构建而变（macOS 系统自带的 SQLite 3.54.0 在 520 字节时仍能打开），不满足前提时 470 字节之内的报告目录上也可能打不开事件库。实测（macOS 的 APFS，经库调用、用真实的 SQLite）：R 为 470 时建 run、事件库（WAL）、判定明细与结束写都写成；471 时事件库打不开（库文件路径 505 字节）；960 时判定明细的临时文件得到「文件名太长」（1024 字节）；961 时建 run 失败。库文件路径 504 字节能打开、505 字节不能，uv 装的 Python 3.13（SQLite 3.53.1）与 Homebrew 的 Python 3.15（SQLite 3.54.1）相同；经相对路径、经符号链接（链接路径 47 字节、真实路径 505 字节）同样打不开，即 SQLite 按解析之后的真实路径计，所以总长按解析之后的路径算。
    - **保证到哪里**：通过检查的报告目录之下，产品为它生成的 run 构造的路径（暂存目录、run 目录、两个记录文件与短锁、事件库、判定明细、报告、`reconcile.log`、`worker.log`、两个产物子目录本身与交给 worker 的路径）都在上限之内；按使用者给出、合名字规则的标识（至多 255 字节）读写记录与报告，路径至多 754 字节，也在内核上限之内，事件库只为产品生成的标识建。产物子目录之下由 worker 与引擎建的路径不在保证之内：gherkai 的 worker 的证据路径按场景键截断，最长约 141 字节；Nova SDK 的文件名带指令的前 30 个字符，估计最长约 232 字节；Midscene SDK 的报告名可由环境变量改。R 不超过 470 时，产物子目录之下 macOS 约余 510 字节、Linux 约余 3500 字节，现有命名放得下；超出时的表现由引擎决定（Nova SDK 建会话目录失败只记日志、不写那一份产物）。手工建在报告目录里的长名目录属于有人改动报告目录，不在其内。
    - 被拒：**每一层名字按 255 字节判**（与 run 标识的名字规则相同）：APFS 的上限按 UTF-16 代码单元计，一层 100 个汉字（300 字节）的目录在 macOS 上建得出、总长也远在上限之内，按字节判会拒掉能用的报告目录；run 标识是产品生成、两个平台要认同一组的名字，适合按字节定规则，报告目录是使用者已有的路径，由文件系统回答才不多拒。**按平台取内核的路径上限**：SQLite 的上限在两个平台上都更紧，单靠内核上限，R 在 471 到 959（macOS）之间仍会在事件库上失败。**让超长路径也能用的特殊处理**（事件库改经相对路径或目录描述符打开）：SQLite 按解析之后的真实路径计长度，相对路径实测同样打不开，要绕开就得改动进程的当前目录或 SQLite 的文件系统层，为远超常见长度的报告目录在每一次打开事件库时多一层机制。**不检查，让系统错误照常报出**：超长的报告目录上各命令给出的说明都说不出真实原因：`run` 在 R 为 471 到 959 时建成记录之后停在 `pending` 并请使用者检查读写权限；`list-runs` 请使用者检查目录权限，`explain` 把事件库打不开说成事件流读取失败，`status` 打出回溯。
  - **持锁的描述符交给注入的持有者**：改名之后，持锁的描述符交给构造 local adapter 时注入的持有者；生产用的持有者不关闭它、也不交出它，锁随进程退出释放。只有推进这个 run 的进程（前台 `run`、本机后台推进进程）构造带持有者的 store；不带持有者的 store 调 `create_run` 即报错（编程错误，什么都不建），只读命令的 store 因此不能建 run。理由：「调用 `create_run` 的进程即持锁者、持有到进程退出」由构造参数写明，不是调用的隐式副作用，与 [0016](./0016-execution-architecture-core-lib-run-model.md)「选实现 = 组合根注入」条的「无隐藏全局」同一取向。
  - **理由**：取锁、写两个文件都在暂存目录上做，写完才改名，所以以 run 标识命名的目录出现时，建它的进程已持有锁；处置的一方只对以 run 标识命名的目录试拿锁（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策三），先改名、后取锁时它会在两步之间拿到锁，把正在建立的 run 当作推进器已退出。建 run 中途进程被强杀时，留在原处的是按名字认得出的暂存目录（掉电与内核崩溃不在其内，见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md)「边界与已知局限」），清理它的一方按名字认出、先取锁再删（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策三、决策八）。以 run 标识直接建目录再写时，中途被强杀留下的目录凭内容分不清「建到一半」与「完整的 run 被删了运行态」，无从安全删除。
  - 被拒：**以 run 目录里还没有运行态为判据、判断与两个文件的写在运行态的短锁内做**（只有运行定义的目录照常建）：以 run 标识命名的目录在写完之前就已出现，中途被强杀留下的只写了一半的目录凭内容无从区分（同上条）；与暂存加改名叠用则是第二套互斥，而按标识写的各入口碰不到暂存目录，短锁在那里没有要防的对象。
  - 被拒：**进程级的全局持有者，外加只供测试的放开入口**：每个 store 的 `create_run` 都隐式让调用方成为持锁者，接口上看不出；生产代码里多出只供测试的入口。
  - 被拒：**由组合根在调用 `create_run` 之前取锁**：暂存目录在 `create_run` 里才建出，调用方无从先取；要先取就得把暂存目录的路径交出 adapter，本机目录的形态随之漏到端口之外。
  - 被拒：**改名用不替换已有目标的系统调用**（macOS `renamex_np` 的 `RENAME_EXCL`、Linux `renameat2` 的 `RENAME_NOREPLACE`）：支持与否随文件系统而变，不支持时要有回退，即两种机制并存；它防的只是替换一个不带记录的空目录。
- `update_job_state` 按 **scope_id 定位单个 job**，写它执行中的状态：认领之后的 `running` 与血缘（决定三的 RUNNING 中间态）；终态由 `commit_job_states` 写。写入的 job 态只能是 `running`、不带点名的标识，否则是参数错误（与 `commit_job_states` 对非终态的参数报错对称；点名只由终态写写下，执行中的写整项替换条目，带进去的标识会随之后的结束写留在由结束写结束的 job 上）；job 不在这个 run 的运行态里时不写（不臆造 job，与认领、投影相同：worker 报出运行定义以外的 scope_id 时，写进去的 `running` 项会让这个 run 永远到不了终态）。同一次写按 [0031](./0031-job-lifecycle-states-and-severity.md) 决定三的取法写 run 状态；库中已是终态的 job 不被改写（[0031](./0031-job-lifecycle-states-and-severity.md) 决定一·补），这一条件与写在同一次条件写里判断：local 在文件锁内，DDB 把「这个 job 在 Map 里且为 `pending` 或 `running`」写进同一次 `update_item` 的条件，不先读后写；run 已结束时写不成（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五），只发这一次写、不另写 job。理由：执行中的写来自已开始的执行（认领之后的事件），迟到的一次可能落在这个 job 的终态之后；不加这一条件，它把终态改回 `running`，此后又能记下第二个终态，「终态只写一次」只剩调用方的次序在守。local adapter 是「读 run_state→改该 scope_id→按锁内读到的整份运行态算 run 状态→写回」的 read-modify-write（在文件锁内完成，与其它写入口互斥，见决定三的并发不变量）。返回值是 run 在这次写时是否仍未结束（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五），local 取锁内读到的 run 状态；前台执行者据 False 得知 run 已被别处结束而停手。库中这个 job 已是终态或不在运行态里而没有写时，返回值同样只看 run：这两种情形都不说明 run 已结束，不是停手的理由，所以不另设一种返回值；DDB 从条件不成立时这次写带回的条目（`ReturnValuesOnConditionCheckFailure`）分辨是 run 已结束、这个 job 已结束或不在 Map 里，还是 STATE 不存在，不另读。执行中的写不会使 run 成为终态，所以一个布尔值就够。这要求 `RunState.jobs` 用 **Map<scope_id> 形状**（见决定五）。
- `commit_job_states` 把**一个或多个**由执行结果结束的 job 记为终态，终态带点名的标识（决定三）：库中已是终态的 job 不被改写（[0031](./0031-job-lifecycle-states-and-severity.md) 决定一·补）；其余给出的 job 与库中的条目按字段合并（下「终态写的字段合并」条）；同一次写按取法写 run 状态，这次写使 run 成为终态时同一次写下结束时刻；run 已结束时写不成（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）。local 在文件锁内按整份运行态计算；DDB 记下 job 终态的写法与条件见 [0034](./0034-detached-batch-reconciler.md) 机制三②。一次写可记多个 job：后台推进一轮里可能有多个 job 得出结果（决定三「后台推进同守」），云端每次写都按整个 STATE 条目计费（[0034](./0034-detached-batch-reconciler.md) 机制三「逐 job 写：内容不变不写，注定不成立的不发」段）。
  - **返回三种结果之一**：写成而 run 仍未结束（`OPEN`，给出的 job 里已是终态的不被改写）、写成并且这次写使 run 成为终态（`ENDED_RUN`）、没有写成（`ALREADY_ENDED`：run 在这次写之前已结束，运行态不变）。理由：报告只由使 run 成为终态的那次写的写入方生成（[0027](./0027-runreport-aggregation-index.md)「ReportStore 接口：整 run 一次写」节），run 成为终态只发生一次，所以谁的终态写返回 `ENDED_RUN`、或谁的结束写写成，谁生成报告；前台执行者据 `ALREADY_ENDED` 得知 run 已被别处结束而停手。被拒：**返回「这次写之前 run 是否仍未结束」的布尔值**，由调用方推断是不是自己这次写使 run 成为终态：写后读回分不出终态是谁写下的（读回之前别的写入方可能已写下最后一个 job 的终态），记住自己写下终态的 job 集合在云端多次调用重叠推进时不知道别的调用写了什么。
  - **终态写的字段合并**：状态取调用方给出的终态。认领时刻以库中的为准：认领那次写是它的来源（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五），库中没有时（没有认领过的 job）取调用方给出的。会话取调用方给出的：它是产出这个结果的那次执行的代表会话，与终态、被点名的明细出自同一个执行结果（决定三「被点名的那一份」条）；调用方没有给出时保留库中的，不以空值覆盖（决定三）。job 级说明不由终态写写下：它只由结束写写下（[0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节），由执行结果结束的 job 的说明在判定明细里（决定三）；库中的原样保留，调用方给出的不写下。点名的标识取调用方给出的：它是与这个终态出自同一个执行结果的那一份（决定三「被点名的那一份」条）；库中未结束的条目没有标识（只由终态写写下），调用方不给出即不点名，这只出现在没有记录的执行在内存里算运行态时（决定二），那里不存明细。库中已是终态的 job 不被改写，别的写入方点名的标识原样保留；结束写、执行中的写、认领与投影都不写标识，结束写对 `jobs` 的整体替换（云端，决定六）原样带上已有的点名。合并定义在 `run_status.commit_applied`（下「按模型使 job 成为终态的两个写入口」条），按写的那一刻库中的条目做：local 是锁内读到的，DDB 是每次重读到的。理由：调用方准备参数与写成之间，别的写可能为同一个 job 写下会话（执行中的写、投影）或认领时刻（认领）；DDB 的写被写入序号挡下、重读再算时同样如此（[0034](./0034-detached-batch-reconciler.md) 机制三②）。被拒：**整项替换、由调用方带上认领时刻与会话**：调用方手里的值是它准备参数那一刻的，晚于那一刻写下的值被抹成空；重读再算也保不住，替换用的仍是调用方的参数。
- `end_run` 是按本格式的模型算出的结束写（结束写的两种做法、来路与说明表见 [0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节）：一次条件写，只在 run 未结束时写成（不结束执行中 job 的来路另要求写下时没有 `running` 的 job，同一小节），返回是否写成，写成即这次写使 run 成为终态；运行态不存在时返回 False（决定六）。只对与本方 run 记录格式版本相同的 run 调用（同一小节）。调用方传入 core 里说明表的一行（`run_status.RunEnding`）：说明连同结构字段 `ends_running_jobs`（这条来路结束不结束执行中的 job）。adapter 不解释说明，写的条件与各 job 记成什么只看运行态与这个字段（[0031](./0031-job-lifecycle-states-and-severity.md) 决定一「状态是一切计算的唯一依据」条）。
- **error 变体是另一个写入口**：只写运行态的公共部分的结束写（做法、来路与条件见 [0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节「运行定义不可用、或 run 由别的格式写出时」条）。调用方给出原因（同一小节说明表下的四句之一）与结束时刻；返回是否写成，写成即这次写使 run 成为终态，运行态不存在时返回 False。它不经 `ending_applied`，不按本格式的模型读运行态，读到的条目原样复制。调用方只有云端推进器，它的存储恒是 DDB adapter；本机没有用到它的来路（没有「运行定义不可用」的情形，别的格式写出的本机 run 也没有一方去结束它，0031 同一小节），所以这个入口只在 DDB adapter 上、不在 `RunStore` 端口上，local adapter 不实现它：在本机实现它只多出一个没有调用方的写入口。它不参与两端对拍（[0034](./0034-detached-batch-reconciler.md) 机制三「两端对拍口径」只覆盖两个 adapter 都有的写入口），结果由 DDB 一侧的测试与 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 实测项 21、23 核对。DDB 的步骤见决定六「两个写入口的步骤」。
  - 理由：两种结束写读记录的方式不同，`end_run` 按本格式的模型读整份运行态、只对本格式的 run 成立，error 变体只认公共部分、对任何格式的 run 都成立；对不认识的属性的做法也不同（并进要写下的条目，与原样复制）。各是一个入口，入口本身说明它对什么样的记录成立，写的一方逐个写入口登记的做法（[0037](./0037-distribution-and-packaging.md) 决策 7「写的一方」）也是一个入口一种。
  - 被拒：**error 变体作为 `end_run` 的一种参数**（说明表一行另带一个「运行定义不可用」的结构字段，`end_run` 按它分支）：同一个入口有两种读记录的方式，用不用本格式的模型取决于调用方给的一个字段，字段给错就会用本格式的模型改写别的格式的记录；登记写入口时，一个入口要登记两种做法。
- **按模型使 job 成为终态的两个写入口，作用由 core 一处定义**：`commit_job_states` 与 `end_run` 对运行态的作用是 `core/gherkai_core/run_status.py` 的 `commit_applied` 与 `ending_applied`（取法 `run_status_of` 在同一处），两个 adapter 读到运行态之后都按它们算出要写下的运行态，各自只负责写的条件与落盘。error 变体的入口不经它们（上条）。理由：取法要看全部 job（[0034](./0034-detached-batch-reconciler.md) 机制三②），两端各写一份就各自演化，两端落库结果相同只剩对拍测试在守。
- **结束时刻由调用方给**：使 run 成为终态的写同时写下结束时刻（[0031](./0031-job-lifecycle-states-and-severity.md) 决定三），`commit_job_states`、`end_run` 与 error 变体的入口都收调用方给的结束时刻。adapter 不取时钟，core 只经注入的时钟取时刻（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策二「各执行方的落实」）；`commit_job_states` 的这次写没有使 run 成为终态时不写它。
- **改写运行态时原样保留不认识的部分**（写的一方的规则归 [0037](./0037-distribution-and-packaging.md) 决策 7，这里是两个 adapter 的落法）：
  - **local**：`run_state.json` 里不属于 `RunState` 模型的顶层键（如后台执行标记 `detached`）只在 `create_run` 时写下，此后每个写入口从锁内读到的原文里把它们原样带回，不逐个补回：逐个补回时，漏补一个键就静默丢失。job 条目一级同样：每个写入口按 scope_id 把读到的各条目里不属于模型的键带回，同名时以模型为准。顶层与 job 条目的模型键集在 `serialize.RUN_STATE_KEYS` 同一处登记。
  - **DDB**：认领与投影逐属性写，不提及的属性原样保留；单条 job 的执行中的写同样逐属性写模型里的键，这次无值的模型键删去（与本机整项替换模型键的结果相同），不提及不认识的属性。整体替换 `jobs` 的两个按模型的写入口（记下 job 终态的写与 `end_run`，决定六）把读到的条目里不在已知键集内的属性并进要写下的条目，已知键不从读到的值并入：并入已知键会把这次应当无值省去的键按读到的旧值写回（在真实的表上的核对登记在 [0034](./0034-detached-batch-reconciler.md) 机制三②的实测项）。error 变体的入口同样整体替换 `jobs`，但不分已知与不认识的键：读到的条目原样复制，只改未结束条目的 `status` 与 `message`（上「error 变体是另一个写入口」条）。
- **local 读到「不存在」即这个 run 不存在**：读运行定义、提交记录的头与运行态的各入口，以及建 run 之后各写入口打开短锁时，都直接打开，把打开得到的「不存在」（`FileNotFoundError`、`NotADirectoryError`）当作这个 run 不存在（读入口返回 None，写入口按上面各条里运行态不存在时的做法返回或报错），不先查是否存在再打开；`list_runs` 读某一项时得到「不存在」即略过这一项。理由：查与开之间 run 目录可能被删去，那时打开抛出的「不存在」会被当作读写记录失败，一边删旧 run 一边执行的 `settle-runs` 因此整体停止（列举之后被删去的 run 应当略过，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策八「处置的次序」一条）；直接打开，「已不在」就只有一种表现，与列举之后被删去的 run 略过是同一口径。

## 决定五：`RunState.jobs` 改 Map<scope_id> 形状（core model 一次到位）

`RunState.jobs` 从 `tuple[JobState, ...]` 改为 **`dict[scope_id, JobState]`**（`scope_id → JobState`）。
理由：实时按单个 job 刷状态需要「按 scope_id 定位某个 job」，list 只能按下标定位（DDB 更是无法按属性值定位 list 元素）。
Map 形状下 `update_job_state` 各 scope 互不干扰、天然支持单元素更新。

- **core model 一次到位、已落地**（不留到 DDB 阶段），落点 + 两条**防回归护栏**（原改造中两个会静默出错的陷阱）：
  - `model.RunState.jobs`：`dict[str, JobState]`（原 `tuple[JobState,...]`）。
  - `serialize.run_state_to_dict`：**护栏**——必须 `state.jobs.values()` 迭代；直接 `for js in state.jobs` 拿到的是 dict 的 **key（字符串）**、`js.scope_id` 静默 AttributeError。
  - `serialize.run_state_from_dict`：决定**落盘 JSON 形状**——本 ADR 选 **JSON 仍落 `list[{scope_id,status,session_id}]`（[0034](./0034-detached-batch-reconciler.md) 后每条另带 omit-when-None 的 `claimed_at`；点名的标识 `result_id` 同样 omit-when-None（决定三）；job 级说明 `message` 同样 omit-when-None，只由结束写写下，[0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节，状态投影与认领原样保留它）、仅内存模型是 Map**（读回时 `{js.scope_id: js}` 重建），`run_state.json` 的落盘形态不随内存模型变：jobs 的列表形态连同各条目的 `scope_id`、`status` 与 `message`，和 run 级的状态、起止时刻与说明一起，是运行态的公共部分（[0037](./0037-distribution-and-packaging.md) 决策 7）；DDB adapter 才在落库层用真 map item。
  - **`core/tests/test_stores.py`**：**护栏**——RunState 的消费方按 scope_id 取（如 `state.jobs["features/wiki.feature:6"]`），**不用整数下标**（dict 不支持，会 TypeError）。
  - （**澄清**：`RunState.jobs` 的读者都按 key 遍历或取值，Map 形状原生支持：从记录组装 RunResult 的 `project.assemble_run_result` 按运行定义里的 scope_id 取 `state.jobs[scope_id]`（[0027](./0027-runreport-aggregation-index.md)「RunResult 的组装只有一处」条），index.html 与 cli 的文本汇总读的是组装结果；[0034](./0034-detached-batch-reconciler.md) 的 `status`：`cli/gherkai_cli/render.py` 的 `render_run_state` 遍历 `state.jobs.items()`。）
- skipped 的 job 也要进 Map（它是 definition 的一部分，缺了会让 RunState 的 job 集与 RunMeta.jobs 对不齐）。各新态的 `session_id` 取值规则见 [0031](./0031-job-lifecycle-states-and-severity.md) 决定一；aborted 留 `session_id`（有现场可查）正是 Map 形状的受益场景。

## 决定六：云端 adapter 的落库形态（DDB/S3）

三层后端不对等、按访问模式各选（三层选型见 [0016](./0016-execution-architecture-core-lib-run-model.md)）：RunStore→DDB（提交记录的 jobs 部分在产物桶里，下「云端提交记录」条）、ResultStore/ReportStore→S3。以下是各后端落库形态的**决策**（怎么实现/怎么测是实现细节，不在此）。

**DDB 表 schema —— 单表、提交记录的头与运行态分两 item**：分区键字段是 `run_id`；排序键字段命名为 **`item_type`**，取值 `'META'` 为提交记录的头、`'STATE'` 为运行态，一个 run 落两个 item（同 `run_id`、`item_type` 各异）。提交记录的 jobs 不在这张表里（下「云端提交记录」条）。

- **为何分两 item（而非合成一个）**：提交记录建 run 时写一次、此后不改；运行态在推进中反复做条件写，每次写都按整个条目计写单位，而运行态那一条装得下的 job 数是一个 run 的 job 数上限的依据（[0025](./0025-plan-module-feature-to-jobs.md)「一个 run 的规模上限」，条目大小的实测见 [0034](./0034-detached-batch-reconciler.md) 机制三②）。合成一个，头的字节（额外请求头与会话预热地址的长度随使用方而变）进运行态的每一次写、占去条目留给 job 的余量，run 记录格式版本也不再存在一条建 run 之后不改的记录里（[0037](./0037-distribution-and-packaging.md) 决策 7：这个号只记在提交记录里）。`load_run_meta`/`load_run_state` 各自独立取（轮询进度高频读 STATE，不带上提交记录）。
- **为何同一张表（而非两张表）—— DDB single-table design（AWS 官方推荐）**：两 item 同属一个 run、共享 `run_id`，同分区键下一次 `Query`（按 run_id）即可一次捞回该 run 的两个 item（同分区访问的便利；强一致读保证的是每个 item 的最新值，不保证多 item 的快照）；两张表则丢掉同分区访问、运维翻倍（两套容量/IAM/备份/监控）。未来加 attempt（续跑，见「留口子」）/ per-scope 维度只需在同 `run_id` 下加新 `item_type` 值、同表零改。**多表是 RDBMS 范式直觉**——搬到 DDB 会丢分区局部性、放大成本。
- **排序键字段名用 `item_type` 而非 DDB 圈惯用缩写 `sk`**：`item_type` 自描述其真实语义（区分同一 run 的提交记录与运行态 item），避免 `sk` 被误读成 scenario/step key 或 DDB secondary index。
- 读用 `ConsistentRead=True`（RunStore 是控制面小记录，强一致的 commit-point 正确性收益 >> RCU 成本）。events 表的**投影读**（`DdbEventLog.records()`，推进步骤的输入）同理强一致：刚写的尾事件（如退出观察者的 `task_exited`）必须立即可见，最终一致读漏尾会把已完成 job 投成仍在跑；2× RRU 相对 run 级读量可忽略。**建表责任在 IaC/组合根、非 adapter**——adapter 假定表已存在（同 [0016](./0016-execution-architecture-core-lib-run-model.md) 窄腰：adapter 不持 schema/IAM 建表权知识）。
- **建 run 是条件写**（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）：依次写 jobs 对象、META、STATE，三次写都带条件：jobs 对象「键不存在才写」（S3 的条件写，`If-None-Match: *`），META 与 STATE「条目不存在」，STATE 在后（kicker 由 STATE 的新建触发，见 0034）。这个 run 是否已存在由这几次条件写裁定，被挡下的都按已存在报出、抛 `RunAlreadyExists`（决定四），不改任何已有的记录：META 的条件写被挡下（头已在），只留下这次写出、没有记录指向的 jobs 对象；在那之前 jobs 对象的条件写就被挡下（得到 412，键已存在）时，什么都没写下。jobs 对象的键带建 run 时新生成的随机段，同一个 run 标识的两次建 run 通常写出两个不同的键；不覆盖已有的 jobs 对象由条件写保证、不靠随机段不相撞：没有条件时，两次建 run 恰好得到同一个键，后提交的一方会在它的头被拒之前就换掉先提交一方的 jobs。所以建 run 之前不先读一次确认这个 run 不存在。jobs 对象的键、各步失败时留下什么见下「云端提交记录」条。
- **STATE item 带写入序号**：数值属性 `write_seq`，`create_run` 写 0；此后 adapter 写 STATE 的 `update_item` 里，改变了整体替换所写内容（`jobs` 与 run 状态）的写在同一次写里把它加一：认领、终态写 `commit_job_states`、结束写的两个入口（`end_run` 与 error 变体的入口）写成即改变了内容；投影的逐 job 写只在这次写提及的字段至少一项与库中不同时写成，写成即加一；投影的标量一步只写 HWM、不加（整体替换不写 HWM）；执行中的写 `update_job_state` 写成即加一、不比较内容（它只由前台执行调用，云端后端没有调用方；多加的一次也只让以序号为条件的写多重读一次）。缺这个属性的记录从 0 起算（与认领计数同一读法）；记下 job 终态的写与结束写以它为条件，用法与理由见 [0034](./0034-detached-batch-reconciler.md) 机制三②与「逐 job 写：内容不变不写，注定不成立的不发」段。它只在 DDB 一侧，不进 `RunState`：本机建 run 之后的写在文件锁内按整份运行态计算（决定三），不需要它；调用方也不经手它（结束写的条件按运行态表达，[0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节）。写入序号属运行态的公共部分，是跨版本不变的约定（[0037](./0037-distribution-and-packaging.md) 决策 7）：以别的格式写出的 run 为对象的写（后端的 error 变体）同样以读到的值为条件、写成即加一，它与按这个 run 的格式写它的一方的先后由此裁定（[0037](./0037-distribution-and-packaging.md) 决策 7「后端遇到别的格式写出的 run」里「与别的写方的先后」）。
  - **两个写入口的步骤**（记下 job 终态的写与结束写；结束写的两种做法各是一个入口，[0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节，决定四）：
    - 记下 job 终态的写与按本格式的模型算出的结束写（`end_run`）：先强一致 `GetItem` 读整个 STATE，按 `run_status.commit_applied` 或 `ending_applied`（决定四）从读到的运行态算出要写下的运行态，再发一次 `update_item`：整体替换 `jobs`（读到的条目里不认识的属性并进去，决定四「改写运行态时原样保留不认识的部分」条），写 run 状态连同状态分组（下「runs 表只有一个 GSI」条的写入规则），这次写改变了的结束时刻与 run 级说明一并写下，序号加一。
    - error 变体：先强一致 `GetItem` 读整个 STATE，只读其中的公共部分（run 级 `status`、`jobs` 各条目的 `status`）与写入序号，不按本格式的模型解读；缺 `status_group` 不算读不出（下「runs 表只有一个 GSI」条里缺分组属性的记录）；公共部分读不出时不写，调用方按闸里公共部分读不出同样处理（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九「落实时，后端各入口先过同一道闸」第一步）。再发一次 `update_item`：`jobs` 以读到的各条目整体替换，状态为 `pending` 或 `running` 的条目把 `status` 写成 `error`、`message` 写成调用方给的原因，条目里其余属性与已结束的条目原样复制；run 级 `status` 与 `status_group` 写成 `error`，`ended_at` 与 `message` 写成调用方给的值，序号加一；STATE 的其余属性不提及、原样保留。
    - 两者的条件相同：序号等于读到的值（读到时没有这个属性即要求仍没有）且 run 未结束。后一项让终态不可变（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）不只靠每一次写都加了序号，STATE 已不在时它同样不成立。run 已结束、结束写不成立或给出的 job 都已是终态时不发写。
  - **重读的次数有上限**：条件不成立即重读再算，每次重试之前等待、等待逐次翻倍，次数的上限按全部重试共等约十秒取（数值见 `core/gherkai_core/adapters/run_store/ddb.py` 的 `_REPLACE_MAX_RETRIES` 与 `_REPLACE_BACKOFF_S`），仍不成立即抛 `RunStateWriteContended`，运行态不因这次写改变，调用方按写不进运行态处理。每次条件不成立都说明读与写之间有别的写写成，不会因两个这样的写入方互相挡住而都写不成；等待针对的是并发的投影：它按 job 逐个写、每次改变了内容的写都让序号加一，job 多的 run 上一次投影持续的时间可能长于一次读与写。上限防的是条件因预料之外的原因一直不成立时无休止地重试。
- **形态变更**：变更表或索引的形态之前，按 [0037](./0037-distribution-and-packaging.md) 决策 7「后端形态变更的迁移口径」评估（默认先设计在线迁移，需要暂停使用的升级是例外，要在 ADR 与 CHANGELOG 里写明）。表的键、状态分组索引的名字、键与投影归云端后端接口版本（[0037](./0037-distribution-and-packaging.md) 决策 7）。
  - **改用状态分组索引的那次索引迁移的实测**（项目自己的开发后端，产品还没有使用者，在暂停使用的前提下迁移一次；起点 runs 表一百余个 item，`status-index` 与 `status-run_id-index` 都为 `ACTIVE`）：已有 GSI 的键不能原地修改，CloudFormation 一次更新只能新增或删除一个 GSI，因此新增一个、删除两个至少需要三次部署。三次部署依次新增 `status_group-run_id-index`（写端随这次上线）、删除 `status-index`（两个读者随这次切到新索引）、删除 `status-run_id-index`（并去掉 `status` 的属性定义），每次 CloudFormation 对 runs 表都只增或删一个索引，三次都成功、没有回滚。新增：部署报完成时新索引仍为 `CREATING`，约十分钟后转为 `ACTIVE`，期间两个旧索引一直是 `ACTIVE`——部署完成不等于索引就绪；另一张写有 300 条 STATE 的表上以 `UpdateTable` 新增同一索引约 17 分钟转为 `ACTIVE`（[0038](./0038-worker-image-delivery.md) 实测项 9），不对回填时长作承诺。删除：部署报完成后几分钟内第一次读 `DescribeTable`，被删的索引已不在、表为 `ACTIVE`（没有观察到 `DELETING` 持续多久）；最后一次之后属性定义只剩 `item_type`、`run_id`、`status_group`，索引只剩 `status_group-run_id-index`。次序取先增后删、写端随新增索引的那次部署上线：每一步都为两个读者各保留可用的索引；写端若晚于新索引的读者上线，切换之前建的 run 没有分组属性、切换之后对清理不可见。被拒的两种次序：先删一个旧索引、再以它的名字重建成新形态，同样三次部署，而从第一次部署到新索引 `ACTIVE` 之间那个读者不可用；把写端与新增索引拆成两次部署（共四次），只为符合文档「加索引的那次更新不改其它资源」的建议，换来多一个过渡阶段与随之多出的一组代码与后端错配的组合，它避开的后果（那次部署回滚后新索引留在表上、不在模板里，须手动删除后重试）可由 `DescribeTable` 发现、可恢复，不涉及 run 数据与清理的正确性。
  - **这次没有核、将来再改索引形态时仍须先核或按保守假设操作的**：①新增的索引 `ACTIVE` 之前就执行下一次改这张表的部署时，CloudFormation 的失败与回滚形态（文档写明这期间不能再更新这张表，见 [0041](./0041-agent-facing-cli-affordances.md) 决策七「更早的索引形态」；保守做法：以 `DescribeTable` 确认 `ACTIVE` 之后再部署）；②删除索引的那次部署在删除发起之后因别的资源失败而回滚的形态（保守做法：回滚之后等 `DescribeTable` 的索引集合与各索引状态稳定、stack 回到可更新的状态再重试；回滚中若重建了被删的索引，按新增处理，等它 `ACTIVE`）；③一个索引 `DELETING` 期间能否删除另一个（保守做法：等前一个从 `DescribeTable` 里消失再删下一个）。
- **runs 表只有一个 GSI `status_group-run_id-index`，两条访问路径共用（写端、索引定义与两个读者已实装）**：分区键 `status_group`、排序键 `run_id`、投影 INCLUDE `worker_task_def_arns`。`status_group` 是 STATE item 的顶层派生属性：run 级状态为非终态时取常量 `live`，为终态时取该终态的状态值；只有 STATE item 带它（META item 没有，稀疏由此构造）。它与它的派生规则属运行态的公共部分，是跨版本不变的约定（[0037](./0037-distribution-and-packaging.md) 决策 7）：任何格式的写方都按同一规则维护它，别的格式写出的 run 同样在这个索引里。**写入规则：每一处写 `status` 的地方，`status_group` 都由同一个派生函数（core 里一处）从这次写入的 `status` 算出，写在同一次写里**，没有例外：`create_run` 按传入初始状态的 `status` 算出，建 run 时初始状态为 `pending`，得 `live`；使 run 成为终态的写（记下最后一个未结束 job 的终态的那次写，或结束写，[0031](./0031-job-lifecycle-states-and-severity.md) 决定三）在同一次 `update_item` 里写成该终态值；认领、投影与 job 状态写把 run 级写成 `running` 时一并写 `live`，它们的条件保证写之前 run 级是非终态，库中值本来就是 `live`（早于本形态写出、缺分组属性的除外，见下），这次是同值写，索引键不变、不产生索引写（依据：DynamoDB 官方的 GSI 写入规则明确，索引写按这次写入实际改变的属性判定，同值写没有改变键的值，按此不写索引；[0034](./0034-detached-batch-reconciler.md) 机制三实测项 6 在以 `status` 为键的索引上对索引键属性的同值写测得为 0；新索引上已实测：这三条把 run 级从 `pending` 换到 `running` 的写对它都计 0，同一张表上以 `status` 为键的索引对它们各计 2，[0038](./0038-worker-image-delivery.md) 实测项 8）。早于本形态写出、还没有 `status_group` 的 STATE（两个来源：从更早的索引形态迁移而来的后端上、改用状态分组索引之前写出的记录——产品不提供这种迁移的路径，[0041](./0041-agent-facing-cli-affordances.md) 决策七「更早的索引形态」；以及 1.5 之前的命令行工具向已是状态分组索引的后端写出的记录，[0038](./0038-worker-image-delivery.md) 清理 pass 条的残余风险⑤；后一种的记录格式版本读作 0，由后端的闸以 error 变体结束，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九「落实时」一段），只有经写 run 级 `status` 的写入（认领、把 run 级写成 `running` 的投影与 job 状态写、使 run 成为终态的写，含 error 变体）才补上分组属性：补上的那次写计一次索引写（把项放进索引），从此进入对应的分组。缺分组属性不算运行态的公共部分读不出，读的一方按 run 级 `status` 判断是否结束。不写 run 级 `status` 的写不碰它，也就不补，例如全部 job 仍为 `pending` 的投影：它不改变任何 job 的状态，因而不写 run 级 `status`（由 [0031](./0031-job-lifecycle-states-and-severity.md) 决定三推出）。不变量因此分两半，由覆盖全部写路径的不变量测试守：写 run 级 `status` 的路径在写之后建立 `status_group` 与 `status` 的对应（等于由 `status` 推出的分组）；其余路径保持已有的对应（写之前对应成立，写之后仍成立；写之前缺分组属性的，写之后仍缺）。两个使用方：worker revision 清理的引用检查读 `live` 分组，取其中各 run 的 `worker_task_def_arns` 求并集（[0038](./0038-worker-image-delivery.md)「清理 pass」条）；`list-runs` 读 `live` 分组取全部非终态 run 的 run_id，按各终态分组取最近 N 条（[0041](./0041-agent-facing-cli-affordances.md) 决策七）。另有 `deploy` 在数据版本要变时对 `live` 分组计数（[0037](./0037-distribution-and-packaging.md) 决策 7「`deploy` 入口的检查」），它的读量与最终一致的程度还没有核过，部署之后核（0037 实测项 8）。GSI 的读只有最终一致，所以 `list-runs` 只从索引取 run_id，状态与 job 计数以 `BatchGetItem`（`ConsistentRead=True`）读回的 STATE item 为准，与上条「读用强一致」一致；清理不读回，理由见 0038 该条。索引不改变「不 Scan runs 表」的约束（表 `RETAIN`、无 TTL，[0038](./0038-worker-image-delivery.md)）。
  - **为何按状态分组、不按状态**：GSI 的分区键每换一次值，索引要删旧项、写新项，计两个写单位（DynamoDB 的 GSI 写入计费规则，[0034](./0034-detached-batch-reconciler.md) 机制三实测项 6 测得每个索引 2.0），而且删旧项与写新项哪个先可见没有承诺，两者之间可能有一段两个分区都查不到的间隙。run 级状态从 `pending` 换到 `running` 时，以 `status` 为键的索引在这两点上都付代价，而两个使用方都不需要区分这两个非终态：清理只问「还没收尾的 run 引用了哪些 revision」，`list-runs` 的非终态部分本来就整段列出、状态以读回为准。改用分组后，换到 `running` 时 `status_group` 仍是 `live`（同值写），`status` 既不是这个索引的键、也不在投影里，索引不计写，索引项在 run 收尾之前一直在 `live` 分组：`pending` 到 `running` 换键造成的间隙随之不再存在。另一条依赖不变：新建 run 的索引项要在清理的静默期之内（约 1 小时）可见，GSI 的传播没有承诺上界，这条依赖在以 `status` 为键的旧索引上本来就有，本设计没有新增（0038「清理 pass」条边界情形 (b)）。一个 run 的索引写由此只剩建 run 一次与收尾换分组两次。终态各自成组是因为 `list-runs` 的 `--status` 按终态逐个取最近 N 条、每个终态各自计名额（0041 决策七「云端实现」），合成一个「已结束」分组就得读回之后再按状态筛，名额与读量都失去上界。
  - **为何一个索引、而不是各管一条路径**：两条路径对键的需求（分区值在 run 存活期间不变，带 `run_id` 排序键以取有界的最近 N 条）可以由同一个索引同时满足，差别只剩清理要的 revision 列表投影，由 `list-runs` 读到的每个索引项多带这个列表承担（读量增量见 0041 决策七状态分组索引的「代价」段）。两个索引意味着每个 run 的每次分组变化在两处各付一次索引写，且两处索引的定义各自维护。
  - **运行成本前后对照**（每个索引项小于 1 KB，一次索引操作计 1 个写单位）：run 以 `pending` 建、只收尾一次。一个经过 `running` 再收尾的 run，此前两个以 `status` 为键的索引（`status-index` 与 `status-run_id-index`）共计 10 个索引写单位，单一状态分组索引为 3；没有经过 `running` 就收尾的 run，由 6 降到 3。run 一到终态，运行态的任何写都不成立，`create_run` 只在 run 不存在时成立（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五），没有把已收尾的 run 改成另一个终态、或整体覆盖已有 STATE 的写，也就没有由它们带来的换分组索引写。索引存储约等于此前 `status-index` 一份（终态 run 的项也带 revision 列表），`status-run_id-index` 那一份不再有。
  - **旧索引定义已删除**：以 `status` 为分区键的 `status-index`（投影 INCLUDE `worker_task_def_arns`，原由清理读）与 `status-run_id-index`（排序键 `run_id`，投影 KEYS_ONLY，原由 `list-runs` 读）都已从部署模板删除，模板里只有 `status_group-run_id-index`。CloudFormation 一次更新只能新增或删除一个 GSI，新增一个、删除两个各占一次部署。
  - **被拒**：①**维持两个以 `status` 为键的索引，只给清理加复查**：每个 run 10 个索引写单位不变；换键与间隙都还在，趟内复查之后漏检要求间隙长于一次分区读取加等待时长，余量只有秒级，远小于静默期给新建 run 留的约 1 小时。②**合并成一个以 `status` 为分区键、带 `run_id` 排序键、投影 revision 列表的索引**：索引写降到每个 run 5，但 `pending` 到 `running` 的换键与间隙都还在，清理仍要靠复查，余量同①；部署次数与本方案相同。③**只留 KEYS_ONLY 的 `status-run_id-index`，清理取 run_id 后以强一致读回 STATE 判断引用**：只需一次部署；换键与间隙都还在，清理另加跨趟确认标记，漏检要求同一个间隙持续不少于两趟的间隔 T。T 取到约 1 小时时，它对传播上界的依赖与本方案的静默期（新建 run 的索引项须在约 1 小时内可见，两种方案都有）同一量级，区别在余量大小、不在有无。被拒的依据是其余几项：运行成本上，每趟清理要强一致读回全部非终态 run 的整个 STATE（含随 job 数增长的 `jobs` Map），读量按 item 大小计、投影不减少读量，每个 run 5 个索引写单位；协议上，多一个 revision 级的确认标记，回收多等一趟；对传播上界的依赖余量取决于 T，T 取小了余量随之变小。④**另立一个稀疏的存活标记索引（建 run 时写、收尾时删，分区键在 run 存活期间不变）供清理，保留 `status-run_id-index` 供 `list-runs`**：清理侧同样没有 `pending` 到 `running` 的换键间隙，但表上是两个索引、每个 run 7 个索引写单位；存活标记与 `status` 是「非终态」的两份表示，漏写标记的方向会让清理看不见在用的 run，而这种违约在别处没有任何表现（`list-runs` 照常可用），只能靠测试发现。本方案的状态分组同样是派生属性，但让清理看不见在用 run 的那个方向（非终态 run 不在 `live` 分组）同样让它从 `list-runs` 的非终态部分消失，违约在使用中即可被发现；反方向（收尾时没有改分组，STATE 已到终态却留在 `live` 分组）对清理偏保守，代价是 `live` 分组的读量随之增长、它引用的 revision 不被回收；`list-runs` 的默认清单按读回的状态仍显示它的真实终态，只有单查该终态（`--status <该终态>`）时它不在所查的分组里而缺席，不易察觉。

**RunState.jobs 落 DDB 用原生 Map（M 型）、非 JSON blob**（以 scope_id 为键、各项带 `status` 与可省的 `message` 的这一形态，连同 run 级的状态、起止时刻与说明，属运行态的公共部分，云端的状态分组与写入序号同属其中，[0037](./0037-distribution-and-packaging.md) 决策 7）：认领按 scope_id 单元素写（[0034](./0034-detached-batch-reconciler.md) 机制三「run 级状态只进不退」条①）；记下 job 终态的写与结束写对 `jobs` 整体替换、以写入序号为条件（[0034](./0034-detached-batch-reconciler.md) 机制三②）；每个 job 条目另带点名的标识 `result_id`（未点名时省键，决定三；记下 job 终态的写与结束写整体替换 `jobs` 时原样带上，漏带即抹掉此前各 job 的点名，两个 adapter 对拍守它）与 job 级说明 `message`（没有时省键，同决定五的落盘键）；**投影写（`project_state`）逐属性**（`SET jobs.#sid.<attr>=…`：未提及的 `session_id`/`claimed_at` 由 update_item 天然保留——对拍 local 的「投影缺字段回填库中值」兜底；整 entry 覆盖时，不带 baseline 的投影会抹掉只由 claim 落库的 `claimed_at`）。blob 无法单元素刷，认领与投影都退化成整 item RMW、违背决定四/五。**字段仍源于 serialize（单一真理源），只是 jobs 的容器形状在 adapter 层从 list 特化成 Map**——这是「DDB adapter 对 jobs 容器的落库层特化」，非第二真理源。**RunStore 侧无 float**（RunMeta/RunState 全 str/int/Status，float 只在 JobResult/RunResult→ResultStore），故原生 Map 无 float→Decimal 顾虑。未 create 就 update 须复刻 local「报错」语义（条件写），结束写在 STATE 不存在时与 local 同样返回 False；session_id=None 沿用 omit-when-None（不写该键、读回得 None）；run 级 `message`（结束的原因，[0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节）同样 omit-when-None，随结束写的同一次条件写落 STATE item。

**ResultStore 的后端是 S3**（坐实 [0016](./0016-execution-architecture-core-lib-run-model.md) 原「待定」）：每次保存明细一个 S3 对象，键为 `<report_dir>/<run_id>/jobs/<result_id>.json`（标识按不透明标识符编码成一段，键里不带 scope_id，理由同决定三「本机判定明细的落点」框），一次 `PutObject`、不带条件，单个对象的写本身是原子的；同一个 job 的多份互不覆盖。读者先从运行态取 job 的清单与各自点名的标识，再按键取那一份，不列举前缀（决定三「点名」条），所以读明细只要读对象的权限、不要 `s3:ListBucket`；没有列举权限时，取一个不存在的键得到的是 AccessDenied 而不是 NoSuchKey，读者按缺读对象的权限报出，说法仍然属实（[0042](./0042-step-evidence-and-explain.md) 决策四「数据来源」段）。将来若需跨 scope 查询/过滤，加 DDB 索引层（加法不返工）。

**云端提交记录：runs 表里的一条头，加产物桶 `definitions/` 前缀下的一个 jobs 对象**。运行定义在云端的存放形态只在本条写全，别处引用本条。

- **头**（META item）：顶层属性是键属性 `run_id` 与 `item_type`、run 记录格式版本 `schema_version`、写出版本 `cli_version`、期限 `deadline_at`、指向 jobs 对象的 `jobs_ref`（值是这个对象的 `s3://` 地址）与 `meta_json`。`meta_json` 是运行定义去掉 `jobs` 之后的序列化，带运行定义里 jobs 之外的全部字段：run 记录格式版本、写出版本、run 标识、建立时刻、期限、额外请求头、并发上限、steps 目录、worker variant、各引擎的任务定义修订（`worker_task_defs`）、worker 协议版本（`worker_protocol_version`）与会话预热地址。顶层的格式版本、写出版本与期限是 `meta_json` 里同名键的副本，值恒同，只读头的各处用投影只取它们、不解析 `meta_json`（下「读整份定义」一项）。一个普通 run 的头约三百字节，不随 job 数增长。头的顶层属性按 [0037](./0037-distribution-and-packaging.md) 决策 7 的基线加登记管：同一个格式版本之内可以加属性，新加的登记缺席含义。头里格式版本的位置与读法是跨版本不变的约定（[0037](./0037-distribution-and-packaging.md) 决策 7）：主键为（run_id，`META`）的条目顶层的数值属性 `schema_version`，缺席读作 0，不是整数即形态违约；别的格式写出的 run 由此认出。
- **jobs 对象**：运行定义的 `jobs` 数组整份序列化成一个对象（与 `serialize.run_meta_to_dict` 产出的 `jobs` 同一形态），DocString 与 DataTable 原样内联其中。键为 `definitions/<run_id>/<随机段>.json`，随机段在每次建 run 时新生成，同一个 run 标识的两次建 run 通常写出两个不同的对象；写它带「键不存在才写」的条件，已有的对象不被覆盖（上「建 run 是条件写」条）。`definitions/` 是产物桶里专放运行定义的前缀：不放在报告前缀之下、不随部署方配置的报告前缀变化，也不在 worker 要读的安装包前缀 `apps/` 之下；这个前缀不设过期规则（[0033](./0033-iac-aws-backend-and-composition-wiring.md)「资源清单」3.）。单设这个前缀是为了把权限收在它上面：提交恒需的写只授在这个前缀上，worker 的 task role 对它另有一条读与写的显式拒绝；两者的理由各在 [0033](./0033-iac-aws-backend-and-composition-wiring.md)「资源清单」节编排进程角色段里「S3 上每次都要的两项收在定义前缀上」一句与「IAM 最小权限」节 task role 表的显式拒绝一行，各方在这个前缀上的权限也登记在这两处。
- **令牌与额外请求头留在头里**：会话预热地址带隧道访问令牌，它与额外请求头都留在头里，提交记录放进产物桶的部分（jobs 对象）不带它们。这只说提交记录：引擎原生的轨迹与报告是 worker 写进桶的产物，可能记下预热地址（各处残留见 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 13「令牌与 cookie 的残留面」一条）。每个 worker 的 task role 对整个产物桶有读写，而它按设计碰不到 runs 表（[0033](./0033-iac-aws-backend-and-composition-wiring.md)「IAM 最小权限」节的 task role 表；谁读得到头见决定三「读取权限」，明文落库的范围见 [0035](./0035-local-app-testing-via-tunnel.md) 决策 5「明确不脱敏」一条）。jobs 对象只有 job 文本，与早已在桶里的 job 输入（[0033](./0033-iac-aws-backend-and-composition-wiring.md)「资源清单」的 job-in）是同一类内容。
- **建 run 的次序与失败时留下的**（次序与条件见上「建 run 是条件写」条）：jobs 对象在头之前写成，读者照头里的地址去取时它已在，S3 上新写成的对象立即读得到写入的内容（下「依据」第 3 项）。各步失败时留下的：写 jobs 对象失败或被条件挡下（键已存在，按 run 已存在报出），什么都没写下；头的写失败或被条件挡下（run 已存在），留下一个没有记录指向的 jobs 对象；运行态的写失败，头与 jobs 对象留在原处，这个 run 没有运行态、不被推进（kicker 由运行态的新建触发）。没有记录指向的 jobs 对象没有读者；它在定义前缀之下，那里不设过期规则（[0033](./0033-iac-aws-backend-and-composition-wiring.md)「资源清单」3.），所以它留在桶里、不会被自动删去。两次建 run 得到同一个 run 标识而 jobs 对象的键不同时就是这样：两份 jobs 对象都写成，头只有一方写成，败的一方留下一个没有头引用、没有过期规则的 jobs 对象。已存在以 `RunAlreadyExists` 报出，其余按写记录失败报出（决定七「失败退出码分层」）。
- **读整份定义**（`load_run_meta`）：强一致读头；先看顶层的 run 记录格式版本，与读的一方不同即按格式版本不合处理（各方怎样处理见 [0037](./0037-distribution-and-packaging.md) 决策 7，后端见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九「落实时，后端各入口先过同一道闸」），不取 jobs 对象；再按 `jobs_ref` 取 jobs 对象，与 `meta_json` 拼回运行定义。读整份定义的是要用到 job 定义的各方：两个推进 Lambda、用户一侧的处置方（`status --wait`、`settle-runs`，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策八）与 `explain`。`explain` 不处置、不写记录，但它以 job 定义为骨架列出 scenario 与 step，由结束写结束的 job 没有明细，骨架是唯一来源（[0042](./0042-step-evidence-and-explain.md) 决策四「数据来源」段）。只读头的各处不取 jobs 对象：不带 `--wait` 的 `status`、`list-runs`，以及清扫里只按期限判断的那一条（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九第 2 条②）。
- **jobs 对象取不到时**：后端与用户一侧归类不同。
  - **后端**：两个推进 Lambda 的执行角色有桶的列举权限（[0033](./0033-iac-aws-backend-and-composition-wiring.md)「资源清单」10. 的桶读写），缺键得到「键不存在」，把它归为运行定义不可用，与提交记录已不在同一类（[0037](./0037-distribution-and-packaging.md) 决策 7，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九「落实时，后端各入口先过同一道闸」），以结束写的 error 变体结束（只写运行态的公共部分，[0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节）并清扫（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九第 2 条）；取它时别的 S3 错误原样抛出，记为这条记录的失败（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九第 2 条「失败与批的隔离」一项），由之后的触发再读。
  - **用户一侧**（处置方 `status --wait`、`settle-runs`，以及 `explain`）：取 jobs 对象失败时，不论得到哪种错误（按最小权限没有列举权限，缺键得到的是拒绝访问；部署方另授了列举权限时得到「键不存在」），都按读写记录失败处理，不按错误码分支。处置方不处置，说明按 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策八「读写记录失败的类别」一条，那里给拒绝访问与「键不存在」这两种补了半句、句子只在那里写全。`explain` 以退出码 2 结束，不显示半份结果（[0042](./0042-step-evidence-and-explain.md) 决策四「退出码」段）。这个 run 由后端在此后带到它的调用里结束（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九「落实时，后端各入口先过同一道闸」）；没有任何调用带到它时，见 0054「边界与已知局限」里「其它局限」。
  - **理由**：缺键不会因重试而好转，分得清它的后端把它记成 error，这个 run 才有结果。用户一侧在最小权限下分不清是权限不够还是对象不在，若照样记成 error，一次权限问题就被永久记成 error（与 [0037](./0037-distribution-and-packaging.md) 决策 7 里读取本身的失败原样抛出同一取向）。拿到「键不存在」时也不另走一支：列举权限授不授由部署方决定，按错误码分支，同一个 run 在用户一侧的结果就随部署方的授权而变；后端总分得清，此后有调用带到这个 run 时由它结束，多出的这一支只让结束提早一些（没有任何调用带到它时，这个 run 留在清单里，见 0054「边界与已知局限」里「其它局限」）。说明里补半句的理由见 0054 同一条。
- **装配**（装配规则只在本项写全，别处引用本项）：云端组合根按命令给 `DynamoDBRunStore` 装配 jobs 对象的存取，所用的桶就是判定明细与报告所在的产物桶。要建 run 或读整份定义的各方给：`submit`、两个推进 Lambda、用户一侧的处置方 `status --wait` 与 `settle-runs`、`explain`（上「读整份定义」一项）；只读头的命令（不带 `--wait` 的 `status`、`list-runs`）可以不给。没给而去建 run 或读整份定义，一律报装配缺失，对所有 run 都报，与 run 的内容无关。没有内联形态：不给存取不等于把 jobs 内联进头，也不设把 jobs 改为内联进 runs 表的选项，云端提交记录只有本条这一种存放形态。理由：装配缺失若只在部分 run 上报出，漏装的组合根在多数 run 上照常工作，到少见的 run 上才失败；对所有 run 都报，漏装在第一次使用时即暴露。
- **大小**：提交记录没有随用例内容变化的大小上限：头不随 job 数增长，jobs 对象在 S3 上。一个 run 的 job 数上限的依据是运行态那一条（[0025](./0025-plan-module-feature-to-jobs.md)「一个 run 的规模上限」，[0034](./0034-detached-batch-reconciler.md) 机制三②「条目大小」）。
- **依据**（判据型的实测数）：
  1. 整份运行定义的序列化（全部内联进一条记录时的 `meta_json`）字节数（core 的 plan 与序列化在本机量，一个 job 一个 scenario、每个 step 约 55 个字符）：500 个 job、每个 3 个 step 为 315,662；每个 5 个 step 为 409,790，已超过 DynamoDB 单条记录的上限 409,600 字节；每个 8 个 step 为 550,884；300 个 job、每个 8 个 step 为 330,484；100 个 job、每个 8 个 step 为 110,084。几乎不放内容、只把 scope 标识用到 245 字节，500 个 job 也有 386,868。DynamoDB 对 410KB 的写以「Item size has exceeded the maximum allowed size」拒绝。整份放进一条记录时，普通用例先于 500 个 job 撞上这一上限。
  2. 逐参数卸载（DocString 与 DataTable 的正文各存一个对象、记录里换成指针）把记录变大：300 个 job、每个 3 个 step、每个 step 带一张 2×2 的 DataTable、路径含中文时，内联为 299,904 字节，卸载之后为 1,372,098 字节（每个指针里带两次百分号编码的 scope 标识与 scenario 标识）；一个 500 个 job、每个带一张 DataTable 的 run，读一次定义要取回 500 个对象。
  3. 同区域实测（EC2 到临时桶与按需计费的临时表）：读约 550KB 的 S3 对象中位 31 毫秒（p95 36），读约 100KB 的中位 25 毫秒，写约 550KB 的中位 38 毫秒；强一致读约 390KB 的一条 DynamoDB 记录中位 6.7 毫秒、96 个读单位，只投影头部属性同样 96 个，写它 381 个写单位；只有头的一条记录读写各 1 个单位、读 2.9 毫秒；S3 对象写成之后立即读，读到的就是写入的内容；带「键不存在才写」条件（`If-None-Match: *`）的 PutObject 在键已存在时得到 412（`PreconditionFailed`），原对象不变。
- 被拒：**只卸载 DocString 与 DataTable 的正文**（按位置把正文换成指向 S3 的指针、读时还原）：scenario 名与 step 文本仍在记录里，普通用例 300 来个 job 就接近单条上限（上「依据」第 1 项）；指针比小的正文还大，带小表格的用例卸载之后记录反而大几倍，读一次定义要逐份取回正文（第 2 项）；还原一方的装配遗漏只在带多行参数的 run 上暴露（上「装配」一项的理由）。
- 被拒：**整份运行定义放 S3**：令牌与额外请求头随提交记录进了产物桶，而每个 worker 的 task role 对整个桶有读写；留在头里，它们在 worker 按设计碰不到的 runs 表上（上「令牌与额外请求头留在头里」一项）。
- 被拒：**正文分成几条记录留在 runs 表里**（不经 S3）。它的好处：提交与读定义都不需要 S3 权限；整份定义留在一个存储里，后端与用户一侧对同一情形得到同样的错误（用户一侧不会把对象不在读成拒绝访问）；不受桶上生命周期规则的影响。被拒的理由：读写量随用例内容增长，推进器每次推进与等待中的 `status --wait` 每次轮询都按整份定义计读单位，约 550KB 的定义一次约 137 个读单位，jobs 放 S3 是 1 个读单位加一次请求（上「依据」第 3 项）；大段正文与运行态挤在同一个分区键上；读路径多出分片数的核对、续读与未读全的判断，读不全与定义违约要靠它分清。owner 2026-11-22 在两者之间选了 jobs 放 S3。
- 被拒：**按大小分两种形态**（小的内联、大的放 S3）：同一条记录两种形态，读者两种都要认，大的那一种只在少见的大 run 上走到，那条路径上的缺陷要到那时才暴露。
- 被拒：**入口按序列化之后的大小拒绝**：上限随用例内容变化，与 [0025](./0025-plan-module-feature-to-jobs.md)「一个 run 的规模上限」节被拒的「云端提交时按各字段的上界估算记录大小、超出再拒」同类，用户从用例本身看不出能不能执行；按上「依据」第 1 项，普通用例先于 500 个 job 撞上它。
- 被拒：**压缩之后内联**：上限仍随内容变化，只是推远。
- 被拒：**一个 job 一条记录**：建 run 变成几百次写（500 个 job 即 500 次）。
- 被拒：**不给 jobs 对象的存取即内联，或设一个改为内联的选项**：同一个后端上提交记录的形态随写它的组合根装配了什么、或使用者选了什么而变，读者两种都要认；内联的那一种受单条记录的大小上限约束，这一上限是协议的硬限、不是调优空间（上「依据」第 1 项）；漏装的提交在小 run 上照常成功、到大 run 上才撞单条上限，装配遗漏被用例内容掩盖（上「装配」一项）。
- **实测项**（实装时在真实的表与桶上各核一次，测试替身之外）：
  1. 约 550KB 的定义（500 个 job、每个 8 个 step 那一格）建 run 之后读回，读回的运行定义与写入的相同。
  2. 同一个 run 标识再建一次：以 run 已存在失败，头、运行态与先前的 jobs 对象都不改，只多出一个没有记录指向的 jobs 对象。让第二次建 run 取到与第一次相同的 jobs 对象键（替换随机段的来源）：jobs 对象的写得到 412，以 run 已存在失败，先前的 jobs 对象、头与运行态都不改，也不多出对象。带「键不存在才写」条件的写在没有桶列举权限的受限角色（提交者按最小权限授予的那一种）下，键已存在时得到的仍是 412（部署之后核）。
  3. 删去一个未结束的 run 的 jobs 对象：推进 Lambda 做结束写的 error 变体；用户一侧的 `status --wait` 与 `settle-runs` 按读写记录失败结束、不改动这个 run 的记录，`explain` 以退出码 2 结束、不显示半份结果。
  4. 没给 jobs 对象存取的 `DynamoDBRunStore`：建 run 与读整份定义都报装配缺失，不带多行参数的 run 同样报；只读头的读照常。
  5. 在部署出的推进 Lambda 里取约 550KB 的 jobs 对象的时延（冷启动与热调用各记下）：上「依据」第 3 项是同区域 EC2 上量的，不代替 Lambda 里的读。

**boto3 依赖 = optional extra（方案 A）**：boto3 进 `[project.optional-dependencies].aws`（core 主依赖仍只 gherkin，缺 boto3 时只有云端 adapter 用起来失败、core 主体可轻量 import）——守 [0016](./0016-execution-architecture-core-lib-run-model.md) 窄腰。

## 决定七：cli 接线 cloud 后端（jobs 对象的存取 + 失败退出码分层）

cli `--backend {local,cloud}` 的组合根装配（两后端都下沉 `compose` 的 `build_local_stores`/`build_cloud_stores`、两种 boto3 句柄、单桶复用 report-dir、`--region`/`--profile`、artifacts URI 化）见 [0016](./0016-execution-architecture-core-lib-run-model.md)「cli `--backend {local,cloud}`」节；`run` 只有本机后端（[0016](./0016-execution-architecture-core-lib-run-model.md) 决策 A）。这里记三条与实时写落库形态强相关的决策：

**jobs 对象的存取按命令装配**：云端组合根给要建 run 或读整份定义的命令装配 jobs 对象的存取，只读头的命令可以不给；各命令归哪一侧、没给时怎样报错、为什么没有内联形态，见决定六「云端提交记录」条的「装配」一项。

**Store port 有 `preflight()`，`begin` 里先探活**：三个 Store port（Run/Result/Report）各有 `preflight() -> None`，**local adapter 是 no-op**（本地无「桶/表不存在」问题）。`RunPersistence.begin` 在 `create_run` **之前**调三个 store 的 `preflight()`。preflight 归 Store 自己（各后端最懂怎么探活、内聚），不外泄到组合根。现行设计里 `preflight()` 的调用方只有 `begin`，而 `begin` 只装配本机 adapter；云端后端只有 `submit`，它在建 run 之前另做资源 preflight（[0033](./0033-iac-aws-backend-and-composition-wiring.md) preflight 节，不探测桶）。所以云端 adapter 的 `preflight()` 在现行设计里没有调用方，不作为云端资源检查的一部分。

**失败退出码分层——切分线 = run 是否已开始执行**（退出码的取值见 [0031](./0031-job-lifecycle-states-and-severity.md) 决定五；全走 stderr）：
- **退 2（还没开始执行就拒绝，与 `assertion_votes` 不在 1 到 5 之内同类，一句诊断、不打回溯）**：缺 boto3（`build_cloud_stores` 的惰性 `import boto3` 抛 ImportError，cli 的 gated except 接住 → 退 2；发行包 `gherkai` 已硬依赖 `gherkai-runtime[aws]`、自带 boto3，装库层 extra 只是库消费者的事，见 [0037](./0037-distribution-and-packaging.md) 决策 2c）；云端 `submit` 的资源 preflight 不过或 `create_run` 抛 botocore 异常（表/桶不存在、无权限、凭证/region 缺）；本机建 run 时写记录失败（前台 `run` 与本机后台推进进程给同一句说明、同一退出码，后台的经回报由 `submit` 输出，[0035](./0035-local-app-testing-via-tunnel.md) 决策 3「三种组合的宿主与次序」里「本机 `submit`」一条），其中记录已写下、而准备执行用的文件（事件库、日志）失败的，说明这个 run 还没有开始执行、在记录里停在 `pending`，并给出把它记为已结束的 `settle-runs` 整条命令，再请使用者重新执行（经 `submit` 报出时说重新提交）；本机后端的报告目录路径太长、或路径里有一层名字太长（决定四「报告目录的路径长度」条），在入口即拒绝、什么都不建。两个后端的「run 已经存在」（`create_run` 抛 `RunAlreadyExists`，决定四）与写记录失败分开报，按这个异常类型判断，不按 `FileExistsError` 一概而论：前者重新执行即可（每次执行生成新的 run_id），后者要先查报告目录的读写权限与剩余空间。前台与后台对同一情形给同一回答，因为两者建 run 的步骤相同（0035 决策 3 同一节），执行方式不改变判定。
- **非零（run 已开始执行，只有本机 `run`）**：运行期间保存明细、写运行态或读回运行态失败。一是 `schedule()` 运行期内 `on_event`/`on_job_complete`、认领或重试之前的读（`RunRecord.claim` / `still_open`，见决定一「服从记录的三项能力」）抛出存储异常（如磁盘写不进；保存明细先按决定三「保存明细失败」重试）：决定三已定 `on_event` 或 `on_job_complete` 抛异常时 schedule 先 stop 所有 worker 再重抛（`on_event` 的异常不产生判定），故会冒泡出 `schedule()`；二是 schedule 返回之后落库服务的结束写，或为组装 RunResult 而读运行态与被点名明细的那一次失败（含被点名的那一份读不到，决定三「ReportStore.write 失败隔离」注与「点名」条）。`run` 以非零退出码结束、终端里有存储错误：给一句产品语言的说明（发生了什么、记录在哪里、可以怎么办），不打回溯（[0039](./0039-user-facing-surfaces-no-internal-references.md)），处理过使用方中断时仍按信号取 130 或 143（[0031](./0031-job-lifecycle-states-and-severity.md) 决定五）；第一种情形里执行中的 job 留在 `running`，被处置时怎样记见决定三「保存明细失败」条。说明按记录是否已是终态分两种：本进程的写已使 run 成为终态（为组装而读的那一次失败，含被点名的那一份读不到）时运行态已是终态、此后不再改变，说明指向 `status`、写明不必重新执行，免得使用方为一次读失败重付一次执行；其余情形 run 停在未结束、这个进程退出之后没有推进器，说明执行已停止，请使用者排除存储问题，用说明里给出的 `settle-runs` 整条命令把这个 run 记为已结束，再重新执行（本机后台推进进程读写记录失败而退出时同一说法，经它的日志给出；出口的规则见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策八「管它的进程退出而 run 未结束的出口」一条）。落库服务对外给出「本进程的写是否已使 run 成为终态」这项事实，组合根据它选说明。退出码只承诺非零、不另设一个专门的值：这次执行没有输出汇总，脚本按非零分流，记录用 `status` 读。

## 现在做 / 留口子

- **决定一~五（实时写接缝）**：`JobSink` port + `schedule.on_job_complete`/`on_event`；`core/gherkai_core/persist.py` 的
  `RunPersistence`（单一 store 锁）；RunStore 生命周期写入口的 local adapter（建 run 经暂存目录与改名，此后的各写入口在同一把文件锁内，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）；`RunState.jobs` 改 Map；cli 接 `RunPersistence`（含 RUNNING 中间态）。
- **决定六（云端 adapter）**：`DynamoDBRunStore`（连同提交记录的 jobs 对象在产物桶里的存取）+ `S3ResultStore` + `S3ReportStore`，单测以 moto 全程 mock，与 local adapter 对拍。组合根接线见决定七。
- **决定七（cli 接线 cloud）**：`--backend {local,cloud}` 组合根装配（两后端下沉 `compose`，详见 [0016](./0016-execution-architecture-core-lib-run-model.md)「cli `--backend {local,cloud}`」节）+ Store 的 preflight 探活 + jobs 对象的存取按命令装配 + 失败退出码分层（退出码 2 为未开始执行，非零为本机运行期）。
- **留口子不做 → 多写者（已在 [0034](./0034-detached-batch-reconciler.md) 落地）**：无状态批量运行下 reconciler 跨进程/跨 Lambda 并发直写 `RunState`，机制（条件写，[0034](./0034-detached-batch-reconciler.md) 机制三）见下「重议」条。续跑/部分重跑的 attempt 维度仍留口子（0034 未涉及）。

## 重议

- ~~若未来「编排进程外的写者」出现……需 owner/lease + 条件更新，另立 ADR~~ **→ 已落地为 [0034](./0034-detached-batch-reconciler.md)**（无状态批量运行：CLI 脱离后 reconciler（Lambda/后台推进进程）替代编排进程、直接从 events 表推演并写 `RunState`，正是「编排进程外的多写者」）。落地方案比当初预告的「owner/lease」更轻：**用 `high_water_mark` 条件写**（`RunState` 带已处理 max seq，写时 `:hwm >= 库中 hwm` 才成功，stale 实例的写被 `ConditionalCheckFailedException` 挡）+ 记下 job 终态的写与结束写以写入序号为条件（[0034](./0034-detached-batch-reconciler.md) 机制三②），无需 lease 租约。真 DDB 实测挡住了 stale 快照把 `passed` 刷回 `running` 的 lost-update（[0034](./0034-detached-batch-reconciler.md) 机制三 + 地基实测）。
- **没被点名的明细占用的存储成为实际问题**时：再议清理（决定三「点名」条：没被点名的明细不读、不列、不清理）。
