"""reconciler（ADR 0034）：无状态批量运行的推进编排——被事件唤醒、幂等、并发安全。

`tick(run_id, meta, …, clock=…)` 一步推进：取时刻 → 读库中运行态（已结束即停止推演）→ 读 EventLog 全量 records → project()
推 RunState → 投影写（只前进、不越过 running）→ 为这一轮已有结果的 job 先存判定明细、再以一次终态写记下它们的终态，run 的状态随之
写下 → plan_next() 在这一轮读到的运行态加上这次终态写的作用上作推进决策：对每个 start 动作重取时刻、未过停止启动的时刻才认领，认领
成功即算出截止时刻、经注入的 Launcher 起 job；已过停止启动的时刻、没有执行中的 job 而仍有未启动的 job 时做到期的结束写。结果是
`TickResult`，宿主据它决定继续推进、从记录生成报告后结束，还是直接结束（ADR 0034 机制三「run 级状态只进不退」条④；ADR 0054
决策二后台推进条「决策」「收尾与报告」两项）。

**无状态 + 幂等**：所有调度态在 EventLog / RunStore（持久），进程内不留。谁调 tick、何时调、并发调都安全
（CAS + HWM 条件写兜底）——各触发源（cloud Stream / local per-run 进程 / status --wait 接力）
共用这一个 tick。「是否已过停止启动的时刻」同样不记：每一轮按当前时刻判断（ADR 0054 决策二后台推进条「不记已过停止启动」）。

**时刻只经注入的时钟取**：tick 自己不读系统时钟，宿主注入与前台同一个读取点（组合根的 `compose.now`），返回带时区的 datetime；
写进记录时经 `serialize.instant_to_iso`，与组合根写时间戳同一种写法。

**守窄腰（[0016]/[0026]）**：本模块不 import subprocess/boto3——「起一个 job」的执行能力经注入的 `Launcher`
（本机后端下起 subprocess worker、旁路落 SQLite 并观察退出；云端后端下调 ECS RunTask）。core 只吐动作、调 Launcher，
副作用在 adapter/组合根。project/plan_next 是纯函数（gherkai_core.project）。
"""
from __future__ import annotations

import enum
import logging
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Protocol

from gherkai_core.model import TERMINAL_STATUSES, Job, JobResult, JobState, RunMeta, RunState
from gherkai_core.ports import ReportStore, ResultStore, RunStore
from gherkai_core.project import assemble_run_result, plan_next, project, project_full, run_duration_ms
from gherkai_core.run_deadline import deadline_of, job_cutoff, past_stop_start
from gherkai_core.run_status import RUN_ENDINGS, CommitOutcome, commit_applied
from gherkai_core.serialize import instant_from_iso, instant_to_iso

logger = logging.getLogger("gherkai_core.reconcile")


class TickOutcome(enum.Enum):
    """一次 `tick` 的结果（ADR 0034 机制三「run 级状态只进不退」条④；ADR 0054 决策二后台推进条「收尾与报告」）。

    后两种都让宿主结束对这个 run 的推进（本机的推进循环与 status --wait 退出，云端这一次调用正常返回）；只有 `COMMITTED` 让宿主
    生成 RunReport。
    """

    # 继续推进：这一次 tick 没有使 run 成为终态（其中可能已记下部分 job 的终态）；或读不到运行态；或到期的结束写没写成而重读的运行态
    # 仍未结束（写下时有执行中的 job：读取之后又有了新的认领）。宿主照常做超时处置并等下一轮。
    CONTINUE = "continue"
    # 这一方的写使 run 成为终态：记下最后一批 job 终态的那次终态写，或到期的结束写，由这一方写成。这一次 tick 交给终态写的判定明细随
    # `TickResult.details` 带出，宿主用它与记录生成报告（`write_report_from_record`）。
    COMMITTED = "committed"
    # run 已结束而使它成为终态的不是这一方：这一轮读到的运行态已是终态（读到即返回，不再推演、投影、认领，也不存明细），或终态写报告
    # run 在这次写之前已是终态，或到期的结束写没写成、重读到别人已写下的终态。宿主不生成报告：报告只由使 run 成为终态的那一方生成。
    ENDED = "ended"


