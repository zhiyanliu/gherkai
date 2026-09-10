# 开发者指南（contributor 入口）

> 使用者看 [`README.md`](./README.md)（仓库首页）与各发行包页面；本文给 contributor：目录结构、开发环境、测试、spike、发布，以及去哪找设计决策。项目约定（沟通/文档纪律/代码纪律/工作方式）在 [`CLAUDE.md`](./CLAUDE.md)，术语在 [`CONTEXT.md`](./CONTEXT.md)。

## 现状与版本线

架构：**核心库 `core/`（Python）自解析 Gherkin → 分组 scope/job → 调度**，每个 scope spawn 一个**薄 worker 子进程**（Midscene=TS / Nova Act=Python），worker 讲统一的 worker↔core 协议（ADR 0024）。`cli/` 是核心库的第一张前端皮（argparse + render），组合根共享层在 `runtime/`（ADR 0016「演进」节）。v0.x 的 cucumber-js/pytest-bdd 双 runner 直跑已**退役**（ADR 0016 / 0022 / 0023）。关键约束：**全栈托管在 AWS 内**（ADR 0009）；**UI 语言支持范围按引擎划分**——Midscene 不限、Nova Act 限英文（ADR 0001）。

| 版本线 | 内容 | 状态 |
|---|---|---|
| v1.0 核心库 | parse + scope 分组 + schedule + 4 ports（Engine/Run/Result/ReportStore）+ 实时写编排；双引擎薄 worker、AgentCore 会话、投票治理、RunReport、网络韧性 | ✅ 真 AWS 端到端 |
| v1.1 云端 | store adapter（DynamoDB/S3，StepArgument offload 解 400KB 限）+ Fargate/ECS 执行面（`FargateEngine` + `gherkai-deploy-aws` 的 CDK stack）；boto3 只在云端路径懒加载（库层 extra `[aws]`，CLI 硬依赖 `gherkai-runtime[aws]`，ADR 0032/0033/0037） | ✅ 真部署真跑 |
| v1.2 无状态跑批 | `submit` 即走 + `status [--wait]`；local 档 per-run 后台进程 + SQLite events；cloud 档三 Lambda 事件驱动链（kicker / reconciler / exit-observer，DDB Stream + EventBridge）；job 墙钟预算兜底（ADR 0034） | ✅ |
| v1.3 本地应用测试 + 能力自述 | `--expose-local` ngrok 隧道（basic-auth 每 run 一换、终态即拆，ADR 0035）；`list-deterministic` / `plan` 派发标注（worker 注册表自述，ADR 0036） | ✅ |
| v1.4 分发与打包 | uv workspace 五包 + PyPI/npm 发行、git tag 版本单旋钮、`gherkai deploy` 内嵌 IaC、worker 镜像 variant 交付（ADR 0037 / 0038） | ✅ v1.4.0 已首发 |

承接 v0.x 顺延项（待真实业务系统）：≥3 真实用例 QA 零代码验收 + 破例清单——当前用骨架用例（wikipedia/example.com）验证方向。

## 目录结构

