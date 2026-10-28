"""`--json` 字段契约的护栏（ADR 0041 决策五）：真渲染器出样例 → 递归收全部键名 → 逐个断言出现在
docs/internals/cli-json-contract.md 里（反引号包裹）。文档漏键即红——文档不靠人读维护，靠真值集对照（CLAUDE.md 文档纪律）。

list-workers 的样例要 moto，护栏放 deploy_aws/tests/test_workers.py，读同一份文档。
"""
from __future__ import annotations

import dataclasses
import json
import re
from pathlib import Path

from gherkai_core import model as M
from gherkai_core.serialize import run_state_to_dict

from gherkai_cli import __main__ as m
from gherkai_cli import render
from gherkai_runtime import compose

DOC = Path(__file__).resolve().parents[2] / "docs" / "internals" / "cli-json-contract.md"


def _documented_keys() -> set[str]:
    return set(re.findall(r"`([A-Za-z_][A-Za-z0-9_.<>/ \[\]]*?)`", DOC.read_text(encoding="utf-8")))


def _leaf_keys(o, out: set[str] | None = None, *, opaque: "set[str]" = frozenset()) -> set[str]:
    """递归收全部 dict 键名（只取键名本身，不含路径——文档按键名解释）。

    opaque 是「到这个键就停止下钻」的键名集（该键本身仍要文档化，它的子键不属本契约）：用于引擎原样透传的
    对象（explain 的 `args` / `result`，内部键随 SDK 漂移，ADR 0042 决策四）。**与 ignore 不同**：ignore 是
    「这个键名不用写进文档」，会连同名的真契约键一起放过；opaque 只切断该节点以下的递归。
    """
    out = set() if out is None else out
    if isinstance(o, dict):
        for k, v in o.items():
            out.add(k)
            if k not in opaque:
                _leaf_keys(v, out, opaque=opaque)
    elif isinstance(o, list):
        for v in o:
            _leaf_keys(v, out, opaque=opaque)
    return out


def _assert_documented(sample, *, section: str, ignore: set[str] = frozenset(),
                       opaque: "set[str]" = frozenset()) -> None:
    documented = _documented_keys()
    # 文档里合法的书写形态：`key` / `a` / `b`（两个键一格）/ `engines.<engine>.family`（路径末段）
    flat = set()
    for token in documented:
        for part in re.split(r"\s*/\s*", token):
            flat.add(part.split(".")[-1].rstrip("[]"))  # 文档里数组键写成 `jobs[]`，比对时按键名
    missing = sorted(k for k in _leaf_keys(sample, opaque=opaque) if k not in flat and k not in ignore)
    assert not missing, f"[{section}] 这些键出现在真实输出里、文档没写：{missing}——改 docs/internals/cli-json-contract.md"


def _mk(cls, **kw):
    names = {f.name for f in dataclasses.fields(cls)}
    return cls(**{k: v for k, v in kw.items() if k in names})


_DF_ARN = "arn:aws:devicefarm:us-west-2:123456789012:session:p/s/00000"  # 真形状的会话 ARN：explain 才会给 console_url


def _sample_run_result() -> M.RunResult:
    """把所有可选字段都填上（votes/cost/report_refs/argument 两种/extra headers/worker_variant…），键才收得全。"""
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
    # 设备 job（ADR 0051 决策 4、7）：三种 origin 的会话各一项、两个计量键、scope 级 error 后合成的 skipped（shortcircuited=False）
    dev_steps = (M.Step(0, "Given", '"https://x"'), M.Step(1, "Then", "对吗"))
    dev_job = _mk(M.Job, scope_id="d.feature:3", scope_name="设备", engine="midscene",
                  scenarios=(M.Scenario(id="d.feature:3", name="设备", steps=dev_steps),), timeout_s=600.0)
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
    meta = _mk(M.RunMeta, run_id="r", created_at="t", jobs=(job, dev_job), max_concurrency=2, steps_dir="/p/steps",
               worker_variant="base", worker_task_defs={"novaact": "arn"}, extra_http_headers=(("X-Test", "y"),))
    return _mk(M.RunResult, run_meta=meta, status=M.Status.ERROR, jobs=[jr, dev_jr], duration_ms=30.0,
               total_time_worked_s=3.5, total_tokens=120, device_observed_s=10.0, device_observed_missing=1)


def test_run_json_keys_are_documented():
    doc = render.to_dict(_sample_run_result())
    doc["artifacts"] = {**compose.local_artifact_locations("/tmp/x", "r"), "worker_log": "file:///tmp/w.log"}
    # 正向断言：样例里确实有远程访问会话与计量键（_mk 会悄悄丢掉 model 里还没有的字段，没有这条护栏会在空集上直接变绿）
    dev = next(j for j in doc["jobs"] if j["scope_id"] == "d.feature:3")
    assert {"sessions", "device_observed_s", "device_observed_missing"} <= set(dev) and len(dev["sessions"]) == 3
    assert {"device_observed_s", "device_observed_missing"} <= set(doc)
    assert "sessions" not in next(j for j in doc["jobs"] if j["scope_id"] == "f.feature:3")  # 桌面 job 省键
    # extra_http_headers / worker_task_defs 的**值**是用户自定键（请求头名 / 引擎名），不是契约键；provider_minutes 是服务商原形快照、
    # 对 core 不透明（ADR 0051 决策 7），到它为止不下钻
    _assert_documented(doc, section="run --json", ignore={"X-Test", "novaact"}, opaque={"provider_minutes", "device"})


