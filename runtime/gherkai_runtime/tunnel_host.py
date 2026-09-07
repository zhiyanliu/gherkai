"""隧道宿主编排（ADR 0035 决策 3）：起隧道 + 映射 definition、守隧道到 run 终态。

**宿主** = 持有隧道 agent 进程生命周期的那个进程（ADR 0035 决策 3 的三形态：前台 `run` 的 CLI 进程 /
local `submit` 的 per-run 进程 / cloud `submit` 的隧道守护进程）。本模块住产品本体层（`gherkai` 知道
run 生命周期，ADR 0016「演进」节）；入口皮（cli / 未来 WebUI）只负责 argparse 与打印：

- `start_tunnel_for_jobs`：起隧道 → 映射 definition → 给出隧道模式恒注入的额外请求头（决策 1/2/4）。
- `compute_watch_ttl_s` + `watch_run_and_stop_tunnel`：cloud submit 守护进程的 TTL 算法与主体循环。

**术语护栏**（同 ADR 0016「演进」节的命名护栏）：叫 host（宿主，取自 ADR 0035 决策 3 的表头术语），
不叫 worker——worker 在 ADR 0024 里专指被 spawn 跑 scope 的引擎进程，与隧道宿主无关。
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from gherkai_core.model import TERMINAL_STATUSES, Job

from gherkai_runtime import compose
from gherkai_runtime import tunnel as _tunnel

# 隧道模式恒注入的额外请求头（ADR 0035 决策 4）：ngrok 免费层对浏览器返回 interstitial 警告页（对自动化
# 致命），带任意值的该头即绕过；付费户带着无害（服务端忽略）→ 不做付费检测、隧道模式下恒注入。
TUNNEL_EXTRA_HTTP_HEADERS = {"ngrok-skip-browser-warning": "1"}

# —— cloud submit 隧道守护 TTL 的两个记账常量（ADR 0035 决策 3 的「TTL 兜底自杀」）——
# TTL 只是**防 ngrok 进程泄漏的上界**，宁长不宜短：短于 run 实际预算时守护会在 run 还在跑时拆隧道，
# 剩余 job 在被测应用不可达下继续跑、以「AI 报导航失败」的假失败告终（兜底机制反成失败源）。
#
# 启动/级联余量（一次性）：submit 只写 runs 表，之后 Stream INSERT 投递 → kicker Lambda 冷启动 →
# RunTask → Fargate 拉镜像/挂 ENI 才真开跑；job 之间还有云端事件链的固有尾延迟（ADR 0034 地基实测：
# worker 真停到可归约 ~27s，瓶颈在 ECS `executionStoppedAt→stoppedAt` 的平台清理），末尾还有 finalize。
# job.timeout_s 从 claim 起算、已含拉镜像（ADR 0034「job timeout」节），故此处兜的是「链路投递 + Lambda
# 冷启动 + 每 job 尾延迟的累计 + 收尾」。取 900s：对常规批量留数倍余量；极大批量用显式 TTL 覆盖。
CLOUD_STARTUP_MARGIN_S = 900.0
# 无 job 预算（`--default-job-timeout <=0` 且未标 `@timeout` ＝ 执行侧不超时）时的 TTL 记账上限。
# **只用于算 TTL，不是执行超时**：TTL 必须有限（否则泄漏兜底失效），故给不超时的 job 记一个明确上界。
UNBOUNDED_JOB_BUDGET_S = 3600.0


@dataclass(frozen=True)
class TunnelSetup:
    """隧道就绪后的三件产物：映射过的 definition + 隧道模式的额外请求头 + 隧道事实（收尾凭据）。"""

    jobs: tuple[Job, ...]
    extra_http_headers: dict[str, str]
    info: _tunnel.TunnelInfo


def start_tunnel_for_jobs(jobs, *, local_origin: str, provider: str = "ngrok") -> TunnelSetup:
    """起隧道并把 definition 里的 origin 映射成公网 URL（ADR 0035 决策 1/2/4）。

    起不来（provider 未知 / agent 不就绪 / 缺 authtoken）→ `tunnel.TunnelError`，调用方归「没开跑就被拒」。
    映射产出新 Job（definition 不可变，见 `map_origin_in_jobs`）；原 jobs 不动。
    """
    info = _tunnel.make_tunnel(provider).start(local_origin)
    mapped = _tunnel.map_origin_in_jobs(list(jobs), local_origin, info.mapped_base)
    return TunnelSetup(jobs=tuple(mapped), extra_http_headers=dict(TUNNEL_EXTRA_HTTP_HEADERS), info=info)


def compute_watch_ttl_s(
    jobs, *, startup_margin_s: float = CLOUD_STARTUP_MARGIN_S,
    unbounded_job_budget_s: float = UNBOUNDED_JOB_BUDGET_S,
) -> float:
    """按 definition 算 cloud submit 隧道守护的 TTL 秒数 = Σ(各 job 预算) + 启动/级联余量。

    **求和而非取 max**：并发 >1 时各 job 部分重叠、真实墙钟 < 各预算之和，故串行总预算对**任何**并发取值
    都是保守上界（并发随 definition 走、cloud 再受部署侧 cap 钳制，ADR 0034 机制四——此处不必知道取值）。
    高估无害：TTL 偏长＝隧道多留一会儿（run 终态照常提前拆）；反向（低估）才会造出假失败。
    无预算（执行侧不超时）的 job 按 `unbounded_job_budget_s` 记账——TTL 必须有限。
    """
    return startup_margin_s + sum(
        (j.timeout_s if j.timeout_s else unbounded_job_budget_s) for j in jobs
    )


def watch_run_and_stop_tunnel(
    run_id: str, *, tunnel_pid: int, runs_table: str, ttl_s: float,
    region: str | None = None, profile: str | None = None,
    poll_interval_s: float = 5.0, on_warn=None,
) -> str:
    """cloud submit 隧道守护进程的主体（ADR 0035 决策 3 cloud 档）：轮询 DDB run 终态 → 拆隧道；
    TTL 到点 → 拆隧道自杀（防「run 卡死 / 查询持续异常」时 ngrok 进程泄漏）。返回拆除原因（调用方打印）。

    读库异常不致命（瞬时网络/限流）——经 `on_warn`（可选，皮层给打印口）报一句后继续轮询，TTL 是最终兜底。
    """
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore

    target = compose.resolve_cloud_target(runs_table=runs_table, region=region, profile=profile)
    run_store = DynamoDBRunStore(compose._make_ddb_table(
        target.runs_table, region=target.region, profile=target.profile))
    deadline = time.monotonic() + ttl_s
    reason = f"TTL 兜底 {ttl_s:.0f}s"
    while time.monotonic() < deadline:
        try:
            state = run_store.load_run_state(run_id)
            if state is not None and state.status in TERMINAL_STATUSES:
                reason = f"run 终态 {state.status.value}"
                break
        except Exception as e:  # 瞬时读库异常不致命——TTL 最终兜底
            if on_warn is not None:
                on_warn(f"读 run 状态失败（继续轮询）：{e}")
        time.sleep(poll_interval_s)
    _tunnel.stop_tunnel(tunnel_pid)
    return reason
