"""RunPersistence 应用服务直测（ADR 0030）：用 fake store 或本机 store 直接验 core 层不变量。

四刀审计发现 RunPersistence 此前零直接单测（只经 cli 端到端间接覆盖）。这里把它的核心契约钉到 core 层：
commit-point 写序 / on_event 只对 ScopeStarted 刷 RUNNING / finalize 的无报告路径 + 报告失败隔离 + 收尾写不成时不覆盖、不写报告 /
begin 初始投影 / aborted 血缘保留 / 认领与认领时刻的保留、重试之前的读、三处发现汇成的停手信号、收尾带 run 级说明（ADR 0054 决策五）。
末尾两条经 schedule 走完整的前台路径，验运行期限收尾与「发现 run 已被别处结束之后不会写下 passed」。
"""
from __future__ import annotations

from gherkai_core.model import (
    Job,
    JobResult,
    RunMeta,
    RunResult,
    ScenarioDone,
    ScopeStarted,
    StepDone,
    Status,
    Votes,
)
from gherkai_core.persist import RunPersistence
from tests.fake_engine import FAR_DEADLINE


def _meta(run_id: str, scope_ids: list[str]) -> RunMeta:
    jobs = tuple(
        Job(scope_id=s, scope_name=s, engine="midscene", scenarios=(), timeout_s=300.0) for s in scope_ids
    )
    return RunMeta(run_id=run_id, created_at="t0", jobs=jobs, deadline_at=FAR_DEADLINE)


def _jr(scope_id: str, status: Status = Status.PASSED, session_id: str | None = None) -> JobResult:
    return JobResult(job=Job(scope_id=scope_id, scope_name=scope_id, engine="midscene", scenarios=(), timeout_s=300.0),
                     status=status, session_id=session_id)


def _recording(*, finalize_lands: bool = True, recorded=None, run_open_at_job_write: bool = True, claim_lands: bool = True):
    """fake RunStore/ResultStore/ReportStore 共享一个有序 calls log：(store, method, scope_or_None)。

    finalize_lands：fake 的 try_finalize 是否写成；写不成时 load_run_state 读回 `recorded`。run_open_at_job_write：update_job_state 报告的
    「这次写时 run 级是否仍未结束」。claim_lands：try_claim_job 是否写成（参数里的认领时刻记进 calls）。"""
    calls: list = []

    class FakeRunStore:
        def preflight(self): calls.append(("run", "preflight", None))
        def create_run(self, meta, initial_state): calls.append(("run", "create_run", initial_state))
        def update_job_state(self, run_id, js):
            calls.append(("run", "update_job_state", js))
            return run_open_at_job_write
        def try_claim_job(self, run_id, scope_id, *, claimed_at=None):
            calls.append(("run", "try_claim_job", (scope_id, claimed_at)))
            return claim_lands
        def try_finalize(self, run_id, status, ended_at, *, message=None, expected_claim_count=None):
            calls.append(("run", "try_finalize", (status, ended_at, message, expected_claim_count)))
            return finalize_lands
        def load_run_state(self, run_id):
            calls.append(("run", "load_run_state", None))
            return recorded

    class FakeResultStore:
        def preflight(self): calls.append(("result", "preflight", None))
        def save_job_result(self, run_id, jr): calls.append(("result", "save_job_result", jr.scope_id))

    class FakeReportStore:
        def preflight(self): calls.append(("report", "preflight", None))
        def write(self, run_id, result, *, created_at=""):
            calls.append(("report", "write", None))
            return f"file:///fake/{run_id}/index.html"

    return calls, FakeRunStore(), FakeResultStore(), FakeReportStore()


# ---- 决定三：on_job_complete commit-point 写序——数据面先于控制面 ----
def test_on_job_complete_saves_result_before_job_state():
    calls, run, result, report = _recording()
    p = RunPersistence("r", run, result, report)
    p.on_job_complete(_jr("a", Status.PASSED))
    methods = [(s, m) for (s, m, _) in calls]
    # 数据面 save_job_result 严格早于控制面 update_job_state（commit-point 核心保证，ADR 0030 决定三）
    assert methods == [("result", "save_job_result"), ("run", "update_job_state")]


