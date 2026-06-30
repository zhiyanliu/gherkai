"""Nova Act 侧引擎路由（G2，ADR 0019）：只跑属于本引擎的 scenario。

规则：scenario 标了 @engine:novaact、或整组未标 engine（默认） → 本引擎跑；
      标了 @engine:midscene → 跳过（交给 Midscene runner）。

pytest-bdd 默认把每个 tag 转 pytest.mark.<tag>，但带冒号的 @engine:novaact 不是合法 marker 名、
也不好用 -m 过滤。故 override pytest_bdd_apply_tag 把它规范成标准 marker，并用 fixture 据 tag 路由 skip。
"""
from __future__ import annotations

import pytest

THIS_ENGINE = "novaact"


def pytest_configure(config):
    """动态注册 tag 转出的 marker（engine_*/scope_*），消除 PytestUnknownMarkWarning。
    marker 名来自 .feature 的 @engine:/@scope: tag，无法预先穷举，故用前缀通配声明。"""
    config.addinivalue_line("markers", "engine_midscene: @engine:midscene tag")
    config.addinivalue_line("markers", "engine_novaact: @engine:novaact tag")
    # scope_* 名动态（@scope:<任意>），声明一个通用说明即可
    config.addinivalue_line("markers", "scope_: @scope:<name> tag（动态名 scope_<name>）")


def pytest_bdd_apply_tag(tag, function):
    """把 @engine:<x> / @scope:<x> 这类带值 tag 规范成合法 marker（冒号→下划线）。"""
    safe = tag.replace(":", "_").replace("-", "_")
    mark = getattr(pytest.mark, safe)
    return mark(function)


def _engine_of(node) -> str | None:
    """从 scenario 节点的 marker 里取 @engine:<x> 的值（None=未标）。"""
    for m in node.iter_markers():
        if m.name.startswith("engine_"):
            return m.name[len("engine_"):]
    return None


@pytest.fixture(autouse=True)
def _route_by_engine(request):
    """非本引擎的 scenario 直接 skip（本引擎 = novaact 或未标 engine=默认）。"""
    engine = _engine_of(request.node)
    if engine is not None and engine != THIS_ENGINE:
        pytest.skip(f"scenario @engine:{engine} 非本引擎（{THIS_ENGINE}），跳过")
