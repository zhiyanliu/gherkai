"""`--json` 字段契约的护栏（ADR 0041 决策五）：真渲染器出样例 → 递归收全部键名 → 逐个断言出现在
docs/internals/cli-json-contract.md 对应命令的那一节里（反引号包裹）。文档漏键即红——文档不靠人读维护，靠真值集对照（CLAUDE.md 文档纪律）。

按节核对而非全页：同名键在别的节写过（如 plan 的 `keywords`）不能替本节的漏写兜底。节间「形状同 `run --json`」式的引用
由 `SECTION_REFS` 显式登记放行。

list-workers 的样例要 moto，护栏放 deploy_aws/tests/test_workers.py，读同一份文档。
"""
from __future__ import annotations

import dataclasses
import json
import re
from pathlib import Path

from gherkai_core import model as M
from gherkai_core.serialize import run_state_to_dict
from gherkai_core.target import validate_job_definition

from gherkai_cli import __main__ as m
from gherkai_cli import render
from gherkai_cli.config import DevicePlatformConfig, DevicesConfig, ProjectConfig
from gherkai_cli.device_selection import build_device_request, resolve_device_selection
from gherkai_runtime import compose

DOC = Path(__file__).resolve().parents[2] / "docs" / "internals" / "cli-json-contract.md"

# 节引用白名单：契约页对与另一节形状相同的子结构只写一处，本节写一句「形状同 …」指过去（不复制表格，免得两处各自漂移）。
# 外层键是被核对的节，内层键是样例里的键名、值是该键**以下**各键另可在哪一节里找到（在本节写出同样算数；该键本身只在本节核对）。只登记文档里确有这句
# 引用的结构，删了引用句就该删这里的条目。
SECTION_REFS: dict[str, dict[str, str]] = {
    "plan": {"jobs": "run"},  # plan 一节：`jobs[]` 与 `run_meta.jobs[]` 结构相同
    # explain 一节：`sessions[]` 与 `report_refs[]` 的形状同 `run --json`；`steps[]` 的 `votes` 同 `run --json` 的 `steps[]`
    "explain": {"sessions": "run", "report_refs": "run", "votes": "run"},
}


def _sections() -> dict[str, str]:
    """契约页按 `## ` 标题切节：键是标题里 `gherkai` 之后的命令名（`run`、`list-deterministic`、`deploy list-workers`…，
    到第一个占位、省略号或选项为止），值是该节全文（含其下的 `###` 子节）。第一个 `## ` 之前的头部与通则不属于任何命令。"""
    sections: dict[str, str] = {}
    for chunk in re.split(r"^## ", DOC.read_text(encoding="utf-8"), flags=re.M)[1:]:
        heading = chunk.partition("\n")[0]
        hit = re.match(r"`gherkai ([a-z][a-z-]*(?: [a-z][a-z-]*)*)", heading)
        assert hit, f"契约页的节标题应形如「`gherkai <命令> … --json`」，现为 {heading!r}：改标题，或改这里的切法"
        assert hit.group(1) not in sections, f"契约页有两节的命令名都是 {hit.group(1)!r}"
        sections[hit.group(1)] = chunk
    return sections


def _documented_keys(text: str) -> set[str]:
    """一段文档里以反引号写出的键名。合法书写形态：`key`、`a` / `b`（一格两个键）、`engines.<engine>.family`（取路径末段）、
    `jobs[]`（数组键，比对时去掉 `[]`）。"""
    keys = set()
    for token in re.findall(r"`([A-Za-z_][A-Za-z0-9_.<>/ \[\]]*?)`", text):
        for part in re.split(r"\s*/\s*", token):
            keys.add(part.split(".")[-1].rstrip("[]"))
    return keys


def _sample_keys(o, where: frozenset[str], *, refs: "dict[str, str]", opaque: "set[str]",
                 out: "set[tuple[str, frozenset[str]]] | None" = None) -> set[tuple[str, frozenset[str]]]:
    """递归收全部 dict 键名，每个键带上「可以在哪些节里找到它」（只取键名本身，不含路径——文档按键名解释）。

    where 起初只有本节；下钻经过 refs 里登记的键时，其下各键另可在被引用的节里找到。
    opaque 是「到这个键就停止下钻」的键名集（该键本身仍要文档化，它的子键不属本契约）：用于引擎原样透传的
    对象（explain 的 `args` / `result`，内部键随 SDK 漂移，ADR 0042 决策四）。**与 ignore 不同**：ignore 是
    「这个键名不用写进文档」，会连同名的真契约键一起放过；opaque 只切断该节点以下的递归。
    """
    out = set() if out is None else out
    if isinstance(o, dict):
        for k, v in o.items():
            out.add((k, where))
            if k not in opaque:
                _sample_keys(v, where | {refs[k]} if k in refs else where, refs=refs, opaque=opaque, out=out)
    elif isinstance(o, list):
        for v in o:
            _sample_keys(v, where, refs=refs, opaque=opaque, out=out)
    return out


