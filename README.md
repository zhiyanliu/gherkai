# Gherkin × (Midscene + Nova Act) × AgentCore Browser

一套 UI 自动化测试框架原型：用 **Gherkin** 描述测试意图，由两个互相独立的 **AI 引擎**（Midscene / Nova Act）执行，由 **AWS Bedrock AgentCore** 云端浏览器承载。三层正交，靠 CDP（Chrome DevTools Protocol）串联。

> 术语与设计决策见 [`CONTEXT.md`](./CONTEXT.md) 和 [`docs/adr/`](./docs/adr/)，外部一手来源见 [`docs/REFERENCES.md`](./docs/REFERENCES.md)。（初始蓝图 `midscene-novaact-prototype-guide.md` 已退役——其内容被 CONTEXT+ADR 全面覆盖且经实测更正。）

## 现状（v1.0，已端到端验证）

架构：**核心库 `core/`（Python）自解析 Gherkin → 分组 scope/job → 调度**，每个 scope spawn 一个**薄 worker 子进程**（Midscene=TS / Nova Act=Python），worker 讲统一的 worker↔core 协议（ADR 0024）。`cli/` 是核心库的第一个前端（组合根）。已**退役** v0.x 的 cucumber-js/pytest-bdd 双 runner 直跑（见 ADR 0016 执行架构 / 0022 BDD runner 退役 / 0023 核心语言）。

三层链路 + v1.0 核心库均已在真实 AWS 账号端到端验证：

| 能力       | 内容                                                                                                    | 状态                                                            |
|------------|---------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| 双引擎执行 | 同一份 `.feature` → 两个引擎薄 worker（cli 经 `@engine` tag 路由）                                        | ✅ 端到端真跑                                                    |
| 云端浏览器 | 两个引擎都接 AgentCore Browser（各自一个会话，CDP 驱动）                                                   | ✅                                                               |
| 核心库     | parse + scope 分组 + schedule 调度 + 4 ports（Engine/Run/Result/ReportStore）+ 实时写编排（RunPersistence） | ✅ 单测覆盖                                                      |
| 云端 store | 状态落 DynamoDB、判定结果与报告落 S3（+ StepArgument offload 解 DDB 400KB 限），boto3 走可选 `core[aws]`    | ✅ 已接 cli（`--backend cloud`）、真 AWS 端到端；moto 单测对拍 local |
| 投票治理   | AI 断言可配 N 次取多数票（`--assertion-votes`，治抖动）                                                    | ✅                                                               |
| RunReport  | 跨引擎归集索引（manifest + index，不融合产物）                                                             | ✅                                                               |
| 网络韧性   | 建连两层重试 + network_error 分类 + SIGTERM 会话泄漏根治                                                | ✅                                                               |

> **承接 v0.x 顺延项（待真实业务系统）**：≥3 真实用例 QA 零代码验收 + 破例清单——当前用骨架用例（wikipedia/example.com）验证方向，真实系统验收顺延。

> **v1.1 云端**：云端 store adapter（DynamoDB/S3）+ **执行面 Fargate/ECS 均已建成 + 真部署真跑**——`--backend cloud` 一个旋钮同时切「存储上云 + worker 跑 Fargate 容器」（`FargateEngine` adapter + `iac_aws_backend` CDK 工程，ADR 0032/0033）。配置与退出码分层见 [`cli/README.md`](./cli/README.md)。

> **v1.2 无状态跑批**（已实装，ADR 0034）：`submit` 提交完就走、返回 run_id，`status [--wait]` 轮询/接力收集——CLI 不必守着 run。local 档起 per-run 后台进程（setsid 脱离 CLI）+ SQLite events 推进；cloud 档三 Lambda 事件驱动链（kicker 冷启动 / reconciler 主推进 / 退出观察者）由 DDB Stream + EventBridge 驱动，submit 机器权限收窄到「提交那一下」。同步 `run` 命令保留不变。每个 job 有墙钟预算兜底（缺省 300s，`@timeout:` tag 按用例声明）——三路推进器统一 enforce，提交完就走也不怕挂死/无限烧钱。

> **v1.3 本地应用测试**（已实装，ADR 0035）：`--expose-local http://localhost:3000`（run/submit 均可）把「跑 CLI 的机器可达」的被测应用经 **ngrok 隧道**暴露给云端浏览器——本地开发中的应用不必发布即可被测。feature 里照写原始地址，框架提交时替换为公网 URL；basic-auth 默认开启（随机凭据每 run 一换、终态即拆、边缘拦截）。四种「跑法×backend」组合全支持（cloud submit 由本机守护进程持有隧道，需保持开机到 run 终态）。**同版还含确定性能力暴露**（ADR 0036）：`list-deterministic` 按引擎列出可复用的确定性 step（worker 注册表自述，零漂移），`plan` 对每个 step 标注派发预期（命中确定性/走 AI，含冲突预检）——写 feature 的人不再对引擎侧能力两眼一抹黑。

