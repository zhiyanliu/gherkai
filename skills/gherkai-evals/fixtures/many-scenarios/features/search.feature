Feature: 词条检索（英文维基）

  @smoke
  Scenario: 搜索并进入词条页
    Given 打开 "https://en.wikipedia.org/wiki/Main_Page"
    When "在搜索框输入 Gherkin 并提交搜索"
    Then "当前是关于 Gherkin 的词条页或消歧义页"

  Scenario: 词条页有目录
    Given 打开 "https://en.wikipedia.org/wiki/Cucumber"
    Then "页面上有一个可展开的目录"

  Scenario: 随机词条能打开
    Given 打开 "https://en.wikipedia.org/wiki/Special:Random"
    Then "打开了一个词条页，没有报错"

  Scenario Outline: 打开词条 <name>
    Given 打开 "https://en.wikipedia.org/wiki/Main_Page"
    When "在搜索框输入 <name> 并提交搜索"
    Then 页面地址匹配 "/wiki/<slug>"

    Examples:
      | name   | slug   |
      | Python | Python |
      | Rust   | Rust   |
