Feature: 示例商店结算
  加入购物车后角标与标题的检查。

  Background:
    Given 打开 "https://shop.example.test/"

  Scenario: 加入购物车后角标出现
    When "点击第一件商品的加入购物车按钮"
    Then 元素 "#cart-count" 可见
    Then "购物车里有 1 件商品"
    Then 页面标题包含 "示例商店"

  @engine:midscene
  Scenario: 加入购物车后角标出现（Midscene）
    When "点击第一件商品的加入购物车按钮"
    Then 元素 "#cart-count" 可见
    Then "购物车里有 1 件商品"
    Then 页面标题包含 "示例商店"
