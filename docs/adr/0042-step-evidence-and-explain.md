# 0042. step 级机读证据（evidence）与 `gherkai explain`

> **Status:** Draft（施工中；翻 Accepted 的审计点：真跑证据内联到「验证」节、影响面列出的每处反向链已落、全文无过程指代）

## 背景

失败证据目前只给人看。一个 step 判 failed / error 之后，能拿到的东西是：

| 引擎 | 原生产物 | 体量 | 机读内容在哪 | 现有 ref |
|---|---|---|---|---|
| Nova Act | 每个 act 一个 `act_<id>_<prompt>.html`；配套 `_trajectory.json` **只在 act 正常返回时落盘**（SDK 的写盘闸门是「结果非空且有 step」；act 抛错时只有 .html，异常对象的 `metadata.trajectory_file_path` 照给路径但文件不存在；唯一例外是 schema 不匹配——结果已就绪才抛，json 仍写） | json 约 300 KB / act（主体是 base64 截图） | json 的 `steps[*].program.calls[name=think].kwargs.value` 是模型逐步推理原文；`steps[*].active_url`、`steps[*].image` | 只指 `.html`（kind=trajectory）；`.json` 随即时上传一起进了产物目录，但无人引用 |
| Midscene | 每个 scope 一个 report html | 约 2.3 MB | 内嵌若干 `<script type="midscene_web_dump">`，`Insight` 类 task 有 `thought` | 指 html（kind=report） |

另外两件事实：

- **step 级失败原因的文字在 core 里丢了。** worker 的 `step_done` 带 `message`（如「AI 断言未过多数票（0/1）：<断言文>」「ActError: …」），`wire` 解析进 `StepDone.message`，但 `StepResult` 没有 `message` 字段、归约时不搬，`jobs/*.json` 的 step 只剩 `error_type` 与链接。只有 job 级失败（超时 / fail-fast / 起 worker 失败）有 message。
- **两引擎的 AI 断言只拿布尔**（Nova `act_get(BOOL_SCHEMA)`、Midscene `aiBoolean`），「为什么判否」只存在于引擎产物里的模型推理文本。

对人，这套够用：点开 html 看。对驱动本工具的 AI agent（[0041](./0041-agent-facing-cli-affordances.md) 的读者），这是排障链上最大的洞：要么教它两套 SDK 内部格式、读兆级文件自己抠，要么它只能看到「failed」两个字。

## 决策

### 一、evidence：worker 在 step 边界产一份 gherkai 自有 schema 的机读证据，挂 step 级 ReportRef（kind=`evidence`）

**谁产**：worker。引擎知识按 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)/[0027](./0027-runreport-aggregation-index.md) 只住 worker，而 step 结束那一刻 worker 手里有能拿到的全部材料：Nova 是本 step 各**正常返回**的 act 刚写盘的 trajectory json（抛错的 act 无 json，见背景表）；Midscene 是 `agent.dump.executions` 里本 step 新增的 execution（内存活对象，抛错的 task 仍在数组里、带 `errorMessage`）。**不是** CLI 事后去解析 SDK 产物（见被拒方案）。

**产什么**：每个跑过 AI 的 step 一份 `evidence.json` + 若干截图文件，schema 由 gherkai 定义、两引擎同形。「act」在此指**一次 AI 调用**（Nova 的 `act`/`act_get`，Midscene 的一次 `ai*`），是 evidence 这份引擎侧产物的结构词，不是 domain model 的字段——与 0027「`act_count` 不进 model」不冲突。

```jsonc
{
  "schema_version": 1,
  "engine": "novaact" | "midscene",
  "scope_id": "...", "scenario_id": "features/login.feature:12", "step_index": 1,   // step_index = scenario 内 0 起的书写序号
  "step": { "keyword": "Then", "text": "页面显示「登录成功」" },
  "status": "passed" | "failed" | "error",      // 与本 step 的 step_done 一致（冗余是为了文件自包含）
  "message": "AI 断言未过多数票（0/1）：…" | null,
  "acts": [
    {
      "index": 0,
      "prompt": "页面显示「登录成功」",         // gherkai 交给引擎的指令（step 文本 + 多行参数），不含 SDK 追加的输出格式样板
      "vote": true | false | null,               // 本次调用计入判定的那一票；null = 本 act 不是投票调用（When/Given 的动作）
      "url": "https://…" | null,                 // 调用结束时的页面 URL（Nova = 末 frame 的 active_url；Midscene = worker 取 page.url()）
      "frames": [                                // 引擎内部逐步观察-思考-动作；Nova = TrajectoryStep，Midscene = ExecutionTask
        { "url": "https://…" | null,             // 逐 frame URL 仅 Nova 有；Midscene 的 task 不带 URL → null
          "thought": "I am on the login page. … Returning false." | null,
          "actions": [ { "name": "agentClick", "args": { "box": "…" } } ],   // args = 引擎原样透传的对象，内部键随 SDK
          "screenshot": "file:///…/act-0-frame-4.jpg" | "s3://…" | null }   // 只有被截图策略选中的 frame 非 null
      ],
      "result": <引擎原生返回值原样> | null,     // Nova = return call 的 kwargs；Midscene = 末 task 的 output。仅供阅读，判票看 vote
      "error": "ActError: …" | null,
      "time_worked_s": 9.8 | null                // Nova 的计费量；Midscene 恒 null（其 per-task timing 是另一种量、不混用）
    }
  ]
}
```

