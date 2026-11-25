"""reconciler（ADR 0034）：无状态批量运行的推进编排——被事件唤醒、幂等、并发安全。

`tick(run_id, meta, …, clock=…, result_store=…)` 一步推进：取时刻 → 读库中运行态（已结束即停止推演）→ 读 EventLog 全量 records →
project() 推 RunState → 投影写（只前进、不越过 running）→ 为这一轮已有结果的 job 各存一份带标识的判定明细、再以一次终态写记下它们的
终态并点名各自的那一份，run 的状态随之写下 → plan_next() 在这一轮读到的运行态加上这次终态写的作用上作推进决策：对每个 start 动作重取
时刻、未过停止启动的时刻才认领，认领成功即算出截止时刻、经注入的 Launcher 起 job；已过停止启动的时刻、没有执行中的 job 而仍有未启动的
job 时做到期的结束写。结果是 `TickOutcome`，宿主据它决定继续推进、从记录生成报告后结束，还是直接结束（ADR 0034 机制三「run 级状态
只进不退」条④；ADR 0054 决策二后台推进条「决策」「收尾与报告」两项）。报告经 `write_report_from_record` 从记录生成：读运行态，按其中
点名的标识读回明细（ADR 0030 决定三「点名」条）；处置方经不记日志、失败原样抛出的 `generate_report_from_record` 生成。

**无状态 + 幂等**：所有调度态在 EventLog / RunStore（持久），进程内不留。谁调 tick、何时调、并发调都安全
（CAS + HWM 条件写兜底）——两个后端的推进器（云端由流与定时触发唤起的 Lambda，可以重叠；本机的后台推进进程，一个 run 至多一个，
ADR 0034「推进器与触发源」）共用这一个 tick。「是否已过停止启动的时刻」同样不记：每一轮按当前时刻判断（ADR 0054 决策二后台推进条
「不记已过停止启动」）。

**时刻只经注入的时钟取**：tick 自己不读系统时钟，宿主注入与前台同一个读取点（组合根的 `compose.now`），返回带时区的 datetime；
写进记录时经 `serialize.instant_to_iso`，与组合根写时间戳同一种写法。

**守窄腰（[0016]/[0026]）**：本模块不 import subprocess/boto3——「起一个 job」的执行能力经注入的 `Launcher`
（本机后端下起 subprocess worker、旁路落 SQLite 并观察退出；云端后端下调 ECS RunTask）。core 只吐动作、调 Launcher，
副作用在 adapter/组合根。project/plan_next 是纯函数（gherkai_core.project）。
"""
from __future__ import annotations

import enum
import logging
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime
from typing import Protocol

from gherkai_core.model import TERMINAL_STATUSES, Job, JobState, RunMeta, RunState
from gherkai_core.named_details import load_named_details, new_result_id
from gherkai_core.ports import ReportStore, ResultStore, RunStore
from gherkai_core.project import assemble_run_result, plan_next, project, project_full, run_duration_ms
from gherkai_core.run_deadline import deadline_of, job_cutoff, past_stop_start
from gherkai_core.run_status import RUN_ENDINGS, CommitOutcome, commit_applied
from gherkai_core.serialize import instant_from_iso, instant_to_iso

logger = logging.getLogger("gherkai_core.reconcile")


class TickOutcome(enum.Enum):
    """一次 `tick` 的结果（ADR 0034 机制三「run 级状态只进不退」条④；ADR 0054 决策二后台推进条「收尾与报告」）。

    后两种都让宿主结束对这个 run 的推进（本机的推进循环退出，云端这一次调用当场清扫这个 run 的 task，`COMMITTED` 在生成报告之后）；
    只有 `COMMITTED` 让宿主生成 RunReport。
    """

    # 继续推进：这一次 tick 没有使 run 成为终态（其中可能已记下部分 job 的终态）；或读不到运行态；或到期的结束写没写成而重读的运行态
    # 仍未结束（写下时有执行中的 job：读取之后又有了新的认领）。宿主照常做超时处置并等下一轮。
    CONTINUE = "continue"
    # 这一方的写使 run 成为终态：记下最后一批 job 终态的那次终态写，或到期的结束写，由这一方写成。推进步骤不交回判定明细，宿主从记录
    # 生成报告（`write_report_from_record`：读运行态、按其中点名的标识读回明细）。
    COMMITTED = "committed"
    # run 已结束而使它成为终态的不是这一方：这一轮读到的运行态已是终态（读到即返回，不再推演、投影、认领，也不存明细），或终态写报告
    # run 在这次写之前已是终态，或到期的结束写没写成、重读到别人已写下的终态。宿主不生成报告：报告只由使 run 成为终态的那一方生成。
    ENDED = "ended"


