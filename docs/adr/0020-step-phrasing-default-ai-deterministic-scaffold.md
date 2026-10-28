# Step 措辞：默认 AI 判断（QA 零预设）+ 确定性 step 脚手架（工程角色按需自建）

> **Status:** Partially-superseded-by 0022/0037 —— 「裸 `When/Then`→默认 AI；确定性=脚手架、测试开发按需建、QA 零代码」核心语义**不变**；落地机制被 0022 反转（从「cucumber 补丁 + pytest-bdd 原生区分」转为「核心库解析关键字 + worker catch-all/确定性注册表派发」，确定性 step 的收集方式从「被 BDD runner 自动收集」转为「写在脚手架文件里、由 worker import 触发注册进注册表」；当时脚手架落在各引擎 `worker/` 目录，见 0022「迁移」条的实装偏差纠正）。**[0037](./0037-distribution-and-packaging.md)（随 v1.4.0）再移定制面**：使用方的确定性 step 写在**使用方项目的 `steps/` 目录**（worker 启动时加载，`@deterministic` 注册机制与脚手架同一条），worker 包内脚手架（`engines/novaact/gherkai_worker_novaact/deterministic_steps.py`、`engines/midscene/src/worker/deterministic.steps.mts`）只承载内建导航这一条（曾内置的示范 step 已退役，示范进 `features/steps/` 模板）——故「确定性 step 仍住脚手架文件」**只对内建导航成立**；「QA 零预设、确定性 step 由测试开发维护」的角色边界不变。下文「Midscene 靠补丁」段属被取代的 v0.x 形态。**第 2、3 条于 2026-10-26 修订**：导航的判据改为「Given / When 后整句是一个地址」，退路从功能开关改为 plan 可见；脚手架曾内置的「页面地址匹配」step 退役，注册表只剩导航一条内建条目；应用目标上任意 scheme 经 DeepLink 交给被测应用（[0048](./0048-test-targets-device-and-ui-kind.md) 决策 7）。两条已就地改写。

断言类 step 的措辞设计，使「AI 柔性主导」([0014](./0014-ai-first-assertions.md)/[0015](./0015-v1-positioning-smoke-not-regression.md)) 落到 QA 的真实书写体验上。

## 问题：路由关键词让 QA 写着别扭

此前断言要写 `Then AI 确认 "..."`。但 `AI 确认` 这四个字**对 engine 毫无意义**（engine 只收到引号里的自然语言，根本不解析 Gherkin 文本）——它纯粹是给 step-definition 正则路由用的关键词。让 QA 写"给工具内部路由用的词"，既别扭又违背"AI 主导"（AI 是默认，不该要 QA 特意声明"用 AI"）。

## 决定：默认 AI / 少数派显式

**让最常用的写法最省事，特例才需要标注**：

1. **默认 AI 判断**：QA 写 `When "{自然语言}"` / `Then "{自然语言}"`——**不带任何关键词**，工具默认喂给 AI（动作 `aiAct`/`act`；断言 `aiBoolean` ↔ `act_get(BOOL_SCHEMA)` + 投票）。这是 ~90% 的情况。
   - **两个引擎匹配机制不同**（已实测）：**Nova Act/pytest-bdd 原生区分 `@when`/`@then`**，裸字符串 step 直接可用。**Midscene/cucumber-js 不区分关键字、仅按 pattern**，故 `When "{string}"` 与 `Then "{string}"` 同 pattern → ambiguous → **靠本地补丁解决**（按 PickleStepType 收窄到关键字，见 [0021](./0021-local-cucumber-patch-step-keyword-disambiguation.md)）。**vanilla cucumber 跑不通裸字符串双 step；补丁是 Midscene 侧此设计的前提。**

