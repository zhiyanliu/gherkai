"""cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不产生 AWS 费用），

验证落盘三层产物 + --json 输出形状（单一可解析 JSON 文档，回归护栏 ADR 0016/0027）。
"""
from __future__ import annotations

import json
from pathlib import Path

from gherkai_core.model import JobResult, RunResult, Status

from gherkai_cli import __main__ as m
from gherkai_runtime import compose


def _fake_schedule_factory():
    """造一个不起 worker 的假 schedule：发事件给 sink（进度）+ on_event（persistence 刷 RUNNING）+ 每 job
    fire on_job_complete（验证实时落库路径）+ 把 run_meta 合成 RunResult。"""
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
        return RunResult(run_meta=run_meta, status=Status.PASSED, jobs=results)
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
    assert "报告:" not in out and "报告:" in err  # 落点提示 → stderr


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
    assert "运行结果" in out and "总状态" in out
    # 进度/event/落点提示在 stderr，不污染 stdout。event 行前缀 `[core <scope>:event]`，与 worker 透传行
    # `[worker <scope>:err]` 同骨架 `[producer scope:kind]`（并发跑批时区分来源、scope 同列可竖扫）。
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


def test_run_rejects_max_concurrency_below_one(tmp_path, monkeypatch, capsys):
    # --max-concurrency < 1 在入口被拒（退 2）：<=0 会让 plan_next 永不提议起 job → run 卡死在 pending
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
    # 同上，submit 侧（坏值会随 definition 到达推进器 → 三路推进器全空转）。零副作用 = 没 fork per-run 进程、
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
    assert forked == []              # per-run 进程一次没 fork
    assert not report_dir.exists()   # definition 也没落库


# ---- plan 预检（dry-run）：纯本地、不连 AWS、零费用 ----

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
    assert "plan（预检，未执行）" in out
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
    def fake(run_meta, engines, sink, opts=None, on_job_complete=None, on_event=None):
        opts_box["opts"] = opts
        opts_box["run_meta"] = run_meta
        results = [JobResult(job=j, status=status) for j in run_meta.jobs]
        if on_job_complete is not None:
            for jr in results:
                on_job_complete(jr)
        return RunResult(run_meta=run_meta, status=status, jobs=results)
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
    # grace 用合法值（≥ Nova 下限）；默认引擎 novaact → min_grace=ACT_TIMEOUT_S+margin。
    good_grace = compose.NOVA_ACT_TIMEOUT_S + compose.NOVA_GRACE_MARGIN_S + 10
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
    assert o.min_grace_s == float(compose.NOVA_ACT_TIMEOUT_S + compose.NOVA_GRACE_MARGIN_S)


def test_run_grace_too_small_rejected(tmp_path, monkeypatch, capsys):
    # 显式给过小 grace（< Nova 下限）→ 入口退 2「没开跑就被拒」（ADR 0024 grace 硬约束、对齐 votes 校验惯例）。
    box = {}
    monkeypatch.setattr(m, "schedule", _capturing_schedule(Status.PASSED, box))
    rc = m.main(["run", str(_write_feature(tmp_path)), "--no-report", "--grace", "5"])
    assert rc == 2
    assert "opts" not in box  # schedule 根本没被调（跑前就拒了）
    assert "--grace=5.0" in capsys.readouterr().err  # 诊断打到 stderr


def test_run_grace_nan_inf_rejected(tmp_path, monkeypatch, capsys):
    """--grace inf/nan 同拒（退 2）：inf 会让 SIGKILL 兜底永不触发、软停失效即挂死（ADR 0024/0026）；
    与 --tunnel-ttl、@timeout 的「有限正数」判据同形。"""
    for bad in ("inf", "nan"):
        box = {}
        monkeypatch.setattr(m, "schedule", _capturing_schedule(Status.PASSED, box))
        rc = m.main(["run", str(_write_feature(tmp_path)), "--no-report", "--grace", bad])
        assert rc == 2, bad
        assert "opts" not in box
        assert "有限正数" in capsys.readouterr().err


def test_run_grace_sentinel_derives_from_engine(tmp_path, monkeypatch, capsys):
    # 不给 --grace（哨兵默认 None）→ 按本 run 引擎推导：novaact → grace = min_grace = act_timeout+margin。
    box = {}
    monkeypatch.setattr(m, "schedule", _capturing_schedule(Status.PASSED, box))
    m.main(["run", str(_write_feature(tmp_path)), "--no-report"])
    o = box["opts"]
    expected = float(compose.NOVA_ACT_TIMEOUT_S + compose.NOVA_GRACE_MARGIN_S)
    assert o.grace_period_s == expected  # 默认从引擎推导，不再是旧的硬编码 10
    assert o.min_grace_s == expected


def test_run_timeout_nonpositive_maps_to_none(tmp_path, monkeypatch, capsys):
    # --default-job-timeout <=0 → Job.timeout_s=None（不超时），是有逻辑的转换，护住它
    box = {}
    monkeypatch.setattr(m, "schedule", _capturing_schedule(Status.PASSED, box))
    m.main(["run", str(_write_feature(tmp_path)), "--no-report", "--default-job-timeout", "0"])
    assert all(j.timeout_s is None for j in box["run_meta"].jobs)


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


# ---- 第四刀：实时写 commit-point 写序（ADR 0030）----
# 用 fake store 记录调用序（共享一个有序 log），注入真 RunPersistence 编排——测真实写序、非 mock 行为。
# 注入点 = patch compose.build_local_stores（ADR 0016：local 装配下沉 compose 后的注入锚，取代旧的 m.Local*）。
def _recording_build_local_stores(calls: list):
    """返回一个替换 compose.build_local_stores 的 fake：产出三个记录调用的 fake store + make_artifacts。"""
    class FakeRunStore:
        def preflight(self): calls.append(("run", "preflight", None))
        def create_run(self, meta, initial_state): calls.append(("run", "create_run", None))
        def update_job_state(self, run_id, js): calls.append(("run", "update_job_state", js.scope_id))
        def finalize_run(self, run_id, status, ended_at): calls.append(("run", "finalize_run", None))

    class FakeResultStore:
        def preflight(self): calls.append(("result", "preflight", None))
        def save_job_result(self, run_id, jr): calls.append(("result", "save_job_result", jr.scope_id))

    class FakeReportStore:
        def preflight(self): calls.append(("report", "preflight", None))
        def write(self, run_id, result, *, created_at=""):
            calls.append(("report", "write", None))
            return f"file:///fake/{run_id}/index.html"

    def fake_build(*, report_dir):
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
    # 注入 fake（patch compose.build_local_stores：cli 调它拿三 store → 喂给真 RunPersistence）
    monkeypatch.setattr(m.compose, "build_local_stores", _recording_build_local_stores(calls))
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
    # ② commit point：finalize_run 在所有 save_job_result 之后（数据面先、控制面摘要后）
    last_save = max(i for i, (s, mth) in enumerate(methods) if mth == "save_job_result")
    finalize_idx = methods.index(("run", "finalize_run"))
    assert finalize_idx > last_save
    # ③ 每 job 一次 save_job_result（两个 scope=两次），且与终态刷 update_job_state 配对
    saves = [scope for (s, mth, scope) in calls if mth == "save_job_result"]
    assert sorted(saves) == ["a", "b"]
    # ④ 每个 save_job_result 紧跟其 update_job_state（commit-point：数据面先于该 job 的控制面态）
    for scope in ("a", "b"):
        si = next(i for i, (s, mth, sc) in enumerate(calls) if mth == "save_job_result" and sc == scope)
        ui = next(i for i, (s, mth, sc) in enumerate(calls) if mth == "update_job_state" and sc == scope and i > si)
        assert ui > si
    # ⑤ ReportStore.write 最后（派生、永远最后）
    assert methods[-1] == ("report", "write")


