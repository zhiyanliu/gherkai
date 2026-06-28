"""wire 协议测试（ADR 0024）：Job 序列化 + 事件反序列化的形状契约。"""
from __future__ import annotations

import json

from core.model import (
    Job,
    Scenario,
    ScenarioDone,
    ScenarioStarted,
    ScopeDone,
    Status,
    Step,
    StepArgument,
    StepDone,
)
from core.wire import event_from_json, event_from_line, job_to_json


# ---- Job 序列化：形状符合 0024 输入示例 ----
def test_job_to_json_shape():
    job = Job(
        scope_id="login",
        scope_name="login",
        engine="novaact",
        scenarios=(
            Scenario(
                id="t.feature:5",
                name="搜索",
                steps=(
                    Step(0, "Given", '打开 "https://x"'),
                    Step(1, "When", "搜索 OpenAI"),
                    Step(2, "Then", "进入词条页"),
                ),
            ),
        ),
    )
    d = job_to_json(job)
    assert d["scope"] == {"id": "login", "name": "login"}
    assert d["engine"] == "novaact"
    assert len(d["scenarios"]) == 1
    sc = d["scenarios"][0]
    assert sc["id"] == "t.feature:5"
    assert sc["steps"][0] == {"index": 0, "keyword": "Given", "text": '打开 "https://x"'}
    # 无 argument 的 step 不带 argument 键
    assert "argument" not in sc["steps"][1]


def test_job_argument_serialization():
    job = Job(
        scope_id="s", scope_name="s", engine="novaact",
        scenarios=(
            Scenario(id="t:1", name="x", steps=(
                Step(0, "Given", "表", StepArgument(kind="dataTable", rows=(("h1", "h2"), ("a", "b")))),
                Step(1, "Given", "文档", StepArgument(kind="docString", content="行1\n行2")),
            )),
        ),
    )
    d = job_to_json(job)
    steps = d["scenarios"][0]["steps"]
    assert steps[0]["argument"] == {"kind": "dataTable", "rows": [["h1", "h2"], ["a", "b"]]}
    assert steps[1]["argument"] == {"kind": "docString", "content": "行1\n行2"}


# ---- 事件反序列化：四种事件按 type 分派 ----
def test_event_scenario_started():
    ev = event_from_json({"type": "scenario_started", "scenarioId": "s:0"})
    assert isinstance(ev, ScenarioStarted)
    assert ev.scenario_id == "s:0"


def test_event_step_done_with_votes_and_cost():
    # cost 是平铺 optional 原生量（ADR 0024）：Nova 报 time_worked_s
    ev = event_from_json({
        "type": "step_done",
        "scenarioId": "s:0",
        "stepIndex": 2,
        "status": "passed",
        "votes": {"yes": 3, "total": 3},
        "cost": {"time_worked_s": 9.3},
    })
    assert isinstance(ev, StepDone)
    assert ev.status == Status.PASSED
    assert ev.votes.yes == 3
    assert ev.cost.time_worked_s == 9.3
    assert ev.cost.tokens is None


def test_event_step_done_cost_tokens():
    # Midscene 报 tokens
    ev = event_from_json({
        "type": "step_done", "scenarioId": "s:0", "stepIndex": 1, "status": "passed",
        "cost": {"tokens": 1915},
    })
    assert ev.cost.tokens == 1915
    assert ev.cost.time_worked_s is None


def test_event_step_done_failed():
    ev = event_from_json({
        "type": "step_done", "scenarioId": "s:0", "stepIndex": 1,
        "status": "failed", "votes": {"yes": 1, "total": 3},
        "errorType": "assertion_failed", "message": "没过多数票",
    })
    assert ev.status == Status.FAILED
    assert ev.error_type == "assertion_failed"


def test_event_scope_done():
    ev = event_from_json({
        "type": "scope_done", "scopeId": "login", "sessionId": "sess-123",
        "reportRefs": [{"granularity": "act", "path": "/tmp/x.html"}],
    })
    assert isinstance(ev, ScopeDone)
    assert ev.scope_id == "login"
    assert ev.session_id == "sess-123"
    assert ev.report_refs[0].path == "/tmp/x.html"


# ---- 从行解析（worker stdout 一行）----
def test_event_from_line():
    line = json.dumps({"type": "scenario_done", "scenarioId": "s:0", "status": "passed"})
    ev = event_from_line(line)
    assert isinstance(ev, ScenarioDone)
    assert ev.status == Status.PASSED


# ---- 未知 type 报错（不静默吞）----
def test_unknown_event_type_raises():
    import pytest
    with pytest.raises(ValueError, match="未知事件 type"):
        event_from_json({"type": "bogus"})
