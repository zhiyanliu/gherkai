"""cli 测试共用的假 worker 自述值与拼出能力自述对象的替身：`conftest.py` 的 autouse 夹具与在子进程里执行 submit 的驱动脚本
（`_submit_driver.py`）都用 `fake_query_capabilities`，断言这些值的用例从这里导入。

放在名字唯一的模块里，不放进 `conftest.py`：`cli/tests` 与 `runtime/tests` 都没有 `__init__.py`，两份 `conftest.py` 都以顶层模块名
`conftest` 载入，后载入的那份占用这个名字（载入顺序随命令行上目录的先后而变），`from conftest import ...` 因此可能取到另一份。
"""
from __future__ import annotations

# 假 worker 自报的 grace 下限（秒）：值本身无所谓，只要两引擎不同、能看出「取 max」与「按引擎分别问」。
FAKE_MIN_GRACE_S = {"novaact": 150.0, "midscene": 31.0}
# 假注册表清单：内容无所谓，只要形状对（pattern/description/example）、条数可数——用例断言的是「清单出自自述对象」。
FAKE_DETERMINISTIC_STEPS = [
    {"pattern": '^"?(?P<url>https?://[^"]+)"?$', "description": "内建导航", "example": 'Given "https://x"', "keywords": ["Given", "When"],
     "targets": [{"device": "desktop", "ui_kinds": ["web"]}]},
    {"pattern": "页面地址匹配 \"(?P<re>[^\"]+)\"", "description": "断言地址", "example": '那么 页面地址匹配 "x"'},  # 旧形态：无 keywords 键
]
# 假自报模型 id：形状对（非空字符串）、两引擎不同即够——doctor 的模型行断言的是「这个值出自自述对象」。
FAKE_MODEL_ID = {"novaact": "nova-act-v1.0", "midscene": "qwen.qwen3-vl-235b-a22b"}


def fake_query_capabilities(engine: str, *, steps_dir=None, timeout_s: float = 60.0) -> dict:
    """`compose.query_capabilities` 的替身：给出确定性的能力自述对象。定位链照真实的走（`resolve_worker_cmd`），只换掉「问 worker」
    那一跳（理由见 `conftest.py` 模块头）。"""
    from gherkai_runtime import compose

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
