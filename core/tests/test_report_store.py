"""LocalReportStore 单测（ADR 0027）：归集 manifest + index，纯本地、不连引擎。"""
import json
import os
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname

from core.adapters.report_store.local import LocalReportStore
from core.model import (
    Job,
    JobResult,
    ReportRef,
    ResourceUri,
    RunMeta,
    RunResult,
    ScenarioResult,
    Status,
    StepResult,
    Votes,
)


def _uri_to_path(uri: str) -> Path:
    """write() 现返回 file:// ResourceUri（ADR 0027 统一资源指针）；测试侧还原成本地 Path 读内容。"""
    return Path(url2pathname(urlparse(uri).path))


def _jr(scope_id: str, engine: str, **kw) -> JobResult:
    """测试 helper：JobResult 持有 Job（definition）+ 判定字段。"""
    job = Job(scope_id=scope_id, scope_name=scope_id, engine=engine, scenarios=())
    return JobResult(job=job, **kw)


def _rr(run_id: str, jobs: list[JobResult], **kw) -> RunResult:
    """测试 helper：RunResult = RunMeta(definition) + 判定 jobs。run_meta.jobs 取自各 jr.job。"""
    meta = RunMeta(run_id=run_id, created_at="", jobs=tuple(jr.job for jr in jobs))
    return RunResult(run_meta=meta, jobs=jobs, **kw)


_RUN_ID = "20260629-abc123"


def _run_with_refs(tmp: Path) -> RunResult:
    # 造真实产物文件，落在 **run 树内**（reports/<run_id>/ 下，对齐真实用法：cli 把 SDK 落点设进 run 目录，
    # ADR 0027）——使 href 相对化命中；相对 run_dir 后 href 应是 "midscene-run/report/x.html" 这类树内相对路径。
    run_dir = tmp / "reports" / _RUN_ID
    report = run_dir / "midscene-run" / "report"
    report.mkdir(parents=True)
    html = report / "x.html"
    html.write_text("<html>原生报告</html>", encoding="utf-8")
    traj = run_dir / "nova-trajectories" / "sess"
    traj.mkdir(parents=True)
    traj_html = traj / "act_0.html"
    traj_html.write_text("<html>traj</html>", encoding="utf-8")
    return _rr(
        _RUN_ID,
        [
            _jr(
                "features/wiki.feature:6", "midscene",
                status=Status.PASSED,
                total_tokens=10573,
                duration_ms=11000.0,
                # scope 级 ref（Midscene report，kind=report，ADR 0027）
                report_refs=(ReportRef(kind="report", ref=ResourceUri(f"file://{html}"), label="Midscene report"),),
                scenarios=[
                    ScenarioResult(
                        scenario_id="features/wiki.feature:6",
                        status=Status.PASSED,
                        # step 级 ref（Nova trajectory 下沉，kind=trajectory，ADR 0027）
                        steps=[StepResult(index=0, status=Status.PASSED,
                                          report_refs=(ReportRef(kind="trajectory", ref=ResourceUri(f"file://{traj_html}")),))],
                    )
                ],
            )
        ],
        status=Status.PASSED,
        duration_ms=12000.0,
        total_tokens=10573,
    )


def test_writes_manifest_and_index(tmp_path: Path):
    run = _run_with_refs(tmp_path)
    store = LocalReportStore(tmp_path / "reports")
    index = store.write(run.run_id, run, created_at="2026-06-29T00:00:00Z")

    run_dir = tmp_path / "reports" / "20260629-abc123"
    # write 返回 file:// ResourceUri（不再是裸 Path）：还原成 Path 后应等于、且文件确实存在
    assert _uri_to_path(index) == (run_dir / "index.html").resolve()
    assert index.startswith("file://") and index.endswith("/index.html")
    assert (run_dir / "manifest.json").exists()
    assert _uri_to_path(index).exists()


