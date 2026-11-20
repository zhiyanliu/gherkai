"""判定明细的点名（ADR 0030 决定三「点名」条）：一次保存的标识怎样生成，读者怎样取被点名的那一份。

- `new_result_id`：写入方每次保存明细之前生成一个标识（前台落库服务在看过停手信号之后，后台推进步骤为每个已有结果的 job 各生成一个），
  明细存成带这个标识的一份，记下这个 job 终态的那次写在它的记录里写下同一个标识。本机对同一次保存的重试沿用调用方给出的标识，重试本身
  不生成标识。
- `load_named_details`：读者唯一的读法。前台收尾、后台报告与 explain 都先读运行态，再经这里按各 job 点名的标识取明细；端口不提供列举，
  没被点名的明细不读。

本模块不取时钟、不写任何东西；读明细的 I/O 经调用方给出的判定存储。
"""
from __future__ import annotations

import secrets
from collections.abc import Iterable
from typing import TYPE_CHECKING

from gherkai_core.errors import NamedDetailMissing

if TYPE_CHECKING:
    from gherkai_core.model import JobResult, JobState
    from gherkai_core.ports import ResultStore


def new_result_id() -> str:
    """一次保存判定明细的标识：16 个小写十六进制字符（64 位随机数），同一个 run 的各次保存之间不重复。

    取 64 位：键里已经带 run_id，标识只需在同一个 run 的各次保存之间不重复，单个 run 的保存次数下碰撞概率可以忽略；运行态的每个 job
    条目都带它，单条运行态记录按 job 数计容量（ADR 0034 机制三②），标识越短、容纳的 job 越多。只用小写字母与数字：本机文件名可能落在
    不区分大小写的文件系统上，大小写不同的两个标识在那里会落成同一个文件。标识不编码 scope_id 或时刻，读者从运行态取 scope。"""
    return secrets.token_hex(8)


def load_named_details(run_id: str, jobs: Iterable[JobState], result_store: ResultStore) -> dict[str, JobResult]:
    """jobs 里各 job 被点名的那一份判定明细，按 jobs 的次序给出 scope_id → JobResult（ADR 0030 决定三「点名」条）。

    只读带标识的 job，按标识取；没带标识的（由结束写结束、未结束）不读、不在结果里。分辨「由执行结果结束」与「由结束写结束」只看有没有
    标识，不看说明、不看存储里有没有明细。

    被点名而读不到时抛 `NamedDetailMissing`（OSError 的子类），不把这个 job 当作没有明细：这个标识下没有明细，或读回的那一份的 scope_id
    与运行态里的这个 job 不同（不把别的 job 的明细附上）。正常写序下被点名的那一份必已存下、且属于这个 job，读不到只会是存放处或运行
    记录被外部删改。判定存储的别的读取失败（权限、网络、内容损坏）原样抛出，不改写成这个异常。"""
    details: dict[str, JobResult] = {}
    for js in jobs:
        if js.result_id is None:
            continue
        jr = result_store.load_job_result(run_id, js.result_id)
        if jr is None:
            raise NamedDetailMissing(run_id, js.scope_id, js.result_id)
        if jr.scope_id != js.scope_id:
            raise NamedDetailMissing(run_id, js.scope_id, js.result_id, found_scope_id=jr.scope_id)
        details[js.scope_id] = jr
    return details
