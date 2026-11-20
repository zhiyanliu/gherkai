"""SubprocessLauncher + reconcile loop 真实运行集成测试（ADR 0034 本机后端）。

**真 spawn echo_worker 子进程**（不产生 AWS 费用，但真 fd3/真退出码/真 SQLite）——这是「绿≠对」里该真实运行的：
launcher 读真 fd3 落 SQLite、真 handle.wait() 拿退出码写 task_exited、reconcile loop 真推进到终态。
纯逻辑部分（project/plan_next/条件写）已在 core 单测覆盖；此处补 launcher 接线的真进程边界。

复用 core/tests/fixtures/echo_worker.py（WORKER_MODE=pass/crash 控制行为）。
"""
from __future__ import annotations

import os
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from gherkai_core.adapters.event_log import SqliteEventLog
from gherkai_core.adapters.result_store.local import LocalResultStore
from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.adapters.subprocess_engine import SubprocessEngine
from gherkai_core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step
from gherkai_core.persist import result_without_record
from gherkai_core.project import DEADLINE_TIMEOUT_MESSAGE
from gherkai_core.run_status import RUN_ENDINGS, CommitOutcome, definition_unavailable_ending
from gherkai_core.serialize import instant_from_iso, instant_to_iso

from gherkai_runtime.detached import SubprocessLauncher, run_reconcile_loop

# 运行期限规则不介入的用例统一用的期限：远在任何真实时刻与假墙钟之后
_FAR = "2999-01-01T00:00:00+00:00"

# echo_worker：core 的测试 fixture（真 worker 的假替身，吐 ADR 0024 事件到 fd3）
_ECHO = str(Path(__file__).resolve().parents[2] / "core" / "tests" / "fixtures" / "echo_worker.py")


def _echo_resolver(mode: str):
    """按 WORKER_MODE 起 echo_worker 的 SubprocessEngine，包成 resolver（所有 engine 名都映射到它）。"""
    env = {**os.environ, "WORKER_MODE": mode}
    engine = SubprocessEngine(cmd=[sys.executable, _ECHO], env=env)
    return lambda _name: engine


def _job(sid: str, timeout_s: float = 600.0) -> Job:  # 运行定义里的预算恒为有限正数（ADR 0054 决策十）
    return Job(scope_id=sid, scope_name=sid, engine="novaact", timeout_s=timeout_s,
               scenarios=(Scenario(id=f"{sid}:0", name="sc", steps=(
                   Step(0, "Given", '"https://x"'), Step(1, "When", "搜索"), Step(2, "Then", "进入"),
               )),))


# 注入确定性墙钟（避免真时钟；这里固定即可，期限远在其后）。固定的墙钟下截止时刻永远不到，用例里的 worker 都自行结束
def _now():
    return datetime(2026, 7, 19, tzinfo=timezone.utc)


def _one_hour_later():
    return datetime(2026, 7, 19, 1, tzinfo=timezone.utc)


def _wait_until(predicate, timeout_s: float = 10.0) -> None:
    """轮询到 predicate 成立；超时即让用例失败，不挂住。"""
    deadline = time.monotonic() + timeout_s
    while not predicate():
        assert time.monotonic() < deadline, "等待的条件没有出现"
        time.sleep(0.01)


def _setup(tmp_path, mode, *sids, timeout_s: float = 600.0, clock=_now, deadline_at: str = _FAR):
    """建一个 run 与它的启动器。clock 是启动器的截止时刻检查读的墙钟，用例须把同一个时钟交给推进循环（组合根两处注入的也是同一个
    读取点）：截止时刻由推进循环取的认领时刻算出，两处时钟不同就比较不出意义。"""
    meta = RunMeta(run_id="run-1", created_at="t0",
                   jobs=tuple(_job(s, timeout_s=timeout_s) for s in sids), deadline_at=deadline_at)
    log = SqliteEventLog(tmp_path / "events.db")
    store = LocalRunStore(tmp_path)
    store.create_run(meta, RunState(run_id="run-1", status=Status.PENDING,
                                    jobs={s: JobState(s, Status.PENDING) for s in sids},
                                    started_at="t0", high_water_mark=0))
    # 测试显式给短 grace（echo_worker 收 SIGTERM 即协作退）；生产由组合根注 compose.engine_min_grace，参数无缺省
    launcher = SubprocessLauncher(_echo_resolver(mode), log, min_grace_fn=lambda _engine: 1.0, clock=clock)
    return meta, log, store, launcher


def test_single_job_passes_end_to_end(tmp_path):
    """真 spawn echo_worker(pass) → 事件落 SQLite → reconcile loop 推进到 passed 终态。"""
    meta, log, store, launcher = _setup(tmp_path, "pass", "a")
    run_reconcile_loop("run-1", meta, log, store, launcher, max_concurrency=1,
                       poll_interval_s=0.05, clock=_now, result_store=LocalResultStore(tmp_path))
    state = store.load_run_state("run-1")
    assert state.status == Status.PASSED
    assert state.jobs["a"].status == Status.PASSED
    assert state.ended_at == "2026-07-19T00:00:00+00:00"
    # 事件真落了 SQLite（scope_started + 各 step_done + scope_done）
    recs = log.records()
    assert any(r.kind == "event" for r in recs)
    assert any(r.kind == "exit" and r.exited.exit_code == 0 for r in recs)


def test_two_jobs_concurrency_one(tmp_path):
    """max_concurrency=1：两 job 串行推进、都 passed。验 loop 起完一个再起下一个。"""
    meta, log, store, launcher = _setup(tmp_path, "pass", "a", "b")
    run_reconcile_loop("run-1", meta, log, store, launcher, max_concurrency=1,
                       poll_interval_s=0.05, clock=_now, result_store=LocalResultStore(tmp_path))
    state = store.load_run_state("run-1")
    assert state.status == Status.PASSED
    assert state.jobs["a"].status == Status.PASSED
    assert state.jobs["b"].status == Status.PASSED


def test_job_timeout_stops_worker_and_attributes_timeout(tmp_path):
    """job timeout local enforce 真实运行（ADR 0034「job timeout」节）：silent worker 卡死不吐新事件、不自退——
    launcher 的截止时刻检查按墙钟到点协作停（SIGTERM→echo 干净地以退出码 0 退出）→ task_exited(timed_out=True)
    → project 判 ERROR + error_type=timeout。**协作停后退出码 0 也不误判 passed**（timed_out 短路内容判定）。"""
    from gherkai_core.project import project_full
    from gherkai_runtime import compose

    meta, log, store, launcher = _setup(tmp_path, "silent", "a", timeout_s=0.5, clock=compose.now)
    run_reconcile_loop("run-1", meta, log, store, launcher, max_concurrency=1,
                       poll_interval_s=0.05, clock=compose.now, result_store=LocalResultStore(tmp_path))
    state = store.load_run_state("run-1")
    assert state.status == Status.ERROR
    assert state.jobs["a"].status == Status.ERROR
    exits = [r for r in log.records() if r.kind == "exit"]
    assert len(exits) == 1 and exits[0].exited.timed_out is True
    claimed = {"a": instant_from_iso(state.jobs["a"].claimed_at)}
    assert exits[0].exited.exited_at > claimed["a"]  # 启动器记下它看到 worker 退出的那一刻（同一个注入的墙钟）
    [jr] = project_full(meta, log.records(), claimed_at=claimed)
    assert jr.error_type == "timeout"  # 归因链端到端（真进程边界）
    assert jr.session_id == "echo-sess"  # 血缘仍从 scope_started 捕获（超时不丢会话线索）


def test_relay_recovers_foreign_timed_out_claim(tmp_path):
    """接力恢复：他人 claim 的 RUNNING job（owner 进程已死、
    无 handle 无观察链）过了截止时刻加 10 秒 → loop 防御扫补写一条判为超时的未知退出（不带退出时刻）收敛 ERROR，run 不永久 wedge。"""
    meta, log, store, launcher = _setup(tmp_path, "pass", "a", timeout_s=60.0, clock=_one_hour_later)
    # 模拟死 owner 遗留态：a 已被 claim（claimed_at 一小时前）、无退出记录、本 launcher 没起过它
    assert store.try_claim_job("run-1", "a", claimed_at="2026-07-19T00:00:00Z") is True
    run_reconcile_loop("run-1", meta, log, store, launcher, max_concurrency=1,
                       poll_interval_s=0.05, clock=_one_hour_later, result_store=LocalResultStore(tmp_path))
    state = store.load_run_state("run-1")
    assert state.status == Status.ERROR
    exits = [r for r in log.records() if r.kind == "exit"]
    assert len(exits) == 1 and exits[0].exited.timed_out is True
    assert exits[0].exited.exit_code is None  # 无观察到的退出码——诚实留空（「码未知」分支被 timed_out 归因短路）
    assert exits[0].exited.exited_at is None  # 也没有可观察的退出时刻


