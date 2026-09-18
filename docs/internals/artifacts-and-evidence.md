# 产物与证据：产物落在哪、哪一份回答哪个问题（local × cloud）

> 本文讲**产物落在哪、哪一份用于回答哪个问题**（机制），不讨论为什么这样设计：设计决策与理由在各 ADR，本文只给指针；与代码或 ADR 不一致时以它们为准。一次 run 的产出横跨五个不同职责的载体（本地文件 / S3 / DynamoDB / CloudWatch / 引擎 SDK 自有目录），每个载体的决策各归一个 ADR；而「排障时该打开哪个文件」这个问题的答案分散在这五个载体上，需要合并才完整。

## 1. 五类产物，各回答一个问题

一次 run 的产出按**职责**分五类。分类比目录结构更重要：同一个目录里既有真值也有派生视图，混读会把派生视图当成判定源。

| 类别           | 内容                                                                                                                                                                                                                                        | 回答的问题                      | 落在哪（见 §2）                           | 可否删除                    |
|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------|-----------------------------------------|-----------------------------|
| **definition** | 提交时固定的 run 定义（run_id / created_at / 并发 / 每个 job 的 scope·engine·scenario·step 原文·timeout）                                                                                                                                     | 「这次提交了什么」                | `run_meta.json` / runs 表 `META` item   | 不能（判定树的骨架）          |
| **运行态**     | 控制面投影：run 级 status、各 job 的 status·session_id·claimed_at，以及事件水位（只有经推进器投影过的 run 才有这一项）                                                                                                                           | 「当前执行到哪 / 是否已提交」     | `run_state.json` / runs 表 `STATE` item | 可（可从判定真值重建）        |
| **判定真值** ★ | 每个 job 一份自包含的判定明细：job→scenario→step 的 status·votes·error_type·message·duration + 全部产物指针                                                                                                                                  | 「结果是什么、为什么」             | `jobs/<urlencode(scope_id)>.json`       | **不能**（唯一权威）          |
| **派生导航**   | `manifest.json`（机读扁平产物清单）+ `index.html`（判定明细树 + 每条产物一行链接，含锚点回跳）                                                                                                                                                   | 「人从哪里开始读」                | 同 run 目录                             | **可删可重建，永不作判定源** |
| **现场证据**   | 引擎原生产物（Nova trajectory `.html`+`_trajectory.json`、`session_summary.json`；Midscene `report/` 下的那份 HTML（文件名由 SDK 生成、含时间戳，不可按固定名查找）+ `report/screenshots/`）+ gherkai 自有的 step 级 `evidence.json` 与它引用的截图 | 「那一步模型看到了什么、如何推理」 | 各引擎产物子目录下（见 §2）               | 可（但删除后排障只剩状态码）  |

排障时最常用的三条推论：

- **判定读 `jobs/*.json`，不读 `index.html`**。`index.html` 里的判定树是从内存 `RunResult` 渲染的**派生视图**；`manifest.json` 不含判定（只有薄信封 + 扁平产物清单，靠 `run_id` 软引用回判定真值）。CI 判定读退出码或 `jobs/*.json`。
- **`run_state.json` 落后于 `jobs/*.json` 是正常的**：写序是「数据面先、控制面后」，读到 run 级终态即保证各 job 的判定明细已全部落盘；两者不一致时以 `jobs/*.json` 为准。
- **原始产物指针（`ref`）的权威落盘处只有 `jobs/*.json`**。`manifest.json` 每条只留 `href`（导航链接）、不留 `ref`；机读原始指针须取自判定真值，不取自派生视图。

> 权威：[ADR 0016](../adr/0016-execution-architecture-core-lib-run-model.md)（三层 port 切分：RunStore 控制面 / ResultStore 数据面 / ReportStore 派生视图）、[ADR 0027](../adr/0027-runreport-aggregation-index.md)（RunReport = 归集索引、manifest/index.html 形态、`href` 不含 `ref`）、[ADR 0030](../adr/0030-realtime-persistence-seam.md) 决定三（commit point 写序与失败语义）；字段逐个的含义见 [`./cli-json-contract.md`](./cli-json-contract.md)（本文不重复字段表）。

## 2. 物理位置：local 与 cloud 是同一棵树的两种载体

