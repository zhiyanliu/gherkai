# 引擎模型的选择与覆盖：默认钉版、按引擎 env 覆盖

> **Status:** Accepted（2026-09-17）

## 背景

**引擎 ≠ 引擎模型，两者分属两层**：「换模型」不等于「换引擎」（引擎的选择是 [0019](./0019-feature-tags-scope-and-engine.md) 的 tag 路由）；本 ADR 只管模型这一层。

两引擎各依赖一个云端模型：Nova Act 引擎的模型由 Nova Act 服务托管（`Workflow(model_id=...)`，[0004](./0004-novaact-iam-auth-via-workflow.md)）；Midscene 引擎经 Bedrock 的 OpenAI 兼容端点（`/openai/v1`，SigV4 service `bedrock`）调视觉模型。三个事实使「单一最佳模型」不成立：

1. **上游推荐随版本变、且各家评价都基于私有评测集**。Midscene 1.12 文档把我们用了半年的 Qwen3-VL 标为「老一代，不推荐」，改荐 Qwen3.x plus、Doubao Seed 2.1、Gemini 3.5 flash——三者在 Bedrock 上都没有；它给 GPT-5.6 / GPT-6 / Kimi 的评价也来自私有评测。这些结论对我们的用例没有可比性。
2. **AWS 上 Midscene 支持的家族在增加**。[0002](./0002-midscene-not-driven-by-gpt55.md) 当年据「Bedrock 上 GPT-5.5 不支持 chat-completions」让 GPT 出局，该事实已变（见其 Status 头）。2026-09 us-east-1 实查：GPT-6 Astra、GPT-5.6 sol / terra / luna（经 inference profile）、Kimi K2.5、Qwen3-VL 四者都能经我们现有的 SigV4 + OpenAI 兼容接线收发图文；Claude、Amazon Nova、Gemma、Mistral 虽有视觉能力但 Midscene 无对应 family。
3. **模型换代会稠密地改判定**。[0004](./0004-novaact-iam-auth-via-workflow.md) 的 A/B：9 个 scenario 有 1 个在两个模型间三遍一致翻转。使用方的应用、语言、预算不同，适合的模型也不同。

## 决策

