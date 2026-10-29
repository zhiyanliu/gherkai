"""确定性 step 注册表（ADR 0022）——Nova 引擎。

测试开发用 `@deterministic(pattern)` 把「正则模式 → handler」登记进一张表。worker 派发
每个 step 时**先查这张表**：命中走精确 handler（拿 Playwright/CDP 句柄判定、**不投票、可复现**），
未命中才落到 AI catch-all（ADR 0020/0024）。内建导航也是这张表里的一条（ADR 0020 第 3 条：Given / When
后整句是一个地址），不再是派发里的独立分支。

为什么匹配放 worker 不放 core（ADR 0022）：确定性 handler 是**引擎特定**的（碰 nova.page 这类
精确 API），匹配表跟着 handler 走最内聚；core 只解析结构 + 调度，对 step 语义无知。

角色边界（ADR 0020）：QA 永远只写自然语言（默认走 AI）；确定性 step 由测试开发注册（QA 不碰）——
本包 `deterministic_steps.py` 只承载内建导航条目与写法说明，使用方的项目专属 step 在项目 `steps/` 目录、由 worker
启动时按 env `GHERKAI_STEPS_DIR` 加载进**本模块这张同一张表**（`user_steps.py` / ADR 0037 决策 4）。

句柄按种类分键（ADR 0050 决策 1，与 Midscene 侧同构、字段名取 Python 惯例的 snake_case）：`playwright`（桌面浏览器）
与 `webdriver`（远程访问会话）。装饰器写法等价于只有 playwright；多句柄形态是普通函数调用
`deterministic(pattern, {"playwright": fn, "webdriver": [{"ui_kinds": [...], "devices": [...], "requires": [...], "handler": fn}]},
description=..., example=...)`。每个 webdriver 条目用 ui_kinds（web / app）与 devices（android / ios）声明适用范围，两个列表
各自独立、覆盖它们的全部组合，缺省为全部取值；requires（1.5 只有 web_context）是运行期前提。本引擎没有设备路径
（ADR 0049 决策 9）：只写了 webdriver 句柄的 step 在本 worker 上永远走 AI，条目的 targets 原样自述、让测试开发看见。

匹配与派发分两步（ADR 0050 决策 1「跨 step 的命中与目标无关」）：`match()` 只看文本命中哪条模式（多条即冲突），不看
目标；`select_handler()` 再按当前目标在命中条目的句柄集合里取句柄，取不到即走 AI、**绝不顺延**到下一条能匹配的模式。

handler 约定：
- playwright 句柄签名 `def handler(ctx, **groups)`：ctx 暴露 `page`（Playwright Page）与 `navigate(url)`（引擎的导航原语）；
  **groups 即正则的具名组**（`(?P<name>...)`）。无具名组则不传额外参数。
- **必须是同步函数**（`def`，不能 `async def`）：本引擎同步执行 handler，返回 awaitable 会被 `run_scope._run_step`
  检出并抛 TypeError（该 step 记 error）——因为 coroutine 不被 await 时里面的断言压根没执行，静默判 passed 是假阳性。
  对侧 Midscene 的 handler 允许 async（那边是 async 执行模型），故这是引擎执行模型差异、不是可对齐项：
  需要异步的判定只能写在 Midscene 侧。
- 判定失败抛 `AssertionError` → step 记 **failed**（断言没过）；抛其它异常 → step 记 **error**。
- 不投票（确定性即无抖动，与 AI 断言的 votes 区分）。
- 条目可声明适用的 Gherkin 关键字 `keywords`（ADR 0050 决策 1）：缺省 Given / When / Then 全部；step 文本命中模式
  但关键字不在集合内时 step 记 error、不转 AI、不顺延到别的模式。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Iterable

KEYWORDS: tuple[str, ...] = ("Given", "When", "Then")  # core 已把 And / But 折叠成这三者之一（ADR 0025）
# 测试目标的两个维度（ADR 0048 决策 1）：取值与 Job 的 target 同名同值；desktop 不在 DEVICES 里（它只有 playwright 句柄）
UI_KINDS: tuple[str, ...] = ("web", "app")
DEVICES: tuple[str, ...] = ("android", "ios")
REQUIREMENTS: tuple[str, ...] = ("web_context",)  # webdriver 条目可声明的运行期前提（ADR 0050 决策 1），封闭集合
_TARGET_DEVICE_ORDER: tuple[str, ...] = ("desktop",) + DEVICES  # 自述里 targets 的固定写出顺序：只管输出，不参与匹配与派发
_HANDLER_KINDS: tuple[str, ...] = ("playwright", "webdriver")
_ENTRY_FIELDS: tuple[str, ...] = ("ui_kinds", "devices", "requires", "handler")


@dataclass(frozen=True)
class WebdriverEntry:
    """规范化后的一个 webdriver 条目：三个元组都已展开为显式取值、按封闭集合的顺序排列。"""
    ui_kinds: tuple[str, ...]
    devices: tuple[str, ...]
    requires: tuple[str, ...]
    handler: Callable


@dataclass(frozen=True)
class Handles:
    """一条 step 的句柄集合：playwright 可空、webdriver 零到多条（注册期已保证不覆盖同一个（设备, 界面类型）组合）。"""
    playwright: Callable | None
    webdriver: tuple[WebdriverEntry, ...]


@dataclass(frozen=True)
class _Entry:
    pattern: re.Pattern
    raw: str  # 原始模式串（报错/调试/自述用）
    description: str  # 供 feature 作者阅读的元数据（ADR 0036）：这步做什么
    example: str  # feature 里怎么写（可直接抄的 step 文本）
    keywords: tuple[str, ...]  # 适用的关键字（ADR 0050 决策 1），缺省全部三个
    handles: Handles


_REGISTRY: list[_Entry] = []


def _normalize_keywords(pattern: str, keywords: Iterable[str] | None) -> tuple[str, ...]:
    """校验并归一 `keywords` 声明：封闭集合、非空、不重复；缺省为全部三个关键字。"""
    if keywords is None:
        return KEYWORDS
    kws = tuple(keywords)
    if not kws:
        raise ValueError(f"deterministic({pattern!r}) 的 keywords 不能为空：缺省（不传）即接受全部关键字")
    unknown = [k for k in kws if k not in KEYWORDS]
    if unknown:
        raise ValueError(f"deterministic({pattern!r}) 的 keywords 含未知取值 {unknown!r}：只能是 {list(KEYWORDS)}")
    if len(set(kws)) != len(kws):
        raise ValueError(f"deterministic({pattern!r}) 的 keywords 有重复：{list(kws)!r}")
    return tuple(k for k in KEYWORDS if k in kws)  # 规范顺序，便于自述与跨语言对拍


_MISSING = object()  # 条目字段缺键的哨兵：缺省只认缺键，显式 None 不是缺省（与 Midscene 侧对 null 的处置一致）


def _closed_set(pattern: str, field: str, values, allowed: tuple[str, ...], allow_empty: bool) -> tuple[str, ...]:
    """条目字段的封闭集合校验与归一（与 keywords 同一套规则）：未知取值、重复即抛；缺键展开为全集；按集合顺序排列。
    allow_empty 只对 requires 为真（空列表与缺键同义：没有前提）。显式 None 不是缺省、按类型不对拒绝。"""
    if values is _MISSING:
        return () if allow_empty else allowed
    if not isinstance(values, (list, tuple)):
        raise ValueError(f"deterministic({pattern!r}) 的 webdriver 条目 {field} 不是列表（None 也不行：缺省就不要给这个字段）")
    vals = tuple(values)
    if not vals and not allow_empty:
        raise ValueError(f"deterministic({pattern!r}) 的 webdriver 条目 {field} 不能为空：缺省（不给）即全部取值")
    unknown = [v for v in vals if v not in allowed]
    if unknown:
        raise ValueError(f"deterministic({pattern!r}) 的 webdriver 条目 {field} 含未知取值 {unknown!r}：只能是 {list(allowed)}")
    if len(set(vals)) != len(vals):
        raise ValueError(f"deterministic({pattern!r}) 的 webdriver 条目 {field} 有重复：{list(vals)!r}")
    return tuple(v for v in allowed if v in vals)


def _normalize_handlers(pattern: str, handlers) -> Handles:
    """注册面第二参的规范化与注册期校验（ADR 0050 决策 1）：违反即抛、按 ADR 0037 决策 4 的加载失败处理。
    校验项与 Midscene 侧逐项一致（跨语言 fixture 对拍）：未知句柄种类、没有任何句柄、句柄不是函数、webdriver 列表为空、
    条目字段的封闭集合、含 web_context 的条目 ui_kinds 必须恰为 ["web"]、两个条目覆盖同一个（设备, 界面类型）组合。"""
    if callable(handlers):
        return Handles(playwright=handlers, webdriver=())
    if not isinstance(handlers, dict):
        raise ValueError(f"deterministic({pattern!r}) 的 handlers 既不是函数也不是字典：传一个 playwright handler 函数，"
                         f"或 {{'playwright': …, 'webdriver': …}} 字典")
    unknown_kinds = [k for k in handlers if k not in _HANDLER_KINDS]
    if unknown_kinds:
        raise ValueError(f"deterministic({pattern!r}) 的 handlers 含未知句柄种类 {unknown_kinds!r}：只能是 {list(_HANDLER_KINDS)}")
    if "playwright" not in handlers and "webdriver" not in handlers:
        raise ValueError(f"deterministic({pattern!r}) 的 handlers 没有任何句柄：至少给 playwright 或 webdriver 之一")
    playwright = handlers.get("playwright")
    if "playwright" in handlers and not callable(playwright):
        raise ValueError(f"deterministic({pattern!r}) 的 playwright 句柄不是函数")
    raw_entries: list = []
    if "webdriver" in handlers:
        wd = handlers["webdriver"]
        raw_entries = list(wd) if isinstance(wd, (list, tuple)) else [wd]
        if not raw_entries:
            raise ValueError(f"deterministic({pattern!r}) 的 webdriver 条目列表不能为空：缺省（不给 webdriver 键）即没有设备句柄")
    entries: list[WebdriverEntry] = []
    covered: set[str] = set()  # "device/ui_kind" → 已有条目覆盖
    for e in raw_entries:
        if not isinstance(e, dict):
            raise ValueError(f"deterministic({pattern!r}) 的 webdriver 条目不是字典")
        unknown_fields = [k for k in e if k not in _ENTRY_FIELDS]
        if unknown_fields:
            raise ValueError(f"deterministic({pattern!r}) 的 webdriver 条目含未知字段 {unknown_fields!r}：只能是 {list(_ENTRY_FIELDS)}")
        if not callable(e.get("handler")):
            raise ValueError(f"deterministic({pattern!r}) 的 webdriver 条目缺 handler 或 handler 不是函数")
        ui_kinds = _closed_set(pattern, "ui_kinds", e.get("ui_kinds", _MISSING), UI_KINDS, False)
        devices = _closed_set(pattern, "devices", e.get("devices", _MISSING), DEVICES, False)
        requires = _closed_set(pattern, "requires", e.get("requires", _MISSING), REQUIREMENTS, True)
        if "web_context" in requires and ui_kinds != ("web",):
            raise ValueError(f"deterministic({pattern!r}) 的 webdriver 条目声明了 requires web_context，ui_kinds 必须恰为 ['web']"
                             f"（应用目标固定原生上下文，前提没有定义）")
        for d in devices:
            for k in ui_kinds:
                key = f"{d}/{k}"
                if key in covered:
                    raise ValueError(f"deterministic({pattern!r}) 的两个 webdriver 条目覆盖同一个（设备, 界面类型）组合 {key}："
                                     f"一个 step 在一个目标上只能有一份实现，不论 requires 是否相同")
                covered.add(key)
        entries.append(WebdriverEntry(ui_kinds=ui_kinds, devices=devices, requires=requires, handler=e["handler"]))
    return Handles(playwright=playwright, webdriver=tuple(entries))


def deterministic(pattern: str, handlers=None, *, description: str, example: str,
                  keywords: Iterable[str] | None = None):
    """注册一条确定性 step。两种写法：

    装饰器（等价于只有 playwright 句柄）：
        @deterministic(r'页面地址匹配 "(?P<pattern>[^"]+)"',
                       description="断言当前页面 URL 匹配给定正则",
                       example='Then 页面地址匹配 "/wiki/OpenAI"',
                       keywords=("Then",))
        def url_matches(ctx, pattern):
            assert re.search(pattern, ctx.page.url)

    多句柄（ADR 0050 决策 1；普通函数调用，`handlers` 为字典、或直接传一个 playwright 函数）：
        deterministic(r'…', {"playwright": url_matches,
                             "webdriver": [{"ui_kinds": ["web"], "requires": ["web_context"], "handler": url_matches_on_device}]},
                      description="…", example="…")

    description/example 必填（ADR 0036：注册即暴露——缺元数据的能力不可被 feature 作者发现，fail-loud）。
    keywords 可选（ADR 0050 决策 1）：这条 step 接受的 Gherkin 关键字子集，缺省全部。
    """
    if not description or not example:
        raise ValueError(f"deterministic({pattern!r}) 注册缺 description/example："
                         f"两者必填——缺了这条 step 不会出现在能力清单里，feature 作者发现不了它")
    compiled = re.compile(pattern)
    kws = _normalize_keywords(pattern, keywords)

    def register(handler: Callable) -> Callable:
        _REGISTRY.append(_Entry(pattern=compiled, raw=pattern, description=description, example=example, keywords=kws,
                                handles=_normalize_handlers(pattern, handler)))
        return handler

    if handlers is None:
        return register
    register(handlers)
    return None


# 条目有实现的测试目标（ADR 0049 决策 1、3）：由句柄推出（ADR 0050 决策 1）——playwright 对应桌面网页；worker 原样报出、
# 不与自己的顶层 targets 求交（交集由命令行工具一侧算，ADR 0049 决策 3）。
PLAYWRIGHT_TARGET: dict = {"device": "desktop", "ui_kinds": ["web"]}


def step_targets(handles: Handles) -> list[dict]:
    """由句柄集合推出 step 的 targets（ADR 0050 决策 1）：playwright → desktop/web；每个 webdriver 条目按 devices × ui_kinds
    展开，再按（设备, requires）聚合、界面类型收进 ui_kinds。写出顺序固定（设备 desktop → android → ios，ui_kinds web → app，
    同一设备下无 requires 在前、有的按取值字典序），与 Midscene 侧逐字节一致。"""
    acc: dict[tuple[str, tuple[str, ...]], set[str]] = {}
    if handles.playwright is not None:
        acc.setdefault((PLAYWRIGHT_TARGET["device"], ()), set()).update(PLAYWRIGHT_TARGET["ui_kinds"])
    for e in handles.webdriver:
        for d in e.devices:
            acc.setdefault((d, e.requires), set()).update(e.ui_kinds)
    out = []
    for (device, requires) in sorted(acc, key=lambda k: (_TARGET_DEVICE_ORDER.index(k[0]), k[1] != (), ",".join(k[1]))):
        item = {"device": device, "ui_kinds": [k for k in UI_KINDS if k in acc[(device, requires)]]}
        if requires:
            item["requires"] = list(requires)
        out.append(item)
    return out


def list_registry() -> list[dict]:
    """注册表自述（ADR 0036「2.」）：作自述入口 `--capabilities` 的 `deterministic_steps` 键给 CLI 转述。"""
    return [{"pattern": e.raw, "description": e.description, "example": e.example, "keywords": list(e.keywords),
             "targets": step_targets(e.handles)}
            for e in _REGISTRY]


class DeterministicConflict(Exception):
    """一个 step 文本命中多条确定性模式（ADR 0022：最多命中一条，多条是配置错误）。

    冲突清单只经 message 传（派发侧把异常文本并入 step_done.message，见 run_scope.py `_run_step` 的失败分支）；用例预检要结构化清单走
    match_batch 的 `{"conflict": [...]}`（ADR 0036），不从异常上挂字段。
    """


class DeterministicKeywordMismatch(Exception):
    """step 文本命中了一条确定性模式，但当前关键字不在该条目声明的 `keywords` 里（ADR 0050 决策 1）。

    派发侧据此记 error、不转 AI、不顺延（典型：`Then` 后只写一个地址——裸地址已是导航语法，Then 没有断言谓词）。
    用例预检的结构化形态是 match_batch 的 `{"keyword_mismatch": pattern, "keywords": [...]}`（ADR 0036）。
    """

    def __init__(self, text: str, keyword: str, pattern: str, keywords: tuple[str, ...], description: str) -> None:
        self.pattern = pattern
        self.keywords = keywords
        super().__init__(f"step {text!r} 命中确定性 step「{description}」，但这条写法只在 {' / '.join(keywords)} 下有意义"
                         f"（当前关键字是 {keyword}）：改用这些关键字之一，或改写这一步")


@dataclass(frozen=True)
class Hit:
    """命中结果：命中条目的句柄集合与具名组。句柄要再经 select_handler 按当前目标取——命中与目标无关（ADR 0050 决策 1）。"""
    handles: Handles
    groups: dict


def _hits(text: str) -> list[tuple[_Entry, re.Match]]:
    """扫注册表收**全部**命中——match（实际运行派发）与 match_batch（用例预检）唯一的扫描实现面。

    两个消费者只在「命中数怎么处置」上分叉，匹配语义本身不复制成两份：ADR 0036 的「同一注册表、
    同一 search 实现」由此结构保证，改匹配面（search→fullmatch、大小写归一、pattern 预处理）不会
    漏改一处让 plan 标注对实际运行撒谎。关键字不进匹配，只在命中之后核对条目的声明；目标也不进匹配。
    """
    return [(e, m) for e in _REGISTRY if (m := e.pattern.search(text))]


def match(text: str, keyword: str | None = None) -> Hit | None:
    """在注册表里找命中 text 的唯一条目。

    返回 Hit 或 None（未命中走 AI）。命中多条 → DeterministicConflict；
    命中一条但 keyword 不在其声明里 → DeterministicKeywordMismatch（keyword 为 None 时不核对）。
    """
    hits = _hits(text)
    if not hits:
        return None
    if len(hits) > 1:
        raws = ", ".join(repr(e.raw) for e, _ in hits)
        raise DeterministicConflict(
            f"step {text!r} 命中多条确定性模式 [{raws}]：一个 step 只能命中一条，请收紧模式"
        )
    entry, m = hits[0]
    if keyword is not None and keyword not in entry.keywords:
        raise DeterministicKeywordMismatch(text, keyword, entry.raw, entry.keywords, entry.description)
    return Hit(handles=entry.handles, groups=m.groupdict())


def select_handler(hit: Hit, device: str, ui_kind: str):
    """命中之后按当前目标取句柄（ADR 0050 决策 1）：desktop/web 取 playwright；设备目标取覆盖这个（设备, 界面类型）组合的那条
    webdriver 条目（注册期已保证至多一条）。返回 ("playwright", fn) / ("webdriver", fn, requires) / None——None 表示命中的模式在
    当前目标上没有句柄：调用方走 AI，**绝不顺延**到下一条能匹配的模式、也不记 error。本引擎的派发只会问 desktop/web。"""
    if device == "desktop":
        return ("playwright", hit.handles.playwright) if ui_kind == "web" and hit.handles.playwright is not None else None
    for e in hit.handles.webdriver:
        if device in e.devices and ui_kind in e.ui_kinds:
            return ("webdriver", e.handler, e.requires)
    return None


def match_batch(items: list) -> list[dict | None]:
    """批量 match 查询（ADR 0036 决策 4）：plan 命中标注用——对每条 step 回答「命中哪条 / 冲突 / 关键字不符 / 未命中」。

    每项是 `{"keyword", "text"}`；也接受裸字符串（旧版命令行工具的形态，此时不核对关键字）。
    与 match() 共用 `_hits`（同一扫描实现面），冲突不抛、结构化返回（plan 是用例预检、不是执行）。输出不带目标信息：
    plan 用命中的模式关联自述清单里该条目的 targets，再按 scope 的目标标注（ADR 0049 决策 3）。
    返回元素：None | {"pattern","description"} | {"conflict": [patterns]} | {"keyword_mismatch": pattern, "keywords": [...]}。
    """
    out: list[dict | None] = []
    for item in items:
        if isinstance(item, str):
            keyword, text = None, item
        else:
            keyword, text = item.get("keyword"), item["text"]
        hits = _hits(text)
        if not hits:
            out.append(None)
        elif len(hits) > 1:
            out.append({"conflict": [e.raw for e, _ in hits]})
        else:
            entry, _ = hits[0]
            if keyword is not None and keyword not in entry.keywords:
                out.append({"keyword_mismatch": entry.raw, "keywords": list(entry.keywords)})
            else:
                out.append({"pattern": entry.raw, "description": entry.description})
    return out


def clear() -> None:
    """清空注册表（仅供测试隔离用）。"""
    _REGISTRY.clear()
