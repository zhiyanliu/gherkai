# 核心↔worker 协议：流式 JSON 契约 + 成本信封（engine 只报原生量、core 只合计）

> **Status:** Accepted

定义核心库（`core/`）与引擎 worker 子进程之间的**唯一契约**：core 喂什么、worker 回什么。这是 v1.0 的「窄腰中的窄腰」——`parse`/`schedule`/两个引擎 worker/RunReport 全依赖它，设计错则全线返工。它同时兑现 [0016](./0016-execution-architecture-core-lib-run-model.md) 一直 defer 的「数据模型字段级 schema」（协议字段 = RunResult/RunReport 的字段来源）。执行形态（两个引擎都子进程、B1 薄 worker）见 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)。

## 设计原则：深模块、小接口

协议接口（调用方必须知道的一切）按「跨引擎概念 vs 引擎特定细节」分两层，保持**小而深**：
- **一等字段** = core 要理解/分支的跨引擎概念（status、votes、cost 原生量、errorType、reportRefs）。删了它们域价值就消失（删除测试）。
- **引擎特定细节 / core 不分支的信息** = 收进带标签的子对象（reportRefs 的 `kind` 开放标签等），core 存但不解析、不分支。引擎差异与派发细节不抬进顶层接口。

> 反面（被拒）：把每个引擎的富返回值（Midscene 的 token/dump、Nova 的 metadata）摊平进协议顶层 → 宽接口、浅模块、消费者要按引擎特例化。实查证实两个引擎返回形状高度非对称（见下「实查依据」），更要靠分层把非对称收进子对象。
>
> **删除测试逼出的收窄**（深模块审计 2026-06）：`kind` 字段从顶层删——core 对一个 step 唯一在乎的是「有没有 `votes`」（=是不是 AI 断言，影响抖动汇总）；`navigate/ai_act/deterministic` 之间的区别是 **worker 的派发细节**，core 不消费（对齐 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)「core 对 step 语义无知」）。（cost 信封同样几经收窄——最终砍成「engine 只报原生量、core 只合计」，见下「成本信封」。）

## 输入（core → worker）：一个 scope 的活

一个 scope 输入 = core 的 plan 模块（[0025](./0025-plan-module-feature-to-jobs.md)）产出的一个 **Job**；core 解析 `.feature` 成有序 step 序列发给 worker，**worker 不碰 `.feature` 文件**（单一解析事实源在 core，[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)）。Background/Outline/DataTable/DocString 已在 plan 阶段展开（[0025](./0025-plan-module-feature-to-jobs.md)），worker 只见展开后的有序 step。

```jsonc
{
  "scope":  { "id": "login", "name": "login" },   // name=@scope tag 原值(可含不宜做 key 的字符)；
                                                  // id=core 派生的干净 key。未标 scope → core 生成两者。
  "engine": "midscene",                           // core 已完成 @engine 冲突校验(见 0019)
  "assertionVotes": 1,                             // AI 断言(Then)投票次数(治抖动，见 0014)；默认 1=单次判定
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
- **`assertionVotes`**：AI 断言（`Then`）投票次数（治种类A抖动，[0014](./0014-ai-first-assertions.md)）。worker 对每个 AI 断言跑 N 次取多数票（`yes > N/2`）、回 `votes:{yes,total:N}`。默认 1=单次判定（仍回 `votes` 以标记「这是 AI 断言」——core 靠 votes 存在与否区分 AI 断言 vs 动作/确定性 step）。组合根经 CLI `--assertion-votes` 设、贯穿 plan→Job。
- **step.`argument`（可选）**：承载展开后的 DataTable/DocString（[0025](./0025-plan-module-feature-to-jobs.md)）；有则有、无则缺省。worker 把它**拼成附加文本接在 step 自然语言后**喂 AI（仅 AI 动作/断言路径；确定性 match/URL 导航在裸 `text` 上判，不接 argument）：**dataTable → markdown 表格**（`rows` 用 `|` 拼回、还原 .feature 原貌、LLM 友好）、**docString → `content` 原样**。**两个引擎同一拼法**（Nova `_argument_text`/`_instruction` ↔ Midscene `argument.ts`，各有对称单测），保同一 feature 行为一致。
- worker 拿 `keyword` + `text` 决定派发（见下「worker 派发」），拿 `text`(+`argument`) 喂引擎。

## 输出（worker → core）：流式 JSON Lines

worker **边跑边流式上报**（每行一个事件），core 实时收。选流式而非「跑完整 scope 一次性回整块」（**本 ADR 新决策**——[0016](./0016-execution-architecture-core-lib-run-model.md) 的 `Engine port: runScope(scope) → JSON 结果` 措辞偏向单次返回，此处细化为流式增量）的理由：① 跑批时能看进度；② worker 中途崩溃仍有部分结果；③ 为未来 WebUI 实时进度铺路。代价（实现略复杂）可接受。

**事件三级 started/done 对齐**（接口的一部分，core 假定有序、乱序为 worker 违约）：每级都有配对的起止事件——`scope_started`…`scope_done`（最外，scope_started 首条、scope_done 末条）⊃ `scenario_started`…`scenario_done` ⊃ `step_started`…`step_done`。worker 在每级开始前发 `*_started`、结束后发 `*_done`。**例外：被 scope 内短路跳过的 step 既不发 `step_started` 也不发 `step_done`，只发一条 `step_skipped`**（它根本没起跑，无起止可配对；core 归约时 `duration_ms=None`，见下 `step_skipped` 事件段 + [0031](./0031-job-lifecycle-states-and-severity.md) 决定六）。

**三级执行时长**（性能指标，与成本正交）：core 用**事件到达的墙钟时间戳**（注入的 `clock`，与超时复用同一时钟）算各级时长——`step/scenario/scope` 各 = 其 `*_done` 到达 − `*_started` 到达；`run` 级 = schedule 整体包住（含并发，≠ 各 scope 之和）。落在 `StepResult.duration_ms` / `ScenarioResult.duration_ms` / `JobResult.duration_ms` / `RunResult.duration_ms`。**这是墙钟时长，不是成本**——与 cost 的 `time_worked_s`（Nova 计费量）正交；测的是 core 收到事件的时刻，含微秒级 IPC 传输延迟（worker 发→core 读），对性能诊断够用。worker 只发 `*_started`/`*_done` 信号、不算时长（worker 报事件、core 算指标）。

**传输通道：三通道分离（实现期细化，子进程 worker）**——0024 事件**不走 stdout**，而走一条专用管道，与引擎 SDK 的进度噪声、worker 自身诊断物理隔离：
- **事件通道**（纯 0024 JSON Lines）：core adapter 自建管道，把写端 fd 号经环境变量 `EVENTS_FD` 告知 worker（`pass_fds` 让子进程继承该 fd 但**不重映射 fd 号**，故不硬编码 3；worker 读 `EVENTS_FD` 打开事件输出）。
- **stdout**：留给引擎 SDK 的进度噪声（Nova Act 把 `act(...)`/trajectory 路径打到 stdout）——adapter 当日志透传，不解析。
- **stderr**：worker 自身诊断/错误——独立通道，不被 SDK 噪声淹。
- 调试回落：worker 无 `EVENTS_FD`（手动直跑、无 adapter）时事件回落 stdout，便于 `echo job | worker` 看输出。
- 起因：真跑发现 Nova Act SDK 把进度信息打进 stdout，会污染事件流（被当 JSON 解析失败）——故把事件挪到专用 fd。

```jsonc
// scope_started 带 sessionId（会话一起就报血缘）——超时/SIGTERM 中途打断、scope_done 缺席时 core 仍记得到（ADR 0028）
{"type":"scope_started","scopeId":"login","sessionId":"..."}
{"type":"scenario_started","scenarioId":"..."}
{"type":"step_started","scenarioId":"...","stepIndex":1}
// 动作步：无 votes（core 据此知道它不是 AI 断言，不纳入抖动汇总）；cost 是原生量（Nova 报时长 / Midscene 报 token）
// step_done 可带 step 级 reportRefs（Nova：本 step 的 act 轨迹，一个 step 可能多个 act，kind=trajectory）
{"type":"step_done","scenarioId":"...","stepIndex":1,"status":"passed","cost":{"time_worked_s":9.3},
   "reportRefs":[{"kind":"trajectory","ref":"file:///.../act_1.html","label":"trajectory"}]}
{"type":"step_started","scenarioId":"...","stepIndex":2}
// AI 断言步：有 votes（core 据此纳入抖动汇总）；N 票各一个 trajectory
{"type":"step_done","scenarioId":"...","stepIndex":2,"status":"passed","votes":{"yes":3,"total":3},"cost":{"tokens":1915}}
{"type":"scenario_done","scenarioId":"...","status":"passed"}
// scope_done 可带 scope 级 reportRefs：Midscene 1 个 report html/worker（kind=report）；Nova 一份 session 汇总（kind=summary）
{"type":"scope_done","scopeId":"login","sessionId":"...",
   "reportRefs":[{"kind":"report","ref":"file:///.../midscene_run/report/xxx.html","label":"Midscene report"}]}
