# plan 模块：`.feature` → job 列表（解析 + scope 分组）

> **Status:** Accepted

核心库把一组 `.feature` 变成可调度的 **job 列表**的模块。它兑现 [0019](./0019-feature-tags-scope-and-engine.md)/[0016](./0016-execution-architecture-core-lib-run-model.md) 一直 defer 到核心库的「scope 分组 + engine 冲突校验 + Gherkin 解析」。输出的 Job 正是 [0024](./0024-worker-core-protocol.md) worker↔core 协议的输入形状。下一块 `schedule`（scope 串/并行调度）以本模块输出为输入，另立。

## 接口（深模块，小）

```
plan(features: [{uri, text}], config: {defaultEngine, defaultAssertionVotes, defaultJobTimeout}) -> Job[]

Job = {
  scopeId, scopeName, engine, assertionVotes,   // votes 维度语义权威在 ADR 0014，本模块只透传
  timeoutS,                                     // job 墙钟预算秒（null=不超时）；tag 语义权威在 ADR 0019、
                                                // 设计取舍与三路 enforce 在 ADR 0034，本模块只解析 + 校验
  scenarios: [
    { id, name, steps: [ { index, keyword, text, argument? } ] }
  ]
}
```

- **接受 feature 内容（`{uri, text}`）而非路径** → core 不碰文件系统（skill：accept dependencies, don't create them），纯数据 in / 纯数据 out，可被 test 直接喂字符串。读文件是组合根/CLI 的事。
- **输出 `Job[]` = [0024](./0024-worker-core-protocol.md) 协议输入形状**：一个 Job = 一个 scope = 一个会话边界 = schedule 交给单个 worker 的活。
- **删除测试**：删掉本模块，「按 tag 分组 + engine 校验 + Gherkin 展开」会在 CLI / 未来 WebUI 各写一遍 → 它在挣钱。

## 内部实现（深，但借力官方 Compiler）

两个 internal seam：

### `parse`（藏第三方库 gherkin-official）

- 每个 feature：`Parser().parse(text)` → 原始 AST → `Compiler().compile({**doc, "uri": uri})` → **pickles（完全展开）** → 映射成我们的领域模型 `{id, name, steps:[{index, keyword, text, argument?}]}`。（`Compiler().compile()` **要求 `gherkin_document` 带 `uri` 键**，缺则 `KeyError`——故 `uri` 是 parse 的必填燃料，不只是关联键元数据。）
- **Background / Scenario Outline+Examples / DataTable / DocString 三档由 Compiler 展开**（实测 `gherkin-official` 已装版可一步给出：Background 前插每个 scenario、Outline 按 Examples 行笛卡尔展开成 N 个 scenario、`<placeholder>` 已插值、DataTable/DocString 已归入 step `argument`）。**不自己写展开**——其边角（And/But 的 Conjunction keywordType 继承、多 Examples 表 + 三层 tag 合并、Rule 层 background 叠加、占位符转义）cucumber 官方都处理好且有跨语言一致性测试背书，自己重写 = 维护一份 cucumber compiler，不值。
- **step 保持 pickle 内顺序 = feature 书写顺序**（见下「step 顺序」语义）。
- **`keyword` 字段（实测要点，避免踩坑）**：pickle step **不含字面 keyword**，只暴露归一化 `type`（取值 `Context`/`Action`/`Outcome`，And/But 已折叠继承上一条非连接词的类型）。parse 把 `type` 映射成我们领域模型的 `keyword`，**统一取书写词 `Given`/`When`/`Then`**（`Context→Given`、`Action→When`、`Outcome→Then`）与 [0024](./0024-worker-core-protocol.md) 示例一致；worker 只需「是不是 `Then`（断言）」这个类别即足够派发（[0024](./0024-worker-core-protocol.md)），故 And/But 字面丢失无碍。
- **`index`**：scenario 内 0-based 书写序号，由 parse 合成（pickle step 无此字段），作 [0024](./0024-worker-core-protocol.md) `stepIndex` 的回指键、不参与重排。
- **`argument`**：承载展开后的 dataTable/docString（有则有、无则缺省）；其内部形状（重映射成自有 `{kind, content/rows}`、不透传 pickle 子 dict）见下「第三方库 seam」节。
- **行号来源（id 派生依赖）**：pickle **不带 `location`/行号**，只有顶层 `astNodeIds`。parse seam **内部同时持有 AST**，用 pickle 的 `astNodeIds` → AST 节点 `location.line` 回查行号（供下「id 派生」用）；Outline 展开的 example 行号取 `astNodeIds` 中的 Examples 行节点。行号属 seam 内部细节，不外泄。

