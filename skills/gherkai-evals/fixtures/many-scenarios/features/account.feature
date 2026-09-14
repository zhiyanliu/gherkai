# 登录相关用例（示例站点 the-internet.herokuapp.com）
Feature: 登录

  @scope:login-flow
  Scenario: 打开登录页
    Given 打开 "https://the-internet.herokuapp.com/login"
    Then "页面上有用户名和密码两个输入框"

  @scope:login-flow
  Scenario: 错误密码被拒
    When "用户名填 tomsmith、密码填 wrong，点登录"
    Then "页面提示密码无效"

  @scope:login-flow
  Scenario: 正确凭据登录成功
    When "用户名填 tomsmith、密码填 SuperSecretPassword!，点登录"
    Then 页面地址匹配 "/secure"
    Then "页面提示已登录到安全区"
