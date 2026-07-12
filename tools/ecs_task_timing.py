#!/usr/bin/env python
"""ECS task 生命周期时间字段抓取（Fargate SIGTERM→退出耗时标定，ADR 0032 / 0024）。

**为何独立成脚本、不改 fargate_engine**：`FargateEngine._task_exit_code`（core/core/adapters/fargate_engine.py）
是产品热路径，返回 `int|None` 供 `_read_events` 轮询判定存活/退出——它**只读 lastStatus/exitCode、丢弃时间
字段**（够判定即可）。grace/stopTimeout 校准要的是 SIGTERM→退出的**真实墙钟预算**（`stoppingAt`/`executionStoppedAt`/`stoppedAt`
的差），属一次性标定、非运行期判定；混进 `_task_exit_code` 会污染其单一职责、且改产品路径需回归。故独立脚本纯读。

**测什么**（DescribeTasks 的时间字段，task STOPPED 后才全）：
- `createdAt`：RunTask 收到请求。
- `startedAt`：容器进入 RUNNING。
- `stoppingAt`：ECS 开始停（发 SIGTERM 的锚点）。
- `executionStoppedAt`：容器进程实际停（worker 退出的锚点）。**stoppingAt→executionStoppedAt = SIGTERM→退出真实耗时**
  ——这是校准 stopTimeout 的核心量（对照生效 stopTimeout；grace 下限 vs stopTimeout 的关系见 ADR 0032 结论 4）。
- `stoppedAt`：task 完全 STOPPED（清理完）。
- `stopCode` / `stoppedReason`：停因（`TaskFailedToStart` / `EssentialContainerExited` / `UserInitiated`(StopTask) 等）。
  SIGTERM→SIGKILL 被 stopTimeout 截断时 stopCode 仍是 UserInitiated，但 executionStoppedAt-stoppingAt ≈ stopTimeout
  即证据（worker 没在 grace 内退干净）。

**run-2/run-3 用法**（协作停止路径：运行中发 StopTask 触发 SIGTERM）：
  1. `--backend cloud` 起一个 worker（或 e2e）；从 events 表见 step_started（act in-flight）。
  2. `aws ecs list-tasks --cluster <cluster>` 拿 task ARN，`aws ecs stop-task` 手动停（触发 SIGTERM）。
  3. task STOPPED 后跑本脚本抓时间字段。或直接 `--wait` 让脚本轮询到 STOPPED 再吐（省得手动等）。

  PYTHONPATH=core core/.venv/bin/python tools/ecs_task_timing.py \\
      --cluster gherkai-cluster --task <task_arn> [--region us-east-1] [--wait] [--stop-timeout 120] [--json]

  --wait：轮询 DescribeTasks 直到 lastStatus==STOPPED（时间字段才全）再吐；默认单次快照（可能字段未齐）。
  --container：算 container 级 exitCode 时匹配的 container 名（默认取第一个）。
  --stop-timeout：task-def 生效的 stopTimeout 秒（判 SIGTERM→退出是否被 SIGKILL 截断的阈值；范围 [1,120]，
                  不给则回落 Fargate 上限 120）——写死 120 会在跑 -c stop_timeout=60 时把「达 60 被截断」误判成过保守。

输出：时间字段原值（ISO）+ 派生的三段耗时（created→started 启动、stopping→executionStopped SIGTERM→退出、
stopping→stopped 总停）+ stopCode/stoppedReason + container exitCode。
"""
from __future__ import annotations

import argparse
import json
import sys
import time

# DescribeTasks 返回的时间字段名（task 级），按生命周期顺序。
_TIME_FIELDS = ("createdAt", "startedAt", "stoppingAt", "executionStoppedAt", "stoppedAt")
_POLL_S = 1.0
_WAIT_TIMEOUT_S = 300.0  # --wait 轮询上限（防 task 卡 STOPPING 永不 STOPPED 时死等）


def _ecs(region: str | None):
    import boto3

    return boto3.client("ecs", region_name=region)


