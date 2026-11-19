"""RunPersistence 应用服务直测（ADR 0030）：用 fake store 或本机 store 直接验 core 层不变量。

四刀审计发现 RunPersistence 此前零直接单测（只经 cli 端到端间接覆盖）。这里把它的核心契约钉到 core 层：
逐 job 的提交点（明细先存、终态写后写）/ on_event 只对 ScopeStarted 与非 attempted 的 SessionOpened 刷 RUNNING / finalize 的结束写
（ADR 0031 决定三「结束写」小节）、从记录组装结果、无报告路径与报告失败隔离 / 别处已结束 run 时不覆盖、不写报告 / begin 初始投影 / aborted 血缘保留 / 认领与认领时刻的
保留、重试之前的读、三处发现汇成的停手信号（ADR 0054 决策五）/ 没有记录的执行在内存里按同一套规则组装结果。
末尾几条经 schedule 走完整的前台路径，验运行期限的结束写与「发现 run 已被别处结束之后不再写」。
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from gherkai_core.errors import RunAlreadyEnded
from gherkai_core.model import (
    Job,
    JobResult,
    JobState,
    RunMeta,
    RunState,
    ScenarioDone,
    ScopeStarted,
    StepDone,
    Status,
    Votes,
)
from gherkai_core.persist import FinalizedRun, RunPersistence, result_without_record
from gherkai_core.run_status import RUN_ENDINGS, CommitOutcome
from gherkai_core.schedule import Execution
from gherkai_core.serialize import instant_to_iso
from tests.fake_engine import FAR_DEADLINE

_CLAIMED = datetime(2030, 1, 1, 8, 0, 0, tzinfo=timezone.utc)
_NOW = datetime(2030, 1, 1, 9, 0, 0, tzinfo=timezone.utc)  # 注入落库服务的墙钟：终态写与结束写的结束时刻、报告的生成时刻
_NOW_ISO = instant_to_iso(_NOW)


def _job(scope_id: str) -> Job:
    return Job(scope_id=scope_id, scope_name=scope_id, engine="midscene", scenarios=(), timeout_s=300.0)


def _meta(run_id: str, scope_ids: list[str]) -> RunMeta:
    return RunMeta(run_id=run_id, created_at="t0", jobs=tuple(_job(s) for s in scope_ids), deadline_at=FAR_DEADLINE)


def _jr(scope_id: str, status: Status = Status.PASSED, session_id: str | None = None) -> JobResult:
    return JobResult(job=_job(scope_id), status=status, session_id=session_id)


def _execution(meta: RunMeta, results: list[JobResult], stopped_by=None, duration_ms: float = 1500.0) -> Execution:
    return Execution(run_meta=meta, results=tuple(results), stopped_by=stopped_by, duration_ms=duration_ms)


def _state(meta: RunMeta, statuses: dict[str, Status], *, status: Status, message: str | None = None) -> RunState:
    """一份与运行定义对应的运行态（fake store 读回的那一份）。"""
    return RunState(run_id=meta.run_id, status=status, message=message, started_at="t0", ended_at="t9",
                    jobs={j.scope_id: JobState(j.scope_id, statuses.get(j.scope_id, Status.PENDING)) for j in meta.jobs})


def _recording(*, commit: CommitOutcome = CommitOutcome.ENDED_RUN, end_run_lands: bool = True, recorded=None,
               run_open_at_job_write: bool = True, claim_lands: bool = True):
    """fake RunStore/ResultStore/ReportStore 共享一个有序 calls log：(store, method, 参数)。

    commit：commit_job_states 的返回值。end_run_lands：end_run 是否写成。recorded：load_run_state 读回的运行态。
    run_open_at_job_write：update_job_state 报告的「这次写时 run 级是否仍未结束」。claim_lands：try_claim_job 是否写成。"""
    calls: list = []

    class FakeRunStore:
        def preflight(self): calls.append(("run", "preflight", None))
        def create_run(self, meta, initial_state): calls.append(("run", "create_run", initial_state))
        def update_job_state(self, run_id, js):
            calls.append(("run", "update_job_state", js))
            return run_open_at_job_write
        def commit_job_states(self, run_id, job_states, *, ended_at):
            calls.append(("run", "commit_job_states", (tuple(job_states), ended_at)))
            return commit
        def end_run(self, run_id, ending, *, ended_at):
            calls.append(("run", "end_run", (ending, ended_at)))
            return end_run_lands
        def try_claim_job(self, run_id, scope_id, *, claimed_at=None):
            calls.append(("run", "try_claim_job", (scope_id, claimed_at)))
            return claim_lands
        def load_run_state(self, run_id):
            calls.append(("run", "load_run_state", None))
            return recorded

    class FakeResultStore:
        def preflight(self): calls.append(("result", "preflight", None))
        def save_job_result(self, run_id, jr): calls.append(("result", "save_job_result", jr.scope_id))

    class FakeReportStore:
        def preflight(self): calls.append(("report", "preflight", None))
        def write(self, run_id, result, *, created_at=""):
            calls.append(("report", "write", (result, created_at)))
            return f"file:///fake/{run_id}/index.html"

    return calls, FakeRunStore(), FakeResultStore(), FakeReportStore()


def _methods(calls) -> list[str]:
    return [m for (_, m, _) in calls]


def _local(tmp_path, scope_ids=("s",), report_store=None):
    from gherkai_core.adapters.result_store.local import LocalResultStore
    from gherkai_core.adapters.run_store.local import LocalRunStore

    run_store, result_store = LocalRunStore(tmp_path), LocalResultStore(tmp_path)
    p = RunPersistence("r", run_store, result_store, report_store, clock=lambda: _NOW)
    meta = _meta("r", list(scope_ids))
    p.begin(meta, started_at="t0")
    return p, run_store, result_store, meta


# ---- 决定三：on_job_complete 逐 job 的提交点——明细先存、终态写后写 ----
def test_on_job_complete_saves_result_before_commit():
    calls, run, result, report = _recording(commit=CommitOutcome.OPEN)
    p = RunPersistence("r", run, result, report, clock=lambda: _NOW)
    p.on_job_complete(_jr("a", Status.PASSED))
    # 数据面 save_job_result 严格早于控制面的终态写（逐 job 提交点的核心保证，ADR 0030 决定三）
    assert [(s, m) for (s, m, _) in calls] == [("result", "save_job_result"), ("run", "commit_job_states")]
    (final,), ended_at = calls[1][2]
    assert (final.scope_id, final.status, ended_at) == ("a", Status.PASSED, _NOW_ISO)  # 结束时刻经注入的墙钟取


def test_on_job_complete_rejects_a_non_terminal_result_and_writes_nothing():
    """判定只有终态（ADR 0031 决定一·补）：交来的 JobResult 不是终态即抛 ValueError，明细与终态都不写。"""
    calls, run, result, report = _recording()
    p = RunPersistence("r", run, result, report)
    with pytest.raises(ValueError):
        p.on_job_complete(_jr("a", Status.RUNNING))
    assert calls == []


# ---- on_event 旁路观察者只对 ScopeStarted 或 origin 不是 attempted 的 SessionOpened 刷 RUNNING、其余事件不落库
# （ADR 0030 决定三「实时写时序」的「job 进行中」条）----
def test_on_event_runs_only_on_scope_started():
    # on_event 不再装饰/转发 sink（进度转发是 schedule 的 progress_sink 的事）——它只是事件观察者：
    # 仅 ScopeStarted 触发一次 RUNNING 刷（带血缘），其余事件零落库（否则每个 step 都刷，就成了 RMW 风暴）。
    calls, run, result, report = _recording()
    p = RunPersistence("r", run, result, report)

    p.on_event(ScopeStarted(scope_id="a", session_id="s1"))            # → 刷 RUNNING
    p.on_event(StepDone(scenario_id="a:0", step_index=0, status=Status.PASSED, votes=Votes(1, 1)))  # → 不刷
    p.on_event(ScenarioDone(scenario_id="a:0", status=Status.PASSED))  # → 不刷

    updates = [js for (s, m, js) in calls if m == "update_job_state"]
    assert len(updates) == 1  # 只有 ScopeStarted 触发了一次
    assert updates[0].scope_id == "a" and updates[0].status == Status.RUNNING and updates[0].session_id == "s1"


# ---- 收尾：本进程的终态写已使 run 成为终态时不再写，读一次运行态组装结果；无报告路径 report_index 为 None
# （ADR 0030 决定二 RunPersistence.finalize 一行与决定三「run 结束」一段）----
def test_finalize_without_report_store_gives_no_report_index():
    meta = _meta("r", ["a"])
    calls, run, result, _ = _recording(commit=CommitOutcome.ENDED_RUN, recorded=_state(meta, {"a": Status.PASSED}, status=Status.PASSED))
    p = RunPersistence("r", run, result, report_store=None)  # WebUI/cron 前端可能不注入 report
    p.on_job_complete(_jr("a"))
    finalized = p.finalize(_execution(meta, [_jr("a")]))
    assert isinstance(finalized, FinalizedRun) and finalized.report_index is None
    assert _methods(calls) == ["save_job_result", "commit_job_states", "load_run_state"]  # 终态写已结束 run：不做结束写
    assert (finalized.result.status, [o.status for o in finalized.result.jobs]) == (Status.PASSED, [Status.PASSED])


def test_finalize_with_report_store_returns_the_index_and_writes_the_report_last():
    meta = _meta("r", ["a"])
    calls, run, result, report = _recording(commit=CommitOutcome.ENDED_RUN,
                                            recorded=_state(meta, {"a": Status.PASSED}, status=Status.PASSED))
    p = RunPersistence("r", run, result, report, clock=lambda: _NOW)
    p.on_job_complete(_jr("a"))
    finalized = p.finalize(_execution(meta, [_jr("a")], duration_ms=4200.0))
    assert finalized.report_index == "file:///fake/r/index.html"
    # 读运行态先、ReportStore.write 后（派生视图永远最后）；报告的生成时刻经注入的墙钟取
    assert _methods(calls)[-2:] == ["load_run_state", "write"]
    written, created_at = calls[-1][2]
    assert written is finalized.result and created_at == _NOW_ISO
    assert written.duration_ms == 4200.0 and [jr.scope_id for jr in written.details] == ["a"]


def test_finalize_isolates_report_write_failure(tmp_path):
    # ReportStore.write 失败不击穿已到终态的 run——终态写已落、判定明细在 ResultStore 安然无恙，故 write 抛异常被隔离：
    # report_index 为 None、不冒泡（报告可从记录重建）。
    class BoomReportStore:
        def preflight(self): pass  # 探活 no-op（真 LocalRunStore/ResultStore 已带 preflight）
        def write(self, run_id, result, *, created_at=""):
            raise OSError("磁盘满，报告写不下")

    p, run_store, _, meta = _local(tmp_path, ("s",), report_store=BoomReportStore())
    p.on_job_complete(_jr("s"))
    finalized = p.finalize(_execution(meta, [_jr("s")]))
    assert finalized.report_index is None and finalized.result.status == Status.PASSED
    # 使 run 成为终态的终态写不在隔离范围内：run_state 是 PASSED 加结束时刻
    state = run_store.load_run_state("r")
    assert state is not None and state.status == Status.PASSED and state.ended_at == _NOW_ISO


def test_finalize_read_failure_after_the_run_ended_propagates_without_a_report():
    """本进程使 run 成为终态之后为组装而读运行态的那一次不在报告的失败隔离之内：读失败原样冒泡（按运行期落库失败处理），报告不生成。"""
    meta = _meta("r", ["a"])
    calls, run, result, report = _recording(commit=CommitOutcome.ENDED_RUN)
    boom = OSError("读不回运行态")

    def failing_read(run_id):
        calls.append(("run", "load_run_state", None))
        raise boom

    run.load_run_state = failing_read
    p = RunPersistence("r", run, result, report)
    p.on_job_complete(_jr("a"))
    with pytest.raises(OSError) as exc:
        p.finalize(_execution(meta, [_jr("a")]))
    assert exc.value is boom and "write" not in _methods(calls)


@pytest.mark.parametrize("by", ["commit", "end-write"])
def test_ended_run_tells_whether_this_process_made_the_run_terminal(by):
    """`ended_run` 只在本进程的某次写使 run 成为终态之后为真：终态写返回 ENDED_RUN，或收尾的结束写写成。之前（终态写返回 OPEN、
    还没有收尾）为假；之后为组装而读运行态失败时它仍为真，调用方据此说明记录已是终态。"""
    meta = _meta("r", ["a", "b"] if by == "end-write" else ["a"])
    calls, run, result, report = _recording(commit=CommitOutcome.OPEN if by == "end-write" else CommitOutcome.ENDED_RUN)
    run.load_run_state = lambda run_id: (_ for _ in ()).throw(OSError("读不回运行态"))
    p = RunPersistence("r", run, result, report)
    assert p.ended_run is False
    p.on_job_complete(_jr("a"))
    assert p.ended_run is (by == "commit")
    with pytest.raises(OSError):
        p.finalize(_execution(meta, [_jr("a")], stopped_by="deadline" if by == "end-write" else None))
    assert p.ended_run is True
    assert ("end_run" in _methods(calls)) is (by == "end-write")


def test_ended_run_stays_false_when_the_failure_comes_before_the_run_ends():
    """执行中途存储失败（终态写本身抛错）：没有写使 run 成为终态，`ended_run` 为假，调用方按执行中途的失败说明。"""
    calls, run, result, report = _recording()

    def failing_commit(run_id, job_states, *, ended_at):
        raise OSError("写不进运行态")

    run.commit_job_states = failing_commit
    p = RunPersistence("r", run, result, report)
    with pytest.raises(OSError):
        p.on_job_complete(_jr("a"))
    assert p.ended_run is False


# ---- 收尾的结束写：仍有未结束的 job 时按执行事实交来的来路结束 run ----
def test_finalize_ends_the_remaining_jobs_by_the_stop_source():
    """本进程的终态写没有使 run 成为终态（还有没有启动的 job）：以执行事实交来的来路做结束写（说明表里那一行），结束时刻经注入的墙钟
    取；写成之后读一次运行态，组装结果并生成报告。没有启动的 job 没有明细。"""
    meta = _meta("r", ["a", "b"])
    recorded = _state(meta, {"a": Status.PASSED, "b": Status.SKIPPED}, status=Status.ABORTED,
                      message=RUN_ENDINGS["deadline"].run_message)
    calls, run, result, report = _recording(commit=CommitOutcome.OPEN, recorded=recorded)
    p = RunPersistence("r", run, result, report, clock=lambda: _NOW)
    p.on_job_complete(_jr("a"))
    finalized = p.finalize(_execution(meta, [_jr("a")], stopped_by="deadline"))
    assert ("run", "end_run", (RUN_ENDINGS["deadline"], _NOW_ISO)) in calls
    assert _methods(calls)[-3:] == ["end_run", "load_run_state", "write"]
    out = finalized.result
    assert (out.status, out.message) == (Status.ABORTED, RUN_ENDINGS["deadline"].run_message)
    assert [(o.scope_id, o.status, o.detail is not None) for o in out.jobs] == [("a", Status.PASSED, True), ("b", Status.SKIPPED, False)]


@pytest.mark.parametrize("stopped_by", [None, "ended-elsewhere"])
def test_finalize_without_a_usable_stop_source_is_an_internal_error(stopped_by):
    """仍有未结束的 job，而执行事实没有给出结束它们的来路（为空，或为「已发现 run 被别处结束」而停手信号没有成立）：执行事实不自洽，
    抛 ValueError（与没有记录时同一处检查），不写任何东西、不生成报告。"""
    meta = _meta("r", ["a", "b"])
    calls, run, result, report = _recording(commit=CommitOutcome.OPEN)
    p = RunPersistence("r", run, result, report)
    p.on_job_complete(_jr("a"))
    with pytest.raises(ValueError, match="没有给出可用于结束它们的来路"):
        p.finalize(_execution(meta, [_jr("a")], stopped_by=stopped_by))
    assert _methods(calls) == ["save_job_result", "commit_job_states"]


def test_finalize_end_write_refused_on_a_run_ended_elsewhere_keeps_the_record_and_writes_no_report(tmp_path):
    """本次执行结束之前别处已把 run 结束（这里是处置的结束写），而本进程直到收尾才碰到它：收尾的结束写被已有的终态挡下，读回之后发出
    停手信号、抛 RunAlreadyEnded（带读回的运行态）；已有的终态、结束时刻与说明不被覆盖，不生成报告。本次已存下、终态写也写成的那一份
    明细原样在。用真 LocalRunStore，结束写的条件在 adapter 里。"""
    calls, _, _, report = _recording()
    p, run_store, result_store, meta = _local(tmp_path, ("a", "b"), report_store=report)
    p.on_job_complete(_jr("a", Status.PASSED))
    settled = RUN_ENDINGS["settle-advancer-exited"]
    assert run_store.end_run("r", settled, ended_at="t5") is True

    with pytest.raises(RunAlreadyEnded) as exc:
        p.finalize(_execution(meta, [_jr("a")], stopped_by="interrupt"))
    assert exc.value.run_id == "r"
    assert (exc.value.recorded.status, exc.value.recorded.message) == (Status.ABORTED, settled.run_message)
    assert p.ended_elsewhere() is True
    state = run_store.load_run_state("r")
    assert (state.status, state.ended_at, state.message) == (Status.ABORTED, "t5", settled.run_message)
    assert (state.jobs["a"].status, state.jobs["b"].status) == (Status.PASSED, Status.SKIPPED)
    assert not any(m == "write" for m in _methods(calls))  # 报告不生成
    assert [jr.scope_id for jr in result_store.load_all("r")] == ["a"]


def test_finalize_end_write_refused_without_a_run_state_is_not_reported_as_ended():
    """结束写没有写成而读回发现运行态不存在：不说成「已被记为已结束」，抛 FileNotFoundError；报告同样不生成。"""
    meta = _meta("r", ["a"])
    calls, run, result, report = _recording(end_run_lands=False, recorded=None)
    p = RunPersistence("r", run, result, report)
    with pytest.raises(FileNotFoundError):
        p.finalize(_execution(meta, [], stopped_by="fail-fast"))
    assert _methods(calls) == ["end_run", "load_run_state"]


def test_finalize_end_write_refused_while_a_job_is_still_running_is_an_internal_error():
    """结束写没有写成、读回的 run 仍未结束：说明运行态里有 running 的 job，而本进程的 job 都已结束，是内部不一致，抛 RuntimeError。"""
    meta = _meta("r", ["a"])
    calls, run, result, report = _recording(end_run_lands=False, recorded=_state(meta, {"a": Status.RUNNING}, status=Status.RUNNING))
    p = RunPersistence("r", run, result, report)
    with pytest.raises(RuntimeError):
        p.finalize(_execution(meta, [], stopped_by="fail-fast"))
    assert p.ended_elsewhere() is False and "write" not in _methods(calls)


def test_finalize_end_write_refused_and_the_read_back_failing_raises_the_read_failure():
    """结束写没有写成、随后为判断原因而读回运行态本身失败：读回的异常原样抛出，不说成「已被记为已结束」（这个结论要靠读回，读回没有
    成功）；不生成报告，停手信号不成立，本进程也没有使 run 成为终态。"""
    meta = _meta("r", ["a"])
    calls, run, result, report = _recording(end_run_lands=False)
    boom = OSError("读不回运行态")

    def failing_read(run_id):
        calls.append(("run", "load_run_state", None))
        raise boom

    run.load_run_state = failing_read
    p = RunPersistence("r", run, result, report)
    with pytest.raises(OSError) as exc:
        p.finalize(_execution(meta, [], stopped_by="fail-fast"))
    assert exc.value is boom and not isinstance(exc.value, RunAlreadyEnded)
    assert _methods(calls) == ["end_run", "load_run_state"]  # 没有写报告
    assert p.ended_elsewhere() is False and p.ended_run is False


def test_finalize_after_the_last_terminal_write_ended_the_run_does_not_use_the_stop_source():
    """执行事实带着来路（这里是 fail-fast），而本进程最后一次终态写已使 run 成为终态：收尾不做结束写，run 的状态取读回的运行态，
    结果里没有来路的说明。"""
    meta = _meta("r", ["a"])
    recorded = _state(meta, {"a": Status.ERROR}, status=Status.ERROR)
    calls, run, result, report = _recording(commit=CommitOutcome.ENDED_RUN, recorded=recorded)
    p = RunPersistence("r", run, result, report, clock=lambda: _NOW)
    p.on_job_complete(_jr("a", Status.ERROR))
    finalized = p.finalize(_execution(meta, [_jr("a", Status.ERROR)], stopped_by="fail-fast"))
    assert "end_run" not in _methods(calls)
    assert _methods(calls) == ["save_job_result", "commit_job_states", "load_run_state", "write"]
    assert finalized.result.message is None
    assert finalized.result.status == recorded.status == Status.ERROR


# ---- ADR 0054 决策五：已发现 run 被别处结束之后不存明细、不写终态，收尾不写、不生成报告，抛 RunAlreadyEnded ----
def test_stop_signal_stops_saving_details_and_writing_terminal_states():
    """停手信号成立之后（这里是认领被拒）交来的结果不被采用：不存明细、不写终态。"""
    calls, run, result, report = _recording(claim_lands=False)
    p = RunPersistence("r", run, result, report)
    assert p.claim("a", _CLAIMED) is False and p.ended_elsewhere() is True
    p.on_job_complete(_jr("b", Status.ABORTED))
    assert _methods(calls) == ["try_claim_job"]


def test_terminal_write_that_finds_the_run_ended_raises_the_stop_signal_and_finalize_raises():
    """终态写报告 run 在这次写之前已是终态（ALREADY_ENDED）：发出停手信号；收尾不做结束写、不生成报告，读回一次运行态并抛 RunAlreadyEnded。"""
    meta = _meta("r", ["a", "b"])
    recorded = _state(meta, {"a": Status.ABORTED, "b": Status.SKIPPED}, status=Status.ABORTED)
    calls, run, result, report = _recording(commit=CommitOutcome.ALREADY_ENDED, recorded=recorded)
    p = RunPersistence("r", run, result, report)
    p.on_job_complete(_jr("a"))
    assert p.ended_elsewhere() is True
    with pytest.raises(RunAlreadyEnded) as exc:
        p.finalize(_execution(meta, [_jr("a")], stopped_by="fail-fast"))
    assert exc.value.recorded is recorded
    assert _methods(calls) == ["save_job_result", "commit_job_states", "load_run_state"]


@pytest.mark.parametrize("how", ["claim", "still_open", "running_write", "terminal_write"])
def test_the_stop_signal_is_published_inside_the_store_lock(how):
    """得知 run 已被别处结束的那次存储操作与停手信号的发布在落库服务的同一把锁内完成（四条途径都是）：on_job_complete 也在这把锁内
    先看信号、再存明细，所以信号发布之后才取到锁的回调不会再存一份明细。"""
    ended = RunState(run_id="r", status=Status.ABORTED, jobs={"a": JobState(scope_id="a", status=Status.ABORTED)})
    calls, run, result, report = _recording(claim_lands=False, recorded=ended, run_open_at_job_write=False,
                                            commit=CommitOutcome.ALREADY_ENDED)
    p = RunPersistence("r", run, result, report)
    held: list[bool] = []
    publish = p._ended.set

    def recording_publish():
        held.append(p._lock.locked())
        publish()

    p._ended.set = recording_publish
    if how == "claim":
        assert p.claim("a", _CLAIMED) is False
    elif how == "still_open":
        assert p.still_open() is False
    elif how == "running_write":
        p.on_event(ScopeStarted(scope_id="a"))
    else:
        p.on_job_complete(_jr("a"))
    assert held == [True] and p.ended_elsewhere() is True


def test_a_result_handed_over_while_the_claim_is_being_refused_is_not_saved():
    """下一个 job 的认领正被拒（那次认领写还没有返回）时，主线程把上一个 job 的结果交给落库服务：它要等认领那一步连同停手信号的发布
    做完才取到锁，随后看到信号，不存明细、不写终态。"""
    import threading as _th

    calls, run, result, report = _recording(claim_lands=False)
    p = RunPersistence("r", run, result, report)
    handed: list[_th.Thread] = []
    refuse = run.try_claim_job

    def refusing_claim(run_id, scope_id, *, claimed_at=None):
        t = _th.Thread(target=lambda: p.on_job_complete(_jr("a")))
        handed.append(t)
        t.start()
        t.join(0.3)  # 结果在认领写返回之前交来：它应当停在锁上，这里等不到它结束
        return refuse(run_id, scope_id, claimed_at=claimed_at)

    run.try_claim_job = refusing_claim
    assert p.claim("b", _CLAIMED) is False
    handed[0].join(5.0)
    assert not handed[0].is_alive()
    assert _methods(calls) == ["try_claim_job"]  # 没有 save_job_result，也没有 commit_job_states


def test_finalize_after_the_stop_signal_still_reports_ended_elsewhere_when_the_run_state_is_gone():
    """停手信号成立之后收尾读回发现运行态不存在：run 已被别处结束这个结论来自之前被拒的那次写，不靠读回，仍抛 RunAlreadyEnded
    （recorded 为 None），调用方走同一个出口。"""
    calls, run, result, report = _recording(claim_lands=False, recorded=None)
    p = RunPersistence("r", run, result, report)
    assert p.claim("a", _CLAIMED) is False
    with pytest.raises(RunAlreadyEnded) as exc:
        p.finalize(_execution(_meta("r", ["a"]), [], stopped_by="ended-elsewhere"))
    assert exc.value.recorded is None and exc.value.__cause__ is None
    assert _methods(calls) == ["try_claim_job", "load_run_state"]


def test_finalize_after_the_stop_signal_still_reports_ended_elsewhere_when_the_read_back_fails():
    """停手信号成立之后收尾的那次读回本身失败（如云端的读取报错）：仍抛 RunAlreadyEnded，recorded 为 None、读回的异常是它的起因。
    调用方因此走同一个出口（说明、按信号取的退出码），不会因为多出的这次读得到一个未归类的异常。不做结束写、不生成报告。"""
    calls, run, result, report = _recording(claim_lands=False)
    boom = RuntimeError("读取失败")

    def failing_read(run_id):
        calls.append(("run", "load_run_state", None))
        raise boom

    run.load_run_state = failing_read
    p = RunPersistence("r", run, result, report)
    assert p.claim("a", _CLAIMED) is False
    with pytest.raises(RunAlreadyEnded) as exc:
        p.finalize(_execution(_meta("r", ["a"]), [], stopped_by="ended-elsewhere"))
    assert exc.value.recorded is None and exc.value.run_id == "r"
    assert exc.value.__cause__ is boom
    assert "（" not in str(exc.value)  # 没有读到状态：消息里不留一对空括号
    assert _methods(calls) == ["try_claim_job", "load_run_state"]  # 没有结束写、报告没有写


# ---- 决定二：begin 写初始全 pending 态，jobs Map 与 run_meta 对齐 ----
def test_begin_writes_all_pending_initial_state():
    calls, run, result, report = _recording()
    p = RunPersistence("r", run, result, report)
    p.begin(_meta("r", ["a", "b"]), started_at="t0")
    # create_run 收到的 initial_state：总 pending、各 job pending、key 集与 run_meta 一致、起止按生命周期
    initial = next(arg for (s, m, arg) in calls if m == "create_run")
    assert initial.status == Status.PENDING
    assert set(initial.jobs.keys()) == {"a", "b"}
    assert all(js.status == Status.PENDING for js in initial.jobs.values())
    assert initial.started_at == "t0" and initial.ended_at is None


# ---- 决定五 + 0031 决定一：aborted 的 session_id 经实时写路径保留（卖点：有现场可查）----
def test_aborted_job_preserves_session_id_through_realtime_write(tmp_path):
    # 用真 LocalRunStore（非 fake）验真合并语义：RUNNING 阶段刷了血缘，aborted 终态写不应清掉它。
    p, run_store, _, _ = _local(tmp_path, ("s",))
    # ① ScopeStarted 刷 RUNNING + 血缘（worker 线程经 sink 的路径）
    p.on_event(ScopeStarted(scope_id="s", session_id="sess-1"))
    # ② aborted 终态：in-flight 被掐的 jr 带 session_id（schedule 的 result 已从 ScopeStarted 累积，见 _reduce）
    p.on_job_complete(_jr("s", Status.ABORTED, session_id="sess-1"))
    js = run_store.load_run_state("r").jobs["s"]
    assert js.status == Status.ABORTED
    assert js.session_id == "sess-1"  # 血缘保留——有现场可查（ADR 0031 决定一）


def test_aborted_with_none_session_does_not_resurrect_but_documents_edge(tmp_path):
    # 边界（记录现状）：若 aborted 在任何 ScopeStarted 抵达前被掐，jr.session_id=None——终态写按字段合并，给出的会话为空时保留库中的，
    # 库中也没有（血缘从未到达）时就是 None。这是「血缘从未收到」的诚实结果，非 bug（无法保留从未到达的血缘）。
    # 正常 in-flight abort（上一个测试）jr 必带 session_id，不走这条。
    p, run_store, _, _ = _local(tmp_path, ("s",))
    # 没有 ScopeStarted（血缘从未到达）→ 直接 aborted 终态、session_id=None
    p.on_job_complete(_jr("s", Status.ABORTED, session_id=None))
    js = run_store.load_run_state("r").jobs["s"]
    assert js.status == Status.ABORTED and js.session_id is None  # 诚实：从未收到血缘


def test_running_phase_has_no_data_plane_file_until_complete(tmp_path):
    """锁定「两面分离」——提交者实测会困惑的点：
    job 处于 RUNNING 时，控制面 run_state.json 显示 running，但数据面 jobs/<scope>.json **还不存在**；
    只有 job 完成（on_job_complete）出了判定，jobs/<scope>.json 才落。
    数据面存的是判定真值，RUNNING 的 job 还没判定，故意不写半截——「jobs/ 里出现文件就表示判定已就绪」。"""
    from urllib.parse import quote

    p, run_store, result_store, _ = _local(tmp_path, ("s",))

    jobs_dir = tmp_path / "r" / "jobs"
    job_file = jobs_dir / (quote("s", safe="") + ".json")

    # —— RUNNING 阶段（job 开始运行、尚未完成）——
    p.on_event(ScopeStarted(scope_id="s", session_id="sess-1"))
    # 控制面：run_state 显示 running（进度可见）
    assert run_store.load_run_state("r").jobs["s"].status == Status.RUNNING
    # 数据面：jobs/<scope>.json **还不存在**（RUNNING 的 job 没判定，不写半截）——这正是提交者看到的现象
    assert not job_file.exists()
    assert result_store.load_all("r") == []

    # —— complete 阶段（on_job_complete 出了判定）——
    p.on_job_complete(_jr("s", Status.PASSED))
    # 数据面：现在才出现 jobs/<scope>.json（即判定就绪）
    assert job_file.exists()
    assert [jr.scope_id for jr in result_store.load_all("r")] == ["s"]
    # 控制面：终态写写下终态
    assert run_store.load_run_state("r").jobs["s"].status == Status.PASSED


def test_run_status_follows_the_terminal_writes_and_the_last_one_ends_the_run(tmp_path):
    """前台 run 的 run 级状态由每次 job 状态写按取法随之写下（ADR 0031 决定三；ADR 0034 机制三「run 级状态只进不退」条③）：begin 后为
    pending；第一个 job 的终态写之后为 running（另一个 job 还没结束）；最后一个 job 的终态写使 run 成为终态（error：有 job 出错），结束
    时刻随这次写写下，收尾不再做结束写。RunPersistence 不另记「是否第一次」，推进由 RunStore 的写自身保证。"""
    p, run_store, _, meta = _local(tmp_path, ("a", "b"))
    assert run_store.load_run_state("r").status == Status.PENDING
    p.on_job_complete(_jr("a", Status.ERROR))
    state = run_store.load_run_state("r")
    assert (state.status, state.jobs["a"].status, state.jobs["b"].status) == (Status.RUNNING, Status.ERROR, Status.PENDING)
    p.on_event(ScopeStarted(scope_id="b", session_id="sess-b"))
    p.on_job_complete(_jr("b", Status.PASSED, session_id="sess-b"))
    state = run_store.load_run_state("r")
    assert (state.status, state.ended_at) == (Status.ERROR, _NOW_ISO)
    finalized = p.finalize(_execution(meta, [_jr("a", Status.ERROR), _jr("b")]))
    assert (finalized.result.status, finalized.result.message) == (Status.ERROR, None)


# ---- 会话事件（ADR 0051 决策 4）：session_opened 刷 RUNNING 带代表会话；attempted 不产生带 None 的写入；锁定后不改写 ----
def test_on_event_session_opened_sets_running_and_never_writes_none_session_id():
    from gherkai_core.model import SessionOpened

    calls, run, result, report = _recording()
    p = RunPersistence("r", run, result, report)
    p.on_event(SessionOpened(scope_id="a", name="A", origin="created", session_id="arn:A"))
    p.on_event(SessionOpened(scope_id="a", name="T", origin="attempted"))            # 结果未知的尝试：不写 None
    p.on_event(SessionOpened(scope_id="a", name="B", origin="created", session_id="arn:B"))  # 换台：后到覆盖
    p.on_event(ScopeStarted(scope_id="a", session_id="arn:B"))                        # 锁定
    p.on_event(SessionOpened(scope_id="a", name="C", origin="discovered", session_id="arn:C"))  # 锁定后不改写
    p.on_job_complete(_jr("a", Status.ERROR, session_id=None))                        # 终态写退回已记的代表会话
    updates = [js for (s, m, js) in calls if m == "update_job_state"]
    assert [(js.status, js.session_id) for js in updates] == [
        (Status.RUNNING, "arn:A"), (Status.RUNNING, "arn:A"), (Status.RUNNING, "arn:B"), (Status.RUNNING, "arn:B"),
        (Status.RUNNING, "arn:B")]
    ((final,), _ended_at) = next(arg for (s, m, arg) in calls if m == "commit_job_states")
    assert (final.status, final.session_id) == (Status.ERROR, "arn:B")
    assert all(js.session_id is not None for js in updates)


def test_on_event_only_attempted_sessions_write_nothing():
    from gherkai_core.model import SessionOpened

    calls, run, result, report = _recording()
    p = RunPersistence("r", run, result, report)
    p.on_event(SessionOpened(scope_id="a", name="T", origin="attempted"))
    assert [m for (_, m, _) in calls if m == "update_job_state"] == []


# ---- ADR 0054 决策五：落库服务向调度循环提供认领、重试之前的读与停手信号；认领时刻在此后的写里保留 ----

def test_claim_writes_the_claim_time_and_later_job_writes_keep_it(tmp_path):
    """认领写成：job 置为 running、认领计数加一、认领时刻按记录的写法（UTC 的 ISO 串）落库；此后开始执行与结束两次 job 状态写都带上它
    （执行中的写是整项替换，不带就会被抹掉；终态写按字段合并、以库中的为准），代表会话照常保留。"""
    p, run_store, _, _ = _local(tmp_path)
    assert p.claim("s", _CLAIMED) is True
    state = run_store.load_run_state("r")
    assert (state.status, state.claim_count) == (Status.RUNNING, 1)
    assert (state.jobs["s"].status, state.jobs["s"].claimed_at) == (Status.RUNNING, instant_to_iso(_CLAIMED))
    p.on_event(ScopeStarted(scope_id="s", session_id="sess-1"))
    js = run_store.load_run_state("r").jobs["s"]
    assert (js.status, js.session_id, js.claimed_at) == (Status.RUNNING, "sess-1", instant_to_iso(_CLAIMED))
    p.on_job_complete(_jr("s", Status.PASSED))
    js = run_store.load_run_state("r").jobs["s"]
    assert (js.status, js.session_id, js.claimed_at) == (Status.PASSED, "sess-1", instant_to_iso(_CLAIMED))
    assert p.ended_elsewhere() is False


def test_claim_rejected_after_the_run_ended_elsewhere_raises_the_stop_signal(tmp_path):
    """别处已把 run 结束（这里是处置的结束写，s 被记 skipped）：认领被拒、job 不变（没有认领时刻），停手信号成立。"""
    p, run_store, _, _ = _local(tmp_path)
    assert run_store.end_run("r", RUN_ENDINGS["settle-advancer-exited"], ended_at="t5") is True
    assert p.claim("s", _CLAIMED) is False
    assert p.ended_elsewhere() is True
    js = run_store.load_run_state("r").jobs["s"]
    assert (js.status, js.claimed_at) == (Status.SKIPPED, None)


@pytest.mark.parametrize("write", ["on_event", "on_job_complete"])
def test_job_state_write_that_finds_the_run_ended_raises_the_stop_signal(tmp_path, write):
    """写 job 状态时 RunStore 报告 run 级已是终态（没有写成）：开始执行与结束两处的写都发出停手信号；别处的结束写记下的终态不被改写。"""
    p, run_store, _, _ = _local(tmp_path)
    assert p.claim("s", _CLAIMED) is True
    settled = RUN_ENDINGS["settle-advancer-exited"]
    assert run_store.end_run("r", settled, ended_at="t5") is True
    assert p.ended_elsewhere() is False  # 只有写或读的时候才发现
    if write == "on_event":
        p.on_event(ScopeStarted(scope_id="s", session_id="sess-1"))
    else:
        p.on_job_complete(_jr("s", Status.PASSED))
    assert p.ended_elsewhere() is True
    state = run_store.load_run_state("r")
    assert (state.status, state.jobs["s"].status, state.jobs["s"].message) == (
        Status.ABORTED, Status.ABORTED, settled.aborted_message)


def test_still_open_reads_the_run_level_status_and_raises_the_signal_on_terminal(tmp_path):
    """重试之前的读：run 级未结束为 True、不发信号；已是终态为 False 并发出停手信号。"""
    p, run_store, _, _ = _local(tmp_path)
    assert p.still_open() is True and p.ended_elsewhere() is False
    assert run_store.end_run("r", RUN_ENDINGS["settle-advancer-exited"], ended_at="t5") is True
    assert p.still_open() is False and p.ended_elsewhere() is True


def test_still_open_without_a_run_state_is_an_error_not_a_verdict():
    """读回发现运行态不存在（begin 之后不该发生）：抛 FileNotFoundError，按运行期落库失败处理，不当作「run 已结束」。"""
    calls, run, result, report = _recording(recorded=None)
    p = RunPersistence("r", run, result, report)
    with pytest.raises(FileNotFoundError):
        p.still_open()
    assert p.ended_elsewhere() is False


# ---- 没有记录的执行（run --no-report）：在内存里按同一套规则给出 run 的结果 ----
def test_result_without_record_applies_the_terminal_writes_then_the_end_write():
    """判出结果的 job 记终态，余下的 job 按执行事实交来的来路做结束写（skipped 加说明），run 的状态按取法；明细取执行事实里的结果，
    墙钟取执行事实的整体时长。与有记录时两个写入口对运行态的作用相同。"""
    meta = _meta("r", ["a", "b", "c"])
    ending = RUN_ENDINGS["fail-fast"]
    out = result_without_record(_execution(meta, [_jr("a", Status.ERROR), _jr("b")], stopped_by="fail-fast", duration_ms=900.0),
                                ended_at=_NOW_ISO)
    assert (out.status, out.message, out.duration_ms) == (Status.ERROR, ending.run_message, 900.0)
    assert [(o.scope_id, o.status, o.state.message, o.detail is not None) for o in out.jobs] == [
        ("a", Status.ERROR, None, True), ("b", Status.PASSED, None, True), ("c", Status.SKIPPED, ending.skipped_message, False)]
    assert out.state.ended_at == _NOW_ISO


# ---- 经 schedule 走完整的前台路径 ----

def test_deadline_finalize_ends_unstarted_jobs_by_the_end_write(tmp_path):
    """经 schedule 的前台执行越过停止启动的时刻（真 LocalRunStore）：已执行的 job 落判定明细并保留认领时刻；没有启动的 job 不落判定
    明细、不认领，收尾的到期结束写把它记 skipped 并带到期的说明，run 按取法记 aborted、run 级说明是「已超过允许运行的时间」。写的次序：
    判定明细先于终态写，没有启动的 job 由结束写结束。"""
    from datetime import timedelta

    from gherkai_core.model import ScenarioDone, ScenarioStarted, ScopeDone
    from gherkai_core.schedule import ScheduleOpts, schedule
    from tests.fake_engine import CollectSink, FakeEngine, FakeResolver

    t = {"s": 0.0}
    base = datetime(2030, 1, 1, tzinfo=timezone.utc)
    p, run_store, result_store, _ = _local(tmp_path, ("a", "b"))
    meta = RunMeta(run_id="r", created_at="t0", jobs=_meta("r", ["a", "b"]).jobs,
                   deadline_at=(base + timedelta(seconds=1000)).isoformat())

    class _Sink(CollectSink):  # a 的内容一完整，墙钟就越过停止启动的时刻（期限减 60 秒）
        def __call__(self, event) -> None:
            super().__call__(event)
            if isinstance(event, ScopeDone):
                t["s"] = 950.0

    def events(sid):
        return [ScopeStarted(scope_id=sid, session_id=f"sess-{sid}"), ScenarioStarted(scenario_id=f"{sid}:0"),
                ScenarioDone(scenario_id=f"{sid}:0", status=Status.PASSED), ScopeDone(scope_id=sid)]

    engine = FakeEngine({"a": events("a"), "b": events("b")})
    ex = schedule(meta, FakeResolver(engine), _Sink(),
                  opts=ScheduleOpts(max_concurrency=1, wall_clock=lambda: base + timedelta(seconds=t["s"]), record=p),
                  on_job_complete=p.on_job_complete, on_event=p.on_event)
    assert ex.stopped_by == "deadline"
    finalized = p.finalize(ex)
    ending = RUN_ENDINGS["deadline"]
    state = run_store.load_run_state("r")
    assert (state.status, state.message, state.ended_at, state.claim_count) == (Status.ABORTED, ending.run_message, _NOW_ISO, 1)
    assert (state.jobs["a"].status, state.jobs["a"].claimed_at) == (Status.PASSED, instant_to_iso(base))
    assert (state.jobs["b"].status, state.jobs["b"].message, state.jobs["b"].claimed_at) == (
        Status.SKIPPED, ending.skipped_message, None)
    assert [jr.scope_id for jr in result_store.load_all("r")] == ["a"]
    assert "b" not in engine.run_count
    assert (finalized.result.status, [jr.scope_id for jr in finalized.result.details]) == (Status.ABORTED, ["a"])


def test_found_ended_during_execution_stores_nothing_more_and_finalize_raises():
    """写 job 状态时得知 run 级已结束（执行中的写没有写成）：此后这个 job 的结果不被采用——不存明细、不写终态；收尾不做结束写、不生成
    报告，读回记录、抛 RunAlreadyEnded。全部 job 都通过也不改变这一点：结果不写进记录。"""
    from gherkai_core.model import ScenarioDone, ScenarioStarted, ScopeDone
    from gherkai_core.schedule import ScheduleOpts, schedule
    from tests.fake_engine import CollectSink, FakeEngine, FakeResolver

    meta = _meta("r", ["a"])
    recorded = _state(meta, {"a": Status.ABORTED}, status=Status.ABORTED)
    calls, run, result, report = _recording(run_open_at_job_write=False, recorded=recorded)  # 每次执行中的写都报告 run 级已结束
    p = RunPersistence("r", run, result, report)
    engine = FakeEngine({"a": [ScopeStarted(scope_id="a"), ScenarioStarted(scenario_id="a:0"),
                               ScenarioDone(scenario_id="a:0", status=Status.PASSED), ScopeDone(scope_id="a")]})
    ex = schedule(meta, FakeResolver(engine), CollectSink(), opts=ScheduleOpts(max_concurrency=1, record=p),
                  on_job_complete=p.on_job_complete, on_event=p.on_event)
    assert [jr.status for jr in ex.results] == [Status.PASSED] and p.ended_elsewhere() is True
    with pytest.raises(RunAlreadyEnded) as exc:
        p.finalize(ex)
    assert exc.value.recorded is recorded
    assert not any(m in ("save_job_result", "commit_job_states", "end_run", "write") for m in _methods(calls))