## 架构速览

```mermaid
flowchart TD
    F["① 用例层<br/>features/*.feature —— 共享 Gherkin（ADR 0005）"]

    subgraph L2["② 产品层"]
        CLI["cli/ —— run / submit / status / plan /<br/>list-engines / list-deterministic<br/>命令行皮（Lambda / 未来 WebUI 是另两张皮）"]
        G["gherkai/ —— 产品本体 = 组合根<br/>引擎注册表与装配 · 资源命名真源 · <br/>隧道口子（ADR 0016「演进」节 / 0035）"]
        C["core/（Python）—— parse → scope 分组 → schedule 调度<br/>窄腰，零引擎依赖（ADR 0016）"]
        CLI --> G --> C
    end

    subgraph L3["③ 执行层 —— 两个独立 AI 引擎，平级"]
        M["Midscene worker（TS）<br/>大脑：Qwen3-VL@Bedrock<br/>鉴权：SigV4 自签"]
        N["Nova Act worker（Python）<br/>大脑：nova-act-latest<br/>鉴权：IAM @workflow"]
    end

    B["④ 浏览器层<br/>AgentCore Browser（aws.browser.v1，每引擎各一个会话）"]

    APP["⑤ 被测应用<br/>公网站点；或本机/内网应用经 ngrok 隧道（--expose-local，ADR 0035）"]

    F --> CLI
    C -- "对每个 scope spawn 薄 worker<br/>讲 worker↔core 协议（ADR 0024）" --> M
    C -- " 同一协议 " --> N
    M -- CDP --> B
    N -- CDP --> B
    B -- " 公网直达 " --> APP
    B -. "ngrok 隧道回本机<br/>（--expose-local）" .-> APP
```

关键约束：**全栈托管在 AWS 内**（ADR 0009）；**范围限英文 UI**（ADR 0001）。

## 目录结构

```
./
├── README.md                  ← 本文件
├── CONTEXT.md                 ← 领域术语表（glossary）
├── CLAUDE.md                  ← 项目约定（沟通/文档纪律/代码纪律/工作方式）——给 AI coding agent 与人
├── docs/                      ← 架构决策与过程记录
│   ├── adr/                   ← 架构决策记录（0001–0034）
│   ├── journey/               ← 任务推进 staging 区（过程产物，吸收进 ADR/code 后可清，见 CLAUDE.md）
│   ├── REFERENCES.md          ← 外部一手来源
│   └── {doc,code}-health-review.md  ← 文档/代码健康度复盘方法
├── features/                  ← 共享 .feature（同一份两个引擎同读；通用 step 风格，QA 零代码）
│   ├── wikipedia_generic.feature / wikipedia_assertions.feature / wikipedia_robustness.feature
│   ├── engine_routing.feature              ← @engine tag 路由验证
│   ├── deterministic_anchor.feature        ← @deterministic 锚点验证（ADR 0022）
│   └── concurrency_and_scope.feature       ← 手工真跑回归夹具：改调度/会话生命周期后重跑验 ADR 0019
├── core/                      ← 窄腰核心库（Python，零引擎依赖，ADR 0016）
│   └── core/{parse,scope,schedule,project,reconcile,persist,model,wire,serialize,ports,errors}.py（project=纯归约投影 / reconcile=无状态推进编排，ADR 0034）+ adapters/{subprocess,fargate}_engine.py + cloud_launcher.py + event_log/{sqlite,ddb}.py（无状态跑批持久事件通道，ADR 0034）+ adapters/{run,result,report}_store/{local,ddb|s3}.py
├── gherkai/                   ← 产品本体 = 组合根共享层（ADR 0016「演进」节；cli/Lambda/WebUI 的共同地基）
│   └── gherkai/{compose.py(引擎注册表/装配) · detached.py(local 无状态跑批宿主) · names.py(资源命名真源)}
├── cli/                       ← 命令行皮（ADR 0016）
│   └── cli/{__main__.py(argparse) · render.py}
├── engines/                   ← 两个可插拔引擎，与 core 平级
│   ├── midscene/   ← TS 子工程：worker/run-scope.ts（薄 worker）· worker/deterministic.ts · lib/agentcore-sigv4.mts · spikes/
│   └── novaact/    ← Python 子工程：worker/run_scope.py（薄 worker）· worker/deterministic.py · lib/workflow_setup.py · spikes/
├── iac_aws_backend/           ← `--backend cloud` 的 AWS 资源 IaC（Python CDK：DDB/S3/ECS/ECR/IAM/VPC + 无状态跑批的 Stream/Lambda/EventBridge，ADR 0033/0034）
├── lambdas/                   ← cloud 无状态跑批的三 Lambda 源（kicker/reconciler/exit-observer，ADR 0034；由 iac 打包部署）
└── tools/                     ← 复用工具库（端到端真跑 / 跨真实边界验证 / 时序诊断；长期资产，见 CLAUDE.md「工作方式」）
```

