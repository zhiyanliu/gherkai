"""cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不烧 AWS），

验证落盘三层产物 + --json 输出形状（单一可解析 JSON 文档，回归护栏 ADR 0016/0027）。
"""
from __future__ import annotations

import json
from pathlib import Path

from core.model import JobResult, RunResult, Status

from cli import __main__ as m


def _fake_schedule_factory():
    """造一个不起 worker 的假 schedule：发一个事件给 sink（验证进度路由）+ 把 run_meta 合成 RunResult。"""
    from core.model import ScopeStarted

    def fake_schedule(run_meta, engines, sink, opts=None):
        for j in run_meta.jobs:
            sink(ScopeStarted(scope_id=j.scope_id))  # 走 sink 路径，让 [event] 进度被发出
        return RunResult(
            run_meta=run_meta,
            status=Status.PASSED,
            jobs=[JobResult(job=j, status=Status.PASSED) for j in run_meta.jobs],
        )
    return fake_schedule


def _write_feature(tmp_path: Path) -> Path:
    feat = tmp_path / "demo.feature"
    feat.write_text(
        "Feature: demo\n  Scenario: s\n    When \"做点啥\"\n", encoding="utf-8"
    )
    return feat


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
    assert "RunReport:" not in out and "RunReport:" in err  # 落点提示 → stderr


def test_text_mode_summary_on_stdout_progress_on_stderr(tmp_path, monkeypatch, capsys):
    # 非 --json（人看模式）：核心产出=文本汇总 → stdout；进度/落点 → stderr。
    # 这样 `cli run … > summary.txt` 拿到纯净汇总，进度照样在终端可见。
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    feat = _write_feature(tmp_path)
    rc = m.main(["run", str(feat), "--report-dir", str(tmp_path / "reports")])
    assert rc == 0
    captured = capsys.readouterr()
    out, err = captured.out, captured.err
    # 主输出（文本汇总）在 stdout
    assert "RunResult" in out and "总状态" in out
    # 进度/event/落点提示在 stderr，不污染 stdout。event 行前缀 `[core <scope>:event]`，与 worker 透传行
    # `[worker <scope>:err]` 同骨架 `[producer scope:kind]`（并发跑批时区分来源、scope 同列可竖扫）。
    assert "plan:" in err and ":event]" in err and "RunReport:" in err
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
    assert len(list((run_dir / "jobs").glob("*.json"))) == 1
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


def test_assertion_votes_below_one_rejected(tmp_path, monkeypatch, capsys):
    # --assertion-votes < 1 在入口被拒（退出码 2）：否则 worker 跑 0 次 AI 断言——
    # 0 → 全判失败（假阴性）；负数 → 0>负/2=True 全绿但零 AI 调用（假阳性，最危险）。绝不让坏值流进 worker。
    called = {"n": 0}
    def spy_schedule(*a, **k):
        called["n"] += 1
        return _fake_schedule_factory()(*a, **k)
    monkeypatch.setattr(m, "schedule", spy_schedule)
    feat = _write_feature(tmp_path)
    for bad in ("0", "-1"):
        rc = m.main(["run", str(feat), "--assertion-votes", bad, "--no-report"])
        assert rc == 2, f"--assertion-votes {bad} 应退出码 2"
    assert called["n"] == 0  # schedule 从未被调用——坏值在入口就被拦，没白起 worker
    err = capsys.readouterr().err
    assert "必须 ≥ 1" in err


# ---- plan 预检（dry-run）：纯本地、不连 AWS、不烧钱 ----

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
    assert "plan（预检，未真跑）" in out
    assert "1 job(scope)" in out
    assert "engine=midscene" in out          # @engine tag 生效
    assert "Then" in out and "对吗" in out    # step 预览


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
    # 同 scope 多 engine → PlanError，预检在真跑前拦截、退 2（省钱）
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
    """假 schedule：把传入 opts 存进 opts_box、按指定 status 合成 RunResult（验退出码/参数映射）。"""
    def fake(run_meta, engines, sink, opts=None):
        opts_box["opts"] = opts
        return RunResult(run_meta=run_meta, status=status,
                         jobs=[JobResult(job=j, status=status) for j in run_meta.jobs])
    return fake


def test_run_exit_code_1_on_failed(tmp_path, monkeypatch, capsys):
    box = {}
    monkeypatch.setattr(m, "schedule", _capturing_schedule(Status.FAILED, box))
    rc = m.main(["run", str(_write_feature(tmp_path)), "--no-report"])
    assert rc == 1  # 跑完但有 failed → 退 1（CI 据此判红）


def test_run_exit_code_1_on_error(tmp_path, monkeypatch, capsys):
    box = {}
    monkeypatch.setattr(m, "schedule", _capturing_schedule(Status.ERROR, box))
    rc = m.main(["run", str(_write_feature(tmp_path)), "--no-report"])
    assert rc == 1


def test_run_schedule_opts_mapping(tmp_path, monkeypatch, capsys):
    box = {}
    monkeypatch.setattr(m, "schedule", _capturing_schedule(Status.PASSED, box))
    m.main(["run", str(_write_feature(tmp_path)), "--no-report",
            "--max-concurrency", "3", "--timeout", "120", "--grace", "7", "--fail-fast"])
    o = box["opts"]
    assert o.max_concurrency == 3 and o.fail_fast is True
    assert o.job_timeout_s == 120.0 and o.grace_period_s == 7.0


def test_run_timeout_nonpositive_maps_to_none(tmp_path, monkeypatch, capsys):
    # --timeout <=0 → job_timeout_s=None（不超时），是有逻辑的转换，护住它
    box = {}
    monkeypatch.setattr(m, "schedule", _capturing_schedule(Status.PASSED, box))
    m.main(["run", str(_write_feature(tmp_path)), "--no-report", "--timeout", "0"])
    assert box["opts"].job_timeout_s is None


# ---- #8 畸形 feature → 友好诊断、退 2、无 traceback ----
def test_malformed_feature_friendly_diagnostic(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())  # 不该走到 schedule
    bad = tmp_path / "bad.feature"
    bad.write_text("this is not gherkin\n  garbage\n", encoding="utf-8")
    for cmd in ("plan", "run"):
        rc = m.main([cmd, str(bad), "--no-report"] if cmd == "run" else [cmd, str(bad)])
        assert rc == 2, f"{cmd} 畸形 feature 应退 2"
        err = capsys.readouterr().err
        assert "语法错误" in err and "Traceback" not in err  # 友好诊断、非 Python traceback
