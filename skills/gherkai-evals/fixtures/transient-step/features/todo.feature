Feature: 待办清单

  @engine:midscene
  Scenario: 删除后立刻撤销
    Given 打开 "http://localhost:8080"
    When 删除 "买牛奶" 后立刻撤销，条目仍在
    Then "列表里仍有三条待办"

  Scenario: Delete then undo (English mirror)
    Given 打开 "http://localhost:8080"
    When 删除 "买牛奶" 后立刻撤销，条目仍在
    Then "the list still shows three items"