```
./
├── README.md                  ← 仓库首页（使用者向）；DEVELOPMENT.md ← 本文（contributor 向）
├── CONTEXT.md                 ← 领域术语表（glossary）
├── CLAUDE.md                  ← 项目约定（沟通/文档纪律/代码纪律/工作方式）——给 AI coding agent 与人
├── pyproject.toml / uv.lock   ← uv workspace 根（成员 = core / runtime / cli / engines/novaact / deploy_aws 五个发行包）：单一 lock + 共用 dev 依赖与 pytest 配置（ADR 0037）
├── .github/                   ← CI 与发布链（workflows/{ci,release}.yml + scripts/；一次性人工前置与本地校验见 .github/workflows/README.md，ADR 0037 决策 8）
├── .claude/commands/          ← Claude Code 项目命令：/doc-health-review、/code-health-review 两条复盘入口（.claude/ 其余为个人配置、不入库）
├── docs/                      ← 架构决策与过程记录
│   ├── adr/                   ← 架构决策记录（0001–0042）
│   ├── guides/                ← 给人的阅读理解文档（机制解读/横切合成等，只讲 how、权威在 ADR）
│   ├── journey/               ← 任务推进的 staging 区（过程产物，吸收进 ADR/code 后即删，见 CLAUDE.md「文档纪律」；可为空）
│   ├── REFERENCES.md          ← 外部一手来源
│   └── {doc,code}-health-review.md  ← 文档/代码健康度复盘方法
├── features/                  ← 共享 .feature（同一份两个引擎同读；通用 step 风格，QA 零代码）
│   ├── wikipedia_generic.feature / wikipedia_assertions.feature / wikipedia_robustness.feature
│   ├── wikipedia_zh.feature                ← 非英文 UI 探针：中文维基 + 中文 step，两引擎同题（ADR 0001 的测量夹具与重议复测入口）
│   ├── engine_routing.feature              ← @engine tag 路由验证
│   ├── deterministic_anchor.feature        ← @deterministic 锚点验证（ADR 0022）
│   └── concurrency_and_scope.feature       ← 手工真跑回归夹具：改调度/会话生命周期后重跑验 ADR 0019
├── core/                      ← 窄腰核心库（发行名 gherkai-core，Python，零引擎依赖，ADR 0016）
│   └── gherkai_core/{parse,scope,schedule,project,reconcile,persist,model,wire,serialize,ports,errors}.py（project=纯归约投影 / reconcile=无状态推进编排，ADR 0034）+ adapters/{subprocess,fargate}_engine.py + adapters/cloud_launcher.py + adapters/event_log/{sqlite,ddb}.py + adapters/{run,result,report}_store/{local,ddb|s3}.py
├── runtime/                   ← 产品本体 = 组合根共享层（发行名 gherkai-runtime；ADR 0016「演进」节；cli/Lambda/WebUI 的共同地基）
│   └── gherkai_runtime/{compose.py(引擎注册表/装配·云目标解析) · detached.py(local 无状态跑批宿主) · names.py(资源命名真源) · tunnel.py / tunnel_host.py(--expose-local 隧道，ADR 0035)}
├── cli/                       ← 命令行皮（发行名 gherkai，命令 gherkai；ADR 0016）
│   └── gherkai_cli/{__main__.py(argparse) · deploy.py(部署 provider 发现/分派皮) · render.py}
├── engines/                   ← 两个可插拔引擎，与 core 平级
│   ├── midscene/   ← npm 包 @gherkai/worker-midscene（ESM）：src/bin.mts（入口）· src/worker/run-scope.mts（薄 worker）· src/worker/deterministic.mts · src/lib/agentcore-sigv4.mts · spikes/
│   └── novaact/    ← 发行包 gherkai-worker-novaact：gherkai_worker_novaact/{run_scope.py（薄 worker）· deterministic.py · user_steps.py · lib/workflow_setup.py} · spikes/
├── deploy_aws/                ← 发行包 gherkai-deploy-aws：`gherkai deploy` 的 AWS provider（Python CDK stack：DDB/S3/ECS/ECR/IAM/VPC + 无状态跑批的 Stream/Lambda/EventBridge；`gherkai_deploy_aws/lambdas/` 是三 Lambda 的 handler 源、随部署打进 asset；worker 镜像交付 `push-worker` / `list-workers`，ADR 0033/0034/0037/0038）
└── tools/                     ← 复用工具库（端到端真跑 / 跨真实边界验证 / 时序诊断 / 知识图刷新；长期资产，见 CLAUDE.md「工作方式」）
```

每个包目录都有两份文档：`README.md` = 发行包页面（逐字上 PyPI/npm，只写使用者内容）、`DEVELOPMENT.md` = 该包的 contributor 文档（模块布局、从 checkout 跑、测试、ADR 指针）——[`cli/`](./cli/DEVELOPMENT.md) · [`core/`](./core/DEVELOPMENT.md) · [`runtime/`](./runtime/DEVELOPMENT.md) · [`deploy_aws/`](./deploy_aws/DEVELOPMENT.md) · [`engines/novaact/`](./engines/novaact/DEVELOPMENT.md) · [`engines/midscene/`](./engines/midscene/DEVELOPMENT.md)。

## 开发环境（从 checkout 跑）

```bash
uv sync                                            # 五个 workspace 成员（core/runtime/cli + novaact worker + deploy-aws provider）一次装齐（共用根 .venv/）
(cd engines/midscene && npm ci && npm run build)   # Midscene worker（npm 包，Node ≥22）：装依赖 + 编译到 dist/
# dev 态让 CLI 用本仓库的 midscene worker（发行版用户走 `npm i -g @gherkai/worker-midscene`，不需此步）：
export GHERKAI_WORKER_MIDSCENE_CMD="node $PWD/engines/midscene/dist/bin.mjs"
```

`uv sync` 把五个成员（`gherkai-core` / `gherkai-runtime` / `gherkai` / `gherkai-worker-novaact` / `gherkai-deploy-aws`）以 editable 装进仓库根的同一个 `.venv/`（ADR 0037：单一 workspace、单一 `uv.lock`）。此后**在仓库根**敲 `uv run gherkai <子命令>`（README 里的 `gherkai …` 在仓库内都写成 `uv run gherkai …`）。

环境隔离：Python 成员与 Nova Act worker 都在仓库根 `.venv`（worker 与 CLI 同 venv 是设计——`python -m gherkai_worker_novaact` 无包装层、fd 直达，ADR 0037 决策 3），Midscene worker 的 TS 依赖在 `engines/midscene/node_modules`——均不污染全局。前置的 AWS 凭证/服务与 ngrok 见 README「前置要求」。

## 测试

```bash
uv run pytest                                    # 全部 workspace 成员的单测（根 pyproject 的 testpaths；-m 'not integration'）
(cd engines/midscene && npm test)                # Midscene worker 单测
uv run pytest core/tests -m integration          # 集成测试：假定真表/桶已预建（见 core/tests/README.md）
```