# ---- 决定三：on_event 旁路观察者只对 ScopeStarted 刷 RUNNING（反向不变量）----
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


# ---- 决定二/三：finalize 的无报告路径——report_store=None 返回 None、仍写收尾、不崩 ----
def test_finalize_without_report_store_returns_none():
    calls, run, result, _ = _recording()
    p = RunPersistence("r", run, result, report_store=None)  # WebUI/cron 前端可能不注入 report
    rr = RunResult(run_meta=_meta("r", ["a"]), status=Status.PASSED, jobs=[_jr("a")])
    ret = p.finalize(rr, ended_at="t9")
    assert ret is None
    assert ("run", "try_finalize", (Status.PASSED, "t9", None, None)) in calls  # RunResult 没有 run 级说明时不写、不判认领计数
    assert not any(m == "write" for (s, m, _) in calls)  # 没 report_store → 不调 write


def test_finalize_with_report_store_returns_uri():
    calls, run, result, report = _recording()
    p = RunPersistence("r", run, result, report)
    rr = RunResult(run_meta=_meta("r", ["a"]), status=Status.PASSED, jobs=[_jr("a")])
    ret = p.finalize(rr, ended_at="t9")
    assert ret == "file:///fake/r/index.html"
    # 收尾写先、ReportStore.write 后（派生视图永远最后）
    methods = [m for (s, m, _) in calls]
    assert methods.index("try_finalize") < methods.index("write")


def test_finalize_isolates_report_write_failure(tmp_path):
    # ReportStore.write 失败不击穿已 commit 的 run——commit point（收尾写）已落、
    # 判定真值在 ResultStore 安然无恙，故 write 抛异常被隔离：finalize 返回 None、不冒泡（报告可重建）。
    from gherkai_core.adapters.run_store.local import LocalRunStore
    from gherkai_core.adapters.result_store.local import LocalResultStore

    class BoomReportStore:
        def preflight(self): pass  # 探活 no-op（真 LocalRunStore/ResultStore 已带 preflight）
        def write(self, run_id, result, *, created_at=""):
            raise OSError("磁盘满，报告写不下")

    run_store = LocalRunStore(tmp_path)
    p = RunPersistence("r", run_store, LocalResultStore(tmp_path), BoomReportStore())
    p.begin(_meta("r", ["s"]), started_at="t0")
    rr = RunResult(run_meta=_meta("r", ["s"]), status=Status.PASSED, jobs=[_jr("s")])
    # 不抛、返回 None（run 已 commit，对外输出/退出码不被派生视图写失败拖垮）
    ret = p.finalize(rr, ended_at="t9")
    assert ret is None
    # commit point 仍落了：run_state 终态是 PASSED 加 ended_at（收尾写不在隔离范围内）
    state = run_store.load_run_state("r")
    assert state is not None and state.status == Status.PASSED and state.ended_at == "t9"
    # 核心不变量：ReportStore.write 抛异常被隔离、run 照常 commit（返回 None + 控制面终态已落），
    # 不抛出击穿。（曾断言 _report_error 留痕，该字段生产端无人消费、已删，见代码 review N7。）


