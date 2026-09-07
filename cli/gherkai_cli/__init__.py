"""cli：产品本体 gherkai 的命令行皮（ADR 0016「演进」节）。

__main__（argparse 皮）+ render（表层渲染）。组合根逻辑在平级包 gherkai（compose/detached/names），
本包只接线 + 表层 IO——Lambda/未来 WebUI 是 gherkai 的另两张皮、不经本包。
"""
