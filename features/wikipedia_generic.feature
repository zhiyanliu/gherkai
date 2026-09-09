# v0.x 通用 step 风格——QA 只写这个文件，零 step 代码、零路由关键词（ADR 0020）。
# Then 后跟纯人话陈述 → 默认走 AI 判断。确定性精确检查（少数派）由测试开发
# 在 deterministic.steps 自建，不在这里预置。
Feature: Wikipedia 搜索（通用 step 风格）

  Scenario: 搜索 OpenAI 并进入词条
    Given 打开 "https://www.wikipedia.org/"
    When "在搜索框输入 OpenAI 并提交搜索"
    Then "当前页面是关于 OpenAI 的维基百科词条页"
