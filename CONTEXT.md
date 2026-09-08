# Gherkin × (Midscene + Nova Act) × AgentCore 测试框架

一套用 Gherkin 描述测试意图、由两个互相独立的 AI 引擎执行、由 AWS 云端浏览器承载的 UI 自动化测试框架。三层正交，靠 CDP（Chrome DevTools Protocol）串联。

## Language

**引擎 (Engine)**:
一个独立的「AI 大脑 + Playwright 驱动」组合，负责把自然语言意图变成浏览器动作。本项目有两个平级、互不替换的引擎：Midscene 与 Nova Act。
_Avoid_: runner（脚本跑测试的工具，含义太窄）、driver（只指底层 Playwright）

**大脑 / 模型角色 (Brain / Model role)**:
引擎内部做决策的 AI 模型。一个引擎可拆成多个模型角色，最关键的是「视觉定位」这一非可选的主力角色。
_Avoid_: 把「模型」与引擎混为一谈——Nova Act 是引擎不是模型。

**视觉定位 (Grounding)**:
把屏幕截图解析成可点击坐标的能力，是 Midscene 主力大脑的核心职责。质量随所选大脑而异（如小字/非拉丁文字的定位弱项属 GPT-5 系，见 ADR 0002）。
_Avoid_: 把 grounding 与 planning（规划/推理角色）混用。

**AgentCore 浏览器会话 (AgentCore Browser session)**:
AWS 托管的、隔离的单个云端 Chromium 实例，暴露一个 CDP-over-WebSocket 自动化 endpoint（鉴权用 upgrade 请求上的 header-based SigV4）。一个会话只承载一个自动化客户端——两个引擎需各自一个会话，不共享。
_Avoid_: 把「会话」与「endpoint 种类」混为一谈。注意此处的 CDP-endpoint SigV4 与 Midscene 调 Bedrock `/openai/v1` 的 SigV4 是两套不同的签名场景，别混。

**穿刺 / Spike**:
一次性、风险优先的最小垂直切片，目的是用最小代价撞通最可能失败的环节、得到「成不成」的认知，而非交付可维护代码。
_Avoid_: 把 spike 与里程碑（M1–M5 的工程推进）混用。

**用例描述层 (Feature)**:
语言无关的 Gherkin `.feature` 文件，描述业务可读的测试意图。**核心库自解析**这份 `.feature`（单一事实源，ADR 0022/0025），分组成 scope/job 后把有序 step 派发给两个引擎 worker（BDD runner 已退役，ADR 0022）。
_Avoid_: 把 feature（意图描述）与 step 派发执行混用。

**骨架验证用例 (Skeleton case)**:
为证明链路本身活着而刻意挑选稳定、中立、英文、无登录站点（如维基百科）写的探针用例。与「真实业务用例」分开看待，避免把站点不稳定的噪声误判成框架缺陷。
_Avoid_: 把骨架验证用例当成最终交付的业务测试。

**穿刺脚本落点（by-engine）**:
spike 脚本**紧贴各自引擎的语言/依赖环境**，放在对应子工程内、诚实标记可丢弃：
- Midscene（TS）→ `engines/midscene/spikes/`，复用 `engines/midscene/node_modules`（含其配方笔记 `SIGV4-FETCH-RECIPE.md`，与代码同居）。
- Nova Act（Python）→ `engines/novaact/spikes/`，用仓库根 workspace 的 `.venv`（`uv run python engines/novaact/spikes/…`；novaact worker 已包化、无独立 venv，ADR 0037）。
不设 git 根级 `spikes/`，spike 紧贴各自引擎子工程。**引擎内**复用的代码（如 Midscene 的 SigV4，仅 Midscene 的 spike 与 bdd 共用）抽到该引擎的 `lib/`（见 `engines/midscene/src/lib/agentcore-sigv4.mts`）；这不是跨引擎共享——SigV4 是 Midscene 专属，Nova Act 走 IAM/Workflow 不碰它。跨引擎真正共享的是 `features/`（用例），见 [跨引擎共享边界](./docs/adr/0013-cross-engine-sharing-boundary.md)（ADR 0013）。
_Avoid_: 把某一引擎专属的 spike/文档/代码放到根级或另一引擎目录下；也别误以为引擎内的 `lib/` 是两个引擎共享。

**确定性断言 vs AI 断言 (Deterministic vs AI assertion)**:
确定性断言用底层 Playwright（`nova.page` / Midscene 的 page）判定，结果可复现；AI 断言用自然语言（Midscene `aiBoolean` / Nova `act_get(BOOL_SCHEMA)`，对称布尔投票，ADR 0014；**不用** Midscene 的 `aiAssert`——抛错黑盒、机制与 Nova 不对称，是被拒方案）判定，贴合卖点但非确定性、且每次消耗模型调用。**已定（ADR 0014）：AI 断言为默认主力**（忠于框架卖点），确定性断言退为高保真补充与逃生舱；代价是非确定性，须配套抖动治理（重试/投票/度量）。抖动治理的具体参数与"哪些判定强制走确定性"靠更难用例的数据迭代。
_Avoid_: 把 AI 断言当成"无需治理就可信"——它为主，但必须配抖动监控。