def _assert_documented(sample, *, section: str, ignore: set[str] = frozenset(),
                       opaque: "set[str]" = frozenset()) -> None:
    """section 是契约页的节名（`_sections` 的键）；样例里的每个键只在本节与 `SECTION_REFS` 登记的被引用节里找。"""
    sections = _sections()
    refs = SECTION_REFS.get(section, {})
    documented = {name: _documented_keys(sections[name]) for name in {section, *refs.values()}}
    missing = sorted({k for k, where in _sample_keys(sample, frozenset({section}), refs=refs, opaque=opaque)
                      if k not in ignore and not any(k in documented[w] for w in where)})
    assert not missing, (f"[{section}] 这些键出现在真实输出里、契约页「{section}」一节没写：{missing}——改 "
                         "docs/internals/cli-json-contract.md 的对应节（与别节形状相同、只写引用句的结构登记进 SECTION_REFS）")


def _mk(cls, **kw):
    names = {f.name for f in dataclasses.fields(cls)}
    return cls(**{k: v for k, v in kw.items() if k in names})


_DF_ARN = "arn:aws:devicefarm:us-west-2:123456789012:session:p/s/00000"  # 真形状的会话 ARN：explain 才会给 console_url
_DF_PROJECT = "arn:aws:devicefarm:us-west-2:123456789012:project:p"
_DF_DEVICE = "arn:aws:devicefarm:us-west-2::device:ABCDEF0123456789"
_CONFIG = ProjectConfig(path=Path("/p/gherkai.toml"),
                        devices=DevicesConfig(platforms={"ios": DevicePlatformConfig(os_version="17")}))


def _device_selections() -> dict:
    """两个平台的设备选择，经真解析函数得出：Android 由选项指定一台（`arn`），iOS 由配置文件按系统版本挑选（`os_version`）——
    plan 的 `devices` 两种形态与设备请求的 `device_arn` / `os_version` 两个二选一键都进差集。"""
    return {"android": resolve_device_selection("android", flag_arn=_DF_DEVICE, env={}, config=_CONFIG),
            "ios": resolve_device_selection("ios", flag_arn=None, env={}, config=_CONFIG)}


