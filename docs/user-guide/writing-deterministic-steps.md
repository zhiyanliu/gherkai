# 编写确定性 step

本页讲怎么把必须精确、不能因模型判断而波动的检查写成代码：`steps/` 目录约定、Python（Nova Act 引擎）与 TypeScript（Midscene 引擎）两侧并排的注册 API、`description` / `example` 的作用、加载失败的表现，以及如何核对与带到云端。哪些判定该写成确定性 step、哪些留给 AI 由 [`writing-features.md`](./writing-features.md) 讲；命令、退出码与报告见 [`running-and-results.md`](./running-and-results.md)；镜像与部署流程见 [`cloud-backend.md`](./cloud-backend.md)。

## 写之前

按 [`writing-features.md`](./writing-features.md) 定下哪些 step 要精确、哪些留给 AI 之后，动手写代码前先确认两点：

- 确定性 step 命中后走你自己的函数：不调模型、不投票、不产生模型费用，同一个页面状态永远给同一个判定。代价是它**不产生 AI 证据**——这一步的判定与耗时照常记进报告和退出码，但没有轨迹页或回放页可看（证据形态见 [`../internals/artifacts-and-evidence.md`](../internals/artifacts-and-evidence.md)）。
- 分工是固定的：feature 作者（QA）只在 `.feature` 里写自然语言；确定性 step 由测试开发写在**你自己项目**的 `steps/` 目录里，不改引擎包的文件。
- 成本与速度也是判据。AI step 每次判定都调用一次模型，投票再乘票数，一步要几秒到几十秒（模型往返与截图）；确定性 step 零模型费用、毫秒级完成，整套用例的墙钟与云端浏览器会话时长都跟着降。出现频次高的检查优先写成确定性：`Background` 里每条 scenario 都要重做的前置检查、`Scenario Outline` 每行数据都要过的断言、被要求投票的断言。费用量级见仓库首页的模型披露表。

## `steps/` 目录与查找顺序

CLI 按以下顺序确定目录，命中即用：

| 顺序 | 来源 | 说明 |
|---|---|---|
| 1 | `--steps-dir DIR` | `run` / `plan` / `submit` / `doctor` / `list-deterministic` 五个子命令都有此选项 |
| 2 | 环境变量 `GHERKAI_STEPS_DIR` | 与上一条同义，适合固定在 shell 或 CI 环境里 |
| 3 | `./steps` | 相对当前工作目录，存在即用 |

选项或环境变量显式指定的目录不存在（或不是目录）时，命令以退出码 2 结束并说明原因：明确指了一个位置而那里没有内容属于配置错误，其中的确定性 step 一条都加载不了。默认的 `./steps` 不存在**不算错**——多数项目没有确定性 step。目录会被解析成绝对路径，并记进这个 run 的元信息：`run` 与 `submit` 起的后台进程、以及后续用 `gherkai status` 把这个 run 推到终态的进程，读到的都是同一个目录，不会因为工作目录不同而换一套 step。

worker 启动时排序递归遍历该目录，两个引擎各取自己的扩展名：

| | Nova Act 引擎 | Midscene 引擎 |
|---|---|---|
| 加载的文件 | `*.py` | `*.mts`、`*.mjs` |
| 跳过 | `test_*.py` | `*.test.*` |
| 都跳过 | 路径中任一段以 `_` 开头的文件或目录（`_helpers.py`、`_pages/`） | 同左 |

`_` 开头的文件与目录用来放辅助模块，step 文件按相对路径导入它们：Python 侧写 `from . import _helpers` 或 `from ._pages import selectors`（`steps/` 不在模块搜索路径上，`import _helpers` 会失败）；TypeScript 侧写 `import { SUBMIT } from "./_pages/selectors.mts"`。辅助模块务必带 `_` 前缀，或整个放进 `_` 开头的目录：Midscene 侧被自动加载却一条 step 都没注册的文件会让 worker 拒绝启动。

