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

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

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
from gherkai_core.run_deadline import RUN_DEADLINE_PASSED_MESSAGE, JobCutoff, TimeoutCause, deadline_of, job_cutoff
from gherkai_core.serialize import instant_from_iso
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
    now 是事件到达 core 的时刻（同步路径下取 schedule 注入的单调时钟 clock()；无状态路径下由 reconciler 从 events
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


# 平台侧退出哨兵（ADR 0034 机制二「退出码缺失」推论）：task 已停止、平台却没有给出 worker 退出码的两种形态都落它——①观察者收到
# STOPPED 却缺 exitCode（容器没能开始运行，如拉不到镜像；云端 tick 按观察者同一提取函数补写时同样）；②同步 `run --backend cloud`
# 下 task 已 STOPPED 却始终取不到 exitCode。
# 推进步骤起 job 失败时不落它：那时 worker 根本没有启动，补偿写退出码未知加启动失败的原因，与前台起 worker 失败交给终结函数的输入相同
# （ADR 0054 决策二后台推进条「时刻」），两条路径对同一个启动异常给出同一句说明。
# 非 0 即走「退出码非零 → ERROR」既有谓词；终结函数只在消息里按它给出平台侧归因的说法，判定不看具体值。选 255 避开 worker 真实语义码
# （如网络故障退出码 80），只为日志/归因可辨识「这是平台侧没给出退出码、不是 worker 执行中崩溃」。core 单点定义，观察者 Lambda、云端 tick
# 的补写与 FargateEngine 都 import 本常量、别各抄一份。
PLATFORM_FAILED_EXIT = 255


def platform_exit_reason(stop_code: str | None, stopped_reason: str | None) -> str:
    """ECS 没给出退出码时随 `PLATFORM_FAILED_EXIT` 一起落的归因串：`stopCode: stoppedReason`，缺一项只用另一项，两项都缺时用固定的
    兜底句（ADR 0034 机制二「退出码缺失」条）。

    唯一一份拼法：退出观察者与云端 tick 的补写（经 provider 包的同一提取函数）、同步路径的 `FargateEngine` 都调它，同一故障在同步与
    无状态两条路径下得到逐字相同的归因（各拼一份即两处漂移，理由同哨兵常量）。"""
    return ": ".join(x for x in (stop_code, stopped_reason) if x) or "平台未给出退出码与原因"