字段全部**可选容缺**（缺 → `null` / 空数组），schema 只承诺键名与类型，不承诺每个引擎每次都填满。**error act 的契约**：act 抛错 → 该 act 的 `error` 非空、`prompt` 与 `time_worked_s`（异常 metadata 带）仍填；Nova 侧 `frames: []`（SDK 不落 json），Midscene 侧 frames 仍在。这是 SDK 事实、不是抽取失败，`explain` 不报 `evidence_missing`。两引擎在 error step 上**不同形**，消费端别把 Nova 的空 frames 当 bug。

**引擎映射**（SDK 耦合唯一允许存在的地方：各引擎一个纯函数、用真产物裁成的 fixture 钉住；判别一律按**值**，不按 SDK 的布尔标志——Nova 的 `is_tool` / `is_return` 在真产物里对所有 call 都是 False，按它判会静默取空）：

| evidence 字段 | Nova Act | Midscene |
|---|---|---|
| 来源 | 该 act 的 `_trajectory.json`，路径取 `result.metadata.trajectory_file_path`（沿用 worker 现有的收集逻辑；**不用**公开属性 `ActResult.trajectory_file_path`——会话未开 `replayable` 时它返 None 并喷 SDK 警告，`act_get` 的结果重建时更是恒 None）。**按普通 dict 用 `.get` 链读**；SDK 侧写出它的 pydantic 模型在私有 `impl/` 目录，仅作阅读指针、不 import、不 `model_validate`（其字段无默认值，一处漂移就整份 ValidationError，与「逐字段容缺」相悖） | step 末读 `agent.dump.executions`（公开属性），按 step 起点的数组长度切出本 step 新增的 execution。**不用** `addDumpUpdateListener`：同一 execution 每加一个 task 就回调一次，需去重。**不从 `@midscene/core` import 类型**：它不是本包声明依赖（只声明 `@midscene/web`），`evidence.mts` 自写只含所用字段的结构类型 |
| act | 一个 trajectory 文件（一次 act / act_get；N 票断言 = N 个 act） | 一个 execution（一次 `aiAct` / `aiBoolean` / `aiQuery`） |
| act.prompt | worker 自己构造的指令串（同送给 `act` 的那个）；**不取** json 的 `prompt`——`act_get` 时 SDK 在尾部追加了 `, format output with jsonschema: {...}` | worker 自己构造的指令串；`execution.name` 形如「Act - <指令>」「Boolean - <断言>」，是 SDK 展示名、不当真值 |
| act.vote | `bool(r.matches_schema and r.parsed_response)`，与 `step_done` 的票源同一表达式（不要用 `result` 反推：模型回非 JSON 或不过 schema 时 `matches_schema=False` 记 no，而 return call 的 kwargs 里仍留着看似为真的原文） | `aiBoolean` 的返回值 |
| act.url | 末 frame 的 `active_url` | 调用返回后 `page.url()` |
| frame | `steps[i]` | `tasks[i]` |
| frame.url | `steps[i].active_url` | null（`uiContext` 只有 shotSize / dpr / screenshot） |
| frame.thought | `steps[i].program.calls` 中 `name == "think"` 的 `kwargs.value`（多个则换行拼接） | `tasks[i].thought` 非空则取之；否则回落 `tasks[i].output.thought`（真产物：`Insight/Boolean` 的推理在 `thought`，`Planning/Plan` 的推理在 `output.thought`；`Planning/Locate` 带空串、`Action Space/*` 无 → null，按值判非空） |
| frame.actions | `calls` 中 `name` 不为 `think` / `return` 者：`{name, args: kwargs}`（如 `agentType`、`waitForPageToSettle`、`takeObservation`） | `{name: "<type>/<subType>", args: param}`（如 `Planning/Plan`、`Planning/Locate`、`Action Space/Tap`、`Insight/Boolean`） |
| frame.screenshot | `steps[i].image`（data URL base64 jpeg）解成 `act-<i>-frame-<j>.jpg` | **不读 `.base64`**：SDK 在每个 task 更新后即 flush 报告，inline 模式下把 `ScreenshotItem` 的 base64 置空、之后读它会对多 MB 的 report.html 做同步全文扫描且找不到即抛。改为给 agent 传 `persistExecutionDump: true`，SDK 把每张截图落成独立文件 `<MIDSCENE_RUN_DIR>/report/screenshots/<id>.<ext>`；evidence 按 `screenshot.id` + 扩展名拼该路径引用，零解码零复制。取哪张：优先 `tasks[i].recorder` 中 `timing === "after-calling"` 的（动作**后**；只有每轮 plan 的末个 task 有），否则 `tasks[i].uiContext.screenshot`（动作**前**）。同一 `ScreenshotItem` 会跨 task 共享（300 ms 复用缓存、只有 Insight 类 task 强制刷新）→ 多个 frame 可指同一 uri。副作用：`persistExecutionDump` 还会在 report 目录写 `<n>.execution.json`，随 scope 末整目录 flush 一并上传，接受 |
| act.result | `calls` 中 `name == "return"` 者的 `kwargs` | 末个 task 的 `output`（`Insight/Boolean` 的 `output` 即该票的布尔） |
| act.error | act 抛出的异常压成**一行** `类型: 信息`（SDK 异常带 `.message` 取它，否则 str() 首个非空行；折叠空白、封顶 300 字。真跑暴露：`ActTimeoutError` 的 str() 是十几行 repr 加反馈链接，整段进 message 会把 run 文本 / explain / jobs json 的「原因」撑开；同一函数也产 `step_done.message`） | `tasks[*].errorMessage` 首个非空 |
| act.time_worked_s | `metadata.time_worked_s` | null |

