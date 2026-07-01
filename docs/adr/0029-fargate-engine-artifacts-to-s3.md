# Fargate Engine adapter 的 artifact→S3：worker 上传、core 不透明搬运（前瞻 draft）

> **状态：draft / proposed（前瞻，未实现）。** Fargate Engine adapter 尚未编码；本 ADR 是一次 SDK 调查
> 的**决策暂存**——把"远程执行模式下 artifact 怎么到 S3"的责任划分先定下来、把调查证据与未决点记牢，
> 待真做 Fargate adapter 时落地（届时本 ADR 转正、补实测结论）。当前 v1.0/v1.1 仍是本地子进程模式
> （[0026](./0026-schedule-module.md) 子进程 adapter），artifact 写本地盘、报 `file://`，不涉及本 ADR。

## 背景：共享文件系统假设在 Fargate 下断了

现状（本地子进程，[0026](./0026-schedule-module.md)/[0024](./0024-worker-core-protocol.md)）：worker 把 trajectory/report
写本地盘（cli 经 env `NOVA_LOGS_DIR`/`MIDSCENE_RUN_DIR` 传产物目录），经 [0024](./0024-worker-core-protocol.md)
`report_refs`（`file://` URI）报给 core，core 不透明搬运、归集成 RunReport（[0027](./0027-runreport-aggregation-index.md)）。
**这成立的前提是 worker 与 core 同机、共享文件系统**——core 直接读得到 worker 写的盘。

未来 Fargate 模式（[0017](./0017-fargate-execution.md) 倾向）：worker 在远程 ECS 容器跑，**容器盘不与 core 共享、且容器停即销毁**。
于是核心问题：**这些 artifact 怎么从容器临时盘到持久的 S3？谁负责上传？**

## 决定：artifact→S3 是 **worker（容器内）** 的职责，core/ReportStore 一行不改

**worker 在容器内写本地产物 → 上传 S3 → 报 `s3://` ref；core/ReportStore 对 ref 不透明搬运（不 stat/不 fetch/不打开），原样归进 RunReport。** 责任划分：

| 角色 | 职责 |
|---|---|
| **worker（容器内）** | 写产物到本地路径 → **上传 S3** → 报 `s3://<bucket>/<prefix>/...` 作 `report_refs.ref`（经 [0024](./0024-worker-core-protocol.md)） |
| **Fargate Engine adapter**（新写，替代 SubprocessEngine） | 只换"怎么起 worker / 怎么停"——`run_scope`→ECS `RunTask`、`handle.stop`→`StopTask`（[0026](./0026-schedule-module.md) 已把信号/进程知识封在 adapter）；S3 落点配置（bucket/prefix/run_id）经 task env 注入（对称现 `compose.py` 经 `NOVA_LOGS_DIR` 注入本地目录） |
| **core / ReportStore / wire / schedule / model** | **一行不改**。`ReportRef.ref` 与 `ReportStore.write` 已是 `ResourceUri`（带 scheme 的统一指针，[0027](./0027-runreport-aggregation-index.md) 封版补丁所立——当时即为 S3 收口）；`s3://` ref 天然穿透 |

**为何 worker 上传、而非 core 去拉**：① "谁产出、谁知落点、谁上传"——worker 在容器内、最知道文件在哪/何时写完（与"产物落点自报"同源，[0028](./0028-transient-network-ssl-resilience.md) 留口子节）；② 让 core 去容器拉文件再传 S3，会把 ECS 卷/容器生命周期/S3 client 知识泄进核心，违背窄腰（[0016](./0016-execution-architecture-core-lib-run-model.md)）；③ 兑现 [0027](./0027-runreport-aggregation-index.md)「新引擎/新落点零改 core」契约——`s3://` 正是 `ResourceUri` 当初留的形态。

**core 不改的代码级依据**（调查已逐行核实）：`ReportRef.ref`/`ReportStore.write` 为 `ResourceUri`（`core/model.py` NewType）；`LocalReportStore._local_path` 对非 `file://` scheme 返回 `None` → `s3://` ref 在归集时走 `href==ref` 原样保留，连 `materialize=True` 也不去碰它（`_local_path` None → 不拷）；`index.html` 渲染只 `escape(href)` 拼 `<a>`，不 stat/open。

