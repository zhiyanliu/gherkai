# `.feature` 用 Gherkin tag 声明 scope 与 engine（G1/G2）

> **状态：tag 语义保留，实现层已转移（见 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)）。** `@scope:`/`@engine:` 的语义**不变**。但其读取/路由/调度从「两套 runner 各自方言（cucumber `--tags` 过滤 / pytest-bdd conftest 把带值 tag 转 marker + skip）」统一为「核心库解析 tag + 调度层据 tag 分组/选腿」。下文「已验证」段描述的两套 runner 消费机制是 v0.x 形态；本 ADR 留待核心库的「调度实现」即由 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md) 落地。

QA 在 `.feature` 里用 **Gherkin 原生 tag** 声明两类配置元信息：会话作用域（scope，G1）与引擎选择（engine，G2）。配置走结构化 tag、测试意图走自然语言 step——各司其职。

## 为什么 tag（而非自然语言/外部配置）

- scope/engine 是**配置**不是**测试意图**；配置该精确可解析，tag 是 Gherkin 标准做法。
- QA 学一两个 tag 约定（`@scope:` `@engine:`）成本远低于"让机器从自然语言里猜配置意图"的不可靠。
- 不放外部配置文件：避免用例与配置两处维护、对应关系易漂移。
- **两腿可解析已实查确认**：cucumber-js 经 `Before` hook 的 `pickle.tags` 拿原始 tag；pytest-bdd 经 `scenario.tags`（带值 tag 不强制转 pytest marker，可取原始字符串）。带值 tag `@scope:x`/`@engine:x` 两腿都读得到。

## tag 语义

### `@scope:<name>`（G1 — 会话作用域）
- 相同 `@scope:X` 的 scenario 归入**同一 scope**：串行、共享浏览器会话/上下文（有操作依赖，如"登录"→"在登录态下改昵称"）。
- 不同 scope 值之间：**并行**、互不共享。
- 未标 scope 的 scenario：各自独立（自成一个单元）。
- scope 是**执行单元 = Job**（[0016](./0016-execution-architecture-core-lib-run-model.md)）。

### `@engine:<midscene|novaact>`（G2 — 引擎选择）
- engine 在语义上是 **scope 级属性**：一个 scope 统一一个引擎。根因——engine = 浏览器会话归属，scope = 会话边界，二者物理绑定（两引擎是两个不共享的 AgentCore 会话，[0006](./0006-form-a-two-subprojects-no-orchestrator.md)/[0011](./0011-agentcore-browser-system-default-vs-custom.md)）。
- **声明方式（容错缺省）**：QA 只需在该 scope 的**任意一个** scenario 上标 `@engine:`，其余 scenario 继承本 scope 的 engine（不必每条都标）。
- **冲突即报错**：同一 scope 出现**多个不同** engine 值 → 配置错误，拒绝运行（不静默取某个——违背可信红绿）。**原因**：同一 scope 跨引擎 = "既共享会话又是两个不共享的会话"，物理自相矛盾。
- **缺省**：整个 scope 未标 engine → 用默认引擎（单腿默认，[0016](./0016-execution-architecture-core-lib-run-model.md)）。
- **双腿交叉验证 = v1.0 不做**（降级，见下「双腿的真实价值」）。`@engine:` 在 v1.0 只做**选腿**（单腿默认），不内建交叉。

## 示例

```gherkin
# step 措辞见 ADR 0020（默认 AI：When/Then 后跟纯人话，无路由关键词）
@scope:login @engine:midscene
Scenario: 登录
  Given 打开 "https://app.example.com"
  When "用账号密码登录"

@scope:login                       # 继承 scope:login 的 engine=midscene；与上条串行、共享会话
Scenario: 在登录态下修改昵称
  When "进入设置，把昵称改为 Alice"
  Then "昵称已变为 Alice"
```

## 范围（tag 语义已定 / 调度实现待核心库）

- **语义已定（本 ADR）**：定 `@scope:`/`@engine:` 语义；两腿各验证"能读到 tag 并据 `@engine:` 选腿"的最小行为（engine 选择无需调度，可立即验，v0.x 已做）。
- **待 v1.0 核心库**：scope 分组 + engine 冲突**校验**的实现见 [0025](./0025-plan-module-feature-to-jobs.md)（plan 模块）；job 间（=scope 间）并行**调度**、会话共享见 [0026](./0026-schedule-module.md)（schedule 模块；scope 内串行已被 worker 消化）。它们需要核心库，bdd 直跑层做不了。执行形态见 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)。

## 已验证（v0.x，2026-06）：`@engine:` 路由两腿对称成立

两腿都能读 tag、据 `@engine:` 正确分流（机制不同、语义对称）：
- **Midscene（cucumber-js）**：`--tags "@engine:midscene"` filter → 只跑本腿 scenario、跳过 `@engine:novaact` 那条。✅
- **Nova Act（pytest-bdd）**：`bdd/conftest.py` 用 `pytest_bdd_apply_tag` 把带值 tag 规范成 marker（冒号→下划线，如 `engine_novaact`）+ autouse fixture 据 tag skip 非本腿 → `@engine:midscene` SKIPPED、`@engine:novaact` PASSED。✅
- 再次印证 [0005](./0005-single-shared-feature-file.md)：同一份 tag，两套 runner 各用各的方式消费。

## 双腿的真实价值：是「可选择/不锁定」，不是「每次交叉」

**双腿交叉验证（同一用例两腿都跑、都过才过）v1.0 不做**。分析（[0010](./0010-spike-as-apples-to-apples-benchmark.md) 把交叉当卖点的调子据此降级）：
- **治不了主要不可靠源**：单引擎不可靠主要来自措辞歧义（交叉治不了，两腿同被歧义断言喂）与种类A抖动（投票已治，比换引擎直接）。
- **不一致时无法定责**：两腿判定不同时，分不清是被测系统 bug 还是两引擎对模糊断言理解不同（[0018](./0018-generic-steps-capability.md) 已证后者真实存在）。高噪声、低价值信号。
- **成本翻倍 + 复杂度**：2× 时间/token/会话；还要定义结果合并、不一致呈现（RunResult 数据模型本身已定，见 [0016](./0016-execution-architecture-core-lib-run-model.md)，但"同一用例两腿判定如何合并/呈现差异"是其上的新语义层，仍需另设计）。
- **与 v1.0 柔性冒烟定位不符**：冒烟要快；交叉慢一倍，废掉冒烟的核心优点。

**双腿的真实价值** = ① 按场景**选**更合适的引擎（`@engine:` 选腿）；② 一次性**选型/对比**；③ 不被单一供应商锁定。日常各用各的。

**未来若要支持交叉**：在**跑批层**把一个用例展开成"× 两个引擎"两次独立运行（不在一个 scope 标两 engine）——记为可选实现方式，非 v1.0。
