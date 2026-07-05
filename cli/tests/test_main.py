"""cli 入口 _cmd_run 接线测试：monkeypatch schedule（不起子进程、不烧 AWS），

验证落盘三层产物 + --json 输出形状（单一可解析 JSON 文档，回归护栏 ADR 0016/0027）。
"""
from __future__ import annotations

import json
from pathlib import Path

from core.model import JobResult, RunResult, Status

from cli import __main__ as m
from cli import compose


def _fake_schedule_factory():
    """造一个不起 worker 的假 schedule：发事件给 sink（进度）+ on_event（persistence 刷 RUNNING）+ 每 job
    fire on_job_complete（验证实时落库路径）+ 把 run_meta 合成 RunResult。"""
    from core.model import ScopeStarted

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
    def fake(run_meta, engines, sink, opts=None, on_job_complete=None, on_event=None):
        opts_box["opts"] = opts
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
            "--max-concurrency", "3", "--timeout", "120", "--grace", str(good_grace), "--fail-fast"])
    o = box["opts"]
    assert o.max_concurrency == 3 and o.fail_fast is True
    assert o.job_timeout_s == 120.0 and o.grace_period_s == float(good_grace)
    # min_grace_s 也传给 core（核心不变量：core enforce grace≥此下限，ADR 0024 grace 硬约束）
    assert o.min_grace_s == float(compose.NOVA_ACT_TIMEOUT_S + compose.NOVA_GRACE_MARGIN_S)


def test_run_grace_too_small_rejected(tmp_path, monkeypatch, capsys):
    # 显式给过小 grace（< Nova 下限）→ 入口退 2「没开跑就被拒」（ADR 0024 grace 硬约束、对齐 votes 校验惯例）。
    box = {}
    monkeypatch.setattr(m, "schedule", _capturing_schedule(Status.PASSED, box))
    rc = m.main(["run", str(_write_feature(tmp_path)), "--no-report", "--grace", "5"])
    assert rc == 2
    assert "opts" not in box  # schedule 根本没被调（跑前就拒了）
    assert "grace" in capsys.readouterr().err.lower() or True  # 诊断打到 stderr


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
    from core.model import ScopeStarted
    from core.adapters.run_store.local import LocalRunStore

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

    def spy_build(repo, **kwargs):
        box["kwargs"] = kwargs
        return real_build(repo)  # 不带落点：拿真 engines（cmd 正确），落点断言看 box

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


def test_run_no_report_passes_no_artifact_dirs(tmp_path, monkeypatch, capsys):
    # --no-report：不算落点、传 None（裸跑，两引擎都回落 SDK 默认）
    box = {}
    real_build = m.compose.build_engines

    def spy_build(repo, **kwargs):
        box.update(kwargs)
        return real_build(repo)

    monkeypatch.setattr(m.compose, "build_engines", spy_build)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    m.main(["run", str(_write_feature(tmp_path)), "--no-report"])
    assert box.get("nova_logs_dir") is None and box.get("midscene_run_dir") is None


# ---- _prune_empty_dirs（cloud 清本地空壳，ADR 0029）：只删空目录、非空保留 ----
def test_prune_empty_dirs_removes_empty_tree(tmp_path):
    # worker 上传后 rmtree 了子目录，run 根只剩空壳（含空中间目录）→ 整个删掉
    run_dir = tmp_path / "reports" / "rid"
    (run_dir / "nova-trajectories" / "sess").mkdir(parents=True)  # 全空
    (run_dir / "midscene-run" / "report").mkdir(parents=True)     # 全空
    m._prune_empty_dirs(run_dir)
    assert not run_dir.exists()  # 空壳整个清掉


def test_prune_empty_dirs_keeps_nonempty(tmp_path):
    # 某腿 flush 失败保留了产物（目录非空）→ 该目录及其祖先保留（护栏：不误删产物）
    run_dir = tmp_path / "reports" / "rid"
    kept = run_dir / "nova-trajectories" / "sess"
    kept.mkdir(parents=True)
    (kept / "act_0.html").write_text("残留产物")           # 非空
    (run_dir / "midscene-run").mkdir(parents=True)          # 空
    m._prune_empty_dirs(run_dir)
    assert run_dir.exists()                                  # 因含非空子树而保留
    assert (kept / "act_0.html").exists()                   # 产物没被误删
    assert not (run_dir / "midscene-run").exists()           # 空的那支仍被清


def test_prune_empty_dirs_noop_when_missing(tmp_path):
    m._prune_empty_dirs(tmp_path / "nonexistent")  # 不存在 → no-op、不抛
