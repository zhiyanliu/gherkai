"""纯归约投影（ADR 0034）：events → JobResult/RunState，无 I/O、无执行编排、不 import boto3。

无状态跑批（[0034](../../docs/adr/0034-detached-batch-reconciler.md)）的 core 侧纯函数层：reconciler
（cloud Lambda / local per-run 进程两宿主）从 events 表全量重放某 run 的事件，经这里纯推演出 RunState +
各 JobResult，再由 adapter 侧条件写落库、CAS 推进。**副作用（CAS/RunTask/PutItem/落库）全在 adapter/
组合根，本模块只吐「当前状态」与「建议动作」**（ADR 0034 core 拆分节；守 0026 纯 reducer 红线）。

与 schedule 的关系：`reduce_event` 是从 `schedule._Worker._reduce` 提炼的**同一份**单事件归约逻辑
（schedule 现 delegate 到此，零行为变化）——同步 `run` 路径与无状态 `submit` 路径共用一份归约码，不复制。
schedule 沿事件流实时喂；reconciler 从持久 events 全量重放喂。两条路径喂同一个纯函数。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from core.model import (
    Event,
    Job,
    JobResult,
    JobState,
    RunMeta,
    RunResult,
    RunState,
    ScenarioDone,
    ScenarioResult,
    ScenarioStarted,
    ScopeDone,
    ScopeStarted,
    Status,
    StepDone,
    StepResult,
    StepSkipped,
    StepStarted,
    _NON_VERDICT,
)


# ============================================================================
# 时长追踪累积态（从 schedule._Timing 提炼——同一形状，供 reduce_event 跨事件累积）
# ============================================================================


@dataclass
class Timing:
    """单个 scope 跑批中各级起始时间戳 + 暂存的 step 结果（core 算墙钟时长用，ADR 0024）。

    从 `schedule._Timing` 提炼到 core.project（reduce_event 的伴随累积态）。schedule 侧 `_Timing`
    保留为本类的别名（`_Timing = Timing`），零行为变化。
    """

    scope_start: float | None = None
    scenario_start: dict[str, float] = field(default_factory=dict)
    step_start: dict[tuple[str, int], float] = field(default_factory=dict)
    steps: dict[str, list[StepResult]] = field(default_factory=dict)  # scenario_id → 暂存 StepResult


def reduce_event(
    event: Event,
    result: JobResult,  # 就地累积
    scenario_status: dict[str, Status],
    timing: Timing,
    now: float,
) -> None:
    """把单个 worker 事件归约进 JobResult（就地累积，ADR 0024/0026）。

    **这是 `schedule._Worker._reduce` 提炼出的同一份逻辑**（schedule delegate 到此，零行为变化）。
    now = 事件到达 core 的墙钟（同步路径 = schedule 的注入 clock()；无状态路径 = reconciler 从 events
    表 item 的 emit 时刻还原）。纯函数：只改传入的 result/scenario_status/timing，无 I/O。
    """
    # started 事件：记各级起始时间戳（now = 事件到达 core 的墙钟，ADR 0024）
    if isinstance(event, ScopeStarted):
        timing.scope_start = now
        # 会话血缘随首事件即落（ADR 0028）：超时/中止时 scope_done 不会到，但 session_id 此刻已记下。
        if event.session_id is not None:
            result.session_id = event.session_id
    elif isinstance(event, ScenarioStarted):
        timing.scenario_start[event.scenario_id] = now
    elif isinstance(event, StepStarted):
        timing.step_start[(event.scenario_id, event.step_index)] = now
    elif isinstance(event, StepDone):
        # scenario 判定只由 ScenarioDone 决定（守 ADR 0026 归约语义）——此处不写 scenario_status。
        # 累加 step 成本到 scope 级（ADR 0024）：core 只合计 engine 报的原生量、不算美元。
        cost = event.cost
        if cost is not None:
            if cost.tokens is not None:
                result.total_tokens = (result.total_tokens or 0) + cost.tokens
            if cost.time_worked_s is not None:
                result.total_time_worked_s = (result.total_time_worked_s or 0.0) + cost.time_worked_s
        st = timing.step_start.get((event.scenario_id, event.step_index))
        dur_ms = (now - st) * 1000.0 if st is not None else None
        timing.steps.setdefault(event.scenario_id, []).append(
            StepResult(index=event.step_index, status=event.status,
                       duration_ms=dur_ms, votes=event.votes, error_type=event.error_type,
                       report_refs=event.report_refs)  # step 级 trajectory 原样搬入（ADR 0027 下沉）
        )
    elif isinstance(event, StepSkipped):
        # scope 内短路（ADR 0031 决定六）：上游 error 后 worker 跳过本 step、没调 AI。
        # 本地构造 StepResult(status=SKIPPED, shortcircuited=True)——绝不写 scenario_status（severity 零污染）。
        st = timing.step_start.get((event.scenario_id, event.step_index))
        dur_ms = (now - st) * 1000.0 if st is not None else None
        timing.steps.setdefault(event.scenario_id, []).append(
            StepResult(index=event.step_index, status=Status.SKIPPED,
                       duration_ms=dur_ms, shortcircuited=True)
        )
    elif isinstance(event, ScenarioDone):
        scenario_status[event.scenario_id] = event.status
        ss = timing.scenario_start.get(event.scenario_id)
        result.scenarios.append(
            ScenarioResult(
                scenario_id=event.scenario_id,
                status=event.status,
                steps=timing.steps.get(event.scenario_id, []),
                duration_ms=(now - ss) * 1000.0 if ss is not None else None,
                report_refs=event.report_refs,
            )
        )
    elif isinstance(event, ScopeDone):
        # 仅在带值时设——别让 scope_done 的 None 覆盖已从 scope_started 捕获的血缘（ADR 0028）。
        if event.session_id is not None:
            result.session_id = event.session_id
        if event.report_refs:
            result.report_refs = result.report_refs + event.report_refs
        if timing.scope_start is not None:
            result.duration_ms = (now - timing.scope_start) * 1000.0


# ============================================================================
# 无状态跑批投影（ADR 0034）：全量 events records → RunState + 各 JobResult
# ============================================================================


@dataclass(frozen=True)
class TaskExited:
    """平台侧退出观察者写入 events 表**独立键空间**的退出记录（ADR 0034 机制一/二）。

    **不是 worker 的 wire 事件**（不在 model.Event union、不进 wire.py 的 worker↔core 协议）——它由
    平台侧观察者产生：cloud = ECS Task STOPPED 事件的极薄 Lambda（从事件 payload 读 exitCode）；
    local = per-run 进程 `proc.wait()`。走独立键空间（SK 前缀 `exit#`，不占 worker 的连续数值 seq 段），
    故不参与 adapter 的单调 seq/断号检测（机制一：免撞号覆盖 scope_done）。

    exit_code=None 仅用于「payload 缺 exitCode 的有界宽限态」（ADR 0032/0034 机制二兜底）——观察者应
    在写 task_exited 前有界等待 exitCode 落值，正常必带值（实测 4/4 含 SIGKILL 都带）。
    """

    scope_id: str
    exit_code: int | None = None


@dataclass(frozen=True)
class EventRecord:
    """events 表里一条记录的投影输入（ADR 0034）：reconciler 从表全量重放时，每条 record 携带的信息。

    worker 执行事件段：kind='event'，带 event（model.Event）+ seq（worker 段单调数值 SK）+ emit_ts（还原的
    worker emit 墙钟，供 reduce_event 算时长）。退出记录：kind='exit'，带 exited（TaskExited），无数值 seq。
    统一成一个输入类型，让 project 一次遍历既归约执行事件、又消费退出记录判「两件都要」。
    """

    scope_id: str
    kind: str  # 'event' | 'exit'
    seq: int | None = None          # 仅 kind='event'：worker 段单调数值 SK（机制一：HWM 只算这个段）
    event: Event | None = None      # 仅 kind='event'
    emit_ts: float | None = None    # 仅 kind='event'：worker emit 的墙钟（reduce_event 的 now）
    exited: TaskExited | None = None  # 仅 kind='exit'


def project(meta: RunMeta, records: list[EventRecord], baseline: RunState | None = None) -> RunState:
    """从某 run 的**全量 events records** 纯推演出 RunState（ADR 0034 reconciler 核心，无 I/O）。

    baseline（可选，当前 RunStore 的 state）：job 态**单调不倒退**的基线。已被 CAS claim 成 RUNNING、但
    worker 还没吐 scope_started 的 job，events 里看不到它、会被算成 PENDING——若无基线，投影写会把它降回
    PENDING、reconciler 下轮又重复 claim/launch（真 bug）。故有基线时：job 的投影态与基线态取**较推进者**
    （pending<running<终态，单调）——events 只推进、claim 的 running 不被降回。无基线（首 tick/纯投影）时全 PENDING 起。

    全量重放（非增量）→ 天然幂等、抗乱序、抗重投（ADR 0034 机制三前提）。步骤：
    1. 按 scope_id 分组 records；每组内 kind='event' 的按 seq 升序喂 reduce_event 归约出 JobResult；
    2. 「两件都要」纯谓词（机制二）：job 达终态 ⟺ 见到 scope_done（内容完整，reduce 已产出终态判定）
       ∧ 见到 task_exited 且 exit_code 表明干净终止（进程终止）。缺任一 → 该 job 仍 RUNNING（会话已起）
       或 PENDING（连 scope_started 都没见）。
    3. 聚合成 RunState：各 JobState（scope_id→status/session_id）+ run 总 status（_aggregate 终态）+
       high_water_mark（所有 scope 的 worker 段 max seq，机制三条件写用）。

    只吐状态、不碰 store、不决定"启不启下一个"（那是 plan_next + adapter 的事）。
    """
    by_scope: dict[str, list[EventRecord]] = {}
    for r in records:
        by_scope.setdefault(r.scope_id, []).append(r)

    jobs_state: dict[str, JobState] = {}
    hwm = 0
    # 占位：有 baseline 用基线态（保留已 claim 的 running——见 docstring），否则 PENDING。
    base_jobs = baseline.jobs if baseline is not None else {}
    for job in meta.jobs:
        base = base_jobs.get(job.scope_id)
        jobs_state[job.scope_id] = base if base is not None else JobState(
            scope_id=job.scope_id, status=Status.PENDING)
    job_by_scope: dict[str, Job] = {j.scope_id: j for j in meta.jobs}

    for scope_id, recs in by_scope.items():
        job = job_by_scope.get(scope_id)
        if job is None:
            continue  # record 指向 definition 外的 scope（不该发生）——忽略，不臆造 job
        result, status, max_seq = _reduce_scope(job, recs)  # 共用归约（与 project_full 单一真源）
        hwm = max(hwm, max_seq)
        # 单调合并（不倒退）：events 算出的态与基线态取较推进者。防「已 claim running 但 events 未到」被降回
        # pending（否则 reconciler 重复 launch，见 test_tick_idempotent）。终态一旦达成不被 running 覆盖。
        prior = jobs_state.get(scope_id)
        if prior is not None and _lifecycle_rank(prior.status) > _lifecycle_rank(status):
            status = prior.status
        jobs_state[scope_id] = JobState(
            scope_id=scope_id, status=status,
            session_id=result.session_id or (prior.session_id if prior else None),
        )

    run_status = _aggregate([js.status for js in jobs_state.values()])
    return RunState(
        run_id=meta.run_id,
        status=run_status,
        jobs=jobs_state,
        high_water_mark=hwm,
    )


def _reduce_scope(job: Job, recs: list[EventRecord]) -> tuple[JobResult, Status, int]:
    """单 scope 归约（project / project_full 共用一份，避免归约逻辑双写漂移）：

    events 段按 seq 升序喂 reduce_event 归约出完整 JobResult；退出记录（独立键空间）取 exit_code 判「两件都要」。
    返回 (完整 JobResult, 派生 status, 该 scope 的 worker 段 max seq)。JobResult.status 会被派生 status 覆盖
    （reduce 期只累积 scenario 明细，最终 job 态由 _job_status 的「两件都要」谓词定）。
    """
    evs = sorted([r for r in recs if r.kind == "event" and r.event is not None],
                 key=lambda r: (r.seq if r.seq is not None else 0))
    max_seq = 0
    for r in evs:
        if r.seq is not None:
            max_seq = max(max_seq, r.seq)
    result = JobResult(job=job, status=Status.PENDING)
    scenario_status: dict[str, Status] = {}
    timing = Timing()
    saw_scope_started = saw_scope_done = False
    for r in evs:
        ev = r.event
        if ev is None:  # evs 已按 kind=='event' 且 event 非 None 过滤，这里显式窄化（类型层面）
            continue
        if isinstance(ev, ScopeStarted):
            saw_scope_started = True
        if isinstance(ev, ScopeDone):
            saw_scope_done = True
        reduce_event(ev, result, scenario_status, timing, r.emit_ts or 0.0)
    exits = [r.exited for r in recs if r.kind == "exit" and r.exited is not None]
    exited = exits[0] if exits else None
    status = _job_status(saw_scope_started, saw_scope_done, exited, scenario_status)
    result.status = status
    return result, status, max_seq


def project_full(meta: RunMeta, records: list[EventRecord]) -> RunResult:
    """从全量 records 推演出**完整 RunResult**（含各 JobResult 明细，ADR 0034）——finalize 收尾用。

    与 `project`（轻量 RunState、供实时投影写/plan_next）共用 `_reduce_scope` 归约；差别只在保留完整明细
    （scenarios/steps/cost/report_refs）。reconciler finalize 抢到 commit 时用它落 ResultStore（判定真值）+
    ReportStore（RunReport 聚合），与同步 run 路径的产物对齐。run 级 status 用真实聚合终态（此处是收尾、非投影，
    可落终态，与 project_state 的钳制不同）。没 record 的 job（未起）不进 RunResult.jobs（同 schedule 只收跑过的）。
    """
    by_scope: dict[str, list[EventRecord]] = {}
    for r in records:
        by_scope.setdefault(r.scope_id, []).append(r)

    job_results: list[JobResult] = []
    for job in meta.jobs:  # 按 definition 序（稳定输出）
        recs = by_scope.get(job.scope_id)
        if not recs:
            continue  # 没起过的 job 无明细可落（reconciler 未 launch 或 pending）——不臆造
        jr, _status, _seq = _reduce_scope(job, recs)
        job_results.append(jr)

    run_status = _aggregate([jr.status for jr in job_results])
    tok = [jr.total_tokens for jr in job_results if jr.total_tokens is not None]
    tw = [jr.total_time_worked_s for jr in job_results if jr.total_time_worked_s is not None]
    return RunResult(
        run_meta=meta,
        status=run_status,
        jobs=job_results,
        total_tokens=sum(tok) if tok else None,
        total_time_worked_s=sum(tw) if tw else None,
    )


def _job_status(
    saw_scope_started: bool,
    saw_scope_done: bool,
    exited: TaskExited | None,
    scenario_status: dict[str, Status],
) -> Status:
    """单个 job 的态（ADR 0034 机制二「两件都要」纯谓词，含 worker 崩溃修正）。

    「两件都要」的**内容完整（scope_done）要求只对声称成功（exit==0）的进程成立**——exit≠0 时进程非干净
    终止（崩溃/网络码/SIGKILL），scope_done 本就不会来（worker 崩了没机会发），此时进程终止本身即终态信号，
    不能再等 scope_done（否则 crash job 永远 RUNNING、reconciler 死循环——真跑 crash worker 复现）。

    - 连 scope_started 都没见：
        · 有 task_exited 且 exit≠0 → ERROR（建连前就崩/网络码 80，scope_started 都没发；进程终止=终态）；
        · 否则 → PENDING（还没起/还没写事件）。
    - 见了 scope_started：
        · exited is None（进程还没终止）→ RUNNING（在跑）；
        · exit_code is None（终止了但 exitCode 未落值，宽限态）→ RUNNING（保守，等观察者补，机制二兜底）；
        · exit_code != 0 → ERROR（进程非干净终止，不论有无 scope_done——崩溃时它不会来；也防"发完 scope_done
          又非0退出"的误报 PASSED）；
        · exit_code == 0 且 saw_scope_done → scenario 归约的终态（passed/failed/error）；
        · exit_code == 0 但没 scope_done（干净退出却没发完内容，罕见）→ ERROR（内容不完整但进程说成功=矛盾，
          judged as error 比 running 死循环安全）。
    """
    # 进程已非干净终止 → error 终态（不论生命周期到哪、有无 scope_done）。放最前：crash/网络码/SIGKILL 统一收敛。
    if exited is not None and exited.exit_code is not None and exited.exit_code != 0:
        return Status.ERROR
    if not saw_scope_started:
        # 没起 + 没有（非0）退出信号 → 还是 pending（含 exited 但 exit==0 的怪异情形也留 pending，罕见、下轮补）
        return Status.PENDING
    if exited is None:
        return Status.RUNNING  # 会话已起、进程还在跑
    if exited.exit_code is None:
        return Status.RUNNING  # 终止了但 exitCode 未落值（宽限态）→ 保守，等观察者补
    # 到此 exit_code == 0（干净退出）
    if not saw_scope_done:
        return Status.ERROR  # 干净退出却没发完 scope_done：内容不完整、进程却说成功=矛盾 → error（不死循环）
    return _aggregate(list(scenario_status.values()))


def _lifecycle_rank(status: Status) -> int:
    """生命周期推进序（ADR 0034，仅用于 project 的单调合并、防态倒退）：pending < running < 任何终态。

    与 severity（ADR 0031，比较终态严重度）正交——这里只关心「推进到哪个阶段」，故所有终态同 rank=2
    （谁先到终态谁算数、不再被 running 覆盖；终态之间的选择由「两件都要」谓词一次定，不在此比较）。
    """
    if status == Status.PENDING:
        return 0
    if status == Status.RUNNING:
        return 1
    return 2  # 任何终态（passed/failed/error/skipped/aborted）


def _aggregate(statuses: list[Status]) -> Status:
    """终态归约（与 schedule._aggregate 同语义，ADR 0031 决定三）：滤非终态判定后，
    任一 error→error；任一 failed→failed；否则 passed（空/全前置态也算 passed）。

    过滤 _NON_VERDICT（skipped/aborted/pending/running）——run 级只看真正出了判定的 job。
    """
    verdicts = [s for s in statuses if s not in _NON_VERDICT]
    if any(s == Status.ERROR for s in verdicts):
        return Status.ERROR
    if any(s == Status.FAILED for s in verdicts):
        return Status.FAILED
    return Status.PASSED


# ============================================================================
# plan_next（ADR 0034 机制四）：纯决策——该启哪些 pending / 是否 finalize
# ============================================================================


@dataclass(frozen=True)
class Action:
    """reconciler 的建议动作（ADR 0034）——纯数据，adapter 侧据此做副作用（CAS/RunTask/finalize）。

    kind='start'：建议启这个 scope_id 的 job（adapter 侧 CAS pending→running 成功才真 RunTask/spawn）；
    kind='finalize'：所有 job 达终态、建议写 run 总 status + 聚合 report（adapter 侧条件写保 commit 恰一次）。
    """

    kind: str  # 'start' | 'finalize'
    scope_id: str | None = None  # kind='start' 时有


def plan_next(state: RunState, max_concurrency: int) -> list[Action]:
    """据当前 RunState 提议下一步动作（ADR 0034 机制四，纯函数、无副作用）。

    - 若所有 job 达终态（无 pending/running）→ [finalize]。
    - 否则：running < max_concurrency 且有 pending → 建议 start 若干 pending（补到并发上限）。
    **只提议**——真正的并发闸是 adapter 的 CAS 条件写（多 reconciler 实例并发提议同一 pending，只有 CAS
    成功的那个真启，其余被拒跳过，机制四）。故这里可乐观提议、不怕多提。
    """
    statuses = [js.status for js in state.jobs.values()]
    running = sum(1 for s in statuses if s == Status.RUNNING)
    pending = [sid for sid, js in state.jobs.items() if js.status == Status.PENDING]

    # 全终态（无 pending 无 running）→ finalize
    if not pending and running == 0:
        return [Action(kind="finalize")]

    actions: list[Action] = []
    slots = max(0, max_concurrency - running)
    for sid in pending[:slots]:
        actions.append(Action(kind="start", scope_id=sid))
    return actions
