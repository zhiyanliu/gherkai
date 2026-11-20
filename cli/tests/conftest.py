"""cli 测试的公共夹具。

**默认不 spawn 真 worker 问能力自述**：`run`/`submit` 的运行前检查、`list-deterministic` 的清单、doctor 的加载
计数、grace 下限全取同一份能力自述对象（`--capabilities`，ADR 0036「5.」/ ADR 0024「引擎自报下限」）。若让每个
用例真去问，用例就依赖「运行测试这台机器装了哪个引擎」——本机装了 Nova 就绿、干净环境以退出码 2 结束（「绿≠对」的经典形态：
结论靠环境、不靠被测逻辑）。故 autouse 只把**自述查询**那一层换成确定性假值，`compose.engine_min_grace` 的
缓存复用、cli 侧的取 max / 退出码 2 分流照真实运行；要验「查不到该怎样」的用例自己 monkeypatch 回去。

替身仍**先过定位链**（真 `resolve_worker_cmd`）：查询本来就以「本机有这个 worker」为前提，跳过这步会把
「本机没装该引擎 → 跳过或退出码 2」那条分支变成测不出来的死路（doctor 的跳过情形正是它），且让本该跳过的用例继续
往下走去碰真 AWS。故只换「问 worker」那一跳、不换「找 worker」那一跳；用例用 `_fake_locator` 之类的替身把
定位链摆成想要的形状，这里跟着它走。
"""
from __future__ import annotations

import pytest

from gherkai_runtime import compose

from _fake_worker import FAKE_DETERMINISTIC_STEPS, FAKE_MIN_GRACE_S, FAKE_MODEL_ID


@pytest.fixture(autouse=True)
def _stub_engine_capabilities(monkeypatch):
    def fake_query_capabilities(engine: str, *, steps_dir=None, timeout_s: float = 60.0) -> dict:
        if engine not in FAKE_MIN_GRACE_S:
            raise ValueError(f"未知引擎 {engine!r}")  # 同 compose 定位链的引擎名校验
        compose.resolve_worker_cmd(engine)  # 定位链照真走：miss → WorkerNotFoundError，同真查询的第一步
        caps = {"schema_version": 2, "engine": engine, "min_grace_s": FAKE_MIN_GRACE_S[engine],
                "targets": [{"device": "desktop", "ui_kinds": ["web"]}],  # 顶层 targets 必有（ADR 0049 决策 2）
                "deterministic_steps": [dict(e) for e in FAKE_DETERMINISTIC_STEPS],
                "model_id": FAKE_MODEL_ID[engine],
                compose.SESSION_WARMUP_KEY: True}  # 两个真 worker 都声明会话预热支持（ADR 0051 决策 13）
        # 真实现自己会按（引擎, steps 目录）缓存这份对象；替身照同一键写一份，好让「本机 run 每引擎只问一次」
        # 那条**生产行为**（engine_min_grace 复用已有自述、不再问 worker）在替身之上照样被测到。
        compose._CAPABILITIES_CACHE.setdefault((engine, None if steps_dir is None else str(steps_dir)), caps)
        return caps

    monkeypatch.setattr(compose, "query_capabilities", fake_query_capabilities)
    # 进程内缓存跨用例泄漏 → 上一个用例的值（或真 worker 的值）污染下一个；两头都清。
    compose._CAPABILITIES_CACHE.clear()
    yield
    compose._CAPABILITIES_CACHE.clear()


@pytest.fixture(autouse=True)
def _no_real_tunnel_sdk(monkeypatch):
    """**测试从不起真实的隧道**：开发环境与 CI 都装了隧道组件（ngrok 的 SDK），误调用会联网、在 ngrok 账号上建会话。生产代码只经
    `tunnel._import_sdk` 导入 SDK（前置检查与起隧道都经它）：这里把它换成记录调用并抛错的函数，被调用即说明某个用例走到了真实的
    SDK；抛出的 AssertionError 可能被调用方的宽泛异常处理吞掉，所以收尾时另按调用次数判失败。夹具本身不导入 SDK。

    要隧道的用例把假的隧道服务登记进 `tunnel.PROVIDERS`，或经 `NgrokTunnel(load_sdk=...)` / 自己对 `tunnel._import_sdk` 打桩注入假
    SDK（覆盖这里的替身）。同时去掉环境变量 NGROK_AUTHTOKEN：用例的结果不随运行测试的机器有没有令牌而变。"""
    from gherkai_runtime import tunnel

    calls: list[str] = []

    def _guarded_import_sdk():
        calls.append("import")
        raise AssertionError("测试不应导入真实的隧道 SDK：请登记假的隧道服务，或经 NgrokTunnel(load_sdk=...) 注入假 SDK")

    monkeypatch.setattr(tunnel, "_import_sdk", _guarded_import_sdk)
    monkeypatch.delenv("NGROK_AUTHTOKEN", raising=False)
    yield
    if calls:
        pytest.fail(f"用例导入了真实的隧道 SDK（{len(calls)} 次）：请登记假的隧道服务，或经 NgrokTunnel(load_sdk=...) 注入假 SDK")


@pytest.fixture(autouse=True)
def _presentation_is_environment_independent(monkeypatch):
    """人读渲染（ADR 0047）不随运行测试的终端变化：固定关色、表格不按终端取宽——否则 `pytest -s` 在真实终端里会因 ANSI 与折行假红。"""
    from gherkai_runtime import textui
    monkeypatch.setattr(textui, "use_color", lambda: False)
    monkeypatch.setattr(textui, "output_width", lambda: textui.NO_WRAP_WIDTH)