def test_no_report_skips_persistence_entirely(tmp_path, monkeypatch, capsys):
    # --no-report：persistence=None，store 装配一次都不该被调（裸跑、零落盘逃生舱）
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
        return RunResult(run_meta=run_meta, status=Status.PASSED, jobs=results)

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
    # fail-fast 护栏（ADR 0027 产物归位）：钉住 __main__ 把两引擎产物落点算成 <report_dir>/<run_id>/<engine-dir>
    # 并传给 build_engines。防止将来改坏 __main__ 那几行接线（否则产物落错地方，只有真跑 AWS 才发现）。
    box = {}
    real_build = m.compose.build_engines

    def spy_build(**kwargs):
        box["kwargs"] = kwargs
        return real_build()  # 不带落点：拿真 engines（cmd 正确），落点断言看 box

    monkeypatch.setattr(m.compose, "build_engines", spy_build)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    report_dir = tmp_path / "reports"
    rc = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(report_dir)])
    assert rc == 0

    nova = box["kwargs"]["nova_logs_dir"]
    mid = box["kwargs"]["midscene_run_dir"]
    # 落点 = <report_dir 绝对化>/<run_id>/<engine 子目录>，两引擎对称、run_id 一致
    assert nova is not None and mid is not None
    assert str(nova).endswith("/nova-trajectories") and str(mid).endswith("/midscene-run")
    assert Path(nova).parent == Path(mid).parent          # 同一 <report_dir>/<run_id> 下
    assert Path(mid).parent.parent == report_dir.resolve()  # 绝对化的 report_dir（避 worker cwd 歧义）


def test_no_report_disables_artifacts_instead_of_tempdir(tmp_path, monkeypatch):
    """`--no-report` = 真不生成（ADR 0037 决策 3）：不注入任何落点、并以 no_artifacts 告知 worker 不产生/不上报
    引擎原生产物——而不是「落系统临时目录」（曾如此、被否）。"""
    box = {}
    real_build = m.compose.build_engines

    def spy_build(**kwargs):
        box.update(kwargs)
        return real_build()

    monkeypatch.setattr(m.compose, "build_engines", spy_build)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    m.main(["run", str(_write_feature(tmp_path)), "--no-report"])
    assert box["nova_logs_dir"] is None and box["midscene_run_dir"] is None
    assert box["no_artifacts"] is True


def test_report_run_passes_absolute_artifact_dirs_and_no_flag(tmp_path, monkeypatch):
    """对照：默认归集档落 <report_dir>/<run_id>/ 下的绝对路径、no_artifacts=False。"""
    box = {}
    real_build = m.compose.build_engines

    def spy_build(**kwargs):
        box.update(kwargs)
        return real_build()

    monkeypatch.setattr(m.compose, "build_engines", spy_build)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(tmp_path / "reports")])
    nova, mid = Path(box["nova_logs_dir"]), Path(box["midscene_run_dir"])
    assert nova.is_absolute() and nova.parent == mid.parent and nova.parent.parent == (tmp_path / "reports").resolve()
    assert box["no_artifacts"] is False


# ---- _render_status：local/cloud 共享的渲染+提示+退出码（ADR 0034，两路一致）----
def _mk_state(status):
    from gherkai_core.model import RunState, JobState
    return RunState(run_id="r", status=status,
                    jobs={"a": JobState("a", status)}, high_water_mark=0)


def _args(wait=False, json_=False):
    from types import SimpleNamespace
    return SimpleNamespace(wait=wait, json=json_, run_id="r")


_LOCS = {"report_index": "file:///tmp/x/r/index.html", "run_meta": "file:///tmp/x/r/run_meta.json",
         "run_state": "file:///tmp/x/r/run_state.json", "jobs_dir": "file:///tmp/x/r/jobs"}


def test_render_status_pending_hints_wait(capsys):
    """pending + 非 --wait + 非 json → 打 --wait 接力提示（提示走 stderr）。退出码 0（查询本身成功）。"""
    rc = m._render_status(_mk_state(Status.PENDING), _args(), wait_hint="gherkai status r --wait", locations=_LOCS)
    err = capsys.readouterr().err
    assert "仍 pending" in err and "gherkai status r --wait" in err
    assert rc == 0


def test_render_status_running_no_hint(capsys):
    """running → 不提示（在跑、正常）。退出码 0。"""
    rc = m._render_status(_mk_state(Status.RUNNING), _args(), wait_hint="x", locations=_LOCS)
    assert "仍 pending" not in capsys.readouterr().err
    assert rc == 0


def test_render_status_terminal_no_hint_and_exitcode(capsys):
    """终态：passed→0、其余终态→1（含派生终态 skipped/aborted），均不提示。"""
    assert m._render_status(_mk_state(Status.PASSED), _args(), wait_hint="x", locations=_LOCS) == 0
    assert m._render_status(_mk_state(Status.FAILED), _args(), wait_hint="x", locations=_LOCS) == 1
    assert m._render_status(_mk_state(Status.ERROR), _args(), wait_hint="x", locations=_LOCS) == 1
    assert m._render_status(_mk_state(Status.SKIPPED), _args(), wait_hint="x", locations=_LOCS) == 1
    assert m._render_status(_mk_state(Status.ABORTED), _args(), wait_hint="x", locations=_LOCS) == 1
    assert "仍 pending" not in capsys.readouterr().err


