# 权威信息源（自查用）

> 抢救自原 `midscene-novaact-prototype-guide.md` §10（该文档已退役），并补入本项目实测中用到的关键路径。
> 注意：决策与实装现状以 `docs/adr/` + code 为准（`CONTEXT.md` 只定术语，见 ADR 0045 决策八）——下面是**外部一手来源**，用于查证细节。

## Midscene（任意页加 `.md` 取 markdown）

- https://midscenejs.com/model-config.md — 全部环境变量（含 `MIDSCENE_*_MODEL_*` 分槽）
- https://midscenejs.com/model-strategy.md — grounding 排名 + 多模型分工（planning 需 multimodal）
- https://midscenejs.com/model-common-config.md — family 列表 + 配置块
- https://midscenejs.com/integrate-with-playwright.md
- https://midscenejs.com/bridge-mode.md — 连桌面 Chrome（CDP 接法参考）
- 安装的源码（本机 ground truth，现为 1.12.8）：`engines/midscene/node_modules/@midscene/core/dist/`、`.../shared/dist/`
  - `createOpenAIClient` 注入点：`@midscene/core .../ai-model/service-caller/openai-client`（`createAndWrapClient` 里 `await createOpenAIClient(baseOpenAI, openAIOptions)`，经同文件 `createChatClient` 调用；`service-caller/index` 只再导出 `createChatClient` 等符号、不含此回调；见 ADR 0008）
  - 隔离 ModelConfigManager：`@midscene/core .../agent/agent.js`（传 `modelConfig` 即切隔离——我们的接线同时传 createOpenAIClient 与 modelConfig；1.12.8 起只传 createOpenAIClient 则是 agent 作用域包装、仍读全局 env，见 `engines/midscene/spikes/SIGV4-FETCH-RECIPE.md` §7）
  - planning 无条件附图：`@midscene/core .../ai-model/workflows/planning/standard-planning.js`（`standardPlan()` 两个消息分支都附 `image_url`，`includeLocateInPlanning` 不去图、只改 system prompt 与定位解析；1.9.8 时此逻辑在 `ai-model/llm-planning.js`，见 ADR 0012）
  - 取结构化 API：`aiBoolean/aiNumber/aiString/aiQuery/aiAsk`（`.../agent/agent.d.ts`，见 ADR 0010/0014）

## Nova Act

- https://github.com/aws/nova-act — README（AgentCore 接法、`nova.page`、HITL）
- https://docs.aws.amazon.com/nova-act/latest/userguide/ — 官方用户指南（HITL 实现、workflow definition 与 IAM 路径、SDK 行为的一手权威；README 只给上手面）
- https://nova.amazon.com/act — API key 生成、Playground
- 安装的源码：`.venv/lib/python3.13/site-packages/nova_act/`（仓库根 workspace venv）
  - AgentCore provider：`browser_auth/agentcore_session_provider.py`（`cdp_session()` yield `(ws_url, headers)`）
  - workflow contextvar：`types/workflow.py`（`@workflow` 设 `set_current_workflow`；`with Workflow` 不设——worker 走 `with Workflow`，故须手动补 `set_current_workflow`，见 `engines/novaact/gherkai_worker_novaact/run_scope.py` / ADR 0004）
- 多语言 SDK（形态 B 探路，**已证伪**：是客户端驱动的 REST 循环、非 `nova.act()` acting 等价物，acting 锁 Python，见 ADR 0006/0023）：npm `@aws-sdk/client-nova-act`、Go `aws-sdk-go-v2/service/novaact`

## AWS Bedrock / AgentCore

- https://docs.aws.amazon.com/bedrock/latest/userguide/inference-chat-completions-mantle.html — **OpenAI chat-completions 端点**（`bedrock-mantle` /v1 与 `bedrock-runtime` /openai/v1；SigV4 或 Bedrock API key）
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/browser-tool.html — AgentCore Browser
- https://docs.aws.amazon.com/bedrock/latest/userguide/ — Bedrock 模型卡、API keys、各模型"支持的 API"矩阵

## 常用 CLI（本项目实测用到）

```bash
# 列模型 + 过滤（确认账号/region 可用性）
aws bedrock list-foundation-models --region us-east-1 --query "modelSummaries[?contains(modelId,'qwen')].[modelId,inputModalities]" --output text

# 注册 workflow definition 的等价 CLI（仅作查证/排障参考——生产不需手动跑：代码经
# engines/novaact/gherkai_worker_novaact/lib/workflow_setup.py 的 ensure_workflow_definition() create-if-not-exists，见 ADR 0004）
aws nova-act create-workflow-definition --region us-east-1 --name <name>

# AgentCore 浏览器会话（数据面）
aws bedrock-agentcore start-browser-session --region us-east-1 --browser-identifier aws.browser.v1 --name <name>
aws bedrock-agentcore stop-browser-session  --region us-east-1 --browser-identifier aws.browser.v1 --session-id <id>
```