def test_grace_query_failure_never_spawns_a_worker(tmp_path):
    """grace 下限现在要 spawn 一次 worker 自述才能取得、**会抛**（ADR 0024「引擎自报下限」：旧 worker 不认入口 /
    定位不到 / 答非契约）——launch 必须问在起 worker **之前**：抛在 run_scope 之后就是「worker 已起、_pump 没起」，
    tick 的 launch 失败补偿（退出码未知的退出记录）以「进程没起」为前提，那时留下的是没人读 fd3、没人 wait、
    没人 stop 的孤儿 worker（真会话真计费）。这里钉：min_grace_fn 抛 → run_scope 零调用、job 经补偿收敛 ERROR。"""
    meta, log, store, _ = _setup(tmp_path, "pass", "a", timeout_s=60.0)
    spawned: list[str] = []
    real_engine = _echo_resolver("pass")("novaact")

    class _Spy:
        def run_scope(self, job, **kw):
            spawned.append(job.scope_id)
            return real_engine.run_scope(job, **kw)

    def _old_worker(_engine: str) -> float:
        raise RuntimeError("引擎 novaact 的能力自述超时")  # 旧 worker 不认 --capabilities 的真实形态之一

    launcher = SubprocessLauncher(lambda _name: _Spy(), log, min_grace_fn=_old_worker, clock=_now)
    run_reconcile_loop("run-1", meta, log, store, launcher, max_concurrency=1,
                       poll_interval_s=0.05, clock=_now, result_store=LocalResultStore(tmp_path))
    assert spawned == []  # 下限取不到 → 一个 worker 都没起（无孤儿）
    state = store.load_run_state("run-1")
    assert state.status == Status.ERROR
    exits = [r for r in log.records() if r.kind == "exit"]
    assert len(exits) == 1 and exits[0].exited.exit_code is None
    assert exits[0].exited.reason == "起 worker 失败：引擎 novaact 的能力自述超时"


def test_crash_worker_finalizes_error(tmp_path):
    """echo_worker(crash) 非 0 退出 → task_exited 带非0 → project 判 error → 终态写记下 error，run 随之为 error（机制二真实运行）。"""
    meta, log, store, launcher = _setup(tmp_path, "crash", "a")
    run_reconcile_loop("run-1", meta, log, store, launcher, max_concurrency=1,
                       poll_interval_s=0.05, clock=_now, result_store=LocalResultStore(tmp_path))
    state = store.load_run_state("run-1")
    assert state.status == Status.ERROR
    # task_exited 记了真实非 0 退出码
    exits = [r for r in log.records() if r.kind == "exit"]
    assert len(exits) == 1 and exits[0].exited.exit_code != 0


def test_report_is_generated_from_the_record_after_the_commit(tmp_path):
    """这一方的写使 run 成为终态之后，推进循环从记录生成报告、只生成一次（ADR 0034 机制三「run 级状态只进不退」条④）：报告里
    run 与 job 的状态就是记录里的运行态；两个 job 的终态各点名一份判定明细（两个标识不同，文件名只由标识构成），报告附上的正是
    按标识读回的那两份（ADR 0030 决定三「点名」条；两个 job 在哪一轮得出结果随真实进程的时序而定，读法不因此不同）；run 级墙钟由
    运行态的开始与结束时刻算出。"""
    from gherkai_core.project import run_duration_ms
    from gherkai_runtime import compose

    # 真时钟（非 _now 常量）：开始与结束两个时刻都要能解析，墙钟才有值
    meta = RunMeta(run_id="run-1", created_at=compose.now_iso(), jobs=(_job("a"), _job("b")), deadline_at=_FAR)
    log = SqliteEventLog(tmp_path / "events.db")
    store = LocalRunStore(tmp_path)
    store.create_run(meta, RunState(run_id="run-1", status=Status.PENDING,
                                    jobs={s: JobState(s, Status.PENDING) for s in ("a", "b")},
                                    started_at=compose.now_iso(), high_water_mark=0))
    launcher = SubprocessLauncher(_echo_resolver("pass"), log, min_grace_fn=lambda _engine: 1.0, clock=compose.now)
    reports = _CapturingReports()
    run_reconcile_loop("run-1", meta, log, store, launcher, max_concurrency=2, poll_interval_s=0.05, clock=compose.now,
                       result_store=LocalResultStore(tmp_path), report_store=reports)

    recorded = store.load_run_state("run-1")
    [result] = reports.results
    assert result.run_id == "run-1"
    assert result.state == recorded and result.status == Status.PASSED  # 状态取记录
    assert [o.scope_id for o in result.jobs] == ["a", "b"]  # 按运行定义的次序列出全部 job
    assert [(d.scope_id, d.status) for d in result.details] == [("a", Status.PASSED), ("b", Status.PASSED)]
    named = {sid: recorded.jobs[sid].result_id for sid in ("a", "b")}
    assert None not in named.values() and named["a"] != named["b"]
    assert sorted(p.name for p in (tmp_path / "run-1" / "jobs").iterdir()) == sorted(f"{rid}.json" for rid in named.values())
    saved = LocalResultStore(tmp_path)
    assert list(result.details) == [saved.load_job_result("run-1", named[sid]) for sid in ("a", "b")]
    assert result.duration_ms is not None and result.duration_ms == run_duration_ms(recorded)


def test_loop_ends_normally_when_the_record_read_for_the_report_fails(tmp_path):
    """为生成报告而读运行态的那一次失败，不击穿已到终态的 run（ADR 0030 决定三「ReportStore.write 失败隔离」框，ADR 0034 机制三
    「run 级状态只进不退」条④）。

    这次读发生在这一方的终态写**之后**，落盘读会因 IO 错、文件写坏而抛。原样抛出去意味着 run 已到终态、报告没有生成，而且
    `drive_local_reconcile` 的拆隧道那步（在本函数返回后才执行）被跳过、隧道留在公网。所以循环正常返回；报告从记录组装，读不到
    记录就不生成；终态写本身不受影响。云端推进侧做法相同，两个宿主各一条护栏。
    """
    from gherkai_core.model import TERMINAL_STATUSES
    from gherkai_runtime import compose

    class _FailsOnTerminalRead:
        """代理真 RunStore：run 已终态时的 load_run_state（即为生成报告而读的那次）抛 OSError，其余原样转发。"""

        def __init__(self, inner):
            self._inner = inner
            self.raised = 0

        def __getattr__(self, name):
            return getattr(self._inner, name)

        def load_run_state(self, run_id):
            state = self._inner.load_run_state(run_id)
            if state is not None and state.status in TERMINAL_STATUSES:
                self.raised += 1
                raise OSError("run_state.json 读坏了")
            return state

    meta, log, inner, launcher = _setup(tmp_path, "pass", "a")
    store, reports = _FailsOnTerminalRead(inner), _CapturingReports()

    # 不抛是第一件要钉的事（把这次读挪出失败隔离即 OSError 原样抛出）
    run_reconcile_loop("run-1", meta, log, store, launcher, max_concurrency=1,
                       poll_interval_s=0.05, clock=_now, result_store=LocalResultStore(tmp_path), report_store=reports)

    assert store.raised == 1                    # 失败确实落在为生成报告而读的那一次上
    assert reports.results == []                # 读不到记录就不生成报告
    assert inner.load_run_state("run-1").status == Status.PASSED  # 终态写本身不受影响


class _RecordingReports:
    def __init__(self) -> None:
        self.written: list[str] = []

    def write(self, run_id, result, *, created_at):
        self.written.append(run_id)


class _BoundedReads:
    """代理真 RunStore：load_run_state 超过上限即抛，推进循环不结束时用例以失败结束而不是挂住。"""

    def __init__(self, inner, limit: int) -> None:
        self._inner, self._limit, self.reads = inner, limit, 0

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def load_run_state(self, run_id):
        self.reads += 1
        if self.reads > self._limit:
            raise RuntimeError("推进循环没有结束")
        return self._inner.load_run_state(run_id)


def test_loop_ends_on_a_run_ended_by_the_definition_unavailable_ending_without_report(tmp_path):
    """已由运行定义不可用的结束写结束的 run（run 与每个 job 都是 error）：本机推进循环读到既有终态，第一轮即退出，不起 worker、不写
    报告、不改运行态（ADR 0034 机制三④）。

    不判停时，这个 run 没有 pending 也没有 running 的 job，推进决策没有任何动作，每一轮都返回继续推进，循环永不结束，随后的拆隧道也
    一直不执行。这里用读次数上限把「不结束」变成有界失败。"""
    meta, log, inner, _ = _setup(tmp_path, "pass", "a", "b")
    assert inner.end_run("run-1", definition_unavailable_ending("提交记录不完整"), ended_at="2026-07-19T00:00:00+00:00") is True
    before = inner.load_run_state("run-1")
    assert before.status == Status.ERROR and {js.status for js in before.jobs.values()} == {Status.ERROR}  # 构造的前提
    spawned: list[str] = []
    launcher = SubprocessLauncher(lambda _name: spawned.append(_name), log, min_grace_fn=lambda _engine: 1.0, clock=_now)
    store, reports = _BoundedReads(inner, limit=20), _RecordingReports()

    run_reconcile_loop("run-1", meta, log, store, launcher, max_concurrency=2,
                       poll_interval_s=0.01, clock=_now, result_store=LocalResultStore(tmp_path), report_store=reports)

    assert store.reads == 1            # 一轮即停
    assert spawned == [] and reports.written == []
    assert inner.load_run_state("run-1") == before


def test_loop_ends_without_report_when_its_commit_is_lost(tmp_path):
    """终态写写不成（并发推进器先写下了同样的终态，run 已结束）：循环照样结束，但不写报告——报告只由使 run 成为终态的一方生成
    （ADR 0054 决策二后台推进条「收尾与报告」）；库中终态是先写下的那一份（ADR 0034 机制三「run 级状态只进不退」条④）。"""

    class _LosesCommit:
        def __init__(self, inner) -> None:
            self._inner = inner
            self.results: list[CommitOutcome] = []

        def __getattr__(self, name):
            return getattr(self._inner, name)

        def commit_job_states(self, run_id, job_states, *, ended_at):
            self._inner.commit_job_states(run_id, job_states, ended_at="other")  # 另一推进器先写下
            self.results.append(self._inner.commit_job_states(run_id, job_states, ended_at=ended_at))
            return self.results[-1]

    meta, log, inner, launcher = _setup(tmp_path, "pass", "a")
    store, reports = _LosesCommit(inner), _RecordingReports()
    run_reconcile_loop("run-1", meta, log, store, launcher, max_concurrency=1,
                       poll_interval_s=0.05, clock=_now, result_store=LocalResultStore(tmp_path), report_store=reports)
    assert store.results == [CommitOutcome.ALREADY_ENDED]
    assert reports.written == []
    state = inner.load_run_state("run-1")
    assert state.status == Status.PASSED and state.ended_at == "other"