Midscene 侧只加载 `.mts` / `.mjs`。这两个扩展名恒按 ESM 解析，与你项目里有没有 `package.json`、`type` 写什么无关。**其它扩展名（含 `.ts` / `.js`）会被直接跳过，也不报错**——那个文件里的 step 一条都不会注册，这些 step 会改由 AI 判定。写完用 `gherkai list-deterministic --engine midscene` 确认清单里有你那条。

同一个 `steps/` 目录可以同时放两侧的文件，各引擎只加载属于自己的那些。

## 注册一条 step

Nova Act 引擎用装饰器 `@deterministic(pattern, *, description, example)`：

```python
# steps/login.py
from gherkai_worker_novaact.deterministic import deterministic


@deterministic(r'以 "(?P<user>[^"]+)" 登录',
               description="确定性填表登录（不走 AI）",
               example='Given 以 "alice" 登录')
def login(ctx, user):
    ctx.page.fill("#user", user)
    ctx.page.click("#submit")
```

Midscene 引擎用函数 `deterministic(pattern, handler, { description, example })`，在文件顶层调用：

```ts
// steps/login.mts
import { deterministic, DeterministicAssertion } from "@gherkai/worker-midscene";

deterministic(
  '元素 "(?<sel>[^"]+)" 可见',
  async ({ page }, { sel }) => {
    try {
      await page.locator(sel).waitFor({ state: "visible", timeout: 5000 });   // 带等待，不读瞬时值
    } catch (e) {
      throw new DeterministicAssertion(`元素 ${sel} 应可见但没有（页面 ${page.url()}）`);  // 超时转成断言失败，带现场
    }
  },
  { description: "断言选择器命中的元素可见（精确判定，不走 AI）", example: 'Then 元素 "#submit" 可见' },
);
```

Midscene 侧的 step 文件只从包名 `@gherkai/worker-midscene` 导入，可用的导出是 `deterministic`、`DeterministicAssertion` 以及 `DeterministicCtx` / `DeterministicHandler` / `DeterministicMeta` 三个类型。

你的项目不需要 `package.json` 或 `node_modules`，也不必在项目里另装这个包：worker 在加载你的 step 文件之前，把这个包名解析到它自己那一份。反过来，把导入写成指向某个安装位置的文件路径（例如另一处 `node_modules` 里的 `dist/index.mjs`）会加载到第二份副本，注册落进 worker 不读的那张表，worker 会报这个文件一条 step 都没注册并拒绝启动。

## handler 拿到什么

两侧的第一个参数都是上下文，`ctx.page` 是 Playwright 的 `Page`；正则的具名组是第二个入参：

| | Nova Act 引擎 | Midscene 引擎 |
|---|---|---|
| 签名 | `def handler(ctx, **groups)` | `(ctx, groups) => void \| Promise<void>` |
| 具名组写法 | `(?P<name>...)`，按关键字参数传入 | `(?<name>...)`，作为对象的字段传入 |
| 无具名组时 | 只收 `ctx` | `groups` 是空对象 |
| 同步 / 异步 | **必须是同步 `def`**：写成 `async def` 的那一步直接记 `error`，因为函数体里的断言不会被执行 | 可以是 `async`，worker 会 `await` |

handler 只拿到上下文与具名组。挂在这一步上的 DataTable / DocString 不会传进来，多行参数只对 AI step 有效。

需要异步判定时只能写在 Midscene 侧。

## 判定与报错

正常返回即通过；判定不成立时抛异常：

| handler 的行为 | 这一步的判定 | 说明 |
|---|---|---|
| 正常返回 | `passed` | 不投票 |
| Nova Act：抛 `AssertionError`（`assert` 语句即可） | `failed` | 异常消息进 step 的错误信息 |
| Midscene：抛 `DeterministicAssertion` 或 `node:assert` 的 `AssertionError` | `failed` | 同上 |
| 抛其它任何异常 | `error` | 属执行错误，不是断言未过 |

`failed` 与 `error` 如何汇总成 run 的退出码，见 [`running-and-results.md`](./running-and-results.md)。

## `description` 与 `example` 的作用

两个字段都**必填**，缺一个则注册时报错、点名那条模式，worker 起不来。它们是 feature 作者唯一能看到的接口：

