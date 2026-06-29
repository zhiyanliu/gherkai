"""LocalReportStore 单测（ADR 0027）：归集 manifest + index，纯本地、不连引擎。"""
import json
from pathlib import Path

from core.adapters.report_store.local import LocalReportStore
from core.model import (
    JobResult,
    ReportRef,
    RunResult,
    ScenarioResult,
    Status,
    StepResult,
)


def _run_with_refs(tmp: Path) -> RunResult:
    # 造一个真实 html 文件供 materialize 测试
    art = tmp / "midscene_run" / "report"
    art.mkdir(parents=True)
    html = art / "x.html"
    html.write_text("<html>原生报告</html>", encoding="utf-8")
    return RunResult(
        run_id="20260629-abc123",
        status=Status.PASSED,
        duration_ms=12000.0,
        total_tokens=10573,
        jobs=[
            JobResult(
                scope_id="features/wiki.feature:6",
                status=Status.PASSED,
                engine="midscene",
                total_tokens=10573,
                duration_ms=11000.0,
                report_refs=(ReportRef(kind="scope", ref=f"file://{html}", label="Midscene report"),),
                scenarios=[
                    ScenarioResult(
                        scenario_id="features/wiki.feature:6",
                        status=Status.PASSED,
                        steps=[StepResult(index=0, status=Status.PASSED)],
                        # scenario 级 ref（act 粒度，对称 Nova）
                        report_refs=(ReportRef(kind="act", ref="file:///tmp/traj/act_0.html"),),
                    )
                ],
            )
        ],
    )


def test_writes_manifest_and_index(tmp_path: Path):
    run = _run_with_refs(tmp_path)
    store = LocalReportStore(tmp_path / "reports")
    index = store.write(run.run_id, run, created_at="2026-06-29T00:00:00Z")

    run_dir = tmp_path / "reports" / "20260629-abc123"
    assert index == run_dir / "index.html"
    assert (run_dir / "manifest.json").exists()
    assert index.exists()


def test_manifest_shape(tmp_path: Path):
    run = _run_with_refs(tmp_path)
    store = LocalReportStore(tmp_path / "reports")
    store.write(run.run_id, run, created_at="2026-06-29T00:00:00Z")
    m = json.loads((tmp_path / "reports" / "20260629-abc123" / "manifest.json").read_text("utf-8"))

    assert m["schema_version"] == 1
    assert m["run_id"] == "20260629-abc123"
    assert m["created_at"] == "2026-06-29T00:00:00Z"
    assert m["tool"] == "yaozhou"
    # result 是 to_dict 的单一真理源
    assert m["result"]["run_id"] == "20260629-abc123"
    assert m["result"]["jobs"][0]["engine"] == "midscene"
    # report_index 扁平投影：scope 级（scenario_id=None）+ act 级各一条
    idx = m["report_index"]
    assert len(idx) == 2
    scope_entry = next(e for e in idx if e["kind"] == "scope")
    act_entry = next(e for e in idx if e["kind"] == "act")
    assert scope_entry["scenario_id"] is None
    assert scope_entry["engine"] == "midscene"
    assert act_entry["scenario_id"] == "features/wiki.feature:6"


def test_index_html_links_and_summary(tmp_path: Path):
    run = _run_with_refs(tmp_path)
    store = LocalReportStore(tmp_path / "reports")
    idx = store.write(run.run_id, run, created_at="x")
    txt = idx.read_text("utf-8")
    assert "20260629-abc123" in txt
    assert "passed" in txt.lower()
    assert "midscene" in txt
    assert "Midscene report" in txt  # label 作锚文本
    assert "[scope]" in txt and "[act]" in txt  # kind 原样回显（不分支）


def test_materialize_copies_local_artifact(tmp_path: Path):
    run = _run_with_refs(tmp_path)
    store = LocalReportStore(tmp_path / "reports")
    store.write(run.run_id, run, materialize=True)
    run_dir = tmp_path / "reports" / "20260629-abc123"
    # 本地 file:// 产物被按字节拷进 artifacts/（带 seq 前缀去碰撞）
    m = json.loads((run_dir / "manifest.json").read_text("utf-8"))
    scope_entry = next(e for e in m["report_index"] if e["kind"] == "scope")
    assert scope_entry["href"].startswith("artifacts/") and scope_entry["href"].endswith("_x.html")
    copied = run_dir / scope_entry["href"]
    assert copied.exists() and copied.read_text("utf-8") == "<html>原生报告</html>"


