# engine artifact→S3：worker 上传、由组合根注入的 S3 落点驱动（落点跟 `--backend cloud`，非绑 Fargate）

> **Status:** Draft —— 决策已定、Fargate 执行 adapter 尚未编码；但**产物上传本身不绑 Fargate**——「subprocess worker + `--backend cloud` 也上传 S3」这部分可先行实现（不依赖 Fargate、且能提前验证云端报告链接闭环，见下）。传输层（事件怎么从远程 worker 回 core）不在本 ADR，见 [0024](./0024-worker-core-protocol.md)「远程传输演进」。

## 本 ADR 只管一件事：artifact 怎么到 S3（传输层剥离到 0024）

Fargate 化牵动两条**正交**的边：① **产物落点**（trajectory/report 怎么持久化到 S3）；② **传输层**（core 怎么把 job 喂给远程 worker、怎么收回事件流）。**本 ADR 只管 ①**。② 是 worker↔core 协议的传输演进（管道在 Fargate 下无对等物、事件走专用 fd 而非 stdout 故 awslogs 抓不到、worker 应为 producer 而非 server），已剥离到 [0024](./0024-worker-core-protocol.md)「远程传输演进」，本 ADR 不重述以免漂移。

## 背景：上传能力此前被误绑在 Fargate

**修正前的旧立场**：把"artifact→S3"完全绑定 Fargate——"当前本地子进程模式 artifact 写本地盘、报 `file://`，不涉及本 ADR"。**这个绑定是错的**：产物落点该由**注入的 S3 落点配置**决定（有 → 传 S3 报 `s3://`，无 → 报 `file://`），而不是由"worker 在哪跑"决定。绑 Fargate 的代价是——`--backend cloud` 下 RunReport（index.html）已上 S3，但里面的产物链接还是 `file:///Users/...`（跨机器断），而这条「index 的 `s3://` 链接对不对」正是本 ADR「留口子」列为头号未决的东西，却要一直等到 Fargate 才验得上。

**修正后**：上传由**组合根注入的 S3 落点配置**驱动（[0016](./0016-execution-architecture-core-lib-run-model.md)「注入、非 env-sniff」），**落点配置跟 `--backend cloud` 走、不跟执行环境走**。于是：

- **`subprocess worker + --backend cloud`**：worker 也上传 S3、报 `s3://`——它是 `fargate + cloud` 的**忠实预演**（唯一差别是 worker 进程在本地还是容器，而那对报告链接正确性无影响）。**现在就能端到端验证** worker 报的 ref ↔ `S3ReportStore` 归集 ↔ index.html 链接可点这整条链，不必等 Fargate。
- **`subprocess worker + --backend local`**：worker 与 core 同机、共享盘，core 直接读得到 → 报 `file://`、不传（不注入 S3 落点）。
- **`fargate worker`**：容器盘停即销毁、core 读不到 → **组合根必须注入 S3 落点**（否则产物必丢，故 fargate 下注入不是可选）。

即：**触发上传的判据始终只有一个**——组合根有没有注入 S3 落点。worker 对"我在哪跑"无知。变的只是**组合根按什么注入**：cloud backend → 注入（subprocess/fargate 都传）；local backend + subprocess → 不注入（同机可读）；fargate → 强制注入（无论 backend，盘会销毁）。这正是 [0016](./0016-execution-architecture-core-lib-run-model.md)「组合根注入」与「worker 引擎逻辑不按执行环境分」的兑现。

## 决定：artifact→S3 是 **worker** 的职责，由注入的 S3 落点配置驱动；core/ReportStore 一行不改

**worker 写本地产物 →（若拿到注入的 S3 落点配置）上传 S3、报 `s3://` ref，否则报 `file://`；core/ReportStore 对 ref 不透明搬运（不 stat/不 fetch/不打开），原样归进 RunReport。** 责任划分：

