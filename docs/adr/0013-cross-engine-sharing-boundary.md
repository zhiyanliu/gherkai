# 跨引擎共享的边界：共享用例（features/），不共享引擎代码

> **Status:** Partially-superseded-by 0023 —— 「共享止于 features/、引擎代码不跨引擎共享」核心结论仍成立（当前 code 即如此）；「公共设施靠统一到一种语言落地」这一前瞻前提被 0023 证伪，改由 Python 核心库 + 两引擎子进程 worker 承载（详见下文）。

什么该在两个引擎间共享、什么不该——这是个会反复被问的架构问题，在此固定判断。

## 判断

**唯一跨引擎共享的是 `features/`（Gherkin 用例文本）**，即 [0005](./0005-single-shared-feature-file.md) 的单一事实源。**引擎的实现代码不跨引擎共享**，各自留在 `engines/midscene/` / `engines/novaact/` 内。

## 为什么代码不跨引擎共享——不只是"语言不同"

语言异构（TS vs Python）是直接障碍，但更深的原因是：**两个引擎本就没有多少同质代码可共享。** 逐项看：

| 关注点 | Midscene 引擎 | Nova Act 引擎 | 可共享？ |
|---|---|---|---|
| 鉴权 | SigV4 自签（[0008](./0008-midscene-bedrock-auth-sigv4-selfsign.md)） | IAM + Workflow（[0004](./0004-novaact-iam-auth-via-workflow.md)） | ❌ 机制根本不同 |
| 模型调用 | OpenAI chat-completions（Qwen3-VL） | Nova 自家 SDK | ❌ |
| 浏览器接入 | connectOverCDP + 自签 upgrade | provider.cdp_session() | ⚠️ 概念像、实现各异 |
| 断言 | aiAssert / page | act_get / page | ⚠️ 语义对齐、API 不同 |

即便都用同一语言，SigV4 与 IAM-Workflow 也是两套东西，抽不到一起。**共享停留在概念层（都接 AgentCore、都出报告、都跑同一 `.feature`），不在代码层。** 引擎内复用（如 `engines/midscene/lib/agentcore-sigv4.mts` 被 Midscene 的 spike+bdd 共用）是健康的，但那是**引擎内**，不是跨引擎——勿混（CONTEXT 曾误把 SigV4 写成"两个引擎共享"，已更正）。

## 将来真正会跨引擎共享的：框架公共设施（暂不做）

不属于任一引擎、属于"框架"本身的东西，将来才是跨引擎共享的对象：
- 报告归集 / 统一（M5）
- AgentCore 会话生命周期编排（起/停/清理/配额）
- 用例与测试数据的组织规范、跑批入口

**这些落地的前提**原以为是「统一到一种语言（形态 B 编排器）」，但后续实查证伪了这个前提的可行性：**Nova Act acting 锁死 Python，全 TS 统一不可行**（[0023](./0023-novaact-acting-python-locked-no-ts-core.md)：`@aws-sdk/client-nova-act` 是客户端驱动的 REST 循环、非 `nova.act()` 等价物）。框架公共设施改由**核心库（Python）+ 两个引擎子进程 worker**承载（[0016](./0016-execution-architecture-core-lib-run-model.md)/[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)）：报告归集=`ReportStore`/RunReport、会话生命周期=各 worker 内、跑批入口=核心调度+CLI。即「跨引擎共享止于 `features/`」仍成立（worker 代码仍各属各引擎），公共设施落在**核心库**这一层、不靠跨引擎共享引擎代码。

## 何时重议

当"框架公共设施"（尤其报告统一、跑批入口）成为硬需求、且形态 B 的统一语言路径被验证可行时，再设跨引擎的共享层，另立 ADR。在那之前，跨引擎共享止于 `features/`。
