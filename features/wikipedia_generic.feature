# v0.x 验证：通用 step 风格——QA 只写这个文件，零 step 代码。
# 句子是自然语言 + 半结构化混用（ADR 0015）：When/Then 直接喂自然语言给 AI；
# 「页面地址包含」是确定性断言锚点（不靠 AI，给精确检查留入口）。
Feature: Wikipedia 搜索（通用 step 风格）

  Scenario: 搜索 OpenAI 并进入词条
    Given 打开 "https://www.wikipedia.org/"
    When AI 执行 "在搜索框输入 OpenAI 并提交搜索"
    Then AI 确认 "当前页面是关于 OpenAI 的维基百科词条页"
    And 页面地址包含 "/wiki/OpenAI"
