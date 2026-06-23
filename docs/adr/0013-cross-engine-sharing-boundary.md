# 跨引擎共享的边界：共享用例（features/），不共享引擎代码

什么该在两个引擎间共享、什么不该——这是个会反复被问的架构问题，在此固定判断。

## 判断

**唯一跨引擎共享的是 `features/`（Gherkin 用例文本）**，即 [0005](./0005-single-shared-feature-file.md) 的单一事实源。**引擎的实现代码不跨引擎共享**，各自留在 `midscene/` / `novaact/` 内。

## 为什么代码不跨引擎共享——不只是"语言不同"

语言异构（TS vs Python）是直接障碍，但更深的原因是：**两个引擎本就没有多少同质代码可共享。** 逐项看：

| 关注点 | Midscene 腿 | Nova Act 腿 | 可共享？ |
|---|---|---|---|
| 鉴权 | SigV4 自签（[0008](./0008-midscene-bedrock-auth-sigv4-selfsign.md)） | IAM + Workflow（[0004](./0004-novaact-iam-auth-via-workflow.md)） | ❌ 机制根本不同 |
| 模型调用 | OpenAI chat-completions（Qwen3-VL） | Nova 自家 SDK | ❌ |
| 浏览器接入 | connectOverCDP + 自签 upgrade | provider.cdp_session() | ⚠️ 概念像、实现各异 |
| 断言 | aiAssert / page | act_get / page | ⚠️ 语义对齐、API 不同 |

即便都用同一语言，SigV4 与 IAM-Workflow 也是两套东西，抽不到一起。**共享停留在概念层（都接 AgentCore、都出报告、都跑同一 `.feature`），不在代码层。** 引擎内复用（如 `midscene/lib/agentcore-sigv4.mts` 被 Midscene 的 spike+bdd 共用）是健康的，但那是**引擎内**，不是跨引擎——勿混（CONTEXT 曾误把 SigV4 写成"两腿共享"，已更正）。

## 将来真正会跨引擎共享的：框架公共设施（暂不做）

不属于任一引擎、属于"框架"本身的东西，将来才是跨引擎共享的对象：
- 报告归集 / 统一（M5）
- AgentCore 会话生命周期编排（起/停/清理/配额）
- 用例与测试数据的组织规范、跑批入口

**这些落地的前提是统一到一种语言**，即形态 B 编排器（[0006](./0006-form-a-two-subprojects-no-orchestrator.md)）。其技术可能性已知但未验证：Nova Act 有官方 TS SDK `@aws-sdk/client-nova-act`，但它是否等同于本地 `nova.act()` 的浏览器自动化语义未证（见 0006 的不确定性记录）。**原型阶段不上形态 B**，故这些公共设施现在不抽；记着方向即可。

## 何时重议

当"框架公共设施"（尤其报告统一、跑批入口）成为硬需求、且形态 B 的统一语言路径被验证可行时，再设跨引擎的共享层，另立 ADR。在那之前，跨引擎共享止于 `features/`。
