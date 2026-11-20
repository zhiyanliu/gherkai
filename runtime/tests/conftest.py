"""runtime 测试的公共夹具。

**测试从不起真实的隧道**：开发环境与 CI 都装了隧道组件（ngrok 的 SDK），误调用会联网、在 ngrok 账号上建会话。自动夹具把
`tunnel._import_sdk` 换成一个记录调用并抛错的函数：生产代码只经它导入 SDK，被调用即说明某个用例走到了真实的 SDK；抛出的
AssertionError 可能被调用方的宽泛异常处理吞掉，所以收尾时另按调用次数判失败。夹具本身不导入 SDK。

要用假 SDK 的用例经 `NgrokTunnel(load_sdk=...)` 注入，或自己对 `tunnel._import_sdk` 打桩（覆盖这里的替身）。同时去掉环境变量
NGROK_AUTHTOKEN：用例的结果不随运行测试的机器有没有令牌而变。

**本机 run 目录**（ADR 0054 决策三、四）：
- `lock_holder`：要建 run 的 `LocalRunStore` 与 `compose.build_local_stores` 传入它。它收下持生命期锁的描述符、用例结束时关闭；
  生产用的持有者没有放开锁的方法。
- `_host_independent_filesystem_type`（autouse）：把边界检查取文件系统类型的那一步换成本平台清单的第一项，结论不依赖宿主的
  文件系统。带 `real_filesystem` 标记的用例不替换；本平台不在清单里、或宿主的系统临时目录所在的类型取到了而不在清单里时跳过，
  判断不了时照常执行（那多半是取法本身坏了，跳过会把它藏起来）。规则与 core 的测试夹具相同。
"""
from __future__ import annotations

import os
import sys

import pytest

from gherkai_core.adapters.run_store import run_dir
from gherkai_runtime import tunnel


@pytest.fixture(autouse=True)
def _no_real_tunnel_sdk(monkeypatch):
    calls: list[str] = []

    def _guarded_import_sdk():
        calls.append("import")
        raise AssertionError("测试不应导入真实的隧道 SDK：请经 NgrokTunnel(load_sdk=...) 注入假 SDK")

    monkeypatch.setattr(tunnel, "_import_sdk", _guarded_import_sdk)
    monkeypatch.delenv("NGROK_AUTHTOKEN", raising=False)
    yield
    if calls:
        pytest.fail(f"用例导入了真实的隧道 SDK（{len(calls)} 次）：请经 NgrokTunnel(load_sdk=...) 注入假 SDK")


class ClosingLockHolder:
    """测试用的持有者：记下收到的描述符，用例结束时由夹具关闭（锁随之放开）。"""

    def __init__(self) -> None:
        self.fds: list[int] = []

    def hold(self, fd: int) -> None:
        self.fds.append(fd)

    def close_all(self) -> None:
        for fd in self.fds:
            try:
                os.close(fd)
            except OSError:
                pass
        self.fds.clear()


@pytest.fixture
def lock_holder():
    holder = ClosingLockHolder()
    yield holder
    holder.close_all()


@pytest.fixture(autouse=True)
def _host_independent_filesystem_type(request, monkeypatch):
    if request.node.get_closest_marker("real_filesystem") is not None:
        if sys.platform not in run_dir.ALLOWED_FILESYSTEMS:
            pytest.skip(f"本机后端在 {sys.platform} 上不可用，跳过真实文件系统的用例")
        tmp = request.getfixturevalue("tmp_path")
        check = run_dir.check_report_dir(tmp)
        if check.verdict is run_dir.Boundary.OUTSIDE:
            pytest.skip(f"宿主的系统临时目录 {tmp} 所在的文件系统是 {check.fs_type}，不在本平台的清单里，跳过真实文件系统的用例")
        return
    allowed = run_dir.ALLOWED_FILESYSTEMS.get(sys.platform)
    if allowed:
        monkeypatch.setattr(run_dir, "filesystem_type", lambda fd: allowed[0])