**截图策略（有上界）**。单次 AI 调用的帧数由引擎 SDK 的默认步数上限封顶（Nova = 30，worker 不改它），每帧一张截图，再乘 `--assertion-votes`（入口只校验 ≥ 1），不设上界时单个 failed Then 可达数十帧、按 100 到 200 KB/帧即 10 MB 量级。故：**frames 列表保留全部 frame 的 thought / actions / url（文本很小），只有 `screenshot` 受限**——failed / error step 每个 act 最多 K = 3 张（末帧、首个含 thought 的帧、出错帧，去重后取前 K），每 step 总数再封 M = 12；passed step 每 act 只留末帧一张。Midscene 侧按 `ScreenshotItem.id` 去重后计。`--no-report` 档（`GHERKAI_NO_ARTIFACTS=1`，[0037](./0037-distribution-and-packaging.md) 决策 3）不产 evidence，且此档 Midscene 关了 `generateReport`、`persistExecutionDump` 随之不设（SDK 禁止二者组合）。

**落哪、怎么传**。evidence 落在**各引擎自己的产物目录**下：Nova `NOVA_LOGS_DIR/evidence/<scenario 键>/step-<n>/`，Midscene `MIDSCENE_RUN_DIR/evidence/<scenario 键>/step-<n>/`；目录内 `evidence.json`，Nova 的截图 `act-<i>-frame-<j>.jpg`（Midscene 的截图是 SDK 落在 `report/screenshots/` 的文件，只引用）。**`<scenario 键>` 由 `scenario_id`（`<uri>:<行>[:<example 行>]`）派生，不用显示名**：标题不唯一（同文件重名只靠 id 区分、`@scope` 又允许跨文件合并成一个 job），且产物目录按 run 共享、S3 key 按相对 run 目录镜像，同一 run 内所有 scope 共用这一命名空间；派生必须确定性且不二次撞名（分隔符转义 + 尾附 id 短哈希），撞了 key 的表现是 evidence 静默互相覆盖、`explain` 读到另一条 scenario 的 thought 且无从察觉。放在引擎目录内的理由：两引擎上传器的 S3 key 都相对各自 run 目录算，复用 [0029](./0029-engine-artifacts-to-s3.md) 的上传器（key 计算、幂等去重、scope 末整目录递归 flush）而不引入新的注入 env 与上传根。**不是零改动**：① 两引擎的后缀→Content-Type 映射现只有 `.html`，`.jpg` / `.json` 会落成 `binary/octet-stream`、浏览器直开变下载，故各加 `.jpg`/`.jpeg` → `image/jpeg`、`.png` → `image/png`、`.json` → `application/json`（两边同规则同步改）；② 上传器加一个「只算 ref 不上传」的方法（Nova `ref_for(path)`、Midscene `refFor(path)`），见下。

**上传时机分两类**。`evidence.json` 的 ref 必须随 `step_done` 走 → emit 前经 `to_report_ref` 即时上传拿 ref。**截图不即时上传**：URI 用上传器同一 key 规则确定性算出（`ref_for`）写进 evidence.json，字节交给 scope 末的整目录 flush（本就递归传整个引擎产物目录，总字节不变）。理由：即时上传是逐文件串行 PutObject 且套了短超时，把 K × 票数次 PutObject 压在判定临界路径上会把已成的判定拖在网络上（[0029](./0029-engine-artifacts-to-s3.md)「上传套超时、退出时间有界」同向）。代价：cloud 档若 worker 在 scope 中途被杀，截图 URI 可能悬空（evidence.json 已传、图没传）——explain 只列 URI 不取图，agent 取图时按「读不到」处理；本地档 `file://` 无此问题。

**怎么挂**。evidence.json 的 ref 作为 `{kind: "evidence", ref, label: "evidence"}` **追加**进该 step 的 `step_done.reportRefs`（Nova 现有的 trajectory 挂载是整体赋值，两者不能各自赋值互相覆盖；Midscene 的 step 级 reportRefs 此前为空，evidence 是首条，`runStep` 需拿到 uploader 与 page）。截图 URI **只写在 evidence.json 内**，不进 reportRefs。协议不变：`ReportRef.kind` 本就是引擎自报的开放字符串（[0027](./0027-runreport-aggregation-index.md)）。**接受的连带影响**：evidence ref 经既有 `collect_report_index` 自动进 manifest 与 index.html 的产物导航节（每个 AI step 多一行 `[evidence]` 链接、计数上升），以及 `run` 文本输出的 step 行下——这正是人/agent 找到证据的入口；该节措辞从「引擎原生产物」放宽为「报告产物（引擎原生产物 + gherkai evidence）」，富渲染（缩略图 / thought 折叠）仍延后。