def test_loop_does_not_rewrite_the_report_of_a_committed_run(tmp_path):
    """另一个推进器已提交终态并写过报告之后，本机推进循环读到既有终态即退出，不重写报告、不改运行态
    （ADR 0034 机制三「run 级状态只进不退」条④）。job 全为终态、事件完整，若照旧走收尾路径就能重写出一份报告，
    所以本例区分得出「读到既有终态时不写报告」。第二个循环经读次数上限代理，循环不结束时本例以失败结束而不是挂住。"""
    meta, log, store, launcher = _setup(tmp_path, "pass", "a")
    first = _RecordingReports()
    run_reconcile_loop("run-1", meta, log, store, launcher, max_concurrency=1,
                       poll_interval_s=0.05, clock=_now, result_store=LocalResultStore(tmp_path), report_store=first)
    assert first.written == ["run-1"]
    before = store.load_run_state("run-1")
    assert before.status == Status.PASSED

    again, bounded = _RecordingReports(), _BoundedReads(store, limit=20)
    run_reconcile_loop("run-1", meta, log, bounded, launcher, max_concurrency=1,
                       poll_interval_s=0.01, clock=_one_hour_later, result_store=LocalResultStore(tmp_path),
                       report_store=again)

    assert bounded.reads == 1          # 一轮即停

    assert again.written == []
    assert store.load_run_state("run-1") == before


def test_drive_local_reconcile_tears_down_tunnel_for_an_already_terminal_run(tmp_path, monkeypatch):
    """`status --wait` 接力与 per-run 进程共用的入口：run 已由运行定义不可用的结束写结束（run 与 job 都是 error）时推进结束、照常
    拆隧道，不写报告、不改运行态（ADR 0034 机制三④）。推进放在线程里、限时等待：循环不结束时本例失败而不挂住。"""
    import threading

    from gherkai_runtime import compose, detached
    from gherkai_runtime import tunnel as gtunnel

    _seed_for_build(tmp_path, "run-t", max_concurrency=1)
    assert LocalRunStore(tmp_path).end_run("run-t", definition_unavailable_ending("提交记录不完整"), ended_at="t1") is True
    before = LocalRunStore(tmp_path).load_run_state("run-t")
    (tmp_path / "run-t" / "tunnel.json").write_text('{"pid": 4343}', encoding="utf-8")
    monkeypatch.setenv("AWS_REGION", "us-test-9")
    env = {**os.environ, "WORKER_MODE": "pass"}
    monkeypatch.setattr(compose, "build_engines",
                        lambda **kw: {"novaact": SubprocessEngine(cmd=[sys.executable, _ECHO], env=env)})
    stopped: list[int] = []
    monkeypatch.setattr(gtunnel, "stop_tunnel", lambda pid: stopped.append(pid))

    worker = threading.Thread(
        target=detached.drive_local_reconcile, args=(str(tmp_path), "run-t", 1),
        kwargs={"region": None, "profile": None, "poll_interval_s": 0.01}, daemon=True)
    worker.start()
    worker.join(timeout=10)

    assert not worker.is_alive(), "推进循环没有结束"
    assert stopped == [4343] and not (tmp_path / "run-t" / "tunnel.json").exists()
    assert not (tmp_path / "run-t" / "index.html").exists() and not (tmp_path / "run-t" / "manifest.json").exists()
    assert LocalRunStore(tmp_path).load_run_state("run-t") == before
    assert before.jobs["a"].status == Status.ERROR


def test_build_local_reconcile_resolves_region_like_foreground(tmp_path, monkeypatch):
    """region 走与前台 run 相同的解析链（ADR 0016 决策 C）：不显式给 --region 时 env/profile config 兜底、
    落实成字符串注入 worker env——曾原样透传 None：worker 里 AgentCore validate_region 见 None 即崩
    （exit 1 零事件，detached 实际运行复现）。"""
    from gherkai_runtime.detached import build_local_reconcile

    # 造最小 run 落盘（build_local_reconcile 要 load_run_meta 读回）
    meta = RunMeta(run_id="run-r", created_at="t0", jobs=(_job("a"),), deadline_at=_FAR)
    store = LocalRunStore(tmp_path)
    store.create_run(meta, RunState(run_id="run-r", status=Status.PENDING,
                                    jobs={"a": JobState("a", Status.PENDING)},
                                    started_at="t0", high_water_mark=0))
    monkeypatch.setenv("AWS_REGION", "us-test-9")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    _m, _l, _s, launcher, _mc, _rs, _rp = build_local_reconcile(
        str(tmp_path), "run-r", max_concurrency=1, region=None, profile=None)
    # 解析结果最终注进各引擎 worker 的 spawn env（与前台 run 同一注入面）
    eng = launcher._resolver("novaact")
    assert eng._env.get("AWS_REGION") == "us-test-9"


def test_build_local_reconcile_goes_through_resolve_aws_identity(tmp_path, monkeypatch):
    """后台重建端与前台 run 共用**同一个** region/profile 解析实现（ADR 0016 决策 C）：本函数不自写一份。

    换掉 `compose.resolve_aws_identity` 即换掉后台这条链——两处各写一份时，改一处漏一处就让同一个 run 在
    提交进程与后台宿主下注入不同的 AWS_REGION/AWS_PROFILE。
    """
    from gherkai_runtime import compose
    from gherkai_runtime.detached import build_local_reconcile

    _seed_for_build(tmp_path, "run-id", max_concurrency=None)
    seen = []

    def _fake_identity(region, profile):
        seen.append((region, profile))
        return "us-test-1", "prof-x"

    monkeypatch.setattr(compose, "resolve_aws_identity", _fake_identity)
    _m, _l, _s, launcher, _mc, _rs, _rp = build_local_reconcile(
        str(tmp_path), "run-id", max_concurrency=1, region=None, profile=None)
    assert seen == [(None, None)]  # 入参原样交给唯一实现，不在本函数预处理
    eng = launcher._resolver("novaact")  # 解析结果最终注进 worker spawn env
    assert eng._env.get("AWS_REGION") == "us-test-1"
    assert eng._env.get("AWS_PROFILE") == "prof-x"


def _seed_for_build(tmp_path, run_id: str, *, max_concurrency: int | None):
    """落一个最小 run（单 pending job）供 build_local_reconcile 读回，meta 的 max_concurrency 按参数。"""
    meta = RunMeta(run_id=run_id, created_at="t0", jobs=(_job("a"),), max_concurrency=max_concurrency, deadline_at=_FAR)
    store = LocalRunStore(tmp_path)
    store.create_run(meta, RunState(run_id=run_id, status=Status.PENDING,
                                    jobs={"a": JobState("a", Status.PENDING)},
                                    started_at="t0", high_water_mark=0))


def test_build_local_reconcile_prefers_meta_max_concurrency(tmp_path):
    """并发上限以 definition 为准：入参 flag 与 meta 冲突时用 meta（ADR 0034 机制四）——`status --wait` 接力者
    的 flag 值可能与 submit 时不同，接力不该悄悄改这个 run 的并行度。"""
    from gherkai_runtime.detached import build_local_reconcile

    _seed_for_build(tmp_path, "run-m", max_concurrency=3)
    _m, _l, _s, _launcher, mc, _rs, _rp = build_local_reconcile(
        str(tmp_path), "run-m", max_concurrency=1, region="us-east-1")
    assert mc == 3


def test_build_local_reconcile_falls_back_to_flag_when_meta_missing(tmp_path):
    """对偶（防「恒取入参」的假绿反面）：meta 无值（打通前落的旧 definition）→ 回落入参 flag。"""
    from gherkai_runtime.detached import build_local_reconcile

    _seed_for_build(tmp_path, "run-f", max_concurrency=None)
    _m, _l, _s, _launcher, mc, _rs, _rp = build_local_reconcile(
        str(tmp_path), "run-f", max_concurrency=2, region="us-east-1")
    assert mc == 2


def test_build_local_reconcile_injects_run_id_to_both_engines(tmp_path, monkeypatch):
    """本 run 的 id 经 env RUN_ID 注给两个 worker（ADR 0024「run_id + scope_id 注入 worker」条）：per-run 进程与 `status --wait`
    接力者都经这里起 worker，worker 用它编码会话名的 run 段（ADR 0051 决策 3、4），缺了它两个 worker 都在建会话前以 1 退出。
    取值是被推进的这个 run，宿主 shell 里残留的同名值不得越过它；本机只注 RUN_ID，不注 SCOPE_ID，事件出口仍是 fd 态。"""
    from gherkai_runtime.detached import build_local_reconcile

    _seed_for_build(tmp_path, "run-id-x", max_concurrency=1)
    monkeypatch.setenv("RUN_ID", "host-run")
    # Midscene worker 经定位链第一级指到占位命令：本例只看 spawn env，不起进程，也不依赖本机有没有构建过 Midscene worker
    monkeypatch.setenv("GHERKAI_WORKER_MIDSCENE_CMD", "node /fake/midscene-worker.mjs")
    monkeypatch.delenv("GHERKAI_WORKER_MIDSCENE_CWD", raising=False)
    _m, _l, _s, launcher, _mc, _rs, _rp = build_local_reconcile(
        str(tmp_path), "run-id-x", max_concurrency=1, region="us-east-1")
    for engine in ("novaact", "midscene"):
        env = launcher._resolver(engine)._env
        assert env is not None and env["RUN_ID"] == "run-id-x", engine
        assert "SCOPE_ID" not in env, engine


