"""进程级信号测试的 fixture worker（ADR 0024 flag-only 中断模型，P1 回归哨兵）。

被 test_interrupt_process.py 真 spawn 成子进程，验证 **run_scope 真实的 flag-only handler**
在真进程收到真 SIGTERM/SIGINT 时：只置标志、协作式退出、干净退（rc=0），不卡死、不被 SIGKILL。

与 core/tests/fixtures/echo_worker.py 范式对称，但**关键区别**：echo_worker 装它自己的假 handler；
本 fixture **装 run_scope 的真 handler `rs._on_signal`（同一函数对象，非手抄副本）**——故若有人把
`rs._on_signal` 从 flag-only 改回 raise 模型（sync-over-greenlet + signal-raise 反模式致死循环卡死，见 ADR 0024
被拒方案），本进程测试会真变红（此前 fixture 装的是手抄的 handler 副本，即便真 handler 回退 raise 模型也不红，
是假哨兵）。跑一个 fake act 紧循环
（每轮顶检查 _stop）——不接 AgentCore、不 import Workflow 真建连、不连 AWS、无 greenlet（纯进程+信号层）。

就绪握手：装完 handler、进循环后往 stderr 打一行 READY——测试侧等到它再发信号
（CPython signal handler 在字节码边界执行，信号早于 handler 安装会丢/行为不定）。
"""
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # worker/ 根，import run_scope
import run_scope as rs


def main() -> int:
    rs._stop.clear()
    # 装 run_scope 的**真** handler（rs._on_signal 是模块级、非闭包）——回退 raise 模型时本测试真变红。
    signal.signal(signal.SIGTERM, rs._on_signal)
    signal.signal(signal.SIGINT, rs._on_signal)

    # 就绪握手：handler 已装、即将进循环 → 通知测试侧可以发信号了。
    sys.stderr.write("READY\n")
    sys.stderr.flush()

    # fake act 紧循环：模拟 worker 主流程在 act 边界安全点反复检查 _stop（无真 act、无 greenlet、无 AWS）。
    # 收到停止信号 → 协作式跳出 → 干净退（rc=0），对称 run_scope 的「安全点检测 → 正常 return 释放会话」。
    while not rs._stop.is_set():
        time.sleep(0.01)  # 让出 CPU；signal handler 在下个字节码边界置标志、本循环下轮即感知
    return 0  # 协作退出（flag-only）：rc=0；若回退 raise 模型撞 greenlet 会卡死→测试侧 SIGKILL 兜底可见


if __name__ == "__main__":
    sys.exit(main())