**报告产物模型 (Report artifact model)**:
两个引擎的报告形态根本不同：**Midscene 出单一 `report.html`**（含每步截图+AI 决策+坐标，整 scope 一份，`kind=report`、挂 scope 级）；**Nova Act 每次 `act`/`act_get` 出一个 trajectory HTML**（`kind=trajectory`、挂到其所属 **step** 级）+ 一份 `session_summary.json` 数字汇总（`kind=summary`、挂 scope 级）。worker 经 0024 协议把产物**指针**报回 core（`reportRefs.ref`，core 内类型 `ResourceUri`＝带 scheme 的统一资源指针：本地 `file://`、未来云端 `s3://`/`https://`，故非裸本地路径；字段形状见 ADR 0024），core **不透明搬运**（不 stat/不 fetch/不打开 ref）。**`kind` 表产物类型（report/trajectory/summary/未来 video/trace），粒度由 report_ref 挂在 step/scenario/scope 哪级表达——二者正交**。同一 `ResourceUri` 也是 `ReportStore.write` 的返回类型（统一"资源指针"概念，ADR 0027）。**RunReport（ADR 0027）= 跨引擎归集索引**：`ReportStore` 把 `RunResult` 归集成 `manifest.json`（机器可读）+ `index.html`（人可导航入口），**不解析/不融合原生产物内容**，只索引/链接（cli 每次 run **默认生成**，`--no-report` 跳过）。index.html 的导航链接（`href`）local 相对化（产物本在 run 树内、目录可整体搬走）、cloud 恒为 `s3://`；`ref` 原始指针原样不改（不透明铁律）。新引擎报任意 `kind` 零改 core（永不按 kind 分支）。
_Avoid_: 笼统说「两个引擎都出报告」而忽略其形态/落点的根本不同；把 `kind` 当粒度维度（它是产物类型，粒度由挂载层级表达）；把 RunReport 当成「解析两个引擎 html 融合成一个大报告」（它只归集索引、不碰产物内容）；以为 core 会按 `kind`/引擎分支处理产物（永不——扩展性契约，ADR 0027）。

## 产品形态

**通用 step (Generic step)**:
极少数**抽象原语**：URL 导航（确定性，含引号内 URL）/ AI 动作（When）/ AI 布尔断言（Then，+投票）/ 确定性锚点（脚手架）。任何用例复用，QA 不写代码——场景细节放进引号里的自然语言，不放进 step 措辞。这是"QA 只写 `.feature`、零代码"承诺的唯一载体，**其能力边界 = 产品能力边界**。两个引擎对称实现（函数签名见 ADR 0018/0020）。**「取数/取串」等原语已删**（ADR 0018：避免过度设计，QA 直接写自然语言让 AI 判，需精确数值走确定性锚点）。AI 动作/断言 step 可挂 **Gherkin DataTable/DocString 多行参数**（一次填多字段表单、粘一大段文本）——worker 拼成附加文本（dataTable→markdown 表格、docString 原样）随 step 自然语言一起喂 AI（确定性/URL 导航路径不接），两个引擎对称（ADR 0024）。
_Avoid_: 写绑死具体场景的 step（如"语言版本数量"）——那不是通用 step；把它当成"任意动作都能稳跑"——开放性动作会引入页面瞬态 flaky（ADR 0018）。

**柔性冒烟 (Flexible smoke)**:
v1.0 的核心定位（ADR 0015）——只验证业务**意图是否达成**（流程能否走通），对达成路径上未被点名的视觉/文案/布局变化高度宽容。AI 柔性是差异化核心，与"精确回归（任何差异都报警）"本质对立。
_Avoid_: 把它当精确/像素级回归工具用。

**点名检查 (Explicit check) vs 确定性锚点 (Deterministic anchor)**:
两个不同层（ADR 0020）：
- **点名检查**：QA 想精确核对某项时，直接写**纯自然语言** `Then "价格是 ¥99"`——仍走**默认 AI 判断**（QA 零代码、无路由关键词）。「能否抓某类变更」取决于 QA 点没点名，不是做不到。
- **确定性锚点**：少数"不容 AI 抖动"的精确检查（URL/DOM），由 **test engineer** 在使用方项目的 `steps/` 目录写 `@deterministic` 注册（Playwright 查询；worker 包内的 `deterministic_steps` 脚手架只留内建示例），不走 AI、不预置（QA 不碰；ADR 0037 决策 4）。
_Avoid_: 以为"不点名也能抓变更"；把它与 A/B 两种不确定性混为一谈；以为 QA 要学特殊措辞（QA 永远只写自然语言）。

