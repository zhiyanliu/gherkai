# CLI Docs and ADRs

> 67 nodes · cohesion 0.08

## Key Concepts

- **ADR 0016 执行架构与分层** (42 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **ADR 0037 分发与包化** (36 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **cli 包 contributor 文档** (20 connections) — `cli/DEVELOPMENT.md`
- **ADR 0038 worker 镜像交付** (20 connections) — `docs/adr/0038-worker-image-delivery.md`
- **ADR 0019 feature tag 语义** (17 connections) — `docs/adr/0019-feature-tags-scope-and-engine.md`
- **ADR 0033 IaC AWS 后端与组合装配** (17 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **ADR 0022 core 解析 + 薄 worker（注册表即扩展点）** (16 connections) — `docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md`
- **ADR 0014 AI 优先的断言策略** (15 connections) — `docs/adr/0014-ai-first-assertions.md`
- **ADR 0029 引擎产物上传 S3** (15 connections) — `docs/adr/0029-engine-artifacts-to-s3.md`
- **Nova Act worker 开发笔记** (15 connections) — `engines/novaact/DEVELOPMENT.md`
- **ADR 0020 默认 AI / 确定性脚手架** (14 connections) — `docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md`
- **ADR 0035 本机应用隧道暴露** (13 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **ADR 0036 确定性能力自述** (13 connections) — `docs/adr/0036-deterministic-capability-discovery.md`
- **ADR 0044 模型选择与覆盖** (12 connections) — `docs/adr/0044-engine-model-selection-and-override.md`
- **ADR 0001: 范围限定英文 UI** (11 connections) — `docs/adr/0001-scope-limited-to-english-ui.md`
- **ADR 0013 跨引擎共享边界** (10 connections) — `docs/adr/0013-cross-engine-sharing-boundary.md`
- **ADR 0032 Fargate 执行环境** (10 connections) — `docs/adr/0032-fargate-execution-environment.md`
- **gherkai-deploy-aws contributor 手册** (9 connections) — `deploy_aws/DEVELOPMENT.md`
- **ADR 0010: spike 作同等条件基准** (9 connections) — `docs/adr/0010-spike-as-apples-to-apples-benchmark.md`
- **ADR 0015 v1 定位：柔性冒烟** (9 connections) — `docs/adr/0015-v1-positioning-smoke-not-regression.md`
- **ADR 0017: 选 Fargate 而非 Runtime** (9 connections) — `docs/adr/0017-cloud-execution-fargate-over-runtime.md`
- **ADR 0004 Nova Act IAM 鉴权** (8 connections) — `docs/adr/0004-novaact-iam-auth-via-workflow.md`
- **ADR 0009 最大化使用 AWS 是硬前提** (8 connections) — `docs/adr/0009-maximize-aws-hard-constraint.md`
- **ADR 0018 通用 step 能力** (8 connections) — `docs/adr/0018-generic-steps-capability.md`
- **ADR 0003 Midscene grounding 用 Bedrock Qwen3-VL** (7 connections) — `docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md`
- *... and 42 more nodes in this community*

## Relationships

- [Core Protocol Documentation](Core_Protocol_Documentation.md) (59 shared connections)
- [Architecture Diagrams](Architecture_Diagrams.md) (23 shared connections)
- [Skill and Release ADRs](Skill_and_Release_ADRs.md) (8 shared connections)
- [Project Conventions Glossary](Project_Conventions_Glossary.md) (8 shared connections)
- [Skill and Packaging Features](Skill_and_Packaging_Features.md) (8 shared connections)
- [Glossary and Changelog](Glossary_and_Changelog.md) (6 shared connections)
- [Artifact Upload Strategy](Artifact_Upload_Strategy.md) (4 shared connections)
- [Naming & Prefix Conventions](Naming_%26_Prefix_Conventions.md) (3 shared connections)
- [Agent Skill Reference Docs](Agent_Skill_Reference_Docs.md) (2 shared connections)
- [Deploy Command Frontend](Deploy_Command_Frontend.md) (1 shared connections)
- [Skill Install Command](Skill_Install_Command.md) (1 shared connections)
- [CDK App and Deploy CLI](CDK_App_and_Deploy_CLI.md) (1 shared connections)

## Source Files

- `.github/workflows/ci.yml`
- `CONTEXT.md`
- `cli/DEVELOPMENT.md`
- `deploy_aws/DEVELOPMENT.md`
- `deploy_aws/README.md`
- `docs/adr/0001-scope-limited-to-english-ui.md`
- `docs/adr/0002-midscene-not-driven-by-gpt55.md`
- `docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md`
- `docs/adr/0004-novaact-iam-auth-via-workflow.md`
- `docs/adr/0005-single-shared-feature-file.md`
- `docs/adr/0006-form-a-two-subprojects-no-orchestrator.md`
- `docs/adr/0007-programmatic-login-hitl-as-escape-hatch.md`
- `docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md`
- `docs/adr/0009-maximize-aws-hard-constraint.md`
- `docs/adr/0010-spike-as-apples-to-apples-benchmark.md`
- `docs/adr/0011-agentcore-browser-system-default-vs-custom.md`
- `docs/adr/0012-planning-shares-qwen3vl-no-text-planner.md`
- `docs/adr/0013-cross-engine-sharing-boundary.md`
- `docs/adr/0014-ai-first-assertions.md`
- `docs/adr/0015-v1-positioning-smoke-not-regression.md`

## Audit Trail

- EXTRACTED: 290 (96%)
- INFERRED: 10 (3%)
- AMBIGUOUS: 2 (1%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*