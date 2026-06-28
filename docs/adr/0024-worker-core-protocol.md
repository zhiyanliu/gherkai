# 核心↔worker 协议：流式 JSON 契约 + 成本信封（非对称 by design）

定义核心库（`core/`）与引擎 worker 子进程之间的**唯一契约**：core 喂什么、worker 回什么。这是 v1.0 的「窄腰中的窄腰」——`parse`/`schedule`/两腿 worker/RunReport 全依赖它，设计错则全线返工。它同时兑现 [0016](./0016-execution-architecture-core-lib-run-model.md) 一直 defer 的「数据模型字段级 schema」（协议字段 = RunResult/RunReport 的字段来源）。执行形态（两腿都子进程、B1 薄 worker）见 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)。

## 设计原则：深模块、小接口

协议接口（调用方必须知道的一切）按「跨引擎概念 vs 引擎特定细节」分两层，保持**小而深**：
- **一等字段** = core 要理解/分支的跨引擎概念（status、votes、cost_usd、errorType、reportRefs）。删了它们域价值就消失（删除测试）。
- **引擎特定细节 / core 不分支的信息** = 收进带标签的子对象（cost 的 `evidence`、reportRefs 的 `granularity` 标签等），core 存但不解析、不分支。引擎差异与派发细节不抬进顶层接口。

> 反面（被拒）：把每个引擎的富返回值（Midscene 的 token/dump、Nova 的 metadata）摊平进协议顶层 → 宽接口、浅模块、消费者要按引擎特例化。实查证实两腿返回形状高度非对称（见下「实查依据」），更要靠分层把非对称收进子对象。
>
> **删除测试逼出的两处收窄**（深模块审计 2026-06）：① 原顶层 `cost.tokens` 下沉进 `evidence`——core 对 token 无任何分支（汇总靠 `cost_usd`、可信度靠 `precision`），放顶层是机制泄漏且逼出 Nova 的 `null` 空洞。② 原 `kind` 字段从顶层删——core 对一个 step 唯一在乎的是「有没有 `votes`」（=是不是 AI 断言，影响抖动汇总）；`navigate/ai_act/deterministic` 之间的区别是 **worker 的派发细节**，core 不消费（对齐 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)「core 对 step 语义无知」）。

## 输入（core → worker）：一个 scope 的活

一个 scope 输入 = core 的 plan 模块（[0025](./0025-plan-module-feature-to-jobs.md)）产出的一个 **Job**；core 解析 `.feature` 成有序 step 序列发给 worker，**worker 不碰 `.feature` 文件**（单一解析事实源在 core，[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)）。Background/Outline/DataTable/DocString 已在 plan 阶段展开（[0025](./0025-plan-module-feature-to-jobs.md)），worker 只见展开后的有序 step。

```jsonc
{
  "scope":  { "id": "login", "name": "login" },   // name=@scope tag 原值(可含不宜做 key 的字符)；
                                                  // id=core 派生的干净 key。未标 scope → core 生成两者。
  "engine": "midscene",                           // core 已完成 @engine 冲突校验(见 0019)
  "scenarios": [
    {
      "id": "...", "name": "搜索 OpenAI 并进入词条",  // name=Scenario: 标题；id 同理派生/生成
      "steps": [
        { "index": 0, "keyword": "Given", "text": "打开 \"https://...\"" },
        { "index": 1, "keyword": "When",  "text": "在搜索框输入 OpenAI 并提交搜索" },
        { "index": 2, "keyword": "Then",  "text": "当前页面是关于 OpenAI 的维基百科词条页" }
        // step 可选带 "argument"：承载 DataTable/DocString 等多行参数（见 0025），有则有、无则缺省
      ]
    }
  ]
}
```

- **`{id, name}` 双标识**：与 scenario 给 QA 的配置心智一致；name 是人写的原值（tag/标题，可含空格/标点），id 是 core 派生的稳定干净 key（用作 RunStore/RunReport 的关联键）。id 派生规则见 [0025](./0025-plan-module-feature-to-jobs.md)。
- **step.`argument`（可选）**：承载展开后的 DataTable/DocString（[0025](./0025-plan-module-feature-to-jobs.md)）；有则有、无则缺省。worker 把它连同 `text` 一起喂引擎。
- worker 拿 `keyword` + `text` 决定派发（见下「worker 派发」），拿 `text`(+`argument`) 喂引擎。

