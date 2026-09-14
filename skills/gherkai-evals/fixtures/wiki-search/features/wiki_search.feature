# 评测 fixture：英文维基（Nova Act 默认引擎）。第一条 scenario 最后一步是刻意写错的事实断言，
# 用来录一份带失败证据的 run；第二条不标 scope、演示 <文件>:<行号> 形态的 scope_id 与项目自写的确定性 step。
Feature: 维基百科搜索

  @scope:search
  Scenario: 搜索 OpenAI 并进入词条页
    Given 打开 "https://en.wikipedia.org/wiki/Main_Page"
    When "在搜索框输入 OpenAI 并提交搜索"
    Then 页面地址匹配 "/wiki/OpenAI"
    Then "当前是关于 OpenAI 的维基百科词条页"
    Then "词条首段说 OpenAI 成立于 1999 年"

  Scenario: 词条标题的精确检查
    Given 打开 "https://en.wikipedia.org/wiki/Python_(programming_language)"
    Then 页面标题包含 "Python"
    Then "页面右侧的信息框里列出了最新稳定版本号"
