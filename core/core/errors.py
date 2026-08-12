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


class PlanError(ValueError):
    """feature 写法/配置违约，拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。

    定义在此（而非 scope.py）：parse 与 scope 两层都会抛（parse 抛会与 scope→parse 的依赖成环），
    共享错误类型归 errors.py（同 WorkerNetworkError 的安置理由）。scope.py re-export 保既有 import 路径。
    """