## 输出（worker → core）：流式 JSON Lines

worker **边跑边流式上报**（每行一个事件），core 实时收。选流式而非「跑完整 scope 一次性回整块」（**本 ADR 新决策**——[0016](./0016-execution-architecture-core-lib-run-model.md) 的 `Engine port: runScope(scope) → JSON 结果` 措辞偏向单次返回，此处细化为流式增量）的理由：① 跑批时能看进度；② worker 中途崩溃仍有部分结果；③ 为未来 WebUI 实时进度铺路。代价（实现略复杂）可接受。

**事件顺序不变量**（接口的一部分，core 假定有序、乱序为 worker 违约）：`scenario_started` 必先于其 `step_done`；`scenario_done` 收尾本 scenario；`scope_done` 收尾全 scope（且为流的最后一条）。

**传输通道：三通道分离（实现期细化，子进程 worker）**——0024 事件**不走 stdout**，而走一条专用管道，与引擎 SDK 的进度噪声、worker 自身诊断物理隔离：
- **事件通道**（纯 0024 JSON Lines）：core adapter 自建管道，把写端 fd 号经环境变量 `EVENTS_FD` 告知 worker（`pass_fds` 让子进程继承该 fd 但**不重映射 fd 号**，故不硬编码 3；worker 读 `EVENTS_FD` 打开事件输出）。
- **stdout**：留给引擎 SDK 的进度噪声（Nova Act 把 `act(...)`/trajectory 路径打到 stdout）——adapter 当日志透传，不解析。
- **stderr**：worker 自身诊断/错误——独立通道，不被 SDK 噪声淹。
- 调试回落：worker 无 `EVENTS_FD`（手动直跑、无 adapter）时事件回落 stdout，便于 `echo job | worker` 看输出。
- 起因：真跑发现 Nova Act SDK 把进度信息打进 stdout，会污染事件流（被当 JSON 解析失败）——故把事件挪到专用 fd。

```jsonc
{"type":"scenario_started","scenarioId":"..."}
// 动作步：无 votes（core 据此知道它不是 AI 断言，不纳入抖动汇总）
{"type":"step_done","scenarioId":"...","stepIndex":1,"status":"passed","cost":{...}}
// AI 断言步：有 votes（core 据此纳入抖动汇总）
{"type":"step_done","scenarioId":"...","stepIndex":2,"status":"passed","votes":{"yes":3,"total":3},"cost":{...}}
// AI 断言失败：投票没过多数
{"type":"step_done","scenarioId":"...","stepIndex":2,"status":"failed",
   "votes":{"yes":1,"total":3},"errorType":"assertion_failed","message":"AI 断言未过多数票(1/3)：..."}
{"type":"scenario_done","scenarioId":"...","status":"passed","reportRefs":[{"granularity":"act","path":"..."}]}
{"type":"scope_done","scopeId":"login","sessionId":"...",
   "reportRefs":[{"granularity":"scope","path":"midscene_run/report/xxx.html"}],
   "costRate":{"nova_act_usd_per_agent_hour":4.75}}
```

- **`cost` 只挂 `step_done`**；scenario/scope 级美元数由 **core 累加 step 的 `cost.cost_usd` 得出**，事件不重复携带（避免双重真相源）。
- **`scopeId`**（= 输入 `scope.id`，RunStore/RunReport 关联键）随 `scope_done` 回；`sessionId` 是语义不同的 AgentCore 会话血缘，二者都带。
- step 不再带 `kind` 字段：core 靠 `votes` 的**存在与否**区分「AI 断言（纳入抖动汇总）vs 其余」即足够；worker 内部如何派发（导航/动作/确定性）是其实现细节，不进协议（见上「删除测试逼出的两处收窄」②）。

### 字段语义

**标识字段**（回指输入的关联键）：
- **`scenarioId` / `stepIndex`**：回指输入的 `scenario.id` / `step.index`，把事件挂回具体 scenario/step。
- **`scopeId`**：回指输入 `scope.id`（RunStore/RunReport 关联键）。
- **`sessionId`**：AgentCore 会话 id（血缘，进 RunStore 控制面，[0016](./0016-execution-architecture-core-lib-run-model.md)）；与 `scopeId` 语义不同。

