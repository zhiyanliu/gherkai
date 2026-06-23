Feature: Wikipedia article search
  As a test author
  I want one Gherkin scenario to drive both AI engines
  So that the same intent runs on Midscene and Nova Act alike

  # 这份 .feature 是单一事实源（ADR 0005），被 cucumber-js(TS) 与 pytest-bdd(Python) 各自加载。
  # step 措辞刻意保持在两套 runner 的方言交集内：纯文本步骤、引号包裹参数。

  Scenario: Search for OpenAI and open its article
    Given the Wikipedia home page is open
    When I search for "OpenAI" and open its article
    Then the page is the Wikipedia article about "OpenAI"