## 前置要求

- AWS 凭证（默认 profile 即可），region **us-east-1**，需具备：
  - Bedrock 模型访问：`qwen.qwen3-vl-235b-a22b`（Midscene 大脑）
  - AgentCore Browser（`bedrock-agentcore` 服务）
  - Nova Act 服务（`nova-act`）+ 模型 `nova-act-latest`
- Nova Act workflow definition（IAM 路径必需）：**代码会自动 create-if-not-exists**（`engines/novaact/lib/workflow_setup.py`），无需手动操作。若想手动预建也可：`aws nova-act create-workflow-definition --region us-east-1 --name spike-wikipedia-benchmark`（见 ADR 0004）。
- Node 22（midscene）、Python 3.13 + uv（novaact）
- （可选，仅 `--expose-local` 本地应用测试需要）[ngrok](https://ngrok.com/download) + authtoken（**注册免费账号即够**，付费账号亦可；`ngrok config add-authtoken <token>`——注意是 dashboard 上的 **Authtoken**，不是 `cr_` 开头的 API key）

## 运行（经核心库 cli，一个入口跑两个引擎）

```bash
# 首次安装：三个运行环境（互相隔离、不污染全局，见下「注意」）
cd cli && uv sync                                  # cli + core（core 作 path 依赖）
(cd ../engines/novaact && uv sync)                 # Nova Act worker 的 .venv（Python 3.13）
(cd ../engines/midscene && npm install)            # Midscene worker 的 node_modules（Node 22）
```

跑法由**两个正交旋钮**组合出来（四种组合都合法），按需各选一档：

- **怎么跑**——前台 `run`（CLI 在线守着，跑完直接给结果）或后台 `submit` + `status`（提交即走，事后查/收）。
- **跑在哪 / 落在哪**（`--backend`）——`local`（默认：worker 跑本机子进程，结果落本地 `reports/`）或 `cloud`（worker 跑 Fargate 容器，状态落 DynamoDB、结果落 S3；需先部署 [`iac_aws_backend`](./iac_aws_backend/README.md)，一条 `cdk deploy` 建齐全部资源）。

### ① 先预检（纯本地、不烧钱）

```bash
uv run python -m cli plan ../features/engine_routing.feature   # 看 scope/job 分组、engine 路由、校验配置；
                                                               # 每个 step 还标注派发预期：命中确定性锚点的标
                                                               # 「← 确定性: <说明>」，纯自然语言步走 AI（不标）
uv run python -m cli list-engines                              # 列可用引擎
uv run python -m cli list-deterministic --engine midscene      # 列该引擎支持的确定性 step（--json 可选，ADR 0036）
```

`list-deterministic` 输出示例（写 feature 时查询可复用的精确断言，照 `示例` 一行抄进 feature 即可）：

```
引擎 midscene 的确定性 step（1 条；test engineer 在 worker 注册表维护，ADR 0022/0036）：
  - 断言当前页面 URL 匹配给定正则（精确判定，不走 AI、不投票）
    示例: Then 页面地址匹配 "/wiki/OpenAI"
    模式: 页面地址(?:精确)?匹配 "(?<pattern>[^"]+)"
```

**先 `plan` 后跑**——真跑烧钱（模型调用 + AgentCore 会话），plan 是纯本地预检。

### ② 前台跑：`run`

```bash
# engine 由 @engine tag 选、未标用 --default-engine
AWS_REGION=us-east-1 uv run python -m cli run ../features/engine_routing.feature
# 调高投票治抖动 / 放开并发 / JSON 输出：
AWS_REGION=us-east-1 uv run python -m cli run ../features/wikipedia_generic.feature \
  --default-engine midscene --assertion-votes 3 --max-concurrency 2 --json
```

默认（local）落盘到 `cli/reports/<run_id>/`：判定真值（`jobs/`）+ 控制面（`run_meta.json`/`run_state.json`）+ RunReport（`index.html` 人看入口 + `manifest.json`）。**边跑边写**：run 开始即落 definition + 初始态，每个 scope 起跑刷 RUNNING、完成即落判定，最后 finalize 总状态。

加 `--backend cloud` 即同一条命令换云端档：worker 改跑 Fargate 容器、状态落 DynamoDB、判定真值与报告落 S3（`--prefix` 与 `cdk deploy` 时一致即可，表/桶/cluster 名由它批量推导）：

```bash
AWS_REGION=us-east-1 uv run python -m cli run ../features/engine_routing.feature \
  --backend cloud --prefix gherkai-
```

### ③ 后台跑批：`submit` + `status`（提交即走；内部称「无状态跑批」，ADR 0034）

`run` 要求 CLI 全程在线（断网/关终端即中止）。`submit` 提交完立即返回 run_id、推进在别处发生，事后用 `status` 查进度/收结果：

```bash
# local 档：本机 fork 一个脱离 CLI 的后台进程推进——不必守着终端，但本机需保持开机
RUN_ID=$(uv run python -m cli submit ../features/wikipedia_generic.feature)
uv run python -m cli status "$RUN_ID"            # 查一眼进度（只读、不推进）
uv run python -m cli status "$RUN_ID" --wait     # 等到终态、按判定给退出码——CI 要 0/1 判定用这个

# cloud 档：definition 落 DynamoDB 即返回，之后由云端 Lambda 事件驱动链推进——提交完关机也跑完
RUN_ID=$(uv run python -m cli submit ../features/wikipedia_generic.feature --backend cloud --prefix gherkai-)
uv run python -m cli status "$RUN_ID" --backend cloud --prefix gherkai- --wait
```

提交完就走不等于失控：每个 job 有墙钟预算兜底（缺省 300s；`@timeout:<秒>` tag 按用例声明、`--default-job-timeout` 改缺省）——卡死/超预算的 job 会被自动停掉并判 `error(timeout)`，local 挂死、cloud 无限烧钱都由它止损。`status` 的 `--backend`/`--report-dir`/`--prefix` 须与 `submit` 时一致（否则查不到）。选项全表、退出码分层、submit/status 语义细节见 [`cli/README.md`](./cli/README.md)。

### ④ 测本地/内网应用：`--expose-local`

被测应用跑在本机（或 CLI 机器可达的内网机器）、没有公网入口？加一个 flag 即可——框架自动起 ngrok 隧道暴露给云端浏览器，feature 里照写原始地址：

```bash
# feature 里写的是 http://localhost:3000（原始地址，plan 也显示它）；
# 框架起隧道后在提交时替换为公网 URL（带每 run 一换的 basic-auth 凭据、终态即拆）
uv run python -m cli run my_app.feature --expose-local http://localhost:3000
RUN_ID=$(uv run python -m cli submit my_app.feature --expose-local http://localhost:3000)
```

前置：装 ngrok + 配 authtoken（见上「前置要求」）。`submit` 后隧道由后台进程持有（cloud 档为守护进程）——**本机需保持开机联网直到 run 终态**。设计与边界见 ADR 0035。

两个引擎读的是**同一份** `features/` 下 `.feature`（通用 step 风格，QA 只写自然语言）。

### 怎么写 `.feature`（QA 零代码，ADR 0020）

- 动作/断言都写**纯自然语言、无路由关键词**：`When "搜索 OpenAI"` / `Then "进入了 OpenAI 词条页"` → 默认走 AI（动作=aiAct/act；断言=aiBoolean/act_get+投票）。
- scope/引擎用 **tag**（ADR 0019）：`@scope:login`（共享会话、串行）/ `@engine:midscene|novaact`（选引擎）。
- **确定性精确检查**（URL/DOM，不容 AI 抖动）：由 test engineer 在 worker 的 `@deterministic` 注册表按需写（`deterministic.steps.ts` / `deterministic_steps.py`；命中走精确 handler、不投票，ADR 0022）（QA 不碰实现，但**可发现可复用**：`list-deterministic` 查当前引擎有哪些、`plan` 看自己写的 step 会不会命中，ADR 0036）。
- **多行参数**：AI 动作/断言 step 可挂 Gherkin DataTable/DocString，worker 拼成附加文本随 step 一起喂 AI（ADR 0024）。

## Spike（可独立跑的技术验证脚本）

```bash
# Midscene 引擎三段隔离自检（模型连接 / 浏览器连接(CDP) / 合体；另有 04 planning 探针 / 05 负向断言，见 engines/midscene/README.md）
cd engines/midscene && AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/01-model-sigv4.ts
# 02-agentcore-cdp.ts / 03-midscene-grounding.ts 同理

# Nova Act 引擎对标 spike
cd engines/novaact && AWS_REGION=us-east-1 .venv/bin/python spikes/wikipedia_benchmark.py
```

## 注意

- 运行会真实消耗 AWS 费用（模型调用 + AgentCore 会话）。
- 环境隔离：TS 依赖在 `engines/midscene/node_modules`，Python 依赖在 `engines/novaact/.venv`，均不污染全局。
