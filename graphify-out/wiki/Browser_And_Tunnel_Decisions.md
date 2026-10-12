# Browser And Tunnel Decisions

> 7 nodes · cohesion 0.33

## Key Concepts

- **ADR 0035: 本地应用经隧道测试** (14 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **ADR 0011: AgentCore 浏览器 system default vs custom** (6 connections) — `docs/adr/0011-agentcore-browser-system-default-vs-custom.md`
- **自建 custom browser（create-browser）** (2 connections) — `docs/adr/0011-agentcore-browser-system-default-vs-custom.md`
- **tunnel.py（--expose-local 隧道 provider）** (2 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **系统默认浏览器 aws.browser.v1** (1 connections) — `docs/adr/0011-agentcore-browser-system-default-vs-custom.md`
- **tunnel_host.py（隧道宿主编排 + 守护 TTL）** (1 connections) — `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- **TunnelProvider 可插拔口子（首个实现 ngrok）** (1 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`

## Relationships

- [Core Library Concepts & ADRs](Core_Library_Concepts_%26_ADRs.md) (4 shared connections)
- [Model Selection ADRs](Model_Selection_ADRs.md) (3 shared connections)
- [Cloud Backend Docs & Diagrams](Cloud_Backend_Docs_%26_Diagrams.md) (2 shared connections)
- [Shared Feature Scope ADRs](Shared_Feature_Scope_ADRs.md) (2 shared connections)
- [Project Docs & Glossary](Project_Docs_%26_Glossary.md) (1 shared connections)
- [Release & Versioning Concepts](Release_%26_Versioning_Concepts.md) (1 shared connections)

## Source Files

- `docs/adr/0011-agentcore-browser-system-default-vs-custom.md`
- `docs/adr/0016-execution-architecture-core-lib-run-model.md`
- `docs/adr/0035-local-app-testing-via-tunnel.md`

## Audit Trail

- EXTRACTED: 20 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*