def test_terminal_status_consumers_use_core_single_source():
    """终态真源不漂移（ADR 0031 决定一·补末条）：三处消费方全引 `gherkai_core.model.TERMINAL_STATUSES`、不各写白名单。

    跨 core/cli/gherkai 三栈的结构性护栏（cli 是唯一同时看得见三者的层）——曾有两份逐字副本，
    新增终态漏改哪份、那份就永远判不到终态（`status --wait` 无限轮询 / 隧道守护只能等满 TTL 才拆）。
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


def test_render_status_wait_pending_no_hint(capsys):
    """--wait 下即使 pending 也不打提示（--wait 本身在接力、提示多余）。"""
    m._render_status(_mk_state(Status.PENDING), _args(wait=True), wait_hint="x", locations=_LOCS)
    assert "仍 pending" not in capsys.readouterr().err


def test_render_status_json_no_hint(capsys):
    """--json（机读）：pending 也不打人读提示，且 stdout 是可解析 JSON。"""
    m._render_status(_mk_state(Status.PENDING), _args(json_=True), wait_hint="x", locations=_LOCS)
    cap = capsys.readouterr()
    assert "仍 pending" not in cap.err
    json.loads(cap.out)  # stdout 是纯 JSON


# ---- list-deterministic（ADR 0036）：按引擎查询确定性能力清单 ----

def test_list_deterministic_text_and_json(monkeypatch, capsys):
    entries = [{"pattern": 'p "(?P<x>[^"]+)"', "description": "断言某事", "example": 'Then p "v"'}]
    calls = []
    monkeypatch.setattr(m.compose, "query_deterministic",
                        lambda engine, steps_dir=None: calls.append(engine) or entries)
    assert m.main(["list-deterministic", "--engine", "midscene"]) == 0
    out = capsys.readouterr().out
    assert "断言某事" in out and 'Then p "v"' in out and calls == ["midscene"]
    assert m.main(["list-deterministic", "--json"]) == 0  # 默认 novaact（对齐 run 缺省）
    doc = json.loads(capsys.readouterr().out)
    assert doc["engine"] == "novaact" and doc["deterministic_steps"] == entries


def test_list_deterministic_worker_failure_exits_2(monkeypatch, capsys):
    def boom(engine, steps_dir=None):
        raise RuntimeError("worker 自述失败（exit 1）：...")

    monkeypatch.setattr(m.compose, "query_deterministic", boom)
    assert m.main(["list-deterministic"]) == 2
    assert "自述失败" in capsys.readouterr().err


# ---- plan 派发标注（ADR 0036 决策 4）----

def _det_feature(tmp_path):
    f = tmp_path / "det.feature"
    f.write_text('Feature: d\n  Scenario: s\n    When "做点啥"\n    Then 页面地址匹配 "x"\n', encoding="utf-8")
    return f


def test_plan_annotates_deterministic_hits(tmp_path, monkeypatch, capsys):
    """plan 标注：worker 自述命中 → 行尾「← 确定性:」；AI step 不标（噪声控制）。"""
    def fake_match(engine, texts, steps_dir=None):
        return [({"pattern": "p", "description": "URL 断言"} if "页面地址" in t else None) for t in texts]

    monkeypatch.setattr(m.compose, "match_deterministic", fake_match)
    assert m.main(["plan", str(_det_feature(tmp_path))]) == 0
    out = capsys.readouterr().out
    assert "← 确定性: URL 断言" in out
    assert out.count("← 确定性") == 1  # AI step 不标


def test_plan_conflict_annotated_and_warned(tmp_path, monkeypatch, capsys):
    """冲突预检（真跑将 error 的注册表配置错）：行内 ⚠ 标注 + stderr 警告；plan 本体仍 0。"""
    monkeypatch.setattr(m.compose, "match_deterministic",
                        lambda engine, texts, steps_dir=None: [{"conflict": ["p1", "p2"]} for _ in texts])
    assert m.main(["plan", str(_det_feature(tmp_path))]) == 0
    captured = capsys.readouterr()
    assert "⚠ 命中多条确定性模式" in captured.out
    assert "收紧注册表模式" in captured.err


def test_plan_annotation_degrades_gracefully(tmp_path, monkeypatch, capsys):
    """标注 best-effort：引擎环境未装/查询失败 → 无标注 + stderr 警告，plan 核心输出不受影响。"""
    def boom(engine, texts, steps_dir=None):
        raise RuntimeError("worker 起不来")

    monkeypatch.setattr(m.compose, "match_deterministic", boom)
    assert m.main(["plan", str(_det_feature(tmp_path))]) == 0
    captured = capsys.readouterr()
    assert "页面地址匹配" in captured.out and "← 确定性" not in captured.out
    assert "标注降级" in captured.err


def test_plan_json_carries_deterministic_field(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(m.compose, "match_deterministic",
                        lambda engine, texts, steps_dir=None: [({"pattern": "p", "description": "d"}
                                                                if "页面地址" in t else None) for t in texts])
    assert m.main(["plan", str(_det_feature(tmp_path)), "--json"]) == 0
    doc = json.loads(capsys.readouterr().out)
    steps = doc["jobs"][0]["scenarios"][0]["steps"]
    assert steps[0]["deterministic"] is None
    assert steps[1]["deterministic"] == {"pattern": "p", "description": "d"}


# ---- 引擎名预检（plan 层拦配置错，防延迟到 run 起 job 才炸）----

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

def test_submit_local_writes_max_concurrency_into_definition(tmp_path, monkeypatch):
    """submit 把 --max-concurrency 落进 definition（推进器读 meta，不靠 flag 通道）。

    fork 出的 per-run 进程仍收 flag（meta 缺值时的回落），但真源是落盘的 meta——推进器与提交进程可能分离
    （cloud 档在 Lambda、local 接力者是另一个 CLI 调用），flag 到不了它们。
    """
    import subprocess

    forked = []

    class _FakeProc:
        pid = 1

    monkeypatch.setattr(subprocess, "Popen", lambda cmd, **kw: forked.append(cmd) or _FakeProc())
    reports = tmp_path / "reports"
    assert m.main(["submit", str(_write_feature(tmp_path)), "--report-dir", str(reports),
                   "--max-concurrency", "3"]) == 0
    run_dirs = [d for d in reports.iterdir() if d.is_dir()]
    assert len(run_dirs) == 1
    meta = json.loads((run_dirs[0] / "run_meta.json").read_text(encoding="utf-8"))
    assert meta["max_concurrency"] == 3
    assert ["--max-concurrency", "3"] == forked[0][-2:]  # per-run 仍带 flag（回落值）


def test_version_flag_prints_dist_version(capsys):
    """--version 打印「gherkai <发行版本>」并退 0——版本真源是包元数据（git tag → uv-dynamic-versioning），
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
    """run 的分叉：定位链 miss → 打安装指引 + 退 2，**且在 spawn/落库之前**——不进 job 级 engine_error
    （「运行时没装」属「没开跑就被拒」层；否则用户拿到一批 error 的 job 结果而非一句能照做的指引）。"""
    monkeypatch.setattr(m.compose, "resolve_worker_cmd", lambda engine, **kw: (_ for _ in ()).throw(_miss(engine)))
    started = []
    monkeypatch.setattr(m, "schedule", lambda *a, **k: started.append(1))
    reports = tmp_path / "reports"
    rc = m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(reports)])
    assert rc == 2
    assert "uv tool install" in capsys.readouterr().err
    assert started == []            # 没开跑
    assert not reports.exists()     # 也没落库（拒在 persistence.begin 之前，不留半成品 run）


def test_run_unused_engine_miss_does_not_block(tmp_path, monkeypatch, capsys):
    """miss 只连坐**用到它**的 run：novaact-only 的 run 在 midscene 未装（dev 常态）下照跑退 0。

    preflight 只查本次 plan 用到的引擎；未用到那条腿即便 miss 也只是「一用即报错」的空腿。
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
    """submit local 同 run（per-run 进程在本机 spawn worker）：提交前退 2、不 fork、不落库——否则「提交成功」
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
    # list-deterministic 的分叉：退 2、消息带安装指引（自述查不了就是查不了，无降级余地）
    def boom(engine, steps_dir=None):
        raise _miss(engine)

    monkeypatch.setattr(m.compose, "query_deterministic", boom)
    assert m.main(["list-deterministic"]) == 2
    assert "uv tool install" in capsys.readouterr().err


def test_plan_degrades_when_worker_runtime_missing(tmp_path, monkeypatch, capsys):
    """plan 的分叉与 run/submit **相反**（ADR 0037 决策 3 明示 + ADR 0036 决策 4）：保持 best-effort 降级——
    只丢该引擎的派发标注 + stderr 警告，plan 本体照出、退 0（feature 作者没装引擎运行时也该能预检写法）。"""
    def boom(engine, texts, steps_dir=None):
        raise _miss("midscene")

    monkeypatch.setattr(m.compose, "match_deterministic", boom)
    assert m.main(["plan", str(_det_feature(tmp_path))]) == 0
    cap = capsys.readouterr()
    assert "页面地址匹配" in cap.out and "← 确定性" not in cap.out
    assert "标注降级" in cap.err