**两种不确定性 (A: flakiness / B: 柔性吞变更)**:
A = 同一页面 AI 判断飘忽（随机噪声）→ **投票可治**；B = 页面真变了但 AI 柔性照样跑过、不报警（灵敏度不足）→ **投票治不了**，v1.0 接受为已知边界（ADR 0015）。
_Avoid_: 以为"投票能带来确定性"——它只压 A，给不了对变更的灵敏度（B）。

**连锁失败读法 (error → 后续 step 短路跳过)**:
scope 内 step 串行，**上一 step `error`（如导航 SSL/网络故障）会短路本 scenario 后续 step**（ADR 0031 决定六 / 0028）——worker 不再对后续 step 调 AI（① 省钱；② 不在**已损坏的环境**（如停在 SSL 错误页）上跑出误导性假失败），而是为每个被跳过的 step 发独立 `step_skipped` 事件；core 据此本地赋 `StepResult(status=skipped, shortcircuited=True)`。**判据锁 `status==error`（不看 error_type）**——两个引擎对称、network/engine 错都触发；**只短路本 scenario**（下一 scenario 可能导航新页恢复，独立用例不牵连；跨 job 是 fail-fast 职责，正交）。`shortcircuited` 是与判定轴（status）正交的第二维（"为什么 skipped"），cli 文本汇总与 RunReport index.html 据此加视觉旁注"因前置 step error 被跳过"。**短路是 worker 行为**（因果只存在于 worker 的串行循环）；core 仍是纯 reducer（ADR 0026）——忠实归约 `step_skipped`、不臆断因果。**skipped 两级同名不同层**：job 级 skipped（fail-fast 整个 job 没 spawn、无 step 明细）vs step 级 shortcircuited（job 跑了一半、剩余 step 被短路、有 step 明细），语义都是"没跑"、层级不同。历史：早期无 step 短路时，"error 后的 failed"曾靠"按 status 顺序猜"加旁注（渲染层缓解）；现已升级为执行层短路 + 读 `shortcircuited` 精确判定。
_Avoid_: 把 step 级 `shortcircuited`（scope 内短路）与 job 级 `skipped`（fail-fast 没 spawn）混为一谈；以为短路跨 scenario（只短路本 scenario）；以为 core 会臆断因果（短路判据在 worker，core 只归约）。

**成本可观测 (Cost observability)**:
产品价值之一：一次跑批花了多少（ADR 0024）。**原则——engine 只报原生量、core 只各自合计、不折美元**：两个引擎计费轴不同（Nova 按 agent 工作时长 `time_worked_s`、Midscene 按 LLM token），core 各自累加成 `total_time_worked_s` / `total_tokens`（step→scope→run，无引擎报则 None）。**美元折算交消费者**（用自己 AWS 账户的真实费率）——框架不内置费率常量（避免追会过期的单价表）。与**墙钟时长** `duration_ms`（性能）正交：`time_worked_s` 是 Nova 计费量、`duration_ms` 是 core 测的执行墙钟，两个数不同。
_Avoid_: 以为框架算美元（不折美元、只报原生量，美元交消费者）；混淆成本 `time_worked_s` 与性能 `duration_ms`。

**Run 数据模型 (Run data model)**:
执行的层级（ADR 0016）：**Run ⊃ Job(=Scope) ⊃ Scenario ⊃ Step**。Scope = 共享操作上下文的 scenario 分组，是执行单元（scope 内串行、scope 间并行）；Feature 是正交的组织轴。Step 是最细一级（core 经 `StepResult` 保留 step 级粒度）。各级带**墙钟时长** `duration_ms`（性能指标）。Run 产出两样：**RunResult**（机器可读汇总判定，给退出码/CI/WebUI；含 run_id、status、各级时长、原生量成本合计 `total_tokens`/`total_time_worked_s`）与 **RunReport**（人看的归集索引，原 M5「报告统一」的归宿，**v1.0 已实现**：manifest.json + index.html 入口，只索引/链接原生产物、不融合内容，ADR 0027）。
_Avoid_: 把 Feature 当执行单元；**把 Job 当 scenario 粒度（破坏会话依赖）——Job = Scope，不是 scenario**；混淆 RunResult（数据）与 RunReport（报告）。

**标识符 (id：scenarioId / scopeId)**:
关联键（把 worker 事件挂回 scenario、未来做 RunStore/DDB 主键），是**不透明标识符**——只在 JSON/dict key/未来 DB key 用，全支持任意 UTF-8（空格、中文路径原样保留，**不 normalize**：任何清洗字符的转换都会把不同输入映射成同一输出、制造撞名，而撞名是静默灾难，比"id 含空格"严重得多）。core **不拿 id 当路径解析**。`scenarioId = <uri>:<行号>[:<example行号>]`；`uri` 由调用方原样传入、core 不解析。**唯一性责任在调用方**：plan 要求 `features` 列表 uri 互异（重复 = 接口违约 → 报错，ADR 0025）。若未来某消费层（URL/文件名）需安全字符 id，由该层做**可逆**编码（urlencode 等、保唯一），不在 core 做有损 normalize。
_Avoid_: 对 id 做有损 normalize（撞名风险 > 可读性收益）；把 id 当文件路径去读；以为 uri 重复会被 core 静默 merge（那是撞 id 的 bug，core 报错；跨文件同 `@scope` 合并是另一回事，见 scope 语义）。

