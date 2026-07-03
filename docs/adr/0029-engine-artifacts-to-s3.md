# engine artifact→S3：worker 上传、由组合根注入的 S3 落点驱动（落点跟 `--backend cloud`，非绑执行环境）

> **Status:** Accepted —— 决策已定：上传由组合根注入的 S3 落点驱动、跟 `--backend cloud` 走（非绑 Fargate）；第一期 `subprocess+cloud` 上传按「第一期实现定论」节落地（进行中）。**Fargate 执行环境特有的**中断丢失/grace/即时上传见 [0032](./0032-fargate-execution-environment.md)；远程事件传输见 [0024](./0024-worker-core-protocol.md)「远程传输演进」。

## 本 ADR 只管一件事：engine 产物怎么到 S3（执行环境/传输层剥离）

云端化牵动三条**正交**的边，本 ADR **只管 ①**：
- ① **产物落点**（trajectory/report 怎么持久化到 S3）——本 ADR。
- ② **传输层**（core 怎么把 job 喂给远程 worker、怎么收事件流）——见 [0024](./0024-worker-core-protocol.md)「远程传输演进」。
- ③ **Fargate 执行环境特有**（容器盘停即销毁的中断丢失、grace/stopTimeout、即时上传粒度）——见 [0032](./0032-fargate-execution-environment.md)。

**产物落点与执行环境正交**：上传能力**不绑 Fargate**——`subprocess worker + --backend cloud` 也上传 S3（是 Fargate 的忠实预演）。故本 ADR 讲的"上传"现在（subprocess+cloud）就做，不必等 Fargate。

## 决策核心：上传由注入的 S3 落点驱动，不由"worker 在哪跑"决定

产物落点该由**组合根注入的 S3 落点配置**决定（有 → 传 S3 报 `s3://`，无 → 报 `file://`），而**不是**由执行环境（subprocess/fargate）决定（[0016](./0016-execution-architecture-core-lib-run-model.md)「注入、非 env-sniff」）。落点配置**跟 `--backend cloud` 走**。于是：

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
| **core / ReportStore / wire / schedule / model** | **一行不改**。`ReportRef.ref` 与 `ReportStore.write` 已是 `ResourceUri`（带 scheme 的统一指针，[0027](./0027-runreport-aggregation-index.md) 封版补丁所立——当时即为 S3 收口）；`s3://` ref 天然穿透 |

（注：Fargate Engine adapter「怎么起 worker/怎么停/事件怎么回」属传输/执行环境，见 [0024](./0024-worker-core-protocol.md)/[0032](./0032-fargate-execution-environment.md)——它注入 S3 落点的动作与 subprocess adapter 对称、无特殊性，不在本 ADR。）

**为何 worker 上传、而非 core 去拉**：① "谁产出、谁知落点、谁上传"——worker 在容器内、最知道文件在哪/何时写完（与"产物落点自报"同源，[0028](./0028-transient-network-ssl-resilience.md) 留口子节）；② 让 core 去容器拉文件再传 S3，会把 ECS 卷/容器生命周期/S3 client 知识泄进核心，违背窄腰（[0016](./0016-execution-architecture-core-lib-run-model.md)）；③ 兑现 [0027](./0027-runreport-aggregation-index.md)「新引擎/新落点零改 core」契约——`s3://` 正是 `ResourceUri` 当初留的形态。

**core 不改的代码级依据**（调查已逐行核实）：`ReportRef.ref`/`ReportStore.write` 为 `ResourceUri`（`core/model.py` NewType）；`make_href` 对非 `file://` scheme（含 `s3://`）恒 `href==ref` 原样保留（只 `file://` 且落 run 树内才相对化，[0027](./0027-runreport-aggregation-index.md)「href 相对化」）；`index.html` 渲染只 `escape(href)` 拼 `<a>`，不 stat/open。

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

（这条与 Fargate 的"中断丢失"同族——都是"干净结束才上传成功"的脆弱性，只是删本地把它从 Fargate 提前到了 subprocess+cloud。Fargate 下容器盘停即销毁使它严重升级，见 [0032](./0032-fargate-execution-environment.md)。）