@dataclass(frozen=True)
class TickResult:
    """`tick` 交还宿主的结果：outcome 是三种结果之一；details 当且仅当 `COMMITTED` 时不为 None。

    details 是这一次 tick（含同一轮的重做）存下并交给终态写的各 job 的判定明细，按运行定义的次序；这一次 tick 没有交给终态写任何 job
    时为空元组（只会出在由到期的结束写使 run 成为终态的时候）。其中可能有终态已由别的推进器写下、这次写跳过的 job：两个推进器读到不同的
    事件快照时（例如补写的超时退出与随后到达的真实退出），报告里这个 job 的状态取运行态，明细可能出自另一份快照。较早轮次写下终态的
    job 不在其中，生成报告时从判定存储读回。宿主把它交给 `write_report_from_record`，状态从记录读，不再另读一次事件重算。"""

    outcome: TickOutcome
    details: tuple[JobResult, ...] | None = None

    def __post_init__(self) -> None:
        if (self.outcome is TickOutcome.COMMITTED) != (self.details is not None):
            raise ValueError("只有这一方的写使 run 成为终态时才带判定明细")


class EventLog(Protocol):
    """事件日志口（reconciler 读全量 records 重放）。写侧：`tick` 只在 launch 失败补偿时调
    `record_exit`；其余退出记录来自退出观察者（本机 launcher 的 proc.wait、云端 exit-observer Lambda、本机同步 run 的
    `EventRecordingEngine`）与推进器宿主的超时处置（本机接力恢复、云端 tick 对无踪 task 的补写，都经
    `record_timed_out_if_absent`；云端 tick 遇已停止却缺退出记录的 task 时，按 DescribeTasks 结果补写，与观察者同一提取算法）；
    worker 执行事件由 worker（云端）或 launcher 旁路（本机）写。各写入方只记事实，是否已过截止时刻由投影判断（`project._reduce_scope`）。"""

    def records(self) -> list: ...  # list[EventRecord]（gherkai_core.project）

    # 单个 scope 有无退出记录（主键点查）——超时处置/接力恢复判「观察链是否已写」用，别为一个 scope 重放整 run。
    def has_exit(self, scope_id: str) -> bool: ...

    # 覆盖同键（独立键空间，机制一）：观察到的退出、launch 失败补偿与云端按 task 对象的补写都经这里。timed_out：发过超时的停止
    # 请求（ADR 0034「job timeout」节归因链）。exited_at：退出时刻（带时区），写入方观察到退出的那一刻；没有可观察的退出时刻时为
    # None。两项都只是事实，写入方不比较截止时刻。
    def record_exit(self, scope_id: str, exit_code: int | None, *, timed_out: bool = False,
                    reason: str | None = None, exited_at: datetime | None = None) -> None: ...

    # 补写判为超时的未知退出（退出码未知、带超时标志、不带退出时刻），只在这个 scope 还没有退出记录时写入：「没有」的判断与写入是
    # 同一次条件写，已有记录时不写、不报错，返回 False（别的写入方已经写了，观察到的退出不被盖掉）；写成返回 True。之后到达的真实
    # 退出照旧经 `record_exit` 覆盖这一条（ADR 0034「job timeout」节「`timed_out` 归因链」）。
    def record_timed_out_if_absent(self, scope_id: str) -> bool: ...


class Launcher(Protocol):
    """起一个 job 的执行能力（注入；机制四 CAS 成功后才调）。

    本机后端下起 subprocess worker（事件旁路落 SQLite EventLog + proc.wait 写 task_exited）；
    云端后端下调 ECS RunTask（worker 自 PutItem events + 退出观察者 Lambda 写 task_exited）。
    reconciler 对「怎么起」无知——只在认领成功后调 launch(job, cutoff_at=…)。

    cutoff_at：这个 job 的截止时刻（带时区），tick 在认领时由认领时刻、job 预算与运行期限经 `run_deadline.job_cutoff` 算出：认领时刻
    加预算，与期限取较早的一个（ADR 0054 决策二第 2 条）。到点的处理由实装负责，都按这个时刻、不另取 launch 时刻起算：本机的推进进程
    按墙钟检查它，云端的一次性定时触发定在它。
    """

    def launch(self, job: Job, *, cutoff_at: datetime) -> None: ...