def test_build_local_reconcile_reads_steps_dir_from_definition(tmp_path, monkeypatch):
    """使用方 step 目录随 definition 走：宿主从 RunStore 读回 meta.steps_dir、
    经 env 注给 worker，**绝不重解析 `./steps`**（ADR 0037 决策 4）——per-run 进程与 `status --wait` 接力者的 CWD 与提交进程
    各不相同，重解析会让同一个 run 在三个宿主下用到不同的确定性 step 集、判定不可复现。
    """
    from gherkai_runtime.detached import build_local_reconcile

    meta = RunMeta(run_id="run-s", created_at="t0", jobs=(_job("a"),), steps_dir="/abs/user/steps", deadline_at=_FAR)
    store = LocalRunStore(tmp_path)
    store.create_run(meta, RunState(run_id="run-s", status=Status.PENDING,
                                    jobs={"a": JobState("a", Status.PENDING)},
                                    started_at="t0", high_water_mark=0))
    # 宿主 CWD 下另有一个 ./steps：必须**不被**用上（definition 是唯一真源）
    (tmp_path / "steps").mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GHERKAI_STEPS_DIR", raising=False)
    _m, _l, _s, launcher, _mc, _rs, _rp = build_local_reconcile(
        str(tmp_path), "run-s", max_concurrency=1, region="us-east-1")
    assert launcher._resolver("novaact")._env["GHERKAI_STEPS_DIR"] == "/abs/user/steps"


def test_build_local_reconcile_no_steps_dir_when_definition_has_none(tmp_path, monkeypatch):
    """对偶（防「恒注入」假绿）：definition 无 steps_dir（未给/旧落盘/云端后端）→ 宿主不注入该 env，
    即便宿主 CWD 下恰好有个 `./steps`（宿主不重解析约定）。"""
    from gherkai_runtime.detached import build_local_reconcile

    _seed_for_build(tmp_path, "run-n", max_concurrency=1)
    (tmp_path / "steps").mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GHERKAI_STEPS_DIR", raising=False)
    _m, _l, _s, launcher, _mc, _rs, _rp = build_local_reconcile(
        str(tmp_path), "run-n", max_concurrency=1, region="us-east-1")
    assert "GHERKAI_STEPS_DIR" not in launcher._resolver("novaact")._env


def test_build_local_reconcile_host_env_steps_dir_does_not_leak(tmp_path, monkeypatch):
    """接力者 shell 的 GHERKAI_STEPS_DIR **不得**越过 definition（宿主一律从 definition 读回）。

    与 `test_build_local_reconcile_no_steps_dir_when_definition_has_none` 的区别正是漏检面：那条先 delenv 该 env，
    恰好绕开继承路径。真实形态是提交时没有确定性 step
    （definition steps_dir=None）、之后在 export 了该 env 的 shell 里 `status <run> --wait` 接力——若组合根只做
    加法，worker 会加载接力者那台机器的 step 目录，本 run 的确定性 step 集与 definition 不符、判定不可复现。
    """
    from gherkai_runtime.detached import build_local_reconcile

    _seed_for_build(tmp_path, "run-leak", max_concurrency=1)
    monkeypatch.setenv("GHERKAI_STEPS_DIR", "/host/relay/steps")
    monkeypatch.setenv("GHERKAI_NO_ARTIFACTS", "1")
    _m, _l, _s, launcher, _mc, _rs, _rp = build_local_reconcile(
        str(tmp_path), "run-leak", max_concurrency=1, region="us-east-1")
    env = launcher._resolver("novaact")._env
    assert env is not None  # 本路径恒注入产物落点，env 必非 None
    assert "GHERKAI_STEPS_DIR" not in env
    assert "GHERKAI_NO_ARTIFACTS" not in env  # 同为组合根拥有的键（产物开关也随 definition 走）


def test_run_state_timestamps_share_one_format(tmp_path):
    """RunState 内时间戳**格式统一**（ADR 0034「时钟也只一份」）：submit 侧写的 started_at 与推进器写的
    claimed_at/ended_at 出自同一个 `compose.now_iso`——曾各宿主一份 `_now_iso`、两种 ISO 格式并存
    （`+00:00` vs `…Z`），`status --json` 的机读消费者被迫兼容两种。故本例用真时钟（非 fake），
    逐字比对「解析回来再 isoformat 是否原样」——任一宿主退回 `strftime` 的 `…Z` 写法即失败。
    """
    from gherkai_runtime import compose

    meta = RunMeta(run_id="run-1", created_at=compose.now_iso(), jobs=(_job("a"),), deadline_at=_FAR)
    log = SqliteEventLog(tmp_path / "events.db")
    store = LocalRunStore(tmp_path)
    store.create_run(meta, RunState(run_id="run-1", status=Status.PENDING,
                                    jobs={"a": JobState("a", Status.PENDING)},
                                    started_at=compose.now_iso(), high_water_mark=0))
    launcher = SubprocessLauncher(_echo_resolver("pass"), log, min_grace_fn=lambda _engine: 1.0, clock=compose.now)
    run_reconcile_loop("run-1", meta, log, store, launcher, max_concurrency=1,
                       poll_interval_s=0.05, clock=compose.now, result_store=LocalResultStore(tmp_path))
    state = store.load_run_state("run-1")
    stamps = {"created_at": meta.created_at, "started_at": state.started_at,
              "ended_at": state.ended_at, "claimed_at": state.jobs["a"].claimed_at}
    assert all(stamps.values()), stamps  # 三个写者都真写了（否则断言空转）
    for name, ts in stamps.items():
        assert ts == instant_from_iso(ts).isoformat(), f"{name}={ts} 与 compose.now_iso 格式不同"


def test_drive_local_reconcile_drives_to_terminal_then_tears_down_tunnel(tmp_path, monkeypatch):
    """local 推进唯一入口的三步护栏（ADR 0034 三宿主同一套机制 + ADR 0035「终态即拆」）：装配 → 推到终态 → 拆隧道。
    只把引擎替成 echo_worker、只桩掉「真杀 pid」这一 OS 边界，其余真实运行——漏掉拆隧道那步即隧道留在公网。"""
    from gherkai_runtime import compose, detached
    from gherkai_runtime import tunnel as gtunnel

    _seed_for_build(tmp_path, "run-d", max_concurrency=1)
    (tmp_path / "run-d" / "tunnel.json").write_text('{"pid": 4242}', encoding="utf-8")
    monkeypatch.setenv("AWS_REGION", "us-test-9")
    env = {**os.environ, "WORKER_MODE": "pass"}
    monkeypatch.setattr(compose, "build_engines",
                        lambda **kw: {"novaact": SubprocessEngine(cmd=[sys.executable, _ECHO], env=env)})
    stopped: list[int] = []
    monkeypatch.setattr(gtunnel, "stop_tunnel", lambda pid: stopped.append(pid))

    detached.drive_local_reconcile(str(tmp_path), "run-d", 1, region=None, profile=None, poll_interval_s=0.01)

    state = LocalRunStore(tmp_path).load_run_state("run-d")
    assert state.status == Status.PASSED  # 推到终态
    # 终态点名的那一份判定明细已存下（明细先于终态写）
    result_id = state.jobs["a"].result_id
    assert result_id is not None and LocalResultStore(tmp_path).load_job_result("run-d", result_id) is not None
    assert stopped == [4242] and not (tmp_path / "run-d" / "tunnel.json").exists()  # 拆了隧道、交棒文件已清


def test_build_local_reconcile_reads_session_warmup_url_back_from_definition(tmp_path, monkeypatch):
    """预热地址随 definition 走（ADR 0051 决策 13）：per-run 重建端从 run_meta 读回、注进两个引擎的 worker env；
    宿主进程继承的同名值不算（三个宿主下同一个 run 要用同一个值）。"""
    from gherkai_runtime.detached import build_local_reconcile

    url = "https://t.ngrok-free.app/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=" + "a" * 32
    meta = RunMeta(run_id="run-w", created_at="t0", jobs=(_job("a"),),
                   extra_http_headers=(("ngrok-skip-browser-warning", "1"),), session_warmup_url=url, deadline_at=_FAR)
    store = LocalRunStore(tmp_path)
    store.create_run(meta, RunState(run_id="run-w", status=Status.PENDING,
                                    jobs={"a": JobState("a", Status.PENDING)},
                                    started_at="t0", high_water_mark=0))
    monkeypatch.setenv("GHERKAI_SESSION_WARMUP_URL", "https://leaked/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=x")
    monkeypatch.setenv("AWS_REGION", "us-test-9")
    monkeypatch.setenv("GHERKAI_WORKER_MIDSCENE_CMD", "node /nonexistent/midscene.mjs")  # 不找真 worker、只看注入面
    launcher = build_local_reconcile(str(tmp_path), "run-w", max_concurrency=1, region=None, profile=None)[3]
    for engine in ("novaact", "midscene"):
        env = launcher._resolver(engine)._env
        assert env["GHERKAI_SESSION_WARMUP_URL"] == url, engine
        assert env["GHERKAI_EXTRA_HTTP_HEADERS"] == '{"ngrok-skip-browser-warning": "1"}', engine


# ---------- 后台推进的到期处理（ADR 0054 决策二后台推进条，实测项 2）----------


class _FastClock:
    """真实时间按倍数走的墙钟：从 start 起，真实的 1 秒算作 factor 秒。推进循环、启动器的截止时刻检查与前台的调度循环读同一种
    时钟，期限可以落在几秒之内，停止启动的提前量（60 秒）仍按规则生效。"""

    def __init__(self, start: datetime, factor: float) -> None:
        self._start, self._factor, self._t0 = start, factor, time.monotonic()

    def __call__(self) -> datetime:
        return self._start + timedelta(seconds=(time.monotonic() - self._t0) * self._factor)


class _CapturingReports:
    """记下每次写报告用的 RunResult。"""

    def __init__(self) -> None:
        self.results: list = []

    def write(self, run_id, result, *, created_at):
        self.results.append(result)


