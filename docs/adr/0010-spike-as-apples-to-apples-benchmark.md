# 两个引擎的 spike 做成「苹果对苹果」对标基准

> **Status:** Accepted

两个 spike（Midscene 引擎的 `engines/midscene/spikes/03-midscene-grounding.ts`、Nova Act 引擎的 `engines/novaact/spikes/wikipedia_benchmark.py`）刻意用**同一用例、同一断言策略、同一度量**，使其不只是各自「证活着」，而是产出一份双引擎**对比基准**。

**决定（三者必须对齐才能比）**：
- **同一用例**：都用维基百科搜索场景（打开 wikipedia.org → 搜一个词 → 断言进入该词条页）——即 CONTEXT.md「探针用例」。
- **同一断言策略**：都做 **A（确定性，Playwright `nova.page`/Midscene page）+ B（AI 断言，`act_get(BOOL_SCHEMA)`/`aiBoolean`）双断言**，并对 B 做 **N 次重复抖动探测**。
- **同一度量**：grounding/动作成功率、A 与 B 对同一页结论是否一致、B 的 N 次抖动率、单次耗时、token/成本。

**交付物**：不是「两个绿灯」，而是一张对比表——Midscene vs Nova Act 在同一任务上的成功率/一致性/抖动/耗时/成本。

**为什么值得记**：项目立项时「两引擎须可对标」的需求是硬约束——若两个 spike 在用例措辞、断言写法、度量口径上漂移，对比就失去意义。任何一个 spike 的改动都要同步另一个，保持可比性。

**注意**：维基用例是英文（合 [0001](./0001-scope-limited-to-english-ui.md)）、无登录（合 [0007](./0007-programmatic-login-hitl-as-escape-hatch.md) 的 spike 不碰认证）。断言哲学 A/B 的取舍原拟由这份基准的抖动数据决定（两侧定义见 CONTEXT「AI 断言」与「确定性断言」两条）；最终由 [0014](./0014-ai-first-assertions.md) 按价值取向落定为 AI 断言为主（该 ADR 自述非实测结论），基准的抖动数据转作校准「何时该降到确定性 step」的依据。本 ADR 只固定「怎么测得可比」，不预判结论。

## 对标结论（两个引擎，单用例 wikipedia/OpenAI，2026-10-29，us-east-1，AgentCore 云端浏览器，各引擎默认模型）

| 度量 | Midscene（`us.openai.gpt-5.6-terra`） | Nova Act（`nova-act-v1.0`） |
|---|---|---|
| 动作成功 | 是 | 是 |
| 动作耗时（只计引擎 act 调用） | 35684 ms | 31076 ms |
| 页面加载等待（动作之后，单独计时） | 2 ms | 0 ms |
| 动作 token（输入 / 输出） | 28097 / 337 | SDK 不暴露 |
| 动作计费时长 time_worked_s | 不适用，按 token 计费 | 30.5 s |
| A 确定性断言（url 含 /wiki/OpenAI） | pass | pass |
| B AI 断言 ×10 | 10/10，抖动 0% | 10/10，抖动 0% |
| A/B 一致 | 是 | 是 |
| B 平均耗时/次 | 5595 ms | 11059 ms |
| B 平均 token/次（输入 / 输出） | 1951 / 42 | SDK 不暴露 |
| B 平均计费时长/次 time_worked_s | 不适用，按 token 计费 | 10.5 s |

表头的模型即各引擎当前默认（见 [0044](./0044-engine-model-selection-and-override.md)「现值」）。可比性靠三处口径：① 两侧动作指令逐字相同（`type "OpenAI" into the search input and submit the search`），断言句逐字相同（`the page is the Wikipedia article about OpenAI`），只保留调用形式的差异（Midscene `aiBoolean`、Nova `act_get(BOOL_SCHEMA)`，见下洞察 ③）；② 动作耗时只包住引擎 act 调用本身（含 SDK 在调用内部的等待），动作之后等页面到 `domcontentloaded` 的时间单列为「页面加载等待」；③ token 的采集边界：Midscene 取 SDK 公开的 `agent.metrics` 累计用量、按调用前后的差值计（与 worker 取 step 用量同一算法），数值来自模型响应里的 usage，某格为 0 表示响应未带 usage、不表示零用量；Nova 侧 SDK（nova-act 3.4.187.0）的 `ActMetadata` 与 botocore 服务模型（nova-act 2025-08-22）里 `InvokeActStep` 的输出（只有 `calls` 与 `stepId`）都没有 token 字段，故标「SDK 不暴露」，成本用 SDK 原生的 `time_worked_s`（两侧计费轴不同的处理见 [0024](./0024-worker-core-protocol.md)「成本信封」）。上一次测量（2026-06-23，指令措辞与计时口径尚未对齐，耗时不与本表直接比较）用的是当时的默认：Midscene 的 Qwen3-VL 动作 58.9 s、B 平均 10.45 s/次，Nova 经已弃用的别名 `nova-act-latest`（见 [0004](./0004-novaact-iam-auth-via-workflow.md)）动作 33.5 s、B 平均 13.2 s/次；两侧同样动作成功、B 10/10 零抖动、A/B 一致。

