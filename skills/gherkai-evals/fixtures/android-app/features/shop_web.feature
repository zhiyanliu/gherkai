Feature: 网页版商城

  Scenario: 首页可达
    Given "https://shop.example.test/"
    Then 页面标题包含 "示例商店"
    Then "页面顶部有导航栏"