def test_plan_json_keys_are_documented():
    job = _sample_run_result().run_meta.jobs[0]
    dispatch = {("f.feature:3", "f.feature:3", 0): {"pattern": "p", "description": "d"},
                ("f.feature:3", "f.feature:3", 1): {"conflict": ["a", "b"]},
                ("f.feature:3", "f.feature:3", 2): {"keyword_mismatch": "p", "keywords": ["Given", "When"]}}
    _assert_documented(render.plan_to_dict([job], "novaact", dispatch), section="plan --json")


def test_status_json_keys_are_documented():
    st = M.RunState(run_id="r", status=M.Status.PASSED,
                    jobs={"a": M.JobState("a", M.Status.PASSED, session_id="s", claimed_at="t")},
                    started_at="t0", ended_at="t9", high_water_mark=3)
    doc = run_state_to_dict(st)
    doc["artifacts"] = compose.cloud_artifact_locations(bucket="b", report_prefix="reports", table="t", run_id="r")
    _assert_documented(doc, section="status --json")


def test_list_engines_and_deterministic_json_keys_are_documented(monkeypatch, capsys):
    def fake(name, *, version=None):
        if name == "novaact":
            return compose.WorkerCmd(cmd=["python", "-m", "gherkai_worker_novaact"], cwd=None, source="同 venv 模块 gherkai_worker_novaact")
        raise compose.WorkerNotFoundError(name, "未找到")
    monkeypatch.setattr(m.compose, "resolve_worker_cmd", fake)
    _assert_documented(m._probe_engines(), section="list-engines --json")
    # list-deterministic：样例取真实命令的 --json 输出（worker 原样条目加 CLI 追加的 available_targets，ADR 0049 决策 6），
    # 以后 CLI 再追加键也进对照
    monkeypatch.setattr(m.compose, "query_capabilities", lambda engine, *, steps_dir=None, timeout_s=60.0: {
        "schema_version": 1, "engine": engine, "min_grace_s": 150.0, "model_id": "nova-act-v1.0",
        "targets": [{"device": "desktop", "ui_kinds": ["web"]}],
        "deterministic_steps": [{"pattern": "p", "description": "d", "example": "e", "keywords": ["Given", "When"],
                                 "targets": [{"device": "desktop", "ui_kinds": ["web"]},
                                             {"device": "android", "ui_kinds": ["web"], "requires": ["web_context"]}]}]})
    assert m.main(["list-deterministic", "--engine", "novaact", "--json"]) == 0
    _assert_documented(json.loads(capsys.readouterr().out), section="list-deterministic --json")


def test_doctor_json_keys_are_documented(monkeypatch, capsys):
    monkeypatch.setattr(m.compose, "resolve_worker_cmd",
                        lambda name, *, version=None: compose.WorkerCmd(cmd=["x"], cwd=None, source="s"))
    monkeypatch.setattr(m._deploy, "provider_entry_points", lambda: [])
    monkeypatch.setattr(m._deploy, "resolve_provider", lambda name=None: (None, "没有可用的部署 provider"))
    monkeypatch.setattr(m.compose, "query_capabilities", lambda engine, *, steps_dir=None, timeout_s=60.0: {
        "schema_version": 1, "engine": engine, "min_grace_s": 150.0, "deterministic_steps": [],
        "targets": [{"device": "desktop", "ui_kinds": ["web"]}, {"device": "android", "ui_kinds": ["web"], "max_session_s": 8880}],
        "model_id": "nova-act-v1.0"})  # 自述六键齐（doctor 的模型行取 model_id、目标行取 targets，ADR 0036「5.」、0049 决策 6）
    assert m.main(["doctor", "--json"]) == 0
    doc = json.loads(capsys.readouterr().out)
    _assert_documented(doc, section="doctor --json")
    # 项名是 `name` 的**值**，键名护栏照不出它：把按引擎后缀的项名归一成 `<engine>` 形态后逐个核对契约页里写了
    page = DOC.read_text(encoding="utf-8")
    for name in {c["name"] for c in doc["checks"]}:
        generic = re.sub(r"\.(novaact|midscene)$", ".<engine>", name)
        assert f"`{generic}`" in page, f"[doctor --json] 项名 {name}（{generic}）没写进 docs/internals/cli-json-contract.md"


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
    _assert_documented(doc, section="explain --json", opaque={"args", "result", "provider_minutes", "device"})