@dataclass(frozen=True)
class TaskExited:
    """平台侧退出观察者写入 events 表**独立键空间**的退出记录（ADR 0034 机制一/二）。

    **不是 worker 的 wire 事件**（不在 model.Event union、不进 wire.py 的 worker↔core 协议）——它
    主要由平台侧退出观察者产生：云端后端下是 ECS Task STOPPED 事件的极薄 Lambda（从事件 payload 读 exitCode），
    本机后端下是 per-run 进程 `proc.wait()`，本机同步 `run` 由 `EventRecordingEngine` 代写；另有 tick 的 launch
    失败补偿（退出码未知，带启动失败的原因），以及推进器宿主在超时处置中的补写（本机接力者在观察链丢失时、云端 tick 在两个 task
    列表都无踪时，补写判为超时的未知退出；云端 tick 遇到已停止却无退出记录的 task 时，按观察者同一提取函数补写）。
    走独立键空间（云端后端下是保留高位数值 SK 加属性 `item_type='exit'`——events 表 SK 是 NUMBER、字符串前缀结构上
    不可行；本机后端下是独立 `exits` 表；见 ADR 0034 机制一），不占 worker 的连续数值 seq 段，故不参与 adapter 的
    单调 seq/断号检测（机制一：免撞号覆盖 scope_done）。

    写入方只记事实，不判断是否已过截止时刻：截止时刻要由运行态里的认领时刻与运行定义算出，云端的退出观察者只看 task 对象。判断只在
    投影里做一次（`_reduce_scope`），各执行方式共用（ADR 0054 决策二后台推进条「截止时刻与说明」）。

    exit_code 为 None 表示退出码未知（有退出记录、却没取到码）。**不是宽限态**（ADR 0034 机制二「退出码缺失」条）：
    观察者只有一次机会看到 STOPPED，缺码时它应落 `PLATFORM_FAILED_EXIT` 哨兵 + reason。None 还来自 tick 的 launch 失败补偿
    （worker 没有启动，带 reason 与失败的时刻）、补写的未知退出（带 timed_out，终结函数按超时判 ERROR）、per-run 进程的
    `proc.wait()` 抛异常、同步 run 记录器停止后未取到码，以及老版本观察者或未知写者；终结函数 `finalize_job` 对不按超时处理的
    None 判 ERROR，绝不判 RUNNING（否则 run 永久 wedge）。
    reason：退出的归因，投影进 job message 给使用方看。两种来源：观察者缺退出码、落 `PLATFORM_FAILED_EXIT` 哨兵时带平台侧归因
    （云端后端下是 `stopCode: stoppedReason`，云端 tick 按同一提取函数补写时也带）；tick 的 launch 失败补偿带「起 worker 失败：
    异常文本」，与同步路径起 worker 失败交给终结函数的原因逐字相同。
    """

    scope_id: str
    exit_code: int | None = None
    # 超时标志（ADR 0034「job timeout」节归因链）：发过超时的停止请求，或补写时已判为超时。本机启动器在检查线程到点发过停止时
    # 带上；云端由 StopTask 的 reason 经 STOPPED 事件 detail.stoppedReason 的哨兵串还原；接力方与云端 tick 补写的未知退出带上。
    # 「退出时已过截止时刻」不由它表示，见 exited_at。
    timed_out: bool = False
    reason: str | None = None  # 退出归因（观察者落哨兵、tick 的 launch 失败补偿时带），见类 docstring
    # 退出时刻（带时区；记录里写成 ISO 串）：本机是推进进程看到 worker 退出的那一刻（经注入的墙钟读取），云端是 task 对象里的执行
    # 停止时刻（观察者与超时处置从同一个 task 取到同一个值），launch 失败补偿是失败时取的那一刻。补写的未知退出没有可观察的退出时刻、
    # 同步 run 的记录器不记，这两种为 None。投影时它严格晚于这个 job 的截止时刻的，与带超时标志的同样按超时交给终结函数。
    exited_at: datetime | None = None


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

    baseline（可选，当前 RunStore 的 state）：job 态**单调不倒退**的基线。已被认领成 RUNNING、但
    worker 还没吐 scope_started 的 job，events 里看不到它、会被算成 PENDING——若无基线，投影写会把它降回
    PENDING、reconciler 下轮又重复 claim/launch（真 bug）。故有基线时：job 的投影态与基线态取**较推进者**
    （pending<running<终态，单调）——events 只推进、claim 的 running 不被降回。无基线（首 tick/纯投影）时全 PENDING 起。

    全量重放（非增量）→ 天然幂等、抗乱序、抗重投（ADR 0034 机制三前提）。步骤：
    1. 按 scope_id 分组 records；每组内 kind='event' 的按 seq 升序喂 reduce_event 归约出 JobResult；
    2. 终结判定（机制二「终结函数与真值表」，单一真源是 `finalize_job`，别在两处各写一份）：
       有退出记录时进程终止本身即终态信号（stop_reason 为 timeout / abort 且内容不完整 → 对应终态；退出码非零或未知 → ERROR；
       exit==0 且见 scope_done → scope 级 error 或 scenario 归约终态；exit==0 无 scope_done（含零事件）→ ERROR）；无退出记录时
       见 scope_started 或非 attempted 的 session_opened → RUNNING、否则 PENDING（只有 attempted 的 session_opened 仍为 PENDING）。
    3. 聚合成 RunState：各 JobState（scope_id→status/session_id）+ run 总 status（_aggregate 的值：任一 job 出了判定即为终态，
       还没有 job 出判定时为前置态；投影写不落它，见 projected_run_status）+
       high_water_mark（所有 scope 的 worker 段 max seq，机制三条件写用）。

    只吐状态、不碰 store、不决定"启不启下一个"（那是 plan_next + adapter 的事）。是否按超时处理与 `project_full` 同一条规则：
    基线里这个 job 的认领时刻读得出时，由它、预算与期限算出截止时刻，退出时刻晚于它的退出按超时处理；读不出（没有基线、还没认领、
    或时刻不合法）时只看退出记录的超时标志。运行态只记各 job 的状态、不记说明，有退出记录而内容不完整的 job 不论是否按超时处理都是
    error，这条规则在这里不改变状态，只是让两处投影交给终结函数的输入一致；说明在 `project_full` 里按同一组输入给出。
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
        prior = jobs_state.get(scope_id)
        cutoff = _cutoff_from_claim(meta, job, prior.claimed_at if prior is not None else None)
        # 共用归约（与 project_full 单一真源）。这里只取状态、会话与 HWM，说明随即丢弃；读不出认领时刻时说明按预算那一句，不影响状态
        result, status, max_seq = _reduce_scope(job, recs, timeout_cause=cutoff.by if cutoff is not None else "budget",
                                                cutoff_at=cutoff.at if cutoff is not None else None)
        hwm = max(hwm, max_seq)
        # 单调合并（不倒退）：events 算出的态与基线态取较推进者。防「已 claim running 但 events 未到」被降回
        # pending（否则 reconciler 重复 launch，见 test_tick_idempotent）。终态一旦达成不被 running 覆盖。
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