def test_manifest_shape(tmp_path: Path):
    run = _run_with_refs(tmp_path)
    store = LocalReportStore(tmp_path / "reports")
    store.write(run.run_id, run, created_at="2026-06-29T00:00:00Z")
    m = json.loads((tmp_path / "reports" / "20260629-abc123" / "manifest.json").read_text("utf-8"))

    assert m["schema_version"] == 1
    assert m["run_id"] == "20260629-abc123"
    assert m["created_at"] == "2026-06-29T00:00:00Z"
    assert "tool" not in m  # 不硬编码不确定的产品名进对外契约（删，无聚合多工具需求）
    # manifest 是纯派生视图：不内嵌 result 真值副本（靠 run_id 软引用，判定真值在 ResultStore，ADR 0027/0016）
    assert "result" not in m
    # report_index 扁平投影：scope 级（scenario_id=None）report + step 级 trajectory 各一条（ADR 0027）
    idx = m["report_index"]
    assert len(idx) == 2
    report_entry = next(e for e in idx if e["kind"] == "report")
    traj_entry = next(e for e in idx if e["kind"] == "trajectory")
    assert report_entry["scenario_id"] is None and report_entry["step_index"] is None  # scope 级
    assert report_entry["engine"] == "midscene"
    # step 级：scenario_id + step_index 都非空（粒度由挂载层级表达，非 kind）
    assert traj_entry["scenario_id"] == "features/wiki.feature:6" and traj_entry["step_index"] == 0
    # manifest 每条只含 href（导航链接），不含 ref（原始指针随 materialize 一并移除——无人读 + 会成绝对泄漏，ADR 0027）
    assert "href" in report_entry and "ref" not in report_entry
    # href 相对化：产物在 run 树内 → 相对 run_dir 的 POSIX 路径（目录可整体搬走、链接不断）
    assert report_entry["href"] == "midscene-run/report/x.html"
    assert traj_entry["href"] == "nova-trajectories/sess/act_0.html"


def test_index_html_links_and_summary(tmp_path: Path):
    run = _run_with_refs(tmp_path)
    store = LocalReportStore(tmp_path / "reports")
    idx = store.write(run.run_id, run, created_at="x")
    txt = _uri_to_path(idx).read_text("utf-8")
    assert "20260629-abc123" in txt
    assert "passed" in txt.lower()
    assert "midscene" in txt
    assert "Midscene report" in txt  # label 作锚文本
    assert "[report]" in txt and "[trajectory]" in txt  # kind 原样回显（不分支）
    assert "step[0]" in txt  # step 级 trajectory 在导航里带 step[N]（同 scenario 多 trajectory 区分）
    # 判定明细块：scope_id / scenario_id / step / sessionId 直接呈现在页上（不止产物导航）
    assert "判定明细" in txt
    assert "features/wiki.feature:6" in txt   # scenario_id
    assert "step[0]" in txt                   # step 级判定


def test_index_html_votes_tally_shown_only_when_multi_vote(tmp_path: Path):
    # 投票 tally：assertion_votes>1 才在 index.html 显 N/N 票；==1（单次判定）隐藏（避免 1/1 噪声）。
    def _run(total: int) -> RunResult:
        return _rr("vrun", [_jr(
            "s", "midscene", status=Status.PASSED,
            scenarios=[ScenarioResult(scenario_id="s:0", status=Status.PASSED, steps=[
                StepResult(index=0, status=Status.PASSED, votes=Votes(yes=total, total=total)),
            ])],
        )], status=Status.PASSED)
    store = LocalReportStore(tmp_path / "reports")
    # 多票：显 tally
    txt3 = _uri_to_path(store.write("vrun", _run(3), created_at="x")).read_text("utf-8")
    assert "3/3 票" in txt3
    # 单票：隐藏（不出现 1/1 票）
    import shutil; shutil.rmtree(tmp_path / "reports")
    txt1 = _uri_to_path(store.write("vrun", _run(1), created_at="x")).read_text("utf-8")
    assert "1/1 票" not in txt1


