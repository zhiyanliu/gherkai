"""CloudLauncher（ADR 0034 cloud 侧）：cloud 的 reconcile.Launcher——RunTask 起 Fargate task（fire-and-forget）。

cloud 对位 local 的 SubprocessLauncher：reconciler（Lambda）机制四 CAS 抢占成功后调 launch(job)，经注入的
FargateEngine `start_scope` 起一个 Fargate task 就返回（不轮询、不读事件——worker 自 PutItem events 到 DDB、
退出观察者 Lambda 补 task_exited、reconciler Lambda 从表重放推进）。

与 local SubprocessLauncher 的**关键不对称**（正确的，非缺陷）：
- local：per-run 进程既起 worker 又亲自读 fd3 落 SQLite + proc.wait 写 task_exited（父进程能看到子进程）。
- cloud：CloudLauncher 只起 task——worker 自己 PutItem events（[0024]，worker 侧不改）、退出观察者是**独立的
  ECS STOPPED 事件 Lambda**（非 launcher，因 launcher 起完 task 就返回、看不到 task 何时退）。这正是「进程干净
  终止只有平台看得见」（机制二）在 cloud 的落地：退出信号来自 ECS 平台事件、不由起 task 的一方观察。
"""
from __future__ import annotations

import logging

from core.model import Job

logger = logging.getLogger("core.adapters.cloud_launcher")


class CloudLauncher:
    """cloud Launcher：按 job.engine 选 FargateEngine（经注入的 resolver），launch=start_scope（fire-and-forget）。

    resolver 与 local SubprocessLauncher 的 resolver 同构（按 engine 名产 Engine）——cloud 的由
    compose.build_fargate_engines + make_resolver 产（cloud FargateEngine 装配的单一真源，不在 launcher 重造），
    故 job-in 前缀 / artifact 落点 / task-def·container 名 / SDK env 全与同步 cloud run 路径一致、零漂移。
    """

    def __init__(self, resolver, *, run_id: str | None = None, timeout_watch=None) -> None:
        self._resolver = resolver
        # job timeout 的到点触发器（ADR 0034「job timeout」节 cloud 档，组合根注入；实现= EventBridge Scheduler
        # one-time schedule，见 lambdas/reconciler.py）。协议：arm(run_id, scope_id, timeout_s)。None=未装配
        # （旧部署/无 env）——有预算的 job 降级为 tick 防御扫 + status --wait，打日志。
        self._run_id = run_id
        self._timeout_watch = timeout_watch

    def launch(self, job: Job) -> None:
        # fire-and-forget：按 engine 取 FargateEngine、start_scope 起 task 就返回。task_arn 不在此保留——
        # reconciler 靠 events 表（worker PutItem）+ task_exited（退出观察者 Lambda 写）推进，不靠 launcher 轮询。
        engine = self._resolver(job.engine)
        engine.start_scope(job)
        if job.timeout_s:
            if self._timeout_watch is None or self._run_id is None:
                logger.warning(
                    "job timeout 未武装（未注入 timeout_watch/run_id）：scope=%s 预算 %ss 降级为 tick 防御扫",
                    job.scope_id, job.timeout_s)
            else:
                # best-effort（ADR 0034「job timeout」节边界）：武装失败不阻塞 launch——保护降级为
                # tick 防御扫（claimed_at ②）+ status --wait，只打日志。
                try:
                    self._timeout_watch.arm(self._run_id, job.scope_id, job.timeout_s)
                except Exception:
                    logger.warning("job timeout 武装失败（best-effort 降级 tick 防御扫）：run=%s scope=%s",
                                   self._run_id, job.scope_id, exc_info=True)