## 发行与打包（见 ADR 0037）

- https://docs.astral.sh/uv/guides/tools/ — `uvx` / `uv tool install`：`<name>` 同时作发行名与命令名解析；extras 用 `--from 'pkg[extra]'`
- https://docs.astral.sh/uv/concepts/projects/dependencies/ — `tool.uv.sources` 只被 uv 认、不进标准元数据（发布 wheel 的 `Requires-Dist` 为裸名）
- https://docs.astral.sh/uv/guides/package/ — `uv build`/`uv publish`；`uv publish` 不生成 attestation（只上传已有 `*.publish.attestation`）；TestPyPI 需 `publish-url`
- https://github.com/astral-sh/attest-action — 生成 PEP 740 attestation 的 Action（在 `uv publish` 之前）
- https://github.com/astral-sh/uv/issues/9811 — uv 不把 workspace/path 依赖翻译成版本 pin（`needs-design`，open）
- https://github.com/ninoseki/uv-dynamic-versioning — git tag 派生版本 + hatch metadata hook 渲染 `pkg=={{ version }}`（依赖须整体 dynamic、`[project]` 侧删除）
- https://github.com/pydantic/pydantic-ai/blob/main/clai/pyproject.toml · https://pypi.org/pypi/clai/json — 上述三段配置的生产先例（`Requires-Dist: pydantic-ai==<clai 同版本>`，随 clai 发版前进；2026-09 采样为 `==2.43.0`）
- https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/ — pending publisher **不**预留项目名（他人先注册即失效）
- https://packaging.python.org/en/latest/discussions/distribution-package-vs-import-package/ — 发行名与 import 名不强制任何关系；同名顶层 import 包可由多个发行包提供
- https://packaging.python.org/en/latest/guides/tool-recommendations/ — PyPA 官方工具推荐（仍只列 pipx）；对照 https://pipx.pypa.io/latest/how-to/use-uv-backend.html（pipx 的 uv backend）与 https://pipx.pypa.io/latest/how-to/standalone-python.html（`--fetch-python missing`）
- https://pypistats.org/api/packages/uv/recent · https://pypistats.org/api/packages/pipx/recent — 月下载量对照（ADR 0037 引用的 28 倍为 2026-08 采样）
- https://docs.astral.sh/uv/concepts/python-versions/ — uv 缺解释器时自动下载托管 CPython（`requires-python >=3.13` 对 uv 用户近乎免费）
- https://peps.python.org/pep-0685/ — extras 名规范化（`deploy-aws` ≡ `deploy_aws`）；https://peps.python.org/pep-0541/ — PyPI 名字回收政策；https://peps.python.org/pep-0740/ — 索引托管的发布 attestation
- https://pypi.org/pypi/core/json — 占住 `core` 名的零文件僵尸包（1.0.1，2011）
- https://docs.npmjs.com/about-scopes — npm scope 即命名空间（`@gherkai/*`）；https://docs.npmjs.com/policies/disputes — npm 名字争议政策（占位包须带真实项目指向）
- https://github.com/tconbeer/harlequin · https://github.com/darrenburns/posting · https://github.com/simonw/llm — 同类 Python CLI 的 README 安装块抽样（`uv tool install` 领头、pipx 回落）
- https://nodejs.org/api/module.html — `module.register()` 异步 customization hooks（独立 loader 线程、`data` 传参）与 `module.registerHooks()`（同步，≥22.15）；https://github.com/privatenumber/tsx — `tsx/esm/api` register 只对 ESM（`.mts`/`.mjs`，或 `package.json#type=module` 下的 `.ts`/`.js`）生效
- https://docs.brew.sh/Package-Acceptance-Policy — homebrew-core 收录门槛（star/fork/仓库年龄）
- https://docs.aws.amazon.com/cdk/v2/guide/getting-started.html — CDK 前置：Python CDK 亦需 Node.js（jsii）
- https://github.com/dagster-io/dagster/blob/master/helm/dagster/README.md — 「chart 版本 = 包版本，镜像 tag 缺省跟 chart」；https://github.com/dagster-io/dagster-cloud/issues/38 — 无版本模板硬编码 URL 致 EU 部署断的事故
- https://docs.prefect.io/v3/concepts/server — client/server 版本兼容的一句规则（本项目改写为「升级即三步」，见 ADR 0037 决策 7）
- https://aws.github.io/chalice/topics/cfn.html · https://aws.github.io/chalice/topics/tf.html — Chalice「IaC 进 wheel + `package --pkg-format cloudformation|terraform` 导出阀」模式；https://github.com/outerbounds/metaflow-tools — Metaflow 的 IaC 单独 repo 模式（被拒方案对照）