def test_default_no_materialize_keeps_ref(tmp_path: Path):
    run = _run_with_refs(tmp_path)
    store = LocalReportStore(tmp_path / "reports")
    store.write(run.run_id, run)  # materialize=False 默认
    run_dir = tmp_path / "reports" / "20260629-abc123"
    assert not (run_dir / "artifacts").exists()
    m = json.loads((run_dir / "manifest.json").read_text("utf-8"))
    scope_entry = next(e for e in m["report_index"] if e["kind"] == "scope")
    assert scope_entry["href"] == scope_entry["ref"]  # 不拷贝时 href == ref


def test_empty_report_refs_still_valid_index(tmp_path: Path):
    run = RunResult(run_id="empty-run", status=Status.PASSED, jobs=[
        JobResult(scope_id="s", status=Status.PASSED, engine="novaact"),
    ])
    store = LocalReportStore(tmp_path / "reports")
    idx = store.write(run.run_id, run)
    txt = idx.read_text("utf-8")
    assert "empty-run" in txt
    assert "无原生报告产物" in txt  # 空态有效页
    m = json.loads((tmp_path / "reports" / "empty-run" / "manifest.json").read_text("utf-8"))
    assert m["report_index"] == []


def test_materialize_same_basename_no_collision(tmp_path: Path):
    # 两个不同目录、同 basename 的本地产物：materialize 不能互相覆盖（数据丢失回归）
    d1 = tmp_path / "a"; d1.mkdir(); (d1 / "report.html").write_text("AAA", encoding="utf-8")
    d2 = tmp_path / "b"; d2.mkdir(); (d2 / "report.html").write_text("BBB", encoding="utf-8")
    run = RunResult(run_id="collide", status=Status.PASSED, jobs=[
        JobResult(scope_id="s1", status=Status.PASSED, engine="e",
                  report_refs=(ReportRef(kind="scope", ref=f"file://{d1}/report.html"),)),
        JobResult(scope_id="s2", status=Status.PASSED, engine="e",
                  report_refs=(ReportRef(kind="scope", ref=f"file://{d2}/report.html"),)),
    ])
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
    ref = "file://" + quote(str(src))  # 路径 percent-encode（空格→%20、中文→%XX）
    run = RunResult(run_id="pe", status=Status.PASSED, jobs=[
        JobResult(scope_id="s", status=Status.PASSED, engine="novaact",
                  report_refs=(ReportRef(kind="act", ref=ref),)),
    ])
    store = LocalReportStore(tmp_path / "reports")
    store.write(run.run_id, run, materialize=True)
    art = tmp_path / "reports" / "pe" / "artifacts"
    copied = list(art.iterdir())
    assert len(copied) == 1 and copied[0].read_text("utf-8") == "traj"


def test_file_uri_with_remote_host_not_copied(tmp_path: Path):
    # file://server/share/x.html（带非 localhost host = 远端/UNC）→ 不当本地拷
    run = RunResult(run_id="unc", status=Status.PASSED, jobs=[
        JobResult(scope_id="s", status=Status.PASSED, engine="e",
                  report_refs=(ReportRef(kind="scope", ref="file://server/share/x.html"),)),
    ])
    store = LocalReportStore(tmp_path / "reports")
    store.write(run.run_id, run, materialize=True)
    # 不拷贝 → 无 artifacts，href 保持原 ref
    assert not (tmp_path / "reports" / "unc" / "artifacts").exists()


def test_remote_ref_not_copied_even_when_materialize(tmp_path: Path):
    # 未来引擎报 https:// 外部 URL：materialize 也不拷贝（不 fetch 远端），href 保持原样
    run = RunResult(run_id="r", status=Status.PASSED, jobs=[
        JobResult(scope_id="s", status=Status.PASSED, engine="future",
                  report_refs=(ReportRef(kind="video", ref="https://example.com/rec.mp4"),)),
    ])
    store = LocalReportStore(tmp_path / "reports")
    store.write(run.run_id, run, materialize=True)
    m = json.loads((tmp_path / "reports" / "r" / "manifest.json").read_text("utf-8"))
    entry = m["report_index"][0]
    assert entry["kind"] == "video"  # 新 kind 零改 core
    assert entry["href"] == "https://example.com/rec.mp4"  # 远端不拷、原样
