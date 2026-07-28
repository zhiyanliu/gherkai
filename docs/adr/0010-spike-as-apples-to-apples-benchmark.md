# 两个引擎的 spike 做成「苹果对苹果」对标基准

> **Status:** Accepted

两根穿刺针（Midscene 引擎、Nova Act 引擎）刻意用**同一用例、同一断言策略、同一度量**，使其不只是各自「证活着」，而是产出一份双引擎**对比基准**。

**决定（三者必须对齐才能比）**：
- **同一用例**：都用维基百科搜索场景（打开 wikipedia.org → 搜一个词 → 断言进入该词条页）——即 CONTEXT.md「骨架验证用例」。
- **同一断言策略**：都做 **A（确定性，Playwright `nova.page`/Midscene page）+ B（AI 断言，`act_get`/`aiAssert`）双断言**，并对 B 做 **N 次重复抖动探测**。
- **同一度量**：grounding/动作成功率、A 与 B 对同一页结论是否一致、B 的 N 次抖动率、单次耗时、token/成本。

**交付物**：不是「两个绿灯」，而是一张对比表——Midscene vs Nova Act 在同一任务上的成功率/一致性/抖动/耗时/成本。

**为什么值得记**：U2/U3 的「对标」要求是硬约束——若两针在用例措辞、断言写法、度量口径上漂移，对比就失去意义。任何一针的改动都要同步另一针，保持可比性。

**注意**：维基用例是英文（合 [0001](./0001-scope-limited-to-english-ui.md)）、无登录（合 [0007](./0007-programmatic-login-hitl-as-escape-hatch.md) 的 spike 不碰认证）。断言哲学 A/B 的最终取舍，由这份基准的抖动数据决定（见 CONTEXT「确定性断言 vs AI 断言」），本 ADR 只固定「怎么测得可比」，不预判结论。

## 对标结论（两个引擎，单用例 wikipedia/OpenAI，2026-06-23，AgentCore 云端）

| | Midscene (Qwen3-VL, SigV4) | Nova Act (nova-act-latest, 纯 IAM Workflow) |
|---|---|---|
| 动作成功/耗时（搜 OpenAI 进词条） | ✅ 58.9s | ✅ 33.5s |
| A 确定性断言（url 含 /wiki/OpenAI） | pass | pass |
| B AI 断言 ×10 | 10/10，抖动 0% | 10/10，抖动 0% |
| A/B 一致 | ✅ | ✅ |
| B 平均耗时/次 | 10.45s | 13.2s |

**信号**：两个引擎在本（简单、确定性强）用例上 AI 断言均零抖动、与确定性断言完全一致——对「AI 断言可信度」是双边正面信号。**但样本仅 1 个用例**，断言哲学的最终取舍仍需更多/更难（动态内容、多候选、模糊判定）的用例才能定。本表为基准的起点，非结论。

## 实测挖出的洞察（对 M5 报告统一关键）

**① 报告产物模型两个引擎根本不同**（见 CONTEXT「报告产物模型」）：
- Midscene → **单一 `report.html`**，落项目内 `midscene_run/report/`，含每步截图+AI 决策+坐标。
- Nova Act → **每次 `act`/`act_get` 各一个 trajectory HTML**（本用例 11 个：1 动作 + 10 断言），默认落 **系统临时目录** `$TMPDIR/..._nova_act_logs/<sessionId>/`。
- → M5「报告统一」必须弥合：单文件 vs 多文件、项目内 vs 临时目录、截图+坐标 vs 逐 act trajectory。

**② Nova Act 报告默认落临时目录、会被系统清理**——留不住、不可追溯。`NovaAct(logs_directory=...)` 可固定到项目内（类比 Midscene 的 `midscene_run/`）。spike 阶段尚未固定（用例已验证通过即可），M2/M5 接入时应设 `logs_directory` 并 gitignore。

**③ 两个引擎的 AI「断言」机制**：spike 里用了不对称写法（Midscene `aiAssert` 抛错式 / Nova Act `act_get(BOOL_SCHEMA)` 取布尔再判定）。**但实际可对称**（2026-06 查证安装源码）：Midscene 有 `aiBoolean(prompt) -> Promise<boolean>`，与 Nova Act `act_get(..., BOOL_SCHEMA)` 形态完全一致（问是非、拿布尔、不抛错）。Midscene 取结构化的全家族：`aiBoolean / aiNumber / aiString / aiQuery<T> / aiAsk`（对标 act_get 的标量与通用版）；`aiAssert` 则是 Nova Act 无对应的抛错式断言。→ 抖动治理（ADR 0014）应统一走 `aiBoolean` ↔ `act_get(BOOL_SCHEMA)` 的对称布尔路径，便于两个引擎都在布尔值上做投票。

**spike→生产差异**：worker 未沿用 spike 的 `aiAssert` 抛错式写法，改走对称布尔投票（Midscene `aiBoolean` ↔ Nova `act_get(BOOL_SCHEMA)`，见 ADR 0014/0024）；Nova trajectory 已由临时目录改为持久化归集（`NOVA_LOGS_DIR`，见 ADR 0027）。