def _cutoff_from_claim(meta: RunMeta, job: Job, claimed_at: str | None) -> JobCutoff | None:
    """运行态里的认领时刻读得出（带时区的 ISO 时刻）时，由它、job 预算与运行期限经 `run_deadline.job_cutoff` 算出截止时刻；没有或
    读不出时为 None。"""
    try:
        claimed = instant_from_iso(claimed_at)
    except ValueError:
        return None
    return job_cutoff(claimed, job.timeout_s, deadline_of(meta))


def _sorted_events(recs: list[EventRecord]) -> list[EventRecord]:
    """一个 scope 的 worker 事件段，按 seq 升序（退出记录不在其中）。"""
    return sorted([r for r in recs if r.kind == "event" and r.event is not None],
                  key=lambda r: (r.seq if r.seq is not None else 0))


@dataclass
class RecoveredScenario:
    """从事件流补取的 scenario 记录（ADR 0042 决策七）：判定真值里没有这条 scenario，事件流里却有它的 step 记录。事件流的只读投影，不是判定。

    status 是事件流里 `scenario_done` 给的 scenario 判定（有的话），None 表示没有 scenario_done、即未完成；steps 与判定真值里的
    StepResult 字段相同（status / votes / error_type / message / duration_ms / report_refs），供 explain 补齐骨架并按 report_refs
    读证据。被中止时还没上报完成记录的 step 只有 step_started、不在其中。
    """

    scenario_id: str
    status: Status | None
    steps: list[StepResult]


def recover_from_events(job: Job, records: list[EventRecord], *, recorded: "set[str] | frozenset[str]") -> list[RecoveredScenario]:
    """从一个 scope 的事件记录里补取判定真值没有的 scenario（ADR 0042 决策七）。

    复用 reduce_event 归约全部事件（与判定路径同一份归约，step 的字段不会另写一遍），然后把「事件流里有 step 记录、却不在
    `recorded`（判定真值里已有的 scenario_id）里」的 scenario 按 definition 顺序给出：既含没有 scenario_done 的未完成 scenario，
    也含事件流里有 scenario_done、判定真值却没写进去的 scenario（同步 run 在归约前退出，如进度输出遇到管道断开、收尾排空超时）——
    判据只能是判定真值有没有，不能是事件流里有没有 scenario_done。不写任何 store、不调终结函数、不改判定。
    """
    result = JobResult(job=job, status=Status.PENDING)
    scenario_status: dict[str, Status] = {}
    timing = Timing()
    for r in _sorted_events(records):
        if r.event is not None:
            reduce_event(r.event, result, scenario_status, timing, r.emit_ts or 0.0)
    by_id = {sr.scenario_id: sr for sr in result.scenarios}
    out: list[RecoveredScenario] = []
    for sc in job.scenarios:
        # 只看事件流里真出现过的 scenario（timing.seen_scenarios）：scope 级 error 后 reduce_event 给零事件 scenario 合成的 SKIPPED
        # 明细不是事件流里的记录，不能当成「已执行、从事件流补取」给出
        if sc.id in recorded or sc.id not in timing.seen_scenarios:
            continue
        sr = by_id.get(sc.id)
        steps = list(sr.steps) if sr is not None else list(timing.steps.get(sc.id, []))
        if not steps:
            continue
        out.append(RecoveredScenario(scenario_id=sc.id, status=scenario_status.get(sc.id), steps=steps))
    return out