def _sample_run_result() -> M.RunResult:
    """把所有可选字段都填上（votes/cost/report_refs/argument 两种/extra headers/worker_variant/设备目标…），键才收得全。

    三个 job：桌面网页、Android 应用（应用条目五项齐全、设备请求指定一台）、iOS 网页（设备请求按系统版本挑选）；设备请求由
    `build_device_request` 从设备选择合成，与 run / submit 的组合根同一条路。"""
    steps = (M.Step(0, "Given", '打开 "https://x"'),
             M.Step(1, "When", "搜索", argument=M.StepArgument(kind="docString", content="c")),
             M.Step(2, "Then", "对吗", argument=M.StepArgument(kind="dataTable", rows=(("a", "b"),))))
    job = _mk(M.Job, scope_id="f.feature:3", scope_name="登录", engine="novaact",
              scenarios=(M.Scenario(id="f.feature:3", name="登录", steps=steps),), assertion_votes=3, timeout_s=300.0)
    sr = _mk(M.ScenarioResult, scenario_id="f.feature:3", status=M.Status.FAILED, duration_ms=12.0,
             report_refs=(M.ReportRef(kind="report", ref="file:///r.html", label="r"),), steps=[
                 _mk(M.StepResult, index=0, status=M.Status.PASSED, duration_ms=1.0),
                 _mk(M.StepResult, index=1, status=M.Status.FAILED, duration_ms=2.0, votes=M.Votes(yes=1, total=3),
                     error_type="assertion_failed", report_refs=(M.ReportRef(kind="trajectory", ref="file:///a.html", label="t"),)),
                 _mk(M.StepResult, index=2, status=M.Status.SKIPPED, shortcircuited=True)])
    jr = _mk(M.JobResult, job=job, status=M.Status.FAILED, scenarios=[sr], session_id="s", duration_ms=20.0,
             total_time_worked_s=3.5, total_tokens=120, error_type="timeout", message="m",
             report_refs=(M.ReportRef(kind="summary", ref="file:///s.json", label="summary"),))
    sel = _device_selections()
    # 设备 job（ADR 0051 决策 4、7）：三种 origin 的会话各一项、两个计量键、scope 级 error 后合成的 skipped（shortcircuited=False）
    dev_steps = (M.Step(0, "When", "点击登录"), M.Step(1, "Then", "对吗"))
    dev_job = _mk(M.Job, scope_id="d.feature:3", scope_name="设备", engine="midscene",
                  scenarios=(M.Scenario(id="d.feature:3", name="设备", steps=dev_steps),), timeout_s=1500.0,
                  target=M.Target(device="android", ui_kind="app",
                                  app=M.AppRef(alias="shop", app_id="com.example.shop", bucket="b",
                                               key="apps/shop.apk", sha256="0" * 64)),
                  device_request=build_device_request(sel["android"], project_arn=_DF_PROJECT, billing_method="METERED",
                                                      acquire_timeout_s=600.0))
    dev_sr = _mk(M.ScenarioResult, scenario_id="d.feature:3", status=M.Status.SKIPPED, steps=[
        _mk(M.StepResult, index=0, status=M.Status.SKIPPED, shortcircuited=False),
        _mk(M.StepResult, index=1, status=M.Status.SKIPPED, shortcircuited=False)])
    sessions = [_mk(M.SessionRecord, session_id=_DF_ARN, name="n-a", origin="created", release="confirmed", observed_s=10.0,
                    provider_minutes={"total": 1, "metered": 1, "unmetered": 0},
                    device={"platform": "android", "model": "Pixel 8", "osVersion": "14", "unit": "u"}),
                _mk(M.SessionRecord, session_id="arn:b", name="n-b", origin="discovered", release="unconfirmed", observed_s=None),
                _mk(M.SessionRecord, session_id=None, name="n-c", origin="attempted", release="unconfirmed")]
    dev_jr = _mk(M.JobResult, job=dev_job, status=M.Status.ERROR, scenarios=[dev_sr], session_id=_DF_ARN,
                 error_type="release_failed", message="m", sessions=sessions, device_observed_s=10.0, device_observed_missing=1)
    ios_steps = (M.Step(0, "Given", '"https://x"'), M.Step(1, "Then", "对吗"))
    ios_job = _mk(M.Job, scope_id="i.feature:3", scope_name="iOS 网页", engine="midscene",
                  scenarios=(M.Scenario(id="i.feature:3", name="iOS 网页", steps=ios_steps),), timeout_s=1500.0,
                  target=M.Target(device="ios", ui_kind="web"),
                  device_request=build_device_request(sel["ios"], project_arn=_DF_PROJECT, billing_method="UNMETERED",
                                                      acquire_timeout_s=600.0))
    ios_sr = _mk(M.ScenarioResult, scenario_id="i.feature:3", status=M.Status.PASSED, duration_ms=8.0, steps=[
        _mk(M.StepResult, index=0, status=M.Status.PASSED, duration_ms=3.0),
        _mk(M.StepResult, index=1, status=M.Status.PASSED, duration_ms=5.0, votes=M.Votes(yes=1, total=1))])
    ios_jr = _mk(M.JobResult, job=ios_job, status=M.Status.PASSED, scenarios=[ios_sr], session_id="arn:i", duration_ms=9.0,
                 sessions=[_mk(M.SessionRecord, session_id="arn:i", name="n-i", origin="created", release="confirmed",
                               observed_s=5.0)], device_observed_s=5.0, device_observed_missing=0)
    meta = _mk(M.RunMeta, run_id="r", created_at="t", jobs=(job, dev_job, ios_job), max_concurrency=2, steps_dir="/p/steps",
               worker_variant="base", worker_task_defs={"novaact": "arn"}, extra_http_headers=(("X-Test", "y"),))
    return _mk(M.RunResult, run_meta=meta, status=M.Status.ERROR, jobs=[jr, dev_jr, ios_jr], duration_ms=30.0,
               total_time_worked_s=3.5, total_tokens=120, device_observed_s=15.0, device_observed_missing=1)