def _describe(ecs, cluster: str, task: str) -> dict | None:
    resp = ecs.describe_tasks(cluster=cluster, tasks=[task])
    tasks = resp.get("tasks", [])
    return tasks[0] if tasks else None


def _iso(dt) -> str | None:
    """boto3 返回的 datetime → ISO 字符串（缺省 None）。"""
    return dt.isoformat() if dt is not None else None


def _delta_s(t: dict, a: str, b: str) -> float | None:
    """t[b] - t[a] 秒数（任一缺 → None）。t 存的是 datetime。"""
    da, db = t.get(a), t.get(b)
    if da is None or db is None:
        return None
    return round((db - da).total_seconds(), 3)


def capture(cluster: str, task: str, region: str | None, wait: bool,
            container: str | None, stop_timeout: int | None) -> dict:
    ecs = _ecs(region)
    t = _describe(ecs, cluster, task)
    if t is None:
        return {"error": f"DescribeTasks 未返回 task（arn 错 / 已从 ECS 记录中过期）：{task}"}

    wait_timed_out = False
    if wait:
        deadline = time.monotonic() + _WAIT_TIMEOUT_S
        while t.get("lastStatus") != "STOPPED" and time.monotonic() < deadline:
            time.sleep(_POLL_S)
            t = _describe(ecs, cluster, task) or t
        wait_timed_out = t.get("lastStatus") != "STOPPED"  # 到点仍未 STOPPED → 时间字段可能不全

    times = {f: t.get(f) for f in _TIME_FIELDS}  # datetime | None
    containers = t.get("containers", [])
    # container 选择 + **显式给名却零匹配**的告警（防名字打错被静默当「无数据」，与真 task 无容器无法区分）。
    container_warning = None
    if container is not None:
        picked = next((c for c in containers if c.get("name") == container), None)
        if picked is None and containers:
            container_warning = (f"--container {container!r} 未匹配任何容器；可用："
                                 f"{[c.get('name') for c in containers]}（是不是名字打错？）")
    else:
        picked = containers[0] if containers else None

    return {
        "cluster": cluster, "task": task,
        "last_status": t.get("lastStatus"),
        "stop_code": t.get("stopCode"),
        "stopped_reason": t.get("stoppedReason"),
        "wait_timed_out": wait_timed_out,
        "container_warning": container_warning,
        "stop_timeout_ref": stop_timeout,  # 用户告知的 task-def 生效 stopTimeout（判 SIGKILL 截断用；None=未告知，回落 120 上限）
        "times_iso": {f: _iso(times[f]) for f in _TIME_FIELDS},
        "durations_s": {
            "created_to_started": _delta_s(times, "createdAt", "startedAt"),
            # SIGTERM→退出真实耗时（stopTimeout 校准核心量，ADR 0032）
            "stopping_to_execution_stopped": _delta_s(times, "stoppingAt", "executionStoppedAt"),
            "stopping_to_stopped": _delta_s(times, "stoppingAt", "stoppedAt"),
        },
        "container": {
            "name": picked.get("name") if picked else None,
            "exit_code": picked.get("exitCode") if picked else None,
            "reason": picked.get("reason") if picked else None,
        } if picked else None,
    }


