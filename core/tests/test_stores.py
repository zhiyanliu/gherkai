"""RunStore / ResultStore local adapter + serialize round-trip 单测（ADR 0016 三层切分）。"""
import json
from pathlib import Path

import pytest

from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.adapters.result_store.local import LocalResultStore
from gherkai_core.serialize import from_dict, job_result_from_dict, job_result_to_dict, to_dict
from gherkai_core.model import (
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
                Step(0, "Given", '"https://x"'),
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
        assert "scope_id" in jr_d                         # 唯一保留的顶层 def 字段就是 join key
        assert "scope_name" not in jr_d and "engine" not in jr_d  # 其余 def 冗余已去（def 在 run_meta）
    # 仍能 round-trip：from_dict 按 scope_id 从 run_meta join 回 def
    r2 = from_dict(d)
    assert r2.jobs[0].job.scenarios[0].steps[1].text == "搜索 OpenAI"
    assert r2.jobs[0].scope_name == "wiki"               # 经 join + property
    assert r2.jobs[0].engine == "midscene"               # join 后 def 完整（engine 也对）


def test_result_store_single_job_file_is_self_contained():
    # ResultStore 单 job 文件是自包含形态（include_job=True 默认）：嵌完整 def，
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
    # omit-when-None：起止为 None（未取时钟的零落盘运行路径；正常 run 由 RunPersistence.begin/finalize 落起止，
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

    # 2) 第一个 job 开始运行 → running（带血缘）；中途读得到「部分完成态」（pending/running 混存）
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
    # Job.timeout_s（ADR 0034「job timeout」节）：键恒在（键集固定，ADR 0037 决策 7）；None 落 null、读回 None；非 None 往返不丢
    from gherkai_core.serialize import job_from_dict, job_to_dict
    j = _job_def("s", "s", "midscene")
    assert job_to_dict(j)["timeout_s"] is None
    assert job_from_dict(job_to_dict(j)).timeout_s is None
    jt = Job(scope_id="t", scope_name="t", engine="midscene", scenarios=j.scenarios, timeout_s=90.0)
    assert job_from_dict(job_to_dict(jt)).timeout_s == 90.0


def test_job_target_and_device_request_round_trip_and_fixed_keys():
    """Job.target / device_request（ADR 0048 决策 3）：桌面 job 两键恒在——target 写 desktop/web、device_request 写 null（键集固定，
    ADR 0037 决策 7）；android/web 与 ios/app（带 device_request）往返恒等；plan 形态的应用条目只写 alias 与 app_id。"""
    from gherkai_core.model import AppRef, DeviceFarmRequest, Target
    from gherkai_core.serialize import job_from_dict, job_to_dict

    j = _job_def("s", "s", "midscene")
    d = job_to_dict(j)
    assert d["target"] == {"device": "desktop", "ui_kind": "web"} and d["device_request"] is None
    assert job_from_dict(d).target == Target() and job_from_dict(d).device_request is None
    dr = DeviceFarmRequest(project_arn="arn:p", os_version="15")
    aw = Job(scope_id="aw", scope_name="aw", engine="midscene", scenarios=j.scenarios, timeout_s=1500.0,
             target=Target(device="android", ui_kind="web"), device_request=dr)
    assert job_from_dict(job_to_dict(aw)) == aw
    assert set(job_to_dict(aw)["device_request"]) == {"provider", "billing_method", "project_arn", "acquire_timeout_s", "os_version"}
    ia = Job(scope_id="ia", scope_name="ia", engine="midscene", scenarios=j.scenarios, timeout_s=900.0,
             target=Target(device="ios", ui_kind="app", app=AppRef(alias="shop", app_id="com.example.Shop", bucket="b", key="k", sha256="h")),
             device_request=DeviceFarmRequest(project_arn="arn:p", device_arn="arn:d", billing_method="UNMETERED"))
    assert job_from_dict(job_to_dict(ia)) == ia
    plan_form = Job(scope_id="p", scope_name="p", engine="midscene", scenarios=j.scenarios, timeout_s=900.0,
                    target=Target(device="ios", ui_kind="app", app=AppRef(alias="shop", app_id="com.example.Shop")))
    assert job_to_dict(plan_form)["target"]["app"] == {"alias": "shop", "app_id": "com.example.Shop"}  # 位置三项省略
    assert job_from_dict(job_to_dict(plan_form), validate=False) == plan_form


@pytest.mark.parametrize("patch, match", [
    (lambda d: d.update(device_request=None), "非桌面目标当且仅当带设备请求"),
    (lambda d: d.pop("device_request"), "缺键 device_request"),   # 键集固定：缺键是定义违约、不是「无设备请求」
    (lambda d: d["device_request"].update(device_arn="arn:d"), "恰给一个"),
    (lambda d: d["device_request"].pop("os_version"), "恰给一个"),
    (lambda d: d["device_request"].update(project_arn=""), "缺 project_arn"),
    (lambda d: d["device_request"].update(acquire_timeout_s=0), "有限正数"),
    (lambda d: d["target"].update(ui_kind="app"), "必须带应用条目"),
    (lambda d: d.update(timeout_s=None), "设备 scope 不存在"),
    (lambda d: d.pop("timeout_s"), "缺键 timeout_s"),
])
def test_job_from_dict_rejects_malformed_device_definitions(patch, match):
    """推进器读 definition 时的结构校验（ADR 0048 决策 3）：非桌面却缺设备请求、ARN 与版本同给或同缺、project_arn 为空、
    预算非有限正数、应用目标缺应用条目、设备 scope 无墙钟预算，都拒绝。"""
    from gherkai_core.errors import DefinitionContractError
    from gherkai_core.model import DeviceFarmRequest, Target
    from gherkai_core.serialize import job_from_dict, job_to_dict

    j = _job_def("s", "s", "midscene")
    aw = Job(scope_id="aw", scope_name="aw", engine="midscene", scenarios=j.scenarios, timeout_s=1500.0,
             target=Target(device="android", ui_kind="web"), device_request=DeviceFarmRequest(project_arn="arn:p", os_version="15"))
    d = job_to_dict(aw)
    patch(d)
    with pytest.raises(DefinitionContractError, match=match):
        job_from_dict(d)


def _ios_app_job(scenarios, **over):
    from gherkai_core.model import AppRef, DeviceFarmRequest, Target

    base = dict(scope_id="ia", scope_name="ia", engine="midscene", scenarios=scenarios, timeout_s=900.0,
                target=Target(device="ios", ui_kind="app", app=AppRef(alias="shop", app_id="com.example.Shop", bucket="b", key="k", sha256="h")),
                device_request=DeviceFarmRequest(project_arn="arn:p", device_arn="arn:d", billing_method="UNMETERED"))
    base.update(over)
    return Job(**base)


@pytest.mark.parametrize("field", ["alias", "app_id", "bucket", "key", "sha256"])
@pytest.mark.parametrize("bad", [None, "", 7], ids=["missing", "empty", "wrong-type"])
def test_validate_definition_rejects_each_incomplete_app_field(field, bad):
    """写前校验（ADR 0048 决策 3）：应用条目五项逐项缺失、空值、错类型都拒绝——直接调校验函数，不只经读端。"""
    import dataclasses

    from gherkai_core.errors import DefinitionContractError
    from gherkai_core.target import validate_job_definition

    j = _job_def("s", "s", "midscene")
    good = _ios_app_job(j.scenarios)
    validate_job_definition(good)  # 完整形态通过
    app = dataclasses.replace(good.target.app, **{field: bad})
    bad_job = dataclasses.replace(good, target=dataclasses.replace(good.target, app=app))
    with pytest.raises(DefinitionContractError, match=f"应用条目缺 {field}"):
        validate_job_definition(bad_job)


@pytest.mark.parametrize("over, match", [
    (dict(device_request=None), "非桌面目标当且仅当带设备请求"),
    (dict(timeout_s=None), "设备 scope 不存在"),
    (dict(timeout_s=float("inf")), "有限正数"),
    (dict(timeout_s=10 ** 400), "有限正数"),  # 超出 float 范围的整数：不是 OverflowError 漏出去
])
def test_validate_definition_rejects_device_job_variants(over, match):
    from gherkai_core.errors import DefinitionContractError
    from gherkai_core.target import validate_job_definition

    j = _job_def("s", "s", "midscene")
    with pytest.raises(DefinitionContractError, match=match):
        validate_job_definition(_ios_app_job(j.scenarios, **over))


@pytest.mark.parametrize("patch, match", [
    (dict(device_arn=123), "device_arn 须为非空文本或不设"),  # 错类型不当作「未提供」
    (dict(device_arn=[]), "device_arn 须为非空文本或不设"),
    (dict(device_arn=None, os_version=None), "恰给一个"),
    (dict(os_version="15"), "恰给一个"),  # 与已有的 device_arn 两个都给
    (dict(project_arn=None), "缺 project_arn"),
    (dict(billing_method=None), "缺 billing_method"),
    (dict(acquire_timeout_s=10 ** 400), "有限正数"),
    (dict(acquire_timeout_s=True), "有限正数"),
    (dict(provider="other"), "服务商未知"),
])
def test_validate_definition_rejects_device_request_variants(patch, match):
    import dataclasses

    from gherkai_core.errors import DefinitionContractError
    from gherkai_core.target import validate_job_definition

    j = _job_def("s", "s", "midscene")
    good = _ios_app_job(j.scenarios)
    bad = dataclasses.replace(good, device_request=dataclasses.replace(good.device_request, **patch))
    with pytest.raises(DefinitionContractError, match=match):
        validate_job_definition(bad)


def test_validate_definition_rejects_desktop_with_device_request_or_app_and_web_with_app():
    """「当且仅当」的反向分支：桌面 job 带设备请求、桌面带应用条目、网页界面带应用条目、应用界面无应用条目，都拒绝；错类型的 device 也拒绝。"""
    import dataclasses

    from gherkai_core.errors import DefinitionContractError
    from gherkai_core.model import AppRef, DeviceFarmRequest, Target
    from gherkai_core.target import validate_job_definition

    j = _job_def("s", "s", "midscene")
    app = AppRef(alias="a", app_id="b", bucket="c", key="d", sha256="e")
    cases = [
        (Job(scope_id="d", scope_name="d", engine="midscene", scenarios=j.scenarios, device_request=DeviceFarmRequest(project_arn="p", os_version="15")), "非桌面目标当且仅当带设备请求"),
        (Job(scope_id="d", scope_name="d", engine="midscene", scenarios=j.scenarios, target=Target(device="desktop", ui_kind="app", app=app)), "不是合法组合"),
        (Job(scope_id="d", scope_name="d", engine="midscene", scenarios=j.scenarios, timeout_s=900.0, target=Target(device="android", ui_kind="web", app=app),
             device_request=DeviceFarmRequest(project_arn="p", os_version="15")), "为网页时不得带"),
        (Job(scope_id="d", scope_name="d", engine="midscene", scenarios=j.scenarios, timeout_s=900.0, target=Target(device="android", ui_kind="app", app=None),
             device_request=DeviceFarmRequest(project_arn="p", os_version="15")), "必须带应用条目"),
        (dataclasses.replace(_ios_app_job(j.scenarios), target=Target(device=[], ui_kind="web")), "不是合法组合"),  # 错类型不抛 TypeError
    ]
    for job, match in cases:
        with pytest.raises(DefinitionContractError, match=match):
            validate_job_definition(job)


@pytest.mark.parametrize("mutate, match", [
    (lambda d: d.update(target="android/web"), "形态不对"),                      # target 不是对象
    (lambda d: d["target"].pop("device"), "不是合法组合"),                        # 缺 device
    (lambda d: d["target"].pop("ui_kind"), "不是合法组合"),
    (lambda d: d["target"].update(app="shop"), "形态不对"),                       # app 不是对象
    (lambda d: d["target"]["app"].pop("alias"), "应用条目缺 alias"),
    (lambda d: d["target"]["app"].pop("app_id"), "应用条目缺 app_id"),
    (lambda d: d.update(device_request="x"), "形态不对"),
    (lambda d: d["device_request"].pop("project_arn"), "缺 project_arn"),
    (lambda d: d["device_request"].pop("billing_method"), "缺 billing_method"),   # 读端不补缺省值
    (lambda d: d["device_request"].pop("acquire_timeout_s"), "有限正数"),
    (lambda d: d["device_request"].pop("provider"), "服务商未知"),
])
def test_job_from_dict_maps_missing_keys_and_wrong_shapes_to_definition_error(mutate, match):
    """读时校验（ADR 0048 决策 3）：键缺失与形态不对也归 DefinitionContractError（不漏 KeyError / TypeError），读端不替缺键补缺省值。"""
    from gherkai_core.errors import DefinitionContractError
    from gherkai_core.serialize import job_from_dict, job_to_dict

    j = _job_def("s", "s", "midscene")
    d = job_to_dict(_ios_app_job(j.scenarios))
    mutate(d)
    with pytest.raises(DefinitionContractError, match=match):
        job_from_dict(d)


def test_job_to_dict_keeps_target_for_illegal_desktop_app_so_read_side_can_reject():
    """写端只对 desktop/web 且无应用条目省键：非法的桌面应用目标不会因省键而在往返后变成合法的 desktop/web。"""
    from gherkai_core.errors import DefinitionContractError
    from gherkai_core.model import AppRef, Target
    from gherkai_core.serialize import job_from_dict, job_to_dict

    j = _job_def("s", "s", "midscene")
    bad = Job(scope_id="d", scope_name="d", engine="midscene", scenarios=j.scenarios,
              target=Target(device="desktop", ui_kind="app", app=AppRef(alias="a", app_id="b", bucket="c", key="d", sha256="e")))
    d = job_to_dict(bad)
    assert "target" in d
    with pytest.raises(DefinitionContractError, match="不是合法组合"):
        job_from_dict(d)


def test_job_from_dict_rejects_incomplete_app_entry_and_desktop_with_app():
    from gherkai_core.errors import DefinitionContractError
    from gherkai_core.model import AppRef, DeviceFarmRequest, Target
    from gherkai_core.serialize import job_from_dict, job_to_dict

    j = _job_def("s", "s", "midscene")
    dr = DeviceFarmRequest(project_arn="arn:p", device_arn="arn:d")
    for app in (AppRef(alias="shop", app_id="x"), AppRef(alias="shop", app_id="x", bucket="b", key="k", sha256=""),
                AppRef(alias="", app_id="x", bucket="b", key="k", sha256="h")):
        bad = Job(scope_id="ia", scope_name="ia", engine="midscene", scenarios=j.scenarios, timeout_s=900.0,
                  target=Target(device="ios", ui_kind="app", app=app), device_request=dr)
        with pytest.raises(DefinitionContractError, match="应用条目"):
            job_from_dict(job_to_dict(bad))
    d = job_to_dict(j)
    d["target"] = {"device": "desktop", "ui_kind": "app", "app": {"alias": "a", "app_id": "b", "bucket": "c", "key": "d", "sha256": "e"}}
    with pytest.raises(DefinitionContractError, match="不是合法组合"):
        job_from_dict(d)


def test_run_meta_extra_http_headers_round_trip():
    # RunMeta.extra_http_headers（ADR 0035 决策 4）：非空往返不丢；None/空表均省键（旧落盘兼容 + 空即无）
    import dataclasses

    from gherkai_core.serialize import run_meta_from_dict, run_meta_to_dict
    meta = _sample_run("h-run").run_meta
    assert run_meta_to_dict(meta)["extra_http_headers"] is None  # 默认 None → null（键集固定，ADR 0037 决策 7）
    assert run_meta_from_dict(run_meta_to_dict(meta)).extra_http_headers is None
    # 空 tuple 与 None 语义合一（都是「不注入额外头」）：同样写 null、读回 None，不落 {} 也不变形出 ()
    empty = dataclasses.replace(meta, extra_http_headers=())
    assert run_meta_to_dict(empty)["extra_http_headers"] is None
    assert run_meta_from_dict(run_meta_to_dict(empty)).extra_http_headers is None
    meta2 = dataclasses.replace(meta, extra_http_headers=(("ngrok-skip-browser-warning", "1"),))
    got = run_meta_from_dict(run_meta_to_dict(meta2))
    assert got.extra_http_headers == (("ngrok-skip-browser-warning", "1"),)


def test_run_meta_max_concurrency_round_trip():
    # RunMeta.max_concurrency（ADR 0034 机制四）：带值往返不丢；None 省键（旧落盘/旧提交侧无此键即回落）
    import dataclasses

    from gherkai_core.serialize import run_meta_from_dict, run_meta_to_dict
    meta = _sample_run("mc-run").run_meta
    assert run_meta_to_dict(meta)["max_concurrency"] is None  # 默认 None → null
    assert run_meta_from_dict(run_meta_to_dict(meta)).max_concurrency is None
    meta3 = dataclasses.replace(meta, max_concurrency=3)
    assert run_meta_to_dict(meta3)["max_concurrency"] == 3
    assert run_meta_from_dict(run_meta_to_dict(meta3)).max_concurrency == 3
    # 1 也必须落键（判真会把它当 None 省掉是另一码事，但 0 才是判真的真陷阱）：
    # `is not None` 判，于是 0 忠实往返、不被悄悄变形成 None（语义校验归组合根，序列化层不改值）
    zero = dataclasses.replace(meta, max_concurrency=0)
    assert run_meta_to_dict(zero)["max_concurrency"] == 0
    assert run_meta_from_dict(run_meta_to_dict(zero)).max_concurrency == 0


def test_run_meta_steps_dir_round_trip():
    """RunMeta.steps_dir（ADR 0037 决策 4）：带值往返不丢；None 省键（旧落盘 / 云端后端不写该字段）。

    载体在 definition 的理由：起 worker 的三个 local 宿主（同步 run / per-run 进程 / `status --wait` 接力者）
    CWD 各不相同，只有随 definition 走才对三者一致（core 只搬运、不消费语义）。
    """
    import dataclasses

    from gherkai_core.serialize import run_meta_from_dict, run_meta_to_dict
    meta = _sample_run("sd-run").run_meta
    assert run_meta_to_dict(meta)["steps_dir"] is None  # 默认 None → null
    assert run_meta_from_dict(run_meta_to_dict(meta)).steps_dir is None
    meta2 = dataclasses.replace(meta, steps_dir="/abs/project/steps")
    assert run_meta_to_dict(meta2)["steps_dir"] == "/abs/project/steps"
    assert run_meta_from_dict(run_meta_to_dict(meta2)).steps_dir == "/abs/project/steps"
    # `is not None` 判（同 max_concurrency）：空串这类无意义值也忠实往返、不在序列化层悄悄变形成「缺失」
    blank = dataclasses.replace(meta, steps_dir="")
    assert run_meta_to_dict(blank)["steps_dir"] == ""
    assert run_meta_from_dict(run_meta_to_dict(blank)).steps_dir == ""


def test_run_meta_worker_fields_round_trip():
    """RunMeta.worker_variant / worker_task_defs（ADR 0038）：带值往返不丢；None 省键（本机后端 / 旧落盘）。

    载体在 definition 的理由与 max_concurrency 同源（ADR 0034「随 definition 走、宿主只读回」）：起 task 的宿主
    （同步 run 的 FargateEngine / kicker / reconciler）与提交进程分离，只有随 META 持久化才到得了推进器；
    且「用的是哪套确定性 step 集」影响判定可复现性、本就属 run 定义。
    """
    import dataclasses

    from gherkai_core.serialize import run_meta_from_dict, run_meta_to_dict
    meta = _sample_run("wk-run").run_meta
    d0 = run_meta_to_dict(meta)
    assert d0["worker_variant"] is None and d0["worker_task_defs"] is None  # 默认 None → 双双 null
    got0 = run_meta_from_dict(d0)
    assert got0.worker_variant is None and got0.worker_task_defs is None

    arns = {"novaact": "arn:aws:ecs:us-east-1:1:task-definition/gherkai-novaact-worker:7",
            "midscene": "arn:aws:ecs:us-east-1:1:task-definition/gherkai-midscene-worker:3"}
    meta2 = dataclasses.replace(meta, worker_variant="login", worker_task_defs=arns)
    d2 = run_meta_to_dict(meta2)
    assert d2["worker_variant"] == "login" and d2["worker_task_defs"] == arns
    got2 = run_meta_from_dict(d2)
    assert got2.worker_variant == "login" and got2.worker_task_defs == arns
    assert got2 == meta2  # 逐字段恒等（往返忠实）

    # 各自独立（序列化层不替语义层做「有 A 必有 B」的把关）
    only_variant = dataclasses.replace(meta, worker_variant="base")
    assert run_meta_to_dict(only_variant)["worker_variant"] == "base"
    assert run_meta_to_dict(only_variant)["worker_task_defs"] is None
    # `is not None` 判（同 steps_dir）：空 dict 也忠实往返、不被悄悄变形成「缺失」
    empty = dataclasses.replace(meta, worker_task_defs={})
    assert run_meta_to_dict(empty)["worker_task_defs"] == {}
    assert run_meta_from_dict(run_meta_to_dict(empty)).worker_task_defs == {}


def test_run_meta_extra_http_headers_multiple_normalize_at_write_side():
    """≥2 个 header：写端按键排序规范化、读端原样保序 → 键值不丢、落盘键序确定，再往返逐字恒等。

    单 header 遮不住的两处：读端若 sorted 则「落盘顺序不等于读回顺序」（from_dict 不是 to_dict 的逆）；
    写端若原样则落盘内容随内存键序漂（同一份 header 表两种落盘形态）。
    """
    import dataclasses

    from gherkai_core.serialize import run_meta_from_dict, run_meta_to_dict
    meta = _sample_run("h2-run").run_meta
    hdrs = (("x-tunnel", "b"), ("ngrok-skip-browser-warning", "1"))  # 非字典序（x- 在前）
    meta2 = dataclasses.replace(meta, extra_http_headers=hdrs)
    d = run_meta_to_dict(meta2)
    assert list(d["extra_http_headers"]) == ["ngrok-skip-browser-warning", "x-tunnel"]  # 写端规范化
    got = run_meta_from_dict(d)
    assert dict(got.extra_http_headers) == dict(hdrs)  # 键值不丢
    assert got.extra_http_headers == (("ngrok-skip-browser-warning", "1"), ("x-tunnel", "b"))  # 读端保落盘序
    # 规范形上往返逐字恒等（写端规范化，故幂等）
    assert run_meta_from_dict(run_meta_to_dict(got)).extra_http_headers == got.extra_http_headers
    # 读端忠实还原落盘键序（手改落盘、键序非字典序）——若读端也 sorted，这条即挂
    unsorted = {**run_meta_to_dict(meta), "extra_http_headers": {"x-tunnel": "b", "ngrok-skip-browser-warning": "1"}}
    assert run_meta_from_dict(unsorted).extra_http_headers == (("x-tunnel", "b"), ("ngrok-skip-browser-warning", "1"))


# ---- definition 的结构版本与固定键集（ADR 0037 决策 7）----

def test_definition_schema_version_is_written_and_read_end_accepts_only_its_own():
    """写端恒写整数 schema_version；读端只认当前这一个：缺键读作 0 拒绝、高于拒绝（带写端 cli_version）、不是整数即定义违约；
    版本核在最前，版本不符时不再看别的键。"""
    from gherkai_core.errors import DefinitionContractError, UnsupportedDefinitionSchema
    from gherkai_core.serialize import DEFINITION_SCHEMA_VERSION, run_meta_from_dict, run_meta_to_dict

    d = run_meta_to_dict(_sample_run("v").run_meta)
    assert d["schema_version"] == DEFINITION_SCHEMA_VERSION == 1 and d["cli_version"] is None
    assert run_meta_from_dict(d).run_id == "v"
    with pytest.raises(UnsupportedDefinitionSchema) as ei:
        run_meta_from_dict({k: v for k, v in d.items() if k != "schema_version"})
    assert (ei.value.found, ei.value.supported, ei.value.cli_version) == (0, 1, None)
    with pytest.raises(UnsupportedDefinitionSchema) as ei:
        run_meta_from_dict({**d, "schema_version": 2, "cli_version": "9.9.0"})
    assert ei.value.found == 2 and ei.value.cli_version == "9.9.0" and "9.9.0" in str(ei.value)
    for bad in ("1", 1.0, True, None):
        with pytest.raises(DefinitionContractError, match="schema_version 须为整数"):
            run_meta_from_dict({**d, "schema_version": bad})
    with pytest.raises(UnsupportedDefinitionSchema):
        run_meta_from_dict({"schema_version": 2})  # 版本不符先于缺键


@pytest.mark.parametrize("key", ["cli_version", "run_id", "created_at", "jobs", "extra_http_headers", "max_concurrency", "steps_dir",
                                 "worker_variant", "worker_task_defs", "session_warmup_url"])
def test_definition_run_level_keys_are_all_required(key):
    """键集固定：run 级任一键缺失都是定义违约（不再用缺省值兜），值可为 null。"""
    from gherkai_core.errors import DefinitionContractError
    from gherkai_core.serialize import run_meta_from_dict, run_meta_to_dict

    d = run_meta_to_dict(_sample_run("k").run_meta)
    d.pop(key)
    with pytest.raises(DefinitionContractError, match=f"缺键 {key}"):
        run_meta_from_dict(d)


@pytest.mark.parametrize("key", ["scope_id", "scope_name", "engine", "scenarios", "assertion_votes", "timeout_s", "target", "device_request"])
def test_definition_job_level_keys_are_all_required(key):
    from gherkai_core.errors import DefinitionContractError
    from gherkai_core.serialize import run_meta_from_dict, run_meta_to_dict

    d = run_meta_to_dict(_sample_run("jk").run_meta)
    d["jobs"][0].pop(key)
    with pytest.raises(DefinitionContractError, match=f"缺键 {key}"):
        run_meta_from_dict(d)


def test_definition_target_must_be_an_object_even_for_desktop():
    from gherkai_core.errors import DefinitionContractError
    from gherkai_core.serialize import run_meta_from_dict, run_meta_to_dict

    d = run_meta_to_dict(_sample_run("t").run_meta)
    d["jobs"][0]["target"] = None
    with pytest.raises(DefinitionContractError, match="target"):
        run_meta_from_dict(d)


def test_run_meta_cli_version_and_session_warmup_url_round_trip():
    import dataclasses

    from gherkai_core.serialize import run_meta_from_dict, run_meta_to_dict
    meta = _sample_run("cv").run_meta
    d = run_meta_to_dict(meta)
    assert d["cli_version"] is None and d["session_warmup_url"] is None
    meta2 = dataclasses.replace(meta, cli_version="1.5.0",
                                session_warmup_url="https://h.example/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=T")
    d2 = run_meta_to_dict(meta2)
    assert d2["cli_version"] == "1.5.0" and d2["session_warmup_url"].endswith("=T")
    assert run_meta_from_dict(d2) == meta2


def test_report_from_dict_is_gated_by_definition_schema():
    """RunReport / manifest 经 run_meta_from_dict 读 definition，同受结构版本闸（读端只认当前版本，不分读的是哪种文件）。"""
    from gherkai_core.errors import UnsupportedDefinitionSchema
    from gherkai_core.serialize import from_dict, to_dict

    doc = to_dict(_sample_run("rep"))
    doc["run_meta"]["schema_version"] = 2
    with pytest.raises(UnsupportedDefinitionSchema):
        from_dict(doc)


def test_local_run_store_peeks_definition_header_without_full_read(tmp_path: Path):
    import dataclasses

    from gherkai_core.errors import UnsupportedDefinitionSchema
    from gherkai_core.model import run_state_from_result
    r = _sample_run("pk")
    store = LocalRunStore(tmp_path)
    store.create_run(dataclasses.replace(r.run_meta, cli_version="1.5.0"), run_state_from_result(r))
    assert store.peek_definition_header("pk") == (1, "1.5.0")
    assert store.peek_definition_header("nope") is None
    path = tmp_path / "pk" / "run_meta.json"
    d = json.loads(path.read_text(encoding="utf-8"))
    d["schema_version"] = 2
    path.write_text(json.dumps(d), encoding="utf-8")
    assert store.peek_definition_header("pk") == (2, "1.5.0")  # 只读头、不按本版本解释正文
    with pytest.raises(UnsupportedDefinitionSchema):
        store.load_run_meta("pk")


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


def test_step_message_survives_round_trip_and_missing_key_is_none():
    """step 级 message 写读两端同批（ADR 0042 决策三）：样例必须带**非默认**的 message——全 None 时
    to_dict/from_dict 往返照不出漏读端（默认值恰好相等的假绿）。旧落盘无此键 → None（向后兼容）。"""
    jr = _sample_run().jobs[0]
    jr.scenarios[0].steps[1] = StepResult(index=1, status=Status.FAILED, error_type="assertion_failed",
                                          message="AI 断言未过多数票（0/1）：搜索 OpenAI")
    d = job_result_to_dict(jr)
    assert d["scenarios"][0]["steps"][1]["message"] == "AI 断言未过多数票（0/1）：搜索 OpenAI"
    assert job_result_from_dict(d).scenarios[0].steps[1].message == "AI 断言未过多数票（0/1）：搜索 OpenAI"
    del d["scenarios"][0]["steps"][1]["message"]
    assert job_result_from_dict(d).scenarios[0].steps[1].message is None


@pytest.mark.parametrize("mutate, match", [
    (lambda d: d["jobs"][0]["scenarios"][0].pop("steps"), "缺键 steps"),
    (lambda d: d["jobs"][0]["scenarios"][0].pop("name"), "缺键 name"),
    (lambda d: d["jobs"][0]["scenarios"][0]["steps"][0].pop("text"), "缺键 text"),
    (lambda d: d["jobs"][0]["scenarios"][0]["steps"][0].update(argument={"kind": "docString"}), "缺键 content"),
    (lambda d: d["jobs"][0]["scenarios"][0]["steps"][0].update(argument={"kind": "dataTable"}), "缺键 rows"),
    (lambda d: d["jobs"][0]["scenarios"][0]["steps"][0].update(argument={"kind": "weird", "content": "x"}), "kind 未知"),
])
def test_definition_scenario_step_and_argument_keys_are_required(mutate, match):
    """键集固定下沿到 scenario / step / 多行参数：缺键是定义违约，读端不补空值（step 的 argument 本身可省：无参数的 step 不带它）。"""
    from gherkai_core.errors import DefinitionContractError
    from gherkai_core.serialize import run_meta_from_dict, run_meta_to_dict

    d = run_meta_to_dict(_sample_run("sc").run_meta)
    mutate(d)
    with pytest.raises(DefinitionContractError, match=match):
        run_meta_from_dict(d)


def test_run_state_message_is_omitted_when_none_and_round_trips_when_set():
    """RunState.message（ADR 0037 决策 7）按运行态既有惯例 omit-when-None：无值不出键，有值原文往返。"""
    from gherkai_core.model import JobState, RunState, Status
    from gherkai_core.serialize import run_state_from_dict, run_state_to_dict

    plain = RunState(run_id="r", status=Status.PASSED, jobs={"a": JobState("a", Status.PASSED)})
    assert "message" not in run_state_to_dict(plain)
    assert run_state_from_dict(run_state_to_dict(plain)).message is None
    told = RunState(run_id="r", status=Status.ERROR, jobs={}, message="提交记录不能由本后端执行：缺 worker 镜像版本")
    d = run_state_to_dict(told)
    assert d["message"] == told.message
    assert run_state_from_dict(d).message == told.message
