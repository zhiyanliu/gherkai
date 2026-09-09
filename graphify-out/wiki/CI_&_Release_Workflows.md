# CI & Release Workflows

> 10 nodes · cohesion 0.33

## Key Concepts

- **release.yml 发布链** (7 connections) — `.github/workflows/release.yml`
- **gherkai_cli.__main__ argparse 皮** (6 connections) — `cli/DEVELOPMENT.md`
- **release images job（GHCR 基底镜像）** (5 connections) — `.github/workflows/release.yml`
- **版本单旋钮（git tag 真源 + skew 三态）** (4 connections) — `CONTEXT.md`
- **CI 与发布链说明** (3 connections) — `.github/workflows/README.md`
- **release build job（gate + uv build）** (3 connections) — `.github/workflows/release.yml`
- **release npm job（@gherkai/worker-midscene）** (3 connections) — `.github/workflows/release.yml`
- **release pypi job（attest + uv publish）** (3 connections) — `.github/workflows/release.yml`
- **ci.yml 工作流** (2 connections) — `.github/workflows/ci.yml`
- **release GitHub Release job** (2 connections) — `.github/workflows/release.yml`

## Relationships

- [Deploy Docs](Deploy_Docs.md) (2 shared connections)
- [Run Result Rendering](Run_Result_Rendering.md) (2 shared connections)
- [Deploy Provider Discovery](Deploy_Provider_Discovery.md) (1 shared connections)
- [SSM Path & Client Composition](SSM_Path_%26_Client_Composition.md) (1 shared connections)
- [Architecture Decision Records](Architecture_Decision_Records.md) (1 shared connections)
- [Domain Glossary](Domain_Glossary.md) (1 shared connections)

## Source Files

- `.github/workflows/README.md`
- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`
- `CONTEXT.md`
- `cli/DEVELOPMENT.md`

## Audit Trail

- EXTRACTED: 22 (96%)
- INFERRED: 1 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*