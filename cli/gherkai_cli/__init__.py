"""cli：产品本体 gherkai 的命令行前端（ADR 0016「演进」节）。

`__main__`（argparse 前端）+ `render`（表层渲染）+ `deploy`（`deploy`/`destroy` 命令面：provider 发现与 flag 接线，
不含 IaC——那些住 provider 包 `gherkai-deploy-aws`，ADR 0037 决策 6）+ `skill_install`（把包数据
`skills/gherkai/` 那份 agent skill 收敛安装进使用方项目，ADR 0043 决策一、三）；`skills/` 是随 wheel 发行的
包数据、不是 code。组合根逻辑在平级包 gherkai_runtime（runtime/，compose/detached/names/tunnel/tunnel_host），
本包只接线 + 表层 IO——Lambda/未来 WebUI 是 gherkai_runtime 的另两个前端、不经本包。
"""
