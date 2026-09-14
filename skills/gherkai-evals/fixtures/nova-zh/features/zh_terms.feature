Feature: 中文词条页上的断言（两引擎同题）

  @engine:novaact @scope:zh-novaact
  Scenario: Nova Act 在中文词条页判断首段用词
    Given 打开 "https://zh.wikipedia.org/wiki/人工智能"
    Then "当前是关于人工智能的维基百科词条页"
    Then "词条首段提到了计算机或机器"

  @engine:midscene @scope:zh-midscene
  Scenario: Midscene 在中文词条页判断首段用词
    Given 打开 "https://zh.wikipedia.org/wiki/人工智能"
    Then "当前是关于人工智能的维基百科词条页"
    Then "词条首段提到了计算机或机器"