def test_index_html_shows_verdict_even_without_report_refs(tmp_path: Path):
    # 用户痛点护栏：纯确定性 run（无引擎报告产物 report_refs=[]）的 index.html 也要能看懂结果——
    # 判定明细（job/scenario/step status + 时长 + sessionId）直接渲染，不再是一张白纸。
    run = _rr(
        "det-run",
        [_jr(
            "features/anchor.feature:7", "midscene",
            status=Status.PASSED, duration_ms=3800.0, session_id="01KW9DSK",
            scenarios=[ScenarioResult(
                scenario_id="features/anchor.feature:7", status=Status.PASSED, duration_ms=3200.0,
                steps=[
                    StepResult(index=0, status=Status.PASSED, duration_ms=3200.0),
                    StepResult(index=1, status=Status.PASSED, duration_ms=0.04),
                ],
            )],
        )],
        status=Status.PASSED, duration_ms=4000.0,
    )
    store = LocalReportStore(tmp_path / "reports")
    idx = store.write(run.run_id, run)
    txt = _uri_to_path(idx).read_text("utf-8")
    # 判定明细可见
    assert "判定明细" in txt
    assert "features/anchor.feature:7" in txt
    assert "step[0]" in txt and "step[1]" in txt
    assert "01KW9DSK" in txt                   # sessionId 呈现（会话血缘可追）
    # 产物区为空但有意义提示，且不再含已移除的内部设计语
    assert "无引擎报告产物" in txt
    assert "本页不解析其内容" not in txt        # 已移除的底注


def test_index_html_taints_shortcircuited_step(tmp_path: Path):
    # 连锁失败旁注（ADR 0031 决定六）：index.html 判定明细里，被 scope 内短路的 step（shortcircuited=True，
    # status=skipped）加视觉旁注"因前置 step error 被跳过"。判据读 shortcircuited 布尔（不再按 status 顺序猜）。
    run = _rr(
        "chain",
        [_jr(
            "s", "novaact", status=Status.ERROR,
            scenarios=[ScenarioResult(
                scenario_id="s:0", status=Status.ERROR,
                steps=[
                    StepResult(index=0, status=Status.ERROR, error_type="network_error"),   # 上游 error（不加旁注）
                    StepResult(index=1, status=Status.SKIPPED, shortcircuited=True),          # 被短路 → 加旁注
                ],
            )],
        )],
        status=Status.ERROR,
    )
    store = LocalReportStore(tmp_path / "reports")
    txt = _uri_to_path(store.write(run.run_id, run)).read_text("utf-8")
    assert "被跳过" in txt                          # 被短路的 step 有旁注
    assert "skipped" in txt                         # 短路 step 显 skipped 态
    # 旁注只挂 step[1]（shortcircuited），不挂 step[0]（error 本身）——用 taint CSS class 精确定位
    assert txt.count("taint") >= 2                  # 至少 CSS 定义 + 一处 span（不误挂到 error 步）


def test_index_html_no_taint_on_plain_failed(tmp_path: Path):
    # 反向护栏（ADR 0031 决定六）：普通 failed（非短路、shortcircuited=False）不加旁注——
    # 避免误伤正常业务失败。判据迁到 shortcircuited 后，"error 后的 failed"若非短路态就不该再加旁注。
    run = _rr(
        "plain",
        [_jr(
            "s", "novaact", status=Status.ERROR,
            scenarios=[ScenarioResult(
                scenario_id="s:0", status=Status.ERROR,
                steps=[
                    StepResult(index=0, status=Status.ERROR, error_type="network_error"),
                    StepResult(index=1, status=Status.FAILED, error_type="assertion_failed"),  # 普通 failed，非短路
                ],
            )],
        )],
        status=Status.ERROR,
    )
    store = LocalReportStore(tmp_path / "reports")
    txt = _uri_to_path(store.write(run.run_id, run)).read_text("utf-8")
    assert "被跳过" not in txt                       # 无 shortcircuited step → 无旁注 span
    assert txt.count("taint") == 1                  # 只剩 CSS 定义那一处，无 span


