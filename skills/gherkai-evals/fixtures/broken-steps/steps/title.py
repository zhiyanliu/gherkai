# 项目自写的确定性 step（Nova Act 引擎）。
from gherkai_worker_novaact.deterministic import deterministic
from projecthelpers.selectors import TITLE  # 这个模块在项目里并不存在


@deterministic(r'页面标题包含 "(?P<word>[^"]+)"',
               description="精确检查浏览器标题是否包含给定文字（不走 AI）",
               example='Then 页面标题包含 "Example Domain"')
def title_contains(ctx, word):
    assert word in ctx.page.title()
