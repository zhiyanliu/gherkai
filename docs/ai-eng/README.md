# docs/ai-eng 索引

本目录存放维护本仓库时用的工作文档，主要读者是 contributor 侧 AI agent，维护者也会读。[`docs/adr/`](../adr/)、[`CONTEXT.md`](../../CONTEXT.md)、[`CLAUDE.md`](../../CLAUDE.md) 与它同属一类，只是位置固定（工具有位置依赖），其余归这里。分类的决策见 [ADR 0045](../adr/0045-documentation-layering-and-placement.md)。

| 文件 | 是什么 | 谁在什么时候读 |
|---|---|---|
| [`REFERENCES.md`](./REFERENCES.md) | 外部一手来源登记（SDK / AWS 文档 / 规范 / 源码内的自查点），ADR 里的「业界现状」与选型事实从这里溯源 | 写或校准 ADR 时 |
| [`doc-health-review.md`](./doc-health-review.md) | 文档健康度复盘的**可复用任务指令**：六类问题、【强制】步骤、提纯审计、跨轮锚点 | 经 `.claude/commands/doc-health-review.md` 触发的 agent |
| [`code-health-review.md`](./code-health-review.md) | 代码健康度复盘的可复用任务指令：DEAD / STALE_INEFFICIENT / VIOLATES_ADR、热区、对抗验证 | 经 `.claude/commands/code-health-review.md` 触发的 agent |

写法约定与 ADR 相同：高密度、单一事实源、精确指针；不复述 ADR 的决策与理由。