1. **默认钉版、随发版评估升级，两引擎同律**。每个引擎的默认模型是钉死的具体 id，由本仓库的评测集（`features/` 下两引擎各自的 wikipedia 用例，加两引擎 `spikes/` 目录里的失败探针；各跑三遍）A/B 选出；换默认只随 gherkai 发版并在 Release 正文点明。Nova 的选型理由与证据在 [0004](./0004-novaact-iam-auth-via-workflow.md)「模型版本选择策略」；Midscene 的默认见下「现值」。此处的评测集是**模型评测集**（升引擎 SDK 时同样用它做回归），与探针用例大体同一批文件、用途不同；驱动 gherkai 的 skill 评测集是另一套资产、不在本 ADR 的选型回路里，见 [0043](./0043-agent-skill-for-driving-gherkai.md)。
2. **覆盖旋钮 = worker 侧 env，两引擎对称**。Nova：`NOVA_MODEL_ID`（[0004](./0004-novaact-iam-auth-via-workflow.md)）。Midscene：`MIDSCENE_MODEL_ID`（Bedrock 模型 id 或 inference profile id，如 `us.openai.gpt-6-astra`）+ 可选 `MIDSCENE_MODEL_FAMILY`（Midscene 的 family 名）。family 缺省时按 id 推断，表住 worker（`lib/agentcore-sigv4`）：`*qwen.qwen3-vl*` → `qwen3-vl`、`*openai.gpt-6*` → `gpt-6`、`*openai.gpt-5*` → `gpt-5`、`*kimi-k2*` → `kimi`、`*kimi-k3*` → `kimi3`、`*deepseek.*` → `deepseek`、`zai.glm-*v*` → `glm-v`（前导 `*` 让 `us.` / `global.` 前缀的 inference profile 形态同样命中——云端换模型的常见形态就是 profile id）；显式 `MIDSCENE_MODEL_FAMILY` 的取值不在 worker 侧校验（合法清单是 SDK 的真值，复刻即第二事实源），打错的家族名由 SDK 在建 agent 时拒；显式给了以显式为准；推不出且未给 → worker 启动即 fail-loud、点名要设 `MIDSCENE_MODEL_FAMILY`——family 决定 Midscene 的提示词与请求参数适配，猜错的后果是静默劣化而不是报错，所以宁可拒绝。生效面与 Nova 一致：本机跑在 shell 里设即生效（worker 继承 env，组合根不清这几个键）；云端 Fargate 容器 env 是显式枚举，烙进定制 worker 镜像的 `ENV`（[0038](./0038-worker-image-delivery.md) variant 机制）**即可，部署侧不必跟着动**：IaC 把 Fargate 任务角色的 `bedrock:InvokeModel` 放到 foundation-model/* 与本账户 inference-profile/*（[0033](./0033-iac-aws-backend-and-composition-wiring.md) IAM 表），可用集合由账户的 Bedrock 模型访问开关决定；仍锁死 service 与资源类型，不是裸 `*`。
3. **可用集合由接线决定，不另做适配**。Midscene 腿只能用 Bedrock OpenAI 兼容端点调得到、且 Midscene 有 family 的模型；GPT 系列须用 inference profile id（地理型 `us.` 或全球 `global.`，见「现值」的取舍）、参数走 `max_completion_tokens`（Midscene 的 `gpt-5` / `gpt-6` family 适配器负责，实测直接给模型 id 或用 `max_tokens` 都被端点 400）；IAM 上除 profile 与 FM ARN 外还需账户默认 project（[0033](./0033-iac-aws-backend-and-composition-wiring.md) IAM 表）；推理型模型的 token 成本含 reasoning tokens。**端点方言由接线层吸收**：Bedrock 的 OpenAI 兼容层不认 `image_url.detail: "original"`（对任何模型都 400「value did not match any expected variant」；OpenAI 原生认它），而 Midscene 的 `gpt-5` / `gpt-6` family 适配器对定位请求固定发这个值且无配置可关——`sigv4Fetch` 在签名前把该字段去掉，让服务端按默认处理（这是对端点方言的适配、不是对模型的适配，住 [0008](./0008-midscene-bedrock-auth-sigv4-selfsign.md) 那层）。preview 或无支持承诺的模型由使用方自担，同 [0004](./0004-novaact-iam-auth-via-workflow.md)。
4. **可见性**。worker `--capabilities` 自报 `model_id`（[0036](./0036-deterministic-capability-discovery.md)「5.」），`doctor` 显示本机 worker 实际用的模型；使用者向披露在 README「判定由谁做出」一节。

**现值**：Nova `nova-act-v1.0`；Midscene `us.openai.gpt-5.6-terra`（family `gpt-5`，地理型跨区 profile）。

**Midscene 默认的选定依据（2026-09 评测集 A/B，每模型 7 个 feature / 9 个 scenario × 3 遍，Kimi 6 遍；provenance 每 pass 由 worker `--capabilities` 自报 model_id 核对）**：

| | Qwen3-VL 235B（旧默认） | GPT-5.6 sol | GPT-5.6 terra | GPT-5.6 luna | GPT-6 Astra | Kimi K2.5 |
|---|---|---|---|---|---|---|
| scenario 终态 | 28 passed / 2 failed | 30 / 0 | 30 / 0 | 29 / 1 | 30 / 0 | 48 passed / 2 failed / 6 timeout |
| 三遍不一致的 scenario | 1 | 0 | 0 | 1 | 0 | 4 |
| AI 步耗时中位 / p90 | 10.1 s / 66 s | 8.0 s / 45 s | 6.8 s / 49 s | 8.1 s / 48 s | 7.1 s / 44 s | 7.7 s / 69 s（单步最长 220 s） |
| tokens / run 中位 | 44.7k | 34.4k | 34.4k | 34.3k | 34.2k | 45.8k |
| 中文 UI 探针 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 6 遍 1 败 |

- **Qwen3-VL** 的两次失败与 luna 的一次失败是同一条用例（首段被捐款横幅推出视口、模型如实判否），属用例视口敏感、已改用例；其余 scenario 两侧一致。**Kimi** 判定不差但尾延迟失控（6 次 300 s job 超时、后三遍不比前三遍好，非冷启动）。**GPT 系**三遍逐遍稳定、比 Qwen 快约三成、省约四分之一 token。
- **成本**（同一条 5 步用例实测 token 折价，Terra 按 $2.20 / cache read $0.22 / $13.20 每百万，Qwen 按 $0.53 / $2.66）：Qwen 约 $0.023 / run，Terra 约 $0.054 / run（约 2.3 倍；Astra 单价更高被否）。Bedrock 对 GPT-5.6 的 chat-completions 响应报告 cached_tokens（重复的 system prompt 第二次起命中；Midscene 三类意图各用不同 system prompt，整条 run 命中 30% 到 54%）；Midscene 的 `gpt-5` 适配器默认关 reasoning，输出 token 极少，$13.20 的输出价几乎不起作用——若使用方打开 `MIDSCENE_MODEL_REASONING_ENABLED` 成本会显著上升。**判据**：每 run 多约 3 美分，换 63 次 run 零失败零抖动与三成提速，对判定工具值得；成本敏感者一个 env 切回 Qwen。
- **地理型 vs 全球 profile**：`us.openai.gpt-5.6-terra` 的目的 region 固定为 us-east-1 / us-east-2 / us-west-2（AWS 承诺地理型 profile 目的集不变；CloudTrail `inferenceRegion` 实查本轮全部落在 us-east-2）。`global.openai.gpt-5.6-terra` 便宜约 9%（$2.00 / $12.00），但目的集是「全部商用 region」且会随 AWS 上线新 region 而变，可能路由到账号未启用的 opt-in region、且 AWS 声明「input prompts and output results may be stored in the opt-in Regions for abuse detection」；本轮实测 global 反而慢约 20%（从 us-east-1 被路由到 us-west-2）、cache 命中相当。**默认取地理型**：披露只需一句「美国境内三个 region」且不会过期，半美分的差价不值得把截图送往全球任一 region 写进用户文档；global 只作 `MIDSCENE_MODEL_ID` 的可选值、不进使用者向文档。
- 数据驻留口径：Nova 模型与 Qwen 在所选 region 内处理；Midscene 默认的 GPT-5.6 经 Bedrock 地理型跨区 profile 在美国境内三个 region 处理；浏览器会话、产物存储仍在所选 region。

## 被拒 / 留口子

- **run 级 `--model <engine>=<id>`，随 definition 持久化、各宿主注入**（`--steps-dir` 的先例，[0037](./0037-distribution-and-packaging.md) 决策 4）——让云端使用方不必烙镜像。留口子不做：等 A/B 数据与真实需求；本机 spawn / 前台 Fargate / detached Lambda / 能力自述四个注入面就是四个会漂的地方。
- **在 gherkai 侧为各家模型写适配**——Midscene 已有 family 适配器，复刻即第二事实源；Nova 侧只有一个服务，无此需求。
- **Midscene 无 family 的视觉模型**（Amazon Nova Lite / Pro、Claude、Gemma 3、Mistral）——要自写适配器，违背薄 worker（[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)）。
- **单一 family 硬编码**（旧态 `MIDSCENE_USE_QWEN3_VL: "true"`）——被推断表 + 显式覆盖替代。
- **IaC 按模型 pin `bedrock:InvokeModel`，换模型经 `gherkai deploy` 加放行参数**——每换一次模型就要重部署，且 IaC 跨工程耦合 worker 常量（曾靠跨语言对拍测试盯一致）；放宽到资源类型一次解决。

## 边界与互链

- [0004](./0004-novaact-iam-auth-via-workflow.md)：Nova 鉴权形态与 Nova 侧选型证据。
- [0036](./0036-deterministic-capability-discovery.md)「5.」：自述对象的 `model_id` 键。
- [0038](./0038-worker-image-delivery.md)：云端覆盖走 variant 镜像 `ENV`。
- [0042](./0042-step-evidence-and-explain.md) 决策六：SDK 版本钉死，与本 ADR 的模型钉版同一逻辑。
