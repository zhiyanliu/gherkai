# Fargate 执行环境：容器盘停即销毁逼出的中断丢失、grace、即时上传（前瞻 draft）

> **Status:** Draft —— Fargate 执行 adapter 尚未编码。本 ADR 收「Fargate/ECS 执行环境**特有**」的问题：容器盘停即销毁的 artifact 中断丢失、grace/stopTimeout 预算、act 粒度即时上传。上传机制本身见 [0029](./0029-engine-artifacts-to-s3.md)（不绑执行环境、subprocess+cloud 已实现）；远程事件传输见 [0024](./0024-worker-core-protocol.md)「远程传输演进」；为何倾向 Fargate 见 [0017](./0017-cloud-execution-fargate-over-runtime.md)。

## 定位：只收「执行环境特有」的一条边

云端化的三条正交边（[0029](./0029-engine-artifacts-to-s3.md) 已划）里，本 ADR 只管 **③ Fargate 执行环境特有**——即"worker 从本地子进程搬进 ECS 容器"这一步**新引入**的问题。**不重述**上传机制（[0029](./0029-engine-artifacts-to-s3.md)：worker 手动上传、key 镜像 run 树、删本地——subprocess+cloud 已做，Fargate 直接复用）与远程传输（[0024](./0024-worker-core-protocol.md)：job-in 走 S3、events-out 走 SQS、stop→StopTask、退出码→DescribeTasks）。

**核心差异**：subprocess 模式 worker 死了产物还在本地盘（[0028](./0028-transient-network-ssl-resilience.md) #3：超时被杀 scope 的 trajectory 至少"留在磁盘"、靠 `session_id` 可手动找）；**Fargate 容器盘停即销毁**——这把"干净结束才上传成功"的脆弱性从"可手动补救"升级成"直接丢"。

## 最大风险：中断丢失在 Fargate 下严重升级（真做前头号待解）

**这是 SDK 调查比"能不能传"更要紧的发现。** [0029](./0029-engine-artifacts-to-s3.md) 的上传（第一期=结束批量）挂在"干净结束"路径——Fargate 下 SIGTERM 中途被杀、容器盘随即销毁，产物直接丢：

- **Nova**：per-act 文件在 `_act()` 的 `finally`→`RunInfoCompiler.compile()` 即写盘（非批量、非原子——`.html`/`.json` 分多次 `open` 顺序写，中断可留"孤零 `.html`"）；结束批量上传若在 SIGTERM 后来不及跑完 → 未上传部分随容器盘销毁而丢。
- **Midscene**：report 边跑边 `appendFile`（每 task flush），中断时盘上已是"含已完成 task 的部分有效 html"；但 SIGTERM handler **只做会话 cleanup、不触达 report**（不上传中途 report）→ 中断产物随容器盘销毁而丢。补救（把抢传提前到 step 安全点）见 [0029](./0029-engine-artifacts-to-s3.md) 及 Journey 0001「Midscene 补救方向」。

**结论倾向**：Fargate 模式**不能纯靠 [0029](./0029-engine-artifacts-to-s3.md) 的"结束批量上传"**，需 **act/step 粒度即时上传**缩小丢失窗口（Nova 无 per-act 写盘后 hook，只能 worker 在每 act 返回后立即自传该 act 文件；Midscene 可在中断路径读当前 `reportFile` 抢传），并要求 Fargate `stopTimeout`(grace) 足够长 + 上传幂等/可续传。**这是真做 Fargate 前的头号待解项。**

## 留口子 / 待真做时定（Fargate 特有）

- **即时上传粒度**：act/step 粒度即时上传 vs [0029](./0029-engine-artifacts-to-s3.md) 的结束批量；与 grace 预算、上传幂等/续传一起定。需真容器发 SIGTERM 实测。
- **grace / stopTimeout 预算**：`handle.stop(grace_period_s)` 现是运行期传参（cli Nova 10s / schedule 5s）；Fargate `stopTimeout` 是 task-def 期常量、≤120s、不能逐次变（[0024](./0024-worker-core-protocol.md) 已记）——上传 + 会话清理必须挤进这个固定预算。
- **botocore/aws-sdk 默认 retry 与 grace 冲突**：上传走 SDK 默认 retry，退化网络下可能吃光 grace 被 SIGKILL 截断（[0028](./0028-transient-network-ssl-resilience.md) 建连段已为此手写退避不用 botocore retry）；上传路径是否也要手写超时/退避预算，需实测。
- **上传错误分类升级**：[0029](./0029-engine-artifacts-to-s3.md) 第一期上传失败=`engine_error`、不进重试域；Fargate 下是否细分 `network_error`、进 worker 建连重试域（[0028](./0028-transient-network-ssl-resilience.md)），与 grace 预算一起定。
- **孤儿产物恢复**：[0028](./0028-transient-network-ssl-resilience.md) #3 记的"中断收尾扫盘"在 Fargate 下从"本地扫目录"变成"查 S3 已传了哪些"——属 Engine adapter 的中断收尾职责，因执行基底而异。

## 重议

- 若中断即时上传仍挡不住高频丢产物 → 另议（如云浏览器侧落盘 / 边录边传的流式 sink）。
- 若 workload 形态变化使 Fargate 不再是执行面首选（[0017](./0017-cloud-execution-fargate-over-runtime.md) 翻盘条件）→ 本 ADR 的容器特有假设需重估。