**关键对称**：cloud 的 S3 key **按相对 run 目录的路径镜像 local 的树**。两个 worker 上传器都以「产物本地绝对路径」减去「本地 run 树根」得到相对路径，再拼接 `<report_dir>/<run_id>/` 前缀构成 key（`keyFor` / Nova 侧同规则）。本机上的相对位置，在 S3 上是同一个相对位置。

下表逐行对齐两个载体，路径一律相对 run 目录根：local 的根是 `<report-dir>/<run_id>/`，cloud 的根是 `s3://<bucket>/<report_dir>/<run_id>/`。

| 相对路径                                                     | 类别                                                                    | cloud 落点 / 存在条件                                                         |
|--------------------------------------------------------------|-------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| `run_meta.json`                                              | definition                                                              | 不在桶里 → runs 表 `META` item                                                |
| `run_state.json`                                             | 运行态                                                                  | 不在桶里 → runs 表 `STATE` item                                               |
| `jobs/<enc>.json`                                            | ★判定真值                                                               | 同形同名                                                                      |
| `manifest.json`                                              | 派生导航                                                                | 同形同名                                                                      |
| `index.html`                                                 | 派生导航（人的入口）                                                      | 同形同名                                                                      |
| `nova-trajectories/<session_id>/`                            | 现场证据：Nova 原生（per-act 页 + 配套 trajectory json + 会话汇总）        | key 镜像相对路径                                                              |
| `nova-trajectories/evidence/<scenario 键>/step-<n>/`         | 现场证据：gherkai 自有（`evidence.json` + 帧截图 `act-<i>-frame-<j>.jpg`） | key 镜像相对路径                                                              |
| `midscene-run/report/`                                       | 现场证据：Midscene 原生（SDK 报告 HTML + `screenshots/`）                  | key 镜像相对路径                                                              |
| `midscene-run/log/`                                          | 现场证据：Midscene SDK 日志                                              | key 镜像相对路径                                                              |
| `midscene-run/evidence/<scenario 键>/step-<n>/evidence.json` | 现场证据：gherkai 自有                                                   | key 镜像相对路径                                                              |
| `worker.log`                                                 | 诊断日志                                                                | 仅 `--quiet` ∧ 本机执行时存在；cloud 无此文件 → 进 CloudWatch（组名与真值见 §5） |
| `reconcile.log`                                              | 诊断日志（本机后台推进进程的输出）                                        | 仅 local `submit`；cloud 档不生成（推进不在本机）                                |
| `events.db`                                                  | 事件通道（SQLite）                                                        | 仅 local `submit`；cloud 档事件在 events 表、不在桶里                           |
| `tunnel.json`                                                | 隧道收尾凭据（pid）                                                       | 仅 local `submit` ∧ `--expose-local`                                          |
| `.runstate.lock`                                             | `run_state` 写面互斥                                                    | 本地文件载体独有                                                              |
| `jobs-in/`                                                   | job 输入（**不是判定**，勿与 `jobs/` 混读）                                | cloud 独有：起 task 时写                                                       |
| `args/`                                                      | definition 的外置正文                                                   | cloud 独有：docString / dataTable 一律 offload、无 size 阈值                    |

日志、机制文件与 `jobs-in/` 不属 §1 的五类：它们不是判定材料，只在特定档下出现（`args/` 例外，它存放的正是 definition 被外置的那部分正文）。

几处需要注意的不对称：

