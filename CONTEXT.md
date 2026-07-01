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
把屏幕截图解析成可点击坐标的能力，是 Midscene 主力大脑的核心职责。英文 UI、小字、非拉丁文字会显著影响其质量。
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
- Nova Act（Python）→ `engines/novaact/spikes/`，用 `engines/novaact/.venv`。
不设 git 根级 `spikes/`，spike 紧贴各自引擎子工程。**引擎内**复用的代码（如 Midscene 的 SigV4，仅 Midscene 的 spike 与 bdd 共用）抽到该引擎的 `lib/`（见 `engines/midscene/lib/agentcore-sigv4.mts`）；这不是跨引擎共享——SigV4 是 Midscene 专属，Nova Act 走 IAM/Workflow 不碰它。跨引擎真正共享的是 `features/`（用例），见 [跨引擎共享边界](./docs/adr/0013-cross-engine-sharing-boundary.md)（ADR 0013）。
_Avoid_: 把某一引擎专属的 spike/文档/代码放到根级或另一引擎目录下；也别误以为引擎内的 `lib/` 是两个引擎共享。

**确定性断言 vs AI 断言 (Deterministic vs AI assertion)**:
确定性断言用底层 Playwright（`nova.page` / Midscene 的 page）判定，结果可复现；AI 断言用自然语言（`act_get` / `aiAssert`）判定，贴合卖点但非确定性、且每次消耗模型调用。**已定（ADR 0014）：AI 断言为默认主力**（忠于框架卖点），确定性断言退为高保真补充与逃生舱；代价是非确定性，须配套抖动治理（重试/投票/度量）。抖动治理的具体参数与"哪些判定强制走确定性"靠更难用例的数据迭代。
_Avoid_: 把 AI 断言当成"无需治理就可信"——它为主，但必须配抖动监控。

**报告产物模型 (Report artifact model)**:
两个引擎的报告形态根本不同：**Midscene 出单一 `report.html`**（含每步截图+AI 决策+坐标，= scope 级）；**Nova Act 出多个分散的 trajectory HTML**（每次 `act`/`act_get` 一个，= act 级）。worker 经 0024 协议把产物**指针**报回 core（`reportRefs.ref`，core 内类型 `ResourceUri`＝带 scheme 的统一资源指针：本地 `file://`、未来云端 `s3://`/`https://`，故非裸本地路径；字段形状见 ADR 0024），core **不透明搬运**（不 stat/不 fetch/不打开 ref）。同一 `ResourceUri` 也是 `ReportStore.write` 的返回类型（统一"资源指针"概念，ADR 0027）。**RunReport（ADR 0027）= 跨引擎归集索引**：`ReportStore` 把 `RunResult` 归集成 `manifest.json`（机器可读）+ `index.html`（人可导航入口），**不解析/不融合原生产物内容**，只索引/链接（cli 每次 run **默认生成**，`--no-report` 跳过、`--materialize` 拷成自包含目录）。新引擎报任意 `kind` 零改 core（永不按 kind 分支）。
_Avoid_: 笼统说「两个引擎都出报告」而忽略其形态/落点/粒度（scope vs act）的根本不同；把 RunReport 当成「解析两个引擎 html 融合成一个大报告」（它只归集索引、不碰产物内容）；以为 core 会按 `kind`/引擎分支处理产物（永不——扩展性契约，ADR 0027）。

## 产品形态（v1.0）

**通用 step (Generic step)**:
极少数**抽象原语**：URL 导航（确定性，含引号内 URL）/ AI 动作（When）/ AI 布尔断言（Then，+投票）/ 确定性锚点（脚手架）。任何用例复用，QA 不写代码——场景细节放进引号里的自然语言，不放进 step 措辞。这是"QA 只写 `.feature`、零代码"承诺的唯一载体，**其能力边界 = 产品能力边界**。两个引擎对称实现（函数签名见 ADR 0018/0020）。**「取数/取串」等原语已删**（ADR 0018：避免过度设计，QA 直接写自然语言让 AI 判，需精确数值走确定性锚点）。AI 动作/断言 step 可挂 **Gherkin DataTable/DocString 多行参数**（一次填多字段表单、粘一大段文本）——worker 拼成附加文本（dataTable→markdown 表格、docString 原样）随 step 自然语言一起喂 AI（确定性/URL 导航路径不接），两个引擎对称（ADR 0024）。
_Avoid_: 写绑死具体场景的 step（如"语言版本数量"）——那不是通用 step；把它当成"任意动作都能稳跑"——开放性动作会引入页面瞬态 flaky（ADR 0018）。

**柔性冒烟 (Flexible smoke)**:
v1.0 的核心定位（ADR 0015）——只验证业务**意图是否达成**（流程能否走通），对达成路径上未被点名的视觉/文案/布局变化高度宽容。AI 柔性是差异化核心，与"精确回归（任何差异都报警）"本质对立。
_Avoid_: 把它当精确/像素级回归工具用。

**点名检查 (Explicit check) vs 确定性锚点 (Deterministic anchor)**:
两个不同层（ADR 0020）：
- **点名检查**：QA 想精确核对某项时，直接写**纯自然语言** `Then "价格是 ¥99"`——仍走**默认 AI 判断**（QA 零代码、无路由关键词）。「能否抓某类变更」取决于 QA 点没点名，不是做不到。
- **确定性锚点**：少数"不容 AI 抖动"的精确检查（URL/DOM），由 **test engineer** 在 `deterministic.steps` 脚手架里写 Playwright 查询，不走 AI、不预置（QA 不碰）。
_Avoid_: 以为"不点名也能抓变更"；把它与 A/B 两种不确定性混为一谈；以为 QA 要学特殊措辞（QA 永远只写自然语言）。

