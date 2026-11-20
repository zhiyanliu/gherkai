"""在一个真实进程里执行一次建成的 `submit --expose-local`（本机或云端后端），供 `test_tunnel_cli.py` 里「开始写出 run 标识之后到达的
Ctrl-C」两条用例启动（ADR 0035 决策 3）。

用法：`python _submit_driver.py <local|cloud> <工作目录> <放行描述符>`；退出码是 `main` 的返回值。

提交进程是这个真实进程，它收到的 SIGINT 是真实的；其余照进程内用例的替身：后台进程是 `_inline_children` 的线程替身（真实管道，线程里
执行真实的主体），推进换成什么都不做的函数、不起 worker；能力自述用 `_fake_worker` 的替身；隧道服务是假的，真实的隧道组件被导入即
失败；云端存储是 `test_backend_cloud` 的假句柄。不联网、不连 AWS。run 标识固定为 `test_tunnel_cli.FIXED_RUN_ID`。

本机后端建 run 的锁与边界检查是真实的：这个进程里没有 cli 测试的自动夹具，持有者在这里显式构造成生产用的 `HoldUntilExit`（锁随
本进程退出释放），边界检查取宿主真实的文件系统类型，所以启动它的用例带 `real_filesystem` 标记。

标准输出换成直接写本进程 fd 1 的流：写出第一个换行之后停住，直到从放行描述符读到一个字节或文件结束。启动它的用例在这段时间里读到
那一行、对本进程发 SIGINT，再放行，于是信号落在 run 标识已经写进管道、`print` 还没有返回的那一刻。
"""
from __future__ import annotations

import os
import signal
import sys
import tempfile
from pathlib import Path


class _HoldAfterFirstLine:
    """写到 fd 1 的标准输出；写出第一个换行之后在放行描述符上等待。"""

    def __init__(self, hold_fd: int) -> None:
        self._hold_fd = hold_fd
        self._held = False

    def write(self, s: str) -> int:
        data = s.encode("utf-8")
        while data:
            data = data[os.write(1, data):]
        if not self._held and "\n" in s:
            self._held = True
            os.read(self._hold_fd, 1)
        return len(s)

    def flush(self) -> None:
        pass


def _no_real_sdk():
    raise AssertionError("不应导入真实的隧道组件")


def _feature(work: Path) -> Path:
    f = work / "t.feature"
    f.write_text('Feature: t\n  Scenario: s\n    When "打开 http://localhost:3000/login"\n', encoding="utf-8")
    return f


def main(backend: str, work: Path, hold_fd: int) -> int:
    signal.signal(signal.SIGINT, signal.default_int_handler)  # 不随启动方的处置：Ctrl-C 即 KeyboardInterrupt

    import pytest

    import gherkai_cli.__main__ as m
    from gherkai_core.adapters.run_store import run_dir
    from gherkai_runtime import compose, detached
    from gherkai_runtime import tunnel as gtunnel

    from _fake_worker import fake_query_capabilities
    from _inline_children import InlineChildren
    from test_backend_cloud import _patch_cloud_handles
    from test_tunnel_cli import FIXED_RUN_ID, ORIGIN, FakeTunnel

    holder = run_dir.HoldUntilExit()
    mp = pytest.MonkeyPatch()
    mp.setattr(compose, "process_lock_holder", lambda: holder)
    mp.setattr(compose, "query_capabilities", fake_query_capabilities)
    mp.setattr(gtunnel, "_import_sdk", _no_real_sdk)
    mp.setitem(gtunnel.PROVIDERS, "ngrok", FakeTunnel().provider)
    mp.setattr(compose, "new_run_id", lambda at=None: FIXED_RUN_ID)
    mp.setattr(detached, "advance_local_run", lambda advancer, meta, **kw: None)
    mp.setattr(tempfile, "tempdir", str(work))  # 守护进程的日志落在工作目录
    feature = str(_feature(work))
    if backend == "local":
        argv = ["submit", feature, "--report-dir", str(work / "reports"), "--region", "us-east-1"]
    else:
        _patch_cloud_handles(mp, [])
        argv = ["submit", feature, "--backend", "cloud", "--ddb-table", "T", "--s3-bucket", "B", "--region", "us-east-1"]
    children = InlineChildren(mp)
    sys.stdout = _HoldAfterFirstLine(hold_fd)
    try:
        rc = m.main([*argv, "--expose-local", ORIGIN])
        children.settle()
    finally:
        children.close()
        mp.undo()
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], Path(sys.argv[2]), int(sys.argv[3])))
