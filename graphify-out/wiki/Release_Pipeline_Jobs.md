# Release Pipeline Jobs

> 5 nodes · cohesion 0.50

## Key Concepts

- **release job: base image（GHCR）** (4 connections) — `.github/workflows/release.yml`
- **release job: gate + build** (2 connections) — `.github/workflows/release.yml`
- **release job: publish npm** (2 connections) — `.github/workflows/release.yml`
- **release job: publish PyPI** (2 connections) — `.github/workflows/release.yml`
- **release job: GitHub Release** (1 connections) — `.github/workflows/release.yml`

## Relationships

- [CLI Docs and ADRs](CLI_Docs_and_ADRs.md) (1 shared connections)

## Source Files

- `.github/workflows/release.yml`

## Audit Trail

- EXTRACTED: 6 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*