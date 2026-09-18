# 开发者指南（contributor 入口）

> 使用者看 [`README.md`](./README.md)（仓库首页）与 [`docs/user-guide/`](./docs/user-guide/README.md)；本文给 contributor：如何参与、目录结构、开发环境、测试、spike、发布，以及去哪找设计决策。项目约定（沟通/文档纪律/代码纪律/工作方式）在 [`CLAUDE.md`](./CLAUDE.md)，术语在 [`CONTEXT.md`](./CONTEXT.md)，全部文档的地图在 [`docs/README.md`](./docs/README.md)。

## 如何参与

- **提 issue**：报缺陷带能复现的最小 `.feature`、完整命令行、以及 `--json` 输出（`plan` / `run` / `status` / `explain` 都有机读形态）；提需求先写场景，再写想要的命令面。
- **提 PR**：本仓库没有常驻 `main`，开发在版本线分支上（`git branch -a` 看当前那条，如 `feat/v1.4-doc-skill`）——从它切分支或 fork，PR 也提回该分支；一个 PR 只做一件事。CI（`.github/workflows/ci.yml`）在 push 与 PR 上跑三件检查，清单与触发面见下文「发布与版本」节末。
- **提交前必过**：仓库根 `uv run pytest` 与 `engines/midscene` 下 `npm test` 全绿。单测绿不等于对——结论一旦依赖 mock 之外的真实行为（进程与信号、并发时序、真实 IO 与网络、真 AWS），按 [`CLAUDE.md`](./CLAUDE.md)「代码纪律」把验证升级成真跑或对抗核查。
- **commit 信息用中文、按逻辑批次**：一个成块的功能或一轮修正收口、测试绿后再提交，不为每次小改动提交；多行信息用 `git commit -F <文件>`。push 由操作者决定时机（仓库公开）。
- **改 code 前先对齐决策**：相关 ADR（[`docs/adr/`](./docs/adr/)）里的契约与不变量先看一眼；需要新决策时先落 ADR，再写实现。
- **改完回头校准文档**：受影响的 ADR、`CONTEXT.md`、各包 `README.md` 与 `DEVELOPMENT.md`、`docs/` 下的页面一并改。枚举型内容（目录树、选项表、模块清单、护栏清单）靠 `ls` / grep / `--help` 逐条对差集，不靠通读。

## 现状与版本线

架构：**核心库 `core/`（Python）自解析 Gherkin → 分组 scope/job → 调度**，每个 scope spawn 一个**薄 worker 子进程**（Midscene=TS / Nova Act=Python），worker 讲统一的 worker↔core 协议（ADR 0024）。`cli/` 是核心库的第一张前端皮（argparse + render），组合根共享层在 `runtime/`（ADR 0016「演进」节）。v0.x 的 cucumber-js/pytest-bdd 双 runner 直跑已**退役**（ADR 0016 / 0022 / 0023）。关键约束：**全栈托管在 AWS 内**（ADR 0009）；**UI 语言支持范围按引擎划分**——Midscene 不限、Nova Act 限英文（ADR 0001）。部件全景先看 [`docs/internals/architecture-overview.md`](./docs/internals/architecture-overview.md)——开头的全景图给出五层与层间指向，往下依次是各层职责、一次 run 的生命周期、本机与云端两种载体、包与发行物的对应，比读下面的目录树快。