def test_run_json_keys_are_documented():
    result = _sample_run_result()
    for j in result.run_meta.jobs:
        validate_job_definition(j)  # 样例是合法的 definition 形态（应用条目五项齐全、设备 job 带设备请求与墙钟预算）
    doc = render.to_dict(result)
    doc["artifacts"] = {**compose.local_artifact_locations("/tmp/x", "r"), "worker_log": "file:///tmp/w.log"}
    # 正向断言：样例里确实有远程访问会话与计量键（_mk 会悄悄丢掉 model 里还没有的字段，没有这条护栏会在空集上直接变绿）
    dev = next(j for j in doc["jobs"] if j["scope_id"] == "d.feature:3")
    assert {"sessions", "device_observed_s", "device_observed_missing"} <= set(dev) and len(dev["sessions"]) == 3
    assert {"device_observed_s", "device_observed_missing"} <= set(doc)
    assert "sessions" not in next(j for j in doc["jobs"] if j["scope_id"] == "f.feature:3")  # 没有会话记录的桌面 job 省键
    # 正向断言：definition 里有设备目标的完整形态——应用条目五项、设备请求的两种二选一形态
    defs = {j["scope_id"]: j for j in doc["run_meta"]["jobs"]}
    assert set(defs["d.feature:3"]["target"]["app"]) == {"alias", "app_id", "bucket", "key", "sha256"}
    assert {"device_arn", "provider", "billing_method", "project_arn", "acquire_timeout_s"} <= set(defs["d.feature:3"]["device_request"])
    assert "os_version" in defs["i.feature:3"]["device_request"]
    # extra_http_headers / worker_task_defs 的**值**是用户自定键（请求头名 / 引擎名），不是契约键；provider_minutes 是服务商原形快照、
    # 对 core 不透明（ADR 0051 决策 7），到它为止不下钻
    _assert_documented(doc, section="run", ignore={"X-Test", "novaact"}, opaque={"provider_minutes", "device"})


def _plan_form(job: M.Job) -> M.Job:
    """definition 形态 → plan 形态：plan 不解析设备请求（恒 null），应用条目只有别名与包名（安装包在 run / submit 时才上传）。"""
    app = job.target.app
    target = job.target if app is None else dataclasses.replace(job.target, app=M.AppRef(alias=app.alias, app_id=app.app_id))
    return dataclasses.replace(job, target=target, device_request=None)


def test_plan_json_keys_are_documented():
    jobs = [_plan_form(j) for j in _sample_run_result().run_meta.jobs]
    dispatch = {("f.feature:3", "f.feature:3", 0): {"pattern": "p", "description": "d"},
                ("f.feature:3", "f.feature:3", 1): {"conflict": ["a", "b"]},
                ("f.feature:3", "f.feature:3", 2): {"keyword_mismatch": "p", "keywords": ["Given", "When"]},
                # 命中条目在该 scope 目标上带运行期前提（ADR 0049 决策 6）：deterministic 另带 requires
                ("i.feature:3", "i.feature:3", 0): {"pattern": "p", "description": "d", "requires": ["web_context"]}}
    doc = render.plan_to_dict(jobs, "novaact", dispatch, _device_selections())
    by_scope = {j["scope_id"]: j for j in doc["jobs"]}
    assert by_scope["i.feature:3"]["scenarios"][0]["steps"][0]["deterministic"]["requires"] == ["web_context"]
    # 正向断言：两个平台的设备选择各是一种形态，应用条目是 plan 形态（少一项设备选择，`devices` 的子键就不进差集）
    assert set(doc["devices"]["android"]) == {"arn", "source"} and set(doc["devices"]["ios"]) == {"os_version", "source"}
    assert set(by_scope["d.feature:3"]["target"]["app"]) == {"alias", "app_id"}
    _assert_documented(doc, section="plan")


def test_status_json_keys_are_documented():
    st = M.RunState(run_id="r", status=M.Status.PASSED,
                    jobs={"a": M.JobState("a", M.Status.PASSED, session_id="s", claimed_at="t")},
                    started_at="t0", ended_at="t9", high_water_mark=3)
    doc = run_state_to_dict(st)
    doc["artifacts"] = compose.cloud_artifact_locations(bucket="b", report_prefix="reports", table="t", run_id="r")
    _assert_documented(doc, section="status")
    # 云端推进链不经任何 job 就把 run 置为 error 时的形态：run 级 `message`，job 仍是未认领的 pending
    st_error = M.RunState(run_id="r", status=M.Status.ERROR, jobs={"a": M.JobState("a", M.Status.PENDING)},
                          started_at="t0", ended_at="t1", high_water_mark=0, message="m")
    doc_error = run_state_to_dict(st_error)
    assert "message" in doc_error
    _assert_documented(doc_error, section="status")