**执行核心库窄腰 (Core-library narrow waist)**:
真正的窄腰是**执行核心库**（解析 `.feature` → 分组 scope → 调度 → 收集结果），**不是 CLI**（见 ADR 0016）。CLI 是核心库的第一个、最薄的前端；WebUI 是另一个前端，**直接调核心、不 shell-out CLI**。CI/skill 通过 CLI 这个皮间接用核心。上层前端与可替换的执行引擎（`Engine` port，本地进程 / Fargate；见下「执行引擎 port」条）都围绕核心库解耦。
_Avoid_: 把逻辑焊死在 CLI `main()` 里；以为"WebUI 要包 CLI"；把"选哪个执行引擎（`Engine`）"当成一锤定终身。
（版本演进 spike→v0.x→v1.0→v1.x→v2.0 见 ADR 0016。）

**执行引擎 port (Engine port)**:
核心库之下真正跑一个 scope 的地方，是一个 **port**（`Engine`，对齐「引擎」术语，ADR 0016），由组合根注入。v1.0 实装为**单个参数化 `SubprocessEngine`**（`cmd`/`cwd`/`env` 参数化即可 spawn Node 或 Python worker——两个引擎"spawn 子进程 + 讲同一套 0024 协议"形状本就一致，无需两个具名 adapter 类；经 `EngineResolver` 按 `job.engine` 选）。演进：v1.0 本地进程（`SubprocessEngine`，浏览器仍在云端 AgentCore Browser）；执行进程上云已实装——`FargateEngine` + `gherkai-deploy-aws` 的 CDK stack（`gherkai deploy` 部署），`--backend cloud` 同时切 Fargate/ECS 执行（批处理 shape-fit 优于 AgentCore Runtime，ADR 0017；已建成真部署，ADR 0032/0033）。
_Avoid_: 混淆"浏览器在云端"（spike 已验证）与"执行进程也在云端"（Fargate，已建成）——两者现皆在云、但仍是两件事；把它当成"核心 import 引擎"——核心永不 import 引擎，只 spawn worker。

**两个引擎都子进程 + 薄 worker (Both-legs-subprocess + thin worker)**:
两引擎语言锁死（Midscene 锁 TS、Nova Act acting 锁 Python，ADR 0023 证伪了全 TS 核心），故核心（Python）**对每个 scope spawn 一个 worker 子进程**——两个引擎对称、核心零引擎依赖。worker = 被 spawn 的进程，一生 = 开 AgentCore 会话 → 按 scope 串行跑 scenarios（每 step 派发成 act/assert）→ 回 JSON → 退出（一次调用 = 一个 job = 一个 scope）。**核心自解析 Gherkin**（单一事实源），worker 只派发不解析——故 cucumber 补丁与 pytest-bdd 路由 hack 退役（ADR 0022）。
_Avoid_: 以为子进程里跑整个 BDD runner（那是被否的 B2）；把 worker（运行时角色）与 engine（领域概念/目录名）混用。

**确定性 step 注册表 (Deterministic step registry)**:
test engineer 扩展确定性锚点的落点：在对应 worker 里登记 `(模式 → handler)`（`@deterministic`）。核心发原始 step 文本，worker 先查注册表命中走精确 handler、未命中落 catch-all 走 AI。匹配放 worker（确定性 handler 引擎特定，碰 Playwright/CDP），核心对 step 语义无知。延续 ADR 0020 角色边界（QA 永不碰）。**注册即暴露**：`description`/`example` 是 `@deterministic` 的必填 kwarg，缺则注册时 fail-loud（ValueError）——裸正则对 feature 作者不可读（ADR 0036）。**能力可发现**：worker 另有两个自述入口（`--list-deterministic` dump 清单 / `--match-steps` 批量回答某批 step 命中什么），CLI `list-deterministic --engine` 与 `plan` 的派发标注（含多模式冲突预检）只是转述之——匹配语义仍 100% 在 worker，core/CLI 不持有 pattern。
_Avoid_: 把匹配放进核心（核心只解析结构+调度，不懂 step 语义）；以为 QA 要写确定性 step；以为清单是另一份外置文件（那是双事实源、必与代码里的 pattern 漂移，ADR 0036 被拒方案）。

