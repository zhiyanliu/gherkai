Feature: 词条浏览

  Background:
    Given 打开 "https://en.wikipedia.org/wiki/Main_Page"

  @scope:deep-dive @timeout:20
  Scenario: 长流程：搜索、进入词条、跳到历史一节
    When "在搜索框输入 Python 并提交搜索"
    Then "当前是 Python 的词条页"
    When "点击目录里的 History 链接"
    Then "页面滚到了 History 一节"

  Scenario Outline: 打开词条 <name>
    When "在搜索框输入 <name> 并提交搜索"
    Then 页面地址匹配 "/wiki/<slug>"

    Examples:
      | name   | slug   |
      | Python | Python |
      | Rust   | Rust   |
