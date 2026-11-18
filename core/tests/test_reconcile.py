"""reconciler tick 测试（ADR 0034、ADR 0054 决策二后台推进条）：推进编排 + 幂等 + CAS 起 job + 收尾 + 到期处理。

用真 SqliteEventLog + LocalRunStore + fake Launcher（记录被 launch 的 job，不起真进程）与注入的假墙钟验证 tick 逻辑：
- 首 tick 从全 pending 起首批（≤max_concurrency），每次认领前另取一次时刻作认领时刻，截止时刻随 launch 交出；
- worker 事件落 log 后 tick 推进态、起下一个；全部结束 → 收尾；
- 幂等：重复 tick 不重复 launch（CAS 挡）；
- 已过停止启动的时刻：不认领；没有执行中的 job、余下的都没启动 → 到期收尾，条件写带认领计数；
- 同一轮里认领因已过停止启动而没做时重新决策一次；快照里有记录的 job 缺认领时刻时不收尾；
- 结果三种（TickOutcome）：继续推进 / 这一方写成收尾（带结果）/ run 已结束而不是这一方写成（不带结果）。
纯编排逻辑（launch 被 fake、时钟被注入）→ 绿即够；真进程脱离 / SQLite 并发是真实运行边界。
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from gherkai_core.adapters.event_log import SqliteEventLog
from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step
from gherkai_core.project import DEADLINE_TIMEOUT_MESSAGE
from gherkai_core.reconcile import TickOutcome, TickResult, finalize_report, tick
from gherkai_core.run_deadline import RUN_DEADLINE_PASSED_MESSAGE
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


def _initial(*sids: str) -> RunState:
    return RunState(run_id="run-1", status=Status.PENDING, jobs={s: JobState(s, Status.PENDING) for s in sids},
                    started_at="t0", high_water_mark=0)


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
    """一个 job 完成（两件都要齐）后，tick 腾出并发位、起下一个 pending。"""
    meta, log, store = _setup(tmp_path, "a", "b", "c")
    launcher = FakeLauncher()
    tick("run-1", meta, log, store, launcher, max_concurrency=2, clock=Clock())  # 起 a,b
    _done_events(log, "a")
    tick("run-1", meta, log, store, launcher, max_concurrency=2, clock=Clock(10))
    assert "c" in launcher.launched  # a 完成腾位 → c 被起
    assert store.load_run_state("run-1").jobs["a"].status == Status.PASSED


def test_tick_commits_when_all_done(tmp_path):
    """全部 job 两件都要齐 → 这一方写成收尾：返回 COMMITTED 且带结果，RunStore 落成终态，ended_at 是这一轮读运行态之前取的时刻。"""
    meta, log, store = _setup(tmp_path, "a")
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock())  # 起 a
    _done_events(log, "a")
    done = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(20))
    assert done.outcome is TickOutcome.COMMITTED
    assert (done.result.status, done.result.message, [jr.scope_id for jr in done.result.jobs]) == (Status.PASSED, None, ["a"])
    state = store.load_run_state("run-1")
    assert (state.status, state.ended_at, state.message) == (Status.PASSED, _iso(20), None)


def test_tick_nonzero_exit_finalizes_error(tmp_path):
    """job 非0退出（机制二）→ 该 job error → run 收尾为 error。"""
    meta, log, store = _setup(tmp_path, "a")
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock())
    _done_events(log, "a", exit_code=1)  # 内容 passed 但进程非干净退出
    done = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(20))
    assert done.outcome is TickOutcome.COMMITTED
    assert store.load_run_state("run-1").status == Status.ERROR


def test_tick_after_commit_reads_existing_terminal(tmp_path):
    """收尾之后再 tick：读到既有终态即停（ADR 0034 机制三「run 级状态只进不退」条④），commit 只一次（ended_at 仍首次）。

    两次结果都让宿主结束推进：首次是这一方写成收尾（宿主写报告），第二次是 run 已结束（宿主不写报告）——
    接力推进器（status --wait）不会因「别人已收尾」永远等不到结束（据 status --wait 死循环的实际运行复现修正）。"""
    meta, log, store = _setup(tmp_path, "a")
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock())
    _done_events(log, "a")
    d1 = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(20))
    d2 = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(30))
    assert d1.outcome is TickOutcome.COMMITTED and d2 == TickResult(TickOutcome.ENDED)
    assert store.load_run_state("run-1").ended_at == _iso(20)  # commit 仍恰一次（首次的时刻，未被第二次覆盖）


class _SpyRunStore(LocalRunStore):
    """真 LocalRunStore，另记下 tick 发出的写（投影、认领、收尾）与收尾写带的认领计数条件。"""

    def __init__(self, root) -> None:
        super().__init__(root)
        self.writes: list[str] = []
        self.finalize_counts: list[int | None] = []

    def project_state(self, run_id, state):
        self.writes.append("project_state")
        return super().project_state(run_id, state)

    def try_claim_job(self, run_id, scope_id, *, claimed_at=None):
        self.writes.append("try_claim_job")
        return super().try_claim_job(run_id, scope_id, claimed_at=claimed_at)

    def try_finalize(self, run_id, status, ended_at, *, message=None, expected_claim_count=None):
        self.writes.append("try_finalize")
        self.finalize_counts.append(expected_claim_count)
        return super().try_finalize(run_id, status, ended_at, message=message, expected_claim_count=expected_claim_count)


class _CountingEventLog(SqliteEventLog):
    def __init__(self, path) -> None:
        super().__init__(path)
        self.record_reads = 0

    def records(self):
        self.record_reads += 1
        return super().records()


def test_tick_on_finalized_run_with_pending_jobs_reads_existing_terminal(tmp_path):
    """库中 run 已收尾（error）而 job 仍 pending（definition 不可用时的收尾形态）：tick 返回 ENDED，
    不读事件、不投影、不认领、不启动、不落判定真值（ADR 0034 机制三「run 级状态只进不退」条④）。

    不判停时，认领被条件挡下、plan_next 每轮都提议 start，tick 每轮都返回 CONTINUE，本机推进循环不会结束。"""
    meta = _meta("a", "b")
    log = _CountingEventLog(tmp_path / "e.db")
    store = _SpyRunStore(tmp_path)
    store.create_run(meta, _initial("a", "b"))
    assert store.try_finalize("run-1", Status.ERROR, "t1", message="definition 不可用") is True
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
    """收尾写写不成（并发推进器在本轮读 baseline 之后先提交了终态）：重读到终态，返回 ENDED、不带结果，宿主不生成报告；判定真值照落
    （写序不变）；库中终态是先提交的那一份（ADR 0054 决策二后台推进条「收尾与报告」）。"""

    class _LosesCommit(LocalRunStore):
        def __init__(self, root) -> None:
            super().__init__(root)
            self.results: list[bool] = []

        def try_finalize(self, run_id, status, ended_at, *, message=None, expected_claim_count=None):
            super().try_finalize(run_id, status, "other")  # 另一推进器先提交
            self.results.append(super().try_finalize(run_id, status, ended_at, message=message,
                                                     expected_claim_count=expected_claim_count))
            return self.results[-1]

    meta, log, store = _setup(tmp_path, "a", store=_LosesCommit(tmp_path))
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock())
    _done_events(log, "a")
    rs = _RecordingResultStore([])

    outcome = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(20), result_store=rs)

    assert outcome == TickResult(TickOutcome.ENDED)
    assert store.results == [False]  # 本实例确实写输
    assert [jr.scope_id for jr in rs.saved] == ["a"]
    state = store.load_run_state("run-1")
    assert state.status == Status.PASSED and state.ended_at == "other"


def test_finalize_inserted_after_baseline_read_continues_then_stops(tmp_path):
    """收尾插在本轮读 baseline 之后：本轮不在判停之内，投影写被终态守卫挡下、认领被条件挡下，返回 CONTINUE；
    下一轮读到终态即停（ADR 0034 机制三「run 级状态只进不退」条④末句）。"""

    class _FinalizedRightAfterRead(LocalRunStore):
        armed = False

        def load_run_state(self, run_id):
            state = super().load_run_state(run_id)
            if self.armed:
                self.armed = False
                assert self.try_finalize(run_id, Status.ERROR, "other") is True
            return state

    meta, log, store = _setup(tmp_path, "a", store=_FinalizedRightAfterRead(tmp_path))
    launcher = FakeLauncher()
    store.armed = True

    assert tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock()).outcome is TickOutcome.CONTINUE
    assert launcher.launched == []  # 认领被「run 未收尾」条件挡下
    assert tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock()).outcome is TickOutcome.ENDED
    state = store.load_run_state("run-1")
    assert state.status == Status.ERROR and state.jobs["a"].status == Status.PENDING


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
    # tick2：重放看到退出码未知 → 两 job ERROR → 全终态 → 收尾，run 收敛
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
    (jr,) = project_full(meta, log.records(), claimed_at=_claimed(store), past_stop_start=False).jobs
    assert (jr.status, jr.error_type, jr.message) == (Status.ERROR, "engine_error", "起 worker 失败：boom: a")


@pytest.mark.parametrize("deadline_at, message", [
    (FAR_DEADLINE, "job 超时（预算 300s，已中止）"),
    (_NEAR, DEADLINE_TIMEOUT_MESSAGE),
])
def test_launch_failure_after_the_cutoff_projects_as_timeout(tmp_path, deadline_at, message):
    """启动调用失败时再取一次时刻，记为退出时刻：补偿只记这个事实、不带超时标志，投影时它晚于这个 job 的截止时刻即按超时处理，与前台
    起 worker 失败的分支得到同一个判定；说明按起作用的那个截止时刻给（预算或期限）。"""
    from gherkai_core.project import project_full

    meta, log, store = _setup(tmp_path, "a", deadline_at=deadline_at)
    clock = Clock(0, 1)
    tick("run-1", meta, log, store, BoomLauncher(clock, then=1000), max_concurrency=1, clock=clock)
    (exit_rec,) = [r.exited for r in log.records() if r.kind == "exit"]
    assert (exit_rec.exit_code, exit_rec.timed_out, exit_rec.exited_at) == (None, False, _at(1000))
    (jr,) = project_full(meta, log.records(), claimed_at=_claimed(store), past_stop_start=True).jobs
    assert (jr.status, jr.error_type, jr.message) == (Status.ERROR, "timeout", message)


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


# ---------- commit-point 写序（ADR 0030 决定三 detached 同守）：判定真值先落、CAS 后 ----------

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

    def try_finalize(self, run_id, status, ended_at, *, message=None, expected_claim_count=None):
        self.seq.append(("finalize", status))
        return super().try_finalize(run_id, status, ended_at, message=message, expected_claim_count=expected_claim_count)


def test_finalize_writes_verdicts_before_commit_point(tmp_path):
    """全 done 的 tick：ResultStore 各 job 判定真值**先**落，再 try_finalize（ADR 0030 决定三写序）——看到终态即
    保证 jobs/*.json 已齐；反序在 detached 下崩在中间就是永久缺失（无人重试）。"""
    seq: list = []
    meta, log, store = _setup(tmp_path, "a", "b", store=_OrderRecordingRunStore(tmp_path, seq))
    rs = _RecordingResultStore(seq)
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(), result_store=rs)
    _done_events(log, "a"); _done_events(log, "b", base=10)
    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(5),
                result_store=rs).outcome is TickOutcome.COMMITTED
    kinds = [x[0] for x in seq]
    assert kinds == ["verdict", "verdict", "finalize"], seq
    assert all(jr.status == Status.PASSED for jr in rs.saved) and store.load_run_state("run-1").status == Status.PASSED


def test_verdict_write_failure_fails_tick_before_commit_and_retry_heals(tmp_path):
    """判定真值落库失败 → 异常原样抛出、**未** commit（状态仍 running）；下一轮 tick（触发源重试）成功落完并 commit。
    若反过来先 CAS 再落，失败发生在 commit 之后就没有下一轮了。"""
    seq: list = []
    meta, log, store = _setup(tmp_path, "a")
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock())
    _done_events(log, "a")
    with pytest.raises(OSError):
        tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(5),
             result_store=_RecordingResultStore(seq, fail=True))
    assert store.load_run_state("run-1").status == Status.RUNNING  # 没 commit
    healthy = _RecordingResultStore(seq)
    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(6),
                result_store=healthy).outcome is TickOutcome.COMMITTED
    assert [jr.scope_id for jr in healthy.saved] == ["a"] and store.load_run_state("run-1").status == Status.PASSED


def test_later_verdict_write_failure_leaves_the_run_uncommitted(tmp_path):
    """前一个 job 的判定已保存、后一个 job 的保存失败（ADR 0034 机制三「run 级状态只进不退」条④ K3）：异常原样抛出，这一轮没有发出
    收尾的条件写，run 仍未结束；重试的一轮保存完全部判定之后才提交。"""

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
    assert [x[0] for x in seq] == ["verdict"]  # 前一个保存了，没有收尾的条件写
    assert store.load_run_state("run-1").status == Status.RUNNING
    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, clock=Clock(6),
                result_store=_RecordingResultStore(seq)).outcome is TickOutcome.COMMITTED
    assert [x[0] for x in seq] == ["verdict", "verdict", "verdict", "finalize"]
    assert store.load_run_state("run-1").status == Status.PASSED


# ---------- 报告（ADR 0054 决策二后台推进条「收尾与报告」）----------

class _Report:
    def __init__(self) -> None:
        self.written: list = []

    def write(self, run_id, result, *, created_at):
        self.written.append((run_id, result, created_at))


def test_report_comes_from_the_committed_result_not_from_a_second_read_of_the_events(tmp_path):
    """报告由写成收尾的那一轮的结果直接生成：之后事件再变（接力方补写的未知退出被真实退出码覆盖之类），报告里的判定仍是提交的那一份；
    run 级墙钟由宿主算好传入。"""
    meta, log, store = _setup(tmp_path, "a")
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock())
    _done_events(log, "a")
    done = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(5))
    log.record_exit("a", 1)  # 提交之后退出记录被改写：再读一次事件重算会得出 error
    reports = _Report()
    finalize_report(done.result, reports, "2030-01-01T00:00:06+00:00", run_duration_ms=4200.0)
    ((run_id, result, created_at),) = reports.written
    assert (run_id, result.status, result.jobs[0].status, result.duration_ms) == ("run-1", Status.PASSED, Status.PASSED, 4200.0)
    assert created_at == "2030-01-01T00:00:06+00:00"


def test_report_follows_the_committing_round_when_two_advancers_read_different_snapshots(tmp_path):
    """两个推进方读到不同的快照、竞争收尾（ADR 0034 机制三「run 级状态只进不退」条④ K1、K2）。固定先后：B 读完运行态、读事件之前，
    A 走完一轮并写成收尾；B 随后按自己的快照走到收尾，条件写写不成。只断言必须成立的正面性质：A 写成、带它这一轮的结果；B 返回不带
    结果的 ENDED；run 级的状态、说明与结束时刻是 A 写下的；用 A 交还的结果生成的报告是 A 的判定。B 落下的判定明细与 A 的谁留在
    存储里不在断言之内（ADR 0034 机制三开头的「判定明细」一条）。"""
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
    assert (outcome_a.result.status, [jr.status for jr in outcome_a.result.jobs]) == (Status.PASSED, [Status.PASSED])
    assert outcome_b == TickResult(TickOutcome.ENDED)  # B 读运行态时 run 未结束：走到了收尾、条件写写不成、重读到终态
    state = store.load_run_state("run-1")
    assert (state.status, state.ended_at, state.message) == (Status.PASSED, _iso(20), None)
    reports = _Report()
    finalize_report(outcome_a.result, reports, "2030-01-01T00:00:21+00:00")
    ((_run_id, result, _created_at),) = reports.written
    assert (result.status, [jr.status for jr in result.jobs]) == (Status.PASSED, [Status.PASSED])


def test_report_write_failure_is_isolated():
    """派生视图写失败不击穿已提交的终态（ADR 0030 决定三）；没有报告落点时什么都不做。"""

    class _Boom:
        def write(self, run_id, result, *, created_at):
            raise OSError("S3 不可达")

    from gherkai_core.model import RunResult
    result = RunResult(run_meta=_meta("a"), status=Status.PASSED)
    finalize_report(result, _Boom(), "t")
    finalize_report(result, None, "t")


# ---------- 到期处理（ADR 0054 决策二后台推进条）----------

def test_past_stop_start_claims_nothing_and_expires_the_run(tmp_path):
    """已过停止启动的时刻、没有执行中的 job、余下的 job 都没有启动：不认领、不启动，到期收尾——已结束的 job 落判定明细，run 级以条件写
    收尾为 error 加「已超过允许运行的时间」，条件带这一轮读到的认领计数；未启动的 job 保持 pending，不在判定清单里。"""
    meta, log, store = _setup(tmp_path, "a", "b", deadline_at=_NEAR, store=_SpyRunStore(tmp_path))
    launcher, rs = FakeLauncher(), _RecordingResultStore([])
    tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(0, 1))  # 起 a
    _done_events(log, "a")

    done = tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(41), result_store=rs)

    assert launcher.launched == ["a"]  # b 没有被认领、没有启动
    assert done.outcome is TickOutcome.COMMITTED
    assert (done.result.status, done.result.message) == (Status.ERROR, RUN_DEADLINE_PASSED_MESSAGE)
    assert [jr.scope_id for jr in done.result.jobs] == ["a"] and [j.scope_id for j in done.result.jobs_without_verdict] == ["b"]
    assert [jr.scope_id for jr in rs.saved] == ["a"]
    assert store.finalize_counts == [1]  # 一次认领之后读到的计数
    state = store.load_run_state("run-1")
    assert (state.status, state.message, state.ended_at) == (Status.ERROR, RUN_DEADLINE_PASSED_MESSAGE, _iso(41))
    assert (state.jobs["a"].status, state.jobs["b"].status) == (Status.PASSED, Status.PENDING)


def test_all_done_after_the_deadline_aggregates_without_the_claim_count_condition(tmp_path):
    """没有执行中的、也没有未启动的 job：照常按各 job 的判定聚合收尾，不管是否已过期限（ADR 0054 决策二第 4 条）；收尾写不带认领计数
    的条件：没有未启动的 job 就不会再有认领。"""
    meta, log, store = _setup(tmp_path, "a", deadline_at=_NEAR, store=_SpyRunStore(tmp_path))
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(0, 1))
    _done_events(log, "a")
    done = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(500))
    assert (done.outcome, done.result.status, done.result.message) == (TickOutcome.COMMITTED, Status.PASSED, None)
    assert store.finalize_counts == [None]


def test_past_stop_start_with_a_running_job_continues(tmp_path):
    """已过停止启动的时刻而还有执行中的 job：不认领、不收尾，继续推进；执行中的 job 由它的截止时刻停下。"""
    meta, log, store = _setup(tmp_path, "a", "b", deadline_at=_NEAR, store=_SpyRunStore(tmp_path))
    launcher = FakeLauncher()
    tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(0, 1))  # 起 a，a 仍在执行
    assert tick("run-1", meta, log, store, launcher, max_concurrency=1, clock=Clock(41)) == TickResult(TickOutcome.CONTINUE)
    assert launcher.launched == ["a"] and "try_finalize" not in store.writes


def test_claim_refused_by_the_deadline_triggers_one_replan_in_the_same_round(tmp_path):
    """这一轮里有认领因已过停止启动的时刻而没有做（每次认领前重做检查）：同一轮里重新取时刻、重新读取运行态与事件、按已过停止启动再
    决策一次（ADR 0054 决策二后台推进条「时刻」），满足到期收尾就当场收尾，不留给不会再来的下一轮。收尾时刻取重新读取之前的那一次。"""
    meta, log, store = _setup(tmp_path, "a", deadline_at=_NEAR)
    clock = Clock(0, 50, 51)  # 轮首未过停止启动的时刻（T0+40）；认领前已过；重新读取之前再取一次

    done = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=clock)

    assert done.outcome is TickOutcome.COMMITTED
    assert (done.result.status, done.result.message, done.result.jobs) == (Status.ERROR, RUN_DEADLINE_PASSED_MESSAGE, [])
    state = store.load_run_state("run-1")
    assert (state.status, state.ended_at, state.jobs["a"].status) == (Status.ERROR, _iso(51), Status.PENDING)
    assert clock.reads == 3


@pytest.mark.parametrize("launch_fails, outcome", [(False, TickOutcome.CONTINUE), (True, TickOutcome.COMMITTED)])
def test_replan_counts_the_jobs_claimed_earlier_in_the_round(tmp_path, launch_fails, outcome):
    """重新决策时这一轮里先前认领成功的 job 计入：它在执行中就不到期收尾、继续推进；它的启动已失败（补写了退出记录）就到期收尾，
    它的判定在清单里。重新决策只做一次：只多读一次时钟。"""

    class _Launcher(FakeLauncher):
        def launch(self, job, *, cutoff_at):
            super().launch(job, cutoff_at=cutoff_at)
            if launch_fails:
                raise RuntimeError("boom")

    meta, log, store = _setup(tmp_path, "a", "b", deadline_at=_NEAR)
    clock = Clock(0, 1, 50, 51)
    launcher = _Launcher()
    done = tick("run-1", meta, log, store, launcher, max_concurrency=2, clock=clock)
    assert done.outcome is outcome and launcher.launched == ["a"]
    assert clock.reads == 4 + (1 if launch_fails else 0)  # 轮首、两次认领前、重新读取前；启动失败时另取一次
    state = store.load_run_state("run-1")
    assert (state.jobs["a"].claimed_at, state.jobs["b"].status) == (_iso(1), Status.PENDING)
    if launch_fails:
        assert [jr.scope_id for jr in done.result.jobs] == ["a"] and state.status == Status.ERROR
        assert state.message == RUN_DEADLINE_PASSED_MESSAGE
    else:
        assert state.status == Status.RUNNING


@pytest.mark.parametrize("claimed_at", [None, "t1", "2030-01-01T00:00:00"])
def test_recorded_job_without_a_claim_time_in_the_snapshot_blocks_the_finalize(tmp_path, claimed_at):
    """快照检查（ADR 0054 决策二后台推进条「快照」）：有记录的 job 在这一轮读到的运行态里不带认领时刻（缺、读不出、不带时区），说明
    手里的运行态比事件旧：不落判定明细、不收尾，按继续推进处理；没有「按预算说明」的回落。读到带认领时刻的运行态之后照常收尾。"""
    meta, log, store = _setup(tmp_path, "a", store=_SpyRunStore(tmp_path))
    store.update_job_state("run-1", JobState("a", Status.RUNNING, claimed_at=claimed_at))
    _done_events(log, "a")
    rs = _RecordingResultStore([])

    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(5),
                result_store=rs) == TickResult(TickOutcome.CONTINUE)
    assert rs.saved == [] and "try_finalize" not in store.writes
    assert store.load_run_state("run-1").status == Status.RUNNING

    store.update_job_state("run-1", JobState("a", Status.PASSED, claimed_at=_iso(0)))
    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(6),
                result_store=rs).outcome is TickOutcome.COMMITTED
    assert [jr.scope_id for jr in rs.saved] == ["a"]


def test_no_expiry_in_a_round_that_cannot_read_the_run_state(tmp_path):
    """读不到运行态的那一轮不做到期收尾（ADR 0054 决策二后台推进条「收尾与报告」），也不写任何东西。"""
    meta = _meta("a", deadline_at=_NEAR)
    store = _SpyRunStore(tmp_path)  # 没有建 run：运行态读不到
    outcome = tick("run-1", meta, SqliteEventLog(tmp_path / "e.db"), store, FakeLauncher(), max_concurrency=1, clock=Clock(50))
    assert outcome == TickResult(TickOutcome.CONTINUE)
    assert "try_finalize" not in store.writes


class _ClaimLandsAfterRead(SqliteEventLog):
    """读事件时另一个推进方的认领恰好落下：它在本轮读运行态之后、收尾写之前认领了 scope（它的时钟落后，还没过停止启动的时刻）。"""

    def __init__(self, path, store, scope: str) -> None:
        super().__init__(path)
        self._store, self._scope, self.landed = store, scope, False

    def records(self):
        recs = super().records()
        if not self.landed:
            self.landed = self._store.try_claim_job("run-1", self._scope, claimed_at=_iso(39))
        return recs


def test_expiry_loses_to_a_claim_that_landed_after_the_read(tmp_path):
    """到期收尾与认领并发（本机）：一个推进方读到「没有执行中的、仍有未启动的」之后，另一个推进方的认领落下——前者的收尾写
    被认领计数的条件挡下，重读到 run 仍未结束，返回继续推进；run 没有结束、新认领的 job 仍是 running。"""
    meta, _, store = _setup(tmp_path, "a", "b", deadline_at=_NEAR, store=_SpyRunStore(tmp_path))
    plain = SqliteEventLog(tmp_path / "e.db")
    tick("run-1", meta, plain, store, FakeLauncher(), max_concurrency=1, clock=Clock(0, 1))  # 起 a
    _done_events(plain, "a")
    log = _ClaimLandsAfterRead(tmp_path / "e.db", store, "b")

    outcome = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, clock=Clock(41))

    assert log.landed is True
    assert outcome == TickResult(TickOutcome.CONTINUE)
    assert store.finalize_counts == [1]  # 收尾写确实发出、带的是读到的计数
    state = store.load_run_state("run-1")
    assert (state.status, state.claim_count, state.jobs["b"].status) == (Status.RUNNING, 2, Status.RUNNING)
    assert state.message is None
