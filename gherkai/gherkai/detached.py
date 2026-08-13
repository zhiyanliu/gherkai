"""无状态跑批的 cli 侧接线（ADR 0034，local 档）：SubprocessLauncher + per-run reconciler 进程。

组合根职责（local 执行环境特有）：把 core 的 reconciler（纯编排）接到真 subprocess 世界——
- **SubprocessLauncher**：机制四 CAS 抢占成功后被 reconciler 调，起一个 worker（复用 SubprocessEngine）、
  在独立线程里读它的 fd3 事件流旁路落 SqliteEventLog（赋 worker 段单调 seq）、worker 退出后 `handle.wait()`
  拿 exitcode 写 task_exited（扮演平台侧退出观察者，机制二 local 对位）。worker 不改、对 SQLite 无知（0034）。
- **per-run reconciler 进程**：`submit` 时 setsid fork 出来的轻进程，循环 tick 直到全 done 自退。

守窄腰：core.reconcile 对「怎么起 worker」无知（经 Launcher 注入）；本模块是 cli（组合根）、可 import
SubprocessEngine/SqliteEventLog。cloud 档的 Launcher（ECS RunTask）是 P4 的另一实现，同一 reconcile.tick。
"""
from __future__ import annotations

import threading
import time
from pathlib import Path

from core.adapters.event_log import SqliteEventLog
from core.adapters.run_store.local import LocalRunStore
from core.model import Job, RunMeta, Status
from core.reconcile import finalize_artifacts, tick
from core.ports import Engine, EngineResolver

# 接力恢复的判定余量秒（ADR 0034「job timeout」节 claimed_at ①）：超预算这么久才认定 owner 已死。
# 非正确性参数（误判也收敛正确——owner 尚活时其 timer 同 deadline 早已触发、真退出记录同带 timed_out，
# 覆盖无害），只为让活 owner 的 stop→grace→真退出路径通常先落、少churn。
_RECOVERY_MARGIN_S = 10.0


class SubprocessLauncher:
    """local Launcher（ADR 0034 机制四回调 + 机制二退出观察者）。

    launch(job)：起 worker（resolver 按 engine 选 SubprocessEngine）→ 后台线程消费 fd3 事件流落 SQLite +
    退出后写 task_exited。非阻塞返回（reconciler 继续 tick，不等 worker 跑完——那是 fire-and-forget，事件
    异步落 SQLite、下轮 tick 从 SQLite 重放看到进展）。

    同时 enforce job timeout（ADR 0034「job timeout」节 local 档）：job.timeout_s 非 None 时起 deadline
    timer——到点先置 timed_out 标志再 handle.stop(engine grace)（协作停，保会话清理不烧钱），worker 退出后
    _pump 的 record_exit 带上标志，project 按归因链收敛 ERROR+timeout。
    """

    def __init__(self, resolver: EngineResolver, event_log: SqliteEventLog, *,
                 min_grace_fn=None) -> None:
        self._resolver = resolver
        self._event_log = event_log
        self._threads: list[threading.Thread] = []
        # engine→grace 下限（组合根注入 compose.engine_min_grace；None → 缺省 5s）：timeout stop 用它当
        # 协作停宽限（grace < 单 act 时长会致会话泄漏，ADR 0024 grace 硬约束——超时杀也不豁免）。
        self._min_grace_fn = min_grace_fn
        # 本 launcher 起过的 scope（run_reconcile_loop 的接力恢复扫豁免它们——自家 job 的 deadline 有 timer 在管）
        self.owned_scopes: set[str] = set()

    def launch(self, job: Job) -> None:
        scope_id = job.scope_id
        self.owned_scopes.add(scope_id)
        engine: Engine = self._resolver(job.engine)
        # raw_sink：SubprocessEngine 读 fd3 每行原始 JSON（解析前）旁路调它——落 SQLite 存原样（存原始行、
        # 读回复用 wire.event_from_line，零新序列化）。seq 按到达序单调递增（worker 一个 scope 串行 emit）。
        # 续号：从 SQLite 已有 max_seq 起（重试/续跑幂等）。闭包持 seq，_pump 的线程内单线程递增、无竞态。
        seq_box = [self._event_log.max_seq(scope_id)]

        def raw_sink(line: str) -> None:
            seq_box[0] += 1
            self._event_log.append_event(scope_id, seq_box[0], line, time.time())

        handle, events = engine.run_scope(job, raw_sink=raw_sink)
        timer: threading.Timer | None = None
        timed_out = threading.Event()
        if job.timeout_s:
            grace = self._min_grace_fn(job.engine) if self._min_grace_fn else 5.0

            def _on_deadline() -> None:
                timed_out.set()  # 先置标志再 stop：_pump 的 record_exit 必见（归因链时序）
                try:
                    handle.stop(grace)  # 协作停（SIGTERM→grace→SIGKILL 兜底，adapter 既有语义）
                except Exception:
                    pass  # stop 失败（如进程恰已退）→ 交给 _pump 的 wait 收敛

            timer = threading.Timer(job.timeout_s, _on_deadline)
            timer.daemon = True
            timer.start()
        t = threading.Thread(
            target=self._pump, args=(scope_id, handle, events, timer, timed_out), daemon=True,
            name=f"launcher-{scope_id}",
        )
        t.start()
        self._threads.append(t)

    def _pump(self, scope_id: str, handle, events, timer=None, timed_out=None) -> None:
        """驱动一个 worker 的 fd3 事件流跑完（落库在 raw_sink 里做）；结束后 handle.wait() 拿 exitcode 写 task_exited。

        迭代 events 只为驱动 fd3 读（每行触发 raw_sink 落库）——迭代产出的 Event 本身丢弃（我们要的是原始行、
        已落库）。异常（含 _read_events 对 rc>0 抛的 RuntimeError/WorkerNetworkError）吞掉：下面 handle.wait()
        拿真实 exitcode 写 task_exited，让 project 据「两件都要」判终态（机制二）。无论如何都写退出记录——
        否则该 job 永远 RUNNING、reconciler 卡住不收尾。
        """
        try:
            for _event in events:
                pass  # 落库已在 raw_sink 完成；此处只驱动 fd3 读到 EOF
        except Exception:
            pass  # worker 异常退出——exitcode 由下面 wait() 拿，经 task_exited 让 project 判 error
        finally:
            if timer is not None:
                timer.cancel()  # 正常退出取消 deadline（已触发的 cancel 无害）
            try:
                exit_code = handle.wait()
            except Exception:
                exit_code = None  # 拿不到退出码 → None（宽限态，机制二保守判 running，人可 status 查）
            self._event_log.record_exit(scope_id, exit_code,
                                        timed_out=bool(timed_out is not None and timed_out.is_set()))