- **Nova 的 per-act 文件与 session 汇总同在 `nova-trajectories/<session_id>/`**（这一层由 SDK 以会话 id 创建，`session_id` 记在 `jobs/*.json` 的 job 层，排障时可直接 `ls` 该目录）：每次 act 一组 `act_<序号>_<指令片段>.html` + 配套 `_trajectory.json`（act 抛错时配套 json 通常未写出、只剩 `.html`），另有 SDK 自身的 trace/log 文件；`session_summary.json`（`kind=summary`）只在该 scope 实际调用过 AI 时才写。Midscene 侧 `report/` 除 `*.html` 与 `screenshots/` 外，还有每个 execution 一份的 `<n>.execution.json`（截图落成独立文件的连带产物，同样只在实际调用过 AI 时才有），随整目录 flush 一并上传。**确切文件名不可推测**：名字里嵌指令片段、且随 SDK 版本漂移，应以判定真值里的那条 `ref` 为准。
- **`jobs/` 与 `jobs-in/` 只差三个字母，语义相反**：`jobs/` 是判定输出（由 ResultStore 枚举），`jobs-in/` 是 cloud 起 task 时写入的 job 输入。两个前缀有意分开，以免 key 冲突、以免 job 输入被当作判定读取。
- **cloud 的 `run_meta` / `run_state` 不在桶里**，`--json` 的 `artifacts` 给的是 `ddb://<表>/<run_id>#META` 形式的**诊断指针**（纯展示、不被任何代码解析）。
- **cloud 档本机通常没有这棵本地树**：产物写在容器内 `/tmp/gherkai-run/<run_id>/` 下的同名子目录里，上传成功即删本地、随容器盘销毁。run 收尾时组合根仍对本机 `<report-dir>/<run_id>/` 做一次「只删空目录」的清理（目录不存在则 no-op；上传失败而保留了产物的目录非空，因此不会被删除）。
- **`--no-report` 不落 definition / 运行态 / 判定明细 / 报告，也不产引擎产物与 evidence**（经 `GHERKAI_NO_ARTIFACTS=1` 告知 worker），local 与 cloud 同律；此档 `<report-dir>/<run_id>/` 下不落任何文件，仍会落盘的部分只在系统临时目录、worker 既不收集也不上报：Nova Act SDK 的 trajectory 无法关闭（不传 `logs_directory`，SDK 写进自身 `mkdtemp` 的目录）、Midscene SDK 的 log/dump（无 `MIDSCENE_RUN_DIR` 时 worker 把落点指向一次性临时目录，避免写入用户 CWD），以及 local 档 `--quiet` 的 worker 日志（`<tmpdir>/gherkai-worker-<run_id>.log`）。
- 引擎产物的落点由组合根经 env **注入**给 worker（`NOVA_LOGS_DIR` / `MIDSCENE_RUN_DIR`），S3 上传落点是另一对注入（`ARTIFACT_S3_BUCKET` / `ARTIFACT_S3_PREFIX`）。worker 不知道自己运行在哪一档，只依据注入是否存在：注入了就上传 S3 并报 `s3://`，未注入则报 `file://`。

> 权威：[ADR 0029](../adr/0029-engine-artifacts-to-s3.md)（worker 上传、S3 key 镜像 run 树、删本地与空壳清理）、[ADR 0027](../adr/0027-runreport-aggregation-index.md)（两引擎落点归位到 run 目录、`href` 相对化）、[ADR 0030](../adr/0030-realtime-persistence-seam.md) 决定六（DDB 两 item、`jobs/` key 布局、argument offload）、[ADR 0037](../adr/0037-distribution-and-packaging.md) 决策 3（`--no-report` = 真不生成）、[ADR 0042](../adr/0042-step-evidence-and-explain.md) 决策一（evidence 落引擎产物目录内、`<scenario 键>` 派生）。云端资源本身（表 / 桶 / 日志组 / 命名与权限）见 [`./cloud-backend-carriers.md`](./cloud-backend-carriers.md)。

## 3. 证据链的串接

![证据链：worker 在 step 判定成立时把证据指针写进判定真值，并把现场抽取为自有格式的证据明细；explain 只解引用自有格式的那一份，引擎原生产物只以链接引用；截图地址确定性算出，字节随后上传](../diagrams/artifacts-evidence-chain.svg)

图注：只有**调用过 AI 的 step** 走这条链：确定性命中与 URL 导航步的判定直接发事件、不产 evidence（`explain` 因此输出「无 AI 证据」，见 §4）。local 档没有异步上传这一环：截图字节在 `evidence.json` 落盘时已经在盘上，异步上传只发生在 cloud 档。图上四个落点的确切文件名与相对路径见 §2 表（`jobs/<enc>.json`、`evidence/<scenario 键>/step-<n>/evidence.json`、帧截图、两个引擎的原生产物子目录）；`explain` 与 `run` / `status` 各自回答什么问题见 §4。

这条链由以下四点确定：

