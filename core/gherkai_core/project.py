"""纯归约投影（ADR 0034）：events → JobResult/RunState，无 I/O、无执行编排、不 import boto3。

无状态批量运行（[0034](../../docs/adr/0034-detached-batch-reconciler.md)）的 core 侧纯函数层：reconciler
（cloud Lambda / local per-run 进程两宿主）从 events 表全量重放某 run 的事件，经这里纯推演出 RunState +
各 JobResult，再由 adapter 侧条件写落库、CAS 推进。**副作用（CAS/RunTask/PutItem/落库）全在 adapter/
组合根，本模块只吐「当前状态」与「建议动作」**（ADR 0034 core 拆分节；守 0026 纯 reducer 红线）。

与 schedule 的关系：`reduce_event` 是从 `schedule._Worker._reduce` 提炼的**同一份**单事件归约逻辑
（schedule 现 delegate 到此，零行为变化）——同步 `run` 路径与无状态 `submit` 路径共用一份归约码，不复制。
schedule 沿事件流实时喂；reconciler 从持久 events 全量重放喂。两条路径喂同一个纯函数。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from gherkai_core.model import (
    TERMINAL_STATUSES,
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
    SessionClosed,
    SessionOpened,
    SessionRecord,
    Status,
    StepDone,
    StepResult,
    StepSkipped,
    StepStarted,
    _NON_VERDICT,
)
from gherkai_core.wire import EX_WORKER_NETWORK


# ============================================================================
# 时长追踪累积态（从 schedule._Timing 提炼——同一形状，供 reduce_event 跨事件累积）
# ============================================================================


@dataclass
class Timing:
    """单个 scope 执行过程中各级起始时间戳 + 暂存的 step 结果（core 算墙钟时长用，ADR 0024）。

    从 `schedule._Timing` 提炼到 gherkai_core.project（reduce_event 的伴随累积态）。schedule 侧 `_Timing`
    保留为本类的别名（`_Timing = Timing`），零行为变化。
    """

    scope_start: float | None = None
    scenario_start: dict[str, float] = field(default_factory=dict)
    step_start: dict[tuple[str, int], float] = field(default_factory=dict)
    steps: dict[str, list[StepResult]] = field(default_factory=dict)  # scenario_id → 暂存 StepResult
    # 代表会话是否已由 scope_started 锁定（ADR 0051 决策 4 / 0024 sessionId 取值优先级）：锁定后任何 session_opened 都不改写
    session_locked: bool = False
    # 见过任何事件（scenario_started / step 事件 / scenario_done）的 scenario：scope 级 error 时据此判「零事件」才合成 SKIPPED
    seen_scenarios: set[str] = field(default_factory=set)


def representative_session(current: str | None, locked: bool, event: Event) -> tuple[str | None, bool]:
    """代表会话（JobState / JobResult 的 session_id）的取值规则（ADR 0051 决策 4 / 0024 sessionId 取值优先级）——
    reduce_event 与 persist.on_event 共用这一份，两条路径不各写一套。

    scope_started 带 sessionId 即为执行会话、一经取到锁定；锁定前取最近一条 origin 不是 attempted 的 session_opened
    （换台重建时后到的覆盖先到的）；attempted 永不写入、不覆盖已有值；scope_done 只在还没有值时补。任何路径都不用 None
    覆盖已有值。返回 (新的代表会话, 新的锁定状态)。"""
    if isinstance(event, ScopeStarted):
        if event.session_id is not None:
            return event.session_id, True
        return current, locked
    if isinstance(event, SessionOpened):
        if locked or event.origin == "attempted" or event.session_id is None:
            return current, locked
        return event.session_id, locked
    if isinstance(event, ScopeDone):
        if current is None and event.session_id is not None:
            return event.session_id, locked
        return current, locked
    return current, locked


def _find_session(sessions: list[SessionRecord], session_id: str | None, name: str) -> SessionRecord | None:
    """按配对键找会话记录（ADR 0024「配对键是 sessionId，缺省时回退为 name」）：事件带 sessionId 时先按它找；找不到或事件不带时
    按会话名找，但只配对双方至少一侧没有 sessionId 的记录——同名而 ARN 不同的两条真实会话不混为一条。"""
    if session_id is not None:
        for s in sessions:
            if s.session_id == session_id:
                return s
    for s in sessions:
        if s.name == name and (s.session_id is None or session_id is None):
            return s
    return None


def reduce_event(
    event: Event,
    result: JobResult,  # 就地累积
    scenario_status: dict[str, Status],
    timing: Timing,
    now: float,
) -> None:
    """把单个 worker 事件归约进 JobResult（就地累积，ADR 0024/0026）。

    **这是 `schedule._Worker._reduce` 提炼出的同一份逻辑**（schedule delegate 到此）。代表会话按 ADR 0024 的取值优先级：
    scope_done 只在还没有值时补、不覆盖 scope_started 已取到的值（此前曾覆盖，属桌面可见变化、记在 CHANGELOG）。
    now 是事件到达 core 的墙钟（同步路径下取 schedule 注入的 clock()；无状态路径下由 reconciler 从 events
    表 item 的 emit 时刻还原）。纯函数：只改传入的 result/scenario_status/timing，无 I/O。
    会话事件（ADR 0051 决策 4、7）在这里归约成 result.sessions 并按代表会话规则更新 result.session_id；scope 级 error
    （scope_done.status == error）在这里对零事件的 scenario 合成 SKIPPED 明细——两条归约路径的明细出自同一份代码。
    """
    # 代表会话（ADR 0051 决策 4）：与 persist.on_event 共用同一规则函数
    result.session_id, timing.session_locked = representative_session(result.session_id, timing.session_locked, event)
    if isinstance(event, (ScenarioStarted, StepStarted, StepDone, StepSkipped, ScenarioDone)):
        timing.seen_scenarios.add(event.scenario_id)
    # started 事件：记各级起始时间戳（now 是事件到达 core 的墙钟，ADR 0024）
    if isinstance(event, ScopeStarted):
        timing.scope_start = now
    elif isinstance(event, SessionOpened):
        # 每个会话一项，按配对键去重（同一 ARN 重发不重复登记）；attempted 的尝试也进清单（session_id 为 None、只有名）；
        # device 原样留在记录上（scope 表头由它派生，ADR 0051 决策 8）
        rec = _find_session(result.sessions, event.session_id, event.name)
        if rec is None:
            result.sessions.append(SessionRecord(session_id=event.session_id, name=event.name, origin=event.origin, device=event.device))
        else:
            if rec.session_id is None and event.session_id is not None:
                rec.session_id = event.session_id  # 按名命中的记录此前没有 ARN：补上，之后同名异 ARN 的会话才不会再并进这一条
            if rec.device is None and event.device is not None:
                rec.device = event.device
    elif isinstance(event, SessionClosed):
        rec = _find_session(result.sessions, event.session_id, event.name)
        if rec is None:
            # 协议要求先 opened 再 closed；没见过 opened 的 closed 仍登记（会话确实存在过，计量与确认集都要算它），
            # origin 按 created 记——这是 worker 违约下的保守补全，不丢任何会话事实。
            rec = SessionRecord(session_id=event.session_id, name=event.name, origin="created")
            result.sessions.append(rec)
        if rec.session_id is None and event.session_id is not None:
            rec.session_id = event.session_id  # 按名配上的记录此前没有 ARN：补上，origin 不改
        rec.release = event.release
        rec.observed_s = event.observed_s
        rec.provider_minutes = event.provider_minutes
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
                       message=event.message,  # step 级失败原因原文（ADR 0042 决策三）
                       report_refs=event.report_refs)  # step 级产物指针原样搬入（内容见 model.StepDone.report_refs 注释）
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
        sr = ScenarioResult(
            scenario_id=event.scenario_id,
            status=event.status,
            steps=timing.steps.get(event.scenario_id, []),
            duration_ms=(now - ss) * 1000.0 if ss is not None else None,
            report_refs=event.report_refs,
        )
        # 同一 scenario 只留一条记录：scope 级 error 后已合成 SKIPPED 的 scenario 若仍收到 scenario_done（worker 违约），
        # 以真实判定取代合成记录，不让同一 scenario_id 出现两条
        existing = next((i for i, x in enumerate(result.scenarios) if x.scenario_id == event.scenario_id), None)
        if existing is None:
            result.scenarios.append(sr)
        else:
            result.scenarios[existing] = sr
    elif isinstance(event, ScopeDone):
        # 代表会话已由上面的 representative_session 处理（scope_done 只在还没有值时补，不覆盖已取到的值，ADR 0024）。
        if event.report_refs:
            result.report_refs = result.report_refs + event.report_refs
        if timing.scope_start is not None:
            result.duration_ms = (now - timing.scope_start) * 1000.0
        if event.status == Status.ERROR:
            synthesize_skipped(result, timing)


def synthesize_skipped(result: JobResult, timing: Timing) -> None:
    """scope 级 error 后的明细补全（ADR 0051 决策 4；0031 决定一、六）：对 definition 中**零事件**的 scenario 按定义顺序追加
    scenario 级 SKIPPED，其全部 step 为 SKIPPED(shortcircuited=False, duration_ms=None)。在途 scenario（见过任何事件而没有
    scenario_done）整条不合成、其未开始的 step 也不合成；不写 scenario_status（合成的 SKIPPED 不进 _aggregate）。
    明细只依据已收到的完成事实：之后到达的超时、abort 或非零退出只改变判定与归因，不撤销这里合成的明细。"""
    done = {sr.scenario_id for sr in result.scenarios}
    for sc in result.job.scenarios:
        if sc.id in done or sc.id in timing.seen_scenarios:
            continue
        result.scenarios.append(ScenarioResult(
            scenario_id=sc.id, status=Status.SKIPPED,
            steps=[StepResult(index=st.index, status=Status.SKIPPED, duration_ms=None, shortcircuited=False) for st in sc.steps],
        ))


# ============================================================================
# 无状态批量运行投影（ADR 0034）：全量 events records → RunState + 各 JobResult
# ============================================================================


# 平台侧退出哨兵（ADR 0034 机制二及其「launch 失败补偿」「退出码缺失」两条推论）：worker 进程**没有**给出退出码的两种形态
# 都落它——①tick 起 task 失败（RunTask 抛/Popen OSError，进程根本没起）；②观察者收到 STOPPED 却缺 exitCode（容器没能开始运行，
# 如拉不到镜像）。非 0 即走「退出码非零 → ERROR」既有谓词，值本身不进任何分支判断；选 255 避开 worker 真实语义码（如网络故障退出码 80），
# 只为日志/归因可辨识「这是平台侧起不来、不是 worker 执行中崩溃」。core 单点定义，tick 与观察者 Lambda 都 import 本常量、别各抄一份。
PLATFORM_FAILED_EXIT = 255


@dataclass(frozen=True)
class TaskExited:
    """平台侧退出观察者写入 events 表**独立键空间**的退出记录（ADR 0034 机制一/二）。

    **不是 worker 的 wire 事件**（不在 model.Event union、不进 wire.py 的 worker↔core 协议）——它由
    平台侧观察者产生：云端后端下是 ECS Task STOPPED 事件的极薄 Lambda（从事件 payload 读 exitCode）；
    本机后端下是 per-run 进程 `proc.wait()`。走独立键空间（云端后端下是保留高位数值 SK 加属性 `item_type='exit'`——
    events 表 SK 是 NUMBER、字符串前缀结构上不可行；本机后端下是独立 `exits` 表；见 ADR 0034 机制一），不占
    worker 的连续数值 seq 段，故不参与 adapter 的单调 seq/断号检测（机制一：免撞号覆盖 scope_done）。

    exit_code 为 None 表示退出码未知（有退出记录、却没取到码）。**不是宽限态**（ADR 0034 机制二「退出码缺失」条）：
    观察者只有一次机会看到 STOPPED，缺码时它应落 `PLATFORM_FAILED_EXIT` 哨兵 + reason；仍写 None 的（老版本观察者/
    未知写者）由 `_job_status` 判 ERROR，绝不判 RUNNING（否则 run 永久 wedge）。
    reason：平台侧归因（云端后端下是 `stopCode: stoppedReason`），只在观察者落哨兵时带；投影进 job message 给使用方看。
    """

    scope_id: str
    exit_code: int | None = None
    # 超时归因（ADR 0034「job timeout」节）：本次退出是否由 timeout 处置的 stop 所致。
    # local 由 launcher 的 timer 标志传入；cloud 经 StopTask reason → STOPPED 事件 detail.stoppedReason
    # 哨兵串还原。终结函数据此取 stop_reason = timeout（内容完整的干净退出除外，见 finalize_job）。
    timed_out: bool = False
    reason: str | None = None  # 平台侧归因（观察者落哨兵时带），见类 docstring


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
    2. 终结判定（机制二「终结函数与真值表」，单一真源是 `finalize_job`，`_job_status` 是它的薄委托，别在两处各写一份）：
       有退出记录时进程终止本身即终态信号（stop_reason 为 timeout / abort 且内容不完整 → 对应终态；退出码非零或未知 → ERROR；
       exit==0 且见 scope_done → scope 级 error 或 scenario 归约终态；exit==0 无 scope_done（含零事件）→ ERROR）；无退出记录时
       见 scope_started 或非 attempted 的 session_opened → RUNNING、否则 PENDING（只有 attempted 的 session_opened 仍为 PENDING）。
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
            # claimed_at 只由 try_claim_job 落库、事件推演不出——从 baseline（prior）带回，
            # 否则 project_state 的整 job 覆盖会把它抹掉（ADR 0034 job timeout 起算点）。
            claimed_at=prior.claimed_at if prior else None,
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

    events 段按 seq 升序喂 reduce_event 归约出完整 JobResult；退出记录（独立键空间）给终结函数退出信息与 stop_reason。
    返回 (完整 JobResult, 派生 status, 该 scope 的 worker 段 max seq)。JobResult.status 会被派生 status 覆盖
    （reduce 期只累积 scenario 明细，最终 job 态由 finalize_job 的真值表定，机制二）。
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
    saw_scope_started = saw_session_opened = False
    scope_done: ScopeDone | None = None
    for r in evs:
        ev = r.event
        if ev is None:  # evs 已按 kind=='event' 且 event 非 None 过滤，这里显式窄化（类型层面）
            continue
        if isinstance(ev, ScopeStarted):
            saw_scope_started = True
        if isinstance(ev, SessionOpened) and ev.origin != "attempted":
            saw_session_opened = True  # 只有 attempted 的 session_opened 不算 RUNNING（ADR 0051 决策 4），与同步路径的实时落库一致
        if isinstance(ev, ScopeDone):
            scope_done = ev
        reduce_event(ev, result, scenario_status, timing, r.emit_ts or 0.0)
    exits = [r.exited for r in recs if r.kind == "exit" and r.exited is not None]
    exited = exits[0] if exits else None
    # 终结判定只由终结函数写（ADR 0034 机制二）：reduce_event 只累积明细、成本与会话记录。无状态路径没有 fail-fast，
    # stop_reason 只可能是 none 或 timeout（推进器写退出记录时带 timed_out）。
    term = finalize_job(
        job=job,
        stop_reason="timeout" if (exited is not None and exited.timed_out) else "none",
        exited=exited is not None,
        exit_code=exited.exit_code if exited is not None else None,
        exit_reason=exited.reason if exited is not None else None,
        saw_scope_started=saw_scope_started,
        saw_session_opened=saw_session_opened,
        scope_done=scope_done,
        scenario_status=scenario_status,
        sessions=result.sessions,
    )
    result.status, result.error_type, result.message = term.status, term.error_type, term.message
    apply_device_metering(result)  # 设备计量两键（ADR 0051 决策 7）：桌面 job 保持 None
    return result, term.status, max_seq


# ============================================================================
# 终结函数与真值表（ADR 0034 机制二）：同步 schedule 与无状态 project 两条路径共用，判定逻辑只此一份
# ============================================================================


@dataclass(frozen=True)
class Termination:
    """终结函数的输出：job 的判定、归因与消息。"""

    status: Status
    error_type: str | None
    message: str | None


# U 非空时追加到 job message 的释放提示，按 job 目标给（ADR 0051 决策 4、7；0034 机制二）：设备 job 的那句逐字取自 ADR 0034；
# 桌面会话是 worker 自持的 AgentCore 浏览器会话，提示不提设备控制台。
DEVICE_RELEASE_FAILED_HINT = "远程访问会话未能确认停止，可能仍在计费，请在设备控制台核对并手动停止"
DESKTOP_RELEASE_FAILED_HINT = "AgentCore 浏览器会话未能确认停止，可能仍在计费，请在 Amazon Bedrock AgentCore 控制台核对并手动停止"


def unconfirmed_sessions(sessions: list[SessionRecord]) -> list[SessionRecord]:
    """未确认集 U（ADR 0034 机制二）：发过 session_opened 而没有 release: confirmed 的会话；attempted 的尝试天然在内。"""
    return [s for s in sessions if not s.confirmed]


def _release_failed_message(unconfirmed: list[SessionRecord], *, device: bool) -> str:
    """U 非空时追加到 job message 的产品语言提示：先按目标给释放提示，再列出会话名；attempted 的尝试另列为「结果未知的创建尝试」。"""
    created = [s.name for s in unconfirmed if s.origin != "attempted"]
    attempted = [s.name for s in unconfirmed if s.origin == "attempted"]
    parts = [DEVICE_RELEASE_FAILED_HINT if device else DESKTOP_RELEASE_FAILED_HINT]
    if created:
        parts.append("未确认停止的会话：" + "、".join(created))
    if attempted:
        parts.append("结果未知的创建尝试：" + "、".join(attempted))
    return "；".join(parts)


def device_metering(sessions: list[SessionRecord]) -> tuple[float, int]:
    """设备计量合计（ADR 0051 决策 7）：origin 为 created / discovered 且 observed_s 非 None 的各项之和，与同类 origin 里
    observed_s 为 None 的项数（含没收到 session_closed 的会话）；attempted 两者都不计。observed_s 为 0.0 计入合计、不计缺失。"""
    real = [s for s in sessions if s.origin != "attempted"]
    return (sum(s.observed_s for s in real if s.observed_s is not None),
            sum(1 for s in real if s.observed_s is None))


def is_device_job(job: Job) -> bool:
    """job 的测试目标是否为设备（判据只取 Job 上的目标字段，ADR 0048）。计量两键、释放提示与 job 级重试门槛都按它分，
    不按有没有会话事件分：桌面与设备 job 都可能带会话记录（ADR 0051 决策 4）。"""
    target = getattr(job, "target", None)
    return target is not None and getattr(target, "device", "desktop") != "desktop"


def apply_device_metering(result: JobResult) -> None:
    """给设备 job 的 JobResult 填两个设备计量键（ADR 0051 决策 7）：只按 job 目标判，不按有没有会话记录判——桌面 worker 也发会话事件
    （决策 4），AgentCore 浏览器会话不是设备分钟，按会话记录判会让每个桌面 job 多出这两键。设备 job 没有会话记录时两键也成对给出（合计 0、
    缺计量 0）；桌面 job 两键保持 None（序列化省键）。"""
    if is_device_job(result.job):
        result.device_observed_s, result.device_observed_missing = device_metering(result.sessions)


def finalize_job(
    *,
    job: Job,
    stop_reason: str,
    exited: bool,
    exit_code: int | None,
    exit_reason: str | None,
    saw_scope_started: bool,
    saw_session_opened: bool,
    scope_done: ScopeDone | None,
    scenario_status: dict[str, Status],
    sessions: list[SessionRecord],
) -> Termination:
    """终结函数（ADR 0034 机制二「终结函数与真值表」）：按行序取第一个命中的行给出 (status, error_type, message)。

    输入：stop_reason 取 none、timeout、abort 之一（推进器首次仲裁落定的主动处置）；退出信息（exited 为 False 即未退出；exited
    且 exit_code 为 None 即退出码未知）；是否见到 scope_done 及其 status / errorType / message；scenario 判定集；会话记录
    （未确认集 U 由此算出）。exit_reason 是平台侧归因或异常文本，只进消息。saw_session_opened 只计 origin 不是 attempted 的
    session_opened：只有结果未知的创建尝试时未退出行判 PENDING（ADR 0051 决策 4）。
    内容完整（干净退出且发了 scope_done）后停止原因不再改写判定：判定已成，收尾拖过预算只改变推进器是否催停，不改结论——
    同步路径收到 scope_done 后不再落定停止原因，无状态路径的 timed_out 记录遇到它同样不改判，两条路径由这里同一条件保证；
    非零退出或退出码未知不算内容完整，照常受前两行约束。
    U 非空时不论判定为何，归因改 release_failed 的行保留原因消息，message 都追加产品语言提示并列出会话名；这条规则对桌面与设备
    job 相同，只有提示那一句按目标给（ADR 0051 决策 4）。
    两条归约路径只负责准备输入，判定逻辑不写第二份。"""
    unconfirmed = unconfirmed_sessions(sessions)
    budget = f"（预算 {job.timeout_s:g}s，已中止）" if job.timeout_s else "（已中止）"
    content_complete = exited and exit_code == 0 and scope_done is not None
    if stop_reason == "timeout" and not content_complete:
        status, error_type, message = Status.ERROR, "timeout", f"job 超时{budget}"
    elif stop_reason == "abort" and not content_complete:
        status, error_type, message = Status.ABORTED, None, "fail-fast：其他 job 失败，本 job 被中止"
    elif not exited:
        status = Status.RUNNING if (saw_session_opened or saw_scope_started) else Status.PENDING
        error_type, message = None, None
    elif exit_code is None or exit_code != 0:
        status = Status.ERROR
        said = scope_done.status == Status.ERROR if scope_done is not None else False  # worker 先报了 scope 级 error 再非零退出
        if exit_code == EX_WORKER_NETWORK:
            error_type = "network_error"
            message = "worker 建连失败（网络/SSL 瞬时故障），退出码 80" + (f"：{exit_reason}" if exit_reason else "")
        elif exit_code == PLATFORM_FAILED_EXIT:
            # 平台侧哨兵（无状态路径观察者缺退出码时落它）；本机 worker 真以 255 退出也走这行，措辞对两种来源都成立
            why = f"：{exit_reason}" if exit_reason else "——详见 worker 日志或部署侧日志"
            error_type, message = "engine_error", f"worker 未能启动或未正常结束（退出码 255；平台侧未取到退出码时也记为 255）{why}"
        elif exit_code is None:
            error_type = "engine_error"
            # exit_reason 由调用方带上下文写好（同步路径：「worker 异常：…」/「起 worker 失败：…」；平台侧：观察者的归因）
            message = exit_reason if exit_reason else "worker 已终止但退出码未知——无法判定为通过，按错误处理"
        elif said:
            error_type, message = "engine_error", f"worker 随后非正常退出（exit {exit_code}）"
        else:
            error_type, message = "engine_error", f"worker 非正常退出（exit {exit_code}；事件流里没有失败原因——详见 worker 日志）"
        if said:
            # 原因消息保留 worker 报的那句（设备 worker 有未确认会话时以 1 退出，ADR 0051 决策 5），退出的说明接在后面
            message = f"{scope_done.message or scope_done.error_type}；{message}"
        if unconfirmed:
            error_type = "release_failed"  # 归因改释放失败，退出原因的消息保留、提示在下面追加
    elif scope_done is None:
        status, error_type = Status.ERROR, "engine_error"
        message = "worker 正常退出但没有报完这次运行的结果——按错误处理（详见 worker 日志）"
    elif scope_done.status == Status.ERROR:
        status, error_type, message = Status.ERROR, scope_done.error_type, scope_done.message
        if unconfirmed:
            error_type = "release_failed"  # worker 报的原因消息保留
    elif not scenario_status:
        status, error_type, message = Status.ERROR, "engine_error", "worker 未报告任何 scenario 判定"
    else:
        status = _aggregate(list(scenario_status.values()))
        error_type, message = None, None
        if unconfirmed:  # worker 违约：判定完整却有会话未确认停止 → 改判 ERROR、release_failed
            status, error_type = Status.ERROR, "release_failed"
    if unconfirmed:
        hint = _release_failed_message(unconfirmed, device=is_device_job(job))
        message = f"{message}；{hint}" if message else hint
    return Termination(status=status, error_type=error_type, message=message)


class NonTerminalSnapshot(RuntimeError):
    """收尾快照里有 job 仍非终态（ADR 0031 决定一·补：JobResult.status 只许终态，强制点在 project_full）。

    正常到不了：tick 只在 plan_next 判全终态时才聚合。到了就说明本次读到的 events 快照落后于判定依据（或写者违约），
    本轮不落任何判定真值、让触发源重试——绝不把 running/pending 写进 jobs/*.json。"""


def project_full(meta: RunMeta, records: list[EventRecord], *, run_duration_ms: float | None = None) -> RunResult:
    """从全量 records 推演出**完整 RunResult**（含各 JobResult 明细，ADR 0034）——finalize 收尾用。

    与 `project`（轻量 RunState、供实时投影写/plan_next）共用 `_reduce_scope` 归约；差别只在保留完整明细
    （scenarios/steps/cost/report_refs）。tick 在 finalize **CAS 之前**用它落 ResultStore（判定真值，ADR 0030 决定三
    写序）；宿主在 done 后用它聚合 RunReport。**守 ADR 0031 不变量**：任一 job 非终态即抛 NonTerminalSnapshot、一份
    判定都不落（前置态绝不进 jobs/*.json）——tick 只在 plan_next 判全终态时才调本函数，正常到不了那一步。run 级 status 用真实聚合终态（此处是收尾、非投影，
    可落终态，与 project_state 的钳制不同）。收尾前提是全 job 终态、每个 job 至少有一条退出记录，故正常没有「无 record 的
    job」；防御分支：没 record 的 job 不臆造明细、不进 RunResult.jobs（与同步 schedule 不同——那边从未 spawn 的 job 记
    SKIPPED，detached 没有 fail-fast、不产生这一态）。run 级 duration_ms 由宿主按 RunState started_at→ended_at 算好经
    `run_duration_ms` 传入（ADR 0024「三级执行时长」detached 条；core 不取时钟、不解析时间戳），缺则 None。
    """
    by_scope: dict[str, list[EventRecord]] = {}
    for r in records:
        by_scope.setdefault(r.scope_id, []).append(r)

    job_results: list[JobResult] = []
    for job in meta.jobs:  # 按 definition 序（稳定输出）
        recs = by_scope.get(job.scope_id)
        if not recs:
            continue  # 没起过的 job 无明细可落（reconciler 未 launch 或 pending）——不臆造
        jr, status, _seq = _reduce_scope(job, recs)
        if status not in TERMINAL_STATUSES:
            raise NonTerminalSnapshot(
                f"收尾聚合读到 job {job.scope_id!r} 仍为 {status.value}：本次事件快照尚未到终态，本轮不落判定、等重放")
        job_results.append(jr)

    run_status = _aggregate([jr.status for jr in job_results])
    tok = [jr.total_tokens for jr in job_results if jr.total_tokens is not None]
    tw = [jr.total_time_worked_s for jr in job_results if jr.total_time_worked_s is not None]
    return RunResult(
        run_meta=meta,
        status=run_status,
        jobs=job_results,
        duration_ms=run_duration_ms,
        total_tokens=sum(tok) if tok else None,
        total_time_worked_s=sum(tw) if tw else None,
        **run_device_metering(job_results),
    )


def run_device_metering(job_results: list[JobResult]) -> dict:
    """run 级设备计量合计（ADR 0051 决策 7）：各设备 job 两键之和；没有设备 job 时两键都是 None（序列化省键）。
    同步 schedule 与无状态 project_full 共用这一份写法。"""
    dev = [jr for jr in job_results if jr.device_observed_s is not None or jr.device_observed_missing is not None]
    if not dev:
        return {"device_observed_s": None, "device_observed_missing": None}
    return {"device_observed_s": sum(jr.device_observed_s or 0.0 for jr in dev),
            "device_observed_missing": sum(jr.device_observed_missing or 0 for jr in dev)}


def _job_status(
    saw_scope_started: bool,
    saw_scope_done: bool,
    exited: TaskExited | None,
    scenario_status: dict[str, Status],
    *,
    saw_session_opened: bool = False,
    scope_done_status: Status | None = None,
    sessions: list[SessionRecord] | None = None,
) -> Status:
    """单个 job 的态——终结函数（`finalize_job`，ADR 0034 机制二真值表）的薄委托，只取 status；保留此名供既有引用与测试。

    下面的 docstring 记录的是「两件都要」谓词的来历与各分支的理由，判定逻辑本身在 finalize_job 一处。

    「两件都要」的**内容完整（scope_done）要求只对声称成功（exit==0）的进程成立**——退出码非零时进程非干净
    终止（崩溃/网络故障/SIGKILL），scope_done 本就不会来（worker 崩了没机会发），此时进程终止本身即终态信号，
    不能再等 scope_done（否则 crash job 永远 RUNNING、reconciler 死循环——实际运行 crash worker 复现）。

    **判定以「有无 task_exited」为一级键，不设 saw_scope_started 前置**（ADR 0034 机制二）——零事件 + exit==0
    （构造期 SIGTERM 干净退出，0024 设计内）若短路成 PENDING，会与已 claim 的 RUNNING 基线单调合并成永停
    RUNNING、run 永不收敛（对抗验证探针复现）：
    - 有 task_exited（进程已终止，退出即终态信号，不论生命周期到哪）：
        · exit_code != 0 → ERROR（崩溃/网络故障/SIGKILL/launch 失败哨兵；也防"发完 scope_done 又非0退出"
          的误报 PASSED）；
        · exit_code is None → ERROR（有退出记录却无码：不可判定为通过；机制二「退出码缺失」条——观察者本应落
          哨兵，此分支是防 wedge 的防御。曾判 RUNNING「等观察者补」，但 STOPPED 事件只来一次、永远补不上）；
        · exit_code == 0 且 saw_scope_done → scenario 归约的终态（passed/failed/error）；
        · exit_code == 0 但没 scope_done（含零事件干净退出）→ ERROR（内容不完整但进程说成功，两者矛盾，
          judged as error 比 running 死循环安全）。
    - 无 task_exited（进程还没终止）：见过 scope_started 或非 attempted 的 session_opened → RUNNING；否则 PENDING（还没起/还没写事件，
      或只有结果未知的创建尝试）。
    """
    probe_job = Job(scope_id="_", scope_name="_", engine="_", scenarios=())
    scope_done = ScopeDone(scope_id="_", status=scope_done_status,
                           error_type="engine_error" if scope_done_status == Status.ERROR else None,
                           message=None) if saw_scope_done else None
    return finalize_job(
        job=probe_job,
        stop_reason="timeout" if (exited is not None and exited.timed_out) else "none",
        exited=exited is not None,
        exit_code=exited.exit_code if exited is not None else None,
        exit_reason=exited.reason if exited is not None else None,
        saw_scope_started=saw_scope_started,
        saw_session_opened=saw_session_opened,
        scope_done=scope_done,
        scenario_status=scenario_status,
        sessions=sessions or [],
    ).status


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
    """终态归约（唯一一份，schedule 与本模块两路径共用——ADR 0031 决定三 / 0034「不复制归约逻辑」）：
    滤非终态判定后，任一 error→error；任一 failed→failed；否则 passed（空/全前置态也算 passed）。

    过滤 _NON_VERDICT（skipped/aborted 派生态 + pending/running 前置态）——run 级只看真正出了判定的
    job。把正确性钉在函数内、不依赖「skipped 必伴随 error」的外部不变量（防未来引入主动 skip 时
    全-skipped run 被误判 passed）。scenario 内归约喂的全是 worker 三态，过滤为 no-op。
    """
    verdicts = [s for s in statuses if s not in _NON_VERDICT]
    if any(s == Status.ERROR for s in verdicts):
        return Status.ERROR
    if any(s == Status.FAILED for s in verdicts):
        return Status.FAILED
    return Status.PASSED


def projected_run_status(jobs: dict[str, JobState]) -> Status:
    """投影写该落库的 run 级 status（ADR 0034 机制三）：投影里全 job 仍 pending → `pending`，否则 `running`。

    **投影不能落 `project` 算出的 run 级 status**——那是 `_aggregate` 的终态聚合值（见上：滤掉 pending/
    running，故连「全 job 还 pending」的 run 也吐 `passed`）；提前落 run 级终态会被 `try_finalize` 的单调
    条件写认成「已 finalize」而挡住 commit point（ADR 0030），run 永远 finalize 不了。

    **判据只看传入的 job 态、不读库、不看传入的 run 级值**：两个 RunStore adapter 须落同一规则，而 DDB 侧
    标量条件写发生在 per-job 条件写之前（那一刻库中 job 态还没更新、读它无意义），判据依赖库就没法对拍。
    真实 tick 流里已 claim 的 job 必在投影中现 `running`（`project` 以 RunStore 态为基线单调合并），故
    「全 pending」说明这个 run 还没起过任何 job——status 如实显示 `pending` 才有诊断价值（读到仍 pending
    就意味着推进可能没启动）。两端取值都是非终态，commit point 的专属性不受影响。
    """
    if all(js.status == Status.PENDING for js in jobs.values()):
        return Status.PENDING
    return Status.RUNNING


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