```

**`step_skipped` 事件（scope 内短路，[0031](./0031-job-lifecycle-states-and-severity.md) 决定六）**：当 scope 内某 step `error` 后，worker
短路后续 step（不调 AI），为每个被跳过的 step 发一条 `step_skipped`——**独立事件、平行于 step_done，不是 step_done 的第 4 个 status**：

```jsonc
// 上游 step error → worker 不再对后续 step 调 AI（省钱），逐个发 step_skipped（无 status/votes/cost）
{"type":"step_done","scenarioId":"...","stepIndex":0,"status":"error","errorType":"network_error"}
{"type":"step_skipped","scenarioId":"...","stepIndex":1}
```

- **为何独立事件而非 status 第 4 态**：wire 严格三态（status 只 passed/failed/error）。「这步没跑」是执行事实、非判定结论，
  故不塞进 `step_done.status`。core 收到 `step_skipped` → 本地构造 `StepResult(status=SKIPPED, shortcircuited=True)`——
  `Status.SKIPPED` 复用（在 StepResult 层直观表「没跑」），但**由 core 本地赋、不经 wire**（同 skipped/aborted 的 core 派生态性质）。
- **短路判据锁 `status==error`（不看 errorType）**：两腿对称、network_error/engine_error 都触发。**scope 内**行为
  （只短路同 scenario/scope 后续 step，不跨 job——跨 job 是 fail-fast 职责）。承载与不变量详见 [0031](./0031-job-lifecycle-states-and-severity.md) 决定六。

- **`cost` 只挂 `step_done`**；scenario/scope/run 级合计由 **core 累加 step 的原生量得出**（token / time_worked_s 各自合计），事件不重复携带（避免双重真相源）。详见下「成本信封」。**多票 AI 断言（assertionVotes>1）的 `step_done.cost` 是该 step 全 N 票之和**——worker 按增量/累加算（Midscene 取累计 token 差、Nova 累加每票 time_worked_s），不是只算最后一票（否则欠计 (N-1)/N）。
- **`scopeId`**（= 输入 `scope.id`，RunStore/RunReport 关联键）随 `scope_done` 回；`sessionId` 是语义不同的 AgentCore 会话血缘——**随 `scope_started` 首先回传（会话一起就报），`scope_done` 仍带作冗余兜底**。提前到 `scope_started` 是因为超时/SIGTERM 中途打断时 `scope_done` 从不 emit，会话却已起——血缘必须先随首事件落到 core（[0028](./0028-transient-network-ssl-resilience.md)）。core 的 `_reduce` 在 `scope_started`/`scope_done` 两处都取（仅在非 None 时设，后者不覆盖前者已捕获的值）。
- step 不再带 `kind` 字段：core 靠 `votes` 的**存在与否**区分「AI 断言（纳入抖动汇总）vs 其余」即足够；worker 内部如何派发（导航/动作/确定性）是其实现细节，不进协议（见上「删除测试逼出的两处收窄」②）。

### 字段语义

**标识字段**（回指输入的关联键）：
- **`scenarioId` / `stepIndex`**：回指输入的 `scenario.id` / `step.index`，把事件挂回具体 scenario/step。
- **`scopeId`**：回指输入 `scope.id`（RunStore/RunReport 关联键）。
- **`sessionId`**：AgentCore 会话 id（血缘，进 RunStore 控制面，[0016](./0016-execution-architecture-core-lib-run-model.md)）；与 `scopeId` 语义不同。

**一等字段**（core 要理解/分支）：
- **`status` 三态**：`passed` / `failed`（断言投票没过 = 测试发现了问题）/ `error`（引擎抛异常 = 没能跑完测试）。`failed` 与 `error` 语义不同，worker 负责区分——前者是测试结论，后者是执行故障。**wire 只传这三态**——`skipped`/`aborted`（fail-fast 派生终态）与 `pending`/`running`（实时写前置态）是 **core 内态、不进 wire**（worker 没起或已被掐时由 schedule 本地赋，见 [0031](./0031-job-lifecycle-states-and-severity.md)）。**scope 内短路的 step 也不经 status 上报**——走独立 `step_skipped` 事件（见上「输出」段 + [0031](./0031-job-lifecycle-states-and-severity.md) 决定六），core 据此本地赋 `StepResult(status=SKIPPED, shortcircuited=True)`。
- **`votes`**：step 是 AI 断言时才有，记 tally `{yes, total}`——够算抖动率（[0014](./0014-ai-first-assertions.md) 投票治种类A抖动）。**`votes` 的存在与否即 core 区分「AI 断言 vs 其余」的唯一依据**（取代了原 `kind` 字段）。
  - **为何只记 tally、不记 per-vote 序列**（澄清，免再纠结）：每票的 **yes/no 是拿得到的**（worker 投票循环里就是逐票布尔，见两个引擎 worker），只是折成 `{yes,total}` 计数。不留逐票序列是因为**投票是无序重复采样**——`[T,F,T]` 相对 `{yes:2,total:3}` 仅多了"顺序"，而顺序无语义，tally 已是全部信息。**真正拿不到的是每票的 thought/reason**（`aiBoolean`/`act_get(BOOL)` 只回布尔、不回"为何这么判"，两个引擎 SDK 皆然）——这才是「留口子不实现」里的「per-vote 细节」所指。
- **`errorType` + `message`**（规范化失败分类）：`errorType` 取自固定类别集，让 RunResult/未来重试能按类型分支；`message` 是人类可读诊断。**`failed` 与 `error` 两态均可带 `errorType`**（`failed`→`assertion_failed`；`error`→其余执行故障类）。**两个引擎映射**：Nova Act 有丰富异常树（按类映射），Midscene 只抛通用 `Error`（归 `engine_error`）。初始类别集：`assertion_failed`（断言没过）/ `timeout` / `guardrail` / `engine_error`（引擎内部/通用异常）/ `navigation_error` / `network_error`（网络/SSL 建连层瞬时故障,可重试,[0028](./0028-transient-network-ssl-resilience.md)）。类别集可随真实失败样本扩充。**退出码约定（[0028](./0028-transient-network-ssl-resilience.md)）**：建连失败发生在任何事件 emit 之前,worker 无法走事件通道,故约定专用退出码 `EX_WORKER_NETWORK=80` 作 out-of-band 信号；adapter 把它翻成 `WorkerNetworkError` → schedule 记 `network_error`。

**core 不分支的附加信息**（存进 RunReport，不进 core 逻辑分支）：
- **`reportRefs`**：可挂 `step_done`/`scenario_done`/`scope_done` 三级事件；每项 `{kind, ref, label?}`。**`kind` 表「产物类型」**（开放字符串：`report` 完整报告页 / `trajectory` 轨迹页 / `summary` 数字汇总 / 未来 `video`/`trace`/`har`…），**「粒度」由挂在哪级事件表达、不由 kind 表达**（step 级挂 step_done、scope 级挂 scope_done）。`ref` 统一 URI、本地 `file://`，`label` 可选锚文本。两个引擎产物形态不同（[0010](./0010-spike-as-apples-to-apples-benchmark.md)）：Midscene 1 个 report html/worker（`kind=report`、`scope_done` 带）；Nova 每 act 一个 trajectory（`kind=trajectory`、下沉到 **`step_done`** 带，本 step 的 act 都挂该 step，一个 step 可多个）+ 一份 session 汇总（`kind=summary`、`scope_done` 带，是引擎特有富信息如 act_count 的载体、非人看报告）。core **永不读 `kind` 值、不解释 `ref`**——不透明搬运、原样归进 RunReport（[0027](./0027-runreport-aggregation-index.md)）。`ReportRef` 形态详见 [0027](./0027-runreport-aggregation-index.md)。

