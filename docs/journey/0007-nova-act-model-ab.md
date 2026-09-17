# Nova Act 模型 v1.0 vs v1.1 preview A/B（判定稳定性 / 耗时 / 超时）

> 类型: 调查记录（待批报告；结论吸收进 ADR 0004「模型版本选择策略」后删）

## 目的

给 ADR 0004「模型版本选择策略（待定）」提供数据：`nova-act-latest`（→ v1.0 GA）与 `nova-act-preview`（→ v1.1_2026-02-09 preview）在同一批 Nova 用例上的 pass / fail 稳定性、单 act 耗时、超时与 engine_error 率是否有明显差异。

## 方法

- 跳板机 `~/yaozhou-v14` dev 树、与发行版同源；worker 常量 `MODEL_ID` 临时改为读 env `NOVA_MODEL_ID`（一行本地补丁，不提交，跑完还原）。本机档 `gherkai run`，模型在云端跑，不涉及部署。
- 用例：`features/` 里全部 Nova 侧 scope（7 个 feature、9 个 scenario：并发与 scope 共享、确定性锚点、引擎路由 r2、维基断言、通用搜索、鲁棒性两条、中文 UI 探针）。
- 每个模型 3 遍，两模型并行跑（同机同时段；模型推理在云端，机上无 CPU 争用）。
- 指标取自 `status --json` / `explain --json`：scenario 终态、AI 步 `duration_ms`、`error_type`；每次 run 的墙钟另计。模型 provenance 经 SDK 日志里的 workflow run id 反查服务端 `GetWorkflowRun.modelId`。

## 结果（2026-09-17，两系列各 21 次 run / 30 个 scenario 终态）

**provenance**：每次 run 的服务端 `GetWorkflowRun.modelId` 都与请求一致——`nova-act-latest` 21 次全部 `nova-act-v1.0`，`nova-act-preview` 21 次全部 `nova-act-v1.1_2026-02-09`；无回退、无警告。

| feature | model | run 终态（3 遍） | scenario 终态一致 | AI 步耗时 中位 / 最大 ms | 超时 | engine_error | run 墙钟中位 s |
|---|---|---|---|---|---|---|---|
| assertions | v1.0 | passed ×3 | 是 | 10166 / 26919 | 0 | 0 | 85.7 |
| assertions | v1.1 | passed ×3 | 是 | 9888 / 26827 | 0 | 0 | 85.9 |
| concurrency | v1.0 | passed ×3 | 是 | 16172 / 27177 | 0 | 0 | 125.2 |
| concurrency | v1.1 | **failed ×3** | 是 | 10036 / 25948 | 0 | 0 | 109.8 |
| det_anchor | v1.0 | passed ×3 | 是 | 无 AI 步 | 0 | 0 | 26.6 |
| det_anchor | v1.1 | passed ×3 | 是 | 无 AI 步 | 0 | 0 | 29.8 |
| generic | v1.0 | passed ×3 | 是 | 18574 / 28107 | 0 | 0 | 66.4 |
| generic | v1.1 | passed ×3 | 是 | 18828 / 28929 | 0 | 0 | 70.3 |
| robustness | v1.0 | **error** / passed / passed | 否 | 27751 / 131593 | 1 | 0 | 223.8 |
| robustness | v1.1 | passed ×3 | 是 | 19183 / 57068 | 0 | 0 | 157.9 |
| routing | v1.0 | passed ×3 | 是 | 9266 / 9432 | 0 | 0 | 34.1 |
| routing | v1.1 | passed ×3 | 是 | 9040 / 9210 | 0 | 0 | 33.8 |
| zh | v1.0 | failed ×3 | 是 | 10267 / 27126 | 0 | 0 | 85.0 |
| zh | v1.1 | failed ×3 | 是 | 9900 / 26704 | 0 | 0 | 82.7 |

汇总：v1.0 scenario passed 26 / failed 3 / error 1，AI 步耗时中位 10637 ms、p90 27751 ms，超时 1；v1.1 passed 24 / failed 6 / error 0，中位 10015 ms、p90 27897 ms，超时 0。耗时上两者等价。

**三处差异的成因**

1. `concurrency` scenario「搜索并进入 Python 词条」：两模型执行「在搜索框输入 Python 并提交搜索」后都落在消歧页 `en.wikipedia.org/wiki/Python`。断言步「当前页面是关于 Python 编程语言的维基百科词条」上，**v1.0 在断言里先点进了 `Python_(programming_language)` 再答 true（三遍皆如此）**；**v1.1 停在消歧页、如实答 false（三遍皆如此）**。这不是抖动，是行为差异：v1.1 不在布尔判定里改页面状态。按「断言不该有副作用」的口径，v1.1 的判定更诚实，v1.0 的 pass 是靠替用例补动作换来的；用例本身也写得松（搜索词落到消歧页是维基常态）。
2. `robustness` scenario「多步骤含开放动作」：v1.0 第 1 遍单个 act（搜索 → 打开词条 → 点正文首个链接）跑了 131.6 s，超过单 act 上界 120 s 判 timeout；另两遍 passed。v1.1 三遍最长 57 s。开放式多步 act 的墙钟在 v1.0 上偶发越界，v1.1 更快收敛。
3. `zh`：两模型同样 failed，thought 同因（在中文首段找字面「计算机 / 机器」未果），与 v1.4.2 起的基线一致。

## 结论

- **模型换代会稠密地改判定，不是噪声**：9 个 scenario 里 1 个（11%）在两模型间三遍一致地翻转；其余 8 个两侧一致。若继续用 `nova-act-latest` 别名，AWS 把 v1.1 升 GA 的那一刻，这类翻转会在零提交的情况下落到用户的 pass / fail 上。→ 支持 ADR 0004 待定项取「钉 `nova-act-v1.0`、升级作为有评估的显式动作」。
- **v1.1 preview 本身不劣于 v1.0**：耗时等价、无超时、判定更守「断言不动作」。等它升 GA 后按本方法重跑一遍即可决定切换；preview 阶段不作默认（无支持承诺、不可钉）。
- 顺带暴露一条用例质量问题：`features/concurrency_and_scope.feature` 的「搜索并进入 Python 词条」依赖模型替它消歧，应把导航写实（进入编程语言词条）或改用确定性 URL 步。
- 方法可复用：跑批与汇总脚本形态见本文「方法」；A/B 需要 worker 侧读 `NOVA_MODEL_ID` 的一行临时补丁，产品侧旋钮的取舍见 ADR 0004。
