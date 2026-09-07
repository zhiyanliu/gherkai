"""`--no-report` = 真不生成（ADR 0037 决策 3）：env GHERKAI_NO_ARTIFACTS=1 时 worker 不收集/不上报引擎原生产物。"""
from __future__ import annotations

from types import SimpleNamespace

from gherkai_worker_novaact import run_scope as rs


def test_flag_reads_env(monkeypatch):
    monkeypatch.delenv("GHERKAI_NO_ARTIFACTS", raising=False)
    assert rs._no_artifacts() is False
    monkeypatch.setenv("GHERKAI_NO_ARTIFACTS", "1")
    assert rs._no_artifacts() is True


def test_trajectory_collection_is_skipped_under_no_artifacts(monkeypatch, tmp_path):
    """有 metadata.trajectory_file_path 也不收集——否则 step_done 会带 reportRef、RunResult 会打印一个「产物」路径。"""
    traj = tmp_path / "act_1_x_trajectory.json"
    traj.write_text("{}", encoding="utf-8")
    r = SimpleNamespace(metadata=SimpleNamespace(trajectory_file_path=str(traj)))
    monkeypatch.setenv("GHERKAI_NO_ARTIFACTS", "1")
    sink: list = []
    rs._collect_traj(r, sink)
    assert sink == []
    monkeypatch.delenv("GHERKAI_NO_ARTIFACTS")
    rs._collect_traj(r, sink)
    assert sink == [str(traj)]  # 对照：正常档照常收集（html 不存在回退 json）