def test_href_relativized_for_artifact_in_run_tree(tmp_path: Path):
    # href 相对化（ADR 0027）：产物在 run 树内 → href 是相对 run_dir 的 POSIX 路径（目录可整拷、链接不断）；
    # 不拷贝产物（无 artifacts/ 目录）、不改写 ref（manifest 已不含 ref）。
    run = _run_with_refs(tmp_path)
    store = LocalReportStore(tmp_path / "reports")
    store.write(run.run_id, run)
    run_dir = tmp_path / "reports" / _RUN_ID
    assert not (run_dir / "artifacts").exists()  # 不再拷贝产物
    m = json.loads((run_dir / "manifest.json").read_text("utf-8"))
    report_entry = next(e for e in m["report_index"] if e["kind"] == "report")
    assert report_entry["href"] == "midscene-run/report/x.html"  # 相对 run_dir
    # href 相对链接从 run_dir 出发解析得回原文件（验证"目录可整体搬走"）
    assert (run_dir / report_entry["href"]).read_text("utf-8") == "<html>原生报告</html>"


def test_href_falls_back_absolute_for_artifact_outside_run_tree(tmp_path: Path):
    # 产物落在 run 树外（worker 没吃到 NOVA_LOGS_DIR/MIDSCENE_RUN_DIR、落 SDK 临时目录）→ relative_to 抛错
    # → href 回落绝对 file://（该条不可移植，已知取舍，ADR 0027）。非"所有 local href 都相对"。
    outside = tmp_path / "elsewhere"; outside.mkdir()
    html = outside / "x.html"; html.write_text("out", encoding="utf-8")
    run = _rr("outside-run", [
        _jr("s", "midscene", status=Status.PASSED,
            report_refs=(ReportRef(kind="report", ref=ResourceUri(f"file://{html}")),)),
    ], status=Status.PASSED)
    store = LocalReportStore(tmp_path / "reports")
    store.write(run.run_id, run)
    m = json.loads((tmp_path / "reports" / "outside-run" / "manifest.json").read_text("utf-8"))
    entry = m["report_index"][0]
    assert entry["href"] == f"file://{html}"  # 回落绝对（树外，不可相对化）


def test_href_relativized_percent_encoded_path(tmp_path: Path):
    # ref 含空格/中文 → file:// URI 会 percent-encode；相对化须能 url2pathname 还原、算出正确相对 href。
    from urllib.parse import quote
    run_dir = tmp_path / "reports" / "pe"
    sub = run_dir / "nova-trajectories"; sub.mkdir(parents=True)
    src = sub / "trajectory 词条页.html"
    src.write_text("traj", encoding="utf-8")
    ref = ResourceUri("file://" + quote(str(src)))  # 路径 percent-encode（空格→%20、中文→%XX）
    run = _rr("pe", [
        _jr("s", "novaact", status=Status.PASSED,
            report_refs=(ReportRef(kind="trajectory", ref=ref),)),
    ], status=Status.PASSED)
    store = LocalReportStore(tmp_path / "reports")
    store.write(run.run_id, run)
    m = json.loads((run_dir / "manifest.json").read_text("utf-8"))
    entry = m["report_index"][0]
    assert entry["href"] == "nova-trajectories/trajectory 词条页.html"  # 相对、已解码
    assert (run_dir / entry["href"]).read_text("utf-8") == "traj"


def test_file_uri_with_remote_host_kept_as_ref(tmp_path: Path):
    # file://server/share/x.html（带非 localhost host = 远端/UNC）→ 不当本地文件、href 原样 ==ref
    run = _rr("unc", [
        _jr("s", "e", status=Status.PASSED,
            report_refs=(ReportRef(kind="report", ref=ResourceUri("file://server/share/x.html")),)),
    ], status=Status.PASSED)
    store = LocalReportStore(tmp_path / "reports")
    store.write(run.run_id, run)
    m = json.loads((tmp_path / "reports" / "unc" / "manifest.json").read_text("utf-8"))
    assert m["report_index"][0]["href"] == "file://server/share/x.html"  # 原样、不相对化


