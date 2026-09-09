# Release & CI Setup

> 13 nodes · cohesion 0.15

## Key Concepts

- **CI 与发布链（`.github/`）** (7 connections) — `.github/workflows/README.md`
- **一次性人工前置（可一遍做完）** (6 connections) — `.github/workflows/README.md`
- **两条工作流** (2 connections) — `.github/workflows/README.md`
- **1. PyPI 占名（先于一切）** (1 connections) — `.github/workflows/README.md`
- **2. PyPI trusted publisher × 5（只有真发行的五个需要）** (1 connections) — `.github/workflows/README.md`
- **3. npm trusted publisher（免 token，无 secret）** (1 connections) — `.github/workflows/README.md`
- **4. GHCR：首次推送后把两个 package 改成 public** (1 connections) — `.github/workflows/README.md`
- **5. 仓库本身必须是 public** (1 connections) — `.github/workflows/README.md`
- **`release.yml` 的 job 图与重跑语义** (1 connections) — `.github/workflows/README.md`
- **TestPyPI 演练（推正式 tag 之前排一次）** (1 connections) — `.github/workflows/README.md`
- **两态基底 Dockerfile 的本地态 build（不发行也能验镜像）** (1 connections) — `.github/workflows/README.md`
- **本地静态校验（不推 tag 也能查大部分）** (1 connections) — `.github/workflows/README.md`
- **维护** (1 connections) — `.github/workflows/README.md`

## Relationships

- [Architecture Decision Records](Architecture_Decision_Records.md) (1 shared connections)

## Source Files

- `.github/workflows/README.md`

## Audit Trail

- EXTRACTED: 13 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*