## 两引擎不对称：统一在 core/协议层，分头在 worker 上传实现层

SDK 调查证实两引擎产物形态/上传能力不对称，"上传那一小段"没法共用一份代码——但这本就是 [0024](./0024-worker-core-protocol.md)「协议形状一致、各语言各写」的现实，非新增分裂。

| | Nova Act（Python） | Midscene（TS） |
|---|---|---|
| 产物形态 | **每 act 一组文件**（`.html`+`_trajectory.json`+`_traces.json`），落 `logs_directory/<session_id>/`；session 末补 `session_summary.json` | **单文件** `report.html`（默认 `single-html`，截图 inline base64、自包含） |
| SDK 能否上传 S3 | **有官方通道**：`S3Writer`（实现 `StopHook` 协议），`NovaAct(logs_directory=本地, stop_hooks=[S3Writer(boto, bucket, prefix)])`，session 停止时自动 `os.walk` 整目录 `boto3 upload_file` | **无任何 S3 能力**（落点写死 `getMidsceneRunSubDir('report')`，仅 `MIDSCENE_RUN_DIR`/`reportFileName`/`outputFormat` 可调，无 sink） |
| Fargate 上传做法 | 给 NovaAct 注册 `S3Writer`（或自写 `StopHook`），报 `s3://`。**注意**：`logs_directory` 只接已存在的本地目录（`validate_path` 用 `os.path.isdir`，`s3://` 直接被拒），**不能让 SDK 直写 S3**——是"写本地、停时上传" | worker 手动：`destroy()` 后从 `agent.reportFile` 读单 html → `@aws-sdk/client-s3 PutObject` → 报 `s3://`。建议显式设 `MIDSCENE_RUN_DIR=/tmp/midscene_run` 使落点可控 |

**共享的环境契约**（两引擎都需要）：容器内有 boto3/aws-sdk + S3 写权限（ECS task role）+ 一个 run/scope 维度的 S3 key 前缀约定。

## 最大风险：中断丢失在 Fargate 下严重升级（必须先解）

**这是本调查比"能不能传"更要紧的发现。** 本地子进程模式下 worker 死了产物还在 core 共享盘（[0028](./0028-transient-network-ssl-resilience.md) #3：超时被杀 scope 的 trajectory 至少"留在磁盘"，可手动找）；**Fargate 容器盘停即销毁**，而两引擎的上传都挂在"干净结束"路径：

- **Nova**：`S3Writer.on_stop` 只在 session **干净停止**触发；SIGTERM 中途通常来不及跑完整目录 `os.walk`+逐文件 upload，且 `on_stop` 抛错被 SDK `_execute_stop_hooks` **静默吞**（只 `_LOGGER.error`，worker 感知不到上传失败）→ 静默丢产物。
- **Midscene**：现 SIGTERM handler 只做会话 cleanup + `process.exit`，**根本不碰 report** → 中断产物 100% 丢。

**结论倾向**：Fargate 模式**不能纯靠"结束批量上传"**，需 **act/step 粒度即时上传**缩小丢失窗口（Nova 无 per-act 写盘后 hook，只能 worker 在每 act 返回后立即自传该 act 文件；Midscene report 边跑边 `appendFile`，可在中断路径读当前 `reportFile` 抢传），并要求 Fargate `stopTimeout`(grace) 足够长 + 上传幂等/可续传。**这是真做 Fargate 前的头号待解项。**

## 调查依据（SDK 源码逐行核实，2026-06；细节存于调查产物，此处只记结论锚点）

