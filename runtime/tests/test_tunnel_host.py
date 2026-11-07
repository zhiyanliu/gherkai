"""tunnel_host 单测（ADR 0035 决策 3）：隧道宿主编排——起隧道+映射、TTL 算法、守护循环。

绿即够的边界（CLAUDE.md「绿≠对·别过度」）：TTL 是纯算术、起隧道/守护循环用 fake provider 与 fake DDB
覆盖「接线 + 终态判定 + TTL 兜底」逻辑。真实边界（ngrok 真起得来、隧道真可达、agent 真脱离进程组）
分别由真实运行与 `test_tunnel.py::test_ngrok_agent_detaches_from_cli_process_group`（真 spawn）覆盖。
"""
from __future__ import annotations

from gherkai_core.model import Job, RunState, Scenario, Status, Step
from gherkai_runtime import compose, tunnel_host
from gherkai_runtime import tunnel as gtunnel

INFO = gtunnel.TunnelInfo(url="https://t.ngrok-free.app", pid=4242, local_origin="http://localhost:3000",
                          warmup_url="https://t.ngrok-free.app/.well-known/gherkai-tunnel-auth?gherkai_tunnel_token=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")


def _job(scope_id: str, timeout_s: float | None) -> Job:
    return Job(scope_id=scope_id, scope_name=scope_id, engine="midscene", timeout_s=timeout_s,
               scenarios=(Scenario(id=f"{scope_id}:1", name="sc",
                                   steps=(Step(0, "Given", '"http://localhost:3000/a"'),)),))


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
    token = INFO.warmup_url.rsplit("=", 1)[1]
    assert token not in repr(setup) and token not in str(setup)  # 令牌不进 repr（日志与异常里打印对象时不带出来）
    # 映射后是新 Job（definition 不可变）：原 jobs 不动；替换进文本的是干净的隧道地址，不内嵌凭据
    assert setup.jobs[0].scenarios[0].steps[0].text == '"https://t.ngrok-free.app/a"'
    assert jobs[0].scenarios[0].steps[0].text == '"http://localhost:3000/a"'


def test_start_tunnel_for_jobs_propagates_tunnel_error(monkeypatch):
    """provider 起不来 → TunnelError 直接冒给调用方（前端归「没开始执行就被拒」、退出码 2，不在本层吞成哨兵）。"""
    import pytest

    def boom(name):
        raise gtunnel.TunnelError("authtoken 未配置")

    monkeypatch.setattr(gtunnel, "make_tunnel", boom)
    with pytest.raises(gtunnel.TunnelError, match="authtoken"):
        tunnel_host.start_tunnel_for_jobs([_job("s1", 300.0)], local_origin="http://localhost:3000")


# ---- compute_watch_ttl_s：TTL 按 definition 算（不是拍一个常数）----

def test_ttl_sums_job_budgets_plus_margin():
    """一次性余量 + Σ(各 job 预算 + 每 job 余量)——求和对任何并发取值都是保守上界（ADR 0034 机制四）。"""
    jobs = [_job("a", 300.0), _job("b", 600.0), _job("c", 120.0)]
    assert tunnel_host.compute_watch_ttl_s(jobs, startup_margin_s=900.0, per_job_margin_s=210.0) == (
        900.0 + 1020.0 + 3 * 210.0)


def test_ttl_default_margins_follow_the_documented_formula():
    """缺省取值下 TTL 为 900 + Σ(各 job 预算) + N × 210（ADR 0035 决策 3）：每 job 的 210 秒由调度精度 60、
    Fargate 停止宽限上限 120、事件链尾延迟 30 组成，停止宽限与云端同步 run 的停止后等待预算同用一个平台上限常量。"""
    assert tunnel_host.CLOUD_STARTUP_MARGIN_S == 900.0
    assert tunnel_host.CLOUD_PER_JOB_MARGIN_S == 210.0
    assert tunnel_host.CLOUD_PER_JOB_MARGIN_S == 60.0 + compose.FARGATE_STOP_TIMEOUT_MAX_S + 30.0
    jobs = [_job("a", 300.0), _job("b", 600.0)]
    assert tunnel_host.compute_watch_ttl_s(jobs) == 900.0 + 900.0 + 2 * 210.0


def test_ttl_per_job_margin_grows_with_job_count():
    """每多一个 job，TTL 多出它的预算再加一份每 job 余量：并发为 1 时用尽预算被停止的 job 各带一段尾部耗时，
    5 个这样的 job 的尾部（5 × 210 = 1050 秒）就超过一次性的 900 秒，余量不随 job 数增长时 TTL 会先到（ADR 0035 决策 3）。"""
    four = [_job(f"s{i}", 300.0) for i in range(4)]
    five = four + [_job("s4", 300.0)]
    assert tunnel_host.compute_watch_ttl_s(five) - tunnel_host.compute_watch_ttl_s(four) == (
        300.0 + tunnel_host.CLOUD_PER_JOB_MARGIN_S)
    tail = 5 * tunnel_host.CLOUD_PER_JOB_MARGIN_S
    assert tail > tunnel_host.CLOUD_STARTUP_MARGIN_S  # 只留一次性余量时，这 5 个 job 的尾部已超出它
    assert tunnel_host.compute_watch_ttl_s(five) - sum(j.timeout_s for j in five) == (
        tunnel_host.CLOUD_STARTUP_MARGIN_S + tail)


