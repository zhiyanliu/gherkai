"""进程级真信号回归哨兵（ADR 0024 flag-only 中断模型，P1）。

补上 test_interrupt_model.py（拦 signal.signal 手调 handler、不发真信号）和 test_subprocess_engine.py
（用 core 的 echo_worker、非 novaact 真 handler）之间的**唯一空白**：真进程收到真 SIGTERM/SIGINT →
**run_scope 的真 handler `rs._on_signal`**（fixture 装的是同一函数对象，非手抄副本）被 CPython 在字节码
边界真调用 → 协作退 → grace 内 rc=0、没被 SIGKILL。

范式对称 core/tests/test_subprocess_engine.py 的 test_adapter_stop_hanging_worker：
真 Popen + 就绪握手 + 真 send_signal + wait(timeout) + 断言 (rc==0 且未超时被强杀)。
零 AWS、零 greenlet、零 chromium、~秒级——默认单测跑（无 marker）。

**这个哨兵护的是「rs._on_signal 保持 flag-only 协作语义」**：fixture 装的是真 `rs._on_signal`，故若有人把
它从「只 _stop.set()」改回「raise」（即撞 playwright greenlet 切换区致死循环卡死的 raise 模型根因，见 ADR 0024 被拒方案），信号在 fixture 主循环里
raise 未捕获异常 → 进程非 0 退出 / 行为改变 → 本测试 rc==0 断言失败、可见（此哨兵的关键设计：原先 fixture 装
手抄副本、改真 handler 测试也不红、是假哨兵；改装真 `rs._on_signal` 才有护栏效力）。**边界诚实说明**：fixture 跑的是无 greenlet 的 fake act
循环，故它验的是「handler 语义 + 协作退范式」，**不复现真 greenlet 卡死本身**（signal-raise 撞
greenlet 切换区致死循环那条路概率性触发、不宜断言，机制见 ADR 0024 被拒方案）；真 greenlet 环境的
干净退（flag-only 改造）已由真 spawn worker + 真 chromium/greenlet 的一次性真跑验证（见 ADR 0024
终止契约）。scenario/投票循环的
_stop 检查回归由 test_interrupt_model.py 的单测覆盖，不靠本进程测试。
"""
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

_FIXTURE = str(Path(__file__).resolve().parent / "fixtures" / "interrupt_worker.py")
_GRACE = 5.0  # 宽松常量：确认 worker 在此内响应信号（非精细标定 grace 预算，那是 ADR 0024 的数字）


def _spawn_and_wait_ready() -> subprocess.Popen:
    """spawn fixture worker，阻塞等 READY 握手（handler 已装、进循环）后返回。"""
    proc = subprocess.Popen(
        [sys.executable, _FIXTURE],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    # 就绪握手：等 handler 装好再发信号（CPython signal 在字节码边界执行，早发会丢/行为不定）。
    assert proc.stderr is not None
    line = proc.stderr.readline()
    assert line.strip() == "READY", f"fixture worker 未就绪握手，得到：{line!r}"
    return proc


@pytest.mark.parametrize("sig", [signal.SIGTERM, signal.SIGINT])
def test_worker_cooperative_stop_on_signal(sig):
    """真 SIGTERM/SIGINT → run_scope flag-only handler 协作退 → grace 内 rc=0、非 SIGKILL。"""
    proc = _spawn_and_wait_ready()
    t0 = time.monotonic()
    proc.send_signal(sig)
    try:
        rc = proc.wait(timeout=_GRACE)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        pytest.fail(
            f"worker 收到 {sig!r} 后未在 {_GRACE}s 内退出（疑似回退 raise 模型撞 greenlet 卡死）"
        )
        return  # unreachable（pytest.fail 必抛）；仅为静态分析确定 rc 已绑定
    elapsed = time.monotonic() - t0
    # flag-only 协作退 = rc 0；被 SIGKILL 强杀会是 -9，默认信号处置会是 -sig。
    assert rc == 0, f"期望协作干净退(rc=0)，实得 rc={rc}（负值=被信号杀，非协作退）"
    assert elapsed < _GRACE, "worker 应即时响应信号、远早于 grace 上限"


def test_worker_runs_until_signaled():
    """反向确认：没有信号时 worker 不会自己退（证明上面的退出确由信号触发、非巧合）。"""
    proc = _spawn_and_wait_ready()
    assert proc.poll() is None  # 就绪后仍在跑
    time.sleep(0.3)
    assert proc.poll() is None, "无信号时 worker 不应自行退出"
    proc.send_signal(signal.SIGTERM)
    proc.wait(timeout=_GRACE)
