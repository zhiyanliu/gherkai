"""运行期限的算式（ADR 0054 决策二）：建 run 时由创建时刻、各 job 的墙钟预算与每 job 尾段推出 `deadline_at`，写进运行定义。

    deadline_at = created_at + 900 秒 + Σ（各 job 的墙钟预算 + 每 job 尾段）

- 每 job 尾段：本机后端取 `2 × G + 10` 秒（`local_per_job_tail_s`），G 是停止宽限：前台 `run` 取这次调用解析出的值，本机 `submit`
  取这个 run 用到的各引擎自报宽限里最大的一个；云端后端取 `CLOUD_PER_JOB_TAIL_S`（210 秒，组成见它的注释）。
- 900 秒是一次性余量（`STARTUP_MARGIN_S`），留给取创建时刻到起第一个 job 之间的各步：起隧道、生成运行定义与建 run、装配与各次
  落库、云端调用。
- 求和而不按并发折算：并发大于 1 时真实墙钟小于各预算之和，串行总和对任何并发取值都偏宽。

尾段与余量是预算的取值，不是「执行一定已停」的上界，它们只决定期限定得多宽。算式只在建 run 时用一次：期限存进运行定义，此后各
执行方与读者都读存下的那个时刻、不重算——停止宽限不在任何记录里，算式也可能随版本变化，重算得不出同一个时刻。

建 run 用到的各个时刻由 `run_times` 一处算出：创建时刻只读一次钟，期限与隧道边缘的到点时刻都由这一次读数推出，生成运行定义与起
隧道用同一份结果（ADR 0054 决策二「落点是运行定义」）。
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Final

from gherkai_core import run_deadline
from gherkai_core.model import Job
from gherkai_core.serialize import instant_from_iso, instant_to_iso

from gherkai_runtime import compose

# 一次性余量（每个 run 一份，与 job 数无关）。
STARTUP_MARGIN_S = 900.0
# 云端后端的每 job 尾段（每个 job 一份，随 job 数线性累加）：job 用尽预算后被停止时，预算点之后还有三段耗时，并发为 1 时逐个 job
# 串行累加，与 job 数成正比，不随 job 数变化的常数余量覆盖不了。job 的墙钟预算从认领起算、已含 RunTask 与拉镜像、挂 ENI
# （ADR 0034「job timeout」节），这里记的是预算之外的耗时。
#   ① 超时触发的调度精度 60s：job 超时由 EventBridge Scheduler 的一次性 schedule 在认领时刻加预算时触发，
#      Scheduler 的触发精度是 60 秒（关闭 flexible time window 也只保证落在指定时刻所在的那一分钟内）。
#   ② 停止宽限 120s：StopTask 之后 worker 在 container stopTimeout 的宽限内收尾，按 Fargate 的平台上限
#      （compose.FARGATE_STOP_TIMEOUT_MAX_S）取值，对任何 variant 都成立。
#   ③ 事件链尾延迟 30s：task 停止到退出可被归约、下一个 job 被认领之间的固有延迟（ADR 0034 实测每步约 20-30 秒，
#      瓶颈在 ECS 平台的清理开销）。这一项是经验值，**不是服务的硬上界**：平台降级、Lambda 限流或极大批量时可能超出，
#      所以算出的期限是按任务量估算的宽度、不是保证（ADR 0054 决策二「尾段与余量」一段）。
# 合计 210 秒。在预算内结束的 job 只有第 ③ 段，按 210 秒取是高估，偏在安全的一侧。
CLOUD_PER_JOB_TAIL_S: Final = 60.0 + float(compose.FARGATE_STOP_TIMEOUT_MAX_S) + 30.0


def local_per_job_tail_s(grace_s: float) -> float:
    """本机后端的每 job 尾段 `2 × G + 10` 秒：job 到点之后的停止等待、排空与再次停止合计约 `2G + 9` 秒（取值来历见 ADR 0054 决策二）。"""
    return 2.0 * grace_s + 10.0


def compute_deadline_at(created_at: str, jobs: Iterable[Job], *, per_job_tail_s: float) -> str:
    """按上面的算式得出运行期限，返回与 `created_at` 同一写法的 UTC ISO 时刻（`compose.now_iso` 的形态）。

    `created_at` 须是带时区的 ISO 时刻，否则抛 ValueError：不带时区的时刻在别的机器上比较会差出时区偏移。各 job 的墙钟预算恒为
    有限正数（运行定义的契约，ADR 0054 决策十），这里不再核。读与写都经 `serialize` 的那一处（`instant_from_iso` / `instant_to_iso`），
    不另写一份解析。"""
    start = instant_from_iso(created_at)
    total_s = STARTUP_MARGIN_S + sum(job.timeout_s + per_job_tail_s for job in jobs)
    return instant_to_iso(start + timedelta(seconds=total_s))


@dataclass(frozen=True)
class RunTimes:
    """建 run 时的各个时刻，都由创建时刻那一次读数算出。"""

    created: datetime  # 创建时刻那一次读数（带时区）；run 标识的时间前缀也取它
    created_at: str  # 创建时刻在记录里的写法（`serialize.instant_to_iso`）
    deadline_at: str  # 运行期限在记录里的写法
    tunnel_closes_at: datetime  # 隧道边缘的到点时刻：运行期限加 300 秒（`run_deadline.overdue_at`）


def run_times(created: datetime, jobs: Iterable[Job], *, per_job_tail_s: float) -> RunTimes:
    """由创建时刻那一次读数算出期限与到点时刻，只算一次。`created` 不带时区即抛 ValueError。"""
    created_at = instant_to_iso(created)
    deadline_at = compute_deadline_at(created_at, jobs, per_job_tail_s=per_job_tail_s)
    return RunTimes(created=created, created_at=created_at, deadline_at=deadline_at,
                    tunnel_closes_at=run_deadline.overdue_at(instant_from_iso(deadline_at)))