| 版本线 | 内容 | 状态 |
|---|---|---|
| v1.0 核心库 | parse + scope 分组 + schedule + 4 ports（Engine/Run/Result/ReportStore）+ 实时写编排；双引擎薄 worker、AgentCore 会话、投票治理、RunReport、网络韧性 | ✅ 真 AWS 端到端 |
| v1.1 云端 | store adapter（DynamoDB/S3，StepArgument offload 解 400KB 限）+ Fargate/ECS 执行面（`FargateEngine` + `gherkai-deploy-aws` 的 CDK stack）；boto3 只在云端路径懒加载（库层 extra `[aws]`，CLI 硬依赖 `gherkai-runtime[aws]`，ADR 0032/0033/0037） | ✅ 真部署真跑 |
| v1.2 无状态跑批 | `submit` 即走 + `status [--wait]`；local 档 per-run 后台进程 + SQLite events；cloud 档三 Lambda 事件驱动链（kicker / reconciler / exit-observer，DDB Stream + EventBridge）；job 墙钟预算兜底（ADR 0034） | ✅ |
| v1.3 本地应用测试 + 能力自述 | `--expose-local` ngrok 隧道（basic-auth 每 run 一换、终态即拆，ADR 0035）；`list-deterministic` / `plan` 派发标注（worker 注册表自述，ADR 0036） | ✅ |
| v1.4 分发与打包 | uv workspace 五包 + PyPI/npm 发行、git tag 版本单旋钮、`gherkai deploy` 内嵌 IaC、worker 镜像 variant 交付（ADR 0037 / 0038） | ✅ 已发行 |

v1 定位还差一项验收没做，前置条件是拿到可得的真实业务系统：至少 3 个真实业务用例由 feature 作者零 step 代码写出并跑通，同时记下每一处不得不写代码的破例。该项自 v0.x 顺延至今，目前只有骨架用例（wikipedia / example.com）在验证方向。验收标准与顺延理由见 [ADR 0016](./docs/adr/0016-execution-architecture-core-lib-run-model.md)「版本切分」节，定位口径见 [ADR 0015](./docs/adr/0015-v1-positioning-smoke-not-regression.md)。

## 目录结构

