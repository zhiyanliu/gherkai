# Step 措辞：默认 AI 判断（QA 零预设）+ 确定性锚点脚手架（工程角色按需自建）

断言类 step 的措辞设计，使「AI 柔性主导」([0014](./0014-ai-first-assertions.md)/[0015](./0015-v1-positioning-smoke-not-regression.md)) 落到 QA 的真实书写体验上。

## 问题：路由关键词让 QA 写着别扭

此前断言要写 `Then AI 确认 "..."`。但 `AI 确认` 这四个字**对 engine 毫无意义**（engine 只收到引号里的自然语言，根本不解析 Gherkin 文本）——它纯粹是给 step-definition 正则路由用的关键词。让 QA 写"给框架内部路由用的词"，既别扭又违背"AI 主导"（AI 是默认，不该要 QA 特意声明"用 AI"）。

## 决定：默认 AI / 少数派显式

**让最常用的写法最省事，特例才需要标注**：

1. **默认 AI 判断**：QA 写 `When "{自然语言}"` / `Then "{自然语言}"`——**不带任何关键词**，框架默认喂给 AI（动作 `aiAct`/`act`；断言 `aiBoolean` ↔ `act_get(BOOL_SCHEMA)` + 投票）。这是 ~90% 的情况。
   - **两腿匹配机制不同**（已实测）：**Nova Act/pytest-bdd 原生区分 `@when`/`@then`**，裸字符串 step 直接可用。**Midscene/cucumber-js 不区分关键字、仅按 pattern**，故 `When "{string}"` 与 `Then "{string}"` 同 pattern → ambiguous → **靠本地补丁解决**（按 PickleStepType 收窄到关键字，见 [0021](./0021-local-cucumber-patch-step-keyword-disambiguation.md)）。**vanilla cucumber 跑不通裸字符串双 step；补丁是 Midscene 侧此设计的前提。**

2. **确定性锚点 = 脚手架，不预置**：少数"必须精确、不容 AI 抖动"的断言（URL/DOM 精确查），做成**空脚手架文件** `deterministic.steps.ts`（Midscene）/ 对应 Python（Nova Act），与 `generic.steps` 同级，内含**说明注释**教 test engineer 怎么加、怎么和 `.feature` 呼应。
   - **不预置任何具体确定性锚点 step**（连 `页面地址包含` 也不预置）——预置就等于要求 QA 学措辞，违背"QA 零预设"。锚点按真实需求自建（避免过度设计，同 [0018](./0018-generic-steps-capability.md) 删"取数原语"的教训）。
   - 两腿脚手架对齐。

## 角色边界（关键）

- **QA**：永远只写 `.feature` 纯人话 → 默认走 AI。**"零代码"对 QA 成立。**
- **Test engineer**（会写代码）：偶尔需精确锚点时，在 `deterministic.steps` 写一小段 Playwright 查询 step。这是 BDD 原本的角色分工，**不破坏 QA 零代码**。

## 删除的过时措辞

- `AI 确认 "..."` → 改为无关键词 `Then "..."`。
- `页面地址包含 "..."` 等**预置确定性 step → 删除**（移入脚手架的"示例/按需自建"，不在 generic 预置）。
- 早先"显式断言锚点=QA 点名让 AI 看"（[0015](./0015-v1-positioning-smoke-not-regression.md) 原措辞）澄清：QA 点名仍走默认 AI 层（写人话）；确定性锚点是工程角色的另一套，不混。

## 实现（改造清单，B 步内）

- Midscene `generic.steps.ts`：`AI 确认 {string}` → `{string}`（默认 AI）；删 `页面地址包含`；新建 `deterministic.steps.ts` 脚手架。
- Nova Act `test_generic_steps.py`：对齐；新建确定性锚点脚手架。
- `features/*.feature`：断言改为无关键词 `Then "{人话}"`。
- 否定断言 `确认页面没有 "..."`：保留（它是通用 AI 否定断言，非绑场景；但措辞可后续也归一，暂留）。