def run_reconcile_loop(
    run_id: str,
    meta: RunMeta,
    event_log: SqliteEventLog,
    run_store: LocalRunStore,
    launcher: SubprocessLauncher,
    max_concurrency: int,
    *,
    poll_interval_s: float = 0.5,
    now_iso_fn=None,
    result_store=None,
    report_store=None,
) -> None:
    """per-run 进程的推进循环：反复 tick 直到全 done（ADR 0034 local 主力触发源）。

    now_iso_fn：注入时间源（组合根传 compose.now_iso；测试传 fake 保确定性）。tick 幂等——崩了 status --wait
    可接力（状态全持久）。全 done（tick 返回 True）即退出（batch shape：跑完即停、不常驻）。

    result_store/report_store（可选）：done 后聚合收尾——从 events 全量重放 project_full 构造完整 RunResult，
    落 ResultStore（判定真值 jobs/*.json）+ ReportStore（RunReport index/manifest），与同步 run 路径产物对齐。
    幂等（从 events 重放、覆盖写同 key）——多个推进者都 done 都聚合无害。注入 None（测试）则跳过收尾。
    """
    import datetime as _dt

    def _now() -> str:
        if now_iso_fn is not None:
            return now_iso_fn()
        return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    while True:
        done = tick(run_id, meta, event_log, run_store, launcher, max_concurrency, now_iso=_now())
        if done:
            # 收尾聚合走 core 唯一一份（曾在此双写一份、与 lambdas/reconciler.py 漂移风险，已合并）
            finalize_artifacts(run_id, meta, event_log, result_store, report_store, _now())
            return
        _recover_timed_out_claims(run_id, meta, event_log, run_store, launcher, _now())
        time.sleep(poll_interval_s)


