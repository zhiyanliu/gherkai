"""definition 结构版本闸门（ADR 0037 决策 7）在 CLI 的接线：status / explain / 本机接力读任何别的东西之前先核结构版本，
不等于本版本支持的即以退出码 2 结束并点名写端版本；云端只读 META 顶层两个属性。另有缺戳例外的接线：带设备目标或会话预热地址的
run 遇无版本戳的后端在资源检查之前以退出码 2 结束。"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gherkai_cli import __main__ as m
from gherkai_core.serialize import DEFINITION_SCHEMA_VERSION

from test_backend_cloud import _patch_cloud_handles, _write_feature
from test_main import _fake_schedule_factory


def _seed_local_run(tmp_path: Path, monkeypatch) -> tuple[Path, str]:
    """用假 schedule 真实执行一次本机 run，落下结构版本 1 的 run_meta.json；返回 (报告目录, run_id)。"""
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    reports = tmp_path / "reports"
    assert m.main(["run", str(_write_feature(tmp_path)), "--report-dir", str(reports), "--quiet"]) == 0
    run_dir = next(d for d in reports.iterdir() if d.is_dir())
    return reports, run_dir.name


def _rewrite_schema(reports: Path, run_id: str, version, cli_version="9.9.0") -> None:
    path = reports / run_id / "run_meta.json"
    d = json.loads(path.read_text(encoding="utf-8"))
    if version is None:
        d.pop("schema_version")
    else:
        d["schema_version"] = version
    d["cli_version"] = cli_version
    path.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")


def test_fresh_run_writes_current_schema_and_status_explain_read_it(tmp_path, monkeypatch, capsys):
    reports, run_id = _seed_local_run(tmp_path, monkeypatch)
    d = json.loads((reports / run_id / "run_meta.json").read_text(encoding="utf-8"))
    assert d["schema_version"] == DEFINITION_SCHEMA_VERSION and "cli_version" in d and d["session_warmup_url"] is None
    assert m.main(["status", run_id, "--report-dir", str(reports)]) == 0
    assert m.main(["explain", run_id, "--report-dir", str(reports)]) == 0


@pytest.mark.parametrize("cmd", ["status", "explain"])
def test_newer_schema_exits_2_naming_writer_and_upgrade(tmp_path, monkeypatch, capsys, cmd):
    reports, run_id = _seed_local_run(tmp_path, monkeypatch)
    _rewrite_schema(reports, run_id, DEFINITION_SCHEMA_VERSION + 1)
    import gherkai_runtime.detached as detached

    def boom(*a, **k):
        raise AssertionError("结构版本不符时不该接力推进")

    monkeypatch.setattr(detached, "drive_local_reconcile", boom)
    argv = [cmd, run_id, "--report-dir", str(reports)] + (["--wait"] if cmd == "status" else [])
    assert m.main(argv) == 2
    err = capsys.readouterr().err
    assert "gherkai 9.9.0" in err and "更新版本" in err and "uv tool upgrade gherkai" in err
    assert f"第 {DEFINITION_SCHEMA_VERSION + 1} 版" in err and f"第 {DEFINITION_SCHEMA_VERSION} 版" in err


@pytest.mark.parametrize("version", [None, 0], ids=["missing-key", "zero"])
def test_older_schema_exits_2_pointing_at_the_writer_version(tmp_path, monkeypatch, capsys, version):
    reports, run_id = _seed_local_run(tmp_path, monkeypatch)
    _rewrite_schema(reports, run_id, version, cli_version="1.4.9")
    assert m.main(["status", run_id, "--report-dir", str(reports)]) == 2
    err = capsys.readouterr().err
    assert "更早版本" in err and "gherkai==1.4.9" in err and "重新提交" in err


def test_reconcile_entry_reports_schema_mismatch_instead_of_traceback(tmp_path, monkeypatch, capsys):
    reports, run_id = _seed_local_run(tmp_path, monkeypatch)
    _rewrite_schema(reports, run_id, DEFINITION_SCHEMA_VERSION + 1)
    assert m.main(["_reconcile", run_id, "--report-dir", str(reports)]) == 2
    assert "更新版本" in capsys.readouterr().err


def test_cloud_status_and_explain_peek_meta_header_before_state(monkeypatch, capsys):
    """云端只读 META 顶层两个属性（投影），不等于本版本即退出码 2；之后不再读 STATE。"""
    reads: list = []

    class _Table:
        def get_item(self, **kw):
            reads.append((kw["Key"]["item_type"], kw.get("ProjectionExpression")))
            if kw["Key"]["item_type"] == "META":
                return {"Item": {"run_id": "r1", "item_type": "META", "schema_version": DEFINITION_SCHEMA_VERSION + 1, "cli_version": "9.9.0"}}
            raise AssertionError("结构版本不符时不该再读运行态")

    record: list = []
    _patch_cloud_handles(monkeypatch, record)
    monkeypatch.setattr(m.compose, "_make_ddb_table", lambda table, *, region, profile: _Table())
    assert m.main(["status", "r1", "--backend", "cloud", "--region", "us-east-1"]) == 2
    assert "gherkai 9.9.0" in capsys.readouterr().err
    assert reads == [("META", "#sv, #cv")]
    reads.clear()
    assert m.main(["explain", "r1", "--backend", "cloud", "--region", "us-east-1"]) == 2
    assert "gherkai 9.9.0" in capsys.readouterr().err and reads == [("META", "#sv, #cv")]


def test_missing_stamp_blocks_runs_that_require_it_before_resource_preflight(tmp_path, monkeypatch, capsys):
    """缺戳例外的接线：谓词为真的 run / submit 遇无版本戳后端以退出码 2 结束、资源检查一次不做；谓词为假（纯桌面）只警告放行。
    谓词本身在 compose（run_requires_backend_stamp），此处 patch 它来验接线。"""
    record: list = []
    _, _, preflight_calls = _patch_cloud_handles(monkeypatch, record)
    monkeypatch.setattr(m.compose, "read_backend_version", lambda **kw: None)        # 无戳
    monkeypatch.setattr(m.compose, "check_version_skew", _real_check_version_skew)  # 验真判据，不用 _patch_skew 的假判定
    monkeypatch.setattr(m.compose, "run_requires_backend_stamp", lambda meta: True)
    monkeypatch.setattr(m, "schedule", _fake_schedule_factory())
    for cmd in ("run", "submit"):
        assert m.main([cmd, str(_write_feature(tmp_path)), "--backend", "cloud", "--region", "us-east-1", "--quiet"] if cmd == "run"
                      else [cmd, str(_write_feature(tmp_path)), "--backend", "cloud", "--region", "us-east-1"]) == 2
        err = capsys.readouterr().err
        assert "没有版本戳" in err and "gherkai deploy" in err
    assert preflight_calls == []
    monkeypatch.setattr(m.compose, "run_requires_backend_stamp", lambda meta: False)
    assert m.main(["run", str(_write_feature(tmp_path)), "--backend", "cloud", "--region", "us-east-1", "--quiet"]) == 0
    assert "没有版本戳" in capsys.readouterr().err   # 只警告
    assert len(preflight_calls) == 1


# `_patch_skew` 把 check_version_skew 换成了假的；缺戳例外要验真判据，取模块加载时的原函数
import gherkai_runtime.compose as _compose_mod  # noqa: E402

_real_check_version_skew = _compose_mod.check_version_skew


def test_schema_gate_runs_before_the_state_file_is_parsed(tmp_path, monkeypatch, capsys):
    """别的版本写出的 run 目录连运行态的形状都不保证：先核结构版本，再读运行态——否则「请升级」会变成一个解析异常。"""
    reports, run_id = _seed_local_run(tmp_path, monkeypatch)
    _rewrite_schema(reports, run_id, DEFINITION_SCHEMA_VERSION + 1)
    state = reports / run_id / "run_state.json"
    d = json.loads(state.read_text(encoding="utf-8"))
    d["status"] = "teleported"
    state.write_text(json.dumps(d), encoding="utf-8")
    for cmd in ("status", "explain"):
        assert m.main([cmd, run_id, "--report-dir", str(reports)]) == 2
        assert "更新版本" in capsys.readouterr().err