```
./
├── README.md                  ← 仓库首页（门面 + 30 秒上手，使用者向）；CONTRIBUTING.md ← 本文（contributor 向）
├── CHANGELOG.md               ← 每版变更说明（使用者语言；GitHub Release 正文由它渲染，发布 gate 要求本版有节）
├── CONTEXT.md                 ← 领域术语表（glossary）
├── CLAUDE.md                  ← 项目约定（沟通/文档纪律/代码纪律/工作方式）——给 contributor 侧 AI agent 与人
├── LICENSE                    ← 许可证（MIT）
├── pyproject.toml / uv.lock   ← uv workspace 根（成员 = core / runtime / cli / engines/novaact / deploy_aws 五个发行包）：单一 lock + 共用 dev 依赖与 pytest 配置（ADR 0037）
├── .github/                   ← CI 与发布链（workflows/{ci,release}.yml + scripts/ + release_body_footer.md（GitHub Release 正文的固定块）；一次性人工前置与本地校验见 .github/workflows/README.md，ADR 0037 决策 8）
├── .claude/commands/          ← Claude Code 项目命令：/doc-health-review、/code-health-review 两条复盘入口（.claude/ 其余为个人配置、不入库）
├── docs/                      ← 全部文档；按读者的分层与归位见 ADR 0045（三类读者、四个入口）
│   ├── README.md              ← 文档地图：使用者 / contributor / 想懂机理的人 / contributor 侧 AI agent 各从哪进
│   ├── adr/                   ← 架构决策记录（0001-0045，每篇带 Status 头）
│   ├── internals/             ← 机理横切解读（只讲 how、权威在 ADR + code）；篇目与主题归属见 docs/internals/README.md
│   ├── user-guide/            ← 使用者文档（安装 / 写 feature / 跑与看结果 / 云端后端 / 配置 / 排错）；owner 表见 docs/user-guide/README.md
│   ├── ai-eng/                ← contributor 侧 AI agent 的工作文档：README.md（该层入口）+ REFERENCES.md（外部一手来源）+ {doc,code}-health-review.md（两条复盘方法）
│   ├── journey/               ← 任务推进的 staging 区，按需创建（过程产物，吸收进 ADR/code 后即删，见 CLAUDE.md「文档纪律」）
│   └── diagrams/              ← 文档里的图：图源 JSON + 导出 SVG + index.html（各层文档共用；GitHub Pages 只发布这一个目录）
├── features/                  ← 共享 .feature（同一份两个引擎同读；通用 step 风格，QA 零代码）
│   ├── wikipedia_generic.feature / wikipedia_assertions.feature / wikipedia_robustness.feature
│   ├── wikipedia_zh.feature                ← 非英文 UI 探针：中文维基 + 中文 step，两引擎同题（ADR 0001 的测量夹具与重议复测入口）
│   ├── engine_routing.feature              ← @engine tag 路由验证
│   ├── deterministic_anchor.feature        ← @deterministic 锚点验证（ADR 0022）
│   └── concurrency_and_scope.feature       ← 手工真跑回归夹具：改调度/会话生命周期后重跑验 ADR 0019
├── core/                      ← 窄腰核心库（发行名 gherkai-core，Python，零引擎依赖，ADR 0016）
├── runtime/                   ← 产品本体 = 组合根共享层（发行名 gherkai-runtime；ADR 0016「演进」节；cli/Lambda/WebUI 的共同地基）
├── cli/                       ← 命令行皮（发行名 gherkai，命令 gherkai；ADR 0016）；随 wheel 发行的 agent skill 住在 gherkai_cli/skills/gherkai/（ADR 0043）
├── engines/                   ← 两个可插拔引擎，与 core 平级
│   ├── midscene/              ← npm 包 @gherkai/worker-midscene（ESM）：薄 worker + 使用方 steps 文件唯一该 import 的公开 API
│   └── novaact/               ← 发行包 gherkai-worker-novaact：薄 worker，`python -m` 入口
├── deploy_aws/                ← 发行包 gherkai-deploy-aws：`gherkai deploy` 的 AWS provider（Python CDK stack + 随部署打成 asset 的三个 Lambda handler 源 + worker 镜像交付命令，ADR 0033/0034/0037/0038）
├── skills/                    ← 不是 skill 的源文件（源文件在 cli/、随 wheel 发行）：gherkai-evals/ = agent skill 的评测资产，维护者与 AI 侧、不分发，资产清单与跑法在 ADR 0043 决策七；结果工作区 gherkai-workspace/ 不入库
├── graphify-out/              ← 代码 + 文档知识图（给 AI agent 先查图后翻源码；刷新见下文「知识图刷新」）
└── tools/                     ← 复用工具库（真跑 / 诊断 / 校验 / 渲染，清单见下表；长期资产，见 CLAUDE.md「工作方式」）
```

每个包目录都有两份文档：`README.md` = 发行包页面（逐字上 PyPI/npm，只写使用者内容）、`DEVELOPMENT.md` = 该包的 contributor 文档（模块布局、从 checkout 跑、测试、ADR 指针）——[`cli/`](./cli/DEVELOPMENT.md) · [`core/`](./core/DEVELOPMENT.md) · [`runtime/`](./runtime/DEVELOPMENT.md) · [`deploy_aws/`](./deploy_aws/DEVELOPMENT.md) · [`engines/novaact/`](./engines/novaact/DEVELOPMENT.md) · [`engines/midscene/`](./engines/midscene/DEVELOPMENT.md)。**文件级的模块布局只在各包 `DEVELOPMENT.md` 维护**，上面的目录树停在包级、不复述——两处都写迟早漂。

`tools/` 里的工具（做真跑、诊断、校验之前先翻一眼，别重造；每个脚本的头注释写了用途、前置与判读）：

