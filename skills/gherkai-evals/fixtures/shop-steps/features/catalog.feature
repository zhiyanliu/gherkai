Feature: 商品目录

  Background:
    Given 打开 "https://shop.example.test/catalog"

  Scenario: 目录页可达
    Then "页面顶部有导航栏"
    Then 页面标题包含 "示例商店"
    Then "这一页看起来不像出错页"

  Scenario: 首件商品的价格
    Then "页面顶部有导航栏"
    When "点开第一件商品"
    Then "价格显示为 ¥ 199.00"

  Scenario Outline: 分类页可达
    Then "页面顶部有导航栏"
    When "点击顶部导航里的分类 <分类>"
    Then 页面标题包含 "<分类>"

    Examples:
      | 分类 |
      | 图书 |
      | 数码 |