def write_report_from_record(meta: RunMeta, run_store: RunStore, details: Iterable[JobResult],
                             report_store: ReportStore | None, *, result_store: ResultStore | None,
                             created_at: str) -> None:
    """这一方的写使 run 成为终态之后，从记录生成 RunReport（派生视图，**永远最后**；ADR 0054 决策二后台推进条「收尾与报告」，ADR 0027
    「ReportStore 接口：整 run 一次写」节）。
    宿主只在 tick 返回 `TickOutcome.COMMITTED` 后调，details 是那次的 `TickResult.details`。

    一次读运行态、按它算 run 级墙钟（started_at 到 ended_at，`project.run_duration_ms`）、组装 run 的结果
    （`project.assemble_run_result`：状态与 job 级说明取运行态，判定明细按下列来源附上），再写报告。判定明细的来源：
    - details 里有的 job（这一次 tick 交给终态写的）用 details 里的那一份；
    - 其余 job 在给了 result_store 时按 scope_id 从判定存储读回。较早轮次写下终态的 job，明细在那一轮的终态写之前已存下，库中已是终态的
      job 之后不再被推进步骤选中、不再存明细，读回的就是那一轮存下的一份；没有存过明细的 job（由结束写结束的）读回为空、不带明细。
      读回依赖一个前提：会生成报告的结束写只有到期这一条来路，它只结束 pending 的 job，pending 的 job 没有存过明细；结束执行中 job
      的结束写（运行定义不可用的变体）之后不生成报告。run 处置不复用这条读回：它会结束执行中的 job，那些 job 可能存过与终态无关的明细。
      两个推进器重叠时，按 scope_id 覆盖同键的保存可能让读回的那一份与写下的终态出自不同的事件快照；
    - result_store 为 None 时只用 details。
    result_store 是必传的关键字参数，调用方自己决定用不用判定存储。

    整段在失败隔离之内：报告是派生只读视图，判定明细与终态在生成之前都已落下，读运行态、读回明细、组装与写报告的任何失败都不击穿已到
    终态的 run，这一步的失败也没有人重试（ADR 0030 决定三「ReportStore.write 失败隔离」注）。运行态读不到时同样不生成报告。判定明细
    不再另读一次事件重算：重算用的事件可能已经变了（接力方补写的未知退出之后又被真实的退出码覆盖）。
    created_at：报告的生成时刻（记录里的写法）。report_store 为 None 时什么都不做：不读运行态，也不读回明细。
    **唯一一份**（云端推进器 Lambda 与本机后台推进进程都调用此处）。纯编排：不 import boto3。
    """
    if report_store is None:
        return
    try:
        state = run_store.load_run_state(meta.run_id)
        if state is None:
            raise FileNotFoundError(f"run {meta.run_id} 的运行状态不存在，无法生成报告")
        in_hand = {jr.scope_id: jr for jr in details}
        if result_store is not None:
            for job in meta.jobs:
                if job.scope_id not in in_hand:
                    jr = result_store.load_job_result(meta.run_id, job.scope_id)
                    if jr is not None:
                        in_hand[job.scope_id] = jr
        result = assemble_run_result(meta, state, in_hand.values(), duration_ms=run_duration_ms(state))
        report_store.write(meta.run_id, result, created_at=created_at)
    except Exception:
        # 派生视图的失败不击穿已到终态的 run；traceback 留在日志里供排障
        logger.warning("这个 run 的报告没有生成：run=%s", meta.run_id, exc_info=True)


