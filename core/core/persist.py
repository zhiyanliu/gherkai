"""RunPersistence（ADR 0030 决定二）：把「一次 run 如何随进度实时落库」收成一处应用服务。

为什么是 core 应用服务、不是每个组合根各写一遍：实时写的编排（commit-point 写序 / RUNNING 中间态 /
按 scope_id 增量刷）对 cli / WebUI / 未来 cron **完全一致，只有注入的 store adapter 不同**。让每个皮各写
一遍必漂移。故收成依赖 Store **ports**（不含具体 adapter、不含执行 reducer）的服务，组合根只注入 adapter。

架构对位：schedule 编排**执行**（Engine port），RunPersistence 编排**存储**（Store ports），两者平级、
都在 core、由组合根组合。schedule 一行不碰 store——它经 sink / on_job_complete 两个回调把事件/JobResult
喂给本服务（ADR 0026/0030）。

commit-point 写序（ADR 0030 决定三）：数据面 ResultStore 先逐 job 落 → 控制面 RunStore.finalize 最后写。
「finalize 一落 = run 已提交、判定就绪」。

并发不变量（ADR 0030 决定三）：两条写 RunStore 的路径——RUNNING 中间态刷在 **worker 线程**（经 sink，
schedule 的 sink_lock 串行）、job 终态刷在 **主线程**（经 on_job_complete，as_completed 串行）——是两个
不同线程经两套不同串行机制。local adapter 的 update_job_state 是整文件 read-modify-write、非自身线程安全。
故本服务**自持一把锁**，所有写 store 的入口都走它，不依赖「sink_lock 与主线程碰巧不撞」。
"""
from __future__ import annotations

import threading

from core.model import (
    Event,
    JobResult,
    JobState,
    RunMeta,
    RunResult,
    RunState,
    ScopeStarted,
    Status,
)
from core.ports import ReportStore, ResultStore, RunStore


class RunPersistence:
    """编排 RunStore + ResultStore（+ 可选 ReportStore）随进度实时落库（ADR 0030）。

    生命周期：begin（run 开始）→ on_event（运行中刷 RUNNING）+ on_job_complete（job 完成落终态）→ finalize（commit point）。
    注入点：on_event → schedule 的 on_event（sink_lock 外）；on_job_complete → schedule 的 on_job_complete（主线程）。
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

    def begin(self, run_meta: RunMeta, *, started_at: str) -> None:
        """run 开始（schedule 之前）：先探活三个 store，再写 definition + 初始全 pending 运行态。

        满足 ADR 0027「提交即返回 runId」——definition 必先于跑批存在。各 job 摆 PENDING、总 PENDING、
        started_at 填、ended_at 缺席（finalize 时填）。

        **create_run 前先 preflight（ADR 0030 决定七）**：探底层可达（云端探表/桶，local no-op）。桶/表名错
        一律在此暴露（不管有无 offload 内容），组合根 gated except 归到退 2——消除「桶名错因是否有 offload
        内容分裂成退 2/退 1」的不一致。探活在 create_run（真写）之前、早于起 worker，不烧引擎钱。
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
        收 ScopeStarted 实时刷该 job 为 RUNNING（带 session_id 血缘）。

        在 worker 线程被调、多 worker 并发——故写 store 经本服务的锁串行（跨线程安全）。
        放在 sink_lock 外，故这次磁盘 RMW 不阻塞别的 worker 的进度显示（与 sink 分离的关键）。
        """
        if isinstance(event, ScopeStarted):
            with self._lock:
                self._run_store.update_job_state(
                    self._run_id,
                    JobState(scope_id=event.scope_id, status=Status.RUNNING, session_id=event.session_id),
                )

    def on_job_complete(self, jr: JobResult) -> None:
        """每个 job 完成（主线程 as_completed 串行 fire）：commit-point 写序——数据面先、控制面 job 态后。

        skipped 的 job 从没 event 流过，但仍经此落库（否则 ResultStore 缺该 scope 文件、CI 读单 scope 落空）。
        """
        with self._lock:
            self._result_store.save_job_result(self._run_id, jr)  # 数据面判定真值【先】
            self._run_store.update_job_state(                     # 控制面 job 终态【后】
                self._run_id,
                JobState(scope_id=jr.scope_id, status=jr.status, session_id=jr.session_id),
            )

    def finalize(self, result: RunResult, *, ended_at: str, materialize: bool = False) -> str | None:
        """run 结束（schedule 返回后）：commit point。

        写总 status + ended_at（finalize_run = commit point，它一落 run 即已提交、判定就绪）；
        再归集 ReportStore（派生视图、永远最后、从终值 RunResult 派生）。返回 ReportStore.write 的 ResourceUri。

        **ReportStore.write 的失败被隔离**（ADR 0030 决定三：报告是派生只读视图、可重建、永不作判定源）——
        它若抛异常（磁盘满/路径不可写等），**不反向击穿已 commit 的 run**：commit point 已落、判定真值在
        ResultStore 安然无恙，故吞掉 write 异常、返回 None（报告可后续从 RunResult 重建），让调用方照常输出汇总/退出码。
        finalize_run 本身**不**在此 try 内——它是 commit point，失败必须冒泡（控制面没落=真问题）。
        """
        with self._lock:
            self._run_store.finalize_run(self._run_id, result.status, ended_at)
            if self._report_store is None:
                return None
            try:
                return self._report_store.write(
                    self._run_id, result, created_at=ended_at, materialize=materialize
                )
            except Exception:
                # 派生视图写失败不击穿已 commit 的 run（判定真值在 ResultStore）；返回 None，报告可从 RunResult 重建。
                # 不留痕：曾存 traceback 到 _report_error 供"可选读取"，但生产端（cli）从不消费——删悬空字段（代码 review）。
                return None
