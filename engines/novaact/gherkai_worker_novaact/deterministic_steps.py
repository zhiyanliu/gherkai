"""确定性 step 脚手架（ADR 0020/0022）—— 本包随 worker 发行的注册表内容：**只有内建导航一条**。

机制（ADR 0022）：worker 派发每个 step 时**先查确定性注册表**（命中走 handler），未命中才落 AI catch-all。
用 `@deterministic(正则)` 注册即可——worker 启动时 import 本模块，顶层的 @deterministic 副作用把本文件里的
条目登记进表。

内建导航（ADR 0020 第 3 条）：一条 step 去掉关键字后**整句只是一个地址**（加不加引号都一样）、且关键字是
Given 或 When，才是导航。判据是结构、不是措辞：不用动词词表，也不再按「引号里出现网址」判断。
    Given "https://www.wikipedia.org/"
    When https://en.wikipedia.org/wiki/OpenAI
句子里还有别的内容（`When 在输入框输入 "https://…"`）不是导航、走 AI；`Then` 后只有一个地址按注册表的
关键字声明记 error（裸地址已是导航语法，Then 没有断言谓词）。网页目标只能打开 http(s) 地址。

**产品不内置任何有措辞的 step**（ADR 0020 第 2 条）：曾内置的 `页面地址匹配 "<正则>"` 已退役。精确核对地址
这类 step 由使用方（测试开发）写进**项目里的 `steps/` 目录**（`steps/*.py`，顶层
`from gherkai_worker_novaact.deterministic import deterministic` 后 `@deterministic` 注册），worker 启动时按
env `GHERKAI_STEPS_DIR` 加载进**同一张表**（见 `user_steps.py`，ADR 0037 决策 4）。本文件是发行包内容、装在
site-packages 里，改它等于 fork。撞 pattern 按 ADR 0036 的 conflict 语义处理（用例预检暴露），
**内建与使用方之间没有优先级覆盖**。

角色边界（ADR 0020）：确定性 step 由测试开发（会写代码的角色）维护；QA 永远只在 .feature 写自然语言
（默认走 AI catch-all，见 `run_scope.py` `_run_step` / ADR 0024「worker 派发」）。

handler 约定（见 `deterministic.py`）：
  - 签名 `def h(ctx, **groups)`：ctx.page 是 Playwright Page、ctx.navigate(url) 是引擎的导航原语；
    groups 是正则具名组 (?P<name>...)。
  - 判定失败抛 AssertionError → step 记 failed；抛其它 → error。
  - 多句柄形态（`deterministic(pattern, {'playwright': fn, 'webdriver': [...]}, description=…, example=…)`，ADR 0050 决策 1）
    本引擎接受、同一套注册期校验，但没有设备路径：webdriver 条目只进自述清单、不被调用（ADR 0049 决策 9），故本文件不示范。

Midscene 侧的对齐脚手架见 `@gherkai/worker-midscene` 的 `worker/deterministic.steps` 模块。
"""
from __future__ import annotations

from gherkai_worker_novaact.deterministic import deterministic

# 地址的形态是 scheme://rest：scheme 按 RFC 3986（字母开头，字母、数字、`+ - .`），rest 非空且不含空白与双引号。
# 只剥去一对包住整句的双引号（q1 / q2 两组用来核对配对；没有结尾引号时 q2 组不参与匹配、取值为 None）。只有一侧带
# 双引号的写法（`"https://example.com`、`https://example.com"`）也命中，由句柄记 error 提示配对、不转 AI。
# 不剥标点：整句不带双引号、且地址末尾是句号、逗号、分号、冒号、叹号、问号、省略号这类标点，或右括号、右引号（ASCII
# 与全角都算，见模式开头否定先行断言里的字符集），整句就不是「一个地址」、走 AI——`When https://example.com/。` 多半
# 是把地址写进了一句话；地址本身以这些字符结尾时加引号即可（`"https://en.wikipedia.org/wiki/Foo_(bar)"`，引号内一律
# 原样当地址）。这条只看整句带不带引号、不看引号在哪一侧，两种单侧写法因此处置相同：`"https://example.com/.` 与
# `https://example.com/."` 都命中、都记引号不配对。
# 空白显式列出、不用 `\s`：ASCII 空白加不换行空格（U+00A0）与全角空格（U+3000，中文输入法在行尾容易多打一个）。
# Python 与 JS 两种正则方言的 `\s` 字符集不同（JS 含 U+FEFF、Python 含 U+0085 与 U+001C 到 U+001F），用 `\s` 会让
# 同一条 step 在两引擎上派发不同；BOM 因此不算空白，开头带 BOM 的整句不命中（BOM 不是字母、也不是空白）。
# `tel:123`（没有 `://`）、含未编码空格的地址、一个普通裸词都不命中。两引擎的模式串除具名组写法（`(?P<` 对 `(?<`）外
# 逐字相同，由 engines/fixtures/navigation-address-cases.json 对拍。
ADDRESS_PATTERN = (r'^[ \t\r\n\f\v\u00a0\u3000]*'
                   r'(?![^" \t\r\n\f\v\u00a0\u3000]*[.,;:!?)\]}。，、；：！？）】」』〉》］｝〕．…”’〗][ \t\r\n\f\v\u00a0\u3000]*$)'
                   r'(?P<q1>"?)(?P<url>[A-Za-z][A-Za-z0-9+.\-]*://[^" \t\r\n\f\v\u00a0\u3000]+)(?P<q2>")?'
                   r'[ \t\r\n\f\v\u00a0\u3000]*$')
WEB_SCHEMES = ("http", "https")


@deterministic(ADDRESS_PATTERN,
               description="内建导航：整句只是一个地址时直接打开它（网页目标只接受 http(s) 地址）",
               example='Given "https://www.wikipedia.org/"',
               keywords=("Given", "When"))
def navigate(ctx, q1: str, url: str, q2: str | None) -> None:
    """内建导航（ADR 0020 第 3 条）：整句为地址的 Given / When step，直接打开，不走 AI。"""
    q2 = q2 or ""  # 没有结尾引号时 q2 组不参与匹配
    if q1 != q2:
        raise ValueError(f"地址两侧的引号不配对：{(q1 + url + q2)!r}——要么都加双引号，要么都不加")
    scheme = url.split("://", 1)[0].lower()
    if scheme not in WEB_SCHEMES:
        raise ValueError(f"网页目标只能打开 http(s) 地址，这一步写的是 {scheme}:// 地址：{url!r}")
    ctx.navigate(url)


# 使用方确定性 step 的写法示例（**抄进你项目的 `steps/*.py` 里改**，别改本文件——见上「产品不内置任何有措辞的 step」）。
# 核对页面地址的 `Then 页面地址匹配 "<正则>"` 有可直接复制的模板，
# 见用户指南《编写确定性 step》的「内建的导航与 `steps/` 模板」一节：
# https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/writing-deterministic-steps.md
#
# from gherkai_worker_novaact.deterministic import deterministic
#
# @deterministic(r'元素 "(?P<sel>[^"]+)" 可见',
#                description="断言选择器命中的元素可见",
#                example='Then 元素 "#submit" 可见')
# def element_visible(ctx, sel: str) -> None:
#     assert ctx.page.locator(sel).is_visible(), f'元素 {sel!r} 应可见'
