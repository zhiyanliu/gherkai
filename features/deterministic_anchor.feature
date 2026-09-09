# 确定性锚点验证（ADR 0022）——验证 @deterministic 注册表在真会话下生效。
# `Then 页面地址匹配 "<正则>"` 是测试开发在 deterministic_steps（两腿脚手架）注册的
# 确定性 step：worker 派发时先查注册表命中它，用 Playwright page.url 精确判定、不走 AI、不投票。
# （纯人话 Then 走 AI 的路径由 wikipedia_generic/assertions 等 feature 覆盖，此处专注锚点本身。）
Feature: 确定性锚点（URL 精确匹配）

  Scenario: 导航后用确定性锚点校验 URL
    Given 打开 "https://www.wikipedia.org/"
    Then 页面地址匹配 "wikipedia\.org"