def _parse_iso(s: str):
    import datetime as _dt

    return _dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def _recover_timed_out_claims(run_id, meta, event_log, run_store, launcher, now_iso: str) -> None:
    """接力恢复 deadline（ADR 0034「job timeout」节 claimed_at ①）：**他人 claim、本进程无 handle** 的
    RUNNING job 超预算（claimed_at 起算）且无退出记录 → 观察链已死（deadline timer 随 owner 进程丢、
    worker 因 fd3 断管随之早亡）→ 直接 record_exit(timed_out=True) 收敛，防 run 永久 wedge。

    自家 job（launcher.owned_scopes）不扫——launch 时的 timer 在管、且要给足协作停 grace。
    与被拒方案「超时时由处置者直接写 task_exited」不冲突：那条拒的是**有活观察链时**绕过它；此处观察链
    已死、直接写是唯一收敛路径。若 owner 其实尚活（余量误判）：其 timer 同一 deadline 早已触发、真退出
    记录同带 timed_out=True，后到覆盖本记录归因不变（INSERT OR REPLACE 同 key）。
    """
    state = run_store.load_run_state(run_id)
    if state is None:
        return
    job_by_scope = {j.scope_id: j for j in meta.jobs}
    exited_scopes = {r.scope_id for r in event_log.records() if r.kind == "exit"}
    now = _parse_iso(now_iso)
    for sid, js in state.jobs.items():
        if js.status != Status.RUNNING or sid in launcher.owned_scopes or sid in exited_scopes:
            continue
        job = job_by_scope.get(sid)
        if job is None or not job.timeout_s or not js.claimed_at:
            continue  # 无预算/无起算点（旧数据）→ 不处置（除超时外无权臆断他人 claim 的死活）
        elapsed = (now - _parse_iso(js.claimed_at)).total_seconds()
        if elapsed > job.timeout_s + _RECOVERY_MARGIN_S:
            event_log.record_exit(sid, None, timed_out=True)  # exit_code=None：无观察到的退出码，诚实留空


# ============================================================================
# per-run 进程：从 run_id + 本地落点重建装配、跑 reconcile loop（submit setsid fork 它）
# ============================================================================


def _paths(report_dir: str, run_id: str):
    """local 无状态跑批的落点：events SQLite 与 RunStore/ResultStore 同在 <report_dir>/<run_id>/。"""
    root = Path(report_dir)
    return root, root / run_id / "events.db"


def build_local_reconcile(repo, report_dir: str, run_id: str, max_concurrency: int,
                          region: str | None = None, profile: str | None = None):
    """从本地落点重建 per-run reconcile 所需的全部（meta 从 RunStore 读回、log/store/launcher 重建）。

    per-run 进程自包含、不依赖父进程内存（fork 后父可退）：definition 已由 submit 的 create_run 落 RunStore，
    这里 load_run_meta 读回；SqliteEventLog/LocalRunStore 都是文件路径，从 report_dir+run_id 重建即同一份。
    返回 (meta, log, store, launcher, max_concurrency, result_store, report_store) 供 run_reconcile_loop
    （后两个是收尾聚合用的落点，与 RunStore 同 <report_dir>/<run_id>/）。
    """
    from gherkai import compose

    root, db_path = _paths(report_dir, run_id)
    store = LocalRunStore(root)
    meta = store.load_run_meta(run_id)
    if meta is None:
        raise FileNotFoundError(f"per-run reconcile：run_meta 不存在（submit 未落库？）：{run_id}")
    log = SqliteEventLog(db_path)
    # 产物落点 env 注入（同步 run 路径的 build_engines 一致）：nova/midscene 产物落 <report_dir>/<run_id>/ 下。
    nova_logs_dir = root / run_id / "nova-trajectories"
    midscene_run_dir = root / run_id / "midscene-run"
    engines = compose.build_engines(
        repo, nova_logs_dir=nova_logs_dir, midscene_run_dir=midscene_run_dir,
        region=region, profile=profile,
    )
    resolver = compose.make_resolver(engines)
    launcher = SubprocessLauncher(resolver, log, min_grace_fn=compose.engine_min_grace)
    # ResultStore + ReportStore（收尾聚合用，落点与 RunStore 同 <report_dir>/<run_id>/，对齐同步 run 路径）
    from core.adapters.result_store.local import LocalResultStore
    from core.adapters.report_store.local import LocalReportStore
    result_store = LocalResultStore(root)
    report_store = LocalReportStore(root)
    return meta, log, store, launcher, max_concurrency, result_store, report_store


def render_run_state(state) -> str:
    """status 命令的 RunState 人读渲染（轻量；权威判定明细读 jobs/*.json / --json）。"""
    lines = [f"run {state.run_id}: {state.status.value}"]
    for sid, js in state.jobs.items():
        sess = f"  session={js.session_id}" if js.session_id else ""
        lines.append(f"  - {sid}: {js.status.value}{sess}")
    if state.ended_at:
        lines.append(f"ended_at={state.ended_at}")
    return "\n".join(lines)
