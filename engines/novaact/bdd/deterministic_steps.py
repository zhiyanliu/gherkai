"""确定性锚点脚手架（ADR 0020）—— 给 TEST ENGINEER（会写代码的角色），不是 QA。

用途：少数"必须精确、不容 AI 抖动"的断言（如 URL 精确、关键 DOM），用底层 Playwright
（nova.page）直接查、**不走 AI**。这是 ADR 0015 的"确定性逃生舱"。

设计（ADR 0020）：
  - 本文件**默认空**，不预置任何具体锚点 step——预置就等于要求 QA 学特定措辞，违背"QA 零预设"。
  - QA 永远只在 .feature 写人话（默认走 AI，见 test_generic_steps.py 的 Then "{claim}"）；"零代码"对 QA 成立。
  - 仅当某断言确需精确、不能容忍 AI 非确定性时，test engineer 在此加一个项目专属 step。

怎么加（示例，需要时取消注释并改成你的项目所需）：
  1) 在 .feature 里用一个**带前缀关键词**的 Then（与默认 AI 的纯 Then "{claim}" 区分开）：
       Then 页面地址包含 "/wiki/OpenAI"
  2) 在此实现该 step（wiring 已就绪：test_generic_steps.py 已 `import deterministic_steps`，
     在此加的 @then step 会自动被 pytest-bdd 收集，无需再改别处）：

  # from pytest_bdd import then, parsers
  # @then(parsers.parse('页面地址包含 "{fragment}"'))
  # def _url_contains(nova_ctx, fragment):
  #     assert fragment in nova_ctx.page.url, f'url 应含 "{fragment}"，实际 {nova_ctx.page.url}'

注意：`nova_ctx` fixture 由 test_generic_steps.py 提供（含 nova.page 这个 Playwright Page）。
Midscene 侧的对齐脚手架见 midscene/bdd/steps/deterministic.steps.ts。
"""
# 默认无 step——确定性锚点由 test engineer 按需自建（见上）。
