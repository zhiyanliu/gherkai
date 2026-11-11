"""reconciler tick 测试（ADR 0034）：推进编排 + 幂等 + CAS 起 job + finalize。

用真 SqliteEventLog + LocalRunStore + fake Launcher（记录被 launch 的 job，不起真进程）验证 tick 逻辑：
- 首 tick 从全 pending 起首批（≤max_concurrency）；
- worker 事件落 log 后 tick 推进态、起下一个；
- 全部两件都要齐 → finalize；
- 幂等：重复 tick 不重复 launch（CAS 挡）；
- 结果三种（TickOutcome）：继续推进 / 本轮走完收尾分支（条件写赢或输都算）/ 读到既有终态（不推演）。
纯编排逻辑（launch 被 fake）→ 绿即够；真进程脱离 / SQLite 并发是真实运行边界。
"""
from __future__ import annotations

from gherkai_core.adapters.event_log import SqliteEventLog
from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.model import Job, JobState, RunMeta, RunState, Scenario, Status, Step
from gherkai_core.project import project_full
from gherkai_core.reconcile import TickOutcome, tick


class FakeLauncher:
    def __init__(self) -> None:
        self.launched: list[str] = []
        self.claimed_at: dict[str, str] = {}

    def launch(self, job: Job, *, claimed_at: str) -> None:
        self.launched.append(job.scope_id)
        self.claimed_at[job.scope_id] = claimed_at


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
    """给某 scope 落「运行完成 passed + 干净退出」的完整事件序列。"""
    log.append_event(sid, base, f'{{"type":"scope_started","scopeId":"{sid}","sessionId":"s"}}', 1.0)
    log.append_event(sid, base + 1, f'{{"type":"scenario_done","scenarioId":"{sid}:1","status":"passed"}}', 2.0)
    log.append_event(sid, base + 2, f'{{"type":"scope_done","scopeId":"{sid}"}}', 3.0)
    log.record_exit(sid, 0)


def test_first_tick_starts_up_to_concurrency(tmp_path):
    meta, log, store = _setup(tmp_path, "a", "b", "c")
    launcher = FakeLauncher()
    done = tick("run-1", meta, log, store, launcher, max_concurrency=2, now_iso="t1")
    assert done is TickOutcome.CONTINUE
    assert len(launcher.launched) == 2  # 起首批 2 个
    # 被 claim 的两个在 RunStore 里是 running
    state = store.load_run_state("run-1")
    running = [s for s, js in state.jobs.items() if js.status == Status.RUNNING]
    assert len(running) == 2


def test_launch_receives_the_claim_timestamp(tmp_path):
    """launch 收到的 claimed_at 就是认领落库的那个时间戳（ADR 0034「job timeout」节：预算从认领起算，
    云端的到点时刻按它取 deadline）——不是 launch 时另取的时刻。"""
    meta, log, store = _setup(tmp_path, "a", "b")
    launcher = FakeLauncher()
    tick("run-1", meta, log, store, launcher, max_concurrency=2, now_iso="t1")
    state = store.load_run_state("run-1")
    assert launcher.claimed_at == {"a": "t1", "b": "t1"}
    assert all(state.jobs[s].claimed_at == launcher.claimed_at[s] for s in ("a", "b"))


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
    # a 运行结束
    _done_events(log, "a")
    tick("run-1", meta, log, store, launcher, max_concurrency=2, now_iso="t2")
    # a 完成腾位 → c 被起
    assert "c" in launcher.launched
    state = store.load_run_state("run-1")
    assert state.jobs["a"].status == Status.PASSED


def test_tick_finalizes_when_all_done(tmp_path):
    """全部 job 两件都要齐 → tick 返回 FINALIZED 且 RunStore finalize 成终态。"""
    meta, log, store = _setup(tmp_path, "a")
    launcher = FakeLauncher()
    tick("run-1", meta, log, store, launcher, max_concurrency=2, now_iso="t1")  # 起 a
    _done_events(log, "a")
    done = tick("run-1", meta, log, store, launcher, max_concurrency=2, now_iso="t2")
    assert done is TickOutcome.FINALIZED
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
    assert done is TickOutcome.FINALIZED
    assert store.load_run_state("run-1").status == Status.ERROR