| 角色 | 职责 |
|---|---|
| **worker** | 写产物到本地路径 →（**拿到注入的 S3 落点配置时**）上传 S3、报 `s3://<bucket>/<prefix>/...` 作 `report_refs.ref`（经 [0024](./0024-worker-core-protocol.md)）；未注入落点则报 `file://`。上传成功后**删本地**（见下「删本地」）。worker 对"我在哪跑"无知——只认落点配置有没有 |
| **组合根（compose.py）** | 决定注入不注入 S3 落点（bucket/prefix/run_id）——**跟 `--backend cloud` 走**：cloud→注入（subprocess/fargate worker 都上传）、local→不注入（同机可读）。对称现在经 `NOVA_LOGS_DIR`/`MIDSCENE_RUN_DIR` 注入本地目录 |
| **Fargate Engine adapter**（新写，替代 SubprocessEngine，**属传输层、见 [0024](./0024-worker-core-protocol.md)**） | 换"怎么起 worker / 怎么停 / 事件怎么回"——`run_scope`→ECS `RunTask`、`handle.stop`→`StopTask`、事件走远程传输。这些是**传输**、不是产物落点，本 ADR 不展开（0024）。它注入 S3 落点的动作与 subprocess adapter 对称、无特殊性 |
| **core / ReportStore / wire / schedule / model** | **一行不改**。`ReportRef.ref` 与 `ReportStore.write` 已是 `ResourceUri`（带 scheme 的统一指针，[0027](./0027-runreport-aggregation-index.md) 封版补丁所立——当时即为 S3 收口）；`s3://` ref 天然穿透 |

**为何 worker 上传、而非 core 去拉**：① "谁产出、谁知落点、谁上传"——worker 在容器内、最知道文件在哪/何时写完（与"产物落点自报"同源，[0028](./0028-transient-network-ssl-resilience.md) 留口子节）；② 让 core 去容器拉文件再传 S3，会把 ECS 卷/容器生命周期/S3 client 知识泄进核心，违背窄腰（[0016](./0016-execution-architecture-core-lib-run-model.md)）；③ 兑现 [0027](./0027-runreport-aggregation-index.md)「新引擎/新落点零改 core」契约——`s3://` 正是 `ResourceUri` 当初留的形态。

**core 不改的代码级依据**（调查已逐行核实）：`ReportRef.ref`/`ReportStore.write` 为 `ResourceUri`（`core/model.py` NewType）；`LocalReportStore._local_path` 对非 `file://` scheme 返回 `None` → `s3://` ref 在归集时走 `href==ref` 原样保留，连 `materialize=True` 也不去碰它（`_local_path` None → 不拷）；`index.html` 渲染只 `escape(href)` 拼 `<a>`，不 stat/open。

## 两引擎不对称：统一在 core/协议层，分头在 worker 上传实现层——但**都是"写本地→传→删本地"，无一方直写 S3**

SDK 调查证实两引擎产物形态/上传能力不对称，"上传那一小段"没法共用一份代码——但这本就是 [0024](./0024-worker-core-protocol.md)「协议形状一致、各语言各写」的现实，非新增分裂。**关键澄清**：两个引擎**都做不到"SDK 直写 S3"**——SDK 都只写本地盘，上传是**写完之后**的一步（Nova 靠 stop-hook、Midscene 靠手动 PutObject），故两腿其实**同构**：写本地 → 上传 S3 → 删本地。终态是 S3 单份（"不多传一份"），但路径上都要过一次本地盘（SDK 使然）。