def _reduce_scope(job: Job, recs: list[EventRecord], *, timeout_cause: TimeoutCause,
                  cutoff_at: datetime | None) -> tuple[JobResult, Status, int]:
    """单 scope 归约（project / project_full 共用一份，避免归约逻辑双写漂移）：

    events 段按 seq 升序喂 reduce_event 归约出完整 JobResult；退出记录（独立键空间）给终结函数退出信息与 stop_reason。
    cutoff_at 与 timeout_cause 是这个 job 的截止时刻与起作用的那一方（调用方由认领时刻、预算与期限经 `run_deadline.job_cutoff`
    算出，见 `project_full`）。是否已过截止时刻只在这里判断一次（ADR 0054 决策二后台推进条「截止时刻与说明」）：退出记录带超时标志，
    或它的退出时刻严格晚于 cutoff_at，都按超时交给终结函数（内容完整的不改判由终结函数保证），与前台终结之前对内容不完整的 job 再查
    一次截止时刻是同一个判断；没有退出时刻的退出记录只看超时标志。cutoff_at 为 None 只来自每轮的无状态投影读不出认领时刻的 job，
    那时同样只看超时标志。timeout_cause 只决定超时的说明。返回 (完整 JobResult, 派生 status, 该 scope 的 worker 段 max seq)。
    JobResult.status 会被派生 status 覆盖（reduce 期只累积 scenario 明细，最终 job 态由 finalize_job 的真值表定，机制二）。
    """
    evs = _sorted_events(recs)
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
    past_cutoff = (exited is not None and exited.exited_at is not None and cutoff_at is not None
                   and exited.exited_at > cutoff_at)
    # 终结判定只由终结函数写（ADR 0034 机制二）：reduce_event 只累积明细、成本与会话记录。无状态路径没有 fail-fast，
    # stop_reason 只可能是 none 或 timeout（上面一段的判断），abort_cause 用不到。
    term = finalize_job(
        job=job,
        stop_reason="timeout" if (exited is not None and (exited.timed_out or past_cutoff)) else "none",
        exited=exited is not None,
        exit_code=exited.exit_code if exited is not None else None,
        exit_reason=exited.reason if exited is not None else None,
        saw_scope_started=saw_scope_started,
        saw_session_opened=saw_session_opened,
        scope_done=scope_done,
        scenario_status=scenario_status,
        sessions=result.sessions,
        timeout_cause=timeout_cause,
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


# 中止的来源（推进器作出 abort 决定时首先成立的那一个）：fail-fast（某 job 已 error）、interrupt（使用方中断，ADR 0024 终止契约）、
# ended-elsewhere（发现这个 run 已被别处记为已结束，ADR 0054 决策二、五）。三者走同一条首次仲裁，只有 job 的说明按来源区分。
AbortCause = Literal["fail-fast", "interrupt", "ended-elsewhere"]

# 被 run 的期限截断的 job 的说明（ADR 0054 决策二第 2 条）；被自己的预算截断的仍是「job 超时（预算 Ns，已中止）」。
DEADLINE_TIMEOUT_MESSAGE = "这个 run 已超过允许运行的时间，job 被中止"
# 因发现 run 已被别处记为已结束而被中止的 job 的说明（ADR 0054 决策二「一次前台执行可能因三种原因停下」一段）。
ENDED_ELSEWHERE_ABORT_MESSAGE = "这个 run 已被记为已结束，job 被中止"

_ABORT_MESSAGES: dict[str, str] = {
    "fail-fast": "fail-fast：其他 job 失败，本 job 被中止",
    "interrupt": "收到中断信号：本 job 被中止",
    "ended-elsewhere": ENDED_ELSEWHERE_ABORT_MESSAGE,
}


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
    timeout_cause: TimeoutCause,
    abort_cause: AbortCause = "fail-fast",
) -> Termination:
    """终结函数（ADR 0034 机制二「终结函数与真值表」）：按行序取第一个命中的行给出 (status, error_type, message)。

    输入：stop_reason 取 none、timeout、abort 之一（推进器首次仲裁落定的主动处置）；退出信息（exited 为 False 即未退出；exited
    且 exit_code 为 None 即退出码未知）；是否见到 scope_done 及其 status / errorType / message；scenario 判定集；会话记录
    （未确认集 U 由此算出）。exit_reason 是平台侧归因或异常文本，只进消息。saw_session_opened 只计 origin 不是 attempted 的
    session_opened：只有结果未知的创建尝试时未退出行判 PENDING（ADR 0051 决策 4）。abort_cause 是作出 abort 决定的来源（取值见
    `AbortCause`），timeout_cause 是超时时起作用的那个截止时刻——budget（job 自己的墙钟预算）或 deadline（run 的期限，ADR 0054
    决策二第 2 条；由 `run_deadline.job_cutoff` 算出）。两者都只进消息、不进判定：超时的 job 不论哪一个截止时刻起作用都是 error、
    类型为 timeout。timeout_cause 没有缺省值：两条路径都由认领时刻、预算与期限算出它（同步路径在认领时算，无状态路径在
    `project_full` 里由运行态里的认领时刻重算），不靠缺省值落到预算那一句。无状态路径不作 abort 决定，abort_cause 用缺省值。
    内容完整（干净退出且发了 scope_done）后停止原因不再改写判定：判定已成，收尾拖过预算只改变推进器是否催停，不改结论——
    同步路径收到 scope_done 后不再落定停止原因，无状态路径按超时交来的退出（带超时标志或退出时刻晚于截止时刻）遇到它同样不改判，
    两条路径由这里同一条件保证；
    非零退出或退出码未知不算内容完整，照常受前两行约束。
    U 非空时不论判定为何，归因改 release_failed 的行保留原因消息，message 都追加产品语言提示并列出会话名；这条规则对桌面与设备
    job 相同，只有提示那一句按目标给（ADR 0051 决策 4）。
    两条归约路径只负责准备输入，判定逻辑不写第二份。"""
    unconfirmed = unconfirmed_sessions(sessions)
    content_complete = exited and exit_code == 0 and scope_done is not None
    if stop_reason == "timeout" and not content_complete:
        if timeout_cause == "deadline":
            message = DEADLINE_TIMEOUT_MESSAGE
        elif timeout_cause == "budget":
            message = f"job 超时（预算 {job.timeout_s:g}s，已中止）"  # 每个 job 都有有限的墙钟预算（ADR 0054 决策十）
        else:
            raise ValueError(f"timeout_cause 须为 budget 或 deadline，现为 {timeout_cause!r}")
        status, error_type = Status.ERROR, "timeout"
    elif stop_reason == "abort" and not content_complete:
        status, error_type, message = Status.ABORTED, None, _ABORT_MESSAGES[abort_cause]
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
            # 平台侧哨兵（观察者、同步云端路径的 FargateEngine 取不到退出码时落它，归因经 exit_reason 到这里）；本机 worker
            # 真以 255 退出也走这行，措辞对两种来源都成立
            why = f"：{exit_reason}" if exit_reason else "——详见 worker 日志或部署侧日志"
            error_type, message = "engine_error", f"worker 未能启动或未正常结束（退出码 255；平台侧未取到退出码时也记为 255）{why}"
        elif exit_code is None:
            error_type = "engine_error"
            # exit_reason 由调用方带上下文写好（同步路径：「worker 异常：…」/「起 worker 失败：…」；无状态路径：tick 的 launch 失败补偿
            # 写的「起 worker 失败：…」，与同步路径同一句）
            message = exit_reason if exit_reason else "worker 已终止但退出码未知——无法判定为通过，按错误处理"
        elif said:
            error_type, message = "engine_error", f"worker 随后非正常退出（退出码 {exit_code}）"
        else:
            error_type, message = "engine_error", f"worker 非正常退出（退出码 {exit_code}；事件流里没有失败原因——详见 worker 日志）"
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
    """收尾快照里有 job 有记录而仍非终态（ADR 0031 决定一·补：JobResult.status 只许终态，强制点在 project_full）。

    正常情况下不会发生：tick 只在 plan_next 提议收尾时才聚合，提议的前提是没有执行中的 job、有记录的 job 都已结束（ADR 0054 决策二
    后台推进条「决策」）。发生了就说明本次读到的 events 快照落后于判定依据（或写者违约），本轮不落任何判定真值、让触发源重试——绝不把
    running/pending 写进 jobs/*.json。"""


