"""reconciler（ADR 0034）：无状态跑批的推进编排——被事件唤醒、幂等、并发安全。

`tick(run_id, meta)` 一步推进：读 EventLog 全量 records → project() 推 RunState → 条件写落库 →
plan_next() 决定动作 → 对每个 start 动作 CAS 抢占成功即经注入的 Launcher 起 job；全终态则 try_finalize。

**无状态 + 幂等**：所有调度态在 EventLog / RunStore（持久），进程内不留。谁调 tick、何时调、并发调都安全
（CAS + HWM 条件写兜底，机制三/四）——三触发源（cloud Stream / local per-run 进程 / status --wait 接力）
共用这一个 tick。

**守窄腰（[0016]/[0026]）**：本模块不 import subprocess/boto3——「起一个 job」的执行能力经注入的 `Launcher`
（local=起 subprocess worker 旁路落 SQLite + 观察退出；cloud=ECS RunTask）。core 只吐动作、调 Launcher，
副作用在 adapter/组合根。project/plan_next 是纯函数（gherkai_core.project）。
"""
from __future__ import annotations

from typing import Protocol

from gherkai_core.model import Job, RunMeta
from gherkai_core.ports import RunStore
from gherkai_core.project import plan_next, project


class EventLog(Protocol):
    """事件日志口（reconciler 读全量 records 重放；写侧仅 launch 失败补偿的 record_exit——正常路径的
    events 由 worker/观察者写，reconciler 不写）。"""

    def records(self) -> list: ...  # list[EventRecord]（gherkai_core.project）

    # 幂等（独立键空间，机制一）。timed_out：超时处置的 stop 所致退出（ADR 0034「job timeout」节归因链）。
    def record_exit(self, scope_id: str, exit_code: int | None, *, timed_out: bool = False,
                    reason: str | None = None) -> None: ...


# launch 失败补偿的哨兵退出码（机制二推论）：定义在 project.py（与 TaskExited 同处、观察者 Lambda 亦 import），此处只引用。
from gherkai_core.project import PLATFORM_FAILED_EXIT  # noqa: E402


class Launcher(Protocol):
    """起一个 job 的执行能力（注入；机制四 CAS 成功后才调）。

    local = 起 subprocess worker（事件旁路落 SQLite EventLog + proc.wait 写 task_exited）；
    cloud = ECS RunTask（worker 自 PutItem events + 退出观察者 Lambda 写 task_exited）。
    reconciler 对「怎么起」无知——只在 CAS 抢占成功后调 launch(job)。
    """

    def launch(self, job: Job) -> None: ...


def finalize_artifacts(run_id, meta, event_log, result_store, report_store, now_iso: str) -> None:
    """done 后聚合判定真值 + RunReport（幂等；ADR 0034 收尾，对齐同步 run 路径产物）。

    tick 的 try_finalize 只写 RunStore 总 status；判定明细（ResultStore）与 RunReport（ReportStore）在此补：
    从 events 全量重放 project_full → RunResult，逐 job save_job_result + report_store.write。幂等（重放 +
    覆盖写同 key）——多个推进者都 done 都聚合无害。store 注入 None（测试）则跳过对应半边；ReportStore 写失败
    隔离（判定真值已在 ResultStore、report 可从 RunResult 重建，ADR 0030 决定三）。
    **唯一一份**（cloud Lambda / local per-run 两宿主同调此处）——曾双写于 detached.py 与 deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py，
    按「不复制归约/收尾逻辑」合并（ADR 0034 core 拆分）。纯编排：只调 project_full 与注入的 store，不 import boto3。
    """
    if result_store is None and report_store is None:
        return
    from gherkai_core.project import project_full

    result = project_full(meta, event_log.records())
    if result_store is not None:
        for jr in result.jobs:
            result_store.save_job_result(run_id, jr)
    if report_store is not None:
        try:
            report_store.write(run_id, result, created_at=now_iso)
        except Exception:
            pass  # 派生视图写失败不击穿判定真值（ADR 0030 决定三）


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
            if run_store.try_claim_job(run_id, act.scope_id, claimed_at=now_iso):
                job = job_by_scope.get(act.scope_id)
                if job is None:
                    continue  # plan_next 从 state.jobs 提议、键集 ⊆ meta.jobs，不该发生；防御跳过
                try:
                    launcher.launch(job)
                except Exception:
                    # launch 失败补偿（ADR 0034 机制二推论）：job 已 CAS 成 RUNNING 却永无 events/
                    # task_exited（进程没起、平台观察者无从观察）——不补偿则永停 RUNNING、整批 wedge、
                    # 三触发源都救不回。tick 在此扮演「起不来」时刻的退出观察者：记非 0 退出，下轮
                    # 重放走「exit≠0 → ERROR」既有谓词收敛。异常不裸穿（失败隔离：别拖垮同批其余 job）。
                    event_log.record_exit(act.scope_id, PLATFORM_FAILED_EXIT)
        elif act.kind == "finalize":
            # 全 job 达终态（plan_next 只在此时给 finalize 动作）→ run 已 done。
            # try_finalize 状态机单调条件写：True=本实例抢到 commit（负责 report 聚合）；False=别人已 finalize
            # （幂等）。**两种都返回 done=True**——run 确已达终态，不能因「别人抢先 finalize」就让本推进者
            # （如 status --wait 接力）返回 False 而永远等不到 done（真跑 status --wait 死循环复现）。
            run_store.try_finalize(run_id, state.status, now_iso)
            return True
    return False
