# 用例描述层用单一共享的 .feature 文件

`.feature`（Gherkin 文本）是整条链路上**唯一**语言无关、可共享的一层。两侧的 runner（Python 的 `pytest-bdd`、TS 的 `cucumber-js`）与 step 实现必然各自一套——这是「双语言裂缝」的物理后果，不是设计选择。

**决定**：被两套 runner 加载的 `.feature` 做成**物理同一个文件**（放 git 根的 `features/`），而非两份各自维护、靠纪律保持一致。这样它是真正的单一事实源——改一次两边都变。

**为什么**：本框架的立身之本就是「一套业务可读用例，两个 AI 引擎都能跑」。退成两份同步只是口号，框架会退化成「两个各自为政的引擎恰好风格像」。

**承受的代价（已知）**：两套 runner 对 Gherkin 方言/step 匹配语法支持不完全一致（cucumber-js 用 Cucumber Expressions/正则；pytest-bdd 用自己的 parser + `parsers.parse`/`re`），step 措辞需取两者交集。这个约束本身有价值：它逼迫 step 措辞保持中立、不绑定某引擎的能力。

## ✅ 已实测（2026-06-23，M2）：同一份 .feature 双 runner 加载，均通过

`features/wikipedia_search.feature` 被两套 runner 各自加载、各驱动一个引擎，都通过：
- **Midscene 侧**：`midscene/` 的 cucumber-js（配置 `cucumber.mjs` 指 `../features/`）→ 1 scenario / 5 steps passed。
- **Nova Act 侧**：`novaact/bdd/test_wikipedia.py` 的 pytest-bdd（`scenarios("../../features/...")`）→ 1 passed。
- 同一句 `When I search for "OpenAI" and open its article` 同时驱动了两个不同语言/不同大脑的引擎——本框架立身之本落地。

**方言交集结论（本 ADR 预言的代价，已实证「可行但需注意」）**：
- `.feature` 文本完全共享、两边都正确匹配。
- 但 **step 定义侧的参数捕获语法不同**：cucumber-js 用 Cucumber Expressions（`{string}`），pytest-bdd 用 `parsers.parse('..."{term}"...')`。同一句 Gherkin 两边都能匹配，只是 step 定义写法各异——符合预期，纪律可控。

**M2 撞出的接线坑（固化备查）**：
- TS：tsx 在 Node 22 须 `NODE_OPTIONS="--import tsx/esm"`（非废弃的 `--loader`）；`midscene` 子工程是 commonjs，故 `midscene/bdd/` 加局部 `package.json` 标 `{"type":"module"}`，且 step 内联 SigV4 fetch 不跨目录引 CJS。
- TS：Midscene `PlaywrightAgent` 的 `.page` 非原始 Playwright Page，导航/确定性断言要单独保存原始 `page`。
- Python：`with Workflow(...)` 不设 contextvar，AgentCore `provider.cdp_session()` 靠 `get_current_workflow()` 鉴权——须 `@workflow` 装饰器，或在 fixture 内手动 `set_current_workflow(wf)`（见 `test_wikipedia.py`）。
