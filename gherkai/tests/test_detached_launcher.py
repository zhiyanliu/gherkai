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


def _job(sid: str) -> Job:
    return Job(scope_id=sid, scope_name=sid, engine="novaact",
               scenarios=(Scenario(id=f"{sid}:0", name="sc", steps=(
                   Step(0, "Given", '打开 "https://x"'), Step(1, "When", "搜索"), Step(2, "Then", "进入"),
               )),))


def _setup(tmp_path, mode, *sids):
    meta = RunMeta(run_id="run-1", created_at="t0", jobs=tuple(_job(s) for s in sids))
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