- `description`：一句话说明这一步做什么。`gherkai list-deterministic` 每条的第一行就是它，`gherkai plan` 的命中标注 `← 确定性: <说明>` 也用它。
- `example`：一条可以直接抄进 `.feature` 的 step 文本，出现在 `gherkai list-deterministic` 的「示例」行。

写 `example` 时用你希望 feature 作者照抄的完整措辞（含 `Given` / `Then` 关键字），因为它就是对方的复制源。

## 匹配规则

被匹配的是关键字之后的 step 原文，`Given` / `Then` 本身不参与匹配：正则里不要写关键字（`example` 里带关键字是给 feature 作者照抄用的）。step 文本外层的双引号如果有，也算在被匹配的文本里。

模式按**子串**匹配 step 文本（不要求整句吻合），并且一条 step 文本**最多只能命中一条**模式。命中多条时这一步记 `error` 并列出撞上的模式；`gherkai plan` 会提前把冲突标成 `← ⚠`，此时 plan 自己的退出码仍是 0。

引擎内建的 step 与你注册的 step 进同一张表，**没有覆盖优先级**：模式撞上就是冲突，得收紧其中一条或改 step 措辞。

## 内建的确定性 step

两个引擎各内建一条，装上引擎即可用，无需写任何文件：

| 引擎 | 注册的模式 | 在 `.feature` 里怎么写 |
|---|---|---|
| Nova Act | `页面地址(?:精确)?匹配 "(?P<pattern>[^"]+)"` | `Then 页面地址匹配 "/wiki/OpenAI"` |
| Midscene | `页面地址(?:精确)?匹配 "(?<pattern>[^"]+)"` | 同上 |

它断言当前页面地址匹配给定正则，措辞「页面地址匹配」与「页面地址精确匹配」都命中。

另有一条内置的导航行为不进注册表：step 文本里双引号内的内容以 `http://` 或 `https://` 开头时，worker 把整段引号内容当作地址直接打开、不调模型，因此它不出现在清单和 `plan` 标注里。写法与注意事项见 [`writing-features.md`](./writing-features.md)。

当前实际有哪些，以 `gherkai list-deterministic --engine <引擎>` 的输出为准。

## 两侧对称地写

同一份 `.feature` 要能在两个引擎上运行，所以每条确定性 step 都在两侧各注册一份：正则语义相同、`description` 与 `example` 文字相同，只有语言方言不同。

只写一侧时，另一个引擎上这一步会改由 AI 判定，运行前检查不会提示你（它只检查本次用到的引擎）。核对方法是两个引擎各查一遍清单，再用 `gherkai plan` 看标注。

## 写得稳：等待与判定

确定性 step 假失败的头号来源是**读了瞬时值**：`is_visible()` / `isVisible()`、直接取 `text_content()` 这类调用取的是当下那一瞬间，页面还在加载就判否，手动打开页面却明明能看到。三条规则：

1. **用带等待的判定，不用瞬时值，也不用固定等待。** Python 侧用 Playwright 的 `expect(...)` 一族（`expect(page.locator(sel)).to_be_visible(timeout=...)`、`to_have_text(...)`、`to_have_url(...)`），它自动重试到超时，超时抛 `AssertionError`，这一步记 `failed`。Midscene 侧用 `locator.waitFor({ state, timeout })` 与 `page.waitForURL(...)`。固定 `sleep` 既慢又照样抖。
2. **等待超时不是断言。** `locator.wait_for(...)` / `locator.waitFor(...)` 超时抛的是 Playwright 的 `TimeoutError`，不是断言异常，这一步会记 `error` 而不是 `failed`，退出码与报告都会把它当执行错误。要让它记 `failed`，捕获后转成 `AssertionError`（Python）或 `DeterministicAssertion`（Midscene），转换时把现场补进消息。
3. **给等待一个几秒的上限。** Playwright 默认 30 秒，一条 step 等满 30 秒会吃掉这个 scope 的墙钟预算（`@timeout`），也拖慢整轮反馈。按页面实际响应给 3 到 10 秒。