## 镜像与 ECS 交付（见 ADR 0038）

- https://github.com/distribution/reference — 镜像引用语法（tag = `[\w][\w.-]{0,127}`，`+`/`!` 非法）
- https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry — GHCR：公共镜像匿名拉取、`GITHUB_TOKEN` 推送
- https://aws.amazon.com/ecr/pricing/ · https://docs.aws.amazon.com/AmazonECR/latest/userguide/pull-through-cache.html — ECR Public 免流量费与 pull-through cache 免认证（本项目运行时不拉公共镜像，故不构成选型依据）；https://docs.docker.com/docker-hub/usage/pulls/ — Docker Hub 匿名拉取限额
- https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_RunTask.html · https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_ContainerOverride.html — RunTask 的容器 override 字段（无 image，故选镜像 = 选 task-def revision，见 ADR 0038）
- https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deregister-task-definition-v2.html · https://docs.aws.amazon.com/AmazonECS/latest/developerguide/delete-task-definition-v2.html — Deregister（INACTIVE：在跑 task 不受影响、不能再起新 task）与 Delete（永久删 INACTIVE）语义
- https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-tasks-services.html#fargate-task-definitions — Fargate `runtimePlatform.cpuArchitecture`（ARM64 / X86_64）按 task-def 设定；https://aws.amazon.com/fargate/pricing/ — x86 与 ARM 单价对照
- https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-push-iam.html — ECR push 最小权限示例（`GetAuthorizationToken` 单开 `Resource: "*"`）
- https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-arm64.html — Fargate ARM64 的考虑事项（不可用面按 AZ：us-east-1 `use1-az3`）；https://docs.aws.amazon.com/AmazonECS/latest/developerguide/security_iam_id-based-policy-examples.html — task-def 类动作不支持资源级权限（`Resource: "*"`）
- https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_DescribeTaskDefinition.html · https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_RegisterTaskDefinition.html — 复制模板时须剔除的只读字段、`include=TAGS`、注册时打 tags 需 `ecs:TagResource`
- https://docs.aws.amazon.com/systems-manager/latest/APIReference/API_GetParametersByPath.html — 单页最多 10 条、`Recursive` 默认 false；标准参数值上限 4KB
- https://github.com/moby/moby/blob/master/api/swagger.yaml — `ImageInspect.RepoDigests` 仅在 pull/push 过 registry 后可用（本地 build 的镜像无 manifest digest）

## Agent Skills（见 ADR 0043）

- https://agentskills.io/specification — Agent Skills 开放规范：`SKILL.md` frontmatter（`name` 小写连字符 ≤ 64 且等于目录名、`description` ≤ 1024 字符）、正文建议 < 500 行、`references/` `scripts/` `assets/` 三类捆绑资源、渐进式披露（元数据常驻 → 触发时读正文 → 按需读 references）
- https://github.com/vercel-labs/skills — `npx skills add <source>`：容器目录默认只扫 `skills/` `.claude/skills/` 等惯用位，任意路径用 `tree/<ref>/<path>` 直指（可钉 tag）；`--agent` 选安装位，`-g` 切全局；Claude Code 落 `.claude/skills/` / `~/.claude/skills/`、Codex 落 `.agents/skills/` / **`~/.codex/skills/`**（项目级 `.codex/skills` 官方从未列出；Codex 全局位与 `gherkai skill install` 的 `~/.agents/skills/` 分叉，见 ADR 0043 决策三）
- https://developers.openai.com/codex/skills — Codex skills：项目级 `.agents/skills/`、用户级 `~/.agents/skills/`；AGENTS.md 只需一行指针
- https://code.claude.com/docs/en/skills — Claude Code skills：项目级 `.claude/skills/`、用户级 `~/.claude/skills/`；frontmatter 允许宿主扩展键
- skill-creator（Anthropic `example-skills` 插件内，本机 `~/.claude/plugins/cache/anthropic-agent-skills/example-skills/<hash>/skills/skill-creator/`）——评测循环（`evals.json` schema、with-skill vs baseline 两臂、`scripts/aggregate_benchmark.py`、`eval-viewer/generate_review.py`）与 description 优化（`scripts/run_loop.py --eval-set <触发集> --skill-path <skill> --model <模型>`，train / held-out 分割；**其触发测量经 `scripts/run_eval.py` 走 `.claude/commands/<name>.md` 那套、在 Claude Code 2.1.270 上对本项目 skill 实测恒 0**，触发率改用自写驱动，见 ADR 0043 决策七）
