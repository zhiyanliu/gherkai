# 认证走程序化登录 / profile 复用，HITL 仅作调试逃生舱

> **Status:** Accepted

真实被测系统几乎都要登录。作为一个**测试框架**，其命脉是无人值守、可重复——这与「人工接管（HITL）」天然冲突。故定调：

**决定**：
- 正式测试用例的认证走 **程序化登录**：用底层 Playwright（`nova.page` / Midscene 的 page）直接注入凭证（用户名/密码从环境变量或密钥管理取，**敏感数据不进 AI prompt**），或预置一个登录好的 AgentCore 托管 profile（`AgentCoreBrowserSessionProvider(profile=...)` 持久化 cookie/localStorage）并复用 session。
- **HITL**（Nova Act 的 Human Intervention Service + DCV 远程画面接管）**降级为非自动化路径**：仅用于开发期调试、过一次性 CAPTCHA，**不进正式用例**。

**为什么不是把 HITL 当一等公民**：内建「跑到登录步暂停等人」会牺牲无人值守，CI 里无法自动跑，会把框架带向「必须有人盯着」，背离测试框架的本质。

**spike 阶段**：第一根穿刺针用无登录站点（维基百科），**完全不碰认证**，避免登录复杂度污染链路验证。本 ADR 只定方向，登录代码留到接入真实被测系统时再写。

**范围前提**：与 [0001](./0001-scope-limited-to-english-ui.md) 一致——若未来出现强 CAPTCHA/必须人工的场景，再单独重议 HITL 的地位。
