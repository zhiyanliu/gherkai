# 云端执行倾向 Fargate/ECS 而非 AgentCore Runtime（批处理 shape-fit）

> **Status:** Accepted

当执行面搬上云（v1.x+，见 [0016](./0016-execution-architecture-core-lib-run-model.md)），**倾向 Fargate/ECS（ECS RunTask）而非 AgentCore Runtime**。这是**倾向性结论**，上云时以实测复核为准——非现在锁死。

## 决定性理由：workload shape 是批处理

测试 job 是"跑完一批 → 出报告 → 退出"的**批处理**。ECS RunTask 原生就是这个（AWS 文档原话"a batch job that performs work, and then stops"），跑完即退、计费停止。AgentCore Runtime 是为**长驻 agent 服务**设计的（session/endpoint/invoke），要把批处理塞进去得用 `add_async_task` + `HealthyBusy` ping **对抗它的 15 分钟 idle-kill 计时器**（官方标注的 footgun：ping 线程一阻塞，session 在测试中途被杀）。

## 诚实修正

初轮调查把 Fargate 的优势框大了，经核对**真正站得住的只有一条半**：
- ✅ **run-to-exit 原生**：ECS 不用跟 idle 计时器搞保活 plumbing；Runtime 要。这是最硬的。
- ⚠️ **成本**：Fargate 全时长计费 vs Runtime 免 idle-CPU——但 Runtime"免 idle"在有浏览器进程时大概率失效、且内存按峰值全程计费；**孰优只能实测**，不能从文档断定。
- ❌ **不算数的**：「结果持久化」「异步语义别扭」——这两条**两个后端都要自建/都适用**，不是 Fargate 的优势（早先表述有误）。

## 翻盘条件（shape 变了才翻，留意这些信号）

Runtime 成为更优选，当且仅当 **workload 从批处理变成长驻服务**：
- 出现**常驻、被反复 invoke 的服务**——如 `test-this-PR` 的按需 API endpoint、agent 间工具调用、交互式服务（含但不限于 chatbot 形态）。
- 需要 **OAuth 入站**（外部认证调用者触发测试）——自调度批处理没有这种调用者。
- 重度 I/O-wait 主导且计费 CPU 真空闲（浏览器进程在场时此条多半不成立）。

若一直是"调度 → 跑批 → 出报告 → 退出"，以上都不触发，Fargate 胜。

## 被否的相邻选项

- **AgentCore Evaluations**（LLM-as-Judge 批量判定）：定位是评估**你自己构建/instrument 的** agent；而本项目的 agent（Midscene/Nova Act 大脑）是**集成进来的黑盒**，不天然适用。且其 LLM-as-Judge 判定我们已用 `aiBoolean`/`act_get` 原生覆盖（[0010](./0010-spike-as-apples-to-apples-benchmark.md)/[0014](./0014-ai-first-assertions.md)）。**去优先级**，除非将来要观测引擎内部。

## 何时坐实

上云时（v1.x），先用真实用例 A/B 实测 Fargate 与（若仍疑）Runtime 的成本/冷启动/会话保活，再最终敲定。`runScope` 的执行实现是可替换的（[0016](./0016-execution-architecture-core-lib-run-model.md)），故即便选错也能换——这降低了本决策的下注风险。
