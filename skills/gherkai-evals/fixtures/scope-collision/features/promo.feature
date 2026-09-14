# 促销页用例（books.toscrape.com 首页当促销页用）
Feature: 促销页

  @scope:catalog-browse
  Scenario: 促销区能看到打折标记
    Given 打开 "https://books.toscrape.com/"
    Then "页面上有带价格的图书列表"

  @scope:catalog-browse
  Scenario: 点开一本促销书
    When "点击第二本书的标题"
    Then "当前是这本书的详情页"