### 二、evidence 是 best-effort，对判定零影响——这是对既有规则开的一个具名例外

evidence 的抽取、落盘、上传任一环失败 → worker 日志一行、本 step 不带 evidence ref，`step_done` 的 status / votes / cost / message 照常发。

**这是例外、不是沿用**：[0029](./0029-engine-artifacts-to-s3.md)「reportRef 指向的文件」条规定 step 内判定现场证据（Nova 每 act 的 `.html` trajectory）上传失败即抛、worker 非 0 退出；[0032](./0032-fargate-execution-environment.md)「上传失败处理」只把 **scope 级** report / summary 降为 best-effort，并明文「与 step 内 trajectory 的强保证不同」。本 ADR 把 evidence（json + 截图）这一新的 step 级产物划入 best-effort 侧：trajectory 是报告链接本身、悬空 = 报告坏；evidence 是判定的注释、缺了只损排障便利。trajectory 的强保证不变。

**实现约束（否则「零影响」不成立）**：evidence 的抽取 / 落盘 / `to_report_ref` / 挂 ref 必须整体裹在自己的 try 里，且位于 step 的 act 异常分类路径**之外**——Nova `_run_step` 的外层 `except Exception` 会把 try 体内任何异常经 `_classify_act_error` 转成 `status="error"`，evidence 若裸放进去，一次上传抖动就把已成的 passed 判定翻成 network_error / engine_error。`to_report_ref` 自身的「失败即抛」契约不动，best-effort 由调用方 try + 日志实现，写法对齐两 worker 现有 scope 级 report 的兜法。**承诺边界**：best-effort 只覆盖 evidence 自身失败；S3 整体不可用时同 step 的 trajectory 上传按 0029 原规则仍报错 → 该 step 仍会变 error，本条不承诺那种场景下 step 保持 passed。

代价：evidence.json 在 emit `step_done` 之前落盘并上传一次（小文件）；Nova 侧 passed step 多解一张 base64 图落盘（不上传），failed / error step 最多解 min(M, K × 票数) 张；Midscene 侧零解码（引用 SDK 已落盘文件）。每 step 增加的临界路径耗时为一次小文件 PutObject 加本地 IO。

### 三、`StepResult` 补 `message`，进 `jobs/*.json`

`StepResult.message: str | None`；`project.py` 从 `StepDone.message` 原样搬入；`serialize` **写读两端同批改**——`job_result_to_dict` 的 step dict 写 `message`，`job_result_from_dict` 重建 `StepResult` 时 `.get("message")`、缺键回 `None`（向后兼容本 ADR 之前落盘的 `jobs/*.json`，处置同 [0031](./0031-job-lifecycle-states-and-severity.md) 给 `shortcircuited` 定的）。读端是 `explain` 的唯一入口（两个 ResultStore 的 `load_job_result` / `load_all` 都经它），漏读端则 message 一落盘即丢。`run --json` 走同一份 serialize 自动带上。文本输出（`render.py`）与报告页（`report_store/local.py` 的 step 行，local / S3 共用）在 failed / error step 行下附原因，沿用 job 级 message 的展示方式。零协议改动（`StepDone.message` 早在 [0024](./0024-worker-core-protocol.md) 里）。

护栏盲区两处，手工补：契约页 `run --json` 的 `steps[]` 表加 `message` 行（护栏按裸键名比对、`message` 已在 job 级出现过，step 级漏写不会变红）；round-trip 测试样例须带一个**非默认**的 step message（样例全 None 时 `to_dict(from_dict(to_dict(r))) == to_dict(r)` 照不出漏读端）。

### 四、`gherkai explain <run_id> [<scope_id>]`：把 evidence 与判定树合成一份「哪步、问什么、看见什么、为什么」的文本或 JSON

**输入**。`run_id` 必填；`scope_id` 可选（缺省 = 该 run 全部 job）；`--scenario SEL` 写法与 run / plan 一致（id 全等 / 行号 / 标题子串；可重复、彼此为或；Outline 声明行选中它全部 example）、**可命中多条**；`--step N` 是 scenario 内 **0 起**的书写序号（= JSON 里 step 的 `index`，与 `run` 文本 `step <index>`、`plan` 文本 `[<index>]` 同一口径，explain 不做 +1 展示），按每条命中的 scenario 各取其第 N 步渲染；`--step` 单给退 2（步号没有归属）；命中的 scenario 都没有第 N 步 → 退 2 并列出候选 id 与步数。`--all` 也展开 passed step（默认列出全部 step、只对 failed / error / skipped / 无记录的 step 展开）；`--full` 关闭文本预算（见下）；`--json`。定位 flag 与 `status` 的全集同形：`--report-dir`（local = run 落点；cloud = 报告 / 判定明细前缀，须与 submit 一致）+ cloud 档 `--backend cloud --prefix --ddb-table --region --profile`；桶名同 `status` 不设 flag、由 prefix / env 推导。不提供 `--tags`（tags 在 scope 分组后即不进 job 定义）。