**worker 派发（不进协议，仅说明 worker 内部如何把 step 变成引擎调用）**：worker 收到 `(keyword, text)` 后按优先级派发——① 命中 test engineer 的确定性注册表（[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)）→ 精确判定、无 votes；② 否则若 step 文本含 URL 字面量（引号内 `https?://…`）→ 内建确定性导航（code 抽 URL 直接 goto/go_to_url，不浪费 AI、不跑偏），动词随意（"打开/访问/前往…"皆可，对齐 [0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md) 纯自然语言）；③ 否则 `When` → AI 动作（aiAct/act，无 votes）、`Then` → AI 断言（aiBoolean/act_get + 投票，带 votes）。这些区别 core 不消费，故不出现在协议字段中。

## 成本信封（cost）：engine 只报原生量，core 只合计，不算美元

**原则：core 不算、不折美元、不判可信度——engine 提供什么原生量就报什么，core 各自合计。** 实查（见下「实查依据」）证实两个引擎计费轴根本不同：**Nova Act 按 agent 工作时长**（SDK 原生给 `time_worked_s`）；**Midscene 按 LLM token**（Bedrock 原生给 token 用量）。两个引擎的**原生信号本就不同**，统一成美元需要一个费率——而费率（尤其 Midscene 的 Qwen token 单价）随 region/协商/版本变、billed 到用户账户，框架不该追那张会过期的单价表。**故 core 只如实搬运 + 合计原生量，美元折算交给消费者（用自己 AWS 账户的真实费率）。**

