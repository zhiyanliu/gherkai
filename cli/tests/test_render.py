"""render（表层渲染）单测：用 fake RunResult/Event，纯字符串/dict 断言，不烧钱。"""
from __future__ import annotations

from core.model import (
    Cost,
    JobResult,
    ReportRef,
    RunResult,
    ScenarioResult,
    ScopeDone,
    Status,
    StepDone,
    StepResult,
    Votes,
)

from cli import render


def _sample_run() -> RunResult:
    return RunResult(
        run_id="20260629-test01",
        status=Status.PASSED,
        duration_ms=12000.0,
        total_tokens=10573,
        total_time_worked_s=None,
        jobs=[
            JobResult(
                scope_id="features/demo.feature:6",
                status=Status.PASSED,
                engine="midscene",
                total_tokens=10573,
                duration_ms=11000.0,
                session_id="sess-abc",
                report_refs=(ReportRef(kind="scope", ref="file:///x/report.html", label="Midscene report"),),
                scenarios=[
                    ScenarioResult(
                        scenario_id="features/demo.feature:6",
                        status=Status.PASSED,
                        duration_ms=10000.0,
                        steps=[
                            StepResult(index=0, status=Status.PASSED, duration_ms=3000.0),
                            StepResult(
                                index=1,
                                status=Status.PASSED,
                                duration_ms=7000.0,
                                votes=Votes(yes=3, total=3),
                            ),
                        ],
                    )
                ],
            )
        ],
    )


def test_render_text_nests_and_shows_cost_and_duration():
    txt = render.render_text(_sample_run())
    assert "总状态: passed" in txt
    assert "10573 tokens" in txt
    assert "总墙钟时长: 12.0s" in txt
    assert "scope 墙钟: 11.0s" in txt
    assert "step[1]: passed (7.0s)" in txt
    assert "sessionId: sess-abc" in txt
    assert "report[scope]: file:///x/report.html" in txt


def test_to_dict_shape_and_no_dollar():
    d = render.to_dict(_sample_run())
    assert d["status"] == "passed"
    assert d["total_tokens"] == 10573
    assert d["total_time_worked_s"] is None
    # 不折美元：dict 里只有原生量，无 cost_usd 等字段
    assert "cost_usd" not in d
    assert d["run_id"] == "20260629-test01"
    job = d["jobs"][0]
    assert job["scope_id"] == "features/demo.feature:6"
    assert job["engine"] == "midscene"
    assert job["report_refs"] == [
        {"kind": "scope", "ref": "file:///x/report.html", "label": "Midscene report"}
    ]
    step1 = job["scenarios"][0]["steps"][1]
    assert step1["votes"] == {"yes": 3, "total": 3}
    assert step1["duration_ms"] == 7000.0


def test_format_event_step_done_with_votes_and_cost():
    ev = StepDone(
        scenario_id="features/demo.feature:6",
        step_index=1,
        status=Status.PASSED,
        votes=Votes(yes=2, total=3),
        cost=Cost(tokens=1234),
    )
    s = render.format_event(ev)
    assert "step_done" in s
    assert "scenario_id=features/demo.feature:6" in s
    assert "step_index=1" in s
    assert "status=passed" in s
    assert "votes=2/3" in s
    assert "tokens=1234" in s


def test_format_event_scope_done():
    s = render.format_event(ScopeDone(scope_id="login", session_id="s1"))
    assert "scope_done" in s
    assert "scope_id=login" in s