# ---- steps/ 定制面（ADR 0037 决策 4）：解析在组合根、随 definition 持久化、worker 只认 env ----

def _spy_build_engines(monkeypatch):
    """记录 build_engines 收到的 kwargs（仍调真身，保 cmd/env 接线真实）。"""
    box = {}
    real = m.compose.build_engines

    def spy(**kwargs):
        box.update(kwargs)
        return real(**kwargs)

    monkeypatch.setattr(m.compose, "build_engines", spy)
    return box


def _spy_run_meta(monkeypatch):
    """记录 definition 构造入参（RunMeta 落库前的真值，cloud 档不落本地文件也验得到）。"""
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

    绝对化：worker 是 cwd 与 CLI 不同的子进程；随 definition 走：本机后台推进/接力宿主的 CWD 与提交进程
    不同（ADR 0034），只有读回同一个值三宿主才用同一套确定性 step、判定才可复现。
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

    None 时 definition 省该键（omit-when-None）——worker 只有内建脚手架注册。
    """
    box = _spy_build_engines(monkeypatch)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    monkeypatch.delenv("GHERKAI_STEPS_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    reports = tmp_path / "r1"
    assert m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(reports), "--quiet"]) == 0
    assert box["steps_dir"] is None
    meta = json.loads(next(reports.iterdir()).joinpath("run_meta.json").read_text(encoding="utf-8"))
    assert "steps_dir" not in meta
    (tmp_path / "steps").mkdir()  # 同一 CWD 下建出约定目录 → 下一次 run 自动用上
    assert m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(tmp_path / "r2"), "--quiet"]) == 0
    assert box["steps_dir"] == str((tmp_path / "steps").resolve())


def test_steps_dir_explicit_but_missing_exits_2(tmp_path, monkeypatch, capsys):
    """显式给的（flag/env）不是目录 → 退 2，**不静默忽略**：忽略等于把该目录里的确定性 step 悄悄换成
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