def _print_human(r: dict) -> None:
    if "error" in r:
        print(f"错误：{r['error']}")
        return
    print(f"cluster={r['cluster']} task={r['task']}")
    print(f"lastStatus={r['last_status']} stopCode={r['stop_code']} stoppedReason={r['stopped_reason']}")
    if r.get("wait_timed_out"):
        print(f"⚠️  --wait 到点仍未 STOPPED（lastStatus={r['last_status']}）——下面时间字段/派生耗时可能不全（非最终值）。")
    if r.get("container_warning"):
        print(f"⚠️  {r['container_warning']}")
    print("--- 时间字段（ISO）---")
    for f, v in r["times_iso"].items():
        print(f"  {f:<22} {v}")
    d = r["durations_s"]
    print("--- 派生耗时（秒）---")
    print(f"  created→started（启动）         {d['created_to_started']}")
    print(f"  stopping→executionStopped      {d['stopping_to_execution_stopped']}  ← SIGTERM→退出真实耗时（stopTimeout 校准核心）")
    print(f"  stopping→stopped（总停）         {d['stopping_to_stopped']}")
    c = r["container"]
    if c:
        print(f"--- container {c['name']} ---  exitCode={c['exit_code']} reason={c['reason']}")
    ste = d["stopping_to_execution_stopped"]
    if ste is not None:
        # 判 SIGKILL 截断的阈值 = **实际生效的 stopTimeout**（--stop-timeout 告知），非写死 120——校准时本就会试不同
        # stop_timeout 值，写死 120 会在 -c stop_timeout=60 时把「达 60 被 SIGKILL」误判成「远低于 120、过保守」（方向反）。
        # 未告知则回落 Fargate 上限 120（保守）。再交叉 exitCode（137≈128+9=SIGKILL）辅助消歧。
        # 用 `is not None`（非 `or`）判在场：--stop-timeout 已在 main() 校验 [1,120]（0/负被拒），此处不会遇非法值；
        # `is not None` 保证「告知了就用告知值」的语义清晰（不因某假值静默回落）。
        ref = r.get("stop_timeout_ref")
        cap = ref if ref is not None else 120
        cap_src = f"--stop-timeout={ref}" if ref is not None else "未告知，回落 Fargate 上限 120"
        exit_code = (c or {}).get("exit_code")
        killed_hint = "（exitCode=137≈SIGKILL，佐证被截断）" if exit_code == 137 else ""
        near_cap = ste >= cap * 0.9  # 逼近生效 stopTimeout 的 90% 视作疑被截断
        if near_cap:
            verdict = f"逼近/达生效 stopTimeout({cap}s)，疑被 SIGKILL 截断、worker 没在宽限内退干净{killed_hint}"
        else:
            verdict = f"明显低于生效 stopTimeout({cap}s)，grace 有余量；对照本 run 引擎的 grace 下限看是否过保守"
        print(f"\n对照生效 stopTimeout（{cap_src}）：SIGTERM→退出={ste}s → {verdict}")


def main() -> None:
    ap = argparse.ArgumentParser(description="ECS task 生命周期时间字段抓取（Fargate SIGTERM→退出标定，ADR 0032）")
    ap.add_argument("--cluster", required=True, help="ECS cluster 名（如 gherkai-cluster）")
    ap.add_argument("--task", required=True, help="task ARN 或 id")
    ap.add_argument("--region", default=None, help="AWS region（默认走 boto 默认链）")
    ap.add_argument("--wait", action="store_true", help="轮询至 STOPPED 再吐（时间字段才全）；默认单次快照")
    ap.add_argument("--container", default=None, help="container 名（算 exitCode 用；默认取第一个）")
    ap.add_argument("--stop-timeout", type=int, default=None,
                    help="task-def 生效的 stopTimeout 秒（判 SIGKILL 截断的阈值；不给则回落 Fargate 上限 120）")
    ap.add_argument("--json", action="store_true", help="吐机读 JSON（默认人读）")
    a = ap.parse_args()
    # 校验 --stop-timeout 落在 [1,120]（对齐 stack._resolve_stop_timeout 的 Fargate 契约）：0/负会污染 near_cap 判定
    # （negative*0.9 恒被 ste≥ 触发→假阳「被截断」），>120 非法。从源头拒，别让非法阈值静默产出错误校准结论。
    if a.stop_timeout is not None and not 1 <= a.stop_timeout <= 120:
        ap.error(f"--stop-timeout={a.stop_timeout} 越界：须 1..120（Fargate stopTimeout 硬上限，对齐 stack.py）")
    r = capture(a.cluster, a.task, a.region, a.wait, a.container, a.stop_timeout)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2, default=str))
    else:
        _print_human(r)
    if "error" in r:
        sys.exit(2)


if __name__ == "__main__":
    main()