**一等字段**（core 要理解/分支）：
- **`status` 三态**：`passed` / `failed`（断言投票没过 = 测试发现了问题）/ `error`（引擎抛异常 = 没能跑完测试）。`failed` 与 `error` 语义不同，worker 负责区分——前者是测试结论，后者是执行故障。
- **`votes`**：step 是 AI 断言时才有，记 tally `{yes, total}`——够算抖动率（[0014](./0014-ai-first-assertions.md) 投票治种类A抖动），不记每票细节（两腿都拿不到 per-vote thought）。**`votes` 的存在与否即 core 区分「AI 断言 vs 其余」的唯一依据**（取代了原 `kind` 字段）。
- **`errorType` + `message`**（规范化失败分类）：`errorType` 取自固定类别集，让 RunResult/未来重试能按类型分支；`message` 是人类可读诊断。**`failed` 与 `error` 两态均可带 `errorType`**（`failed`→`assertion_failed`；`error`→其余执行故障类）。**两腿映射**：Nova Act 有丰富异常树（按类映射），Midscene 只抛通用 `Error`（归 `engine_error`）。初始类别集：`assertion_failed`（断言没过）/ `timeout` / `guardrail` / `engine_error`（引擎内部/通用异常）/ `navigation_error`。类别集可随真实失败样本扩充。

**core 不分支的附加信息**（存进 RunReport，不进 core 逻辑分支）：
- **`reportRefs`**：list，每项带 `granularity` 标签（`scope` 级 / `act` 级）。两腿报告粒度不同（Midscene 1 个 html/worker；Nova 每 act 一个 trajectory，[0010](./0010-spike-as-apples-to-apples-benchmark.md)），core **不按 granularity 分支**——有啥收啥、原样归进 RunReport 供人渲染；`granularity` 只是给渲染层的标签。

**worker 派发（不进协议，仅说明 worker 内部如何把 step 变成引擎调用）**：worker 收到 `(keyword, text)` 后按优先级派发——① 命中 test engineer 的确定性注册表（[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)）→ 精确判定、无 votes；② 否则若 step 文本含 URL 字面量（引号内 `https?://…`）→ 内建确定性导航（code 抽 URL 直接 goto/go_to_url，不浪费 AI、不跑偏），动词随意（"打开/访问/前往…"皆可，对齐 [0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md) 纯人话）；③ 否则 `When` → AI 动作（aiAct/act，无 votes）、`Then` → AI 断言（aiBoolean/act_get + 投票，带 votes）。这些区别 core 不消费，故不出现在协议字段中。

## 成本信封（cost）：dollar 轴对称、token 轴非对称——by design

产品要「成本可观测」（每 scenario/scope 一个美元数）。实查（见下「实查依据」）证实两腿计费轴根本不同：Midscene 按 LLM token、Nova Act 按 **agent 工作时长**。结论：**`cost_usd` 可对称，token 不可对称**。

```jsonc
// Midscene step 的 cost：
"cost": {
  "cost_usd": 0.0123,          // 一等、对称、可跨引擎 sum() 汇总(产品核心价值)
  "precision": "exact",        // 派生自 basis：exact | estimated——消费者据此判可信度，不必懂 basis
  "basis": "tokens",           // 判别器："tokens" | "agent_time"——判定 evidence 形状(结构标签)
  "evidence": { "prompt_tokens": 1820, "completion_tokens": 95, "total_tokens": 1915 }
}

// Nova Act step 的 cost（同一顶层形状，evidence 由 basis 判别为另一支）：
"cost": {
  "cost_usd": 0.0123,
  "precision": "estimated",    // agent_time → estimated（SDK 自标 "Approx."、且 preview 档费率未公开）
  "basis": "agent_time",
  "evidence": { "time_worked_s": 9.3, "human_wait_time_s": 0, "num_steps_executed": 4 }
}

// scope_done 上另带（见上输出示例）：
"costRate": { "nova_act_usd_per_agent_hour": 4.75 }   // 配置常量，价格变了不动 schema
```