`cost` 是**平铺、各 optional 的原生量**（无 `cost_usd`/`precision`/`basis`/`costRate`——这些都已删）：

```jsonc
// Nova Act step 的 cost（SDK 原生给 time_worked_s）：
"cost": { "time_worked_s": 9.3 }

// Midscene step 的 cost（Bedrock 原生给 token）：
"cost": { "tokens": 1915 }
```

- **`cost` 的字段全 optional**：`tokens`（LLM token 用量）/ `time_worked_s`（agent 工作时长秒）。engine 报哪个就有哪个——**哪个量有值，本身就说明该 engine 按什么计费**，不需要额外的 `basis` 判别器或 `precision` 可信度标签。
- **core 只各自合计、不交叉、不折算**：`StepDone.cost.tokens` → `JobResult.total_tokens` → `RunResult.total_tokens`；`time_worked_s` 同理 → `total_time_worked_s`。语义「无引擎报这个量则 None、不假装 0」。混引擎跑批时两个原生量**各自合计、互不污染、都不丢**。
- **连 Nova 也不自折美元**：Nova 的 `$4.75/agent-hour` 虽是公开统一费率可硬编码，但为「两个引擎对称、不维护会过期的费率」起见仍只报 `time_worked_s`——core 退回纯搬运的薄管道，美元折算权完全归消费者（用自己账户费率）。
- **扩展**：未来新引擎若有新计费轴（如「按请求数」），`cost` 加一个 optional 原生量字段、`RunResult` 加一个对应合计即可，顶层不破坏。

## 实查依据（2026-06，读已装源码 + 线上核实，经对抗核验）

- **Midscene**：`aiAct()→string|undefined`、`aiBoolean()→bare boolean`，**失败抛异常**（status 由 worker 捕获算出）；token 在 `agent._unstableLogContent().executions[].tasks[].usage.total_tokens`；报告路径 `agent.reportFile`（destroy 后），1 个 html/worker。
- **Nova Act**：`act()→ActResult`、`act_get()→ActGetResult(matches_schema/parsed_response)`，**失败抛异常树**（guardrail/timeout/agentFailed/限流…）；**token/cost 任何 SDK 路径都拿不到**（`ActResult`/`ActMetadata`/trajectory/wire 全无 token 字段；`InvokeActStepResponse` 只有 `calls`+`step_id`；pydantic 默认 ignore，即便服务端回 usage 也被静默丢弃）。
- **Nova 原生量 `time_worked_s`**：SDK 原生给（= 工作时长扣除等人时间，自标 "Approx. Time Worked"）。它与 Nova 计费口径一致（Nova 按 **$4.75/agent-hour**、扣除等人时间，`aws.amazon.com/nova/pricing` 逐字核实）——故消费者可用 `time_worked_s/3600 × 费率` 高保真折美元。**但折算由消费者做、不由 worker/core 做**（框架只报原生量，不内置 $4.75）。
- **两个 UNKNOWN（记为 SDK 外、v1.0 不依赖，非可用路径）**：① 线上 invoke-step 响应是否藏了被 SDK 丢弃的 usage——需真实抓包才能定；② CloudWatch/Cost Explorer 是否暴露可读的 per-act 成本指标——需 AWS Nova Act 用户指南（JS SPA，未能 fetch）。两者 v1.0 都不依赖；若未来追求精确 token 成本再探。

## 协议是测试面（skill：interface is the test surface）

core 的 `schedule`/汇总逻辑应能用一个**假 worker**（in-memory adapter，吐预设的 JSON Lines）测试，无需真起子进程、真连 AgentCore。这要求协议是纯数据（输入纯数据 in、事件流 out），不夹带句柄/回调——本 ADR 的 schema 满足。`Engine` port 的两个真 adapter（spawn node / spawn python worker）与这个假 adapter 形状一致（[0016](./0016-execution-architecture-core-lib-run-model.md)）。

## 终止契约（core 请求 worker 优雅停止）

协议是**单向数据流**（core 一次性喂 job → worker 流式吐事件）+ **进程级生命周期**。core 对运行中 worker 唯一需要下达的指令是「停」（超时兜底 / fail-fast 中止，见 [0026](./0026-schedule-module.md)），故不引入双向控制通道，而是把「停」做成显式契约——**分三层、各管一段，「怎么停」的机制不在协议顶层**：