**Ports 层 (Ports & adapters)**:
核心库把可替换的外部依赖收成独立 port，导出稳定接口；核心只依赖接口。四个核心 port（ADR 0016）：`Engine`（跑 scope）、`RunStore`（**控制面**：run 的 definition(RunMeta) + 运行态(RunState：status/血缘/起止)，频繁读写、撑轮询续跑——DDB 主要服务它）、`ResultStore`（**数据面**：每 job(=scope) 判定真值/投票，追加为主——判定真值唯一权威）、`ReportStore`（把 `RunResult` 归集成 RunReport=manifest+index 的派生只读导航视图，ADR 0027）。`RunStore` 从原 `ResultStore` 拆出（控制面 vs 数据面访问模式不同）。**v1.2 无状态跑批另加两个同性质 port**（ADR 0034，定义在 `core/gherkai_core/reconcile.py`——只服务无状态推进路径）：`EventLog`（事件日志：local SQLite / cloud DDB events 表，reconciler 全量重放推演状态的写模型）与 `Launcher`（起一个 job：subprocess / ECS RunTask），同样由组合根注入、同样可替换。**具体 adapter 由组合根（CLI main / WebUI bootstrap）注入**，不由 module 内部 env-sniff 自选（后者是本项目踩过的 Midscene `GlobalConfigManager` 反模式）。**两套 store 对称并存**：四个 port 的 local adapter 落文件（见 `core/gherkai_core/adapters/`，落盘形状以代码/ADR 0016 为准），cli 落 `<report-dir>/<run_id>/`；cloud 侧 RunStore→DynamoDB、Result/ReportStore→S3（+ StepArgument offload 解 DDB 400KB 限），**行为对拍 local**、boto3 走库层可选依赖 `gherkai-core[aws]` / `gherkai-runtime[aws]`（ADR 0030 决定六；CLI 发行包 `gherkai` 则**硬依赖** `gherkai-runtime[aws]`，ADR 0037 决策 2c——库层 extra 只留给库消费者，code 层「local 路径绝不 import boto3」的懒加载不变量不动）。两套都只持久化已成形模型，**未发明 ADR 有意 defer 的字段**（jobId、job 级起止待真实需求逼出；run 级起止已由 ADR 0030 实装）。注哪套由 `--backend {local,cloud}`（默认 local，ADR 0030 决定七）定，两套 store 在产品本体 `runtime/gherkai_runtime/compose.py` 对称装配（cli/Lambda/未来 WebUI 共用，ADR 0016「演进」节）；`--backend cloud` 同时把执行面切到 `FargateEngine` + `gherkai-deploy-aws` 包的 CDK stack（`gherkai deploy`，ADR 0032/0033/0037）。**无状态跑批（v1.2，ADR 0034）**：`submit` 提交完就走 + `status [--wait]` 轮询/接力收集（同步 `run` 保留）——CQRS + 无状态事件驱动 reconciler（core 抽纯 `project`/`plan_next` + `reconcile.tick`，local/cloud 共用；local=per-run 进程+SQLite events sink，cloud=三 Lambda 事件驱动链 + DDB Stream + EventBridge，链上分工见 ADR 0034）。**「续跑/轮询读取面」由此定型**：外部只读 `RunState`（reconciler 是唯一写者、纯从 events 推演）、`RunState` 加 `high_water_mark` 挡并发 stale 覆盖——不再是「待逼出」。
_Avoid_: 把多个 port 揉成一个上帝 module；让 port-module 用全局单例自选实现；混淆控制面（RunStore）与数据面（ResultStore）。

**本地应用暴露 / 隧道 (Local app exposure / tunnel)**:
把「跑 CLI 的机器可达」的被测应用（`http://localhost:3000`，也可是局域网另一台机器）经隧道暴露给云端浏览器的能力，由 `--expose-local <origin>` 显式启用（ADR 0035；默认路径零新依赖、零出网变化）。`TunnelProvider` 是**组合根共享层（`runtime/gherkai_runtime/`）的可插拔口子**、不是 core port——首个也是当前唯一实现 ngrok（`runtime/gherkai_runtime/tunnel.py`；对 ADR 0009「最大化用 AWS」的登记例外，AWS 内实查无「开发机 → 云端浏览器」这条入站通道的等价物）。**URL 映射在组合根做**：起隧道拿到公网 URL 后，把 job 文本及其 argument 里该 origin 前缀替换成隧道 URL（前缀字符串级，`localhost` 与 `127.0.0.1` 不互认），故 core/worker/引擎/AI 对隧道无知；`plan` 显示替换前的原始地址（零副作用）。认证 = URL 内嵌随机 basic-auth 凭据（ngrok 边缘节点拦截），安全面靠随机 URL + 随机凭据 + **每 run 一换 + 终态即拆**。隧道宿主按跑法分三形态（前台 `run`=CLI 进程 atexit / local `submit`=per-run 进程 / cloud `submit`=setsid 守护进程 + TTL 兜底，编排见 `runtime/gherkai_runtime/tunnel_host.py`）。
_Avoid_: 以为 core/worker 懂隧道（映射在组合根；definition 只多一个 `RunMeta.extra_http_headers`）；以为「提交完就走」＝可以关机（关机/断网=隧道断=run 以导航失败告终，是明示边界不是 bug）；把守护进程 TTL 当可随手拍小的保险常数（TTL 到点无条件拆，短于实际预算会让剩余 job 在应用不可达下跑成假失败——故按 definition 算，见 ADR 0035 决策 3）。

