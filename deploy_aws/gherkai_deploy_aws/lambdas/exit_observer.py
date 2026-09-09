"""退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。

EventBridge rule（detail-type='ECS Task State Change'、lastStatus=STOPPED、本 cluster）触发本 handler。
它是**平台侧外部观察者**——worker 崩了/被 SIGKILL 也照发（进程干净终止只有平台看得见，机制二）。职责极薄：
从 STOPPED event 拿 run_id/scope_id（RunTask 注入的 env 原样在 detail.overrides，真验证据坐实）+ exitCode
（detail.containers[].exitCode，真验 4/4 含 SIGKILL=137 都带）→ DdbEventLog.record_exit 写 task_exited
（保留高位 SK 独立键空间）。写完即返回——reconciler Lambda 由 events 表 Stream 变化触发、接力推进。
**只为 detached run 写**：同 cluster 的同步 `run --backend cloud` 的 task 同样触发本 handler，写前分流（见
`_is_detached`；不变量与故障形态见 ADR 0034 端到端 cloud 1b 与机制一）。

**缺 exitCode → 落哨兵（机制二「退出码缺失」条）**：STOPPED 事件锚在 stoppedAt（已过 exitCode 落值窗口），正常退出
必带码（真验 4/4）；缺码 = 容器没跑起来（stopCode=TaskFailedToStart：拉不到镜像/缺 secret/放置失败），且本事件是观察者
**唯一一次机会**（ECS 不会再发）→ 写 `PLATFORM_FAILED_EXIT` 哨兵 + reason（`stopCode: stoppedReason`），投影走
「exit≠0 → ERROR」收敛、用户在 job message 里看到归因。曾写 None 当宽限态等「下轮补」——没有下轮，run 永久 wedge。
不在此重查 DescribeTasks（保持 handler 薄、无 ECS IAM；对 TaskFailedToStart 重查也永远拿不到码）。

打包：本文件与 reconciler.py 是 **asset 原料**（住在 provider 包 `gherkai_deploy_aws/lambdas/`，ADR 0037 决策 6），
由 `BackendStack._build_lambda_asset` 摊到 zip **根**（故按顶层模块名 import reconciler，不走包路径）。
boto3 是 Lambda runtime 自带。
env：EVENTS_TABLE（events 表名）、RUNS_TABLE（判 run 是否 detached，见 `_is_detached`）、
AWS_REGION（Lambda runtime 自带）。
"""
from __future__ import annotations

import os


def _extract(detail: dict) -> tuple[str | None, str | None, int | None, bool, str | None]:
    """从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code, timed_out, reason)。

    run_id/scope_id：RunTask 注入的 env 原样在 detail.overrides.containerOverrides[].environment（真验坐实）。
    exit_code：detail.containers[] 里匹配的 container 的 exitCode；**缺 → `PLATFORM_FAILED_EXIT` 哨兵**（容器没跑
    起来，见模块头），此时 reason = `stopCode: stoppedReason`（用户可见归因）；带码时 reason=None（worker 自己的日志才是归因源）。
    timed_out：detail.stoppedReason 含超时哨兵（reconciler 的超时处置 StopTask(reason) 原样出现在此，
    ADR 0034「job timeout」节归因链）→ task_exited 带 timed_out=True。
    """
    from reconciler import TIMEOUT_STOP_SENTINEL
    from gherkai_core.project import PLATFORM_FAILED_EXIT
    run_id = scope_id = None
    for co in detail.get("overrides", {}).get("containerOverrides", []):
        for e in co.get("environment", []):
            if e.get("name") == "RUN_ID":
                run_id = e.get("value")
            elif e.get("name") == "SCOPE_ID":
                scope_id = e.get("value")
    exit_code = None
    containers = detail.get("containers", [])
    if containers:
        # 取第一个带 exitCode 的 container（worker 是 essential 单容器；多容器时 worker 容器的码即 task 结果）
        for c in containers:
            if c.get("exitCode") is not None:
                exit_code = c["exitCode"]
                break
    stopped_reason = detail.get("stoppedReason") or ""
    timed_out = TIMEOUT_STOP_SENTINEL in stopped_reason
    reason = None
    if exit_code is None:
        exit_code = PLATFORM_FAILED_EXIT
        reason = ": ".join(x for x in (detail.get("stopCode"), stopped_reason) if x) or "平台未给出退出码与原因"
    return run_id, scope_id, exit_code, timed_out, reason


def _is_detached(run_id: str) -> bool:
    """本 run 是否由云端推进器管（ADR 0034 端到端 cloud 1b：`detached` 标记在 runs 表 STATE item 上）。

    EventBridge rule 只按 cluster+STOPPED 过滤，而同步 `run --backend cloud` 的 task 与 detached 共用一个
    cluster、必触发本 handler——但同步路径不用 `DdbEventLog`，给它写 `task_exited` 既无人消费、还会让它的
    events Query 读端撞上「无 `body` 属性的 item」（机制一）。故写前分流，判据与 kicker 的 Stream filter 同源。
    """
    import boto3
    from gherkai_core.adapters.run_store.ddb import DynamoDBRunStore

    # 只读 STATE 的标记属性，不读 META → 无需注入 arg_offloader（ADR 0030 决定七的 fail-loud 不涉及）
    table = boto3.resource("dynamodb").Table(os.environ["RUNS_TABLE"])
    return DynamoDBRunStore(table).is_detached(run_id)


def _event_log(run_id: str, scope_id: str):
    """构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。"""
    import boto3
    from gherkai_core.adapters.event_log import DdbEventLog

    table_name = os.environ["EVENTS_TABLE"]
    table = boto3.resource("dynamodb").Table(table_name)
    # scope_ids 只需当前这个（record_exit 只写本 scope 的 task_exited；不读全量，故单元素够）
    return DdbEventLog(table, run_id, [scope_id])


def handler(event, context):
    """EventBridge ECS STOPPED 事件入口。写本 task 的 task_exited。"""
    detail = event.get("detail", {})
    run_id, scope_id, exit_code, timed_out, reason = _extract(detail)
    if not run_id or not scope_id:
        # 非本框架起的 task（同 cluster 别的负载）或 env 缺失 → 忽略（rule 已按 cluster 过滤，此为双保险）
        print(f"exit_observer: 跳过（缺 run_id/scope_id）taskArn={detail.get('taskArn')}")
        return {"skipped": True}
    if not _is_detached(run_id):
        print(f"exit_observer: 跳过（run {run_id} 非 detached，同步 cloud run 自己观察退出）")
        return {"skipped": True, "reason": "not-detached"}
    log = _event_log(run_id, scope_id)
    log.record_exit(scope_id, exit_code, timed_out=timed_out, reason=reason)
    print(f"exit_observer: task_exited run={run_id} scope={scope_id} exit={exit_code} timed_out={timed_out}"
          + (f" reason={reason!r}" if reason else ""))
    return {"ok": True, "run_id": run_id, "scope_id": scope_id, "exit_code": exit_code, "timed_out": timed_out,
            "reason": reason}
