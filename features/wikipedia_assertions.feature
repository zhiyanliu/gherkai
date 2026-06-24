# v0.x 打磨 generic steps · 第一批：断言类能力（① 提取数据断言 + ⑤ 否定/不存在断言）
# 故意写会戳穿现有 4 个 generic step 的句子，暴露缺口 → 决定要新增哪些 step 类型。
# 两腿都跑（Midscene cucumber-js / Nova Act pytest-bdd），对比能力差异。
Feature: 维基断言能力打磨

  Scenario: 提取数据并精确断言 + 否定断言
    Given 打开 "https://www.wikipedia.org/"
    # ⑤ 否定/不存在断言：现有 aiBoolean 问否定句靠不靠谱？
    Then 确认页面没有 "服务器错误" 的提示
    # ① 提取数字再比较：现有只有 aiBoolean，无 aiNumber → 应戳穿
    Then 页面上展示的语言版本数量应该大于 "5"
    When AI 执行 "在搜索框输入 OpenAI 并提交搜索"
    # ① 提取字符串断言：进入词条后，需 aiQuery/aiString → 应戳穿
    Then 词条首段应该提到 "artificial intelligence"
    And 页面地址包含 "/wiki/OpenAI"