两条纯文档/文案护栏也在单测里：`cli/tests/test_user_facing_messages.py`（产品面文案不带内部指代）、`cli/tests/test_package_readmes.py`（包页面 / 根 README 使用者向、每包有 DEVELOPMENT.md）。单测绿不等于对——凡结论依赖 mock 之外的真实行为（进程/信号/并发/真 AWS），按 CLAUDE.md「绿≠对」升级验证；端到端真跑的现成工具在 `tools/`（先翻一眼、别重造）。

## Spike（可独立跑的技术验证脚本）

```bash
# Midscene 引擎三段隔离自检（模型连接 / 浏览器连接(CDP) / 合体；另有 04 planning 探针 / 05 负向断言，见 engines/midscene/DEVELOPMENT.md）
cd engines/midscene && AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/01-model-sigv4.ts
# 02-agentcore-cdp.ts / 03-midscene-grounding.ts 同理

# Nova Act 引擎对标 spike
AWS_REGION=us-east-1 uv run python engines/novaact/spikes/wikipedia_benchmark.py   # 用仓库根 .venv（novaact 无独立 venv）
```

## 知识图刷新（graphify）

`graphify-out/`（`graph.json` / `GRAPH_REPORT.md` / `wiki/`）是给 AI agent 的代码 + 文档知识图（CLAUDE.md「graphify」节让 agent 先查图再翻源码）。维护分两层：

- **AST 层自动**：`graphify hook install` 装的 post-commit hook 在每次含代码文件的 commit 后重抽代码、重聚类；不调 LLM。
- **LLM 层手动、周期性**：文档语义抽取与社区命名要 LLM（AWS Bedrock），hook 覆盖不到——改了 ADR / README / guides，或报告里社区名退化成文件名（hook 按枢纽节点起的临时名）时跑：

```bash
tools/graphify_refresh.sh            # 抽取到收敛 → LLM 命名社区 + 重生成报告 → 导出 wiki（顺序有意义，env 默认值见脚本头注释）
tools/graphify_refresh.sh --force    # 全量重抽（清残留节点时；费用按全仓文档量计）
```

需要 Bedrock 凭证，且 env 里有 `AWS_REGION` 或 `AWS_PROFILE`（脚本会回落 `aws configure get region`）。本机没凭证时到有凭证的机器上跑：rsync 工作区过去（排除 `.git` / `.venv` / `node_modules`，**带上 `graphify-out/`** 以复用增量缓存）→ 跑脚本 → rsync `graphify-out/` 回来时**排除 `.graphify_root`**（它存绝对路径，带回会让本地 hook 重建失败）→ commit `graph.json` / `GRAPH_REPORT.md` / `manifest.json` / `wiki/`（其余是缓存与滚动备份，`.gitignore` 已排除）。

## 发布与版本

**版本真源只有 git tag `vX.Y.Z`**——五个 Python 发行包、npm 包 `@gherkai/worker-midscene`、两个 worker 基底镜像同号，pyproject 与 package.json 里都没有手写版本号（ADR 0037 决策 2b/7）。发布因此是一个动作：

```bash
git tag v1.4.0 && git push origin v1.4.0   # GitHub Actions 接手：gate（版本==tag）→ PyPI → npm → GHCR 基底镜像 → GitHub Release
```

CI（push `main` / PR / 手动）跑三件：全成员 `pytest`、midscene 的 `npm ci && npm run build && npm test`、`uv build --all-packages` 的打包元数据 smoke + 发布 gate 演练。一次性人工前置（PyPI trusted publisher、npm trusted publisher、GHCR 可见性核对）、TestPyPI 演练、以及**不推 tag 也能做的本地静态校验**，全在 [`.github/workflows/README.md`](./.github/workflows/README.md)；决策与理由在 [ADR 0037 决策 8](./docs/adr/0037-distribution-and-packaging.md)。

## 文档去哪读

- 决策与理由：[`docs/adr/`](./docs/adr/)（每篇带 Status 头；Accepted 的自包含）
- 机制横切解读：[`docs/guides/`](./docs/guides/)
- 术语：[`CONTEXT.md`](./CONTEXT.md)；外部一手来源：[`docs/REFERENCES.md`](./docs/REFERENCES.md)
- 复盘方法（给 AI coding agent 执行的任务指令，不是人手工清单）：[`docs/doc-health-review.md`](./docs/doc-health-review.md)（全部文档对照 code 去漂移）/ [`docs/code-health-review.md`](./docs/code-health-review.md)（全部生产代码查死代码 / 过时 / 违背 ADR）。事件驱动：显著构建里程碑或一批 ADR 增改后跑，不定期空跑。Claude Code 里敲 `/doc-health-review`、`/code-health-review`（入口在 [`.claude/commands/`](./.claude/commands/)，只是把方法文档喂给 agent 并强调不可跳过的步骤）；其它 AI coding 工具把对应方法文档整份作为任务指令即可。客观类问题 agent 直接改，主观类出报告待批。
