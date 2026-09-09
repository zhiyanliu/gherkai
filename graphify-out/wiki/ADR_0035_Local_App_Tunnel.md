# ADR 0035 Local App Tunnel

> 10 nodes · cohesion 0.20

## Key Concepts

- **0035. 本地应用测试：自动隧道把开发机上的被测应用暴露给云端浏览器** (6 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **决策** (5 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **1. `TunnelProvider` 可插拔口子（`gherkai-runtime` 组合根共享层），首个实现 = ngrok** (1 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **2. URL 映射：feature 写原始地址，组装 job 时替换** (1 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **3. 四种「跑法 × backend」组合全支持；隧道生命周期按宿主分三形态** (1 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **4. `ngrok-skip-browser-warning` 头恒注入（仅隧道模式）** (1 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **背景与问题** (1 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **被拒/被缓方案（护栏）** (1 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **调研结论（内联，自包含）** (1 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`
- **边界与不变量** (1 connections) — `docs/adr/0035-local-app-testing-via-tunnel.md`

## Relationships

- [Architecture Decision Records](Architecture_Decision_Records.md) (1 shared connections)

## Source Files

- `docs/adr/0035-local-app-testing-via-tunnel.md`

## Audit Trail

- EXTRACTED: 10 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*