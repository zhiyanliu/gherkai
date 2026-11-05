"""cli：产品本体 gherkai 的命令行前端（ADR 0016「演进」节）。

本包只负责参数解析、接线与表层 IO，各模块的职责见 cli/DEVELOPMENT.md「模块」节；`skills/` 是随 wheel
发行的包数据、不是 code。部署命令面不含 IaC，IaC 位于 provider 包 `gherkai-deploy-aws`（ADR 0037 决策 6）。
组合根逻辑在平级包 gherkai_runtime（runtime/，模块职责见 runtime/DEVELOPMENT.md「模块」节）；Lambda 与未来的
WebUI 是 gherkai_runtime 的另两个前端、不经本包。
"""