# ---- ADR 0054 决策五：收尾写不成（run 级已是终态）时不覆盖、不写报告，抛 RunAlreadyEnded ----
def test_finalize_on_a_run_ended_elsewhere_keeps_the_record_and_writes_no_report(tmp_path):
    """本次执行结束之前别处已把 run 记为已结束（带 run 级说明）：finalize 不覆盖已有的终态、ended_at 与说明，不生成报告，
    抛 RunAlreadyEnded 并带读回的运行态；本次已得出的 job 判定此前已写入，不受影响。用真 LocalRunStore，条件写的判定在 adapter 里。"""
    import pytest

    from gherkai_core.adapters.result_store.local import LocalResultStore
    from gherkai_core.adapters.run_store.local import LocalRunStore
    from gherkai_core.errors import RunAlreadyEnded

    calls, _, _, report = _recording()
    run_store, result_store = LocalRunStore(tmp_path), LocalResultStore(tmp_path)
    p = RunPersistence("r", run_store, result_store, report)
    meta = _meta("r", ["a", "b"])
    p.begin(meta, started_at="t0")
    p.on_job_complete(_jr("a", Status.PASSED))
    assert run_store.try_finalize("r", Status.ERROR, "t5", message="已超过允许运行的时间（已记为已结束）") is True

    with pytest.raises(RunAlreadyEnded) as exc:
        p.finalize(RunResult(run_meta=meta, status=Status.PASSED, jobs=[_jr("a"), _jr("b")]), ended_at="t9")
    assert exc.value.run_id == "r"
    assert (exc.value.recorded.status, exc.value.recorded.message) == (Status.ERROR, "已超过允许运行的时间（已记为已结束）")
    state = run_store.load_run_state("r")
    assert (state.status, state.ended_at, state.message) == (Status.ERROR, "t5", "已超过允许运行的时间（已记为已结束）")
    assert not any(m == "write" for (_, m, _) in calls)  # 报告不生成
    assert [jr.scope_id for jr in result_store.load_all("r")] == ["a"]  # 已写入的判定原样在


def test_finalize_refused_without_a_run_state_is_not_reported_as_ended():
    """收尾写不成而读回发现运行态不存在：不说成「已被记为已结束」，抛 FileNotFoundError；报告同样不生成。"""
    import pytest

    calls, run, result, report = _recording(finalize_lands=False, recorded=None)
    p = RunPersistence("r", run, result, report)
    with pytest.raises(FileNotFoundError):
        p.finalize(RunResult(run_meta=_meta("r", ["a"]), status=Status.PASSED, jobs=[_jr("a")]), ended_at="t9")
    assert [m for (_, m, _) in calls] == ["try_finalize", "load_run_state"]


def test_finalize_refused_and_the_read_back_fails_still_reports_ended_elsewhere():
    """收尾写不成之后的那次读回本身失败（如云端的读取报错）：仍抛 RunAlreadyEnded，recorded 为 None、读回的异常是它的起因。
    调用方因此走同一个出口（说明、按信号取的退出码），不会因为多出的这次读得到一个未归类的异常。报告同样不生成。"""
    import pytest

    from gherkai_core.errors import RunAlreadyEnded

    calls, run, result, report = _recording(finalize_lands=False)
    boom = RuntimeError("读取失败")

    def failing_read(run_id):
        calls.append(("run", "load_run_state", None))
        raise boom

    run.load_run_state = failing_read
    p = RunPersistence("r", run, result, report)
    with pytest.raises(RunAlreadyEnded) as exc:
        p.finalize(RunResult(run_meta=_meta("r", ["a"]), status=Status.PASSED, jobs=[_jr("a")]), ended_at="t9")
    assert exc.value.recorded is None and exc.value.run_id == "r"
    assert exc.value.__cause__ is boom
    assert "（" not in str(exc.value)  # 没有读到状态：消息里不留一对空括号
    assert [m for (_, m, _) in calls] == ["try_finalize", "load_run_state"]  # 报告没有写


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
def test_aborted_job_preserves_session_id_through_realtime_write():
    # 用真 LocalRunStore（非 fake）验真覆盖语义：RUNNING 阶段刷了血缘，aborted 终态刷不应清掉它。
    import tempfile
    from gherkai_core.adapters.run_store.local import LocalRunStore
    from gherkai_core.adapters.result_store.local import LocalResultStore

    with tempfile.TemporaryDirectory() as d:
        run_store = LocalRunStore(d)
        p = RunPersistence("r", run_store, LocalResultStore(d))
        p.begin(_meta("r", ["s"]), started_at="t0")
        # ① ScopeStarted 刷 RUNNING + 血缘（worker 线程经 sink 的路径）
        p.on_event(ScopeStarted(scope_id="s", session_id="sess-1"))
        # ② aborted 终态：in-flight 被掐的 jr 带 session_id（schedule 的 result 已从 ScopeStarted 累积，见 _reduce）
        p.on_job_complete(_jr("s", Status.ABORTED, session_id="sess-1"))
        state = run_store.load_run_state("r")
        assert state is not None
        js = state.jobs["s"]
        assert js.status == Status.ABORTED
        assert js.session_id == "sess-1"  # 血缘保留——有现场可查（ADR 0031 决定一）


