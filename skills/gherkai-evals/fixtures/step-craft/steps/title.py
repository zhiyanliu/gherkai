# 项目自写的确定性 step（Nova Act 引擎）。
from gherkai_worker_novaact.deterministic import deterministic


@deterministic(r'页面标题包含 "(?P<text>[^"]+)"',
               description="断言页面标题包含给定文本（精确判定，不走 AI）",
               example='Then 页面标题包含 "示例商店"')
async def title_contains(ctx, text):
    title = ctx.page.title()
    assert text in title, f"标题 {title!r} 不含 {text!r}"
