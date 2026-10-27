"""命令行的进度与诊断输出（ADR 0047）：一个函数，供 `__main__` 与各编排模块共用。"""
from __future__ import annotations

import sys


def progress(*args, **kwargs) -> None:
    """进度/诊断输出 → stderr（业界惯例：stdout 留给该命令的核心产出/数据，stderr 给所有诊断）。

    这样 `gherkai run … --json > r.json` 拿到纯净 JSON、`gherkai run … > summary.txt` 拿到纯净文本汇总，
    进度（plan/event/run_id/RunReport 落点）照样在终端可见、不污染被重定向的主输出。

    **stderr 上的进度与诊断行不上色（即终端默认前景色）是有意约定**：默认色专属 cli main/core 的进度输出
    （含 `[core …:event]`），与 worker 透传行的调色板物理不相交——worker 前缀调色板有意排除白/默认色，也排除红绿
    （红绿留给判定语义；见 subprocess_engine._ANSI_COLORS），故并发批量运行期间「core 说的」恒默认色、「worker 透传的」
    恒有色，一眼可分。stdout 上的汇总树与表格按 ADR 0047 使用语义颜色，但只在批量运行结束后输出、不与透传行交错；
    给 stderr 进度行加色前先考虑这条约定。
    """
    kwargs.setdefault("file", sys.stderr)
    print(*args, **kwargs)