def project_full(
    meta: RunMeta,
    records: list[EventRecord],
    *,
    claimed_at: Mapping[str, datetime],
    past_stop_start: bool,
) -> RunResult:
    """从全量 records 推演出**完整 RunResult**（含各 JobResult 明细与 run 级裁决，ADR 0034）——收尾用。

    与 `project`（轻量 RunState、供实时投影写/plan_next）共用 `_reduce_scope` 归约；差别在保留完整明细
    （scenarios/steps/cost/report_refs）与给出超时的说明、run 级裁决。tick 在收尾的条件写**之前**用它落 ResultStore（判定真值，
    ADR 0030 决定三写序），条件写写成之后宿主用同一份结果生成 RunReport（ADR 0054 决策二后台推进条「收尾与报告」）。

    - **判定只装有记录的 job**：事件流里没有任何记录的 job（没有启动，或已过停止启动的时刻而不再启动）不臆造明细、不进
      RunResult.jobs，它们是 run_meta.jobs 与 jobs 的差，与同步路径因到期或发现 run 已被别处结束而没有启动的 job 同一形态（ADR 0054
      决策二）。**守 ADR 0031 不变量**：有记录的 job 非终态即抛 NonTerminalSnapshot、一份判定都不落（前置态绝不进 jobs/*.json）。
    - **截止时刻由认领时刻重算**（ADR 0054 决策二第 2 条与后台推进条「截止时刻与说明」）：claimed_at 给出每个有记录的 job 的认领
      时刻（取自这一轮读到的运行态），与它的预算、运行期限经 `run_deadline.job_cutoff` 算出截止时刻与起作用的那一方；与同步路径在
      认领时算出的是同一个算法、同一组输入，退出记录里不另记。截止时刻用于判断这次退出是否按超时处理（退出记录带超时标志，或退出
      时刻晚于它，见 `_reduce_scope`），起作用的那一方决定超时的说明。有记录的 job 不在 claimed_at 里即抛 ValueError：调用方要先
      确认快照里每个有记录的 job 都带认领时刻（tick 的快照检查），这里不回落到预算那一句。
    - **run 级的状态与说明由 `run_verdict` 给出**，与同步路径同一个裁决函数：past_stop_start 是这一轮是否已过停止启动的时刻，
      无状态路径没有使用方中断、也不会在读到 run 级终态之后走到这里，另两项恒为 False。已过停止启动的时刻、有 job 没有判定时是
      error 加 `RUN_DEADLINE_PASSED_MESSAGE`；全部 job 都有判定时照常聚合。此处是收尾、非投影，可落终态，与 project_state 的钳制
      不同。
    - run 级 duration_ms 为空：它是 RunState started_at→ended_at，宿主生成报告时补（ADR 0024「三级执行时长」detached 条）。
    """
    by_scope: dict[str, list[EventRecord]] = {}
    for r in records:
        by_scope.setdefault(r.scope_id, []).append(r)

    deadline = deadline_of(meta)
    job_results: list[JobResult] = []
    for job in meta.jobs:  # 按 definition 序（稳定输出）
        recs = by_scope.get(job.scope_id)
        if not recs:
            continue  # 没有启动的 job 无明细可落——不臆造
        at = claimed_at.get(job.scope_id)
        if at is None:
            raise ValueError(f"收尾快照缺少 job {job.scope_id!r} 的认领时刻，算不出超时时起作用的截止时刻")
        cutoff = job_cutoff(at, job.timeout_s, deadline)
        jr, status, _seq = _reduce_scope(job, recs, timeout_cause=cutoff.by, cutoff_at=cutoff.at)
        if status not in TERMINAL_STATUSES:
            raise NonTerminalSnapshot(
                f"收尾聚合读到 job {job.scope_id!r} 仍为 {status.value}：本次事件快照尚未到终态，本轮不落判定、等重放")
        job_results.append(jr)

    verdict = run_verdict(job_results, meta.jobs, past_stop_start=past_stop_start, interrupted=False, ended_elsewhere=False)
    return RunResult(
        run_meta=meta,
        status=verdict.status,
        message=verdict.message,
        jobs=job_results,
        **run_totals(job_results, jobs=meta.jobs),
    )


