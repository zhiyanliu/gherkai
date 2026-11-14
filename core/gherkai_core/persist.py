"""RunPersistence（ADR 0030 决定二）：把「一次 run 如何随进度实时落库」收成一处应用服务。

为什么是 core 应用服务、不是每个组合根各写一遍：实时写的编排（commit-point 写序 / RUNNING 中间态 /
按 scope_id 增量刷）对 cli / WebUI / 未来 cron **完全一致，只有注入的 store adapter 不同**。让每个前端各写
一遍必漂移。故收成依赖 Store **ports**（不含具体 adapter、不含执行 reducer）的服务，组合根只注入 adapter。

架构对位：schedule 编排**执行**（Engine port），RunPersistence 编排**存储**（Store ports），两者平级、
都在 core、由组合根组合。schedule 一行不碰 store——它经 on_event / on_job_complete 两个回调把事件/JobResult
喂给本服务（sink 只供进度显示，不经本服务；ADR 0026/0030）。

commit-point 写序（ADR 0030 决定三）：数据面 ResultStore 先逐 job 落 → 控制面 RunStore.try_finalize 最后写。
「收尾写一落，就表示 run 已提交、判定就绪」。收尾与别的写入方用同一个条件写（ADR 0054 决策五）：run 级已是终态时
不覆盖它，抛 `RunAlreadyEnded`。

并发：两条写 RunStore 的路径——RUNNING 中间态刷在 **worker 线程**（经 on_event，在 schedule 的 sink_lock **之外** fire，
故落库不堵别的 worker 的进度显示）、job 终态刷在 **主线程**（经 on_job_complete，在 schedule 等待 job 完成的循环里串行调用）。
RunStore 的每个写入口对并发的别的写入方都是安全的（本机在文件锁内读改写，云端的每一次写都带条件），跨进程的别的写入方由它们挡住；本服务
**自持一把锁**另有两个用处：护住进程内记下的代表会话（`_session`，读改写跨线程），并让同一进程里的写按调用次序依次落库。
"""
from __future__ import annotations

import threading

from gherkai_core.errors import RunAlreadyEnded
from gherkai_core.model import (
    Event,
    JobResult,
    JobState,
    RunMeta,
    RunResult,
    RunState,
    ScopeStarted,
    SessionOpened,
    Status,
)
from gherkai_core.ports import ReportStore, ResultStore, RunStore
from gherkai_core.project import representative_session