- **逻辑层（协议顶层）：schedule 经 worker 句柄请求「停」**（`handle.stop(gracePeriod)`；`handle` 由 `engine.run_scope(job)` 返回、schedule 持有，见 [0026](./0026-schedule-module.md)）。schedule 只表达逻辑意图，**不懂信号/进程**。（`Engine` port 只有 `run_scope`，**不挂 stop**——句柄自己知道怎么停，无需把 handle 反传回 engine。）
- **机制层（Engine adapter / WorkerHandle）：把「停」翻成具体机制**——**子进程 adapter**：`SIGTERM` → 等 `gracePeriod`（默认 5s）→ 未退 `SIGKILL` 兜底；**未来 Fargate adapter**：`StopTask`。信号/进程是 adapter 的「进程世界」知识（[0016](./0016-execution-architecture-core-lib-run-model.md) ports&adapters），不渗进 schedule/协议顶层。
- **worker 层：worker 捕获 `SIGTERM`/`SIGINT` 做会话清理**（防泄漏继续烧钱）。两腿机制不同但**都满足同一契约：收到信号后释放会话、干净退出、不 hang、不泄漏**。**关键不对称（源于运行时模型，非疏漏）**：Nova 是 Python + playwright 同步 API（greenlet），signal handler `raise` 会把异步异常注入主线程任意字节码点、可能撞 greenlet 切换关键区致死循环卡死（Journey 0001 发现 #2）——**故 Nova 必须改 flag-only**（下述）。Midscene 是 Node 单线程事件循环、无 greenlet，`process.on(signal)` handler 作为回调排进事件循环、**不注入/不打断运行中代码**（结构上不可能出现 Nova 那种 hang，Midscene 中断实测 `hung=false` 印证，见 [Journey 0001](../journey/0001-wps-interruption-loss-spike.md) 的「引擎 × 中断时机」数据表）——**故 Midscene 维持现状**（handler 已满足契约：释放会话、不 hang、不泄漏），不改为 flag-only（改 flag-only 只为"对称"、非修 bug，按代码纪律不动无 bug 的工作代码）。
  - **Nova worker**：SIGTERM/SIGINT 共用 handler，**只 `set` 一个模块级 `threading.Event`**；主流程在 **act 边界安全点**（scope/scenario/step 循环顶、投票循环、建连重试循环、退避 `_stop.wait` 唤醒处）检测标志 → 正常 `return`/`break` **退出三层 `with`（NovaAct / `cdp_session` / Workflow）** → `cdp_session` 内 `with browser_session` 的 `__exit__`（`@contextmanager` 的 finally，**正常退出与异常退出同样触发**）释放会话。**单 act 有界返回靠 SDK 的 per-act `timeout`**（见下「act 有界返回」），使标志位在有限时间内必被检测到。`nova.stop()`/`close()` 只关 Playwright 连接、关不掉 AgentCore 会话（会继续烧钱），故释放必须走 `cdp_session.__exit__`。
    - **被拒方案（护栏，防重进坑）**：曾用「handler `raise _Terminated(BaseException)` 穿透 step 级 `except Exception` → 三层 `with __exit__`」（`_NetworkExhausted` 同）。**废弃**：CPython 信号在主线程任意字节码边界"凭空"抛异常，落进 Nova SDK 的 playwright greenlet 切换关键区时撕裂 greenlet 状态机 → 概率性无限循环卡死、100% CPU、`__exit__` 跑不到、会话泄漏（Journey 0001 发现 #2，实测复现）。这是 sync-over-greenlet + signal-raise 的**结构性反模式，无法靠改 raise 时机/异常类型修复**——只能改协作式标志位。
    - **被拒方案（护栏，防重复调研）：asyncio 化以「消除」greenlet**。技术上**可行且更根治**（已核实、非猜测）：Nova SDK 有官方完整异步实现 `nova_act.asyncio.NovaAct`（`async with` + `await act/act_get`，内部 `async_playwright`、无 greenlet），切过去 `sync_playwright` 从执行路径彻底消失、发现 #2 的故障对象不复存在；signal 走 `loop.add_signal_handler`（事件循环调度、不在任意字节码点注入异常）+ `task.cancel()`（await 点协作式取消）。**仍拒**，四条硬事实：① 约 **5 倍工作量**——`_run_step/_run_scenario/_run_session/main` 四层全染 `async`、确定性 handler 契约**反转**（现禁 async → 须支持 await）、~15 测试 + fake 转 async、新增 pytest-asyncio 依赖；② **建连侧根不掉**——`nova_act.asyncio.browser_auth` 是空文件，`AgentCoreBrowserSessionProvider.cdp_session` 只有同步版、底层 `bedrock_agentcore.browser_session` 亦同步 only，建连/释放段无论如何阻塞事件循环，asyncio 一分好处拿不到；③ **仍需叠 flag-only**——`await nova.act()` 依旧不可中途打断，SIGTERM 来了还是「置标志 + await 边界检查 + per-act timeout」这套，flag-only 是 async 之上的额外工作、非替代品；④ **无正确性/即时性增益**——`task.cancel()` mid-act 撞上「act 不幂等」同一语义墙（见下「act 有界返回」），与 flag-only 的中断边界**等价**，async 的收益仅剩「更优雅」这类非功能项。故 flag-only 是**知道有 async 可选、看清代价后的主动权衡**，非「SDK 不支持 async 的无奈」。**重议触发条件**：当「优雅停 / 中断抢传即时性」升级为硬需求，或「两腿执行模型对称（Nova 与 Midscene 同为 async）」成为显式目标时，再重启 async 评估。
  - **Midscene worker（现状，不改为 flag-only）**：SIGTERM/SIGINT handler（共用一个，Ctrl-C 亦纳入）走**有序显式 cleanup**——**先 `StopBrowserSession` 释放会话**（最重要、优先，各套超时预算并行 Stop）、再 `browser.close()` 套超时；`StopBrowserSession` 失败不静默吞 → 置 `cleanupFailed` → worker **非 0 退出**（泄漏可观测）；**cleanup 之后**追加一次 best-effort 中断兜底抢传（读 `agent.reportFile` 调 `snapshot` 上传那份增量 report，救「首个/当前 act 中途、无 prior step_done」这格——见 [0029](./0029-engine-artifacts-to-s3.md)「act 边界抢传」），失败吞、不影响退出码；再 `process.exit`。Node 无 greenlet，handler 作为事件循环回调运行、不撞 Nova 那种 greenlet 卡死，**能在 handler 里安全 `await` 一次上传**（Nova 因 greenlet 做不到、只能主流程安全点抢传——关键不对称）——现状已满足契约（释放会话、不 hang、不泄漏），无需改 flag-only。
  - 两腿都遵循「会话释放优先、失败可观测」。**SIGKILL 兜底（grace 超时）时会话清理落空 → 泄漏**；Nova 改 flag-only 软停后，此泄漏窗口比旧的即时 raise 打断**放大**（须等 in-flight act 到安全点才释放，见下「已接受代价」）。
