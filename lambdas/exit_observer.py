"""退出观察者 Lambda（ADR 0034，机制二 cloud 落地）：ECS Task STOPPED 事件 → 写 task_exited。

EventBridge rule（detail-type='ECS Task State Change'、lastStatus=STOPPED、本 cluster）触发本 handler。
它是**平台侧外部观察者**——worker 崩了/被 SIGKILL 也照发（进程干净终止只有平台看得见，机制二）。职责极薄：
从 STOPPED event 拿 run_id/scope_id（RunTask 注入的 env 原样在 detail.overrides，真验证据坐实）+ exitCode
（detail.containers[].exitCode，真验 4/4 含 SIGKILL=137 都带）→ DdbEventLog.record_exit 写 task_exited
（保留高位 SK 独立键空间）。写完即返回——reconciler Lambda 由 events 表 Stream 变化触发、接力推进。

**exitCode 落值兜底（机制二）**：STOPPED 事件锚在 stoppedAt（已过 exitCode 落值窗口，真验证实必带值）；
极少数缺 exitCode 时写 None（宽限态，project 保守判 running，reconciler 下轮由别的信号补——或 status --wait
人工兜底）。不在此重查 DescribeTasks（保持 handler 薄、无额外 IAM；真验证明基本不需要）。

打包：本文件 + core 一起进 Lambda zip（部署见 iac_aws_backend）。boto3 是 Lambda runtime 自带。
env：EVENTS_TABLE（events 表名）、AWS_REGION（Lambda runtime 自带）。
"""
from __future__ import annotations

import os


def _extract(detail: dict) -> tuple[str | None, str | None, int | None]:
    """从 STOPPED event 的 detail 拿 (run_id, scope_id, exit_code)。

    run_id/scope_id：RunTask 注入的 env 原样在 detail.overrides.containerOverrides[].environment（真验坐实）。
    exit_code：detail.containers[] 里匹配的 container 的 exitCode（缺 → None，宽限态）。
    """
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
    return run_id, scope_id, exit_code


def _event_log(run_id: str, scope_id: str):
    """构造 DdbEventLog（Lambda 组合根：读 env 造 boto3 表资源注入 core adapter）。"""
    import boto3
    from core.adapters.event_log import DdbEventLog

    table_name = os.environ["EVENTS_TABLE"]
    table = boto3.resource("dynamodb").Table(table_name)
    # scope_ids 只需当前这个（record_exit 只写本 scope 的 task_exited；不读全量，故单元素够）
    return DdbEventLog(table, run_id, [scope_id])


def handler(event, context):
    """EventBridge ECS STOPPED 事件入口。写本 task 的 task_exited。"""
    detail = event.get("detail", {})
    run_id, scope_id, exit_code = _extract(detail)
    if not run_id or not scope_id:
        # 非本框架起的 task（同 cluster 别的负载）或 env 缺失 → 忽略（rule 已按 cluster 过滤，此为双保险）
        print(f"exit_observer: 跳过（缺 run_id/scope_id）taskArn={detail.get('taskArn')}")
        return {"skipped": True}
    log = _event_log(run_id, scope_id)
    log.record_exit(scope_id, exit_code)
    print(f"exit_observer: task_exited run={run_id} scope={scope_id} exit={exit_code}")
    return {"ok": True, "run_id": run_id, "scope_id": scope_id, "exit_code": exit_code}
