Feature: 首页冒烟

  Scenario: 首页能打开
    Given 打开 "https://example.com/"
    Then "页面上能看到大标题 Example Domain"
    Then 页面标题包含 "Example Domain"