**推进器 (advancer)**:
把 run 从提交推到终态的执行体统称——**角色词、不是组件名**（code 里没有单一对应符号，这也是造词的原因）。按驱动模型分：同步驱动的推进器 = CLI 进程内的 `schedule()` 循环；无状态驱动的推进器 = 调 `reconcile.tick` 的宿主，共四个——local per-run 进程、local `status --wait` 接力者、cloud kicker λ、cloud reconciler λ（后两个同 code、都跑完整 `tick`——kicker 不是「只起首批的薄壳」，而是与 reconciler 等价的完整推进器，差别只在触发面：kicker 接 runs 表 Stream、`status --wait` 的踢一脚与超时闹钟到点，reconciler 接 events 表 Stream 的事件级联。冷启动时 kicker 的输出恰好是「起首批」——那是完整 `tick` 对空 run 的自然结果、非专用精简逻辑；其另两个入口做的接力推进与超时处置，靠的正是同一份完整 `tick`）。文档里两种计数并存、切面不同：「三路推进器」按跑法数（同步 `run` / local `submit` / cloud `submit`），「四个宿主」按进程数（只数 `tick` 的）。机制见 ADR 0034（核心思想与机制一–四），给人的导览见 `docs/guides/execution-and-reconciliation.md`。
_Avoid_: 把「推进器」读作 reconciler 的中文名——reconciler（无论指 CQRS 机制角色还是同名 Lambda）只是推进器之一；在 README 层使用本词（内部抽象，README 用命令/组件的具体名，读者上下文里没有它）。

**job 墙钟预算 (job timeout)**:
「一个 job 最多跑多久」的用户预算（墙钟，从推进器起这个 job 时起算——detached 档即 claim 时刻，故含拉镜像/挂 ENI 等启动开销）。**两层声明、tag 优先**：scope 级 `@timeout:N` tag（ADR 0019；同 scope 声明不一致 → `PlanError`）+ CLI `--default-job-timeout`（未标 tag 的兜底，`<=0`=不超时），与 `@engine`/`--default-engine` 同构。**载体在 definition**（`Job.timeout_s`，随 RunMeta 持久化）——预算属 run 的定义、与推进方式无关，故必须随 run 走到任何推进器；三路推进器（同步 `run` / local per-run 进程 / cloud 事件驱动链）各自 enforce 同一形态「到点回调 → 仍未终态则 stop → 交既有退出观察链收敛」，worker 不消费 timeout（只守 flag-only 停止契约）。超时归因 = `error` + `error_type="timeout"`（主动中止而非引擎故障，ADR 0031 决定一）。两层取舍与三路 enforce 见 ADR 0034「job timeout」节。
_Avoid_: 把它当运行参数（曾是 `ScheduleOpts` 参数、不进 definition，detached 推进器就拿不到它——已退役）；与 act 级超时（Nova 的 `NOVA_ACT_TIMEOUT_S`）或尚未做的 run 级总预算混为一谈；以为 worker 会自己超时自杀（enforce 全在推进器侧）。

**三名分离：发行名 / import 名 / 命令名 (dist name / import name / command name)**:
（ADR 0037 决策 2；**三名分离已随发行重组落地**：`core/gherkai_core`＝`gherkai-core`、`runtime/gherkai_runtime`＝`gherkai-runtime`、`cli/gherkai_cli`＝`gherkai`＋命令 `gherkai`，三者是根 uv workspace 的成员；`gherkai-worker-novaact`/`gherkai-deploy-aws` 两个发行名待引擎/部署层包化。尚未上 PyPI，首发即 1.4.0。）一个 Python 交付物有三个名字、各自独立取：**发行名**是 PyPI 上的包名（`gherkai` / `gherkai-runtime` / `gherkai-core` / `gherkai-worker-novaact` / `gherkai-deploy-aws`），**import 名**是 `site-packages` 里的顶层目录（一律 `gherkai_` 前缀：`gherkai_cli` / `gherkai_runtime` / `gherkai_core` / …），**命令名**是 console script（`gherkai`）。唯一硬约束：**用户敲的发行名 = 命令名**（`uvx <name>` 把 `<name>` 同时当发行名与命令名解析），故 CLI 发行包叫 `gherkai`、中间层让位叫 `gherkai-runtime`。版本真源 = git tag，兄弟包间 `==` lockstep pin（ADR 0037 决策 2）。
_Avoid_: 用裸通用词作发行名或 import 名（`core`/`cli`——前者 PyPI 已被占、后者与他人同名顶层包静默合并/互删）；把「发行名 ≠ import 名」当异常（`gherkin-official` 的 import 名就是 `gherkin`，是常态）；为兄弟包写 `>=` 范围依赖（装出未测混搭）。

