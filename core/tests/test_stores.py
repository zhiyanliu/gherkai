"""RunStore / ResultStore local adapter + serialize round-trip 单测（ADR 0016 三层切分）。"""
import json
from pathlib import Path

from core.adapters.run_store.local import LocalRunStore
from core.adapters.result_store.local import LocalResultStore
from core.serialize import from_dict, job_result_from_dict, job_result_to_dict, to_dict
from core.model import (
    Job,
    JobResult,
    JobState,
    ReportRef,
    ResourceUri,
    RunMeta,
    RunState,
    RunResult,
    Scenario,
    ScenarioResult,
    Status,
    Step,
    StepResult,
    Votes,
    run_state_from_result,
)


def _job_def(scope_id: str, scope_name: str, engine: str) -> Job:
    # 非平凡 definition：含 scenarios/steps + 非默认 assertion_votes，护住 round-trip（Job 嵌套必须完整重建）
    return Job(
        scope_id=scope_id, scope_name=scope_name, engine=engine,
        scenarios=(
            Scenario(id=f"{scope_id}", name=scope_name, steps=(
                Step(0, "Given", '打开 "https://x"'),
                Step(1, "When", "搜索 OpenAI"),
            )),
        ),
        assertion_votes=3,  # 非默认值：护住 serialize round-trip 不丢该字段
    )


def _sample_run(run_id: str = "20260629-abc") -> RunResult:
    j0 = _job_def("features/wiki.feature:6", "wiki", "midscene")  # 含 /:，测不透明 id 编码
    j1 = _job_def("登录场景", "登录场景", "novaact")              # 中文 scope_id，测可逆编码
    return RunResult(
        run_meta=RunMeta(run_id=run_id, created_at="2026-06-29T00:00:00Z", jobs=(j0, j1)),
        status=Status.FAILED,
        duration_ms=12000.0,
        total_tokens=10573,
        total_time_worked_s=58.6,
        jobs=[
            JobResult(
                job=j0,
                status=Status.PASSED,
                total_tokens=10573,
                duration_ms=11000.0,
                session_id="sess-1",
                report_refs=(ReportRef(kind="report", ref=ResourceUri("file:///x.html"), label="r"),),
                scenarios=[
                    ScenarioResult(
                        scenario_id="features/wiki.feature:6",
                        status=Status.PASSED,
                        duration_ms=10000.0,
                        steps=[
                            StepResult(index=0, status=Status.PASSED, duration_ms=3000.0,
                                       report_refs=(ReportRef(kind="trajectory", ref=ResourceUri("file:///a.html")),)),
                            StepResult(index=1, status=Status.PASSED, duration_ms=7000.0,
                                       votes=Votes(yes=3, total=3)),
                            # 被短路的 step（ADR 0031 决定六）：SKIPPED + shortcircuited=True，护 round-trip
                            # 不丢该字段（默认 False，若序列化漏了会假绿——故这里显式非默认值）。
                            StepResult(index=2, status=Status.SKIPPED, shortcircuited=True),
                        ],
                    )
                ],
            ),
            JobResult(
                job=j1,
                status=Status.FAILED,
                error_type="assertion_failed",
                message="没过",
            ),
        ],
    )


# ---- serialize round-trip：from_dict(to_dict(r)) 字段级等价 ----
def test_serialize_round_trip():
    r = _sample_run()
    r2 = from_dict(to_dict(r))
    assert r2.run_id == r.run_id
    assert r2.run_meta.created_at == "2026-06-29T00:00:00Z"
    assert r2.status == r.status == Status.FAILED
    assert r2.duration_ms == 12000.0
    assert r2.total_tokens == 10573 and r2.total_time_worked_s == 58.6
    assert len(r2.jobs) == 2
    j0 = r2.jobs[0]
    assert j0.scope_id == "features/wiki.feature:6" and j0.engine == "midscene"  # 经 property
    assert j0.scope_name == "wiki"  # 重构补齐的字段（旧版漏抄）
    assert j0.job.scenarios[0].steps[1].text == "搜索 OpenAI"  # definition 完整重建（护 round-trip）
    assert j0.job.assertion_votes == 3  # assertion_votes 经 round-trip 不丢
    assert j0.session_id == "sess-1"
    assert j0.report_refs[0].kind == "report" and j0.report_refs[0].label == "r"
    sr = j0.scenarios[0]
    assert sr.steps[0].report_refs[0].kind == "trajectory"  # step 级 trajectory 经 round-trip 不丢
    assert sr.report_refs == ()  # 不再聚合到 scenario 级
    assert sr.steps[1].votes.yes == 3 and sr.steps[1].votes.total == 3
    assert sr.steps[0].duration_ms == 3000.0
    # 被短路 step 的 shortcircuited=True 经 round-trip 不丢（ADR 0031 决定六）——
    # 显式验证非默认值往返，防"序列化漏字段但默认 False 恰好相等"的假绿。
    assert sr.steps[2].status == Status.SKIPPED and sr.steps[2].shortcircuited is True
    assert sr.steps[0].shortcircuited is False  # 正常步默认 False 也正确往返
    j1 = r2.jobs[1]
    assert j1.scope_id == "登录场景" and j1.error_type == "assertion_failed" and j1.message == "没过"


