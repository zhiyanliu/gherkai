# 用例描述层用单一共享的 .feature 文件

> **Status:** Accepted

`.feature`（Gherkin 文本）是整条链路上**唯一**语言无关、可共享的一层。两侧的 runner（Python 的 `pytest-bdd`、TS 的 `cucumber-js`）与 step 实现必然各自一套——这是「双语言裂缝」的物理后果，不是设计选择。

**决定**：被两套 runner 加载的 `.feature` 做成**物理同一个文件**（放 git 根的 `features/`），而非两份各自维护、靠纪律保持一致。这样它是真正的单一事实源——改一次两边都变。

**为什么**：本框架的立身之本就是「一套业务可读用例，两个 AI 引擎都能跑」。退成两份同步只是口号，框架会退化成「两个各自为政的引擎恰好风格像」。

**承受的代价（已知）**：两套 runner 对 Gherkin 方言/step 匹配语法支持不完全一致（cucumber-js 用 Cucumber Expressions/正则；pytest-bdd 用自己的 parser + `parsers.parse`/`re`），step 措辞需取两者交集。这个约束本身有价值：它逼迫 step 措辞保持中立、不绑定某引擎的能力。

## ✅ 已实测（M2 起）：同一份 .feature 双 runner 加载，均通过

> **演进（v1.0）**：下述「双 runner 各自加载」的 runner 层（cucumber-js `cucumber.mjs` + pytest-bdd `scenarios()` + `{type:module}` + cucumber patch）已退役（[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)）；现由核心 `core/gherkai_core/parse.py` 自解析同一份 `.feature`、派发薄 worker（Nova `engines/novaact/gherkai_worker_novaact/run_scope.py` / Midscene `engines/midscene/src/worker/run-scope.mts`）执行。**「单一物理共享 .feature」的核心决定不变**——只是加载方从双 runner 变成了核心。下述 M2 实测是当时的验证脉络，保留。

同一份 `.feature` 被两套 runner 各自加载、各驱动一个引擎，都通过：
- **Midscene 侧**：`engines/midscene/` 的 cucumber-js（配置 `cucumber.mjs` 的 `paths` 指 `../../features/`）。
- **Nova Act 侧**：`engines/novaact/bdd/` 的 pytest-bdd（`scenarios(str(FEATURES_DIR))`，`FEATURES_DIR` 上溯到根 `features/`）。
- 同一句自然语言 step 同时驱动了两个不同语言/不同大脑的引擎——本框架立身之本落地。

**方言交集结论（本 ADR 预言的代价，已实证「可行但需注意」）**：
- `.feature` 文本完全共享、两边都正确匹配。
- 但 **step 定义侧的参数捕获语法不同**：cucumber-js 用 Cucumber Expressions（`{string}`），pytest-bdd 用 `parsers.parse('..."{term}"...')`。同一句 Gherkin 两边都能匹配，只是 step 定义写法各异——符合预期，纪律可控。

**M2 撞出的接线坑（固化备查）**：
- TS：tsx 在 Node 22 须 `NODE_OPTIONS="--import tsx/esm"`（非废弃的 `--loader`）；`midscene` 子工程是 commonjs，故 `engines/midscene/bdd/` 加局部 `package.json` 标 `{"type":"module"}`，且 step 内联 SigV4 fetch 不跨目录引 CJS。
- TS：Midscene `PlaywrightAgent` 的 `.page` 非原始 Playwright Page，导航/确定性断言要单独保存原始 `page`。
- Python：`with Workflow(...)` 不设 contextvar，AgentCore `provider.cdp_session()` 靠 `get_current_workflow()` 鉴权——须 `@workflow` 装饰器，或手动 `set_current_workflow(wf)`（当时在 BDD fixture `test_generic_steps.py` 里做，该文件已随 BDD runner 退役删除、[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)；接线要求本身不变，现落在 worker 启动段）。