Python 侧 `from playwright.sync_api import expect` 可以直接用：worker 环境自带 Playwright。Midscene 侧**运行期不要 import `playwright`**：step 文件所在目录没有 `node_modules`，worker 只把 `@gherkai/worker-midscene` 这一个包名解析到自己那份，别的包名解析不到；`import type { Page } from "playwright"` 只当类型用、编译期擦除，可以写。

## 写得能诊断：失败消息带现场

确定性 step 不产生截图与模型思考，失败时 `gherkai explain` 里这一步只有一行原因，云端更是只剩这一行。消息必须自带现场：当前页面地址、用的选择器、期望值与实际值（长文本截断）。「断言未过」「元素不可见」这种消息在云端等于没有信息。下面 Python 与 TypeScript 两侧的判定函数都这么做。

## 组织与单测：判定逻辑与注册分离

推荐的目录形态：

```
steps/
  _checks.py        # 判定逻辑（Python），只依赖 Playwright 的 Page；_ 开头，worker 不当 step 文件加载
  _checks.mts       # 同一组判定的 TypeScript 实现
  cart.py           # 注册（薄壳）：模式 + description / example，调用 _checks
  cart.mts          # 同上，Midscene 侧
  test_checks.py    # Python 单测：worker 跳过 test_ 开头的文件
  cart.test.mts     # TypeScript 单测：worker 跳过 .test. 文件
```

这样分的理由有三条：判定逻辑能在本地用真浏览器单测；两侧能共享同一份选择器表；辅助模块不会被当成 step 文件加载（Midscene 侧一条都不注册的文件会让 worker 拒绝启动）。

判定函数（两侧）：

```python
# steps/_checks.py
from playwright.sync_api import Page, expect


def element_visible(page: Page, selector: str, timeout_ms: int = 5000) -> None:
    """选择器命中的元素在 timeout_ms 内可见；否则抛 AssertionError（step 记 failed），消息带页面地址与选择器。"""
    try:
        expect(page.locator(selector)).to_be_visible(timeout=timeout_ms)
    except AssertionError as e:
        first = str(e).splitlines()[0] if str(e) else ""
        raise AssertionError(f"元素 {selector} 应可见但没有（页面 {page.url}）：{first}") from e
```

```ts
// steps/_checks.mts
import type { Page } from "playwright";
import { DeterministicAssertion } from "@gherkai/worker-midscene";

export async function elementVisible(page: Page, selector: string, timeoutMs = 5000): Promise<void> {
  try {
    await page.locator(selector).waitFor({ state: "visible", timeout: timeoutMs });
  } catch (e) {
    const first = String((e as Error).message ?? e).split("\n")[0];
    throw new DeterministicAssertion(`元素 ${selector} 应可见但没有（页面 ${page.url()}）：${first}`);
  }
}
```

注册文件只剩薄壳：

```python
# steps/cart.py
from gherkai_worker_novaact.deterministic import deterministic

from . import _checks


@deterministic(r'元素 "(?P<sel>[^"]+)" 可见',
               description="断言选择器命中的元素可见（精确判定，不走 AI）",
               example='Then 元素 "#submit" 可见')
def element_visible(ctx, sel):
    _checks.element_visible(ctx.page, sel)
```

```ts
// steps/cart.mts
import { deterministic } from "@gherkai/worker-midscene";
import { elementVisible } from "./_checks.mts";

deterministic(
  '元素 "(?<sel>[^"]+)" 可见',
  async ({ page }, { sel }) => elementVisible(page, sel),
  { description: "断言选择器命中的元素可见（精确判定，不走 AI）", example: 'Then 元素 "#submit" 可见' },
);
```

单测在本地用真浏览器、本地页面进行，不开云端浏览器会话、不调模型、不需要 AWS 凭证。测的是判定函数，不是注册文件：Python 的注册文件用相对导入，只在 worker 的加载环境里成立。