def test_tick_after_commit_reads_existing_terminal(tmp_path):
    """收尾之后再 tick：读到既有终态即停（ADR 0034 机制三「run 级状态只进不退」条④），commit 只一次（ended_at 仍首次）。

    两次结果都让宿主结束推进：首次是本轮走完收尾分支（宿主写报告），第二次是读到既有终态（宿主不写报告）——
    接力推进器（status --wait）不会因「别人已 finalize」永远等不到结束（据 status --wait 死循环的实际运行复现修正）。"""
    meta, log, store = _setup(tmp_path, "a")
    launcher = FakeLauncher()
    tick("run-1", meta, log, store, launcher, max_concurrency=2, now_iso="t1")
    _done_events(log, "a")
    d1 = tick("run-1", meta, log, store, launcher, max_concurrency=2, now_iso="t2")
    d2 = tick("run-1", meta, log, store, launcher, max_concurrency=2, now_iso="t3")
    assert d1 is TickOutcome.FINALIZED and d2 is TickOutcome.ALREADY_TERMINAL
    assert store.load_run_state("run-1").ended_at == "t2"  # commit 仍恰一次（首次的 t2，未被 t3 覆盖）


class _SpyRunStore(LocalRunStore):
    """真 LocalRunStore，另记下 tick 发出的写（投影、认领、收尾）。"""

    def __init__(self, root) -> None:
        super().__init__(root)
        self.writes: list[str] = []

    def project_state(self, run_id, state):
        self.writes.append("project_state")
        return super().project_state(run_id, state)

    def try_claim_job(self, run_id, scope_id, *, claimed_at=None):
        self.writes.append("try_claim_job")
        return super().try_claim_job(run_id, scope_id, claimed_at=claimed_at)

    def try_finalize(self, run_id, status, ended_at, *, message=None):
        self.writes.append("try_finalize")
        return super().try_finalize(run_id, status, ended_at, message=message)


class _CountingEventLog(SqliteEventLog):
    def __init__(self, path) -> None:
        super().__init__(path)
        self.record_reads = 0

    def records(self):
        self.record_reads += 1
        return super().records()


def test_tick_on_finalized_run_with_pending_jobs_reads_existing_terminal(tmp_path):
    """库中 run 已收尾（error）而 job 仍 pending（definition 不可用时的收尾形态）：tick 返回 ALREADY_TERMINAL，
    不读事件、不投影、不认领、不启动、不落判定真值（ADR 0034 机制三「run 级状态只进不退」条④）。

    不判停时，认领被条件挡下、plan_next 每轮都提议 start，tick 每轮都返回 CONTINUE，本机推进循环不会结束。"""
    meta = _meta("a", "b")
    log = _CountingEventLog(tmp_path / "e.db")
    store = _SpyRunStore(tmp_path)
    store.create_run(meta, RunState(run_id="run-1", status=Status.PENDING,
                                    jobs={s: JobState(s, Status.PENDING) for s in ("a", "b")},
                                    started_at="t0", high_water_mark=0))
    assert store.try_finalize("run-1", Status.ERROR, "t1", message="definition 不可用") is True
    store.writes.clear()
    _done_events(log, "a")  # 库里有事件也不读
    before = store.load_run_state("run-1")
    launcher, rs = FakeLauncher(), _RecordingResultStore([])

    outcome = tick("run-1", meta, log, store, launcher, max_concurrency=2, now_iso="t2", result_store=rs)

    assert outcome is TickOutcome.ALREADY_TERMINAL
    assert launcher.launched == [] and rs.saved == []
    assert store.writes == [] and log.record_reads == 0
    assert store.load_run_state("run-1") == before


