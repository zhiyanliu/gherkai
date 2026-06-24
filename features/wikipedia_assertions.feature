# v0.x 断言能力打磨：默认 AI 判断（纯人话）+ 否定断言。两腿都跑。
Feature: 维基断言能力打磨

  Scenario: AI 断言 + 否定断言（纯人话，无路由关键词）
    Given 打开 "https://www.wikipedia.org/"
    # 否定/不存在断言 → 直接写人话，默认 AI 判（AI 能理解否定陈述）
    Then "页面没有出现服务器错误"
    # 取数意图 → 直接写人话让 AI 判（不必"取数再比较"）
    Then "页面上展示的语言版本超过 5 种"
    When "在搜索框输入 OpenAI 并提交搜索"
    # 取文本意图 → 同样人话
    Then "词条首段提到了 artificial intelligence"
