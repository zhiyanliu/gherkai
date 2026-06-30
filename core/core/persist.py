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
from core.ports import ReportStore, ResultStore, RunStore, Sink


class RunPersistence:
    """编排 RunStore + ResultStore（+ 可选 ReportStore）随进度实时落库（ADR 0030）。

    生命周期：begin（run 开始）→ sink 装饰 + on_job_complete（运行中实时）→ finalize（commit point）。
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
        """run 开始（schedule 之前）：写 definition + 初始全 pending 运行态。

        满足 ADR 0027「提交即返回 runId」——definition 必先于跑批存在。各 job 摆 PENDING、总 PENDING、
        started_at 填、ended_at 缺席（finalize 时填）。
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
            self._run_store.create_run(run_meta, initial)

    def sink(self, inner: Sink) -> Sink:
        """装饰内层 sink：转发原有进度回调 + 收 ScopeStarted 实时刷该 job 为 RUNNING（带 session_id 血缘）。

        在 worker 线程被调（schedule 的 sink_lock 串行）；写 store 仍经本服务的锁（跨线程安全）。
        """
        def wrapped(event: Event) -> None:
            inner(event)  # 先转发进度（不被落库异常吞掉显示）
            if isinstance(event, ScopeStarted):
                with self._lock:
                    self._run_store.update_job_state(
                        self._run_id,
                        JobState(scope_id=event.scope_id, status=Status.RUNNING, session_id=event.session_id),
                    )
        return wrapped

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

        写总 status + ended_at（finalize_run）；再归集 ReportStore（派生视图、永远最后、从终值 RunResult 派生）。
        返回 ReportStore.write 的 ResourceUri（无 report_store 则 None）。各 job 判定真值此前已逐个流式落。
        """
        with self._lock:
            self._run_store.finalize_run(self._run_id, result.status, ended_at)
            if self._report_store is not None:
                return self._report_store.write(
                    self._run_id, result, created_at=ended_at, materialize=materialize
                )
        return None
