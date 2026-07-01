"""LocalReportStore 单测（ADR 0027）：归集 manifest + index，纯本地、不连引擎。"""
import json
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


def _run_with_refs(tmp: Path) -> RunResult:
    # 造一个真实 html 文件供 materialize 测试
    art = tmp / "midscene_run" / "report"
    art.mkdir(parents=True)
    html = art / "x.html"
    html.write_text("<html>原生报告</html>", encoding="utf-8")
    return _rr(
        "20260629-abc123",
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
                                          report_refs=(ReportRef(kind="trajectory", ref=ResourceUri("file:///tmp/traj/act_0.html")),))],
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
    # 用户痛点护栏：纯确定性 run（无原生产物 report_refs=[]）的 index.html 也要能看懂结果——
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
    assert "无原生报告产物" in txt
    assert "本页不解析其内容" not in txt        # 已移除的底注


def test_index_html_taints_failed_after_error(tmp_path: Path):
    # 连锁失败读法（ADR 0028）：index.html 判定明细里，同 scenario 内 error 之后的 failed step 加视觉旁注；
    # error 之前的 failed 不加（判据只看 status 顺序、不改判定）。
    run = _rr(
        "chain",
        [_jr(
            "s", "novaact", status=Status.ERROR,
            scenarios=[ScenarioResult(
                scenario_id="s:0", status=Status.ERROR,
                steps=[
                    StepResult(index=0, status=Status.ERROR, error_type="network_error"),   # 上游 error
                    StepResult(index=1, status=Status.FAILED, error_type="assertion_failed"),  # 连锁果 → 加旁注
                ],
            )],
        )],
        status=Status.ERROR,
    )
    store = LocalReportStore(tmp_path / "reports")
    txt = _uri_to_path(store.write(run.run_id, run)).read_text("utf-8")
    assert "可能不可信" in txt                     # error 之后的 failed 有旁注
    # 旁注只挂 step[1]（failed），不挂 step[0]（error 本身）——用 taint CSS class 精确定位
    assert txt.count("taint") >= 2                 # 至少 CSS 定义 + 一处 span（不误挂到 error 步）
    assert "归集索引（ADR" not in txt


def test_materialize_copies_local_artifact(tmp_path: Path):
    run = _run_with_refs(tmp_path)
    store = LocalReportStore(tmp_path / "reports")
    store.write(run.run_id, run, materialize=True)
    run_dir = tmp_path / "reports" / "20260629-abc123"
    # 本地 file:// 产物被按字节拷进 artifacts/（带 seq 前缀去碰撞）
    m = json.loads((run_dir / "manifest.json").read_text("utf-8"))
    report_entry = next(e for e in m["report_index"] if e["kind"] == "report")
    assert report_entry["href"].startswith("artifacts/") and report_entry["href"].endswith("_x.html")
    copied = run_dir / report_entry["href"]
    assert copied.exists() and copied.read_text("utf-8") == "<html>原生报告</html>"


def test_default_no_materialize_keeps_ref(tmp_path: Path):
    run = _run_with_refs(tmp_path)
    store = LocalReportStore(tmp_path / "reports")
    store.write(run.run_id, run)  # materialize=False 默认
    run_dir = tmp_path / "reports" / "20260629-abc123"
    assert not (run_dir / "artifacts").exists()
    m = json.loads((run_dir / "manifest.json").read_text("utf-8"))
    report_entry = next(e for e in m["report_index"] if e["kind"] == "report")
    assert report_entry["href"] == report_entry["ref"]  # 不拷贝时 href == ref


def test_empty_report_refs_still_valid_index(tmp_path: Path):
    run = _rr("empty-run", [_jr("s", "novaact", status=Status.PASSED)], status=Status.PASSED)
    store = LocalReportStore(tmp_path / "reports")
    idx = store.write(run.run_id, run)
    txt = _uri_to_path(idx).read_text("utf-8")
    assert "empty-run" in txt
    assert "无原生报告产物" in txt  # 空态有效页
    m = json.loads((tmp_path / "reports" / "empty-run" / "manifest.json").read_text("utf-8"))
    assert m["report_index"] == []