| | Nova Act（Python） | Midscene（TS） |
|---|---|---|
| 产物形态 | **每 act 一组文件**（`.html`+`_trajectory.json`+`_traces.json`），落 `logs_directory/<session_id>/`；session 末补 `session_summary.json` | **单文件** `report.html`（默认 `single-html`，截图 inline base64、自包含） |
| SDK 能否**直写** S3 | **不能**。`logs_directory` 只接已存在的本地目录（`validate_path` 用 `os.path.isdir`，`s3://` 直接被拒）——SDK 必须写本地。官方给的是**写完再传**的通道 `S3Writer`（实现 `StopHook`），session 停止时 `os.walk` 本地目录逐文件 `upload_file` | **不能**，且无任何 S3 能力（落点写死 `getMidsceneRunSubDir('report')`，仅 `MIDSCENE_RUN_DIR`/`reportFileName`/`outputFormat` 可调，无 sink） |
| 上传做法 | 给 NovaAct 注册 `S3Writer`（或自写 `StopHook`），传完报 `s3://`。是"写本地、停时上传"——**非 SDK 直写** | worker 手动：`destroy()` 后从 `agent.reportFile` 读单 html → `@aws-sdk/client-s3 PutObject` → 报 `s3://`。建议显式设 `MIDSCENE_RUN_DIR=/tmp/midscene_run` 使落点可控 |
| 删本地 | 上传成功确认后删 `logs_directory/<session_id>/`（subprocess+cloud 下 `NOVA_LOGS_DIR` 是持久目录、不删会残留；fargate 下容器销毁自然清，为对称/预演一致仍主动删） | 上传成功确认后删 `agent.reportFile` |

**共享的环境契约**（两引擎都需要）：进程内有 boto3/aws-sdk + S3 写权限（subprocess+cloud=本地 AWS 凭证 / fargate=ECS task role）+ 一个 run/scope 维度的 S3 key 前缀约定。

## 删本地：必须以「上传成功确认」为前提，且中断场景单独权衡

上传后删本地是为达成"S3 单份、不占本地盘"（尤其 subprocess+cloud 下 `NOVA_LOGS_DIR` 持久目录会累积）。但删本地**移除了一张安全网**——必须守两条：

1. **删的前提是「上传成功确认」**：先确认 `PutObject`/`upload_file` 成功返回，再删本地；上传失败绝不删（否则上传失败 + 已删本地 = 双丢）。
2. **中断场景单独权衡**：subprocess 模式下，本地盘原本是 [0028](./0028-transient-network-ssl-resilience.md) #3 的兜底——"超时/中止被杀的 scope，trajectory **可能留在** `nova-trajectories/<session_id>/`，靠 `session_id` 可**手动定位**"。一旦改成"上传成功后删本地"，被 SIGKILL 中途杀掉的 worker 会落在最糟组合：上传可能没跑完（SIGKILL 不给清理机会），而本地文件的存在性也不再可靠（要么已删、要么在但无人知晓）——0028 #3 的"至少留在磁盘、可手动找"前提随之失效。**故删本地不能无条件下放到中断路径**；恰当的孤儿恢复归 **Engine adapter 的中断收尾职责**（[0028](./0028-transient-network-ssl-resilience.md) #3 已论证：本地扫目录 / Fargate 查 S3，因执行基底而异），不放 worker 的 SIGTERM 路径、不破 [0027](./0027-runreport-aggregation-index.md) ReportStore 铁律。

（这条与下节"中断丢失"同族——都是"干净结束才上传成功"的脆弱性，只是删本地把它从 Fargate 提前到了 subprocess+cloud。）

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

## 分期：哪些可先行（subprocess+cloud）、哪些必须等 Fargate

上传能力从 Fargate 解绑后，实现分两期：

- **第一期（可先行，不依赖 Fargate）**：`subprocess worker + --backend cloud` 下上传 S3、报 `s3://`、删本地。这一期就能**端到端验证云端报告链接闭环**（worker 报的 `s3://` ref ↔ `S3ReportStore` 归集 ↔ index.html 链接可点），把下面「S3 key 命名」「上传错误分类」这些原本要等 Fargate 的未决点**提前坐实**。它**不涉及**中断丢失升级（subprocess 本地盘仍在，只是"删本地"要守上节两条护栏）、也不涉及传输层改造（走现有管道）。
- **第二期（必须等 Fargate）**：远程执行下的中断丢失（容器盘停即销毁）、grace/stopTimeout 预算、即时上传粒度——这些是**执行环境**逼出的，subprocess 预演不到，见下「最大风险」与 [0024](./0024-worker-core-protocol.md) 传输演进。