def test_aborted_with_none_session_does_not_resurrect_but_documents_edge():
    # 边界（记录现状）：若 aborted 在任何 ScopeStarted 抵达前被掐，jr.session_id=None——
    # 此时 update_job_state 会用 None 整体覆盖（local 是整 item 替换）。这是「血缘从未收到」的诚实结果，
    # 非 bug（无法保留从未到达的血缘）。正常 in-flight abort（上一个测试）jr 必带 session_id，不走这条。
    import tempfile
    from gherkai_core.adapters.run_store.local import LocalRunStore
    from gherkai_core.adapters.result_store.local import LocalResultStore

    with tempfile.TemporaryDirectory() as d:
        run_store = LocalRunStore(d)
        p = RunPersistence("r", run_store, LocalResultStore(d))
        p.begin(_meta("r", ["s"]), started_at="t0")
        # 没有 ScopeStarted（血缘从未到达）→ 直接 aborted 终态、session_id=None
        p.on_job_complete(_jr("s", Status.ABORTED, session_id=None))
        js = run_store.load_run_state("r").jobs["s"]
        assert js.status == Status.ABORTED and js.session_id is None  # 诚实：从未收到血缘


def test_running_phase_has_no_data_plane_file_until_complete(tmp_path):
    """锁定「两面分离」（ADR 0016 三层切分 + 0030）——提交者实测会困惑的点：
    job 处于 RUNNING 时，控制面 run_state.json 显示 running，但数据面 jobs/<scope>.json **还不存在**；
    只有 job 完成（on_job_complete）出了判定，jobs/<scope>.json 才落。
    数据面存的是判定真值，RUNNING 的 job 还没判定，故意不写半截——「jobs/ 里出现文件就表示判定已就绪」。"""
    from urllib.parse import quote
    from gherkai_core.adapters.run_store.local import LocalRunStore
    from gherkai_core.adapters.result_store.local import LocalResultStore

    run_store = LocalRunStore(tmp_path)
    result_store = LocalResultStore(tmp_path)
    p = RunPersistence("r", run_store, result_store)
    p.begin(_meta("r", ["s"]), started_at="t0")

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
    # 数据面：现在才出现 jobs/<scope>.json（即判定就绪，commit-point 语义）
    assert job_file.exists()
    assert [jr.scope_id for jr in result_store.load_all("r")] == ["s"]
    # 控制面：同步刷成终态
    assert run_store.load_run_state("r").jobs["s"].status == Status.PASSED


def test_run_status_advances_when_first_job_leaves_pending(tmp_path):
    """前台 run 的 run 级状态（ADR 0034 机制三「run 级状态只进不退」条③）：begin 后为 pending；第一个 job 离开 pending 的那一次写
    之后为 running，哪怕那一次是从 pending 直接写成终态（SKIPPED 的 job 不经 RUNNING）；finalize 落定终态。RunPersistence
    不另记「是否第一次」，推进由 RunStore 的 job 写自身保证。"""
    from gherkai_core.adapters.run_store.local import LocalRunStore
    from gherkai_core.adapters.result_store.local import LocalResultStore

    run_store = LocalRunStore(tmp_path)
    p = RunPersistence("r", run_store, LocalResultStore(tmp_path))
    meta = _meta("r", ["a", "b"])
    p.begin(meta, started_at="t0")
    assert run_store.load_run_state("r").status == Status.PENDING
    p.on_job_complete(_jr("a", Status.SKIPPED))
    state = run_store.load_run_state("r")
    assert (state.status, state.jobs["a"].status, state.jobs["b"].status) == (
        Status.RUNNING, Status.SKIPPED, Status.PENDING)
    p.on_event(ScopeStarted(scope_id="b", session_id="sess-b"))
    p.on_job_complete(_jr("b", Status.PASSED, session_id="sess-b"))
    assert run_store.load_run_state("r").status == Status.RUNNING
    p.finalize(RunResult(run_meta=meta, status=Status.PASSED, jobs=[_jr("a", Status.SKIPPED), _jr("b")]), ended_at="t9")
    assert run_store.load_run_state("r").status == Status.PASSED


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
        (Status.RUNNING, "arn:B"), (Status.ERROR, "arn:B")]
    assert all(js.session_id is not None for js in updates)


