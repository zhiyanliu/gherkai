"""reconciler（ADR 0034）：无状态批量运行的推进编排——被事件唤醒、幂等、并发安全。

`tick(run_id, meta)` 一步推进：读库中运行态（已收尾即停止推演）→ 读 EventLog 全量 records → project() 推 RunState →
条件写落库 → plan_next() 决定动作 → 对每个 start 动作认领成功即经注入的 Launcher 起 job；全终态则 try_finalize。
结果是 `TickOutcome` 三种之一，宿主据它决定继续推进、生成报告后结束，还是直接结束（ADR 0034 机制三
「run 级状态只进不退」条④）。

**无状态 + 幂等**：所有调度态在 EventLog / RunStore（持久），进程内不留。谁调 tick、何时调、并发调都安全
（CAS + HWM 条件写兜底，机制三/四）——三触发源（cloud Stream / local per-run 进程 / status --wait 接力）
共用这一个 tick。

**守窄腰（[0016]/[0026]）**：本模块不 import subprocess/boto3——「起一个 job」的执行能力经注入的 `Launcher`
（本机后端下起 subprocess worker、旁路落 SQLite 并观察退出；云端后端下调 ECS RunTask）。core 只吐动作、调 Launcher，
副作用在 adapter/组合根。project/plan_next 是纯函数（gherkai_core.project）。
"""
from __future__ import annotations

import enum
import logging
from typing import Protocol

from gherkai_core.model import TERMINAL_STATUSES, Job, RunMeta
from gherkai_core.ports import ResultStore, RunStore
# PLATFORM_FAILED_EXIT：launch 失败补偿的哨兵退出码（机制二推论），定义在 project.py（与 TaskExited 同处、观察者 Lambda 亦 import），此处只引用。
from gherkai_core.project import PLATFORM_FAILED_EXIT, plan_next, project, project_full

logger = logging.getLogger("gherkai_core.reconcile")


class TickOutcome(enum.Enum):
    """一次 `tick` 的结果（ADR 0034 机制三「run 级状态只进不退」条④）。

    后两种都让宿主结束对这个 run 的推进；只有 `FINALIZED` 让宿主生成 RunReport。
    """

    # 继续推进：本轮没有走到收尾分支，宿主照常做超时处置并等下一轮。
    CONTINUE = "continue"
    # 本轮走完收尾分支：判定真值已落、try_finalize 已执行。条件写赢或输都算（输表示并发推进器先提交了终态，
    # 两边都在 baseline 未收尾时进入收尾分支，报告各写一次、幂等覆盖）。
    FINALIZED = "finalized"
    # 读到既有终态：本轮读到的库中运行态已收尾，没有推演、投影、认领，也没有落判定真值。宿主不生成报告：
    # 按此刻的事件重写会覆盖已有报告，而事件过期后重算的结果是错的。
    ALREADY_TERMINAL = "already_terminal"


class EventLog(Protocol):
    """事件日志口（reconciler 读全量 records 重放）。写侧：`tick` 只在 launch 失败补偿时调
    `record_exit`；其余退出记录来自退出观察者（本机 launcher 的 proc.wait、云端 exit-observer Lambda、本机同步 run 的
    `EventRecordingEngine`）与推进器宿主的超时处置（本机接力恢复、云端 tick 对无踪 task 的直写，均带 timed_out；云端 tick
    遇已停止却缺退出记录的 task 时，按 DescribeTasks 结果补写，与观察者同一提取算法）；worker 执行事件由 worker（云端）或
    launcher 旁路（本机）写。"""

    def records(self) -> list: ...  # list[EventRecord]（gherkai_core.project）

    # 单个 scope 有无退出记录（主键点查）——超时处置/接力恢复判「观察链是否已写」用，别为一个 scope 重放整 run。
    def has_exit(self, scope_id: str) -> bool: ...

    # 幂等（独立键空间，机制一）。timed_out：超时处置的 stop 所致退出（ADR 0034「job timeout」节归因链）。
    def record_exit(self, scope_id: str, exit_code: int | None, *, timed_out: bool = False,
                    reason: str | None = None) -> None: ...