def tick(
    run_id: str,
    meta: RunMeta,
    event_log: EventLog,
    run_store: RunStore,
    launcher: Launcher,
    max_concurrency: int,
    *,
    clock: Callable[[], datetime],
    result_store: ResultStore | None = None,
) -> TickResult:
    """推进一步，返回 `TickResult`（三种结果的含义见 `TickOutcome`）。

    clock：宿主注入的墙钟，返回带时区的 datetime（组合根传 `compose.now`）。本函数在三处取它（ADR 0054 决策二后台推进条「时刻」）：
    - 每次读取运行态之前取一次，用于这一轮的推进决策（是否已过停止启动的时刻）与这一轮写下的结束时刻 ended_at；
    - 每次认领之前再取一次，作这个 job 的认领时刻，并重做停止启动的检查，已过即不认领。靠后的认领不沿用轮首的时刻：前面的读取、
      保存与启动调用有耗时，沿用会让靠后的 job 少拿到预算；
    - 启动调用失败时再取一次，作补写的退出记录的退出时刻（是否已过截止时刻由投影判断）。

    幂等：可反复调、并发调。一轮的步骤（ADR 0034「端到端流程」cloud 第 4 步与机制三「run 级状态只进不退」条④的步骤；ADR 0054
    决策二后台推进条）：
    1. 读库中运行态作 baseline。读不到即返回 `CONTINUE`，不读事件、不写任何东西：这一轮的认领、投影与结束写都写不成，终态写会抛错。
       run 已是终态即返回 `ENDED`，不读事件、不投影、不认领、不存明细（ADR 0034 机制三「run 级状态只进不退」条④）。
    2. 读 EventLog 全量 records，project() 纯推演出 RunState（含 HWM），再以 project_state() 投影写：投影只前进、不越过 running，
       不写 job 的终态（adapter 写的时候把事件推出的终态钳在 running）；写不成（stale 被挡、run 已结束）无害，返回值不看。
    3. 记下这一轮已有结果的 job 的终态（选哪些 job 见 `_committable`）：先由 project_full 从同一份 records 给出它们的判定明细、配了
       ResultStore 时逐个存下，再以一次终态写（`RunStore.commit_job_states`）记下它们的终态，会话与认领时刻取这一轮的投影。任一份明细
       存不成即原样抛出：这一遍（从读运行态起算，重做是另一遍）一个终态都不写，也不认领、不做结束写，这一遍已存下明细的 job 一并留在
       running，下一轮重存再写；重做那一遍存不成时，第一遍已写下的终态与已做的认领不收回（ADR 0034
       机制三「run 级状态只进不退」条④ K3）。终态写的结果：使 run 成为终态即返回 `COMMITTED`；run 在这次写之前已是终态即返回
       `ENDED`，不另读、不启动 job；run 仍未结束时，以这次写对 baseline 的作用（`run_status.commit_applied`）作推进决策用的运行态。
    4. 推进决策（plan_next）只看运行态：这一轮读到的 baseline 加上第 3 步终态写的作用，不看投影。交给它之前 job 按运行定义的次序重排
       （ADR 0034 机制四）：存储不保证 jobs 的次序，并发上限靠各推进器对同一段 pending 前缀的认领碰撞来守，次序不一致时两次重叠的推进
       会各认领一个不同的 job。这一轮读运行态之后才被别处认领的 job 在其中仍是 pending，只多出一次被认领条件挡下的启动提议，或一次写下时有执行中的 job
       而没写成的到期结束写。
    5. 动作：
       - start：取认领时刻，已过停止启动的时刻即不认领、结束这一组 start；否则 try_claim_job() 认领（机制四），成功的那个（本实例）
         才由认领时刻算出截止时刻、launcher.launch(job, cutoff_at=…) 真起。启动调用失败时补写退出记录（见下）。
       - expire：到期的结束写（见 `_end_expired`）。
    6. 这一轮有认领因已过停止启动的时刻而没有做时，同一轮里从第 1 项起重做一次（重新取时刻、重新读取运行态与事件），按已过停止启动
       再决策（这一轮里先前认领成功的 job 与已记下的终态都在重新读到的运行态里，不再存、再写）：不拿轮首的快照做结束写，也不就此
       返回——云端没有别的东西会再触发一轮，停在这里的 run 满足到期的结束写却没有人做。重新决策只做一次，已过停止启动之后不会再提议
       启动。重做那一遍使 run 成为终态时，交还的明细含两遍交给终态写的全部。
    其余情形返回 `CONTINUE`。baseline 读到之后才插入的终态不在这一次读取的判停之内：本轮的投影写与认领被条件挡下，终态写返回
    `ALREADY_ENDED`。

    launch 失败补偿（ADR 0034 机制二推论）：job 已 CAS 成 RUNNING 却永无 events/task_exited（进程没起、平台观察者无从观察），不补偿
    则永停 RUNNING。tick 在此扮演「起不来」时刻的退出观察者：退出码未知、原因是「起 worker 失败：异常文本」，与前台起 worker 失败交给
    终结函数的输入相同；失败时取的时刻记为退出时刻，它晚于这个 job 的截止时刻时投影按到点处理，与前台起 worker 失败的分支得到同一个
    判定（ADR 0054 决策二后台推进条「时刻」）。补偿只记事实、不带超时标志。异常不向外抛出（失败隔离：别拖垮同批其余 job），traceback
    另留在日志里供排障。
    """
    deadline = deadline_of(meta)
    job_by_scope: dict[str, Job] = {j.scope_id: j for j in meta.jobs}
    committed: dict[str, JobResult] = {}  # 这一次 tick 交给终态写的明细，跨重做保留
    replanned = False
    while True:
        now = clock()
        # 基线取当前 RunStore 态，先于读事件：已结束时省掉全量事件读，判停、推演与推进决策用的是同一份 baseline。基线让 project 的
        # job 态单调不倒退（已认领成 running 但 worker 还没吐 scope_started 的 job，不被降回 pending → 不重复 launch，机制四）。
        # 首 tick 时 STATE 已由 create_run 建。手里的运行态可能比事件旧，写终态之前按 job 检查，见 `_committable`。
        baseline = run_store.load_run_state(run_id)
        if baseline is None:
            return TickResult(TickOutcome.CONTINUE)
        if baseline.status in TERMINAL_STATUSES:
            return TickResult(TickOutcome.ENDED)
        records = event_log.records()
        state = project(meta, records, baseline)
        # 投影写：stale 被挡、run 已结束时返回 False——无害，本 tick 只是没推进落库，下轮（或别的实例）会重推。
        run_store.project_state(run_id, state)

        view = baseline
        claims = _committable(baseline, state)
        if claims:
            results = project_full(meta, [r for r in records if r.scope_id in claims], claimed_at=claims)
            if result_store is not None:
                for jr in results:
                    result_store.save_job_result(run_id, jr)  # 明细先存；任一份失败即原样抛出，这一轮不写终态、不启动 job
            finals = [JobState(scope_id=jr.scope_id, status=jr.status, session_id=state.jobs[jr.scope_id].session_id,
                               claimed_at=state.jobs[jr.scope_id].claimed_at) for jr in results]
            at = instant_to_iso(now)
            outcome = run_store.commit_job_states(run_id, finals, ended_at=at)
            committed.update((jr.scope_id, jr) for jr in results)
            if outcome is CommitOutcome.ENDED_RUN:
                return TickResult(TickOutcome.COMMITTED, _ordered(meta, committed))
            if outcome is CommitOutcome.ALREADY_ENDED:
                return TickResult(TickOutcome.ENDED)
            applied, _ = commit_applied(baseline, finals, ended_at=at)
            assert applied is not None  # baseline 未结束，终态写的作用总能算出
            view = applied
        # 推进决策按运行定义的次序看 job（理由见 docstring 第 4 项）
        view = replace(view, jobs={j.scope_id: view.jobs[j.scope_id] for j in meta.jobs if j.scope_id in view.jobs})

        stop_start = replanned or past_stop_start(now, deadline)
        refused = False
        for act in plan_next(view, max_concurrency, past_stop_start=stop_start):
            if act.kind == "expire":
                return _end_expired(run_id, run_store, ended_at=now, details=_ordered(meta, committed))
            # start：先确认 job 存在，再认领：防御跳过时不会留下一个已认领成 running 却无人启动的 job。
            job = job_by_scope.get(act.scope_id) if act.scope_id is not None else None
            if job is None:
                continue  # plan_next 从 view.jobs 提议、键集是 meta.jobs 的子集，不该发生；防御跳过
            claimed_at = clock()
            if past_stop_start(claimed_at, deadline):
                refused = True  # 余下的 start 不再逐个检查：已过停止启动的时刻，改为同一轮里重新决策
                break
            # 认领：多实例并发提议同一 pending，只有一个成功（机制四严格并发闸）。写进记录的认领时刻与算截止时刻的是同一个值。
            if run_store.try_claim_job(run_id, job.scope_id, claimed_at=instant_to_iso(claimed_at)):
                _launch(run_id, job, launcher, event_log, clock, job_cutoff(claimed_at, job.timeout_s, deadline).at)
        if refused and not replanned:
            replanned = True
            continue
        return TickResult(TickOutcome.CONTINUE)