2. **确定性 step = 脚手架，QA 零预设**：少数"必须精确、不容 AI 抖动"的断言（URL/DOM 精确查），做成脚手架文件 `engines/midscene/src/worker/deterministic.steps.mts`（Midscene）/ `engines/novaact/gherkai_worker_novaact/deterministic_steps.py`（Nova Act），与各引擎 worker 主模块同级（分别与 `run-scope.mts` / `run_scope.py` 同目录；迁移史见 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)「迁移」条）；使用方自己的确定性 step 写在项目 `steps/` 目录（[0037](./0037-distribution-and-packaging.md) 决策 4），内含**说明注释**教测试开发怎么加、怎么和 `.feature` 呼应。
   - **对 QA 零预设**：QA 永不碰确定性 step、不学任何措辞——它由**测试开发角色**按真实需求维护（避免过度设计，同 [0018](./0018-generic-steps-capability.md) 删"取数原语"的教训）。
   - **内建 step 退役（2026-10-26 修订）**：脚手架曾各内置一条演示兼验证用的 `页面地址(?:精确)?匹配 "<正则>"`，自 1.5 起退役。理由：产品自带一条有固定措辞的 step，等于产品替项目决定哪些确定性 step 存在，违背本条「由测试开发按真实需求维护」的角色边界，也让 QA 多背一句措辞；「演示」该放在用户指南、agent skill 的参考与 `steps/` 模板里，由使用方复制进自己的项目。退役后注册表里唯一的内建条目是第 3 条的导航，它没有措辞、只有结构。**注册表同时是能力自述面**（[0036](./0036-deterministic-capability-discovery.md)：注册即暴露——`@deterministic` 的 description / example 必填、QA 可用 `list-deterministic` 主动查已有的确定性 step）：「主动查」不等于「预设措辞」，本条「QA 零预设」不变量仍成立。被拒的保留理由「它是 skill「导航后紧跟确定性落点核对」规则的载体」不成立：规则改为「紧跟一条确定性落点核对（页面上有某按钮、标题包含，或项目 `steps/` 里自写的地址核对 step）」，地址核对的写法由模板给出即可；设备目标上的分写归 [0048](./0048-test-targets-device-and-ui-kind.md) 决策 7。
   - 两个引擎脚手架对齐。

3. **导航的判据是结构，不是措辞**：一条 step 去掉关键字后**整句只是一个地址**（加不加引号都一样），且关键字是 Given 或 When，才是导航。worker 把它当注册表里**唯一的内建条目**处理（模式 = 整句为地址，适用关键字 Given / When），所以 plan 与 `list-deterministic` 对它的标注与其它确定性 step 一致，派发顺序只剩「注册表命中走精确实现，否则走 AI」两段。
   - **地址的边界**：地址 = `scheme://rest`，scheme 按 RFC 3986（字母开头，字母、数字、`+ - .`），`rest` 非空且不含空白与双引号；只剥去包住整句的一对双引号。**空白显式列出、不用 `\s`**：ASCII 空白加不换行空格（U+00A0）与全角空格（U+3000）——两种正则方言的 `\s` 字符集不同（JS 含 U+FEFF、Python 含 U+0085 与 U+001C 到 U+001F），用它同一条 step 会在两引擎上派发不同；BOM 不算空白，开头带 BOM 的整句不命中。**不剥标点**：不带引号的地址末尾若是句号、逗号、分号、冒号、叹号、问号、省略号这类标点或右括号、右引号（ASCII 与全角都算，封闭集合写在两侧模式串里、由跨语言夹具对拍），整句就不是「一个地址」，这一步走 AI，plan 里看得见；引号内一律原样当地址，地址本身以这些字符结尾时加引号写。`tel:123`（没有 `://`）、含未编码空格的地址、Given 后一个普通裸词，都不是地址、都走 AI，不猜。Scenario Outline 的占位符先插值再匹配（[0025](./0025-plan-module-feature-to-jobs.md)），不是漏洞。整句地址的 step 带 DocString / DataTable 时记 error：确定性 step 不接收多行参数（[0024](./0024-worker-core-protocol.md)）。
   - **网页目标**：地址须是 http(s)；桌面用 `goto` / `go_to_url` 打开，设备上的网页目标按网页上下文的探测结论选路线：可用时在网页上下文调 `url`，否则经 `mobile: deepLink` 交给系统浏览器（[0052](./0052-appium-interface-adapter-and-platform-differences.md) 决策 4、5）；非 http(s) 的地址在执行时由句柄记 error「网页目标只能打开 http(s) 地址」，不转 AI。plan 对它仍标「内建导航」、不预检协议：匹配探针与目标无关（[0049](./0049-worker-capabilities-targets-keys.md) 决策 3 与被拒方案），协议是否受支持是该目标句柄的执行期判定。**应用目标**：任意 scheme（含 http(s)）都经 `mobile: deepLink` 带包名或 bundleId 交给被测应用，做不到时 step 级 fail-fast，规则归 [0048](./0048-test-targets-device-and-ui-kind.md) 决策 7。目标来自 scope 的声明（[0048](./0048-test-targets-device-and-ui-kind.md) 决策 2），不从 step 文本推断。
   - **不是整句** → 不是导航，走 AI：`When 在输入框输入 "https://…"` 是在输入，`Then 分享面板里的链接是 "https://…"` 是在断言。**Then 后只有一个地址** → 命中模式但关键字不符，按注册表的通用规则（[0050](./0050-deterministic-step-handles-and-testing.md) 决策 1 的关键字声明）记 error、提示「这条写法只在 Given / When 下有意义」，不交给 AI：裸地址已保留为导航语法，Then 后只有地址没有表达任何断言谓词，交给 AI 等于让模型猜要断言什么。
   - **不含地址 → 回落默认 AI**（如 `访问 OpenAI 的维基页` / `回到首页` → `aiAct` / `act`，让引擎自己导航）。
   - **退路 = plan 可见**：导航与其它确定性 step 一样在 plan 里逐条标出，标注用条目的 description（当前为「内建导航：整句只是一个地址时直接打开它（网页目标只接受 http(s) 地址）」；应用目标上经 DeepLink 的说明文字随 webdriver 句柄落地，[0048](./0048-test-targets-device-and-ui-kind.md) 决策 7），残余的误判（Given / When 里单独写一个地址却不是要打开它）在花钱执行之前就能看到并改写。
   - **被取代的两代写法（护栏）**：① 固定措辞 `Given 打开 "{url}"`——要 QA 背措辞；② 「引号里出现网址就导航」（v1.0 到 v1.4）——`Then 分享链接是 "https://…"` 这类断言被误当导航，当年的退路是「误伤就把整个功能退回全 AI」，粗到不可用。也不用动词词表（打开 / 访问 / 前往…）：词表永远不全，漏一个就静默走 AI，且仍要背词。结构判据零词表、零歧义：一句话只有一个地址时，不可能是在「提及」它。
   - **落点 = worker 的派发逻辑**（不在 core，对齐 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)「core 对 step 语义无知」；协议形态见 [0024](./0024-worker-core-protocol.md)）。

