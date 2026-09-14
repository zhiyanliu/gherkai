# 商品目录（英文站点 books.toscrape.com，公开、无登录）
Feature: 商品目录

  @smoke @scope:catalog-browse
  Scenario: 首页能看到商品列表
    Given 打开 "https://books.toscrape.com/"
    Then "页面上有一排带价格的图书"

  @smoke @scope:catalog-browse
  Scenario: 进入第一本书的详情页
    When "点击第一本书的标题"
    Then "当前是这本书的详情页，能看到价格与库存"

  @scope:catalog-category
  Scenario: 按分类筛选
    Given 打开 "https://books.toscrape.com/"
    When "点击左侧分类里的 Travel"
    Then 页面地址匹配 "/category/books/travel"
    Then "列表里只剩 Travel 分类的书"

  Scenario: 分页到第二页
    Given 打开 "https://books.toscrape.com/"
    When "点击底部的 next"
    Then 页面地址匹配 "page-2\.html"