def test_materialize_same_basename_no_collision(tmp_path: Path):
    # 两个不同目录、同 basename 的本地产物：materialize 不能互相覆盖（数据丢失回归）
    d1 = tmp_path / "a"; d1.mkdir(); (d1 / "report.html").write_text("AAA", encoding="utf-8")
    d2 = tmp_path / "b"; d2.mkdir(); (d2 / "report.html").write_text("BBB", encoding="utf-8")
    run = _rr("collide", [
        _jr("s1", "e", status=Status.PASSED,
            report_refs=(ReportRef(kind="report", ref=ResourceUri(f"file://{d1}/report.html")),)),
        _jr("s2", "e", status=Status.PASSED,
            report_refs=(ReportRef(kind="report", ref=ResourceUri(f"file://{d2}/report.html")),)),
    ], status=Status.PASSED)
    store = LocalReportStore(tmp_path / "reports")
    store.write(run.run_id, run, materialize=True)
    art = tmp_path / "reports" / "collide" / "artifacts"
    copied = sorted(art.iterdir())
    assert len(copied) == 2, f"两个同名产物都应保留，实际 {copied}"
    contents = {p.read_text("utf-8") for p in copied}
    assert contents == {"AAA", "BBB"}  # 都没丢


def test_materialize_percent_encoded_path(tmp_path: Path):
    # ref 含空格/中文 → file:// URI 会 percent-encode；materialize 须能 url2pathname 还原找到文件
    from urllib.parse import quote
    src = tmp_path / "trajectory 词条页.html"
    src.write_text("traj", encoding="utf-8")
    ref = ResourceUri("file://" + quote(str(src)))  # 路径 percent-encode（空格→%20、中文→%XX）
    run = _rr("pe", [
        _jr("s", "novaact", status=Status.PASSED,
            report_refs=(ReportRef(kind="trajectory", ref=ref),)),
    ], status=Status.PASSED)
    store = LocalReportStore(tmp_path / "reports")
    store.write(run.run_id, run, materialize=True)
    art = tmp_path / "reports" / "pe" / "artifacts"
    copied = list(art.iterdir())
    assert len(copied) == 1 and copied[0].read_text("utf-8") == "traj"


def test_file_uri_with_remote_host_not_copied(tmp_path: Path):
    # file://server/share/x.html（带非 localhost host = 远端/UNC）→ 不当本地拷
    run = _rr("unc", [
        _jr("s", "e", status=Status.PASSED,
            report_refs=(ReportRef(kind="scope", ref=ResourceUri("file://server/share/x.html")),)),
    ], status=Status.PASSED)
    store = LocalReportStore(tmp_path / "reports")
    store.write(run.run_id, run, materialize=True)
    # 不拷贝 → 无 artifacts，href 保持原 ref
    assert not (tmp_path / "reports" / "unc" / "artifacts").exists()


def test_remote_ref_not_copied_even_when_materialize(tmp_path: Path):
    # 未来引擎报 https:// 外部 URL：materialize 也不拷贝（不 fetch 远端），href 保持原样
    run = _rr("r", [
        _jr("s", "future", status=Status.PASSED,
            report_refs=(ReportRef(kind="video", ref=ResourceUri("https://example.com/rec.mp4")),)),
    ], status=Status.PASSED)
    store = LocalReportStore(tmp_path / "reports")
    store.write(run.run_id, run, materialize=True)
    m = json.loads((tmp_path / "reports" / "r" / "manifest.json").read_text("utf-8"))
    entry = m["report_index"][0]
    assert entry["kind"] == "video"  # 新 kind 零改 core
    assert entry["href"] == "https://example.com/rec.mp4"  # 远端不拷、原样
