"""runtime 测试的公共夹具。

**测试从不起真实的隧道**：开发环境与 CI 都装了隧道组件（ngrok 的 SDK），误调用会联网、在 ngrok 账号上建会话。自动夹具把
`tunnel._import_sdk` 换成一个记录调用并抛错的函数：生产代码只经它导入 SDK，被调用即说明某个用例走到了真实的 SDK；抛出的
AssertionError 可能被调用方的宽泛异常处理吞掉，所以收尾时另按调用次数判失败。夹具本身不导入 SDK。

要用假 SDK 的用例经 `NgrokTunnel(load_sdk=...)` 注入，或自己对 `tunnel._import_sdk` 打桩（覆盖这里的替身）。同时去掉环境变量
NGROK_AUTHTOKEN：用例的结果不随运行测试的机器有没有令牌而变。
"""
from __future__ import annotations

import pytest

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
