# 项目自写的确定性 step（Nova Act 引擎）。
from gherkai_worker_novaact.deterministic import deterministic


@deterministic(r'元素 "(?P<sel>[^"]+)" 可见',
               description="断言选择器命中的元素可见（精确判定，不走 AI）",
               example='Then 元素 "#cart-count" 可见')
def element_visible(ctx, sel):
    assert ctx.page.locator(sel).is_visible()
