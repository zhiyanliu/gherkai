"""compose（组合根逻辑）单测：不起任何子进程、不烧钱。"""
from __future__ import annotations

from pathlib import Path

import pytest

from cli import compose
from core.scope import FeatureSource


def test_build_engines_has_both_legs():
    repo = compose.repo_root()
    engines = compose.build_engines(repo)
    assert set(engines) == {"novaact", "midscene"}
    # cmd 指向各自 worker（不实际起进程，只查接线）
    assert any("run_scope.py" in c for c in engines["novaact"].cmd)
    assert any("run-scope.ts" in c for c in engines["midscene"].cmd)


def test_resolver_known_and_unknown():
    engines = compose.build_engines(compose.repo_root())
    resolver = compose.make_resolver(engines)
    assert resolver("novaact") is engines["novaact"]
    with pytest.raises(ValueError, match="未知引擎"):
        resolver("nope")


def test_load_feature_uri_relative_to_repo(tmp_path: Path):
    # 仓库内的 feature → uri 是相对仓库根的路径
    repo = tmp_path
    feat = repo / "features" / "demo.feature"
    feat.parent.mkdir(parents=True)
    feat.write_text("Feature: x\n  Scenario: y\n    When \"做点啥\"\n", encoding="utf-8")
    fs = compose.load_feature(feat, repo)
    assert isinstance(fs, FeatureSource)
    assert fs.uri == "features/demo.feature"
    assert "Scenario: y" in fs.text


def test_load_feature_outside_repo_uses_absolute(tmp_path: Path):
    # 仓库外的 feature → 退用绝对路径（不崩）
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "other.feature"
    outside.write_text("Feature: z\n", encoding="utf-8")
    fs = compose.load_feature(outside, repo)
    assert fs.uri == str(outside.resolve())


def test_repo_root_contains_core_and_engines():
    repo = compose.repo_root()
    assert (repo / "core").is_dir()
    assert (repo / "engines").is_dir()


def test_build_engines_injects_artifact_dirs_symmetrically(tmp_path: Path):
    # 两引擎对称：产物落点经环境变量注入各自 worker 的 env（ADR 0027 产物归位）。
    repo = compose.repo_root()
    nova_dir = tmp_path / "r1" / "nova-trajectories"
    mid_dir = tmp_path / "r1" / "midscene-run"
    engines = compose.build_engines(repo, nova_logs_dir=nova_dir, midscene_run_dir=mid_dir)
    assert engines["novaact"]._env["NOVA_LOGS_DIR"] == str(nova_dir)
    assert engines["midscene"]._env["MIDSCENE_RUN_DIR"] == str(mid_dir)
    # 完整继承 os.environ（叠加而非替换）——否则 worker 丢 AWS 凭证等
    import os
    assert engines["midscene"]._env.get("PATH") == os.environ.get("PATH")


def test_build_engines_no_dirs_leaves_env_none(tmp_path: Path):
    # 不传落点（如 --no-report）：env 保持 None，SubprocessEngine 回落继承 os.environ（不硬替换）。
    engines = compose.build_engines(compose.repo_root())
    assert engines["novaact"]._env is None
    assert engines["midscene"]._env is None