1. **产出方**：worker，在 step 结束时产出。此时它才持有引擎的材料（Nova 是刚写盘的 trajectory json，Midscene 是内存里的 `agent.dump.executions`），而非由 CLI 事后解析 SDK 产物。落盘分两处：`evidence.json` 由 worker 直接写进引擎产物目录；指向它的 `kind=evidence` 那条 `ref` 随 `step_done` 事件进入判定链，落在 `jobs/*.json` 的 `step.report_refs`。
2. **只解引用 `kind=="evidence"`**：`explain` 取得 step 的 `report_refs` 后只读 `kind=="evidence"` 那条（`_explain_read_evidence`），其余 `report` / `trajectory` / `summary` **作为链接原样输出**。判据是「内容是否为本项目定义的 schema」：引擎原生格式随 SDK 版本漂移，解析它等于把引擎知识引入 CLI。读字节的唯一入口是 `compose.read_resource`（`file://` 复用 report_store 的 URI→路径解析，`s3://` 走 `get_object`）。
3. **截图只给地址、不内嵌图**：`frames[].screenshot` 是 `file://` 或 `s3://` URI，按上传器的同一套 key 规则**确定性计算得出**，因此可以先写进 `evidence.json`；字节则在这一步的 `step_done` 发出**之后**才交后台队列上传（cloud 档；local 档不经上传，截图字节在写 `evidence.json` 时已在盘上）。判定因此不受网络阻塞，字节通常在下一个 step 结束前到达。
4. **文本形态是摘要，不是全文**：`explain` 默认每个 act 只渲染最后一个带 `thought` 的 frame（超长推理截断并指回 `--json` 或那份 `evidence.json`），其余 frame 只给出数量；`--full` 取消预算，`--all` 一并展开 passed step。文本里的 key 与 `--json` 字段名逐字相同，从文本对照 JSON 无需转换。

> 权威：[ADR 0042](../adr/0042-step-evidence-and-explain.md)（决策一 evidence schema 与两引擎映射表、决策二 best-effort、决策四 `explain`、决策五「解引用许可按层收窄」）、[ADR 0027](../adr/0027-runreport-aggregation-index.md)（`ReportRef` 三元组、core 对它永久不透明搬运）。字段与取值全集见 [`./cli-json-contract.md`](./cli-json-contract.md)。

## 4. 一次失败的三步读法

```
① gherkai status <run_id> --wait        → 等到终态；终态时输出报告 / 运行元信息 / 判定明细的位置
② gherkai explain <run_id> [<scope_id>] → 哪一步、提问内容、模型看到什么、判定依据（默认只展开非 passed）
③ 打开 ①/② 给出的 index.html 或原生产物链接 → 引擎自身的报告页 / 轨迹页 / 截图，查看现场
```

这三步里的 `explain` 不是判定门：它**从不表判定**（退出码只用 0 / 2，即使一条证据都没有也退 0），判定码只由 `run` 与 `status` 给出（`status` 仅在读到终态时表判定、未达终态退 0，因此 CI 取判定须用 `status --wait`）。各命令退出码分别回答什么问题见 [`./verdict-model.md`](./verdict-model.md)「退出码」节。detached run 未到终态时判定明细尚未落盘，`explain` 输出一行「先用 `status --wait`」并退 0。

**提示与含义对照**（文本形态；机读侧对应 `record_missing` / `evidence_missing` / `aborted_hint`）：