def _launch(run_id: str, job: Job, launcher: Launcher, event_log: EventLog, clock: Callable[[], datetime],
            cutoff_at: datetime) -> None:
    """认领成功之后起 job；启动调用失败时补写退出记录（补偿的理由与写法见 `tick` 末段）。"""
    try:
        launcher.launch(job, cutoff_at=cutoff_at)
    except Exception as e:
        logger.warning("这个 job 没能启动，已按错误处理：run=%s scope=%s", run_id, job.scope_id, exc_info=True)
        event_log.record_exit(job.scope_id, None, reason=f"起 worker 失败：{e}", exited_at=clock())


def _committable(baseline: RunState, state: RunState) -> dict[str, datetime]:
    """这一轮可以写终态的 job 与它们的认领时刻（ADR 0054 决策二后台推进条「快照」）：投影为终态、在这一轮读到的运行态里仍未结束，
    且在其中带读得出的认领时刻（读不出或不带时区的算不带）。

    推进步骤先读运行态、后读事件，手里的运行态可能比事件旧：投影为终态而运行态里不带认领时刻的 job 是这一轮读运行态之后才被认领的
    （推进步骤的认领在同一次写里写下 running 与认领时刻，所以这样的 job 在这一轮读到的运行态里是 pending），这一轮不为它存明细、不写
    终态，下一轮读到新的运行态再做，别的 job 照写。不用「取不到认领时刻就按预算说明」这样的回落：截止时刻要由认领时刻算出，回落
    得出的可能是错的那一句。

    运行态里已是终态的 job 不选（终态只写一次，也不再为它存明细）。按运行态是否未结束来筛、不拿投影比：project 只在运行态的等级严格
    更高时取运行态，两边都是终态时投影可能与记录不同。被选中的 job 在运行态里带认领时刻，project 判它用的截止时刻就由这个认领时刻
    算出，与交给 project_full 的输入相同，所以 project_full 对它们不会因快照不到终态或缺认领时刻而抛错。"""
    out: dict[str, datetime] = {}
    for sid, js in state.jobs.items():
        if js.status not in TERMINAL_STATUSES:
            continue
        base = baseline.jobs.get(sid)
        if base is None or base.status in TERMINAL_STATUSES:
            continue
        try:
            out[sid] = instant_from_iso(base.claimed_at)
        except ValueError:
            continue
    return out


