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
    StepSkipped,
)
from core.wire import event_from_json, event_from_line, job_to_json


# ---- Job 序列化：形状符合 ADR 0024 输入示例 ----
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
    assert d["assertionVotes"] == 1  # 默认投票次数随 job 进协议（worker 据此跑 AI 断言，ADR 0014/0024）
    assert len(d["scenarios"]) == 1
    sc = d["scenarios"][0]
    assert sc["id"] == "t.feature:5"
    assert sc["steps"][0] == {"index": 0, "keyword": "Given", "text": '打开 "https://x"'}
    # 无 argument 的 step 不带 argument 键
    assert "argument" not in sc["steps"][1]


def test_job_to_json_assertion_votes_passthrough():
    # assertionVotes 原样透传进协议（组合根设的非默认值，worker 据此跑 N 次取多数票）
    job = Job(scope_id="s", scope_name="s", engine="midscene", scenarios=(), assertion_votes=5)
    assert job_to_json(job)["assertionVotes"] == 5


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


def test_event_step_done_with_report_refs():
    # step 级 trajectory 下沉（ADR 0027）：wire 读 step_done 的 reportRefs（kind=trajectory）
    ev = event_from_json({
        "type": "step_done", "scenarioId": "s:0", "stepIndex": 1, "status": "passed",
        "reportRefs": [
            {"kind": "trajectory", "ref": "file:///tmp/act_0.html", "label": "trajectory 1"},
            {"kind": "trajectory", "ref": "file:///tmp/act_1.html", "label": "trajectory 2"},
        ],
    })
    assert isinstance(ev, StepDone)
    assert len(ev.report_refs) == 2  # 一个 step 可多个 act
    assert ev.report_refs[0].kind == "trajectory"
    assert ev.report_refs[1].ref == "file:///tmp/act_1.html"


def test_event_step_done_no_report_refs_defaults_empty():
    # 无 reportRefs 的 step_done（确定性/导航步）→ 空 tuple（向后兼容）
    ev = event_from_json({"type": "step_done", "scenarioId": "s:0", "stepIndex": 0, "status": "passed"})
    assert ev.report_refs == ()


def test_event_step_skipped():
    # scope 内短路（ADR 0031 决定六）：step_skipped 独立事件、无 status/votes/cost——
    # 加法解析，不碰 step_done 三态。core 据此本地赋 StepResult(SKIPPED, shortcircuited=True)。
    ev = event_from_json({"type": "step_skipped", "scenarioId": "s:0", "stepIndex": 2})
    assert isinstance(ev, StepSkipped)
    assert ev.scenario_id == "s:0"
    assert ev.step_index == 2
    # 没有 status 字段（不是 step_done 的第 4 态；不参与判定/severity）
    assert not hasattr(ev, "status")


def test_event_step_done_parse_unaffected_by_step_skipped():
    # 回归护栏：step_skipped 分支是加法——step_done 的三态解析（Status(d["status"])）不受影响。
    ev = event_from_json({"type": "step_done", "scenarioId": "s:0", "stepIndex": 0, "status": "error",
                          "errorType": "network_error"})
    assert isinstance(ev, StepDone)
    assert ev.status == Status.ERROR


def test_event_scope_done():
    # scope 级 report_ref：Midscene report / Nova session summary（kind=summary，scope 级新语义）
    ev = event_from_json({
        "type": "scope_done", "scopeId": "login", "sessionId": "sess-123",
        "reportRefs": [{"kind": "summary", "ref": "file:///tmp/session_summary.json", "label": "Nova session summary"}],
    })
    assert isinstance(ev, ScopeDone)
    assert ev.scope_id == "login"
    assert ev.session_id == "sess-123"
    assert ev.report_refs[0].kind == "summary"
    assert ev.report_refs[0].ref == "file:///tmp/session_summary.json"
    assert ev.report_refs[0].label == "Nova session summary"


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


# ---- 退出码约定（out-of-band 协议通道，ADR 0024「退出码约定」/ 0028）----
# 常量与翻译在 wire 一处、两个 Engine adapter 共用（曾各抄一份、靠「两处必须同值」的注释维持）：本组守那份单一事实源。
def test_ex_worker_network_value_is_protocol_pinned():
    """80 是跨语言约定值（两个引擎 worker 各自硬编码）——改这个数即改协议，须同步两 worker。"""
    from core.wire import EX_WORKER_NETWORK
    assert EX_WORKER_NETWORK == 80


def test_raise_for_worker_exit_maps_codes():
    """码→异常的分类（schedule 按类型分流：WorkerNetworkError→network_error 可重试 / RuntimeError→error）。

    0 与负码不抛：负码只来自 SIGKILL（schedule 主动停 worker 的尾路径），非 worker 自报的故障、不在此翻译。
    """
    import pytest

    from core.errors import WorkerNetworkError
    from core.wire import raise_for_worker_exit

    raise_for_worker_exit(0, code_label="returncode")   # 正常退出
    raise_for_worker_exit(-9, code_label="returncode")  # SIGKILL 强杀
    with pytest.raises(WorkerNetworkError):
        raise_for_worker_exit(80, code_label="returncode")


def test_raise_for_worker_exit_label_names_the_transport_field():
    """两个 adapter 共用同一翻译、只换 code_label：消息说各自传输的字段名（子进程 returncode / ECS exitCode）。"""
    import pytest

    from core.errors import WorkerNetworkError
    from core.wire import raise_for_worker_exit

    with pytest.raises(RuntimeError, match=r"returncode=1\b") as sub:
        raise_for_worker_exit(1, code_label="returncode")
    assert not isinstance(sub.value, WorkerNetworkError)  # 非 80 不进 network_error 分类
    with pytest.raises(RuntimeError, match=r"exitCode=137\b"):
        raise_for_worker_exit(137, code_label="exitCode")
