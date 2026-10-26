"""项目自写的确定性 step（Nova Act 引擎）：断言当前页面地址匹配给定正则。与 steps/url_matches.mts 成对：同一正则、同一元数据。"""
import re

from gherkai_worker_novaact.deterministic import deterministic


@deterministic(r'页面地址匹配 "(?P<pattern>[^"]+)"',  # [^"]+（非 .+）：防 step 里出现第二对引号时贪婪跨引号捕获
               description="断言当前页面地址匹配给定正则（精确判定，不走 AI、不投票）",
               example='Then 页面地址匹配 "/wiki/OpenAI"',
               keywords=("Then",))
def url_matches(ctx, pattern: str) -> None:
    url = ctx.page.url
    assert re.search(pattern, url), f"页面地址应匹配 {pattern!r}，实际 {url!r}"