**两种不确定性 (A: flakiness / B: 柔性吞变更)**:
A = 同一页面 AI 判断飘忽（随机噪声）→ **投票可治**；B = 页面真变了但 AI 柔性照样跑过、不报警（灵敏度不足）→ **投票治不了**，v1.0 接受为已知边界（ADR 0015）。
_Avoid_: 以为"投票能带来确定性"——它只压 A，给不了对变更的灵敏度（B）。

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
真正的窄腰是**执行核心库**（解析 `.feature` → 分组 scope → 调度 → 收集结果），**不是 CLI**（早先措辞修正，见 ADR 0016）。CLI 是核心库的第一个、最薄的前端；WebUI 是另一个前端，**直接调核心、不 shell-out CLI**。CI/skill 通过 CLI 这个皮间接用核心。上层前端与可替换的执行引擎（`Engine` port，本地进程 / Fargate；见下「执行引擎 port」条）都围绕核心库解耦。
_Avoid_: 把逻辑焊死在 CLI `main()` 里；以为"WebUI 要包 CLI"；把"选哪个执行引擎（`Engine`）"当成一锤定终身。
（版本演进 spike→v0.x→v1.0→v1.x→v2.0 见 ADR 0016。）

**执行引擎 port (Engine port)**:
核心库之下真正跑一个 scope 的地方，是一个 **port**（`Engine`，对齐「引擎」术语，ADR 0016），由组合根注入。v1.0 实装为**单个参数化 `SubprocessEngine`**（`cmd`/`cwd`/`env` 参数化即可 spawn Node 或 Python worker——两个引擎"spawn 子进程 + 讲同一套 0024 协议"形状本就一致，无需两个具名 adapter 类；经 `EngineResolver` 按 `job.engine` 选）。演进：v1.0 本地进程（浏览器仍在云端 AgentCore Browser）→ 云端倾向 Fargate/ECS（批处理 shape-fit，ADR 0017；非 AgentCore Runtime）。
_Avoid_: 混淆"浏览器在云端"（spike 已验证）与"执行进程也在云端"（>v1.0）；把它当成"核心 import 引擎"——核心永不 import 引擎，只 spawn worker。

**两个引擎都子进程 + 薄 worker (Both-legs-subprocess + thin worker)**:
两引擎语言锁死（Midscene 锁 TS、Nova Act acting 锁 Python，ADR 0023 证伪了全 TS 核心），故核心（Python）**对每个 scope spawn 一个 worker 子进程**——两个引擎对称、核心零引擎依赖。worker = 被 spawn 的进程，一生 = 开 AgentCore 会话 → 按 scope 串行跑 scenarios（每 step 派发成 act/assert）→ 回 JSON → 退出（一次调用 = 一个 job = 一个 scope）。**核心自解析 Gherkin**（单一事实源），worker 只派发不解析——故 cucumber 补丁与 pytest-bdd 路由 hack 退役（ADR 0022）。
_Avoid_: 以为子进程里跑整个 BDD runner（那是被否的 B2）；把 worker（运行时角色）与 engine（领域概念/目录名）混用。

**确定性 step 注册表 (Deterministic step registry)**:
test engineer 扩展确定性锚点的落点：在对应 worker 里登记 `(模式 → handler)`（`@deterministic`）。核心发原始 step 文本，worker 先查注册表命中走精确 handler、未命中落 catch-all 走 AI。匹配放 worker（确定性 handler 引擎特定，碰 Playwright/CDP），核心对 step 语义无知。延续 ADR 0020 角色边界（QA 永不碰）。
_Avoid_: 把匹配放进核心（核心只解析结构+调度，不懂 step 语义）；以为 QA 要写确定性 step。

**Ports 层 (Ports & adapters)**:
核心库把可替换的外部依赖收成独立 port，导出稳定接口；核心只依赖接口。四个 port（ADR 0016）：`Engine`（跑 scope）、`RunStore`（**控制面**：run 的 definition(RunMeta) + 运行态(RunState：status/血缘/起止)，频繁读写、撑轮询续跑——DDB 主要服务它）、`ResultStore`（**数据面**：每 job(=scope) 判定真值/投票，追加为主——判定真值唯一权威）、`ReportStore`（把 `RunResult` 归集成 RunReport=manifest+index 的派生只读导航视图，ADR 0027）。`RunStore` 从原 `ResultStore` 拆出（控制面 vs 数据面访问模式不同）。**具体 adapter 由组合根（CLI main / WebUI bootstrap）注入**，不由 module 内部 env-sniff 自选（后者是本项目踩过的 Midscene `GlobalConfigManager` 反模式）。**当前实装**：四个 port 的 local adapter 均已建（见 `core/core/adapters/`，落盘形状以代码/ADR 0016 为准），cli 跑完落 `<report-dir>/<run_id>/`；只持久化已成形模型，**未发明 ADR 有意 defer 的字段**（jobId/起止/续跑读取面待真实需求逼出）。**云端 store adapter（RunStore→DynamoDB、Result/ReportStore→S3，+ StepArgument offload 解 DDB 400KB 限）已建**——行为对拍 local、moto 全程 mock 单测、boto3 走可选依赖 `core[aws]`（ADR 0030 决定六）；组合根按 backend 注入哪套（cli `--backend` 接线是独立分片）。**执行面 Fargate/ECS 仍待建**（ADR 0017 倾向）。
_Avoid_: 把多个 port 揉成一个上帝 module；让 port-module 用全局单例自选实现；混淆控制面（RunStore）与数据面（ResultStore）。
