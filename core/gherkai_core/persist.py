"""RunPersistence（ADR 0030 决定二）：把「一次 run 如何随进度实时落库」收成一处应用服务。

为什么是 core 应用服务、不是每个组合根各写一遍：实时写的编排（逐 job 的提交点 / RUNNING 中间态 / 按 scope_id 增量刷 / 收尾的
结束写与从记录组装结果）对 cli / WebUI / 未来 cron **完全一致，只有注入的 store adapter 不同**。让每个前端各写一遍必漂移。故收成依赖
Store **ports**（不含具体 adapter、不含执行 reducer）的服务，组合根只注入 adapter。

架构对位：schedule 编排**执行**（Engine port），RunPersistence 编排**存储**（Store ports），两者平级、
都在 core、由组合根组合。schedule 一行不碰 store——它经 on_event / on_job_complete 两个回调把事件/JobResult
喂给本服务（sink 只供进度显示，不经本服务；ADR 0026/0030），并经本服务实现的 `RunRecord` 认领 job、在重试之前读 run 级状态、
轮询停手信号（ADR 0054 决策五「执行方服从记录」）。schedule 返回执行事实（`schedule.Execution`），不给出 run 的状态；run 的结果由
本服务从记录组装（`finalize`），没有记录的执行由 `result_without_record` 按同一套规则在内存里组装。

逐 job 的提交点（ADR 0030 决定三）：由执行结果结束的 job 先存判定明细（ResultStore，存成带这次保存生成的标识的一份），再以终态写
（`RunStore.commit_job_states`）记下它的终态并点名那一份（`JobState.result_id`，同决定三「点名」条），run 的状态在同一次写里按取法
随之写下。schedule 返回之后仍有未结束的 job（到期、fail-fast 或使用方中断时没有启动的）由结束写（`RunStore.end_run`）结束，来路取
执行事实交来的那一条。使 run 成为终态的那次写是本进程写成的，本服务才读一次运行态、按其中点名的标识从判定存储读回明细、组装 run 的
结果并生成报告；本进程内存里的执行结果不参与组装，读法与后台报告、explain 相同（`named_details.load_named_details`）。本次执行结束
之前别处已把 run 结束时不覆盖已有的终态、不生成报告，抛 `RunAlreadyEnded`。

并发：写 RunStore 的路径有三条——认领与 RUNNING 中间态刷在 **worker 线程**（认领在起 worker 之前；RUNNING 经 on_event，在 schedule 的
sink_lock **之外** fire，故落库不堵别的 worker 的进度显示）、job 终态写在 **主线程**（经 on_job_complete，在 schedule 等待 job 完成的
循环里串行调用）。RunStore 的每个写入口对并发的别的写入方都是安全的（本机建 run 之后的写入口在文件锁内读改写，云端的每一次写都
带条件），跨进程的别的写入方由它们挡住；本服务**自持一把锁**另有两个用处：护住进程内记下的代表会话与认领时刻（`_session`、`_claimed_at`，读改写跨线程），并让同一
进程里的写按调用次序依次落库。保存明细也在这把锁内（连同本机组合根给的判定存储在保存失败时的退避重试，最多约 7 秒）：停手信号的发布
与「先看信号、再存明细」因此在同一把锁里；代价是重试期间别的 worker 线程的认领与执行中的写随之等待，只在判定存储写不进时出现
（ADR 0030 决定三「保存明细失败」条）。停手信号是一个线程安全的事件标志，读它不取锁、不碰存储。
"""
from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from gherkai_core.errors import RunAlreadyEnded
from gherkai_core.model import (
    TERMINAL_STATUSES,
    Event,
    JobResult,
    JobState,
    ResourceUri,
    RunMeta,
    RunResult,
    RunState,
    ScopeStarted,
    SessionOpened,
    Status,
)
from gherkai_core.named_details import load_named_details, new_result_id
from gherkai_core.ports import ReportStore, ResultStore, RunStore
from gherkai_core.project import assemble_run_result, representative_session
from gherkai_core.run_deadline import system_wall_clock
from gherkai_core.run_status import CommitOutcome, StopSource, ending_of_stop, state_without_record
from gherkai_core.schedule import Execution
from gherkai_core.serialize import instant_to_iso