**`--scenario` 的匹配器另起、不复用 run/plan 的**：那个谓词按 `ParsedScenario.uri` 切尾、按 `tags` 判（0041 决策一），explain 只读 RunStore / ResultStore、不重解 `.feature`，两者都拿不到。匹配对象 = job 定义里的 `Scenario.id` / `Scenario.name`：id 档全等；标题档对 `name` 子串；行号档从 `scenario_id` 尾部取连续数字段比对（有损：uri 自身以数字冒号段结尾时可能误命中，接受此边角）。

**数据来源**。`--backend cloud` 时**先于任何云端读**过版本 skew 闸门（`compose.check_backend_skew`，与 `status` 同形：block 退 2、戳缺失或 CLI 偏旧只提示）。然后经现有 RunStore / ResultStore 读 run 元信息与每个 `JobResult`（含 job 定义 → scenario 名、step 关键字与文本；装配走 `compose.build_local_stores` / `build_cloud_stores`）；对每个 step 取 `report_refs` 中 `kind == "evidence"` 的 ref，经 `compose.read_resource(uri)` 读取（`file://` 复用 report_store 既有的 URI→路径解析、不写第三份；`s3://` 走 boto `get_object`，client 经 `build_cloud_stores` 已有的钩子拿、boto 仍只惰性 import、`file://` 档零 boto 依赖）。**云端权限面与 `status` 不同**：同样要 SSM 版本戳读 + runs 表 GetItem，另需该桶 `s3:GetObject`（判定明细与 evidence 对象），不带 `scope_id` 时还需 `s3:ListBucket`；不需要 `status --wait` 的 `lambda:InvokeFunction`。缺哪样退 2、诊断点名。

**记录缺口的两种情形，分开表达**：

- **JobResult 只含收到 `scenario_done` 的 scenario**——worker 被外部中止（超时 / fail-fast / 信号）时未完成的 scenario 不算判定、其 step 记录不进 `jobs/*.json`。explain 以 job 定义为骨架逐 scenario / 逐 step 渲染，无记录的 step 文本打「无记录（未执行或未上报）」、JSON 给 `status: null` + `record_missing: true`；无任何 step 记录的 job 单独渲染一段 job 判定块（status / error_type / message + job 级 report_refs + 「诊断细节见 worker 日志」）。被中止 job 里已跑完的 step 其 evidence 已产且已上传，但 ref 只在事件记录里；**本 ADR 不让 explain 读事件流**（compose 现只暴露三个 store，加事件接缝是另一件事），输出里提示「本 job 被中止，部分已执行 step 的证据未进判定记录」。
- **step 有记录但无 evidence** → `evidence: null` + `evidence_missing: "no_ref" | "unreadable" | "unsupported_schema"`。`no_ref` 覆盖「确定性 / URL 导航 step 本就不产」与「AI 跑了但抽取失败」两种，结果树分不出来；文本打「无 AI 证据」。

**未终态 run 分两档**：同步 `run` 中途可见已完成 job（逐 job 落 ResultStore），文本形态经 stderr 提示「run 仍在跑，以下为已完成部分」（stdout 只放核心产出，与 `status` 的提示同律）；`submit` 的 detached run（本地 per-run 进程与云端 reconciler 同一份 tick）在全 job 终态 finalize 时才一次性落 ResultStore，未终态时零文件——explain 退 0、只打一行「判定明细尚未落地，可先用 `status --wait` 等到终态」。让 detached run 中途可见需从事件流逐 scope 归约，属另一个决策。`--json` 下不打任何提示行（0041 决策三：stdout 只有一个 JSON 文档），机读侧靠顶层 `status` 自明。

**文本形态**（skipped 只由上游 `status == error` 短路产生，判据是 `StepResult.shortcircuited`、不按 status 顺序猜，作用域是同一 scenario；断言 `failed` **不**短路后续 step，见 [0031](./0031-job-lifecycle-states-and-severity.md) 决定六与 [0028](./0028-transient-network-ssl-resilience.md)）：

```
run 20260910T080630Z-9fa261  status=failed
scope features/login.feature:6  engine=novaact  status=failed  session=01a0…
  scenario features/login.feature:12  密码错误时不放行  failed
    step 0  Given 打开 "https://app.example.com/login"      passed  (1.1s)
    step 1  When 输入用户名「alice」与密码「wrong」           passed  (9.4s)
    step 2  Then 页面显示「登录成功」                        failed  votes 0/1  (12.1s)
      原因：AI 断言未过多数票（0/1）：页面显示「登录成功」
      act 0  vote=false  url=https://app.example.com/login
        think: I am on the login page. The task asks whether the page shows "登录成功".
               I see an error banner "密码错误" instead. Returning false.
        截图: file:///…/evidence/…/step-2/act-0-frame-4.jpg
        其余 4 个 frame 已省略（--full 查看）
    step 3  When 点击「退出」                                 passed  (3.2s)
  scenario features/login.feature:20  锁定账户提示  error
    step 0  Given 打开 "https://app.example.com/login"      error  (network_error)
      原因：worker 建连失败（网络/SSL 瞬时故障）：…
      无 AI 证据
    step 1  Then 页面提示「账户已锁定」                      skipped  ⚠ 因前置 step error 被跳过（未执行）
```

