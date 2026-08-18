"""tunnel_host 单测（ADR 0035 决策 3）：隧道宿主编排——起隧道+映射、TTL 算法、守护循环。

绿即够的边界（CLAUDE.md「绿≠对·别过度」）：TTL 是纯算术、起隧道/守护循环用 fake provider 与 fake DDB
覆盖「接线 + 终态判定 + TTL 兜底」逻辑。真实边界（ngrok 真起得来、隧道真可达、agent 真脱离进程组）
分别由真跑与 `test_tunnel.py::test_ngrok_agent_detaches_from_cli_process_group`（真 spawn）覆盖。
"""
from __future__ import annotations

from core.model import Job, RunState, Scenario, Status, Step
from gherkai import compose, tunnel_host
from gherkai import tunnel as gtunnel

INFO = gtunnel.TunnelInfo(url="https://t.ngrok-free.app", auth="u1:p1", pid=4242,
                          local_origin="http://localhost:3000")


def _job(scope_id: str, timeout_s: float | None) -> Job:
    return Job(scope_id=scope_id, scope_name=scope_id, engine="midscene", timeout_s=timeout_s,
               scenarios=(Scenario(id=f"{scope_id}:1", name="sc",
                                   steps=(Step(0, "Given", '打开 "http://localhost:3000/a"'),)),))


# ---- start_tunnel_for_jobs：起隧道 → 映射 definition → 恒注入 header（决策 1/2/4）----

def test_start_tunnel_for_jobs_maps_and_injects_headers(monkeypatch):
    calls = []

    class _Provider:
        def start(self, origin, **kw):
            calls.append(origin)
            return INFO

    monkeypatch.setattr(gtunnel, "make_tunnel", lambda name: calls.append(name) or _Provider())
    jobs = [_job("s1", 300.0)]
    setup = tunnel_host.start_tunnel_for_jobs(jobs, local_origin="http://localhost:3000")
    assert calls == ["ngrok", "http://localhost:3000"]
    assert setup.info is INFO
    assert setup.extra_http_headers == {"ngrok-skip-browser-warning": "1"}
    # 映射后是新 Job（definition 不可变）：原 jobs 不动
    assert setup.jobs[0].scenarios[0].steps[0].text == '打开 "https://u1:p1@t.ngrok-free.app/a"'
    assert jobs[0].scenarios[0].steps[0].text == '打开 "http://localhost:3000/a"'


def test_start_tunnel_for_jobs_propagates_tunnel_error(monkeypatch):
    """provider 起不来 → TunnelError 直接冒给调用方（皮归「没开跑就被拒」退 2，不在本层吞成哨兵）。"""
    import pytest

    def boom(name):
        raise gtunnel.TunnelError("authtoken 未配置")

    monkeypatch.setattr(gtunnel, "make_tunnel", boom)
    with pytest.raises(gtunnel.TunnelError, match="authtoken"):
        tunnel_host.start_tunnel_for_jobs([_job("s1", 300.0)], local_origin="http://localhost:3000")


# ---- compute_watch_ttl_s：TTL 按 definition 算（不是拍一个常数）----

def test_ttl_sums_job_budgets_plus_margin():
    """Σ(各 job 预算) + 启动余量——cloud 档并发恒 1（ADR 0034），求和是保守上界。"""
    jobs = [_job("a", 300.0), _job("b", 600.0), _job("c", 120.0)]
    assert tunnel_host.compute_watch_ttl_s(jobs, startup_margin_s=900.0) == 900.0 + 1020.0


def test_ttl_scales_past_the_old_fixed_hour():
    """本条锁住被修的病根：12 个默认预算（300s）的 job 已超旧的恒定 1h TTL——TTL 必须随 definition 涨，
    否则守护会在 run 还在跑时拆隧道，剩余 job 以「AI 报导航失败」的假失败告终（ADR 0035 决策 3）。"""
    jobs = [_job(f"s{i}", 300.0) for i in range(12)]
    assert tunnel_host.compute_watch_ttl_s(jobs) > 3600.0


def test_ttl_gives_unbounded_jobs_an_explicit_ceiling():
    """`--default-job-timeout <=0`（执行侧不超时）→ job.timeout_s=None：TTL 仍须有限（否则泄漏兜底失效）。"""
    ttl = tunnel_host.compute_watch_ttl_s([_job("a", None), _job("b", None)],
                                          startup_margin_s=0.0, unbounded_job_budget_s=1000.0)
    assert ttl == 2000.0


def test_ttl_empty_definition_is_just_the_margin():
    assert tunnel_host.compute_watch_ttl_s([], startup_margin_s=900.0) == 900.0


# ---- watch_run_and_stop_tunnel：轮询终态即拆 / TTL 兜底自杀 ----

def _patch_run_store(monkeypatch, states):
    """把 compose._make_ddb_table 换成吐固定 RunState 序列的 fake（states 用尽后复用最后一个）。"""
    seq = list(states)

    class _FakeStore:
        def load_run_state(self, run_id):
            got = seq.pop(0) if len(seq) > 1 else seq[0]
            if isinstance(got, Exception):
                raise got
            return got

    monkeypatch.setattr(compose, "_make_ddb_table", lambda t, *, region, profile: object())
    monkeypatch.setattr("core.adapters.run_store.ddb.DynamoDBRunStore", lambda table: _FakeStore())


def _state(status: Status) -> RunState:
    return RunState(run_id="r1", status=status, jobs={}, high_water_mark=0)


def test_watch_stops_tunnel_on_terminal_state(monkeypatch):
    stopped = []
    monkeypatch.setattr(gtunnel, "stop_tunnel", lambda pid: stopped.append(pid))
    monkeypatch.setattr(compose, "resolve_region", lambda r, p: r)
    _patch_run_store(monkeypatch, [_state(Status.RUNNING), _state(Status.PASSED)])
    import time as _t

    monkeypatch.setattr(_t, "sleep", lambda s: None)
    reason = tunnel_host.watch_run_and_stop_tunnel(
        "r1", tunnel_pid=777, runs_table="tbl", ttl_s=600.0, region="us-east-1")
    assert stopped == [777] and "passed" in reason


def test_watch_ttl_fallback_when_run_never_settles(monkeypatch):
    """读库一直异常（run 卡死/查询异常）→ 不致命、继续轮询，TTL 到点拆隧道自杀（防 ngrok 泄漏）。"""
    stopped, warned = [], []
    monkeypatch.setattr(gtunnel, "stop_tunnel", lambda pid: stopped.append(pid))
    monkeypatch.setattr(compose, "resolve_region", lambda r, p: r)
    _patch_run_store(monkeypatch, [RuntimeError("ddb down")])
    import time as _t

    monkeypatch.setattr(_t, "sleep", lambda s: None)
    clock = {"t": 0.0}

    def mono():
        clock["t"] += 400.0
        return clock["t"]

    monkeypatch.setattr(_t, "monotonic", mono)
    reason = tunnel_host.watch_run_and_stop_tunnel(
        "r1", tunnel_pid=777, runs_table="tbl", ttl_s=600.0, region="us-east-1",
        on_warn=warned.append)
    assert stopped == [777] and "TTL" in reason
    assert warned and "读 run 状态失败" in warned[0]  # 诊断经 on_warn 交给皮打印
