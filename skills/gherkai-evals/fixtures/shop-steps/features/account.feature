Feature: 账户

  Scenario: 登录页可达
    Given 打开 "https://shop.example.test/login"
    Then 页面标题包含 "登录"
    Then "页面上有用户名与密码两个输入框"
