# Tunnel & Capability ADRs

> 22 nodes · cohesion 0.14

## Key Concepts

- **ADR 0037 分发与包化** (22 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **ADR 0035 经隧道测试本地应用** (10 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **ADR 0036 确定性能力自述** (8 connections) — `docs/adr/0036-deterministic-capability-discovery.md`
- **worker --capabilities 能力自述入口** (6 connections) — `docs/adr/0036-deterministic-capability-discovery.md`
- **版本 skew 三态检查（SSM 版本戳 vs CLI 版本）** (6 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **steps/ 目录约定与 GHERKAI_STEPS_DIR 随 definition 走** (5 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **gherkai doctor 只读自检（按组件分组、required 项定退出码）** (5 connections) — `docs/adr/0041-agent-facing-cli-affordances.md`
- **ADR 0034 无状态批量运行的事件链** (4 connections) — `docs/adr/0034-detached-batch-reconciler.md`
- **RunMeta.extra_http_headers 与 ngrok-skip-browser-warning 注入** (3 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **TunnelProvider 可插拔口子（首实现 ngrok）** (3 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **ADR 0011 AgentCore 浏览器层：默认 vs 自建** (2 connections) — `docs/adr/0011-agentcore-browser-system-default-vs-custom.md`
- **--expose-local 与 job 组装期 URL 前缀替换** (2 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **隧道生命周期按宿主分三形态** (2 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **TTL 按 definition 计算（compute_watch_ttl_s）** (2 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **CLI list-deterministic --engine** (2 connections) — `docs/adr/0036-deterministic-capability-discovery.md`
- **确定性 step 注册必带 description/example 元数据** (2 connections) — `docs/adr/0036-deterministic-capability-discovery.md`
- **git tag 唯一版本真源 + 兄弟包 == 同版本 pin** (2 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **worker 四级定位链（取代 repo_root）** (2 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **gherkai skill install（整目录收敛 + 版本标记）** (2 connections) — `docs/adr/0043-agent-skill-for-driving-gherkai.md`
- **plan 命中标注与 --match-steps 批量匹配** (1 connections) — `docs/adr/0036-deterministic-capability-discovery.md`
- **gherkai deploy：IaC 进 wheel、provider 发现** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **三名分离：发行名 / import 名 / 命令名** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`

## Relationships

- [AWS Architecture ADRs](AWS_Architecture_ADRs.md) (10 shared connections)
- [Architecture ADRs (Core)](Architecture_ADRs_%28Core%29.md) (8 shared connections)
- [Docs & Terminology ADRs](Docs_%26_Terminology_ADRs.md) (7 shared connections)
- [AWS Deploy Package Docs](AWS_Deploy_Package_Docs.md) (2 shared connections)
- [Contributor Guardrail Docs](Contributor_Guardrail_Docs.md) (2 shared connections)

## Source Files

- `docs/adr/0011-agentcore-browser-system-default-vs-custom.md`
- `docs/adr/0034-detached-batch-reconciler.md`
- `docs/adr/0035-local-app-testing-via-tunnel.md`
- `docs/adr/0036-deterministic-capability-discovery.md`
- `docs/adr/0037-distribution-and-packaging.md`
- `docs/adr/0041-agent-facing-cli-affordances.md`
- `docs/adr/0043-agent-skill-for-driving-gherkai.md`

## Audit Trail

- EXTRACTED: 61 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*