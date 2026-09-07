"""reconciler tick 测试（ADR 0034 P3）：推进编排 + 幂等 + CAS 起 job + finalize。

用真 SqliteEventLog + LocalRunStore + fake Launcher（记录被 launch 的 job，不起真进程）验证 tick 逻辑：
- 首 tick 从全 pending 起首批（≤max_concurrency）；
- worker 事件落 log 后 tick 推进态、起下一个；
- 全部两件都要齐 → finalize；
- 幂等：重复 tick 不重复 launch（CAS 挡）。
纯编排逻辑（launch 被 fake）→ 绿即够；真进程脱离/SQLite 并发是 P3 后半的真跑边界。
"""
from __future__ import annotations

from gherkai_core.adapters.event_log import SqliteEventLog
from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step
from gherkai_core.reconcile import tick


class FakeLauncher:
    def __init__(self) -> None:
        self.launched: list[str] = []

    def launch(self, job: Job) -> None:
        self.launched.append(job.scope_id)


def _job(sid: str) -> Job:
    return Job(scope_id=sid, scope_name=sid, engine="novaact",
               scenarios=(Scenario(id=f"{sid}:1", name="s", steps=(Step(0, "Given", "x"),)),))


def _meta(*sids: str) -> RunMeta:
    return RunMeta(run_id="run-1", created_at="t0", jobs=tuple(_job(s) for s in sids))


def _setup(tmp_path, *sids: str):
    meta = _meta(*sids)
    log = SqliteEventLog(tmp_path / "e.db")
    store = LocalRunStore(tmp_path)
    initial = RunState(run_id="run-1", status=Status.PENDING,
                       jobs={s: JobState(s, Status.PENDING) for s in sids},
                       started_at="t0", high_water_mark=0)
    store.create_run(meta, initial)
    return meta, log, store


def _done_events(log, sid, base=1):
    """给某 scope 落「跑完 passed + 干净退出」的完整事件序列。"""
    log.append_event(sid, base, f'{{"type":"scope_started","scopeId":"{sid}","sessionId":"s"}}', 1.0)
    log.append_event(sid, base + 1, f'{{"type":"scenario_done","scenarioId":"{sid}:1","status":"passed"}}', 2.0)
    log.append_event(sid, base + 2, f'{{"type":"scope_done","scopeId":"{sid}"}}', 3.0)
    log.record_exit(sid, 0)


def test_first_tick_starts_up_to_concurrency(tmp_path):
    meta, log, store = _setup(tmp_path, "a", "b", "c")
    launcher = FakeLauncher()
    done = tick("run-1", meta, log, store, launcher, max_concurrency=2, now_iso="t1")
    assert done is False
    assert len(launcher.launched) == 2  # 起首批 2 个
    # 被 claim 的两个在 RunStore 里是 running
    state = store.load_run_state("run-1")
    running = [s for s, js in state.jobs.items() if js.status == Status.RUNNING]
    assert len(running) == 2


def test_tick_idempotent_no_double_launch(tmp_path):
    """重复 tick 不重复 launch（CAS 挡已 running，机制四）。"""
    meta, log, store = _setup(tmp_path, "a", "b")
    launcher = FakeLauncher()
    tick("run-1", meta, log, store, launcher, max_concurrency=2, now_iso="t1")
    n1 = len(launcher.launched)
    tick("run-1", meta, log, store, launcher, max_concurrency=2, now_iso="t1")  # 再 tick
    assert len(launcher.launched) == n1  # 没多起（a/b 已 running）


def test_tick_starts_next_after_completion(tmp_path):
    """一个 job 完成（两件都要齐）后，tick 腾出并发位、起下一个 pending。"""
    meta, log, store = _setup(tmp_path, "a", "b", "c")
    launcher = FakeLauncher()
    tick("run-1", meta, log, store, launcher, max_concurrency=2, now_iso="t1")  # 起 a,b
    # a 跑完
    _done_events(log, "a")
    tick("run-1", meta, log, store, launcher, max_concurrency=2, now_iso="t2")
    # a 完成腾位 → c 被起
    assert "c" in launcher.launched
    state = store.load_run_state("run-1")
    assert state.jobs["a"].status == Status.PASSED


def test_tick_finalizes_when_all_done(tmp_path):
    """全部 job 两件都要齐 → tick 返回 True 且 RunStore finalize 成终态。"""
    meta, log, store = _setup(tmp_path, "a")
    launcher = FakeLauncher()
    tick("run-1", meta, log, store, launcher, max_concurrency=2, now_iso="t1")  # 起 a
    _done_events(log, "a")
    done = tick("run-1", meta, log, store, launcher, max_concurrency=2, now_iso="t2")
    assert done is True
    state = store.load_run_state("run-1")
    assert state.status == Status.PASSED
    assert state.ended_at == "t2"