def test_on_event_only_attempted_sessions_write_nothing():
    from gherkai_core.model import SessionOpened

    calls, run, result, report = _recording()
    p = RunPersistence("r", run, result, report)
    p.on_event(SessionOpened(scope_id="a", name="T", origin="attempted"))
    assert [m for (_, m, _) in calls if m == "update_job_state"] == []


# ---- ADR 0054 决策五：落库服务向调度循环提供认领、重试之前的读与停手信号；认领时刻在此后的写里保留 ----

from datetime import datetime, timezone  # noqa: E402

import pytest  # noqa: E402

from gherkai_core.serialize import instant_to_iso  # noqa: E402

_CLAIMED = datetime(2030, 1, 1, 8, 0, 0, tzinfo=timezone.utc)


def _local(tmp_path, scope_ids=("s",)):
    from gherkai_core.adapters.result_store.local import LocalResultStore
    from gherkai_core.adapters.run_store.local import LocalRunStore

    run_store, result_store = LocalRunStore(tmp_path), LocalResultStore(tmp_path)
    p = RunPersistence("r", run_store, result_store)
    meta = _meta("r", list(scope_ids))
    p.begin(meta, started_at="t0")
    return p, run_store, result_store, meta


def test_claim_writes_the_claim_time_and_later_job_writes_keep_it(tmp_path):
    """认领写成：job 置为 running、认领计数加一、认领时刻按记录的写法（UTC 的 ISO 串）落库；此后开始执行与结束两次 job 状态写都带上它
    （adapter 是整项替换，不带就会被抹掉），代表会话照常保留。"""
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
    """别处已把 run 记为已结束：认领被拒、job 不变（保持 pending、没有认领时刻），停手信号成立。"""
    p, run_store, _, _ = _local(tmp_path)
    assert run_store.try_finalize("r", Status.ERROR, "t5", message="已超过允许运行的时间（已记为已结束）") is True
    assert p.claim("s", _CLAIMED) is False
    assert p.ended_elsewhere() is True
    js = run_store.load_run_state("r").jobs["s"]
    assert (js.status, js.claimed_at) == (Status.PENDING, None)


@pytest.mark.parametrize("write", ["on_event", "on_job_complete"])
def test_job_state_write_that_finds_the_run_ended_raises_the_stop_signal(tmp_path, write):
    """写 job 状态时 RunStore 报告 run 级已是终态（只写了 job）：开始执行与结束两处的写都发出停手信号；终态不被改回 running。"""
    p, run_store, _, _ = _local(tmp_path)
    assert p.claim("s", _CLAIMED) is True
    assert run_store.try_finalize("r", Status.ERROR, "t5") is True
    assert p.ended_elsewhere() is False  # 只有写或读的时候才发现
    if write == "on_event":
        p.on_event(ScopeStarted(scope_id="s", session_id="sess-1"))
    else:
        p.on_job_complete(_jr("s", Status.ABORTED))
    assert p.ended_elsewhere() is True
    assert run_store.load_run_state("r").status == Status.ERROR


def test_still_open_reads_the_run_level_status_and_raises_the_signal_on_terminal(tmp_path):
    """重试之前的读：run 级未结束为 True、不发信号；已是终态为 False 并发出停手信号。"""
    p, run_store, _, _ = _local(tmp_path)
    assert p.still_open() is True and p.ended_elsewhere() is False
    assert run_store.try_finalize("r", Status.ERROR, "t5") is True
    assert p.still_open() is False and p.ended_elsewhere() is True


def test_still_open_without_a_run_state_is_an_error_not_a_verdict():
    """读回发现运行态不存在（begin 之后不该发生）：抛 FileNotFoundError，按运行期落库失败处理，不当作「run 已结束」。"""
    calls, run, result, report = _recording(recorded=None)
    p = RunPersistence("r", run, result, report)
    with pytest.raises(FileNotFoundError):
        p.still_open()
    assert p.ended_elsewhere() is False


