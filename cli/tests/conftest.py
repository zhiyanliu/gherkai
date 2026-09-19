"""cli 测试的公共夹具。

**默认不 spawn 真 worker 问能力自述**：`run`/`submit` 的运行前检查、`list-deterministic` 的清单、doctor 的加载
计数、grace 下限全取同一份能力自述对象（`--capabilities`，ADR 0036「5.」/ ADR 0024「引擎自报下限」）。若让每个
用例真去问，用例就依赖「运行测试这台机器装了哪个引擎」——本机装了 Nova 就绿、干净环境退 2（「绿≠对」的经典形态：
结论靠环境、不靠被测逻辑）。故 autouse 只把**自述查询**那一层换成确定性假值，`compose.engine_min_grace` 的
缓存复用、cli 侧的取 max / 退 2 分流照真实运行；要验「查不到该怎样」的用例自己 monkeypatch 回去。

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
# 假注册表清单：内容无所谓，只要形状对（pattern/description/example）、条数可数——用例断言的是「清单出自自述对象」。
FAKE_DETERMINISTIC_STEPS = [
    {"pattern": '打开 "(?P<url>[^"]+)"', "description": "打开某个地址", "example": '当 打开 "https://x"'},
    {"pattern": "页面地址匹配 \"(?P<re>[^\"]+)\"", "description": "断言地址", "example": '那么 页面地址匹配 "x"'},
]
# 假自报模型 id：形状对（非空字符串）、两引擎不同即够——doctor 的模型行断言的是「这个值出自自述对象」。
FAKE_MODEL_ID = {"novaact": "nova-act-v1.0", "midscene": "qwen.qwen3-vl-235b-a22b"}


@pytest.fixture(autouse=True)
def _stub_engine_capabilities(monkeypatch):
    def fake_query_capabilities(engine: str, *, steps_dir=None, timeout_s: float = 60.0) -> dict:
        if engine not in FAKE_MIN_GRACE_S:
            raise ValueError(f"未知引擎 {engine!r}")  # 同 compose 定位链的引擎名校验
        compose.resolve_worker_cmd(engine)  # 定位链照真走：miss → WorkerNotFoundError，同真查询的第一步
        caps = {"schema_version": 1, "engine": engine, "min_grace_s": FAKE_MIN_GRACE_S[engine],
                "deterministic_steps": [dict(e) for e in FAKE_DETERMINISTIC_STEPS],
                "model_id": FAKE_MODEL_ID[engine]}
        # 真实现自己会按（引擎, steps 目录）缓存这份对象；替身照同一键写一份，好让「本机 run 每引擎只问一次」
        # 那条**生产行为**（engine_min_grace 复用已有自述、不再问 worker）在替身之上照样被测到。
        compose._CAPABILITIES_CACHE.setdefault((engine, None if steps_dir is None else str(steps_dir)), caps)
        return caps

    monkeypatch.setattr(compose, "query_capabilities", fake_query_capabilities)
    # 进程内缓存跨用例泄漏 → 上一个用例的值（或真 worker 的值）污染下一个；两头都清。
    compose._CAPABILITIES_CACHE.clear()
    yield
    compose._CAPABILITIES_CACHE.clear()
