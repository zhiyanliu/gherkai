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
    result,  # JobResult（就地累积；不标类型避免与 schedule 的循环 import）
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


def project(meta: RunMeta, records: list[EventRecord]) -> RunState:
    """从某 run 的**全量 events records** 纯推演出 RunState（ADR 0034 reconciler 核心，无 I/O）。

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
    # 先给 definition 里每个 job 一个 PENDING 占位（没有任何 record 的 job = 还没起，PENDING）
    for job in meta.jobs:
        jobs_state[job.scope_id] = JobState(scope_id=job.scope_id, status=Status.PENDING)
    job_by_scope: dict[str, Job] = {j.scope_id: j for j in meta.jobs}

    for scope_id, recs in by_scope.items():
        job = job_by_scope.get(scope_id)
        if job is None:
            continue  # record 指向 definition 外的 scope（不该发生）——忽略，不臆造 job
        # 单 scope 归约：worker 段事件按 seq 升序喂 reduce_event
        evs = sorted([r for r in recs if r.kind == "event" and r.event is not None],
                     key=lambda r: (r.seq if r.seq is not None else 0))
        for r in evs:
            if r.seq is not None:
                hwm = max(hwm, r.seq)
        result = JobResult(job=job, status=Status.PENDING)
        scenario_status: dict[str, Status] = {}
        timing = Timing()
        saw_scope_started = False
        saw_scope_done = False
        for r in evs:
            ev = r.event
            if isinstance(ev, ScopeStarted):
                saw_scope_started = True
            if isinstance(ev, ScopeDone):
                saw_scope_done = True
            reduce_event(ev, result, scenario_status, timing, r.emit_ts or 0.0)  # type: ignore[arg-type]
        # 退出记录（机制一/二）：独立键空间、无 seq，单独取
        exits = [r.exited for r in recs if r.kind == "exit" and r.exited is not None]
        exited = exits[0] if exits else None

        status = _job_status(saw_scope_started, saw_scope_done, exited, scenario_status)
        jobs_state[scope_id] = JobState(
            scope_id=scope_id, status=status, session_id=result.session_id,
        )

    run_status = _aggregate([js.status for js in jobs_state.values()])
    return RunState(
        run_id=meta.run_id,
        status=run_status,
        jobs=jobs_state,
        high_water_mark=hwm,
    )


def _job_status(
    saw_scope_started: bool,
    saw_scope_done: bool,
    exited: TaskExited | None,
    scenario_status: dict[str, Status],
) -> Status:
    """单个 job 的态（ADR 0034 机制二「两件都要」纯谓词）。

    - 连 scope_started 都没见 → PENDING（还没起/还没写事件）。
    - 见了 scope_started 但「两件」没齐（缺 scope_done 或缺 task_exited）→ RUNNING（会话已起、在跑）。
    - 「两件都要」齐（scope_done ∧ task_exited）→ 终态：
        · exit_code 非 0 → ERROR（进程非干净终止，即使 scope_done 说 passed 也不吞，防误报 PASSED）；
        · exit_code == 0 → scenario 归约的终态（passed/failed/error）。
      exit_code=None（宽限态未落值，罕见）→ 保守判 RUNNING（不轻易落终态，等观察者补 exitCode）。
    """
    if not saw_scope_started:
        return Status.PENDING
    if not saw_scope_done or exited is None:
        return Status.RUNNING
    if exited.exit_code is None:
        return Status.RUNNING  # 两件之一（exitCode）尚未落值 → 保守，不落终态
    if exited.exit_code != 0:
        return Status.ERROR  # 进程非干净终止：即使内容完整也判 error（防"发完 scope_done 又非0退出"误报）
    return _aggregate(list(scenario_status.values()))


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
