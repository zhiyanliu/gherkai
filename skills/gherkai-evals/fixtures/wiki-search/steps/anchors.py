# 项目自写的确定性 step（Nova Act 引擎，Python）。与 steps/anchors.mts 成对：同一正则、同一元数据。
from gherkai_worker_novaact.deterministic import deterministic


@deterministic(r'页面标题包含 "(?P<word>[^"]+)"',
               description="精确检查浏览器标题是否包含给定文字（不走 AI）",
               example='Then 页面标题包含 "Python"')
def title_contains(ctx, word):
    title = ctx.page.title()
    assert word in title, f"页面标题应包含 {word!r}，实际是 {title!r}"
