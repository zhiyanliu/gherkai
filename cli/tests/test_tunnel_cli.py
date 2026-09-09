"""--expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。

「ngrok 真起得来 / 隧道 URL 真可达 / 浏览器真过 basic-auth」是真实边界，由真跑验证；
此处锁「接线 + 映射 + 生命周期交棒」的纯逻辑。
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import gherkai_cli.__main__ as m
from gherkai_core.model import JobResult, RunResult, Status
from gherkai_runtime import tunnel as gtunnel

INFO = gtunnel.TunnelInfo(url="https://t.ngrok-free.app", auth="u1:p1", pid=777,
                          local_origin="http://localhost:3000")


def _write_feature(tmp_path: Path) -> Path:
    f = tmp_path / "t.feature"
    f.write_text('Feature: t\n  Scenario: s\n    When "打开 http://localhost:3000/login"\n', encoding="utf-8")
    return f


def _patch_tunnel(monkeypatch, calls: list):
    class _Provider:
        def start(self, origin, **kw):
            calls.append(("start", origin))
            return INFO

    monkeypatch.setattr(gtunnel, "make_tunnel", lambda name: calls.append(("make", name)) or _Provider())
    monkeypatch.setattr(gtunnel, "stop_tunnel", lambda pid: calls.append(("stop", pid)))


def test_run_expose_local_maps_jobs_and_injects_headers(tmp_path, monkeypatch):
    """run --expose-local：job 文本中 origin 前缀 → 凭据内嵌隧道 URL；skip 头进 RunMeta（ADR 0035 决策 2/4）。"""
    calls, box = [], {}
    _patch_tunnel(monkeypatch, calls)

    def fake_schedule(run_meta, engines, sink, opts=None, on_job_complete=None, on_event=None):
        box["run_meta"] = run_meta
        results = [JobResult(job=j, status=Status.PASSED) for j in run_meta.jobs]
        return RunResult(run_meta=run_meta, status=Status.PASSED, jobs=results)

    monkeypatch.setattr(m, "schedule", fake_schedule)
    rc = m.main(["run", str(_write_feature(tmp_path)), "--no-report",
                 "--expose-local", "http://localhost:3000"])
    assert rc == 0
    meta = box["run_meta"]
    step = meta.jobs[0].scenarios[0].steps[0]
    assert "https://u1:p1@t.ngrok-free.app/login" in step.text  # 前缀替换 + 凭据内嵌
    assert "localhost:3000" not in step.text
    assert dict(meta.extra_http_headers) == {"ngrok-skip-browser-warning": "1"}
    assert ("make", "ngrok") in calls and ("start", "http://localhost:3000") in calls


def test_run_without_expose_local_zero_change(tmp_path, monkeypatch):
    """不给 --expose-local：不碰 tunnel 模块、meta 无 headers（默认路径零变化，ADR 0035 边界）。"""
    calls, box = [], {}
    _patch_tunnel(monkeypatch, calls)

    def fake_schedule(run_meta, engines, sink, opts=None, on_job_complete=None, on_event=None):
        box["run_meta"] = run_meta
        return RunResult(run_meta=run_meta, status=Status.PASSED,
                         jobs=[JobResult(job=j, status=Status.PASSED) for j in run_meta.jobs])

    monkeypatch.setattr(m, "schedule", fake_schedule)
    rc = m.main(["run", str(_write_feature(tmp_path)), "--no-report"])
    assert rc == 0
    assert calls == []
    assert box["run_meta"].extra_http_headers is None


def test_run_tunnel_failure_exits_2(tmp_path, monkeypatch, capsys):
    """隧道起不来（如 authtoken 缺失）→ 退 2「没开跑就被拒」，不产生引擎费用。"""
    def boom(name):
        raise gtunnel.TunnelError("ngrok 隧道未就绪…authtoken 未配置")

    monkeypatch.setattr(gtunnel, "make_tunnel", boom)
    rc = m.main(["run", str(_write_feature(tmp_path)), "--no-report",
                 "--expose-local", "http://localhost:3000"])
    assert rc == 2
    assert "authtoken" in capsys.readouterr().err


def test_submit_local_writes_tunnel_file_for_per_run_cleanup(tmp_path, monkeypatch):
    """local submit：tunnel.json 落 run 目录（pid 交棒给 per-run/接力收尾者，ADR 0035 决策 3）。"""
    calls = []
    _patch_tunnel(monkeypatch, calls)
    forked = []

    class _FakeProc:
        pid = 1

    monkeypatch.setattr(subprocess, "Popen", lambda cmd, **kw: forked.append(cmd) or _FakeProc())
    rc = m.main(["submit", str(_write_feature(tmp_path)),
                 "--report-dir", str(tmp_path / "reports"),
                 "--expose-local", "http://localhost:3000"])
    assert rc == 0
    run_dirs = [d for d in (tmp_path / "reports").iterdir() if d.is_dir()]
    assert len(run_dirs) == 1
    tj = json.loads((run_dirs[0] / "tunnel.json").read_text(encoding="utf-8"))
    assert tj["pid"] == 777 and tj["url"] == INFO.url
    assert any("_reconcile" in c for c in forked[0])  # per-run 照常 fork（它是收尾宿主）
    # definition 里的 URL 已替换（per-run/云端读回即隧道地址）
    meta = json.loads((run_dirs[0] / "run_meta.json").read_text(encoding="utf-8"))
    assert "u1:p1@t.ngrok-free.app" in json.dumps(meta, ensure_ascii=False)


def test_tunnel_watch_entry_wires_argparse_to_host_and_prints(monkeypatch, capsys):
    """_tunnel_watch 入口：argparse → tunnel_host.watch_run_and_stop_tunnel + 打印拆除原因。

    守护主体（轮询终态 / TTL 兜底）的逻辑归 runtime/tests/test_tunnel_host.py；此处只锁「皮传对参数」。
    """
    from gherkai_runtime import tunnel_host

    seen = {}

    def fake_watch(run_id, **kw):
        seen["run_id"] = run_id
        seen.update(kw)
        return "run 终态 passed"

    monkeypatch.setattr(tunnel_host, "watch_run_and_stop_tunnel", fake_watch)
    rc = m.main(["_tunnel_watch", "r1", "--tunnel-pid", "777", "--ttl", "1500",
                 "--ddb-table", "tbl", "--region", "us-east-1"])
    assert rc == 0
    assert seen["run_id"] == "r1" and seen["tunnel_pid"] == 777
    assert seen["runs_table"] == "tbl" and seen["ttl_s"] == 1500.0 and seen["region"] == "us-east-1"
    assert "run 终态 passed" in capsys.readouterr().out


def test_tunnel_watch_requires_explicit_ttl():
    """--ttl 无默认值（必给）：曾恒 1h 且无任何生产写入者、与 run 预算脱钩（ADR 0035 决策 3），不留幻影默认。"""
    import pytest

    with pytest.raises(SystemExit) as ei:
        m.main(["_tunnel_watch", "r1", "--tunnel-pid", "777", "--ddb-table", "tbl"])
    assert ei.value.code == 2


def test_plan_expose_local_annotates_not_replaces(tmp_path, capsys):
    """plan：显示替换前原始地址 + 标注将映射（零副作用不起隧道，ADR 0035 决策 2）。"""
    rc = m.main(["plan", str(_write_feature(tmp_path)), "--expose-local", "http://localhost:3000"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "http://localhost:3000" in captured.out  # 原始地址（替换前）
    assert "原始地址" in captured.err  # 标注在 stderr（诊断面）


def test_submit_rejects_nonpositive_tunnel_ttl_before_starting_tunnel(tmp_path, monkeypatch, capsys):
    """--tunnel-ttl <=0 → 退 2 且**没起隧道**（早拒才真零副作用，对齐 --grace 的入口校验惯例）。"""
    calls = []
    _patch_tunnel(monkeypatch, calls)
    rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud",
                 "--expose-local", "http://localhost:3000", "--tunnel-ttl", "0"])
    assert rc == 2
    assert calls == []  # 隧道一次都没起
    assert "--tunnel-ttl" in capsys.readouterr().err


def test_submit_rejects_nonfinite_tunnel_ttl(tmp_path, monkeypatch, capsys):
    """--tunnel-ttl nan/inf → 退 2（float() 会收下它们；nan 使守护的 monotonic()<deadline 首轮
    即 False → 隧道 submit 后立刻被拆——与 @timeout: 的 isfinite 校验同一理由）。"""
    calls = []
    _patch_tunnel(monkeypatch, calls)
    for bad in ("nan", "inf"):
        rc = m.main(["submit", str(_write_feature(tmp_path)), "--backend", "cloud",
                     "--expose-local", "http://localhost:3000", "--tunnel-ttl", bad])
        assert rc == 2, f"--tunnel-ttl {bad} 应被拒"
        assert calls == []  # 隧道一次都没起
        assert "--tunnel-ttl" in capsys.readouterr().err