```python
# steps/test_checks.py
import pytest
from playwright.sync_api import sync_playwright

import _checks  # pytest 把测试所在目录放进导入路径，直接导入辅助模块


@pytest.fixture(scope="module")
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        yield browser.new_page()
        browser.close()


def test_visible_passes(page):
    page.set_content('<button id="submit">go</button>')
    _checks.element_visible(page, "#submit")


def test_hidden_fails_with_context(page):
    page.set_content('<button id="submit" hidden>go</button>')
    with pytest.raises(AssertionError, match=r"#submit"):
        _checks.element_visible(page, "#submit", timeout_ms=300)
```

```ts
// steps/cart.test.mts
import { after, before, test } from "node:test";
import assert from "node:assert/strict";
import { chromium, type Browser, type Page } from "playwright";
import { DeterministicAssertion } from "@gherkai/worker-midscene";
import { elementVisible } from "./_checks.mts";

let browser: Browser;
let page: Page;
before(async () => { browser = await chromium.launch(); page = await browser.newPage(); });
after(async () => { await browser.close(); });

test("visible passes", async () => {
  await page.setContent('<button id="submit">go</button>');
  await elementVisible(page, "#submit");
});

test("hidden fails with context", async () => {
  await page.setContent('<button id="submit" hidden>go</button>');
  await assert.rejects(elementVisible(page, "#submit", 300),
    (e: unknown) => e instanceof DeterministicAssertion && /#submit/.test((e as Error).message));
});
```

运行方式与开发依赖（只装在你的项目里，与 gherkai 命令行的安装无关）：

```bash
# Python 侧：pytest 与 playwright 作为项目的开发依赖；浏览器装一次
uv add --dev pytest playwright && uv run playwright install chromium
uv run pytest steps

# TypeScript 侧：playwright 与 @gherkai/worker-midscene（取 DeterministicAssertion 与类型）作为开发依赖
npm i -D playwright @gherkai/worker-midscene && npx playwright install chromium
node --test steps/*.test.mts          # Node 22.18 起原生执行 .mts；更早的 22.x 写 node --experimental-strip-types --test steps/*.test.mts
```

单测与下一节的本地核对都通过之后才值得实际运行：实际运行开云端浏览器会话、调用模型，只在要真实结果时做。

### 改一条已在用的 step

