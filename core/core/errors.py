"""core 的类型化异常（ADR 0028）。

放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在 adapter 里会让
core 反依赖 adapter（违反 ports.py 六边形「adapter 一律组合根注入」）。adapter 抛、core 接。
"""
from __future__ import annotations


class WorkerNetworkError(RuntimeError):
    """worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。

    subprocess_engine 把该退出码翻成本异常；schedule 据此把 job 记 error_type="network_error"，
    并在「会话未起（零 step_done）」时选择性重试整个 job。
    """
