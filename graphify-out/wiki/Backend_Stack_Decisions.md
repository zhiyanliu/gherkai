# Backend Stack Decisions

> 17 nodes · cohesion 0.13

## Key Concepts

- **gherkai deploy push-worker（八步流程）** (5 connections) — `docs/adr/0038-worker-image-delivery.md`
- **BackendStack 资源清单（DDB/S3/ECS/IAM/SSM/Lambda）** (4 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **preflight fail-fast（探资源存在性、点名 prefix）** (3 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **版本 skew 检查（三态）** (3 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **steps/ 定制面 + RunMeta.steps_dir** (3 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **两层命名：prefix 批量默认 + 单资源覆盖** (2 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **VPC 来源三档（复用/默认/建新，零 NAT）** (2 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **RunMeta.extra_http_headers（额外请求头通道）** (2 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **--list-deterministic dump 模式 / CLI 子命令** (2 connections) — `docs/adr/0036-deterministic-capability-discovery.md`
- **gherkai deploy（IaC 进 wheel、provider 中立）** (2 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **清理 pass（退休 tag + 静默期 + 在跑 run 安全阀）** (2 connections) — `docs/adr/0038-worker-image-delivery.md`
- **默认指针 worker-default** (2 connections) — `docs/adr/0038-worker-image-delivery.md`
- **variant（具名 step 集 = 一个定制镜像）** (2 connections) — `docs/adr/0038-worker-image-delivery.md`
- **task role IAM 最小权限（动作 × 资源两维收窄）** (1 connections) — `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- **--match-steps 批量匹配 + plan 命中标注** (1 connections) — `docs/adr/0036-deterministic-capability-discovery.md`
- **uv workspace 五包 + 三名分离 + git tag 版本 lockstep** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **names.image_tag / ecr_repo_name（tag 命名真源）** (1 connections) — `docs/adr/0038-worker-image-delivery.md`

## Relationships

- [Status & Timeout Mechanisms](Status_%26_Timeout_Mechanisms.md) (2 shared connections)

## Source Files

- `docs/adr/0033-iac-aws-backend-and-composition-wiring.md`
- `docs/adr/0035-local-app-testing-via-tunnel.md`
- `docs/adr/0036-deterministic-capability-discovery.md`
- `docs/adr/0037-distribution-and-packaging.md`
- `docs/adr/0038-worker-image-delivery.md`

## Audit Trail

- EXTRACTED: 19 (95%)
- INFERRED: 1 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*