"""reconciler（ADR 0034）：无状态批量运行的推进编排——被事件唤醒、幂等、并发安全。

`tick(run_id, meta, …, clock=…)` 一步推进：取时刻 → 读库中运行态（已收尾即停止推演）→ 读 EventLog 全量 records → project()
推 RunState → 条件写落库 → plan_next() 决定动作 → 对每个 start 动作重取时刻、未过停止启动的时刻才认领，认领成功即算出截止时刻、
经注入的 Launcher 起 job；收尾动作先落判定明细，再使 run 成为终态：全部 job 已结束时以终态写记下各 job 的终态（run 的状态随之写下），
已过停止启动的时刻而余下的 job 都没有启动时做到期的结束写。结果是 `TickResult`，宿主据它决定继续推进、从记录生成报告后结束，还是
直接结束（ADR 0034 机制三「run 级状态只进不退」条④）。

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
from collections.abc import Callable, Collection, Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from gherkai_core.model import TERMINAL_STATUSES, Job, JobResult, JobState, RunMeta, RunState
from gherkai_core.ports import ReportStore, ResultStore, RunStore
from gherkai_core.project import assemble_run_result, plan_next, project, project_full, run_duration_ms
from gherkai_core.run_deadline import deadline_of, job_cutoff, past_stop_start
from gherkai_core.run_status import RUN_ENDINGS, CommitOutcome
from gherkai_core.serialize import instant_from_iso, instant_to_iso

logger = logging.getLogger("gherkai_core.reconcile")


class TickOutcome(enum.Enum):
    """一次 `tick` 的结果（ADR 0034 机制三「run 级状态只进不退」条④）。

    后两种都让宿主结束对这个 run 的推进（本机的推进循环与 status --wait 退出，云端这一次调用正常返回）；只有 `COMMITTED` 让宿主
    生成 RunReport。
    """

    # 继续推进：本轮没有收尾——没有走到收尾动作，或走到了而这一轮的快照不能收尾（有记录的 job 在读到的运行态里缺认领时刻、读不到运行态），
    # 或到期的结束写没写成而重读的运行态仍未结束（写下时有执行中的 job：读取之后又有了新的认领）。宿主照常做超时处置并等下一轮。
    CONTINUE = "continue"
    # 这一方的写使 run 成为终态：判定明细已落，终态写或到期的结束写由这一方写成。这一轮落下的判定明细随 `TickResult.details` 带出，
    # 宿主用它与记录生成报告（`write_report_from_record`）。
    COMMITTED = "committed"
    # run 已结束而使它成为终态的不是这一方：这一轮读到的运行态已收尾（读到即返回，不再推演、投影、认领，也不落判定明细），或终态写报告
    # run 在这次写之前已是终态，或到期的结束写没写成、重读到别人已写下的终态。宿主不生成报告：报告只由使 run 成为终态的那一方生成。
    ENDED = "ended"


@dataclass(frozen=True)
class TickResult:
    """`tick` 交还宿主的结果：outcome 是三种结果之一；details 当且仅当 `COMMITTED` 时不为 None，是这一轮落下的各 job 判定明细（按运行
    定义的次序，只有事件流里有记录的 job；到期而一个 job 都没有启动时为空元组）。宿主把它交给 `write_report_from_record`，状态从记录读，
    不再另读一次事件重算。"""

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
                             report_store: ReportStore | None, *, created_at: str) -> None:
    """这一方的写使 run 成为终态之后，从记录生成 RunReport（派生视图，**永远最后**；ADR 0054 决策二后台推进条「收尾与报告」，ADR 0027
    「ReportStore 接口：整 run 一次写」节）。
    宿主只在 tick 返回 `TickOutcome.COMMITTED` 后调，details 是那次的 `TickResult.details`。

    一次读运行态、按它算 run 级墙钟（started_at 到 ended_at，`project.run_duration_ms`）、与 details 一起组装 run 的结果
    （`project.assemble_run_result`：状态与 job 级说明取运行态，有记录的 job 附上这一轮的判定明细），再写报告。整段在失败隔离之内：
    报告是派生只读视图，判定明细与终态在生成之前都已落下，读运行态、组装与写报告的任何失败都不击穿已到终态的 run，这一步的失败也
    没有人重试（ADR 0030 决定三「ReportStore.write 失败隔离」注）。运行态读不到时同样不生成报告。判定明细不再另读一次事件重算：
    重算用的事件可能已经变了（接力方补写的未知退出之后又被真实的退出码覆盖）。
    created_at：报告的生成时刻（记录里的写法）。report_store 为 None 时什么都不做。
    **唯一一份**（云端推进器 Lambda 与本机后台推进进程都调用此处）。纯编排：不 import boto3。
    """
    if report_store is None:
        return
    try:
        state = run_store.load_run_state(meta.run_id)
        if state is None:
            raise FileNotFoundError(f"run {meta.run_id} 的运行状态不存在，无法生成报告")
        result = assemble_run_result(meta, state, details, duration_ms=run_duration_ms(state))
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
    - 每次读取运行态之前取一次，用于这一轮的推进决策（是否已过停止启动的时刻）与收尾时刻 ended_at；
    - 每次认领之前再取一次，作这个 job 的认领时刻，并重做停止启动的检查，已过即不认领。靠后的认领不沿用轮首的时刻：前面的读取与
      启动调用有耗时，沿用会让靠后的 job 少拿到预算；
    - 启动调用失败时再取一次，作补写的退出记录的退出时刻（是否已过截止时刻由投影判断）。

    幂等：可反复调、并发调。步骤：
    1. 读库中运行态作 baseline；run 级已是终态即返回 `ENDED`，不读事件、不投影、不认领、不落判定真值
       （ADR 0034 机制三「run 级状态只进不退」条④）。
    2. 读 EventLog 全量 records → project() 纯推演完整 RunState（含 HWM）。
    3. project_state() HWM 条件写落 RunState（stale 被挡、无害——下轮重读重推，机制三）。
    4. plan_next() → 动作：
       - start：取认领时刻，已过停止启动的时刻即不认领、结束这一组 start；否则 try_claim_job() 认领（机制四），成功的那个（本实例）
         才由认领时刻算出截止时刻、launcher.launch(job, cutoff_at=…) 真起。启动调用失败时补写退出记录（见下）。
       - finalize / finalize_expired：见 `_finalize`——快照检查、判定真值先落，再以终态写（全部 job 已结束）或到期的结束写使 run
         成为终态，到期的结束写没写成时重读一次。
    5. 这一轮有认领因已过停止启动的时刻而没有做时，同一轮里从第 1 项起重做一次（重新取时刻、重新读取运行态与事件），按已过停止启动
       再决策（这一轮里先前认领成功的 job 计入其中）：不拿轮首的快照收尾，也不就此返回——云端没有别的东西会再触发一轮，停在这里的
       run 满足到期收尾却没有人收。重新决策只做一次，已过停止启动之后不会再提议启动。
    plan_next 没有给出收尾动作、也不再重新决策时返回 `CONTINUE`。baseline 读到之后才插入的收尾不在这一次读取的判停之内：本轮的
    投影写被终态守卫挡下、认领被条件挡下。

    launch 失败补偿（ADR 0034 机制二推论）：job 已 CAS 成 RUNNING 却永无 events/task_exited（进程没起、平台观察者无从观察），不补偿
    则永停 RUNNING。tick 在此扮演「起不来」时刻的退出观察者：退出码未知、原因是「起 worker 失败：异常文本」，与前台起 worker 失败交给
    终结函数的输入相同；失败时取的时刻记为退出时刻，它晚于这个 job 的截止时刻时投影按到点处理，与前台起 worker 失败的分支得到同一个
    判定（ADR 0054 决策二后台推进条「时刻」）。补偿只记事实、不带超时标志。异常不向外抛出（失败隔离：别拖垮同批其余 job），traceback
    另留在日志里供排障。
    """
    deadline = deadline_of(meta)
    job_by_scope: dict[str, Job] = {j.scope_id: j for j in meta.jobs}
    replanned = False
    while True:
        now = clock()
        # 基线取当前 RunStore 态，先于读事件：已收尾时省掉全量事件读，判停与本轮推演用的是同一份 baseline。
        # 读序不影响投影的正确性：插在两次读之间的认领只让本轮多提议一次被认领条件挡下的 start，插在两次读之间的事件只让
        # 本轮推演比 baseline 更新，按生命周期序合并照常。基线让 project 的 job 态单调不倒退（已认领成 running
        # 但 worker 还没吐 scope_started 的 job，不被降回 pending → 不重复 launch，机制四）。首 tick 时 STATE 已由 create_run 建。
        # 收尾要防的是另一面：手里的运行态可能比事件旧，见 `_finalize` 的快照检查。
        baseline = run_store.load_run_state(run_id)
        if baseline is not None and baseline.status in TERMINAL_STATUSES:
            return TickResult(TickOutcome.ENDED)
        records = event_log.records()
        state = project(meta, records, baseline)
        # HWM 条件写：stale 被挡返回 False——无害，本 tick 只是没推进落库，下轮（或别的实例）会重推。
        run_store.project_state(run_id, state)

        stop_start = replanned or past_stop_start(now, deadline)
        recorded = {r.scope_id for r in records if r.scope_id in job_by_scope}
        refused = False
        for act in plan_next(state, max_concurrency, past_stop_start=stop_start, recorded=recorded):
            if act.kind == "start":
                # 先确认 job 存在，再认领：防御跳过时不会留下一个已认领成 running 却无人启动的 job。
                job = job_by_scope.get(act.scope_id) if act.scope_id is not None else None
                if job is None:
                    continue  # plan_next 从 state.jobs 提议、键集是 meta.jobs 的子集，不该发生；防御跳过
                claimed_at = clock()
                if past_stop_start(claimed_at, deadline):
                    refused = True  # 余下的 start 不再逐个检查：已过停止启动的时刻，改为同一轮里重新决策
                    break
                # 认领：多实例并发提议同一 pending，只有一个成功（机制四严格并发闸）。写进记录的认领时刻与算截止时刻的是同一个值。
                if run_store.try_claim_job(run_id, job.scope_id, claimed_at=instant_to_iso(claimed_at)):
                    _launch(run_id, job, launcher, event_log, clock, job_cutoff(claimed_at, job.timeout_s, deadline).at)
            else:
                return _finalize(run_id, meta, records, baseline, state, run_store, result_store, ended_at=now,
                                 recorded=recorded, expired=act.kind == "finalize_expired")
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