def _verdict(result) -> tuple:
    """报告由它生成的那几项：run 级状态与说明；按运行定义的次序，各 job 的状态与 job 级说明（取运行态），有判定明细的另带明细里
    的错误类型与说明，由结束写结束的 job 没有明细、记为 None。"""
    return (result.status, result.message,
            [(o.scope_id, o.status, o.state.message,
              None if o.detail is None else (o.detail.error_type, o.detail.message)) for o in result.jobs])


def _foreground_result(execution):
    """前台同一情形的 run 结果：调度循环交回的执行事实按与记录相同的取法在内存里组装（与 `run --no-report` 同一条路）。"""
    return result_without_record(execution, ended_at="2026-07-19T00:00:00+00:00")


def test_advancer_stops_the_running_job_at_the_run_deadline_like_the_foreground(tmp_path):
    """本机推进进程到期（ADR 0054 实测项 2、4 的本机一对）：a 在停止启动之前被认领、它的预算远长于期限，截止时刻因此是期限；b 因
    并发上限排在后面，到了停止启动的时刻不再启动。期限一到推进进程按墙钟停下 a（真 echo_worker 收 SIGTERM 退出），a 记 aborted、
    说明是期限那一句、没有错误类型；b 由结束写记 skipped、带到期的说明、没有判定明细；run 状态按取法为 aborted、带 run 级的到期
    说明，报告生成。同一情形交给前台的调度循环（同一个 worker、同一种时钟），按同一套取法得到的结果逐项相同。"""
    from gherkai_core.schedule import ScheduleOpts, schedule

    ending = RUN_ENDINGS["deadline"]
    start = datetime(2026, 7, 19, tzinfo=timezone.utc)
    deadline_at = instant_to_iso(start + timedelta(seconds=120))  # 真实 2 秒后到期，1 秒后过停止启动的时刻
    clock = _FastClock(start, 60.0)
    meta, log, store, launcher = _setup(tmp_path, "silent", "a", "b", timeout_s=7200.0, clock=clock,
                                        deadline_at=deadline_at)
    reports = _CapturingReports()
    run_reconcile_loop("run-1", meta, log, store, launcher, max_concurrency=1, poll_interval_s=0.05, clock=clock,
                       result_store=LocalResultStore(tmp_path), report_store=reports)

    state = store.load_run_state("run-1")
    assert (state.status, state.message) == (Status.ABORTED, ending.run_message)
    assert (state.jobs["a"].status, state.jobs["b"].status) == (Status.ABORTED, Status.SKIPPED)
    assert state.jobs["b"].message == ending.skipped_message
    exits = [r for r in log.records() if r.kind == "exit"]
    assert [(r.scope_id, r.exited.timed_out) for r in exits] == [("a", True)]  # 推进进程到点停下的 a；b 从没启动
    # a 的终态点名它的那一份；b 由结束写结束，没有判定明细、终态不点名
    assert state.jobs["a"].result_id is not None and state.jobs["b"].result_id is None
    assert [p.name for p in (tmp_path / "run-1" / "jobs").iterdir()] == [f"{state.jobs['a'].result_id}.json"]
    [background] = reports.results
    assert _verdict(background) == (Status.ABORTED, ending.run_message,
                                    [("a", Status.ABORTED, None, (None, DEADLINE_TIMEOUT_MESSAGE)),
                                     ("b", Status.SKIPPED, ending.skipped_message, None)])

    execution = schedule(meta, _echo_resolver("silent"), lambda _event: None,
                         opts=ScheduleOpts(max_concurrency=1, grace_period_s=1.0, wall_clock=_FastClock(start, 60.0),
                                           heartbeat_interval_s=0.05))
    assert _verdict(_foreground_result(execution)) == _verdict(background)


def test_relay_after_the_advancer_is_gone_ends_an_expired_run_without_starting_jobs(tmp_path, monkeypatch):
    """推进进程已不在、过了期限之后的一次 `status --wait` 接力：经两者共用的入口推进，a 是原推进进程认领、观察链
    已断的 job，b 没有启动过。a 的预算让它自己的截止时刻还在半小时之后，截止时刻由期限（一小时之前）封顶，接力方按封顶后的时刻判，
    墙钟早已过了它加 10 秒，第一轮即补写超时，a 因此记 aborted、说明是期限那一句；b 不认领、不启动，由到期的结束写记 skipped；run
    状态按取法为 aborted、带到期说明，报告由接力方生成。组合根照真实装配，只把引擎换成记录启动的替身、停止宽限的查询换成固定值
    （误启动 job 时启动调用落到替身上、被记下）。"""
    from gherkai_runtime import compose, detached

    now = compose.now()
    meta = RunMeta(run_id="run-x", created_at=instant_to_iso(now - timedelta(hours=3)),
                   jobs=(_job("a", timeout_s=7200.0), _job("b", timeout_s=7200.0)),
                   deadline_at=instant_to_iso(now - timedelta(hours=1)))
    store = LocalRunStore(tmp_path)
    store.create_run(meta, RunState(run_id="run-x", status=Status.RUNNING,
                                    jobs={s: JobState(s, Status.PENDING) for s in ("a", "b")},
                                    started_at=meta.created_at, high_water_mark=0))
    assert store.try_claim_job("run-x", "a", claimed_at=instant_to_iso(now - timedelta(minutes=90))) is True
    log = SqliteEventLog(compose.events_db_path(str(tmp_path), "run-x"))
    log.append_event("a", 1, '{"type":"scope_started","scopeId":"a","sessionId":"echo-sess"}', 1.0)  # 原 worker 留下的

    spawned: list[str] = []

    class _Spy:
        def run_scope(self, job, **kw):
            spawned.append(job.scope_id)
            raise AssertionError("到期之后不应启动任何 job")

    monkeypatch.setenv("AWS_REGION", "us-test-9")
    monkeypatch.setattr(compose, "build_engines", lambda **kw: {"novaact": _Spy()})
    monkeypatch.setattr(compose, "engine_min_grace", lambda _engine: 5.0)
    relay = threading.Thread(target=detached.drive_local_reconcile, args=(str(tmp_path), "run-x", 1),
                             kwargs={"poll_interval_s": 0.01}, daemon=True)
    relay.start()
    relay.join(timeout=20)

    assert not relay.is_alive(), "接力没有结束"
    assert spawned == []
    ending = RUN_ENDINGS["deadline"]
    state = LocalRunStore(tmp_path).load_run_state("run-x")
    assert (state.status, state.message) == (Status.ABORTED, ending.run_message)
    assert (state.jobs["a"].status, state.jobs["b"].status) == (Status.ABORTED, Status.SKIPPED)
    assert state.jobs["b"].message == ending.skipped_message
    [exit_rec] = [r for r in log.records() if r.kind == "exit"]
    assert (exit_rec.scope_id, exit_rec.exited.exit_code, exit_rec.exited.timed_out) == ("a", None, True)
    assert (tmp_path / "run-x" / "manifest.json").exists() and (tmp_path / "run-x" / "index.html").exists()
    # a 的终态点名接力方存下的那一份；b 由结束写结束，没有判定明细、终态不点名
    result_id = state.jobs["a"].result_id
    assert result_id is not None and state.jobs["b"].result_id is None
    assert [p.name for p in (tmp_path / "run-x" / "jobs").iterdir()] == [f"{result_id}.json"]
    jr = LocalResultStore(tmp_path).load_job_result("run-x", result_id)
    assert (jr.status, jr.error_type, jr.message) == (Status.ABORTED, None, DEADLINE_TIMEOUT_MESSAGE)  # 起作用的是期限


class _RecordsExits:
    """代理真 EventLog：记下经它写的每条退出记录（接力方写没写、写了什么），其余原样转发。两个写入口都记：观察到的退出记为
    (scope_id, 退出码, 关键字参数)，补写的未知退出记为 (scope_id, "timed-out-if-absent", 是否写成)。"""

    def __init__(self, inner) -> None:
        self._inner, self.exits = inner, []

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def record_exit(self, scope_id, exit_code, **kw):
        self.exits.append((scope_id, exit_code, kw))
        return self._inner.record_exit(scope_id, exit_code, **kw)

    def record_timed_out_if_absent(self, scope_id):
        written = self._inner.record_timed_out_if_absent(scope_id)
        self.exits.append((scope_id, "timed-out-if-absent", written))
        return written


# ---------- 启动器记下退出时刻（ADR 0054 决策二后台推进条）、接力的判定条件与条件补写 ----------


class _SettableClock:
    """只在用例改它时才变的墙钟。"""

    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


class _ParkedChecks:
    """由用例掌握启动器检查线程的到点决定：第一次决定照常做，做完置 first_done；之后的每一次在进入决定之前停住、置 parked，等用例
    置 go 才做，做完置 later_done。decisions 依次记下每一次决定的结果（True 是到点、要停）。install 换掉启动器为每个 job 建的互斥
    对象，只换外面这一层，看到退出与到点决定本身照旧由被测的实现做。"""

    def __init__(self) -> None:
        self.first_done, self.parked, self.go, self.later_done = (threading.Event() for _ in range(4))
        self.decisions: list[bool] = []

    def install(self, monkeypatch) -> None:
        from gherkai_runtime import detached

        checks = self

        class _Probed(detached._ExitOrCutoff):
            def stop_due(self) -> bool:
                later = checks.first_done.is_set()
                if later:
                    checks.parked.set()
                    checks.go.wait(30)
                due = super().stop_due()
                checks.decisions.append(due)
                (checks.later_done if later else checks.first_done).set()
                return due

        monkeypatch.setattr(detached, "_ExitOrCutoff", _Probed)


