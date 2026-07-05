# Fargate 云端执行化：进度总纲 + task breakdown

> **类型：** Journey / 进度导航（**跨 WP 的计划状态**，非某次调查的证据——特定调查证据见 0001+）。
> **为何存在：** task 系统跨 compact/会话会丢；本文件入仓、是 compact 后接手工作的**第一份该读的**——一眼看到全局进度、各 WP 状态、指向哪份 ADR/证据。
> **维护：** 每完成一个 WP / 有新决策落 ADR，回来更新本文件的状态表 + 指针。**只记状态与导航，不记实现细节**（细节在 ADR/各专项 Journey/code）。

## 大目标

把 UI 测试框架的**执行面**搬上云：worker 从本地 subprocess → AWS Fargate/ECS 容器。
现状：存储面（RunStore→DDB、Result/Report→S3）+ 产物面（引擎产物→S3）已上云；**执行面仍是本地 subprocess**（worker 在本地跑、连远程 AgentCore 浏览器）。

## 两条正交轴（贯穿全局，勿混）

- **Engine adapter**（按执行环境分）：SubprocessEngine（现有）/ FargateEngine（待建）。
- **Engine worker**（按 AI 引擎分）：novaact（Python）/ midscene（TS）。
- **worker 引擎逻辑不按执行环境分**；worker 的 **I/O 边缘**（job 入口 / 事件 sink / 产物落点）才是随执行环境变的、应抽象成可注入接口（ADR 0016 组合根注入 / 0024 远程传输演进）。

## task breakdown + 状态

| WP | 内容 | 状态 | 落点/证据 |
|---|---|---|---|
| **WP-S** | 中断丢失实测预演 + 抢传验证（Fargate 中断韧性的事实前置） | ✅ 完成 | [journey/0001](./0001-wps-interruption-loss-spike.md)（5 发现、8 格数据、抢传验证、Midscene 补救方向） |
| **#7** | 修 Nova SIGTERM 中断模型（flag-only + act timeout + grace enforce）——WP0 入口条件、独立现有生产 bug | ✅ 完成（commit `7404bba`） | ADR 0024 终止契约 / 0028 / 0026 / 0032；证据 0001。三层测试 + 真跑验证 hung=false |
| **WP0** | worker I/O 边缘抽象成可注入接口（job source 读 stdin↔S3、event sink 写 EVENTS_FD↔SQS）；纯重构、零行为变化；对称已有 ArtifactUploader | ⬜ 待做（#7 已铺干净中断模型地基） | 依赖 #7✅ |
| **WP1** | Fargate 传输层：core SQS encode/decode + FargateEngine adapter（RunTask/StopTask/DescribeTasks）+ worker 注入 S3/SQS + schedule 存活判定迁移（事件流沉默→DescribeTasks） | ⬜ 待做 | ADR 0024「远程传输演进」（Draft）；依赖 WP0 接口定型 |
| **WP2** | 基础设施：Docker 镜像 + ECS task-def + IAM task role + SQS FIFO + cluster + IaC（全仓从零）+ 组合根 build_engines 补 Fargate 分支（当前 --backend cloud 仍返回 SubprocessEngine） | ⬜ 待做 | 依赖 WP1 接口定型 |
| **WP3** | Fargate 中断韧性：act 粒度即时上传（抢传，两腿不对称见 0001）+ grace/stopTimeout 预算 + botocore retry vs grace + 错误分类升级 + 孤儿产物恢复 | ⬜ 待做 | ADR 0032（Draft，收 Fargate 特有）；WP-S 预演数据 0001；依赖 WP1+WP2 |

## 已冻结的关键设计（ADR 索引，真做各 WP 前必读对应条）

- **ADR 0024**「远程传输演进」：port 抽象 survive、pipe 传输 die；job-in→S3、events-out→SQS FIFO（MessageGroupId=scope_id 保序）、stop→StopTask、退出码→DescribeTasks。**终止契约**：两腿会话释放契约 + Nova flag-only（#7 已实现）+ act 有界返回 + grace 硬约束（core enforce）+ 两条被拒护栏（raise 模型 / asyncio 化）。
- **ADR 0032**（Draft）：Fargate 执行环境特有——容器盘停即销毁的中断丢失、grace/stopTimeout 预算、act 粒度即时抢传。头号待解项=中断丢失（WP-S 已量化，见 0001）。
- **ADR 0029**（Accepted）：产物→S3 上传，subprocess+cloud 已实现、是 Fargate 忠实预演。Midscene 抢传补救方向见 0001。
- **ADR 0016**：core 纯库/窄腰/组合根注入/worker 引擎逻辑不按执行环境分——所有 WP 的架构红线。
- **ADR 0026**：schedule 纯 reducer、对引擎无知。

## 已确立的重要事实/取舍（防重新调研）

- **Nova 中断只能软停、非即时**（act 靠 SDK per-act timeout 有界返回，act 不幂等使即时打断无语义收益）——ADR 0024 / 0001。
- **asyncio 消除 greenlet 技术可行但被拒**（~5x 代价 + 建连侧 SDK 无 async provider 根不掉 + 仍需叠 flag-only）——ADR 0024 被拒护栏。
- **孤儿会话不做 core reaper**，靠 AgentCore 原生 session TTL（sessionTimeoutSeconds，默认 1h、可收紧）兜底——ADR 0024「已接受代价」。
- **Midscene 无 greenlet 卡死风险**（Node 单线程事件循环），#7 只改 Nova——ADR 0024 终止契约。
- **两腿抢传不对称**：Nova 每 act 独立 trajectory（distinct key 幂等）；Midscene 单份增长 report（overwrite 同 key、带宽/粒度取舍 + uploader 幂等守卫冲突 + agent 引用上提）——WP3 须单独设计，见 0001。

## 工作节奏（约定）

每个 WP 按「**设计冻结（落 ADR）→ 实现 → 两轮对抗 review（doc + code，workflow 分维度 finder + 对抗验证）→ commit**」走。改 code 前先落 ADR（CLAUDE.md 纪律）。commit 前两轮 review。