def test_serialize_round_trip_deep_equal_dict():
    # 更强：to_dict(from_dict(to_dict(r))) == to_dict(r)（dict 层完全一致）
    r = _sample_run()
    d1 = to_dict(r)
    d2 = to_dict(from_dict(d1))
    assert d1 == d2


def test_aggregate_to_dict_normalized_no_def_duplication():
    # 聚合视图 normalize（ADR 0016）：definition 只在 run_meta.jobs[] 出现一份；
    # jobs[] 只背判定、不嵌 job def（防同一批 Job 在一个 dict 里序列化两份的冗余回归）。
    d = to_dict(_sample_run())
    assert "scenarios" in d["run_meta"]["jobs"][0]      # def 唯一真值在 run_meta
    for jr_d in d["jobs"]:
        assert "job" not in jr_d                         # 判定项不嵌完整 def
        assert "scope_id" in jr_d                         # 唯一保留的顶层 def 字段 = join key
        assert "scope_name" not in jr_d and "engine" not in jr_d  # 其余 def 冗余已去（def 在 run_meta）
    # 仍能 round-trip：from_dict 按 scope_id 从 run_meta join 回 def
    r2 = from_dict(d)
    assert r2.jobs[0].job.scenarios[0].steps[1].text == "搜索 OpenAI"
    assert r2.jobs[0].scope_name == "wiki"               # 经 join + property
    assert r2.jobs[0].engine == "midscene"               # join 后 def 完整（engine 也对）


def test_result_store_single_job_file_is_self_contained():
    # ResultStore 单 job 文件 = 自包含形态（include_job=True 默认）：嵌完整 def，
    # CI 单独读一个 jobs/<scope_id>.json 不依赖 run_meta 即可重建（与聚合 normalize 形态相对）。
    jr = _sample_run().jobs[0]
    d = job_result_to_dict(jr)                            # 默认 include_job=True
    assert "job" in d and "scenarios" in d["job"]         # 自包含：嵌完整 def
    jr2 = job_result_from_dict(d)                          # 不传 job=，从嵌套重建
    assert jr2.job.scenarios[0].steps[1].text == "搜索 OpenAI"
    assert jr2.scope_name == "wiki" and jr2.engine == "midscene"


# ---- LocalRunStore：save(meta,state) → load_run_meta/load_run_state 往返 ----
def test_run_store_save_load(tmp_path: Path):
    store = LocalRunStore(tmp_path / "runs")
    r = _sample_run("run-1")
    store.save_run(r.run_meta, run_state_from_result(r))
    run_dir = tmp_path / "runs" / "run-1"
    assert (run_dir / "run_meta.json").exists()
    assert (run_dir / "run_state.json").exists()
    # definition 读回
    meta = store.load_run_meta("run-1")
    assert meta is not None and meta.run_id == "run-1" and meta.created_at == "2026-06-29T00:00:00Z"
    assert len(meta.jobs) == 2 and meta.jobs[0].scope_id == "features/wiki.feature:6"
    # 运行态读回（status/血缘，不含判定明细）。jobs 是 Map（scope_id → JobState，ADR 0030），按 key 取。
    state = store.load_run_state("run-1")
    assert state is not None and state.status == Status.FAILED
    j0 = state.jobs["features/wiki.feature:6"]
    j1 = state.jobs["登录场景"]
    assert j0.scope_id == "features/wiki.feature:6" and j0.session_id == "sess-1"
    assert j0.status == Status.PASSED and j1.status == Status.FAILED