def run_totals(job_results: list[JobResult], *, jobs: Sequence[Job]) -> dict:
    """RunResult 的 run 级合计四键（唯一一份，同步 schedule 与无状态 project_full 共用，ADR 0034「不复制归约逻辑」）。

    jobs 是运行定义里的全部 job（`RunMeta.jobs`），job_results 是其中有判定的那些。加新的原生量字段（ADR 0024「成本信封」扩展条）
    只改这里。两组键的缺失语义不同，各自保留、不套同一条求和规则：
    - total_tokens 与 total_time_worked_s 各自跨 job 求和，只合计报了这个量的 job：没有任何 job 报时为 None（不假装 0），
      报了 0 照记 0（ADR 0024）。
    - device_observed_s 与 device_observed_missing 是设备计量（ADR 0051 决策 7），对有判定的设备 job 成对合计，某一键缺失按 0 计入。
      两键出现与否按运行定义里有没有设备目标的 job 判断，不按判定清单（ADR 0054 决策二）：判定清单可能不全（有 job 没有启动），
      设备 job 全部没有启动时两键都是 0、不省键；运行定义里没有设备 job 时两键都是 None（序列化省键）。判定清单完整时，有判定的
      设备 job 恰是运行定义里的设备 job，两种判法结果相同。
    """
    tok = [jr.total_tokens for jr in job_results if jr.total_tokens is not None]
    tw = [jr.total_time_worked_s for jr in job_results if jr.total_time_worked_s is not None]
    has_device = any(is_device_job(j) for j in jobs)
    dev = [jr for jr in job_results if is_device_job(jr.job)]
    return {
        "total_tokens": sum(tok) if tok else None,
        "total_time_worked_s": sum(tw) if tw else None,
        "device_observed_s": sum((jr.device_observed_s or 0.0 for jr in dev), 0.0) if has_device else None,
        "device_observed_missing": sum(jr.device_observed_missing or 0 for jr in dev) if has_device else None,
    }


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
    """状态归约（唯一一份，schedule 与本模块两条路径共用，ADR 0031 决定三、ADR 0034「不复制归约逻辑」）。

    先滤掉 _NON_VERDICT（skipped、aborted 两个派生态与 pending、running 两个前置态），只看已出判定的态：
    判定集非空时，有 error 判 error，否则有 failed 判 failed，否则判 passed。
    判定集为空而输入非空时不判 passed（ADR 0031 决定三）：输入里有 aborted 判 aborted，否则有 skipped 判 skipped，
    否则有 running 判 running，否则（全部 pending）判 pending。全部 job 被中止或没有启动的 run 因此不会记成 passed，
    这一点在函数内成立，不依赖「fail-fast 产生的 skipped 必定伴随一个 error」这类调用方条件；无状态投影里还没有任何
    job 出判定的 run 得到前置态，不得到终态。
    空输入仍判 passed，只作函数层兜底：CLI 入口对零 scenario 批（筛空或不加筛选）以退出码 2 拒绝（ADR 0041 决策一）；
    无状态路径下仍可能遇到空输入：旧版本 CLI 提交的零个 job 的 run（运行定义里有 job 而都没有判定时，`run_verdict` 不走到聚合）。
    这里保留终态：无状态路径在没有 pending 与 running 时经 `run_verdict` 把本函数的值交给收尾写入，返回前置态会让零个 job 的 run
    永远停在非终态。
    scenario 级归约（finalize_job）只喂 worker 报的三态，且判定集为空的情形在那里另判 error，过滤与空判定集规则都不生效。
    """
    verdicts = [s for s in statuses if s not in _NON_VERDICT]
    if any(s == Status.ERROR for s in verdicts):
        return Status.ERROR
    if any(s == Status.FAILED for s in verdicts):
        return Status.FAILED
    if verdicts or not statuses:
        return Status.PASSED
    # 判定集为空：输入全在 _NON_VERDICT 里，按 aborted、skipped、running 的顺序取第一个出现的，剩下的只能全是 pending
    for s in (Status.ABORTED, Status.SKIPPED, Status.RUNNING):
        if s in statuses:
            return s
    return Status.PENDING