def test_submit_local_persists_steps_dir_into_definition(tmp_path, monkeypatch):
    """submit 侧同 run：解析一次写进 definition——per-run 进程/接力者从 definition 读回（**不**收 flag，
    也不重解析 `./steps`），三宿主才一致（ADR 0037 决策 4）。"""
    import subprocess

    class _FakeProc:
        pid = 1

    forked = []
    monkeypatch.setattr(subprocess, "Popen", lambda cmd, **kw: forked.append(cmd) or _FakeProc())
    # 提交侧预检会以自述入口探 worker（ADR 0037 决策 4）；本测只验持久化通道，把探测桩掉（上面的假 Popen 会让
    # subprocess.run 拿到假对象）。
    monkeypatch.setattr(m.compose, "query_deterministic", lambda engine, *, steps_dir=None, timeout_s=60.0: [])
    steps = tmp_path / "steps"
    steps.mkdir()
    monkeypatch.delenv("GHERKAI_STEPS_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    reports = tmp_path / "reports"
    assert m.main(["submit", str(_write_feature(tmp_path)), "--report-dir", str(reports)]) == 0
    meta = json.loads(next(reports.iterdir()).joinpath("run_meta.json").read_text(encoding="utf-8"))
    assert meta["steps_dir"] == str(steps.resolve())
    assert "--steps-dir" not in forked[0]  # per-run 不收 flag：值只经 definition 传（单一通道）


def test_plan_and_list_deterministic_pass_steps_dir_to_worker(tmp_path, monkeypatch, capsys):
    """三个自述入口同样加载 steps 目录（ADR 0037 决策 4）→ plan 标注与 list-deterministic 清单反映定制 step。"""
    steps = tmp_path / "steps"
    steps.mkdir()
    monkeypatch.delenv("GHERKAI_STEPS_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    seen = {}
    monkeypatch.setattr(m.compose, "match_deterministic",
                        lambda engine, texts, steps_dir=None: seen.update(match=steps_dir) or [None] * len(texts))
    monkeypatch.setattr(m.compose, "query_deterministic",
                        lambda engine, steps_dir=None: seen.update(query=steps_dir) or [])
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
    """steps 文件加载失败（worker 自述非零退出）→ plan 退 2、不降级成「无标注」（ADR 0037 决策 4 提交侧前置）。"""
    feat = tmp_path / "t.feature"
    feat.write_text('Feature: t\n  Scenario: s\n    When "做点啥"\n', encoding="utf-8")
    steps = _steps_dir_with_file(tmp_path)

    def boom(engine, texts, *, steps_dir=None, timeout_s=60.0):
        raise compose.WorkerSelfDescribeError(engine, 2, "demo.py：SyntaxError", "确定性命中查询")

    monkeypatch.setattr(compose, "match_deterministic", boom)
    rc = m.main(["plan", str(feat), "--steps-dir", str(steps)])
    assert rc == 2
    assert "steps 加载失败" in capsys.readouterr().err


def test_plan_degrades_when_worker_missing(tmp_path, monkeypatch, capsys):
    """对照：定位链 miss（运行时没装）plan 仍降级退 0（ADR 0036 决策 4 / 0037 决策 3 的分叉保留）。"""
    feat = tmp_path / "t.feature"
    feat.write_text('Feature: t\n  Scenario: s\n    When "做点啥"\n', encoding="utf-8")

    def missing(engine, texts, *, steps_dir=None, timeout_s=60.0):
        raise compose.WorkerNotFoundError(engine, "装法：…")

    monkeypatch.setattr(compose, "match_deterministic", missing)
    rc = m.main(["plan", str(feat)])
    assert rc == 0
    assert "标注降级" in capsys.readouterr().err


def test_run_and_submit_exit_2_before_spawn_when_user_steps_fail(tmp_path, monkeypatch, capsys):
    """run / submit：steps 目录已解析时先以自述入口探一次，worker 非零退出 → 起任何 job 之前退 2（不进 job 级 error）。"""
    feat = tmp_path / "t.feature"
    feat.write_text('Feature: t\n  Scenario: s\n    When "做点啥"\n', encoding="utf-8")
    steps = _steps_dir_with_file(tmp_path)
    monkeypatch.setattr(compose, "resolve_worker_cmd", _fake_worker_cmd)

    def boom(engine, *, steps_dir=None, timeout_s=60.0):
        raise compose.WorkerSelfDescribeError(engine, 2, "demo.py：SyntaxError", "确定性能力查询")

    monkeypatch.setattr(compose, "query_deterministic", boom)
    spawned = {"n": 0}
    monkeypatch.setattr(m, "schedule", lambda *a, **k: spawned.__setitem__("n", spawned["n"] + 1))
    assert m.main(["run", str(feat), "--no-report", "--steps-dir", str(steps)]) == 2
    assert spawned["n"] == 0
    assert m.main(["submit", str(feat), "--report-dir", str(tmp_path / "r"), "--steps-dir", str(steps)]) == 2
    assert "steps 加载失败" in capsys.readouterr().err
    assert not (tmp_path / "r").exists() or not any((tmp_path / "r").iterdir())  # 没落任何 run 记录


def test_plan_rejects_a_directory_as_feature(tmp_path, capsys):
    """给了目录 / 读不了的路径 → 退 2「读 feature 失败」，不是 IsADirectoryError traceback（退码语义 ADR 0021）。
    读 feature 的失败面不止 FileNotFoundError：目录、权限、非 UTF-8 都属输入问题，同档处置。"""
    rc = m.main(["plan", str(tmp_path)])
    assert rc == 2
    assert "读 feature 失败" in capsys.readouterr().err


def test_render_status_pending_run_with_claimed_job_does_not_hint(capsys):
    """run 级仍 pending 但已有 job 被 claim（running）→ 推进已开始，不提示「可能未启动」。这是 detached 的正常窗口：
    claim 只动 job、run 级要等下一次投影写；Fargate 拉起期间恒如此（真跑 submit 后连查三次撞见误报）。"""
    from gherkai_core.model import JobState, RunState
    state = RunState(run_id="r", status=Status.PENDING,
                     jobs={"a": JobState("a", Status.RUNNING), "b": JobState("b", Status.PENDING)}, high_water_mark=0)
    assert m._render_status(state, _args(), wait_hint="x", locations=_LOCS) == 0
    assert "仍 pending" not in capsys.readouterr().err


def test_render_status_terminal_prints_artifact_locations(capsys):
    """终态时对标 `run` 结束的三行：报告 / 运行元信息 / 判定明细（S3 或本地路径可直接复制）；未终态不打（产物还没落）。"""
    m._render_status(_mk_state(Status.PASSED), _args(), wait_hint="x", locations=_LOCS)
    err = capsys.readouterr().err
    assert "报告: file:///tmp/x/r/index.html" in err and "判定明细: file:///tmp/x/r/jobs" in err
    assert "运行元信息: file:///tmp/x/r/run_meta.json、file:///tmp/x/r/run_state.json" in err
    m._render_status(_mk_state(Status.RUNNING), _args(), wait_hint="x", locations=_LOCS)
    assert "报告:" not in capsys.readouterr().err
    # --json 形状不变：stdout 纯 RunState JSON，stderr 不掺位置行
    m._render_status(_mk_state(Status.PASSED), _args(json_=True), wait_hint="x", locations=_LOCS)
    cap = capsys.readouterr()
    json.loads(cap.out)
    assert "报告:" not in cap.err


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
    """一个 --tags 值内逗号 = 任一命中；重复 --tags = 都要命中；@ 可省。"""
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
    assert m.main(["plan", str(feat), "--json", "--scenario", "3", "--scenario", ":9"]) == 0  # 行 3 = 登录成功，行 9 = 搜索
    assert _plan_names(capsys) == ["搜索", "登录成功"]
    assert m.main(["plan", str(feat), "--json", "--scenario", f"{feat}:6"]) == 0
    assert _plan_names(capsys) == ["结账"]
    assert m.main(["plan", str(feat), "--json", "--tags", "slow", "--scenario", "搜"]) == 0
    assert _plan_names(capsys) == ["搜索"]


def test_plan_empty_selection_exits_2_and_lists_candidates(tmp_path, capsys):
    """筛空 → 退 2 并列全部候选（id  标题），别静默跑空批。"""
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


def test_list_engines_json_shape(monkeypatch, capsys):
    _fake_locator(monkeypatch)
    assert m.main(["list-engines", "--json"]) == 0
    rows = json.loads(capsys.readouterr().out)
    by = {r["engine"]: r for r in rows}
    assert set(by) == {"midscene", "novaact"}
    assert by["novaact"]["available"] is True and by["novaact"]["cmd"][-1] == "gherkai_worker_novaact" and by["novaact"]["hint"] is None
    assert by["midscene"]["available"] is False and by["midscene"]["cmd"] is None and "未找到" in by["midscene"]["hint"]


def test_doctor_local_json_checks_and_exit_codes(tmp_path, monkeypatch, capsys):
    """local 自检：引擎（一缺一在→any ok）、steps 目录加载、云端项标未查、provider 未装标可选；全 required ok → 0；
    steps 加载失败 → 2（agent 据退出码分流）。"""
    _fake_locator(monkeypatch)
    _no_provider(monkeypatch)
    steps = tmp_path / "steps"; steps.mkdir()
    monkeypatch.setattr(m.compose, "query_deterministic", lambda engine, *, steps_dir=None, timeout_s=60.0: [{"pattern": "a"}, {"pattern": "b"}])
    assert m.main(["doctor", "--json", "--steps-dir", str(steps)]) == 0
    doc = json.loads(capsys.readouterr().out)
    by = {(c["section"], c["name"]): c for c in doc["checks"]}
    assert doc["ok"] is True
    assert by[("engines", "novaact")]["ok"] and not by[("engines", "midscene")]["ok"] and by[("engines", "midscene")]["required"] is False
    assert by[("engines", "any")]["ok"] and by[("engines", "any")]["required"] is True
    assert by[("steps", "load.novaact")]["ok"] and "2 条" in by[("steps", "load.novaact")]["detail"]
    assert ("steps", "load.midscene") not in by  # 没装的引擎不探自述
    assert by[("aws", "identity")]["required"] is False and "未查" in by[("aws", "identity")]["detail"]
    assert by[("provider", "deploy-aws")]["ok"] and "只有部署方需要" in by[("provider", "deploy-aws")]["detail"]

    def boom(engine, *, steps_dir=None, timeout_s=60.0):
        raise RuntimeError("worker 自述退 1：steps/login.py 第 3 行 SyntaxError")  # doctor 对任何加载异常都原样转述
    monkeypatch.setattr(m.compose, "query_deterministic", boom)
    assert m.main(["doctor", "--json", "--steps-dir", str(steps)]) == 2
    doc = json.loads(capsys.readouterr().out)
    bad = next(c for c in doc["checks"] if c["name"] == "load.novaact")
    assert doc["ok"] is False and bad["ok"] is False and "SyntaxError" in bad["detail"]


def test_doctor_no_engine_at_all_fails_locally_but_not_for_cloud(monkeypatch, capsys):
    _fake_locator(monkeypatch, available=())
    _no_provider(monkeypatch)
    assert m.main(["doctor", "--json"]) == 2
    assert json.loads(capsys.readouterr().out)["ok"] is False
    # cloud 档不需要本机 worker：engines.any 降为可选，其余云端项被 fake 成 ok
    monkeypatch.setattr(m.compose, "probe_aws_identity", lambda *, region, profile: {"account": "x", "arn": "arn:aws:sts::x:assumed-role/r", "region": region})
    monkeypatch.setattr(m.compose, "check_backend_skew", lambda **kw: (compose.SKEW_OK, "", "1.4.1"))
    monkeypatch.setattr(m.compose, "preflight_cloud_resources", lambda **kw: None)
    monkeypatch.setattr(m.compose, "read_worker_default", lambda **kw: "base")
    monkeypatch.setattr(m.compose, "resolve_worker_variant", lambda **kw: {
        e: compose.WorkerResolution(engine=e, variant=kw["variant"], revision_arn=f"arn:{e}:7", digest="sha256:0") for e in kw["engines"]})
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
    assert m.main(["doctor", "--prefix", "vfy-", "--region", "us-east-1", "--json"]) == 2  # 给了 --prefix 即查云端
    doc = json.loads(capsys.readouterr().out)
    by = {(c["section"], c["name"]): c for c in doc["checks"]}
    assert not by[("backend", "version")]["ok"] and "skew" in by[("backend", "version")]["detail"]
    assert not by[("backend", "resources")]["ok"] and "vfy-events" in by[("backend", "resources")]["detail"]
    assert not by[("backend", "worker.novaact")]["ok"] and not by[("backend", "worker.midscene")]["ok"]
    assert not by[("backend", "worker.any")]["ok"] and by[("backend", "worker.any")]["required"] is True  # 两引擎都解析不到才算必修失败


def test_doctor_provider_section_comes_from_provider_doctor(monkeypatch, capsys):
    """装了 deploy-aws extra → 经 provider 接缝调它的 doctor(args)，required 项失败让整体退 2。"""
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
    # 人读形态：✗ 标必修、- 标可选缺失
    assert m.main(["doctor"]) == 2
    out = capsys.readouterr().out
    assert "✗ provider.node" in out and "- provider.container-engine" in out and "自检有失败项" in out
    assert "部署工具链有缺口" in out  # provider 段缺项单独点出，别混在通用的可选缺失里


def test_doctor_cloud_credential_failure_is_required_and_exits_2(monkeypatch, capsys):
    """凭证探针抛 → aws.identity 必修失败、backend 标未查（可选）、退 2；不去碰后端。"""
    _fake_locator(monkeypatch); _no_provider(monkeypatch)
    monkeypatch.setattr(m.compose, "probe_aws_identity", lambda **kw: (_ for _ in ()).throw(RuntimeError("Unable to locate credentials")))
    touched = []
    monkeypatch.setattr(m.compose, "check_backend_skew", lambda **kw: touched.append("skew") or (compose.SKEW_OK, "", "1"))
    assert m.main(["doctor", "--prefix", "vfy-", "--region", "us-east-1", "--json"]) == 2
    by = {(c["section"], c["name"]): c for c in json.loads(capsys.readouterr().out)["checks"]}
    assert not by[("aws", "identity")]["ok"] and by[("aws", "identity")]["required"] is True
    assert "Unable to locate credentials" in by[("aws", "identity")]["detail"]
    assert by[("backend", "reachability")]["required"] is False and "未查" in by[("backend", "reachability")]["detail"]
    assert touched == []


def test_doctor_cloud_without_region_fails_region_check_first(monkeypatch, capsys):
    """region 解析不出 → aws.region 必修失败、后端标未查，不会把 NoRegionError 误诊成「prefix 配错」。"""
    _fake_locator(monkeypatch); _no_provider(monkeypatch)
    monkeypatch.setattr(m.compose, "resolve_region", lambda r, p: None)
    monkeypatch.setattr(m.compose, "probe_aws_identity", lambda **kw: (_ for _ in ()).throw(AssertionError("不该被调")))
    assert m.main(["doctor", "--backend", "cloud", "--json"]) == 2
    by = {(c["section"], c["name"]): c for c in json.loads(capsys.readouterr().out)["checks"]}
    assert not by[("aws", "region")]["ok"] and "AWS_REGION" in by[("aws", "region")]["detail"]
    assert ("aws", "identity") not in by and "region" in by[("backend", "reachability")]["detail"]


def test_doctor_cloud_profile_error_at_target_resolution_is_a_credential_failure(monkeypatch, capsys):
    """--profile 打错在 resolve_cloud_target 就炸（读 profile config）→ 与探针失败同一句诊断、退 2，不冒 traceback。"""
    _fake_locator(monkeypatch); _no_provider(monkeypatch)
    monkeypatch.setattr(m.compose, "resolve_cloud_target", lambda **kw: (_ for _ in ()).throw(RuntimeError("The config profile (nope) could not be found")))
    assert m.main(["doctor", "--prefix", "vfy-", "--profile", "nope", "--json"]) == 2
    by = {(c["section"], c["name"]): c for c in json.loads(capsys.readouterr().out)["checks"]}
    assert not by[("aws", "identity")]["ok"] and "凭证/region 不可用" in by[("aws", "identity")]["detail"]


def test_doctor_cloud_missing_default_pointer_is_required_failure(monkeypatch, capsys):
    _fake_locator(monkeypatch); _no_provider(monkeypatch)
    monkeypatch.setattr(m.compose, "probe_aws_identity", lambda **kw: {"account": "x", "arn": "arn", "region": kw["region"]})
    monkeypatch.setattr(m.compose, "check_backend_skew", lambda **kw: (compose.SKEW_OK, "", "1.4.1"))
    monkeypatch.setattr(m.compose, "preflight_cloud_resources", lambda **kw: None)
    monkeypatch.setattr(m.compose, "read_worker_default", lambda **kw: None)
    assert m.main(["doctor", "--prefix", "vfy-", "--region", "us-east-1", "--json"]) == 2
    by = {(c["section"], c["name"]): c for c in json.loads(capsys.readouterr().out)["checks"]}
    assert not by[("backend", "worker.default")]["ok"] and "gherkai deploy" in by[("backend", "worker.default")]["detail"]
    assert ("backend", "worker.any") not in by  # 指针都没有，不再逐引擎


def test_doctor_provider_installed_but_broken_is_required_failure(monkeypatch, capsys):
    """装了 deploy-aws extra 却加载失败（半装/版本不匹配）→ 必修失败：明确装了的东西坏了；靠 entry point 结构判、不靠文案前缀。"""
    _fake_locator(monkeypatch)
    monkeypatch.setattr(m._deploy, "provider_entry_points", lambda: [object()])
    monkeypatch.setattr(m._deploy, "resolve_provider", lambda name=None: (None, "部署 provider 'aws' 加载失败（entry point x）：ImportError"))
    assert m.main(["doctor", "--json"]) == 2
    by = {(c["section"], c["name"]): c for c in json.loads(capsys.readouterr().out)["checks"]}
    assert not by[("provider", "deploy-aws")]["ok"] and by[("provider", "deploy-aws")]["required"] is True
    # 装了多个未指名：不是故障，只是不替用户猜哪个云
    monkeypatch.setattr(m._deploy, "provider_entry_points", lambda: [object(), object()])
    monkeypatch.setattr(m._deploy, "resolve_provider", lambda name=None: (None, "装了多个部署 provider（aws, gcp）：用 --provider <名> 指定其一。"))
    assert m.main(["doctor", "--json"]) == 0


def test_doctor_runs_worker_self_describe_even_without_steps_dir(monkeypatch, capsys):
    """无 steps/ 目录也对可用引擎跑一次自述（验 worker 起得来），但只作可选项：自述失败不改退出码。"""
    _fake_locator(monkeypatch); _no_provider(monkeypatch)
    monkeypatch.chdir(monkeypatch._temp_dir if hasattr(monkeypatch, "_temp_dir") else ".")
    monkeypatch.delenv("GHERKAI_STEPS_DIR", raising=False)
    monkeypatch.setattr(m.compose, "query_deterministic", lambda engine, *, steps_dir=None, timeout_s=60.0: (_ for _ in ()).throw(RuntimeError("worker 起不来")))
    assert m.main(["doctor", "--json"]) == 0
    by = {(c["section"], c["name"]): c for c in json.loads(capsys.readouterr().out)["checks"]}
    assert not by[("steps", "load.novaact")]["ok"] and by[("steps", "load.novaact")]["required"] is False


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
    """--scope = 报告里的 scope_id：named scope 的名字选中整个 scope（两条都跑），未标 scope 的用 <文件>:<行>；
    与 --scenario 同给为且。plan 文本里 named scope 不再重复打 (name=…)。"""
    p = tmp_path / "s.feature"
    p.write_text("Feature: F\n"
                 "  @scope:browse\n  Scenario: 进入\n    When \"a\"\n"
                 "  @scope:browse\n  Scenario: 停留\n    When \"b\"\n"
                 "  Scenario: 独立\n    When \"c\"\n", encoding="utf-8")
    assert m.main(["plan", str(p), "--json", "--scope", "browse"]) == 0
    assert _plan_names(capsys) == ["停留", "进入"]
    assert m.main(["plan", str(p), "--json", "--scope", f"{p}:8"]) == 0   # 未标 scope：scope_id = uri:line
    assert _plan_names(capsys) == ["独立"]
    assert m.main(["plan", str(p), "--json", "--scope", "browse", "--scenario", "停留"]) == 0
    assert _plan_names(capsys) == ["停留"]
    assert m.main(["plan", str(p), "--scope", "browse"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("===== plan") and "job scope='browse' engine=" in out and "(name=" not in out
    assert m.main(["plan", str(p), "--scope", ""]) == 2 and "--scope 的值不能为空" in capsys.readouterr().err


# ---- explain（ADR 0042 决策四）：判定明细 + step 级机读证据的合成视图 ----
# 夹具照 ADR 的文本样例搭（同一份 run 喂各用例）：一个 scope、两条 scenario——第一条 failed 且第 3 步无记录
# （worker 被中止的形态）、第二条 error 后短路。evidence 是真文件、ref 是真 file:// URI（读路径全程真跑）。

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
    s1 = (Step(0, "Given", '打开 "https://app.example.com/login"'),
          Step(1, "When", "输入用户名「alice」与密码「wrong」"),
          Step(2, "Then", "页面显示「登录成功」"),
          Step(3, "When", "点击「退出」"))
    s2 = (Step(0, "Given", '打开 "https://app.example.com/login"'), Step(1, "Then", "页面提示「账户已锁定」"))
    return Job(scope_id=scope_id, scope_name="登录", engine="novaact",
               scenarios=(Scenario(id="features/login.feature:12", name="密码错误时不放行", steps=s1),
                          Scenario(id="features/login.feature:20", name="锁定账户提示", steps=s2)))


def _explain_run(tmp_path, *, evidence=..., run_status=None, with_results=True, job_only=False,
                 evidence_text=None):
    """在 tmp_path/reports 下搭一个 run：run_meta/run_state + 一份 JobResult（+ 真 evidence.json）。

    evidence=None → step 2 不挂 evidence ref（no_ref）；evidence_text 给非 JSON 串 → unreadable；
    with_results=False → 只落 run_meta/run_state（detached run 未 finalize 的零文件形态）；
    job_only=True → JobResult 有 job 级判定但零 step 记录（worker 没起来/起来就被掐）。
    """
    from gherkai_core.model import (JobResult, JobState, ReportRef, RunMeta, RunState, ScenarioResult,
                                    Status as S, StepResult, Votes)
    root = tmp_path / "reports"
    run_id = "20260910T080630Z-9fa261"
    job = _explain_job()
    refs2 = [ReportRef(kind="trajectory", ref="file:///tmp/act-0.html", label="act 0")]
    if evidence is not ... or evidence_text is not None:
        payload = evidence_text if evidence_text is not None else json.dumps(evidence, ensure_ascii=False)
    else:
        payload = json.dumps(_evidence_fixture(), ensure_ascii=False)
    if evidence is not None or evidence_text is not None:
        ev_dir = root / run_id / "evidence"
        ev_dir.mkdir(parents=True, exist_ok=True)
        ev_path = ev_dir / "evidence.json"
        ev_path.write_text(payload, encoding="utf-8")
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
                   message="job 墙钟超时被停" if job_only else None,
                   report_refs=(ReportRef(kind="summary", ref="file:///tmp/summary.json", label="summary"),))
    st = run_status or (S.ABORTED if job_only else S.FAILED)
    run_store, result_store, _rp, _mk = compose.build_local_stores(report_dir=str(root))
    run_store.save_run(RunMeta(run_id=run_id, created_at="2026-09-10T08:06:30Z", jobs=(job,)),
                       RunState(run_id=run_id, status=st, jobs={job.scope_id: JobState(job.scope_id, st)},
                                started_at="t0", ended_at="t9" if st in m.TERMINAL_STATUSES else None))
    if with_results:
        result_store.save_job_result(run_id, jr)
    return root, run_id


def _explain(capsys, root, run_id, *flags):
    rc = m.main(["explain", run_id, *flags, "--report-dir", str(root)])
    cap = capsys.readouterr()
    return rc, cap.out, cap.err


def test_explain_text_renders_reason_thought_screenshot_and_gaps(tmp_path, capsys):
    """文本形态（ADR 0042 决策四）：原因行、末个带推理的 frame 的 think + 截图、被省略 frame 计数、
    短路旁注只在 shortcircuited 的 step 上、无记录 step、证据缺失的 step 打「无 AI 证据」+ 兜底 ref。"""
    root, run_id = _explain_run(tmp_path)
    rc, out, err = _explain(capsys, root, run_id)
    assert rc == 0  # 证据渲染器不表判定：run 判 failed 也退 0
    assert f"run {run_id}  status=failed" in out
    assert "scope features/login.feature:6  engine=novaact  status=failed  session=01a0deadbeef" in out
    assert "scenario features/login.feature:12  密码错误时不放行  failed" in out
    assert "step 2  Then 页面显示「登录成功」  failed  votes 0/1  (12.1s)" in out
    assert "原因：AI 断言未过多数票（0/1）：页面显示「登录成功」" in out
    assert "act 0  vote=false  url=https://app.example.com/login" in out
    assert "think: I am on the login page." in out and "Returning false." in out
    assert "截图: file:///tmp/act-0-frame-4.jpg" in out
    assert "其余 1 个 frame 已省略（--full 查看）" in out          # 两个 frame，只渲染了带推理的那个
    assert "step 3  When 点击「退出」  无记录（未执行或未上报）" in out
    assert "step 0  Given 打开 \"https://app.example.com/login\"  error  (network_error)" in out
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
    """--scenario：id 全等 / 行号（scenario_id 尾部数字段）/ 标题子串三档，可重复且彼此为或。"""
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
    """--step 单给退 2（步号没有归属）；命中的 scenario 都没有第 N 步 → 退 2 并列出候选 id 与步数；
    正常时只渲染每条命中 scenario 的第 N 步。"""
    root, run_id = _explain_run(tmp_path)
    rc, _out, err = _explain(capsys, root, run_id, "--step", "2")
    assert rc == 2 and "--step 要和 --scenario 一起给" in err
    rc, _out, err = _explain(capsys, root, run_id, "--scenario", "12", "--step", "9")
    assert rc == 2 and "都没有第 9 步" in err and "features/login.feature:12  4 step" in err
    rc, out, _ = _explain(capsys, root, run_id, "--scenario", "12", "--step", "2")
    assert rc == 0 and "step 2  Then" in out and "step 0  Given" not in out


def test_explain_all_expands_passed_and_full_drops_the_text_budget(tmp_path, capsys):
    """--all 也展开 passed step；--full 逐 frame 全文（省略计数消失、无推理的 frame 也现身）。"""
    root, run_id = _explain_run(tmp_path)
    _rc, out, _ = _explain(capsys, root, run_id, "--full")
    assert "其余" not in out and "frame 0  url=https://app.example.com" in out and "frame 1" in out
    _rc, out, _ = _explain(capsys, root, run_id)
    assert "step 0  Given 打开 \"https://app.example.com/login\"  passed  (1.1s)" in out
    passed_block = out.split("step 0  Given")[1].split("step 1")[0]
    assert "无 AI 证据" not in passed_block           # 默认不展开 passed
    _rc, out, _ = _explain(capsys, root, run_id, "--all")
    assert "无 AI 证据" in out.split("step 0  Given")[1].split("step 1")[0]


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
    assert "未找到 scope" in err and "features/login.feature:6" in err   # 列出本 run 已落地的 scope
    assert m.main(["explain", run_id, "features/login.feature:6", "--report-dir", str(root)]) == 0


def test_explain_detached_run_without_job_files_exits_0_with_one_hint(tmp_path, capsys):
    """detached run 未终态时零判定明细（全 job 终态才一次性落）→ 退 0 + 一行提示；--json 不打提示、
    stdout 仍只有一个文档（机读侧靠顶层 status 自明）。"""
    from gherkai_core.model import Status as S
    root, run_id = _explain_run(tmp_path, with_results=False, run_status=S.RUNNING)
    rc, out, err = _explain(capsys, root, run_id)
    assert rc == 0 and out == "" and "判定明细尚未落地" in err and f"gherkai status {run_id} --wait" in err
    rc, out, err = _explain(capsys, root, run_id, "--json")
    assert rc == 0 and err == ""
    doc = json.loads(out)
    assert doc["status"] == "running" and doc["scopes"] == []


def test_explain_nonterminal_sync_run_says_partial(tmp_path, capsys):
    """同步 run 中途已有落地的 job → 首行提示「以下为已完成部分」；--json 不打提示行。"""
    from gherkai_core.model import Status as S
    root, run_id = _explain_run(tmp_path, run_status=S.RUNNING)
    rc, out, err = _explain(capsys, root, run_id)
    assert rc == 0 and "run 仍在跑，以下为已完成部分" in err and "scenario features/login.feature:12" in out
    rc, out, err = _explain(capsys, root, run_id, "--json")
    assert rc == 0 and err == "" and json.loads(out)["status"] == "running"


def test_explain_job_without_step_records_gets_a_job_block(tmp_path, capsys):
    """零 step 记录的 job（worker 没起来/起来就被掐）：单独一段 job 判定块（判定 + 归因 + 产物 + 去看 worker 日志），
    骨架仍逐 step 打「无记录」。"""
    root, run_id = _explain_run(tmp_path, job_only=True)
    rc, out, _ = _explain(capsys, root, run_id)
    assert rc == 0
    assert "判定：aborted  (timeout: job 墙钟超时被停)" in out
    assert "诊断细节见 worker 日志" in out
    assert "report（summary）: file:///tmp/summary.json" in out
    # 两条 scenario 各自也没有判定记录（scenario_done 没到）→ 2 条 scenario 行 + 4+2 条 step 行
    assert out.count("无记录（未执行或未上报）") == 8
    assert "scenario features/login.feature:20  锁定账户提示  无记录（未执行或未上报）" in out
    doc = json.loads(_explain(capsys, root, run_id, "--json")[1])
    assert doc["scopes"][0]["aborted_hint"] is None      # 零记录不是「部分记录」，不打那句


def _explain_cloud_stores(jr, state):
    """假的云端两 store（explain 只读 RunStore/ResultStore）：验接线与读路径，不连真 AWS。"""
    class _RunStore:
        def load_run_state(self, run_id):
            return state

    class _ResultStore:
        def load_all(self, run_id):
            return [jr]

        def load_job_result(self, run_id, scope_id):
            return jr if scope_id == jr.scope_id else None

    return _RunStore(), _ResultStore(), object(), (lambda run_id, report_index: {})


def test_explain_cloud_blocks_on_version_skew_before_any_cloud_read(monkeypatch, capsys):
    """cloud 档第一道闸是版本 skew（先于任何云端读）：block → 退 2，且根本没去装 store。"""
    monkeypatch.setattr(m.compose, "check_backend_skew",
                        lambda **kw: (compose.SKEW_BLOCK, "本机 CLI 新于后端", "1.3.0"))
    monkeypatch.setattr(m.compose, "build_cloud_stores",
                        lambda **kw: (_ for _ in ()).throw(AssertionError("skew 拦下后不该装 store")))
    assert m.main(["explain", "r", "--backend", "cloud", "--prefix", "vfy-", "--region", "us-east-1"]) == 2
    assert "本机 CLI 新于后端" in capsys.readouterr().err


def test_explain_cloud_reads_evidence_from_s3(monkeypatch, capsys):
    """cloud 档：判定明细经 ResultStore 读回，证据经注入的 s3 client `get_object` 读回（s3:// 解引用路径）。"""
    import io

    from gherkai_core.model import JobResult, JobState, ReportRef, RunState, ScenarioResult, StepResult, Votes
    ev = json.dumps(_evidence_fixture(), ensure_ascii=False).encode("utf-8")
    job = _explain_job()
    jr = JobResult(job=job, status=Status.FAILED, session_id="s-1", scenarios=[
        ScenarioResult(scenario_id="features/login.feature:12", status=Status.FAILED, steps=[
            StepResult(index=2, status=Status.FAILED, votes=Votes(yes=0, total=1), message="断言未过",
                       report_refs=(ReportRef(kind="evidence", ref="s3://bkt/reports/r/ev.json", label="evidence"),))])])
    state = RunState(run_id="r", status=Status.FAILED, jobs={job.scope_id: JobState(job.scope_id, Status.FAILED)},
                     ended_at="t9")
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
    """多 scope 下 --scenario 只命中其一：未命中的 scope 不产空壳条目（文本/JSON 同律）；命中的 scope 的
    has_step_records 不随筛选变化。"""
    from gherkai_core.model import Job, JobResult, Scenario, ScenarioResult, Status as S, Step, StepResult
    from gherkai_cli import render
    j1 = _explain_job(scope_id="a.feature:6")
    j2 = Job(scope_id="b.feature:6", scope_name="b", engine="novaact",  # 与 a 无共同 scenario → 筛 :12 时整个未命中
             scenarios=(Scenario(id="features/other.feature:5", name="其它", steps=(Step(0, "Given", "x"),)),))
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
    """纯数字 / :数字 只当行号、不回落标题子串（与 run/plan 同律）；标题子串、id 全等照常。"""
    from gherkai_core.model import Scenario
    sc = Scenario(id="f.feature:12", name="重试3次后放行", steps=())
    hit = m._explain_scenario_matches
    assert hit(sc, ["3"]) is False          # 标题含 3，但 3 不是行号 → 不命中
    assert hit(sc, [":12"]) and hit(sc, ["12"]) and hit(sc, ["重试"]) and hit(sc, ["f.feature:12"])
    assert hit(sc, ["3", "重试"]) is True   # 或