### `scope`（tag 分组 + engine 校验）

- 读每个 scenario 的 tag → 按 `@scope:<name>` 分组 → 每组解析 `@engine` → 产出 Job。
- 语义见下。

## 已定语义

### scope 全局命名空间（跨文件合并，撞名 warning）

- 相同 `@scope:X` 的 scenario 归同一 scope，**无论在哪个 `.feature` 文件**——忠于 [0019](./0019-feature-tags-scope-and-engine.md)「相同值同 scope」字面语义，保住「一条 session 线可跨文件组织」的表达力。
- **跨文件合并时打 warning log**：多人写不同 feature 可能意外撞名 → 意外串到一个会话/串行。warning 给可见信号，不阻断（合并仍按字面语义生效）。
- **未标 `@scope` 的 scenario**：各自独立 = 各自一个**单元素 scope = 各自一个 job/会话**（[0016](./0016-execution-architecture-core-lib-run-model.md) job=scope 的直接推论）。其成本含义（N 个独立 scenario = N 个会话）由 schedule 的并发上限治理，不是 plan 的事。

### 一个 scenario 多个 `@scope` 值 → 报错（feature 级传播允许）

- **背景**：Gherkin 标准里，贴在 **Feature 行**的 tag 会**下传给该 feature 的每个 scenario**（gherkin-official 编译出的 pickle `tags` 已合并 feature 级 + scenario 级）。故一个 scenario 可能同时背 feature 级 `@scope:login` + 自身的 `@scope:checkout` = 两个不同 `@scope` 值。
- **裁决（与 engine 冲突对称）**：一个 scenario 解析出**多个不同 `@scope` 值 → 报错、拒绝运行**。理由同 engine：scope = 会话边界，一个 scenario 只能属一条会话线，同属两个 scope 物理自相矛盾。
- **feature 级 `@scope` 传播仍允许**：在 Feature 行标 `@scope:X` 让整个文件归一个会话，是受支持的便利写法——只要其下没有 scenario 再标一个**不同**的 `@scope` 值（标相同值无害、不算冲突）。

### engine 解析（scope 级，规则同 [0019](./0019-feature-tags-scope-and-engine.md)）

本模块兑现 engine 解析的校验实现；规则与否决理由的权威在 0019。三种情形：
- 整 scope 未标 `@engine` → 用 `config.defaultEngine`；
- scope 内任一 scenario 标了 → 全 scope 继承；
- 同 scope 多个不同 engine 值 → 报错拒运行（物理自相矛盾）。

### timeout 解析（scope 级，规则同 [0019](./0019-feature-tags-scope-and-engine.md)）

本模块兑现 job 墙钟预算（`@timeout:N`）解析的校验实现，与 engine 解析同构；tag 语义权威在 [0019](./0019-feature-tags-scope-and-engine.md)、两层设计取舍与三路 enforce 在 [0034](./0034-detached-batch-reconciler.md)「job timeout」节，本模块只解析定值、填进 `Job.timeoutS`：
- 整 scope 未标 `@timeout` → 用 `config.defaultJobTimeout`（未给 = 不超时）；
- scope 内任一 scenario 标了 → 全 scope 继承；
- 同 scope 多个不同 `@timeout` 值 → 报错拒运行（一个 job = 一个预算，同 engine 冲突先例）；
- 值非**有限正数**（非数字 / `<=0` / `nan` / `inf`）→ 报错（「标了 tag 却想不超时」不成立——删 tag 走缺省即可，不静默当无预算）。`nan`/`inf` 须**显式**拒：`float()` 收它们（`nan`/`inf`/`1e400` 都不抛）且都不满足 `<=0`，而三路推进器一律用 `>` 比较 deadline/预算——nan 让比较恒 False、inf 是无穷预算，两者都把「标了 tag」静默变成「永不超时」（校验器用 `math.isfinite` 拦）。

### step 顺序 = 书写顺序，keyword 只决定派发

