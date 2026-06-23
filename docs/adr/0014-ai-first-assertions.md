# 断言哲学：AI 断言为主，配套可靠性纪律

测试用例的断言**默认走 AI**（Midscene `aiAssert` / Nova Act `act_get`+schema），让框架忠于其立身之本——「用 AI 引擎做自动化测试」。确定性断言（底层 Playwright `page`）退为**高保真补充与逃生舱**，而非默认。

## 为什么 AI 为主（价值取向，非实测结论）

本框架的卖点就是 AI 驱动（[0005](./0005-single-shared-feature-file.md)/[0006](./0006-form-a-two-subprojects-no-orchestrator.md)）。若判定环节退回确定性 Playwright 为主，则 AI 大脑只用于「执行动作」、判定把 AI 绕开，等于自废一半卖点。故断言也拥抱 AI。

## 代价是真实的——必须配套纪律（否则 flaky 反噬）

AI 断言**非确定性、且每次消耗模型调用**。「AI 为主」不等于「无视风险」，必须配：

1. **抖动治理**：AI 断言应可重试 / 多次投票（如 N 次取多数），并**记录抖动率**；CI 里监控抖动趋势。拥抱非确定性 = 必须为它买这份保险。
   - **两腿用对称的布尔路径做投票**（查证安装源码）：Midscene `aiBoolean(prompt) -> boolean` ↔ Nova Act `act_get(prompt, BOOL_SCHEMA) -> bool`，都「问是非、拿布尔、不抛错」，可直接在布尔值上 N 次投票。**不要**用 Midscene 的 `aiAssert`（抛错黑盒）做投票——它要 catch 异常、机制和 Nova Act 不对称。`aiAssert` 留给"判定即终止"的简单场景。
   - Midscene 取结构化全家族可选：`aiBoolean / aiNumber / aiString / aiQuery<T> / aiAsk`。
2. **确定性逃生舱**：当判定**不可模糊**且确定性手段能精确表达（如 URL、DOM 存在性、精确数值）时，允许用确定性断言作高保真补充。它不是被禁止，是从「默认」降为「按需」。
3. **持续度量校准**：当前仅 1 个对 AI 友好的用例（维基/OpenAI）两腿各 10 次**零抖动**——这是正面信号但**不足以反推 AI 断言在难场景可靠**（见 [0010](./0010-spike-as-apples-to-apples-benchmark.md)）。需对更难用例（模糊判定 / 动态内容 / 细微差异如禁用态）持续测抖动率，用数据校准「何时该降到确定性逃生舱」。

## 现状与未决

- **已定**：AI 断言为默认方向（本 ADR）。
- **未定（靠数据迭代，不阻塞）**：抖动治理的具体参数（投票次数 N、阈值）、哪些判定类型应强制走确定性逃生舱——待更难用例的抖动数据出来后细化，届时更新本 ADR，不另立。
- 抖动探测脚手架已在 spike（Midscene `03-midscene-grounding.ts`、Nova Act `wikipedia_benchmark.py` 各含 N=10 抖动），可复用到更难用例。
