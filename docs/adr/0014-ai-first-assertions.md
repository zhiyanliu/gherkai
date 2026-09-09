# 断言哲学：AI 断言为主，配套可靠性纪律

> **Status:** Accepted

测试用例的断言**默认走 AI**（Midscene `aiBoolean` / Nova Act `act_get(BOOL_SCHEMA)`，两侧对称布尔 + 投票；**不走** Midscene `aiAssert`——抛错黑盒、与 Nova Act 不对称，见下「抖动治理」条），让框架忠于其立身之本——「用 AI 引擎做自动化测试」。确定性断言（底层 Playwright `page`）退为**高保真补充与逃生舱**，而非默认。

## 为什么 AI 为主（价值取向，非实测结论）

本框架的卖点就是 AI 驱动（[0005](./0005-single-shared-feature-file.md)/[0006](./0006-form-a-two-subprojects-no-orchestrator.md)）。若判定环节退回确定性 Playwright 为主，则 AI 大脑只用于「执行动作」、判定把 AI 绕开，等于自废一半卖点。故断言也拥抱 AI。

## 代价是真实的——必须配套纪律（否则 flaky 反噬）

AI 断言**非确定性、且每次消耗模型调用**。「AI 为主」不等于「无视风险」，必须配：

1. **抖动治理**：AI 断言应可重试 / 多次投票（如 N 次取多数），并**记录抖动率**；CI 里监控抖动趋势。拥抱非确定性 = 必须为它买这份保险。
   - **两个引擎用对称的布尔路径做投票**（查证安装源码）：Midscene `aiBoolean(prompt) -> boolean` ↔ Nova Act `act_get(prompt, BOOL_SCHEMA) -> bool`，都「问是非、拿布尔、不抛错」，可直接在布尔值上 N 次投票。**不要**用 Midscene 的 `aiAssert`（抛错黑盒）做投票——它要 catch 异常、机制和 Nova Act 不对称。`aiAssert` 留给"判定即终止"的简单场景。
   - 布尔之外的取结构化路径（取数/取串等）及两个引擎的对称映射与边界，见 [0018](./0018-generic-steps-capability.md)；Midscene 该家族的 API 面与 `.d.ts` 位置见 [REFERENCES](../REFERENCES.md)。
2. **确定性逃生舱**：当判定**不可模糊**且确定性手段能精确表达（如 URL、DOM 存在性、精确数值）时，允许用确定性断言作高保真补充。它不是被禁止，是从「默认」降为「按需」。
3. **持续度量校准**：当前仅 1 个对 AI 友好的用例（维基/OpenAI）两个引擎各 10 次**零抖动**——这是正面信号但**不足以反推 AI 断言在难场景可靠**（见 [0010](./0010-spike-as-apples-to-apples-benchmark.md)）。需对更难用例（模糊判定 / 动态内容 / 细微差异如禁用态）持续测抖动率，用数据校准「何时该降到确定性逃生舱」。

## 现状与未决

- **已定**：AI 断言为默认方向（本 ADR）。
- **已定（投票次数 N 可配，v1.0 落地）**：投票次数 = `assertion_votes`，组合根经 CLI `--assertion-votes N` 设、贯穿 plan→Job→worker 协议→两个引擎 worker（[0024](./0024-worker-core-protocol.md)/[0025](./0025-plan-module-feature-to-jobs.md)/[0026](./0026-schedule-module.md)）。**默认 N=1**（单次判定、不做抖动检测——结果/日志最直观，避免功能未被理解时的噪声）；调高（如 3/5）才启用「N 次取多数票」抖动治理。`total==1` 时渲染隐藏投票 tally、`>1` 才显（机器可读层始终保留完整 votes）。
- **未定（靠数据迭代，不阻塞）**：N 的**推荐缺省值**（何时该把默认从 1 调高）、投票通过**阈值**（当前多数票 `yes > N/2`）、哪些判定类型应强制走确定性逃生舱——模糊判定 / 负向 / 措辞歧义的首批数据已出（见 [0018](./0018-generic-steps-capability.md)），暴露的主导风险是**措辞歧义**而非抖动率；N 的缺省值与阈值仍待抖动量化数据，出来后细化、届时更新本 ADR，不另立。
- 抖动探测脚手架已在 spike（Midscene `03-midscene-grounding.ts`、Nova Act `wikipedia_benchmark.py` 各含 N=10 抖动），可复用到更难用例。
