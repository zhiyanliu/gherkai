"""CloudLauncher（ADR 0034 P4）：cloud 的 reconcile.Launcher——RunTask 起 Fargate task（fire-and-forget）。

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

from core.model import Job


class CloudLauncher:
    """cloud Launcher：持一个 FargateEngine，launch=start_scope（fire-and-forget 起 task）。"""

    def __init__(self, fargate_engine) -> None:
        self._engine = fargate_engine

    def launch(self, job: Job) -> None:
        # fire-and-forget：起 task 就返回。task_arn 不在此保留——reconciler 靠 events 表（worker PutItem）+
        # task_exited（退出观察者 Lambda 写）推进，不靠 launcher 持 task_arn 轮询（对照 local 也不持，一致）。
        self._engine.start_scope(job)
