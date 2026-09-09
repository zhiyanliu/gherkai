# Step 措辞：默认 AI 判断（QA 零预设）+ 确定性锚点脚手架（工程角色按需自建）

> **Status:** Partially-superseded-by 0022 —— 「裸 `When/Then`→默认 AI；确定性=脚手架、测试开发按需建、QA 零代码」核心语义**不变**；落地机制被反转（从「cucumber 补丁 + pytest-bdd 原生区分」转为「核心库解析关键字 + worker catch-all/确定性注册表派发」，确定性锚点的收集方式从「被 BDD runner 自动收集」转为「写在 `engines/*/worker/` 下的脚手架文件、由 worker import 触发注册进注册表」——**锚点仍住脚手架文件**，见 0022「迁移」条的实装偏差纠正）。下文「Midscene 靠补丁」段属被取代的 v0.x 形态。

断言类 step 的措辞设计，使「AI 柔性主导」([0014](./0014-ai-first-assertions.md)/[0015](./0015-v1-positioning-smoke-not-regression.md)) 落到 QA 的真实书写体验上。

## 问题：路由关键词让 QA 写着别扭

此前断言要写 `Then AI 确认 "..."`。但 `AI 确认` 这四个字**对 engine 毫无意义**（engine 只收到引号里的自然语言，根本不解析 Gherkin 文本）——它纯粹是给 step-definition 正则路由用的关键词。让 QA 写"给框架内部路由用的词"，既别扭又违背"AI 主导"（AI 是默认，不该要 QA 特意声明"用 AI"）。

## 决定：默认 AI / 少数派显式

**让最常用的写法最省事，特例才需要标注**：

1. **默认 AI 判断**：QA 写 `When "{自然语言}"` / `Then "{自然语言}"`——**不带任何关键词**，框架默认喂给 AI（动作 `aiAct`/`act`；断言 `aiBoolean` ↔ `act_get(BOOL_SCHEMA)` + 投票）。这是 ~90% 的情况。
   - **两个引擎匹配机制不同**（已实测）：**Nova Act/pytest-bdd 原生区分 `@when`/`@then`**，裸字符串 step 直接可用。**Midscene/cucumber-js 不区分关键字、仅按 pattern**，故 `When "{string}"` 与 `Then "{string}"` 同 pattern → ambiguous → **靠本地补丁解决**（按 PickleStepType 收窄到关键字，见 [0021](./0021-local-cucumber-patch-step-keyword-disambiguation.md)）。**vanilla cucumber 跑不通裸字符串双 step；补丁是 Midscene 侧此设计的前提。**

2. **确定性锚点 = 脚手架，QA 零预设**：少数"必须精确、不容 AI 抖动"的断言（URL/DOM 精确查），做成脚手架文件 `deterministic.steps.ts`（Midscene）/ `deterministic_steps.py`（Nova Act），与各引擎 worker 主模块同级（`engines/*/worker/`，落点见 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)「迁移」条），内含**说明注释**教测试开发怎么加、怎么和 `.feature` 呼应。
   - **对 QA 零预设**：QA 永不碰确定性锚点、不学任何措辞——锚点由**测试开发角色**按真实需求维护（避免过度设计，同 [0018](./0018-generic-steps-capability.md) 删"取数原语"的教训）。
   - **落地现状（[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md) 决定，非当初"空脚手架"）**：脚手架现由测试开发各内置**一个**演示/验证用 URL 锚点 `页面地址(?:精确)?匹配 "<正则>"`（`features/deterministic_anchor.feature` 实跑验证）；脚手架文件本身迁入 `engines/*/worker/`、由 worker import 触发注册进注册表（锚点仍写在脚手架文件里，注册表只是收集机制）——锚点由测试开发维护、非 QA 预设，故不违背"QA 零预设"。当初"空脚手架、零具体锚点"的设想已被此演示锚点取代。**注册表现同时是能力自述面**（[0036](./0036-deterministic-capability-discovery.md)：注册即暴露——`@deterministic` 的 description/example 必填、QA 可用 `list-deterministic` 主动查已有锚点）：**「主动查」不等于「预设措辞」**，本条"QA 零预设"不变量仍成立。
   - 两个引擎脚手架对齐。

3. **URL 形态自动分流（导航不写死动词）**：QA 写到 URL 时（如 `Given 打开 "https://..."` / `访问 "https://..."` / `前往 "https://..."`），框架**按 step 文本里有没有 URL 字面量**（引号内 `https?://…`）自动分流，**不锁动词**：
   - **含 URL → 内建确定性导航**（code 抽出 URL 直接 `goto`/`go_to_url`，精确、不浪费 AI、不会被理解成"搜索"而跑偏）。动词随便写，QA 不必记固定措辞——对齐本 ADR"QA 只写自然语言"。
   - **不含 URL → 回落默认 AI**（如 `访问 OpenAI 的维基页` / `回到首页` → `aiAct`/`act`，让引擎自己导航）。
   - 这是 A（确定性）+ B（AI）的组合：URL 已知时享受精确，未知时享受柔性。**退路**：若 URL 检测出现误伤（句中只是提及 URL、并非要导航），把 code 路退化成全 AI（B）。
   - **落点 = worker 的派发逻辑**（不在 core，对齐 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)「core 对 step 语义无知」；协议形态见 [0024](./0024-worker-core-protocol.md)）。取代了早先 `Given 打开 "{url}"` 的固定措辞写法。

## 角色边界（关键）

- **QA**：永远只写 `.feature` 纯自然语言 → 默认走 AI。**"零代码"对 QA 成立。**
- **测试开发**（会写代码）：偶尔需精确锚点时，在确定性脚手架（`worker/deterministic.steps.ts` / `worker/deterministic_steps.py`）写一小段 Playwright 查询 step。这是 BDD 原本的角色分工，**不破坏 QA 零代码**。

## 删除的过时措辞

- `AI 确认 "..."` → 改为无关键词 `Then "..."`。否定断言 `确认页面没有 "..."` **同归一为无关键词** `Then "{自然语言}"`（AI 直接判否定陈述，如 `features/wikipedia_assertions.feature` 的 `"页面没有出现服务器错误"`），未保留该关键词 step。
- `页面地址包含 "..."` 等**预置确定性 step → 删除**（移入脚手架的"示例/按需自建"，不在 generic 预置）。
- 早先"显式断言锚点=QA 点名让 AI 看"（[0015](./0015-v1-positioning-smoke-not-regression.md) 原措辞）澄清：QA 点名仍走默认 AI 层（写自然语言）；确定性锚点是工程角色的另一套，不混。