- **`cost_usd` = 一等、对称、可汇总**：两腿都填，由 core 累加 step 得出 scenario/scope 级（事件不重复携带），是跨引擎成本汇总的产品价值所在。**不**埋进不透明袋子——那会毁掉跨引擎汇总、逼每个消费者按引擎特例化。
- **顶层只有 `cost_usd` + `precision` + `basis` + `evidence`，对两腿真正对称**（无 Nova 的 `null` 空洞）。token 计数**只活在 `evidence` 的 `basis=tokens` 分支**——core 对 token 无任何分支（汇总靠 `cost_usd`、可信度靠 `precision`），故不抬进顶层（删除测试逼出，见上）。
- **`basis` = 结构判别器**：值 `tokens`/`agent_time` 命名**机制**（决定 `evidence` 形状：token 计数 vs 时间字段），不命名可信度。理由：basis 是 evidence union 必须的结构标签；若未来出现「按时间计费但实测」的引擎，命名机制仍准确，而 measured/estimated 二分会先崩。
- **`precision` = 由 basis 派生的可信度**（`tokens`→`exact`；`agent_time`→`estimated`），**写进 schema**（不让消费者从 basis 自行反推、不外泄到 ADR 散文）：`exact` = token×单价精确；`estimated` = `time_worked_s/3600×rate`，SDK 自标 "Approx."、且 API-key/preview 档费率未公开。
- **`rate`（即 `costRate.nova_act_usd_per_agent_hour`）= 随 `scope_done` 携带的配置常量**（非一等顶层字段；默认 4.75，来源 `aws.amazon.com/nova/pricing`）：AWS 可能改价、且 preview 档费率未公开，故价格不进固定 schema。散文中称 `rate`、schema 中即 `costRate.nova_act_usd_per_agent_hour`，二者同指。

## 实查依据（2026-06，读已装源码 + 线上核实，经对抗核验）

- **Midscene**：`aiAct()→string|undefined`、`aiBoolean()→bare boolean`，**失败抛异常**（status 由 worker 捕获算出）；token/cost 在 `agent.dump…usage`（prompt/completion/total + cost）；报告路径 `agent.reportFile`（destroy 后），1 个 html/worker。
- **Nova Act**：`act()→ActResult`、`act_get()→ActGetResult(matches_schema/parsed_response)`，**失败抛异常树**（guardrail/timeout/agentFailed/限流…）；**token/cost 任何 SDK 路径都拿不到**（`ActResult`/`ActMetadata`/trajectory/wire 全无 token 字段；`InvokeActStepResponse` 只有 `calls`+`step_id`；pydantic 默认 ignore，即便服务端回 usage 也被静默丢弃）。
- **成本冒烟枪**：Nova Act 计费 = **$4.75/agent-hour**（`aws.amazon.com/nova/pricing` 逐字核实），按「真实工作墙钟时间、扣除等人时间」计；SDK 的 `time_worked_s = (end−start) − human_wait_time_s`（公式 `_calculate_time_worked`，`dispatcher.py:117-148`；"Approx. Time Worked" 字样在 `dispatcher.py:167-169` 的 `_log_time_worked`）与 AWS 计费口径一致（同按扣除等待的真实工作时长）→ `cost_usd = time_worked_s/3600×4.75` 是高保真成本估算，比 token×单价表更贴近账单。
- **两个 UNKNOWN（记为 SDK 外、v1.0 不依赖，非可用路径）**：① 线上 invoke-step 响应是否藏了被 SDK 丢弃的 usage——需真实抓包才能定；② CloudWatch/Cost Explorer 是否暴露可读的 per-act 成本指标——需 AWS Nova Act 用户指南（JS SPA，未能 fetch）。两者 v1.0 都不依赖；若未来追求精确 token 成本再探。

## 协议是测试面（skill：interface is the test surface）

core 的 `schedule`/汇总逻辑应能用一个**假 worker**（in-memory adapter，吐预设的 JSON Lines）测试，无需真起子进程、真连 AgentCore。这要求协议是纯数据（输入纯数据 in、事件流 out），不夹带句柄/回调——本 ADR 的 schema 满足。`Engine` port 的两个真 adapter（spawn node / spawn python worker）与这个假 adapter 形状一致（[0016](./0016-execution-architecture-core-lib-run-model.md)）。

