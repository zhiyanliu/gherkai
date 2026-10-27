"""wire 协议测试（ADR 0024）：Job 序列化 + 事件反序列化的形状契约。"""
from __future__ import annotations

import json

from gherkai_core.model import (
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
from gherkai_core.wire import event_from_json, event_from_line, job_to_json


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
                    Step(0, "Given", '"https://x"'),
                    Step(1, "When", "搜索 OpenAI"),
                    Step(2, "Then", "进入词条页"),
                ),
            ),
        ),
    )
    d = job_to_json(job)
    assert d["scope"] == {"id": "login", "name": "login"}
    assert d["engine"] == "novaact"
    assert d["assertionVotes"] == 1  # 默认投票次数随 job 进协议（worker 据此执行 AI 断言，ADR 0014/0024）
    assert len(d["scenarios"]) == 1
    sc = d["scenarios"][0]
    assert sc["id"] == "t.feature:5"
    assert sc["steps"][0] == {"index": 0, "keyword": "Given", "text": '"https://x"'}
    # 无 argument 的 step 不带 argument 键
    assert "argument" not in sc["steps"][1]


def test_job_to_json_key_set_is_fixed_and_carries_schema_version():
    """协议（ADR 0024「job 行的结构版本与固定键集」、0048 决策 3）：键集与 job 形态无关、恒为八键；无值写 null；schemaVersion 恒为 1。"""
    from gherkai_core.wire import PROTOCOL_SCHEMA_VERSION

    fixed = {"schemaVersion", "scope", "engine", "scenarios", "assertionVotes", "timeoutS", "target", "deviceRequest"}
    d = job_to_json(Job(scope_id="s", scope_name="s", engine="novaact", scenarios=()))
    assert set(d) == fixed and d["schemaVersion"] == PROTOCOL_SCHEMA_VERSION == 1
    assert d["timeoutS"] is None and d["target"] == {"device": "desktop", "uiKind": "web"} and d["deviceRequest"] is None
    assert job_to_json(Job(scope_id="s", scope_name="s", engine="novaact", scenarios=(), timeout_s=300.0))["timeoutS"] == 300.0


def _device_jobs() -> dict[str, Job]:
    """三种形态（engines/fixtures/job-lines.json 的同一组输入）：桌面无预算、Android 网页（按版本族选设备）、iOS 应用（指定设备 ARN）。"""
    from gherkai_core.model import AppRef, DeviceFarmRequest, Target

    steps = (Step(0, "Given", "https://x/"), Step(1, "Then", "看到标题"))
    scs = (Scenario(id="f.feature:3", name="s", steps=steps),)
    return {
        "desktop": Job(scope_id="web", scope_name="web", engine="novaact", scenarios=scs, assertion_votes=1),
        "android_web": Job(scope_id="aw", scope_name="aw", engine="midscene", scenarios=scs, assertion_votes=3, timeout_s=1500.0,
                           target=Target(device="android", ui_kind="web"),
                           device_request=DeviceFarmRequest(project_arn="arn:aws:devicefarm:us-west-2:123456789012:project:p",
                                                            os_version="15", billing_method="METERED", acquire_timeout_s=600.0)),
        "ios_app": Job(scope_id="ia", scope_name="ia", engine="midscene", scenarios=scs, assertion_votes=1, timeout_s=900.0,
                       target=Target(device="ios", ui_kind="app",
                                     app=AppRef(alias="shop", app_id="com.example.Shop", bucket="b", key="apps/sha/shop.ipa", sha256="ab" * 32)),
                       device_request=DeviceFarmRequest(project_arn="arn:aws:devicefarm:us-west-2:123456789012:project:p",
                                                        device_arn="arn:aws:devicefarm:us-west-2::device:D1", billing_method="UNMETERED",
                                                        acquire_timeout_s=900.0)),
    }


def test_job_to_json_device_shapes_and_key_sets():
    """设备 job 的可选键形态（ADR 0048 决策 3 / 0024）：target.device / uiKind / app.{alias,bucket,key,sha256,appId}，
    deviceRequest.{provider, deviceArn 或 osVersion 二选一, billingMethod, projectArn, acquireTimeoutS}；按键集合差集断言。"""
    jobs = _device_jobs()
    aw = job_to_json(jobs["android_web"])
    assert set(aw) == {"schemaVersion", "scope", "engine", "scenarios", "assertionVotes", "timeoutS", "target", "deviceRequest"}
    assert aw["target"] == {"device": "android", "uiKind": "web"}
    assert set(aw["deviceRequest"]) == {"provider", "osVersion", "billingMethod", "projectArn", "acquireTimeoutS"}
    ia = job_to_json(jobs["ios_app"])
    assert set(ia["target"]) == {"device", "uiKind", "app"} and set(ia["target"]["app"]) == {"alias", "bucket", "key", "sha256", "appId"}
    assert set(ia["deviceRequest"]) == {"provider", "deviceArn", "billingMethod", "projectArn", "acquireTimeoutS"}
    assert ia["deviceRequest"]["provider"] == "aws-device-farm" and ia["target"]["app"]["appId"] == "com.example.Shop"