| 提示文本                                                 | 含义                                                                                                                                       | 处理                                                                                                                                                    |
|----------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| `无 AI 证据`                                             | 这一步有判定记录，但没有 `kind=evidence` 的指针。三种情形在此**无法区分**：确定性 / 导航 step 本就不产、AI 已执行但抽取失败、这一步完全没有记录 | 区分「未执行」与「已执行但未产证据」看 `record_missing`；确定性 step 为何不产证据见 [`./deterministic-step-lifecycle.md`](./deterministic-step-lifecycle.md) |
| `无记录（未执行或未上报）`                                 | 骨架（job 定义）里有这一步，判定明细里没有它：worker 被外部中止时，未执行完的 scenario 不进判定明细                                             | 查看同一 scope 的 job 级判定块与 worker 日志；这一行不表示该 step 失败                                                                                   |
| `本 job 被中止，部分已执行 step 的证据未进判定记录`       | 该 job 终态是 aborted 或 error，且只有**部分** step 有记录。已执行 step 的 evidence **已产出并上传**，但其指针只留在事件记录里、未进判定明细   | 沿 `index.html` / job 级 `report_refs` 查找引擎原生产物；证据文件本身也可按 §2 的 `evidence/<scenario 键>/step-<n>/` 路径直接定位                        |
| `AI 证据的格式版本这个版本的 gherkai 认不出（升级后再看）` | `evidence.json` 的 `schema_version` 不是当前 CLI 认识的那个版本                                                                            | 升级 CLI；产物本身未损坏                                                                                                                                 |
| `AI 证据读不到（文件不在或内容已损坏）`                    | 指针存在，但按指针取不到字节（对象不存在 / 无权限 / 不是 JSON）                                                                               | cloud 档先核对 `--prefix` / `--report-dir` 与凭证；worker 被强制终止的 run 见 §5「cloud 档某张截图的 URI 偶尔取不到对象」条                                |
| 一段 `判定：<status>` + `诊断细节见 worker 日志`          | 该 job **没有任何 step 记录**（worker 未启动，或启动后即被终止）                                                                              | 查看 worker 日志（local `--quiet` 档 = `worker.log`，cloud = CloudWatch 日志组）                                                                           |

> 权威：[ADR 0042](../adr/0042-step-evidence-and-explain.md) 决策四（记录缺口的两种情形、退出码只用 0/2、文本预算）、[ADR 0031](../adr/0031-job-lifecycle-states-and-severity.md)（各 job / step 状态的含义与短路旁注）。判定语义本身（各态怎么聚合、`shortcircuited` 判据）见 [`./verdict-model.md`](./verdict-model.md)；`--wait` 谁在推进、超时怎么算见 [`./execution-and-reconciliation.md`](./execution-and-reconciliation.md)。

## 5. 边界（有意取舍，非遗漏）