- **会话清理归 worker，schedule/adapter 不碰 AgentCore**：schedule 只下逻辑「停」、adapter 只发信号杀进程——**`StopBrowserSession` 只由 worker 调**（Nova 经 `cdp_session.__exit__` 间接、Midscene 显式调）。worker 干净退出时会话由它自己释放，core 全程不碰 AgentCore。
- **act 有界返回（Nova 软停的前提机制）**：flag-only 只在 act 边界安全点被检测，故单 act 必须有时间上界、否则长 act 卡住时标志永不被检测。Nova SDK 的 `act()`/`act_get()` 有 per-call `timeout`（int，[2,1800]s），到点在 dispatch 循环 **step 边界安全点**同线程抛 `ActTimeoutError`（非 greenlet 切换区、可 catch，worker 已分类为 `timeout`）。worker 给每个 act 设 `timeout=ACT_TIMEOUT_S`（具体值真跑标定），使 in-flight act 在 `~timeout + 单 step 最坏耗时`内必返回。**这是软停语义，非即时打断**：SIGTERM 后中断延迟上界 = 当前 act 剩余 timeout 预算 + 单 step 最坏耗时。**不选「子进程隔离 act 求即时打断」**——act 不幂等，即时弃用飞行中的 act 与等它跑完在语义上同样无法回滚，即时性换不来语义收益，且实现复杂（playwright greenlet 句柄难跨进程）。
- **grace 硬约束（连带，已在代码 enforce）**：`grace ≥ ACT_TIMEOUT_S + 单 step 最坏 + 会话释放耗时 + 余量`。若 grace < act_timeout，SIGTERM 落长 act 中途时 SIGKILL 必先到 → `__exit__` 不跑 → 会话泄漏、软停白做。**这条不再靠人工设值，而是有护栏强制**（分层不破 core 引擎无关纯度，[0016](./0016-execution-architecture-core-lib-run-model.md)/[0026](./0026-schedule-module.md)）：
  - **core 只校验引擎无关的「关系」**：`ScheduleOpts` 加 `min_grace_s`（调用方声明的下限，纯数、无引擎语义）；schedule 起 worker 前 enforce `grace_period_s > 0 且 ≥ min_grace_s`，否则 `raise ValueError`。core **不认「120 从何而来」、不认引擎名**——只知「传入 grace 必须 ≥ 调用方声明的下限」。任何前端（cli/未来 WebUI）都受此同一护栏（兑现「入口不许配危险值」）。
  - **组合根持引擎特定的「值」**：`compose` 拥有**单一 `NOVA_ACT_TIMEOUT_S` 常量**（默认 120，env 可覆盖），同时派生两端——① 注入 worker 的 `NOVA_ACT_TIMEOUT_S` env、② 算 Nova 的 grace 下限 `ACT_TIMEOUT_S + margin`（消除「worker 默认 120」与「grace 下限」两处独立 120 的漂移）。`--grace` 默认改**哨兵**（不给 → 按本 run 引擎推导下限、Nova run 自然 ≥ act_timeout+margin、midscene-only run 回到小值；显式给过小 → core enforce 拒绝、cli 友好退 2）。混引擎 run 取各引擎下限的 **max**（grace 是 run 级单值）。
  - **旧默认值漂移已消除**：此前 cli `--grace`=10 / `ScheduleOpts`=5 远小于 ACT_TIMEOUT_S=120、每个 Nova run 恒在违约区靠 session TTL 兜底——改哨兵默认后默认值也从同一下限派生。
  - `margin`（单 step 最坏 + 会话释放 + 余量）是**有界的待真跑标定量**（保守起点见 [0028](./0028-transient-network-ssl-resilience.md)），做成组合根具名常量、标定完改一处。
  - **未来更干净**：引擎经 `Engine` port 自声明 `min_grace_s`、组合根查询后聚合，替代 compose 里 `engine_name=="novaact"` 分支——动 port、影响两腿 adapter，defer（现阶段先用 compose 内映射）。
- **已接受代价 + 泄漏兜底（AgentCore 原生 session TTL，非 core reaper）**：flag-only 软停放大了 SIGKILL 前的会话泄漏窗口（等 act 到安全点才释放）。此泄漏只在**低频双重失守**（SIGKILL 硬杀 ∧ grace < act_timeout）时发生，且**有原生上界**：AgentCore `start_browser_session` 的 `sessionTimeoutSeconds`（范围 1–28800s、默认 3600s=1h）到点由服务端自动回收会话——泄漏最多烧到 TTL 到期。**故不引入 core 侧 reaper**：一个低频、有服务端 TTL 封顶的残余，不值得为它让 core/adapter 新增一个碰 AgentCore 的回收组件（破 [0016](./0016-execution-architecture-core-lib-run-model.md) 窄腰、扩大会话心智负担）。**零污染做法**：worker 起会话时把 `sessionTimeoutSeconds` 设为合理值（略大于 `ACT_TIMEOUT_S + grace` 量级）收紧泄漏上界，core 一行不改、不碰 AWS（**前提：Nova SDK 的 `AgentCoreBrowserSessionProvider` 是否允许透传该参数待实现时验；不允许则退回默认 1h，仍是有界兜底**）。**重议闸门**：若真跑观测到"TTL 兜底不够（泄漏成本痛）"，再议主动 reaper——届时须论证它不破窄腰（落 adapter 边缘/组合根收尾钩子、不进 core 纯库与 schedule reducer），并依赖会话血缘回传（[0028](./0028-transient-network-ssl-resilience.md)）。
- **SIGINT（Ctrl-C）一并纳入**：worker 原只装 SIGTERM handler，Ctrl-C 走默认 → mid-act 抛 `KeyboardInterrupt`（同类 BaseException 异步 raise、同样撞 greenlet）。改造后 SIGTERM/SIGINT 共用 flag-only handler，Ctrl-C 变协作式停。
- **发现 #1（建连早期误报 engine_error，Journey 0001 发现 #1）顺带根治**：`Workflow()` 构造期（`main()` 早期、旧 `try/except _Terminated` 之外）到达的 SIGTERM，旧 handler raise 无人 catch → 裸 traceback → exit 1 → adapter 归 `engine_error`（误报；此刻会话未起、无泄漏）。flag-only handler **绝不 raise** → 构造期 SIGTERM 只置标志，构造完成后建连前第一个安全点 `return 0` 干净退出，不再误报。
- **未来演进（控制流，记路标不实现）**：若 core 需要对运行中 worker 下达「停」之外的指令（暂停 / 取消单个 scenario / 动态调度 / WebUI 交互），届时引入**显式 core→worker 控制通道**（双向消息流），另立 ADR。当前唯一控制指令是「停」，为一条指令建通用双向协议属过度工程（删除测试）。