- worker 拿到的 steps **严格按 feature 书写顺序**，逐条执行；**keyword 不约束顺序、不触发重排**。
- 合法且要支持乱序：`Given→Then→When→Then`（现有 `features/wikipedia_assertions.feature` 就是真实样本）——Then 在 When 前 = 就在那个时点判定。Gherkin 关键字本不强制 Given/When/Then 顺序，我们忠于此。
- keyword 的唯一作用 = worker 派发（`When`→AI 动作 / `Then`→AI 断言+投票 / URL 形态→确定性导航 / 命中注册表→确定性，见 [0024](./0024-worker-core-protocol.md)/[0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md)）。core 不消费 keyword 的顺序语义。
- **keyword 判不出 = 拒绝猜（fail-fast，首轮 code-health 逼出）**：gherkin Compiler 对 `*` 步骤与「无前驱非连接词」的首条 And/But 给 `type='Unknown'`（实测 gherkin 41.0）——此时派发语义无从判定，曾静默兜底成 Given，会把本该是断言的 step 当动作派发、断言永不执行（假绿方向的静默错标）。现抛 `PlanError` 让用户写明关键字；有前驱的 And/But 照常继承、不受影响。回归护栏 `core/tests/test_plan.py` 的 fail-fast 两用例。

### id 派生（RunStore/RunReport 关联键：稳定 + 可追溯）

**id 是不透明标识符**：`scenarioId`/`scopeId` 只在 JSON/dict key/未来 DB key 用（全支持任意 UTF-8），core **不拿它当路径解析**。**不对 id 做 normalize**——清洗字符（空格→下划线、删非 ASCII 等）会把不同输入映射成同一输出、**制造撞名**，而撞名是静默灾难（schedule 归位错乱、DB 主键冲突），远比「id 含空格/中文」严重。故含空格/中文的 uri **原样保留**。若未来某消费层（URL/文件名）需安全字符 id，由该层做**可逆**编码（urlencode 等、保唯一），不在 core 做有损转换。

**`uri` 约定 + 互异契约**：plan 把调用方传入的 `uri` **原样**用作 id 前缀，**不做路径解析**（plan 不碰 FS、无 base dir）。调用方（组合根/CLI）负责传**稳定可读且互异**的 `uri`。**plan 入口校验 uri 互异——重复 = 接口违约 → 报错**（同一文件喂两遍会撞 scenarioId、结果错乱；这是脏输入，fail-fast，不静默吞）。注意这与「跨文件同 `@scope` 合并」（领域语义、warning）**正交**：前者是 uri 重复（bug、报错），后者是不同 uri 但同 scope 值（有意、合并、warning）。收集去重等便利逻辑由调用方负责，core 窄腰只接 uri 互异的列表。下文 id 规则统一以 `<uri>` 表示。

- `scenarioId`：`<uri>:<scenario行号>`；Outline 展开的多个 scenario 共享 scenario 行号，故各自再加 `:<example行号>` 消歧（行号取自 AST，见上「行号来源」）。
- `scenarioName`：Scenario 标题（`<placeholder>` 已插值）；Outline 展开的多个 scenario 若标题模板不含占位符会重名，故**追加 Examples 行标识**（实现用 `[@<example行号>]`，如 `登录 [@15]`）保证可区分、可追溯。
- `scopeId`：有 `@scope:X` → 用 `X`（干净 token）；无标 → 各 scenario 自成单元素 scope，`scopeId` **= 该 scenario 的 `scenarioId`**（直接复用，自动继承上面的 Outline `:<example行号>` 消歧，不会撞 id）。
- `scopeName`：有 `@scope:X` → `@scope` 原值（可含空格/标点的人写名）；无标 → 取该 scenario 的标题（人写名），**不复用机器派生的 `scopeId`**（保持 name = 人写展示名的语义，对齐 [0024](./0024-worker-core-protocol.md)）。
- 行号稳定（feature 不大改即不变）、人可读出来源。若未来需更强稳定性可引 `@id:` tag，暂不做。

## 第三方库 seam（gherkin-official 藏在 parse 后）