def _by_thread(*, check, pump, other):
    """按读墙钟的线程返回时刻的墙钟：启动器给 job a 起的检查线程读 check()，推进线程（看到 a 退出时读退出时刻）读 pump()，
    其余（推进循环取认领时刻与收尾时刻）读 other。"""

    def clock() -> datetime:
        name = threading.current_thread().name
        if name == "cutoff-a":
            return check()
        if name == "launcher-a":
            return pump()
        return other

    return clock


def _run_in_thread(meta, log, store, launcher, clock, reports, tmp_path) -> threading.Thread:
    """在后台线程里推进 run-1 到结束（并发上限 1），报告记进 reports。"""
    loop = threading.Thread(target=run_reconcile_loop, args=("run-1", meta, log, store, launcher, 1), daemon=True,
                            kwargs={"poll_interval_s": 0.02, "clock": clock, "report_store": reports,
                                    "result_store": LocalResultStore(tmp_path)})
    loop.start()
    return loop


def test_worker_exiting_on_its_own_after_its_cutoff_gets_the_foreground_verdict(tmp_path, monkeypatch):
    """worker 在截止时刻之后、启动器下一次到点决定之前自己异常退出（真进程，实测项 11 的本机一侧）：启动器只记事实，退出记录不带超时
    标志、带它看到 worker 退出的那一刻；投影按退出时刻晚于截止时刻判为超时，判定、错误类型与说明和前台同一情形相同（前台在终结
    之前对内容不完整的 job 再查一次截止时刻）。先后由事件确立：检查线程的第一次到点决定做完（读到的是截止之前的时刻）之后才拨过截止
    时刻、建让 worker 崩溃的文件；此后的到点决定停在进入之前，直到推进结束才放行，所以 worker 退出之前没有第二次决定，退出码保持 worker
    自己的 3，超时只能来自投影对退出时刻的判断。"""
    from gherkai_core.model import ScenarioStarted
    from gherkai_core.schedule import ScheduleOpts, schedule

    start = datetime(2026, 7, 19, tzinfo=timezone.utc)
    past_cutoff = start + timedelta(seconds=61)  # 预算 60 秒，认领时刻即 start

    checks = _ParkedChecks()
    checks.install(monkeypatch)
    bg_gate = tmp_path / "bg-crash-now"
    monkeypatch.setenv("WORKER_CRASH_AFTER_FILE", str(bg_gate))
    bg_clock = _SettableClock(start)
    meta, log, store, launcher = _setup(tmp_path, "crash", "a", timeout_s=60.0, clock=bg_clock)
    reports = _CapturingReports()
    loop = _run_in_thread(meta, log, store, launcher, bg_clock, reports, tmp_path)
    try:
        assert checks.first_done.wait(10), "检查线程没有做第一次到点决定"
        assert checks.decisions == [False]  # 读到的是截止之前的时刻（worker 还在等那个文件，没有退出）
        bg_clock.now = past_cutoff
        bg_gate.touch()
        loop.join(timeout=20)
    finally:
        checks.go.set()
    assert not loop.is_alive(), "推进没有结束"
    [exit_rec] = [r for r in log.records() if r.kind == "exit"]
    assert (exit_rec.exited.exit_code, exit_rec.exited.timed_out, exit_rec.exited.exited_at) == (3, False, past_cutoff)
    [background] = reports.results

    fg_gate = tmp_path / "fg-crash-now"
    monkeypatch.setenv("WORKER_CRASH_AFTER_FILE", str(fg_gate))
    fg_clock, started, out = _SettableClock(start), threading.Event(), {}

    def sink(event) -> None:
        if isinstance(event, ScenarioStarted):
            started.set()

    def run_foreground() -> None:
        out["result"] = schedule(meta, _echo_resolver("crash"), sink,
                                 opts=ScheduleOpts(max_concurrency=1, grace_period_s=1.0, wall_clock=fg_clock,
                                                   heartbeat_interval_s=0.05))

    foreground = threading.Thread(target=run_foreground, daemon=True)
    foreground.start()
    assert started.wait(10)
    fg_clock.now = past_cutoff
    fg_gate.touch()
    foreground.join(timeout=20)
    assert not foreground.is_alive(), "前台没有结束"

    expected = (Status.ERROR, None, [("a", Status.ERROR, None, ("timeout", "job 超时（预算 60s，已中止）"))])
    assert _verdict(background) == expected
    assert _verdict(_foreground_result(out["result"])) == expected


def test_an_exit_seen_before_the_cutoff_decision_keeps_the_verdict_the_foreground_gives(tmp_path, monkeypatch):
    """看到 worker 退出与到点决定互斥，推进线程先看到退出的一种先后（ADR 0054 决策二后台推进条「截止时刻与说明」）。worker 在截止时刻
    之前自己以 3 退出；推进线程读到的退出时刻是截止前 1 秒，读完停在看到退出的中途；这时放行检查线程的下一次到点决定，它若读墙钟会
    读到截止后 1 秒。互斥时这次决定要等推进线程做完，随后看到已经退出，不再读墙钟、不置超时标志、不停止：退出记录是 (3, 不带标志,
    截止前 1 秒)，后台给这个 job 的状态、错误类型与说明与前台在截止时刻之前看到同样的退出时相同。不互斥时检查线程在这个间隔里置上
    标志，记录被判为超时。检查线程的第一次决定在 worker 退出之前做完（截止之前），第二次停在进入决定之前，由用例在推进线程停住之后
    放行，先后因此固定。"""
    from gherkai_core.schedule import ScheduleOpts, schedule

    start = datetime(2026, 7, 19, tzinfo=timezone.utc)
    cutoff = start + timedelta(seconds=60)  # 预算 60 秒，认领时刻即 start
    pump_paused, release_pump = threading.Event(), threading.Event()

    def pump_reads_exit_time() -> datetime:
        pump_paused.set()
        release_pump.wait(30)
        return cutoff - timedelta(seconds=1)

    clock = _by_thread(check=lambda: cutoff + timedelta(seconds=1) if pump_paused.is_set() else start,
                       pump=pump_reads_exit_time, other=start)
    checks = _ParkedChecks()
    checks.install(monkeypatch)
    gate = tmp_path / "crash-now"
    monkeypatch.setenv("WORKER_CRASH_AFTER_FILE", str(gate))
    meta, log, store, launcher = _setup(tmp_path, "crash", "a", timeout_s=60.0, clock=clock)
    reports = _CapturingReports()
    loop = _run_in_thread(meta, log, store, launcher, clock, reports, tmp_path)
    try:
        assert checks.parked.wait(10), "检查线程的第二次到点决定没有停住"
        gate.touch()  # worker 自己以 3 退出
        assert pump_paused.wait(10), "推进线程没有读退出时刻"
        checks.go.set()
        assert not checks.later_done.wait(0.5), "推进线程看到退出的中途，检查线程做成了到点决定"
    finally:
        release_pump.set()
        checks.go.set()
    loop.join(timeout=20)
    assert not loop.is_alive(), "推进没有结束"
    assert checks.later_done.wait(10)
    assert checks.decisions == [False, False]
    [exit_rec] = [r.exited for r in log.records() if r.kind == "exit"]
    assert (exit_rec.exit_code, exit_rec.timed_out, exit_rec.exited_at) == (3, False, cutoff - timedelta(seconds=1))
    [background] = reports.results
    assert [jr.error_type for jr in background.details] == ["engine_error"]

    execution = schedule(meta, _echo_resolver("crash"), lambda _event: None,  # 那个文件已在：worker 报出 scenario_started 即崩
                         opts=ScheduleOpts(max_concurrency=1, grace_period_s=1.0, wall_clock=lambda: start,
                                           heartbeat_interval_s=0.05))
    assert _verdict(_foreground_result(execution)) == _verdict(background)


def test_a_cutoff_decided_before_the_exit_marks_the_exit_as_timed_out(tmp_path, monkeypatch):
    """反过来的先后：检查线程先做到点决定（读到截止后 1 秒），置上超时标志、要发停止请求；停止请求挡在发出之前，worker 随后自己以 3
    退出，推进线程看到退出时读到截止后 2 秒。退出记录带超时标志、退出时刻是推进线程读的那一刻，判为超时。停止请求在互斥之外发：它被
    挡住期间推进线程照常看到退出、写下退出记录。"""
    start = datetime(2026, 7, 19, tzinfo=timezone.utc)
    cutoff = start + timedelta(seconds=60)  # 预算 60 秒，认领时刻即 start
    clock = _by_thread(check=lambda: cutoff + timedelta(seconds=1), pump=lambda: cutoff + timedelta(seconds=2),
                       other=start)
    stop_entered, release_stop = threading.Event(), threading.Event()
    real_engine = _echo_resolver("crash")("novaact")

    class _HeldStop:
        """worker 句柄的代理：停止请求先挡住，用例放行之后才发给 worker。"""

        def __init__(self, inner) -> None:
            self._inner = inner

        def wait(self, *args):
            return self._inner.wait(*args)

        def stop(self, grace_period_s):
            stop_entered.set()
            release_stop.wait(30)
            return self._inner.stop(grace_period_s)

    class _Engine:
        def run_scope(self, job, **kw):
            handle, events = real_engine.run_scope(job, **kw)
            return _HeldStop(handle), events

    gate = tmp_path / "crash-now"
    monkeypatch.setenv("WORKER_CRASH_AFTER_FILE", str(gate))
    meta, log, store, _ = _setup(tmp_path, "crash", "a", timeout_s=60.0, clock=clock)
    launcher = SubprocessLauncher(lambda _name: _Engine(), log, min_grace_fn=lambda _engine: 1.0, clock=clock)
    reports = _CapturingReports()
    loop = _run_in_thread(meta, log, store, launcher, clock, reports, tmp_path)
    try:
        assert stop_entered.wait(10), "检查线程没有决定停止"
        gate.touch()  # worker 自己以 3 退出，停止请求还没有发出
        _wait_until(lambda: any(r.kind == "exit" for r in log.records()))
    finally:
        release_stop.set()
    loop.join(timeout=20)
    assert not loop.is_alive(), "推进没有结束"
    [exit_rec] = [r.exited for r in log.records() if r.kind == "exit"]
    assert (exit_rec.exit_code, exit_rec.timed_out, exit_rec.exited_at) == (3, True, cutoff + timedelta(seconds=2))
    [background] = reports.results
    assert _verdict(background) == (Status.ERROR, None,
                                    [("a", Status.ERROR, None, ("timeout", "job 超时（预算 60s，已中止）"))])


