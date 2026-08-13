"""SubprocessLauncher + reconcile loop 真跑集成测试（ADR 0034 P3b）。

**真 spawn echo_worker 子进程**（不烧 AWS，但真 fd3/真退出码/真 SQLite）——这是「绿≠对」里该真跑的：
launcher 读真 fd3 落 SQLite、真 handle.wait() 拿退出码写 task_exited、reconcile loop 真推进到终态。
纯逻辑部分（project/plan_next/条件写）已在 core 单测覆盖；此处补 launcher 接线的真进程边界。

复用 core/tests/fixtures/echo_worker.py（WORKER_MODE=pass/crash 控制行为）。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from core.adapters.event_log import SqliteEventLog
from core.adapters.run_store.local import LocalRunStore
from core.adapters.subprocess_engine import SubprocessEngine
from core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step

from gherkai.detached import SubprocessLauncher, run_reconcile_loop

# echo_worker：core 的测试 fixture（真 worker 的假替身，吐 ADR 0024 事件到 fd3）
_ECHO = str(Path(__file__).resolve().parents[2] / "core" / "tests" / "fixtures" / "echo_worker.py")


def _echo_resolver(mode: str):
    """按 WORKER_MODE 起 echo_worker 的 SubprocessEngine，包成 resolver（所有 engine 名都映射到它）。"""
    env = {**os.environ, "WORKER_MODE": mode}
    engine = SubprocessEngine(cmd=[sys.executable, _ECHO], env=env)
    return lambda _name: engine


def _job(sid: str, timeout_s: float | None = None) -> Job:
    return Job(scope_id=sid, scope_name=sid, engine="novaact", timeout_s=timeout_s,
               scenarios=(Scenario(id=f"{sid}:0", name="sc", steps=(
                   Step(0, "Given", '打开 "https://x"'), Step(1, "When", "搜索"), Step(2, "Then", "进入"),
               )),))


def _setup(tmp_path, mode, *sids, timeout_s: float | None = None):
    meta = RunMeta(run_id="run-1", created_at="t0",
                   jobs=tuple(_job(s, timeout_s=timeout_s) for s in sids))
    log = SqliteEventLog(tmp_path / "events.db")
    store = LocalRunStore(tmp_path)
    store.create_run(meta, RunState(run_id="run-1", status=Status.PENDING,
                                    jobs={s: JobState(s, Status.PENDING) for s in sids},
                                    started_at="t0", high_water_mark=0))
    launcher = SubprocessLauncher(_echo_resolver(mode), log)
    return meta, log, store, launcher


# 注入确定性 now（避免真时钟；loop 只需单调即可，这里固定即可，tick 不依赖时间差）
def _now():
    return "2026-07-19T00:00:00Z"


def test_single_job_passes_end_to_end(tmp_path):
    """真 spawn echo_worker(pass) → 事件落 SQLite → reconcile loop 推进到 passed 终态。"""
    meta, log, store, launcher = _setup(tmp_path, "pass", "a")
    run_reconcile_loop("run-1", meta, log, store, launcher, max_concurrency=1,
                       poll_interval_s=0.05, now_iso_fn=_now)
    state = store.load_run_state("run-1")
    assert state.status == Status.PASSED
    assert state.jobs["a"].status == Status.PASSED
    assert state.ended_at == "2026-07-19T00:00:00Z"
    # 事件真落了 SQLite（scope_started + 各 step_done + scope_done）
    recs = log.records()
    assert any(r.kind == "event" for r in recs)
    assert any(r.kind == "exit" and r.exited.exit_code == 0 for r in recs)


def test_two_jobs_concurrency_one(tmp_path):
    """max_concurrency=1：两 job 串行推进、都 passed。验 loop 起完一个再起下一个。"""
    meta, log, store, launcher = _setup(tmp_path, "pass", "a", "b")
    run_reconcile_loop("run-1", meta, log, store, launcher, max_concurrency=1,
                       poll_interval_s=0.05, now_iso_fn=_now)
    state = store.load_run_state("run-1")
    assert state.status == Status.PASSED
    assert state.jobs["a"].status == Status.PASSED
    assert state.jobs["b"].status == Status.PASSED


def test_job_timeout_stops_worker_and_attributes_timeout(tmp_path):
    """job timeout local enforce 真跑（ADR 0034「job timeout」节）：silent worker 卡死不吐新事件、不自退——
    launcher 的 deadline timer 到点协作停（SIGTERM→echo 干净退 0）→ task_exited(timed_out=True)
    → project 判 ERROR + error_type=timeout。**协作退 0 也不误判 passed**（timed_out 短路内容判定）。"""
    from core.project import project_full

    meta, log, store, launcher = _setup(tmp_path, "silent", "a", timeout_s=0.5)
    run_reconcile_loop("run-1", meta, log, store, launcher, max_concurrency=1,
                       poll_interval_s=0.05, now_iso_fn=_now)
    state = store.load_run_state("run-1")
    assert state.status == Status.ERROR
    assert state.jobs["a"].status == Status.ERROR
    exits = [r for r in log.records() if r.kind == "exit"]
    assert len(exits) == 1 and exits[0].exited.timed_out is True
    jr = project_full(meta, log.records()).jobs[0]
    assert jr.error_type == "timeout"  # 归因链端到端（真进程边界）
    assert jr.session_id == "echo-sess"  # 血缘仍从 scope_started 捕获（超时不丢会话线索）


def test_relay_recovers_foreign_timed_out_claim(tmp_path):
    """接力恢复（ADR 0034「job timeout」节 claimed_at ①）：他人 claim 的 RUNNING job（owner 进程已死、
    无 handle 无观察链）超预算 → loop 防御扫直接 record_exit(timed_out=True) 收敛 ERROR，run 不永久 wedge。"""
    meta, log, store, launcher = _setup(tmp_path, "pass", "a", timeout_s=60.0)
    # 模拟死 owner 遗留态：a 已被 claim（claimed_at 一小时前）、无退出记录、本 launcher 没起过它
    assert store.try_claim_job("run-1", "a", claimed_at="2026-07-19T00:00:00Z") is True
    run_reconcile_loop("run-1", meta, log, store, launcher, max_concurrency=1,
                       poll_interval_s=0.05, now_iso_fn=lambda: "2026-07-19T01:00:00Z")
    state = store.load_run_state("run-1")
    assert state.status == Status.ERROR
    exits = [r for r in log.records() if r.kind == "exit"]
    assert len(exits) == 1 and exits[0].exited.timed_out is True
    assert exits[0].exited.exit_code is None  # 无观察到的退出码——诚实留空（宽限态被 timed_out 短路）


def test_crash_worker_finalizes_error(tmp_path):
    """echo_worker(crash) 非 0 退出 → task_exited 带非0 → project 判 error → run finalize error（机制二真跑）。"""
    meta, log, store, launcher = _setup(tmp_path, "crash", "a")
    run_reconcile_loop("run-1", meta, log, store, launcher, max_concurrency=1,
                       poll_interval_s=0.05, now_iso_fn=_now)
    state = store.load_run_state("run-1")
    assert state.status == Status.ERROR
    # task_exited 记了真实非 0 退出码
    exits = [r for r in log.records() if r.kind == "exit"]
    assert len(exits) == 1 and exits[0].exited.exit_code != 0


def test_build_local_reconcile_resolves_region_like_foreground(tmp_path, monkeypatch):
    """region 走与前台 run 相同的解析链（ADR 0016 决策 C）：不显式给 --region 时 env/profile config 兜底、
    落实成字符串注入 worker env——曾原样透传 None：worker 里 AgentCore validate_region 见 None 即崩
    （exit 1 零事件，detached 真跑复现）。"""
    from gherkai.detached import build_local_reconcile

    # 造最小 run 落盘（build_local_reconcile 要 load_run_meta 读回）
    meta = RunMeta(run_id="run-r", created_at="t0", jobs=(_job("a"),))
    store = LocalRunStore(tmp_path)
    store.create_run(meta, RunState(run_id="run-r", status=Status.PENDING,
                                    jobs={"a": JobState("a", Status.PENDING)},
                                    started_at="t0", high_water_mark=0))
    monkeypatch.setenv("AWS_REGION", "us-test-9")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    repo = Path(__file__).resolve().parents[2]
    _m, _l, _s, launcher, _mc, _rs, _rp = build_local_reconcile(
        repo, str(tmp_path), "run-r", max_concurrency=1, region=None, profile=None)
    # 解析结果最终注进各引擎 worker 的 spawn env（与前台 run 同一注入面）
    eng = launcher._resolver("novaact")
    assert eng._env.get("AWS_REGION") == "us-test-9"