- core 只认我们的领域模型 `{id,name,steps[{index,keyword,text,argument?}]}`；**gherkin 的 pickle dict 形状不外泄**到 core 其余部分。
- **`argument` 是 parse 重映射成的自有形状、不透传 pickle 子 dict**：实测 pickle 的 argument 是 `{docString:{content}}` / `{dataTable:{rows:[{cells:[{value}]}]}}` 这类 gherkin 内部结构；parse 把它归一成我们自有的简洁形状（如 `{kind:"docString", content}` / `{kind:"dataTable", rows:[[cell…]…]}`），避免 pickle 形状经 argument 漏进领域模型。
- 这是个 seam，但**性质 = 单实现（gherkin-official）+ 防御性封装**，**非** [0024](./0024-worker-core-protocol.md) `Engine` port 那种「两个真 adapter」的 seam（那里 engines/midscene/novaact 是两个真实现）。立得住靠两个理由：① [0024](./0024-worker-core-protocol.md) 的 step 领域模型 ≠ pickle 形状，本就要转换层；② 本项目有被第三方解析库行为坑过的教训（cucumber 补丁 [0021](./0021-local-cucumber-patch-step-keyword-disambiguation.md) → 已退役、core 自解析 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)），把库行为收在一个接口后，升级/适配/替换只动 `parse` 内部。（下条「升级 ≥31.0.0 回归比对」是**同库版本迁移**，非引入第二个解析器实现。）
- 版本（实装）：**core 子工程装 `gherkin-official 41.0.0`，直接用顶层导出 `from gherkin import Parser, Compiler`**（≥31.0.0 起提供顶层导出）。导入名 `gherkin`。（novaact 子工程**不依赖 gherkin-official**——worker **不 import gherkin**、不解析 `.feature`（解析是 core 的事，[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)），故 core 用哪版 gherkin 与 worker 无版本耦合。）**不依赖 pytest-bdd 的内部解析符号**（既要退役、又是非公开 API）。Parser→dict、Compiler→pickles 这套核心契约跨大版本稳定；升级后用同一 feature 回归比对一次。

## test cases（护栏，本模块强制）

「三档全支持」必须有测试背书（否则边角易漏）。覆盖：

- Background 前插每个 scenario；
- Scenario Outline 按 Examples 多行展开 + `<placeholder>` 插值；**且展开后 N 个 scenario 的 id 与 name 各自可区分**（id 靠 `:<example行号>`；name 追加 Examples 行标识，避免 N 个同名）；
- DataTable / DocString 进 step `argument`（重映射成自有形状，非 pickle 子 dict）；
- 乱序 `Given→Then→When→Then`（保序、不重排）；keyword 由 pickle `type`（Context/Action/Outcome）映射成 `Given/When/Then`；
- 跨文件相同 `@scope` 合并（+ warning）；
- **重复 uri → 报错**（接口违约；与上一条跨文件 `@scope` 合并正交：那是 warning、这是 error）；不同 uri 即便内容相同 → 放行；
- 同一 scope 多个不同 engine → 报错；
- 一个 scenario 多个不同 `@scope` 值（feature 级传播 + scenario 级）→ 报错；feature 级 `@scope` 传播（无冲突时）→ 正常归一个 scope；
- scope 缺省 engine → 用 defaultEngine；
- 同一 scope 多个不同 `@timeout` → 报错；`@timeout` 非数字 / `<=0` / `nan` / `inf`（含 `1e400` 溢出成 inf）→ 报错；
- timeout 缺省兜底 + tag 优先（同一批里标了 `@timeout` 的 scope 走 tag、未标的走 `defaultJobTimeout`）；无 tag 又无缺省 → 不超时；
- 未标 scope 的 scenario → 各自独立成 job（含未标 scope 的 Outline → N 个 job 不撞 id）；
- id 派生稳定可追溯。

## 现在做 / 留口子

- **现在做（v1.0）**：上述 `plan` 接口、parse（借 Compiler）、scope 分组 + engine 校验、id 派生、三档 Gherkin 特性、test cases。
- **留口子不实现**：`@id:` 显式 id tag；Rule 层级的特殊处理（Compiler 已展开，暂不暴露 Rule 概念到领域模型）；feature 级 tag 的更多语义（现仅 `@scope`/`@engine`）。

## 重议

- 若 Gherkin 特性展开行为随 gherkin-official 升级变化 → 只动 `parse` 内部 + 回归 test cases。
- 若出现 id 跨运行不稳的真实痛点（feature 频繁改行号）→ 引 `@id:` tag。