def test_list_engines_and_deterministic_json_keys_are_documented(monkeypatch, capsys):
    def fake(name, *, version=None):
        if name == "novaact":
            return compose.WorkerCmd(cmd=["python", "-m", "gherkai_worker_novaact"], cwd=None, source="同 venv 模块 gherkai_worker_novaact")
        raise compose.WorkerNotFoundError(name, "未找到")
    monkeypatch.setattr(m.compose, "resolve_worker_cmd", fake)
    _assert_documented(m._probe_engines(), section="list-engines")
    # list-deterministic：样例取真实命令的 --json 输出（worker 原样条目加 CLI 追加的 available_targets，ADR 0049 决策 6），
    # 以后 CLI 再追加键也进对照
    monkeypatch.setattr(m.compose, "query_capabilities", lambda engine, *, steps_dir=None, timeout_s=60.0: {
        "schema_version": 2, "engine": engine, "min_grace_s": 150.0, "model_id": "nova-act-v1.0",
        "targets": [{"device": "desktop", "ui_kinds": ["web"]}],
        "deterministic_steps": [{"pattern": "p", "description": "d", "example": "e", "keywords": ["Given", "When"],
                                 "targets": [{"device": "desktop", "ui_kinds": ["web"]},
                                             {"device": "android", "ui_kinds": ["web"], "requires": ["web_context"]}]}]})
    assert m.main(["list-deterministic", "--engine", "novaact", "--json"]) == 0
    _assert_documented(json.loads(capsys.readouterr().out), section="list-deterministic")


def _stub_local_doctor(monkeypatch):
    """doctor 本机各段的替身：两个引擎都定位得到、自述带全部键，没有部署 provider。"""
    monkeypatch.setattr(m.compose, "resolve_worker_cmd",
                        lambda name, *, version=None: compose.WorkerCmd(cmd=["x"], cwd=None, source="s"))
    monkeypatch.setattr(m._deploy, "provider_entry_points", lambda: [])
    monkeypatch.setattr(m._deploy, "resolve_provider", lambda name=None: (None, "没有可用的部署 provider"))
    monkeypatch.setattr(m.compose, "query_capabilities", lambda engine, *, steps_dir=None, timeout_s=60.0: {
        "schema_version": 2, "engine": engine, "min_grace_s": 150.0, "deterministic_steps": [],
        "targets": [{"device": "desktop", "ui_kinds": ["web"]}, {"device": "android", "ui_kinds": ["web"], "max_session_s": 8880}],
        "model_id": "nova-act-v1.0"})  # 自述六键齐（doctor 的模型行取 model_id、目标行取 targets，ADR 0036「5.」、0049 决策 6）


def _assert_check_names_documented(doc) -> None:
    """项名是 `name` 的**值**，键名护栏照不出它：把按引擎后缀的项名归一成 `<engine>` 形态后逐个核对契约页 doctor 一节里写了。"""
    page = _sections()["doctor"]
    for name in {c["name"] for c in doc["checks"]}:
        generic = re.sub(r"\.(novaact|midscene)$", ".<engine>", name)
        assert f"`{generic}`" in page, f"[doctor] 项名 {name}（{generic}）没写进 docs/internals/cli-json-contract.md 的 doctor 一节"


def test_doctor_json_keys_are_documented(monkeypatch, capsys):
    _stub_local_doctor(monkeypatch)
    assert m.main(["doctor", "--json"]) == 0
    doc = json.loads(capsys.readouterr().out)
    _assert_documented(doc, section="doctor")
    _assert_check_names_documented(doc)


