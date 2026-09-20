Feature: 购物车

  Scenario: 购物车页可达
    Given 打开 "https://shop.example.test/cart"
    Then 页面标题包含 "购物车"
    Then "空购物车时页面提示去逛逛"