## 留口子 / 待真做时定

- **上传时机**（Fargate 头号项，第一期不涉及）：act/step 粒度即时上传 vs 结束批量；与 grace 预算、上传幂等/续传一起定。需真容器发 SIGTERM 实测。
- **S3 key 命名 ↔ `ResourceUri` `s3://` 形态**（第一期即可坐实）：`S3Writer` 默认 key=`<prefix><session_id>/<相对路径>`，与本仓 `reports/<run_id>/scope/scenario` 归集语义不同——需定"prefix 怎么编码 run_id/scope_id"+"worker 报的 `s3://` ref 与实际上传 key 逐字一致"（否则 index 链接断）。**这条正是第一期要验的主目标。**
- **`materialize` 在 `S3ReportStore` 下的目标语义（已定，实现分两步）**：目标**对标 Local**——Local 的 `materialize=True` 把产物收拢进 `reports/<run_id>/artifacts/`、链接转相对求自包含；S3 版对称地把产物收拢进 **`s3://bucket/<prefix>/<run_id>/artifacts/`**、链接转相对（同一概念换存储介质，非新范式）。产物**原位**可能 `file://`（subprocess+local worker 本地）或 `s3://`（subprocess+cloud / Fargate worker 已传，本 ADR 路径），故 S3 materialize 要处理两种源：`file://` 源 → upload 到 report 前缀；`s3://` 源 → `copy_object` 到 report 前缀（「materialize 语义跨 worker 模式/backend」的体现）。
  - **v1.1 第一版 `S3ReportStore`：`materialize` 当 no-op**（收到 `True` 也忽略、**不报错**——cli 会透传 `--materialize`，报错会炸）。第一版只把核心事做对：**把 RunReport 自身（manifest.json + index.html）写上 S3、返回 `s3://…/index.html` 的 `ResourceUri`**，`href==ref`。产物收拢到 S3 `artifacts/` 的自包含实现留后续（目标已定如上，不再纠结）。
  - 交付的是「链接可能不完全可点」的 S3 RunReport（`file://` 链接跨机器断、`s3://` 链接待 presign）——**已知、接受**的第一版取舍。确认不反向逼 core 改 `_collect`/`_entry`（S3ReportStore 复用现有 `_render_index_html`、只换落点与返回 scheme）。
- **S3 上传错误的分类**：`S3Writer` 构造期预检失败 / 上传失败，算 `network_error` 还是 `engine_error`、是否进 worker 建连重试域（[0028](./0028-transient-network-ssl-resilience.md)）——待定。
- **botocore/aws-sdk 默认 retry 与 grace 冲突**：上传走 SDK 默认 retry，退化网络下可能吃光 grace 被 SIGKILL 截断（[0028](./0028-transient-network-ssl-resilience.md) 建连段已为此手写退避不用 botocore retry）；上传路径是否也要手写超时/退避预算，需实测。
- **AgentCore 后端下产物真实落点（已由真跑证实）**：源码看 `logs_directory`/`reportFile` 都在 worker 进程本地盘（SDK 进程本地 `open`/`appendFile`），截图数据虽经 CDP 从云浏览器回传，但**文件确落 worker 本地盘**——`--backend cloud` 真跑（subprocess worker）产物落在本地 `cli/reports/<run_id>/{nova-trajectories,midscene-run}/`，report+run 元信息才上 S3/DDB。故"worker 上传其本地盘文件"前提成立（Fargate 下即容器盘）。

## 重议

- 若 `S3ReportStore`（materialize/归档语义）需求逼出更多结构 → 它是新增 adapter，按 [0027](./0027-runreport-aggregation-index.md) 预期实现，不改 core 逻辑。
- 若中断丢失即时上传仍挡不住高频丢产物 → 另议（如云浏览器侧落盘 / 边录边传的流式 sink）。