def _ordered(meta: RunMeta, committed: Mapping[str, JobResult]) -> tuple[JobResult, ...]:
    """这一次 tick 交给终态写的明细，按运行定义的次序。"""
    return tuple(committed[j.scope_id] for j in meta.jobs if j.scope_id in committed)


def _end_expired(run_id: str, run_store: RunStore, *, ended_at: datetime, details: tuple[JobResult, ...]) -> TickResult:
    """到期的结束写：以「执行方自己到期」这条来路结束 run（`RunStore.end_run`，ADR 0054 决策二第 3 条与后台推进条「收尾与报告」），
    运行态里是 pending 的 job 记 skipped、带到期的说明，run 随之成为终态。结束写的条件是写下时 run 未结束、没有 running 的 job。

    写成即 `COMMITTED`，带着这一次 tick 交给终态写的明细。没写成时重读一次运行态：已是终态说明别人已经结束了它，返回 `ENDED`；仍未
    结束（写下时有执行中的 job：读取之后有了新的认领）或读不到返回 `CONTINUE`，新认领的 job 照常在它的截止时刻被停下。"""
    if run_store.end_run(run_id, RUN_ENDINGS["deadline"], ended_at=instant_to_iso(ended_at)):
        return TickResult(TickOutcome.COMMITTED, details)
    after = run_store.load_run_state(run_id)
    if after is not None and after.status in TERMINAL_STATUSES:
        return TickResult(TickOutcome.ENDED)
    return TickResult(TickOutcome.CONTINUE)
