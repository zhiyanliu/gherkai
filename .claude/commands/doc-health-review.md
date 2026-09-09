---
description: 文档健康度复盘（全部项目文档对照 code 拉齐、去漂移）
---

Read `docs/doc-health-review.md` 并**严格按其中记录的方法**执行文档健康度复盘任务。

要点（细节以 `docs/doc-health-review.md` 为准，不在此复制以免漂移）：
- 这是重活，覆盖全部项目文档——起 workflow 并行审计，别单线程扫。
- 文件里标 **【强制】** 的步骤不可跳过：STALE 类必对照 code 核实、客观类必对抗验证、**必做提纯/密度审计（审计集 = 全部 ADR + CONTEXT，git 历史层读+具名审计记录，空槽=复盘未完成）**、必做 cross-ADR 视角。
- **引用方向合规**是维度之一：长期文档（ADR/CONTEXT/README）不得引用 `docs/journey/`、不得用裸 WP 编号（悬空指针）；Accepted ADR 必自包含。判据权威在 CLAUDE.md 文档纪律，检查法在 `docs/doc-health-review.md`。
- 客观类（矛盾/过时/坏链接）直接改——**但 code 偏离 ADR 已定设计的不一致不改文档**，报操作者裁定并移交 code-health；主观类（压缩/重组/施工叙事提纯）先出报告待操作者批。
