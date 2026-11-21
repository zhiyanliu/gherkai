"""definition 结构版本闸门在 CLI 的接线（ADR 0037 决策 7「definition 结构版本」段与「戳缺失」条的例外）：status / explain 读任何别的
东西之前先核结构版本，不等于本版本支持的即以退出码 2 结束并点名写端版本；云端只读 META 顶层两个属性。等待中的 status --wait 只拦别的
版本写出的 run，提交记录不存在或内容不合法的按期限读不出接着等待、可以被处置，处置之后按不带 --wait 的显示规则结束。本机后台推进进程用
自己生成的那份运行定义推进、不从记录读回，所以没有「读不到可用的运行定义」这一种情形。另有缺戳例外的接线：带设备目标或给了 --expose-local 的云端 submit 遇无版本戳的后端在资源检查之前以退出码 2 结束。"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gherkai_cli import __main__ as m
from gherkai_core.adapters.run_store.local import LocalRunStore
from gherkai_core.model import Status
from gherkai_core.serialize import DEFINITION_SCHEMA_VERSION
from gherkai_runtime import detached

from _inline_children import inline_children  # noqa: F401 —— 夹具：本机 submit 启动的后台推进进程在线程里执行
from test_backend_cloud import _patch_cloud_handles, _write_feature
from test_main import _fake_schedule_factory, advanced  # noqa: F401 —— advanced 是夹具


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
    进程中途被结束），执行中的 job 也就没有点名判定明细。返回运行态文件的路径。"""
    path = reports / run_id / "run_state.json"
    st = json.loads(path.read_text(encoding="utf-8"))
    st["status"] = "running"
    st["detached"] = True
    st.pop("ended_at", None)
    for job in st["jobs"]:
        job["status"] = "running"
        job.pop("result_id", None)
    path.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    return path


def _drop_a_target_key(reports: Path, run_id: str) -> None:
    """同版本下的形态违约：真的从 run_meta.json 删掉一个 job 的 target 键。"""
    path = reports / run_id / "run_meta.json"
    d = json.loads(path.read_text(encoding="utf-8"))
    d["jobs"][0].pop("target")
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


