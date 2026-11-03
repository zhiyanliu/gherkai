# 手机 Chrome 上的维基百科冒烟用例（Device Farm 上的 Android 设备）。
@engine:midscene @device:android
Feature: 手机上的维基百科

  @scope:wiki-browse
  Scenario: 打开 OpenAI 词条
    Given "https://en.wikipedia.org/wiki/OpenAI"
    Then "当前是 OpenAI 的维基百科词条页"

  @scope:wiki-browse
  Scenario: 从首页搜索 Python
    Given "https://en.wikipedia.org/wiki/Main_Page"
    Then "当前页面是英文维基百科的首页"
    When "在搜索框输入 Python 并提交搜索"
    Then "页面显示与 Python 相关的词条或搜索结果"

  @scope:wiki-browse
  Scenario: 打开 Linux 词条
    Given "https://en.wikipedia.org/wiki/Linux"
    Then "当前是 Linux 的维基百科词条页"

  @scope:wiki-mobile-url
  Scenario: OpenAI 词条的地址精确核对
    Given "https://en.m.wikipedia.org/wiki/OpenAI"
    Then 页面地址匹配 "^https://en\.m\.wikipedia\.org/wiki/OpenAI$"