class Launcher(Protocol):
    """起一个 job 的执行能力（注入；机制四 CAS 成功后才调）。

    本机后端下起 subprocess worker（事件旁路落 SQLite EventLog + proc.wait 写 task_exited）；
    云端后端下调 ECS RunTask（worker 自 PutItem events + 退出观察者 Lambda 写 task_exited）。
    reconciler 对「怎么起」无知——只在认领成功后调 launch(job, claimed_at=…)。

    claimed_at：本次认领落库的同一个时间戳（`try_claim_job` 写进 `JobState.claimed_at` 的那个值）。job 墙钟预算
    从 claim 起算（ADR 0034「job timeout」节「产品语义」段），到点时刻要按它算的实装（云端的一次性 schedule）据此取
    deadline，不另取 launch 时刻；在本进程内计时的实装可以不用它。
    """

    def launch(self, job: Job, *, claimed_at: str) -> None: ...


def finalize_report(run_id, meta, event_log, report_store, now_iso: str, *, run_duration_ms: float | None = None) -> None:
    """收尾分支走完后写 RunReport（派生视图，**永远最后**；ADR 0030 决定三 / 0034「数据模型三件套」RunReport 行与
    「端到端流程」cloud 第 4 步 ④）。宿主在 tick 返回 `TickOutcome.FINALIZED` 后调；读到既有终态时不调。

    判定真值（ResultStore 各 job）**不在此写**——它在 tick 的 finalize 分支、CAS 之前落（写序见 `tick`）；这里只剩
    派生的报告：从 events 全量重放 project_full → RunResult → report_store.write。幂等（重放 + 覆盖写同 key）——多个
    推进器都走完收尾分支时各写一次无害。写失败隔离：判定真值已随 commit 落定、报告可从 RunResult 重建，不让它击穿
    已提交终态的 run。
    run_duration_ms：run 级墙钟（RunState started_at→ended_at），宿主算好传入（core 不解析时间戳）；缺则报告墙钟显「?」。
    **唯一一份**（cloud Lambda 与 local per-run 两宿主都调用此处，ADR 0034 core 拆分）。纯编排：不 import boto3。
    """
    if report_store is None:
        return
    try:
        report_store.write(run_id, project_full(meta, event_log.records(), run_duration_ms=run_duration_ms),
                           created_at=now_iso)
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
    result_store: ResultStore | None = None,
) -> TickOutcome:
    """推进一步，返回 `TickOutcome`（三种结果的含义见其定义）。

    幂等：可反复调、并发调。步骤（ADR 0034 端到端流程）：
    1. 读库中运行态作 baseline；run 级已是终态即返回 `ALREADY_TERMINAL`，不读事件、不投影、不认领、不落判定真值
       （ADR 0034 机制三「run 级状态只进不退」条④）。
    2. 读 EventLog 全量 records → project() 纯推演完整 RunState（含 HWM）。
    3. project_state() HWM 条件写落 RunState（stale 被挡、无害——下轮重读重推，机制三）。
    4. plan_next() → 动作：
       - start：try_claim_job() 认领（机制四），成功的那个（本实例）才 launcher.launch(job, claimed_at=now_iso) 真起
         （与 claim 落库同一个时间戳，超时到点按它起算）。
       - finalize：先从**同一份** records 快照聚合各 job 判定真值落 result_store（注入时；commit-point 写序，ADR 0030
         决定三 detached 同守），再 try_finalize() 状态机单调条件写（机制三）commit，返回 `FINALIZED`；RunReport 由宿主
         随后写（`finalize_report`）。聚合/落库异常原样抛出：commit 前失败 → 本轮 tick 失败、触发源重试；commit 后无人重试。
    没有走到收尾分支即返回 `CONTINUE`。baseline 读到之后才插入的收尾不在第 1 步的判停之内：本轮的投影写被终态守卫挡下、
    认领被条件挡下，本轮照常返回 `CONTINUE` 或 `FINALIZED`，下一轮读到终态即停。
    """
    # 基线取当前 RunStore 态，先于读事件：已收尾时省掉全量事件读，判停与本轮推演用的是同一份 baseline。
    # 读序不影响正确性：插在两次读之间的认领只让本轮多提议一次被认领条件挡下的 start，插在两次读之间的事件只让
    # 本轮推演比 baseline 更新，按生命周期序合并照常。基线让 project 的 job 态单调不倒退（已认领成 running
    # 但 worker 还没吐 scope_started 的 job，不被降回 pending → 不重复 launch，机制四）。首 tick 时 STATE 已由 create_run 建。
    baseline = run_store.load_run_state(run_id)
    if baseline is not None and baseline.status in TERMINAL_STATUSES:
        return TickOutcome.ALREADY_TERMINAL
    records = event_log.records()
    state = project(meta, records, baseline)
    # HWM 条件写：stale 被挡返回 False——无害，本 tick 只是没推进落库，下轮（或别的实例）会重推。
    run_store.project_state(run_id, state)

    actions = plan_next(state, max_concurrency)
    job_by_scope: dict[str, Job] = {j.scope_id: j for j in meta.jobs}

    for act in actions:
        if act.kind == "start" and act.scope_id is not None:
            # 先确认 job 存在，再认领：防御跳过时不会留下一个已认领成 running 却无人启动的 job。
            job = job_by_scope.get(act.scope_id)
            if job is None:
                continue  # plan_next 从 state.jobs 提议、键集是 meta.jobs 的子集，不该发生；防御跳过
            # 认领：多实例并发提议同一 pending，只有一个成功（机制四严格并发闸）。
            if run_store.try_claim_job(run_id, act.scope_id, claimed_at=now_iso):
                try:
                    launcher.launch(job, claimed_at=now_iso)
                except Exception as e:
                    # launch 失败补偿（ADR 0034 机制二推论）：job 已 CAS 成 RUNNING 却永无 events/
                    # task_exited（进程没起、平台观察者无从观察）——不补偿则永停 RUNNING、整批 wedge、
                    # 三触发源都救不回。tick 在此扮演「起不来」时刻的退出观察者：记非 0 退出，下轮
                    # 重放走「退出码非零 → ERROR」既有谓词收敛。异常不向外抛出（失败隔离：别拖垮同批其余 job）。
                    # 异常文本作 reason 随退出记录进 job message（措辞与同步路径 schedule 的「起 worker 失败：…」一致），
                    # 否则 RunTask 放置失败的归因、引擎未解析的指引都会丢；traceback 另留在日志里供排障。
                    logger.warning("这个 job 没能启动，已按错误处理：run=%s scope=%s", run_id, act.scope_id,
                                   exc_info=True)
                    event_log.record_exit(act.scope_id, PLATFORM_FAILED_EXIT, reason=f"起 worker 失败：{e}")
        elif act.kind == "finalize":
            # 全 job 达终态（plan_next 只在此时给 finalize 动作）→ run 已达终态。
            # ① 判定真值先落（ADR 0030 决定三写序）：用本 tick 已读的 records（与 state 同一快照，不再读一次），
            #    project_full 逐 job 落 ResultStore；它对非终态 job 抛（ADR 0031 不变量守卫）——异常不在本 tick 内捕获、原样抛出，
            #    让触发源重试；绝不先 CAS 再补（CAS 之后无人重试，产物缺失即永久）。多个推进器并发都落、幂等覆盖同 key。
            if result_store is not None:
                for jr in project_full(meta, records).jobs:
                    result_store.save_job_result(run_id, jr)
            # ② try_finalize 状态机单调条件写：True 表示本实例抢到 commit；False 表示别人已 finalize（幂等）。
            #    **两种都返回 FINALIZED**——run 确已达终态，不能因「别人抢先 finalize」就让本推进器
            #    （如 status --wait 接力）返回 CONTINUE 而永远等不到结束（实际运行 status --wait 死循环复现）。
            run_store.try_finalize(run_id, state.status, now_iso)
            return TickOutcome.FINALIZED
    return TickOutcome.CONTINUE