def test_ttl_scales_past_the_old_fixed_hour():
    """本条锁住被修的病根：12 个默认预算（300s）的 job 已超旧的恒定 1h TTL——TTL 必须随 definition 涨，
    否则守护会在 run 尚未结束时拆隧道，剩余 job 以「AI 报导航失败」的假失败告终（ADR 0035 决策 3）。"""
    jobs = [_job(f"s{i}", 300.0) for i in range(12)]
    assert tunnel_host.compute_watch_ttl_s(jobs) > 3600.0


def test_ttl_gives_unbounded_jobs_an_explicit_ceiling():
    """`--default-job-timeout <=0`（执行侧不超时）→ job.timeout_s=None：TTL 仍须有限（否则泄漏兜底失效）；
    每 job 余量对这样的 job 照样计入。"""
    ttl = tunnel_host.compute_watch_ttl_s([_job("a", None), _job("b", None)],
                                          startup_margin_s=0.0, per_job_margin_s=0.0,
                                          unbounded_job_budget_s=1000.0)
    assert ttl == 2000.0
    assert tunnel_host.compute_watch_ttl_s([_job("a", None)], startup_margin_s=0.0, per_job_margin_s=210.0,
                                           unbounded_job_budget_s=1000.0) == 1210.0


def test_ttl_empty_definition_is_just_the_margin():
    """没有 job 时只剩一次性余量：每 job 余量按 job 数计入，零个 job 不加。"""
    assert tunnel_host.compute_watch_ttl_s([], startup_margin_s=900.0) == 900.0


# ---- watch_run_and_stop_tunnel：轮询终态即拆 / TTL 兜底自杀 ----

def _patch_run_store(monkeypatch, states):
    """把 compose._make_ddb_table 换成吐固定 RunState 序列的 fake（states 用尽后复用最后一个）。"""
    seq = list(states)

    class _FakeStore:
        def load_run_state(self, run_id):
            got = seq.pop(0) if len(seq) > 1 else seq[0]
            if isinstance(got, BaseException):
                raise got
            return got

    monkeypatch.setattr(compose, "_make_ddb_table", lambda t, *, region, profile: object())
    monkeypatch.setattr("gherkai_core.adapters.run_store.ddb.DynamoDBRunStore", lambda table: _FakeStore())


def _state(status: Status) -> RunState:
    return RunState(run_id="r1", status=status, jobs={}, high_water_mark=0)


def test_watch_stops_tunnel_on_terminal_state(monkeypatch):
    stopped = []
    monkeypatch.setattr(gtunnel, "stop_tunnel", lambda pid: stopped.append(pid))
    monkeypatch.setattr(compose, "resolve_region", lambda r, p, **kw: r)
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
    monkeypatch.setattr(compose, "resolve_region", lambda r, p, **kw: r)
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
    assert warned and "读 run 状态失败" in warned[0]  # 诊断经 on_warn 交给前端打印


def test_watch_stops_tunnel_even_when_store_assembly_fails(monkeypatch):
    """store 装配段抛（region 解析不出/凭证坏）→ 守护进程带着异常退出，但隧道**必须已拆**（ADR 0035：守护进程是隧道
    唯一宿主，它死了没人再拆）。不要把拆除移到循环之后：装配段抛出时执行不到那里，ngrok 会永久留在公网。"""
    import pytest

    stopped = []
    monkeypatch.setattr(gtunnel, "stop_tunnel", lambda pid: stopped.append(pid))
    monkeypatch.setattr(compose, "resolve_cloud_target", lambda **kw: (_ for _ in ()).throw(RuntimeError("no region")))
    with pytest.raises(RuntimeError, match="no region"):
        tunnel_host.watch_run_and_stop_tunnel("r1", tunnel_pid=778, runs_table="tbl", ttl_s=600.0, region=None)
    assert stopped == [778]


def test_watch_stops_tunnel_when_stop_signal_interrupts_polling(monkeypatch):
    """守护进程入口把 SIGTERM / SIGHUP 转成 SystemExit：它不是 Exception，轮询里容忍读库异常的 `except Exception`
    不能把它当成一次读库失败吞掉，异常须冒出主体，隧道经 finally 拆掉（守护进程是隧道唯一宿主，ADR 0035 决策 3）。"""
    import pytest

    stopped, warned = [], []
    monkeypatch.setattr(gtunnel, "stop_tunnel", lambda pid: stopped.append(pid))
    monkeypatch.setattr(compose, "resolve_region", lambda r, p, **kw: r)
    _patch_run_store(monkeypatch, [_state(Status.RUNNING), SystemExit(128 + 15)])
    import time as _t

    monkeypatch.setattr(_t, "sleep", lambda s: None)
    clock = {"t": 0.0}

    def mono():  # 每读一次前进 1s：SystemExit 若被当成读库失败吞掉，约 600 次轮询后按 TTL 返回、本条随即失败，不会忙等满 600 秒
        clock["t"] += 1.0
        return clock["t"]

    monkeypatch.setattr(_t, "monotonic", mono)
    with pytest.raises(SystemExit):
        tunnel_host.watch_run_and_stop_tunnel(
            "r1", tunnel_pid=779, runs_table="tbl", ttl_s=600.0, region="us-east-1", on_warn=warned.append)
    assert stopped == [779] and warned == []
