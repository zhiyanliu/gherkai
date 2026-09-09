# 非英文 UI 探针：纯中文页面 + 中文 step，两引擎各一个 scenario、步骤完全相同（ADR 0001「扩到非英文 UI 的路径」
# 第 1 步的测量夹具）。配 --assertion-votes N 测 AI 断言在中文 UI 上的抖动率，与英文探针 wikipedia_*.feature 同构：
# 稳定、中立、无登录站点。会真连 AgentCore、产生 AWS 费用，不进日常 QA 流。
Feature: 中文维基搜索（非英文 UI 探针）

  @engine:midscene @scope:zh-midscene
  Scenario: Midscene 在中文 UI 上搜索并断言
    Given 打开 "https://zh.wikipedia.org/"
    Then "页面没有出现服务器错误"
    When "在搜索框输入 人工智能 并提交搜索"
    Then "当前页面是关于人工智能的维基百科词条页"
    Then "词条首段提到了计算机或机器"

  @engine:novaact @scope:zh-novaact
  Scenario: Nova Act 在中文 UI 上搜索并断言
    Given 打开 "https://zh.wikipedia.org/"
    Then "页面没有出现服务器错误"
    When "在搜索框输入 人工智能 并提交搜索"
    Then "当前页面是关于人工智能的维基百科词条页"
    Then "词条首段提到了计算机或机器"