## 终止契约（core 请求 worker 优雅停止）

协议是**单向数据流**（core 一次性喂 job → worker 流式吐事件）+ **进程级生命周期**。core 对运行中 worker 唯一需要下达的指令是「停」（超时兜底 / fail-fast 中止，见 [0026](./0026-schedule-module.md)），故不引入双向控制通道，而是把「停」做成显式契约——**分三层、各管一段，「怎么停」的机制不在协议顶层**：

- **逻辑层（协议顶层）：schedule 经 worker 句柄请求「停」**（`handle.stop(gracePeriod)`；`handle` 由 `engine.run_scope(job)` 返回、schedule 持有，见 [0026](./0026-schedule-module.md)）。schedule 只表达逻辑意图，**不懂信号/进程**。（`Engine` port 只有 `run_scope`，**不挂 stop**——句柄自己知道怎么停，无需把 handle 反传回 engine。）
- **机制层（Engine adapter / WorkerHandle）：把「停」翻成具体机制**——**子进程 adapter**：`SIGTERM` → 等 `gracePeriod`（默认 5s）→ 未退 `SIGKILL` 兜底；**未来 Fargate adapter**：`StopTask`。信号/进程是 adapter 的「进程世界」知识（[0016](./0016-execution-architecture-core-lib-run-model.md) ports&adapters），不渗进 schedule/协议顶层。
- **worker 层：worker 必须响应停止信号做清理**。子进程 worker **必须捕获 `SIGTERM`**——但**不是在 handler 里 `sys.exit`**（那会跳过 `with` 块的 `__exit__`、泄漏 AgentCore 会话，是已修的真实 bug），而是 **handler `raise` 一个 `BaseException` 子类**（如 `_Terminated`；继承 `BaseException` 而非 `Exception` 以穿透 step 级 `except Exception` 不被吞）→ 异常冒泡触发三层 `with`（Workflow / `cdp_session` / `NovaAct`）的 `__exit__` 解栈，由 `cdp_session` 内 `with browser_session` 的 `__exit__` **真正释放 AgentCore 会话**（手动 `nova.close()` 只关 Playwright 连接、关不掉会话）。SIGKILL 兜底时会话清理可能落空（已知代价）。
- **会话清理归 worker，schedule/adapter 都不懂 AgentCore**：三层都不调 StopBrowserSession，各层只认下层的契约边界（保持纯净）。
- **未来演进（控制流，记路标不实现）**：若 core 需要对运行中 worker 下达「停」之外的指令（暂停 / 取消单个 scenario / 动态调度 / WebUI 交互），届时引入**显式 core→worker 控制通道**（双向消息流），另立 ADR。当前唯一控制指令是「停」，为一条指令建通用双向协议属过度工程（删除测试）。

## 现在做 / 留口子

- **现在做（v1.0，已落地）**：上述输入/输出 schema、cost 信封、三态 status/votes 区分 AI 断言；worker 派发逻辑（URL 导航 > 默认 AI）；Nova worker 由 `time_worked_s` 算 cost_usd、`get_session_id()` 取会话血缘。
- **已实现但粗粒度（留待细化）**：`errorType` —— Nova worker 当前一律归 `engine_error`（`except Exception` 兜底），按 Nova 异常树细分（timeout/guardrail/navigation_error）留口子；确定性 step 注册表（[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)）—— 仅内建 URL→导航分支，注册表本身未建。
- **留口子不实现**：精确 token 成本（Nova 侧，等上述 UNKNOWN 有结论）；per-vote 细节；**`reportRefs`**（Nova worker 暂未设 `replayable=True` 采 trajectory 路径，事件不带 reportRefs；协议形状已留、worker 未填）；trajectory 内部结构的结构化提取。

## 重议

- 若出现第三个引擎、或某引擎计费轴变化（如 Midscene 包月）→ `basis` 判别器与 `evidence` union 扩值、`precision` 随之映射即可，顶层 `cost_usd` 接口不动。
- 若实查的两个 UNKNOWN 有结论（线上 usage 可抓 / CloudWatch 有可读成本指标）→ Nova 侧 token 或精确成本可补，更新本 ADR。
