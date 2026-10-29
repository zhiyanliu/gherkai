# 确定性 step 验证（ADR 0022）——验证 @deterministic 注册表在真会话下生效。
# `Then 页面地址匹配 "<正则>"` 是 features/steps/ 里的示范 step（两引擎成对，使用方项目的 steps/ 模板）：
# 运行时须带 `--steps-dir features/steps`（或环境变量 GHERKAI_STEPS_DIR）加载；worker 派发时先查注册表命中它，
# 用 Playwright page.url 精确判定、不走 AI、不投票。第一步是内建导航：Given 后整句是一个地址（ADR 0020 第 3 条）。
# （纯自然语言 Then 走 AI 的路径由 wikipedia_generic/assertions 等 feature 覆盖，此处专注确定性 step 本身。）
Feature: 确定性 step（URL 精确匹配）

  Scenario: 导航后用确定性 step 校验 URL
    Given "https://www.wikipedia.org/"
    Then 页面地址匹配 "wikipedia\.org"