def test_run_store_load_missing_returns_none(tmp_path: Path):
    store = LocalRunStore(tmp_path / "runs")
    assert store.load_run_meta("nope") is None
    assert store.load_run_state("nope") is None


def test_run_state_timestamps_round_trip(tmp_path: Path):
    # started_at/ended_at 非 None 时也须经 save/load 完整保留（不止测 None 态）。
    # run_state_from_result 只投影运行态、不填起止（ADR 0016），故直接造带时间戳的 RunState 测落盘往返。
    store = LocalRunStore(tmp_path / "runs")
    meta = _sample_run("run-ts").run_meta
    state = RunState(
        run_id="run-ts", status=Status.PASSED,
        jobs={"features/wiki.feature:6": JobState(scope_id="features/wiki.feature:6", status=Status.PASSED, session_id="sess-1")},
        started_at="2026-06-29T00:00:00Z", ended_at="2026-06-29T00:05:00Z",
    )
    store.save_run(meta, state)
    got = store.load_run_state("run-ts")
    assert got is not None
    assert got.started_at == "2026-06-29T00:00:00Z"
    assert got.ended_at == "2026-06-29T00:05:00Z"
    assert got == state  # 全字段等价


def test_run_state_omits_null_timestamps(tmp_path: Path):
    # omit-when-None：起止为 None（未取时钟的裸跑路径；正常 run 由 RunPersistence.begin/finalize 落起止，
    # ADR 0030）时，落盘 JSON **不写**这两个键（不是写 null）——避免"永远 null 的字段被当 bug"的体验
    # 噪音。round-trip 仍还原回 None。
    store = LocalRunStore(tmp_path / "runs")
    r = _sample_run("run-null")  # run_state_from_result 不填起止 → None
    store.save_run(r.run_meta, run_state_from_result(r))
    raw = json.loads((tmp_path / "runs" / "run-null" / "run_state.json").read_text("utf-8"))
    assert "started_at" not in raw and "ended_at" not in raw  # 键缺席，非 null
    got = store.load_run_state("run-null")
    assert got is not None and got.started_at is None and got.ended_at is None  # 读回仍 None


# ---- LocalResultStore：每 job 落盘 + scope_id 不透明编码 ----
def test_result_store_save_load_job(tmp_path: Path):
    store = LocalResultStore(tmp_path / "runs")
    r = _sample_run("run-2")
    for jr in r.jobs:
        store.save_job_result("run-2", jr)
    # 含 /:中文 的 scope_id 都安全成文件名（可逆编码、不撞名、不当路径）
    jobs_dir = tmp_path / "runs" / "run-2" / "jobs"
    assert len(list(jobs_dir.glob("*.json"))) == 2
    # 读回单 job（判定真值 + definition 完整）
    j0 = store.load_job_result("run-2", "features/wiki.feature:6")
    assert j0 is not None and j0.engine == "midscene" and j0.scope_name == "wiki"
    j1 = store.load_job_result("run-2", "登录场景")
    assert j1 is not None and j1.error_type == "assertion_failed"
    # 读回全部
    allj = store.load_all("run-2")
    assert len(allj) == 2


def test_result_store_scope_id_not_path_traversal(tmp_path: Path):
    # scope_id 含 / 不会被当路径（编码后是单个文件名，不会逃逸出 jobs/）
    store = LocalResultStore(tmp_path / "runs")
    jr = JobResult(job=_job_def("a/b/c:9", "anchor", "midscene"), status=Status.PASSED)
    store.save_job_result("run-3", jr)
    jobs_dir = tmp_path / "runs" / "run-3" / "jobs"
    files = list(jobs_dir.glob("*.json"))
    assert len(files) == 1
    assert "/" not in files[0].name.replace(".json", "")  # / 被编码，没造子目录
    assert store.load_job_result("run-3", "a/b/c:9").scope_id == "a/b/c:9"


# ---- RunStore 实时写三段（ADR 0030）：create_run → update_job_state×N → finalize_run ----
def _initial_state(run_id: str, scope_ids: list[str]) -> RunState:
    """run 开始时的初始态：各 job 摆 pending、总 pending、起止未填。"""
    return RunState(
        run_id=run_id, status=Status.PENDING,
        jobs={sid: JobState(scope_id=sid, status=Status.PENDING) for sid in scope_ids},
        started_at="2026-07-01T00:00:00Z",
    )


