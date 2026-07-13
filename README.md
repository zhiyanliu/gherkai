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

> **v1.1 云端**：云端 store adapter（DynamoDB/S3）+ **执行面 Fargate/ECS 均已建成 + 真部署真跑**——`--backend cloud` 一个旋钮同时切「存储上云 + worker 跑 Fargate 容器」（`FargateEngine` adapter + `iac_aws_backend` CDK 工程，ADR 0032/0033）。配置与退出码分层见 [`cli/README.md`](./cli/README.md)。待做：无状态跑批（提交→轮询→脱离 run，ADR 0017）。

## 架构速览

```
① 用例层   features/*.feature              ← 共享 Gherkin（ADR 0005）
              │
② 核心库   core/（Python）：parse → scope 分组 → schedule 调度   ← 窄腰，零引擎依赖（ADR 0016）
   前端    cli/（run / plan / list-engines）= 组合根，注入引擎
              │  对每个 scope spawn 一个薄 worker，讲协议（ADR 0024）
③ 执行层   Midscene worker(TS)  ┃  Nova Act worker(Python)   ← 两个独立 AI 引擎，平级
   大脑    Qwen3-VL@Bedrock     ┃  nova-act-latest
   鉴权    SigV4 自签            ┃  IAM @workflow
              │  都经 CDP 驱动
④ 浏览器层 AgentCore Browser（aws.browser.v1，每引擎各一个会话）
```

关键约束：**全栈托管在 AWS 内**（ADR 0009）；**范围限英文 UI**（ADR 0001）。

## 目录结构

```
./
├── README.md                  ← 本文件
├── CONTEXT.md                 ← 领域术语表（glossary）
├── CLAUDE.md                  ← 项目约定（沟通/文档纪律/代码纪律/工作方式）——给 AI coding agent 与人
├── docs/                      ← 架构决策与过程记录
│   ├── adr/                   ← 架构决策记录（0001–0033）
│   ├── journey/               ← 任务推进 staging 区（过程产物，吸收进 ADR/code 后可清，见 CLAUDE.md）
│   ├── REFERENCES.md          ← 外部一手来源
│   └── {doc,code}-health-review.md  ← 文档/代码健康度复盘方法
├── features/                  ← 共享 .feature（同一份两个引擎同读；通用 step 风格，QA 零代码）
│   ├── wikipedia_generic.feature / wikipedia_assertions.feature / wikipedia_robustness.feature
│   ├── engine_routing.feature              ← @engine tag 路由验证
│   ├── deterministic_anchor.feature        ← @deterministic 锚点验证（ADR 0022）
│   └── concurrency_and_scope.feature       ← 手工真跑回归夹具：改调度/会话生命周期后重跑验 ADR 0019
├── core/                      ← 窄腰核心库（Python，零引擎依赖，ADR 0016）
│   └── core/{parse,scope,schedule,persist,model,wire,serialize,ports,errors}.py + adapters/{subprocess,fargate}_engine.py（Engine：local/cloud）+ adapters/{run,result,report}_store/{local,ddb|s3}.py（本地 + 云端）
├── cli/                       ← 核心库的第一个前端 = 组合根（ADR 0016）
│   └── cli/{__main__.py(argparse) · compose.py(引擎注册表) · render.py}
├── engines/                   ← 两个可插拔引擎，与 core 平级
│   ├── midscene/   ← TS 子工程：worker/run-scope.ts（薄 worker）· worker/deterministic.ts · lib/agentcore-sigv4.mts · spikes/
│   └── novaact/    ← Python 子工程：worker/run_scope.py（薄 worker）· worker/deterministic.py · lib/workflow_setup.py · spikes/
├── iac_aws_backend/           ← `--backend cloud` 的 AWS 资源 IaC（Python CDK：DDB/S3/ECS/ECR/IAM/VPC，ADR 0033）
└── tools/                     ← 复用工具库（端到端真跑 / 跨真实边界验证 / 时序诊断；长期资产，见 CLAUDE.md「工作方式」）
```

