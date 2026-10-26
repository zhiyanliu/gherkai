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

handler 约定：
- 签名 `def handler(ctx, **groups)`：ctx 暴露 `page`（Playwright Page）与 `navigate(url)`（引擎的导航原语）；
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


@dataclass(frozen=True)
class _Entry:
    pattern: re.Pattern
    handler: Callable
    raw: str  # 原始模式串（报错/调试/自述用）
    description: str  # 人话元数据（ADR 0036）：这步做什么（给 feature 作者读）
    example: str  # feature 里怎么写（可直接抄的 step 文本）
    keywords: tuple[str, ...]  # 适用的关键字（ADR 0050 决策 1），缺省全部三个


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


def deterministic(pattern: str, *, description: str, example: str,
                  keywords: Iterable[str] | None = None) -> Callable:
    """装饰器：把 handler 按正则 pattern 登记进注册表。

    description/example 必填（ADR 0036：注册即暴露——缺元数据的能力不可被 feature 作者发现，fail-loud）。
    keywords 可选（ADR 0050 决策 1）：这条 step 接受的 Gherkin 关键字子集，缺省全部。
    用法（使用方在自己的 `steps/*.py` 里同样写法）：
        @deterministic(r'页面地址匹配 "(?P<pattern>[^"]+)"',
                       description="断言当前页面 URL 匹配给定正则",
                       example='Then 页面地址匹配 "/wiki/OpenAI"',
                       keywords=("Then",))
        def url_matches(ctx, pattern):
            assert re.search(pattern, ctx.page.url)
    """
    if not description or not example:
        raise ValueError(f"deterministic({pattern!r}) 注册缺 description/example："
                         f"两者必填——缺了这条 step 不会出现在能力清单里，feature 作者发现不了它")
    compiled = re.compile(pattern)
    kws = _normalize_keywords(pattern, keywords)

    def register(handler: Callable) -> Callable:
        _REGISTRY.append(_Entry(pattern=compiled, handler=handler, raw=pattern,
                                description=description, example=example, keywords=kws))
        return handler

    return register


# 条目有实现的测试目标（ADR 0049 决策 1、3）：由句柄推出（ADR 0050 决策 1）——本引擎的条目只有 playwright 一种句柄，
# 对应桌面网页；worker 原样报出、不与自己的顶层 targets 求交（交集由命令行工具一侧算，ADR 0049 决策 3）。
PLAYWRIGHT_TARGET: dict = {"device": "desktop", "ui_kinds": ["web"]}


def list_registry() -> list[dict]:
    """注册表自述（ADR 0036「2.」）：作自述入口 `--capabilities` 的 `deterministic_steps` 键给 CLI 转述。"""
    return [{"pattern": e.raw, "description": e.description, "example": e.example, "keywords": list(e.keywords),
             "targets": [{"device": PLAYWRIGHT_TARGET["device"], "ui_kinds": list(PLAYWRIGHT_TARGET["ui_kinds"])}]}
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


def _hits(text: str) -> list[tuple[_Entry, re.Match]]:
    """扫注册表收**全部**命中——match（实际运行派发）与 match_batch（用例预检）唯一的扫描实现面。

    两个消费者只在「命中数怎么处置」上分叉，匹配语义本身不复制成两份：ADR 0036 的「同一注册表、
    同一 search 实现」由此结构保证，改匹配面（search→fullmatch、大小写归一、pattern 预处理）不会
    漏改一处让 plan 标注对实际运行撒谎。关键字不进匹配，只在命中之后核对条目的声明。
    """
    return [(e, m) for e in _REGISTRY if (m := e.pattern.search(text))]


def match(text: str, keyword: str | None = None):
    """在注册表里找命中 text 的唯一 handler。

    返回 (handler, groups_dict) 或 None（未命中走 AI）。命中多条 → DeterministicConflict；
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
    return entry.handler, m.groupdict()


def match_batch(items: list) -> list[dict | None]:
    """批量 match 查询（ADR 0036 决策 4）：plan 命中标注用——对每条 step 回答「命中哪条 / 冲突 / 关键字不符 / 未命中」。

    每项是 `{"keyword", "text"}`；也接受裸字符串（旧版命令行工具的形态，此时不核对关键字）。
    与 match() 共用 `_hits`（同一扫描实现面），冲突不抛、结构化返回（plan 是用例预检、不是执行）。
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