## 调查依据（SDK 源码逐行核实，2026-06；细节存于调查产物，此处只记结论锚点）

- **Nova `logs_directory` 本地 only**：`nova_act/impl/inputs.py:60` `validate_path` → `os.path.isdir` 拒 `s3://`；None 时回落 `tempfile.mkdtemp`（非持久）。
- **Nova 官方 S3 通道**：`nova_act/util/s3_writer.py:26` `class S3Writer(StopHook)`，`on_stop` 里 `os.walk(get_logs_directory())` + `bucket.upload_file`；构造期 `head_bucket`+`list_objects` 预检权限（bucket/IAM 错在**建会话阶段**就抛）。`StopHook` 是通用协议（`nova_act/types/hooks.py`），可自写。
- **Nova 写盘时机**：per-act 文件在 `_act()` 的 `finally`→`RunInfoCompiler.compile()` 即写（非批量，非原子——`.html`/`.json` 分多次 `open` 顺序写，故中断可留"孤零 `.html`"）；`session_summary.json` 仅 `_stop()` 写一次。
- **Midscene 落点写死本地**：`@midscene/core` `report-generator.js` `getMidsceneRunSubDir('report')`=`cwd/MIDSCENE_RUN_DIR/report/`；无 S3/sink；`agent.reportFile` 构造后即有绝对路径（不必等 destroy）。report 边跑边 `appendFile`（每 task flush），中断时盘上已是"含已完成 task 的部分有效 html"。

## 分期：上传第一期（subprocess+cloud，现在做）/ Fargate 增强（未来）

上传能力从执行环境解绑后，实现分两期：

- **第一期（本 ADR，subprocess+cloud，不依赖 Fargate）**：`subprocess worker + --backend cloud` 下上传 S3、报 `s3://`、删本地。这一期就能**端到端验证云端报告链接闭环**（worker 报的 `s3://` ref ↔ `S3ReportStore` 归集 ↔ index.html 链接可点），把「S3 key 命名」「上传错误分类」等未决点**提前坐实**（见下「第一期实现定论」）。它**不涉及**中断丢失升级（subprocess 本地盘仍在，只是"删本地"守两条护栏）、也不涉及传输层改造（走现有管道）。
- **Fargate 增强（[0032](./0032-fargate-execution-environment.md)，未来）**：远程执行下容器盘停即销毁逼出的中断丢失、grace/stopTimeout 预算、act 粒度即时上传——这些是**执行环境**特有的，subprocess 预演不到，属 [0032](./0032-fargate-execution-environment.md)；远程事件传输见 [0024](./0024-worker-core-protocol.md)。

## 第一期实现定论（subprocess+cloud，已敲定）

第一期真做时把下面几点从"待定"钉死（原"留口子"里对应项标状态）：

