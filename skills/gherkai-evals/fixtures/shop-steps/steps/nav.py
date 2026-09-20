# 项目自写的确定性 step（Nova Act 引擎）。
import re

from playwright.sync_api import expect

from gherkai_worker_novaact.deterministic import deterministic


@deterministic(r'页面标题包含 "(?P<text>[^"]+)"',
               description="断言页面标题包含给定文本（精确判定，不走 AI）",
               example='Then 页面标题包含 "示例商店"')
def title_contains(ctx, text):
    try:
        expect(ctx.page).to_have_title(re.compile(re.escape(text)), timeout=5000)
    except AssertionError as e:
        raise AssertionError(f"标题应包含 {text!r}，实际 {ctx.page.title()!r}（页面 {ctx.page.url}）") from e