@dataclass(frozen=True)
class RunVerdict:
    """run 级的裁决：状态与 run 级说明。说明只在没有任何 job 能承载原因时有值（与运行态的 run 级 message 同义）。"""

    status: Status
    message: str | None = None


def run_verdict(
    job_results: Sequence[JobResult],
    jobs: Sequence[Job],
    *,
    past_stop_start: bool,
    interrupted: bool,
    ended_elsewhere: bool,
) -> RunVerdict:
    """run 级裁决（唯一一份，前台与后台共用）：包住 `_aggregate`，加上聚合之外的例外，按序取第一条成立的。前台的
    `schedule` 在返回 RunResult 时调它，后台经 `project_full` 调它，两条路径收尾时写下的 run 级状态与说明都出自这里。

    job_results 是有判定的 job（判定只有终态），jobs 是运行定义里的全部 job，「没有判定的 job」即两者的差：已过停止启动的时刻、
    或发现 run 已被别处记为已结束时没有启动的 job，它们的运行态保持 pending、不产出判定。因 fail-fast 或使用方中断而没有启动的
    job 记为 skipped，有判定。

    1. 已过停止启动的时刻（past_stop_start：前台取执行期间的检查是否观察到过它，一经观察到即成立、不因系统时钟回拨撤销，收尾时
       不再读墙钟；后台取推进步骤这一轮的判断；判断本身是 `run_deadline.past_stop_start`）、而有 job 没有判定：error，说明是
       `RUN_DEADLINE_PASSED_MESSAGE`。run 的时间用完不是哪一个 job 的原因，也不替没有执行的 job 下结论；全部已启动的 job 都通过时
       聚合会得出 passed，所以不能靠聚合。优先于使用方中断的 aborted。
    2. 被外部停下的 run 记 aborted、无说明，不按仅有的判定聚合。成立条件有三种：
       - 处理过使用方中断（interrupted），且有 job 记为 aborted 或 skipped、或有 job 没有判定。已有 job 出了判定时（aborted 与
         passed 并存）聚合给 passed，全部 job 都没有启动时它给 skipped，被中断的 run 在两种情形下都应记 aborted。fail-fast 不走
         这里：它必伴随 error，run 级由聚合判 error。
       - 已发现 run 被别处记为已结束（ended_elsewhere：认领被拒、重试之前读到终态，或写 job 状态时得知 run 级已结束）。这次执行
         的 run 级结果本不成为记录：收尾的条件写被已有的终态挡下；万一写成了（记录其实没有结束，属于不该发生的不一致），写下的也不能
         是 passed——发现之后执行已中止，各 job 的判定不代表这个 run 的结果。
       - 有 job 没有判定而不属于第 1 条。正常的调用方到不了这里（没有判定只有上面两种原因），这一条让「有 job 没有判定的 run 不会
         得到 passed」在函数内成立，不依赖调用方传对标记。
    3. 其余：`_aggregate` 对各 job 判定的值，无说明。全部 job 都有判定时，不论当前时刻是否已过期限都照常聚合（被期限截断的 job
       自身是 error，聚合自然得出 error），ADR 0054 决策二第 4 条。

    后台推进没有使用方中断，读到 run 级终态时直接停止推演、不走到裁决，所以它的 interrupted 与 ended_elsewhere 都取 False。"""
    decided = {jr.scope_id for jr in job_results}
    undecided = any(j.scope_id not in decided for j in jobs)
    if past_stop_start and undecided:
        return RunVerdict(Status.ERROR, RUN_DEADLINE_PASSED_MESSAGE)
    stopped_short = undecided or any(jr.status in (Status.ABORTED, Status.SKIPPED) for jr in job_results)
    if ended_elsewhere or undecided or (interrupted and stopped_short):
        return RunVerdict(Status.ABORTED)
    return RunVerdict(_aggregate([jr.status for jr in job_results]))