- **Nova `logs_directory` 本地 only**：`nova_act/impl/inputs.py:60` `validate_path` → `os.path.isdir` 拒 `s3://`；None 时回落 `tempfile.mkdtemp`（非持久）。
- **Nova 官方 S3 通道**：`nova_act/util/s3_writer.py:26` `class S3Writer(StopHook)`，`on_stop` 里 `os.walk(get_logs_directory())` + `bucket.upload_file`；构造期 `head_bucket`+`list_objects` 预检权限（bucket/IAM 错在**建会话阶段**就抛）。`StopHook` 是通用协议（`nova_act/types/hooks.py`），可自写。
- **Nova 写盘时机**：per-act 文件在 `_act()` 的 `finally`→`RunInfoCompiler.compile()` 即写（非批量，非原子——`.html`/`.json` 分多次 `open` 顺序写，故中断可留"孤零 `.html`"）；`session_summary.json` 仅 `_stop()` 写一次。
- **Midscene 落点写死本地**：`@midscene/core` `report-generator.js` `getMidsceneRunSubDir('report')`=`cwd/MIDSCENE_RUN_DIR/report/`；无 S3/sink；`agent.reportFile` 构造后即有绝对路径（不必等 destroy）。report 边跑边 `appendFile`（每 task flush），中断时盘上已是"含已完成 task 的部分有效 html"。

## 留口子 / 待真做时定

- **上传时机**（头号项）：act/step 粒度即时上传 vs 结束批量；与 grace 预算、上传幂等/续传一起定。需真容器发 SIGTERM 实测。
- **S3 key 命名 ↔ `ResourceUri` `s3://` 形态**：`S3Writer` 默认 key=`<prefix><session_id>/<相对路径>`，与本仓 `reports/<run_id>/scope/scenario` 归集语义不同——需定"prefix 怎么编码 run_id/scope_id"+"worker 报的 `s3://` ref 与实际上传 key 逐字一致"（否则 index 链接断）。
- **`materialize` 在 `S3ReportStore` 下的目标语义（已定，实现分两步）**：目标**对标 Local**——Local 的 `materialize=True` 把产物收拢进 `reports/<run_id>/artifacts/`、链接转相对求自包含；S3 版对称地把产物收拢进 **`s3://bucket/<prefix>/<run_id>/artifacts/`**、链接转相对（同一概念换存储介质，非新范式）。产物**原位**可能 `file://`（subprocess worker 本地）或 `s3://`（Fargate worker 已传，本 ADR 路径），故 S3 materialize 要处理两种源：`file://` 源 → upload 到 report 前缀；`s3://` 源 → `copy_object` 到 report 前缀（「materialize 语义跨 worker 模式」的体现）。
  - **v1.1 第一版 `S3ReportStore`：`materialize` 当 no-op**（收到 `True` 也忽略、**不报错**——cli 会透传 `--materialize`，报错会炸）。第一版只把核心事做对：**把 RunReport 自身（manifest.json + index.html）写上 S3、返回 `s3://…/index.html` 的 `ResourceUri`**，`href==ref`。产物收拢到 S3 `artifacts/` 的自包含实现留后续（目标已定如上，不再纠结）。
  - 交付的是「链接可能不完全可点」的 S3 RunReport（`file://` 链接跨机器断、`s3://` 链接待 presign）——**已知、接受**的第一版取舍。确认不反向逼 core 改 `_collect`/`_entry`（S3ReportStore 复用现有 `_render_index_html`、只换落点与返回 scheme）。
- **S3 上传错误的分类**：`S3Writer` 构造期预检失败 / 上传失败，算 `network_error` 还是 `engine_error`、是否进 worker 建连重试域（[0028](./0028-transient-network-ssl-resilience.md)）——待定。
- **botocore/aws-sdk 默认 retry 与 grace 冲突**：上传走 SDK 默认 retry，退化网络下可能吃光 grace 被 SIGKILL 截断（[0028](./0028-transient-network-ssl-resilience.md) 建连段已为此手写退避不用 botocore retry）；上传路径是否也要手写超时/退避预算，需实测。
- **AgentCore 后端下产物真实落点**：源码看 `logs_directory`/`reportFile` 都在 worker 容器本地盘（SDK 进程本地 `open`/`appendFile`），但截图数据经 CDP 从云浏览器回传——未直接证伪"文件确在容器本地盘"。需真跑确认，否则"worker 上传容器盘文件"前提不成立。

## 重议

- 若 `S3ReportStore`（materialize/归档语义）需求逼出更多结构 → 它是新增 adapter，按 [0027](./0027-runreport-aggregation-index.md) 预期实现，不改 core 逻辑。
- 若中断丢失即时上传仍挡不住高频丢产物 → 另议（如云浏览器侧落盘 / 边录边传的流式 sink）。
