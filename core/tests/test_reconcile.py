"""reconciler tick 测试：推进编排 + 幂等 + CAS 起 job + 逐 job 写序 + 到期处理。

用真 SqliteEventLog + RunStore（LocalRunStore，部分用例另以 moto 上的 DynamoDBRunStore 对拍）+ fake Launcher（记录被 launch 的 job，
不起真进程）+ 记下每次保存的判定存储（`_RecordingResultStore`，部分用例套在真 LocalResultStore 外面）与注入的假墙钟验证 tick 逻辑：
- 首 tick 从全 pending 起首批（≤max_concurrency），每次认领前另取一次时刻作认领时刻，截止时刻随 launch 交出；
- 逐 job 写序（ADR 0030 决定三、ADR 0034 机制三「run 级状态只进不退」条④的步骤）：每一轮为已有结果的 job 各存一份带标识的判定明细、
  再以一次终态写记下它们的终态并点名各自的那一份，run 的状态随之写下；投影只前进、不越过 running；推进决策在这一轮读到的运行态加上
  终态写的作用上作出，同一轮就能腾出并发位、判出「没有执行中的 job」；
- 按 job 判断快照：在这一轮读到的运行态里不带认领时刻的 job 这一轮不写，别的 job 照写；
- 幂等：重复 tick 不重复 launch（CAS 挡）；
- 已过停止启动的时刻：不认领；没有执行中的 job、仍有未启动的就做到期的结束写，写下时有 running 的 job 即写不成；
- 同一轮里认领因已过停止启动而没做时重新决策一次；
- 结果三种（TickOutcome）：继续推进 / 这一方的写使 run 成为终态 / run 已结束而使它成为终态的不是这一方；推进步骤不交回明细，报告由
  宿主经 `write_report_from_record` 从记录生成：读运行态，按其中点名的标识读回明细（ADR 0030 决定三「点名」条）。
并发与先后类的性质用固定先后构造：在读与写之间经包装的 RunStore 或事件日志插入另一方的动作。
纯编排逻辑（launch 被 fake、时钟被注入）→ 绿即够；真进程脱离 / SQLite 并发是真实运行边界。
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from gherkai_core.adapters.event_log import SqliteEventLog
from gherkai_core.adapters.result_store.local import LocalResultStore
from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.errors import NamedDetailMissing
from gherkai_core.model import Job, JobResult, JobState, RunMeta, RunState, Scenario, Status, Step
from gherkai_core.project import DEADLINE_TIMEOUT_MESSAGE
from gherkai_core.reconcile import TickOutcome, tick, write_report_from_record
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


class _RecordingResultStore:
    """记下每次保存的判定存储：saved 是存下的明细、ids 是 (scope_id, 标识)，都按保存的次序；按标识读回，loads 记下读过的标识。

    给了 inner 时存与读都转交给它（几个替身可以共用一处存放，各自记下自己的保存）；没给时存在内存里。fail 为 True 时每次保存都抛
    OSError。seq 与别的替身共用，用来核对写的先后。"""

    def __init__(self, seq: list | None = None, fail: bool = False, *, inner=None) -> None:
        self.seq = seq if seq is not None else []
        self.fail, self.inner = fail, inner
        self.saved: list[JobResult] = []
        self.ids: list[tuple[str, str]] = []
        self.loads: list[str] = []
        self._by_id: dict[str, JobResult] = {}

    def save_job_result(self, run_id, result_id, jr):
        if self.fail:
            raise OSError("S3 不可达")
        if self.inner is not None:
            self.inner.save_job_result(run_id, result_id, jr)
        else:
            self._by_id[result_id] = jr
        self.seq.append(("verdict", jr.scope_id, jr.status))
        self.saved.append(jr)
        self.ids.append((jr.scope_id, result_id))

    def load_job_result(self, run_id, result_id):
        self.loads.append(result_id)
        if self.inner is not None:
            return self.inner.load_job_result(run_id, result_id)
        return self._by_id.get(result_id)

    def id_of(self, scope_id: str) -> str:
        """这个 job 唯一一次保存所用的标识（存过不止一次时报错，免得断言取错一份）。"""
        (rid,) = [rid for sid, rid in self.ids if sid == scope_id]
        return rid


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


def _job_files(root) -> list[str]:
    """run-1 的判定明细目录里的文件名（排序后）。"""
    jobs_dir = root / "run-1" / "jobs"
    return sorted(p.name for p in jobs_dir.iterdir()) if jobs_dir.exists() else []


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
    done = tick("run-1", meta, log, store, launcher, max_concurrency=2, clock=Clock(), result_store=_RecordingResultStore())
    assert done is TickOutcome.CONTINUE
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
    tick("run-1", meta, log, store, launcher, max_concurrency=2, clock=Clock(0, 1, 7), result_store=_RecordingResultStore())
    state = store.load_run_state("run-1")
    assert (state.jobs["a"].claimed_at, state.jobs["b"].claimed_at) == (_iso(1), _iso(7))
    assert launcher.cutoff_at == {"a": _at(301), "b": _at(307)}


def test_cutoff_is_capped_by_the_run_deadline(tmp_path):
    """截止时刻以运行期限封顶（ADR 0054 决策二第 2 条）：认领时刻加预算晚于期限时，交给 launch 的是期限本身。"""
    meta, log, store = _setup(tmp_path, "a", deadline_at=_NEAR)
    launcher = FakeLauncher()
    tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(0, 1), result_store=_RecordingResultStore())
    assert launcher.cutoff_at == {"a": _at(100)}


def test_tick_idempotent_no_double_launch(tmp_path):
    """重复 tick 不重复 launch（CAS 挡已 running，机制四）。"""
    meta, log, store = _setup(tmp_path, "a", "b")
    launcher, rs = FakeLauncher(), _RecordingResultStore()
    tick("run-1", meta, log, store, launcher, max_concurrency=2, clock=Clock(), result_store=rs)
    n1 = len(launcher.launched)
    tick("run-1", meta, log, store, launcher, max_concurrency=2, clock=Clock(), result_store=rs)  # 再 tick
    assert len(launcher.launched) == n1  # 没多起（a/b 已 running）


def test_tick_starts_next_after_completion(tmp_path):
    """一个 job 完成（两件都要齐）后，同一轮先记下它的终态，再用腾出的并发位起下一个 pending。"""
    meta, log, store = _setup(tmp_path, "a", "b", "c")
    launcher, rs = FakeLauncher(), _RecordingResultStore()
    tick("run-1", meta, log, store, launcher, max_concurrency=2, clock=Clock(), result_store=rs)  # 起 a,b
    _done_events(log, "a")
    tick("run-1", meta, log, store, launcher, max_concurrency=2, clock=Clock(10), result_store=rs)
    assert "c" in launcher.launched  # a 完成腾位 → c 被起
    assert store.load_run_state("run-1").jobs["a"].status == Status.PASSED


def test_tick_commits_when_all_done(tmp_path):
    """全部 job 两件都要齐 → 这一方的终态写使 run 成为终态：返回 COMMITTED，job 的终态点名这一轮存下的那一份明细，run 的状态按取法
    写下，ended_at 是这一轮读运行态之前取的时刻。"""
    meta, log, store = _setup(tmp_path, "a")
    rs = _RecordingResultStore()
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(), result_store=rs)  # 起 a
    _done_events(log, "a")
    done = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(20), result_store=rs)
    assert done is TickOutcome.COMMITTED
    assert [(jr.scope_id, jr.status) for jr in rs.saved] == [("a", Status.PASSED)]
    state = store.load_run_state("run-1")
    assert (state.status, state.ended_at, state.message) == (Status.PASSED, _iso(20), None)
    assert state.jobs["a"].result_id == rs.id_of("a")


def test_tick_nonzero_exit_commits_error(tmp_path):
    """job 非0退出（机制二）→ 该 job error → run 按取法为 error。"""
    meta, log, store = _setup(tmp_path, "a")
    rs = _RecordingResultStore()
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(), result_store=rs)
    _done_events(log, "a", exit_code=1)  # 内容 passed 但进程非干净退出
    done = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(20), result_store=rs)
    assert done is TickOutcome.COMMITTED
    assert store.load_run_state("run-1").status == Status.ERROR


def test_tick_after_commit_reads_existing_terminal(tmp_path):
    """run 成为终态之后再 tick：读到既有终态即停（ADR 0034 机制三「run 级状态只进不退」条④），终态只写一次（ended_at 仍首次）。

    两次结果都让宿主结束推进：首次是这一方的写使 run 成为终态（宿主写报告），第二次是 run 已结束（宿主不写报告）——
    status --wait 的接力不会因「别人已使 run 成为终态」永远等不到结束（据 status --wait 死循环的实际运行复现修正）。"""
    meta, log, store = _setup(tmp_path, "a")
    rs = _RecordingResultStore()
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(), result_store=rs)
    _done_events(log, "a")
    d1 = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(20), result_store=rs)
    d2 = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(30), result_store=rs)
    assert d1 is TickOutcome.COMMITTED and d2 is TickOutcome.ENDED
    assert store.load_run_state("run-1").ended_at == _iso(20)  # 终态只写一次（首次的时刻，未被第二次覆盖）
    assert len(rs.saved) == 1  # 读到既有终态的那一轮不再存明细


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
    launcher, rs = FakeLauncher(), _RecordingResultStore()

    outcome = tick("run-1", meta, log, store, launcher, max_concurrency=2, clock=Clock(), result_store=rs)

    assert outcome is TickOutcome.ENDED
    assert launcher.launched == [] and rs.saved == []
    assert store.writes == [] and log.record_reads == 0
    assert store.load_run_state("run-1") == before


def test_commit_lost_to_another_advancer_ends_without_a_result(tmp_path):
    """终态写写不成（并发推进器在本轮读 baseline 之后先使 run 成为终态）：终态写报告 run 在这次写之前已是终态，返回 ENDED、不另读，
    宿主不生成报告；这一方的明细照常先存下（写序不变），但没被点名；库中的终态与点名都是先写成的那一方的（ADR 0034 机制三「run 级
    状态只进不退」条④第 6 步与同条 K2，ADR 0030 决定三「被点名的那一份」条）。"""

    class _LosesCommit(LocalRunStore):
        def __init__(self, root) -> None:
            super().__init__(root)
            self.results: list[CommitOutcome] = []

        def commit_job_states(self, run_id, job_states, *, ended_at):
            # 另一推进器先写成：它点名的是它自己那次保存的标识
            super().commit_job_states(run_id, [replace(js, result_id="00000000000000ff") for js in job_states],
                                      ended_at="other")
            self.results.append(super().commit_job_states(run_id, job_states, ended_at=ended_at))
            return self.results[-1]

    meta, log, store = _setup(tmp_path, "a", store=_LosesCommit(tmp_path))
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(), result_store=_RecordingResultStore())
    _done_events(log, "a")
    rs = _RecordingResultStore()

    outcome = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(20), result_store=rs)

    assert outcome is TickOutcome.ENDED
    assert store.results == [CommitOutcome.ALREADY_ENDED]  # 本实例确实写输
    assert [jr.scope_id for jr in rs.saved] == ["a"]
    state = store.load_run_state("run-1")
    assert state.status == Status.PASSED and state.ended_at == "other"
    assert state.jobs["a"].result_id == "00000000000000ff" != rs.id_of("a")


def test_commit_finding_the_run_ended_elsewhere_stops_without_claiming(any_store, tmp_path):
    """终态写返回 ALREADY_ENDED（读运行态之后、终态写之前，别处以结束写结束了 run）：返回 ENDED，之后不认领、不启动，也不另读；
    明细在终态写之前已存下（写序不变），没被点名：结束写不点名，a 由它记为 aborted、不带标识。仍有 pending 的 job 也不再提议启动。"""
    meta, log, store = _setup(tmp_path, "a", "b", store=any_store)
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(0, 1),
         result_store=_RecordingResultStore())  # 起 a
    _done_events(log, "a")
    store.clear()
    store.before["commit_job_states"] = lambda: store.inner.end_run(
        "run-1", RUN_ENDINGS["settle-advancer-exited"], ended_at="other")
    launcher, rs = FakeLauncher(), _RecordingResultStore()

    outcome = tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(10), result_store=rs)

    assert outcome is TickOutcome.ENDED
    assert store.writes == ["project_state", "commit_job_states"]  # 没有认领
    assert launcher.launched == [] and [jr.scope_id for jr in rs.saved] == ["a"]
    state = store.load_run_state("run-1")
    assert (state.status, state.ended_at, state.jobs["a"].status, state.jobs["b"].status) == (
        Status.ABORTED, "other", Status.ABORTED, Status.SKIPPED)
    assert (state.jobs["a"].result_id, state.jobs["b"].result_id) == (None, None)


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
    launcher, rs = FakeLauncher(), _RecordingResultStore()
    store.armed = True

    assert tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(),
                result_store=rs) is TickOutcome.CONTINUE
    assert launcher.launched == []  # 认领被「run 未结束」条件挡下
    assert tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(),
                result_store=rs) is TickOutcome.ENDED
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
    boom, rs = BoomLauncher(), _RecordingResultStore()
    # tick1：两个 job 都被 claim、launch 都抛异常——异常不向外抛出、补偿落 task_exited
    assert tick("run-1", meta, log, store, boom, max_concurrency=2, clock=Clock(),
                result_store=rs) is TickOutcome.CONTINUE
    assert boom.attempts == ["a", "b"]  # 第一个失败不拖垮第二个（失败隔离）
    # tick2：重放看到退出码未知 → 两 job ERROR → 一次终态写记下两者，run 随之成为终态
    assert tick("run-1", meta, log, store, boom, max_concurrency=2, clock=Clock(5),
                result_store=rs) is TickOutcome.COMMITTED
    state = store.load_run_state("run-1")
    assert state.status == Status.ERROR
    assert all(js.status == Status.ERROR for js in state.jobs.values())
    assert boom.attempts == ["a", "b"]  # 不重复 launch（已 ERROR、plan_next 不再提议）


def test_launch_failure_records_unknown_exit_with_the_same_reason_as_the_foreground(tmp_path):
    """launch 抛错的补偿与前台起 worker 失败交给终结函数的输入相同：退出码未知、原因是「起 worker 失败：异常文本」，不再用平台哨兵
    退出码；退出时刻是失败时取的那一刻（截止时刻之前），不带超时标志；job 的说明就是这句原因，与前台逐字相同。"""
    from gherkai_core.project import project_full

    meta, log, store = _setup(tmp_path, "a")
    tick("run-1", meta, log, store, BoomLauncher(), max_concurrency=1, clock=Clock(), result_store=_RecordingResultStore())
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
    tick("run-1", meta, log, store, BoomLauncher(clock, then=1000), max_concurrency=1, clock=clock,
         result_store=_RecordingResultStore())
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
    hb, rs = HalfBoom(), _RecordingResultStore()
    tick("run-1", meta, log, store, hb, max_concurrency=2, clock=Clock(), result_store=rs)
    assert hb.launched == ["b"]  # b 照常起
    _done_events(log, "b")  # b 运行完成 passed
    assert tick("run-1", meta, log, store, hb, max_concurrency=2, clock=Clock(5),
                result_store=rs) is TickOutcome.COMMITTED
    state = store.load_run_state("run-1")
    assert state.jobs["a"].status == Status.ERROR
    assert state.jobs["b"].status == Status.PASSED
    assert state.status == Status.ERROR  # 任一 error → run error（ADR 0031 决定三）


# ---------- 逐 job 写序：判定明细先存、终态写后写并点名它，推进决策在终态写之后（ADR 0030 决定三「后台推进同守」条与「点名」条，
# ADR 0034 机制三「run 级状态只进不退」条④的步骤）----------

class _OrderRecordingRunStore(LocalRunStore):
    def __init__(self, root, seq: list) -> None:
        super().__init__(root)
        self.seq = seq

    def commit_job_states(self, run_id, job_states, *, ended_at):
        self.seq.append(("commit", tuple((js.scope_id, js.status) for js in job_states),
                         {js.scope_id: js.result_id for js in job_states}))
        return super().commit_job_states(run_id, job_states, ended_at=ended_at)


def test_verdicts_are_saved_before_the_terminal_write(tmp_path):
    """同一轮两个 job 都有结果：ResultStore 各 job 判定明细**先**落，再一次终态写记下这一轮的全部终态（ADR 0030 决定三「后台推进同守」
    条）——看到终态即保证它点名的那一份已存下；反序在 detached 下崩在中间就是永久缺失（无人重试）。每个 job 的明细各用一个标识，终态写
    给出的正是这些标识，运行态随之点名（同决定三「点名」条）。"""
    seq: list = []
    meta, log, store = _setup(tmp_path, "a", "b", store=_OrderRecordingRunStore(tmp_path, seq))
    rs = _RecordingResultStore(seq)
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(), result_store=rs)
    _done_events(log, "a"); _done_events(log, "b", base=10)
    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(5),
                result_store=rs) is TickOutcome.COMMITTED
    kinds = [x[0] for x in seq]
    assert kinds == ["verdict", "verdict", "commit"], seq
    assert seq[-1][1] == (("a", Status.PASSED), ("b", Status.PASSED))  # 一次写记下这一轮全部的终态
    assert seq[-1][2] == dict(rs.ids) and rs.id_of("a") != rs.id_of("b")
    state = store.load_run_state("run-1")
    assert {sid: js.result_id for sid, js in state.jobs.items()} == dict(rs.ids)
    assert all(jr.status == Status.PASSED for jr in rs.saved) and state.status == Status.PASSED


def test_a_job_that_ends_first_is_committed_in_its_own_round_and_the_run_stays_open(any_store, tmp_path):
    """两个 job 先后结束：先结束的那一轮由终态写记下它（终态写只收到它一个），run 仍为 running；另一个 job 结束的那一轮使 run 成为
    终态，结束时刻是这一轮的轮首时刻。先写下的 a 点名的标识在 b 的终态写之后原样保留（云端那次写整体替换 jobs，同样带上它）。"""
    meta, log, store = _setup(tmp_path, "a", "b", store=any_store)
    rs = _RecordingResultStore()
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(0, 1, 2), result_store=rs)  # 起 a、b
    _done_events(log, "a")
    store.clear()

    first = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(10), result_store=rs)

    assert first is TickOutcome.CONTINUE
    assert store.commits == [(("a", Status.PASSED),)]
    state = store.load_run_state("run-1")
    assert (state.status, state.ended_at, state.jobs["a"].status, state.jobs["b"].status) == (
        Status.RUNNING, None, Status.PASSED, Status.RUNNING)
    assert state.jobs["a"].claimed_at == _iso(1)  # 终态写保留认领时刻
    assert (state.jobs["a"].result_id, state.jobs["b"].result_id) == (rs.id_of("a"), None)

    _done_events(log, "b", base=10)
    second = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(20), result_store=rs)

    assert second is TickOutcome.COMMITTED
    assert store.commits[-1] == (("b", Status.PASSED),)
    state = store.load_run_state("run-1")
    assert (state.status, state.ended_at) == (Status.PASSED, _iso(20))
    assert (state.jobs["a"].result_id, state.jobs["b"].result_id) == (rs.id_of("a"), rs.id_of("b"))


def test_a_freed_slot_is_used_in_the_same_round(any_store, tmp_path):
    """并发上限为 1、a 结束而 b 未启动：同一轮先写下 a 的终态，再在加上这次写的作用的运行态上决策、认领 b，不停住（推进决策若只看这一轮
    读到的运行态，a 仍占着并发位，b 要等下一次触发）。"""
    meta, log, store = _setup(tmp_path, "a", "b", store=any_store)
    rs = _RecordingResultStore()
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(0, 1), result_store=rs)  # 起 a
    _done_events(log, "a")
    store.clear()
    launcher = FakeLauncher()

    outcome = tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(10, 11), result_store=rs)

    assert outcome is TickOutcome.CONTINUE
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

    tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(), result_store=_RecordingResultStore())

    assert launcher.launched == ["a"]


def test_verdict_write_failure_fails_tick_before_commit_and_retry_heals(tmp_path):
    """判定真值落库失败 → 异常原样抛出、**未**写终态（job 与 run 仍为 running，不点名）；下一轮 tick（触发源重试）成功落完并写下终态，
    点名的是这一轮存下的那一份。若反过来先写终态再落，失败发生在终态写之后就没有下一轮了。"""
    seq: list = []
    meta, log, store = _setup(tmp_path, "a")
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(), result_store=_RecordingResultStore())
    _done_events(log, "a")
    with pytest.raises(OSError):
        tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(5),
             result_store=_RecordingResultStore(seq, fail=True))
    state = store.load_run_state("run-1")
    assert (state.status, state.jobs["a"].status, state.jobs["a"].result_id) == (Status.RUNNING, Status.RUNNING, None)
    healthy = _RecordingResultStore(seq)
    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(6),
                result_store=healthy) is TickOutcome.COMMITTED
    state = store.load_run_state("run-1")
    assert [jr.scope_id for jr in healthy.saved] == ["a"] and state.status == Status.PASSED
    assert state.jobs["a"].result_id == healthy.id_of("a")


class _FailsOnSecondSave(_RecordingResultStore):
    """存下第一份之后，此后的每次保存都失败。"""

    def save_job_result(self, run_id, result_id, jr):
        if self.saved:
            raise OSError("S3 不可达")
        super().save_job_result(run_id, result_id, jr)


def test_later_verdict_write_failure_leaves_the_run_uncommitted(tmp_path):
    """前一个 job 的判定已保存、后一个 job 的保存失败：异常原样抛出，这一轮没有发出终态写，两个 job 与 run 都仍为 running，已存下的那一份
    没被点名；重试的一轮另生成标识、保存完全部判定之后才写终态，点名的是重试这一轮的标识（ADR 0034 机制三「run 级状态只进不退」条④
    K3；ADR 0030 决定三「保存明细失败」条与「后台推进同守」条）。"""
    seq: list = []
    meta, log, store = _setup(tmp_path, "a", "b", store=_OrderRecordingRunStore(tmp_path, seq))
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(), result_store=_RecordingResultStore())
    _done_events(log, "a"); _done_events(log, "b", base=10)
    failing = _FailsOnSecondSave(seq)
    with pytest.raises(OSError):
        tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(5), result_store=failing)
    assert [x[0] for x in seq] == ["verdict"]  # 前一个保存了，没有终态写
    state = store.load_run_state("run-1")
    assert (state.status, state.jobs["a"].status, state.jobs["b"].status) == (Status.RUNNING, Status.RUNNING, Status.RUNNING)
    assert (state.jobs["a"].result_id, state.jobs["b"].result_id) == (None, None)
    retry = _RecordingResultStore(seq)
    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(6),
                result_store=retry) is TickOutcome.COMMITTED
    assert [x[0] for x in seq] == ["verdict", "verdict", "verdict", "commit"]
    state = store.load_run_state("run-1")
    assert state.status == Status.PASSED
    assert (state.jobs["a"].result_id, state.jobs["b"].result_id) == (retry.id_of("a"), retry.id_of("b"))
    assert state.jobs["a"].result_id != failing.id_of("a")


def test_a_round_that_cannot_save_a_verdict_starts_no_job(any_store, tmp_path):
    """保存明细失败的那一轮不认领、不启动：两个执行中的 job 都有结果，第二份存不成时原样抛出，没有终态写、没有认领，仍有的 pending
    不被启动，执行中的 job（含已存下明细的）留在 running。重试的一轮重存全部、一次写下，再用腾出的并发位启动 pending 的 job。"""
    meta, log, store = _setup(tmp_path, "a", "b", "c", store=any_store)
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(),
         result_store=_RecordingResultStore())  # 起 a、b
    _done_events(log, "a"); _done_events(log, "b", base=10)
    store.clear()
    launcher = FakeLauncher()

    with pytest.raises(OSError):
        tick("run-1", meta, log, store, launcher, max_concurrency=2, clock=Clock(5), result_store=_FailsOnSecondSave())

    assert store.writes == ["project_state"] and launcher.launched == []
    state = store.load_run_state("run-1")
    assert [state.jobs[s].status for s in ("a", "b", "c")] == [Status.RUNNING, Status.RUNNING, Status.PENDING]
    assert state.status == Status.RUNNING

    healthy = _RecordingResultStore()
    store.clear()
    assert tick("run-1", meta, log, store, launcher, max_concurrency=2, clock=Clock(6),
                result_store=healthy) is TickOutcome.CONTINUE
    assert [jr.scope_id for jr in healthy.saved] == ["a", "b"]
    assert store.commits == [(("a", Status.PASSED), ("b", Status.PASSED))]
    assert store.writes == ["project_state", "commit_job_states", "try_claim_job"] and launcher.launched == ["c"]
    state = store.load_run_state("run-1")
    assert (state.jobs["a"].result_id, state.jobs["b"].result_id) == (healthy.id_of("a"), healthy.id_of("b"))


# ---------- 按 job 判断快照（ADR 0054 决策二后台推进条「快照」）----------

@pytest.mark.parametrize("deadline_at, at", [(FAR_DEADLINE, 10), (_NEAR, 41)], ids=["未过停止启动", "已过停止启动"])
def test_a_job_claimed_after_the_read_is_not_committed_this_round(any_store, tmp_path, deadline_at, at):
    """同一轮两个 job 都有结果，一个在这一轮读到的运行态里带认领时刻，另一个是读运行态之后才被别处认领的（读到的运行态里它是
    pending、不带认领时刻）：只为前者存明细、写终态，后者这一轮不写明细、不写终态，下一轮读到新的运行态再写。后者在决策用的运行态里
    仍是 pending：未过停止启动的时刻时多一次被认领条件挡下的启动提议；已过而没有别的执行中的 job 时多一次没写成的到期结束写（库中它
    是 running），重读之后继续推进。"""
    meta, log, store = _setup(tmp_path, "a", "b", deadline_at=deadline_at, store=any_store)
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(0, 1),
         result_store=_RecordingResultStore())  # 起 a
    _done_events(log, "a")

    def _other_advancer_claims_and_b_finishes():
        assert store.inner.try_claim_job("run-1", "b", claimed_at=_iso(5)) is True
        _done_events(log, "b", base=10)

    store.clear()
    store.after["load_run_state"] = _other_advancer_claims_and_b_finishes
    rs, launcher = _RecordingResultStore(), FakeLauncher()

    outcome = tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(at), result_store=rs)

    assert outcome is TickOutcome.CONTINUE
    assert [jr.scope_id for jr in rs.saved] == ["a"] and store.commits == [(("a", Status.PASSED),)]
    assert launcher.launched == []
    assert store.writes == ["project_state", "commit_job_states",
                            "try_claim_job" if deadline_at == FAR_DEADLINE else "end_run"]
    state = store.load_run_state("run-1")
    assert (state.status, state.jobs["a"].status, state.jobs["b"].status, state.message) == (
        Status.RUNNING, Status.PASSED, Status.RUNNING, None)

    done = tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(at + 1), result_store=rs)

    assert done is TickOutcome.COMMITTED
    assert [jr.scope_id for jr in rs.saved] == ["a", "b"]
    state = store.load_run_state("run-1")
    assert (state.status, state.message, state.jobs["b"].claimed_at) == (Status.PASSED, None, _iso(5))
    assert (state.jobs["a"].result_id, state.jobs["b"].result_id) == (rs.id_of("a"), rs.id_of("b"))


@pytest.mark.parametrize("claimed_at", [None, "t1", "2030-01-01T00:00:00"])
def test_job_without_a_readable_claim_time_is_not_committed_this_round(tmp_path, claimed_at):
    """运行态里的认领时刻缺、读不出或不带时区的 job（ADR 0054 决策二后台推进条「快照」）：投影为终态也不存明细、不写终态，按继续推进
    处理；没有「按预算说明」的回落。对照：同样的事件、运行态里带认领时刻的 run 照常写下终态。"""
    meta, log, store = _setup(tmp_path, "a", store=_SpyRunStore(tmp_path))
    store.update_job_state("run-1", JobState("a", Status.RUNNING, claimed_at=claimed_at))
    _done_events(log, "a")
    rs = _RecordingResultStore()

    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(5),
                result_store=rs) is TickOutcome.CONTINUE
    assert rs.saved == [] and "commit_job_states" not in store.writes
    assert store.load_run_state("run-1").status == Status.RUNNING

    control_dir = tmp_path / "control"
    control_dir.mkdir()
    meta, log, store = _setup(control_dir, "a", store=_SpyRunStore(control_dir))
    store.update_job_state("run-1", JobState("a", Status.RUNNING, claimed_at=_iso(0)))
    _done_events(log, "a")
    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(6),
                result_store=rs) is TickOutcome.COMMITTED
    assert [jr.scope_id for jr in rs.saved] == ["a"]


# ---------- 两个推进器重叠，各记一部分 job（ADR 0034 机制三「run 级状态只进不退」条④；ADR 0030 决定三「被点名的那一份」条）----------

@pytest.mark.parametrize("first", ["partial", "complete"])
def test_overlapping_advancers_each_commit_a_part_and_exactly_one_commits_the_run(any_store, tmp_path, first):
    """两个推进器读到的事件快照不同：P 只看到 a 有结果（passed），Q 看到 a（进程非干净退出，error）与 b 都有结果。固定先后：一方读完
    运行态之后、写下终态之前，另一方走完一整轮。两方的明细存进同一处判定存储、各用自己的标识，互不覆盖。

    先写成的是 P（first=partial）时，P 记下 a、run 仍未结束，返回继续推进；Q 再写时 a 已是终态被跳过、记下 b 之后 run 成为终态，Q 返回
    COMMITTED。先写成的是 Q 时，Q 使 run 成为终态；P 的终态写返回 ALREADY_ENDED，P 返回 ENDED。两种先后下都恰有一方得到 COMMITTED，
    run 的结束时刻是它这一轮的轮首时刻；运行态里 a 点名的是先写成的那一方的标识，报告按点名读回的 a 正是那一份、与 a 的终态一致，后写
    一方为 a 存下的那一份不被读。"""
    meta, log_p, store = _setup(tmp_path, "a", "b", store=any_store)
    tick("run-1", meta, log_p, store, FakeLauncher(), max_concurrency=2, clock=Clock(0, 1, 2),
         result_store=_RecordingResultStore())  # 起 a、b
    _done_events(log_p, "a")
    log_q = SqliteEventLog(tmp_path / "q.db")
    _done_events(log_q, "a", exit_code=1); _done_events(log_q, "b", base=10)
    shared = LocalResultStore(tmp_path / "results")
    rs = {"P": _RecordingResultStore(inner=shared), "Q": _RecordingResultStore(inner=shared)}
    results: dict[str, TickOutcome] = {}

    def _run(name, log, at):
        def go():
            results[name] = tick("run-1", meta, log, store.inner, FakeLauncher(), max_concurrency=2, clock=Clock(at),
                                 result_store=rs[name])
        return go

    if first == "partial":
        store.before["commit_job_states"] = _run("P", log_p, 10)  # Q 读完运行态、写终态之前，P 走完一轮
        results["Q"] = tick("run-1", meta, log_q, store, FakeLauncher(), max_concurrency=2, clock=Clock(20),
                            result_store=rs["Q"])
        expected, a_by, a_status = {"P": TickOutcome.CONTINUE, "Q": TickOutcome.COMMITTED}, "P", Status.PASSED
    else:
        store.before["commit_job_states"] = _run("Q", log_q, 20)  # P 读完运行态、写终态之前，Q 走完一轮
        results["P"] = tick("run-1", meta, log_p, store, FakeLauncher(), max_concurrency=2, clock=Clock(10),
                            result_store=rs["P"])
        expected, a_by, a_status = {"P": TickOutcome.ENDED, "Q": TickOutcome.COMMITTED}, "Q", Status.ERROR
    later = "Q" if a_by == "P" else "P"

    assert results == expected
    assert list(results.values()).count(TickOutcome.COMMITTED) == 1
    state = store.load_run_state("run-1")
    assert (state.status, state.ended_at, state.jobs["a"].status, state.jobs["b"].status) == (
        a_status, _iso(20), a_status, Status.PASSED)  # b passed：run 的状态随 a 的终态
    assert (state.jobs["a"].result_id, state.jobs["b"].result_id) == (rs[a_by].id_of("a"), rs["Q"].id_of("b"))
    assert rs[later].id_of("a") != rs[a_by].id_of("a")  # 后写一方也存下了一份
    assert len(list((tmp_path / "results" / "run-1" / "jobs").iterdir())) == 3

    reader, reports = _RecordingResultStore(inner=shared), _Report()
    write_report_from_record(meta, store.inner, reader, reports, created_at="t")
    ((_run_id, result, _created_at),) = reports.written
    assert sorted(reader.loads) == sorted([rs[a_by].id_of("a"), rs["Q"].id_of("b")])
    assert [(o.scope_id, o.status, o.detail.status) for o in result.jobs] == [
        ("a", a_status, a_status), ("b", Status.PASSED, Status.PASSED)]


# ---------- 报告：使 run 成为终态的那一方从记录生成，明细一律按运行态里点名的标识读回
# （ADR 0027「ReportStore 接口：整 run 一次写」节；ADR 0034 机制三「run 级状态只进不退」条④ K2）----------

class _Report:
    def __init__(self) -> None:
        self.written: list = []

    def write(self, run_id, result, *, created_at):
        self.written.append((run_id, result, created_at))


def test_report_comes_from_the_record_and_the_named_details_not_from_a_second_read_of_the_events(tmp_path):
    """报告从记录组装：状态取运行态，判定明细取运行态点名的那一份；之后事件再变（接力方补写的未知退出被真实退出码覆盖之类），报告里的
    判定仍是记下终态时存下的那一份。run 级墙钟由运行态的起止算出。"""
    meta, log, store = _setup(tmp_path, "a")
    rs = _RecordingResultStore()
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(), result_store=rs)
    _done_events(log, "a")
    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(5),
                result_store=rs) is TickOutcome.COMMITTED
    log.record_exit("a", 1)  # 提交之后退出记录被改写：再读一次事件重算会得出 error
    reports = _Report()
    write_report_from_record(meta, store, rs, reports, created_at="2030-01-01T00:00:06+00:00")
    ((run_id, result, created_at),) = reports.written
    assert (run_id, result.status, result.jobs[0].status, result.details[0].status) == (
        "run-1", Status.PASSED, Status.PASSED, Status.PASSED)
    assert rs.loads == [rs.id_of("a")]
    assert result.duration_ms == 5000.0  # 运行态的 started_at（T0）到 ended_at（T0+5）
    assert created_at == "2030-01-01T00:00:06+00:00"


def test_report_follows_the_committing_round_when_two_advancers_read_different_snapshots(tmp_path):
    """两个推进器读到不同的快照、竞争使 run 成为终态（ADR 0034 机制三「run 级状态只进不退」条④ K1、K2）。固定先后：B 读完运行态、读
    事件之前，A 走完一轮并写成终态；B 随后按自己的快照（只有补写的未知退出，判超时）存下明细、发出终态写，终态写报告 run 已结束。A 写成、
    返回 COMMITTED；B 返回 ENDED；run 级的状态、说明与结束时刻是 A 写下的。两方的明细存进同一处、各用自己的标识，B 存下的那一份与 A 的
    互不覆盖（ADR 0034 机制三「判定明细」条），运行态点名 A 的那一份，从记录生成的报告只读它，是 A 的判定（ADR 0030 决定三「点名」条）。"""
    meta, log_a, store = _setup(tmp_path, "a")
    tick("run-1", meta, log_a, store, FakeLauncher(), max_concurrency=1, clock=Clock(),
         result_store=_RecordingResultStore())  # 认领并启动 a
    _done_events(log_a, "a")  # A 读到的快照：完整的结果，判 passed
    shared = LocalResultStore(tmp_path)
    rs_a, rs_b = _RecordingResultStore(inner=shared), _RecordingResultStore(inner=shared)

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

    assert log_b.committed is TickOutcome.COMMITTED
    assert outcome_b is TickOutcome.ENDED  # B 读运行态时 run 未结束：发出了终态写、终态写报告 run 已结束
    assert [jr.status for jr in rs_a.saved] == [Status.PASSED] and [jr.status for jr in rs_b.saved] == [Status.ERROR]
    state = store.load_run_state("run-1")
    assert (state.status, state.ended_at, state.message) == (Status.PASSED, _iso(20), None)
    assert state.jobs["a"].result_id == rs_a.id_of("a") != rs_b.id_of("a")
    assert _job_files(tmp_path) == sorted([f"{rs_a.id_of('a')}.json", f"{rs_b.id_of('a')}.json"])

    reader, reports = _RecordingResultStore(inner=shared), _Report()
    write_report_from_record(meta, store, reader, reports, created_at="2030-01-01T00:00:21+00:00")
    ((_run_id, result, _created_at),) = reports.written
    assert reader.loads == [rs_a.id_of("a")]
    assert (result.status, [o.status for o in result.jobs], [jr.status for jr in result.details]) == (
        Status.PASSED, [Status.PASSED], [Status.PASSED])


def test_report_reads_only_the_details_named_in_the_run_state(tmp_path):
    """报告的明细按运行态里点名的标识读回，较早轮次与最后一轮写下终态的 job 读法相同；由到期的结束写记 skipped 的 job 没有标识，一次都
    不读、报告里不带明细。"""
    meta, log, store = _setup(tmp_path, "a", "b", "c", deadline_at=_NEAR)
    rs = _RecordingResultStore(inner=LocalResultStore(tmp_path))
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(0, 1, 2), result_store=rs)  # 起 a、b
    _done_events(log, "a")
    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(41),
                result_store=rs) is TickOutcome.CONTINUE  # 记下 a；b 仍在执行，不做结束写
    _done_events(log, "b", base=10)
    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(42),
                result_store=rs) is TickOutcome.COMMITTED
    state = store.load_run_state("run-1")
    assert [state.jobs[s].status for s in ("a", "b", "c")] == [Status.PASSED, Status.PASSED, Status.SKIPPED]
    assert state.jobs["c"].result_id is None

    reports = _Report()
    write_report_from_record(meta, store, rs, reports, created_at="t")
    ((_run_id, result, _created_at),) = reports.written
    assert sorted(rs.loads) == sorted([rs.id_of("a"), rs.id_of("b")])
    assert [(o.scope_id, o.status, o.detail is not None) for o in result.jobs] == [
        ("a", Status.PASSED, True), ("b", Status.PASSED, True), ("c", Status.SKIPPED, False)]


def test_report_generation_failures_are_isolated(tmp_path, caplog):
    """生成报告的各步都在失败隔离之内（ADR 0030 决定三「ReportStore.write 失败隔离」注）：写报告失败、为组装而读运行态失败、运行态不存在、
    从判定存储读回明细失败、被点名的那一份读不到，都不击穿已到终态的 run，也不抛出，各留一条警告；没有报告落点时什么都不做、不读运行态，
    也不读回明细。"""

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

        def load_job_result(self, run_id, result_id):
            self.loads += 1
            raise OSError("S3 不可达")

    meta, log, store = _setup(tmp_path, "a", "b")
    rs = LocalResultStore(tmp_path)
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(), result_store=rs)
    _done_events(log, "a")
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(4), result_store=rs)  # 较早一轮记下 a
    _done_events(log, "b", base=10)
    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(5),
                result_store=rs) is TickOutcome.COMMITTED

    reports = _Report()
    with caplog.at_level(logging.WARNING, logger="gherkai_core.reconcile"):
        write_report_from_record(meta, store, rs, _Boom(), created_at="t")
        write_report_from_record(meta, _ReadFails(tmp_path), rs, reports, created_at="t")
        write_report_from_record(meta, LocalRunStore(tmp_path / "elsewhere"), rs, reports, created_at="t")
        failing = _LoadFails()
        write_report_from_record(meta, store, failing, reports, created_at="t")
        assert failing.loads == 1
        (tmp_path / "run-1" / "jobs" / f"{store.load_run_state('run-1').jobs['b'].result_id}.json").unlink()
        write_report_from_record(meta, store, rs, reports, created_at="t")
    assert reports.written == []
    warnings = [r for r in caplog.records if r.getMessage() == "这个 run 的报告没有生成：run=run-1"]
    assert len(warnings) == 5
    assert isinstance(warnings[-1].exc_info[1], NamedDetailMissing)

    counting, untouched = _Counting(tmp_path), _LoadFails()
    write_report_from_record(meta, counting, untouched, None, created_at="t")
    assert counting.reads == 0 and untouched.loads == 0


# ---------- 接力补写的超时退出（ADR 0034「job timeout」节「`timed_out` 归因链」）----------

def test_a_relay_written_timeout_is_committed_and_a_later_real_exit_changes_nothing(tmp_path):
    """接力补写一条带超时标志、退出码未知的退出记录之后，下一轮由这一轮的快照存下明细（预算到点：error 加 timeout）再以终态写记下、
    点名它；之后才到的真实退出覆盖了退出记录，但运行态里这个 job 已是终态、不再被选中：记录、点名与存下的明细都不变，也不再另存一份。"""
    meta, log, store = _setup(tmp_path, "a", "b", store=_SpyRunStore(tmp_path))
    rs = LocalResultStore(tmp_path)
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(), result_store=rs)  # 起 a、b
    assert log.record_timed_out_if_absent("a") is True

    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(400),
                result_store=rs) is TickOutcome.CONTINUE
    named = store.load_run_state("run-1").jobs["a"]
    saved = rs.load_job_result("run-1", named.result_id)
    assert (saved.status, saved.error_type) == (Status.ERROR, "timeout")
    assert named.status == Status.ERROR

    _done_events(log, "a")  # 真实的退出（干净退出、内容完整）在补写之后到达，覆盖了退出记录
    store.writes.clear()
    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(401),
                result_store=rs) is TickOutcome.CONTINUE
    assert store.writes == ["project_state"]  # 没有终态写
    assert store.load_run_state("run-1").jobs["a"] == named
    assert rs.load_job_result("run-1", named.result_id) == saved
    assert _job_files(tmp_path) == [f"{named.result_id}.json"]


def test_overlapping_advancers_leave_the_relay_timeout_in_the_run_state(tmp_path):
    """两个推进方重叠：认领方的一轮读完运行态（a 仍在执行）之后，接力方完整推进一轮，按补写的超时退出存下 a 的明细并记下终态（error）；
    随后 a 的真实退出（干净退出、内容完整）到达，认领方这一轮读到的是它，另存一份 passed 的明细，按旧的运行态为 a 发出终态写。运行态里
    a 的终态不变，run 仍未结束；a 点名的仍是接力方的那一份（error、超时），认领方存下的那一份不被点名，被点名的明细与终态一致。"""
    meta, log, inner = _setup(tmp_path, "a", "b")
    shared = LocalResultStore(tmp_path)
    relay, owner_rs = _RecordingResultStore(inner=shared), _RecordingResultStore(inner=shared)
    tick("run-1", meta, log, inner, FakeLauncher(), max_concurrency=2, clock=Clock(), result_store=relay)  # 起 a、b
    assert log.record_timed_out_if_absent("a") is True  # 接力方补写
    owner = _Store(inner)
    outcomes = {}

    def relay_round_then_real_exit():
        outcomes["relay"] = tick("run-1", meta, log, inner, FakeLauncher(), max_concurrency=2, clock=Clock(400),
                                 result_store=relay)
        assert inner.load_run_state("run-1").jobs["a"].status == Status.ERROR  # 接力方已按超时记下 a
        _done_events(log, "a")  # 真实退出在接力方那一轮之后到达，覆盖补写的那一条

    owner.after["load_run_state"] = relay_round_then_real_exit
    outcomes["owner"] = tick("run-1", meta, log, owner, FakeLauncher(), max_concurrency=2, clock=Clock(401),
                             result_store=owner_rs)

    assert outcomes == {"relay": TickOutcome.CONTINUE, "owner": TickOutcome.CONTINUE}
    assert owner.commits == [(("a", Status.PASSED),)]  # 认领方确实按真实退出、在旧的运行态上发出了终态写
    assert [jr.status for jr in owner_rs.saved] == [Status.PASSED]
    state = inner.load_run_state("run-1")
    assert (state.status, state.jobs["a"].status, state.jobs["b"].status) == (Status.RUNNING, Status.ERROR, Status.RUNNING)
    assert state.jobs["a"].result_id == relay.id_of("a") != owner_rs.id_of("a")
    named = shared.load_job_result("run-1", state.jobs["a"].result_id)
    assert (named.status, named.error_type) == (Status.ERROR, "timeout")


# ---------- 到期处理：到期的结束写把未启动的 job 记 skipped 并带到期的说明，run 随之成为终态
# （ADR 0054 决策二第 3 条与后台推进条）----------

def test_past_stop_start_claims_nothing_and_expires_the_run(tmp_path):
    """已过停止启动的时刻，最后一个执行中的 job 在这一轮得出结果，仍有未启动的 job：不认领、不启动；同一轮先写下这个 job 的终态，
    再在加上这次写的作用的运行态上判出「没有执行中的 job」、做到期的结束写——写的次序是投影、终态写、结束写。结束写把未启动的 job
    记 skipped 并带到期的说明、不点名，run 按取法记 aborted、带「已超过允许运行的时间」；返回 COMMITTED，已记下的 job 点名的标识
    原样保留。"""
    meta, log, store = _setup(tmp_path, "a", "b", deadline_at=_NEAR, store=_SpyRunStore(tmp_path))
    launcher, rs = FakeLauncher(), _RecordingResultStore()
    tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(0, 1), result_store=_RecordingResultStore())  # 起 a
    _done_events(log, "a")
    store.writes.clear()

    done = tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(41), result_store=rs)

    assert launcher.launched == ["a"]  # b 没有被认领、没有启动
    assert done is TickOutcome.COMMITTED
    assert [jr.scope_id for jr in rs.saved] == ["a"]
    assert store.writes == ["project_state", "commit_job_states", "end_run"]
    state = store.load_run_state("run-1")
    assert (state.status, state.message, state.ended_at) == (Status.ABORTED, _DEADLINE_ENDING.run_message, _iso(41))
    assert (state.jobs["a"].status, state.jobs["b"].status, state.jobs["b"].message) == (
        Status.PASSED, Status.SKIPPED, _DEADLINE_ENDING.skipped_message)
    assert (state.jobs["a"].result_id, state.jobs["b"].result_id) == (rs.id_of("a"), None)


def test_all_done_after_the_deadline_ends_by_the_terminal_write(tmp_path):
    """没有执行中的、也没有未启动的 job：run 在记下各 job 终态的那次写里随之成为终态，不论是否已过期限，不做结束写、不带到期的说明
    （ADR 0054 决策二第 4 条）。"""
    meta, log, store = _setup(tmp_path, "a", deadline_at=_NEAR, store=_SpyRunStore(tmp_path))
    rs = _RecordingResultStore()
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(0, 1), result_store=rs)
    _done_events(log, "a")
    done = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(500), result_store=rs)
    assert done is TickOutcome.COMMITTED
    assert "commit_job_states" in store.writes and "end_run" not in store.writes
    state = store.load_run_state("run-1")
    assert (state.status, state.message) == (Status.PASSED, None)


def test_past_stop_start_with_a_running_job_continues(tmp_path):
    """已过停止启动的时刻而还有执行中的 job：不认领、不做结束写，继续推进，这一轮只有投影写；执行中的 job 由它的截止时刻停下。"""
    meta, log, store = _setup(tmp_path, "a", "b", deadline_at=_NEAR, store=_SpyRunStore(tmp_path))
    launcher, rs = FakeLauncher(), _RecordingResultStore()
    tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(0, 1), result_store=rs)  # 起 a，a 仍在执行
    store.writes.clear()
    assert tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(41),
                result_store=rs) is TickOutcome.CONTINUE
    assert launcher.launched == ["a"] and store.writes == ["project_state"]


def test_claim_refused_by_the_deadline_triggers_one_replan_in_the_same_round(tmp_path):
    """这一轮里有认领因已过停止启动的时刻而没有做（每次认领前重做检查）：同一轮里重新取时刻、重新读取运行态与事件、按已过停止启动再
    决策一次（ADR 0054 决策二后台推进条「时刻」），满足到期的结束写就当场做，不留给不会再来的下一轮。结束时刻取重新读取之前的
    那一次。"""
    meta, log, store = _setup(tmp_path, "a", deadline_at=_NEAR)
    clock = Clock(0, 50, 51)  # 轮首未过停止启动的时刻（T0+40）；认领前已过；重新读取之前再取一次
    rs = _RecordingResultStore()

    done = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=clock, result_store=rs)

    assert done is TickOutcome.COMMITTED and rs.saved == []  # 一个 job 都没有启动，也没有存明细
    state = store.load_run_state("run-1")
    assert (state.status, state.message, state.ended_at, state.jobs["a"].status, state.jobs["a"].result_id) == (
        Status.ABORTED, _DEADLINE_ENDING.run_message, _iso(51), Status.SKIPPED, None)
    assert clock.reads == 3


@pytest.mark.parametrize("launch_fails, outcome", [(False, TickOutcome.CONTINUE), (True, TickOutcome.COMMITTED)])
def test_replan_counts_the_jobs_claimed_earlier_in_the_round(tmp_path, launch_fails, outcome):
    """重新决策时这一轮里先前认领成功的 job 计入：它在执行中就不做到期的结束写、继续推进；它的启动已失败（补写了退出记录）就在重做的
    那一遍存下它的明细、写下它的终态并点名，随后做到期的结束写，run 有 error 即记 error。重新决策只做一次：只多读一次时钟。"""

    class _Launcher(FakeLauncher):
        def launch(self, job, *, cutoff_at):
            super().launch(job, cutoff_at=cutoff_at)
            if launch_fails:
                raise RuntimeError("boom")

    meta, log, store = _setup(tmp_path, "a", "b", deadline_at=_NEAR, store=_SpyRunStore(tmp_path))
    clock = Clock(0, 1, 50, 51)
    launcher, rs = _Launcher(), _RecordingResultStore()
    done = tick("run-1", meta, log, store, launcher, max_concurrency=2, clock=clock, result_store=rs)
    assert done is outcome and launcher.launched == ["a"]
    assert clock.reads == 4 + (1 if launch_fails else 0)  # 轮首、两次认领前、重新读取前；启动失败时另取一次
    state = store.load_run_state("run-1")
    assert state.jobs["a"].claimed_at == _iso(1)
    if launch_fails:
        assert [jr.scope_id for jr in rs.saved] == ["a"] and state.jobs["a"].result_id == rs.id_of("a")
        assert store.writes == ["project_state", "try_claim_job", "project_state", "commit_job_states", "end_run"]
        assert (state.status, state.message, state.jobs["b"].status) == (Status.ERROR, _DEADLINE_ENDING.run_message, Status.SKIPPED)
    else:
        assert rs.saved == []
        assert store.writes == ["project_state", "try_claim_job", "project_state"]
        assert (state.status, state.jobs["b"].status) == (Status.RUNNING, Status.PENDING)


def test_replan_keeps_what_the_first_pass_committed(any_store, tmp_path):
    """重做的那一遍读到第一遍已记下的终态：不再为它存明细、不再写它的终态，只为这之后才有结果的 job 存、写；重做那一遍做结束写使 run
    成为终态时，两遍各自点名的标识都在运行态里。固定先后：第一遍记下 a，认领 b 而 b 启动失败（补写了退出记录），认领 c 之前已过
    停止启动的时刻；重做的那一遍记下 b，再以到期的结束写结束 c。"""

    class _BFails(FakeLauncher):
        def launch(self, job, *, cutoff_at):
            super().launch(job, cutoff_at=cutoff_at)
            if job.scope_id == "b":
                raise RuntimeError("boom: b")

    meta, log, store = _setup(tmp_path, "a", "b", "c", deadline_at=_NEAR, store=any_store)
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(0, 1),
         result_store=_RecordingResultStore())  # 起 a
    _done_events(log, "a")
    store.clear()
    rs = _RecordingResultStore()
    clock = Clock(30, 31, 32, 50, 51)  # 轮首、认领 b、b 启动失败的退出时刻、认领 c 之前（已过 T0+40）、重新读取之前

    done = tick("run-1", meta, log, store, _BFails(), max_concurrency=2, clock=clock, result_store=rs)

    assert done is TickOutcome.COMMITTED
    assert [jr.scope_id for jr in rs.saved] == ["a", "b"]
    assert store.writes == ["project_state", "commit_job_states", "try_claim_job",
                            "project_state", "commit_job_states", "end_run"]
    assert store.commits == [(("a", Status.PASSED),), (("b", Status.ERROR),)]
    state = store.load_run_state("run-1")
    assert (state.status, state.ended_at, state.message) == (Status.ERROR, _iso(51), _DEADLINE_ENDING.run_message)
    assert [state.jobs[s].status for s in ("a", "b", "c")] == [Status.PASSED, Status.ERROR, Status.SKIPPED]
    assert [state.jobs[s].result_id for s in ("a", "b", "c")] == [rs.id_of("a"), rs.id_of("b"), None]


def test_a_save_failure_in_the_redo_pass_keeps_what_the_first_pass_wrote(any_store, tmp_path):
    """保存失败的保护按「遍」算（从读运行态起算，同一轮的重做是另一遍）：重做那一遍有明细存不成时原样抛出，这一遍不写终态、不认领、
    不做结束写；第一遍已写下的终态、点名与已做的认领不收回（终态只写一次）。固定先后同上一条：第一遍记下 a、认领 b 而 b 启动失败，认领 c
    之前已过停止启动的时刻；重做的那一遍为 b 存明细时失败。"""

    class _BFails(FakeLauncher):
        def launch(self, job, *, cutoff_at):
            super().launch(job, cutoff_at=cutoff_at)
            if job.scope_id == "b":
                raise RuntimeError("boom: b")

    class _CannotSaveB(_RecordingResultStore):
        def save_job_result(self, run_id, result_id, jr):
            if jr.scope_id == "b":
                raise OSError("判定存储写不进")
            super().save_job_result(run_id, result_id, jr)

    meta, log, store = _setup(tmp_path, "a", "b", "c", deadline_at=_NEAR, store=any_store)
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(0, 1),
         result_store=_RecordingResultStore())  # 起 a
    _done_events(log, "a")
    store.clear()
    rs = _CannotSaveB()
    with pytest.raises(OSError, match="判定存储写不进"):
        tick("run-1", meta, log, store, _BFails(), max_concurrency=2, clock=Clock(30, 31, 32, 50, 51), result_store=rs)

    assert [jr.scope_id for jr in rs.saved] == ["a"]
    assert store.writes == ["project_state", "commit_job_states", "try_claim_job", "project_state"]  # 重做那一遍只有投影写
    assert store.commits == [(("a", Status.PASSED),)]
    state = store.load_run_state("run-1")
    assert (state.status, state.ended_at) == (Status.RUNNING, None)
    assert [state.jobs[s].status for s in ("a", "b", "c")] == [Status.PASSED, Status.RUNNING, Status.PENDING]
    assert state.jobs["b"].claimed_at == _iso(31)
    assert (state.jobs["a"].result_id, state.jobs["b"].result_id) == (rs.id_of("a"), None)


def test_no_writes_and_no_event_reads_in_a_round_that_cannot_read_the_run_state(tmp_path):
    """读不到运行态的那一轮返回继续推进，不读事件、不写任何东西：认领、投影与结束写都写不成，终态写会抛错（ADR 0054 决策二后台推进条
    「收尾与报告」）。已过停止启动的时刻也不做到期的结束写，也不存明细。"""
    meta = _meta("a", deadline_at=_NEAR)
    store = _SpyRunStore(tmp_path)  # 没有建 run：运行态读不到
    log, launcher, rs = _CountingEventLog(tmp_path / "e.db"), FakeLauncher(), _RecordingResultStore()
    outcome = tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(50), result_store=rs)
    assert outcome is TickOutcome.CONTINUE
    assert store.writes == [] and log.record_reads == 0 and launcher.launched == [] and rs.saved == []


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
    rs = _RecordingResultStore()
    tick("run-1", meta, plain, store, FakeLauncher(), max_concurrency=1, clock=Clock(0, 1), result_store=rs)  # 起 a
    _done_events(plain, "a")
    log = _ClaimLandsAfterRead(tmp_path / "e.db", store, "b")

    outcome = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(41), result_store=rs)

    assert log.landed is True
    assert outcome is TickOutcome.CONTINUE
    assert store.writes.count("end_run") == 1  # 结束写确实发出
    state = store.load_run_state("run-1")
    assert (state.status, state.claim_count, state.jobs["a"].status, state.jobs["b"].status) == (
        Status.RUNNING, 2, Status.PASSED, Status.RUNNING)
    assert state.message is None