**信号**：两个引擎在本（简单、确定性强）用例上 AI 断言均 10/10 零抖动、与确定性断言完全一致，换到当前默认模型后依然如此——对「AI 断言可信度」是双边正面信号。**但样本仅 1 个用例**，断言哲学的最终取舍仍需更多/更难（动态内容、多候选、模糊判定）的用例才能定。（当时判断；后由 [0014](./0014-ai-first-assertions.md) 按价值取向落定，更难用例的数据转作校准）耗时与成本只有单次测量：动作两侧同量级（35.7 s / 31.1 s），B 单次 Midscene 约为 Nova 的一半（5.6 s / 11.1 s）；Nova 的计费时长与 act 耗时几乎相等（动作 30.5 / 31.1 s，B 10.5 / 11.1 s）；两侧计费单位不同（token 与 agent 工作时长），美元比较须按使用方账户的费率折算。本表为基准的起点，非结论。

## 实测挖出的洞察（对跨引擎报告统一关键）

**① 引擎原生产物两个引擎根本不同**（见 CONTEXT「引擎原生产物」）：
- Midscene → **单一 `report.html`**，落项目内 `midscene_run/report/`，含每步截图+AI 决策+坐标。
- Nova Act → **每次 `act`/`act_get` 各一个 trajectory HTML**（本用例 11 个：1 动作 + 10 断言），默认落 **系统临时目录** `$TMPDIR/..._nova_act_logs/<sessionId>/`。
- → 「报告统一」要面对三处差异：单文件 vs 多文件、项目内 vs 临时目录、截图+坐标 vs 逐 act trajectory。**v1.0 已由 [0027](./0027-runreport-aggregation-index.md) 兑现，且结论是「不融合原生产物内容」**——只做跨引擎归集索引（产物形态见该 ADR），链接各自原生产物、不解析融合其内容，故这三处差异不必在报告层抹平。

**② Nova Act 报告默认落临时目录、会被系统清理**——留不住、不可追溯。`NovaAct(logs_directory=...)` 可固定到项目内（类比 Midscene 的 `midscene_run/`）。spike 阶段尚未固定（用例已验证通过即可），后续接入生产链路时应设 `logs_directory` 并 gitignore（已兑现，见下「spike→生产差异」）。

**③ 两个引擎的 AI「断言」机制**：spike 最初用了不对称写法（Midscene `aiAssert` 抛错式 / Nova Act `act_get(BOOL_SCHEMA)` 取布尔再判定），现已对齐：Midscene 侧改用 `aiBoolean`，与 worker 的投票路径一致（上表即对齐后的测量）。对齐的依据是两侧**实际可对称**（2026-06 查证安装源码）：Midscene 有 `aiBoolean(prompt) -> Promise<boolean>`，与 Nova Act `act_get(..., BOOL_SCHEMA)` 形态完全一致（问是非、拿布尔、不抛错）。Midscene 取结构化的全家族：`aiBoolean / aiNumber / aiString / aiQuery<T> / aiAsk`（对标 act_get 的标量与通用版）；`aiAssert` 则是 Nova Act 无对应的抛错式断言。→ 抖动治理（ADR 0014）应统一走 `aiBoolean` ↔ `act_get(BOOL_SCHEMA)` 的对称布尔路径，便于两个引擎都在布尔值上做投票（对称有边界：命题措辞含歧义时两引擎判定可能分叉，见 [0018](./0018-generic-steps-capability.md)「两个引擎对称（精确化）」条的负向验证）。

**spike→生产差异**：AI 断言写法已不是差异——worker 未沿用 spike 早期的 `aiAssert` 抛错式写法、走对称布尔投票（Midscene `aiBoolean` ↔ Nova `act_get(BOOL_SCHEMA)`，见 ADR 0014/0024），spike 现已改为同一路径（见 ③）；上文 ①② 记的落点是**两个 SDK 未被注入落点时的默认**（Nova 系统临时目录 / Midscene 相对 cwd 的 `midscene_run/`，二者至今仍是 SDK 默认），生产里组合根经 `NOVA_LOGS_DIR` / `MIDSCENE_RUN_DIR` 把**两个引擎的落点对称地**归位到 run 专属目录（`reports/<run_id>/` 树内），故 ② 的「应设 `logs_directory` 并 gitignore」已兑现、①② 的落点均非生产现状——具体子目录、对称理由与「不融合原生产物内容」结论见 [0027](./0027-runreport-aggregation-index.md)。
