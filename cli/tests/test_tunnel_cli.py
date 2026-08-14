"""--expose-local 的 CLI 接线测试（ADR 0035）：fake tunnel provider——不真起 ngrok、不连 AWS。

「ngrok 真起得来 / 隧道 URL 真可达 / 浏览器真过 basic-auth」是真实边界，由真跑验证；
此处锁「接线 + 映射 + 生命周期交棒」的纯逻辑。
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import cli.__main__ as m
from core.model import JobResult, RunResult, Status
from gherkai import tunnel as gtunnel

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
    """隧道起不来（如 authtoken 缺失）→ 退 2「没开跑就被拒」，不烧引擎钱。"""
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


def test_tunnel_watch_stops_on_terminal_state(monkeypatch):
    """_tunnel_watch 守护：轮询到 run 终态 → 拆隧道退出（ADR 0035 决策 3 cloud 档）。"""
    stopped = []

    class _StateTable:
        def get_item(self, **kw):
            return {"Item": {"run_id": "r1", "item_type": "STATE", "status": "passed", "jobs": {}}}

    monkeypatch.setattr(m.compose, "_make_ddb_table", lambda t, *, region, profile: _StateTable())
    monkeypatch.setattr(gtunnel, "stop_tunnel", lambda pid: stopped.append(pid))
    import time as _t

    monkeypatch.setattr(_t, "sleep", lambda s: None)
    rc = m.main(["_tunnel_watch", "r1", "--tunnel-pid", "777",
                 "--ddb-table", "tbl", "--region", "us-east-1"])
    assert rc == 0 and stopped == [777]


def test_tunnel_watch_ttl_fallback(monkeypatch):
    """run 永不终态（查询一直异常）→ TTL 到点拆隧道自杀（防 ngrok 进程泄漏）。"""
    stopped = []

    class _BoomTable:
        def get_item(self, **kw):
            raise RuntimeError("ddb down")

    monkeypatch.setattr(m.compose, "_make_ddb_table", lambda t, *, region, profile: _BoomTable())
    monkeypatch.setattr(gtunnel, "stop_tunnel", lambda pid: stopped.append(pid))
    import time as _t

    monkeypatch.setattr(_t, "sleep", lambda s: None)
    clock = {"t": 0.0}

    def mono():
        clock["t"] += 400.0
        return clock["t"]

    monkeypatch.setattr(_t, "monotonic", mono)
    rc = m.main(["_tunnel_watch", "r1", "--tunnel-pid", "777",
                 "--ddb-table", "tbl", "--region", "us-east-1", "--ttl", "600"])
    assert rc == 0 and stopped == [777]


def test_plan_expose_local_annotates_not_replaces(tmp_path, capsys):
    """plan：显示替换前原始地址 + 标注将映射（零副作用不起隧道，ADR 0035 决策 2）。"""
    rc = m.main(["plan", str(_write_feature(tmp_path)), "--expose-local", "http://localhost:3000"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "http://localhost:3000" in captured.out  # 原始地址（替换前）
    assert "原始地址" in captured.err  # 标注在 stderr（诊断面）