## 前置要求

- AWS 凭证（默认 profile 即可），region **us-east-1**，需具备：
  - Bedrock 模型访问：`qwen.qwen3-vl-235b-a22b`（Midscene 大脑）
  - AgentCore Browser（`bedrock-agentcore` 服务）
  - Nova Act 服务（`nova-act`）+ 模型 `nova-act-latest`
- Nova Act workflow definition（IAM 路径必需）：**代码会自动 create-if-not-exists**（`engines/novaact/lib/workflow_setup.py`），无需手动操作。若想手动预建也可：`aws nova-act create-workflow-definition --region us-east-1 --name spike-wikipedia-benchmark`（见 ADR 0004）。
- Node 22（midscene）、Python 3.13 + uv（novaact）

## 运行（经核心库 cli，一个入口跑两个引擎）

```bash
cd cli
uv sync                                            # 装环境（core 作 path 依赖）

# ① 预检（纯本地、不烧钱）：看 .feature 分出哪些 scope/job、engine 路由对不对、校验配置
uv run python -m cli plan ../features/engine_routing.feature

# ② 真跑（会烧 AWS 钱：模型调用 + AgentCore 会话）。engine 由 @engine tag 选、未标用 --default-engine
AWS_REGION=us-east-1 uv run python -m cli run ../features/engine_routing.feature
# 调高投票治抖动 / 放开并发 / JSON 输出：
AWS_REGION=us-east-1 uv run python -m cli run ../features/wikipedia_generic.feature \
  --default-engine midscene --assertion-votes 3 --max-concurrency 2 --json

# 列可用引擎（不烧钱）
uv run python -m cli list-engines

# ③ 云端落库（可选）：状态落 DynamoDB、判定真值与报告落 S3（表/桶需预先建好）
AWS_REGION=us-east-1 uv run python -m cli run ../features/engine_routing.feature \
  --backend cloud --ddb-table <你的表> --s3-bucket <你的桶>
```

**默认 local**：落盘到 `cli/reports/<run_id>/`：判定真值（`jobs/`）+ 控制面（`run_meta.json`/`run_state.json`）+ RunReport（`index.html` 人看入口 + `manifest.json`）。
**边跑边写**：run 开始即落 definition + 初始态，每个 scope 起跑刷 RUNNING、完成即落判定，最后 finalize 总状态——可「提交即返回 runId、之后轮询看进度」。详见 [`cli/README.md`](./cli/README.md)。
**先 `plan` 后 `run`**——run 真烧钱，plan 是纯本地预检。
**`--backend cloud`**（可选）：把上面这套落到 DynamoDB（状态）+ S3（判定真值与报告）而非本地目录。表/桶需先用你的 IaC / `aws` cli 建好（框架假定已存在）；不给 `--ddb-table/--s3-bucket` 可用 `AWS_DDB_TABLE/AWS_S3_BUCKET` 兜底；凭证/region 走 boto3 默认链（可加 `--profile/--region`）。云端配置、退出码分层、建表建桶命令见 [`cli/README.md`](./cli/README.md)。

两个引擎读的是**同一份** `features/` 下 `.feature`（通用 step 风格，QA 只写自然语言）。

### 怎么写 `.feature`（QA 零代码，ADR 0020）

- 动作/断言都写**纯自然语言、无路由关键词**：`When "搜索 OpenAI"` / `Then "进入了 OpenAI 词条页"` → 默认走 AI（动作=aiAct/act；断言=aiBoolean/act_get+投票）。
- scope/引擎用 **tag**（ADR 0019）：`@scope:login`（共享会话、串行）/ `@engine:midscene|novaact`（选引擎）。
- **确定性精确检查**（URL/DOM，不容 AI 抖动）：由 test engineer 在 worker 的 `@deterministic` 注册表按需写（`deterministic.steps.ts` / `deterministic_steps.py`；命中走精确 handler、不投票，ADR 0022）（QA 不碰）。
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