- 改判定逻辑：先单测，再按下一节核对清单与标注；云端还要重新构建镜像并推送，见 [带到云端](#带到云端)。
- 改措辞（`example`）：`example` 就是 feature 作者照抄的接口，改它等于改所有用到它的 feature。宁可加一条新模式、旧模式保留一段过渡期，但两条模式不得同时命中同一句 step 文本。
- 删 step：先全文搜索全部 feature 确认没人用；删后那些 step 会静默改由 AI 判定，`plan` 里标注消失是唯一信号。

## 在本机核对

下面这几条命令都要在本机拉起对应引擎的 worker，两个引擎的装法见 [`getting-started.md`](./getting-started.md)。

```bash
gherkai list-deterministic --engine novaact --steps-dir ./steps   # 人读清单
gherkai list-deterministic --engine midscene --json               # 机器可读
gherkai plan features/*.feature --steps-dir ./steps                # 每个 step 走确定性还是 AI
gherkai doctor --steps-dir ./steps                                 # 目录与加载结果
```

- `list-deterministic`：每条打三行——说明、`示例:`、`模式:`；`--engine` 缺省 `novaact`；清单含内建与你注册的全部条目。该引擎的 worker 没装时命令以退出码 2 结束，并原地给出安装命令。
- `plan`：命中的 step 后面标 `← 确定性: <说明>`，冲突标 `← ⚠`，走 AI 的不标（减少噪声）。某个引擎的 worker 不可用时 `plan` 不会失败，但该引擎的 step 一个标注都没有，stderr 会说明标注已降级——这种情况下不要把「没有标注」读成「都走 AI」。示例 `.feature` 在仓库的 [`features/`](../../features/) 目录。
- `doctor`：`steps.dir` 显示解析到的目录（没有目录时说明只有内建 step），`steps.load.<引擎>` 显示该引擎加载后共有多少条。

这些命令都不建浏览器会话、不调模型，不产生模型费用。

## 加载失败的表现

任何一个 step 文件加载不了，命令就**拒绝运行**，不会跳过它——跳过等于把这些精确判定改成 AI 判定，而 run 仍可能报通过。

| 症状 | 原因 | 怎么办 |
|---|---|---|
| `plan` / `run` / `submit` 在起第一个 job 前以退出码 2 结束，点名某个文件与异常 | 该文件有语法错误或缺依赖 | 先修那个文件 |
| 启动即报错并点名某条模式 | 注册时缺 `description` 或 `example` | 补齐两个字段 |
| Midscene 报某个文件一条确定性 step 都没注册 | 该文件没在顶层调用 `deterministic(...)`，或按文件路径导入了另一处安装的同名包 | 确认顶层有注册调用，且导入写的是包名 `@gherkai/worker-midscene` |
| 命令以退出码 2 结束，说 `--steps-dir` 或 `GHERKAI_STEPS_DIR` 指的目录不存在 | 路径写错或目录被移走 | 改成正确路径 |
| `list-deterministic`、`plan` 或运行前检查以退出码 2 结束，只有一句解析错误、没点名文件 | worker 与命令行工具版本不一致 | 把两侧装成同版本后重试 |
| 写了 `steps/` 却全部走 AI，或少了几条 | 目录没被读到；Midscene 侧文件用了 `.mts` / `.mjs` 以外的扩展名（被跳过，不报错）；或正则与 step 文本不匹配 | 确认 `--steps-dir` 指对，扩展名改成 `.mts` 或 `.mjs`，再用 `list-deterministic` 核对清单条数，对照 `example` 改 step 文本 |

写法问题不会让加载失败，只在判定结果上露出来：

| 症状 | 多半是 | 怎么办 |
|---|---|---|
| 时不时判否，手动打开页面明明能看到 | 读了瞬时值（`is_visible()` / `isVisible()`、没等页面就取文本） | 换成带等待的判定，见 [写得稳](#写得稳等待与判定) |
| 判定不成立却记 `error` 而不是 `failed` | 抛的是 `TimeoutError` 或别的异常 | 捕获后转成 `AssertionError` / `DeterministicAssertion`，补上现场 |
| Nova Act 上这一步记 `error`，Midscene 上正常 | Python handler 写成了 `async def` | 改成同步函数 |
| Midscene 上 `plan` 没有确定性标注，Nova Act 上有 | Midscene 侧文件扩展名是 `.ts` / `.js`（收集时静默跳过），或只写了 Python 一侧 | 改成 `.mts`，或补另一侧 |
| 云端失败只剩一句「断言未过」 | 失败消息没带现场 | 消息里带页面地址、选择器、期望与实际，见 [写得能诊断](#写得能诊断失败消息带现场) |

更多症状与处置见 [`troubleshooting.md`](./troubleshooting.md)。

## 带到云端

`--backend cloud` 时 worker 运行在云端容器里，读不到本机的 `steps/`：显式给了 `--steps-dir` 会打一句提示，用 `GHERKAI_STEPS_DIR` 或默认 `./steps` 时没有提示，本机目录一律不生效。云端要用的确定性 step 需要构建成一个 worker 镜像 variant（在基础镜像上复制 `steps/`），由部署方推送后用 `--worker-variant` 选用。构建、推送与默认指针见 [`cloud-backend.md`](./cloud-backend.md)。

因此改完 `steps/` 之后必须重新构建并推送镜像，云端才会用上新版本：提交时不比对镜像里 step 的新旧，新写的 step 在云端会改由 AI 判定，改过的 step 仍按镜像里的旧版本执行。

## 更多

想了解这套机制内部如何运转（同一张注册表怎么同时喂清单、`plan` 标注与实际运行，本机与云端为什么是两个真值源），见 [`../internals/deterministic-step-lifecycle.md`](../internals/deterministic-step-lifecycle.md)。`--steps-dir` 之外的选项与环境变量见 [`configuration.md`](./configuration.md)。