def test_finalize_branch_counts_as_finalized_when_commit_lost(tmp_path):
    """收尾分支的 try_finalize 写输（并发推进器在本轮读 baseline 之后先提交了终态）：仍返回 FINALIZED，
    判定真值照落；库中终态是先提交的那一份（ADR 0034 机制三「run 级状态只进不退」条④：写赢或写输都算本轮走完收尾分支）。"""

    class _LosesCommit(LocalRunStore):
        def __init__(self, root) -> None:
            super().__init__(root)
            self.results: list[bool] = []

        def try_finalize(self, run_id, status, ended_at, *, message=None):
            super().try_finalize(run_id, status, "other")  # 另一推进器先提交
            self.results.append(super().try_finalize(run_id, status, ended_at, message=message))
            return self.results[-1]

    meta = _meta("a")
    log = SqliteEventLog(tmp_path / "e.db")
    store = _LosesCommit(tmp_path)
    store.create_run(meta, RunState(run_id="run-1", status=Status.PENDING,
                                    jobs={"a": JobState("a", Status.PENDING)}, started_at="t0", high_water_mark=0))
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, now_iso="t1")
    _done_events(log, "a")
    rs = _RecordingResultStore([])

    outcome = tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, now_iso="t2", result_store=rs)

    assert outcome is TickOutcome.FINALIZED
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

    meta = _meta("a")
    log = SqliteEventLog(tmp_path / "e.db")
    store = _FinalizedRightAfterRead(tmp_path)
    store.create_run(meta, RunState(run_id="run-1", status=Status.PENDING,
                                    jobs={"a": JobState("a", Status.PENDING)}, started_at="t0", high_water_mark=0))
    launcher = FakeLauncher()
    store.armed = True

    assert tick("run-1", meta, log, store, launcher, max_concurrency=1, now_iso="t1") is TickOutcome.CONTINUE
    assert launcher.launched == []  # 认领被「run 未收尾」条件挡下
    assert tick("run-1", meta, log, store, launcher, max_concurrency=1, now_iso="t2") is TickOutcome.ALREADY_TERMINAL
    state = store.load_run_state("run-1")
    assert state.status == Status.ERROR and state.jobs["a"].status == Status.PENDING


class BoomLauncher:
    """launch 必抛的 fake（RunTask 放置失败/task-def 配错/Popen OSError 的抽象）。"""

    def __init__(self) -> None:
        self.attempts: list[str] = []

    def launch(self, job: Job, *, claimed_at: str) -> None:
        self.attempts.append(job.scope_id)
        raise RuntimeError(f"boom: {job.scope_id}")


def test_launch_failure_does_not_wedge_run(tmp_path):
    """launch 抛异常 → 补偿记非0退出 → 下轮判 ERROR 收敛，run 不 wedge（ADR 0034 机制二推论）。"""
    meta, log, store = _setup(tmp_path, "a", "b")
    boom = BoomLauncher()
    # tick1：两个 job 都被 claim、launch 都抛异常——异常不向外抛出、补偿落 task_exited
    done = tick("run-1", meta, log, store, boom, max_concurrency=2, now_iso="t1")
    assert done is TickOutcome.CONTINUE
    assert boom.attempts == ["a", "b"]  # 第一个失败不拖垮第二个（失败隔离）
    # tick2：重放看到退出码非零 → 两 job ERROR → 全终态 → finalize，run 收敛
    done = tick("run-1", meta, log, store, boom, max_concurrency=2, now_iso="t2")
    assert done is TickOutcome.FINALIZED
    state = store.load_run_state("run-1")
    assert state.status == Status.ERROR
    assert all(js.status == Status.ERROR for js in state.jobs.values())
    assert boom.attempts == ["a", "b"]  # 不重复 launch（已 ERROR、plan_next 不再提议）


def test_launch_failure_reason_reaches_job_message(tmp_path):
    """launch 抛错的异常文本随退出记录进 job message（与同步路径同句），使用方能看到起不来的原因。"""
    meta, log, store = _setup(tmp_path, "a")
    tick("run-1", meta, log, store, BoomLauncher(), max_concurrency=1, now_iso="t1")
    (jr,) = project_full(meta, log.records()).jobs
    assert jr.status == Status.ERROR
    assert "起 worker 失败：boom: a" in (jr.message or "")