def projected_run_status(jobs: dict[str, JobState]) -> Status:
    """投影写对 run 级 status 的取值（ADR 0034 机制三）：投影里全 job 仍 pending → `pending`，否则 `running`。

    **`pending` 的含义是「不写 run 级」**：两个 RunStore adapter 拿到 `pending` 时都保留库中 run 级原值（`create_run` 落的
    `pending`，或此前某次认领、投影写下的 `running`），只有 `running` 才落库。这样认领之后、拿着认领之前读到的 baseline
    写出的全 pending 投影不会把 run 级改回 `pending`（ADR 0034 机制三「run 级状态只进不退」条②）。

    **投影不能落 `project` 算出的 run 级 status**——那是 `_aggregate` 的值，只要有一个 job 出了判定就是终态（一个 job
    已 passed、其余还 pending 的 run 得到 `passed`），只有还没有 job 出判定时才是前置态；提前落 run 级终态会被 `try_finalize`
    的单调条件写认成「已 finalize」而挡住 commit point（ADR 0030），run 永远 finalize 不了。故 `_aggregate` 对空判定集
    给出前置态之后，这条钳制仍然需要：运行中的 run 只要有 job 出了判定，`_aggregate` 的值就不能原样落库。

    **判据只看传入的 job 态、不读库、不看传入的 run 级值**：两个 RunStore adapter 须落同一规则，而 DDB 侧
    标量条件写发生在 per-job 条件写之前（那一刻库中 job 态还没更新、读它无意义），判据依赖库就没法对拍。
    并发实例可能拿着认领之前读到的 baseline 投影，所以「投影里全 pending」不证明库中没有 job 已被认领；run 级是否
    已离开 `pending` 由认领与前台 job 写在同一次写里保证，投影在这种情形下不写 run 级、也就不会撤销它。两端取值都是
    非终态，commit point 的专属性不受影响。
    """
    if all(js.status == Status.PENDING for js in jobs.values()):
        return Status.PENDING
    return Status.RUNNING


# ============================================================================
# plan_next（ADR 0034 机制四、ADR 0054 决策二）：纯决策——该启哪些 pending / 是否收尾
# ============================================================================


ActionKind = Literal["start", "finalize", "finalize_expired"]


@dataclass(frozen=True)
class Action:
    """reconciler 的建议动作（ADR 0034）——纯数据，adapter 侧据此做副作用（CAS/RunTask/收尾）。

    kind='start'：建议启这个 scope_id 的 job（adapter 侧 CAS pending→running 成功才真 RunTask/spawn）；
    kind='finalize'：没有执行中的 job、也没有未启动的 job，按各 job 的判定收尾（ADR 0054 决策二第 4 条，不论是否已过期限）；
    kind='finalize_expired'：已过停止启动的时刻、没有执行中的 job、余下的 job 都没有启动，到期收尾（第 3 条）：run 级记为 error
    加说明，收尾写另以「读到运行态以来没有新的认领」为条件。两种收尾的条件写都保 commit 恰一次。
    """

    kind: ActionKind
    scope_id: str | None = None  # kind='start' 时有


def plan_next(state: RunState, max_concurrency: int, *, past_stop_start: bool, recorded: Collection[str]) -> list[Action]:
    """据当前 RunState 提议下一步动作（ADR 0034 机制四、ADR 0054 决策二，纯函数、无副作用）。

    past_stop_start：当前时刻是否已过停止启动的时刻（推进步骤由这一轮取的时刻判断，`run_deadline.past_stop_start`）。
    recorded：事件流里有任何记录的 scope。「未启动」的 job 是投影为 pending 而没有任何记录的 job；有记录而投影仍为 pending 的 job
    （别的推进方刚认领、worker 只发出了结果未知的建会话尝试）已经有人启动了它。

    - 没有 pending、也没有 running → [finalize]。
    - 已过停止启动的时刻：不提议 start。没有 running、pending 的 job 都没有记录 → [finalize_expired]；否则（还有 running，或有
      记录而仍为 pending 的 job）不提议任何动作，这一轮继续推进。
    - 否则：running < max_concurrency 且有 pending → 建议 start 若干 pending（补到并发上限）。
    **只提议**——真正的并发闸是 adapter 的 CAS 条件写（多 reconciler 实例并发提议同一 pending，只有 CAS
    成功的那个真启，其余被拒跳过，机制四）。故这里可乐观提议、不怕多提。
    """
    statuses = [js.status for js in state.jobs.values()]
    running = sum(1 for s in statuses if s == Status.RUNNING)
    pending = [sid for sid, js in state.jobs.items() if js.status == Status.PENDING]

    # 没有执行中、也没有未结束的 job → 按各 job 的判定收尾
    if not pending and running == 0:
        return [Action(kind="finalize")]

    if past_stop_start:
        if running == 0 and not any(sid in recorded for sid in pending):
            return [Action(kind="finalize_expired")]
        return []

    actions: list[Action] = []
    slots = max(0, max_concurrency - running)
    for sid in pending[:slots]:
        actions.append(Action(kind="start", scope_id=sid))
    return actions