def test_tick_nonzero_exit_finalizes_error(tmp_path):
    """job 非0退出（机制二）→ 该 job error → run finalize 为 error。"""
    meta, log, store = _setup(tmp_path, "a")
    launcher = FakeLauncher()
    tick("run-1", meta, log, store, launcher, max_concurrency=2, now_iso="t1")
    # 内容 passed 但进程非干净退出
    log.append_event("a", 1, '{"type":"scope_started","scopeId":"a","sessionId":"s"}', 1.0)
    log.append_event("a", 2, '{"type":"scenario_done","scenarioId":"a:1","status":"passed"}', 2.0)
    log.append_event("a", 3, '{"type":"scope_done","scopeId":"a"}', 3.0)
    log.record_exit("a", 1)  # 非0
    done = tick("run-1", meta, log, store, launcher, max_concurrency=2, now_iso="t2")
    assert done is True
    assert store.load_run_state("run-1").status == Status.ERROR


def test_double_finalize_idempotent(tmp_path):
    """两个 tick 都见全终态：都返回 done=True（run 确已达终态），但 commit 只一次（机制三，ended_at 仍首次）。

    关键：第二个 tick 也返回 True——不能因「别人抢先 finalize」让接力推进者（status --wait）永远等不到 done
    （P3b-2 真跑 status --wait 死循环复现的修正）。commit 恰一次由 try_finalize 状态机单调条件写保证。"""
    meta, log, store = _setup(tmp_path, "a")
    launcher = FakeLauncher()
    tick("run-1", meta, log, store, launcher, max_concurrency=2, now_iso="t1")
    _done_events(log, "a")
    d1 = tick("run-1", meta, log, store, launcher, max_concurrency=2, now_iso="t2")
    d2 = tick("run-1", meta, log, store, launcher, max_concurrency=2, now_iso="t3")
    assert d1 is True and d2 is True  # 两个都见 run 达终态 → 都 done（接力者不被"别人已 finalize"卡死）
    assert store.load_run_state("run-1").ended_at == "t2"  # commit 仍恰一次（首次的 t2，未被 t3 覆盖）


class BoomLauncher:
    """launch 必抛的 fake（RunTask 放置失败/task-def 配错/Popen OSError 的抽象）。"""

    def __init__(self) -> None:
        self.attempts: list[str] = []

    def launch(self, job: Job) -> None:
        self.attempts.append(job.scope_id)
        raise RuntimeError(f"boom: {job.scope_id}")


def test_launch_failure_does_not_wedge_run(tmp_path):
    """launch 抛异常 → 补偿记非0退出 → 下轮判 ERROR 收敛，run 不 wedge（ADR 0034 机制二推论）。"""
    meta, log, store = _setup(tmp_path, "a", "b")
    boom = BoomLauncher()
    # tick1：两个 job 都被 claim、launch 都炸——异常不裸穿、补偿落 task_exited
    done = tick("run-1", meta, log, store, boom, max_concurrency=2, now_iso="t1")
    assert done is False
    assert boom.attempts == ["a", "b"]  # 第一个炸不拖垮第二个（失败隔离）
    # tick2：重放看到 exit≠0 → 两 job ERROR → 全终态 → finalize，run 收敛
    done = tick("run-1", meta, log, store, boom, max_concurrency=2, now_iso="t2")
    assert done is True
    state = store.load_run_state("run-1")
    assert state.status == Status.ERROR
    assert all(js.status == Status.ERROR for js in state.jobs.values())
    assert boom.attempts == ["a", "b"]  # 不重复 launch（已 ERROR、plan_next 不再提议）


def test_launch_failure_isolated_other_job_completes(tmp_path):
    """一个 job 起不来，另一个照常跑完——失败隔离 + 聚合 ERROR。"""

    class HalfBoom:
        def __init__(self) -> None:
            self.launched: list[str] = []

        def launch(self, job: Job) -> None:
            if job.scope_id == "a":
                raise RuntimeError("boom: a")
            self.launched.append(job.scope_id)

    meta, log, store = _setup(tmp_path, "a", "b")
    hb = HalfBoom()
    tick("run-1", meta, log, store, hb, max_concurrency=2, now_iso="t1")
    assert hb.launched == ["b"]  # b 照常起
    _done_events(log, "b")  # b 跑完 passed
    done = tick("run-1", meta, log, store, hb, max_concurrency=2, now_iso="t2")
    assert done is True
    state = store.load_run_state("run-1")
    assert state.jobs["a"].status == Status.ERROR
    assert state.jobs["b"].status == Status.PASSED
    assert state.status == Status.ERROR  # 任一 error → run error（ADR 0031 决定三）
