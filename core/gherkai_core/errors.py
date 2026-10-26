"""core 的类型化异常（ADR 0028）。

放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在 adapter 里会让
core 反依赖 adapter（违反 ports.py 六边形「adapter 一律组合根注入」）。adapter 抛、core 接。
"""
from __future__ import annotations


class WorkerExitError(RuntimeError):
    """worker 进程以非零退出码结束（ADR 0024「退出码约定」/ 0034 机制二「退出信息」）。

    `wire.raise_for_worker_exit` 把非零退出码翻成本异常（两个 Engine adapter 共用），`exit_code` 带原码：正码是 worker 自报
    （崩溃 / 会话清理失败的 1 / 网络故障的 80），负码是被信号强杀（SIGKILL 为 -9）。终结函数据此判「退出码非零」一行，
    不再从消息文本里解析退出码。
    """

    def __init__(self, exit_code: int, message: str) -> None:
        super().__init__(message)
        self.exit_code = exit_code


class WorkerNetworkError(WorkerExitError):
    """worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。

    `wire.raise_for_worker_exit` 把该退出码翻成本异常（两个 Engine adapter 共用）；schedule 据此把 job 记 error_type="network_error"，
    并在「会话未起（零 step_done）」时选择性重试整个 job。是 WorkerExitError 的子类（exit_code 恒为网络故障退出码）。
    """

    def __init__(self, message: str, exit_code: int = 80) -> None:
        super().__init__(exit_code, message)


class DefinitionContractError(ValueError):
    """definition 的结构违约（ADR 0048 决策 3）：非桌面目标没有设备请求、应用条目不完整、设备请求字段不成对等。
    写 definition 之前（组合根）与推进器读 definition 时各核一次；plan 形态的 Job 不走它（那一形态本来就没有设备请求）。"""


class FeatureContractError(ValueError):
    """用例契约违约（feature 写法或配置违约），拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。
    按「是什么」命名而不按「在哪一步被发现」命名：parse 与 scope 两层都会抛，run 与 plan 都会遇到，不专属 plan 阶段。

    定义在此（而非 scope.py）：parse 与 scope 两层都会抛（parse 抛会与 scope→parse 的依赖成环），
    共享错误类型归 errors.py（同 WorkerNetworkError 的安置理由）。scope.py re-export 保既有 import 路径。
    """
