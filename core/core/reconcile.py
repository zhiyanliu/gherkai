"""reconciler（ADR 0034）：无状态跑批的推进编排——被事件唤醒、幂等、并发安全。

`tick(run_id, meta)` 一步推进：读 EventLog 全量 records → project() 推 RunState → 条件写落库 →
plan_next() 决定动作 → 对每个 start 动作 CAS 抢占成功即经注入的 Launcher 起 job；全终态则 try_finalize。

**无状态 + 幂等**：所有调度态在 EventLog / RunStore（持久），进程内不留。谁调 tick、何时调、并发调都安全
（CAS + HWM 条件写兜底，机制三/四）——三触发源（cloud Stream / local per-run 进程 / status --wait 接力）
共用这一个 tick。

**守窄腰（[0016]/[0026]）**：本模块不 import subprocess/boto3——「起一个 job」的执行能力经注入的 `Launcher`
（local=起 subprocess worker 旁路落 SQLite + 观察退出；cloud=ECS RunTask）。core 只吐动作、调 Launcher，
副作用在 adapter/组合根。project/plan_next 是纯函数（core.project）。
"""
from __future__ import annotations

from typing import Protocol

from core.model import Job, RunMeta
from core.ports import RunStore
from core.project import plan_next, project


class EventLog(Protocol):
    """事件日志读口（reconciler 只读全量 records 重放；写由 Launcher 侧/worker 做）。"""

    def records(self) -> list: ...  # list[EventRecord]（core.project）


class Launcher(Protocol):
    """起一个 job 的执行能力（注入；机制四 CAS 成功后才调）。

    local = 起 subprocess worker（事件旁路落 SQLite EventLog + proc.wait 写 task_exited）；
    cloud = ECS RunTask（worker 自 PutItem events + 退出观察者 Lambda 写 task_exited）。
    reconciler 对「怎么起」无知——只在 CAS 抢占成功后调 launch(job)。
    """

    def launch(self, job: Job) -> None: ...


def tick(
    run_id: str,
    meta: RunMeta,
    event_log: EventLog,
    run_store: RunStore,
    launcher: Launcher,
    max_concurrency: int,
    *,
    now_iso: str,
) -> bool:
    """推进一步。返回 run 是否已达终态（全 done 且 finalize 成功/已被别人 finalize）。

    幂等：可反复调、并发调。步骤（ADR 0034 端到端流程）：
    1. 读 EventLog 全量 records → project() 纯推演完整 RunState（含 HWM）。
    2. project_state() HWM 条件写落 RunState（stale 被挡、无害——下轮重读重推，机制三）。
    3. plan_next() → 动作：
       - start：try_claim_job() CAS 抢占（机制四），成功的那个（本实例）才 launcher.launch(job) 真起。
       - finalize：try_finalize() 状态机单调条件写（机制三），成功=本实例 commit（触发 report 由组合根收尾）。
    """
    records = event_log.records()
    # 基线 = 当前 RunStore 态：让 project 的 job 态单调不倒退（已 CAS claim 成 running 但 worker 还没吐
    # scope_started 的 job，不被降回 pending → 不重复 launch，机制四）。首 tick 时 STATE 已由 create_run 建。
    baseline = run_store.load_run_state(run_id)
    state = project(meta, records, baseline)
    # HWM 条件写：stale 被挡返回 False——无害，本 tick 只是没推进落库，下轮（或别的实例）会重推。
    run_store.project_state(run_id, state)

    actions = plan_next(state, max_concurrency)
    job_by_scope: dict[str, Job] = {j.scope_id: j for j in meta.jobs}

    for act in actions:
        if act.kind == "start" and act.scope_id is not None:
            # CAS 抢占：多实例并发提议同一 pending，只有一个成功（机制四严格并发闸）。
            if run_store.try_claim_job(run_id, act.scope_id):
                job = job_by_scope.get(act.scope_id)
                if job is not None:
                    launcher.launch(job)
        elif act.kind == "finalize":
            # 状态机单调条件写：commit 恰一次（机制三）。成功=本实例负责收尾（report 聚合在组合根）。
            return run_store.try_finalize(run_id, state.status, now_iso)
    return False
