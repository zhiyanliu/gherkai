"""cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不产生 AWS 费用），

验证落盘三层产物 + --json 输出形状（单一可解析 JSON 文档，回归护栏 ADR 0016/0027）。
"""
from __future__ import annotations

import json

import pytest
import re
from pathlib import Path

from gherkai_core.model import JobResult, JobState, Status
from gherkai_core.run_status import RUN_ENDINGS, CommitOutcome
from gherkai_core.schedule import Execution
from gherkai_core.serialize import DEFINITION_SCHEMA_VERSION

from gherkai_cli import __main__ as m
from gherkai_cli import submission
from gherkai_runtime import compose, detached, textui

from _inline_children import inline_children  # noqa: F401 —— 夹具：本机 submit 启动的后台推进进程在线程里执行
from _fake_worker import FAKE_MIN_GRACE_S, FAKE_MODEL_ID  # 假 worker 自报的下限 / 模型 id（autouse 夹具注的那份）

# 收集期取到的真实现：conftest 的 autouse 替身在用例运行时才装上，要让真契约校验参与的用例把它装回去
_REAL_QUERY_CAPABILITIES = compose.query_capabilities


def _execution(run_meta, results, stopped_by=None) -> Execution:
    """假 schedule 交回的执行事实：判出结果的 job、余下的 job 不再启动的来源（没有为 None）；墙钟时长取 0。"""
    return Execution(run_meta=run_meta, results=tuple(results), stopped_by=stopped_by, duration_ms=0.0)


def _fake_schedule_factory():
    """造一个不起 worker 的假 schedule：发事件给 sink（进度）+ on_event（persistence 刷 RUNNING）+ 每 job
    fire on_job_complete（验证实时落库路径）+ 交回执行事实。"""
    from gherkai_core.model import ScopeStarted

    def fake_schedule(run_meta, engines, sink, opts=None, on_job_complete=None, on_event=None):
        results = []
        for j in run_meta.jobs:
            ev = ScopeStarted(scope_id=j.scope_id)
            sink(ev)                       # 进度 [event] 路由
            if on_event is not None:
                on_event(ev)               # 旁路观察者：persistence 刷 RUNNING（sink_lock 外，ADR 0030）
            jr = JobResult(job=j, status=Status.PASSED)
            results.append(jr)
            if on_job_complete is not None:
                on_job_complete(jr)        # job 完成即回调：persistence 实时落 ResultStore + RunStore
        return _execution(run_meta, results)
    return fake_schedule


def _write_feature(tmp_path: Path) -> Path:
    feat = tmp_path / "demo.feature"
    feat.write_text(
        "Feature: demo\n  Scenario: s\n    When \"做点啥\"\n", encoding="utf-8"
    )
    return feat


@pytest.fixture
def advanced(monkeypatch) -> list:
    """本机 submit 的用例配合 `inline_children` 使用：后台推进进程照常建 run、回报，推进本身换成记录调用的函数（不起 worker），
    依次记下它收到的运行定义。run 因此停在 pending、带后台执行标记，与刚提交还没有推进的 run 相同。"""
    calls: list = []
    monkeypatch.setattr(detached, "advance_local_run", lambda advancer, meta, **kw: calls.append(meta))
    return calls


def _submitted_run_dir(reports: Path) -> Path:
    """本机 submit 之后报告目录里唯一的 run 目录。"""
    [run_dir] = [d for d in reports.iterdir() if d.is_dir()]
    return run_dir


def test_json_output_is_single_parseable_document(tmp_path, monkeypatch, capsys):
    # --json + 默认归集：stdout 必须是**单个** JSON 文档（不得吐两个对象，回归护栏）。
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    feat = _write_feature(tmp_path)
    report_dir = tmp_path / "reports"

    rc = m.main(["run", str(feat), "--json", "--report-dir", str(report_dir)])
    assert rc == 0

    captured = capsys.readouterr()
    out, err = captured.out, captured.err
    doc = json.loads(out)  # 整段必须是单一合法 JSON（两个对象拼接、或进度污染都会在此抛错）
    assert doc["status"] == "passed"
    # 产物落点折进同一文档的 artifacts（不再二次 print）
    assert "artifacts" in doc
    assert doc["artifacts"]["run_meta"].endswith("run_meta.json")
    assert "run.json" not in out  # 不再引用三层重构后不存在的 run.json
    # stdout/stderr 切分（业界惯例）：进度/落点提示全在 stderr，stdout 只放纯 JSON 数据
    assert "plan:" not in out and "plan:" in err      # plan 进度 → stderr
    assert "run_id=" not in out and "run_id=" in err  # run_id 提示 → stderr
    assert "报告:" not in out and "报告:" in err  # 落点提示 → stderr


def test_text_mode_summary_on_stdout_progress_on_stderr(tmp_path, monkeypatch, capsys):
    # 非 --json（人看模式）：核心产出是文本汇总 → stdout；进度/落点 → stderr。
    # 这样 `gherkai run … > summary.txt` 拿到纯净汇总，进度照样在终端可见。
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    feat = _write_feature(tmp_path)
    rc = m.main(["run", str(feat), "--report-dir", str(tmp_path / "reports")])
    assert rc == 0
    captured = capsys.readouterr()
    out, err = captured.out, captured.err
    # 主输出（文本汇总）在 stdout
    assert "运行结果" in out and "总状态" in out
    # 进度/event/落点提示在 stderr，不污染 stdout。event 行前缀 `[core <scope>:event]`，与 worker 透传行
    # `[worker <scope>:err]` 同骨架 `[producer scope:kind]`（并发批量运行期间区分来源、scope 同列可竖扫）。
    assert "plan:" in err and ":event]" in err and "报告:" in err
    assert "plan:" not in out and ":event]" not in out


def test_run_writes_three_layer_artifacts(tmp_path, monkeypatch, capsys):
    # 默认归集落三层产物：RunStore(run_meta+run_state) + ResultStore(jobs/) + ReportStore(index/manifest)。
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    feat = _write_feature(tmp_path)
    report_dir = tmp_path / "reports"

    rc = m.main(["run", str(feat), "--json", "--report-dir", str(report_dir)])
    assert rc == 0

    run_dirs = list(report_dir.iterdir())
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]
    assert (run_dir / "run_meta.json").exists()
    assert (run_dir / "run_state.json").exists()
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "index.html").exists()
    assert (run_dir / "jobs").is_dir()
    # 判定明细一份一个文件，文件名就是运行态里这个 job 点名的标识
    [job_state] = json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))["jobs"]
    assert [p.name for p in (run_dir / "jobs").glob("*.json")] == [f"{job_state['result_id']}.json"]
    # 三层重构后不存在单一 run.json
    assert not (run_dir / "run.json").exists()


def test_no_report_skips_artifacts(tmp_path, monkeypatch, capsys):
    # --no-report：不落盘、--json 仍是单一文档（无 artifacts 键）。
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    feat = _write_feature(tmp_path)
    report_dir = tmp_path / "reports"

    rc = m.main(["run", str(feat), "--json", "--no-report", "--report-dir", str(report_dir)])
    assert rc == 0
    out = capsys.readouterr().out
    doc = json.loads(out)
    assert "artifacts" not in doc
    assert not report_dir.exists()  # --no-report 不创建落点


def test_assertion_votes_outside_one_to_five_rejected(tmp_path, monkeypatch, capsys):
    # --assertion-votes 取 1 到 5（ADR 0014「现状与未决」），两侧越界是同一处检查、在入口以退出码 2 拒绝。小于 1 时 worker 执行
    # 0 次 AI 断言——0 → 全判失败（假阴性）；负数 → 0>负/2=True 全绿但零 AI 调用（假阳性，最危险）。大于 5 时说明给出改法。
    called = {"n": 0}
    def spy_schedule(*a, **k):
        called["n"] += 1
        return _fake_schedule_factory()(*a, **k)
    monkeypatch.setattr(m, "schedule", spy_schedule)
    feat = _write_feature(tmp_path)
    for bad, why in (("0", "不被执行"), ("-1", "不被执行"), ("6", "改写这条断言的措辞或改成确定性 step"), ("100", "分多次执行")):
        rc = m.main(["run", str(feat), "--assertion-votes", bad, "--no-report"])
        assert rc == 2, f"--assertion-votes {bad} 应退出码 2"
        err = capsys.readouterr().err
        assert f"--assertion-votes 须为 1 到 5 之间的整数（收到 {bad}）" in err and why in err
    assert called["n"] == 0  # schedule 从未被调用——坏值在入口就被拦，没白起 worker
    for bad in ("0", "6"):  # plan 与 submit 走同一处检查
        assert m.main(["plan", str(feat), "--assertion-votes", bad]) == 2
        assert "须为 1 到 5 之间的整数" in capsys.readouterr().err
        assert m.main(["submit", str(feat), "--assertion-votes", bad, "--report-dir", str(tmp_path / "r")]) == 2
        assert "须为 1 到 5 之间的整数" in capsys.readouterr().err
    assert not (tmp_path / "r").exists()


@pytest.mark.parametrize("votes", ["1", "5"])
def test_assertion_votes_at_both_ends_of_the_range_pass(tmp_path, monkeypatch, capsys, votes):
    feat = _write_feature(tmp_path)
    assert m.main(["plan", str(feat), "--json", "--assertion-votes", votes]) == 0
    assert json.loads(capsys.readouterr().out)["jobs"][0]["assertion_votes"] == int(votes)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    assert m.main(["run", str(feat), "--assertion-votes", votes, "--no-report"]) == 0


def test_assertion_votes_help_states_the_range(capsys):
    """三个命令的 --help 都写出取值范围。"""
    for cmd in ("run", "plan", "submit"):
        with pytest.raises(SystemExit):
            m.main([cmd, "--help"])
        out = re.sub(r"\s+", "", capsys.readouterr().out)  # argparse 按终端宽度折行，中文长串也可能在字间折开
        assert "取1到5之间的整数" in out, cmd


def _write_feature_with_jobs(tmp_path: Path, n: int) -> Path:
    """一条未标 scope 的 Outline，展开成 n 个 scenario、各自一个 job。"""
    feat = tmp_path / "many.feature"
    rows = "".join(f"      | {i} |\n" for i in range(n))
    feat.write_text(f"Feature: F\n  Scenario Outline: o <n>\n    When \"做 <n>\"\n    Examples:\n      | n |\n{rows}",
                    encoding="utf-8")
    return feat


def _size_cap_line(err: str) -> str:
    [line] = [ln for ln in err.splitlines() if "超过了一个 run 的上限" in ln]
    return line


def test_run_size_cap_rejects_plan_run_and_local_submit_with_one_sentence(tmp_path, monkeypatch, capsys):
    """一个 run 至多 500 个 job（ADR 0025「一个 run 的规模上限」）：plan、run、本机 submit 以同一句说明、退出码 2 结束，没有开始执行——
    schedule 一次没调、后台推进进程没有启动、报告目录没有建。500 个 job 照常通过。"""
    import subprocess

    assert m.main(["plan", str(_write_feature_with_jobs(tmp_path, 500))]) == 0
    capsys.readouterr()
    called = {"n": 0}
    monkeypatch.setattr(m, "schedule", lambda *a, **k: called.__setitem__("n", called["n"] + 1))
    forked = []
    monkeypatch.setattr(subprocess, "Popen", lambda cmd, **kw: forked.append(cmd))
    feat = _write_feature_with_jobs(tmp_path, 501)
    reports = tmp_path / "reports"
    lines = []
    for argv in (["plan", str(feat)],
                 ["run", str(feat), "--report-dir", str(reports)],
                 ["submit", str(feat), "--report-dir", str(reports)]):
        assert m.main(argv) == 2, argv[0]
        lines.append(_size_cap_line(capsys.readouterr().err))
    assert len(set(lines)) == 1 and "501 个 job" in lines[0] and "500" in lines[0]
    # 前缀不预设原因：job 太多不是配置矛盾，run 与 submit 下也不说「plan 失败」
    assert lines[0].startswith("用例预检未通过，拒绝运行：这个 run 有 501 个 job")
    assert "配置矛盾" not in lines[0] and "plan 失败" not in lines[0]
    assert called["n"] == 0 and forked == [] and not reports.exists()


def test_feature_path_that_is_not_valid_utf8_exits_2(tmp_path, monkeypatch, capsys):
    """Linux 上文件名含非 UTF-8 字节时，命令行参数按 surrogateescape 解码，uri 里带孤立代理字符：plan、run、submit 以退出码 2
    结束并说明改名，不以回溯结束。这台机器的文件系统未必接受这样的文件名，所以由 load_feature 直接给出这样的 uri。"""
    from gherkai_core.scope import FeatureSource

    feat = _write_feature(tmp_path)
    text = feat.read_text(encoding="utf-8")
    monkeypatch.setattr(compose, "load_feature", lambda path: FeatureSource(uri="caf\udce9.feature", text=text))
    monkeypatch.setattr(m, "schedule", lambda *a, **k: pytest.fail("不应开始执行"))
    for argv in (["plan", str(feat)], ["run", str(feat), "--no-report"],
                 ["submit", str(feat), "--report-dir", str(tmp_path / "r")]):
        assert m.main(argv) == 2, argv[0]
        err = capsys.readouterr().err
        assert "用例预检未通过，拒绝运行：" in err and "不是有效的 UTF-8 文本" in err, argv[0]
    assert not (tmp_path / "r").exists()


def test_run_rejects_max_concurrency_below_one(tmp_path, monkeypatch, capsys):
    # --max-concurrency < 1 在入口被拒（退出码 2）：<=0 会让 plan_next 永不提议起 job → run 卡死在 pending
    # （比「慢一点」严重得多）。**零副作用**：schedule 一次没调、落点目录都没建（拒在读 feature/落库之前）。
    called = {"n": 0}
    monkeypatch.setattr(m, "schedule", lambda *a, **k: called.__setitem__("n", called["n"] + 1))
    feat = _write_feature(tmp_path)
    report_dir = tmp_path / "reports"
    for bad in ("0", "-1"):
        rc = m.main(["run", str(feat), "--max-concurrency", bad, "--report-dir", str(report_dir)])
        assert rc == 2, f"--max-concurrency {bad} 应退出码 2"
        assert "--max-concurrency" in capsys.readouterr().err
    assert called["n"] == 0          # schedule 从未被调用
    assert not report_dir.exists()   # 落库也没发生（persistence.begin 都没走到）


def test_submit_rejects_max_concurrency_below_one(tmp_path, monkeypatch, capsys):
    # 同上，submit 侧（坏值会随 definition 到达推进器 → 三路推进器全空转）。零副作用即没启动后台推进进程、
    # 没写 run 目录（对齐 test_tunnel_cli 的「隧道一次都没起」断言风格：早拒才真零副作用）。
    import subprocess

    forked = []
    monkeypatch.setattr(subprocess, "Popen", lambda cmd, **kw: forked.append(cmd))
    feat = _write_feature(tmp_path)
    report_dir = tmp_path / "reports"
    for bad in ("0", "-1"):
        rc = m.main(["submit", str(feat), "--max-concurrency", bad, "--report-dir", str(report_dir)])
        assert rc == 2, f"--max-concurrency {bad} 应退出码 2"
        assert "--max-concurrency" in capsys.readouterr().err
    assert forked == []              # 后台推进进程一次也没有启动
    assert not report_dir.exists()   # definition 也没落库


# ---- 用例预检（plan）：纯本地、不连 AWS、零费用 ----

def test_plan_text_shows_scope_grouping(tmp_path, capsys):
    # plan 子命令：读 feature → 渲染 scope/job 分组，不起 worker（无需 monkeypatch schedule）。
    feat = tmp_path / "demo.feature"
    feat.write_text(
        "@scope:s @engine:midscene\nFeature: F\n  Scenario: a\n    When \"做事\"\n    Then \"对吗\"\n",
        encoding="utf-8",
    )
    rc = m.main(["plan", str(feat)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "plan（用例预检，未执行）" in out
    assert "1 job(scope)" in out
    assert "engine=midscene" in out          # @engine tag 生效
    assert "Then" in out and "对吗" in out    # step 预览


# ---- 测试目标与按目标的 timeout（ADR 0048 决策 4、5；0034「job timeout」节）----

def test_plan_shows_target_and_device_session_count(tmp_path, capsys):
    feat = _write_feature(tmp_path)
    assert m.main(["plan", str(feat)]) == 0
    out = capsys.readouterr().out
    assert "target=desktop/web" in out and "远程访问会话 0" in out
    assert m.main(["plan", str(feat), "--json"]) == 0
    doc = json.loads(capsys.readouterr().out)
    assert doc["device_session_count"] == 0
    assert doc["jobs"][0]["target"] == {"device": "desktop", "ui_kind": "web"} and doc["jobs"][0]["device_request"] is None  # 键集固定
    assert doc["jobs"][0]["timeout_s"] == 300.0  # 不给 --default-job-timeout（哨兵「未指定」）：plan 层按目标补桌面缺省 300


def test_default_job_timeout_sentinel_explicit_and_non_finite(tmp_path, capsys):
    feat = _write_feature(tmp_path)
    assert m.main(["plan", str(feat), "--json", "--default-job-timeout", "0"]) == 0
    assert json.loads(capsys.readouterr().out)["jobs"][0]["timeout_s"] == 7200.0  # 显式非正：取产品上限（不再有「不超时」）
    assert m.main(["plan", str(feat), "--json", "--default-job-timeout", "7201"]) == 2  # 有效预算超过上限：计划阶段拒绝
    assert "超过了上限 7200 秒" in capsys.readouterr().err
    assert m.main(["plan", str(feat), "--json", "--default-job-timeout", "120"]) == 0
    assert json.loads(capsys.readouterr().out)["jobs"][0]["timeout_s"] == 120.0  # 显式 120 与内建缺省可区分
    for bad in ("nan", "inf", "1e400", "abc"):  # 归一化只接受有限数（nan / inf 会让超时保护静默失效）
        with pytest.raises(SystemExit) as ei:
            m.main(["plan", str(feat), "--default-job-timeout", bad])
        assert ei.value.code == 2
        assert "--default-job-timeout" in capsys.readouterr().err


def test_plan_config_receives_sentinel_explicit_value_and_device_defaults(tmp_path, monkeypatch):
    """CLI 组装的 PlanConfig：不给 --default-job-timeout 传「未指定」哨兵 None（与显式 300 可区分）；设备缺省与下限按内建获取预算算出
    （600 加 900 / 600 加 180）；桌面缺省 300。"""
    box = {}
    real_plan = m.plan

    def spy(features, cfg, **kw):
        box["cfg"] = cfg
        return real_plan(features, cfg, **kw)

    monkeypatch.setattr(m, "plan", spy)
    feat = _write_feature(tmp_path)
    assert m.main(["plan", str(feat)]) == 0
    cfg = box["cfg"]
    assert cfg.default_job_timeout_s is None
    assert (cfg.default_desktop_job_timeout_s, cfg.default_device_job_timeout_s, cfg.min_device_job_timeout_s) == (300.0, 1500.0, 780.0)
    assert m.main(["plan", str(feat), "--default-job-timeout", "300"]) == 0
    assert box["cfg"].default_job_timeout_s == 300.0


@pytest.mark.parametrize("cmd", ["run", "submit"])
def test_run_and_submit_reject_non_finite_default_job_timeout(tmp_path, cmd, capsys):
    """三处 --default-job-timeout 各自声明：run 与 submit 对 nan / inf 同样以退出码 2 结束（argparse 层）。"""
    feat = _write_feature(tmp_path)
    for bad in ("nan", "inf"):
        with pytest.raises(SystemExit) as ei:
            m.main([cmd, str(feat), "--default-job-timeout", bad])
        assert ei.value.code == 2 and "--default-job-timeout" in capsys.readouterr().err


def test_plan_shows_device_target_and_session_count_when_engine_supports_it(tmp_path, monkeypatch, capsys):
    """ADR 0048 决策 5：引擎自述支持 Android 时，plan 显示 target=android/web、远程访问会话数 1，--json 里 device_session_count 为 1、
    job 带 target、timeout_s 取设备缺省 1500。"""
    feat = tmp_path / "dev.feature"
    feat.write_text("@device:android\nFeature: F\n  Scenario: a\n    When \"做事\"\n", encoding="utf-8")

    def caps_with_android(engine, *, steps_dir=None, timeout_s=60.0):
        return {"schema_version": 2, "engine": engine, "min_grace_s": 150.0, "deterministic_steps": [], "model_id": "m",
                "targets": [{"device": "desktop", "ui_kinds": ["web"]}, {"device": "android", "ui_kinds": ["web", "app"], "max_session_s": 8000.0}]}

    def no_match(engine, *a, **k):
        raise compose.WorkerUnavailableError(engine, "查询超时")  # 取不到：标注降级，plan 本体照出

    monkeypatch.setattr(compose, "query_capabilities", caps_with_android)
    monkeypatch.setattr(compose, "match_deterministic", no_match)
    assert m.main(["plan", str(feat)]) == 0
    out = capsys.readouterr().out
    assert "target=android/web" in out and "远程访问会话 1" in out
    assert m.main(["plan", str(feat), "--json"]) == 0
    doc = json.loads(capsys.readouterr().out)
    assert doc["device_session_count"] == 1
    assert doc["jobs"][0]["target"] == {"device": "android", "ui_kind": "web"} and doc["jobs"][0]["timeout_s"] == 1500.0


def test_validate_definition_rejects_plan_form_device_job_before_writing():
    """写 definition 之前的结构校验（ADR 0048 决策 3 第一处）：组合根尚未填入设备请求的设备 job 以退出码 2 被拒；桌面 job 放行。"""
    from gherkai_core.model import Job, Scenario, Step, Target

    scs = (Scenario(id="f:1", name="n", steps=(Step(0, "When", "x"),)),)
    device = Job(scope_id="d", scope_name="d", engine="midscene", scenarios=scs, timeout_s=1500.0, target=Target(device="android", ui_kind="web"))
    desktop = Job(scope_id="w", scope_name="w", engine="midscene", scenarios=scs, timeout_s=300.0)
    assert submission.validate_definition([desktop]) is None
    assert submission.validate_definition([desktop, device]) == 2


def test_plan_json_app_entry_is_exactly_alias_and_app_id():
    """plan 形态的应用条目只有别名与包名两键（位置三项由组合根在提交时填入，ADR 0048 决策 3）。"""
    from gherkai_core.model import AppRef, Job, Scenario, Step, Target

    scs = (Scenario(id="f:1", name="n", steps=(Step(0, "When", "x"),)),)
    job = Job(scope_id="d", scope_name="d", engine="midscene", scenarios=scs, timeout_s=1500.0,
              target=Target(device="android", ui_kind="app", app=AppRef(alias="shop", app_id="com.example.shop")))
    doc = m.render.plan_to_dict([job], "midscene", None)
    assert doc["jobs"][0]["target"] == {"device": "android", "ui_kind": "app", "app": {"alias": "shop", "app_id": "com.example.shop"}}


def test_cloud_submit_rejects_device_job_in_shared_prestep_before_touching_cloud(tmp_path, monkeypatch, capsys):
    """设备选择接在 run / submit 的共享前置里（ADR 0053 决策 4）：没有任何来源指定设备的设备 job 在这里以退出码 2 被拒、消息是产品语言，
    之后的云端解析一步都不走（删掉接线这条用例会撞到被禁的云端调用）。本机 run 的同一拒绝见
    test_project_config 的 test_unspecified_device_plan_warns_but_run_and_submit_exit_2_before_any_cloud_call。"""
    feat = tmp_path / "dev.feature"
    feat.write_text("@device:android\nFeature: F\n  Scenario: a\n    When \"做事\"\n", encoding="utf-8")

    def forbidden(*a, **k):
        raise AssertionError("设备 job 应在写前校验被拒，不该走到云端解析")

    monkeypatch.setattr(compose, "resolve_cloud_target", forbidden)
    monkeypatch.setattr(m, "_cloud_skew_gate", forbidden)
    assert m.main(["submit", str(feat), "--backend", "cloud", "--prefix", "p-"]) == 2
    err = capsys.readouterr().err
    assert "没有指定用哪台设备" in err and "[devices.android]" in err and "--android-device-arn" in err
    assert "当且仅当" not in err and "设备请求" not in err


def test_device_target_rejected_by_plan_and_preflight_when_engine_lacks_target(tmp_path, monkeypatch, capsys):
    """ADR 0048 决策 4：假 worker 自述只有桌面网页，标了 @device:android 的 scope 在 plan 与 run 的执行前预检都以退出码 2 结束、消息给出改法；
    不建立任何会话（run 不该走到 schedule）。"""
    feat = tmp_path / "dev.feature"
    feat.write_text("@device:android\nFeature: F\n  Scenario: a\n    When \"做事\"\n", encoding="utf-8")
    assert m.main(["plan", str(feat)]) == 2
    err = capsys.readouterr().err
    assert "不支持这个目标" in err and "Android 网页" in err and "@engine:" in err and "--default-engine" in err
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    assert m.main(["run", str(feat), "--no-report"]) == 2
    assert "不支持这个目标" in capsys.readouterr().err


def test_plan_target_check_degrades_when_capabilities_unavailable(tmp_path, monkeypatch, capsys):
    """能力自述取不到（引擎没装、查询失败）时 plan 只警告、不判定（ADR 0048 决策 4），最终由执行前预检拒绝。"""
    feat = tmp_path / "dev.feature"
    feat.write_text("@device:android\nFeature: F\n  Scenario: a\n    When \"做事\"\n", encoding="utf-8")

    def unavailable(engine, *, steps_dir=None, timeout_s=60.0):
        raise compose.WorkerUnavailableError(engine, "自述超时")

    def no_match(engine, *a, **k):
        raise compose.WorkerUnavailableError(engine, "查询超时")

    monkeypatch.setattr(compose, "query_capabilities", unavailable)
    monkeypatch.setattr(compose, "match_deterministic", no_match)
    assert m.main(["plan", str(feat)]) == 0
    err = capsys.readouterr().err
    assert "目标核对降级" in err and "不支持这个目标" not in err


def _fake_old_worker(tmp_path: Path, monkeypatch, *, engine: str, schema_version: int) -> Path:
    """真起子进程的假 worker（经定位链第一级的 env 覆写）：能力自述报给定的协议版本、不带 targets（1.4 的形态），
    匹配查询逐条答作走 AI 并以 0 退出（1.4 的 Midscene worker 对对象条目的实际行为）。返回记录每次所收 flag 的日志文件。"""
    import shlex
    import sys

    log = tmp_path / "worker-calls.log"
    script = tmp_path / "old_worker.py"
    script.write_text(
        "import json, sys\n"
        "log, flag = sys.argv[1], sys.argv[2]\n"
        "open(log, 'a', encoding='utf-8').write(flag + '\\n')\n"
        "if flag == '--capabilities':\n"
        f"    print(json.dumps({{'schema_version': {schema_version}, 'engine': '{engine}', 'min_grace_s': 31,"
        " 'deterministic_steps': [], 'model_id': 'm'}))\n"
        "elif flag == '--match-steps':\n"
        "    print(json.dumps([None for _ in json.load(sys.stdin)]))\n",
        encoding="utf-8")
    monkeypatch.setenv(f"GHERKAI_WORKER_{engine.upper()}_CMD",
                       f"{shlex.quote(sys.executable)} {shlex.quote(str(script))} {shlex.quote(str(log))}")
    monkeypatch.delenv(f"GHERKAI_WORKER_{engine.upper()}_CWD", raising=False)
    monkeypatch.setattr(compose, "query_capabilities", _REAL_QUERY_CAPABILITIES)  # 真契约校验参与
    return log


def test_plan_checks_protocol_version_before_match_query(tmp_path, monkeypatch, capsys):
    """ADR 0036 决策 4「匹配查询的前置」：新命令行工具配协议版本为 1 的旧 Midscene worker，plan 先取能力自述、核到版本不一致即以
    退出码 2 结束并转述版本不一致那一句，不发匹配查询（旧 worker 对匹配查询的回答形状完全合法，先发就会被当作全部走 AI）。"""
    feat = tmp_path / "t.feature"
    feat.write_text('@engine:midscene\nFeature: t\n  Scenario: s\n    Given "https://example.com/"\n', encoding="utf-8")
    log = _fake_old_worker(tmp_path, monkeypatch, engine="midscene", schema_version=1)
    assert m.main(["plan", str(feat)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "plan 拒绝出结果" in captured.err and "能力自述格式版本是 1，这个命令行工具认的是 2" in captured.err
    assert "命令行工具与 worker 的版本不一致，请把两者装成同一版本。" in captured.err
    assert "标注降级" not in captured.err and "以 worker 自己的报错为准" not in captured.err  # 不是降级、也不是 worker 自己的报错
    assert log.read_text(encoding="utf-8").split() == ["--capabilities"]  # 匹配查询没有发出


@pytest.mark.parametrize("failure", [
    compose.WorkerIncompatibleError("novaact", "引擎 novaact 自述的模型 id 不是非空字符串（''）：命令行工具与 worker 的版本不一致，请把两者装成同一版本。"),
    compose.WorkerIncompatibleError("novaact", "要问的是引擎 novaact 的 worker，回答的却自称 'midscene'——这个引擎的 worker 路径指错了？（检查 GHERKAI_WORKER_*_CMD）"),
    ValueError("环境变量 NOVA_ACT_TIMEOUT_S 须是正整数秒（单个 AI 操作的时间上界），当前值：'120s'。改成整数秒（如 120），或删掉它使用默认值 120。"),
    compose.WorkerSelfDescribeError("novaact", 2, "demo.py：SyntaxError", "能力自述"),
])
def test_plan_exits_2_without_match_query_when_capabilities_incompatible_or_misconfigured(tmp_path, monkeypatch, capsys, failure):
    """自述取到了但不兼容（身份位或载荷键不合契约）、NOVA_ACT_TIMEOUT_S 取值不合法、worker 自述非零退出（使用方 steps 加载失败）：
    plan 与 run 同样以退出码 2 结束、转述该项诊断，不降级、不发匹配查询（ADR 0036 决策 4：plan 不比 run 宽）；成因提示只接在
    worker 非零退出之后，其余几项的消息出自命令行工具自己、本身即诊断。"""
    def broken(engine, **kw):
        raise failure

    def forbidden(*a, **k):
        raise AssertionError("能力自述不合要求时不应发匹配查询")

    monkeypatch.setattr(m.compose, "query_capabilities", broken)
    monkeypatch.setattr(m.compose, "match_deterministic", forbidden)
    assert m.main(["plan", str(_det_feature(tmp_path))]) == 2
    err = capsys.readouterr().err
    assert "plan 拒绝出结果" in err and str(failure) in err and "降级" not in err
    assert ("以 worker 自己的报错为准" in err) is isinstance(failure, compose.WorkerSelfDescribeError)


def test_plan_asks_capabilities_before_match_once_per_engine(tmp_path, monkeypatch, capsys):
    """正常路径的顺序（ADR 0036 决策 4）：每个用到的引擎先各取一次能力自述（桌面 job 也问），全部核过之后才发匹配查询；
    标注阶段的目标交集复用那一份、不再重问，故每引擎恰好自述一次、匹配查询一次。"""
    feat = tmp_path / "mixed.feature"
    feat.write_text(
        "Feature: mixed\n"
        "  @engine:midscene\n  Scenario: a\n    When \"做点啥\"\n"
        "  @engine:novaact\n  Scenario: b\n    When \"做点啥\"\n", encoding="utf-8")
    _fake_locator(monkeypatch, available=("novaact", "midscene"))
    calls: list[tuple[str, str]] = []
    stubbed = compose.query_capabilities  # conftest autouse 的确定性假替身
    monkeypatch.setattr(m.compose, "query_capabilities",
                        lambda engine, **kw: calls.append(("capabilities", engine)) or stubbed(engine, **kw))
    monkeypatch.setattr(m.compose, "match_deterministic",
                        lambda engine, items, steps_dir=None: calls.append(("match", engine)) or [None for _ in items])
    assert m.main(["plan", str(feat)]) == 0
    assert sorted(calls[:2]) == [("capabilities", "midscene"), ("capabilities", "novaact")]
    assert sorted(calls[2:]) == [("match", "midscene"), ("match", "novaact")]
    assert "降级" not in capsys.readouterr().err


def test_target_rejections_flag_timeout_over_session_limit():
    """执行前预检的第二项目标检查（ADR 0048 决策 3）：job 墙钟预算超过该目标的会话上限即拒绝；桌面条目不带上限不检查。"""
    from gherkai_core.model import Job, Scenario, Step, Target

    caps = {"targets": [{"device": "android", "ui_kinds": ["web", "app"], "max_session_s": 8000.0}, {"device": "desktop", "ui_kinds": ["web"]}]}
    scs = (Scenario(id="f:1", name="n", steps=(Step(0, "When", "x"),)),)
    over = Job(scope_id="s", scope_name="s", engine="midscene", scenarios=scs, timeout_s=9000.0, target=Target(device="android", ui_kind="web"))
    [msg] = submission.target_rejections([over], caps)
    assert "超过了引擎 midscene 在 Android 网页上的会话上限 8000 秒" in msg and "--default-job-timeout" in msg
    within = Job(scope_id="s", scope_name="s", engine="midscene", scenarios=scs, timeout_s=7000.0, target=Target(device="android", ui_kind="web"))
    desktop = Job(scope_id="d", scope_name="d", engine="midscene", scenarios=scs, timeout_s=99999.0)
    assert submission.target_rejections([within, desktop], caps) == []


def test_plan_json_shape(tmp_path, capsys):
    feat = tmp_path / "demo.feature"
    feat.write_text("Feature: F\n  Scenario: a\n    When \"做事\"\n", encoding="utf-8")
    rc = m.main(["plan", str(feat), "--default-engine", "midscene", "--json"])
    assert rc == 0
    doc = json.loads(capsys.readouterr().out)   # 单一 JSON 文档
    assert doc["job_count"] == 1 and doc["scenario_count"] == 1
    assert doc["default_engine"] == "midscene"
    assert doc["jobs"][0]["engine"] == "midscene"   # 未标 @engine → 用 default


def test_plan_rejects_engine_conflict(tmp_path, capsys):
    # 同 scope 多 engine → FeatureContractError，预检在实际运行前拦截、以退出码 2 结束（省钱）
    feat = tmp_path / "conflict.feature"
    feat.write_text(
        "@scope:x @engine:midscene\nFeature: F\n  Scenario: a\n    When \"x\"\n"
        "  @scope:x @engine:novaact\n  Scenario: b\n    When \"y\"\n",
        encoding="utf-8",
    )
    rc = m.main(["plan", str(feat)])
    assert rc == 2
    assert "多个 @engine" in capsys.readouterr().err   # 错误走 stderr


def test_plan_text_argument_hint(tmp_path, capsys):
    # 文本模式对 DataTable/DocString 标注尺寸（保持紧凑；完整内容走 --json）
    feat = tmp_path / "arg.feature"
    feat.write_text(
        "Feature: F\n  Scenario: a\n    When 填表\n      | k | v |\n      | 用户名 | alice |\n"
        "    Then 反馈\n      \"\"\"\n      行1\n      行2\n      \"\"\"\n",
        encoding="utf-8",
    )
    rc = m.main(["plan", str(feat)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "+dataTable(2×2)" in out    # 2 行 × 2 列
    assert "+docString(2 行)" in out


# ---- #7 run 退出码 + ScheduleOpts 参数映射 ----
def _capturing_schedule(status, opts_box):
    """假 schedule：把传入 opts 存进 opts_box、每个 job 都判出指定 status（验退出码/参数映射）。"""
    def fake(run_meta, engines, sink, opts=None, on_job_complete=None, on_event=None):
        opts_box["opts"] = opts
        opts_box["run_meta"] = run_meta
        results = [JobResult(job=j, status=status) for j in run_meta.jobs]
        if on_job_complete is not None:
            for jr in results:
                on_job_complete(jr)
        return _execution(run_meta, results)
    return fake


def test_run_exit_code_1_on_failed(tmp_path, monkeypatch, capsys):
    box = {}
    monkeypatch.setattr(m, "schedule", _capturing_schedule(Status.FAILED, box))
    rc = m.main(["run", str(_write_feature(tmp_path)), "--no-report"])
    assert rc == 1  # 运行结束但有 failed → 退出码 1（CI 据此判红）


def test_run_exit_code_1_on_error(tmp_path, monkeypatch, capsys):
    box = {}
    monkeypatch.setattr(m, "schedule", _capturing_schedule(Status.ERROR, box))
    rc = m.main(["run", str(_write_feature(tmp_path)), "--no-report"])
    assert rc == 1


def test_run_schedule_opts_mapping(tmp_path, monkeypatch, capsys):
    box = {}
    monkeypatch.setattr(m, "schedule", _capturing_schedule(Status.PASSED, box))
    # grace 用合法值（≥ Nova 下限）；默认引擎 novaact → min_grace 取该引擎 worker 自报的下限（假 worker 见 conftest）。
    good_grace = FAKE_MIN_GRACE_S["novaact"] + 10
    m.main(["run", str(_write_feature(tmp_path)), "--no-report",
            "--max-concurrency", "3", "--default-job-timeout", "120", "--grace", str(good_grace), "--fail-fast"])
    o = box["opts"]
    assert o.max_concurrency == 3 and o.fail_fast is True
    assert o.grace_period_s == float(good_grace)
    # timeout 载体在 definition（ADR 0034「job timeout」节）：--default-job-timeout 填进未标 @timeout 的 Job
    assert all(j.timeout_s == 120.0 for j in box["run_meta"].jobs)
    # max_concurrency 同步落 definition（ADR 0034 机制四）：同步 run 的 ScheduleOpts 仍直用 flag（同进程），
    # 但 meta 照落——definition 要诚实记「这个 run 声明了几路并行」
    assert box["run_meta"].max_concurrency == 3
    # min_grace_s 也传给 core（核心不变量：core enforce grace≥此下限，ADR 0024 grace 硬约束）
    assert o.min_grace_s == FAKE_MIN_GRACE_S["novaact"]


def test_run_grace_too_small_rejected(tmp_path, monkeypatch, capsys):
    # 显式给过小 grace（< Nova 下限）→ 入口给退出码 2「没开始执行就被拒」（ADR 0024 grace 硬约束、对齐 votes 校验惯例）。
    box = {}
    monkeypatch.setattr(m, "schedule", _capturing_schedule(Status.PASSED, box))
    rc = m.main(["run", str(_write_feature(tmp_path)), "--no-report", "--grace", "5"])
    assert rc == 2
    assert "opts" not in box  # schedule 根本没被调（运行前就拒了）
    assert "--grace=5.0" in capsys.readouterr().err  # 诊断打到 stderr


def test_run_grace_nan_inf_rejected(tmp_path, monkeypatch, capsys):
    """--grace inf/nan 同拒（退出码 2）：inf 会让 SIGKILL 兜底永不触发、软停失效即挂死（ADR 0024/0026）；
    与 @timeout 的「有限正数」判据相同。"""
    for bad in ("inf", "nan"):
        box = {}
        monkeypatch.setattr(m, "schedule", _capturing_schedule(Status.PASSED, box))
        rc = m.main(["run", str(_write_feature(tmp_path)), "--no-report", "--grace", bad])
        assert rc == 2, bad
        assert "opts" not in box
        assert "有限正数" in capsys.readouterr().err


def test_run_grace_sentinel_derives_from_engine_self_report(tmp_path, monkeypatch, capsys):
    """不给 --grace（哨兵默认 None）→ 按本 run 引擎**自报**的下限推导（ADR 0024「引擎自报下限」）：
    novaact-only run 的 grace 等于 min_grace，即该引擎 worker 报的值，不再是组合根算的常量、也不是旧的硬编码 10。"""
    box = {}
    monkeypatch.setattr(m, "schedule", _capturing_schedule(Status.PASSED, box))
    m.main(["run", str(_write_feature(tmp_path)), "--no-report"])
    o = box["opts"]
    assert o.grace_period_s == FAKE_MIN_GRACE_S["novaact"]
    assert o.min_grace_s == FAKE_MIN_GRACE_S["novaact"]


def test_run_grace_mixed_engines_takes_max_of_self_reported(tmp_path, monkeypatch, capsys):
    """混引擎 run 取各引擎自报下限的 max（grace 是 run 级单值，ADR 0024）——两个引擎都问、按大的那个定。"""
    feat = tmp_path / "mixed.feature"
    feat.write_text(
        "Feature: mixed\n"
        "  @engine:midscene\n  Scenario: a\n    When \"做点啥\"\n"
        "  @engine:novaact\n  Scenario: b\n    When \"做点啥\"\n", encoding="utf-8")
    _fake_locator(monkeypatch, available=("novaact", "midscene"))  # 两个引擎都得「装了」才能取得（dev 机常缺 midscene）
    asked: list[str] = []
    stubbed = compose.query_capabilities  # conftest autouse 装的确定性假替身（不是真 spawn），此处只在它外面加计数
    monkeypatch.setattr(m.compose, "query_capabilities",
                        lambda engine, **kw: asked.append(engine) or stubbed(engine, **kw))
    box = {}
    monkeypatch.setattr(m, "schedule", _capturing_schedule(Status.PASSED, box))
    assert m.main(["run", str(feat), "--no-report"]) == 0
    assert sorted(asked) == ["midscene", "novaact"]
    assert box["opts"].min_grace_s == max(FAKE_MIN_GRACE_S.values())


def test_local_run_asks_each_engine_for_capabilities_once(tmp_path, monkeypatch, capsys):
    """本机 run **每引擎只问一次能力自述**（ADR 0036「5.」一次 spawn 拿全：steps 加载结果 + 清单 + grace 下限）。

    运行前检查带着解析出的 steps 目录问那一次，2a 的 grace 下限就复用同一份对象（compose 的进程内缓存，下限与
    使用方 step 无关）——两处各问一次等于每个引擎多 spawn 一个 worker（Nova 每次还要 import SDK）。
    计数装在假替身**外面**：替身只替掉「问 worker」那一跳，被测的是 cli 与 compose 的复用逻辑。
    """
    steps = tmp_path / "steps"
    steps.mkdir()
    asked: list[tuple] = []
    stubbed = compose.query_capabilities  # conftest autouse 装的确定性假替身（不是真 spawn）
    monkeypatch.setattr(m.compose, "query_capabilities",
                        lambda engine, **kw: asked.append((engine, kw.get("steps_dir"))) or stubbed(engine, **kw))
    box = {}
    monkeypatch.setattr(m, "schedule", _capturing_schedule(Status.PASSED, box))
    assert m.main(["run", str(_write_feature(tmp_path)), "--no-report", "--steps-dir", str(steps)]) == 0
    assert asked == [("novaact", str(steps.resolve()))]  # 只一次，且带着解析出的 steps 目录
    assert box["opts"].min_grace_s == FAKE_MIN_GRACE_S["novaact"]  # 下限仍取自那份自述


def test_run_engine_self_describe_failure_refuses_to_run(tmp_path, monkeypatch, capsys):
    """取不到引擎自报的下限（版本不一致的 worker 不认该入口 / 起不来 / 输出不合契约）→ **以退出码 2 结束、绝不回落猜的下限**
    （ADR 0024「引擎自报下限」fail-loud；回落就是 grace 默默不够、收尾被强杀）。文案与自述失败同一口径。"""
    box = {}
    monkeypatch.setattr(m, "schedule", _capturing_schedule(Status.PASSED, box))
    monkeypatch.setattr(m.compose, "query_capabilities", lambda engine, **kw: (_ for _ in ()).throw(
        compose.WorkerSelfDescribeError(engine, 2, "unrecognized arguments: --capabilities", "能力自述")))
    rc = m.main(["run", str(_write_feature(tmp_path)), "--no-report"])
    assert rc == 2
    assert "opts" not in box  # schedule 根本没被调（运行前就拒了，零副作用）
    err = capsys.readouterr().err
    assert "worker 自述失败，拒绝运行" in err and "novaact" in err


def test_run_timeout_nonpositive_maps_to_product_cap(tmp_path, monkeypatch, capsys):
    # --default-job-timeout <=0 → Job.timeout_s 取产品上限 7200（ADR 0054 决策十），是有逻辑的转换，护住它
    box = {}
    monkeypatch.setattr(m, "schedule", _capturing_schedule(Status.PASSED, box))
    m.main(["run", str(_write_feature(tmp_path)), "--no-report", "--default-job-timeout", "0"])
    assert box["run_meta"].jobs and all(j.timeout_s == 7200.0 for j in box["run_meta"].jobs)


def _deadline_offset_s(meta) -> float:
    from datetime import datetime
    return (datetime.fromisoformat(meta.deadline_at) - datetime.fromisoformat(meta.created_at)).total_seconds()


def test_run_writes_deadline_from_the_resolved_grace_even_with_no_report(tmp_path, monkeypatch, capsys):
    """前台 run 的运行期限（ADR 0054 决策二）：本机后端的每 job 尾段取这次调用解析出的停止宽限 G，2G + 10 秒；
    `--no-report` 不落任何记录，definition 里同样带期限（执行方要用它）。不给 --grace 时 G 跟随引擎自报的下限。"""
    from gherkai_core.schedule import ScheduleOpts
    box = {}
    monkeypatch.setattr(m, "schedule", _capturing_schedule(Status.PASSED, box))
    assert m.main(["run", str(_write_feature(tmp_path)), "--no-report", "--default-job-timeout", "600", "--grace", "200"]) == 0
    assert _deadline_offset_s(box["run_meta"]) == 900 + 600 + 2 * 200 + 10
    assert m.main(["run", str(_write_feature(tmp_path)), "--no-report"]) == 0
    [job] = box["run_meta"].jobs
    grace = max(FAKE_MIN_GRACE_S[job.engine], ScheduleOpts.grace_period_s)
    assert _deadline_offset_s(box["run_meta"]) == 900 + 300 + 2 * grace + 10


def test_local_submit_deadline_takes_the_largest_engine_grace(tmp_path, monkeypatch, inline_children, advanced):
    """本机 submit 没有 run 级的停止宽限：期限取这个 run 用到的各引擎自报宽限里最大的一个，每个 job 都按它算尾段。宽限由提交进程算好
    交给后台推进进程，写进它生成的运行定义，推进用的也是这一份。"""
    from gherkai_core.serialize import run_meta_from_dict

    _fake_locator(monkeypatch, available=("novaact", "midscene"))  # 两个引擎都在本机（运行前检查要找到 worker）
    feat = tmp_path / "two.feature"
    feat.write_text("Feature: F\n  @scope:a @engine:novaact\n  Scenario: s1\n    When \"做 A\"\n"
                    "  @scope:b @engine:midscene\n  Scenario: s2\n    When \"做 B\"\n", encoding="utf-8")
    reports = tmp_path / "reports"
    assert m.main(["submit", str(feat), "--report-dir", str(reports)]) == 0
    inline_children.settle()
    run_dir = _submitted_run_dir(reports)
    meta = run_meta_from_dict(json.loads((run_dir / "run_meta.json").read_text(encoding="utf-8")))
    grace = max(FAKE_MIN_GRACE_S.values())
    assert _deadline_offset_s(meta) == 900 + 2 * (300 + 2 * grace + 10)
    assert advanced == [meta]


def test_local_submit_exits_2_when_engine_grace_cannot_be_read(tmp_path, monkeypatch, capsys):
    """本机 submit 取不到引擎自报宽限时与 run 一样拒绝：退出码 2、不启动后台推进进程、不落库。"""
    import subprocess

    forked = []
    monkeypatch.setattr(subprocess, "Popen", lambda cmd, **kw: forked.append(cmd))

    def boom(engine):
        raise RuntimeError("worker 起不来")

    monkeypatch.setattr(m.compose, "engine_min_grace", boom)
    reports = tmp_path / "reports"
    assert m.main(["submit", str(_write_feature(tmp_path)), "--report-dir", str(reports)]) == 2
    assert forked == [] and not reports.exists()
    assert "worker 自述失败，拒绝提交" in capsys.readouterr().err


# ---- #8 畸形 feature → 友好诊断、以退出码 2 结束、无 traceback ----
def test_malformed_feature_friendly_diagnostic(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())  # 不该走到 schedule
    bad = tmp_path / "bad.feature"
    bad.write_text("this is not gherkin\n  garbage\n", encoding="utf-8")
    for cmd in ("plan", "run"):
        rc = m.main([cmd, str(bad), "--no-report"] if cmd == "run" else [cmd, str(bad)])
        assert rc == 2, f"{cmd} 畸形 feature 应以退出码 2 结束"
        err = capsys.readouterr().err
        assert "语法错误" in err and "Traceback" not in err  # 友好诊断、非 Python traceback


# ---- 前台实时写的写序：逐 job 先存明细、再写终态并点名，收尾按点名读回（ADR 0030 决定三）----
# 用 fake store 记录调用序（共享一个有序 log），注入真 RunPersistence 编排——测真实写序、非 mock 行为。
# 注入点是 patch compose.build_local_stores（ADR 0016：local 装配下沉 compose 后的注入锚，取代旧的 m.Local*）。
def _recording_build_local_stores(calls: list, named: list):
    """返回一个替换 compose.build_local_stores 的 fake：产出三个记录调用的 fake store + make_artifacts。run store 在内存里持有
    运行态，终态写与结束写对它的作用取 core 的那一处定义（`run_status.commit_applied`、`ending_applied`），与两个真 adapter 相同。
    判定存储按标识存取，读回的就是那个标识下存的一份。named 依次记下 (哪一方, scope_id, 标识)：保存时记 "saved"，终态写里给出的
    JobState 记 "committed"。"""
    from dataclasses import replace

    from gherkai_core.run_status import commit_applied, ending_applied

    class FakeRunStore:
        state = None

        def preflight(self): calls.append(("run", "preflight", None))

        def create_run(self, meta, initial_state):
            calls.append(("run", "create_run", None))
            self.state = initial_state

        def update_job_state(self, run_id, js):
            calls.append(("run", "update_job_state", js.scope_id))
            self.state = replace(self.state, status=Status.RUNNING, jobs={**self.state.jobs, js.scope_id: js})
            return True

        def commit_job_states(self, run_id, job_states, *, ended_at):
            calls.append(("run", "commit_job_states", ",".join(js.scope_id for js in job_states)))
            named.extend(("committed", js.scope_id, js.result_id) for js in job_states)
            new_state, outcome = commit_applied(self.state, job_states, ended_at=ended_at)
            if new_state is not None:
                self.state = new_state
            return outcome

        def end_run(self, run_id, ending, *, ended_at):
            calls.append(("run", "end_run", None))
            new_state = ending_applied(self.state, ending, ended_at=ended_at)
            if new_state is not None:
                self.state = new_state
            return new_state is not None

        def load_run_state(self, run_id):
            calls.append(("run", "load_run_state", None))
            return self.state

    class FakeResultStore:
        def __init__(self):
            self.saved = {}  # 标识 → 明细

        def preflight(self): calls.append(("result", "preflight", None))

        def save_job_result(self, run_id, result_id, jr):
            calls.append(("result", "save_job_result", jr.scope_id))
            named.append(("saved", jr.scope_id, result_id))
            self.saved[result_id] = jr

        def load_job_result(self, run_id, result_id):
            calls.append(("result", "load_job_result", result_id))
            return self.saved.get(result_id)

    class FakeReportStore:
        def preflight(self): calls.append(("report", "preflight", None))
        def write(self, run_id, result, *, created_at=""):
            calls.append(("report", "write", None))
            return f"file:///fake/{run_id}/index.html"

    def fake_build(*, report_dir, lock_holder=None):
        def make_artifacts(run_id, report_index):
            d = {"run_meta": f"file:///{run_id}/run_meta.json", "run_state": f"file:///{run_id}/run_state.json",
                 "jobs_dir": f"file:///{run_id}/jobs"}
            if report_index is not None:
                d["report_index"] = str(report_index)
            return d
        return FakeRunStore(), FakeResultStore(), FakeReportStore(), make_artifacts

    return fake_build


def _two_scope_feature(tmp_path: Path) -> Path:
    feat = tmp_path / "two.feature"
    feat.write_text(
        "Feature: F\n"
        "  @scope:a\n  Scenario: sa\n    When \"x\"\n"
        "  @scope:b\n  Scenario: sb\n    When \"y\"\n",
        encoding="utf-8",
    )
    return feat


def test_realtime_commit_point_write_order(tmp_path, monkeypatch, capsys):
    calls: list = []
    named: list = []
    # 注入 fake（patch compose.build_local_stores：cli 调它拿三 store → 喂给真 RunPersistence）
    monkeypatch.setattr(m.compose, "build_local_stores", _recording_build_local_stores(calls, named))
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())  # 每 job fire on_job_complete

    rc = m.main(["run", str(_two_scope_feature(tmp_path)), "--report-dir", str(tmp_path / "r"), "--quiet"])
    assert rc == 0

    methods = [(s, mth) for (s, mth, _) in calls]
    # ① create_run 是第一个**写**（preflight 探活在它之前、但那是探底不是写）；create_run 在所有 save_job_result 之前
    writes = [(s, mth) for (s, mth) in methods if mth != "preflight"]
    assert writes[0] == ("run", "create_run")
    first_save = next(i for i, (s, mth) in enumerate(methods) if mth == "save_job_result")
    create_idx = methods.index(("run", "create_run"))
    assert create_idx < first_save
    # ①b preflight（三个 store 各一次）全在 create_run 之前（ADR 0030 决定七：begin 先探活再写）
    last_preflight = max(i for i, (s, mth) in enumerate(methods) if mth == "preflight")
    assert last_preflight < create_idx
    assert sum(1 for (s, mth) in methods if mth == "preflight") == 3
    # ② 每 job 一次 save_job_result（两个 scope 即两次），各配一次只记它自己的终态写 commit_job_states
    saves = [scope for (s, mth, scope) in calls if mth == "save_job_result"]
    commits = [scope for (s, mth, scope) in calls if mth == "commit_job_states"]
    assert sorted(saves) == ["a", "b"] and sorted(commits) == ["a", "b"]
    # ②b 点名：终态写给出的 JobState 带的就是这个 job 那次保存用的标识，两个 job 的标识不同
    saved = {sid: rid for (side, sid, rid) in named if side == "saved"}
    committed = {sid: rid for (side, sid, rid) in named if side == "committed"}
    assert committed == saved and len(set(saved.values())) == 2 and None not in saved.values()
    # ③ 逐 job 的提交点：明细先存、这个 job 的终态写紧跟其后，中间没有别的写
    for scope in ("a", "b"):
        si = calls.index(("result", "save_job_result", scope))
        assert calls[si + 1] == ("run", "commit_job_states", scope)
    # ④ 最后一个 job 的终态写使 run 成为终态：之后不再做结束写；为组装汇总读一次运行态，再按其中点名的标识逐个读回明细
    assert ("run", "end_run") not in methods
    last_commit = max(i for i, (s, mth) in enumerate(methods) if mth == "commit_job_states")
    read_idx = methods.index(("run", "load_run_state"))
    assert last_commit < read_idx
    assert methods[read_idx + 1:read_idx + 3] == [("result", "load_job_result")] * 2
    assert sorted(rid for (s, mth, rid) in calls if mth == "load_job_result") == sorted(saved.values())
    # ⑤ ReportStore.write 最后（派生、永远最后），紧跟在读回明细之后
    assert methods[-1] == ("report", "write") and read_idx == len(methods) - 4


# ---- 前台 run 建 run 失败：一句说明、退出码 2、不打回溯，不开始执行（ADR 0030 决定七）----
# 与本机后台推进进程同一函数、同一句（`_run_record_failure`）。记录还没有写下、建事件库失败两种另见 test_tunnel_cli。

_FIXED_RUN_ID = "20300102T030405Z-abcdef"


class _RecordingTunnel:
    """登记进 `tunnel.PROVIDERS` 的假隧道服务：只模仿口子的外部表面（前置检查、起隧道、返回对象的 close），记下关闭的次数。"""

    url = "https://t.example.test"

    def __init__(self) -> None:
        self.closes = 0

    def check_prerequisites(self) -> None:
        pass

    def start(self, local_origin, *, closes_at, timeout_s=None):
        from gherkai_runtime import tunnel as gtunnel

        return gtunnel.TunnelInfo(url=self.url, local_origin=gtunnel.normalize_origin(local_origin),
                                  warmup_url=gtunnel.warmup_url_for(self.url, "a" * 32), closer=self._close)

    def _close(self) -> None:
        self.closes += 1


def test_run_on_an_existing_run_exits_2_with_its_own_sentence_and_closes_the_session_at_exit(tmp_path, monkeypatch, capsys):
    """前台 run 建 run 时这个 run 已经存在（报告目录里已有同一标识的运行态）：说「已经存在、没有重新建立」而不是写记录失败，退出码 2、
    不打回溯、不开始执行，已有的运行态不被改动。隧道在建 run 之前已经建成：关闭会话登记在 atexit 上，命令返回时会话仍开着、进程退出时
    关闭（ADR 0035 决策 3「寿命」）。"""
    import atexit

    from gherkai_runtime import tunnel as gtunnel

    service = _RecordingTunnel()
    monkeypatch.setitem(gtunnel.PROVIDERS, "ngrok", lambda: service)
    registered: list = []
    monkeypatch.setattr(atexit, "register", lambda fn, *a, **k: registered.append(fn) or fn)
    monkeypatch.setattr(compose, "new_run_id", lambda at=None: _FIXED_RUN_ID)
    monkeypatch.setattr(m, "schedule", lambda *a, **k: pytest.fail("run 已存在时不该开始执行"))
    reports = tmp_path / "reports"
    existing = reports / _FIXED_RUN_ID / "run_state.json"
    existing.parent.mkdir(parents=True)
    existing.write_text("{}", encoding="utf-8")
    rc = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(reports),
                 "--expose-local", "http://localhost:3000"])
    cap = capsys.readouterr()
    assert rc == 2 and cap.out == ""
    assert f"run {_FIXED_RUN_ID} 已经存在，没有重新建立。请重新执行这条命令。" in cap.err.splitlines()
    assert "写这个 run 的记录失败" not in cap.err and "Traceback" not in cap.err
    assert existing.read_text(encoding="utf-8") == "{}"
    closers = [fn for fn in registered if isinstance(getattr(fn, "__self__", None), gtunnel.TunnelInfo)]
    assert len(closers) == 1 and service.closes == 0
    closers[0]()
    assert service.closes == 1


def test_run_quiet_worker_log_failure_after_the_record_exits_2_and_leaves_the_run_pending(tmp_path, monkeypatch, capsys):
    """前台 run 的记录已写下、`--quiet` 的 worker 日志打不开（日志的位置被一个目录占着）：说明记录已写下、还没有开始执行、停在 pending，
    退出码 2、不打回溯；与本机后台推进进程打不开 reconcile.log 是同一句。日志的位置在真实的建 run 返回之后才被占上：事先在 run 目录里
    放东西，建 run 会因为这个位置已有非空目录而得到「已经存在」。"""
    from gherkai_core.adapters.run_store.local import LocalRunStore

    monkeypatch.setattr(compose, "new_run_id", lambda at=None: _FIXED_RUN_ID)
    monkeypatch.setattr(m, "schedule", lambda *a, **k: pytest.fail("准备执行用的文件失败时不该开始执行"))
    real_build = compose.build_local_stores

    def build_then_block_the_log(**kw):
        stores = real_build(**kw)
        real_create = stores[0].create_run

        def create_then_block(meta, initial_state):
            real_create(meta, initial_state)
            (Path(kw["report_dir"]) / meta.run_id / "worker.log").mkdir()
        stores[0].create_run = create_then_block
        return stores

    monkeypatch.setattr(compose, "build_local_stores", build_then_block_the_log)
    reports = tmp_path / "reports"
    rc = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(reports), "--quiet"])
    cap = capsys.readouterr()
    assert rc == 2 and cap.out == ""
    assert f"run {_FIXED_RUN_ID} 的记录已经写下，但在报告目录 {reports.resolve()} 里准备执行用的文件失败：" in cap.err
    assert "还没有开始执行，这个 run 在记录里停在 pending。" in cap.err and "Traceback" not in cap.err
    assert LocalRunStore(reports).load_run_state(_FIXED_RUN_ID).status == Status.PENDING


# ---- run 被别处结束：本机 run 执行中途另一个写入方结束了这个 run，前台服从记录（ADR 0054 决策五「执行方服从记录」）----
# 得知之后本次判出的结果不写进记录，结束时不覆盖已有的终态、不生成报告，stdout 不输出，退出码 1（处理过中断时按信号取）。

_ENDED_AT = "2026-11-15T00:00:00+00:00"
_SETTLED = RUN_ENDINGS["settle-advancer-exited"]  # 处置「锁拿到了」那一行：另一个写入方用的结束写


def _detail_files(run_dir: Path) -> list[str]:
    """run 目录下全部判定明细文件的标识（文件名去掉扩展名），排序给出；目录不在时为空。端口不提供列举，用例直接看存放处，以确认
    没有多存、也没有漏存。"""
    jobs_dir = run_dir / "jobs"
    return sorted(p.stem for p in jobs_dir.glob("*.json")) if jobs_dir.is_dir() else []


def _schedule_ended_elsewhere(end_it, *, signum=None):
    """假 schedule：第一个 job 完成之后调 end_it(run_id)，模拟另一个写入方在本次执行进行中把这个 run 记为已结束，余下的 job
    照常执行并完成。给了 signum 时另像真 schedule 一样处理一次使用方中断（向本进程发信号、回调 on_interrupt(1)），判定不变。"""
    import signal as _signal

    inner = _fake_schedule_factory()

    def fake_schedule(run_meta, engines, sink, opts=None, on_job_complete=None, on_event=None):
        if signum is not None:
            _signal.raise_signal(signum)
            opts.on_interrupt(1)
        ended: list[str] = []

        def on_complete(jr):
            on_job_complete(jr)
            if not ended:
                ended.append(jr.scope_id)
                end_it(run_meta.run_id)

        return inner(run_meta, engines, sink, opts, on_job_complete=on_complete, on_event=on_event)

    return fake_schedule


def _end_locally(reports: Path):
    """另一个写入方：同一个报告目录上的 run store 以结束写结束这个 run（处置那一行，与处置方用的是同一个写入口）。"""
    from gherkai_core.adapters.run_store.local import LocalRunStore

    def end_it(run_id: str) -> None:
        assert LocalRunStore(reports).end_run(run_id, _SETTLED, ended_at=_ENDED_AT) is True

    return end_it


@pytest.mark.parametrize("flags", [[], ["--json"]], ids=["text", "json"])
def test_run_keeps_the_recorded_end_when_the_run_was_ended_elsewhere(tmp_path, monkeypatch, capsys, flags):
    """本机后端：a 判出结果之后、b 执行之前，run 被别处以结束写结束（b 记 skipped，run 记 aborted 并带说明）。b 的执行中的写写不成，
    前台由此得知 run 已结束：b 判出的结果不存明细、不写终态，结束时不覆盖这条记录、不生成报告；stdout 什么都不输出（结果以记录为准），
    stderr 说明记录里的状态与原因、给出判定明细的落点；退出码 1。"""
    from gherkai_core.adapters.run_store.local import LocalRunStore

    reports = tmp_path / "reports"
    monkeypatch.setattr(m, "schedule", _schedule_ended_elsewhere(_end_locally(reports)))
    rc = m.main(["run", str(_two_scope_feature(tmp_path)), "--report-dir", str(reports), *flags])
    cap = capsys.readouterr()
    assert rc == 1
    assert cap.out == ""
    [run_dir] = [d for d in reports.iterdir() if d.is_dir()]
    run_id = run_dir.name
    assert (f"run {run_id} 在本次执行结束之前已被记为已结束，本次执行没有覆盖这条记录，也没有生成报告。"
            f"记录里的状态为 aborted，原因：{_SETTLED.run_message}。\n") in cap.err
    assert "已得出的判定已写入" not in cap.err
    assert f"判定明细: {compose.local_artifact_locations(str(reports), run_id)['jobs_dir']}" in cap.err
    assert "Traceback" not in cap.err
    # 记录是那次结束写的结果：a 是本次执行先写下的终态并点名了它的明细，b 是结束写记下的 skipped 与说明、不点名；b 判出的结果
    # 没有写进记录，也没有存明细：明细目录里只有 a 被点名的那一份
    state = LocalRunStore(reports).load_run_state(run_id)
    assert (state.status, state.message, state.ended_at) == (Status.ABORTED, _SETTLED.run_message, _ENDED_AT)
    assert {sid: (js.status, js.message) for sid, js in state.jobs.items()} == {
        "a": (Status.PASSED, None), "b": (Status.SKIPPED, _SETTLED.skipped_message)}
    assert state.jobs["a"].result_id is not None and state.jobs["b"].result_id is None
    assert _detail_files(run_dir) == [state.jobs["a"].result_id]
    _rs, result_store, _rp, _mk = compose.build_local_stores(report_dir=str(reports))
    assert result_store.load_job_result(run_id, state.jobs["a"].result_id).scope_id == "a"
    assert not (run_dir / "index.html").exists()


def test_run_ended_elsewhere_without_a_run_level_reason_names_only_the_recorded_status(tmp_path, monkeypatch, capsys):
    """别处使 run 成为终态的写没有带 run 级说明（另一个写入方以终态写记下余下的 job，run 随最后一个 job 的终态成为终态）：说明里只给
    记录里的状态，不留一个空的「原因」。"""
    from gherkai_core.adapters.run_store.local import LocalRunStore

    reports = tmp_path / "reports"

    def end_it(run_id: str) -> None:
        outcome = LocalRunStore(reports).commit_job_states(run_id, [JobState("b", Status.FAILED)], ended_at=_ENDED_AT)
        assert outcome == CommitOutcome.ENDED_RUN

    monkeypatch.setattr(m, "schedule", _schedule_ended_elsewhere(end_it))
    assert m.main(["run", str(_two_scope_feature(tmp_path)), "--report-dir", str(reports), "--quiet"]) == 1
    err = capsys.readouterr().err
    assert "也没有生成报告。记录里的状态为 failed。\n" in err and "原因" not in err


def test_run_ended_elsewhere_after_an_interrupt_exits_by_signal(tmp_path, monkeypatch, capsys):
    """处理过使用方中断、收尾时又发现 run 已被别处记为已结束：退出码仍按信号取（与中断的规则一致），说明照常给出。"""
    import signal as _signal

    reports = tmp_path / "reports"
    monkeypatch.setattr(m, "schedule", _schedule_ended_elsewhere(_end_locally(reports), signum=_signal.SIGTERM))
    assert m.main(["run", str(_two_scope_feature(tmp_path)), "--report-dir", str(reports)]) == 143
    cap = capsys.readouterr()
    assert cap.out == "" and "在本次执行结束之前已被记为已结束" in cap.err


def test_run_ended_elsewhere_exits_by_signal_even_when_the_record_cannot_be_read_back(tmp_path, monkeypatch, capsys):
    """处理过使用方中断、得知 run 已被别处结束之后读回运行态又失败：仍走同一个出口，退出码按信号取（SIGTERM 为 143），
    说明照常给出并写明记录没有读出来，判定明细的落点照常给出；没有未归类的异常。"""
    import signal as _signal

    from gherkai_core.adapters.run_store.local import LocalRunStore

    reports = tmp_path / "reports"
    end_locally = _end_locally(reports)

    def end_it(run_id: str) -> None:
        end_locally(run_id)

        def failing_read(self, rid):
            raise OSError("读取失败")

        monkeypatch.setattr(LocalRunStore, "load_run_state", failing_read)   # 之后的读回失败

    monkeypatch.setattr(m, "schedule", _schedule_ended_elsewhere(end_it, signum=_signal.SIGTERM))
    rc = m.main(["run", str(_two_scope_feature(tmp_path)), "--report-dir", str(reports)])
    cap = capsys.readouterr()
    assert rc == 143 and cap.out == ""
    [run_dir] = [d for d in reports.iterdir() if d.is_dir()]
    assert (f"run {run_dir.name} 在本次执行结束之前已被记为已结束，本次执行没有覆盖这条记录，也没有生成报告。"
            "记录里的状态这一次没有读出来。\n") in cap.err
    assert "判定明细: " in cap.err and "Traceback" not in cap.err


def test_run_ended_elsewhere_before_any_job_result_names_no_detail_location(tmp_path, monkeypatch, capsys):
    """别处在第一个 job 开始执行之前结束了这个 run：每个 job 的执行中的写都写不成，前台由此得知 run 已结束，没有存下任何判定明细，
    判定明细的目录没有建出来。stderr 照常说明记录里的状态与原因，不给判定明细的落点（不指向不存在的位置）；stdout 什么都不输出，
    退出码 1。"""
    reports = tmp_path / "reports"
    end_locally = _end_locally(reports)
    inner = _fake_schedule_factory()

    def fake_schedule(run_meta, engines, sink, opts=None, on_job_complete=None, on_event=None):
        end_locally(run_meta.run_id)
        return inner(run_meta, engines, sink, opts, on_job_complete=on_job_complete, on_event=on_event)

    monkeypatch.setattr(m, "schedule", fake_schedule)
    rc = m.main(["run", str(_two_scope_feature(tmp_path)), "--report-dir", str(reports)])
    cap = capsys.readouterr()
    assert rc == 1 and cap.out == ""
    [run_dir] = [d for d in reports.iterdir() if d.is_dir()]
    assert not (run_dir / "jobs").exists()
    assert (f"run {run_dir.name} 在本次执行结束之前已被记为已结束，本次执行没有覆盖这条记录，也没有生成报告。"
            f"记录里的状态为 aborted，原因：{_SETTLED.run_message}。\n") in cap.err
    assert "判定明细: " not in cap.err and "Traceback" not in cap.err


@pytest.mark.parametrize("signum, expected", [(None, 1), ("SIGTERM", 143)], ids=["no-interrupt", "after-sigterm"])
def test_run_ended_elsewhere_exit_survives_a_failing_look_at_the_details_directory(tmp_path, monkeypatch, capsys, signum,
                                                                                    expected):
    """run 被别处结束的出口里，看判定明细的目录在不在的那一次探测失败（目录已不可访问）：只是少打「判定明细」一行，说明照常给出，
    不打回溯；退出码仍是 1，调度循环处理过 SIGTERM 时仍是 143。"""
    import signal as _signal

    reports = tmp_path / "reports"
    end_locally = _end_locally(reports)
    real_is_dir = Path.is_dir

    def failing_is_dir(self):
        if self.name == "jobs":
            raise PermissionError(13, "Permission denied")
        return real_is_dir(self)

    def end_it(run_id: str) -> None:
        end_locally(run_id)
        monkeypatch.setattr(Path, "is_dir", failing_is_dir)  # 之后对明细目录的探测失败

    monkeypatch.setattr(m, "schedule",
                        _schedule_ended_elsewhere(end_it, signum=getattr(_signal, signum) if signum else None))
    rc = m.main(["run", str(_two_scope_feature(tmp_path)), "--report-dir", str(reports)])
    cap = capsys.readouterr()
    assert rc == expected and cap.out == ""
    assert "在本次执行结束之前已被记为已结束" in cap.err
    assert "判定明细: " not in cap.err and "Traceback" not in cap.err


def test_interrupt_arriving_during_the_wrap_up_does_not_cut_the_output_short(tmp_path, monkeypatch, capsys):
    """`schedule` 返回之后、收尾期间才到的 SIGINT：只置标志的处理器仍在，这次中断不打断结束写、读回运行态、生成报告与输出；全部 job
    已完成，调度循环没有处置过中断，退出码按 run 的状态取。命令结束之后信号的处置恢复原状。"""
    import signal as _signal

    from gherkai_core.persist import RunPersistence

    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    real_finalize = RunPersistence.finalize

    def finalize_after_a_late_interrupt(self, execution):
        _signal.raise_signal(_signal.SIGINT)
        return real_finalize(self, execution)

    monkeypatch.setattr(RunPersistence, "finalize", finalize_after_a_late_interrupt)
    before = _signal.getsignal(_signal.SIGINT)
    reports = tmp_path / "reports"
    rc = m.main(["run", str(_two_scope_feature(tmp_path)), "--report-dir", str(reports), "--json"])
    cap = capsys.readouterr()
    assert rc == 0
    assert json.loads(cap.out)["status"] == "passed"
    [run_dir] = [d for d in reports.iterdir() if d.is_dir()]
    assert (run_dir / "index.html").exists()
    assert _signal.getsignal(_signal.SIGINT) is before


# ---- 前台执行遵守运行期限、服从记录：组合根的注入与到期结束的输出 ----
# 到期时被期限截断的 job 记 aborted，没有启动的 job 由结束写记 skipped 并带到期的说明，run 随之为 aborted（ADR 0054 决策二「各执行方
# 的落实」前台执行条）；run 被别处结束时服从记录（ADR 0054 决策五）。

def test_run_injects_the_wall_clock_and_the_record_into_schedule(tmp_path, monkeypatch, capsys):
    """前台 run 交给调度循环与落库服务的墙钟是组合根写时间戳的同一个读取点 `compose.now`；有记录时，认领、重试之前的读与停手信号由
    这次 run 的落库服务提供，`--no-report` 没有记录、只注入墙钟。"""
    from gherkai_core.persist import RunPersistence

    box = {}
    clocks = []

    def spy_persistence(*a, **kw):
        clocks.append(kw.get("clock"))
        return RunPersistence(*a, **kw)

    monkeypatch.setattr(m, "RunPersistence", spy_persistence)
    monkeypatch.setattr(m, "schedule", _capturing_schedule(Status.PASSED, box))
    assert m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(tmp_path / "reports")]) == 0
    assert box["opts"].wall_clock is compose.now and clocks == [compose.now]
    assert isinstance(box["opts"].record, RunPersistence)
    assert m.main(["run", str(_write_feature(tmp_path)), "--no-report"]) == 0
    assert box["opts"].wall_clock is compose.now and box["opts"].record is None


class _WallClock:
    """可拨的墙钟，替换组合根的 `compose.now`：建 run 的时刻（从而运行期限）、认领时刻与各次比较都取它。"""

    def __init__(self, start):
        self.t = start

    def __call__(self):
        return self.t


class _StopHandle:
    def __init__(self) -> None:
        import threading

        self.stopped = threading.Event()

    def stop(self, grace_period_s: float) -> None:
        self.stopped.set()


class _ScriptedEngine:
    """进程内的假引擎：scope_id → script(job, handle) 给出事件流。`started` 记下被起过的 scope；没有脚本的 scope 被起即抛
    KeyError（按起 worker 失败记 error），用例据此看出不该启动的 job 是否被启动了。"""

    def __init__(self, scripts) -> None:
        self.scripts = scripts
        self.started: list[str] = []

    def run_scope(self, job):
        self.started.append(job.scope_id)
        handle = _StopHandle()
        return handle, self.scripts[job.scope_id](job, handle)


def _real_schedule_with(monkeypatch, engine, *, before=None):
    """真 schedule、假引擎：两个引擎名都解析到 engine。before(run_meta) 在调度开始之前调用（拨墙钟或记下 run_id）。"""
    real = m.schedule
    monkeypatch.setattr(m.compose, "build_engines", lambda **kw: {"novaact": engine, "midscene": engine})

    def wrapped(run_meta, *a, **kw):
        if before is not None:
            before(run_meta)
        return real(run_meta, *a, **kw)

    monkeypatch.setattr(m, "schedule", wrapped)


_T0 = __import__("datetime").datetime(2026, 11, 15, tzinfo=__import__("datetime").timezone.utc)


def _deadline_mid_run(monkeypatch):
    """两个 scope（a、b）、并发 1，执行中途到达运行期限。期限是建 run 的时刻加 900 秒、再加两个 job 各自的预算 300 秒与尾段
    2 × 150 + 10 秒，即 T0 + 2120 秒（停止宽限取假 worker 自报的 150 秒）。调度开始时墙钟拨到 T0 + 1900：认领 a 的时刻加预算晚于期限，
    a 的截止时刻就是期限；a 起来之后墙钟越过期限，a 按超时停下，b 起 worker 之前已过停止启动的时刻（期限减 60 秒），不启动。
    返回（墙钟，引擎）。"""
    from datetime import timedelta

    from gherkai_core.model import ScenarioStarted, ScopeStarted

    clock = _WallClock(_T0)
    monkeypatch.setattr(m.compose, "now", clock)

    def script_a(job, handle):
        yield ScopeStarted(scope_id=job.scope_id)
        clock.t = _T0 + timedelta(seconds=2121)
        yield ScenarioStarted(scenario_id=job.scenarios[0].id)  # 越过期限之后的第一个事件：调度循环据此停下 a
        handle.stopped.wait(5)

    engine = _ScriptedEngine({"a": script_a})
    _real_schedule_with(monkeypatch, engine, before=lambda meta: setattr(clock, "t", _T0 + timedelta(seconds=1900)))
    return clock, engine


_PAST_DEADLINE = RUN_ENDINGS["deadline"]  # 执行方自己到期的结束写那一行


@pytest.mark.parametrize("flags", [[], ["--json"]], ids=["text", "json"])
def test_run_past_the_deadline_ends_as_aborted_with_the_run_message(tmp_path, monkeypatch, capsys, flags):
    """执行中途到达运行期限（真 schedule、真本机存储）：执行中的 a 被期限截断、记 aborted（说明是期限那一句、没有归因），排队的 b 不启动，
    由结束写记 skipped 并带到期的说明，run 随之为 aborted 并带 run 级说明；记录、报告与 stdout 都是这一份，退出码 1。b 没有判定明细；
    文本汇总与报告把它排在 a 之后、给出状态与说明，`--json` 的 jobs[] 按运行定义的次序列出两个 job。认领时刻随认领写下，之后两次 job
    状态写都保留它。"""
    from gherkai_core.adapters.run_store.local import LocalRunStore
    from gherkai_core.project import DEADLINE_TIMEOUT_MESSAGE
    from gherkai_core.serialize import instant_to_iso
    from datetime import timedelta

    _clock, engine = _deadline_mid_run(monkeypatch)
    reports = tmp_path / "reports"
    rc = m.main(["run", str(_two_scope_feature(tmp_path)), "--report-dir", str(reports), "--max-concurrency", "1", *flags])
    cap = capsys.readouterr()
    assert rc == 1 and engine.started == ["a"], cap.err
    [run_dir] = [d for d in reports.iterdir() if d.is_dir()]
    state = LocalRunStore(reports).load_run_state(run_dir.name)
    assert (state.status, state.message) == (Status.ABORTED, _PAST_DEADLINE.run_message)
    assert {sid: (js.status, js.message) for sid, js in state.jobs.items()} == {
        "a": (Status.ABORTED, None), "b": (Status.SKIPPED, _PAST_DEADLINE.skipped_message)}
    assert state.jobs["a"].claimed_at == instant_to_iso(_T0 + timedelta(seconds=1900)) and state.jobs["b"].claimed_at is None
    assert state.claim_count == 1
    # a 的终态点名了它的明细，那也是明细目录里唯一的一份；b 由结束写结束，不点名
    assert state.jobs["b"].result_id is None and _detail_files(run_dir) == [state.jobs["a"].result_id]
    _rs, result_store, _rp, _mk = compose.build_local_stores(report_dir=str(reports))
    jr = result_store.load_job_result(run_dir.name, state.jobs["a"].result_id)
    assert (jr.scope_id, jr.status, jr.error_type, jr.message) == ("a", Status.ABORTED, None, DEADLINE_TIMEOUT_MESSAGE)
    page = (run_dir / "index.html").read_text(encoding="utf-8")
    assert f"说明: {_PAST_DEADLINE.run_message}" in page and "<code>b</code> <b>skipped</b>" in page
    assert _PAST_DEADLINE.skipped_message in page
    if flags:
        doc = json.loads(cap.out)
        assert (doc["status"], doc["message"]) == ("aborted", _PAST_DEADLINE.run_message)
        assert [(j["scope_id"], j["status"]) for j in doc["jobs"]] == [("a", "aborted"), ("b", "skipped")]
        assert doc["jobs"][1] == {"scope_id": "b", "status": "skipped", "message": _PAST_DEADLINE.skipped_message}
        assert doc["jobs"][0]["error_type"] is None and doc["jobs"][0]["message"] == DEADLINE_TIMEOUT_MESSAGE
        assert doc["run_meta"]["deadline_at"] == instant_to_iso(_T0 + timedelta(seconds=2120))
    else:
        assert "总状态: aborted" in cap.out and f"说明: {_PAST_DEADLINE.run_message}" in cap.out
        assert f"job 'a': aborted  ({DEADLINE_TIMEOUT_MESSAGE})" in cap.out
        assert f"job 'b': skipped  ({_PAST_DEADLINE.skipped_message})" in cap.out
    assert "报告: " in cap.err


def test_run_no_report_obeys_the_deadline_and_shows_it_only_in_the_result(tmp_path, monkeypatch, capsys):
    """`--no-report` 没有记录、没有认领：同样在期限停下执行中的 job、不启动排队的 job；结果按同一套规则在内存里算出（a aborted、
    b skipped 加到期的说明、run aborted 加 run 级说明），与有记录时相同，什么都不落盘，退出码 1。"""
    _clock, engine = _deadline_mid_run(monkeypatch)
    monkeypatch.setattr(m.compose, "build_local_stores", lambda **kw: pytest.fail("--no-report 不该装配任何 store"))
    reports = tmp_path / "reports"
    rc = m.main(["run", str(_two_scope_feature(tmp_path)), "--no-report", "--report-dir", str(reports),
                 "--max-concurrency", "1", "--json"])
    doc = json.loads(capsys.readouterr().out)
    assert rc == 1 and engine.started == ["a"] and not reports.exists()
    assert (doc["status"], doc["message"]) == ("aborted", _PAST_DEADLINE.run_message) and "artifacts" not in doc
    assert [(j["scope_id"], j["status"]) for j in doc["jobs"]] == [("a", "aborted"), ("b", "skipped")]
    assert doc["jobs"][0]["error_type"] is None
    assert doc["jobs"][1] == {"scope_id": "b", "status": "skipped", "message": _PAST_DEADLINE.skipped_message}


def test_run_past_the_deadline_after_an_interrupt_exits_by_signal(tmp_path, monkeypatch, capsys):
    """到期之后又处理过使用方中断：没有启动的 job 由到期那一行的结束写记下（来路取最先登记的那一条），记录与输出都是这一份，
    退出码按信号取。"""
    import signal as _signal

    from gherkai_core.adapters.run_store.local import LocalRunStore

    def fake_schedule(run_meta, engines, sink, opts=None, on_job_complete=None, on_event=None):
        _signal.raise_signal(_signal.SIGINT)
        assert opts.interrupt() == 1
        opts.on_interrupt(1)
        first = JobResult(job=run_meta.jobs[0], status=Status.ERROR, error_type="timeout", message="job 超时")
        on_job_complete(first)
        return _execution(run_meta, [first], stopped_by="deadline")

    monkeypatch.setattr(m, "schedule", fake_schedule)
    reports = tmp_path / "reports"
    assert m.main(["run", str(_two_scope_feature(tmp_path)), "--report-dir", str(reports)]) == 130
    out = capsys.readouterr().out
    assert f"说明: {_PAST_DEADLINE.run_message}" in out and f"job 'b': skipped  ({_PAST_DEADLINE.skipped_message})" in out
    [run_dir] = [d for d in reports.iterdir() if d.is_dir()]
    state = LocalRunStore(reports).load_run_state(run_dir.name)
    assert (state.status, state.message, state.jobs["b"].status) == (Status.ERROR, _PAST_DEADLINE.run_message, Status.SKIPPED)


def test_run_stops_when_another_writer_ends_the_run_mid_execution(tmp_path, monkeypatch, capsys):
    """真 schedule、真本机存储：a 执行中另一个写入方以结束写结束了这个 run（a 记 aborted、b 记 skipped，各带处置那一行的说明）。
    a 的下一次 job 状态写得知 run 已结束，调度循环停下 a、b 不启动；a 停下之后的结果不存明细、不写终态，记录保持那次结束写的结果；
    收尾不覆盖记录、不生成报告，stdout 为空，退出码 1。"""
    from gherkai_core.adapters.run_store.local import LocalRunStore
    from gherkai_core.model import ScopeStarted

    reports = tmp_path / "reports"
    box = {}

    def script_a(job, handle):
        assert LocalRunStore(reports).end_run(box["run_id"], _SETTLED, ended_at=_ENDED_AT) is True
        yield ScopeStarted(scope_id=job.scope_id)  # 这次 job 状态写落在 run 已结束之后
        handle.stopped.wait(5)

    engine = _ScriptedEngine({"a": script_a})
    _real_schedule_with(monkeypatch, engine, before=lambda meta: box.update(run_id=meta.run_id))
    rc = m.main(["run", str(_two_scope_feature(tmp_path)), "--report-dir", str(reports), "--max-concurrency", "1", "--json"])
    cap = capsys.readouterr()
    assert rc == 1 and cap.out == "" and engine.started == ["a"], cap.err
    assert "在本次执行结束之前已被记为已结束" in cap.err
    state = LocalRunStore(reports).load_run_state(box["run_id"])
    assert (state.status, state.message, state.ended_at) == (Status.ABORTED, _SETTLED.run_message, _ENDED_AT)
    assert {sid: (js.status, js.message) for sid, js in state.jobs.items()} == {
        "a": (Status.ABORTED, _SETTLED.aborted_message), "b": (Status.SKIPPED, _SETTLED.skipped_message)}
    assert all(js.result_id is None for js in state.jobs.values()) and _detail_files(reports / box["run_id"]) == []
    assert not (reports / box["run_id"] / "index.html").exists()


def _three_scope_feature(tmp_path: Path) -> Path:
    feat = tmp_path / "three.feature"
    feat.write_text(
        "Feature: F\n"
        "  @scope:a\n  Scenario: sa\n    When \"x\"\n"
        "  @scope:b\n  Scenario: sb\n    When \"y\"\n"
        "  @scope:c\n  Scenario: sc\n    When \"z\"\n",
        encoding="utf-8",
    )
    return feat


def test_run_json_lists_every_job_in_definition_order_after_fail_fast(tmp_path, monkeypatch, capsys):
    """真 schedule、真本机存储，fail-fast、并发 1：a 起 worker 失败记 error，b、c 没有启动，由 fail-fast 那一行的结束写记 skipped；
    `--json` 的 jobs[] 按运行定义的次序列出全部 job（ADR 0041 决策三），没有判定明细的项只有 scope_id、status 与 message；
    判定明细只有 a 一份，退出码 1。"""
    fail_fast = RUN_ENDINGS["fail-fast"]
    engine = _ScriptedEngine({})  # 没有脚本：每个被起的 scope 都按起 worker 失败记 error
    _real_schedule_with(monkeypatch, engine)
    reports = tmp_path / "reports"
    rc = m.main(["run", str(_three_scope_feature(tmp_path)), "--report-dir", str(reports), "--max-concurrency", "1",
                 "--fail-fast", "--json"])
    cap = capsys.readouterr()
    assert rc == 1 and engine.started == ["a"], cap.err
    doc = json.loads(cap.out)
    assert (doc["status"], doc["message"]) == ("error", fail_fast.run_message)
    assert [(j["scope_id"], j["status"]) for j in doc["jobs"]] == [("a", "error"), ("b", "skipped"), ("c", "skipped")]
    assert doc["jobs"][1:] == [{"scope_id": sid, "status": "skipped", "message": fail_fast.skipped_message} for sid in ("b", "c")]
    from gherkai_core.adapters.run_store.local import LocalRunStore
    [run_dir] = [d for d in reports.iterdir() if d.is_dir()]
    state = LocalRunStore(reports).load_run_state(run_dir.name)
    assert [sid for sid, js in state.jobs.items() if js.result_id is not None] == ["a"]
    assert _detail_files(run_dir) == [state.jobs["a"].result_id]


def test_run_exit_code_and_output_take_the_run_status_from_the_record(tmp_path, monkeypatch, capsys):
    """退出码与输出里的 run 状态取自记录（ADR 0031 决定五「数据源」）：判出结果的 job 全部通过，而另一个 job 因到期没有启动、由结束写
    记 skipped，记录里的 run 为 aborted，退出码 1。`--no-report` 没有记录，按同一套规则在内存里算出，JSON 里 run 与各 job 的状态、
    说明与有记录时相同。"""
    from gherkai_core.adapters.run_store.local import LocalRunStore

    def fake_schedule(run_meta, engines, sink, opts=None, on_job_complete=None, on_event=None):
        first = JobResult(job=run_meta.jobs[0], status=Status.PASSED)
        if on_job_complete is not None:
            on_job_complete(first)
        return _execution(run_meta, [first], stopped_by="deadline")

    monkeypatch.setattr(m, "schedule", fake_schedule)
    feat = str(_two_scope_feature(tmp_path))
    reports = tmp_path / "reports"
    assert m.main(["run", feat, "--report-dir", str(reports), "--json"]) == 1
    recorded = json.loads(capsys.readouterr().out)
    [run_dir] = [d for d in reports.iterdir() if d.is_dir()]
    assert recorded["status"] == LocalRunStore(reports).load_run_state(run_dir.name).status.value == "aborted"
    assert m.main(["run", feat, "--no-report", "--json"]) == 1
    in_memory = json.loads(capsys.readouterr().out)

    def outcome(doc):
        return doc["status"], doc["message"], [(j["scope_id"], j["status"], j.get("message")) for j in doc["jobs"]]

    assert outcome(in_memory) == outcome(recorded) == (
        "aborted", _PAST_DEADLINE.run_message, [("a", "passed", None), ("b", "skipped", _PAST_DEADLINE.skipped_message)])


def _disk_full(*_a, **_kw):
    raise OSError(28, "No space left on device")


def _no_wait_save_retry(monkeypatch) -> list[float]:
    """本机推进器的判定存储照组合根的装配（本机文件存储外面套保存失败的退避重试），只把等待换成不真等待、记下秒数；返回记下的等待。
    磁盘写不进的用例因此不必真等 1、2、4 秒。"""
    from gherkai_core.adapters.result_store.local import LocalResultStore
    from gherkai_core.adapters.result_store.retrying import RetryingResultStore

    waits: list[float] = []
    monkeypatch.setattr(m.compose, "local_result_store",
                        lambda root: RetryingResultStore(LocalResultStore(root), sleep=waits.append))
    return waits


def test_run_storage_failure_mid_run_gives_one_sentence_and_exits_nonzero(tmp_path, monkeypatch, capsys):
    """运行期落库失败（保存判定明细时磁盘一直写不进，ADR 0030 决定七）：保存按 1、2、4 秒退避重试，四次都用同一个标识，仍失败才放弃；
    不打回溯，stderr 一句说明（发生了什么、记录在哪里、怎么办），stdout 为空（`--json` 也是），退出码 1；这个 job 在记录里留在
    running、不点名，没有存下任何明细，不生成报告。"""
    from gherkai_core.adapters.result_store.local import LocalResultStore
    from gherkai_core.adapters.run_store.local import LocalRunStore

    waits = _no_wait_save_retry(monkeypatch)
    attempts: list[str] = []

    def disk_full(self, run_id, result_id, job):
        attempts.append(result_id)
        _disk_full()

    monkeypatch.setattr(LocalResultStore, "save_job_result", disk_full)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    reports = tmp_path / "reports"
    rc = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(reports), "--json"])
    cap = capsys.readouterr()
    assert rc == 1 and cap.out == "" and "Traceback" not in cap.err
    assert waits == [1.0, 2.0, 4.0] and len(attempts) == 4 and len(set(attempts)) == 1
    [run_dir] = [d for d in reports.iterdir() if d.is_dir()]
    run_id = run_dir.name
    assert f"run {run_id} 读写本机的运行记录失败，执行已停止，没有输出汇总：" in cap.err and "No space left on device" in cap.err
    assert f"记录在 {run_dir.resolve()}" in cap.err and f"gherkai status {run_id} --report-dir {reports}" in cap.err
    assert "磁盘的剩余空间与读写权限" in cap.err and "然后重新执行" in cap.err and "不必重新执行" not in cap.err
    state = LocalRunStore(reports).load_run_state(run_id)
    assert state.status == Status.RUNNING and [(js.status, js.result_id) for js in state.jobs.values()] == [(Status.RUNNING, None)]
    assert _detail_files(run_dir) == [] and not (run_dir / "index.html").exists()


def test_run_records_the_job_after_one_failed_save_and_names_the_retried_detail(tmp_path, monkeypatch, capsys, caplog):
    """保存判定明细失败一次（磁盘一时写不进）：留一条警告，等 1 秒后用同一个标识再存一次即成，run 照常通过、退出码 0；终态点名的
    就是重试所用的标识，明细目录里只有这一份，`--json` 的结果出自读回的那一份。"""
    import logging

    from gherkai_core.adapters.result_store.local import LocalResultStore
    from gherkai_core.adapters.run_store.local import LocalRunStore

    waits = _no_wait_save_retry(monkeypatch)
    attempts: list[str] = []
    real_save = LocalResultStore.save_job_result

    def fail_once(self, run_id, result_id, job):
        attempts.append(result_id)
        if len(attempts) == 1:
            _disk_full()
        real_save(self, run_id, result_id, job)

    monkeypatch.setattr(LocalResultStore, "save_job_result", fail_once)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    reports = tmp_path / "reports"
    with caplog.at_level(logging.WARNING):
        rc = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(reports), "--json"])
    cap = capsys.readouterr()
    assert rc == 0 and json.loads(cap.out)["status"] == "passed", cap.err
    assert waits == [1.0] and len(attempts) == 2 and attempts[0] == attempts[1]
    assert [r.levelno for r in caplog.records if r.name.endswith("result_store.retrying")] == [logging.WARNING]
    [run_dir] = [d for d in reports.iterdir() if d.is_dir()]
    [js] = LocalRunStore(reports).load_run_state(run_dir.name).jobs.values()
    assert (js.status, js.result_id) == (Status.PASSED, attempts[0])
    assert _detail_files(run_dir) == [attempts[0]]


def test_run_storage_failure_after_an_interrupt_exits_by_signal(tmp_path, monkeypatch, capsys):
    """处理过使用方中断之后遇到运行期落库失败：说明照常给出，退出码仍按信号取（SIGTERM 为 143）。"""
    import signal as _signal

    from gherkai_core.adapters.result_store.local import LocalResultStore

    inner = _fake_schedule_factory()

    def fake_schedule(run_meta, engines, sink, opts=None, on_job_complete=None, on_event=None):
        _signal.raise_signal(_signal.SIGTERM)
        opts.on_interrupt(1)
        return inner(run_meta, engines, sink, opts, on_job_complete=on_job_complete, on_event=on_event)

    waits = _no_wait_save_retry(monkeypatch)
    monkeypatch.setattr(LocalResultStore, "save_job_result", _disk_full)
    monkeypatch.setattr(m, "schedule", fake_schedule)
    rc = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(tmp_path / "reports")])
    cap = capsys.readouterr()
    assert rc == 143 and cap.out == "" and "读写本机的运行记录失败" in cap.err and "Traceback" not in cap.err
    assert waits == [1.0, 2.0, 4.0]  # 处理过中断也照常重试完（处理器只记标志）


def test_run_interrupt_during_a_save_retry_that_fails_exits_by_the_storage_failure(tmp_path, monkeypatch, capsys):
    """保存明细的退避重试期间收到中断、重试仍用尽：调度循环没有机会处置这次中断（存储异常从落库回调冒出 schedule，这一点由 core
    的 schedule 测试核对），CLI 不打中断提示，退出码按运行期落库失败取 1、不按信号取（ADR 0030 决定三「前台在锁内重试」条的代价）。
    先后由构造固定：信号在第一次保存尝试里发出。"""
    import signal as _signal

    from gherkai_core.adapters.result_store.local import LocalResultStore

    attempts: list[str] = []

    def signal_then_disk_full(self, run_id, result_id, job):
        attempts.append(result_id)
        if len(attempts) == 1:
            _signal.raise_signal(_signal.SIGINT)
        _disk_full()

    waits = _no_wait_save_retry(monkeypatch)
    monkeypatch.setattr(LocalResultStore, "save_job_result", signal_then_disk_full)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())  # 像真 schedule 一样：落库回调抛出时不调 on_interrupt
    rc = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(tmp_path / "reports")])
    cap = capsys.readouterr()
    assert rc == 1 and cap.out == "" and "Traceback" not in cap.err
    assert "读写本机的运行记录失败" in cap.err and "收到中断信号" not in cap.err
    assert waits == [1.0, 2.0, 4.0] and len(attempts) == 4  # 中断不打断重试（处理器只记标志）


def test_run_named_detail_missing_at_wrap_up_takes_the_storage_failure_exit(tmp_path, monkeypatch, capsys):
    """本进程的终态写使 run 成为终态之后，收尾按运行态点名的标识读回明细，那一份却读不到（存放处被外部删改）：按记录残缺处理，与读回
    运行态失败同一出口（一句说明、不打回溯、stdout 为空、退出码 1），说明里写明是哪个 job 的明细读不到、记录已是最终状态、不必重新
    执行；不把这个 job 当作没有明细来输出汇总，也不生成报告。"""
    from gherkai_core.adapters.result_store.local import LocalResultStore
    from gherkai_core.adapters.run_store.local import LocalRunStore

    monkeypatch.setattr(LocalResultStore, "load_job_result", lambda self, run_id, result_id: None)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    reports = tmp_path / "reports"
    rc = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(reports), "--json"])
    cap = capsys.readouterr()
    assert rc == 1 and cap.out == "" and "Traceback" not in cap.err
    [run_dir] = [d for d in reports.iterdir() if d.is_dir()]
    run_id = run_dir.name
    [js] = LocalRunStore(reports).load_run_state(run_id).jobs.values()
    assert js.status == Status.PASSED and js.result_id is not None
    assert f"run {run_id} 已结束，结果已写进本机的运行记录，但读回运行记录失败" in cap.err
    assert f"job {js.scope_id} 的判定明细读不到" in cap.err and "不必重新执行" in cap.err
    assert not (run_dir / "index.html").exists()


def test_run_read_back_failure_after_the_run_ended_takes_the_storage_failure_exit(tmp_path, monkeypatch, capsys):
    """本进程的终态写使 run 成为终态之后，为组装汇总而读运行态失败：这次读不在报告的失败隔离之内，与运行期落库失败同一出口
    （一句说明、不打回溯、stdout 为空、退出码 1），不生成报告；记录已是终态。说明与执行中途的失败不同：写明记录已是最终状态、
    用 status 查看、不必重新执行，不说执行中的 job 仍为 running。"""
    from gherkai_core.adapters.run_store.local import LocalRunStore

    real_read = LocalRunStore.load_run_state
    monkeypatch.setattr(LocalRunStore, "load_run_state", _disk_full)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    reports = tmp_path / "reports"
    rc = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(reports)])
    cap = capsys.readouterr()
    assert rc == 1 and cap.out == "" and "Traceback" not in cap.err
    [run_dir] = [d for d in reports.iterdir() if d.is_dir()]
    run_id = run_dir.name
    assert f"run {run_id} 已结束，结果已写进本机的运行记录，但读回运行记录失败，没有输出汇总，也没有生成报告：" in cap.err
    assert "No space left on device" in cap.err and f"记录在 {run_dir.resolve()}，已是这个 run 的最终状态" in cap.err
    assert f"gherkai status {run_id} --report-dir {reports}" in cap.err and "不必重新执行" in cap.err
    assert "仍为 running" not in cap.err and "然后重新执行" not in cap.err
    assert real_read(LocalRunStore(reports), run_id).status == Status.PASSED
    assert not (run_dir / "index.html").exists()


def test_no_report_skips_persistence_entirely(tmp_path, monkeypatch, capsys):
    # --no-report：persistence=None，store 装配一次都不该被调（零落盘运行路径）
    constructed = {"n": 0}
    def boom(**kwargs):
        constructed["n"] += 1
        raise AssertionError("--no-report 不该装配任何 store")
    monkeypatch.setattr(m.compose, "build_local_stores", boom)
    monkeypatch.setattr(m.compose, "build_cloud_stores", boom)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    rc = m.main(["run", str(_write_feature(tmp_path)), "--no-report"])
    assert rc == 0
    assert constructed["n"] == 0


def test_run_state_shows_running_then_final(tmp_path, monkeypatch, capsys):
    # 实时写真效果（用真 LocalRunStore）：ScopeStarted 刷 RUNNING + 血缘随首事件落。
    # fake schedule 先发 ScopeStarted（带 session_id）→ persistence 刷 RUNNING；再 on_job_complete 刷终态。
    from gherkai_core.model import ScopeStarted
    from gherkai_core.adapters.run_store.local import LocalRunStore

    def fake_schedule(run_meta, engines, sink, opts=None, on_job_complete=None, on_event=None):
        results = []
        for j in run_meta.jobs:
            ev = ScopeStarted(scope_id=j.scope_id, session_id="sess-xyz")
            sink(ev)
            if on_event:
                on_event(ev)  # 旁路观察者：persistence 刷 RUNNING + 血缘
            jr = JobResult(job=j, status=Status.PASSED, session_id="sess-xyz")
            results.append(jr)
            if on_job_complete:
                on_job_complete(jr)
        return _execution(run_meta, results)

    monkeypatch.setattr(m, "schedule", fake_schedule)
    report_dir = tmp_path / "r"
    rc = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(report_dir), "--quiet"])
    assert rc == 0
    # 落库后读 run_state：终态 passed，血缘已落（首事件即捕获）
    run_dir = next((report_dir).iterdir())
    state = LocalRunStore(report_dir).load_run_state(run_dir.name)
    assert state is not None and state.status == Status.PASSED
    js = next(iter(state.jobs.values()))
    assert js.status == Status.PASSED and js.session_id == "sess-xyz"


def test_run_wires_artifact_dirs_to_build_engines(tmp_path, monkeypatch, capsys):
    # fail-fast 护栏（ADR 0027 产物归位）：固定住 __main__ 把两引擎产物落点算成 <report_dir>/<run_id>/<engine-dir>
    # 并传给 build_engines。防止将来改坏 __main__ 那几行接线（否则产物落错地方，只有在真实 AWS 上运行才发现）。
    box = {}
    real_build = m.compose.build_engines

    def spy_build(**kwargs):
        box["kwargs"] = kwargs
        return real_build(run_id=kwargs["run_id"])  # 只转发必给的 run id、不带落点：拿真 engines（cmd 正确），落点断言看 box

    monkeypatch.setattr(m.compose, "build_engines", spy_build)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    report_dir = tmp_path / "reports"
    rc = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(report_dir)])
    assert rc == 0

    nova = box["kwargs"]["nova_logs_dir"]
    mid = box["kwargs"]["midscene_run_dir"]
    # 落点是 <report_dir 绝对化>/<run_id>/<engine 子目录>，两引擎对称、run_id 一致
    assert nova is not None and mid is not None
    assert str(nova).endswith("/nova-trajectories") and str(mid).endswith("/midscene-run")
    assert Path(nova).parent == Path(mid).parent          # 同一 <report_dir>/<run_id> 下
    assert Path(mid).parent.parent == report_dir.resolve()  # 绝对化的 report_dir（避 worker cwd 歧义）
    # 本 run 的 id 一并交给 build_engines（经 env RUN_ID 注给 worker，编码会话名的 run 段，ADR 0024「run_id + scope_id 注入
    # worker」条）：与落点目录名同一个值。缺了它两个 worker 都在建会话前以 1 退出，本机后端的每个 run 都失败。
    assert box["kwargs"]["run_id"] == Path(mid).parent.name


def test_no_report_disables_artifacts_instead_of_tempdir(tmp_path, monkeypatch):
    """`--no-report` 即真不生成（ADR 0037 决策 3）：不注入任何落点、并以 no_artifacts 告知 worker 不产生/不上报
    引擎原生产物——而不是「落系统临时目录」（曾如此、被否）。"""
    box = {}
    real_build = m.compose.build_engines

    def spy_build(**kwargs):
        box.update(kwargs)
        return real_build(run_id=kwargs["run_id"])

    monkeypatch.setattr(m.compose, "build_engines", spy_build)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    m.main(["run", str(_write_feature(tmp_path)), "--no-report"])
    assert box["nova_logs_dir"] is None and box["midscene_run_dir"] is None
    assert box["no_artifacts"] is True
    assert box["run_id"]  # 不落库也照传 run id：会话名的 run 段与是否生成报告无关


def test_report_run_passes_absolute_artifact_dirs_and_no_flag(tmp_path, monkeypatch):
    """对照：默认归集方式落 <report_dir>/<run_id>/ 下的绝对路径、no_artifacts=False。"""
    box = {}
    real_build = m.compose.build_engines

    def spy_build(**kwargs):
        box.update(kwargs)
        return real_build(run_id=kwargs["run_id"])

    monkeypatch.setattr(m.compose, "build_engines", spy_build)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(tmp_path / "reports")])
    nova, mid = Path(box["nova_logs_dir"]), Path(box["midscene_run_dir"])
    assert nova.is_absolute() and nova.parent == mid.parent and nova.parent.parent == (tmp_path / "reports").resolve()
    assert box["no_artifacts"] is False


# ---- _render_status：local/cloud 共享的渲染+提示+退出码（两路一致）----
def _mk_state(status):
    from gherkai_core.model import RunState, JobState
    return RunState(run_id="r", status=status,
                    jobs={"a": JobState("a", status)}, high_water_mark=0)


def _args(wait=False, json_=False):
    from types import SimpleNamespace
    return SimpleNamespace(wait=wait, json=json_, run_id="r")


_LOCS = {"report_index": "file:///tmp/x/r/index.html", "run_meta": "file:///tmp/x/r/run_meta.json",
         "run_state": "file:///tmp/x/r/run_state.json", "jobs_dir": "file:///tmp/x/r/jobs"}


def test_render_status_prints_the_given_hint_only_without_wait_and_json(capsys):
    """调用方算好的提示只在不带 --wait、不是 --json 时打到 stderr；它不改变 stdout 与退出码。不给提示时什么都不打。"""
    hint = "提示：这是调用方算好的一句"
    rc = m._render_status(_mk_state(Status.PENDING), _args(), hint=hint, locations=_LOCS)
    cap = capsys.readouterr()
    assert rc == 0 and cap.err.splitlines() == [hint] and cap.out.splitlines()[0] == "run r: pending"
    for args in (_args(wait=True), _args(json_=True)):
        assert m._render_status(_mk_state(Status.PENDING), args, hint=hint, locations=_LOCS) == 0
        assert hint not in capsys.readouterr().err
    assert m._render_status(_mk_state(Status.PENDING), _args(), locations=_LOCS) == 0
    assert capsys.readouterr().err == ""


def test_render_status_running_no_hint(capsys):
    """running、不给提示 → stderr 为空（未结束不打产物位置）。退出码 0。"""
    rc = m._render_status(_mk_state(Status.RUNNING), _args(), locations=_LOCS)
    assert capsys.readouterr().err == ""
    assert rc == 0


def test_render_status_terminal_no_hint_and_exitcode(capsys):
    """终态：passed→0、其余终态→1（含派生终态 skipped/aborted）。"""
    assert m._render_status(_mk_state(Status.PASSED), _args(), locations=_LOCS) == 0
    assert m._render_status(_mk_state(Status.FAILED), _args(), locations=_LOCS) == 1
    assert m._render_status(_mk_state(Status.ERROR), _args(), locations=_LOCS) == 1
    assert m._render_status(_mk_state(Status.SKIPPED), _args(), locations=_LOCS) == 1
    assert m._render_status(_mk_state(Status.ABORTED), _args(), locations=_LOCS) == 1
    assert "提示" not in capsys.readouterr().err


def test_terminal_status_consumers_use_core_single_source():
    """终态真源不漂移（ADR 0031 决定一·补末条）：三处消费方全引 `gherkai_core.model.TERMINAL_STATUSES`、不各写白名单。

    跨 core/cli/gherkai 三栈的结构性护栏（cli 是唯一同时看得见三者的层）——曾有两份逐字副本，
    新增终态漏改哪份、那份就永远判不到终态（`status --wait` 无限轮询 / 隧道守护进程要等到期限加 300 秒才关闭隧道）。
    """
    from pathlib import Path

    from gherkai_core.model import TERMINAL_STATUSES
    from gherkai_runtime import tunnel_host

    assert m.TERMINAL_STATUSES is TERMINAL_STATUSES
    assert tunnel_host.TERMINAL_STATUSES is TERMINAL_STATUSES
    for mod in (m, tunnel_host):
        src = Path(mod.__file__).read_text(encoding="utf-8")
        # 白名单副本的字面特征（正列终态集）——出现即回归
        assert "Status.PASSED, Status.FAILED" not in src, f"{mod.__name__} 又正列了一份终态白名单"


def test_render_status_shows_run_level_message_in_text_and_json(capsys):
    """run 级消息（ADR 0037 决策 7）：文本在状态行下多一行、--json 多一个键；没有消息时两处都没有。退出码不变（error 仍 1）。"""
    from gherkai_core.model import RunState
    told = RunState(run_id="r", status=Status.ERROR, jobs={}, message="提交记录不能由本后端执行：结构版本 2，本后端认 1")
    assert m._render_status(told, _args(), locations=_LOCS) == 1
    out = capsys.readouterr().out
    assert out.splitlines()[0] == "run r: error" and "message=提交记录不能由本后端执行：结构版本 2，本后端认 1" in out
    assert m._render_status(told, _args(json_=True), locations=_LOCS) == 1
    assert json.loads(capsys.readouterr().out)["message"] == told.message
    assert m._render_status(_mk_state(Status.ERROR), _args(json_=True), locations=_LOCS) == 1
    assert "message" not in json.loads(capsys.readouterr().out)


def test_render_status_json_no_hint(capsys):
    """--json（机读）：给了提示也不打，stderr 为空，stdout 是可解析 JSON。"""
    m._render_status(_mk_state(Status.PENDING), _args(json_=True), hint="提示：x", locations=_LOCS)
    cap = capsys.readouterr()
    assert cap.err == ""
    json.loads(cap.out)  # stdout 是纯 JSON


# ---- list-deterministic（ADR 0036）：按引擎查询确定性能力清单 ----

def test_list_deterministic_text_and_json(monkeypatch, capsys):
    """清单取自能力自述对象的 deterministic_steps 键（ADR 0036「5.」「加键不加入口」），文本与 --json 的形状
    逐字不变——自述对象的其它键（下限/身份位）**不得**漏进输出。"""
    entries = [{"pattern": 'p "(?P<x>[^"]+)"', "description": "断言某事", "example": 'Then p "v"'},
               {"pattern": "^nav$", "description": "只在动作关键字下", "example": "Given nav", "keywords": ["Given", "When"]},
               {"pattern": "^all$", "description": "三个关键字都声明", "example": "Then all", "keywords": ["Given", "When", "Then"]}]
    calls = []
    monkeypatch.setattr(m.compose, "query_capabilities",
                        lambda engine, *, steps_dir=None, timeout_s=60.0: calls.append(engine) or
                        {"schema_version": 2, "engine": engine, "min_grace_s": 150.0, "model_id": "qwen.qwen3-vl-235b-a22b",
                         "targets": [{"device": "desktop", "ui_kinds": ["web"]}], "deterministic_steps": entries})
    assert m.main(["list-deterministic", "--engine", "midscene"]) == 0
    out = capsys.readouterr().out
    assert "断言某事" in out and 'Then p "v"' in out and calls == ["midscene"]
    assert "关键字" in out and "任意" in out  # 条目没有 keywords 声明（旧 worker）→ 显示接受任意关键字
    assert "Given / When" in out  # 声明了子集的条目按声明显示
    assert out.count("任意") == 2  # 没声明的与三个全声明的都显示「任意」
    assert "目标" in out and out.count("桌面网页") == 3  # 条目都没声明 targets → step 级按缺键语义为桌面网页，与 worker 声明的桌面网页取交集后都是桌面网页（ADR 0049 决策 2、3）
    assert "^nav$" in out  # 模式列是复制源、不折行（ADR 0047 标识列）
    assert m.main(["list-deterministic", "--json"]) == 0  # 默认 novaact（对齐 run 缺省）
    doc = json.loads(capsys.readouterr().out)
    desktop = [{"device": "desktop", "ui_kinds": ["web"]}]
    # 每项是 worker 原样条目加 CLI 算出的 available_targets（ADR 0049 决策 6）；不带 min_grace_s 等自述项
    assert doc == {"engine": "novaact", "deterministic_steps": [dict(e, available_targets=desktop) for e in entries]}


def test_list_deterministic_targets_column_intersection_and_unsupported_note(monkeypatch, capsys):
    """目标列（ADR 0049 决策 3、6）：列交集目标、带前提的条目附前提；声明了但该引擎不支持的目标单独注明——那条句柄永远不会被
    这个引擎调用，测试开发要看见；--json 同时保留 worker 原样的 targets 与 CLI 算出的 available_targets，两者分开。"""
    entries = [{"pattern": "a", "description": "跨目标核对", "example": "Then a", "targets": [
                   {"device": "desktop", "ui_kinds": ["web"]},
                   {"device": "android", "ui_kinds": ["web", "app"], "requires": ["web_context"]},
                   {"device": "ios", "ui_kinds": ["app"]}]},
               {"pattern": "b", "description": "只有设备", "example": "Then b", "targets": [{"device": "ios", "ui_kinds": ["web"], "requires": ["foo"]}]}]
    monkeypatch.setattr(m.compose, "query_capabilities",
                        lambda engine, *, steps_dir=None, timeout_s=60.0: {
                            "schema_version": 2, "engine": engine, "min_grace_s": 31.0, "model_id": "m",
                            "targets": [{"device": "desktop", "ui_kinds": ["web"]}, {"device": "android", "ui_kinds": ["web"], "max_session_s": 8880}],
                            "deterministic_steps": entries})
    assert m.main(["list-deterministic", "--engine", "midscene"]) == 0
    out = capsys.readouterr().out
    assert "桌面网页、Android 网页（需要网页上下文）" in out
    assert "声明了「Android 应用（需要网页上下文）、iOS 应用」，此引擎不支持" in out  # 不支持的目标同样带前提
    assert "（此引擎上无可用目标）；声明了「iOS 网页（需要 foo）」，此引擎不支持" in out  # 未知前提原样显示（ADR 0049 决策 1）
    assert m.main(["list-deterministic", "--engine", "midscene", "--json"]) == 0
    doc = json.loads(capsys.readouterr().out)
    assert doc["deterministic_steps"][0]["targets"] == entries[0]["targets"]  # 原样
    assert doc["deterministic_steps"][0]["available_targets"] == [
        {"device": "desktop", "ui_kinds": ["web"]}, {"device": "android", "ui_kinds": ["web"], "requires": ["web_context"]}]
    assert doc["deterministic_steps"][1]["available_targets"] == []


def test_list_deterministic_worker_failure_exits_2(monkeypatch, capsys):
    def boom(engine, *, steps_dir=None, timeout_s=60.0):
        raise RuntimeError("worker 自述失败（退出码 1）：...")

    monkeypatch.setattr(m.compose, "query_capabilities", boom)
    assert m.main(["list-deterministic"]) == 2
    assert "自述失败" in capsys.readouterr().err


# ---- plan 派发标注（ADR 0036 决策 4）----

def _det_feature(tmp_path):
    f = tmp_path / "det.feature"
    f.write_text('Feature: d\n  Scenario: s\n    When "做点啥"\n    Then 页面地址匹配 "x"\n', encoding="utf-8")
    return f


def test_plan_annotates_deterministic_hits(tmp_path, monkeypatch, capsys):
    """plan 标注：worker 自述命中 → 行尾「← 确定性:」；AI step 不标（噪声控制）。"""
    def fake_match(engine, items, steps_dir=None):
        assert all(set(it) == {"keyword", "text"} for it in items), items  # 探针每项带关键字与裸文本（ADR 0036 / 0050 决策 1）
        return [({"pattern": "p", "description": "URL 断言"} if "页面地址" in it["text"] else None) for it in items]

    monkeypatch.setattr(m.compose, "match_deterministic", fake_match)
    assert m.main(["plan", str(_det_feature(tmp_path))]) == 0
    out = capsys.readouterr().out
    assert "← 确定性: URL 断言" in out
    assert out.count("← 确定性") == 1  # AI step 不标


def test_plan_conflict_annotated_and_warned(tmp_path, monkeypatch, capsys):
    """冲突预检（实际运行将 error 的注册表配置错）：行内 ⚠ 标注 + stderr 警告；plan 本体仍 0。"""
    monkeypatch.setattr(m.compose, "match_deterministic",
                        lambda engine, items, steps_dir=None: [{"conflict": ["p1", "p2"]} for _ in items])
    assert m.main(["plan", str(_det_feature(tmp_path))]) == 0
    captured = capsys.readouterr()
    assert "⚠ 命中多条确定性模式" in captured.out
    assert "收紧注册表里的匹配模式" in captured.err


def test_plan_keyword_mismatch_annotated_and_warned(tmp_path, monkeypatch, capsys):
    """命中但关键字不符（ADR 0050 决策 1，典型是 Then 后只写一个地址）：行内 ⚠ 标出接受的关键字 + stderr 警告；plan 本体仍 0。"""
    f = tmp_path / "kw.feature"
    f.write_text('Feature: k\n  Scenario: s\n    Given "https://x"\n    Then "https://x"\n', encoding="utf-8")

    def fake_match(engine, items, steps_dir=None):
        return [({"pattern": "nav", "description": "内建导航"} if it["keyword"] != "Then"
                 else {"keyword_mismatch": "nav", "keywords": ["Given", "When"]}) for it in items]

    monkeypatch.setattr(m.compose, "match_deterministic", fake_match)
    assert m.main(["plan", str(f)]) == 0
    captured = capsys.readouterr()
    assert "← 确定性: 内建导航" in captured.out
    assert "⚠ 写法与关键字不符：这条 step 只在 Given / When 下有意义" in captured.out
    assert "写法与关键字不符" in captured.err
    assert m.main(["plan", str(f), "--json"]) == 0
    steps = json.loads(capsys.readouterr().out)["jobs"][0]["scenarios"][0]["steps"]
    assert steps[1]["deterministic"] == {"keyword_mismatch": "nav", "keywords": ["Given", "When"]}


def test_plan_annotation_degrades_gracefully(tmp_path, monkeypatch, capsys):
    """标注 best-effort：引擎环境未装、查询取不到结果 → 无标注 + stderr 警告，plan 核心输出不受影响。"""
    def boom(engine, items, steps_dir=None):
        raise compose.WorkerUnavailableError(engine, "worker 起不来")

    monkeypatch.setattr(m.compose, "match_deterministic", boom)
    assert m.main(["plan", str(_det_feature(tmp_path))]) == 0
    captured = capsys.readouterr()
    assert "页面地址匹配" in captured.out and "← 确定性" not in captured.out
    assert "标注降级" in captured.err


def test_plan_json_carries_deterministic_field(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(m.compose, "match_deterministic",
                        lambda engine, items, steps_dir=None: [({"pattern": "p", "description": "d"}
                                                                if "页面地址" in it["text"] else None) for it in items])
    assert m.main(["plan", str(_det_feature(tmp_path)), "--json"]) == 0
    doc = json.loads(capsys.readouterr().out)
    steps = doc["jobs"][0]["scenarios"][0]["steps"]
    assert steps[0]["deterministic"] is None
    assert steps[1]["deterministic"] == {"pattern": "p", "description": "d"}


# ---- 引擎名预检（plan 层拦配置错，防延迟到 run 起 job 时才报错）----

def test_unknown_engine_tag_rejected_at_plan(tmp_path, capsys):
    f = tmp_path / "bad.feature"
    f.write_text('Feature: t\n  @engine:midsence\n  Scenario: s\n    When "x"\n', encoding="utf-8")
    assert m.main(["plan", str(f)]) == 2
    err = capsys.readouterr().err
    assert "midsence" in err and "可用" in err


def test_default_engine_flag_has_choices():
    # --default-engine 拼错被 argparse 拦（SystemExit 2，最早拦截点 + 报错自带合法值清单）
    import pytest
    with pytest.raises(SystemExit) as ei:
        m.main(["plan", "x.feature", "--default-engine", "midsence"])
    assert ei.value.code == 2


# ---- max_concurrency 随 definition 走（ADR 0034 机制四）----

def test_submit_local_writes_max_concurrency_into_definition(tmp_path, monkeypatch, inline_children, advanced):
    """submit 把 --max-concurrency 落进 definition（推进器读 meta，不靠 flag 通道）。

    后台推进进程的启动命令里没有这个选项：值随经标准输入交出的输入走，写进后台推进进程生成的运行定义，它推进用的也是这一份。
    推进器与提交进程可能分离（云端后端在 Lambda，本机是另一个后台进程），它们只能从运行定义取到这个值。
    """
    reports = tmp_path / "reports"
    assert m.main(["submit", str(_write_feature(tmp_path)), "--report-dir", str(reports),
                   "--max-concurrency", "3"]) == 0
    inline_children.settle()
    meta = json.loads((_submitted_run_dir(reports) / "run_meta.json").read_text(encoding="utf-8"))
    assert meta["max_concurrency"] == 3
    assert "--max-concurrency" not in inline_children.only().argv
    assert [mt.max_concurrency for mt in advanced] == [3]


def test_version_flag_prints_dist_version(capsys):
    """--version 打印「gherkai <发行版本>」并以退出码 0 结束——版本真源是包元数据（git tag → uv-dynamic-versioning），
    代码内不复制版本号（ADR 0037 决策 2b）。"""
    import pytest

    with pytest.raises(SystemExit) as ei:
        m.main(["--version"])
    assert ei.value.code == 0
    out = capsys.readouterr().out.strip()
    assert out.startswith("gherkai ") and len(out.split()) == 2, out


# ---- worker 定位链的 miss 语义**按调用点分叉**（ADR 0037 决策 3）----

def _miss(engine: str = "novaact"):
    """定位链全 miss 的结构化异常（带该引擎安装指引），仿 compose.resolve_worker_cmd 的抛出物。"""
    hint = {"novaact": "装法：uv tool install 'gherkai[local]'",
            "midscene": "装法：npm i -g @gherkai/worker-midscene"}[engine]
    return compose.WorkerNotFoundError(engine, f"引擎 {engine} 的 worker 运行时未找到。{hint}")


def test_run_exits_2_before_spawn_when_worker_runtime_missing(tmp_path, monkeypatch, capsys):
    """run 的分叉：定位链 miss → 打安装指引 + 以退出码 2 结束，**且在 spawn/落库之前**——不进 job 级 engine_error
    （「运行时没装」属「没开始执行就被拒」层；否则用户拿到一批 error 的 job 结果而非一句能照做的指引）。"""
    monkeypatch.setattr(m.compose, "resolve_worker_cmd", lambda engine, **kw: (_ for _ in ()).throw(_miss(engine)))
    started = []
    monkeypatch.setattr(m, "schedule", lambda *a, **k: started.append(1))
    reports = tmp_path / "reports"
    rc = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(reports)])
    assert rc == 2
    assert "uv tool install" in capsys.readouterr().err
    assert started == []            # 没开始执行
    assert not reports.exists()     # 也没落库（拒在 persistence.begin 之前，不留半成品 run）


def test_run_unused_engine_miss_does_not_block(tmp_path, monkeypatch, capsys):
    """miss 只影响**用到它**的 run：novaact-only 的 run 在 midscene 未装（dev 常态）下照常运行并以退出码 0 结束。

    preflight 只查本次 plan 用到的引擎；未用到的那个引擎即便 miss 也只是「一用即报错」。
    """
    real = m.compose.resolve_worker_cmd
    asked = []

    def spy(engine, **kw):
        asked.append(engine)
        if engine == "midscene":
            raise _miss("midscene")
        return real(engine, **kw)

    monkeypatch.setattr(m.compose, "resolve_worker_cmd", spy)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    rc = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(tmp_path / "r"), "--quiet"])
    assert rc == 0 and "novaact" in asked


def test_submit_local_exits_2_when_worker_runtime_missing(tmp_path, monkeypatch, capsys):
    """submit local 同 run（后台推进进程在本机启动 worker）：提交前以退出码 2 结束、不启动后台推进进程、不落库——否则「提交成功」
    之后后台每个 job 都 engine_error，用户要去翻 reconcile.log 才知道是没装 worker。"""
    import subprocess

    forked = []
    monkeypatch.setattr(subprocess, "Popen", lambda cmd, **kw: forked.append(cmd))
    monkeypatch.setattr(m.compose, "resolve_worker_cmd", lambda engine, **kw: (_ for _ in ()).throw(_miss(engine)))
    reports = tmp_path / "reports"
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--report-dir", str(reports)])
    assert rc == 2 and forked == []
    assert not reports.exists()
    assert "uv tool install" in capsys.readouterr().err


def test_list_deterministic_worker_not_found_exits_2(monkeypatch, capsys):
    # list-deterministic 的分叉：以退出码 2 结束、消息带安装指引（自述查不了就是查不了，无降级余地）
    def boom(engine, *, steps_dir=None, timeout_s=60.0):
        raise _miss(engine)

    monkeypatch.setattr(m.compose, "query_capabilities", boom)
    assert m.main(["list-deterministic"]) == 2
    assert "uv tool install" in capsys.readouterr().err


def test_plan_degrades_when_worker_runtime_missing(tmp_path, monkeypatch, capsys):
    """plan 的分叉与 run/submit **相反**（ADR 0037 决策 3 明示 + ADR 0036 决策 4）：保持 best-effort 降级——
    只丢该引擎的派发标注 + stderr 警告，plan 本体照出、以退出码 0 结束（feature 作者没装引擎运行时也该能预检写法）。"""
    def boom(engine, items, steps_dir=None):
        raise _miss("midscene")

    monkeypatch.setattr(m.compose, "match_deterministic", boom)
    assert m.main(["plan", str(_det_feature(tmp_path))]) == 0
    cap = capsys.readouterr()
    assert "页面地址匹配" in cap.out and "← 确定性" not in cap.out
    assert "标注降级" in cap.err


# ---- steps/ 定制面（ADR 0037 决策 4）：解析在组合根、随 definition 持久化、worker 只认 env ----

def _spy_build_engines(monkeypatch):
    """记录 build_engines 收到的 kwargs（仍调真实实现，保 cmd/env 接线真实）。

    每次调用都断言带了 run id：同步 run 不传它，worker 拿不到 RUN_ID、在建会话前以 1 退出（ADR 0024「run_id + scope_id 注入
    worker」条）；放在共用的 spy 里，经它的每条用例都兜住这一条。"""
    box = {}
    real = m.compose.build_engines

    def spy(**kwargs):
        assert kwargs.get("run_id"), "同步 run 须把本 run 的 id 传给 build_engines"
        box.update(kwargs)
        return real(**kwargs)

    monkeypatch.setattr(m.compose, "build_engines", spy)
    return box


def _spy_run_meta(monkeypatch):
    """记录 definition 构造入参（RunMeta 落库前的真值，云端后端不落本地文件也验得到）。"""
    box = {}
    real = m.RunMeta

    def spy(**kwargs):
        box.update(kwargs)
        return real(**kwargs)

    monkeypatch.setattr(m, "RunMeta", spy)
    return box


def test_run_steps_dir_flag_resolves_absolute_and_persists(tmp_path, monkeypatch):
    """`--steps-dir` → ①绝对化后注给 worker（build_engines 的 steps_dir → env GHERKAI_STEPS_DIR）
    ②写进 definition（`RunMeta.steps_dir`）。

    绝对化：worker 是 cwd 与 CLI 不同的子进程；随 definition 走：本机后台推进进程的 CWD 与提交进程
    可以不同，只有用同一个值，各宿主才用同一套确定性 step、判定才可复现。
    """
    steps = tmp_path / "mysteps"
    steps.mkdir()
    box = _spy_build_engines(monkeypatch)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    monkeypatch.delenv("GHERKAI_STEPS_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    reports = tmp_path / "reports"
    assert m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(reports),
                   "--steps-dir", "mysteps", "--quiet"]) == 0  # 相对给的 flag
    assert box["steps_dir"] == str(steps.resolve())            # 组合根侧已绝对化
    meta = json.loads(next(reports.iterdir()).joinpath("run_meta.json").read_text(encoding="utf-8"))
    assert meta["steps_dir"] == str(steps.resolve())


def test_run_steps_dir_env_and_flag_precedence(tmp_path, monkeypatch):
    # 解析顺序：--steps-dir > env GHERKAI_STEPS_DIR（两者都是显式意图，flag 更近）
    (tmp_path / "from-env").mkdir()
    (tmp_path / "from-flag").mkdir()
    monkeypatch.setenv("GHERKAI_STEPS_DIR", str(tmp_path / "from-env"))
    box = _spy_build_engines(monkeypatch)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    assert m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(tmp_path / "r1"), "--quiet"]) == 0
    assert box["steps_dir"] == str(tmp_path / "from-env")      # 无 flag → 用 env
    assert m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(tmp_path / "r2"),
                   "--steps-dir", str(tmp_path / "from-flag"), "--quiet"]) == 0
    assert box["steps_dir"] == str(tmp_path / "from-flag")     # flag 压 env


def test_run_default_steps_dir_used_only_when_it_exists(tmp_path, monkeypatch):
    """末级默认 `./steps`（相对**提交时** CWD）：存在才用、不存在则 None（「没这个目录」是多数项目的常态）。

    None 时 definition 该键为 null——worker 只有内建脚手架注册。
    """
    box = _spy_build_engines(monkeypatch)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    monkeypatch.delenv("GHERKAI_STEPS_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    reports = tmp_path / "r1"
    assert m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(reports), "--quiet"]) == 0
    assert box["steps_dir"] is None
    meta = json.loads(next(reports.iterdir()).joinpath("run_meta.json").read_text(encoding="utf-8"))
    assert meta["steps_dir"] is None
    (tmp_path / "steps").mkdir()  # 同一 CWD 下建出约定目录 → 下一次 run 自动用上
    assert m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(tmp_path / "r2"), "--quiet"]) == 0
    assert box["steps_dir"] == str((tmp_path / "steps").resolve())


def test_steps_dir_explicit_but_missing_exits_2(tmp_path, monkeypatch, capsys):
    """显式给的（flag/env）不是目录 → 以退出码 2 结束，**不静默忽略**：忽略等于把该目录里的确定性 step 悄悄换成
    AI 判定、run 还可能「通过」（假绿），是本项目最忌的静默降级（ADR 0037 决策 4 fail-loud 同源）。"""
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    monkeypatch.delenv("GHERKAI_STEPS_DIR", raising=False)
    feat = str(_write_feature(tmp_path))
    assert m.main(["run", feat, "--report-dir", str(tmp_path / "r"), "--steps-dir", str(tmp_path / "nope")]) == 2
    assert "--steps-dir" in capsys.readouterr().err
    monkeypatch.setenv("GHERKAI_STEPS_DIR", str(tmp_path / "nope"))
    assert m.main(["plan", feat]) == 2
    assert "GHERKAI_STEPS_DIR" in capsys.readouterr().err
    assert m.main(["list-deterministic"]) == 2


def test_submit_local_persists_steps_dir_into_definition(tmp_path, monkeypatch, inline_children, advanced):
    """submit 侧同 run：提交进程解析一次，经交给后台推进进程的输入写进 definition——后台推进进程用这一份推进（启动命令里**没有**
    这个选项，后台推进进程也不按自己的工作目录重解析 `./steps`），各宿主才一致。"""
    # 提交侧运行前检查会问一次能力自述（ADR 0037 决策 4）；本测只验持久化通道，那一跳由 conftest 的 autouse
    # 假替身盖住（不 spawn 真 worker）。
    steps = tmp_path / "steps"
    steps.mkdir()
    monkeypatch.delenv("GHERKAI_STEPS_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    reports = tmp_path / "reports"
    assert m.main(["submit", str(_write_feature(tmp_path)), "--report-dir", str(reports)]) == 0
    inline_children.settle()
    meta = json.loads((_submitted_run_dir(reports) / "run_meta.json").read_text(encoding="utf-8"))
    assert meta["steps_dir"] == str(steps.resolve())
    assert "--steps-dir" not in inline_children.only().argv  # 启动命令不带它：值只经 definition 传（单一通道）
    assert [mt.steps_dir for mt in advanced] == [str(steps.resolve())]


def test_plan_and_list_deterministic_pass_steps_dir_to_worker(tmp_path, monkeypatch, capsys):
    """两个非 job 入口同样加载 steps 目录（ADR 0037 决策 4）→ plan 标注与 list-deterministic 清单反映定制 step。"""
    steps = tmp_path / "steps"
    steps.mkdir()
    monkeypatch.delenv("GHERKAI_STEPS_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    seen = {}
    monkeypatch.setattr(m.compose, "match_deterministic",
                        lambda engine, texts, steps_dir=None: seen.update(match=steps_dir) or [None] * len(texts))
    monkeypatch.setattr(m.compose, "query_capabilities",
                        lambda engine, *, steps_dir=None, timeout_s=60.0: seen.update(query=steps_dir) or
                        {"schema_version": 2, "engine": engine, "min_grace_s": 150.0, "deterministic_steps": [], "model_id": "nova-act-v1.0",
                         "targets": [{"device": "desktop", "ui_kinds": ["web"]}]})
    assert m.main(["plan", str(_det_feature(tmp_path))]) == 0
    assert m.main(["list-deterministic"]) == 0
    assert seen["match"] == str(steps.resolve()) and seen["query"] == str(steps.resolve())


def _steps_dir_with_file(tmp_path: Path) -> Path:
    d = tmp_path / "steps"
    d.mkdir()
    (d / "demo.py").write_text("# placeholder\n", encoding="utf-8")
    return d


def _fake_worker_cmd(engine: str, **kw):
    return compose.WorkerCmd(cmd=["python", "-m", "x"], cwd=None, source="test")


def test_plan_exits_2_when_user_steps_fail_to_load(tmp_path, monkeypatch, capsys):
    """steps 文件加载失败（worker 自述非零退出）→ plan 以退出码 2 结束、不降级成「无标注」（ADR 0037 决策 4 提交侧前置）。"""
    feat = tmp_path / "t.feature"
    feat.write_text('Feature: t\n  Scenario: s\n    When "做点啥"\n', encoding="utf-8")
    steps = _steps_dir_with_file(tmp_path)

    def boom(engine, texts, *, steps_dir=None, timeout_s=60.0):
        raise compose.WorkerSelfDescribeError(engine, 2, "demo.py：SyntaxError", "确定性命中查询")

    monkeypatch.setattr(compose, "match_deterministic", boom)
    rc = m.main(["plan", str(feat), "--steps-dir", str(steps)])
    assert rc == 2
    err = capsys.readouterr().err
    assert "plan 拒绝出结果" in err and "版本不一致" in err  # 不降级；成因提示（steps 加载失败或版本不一致）与其它入口同一句


def test_plan_exits_2_and_relays_worker_sentence_when_match_input_rejected(tmp_path, monkeypatch, capsys):
    """worker 拒绝 match 查询的输入形状（命令行工具与 worker 版本不一致，ADR 0036 决策 4）→ plan 以退出码 2 结束并转述 worker 的那一句，
    不降级成「无标注」；worker 的这次非零退出与 steps 加载失败同属 WorkerSelfDescribeError，CLI 不另设分支。"""
    feat = tmp_path / "t.feature"
    feat.write_text('Feature: t\n  Scenario: s\n    When "做点啥"\n', encoding="utf-8")
    sentence = "收到的确定性 step 查询不是这个 worker 认的格式：命令行工具与 worker 的版本不一致，请把两者装成同一版本。"

    def rejected(engine, items, *, steps_dir=None, timeout_s=60.0):
        raise compose.WorkerSelfDescribeError(engine, 2, f"worker: {sentence}\n", "确定性 step 查询")

    monkeypatch.setattr(compose, "match_deterministic", rejected)
    assert m.main(["plan", str(feat)]) == 2
    err = capsys.readouterr().err
    assert "plan 拒绝出结果" in err and sentence in err and "标注降级" not in err


def test_plan_degrades_when_worker_missing(tmp_path, monkeypatch, capsys):
    """对照：定位链 miss（运行时没装）plan 仍降级并以退出码 0 结束（ADR 0036 决策 4 / 0037 决策 3 的分叉保留）。"""
    feat = tmp_path / "t.feature"
    feat.write_text('Feature: t\n  Scenario: s\n    When "做点啥"\n', encoding="utf-8")

    def missing(engine, texts, *, steps_dir=None, timeout_s=60.0):
        raise compose.WorkerNotFoundError(engine, "装法：…")

    monkeypatch.setattr(compose, "match_deterministic", missing)
    rc = m.main(["plan", str(feat)])
    assert rc == 0
    assert "标注降级" in capsys.readouterr().err


def test_run_and_submit_exit_2_before_spawn_when_user_steps_fail(tmp_path, monkeypatch, capsys):
    """run / submit：运行前先问一次能力自述，worker 非零退出 → 起任何 job 之前以退出码 2 结束（不进 job 级 error）。

    **文案中性**：该入口现在会加载使用方 steps，非零退出既可能是那些文件加载失败、也可能是这个引擎的 worker
    与命令行工具版本不一致（不认该入口）——两种成因都得点到，别把用户往单一方向带。"""
    feat = tmp_path / "t.feature"
    feat.write_text('Feature: t\n  Scenario: s\n    When "做点啥"\n', encoding="utf-8")
    steps = _steps_dir_with_file(tmp_path)
    monkeypatch.setattr(compose, "resolve_worker_cmd", _fake_worker_cmd)

    def boom(engine, *, steps_dir=None, timeout_s=60.0):
        raise compose.WorkerSelfDescribeError(engine, 2, "demo.py：SyntaxError", "能力自述")

    monkeypatch.setattr(compose, "query_capabilities", boom)
    spawned = {"n": 0}
    monkeypatch.setattr(m, "schedule", lambda *a, **k: spawned.__setitem__("n", spawned["n"] + 1))
    assert m.main(["run", str(feat), "--no-report", "--steps-dir", str(steps)]) == 2
    assert spawned["n"] == 0
    assert m.main(["submit", str(feat), "--report-dir", str(tmp_path / "r"), "--steps-dir", str(steps)]) == 2
    err = capsys.readouterr().err
    assert "demo.py：SyntaxError" in err  # 原样转述 worker 诊断
    assert "steps/ 目录里的文件加载失败" in err and "版本不一致" in err
    assert not (tmp_path / "r").exists() or not any((tmp_path / "r").iterdir())  # 没落任何 run 记录


def test_incompatible_self_description_is_relayed_without_worker_cause_hint(tmp_path, monkeypatch, capsys):
    """自述取到了、与命令行工具不兼容（此处是协议版本不一致）：run、list-deterministic 以退出码 2 结束，doctor 落进 steps.load 行，
    三处都只转述 compose 给的那一句，不接「以 worker 自己的报错为准」的成因提示——这句诊断出自命令行工具自己的契约核对，
    不是 worker 的报错（ADR 0036「5.」末段：消费者按异常类区分）。"""
    sentence = "引擎 novaact 的能力自述格式版本是 1，这个命令行工具认的是 2：命令行工具与 worker 的版本不一致，请把两者装成同一版本。"
    _fake_locator(monkeypatch)
    _no_provider(monkeypatch)
    monkeypatch.delenv("GHERKAI_STEPS_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(m.compose, "query_capabilities", lambda engine, **kw: (_ for _ in ()).throw(
        compose.WorkerIncompatibleError(engine, sentence)))
    monkeypatch.setattr(m, "schedule", lambda *a, **k: pytest.fail("自述不兼容时不应起 job"))
    assert m.main(["run", str(_write_feature(tmp_path)), "--no-report"]) == 2
    assert m.main(["list-deterministic"]) == 2
    err = capsys.readouterr().err
    assert err.count(sentence) == 2 and "以 worker 自己的报错为准" not in err
    assert m.main(["doctor", "--json"]) == 0  # 无 steps/ 目录：自述失败只是可选项
    by = {(c["section"], c["name"]): c for c in json.loads(capsys.readouterr().out)["checks"]}
    assert by[("steps", "load.novaact")]["detail"] == f"worker 自述失败：{sentence}"


def test_plan_rejects_a_directory_as_feature(tmp_path, capsys):
    """给了目录 / 读不了的路径 → 以退出码 2 结束并报「读 feature 失败」，不是 IsADirectoryError traceback（退出码分层见 ADR 0030 决定七）。
    读 feature 的失败面不止 FileNotFoundError：目录、权限、非 UTF-8 都属输入问题，同类处置。"""
    rc = m.main(["plan", str(tmp_path)])
    assert rc == 2
    assert "读 feature 失败" in capsys.readouterr().err


def test_same_feature_given_twice_is_deduped_not_rejected(tmp_path, capsys):
    """同一个 .feature 传两遍：CLI 按一次算 + 打一行提示，不再撞 core 窄腰的 uri 互异违约而以退出码 2 结束
    （收集去重是调用方的责任，ADR 0025）。"""
    feat = _write_feature(tmp_path)
    rc = m.main(["plan", str(feat), str(feat), "--json"])
    assert rc == 0
    doc = json.loads(capsys.readouterr().out)
    assert len(doc["jobs"]) == 1 and sum(len(j["scenarios"]) for j in doc["jobs"]) == 1


def test_differently_written_same_file_is_deduped_with_a_hint(tmp_path, monkeypatch, capsys):
    """写法不同、归一后是同一个文件（`demo.feature` 与 `sub/../demo.feature`）→ 同样按一次算：
    去重键必须取 load_feature 算出的 uri（路径归一后），不是原始路径字符串——glob + 显式并列常撞出这种混写。
    提示点名被忽略的那个写法（可能是打错了文件名）。

    注：`./x.feature` 不足以守住这条——argparse 的 `type=Path` 已把 `./` 折掉，两个入参到这里已是同一字符串。
    """
    _write_feature(tmp_path)
    (tmp_path / "sub").mkdir()
    monkeypatch.chdir(tmp_path)
    rc = m.main(["plan", "demo.feature", "sub/../demo.feature", "--json"])
    cap = capsys.readouterr()
    assert rc == 0, cap.err
    assert len(json.loads(cap.out)["jobs"]) == 1
    assert "忽略 1 个重复路径" in cap.err and "sub/../demo.feature" in cap.err


def test_render_status_terminal_prints_artifact_locations(capsys):
    """终态时对标 `run` 结束的三行：报告 / 运行元信息 / 判定明细（S3 或本地路径可直接复制）；未终态不打（报告还没生成）。"""
    m._render_status(_mk_state(Status.PASSED), _args(), locations=_LOCS)
    err = capsys.readouterr().err
    assert "报告: file:///tmp/x/r/index.html" in err and "判定明细: file:///tmp/x/r/jobs" in err
    assert "运行元信息: file:///tmp/x/r/run_meta.json、file:///tmp/x/r/run_state.json" in err
    m._render_status(_mk_state(Status.RUNNING), _args(), locations=_LOCS)
    assert "报告:" not in capsys.readouterr().err
    # --json 形状不变：stdout 纯 RunState JSON，stderr 不掺位置行
    m._render_status(_mk_state(Status.PASSED), _args(json_=True), locations=_LOCS)
    cap = capsys.readouterr()
    json.loads(cap.out)
    assert "报告:" not in cap.err


def test_render_status_without_a_report_drops_only_the_report_line(capsys):
    """本命令处置了这个 run 而报告没有生成时（report_written=False），人读方式只少报告那一行，另两行照旧、开头的空行留在第一行上；
    --json 的 artifacts 照样给出报告的约定落点（它不表达那里有没有内容）。"""
    m._render_status(_mk_state(Status.ABORTED), _args(), locations=_LOCS, report_written=False)
    assert capsys.readouterr().err.splitlines() == [
        "", "运行元信息: file:///tmp/x/r/run_meta.json、file:///tmp/x/r/run_state.json", "判定明细: file:///tmp/x/r/jobs"]
    m._render_status(_mk_state(Status.ABORTED), _args(json_=True), locations=_LOCS, report_written=False)
    assert json.loads(capsys.readouterr().out)["artifacts"] == _LOCS


def test_run_terminal_prints_the_same_three_artifact_lines(tmp_path, monkeypatch, capsys):
    """`run` 结束打的三行与 `status` 终态**同一份**（`_print_artifact_lines`）：报告 / 运行元信息 / 判定明细，
    值取本次 run 的落点（file:// 可直接复制）。两处曾各抄一份，文案或键名一改就分叉。"""
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    reports = tmp_path / "reports"
    assert m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(reports)]) == 0
    err = capsys.readouterr().err
    run_dir = next(d for d in reports.iterdir() if d.is_dir())
    assert f"报告: {(run_dir / 'index.html').as_uri()}" in err
    assert (f"运行元信息: {(run_dir / 'run_meta.json').as_uri()}、"
            f"{(run_dir / 'run_state.json').as_uri()}") in err
    assert f"判定明细: {(run_dir / 'jobs').as_uri()}" in err


def test_artifact_lines_report_write_failure_falls_back_to_a_note(capsys):
    """报告写入被隔离（落点表里没有 report_index 键，ADR 0030 决定三）→ 报告那行给「写失败」提示，
    既不打裸 None、也不掩盖另两行仍然有效。"""
    m._print_artifact_lines({k: v for k, v in _LOCS.items() if k != "report_index"})
    err = capsys.readouterr().err
    assert "报告: <报告写入失败" in err and "None" not in err
    assert "判定明细: file:///tmp/x/r/jobs" in err  # 判定结果照旧落库、位置照打


def test_run_lists_each_job_but_submit_only_prints_the_count(tmp_path, monkeypatch, capsys, inline_children, advanced):
    """run 与 submit 共享同一段前置（plan → steps 目录 → 本机后端 worker 检查），唯一的输出差别是逐 job 明细：
    run 打（本机批量运行要看得见分组），submit 不打（提交完就走、进度看 status）。计数行两处相同。"""
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    assert m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(tmp_path / "r")]) == 0
    err = capsys.readouterr().err
    assert "plan: 1 job(s)" in err and "- scope=" in err

    assert m.main(["submit", str(_write_feature(tmp_path)), "--report-dir", str(tmp_path / "s")]) == 0
    inline_children.settle()
    err = capsys.readouterr().err
    assert "plan: 1 job(s)" in err and "- scope=" not in err


def test_run_and_submit_share_one_steps_dir_help_text(capsys):
    """`--steps-dir` 的 help 在 run/submit 两处共用同一段措辞：run 的一段在公共段后加「值随提交记录走」，submit 的一段在 run 的一段
    之后再加本机后台推进进程照它执行与云端后端不生效两句（run 只有本机后端，不写云端那句）；共有的部分只写一处，改一处即两处生效。
    `plan`、`doctor` 等不产提交记录的子命令用不加补充的公共段（`doctor` 同样带 `--backend`，判据不是它）。
    """
    import argparse

    sub = next(a for a in m._build_parser()._actions if isinstance(a, argparse._SubParsersAction))

    def steps_dir_help(command: str) -> str:
        return next(a.help for a in sub.choices[command]._actions if "--steps-dir" in a.option_strings)

    assert steps_dir_help("run") == m._STEPS_DIR_HELP_RUN and steps_dir_help("submit") == m._STEPS_DIR_HELP_SUBMIT
    assert m._STEPS_DIR_HELP_SUBMIT.startswith(m._STEPS_DIR_HELP_RUN) and m._STEPS_DIR_HELP_RUN.startswith(m._STEPS_DIR_HELP)
    assert "--backend cloud" not in steps_dir_help("run") and "--backend cloud" in steps_dir_help("submit")
    assert steps_dir_help("plan").startswith(m._STEPS_DIR_HELP)
    assert steps_dir_help("plan") != m._STEPS_DIR_HELP_RUN
    # doctor 也带 --backend，却只查环境、不产提交记录 → 恒用不加补充的公共段（守住「判据不是 --backend」）
    assert steps_dir_help("doctor") == m._STEPS_DIR_HELP


# ---- --tags / --scenario 筛选（ADR 0041 决策一）：run/plan/submit 同一解析 ----
def _tagged_feature(tmp_path):
    p = tmp_path / "sel.feature"
    p.write_text("Feature: F\n"
                 "  @smoke\n  Scenario: 登录成功\n    When \"a\"\n"
                 "  @slow\n  Scenario: 结账\n    When \"b\"\n"
                 "  @smoke @slow\n  Scenario: 搜索\n    When \"c\"\n", encoding="utf-8")
    return p


def _plan_names(capsys, *extra):
    out = json.loads(capsys.readouterr().out)
    return sorted(sc["name"] for j in out["jobs"] for sc in j["scenarios"])


def test_plan_tags_any_within_value_and_all_across_flags(tmp_path, capsys):
    """一个 --tags 值内逗号表示任一命中；重复 --tags 表示都要命中；@ 可省。"""
    feat = _tagged_feature(tmp_path)
    assert m.main(["plan", str(feat), "--json", "--tags", "smoke"]) == 0
    assert _plan_names(capsys) == ["搜索", "登录成功"]
    assert m.main(["plan", str(feat), "--json", "--tags", "@smoke,@slow"]) == 0
    assert _plan_names(capsys) == ["搜索", "登录成功", "结账"]  # sorted() 按码点
    assert m.main(["plan", str(feat), "--json", "--tags", "smoke", "--tags", "slow"]) == 0
    assert _plan_names(capsys) == ["搜索"]


def test_plan_scenario_by_id_line_or_title_substring(tmp_path, capsys):
    """--scenario：<uri>:<行> / 行号 / :行号 / 标题子串；多个为或；与 --tags 同给为且。"""
    feat = _tagged_feature(tmp_path)
    assert m.main(["plan", str(feat), "--json", "--scenario", "结账"]) == 0
    assert _plan_names(capsys) == ["结账"]
    assert m.main(["plan", str(feat), "--json", "--scenario", "3", "--scenario", ":9"]) == 0  # 行 3 是登录成功，行 9 是搜索
    assert _plan_names(capsys) == ["搜索", "登录成功"]
    assert m.main(["plan", str(feat), "--json", "--scenario", f"{feat}:6"]) == 0
    assert _plan_names(capsys) == ["结账"]
    assert m.main(["plan", str(feat), "--json", "--tags", "slow", "--scenario", "搜"]) == 0
    assert _plan_names(capsys) == ["搜索"]


def test_plan_empty_selection_exits_2_and_lists_candidates(tmp_path, capsys):
    """筛空 → 以退出码 2 结束并列出全部候选（id  标题），别静默运行空批。"""
    feat = _tagged_feature(tmp_path)
    assert m.main(["plan", str(feat), "--json", "--tags", "nope"]) == 2
    err = capsys.readouterr().err
    assert "没有 scenario 匹配 --tags nope" in err and "登录成功" in err and "结账" in err and "搜索" in err
    assert "@smoke @slow" in err  # 候选行带 tags，方便改 --tags


def test_run_tags_narrow_the_definition_and_report_selection(tmp_path, monkeypatch, capsys):
    """run 与 plan 同一解析：筛后的 job 集就是 definition（schedule 只收到被选中的），stderr 打「筛选：N/M」。"""
    feat = _tagged_feature(tmp_path)
    box = {}
    monkeypatch.setattr(m, "schedule", _capturing_schedule(Status.PASSED, box))
    rc = m.main(["run", str(feat), "--no-report", "--tags", "slow"])
    assert rc == 0
    assert sorted(sc.name for j in box["run_meta"].jobs for sc in j.scenarios) == ["搜索", "结账"]
    assert "筛选：2/3 scenario" in capsys.readouterr().err


def test_run_quiet_writes_worker_log_and_reports_its_location(tmp_path, monkeypatch, capsys):
    """--quiet（ADR 0041 决策二）：worker 日志落 <run_dir>/worker.log（--no-report 落临时目录），结束只打一行位置；
    --json 的 artifacts 带 worker_log。schedule 被 fake、不起真 worker，这里验的是装配与输出面。"""
    box = {}
    monkeypatch.setattr(m, "schedule", _capturing_schedule(Status.PASSED, box))
    rc = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(tmp_path / "r"), "--quiet"])
    assert rc == 0
    err = capsys.readouterr().err
    assert "worker 日志: file://" in err and "/worker.log" in err
    assert list((tmp_path / "r").glob("*/worker.log"))
    rc = m.main(["run", str(_write_feature(tmp_path)), "--no-report", "--quiet", "--json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["artifacts"]["worker_log"].startswith("file://") and out["artifacts"]["worker_log"].endswith(".log")
    assert "run_meta" not in out["artifacts"]  # --no-report 没落库，只剩 worker_log


# ---- list-engines --json / doctor（ADR 0041 决策三、四）----
def _fake_locator(monkeypatch, available=("novaact",)):
    """把定位链换成假的：available 里的引擎命中「同 venv 模块」，其余 miss（带安装指引）。"""
    def fake(name, *, version=None):
        if name in available:
            return compose.WorkerCmd(cmd=["python", "-m", f"gherkai_worker_{name}"], cwd=None, source=f"同 venv 模块 gherkai_worker_{name}")
        raise compose.WorkerNotFoundError(name, f"引擎 {name} 的 worker 运行时未找到。装法略")
    monkeypatch.setattr(m.compose, "resolve_worker_cmd", fake)


def _no_provider(monkeypatch):
    monkeypatch.setattr(m._deploy, "provider_entry_points", lambda: [])
    monkeypatch.setattr(m._deploy, "resolve_provider", lambda name=None: (None, "没有可用的部署 provider：装 `gherkai[deploy-aws]`"))


def _stub_device_farm(monkeypatch, *, arn=None, sessions=(), list_error=None, read_error=None):
    """doctor 云端段末尾的设备支持两行（`backend.devices.project` / `backend.devices.sessions`）的替身：项目 ARN 的 SSM 读与会话列举都不连真 AWS。

    缺省摆成「部署未启用设备支持」（SSM 没有项目 ARN）、且断言此时不去列举会话；返回记录调用的字典，供用例核对读 SSM 用的
    prefix / 后端区域与列举用的项目 ARN / profile。凡走到 `aws.identity` 通过的 doctor 云端用例都要摆它，否则会去读真 SSM。
    """
    from gherkai_runtime import devicefarm

    calls: dict = {"read": [], "list": []}

    def read(**kw):
        calls["read"].append(kw)
        if read_error is not None:
            raise read_error
        return arn

    def list_open(project_arn, *, profile):
        calls["list"].append((project_arn, profile))
        if arn is None:
            raise AssertionError("SSM 里没有项目 ARN 时不该列举会话")
        if list_error is not None:
            raise list_error
        return list(sessions)

    monkeypatch.setattr(m.compose, "read_device_farm_project", read)
    monkeypatch.setattr(devicefarm, "list_open_sessions", list_open)
    return calls


def test_list_engines_json_shape(monkeypatch, capsys):
    _fake_locator(monkeypatch)
    assert m.main(["list-engines", "--json"]) == 0
    rows = json.loads(capsys.readouterr().out)
    by = {r["engine"]: r for r in rows}
    assert set(by) == {"midscene", "novaact"}
    assert by["novaact"]["available"] is True and by["novaact"]["cmd"][-1] == "gherkai_worker_novaact" and by["novaact"]["hint"] is None
    assert by["midscene"]["available"] is False and by["midscene"]["cmd"] is None and "未找到" in by["midscene"]["hint"]


def test_doctor_local_json_checks_and_exit_codes(tmp_path, monkeypatch, capsys):
    """local 自检：引擎（一缺一在→any ok）、steps 目录加载、云端两项与未装的 provider 标未查；全 required ok → 0；
    steps 加载失败 → 2（agent 据退出码分流）。"""
    _fake_locator(monkeypatch)
    _no_provider(monkeypatch)
    steps = tmp_path / "steps"; steps.mkdir()
    monkeypatch.setattr(m.compose, "query_capabilities", lambda engine, *, steps_dir=None, timeout_s=60.0: {
        "schema_version": 2, "engine": engine, "min_grace_s": 150.0, "model_id": "nova-act-v1.0",
        "targets": [{"device": "desktop", "ui_kinds": ["web"]}],
        "deterministic_steps": [{"pattern": "a"}, {"pattern": "b"}]})  # 计数取自述对象的清单键（ADR 0036「5.」）
    # 被拒方案的护栏（ADR 0051 决策 10）：本机后端即使配置了项目 ARN，doctor 也不读 SSM、不列会话——不带云端参数的 doctor 不做 AWS 调用。
    # 两个替身抛的异常会被设备两行的 except 吞成可选行，所以真正的断言是「设备两行不存在」。
    from gherkai_runtime import devicefarm
    monkeypatch.setenv("GHERKAI_DEVICE_FARM_PROJECT_ARN", _DF_PROJECT)

    def _no_ssm_read(**kw):
        raise AssertionError("本机 doctor 不该读 SSM")

    def _no_list(*a, **kw):
        raise AssertionError("本机 doctor 不该列举会话")

    monkeypatch.setattr(m.compose, "read_device_farm_project", _no_ssm_read)
    monkeypatch.setattr(devicefarm, "list_open_sessions", _no_list)
    assert m.main(["doctor", "--json", "--steps-dir", str(steps)]) == 0
    doc = json.loads(capsys.readouterr().out)
    by = {(c["section"], c["name"]): c for c in doc["checks"]}
    assert doc["ok"] is True
    assert not any(c["name"].startswith("devices.") for c in doc["checks"])
    assert by[("engines", "novaact")]["ok"] and not by[("engines", "midscene")]["ok"] and by[("engines", "midscene")]["required"] is False
    assert by[("engines", "any")]["ok"] and by[("engines", "any")]["required"] is True
    assert by[("steps", "load.novaact")]["ok"] and "2 条" in by[("steps", "load.novaact")]["detail"]
    assert ("steps", "load.midscene") not in by  # 没装的引擎不探自述
    assert "未查" in by[("aws", "identity")]["detail"]
    # 未查是单独一种结果（ADR 0041 决策四）：每一行都带 skipped 键；未查的行恒 ok=true、required=false，其余行 skipped=false
    assert all(isinstance(c.get("skipped"), bool) for c in doc["checks"])
    unchecked = {key for key, c in by.items() if c["skipped"]}
    assert unchecked == {("aws", "identity"), ("backend", "reachability"), ("provider", "deploy-aws")}
    assert all(by[key]["ok"] is True and by[key]["required"] is False for key in unchecked)
    assert "只有部署方需要" in by[("provider", "deploy-aws")]["detail"]  # 没装部署 provider：有没有装已查到，未查的是工具链自检
    # 人读形态：未查的行结果列为 ·，查过且通过的仍为 ✓；尾行点明 · 的含义
    assert m.main(["doctor", "--steps-dir", str(steps)]) == 0
    out = capsys.readouterr().out
    for row in ("aws.identity", "backend.reachability", "provider.deploy-aws"):
        assert re.search(r"·\s*│\s*" + re.escape(row) + r"\s", out), row
    assert re.search(r"✓\s*│\s*engines\.novaact\s", out)
    assert "自检通过（· 为未查，原因见说明列）" in out

    def boom(engine, *, steps_dir=None, timeout_s=60.0):
        raise RuntimeError("worker 自述以退出码 1 结束：steps/login.py 第 3 行 SyntaxError")  # doctor 对任何加载异常都原样转述
    monkeypatch.setattr(m.compose, "query_capabilities", boom)
    assert m.main(["doctor", "--json", "--steps-dir", str(steps)]) == 2
    doc = json.loads(capsys.readouterr().out)
    bad = next(c for c in doc["checks"] if c["name"] == "load.novaact")
    assert doc["ok"] is False and bad["ok"] is False and "SyntaxError" in bad["detail"]


def test_doctor_no_engine_at_all_fails_locally_but_not_for_cloud(monkeypatch, capsys):
    _fake_locator(monkeypatch, available=())
    _no_provider(monkeypatch)
    assert m.main(["doctor", "--json"]) == 2
    assert json.loads(capsys.readouterr().out)["ok"] is False
    # 云端后端不需要本机 worker：engines.any 降为可选，其余云端项被 fake 成 ok
    monkeypatch.setattr(m.compose, "probe_aws_identity", lambda *, region, profile: {"account": "x", "arn": "arn:aws:sts::x:assumed-role/r", "region": region})
    monkeypatch.setattr(m.compose, "check_backend_skew", lambda **kw: (compose.SKEW_OK, "", "1.4.1"))
    monkeypatch.setattr(m.compose, "preflight_cloud_resources", lambda **kw: None)
    monkeypatch.setattr(m.compose, "read_worker_default", lambda **kw: "base")
    monkeypatch.setattr(m.compose, "resolve_worker_variant", lambda **kw: {
        e: compose.WorkerResolution(engine=e, variant=kw["variant"], revision_arn=f"arn:{e}:7", digest="sha256:0") for e in kw["engines"]})
    _stub_device_farm(monkeypatch)
    assert m.main(["doctor", "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1", "--json"]) == 0
    doc = json.loads(capsys.readouterr().out)
    by = {(c["section"], c["name"]): c for c in doc["checks"]}
    assert by[("engines", "any")]["required"] is False
    assert by[("aws", "region")]["ok"] and by[("aws", "region")]["detail"] == "us-east-1"
    assert by[("aws", "identity")]["ok"] and "assumed-role" in by[("aws", "identity")]["detail"]
    assert by[("backend", "version")]["ok"] and by[("backend", "resources")]["ok"]
    assert by[("backend", "worker.default")]["ok"] and by[("backend", "worker.default")]["required"] is False
    assert by[("backend", "worker.novaact")]["ok"] and "arn:novaact:7" in by[("backend", "worker.novaact")]["detail"]
    assert by[("backend", "worker.novaact")]["required"] is False and by[("backend", "worker.any")]["ok"] and by[("backend", "worker.any")]["required"] is True


def test_doctor_cloud_reports_backend_failures_and_exits_2(monkeypatch, capsys):
    _fake_locator(monkeypatch)
    _no_provider(monkeypatch)
    monkeypatch.setattr(m.compose, "probe_aws_identity", lambda *, region, profile: {"account": "x", "arn": "arn", "region": region})
    monkeypatch.setattr(m.compose, "check_backend_skew", lambda **kw: (compose.SKEW_BLOCK, "版本 skew：本机 CLI 新于后端", "1.3.0"))
    monkeypatch.setattr(m.compose, "preflight_cloud_resources", lambda **kw: "events 表 vfy-events 不存在——prefix 配错或后端未部署")
    monkeypatch.setattr(m.compose, "read_worker_default", lambda **kw: "base")
    monkeypatch.setattr(m.compose, "resolve_worker_variant", lambda **kw: (_ for _ in ()).throw(compose.WorkerVariantError("没有映射", engine=kw["engines"][0])))
    _stub_device_farm(monkeypatch)
    assert m.main(["doctor", "--prefix", "vfy-", "--region", "us-east-1", "--json"]) == 2  # 给了 --prefix 即查云端
    doc = json.loads(capsys.readouterr().out)
    by = {(c["section"], c["name"]): c for c in doc["checks"]}
    assert not by[("backend", "version")]["ok"] and "skew" in by[("backend", "version")]["detail"]
    assert not by[("backend", "resources")]["ok"] and "vfy-events" in by[("backend", "resources")]["detail"]
    assert not by[("backend", "worker.novaact")]["ok"] and not by[("backend", "worker.midscene")]["ok"]
    assert not by[("backend", "worker.any")]["ok"] and by[("backend", "worker.any")]["required"] is True  # 两引擎都解析不到才算必修失败
    # 一个 revision 都没解析到 → 停止宽限无从比对：整行记未查（不去 describe 任何 task-def，也不冒充「查过了」）
    grace = by[("backend", "worker.grace")]
    assert grace["skipped"] is True and grace["ok"] is True and grace["required"] is False
    assert "没有解析到镜像的引擎" in grace["detail"]
    # 查过而没通过的行不记未查
    assert by[("backend", "version")]["skipped"] is False and by[("backend", "worker.any")]["skipped"] is False


# ---- doctor --backend cloud 的停止宽限比对（ADR 0024「引擎自报下限」× ADR 0032 真容器校准结论 4）----

def _cloud_backend_ok(monkeypatch):
    """把 cloud doctor 里 worker.grace 之前的每一项摆成 ok，只留停止宽限那行做变量。"""
    _no_provider(monkeypatch)
    monkeypatch.setattr(m.compose, "probe_aws_identity",
                        lambda *, region, profile: {"account": "x", "arn": "arn", "region": region})
    monkeypatch.setattr(m.compose, "check_backend_skew", lambda **kw: (compose.SKEW_OK, "", "1.4.1"))
    monkeypatch.setattr(m.compose, "preflight_cloud_resources", lambda **kw: None)
    monkeypatch.setattr(m.compose, "read_worker_default", lambda **kw: "base")
    monkeypatch.setattr(m.compose, "resolve_worker_variant", lambda **kw: {
        e: compose.WorkerResolution(engine=e, variant=kw["variant"], revision_arn=f"arn:{e}:7", digest="sha256:0")
        for e in kw["engines"]})
    _stub_device_farm(monkeypatch)


def _stub_stop_timeout(monkeypatch, value, asked=None):
    def fake(revision_arn, *, engine, region=None, profile=None, ecs=None):
        if asked is not None:
            asked.append((engine, revision_arn))
        return value(engine) if callable(value) else value
    monkeypatch.setattr(m.compose, "read_task_def_stop_timeout", fake)


def _doctor_cloud_json(capsys, expect_rc=0):
    assert m.main(["doctor", "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1", "--json"]) == expect_rc
    return {(c["section"], c["name"]): c for c in json.loads(capsys.readouterr().out)["checks"]}


def test_doctor_cloud_worker_grace_ok_and_skips_engine_without_local_worker(monkeypatch, capsys):
    """两态一测：本机装了的引擎（midscene）下限 ≤ 云端停止宽限 → ✓；本机没装的（novaact）**跳过**。

    跳过而非失败：下限是 worker 自报的，本机没这个 worker 就问不出来——只提交、不在本机执行的人不该为这一行装运行时。
    比对只对**已解析到 revision** 的引擎做一次 describe（不去猜没解析到的那个引擎）。
    """
    _fake_locator(monkeypatch, available=("midscene",))
    _cloud_backend_ok(monkeypatch)
    asked: list[tuple] = []
    _stub_stop_timeout(monkeypatch, 120, asked)
    by = _doctor_cloud_json(capsys)
    row = by[("backend", "worker.grace")]
    assert row["ok"] and row["required"] is False
    assert row["skipped"] is False  # 比了一个引擎：按已做的部分给结果，跳过的那个写在说明里，不记未查
    assert f"收尾需 {FAKE_MIN_GRACE_S['midscene']:g}s ≤ 云端停止宽限 120s" in row["detail"]
    assert "本机没有 novaact 的 worker，跳过" in row["detail"]
    assert asked == [("midscene", "arn:midscene:7")]  # 跳过的引擎不 describe


def test_doctor_cloud_worker_grace_without_any_local_worker_is_unchecked(monkeypatch, capsys):
    """两个引擎都解析到了镜像、但本机一个对应的 worker 都没有 → 一项比对都没做，整行记未查（ADR 0041 决策四），
    不再以 ok=true 的「跳过」冒充查过；说明列点名缺的 worker，也不去 describe 任何 task-def。人读结果列为 ·。"""
    _fake_locator(monkeypatch, available=())
    _cloud_backend_ok(monkeypatch)
    asked: list[tuple] = []
    _stub_stop_timeout(monkeypatch, 120, asked)
    row = _doctor_cloud_json(capsys)[("backend", "worker.grace")]
    assert row["skipped"] is True and row["ok"] is True and row["required"] is False
    assert row["detail"].startswith("未查：") and "midscene/novaact" in row["detail"]
    assert asked == []
    assert m.main(["doctor", "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1"]) == 0
    assert re.search(r"·\s*│\s*backend\.worker\.grace\s", capsys.readouterr().out)


def test_doctor_cloud_worker_grace_single_revision_without_its_local_worker_is_unchecked(monkeypatch, capsys):
    """只解析到 midscene 的镜像、本机只有 novaact 的 worker 时，解析到的引擎本机都没有 worker：一项比对都没做，整行记未查。
    判据是「解析到的引擎」而不是全部引擎：本机有另一个引擎的 worker 不算做了比对，也不去读任何 task definition。"""
    _fake_locator(monkeypatch, available=("novaact",))
    _cloud_backend_ok(monkeypatch)

    def resolve(**kw):
        eng = kw["engines"][0]
        if eng != "midscene":
            raise compose.WorkerVariantError("没有映射", engine=eng)
        return {eng: compose.WorkerResolution(engine=eng, variant=kw["variant"], revision_arn=f"arn:{eng}:7", digest="sha256:0")}
    monkeypatch.setattr(m.compose, "resolve_worker_variant", resolve)
    asked: list[tuple] = []
    _stub_stop_timeout(monkeypatch, 120, asked)
    by = _doctor_cloud_json(capsys)
    assert by[("backend", "worker.midscene")]["ok"] and not by[("backend", "worker.novaact")]["ok"]
    row = by[("backend", "worker.grace")]
    assert row["skipped"] is True and row["ok"] is True and row["required"] is False
    assert row["detail"].startswith("未查：") and "本机没有 midscene 的 worker" in row["detail"]
    assert asked == []


def test_doctor_cloud_worker_grace_probe_error_with_other_engine_skipped_is_a_result(monkeypatch, capsys):
    """一个引擎探测出错、另一个本机没有 worker：探测出错是检查失败、不是未查，整行按已做的部分给结果（ok=false、skipped=false）。"""
    _fake_locator(monkeypatch, available=("midscene",))
    _cloud_backend_ok(monkeypatch)
    _stub_stop_timeout(monkeypatch, lambda engine: (_ for _ in ()).throw(RuntimeError("ThrottlingException")))
    row = _doctor_cloud_json(capsys)[("backend", "worker.grace")]
    assert row["skipped"] is False and row["ok"] is False and row["required"] is False
    assert "读不到云端为它设的停止宽限" in row["detail"] and "本机没有 novaact 的 worker，跳过" in row["detail"]


def test_doctor_cloud_worker_grace_shortfall_is_optional_gap_not_failure(monkeypatch, capsys):
    """下限 > 云端停止宽限 → `-`（可选能力缺失）、退出码仍 0：这是 ADR 0032 真容器校准结论 4 的既定接受
    （Fargate stopTimeout 有平台上限、Nova 的下限更大），不挡任何一次正常的批量运行，只让它看得见 + 给出抬高的办法。
    处置分两支：未顶到平台上限可抬、顶满即「已知并接受」——部署缺省就是平台硬顶，Nova 在正常后端上恒落这一格，
    只给「抬高」会让用户追一个已接受的残余。"""
    _fake_locator(monkeypatch, available=("novaact", "midscene"))
    _cloud_backend_ok(monkeypatch)
    _stub_stop_timeout(monkeypatch, 120)
    by = _doctor_cloud_json(capsys)
    row = by[("backend", "worker.grace")]
    assert row["ok"] is False and row["required"] is False  # 可选缺失：退出码 0（上面的 expect_rc）
    assert f"novaact: 收尾需 {FAKE_MIN_GRACE_S['novaact']:g}s > 云端停止宽限 120s" in row["detail"]
    assert "gherkai deploy --stop-timeout" in row["detail"]
    assert "已知并接受" in row["detail"]  # 顶满平台上限的那支处置也在（Nova 在部署缺省下恒落此格）
    assert f"midscene: 收尾需 {FAKE_MIN_GRACE_S['midscene']:g}s ≤" in row["detail"]  # 另一个引擎照过
    # 人读形态：- 标可选缺失（同 provider 段可选项）
    _stub_stop_timeout(monkeypatch, 120)
    assert m.main(["doctor", "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1"]) == 0
    assert re.search(r"-\s*│\s*backend\.worker\.grace", capsys.readouterr().out)   # 表格：结果列 - 与检查项同行


def test_doctor_cloud_worker_grace_shortfall_consequence_follows_engine(monkeypatch, capsys):
    """缺口的后果按引擎的下限构成分写：Nova 的下限是单个 AI 操作的上界加收尾余量，后果写「停止落在长操作早期」那一种
    极端情形；Midscene 的下限是收尾各段预算之和，与 AI 操作时长无关，不能套 Nova 的推导，只写收尾较慢时可能截断。"""
    _fake_locator(monkeypatch, available=("novaact", "midscene"))
    _cloud_backend_ok(monkeypatch)
    _stub_stop_timeout(monkeypatch, 20)  # 两个引擎的下限都大于它
    detail = _doctor_cloud_json(capsys)[("backend", "worker.grace")]["detail"]
    nova, mids = (next(p for p in detail.split("；") if p.startswith(f"{e}:")) for e in ("novaact", "midscene"))
    assert "AI 操作" in nova and "云端会话超时回收" in nova
    assert "AI 操作" not in mids and "浏览器会话" not in mids
    assert "可能在释放会话或保存产物之前被强制终止" in mids
    assert "gherkai deploy --stop-timeout" in mids  # 处置照给


def test_doctor_cloud_worker_grace_unset_stop_timeout_is_reported(monkeypatch, capsys):
    """云端没为该 container 设 stopTimeout（读回 None）→ 报「无从判断」，不当成 ✓（也不猜平台默认值）。"""
    _fake_locator(monkeypatch, available=("midscene",))
    _cloud_backend_ok(monkeypatch)
    _stub_stop_timeout(monkeypatch, None)
    row = _doctor_cloud_json(capsys)[("backend", "worker.grace")]
    assert row["ok"] is False and "云端没为它设停止宽限" in row["detail"]


def test_doctor_cloud_worker_grace_query_failure_lands_in_detail(monkeypatch, capsys):
    """取不到本机 worker 的下限（版本不一致的 worker 不认该入口 / 起不来）→ 转述诊断、不静默按「够用」放过；
    doctor 是只读自检，一行报到底，不像 run 那样以退出码 2 结束。"""
    _fake_locator(monkeypatch, available=("midscene",))
    _cloud_backend_ok(monkeypatch)
    monkeypatch.setattr(m.compose, "query_capabilities", lambda engine, **kw: (_ for _ in ()).throw(
        compose.WorkerSelfDescribeError(engine, 2, "unrecognized arguments: --capabilities", "能力自述")))
    monkeypatch.setattr(m.compose, "read_task_def_stop_timeout",
                        lambda *a, **kw: (_ for _ in ()).throw(AssertionError("下限都没问到，不该去 describe")))
    row = _doctor_cloud_json(capsys)[("backend", "worker.grace")]
    assert row["ok"] is False and "未能从本机 worker 取得收尾宽限" in row["detail"]


@pytest.mark.parametrize("stamp, cli_version, verdict, phrase", [
    (None, "1.4.1", compose.SKEW_WARN, "后端没有版本戳"),
    ("1.4.1", None, compose.SKEW_SKIP, "取不到自身版本"),
    ("1.4.1", "1.5.0.dev3+g1234567", compose.SKEW_SKIP, "不是正式发行版本"),
], ids=["stamp-missing", "cli-version-unknown", "not-a-release"])
def test_doctor_cloud_backend_version_warn_or_skip_verdict_is_a_checked_pass(
        monkeypatch, capsys, stamp, cli_version, verdict, phrase):
    """版本戳缺失、CLI 版本取不到、有一侧不是正式发行版本：读到或确认缺失版本戳并按规则得出了「提示、不拦」的结论，
    这一行是查过且通过（ok=true、skipped=false），不记未查。判定与提示语走真实的比对规则，只替掉读版本戳与取自身版本两处。"""
    _fake_locator(monkeypatch, available=("novaact", "midscene"))
    real_skew = m.compose.check_backend_skew
    _cloud_backend_ok(monkeypatch)
    _stub_stop_timeout(monkeypatch, 10_000)
    monkeypatch.setattr(m.compose, "check_backend_skew", real_skew)
    monkeypatch.setattr(m.compose, "read_backend_version", lambda **kw: stamp)
    monkeypatch.setattr(m, "_installed_version", lambda: cli_version)
    assert compose.check_version_skew(stamp, cli_version, prefix="vfy-")[0] == verdict  # 用例摆出的确实是这种判定
    row = _doctor_cloud_json(capsys)[("backend", "version")]
    assert row["ok"] is True and row["skipped"] is False and row["required"] is True
    assert phrase in row["detail"]


def test_doctor_cloud_backend_version_read_error_is_a_failure_not_unchecked(monkeypatch, capsys):
    """读版本戳本身出错（权限、网络）：检查失败而不是未查——ok=false、skipped=false，必修项失败以退出码 2 结束。"""
    _fake_locator(monkeypatch, available=("novaact", "midscene"))
    _cloud_backend_ok(monkeypatch)
    _stub_stop_timeout(monkeypatch, 10_000)
    monkeypatch.setattr(m.compose, "check_backend_skew",
                        lambda **kw: (_ for _ in ()).throw(RuntimeError("AccessDeniedException")))
    row = _doctor_cloud_json(capsys, expect_rc=2)[("backend", "version")]
    assert row["ok"] is False and row["skipped"] is False and row["required"] is True
    assert "读不到后端版本戳" in row["detail"] and "AccessDeniedException" in row["detail"]


def test_doctor_provider_section_comes_from_provider_doctor(monkeypatch, capsys):
    """装了 deploy-aws extra → 经 provider 接缝调它的 doctor(args)，required 项失败让整体以退出码 2 结束。"""
    _fake_locator(monkeypatch)

    class _Prov:
        name = "aws"
        def doctor(self, args):
            return [{"name": "node", "ok": False, "required": True, "detail": "找不到 node：需要 Node ≥ 22"},
                    {"name": "container-engine", "ok": False, "required": False, "detail": "docker 未装"}]
    monkeypatch.setattr(m._deploy, "provider_entry_points", lambda: [object()])
    monkeypatch.setattr(m._deploy, "resolve_provider", lambda name=None: (_Prov(), None))
    assert m.main(["doctor", "--json"]) == 2
    doc = json.loads(capsys.readouterr().out)
    by = {(c["section"], c["name"]): c for c in doc["checks"]}
    assert by[("provider", "node")]["required"] is True and not by[("provider", "node")]["ok"]
    assert by[("provider", "container-engine")]["required"] is False
    assert by[("provider", "node")]["skipped"] is False and by[("provider", "container-engine")]["skipped"] is False  # provider 不给 skipped 即 false
    # 人读形态：✗ 标必修、- 标可选缺失
    assert m.main(["doctor"]) == 2
    out = capsys.readouterr().out
    assert re.search(r"✗\s*│\s*provider\.node", out) and re.search(r"-\s*│\s*provider\.container-engine", out)
    assert "自检有失败项（✗ 为必修；- 为可选能力缺失；· 为未查，原因见说明列）" in out  # 本机 doctor 有云端两行未查
    assert "部署工具链有缺口" in out  # provider 段缺项单独点出，别混在通用的可选缺失里


def _provider_with_doctor(monkeypatch, checks):
    class _Prov:
        name = "aws"

        def doctor(self, args):
            return checks
    monkeypatch.setattr(m._deploy, "provider_entry_points", lambda: [object()])
    monkeypatch.setattr(m._deploy, "resolve_provider", lambda name=None: (_Prov(), None))


def test_doctor_provider_reported_skipped_is_kept_but_never_masks_a_failure(monkeypatch, capsys):
    """provider 自检项可带可选的 skipped（ADR 0037 决策 6 的契约）：给 true 且 ok=true 的记未查（required 一并落为 false）；
    同时给 skipped=true 与 ok=false 的按它报告的问题输出——skipped 记 false，ok 与 required 照它给的，免得标记盖住失败。"""
    _fake_locator(monkeypatch)
    _provider_with_doctor(monkeypatch, [
        {"name": "node", "ok": True, "required": True, "skipped": True, "detail": "未查：本机不部署"},
        {"name": "cdk", "ok": False, "required": True, "skipped": True, "detail": "找不到 cdk"},
        {"name": "container-engine", "ok": True, "detail": "docker 可用"}])
    assert m.main(["doctor", "--json"]) == 2  # cdk 那行仍是必修失败
    by = {(c["section"], c["name"]): c for c in json.loads(capsys.readouterr().out)["checks"]}
    assert by[("provider", "node")] == {"section": "provider", "name": "node", "ok": True, "required": False,
                                        "skipped": True, "detail": "未查：本机不部署"}
    assert by[("provider", "cdk")]["skipped"] is False and by[("provider", "cdk")]["ok"] is False
    assert by[("provider", "cdk")]["required"] is True
    assert by[("provider", "container-engine")]["skipped"] is False  # 不给即 false，入口补齐键
    assert m.main(["doctor"]) == 2
    out = capsys.readouterr().out
    assert re.search(r"·\s*│\s*provider\.node\s", out) and re.search(r"✗\s*│\s*provider\.cdk\s", out)


def test_doctor_provider_without_self_check_is_unchecked(monkeypatch, capsys):
    """装上的 provider 不提供自检 → 以 provider 名作项名的一行记未查（有没有装已查到，未查的是部署工具链自检）；
    自检本身抛错则是检查失败、不是未查。"""
    _fake_locator(monkeypatch)

    class _NoDoctor:
        name = "aws"
    monkeypatch.setattr(m._deploy, "provider_entry_points", lambda: [object()])
    monkeypatch.setattr(m._deploy, "resolve_provider", lambda name=None: (_NoDoctor(), None))
    assert m.main(["doctor", "--json"]) == 0
    row = {(c["section"], c["name"]): c for c in json.loads(capsys.readouterr().out)["checks"]}[("provider", "aws")]
    assert row["skipped"] is True and row["ok"] is True and row["required"] is False and "未提供自检" in row["detail"]

    class _Boom:
        name = "aws"

        def doctor(self, args):
            raise RuntimeError("node 版本解析失败")
    monkeypatch.setattr(m._deploy, "resolve_provider", lambda name=None: (_Boom(), None))
    assert m.main(["doctor", "--json"]) == 0
    row = {(c["section"], c["name"]): c for c in json.loads(capsys.readouterr().out)["checks"]}[("provider", "aws")]
    assert row["skipped"] is False and row["ok"] is False and "自检出错" in row["detail"]


def _every_row_checked(monkeypatch):
    """云端各项查过、provider 自检三项都给了结果、停止宽限比到了：整张表没有未查的行。"""
    _fake_locator(monkeypatch, available=("novaact", "midscene"))
    _cloud_backend_ok(monkeypatch)
    _stub_stop_timeout(monkeypatch, 10_000)
    _provider_with_doctor(monkeypatch, [{"name": n, "ok": True, "detail": "可用"} for n in ("node", "cdk", "container-engine")])


def test_doctor_tail_line_explains_unchecked_mark_only_when_present(monkeypatch, capsys):
    """尾行只在有未查行时点明 ·：表里没有未查的行时既没有 · 也不出这句。"""
    _every_row_checked(monkeypatch)
    by = _doctor_cloud_json(capsys)
    assert not any(c["skipped"] for c in by.values())
    assert m.main(["doctor", "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1"]) == 0
    out = capsys.readouterr().out
    assert "·" not in out and out.rstrip().endswith("自检通过")


def test_doctor_tail_line_on_failure_without_unchecked_rows_omits_unchecked_mark(monkeypatch, capsys):
    """必修项失败、但表里没有未查的行：退出码 2，尾行只注 ✗ 与 -，不出 · 的说明——这句跟着未查的行出现，不跟着失败出现。"""
    _every_row_checked(monkeypatch)
    monkeypatch.setattr(m.compose, "check_backend_skew",
                        lambda **kw: (compose.SKEW_BLOCK, "版本不一致：本机 CLI 新于后端", "1.3.0"))
    by = _doctor_cloud_json(capsys, expect_rc=2)
    assert by[("backend", "version")]["ok"] is False and by[("backend", "version")]["required"] is True
    assert not any(c["skipped"] for c in by.values())
    assert m.main(["doctor", "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1"]) == 2
    out = capsys.readouterr().out
    assert re.search(r"✗\s*│\s*backend\.version\s", out)
    assert "·" not in out and out.rstrip().endswith("自检有失败项（✗ 为必修；- 为可选能力缺失）")


_REAL_USE_COLOR = textui.use_color  # 导入本模块时取真实的颜色策略：autouse 夹具在每条用例里把它换成固定关色


def test_doctor_colors_unchecked_mark_dim_and_honours_no_color(monkeypatch, capsys):
    """颜色开着时（FORCE_COLOR）结果列按语义上色：· 淡显、✓ 绿；NO_COLOR 为非空值时（与 FORCE_COLOR 同时设也一样）不发
    任何 ANSI 序列，符号与文字照旧；颜色开着时 --json 也不带 ANSI、整段可解析。颜色策略用真实的那份。"""
    _fake_locator(monkeypatch)
    _no_provider(monkeypatch)
    monkeypatch.setattr(textui, "use_color", _REAL_USE_COLOR)
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("TERM", raising=False)
    monkeypatch.setenv("FORCE_COLOR", "1")
    unchecked = ("aws.identity", "backend.reachability", "provider.deploy-aws")
    assert m.main(["doctor"]) == 0
    out = capsys.readouterr().out

    def sgr(mark: str, row: str) -> str | None:
        """检查项为 row 的那一行里，结果列符号 mark 的 SGR 参数（如淡显为 2、绿为 32）。"""
        line = next(l for l in out.splitlines() if re.search(re.escape(row) + r"\s", l))
        hit = re.search(r"\x1b\[([0-9;]*)m" + re.escape(mark) + r"\x1b\[0m", line)
        return hit.group(1) if hit else None

    for row in unchecked:
        assert sgr("·", row) == "2", row
    assert sgr("✓", "engines.novaact") == "32"
    monkeypatch.setenv("NO_COLOR", "1")
    assert m.main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert "\x1b[" not in out
    for row in unchecked:
        assert re.search(r"·\s*│\s*" + re.escape(row) + r"\s", out), row
    assert re.search(r"✓\s*│\s*engines\.novaact\s", out) and "自检通过（· 为未查，原因见说明列）" in out
    monkeypatch.delenv("NO_COLOR")
    assert m.main(["doctor", "--json"]) == 0
    raw = capsys.readouterr().out
    assert "\x1b[" not in raw
    doc = json.loads(raw)
    assert {f"{c['section']}.{c['name']}" for c in doc["checks"] if c["skipped"]} == set(unchecked)


def test_doctor_cloud_credential_failure_is_required_and_exits_2(monkeypatch, capsys):
    """凭证探针抛 → aws.identity 必修失败、占位行 backend.reachability 记未查（ok=true、required=false：失败由上一行报，
    这一行不重复报问题）、以退出码 2 结束；不去碰后端。人读形态：上一行 ✗、占位行 ·。"""
    _fake_locator(monkeypatch); _no_provider(monkeypatch)
    monkeypatch.setattr(m.compose, "probe_aws_identity", lambda **kw: (_ for _ in ()).throw(RuntimeError("Unable to locate credentials")))
    touched = []
    monkeypatch.setattr(m.compose, "check_backend_skew", lambda **kw: touched.append("skew") or (compose.SKEW_OK, "", "1"))
    assert m.main(["doctor", "--prefix", "vfy-", "--region", "us-east-1", "--json"]) == 2
    doc = json.loads(capsys.readouterr().out)
    by = {(c["section"], c["name"]): c for c in doc["checks"]}
    assert doc["ok"] is False
    identity, reach = by[("aws", "identity")], by[("backend", "reachability")]
    assert not identity["ok"] and identity["required"] is True and identity["skipped"] is False
    assert "Unable to locate credentials" in identity["detail"]
    assert reach["skipped"] is True and reach["ok"] is True and reach["required"] is False
    assert reach["detail"] == "未查：AWS 身份检查未通过"
    assert touched == []
    assert m.main(["doctor", "--prefix", "vfy-", "--region", "us-east-1"]) == 2
    out = capsys.readouterr().out
    assert re.search(r"✗\s*│\s*aws\.identity\s", out) and re.search(r"·\s*│\s*backend\.reachability\s", out)


def test_doctor_cloud_without_region_fails_region_check_first(monkeypatch, capsys):
    """region 解析不出 → aws.region 必修失败、后端标未查，不会把 NoRegionError 误诊成「prefix 配错」。"""
    _fake_locator(monkeypatch); _no_provider(monkeypatch)
    monkeypatch.setattr(m.compose, "resolve_region", lambda r, p, **kw: None)
    monkeypatch.setattr(m.compose, "probe_aws_identity", lambda **kw: (_ for _ in ()).throw(AssertionError("不该被调")))
    assert m.main(["doctor", "--backend", "cloud", "--json"]) == 2
    by = {(c["section"], c["name"]): c for c in json.loads(capsys.readouterr().out)["checks"]}
    assert not by[("aws", "region")]["ok"] and "AWS_REGION" in by[("aws", "region")]["detail"]
    assert by[("aws", "region")]["required"] is True and by[("aws", "region")]["skipped"] is False
    reach = by[("backend", "reachability")]
    assert ("aws", "identity") not in by and reach["detail"] == "未查：region 未能解析"
    assert reach["skipped"] is True and reach["ok"] is True and reach["required"] is False


def test_doctor_cloud_profile_error_at_target_resolution_is_a_credential_failure(monkeypatch, capsys):
    """--profile 打错时 resolve_cloud_target 就抛异常（读 profile config）→ 与探针失败同一句诊断、以退出码 2 结束，不冒 traceback。"""
    _fake_locator(monkeypatch); _no_provider(monkeypatch)
    monkeypatch.setattr(m.compose, "resolve_cloud_target", lambda **kw: (_ for _ in ()).throw(RuntimeError("The config profile (nope) could not be found")))
    assert m.main(["doctor", "--prefix", "vfy-", "--profile", "nope", "--json"]) == 2
    by = {(c["section"], c["name"]): c for c in json.loads(capsys.readouterr().out)["checks"]}
    assert not by[("aws", "identity")]["ok"] and "凭证/region 不可用" in by[("aws", "identity")]["detail"]
    reach = by[("backend", "reachability")]
    assert reach["skipped"] is True and reach["ok"] is True and reach["required"] is False


def test_doctor_cloud_missing_default_pointer_is_required_failure(monkeypatch, capsys):
    _fake_locator(monkeypatch); _no_provider(monkeypatch)
    monkeypatch.setattr(m.compose, "probe_aws_identity", lambda **kw: {"account": "x", "arn": "arn", "region": kw["region"]})
    monkeypatch.setattr(m.compose, "check_backend_skew", lambda **kw: (compose.SKEW_OK, "", "1.4.1"))
    monkeypatch.setattr(m.compose, "preflight_cloud_resources", lambda **kw: None)
    monkeypatch.setattr(m.compose, "read_worker_default", lambda **kw: None)
    _stub_device_farm(monkeypatch)
    assert m.main(["doctor", "--prefix", "vfy-", "--region", "us-east-1", "--json"]) == 2
    by = {(c["section"], c["name"]): c for c in json.loads(capsys.readouterr().out)["checks"]}
    assert not by[("backend", "worker.default")]["ok"] and "gherkai deploy" in by[("backend", "worker.default")]["detail"]
    assert ("backend", "worker.any") not in by  # 指针都没有，不再逐引擎
    # 设备支持与 worker 镜像无关：默认指针缺失时设备两行照查（这里 SSM 没有项目 ARN，只出 devices.project 一行）
    assert ("backend", "devices.project") in by


# ---- doctor --backend cloud 的设备支持两行（ADR 0051 决策 6 泄漏护栏、决策 10；项名见 docs/internals/cli-json-contract.md）----

_DF_PROJECT = "arn:aws:devicefarm:us-west-2:123456789012:project:proj-1"
_DF_SESSION_QUEUED = "arn:aws:devicefarm:us-west-2:123456789012:session:proj-1/sess-1/00000"
_DF_SESSION_RUNNING = "arn:aws:devicefarm:us-west-2:123456789012:session:proj-1/sess-2/00000"


def _doctor_devices_cloud(monkeypatch, capsys, **stub):
    """云端 doctor 其余各项摆成 ok（本机不装 worker：停止宽限整行记未查、不去 describe），只留设备两行做变量；退出码恒为 0——
    设备行全是可选项，任何结果都不改退出码。返回（按 (section, name) 索引的检查项, 替身的调用记录）。"""
    _fake_locator(monkeypatch, available=())
    _cloud_backend_ok(monkeypatch)
    calls = _stub_device_farm(monkeypatch, **stub)
    return _doctor_cloud_json(capsys, expect_rc=0), calls


def test_doctor_cloud_devices_not_enabled_is_one_optional_row(monkeypatch, capsys):
    """SSM 没有项目 ARN → 只出 `backend.devices.project` 一行「部署未启用设备支持」，可选（`-`）、退出码不变，不去列举会话。
    SSM 读用后端的区域与 prefix（Device Farm 的固定区域只用于 Device Farm 客户端，SSM 仍在后端区域）。"""
    by, calls = _doctor_devices_cloud(monkeypatch, capsys)
    row = by[("backend", "devices.project")]
    assert row["ok"] is False and row["required"] is False
    assert "部署未启用设备支持" in row["detail"] and "gherkai deploy" in row["detail"]
    assert ("backend", "devices.sessions") not in by
    assert calls["list"] == []
    assert [(kw["prefix"], kw["region"]) for kw in calls["read"]] == [("vfy-", "us-east-1")]
    # 人读形态：结果列 - 与检查项同行；整体仍是「自检通过」
    _stub_device_farm(monkeypatch)
    assert m.main(["doctor", "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1"]) == 0
    out = capsys.readouterr().out
    assert re.search(r"-\s*│\s*backend\.devices\.project", out) and "自检通过" in out


def test_doctor_cloud_devices_lists_open_sessions_with_console_link_and_stop_command(monkeypatch, capsys):
    """有未到 COMPLETED 的会话（含排队中）→ `backend.devices.sessions` 逐条给会话 ARN、状态、控制台链接与 us-west-2 的停止命令；
    有残留只标 `-`（正在执行的 run 也有会话，doctor 判断不了是否仍在使用），退出码不变。控制台链接与 explain 同一份拼法。"""
    from datetime import datetime, timezone

    from gherkai_core.device_session import console_url
    from gherkai_runtime.devicefarm import OpenSession

    sessions = [OpenSession(arn=_DF_SESSION_QUEUED, name="gherkai-r1-s1", status="PENDING",
                            created=datetime(2026, 10, 29, 8, 0, tzinfo=timezone.utc)),
                OpenSession(arn=_DF_SESSION_RUNNING, name=None, status="RUNNING", created=None)]
    from dataclasses import replace
    real_resolve = m.compose.resolve_cloud_target
    monkeypatch.setattr(m.compose, "resolve_cloud_target", lambda **kw: replace(real_resolve(**kw), profile="team"))
    by, calls = _doctor_devices_cloud(monkeypatch, capsys, arn=_DF_PROJECT, sessions=sessions)
    project = by[("backend", "devices.project")]
    assert project["ok"] is True and project["required"] is False and _DF_PROJECT in project["detail"]
    row = by[("backend", "devices.sessions")]
    assert row["ok"] is False and row["required"] is False
    detail = row["detail"]
    assert "2 个" in detail and "PENDING" in detail and "RUNNING" in detail and "gherkai-r1-s1" in detail
    for arn in (_DF_SESSION_QUEUED, _DF_SESSION_RUNNING):
        # 停止命令带上 doctor 用的 profile：照抄执行时不落到另一套默认凭证
        assert f"aws devicefarm stop-remote-access-session --region us-west-2 --arn {arn} --profile team" in detail
        url = console_url(arn)
        assert url is not None and url in detail
    assert "https://us-west-2.console.aws.amazon.com/devicefarm/" in detail
    assert calls["list"] == [(_DF_PROJECT, "team")]  # 列举用 SSM 读到的项目 ARN，凭证沿用 doctor 的 profile
    assert [kw["profile"] for kw in calls["read"]] == ["team"]  # 读 SSM 记录同样沿用 doctor 的 profile


def test_doctor_cloud_devices_without_open_sessions_passes(monkeypatch, capsys):
    by, _calls = _doctor_devices_cloud(monkeypatch, capsys, arn=_DF_PROJECT, sessions=[])
    row = by[("backend", "devices.sessions")]
    assert row["ok"] is True and row["required"] is False and "没有未结束的远程访问会话" in row["detail"]


def test_doctor_cloud_devices_access_denied_is_its_own_row(monkeypatch, capsys):
    """当前凭证没有列举会话的权限 → `backend.devices.sessions` 单独一行说明缺哪项权限，可选、退出码不变；项目行照常通过。"""
    from gherkai_runtime.devicefarm import DeviceFarmAccessDenied

    by, _calls = _doctor_devices_cloud(monkeypatch, capsys, arn=_DF_PROJECT,
                                       list_error=DeviceFarmAccessDenied("ListRemoteAccessSessions", "AccessDeniedException"))
    assert by[("backend", "devices.project")]["ok"] is True
    row = by[("backend", "devices.sessions")]
    assert row["ok"] is False and row["required"] is False
    assert "权限" in row["detail"] and "devicefarm:ListRemoteAccessSessions" in row["detail"] and "us-west-2" in row["detail"]


def test_doctor_cloud_devices_other_failures_land_in_detail(monkeypatch, capsys):
    """其余失败（限流、网络、服务端故障）原样转述进对应那行，不当成「没有会话」或「未启用」：列举失败报在会话行；
    读 SSM 失败报在项目行、点名读的参数路径，且不再列举。两种都只标 `-`，与停止宽限一行的读失败同一处置。"""
    by, _calls = _doctor_devices_cloud(monkeypatch, capsys, arn=_DF_PROJECT, list_error=RuntimeError("Rate exceeded"))
    row = by[("backend", "devices.sessions")]
    assert row["ok"] is False and row["required"] is False and "Rate exceeded" in row["detail"]
    assert "没有未结束" not in row["detail"]
    assert "重新运行 doctor" in row["detail"] and "请部署方重新执行 gherkai deploy" in row["detail"]  # 怎么办

    by, calls = _doctor_devices_cloud(monkeypatch, capsys, arn=_DF_PROJECT, read_error=RuntimeError("Could not connect to the endpoint URL"))
    row = by[("backend", "devices.project")]
    assert row["ok"] is False and row["required"] is False
    assert "Could not connect" in row["detail"] and "/vfy-backend/device-farm-project" in row["detail"]
    assert "重新运行 doctor" in row["detail"] and "权限" not in row["detail"]  # 网络问题不说成权限问题
    assert "部署未启用设备支持" not in row["detail"]  # 读不到不等于没有
    assert ("backend", "devices.sessions") not in by and calls["list"] == []


def test_doctor_cloud_devices_project_read_access_denied_names_permission(monkeypatch, capsys):
    """读 SSM 项目记录遇无权限（自定义的窄 SSM 策略没覆盖新参数）：项目行点名 ssm:GetParameter 与参数路径，不把它说成凭证或网络
    问题，仍只标 `-`、不再列举。"""
    class _Denied(Exception):
        response = {"Error": {"Code": "AccessDeniedException", "Message": "not authorized to perform ssm:GetParameter"}}
        operation_name = "GetParameter"

    by, calls = _doctor_devices_cloud(monkeypatch, capsys, arn=_DF_PROJECT, read_error=_Denied("denied"))
    row = by[("backend", "devices.project")]
    assert row["ok"] is False and row["required"] is False
    assert "ssm:GetParameter" in row["detail"] and "/vfy-backend/device-farm-project" in row["detail"]
    assert "网络" not in row["detail"]
    assert ("backend", "devices.sessions") not in by and calls["list"] == []

    # 凭证链里 AssumeRole 被拒（profile 配置的角色）不是这个参数的权限问题：不列 ssm:GetParameter，按凭证与网络提示
    class _AssumeDenied(Exception):
        response = {"Error": {"Code": "AccessDenied", "Message": "not authorized to perform sts:AssumeRole"}}
        operation_name = "AssumeRole"

    by, _calls = _doctor_devices_cloud(monkeypatch, capsys, arn=_DF_PROJECT, read_error=_AssumeDenied("denied"))
    row = by[("backend", "devices.project")]
    assert row["ok"] is False and "ssm:GetParameter" not in row["detail"] and "凭证" in row["detail"]


def test_cli_help_does_not_load_device_farm_module_or_aws_sdk():
    """Device Farm 模块在 doctor 的设备两行里才导入：加载 CLI 与 `--help` 不为它拉起 AWS SDK。

    在子进程里往 `sys.modules` 放毒化条目（值为 None 时 import 立即失败），而不是事后断言「不在 sys.modules 里」——本会话的其他用例早已
    import 过它们。"""
    import subprocess
    import sys

    code = ("import sys\n"
            "for name in ('boto3', 'botocore'):\n"
            "    sys.modules[name] = None\n"
            "from gherkai_cli import __main__ as m\n"
            "try:\n"
            "    m.main(['--help'])\n"
            "except SystemExit as e:\n"
            "    assert e.code == 0, e.code\n"
            "assert 'gherkai_runtime.devicefarm' not in sys.modules\n")
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr


def test_doctor_provider_installed_but_broken_is_required_failure(monkeypatch, capsys):
    """装了 deploy-aws extra 却加载失败（半装/版本不匹配）→ 必修失败：明确装了的东西坏了；靠 entry point 结构判、不靠文案前缀。"""
    _fake_locator(monkeypatch)
    monkeypatch.setattr(m._deploy, "provider_entry_points", lambda: [object()])
    monkeypatch.setattr(m._deploy, "resolve_provider", lambda name=None: (None, "部署 provider 'aws' 加载失败（entry point x）：ImportError"))
    assert m.main(["doctor", "--json"]) == 2
    by = {(c["section"], c["name"]): c for c in json.loads(capsys.readouterr().out)["checks"]}
    assert not by[("provider", "deploy-aws")]["ok"] and by[("provider", "deploy-aws")]["required"] is True
    assert by[("provider", "deploy-aws")]["skipped"] is False  # 装了却坏了是查过的失败，不是未查
    # 装了多个未指名：不是故障，只是不替用户猜哪个云——部署工具链的自检没有执行，记未查
    monkeypatch.setattr(m._deploy, "provider_entry_points", lambda: [object(), object()])
    monkeypatch.setattr(m._deploy, "resolve_provider", lambda name=None: (None, "装了多个部署 provider（aws, gcp）：用 --provider <名> 指定其一。"))
    assert m.main(["doctor", "--json"]) == 0
    row = {(c["section"], c["name"]): c for c in json.loads(capsys.readouterr().out)["checks"]}[("provider", "deploy-aws")]
    assert row["skipped"] is True and row["ok"] is True and row["required"] is False and "多个部署 provider" in row["detail"]


def test_doctor_runs_worker_self_describe_even_without_steps_dir(monkeypatch, capsys):
    """无 steps/ 目录也对可用引擎执行一次自述（验 worker 起得来），但只作可选项：自述失败不改退出码。"""
    _fake_locator(monkeypatch); _no_provider(monkeypatch)
    monkeypatch.chdir(monkeypatch._temp_dir if hasattr(monkeypatch, "_temp_dir") else ".")
    monkeypatch.delenv("GHERKAI_STEPS_DIR", raising=False)
    monkeypatch.setattr(m.compose, "query_capabilities", lambda engine, *, steps_dir=None, timeout_s=60.0: (_ for _ in ()).throw(RuntimeError("worker 起不来")))
    assert m.main(["doctor", "--json"]) == 0
    by = {(c["section"], c["name"]): c for c in json.loads(capsys.readouterr().out)["checks"]}
    assert not by[("steps", "load.novaact")]["ok"] and by[("steps", "load.novaact")]["required"] is False


def test_doctor_reports_worker_self_reported_model(tmp_path, monkeypatch, capsys):
    """doctor 出一行 engines.model.<engine>：模型 id 取自那份能力自述对象（ADR 0036「5.」的 `model_id` 键），
    让 worker 侧 env 覆盖过默认模型的机器一眼可见（ADR 0004「模型版本选择策略」）。

    纯展示故 required=False（模型不是「装没装」那种缺口）；不额外 spawn——与 steps.load 那行共用同一次自述
    （本用例的替身在 conftest 的假自述之上只加计数）。
    """
    _fake_locator(monkeypatch, available=("novaact", "midscene")); _no_provider(monkeypatch)
    monkeypatch.delenv("GHERKAI_STEPS_DIR", raising=False); monkeypatch.chdir(tmp_path)  # 不受运行测试的 cwd 里有没有 steps/ 影响
    asked: list[str] = []
    stubbed = compose.query_capabilities  # conftest autouse 的确定性假替身
    monkeypatch.setattr(m.compose, "query_capabilities",
                        lambda engine, **kw: asked.append(engine) or stubbed(engine, **kw))
    assert m.main(["doctor", "--json"]) == 0
    by = {(c["section"], c["name"]): c for c in json.loads(capsys.readouterr().out)["checks"]}
    row = by[("engines", "model.novaact")]
    assert row["ok"] is True and row["required"] is False and FAKE_MODEL_ID["novaact"] in row["detail"]
    assert FAKE_MODEL_ID["midscene"] in by[("engines", "model.midscene")]["detail"]
    assert sorted(asked) == ["midscene", "novaact"]  # 每引擎仍只问一次自述（模型行不是第二次 spawn）

    assert m.main(["doctor"]) == 0  # 文本视图同一行
    out = capsys.readouterr().out
    assert re.search(r"✓\s*│\s*engines\.model\.novaact\s*│\s*模型 " + re.escape(FAKE_MODEL_ID["novaact"]) + r"（本机 worker 自报）", out)  # 同一行
    # 表格各行按 add 的插入顺序排列，故模型行须位于 engines 段内（steps 段之前），否则两段交错
    assert out.index("engines.model.novaact") < out.index("steps.dir")


def test_doctor_reports_worker_targets_with_session_limit_minutes(tmp_path, monkeypatch, capsys):
    """doctor 出一行 engines.targets.<engine>（ADR 0049 决策 6）：目标清单取自同一次自述、纯展示（required=False）；带
    max_session_s 的目标附分钟数；不展示 requires；worker 只声明桌面网页时显示桌面网页；不支持设备不算失败。"""
    _fake_locator(monkeypatch, available=("novaact", "midscene")); _no_provider(monkeypatch)
    monkeypatch.delenv("GHERKAI_STEPS_DIR", raising=False); monkeypatch.chdir(tmp_path)
    stubbed = compose.query_capabilities  # conftest 的假自述：顶层 targets 只有桌面网页

    def with_targets(engine, **kw):
        caps = dict(stubbed(engine, **kw))
        if engine == "midscene":
            caps["targets"] = [{"device": "desktop", "ui_kinds": ["web"]},
                               {"device": "android", "ui_kinds": ["web", "app"], "max_session_s": 8880}]
            caps["deterministic_steps"] = [dict(caps["deterministic_steps"][0],
                                                targets=[{"device": "android", "ui_kinds": ["web"], "requires": ["web_context"]}])]
        return caps

    monkeypatch.setattr(m.compose, "query_capabilities", with_targets)
    assert m.main(["doctor", "--json"]) == 0
    by = {(c["section"], c["name"]): c for c in json.loads(capsys.readouterr().out)["checks"]}
    nova = by[("engines", "targets.novaact")]
    assert nova["ok"] is True and nova["required"] is False and nova["detail"] == "支持的测试目标：桌面网页（本机 worker 自报）"
    mid = by[("engines", "targets.midscene")]
    assert mid["ok"] is True and mid["required"] is False  # 不支持设备不算失败、支持设备也只是展示
    assert "桌面网页、Android 网页、Android 应用（会话上限 148 分钟）" in mid["detail"]
    assert m.render.targets_label([{"device": "ios", "ui_kinds": ["web"], "max_session_s": 1000}], with_session_limit=True) == "iOS 网页（会话上限 16.7 分钟）"
    assert m.render.targets_label([], with_session_limit=True) == "无"  # worker 声明不支持任何目标
    assert m.main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert out.index("engines.targets.novaact") < out.index("steps.dir")  # 仍在 engines 段内


def test_doctor_omits_model_row_when_self_describe_fails(tmp_path, monkeypatch, capsys):
    """自述失败（版本不一致 / 起不来 / 使用方 steps 报错）→ **没有** 模型行：模型未知就不出这一行，
    不拿占位符冒充事实（失败本身由 steps.load 那行报）。"""
    _fake_locator(monkeypatch); _no_provider(monkeypatch)
    monkeypatch.delenv("GHERKAI_STEPS_DIR", raising=False); monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(m.compose, "query_capabilities", lambda engine, **kw: (_ for _ in ()).throw(
        compose.WorkerSelfDescribeError(engine, 2, "unrecognized arguments: --capabilities", "能力自述")))
    assert m.main(["doctor", "--json"]) == 0  # 无 steps/ 目录 → 自述失败只是可选项
    by = {(c["section"], c["name"]): c for c in json.loads(capsys.readouterr().out)["checks"]}
    assert ("engines", "model.novaact") not in by
    assert ("engines", "targets.novaact") not in by  # 目标行与模型行同一口径：自述失败就不出
    assert not by[("steps", "load.novaact")]["ok"]


def test_doctor_steps_dir_error_reason_lands_in_json_detail(tmp_path, monkeypatch, capsys):
    _fake_locator(monkeypatch); _no_provider(monkeypatch)
    assert m.main(["doctor", "--json", "--steps-dir", str(tmp_path / "nope")]) == 2
    by = {(c["section"], c["name"]): c for c in json.loads(capsys.readouterr().out)["checks"]}
    assert not by[("steps", "dir")]["ok"] and "不是目录" in by[("steps", "dir")]["detail"] and "nope" in by[("steps", "dir")]["detail"]


def test_scenario_digit_selector_is_line_only_and_outline_declaration_line_selects_all_examples(tmp_path, capsys):
    """纯数字 SEL 只当行号、不回落标题子串（标题「重试3次」不被 --scenario 3 连带选中）；Scenario Outline 的 id 是
    <uri>:<声明行>:<数据行>，给声明行选中全部 example。"""
    p = tmp_path / "o.feature"
    p.write_text("Feature: F\n"
                 "  Scenario Outline: 下单 <n>\n    When \"买 <n> 件\"\n    Examples:\n      | n |\n      | 1 |\n      | 2 |\n"
                 "  Scenario: 重试3次\n    When \"x\"\n", encoding="utf-8")
    assert m.main(["plan", str(p), "--json", "--scenario", "2"]) == 0
    assert _plan_names(capsys) == ["下单 1 [@6]", "下单 2 [@7]"]  # 声明行 2 → 两条 example（标题带 Examples 行标记）；「重试3次」不因含数字被带上
    assert m.main(["plan", str(p), "--json", "--scenario", "3"]) == 2  # 行 3 是 When 行、不是 scenario；不回落成标题子串
    assert "没有 scenario 匹配" in capsys.readouterr().err
    assert m.main(["plan", str(p), "--json", "--scenario", "重试"]) == 0
    assert _plan_names(capsys) == ["重试3次"]


def test_empty_selection_flag_values_are_rejected(tmp_path, capsys):
    feat = _tagged_feature(tmp_path)
    assert m.main(["plan", str(feat), "--tags", ""]) == 2 and "--tags 的值不能为空" in capsys.readouterr().err
    assert m.main(["plan", str(feat), "--tags", "@,"]) == 2
    assert m.main(["plan", str(feat), "--scenario", " "]) == 2 and "--scenario 的值不能为空" in capsys.readouterr().err


def test_scope_filter_selects_whole_named_scope_by_id(tmp_path, capsys):
    """--scope 即报告里的 scope_id：named scope 的名字选中整个 scope（两条都运行），未标 scope 的用 <文件>:<行>；
    与 --scenario 同给为且。plan 文本里 named scope 不再重复打 (name=…)。"""
    p = tmp_path / "s.feature"
    p.write_text("Feature: F\n"
                 "  @scope:browse\n  Scenario: 进入\n    When \"a\"\n"
                 "  @scope:browse\n  Scenario: 停留\n    When \"b\"\n"
                 "  Scenario: 独立\n    When \"c\"\n", encoding="utf-8")
    assert m.main(["plan", str(p), "--json", "--scope", "browse"]) == 0
    assert _plan_names(capsys) == ["停留", "进入"]
    assert m.main(["plan", str(p), "--json", "--scope", f"{p}:8"]) == 0   # 未标 scope：scope_id 形如 uri:line
    assert _plan_names(capsys) == ["独立"]
    assert m.main(["plan", str(p), "--json", "--scope", "browse", "--scenario", "停留"]) == 0
    assert _plan_names(capsys) == ["停留"]
    assert m.main(["plan", str(p), "--scope", "browse"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("plan（用例预检") and "job scope='browse' engine=" in out and "(name=" not in out
    assert m.main(["plan", str(p), "--scope", ""]) == 2 and "--scope 的值不能为空" in capsys.readouterr().err


# ---- explain（ADR 0042 决策四）：判定明细 + step 级机读证据的合成视图 ----
# 夹具照 ADR 的文本样例搭（同一份 run 喂各用例）：一个 scope、两条 scenario——第一条 failed 且第 3 步无记录
# （worker 被中止的形态）、第二条 error 后短路。evidence 是真文件、ref 是真 file:// URI（读路径全程真实运行）。

def _evidence_fixture(*, step_index=2, thought="I am on the login page.\n看到「密码错误」。Returning false.",
                      screenshot="file:///tmp/act-0-frame-4.jpg", schema_version=1) -> dict:
    return {
        "schema_version": schema_version, "engine": "novaact",
        "scope_id": "features/login.feature:6", "scenario_id": "features/login.feature:12",
        "step_index": step_index, "step": {"keyword": "Then", "text": "页面显示「登录成功」"},
        "status": "failed", "message": "AI 断言未过多数票（0/1）：页面显示「登录成功」",
        "acts": [{
            "index": 0, "prompt": "页面显示「登录成功」", "vote": False, "url": "https://app.example.com/login",
            "frames": [
                {"url": "https://app.example.com", "thought": None,
                 "actions": [{"name": "agentClick", "args": {"box": "1,2"}}], "screenshot": None},
                {"url": "https://app.example.com/login", "thought": thought,
                 "actions": [{"name": "takeObservation", "args": {}}], "screenshot": screenshot},
            ],
            "result": {"value": "false"}, "error": None, "time_worked_s": 9.8,
        }],
    }


def _explain_job(*, scope_id="features/login.feature:6"):
    from gherkai_core.model import Job, Scenario, Step
    s1 = (Step(0, "Given", '"https://app.example.com/login"'),
          Step(1, "When", "输入用户名「alice」与密码「wrong」"),
          Step(2, "Then", "页面显示「登录成功」"),
          Step(3, "When", "点击「退出」"))
    s2 = (Step(0, "Given", '"https://app.example.com/login"'), Step(1, "Then", "页面提示「账户已锁定」"))
    return Job(scope_id=scope_id, scope_name="登录", engine="novaact",
               scenarios=(Scenario(id="features/login.feature:12", name="密码错误时不放行", steps=s1),
                          Scenario(id="features/login.feature:20", name="锁定账户提示", steps=s2)), timeout_s=300.0)


def _explain_run(tmp_path, *, evidence=..., run_status=None, with_results=True, job_only=False,
                 evidence_text=None, job=None):
    """在 tmp_path/reports 下搭一个 run：run_meta/run_state + 一份 JobResult（+ 真 evidence.json）。

    evidence=None → step 2 不挂 evidence ref（no_ref）；evidence_text 给非 JSON 串 → unreadable；
    with_results=False → 只落 run_meta/run_state（后台 run 还没有 job 得出结果时的零文件形态）；
    job_only=True → JobResult 有 job 级判定但零 step 记录（worker 没起来/起来就被掐）；
    job 给了就替换默认的 `_explain_job()`（scenario id 与 step 数须与之一致，判定记录照默认那份搭）。
    """
    from gherkai_core.model import (JobResult, JobState, ReportRef, RunMeta, RunState, ScenarioResult,
                                    Status as S, StepResult, Votes)
    root = tmp_path / "reports"
    run_id = "20260910T080630Z-9fa261"
    job = job or _explain_job()
    refs2 = [ReportRef(kind="trajectory", ref="file:///tmp/act-0.html", label="act 0")]
    if evidence is not ... or evidence_text is not None:
        payload = evidence_text if evidence_text is not None else json.dumps(evidence, ensure_ascii=False)
    else:
        payload = json.dumps(_evidence_fixture(), ensure_ascii=False)
    ev_path = None  # 证据文件在建 run 之后写进 run 目录：建 run 要求以 run 标识命名的位置还没有非空目录
    if evidence is not None or evidence_text is not None:
        ev_path = root / run_id / "evidence" / "evidence.json"
        refs2.insert(0, ReportRef(kind="evidence", ref=ev_path.resolve().as_uri(), label="evidence"))
    scenarios = [] if job_only else [
        ScenarioResult(scenario_id="features/login.feature:12", status=S.FAILED, duration_ms=22600.0, steps=[
            StepResult(index=0, status=S.PASSED, duration_ms=1100.0),
            StepResult(index=1, status=S.PASSED, duration_ms=9400.0),
            StepResult(index=2, status=S.FAILED, duration_ms=12100.0, votes=Votes(yes=0, total=1),
                       error_type="assertion_failed",
                       message="AI 断言未过多数票（0/1）：页面显示「登录成功」", report_refs=tuple(refs2)),
        ]),  # step 3 无记录（被中止：scenario_done 没到，这一步的记录不进 jobs/*.json）
        ScenarioResult(scenario_id="features/login.feature:20", status=S.ERROR, steps=[
            StepResult(index=0, status=S.ERROR, error_type="network_error",
                       message="建连失败（网络/SSL 瞬时故障）：timed out",
                       report_refs=(ReportRef(kind="trajectory", ref="file:///tmp/act-1.html", label="act 0"),)),
            StepResult(index=1, status=S.SKIPPED, shortcircuited=True),
        ]),
    ]
    jr = JobResult(job=job, status=S.ABORTED if job_only else S.FAILED, scenarios=scenarios,
                   session_id="01a0deadbeef", error_type="timeout" if job_only else None,
                   message="job 墙钟预算用尽被停" if job_only else None,
                   report_refs=(ReportRef(kind="summary", ref="file:///tmp/summary.json", label="summary"),))
    st = run_status or (S.ABORTED if job_only else S.FAILED)
    run_store, result_store, _rp, _mk = compose.build_local_stores(report_dir=str(root), lock_holder=compose.process_lock_holder())
    # 运行态经写入口得到，写序同写入方：建 run（全 pending）→ 执行中的写记 running（run 随之为 running）→ 先存明细，终态写再记下这个
    # job 的终态并点名那一份（只有一个 job，run 随之成为终态）。run_status 给 running 时明细已存下而终态还没有写，那一份不被点名
    run_store.create_run(RunMeta(run_id=run_id, created_at="2026-09-10T08:06:30Z", jobs=(job,), deadline_at="2026-01-01T01:00:00+00:00"),
                         RunState(run_id=run_id, status=S.PENDING, jobs={job.scope_id: JobState(job.scope_id, S.PENDING)},
                                  started_at="t0"))
    if ev_path is not None:
        ev_path.parent.mkdir(parents=True)
        ev_path.write_text(payload, encoding="utf-8")
    result_id = _save_detail(result_store, run_id, jr) if with_results else None
    if st == S.RUNNING:
        run_store.update_job_state(run_id, JobState(job.scope_id, S.RUNNING))
    elif st in m.TERMINAL_STATUSES:
        assert run_store.commit_job_states(run_id, [JobState(job.scope_id, st, result_id=result_id)],
                                           ended_at="t9") == CommitOutcome.ENDED_RUN
    return root, run_id


def _save_detail(result_store, run_id: str, jr) -> str:
    """像写入方那样存一份明细：生成一个标识、存成带它的一份，返回标识（终态写据它点名）。"""
    from gherkai_core.named_details import new_result_id

    result_id = new_result_id()
    result_store.save_job_result(run_id, result_id, jr)
    return result_id


def _explain(capsys, root, run_id, *flags):
    rc = m.main(["explain", run_id, *flags, "--report-dir", str(root)])
    cap = capsys.readouterr()
    return rc, cap.out, cap.err


def test_explain_text_renders_reason_thought_screenshot_and_gaps(tmp_path, capsys):
    """文本形态（ADR 0042 决策四）：原因行、末个带推理的 frame 的 think + 截图、被省略 frame 计数、
    短路旁注只在 shortcircuited 的 step 上、无记录 step、证据缺失的 step 打「无 AI 证据」+ 兜底 ref。"""
    root, run_id = _explain_run(tmp_path)
    rc, out, err = _explain(capsys, root, run_id)
    assert rc == 0  # 证据渲染器不表判定：run 判 failed 也以退出码 0 结束
    assert f"run {run_id}  status=failed" in out
    assert "scope features/login.feature:6  engine=novaact  status=failed  session=01a0deadbeef" in out
    assert "scenario features/login.feature:12  密码错误时不放行  failed" in out
    assert "step 2  Then 页面显示「登录成功」  failed  votes 0/1  (12.1s)" in out
    assert "message: AI 断言未过多数票（0/1）：页面显示「登录成功」" in out
    assert "act 0  vote=false  url=https://app.example.com/login" in out
    assert "thought: I am on the login page." in out and "Returning false." in out
    assert "screenshot: file:///tmp/act-0-frame-4.jpg" in out
    assert "其余 1 个 frame 已省略（--full 查看）" in out          # 两个 frame，只渲染了带推理的那个
    assert "step 3  When 点击「退出」  无记录（未执行或未上报）" in out
    assert "step 0  Given \"https://app.example.com/login\"  error  (network_error)" in out
    assert "无 AI 证据" in out and "report（act 0）: file:///tmp/act-1.html" in out   # 缺证据 → 兜底指针
    marker = "⚠ 因前置 step error 被跳过（未执行）"
    assert out.count(marker) == 1 and marker in out.split("step 1  Then 页面提示「账户已锁定」")[1]
    assert "passed  (1.1s)" in out and "think" not in out.split("step 0  Given")[1].split("step 1")[0]
    assert err == ""  # 终态 run：无提示行


def test_explain_json_is_single_document_with_record_and_evidence_gaps(tmp_path, capsys):
    """--json：stdout 只有一个可严格解析的文档；无记录 step 给 status=null + record_missing；
    有记录但没挂 evidence 的给 evidence_missing=no_ref；挂了的内嵌 evidence 全文。"""
    root, run_id = _explain_run(tmp_path)
    rc, out, err = _explain(capsys, root, run_id, "--json")
    assert rc == 0
    doc = json.loads(out)
    assert doc["run_id"] == run_id and doc["status"] == "failed" and len(doc["scopes"]) == 1
    sc = doc["scopes"][0]
    assert sc["scope_id"] == "features/login.feature:6" and sc["engine"] == "novaact"
    assert sc["session_id"] == "01a0deadbeef" and sc["report_refs"][0]["kind"] == "summary"
    s1, s2 = sc["scenarios"]
    assert [st["record_missing"] for st in s1["steps"]] == [False, False, False, True]
    assert s1["steps"][3]["status"] is None and s1["steps"][3]["evidence_missing"] == "no_ref"
    assert s1["steps"][0]["evidence_missing"] == "no_ref" and s1["steps"][0]["evidence"] is None
    ev = s1["steps"][2]["evidence"]
    assert s1["steps"][2]["evidence_missing"] is None and ev["schema_version"] == 1
    assert ev["acts"][0]["vote"] is False and ev["acts"][0]["frames"][1]["thought"].startswith("I am on")
    assert s2["steps"][1]["shortcircuited"] is True and s2["steps"][1]["status"] == "skipped"
    assert s2["steps"][0]["message"].startswith("建连失败")
    assert err == ""


def test_explain_scenario_selector_matches_id_line_title_and_ors(tmp_path, capsys):
    """--scenario：id 全等 / 行号（scenario_id 尾部数字段）/ 标题子串三种匹配，可重复且彼此为或。"""
    root, run_id = _explain_run(tmp_path)
    for sel in ("features/login.feature:12", "12", "密码错误"):
        rc, out, _ = _explain(capsys, root, run_id, "--scenario", sel)
        assert rc == 0 and "features/login.feature:12" in out and "features/login.feature:20" not in out
    rc, out, _ = _explain(capsys, root, run_id, "--scenario", "12", "--scenario", "锁定")
    assert rc == 0 and "features/login.feature:12" in out and "features/login.feature:20" in out
    rc, _out, err = _explain(capsys, root, run_id, "--scenario", "不存在的标题")
    assert rc == 2 and "没有 scenario 匹配" in err and "features/login.feature:20  锁定账户提示  2 step" in err
    assert m.main(["explain", run_id, "--report-dir", str(root), "--scenario", " "]) == 2


def test_explain_step_needs_scenario_and_lists_candidates_when_absent(tmp_path, capsys):
    """--step 单给即以退出码 2 结束（步号没有归属）；命中的 scenario 都没有第 N 步 → 同样以退出码 2 结束并列出候选 id 与步数；
    正常时只渲染每条命中 scenario 的第 N 步。"""
    root, run_id = _explain_run(tmp_path)
    rc, _out, err = _explain(capsys, root, run_id, "--step", "2")
    assert rc == 2 and "--step 要和 --scenario 一起给" in err
    rc, _out, err = _explain(capsys, root, run_id, "--scenario", "12", "--step", "9")
    assert rc == 2 and "都没有第 9 步" in err and "features/login.feature:12  4 step" in err
    rc, out, _ = _explain(capsys, root, run_id, "--scenario", "12", "--step", "2")
    assert rc == 0 and "step 2  Then" in out and "step 0  Given" not in out


def test_explain_named_step_expands_even_when_passed(tmp_path, capsys):
    """显式 --step 点名的那一步即展开证据（点名就是想看），不必再给 --all；默认视图对同一 passed 步仍不展开。"""
    root, run_id = _explain_run(tmp_path)
    _rc, out, _ = _explain(capsys, root, run_id)
    assert "step 0  Given" in out and "无 AI 证据" not in out.split("step 0  Given")[1].split("step 1")[0]
    rc, out, _ = _explain(capsys, root, run_id, "--scenario", "12", "--step", "0")
    assert rc == 0 and "step 0  Given" in out
    block = out.split("step 0  Given")[1]
    assert ("无 AI 证据" in block) or ("act 0" in block)  # 展开了（该步有无 AI 证据两种形态都算展开）


def test_explain_all_expands_passed_and_full_drops_the_text_budget(tmp_path, capsys):
    """--all 也展开 passed step；--full 逐 frame 全文（省略计数消失、无推理的 frame 也现身）。"""
    root, run_id = _explain_run(tmp_path)
    _rc, out, _ = _explain(capsys, root, run_id, "--full")
    assert "其余" not in out and "frame 0  url=https://app.example.com" in out and "frame 1" in out
    _rc, out, _ = _explain(capsys, root, run_id)
    assert "step 0  Given \"https://app.example.com/login\"  passed  (1.1s)" in out
    passed_block = out.split("step 0  Given")[1].split("step 1")[0]
    assert "无 AI 证据" not in passed_block           # 默认不展开 passed
    _rc, out, _ = _explain(capsys, root, run_id, "--all")
    assert "无 AI 证据" in out.split("step 0  Given")[1].split("step 1")[0]


def test_explain_masks_tunnel_credentials_in_text_and_json(tmp_path, capsys):
    """隧道模式下定义里的 step 文本与证据里的地址、指令都带凭据：explain 两种形态都只显示 `https://***@…`
    （ADR 0035 决策 5）。落盘的 run 定义与证据文件不在本用例的断言范围内。"""
    import dataclasses

    cred = "https://u1:p1@h.example/"
    base = _explain_job()
    open_step = f'打开 "{cred}login"'
    scenarios = tuple(
        dataclasses.replace(sc, steps=(dataclasses.replace(sc.steps[0], text=open_step), *sc.steps[1:]))
        for sc in base.scenarios)
    job = dataclasses.replace(base, scenarios=scenarios)
    evidence = _evidence_fixture(thought=f"I am on {cred}login.\n看到「密码错误」。Returning false.")
    act = evidence["acts"][0]
    act["url"] = f"{cred}login"
    act["prompt"] = f"确认 {cred}login 显示「登录成功」"
    for fr in act["frames"]:
        fr["url"] = f"{cred}login"
    root, run_id = _explain_run(tmp_path, evidence=evidence, job=job)

    rc, out, _ = _explain(capsys, root, run_id)
    assert rc == 0
    assert "u1:p1@" not in out
    assert "url=https://***@h.example/login" in out                       # 证据里的页面地址
    assert 'step 0  Given 打开 "https://***@h.example/login"' in out        # 定义里的 step 文本

    rc, out, _ = _explain(capsys, root, run_id, "--json")
    assert rc == 0
    assert "u1:p1@" not in out
    doc = json.loads(out)
    s1 = doc["scopes"][0]["scenarios"][0]
    assert s1["steps"][0]["text"] == '打开 "https://***@h.example/login"'
    ev = s1["steps"][2]["evidence"]
    assert ev["acts"][0]["url"] == "https://***@h.example/login"
    assert ev["acts"][0]["prompt"] == "确认 https://***@h.example/login 显示「登录成功」"
    assert ev["acts"][0]["frames"][1]["thought"].startswith("I am on https://***@h.example/login.")


def test_explain_long_thought_is_truncated_with_pointer(tmp_path, capsys):
    """单段推理超预算 → 截断并指出完整内容在哪（--json 或那份 evidence.json）；--full 不截断。"""
    root, run_id = _explain_run(tmp_path, evidence=_evidence_fixture(thought="推" * 1000))
    _rc, out, _ = _explain(capsys, root, run_id)
    assert "…（已截断；完整内容见 --json 或 evidence.json：file://" in out
    assert out.count("推") == 800
    _rc, out, _ = _explain(capsys, root, run_id, "--full")
    assert "已截断" not in out and out.count("推") == 1000


def test_explain_unreadable_and_unsupported_evidence(tmp_path, capsys):
    """读不到/解不开 → unreadable；schema_version 不认识 → unsupported_schema。两者都不影响退出码（0）。"""
    root, run_id = _explain_run(tmp_path, evidence_text="{ 不是 JSON")
    rc, out, _ = _explain(capsys, root, run_id)
    assert rc == 0 and "AI 证据读不到" in out
    rc, out, _ = _explain(capsys, root, run_id, "--json")
    assert rc == 0 and json.loads(out)["scopes"][0]["scenarios"][0]["steps"][2]["evidence_missing"] == "unreadable"
    root, run_id = _explain_run(tmp_path / "v2", evidence=_evidence_fixture(schema_version=99))
    rc, out, _ = _explain(capsys, root, run_id)
    assert rc == 0 and "认不出" in out
    rc, out, _ = _explain(capsys, root, run_id, "--json")
    assert json.loads(out)["scopes"][0]["scenarios"][0]["steps"][2]["evidence_missing"] == "unsupported_schema"


def test_explain_unknown_run_and_scope_exit_2(tmp_path, capsys):
    root, run_id = _explain_run(tmp_path)
    assert m.main(["explain", "no-such-run", "--report-dir", str(root)]) == 2
    assert "未找到 run" in capsys.readouterr().err
    assert m.main(["explain", run_id, "no-such-scope", "--report-dir", str(root)]) == 2
    err = capsys.readouterr().err
    assert "未找到 scope" in err and "features/login.feature:6" in err   # 列出这个 run 的 scope
    assert m.main(["explain", run_id, "features/login.feature:6", "--report-dir", str(root)]) == 0


@pytest.mark.parametrize("command", ["status", "explain"])
def test_an_identifier_too_long_for_a_directory_name_is_an_unknown_run(command, tmp_path, capsys):
    """run 标识长到不能作一层目录名（按文件系统编码超过 255 字节，如手误粘贴了一大段）：与不存在的 run 一样给「未找到 run」、
    退出码 2，不以「文件名太长」的回溯结束。报告目录存在，读入口确实会去找这个名字。"""
    root = tmp_path / "reports"
    root.mkdir()
    long_id = "a" * 300
    assert m.main([command, long_id, "--report-dir", str(root)]) == 2
    assert f"未找到 run：{long_id}" in capsys.readouterr().err


def test_explain_named_scope_ended_without_detail_shows_the_recorded_status(tmp_path, capsys):
    """点名的 job 已结束而没有判定明细（a 出错之后 b 没有启动，由 fail-fast 那一行的结束写记 skipped）：按运行态给出状态与说明，
    退出码 0，不报「未找到 scope」；`--json` 的 scopes[] 只有这一项的三个键。点名的 scope 不在这个 run 里时照旧以退出码 2 结束。"""
    from gherkai_core.model import RunMeta, RunState

    root = tmp_path / "reports"
    run_id = "20260910T080630Z-9fa262"
    a, b = _explain_job(scope_id="a"), _explain_job(scope_id="b")
    run_store, result_store, _rp, _mk = compose.build_local_stores(report_dir=str(root), lock_holder=compose.process_lock_holder())
    run_store.create_run(RunMeta(run_id=run_id, created_at="2026-09-10T08:06:30Z", jobs=(a, b), deadline_at="2026-01-01T01:00:00+00:00"),
                         RunState(run_id=run_id, status=Status.PENDING, started_at="t0",
                                  jobs={"a": JobState("a", Status.PENDING), "b": JobState("b", Status.PENDING)}))
    rid = _save_detail(result_store, run_id, JobResult(job=a, status=Status.ERROR, error_type="engine_error", message="m"))
    assert run_store.commit_job_states(run_id, [JobState("a", Status.ERROR, result_id=rid)], ended_at="t9") == CommitOutcome.OPEN
    fail_fast = RUN_ENDINGS["fail-fast"]
    assert run_store.end_run(run_id, fail_fast, ended_at="t9") is True

    rc, out, err = _explain(capsys, root, run_id, "b")
    assert rc == 0 and "未找到 scope" not in err
    assert f"run {run_id}  status=error" in out and "scope b  status=skipped" in out
    assert f"message: {fail_fast.skipped_message}" in out and m.render._NO_DETAIL in out
    rc, out, err = _explain(capsys, root, run_id, "b", "--json")
    assert rc == 0 and err == ""
    assert json.loads(out) == {"run_id": run_id, "status": "error",
                               "scopes": [{"scope_id": "b", "status": "skipped", "message": fail_fast.skipped_message}]}
    rc, _out, err = _explain(capsys, root, run_id, "c")
    assert rc == 2 and "未找到 scope：c" in err


def test_explain_named_scope_still_running_while_the_run_is_running_says_not_landed(tmp_path, capsys):
    """后台推进的 run 仍为 running、a 已被认领、仍在执行，还没有判定明细（明细在它得出结果的那一轮、写下终态之前才存下）：点名 a 给
    「判定明细尚未落地」的提示、退出码 0，`--json` 的 scopes 为空，与不点名时的说法相同；不按运行态给出 a 的状态，也不报「未找到
    scope」。"""
    from gherkai_core.model import RunMeta, RunState

    root = tmp_path / "reports"
    run_id = "20260910T080630Z-9fa263"
    a, b = _explain_job(scope_id="a"), _explain_job(scope_id="b")
    run_store, _result_store, _rp, _mk = compose.build_local_stores(report_dir=str(root), lock_holder=compose.process_lock_holder())
    run_store.create_run(RunMeta(run_id=run_id, created_at="2026-09-10T08:06:30Z", jobs=(a, b),
                                 deadline_at="2026-09-10T09:06:30+00:00"),
                         RunState(run_id=run_id, status=Status.PENDING, started_at="t0",
                                  jobs={"a": JobState("a", Status.PENDING), "b": JobState("b", Status.PENDING)}))
    assert run_store.try_claim_job(run_id, "a", claimed_at="2026-09-10T08:06:31+00:00") is True
    assert run_store.try_claim_job(run_id, "b", claimed_at="2026-09-10T08:06:31+00:00") is True
    state = run_store.load_run_state(run_id)
    assert state.status == Status.RUNNING and state.jobs["a"].status == Status.RUNNING  # 构造的前提

    rc, out, err = _explain(capsys, root, run_id, "a")
    assert rc == 0 and out == "" and "判定明细尚未落地" in err and m.render._NO_DETAIL not in err
    rc, out, err = _explain(capsys, root, run_id, "a", "--json")
    assert rc == 0 and err == ""
    doc = json.loads(out)
    assert doc["run_id"] == run_id and doc["status"] == "running" and doc["scopes"] == []
    rc, out, err = _explain(capsys, root, run_id)
    assert rc == 0 and out == "" and "判定明细尚未落地" in err
    rc, _out, err = _explain(capsys, root, run_id, "c")  # 这个 run 里没有的 scope：一份明细都没有时同样以退出码 2 结束
    assert rc == 2 and "未找到 scope：c" in err


def test_explain_named_scope_still_running_after_another_job_landed_says_not_landed(tmp_path, capsys):
    """run 仍为 running，b 已得出结果（先存明细、再由终态写记下），a 仍在执行：点名 a 给「判定明细尚未落地」的提示、退出码 0，
    `--json` 的 scopes 为空，不因 b 已有明细而报「未找到 scope」；不点名时照常给出 b 的明细；点名这个 run 里没有的 scope 以退出码 2
    结束。"""
    from gherkai_core.model import RunMeta, RunState

    root = tmp_path / "reports"
    run_id = "20260910T080630Z-9fa264"
    a, b = _explain_job(scope_id="a"), _explain_job(scope_id="b")
    run_store, result_store, _rp, _mk = compose.build_local_stores(report_dir=str(root), lock_holder=compose.process_lock_holder())
    run_store.create_run(RunMeta(run_id=run_id, created_at="2026-09-10T08:06:30Z", jobs=(a, b),
                                 deadline_at="2026-09-10T09:06:30+00:00"),
                         RunState(run_id=run_id, status=Status.PENDING, started_at="t0",
                                  jobs={"a": JobState("a", Status.PENDING), "b": JobState("b", Status.PENDING)}))
    assert run_store.try_claim_job(run_id, "a", claimed_at="2026-09-10T08:06:31+00:00") is True
    assert run_store.try_claim_job(run_id, "b", claimed_at="2026-09-10T08:06:31+00:00") is True
    rid = _save_detail(result_store, run_id, JobResult(job=b, status=Status.PASSED))
    assert run_store.commit_job_states(run_id, [JobState("b", Status.PASSED, result_id=rid)], ended_at="t5") == CommitOutcome.OPEN
    state = run_store.load_run_state(run_id)
    assert (state.status, state.jobs["a"].status, state.jobs["b"].status) == (  # 构造的前提
        Status.RUNNING, Status.RUNNING, Status.PASSED)

    rc, out, err = _explain(capsys, root, run_id, "a")
    assert rc == 0 and out == "" and "判定明细尚未落地" in err and "未找到 scope" not in err
    rc, out, err = _explain(capsys, root, run_id, "a", "--json")
    assert rc == 0 and err == ""
    doc = json.loads(out)
    assert doc["run_id"] == run_id and doc["status"] == "running" and doc["scopes"] == []
    rc, out, err = _explain(capsys, root, run_id)
    assert rc == 0 and "run 仍在运行，以下为已完成部分" in err and "scope b" in out and "scope a" not in out
    rc, _out, err = _explain(capsys, root, run_id, "c")
    assert rc == 2 and "未找到 scope：c（这个 run 的 scope：a、b）" in err


def test_explain_detached_run_without_job_files_exits_0_with_one_hint(tmp_path, capsys):
    """detached run 还没有 job 得出结果时零判定明细（明细在每个 job 得出结果时才存下）→ 退出码 0 + 一行提示；--json 不打提示、
    stdout 仍只有一个文档（机读侧靠顶层 status 自明）。"""
    from gherkai_core.model import Status as S
    root, run_id = _explain_run(tmp_path, with_results=False, run_status=S.RUNNING)
    rc, out, err = _explain(capsys, root, run_id)
    # 建议命令要能原样运行成功：本机后端必带 --report-dir（默认 reports/ 与本用例的 tmp 根不同，不带即查不到）
    assert rc == 0 and out == "" and "判定明细尚未落地" in err
    assert f"gherkai status {run_id} --report-dir {root} --wait" in err
    rc, out, err = _explain(capsys, root, run_id, "--json")
    assert rc == 0 and err == ""
    doc = json.loads(out)
    assert doc["status"] == "running" and doc["scopes"] == []


def _explain_two_job_run(tmp_path, run_id: str, scopes=("a", "b")):
    """建一个 run，运行定义按 scopes 的次序列出 job，每个 job 都已认领、在执行；返回 (报告目录, run store, 判定存储, scope_id → Job)。"""
    from gherkai_core.model import RunMeta, RunState

    root = tmp_path / "reports"
    jobs = {sid: _explain_job(scope_id=sid) for sid in scopes}
    run_store, result_store, _rp, _mk = compose.build_local_stores(report_dir=str(root), lock_holder=compose.process_lock_holder())
    run_store.create_run(RunMeta(run_id=run_id, created_at="2026-09-10T08:06:30Z", jobs=tuple(jobs.values()),
                                 deadline_at="2026-09-10T09:06:30+00:00"),
                         RunState(run_id=run_id, status=Status.PENDING, started_at="t0",
                                  jobs={sid: JobState(sid, Status.PENDING) for sid in scopes}))
    for sid in scopes:
        assert run_store.try_claim_job(run_id, sid, claimed_at="2026-09-10T08:06:31+00:00") is True
    return root, run_store, result_store, jobs


def test_explain_does_not_show_a_detail_saved_before_its_terminal_write(tmp_path, capsys):
    """判定明细先于终态存下。a 的明细已存下而它的终态还没有写下（运行态里它仍在执行、没有点名），b 已结束并点名了它的那一份：
    explain 先看运行态，不点名 scope 时只给出 b，不把 a 存下的那一份当作已完成的部分展示；点名 a 时按「判定明细尚未落地」提示、
    退出码 0，`--json` 的 scopes 为空、status 是运行态里的 running。"""
    run_id = "20260910T080630Z-9fa265"
    root, run_store, result_store, jobs = _explain_two_job_run(tmp_path, run_id)
    _save_detail(result_store, run_id, JobResult(job=jobs["a"], status=Status.FAILED, error_type="engine_error",
                                                 message="还没有被采用的结果"))
    rid = _save_detail(result_store, run_id, JobResult(job=jobs["b"], status=Status.PASSED))
    assert run_store.commit_job_states(run_id, [JobState("b", Status.PASSED, result_id=rid)], ended_at="t5") == CommitOutcome.OPEN

    rc, out, err = _explain(capsys, root, run_id)
    assert rc == 0 and "以下为已完成部分" in err and "scope b" in out and "scope a" not in out
    assert "还没有被采用的结果" not in out
    rc, out, err = _explain(capsys, root, run_id, "--json")
    assert rc == 0 and err == "" and [sc["scope_id"] for sc in json.loads(out)["scopes"]] == ["b"]
    rc, out, err = _explain(capsys, root, run_id, "a")
    assert rc == 0 and out == "" and "判定明细尚未落地" in err and "已完成部分" not in err
    rc, out, err = _explain(capsys, root, run_id, "a", "--json")
    doc = json.loads(out)
    assert rc == 0 and err == "" and doc["status"] == "running" and doc["scopes"] == []


def test_explain_does_not_show_a_detail_left_by_a_job_the_ending_write_ended(tmp_path, capsys):
    """a 的明细已存下、终态还没有写下时，run 被处置的结束写结束：a 在运行态里记 aborted、不点名，b 先前点名的那一份原样保留。存储里
    a 那份没被点名的明细在两种调用下都不出现：不点名 scope 时只给出 b；点名 a 时只给运行态里的状态与说明，`--json` 只有三个键。"""
    from gherkai_core.run_status import RUN_ENDINGS

    ending = RUN_ENDINGS["settle-advancer-exited"]
    run_id = "20260910T080630Z-9fa266"
    root, run_store, result_store, jobs = _explain_two_job_run(tmp_path, run_id)
    rid = _save_detail(result_store, run_id, JobResult(job=jobs["b"], status=Status.PASSED))
    assert run_store.commit_job_states(run_id, [JobState("b", Status.PASSED, result_id=rid)], ended_at="t5") == CommitOutcome.OPEN
    _save_detail(result_store, run_id, JobResult(job=jobs["a"], status=Status.FAILED, error_type="engine_error",
                                                 message="没被采用的结果"))
    assert run_store.end_run(run_id, ending, ended_at="t9") is True
    state = run_store.load_run_state(run_id)
    assert (state.jobs["a"].status, state.jobs["a"].result_id, state.jobs["b"].result_id) == (  # 构造的前提
        Status.ABORTED, None, rid)

    rc, out, _err = _explain(capsys, root, run_id)
    assert rc == 0 and "scope b" in out and "scope a" not in out and "没被采用的结果" not in out
    rc, out, _err = _explain(capsys, root, run_id, "--json")
    assert rc == 0 and [sc["scope_id"] for sc in json.loads(out)["scopes"]] == ["b"]
    rc, out, err = _explain(capsys, root, run_id, "a", "--json")
    assert rc == 0 and err == "" and json.loads(out) == {"run_id": run_id, "status": "aborted", "scopes": [
        {"scope_id": "a", "status": "aborted", "message": ending.aborted_message}]}
    rc, out, _err = _explain(capsys, root, run_id, "a")
    assert rc == 0 and "scope a  status=aborted" in out and m.render._NO_DETAIL in out and "没被采用的结果" not in out


def test_explain_reads_the_named_detail_when_a_job_has_several(tmp_path, capsys):
    """同一个 job 存过两份明细（两个推进方各存一份）：运行态点名的是写成终态那一方存下的一份，后到的一方存下的那一份没被点名。两种
    调用读的都是被点名的那一份。"""
    run_id = "20260910T080630Z-9fa267"
    root, run_store, result_store, jobs = _explain_two_job_run(tmp_path, run_id, scopes=("a",))
    named = _save_detail(result_store, run_id, JobResult(job=jobs["a"], status=Status.FAILED, error_type="engine_error",
                                                         message="写成终态那一方的结果"))
    assert run_store.commit_job_states(run_id, [JobState("a", Status.FAILED, result_id=named)],
                                       ended_at="t9") == CommitOutcome.ENDED_RUN
    _save_detail(result_store, run_id, JobResult(job=jobs["a"], status=Status.PASSED))  # 后到的一方：终态已写下，它的这一份不被点名
    assert len(_detail_files(root / run_id)) == 2  # 构造的前提：存放处里有两份
    for flags in ((), ("a",)):
        rc, out, _err = _explain(capsys, root, run_id, *flags, "--json")
        [sc] = json.loads(out)["scopes"]
        assert rc == 0 and (sc["scope_id"], sc["status"], sc["message"]) == ("a", "failed", "写成终态那一方的结果")


def test_explain_lists_named_jobs_and_scope_candidates_by_scope_id(tmp_path, capsys):
    """不点名 scope 时按 scope_id 的次序列出点名了明细的 job，「未找到 scope」的候选同样按 scope_id 排序、取自运行态：两个后端是同一
    种次序，不随运行定义或存放处的次序变化（这里运行定义的次序是 b、a）。"""
    run_id = "20260910T080630Z-9fa268"
    root, run_store, result_store, jobs = _explain_two_job_run(tmp_path, run_id, scopes=("b", "a"))
    finals = [JobState(sid, Status.PASSED, result_id=_save_detail(result_store, run_id, JobResult(job=jobs[sid], status=Status.PASSED)))
              for sid in ("b", "a")]
    assert run_store.commit_job_states(run_id, finals, ended_at="t9") == CommitOutcome.ENDED_RUN
    rc, out, _err = _explain(capsys, root, run_id, "--json")
    assert rc == 0 and [sc["scope_id"] for sc in json.loads(out)["scopes"]] == ["a", "b"]
    rc, out, _err = _explain(capsys, root, run_id)
    assert rc == 0 and out.index("scope a") < out.index("scope b")
    rc, _out, err = _explain(capsys, root, run_id, "c")
    assert rc == 2 and "未找到 scope：c（这个 run 的 scope：a、b）" in err


def test_explain_exits_2_when_the_named_detail_cannot_be_read(tmp_path, capsys):
    """运行态点名的那一份读不到（存放处里那个文件被删掉）：按记录残缺处理，点名与不点名 scope、人读与 `--json` 都以退出码 2 结束，
    stderr 一句说明哪个 job 的明细读不到，stdout 为空，不当作没有明细给出状态与说明；没受影响的 job 照常可读。运行态被改成指向别的
    job 的那一份时同样以退出码 2 结束，不把别的 job 的明细附上。"""
    run_id = "20260910T080630Z-9fa269"
    root, run_store, result_store, jobs = _explain_two_job_run(tmp_path, run_id)
    ra, rb = (_save_detail(result_store, run_id, JobResult(job=jobs[sid], status=Status.PASSED)) for sid in ("a", "b"))
    assert run_store.commit_job_states(run_id, [JobState("a", Status.PASSED, result_id=ra),
                                                JobState("b", Status.PASSED, result_id=rb)], ended_at="t9") == CommitOutcome.ENDED_RUN
    (root / run_id / "jobs" / f"{ra}.json").unlink()
    for flags in ((), ("a",), ("--json",), ("a", "--json")):
        rc, out, err = _explain(capsys, root, run_id, *flags)
        assert rc == 2 and out == "" and "Traceback" not in err, flags
        assert f"job a 的判定明细读不到（标识 {ra}）" in err and "可能已被删除" in err, flags
        assert "这个 job 的状态仍可用 status 查看" in err, flags  # 说明里带「怎么办」
    rc, _out, _err = _explain(capsys, root, run_id, "b")
    assert rc == 0

    path = root / run_id / "run_state.json"
    st = json.loads(path.read_text(encoding="utf-8"))
    for j in st["jobs"]:
        if j["scope_id"] == "a":
            j["result_id"] = rb  # 绕过写入口改动运行态：a 指向 b 的那一份
    path.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    rc, out, err = _explain(capsys, root, run_id, "a", "--json")
    assert rc == 2 and out == "" and "属于 job b" in err


def test_explain_job_without_step_records_gets_a_job_block(tmp_path, capsys):
    """零 step 记录的 job（worker 没起来/起来就被掐）：单独一段 job 判定块（判定 + 归因 + 产物 + 去看 worker 日志），
    骨架仍逐 step 打「无记录」。"""
    root, run_id = _explain_run(tmp_path, job_only=True)
    rc, out, _ = _explain(capsys, root, run_id)
    assert rc == 0
    assert "判定：aborted  (timeout: job 墙钟预算用尽被停)" in out
    assert "诊断细节见 worker 日志" in out
    assert "report（summary）: file:///tmp/summary.json" in out
    # 两条 scenario 各自也没有判定记录（scenario_done 没到）→ 2 条 scenario 行 + 4+2 条 step 行
    assert out.count("无记录（未执行或未上报）") == 8
    assert "scenario features/login.feature:20  锁定账户提示  无记录（未执行或未上报）" in out
    doc = json.loads(_explain(capsys, root, run_id, "--json")[1])
    # 被中止且有无记录 step → 要从事件流补取；这个 run 没有 events.db（旧版本执行或 --no-report）→ 提示写明读不到的原因（ADR 0042 决策七）
    assert doc["scopes"][0]["aborted_hint"].startswith("本 job 被中止，无法从事件流补取") and "事件流记录" in doc["scopes"][0]["aborted_hint"]


_CLOUD_RESULT_ID = "0123456789abcdef"  # 假云端运行态里点名的标识


def _explain_cloud_stores(jr, state):
    """假的云端两 store（explain 只读 RunStore/ResultStore）：验接线与读路径，不连真 AWS。判定存储与真端口一样只有按标识取的读法、
    没有列举入口；jr 存在运行态里这个 job 点名的标识下，别的标识下没有明细。"""
    named = state.jobs[jr.scope_id].result_id if jr is not None else None

    class _RunStore:
        def peek_definition_header(self, run_id):
            return (DEFINITION_SCHEMA_VERSION, None)  # 结构版本闸先于运行态读（ADR 0037 决策 7）：本版本、放行

        def load_run_state(self, run_id):
            return state

    class _ResultStore:
        def load_job_result(self, run_id, result_id):
            return jr if named is not None and result_id == named else None

    return _RunStore(), _ResultStore(), object()


def _events_db_with_unfinished_scenario(root, run_id, scope_id: str, evidence_uri: str):
    """给 _explain_run 搭的 run 写一份事件流：scenario :12 执行到第三步被中止（两条 step_done、第三步只有 step_started），:20 零事件。"""
    from gherkai_core.adapters.event_log import SqliteEventLog
    log = SqliteEventLog(compose.events_db_path(root, run_id))
    lines = [
        {"type": "scope_started", "scopeId": scope_id, "sessionId": "01a0deadbeef"},
        {"type": "scenario_started", "scenarioId": "features/login.feature:12"},
        {"type": "step_started", "scenarioId": "features/login.feature:12", "stepIndex": 0},
        {"type": "step_done", "scenarioId": "features/login.feature:12", "stepIndex": 0, "status": "passed"},
        {"type": "step_started", "scenarioId": "features/login.feature:12", "stepIndex": 1},
        {"type": "step_done", "scenarioId": "features/login.feature:12", "stepIndex": 1, "status": "failed",
         "votes": {"yes": 0, "total": 1}, "errorType": "assertion_failed", "message": "AI 断言未过多数票（0/1）：页面显示「已登录」",
         "reportRefs": [{"kind": "evidence", "ref": evidence_uri, "label": "evidence"}]},
        {"type": "step_started", "scenarioId": "features/login.feature:12", "stepIndex": 2},
    ]
    for i, d in enumerate(lines, start=1):
        log.append_event(scope_id, i, json.dumps(d, ensure_ascii=False), 1000.0 + i)
    return log


def test_explain_recovers_unfinished_steps_from_the_event_stream(tmp_path, capsys):
    """被中止 job 的 step 记录从事件流补取（ADR 0042 决策七）：没有 scenario_done 的 scenario 标 unfinished、其已执行完的 step 带
    record_source=events 与证据，被中止时正在执行的第三步与没到的第四步仍无记录；aborted_hint 为 null；文本标「记录取自事件流」。"""
    root, run_id = _explain_run(tmp_path, job_only=True)
    ev_uri = (root / run_id / "evidence" / "evidence.json").resolve().as_uri()
    _events_db_with_unfinished_scenario(root, run_id, "features/login.feature:6", ev_uri)
    rc, out, err = _explain(capsys, root, run_id, "--json")
    assert rc == 0 and err == ""
    sc = json.loads(out)["scopes"][0]
    assert sc["aborted_hint"] is None and sc["has_step_records"] is False  # 判定明细里仍然零记录，这是 job 的事实
    s12, s20 = sc["scenarios"]
    assert s12["status"] is None and s12["unfinished"] is True
    assert [st["record_source"] for st in s12["steps"]] == ["events", "events", None, None]
    assert [st["record_missing"] for st in s12["steps"]] == [False, False, True, True]
    assert s12["steps"][0]["status"] == "passed" and s12["steps"][1]["status"] == "failed"
    assert s12["steps"][1]["votes"] == {"yes": 0, "total": 1} and s12["steps"][1]["message"].startswith("AI 断言未过")
    assert s12["steps"][1]["evidence"]["schema_version"] == 1 and s12["steps"][1]["evidence_missing"] is None
    assert s12["steps"][0]["duration_ms"] == 1000.0  # step_started 到 step_done 的到达时刻差
    assert s20["status"] is None and s20["unfinished"] is False and all(st["record_missing"] for st in s20["steps"])
    rc, out, _ = _explain(capsys, root, run_id)
    assert "scenario features/login.feature:12  密码错误时不放行  未完成" in out
    assert "step 1  When 输入用户名「alice」与密码「wrong」  failed  votes 0/1" in out and "（记录取自事件流）" in out
    assert out.count("（记录取自事件流）") == 2 and "本 job 被中止" not in out
    assert "scenario features/login.feature:20  锁定账户提示  无记录（未执行或未上报）" in out


def test_explain_recovers_a_scenario_whose_scenario_done_never_reached_the_verdict(tmp_path, capsys):
    """事件流里有 scenario_done、判定明细却没有这条 scenario（同步 run 在归约前退出）：也补取，scenario 的 status 取事件流里的判定、
    unfinished 为 false，其 step 的 record_source 仍是 events。"""
    from gherkai_core.adapters.event_log import SqliteEventLog
    root, run_id = _explain_run(tmp_path, job_only=True)
    log = SqliteEventLog(compose.events_db_path(root, run_id))
    lines = [
        {"type": "scope_started", "scopeId": "features/login.feature:6"},
        {"type": "scenario_started", "scenarioId": "features/login.feature:20"},
        {"type": "step_done", "scenarioId": "features/login.feature:20", "stepIndex": 0, "status": "passed"},
        {"type": "step_done", "scenarioId": "features/login.feature:20", "stepIndex": 1, "status": "passed"},
        {"type": "scenario_done", "scenarioId": "features/login.feature:20", "status": "passed"},
    ]
    for i, d in enumerate(lines, start=1):
        log.append_event("features/login.feature:6", i, json.dumps(d), 10.0 + i)
    sc = json.loads(_explain(capsys, root, run_id, "--json")[1])["scopes"][0]
    s20 = sc["scenarios"][1]
    assert s20["status"] == "passed" and s20["unfinished"] is False
    assert [st["record_source"] for st in s20["steps"]] == ["events", "events"] and sc["aborted_hint"] is None
    rc, out, _ = _explain(capsys, root, run_id)
    assert "scenario features/login.feature:20  锁定账户提示  passed" in out and out.count("（记录取自事件流）") == 2


def test_explain_unreadable_event_db_degrades_to_the_hint(tmp_path, capsys):
    """events.db 打不开或损坏：explain 仍以退出码 0 输出，只在该 job 的 aborted_hint 写明读取失败（ADR 0042 决策七第 3 条）。"""
    root, run_id = _explain_run(tmp_path, job_only=True)
    compose.events_db_path(root, run_id).write_bytes(b"not a sqlite file at all")
    rc, out, err = _explain(capsys, root, run_id, "--json")
    assert rc == 0
    sc = json.loads(out)["scopes"][0]
    assert sc["aborted_hint"].startswith("本 job 被中止，无法从事件流补取") and "读取失败" in sc["aborted_hint"]
    assert all(st["record_missing"] for scen in sc["scenarios"] for st in scen["steps"])


def test_explain_recovery_is_only_attempted_for_aborted_or_error_jobs_with_gaps(tmp_path, capsys, monkeypatch):
    """有完整判定记录的 failed job 不读事件流；判定明细已有的 scenario 不从事件流改写。"""
    root, run_id = _explain_run(tmp_path)  # failed、scenario :12 有判定记录（step 3 无记录）、:20 有判定记录
    _events_db_with_unfinished_scenario(root, run_id, "features/login.feature:6", "file:///tmp/none.json")
    opened = []
    real = compose.build_local_event_log
    monkeypatch.setattr(m.compose, "build_local_event_log", lambda *a, **k: (opened.append(a), real(*a, **k))[1])
    doc = json.loads(_explain(capsys, root, run_id, "--json")[1])
    s12 = doc["scopes"][0]["scenarios"][0]
    assert opened == []  # failed 的 job 不读事件流
    assert s12["status"] == "failed" and s12["unfinished"] is False
    assert [st["record_source"] for st in s12["steps"]] == ["verdict", "verdict", "verdict", None]


def test_explain_reports_when_the_event_stream_has_no_record_for_the_job(tmp_path, capsys):
    """事件库在、却没有这个 job 的任何记录（云端 7 天过期后的形态，本机则是 worker 没发过事件）：算补取失败，aborted_hint 写明原因。"""
    from gherkai_core.adapters.event_log import SqliteEventLog
    root, run_id = _explain_run(tmp_path, job_only=True)
    SqliteEventLog(compose.events_db_path(root, run_id))  # 建库但不写任何记录
    sc = json.loads(_explain(capsys, root, run_id, "--json")[1])["scopes"][0]
    assert sc["aborted_hint"].startswith("本 job 被中止，无法从事件流补取") and "没有这个 job 的记录" in sc["aborted_hint"]
    assert sc["recovered_steps"] == 0
    rc, out, _ = _explain(capsys, root, run_id)
    assert "诊断细节见 worker 日志" in out  # 判定明细与事件流都没给出 step 时才指去看日志


def test_explain_treats_an_exit_only_event_stream_as_no_record_for_the_job(tmp_path, capsys):
    """事件库里这个 job 只有退出记录、没有任何事件行（云端 events 表的事件行 7 天过期后只剩不带 TTL 的退出记录；本机 worker 没发事件就退出）：
    算补取失败并写明原因，不是「补到零条、也不说明」。"""
    from gherkai_core.adapters.event_log import SqliteEventLog
    root, run_id = _explain_run(tmp_path, job_only=True)
    SqliteEventLog(compose.events_db_path(root, run_id)).record_exit("features/login.feature:6", 1)
    sc = json.loads(_explain(capsys, root, run_id, "--json")[1])["scopes"][0]
    assert "没有这个 job 的记录" in sc["aborted_hint"] and sc["recovered_steps"] == 0


def test_explain_degrades_when_event_reduction_fails(tmp_path, capsys):
    """事件行能过解析、归约时却因 worker 违约的字段值抛出（这里计量给成字串，求和时 TypeError）：与读取失败同一口径，只落 aborted_hint
    的原因，explain 不抛、退出码不变。"""
    from gherkai_core.adapters.event_log import SqliteEventLog
    root, run_id = _explain_run(tmp_path, job_only=True)
    log = SqliteEventLog(compose.events_db_path(root, run_id))
    scope_id = "features/login.feature:6"
    lines = [
        {"type": "scope_started", "scopeId": scope_id, "sessionId": "01a0deadbeef"},
        {"type": "scenario_started", "scenarioId": "features/login.feature:12"},
        {"type": "step_started", "scenarioId": "features/login.feature:12", "stepIndex": 0},
        {"type": "step_done", "scenarioId": "features/login.feature:12", "stepIndex": 0, "status": "passed", "cost": {"tokens": "1"}},
        {"type": "step_started", "scenarioId": "features/login.feature:12", "stepIndex": 1},
        {"type": "step_done", "scenarioId": "features/login.feature:12", "stepIndex": 1, "status": "passed", "cost": {"tokens": "1"}},
    ]
    for i, d in enumerate(lines, start=1):
        log.append_event(scope_id, i, json.dumps(d), 1000.0 + i)
    rc, out, _ = _explain(capsys, root, run_id, "--json")
    sc = json.loads(out)["scopes"][0]
    assert rc == 0 and "事件流记录解析失败" in sc["aborted_hint"] and "unsupported operand" in sc["aborted_hint"]
    assert sc["recovered_steps"] == 0 and all(st["record_missing"] for scen in sc["scenarios"] for st in scen["steps"])


def test_explain_recovered_steps_is_a_job_level_count_so_filtering_does_not_bring_back_the_log_hint(tmp_path, capsys):
    """recovered_steps 按整个 job 统计、不随 --scenario/--step 变化：筛到补回了记录的 job 里一个无记录 step 时，文档仍报补到的步数、
    文本不再打「诊断细节见 worker 日志」（曾按筛后文档数，筛剩无记录 step 就把它当成零记录 job）。"""
    root, run_id = _explain_run(tmp_path, job_only=True)
    _events_db_with_unfinished_scenario(root, run_id, "features/login.feature:6", "file:///tmp/none.json")
    rc, out, _ = _explain(capsys, root, run_id, "--scenario", "12", "--step", "3", "--json")
    sc = json.loads(out)["scopes"][0]
    steps = [st for scen in sc["scenarios"] for st in scen["steps"]]
    assert rc == 0 and sc["recovered_steps"] == 2 and len(steps) == 1 and steps[0]["record_missing"]
    rc, out, _ = _explain(capsys, root, run_id, "--scenario", "12", "--step", "3")
    assert rc == 0 and "诊断细节见 worker 日志" not in out


def test_local_submit_marks_the_run_detached_and_foreground_run_does_not(tmp_path, monkeypatch, inline_children, advanced):
    """本机 submit 的后台推进进程建的 run 的 run_state.json 带顶层 detached 标记（只作描述）；前台 run 产出的没有。"""
    reports = tmp_path / "s"
    assert m.main(["submit", str(_write_feature(tmp_path)), "--report-dir", str(reports)]) == 0
    inline_children.settle()
    run_dir = _submitted_run_dir(reports)
    assert json.loads((run_dir / "run_state.json").read_text(encoding="utf-8"))["detached"] is True
    # 前台 run 真走一遍 `run` 命令（假 schedule，不起 worker）：它建的 run_state.json 不带标记
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    fg = tmp_path / "fg"
    assert m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(fg), "--quiet"]) == 0
    fg_dir = next(d for d in fg.iterdir() if d.is_dir())
    assert "detached" not in json.loads((fg_dir / "run_state.json").read_text(encoding="utf-8"))


# ---- 本机后台推进进程在保存判定明细一直失败、推进中遇到事件库错误或读到解析不了的运行态时的出口 ----
# 真实装配与真实推进步骤，只把引擎换成空表（不起 worker）、把判定存储的等待换成记录；后台推进进程经 `inline_children` 在线程里执行。


def _stage_a_finished_job(reports: Path, meta) -> None:
    """把刚建成、只有一个 job 的 run 摆成推进到一半的样子：这个 job 已认领、在执行，事件库里已有它执行完的事件与退出记录，下一次
    推进即为它存明细、写终态。"""
    from gherkai_core.adapters.event_log import SqliteEventLog
    from gherkai_core.adapters.run_store.local import LocalRunStore

    [job] = meta.jobs
    assert LocalRunStore(reports).try_claim_job(meta.run_id, job.scope_id, claimed_at=compose.now_iso()) is True
    log = SqliteEventLog(compose.events_db_path(reports, meta.run_id))
    lines = [{"type": "scope_started", "scopeId": job.scope_id, "sessionId": "s-1"},
             {"type": "scenario_done", "scenarioId": job.scenarios[0].id, "status": "passed"},
             {"type": "scope_done", "scopeId": job.scope_id}]
    for seq, line in enumerate(lines, start=1):
        log.append_event(job.scope_id, seq, json.dumps(line), float(seq))
    log.record_exit(job.scope_id, 0, exited_at=compose.now())


def _submit_one_job(tmp_path: Path, monkeypatch, inline_children) -> tuple[Path, str, int]:
    """本机 submit 提交一个只有一个 job 的 run（报告目录 tmp_path/reports），等后台推进进程结束；返回 (报告目录, run_id, 后台推进进程
    的退出码)。推进换成什么由调用方先装好；引擎换成空表，真实推进不起 worker。"""
    _fake_locator(monkeypatch, available=("novaact", "midscene"))
    monkeypatch.setattr(m.compose, "build_engines", lambda **kw: {})
    reports = tmp_path / "reports"
    assert m.main(["submit", str(_write_feature(tmp_path)), "--report-dir", str(reports)]) == 0
    inline_children.settle()
    return reports, _submitted_run_dir(reports).name, inline_children.only().returncode


def _assert_left_running(reports: Path, run_id: str) -> None:
    """这个 job 没有写下终态、在记录里仍为 running、不点名，run 没有结束，没有存下任何明细、没有报告。"""
    from gherkai_core.adapters.run_store.local import LocalRunStore

    state = LocalRunStore(reports).load_run_state(run_id)
    assert state.status not in m.TERMINAL_STATUSES and state.ended_at is None
    assert [(js.status, js.result_id) for js in state.jobs.values()] == [(Status.RUNNING, None)]
    assert _detail_files(reports / run_id) == [] and not (reports / run_id / "index.html").exists()


def test_background_advancer_exits_1_with_one_sentence_when_saving_the_detail_keeps_failing(tmp_path, monkeypatch, capsys,
                                                                                            inline_children):
    """后台推进进程保存判定明细一直失败（磁盘写不进）：按 1、2、4 秒退避重试仍失败，进程在 reconcile.log 里打一句说明（发生了什么、记录
    在哪里、用哪条 settle-runs 命令把它记为已结束再重新提交）、不打回溯，以退出码 1 结束；这个 run 没有结束、不做结束写。提交进程此前
    已收到回报，以 0 结束。"""
    from gherkai_core.adapters.result_store.local import LocalResultStore

    reports = tmp_path / "reports"
    real_advance = detached.advance_local_run

    def advance_from_half_way(advancer, meta, **kw):  # 推进开始时这个 job 已由 worker 执行完：下一次推进要为它存明细
        _stage_a_finished_job(reports, meta)
        return real_advance(advancer, meta, **kw)

    monkeypatch.setattr(detached, "advance_local_run", advance_from_half_way)
    waits = _no_wait_save_retry(monkeypatch)
    monkeypatch.setattr(LocalResultStore, "save_job_result", _disk_full)

    reports, run_id, returncode = _submit_one_job(tmp_path, monkeypatch, inline_children)
    cap = capsys.readouterr()
    assert cap.out == f"{run_id}\n" and "已提交（本机后台推进中）" in cap.err
    log = (reports / run_id / "reconcile.log").read_text(encoding="utf-8")
    assert returncode == 1 and "Traceback" not in log and waits == [1.0, 2.0, 4.0]
    assert f"run {run_id} 读写本机的运行记录失败，后台推进已停止：" in log and "No space left on device" in log
    assert f"记录在 {(reports / run_id).resolve()}，出错时执行中的 job 在记录里仍为 running" in log
    assert ("请检查这个目录所在磁盘的剩余空间与读写权限，再用 "
            f"gherkai settle-runs {run_id} --report-dir {reports} 把这个 run 记为已结束，然后重新提交。") in log
    assert "读写本机的运行记录失败" not in cap.err  # 说明只进日志：提交进程的终端此时早已收到回报、退出
    _assert_left_running(reports, run_id)


@pytest.mark.parametrize("damage", ["events-db", "run-state"])
def test_background_advancer_exits_1_with_one_sentence_when_the_record_breaks_while_advancing(
        damage, tmp_path, monkeypatch, capsys, inline_children):
    """推进中记录坏掉，后台推进进程同样只打一句说明（写进 reconcile.log）、不打回溯，以退出码 1 结束，run 停在未结束：
    - 事件库不再是 SQLite 库（读事件得到 sqlite3.DatabaseError，不是 OSError）：读写记录失败的那一句，给出把它记为已结束的 settle-runs
      整条命令，再重新提交；
    - 运行态解析不了：这样的 run 处置方也不结束，说明取 settle-runs 对它的同一句（不改动它、确认不需要之后可以手工移走），不说可以
      记为已结束。"""
    reports = tmp_path / "reports"
    real_advance = detached.advance_local_run

    def advance_after_breaking(advancer, meta, **kw):
        run = reports / meta.run_id
        if damage == "events-db":
            compose.events_db_path(reports, meta.run_id).write_bytes(b"not a sqlite file at all, long enough to be read")
        else:
            (run / "run_state.json").write_text("{broken", encoding="utf-8")
        return real_advance(advancer, meta, **kw)

    monkeypatch.setattr(detached, "advance_local_run", advance_after_breaking)
    reports, run_id, returncode = _submit_one_job(tmp_path, monkeypatch, inline_children)
    log = (reports / run_id / "reconcile.log").read_text(encoding="utf-8")
    assert returncode == 1 and "Traceback" not in log
    if damage == "events-db":
        assert f"run {run_id} 读写本机的运行记录失败，后台推进已停止：file is not a database。" in log
        assert (f"再用 gherkai settle-runs {run_id} --report-dir {reports} 把这个 run 记为已结束，然后重新提交。") in log
        from gherkai_core.adapters.run_store.local import LocalRunStore

        assert LocalRunStore(reports).load_run_state(run_id).status not in m.TERMINAL_STATUSES
    else:
        try:
            json.loads("{broken")
        except ValueError as e:
            why = str(e)
        assert (f"run {run_id} 的运行状态记录读不出，后台推进已停止：{why}。settle-runs 与 status --wait 不改动这个 run 的记录，"
                f"确认不需要之后可以手工移走 run 目录 {(reports / run_id).resolve()}。") in log
        assert "settle-runs " + run_id not in log  # 不给把它记为已结束的命令


def test_background_advancer_lets_a_value_error_that_is_not_about_the_record_through(tmp_path, monkeypatch, capsys,
                                                                                     inline_children):
    """推进中抛出的值错误，而运行态照样读得出：不是「运行态读不出」，原样抛出（进程以回溯结束），不打那一句。"""
    def advance(advancer, meta, **kw):
        raise ValueError("not about the record")

    monkeypatch.setattr(detached, "advance_local_run", advance)
    _fake_locator(monkeypatch, available=("novaact", "midscene"))
    monkeypatch.setattr(m.compose, "build_engines", lambda **kw: {})
    reports = tmp_path / "reports"
    assert m.main(["submit", str(_write_feature(tmp_path)), "--report-dir", str(reports)]) == 0
    inline_children.settle()
    child = inline_children.only()
    assert str(child.expect_error(ValueError)) == "not about the record"
    run_id = _submitted_run_dir(reports).name
    assert "运行状态记录读不出" not in (reports / run_id / "reconcile.log").read_text(encoding="utf-8")


def test_explain_cloud_recovers_from_events_table_and_reports_missing_permission(monkeypatch, capsys):
    """云端：补取经 compose.build_cloud_event_log（events 表 Query）；表读不到或缺权限时只在 aborted_hint 写原因、退出码仍 0。"""
    from gherkai_core.model import JobResult, JobState, RunState
    from gherkai_core.project import EventRecord
    from gherkai_core.wire import event_from_line
    job = _explain_job()
    jr = JobResult(job=job, status=Status.ABORTED, session_id="s-1", error_type="timeout", message="预算用尽")
    state = RunState(run_id="r", status=Status.ABORTED, ended_at="t9",
                     jobs={job.scope_id: JobState(job.scope_id, Status.ABORTED, result_id=_CLOUD_RESULT_ID)})
    monkeypatch.setattr(m.compose, "check_backend_skew", lambda **kw: (compose.SKEW_OK, "", "1.4.1"))
    monkeypatch.setattr(m.compose, "build_cloud_stores", lambda **kw: _explain_cloud_stores(jr, state))
    asked = []

    class _Log:
        def records(self):
            lines = [
                {"type": "scope_started", "scopeId": job.scope_id},
                {"type": "scenario_started", "scenarioId": "features/login.feature:12"},
                {"type": "step_done", "scenarioId": "features/login.feature:12", "stepIndex": 0, "status": "passed"},
            ]
            return [EventRecord(scope_id=job.scope_id, kind="event", seq=i, event=event_from_line(json.dumps(d)), emit_ts=float(i))
                    for i, d in enumerate(lines, start=1)]

    def fake_build(**kw):
        asked.append(kw)
        return _Log()

    monkeypatch.setattr(m.compose, "build_cloud_event_log", fake_build)
    rc = m.main(["explain", "r", "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1", "--json"])
    sc = json.loads(capsys.readouterr().out)["scopes"][0]
    assert rc == 0 and asked[0]["events_table"] == "vfy-events" and asked[0]["scope_ids"] == [job.scope_id]
    assert sc["aborted_hint"] is None and sc["scenarios"][0]["unfinished"] is True
    assert sc["scenarios"][0]["steps"][0]["record_source"] == "events"

    class _Denied(Exception):
        pass

    def denied(**kw):
        raise _Denied("AccessDeniedException: Query")

    monkeypatch.setattr(m.compose, "build_cloud_event_log", denied)
    monkeypatch.setattr(m.compose, "is_botocore_error", lambda e: isinstance(e, _Denied))
    rc = m.main(["explain", "r", "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1", "--json"])
    sc = json.loads(capsys.readouterr().out)["scopes"][0]
    assert rc == 0 and sc["aborted_hint"].startswith("本 job 被中止，无法从事件流补取") and "vfy-events" in sc["aborted_hint"]
    assert "不可达或缺读权限" in sc["aborted_hint"]
    assert all(st["record_missing"] for scen in sc["scenarios"] for st in scen["steps"])

    # 记录解析失败（worker 违约行，不是 botocore 异常）同样降级：explain 不抛、原因写明
    class _BadLog:
        def records(self):
            raise ValueError("未知事件 type: 'brand_new_event'（不符合 worker↔core 协议）")

    monkeypatch.setattr(m.compose, "build_cloud_event_log", lambda **kw: _BadLog())
    rc = m.main(["explain", "r", "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1", "--json"])
    sc = json.loads(capsys.readouterr().out)["scopes"][0]
    assert rc == 0 and "记录读取或解析失败" in sc["aborted_hint"] and "brand_new_event" in sc["aborted_hint"]


def test_sync_run_writes_the_event_stream_db_unless_no_report(tmp_path, monkeypatch, capsys):
    """前台 run 也落 <report_dir>/<run_id>/events.db（ADR 0042 决策七）；--no-report 的零落盘运行不写。"""
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    feat = _write_feature(tmp_path)
    report_dir = tmp_path / "reports"
    assert m.main(["run", str(feat), "--json", "--report-dir", str(report_dir)]) == 0
    run_id = json.loads(capsys.readouterr().out)["run_id"]
    assert compose.events_db_path(report_dir, run_id).exists()
    before = sorted(tmp_path.rglob("events.db"))
    monkeypatch.chdir(tmp_path)  # --no-report 不给 --report-dir：若守卫失效，库会落到 cwd/reports 下，chdir 后它在 tmp_path 里才照得出
    assert m.main(["run", str(feat), "--json", "--no-report"]) == 0
    assert sorted(tmp_path.rglob("events.db")) == before  # 零落盘运行没有新建任何事件库


def test_explain_cloud_blocks_on_version_skew_before_any_cloud_read(monkeypatch, capsys):
    """云端后端第一道闸是版本 skew（先于任何云端读）：block → 以退出码 2 结束，且根本没去装 store。"""
    monkeypatch.setattr(m.compose, "check_backend_skew",
                        lambda **kw: (compose.SKEW_BLOCK, "本机 CLI 新于后端", "1.3.0"))
    monkeypatch.setattr(m.compose, "build_cloud_stores",
                        lambda **kw: (_ for _ in ()).throw(AssertionError("skew 拦下后不该装 store")))
    assert m.main(["explain", "r", "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1"]) == 2
    assert "本机 CLI 新于后端" in capsys.readouterr().err


def test_explain_cloud_reads_evidence_from_s3(monkeypatch, capsys):
    """云端后端：判定明细经 ResultStore 读回，证据经注入的 s3 client `get_object` 读回（s3:// 解引用路径）。"""
    import io

    from gherkai_core.model import JobResult, JobState, ReportRef, RunState, ScenarioResult, StepResult, Votes
    ev = json.dumps(_evidence_fixture(), ensure_ascii=False).encode("utf-8")
    job = _explain_job()
    jr = JobResult(job=job, status=Status.FAILED, session_id="s-1", scenarios=[
        ScenarioResult(scenario_id="features/login.feature:12", status=Status.FAILED, steps=[
            StepResult(index=2, status=Status.FAILED, votes=Votes(yes=0, total=1), message="断言未过",
                       report_refs=(ReportRef(kind="evidence", ref="s3://bkt/reports/r/ev.json", label="evidence"),))])])
    state = RunState(run_id="r", status=Status.FAILED, ended_at="t9",
                     jobs={job.scope_id: JobState(job.scope_id, Status.FAILED, result_id=_CLOUD_RESULT_ID)})
    monkeypatch.setattr(m.compose, "check_backend_skew", lambda **kw: (compose.SKEW_OK, "", "1.4.1"))
    monkeypatch.setattr(m.compose, "build_cloud_stores", lambda **kw: _explain_cloud_stores(jr, state))
    got = []

    class _S3:
        def get_object(self, Bucket, Key):
            got.append((Bucket, Key))
            return {"Body": io.BytesIO(ev)}

    monkeypatch.setattr(m.compose, "_make_s3_client", lambda **kw: _S3())
    rc = m.main(["explain", "r", "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1", "--json"])
    out = capsys.readouterr().out
    assert rc == 0 and got == [("bkt", "reports/r/ev.json")]
    step = json.loads(out)["scopes"][0]["scenarios"][0]["steps"][2]
    assert step["evidence"]["acts"][0]["vote"] is False and step["evidence_missing"] is None


def test_explain_cloud_not_landed_hint_carries_cloud_locator_flags(monkeypatch, capsys):
    """云端后端「判定明细尚未落地」给的 status 命令必带 --backend cloud --prefix：照抄要能运行成功，
    否则落回本机后端、报「未找到 run」还把人引去查 --report-dir（方向指错）。prefix 取已解析的那个。"""
    from gherkai_core.model import JobState, RunState
    job = _explain_job()
    state = RunState(run_id="r", status=Status.PENDING,
                     jobs={job.scope_id: JobState(job.scope_id, Status.PENDING)})

    class _NothingLanded:
        def load_job_result(self, run_id, result_id):
            raise AssertionError("运行态里没有点名明细的 job，不该读判定存储")

    run_store = _explain_cloud_stores(None, state)[0]
    monkeypatch.setattr(m.compose, "check_backend_skew", lambda **kw: (compose.SKEW_OK, "", "1.4.1"))
    monkeypatch.setattr(m.compose, "build_cloud_stores",
                        lambda **kw: (run_store, _NothingLanded(), object()))
    rc = m.main(["explain", "r", "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1"])
    err = capsys.readouterr().err
    assert rc == 0 and "判定明细尚未落地" in err
    assert "gherkai status r --backend cloud --prefix vfy- --wait" in err


@pytest.mark.parametrize("scope", [None, "features/login.feature:6"], ids=["all-scopes", "one-scope"])
def test_explain_cloud_detail_read_failure_asks_only_for_object_read_permission(monkeypatch, capsys, scope):
    """云端读被点名的那一份失败（缺读对象的权限；没有列举权限时取一个不存在的键同样是拒绝访问）：点名与不点名 scope 都以退出码 2
    结束，说明只要求读桶里对象的权限，不提列举权限；判定存储只按运行态点名的标识取了那一份。"""
    from gherkai_core.model import JobState, RunState

    job = _explain_job()
    state = RunState(run_id="r", status=Status.FAILED, ended_at="t9",
                     jobs={job.scope_id: JobState(job.scope_id, Status.FAILED, result_id=_CLOUD_RESULT_ID)})

    class _Denied(Exception):
        pass

    reads: list[str] = []

    class _DeniedStore:
        def load_job_result(self, run_id, result_id):
            reads.append(result_id)
            raise _Denied("AccessDenied: GetObject")

    run_store = _explain_cloud_stores(None, state)[0]
    monkeypatch.setattr(m.compose, "check_backend_skew", lambda **kw: (compose.SKEW_OK, "", "1.4.1"))
    monkeypatch.setattr(m.compose, "build_cloud_stores", lambda **kw: (run_store, _DeniedStore(), object()))
    monkeypatch.setattr(m.compose, "is_botocore_error", lambda e: isinstance(e, _Denied))
    rc = m.main(["explain", "r", *([scope] if scope else []), "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1"])
    err = capsys.readouterr().err
    assert rc == 2 and "explain --backend cloud 读判定明细失败：需要读桶" in err and "里对象的权限" in err
    assert "列举" not in err and "AccessDenied" in err
    assert reads == [_CLOUD_RESULT_ID]


def test_explain_filter_to_unrecorded_step_does_not_fake_job_verdict_block(tmp_path, capsys):
    """--scenario/--step 筛到一个无记录的 step 时，「零 step 记录的 job 判定块」不能凭筛后视图误打：
    has_step_records 是 job 级事实、按未筛判定树算（ADR 0042 决策四）。"""
    root, run_id = _explain_run(tmp_path)
    rc, out, _ = _explain(capsys, root, run_id, "--scenario", "密码", "--step", "3")
    assert rc == 0 and "step 3  When 点击「退出」  无记录（未执行或未上报）" in out
    assert "诊断细节见 worker 日志" not in out and "判定：" not in out
    rc, out, _ = _explain(capsys, root, run_id, "--scenario", "密码", "--step", "3", "--json")
    doc = json.loads(out)
    assert doc["scopes"][0]["has_step_records"] is True
    assert [s["record_missing"] for s in doc["scopes"][0]["scenarios"][0]["steps"]] == [True]


def test_explain_to_dict_drops_unmatched_scopes_and_keeps_job_fact():
    """多 scope 下 --scenario 只命中其一：未命中的 scope 不产空壳条目（文本与 JSON 规则一致）；命中的 scope 的
    has_step_records 不随筛选变化。"""
    from gherkai_core.model import Job, JobResult, Scenario, ScenarioResult, Status as S, Step, StepResult
    from gherkai_cli import render
    j1 = _explain_job(scope_id="a.feature:6")
    j2 = Job(scope_id="b.feature:6", scope_name="b", engine="novaact",  # 与 a 无共同 scenario → 筛 :12 时整个未命中
             scenarios=(Scenario(id="features/other.feature:5", name="其它", steps=(Step(0, "Given", "x"),)),), timeout_s=300.0)
    jr1 = JobResult(job=j1, status=S.FAILED, scenarios=[ScenarioResult(
        scenario_id="features/login.feature:12", status=S.FAILED,
        steps=[StepResult(index=0, status=S.PASSED), StepResult(index=1, status=S.FAILED, message="x")])])
    jr2 = JobResult(job=j2, status=S.PASSED, scenarios=[ScenarioResult(
        scenario_id="features/other.feature:5", status=S.PASSED, steps=[StepResult(index=0, status=S.PASSED)])])
    reader = lambda refs: (None, "no_ref")
    # 全量：两个 scope 都在
    full = render.explain_to_dict(run_id="r", status="failed", results=[jr1, jr2], evidence_reader=reader)
    assert [s["scope_id"] for s in full["scopes"]] == ["a.feature:6", "b.feature:6"]
    assert all(s["has_step_records"] for s in full["scopes"])
    # 只命中 a 里的 scenario:12 且筛到无记录的 step 3 → b 整个不出现；a 的 has_step_records 仍 True
    doc = render.explain_to_dict(run_id="r", status="failed", results=[jr1, jr2], evidence_reader=reader,
                                 scenario_ids={"features/login.feature:12"}, step_index=3)
    assert [s["scope_id"] for s in doc["scopes"]] == ["a.feature:6"]
    assert doc["scopes"][0]["has_step_records"] is True
    text = render.render_explain_text(doc)
    assert "诊断细节见 worker 日志" not in text and "b.feature:6" not in text


def test_explain_scenario_matcher_digits_are_line_numbers_only():
    """纯数字 / :数字 只当行号、不回落标题子串（与 run/plan 规则一致）；标题子串、id 全等照常。"""
    from gherkai_core.model import Scenario
    sc = Scenario(id="f.feature:12", name="重试3次后放行", steps=())
    hit = m._explain_scenario_matches
    assert hit(sc, ["3"]) is False          # 标题含 3，但 3 不是行号 → 不命中
    assert hit(sc, [":12"]) and hit(sc, ["12"]) and hit(sc, ["重试"]) and hit(sc, ["f.feature:12"])
    assert hit(sc, ["3", "重试"]) is True   # 或


def test_help_hides_internal_entry_points(capsys):
    """`gherkai --help` 不列内部入口：_reconcile / _tunnel_watch 是 submit 在后台启动的子进程入口，不供直接使用。
    argparse 对子命令传 help=SUPPRESS 会漏出「==SUPPRESS==」，故实现是「不传 help + 收窄 metavar」；本测试守住两条。"""
    import pytest

    with pytest.raises(SystemExit) as e:
        m.main(["--help"])
    assert e.value.code == 0
    out = capsys.readouterr().out
    assert "_reconcile" not in out and "_tunnel_watch" not in out and "SUPPRESS" not in out, out
    assert "submit" in out and "status" in out  # 公开命令仍在
    # 隐藏不等于禁用：内部入口照常可解析（submit 启动的后台进程靠它）
    with pytest.raises(SystemExit) as e2:
        m.main(["_reconcile", "--help"])
    assert e2.value.code == 0


def test_complete_definition_entry_points_run_the_pre_write_check(capsys):
    """两个填完入口（ADR 0048 决策 3）：没有设备请求的设备 job 在本机与云端入口都以退出码 2 被拒，校验在入口内部、调用方不另调。"""
    from types import SimpleNamespace

    from gherkai_cli import config as cfgmod
    from gherkai_cli import submission
    from gherkai_core.model import Job, Scenario, Step, Target

    scs = (Scenario(id="f:1", name="n", steps=(Step(0, "When", "x"),)),)
    device = Job(scope_id="d", scope_name="d", engine="midscene", scenarios=scs, timeout_s=1500.0, target=Target(device="android", ui_kind="web"))
    args = SimpleNamespace(region=None, profile=None, project_config=cfgmod.NO_CONFIG)
    assert submission.complete_local_definition(args, submission.Prepared(jobs=[device], steps_dir=None)) == 2
    assert "设备请求" in capsys.readouterr().err
    assert submission.complete_cloud_definition(args, None, submission.Prepared(jobs=[device], steps_dir=None), [device]) == 2
    assert "设备请求" in capsys.readouterr().err


def test_plan_marks_hit_without_handle_on_scope_target_as_ai(tmp_path, monkeypatch, capsys):
    """命中了确定性 step、但它在该 scope 的目标上没有实现（句柄声明与 worker 支持的交集不含该目标，ADR 0049 决策 3、6；0050 决策 1）：
    plan 不标「确定性」、--json 里 deterministic 为 null、stderr 说明将由 AI 执行；同引擎里在该目标上有实现的 step 照常标注。"""
    def fake_match(engine, items, steps_dir=None):
        return [({"pattern": "设备专用", "description": "只有设备句柄"} if "设备专用" in it["text"]
                 else {"pattern": "p", "description": "URL 断言"} if "页面地址" in it["text"] else None) for it in items]

    def fake_caps(engine, *, steps_dir=None, **kw):
        return {"schema_version": 2, "engine": engine, "min_grace_s": 0, "model_id": "m",
                "targets": [{"device": "desktop", "ui_kinds": ["web"]}],
                "deterministic_steps": [
                    {"pattern": "设备专用", "description": "只有设备句柄", "example": "e", "keywords": ["Given", "When", "Then"],
                     "targets": [{"device": "android", "ui_kinds": ["app"]}]},
                    {"pattern": "p", "description": "URL 断言", "example": "e", "keywords": ["Given", "When", "Then"],
                     "targets": [{"device": "desktop", "ui_kinds": ["web"]}]}]}

    monkeypatch.setattr(m.compose, "match_deterministic", fake_match)
    monkeypatch.setattr(m.compose, "query_capabilities", fake_caps)
    f = tmp_path / "d.feature"
    f.write_text('Feature: d\n  Scenario: s\n    When 设备专用 x\n    Then 页面地址匹配 "x"\n', encoding="utf-8")
    assert m.main(["plan", str(f)]) == 0
    captured = capsys.readouterr()
    assert "← 确定性: URL 断言" in captured.out and captured.out.count("← 确定性") == 1
    assert "设备专用" in captured.err and "没有实现" in captured.err and "由 AI 执行" in captured.err
    assert m.main(["plan", str(f), "--json"]) == 0
    steps = json.loads(capsys.readouterr().out)["jobs"][0]["scenarios"][0]["steps"]
    assert steps[0]["deterministic"] is None and steps[1]["deterministic"] == {"pattern": "p", "description": "URL 断言"}


def test_plan_degrades_target_check_with_a_note_when_capabilities_unavailable(tmp_path, monkeypatch, capsys):
    """能力自述取不到（超时、起不来、输出不是合法 JSON）时按目标核对那一步降级（命中仍标确定性），stderr 有降级提示而不是静默；
    match 查询照发。取不到这一结果在本次 plan 内复用：自述只问一次，标注阶段不再重问（ADR 0036 决策 4）。"""
    monkeypatch.setattr(m.compose, "match_deterministic",
                        lambda engine, items, steps_dir=None: [({"pattern": "p", "description": "URL 断言"} if "页面地址" in it["text"] else None) for it in items])
    asked: list[str] = []

    def boom(engine, *, steps_dir=None, **kw):
        asked.append(engine)
        raise compose.WorkerUnavailableError(engine, f"引擎 {engine} 的能力自述超时（60s）")

    monkeypatch.setattr(m.compose, "query_capabilities", boom)
    assert m.main(["plan", str(_det_feature(tmp_path))]) == 0
    captured = capsys.readouterr()
    assert "← 确定性: URL 断言" in captured.out
    assert "标注降级" in captured.err and "不按 scope 目标核对" in captured.err and "能力自述超时" in captured.err
    assert asked == ["novaact"]


# ---- 使用方中断（ADR 0024 终止契约「使用方中断」条；退出码见 ADR 0031 决定五）----

def _interrupting_schedule_factory(signum, acted: bool = True):
    """假 schedule：在等待 job 的位置模拟使用方中断——向本进程发 signum（CLI 装的只置标志的处理器把它记下来），
    断言 opts.interrupt() 轮询到级别 1；acted 时像真 schedule 一样回调 on_interrupt(1) 并把 job 判 aborted。"""
    import signal as _signal

    def fake_schedule(run_meta, engines, sink, opts=None, on_job_complete=None, on_event=None):
        _signal.raise_signal(signum)
        assert opts.interrupt() == 1, "CLI 装的处理器应把一次信号记成级别 1"
        status = Status.ABORTED if acted else Status.PASSED
        if acted:
            opts.on_interrupt(1)
        results = []
        for j in run_meta.jobs:
            jr = JobResult(job=j, status=status)
            results.append(jr)
            if on_job_complete is not None:
                on_job_complete(jr)
        return _execution(run_meta, results)

    return fake_schedule


@pytest.mark.parametrize(("signum", "rc"), [(__import__("signal").SIGINT, 130), (__import__("signal").SIGTERM, 143)])
def test_run_interrupted_exits_by_signal_prints_hint_and_restores_handlers(tmp_path, monkeypatch, capsys, signum, rc):
    import signal as _signal

    monkeypatch.setattr(m, "schedule", _interrupting_schedule_factory(signum))
    before = (_signal.getsignal(_signal.SIGINT), _signal.getsignal(_signal.SIGTERM))
    code = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(tmp_path / "reports")])
    assert code == rc  # 128 + 信号号，不按判定
    err = capsys.readouterr().err
    assert "正在停止 worker 并释放会话" in err
    assert "再按一次 Ctrl-C" in err and "继续计费" in err and "释放宽限为" in err  # 首次中断提示：可以再按、但会话可能释放不掉
    assert (_signal.getsignal(_signal.SIGINT), _signal.getsignal(_signal.SIGTERM)) == before  # 处理器已还原


def test_run_interrupt_not_acted_on_exits_by_verdict(tmp_path, monkeypatch, capsys):
    """中断到达时 schedule 已没有可处置的 job（on_interrupt 未被调）：退出码按判定给、不打中断提示。"""
    import signal as _signal

    monkeypatch.setattr(m, "schedule", _interrupting_schedule_factory(_signal.SIGINT, acted=False))
    code = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(tmp_path / "reports")])
    assert code == 0
    assert "收到中断信号" not in capsys.readouterr().err


def test_run_second_interrupt_prints_release_warning(tmp_path, monkeypatch, capsys):
    """再次中断（级别 2）：提示会话可能未释放、到 AWS 控制台核对（设备目标看 Device Farm，桌面目标看 AgentCore）。"""
    import signal as _signal

    def fake_schedule(run_meta, engines, sink, opts=None, on_job_complete=None, on_event=None):
        _signal.raise_signal(_signal.SIGINT)
        _signal.raise_signal(_signal.SIGINT)
        assert opts.interrupt() == 2
        opts.on_interrupt(1)
        opts.on_interrupt(2)
        return _execution(run_meta, [], stopped_by="interrupt")  # 一个 job 都没有启动：由中断那一行的结束写记 skipped

    monkeypatch.setattr(m, "schedule", fake_schedule)
    code = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(tmp_path / "reports")])
    assert code == 130
    err = capsys.readouterr().err
    assert "会话可能未释放" in err and "Device Farm" in err and "AgentCore" in err


def test_interrupt_prompts_by_level():
    """两级提示：首次说宽限秒数与「再按一次 Ctrl-C 会立即结束 worker」，第二级说立即结束 worker 并指向控制台核对两类会话。"""
    first = m._interrupt_prompt(1, grace=63.5)
    assert "释放宽限为 63.5 秒" in first and "再按一次 Ctrl-C" in first and "继续计费" in first
    second = m._interrupt_prompt(2, grace=63.5)
    assert second.startswith("再次收到中断信号，立即结束 worker") and "Device Farm" in second and "AgentCore" in second


# ---- 零 scenario 批（ADR 0041 决策一）----

@pytest.mark.parametrize("cmd", ["plan", "run", "submit"])
def test_zero_scenario_batch_is_rejected_with_exit_2(tmp_path, cmd, monkeypatch, capsys):
    """不加筛选、plan 产出零个 job 的批（只有 Feature 头）与筛空一样以退出码 2 拒绝：消息点名文件，run 不进入执行、
    submit 不落 run 记录——零 job 的 run 判 passed、退出码 0 是空洞的成功。"""
    import subprocess

    feat = tmp_path / "empty.feature"
    feat.write_text("Feature: 只有标题\n", encoding="utf-8")
    monkeypatch.setattr(m, "schedule", lambda *a, **k: pytest.fail("零 scenario 批不该进入执行"))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("零 scenario 批不该起后台推进进程"))
    reports = tmp_path / "reports"
    argv = [cmd, str(feat)] + ([] if cmd == "plan" else ["--report-dir", str(reports)])
    assert m.main(argv) == 2
    err = capsys.readouterr().err
    assert "没有可执行的 scenario" in err and str(feat) in err
    assert not reports.exists()


# ---- plan 预告确定性 step 的运行期前提（ADR 0048 决策 6、ADR 0049 决策 6）----

def test_plan_shows_step_requires_only_on_targets_that_declare_it(tmp_path, monkeypatch, capsys):
    """命中条目在该 scope 目标上带运行期前提：设备网页目标的文本标注追加前提说明、--json 的 deterministic 带 requires；
    同一条 step 在桌面网页与设备应用目标上没有前提，输出不变（不带 requires 键）。"""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "app.apk").write_bytes(b"x")  # plan 只核对安装包存在
    (tmp_path / "gherkai.toml").write_text("[apps.wiki]\nandroid = { file = 'app.apk', package = 'org.wikipedia' }\n",
                                           encoding="utf-8")

    def fake_caps(engine, *, steps_dir=None, **kw):
        return {"schema_version": 2, "engine": engine, "min_grace_s": 0, "model_id": "m",
                "targets": [{"device": "desktop", "ui_kinds": ["web"]}, {"device": "android", "ui_kinds": ["web", "app"]}],
                "deterministic_steps": [
                    {"pattern": "p", "description": "URL 断言", "example": "e", "keywords": ["Given", "When", "Then"],
                     "targets": [{"device": "desktop", "ui_kinds": ["web"]},
                                 {"device": "android", "ui_kinds": ["app"]},
                                 {"device": "android", "ui_kinds": ["web"], "requires": ["web_context"]}]}]}

    monkeypatch.setattr(m.compose, "match_deterministic",
                        lambda engine, items, steps_dir=None: [({"pattern": "p", "description": "URL 断言"}
                                                                if "页面地址" in it["text"] else None) for it in items])
    monkeypatch.setattr(m.compose, "query_capabilities", fake_caps)
    note = "（需要网页上下文；设备不提供时记为错误）"
    cases = [("", False), ("@device:android\n", True), ("@device:android @app:wiki\n", False)]
    for i, (tags, has_requires) in enumerate(cases):
        f = tmp_path / f"t{i}.feature"
        f.write_text(f'{tags}Feature: d\n  Scenario: s\n    Then 页面地址匹配 "x"\n', encoding="utf-8")
        assert m.main(["plan", str(f)]) == 0
        out = capsys.readouterr().out
        assert "← 确定性: URL 断言" in out and (note in out) is has_requires, tags
        assert m.main(["plan", str(f), "--json"]) == 0
        det = json.loads(capsys.readouterr().out)["jobs"][0]["scenarios"][0]["steps"][0]["deterministic"]
        expected = {"pattern": "p", "description": "URL 断言"}
        assert det == ({**expected, "requires": ["web_context"]} if has_requires else expected), tags


# ---- AWS 身份解析失败（ADR 0030 决定七：凭证与 region 不可用以退出码 2 结束、不冒 traceback）----

_NO_SUCH_PROFILE = "gherkai-no-such-profile"


def _no_such_profile_env(tmp_path, monkeypatch) -> None:
    """profile 名不存在、region 不从任何来源给出：解析 region 时要读这个 profile 的配置，boto3 在构造期抛 ProfileNotFound。
    AWS 配置指向空文件（不读本机真实的 ~/.aws），工作目录换到 tmp（不读仓库里的 gherkai.toml）。"""
    for k in ("AWS_REGION", "AWS_DEFAULT_REGION", "AWS_PROFILE", "AWS_DEFAULT_PROFILE", "GHERKAI_CONFIG"):
        monkeypatch.delenv(k, raising=False)
    empty = tmp_path / "aws-empty"
    empty.write_text("", encoding="utf-8")
    monkeypatch.setenv("AWS_CONFIG_FILE", str(empty))
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(empty))
    monkeypatch.chdir(tmp_path)


def _assert_identity_error(capsys) -> None:
    err = capsys.readouterr().err
    assert "AWS 身份不可用" in err and _NO_SUCH_PROFILE in err and "Traceback" not in err


def test_missing_profile_exits_2_before_side_effects_on_run_and_local_submit(tmp_path, monkeypatch, capsys):
    """run 与本机 submit：profile 读不出来时在起隧道、上传与落库之前以退出码 2 结束，submit 不留没有推进进程的 run 记录。"""
    import subprocess

    _no_such_profile_env(tmp_path, monkeypatch)
    feat = _write_feature(tmp_path)
    monkeypatch.setattr(m, "schedule", lambda *a, **k: pytest.fail("身份解析失败不该进入执行"))
    monkeypatch.setattr(m, "_setup_tunnel", lambda *a, **k: pytest.fail("身份解析失败不该起隧道"))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("身份解析失败不该起后台推进进程"))
    reports = tmp_path / "reports"
    assert m.main(["run", str(feat), "--report-dir", str(reports), "--profile", _NO_SUCH_PROFILE]) == 2
    _assert_identity_error(capsys)
    assert m.main(["submit", str(feat), "--report-dir", str(reports), "--profile", _NO_SUCH_PROFILE]) == 2
    _assert_identity_error(capsys)
    assert not reports.exists()


@pytest.mark.parametrize("cmd", ["status", "explain"])
def test_missing_profile_exits_2_on_cloud_queries(tmp_path, cmd, monkeypatch, capsys):
    _no_such_profile_env(tmp_path, monkeypatch)
    monkeypatch.setattr(m, "_cloud_skew_gate", lambda *a, **k: pytest.fail("身份解析失败不该读云端"))
    assert m.main([cmd, "r1", "--backend", "cloud", "--profile", _NO_SUCH_PROFILE]) == 2
    _assert_identity_error(capsys)


def test_missing_profile_exits_2_on_cloud_submit_before_any_cloud_read(tmp_path, monkeypatch, capsys):
    """云端 submit 在 skew 闸之前以退出码 2 结束。本机 status（含 --wait）不解析身份，见 test_settle_runs 里的同名用例。"""
    _no_such_profile_env(tmp_path, monkeypatch)
    monkeypatch.setattr(m, "_cloud_skew_gate", lambda *a, **k: pytest.fail("身份解析失败不该读云端"))
    assert m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud", "--profile", _NO_SUCH_PROFILE]) == 2
    _assert_identity_error(capsys)


# ---- 打给使用方照抄执行的 status 命令（ADR 0042 决策四）----

def test_status_hints_quote_report_dir_with_spaces(tmp_path, monkeypatch, capsys, inline_children, advanced):
    """submit 的查进度提示、explain 的 --wait 提示与记录写下之后准备执行用的文件失败时给出的 settle-runs 整条命令都对 --report-dir 加
    shell 引号：项目路径带空格时，shlex 切回来的 --report-dir 与原路径相等，命令能原样粘贴执行。"""
    import shlex
    import sqlite3

    from gherkai_core.adapters import event_log

    reports = tmp_path / "My Project" / "reports"
    assert m.main(["submit", str(_write_feature(tmp_path)), "--report-dir", str(reports)]) == 0
    inline_children.settle()
    cap = capsys.readouterr()
    run_id = cap.out.strip()
    hints = [("status", run_id, re.search(r"查进度：(gherkai status .*)$", cap.err, re.M).group(1))]
    assert m.main(["explain", run_id, "--report-dir", str(reports)]) == 0
    hints.append(("status", run_id, re.search(r"可先用 (gherkai status .*? --wait) 等到终态", capsys.readouterr().err).group(1)))

    def broken_event_log(path):
        raise sqlite3.OperationalError("unable to open database file")

    monkeypatch.setattr(event_log, "SqliteEventLog", broken_event_log)
    monkeypatch.setattr(m, "schedule", lambda *a, **k: pytest.fail("准备执行用的文件失败时不该开始执行"))
    assert m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(reports)]) == 2
    err = capsys.readouterr().err
    failed = re.search(r"run (\S+) 的记录已经写下", err).group(1)
    hints.append(("settle-runs", failed, re.search(r"再用 (gherkai settle-runs .*?) 把这个 run 记为已结束", err).group(1)))
    for verb, rid, hint in hints:
        argv = shlex.split(hint)
        assert argv[:3] == ["gherkai", verb, rid], hint
        assert argv[argv.index("--report-dir") + 1] == str(reports), hint


# ---- list-runs ----

_LR_CLI = "1.5.0"  # 用例里本 CLI 的版本（哪些 run 由当前版本写出，以它为比对对象）


def _seed_run(root: Path, run_id: str, status, job_statuses=(), *, detached: bool = False, cli_version: "str | None" = _LR_CLI,
              started_at: str = "2026-11-10T08:00:00+00:00", ended_at: "str | None" = None, message: "str | None" = None) -> None:
    """用真 LocalRunStore 在 root 下写一个 run（run_meta.json 头带写出版本，run_state.json 按 detached 带标记）。生命期锁交给
    这个用例的持有者（conftest 的 `lock_holder`），用例结束时放开。"""
    from gherkai_core.adapters.run_store.local import LocalRunStore
    from gherkai_core.model import Job, JobState, RunMeta, RunState, Scenario, Step

    jobs = {f"f.feature:{i}": JobState(f"f.feature:{i}", s) for i, s in enumerate(job_statuses)}
    # 运行定义至少要有一个 job（建 run 的入口拒绝没有 job 的运行定义）；列举只读运行态里的 job，不看这里的定义
    defined = tuple(Job(scope_id=sid, scope_name=sid, engine="novaact", timeout_s=300.0,
                        scenarios=(Scenario(id=sid, name="s", steps=(Step(index=0, keyword="Given", text="x"),)),))
                    for sid in (jobs or {"f.feature:0": None}))
    LocalRunStore(root, detached=detached, lock_holder=compose.process_lock_holder()).create_run(
        RunMeta(run_id=run_id, created_at=started_at, jobs=defined, cli_version=cli_version, deadline_at="2026-01-01T01:00:00+00:00"),
        RunState(run_id=run_id, status=status, jobs=jobs, started_at=started_at, ended_at=ended_at, message=message))


def _seed_raw_run_state(root: Path, run_id: str, text: str) -> None:
    """只写一份原样的 run_state.json（损坏的、或状态值本版本不认识的），不写 run_meta.json。"""
    (root / run_id).mkdir(parents=True, exist_ok=True)
    (root / run_id / "run_state.json").write_text(text, encoding="utf-8")


def _seed_listing_fixture(root: Path) -> None:
    """三个终态、两个未结束（一个 submit 的、一个前台的）、一个运行态损坏、一个状态值不认识、一个不是 run 的目录。"""
    S = Status
    _seed_run(root, "20261110T080000Z-a00001", S.PASSED, [S.PASSED, S.PASSED], ended_at="2026-11-10T08:05:00+00:00")
    _seed_run(root, "20261110T090000Z-a00002", S.FAILED, [S.PASSED, S.FAILED], ended_at="2026-11-10T09:05:00Z",
              cli_version="1.4.0")
    _seed_run(root, "20261110T100000Z-a00003", S.ERROR, [S.PENDING], detached=True, ended_at="2026-11-10T10:00:05+00:00",
              message="提交记录不完整", cli_version=None)
    _seed_run(root, "20261110T070000Z-b00001", S.PENDING, [S.PENDING], detached=True)
    _seed_run(root, "20261110T060000Z-b00002", S.RUNNING, [S.RUNNING, S.PENDING])
    _seed_raw_run_state(root, "20261110T050000Z-c00001", "{broken")
    _seed_raw_run_state(root, "20261110T040000Z-c00002",
                        json.dumps({"run_id": "20261110T040000Z-c00002", "status": "paused", "jobs": []}))
    (root / "20261110T030000Z-d00001").mkdir()  # 没有 run_state.json：不是 run 目录，跳过


def _list_runs_json(capsys, *argv) -> dict:
    assert m.main(["list-runs", *argv, "--json"]) == 0, capsys.readouterr().err
    return json.loads(capsys.readouterr().out)


def _table_row(out: str, run_id: str) -> list[str]:
    """人读表格里 run_id 所在那一行的各格（去掉框线与两侧空白）。"""
    line = next(ln for ln in out.splitlines() if run_id in ln)
    return [c.strip() for c in line.split("│")[1:-1]]


def test_list_runs_local_default_lists_all_ongoing_and_newest_finished_first(tmp_path, monkeypatch, capsys):
    """默认清单：全部未结束的 run、最近 N 条已结束的 run（按 run_id 即创建时间，不按结束时间），无法读取的找到即列出、不占 N 的名额，
    整体按 run_id 降序；没有 run_state.json 的目录不列。"""
    monkeypatch.setattr(m, "_installed_version", lambda: _LR_CLI)
    root = tmp_path / "reports"
    _seed_listing_fixture(root)
    # 早创建、晚结束：在已结束的 run 里创建得最早，结束得最晚
    _seed_run(root, "20261110T075000Z-a00000", Status.PASSED, [Status.PASSED], started_at="2026-11-10T07:50:00+00:00",
              ended_at="2026-11-10T12:00:00+00:00")
    doc = _list_runs_json(capsys, "--report-dir", str(root))
    assert [r["run_id"] for r in doc["runs"]] == [
        "20261110T100000Z-a00003", "20261110T090000Z-a00002", "20261110T080000Z-a00001", "20261110T075000Z-a00000",
        "20261110T070000Z-b00001", "20261110T060000Z-b00002", "20261110T050000Z-c00001", "20261110T040000Z-c00002"]
    # --limit 只约束已结束的部分，按创建时间取最近的：留下 a00003、a00002，结束得最晚的 a00000 不在其中
    doc = _list_runs_json(capsys, "--report-dir", str(root), "--limit", "2")
    assert [r["run_id"] for r in doc["runs"]] == [
        "20261110T100000Z-a00003", "20261110T090000Z-a00002", "20261110T070000Z-b00001", "20261110T060000Z-b00002",
        "20261110T050000Z-c00001", "20261110T040000Z-c00002"]


def test_list_runs_local_limit_does_not_cut_ongoing_runs(tmp_path, monkeypatch, capsys):
    """未结束的 run 多于 --limit 时全部列出：--limit 只截已结束的部分（夹具里未结束的有两条，--limit 1）。"""
    monkeypatch.setattr(m, "_installed_version", lambda: _LR_CLI)
    root = tmp_path / "reports"
    _seed_listing_fixture(root)
    doc = _list_runs_json(capsys, "--report-dir", str(root), "--limit", "1")
    assert [r["run_id"] for r in doc["runs"]] == [
        "20261110T100000Z-a00003", "20261110T070000Z-b00001", "20261110T060000Z-b00002",
        "20261110T050000Z-c00001", "20261110T040000Z-c00002"]


def test_list_runs_local_status_filter_keeps_unreadable_rows_and_limit_only_on_finished(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(m, "_installed_version", lambda: _LR_CLI)
    root = tmp_path / "reports"
    _seed_listing_fixture(root)
    doc = _list_runs_json(capsys, "--report-dir", str(root), "--status", "running", "--status", "failed")
    assert [(r["run_id"], r.get("status")) for r in doc["runs"]] == [
        ("20261110T090000Z-a00002", "failed"), ("20261110T060000Z-b00002", "running"),
        ("20261110T050000Z-c00001", None), ("20261110T040000Z-c00002", None)]
    doc = _list_runs_json(capsys, "--report-dir", str(root), "--status", "passed", "--status", "failed", "--status", "error",
                          "--limit", "2")
    assert [r["run_id"] for r in doc["runs"] if not r.get("unreadable")] == [
        "20261110T100000Z-a00003", "20261110T090000Z-a00002"]


def test_list_runs_local_json_shape_and_writer_version_marking(tmp_path, monkeypatch, capsys):
    """顶层是所查的落点（解析后的绝对路径）与执行这次清单的版本 cli_version；每项的键按出现条件给出，cli_version 恒有：
    写出这个 run 的版本，读不到为 null，不为 null 且与顶层相同即由当前版本写出。"""
    monkeypatch.setattr(m, "_installed_version", lambda: _LR_CLI)
    monkeypatch.chdir(tmp_path)
    _seed_listing_fixture(tmp_path / "reports")
    doc = _list_runs_json(capsys, "--report-dir", "reports")
    assert set(doc) == {"backend", "report_dir", "cli_version", "runs"}
    assert doc["backend"] == "local" and doc["report_dir"] == str((tmp_path / "reports").resolve())
    assert doc["cli_version"] == _LR_CLI
    by = {r["run_id"]: r for r in doc["runs"]}
    assert by["20261110T080000Z-a00001"] == {
        "run_id": "20261110T080000Z-a00001", "status": "passed", "started_at": "2026-11-10T08:00:00+00:00",
        "ended_at": "2026-11-10T08:05:00+00:00", "job_counts": {"passed": 2}, "detached": False,
        "cli_version": _LR_CLI}  # 当前版本写出：与顶层的 cli_version 相同
    assert by["20261110T090000Z-a00002"]["cli_version"] == "1.4.0"
    assert by["20261110T090000Z-a00002"]["job_counts"] == {"passed": 1, "failed": 1}
    assert by["20261110T100000Z-a00003"]["cli_version"] is None and by["20261110T100000Z-a00003"]["message"] == "提交记录不完整"
    assert by["20261110T070000Z-b00001"]["detached"] is True and "ended_at" not in by["20261110T070000Z-b00001"]
    # 运行态解析不了的项只有 run_id、unreadable 与 cli_version（没有 run_meta.json，读不到写出版本）
    assert by["20261110T050000Z-c00001"] == {"run_id": "20261110T050000Z-c00001", "unreadable": True, "cli_version": None}
    assert by["20261110T040000Z-c00002"] == {"run_id": "20261110T040000Z-c00002", "unreadable": True, "cli_version": None}
    assert all("cli_version" in r for r in doc["runs"])
    # 本 CLI 版本未知（未装成包）时顶层为 null，每项照常给出写出版本
    monkeypatch.setattr(m, "_installed_version", lambda: None)
    doc = _list_runs_json(capsys, "--report-dir", "reports")
    assert doc["cli_version"] is None
    assert {r["run_id"]: r["cli_version"] for r in doc["runs"]}["20261110T080000Z-a00001"] == _LR_CLI


def test_list_runs_local_wrongly_typed_fields_are_unreadable_rows_and_unknown_versions(tmp_path, monkeypatch, capsys):
    """运行态里清单要输出的字段类型不对（起始时刻是数字、run 级 message 是对象、job 状态值不合法）列为无法读取；写出版本不是字符串
    读作未知。--json 不带出非字符串的值，人读表格照常输出。"""
    monkeypatch.setattr(m, "_installed_version", lambda: _LR_CLI)
    root = tmp_path / "reports"
    bad_states = {"20261110T080000Z-e00001": {"started_at": 1731225600},
                  "20261110T080000Z-e00002": {"message": {"text": "m"}},
                  "20261110T080000Z-e00003": {"jobs": [{"scope_id": "s", "status": 3}]}}
    for run_id, bad in bad_states.items():
        _seed_raw_run_state(root, run_id, json.dumps({"run_id": run_id, "status": "passed", "jobs": [], **bad}))
    numeric_writer = "20261110T090000Z-e00004"
    _seed_run(root, numeric_writer, Status.PASSED, [Status.PASSED], ended_at="2026-11-10T09:05:00+00:00")
    (root / numeric_writer / "run_meta.json").write_text(json.dumps({"schema_version": 1, "cli_version": 150}), encoding="utf-8")

    by = {r["run_id"]: r for r in _list_runs_json(capsys, "--report-dir", str(root))["runs"]}
    for run_id in bad_states:
        assert by[run_id] == {"run_id": run_id, "unreadable": True, "cli_version": None}
    assert by[numeric_writer]["status"] == "passed" and by[numeric_writer]["cli_version"] is None
    assert m.main(["list-runs", "--report-dir", str(root)]) == 0
    out = capsys.readouterr().out
    for run_id in bad_states:
        assert _table_row(out, run_id)[1:] == [m.render.UNREADABLE_RUN_STATUS, "-", "-", "-", "未知"]  # 没有任何提示：提示列不出现
    # 当前版本已知、没有任何一行由它写出、也没有提示列：图例照样是第一行（它说明比对的基准，不承诺有带星的行）
    assert out.splitlines()[0] == f"当前 gherkai 版本 {_LR_CLI}（版本列以 * 标出）" and " *" not in out.split("\n", 1)[1]
    assert _table_row(out, numeric_writer)[5] == "未知"
    assert "提示" not in _table_row(out, "run_id")


def test_list_runs_local_text_table_marks_version_and_unreadable(tmp_path, monkeypatch, capsys, request):
    monkeypatch.setattr(m, "_installed_version", lambda: _LR_CLI)
    # 时刻列换算到本机时区显示：把本机时区钉在 UTC+8，断言才不随执行测试的机器变化
    import time as _time
    monkeypatch.setenv("TZ", "Asia/Shanghai")
    _time.tzset()
    request.addfinalizer(lambda: (monkeypatch.undo(), _time.tzset()))
    root = tmp_path / "reports"
    _seed_listing_fixture(root)
    assert m.main(["list-runs", "--report-dir", str(root)]) == 0
    out = capsys.readouterr().out
    # 表格上方一行图例点明当前版本；版本列恒有值，当前版本写出的在版本串后带 *
    assert out.splitlines()[0] == f"当前 gherkai 版本 {_LR_CLI}（版本列以 * 标出）"
    header = _table_row(out, "run_id")
    assert header == ["run_id", "状态", "开始（本地）", "结束（本地）", "job", "版本", "提示"]
    same = _table_row(out, "20261110T080000Z-a00001")
    # job 的状态都与 run 的状态相同：只给总数，不把状态列再说一遍
    assert same == ["20261110T080000Z-a00001", "passed", "2026-11-10 16:00:00", "2026-11-10 16:05:00", "2",
                    f"{_LR_CLI} *", ""]  # UTC 08:00 → 本机 16:00
    # 有 job 的状态与 run 的状态不同：总数后括注各状态的个数；其它版本写出的只给版本串、不带 *
    assert _table_row(out, "20261110T090000Z-a00002")[4:6] == ["2（passed 1 · failed 1）", "1.4.0"]
    errored = _table_row(out, "20261110T100000Z-a00003")
    assert errored[5] == "未知" and errored[6] == "提交记录不完整"
    assert errored[4] == "1（pending 1）"  # 只有一种 job 状态、但与 run 的状态不同：同样括注
    # 后台执行标记只作描述：未结束的前台 run 与 submit 的 run 都没有提示
    assert _table_row(out, "20261110T060000Z-b00002")[6] == ""
    assert _table_row(out, "20261110T070000Z-b00001")[6] == ""
    broken = _table_row(out, "20261110T050000Z-c00001")
    assert broken == ["20261110T050000Z-c00001", m.render.UNREADABLE_RUN_STATUS, "-", "-", "-", "未知", ""]
    assert "20261110T030000Z-d00001" not in out


def test_list_runs_local_text_table_without_a_known_current_version_has_no_legend_and_no_star(tmp_path, monkeypatch, capsys):
    """本 CLI 版本取不到（未装成包）时不打图例、没有哪一行带 *，版本列照常给出各 run 的写出版本。"""
    monkeypatch.setattr(m, "_installed_version", lambda: None)
    root = tmp_path / "reports"
    _seed_listing_fixture(root)
    assert m.main(["list-runs", "--report-dir", str(root)]) == 0
    out = capsys.readouterr().out
    assert "当前 gherkai 版本" not in out and "*" not in out
    assert out.lstrip().startswith("╭")  # 表格直接开头，上方没有图例行
    assert _table_row(out, "20261110T080000Z-a00001")[5] == _LR_CLI
    assert _table_row(out, "20261110T090000Z-a00002")[5] == "1.4.0"
    assert _table_row(out, "20261110T100000Z-a00003")[5] == "未知"


def test_list_runs_local_unreadable_rows_still_carry_the_writer_version(tmp_path, monkeypatch, capsys):
    """运行态解析失败、提交记录头部读得到的 run：机读项照常带写出版本，人读版本列照常给出，当前版本写出的同样带 *。"""
    monkeypatch.setattr(m, "_installed_version", lambda: _LR_CLI)
    root = tmp_path / "reports"
    mine, older = "20261110T090000Z-g00001", "20261110T080000Z-g00002"
    _seed_run(root, mine, Status.PASSED, [Status.PASSED])
    _seed_run(root, older, Status.PASSED, [Status.PASSED], cli_version="1.4.0")
    for run_id in (mine, older):
        (root / run_id / "run_state.json").write_text("{broken", encoding="utf-8")
    by = {r["run_id"]: r for r in _list_runs_json(capsys, "--report-dir", str(root))["runs"]}
    assert by[mine] == {"run_id": mine, "unreadable": True, "cli_version": _LR_CLI}
    assert by[older] == {"run_id": older, "unreadable": True, "cli_version": "1.4.0"}
    assert m.main(["list-runs", "--report-dir", str(root)]) == 0
    out = capsys.readouterr().out
    assert _table_row(out, mine)[1:] == [m.render.UNREADABLE_RUN_STATUS, "-", "-", "-", f"{_LR_CLI} *"]
    assert _table_row(out, older)[1:] == [m.render.UNREADABLE_RUN_STATUS, "-", "-", "-", "1.4.0"]


def test_list_runs_local_text_table_gives_an_out_of_range_time_as_is(tmp_path, monkeypatch, capsys, request):
    """时刻换算到本机时区后越出可表示的范围：该格原样给出 ISO 时刻，整张表照常输出、退出码 0。"""
    monkeypatch.setattr(m, "_installed_version", lambda: _LR_CLI)
    import time as _time
    monkeypatch.setenv("TZ", "Asia/Shanghai")  # UTC+8：9999-12-31 23:59:59 UTC 换算后落在 10000 年
    _time.tzset()
    request.addfinalizer(lambda: (monkeypatch.undo(), _time.tzset()))
    root = tmp_path / "reports"
    edge = "9999-12-31T23:59:59+00:00"
    _seed_run(root, "20261110T090000Z-f00001", Status.PASSED, [Status.PASSED], started_at=edge,
              ended_at="2026-11-10T08:05:00+00:00")
    _seed_run(root, "20261110T080000Z-f00002", Status.PASSED, [Status.PASSED], ended_at="2026-11-10T08:05:00+00:00")
    assert m.main(["list-runs", "--report-dir", str(root)]) == 0
    out = capsys.readouterr().out
    assert _table_row(out, "20261110T090000Z-f00001")[2:4] == [edge, "2026-11-10 16:05:00"]
    assert _table_row(out, "20261110T080000Z-f00002")[2] == "2026-11-10 16:00:00"


def test_list_runs_local_empty_hints_name_the_directory_and_tell_missing_from_empty(tmp_path, monkeypatch, capsys):
    """空清单只打一行：目录不存在与目录下没有 run 两种说法，都点名解析后的目录、提示核对定位参数；--json 下没有提示，
    只有落点、当前版本与空数组。"""
    monkeypatch.setattr(m, "_installed_version", lambda: _LR_CLI)
    missing = tmp_path / "nope"
    assert m.main(["list-runs", "--report-dir", str(missing)]) == 0
    out = capsys.readouterr().out.strip()
    assert out.count("\n") == 0 and str(missing.resolve()) in out and "不存在" in out and "--report-dir" in out
    empty = tmp_path / "reports"
    empty.mkdir()
    assert m.main(["list-runs", "--report-dir", str(empty)]) == 0
    out = capsys.readouterr().out.strip()
    assert out.count("\n") == 0 and f"{empty.resolve()} 下没有任何 run" in out and "--report-dir" in out
    _seed_run(empty, "20261110T080000Z-a00001", Status.PASSED, [Status.PASSED], ended_at="t")
    assert m.main(["list-runs", "--report-dir", str(empty), "--status", "failed", "--status", "error"]) == 0
    assert "没有状态为 failed、error 的 run" in capsys.readouterr().out
    cap_json = _list_runs_json(capsys, "--report-dir", str(missing))
    assert cap_json == {"backend": "local", "report_dir": str(missing.resolve()), "cli_version": _LR_CLI, "runs": []}


def test_list_runs_local_unreadable_report_dir_exits_2(tmp_path, capsys):
    import os
    if os.geteuid() == 0:
        pytest.skip("root 不受目录权限约束")
    root = tmp_path / "reports"
    _seed_run(root, "20261110T080000Z-a00001", Status.PASSED, [Status.PASSED], ended_at="t")
    root.chmod(0)
    try:
        rc = m.main(["list-runs", "--report-dir", str(root)])
    finally:
        root.chmod(0o755)
    cap = capsys.readouterr()
    assert rc == 2 and cap.out == "" and str(root.resolve()) in cap.err and "Traceback" not in cap.err


@pytest.mark.parametrize("argv", [["--limit", "0"], ["--limit", "-3"], ["--limit", "x"], ["--status", "paused"]])
def test_list_runs_rejects_bad_limit_and_status_with_exit_2(argv, capsys):
    with pytest.raises(SystemExit) as ei:
        m.main(["list-runs", *argv])
    assert ei.value.code == 2
    assert ("须为正整数" in capsys.readouterr().err) is (argv[0] == "--limit")


def test_list_runs_reads_report_dir_from_the_project_config_file(tmp_path, monkeypatch, capsys):
    """定位参数的取值来源与 status 相同，含配置文件那一层（路径相对配置文件所在目录）。"""
    monkeypatch.delenv("GHERKAI_CONFIG", raising=False)
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "gherkai.toml").write_text('[common]\nreport-dir = "out"\n', encoding="utf-8")
    _seed_run(proj / "out", "20261110T080000Z-a00001", Status.PASSED, [Status.PASSED], ended_at="t")
    monkeypatch.chdir(tmp_path)
    doc = _list_runs_json(capsys, "--config", str(proj / "gherkai.toml"))
    assert doc["report_dir"] == str((proj / "out").resolve()) and len(doc["runs"]) == 1


# 云端：skew 闸记一笔、runs 表句柄与 DescribeTable 是替身、DynamoDBRunStore 换成按调用参数返回预置清单的替身

def _listing(run_id: str, status, *, detached: bool = True, header=(1, _LR_CLI), jobs=()):
    from gherkai_core.model import JobState, RunListing, RunState
    state = None if status is None else RunState(run_id=run_id, status=status,
                                                 jobs={f"s{i}": JobState(f"s{i}", s) for i, s in enumerate(jobs)},
                                                 started_at="2026-11-10T08:00:00+00:00")
    return RunListing(run_id=run_id, state=state, detached=detached, header=header)


def _cloud_list_runs_env(monkeypatch, tmp_path, *, index_status="ACTIVE", index_list=True, parts=None, list_error=None,
                         skew_rc=None):
    """把云端 list-runs 的 AWS 边界换成替身，返回记录调用顺序的列表。index_status：状态分组索引的状态，None 表示表上没有
    这个索引；index_list=False 时 DescribeTable 的响应里没有索引清单这个字段（表上没有任何索引）。parts：状态元组 → 该次
    端口调用返回的列举项，值为异常时该次调用抛出它（只让某一次调用失败）；list_error：每次调用都抛出的异常。"""
    from types import SimpleNamespace

    from gherkai_core.adapters.run_store import ddb as _ddb
    from gherkai_runtime import names as _nm

    for k in ("AWS_DDB_TABLE", "AWS_RESOURCE_PREFIX", "AWS_PROFILE", "GHERKAI_CONFIG"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(m, "_installed_version", lambda: _LR_CLI)
    calls: list = []

    def skew(target, **kw):
        calls.append(("skew", target.prefix))
        return skew_rc, None

    def make_table(table, *, region, profile):
        def describe_table(*, TableName):
            calls.append(("describe", TableName))
            if not index_list:
                return {"Table": {"TableName": TableName}}
            # 清单里排在前面的另一个索引恒为 ACTIVE：就绪判定只看状态分组索引，它缺失或未就绪时不被这个索引顶替
            gsis = [{"IndexName": "other-index", "IndexStatus": "ACTIVE"}]
            if index_status is not None:
                gsis.append({"IndexName": _nm.RUNS_STATUS_GROUP_GSI, "IndexStatus": index_status})
            return {"Table": {"TableName": TableName, "GlobalSecondaryIndexes": gsis}}
        return SimpleNamespace(name=table, meta=SimpleNamespace(client=SimpleNamespace(describe_table=describe_table)))

    class FakeStore:
        def __init__(self, table, **kw):
            calls.append(("store", table.name, kw.get("list_index_name")))

        def list_runs(self, statuses, *, limit):
            calls.append(("list", [s.value for s in statuses], limit))
            if list_error is not None:
                raise list_error
            got = (parts or {}).get(tuple(s.value for s in statuses), [])
            if isinstance(got, Exception):
                raise got
            return list(got)

    monkeypatch.setattr(m, "_cloud_skew_gate", skew)
    monkeypatch.setattr(compose, "_make_ddb_table", make_table)
    monkeypatch.setattr(_ddb, "DynamoDBRunStore", FakeStore)
    return calls


_TERMINAL_VALUES = ["passed", "failed", "error", "skipped", "aborted"]


def test_list_runs_cloud_checks_skew_then_index_then_lists_ongoing_before_finished(tmp_path, monkeypatch, capsys):
    """调用顺序：版本 skew 闸 → DescribeTable 判索引就绪 → 装配注入状态分组索引名 → 先非终态（不截断）后终态（截 N）；
    --report-dir 在云端被忽略、不报错；--json 顶层是前缀、region、解析后的表名与当前版本。"""
    from gherkai_runtime import names as _nm

    calls = _cloud_list_runs_env(monkeypatch, tmp_path)
    doc = _list_runs_json(capsys, "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1", "--report-dir", "whatever")
    table = _nm.default_name("vfy-", _nm.BASE_RUNS_TABLE)
    assert calls == [("skew", "vfy-"), ("describe", table), ("store", table, _nm.RUNS_STATUS_GROUP_GSI),
                     ("list", ["pending", "running"], None), ("list", _TERMINAL_VALUES, 20)]
    assert doc == {"backend": "cloud", "prefix": "vfy-", "region": "us-east-1", "ddb_table": table, "cli_version": _LR_CLI,
                   "runs": []}
    assert "whatever" not in json.dumps(doc)


def test_list_runs_cloud_merge_keeps_the_later_read_filters_by_read_back_status_and_cuts_finished(tmp_path, monkeypatch, capsys):
    """端口不复筛：非终态那次读回已是终态的 run 归入终态部分、同受 --limit 截取；两次都有的 run 保留后一次读回的；
    无法读取的找到即列出；--status 只含一侧时只做那一次调用，读回状态不在请求里的行被滤掉。"""
    S = Status
    parts = {
        ("pending", "running"): [_listing("20261110T120000Z-a", S.PENDING), _listing("20261110T110000Z-c", S.RUNNING),
                                 _listing("20261110T100000Z-b", S.RUNNING), _listing("20261110T095000Z-x", S.PASSED)],
        tuple(_TERMINAL_VALUES): [_listing("20261110T100000Z-b", S.PASSED), _listing("20261110T090000Z-d", S.FAILED),
                                  _listing("20261110T080000Z-e", S.ERROR), _listing("20261110T070000Z-u", None)],
    }
    _cloud_list_runs_env(monkeypatch, tmp_path, parts=parts)
    doc = _list_runs_json(capsys, "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1", "--limit", "2")
    assert [(r["run_id"], r.get("status")) for r in doc["runs"]] == [
        ("20261110T120000Z-a", "pending"), ("20261110T110000Z-c", "running"), ("20261110T100000Z-b", "passed"),
        ("20261110T095000Z-x", "passed"), ("20261110T070000Z-u", None)]

    calls = _cloud_list_runs_env(monkeypatch, tmp_path, parts={("running",): [
        _listing("20261110T110000Z-c", S.RUNNING), _listing("20261110T100000Z-y", S.PASSED)]})
    doc = _list_runs_json(capsys, "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1", "--status", "running")
    assert [r["run_id"] for r in doc["runs"]] == ["20261110T110000Z-c"]
    assert [c for c in calls if c[0] == "list"] == [("list", ["running"], None)]

    calls = _cloud_list_runs_env(monkeypatch, tmp_path)
    _list_runs_json(capsys, "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1", "--status", "aborted",
                    "--status", "passed", "--limit", "5")
    assert [c for c in calls if c[0] == "list"] == [("list", ["passed", "aborted"], 5)]  # 状态按固定顺序，不按给出的顺序


def test_list_runs_cloud_limit_does_not_cut_ongoing_runs(tmp_path, monkeypatch, capsys):
    """未结束的 run 多于 --limit 时全部列出：合并只截读回为终态的部分（三条未结束、两条已结束，--limit 1）。"""
    S = Status
    parts = {
        ("pending", "running"): [_listing("20261110T120000Z-a", S.PENDING), _listing("20261110T110000Z-b", S.PENDING),
                                 _listing("20261110T100000Z-c", S.RUNNING)],
        tuple(_TERMINAL_VALUES): [_listing("20261110T090000Z-d", S.PASSED), _listing("20261110T080000Z-e", S.FAILED)],
    }
    _cloud_list_runs_env(monkeypatch, tmp_path, parts=parts)
    doc = _list_runs_json(capsys, "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1", "--limit", "1")
    assert [r["run_id"] for r in doc["runs"]] == [
        "20261110T120000Z-a", "20261110T110000Z-b", "20261110T100000Z-c", "20261110T090000Z-d"]


@pytest.mark.parametrize("index_status, index_list, needles", [
    (None, False, ("还没有 run 清单索引",)),  # 响应里没有索引清单
    (None, True, ("还没有 run 清单索引",)),  # 表上只有另一个 ACTIVE 的索引
    ("CREATING", True, ("还在建立", "请部署方检查索引的建立进度")),
    ("DELETING", True, ("正在被删除",)),
], ids=["no-index-list", "only-other-index-active", "creating", "deleting"])
def test_list_runs_cloud_index_missing_or_not_ready_exits_2_before_any_query(index_status, index_list, needles, tmp_path,
                                                                             monkeypatch, capsys):
    """索引缺失或未就绪：退出码 2、提示点名索引，不装配 store、不发查询。"""
    calls = _cloud_list_runs_env(monkeypatch, tmp_path, index_status=index_status, index_list=index_list)
    rc = m.main(["list-runs", "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1", "--json"])
    cap = capsys.readouterr()
    assert rc == 2 and cap.out == "" and "status_group-run_id-index" in cap.err
    assert all(n in cap.err for n in needles)
    assert [c[0] for c in calls] == ["skew", "describe"]


def test_list_runs_cloud_index_updating_is_let_through(tmp_path, monkeypatch, capsys):
    _cloud_list_runs_env(monkeypatch, tmp_path, index_status="UPDATING")
    assert _list_runs_json(capsys, "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1")["runs"] == []


def test_list_runs_cloud_skew_block_exits_2_before_reading_the_table(tmp_path, monkeypatch, capsys):
    calls = _cloud_list_runs_env(monkeypatch, tmp_path, skew_rc=2)
    assert m.main(["list-runs", "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1"]) == 2
    assert calls == [("skew", "vfy-")]


def test_list_runs_cloud_read_failures_exit_2_without_a_partial_list(tmp_path, monkeypatch, capsys):
    """AWS 错误（无权限一类）与批量读回重试耗尽都以退出码 2 结束、stdout 没有清单；不打印回溯。"""
    from botocore.exceptions import ClientError

    from gherkai_core.adapters.run_store.ddb import RunListingIncomplete

    denied = ClientError({"Error": {"Code": "AccessDeniedException", "Message": "not authorized"}}, "Query")
    _cloud_list_runs_env(monkeypatch, tmp_path, list_error=denied)
    assert m.main(["list-runs", "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1"]) == 2
    cap = capsys.readouterr()
    assert cap.out == "" and "读不到运行状态表 vfy-runs" in cap.err and "AccessDeniedException" in cap.err
    _cloud_list_runs_env(monkeypatch, tmp_path, list_error=RunListingIncomplete("vfy-runs", 3, 5))
    assert m.main(["list-runs", "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1"]) == 2
    cap = capsys.readouterr()
    assert cap.out == "" and "没有读回" in cap.err and "Traceback" not in cap.err


@pytest.mark.parametrize("as_json", [False, True])
@pytest.mark.parametrize("error_kind", ["denied", "incomplete"])
def test_list_runs_cloud_failure_in_the_finished_part_gives_no_partial_list(error_kind, as_json, tmp_path, monkeypatch, capsys):
    """非终态那次已读到 run、终态那次失败：同样以退出码 2 结束，stdout 不输出已读到的那部分（人读与 --json 都一样）。"""
    from botocore.exceptions import ClientError

    from gherkai_core.adapters.run_store.ddb import RunListingIncomplete

    error = (ClientError({"Error": {"Code": "AccessDeniedException", "Message": "not authorized"}}, "Query")
             if error_kind == "denied" else RunListingIncomplete("vfy-runs", 3, 5))
    calls = _cloud_list_runs_env(monkeypatch, tmp_path, parts={
        ("pending", "running"): [_listing("20261110T120000Z-a", Status.RUNNING)], tuple(_TERMINAL_VALUES): error})
    argv = ["list-runs", "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1"] + (["--json"] if as_json else [])
    assert m.main(argv) == 2
    cap = capsys.readouterr()
    assert cap.out == "" and "20261110T120000Z-a" not in cap.err and "Traceback" not in cap.err
    assert ("AccessDeniedException" if error_kind == "denied" else "没有读回") in cap.err
    assert [c for c in calls if c[0] == "list"] == [("list", ["pending", "running"], None), ("list", _TERMINAL_VALUES, 20)]


def test_list_runs_cloud_empty_hint_names_prefix_region_and_table(tmp_path, monkeypatch, capsys):
    _cloud_list_runs_env(monkeypatch, tmp_path)
    assert m.main(["list-runs", "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1", "--ddb-table", "my-runs"]) == 0
    out = capsys.readouterr().out.strip()
    assert out.count("\n") == 0 and "vfy-" in out and "us-east-1" in out and "my-runs" in out and "--prefix" in out


def test_list_runs_cloud_missing_profile_exits_2_before_reading_the_cloud(tmp_path, monkeypatch, capsys):
    _no_such_profile_env(tmp_path, monkeypatch)
    monkeypatch.setattr(m, "_cloud_skew_gate", lambda *a, **k: pytest.fail("身份解析失败不该读云端"))
    assert m.main(["list-runs", "--backend", "cloud", "--profile", _NO_SUCH_PROFILE]) == 2
    _assert_identity_error(capsys)