- **注入机制（组合根，非 env-sniff）**：cloud 时 `compose.build_engines` 给 worker 多注入一组 S3 落点 env——`ARTIFACT_S3_BUCKET` + `ARTIFACT_S3_PREFIX`（=`<report_dir>/<run_id>/`），对称现有 `NOVA_LOGS_DIR`/`MIDSCENE_RUN_DIR`。**local 不注入 → worker 走原 `file://` 路径、零行为变化**。worker 只认"有没有这组 env"，对"我在哪跑（subprocess/fargate）"无知（[0016](./0016-execution-architecture-core-lib-run-model.md) 注入红线）。
- **两腿都 worker 手动上传（boto3 / @aws-sdk/client-s3）**：Nova 不用官方 `S3Writer` stop-hook，改 worker 手动 `upload_file`——与 Midscene 手动 `PutObject` 对称、时序完全可控（先确认上传成功再删本地）、上传错误直接可观测（不被 SDK 静默吞）。
- **S3 key 镜像本地 run 树**：产物 key = `ARTIFACT_S3_PREFIX` + 产物在本地 run 树内的相对路径（如 `<report_dir>/<run_id>/nova-trajectories/<session>/act_0.html`、`.../midscene-run/report/x.html`）。**与 index.html/manifest 同前缀**（`S3ReportStore` 也写在 `<prefix>/<run_id>/` 下），布局工整、为将来 cloud href 相对化留一致结构。**worker 报的 `s3://bucket/<key>` ref 必须与实际上传 key 逐字一致**（否则 index 链接断）——这是第一期主验目标。
- **上传时机 = 结束批量**（非 act 粒度即时）：scope 末一次性上传该 scope 产生的所有产物。**subprocess 本地盘不销毁、无中断丢失压力**，批量最简够用；act 粒度即时上传是第二期（Fargate 容器盘停即销毁）才需要的，第一期不做。
- **删本地 = 上传成功确认后删**：`upload_file`/`PutObject` 成功返回后才删对应本地文件（达成"S3 单份"）；**上传失败绝不删**（守上节「删本地」两条护栏，避免双丢）。
- **上传错误分类 = `engine_error`、不进重试域**：第一期上传失败归 `engine_error`（act 不幂等、网络重试是第二期 Fargate 才细化的，[0028](./0028-transient-network-ssl-resilience.md)）；上传失败让 worker 可观测（报 error / 非 0 退出），不静默吞。
- **core / ReportStore 一行不改**：`s3://` ref 天然穿透（[0027](./0027-runreport-aggregation-index.md)，a 已验 `href==ref` for s3://）。

## 留口子 / 待真做时定

- **~~S3 key 命名 ↔ `ResourceUri` `s3://` 形态~~（第一期已定，见上「第一期实现定论」）**：定为「S3 key 镜像本地 run 树、与 report 同 `<prefix>/<run_id>/` 前缀、worker 报的 `s3://` ref 与上传 key 逐字一致」。不沿用 `S3Writer` 默认的 `<prefix><session_id>/` 布局（那与 report 的 `<run_id>/` 归集语义不匹配）。
- **~~S3 上传错误的分类~~（第一期已定，见上）**：第一期=`engine_error`、不进重试域、可观测（不静默吞）。是否细分 `network_error`/进重试域待 Fargate（[0032](./0032-fargate-execution-environment.md)，与 grace 预算一起定）。
- **~~`materialize` 在 `S3ReportStore` 下的目标语义~~（已废——materialize 整体移除，[0027](./0027-runreport-aggregation-index.md)）**：曾计划 S3 版 materialize 把产物 `copy_object` 收拢进 `s3://…/<run_id>/artifacts/` 求自包含（对标 Local 的 `artifacts/` 拷贝）。**现已废弃**：① cloud 报告决定用 `s3://` 绝对链接（不 presign、`href==ref`）——`s3://` 全局可寻址、拷/分享不断，`copy_object` 进 `artifacts/` 零收益；② materialize 概念整体移除（[0027](./0027-runreport-aggregation-index.md)「被拒方案」）。故 `S3ReportStore` 只把 RunReport 自身（manifest+index）写 S3、`href==ref`（`s3://`），不做任何产物拷贝——这从「第一版 no-op 的临时取舍」转正为「终态设计」。
- **上传时机 / botocore retry vs grace / 中断即时上传**（Fargate 特有）：这些是容器盘停即销毁逼出的，移到 [0032](./0032-fargate-execution-environment.md)——第一期 subprocess+cloud 走结束批量、本地盘不销毁，不涉及。
- **AgentCore 后端下产物真实落点（已由真跑证实）**：源码看 `logs_directory`/`reportFile` 都在 worker 进程本地盘（SDK 进程本地 `open`/`appendFile`），截图数据虽经 CDP 从云浏览器回传，但**文件确落 worker 本地盘**——`--backend cloud` 真跑（subprocess worker）产物落在本地 `cli/reports/<run_id>/{nova-trajectories,midscene-run}/`，report+run 元信息才上 S3/DDB。故"worker 上传其本地盘文件"前提成立（Fargate 下即容器盘）。

## 重议

- 若 `S3ReportStore` 需求逼出更多结构 → 它是新增 adapter，按 [0027](./0027-runreport-aggregation-index.md) 预期实现，不改 core 逻辑。
