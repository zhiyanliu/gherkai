Feature: 本机开发中的待办应用

  Scenario: 首页可达
    Given 打开 "http://127.0.0.1:3000/"
    Then "页面标题是待办清单"
    Then "页面上有一个新增待办的输入框"

  Scenario: 新增一条待办
    Given 打开 "http://127.0.0.1:3000/"
    When "在输入框里输入 买牛奶 并回车"
    Then "列表里出现了 买牛奶"
