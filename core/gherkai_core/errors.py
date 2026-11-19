"""core 的类型化异常（ADR 0028）。

放 core 而非 adapter：schedule 要 catch 它做 network 重试判定，若定义在 adapter 里会让
core 反依赖 adapter（违反核心注入接口「adapter 一律由组合根注入」的约定，见 ports.py 模块头）。adapter 抛、core 接。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gherkai_core.model import RunState


class WorkerExitError(RuntimeError):
    """worker 进程以非零退出码结束（ADR 0024「退出码约定」/ 0034 机制二「退出信息」）。

    子进程 adapter 经 `wire.raise_for_worker_exit` 把非零退出码翻成本异常（ADR 0028「关键不变量:退出码携带 network 信号」节），
    `exit_code` 带原码：正码多为 worker 自报（崩溃 / 会话清理失败的 1、Nova worker 加载使用方 steps 失败的 2、网络故障的 80）；
    被信号强杀时为负码（SIGKILL 为 -9）。云端后端的退出码不经本异常：退出观察者把它写成退出记录，推进器在投影里交给终结函数
    （缺退出码时落的平台侧哨兵与归因见 ADR 0034 机制二「退出码缺失」条）。

    终结函数据有类型的 `exit_code` 判「退出码非零」一行，不从消息文本里解析；消息由终结函数按码给出，异常消息不进 job 的说明。
    """

    def __init__(self, exit_code: int, message: str) -> None:
        super().__init__(message)
        self.exit_code = exit_code


class WorkerNetworkError(WorkerExitError):
    """worker 以「网络/SSL 瞬时故障」专用退出码退出（建连失败、重试耗尽，ADR 0028）。

    子进程 adapter 经 `wire.raise_for_worker_exit` 把该退出码翻成本异常；schedule 据此把 job 记 error_type="network_error"，
    并在「会话未起（零 step_done）」时选择性重试整个 job。是 WorkerExitError 的子类（exit_code 恒为网络故障退出码）。
    """

    def __init__(self, message: str, exit_code: int = 80) -> None:
        super().__init__(exit_code, message)


class UnsupportedDefinitionSchema(ValueError):
    """definition 的结构版本不是本读端认的那一个（ADR 0037 决策 7）。

    读端只认当前一个结构版本：高于它表示写端更新（读端该升级），低于它或缺键表示写端更旧（用写出它的那个版本读，或重新提交）。
    读端不为任何旧版本留分支或缺省，结构变化一律靶在这一个比较上。`found` / `supported` 供调用点写出两边的版本号，
    `cli_version` 是写出这份 definition 的命令行工具版本（definition 自记、只记不比），有则用来点名「由哪个版本写出」。
    """

    def __init__(self, found: int, supported: int, *, cli_version: str | None = None) -> None:
        by = f"（由 gherkai {cli_version} 写出）" if cli_version else ""
        super().__init__(f"definition 的结构版本为 {found}，本读端只认 {supported}{by}")
        self.found = found
        self.supported = supported
        self.cli_version = cli_version


class DefinitionContractError(ValueError):
    """definition 的结构违约（ADR 0048 决策 3）：非桌面目标没有设备请求、应用条目不完整、设备请求字段不成对等。
    写 definition 之前（组合根）与推进器读 definition 时各核一次；plan 形态的 Job 不走它（那一形态本来就没有设备请求）。"""


class RunAlreadyEnded(RuntimeError):
    """前台执行收尾时 run 级已是终态：本次执行结束之前，别处已把这个 run 记为已结束（ADR 0054 决策五「执行方服从记录」）。

    `RunPersistence.finalize` 的收尾条件写没有写成时抛出：已有的终态不被覆盖，报告也不生成（报告从本次执行的结果派生，会与
    记录里的终态矛盾）。本次执行已得出的各 job 判定此前已逐个写入。`recorded` 是收尾写不成之后读回的运行态，调用方据它说明
    记录里的状态与原因（run 级 `message`）；这次读回失败时为 None，结论不变，只是说明里给不出记录的状态。
    """

    def __init__(self, run_id: str, recorded: RunState | None) -> None:
        state = f"（{recorded.status.value}）" if recorded is not None else ""
        super().__init__(f"run {run_id} 在本次执行结束之前已被记为已结束{state}，本次的结果没有覆盖它")
        self.run_id = run_id
        self.recorded = recorded


class FeatureContractError(ValueError):
    """用例契约违约（feature 写法或配置违约），拒绝运行（ADR 0019/0025）：engine 冲突、多 @scope 值、步骤关键字判不出等。
    按「是什么」命名而不按「在哪一步被发现」命名：parse 与 scope 两层都会抛，run 与 plan 都会遇到，不专属 plan 阶段。

    定义在此（而非 scope.py）：parse 与 scope 两层都会抛（parse 抛会与 scope→parse 的依赖成环），
    共享错误类型归 errors.py（同 WorkerNetworkError 的安置理由）。scope.py re-export 保既有 import 路径。
    """