def _claim_times(baseline: RunState | None, recorded: Collection[str]) -> dict[str, datetime] | None:
    """快照检查：每个有记录的 job 在这一轮读到的运行态里都带认领时刻时，返回它们的认领时刻；
    有一个不带（或读不出、不带时区），或这一轮读不到运行态，返回 None。

    推进步骤先读运行态、后读事件，手里的运行态可能比事件旧：有记录的 job 不带认领时刻，说明它是在这一轮读运行态之后才被认领的，
    这一轮不收尾，下一轮读到新的运行态再做。不用「取不到认领时刻就按预算说明」这样的回落：那会让拿着旧运行态的推进方用错的说明覆盖
    别人已经写对的判定明细。"""
    if baseline is None:
        return None
    out: dict[str, datetime] = {}
    for sid in recorded:
        js = baseline.jobs.get(sid)
        try:
            out[sid] = instant_from_iso(js.claimed_at if js is not None else None)
        except ValueError:
            return None
    return out


def _finalize(run_id: str, meta: RunMeta, records: list, baseline: RunState | None, state: RunState, run_store: RunStore,
              result_store: ResultStore | None, *, ended_at: datetime, recorded: Collection[str], expired: bool) -> TickResult:
    """收尾分支（plan_next 给出 finalize 或 finalize_expired 时）。写的次序不变：判定明细、使 run 成为终态的写、报告（报告由宿主写）。

    ① 快照检查（`_claim_times`）不过即按继续推进处理；读不到运行态的一轮同样不收尾，到期收尾也就不做。
    ② 判定真值先落：用本 tick 已读的 records（与 state 同一快照，不再读一次），project_full 逐 job 落
       ResultStore；它对有记录而非终态的 job 抛——异常不在本 tick 内捕获、原样抛出，让触发源重试；绝不先写终态再补（之后无人重试，
       产物缺失即永久；ADR 0030 决定三，强制点见 ADR 0031 决定一·补「不变量的强制点」）。保存覆盖同 key、不带条件，保存抛错同样原样
       抛出、这一轮不写终态（ADR 0034 机制三「run 级状态只进不退」条④ K3）。
    ③ 使 run 成为终态：
       - 全部 job 已结束（finalize）：以终态写（`RunStore.commit_job_states`）一次记下 project_full 给出的各 job 的终态，会话与认领时刻
         取这一轮的投影。run 的状态由 adapter 在同一次写里按取法从记录算出（ADR 0031 决定三），投影已写下的终态不被改写。
       - 到期（finalize_expired）：以「执行方自己到期」这条来路做结束写（`RunStore.end_run`），运行态里是 pending 的 job 记 skipped、
         带到期的说明，run 随之成为终态。结束写的条件是写下时没有 running 的 job，读到之后另一个推进方的认领落下时它写不成。
    ④ 终态写的结果：写成且使 run 成为终态即 `COMMITTED`，带着这一轮的判定明细供宿主生成报告；run 在这次写之前已是终态即 `ENDED`，
       不另读；写成而 run 仍未结束不该出现（全部 job 都给出了终态），按继续推进处理。结束写写成即 `COMMITTED`；没写成时重读一次运行态：
       已是终态说明别人已经收尾，返回 `ENDED`；仍未结束（读取之后有了新的认领）返回 `CONTINUE`，新认领的 job 照常在它的截止时刻被停下。
       没使 run 成为终态的一方不生成报告。
    """
    claimed = _claim_times(baseline, recorded)
    if claimed is None or baseline is None:
        return TickResult(TickOutcome.CONTINUE)
    results = project_full(meta, records, claimed_at=claimed)
    if result_store is not None:
        for jr in results:
            result_store.save_job_result(run_id, jr)
    at = instant_to_iso(ended_at)
    if not expired:
        finals = []
        for jr in results:
            projected = state.jobs.get(jr.scope_id)
            finals.append(JobState(scope_id=jr.scope_id, status=jr.status,
                                   session_id=projected.session_id if projected is not None else jr.session_id,
                                   claimed_at=projected.claimed_at if projected is not None else None))
        outcome = run_store.commit_job_states(run_id, finals, ended_at=at)
        if outcome is CommitOutcome.ENDED_RUN:
            return TickResult(TickOutcome.COMMITTED, tuple(results))
        if outcome is CommitOutcome.ALREADY_ENDED:
            return TickResult(TickOutcome.ENDED)
        return TickResult(TickOutcome.CONTINUE)  # 防御：全部 job 都给出了终态，这次写本应使 run 成为终态
    if run_store.end_run(run_id, RUN_ENDINGS["deadline"], ended_at=at):
        return TickResult(TickOutcome.COMMITTED, tuple(results))
    after = run_store.load_run_state(run_id)
    if after is not None and after.status in TERMINAL_STATUSES:
        return TickResult(TickOutcome.ENDED)
    return TickResult(TickOutcome.CONTINUE)
