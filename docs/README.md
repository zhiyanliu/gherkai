# 文档地图

本仓库的文档按**读者**分三类。找文档先看自己是谁，再进对应的入口；每个入口页同时是该类的索引与「谁负责讲什么」的表。分层的决策与理由见 [ADR 0045](./adr/0045-documentation-layering-and-placement.md)。

| 你是 | 从这里进 | 这一类里还有什么 |
|---|---|---|
| **使用者**（写 `.feature`、跑测试、看结果的人，以及替你操作的 AI agent） | [`user-guide/`](./user-guide/README.md) | 仓库首页 [`README.md`](../README.md)（门面与 30 秒上手）；各发行包的页面（[`gherkai`](https://pypi.org/project/gherkai/)、[`@gherkai/worker-midscene`](https://www.npmjs.com/package/@gherkai/worker-midscene) 等，只是入口，细节都在 user guide）；每版变更 [`CHANGELOG.md`](../CHANGELOG.md)；随 CLI 发行的 agent skill（`gherkai skill install`） |
| **contributor**（改代码、跑测试、发版的人） | 根 [`CONTRIBUTING.md`](../CONTRIBUTING.md) | 各包目录下的 `DEVELOPMENT.md`（该包的模块布局、从 checkout 跑、测试）；发布链与一次性前置 [`.github/workflows/README.md`](../.github/workflows/README.md) |
| **想懂机理的技术读者**（架构、执行模型、云端载体） | [`internals/`](./internals/README.md) | 每篇只讲系统如何运转（how），权威在 ADR 与代码 |
| **构建本工具的 AI coding agent** | [`CLAUDE.md`](../CLAUDE.md)（项目约定） | [`adr/`](./adr/)（稳定决策：what / why / trade-off）；[`CONTEXT.md`](../CONTEXT.md)（领域概念与术语）；[`ai-eng/`](./ai-eng/README.md)（外部一手来源、复盘方法）；`journey/`（跨会话任务的过程暂存，随任务收尾清空） |

## 三条阅读规则

- **权威在 ADR 与代码**。user guide 与 internals 都是派生视图：与 ADR 或代码冲突时以后者为准，并提 issue 或直接修正文档。
- **一个主题只有一篇是 owner**。同一件事只在一处展开，其余地方给链接。各类入口页的表就是 owner 表。
- **口吻随读者变**。用户文档是产品说明（陈述句、任务导向、不用隐喻和内部说法）；contributor 与 internals 文档是技术说明；ADR 与 CONTEXT 为 AI 检索优化、密度高。