def test_job_lines_golden_matches_fixture_shared_with_midscene():
    """Python 到 TS 的往返（ADR 0048 决策 3）：三份 golden 行只有一份（engines/fixtures/job-lines.json），本测试核 Python 侧产出逐字相等，
    Midscene 侧 job-source.test.mts 核 TS 的 Job 类型字段清单与同一文件的键集合一致——任一侧加字段而另一侧没跟，测试就会变红。"""
    import json
    from pathlib import Path

    fixture = json.loads((Path(__file__).resolve().parents[2] / "engines" / "fixtures" / "job-lines.json").read_text(encoding="utf-8"))
    produced = {name: job_to_json(job) for name, job in _device_jobs().items()}
    assert fixture["jobs"] == produced, "golden 与 job_to_json 产出不一致：改了协议形状就同步改 fixture（并让 TS 侧测试跟上）"


def test_job_to_json_assertion_votes_passthrough():
    # assertionVotes 原样透传进协议（组合根设的非默认值，worker 据此执行 N 次取多数票）
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


def test_step_done_message_masks_tunnel_credentials():
    """解码时盖住 step_done.message 里的隧道凭据（ADR 0035 决策 5）：第三方 worker 没脱敏也进不了判定记录。"""
    line = json.dumps({"type": "step_done", "scenarioId": "s:0", "stepIndex": 0, "status": "failed",
                       "errorType": "assertion_failed",
                       "message": "页面停在 https://u1:p1@h.example/home 未跳转"}, ensure_ascii=False)
    ev = event_from_line(line)
    assert isinstance(ev, StepDone)
    assert ev.message == "页面停在 https://***@h.example/home 未跳转"


def test_step_done_without_message_stays_none():
    ev = event_from_json({"type": "step_done", "scenarioId": "s:0", "stepIndex": 0, "status": "passed"})
    assert isinstance(ev, StepDone) and ev.message is None


# ---- 未知 type 报错（不静默吞）----
def test_unknown_event_type_raises():
    import pytest
    with pytest.raises(ValueError, match="未知事件 type"):
        event_from_json({"type": "bogus"})


# ---- 退出码约定（out-of-band 协议通道，ADR 0024「退出码约定」/ 0028）----
# 常量与翻译在 wire 一处、两个 Engine adapter 共用（曾各抄一份、靠「两处必须同值」的注释维持）：本组守那份单一事实源。
def test_ex_worker_network_value_is_protocol_pinned():
    """80 是跨语言约定值（两个引擎 worker 各自硬编码）——改这个数即改协议，须同步两 worker。"""
    from gherkai_core.wire import EX_WORKER_NETWORK
    assert EX_WORKER_NETWORK == 80


def test_raise_for_worker_exit_maps_codes():
    """码→异常的分类（ADR 0034 机制二「退出信息」）：0 不抛；80 → WorkerNetworkError（可重试的 network_error）；其余非零含负码
    → WorkerExitError 带原码。负码（SIGKILL 为 -9）曾按干净退出处理——进程非干净终止本身即终态信号，不再放行。"""
    import pytest

    from gherkai_core.errors import WorkerExitError, WorkerNetworkError
    from gherkai_core.wire import raise_for_worker_exit

    raise_for_worker_exit(0, code_label="returncode")   # 正常退出
    with pytest.raises(WorkerExitError) as killed:
        raise_for_worker_exit(-9, code_label="returncode")  # SIGKILL 强杀：非零 → 终态信号
    assert killed.value.exit_code == -9 and not isinstance(killed.value, WorkerNetworkError)
    with pytest.raises(WorkerNetworkError) as net:
        raise_for_worker_exit(80, code_label="returncode")
    assert isinstance(net.value, WorkerExitError) and net.value.exit_code == 80  # 网络故障是退出码异常的子类
    with pytest.raises(WorkerExitError) as one:
        raise_for_worker_exit(1, code_label="exitCode")
    assert one.value.exit_code == 1


def test_raise_for_worker_exit_label_names_the_transport_field():
    """两个 adapter 共用同一翻译、只换 code_label：消息说各自传输的字段名（子进程 returncode / ECS exitCode）。"""
    import pytest

    from gherkai_core.errors import WorkerNetworkError
    from gherkai_core.wire import raise_for_worker_exit

    with pytest.raises(RuntimeError, match=r"returncode=1\b") as sub:
        raise_for_worker_exit(1, code_label="returncode")
    assert not isinstance(sub.value, WorkerNetworkError)  # 非 80 不进 network_error 分类
    with pytest.raises(RuntimeError, match=r"exitCode=137\b"):
        raise_for_worker_exit(137, code_label="exitCode")