def test_doctor_cloud_json_keys_are_documented(monkeypatch, capsys):
    """云端变体：AWS 调用全部打桩（身份、版本戳、资源、默认 variant 与解析、停止宽限、Device Farm 项目参数与会话列举），
    让 `_doctor_cloud` 一路走到设备支持两行：项目已部署、有一个未结束的会话，`backend.devices.sessions` 才会出现。
    本机变体只走到云端未查的占位，aws / backend 两段的真实项名要靠这一条进差集。"""
    from datetime import datetime, timezone

    from gherkai_runtime import devicefarm

    _stub_local_doctor(monkeypatch)
    monkeypatch.setattr(m.compose, "probe_aws_identity", lambda *, region, profile: {
        "account": "123456789012", "arn": "arn:aws:sts::123456789012:assumed-role/r/s", "region": region})
    monkeypatch.setattr(m.compose, "check_backend_skew", lambda **kw: (compose.SKEW_OK, "", "1.5.0"))
    monkeypatch.setattr(m.compose, "preflight_cloud_resources", lambda **kw: None)
    monkeypatch.setattr(m.compose, "read_worker_default", lambda **kw: "base")
    monkeypatch.setattr(m.compose, "resolve_worker_variant", lambda **kw: {
        e: compose.WorkerResolution(engine=e, variant=kw["variant"], revision_arn=f"arn:{e}:7", digest="sha256:0")
        for e in kw["engines"]})
    monkeypatch.setattr(m.compose, "read_task_def_stop_timeout",
                        lambda revision_arn, *, engine, region=None, profile=None, ecs=None: 120)
    monkeypatch.setattr(m.compose, "read_device_farm_project", lambda **kw: _DF_PROJECT)
    monkeypatch.setattr(devicefarm, "list_open_sessions", lambda project_arn, *, profile: [
        devicefarm.OpenSession(arn=_DF_ARN, name="gherkai-r-s", status="RUNNING",
                               created=datetime(2026, 10, 29, 8, 0, tzinfo=timezone.utc))])
    assert m.main(["doctor", "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1", "--json"]) == 0
    doc = json.loads(capsys.readouterr().out)
    by = {(c["section"], c["name"]): c for c in doc["checks"]}
    # 正向断言：打桩确实让 doctor 走到了云端各项与设备两行（少一个替身就会提前结束，差集在缺项上直接变绿）
    assert {("aws", "region"), ("aws", "identity"), ("backend", "version"), ("backend", "resources"),
            ("backend", "worker.default"), ("backend", "worker.any"), ("backend", "worker.grace"),
            ("backend", "devices.project"), ("backend", "devices.sessions")} <= set(by)
    assert _DF_ARN in by[("backend", "devices.sessions")]["detail"]
    _assert_documented(doc, section="doctor")
    _assert_check_names_documented(doc)


def _sample_evidence() -> dict:
    """手搭的 evidence 夹具（ADR 0042 决策一的 schema，固定键全填）——形状与两引擎映射测试用的真产物裁剪版一致。

    `frames[].actions[].args` 与 `acts[].result` 内塞了引擎侧的键（`box` / `matches_schema`…）：它们是引擎原样
    透传的对象、不属本契约，护栏须在这两个节点停止下钻——若 opaque 机制失效，这些键会漏进比对、本用例立刻变红。
    """
    return {
        "schema_version": 1, "engine": "novaact", "scope_id": "f.feature:3",
        "scenario_id": "f.feature:3", "step_index": 2,
        "step": {"keyword": "Then", "text": "对吗"},
        "status": "failed", "message": "AI 断言未过多数票（0/1）：对吗",
        # 设备目标的加键（ADR 0051 决策 8）：全部填上，键才进差集
        "step_kind": "ai", "url": None, "url_missing": "no_web_context",
        "controls": {"items": [{"type": "Button", "id": "login", "text": "登录", "a11y_id": "btn-login"}], "total": 1, "truncated": False},
        "controls_missing": None, "page_source": "file:///r/page-source.xml", "page_source_truncated": False,
        "acts": [{
            "index": 0, "prompt": "对吗", "vote": False, "url": "https://x/login",
            "frames": [{"url": "https://x/login", "thought": "Returning false.",
                        "actions": [{"name": "agentClick", "args": {"box": "1,2,3,4"}}],
                        "screenshot": "file:///r/act-0-frame-1.jpg"}],
            "result": {"matches_schema": True, "parsed_response": "false"},
            "error": "ActError: timed out", "time_worked_s": 9.8,
        }],
    }


def test_explain_json_keys_are_documented():
    """explain 的样例由**真渲染器**从手搭 JobResult + evidence 夹具生成（否则 evidence 那批键根本不进比对）；桌面与设备 job 各一个，
    设备 job 的 sessions[] 与两个计量键也进差集。"""
    doc = render.explain_to_dict(run_id="r", status="failed", results=list(_sample_run_result().jobs),
                                 evidence_reader=lambda refs: (_sample_evidence(), None))
    dev = next(s for s in doc["scopes"] if s["scope_id"] == "d.feature:3")
    assert {"sessions", "device_observed_s", "device_observed_missing", "console_url"} <= set(dev) and len(dev["sessions"]) == 3  # 正向断言，防空集变绿
    assert "sessions" not in next(s for s in doc["scopes"] if s["scope_id"] == "f.feature:3")
    _assert_documented(doc, section="explain", opaque={"args", "result", "provider_minutes", "device"})
