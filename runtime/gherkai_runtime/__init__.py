"""gherkai：产品本体 = 组合根共享层（ADR 0016「演进」节）。

持有产品级知识——引擎注册表与装配（compose）、local 无状态跑批宿主（detached）、资源命名真源（names）、
隧道与其宿主编排（tunnel / tunnel_host，ADR 0035）。
cli 与 Lambda 是它的两个入口（入口 → gherkai_runtime → core，窄腰红线不变：引擎知识不进 core），入口只做参数解析与呈现。
"""
