"""cli 测试共用的假 worker 自述值：`conftest.py` 的 autouse 夹具拿它们拼出能力自述对象，断言这些值的用例从这里导入。

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