**文本预算**：文本形态是给 agent 一次读进上下文的摘要，不是 evidence 全文转写。每个 act 默认只渲染**最后一个带 thought 的 frame**（判否理由通常落在末次观察）及其截图 uri；单段 thought 超过 800 字截断并接一行「…（已截断；完整内容见 --json 或 evidence.json：<ref>）」；被省略的 frame 打一行「其余 M 个 frame 已省略」。`--full` 关闭预算、逐 frame 全文。理由：一个 3 票断言最坏 90 段 thought，文本形态若无预算会一次撑爆 agent 上下文，而它恰是 agent 的首选读法。evidence 缺失的 step 下打一行该 step / 该 scope 的其它原生产物 ref 作兜底指针。

**JSON 形态**（筛选生效时无一命中的 scope 不产出空壳条目）：`{run_id, status, scopes: [{scope_id, engine, status, error_type, message, session_id, report_refs, aborted_hint, has_step_records, scenarios: [{scenario_id, name, status, steps: [{index, keyword, text, status, votes, error_type, message, shortcircuited, duration_ms, report_refs, record_missing, evidence: <evidence.json 全文> | null, evidence_missing}]}]}]}`。`report_refs` 原样搬既有字段、不解析（含 evidence 之外的 trajectory / report / summary）：explain 已从 ResultStore 读到整个 JobResult、这些 ref 就在手上，云端 `status --json` 只投影 RunState 没有它们，不搬等于让 agent 自己去 S3 抠 `jobs/*.json`。evidence 全文内嵌可以：它不含 base64、只有 uri。**契约页与护栏**：evidence 的固定键单列一节；`frames[].actions[].args` 与 `acts[].result` 是引擎原样透传的对象，内部键随 SDK、不属于本契约，护栏在这两个节点**停止递归**（不是塞 `ignore` 名单——那会连真契约键一起放过），`_leaf_keys` 需支持「指定键处停止下钻」；explain 的护栏样例由手搭的 evidence 夹具喂进渲染器生成（形状与两引擎映射测试共用的真产物裁剪版一致），否则 evidence 那批键根本不进比对。

**退出码：只用 0 / 2，不用 1**。explain 是证据渲染器、不重复表判定（判定码看 `run` / `status --wait`），run 判 failed / error 时 explain 仍退 0；同款先例是 [0041](./0041-agent-facing-cli-affordances.md) 决策四的 `doctor`。0 = 渲染成功（哪怕全部 step 无 evidence、判定明细尚未落地）；2 = 参数错（含 `--step` 未同给 `--scenario`、命中的 scenario 都无第 N 步）/ run 或 scope 不存在 / cloud 档 skew block 或凭证·region·权限不可用。

**归类**：查询类命令，进 [0041](./0041-agent-facing-cli-affordances.md) 决策三的清单；字段进 JSON 契约页（0041 决策五）。所有用户可见文字（`--help`、提示、原因与短路说明、worker 抽取失败那一行日志）同受 [0039](./0039-user-facing-surfaces-no-internal-references.md) 约束，新增的 `evidence.py` / `evidence.mts` / `explain` 落在既有护栏扫描根内。

### 五、与 [0027](./0027-runreport-aggregation-index.md) 的关系：铁律不破，一条消费端规则按层收窄，一个留口子用对的方式填上

- 铁律（`model / wire / schedule` 对 `ReportRef` 永久不透明搬运、永不解析产物内容、永不按 kind 分支）不变。新增的 `StepResult.message` 是搬事件里既有的字符串，不是解析产物。
- 0027「消费端只当 URI 用、不 stat / open」写在皮层只打链接的年代，本 ADR 把它**按层收窄**：`model / wire / schedule / ReportStore` 永不 open / fetch / 改写 ref 不变；皮层侧（`compose.read_resource` 与 `explain`）**只对 gherkai 自有 schema 的 ref（`kind == "evidence"`）解引用**，对引擎原生产物（`report` / `trajectory` / `summary`）仍只当链接、永不解析。解引用许可绑在「内容是不是我们自己定义的 schema」上，不是「皮层就能随便打开产物」。0027 该条原地改写并反向链本 ADR。
- 0027 留口子「trajectory 内部结构化提取」由本 ADR 落地，位置是 **worker**（引擎知识的唯一住处）。0027 的 kind 例举补 `evidence`、「Midscene 保持 scope 级」改为「Midscene 的 report 仍 scope 级，evidence 下沉 step 级」、留口子条目标已落地。

### 六、SDK 格式漂移的防线

两引擎依赖都不是钉死版本（Nova `nova-act>=3.4.187.0`，Midscene `@midscene/web ^1.9.8`）。防线四道：

