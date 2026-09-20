"""adapters：ports 的具体实现，由组合根注入（ADR 0016 窄腰 + 注入红线：adapter 不 env-sniff 自选实现）。

每个 port 一个子包、同一 port 的 local 与云端后端并列在包内（多后端不按后端混放）；Engine 与 Launcher 例外——
实装即顶层模块。`EventLog`/`Launcher` 两个 port 定义在 `reconcile.py`、其余在 `ports.py`（ADR 0034）。
`_` 前缀模块是 adapter 间共享的私有件、非 port 实装；云端 adapter 需 `aws` extra（守卫见 `_boto.py`，
那是冗余兜底，主拦截在组合根）。清单真值集就是本目录，对照 ADR 0016「adapters 按 port 分子目录」树。
"""