def test_relay_keeps_a_real_exit_record_written_between_its_check_and_its_write(tmp_path):
    """补写不覆盖已观察到的退出：接力方点查过「还没有退出记录」之后、补写之前，原推进进程写下了 a 的真实
    退出记录与此前的事件（这里在点查返回之前写下）。补写是条件写、不成立，留下的是真实的那一条，a 保留完整的判定、run 按内容通过。
    墙钟早已过了 a 的截止时刻加 10 秒，第一轮即点查退出记录。"""
    meta, inner_log, store, launcher = _setup(tmp_path, "pass", "a", timeout_s=60.0, clock=_one_hour_later)
    assert store.try_claim_job("run-1", "a", claimed_at="2026-07-19T00:00:00+00:00") is True
    real_exit_at = datetime(2026, 7, 19, 0, 0, 30, tzinfo=timezone.utc)

    class _RealExitLandsAfterTheCheck(_RecordsExits):
        def has_exit(self, scope_id):
            seen = self._inner.has_exit(scope_id)
            if not seen:  # 原推进进程恰在这时写下 worker 的事件与它观察到的退出
                self._inner.append_event(scope_id, 1, '{"type":"scope_started","scopeId":"a","sessionId":"s"}', 1.0)
                self._inner.append_event(scope_id, 2, '{"type":"scenario_done","scenarioId":"a:0","status":"passed"}', 2.0)
                self._inner.append_event(scope_id, 3, '{"type":"scope_done","scopeId":"a"}', 3.0)
                self._inner.record_exit(scope_id, 0, exited_at=real_exit_at)
            return seen

    log = _RealExitLandsAfterTheCheck(inner_log)
    run_reconcile_loop("run-1", meta, log, _BoundedReads(store, limit=200), launcher, max_concurrency=1,
                       poll_interval_s=0.001, clock=_one_hour_later, result_store=LocalResultStore(tmp_path))

    assert log.exits == [("a", "timed-out-if-absent", False)]  # 补写确实发出了，只是没有写成
    [exit_rec] = [r.exited for r in inner_log.records() if r.kind == "exit"]
    assert (exit_rec.exit_code, exit_rec.timed_out, exit_rec.exited_at) == (0, False, real_exit_at)
    state = store.load_run_state("run-1")
    assert (state.status, state.jobs["a"].status) == (Status.PASSED, Status.PASSED)


def _foreign_claims(tmp_path, claims: dict[str, str | None], *, deadline_at: str = _FAR):
    """建一个 run，claims 里的每个 job 都由别的推进方认领（本进程的启动器没有起过它）、认领时刻取给定的值，都没有退出记录；预算
    60 秒。返回的事件库记下接力方经它写的每条退出记录。"""
    meta, log, store, launcher = _setup(tmp_path, "pass", *claims, timeout_s=60.0, deadline_at=deadline_at)
    for sid, claimed_at in claims.items():
        assert store.try_claim_job("run-1", sid, claimed_at=claimed_at) is True
    return meta, _RecordsExits(log), store, launcher


@pytest.mark.parametrize("deadline_at, cutoff", [
    (_FAR, datetime(2026, 7, 19, 0, 1, tzinfo=timezone.utc)),
    ("2026-07-19T00:00:30+00:00", datetime(2026, 7, 19, 0, 0, 30, tzinfo=timezone.utc)),
], ids=["budget", "capped-by-deadline"])
def test_relay_writes_only_once_the_wall_clock_is_strictly_past_the_cutoff_plus_ten_seconds(tmp_path, deadline_at, cutoff):
    """接力判超时的判定条件：墙钟严格晚于截止时刻加 10 秒、仍没有退出记录时才补写。截止时刻与认领方同一个算法：认领时刻加预算
    （60 秒），期限更早时以期限封顶、按封顶后的时刻判。恰在截止时刻、恰在截止时刻加 10 秒时都不写，再晚一微秒即写。"""
    from gherkai_runtime import detached

    meta, log, store, launcher = _foreign_claims(tmp_path, {"a": "2026-07-19T00:00:00+00:00"}, deadline_at=deadline_at)
    boundary = cutoff + timedelta(seconds=10)
    for now in (cutoff, boundary):
        detached._recover_timed_out_claims("run-1", meta, log, store, launcher.owned_scopes, now=now)
    assert log.exits == []
    detached._recover_timed_out_claims("run-1", meta, log, store, launcher.owned_scopes,
                                       now=boundary + timedelta(microseconds=1))
    assert log.exits == [("a", "timed-out-if-absent", True)]


def test_relay_leaves_its_own_jobs_and_jobs_without_a_readable_claim_time(tmp_path):
    """接力方不处置的两类执行中 job，墙钟都已远过截止时刻加 10 秒：本进程的启动器手里的 job（它的截止时刻检查在管），与认领时刻
    缺失、不是时刻或不带时区的 job（没有起算点）。同一轮里认领时刻正常的别人的 job 照常补写，说明这一轮确实判过。"""
    from gherkai_runtime import detached

    claimed = "2026-07-19T00:00:00+00:00"
    meta, log, store, launcher = _foreign_claims(tmp_path, {
        "own": claimed, "missing": None, "garbled": "认领时刻", "naive": "2026-07-19T00:00:00", "lost": claimed})
    launcher.owned_scopes.add("own")
    detached._recover_timed_out_claims("run-1", meta, log, store, launcher.owned_scopes, now=_one_hour_later())
    assert log.exits == [("lost", "timed-out-if-absent", True)]


# ---------- 接力在逐 job 写序下：补写的超时退出成为终态的那一轮、报告按点名读回各轮的明细 ----------


def test_a_relay_timed_out_exit_is_recorded_with_its_detail_and_a_later_real_exit_changes_neither(tmp_path):
    """接力补写的超时退出怎样成为终态：a 由已不在的推进进程认领、早已过了截止时刻加 10 秒，b 也由它认领、还没到截止时刻。第一轮
    接力方为 a 补写超时的退出记录；下一轮 tick 按这一轮的事件为 a 存下一份判定明细（预算到点：error 加 timeout），再以终态写记下它并
    点名这一份，b 仍在执行、run 仍未结束。a 的真实退出（退出码 0、内容完整、退出时刻在截止时刻之前，单看它会判为 passed）与 b 的结果
    在 a 的终态写落下之后才写进事件库：真实退出覆盖了退出记录，但 a 在运行态里已是终态，之后的轮次不再为它存明细、写终态，a 的点名与
    那一份明细都不变，存放处只多出 b 的一份；b 得出结果的那一轮使 run 成为终态，报告里两个 job 的明细都按运行态里点名的标识读回（ADR
    0030 决定三「点名」条）。全程只有推进循环一个线程，事件在 a 的终态写落下之后、tick 拿到这次写的结果之前写入，先后因此固定。"""
    meta, log, inner, launcher = _setup(tmp_path, "pass", "a", "b", timeout_s=60.0, clock=_one_hour_later)
    assert inner.try_claim_job("run-1", "a", claimed_at="2026-07-19T00:00:00+00:00") is True  # 截止 00:01:00，早已过
    assert inner.try_claim_job("run-1", "b", claimed_at="2026-07-19T00:59:30+00:00") is True  # 截止 01:00:30，还没到

    def finish(scope_id: str, exited_at: datetime) -> None:
        """原推进进程起的 worker 内容完整地结束、以退出码 0 退出。"""
        log.append_event(scope_id, 1, f'{{"type":"scope_started","scopeId":"{scope_id}","sessionId":"s-{scope_id}"}}', 1.0)
        log.append_event(scope_id, 2, f'{{"type":"scenario_done","scenarioId":"{scope_id}:0","status":"passed"}}', 2.0)
        log.append_event(scope_id, 3, f'{{"type":"scope_done","scopeId":"{scope_id}"}}', 3.0)
        log.record_exit(scope_id, 0, exited_at=exited_at)

    class _LateResults:
        """代理真 RunStore：记下每次终态写给出的 job 与结果、各 job 点名的标识；第一次终态写落下之后、把结果交回 tick 之前，写下 a 的
        真实退出与 b 的结果；其余原样转发。"""

        def __init__(self, inner) -> None:
            self._inner, self.commits, self.named = inner, [], {}

        def __getattr__(self, name):
            return getattr(self._inner, name)

        def commit_job_states(self, run_id, job_states, *, ended_at):
            outcome = self._inner.commit_job_states(run_id, job_states, ended_at=ended_at)
            self.commits.append(([js.scope_id for js in job_states], outcome))
            self.named.update({js.scope_id: js.result_id for js in job_states})
            if len(self.commits) == 1:
                # a 的退出时刻在它的截止时刻之前：这一条若被重新推演，a 会判为 passed；b 的退出时刻同样在它的截止时刻之前
                finish("a", datetime(2026, 7, 19, 0, 0, 30, tzinfo=timezone.utc))
                finish("b", _one_hour_later())
            return outcome

    store, reports = _LateResults(inner), _CapturingReports()
    run_reconcile_loop("run-1", meta, log, _BoundedReads(store, limit=50), launcher, max_concurrency=2,
                       poll_interval_s=0.001, clock=_one_hour_later,
                       result_store=LocalResultStore(tmp_path), report_store=reports)

    assert store.commits == [(["a"], CommitOutcome.OPEN), (["b"], CommitOutcome.ENDED_RUN)]
    [exit_a] = [r.exited for r in log.records() if r.kind == "exit" and r.scope_id == "a"]
    assert (exit_a.exit_code, exit_a.timed_out) == (0, False)  # 真实退出确实覆盖了补写的那一条
    state = inner.load_run_state("run-1")
    assert (state.status, state.jobs["a"].status, state.jobs["b"].status) == (Status.ERROR, Status.ERROR, Status.PASSED)
    # 运行态点名的就是两次终态写各自给出的标识；a 只存过一份，存放处共两份
    assert {sid: js.result_id for sid, js in state.jobs.items()} == store.named and None not in store.named.values()
    assert sorted(p.name for p in (tmp_path / "run-1" / "jobs").iterdir()) == sorted(
        f"{rid}.json" for rid in store.named.values())
    saved_a = LocalResultStore(tmp_path).load_job_result("run-1", state.jobs["a"].result_id)
    assert (saved_a.status, saved_a.error_type) == (Status.ERROR, "timeout")
    [result] = reports.results
    assert [(d.scope_id, d.status, d.error_type) for d in result.details] == [
        ("a", Status.ERROR, "timeout"), ("b", Status.PASSED, None)]