## 远程传输演进（Fargate：port 抽象活、pipe 传输死；记路标不实现）

> 前瞻 draft 性质的一节：Fargate 执行 adapter 尚未编码。这里钉的是**已想清、不会变**的边界（哪些 survive、哪些必改），供真做时照做；具体传输选型（HTTP/队列/CloudWatch）留到那时定，不在此焊死。产物→S3 是**正交的另一条边**，见 [0029](./0029-engine-artifacts-to-s3.md)。

当前传输是**OS 管道**：core 是 worker 父进程，job 写 worker stdin、事件读 worker 的 `EVENTS_FD` fd、退出码经 `proc.wait()`。搬到 Fargate（[0017](./0017-cloud-execution-fargate-over-runtime.md)），core 不再是 worker 父进程，**管道语义（父子进程 / fd 继承 / EOF / stdin）全无对等物**。核实（AWS 文档 + 本仓 code，2026-07）的结论分两层：

**① `Engine` port 抽象 survive。** port 是 `run_scope(job) → (WorkerHandle, Iterator[Event])` + JSON-Lines 线格式这个**抽象契约**，本就与传输解耦——「协议是测试面」的 in-memory 假 worker（见上节）即证明 core/schedule/wire/model 不关心"事件行从哪来"。Fargate 化**不改** core/schedule/wire/model、不改 port 签名、不改线格式。

**② pipe 传输实现 die，worker 的 I/O 边缘必改（引擎逻辑不动）。** 三路各自要换（`FargateEngine` adapter 侧换传输、worker 侧换 I/O 边缘）：

| 通道 | 当前（管道） | Fargate | worker 要改的 I/O 边缘 |
|---|---|---|---|
| **job 入口** | 写 stdin → 关 stdin | RunTask **无 stdin**；overrides 有 8192 字符硬上限，含 feature 的 job 塞不下 → core 先 `PutObject` 整 job 到 S3、RunTask 经 env 只传小指针（`JOB_S3_URI`） | `sys.stdin.readline()`/`process.stdin` → 读 env 指针 + `GetObject` 拉 job |
| **事件出口** | worker 写 `EVENTS_FD` fd，core 读端逐行 `event_from_line` | 无 fd 继承。**【关键坑】事件走专用 fd、不在 stdout（三通道分离，见上），故 awslogs/CloudWatch 抓不到事件**——不能"tail stdout 重建"（要么抓不到、要么把事件挪回 stdout 重新引入被三通道分离修掉的 SDK 噪声污染）。改成 worker `SendMessage` 到 SQS（见下「SQS 作 events-out 传输」） | `emit()` 的 sink 从"写 fd"改成"`SendMessage` 到注入的 SQS 队列" |
| **停 / 退出码** | `handle.stop`=SIGTERM→grace→SIGKILL；管道 EOF + `proc.wait()` 同步读退出码 80 | `StopTask`（grace 变成 task-def 期常量 `stopTimeout`、Fargate 上限 120s、**不能逐次传**）；退出码经 `DescribeTasks` 读 `containers[].exitCode`（须等 `lastStatus==STOPPED`，STOPPED 前常 null） | **worker 不改**——照样 `exit 80`；只是 adapter 读取从 `proc.wait()` 换成 `DescribeTasks` |

**架构结论（贯穿产物半 [0029](./0029-engine-artifacts-to-s3.md) 与传输半）**：**worker 的引擎逻辑（派发/投票/短路/产物生成）不按执行环境分；worker 的 I/O 边缘（job 入口、事件 sink、产物落点）本质是传输/落点，应抽象成可注入接口**——subprocess 注入"读 stdin / 写 fd / 报 `file://`"，fargate 注入"读 S3 / `SendMessage` 到 SQS / 报 `s3://`"。这与 core 侧已有的 `Engine` adapter（subprocess/fargate 两种传输实现）对称。**worker 永远是事件的 producer/client，不是 server**——短命、跑完即退的 worker 不该 listen 等长驻 core 来连；换成队列后**两端都不 listen**（见下）。这条兑现 [0016](./0016-execution-architecture-core-lib-run-model.md)「组合根注入」+「worker 引擎逻辑不按执行环境分」。

### SQS 作 events-out 传输（不自建 relay）

远程场景（Fargate worker 与 core/cli/WebUI 跨机器）需要一个 server 端中转事件。**不自建**——`--backend cloud` 已锁定 = AWS（DDB/S3/Fargate/AgentCore 全在用），自建一个"要部署、要做保序/背压/续传/鉴权"的 http-relay 就是**重新发明消息队列，且多半不如 SQS**。故 events-out 走 **SQS FIFO**。

**SQS FIFO 恰好就是「0024-无关的有序帧传输、只读 envelope、payload 不透明」这个抽象的 managed 实现**——分界设计仍成立，只是 server 端由 SQS 充当：

| 归属 | 内容 |
|---|---|
| **core（通用、单一事实源）** | 0024 事件模型 + 线格式（不变）+ **SQS 编解码**：worker 侧 `encode(event)→SendMessage`、adapter 侧 `ReceiveMessage→decode→yield Event`。纯逻辑、无 server，不破"core 纯库"；adapter(decode) 与 Python worker(encode) 复用，TS worker 按同一 spec 各写（本 ADR「各语言各写」） |
| **SQS（managed，非我方代码）** | 队列本身：持久、保序、可见性超时/重投、DLQ、背压。message body=0024 JSON line（**SQS 从不解析 body**）；`MessageGroupId`/去重 id=envelope（SQS 只用它路由+保序，不看 payload 语义） |

