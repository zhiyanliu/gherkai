"""RetryingResultStore：本机推进器的判定存储，保存失败时退避重试（ADR 0030 决定三「保存明细失败」条）。

本机的组合根在 `LocalResultStore` 外面套这一层：前台 `run`、后台推进进程与 `status --wait` 接力都经同一个装配入口拿到它。推进步骤
（`reconcile.tick`）与落库服务（`persist.RunPersistence`）本身没有等待；云端的组合根不套，云端保存失败让这次调用失败，由流的重试或
之后的触发重做。不放进推进步骤或 S3 adapter：两者都由云端共用，那里的等待关不掉。

前台在落库服务的锁内保存，重试连同等待也在锁内：停手信号的发布与「先看信号、再存明细」仍在同一把锁里。代价是重试期间别的 worker 线程
的认领与执行中的写、调度循环对期限与中断的处置最多推迟约 7 秒，只在判定存储写不进时出现。
"""
from __future__ import annotations

import logging
import time
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gherkai_core.model import JobResult
    from gherkai_core.ports import ResultStore

logger = logging.getLogger(__name__)

# 首次保存失败之后依次等这几秒各再保存一次：首次加三次重试，共四次尝试、共等 7 秒
SAVE_RETRY_DELAYS_S: tuple[float, ...] = (1.0, 2.0, 4.0)


class RetryingResultStore:
    """保存失败时按 1、2、4 秒退避再保存，每次都用调用方给出的同一个标识；读与探活原样转交给被包住的判定存储。

    只对 OSError 重试：本机文件存储的写入失败（磁盘满、没有写权限、目录被删除）都表现为 OSError，别的异常是 code 的缺陷，原样抛出、
    不重试。首次加三次重试仍失败即抛出最后那个异常。每次重试之前在日志里留一句警告（前台没有配置 logging 时经 `logging.lastResort` 出现在
    stderr 上，后台推进进程的 stderr 进它的日志）。同一个标识再存一次即覆盖，前一次尝试若已写成，后一次写下的内容相同。
    """

    def __init__(self, inner: ResultStore, *, delays_s: Sequence[float] = SAVE_RETRY_DELAYS_S,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self._inner = inner
        self._delays_s = tuple(delays_s)
        self._sleep = sleep

    def save_job_result(self, run_id: str, result_id: str, job: JobResult) -> None:
        for delay in self._delays_s:
            try:
                self._inner.save_job_result(run_id, result_id, job)
                return
            except OSError as e:
                logger.warning("job %s 的判定明细没有存下（%s），%g 秒后重试", job.scope_id, e, delay)
                self._sleep(delay)
        self._inner.save_job_result(run_id, result_id, job)  # 最后一次：失败即原样抛出

    def load_job_result(self, run_id: str, result_id: str) -> JobResult | None:
        return self._inner.load_job_result(run_id, result_id)

    def preflight(self) -> None:
        self._inner.preflight()
