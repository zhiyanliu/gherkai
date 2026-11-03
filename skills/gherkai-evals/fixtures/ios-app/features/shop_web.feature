Feature: 网页版商城

  Scenario: 搜索结果页
    Given "https://shop.example.test/search?q=sneakers"
    Then 页面地址匹配 "^https://shop\.example\.test/search\?q=sneakers$"
    Then "搜索结果列表里至少有一个商品"
