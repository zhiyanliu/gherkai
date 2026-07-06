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


def test_build_engines_no_dirs_midscene_env_none(tmp_path: Path):
    # 不传落点（如 --no-report）：midscene env 保持 None，SubprocessEngine 回落继承 os.environ（不硬替换）。
    engines = compose.build_engines(compose.repo_root())
    assert engines["midscene"]._env is None


def test_build_engines_nova_always_has_act_timeout(tmp_path: Path):
    # Nova env **恒非 None**：即便无产物落点，组合根也要注入 NOVA_ACT_TIMEOUT_S（双端同源，ADR 0024 grace 硬约束）——
    # worker 读它作 act timeout、组合根用同一常量算 grace 下限，消除两处独立 120 的漂移。
    engines = compose.build_engines(compose.repo_root())
    assert engines["novaact"]._env is not None
    assert engines["novaact"]._env["NOVA_ACT_TIMEOUT_S"] == str(compose.NOVA_ACT_TIMEOUT_S)


def test_build_engines_injects_artifact_s3_env_symmetrically(tmp_path: Path):
    # artifact_s3=(bucket, prefix) → 两腿 worker 都拿到 ARTIFACT_S3_BUCKET/PREFIX env（worker from_env 真正读的东西，
    # ADR 0029）。跨越"__main__ 算元组 → compose 翻成 env"这道缝，防键名写错/合并漏掉时静默退回 file://（review #5）。
    repo = compose.repo_root()
    nova_dir = tmp_path / "rid" / "nova-trajectories"
    mid_dir = tmp_path / "rid" / "midscene-run"
    engines = compose.build_engines(
        repo, nova_logs_dir=nova_dir, midscene_run_dir=mid_dir, artifact_s3=("bkt", "runs/rid/"),
    )
    for eng in ("novaact", "midscene"):
        assert engines[eng]._env["ARTIFACT_S3_BUCKET"] == "bkt"
        assert engines[eng]._env["ARTIFACT_S3_PREFIX"] == "runs/rid/"  # 与 S3ReportStore 同前缀（逐字）


def test_build_engines_artifact_s3_alone_makes_env_nonnull(tmp_path: Path):
    # 只给 artifact_s3、不给 local dir（防御 _env 的 "local_dir is None and not s3_env" 早返回守卫吞掉 s3_env）：
    # env 必须非 None 且含 S3 落点，否则 worker 拿不到、静默退回 file://。
    engines = compose.build_engines(compose.repo_root(), artifact_s3=("bkt", "runs/rid/"))
    for eng in ("novaact", "midscene"):
        assert engines[eng]._env is not None
        assert engines[eng]._env["ARTIFACT_S3_BUCKET"] == "bkt"


def test_build_engines_no_artifact_s3_env_has_no_s3_keys(tmp_path: Path):
    # local（不给 artifact_s3）：env 里不含 S3 落点键（worker no-op 报 file://、零行为变化，ADR 0029）。
    nova_dir = tmp_path / "rid" / "nova-trajectories"
    engines = compose.build_engines(compose.repo_root(), nova_logs_dir=nova_dir)
    assert "ARTIFACT_S3_BUCKET" not in engines["novaact"]._env


# ---- engine_min_grace：按引擎给 grace 下限（ADR 0024 grace 硬约束）----
def test_engine_min_grace_nova_covers_act_timeout_plus_margin():
    # 断言语义关系而非重述公式（否则同义反复、测不出常量漂移）：Nova 下限须**严格大于**单 act 上界——
    # 才留得出会话释放余量（SIGTERM 落长 act 中途须等 act 有界返回才协作退释放会话，ADR 0024）。
    # 若 margin 误设为 0（违 ADR「grace 须留会话释放余量」红线），下限=act_timeout，此断言会红。
    g = compose.engine_min_grace("novaact")
    assert g > compose.NOVA_ACT_TIMEOUT_S, "Nova grace 下限须 > 单 act 上界（留会话释放余量）"
    assert compose.NOVA_GRACE_MARGIN_S > 0, "margin 须 > 0（ADR 0024 会话释放余量红线）"


def test_engine_min_grace_midscene_nonzero_covers_onsignal_budget():
    # Midscene 下限 = MIDSCENE_GRACE_MIN_S（非零）：onSignal 收尾路径超时预算之和须 < grace，否则 worker 被
    # SIGKILL、中断兜底 report 抢传截断（ADR 0024 grace 硬约束；曾为 0.0 致 midscene-only run grace 回落 5s < 上传 10s）。
    assert compose.engine_min_grace("midscene") == float(compose.MIDSCENE_GRACE_MIN_S)
    assert compose.engine_min_grace("midscene") > 0.0
    # 必须够 onSignal 最坏串行路径（会话 Stop + browser.close + 中断兜底上传超时），且 > Midscene 上传超时 10s。
    assert compose.MIDSCENE_GRACE_MIN_S >= 10


def test_engine_min_grace_unknown_engine_zero():
    # 未知引擎无下限（0.0）——保守：core enforce grace > 0 仍兜底。
    assert compose.engine_min_grace("unknown") == 0.0


def test_engine_min_grace_mixed_run_takes_max():
    # 混引擎 run 的 min_grace = 各引擎下限的 max（grace 是 run 级单值，__main__ 取 max）——Nova 下限最大、支配。
    legs = ["novaact", "midscene"]
    assert max(compose.engine_min_grace(e) for e in legs) == compose.engine_min_grace("novaact")
