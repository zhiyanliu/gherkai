"""运行期限的规则（ADR 0054 决策二）：执行方把当前墙钟时刻与运行期限比较，判断还能否启动 job、执行中的 job 何时截止。

期限 `RunMeta.deadline_at` 在建 run 时算出、写进运行定义，之后不变（算式在 `gherkai_runtime.deadline`）；这里是拿它与当前时刻
比较的规则，以及由它推出的期限之后那个时刻（见文末）。前台的调度循环与后台的推进步骤都用这一份，提前量与「是否已过」的判断不另写。到期时的说明不在这里：没有启动的 job 与
run 级的说明在结束写的说明表（`run_status.RUN_ENDINGS` 的执行方自己到期一行），被期限截断的 job 的说明在终结函数
（`project.DEADLINE_TIMEOUT_MESSAGE`）。

**墙钟时刻在 core 里的类型是带时区的 datetime。** ISO 串只是记录里的写法（`deadline_at`、`JobState.claimed_at`、组合根的
`compose.now_iso`）：读记录里的时刻用 `serialize.instant_from_iso`，写进记录用 `serialize.instant_to_iso`。本模块的函数只收
datetime，不收 ISO 串；不带时区的 datetime 与带时区的比较时 Python 抛 TypeError，误用不会悄悄得出错的结论。

**比较一律按墙钟。** 期限是别的机器也要拿来比较的时刻，单调时钟在系统休眠时不走；job 自己的预算同按墙钟，前台与后台的截止时刻
才是同一个算法（ADR 0054 决策二「检查用墙钟」一段）。停止等待、排空这些时长不进记录，仍按单调时钟计，不在这里。

「已过」一律指严格晚于，与 job 预算到点的判断（当前时刻大于截止时刻）同一取法。

期限之后还有一个时刻：期限加 300 秒（`overdue_at`）。可以处置一个 run 的条件（ADR 0054 决策六，判断是 `past_overdue`）与隧道边缘的
到点拒绝（ADR 0051 决策 13「边缘策略」）都取它，code 里只有这一处算法，两处不各自加 300 秒。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Final, Literal

from gherkai_core.model import RunMeta
from gherkai_core.serialize import instant_from_iso

# 停止启动的提前量（秒）：当前时刻已过 deadline_at 减去它，就不再启动新的 job，同一个 job 的重试也不再启动。从发出启动到 job
# 真正开始执行需要时间，卡着期限启动的 job 来不及被正常停止。
STOP_START_LEAD_S = 60.0

# 期限之后的余量（秒）：给时钟偏差与仍在的推进器按期限自己结束留出余地，不是收尾时长的上界（ADR 0054 决策六）。
OVERDUE_MARGIN_S: Final = 300.0

# 执行中的 job 被截断时起作用的是哪一个时刻：job 自己的墙钟预算（budget），还是 run 的期限（deadline）。终结函数据它判定内容不完整的
# 超时 job：被预算截断的记 error 加 timeout，被期限截断的记 aborted（`project.finalize_job`）。
TimeoutCause = Literal["budget", "deadline"]


def system_wall_clock() -> datetime:
    """系统墙钟的当前时刻（UTC）。调度循环的墙钟由组合根注入，未注入时取它；core 的其余部分不读时钟。"""
    return datetime.now(timezone.utc)


def deadline_of(meta: RunMeta) -> datetime:
    """运行定义里的期限，解析成带时区的 datetime。读 definition 时已核过它是带时区的 ISO 时刻，这里与那次校验共用同一处解析；
    直接构造、没有经过读端的 RunMeta 带了读不出的值时同样抛 ValueError。"""
    return instant_from_iso(meta.deadline_at)


def stop_start_at(deadline: datetime) -> datetime:
    """停止启动的时刻：期限减去提前量。"""
    return deadline - timedelta(seconds=STOP_START_LEAD_S)


def past_stop_start(now: datetime, deadline: datetime) -> bool:
    """当前时刻是否已过停止启动的时刻。已过时不再启动新的 job，也不再重试；还有没有启动的 job 时，run 由执行方自己到期这条来路的
    结束写结束。"""
    return now > stop_start_at(deadline)


def past_deadline(now: datetime, deadline: datetime) -> bool:
    """当前时刻是否已过期限本身。执行中的 job 的截止时刻以期限封顶，各 job 是否到点按 `job_cutoff` 给出的时刻判断；本函数供不看
    具体 job 的判断使用。"""
    return now > deadline


def overdue_at(deadline: datetime) -> datetime:
    """期限加 300 秒（`OVERDUE_MARGIN_S`）：处置条件里的「已过期限加 300 秒」与隧道边缘到点拒绝的时刻都是它。"""
    return deadline + timedelta(seconds=OVERDUE_MARGIN_S)


def past_overdue(now: datetime, deadline: datetime) -> bool:
    """当前时刻是否已过期限加 300 秒（严格晚于 `overdue_at`）：可以处置一个 run 的两个条件之一（ADR 0054 决策六）。处置方各读自己的
    墙钟，这个判断只看传入的时刻。"""
    return now > overdue_at(deadline)


@dataclass(frozen=True)
class JobCutoff:
    """一个 job 的截止时刻与起作用的那一方。"""

    at: datetime
    by: TimeoutCause


def job_cutoff(claimed_at: datetime, timeout_s: float, deadline: datetime) -> JobCutoff:
    """job 的截止时刻：认领时刻加它的墙钟预算，与期限取较早的一个；两者相等时算 job 自己的预算到点。

    认领时刻是认领方在发出认领的那次写之前取的墙钟（没有记录的执行在同一位置取、不写），同一个 job 的重试共享这个截止时刻、不另外
    延长。截止时刻只由认领时刻、预算与期限这三个已经记下的值算出，前台与后台按同一个算法得到同一个结论，不需要另记实际是哪一个
    起了作用：超时的判定与说明由 `by` 决定，见 `project.finalize_job` 的 timeout_cause。"""
    own = claimed_at + timedelta(seconds=timeout_s)
    if own <= deadline:
        return JobCutoff(at=own, by="budget")
    return JobCutoff(at=deadline, by="deadline")