class EventLog(Protocol):
    """事件日志口（reconciler 读全量 records 重放）。`tick` 只用这两个方法：读全量 records，以及 launch 失败补偿时的
    `record_exit`。其余退出记录来自退出观察者（本机 launcher 的 proc.wait、云端 exit-observer Lambda、本机同步 run 的
    `EventRecordingEngine`）与云端的超时处置（对无踪 task 的补写、遇已停止却缺退出记录的 task 时按 DescribeTasks 结果补写，与观察者
    同一提取算法）；云端超时处置直接用 `DdbEventLog` 上的点查与条件补写，不经这个协议。worker 执行事件由 worker（云端）或 launcher
    旁路（本机）写。各写入方只记事实，是否已过截止时刻由投影判断（`project._reduce_scope`）。"""

    def records(self) -> list: ...  # list[EventRecord]（gherkai_core.project）

    # 覆盖同键（独立键空间，机制一）：观察到的退出、launch 失败补偿与云端按 task 对象的补写都经这里。timed_out：发过超时的停止
    # 请求（ADR 0034「job timeout」节归因链）。exited_at：退出时刻（带时区），写入方观察到退出的那一刻；没有可观察的退出时刻时为
    # None。两项都只是事实，写入方不比较截止时刻。
    def record_exit(self, scope_id: str, exit_code: int | None, *, timed_out: bool = False,
                    reason: str | None = None, exited_at: datetime | None = None) -> None: ...


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


def generate_report_from_record(run_id: str, meta: RunMeta, run_store: RunStore, result_store: ResultStore,
                                report_store: ReportStore, *, created_at: str) -> None:
    """按 run_id 从记录生成 RunReport（派生视图，**永远最后**；ADR 0027「ReportStore 接口：整 run 一次写」节）。只由使 run 成为终态的
    那次写的写入方调用：推进器经 `write_report_from_record`，处置方直接调它（ADR 0054 决策七「报告」）。

    一次读运行态、按它算 run 级墙钟（started_at 到 ended_at，`project.run_duration_ms`），按其中各 job 点名的标识从判定存储读回明细
    （`named_details.load_named_details`，与前台收尾、explain 同一种读法，ADR 0030 决定三「点名」条），组装 run 的结果
    （`project.assemble_run_result`：状态与 job 级说明取运行态，job 按 meta 逐个列出），再写报告。由结束写结束的 job 没有标识、不读，
    只有状态与说明；存储里没被点名的明细（别的推进方存下而终态由这一方写下的、存下之后终态写没写成的）不读。判定明细不另读一次事件
    重算：重算用的事件可能已经变了（云端补写的未知退出之后又被真实的退出码覆盖）。

    读记录与写报告都按 run_id，组装用的运行定义也带这个标识，不取 meta 里的那一个：处置方按 run 目录的名字处置，复制出来的 run 目录
    里两者不同（ADR 0054 决策七「报告」）。推进器生成的 run 两者相同。

    任何失败原样抛出、不记日志：运行态不存在抛 FileNotFoundError，被点名的那一份读不到抛 `NamedDetailMissing`，运行态与运行定义
    不对应抛 ValueError，读写存储的失败照原样。报告是否生成由调用方据此作结构化的结果（处置方要说明报告没有生成及其原因，不把
    回溯打到终端，ADR 0039）。created_at：报告的生成时刻（记录里的写法）。纯编排：不 import boto3。"""
    state = run_store.load_run_state(run_id)
    if state is None:
        raise FileNotFoundError(f"run {run_id} 的运行状态不存在，无法生成报告")
    details = load_named_details(run_id, state.jobs.values(), result_store)
    named = meta if meta.run_id == run_id else replace(meta, run_id=run_id)
    result = assemble_run_result(named, state, details.values(), duration_ms=run_duration_ms(state))
    report_store.write(run_id, result, created_at=created_at)


