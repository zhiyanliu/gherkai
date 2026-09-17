# docs/ai-eng 索引

给**构建本工具的 AI coding agent** 的工作文档，与 [`docs/adr/`](../adr/)、[`CONTEXT.md`](../../CONTEXT.md)、[`CLAUDE.md`](../../CLAUDE.md) 同属一类读者；那三处位置固定（工具有位置依赖），其余归本目录。分类的决策见 [ADR 0045](../adr/0045-documentation-layering-and-placement.md)。

| 文件 | 是什么 | 谁在什么时候读 |
|---|---|---|
| [`REFERENCES.md`](./REFERENCES.md) | 外部一手来源登记（SDK / AWS 文档 / 规范 / 源码内的自查点），ADR 里的「业界现状」与选型事实从这里溯源 | 写或校准 ADR 时 |
| [`doc-health-review.md`](./doc-health-review.md) | 文档健康度复盘的**可复用任务指令**：六类问题、【强制】步骤、提纯审计、跨轮锚点 | 经 `.claude/commands/doc-health-review.md` 触发的 agent |
| [`code-health-review.md`](./code-health-review.md) | 代码健康度复盘的可复用任务指令：DEAD / STALE_INEFFICIENT / VIOLATES_ADR、热区、对抗验证 | 经 `.claude/commands/code-health-review.md` 触发的 agent |

写法约定与 ADR 相同：高密度、单一事实源、精确指针；不复述 ADR 的决策与理由。