1. 映射函数只读表中列出的少数字段、每个字段当可选，读不到就 null、不抛；判别按值不按 SDK 标志（`is_tool` / `is_return` 之训）；Nova 的 `prompt` 被 SDK 改写、同属「不能照抄 SDK 字段」。
2. 每引擎一份**由真产物裁成的 fixture**（Nova：真 `_trajectory.json` 去掉 base64；Midscene：真 execution 的 JSON），测试断言映射结果——格式漂移在升版跑测试时变红。
3. `schema_version` 让消费端可判：`explain` 遇到不认识的版本明说 `unsupported_schema`。
4. **Nova 的「json 存在」前提押在一个与 SDK 自身文档相悖的实现细节上**：写盘条件只有「传了 `logs_directory` 且 act 有 step」，与 `replayable` 无关，而 SDK 公开属性却按 `replayable` 判该路径「不可用」。SDK 未来把写盘收进 `replayable` 门 → 所有 Nova evidence 静默变空，fixture 测试**照不出**（它只测映射函数）。故验证清单必有一条**真跑**断言 trajectory json 真落盘且 `frames` 非空。**不靠「顺手打开 replayable」消除该风险**：`simplified_dom` 是必填字段、现恒为空串，一开 `replayable` 每 frame 的简化 DOM 就写进 json，单 act 体量在 300 KB 上再显著上涨。

agent / skill 只依赖 evidence schema 与 `explain` 输出，两者都是我们自己的东西；SDK 耦合被关进每个 worker 的一个函数里且有测试盯着。这是本方案相对「在 skill 里教 agent 读 SDK 产物」的核心优势。

## 被拒方案

- **CLI 事后解析 SDK 原生产物做 explain**：CLI 得认两套随 SDK 版本漂的内部格式、cloud 档先下载兆级文件、引擎知识跑进 CLI（违背 0022 / 0027 的分层）。脆弱只是从 skill 搬进了 code。
- **evidence 内嵌进 `step_done` 事件 / `jobs/*.json`**：改协议；jobs json 从判定记录变成证据仓；截图无论如何要落文件。ref 一条就够。
- **`run --json` / `status --json` 内嵌 evidence**：它们是判定视图，证据按需经 `explain` 取。
- **只给原生 json 加 ref、格式由 skill 说明**：零抽取代码，但把两套 SDK 内部格式写进 skill 散文、无测试盯着，升版即漂。
- **evidence 集中落 `reports/<run_id>/evidence/`**：两引擎上传器的 key 都相对各自 run 目录算，集中落要新增注入 env 与上传根，为目录美观开新路径不值。`explain` 顺 ref 找、落哪对消费者透明。
- **Midscene 走 `outputFormat: "html-and-external-assets"` 目录模式取截图**：report 从单文件变目录，牵动 `kind=report` 的 ref 与中断抢传路径，比 `persistExecutionDump` 代价大得多。
- **截图即时上传**：K × 票数次串行 PutObject 压在判定临界路径上；改为确定性 URI + scope 末 flush 兜底。
- **evidence 用 SDK 的 `is_tool` / `is_return` 或 `ActResult.trajectory_file_path` 公开属性**：真产物 / 真会话下前者恒 False、后者恒 None。

## 不做 / 延后

- **断言时向模型要理由**（Nova `BOOL_SCHEMA` → `{result, reason}`、Midscene `aiBoolean` → 带 reason 的 `aiQuery`）：一行就知道为什么判否，但改了断言提问方式、影响判定质量与两引擎对标口径（[0010](./0010-spike-as-apples-to-apples-benchmark.md)、[0014](./0014-ai-first-assertions.md)），需单独 ADR + 真跑对比。先看 thought 文本够不够用。
- **Nova error act 的现场截图**（失败点直接 `nova.page.screenshot()` + `page.url`）：可补上 Nova 侧 error step 的空 frames，但 CDP 断连类失败下该路径自身也不可用，仍是 best-effort；不混进映射表当既有来源，等 explain 用起来看是否真缺。
- **explain 读事件流找回被中止 job 的 evidence ref**、**detached run 中途可见**：都要新的 core 接缝，各自另议。
- 确定性 step 的 evidence（当时 URL / 截图）：0027 另一留口子，本 ADR 不动。
- 报告 index.html 内嵌渲染 evidence（截图缩略、thought 折叠）：皮层富渲染，等 explain 用起来再定形态。

## 影响面

**code**

- `core/gherkai_core/model.py`（`StepResult.message`；`ReportRef.kind` docstring 约定值补 `evidence`；`StepDone.report_refs` / `StepResult.report_refs` 注释去掉「只有 Nova 有 step 级产物」的暗示）、`project.py`、`serialize.py`（step dict 双向：to_dict 落键 / from_dict `.get` 容缺）。
- `core/gherkai_core/adapters/report_store/local.py`：step 行补 message；产物导航节标题 / tooltip / 空态 / docstring 措辞改「报告产物（引擎原生产物 + gherkai evidence）」；断言旧文案的 `core/tests/test_report_store.py`、`test_s3_report_store.py` 同改。URI→路径解析提升为公开小工具供 `read_resource` 复用。
- `engines/novaact/gherkai_worker_novaact/run_scope.py`（evidence 钩子、追加 ref、删「SDK 在 finally 已写盘」的错误注释）+ 新模块 `evidence.py`；`lib/artifact_upload.py`（Content-Type 映射、`ref_for`）；fixture 测试。
- `engines/midscene/src/worker/run-scope.mts`（`persistExecutionDump: true`、`runStep` 拿 uploader 与 page、step 级 reportRefs 首次出现）+ 新模块 `evidence.mts`（自写结构类型）；`src/lib/artifact-upload.mts`（Content-Type 映射、`refFor`）；fixture 测试。
- `runtime/gherkai_runtime/compose.py`：`read_resource(uri)`。
- `cli/gherkai_cli/__main__.py`：`explain` 子命令（含 skew 闸门、结果树匹配器）；`render.py`：文本渲染 + step 行补原因；`cli/tests/test_cli_json_contract.py`：`_leaf_keys` 支持在指定键处停止下钻 + explain 样例（内嵌 evidence 夹具）。

