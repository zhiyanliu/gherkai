# Packaging & Distribution ADR

> 24 nodes · cohesion 0.08

## Key Concepts

- **0037. 分发与打包：PyPI 多包 workspace（uv-first）+ `gherkai deploy` 进 wheel** (18 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **决策 2：Python 侧 = uv workspace 多包发布，PyPI + uv-first** (5 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **背景与问题** (3 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **2a. 三名分离：发行名 / import 名 / 命令名各自取，约束只有一条** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **2b. 版本：git tag 唯一真源，兄弟包 `==` lockstep pin，不做兼容矩阵** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **2c. extras 边界：`[aws]` 只在库层，CLI 上两个正交 extra** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **2d. `requires-python >=3.13` 维持** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **业界现状（2026，为选型提供的外部事实；一手来源登记在 [docs/REFERENCES.md](../REFERENCES.md)「分发与打包」节）** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **决策 1：交付物按打包技术划分，worker 运行时是硬核** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **决策 3：worker 运行时的交付——安装与拉起正交，四级定位链，`repo_root()` 全部消费点退役** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **决策 4：确定性 step 的定制面——`steps/` 目录约定 + env 注入，local/cloud 同一机制** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **决策 5：worker 镜像两层分工——维护者 GHCR 基底 + 使用方定制层（机制见 0038）** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **决策 6：部署 = `gherkai deploy`——命令 provider 中立，分发单元带 provider** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **决策 7：版本单旋钮贯穿 + skew 检查（三态齐全）** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **决策 8：CI 发布链与占名** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **决策总览** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **实测项（**已清零**；「绿≠对」——每条都依赖 mock 之外的真实行为，证据内联于各条）** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **对既有 ADR 的影响（反向链已落各 Status 头；本 ADR 翻 Accepted 时标注已同步）** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **对既有文档与 code 注释的影响（校准清单，翻 Accepted 时已逐条完成；括注是当时的到期点，路径名为当时的路径）** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **工程布局（目标态；[0016](./0016-execution-architecture-core-lib-run-model.md) 布局图在发行重组实装后据此校准）** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **施工前现状实测（历史快照——本 ADR 的证据基座；下列每一条今已被决策 1–8 改变）** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **落地次序与依赖（依赖关系，非进度追踪；本节编号只在本节内部使用，其它文档不引用它）** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **被拒方案（护栏，防未来重踩）** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`
- **重议闸门** (1 connections) — `docs/adr/0037-distribution-and-packaging.md`

## Relationships

- [ADR Index & Dev Docs](ADR_Index_%26_Dev_Docs.md) (1 shared connections)

## Source Files

- `docs/adr/0037-distribution-and-packaging.md`

## Audit Trail

- EXTRACTED: 24 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*