@pytest.mark.parametrize("damage", ["newer-schema", "not-json", "deleted"])
def test_background_advancer_advances_the_definition_it_generated_without_reading_it_back(tmp_path, monkeypatch, capsys,
                                                                                         inline_children, advanced, damage):
    """本机后台推进进程用自己生成的那份运行定义推进，不从记录读回（ADR 0035 决策 3「本机 `submit`」）：建 run 之后记录里的运行定义被
    改成更新的结构版本、写坏或删去，它照常回报建成，交给推进的仍是写下时的那一份，运行态不被改写成结束。"""
    reports = tmp_path / "reports"
    real_assemble = detached.assemble_local_run
    written: list = []

    def assemble_then_damage(meta, report_dir, **kw):
        parts = real_assemble(meta, report_dir, **kw)
        written.append(LocalRunStore(reports).load_run_meta(meta.run_id))  # 建 run 写下的那一份
        path = reports / meta.run_id / "run_meta.json"
        if damage == "newer-schema":
            _rewrite_schema(reports, meta.run_id, DEFINITION_SCHEMA_VERSION + 1)
        elif damage == "not-json":
            path.write_text("{", encoding="utf-8")
        else:
            path.unlink()
        return parts

    monkeypatch.setattr(detached, "assemble_local_run", assemble_then_damage)
    assert m.main(["submit", str(_write_feature(tmp_path)), "--report-dir", str(reports)]) == 0
    inline_children.settle()
    [meta] = written
    assert capsys.readouterr().out == f"{meta.run_id}\n"
    assert inline_children.only().returncode == 0 and advanced == [meta]
    state = LocalRunStore(reports).load_run_state(meta.run_id)
    assert (state.status, state.message, state.ended_at) == (Status.PENDING, None, None)


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
    谓词本身在 compose（run_requires_backend_stamp），此处 patch 它来验接线：它收到的是这次 run 的 job 与有没有给 --expose-local。"""
    record: list = []
    _, _, preflight_calls = _patch_cloud_handles(monkeypatch, record)
    monkeypatch.setattr(m.compose, "read_backend_version", lambda **kw: None)        # 无戳
    monkeypatch.setattr(m.compose, "check_version_skew", _real_check_version_skew)  # 验真判据，不用 _patch_skew 的假判定
    asked: list = []

    def requires(answer: bool):
        def predicate(jobs, *, tunneled):
            asked.append(([j.scope_id for j in jobs], tunneled))
            return answer
        return predicate

    monkeypatch.setattr(m.compose, "run_requires_backend_stamp", requires(True))
    argv = ["submit", str(_write_feature(tmp_path)), "--backend", "cloud", "--region", "us-east-1"]
    assert m.main(argv) == 2
    err = capsys.readouterr().err
    assert "没有版本戳" in err and "gherkai deploy" in err
    assert preflight_calls == []
    monkeypatch.setattr(m.compose, "run_requires_backend_stamp", requires(False))
    assert m.main(argv) == 0
    assert "没有版本戳" in capsys.readouterr().err   # 只警告
    assert len(preflight_calls) == 1
    assert len(asked) == 2 and all(scopes and tunneled is False for scopes, tunneled in asked)


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


def _release_on_the_second_poll(monkeypatch, lock_holder) -> list:
    """把等待中的轮询间隔换成不真等的函数：第二次轮询时放开 seed 那次 run 留下的锁（等于执行它的进程已退出）。"""
    import time as _time

    polls: list = []

    def sleep(s):
        polls.append(s)
        if len(polls) == 2:
            lock_holder.close_all()

    monkeypatch.setattr(_time, "sleep", sleep)
    return polls


def test_status_wait_settles_a_run_with_a_contract_violating_definition_and_then_shows_like_status(
        tmp_path, monkeypatch, capsys, lock_holder):
    """`status --wait` 遇到同版本下形态违约的提交记录（不是别的版本写出，这里是一个 job 少了 target 键）：期限读不出、只凭锁，说明一次
    之后接着等待；执行它的进程退出（锁放开）即处置，先说已记为已结束、报告没有生成，再按不带 --wait 的 status 的显示规则显示：显示只核
    提交记录的头，头读得出，所以照常显示终态、以 1 结束，不打回溯（ADR 0054 决策八「等待中的 status --wait」）。"""
    reports, run_id = _seed_local_run(tmp_path, monkeypatch)
    capsys.readouterr()
    _drop_a_target_key(reports, run_id)
    _as_detached_run_in_progress(reports, run_id)
    report = (reports / run_id / "index.html").read_bytes()  # seed 那次前台 run 结束时写的报告
    polls = _release_on_the_second_poll(monkeypatch, lock_holder)
    assert m.main(["status", run_id, "--wait", "--report-dir", str(reports)]) == 1
    cap = capsys.readouterr()
    lines = cap.err.splitlines()
    assert "Traceback" not in cap.err and polls == [1.0, 1.0]
    assert lines[0].startswith(f"run {run_id} 的提交记录不完整或形态不对，不知道它允许运行到什么时候")
    assert lines[1].startswith(f"本命令已把 run {run_id} 记为已结束：执行它的 gherkai 进程已退出；报告没有生成：")
    assert not any(ln.startswith("报告:") for ln in lines)  # 报告没有生成：不给报告的位置
    assert cap.out.splitlines()[0] == f"run {run_id}: aborted"
    state = LocalRunStore(reports).load_run_state(run_id)
    assert (state.status, state.message) == (Status.ABORTED, "执行这个 run 的 gherkai 进程已退出（已记为已结束）")
    assert (reports / run_id / "index.html").read_bytes() == report  # 运行定义读不出：处置没有生成新的报告


@pytest.mark.parametrize("damage, told, shown", [("not-json", "提交记录不完整或形态不对", 2), ("deleted", "提交记录不存在", 1)])
def test_status_wait_settles_a_run_whose_definition_is_unreadable_or_gone(tmp_path, monkeypatch, capsys, lock_holder,
                                                                          damage, told, shown):
    """提交记录不是合法 JSON，或已被删去：不是别的版本写出，期限读不出、只凭锁；等待中说明一次，执行它的进程退出即处置。之后显示时
    沿用不带 --wait 的 status 的规则：提交记录不完整的以 2 结束，不存在的照常显示、按终态（aborted）以 1 结束。不出现读写记录失败的那一句、
    不打回溯，报告没有生成。"""
    reports, run_id = _seed_local_run(tmp_path, monkeypatch)
    capsys.readouterr()
    _as_detached_run_in_progress(reports, run_id)
    path = reports / run_id / "run_meta.json"
    if damage == "not-json":
        path.write_text("{", encoding="utf-8")
    else:
        path.unlink()
    _release_on_the_second_poll(monkeypatch, lock_holder)
    assert m.main(["status", run_id, "--wait", "--report-dir", str(reports)]) == shown
    err = capsys.readouterr().err
    assert "Traceback" not in err and "读写" not in err
    assert err.splitlines()[0].startswith(f"run {run_id} 的{told}，不知道它允许运行到什么时候")
    assert "报告没有生成" in err.splitlines()[1]
    assert LocalRunStore(reports).load_run_state(run_id).status is Status.ABORTED

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
