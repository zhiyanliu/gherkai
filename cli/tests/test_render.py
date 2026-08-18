"""render（表层渲染）单测：用 fake RunResult/Event，纯字符串/dict 断言，不烧钱。"""
from __future__ import annotations

from core.model import (
    Cost,
    Job,
    JobResult,
    ReportRef,
    ResourceUri,
    RunMeta,
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
    job = Job(scope_id="features/demo.feature:6", scope_name="demo", engine="midscene", scenarios=())
    return RunResult(
        run_meta=RunMeta(run_id="20260629-test01", created_at="", jobs=(job,)),
        status=Status.PASSED,
        duration_ms=12000.0,
        total_tokens=10573,
        total_time_worked_s=None,
        jobs=[
            JobResult(
                job=job,
                status=Status.PASSED,
                total_tokens=10573,
                duration_ms=11000.0,
                session_id="sess-abc",
                report_refs=(ReportRef(kind="report", ref=ResourceUri("file:///x/report.html"), label="Midscene report"),),
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
    assert "step 1: passed (7.0s) 投票 3/3" in txt  # 多票 step 显 tally（与 format_event/index.html 一致）
    assert "step 0: passed (3.0s)" in txt and "投票" not in txt.split("step 0")[1].split("step 1")[0]  # step0 无 votes 不显
    assert "session id: sess-abc" in txt
    assert "report（Midscene report）: file:///x/report.html" in txt  # label 作锚文本、缺则回落 kind


def test_render_text_shows_step_level_report_refs():
    # 回归：Nova trajectory 挂 step 级 report_refs（下沉，ADR 0027）——文本汇总必须打 step 级，
    # 否则 Nova 报告静默漏掉（曾漏打过；一个 step 可多个 trajectory）。
    from core.model import StepResult
    job = Job(scope_id="s", scope_name="s", engine="novaact", scenarios=())
    run = RunResult(
        run_meta=RunMeta(run_id="r", created_at="", jobs=(job,)),
        status=Status.PASSED,
        jobs=[JobResult(job=job, status=Status.PASSED, scenarios=[
            ScenarioResult(scenario_id="s:0", status=Status.PASSED, steps=[
                StepResult(index=0, status=Status.PASSED, report_refs=(
                    ReportRef(kind="trajectory", ref=ResourceUri("file:///t/act_0.html"), label=None),
                    ReportRef(kind="trajectory", ref=ResourceUri("file:///t/act_1.html"), label="trajectory 2"),
                )),
            ]),
        ])],
    )
    txt = render.render_text(run)
    # step 级 ref 都被渲染：label 缺 → 回落 kind "trajectory"；有 label → 用 label
    assert "report（trajectory）: file:///t/act_0.html" in txt
    assert "report（trajectory 2）: file:///t/act_1.html" in txt


def test_render_text_annotates_shortcircuited_step():
    # 连锁失败旁注（ADR 0031 决定六）：被 scope 内短路的 step（shortcircuited=True，status=skipped）加旁注
    # "因前置 step error 被跳过"；上游 error 步本身不加。判据读 shortcircuited 布尔（不再按 status 顺序猜）。
    from core.model import StepResult
    job = Job(scope_id="s", scope_name="s", engine="novaact", scenarios=())
    run = RunResult(
        run_meta=RunMeta(run_id="r", created_at="", jobs=(job,)),
        status=Status.ERROR,
        jobs=[JobResult(job=job, status=Status.ERROR, scenarios=[
            ScenarioResult(scenario_id="s:0", status=Status.ERROR, steps=[
                StepResult(index=0, status=Status.ERROR, error_type="network_error"),   # 上游 error
                StepResult(index=1, status=Status.SKIPPED, shortcircuited=True),          # 被短路 → 加旁注
            ]),
        ])],
    )
    txt = render.render_text(run)
    lines = txt.splitlines()
    step1 = next(l for l in lines if "step 1:" in l)
    step0 = next(l for l in lines if "step 0:" in l)
    assert "被跳过" in step1          # 被短路的 step 加旁注
    assert "skipped" in step1         # 显 skipped 态
    assert "被跳过" not in step0      # 上游 error 步本身不加


def test_render_text_no_annotation_on_plain_failed():
    # 反向护栏（ADR 0031 决定六）：普通 failed（shortcircuited=False，含"error 后的 failed"）不加旁注——
    # 判据迁到 shortcircuited 后，只有真被短路的 step 才加旁注，避免误伤正常业务失败。
    from core.model import StepResult
    job = Job(scope_id="s", scope_name="s", engine="novaact", scenarios=())
    run = RunResult(
        run_meta=RunMeta(run_id="r", created_at="", jobs=(job,)),
        status=Status.ERROR,
        jobs=[JobResult(job=job, status=Status.ERROR, scenarios=[
            ScenarioResult(scenario_id="s:0", status=Status.ERROR, steps=[
                StepResult(index=0, status=Status.ERROR, error_type="network_error"),
                StepResult(index=1, status=Status.FAILED, error_type="assertion_failed"),  # 普通 failed，非短路
            ]),
        ])],
    )
    txt = render.render_text(run)
    assert "被跳过" not in txt         # 无 shortcircuited step → 全程无旁注


def test_to_dict_shape_and_no_dollar():
    d = render.to_dict(_sample_run())
    assert d["status"] == "passed"
    assert d["total_tokens"] == 10573
    assert d["total_time_worked_s"] is None
    # 不折美元：dict 里只有原生量，无 cost_usd 等字段
    assert "cost_usd" not in d
    assert d["run_id"] == "20260629-test01"
    job = d["jobs"][0]
    # 聚合形态 normalize：jobs[] 只留 scope_id 作 join key；engine/scope_name 在 run_meta.jobs[]（不冗余）
    assert job["scope_id"] == "features/demo.feature:6"
    assert "engine" not in job and "scope_name" not in job
    assert d["run_meta"]["jobs"][0]["engine"] == "midscene"   # def 真值在 run_meta
    assert job["report_refs"] == [
        {"kind": "report", "ref": "file:///x/report.html", "label": "Midscene report"}
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


def test_format_event_single_vote_hides_tally():
    # assertion_votes=1 → Votes(1,1)：单次判定无抖动 tally 意义，渲染不显 "1/1"（避免噪声）
    ev = StepDone(scenario_id="x", step_index=0, status=Status.PASSED, votes=Votes(yes=1, total=1))
    s = render.format_event(ev)
    assert "votes=" not in s  # total==1 隐藏
    # 但多票仍显
    ev3 = StepDone(scenario_id="x", step_index=0, status=Status.PASSED, votes=Votes(yes=3, total=3))
    assert "votes=3/3" in render.format_event(ev3)


def test_format_event_omits_scope_id():
    # scope_id 不再进事件行——它归调用方的 `[core <scope>:event]` 前缀（见 __main__.py sink），
    # 行内只留前缀没有的字段，避免 `[core login:event] scope_done scope_id=login` 这种重复。
    s = render.format_event(ScopeDone(scope_id="login", session_id="s1"))
    assert "scope_done" in s
    assert "scope_id=" not in s  # scope 归前缀，行内不再重复


# ---- render_run_state：status 的 RunState 人读渲染（皮的事，从 gherkai 归位到此，ADR 0016「归属清算」条）----

def test_render_run_state_lists_jobs_and_session_lineage():
    from core.model import JobState, RunState

    state = RunState(run_id="r1", status=Status.RUNNING, high_water_mark=3, jobs={
        "a": JobState("a", Status.PASSED, session_id="sess-1"),
        "b": JobState("b", Status.RUNNING),
    })
    s = render.render_run_state(state)
    assert s.splitlines()[0] == "run r1: running"
    assert "  - a: passed  session=sess-1" in s   # 有会话血缘则显
    assert "  - b: running" in s and "session=None" not in s  # 无则不显、不打裸 None
    assert "ended_at" not in s  # 未达终态、无 ended_at 时不打该行


def test_render_run_state_shows_ended_at_when_terminal():
    from core.model import JobState, RunState

    state = RunState(run_id="r1", status=Status.PASSED, high_water_mark=9,
                     jobs={"a": JobState("a", Status.PASSED)}, ended_at="2026-01-01T00:00:00Z")
    assert "ended_at=2026-01-01T00:00:00Z" in render.render_run_state(state)