**worker 定位链 (worker locate chain)**:
（已落地：`repo_root()` 已整体退役，ADR 0037 决策 3；第四级 fd 预演已做——uvx 穿透、保留给 novaact；npx 不穿透、midscene 无第四级。）组合根解析「用什么命令 spawn 某引擎 worker」的四级顺序：① env `GHERKAI_WORKER_<ENGINE>_CMD`（+ 可选 `_CWD`）显式覆写 → ② 同 venv 入口（Python 引擎：`sys.executable -m gherkai_worker_novaact`，经 CLI extra `[local]` 装进 CLI 自己的 venv）→ ③ PATH 上的可执行（`gherkai-worker-<engine>`，midscene 由 `npm i -g @gherkai/worker-midscene` 提供）→ ④ 兜底拉起 `uvx gherkai-worker-novaact==<CLI 版本>`（仅 novaact、仅纯发行版本；npx 实测不穿透 fd3，midscene 无此级）。四级全 miss 抛结构化异常、由调用点分叉处置（`run`/`submit`/`list-deterministic` 退 2，`plan` 保持 best-effort 降级）。dev 与分发**同一条链**、不设 dev 模式特判（ADR 0037 决策 3）。
_Avoid_: 让 worker 定位依赖 repo 目录结构（分发后没有 repo）；把「安装」与「拉起」绑在一起（二者正交：`[local]` 负责装、定位链负责起）；给 worker 定专属 cwd（产物落点一律经绝对路径 env 注入；`--no-report` 档不注入落点并经 `GHERKAI_NO_ARTIFACTS` 令 worker 不生成/不上报产物）；在定位链里统一退码（`plan` 的降级契约是 ADR 0036 已定行为）。

**steps 目录 / 定制面 (steps dir / customization surface)**:
（已落地，ADR 0037 决策 4；worker 包内的 `deterministic_steps.py` / `deterministic.steps.mts` 只留内建示例。）使用方放确定性 step 定义文件的目录（默认项目内 `steps/`，`--steps-dir` / env `GHERKAI_STEPS_DIR` 覆写），是**使用方的地盘**、与 features 同处。提交侧解析成绝对路径**随 definition 持久化**（`RunMeta.steps_dir`），所有起 worker 的宿主从 definition 读回、经 env 注给 worker；worker 启动时排序递归加载（Python `*.py` 顶层 `@deterministic` 副作用注册 / TS 只认 `.mts`/`.mjs`——模块体系不依赖使用方目录的 `package.json#type`——动态 import，裸 specifier `@gherkai/worker-midscene` 由 worker 随 dist 发布的 resolve hook 解析到自身同一 URL），**任一文件加载失败即 fail-loud 退出（两侧）；midscene 侧另有「加载后零注册即退出」的双实例护栏**，三个自述入口同样加载，故 `list-deterministic`/`plan` 标注反映定制。cloud 档：steps 烙进定制镜像（`COPY steps/` + `ENV`），镜像里的 steps 是否最新由使用方管理、preflight 不比对，想区分就换 variant（ADR 0037 决策 4、ADR 0038）。
_Avoid_: 把「定制」理解为改 worker 包源码（那是 fork 模式，PyPI 化后不成立）；让约定逻辑进 worker（worker 只认 env）；加载失败静默跳过（确定性 step 会被静默换成 AI catch-all）；引入「使用方覆盖内建」优先级（撞 pattern 按 ADR 0036 conflict 语义处理）。