- **保序粒度天生匹配**：本仓顺序要求是"**scope 内保序、scope 间并行**"（[0016](./0016-execution-architecture-core-lib-run-model.md)）。SQS FIFO 保序粒度正是 **per-`MessageGroupId`**——令 **`MessageGroupId = scope_id`**，同 scope 事件严格保序、不同 scope 并行消费。FIFO 的 MessageGroupId 天生就是这个抽象，不必自己实现"按 scope 分组保序"。
- **拓扑：两端都不 listen**。worker `SendMessage`（producer push）、core 侧 adapter `ReceiveMessage` 长轮询（consumer pull）。这消解了自建方案绕不开的"谁 listen"难题（worker 短命不能 listen、cli 本地无公网入口不能 listen）。时间解耦恰配 Fargate run-to-exit：worker 跑完即退，事件留队列等 core 消费。
- **只管 events-out，不管 job-in**：SQS 是队列非 request/response，job（可能含大 feature）不塞 SQS——**job-in 仍走 S3**（见上表 job 入口行）。传输不对称（job-in→S3、events-out→SQS）是两者方向/性质不同的自然结果，非缺陷。
- **控制面不走 SQS**：`stop`=StopTask、退出码=DescribeTasks 都是 ECS 控制面，adapter 直连 AWS（worker 的 SIGTERM 处理不变）。将来若真要承载「停」之外的双向控制指令 → 即上「未来演进（控制流）」记的那条 core→worker 通道路标。
- **环境契约**：容器内 boto3/aws-sdk + SQS 发送权限（ECS task role）；core 侧 SQS 接收权限；队列由 IaC 建。moto 可 mock（与现 DDB/S3 单测策略一致）。

**换传输后受威胁的不变量 / 残留风险**（真做时必须守）：

- **顺序**（本 ADR「core 假定有序、乱序=worker 违约」不变量）：OS 管道天然保序；**SQS FIFO 按 `MessageGroupId=scope_id` 保序**满足"scope 内保序"（scope 间本就该并行）。不用 SQS standard（不保序）。
- **消息大小**：0024 事件极少超 SQS 单消息 256KB（reportRefs 是指针非内容）；真超了用 SQS extended client（body offload 到 S3，本仓已有 S3）。
- **延迟**：管道近实时（微秒级 IPC）；SQS 长轮询通常亚秒级（消息一到即返回、不等满），比 CloudWatch tail 轻，但仍非 IPC 级——会略退化 [0030](./0030-realtime-persistence-seam.md) 实时落库时效。
- **存活判定迁移**（关键）：Fargate 下 **worker 卡死不再靠"事件流沉默"判**（[0026](./0026-schedule-module.md) 心跳机制）——事件经 SQS，队列静默≠worker 死。云端 worker 存活改由 ECS `DescribeTasks` task 状态判。心跳/超时的判据从"事件流"迁到"ECS task 状态"。
- **grace 不对称**：`handle.stop(grace_period_s)` 现在是运行期传参，`--grace` 哨兵默认按本 run 各引擎下限取 max（组合根 `engine_min_grace`：Nova≈`ACT_TIMEOUT_S+margin`=180s、midscene-only≈`MIDSCENE_GRACE_MIN_S`=25s、混引擎取 180s；`ScheduleOpts.grace_period_s` 默认 5s 是无引擎下限时的兜底）；Fargate `stopTimeout` 是 task-def 期常量、≤120s、不能逐次变——叠加容器盘停即销毁的 artifact 丢失（[0032](./0032-fargate-execution-environment.md) 头号待解项）。

## 现在做 / 留口子

- **现在做（v1.0，已落地）**：上述输入/输出 schema、cost 信封（engine 报原生量 time_worked_s/tokens、core 合计）、三态 status/votes 区分 AI 断言；worker 派发逻辑（确定性注册表 > 内建 URL 导航 > 默认 AI，[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)）；两个引擎对称的 `@deterministic` 注册表（命中走精确 handler、不投票）；两个引擎 worker `get_session_id` 取会话血缘、随 `scope_started` 首传、`scope_done` 兜底（机制见上「字段语义·`sessionId`」，[0028](./0028-transient-network-ssl-resilience.md)）；**两个引擎的 reportRefs（kind=产物类型、粒度由挂载层级表达）**——Midscene 取 `agent.reportFile` 报 `kind=report` 于 `scope_done`（scope 级）；Nova 设 `logs_directory` 持久化 trajectory、取 `metadata.trajectory_file_path` 报 `kind=trajectory` **下沉到 `step_done`**（step 级，本 step 的 act 都挂该 step）+ session 汇总报 `kind=summary` 于 `scope_done`，归集成 RunReport（[0027](./0027-runreport-aggregation-index.md)）。
- **`errorType` 分类（已细化）**：建连层瞬时故障 → `network_error`（两个引擎 worker 建连重试 + 退出码约定,[0028](./0028-transient-network-ssl-resilience.md)）；act 中途失败 Nova worker 经 `_classify_act_error` 按 SDK 异常树细分——网络瞬时→`network_error`、`ActTimeoutError`→`timeout`、`ActGuardrailsError`/`ActStateGuardrailError`→`guardrail`、其余→`engine_error` 兜底（**仅诊断分类、不触发重试/恢复**，[0028](./0028-transient-network-ssl-resilience.md)）。`navigation_error` 暂无对应 SDK 类、留空槽位；Midscene 只抛通用 `Error`，act 中途仅区分 network_error vs engine_error。
- **留口子不实现**：per-vote 细节（= 每票的 thought/reason，SDK 拿不到；非 yes/no——见上 `votes` 字段澄清）；trajectory 内部结构的结构化提取；美元折算（交消费者，框架不做）。

## 重议

- 第三个引擎 / 新计费轴的扩展方式见上「成本信封」扩展条。
- 若产品确需框架直接给美元 → 在**消费层**（CLI/报告/WebUI）加费率配置做折算，而非在 worker/core 内置费率（保持 core 纯搬运）。