def initial_run_state(meta: RunMeta, *, started_at: str) -> RunState:
    """一个新 run 的初始运行态，交给 `RunStore.create_run`：各 job 与 run 都是 pending，started_at 照填（记录里的写法），ended_at、
    run 级说明与 high_water_mark 都缺席（ended_at 由使 run 成为终态的那次写填；high_water_mark 只由后台推进的投影写写下，两个
    adapter 都把缺席当作 0）。

    建 run 的各处（前台执行的 `RunPersistence.begin`、本机后台推进进程、云端 submit）都用它，初始运行态只有这一种形态。云端 adapter
    建 run 时另写的写入序号初值 0 不属于运行态模型，由 `DynamoDBRunStore` 写 STATE 条目时自带。"""
    return RunState(
        run_id=meta.run_id,
        status=Status.PENDING,
        jobs={job.scope_id: JobState(scope_id=job.scope_id, status=Status.PENDING) for job in meta.jobs},
        started_at=started_at,
    )


@dataclass(frozen=True)
class FinalizedRun:
    """`RunPersistence.finalize` 的结果：从记录组装出的 run 结果，与报告入口页的位置（没有报告落点、或写报告失败时为 None）。"""

    result: RunResult
    report_index: ResourceUri | None


class RunPersistence:
    """编排 RunStore + ResultStore（+ 可选 ReportStore）随进度实时落库（ADR 0030），并向调度循环提供这次 run 的记录（实现
    `ports.RunRecord`，ADR 0054 决策五）。

    生命周期：begin（run 开始）→ claim（每个 job 起 worker 之前）+ on_event（运行中刷 RUNNING）+ on_job_complete（job 完成：存明细，
    写终态并点名它）→ finalize（schedule 返回之后：需要时做结束写，从记录组装 run 的结果并生成报告）。重试之前调 still_open；
    ended_elsewhere 随时可读。
    注入点：on_event → schedule 的 on_event（sink_lock 外）；on_job_complete → schedule 的 on_job_complete（主线程）；本对象本身 →
    ScheduleOpts.record。
    begin 在 run 已存在时失败（RunStore.create_run 抛 `RunAlreadyExists`，什么都不改）；finalize 在 run 已被别处记为已结束时
    抛 `RunAlreadyEnded`。

    停手信号（ended_elsewhere）汇集三处发现：认领被拒、重试之前读到 run 级终态、写 job 状态时 RunStore 报告 run 级已结束（on_event 的
    执行中写返回 False，on_job_complete 的终态写返回 ALREADY_ENDED）。成立之后不撤销。得知 run 已结束的那次存储操作与信号的发布在
    本服务的同一把锁内完成，on_job_complete 也在这把锁内先看信号、再存明细：任何一次操作得知之后，此后才取到锁的 on_job_complete
    都不再存明细（ADR 0054 决策五「执行方得知 run 已结束之后就不存明细」条）。

    clock：组合根注入的墙钟（返回带时区的 datetime，与调度循环同一个读取点），终态写与结束写的结束时刻、报告的生成时刻经它取；缺省取
    系统墙钟。
    """

    def __init__(
        self,
        run_id: str,
        run_store: RunStore,
        result_store: ResultStore,
        report_store: ReportStore | None = None,
        *,
        clock: Callable[[], datetime] = system_wall_clock,
    ) -> None:
        self._run_id = run_id
        self._run_store = run_store
        self._result_store = result_store
        self._report_store = report_store
        self._clock = clock
        self._lock = threading.Lock()  # 单一 store 锁：串行所有写 store 的入口（认领 + RUNNING 刷 + 终态写，跨线程）
        # 每个 scope 的代表会话与锁定状态（ADR 0051 决策 4）：两个 RunStore adapter 的 update_job_state 都整项覆盖 JobState，
        # 本服务须自己记住代表会话，任何写入都不能用 None 覆盖已有的 session_id。规则函数与 reduce_event 共用一份。
        self._session: dict[str, tuple[str | None, bool]] = {}
        # 每个 scope 的认领时刻（记录里的 ISO 写法，ADR 0054 决策五）：认领写成时记下，此后开始执行与结束两次 job 状态写都带上——
        # 同一理由，adapter 的整项替换不带它就会把它抹掉。没有认领过的 job 没有这一项。
        self._claimed_at: dict[str, str] = {}
        self._ended_run = False  # 本进程的某次写使 run 成为终态（终态写返回 ENDED_RUN，或结束写写成）
        self._ended = threading.Event()  # 停手信号：已发现这个 run 被别处记为已结束

    def begin(self, run_meta: RunMeta, *, started_at: str) -> None:
        """run 开始（schedule 之前）：先探活三个 store，再写 definition + 初始运行态（`initial_run_state`）。

        满足 ADR 0027「提交即返回 runId」——definition 必先于批量运行存在。

        **create_run 前先 preflight**：探底层可达（云端探表/桶，local no-op）。桶/表名错
        一律在此暴露（不管有无 offload 内容），组合根 gated except 归到退出码 2——消除「桶名错因是否有 offload
        内容分裂成退出码 2 还是退出码 1」的不一致。探活在 create_run（真写）之前、早于起 worker，不产生引擎费用。
        """
        initial = initial_run_state(run_meta, started_at=started_at)
        with self._lock:
            # 探活先于任何写：三个 store 各探自己的后端（云端探表/桶失败即抛，local no-op）
            self._run_store.preflight()
            self._result_store.preflight()
            if self._report_store is not None:
                self._report_store.preflight()
            self._run_store.create_run(run_meta, initial)

    def claim(self, scope_id: str, claimed_at: datetime) -> bool:
        """认领一个 job（`RunRecord.claim`，在 worker 线程里、起 worker 之前调用）：经 `RunStore.try_claim_job` 的条件写把它从 pending
        置为 running，认领时刻按记录的写法（UTC 的 ISO 串，与组合根写时间戳同一形态）随这次写落库并记下。被拒即发出停手信号（在同
        一把锁内，见类文档串）、返回 False：前台执行时这个 job 只会在这里被认领一次，被拒的原因只能是 run 级已是终态。写入失败照常
        抛出。"""
        claimed_iso = instant_to_iso(claimed_at)
        with self._lock:
            claimed = self._run_store.try_claim_job(self._run_id, scope_id, claimed_at=claimed_iso)
            if claimed:
                self._claimed_at[scope_id] = claimed_iso
            else:
                self._ended.set()
        return claimed

    def still_open(self) -> bool:
        """读一次 run 级状态（`RunRecord.still_open`，job 级重试重新起 worker 之前调用）：pending 或 running 返回 True；已是终态即发出
        停手信号（读与发布在同一把锁内，见类文档串）、返回 False。运行态不存在（begin 之后不该发生）抛 FileNotFoundError，读取失败
        照常抛出。"""
        with self._lock:
            state = self._run_store.load_run_state(self._run_id)
            if state is None:
                raise FileNotFoundError(f"run {self._run_id} 的运行状态不存在，无法确认它是否已结束")
            if state.status in (Status.PENDING, Status.RUNNING):
                return True
            self._ended.set()
            return False

    def ended_elsewhere(self) -> bool:
        """停手信号（`RunRecord.ended_elsewhere`）：是否已发现这个 run 被别处记为已结束。只读进程内的标记。"""
        return self._ended.is_set()

    @property
    def ended_run(self) -> bool:
        """本进程的某次写是否已使 run 成为终态（终态写返回 ENDED_RUN，或结束写写成）。只读进程内的标记，不读存储。成立之后记录
        不再变：此后的存储失败只会出在为组装 run 的结果而读运行态的那一次（finalize 第 4 步），调用方据此说明记录已是终态。"""
        return self._ended_run

    def _write_job_state(self, job_state: JobState) -> None:
        """写一个 job 执行中的运行态（调用方持锁）：RunStore 报告 run 级在这次写时已是终态（没有写成）即发出停手信号。"""
        if not self._run_store.update_job_state(self._run_id, job_state):
            self._ended.set()

    def on_event(self, event: Event) -> None:
        """事件旁路观察者（注入 schedule 的 on_event，在 sink_lock **之外**调，ADR 0030 决定三）：
        收 SessionOpened（origin 不是 attempted，ADR 0051 决策 4：scope_started 之前的准备期 job 即算 RUNNING）或 ScopeStarted 实时刷该 job 为
        RUNNING，session_id 按代表会话规则（scope_started 的值一经取到锁定；此前取最近一条非 attempted 的 session_opened；
        attempted 不写入），写入永不带 None 覆盖已有值；认领时刻原样带上。

        在 worker 线程被调、多 worker 并发——故写 store 经本服务的锁串行（跨线程安全）。
        放在 sink_lock 外，故这次磁盘 RMW 不阻塞别的 worker 的进度显示（与 sink 分离的关键）。
        """
        if isinstance(event, (ScopeStarted, SessionOpened)):
            with self._lock:
                current, locked = self._session.get(event.scope_id, (None, False))
                session_id, locked = representative_session(current, locked, event)
                self._session[event.scope_id] = (session_id, locked)
                if isinstance(event, SessionOpened) and event.origin == "attempted" and session_id is None:
                    return  # 结果未知的尝试不产生带 None 的写入（job 态由后续事件或终态写落）
                self._write_job_state(JobState(scope_id=event.scope_id, status=Status.RUNNING, session_id=session_id,
                                               claimed_at=self._claimed_at.get(event.scope_id)))

    def on_job_complete(self, jr: JobResult) -> None:
        """每个由执行结果结束的 job 完成（在主线程等待 job 完成的循环里串行调用）：逐 job 的提交点——判定明细【先】存，再以终态写记下
        这个 job 的终态并点名那一份，run 的状态在同一次写里随之写下（ADR 0030 决定三）。

        - jr 的状态不是终态即抛 ValueError、什么都不写：判定只有终态，强制点在保存明细之前（ADR 0031 决定一·补）。
        - 停手信号已成立（已发现 run 被别处结束）时不存明细、不写终态：迟到的结果不被采用（ADR 0054 决策五）。
        - 否则在锁内看过停手信号之后生成一个标识（`named_details.new_result_id`），把明细存成带这个标识的一份；存不成即原样抛出，这个
          job 这次不写终态（本机组合根给的判定存储先按退避重试，同一个标识，用尽才抛出；ADR 0030 决定三「保存明细失败」条）。
        - 存成之后以终态写记下终态、点名这个标识（`JobState.result_id`）。终态写报告 run 在这次写之前已是终态（ALREADY_ENDED）即发出
          停手信号，存下的那一份没被点名、不被读；调度循环在这个回调返回之后当场读进来。这次写使 run 成为终态（ENDED_RUN）时记下，
          收尾不再做结束写。报告不在这里生成，留到 finalize，明细届时按运行态里的标识读回。
        没有启动的 job schedule 不回调，它们由收尾的结束写结束、没有判定明细。终态写带的会话取 jr 的代表会话，它为 None 时退回本服务已记
        的值，不用 None 覆盖（ADR 0051 决策 4）；认领时刻原样带上。
        """
        if jr.status not in TERMINAL_STATUSES:
            raise ValueError(f"job {jr.scope_id} 的结果不是终态（{jr.status.value}），不能记下")
        with self._lock:
            if self._ended.is_set():
                return  # 得知 run 已结束之后不存明细（ADR 0054 决策五）
            result_id = new_result_id()
            self._result_store.save_job_result(self._run_id, result_id, jr)  # 判定明细【先】，存成带这个标识的一份
            remembered = self._session.get(jr.scope_id, (None, False))[0]
            final = JobState(scope_id=jr.scope_id, status=jr.status, session_id=jr.session_id or remembered,
                             claimed_at=self._claimed_at.get(jr.scope_id), result_id=result_id)
            outcome = self._run_store.commit_job_states(self._run_id, [final],
                                                        ended_at=instant_to_iso(self._clock()))  # 终态【后】，并点名这一份
            if outcome is CommitOutcome.ALREADY_ENDED:
                self._ended.set()  # 存下的那一份没被点名、不被读
                return
            if outcome is CommitOutcome.ENDED_RUN:
                self._ended_run = True

    def finalize(self, execution: Execution) -> FinalizedRun:
        """run 结束（schedule 返回之后）：需要时做结束写，再从记录组装 run 的结果并生成报告（ADR 0030 决定三「run 结束」一段）。

        1. 本进程的终态写已使 run 成为终态：不再写，直接到第 4 步。
        2. 已发现 run 被别处结束（停手信号成立）：不写、不生成报告，读回一次运行态，抛 `RunAlreadyEnded`（带读回的运行态）。这次读回
           失败或读不到运行态时仍抛 `RunAlreadyEnded`（`recorded` 为 None，读回失败时那个异常作为它的起因）：run 已被别处结束这个
           结论不靠读回，调用方照同一个出口结束。
        3. 否则仍有未结束的 job：以 execution.stopped_by 这条来路做结束写（说明取 `RUN_ENDINGS` 里那一行，结束时刻经注入的墙钟取）。
           来路为空、或为「已发现 run 被别处结束」而停手信号没有成立，执行事实不自洽，抛 ValueError（`run_status.ending_of_stop`，
           与没有记录时同一处检查）。结束写没有写成时读回一次：运行态
           不存在抛 FileNotFoundError（begin 之后不该发生）；已是终态说明别处恰在这之前结束了它，发出停手信号并抛 `RunAlreadyEnded`；
           仍未结束（有 running 的 job，而本进程的 job 都已结束）抛 RuntimeError。
        4. 使 run 成为终态的那次写是本进程写成的：读一次运行态。终态之后运行态不再变，这次读到的就是定论。各 job 的明细按其中点名的
           标识从判定存储读回（`named_details.load_named_details`，与后台报告、explain 同一种读法；由结束写结束的 job 没有标识、不读），
           不用本进程内存里的那一份：输出与随后的 status、explain、报告出自同一份记录（ADR 0027「RunResult 的组装只有一处」条）。再组装
           run 的结果（`project.assemble_run_result`，墙钟取 execution.duration_ms）：汇总、`--json`、退出码与报告都出自它。读运行态与
           读被点名明细的这一次不在报告的失败隔离之内：读失败照常抛出（被点名的那一份读不到抛 `NamedDetailMissing`，是 OSError 的子类），
           按运行期落库失败处理，不生成报告；这时 `ended_run` 已为 True，调用方据此说明记录已是终态。
        5. 有报告落点时写报告（ReportStore.write），生成时刻与结束写的结束时刻取同一次读数。

        **写不成时不覆盖、不写报告**：本次执行结束之前别处已把 run 记为已结束时，已有的终态对所有写入方不可变（ADR 0054 决策五「结束时
        前台执行方不覆盖已有的终态」条），报告只由使 run 成为终态的那次写的写入方生成（ADR 0027「ReportStore 接口：整 run 一次写」节），
        所以都不写。

        **ReportStore.write 的失败被隔离**（ADR 0030 决定三「ReportStore.write 失败隔离」注）：报告是派生只读视图、可从记录重建、永不作
        判定源。它抛异常（磁盘满/路径不可写等）时不击穿已到终态的 run：report_index 为 None，调用方照常输出汇总与退出码。结束写、读运行态
        与读被点名明细本身**不**在隔离之内：记录没有写下或读不回是真问题，必须冒泡。
        """
        with self._lock:
            now = instant_to_iso(self._clock())
            if not self._ended_run:
                if self._ended.is_set():
                    try:
                        recorded = self._run_store.load_run_state(self._run_id)
                    except Exception as e:
                        raise RunAlreadyEnded(self._run_id, None) from e
                    raise RunAlreadyEnded(self._run_id, recorded)
                self._end_remaining(execution.stopped_by, ended_at=now)
            state = self._run_store.load_run_state(self._run_id)
            if state is None:
                raise FileNotFoundError(f"run {self._run_id} 的运行状态不存在，无法给出结果")
            details = load_named_details(self._run_id, state.jobs.values(), self._result_store)
            result = assemble_run_result(execution.run_meta, state, details.values(), duration_ms=execution.duration_ms)
            if self._report_store is None:
                return FinalizedRun(result, None)
            try:
                index = self._report_store.write(self._run_id, result, created_at=now)
            except Exception:
                # 派生视图写失败不击穿已到终态的 run（状态在运行态、判定明细在 ResultStore）；报告可从记录重建。
                # 不留痕：曾存 traceback 到 _report_error 供"可选读取"，但生产端（cli）从不消费——按悬空字段判据删。
                index = None
            return FinalizedRun(result, index)

    def _end_remaining(self, stopped_by: StopSource | None, *, ended_at: str) -> None:
        """以 stopped_by 这条来路做结束写（调用方持锁；见 finalize 第 3 步）。写成即记下本进程使 run 成为终态。"""
        if self._run_store.end_run(self._run_id, ending_of_stop(stopped_by), ended_at=ended_at):
            self._ended_run = True
            return
        recorded = self._run_store.load_run_state(self._run_id)
        if recorded is None:
            raise FileNotFoundError(f"run {self._run_id} 的运行状态不存在，无法记下结果")
        if recorded.status in TERMINAL_STATUSES:
            self._ended.set()
            raise RunAlreadyEnded(self._run_id, recorded)
        raise RuntimeError(f"run {self._run_id} 仍有执行中的 job，无法结束它")


def result_without_record(execution: Execution, *, ended_at: str) -> RunResult:
    """没有记录的执行（`run --no-report`）的 run 结果：运行态按有记录时两个写入口对运行态的作用在内存里算出
    （`run_status.state_without_record`：先记下判出结果的 job 的终态，run 还没到终态时按余下的 job 不再启动的来源做结束写），再经与
    有记录时同一处组装（`project.assemble_run_result`，各 job 的判定明细就是 execution.results）。ended_at 是记作结束时刻的那一刻
    （记录里的写法）。"""
    state = state_without_record(execution.run_meta, execution.results, execution.stopped_by, ended_at=ended_at)
    return assemble_run_result(execution.run_meta, state, execution.results, duration_ms=execution.duration_ms)
