# Report Store Output

> 7 nodes · cohesion 0.29

## Key Concepts

- **ReportStore.write（整 run 一次写）** (4 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **href 相对化（local 相对 / cloud 恒等 ref）** (2 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **index.html（判定明细树 + 产物导航）** (2 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **JobResult 持有 Job、engine 经 property delegate** (1 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **manifest.json（薄信封 + 扁平 report_index）** (1 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **被拒方案：materialize 产物拷贝** (1 connections) — `docs/adr/0027-runreport-aggregation-index.md`
- **run_id（归集索引主键，组合根生成）** (1 connections) — `docs/adr/0027-runreport-aggregation-index.md`

## Relationships

- No strong cross-community connections detected

## Source Files

- `docs/adr/0027-runreport-aggregation-index.md`

## Audit Trail

- EXTRACTED: 6 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*