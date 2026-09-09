# CI and Release Workflows

> 10 nodes · cohesion 0.33

## Key Concepts

- **release.yml 发布链** (7 connections) — `.github/workflows/release.yml`
- **gherkai_cli.__main__ argparse 皮** (6 connections) — `cli/DEVELOPMENT.md`
- **release images job（GHCR 基底镜像）** (5 connections) — `.github/workflows/release.yml`
- **CI 与发布链说明** (4 connections) — `.github/workflows/README.md`
- **版本单旋钮（git tag 真源 + skew 三态）** (4 connections) — `CONTEXT.md`
- **release build job（gate + uv build）** (3 connections) — `.github/workflows/release.yml`
- **release npm job（@gherkai/worker-midscene）** (3 connections) — `.github/workflows/release.yml`
- **release pypi job（attest + uv publish）** (3 connections) — `.github/workflows/release.yml`
- **ci.yml 工作流** (2 connections) — `.github/workflows/ci.yml`
- **release GitHub Release job** (2 connections) — `.github/workflows/release.yml`

## Relationships

- [ADR Index & Dev Docs](ADR_Index_%26_Dev_Docs.md) (2 shared connections)
- [Deploy AWS README](Deploy_AWS_README.md) (2 shared connections)
- [Deploy Provider Discovery](Deploy_Provider_Discovery.md) (1 shared connections)
- [Run Result Verdict Model](Run_Result_Verdict_Model.md) (1 shared connections)
- [Plan Command & Rendering](Plan_Command_%26_Rendering.md) (1 shared connections)
- [Composition Root Wiring](Composition_Root_Wiring.md) (1 shared connections)
- [Domain Glossary](Domain_Glossary.md) (1 shared connections)

## Source Files

- `.github/workflows/README.md`
- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`
- `CONTEXT.md`
- `cli/DEVELOPMENT.md`

## Audit Trail

- EXTRACTED: 23 (96%)
- INFERRED: 1 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*