**worker 镜像：基底 / variant / 默认指针 (worker image: base / variant / default pointer)**:
（ADR 0038，**已落地**：`gherkai deploy push-worker` / `list-workers`、deploy 四步、运行时显式 revision、preflight variant 解析；真账户实测待清。曾经的形态——`tools/build_push_workers.py` 全量 build、task-def 焊死 `latest`、RunTask 传 family——已退役。）**基底**由维护者 CI 发到 GHCR（`ghcr.io/zhiyanliu/gherkai-worker-{novaact,midscene}:X.Y.Z`，linux/amd64，零使用方内容，ADR 0037 决策 5）。**variant** = 一套具名的确定性 step 集 = 一个定制镜像：developer 本地 `FROM 基底` + `COPY steps/` 自己 build（必须 `--platform linux/amd64`），部署方 `gherkai deploy push-worker <本地镜像> --engine <e> --variant <名>` 推送到自己私有 ECR（tag = `<CLI 版本>-<variant>`，`gherkai_runtime.names.image_tag` 归一化 + 校验）（推送前校验架构、不是 amd64 即退 2）并为该（引擎，variant）注册一个 **按推送后取得的 digest 引用镜像、tags 记血缘**的 task-def revision，映射记进 SSM；基底同步进 ECR 的那份叫 `base`。**默认指针**（SSM，部署级一个）决定提交时不给 `--worker-variant` 用哪个，deploy 初始化为 `base`、`push-worker --set-default` 改指、升级不重置。运行时只用 definition 里解析好的显式 revision、永不用 family（旧 definition 缺字段时按后端默认指针解析）；tag 可变、replace 自决；旧 revision 先打 `retired-at` tag，由 push-worker / deploy 末尾的清理 pass 在静默期满且无在跑 run 引用时删；push 前先校版本 skew。多版本并存 = 多 prefix 多环境，CLI 经 `--prefix` 显式选择。
_Avoid_: 让 gherkai 拥有镜像构建（只给三行模板）；把 variant 参数叫 `--tag`（它只是 tag 后缀）；task-def 引用 `latest` 或 RunTask 传 family（任何一次 push 都会劫持默认）；revision 按 tag 而非 digest 引用（重推会换掉在跑 run 的镜像）；让 preflight 比对镜像内 steps 与本地 steps（内容由使用方负责、提交者未必有 steps 目录）；支持 ARM64/多架构（Fargate ARM64 有按 AZ 的不可用面，复杂度不值，ADR 0038 被拒方案）；用 SSM 列表存退休名单（4KB 上限、与 revision 分家）；重派生后立即删旧 revision（INACTIVE 不能再起新 task、detached run 会断）；把基底 registry 的运行时拉取特性当选型依据（运行时只拉自己 ECR）。

**部署 provider (deploy provider)**:
（ADR 0037 决策 6，已落地。）`gherkai deploy` / `gherkai destroy` 是 provider 中立的命令面：CLI 皮只经 entry point group `gherkai.deploy` **发现**已装的 provider 包、把它的 flag 贴到子命令上、按动作分派——皮零 IaC 知识、不 import `aws_cdk`/boto3。当前唯一 provider = `gherkai-deploy-aws`（`gherkai_deploy_aws.cli:Provider`，经 CLI extra `[deploy-aws]` 装、只有部署方需要）：收编了 CDK stack 与 Lambda handler 源，命令拼 context、在临时工作目录生成 `cdk.json`、调 cdk CLI；`--vpc` 三档必给（运行期校验，`--bootstrap` 除外）并随 stack 写 SSM 供**三态比对**，版本戳同为 stack 资源。区分：**「部署方」**装 `[deploy-aws]` 跑 deploy；**「提交方」**只装 `gherkai` 跑 run/submit，两者靠 SSM 版本戳做 skew 比对（见下「版本单旋钮」）。

**版本单旋钮 (single version knob)**:
（ADR 0037 决策 7；**git tag 真源 + 兄弟包 `==` lockstep pin 已落地**——五个 Python 包均 dynamic version、由 `uv-dynamic-versioning` 从 git tag 派生，pyproject 里零手写版本号；skew 三态已落地——`compose.check_backend_skew`，run/submit/status 的 cloud 路径先于资源 preflight；`gherkai deploy` 写 SSM 版本戳已落地。）一个 git tag `vX.Y.Z` 派生全部交付物的版本：五个 Python 包（`==` lockstep）、npm 包、基底镜像 tag、定制镜像 tag 的版本前缀、部署 stack 的 SSM 版本戳（stack 资源、与部署事务同生死）、GitHub Release。不做兼容矩阵，替代物 = preflight skew **三态**检查（戳缺失 = 0037 前部署 → 警告不拦；CLI 新于后端 → 退 2、不设放行口（临时用 `uvx --from 'gherkai==<后端版本>'` 跑同版本 CLI）；旧于 → 警告；非纯净版本跳过——靠 `uv-dynamic-versioning` 的 `dirty=true` + metadata 默认行为保证非纯净构建必带 `+`；metadata **不**显式开——开了干净 tag 也带 `+sha`、发布 gate 必败），其后 preflight 再按本 run 引擎解析 worker variant（ADR 0038）。操作规则 = **升级即三步**：`uv tool upgrade gherkai` → 立刻 `gherkai deploy`（新模板、同步新版本 `base`、重派生）→ 有自定义 variant 的团队从新基底重 build 并 `push-worker`（默认指针不重置、推上去即恢复）；非部署者等部署者做完再升（ADR 0037 决策 7）。
_Avoid_: 在 pyproject/package.json 手写版本号（双真源）；为 CLI↔后端↔镜像维护兼容矩阵；把 Prefect 的「先升 server 再升 client」直译过来（本架构后端由 CLI 的 `[deploy-aws]` 部署、同版本钉死，做不到反序）；升级只升 CLI 不 deploy 不重推 variant（preflight 会拦，别绕）。