| 现象                                                                                 | 为什么                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | 指针                                                                                                                                                                                                                                                                                                     |
|--------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **纯确定性 run 的产物清单是空的**，`index.html` 显示「本次 run 无报告产物」             | 引擎原生产物只在实际调用过 AI 时才产生（Nova 的 trajectory 要有 act、Midscene 的 report 要调用过 agent），确定性 step 走页面 API、从不调用引擎；evidence 同理。**判定不受影响**：每个确定性 step 的 pass/fail/error 与时长都在判定真值里                                                                                                                                                                                                                                                                                                                        | [ADR 0027](../adr/0027-runreport-aggregation-index.md)「纯确定性用例 → 空 report_index」（含「确定性 step 产物可观测性」这个仍未关闭的缺口）                                                                                                                                                                   |
| **cloud 档没有 `worker.log`**                                                        | worker 在容器内运行，日志由 task 的 log driver 进 CloudWatch 日志组 `/<prefix>worker/<engine>`（stream 前缀 = 引擎名）。`--json` 的 `artifacts` 因此**不含** `worker_log` 键，该键只在 `--quiet` 且本机执行时出现                                                                                                                                                                                                                                                                                                                                            | [ADR 0041](../adr/0041-agent-facing-cli-affordances.md) 决策二（`--quiet` 的落点）；日志组名不经 `names.py`、由 stack 建 task-def 时确定（真值 = `deploy_aws/gherkai_deploy_aws/stack.py` 里 worker container 的 `LogDriver.aws_logs`：`log_group_name` = `/<prefix>worker/<engine>`、`stream_prefix` = 引擎名） |
| **`--no-report` 下 `<report-dir>` 不落任何文件**                                     | 它的含义是「不生成产物」，不是「落到别处」：不注入落点 + `GHERKAI_NO_ARTIFACTS=1` 令 worker 不生成、不上报；cloud 档同样注入此 env，因此也没有 S3 上传                                                                                                                                                                                                                                                                                                                                                                                                           | [ADR 0037](../adr/0037-distribution-and-packaging.md) 决策 3（含被拒方案「落系统临时目录」及其理由）                                                                                                                                                                                                         |
| **被中止的 job，`explain` 只输出一行提示，不给出已产出的 evidence**                    | 未执行完的 scenario 不发 `scenario_done`，其 step 记录不进判定明细，evidence 指针**只留在事件记录里**；而 `explain` 按设计只读判定明细、不读事件流                                                                                                                                                                                                                                                                                                                                                                                                          | [ADR 0042](../adr/0042-step-evidence-and-explain.md)「已知缺口与重议闸门」（含触发信号与预案：给 core 开事件流读接缝）                                                                                                                                                                                        |
| **cloud 档某张截图的 URI 偶尔取不到对象**                                            | 进程被**强制终止**（SIGKILL / 容器被回收）时，最后一个 step 在途的一两张截图字节可能未完成上传（URI 早已写进 `evidence.json`，见 §3）。正常路径与收尾的有界排空已由实际运行覆盖「中途被终止也不丢」                                                                                                                                                                                                                                                                                                                                                              | [ADR 0042](../adr/0042-step-evidence-and-explain.md)「截图字节的残余风险」、[ADR 0032](../adr/0032-fargate-execution-environment.md)（容器盘停即销毁、grace 组成、孤儿产物 reaper 为何否决）                                                                                                                    |
| **报告写失败不会使 run 判定为失败**                                                  | RunReport 是纯派生视图、可重建，故它的写入在 commit point **之后**、异常被隔离；此时 `run --json` 的 `artifacts` **省略** `report_index` 键，人读档收尾行输出「报告: <报告写入失败，已跳过；判定结果不受影响、仍已落库>」。`status` 不同：它给出的是**约定落点**（无论写成功与否都照常输出、`--json` 的 `artifacts` 也恒含 `report_index`），不反映写入失败。cloud 档还多一层：`status --backend cloud` 输出的 `s3://` 前缀直接取本次传入的 `--report-dir`、查询侧不与后端记录比对（那道比对只在 `submit` / `doctor` 的提交侧做），因此传错时输出的是一组指向不存在对象的位置 | [ADR 0030](../adr/0030-realtime-persistence-seam.md) 决定三                                                                                                                                                                                                                                              |
| **`jobs/*.json` 里的 `ref` 是绝对路径，报告目录整体复制到另一台机器后这些链接会失效** | 自包含只做到「半可移植」：`index.html` / `manifest.json` 的 `href` 相对化（可整目录迁移），判定真值里的 `ref` 保持绝对（provenance）。跨机器分享用 `index.html`，或直接用 cloud 档（产物全在 S3、`s3://` 全局可寻址）                                                                                                                                                                                                                                                                                                                                                | [ADR 0027](../adr/0027-runreport-aggregation-index.md)「被拒方案：不做 materialize 式产物拷贝」                                                                                                                                                                                                             |

> 权威：上表每行的 ADR 指针即该条的权威；跨条的共同前提是「判定真值 > 报告产物」这条优先级（[ADR 0029](../adr/0029-engine-artifacts-to-s3.md)）与「派生视图可重建、永不作判定源」（[ADR 0027](../adr/0027-runreport-aggregation-index.md)）。

## 6. 延伸阅读

| 延伸主题                                                                 | 文档                                                                     |
|--------------------------------------------------------------------------|--------------------------------------------------------------------------|
| 每个字段的类型与出现条件（`run` / `status` / `explain` / `evidence` 全集） | [`./cli-json-contract.md`](./cli-json-contract.md)                       |
| 谁在推进、事件走哪条物理通道、超时由谁强制、诊断落在哪                      | [`./execution-and-reconciliation.md`](./execution-and-reconciliation.md) |
| 各判定态的语义与聚合规则、短路与严重度                                    | [`./verdict-model.md`](./verdict-model.md)                               |
| 确定性 step 为什么不产产物、它的注册与发现                                | [`./deterministic-step-lifecycle.md`](./deterministic-step-lifecycle.md) |
| 云端载体本身：两张表、桶、日志组、命名与权限面                               | [`./cloud-backend-carriers.md`](./cloud-backend-carriers.md)             |
| RunReport 的语义与扩展性契约（新引擎零改 core）                            | [ADR 0027](../adr/0027-runreport-aggregation-index.md)                   |
| evidence schema、两引擎映射表、SDK 漂移防线                                | [ADR 0042](../adr/0042-step-evidence-and-explain.md)                     |
