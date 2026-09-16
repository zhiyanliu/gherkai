"""cli 测试的公共夹具。

**默认不 spawn 真 worker 问 grace 下限**：`run` 的下限现在向各引擎 worker 问（`--capabilities` 自述，
ADR 0024「引擎自报下限」）。若让每个 run 用例真去问，用例就依赖「跑测试这台机器装了哪个引擎」——本机装了
Nova 就绿、干净环境退 2（「绿≠对」的经典形态：结论靠环境、不靠被测逻辑）。故 autouse 只把**自述查询**那一层
换成确定性假值，`compose.engine_min_grace` 的契约校验与缓存、cli 侧的取 max / 退 2 分流照真跑；要验「查不到
该怎样」的用例自己 monkeypatch 回去（如 run 的自述失败档）。

替身仍**先过定位链**（真 `resolve_worker_cmd`）：查询本来就以「本机有这个 worker」为前提，跳过这步会把
「本机没装该引擎 → 跳过/退 2」那条分支变成测不出来的死路（doctor 的跳过档正是它），且让本该跳过的用例继续
往下走去碰真 AWS。故只换「问 worker」那一跳、不换「找 worker」那一跳；用例用 `_fake_locator` 之类的替身把
定位链摆成想要的形状，这里跟着它走。
"""
from __future__ import annotations

import pytest

from gherkai_runtime import compose

# 假 worker 自报的 grace 下限（秒）：值本身无所谓，只要两引擎不同、能看出「取 max」与「按引擎分别问」。
FAKE_MIN_GRACE_S = {"novaact": 150.0, "midscene": 31.0}


@pytest.fixture(autouse=True)
def _stub_engine_capabilities(monkeypatch):
    def fake_query_capabilities(engine: str, *, timeout_s: float = 60.0) -> dict:
        if engine not in FAKE_MIN_GRACE_S:
            raise ValueError(f"未知引擎 {engine!r}")  # 同 compose 定位链的引擎名校验
        compose.resolve_worker_cmd(engine)  # 定位链照真走：miss → WorkerNotFoundError，同真查询的第一步
        return {"schema_version": 1, "engine": engine, "min_grace_s": FAKE_MIN_GRACE_S[engine]}

    monkeypatch.setattr(compose, "query_capabilities", fake_query_capabilities)
    # 进程内缓存跨用例泄漏 → 上一个用例的值（或真 worker 的值）污染下一个；两头都清。
    compose._ENGINE_MIN_GRACE_CACHE.clear()
    yield
    compose._ENGINE_MIN_GRACE_CACHE.clear()
