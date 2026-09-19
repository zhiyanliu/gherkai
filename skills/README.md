# skills/

gherkai agent skill 的源文件**不在**这里：skill 随 CLI 一起发行，源文件在 [`cli/gherkai_cli/skills/gherkai/`](../cli/gherkai_cli/skills/gherkai/)，装法见用户指南的 [`docs/user-guide/getting-started.md`](../docs/user-guide/getting-started.md)「上手路径一：交给 AI agent」。本目录只放 contributor 迭代这份 skill 用的评测资产 `gherkai-evals/`（skill 评测集、fixture、评分提示词模板；不随包发行，使用 gherkai 不需要它；资产清单与一轮评测的运行方法见 [ADR 0043](../docs/adr/0043-agent-skill-for-driving-gherkai.md) 决策七）；`gherkai-workspace/` 是评测结果的工作区，不入库。
