# BDD runner 退役：核心库自解析 Gherkin + 两腿薄 worker（确定性 step = worker 注册表）

核心库（v1.0）落地执行形态时的关键转向：**不再让每条腿跑整个 BDD runner（cucumber-js / pytest-bdd），而是核心库自己解析 `.feature`、把每个 step 派发给一个薄 worker 子进程。** 本 ADR 记录这个转向（代号 B1）、它退役了哪些 hack、确定性 step 怎么扩展、以及对 [0019](./0019-feature-tags-scope-and-engine.md)/[0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md)/[0021](./0021-local-cucumber-patch-step-keyword-disambiguation.md) 的影响。执行架构总成见 [0016](./0016-execution-architecture-core-lib-run-model.md)。

## 两个候选

| | **B2：子进程 = 现有 BDD runner** | **B1：子进程 = 薄 worker，核心自解析（选中）** |
|---|---|---|
| 核心做什么 | 只按 scope/tag 浅筛+调度，把过滤后的 `.feature` 丢给子进程 | **解析 Gherkin AST + 分组 scope**，把「这个 scope 的 steps」发给 worker |
| 子进程做什么 | 跑整个 cucumber-js/pytest-bdd，**重新解析**再执行 | 只把每个 step 派发成 `act/aiAct` 或 `assert+投票`，打到会话上 |
| 解析 | **两套 parser**（核心浅筛 + runner 深解析） | **单一事实源**（核心）—— 符合 [0016](./0016-execution-architecture-core-lib-run-model.md) 字面 |
| cucumber 补丁（[0021](./0021-local-cucumber-patch-step-keyword-disambiguation.md)） | **继续背着** | **退役** |

## 决定：B1，理由

1. **它就是 [0016](./0016-execution-architecture-core-lib-run-model.md) 字面写的**「核心解析 `.feature` → 分组 scope → 调度 → 收集结果」。B2 把解析留在 runner，核心并不真正拥有解析，与窄腰定义相悖。
2. **退役一批 hack**（见下）。
3. **我们的「通用 step」模型几乎没用到 BDD runner 的价值**：它只有**一条 catch-all pattern**（[0018](./0018-generic-steps-capability.md)/[0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md)），不是丰富的 step 库。留着 runner 纯粹是为它的解析，而解析核心自己做更干净。
4. **丢的是装饰器，不是逻辑**：开会话、act、投票、确定性 handler 的代码全搬进 worker 复用，只脱掉 `@when/@then`/`scenarios()` 这层外壳。

**代价**：放弃「包一层就能用」的省事；要写个小 Gherkin 解析+派发（Python 侧用官方 `gherkin-official`）。值得——scope 分组、RunReport 归集本来也要在核心写。

## worker 进程跑什么（一次调用 = 一个 scope = 一个 job）

核心**对一个 scope** spawn 一个 worker 子进程。worker 的一生：

1. **启动**：从 stdin/临时文件接收输入——这个 scope 的 scenario 列表（每个含有序 steps：关键字+文本）、引擎配置。
2. **开会话**：建一个 AgentCore 浏览器会话（**这段就是现 `generic.steps.ts` 的 Before hook / `nova_ctx` fixture 已跑通的代码**，原样搬进 worker 启动段）。
3. **按 scope 串行跑 scenarios**：对每个 step——
   - 先查 worker 的**确定性 step 注册表** → 命中走 handler（精确 assert、不投票）；
   - 未命中 → 落到 catch-all → 走 AI（When→`act`/`aiAct`；Then→`assert`+多次投票）。
   - 会话在 scope 内 scenario 间**共享**（scope=串行共享会话，[0019](./0019-feature-tags-scope-and-engine.md)）。
4. **收结果**：每 scenario 产出 pass/fail、投票抖动数据、原生报告引用（Midscene html / Nova trajectory 路径）。
5. **回传 + 退出**：结构化结果（JSON）写回 stdout/结果文件，关会话，进程退出。

核心**永不 import 引擎**：只 spawn、喂 JSON、读 JSON。这就是 [0016](./0016-execution-architecture-core-lib-run-model.md) `Engine` port 两个 adapter「形状一致」的含义。

## 确定性 step 怎么扩展（test engineer 的扩展点）

> **实现状态（v1.0 当前）**：下述 `@deterministic` 注册表**尚未落地**——Nova worker（`novaact/worker/run_scope.py`）当前只有**内建的 URL→导航确定性分支**（step 文本含引号内 URL → `go_to_url`，[0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md)），其余 step 走默认 AI catch-all（When→act / Then→act_get+投票）。下文描述的「test engineer 自注册任意确定性 step」是**留口子的设计目标**，待真实需求出现时建。

**扩展点 = 对应 worker 里的一张 step 注册表**（`(模式 → handler)`）。延续 [0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md) 的脚手架定位与角色边界（QA 永远只写人话、不碰确定性 step）：

