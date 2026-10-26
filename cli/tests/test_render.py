"""render（表层渲染）单测：用 fake RunResult/Event，纯字符串/dict 断言，零费用。"""
from __future__ import annotations

from gherkai_core.model import (
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

from gherkai_cli import render


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
    from gherkai_core.model import StepResult
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
    from gherkai_core.model import StepResult
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
    assert render._SHORTCIRCUIT_NOTE in step1  # 与 explain 的 step 行同一句（措辞单点，别再各抄一份）
    assert "skipped" in step1         # 显 skipped 态
    assert "被跳过" not in step0      # 上游 error 步本身不加


def test_index_html_shortcircuit_note_matches_cli_wording():
    """跨包措辞护栏（ADR 0031 决定六）：报告入口页的短路旁注与本模块的旁注是同一句。

    core 不能 import cli（分层方向），那句在两包各有一份字面量；测试两边都能 import，故护栏放 cli 侧——
    改一处忘改另一处本条就红（此前两包各只被自己的字面量守住，措辞可静默分叉）。
    比对前 unescape：core 那份内嵌进 HTML，将来措辞若带 & / < 也照样对得上。
    """
    import html as html_mod

    from gherkai_core.adapters.report_store.local import render_index_html

    job = Job(scope_id="s", scope_name="s", engine="novaact", scenarios=())
    run = RunResult(
        run_meta=RunMeta(run_id="r", created_at="", jobs=(job,)),
        status=Status.ERROR,
        jobs=[JobResult(job=job, status=Status.ERROR, scenarios=[
            ScenarioResult(scenario_id="s:0", status=Status.ERROR, steps=[
                StepResult(index=0, status=Status.ERROR, error_type="network_error"),   # 上游 error（不加旁注）
                StepResult(index=1, status=Status.SKIPPED, shortcircuited=True),          # 被短路 → 加旁注
            ]),
        ])],
    )
    manifest = {"run_id": run.run_id, "created_at": "", "report_index": []}
    txt = html_mod.unescape(render_index_html(manifest, run))
    assert txt.count(render._SHORTCIRCUIT_NOTE) == 1   # 只挂被短路那一步，且与文本渲染逐字相同


def test_index_html_scope_skipped_note_matches_cli_wording():
    """跨包措辞护栏（ADR 0051 决策 4 / 0031 决定六）：scope 级 error 后合成的 skipped（shortcircuited=False）在报告入口页与文本树是同一句，
    且不与被短路的旁注混用。"""
    import html as html_mod

    from gherkai_core.adapters.report_store.local import render_index_html

    job = Job(scope_id="s", scope_name="s", engine="midscene", scenarios=())
    run = RunResult(
        run_meta=RunMeta(run_id="r", created_at="", jobs=(job,)),
        status=Status.ERROR,
        jobs=[JobResult(job=job, status=Status.ERROR, error_type="session_lost", message="设备没了", scenarios=[
            ScenarioResult(scenario_id="s:0", status=Status.SKIPPED, steps=[
                StepResult(index=0, status=Status.SKIPPED, shortcircuited=False),
                StepResult(index=1, status=Status.SKIPPED, shortcircuited=False)]),
        ])],
    )
    manifest = {"run_id": run.run_id, "created_at": "", "report_index": []}
    txt = html_mod.unescape(render_index_html(manifest, run))
    assert txt.count(render._SCOPE_SKIPPED_NOTE) == 2 and render._SHORTCIRCUIT_NOTE not in txt
    tree = render.render_text(run)
    assert tree.count(render._SCOPE_SKIPPED_NOTE) == 2 and render._SHORTCIRCUIT_NOTE not in tree


def test_run_tree_shows_device_metering_and_unconfirmed_sessions():
    """设备 job（ADR 0051 决策 7；0034 机制二 U 集）：设备占用时长与缺计量会话数、未确认停止的会话名、结果未知的创建尝试单独标；桌面 job 不出这些行。"""
    from gherkai_core.model import SessionRecord

    job = Job(scope_id="d", scope_name="d", engine="midscene", scenarios=())
    sessions = [SessionRecord(session_id="arn:a", name="n-a", origin="created", release="confirmed", observed_s=90.0),
                SessionRecord(session_id="arn:b", name="n-b", origin="created", release="unconfirmed", observed_s=None),
                SessionRecord(session_id=None, name="n-c", origin="attempted", release="unconfirmed")]
    jr = JobResult(job=job, status=Status.ERROR, error_type="release_failed", message="m", sessions=sessions,
                   device_observed_s=90.0, device_observed_missing=1)
    run = RunResult(run_meta=RunMeta(run_id="r", created_at="", jobs=(job,)), status=Status.ERROR, jobs=[jr],
                    device_observed_s=90.0, device_observed_missing=1)
    txt = render.render_text(run)
    assert "设备占用时长合计: 90.0s（另有 1 个会话缺计量）" in txt
    assert "设备占用时长: 90.0s（另有 1 个会话缺计量）" in txt
    assert "未确认停止的会话: n-b" in txt and "结果未知的创建尝试: n-c" in txt and "n-a" not in txt.split("未确认停止的会话: ")[1].split("\n")[0]
    desktop = render.render_text(_sample_run())
    assert "设备占用" not in desktop and "未确认停止" not in desktop


def test_explain_carries_sessions_and_metering_and_skips_evidence_note_for_synthesized_skipped():
    from gherkai_core.model import Scenario, SessionRecord, Step

    sc = Scenario(id="d:0", name="n", steps=(Step(0, "Given", "a"), Step(1, "Then", "b")))
    job = Job(scope_id="d", scope_name="d", engine="midscene", scenarios=(sc,))
    jr = JobResult(job=job, status=Status.ERROR, error_type="precheck_failed", message="设备不支持", session_id=None,
                   sessions=[SessionRecord(session_id=None, name="n-t", origin="attempted", release="unconfirmed")],
                   device_observed_s=0.0, device_observed_missing=0,
                   scenarios=[ScenarioResult(scenario_id="d:0", status=Status.SKIPPED, steps=[
                       StepResult(index=0, status=Status.SKIPPED, shortcircuited=False),
                       StepResult(index=1, status=Status.SKIPPED, shortcircuited=False)])])
    doc = render.explain_to_dict(run_id="r", status="error", results=[jr], evidence_reader=lambda refs: (None, "no_ref"))
    scope = doc["scopes"][0]
    assert scope["sessions"][0]["origin"] == "attempted" and scope["device_observed_s"] == 0.0 and scope["device_observed_missing"] == 0
    assert scope["has_step_records"] is True  # 合成记录也是记录：判定块不按「零记录」渲染
    txt = render.render_explain_text(doc, expand_passed=True)
    assert txt.count(render._SCOPE_SKIPPED_NOTE) == 2 and "无 AI 证据" not in txt
    assert "结果未知的创建尝试: n-t" in txt
    assert "判定：error  (precheck_failed: 设备不支持)" in txt and "诊断细节见 worker 日志" not in txt  # 全是合成记录也打判定行


def test_explain_prints_verdict_line_for_error_with_error_type_regardless_of_records():
    """ADR 0042 决策四：job 判 error / aborted 且带 error_type 时总打判定行，与有无 step 记录无关；「诊断细节见 worker 日志」只在零记录时打；
    passed / failed 有记录时不打判定行。"""
    from gherkai_core.model import Scenario, Step

    sc = Scenario(id="d:0", name="n", steps=(Step(0, "Given", "a"),))
    job = Job(scope_id="d", scope_name="d", engine="midscene", scenarios=(sc,))
    recorded = [ScenarioResult(scenario_id="d:0", status=Status.PASSED, steps=[StepResult(index=0, status=Status.PASSED)])]

    def text(jr):
        return render.render_explain_text(render.explain_to_dict(run_id="r", status=jr.status.value, results=[jr],
                                                                 evidence_reader=lambda refs: (None, "no_ref")), expand_passed=True)

    with_records = text(JobResult(job=job, status=Status.ERROR, error_type="release_failed", message="m", scenarios=recorded))
    assert "判定：error  (release_failed: m)" in with_records and "诊断细节见 worker 日志" not in with_records
    zero = text(JobResult(job=job, status=Status.ERROR, error_type="timeout", message="job 超时"))
    assert "判定：error  (timeout: job 超时)" in zero and "诊断细节见 worker 日志" in zero
    assert "判定：" not in text(JobResult(job=job, status=Status.PASSED, scenarios=recorded))
    desktop = render.explain_to_dict(run_id="r", status="passed", results=[_sample_run().jobs[0]], evidence_reader=lambda refs: (None, "no_ref"))
    assert "sessions" not in desktop["scopes"][0]  # 桌面 job 省键


def test_format_event_renders_session_events_without_endpoints():
    from gherkai_core.model import SessionClosed, SessionOpened

    opened = render.format_event(SessionOpened(scope_id="s", name="gherkai:r:ab:1:s", origin="created", session_id="arn:x",
                                                device={"platform": "android", "model": "m"}))
    assert opened == "session_opened origin=created name=gherkai:r:ab:1:s"
    closed = render.format_event(SessionClosed(scope_id="s", name="n", release="unconfirmed", observed_s=12.5))
    assert closed == "session_closed release=unconfirmed name=n observed_s=12.5"
    from gherkai_core.model import ScopeDone
    assert render.format_event(ScopeDone(scope_id="s", status=Status.ERROR, error_type="acquire_timeout", message="m")) == \
        "scope_done status=error error_type=acquire_timeout"


def test_render_text_no_annotation_on_plain_failed():
    # 反向护栏（ADR 0031 决定六）：普通 failed（shortcircuited=False，含"error 后的 failed"）不加旁注——
    # 判据迁到 shortcircuited 后，只有真被短路的 step 才加旁注，避免误伤正常业务失败。
    from gherkai_core.model import StepResult
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


# ---- render_run_state：status 的 RunState 人读渲染（前端的事，从 gherkai 归位到此，ADR 0016「归属清算」条）----

def test_render_run_state_lists_jobs_and_session_lineage():
    from gherkai_core.model import JobState, RunState

    state = RunState(run_id="r1", status=Status.RUNNING, high_water_mark=3, jobs={
        "a": JobState("a", Status.PASSED, session_id="sess-1"),
        "b": JobState("b", Status.RUNNING),
    })
    s = render.render_run_state(state)
    assert s.splitlines()[0] == "run r1: running"
    assert "sess-1" in s and "passed" in s          # 有会话血缘则显（表格渲染，只断言内容，ADR 0047）
    assert "running" in s and "None" not in s        # 无则显 -，不打裸 None
    assert "ended_at" not in s  # 未达终态、无 ended_at 时不打该行


def test_render_run_state_shows_ended_at_when_terminal():
    from gherkai_core.model import JobState, RunState

    state = RunState(run_id="r1", status=Status.PASSED, high_water_mark=9,
                     jobs={"a": JobState("a", Status.PASSED)}, ended_at="2026-01-01T00:00:00Z")
    assert "ended_at=2026-01-01T00:00:00Z" in render.render_run_state(state)


def test_render_text_shows_reason_for_fail_fast_states():
    """skipped/aborted 的 error_type 恒 None（ADR 0031 决定一）——「为什么没执行」只在 message，人读文本必须显；
    且 error_type 为 None 时不打裸 "None:" 前缀。"""
    jobs = [Job(scope_id=s, scope_name=s, engine="novaact", scenarios=[]) for s in ("checkout", "login")]
    a = JobResult(job=jobs[0], status=Status.SKIPPED)
    a.message = "fail-fast：本次运行已中止，未启动（worker 未 spawn）"
    b = JobResult(job=jobs[1], status=Status.ABORTED)
    b.message = "fail-fast：其他 job 失败，本 job 被中止"
    meta = RunMeta(run_id="r1", created_at="2026-01-01T00:00:00Z", jobs=tuple(jobs))
    out = render.render_text(RunResult(run_meta=meta, status=Status.ERROR, jobs=[a, b]))
    assert "未启动" in out and "本 job 被中止" in out
    assert "None:" not in out


def test_render_text_step_reason_line_is_single_line_and_only_when_present():
    """step 级原因行（ADR 0042 决策三）：failed/error step 下附「原因: …」，多行/多余空白折叠成一行；passed 步不显。"""
    job = Job(scope_id="s", scope_name="s", engine="novaact", scenarios=())
    jr = JobResult(job=job, status=Status.ERROR, scenarios=[ScenarioResult(scenario_id="s:1", status=Status.ERROR, steps=[
        StepResult(index=0, status=Status.PASSED, duration_ms=10.0),
        StepResult(index=1, status=Status.ERROR, error_type="timeout", duration_ms=20.0,
                   message="ActTimeoutError: 超时\n  at foo\n\n  at bar"),
    ])])
    out = render.render_text(RunResult(run_meta=RunMeta(run_id="r", created_at="", jobs=(job,)), status=Status.ERROR, jobs=[jr]))
    lines = out.splitlines()
    reason = [ln for ln in lines if "原因: " in ln]          # 树形渲染：只断言内容（ADR 0047）
    assert len(reason) == 1 and reason[0].endswith("原因: ActTimeoutError: 超时 at foo at bar")
    i0 = next(i for i, ln in enumerate(lines) if "step 0: passed (0.0s)" in ln)
    assert "原因" not in lines[i0 + 1]


def test_job_line_with_error_type_but_no_message_has_no_orphan_colon():
    """job 行有分类、message 为 None → 只显分类 `(worker_crashed)`，不打 `(worker_crashed: None)`——与报告页 index.html 判法一致。"""
    job = Job(scope_id="s", scope_name="s", engine="novaact", scenarios=[])
    jr = JobResult(job=job, status=Status.ERROR)
    jr.error_type = "worker_crashed"
    meta = RunMeta(run_id="r", created_at="2026-01-01T00:00:00Z", jobs=(job,))
    out = render.render_text(RunResult(run_meta=meta, status=Status.ERROR, jobs=[jr]))
    assert "(worker_crashed)" in out and "None" not in out



def test_run_tree_attaches_reason_and_refs_under_their_step():
    """层级归属（ADR 0047）：原因与产物地址挂在所属 step 下，不挂到 scenario 或 job。"""
    from gherkai_core.model import ReportRef
    job = Job(scope_id="s", scope_name="s", engine="novaact", scenarios=())
    st1 = StepResult(index=1, status=Status.FAILED, duration_ms=5.0, message="断言未过",
                     report_refs=[ReportRef(kind="evidence", ref="file:///e.json")])
    jr = JobResult(job=job, status=Status.FAILED, scenarios=[ScenarioResult(scenario_id="s:1", status=Status.FAILED, steps=[
        StepResult(index=0, status=Status.PASSED, duration_ms=1.0), st1])])
    root = render.run_tree(RunResult(run_meta=RunMeta(run_id="r", created_at="", jobs=(job,)), status=Status.FAILED, jobs=[jr]))
    step1 = root.find("step 1: ")
    assert step1 is not None
    labels = [str(c.label) for c in step1.children]
    assert any(l.startswith("原因: 断言未过") for l in labels) and any("file:///e.json" in l for l in labels)
    scenario = root.find("scenario 's:1'")
    assert not any("原因" in str(c.label) for c in scenario.children)   # 原因不挂在 scenario 层