def test_finalize_writes_the_run_level_message_without_a_claim_count_condition():
    """收尾把 RunResult 的 run 级说明随条件写写入，不带认领计数的条件（前台执行是这个 run 唯一的认领方，收尾在线程池排空之后）。"""
    from gherkai_core.run_deadline import RUN_DEADLINE_PASSED_MESSAGE

    calls, run, result, report = _recording()
    p = RunPersistence("r", run, result, report)
    rr = RunResult(run_meta=_meta("r", ["a", "b"]), status=Status.ERROR, message=RUN_DEADLINE_PASSED_MESSAGE, jobs=[_jr("a")])
    p.finalize(rr, ended_at="t9")
    assert ("run", "try_finalize", (Status.ERROR, "t9", RUN_DEADLINE_PASSED_MESSAGE, None)) in calls


def test_deadline_finalize_leaves_unstarted_jobs_pending_without_a_verdict(tmp_path):
    """经 schedule 的前台执行越过停止启动的时刻（真 LocalRunStore）：已执行的 job 落判定明细并保留认领时刻；没有启动的 job 不落判定
    明细、运行态保持 pending、没有认领时刻；run 级以条件写落定 error 加「已超过允许运行的时间」。写的次序不变：判定明细先于 run 级终态。"""
    from datetime import timedelta

    from gherkai_core.model import ScenarioDone, ScenarioStarted, ScopeDone
    from gherkai_core.run_deadline import RUN_DEADLINE_PASSED_MESSAGE
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
    res = schedule(meta, FakeResolver(engine), _Sink(),
                   opts=ScheduleOpts(max_concurrency=1, wall_clock=lambda: base + timedelta(seconds=t["s"]), record=p),
                   on_job_complete=p.on_job_complete, on_event=p.on_event)
    assert (res.status, res.message) == (Status.ERROR, RUN_DEADLINE_PASSED_MESSAGE)
    p.finalize(res, ended_at="t9")
    state = run_store.load_run_state("r")
    assert (state.status, state.message, state.ended_at, state.claim_count) == (Status.ERROR, RUN_DEADLINE_PASSED_MESSAGE, "t9", 1)
    assert (state.jobs["a"].status, state.jobs["a"].claimed_at) == (Status.PASSED, instant_to_iso(base))
    assert (state.jobs["b"].status, state.jobs["b"].claimed_at) == (Status.PENDING, None)
    assert [jr.scope_id for jr in result_store.load_all("r")] == ["a"]
    assert "b" not in engine.run_count


def test_found_ended_but_finalize_lands_writes_aborted_not_passed():
    """写 job 状态时得知 run 级已结束，收尾照样走条件写；万一它写成了（记录其实没有结束，属于不该发生的不一致），写下的 run 级结果是
    aborted、不是 passed——哪怕全部 job 都通过了。"""
    from gherkai_core.model import ScenarioDone, ScenarioStarted, ScopeDone
    from gherkai_core.schedule import ScheduleOpts, schedule
    from tests.fake_engine import CollectSink, FakeEngine, FakeResolver

    calls, run, result, report = _recording(run_open_at_job_write=False)  # 每次 job 状态写都报告 run 级已结束，收尾写却写成
    p = RunPersistence("r", run, result, report)
    meta = _meta("r", ["a"])
    engine = FakeEngine({"a": [ScopeStarted(scope_id="a"), ScenarioStarted(scenario_id="a:0"),
                               ScenarioDone(scenario_id="a:0", status=Status.PASSED), ScopeDone(scope_id="a")]})
    res = schedule(meta, FakeResolver(engine), CollectSink(), opts=ScheduleOpts(max_concurrency=1, record=p),
                   on_job_complete=p.on_job_complete, on_event=p.on_event)
    assert [jr.status for jr in res.jobs] == [Status.PASSED]
    p.finalize(res, ended_at="t9")
    finalized = [args for (_, m, args) in calls if m == "try_finalize"]
    assert finalized == [(Status.ABORTED, "t9", None, None)]
