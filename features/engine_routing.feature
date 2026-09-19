# v0.x 验证：tag 路由——每个引擎只执行标了自己（或未标=默认）的 scenario。
# 验证 @engine: tag 两个引擎都可读、可据此路由。用 example.com（极简稳定，本验证只关心路由不关心内容）。
Feature: 引擎路由（tag 验证）

  @engine:midscene @scope:r1
  Scenario: 只在 Midscene 引擎执行
    Given 打开 "https://example.com"
    Then "页面包含 Example Domain 字样"

  @engine:novaact @scope:r2
  Scenario: 只在 Nova Act 引擎执行
    Given 打开 "https://example.com"
    Then "页面包含 Example Domain 字样"