def test_realtime_write_lifecycle(tmp_path: Path):
    store = LocalRunStore(tmp_path / "runs")
    meta = _sample_run("rt-run").run_meta
    scope_ids = ["features/wiki.feature:6", "登录场景"]

    # 1) 开始：写 definition + 全 pending 初始态
    store.create_run(meta, _initial_state("rt-run", scope_ids))
    s0 = store.load_run_state("rt-run")
    assert s0 is not None and s0.status == Status.PENDING
    assert all(js.status == Status.PENDING for js in s0.jobs.values())
    assert store.load_run_meta("rt-run") is not None  # definition 也落了

    # 2) 第一个 job 起跑 → running（带血缘）；中途读得到「部分完成态」（pending/running 混存）
    store.update_job_state("rt-run", JobState("features/wiki.feature:6", Status.RUNNING, session_id="sess-1"))
    mid = store.load_run_state("rt-run")
    assert mid is not None
    assert mid.jobs["features/wiki.feature:6"].status == Status.RUNNING
    assert mid.jobs["features/wiki.feature:6"].session_id == "sess-1"
    assert mid.jobs["登录场景"].status == Status.PENDING  # 另一个还没动——Map 单元素更新不互相污染
    assert mid.status == Status.PENDING  # 总状态还没 finalize

    # 3) 两个 job 各自完成
    store.update_job_state("rt-run", JobState("features/wiki.feature:6", Status.PASSED, session_id="sess-1"))
    store.update_job_state("rt-run", JobState("登录场景", Status.FAILED))
    s2 = store.load_run_state("rt-run")
    assert s2 is not None
    assert s2.jobs["features/wiki.feature:6"].status == Status.PASSED
    assert s2.jobs["登录场景"].status == Status.FAILED

    # 4) finalize（commit point）：写总 status + ended_at；各 job 态保留
    store.finalize_run("rt-run", Status.FAILED, "2026-07-01T00:05:00Z")
    final = store.load_run_state("rt-run")
    assert final is not None
    assert final.status == Status.FAILED
    assert final.ended_at == "2026-07-01T00:05:00Z"
    assert final.started_at == "2026-07-01T00:00:00Z"  # create_run 填的起点保留
    assert final.jobs["features/wiki.feature:6"].status == Status.PASSED  # job 态没被 finalize 覆盖


def test_update_job_state_before_create_raises(tmp_path: Path):
    # 未 create_run 就 update/finalize → 报错（须先建初始态，不静默吞）
    import pytest
    store = LocalRunStore(tmp_path / "runs")
    with pytest.raises(FileNotFoundError):
        store.update_job_state("nope", JobState("s", Status.RUNNING))
    with pytest.raises(FileNotFoundError):
        store.finalize_run("nope", Status.PASSED, "t")


def test_job_timeout_s_round_trip():
    # Job.timeout_s（ADR 0034「job timeout」节）：非 None 经 round-trip 不丢；None 落盘省键（旧数据兼容）
    from core.serialize import job_from_dict, job_to_dict
    j = _job_def("s", "s", "midscene")
    assert "timeout_s" not in job_to_dict(j)  # omit-when-None（旧读端兼容）
    assert job_from_dict(job_to_dict(j)).timeout_s is None
    jt = Job(scope_id="t", scope_name="t", engine="midscene", scenarios=j.scenarios, timeout_s=90.0)
    assert job_from_dict(job_to_dict(jt)).timeout_s == 90.0


def test_run_meta_extra_http_headers_round_trip():
    # RunMeta.extra_http_headers（ADR 0035 决策 4）：非空往返不丢；None/空表均省键（旧落盘兼容 + 空即无）
    import dataclasses

    from core.serialize import run_meta_from_dict, run_meta_to_dict
    meta = _sample_run("h-run").run_meta
    assert "extra_http_headers" not in run_meta_to_dict(meta)  # 默认 None → omit
    assert run_meta_from_dict(run_meta_to_dict(meta)).extra_http_headers is None
    # 空 tuple 与 None 语义合一（都是「不注入额外头」）：同样省键、读回 None，不落 {} 也不变形出 ()
    empty = dataclasses.replace(meta, extra_http_headers=())
    assert "extra_http_headers" not in run_meta_to_dict(empty)
    assert run_meta_from_dict(run_meta_to_dict(empty)).extra_http_headers is None
    meta2 = dataclasses.replace(meta, extra_http_headers=(("ngrok-skip-browser-warning", "1"),))
    got = run_meta_from_dict(run_meta_to_dict(meta2))
    assert got.extra_http_headers == (("ngrok-skip-browser-warning", "1"),)