def test_remote_ref_kept_as_ref(tmp_path: Path):
    # 未来引擎报 https:// / s3:// 外部 URL：不相对化（只 file:// 相对化，只按 scheme 分支），href 原样。
    run = _rr("r", [
        _jr("s", "future", status=Status.PASSED,
            report_refs=(ReportRef(kind="video", ref=ResourceUri("https://example.com/rec.mp4")),)),
    ], status=Status.PASSED)
    store = LocalReportStore(tmp_path / "reports")
    store.write(run.run_id, run)
    m = json.loads((tmp_path / "reports" / "r" / "manifest.json").read_text("utf-8"))
    entry = m["report_index"][0]
    assert entry["kind"] == "video"  # 新 kind 零改 core
    assert entry["href"] == "https://example.com/rec.mp4"  # 远端不相对、原样


def test_href_relativized_through_symlinked_run_dir(tmp_path: Path):
    # 锚住 _relative_href 里 run_dir.resolve() 的 symlink 防御（review #3：否则 macOS /tmp↔/private/tmp
    # 或任何 symlinked 落点下，run_dir(经 symlink) 与 ref(已规范化绝对) 不一致 → relative_to 抛 ValueError →
    # 误回落绝对 href、报告失可移植性）。用真 os.symlink 构造：run_dir 经软链传入，产物 ref 用规范化绝对路径。
    real_base = tmp_path / "real"; real_base.mkdir()
    link_base = tmp_path / "link"
    os.symlink(real_base, link_base)  # link_base → real_base
    # 产物落在（经软链看到的）run_dir 树内，但 ref 用规范化绝对路径（模拟 worker 报 file://<resolved>）
    run_id = "sym-run"
    art = real_base / run_id / "midscene-run" / "report"
    art.mkdir(parents=True)
    html = art / "x.html"; html.write_text("<html>s</html>", encoding="utf-8")
    ref = ResourceUri(f"file://{html.resolve()}")  # 规范化绝对（不含软链段）
    run = _rr(run_id, [
        _jr("s", "midscene", status=Status.PASSED,
            report_refs=(ReportRef(kind="report", ref=ref),)),
    ], status=Status.PASSED)
    # store 的 root 经软链传入 → run_dir = link/<run_id>（含软链段），与 ref（已规范化）字面不一致
    store = LocalReportStore(link_base)
    store.write(run.run_id, run)
    m = json.loads((real_base / run_id / "manifest.json").read_text("utf-8"))
    # 两侧都 resolve 后才能算相对 → href 仍是树内相对路径（去掉任一 resolve 会回落绝对 file://，测试即红）
    assert m["report_index"][0]["href"] == "midscene-run/report/x.html"


def test_href_relativized_for_bare_path_ref(tmp_path: Path):
    # 裸路径 ref（无 scheme）当本地文件相对化（review #6：_local_path 的防御性分支，钉住行为）。
    # 生产 ref 恒带 scheme（ADR 0024），此为防御分支——显式测，避免它悄悄失效或被误删。
    run_dir = tmp_path / "reports" / "bare"
    sub = run_dir / "nova-trajectories"; sub.mkdir(parents=True)
    src = sub / "act_0.html"; src.write_text("bare", encoding="utf-8")
    ref = ResourceUri(str(src.resolve()))  # 裸绝对路径，无 file:// 前缀
    run = _rr("bare", [
        _jr("s", "novaact", status=Status.PASSED,
            report_refs=(ReportRef(kind="trajectory", ref=ref),)),
    ], status=Status.PASSED)
    store = LocalReportStore(tmp_path / "reports")
    store.write(run.run_id, run)
    m = json.loads((run_dir / "manifest.json").read_text("utf-8"))
    assert m["report_index"][0]["href"] == "nova-trajectories/act_0.html"  # 裸本地路径也相对化


def test_empty_report_refs_still_valid_index(tmp_path: Path):
    run = _rr("empty-run", [_jr("s", "novaact", status=Status.PASSED)], status=Status.PASSED)
    store = LocalReportStore(tmp_path / "reports")
    idx = store.write(run.run_id, run)
    txt = _uri_to_path(idx).read_text("utf-8")
    assert "empty-run" in txt
    assert "无引擎报告产物" in txt  # 空态有效页
    m = json.loads((tmp_path / "reports" / "empty-run" / "manifest.json").read_text("utf-8"))
    assert m["report_index"] == []
