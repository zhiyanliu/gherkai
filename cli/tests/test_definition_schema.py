"""definition 结构版本闸门在 CLI 的接线（ADR 0037 决策 7「definition 结构版本」段与「戳缺失」条的例外）：status / explain / 本机
接力读任何别的东西之前先核结构版本，不等于本版本支持的即以退出码 2 结束并点名写端版本；云端只读 META 顶层两个属性。本机后台推进进程读
不到可用的运行定义时另以结束写的 error 变体结束 run，接力不写。另有缺戳例外的接线：带设备目标或会话预热地址的云端 submit 遇无版本戳的
后端在资源检查之前以退出码 2 结束。"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gherkai_cli import __main__ as m
from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.model import Status
from gherkai_core.run_status import DEFINITION_CONTRACT_REASON, schema_mismatch_reason
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


def _as_detached_run_in_progress(reports: Path, run_id: str) -> Path:
    """把前台 run 产出的 seed 改成 submit 提交、推进到一半的形态：带后台执行的标记，run 与各 job 都在执行、没有结束时刻（模拟后台推进
    进程中途被结束）。后台推进进程与接力只对这种 run 动作。返回运行态文件的路径。"""
    path = reports / run_id / "run_state.json"
    st = json.loads(path.read_text(encoding="utf-8"))
    st["status"] = "running"
    st["detached"] = True
    st.pop("ended_at", None)
    for job in st["jobs"]:
        job["status"] = "running"
    path.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    return path


def _drop_a_target_key(reports: Path, run_id: str) -> None:
    """同版本下的形态违约：真的从 run_meta.json 删掉一个 job 的 target 键。"""
    path = reports / run_id / "run_meta.json"
    d = json.loads(path.read_text(encoding="utf-8"))
    d["jobs"][0].pop("target")
    path.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")


def _assert_ended_by_the_definition_unavailable_ending(reports: Path, run_id: str, reason: str) -> None:
    """run 与每个 job 都记 error，run 级说明与 job 级说明都是这句原因，带结束时刻。"""
    state = LocalRunStore(reports).load_run_state(run_id)
    assert (state.status, state.message) == (Status.ERROR, reason)
    assert state.jobs and all((js.status, js.message) == (Status.ERROR, reason) for js in state.jobs.values())
    assert state.ended_at is not None


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


def test_background_advancer_ends_the_run_with_the_error_ending_on_a_schema_mismatch(tmp_path, monkeypatch, capsys):
    """后台推进进程（submit 启动的那个）读到结构版本不符的提交记录：它是这个 run 的推进器，以结束写的 error 变体结束 run，原因是与
    云端推进器同一句；随后在日志里打印命令行的那一句、以退出码 2 结束，不是裸 traceback。"""
    reports, run_id = _seed_local_run(tmp_path, monkeypatch)
    _rewrite_schema(reports, run_id, DEFINITION_SCHEMA_VERSION + 1)
    _as_detached_run_in_progress(reports, run_id)
    assert m.main(["_reconcile", run_id, "--report-dir", str(reports)]) == 2
    err = capsys.readouterr().err
    assert "更新版本" in err
    assert f"run {run_id} 已结束：这个 run 与还没有结束的 job 记为 error，原因写进了运行状态。" in err
    _assert_ended_by_the_definition_unavailable_ending(
        reports, run_id, schema_mismatch_reason(DEFINITION_SCHEMA_VERSION + 1, DEFINITION_SCHEMA_VERSION, "9.9.0"))


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
    """缺戳例外的接线：谓词为真的云端 submit 遇无版本戳后端以退出码 2 结束、资源检查一次不做；谓词为假（纯桌面）只警告放行。
    谓词本身在 compose（run_requires_backend_stamp），此处 patch 它来验接线。"""
    record: list = []
    _, _, preflight_calls = _patch_cloud_handles(monkeypatch, record)
    monkeypatch.setattr(m.compose, "read_backend_version", lambda **kw: None)        # 无戳
    monkeypatch.setattr(m.compose, "check_version_skew", _real_check_version_skew)  # 验真判据，不用 _patch_skew 的假判定
    monkeypatch.setattr(m.compose, "run_requires_backend_stamp", lambda meta: True)
    argv = ["submit", str(_write_feature(tmp_path)), "--backend", "cloud", "--region", "us-east-1"]
    assert m.main(argv) == 2
    err = capsys.readouterr().err
    assert "没有版本戳" in err and "gherkai deploy" in err
    assert preflight_calls == []
    monkeypatch.setattr(m.compose, "run_requires_backend_stamp", lambda meta: False)
    assert m.main(argv) == 0
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


def test_local_relay_reports_contract_violation_with_exit_2_instead_of_traceback(tmp_path, monkeypatch, capsys):
    """`status --wait` 接力读到同版本下形态违约的提交记录：以退出码 2 结束并说明，不是裸 traceback；运行态不动，不写 run 级说明
    （ADR 0037 决策 7「definition 结构版本」段，ADR 0031 决定三「结束写」小节「运行定义不可用时」条）。接力不是这个 run 的推进器：
    读不懂可能只是本机的版本不同，原来的后台推进进程可能仍在正常推进。"""
    reports, run_id = _seed_local_run(tmp_path, monkeypatch)
    _drop_a_target_key(reports, run_id)
    state_path = _as_detached_run_in_progress(reports, run_id)
    before = state_path.read_text(encoding="utf-8")
    assert m.main(["status", run_id, "--wait", "--report-dir", str(reports)]) == 2
    err = capsys.readouterr().err
    assert "提交记录不完整" in err and "target" in err
    assert state_path.read_text(encoding="utf-8") == before


def test_background_advancer_ends_the_run_with_the_error_ending_on_contract_violation(tmp_path, monkeypatch, capsys):
    """后台推进进程读到同版本下形态违约的提交记录：以结束写的 error 变体结束 run，与云端推进器同一写法（ADR 0037 决策 7「definition
    结构版本」段，ADR 0031 决定三「结束写」小节「运行定义不可用时」条）：执行中的 job 一并记 error，说明是产品语言的那一句，不带契约
    异常的原文；随后拆隧道，在日志里打印带原文的那一句、以退出码 2 结束。这一写不生成报告：报告文件一个字节不变。"""
    from gherkai_runtime import tunnel as gtunnel

    reports, run_id = _seed_local_run(tmp_path, monkeypatch)
    _drop_a_target_key(reports, run_id)
    _as_detached_run_in_progress(reports, run_id)
    (reports / run_id / "tunnel.json").write_text('{"pid": 4545}', encoding="utf-8")
    stopped: list[int] = []
    monkeypatch.setattr(gtunnel, "stop_tunnel", lambda pid: stopped.append(pid))
    report_files = {name: (reports / run_id / name).read_bytes() for name in ("index.html", "manifest.json")}

    assert m.main(["_reconcile", run_id, "--report-dir", str(reports)]) == 2
    err = capsys.readouterr().err
    assert "提交记录不完整" in err and "target" in err
    assert f"run {run_id} 已结束：这个 run 与还没有结束的 job 记为 error，原因写进了运行状态。" in err
    _assert_ended_by_the_definition_unavailable_ending(reports, run_id, DEFINITION_CONTRACT_REASON)
    assert stopped == [4545] and not (reports / run_id / "tunnel.json").exists()
    assert {name: (reports / run_id / name).read_bytes() for name in report_files} == report_files


@pytest.mark.parametrize("argv_head", [["status"], ["status", "--wait"], ["explain"]], ids=["status", "status-wait", "explain"])
def test_header_stage_contract_violation_exits_2_and_leaves_the_run_untouched(tmp_path, monkeypatch, capsys, argv_head):
    """读头阶段的形态违约（结构版本字段不是整数）：三个本机读端都以退出码 2 结束并说明，不是裸异常；运行态不被改动、不写 run 级消息
    （本机读端有退出码可交）。"""
    reports, run_id = _seed_local_run(tmp_path, monkeypatch)
    _rewrite_schema(reports, run_id, True)
    before = (reports / run_id / "run_state.json").read_text(encoding="utf-8")
    cmd, *rest = argv_head
    assert m.main([cmd, run_id, *rest, "--report-dir", str(reports)]) == 2
    assert "提交记录不完整" in capsys.readouterr().err
    assert (reports / run_id / "run_state.json").read_text(encoding="utf-8") == before


def test_cloud_status_and_explain_report_header_contract_violation_with_exit_2(monkeypatch, capsys):
    """云端两个读端读 META 头时的形态违约（结构版本字段不是整数）：以退出码 2 结束并说明，不是裸异常；之后不再读运行态。"""
    reads: list = []

    class _Table:
        def get_item(self, **kw):
            reads.append(kw["Key"]["item_type"])
            if kw["Key"]["item_type"] == "META":
                return {"Item": {"run_id": "r1", "item_type": "META", "schema_version": True, "cli_version": "1.5.0"}}
            raise AssertionError("头读不出来时不该再读运行态")

    _patch_cloud_handles(monkeypatch, [])
    monkeypatch.setattr(m.compose, "_make_ddb_table", lambda table, *, region, profile: _Table())
    for argv in (["status", "r1", "--backend", "cloud", "--region", "us-east-1"], ["explain", "r1", "--backend", "cloud", "--region", "us-east-1"]):
        reads.clear()
        assert m.main(argv) == 2
        assert "提交记录不完整" in capsys.readouterr().err and reads == ["META"]