# ---------- 判定存储的装配与保存明细失败（ADR 0030 决定三「保存明细失败」条）----------


class _FlakySaves:
    """代理判定存储：前 fail_first 次保存抛 OSError（磁盘写不进），之后原样转交；saves 依次记下每次保存的 (scope_id, 标识, 成败)。
    读与探活原样转交。"""

    def __init__(self, inner, *, fail_first: int) -> None:
        self._inner, self._left, self.saves = inner, fail_first, []

    def save_job_result(self, run_id, result_id, job):
        if self._left > 0:
            self._left -= 1
            self.saves.append((job.scope_id, result_id, "failed"))
            raise OSError(28, "No space left on device")
        self._inner.save_job_result(run_id, result_id, job)
        self.saves.append((job.scope_id, result_id, "saved"))

    def load_job_result(self, run_id, result_id):
        return self._inner.load_job_result(run_id, result_id)

    def preflight(self) -> None:
        self._inner.preflight()


def test_build_local_reconcile_takes_the_result_store_from_the_single_local_entry(tmp_path, monkeypatch):
    """后台推进进程与 status --wait 接力的装配经 `compose.local_result_store` 取判定存储，与前台 run 的 `build_local_stores` 是同一个
    入口，保存失败的退避重试因此对两种推进器一致。换掉那个入口，这里拿到的就是换上的那一个、入参是 report_dir；不换时拿到的是带
    重试的那一种。"""
    from gherkai_core.adapters.result_store.retrying import RetryingResultStore
    from gherkai_runtime import compose
    from gherkai_runtime.detached import build_local_reconcile

    _seed_for_build(tmp_path, "run-rs", max_concurrency=1)
    built = build_local_reconcile(str(tmp_path), "run-rs", max_concurrency=1, region="us-east-1")
    assert isinstance(built[5], RetryingResultStore)
    seen: list = []
    sentinel = object()
    monkeypatch.setattr(compose, "local_result_store", lambda root: seen.append(root) or sentinel)
    assert build_local_reconcile(str(tmp_path), "run-rs", max_concurrency=1, region="us-east-1")[5] is sentinel
    assert seen == [tmp_path]


def test_a_failed_save_is_retried_with_the_same_id_and_the_terminal_state_names_it(tmp_path):
    """后台推进保存判定明细失败一次：判定存储等 1 秒之后再保存，两次用同一个标识；存成之后照常写下终态并点名这个标识，run 照常通过，
    报告附上的就是这一份，推进循环不抛。判定存储照组合根的形态装配（本机文件存储外面套保存重试），等待换成记录。"""
    from gherkai_core.adapters.result_store.retrying import RetryingResultStore

    meta, log, store, launcher = _setup(tmp_path, "pass", "a")
    flaky, sleeps, reports = _FlakySaves(LocalResultStore(tmp_path), fail_first=1), [], _CapturingReports()
    run_reconcile_loop("run-1", meta, log, store, launcher, max_concurrency=1, poll_interval_s=0.05, clock=_now,
                       result_store=RetryingResultStore(flaky, sleep=sleeps.append), report_store=reports)

    assert [(sid, outcome) for sid, _rid, outcome in flaky.saves] == [("a", "failed"), ("a", "saved")]
    first_id, second_id = (rid for _sid, rid, _outcome in flaky.saves)
    assert first_id == second_id and sleeps == [1.0]
    state = store.load_run_state("run-1")
    assert (state.status, state.jobs["a"].status, state.jobs["a"].result_id) == (Status.PASSED, Status.PASSED, first_id)
    [result] = reports.results
    assert list(result.details) == [LocalResultStore(tmp_path).load_job_result("run-1", first_id)]


def test_drive_local_reconcile_stops_without_tearing_down_the_tunnel_when_saves_keep_failing(tmp_path, monkeypatch):
    """保存判定明细一直失败（磁盘写不进）：重试 3 次（间隔 1、2、4 秒，四次都用同一个标识）之后 OSError 原样穿出推进的唯一入口，说明
    与退出码由调用方给出；这个 job 不写终态、在记录里仍为 running、不点名，run 没有结束，不生成报告，也不拆隧道（随后用 status --wait
    接着推进的一方还要用它）。组合根照真实装配，只把引擎换成 echo_worker、把判定存储的装配入口换成「一直失败的本机文件存储外面套
    等待换成记录的重试」，桩掉「真杀 pid」这一 OS 边界。"""
    from gherkai_core.adapters.result_store.retrying import RetryingResultStore
    from gherkai_core.model import TERMINAL_STATUSES
    from gherkai_runtime import compose, detached
    from gherkai_runtime import tunnel as gtunnel

    _seed_for_build(tmp_path, "run-f", max_concurrency=1)
    (tmp_path / "run-f" / "tunnel.json").write_text('{"pid": 4545}', encoding="utf-8")
    monkeypatch.setenv("AWS_REGION", "us-test-9")
    env = {**os.environ, "WORKER_MODE": "pass"}
    monkeypatch.setattr(compose, "build_engines",
                        lambda **kw: {"novaact": SubprocessEngine(cmd=[sys.executable, _ECHO], env=env)})
    stopped: list[int] = []
    monkeypatch.setattr(gtunnel, "stop_tunnel", lambda pid: stopped.append(pid))
    stores: list[_FlakySaves] = []
    sleeps: list[float] = []

    def _always_failing(root):
        stores.append(_FlakySaves(LocalResultStore(root), fail_first=1_000))
        return RetryingResultStore(stores[-1], sleep=sleeps.append)

    monkeypatch.setattr(compose, "local_result_store", _always_failing)

    with pytest.raises(OSError, match="No space left on device"):
        detached.drive_local_reconcile(str(tmp_path), "run-f", 1, region=None, profile=None, poll_interval_s=0.01)

    [flaky] = stores
    assert [outcome for _sid, _rid, outcome in flaky.saves] == ["failed"] * 4
    assert len({rid for _sid, rid, _outcome in flaky.saves}) == 1 and sleeps == [1.0, 2.0, 4.0]
    state = LocalRunStore(tmp_path).load_run_state("run-f")
    assert state.status not in TERMINAL_STATUSES and state.ended_at is None
    assert (state.jobs["a"].status, state.jobs["a"].result_id) == (Status.RUNNING, None)
    assert not (tmp_path / "run-f" / "index.html").exists() and not (tmp_path / "run-f" / "manifest.json").exists()
    assert stopped == [] and (tmp_path / "run-f" / "tunnel.json").exists()


# ---------- 本机后台推进进程读不到可用的运行定义（与云端推进器同一种结束写）----------


def test_end_run_for_unusable_definition_ends_every_unfinished_job_with_the_reason(tmp_path):
    """读不到可用的运行定义时的结束写（ADR 0031 决定三「结束写」小节「运行定义不可用时」条）：执行中与没有启动的 job 都记 error、
    说明是给出的原因，认领时刻保留，已结束的 job 不变；run 随之为 error，带同一句 run 级说明与结束时刻。run 已结束、运行态不存在时都
    没有写成，运行态不变。"""
    from gherkai_core.run_status import DEFINITION_CONTRACT_REASON
    from gherkai_runtime import detached

    _meta, _log, store, _launcher = _setup(tmp_path, "pass", "a", "b", "c")
    claimed = "2026-07-19T00:00:00+00:00"
    assert store.try_claim_job("run-1", "a", claimed_at=claimed) is True
    assert store.try_claim_job("run-1", "c", claimed_at=claimed) is True
    assert store.commit_job_states("run-1", [JobState("c", Status.PASSED)], ended_at=claimed) == CommitOutcome.OPEN

    reason = DEFINITION_CONTRACT_REASON
    assert detached.end_run_for_unusable_definition(str(tmp_path), "run-1", reason) is True
    state = store.load_run_state("run-1")
    assert (state.status, state.message) == (Status.ERROR, reason)
    assert {sid: (js.status, js.message) for sid, js in state.jobs.items()} == {
        "a": (Status.ERROR, reason), "b": (Status.ERROR, reason), "c": (Status.PASSED, None)}
    assert state.jobs["a"].claimed_at == claimed
    instant_from_iso(state.ended_at)  # 记录写法的时刻，解析不了即抛

    assert detached.end_run_for_unusable_definition(str(tmp_path), "run-1", "另一句") is False
    assert store.load_run_state("run-1") == state
    assert detached.end_run_for_unusable_definition(str(tmp_path), "no-such-run", reason) is False
