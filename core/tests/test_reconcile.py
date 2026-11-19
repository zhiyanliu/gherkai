"""reconciler tick 测试：推进编排 + 幂等 + CAS 起 job + 逐 job 写序 + 到期处理。

用真 SqliteEventLog + RunStore（LocalRunStore，部分用例另以 moto 上的 DynamoDBRunStore 对拍）+ fake Launcher（记录被 launch 的 job，
不起真进程）与注入的假墙钟验证 tick 逻辑：
- 首 tick 从全 pending 起首批（≤max_concurrency），每次认领前另取一次时刻作认领时刻，截止时刻随 launch 交出；
- 逐 job 写序（ADR 0030 决定三、ADR 0034 机制三「run 级状态只进不退」条④的步骤）：每一轮为已有结果的 job 先存判定明细、再以一次
  终态写记下它们的终态，run 的状态随之写下；投影只前进、不越过 running；推进决策在这一轮读到的运行态加上终态写的作用上作出，同一轮
  就能腾出并发位、判出「没有执行中的 job」；
- 按 job 判断快照：在这一轮读到的运行态里不带认领时刻的 job 这一轮不写，别的 job 照写；
- 幂等：重复 tick 不重复 launch（CAS 挡）；
- 已过停止启动的时刻：不认领；没有执行中的 job、仍有未启动的就做到期的结束写，写下时有 running 的 job 即写不成；
- 同一轮里认领因已过停止启动而没做时重新决策一次；
- 结果三种（TickOutcome）：继续推进 / 这一方的写使 run 成为终态（带这一次 tick 交给终态写的明细）/ run 已结束而使它成为终态的不是
  这一方（不带明细）；报告由宿主经 `write_report_from_record` 从记录生成，较早轮次的明细从判定存储读回。
并发与先后类的性质用固定先后构造：在读与写之间经包装的 RunStore 或事件日志插入另一方的动作。
纯编排逻辑（launch 被 fake、时钟被注入）→ 绿即够；真进程脱离 / SQLite 并发是真实运行边界。
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from gherkai_core.adapters.event_log import SqliteEventLog
from gherkai_core.adapters.result_store.local import LocalResultStore
from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step
from gherkai_core.project import DEADLINE_TIMEOUT_MESSAGE
from gherkai_core.reconcile import TickOutcome, TickResult, tick, write_report_from_record
from gherkai_core.run_status import RUN_ENDINGS, CommitOutcome
from gherkai_core.serialize import instant_to_iso
from tests.fake_engine import FAR_DEADLINE

T0 = datetime(2030, 1, 1, tzinfo=timezone.utc)  # 假墙钟的零点（远早于 FAR_DEADLINE）


def _at(seconds: float) -> datetime:
    return T0 + timedelta(seconds=seconds)


def _iso(seconds: float) -> str:
    return instant_to_iso(_at(seconds))


class Clock:
    """假墙钟：依次返回给定的时刻（秒，相对 T0），用完之后停在最后一个；记下读取次数。"""

    def __init__(self, *seconds: float) -> None:
        self._seq = list(seconds) or [0.0]
        self.reads = 0

    def set(self, *seconds: float) -> None:
        self._seq = list(seconds)

    def __call__(self) -> datetime:
        self.reads += 1
        s = self._seq.pop(0) if len(self._seq) > 1 else self._seq[0]
        return _at(s)


class FakeLauncher:
    def __init__(self) -> None:
        self.launched: list[str] = []
        self.cutoff_at: dict[str, datetime] = {}

    def launch(self, job: Job, *, cutoff_at: datetime) -> None:
        self.launched.append(job.scope_id)
        self.cutoff_at[job.scope_id] = cutoff_at


def _job(sid: str) -> Job:
    return Job(scope_id=sid, scope_name=sid, engine="novaact",
               scenarios=(Scenario(id=f"{sid}:1", name="s", steps=(Step(0, "Given", "x"),)),), timeout_s=300.0)


def _meta(*sids: str, deadline_at: str = FAR_DEADLINE) -> RunMeta:
    return RunMeta(run_id="run-1", created_at="t0", jobs=tuple(_job(s) for s in sids), deadline_at=deadline_at)


# 期限在 T0 之后 100 秒：停止启动的时刻是 T0+40
_NEAR = instant_to_iso(_at(100))
_DEADLINE_ENDING = RUN_ENDINGS["deadline"]  # 到期的结束写：run 级说明与没有启动的 job 的说明


def _initial(*sids: str) -> RunState:
    return RunState(run_id="run-1", status=Status.PENDING, jobs={s: JobState(s, Status.PENDING) for s in sids},
                    started_at=_iso(0), high_water_mark=0)


def _setup(tmp_path, *sids: str, deadline_at: str = FAR_DEADLINE, store=None):
    meta = _meta(*sids, deadline_at=deadline_at)
    log = SqliteEventLog(tmp_path / "e.db")
    store = store if store is not None else LocalRunStore(tmp_path)
    store.create_run(meta, _initial(*sids))
    return meta, log, store


def _done_events(log, sid, base=1, exit_code=0):
    """给某 scope 落「运行完成 passed + 退出」的完整事件序列。"""
    log.append_event(sid, base, f'{{"type":"scope_started","scopeId":"{sid}","sessionId":"s"}}', 1.0)
    log.append_event(sid, base + 1, f'{{"type":"scenario_done","scenarioId":"{sid}:1","status":"passed"}}', 2.0)
    log.append_event(sid, base + 2, f'{{"type":"scope_done","scopeId":"{sid}"}}', 3.0)
    log.record_exit(sid, exit_code)


class _Store:
    """把一个 RunStore 包一层：记下 tick 发出的写（投影、认领、终态写、结束写）与每次终态写给出的 job，并可在某个入口被调用之前或
    之后插入另一方的动作（各只插一次），用来固定读与写之间的先后。插入的动作直接用里面那个 store，不计入记录。"""

    def __init__(self, inner) -> None:
        self.inner = inner
        self.writes: list[str] = []
        self.commits: list[tuple[tuple[str, Status], ...]] = []
        self.before: dict[str, Callable[[], None]] = {}
        self.after: dict[str, Callable[[], None]] = {}

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def _call(self, name: str, *args, **kwargs):
        hook = self.before.pop(name, None)
        if hook is not None:
            hook()
        result = getattr(self.inner, name)(*args, **kwargs)
        hook = self.after.pop(name, None)
        if hook is not None:
            hook()
        return result

    def clear(self) -> None:
        self.writes.clear()
        self.commits.clear()

    def load_run_state(self, run_id):
        return self._call("load_run_state", run_id)

    def project_state(self, run_id, state):
        self.writes.append("project_state")
        return self._call("project_state", run_id, state)

    def try_claim_job(self, run_id, scope_id, *, claimed_at=None):
        self.writes.append("try_claim_job")
        return self._call("try_claim_job", run_id, scope_id, claimed_at=claimed_at)

    def commit_job_states(self, run_id, job_states, *, ended_at):
        self.writes.append("commit_job_states")
        self.commits.append(tuple((js.scope_id, js.status) for js in job_states))
        return self._call("commit_job_states", run_id, job_states, ended_at=ended_at)

    def end_run(self, run_id, ending, *, ended_at):
        self.writes.append("end_run")
        return self._call("end_run", run_id, ending, ended_at=ended_at)


@pytest.fixture(params=["local", "ddb"])
def any_store(request, tmp_path):
    """两个 RunStore adapter 各来一遍（对拍），外面包一层 `_Store`：本机用 tmp_path，云端用 moto 建好的表。"""
    if request.param == "local":
        return _Store(LocalRunStore(tmp_path))
    return _Store(request.getfixturevalue("ddb_run_store"))


def test_first_tick_starts_up_to_concurrency(tmp_path):
    meta, log, store = _setup(tmp_path, "a", "b", "c")
    launcher = FakeLauncher()
    done = tick("run-1", meta, log, store, launcher, max_concurrency=2, clock=Clock())
    assert done == TickResult(TickOutcome.CONTINUE)
    assert len(launcher.launched) == 2  # 起首批 2 个
    # 被 claim 的两个在 RunStore 里是 running
    state = store.load_run_state("run-1")
    running = [s for s, js in state.jobs.items() if js.status == Status.RUNNING]
    assert len(running) == 2


def test_each_claim_takes_its_own_time_and_launch_receives_the_cutoff(tmp_path):
    """每次认领之前另取一次时刻作认领时刻（ADR 0054 决策二后台推进条「时刻」）：靠后的认领不沿用轮首的时刻。写进运行态的认领时刻
    与算截止时刻的是同一个值；截止时刻是认领时刻加预算，随 launch 交出。"""
    meta, log, store = _setup(tmp_path, "a", "b")
    launcher = FakeLauncher()
    tick("run-1", meta, log, store, launcher, max_concurrency=2, clock=Clock(0, 1, 7))
    state = store.load_run_state("run-1")
    assert (state.jobs["a"].claimed_at, state.jobs["b"].claimed_at) == (_iso(1), _iso(7))
    assert launcher.cutoff_at == {"a": _at(301), "b": _at(307)}


def test_cutoff_is_capped_by_the_run_deadline(tmp_path):
    """截止时刻以运行期限封顶（ADR 0054 决策二第 2 条）：认领时刻加预算晚于期限时，交给 launch 的是期限本身。"""
    meta, log, store = _setup(tmp_path, "a", deadline_at=_NEAR)
    launcher = FakeLauncher()
    tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(0, 1))
    assert launcher.cutoff_at == {"a": _at(100)}


def test_tick_idempotent_no_double_launch(tmp_path):
    """重复 tick 不重复 launch（CAS 挡已 running，机制四）。"""
    meta, log, store = _setup(tmp_path, "a", "b")
    launcher = FakeLauncher()
    tick("run-1", meta, log, store, launcher, max_concurrency=2, clock=Clock())
    n1 = len(launcher.launched)
    tick("run-1", meta, log, store, launcher, max_concurrency=2, clock=Clock())  # 再 tick
    assert len(launcher.launched) == n1  # 没多起（a/b 已 running）


def test_tick_starts_next_after_completion(tmp_path):
    """一个 job 完成（两件都要齐）后，同一轮先记下它的终态，再用腾出的并发位起下一个 pending。"""
    meta, log, store = _setup(tmp_path, "a", "b", "c")
    launcher = FakeLauncher()
    tick("run-1", meta, log, store, launcher, max_concurrency=2, clock=Clock())  # 起 a,b
    _done_events(log, "a")
    tick("run-1", meta, log, store, launcher, max_concurrency=2, clock=Clock(10))
    assert "c" in launcher.launched  # a 完成腾位 → c 被起
    assert store.load_run_state("run-1").jobs["a"].status == Status.PASSED


def test_tick_commits_when_all_done(tmp_path):
    """全部 job 两件都要齐 → 这一方的终态写使 run 成为终态：返回 COMMITTED 且带这一次 tick 交给终态写的判定明细，run 的状态按取法
    写下，ended_at 是这一轮读运行态之前取的时刻。"""
    meta, log, store = _setup(tmp_path, "a")
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock())  # 起 a
    _done_events(log, "a")
    done = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(20))
    assert done.outcome is TickOutcome.COMMITTED
    assert [(jr.scope_id, jr.status) for jr in done.details] == [("a", Status.PASSED)]
    state = store.load_run_state("run-1")
    assert (state.status, state.ended_at, state.message) == (Status.PASSED, _iso(20), None)


def test_tick_nonzero_exit_commits_error(tmp_path):
    """job 非0退出（机制二）→ 该 job error → run 按取法为 error。"""
    meta, log, store = _setup(tmp_path, "a")
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock())
    _done_events(log, "a", exit_code=1)  # 内容 passed 但进程非干净退出
    done = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(20))
    assert done.outcome is TickOutcome.COMMITTED
    assert store.load_run_state("run-1").status == Status.ERROR


def test_tick_after_commit_reads_existing_terminal(tmp_path):
    """run 成为终态之后再 tick：读到既有终态即停（ADR 0034 机制三「run 级状态只进不退」条④），终态只写一次（ended_at 仍首次）。

    两次结果都让宿主结束推进：首次是这一方的写使 run 成为终态（宿主写报告），第二次是 run 已结束（宿主不写报告）——
    status --wait 的接力不会因「别人已使 run 成为终态」永远等不到结束（据 status --wait 死循环的实际运行复现修正）。"""
    meta, log, store = _setup(tmp_path, "a")
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock())
    _done_events(log, "a")
    d1 = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(20))
    d2 = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(30))
    assert d1.outcome is TickOutcome.COMMITTED and d2 == TickResult(TickOutcome.ENDED)
    assert store.load_run_state("run-1").ended_at == _iso(20)  # 终态只写一次（首次的时刻，未被第二次覆盖）


class _SpyRunStore(LocalRunStore):
    """真 LocalRunStore，另记下 tick 发出的写（投影、认领、终态写、结束写）。"""

    def __init__(self, root) -> None:
        super().__init__(root)
        self.writes: list[str] = []

    def project_state(self, run_id, state):
        self.writes.append("project_state")
        return super().project_state(run_id, state)

    def try_claim_job(self, run_id, scope_id, *, claimed_at=None):
        self.writes.append("try_claim_job")
        return super().try_claim_job(run_id, scope_id, claimed_at=claimed_at)

    def commit_job_states(self, run_id, job_states, *, ended_at):
        self.writes.append("commit_job_states")
        return super().commit_job_states(run_id, job_states, ended_at=ended_at)

    def end_run(self, run_id, ending, *, ended_at):
        self.writes.append("end_run")
        return super().end_run(run_id, ending, ended_at=ended_at)


class _CountingEventLog(SqliteEventLog):
    def __init__(self, path) -> None:
        super().__init__(path)
        self.record_reads = 0

    def records(self):
        self.record_reads += 1
        return super().records()


def test_tick_on_an_ended_run_reads_existing_terminal(tmp_path):
    """库中 run 已结束（这里是处置的结束写，两个 job 都没有启动、记 skipped）：tick 返回 ENDED，
    不读事件、不投影、不认领、不启动、不落判定真值（ADR 0034 机制三「run 级状态只进不退」条④）。

    不判停时，这一轮照常读事件、发出投影写，再提议启动（被认领条件挡下）。"""
    meta = _meta("a", "b")
    log = _CountingEventLog(tmp_path / "e.db")
    store = _SpyRunStore(tmp_path)
    store.create_run(meta, _initial("a", "b"))
    assert store.end_run("run-1", RUN_ENDINGS["settle-advancer-exited"], ended_at="t1") is True
    store.writes.clear()
    _done_events(log, "a")  # 库里有事件也不读
    before = store.load_run_state("run-1")
    launcher, rs = FakeLauncher(), _RecordingResultStore([])

    outcome = tick("run-1", meta, log, store, launcher, max_concurrency=2, clock=Clock(), result_store=rs)

    assert outcome == TickResult(TickOutcome.ENDED)
    assert launcher.launched == [] and rs.saved == []
    assert store.writes == [] and log.record_reads == 0
    assert store.load_run_state("run-1") == before


def test_commit_lost_to_another_advancer_ends_without_a_result(tmp_path):
    """终态写写不成（并发推进器在本轮读 baseline 之后先使 run 成为终态）：终态写报告 run 在这次写之前已是终态，返回 ENDED、不带明细、
    不另读，宿主不生成报告；判定真值照落（写序不变）；库中终态是先写成的那一份（ADR 0034 机制三「run 级状态只进不退」条④第 6 步
    与同条 K2）。"""

    class _LosesCommit(LocalRunStore):
        def __init__(self, root) -> None:
            super().__init__(root)
            self.results: list[CommitOutcome] = []

        def commit_job_states(self, run_id, job_states, *, ended_at):
            super().commit_job_states(run_id, job_states, ended_at="other")  # 另一推进器先写成
            self.results.append(super().commit_job_states(run_id, job_states, ended_at=ended_at))
            return self.results[-1]

    meta, log, store = _setup(tmp_path, "a", store=_LosesCommit(tmp_path))
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock())
    _done_events(log, "a")
    rs = _RecordingResultStore([])

    outcome = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(20), result_store=rs)

    assert outcome == TickResult(TickOutcome.ENDED)
    assert store.results == [CommitOutcome.ALREADY_ENDED]  # 本实例确实写输
    assert [jr.scope_id for jr in rs.saved] == ["a"]
    state = store.load_run_state("run-1")
    assert state.status == Status.PASSED and state.ended_at == "other"


def test_commit_finding_the_run_ended_elsewhere_stops_without_claiming(any_store, tmp_path):
    """终态写返回 ALREADY_ENDED（读运行态之后、终态写之前，别处以结束写结束了 run）：返回 ENDED，之后不认领、不启动，也不另读；
    明细在终态写之前已存下（写序不变）。仍有 pending 的 job 也不再提议启动。"""
    meta, log, store = _setup(tmp_path, "a", "b", store=any_store)
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(0, 1))  # 起 a
    _done_events(log, "a")
    store.clear()
    store.before["commit_job_states"] = lambda: store.inner.end_run(
        "run-1", RUN_ENDINGS["settle-advancer-exited"], ended_at="other")
    launcher, rs = FakeLauncher(), _RecordingResultStore([])

    outcome = tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(10), result_store=rs)

    assert outcome == TickResult(TickOutcome.ENDED)
    assert store.writes == ["project_state", "commit_job_states"]  # 没有认领
    assert launcher.launched == [] and [jr.scope_id for jr in rs.saved] == ["a"]
    state = store.load_run_state("run-1")
    assert (state.status, state.ended_at, state.jobs["a"].status, state.jobs["b"].status) == (
        Status.ABORTED, "other", Status.ABORTED, Status.SKIPPED)


def test_ending_inserted_after_baseline_read_continues_then_stops(tmp_path):
    """结束写插在本轮读 baseline 之后：本轮不在判停之内，投影写被终态守卫挡下、认领被条件挡下，返回 CONTINUE；
    下一轮读到终态即停（ADR 0034 机制三「run 级状态只进不退」条④末句）。"""

    class _EndedRightAfterRead(LocalRunStore):
        armed = False

        def load_run_state(self, run_id):
            state = super().load_run_state(run_id)
            if self.armed:
                self.armed = False
                assert self.end_run(run_id, RUN_ENDINGS["settle-advancer-exited"], ended_at="other") is True
            return state

    meta, log, store = _setup(tmp_path, "a", store=_EndedRightAfterRead(tmp_path))
    launcher = FakeLauncher()
    store.armed = True

    assert tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock()).outcome is TickOutcome.CONTINUE
    assert launcher.launched == []  # 认领被「run 未结束」条件挡下
    assert tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock()).outcome is TickOutcome.ENDED
    state = store.load_run_state("run-1")
    assert (state.status, state.ended_at, state.jobs["a"].status) == (Status.ABORTED, "other", Status.SKIPPED)


# ---------- launch 失败补偿（ADR 0034 机制二推论、ADR 0054 决策二后台推进条「时刻」）----------

class BoomLauncher:
    """launch 必抛的 fake（RunTask 放置失败/task-def 配错/Popen OSError 的抽象）；可在抛出前推进假墙钟（启动调用拖过截止时刻）。"""

    def __init__(self, clock: Clock | None = None, then: float | None = None) -> None:
        self.attempts: list[str] = []
        self._clock, self._then = clock, then

    def launch(self, job: Job, *, cutoff_at: datetime) -> None:
        self.attempts.append(job.scope_id)
        if self._clock is not None and self._then is not None:
            self._clock.set(self._then)
        raise RuntimeError(f"boom: {job.scope_id}")


def _claimed(store) -> dict[str, datetime]:
    from gherkai_core.serialize import instant_from_iso
    return {sid: instant_from_iso(js.claimed_at) for sid, js in store.load_run_state("run-1").jobs.items() if js.claimed_at}


def test_launch_failure_does_not_wedge_run(tmp_path):
    """launch 抛异常 → 补偿记退出 → 下轮判 ERROR 收敛，run 不 wedge（ADR 0034 机制二推论）。"""
    meta, log, store = _setup(tmp_path, "a", "b")
    boom = BoomLauncher()
    # tick1：两个 job 都被 claim、launch 都抛异常——异常不向外抛出、补偿落 task_exited
    assert tick("run-1", meta, log, store, boom, max_concurrency=2, clock=Clock()).outcome is TickOutcome.CONTINUE
    assert boom.attempts == ["a", "b"]  # 第一个失败不拖垮第二个（失败隔离）
    # tick2：重放看到退出码未知 → 两 job ERROR → 一次终态写记下两者，run 随之成为终态
    assert tick("run-1", meta, log, store, boom, max_concurrency=2, clock=Clock(5)).outcome is TickOutcome.COMMITTED
    state = store.load_run_state("run-1")
    assert state.status == Status.ERROR
    assert all(js.status == Status.ERROR for js in state.jobs.values())
    assert boom.attempts == ["a", "b"]  # 不重复 launch（已 ERROR、plan_next 不再提议）


def test_launch_failure_records_unknown_exit_with_the_same_reason_as_the_foreground(tmp_path):
    """launch 抛错的补偿与前台起 worker 失败交给终结函数的输入相同：退出码未知、原因是「起 worker 失败：异常文本」，不再用平台哨兵
    退出码；退出时刻是失败时取的那一刻（截止时刻之前），不带超时标志；job 的说明就是这句原因，与前台逐字相同。"""
    from gherkai_core.project import project_full

    meta, log, store = _setup(tmp_path, "a")
    tick("run-1", meta, log, store, BoomLauncher(), max_concurrency=1, clock=Clock())
    (exit_rec,) = [r.exited for r in log.records() if r.kind == "exit"]
    assert (exit_rec.exit_code, exit_rec.timed_out, exit_rec.reason) == (None, False, "起 worker 失败：boom: a")
    assert exit_rec.exited_at == _at(0)
    (jr,) = project_full(meta, log.records(), claimed_at=_claimed(store))
    assert (jr.status, jr.error_type, jr.message) == (Status.ERROR, "engine_error", "起 worker 失败：boom: a")


@pytest.mark.parametrize("deadline_at, expected", [
    (FAR_DEADLINE, (Status.ERROR, "timeout", "job 超时（预算 300s，已中止）")),
    (_NEAR, (Status.ABORTED, None, DEADLINE_TIMEOUT_MESSAGE)),
])
def test_launch_failure_after_the_cutoff_projects_as_timeout(tmp_path, deadline_at, expected):
    """启动调用失败时再取一次时刻，记为退出时刻：补偿只记这个事实、不带超时标志，投影时它晚于这个 job 的截止时刻即按到点处理，与前台
    起 worker 失败的分支得到同一个判定；按起作用的那个截止时刻记：预算是 error 加 timeout，期限是 aborted（ADR 0031 决定一）。"""
    from gherkai_core.project import project_full

    meta, log, store = _setup(tmp_path, "a", deadline_at=deadline_at)
    clock = Clock(0, 1)
    tick("run-1", meta, log, store, BoomLauncher(clock, then=1000), max_concurrency=1, clock=clock)
    (exit_rec,) = [r.exited for r in log.records() if r.kind == "exit"]
    assert (exit_rec.exit_code, exit_rec.timed_out, exit_rec.exited_at) == (None, False, _at(1000))
    (jr,) = project_full(meta, log.records(), claimed_at=_claimed(store))
    assert (jr.status, jr.error_type, jr.message) == expected


def test_launch_failure_isolated_other_job_completes(tmp_path):
    """一个 job 起不来，另一个照常运行完成——失败隔离 + 聚合 ERROR。"""

    class HalfBoom:
        def __init__(self) -> None:
            self.launched: list[str] = []

        def launch(self, job: Job, *, cutoff_at: datetime) -> None:
            if job.scope_id == "a":
                raise RuntimeError("boom: a")
            self.launched.append(job.scope_id)

    meta, log, store = _setup(tmp_path, "a", "b")
    hb = HalfBoom()
    tick("run-1", meta, log, store, hb, max_concurrency=2, clock=Clock())
    assert hb.launched == ["b"]  # b 照常起
    _done_events(log, "b")  # b 运行完成 passed
    assert tick("run-1", meta, log, store, hb, max_concurrency=2, clock=Clock(5)).outcome is TickOutcome.COMMITTED
    state = store.load_run_state("run-1")
    assert state.jobs["a"].status == Status.ERROR
    assert state.jobs["b"].status == Status.PASSED
    assert state.status == Status.ERROR  # 任一 error → run error（ADR 0031 决定三）


# ---------- 逐 job 写序：判定明细先存、终态写后写，推进决策在终态写之后（ADR 0030 决定三「后台推进同守」条，
# ADR 0034 机制三「run 级状态只进不退」条④的步骤）----------

class _RecordingResultStore:
    def __init__(self, seq: list, fail: bool = False) -> None:
        self.seq, self.fail, self.saved = seq, fail, []

    def save_job_result(self, run_id, jr):
        if self.fail:
            raise OSError("S3 不可达")
        self.seq.append(("verdict", jr.scope_id, jr.status))
        self.saved.append(jr)


class _OrderRecordingRunStore(LocalRunStore):
    def __init__(self, root, seq: list) -> None:
        super().__init__(root)
        self.seq = seq

    def commit_job_states(self, run_id, job_states, *, ended_at):
        self.seq.append(("commit", tuple((js.scope_id, js.status) for js in job_states)))
        return super().commit_job_states(run_id, job_states, ended_at=ended_at)


def test_verdicts_are_saved_before_the_terminal_write(tmp_path):
    """同一轮两个 job 都有结果：ResultStore 各 job 判定明细**先**落，再一次终态写记下这一轮的全部终态（ADR 0030 决定三「后台推进同守」
    条）——看到终态即保证 jobs/*.json 已齐；反序在 detached 下崩在中间就是永久缺失（无人重试）。"""
    seq: list = []
    meta, log, store = _setup(tmp_path, "a", "b", store=_OrderRecordingRunStore(tmp_path, seq))
    rs = _RecordingResultStore(seq)
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(), result_store=rs)
    _done_events(log, "a"); _done_events(log, "b", base=10)
    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(5),
                result_store=rs).outcome is TickOutcome.COMMITTED
    kinds = [x[0] for x in seq]
    assert kinds == ["verdict", "verdict", "commit"], seq
    assert seq[-1][1] == (("a", Status.PASSED), ("b", Status.PASSED))  # 一次写记下这一轮全部的终态
    assert all(jr.status == Status.PASSED for jr in rs.saved) and store.load_run_state("run-1").status == Status.PASSED


def test_a_job_that_ends_first_is_committed_in_its_own_round_and_the_run_stays_open(any_store, tmp_path):
    """两个 job 先后结束：先结束的那一轮由终态写记下它（终态写只收到它一个），run 仍为 running；另一个 job 结束的那一轮使 run 成为
    终态，交还的明细只有这一次 tick 交给终态写的那个 job，结束时刻是这一轮的轮首时刻。"""
    meta, log, store = _setup(tmp_path, "a", "b", store=any_store)
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(0, 1, 2))  # 起 a、b
    _done_events(log, "a")
    store.clear()

    first = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(10))

    assert first == TickResult(TickOutcome.CONTINUE)
    assert store.commits == [(("a", Status.PASSED),)]
    state = store.load_run_state("run-1")
    assert (state.status, state.ended_at, state.jobs["a"].status, state.jobs["b"].status) == (
        Status.RUNNING, None, Status.PASSED, Status.RUNNING)
    assert state.jobs["a"].claimed_at == _iso(1)  # 终态写保留认领时刻

    _done_events(log, "b", base=10)
    second = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(20))

    assert second.outcome is TickOutcome.COMMITTED
    assert [jr.scope_id for jr in second.details] == ["b"]
    assert store.commits[-1] == (("b", Status.PASSED),)
    state = store.load_run_state("run-1")
    assert (state.status, state.ended_at) == (Status.PASSED, _iso(20))


def test_a_freed_slot_is_used_in_the_same_round(any_store, tmp_path):
    """并发上限为 1、a 结束而 b 未启动：同一轮先写下 a 的终态，再在加上这次写的作用的运行态上决策、认领 b，不停住（推进决策若只看这一轮
    读到的运行态，a 仍占着并发位，b 要等下一次触发）。"""
    meta, log, store = _setup(tmp_path, "a", "b", store=any_store)
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(0, 1))  # 起 a
    _done_events(log, "a")
    store.clear()
    launcher = FakeLauncher()

    outcome = tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(10, 11))

    assert outcome == TickResult(TickOutcome.CONTINUE)
    assert store.writes == ["project_state", "commit_job_states", "try_claim_job"]
    assert launcher.launched == ["b"]
    state = store.load_run_state("run-1")
    assert (state.jobs["a"].status, state.jobs["b"].status, state.jobs["b"].claimed_at) == (
        Status.PASSED, Status.RUNNING, _iso(11))


def test_proposed_starts_follow_the_definition_order_not_the_stored_order(any_store, tmp_path):
    """交给推进决策的运行态按运行定义的次序重排：存储读回的 jobs 次序与运行定义相反时（DynamoDB 的 Map 不保证次序），提议启动的仍是
    运行定义里靠前的那个。各推进器按同一次序提议，并发上限才靠认领碰撞守得住。"""

    class _Reversed(_Store):
        def load_run_state(self, run_id):
            state = super().load_run_state(run_id)
            return None if state is None else replace(state, jobs=dict(sorted(state.jobs.items(), reverse=True)))

    meta, log, store = _setup(tmp_path, "a", "b", "c", store=_Reversed(any_store.inner))
    assert list(store.load_run_state("run-1").jobs) == ["c", "b", "a"]
    launcher = FakeLauncher()

    tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock())

    assert launcher.launched == ["a"]


def test_verdict_write_failure_fails_tick_before_commit_and_retry_heals(tmp_path):
    """判定真值落库失败 → 异常原样抛出、**未**写终态（job 与 run 仍为 running）；下一轮 tick（触发源重试）成功落完并写下终态。
    若反过来先写终态再落，失败发生在终态写之后就没有下一轮了。"""
    seq: list = []
    meta, log, store = _setup(tmp_path, "a")
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock())
    _done_events(log, "a")
    with pytest.raises(OSError):
        tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(5),
             result_store=_RecordingResultStore(seq, fail=True))
    state = store.load_run_state("run-1")
    assert (state.status, state.jobs["a"].status) == (Status.RUNNING, Status.RUNNING)  # 没写终态
    healthy = _RecordingResultStore(seq)
    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(6),
                result_store=healthy).outcome is TickOutcome.COMMITTED
    assert [jr.scope_id for jr in healthy.saved] == ["a"] and store.load_run_state("run-1").status == Status.PASSED


def test_later_verdict_write_failure_leaves_the_run_uncommitted(tmp_path):
    """前一个 job 的判定已保存、后一个 job 的保存失败：异常原样抛出，这一轮没有发出终态写，两个 job 与 run 都仍为 running；重试的一轮
    保存完全部判定之后才写终态（ADR 0034 机制三「run 级状态只进不退」条④ K3）。"""

    class _FailsOnSecondSave(_RecordingResultStore):
        def save_job_result(self, run_id, jr):
            if self.saved:
                raise OSError("S3 不可达")
            super().save_job_result(run_id, jr)

    seq: list = []
    meta, log, store = _setup(tmp_path, "a", "b", store=_OrderRecordingRunStore(tmp_path, seq))
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock())
    _done_events(log, "a"); _done_events(log, "b", base=10)
    with pytest.raises(OSError):
        tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(5),
             result_store=_FailsOnSecondSave(seq))
    assert [x[0] for x in seq] == ["verdict"]  # 前一个保存了，没有终态写
    state = store.load_run_state("run-1")
    assert (state.status, state.jobs["a"].status, state.jobs["b"].status) == (Status.RUNNING, Status.RUNNING, Status.RUNNING)
    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(6),
                result_store=_RecordingResultStore(seq)).outcome is TickOutcome.COMMITTED
    assert [x[0] for x in seq] == ["verdict", "verdict", "verdict", "commit"]
    assert store.load_run_state("run-1").status == Status.PASSED


def test_a_round_that_cannot_save_a_verdict_starts_no_job(any_store, tmp_path):
    """保存明细失败的那一轮不认领、不启动：两个执行中的 job 都有结果，第二份存不成时原样抛出，没有终态写、没有认领，仍有的 pending
    不被启动，执行中的 job（含已存下明细的）留在 running。重试的一轮重存全部、一次写下，再用腾出的并发位启动 pending 的 job。"""

    class _FailsOnSecondSave(_RecordingResultStore):
        def save_job_result(self, run_id, jr):
            if self.saved:
                raise OSError("S3 不可达")
            super().save_job_result(run_id, jr)

    meta, log, store = _setup(tmp_path, "a", "b", "c", store=any_store)
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock())  # 起 a、b
    _done_events(log, "a"); _done_events(log, "b", base=10)
    store.clear()
    launcher = FakeLauncher()

    with pytest.raises(OSError):
        tick("run-1", meta, log, store, launcher, max_concurrency=2, clock=Clock(5), result_store=_FailsOnSecondSave([]))

    assert store.writes == ["project_state"] and launcher.launched == []
    state = store.load_run_state("run-1")
    assert [state.jobs[s].status for s in ("a", "b", "c")] == [Status.RUNNING, Status.RUNNING, Status.PENDING]
    assert state.status == Status.RUNNING

    healthy = _RecordingResultStore([])
    store.clear()
    assert tick("run-1", meta, log, store, launcher, max_concurrency=2, clock=Clock(6),
                result_store=healthy) == TickResult(TickOutcome.CONTINUE)
    assert [jr.scope_id for jr in healthy.saved] == ["a", "b"]
    assert store.commits == [(("a", Status.PASSED), ("b", Status.PASSED))]
    assert store.writes == ["project_state", "commit_job_states", "try_claim_job"] and launcher.launched == ["c"]


# ---------- 按 job 判断快照（ADR 0054 决策二后台推进条「快照」）----------

@pytest.mark.parametrize("deadline_at, at", [(FAR_DEADLINE, 10), (_NEAR, 41)], ids=["未过停止启动", "已过停止启动"])
def test_a_job_claimed_after_the_read_is_not_committed_this_round(any_store, tmp_path, deadline_at, at):
    """同一轮两个 job 都有结果，一个在这一轮读到的运行态里带认领时刻，另一个是读运行态之后才被别处认领的（读到的运行态里它是
    pending、不带认领时刻）：只为前者存明细、写终态，后者这一轮不写明细、不写终态，下一轮读到新的运行态再写。后者在决策用的运行态里
    仍是 pending：未过停止启动的时刻时多一次被认领条件挡下的启动提议；已过而没有别的执行中的 job 时多一次没写成的到期结束写（库中它
    是 running），重读之后继续推进。"""
    meta, log, store = _setup(tmp_path, "a", "b", deadline_at=deadline_at, store=any_store)
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(0, 1))  # 起 a
    _done_events(log, "a")

    def _other_advancer_claims_and_b_finishes():
        assert store.inner.try_claim_job("run-1", "b", claimed_at=_iso(5)) is True
        _done_events(log, "b", base=10)

    store.clear()
    store.after["load_run_state"] = _other_advancer_claims_and_b_finishes
    rs, launcher = _RecordingResultStore([]), FakeLauncher()

    outcome = tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(at), result_store=rs)

    assert outcome == TickResult(TickOutcome.CONTINUE)
    assert [jr.scope_id for jr in rs.saved] == ["a"] and store.commits == [(("a", Status.PASSED),)]
    assert launcher.launched == []
    assert store.writes == ["project_state", "commit_job_states",
                            "try_claim_job" if deadline_at == FAR_DEADLINE else "end_run"]
    state = store.load_run_state("run-1")
    assert (state.status, state.jobs["a"].status, state.jobs["b"].status, state.message) == (
        Status.RUNNING, Status.PASSED, Status.RUNNING, None)

    done = tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(at + 1), result_store=rs)

    assert done.outcome is TickOutcome.COMMITTED and [jr.scope_id for jr in done.details] == ["b"]
    assert [jr.scope_id for jr in rs.saved] == ["a", "b"]
    state = store.load_run_state("run-1")
    assert (state.status, state.message, state.jobs["b"].claimed_at) == (Status.PASSED, None, _iso(5))


@pytest.mark.parametrize("claimed_at", [None, "t1", "2030-01-01T00:00:00"])
def test_job_without_a_readable_claim_time_is_not_committed_this_round(tmp_path, claimed_at):
    """运行态里的认领时刻缺、读不出或不带时区的 job（ADR 0054 决策二后台推进条「快照」）：投影为终态也不存明细、不写终态，按继续推进
    处理；没有「按预算说明」的回落。对照：同样的事件、运行态里带认领时刻的 run 照常写下终态。"""
    meta, log, store = _setup(tmp_path, "a", store=_SpyRunStore(tmp_path))
    store.update_job_state("run-1", JobState("a", Status.RUNNING, claimed_at=claimed_at))
    _done_events(log, "a")
    rs = _RecordingResultStore([])

    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(5),
                result_store=rs) == TickResult(TickOutcome.CONTINUE)
    assert rs.saved == [] and "commit_job_states" not in store.writes
    assert store.load_run_state("run-1").status == Status.RUNNING

    control_dir = tmp_path / "control"
    control_dir.mkdir()
    meta, log, store = _setup(control_dir, "a", store=_SpyRunStore(control_dir))
    store.update_job_state("run-1", JobState("a", Status.RUNNING, claimed_at=_iso(0)))
    _done_events(log, "a")
    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(6),
                result_store=rs).outcome is TickOutcome.COMMITTED
    assert [jr.scope_id for jr in rs.saved] == ["a"]


# ---------- 两个推进器重叠，各记一部分 job（ADR 0034 机制三「run 级状态只进不退」条④）----------

@pytest.mark.parametrize("first", ["partial", "complete"])
def test_overlapping_advancers_each_commit_a_part_and_exactly_one_commits_the_run(any_store, tmp_path, first):
    """两个推进器读到的事件快照不同：P 只看到 a 有结果，Q 看到 a、b 都有结果。固定先后：一方读完运行态之后、写下终态之前，另一方走完
    一整轮。先写成的是 P（first=partial）时，P 记下 a、run 仍未结束，返回继续推进；Q 再写时 a 已是终态被跳过、记下 b 之后 run 成为终态，
    Q 返回 COMMITTED。先写成的是 Q 时，Q 使 run 成为终态；P 的终态写返回 ALREADY_ENDED，P 返回 ENDED。两种先后下都恰有一方得到
    COMMITTED，run 的结束时刻是它这一轮的轮首时刻。明细与写下的终态是否出自同一份快照不在断言之内。"""
    meta, log_p, store = _setup(tmp_path, "a", "b", store=any_store)
    tick("run-1", meta, log_p, store, FakeLauncher(), max_concurrency=2, clock=Clock(0, 1, 2))  # 起 a、b
    _done_events(log_p, "a")
    log_q = SqliteEventLog(tmp_path / "q.db")
    _done_events(log_q, "a"); _done_events(log_q, "b", base=10)
    results: dict[str, TickResult] = {}

    def _run(name, log, at):
        def go():
            results[name] = tick("run-1", meta, log, store.inner, FakeLauncher(), max_concurrency=2, clock=Clock(at))
        return go

    if first == "partial":
        store.before["commit_job_states"] = _run("P", log_p, 10)  # Q 读完运行态、写终态之前，P 走完一轮
        results["Q"] = tick("run-1", meta, log_q, store, FakeLauncher(), max_concurrency=2, clock=Clock(20))
        expected = {"P": TickOutcome.CONTINUE, "Q": TickOutcome.COMMITTED}
        ended_at = _iso(20)
    else:
        store.before["commit_job_states"] = _run("Q", log_q, 20)  # P 读完运行态、写终态之前，Q 走完一轮
        results["P"] = tick("run-1", meta, log_p, store, FakeLauncher(), max_concurrency=2, clock=Clock(10))
        expected = {"P": TickOutcome.ENDED, "Q": TickOutcome.COMMITTED}
        ended_at = _iso(20)

    assert {name: r.outcome for name, r in results.items()} == expected
    assert [r.outcome for r in results.values()].count(TickOutcome.COMMITTED) == 1
    assert [jr.scope_id for jr in results["Q"].details] == ["a", "b"]
    state = store.load_run_state("run-1")
    assert (state.status, state.ended_at, state.jobs["a"].status, state.jobs["b"].status) == (
        Status.PASSED, ended_at, Status.PASSED, Status.PASSED)


# ---------- 报告：使 run 成为终态的那一方从记录生成，这一次 tick 的明细用内存、较早轮次的从判定存储读回
# （ADR 0027「ReportStore 接口：整 run 一次写」节；ADR 0034 机制三「run 级状态只进不退」条④ K2）----------

class _Report:
    def __init__(self) -> None:
        self.written: list = []

    def write(self, run_id, result, *, created_at):
        self.written.append((run_id, result, created_at))


def test_report_comes_from_the_record_and_the_committed_details_not_from_a_second_read_of_the_events(tmp_path):
    """报告从记录组装：状态取运行态，判定明细取写成的那一轮交还的那一份；之后事件再变（接力方补写的未知退出被真实退出码覆盖之类），
    报告里的判定仍是提交的那一份。run 级墙钟由运行态的起止算出。"""
    meta, log, store = _setup(tmp_path, "a")
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock())
    _done_events(log, "a")
    done = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(5))
    log.record_exit("a", 1)  # 提交之后退出记录被改写：再读一次事件重算会得出 error
    reports = _Report()
    write_report_from_record(meta, store, done.details, reports, result_store=None,
                             created_at="2030-01-01T00:00:06+00:00")
    ((run_id, result, created_at),) = reports.written
    assert (run_id, result.status, result.jobs[0].status, result.details[0].status) == (
        "run-1", Status.PASSED, Status.PASSED, Status.PASSED)
    assert result.duration_ms == 5000.0  # 运行态的 started_at（T0）到 ended_at（T0+5）
    assert created_at == "2030-01-01T00:00:06+00:00"


def test_report_follows_the_committing_round_when_two_advancers_read_different_snapshots(tmp_path):
    """两个推进器读到不同的快照、竞争使 run 成为终态（ADR 0034 机制三「run 级状态只进不退」条④ K1、K2）。固定先后：B 读完运行态、读
    事件之前，A 走完一轮并写成终态；B 随后按自己的快照存下明细、发出终态写，终态写报告 run 已结束。只断言必须成立的正面性质：A 写成、
    带它这一轮的判定明细；B 返回不带明细的 ENDED；run 级的状态、说明与结束时刻是 A 写下的；用 A 交还的明细与记录生成的报告是 A 的判定。
    B 落下的判定明细与 A 的谁留在存储里不在断言之内。"""
    meta, log_a, store = _setup(tmp_path, "a")
    tick("run-1", meta, log_a, store, FakeLauncher(), max_concurrency=1, clock=Clock())  # 认领并启动 a
    _done_events(log_a, "a")  # A 读到的快照：完整的结果，判 passed
    rs_a, rs_b = _RecordingResultStore([]), _RecordingResultStore([])

    class _OtherAdvancerCommitsFirst(SqliteEventLog):
        """B 的事件日志：B 第一次读事件时，先让 A 走完一轮。"""

        committed = None

        def records(self):
            if self.committed is None:
                self.committed = tick("run-1", meta, log_a, store, FakeLauncher(), max_concurrency=1, clock=Clock(20),
                                      result_store=rs_a)
            return super().records()

    log_b = _OtherAdvancerCommitsFirst(tmp_path / "b.db")
    assert log_b.record_timed_out_if_absent("a") is True  # B 读到的快照：只有补写的未知退出，判超时

    outcome_b = tick("run-1", meta, log_b, store, FakeLauncher(), max_concurrency=1, clock=Clock(30), result_store=rs_b)

    outcome_a = log_b.committed
    assert outcome_a.outcome is TickOutcome.COMMITTED
    assert [jr.status for jr in outcome_a.details] == [Status.PASSED]
    assert outcome_b == TickResult(TickOutcome.ENDED)  # B 读运行态时 run 未结束：发出了终态写、终态写报告 run 已结束
    state = store.load_run_state("run-1")
    assert (state.status, state.ended_at, state.message) == (Status.PASSED, _iso(20), None)
    reports = _Report()
    write_report_from_record(meta, store, outcome_a.details, reports, result_store=None,
                             created_at="2030-01-01T00:00:21+00:00")
    ((_run_id, result, _created_at),) = reports.written
    assert (result.status, [o.status for o in result.jobs], [jr.status for jr in result.details]) == (
        Status.PASSED, [Status.PASSED], [Status.PASSED])


class _LoadCountingResultStore(LocalResultStore):
    def __init__(self, root) -> None:
        super().__init__(root)
        self.loads: list[str] = []

    def load_job_result(self, run_id, scope_id):
        self.loads.append(scope_id)
        return super().load_job_result(run_id, scope_id)


def test_report_reads_back_details_of_earlier_rounds_and_uses_this_rounds_in_memory(tmp_path):
    """使 run 成为终态的那一轮，内存里只有这一次 tick 交给终态写的明细：较早轮次写下终态的 job 从判定存储按 scope_id 读回，这一轮的用
    内存里的那一份，不为它读存储；由到期的结束写记 skipped 的 job 从没存过明细，读回为空、报告里不带明细。没有判定存储时只用内存。"""
    meta, log, store = _setup(tmp_path, "a", "b", "c", deadline_at=_NEAR)
    rs = _LoadCountingResultStore(tmp_path)
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(0, 1, 2), result_store=rs)  # 起 a、b
    _done_events(log, "a")
    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(41),
                result_store=rs) == TickResult(TickOutcome.CONTINUE)  # 记下 a；b 仍在执行，不做结束写
    _done_events(log, "b", base=10)
    done = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(42), result_store=rs)
    assert done.outcome is TickOutcome.COMMITTED and [jr.scope_id for jr in done.details] == ["b"]
    state = store.load_run_state("run-1")
    assert [state.jobs[s].status for s in ("a", "b", "c")] == [Status.PASSED, Status.PASSED, Status.SKIPPED]

    reports = _Report()
    write_report_from_record(meta, store, done.details, reports, result_store=rs, created_at="t")
    ((_run_id, result, _created_at),) = reports.written
    assert rs.loads == ["a", "c"]
    assert [(o.scope_id, o.status, o.detail is not None) for o in result.jobs] == [
        ("a", Status.PASSED, True), ("b", Status.PASSED, True), ("c", Status.SKIPPED, False)]
    assert result.jobs[1].detail is done.details[0]

    only_memory = _Report()
    write_report_from_record(meta, store, done.details, only_memory, result_store=None, created_at="t")
    ((_run_id, result, _created_at),) = only_memory.written
    assert [o.detail is not None for o in result.jobs] == [False, True, False]


def test_report_generation_failures_are_isolated(tmp_path):
    """生成报告的各步都在失败隔离之内（ADR 0030 决定三「ReportStore.write 失败隔离」注）：写报告失败、为组装而读运行态失败、运行态不存在、
    从判定存储读回明细失败，都不击穿已到终态的 run，也不抛出；没有报告落点时什么都不做、不读运行态，也不读回明细。"""

    class _Boom:
        def write(self, run_id, result, *, created_at):
            raise OSError("S3 不可达")

    class _ReadFails(LocalRunStore):
        def load_run_state(self, run_id):
            raise OSError("读不回运行态")

    class _Counting(LocalRunStore):
        reads = 0

        def load_run_state(self, run_id):
            self.reads += 1
            return super().load_run_state(run_id)

    class _LoadFails:
        loads = 0

        def load_job_result(self, run_id, scope_id):
            self.loads += 1
            raise OSError("S3 不可达")

    meta, log, store = _setup(tmp_path, "a", "b")
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock())
    _done_events(log, "a")
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(4))  # 较早一轮记下 a
    _done_events(log, "b", base=10)
    done = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(5))
    assert [jr.scope_id for jr in done.details] == ["b"]

    write_report_from_record(meta, store, done.details, _Boom(), result_store=None, created_at="t")
    reports = _Report()
    write_report_from_record(meta, _ReadFails(tmp_path), done.details, reports, result_store=None, created_at="t")
    write_report_from_record(meta, LocalRunStore(tmp_path / "elsewhere"), done.details, reports, result_store=None,
                             created_at="t")
    failing = _LoadFails()
    write_report_from_record(meta, store, done.details, reports, result_store=failing, created_at="t")
    assert failing.loads == 1 and reports.written == []
    counting, untouched = _Counting(tmp_path), _LoadFails()
    write_report_from_record(meta, counting, done.details, None, result_store=untouched, created_at="t")
    assert counting.reads == 0 and untouched.loads == 0


# ---------- 接力补写的超时退出（ADR 0034「job timeout」节「`timed_out` 归因链」）----------

def test_a_relay_written_timeout_is_committed_and_a_later_real_exit_changes_nothing(tmp_path):
    """接力补写一条带超时标志、退出码未知的退出记录之后，下一轮由这一轮的快照存下明细（预算到点：error 加 timeout）再以终态写记下；
    之后才到的真实退出覆盖了退出记录，但运行态里这个 job 已是终态、不再被选中：记录与存下的明细都不变。"""
    meta, log, store = _setup(tmp_path, "a", "b", store=_SpyRunStore(tmp_path))
    rs = LocalResultStore(tmp_path)
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock())  # 起 a、b
    assert log.record_timed_out_if_absent("a") is True

    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(400),
                result_store=rs) == TickResult(TickOutcome.CONTINUE)
    saved = rs.load_job_result("run-1", "a")
    assert (saved.status, saved.error_type) == (Status.ERROR, "timeout")
    assert store.load_run_state("run-1").jobs["a"].status == Status.ERROR

    _done_events(log, "a")  # 真实的退出（干净退出、内容完整）在补写之后到达，覆盖了退出记录
    store.writes.clear()
    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(401),
                result_store=rs) == TickResult(TickOutcome.CONTINUE)
    assert store.writes == ["project_state"]  # 没有终态写
    assert store.load_run_state("run-1").jobs["a"].status == Status.ERROR
    assert rs.load_job_result("run-1", "a") == saved


def test_overlapping_advancers_leave_the_relay_timeout_in_the_run_state(tmp_path):
    """两个推进方重叠：认领方的一轮读完运行态（a 仍在执行）之后，接力方完整推进一轮，按补写的超时退出记下 a 的终态（error）；随后 a 的
    真实退出（干净退出、内容完整）到达，认领方这一轮读到的是它，按旧的运行态为 a 发出 passed 的终态写。运行态里 a 的终态不变，run 仍
    未结束。判定明细按 scope_id 保存，认领方这一轮存下的那一份覆盖接力方的，这里不断言明细与终态一致。"""
    meta, log, inner = _setup(tmp_path, "a", "b")
    rs = LocalResultStore(tmp_path)
    tick("run-1", meta, log, inner, FakeLauncher(), max_concurrency=2, clock=Clock())  # 起 a、b
    assert log.record_timed_out_if_absent("a") is True  # 接力方补写
    owner = _Store(inner)
    outcomes = {}

    def relay_round_then_real_exit():
        outcomes["relay"] = tick("run-1", meta, log, inner, FakeLauncher(), max_concurrency=2, clock=Clock(400),
                                 result_store=rs)
        assert inner.load_run_state("run-1").jobs["a"].status == Status.ERROR  # 接力方已按超时记下 a
        _done_events(log, "a")  # 真实退出在接力方那一轮之后到达，覆盖补写的那一条

    owner.after["load_run_state"] = relay_round_then_real_exit
    outcomes["owner"] = tick("run-1", meta, log, owner, FakeLauncher(), max_concurrency=2, clock=Clock(401),
                             result_store=rs)

    assert outcomes == {"relay": TickResult(TickOutcome.CONTINUE), "owner": TickResult(TickOutcome.CONTINUE)}
    assert owner.commits == [(("a", Status.PASSED),)]  # 认领方确实按真实退出、在旧的运行态上发出了终态写
    state = inner.load_run_state("run-1")
    assert (state.status, state.jobs["a"].status, state.jobs["b"].status) == (Status.RUNNING, Status.ERROR, Status.RUNNING)


# ---------- 到期处理：到期的结束写把未启动的 job 记 skipped 并带到期的说明，run 随之成为终态
# （ADR 0054 决策二第 3 条与后台推进条）----------

def test_past_stop_start_claims_nothing_and_expires_the_run(tmp_path):
    """已过停止启动的时刻，最后一个执行中的 job 在这一轮得出结果，仍有未启动的 job：不认领、不启动；同一轮先写下这个 job 的终态，
    再在加上这次写的作用的运行态上判出「没有执行中的 job」、做到期的结束写——写的次序是投影、终态写、结束写。结束写把未启动的 job
    记 skipped 并带到期的说明，run 按取法记 aborted、带「已超过允许运行的时间」；返回 COMMITTED，交还的明细带这个 job。"""
    meta, log, store = _setup(tmp_path, "a", "b", deadline_at=_NEAR, store=_SpyRunStore(tmp_path))
    launcher, rs = FakeLauncher(), _RecordingResultStore([])
    tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(0, 1))  # 起 a
    _done_events(log, "a")
    store.writes.clear()

    done = tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(41), result_store=rs)

    assert launcher.launched == ["a"]  # b 没有被认领、没有启动
    assert done.outcome is TickOutcome.COMMITTED
    assert [jr.scope_id for jr in done.details] == ["a"]
    assert [jr.scope_id for jr in rs.saved] == ["a"]
    assert store.writes == ["project_state", "commit_job_states", "end_run"]
    state = store.load_run_state("run-1")
    assert (state.status, state.message, state.ended_at) == (Status.ABORTED, _DEADLINE_ENDING.run_message, _iso(41))
    assert (state.jobs["a"].status, state.jobs["b"].status, state.jobs["b"].message) == (
        Status.PASSED, Status.SKIPPED, _DEADLINE_ENDING.skipped_message)


def test_all_done_after_the_deadline_ends_by_the_terminal_write(tmp_path):
    """没有执行中的、也没有未启动的 job：run 在记下各 job 终态的那次写里随之成为终态，不论是否已过期限，不做结束写、不带到期的说明
    （ADR 0054 决策二第 4 条）。"""
    meta, log, store = _setup(tmp_path, "a", deadline_at=_NEAR, store=_SpyRunStore(tmp_path))
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(0, 1))
    _done_events(log, "a")
    done = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(500))
    assert done.outcome is TickOutcome.COMMITTED
    assert "commit_job_states" in store.writes and "end_run" not in store.writes
    state = store.load_run_state("run-1")
    assert (state.status, state.message) == (Status.PASSED, None)


def test_past_stop_start_with_a_running_job_continues(tmp_path):
    """已过停止启动的时刻而还有执行中的 job：不认领、不做结束写，继续推进，这一轮只有投影写；执行中的 job 由它的截止时刻停下。"""
    meta, log, store = _setup(tmp_path, "a", "b", deadline_at=_NEAR, store=_SpyRunStore(tmp_path))
    launcher = FakeLauncher()
    tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(0, 1))  # 起 a，a 仍在执行
    store.writes.clear()
    assert tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(41)) == TickResult(TickOutcome.CONTINUE)
    assert launcher.launched == ["a"] and store.writes == ["project_state"]


def test_claim_refused_by_the_deadline_triggers_one_replan_in_the_same_round(tmp_path):
    """这一轮里有认领因已过停止启动的时刻而没有做（每次认领前重做检查）：同一轮里重新取时刻、重新读取运行态与事件、按已过停止启动再
    决策一次（ADR 0054 决策二后台推进条「时刻」），满足到期的结束写就当场做，不留给不会再来的下一轮。结束时刻取重新读取之前的
    那一次。"""
    meta, log, store = _setup(tmp_path, "a", deadline_at=_NEAR)
    clock = Clock(0, 50, 51)  # 轮首未过停止启动的时刻（T0+40）；认领前已过；重新读取之前再取一次

    done = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=clock)

    assert done.outcome is TickOutcome.COMMITTED and done.details == ()  # 一个 job 都没有启动
    state = store.load_run_state("run-1")
    assert (state.status, state.message, state.ended_at, state.jobs["a"].status) == (
        Status.ABORTED, _DEADLINE_ENDING.run_message, _iso(51), Status.SKIPPED)
    assert clock.reads == 3


@pytest.mark.parametrize("launch_fails, outcome", [(False, TickOutcome.CONTINUE), (True, TickOutcome.COMMITTED)])
def test_replan_counts_the_jobs_claimed_earlier_in_the_round(tmp_path, launch_fails, outcome):
    """重新决策时这一轮里先前认领成功的 job 计入：它在执行中就不做到期的结束写、继续推进；它的启动已失败（补写了退出记录）就在重做的
    那一遍写下它的终态，随后做到期的结束写，它的判定明细随结果交还，run 有 error 即记 error。重新决策只做一次：只多读一次时钟。"""

    class _Launcher(FakeLauncher):
        def launch(self, job, *, cutoff_at):
            super().launch(job, cutoff_at=cutoff_at)
            if launch_fails:
                raise RuntimeError("boom")

    meta, log, store = _setup(tmp_path, "a", "b", deadline_at=_NEAR, store=_SpyRunStore(tmp_path))
    clock = Clock(0, 1, 50, 51)
    launcher = _Launcher()
    done = tick("run-1", meta, log, store, launcher, max_concurrency=2, clock=clock)
    assert done.outcome is outcome and launcher.launched == ["a"]
    assert clock.reads == 4 + (1 if launch_fails else 0)  # 轮首、两次认领前、重新读取前；启动失败时另取一次
    state = store.load_run_state("run-1")
    assert state.jobs["a"].claimed_at == _iso(1)
    if launch_fails:
        assert [jr.scope_id for jr in done.details] == ["a"]
        assert store.writes == ["project_state", "try_claim_job", "project_state", "commit_job_states", "end_run"]
        assert (state.status, state.message, state.jobs["b"].status) == (Status.ERROR, _DEADLINE_ENDING.run_message, Status.SKIPPED)
    else:
        assert store.writes == ["project_state", "try_claim_job", "project_state"]
        assert (state.status, state.jobs["b"].status) == (Status.RUNNING, Status.PENDING)


def test_replan_keeps_what_the_first_pass_committed(any_store, tmp_path):
    """重做的那一遍读到第一遍已记下的终态：不再为它存明细、不再写它的终态，只为这之后才有结果的 job 存、写；重做那一遍做结束写使 run
    成为终态时，交还的明细含两遍交给终态写的全部。固定先后：第一遍记下 a，认领 b 而 b 启动失败（补写了退出记录），认领 c 之前已过
    停止启动的时刻；重做的那一遍记下 b，再以到期的结束写结束 c。"""

    class _BFails(FakeLauncher):
        def launch(self, job, *, cutoff_at):
            super().launch(job, cutoff_at=cutoff_at)
            if job.scope_id == "b":
                raise RuntimeError("boom: b")

    meta, log, store = _setup(tmp_path, "a", "b", "c", deadline_at=_NEAR, store=any_store)
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(0, 1))  # 起 a
    _done_events(log, "a")
    store.clear()
    rs = _RecordingResultStore([])
    clock = Clock(30, 31, 32, 50, 51)  # 轮首、认领 b、b 启动失败的退出时刻、认领 c 之前（已过 T0+40）、重新读取之前

    done = tick("run-1", meta, log, store, _BFails(), max_concurrency=2, clock=clock, result_store=rs)

    assert done.outcome is TickOutcome.COMMITTED
    assert [jr.scope_id for jr in done.details] == ["a", "b"] and [jr.scope_id for jr in rs.saved] == ["a", "b"]
    assert store.writes == ["project_state", "commit_job_states", "try_claim_job",
                            "project_state", "commit_job_states", "end_run"]
    assert store.commits == [(("a", Status.PASSED),), (("b", Status.ERROR),)]
    state = store.load_run_state("run-1")
    assert (state.status, state.ended_at, state.message) == (Status.ERROR, _iso(51), _DEADLINE_ENDING.run_message)
    assert [state.jobs[s].status for s in ("a", "b", "c")] == [Status.PASSED, Status.ERROR, Status.SKIPPED]


def test_no_writes_and_no_event_reads_in_a_round_that_cannot_read_the_run_state(tmp_path):
    """读不到运行态的那一轮返回继续推进，不读事件、不写任何东西：认领、投影与结束写都写不成，终态写会抛错（ADR 0054 决策二后台推进条
    「收尾与报告」）。已过停止启动的时刻也不做到期的结束写。"""
    meta = _meta("a", deadline_at=_NEAR)
    store = _SpyRunStore(tmp_path)  # 没有建 run：运行态读不到
    log, launcher = _CountingEventLog(tmp_path / "e.db"), FakeLauncher()
    outcome = tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(50))
    assert outcome == TickResult(TickOutcome.CONTINUE)
    assert store.writes == [] and log.record_reads == 0 and launcher.launched == []


class _ClaimLandsAfterRead(SqliteEventLog):
    """读事件时另一个推进器的认领恰好落下：它在本轮读运行态之后、结束写之前认领了 scope（它的时钟落后，还没过停止启动的时刻）。"""

    def __init__(self, path, store, scope: str) -> None:
        super().__init__(path)
        self._store, self._scope, self.landed = store, scope, False

    def records(self):
        recs = super().records()
        if not self.landed:
            self.landed = self._store.try_claim_job("run-1", self._scope, claimed_at=_iso(39))
        return recs


def test_expiry_loses_to_a_claim_that_landed_after_the_read(tmp_path):
    """到期的结束写与认领并发（本机）：一个推进器读到「没有执行中的、仍有未启动的」之后，另一个推进器的认领落下——前者的结束写按写下时的
    运行态判断，那时已有 running 的 job，写不成；重读到 run 仍未结束，返回继续推进；run 没有结束、新认领的 job 仍是 running，同一轮
    得出结果的 a 已由终态写记下。"""
    meta, _, store = _setup(tmp_path, "a", "b", deadline_at=_NEAR, store=_SpyRunStore(tmp_path))
    plain = SqliteEventLog(tmp_path / "e.db")
    tick("run-1", meta, plain, store, FakeLauncher(), max_concurrency=1, clock=Clock(0, 1))  # 起 a
    _done_events(plain, "a")
    log = _ClaimLandsAfterRead(tmp_path / "e.db", store, "b")

    outcome = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(41))

    assert log.landed is True
    assert outcome == TickResult(TickOutcome.CONTINUE)
    assert store.writes.count("end_run") == 1  # 结束写确实发出
    state = store.load_run_state("run-1")
    assert (state.status, state.claim_count, state.jobs["a"].status, state.jobs["b"].status) == (
        Status.RUNNING, 2, Status.PASSED, Status.RUNNING)
    assert state.message is None