## 角色边界（关键）

> 角色正名与边界矩阵的单一真源现为 [0040](./0040-consumer-role-model-and-terminology.md)（「测试开发」即当时所称 test engineer）；本节保留当时的决策内容。

- **QA**：永远只写 `.feature` 纯自然语言 → 默认走 AI。**"零代码"对 QA 成立。**
- **测试开发**（会写代码）：偶尔需精确核对时，在确定性脚手架里写一小段 Playwright 查询 step。这是 BDD 原本的角色分工，**不破坏 QA 零代码**。（当时的落点 = worker 包内脚手架文件；**定制面已由 [0037](./0037-distribution-and-packaging.md) 决策 4 反转**——使用方的确定性 step 写进项目里的 `steps/` 目录、加载进同一张确定性注册表（各引擎的扩展名与 `steps/` 目录的解析顺序（flag > env > 项目配置文件 > 默认；配置文件一层见 [0053](./0053-project-config-file.md) 决策 2）见该决策），worker 包内脚手架只承载内建导航这一条（曾内置的示范 step 已退役，示范进 `features/steps/` 模板）：那是发行包内容，改它等于 fork。角色分工本身不变。）

## 删除的过时措辞

- `AI 确认 "..."` → 改为无关键词 `Then "..."`。否定断言 `确认页面没有 "..."` **同归一为无关键词** `Then "{自然语言}"`（AI 直接判否定陈述，如 `features/wikipedia_assertions.feature` 的 `"页面没有出现服务器错误"`），未保留该关键词 step。
- `页面地址包含 "..."` 等**预置确定性 step → 删除**（移入脚手架的"示例/按需自建"，不在 generic 预置）。
- 早先"显式断言锚点=QA 点名让 AI 看"（[0015](./0015-v1-positioning-smoke-not-regression.md) 原措辞）澄清：QA 点名仍走默认 AI 层（写自然语言）；确定性 step 是工程角色的另一套，不混。