| 工具 | 干什么 |
|---|---|
| `e2e_harness.py`（用法与判读见 `e2e_harness.md`） | worker 端到端真跑：真 spawn worker、真事件流、真会话，可注入中断时机；opt-in、不进 pytest、产生真实 AWS 费用 |
| `ecs_task_timing.py` | 抓 ECS task 生命周期的时间字段，标定 SIGTERM → 退出的真实墙钟预算（校 grace / stopTimeout） |
| `events_wallclock.py` | 从 events 表还原 worker emit 时刻，算单 act 墙钟分布（校 grace margin） |
| `build_diagrams.mjs` | 文档图两段式构建：`docs/diagrams/*.json` → `archify deliver` 出可交互 HTML（确定性渲染）→ 无头 Chrome 从 HTML 导出 SVG（`--png` 另导 PNG 供目视）；依赖 `engines/midscene` 的 Playwright 与本机 Chrome（见下文「图」） |
| `render_skill_contract.py` | `--json` 契约页 → agent skill 里那份副本的确定性转换（ADR 0043 决策四） |
| `graphify_refresh.sh` | 知识图的 LLM 侧刷新（见下文「知识图刷新」） |

## 开发环境（从 checkout 跑）

前置工具链：Python ≥ 3.13 + [uv](https://docs.astral.sh/uv/)；Node ≥ 22（Midscene worker 与 `gherkai deploy` 都要）；改部署侧另需容器引擎（docker）。各项装法与版本要求见 [`docs/user-guide/getting-started.md`](./docs/user-guide/getting-started.md)。

```bash
uv sync                                            # 五个 workspace 成员（core/runtime/cli + novaact worker + deploy-aws provider）一次装齐（共用根 .venv/）
(cd engines/midscene && npm ci && npm run build)   # Midscene worker（npm 包，Node ≥22）：装依赖 + 编译到 dist/
# dev 态让 CLI 用本仓库的 midscene worker（发行版用户走 `npm i -g @gherkai/worker-midscene`，不需此步）：
export GHERKAI_WORKER_MIDSCENE_CMD="node $PWD/engines/midscene/dist/bin.mjs"
```

`uv sync` 把五个成员（`gherkai-core` / `gherkai-runtime` / `gherkai` / `gherkai-worker-novaact` / `gherkai-deploy-aws`）以 editable 装进仓库根的同一个 `.venv/`（ADR 0037：单一 workspace、单一 `uv.lock`）。此后**在仓库根**敲 `uv run gherkai <子命令>`（文档里的 `gherkai …` 示例在仓库内都写成 `uv run gherkai …`）。

环境隔离：Python 成员与 Nova Act worker 都在仓库根 `.venv`（worker 与 CLI 同 venv 是设计——`python -m gherkai_worker_novaact` 无包装层、fd 直达，ADR 0037 决策 3），Midscene worker 的 TS 依赖在 `engines/midscene/node_modules`——均不污染全局。AWS 凭证、需开通的服务、ngrok 这些前置见 [`docs/user-guide/getting-started.md`](./docs/user-guide/getting-started.md)。

## 在有凭证的机器上验未发布的工作树

本机没有 AWS 凭证时，真跑（本机档 `run` 也要连 AgentCore 与模型）到一台有凭证的开发机上做；机器、前缀、region 这类环境事实不入 repo，走操作者自己的备忘。流程如下，其后每条注意事项都对应一次真实发生过的失败：

```bash
# 1) 把工作树同步过去（不要 push 半成品到 public repo）；排除本地产物，保留 .git 让版本能从 tag 派生
rsync -az --delete --exclude .venv --exclude node_modules --exclude graphify-out --exclude reports \
      --exclude engines/midscene/dist --exclude skills/gherkai-workspace --exclude .pytest_cache --exclude __pycache__ \
      --exclude .claude/ --exclude .agents/ ./ <user>@<host>:~/<repo-copy>/
# 2) 在那份 checkout 里用 uv run 跑——PyPI 装的 gherkai 是发行版，没有新代码
ssh <host> 'cd ~/<repo-copy> && export PATH=$PATH:~/.local/bin && AWS_REGION=<region> uv run gherkai run features/x.feature'
```

- 已 push 的代码可以直接在远端 `git pull https://github.com/zhiyanliu/gherkai.git <branch>`（匿名 https；远端一般没有 git 的 SSH key，`origin` 是 SSH URL 拉不动）。
- 远端 `.venv` 里的发行版本是**上次 `uv sync` 时的快照**（`uv run` 会重新装 editable 成员，但版本串跟当时的 git 状态走）；worker 镜像 tag 含精确版本串，所以这份 checkout **不能** cloud `run` / `submit`（variant 解析找不到 `<该版本>-base`，退 2 是设计内提示）——验云端侧新代码只能用只读命令或另推 dev 版 variant（`gherkai deploy push-worker`，见 ADR 0038）。
- Midscene 的 dev worker：`cd engines/midscene && npm run build` 出 `dist/bin.mjs`，再把它软链成 PATH 上的 `gherkai-worker-midscene`（或设 `GHERKAI_WORKER_MIDSCENE_CMD`），CLI 就按定位链找到它。
- 要一份带 error act 的证据（验 `explain` 的错误分支）：`NOVA_ACT_TIMEOUT_S=2` 让 Nova 的 act 必超时。
- ssh 长等待会被远端掐断：带 `-o ServerAliveInterval=15`，`status --wait` 这类长等改成 15 秒一轮的 `status --json` 轮询；长任务用 `nohup … > log 2>&1 &` 起、再轮询日志。偶发 kex 阶段被拒（TCP 通、sshd 拒）——等几分钟重试，别急着重启实例。
- 录评测 fixture 的远端步骤见 ADR 0043 决策七；知识图刷新见下节。

## 测试

```bash
uv run pytest                                    # 全部 workspace 成员的单测（根 pyproject 的 testpaths；-m 'not integration'）
(cd engines/midscene && npm test)                # Midscene worker 单测
uv run pytest core/tests -m integration          # 集成测试：假定真表/桶已预建（见 core/tests/README.md）
```

文档与文案护栏也在单测里（改了文档、CLI 文案或 agent skill 之后跟着跑）：

| 护栏 | 守什么 |
|---|---|
| `cli/tests/test_cli_json_contract.py` | `--json` 字段契约：真渲染器出样例 → 递归收全部键名 → 逐个断言出现在 `docs/internals/cli-json-contract.md`，文档漏键即红 |
| `deploy_aws/tests/test_workers.py` | 同一份契约页的 `list-workers` 字段（样例要 moto，故断言留在 provider 包侧） |
| `cli/tests/test_user_facing_messages.py` | 产品面文案不带内部指代：AST 扫五个生产包的 Python 字面量 + Midscene 的 `.mts` 源，注释与 docstring 放行 |
| `cli/tests/test_package_readmes.py` | 进包的 README（各包 pyproject `readme` 指向的那份 + npm `files` 里的）与各包 Summary：零内部指代 + 零相对链接；根 `README.md`：只查零内部指代（它的相对链接在 GitHub 上正常渲染，可达性由 `test_user_docs.py` 断）；另断言每个包目录一份 `DEVELOPMENT.md`、根一份 `CONTRIBUTING.md`，以及 GitHub Release 正文的固定块 |
| `cli/tests/test_user_docs.py` | 仓库内的用户文档（`docs/user-guide/**`、根 `README.md`、`CHANGELOG.md`）：零内部指代、相对链接可达、不把读者引向 contributor 侧文档（ADR / CONTEXT / CLAUDE.md / journey / ai-eng）、owner 表与目录两向差集；另守图：`docs/diagrams/` 的 JSON 图源与导出 SVG 成对、图源零内部指代、README / 本文 / `docs/**` 里不留 mermaid 块 |
| `cli/tests/test_release_notes.py` | `.github/scripts/release_notes.py` 两件事：「已发行 tag 在 `CHANGELOG.md` 里有非空节」的 gate 与 Release 正文渲染 |
| `cli/tests/test_skill.py` | 随 wheel 发行的 agent skill：文案与指针形态、`gherkai <子命令> --flag` 组合对照 argparse 真值与「仅某命令」排他、反引号键名对照契约页、契约页转换副本相等、目录白名单与形态上限、评测 fixture 的 ignore 行为与可搬迁不变量 |
| `deploy_aws/tests/test_skill_deploy_tokens.py` | skill 里 `deploy` / `destroy` 那批命令 token 对照 provider 的真 parser（provider 住 `[deploy-aws]` extra、皮的测试不该强依赖它） |

禁词表、相对链接正则与 skill 的命令 token 抽取器住在 `cli/tests/_doc_rules.py`——五个消费方共用（四份护栏 `test_package_readmes.py` / `test_user_docs.py` / `test_skill.py` / `test_skill_deploy_tokens.py`，外加 `tools/render_skill_contract.py` 的自查），别再抄第二份。单测绿不等于对——凡结论依赖 mock 之外的真实行为（进程/信号/并发/真 AWS），按 CLAUDE.md「绿≠对」升级验证；端到端真跑的现成工具在 `tools/`（先翻一眼、别重造）。

**图**：全部图统一用 archify，图源与静态图在 [`docs/diagrams/`](./docs/diagrams/)：改图 = 改 `<name>.json`，跑 `node tools/build_diagrams.mjs [docs/diagrams/<name>.json]`（deliver 出 HTML、再从 HTML 导出 SVG；`--png` 另导 PNG 只供目视、不入库），JSON 与 SVG 同 commit；正文以 markdown 图片语法嵌入 `docs/diagrams/<name>.svg`。HTML 默认不入库（`.gitignore` 排除）；只有发布到 GitHub Pages 的可交互大图才入库 HTML，发布 = `.gitignore` 加白名单行 + `docs/diagrams/index.html` 加链接 + HTML 入库三者同 commit，[`.github/workflows/pages.yml`](./.github/workflows/pages.yml) 把该目录原样上传。图上只画结构与指向，会漂的字面量留正文；图源零内部指代（护栏 `cli/tests/test_user_docs.py` 扫 JSON、断言 JSON 与 SVG 成对且 SVG 末尾的图源 sha256 指纹与 JSON 一致——改了图源没重导在 CI 里就红、正文无 mermaid 块、入库 HTML 有图源且在 index 有链接）。形态、立图门槛与被拒方案见 [ADR 0045](./docs/adr/0045-documentation-layering-and-placement.md) 决策七。作图怎么一次画对（类型、内容规则、布局清单、archify 技法）见 [`docs/ai-eng/diagram-authoring.md`](./docs/ai-eng/diagram-authoring.md)；在 Claude Code 里 `/diagram` 或提到改图即自动加载该方法（项目级 skill [`.claude/skills/diagram/`](./.claude/skills/diagram/SKILL.md)）。

**派生文件的自动同步（Claude Code）**：项目级 hook [`.claude/hooks/sync-derived.sh`](./.claude/hooks/sync-derived.sh)（由入库的 [`.claude/settings.json`](./.claude/settings.json) 挂在 Edit / Write / MultiEdit / Bash 之后）在每次工具调用后做两件事：skill 契约副本与源不同步就用 `tools/render_skill_contract.py` 重渲染并告知 agent；`docs/diagrams/*.json` 比同名 SVG 新就提醒跑 `tools/build_diagrams.mjs`（不自动重建）。首次进入仓库时 Claude Code 会请你确认一次项目 hook。这只是编辑时刻的便利层，Codex / 人手编辑与 CI 仍靠 `cli/tests/test_skill.py`、`cli/tests/test_user_docs.py` 兜底。个人配置（graphify 的 hook-guard、plugin 开关）放 `.claude/settings.local.json`，不入库。

## Spike（可独立跑的技术验证脚本）

```bash
# Midscene 引擎三段隔离自检（模型连接 / 浏览器连接(CDP) / 合体；另有 04 planning 探针 / 05 负向断言，见 engines/midscene/DEVELOPMENT.md）
cd engines/midscene && AWS_REGION=us-east-1 node_modules/.bin/tsx spikes/01-model-sigv4.ts
# 02-agentcore-cdp.ts / 03-midscene-grounding.ts 同理

# Nova Act 引擎对标 spike
AWS_REGION=us-east-1 uv run python engines/novaact/spikes/wikipedia_benchmark.py   # 用仓库根 .venv（novaact 无独立 venv）
AWS_REGION=us-east-1 uv run python engines/novaact/spikes/negative_assertions.py   # 负向断言（对标 midscene 05）
```

## 知识图刷新（graphify）

`graphify-out/`（`graph.json` / `GRAPH_REPORT.md` / `wiki/`）是给 AI agent 的代码 + 文档知识图（CLAUDE.md「graphify」节让 agent 先查图再翻源码）。维护分两层：

- **AST 层自动**：`graphify hook install` 装的 post-commit hook 在每次含代码文件的 commit 后重抽代码、重聚类；不调 LLM。
- **LLM 层手动、周期性**：文档语义抽取与社区命名要 LLM（AWS Bedrock），hook 覆盖不到——改了 ADR / README / `docs/` 下的页面，或报告里社区名退化成文件名（hook 按枢纽节点起的临时名）时跑：

```bash
tools/graphify_refresh.sh            # 抽取到收敛 → LLM 命名社区 + 重生成报告 → 导出 wiki（顺序有意义，env 默认值见脚本头注释）
tools/graphify_refresh.sh --force    # 全量重抽（清残留节点时；费用按全仓文档量计）
```

扫描范围由 `.gitignore` + 根 `.graphifyignore` 决定：评测 fixture（`skills/gherkai-evals/fixtures/`，运行产物快照、截图是 PNG 占位却带 .jpg 扩展名，送 Bedrock 会被拒并拖垮整块抽取）与评测 workspace 排除在图外。需要 Bedrock 凭证，且 env 里有 `AWS_REGION` 或 `AWS_PROFILE`（脚本会回落 `aws configure get region`）。本机没凭证时到有凭证的机器上跑：rsync 工作区过去（排除 `.git` / `.venv` / `node_modules`，**带上 `graphify-out/`** 以复用增量缓存）→ 跑脚本 → rsync `graphify-out/` 回来时**排除 `.graphify_root`**（它存绝对路径，带回会让本地 hook 重建失败）→ commit `graph.json` / `GRAPH_REPORT.md` / `manifest.json` / `wiki/`（其余是缓存与滚动备份，`.gitignore` 已排除）。

## 发布与版本

**推 tag `vX.Y.Z` 不进 CI、直接进发布链**（`.github/workflows/release.yml`；CI 的分支过滤把 tag 排除在外）——发布路径上只有下面那道 gate，不跑 `pytest` 与 `npm test`，所以该跑绿的测试与本地校验必须在推 tag 之前做完。

**版本真源只有 git tag `vX.Y.Z`**——五个 Python 发行包、npm 包 `@gherkai/worker-midscene`、两个 worker 基底镜像同号（ADR 0037 决策 2b/7）。五个发行包的 pyproject 都写 `dynamic = ["version"]`、没有版本字段（uv-dynamic-versioning 从 tag 算；不发行的 workspace 根另写死 `0.0.0`）；`engines/midscene/package.json` 只留占位 `0.0.0-dev`，发布链在 `npm publish` 前按 tag 改写它，谁都不该手工维护那一行。发布因此是一个动作，前提是该版的变更说明已写好：

```bash
git tag vX.Y.Z && git push origin vX.Y.Z   # GitHub Actions 接手：gate（tag 形态 + CHANGELOG 有本版节 + 版本==tag）→ PyPI → npm → GHCR 基底镜像 → GitHub Release
```

发版前写 `CHANGELOG.md` 的该版节（Keep a Changelog 形态、使用者语言：小节名用 新增 / 变化 / 移除 / 修复，外加本项目自加的 升级须知）——发布 gate 校验本 tag 在 changelog 里有非空节，缺则发版失败；GitHub Release 正文 = 该节 + `.github/release_body_footer.md` 的固定块，由 `.github/scripts/release_notes.py` 渲染（ADR 0045 决策五）。

发版后的验证里有一项手动的：把新版本部署到验证环境后，用 agent skill 的云端一条线（`doctor --backend cloud --prefix <前缀>` → `plan` → `submit` → `status --wait` → `explain`）在有凭证的机器上真走一遍——它是 skill 评测里唯一没被真实数据覆盖的域（评测舞台刻意无凭证），结论回填 ADR 0043「验证」节。同一次真跑顺带核一件事：Nova Act 的 workflow definition 名已改为产品名 `gherkai-worker`（原 spike 期代号），首次 `run --engine novaact` 须在使用方账户自动建出该名的 definition 且 run 到终态——create-if-not-exists 跨真实 AWS 边界，单测绿不算证据（ADR 0004）。

CI（任意分支的 push、PR、手动触发）跑三件：全成员 `pytest`、midscene 的 `npm ci && npm run build && npm test`、`uv build --all-packages` 的打包元数据 smoke + 发布 gate 演练。一次性人工前置（PyPI trusted publisher、npm trusted publisher、GHCR 可见性核对）、TestPyPI 演练、以及**不推 tag 也能做的本地静态校验**，全在 [`.github/workflows/README.md`](./.github/workflows/README.md)；决策与理由在 [ADR 0037 决策 8](./docs/adr/0037-distribution-and-packaging.md)。

## 文档去哪读

全部文档的地图是 [`docs/README.md`](./docs/README.md)（按读者分类、每类的入口与 owner 表）。四层分工，决策与理由见 [ADR 0045](./docs/adr/0045-documentation-layering-and-placement.md)：

| 层 | 在哪 | 装什么 |
|---|---|---|
| 决策 | [`docs/adr/`](./docs/adr/) | 稳定决策的 what / why / trade-off，每篇带 Status 头、Accepted 的自包含。与其它文档冲突时以 ADR 与 code 为准 |
| 机理 | [`docs/internals/`](./docs/internals/README.md) | 给想懂机理的技术读者的横切解读：只讲 how、不复述 why，正文带 ADR 指针 |
| 使用 | [`docs/user-guide/`](./docs/user-guide/README.md)、根 [`README.md`](./README.md)、各包 `README.md`、`CHANGELOG.md`、随 CLI 发行的 agent skill | 使用者与替使用者操作的 AI agent 读：产品说明口吻、零内部指代、包页面只作入口 |
| 参与 | 本文、各包 `DEVELOPMENT.md`、[`.github/workflows/README.md`](./.github/workflows/README.md) | 在这个仓库里怎么干活：布局、环境、测试、发布链 |

另外两处：术语在 [`CONTEXT.md`](./CONTEXT.md)；contributor 侧 AI agent 的工作文档在 [`docs/ai-eng/`](./docs/ai-eng/README.md)——外部一手来源 [`REFERENCES.md`](./docs/ai-eng/REFERENCES.md) 与两条复盘方法。

- 复盘方法（给 contributor 侧 AI agent 执行的任务指令，不是人手工清单）：[`docs/ai-eng/doc-health-review.md`](./docs/ai-eng/doc-health-review.md)（全部文档对照 code 去漂移）/ [`docs/ai-eng/code-health-review.md`](./docs/ai-eng/code-health-review.md)（全部生产代码查死代码 / 过时 / 违背 ADR）。事件驱动：显著构建里程碑或一批 ADR 增改后跑，不定期空跑。Claude Code 里敲 `/doc-health-review`、`/code-health-review`（入口在 [`.claude/commands/`](./.claude/commands/)，只是把方法文档喂给 agent 并强调不可跳过的步骤）；其它 AI coding 工具把对应方法文档整份作为任务指令即可。客观类问题 agent 直接改，主观类出报告待批。
