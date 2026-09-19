---
name: doc-diagram
description: 在本仓库新增、修改或调整 docs/diagrams/ 下的文档图（架构 / 流程 / 时序 / 数据流 / 状态图）时用：给某页配图、把一段文字画成图、按评审意见改布局、重导 SVG。它先读本项目的作图方法与布局清单，再调 archify 作者化与校验，最后用 tools/build_diagrams.mjs 构建导出。用户提到「画图 / 配图 / 改图 / 调布局 / 出图 / 重导 SVG」或点名 docs/diagrams 里的图名时触发。
---

读 `docs/ai-eng/diagram-authoring.md` 并**严格按其中的流程、内容规则、布局清单与技法**执行，不要退化成「照 mermaid 拓扑随手转一张」。作者化与校验用 `archify` skill，构建与导出用 `tools/build_diagrams.mjs`，校验档、PNG 自检与交付要求（JSON 与 SVG 同 commit 等）按方法文档的步骤 4、5、7。