class RunPersistence:
    """编排 RunStore + ResultStore（+ 可选 ReportStore）随进度实时落库（ADR 0030）。

    生命周期：begin（run 开始）→ on_event（运行中刷 RUNNING）+ on_job_complete（job 完成落终态）→ finalize（commit point）。
    注入点：on_event → schedule 的 on_event（sink_lock 外）；on_job_complete → schedule 的 on_job_complete（主线程）。
    begin 在 run 已存在时失败（RunStore.create_run 抛 FileExistsError，什么都不改）；finalize 在 run 已被别处记为已结束时
    抛 `RunAlreadyEnded`。
    """

    def __init__(
        self,
        run_id: str,
        run_store: RunStore,
        result_store: ResultStore,
        report_store: ReportStore | None = None,
    ) -> None:
        self._run_id = run_id
        self._run_store = run_store
        self._result_store = result_store
        self._report_store = report_store
        self._lock = threading.Lock()  # 单一 store 锁：串行所有写 store 的入口（RUNNING 刷 + 终态刷，跨线程）
        # 每个 scope 的代表会话与锁定状态（ADR 0051 决策 4）：两个 RunStore adapter 的 update_job_state 都整项覆盖 JobState，
        # 本服务须自己记住代表会话，任何写入都不能用 None 覆盖已有的 session_id。规则函数与 reduce_event 共用一份。
        self._session: dict[str, tuple[str | None, bool]] = {}

    def begin(self, run_meta: RunMeta, *, started_at: str) -> None:
        """run 开始（schedule 之前）：先探活三个 store，再写 definition + 初始全 pending 运行态。

        满足 ADR 0027「提交即返回 runId」——definition 必先于批量运行存在。各 job 摆 PENDING、总 PENDING、
        started_at 填、ended_at 缺席（finalize 时填）。

        **create_run 前先 preflight（ADR 0030 决定七）**：探底层可达（云端探表/桶，local no-op）。桶/表名错
        一律在此暴露（不管有无 offload 内容），组合根 gated except 归到退出码 2——消除「桶名错因是否有 offload
        内容分裂成退出码 2 还是退出码 1」的不一致。探活在 create_run（真写）之前、早于起 worker，不产生引擎费用。
        """
        initial = RunState(
            run_id=self._run_id,
            status=Status.PENDING,
            jobs={
                job.scope_id: JobState(scope_id=job.scope_id, status=Status.PENDING)
                for job in run_meta.jobs
            },
            started_at=started_at,
        )
        with self._lock:
            # 探活先于任何写：三个 store 各探自己的后端（云端探表/桶失败即抛，local no-op）
            self._run_store.preflight()
            self._result_store.preflight()
            if self._report_store is not None:
                self._report_store.preflight()
            self._run_store.create_run(run_meta, initial)

    def on_event(self, event: Event) -> None:
        """事件旁路观察者（注入 schedule 的 on_event，在 sink_lock **之外**调，ADR 0030 决定三）：
        收 SessionOpened（origin 不是 attempted，ADR 0051 决策 4：scope_started 之前的准备期 job 即算 RUNNING）或 ScopeStarted 实时刷该 job 为
        RUNNING，session_id 按代表会话规则（scope_started 的值一经取到锁定；此前取最近一条非 attempted 的 session_opened；
        attempted 不写入），写入永不带 None 覆盖已有值。

        在 worker 线程被调、多 worker 并发——故写 store 经本服务的锁串行（跨线程安全）。
        放在 sink_lock 外，故这次磁盘 RMW 不阻塞别的 worker 的进度显示（与 sink 分离的关键）。
        """
        if isinstance(event, (ScopeStarted, SessionOpened)):
            with self._lock:
                current, locked = self._session.get(event.scope_id, (None, False))
                session_id, locked = representative_session(current, locked, event)
                self._session[event.scope_id] = (session_id, locked)
                if isinstance(event, SessionOpened) and event.origin == "attempted" and session_id is None:
                    return  # 结果未知的尝试不产生带 None 的写入（job 态由后续事件或终态刷落）
                self._run_store.update_job_state(
                    self._run_id,
                    JobState(scope_id=event.scope_id, status=Status.RUNNING, session_id=session_id),
                )

    def on_job_complete(self, jr: JobResult) -> None:
        """每个 job 完成（在主线程等待 job 完成的循环里串行调用）：commit-point 写序——数据面先、控制面 job 态后。

        skipped 的 job 从没 event 流过，但仍经此落库（否则 ResultStore 缺该 scope 文件、CI 读单 scope 落空）。
        """
        with self._lock:
            self._result_store.save_job_result(self._run_id, jr)  # 数据面判定真值【先】
            # 终态写带 session_id：JobResult.session_id 按同一代表会话规则归约而来；它为 None 时退回本服务已记的值，
            # 不用 None 覆盖（ADR 0051 决策 4）
            remembered = self._session.get(jr.scope_id, (None, False))[0]
            self._run_store.update_job_state(                     # 控制面 job 终态【后】
                self._run_id,
                JobState(scope_id=jr.scope_id, status=jr.status, session_id=jr.session_id or remembered),
            )

    def finalize(self, result: RunResult, *, ended_at: str) -> str | None:
        """run 结束（schedule 返回后）：commit point。

        以 `try_finalize` 条件写总 status + ended_at（这次写就是 commit point，它一落 run 即已提交、判定就绪）；
        再归集 ReportStore（派生视图、永远最后、从终值 RunResult 派生）。返回 ReportStore.write 的 ResourceUri。

        **写不成时不覆盖、不写报告**（ADR 0054 决策五）：run 级已是终态，说明本次执行结束之前别处已把它记为已结束；已有的终态
        对所有写入方不可变，报告从本次结果派生、会与记录矛盾，所以都不写，抛 `RunAlreadyEnded`（带读回的运行态）。各 job 的判定
        此前已由 on_job_complete 逐个写入，不受影响。条件写不区分「已是终态」与「运行态不存在」，写不成之后读回一次来分辨：
        运行态不存在抛 FileNotFoundError（begin 之后不该发生）。这次读回本身失败时仍抛 `RunAlreadyEnded`（`recorded` 为 None、
        读回的异常作为它的起因）：收尾没有写成这个结论不靠读回，调用方照同一个出口结束，不因为多出的这次读另有一条失败路径。

        **ReportStore.write 的失败被隔离**（ADR 0030 决定三：报告是派生只读视图、可重建、永不作判定源）——
        它若抛异常（磁盘满/路径不可写等），**不反向击穿已 commit 的 run**：commit point 已落、判定真值在
        ResultStore 安然无恙，故吞掉 write 异常、返回 None（报告可后续从 RunResult 重建），让调用方照常输出汇总/退出码。
        收尾写本身**不**在此 try 内——它是 commit point，失败必须冒泡（控制面没落是真问题）。
        """
        with self._lock:
            if not self._run_store.try_finalize(self._run_id, result.status, ended_at):
                try:
                    recorded = self._run_store.load_run_state(self._run_id)
                except Exception as e:
                    raise RunAlreadyEnded(self._run_id, None) from e
                if recorded is None:
                    raise FileNotFoundError(f"run {self._run_id} 的运行状态不存在，无法记下结果")
                raise RunAlreadyEnded(self._run_id, recorded)
            if self._report_store is None:
                return None
            try:
                return self._report_store.write(self._run_id, result, created_at=ended_at)
            except Exception:
                # 派生视图写失败不击穿已 commit 的 run（判定真值在 ResultStore）；返回 None，报告可从 RunResult 重建。
                # 不留痕：曾存 traceback 到 _report_error 供"可选读取"，但生产端（cli）从不消费——按悬空字段判据删。
                return None
