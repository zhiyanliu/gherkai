"""RunPersistence 应用服务直测（ADR 0030）：脱离 cli/schedule，用 fake store 直接验 core 层不变量。

四刀审计发现 RunPersistence 此前零直接单测（只经 cli 端到端间接覆盖）。这里把它的核心契约钉到 core 层：
commit-point 写序 / on_event 只对 ScopeStarted 刷 RUNNING / finalize 逃生舱 + 报告失败隔离 / begin 初始投影 / aborted 血缘保留。
"""
from __future__ import annotations

from core.model import (
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
from core.persist import RunPersistence


def _meta(run_id: str, scope_ids: list[str]) -> RunMeta:
    jobs = tuple(
        Job(scope_id=s, scope_name=s, engine="midscene", scenarios=()) for s in scope_ids
    )
    return RunMeta(run_id=run_id, created_at="t0", jobs=jobs)


def _jr(scope_id: str, status: Status = Status.PASSED, session_id: str | None = None) -> JobResult:
    return JobResult(job=Job(scope_id=scope_id, scope_name=scope_id, engine="midscene", scenarios=()),
                     status=status, session_id=session_id)


def _recording():
    """fake RunStore/ResultStore/ReportStore 共享一个有序 calls log：(store, method, scope_or_None)。"""
    calls: list = []

    class FakeRunStore:
        def preflight(self): calls.append(("run", "preflight", None))
        def create_run(self, meta, initial_state): calls.append(("run", "create_run", initial_state))
        def update_job_state(self, run_id, js): calls.append(("run", "update_job_state", js))
        def finalize_run(self, run_id, status, ended_at): calls.append(("run", "finalize_run", (status, ended_at)))

    class FakeResultStore:
        def preflight(self): calls.append(("result", "preflight", None))
        def save_job_result(self, run_id, jr): calls.append(("result", "save_job_result", jr.scope_id))

    class FakeReportStore:
        def preflight(self): calls.append(("report", "preflight", None))
        def write(self, run_id, result, *, created_at="", materialize=False):
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
    # 仅 ScopeStarted 触发一次 RUNNING 刷（带血缘），其余事件零落库（否则每个 step 都刷 = RMW 风暴）。
    calls, run, result, report = _recording()
    p = RunPersistence("r", run, result, report)

    p.on_event(ScopeStarted(scope_id="a", session_id="s1"))            # → 刷 RUNNING
    p.on_event(StepDone(scenario_id="a:0", step_index=0, status=Status.PASSED, votes=Votes(1, 1)))  # → 不刷
    p.on_event(ScenarioDone(scenario_id="a:0", status=Status.PASSED))  # → 不刷

    updates = [js for (s, m, js) in calls if m == "update_job_state"]
    assert len(updates) == 1  # 只有 ScopeStarted 触发了一次
    assert updates[0].scope_id == "a" and updates[0].status == Status.RUNNING and updates[0].session_id == "s1"


# ---- 决定二/三：finalize 逃生舱——report_store=None 返回 None、仍 finalize_run、不崩 ----
def test_finalize_without_report_store_returns_none():
    calls, run, result, _ = _recording()
    p = RunPersistence("r", run, result, report_store=None)  # WebUI/cron 皮可能不注入 report
    rr = RunResult(run_meta=_meta("r", ["a"]), status=Status.PASSED, jobs=[_jr("a")])
    ret = p.finalize(rr, ended_at="t9")
    assert ret is None
    assert ("run", "finalize_run", (Status.PASSED, "t9")) in calls
    assert not any(m == "write" for (s, m, _) in calls)  # 没 report_store → 不调 write


def test_finalize_with_report_store_returns_uri():
    calls, run, result, report = _recording()
    p = RunPersistence("r", run, result, report)
    rr = RunResult(run_meta=_meta("r", ["a"]), status=Status.PASSED, jobs=[_jr("a")])
    ret = p.finalize(rr, ended_at="t9")
    assert ret == "file:///fake/r/index.html"
    # finalize_run 先、ReportStore.write 后（派生视图永远最后）
    methods = [m for (s, m, _) in calls]
    assert methods.index("finalize_run") < methods.index("write")


def test_finalize_isolates_report_write_failure(tmp_path):
    # #1（review）：ReportStore.write 失败不击穿已 commit 的 run——commit point（finalize_run）已落、
    # 判定真值在 ResultStore 安然无恙，故 write 抛异常被隔离：finalize 返回 None、不冒泡（报告可重建）。
    from core.adapters.run_store.local import LocalRunStore
    from core.adapters.result_store.local import LocalResultStore

    class BoomReportStore:
        def preflight(self): pass  # 探活 no-op（真 LocalRunStore/ResultStore 已带 preflight）
        def write(self, run_id, result, *, created_at="", materialize=False):
            raise OSError("磁盘满，报告写不下")

    run_store = LocalRunStore(tmp_path)
    p = RunPersistence("r", run_store, LocalResultStore(tmp_path), BoomReportStore())
    p.begin(_meta("r", ["s"]), started_at="t0")
    rr = RunResult(run_meta=_meta("r", ["s"]), status=Status.PASSED, jobs=[_jr("s")])
    # 不抛、返回 None（run 已 commit，对外输出/退出码不被派生视图写失败拖垮）
    ret = p.finalize(rr, ended_at="t9")
    assert ret is None
    # commit point 仍落了：run_state 终态 = PASSED + ended_at（finalize_run 不在隔离范围内）
    state = run_store.load_run_state("r")
    assert state is not None and state.status == Status.PASSED and state.ended_at == "t9"
    assert p._report_error is not None and "磁盘满" in p._report_error  # 失败留痕供诊断


# ---- 决定二：begin 写初始全 pending 态，jobs Map 与 run_meta 对齐 ----
def test_begin_writes_all_pending_initial_state():
    calls, run, result, report = _recording()
    p = RunPersistence("r", run, result, report)
    p.begin(_meta("r", ["a", "b"]), started_at="t0")
    # create_run 收到的 initial_state：总 pending、各 job pending、key 集 == run_meta、起止按生命周期
    initial = next(arg for (s, m, arg) in calls if m == "create_run")
    assert initial.status == Status.PENDING
    assert set(initial.jobs.keys()) == {"a", "b"}
    assert all(js.status == Status.PENDING for js in initial.jobs.values())
    assert initial.started_at == "t0" and initial.ended_at is None


# ---- 决定五 + 0031 决定一：aborted 的 session_id 经实时写路径保留（卖点：有现场可查）----
def test_aborted_job_preserves_session_id_through_realtime_write():
    # 用真 LocalRunStore（非 fake）验真覆盖语义：RUNNING 阶段刷了血缘，aborted 终态刷不应清掉它。
    import tempfile
    from core.adapters.run_store.local import LocalRunStore
    from core.adapters.result_store.local import LocalResultStore

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
    from core.adapters.run_store.local import LocalRunStore
    from core.adapters.result_store.local import LocalResultStore

    with tempfile.TemporaryDirectory() as d:
        run_store = LocalRunStore(d)
        p = RunPersistence("r", run_store, LocalResultStore(d))
        p.begin(_meta("r", ["s"]), started_at="t0")
        # 没有 ScopeStarted（血缘从未到达）→ 直接 aborted 终态、session_id=None
        p.on_job_complete(_jr("s", Status.ABORTED, session_id=None))
        js = run_store.load_run_state("r").jobs["s"]
        assert js.status == Status.ABORTED and js.session_id is None  # 诚实：从未收到血缘


def test_running_phase_has_no_data_plane_file_until_complete(tmp_path):
    """钉死「两面分离」（ADR 0016 三层切分 + 0030）——用户实测会困惑的点：
    job 处于 RUNNING 时，控制面 run_state.json 显示 running，但数据面 jobs/<scope>.json **还不存在**；
    只有 job 完成（on_job_complete）出了判定，jobs/<scope>.json 才落。
    数据面 = 判定真值，RUNNING 的 job 还没判定，故意不写半截——「jobs/ 里出现文件 = 判定已就绪」。"""
    from urllib.parse import quote
    from core.adapters.run_store.local import LocalRunStore
    from core.adapters.result_store.local import LocalResultStore

    run_store = LocalRunStore(tmp_path)
    result_store = LocalResultStore(tmp_path)
    p = RunPersistence("r", run_store, result_store)
    p.begin(_meta("r", ["s"]), started_at="t0")

    jobs_dir = tmp_path / "r" / "jobs"
    job_file = jobs_dir / (quote("s", safe="") + ".json")

    # —— RUNNING 阶段（job 起跑、尚未完成）——
    p.on_event(ScopeStarted(scope_id="s", session_id="sess-1"))
    # 控制面：run_state 显示 running（进度可见）
    assert run_store.load_run_state("r").jobs["s"].status == Status.RUNNING
    # 数据面：jobs/<scope>.json **还不存在**（RUNNING 的 job 没判定，不写半截）——这正是用户看到的现象
    assert not job_file.exists()
    assert result_store.load_all("r") == []

    # —— complete 阶段（on_job_complete 出了判定）——
    p.on_job_complete(_jr("s", Status.PASSED))
    # 数据面：现在才出现 jobs/<scope>.json（= 判定就绪，commit-point 语义）
    assert job_file.exists()
    assert [jr.scope_id for jr in result_store.load_all("r")] == ["s"]
    # 控制面：同步刷成终态
    assert run_store.load_run_state("r").jobs["s"].status == Status.PASSED
