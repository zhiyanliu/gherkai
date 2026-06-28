# e2e 验证 feature（非 QA 用例）：验证 scope 间并发 + scope 内串行共享会话 + cost 汇总。
# 用 wikipedia 稳定站点（ADR：骨架验证用例）。每个 scenario 尽量短，控制烧钱。
#
# 结构（ADR 0019）：
#   @scope:browse —— 含 2 个 scenario，验证「scope 内串行、共享同一会话」：
#       第 1 个导航到 OpenAI 词条；第 2 个**不重新导航**，直接断言「仍在 OpenAI 词条页」
#       —— 只有真共享会话（同一浏览器、保留上一 scenario 的页面状态）才能过。
#   @scope:search —— 独立 scope，与 browse 并发跑（验证 scope 间并行 + 多 AgentCore 会话）。
Feature: 并发与 scope 共享会话验证

  @scope:browse
  Scenario: 进入 OpenAI 词条页
    Given 打开 "https://en.wikipedia.org/wiki/OpenAI"
    Then "当前页面是关于 OpenAI 的维基百科词条"

  @scope:browse
  Scenario: 仍停留在 OpenAI 词条页（验证共享会话，不重新导航）
    Then "当前仍停留在 OpenAI 的维基百科词条页"

  @scope:search
  Scenario: 搜索并进入 Python 词条
    Given 打开 "https://www.wikipedia.org/"
    When "在搜索框输入 Python 并提交搜索"
    Then "当前页面是关于 Python 编程语言的维基百科词条"