**文档（反向链逐处列出，Accepted 前逐条核）**

- [0024](./0024-worker-core-protocol.md)：kind 例举补 `evidence`；「Midscene 1 个 report html/worker（scope_done 带）；Nova 每 act 一个 trajectory（下沉 step_done）」改为「两引擎都在 `step_done` 带 `kind=evidence`；Midscene 的 report 仍 scope 级」；协议示例里「只有 Nova 有 step 级 reportRefs」的行内注释同改。
- [0027](./0027-runreport-aggregation-index.md)：kind 例举补 `evidence`；「Midscene 保持 scope 级」句改写；「消费端不 stat / open」条按层收窄并反向链；留口子「trajectory 内部结构化提取」标已落地；index.html 形态 ② 条与空态条措辞同步。
- [0029](./0029-engine-artifacts-to-s3.md)「reportRef 指向的文件」条、[0032](./0032-fargate-execution-environment.md)「上传失败处理」条：各加一行「step 级产物已有一个具名例外：evidence，见 0042」。
- [0037](./0037-distribution-and-packaging.md) 决策 7 接线句：cloud 入口由 run / submit / status 三个改为四个、补 `explain`。
- [0041](./0041-agent-facing-cli-affordances.md)：决策三查询类命令清单补 `explain --json`；「重议闸门」失败证据机读化一条标已由本 ADR 落地并反向链；Status 头**保持 Accepted**、按 0030 / 0034 的既有写法追加一句反向链——0041 无决策被反转，不写 Partially-superseded。
- `docs/guides/cli-json-contract.md`：`run --json` steps 表补 `message`；step 级 `report_refs` 说明补 `kind=evidence`、两引擎皆有；新增 `explain --json` 一节（含 evidence 固定键与两个不透明节点、`record_missing` / `evidence_missing` 取值）。
- `cli/README.md`（explain 用法；退出码节补「explain 只说证据读出来了吗、不表判定」；index.html 描述含 evidence 行）、根 `README.md`、`cli/DEVELOPMENT.md`（RunReport 内部：清单含 evidence）、`DEVELOPMENT.md` ADR 范围、`engines/midscene/DEVELOPMENT.md` worker 模块枚举补 evidence。
- `CONTEXT.md`：术语表 kind 枚举补 `evidence`、两引擎 step_done 带 evidence 一句（core 不透明搬运那句主语是 core、仍成立，只补皮层解引用半句）；版本单旋钮的 cloud 入口数三改四。

**交付链（不改 IaC 资源，但不重部署云端看不到）**

- cloud 档的 `jobs/*.json` 由 reconciler Lambda 投影产出，Lambda 里的 `gherkai_core` 是部署时从已安装包复制进 asset 的（[0037](./0037-distribution-and-packaging.md) 决策 6）→ `StepResult.message` 要重跑 `gherkai deploy` 才在云端生效。
- evidence 住 worker 镜像 → 云端要产 evidence 必须推带新 worker 代码的镜像（dev 树 = `gherkai deploy push-worker`；发行版 = 新基底 + `gherkai deploy`）。

## 验证（Accepted 前必做，结论内联到此处）

- 单测：两引擎映射函数对真产物 fixture（含 Midscene 的 error task、Nova 的 N 票）；best-effort 路径（抽取 / 上传抛异常 → `step_done` 照发、无 evidence ref、status 不变）；serialize round-trip 带非默认 step message；`explain` 本地 / 云端两档读取、`record_missing` 与三种 `evidence_missing`、多命中 `--scenario` + `--step`、退出码；cloud 档 skew 三态；契约护栏含 evidence 夹具。
- 真跑（跳板机；**先重传 Lambda asset + 推新 worker 镜像**，否则 cloud 档必然看不到 message / evidence、易误判成 bug）：
  - Nova 故意失败的 AI 断言：trajectory json 真落盘、evidence.json 的 `frames` 非空、末帧 thought 解释了判否、`vote=false`；
  - Nova 故意 act 超时（`ActTimeoutError`）：evidence.json 可解析、`acts[0].error` 非空、`frames == []`、`explain` 退 0；
  - Midscene 故意失败的 AI 断言：`Insight/Boolean` 的 thought 进 evidence、截图文件存在且被引用；
  - 截图在浏览器**渲染**而非下载（Content-Type=image/jpeg）；`explain --json` 可被严格解析；cloud 档 `s3://` 读取可用、flush 后截图 URI 可取。