def write_report_from_record(meta: RunMeta, run_store: RunStore, result_store: ResultStore,
                             report_store: ReportStore | None, *, created_at: str) -> None:
    """推进器的写使 run 成为终态之后，从记录生成 RunReport（`generate_report_from_record`，按 meta 里的 run 标识；ADR 0054 决策二
    后台推进条「收尾与报告」）。宿主只在 tick 返回 `TickOutcome.COMMITTED` 后调。

    整段在失败隔离之内：报告是派生只读视图，判定明细与终态在生成之前都已落下，读运行态、读回明细、组装与写报告的任何失败都不击穿已到
    终态的 run，这一步的失败也没有人重试（ADR 0030 决定三「ReportStore.write 失败隔离」注）。运行态读不到、被点名的那一份读不到
    （`NamedDetailMissing`）时同样不生成报告，日志里留一条带回溯的警告：两个宿主（云端推进器 Lambda、本机后台推进进程）的日志都不到
    使用者的终端。report_store 为 None 时什么都不做：不读运行态，也不读回明细。纯编排：不 import boto3。
    """
    if report_store is None:
        return
    try:
        generate_report_from_record(meta.run_id, meta, run_store, result_store, report_store, created_at=created_at)
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
    result_store: ResultStore,
) -> TickOutcome:
    """推进一步，返回 `TickOutcome`（三种结果的含义见它的文档串）。

    result_store：判定存储，必传（ADR 0034 机制三「run 级状态只进不退」条④ K3）。由执行结果结束的 job 都在这里存下一份明细、由终态写
    点名，「由执行结果结束」与「由结束写结束」只看终态有没有点名（ADR 0030 决定三「点名」条），所以推进路径上没有不存明细的终态写。

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
       不写 job 的终态（adapter 写的时候把事件推出的终态钳在 running）；只交 baseline 里未结束的 job，已是终态的 job 不发写（ADR 0034
       机制三「逐 job 写：内容不变不写，注定不成立的不发」段）；写不成（stale 被挡、run 已结束）无害，返回值不看。
    3. 记下这一轮已有结果的 job 的终态（选哪些 job 见 `_committable`）：project_full 从同一份 records 给出它们的判定明细，每个 job 各
       生成一个标识（`named_details.new_result_id`）、存成带这个标识的一份，再以一次终态写（`RunStore.commit_job_states`）记下它们的
       终态并点名各自的那一份（`JobState.result_id`），会话与认领时刻取这一轮的投影。云端的终态写被写入序号挡下、重读再算时用的仍是
       这组 JobState，点名的标识不变（ADR 0030 决定三「被点名的那一份」条）。其中有 job 在库中已由别的推进方写下终态时，终态写跳过它，
       它这一轮存下的那一份不被点名，库中点名的是写成终态那一方的。任一份明细存不成即原样抛出：这一遍（从读运行态起算，重做是另一遍）
       一个终态都不写，也不认领、不做结束写，这一遍已存下明细的 job 一并留在 running、存下的那几份不被点名，下一轮另生成标识再存再写；
       重做那一遍存不成时，第一遍已写下的终态与已做的认领不收回（ADR 0034 机制三「run 级状态只进不退」条④ K3）。本函数不等待、不重试：
       本机推进器的组合根给出的判定存储自带保存失败的退避重试（同一个标识），云端由流的重试或之后的触发再做（ADR 0030 决定三「保存
       明细失败」条）。终态写的结果：使 run 成为终态即返回 `COMMITTED`；run 在这次写之前已是终态即返回 `ENDED`，不另读、不启动
       job；run 仍未结束时，以这次写对 baseline 的作用（`run_status.commit_applied`）作推进决策用的运行态。
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
       启动。
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
    replanned = False
    while True:
        now = clock()
        # 基线取当前 RunStore 态，先于读事件：已结束时省掉全量事件读，判停、推演与推进决策用的是同一份 baseline。基线让 project 的
        # job 态单调不倒退（已认领成 running 但 worker 还没吐 scope_started 的 job，不被降回 pending → 不重复 launch，机制四）。
        # 首 tick 时 STATE 已由 create_run 建。手里的运行态可能比事件旧，写终态之前按 job 检查，见 `_committable`。
        baseline = run_store.load_run_state(run_id)
        if baseline is None:
            return TickOutcome.CONTINUE
        if baseline.status in TERMINAL_STATUSES:
            return TickOutcome.ENDED
        records = event_log.records()
        state = project(meta, records, baseline)
        # 投影写：stale 被挡、run 已结束时返回 False——无害，本 tick 只是没推进落库，下轮（或别的实例）会重推。只交 baseline 里未结束的
        # job（ADR 0034 机制三「逐 job 写：内容不变不写，注定不成立的不发」段）：终态只写一次、之后不变，对已是终态的 job 的逐 job 写注定
        # 被条件挡下，云端却按整个 STATE 条目计费。跳过不改变结果，依据是终态不可变，不是「与 baseline 相同」。
        run_store.project_state(run_id, replace(state, jobs={
            sid: js for sid, js in state.jobs.items()
            if sid in baseline.jobs and baseline.jobs[sid].status not in TERMINAL_STATUSES}))

        view = baseline
        claims = _committable(baseline, state)
        if claims:
            results = project_full(meta, [r for r in records if r.scope_id in claims], claimed_at=claims)
            finals: list[JobState] = []
            for jr in results:
                result_id = new_result_id()
                # 明细先存，一个 job 一个标识；任一份失败即原样抛出：这一遍不写终态、不认领、不做结束写，已存下的几份都不被点名
                result_store.save_job_result(run_id, result_id, jr)
                js = state.jobs[jr.scope_id]
                finals.append(JobState(scope_id=jr.scope_id, status=jr.status, session_id=js.session_id,
                                       claimed_at=js.claimed_at, result_id=result_id))
            at = instant_to_iso(now)
            # 一次终态写记下它们，各点名各自的那一份；云端被写入序号挡下时在 adapter 里重读再算，用的仍是这组 JobState（同一组标识）
            outcome = run_store.commit_job_states(run_id, finals, ended_at=at)
            if outcome is CommitOutcome.ENDED_RUN:
                return TickOutcome.COMMITTED
            if outcome is CommitOutcome.ALREADY_ENDED:
                return TickOutcome.ENDED
            applied, _ = commit_applied(baseline, finals, ended_at=at)
            assert applied is not None  # baseline 未结束，终态写的作用总能算出
            view = applied
        # 推进决策按运行定义的次序看 job（理由见 docstring 第 4 项）
        view = replace(view, jobs={j.scope_id: view.jobs[j.scope_id] for j in meta.jobs if j.scope_id in view.jobs})

        stop_start = replanned or past_stop_start(now, deadline)
        refused = False
        for act in plan_next(view, max_concurrency, past_stop_start=stop_start):
            if act.kind == "expire":
                return _end_expired(run_id, run_store, ended_at=now)
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
        return TickOutcome.CONTINUE


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


def _end_expired(run_id: str, run_store: RunStore, *, ended_at: datetime) -> TickOutcome:
    """到期的结束写：以「执行方自己到期」这条来路结束 run（`RunStore.end_run`，ADR 0054 决策二第 3 条与后台推进条「收尾与报告」），
    运行态里是 pending 的 job 记 skipped、带到期的说明，run 随之成为终态。结束写的条件是写下时 run 未结束、没有 running 的 job。结束写
    不点名：由它结束的 job 没有标识，已由终态写记下的 job 点名的标识原样保留。

    写成即 `COMMITTED`。没写成时重读一次运行态：已是终态说明别人已经结束了它，返回 `ENDED`；仍未结束（写下时有执行中的 job：读取之后
    有了新的认领）或读不到返回 `CONTINUE`，新认领的 job 照常在它的截止时刻被停下。"""
    if run_store.end_run(run_id, RUN_ENDINGS["deadline"], ended_at=instant_to_iso(ended_at)):
        return TickOutcome.COMMITTED
    after = run_store.load_run_state(run_id)
    if after is not None and after.status in TERMINAL_STATUSES:
        return TickOutcome.ENDED
    return TickOutcome.CONTINUE
