"""运行期限的算式（ADR 0054 决策二）：建 run 时由创建时刻、各 job 的墙钟预算与每 job 尾段推出 `deadline_at`，写进运行定义。

    deadline_at = created_at + 900 秒 + Σ（各 job 的墙钟预算 + 每 job 尾段）

- 每 job 尾段：本机后端取 `2 × G + 10` 秒（`local_per_job_tail_s`），G 是停止宽限：前台 `run` 取这次调用解析出的值，本机 `submit`
  取这个 run 用到的各引擎自报宽限里最大的一个；云端后端取 `CLOUD_PER_JOB_TAIL_S`，即隧道存活时间上限已在用的每 job 余量
  （`tunnel_host.CLOUD_PER_JOB_MARGIN_S`，210 秒）。
- 900 秒是一次性余量（`STARTUP_MARGIN_S`），留给建 run 到起第一个 job 之间的装配与各次落库、云端调用。
- 求和而不按并发折算：并发大于 1 时真实墙钟小于各预算之和，串行总和对任何并发取值都偏宽（与 `compute_watch_ttl_s` 同一做法）。

尾段与余量是预算的取值，不是「执行一定已停」的上界，它们只决定期限定得多宽。算式只在建 run 时用一次：期限存进运行定义，此后各
执行方与读者都读存下的那个时刻、不重算——停止宽限不在任何记录里，算式也可能随版本变化，重算得不出同一个时刻。
"""
from __future__ import annotations

from collections.abc import Iterable
from datetime import timedelta

from gherkai_core.model import Job
from gherkai_core.serialize import instant_from_iso, instant_to_iso

from gherkai_runtime.tunnel_host import CLOUD_PER_JOB_MARGIN_S

# 一次性余量（每个 run 一份，与 job 数无关）：与隧道存活时间上限的一次性余量同值，各自独立持有（两者回答的问题不同）。
STARTUP_MARGIN_S = 900.0
# 云端后端的每 job 尾段：超时触发的调度精度、停止宽限与事件链尾延迟之和，组成见 tunnel_host.CLOUD_PER_JOB_MARGIN_S 的注释。
CLOUD_PER_JOB_TAIL_S = CLOUD_PER_JOB_MARGIN_S


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