def test_launch_failure_isolated_other_job_completes(tmp_path):
    """一个 job 起不来，另一个照常运行完成——失败隔离 + 聚合 ERROR。"""

    class HalfBoom:
        def __init__(self) -> None:
            self.launched: list[str] = []

        def launch(self, job: Job, *, claimed_at: str) -> None:
            if job.scope_id == "a":
                raise RuntimeError("boom: a")
            self.launched.append(job.scope_id)

    meta, log, store = _setup(tmp_path, "a", "b")
    hb = HalfBoom()
    tick("run-1", meta, log, store, hb, max_concurrency=2, now_iso="t1")
    assert hb.launched == ["b"]  # b 照常起
    _done_events(log, "b")  # b 运行完成 passed
    done = tick("run-1", meta, log, store, hb, max_concurrency=2, now_iso="t2")
    assert done is TickOutcome.FINALIZED
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

    def try_finalize(self, run_id, status, ended_at, *, message=None):
        self.seq.append(("finalize", status))
        return super().try_finalize(run_id, status, ended_at, message=message)


def test_finalize_writes_verdicts_before_commit_point(tmp_path):
    """全 done 的 tick：ResultStore 各 job 判定真值**先**落，再 try_finalize（ADR 0030 决定三写序）——看到终态即
    保证 jobs/*.json 已齐；反序在 detached 下崩在中间就是永久缺失（无人重试）。"""
    seq: list = []
    meta = _meta("a", "b")
    log = SqliteEventLog(tmp_path / "e.db")
    store = _OrderRecordingRunStore(tmp_path, seq)
    store.create_run(meta, RunState(run_id="run-1", status=Status.PENDING,
                                    jobs={s: JobState(s, Status.PENDING) for s in ("a", "b")},
                                    started_at="t0", high_water_mark=0))
    rs = _RecordingResultStore(seq)
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, now_iso="t1", result_store=rs)
    _done_events(log, "a"); _done_events(log, "b", base=10)
    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=2, now_iso="t2", result_store=rs) is TickOutcome.FINALIZED
    kinds = [x[0] for x in seq]
    assert kinds == ["verdict", "verdict", "finalize"], seq
    assert all(jr.status == Status.PASSED for jr in rs.saved) and store.load_run_state("run-1").status == Status.PASSED


def test_verdict_write_failure_fails_tick_before_commit_and_retry_heals(tmp_path):
    """判定真值落库失败 → 异常原样抛出、**未** commit（状态仍 running）；下一轮 tick（触发源重试）成功落完并 commit。
    若反过来先 CAS 再落，失败发生在 commit 之后就没有下一轮了。"""
    import pytest
    seq: list = []
    meta, log, store = _setup(tmp_path, "a")
    tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, now_iso="t1")
    _done_events(log, "a")
    with pytest.raises(OSError):
        tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, now_iso="t2",
             result_store=_RecordingResultStore(seq, fail=True))
    assert store.load_run_state("run-1").status == Status.RUNNING  # 没 commit
    healthy = _RecordingResultStore(seq)
    assert tick("run-1", meta, log, store, FakeLauncher(), max_concurrency=1, now_iso="t3", result_store=healthy) is TickOutcome.FINALIZED
    assert [jr.scope_id for jr in healthy.saved] == ["a"] and store.load_run_state("run-1").status == Status.PASSED


def test_finalize_report_passes_run_duration_into_the_report(tmp_path):
    """收尾报告带宿主算好的 run 级墙钟（RunState started_at→ended_at）。"""
    from gherkai_core.reconcile import finalize_report

    meta, log, store = _setup(tmp_path, "a")
    _done_events(log, "a")
    seen = {}

    class _Report:
        def write(self, run_id, result, *, created_at):
            seen["duration_ms"] = result.duration_ms

    finalize_report("run-1", meta, log, _Report(), "t9", run_duration_ms=4200.0)
    assert seen["duration_ms"] == 4200.0