```python
# novaact worker 内（midscene worker 是对称的 TS 版）
@deterministic(r'当前 URL 匹配 "(?P<pattern>.+)"')
def url_matches(ctx, pattern):
    assert re.search(pattern, ctx.page.url)          # 拿会话/CDP 句柄精确判定，不投票

@deterministic(r'元素 "(?P<sel>.+)" 的颜色是 "(?P<hex>#[0-9a-fA-F]{6})"')
def color_is(ctx, sel, hex):
    got = ctx.page.eval(f'getComputedStyle(document.querySelector({sel!r})).color')
    assert to_hex(got) == hex
```

设计要点：

- **几乎零写法变化**：现 `deterministic.steps.ts` / `deterministic_steps.py` 那两个空脚手架的归宿——从「被 BDD runner 自动收集」变成「被 worker 注册表收集」，test engineer 还是写个带模式的函数，只把 `@when/@then` 换成我们的 `@deterministic`。
- **匹配放 worker，不放核心**：核心只发原始 step 文本；worker 先查自己的确定性表、未命中再走 AI。确定性 handler 是**引擎特定**的（要碰 Playwright 句柄、CDP eval），匹配表跟着 handler 走最内聚；核心保持对 step 语义无知（只管解析结构 + 调度）。
- **两腿对称但各自语言**：确定性检查天然依赖引擎/CDP 的精确能力，**本就该写在对应 worker 里**（midscene=TS+Playwright，nova=Python）。这不是缺陷，是确定性检查的本质（它碰具体引擎精确 API，不像 AI step 引擎无关）。
- **冲突规则自定**（如「最多命中一条，多条报错」），比 cucumber 的 pattern 歧义可控得多——这正是 B1 退役补丁的同源好处。

## 退役清单（B1 真正删除/作废的东西）

真删的只有 4 样「BDD runner 入口管道」，**spike、sigv4 recipe、workflow_setup、step 逻辑一个都不删**：

| 退役 | 原因 |
|---|---|
| `midscene/cucumber.mjs` | worker 形态不需要 cucumber 入口 |
| `midscene/patches/@cucumber+cucumber+13.0.0.patch` + `postinstall` | **B1 核心红利**：核心从 AST 直接知道关键字，When/Then 歧义消失（[0021](./0021-local-cucumber-patch-step-keyword-disambiguation.md) 那个 pattern-only 匹配问题不复存在） |
| `novaact/bdd/conftest.py`（tag 路由 hook） | engine 路由改由核心调度层做（[0019](./0019-feature-tags-scope-and-engine.md)） |
| `midscene/bdd/package.json`（`{type:module}`） | 折叠进 worker 工程配置 |

**存活/迁移（不删）**：`agentcore-sigv4.mts`、`workflow_setup.py`（worker 进程内直接用）；`generic.steps` / `test_generic_steps` 的**逻辑**（开会话/act/投票，迁入 worker，脱装饰器）；`deterministic.steps` / `deterministic_steps`（迁入 worker 注册表）；全部 spike 与 `SIGV4-FETCH-RECIPE.md`（独立可跑的证据，[0010](./0010-spike-as-apples-to-apples-benchmark.md)，保留在 `spike-validated` tag 与各引擎 `spikes/`）。

## 对既有 ADR 的影响

- **[0021](./0021-local-cucumber-patch-step-keyword-disambiguation.md)（cucumber 补丁）→ 基本作废**：补丁是「BDD runner 入口 + pattern-only 匹配」的产物；B1 下核心从 AST 知关键字，问题消失。0021 作为决策史保留（记录我们曾用 patch-package 解歧义、为何、后来为何退役）。
- **[0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md)（默认 AI / 少数派显式）→ 语义保留，实现层转移**：「裸 `When/Then` 人话→默认 AI；确定性=脚手架」的语义不变；落地从「cucumber 补丁 + pytest-bdd 原生区分」转为「核心解析关键字 + worker catch-all/注册表派发」。0020 里「Midscene 靠补丁」那段被本 ADR 取代。
- **[0019](./0019-feature-tags-scope-and-engine.md)（scope/engine tag）→ 语义保留，实现层转移**：tag 语义不变；tag 的读取/路由/scope 调度从「两套 runner 各自方言（cucumber `--tags` / pytest-bdd conftest marker）」统一为「核心解析 tag + 调度」。0019 留待核心库的「调度实现」即由本转向落地。
- **[0016](./0016-execution-architecture-core-lib-run-model.md)**：本 ADR 是其「核心解析→分组→调度」与 `Engine` port 的具体落地形态。

## 重议

- 若将来通用 step 之外确实需要丰富的 step 库 / BDD 报告生态，重新评估是否引回某种 runner。当前「一条 catch-all + 少量确定性锚点」的模型不需要。