def test_run_meta_extra_http_headers_multiple_normalize_at_write_side():
    """≥2 个 header：写端按键排序规范化、读端原样保序 → 键值不丢、落盘键序确定，再往返逐字恒等。

    单 header 遮不住的两处：读端若 sorted 则「落盘顺序 ≠ 读回顺序」（from_dict 不是 to_dict 的逆）；
    写端若原样则落盘内容随内存键序漂（同一份 header 表两种落盘形态）。
    """
    import dataclasses

    from core.serialize import run_meta_from_dict, run_meta_to_dict
    meta = _sample_run("h2-run").run_meta
    hdrs = (("x-tunnel", "b"), ("ngrok-skip-browser-warning", "1"))  # 非字典序（x- 在前）
    meta2 = dataclasses.replace(meta, extra_http_headers=hdrs)
    d = run_meta_to_dict(meta2)
    assert list(d["extra_http_headers"]) == ["ngrok-skip-browser-warning", "x-tunnel"]  # 写端规范化
    got = run_meta_from_dict(d)
    assert dict(got.extra_http_headers) == dict(hdrs)  # 键值不丢
    assert got.extra_http_headers == (("ngrok-skip-browser-warning", "1"), ("x-tunnel", "b"))  # 读端保落盘序
    # 规范形上往返逐字恒等（写端规范化 ⇒ 幂等）
    assert run_meta_from_dict(run_meta_to_dict(got)).extra_http_headers == got.extra_http_headers
    # 读端忠实还原落盘键序（旧落盘由写端排序前落的、键序未必字典序）——若读端也 sorted，这条即挂
    legacy = {"run_id": "legacy", "created_at": "", "jobs": [],
              "extra_http_headers": {"x-tunnel": "b", "ngrok-skip-browser-warning": "1"}}
    assert run_meta_from_dict(legacy).extra_http_headers == (("x-tunnel", "b"), ("ngrok-skip-browser-warning", "1"))


def test_job_state_claimed_at_round_trip(tmp_path: Path):
    # JobState.claimed_at（timeout 起算点）：落盘/读回不丢；未 claim 的省键 → None
    store = LocalRunStore(tmp_path / "runs")
    meta = _sample_run("ca-run").run_meta
    sid0, sid1 = meta.jobs[0].scope_id, meta.jobs[1].scope_id
    state = RunState(run_id="ca-run", status=Status.RUNNING, jobs={
        sid0: JobState(sid0, Status.RUNNING, claimed_at="2026-08-13T00:00:00Z"),
        sid1: JobState(sid1, Status.PENDING),
    })
    store.save_run(meta, state)
    got = store.load_run_state("ca-run")
    assert got.jobs[sid0].claimed_at == "2026-08-13T00:00:00Z"
    assert got.jobs[sid1].claimed_at is None


def test_run_state_jobs_map_round_trip(tmp_path: Path):
    # RunState.jobs 是 Map（ADR 0030）：内存 dict → 落盘 list JSON → 读回仍是等价 Map
    store = LocalRunStore(tmp_path / "runs")
    meta = _sample_run("map-run").run_meta
    state = RunState(
        run_id="map-run", status=Status.PASSED,
        jobs={
            "features/wiki.feature:6": JobState("features/wiki.feature:6", Status.PASSED, session_id="s1"),
            "登录场景": JobState("登录场景", Status.PASSED),
        },
    )
    store.save_run(meta, state)
    # 落盘 JSON 仍是 list（向后兼容）
    raw = json.loads((tmp_path / "runs" / "map-run" / "run_state.json").read_text("utf-8"))
    assert isinstance(raw["jobs"], list) and len(raw["jobs"]) == 2
    # 读回是等价 Map
    got = store.load_run_state("map-run")
    assert got is not None and got == state
    assert isinstance(got.jobs, dict)
