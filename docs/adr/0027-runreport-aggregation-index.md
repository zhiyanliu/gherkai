# RunReport：跨引擎归集索引（不融合原生产物内容）

> **Status:** Accepted

兑现 [0016](./0016-execution-architecture-core-lib-run-model.md) 一直 deferred 的「报告统一」（原里程碑 M5）。本 ADR 定 **RunReport 的语义、形态与扩展性契约**，并落地 `ReportStore` 的 local adapter。

## 决定：RunReport = 归集索引，不是内容融合

两个引擎的**原生**报告形态根本不同且不可统一（[0010](./0010-spike-as-apples-to-apples-benchmark.md) / CONTEXT「报告产物模型」）：Midscene 出单个 `report.html`（整 scope 一份），Nova 每次 act 出一个 trajectory（挂到其所属 step）+ 一份 session 汇总；未来引擎可能是录屏、外部 URL、JSON trace。

**RunReport 不试图解析/重渲染这些产物**——那等于给每个引擎写一个 HTML 解析器，既脆又把 core 锁死到具体引擎。RunReport 是一份**跨引擎、跨产物的统一目录 + 导航入口**：

- **`manifest.json`** —— 机器可读（CI / WebUI 消费）：**薄信封**（schema_version/run_id/created_at）+ 一份扁平的报告产物清单（report_index，每条指向哪个 scope·scenario、哪个引擎、什么 kind、产物在哪）。**不内嵌判定/时长/成本**——那是 `RunResult` 真值、靠 `run_id` 软引用到 `ResultStore` 取（详见下「manifest.json 形态」）。
- **`index.html`** —— 人可导航：一个最小的单文件入口，判定明细树（判定/时长/成本从内存 `RunResult` 渲染）+ 每个产物一行链接，点开看**原样的**原生产物。

原生产物保持原样（各引擎自己最懂怎么呈现），RunReport 只**索引/链接**它们。

> **允许 vs 禁止的边界（写死）**：core/ReportStore 对产物只允许「按字节拷贝/移动 + 算一个链接」；**禁止**解析、重写、抽截图、合并内容。「产物在哪、属于谁」是归集索引的本分；「产物里画了什么」是引擎的事。

## 扩展性契约：新引擎零改 core

头等约束。保证机制：

- **`ReportRef = {kind: str, ref: ResourceUri, label: str | None}`**（取代旧 `{granularity: Literal["scope","act"], path}`）：
  - `kind` —— **产物类型**（开放字符串，引擎自报）：`report`（完整报告页）/ `trajectory`（轨迹页）/ `summary`（数字汇总）/ 未来 `video`/`trace`/`har`…。core/gherkai_core/wire/schedule **永不读它的值、永不按它分支**，是文档化约定常量、非枚举。**「粒度」不由 kind 表达，而由 report_ref 挂在哪一级表达**——`StepResult.report_refs`=step 级、`ScenarioResult.report_refs`=scenario 级、`JobResult.report_refs`=scope 级。（旧值 `scope`/`act` 把粒度混进了 kind——`scope` 是粒度、`act` 是引擎内部动作类型；归正为纯类型维度，粒度交给挂载层级，二者正交、不重复不撞名。）
  - `ref` —— **统一指针 `ResourceUri`**，不假定是本地文件。本地产物用 `file://` 前缀；未来可是 `s3://`/`https://`。core/ReportStore **不 stat、不 fetch、不打开** ref，只索引/链接。
  - `label` —— 可选人类可读锚文本；缺省由消费端回落 `kind`。worker 可全部不报。
- **铁律**：`core/gherkai_core/model.py`、`core/gherkai_core/wire.py`、`core/gherkai_core/schedule.py` 对 `ReportRef` 永久是**不透明搬运**。任何「按 kind 选 `<video>`/`<iframe>`」之类的渲染分支**只允许出现在 cli / WebUI 皮层**，绝不写回 core。
- 新引擎接入 = 它的 worker 报自己的 `ReportRef`，经 [0024](./0024-worker-core-protocol.md) 协议原样进 `report_refs`，归到 RunReport，**core 一行不改**。

> 旧 `granularity: Literal` 是「核心谎称收窄、wire 实则放行」的假约束——`wire.py` 反序列化时从不校验枚举、Midscene worker 的 TS 类型本就是 `string`。放开成 `str` 是**消除既存不一致**，非新增灵活性。

## run_id：归集索引的主键（落地逼出）

归集必须有个 run 标识（manifest 目录名 / 未来 DDB 主键）。[0016](./0016-execution-architecture-core-lib-run-model.md) 早把 `run_id` 列为「持久化层 Run 级字段、deferred」——RunReport 落地把它逼了出来：

- **生成权在组合根**（cli 的 `compose` / 未来 WebUI bootstrap），不在 `schedule` 内部生成。理由：WebUI 语义是「提交即返回 runId、之后轮询」——runId 必须**先于**跑批存在；schedule 内部生成会与该模型打架。也避免 schedule 内部 `uuid`/时钟破坏其「fake-clock 可确定性单测」的定位。
- **run_id 落进 `RunMeta`（definition），`RunResult` 经 property 取**：组合根生成 run_id 后包成 `RunMeta(run_id, created_at, jobs)` 喂 `schedule(run_meta, ...)`；`RunResult` 持 `run_meta`、`run_id` 经 property delegate（自描述：落库后用自身字段对上主键）。run_id 归位 definition 层属「三层切分」（见 [0016](./0016-execution-architecture-core-lib-run-model.md)）。
- run_id 对调用方**不透明**，只保证「可排序 + 抗碰撞」（实现用时间戳前缀 + 随机尾，格式留 `compose` 实现、不入本 ADR 契约）。
- **生命周期**：run_id 在组合根生成（先于 `schedule`）。`plan` 阶段失败（feature 读不到 / `PlanError`）发生在 schedule 之前 → 不生成 run_id、不产 RunReport。

## JobResult 自带 `engine`（经持有的 `Job`）

RunReport 要按引擎标注每条产物。`JobResult` 须能就地拿到 `engine`（否则要跨 `Job[]` 按 scope_id join 才拿得到，脆弱且让 adapter 同时认识输入侧 `Job` 与输出侧 `RunResult` 两套模型）。

**`JobResult` 持有它的 `Job`(definition)，`engine`/`scope_id`/`scope_name` 经 property delegate 给 `self.job`**（不重复抄存——抄字段易漏，持 `Job` + property 则存储唯一、读法稳定）。`RunResult` 自此自包含，`to_dict`/manifest 直接读 `jr.engine`，无需跨模型 join（属「三层切分」，见 [0016](./0016-execution-architecture-core-lib-run-model.md)）。

## ReportStore 接口：整 run 一次写

旧 `save_report_ref(run_id, scope_id, path, granularity)`（逐条、且连 scenario_id 都没有，承载不了 scenario 级 ref）退役。改为**整 run 一次**：

```python
class ReportStore(Protocol):
    def write(self, run_id: str, result: RunResult, *, created_at: str = "") -> ResourceUri:
        """从 RunResult 归集出 <report_root>/<run_id>/{manifest.json, index.html}，返回 index.html 的 ResourceUri。

        读 result 的 report_refs + 各级 status/时长/成本 + step 级 votes/error_type/shortcircuited，
        渲染成「判定明细树 + 产物导航」的**人看视图**（明细树见下「index.html 形态」）；
        **但不拿 status 当 CI 判定源**（判定真值在 RunResult/ResultStore，index.html 只是派生人看视图）。
        """
```

（无 `materialize` 参数——产物拷贝式的 materialize 已否决，见下「被拒方案」。）

- **返回 `ResourceUri` 而非 `Path`**（封版前收口）：`LocalReportStore` 回 `file://…/index.html`，`S3ReportStore` 回 `s3://…/index.html`（v1.1 已建，ADR 0030 决定六）——**同一签名容两种落点**，否则 S3 adapter 被迫返回 `Path` 包 `s3://`（`Path` 会把 `s3://b/x` 折成 `s3:/b/x`，错）。`ResourceUri = NewType("ResourceUri", str)`（定义在 `core/gherkai_core/model.py`）：把这个**本就存在于 `ReportRef.ref` 注释里**的约定提升成命名类型，统一「`ReportRef.ref` 与 `write` 返回值都是带 scheme 的资源指针」。比裸 `str` 多一层意图、又零运行时成本/零依赖（运行时即 `str`）。消费端（cli/WebUI）只当 URI 用、不 stat/open。
  - 实现注意：`LocalReportStore` 内 `index_path.resolve().as_uri()`——`as_uri()` 要求绝对路径，而 cli 默认 `--report-dir` 是相对的（`reports`），不 `resolve()` 会抛 `ValueError`。
- **`index.html` 链接（`href`）指向产物原位**：不拷贝、不搬运产物。`href` 是 core 自己生成的**导航链接**（`index.html` 的 `<a href>`），local 相对化、cloud 恒等于 `ref`（见下「href 相对化」）。

> **`ref` 由 worker 定，`href` 由 core 算——铁律圈的是 `ref`，不是 `href`（关键边界，别混）**：
> - `ReportRef.ref` 指向**哪**是 **worker** 决定的——`--backend local`(subprocess) worker 产物落本地、报 `file://`；`--backend cloud`(Fargate) worker（或 subprocess+注入落点的内部预演路径，[0016](./0016-execution-architecture-core-lib-run-model.md) 决策 B）**自己上传 S3**、报 `s3://`（[0029](./0029-engine-artifacts-to-s3.md)，落点由组合根注入的 S3 配置驱动、注入即上传）。**ReportStore 不上传 worker 产物、不碰其持久化**（per-worker by-design，[0016](./0016-execution-architecture-core-lib-run-model.md)「worker⊥store」），只**不透明搬运**这个 `ref`（不 stat/fetch/open/**改写**——包括绝不把 `ref` 从绝对改成相对）。
> - `href` 是**正交的另一件事、且不受铁律约束**：它是 core 为 `index.html` 导航自算的链接，本就允许 core 生成/改写（「算一个链接」是 ReportStore 的本分）。local 把 `href` 相对化（指向产物在 run 树内原位，如 `nova-trajectories/<s>/act_0.html`）→ 报告目录整拷到别的机器链接不断；cloud 下 `s3://` 全局可寻址、无相对必要，`href==ref`。
> - `LocalReportStore` → `S3ReportStore`（v1.1 已建）只换「manifest+index 这些 **core 派生数据**落哪 / 返回的 URI scheme / `href` 相对化策略」，core 不动、且复用同一份 `_render_index_html` 与 `collect_report_index`（单一渲染真理源）。（注意区分：`S3ReportStore` 是把 **RunReport 自身**（manifest/index.html）写到 S3，与「worker 把自己的产物上传 S3」是两回事。）

- **`write` 失败被隔离、不击穿已 commit 的 run**（实时写接缝，[0030](./0030-realtime-persistence-seam.md)）：RunReport 是**纯派生只读视图、可重建、永不作判定源**——故 `RunPersistence.finalize` 在 commit point（`finalize_run`，判定真值已落 ResultStore）之后才调 `ReportStore.write`，且把 write 的异常隔离（吞掉+留痕+返回 None），不让一个「可重建的报告」写失败把整个 run 拖成裸 traceback 退出、CI 拿不到判定输出。

> **被拒方案：不做「materialize」式的产物拷贝**（别重新进坑）。曾有过一个 opt-in「把产物按字节拷进 `<run_id>/artifacts/` 求自包含」的开关，已否决——报告自包含由 `href` 相对化零成本达成（产物本就在 run 树内），而拷贝是「拷一份已在树里的东西」的纯磁盘放大；云端用 `s3://` 绝对链接（全局可寻址、拷/分享不断），拷贝亦零收益。**取舍**：报告「半可移植」——`index.html`/`manifest.json` 相对 `href` 可整目录搬走，`jobs/*.json` 的 `ref` 保持绝对（判定真值/provenance）拷机器后其产物链接仍断；跨机器分享用 `index.html` 或 `--backend cloud`（全在 S3）即可，不为此付全量拷贝代价。

**「生成 RunReport」cli 默认开**：每次 run 都归集到 `<report-dir>/<run_id>/`（`--report-dir` 配落点，默认 `reports/`）；`--no-report` 是逃生舱（CI 只看退出码/JSON、或调试不想落盘）。理由：manifest+index 仅几 KB，却给出「这次 run 结果在哪、各引擎报告在哪」的统一入口——一个跑完不知结果在哪的工具是不完整的，不该要用户记得加 flag。

**两个引擎产物都归位到 run 目录内——落点对称**：cli 经环境变量把两个 SDK 的产物
落点都设到 `reports/<run_id>/` 下（[0016](./0016-execution-architecture-core-lib-run-model.md) 组合根注入）：
- **Nova**：`NOVA_LOGS_DIR` → SDK `logs_directory`，trajectory 落 `reports/<run_id>/nova-trajectories/`。
- **Midscene**：`MIDSCENE_RUN_DIR` → SDK run 根目录，`report.html` 落 `reports/<run_id>/midscene-run/report/`。
  （SDK 用 `path.resolve(cwd, MIDSCENE_RUN_DIR)`，cli 传**绝对路径**避 worker cwd 歧义。）
- 故 RunReport 的产物**都在 `reports/<run_id>/` 树内**。**正因产物就在树内**，`index.html` 的 `href` 相对化（相对 run 目录）即让整个 `reports/<run_id>/` 目录可原样搬走、链接不断——这正是移除 materialize 的底气（无需拷贝即自包含）。
- **归位的另一收益**：产物不再落相对 worker cwd 的固定 `midscene_run/`（每 run 覆盖、与 run 无关），
  而是 run 专属目录——为 v1.1 云端归集/上传（[0016](./0016-execution-architecture-core-lib-run-model.md) worker⊥store）铺路，两引擎落点对称、处理一致。

### href 相对化（local 相对 / cloud 恒等 ref）

`collect_report_index` 经 `make_href(rr)` 回调算每条 `href`（`ref` 永远原样保留、不改写）：
- **local**：`ref` 是本地文件（`file://` 或裸本地路径）且解析出的路径落在 run 目录树内 → `href` = 相对 run 目录的路径（`resolve()` 后再 `relative_to`，防 macOS `/tmp`↔`/private/tmp` symlink 造假 `ValueError`）；否则（远端 scheme `s3`/`http` / 落在树外，如 worker 没吃到落点环境变量而落 SDK 临时目录）→ `href` 回落 = `ref`（绝对，该条不可移植，有测试覆盖 + 文档注明「非所有 local href 都相对」）。
- **cloud（S3）**：`href` 恒 = `ref`（`s3://` 全局可寻址、无相对必要）。
- **只按 scheme 分支（`file://` 相对、其余 identity），绝不按 `kind` 分支**——后者才是铁律点名禁止的。为算相对 href 而 `urlparse` 解析 `ref` 字符串**不越铁律**：铁律「禁止解析」的宾语是产物**内容**（HTML/trajectory 字节），非 `ref` 指针串；「算一个链接」本就要读 `ref`。

**职责边界（三 port 正交，[0016](./0016-execution-architecture-core-lib-run-model.md)）**：`RunStore`=控制面（definition `RunMeta` + 运行态 `RunState`：status/血缘）、`ResultStore`=数据面（判定真值唯一权威）、`ReportStore`=**纯派生只读导航视图**（可从 `RunResult` 完全重建、永不作 CI 判定源）。`ResultStore` 旧 docstring「RunReport 归集靠它」一句删除——归集职责移交 `ReportStore`。

## manifest.json 形态

**纯派生导航视图：薄信封 + 扁平 report_index，不内嵌 result 真值副本**。判定真值由 `ResultStore` 持有（数据面，每 job 落 `jobs/<scope_id>.json` / 未来对象存储），运行态/身份由 `RunStore` 持有（`run_meta.json` + `run_state.json` / 未来 DDB，[0016](./0016-execution-architecture-core-lib-run-model.md)）；manifest 靠 **`run_id` 软引用**那次 run——CI 要判定就拿 run_id 找 `ResultStore`。这样 report 是真·派生品（可删可重建、永不作判定源），无真值冗余、无一致性风险。

```jsonc
{
  "schema_version": 1,
  "run_id": "...",               // 软引用那次 run；完整判定真值在 ResultStore（jobs/*.json），按此 id 取
  "created_at": "...",           // 组合根生成的时间戳（字符串，由调用方传入）
  "report_index": [              // 扁平投影，便于 CI/WebUI 直接遍历
    { "scope_id": "...", "scenario_id": "..."|null, "step_index": N|null, "engine": "...", "kind": "...",
      "href": "...", "label": "..." }   // 只有 href（导航链接）——原始 ref 不进 manifest，见下
  ]
}
```

- `report_index` 从内存 `RunResult` 树一次投影（含全部 report_refs 三级，**不走逐条 append**）；**粒度由 `scenario_id`/`step_index` 是否为 null 表达**：`scenario_id=null` = scope 级；`scenario_id` 非空且 `step_index=null` = scenario 级；两者都非空 = step 级（同 scenario 多 trajectory 靠 step_index 区分）。
- **每条只含 `href`（导航链接），不含 `ref`**（曾有 `ref` 字段，随 materialize 一并移除）。理由：① manifest 是**纯派生导航视图**，`href` 承担全部导航语义、无人读 `ref`（index.html 渲染只用 `href`；全仓无生产代码回读 manifest.json）；② 若保留 `ref`，`href` 相对化后 `ref` 因铁律必须留绝对（不能相对化它）→ 变成一条**无人读却泄漏机器路径的绝对 `file://`**。删 `ref` 既消冗余又消泄漏。**原始不透明指针 `ref` 的权威落盘处收敛到 `jobs/*.json`（ResultStore 判定真值）+ 内存 `RunResult`**——未来 WebUI/CI 要原始指针应去 ResultStore 取（判定真值），不向派生 report 视图要，这反而强化了三层分层。（这是 manifest schema 契约变更，本仓无 in-repo 消费者故低风险，仍记为契约变更防漂移。）
- index.html 的 run 摘要 + 整棵判定明细树（job→scenario→step，各级上色 + step 级 votes/error_type/shortcircuited 旁注）**直接用内存 `RunResult`** 渲染，不从 manifest 读（manifest 已不含 result）。
- **manifest 不内嵌 `to_dict(result)`**（曾考虑、否决）：那会让派生视图承载判定真值副本（与 `ResultStore`/`RunStore` 冗余）；改为软引用 run_id 消除冗余。`serialize` 仍是单一序列化真理源（cli `--json` 与各 store 共用），只是不塞进 manifest。
- `to_dict` 含 `job.engine`、`scenario.report_refs`（序列化补齐项）。
- manifest **不冗余 status 当判定源**——`result` 里已有，CI 读 `result.status`，不读信封。

## index.html 形态

纯 Python 字符串拼装 + `html.escape()`，**无模板引擎、无外链 JS/CSS、单文件**（对齐 `wire.py`「手写映射、显式稳定」与 core「薄编排层无重型依赖」）。**两大块**（皆从内存 `RunResult` 渲染）：

- 顶部一行 run 摘要（run_id + 总 status + duration + 原生量成本）。
- **① 判定明细树**：job→scenario→step，逐级上色（含派生态 skipped/aborted、前置态 pending/running 各自配色，非兜底灰，见 [0031](./0031-job-lifecycle-states-and-severity.md)）+ step 级 status/votes tally/error_type/时长。**被 scope 内短路的 step 显 `skipped` 态 + 读 `shortcircuited` 布尔加「⚠ 因前置 step error 被跳过」旁注**（连锁失败旁注，判据是 shortcircuited 而非「按 status 顺序猜」，见 [0031](./0031-job-lifecycle-states-and-severity.md) 决定六）。让纯确定性 run（无原生产物）也一眼看懂结果。**但不拿它当 CI 判定源**（判定真值在 ResultStore）。
- **② 原生报告产物导航清单**：每条 report_ref 一行——job.status 上色 + scope_id（+ scenario_id/step[N] 表粒度）+ engine + `[kind]` + 指向 `href` 的 `<a>`（`label` 或回落 `kind` 作锚文本）。`href` 由 `make_href` 算（local 相对 / cloud 恒等 ref，见上「href 相对化」）。
- 上色用内联 `<style>`。
- **空态**：无任何 report_ref 时②仍生成有效的「空报告」清单（标注本次无原生产物）、①判定明细树照常渲染，不报错。

## Nova reportRef 的回传与归属（trajectory 下沉 step 级 + session 汇总）

Nova worker 设 `NovaAct(logs_directory=<run 专属持久目录>)`，act/act_get 的 trajectory 落到那里。两类产物、两级归属：

- **trajectory 下沉到 step 级**（`kind=trajectory`，经 [0024](./0024-worker-core-protocol.md) `StepDone.report_refs` 回传）：worker 在**每个 step 内**收集本 step 触发的 act 产物（一个 step 可能多次 act → 多个 trajectory），随该 step 的 `step_done` 报出，归到 `StepResult.report_refs`。**为何下沉到 step 而非 scenario**：`act` 是引擎内部动作粒度、比 step 还细,但 step 是 domain 有效概念——把 act 轨迹挂到它所属的 step 下,信息最全（agent 能精确追溯「step N 这次判定 → 这几个 act 轨迹」）,而聚合到 scenario 级会丢失 act↔step 归属。（下沉后 Nova 不再填 `scenario_done.report_refs`——该字段保留、协议向后兼容。）
- **session 汇总作 scope 级**（`kind=summary`，经 `ScopeDone.report_refs` 回传）：Nova SDK 落的 `session_summary.json`（session_id/time_worked_s/**act_count** 等）作 scope 级 report_ref。它**不是人看报告、是数字汇总**——作为「引擎特有富信息」的载体经不透明指针带给 agent（见下「引擎特有量不进 model」）。

**Midscene 保持 scope 级**（`kind=report`，`scope_done.report_refs`，1 个 report html/worker）。两引擎产物形态/粒度不同（[0010](./0010-spike-as-apples-to-apples-benchmark.md)），core 不分支、不透明搬运——这正是「引擎自报粒度、core 不规定每级都得有」。

### 引擎特有量不进 model：判据是「domain 是否有效」，不是「引擎套不套得上」

`act_count`（scope 内 AI 动作次数）等 **不进 model 通用字段**——判据不是「Midscene 套不上」（那类「某引擎给不出→null」的量如 `time_worked_s` 照样进 model），而是 **`act` 是 Nova 引擎内部实现粒度、非我们 domain 的有效概念**（domain 有效的是 step；一个 step 展开成几次 act 是引擎内部细节）。model 只收 domain 有效的通用概念，引擎特有的内部量留在产物文件（session_summary.json）里、经 `kind=summary` 的不透明指针带出给 agent——这样 model 保持引擎无关的通用契约不被撑破，富信息也不丢。

## 纯确定性用例 → 空 report_index（已知、合理、非缺陷）

一个**只含确定性 step**（导航 + `@deterministic` 锚点，零 AI step）的用例，跑出的 RunReport
`report_index` **为空**、`index.html` 显示「本次 run 无原生报告产物」。这是**有意的诚实空态**，不是 bug：

- 原生报告产物**只在引擎实际执行 AI 操作时才产生**（Midscene 的 `agent.reportFile` 仅在调过
  agent 后存在；Nova 的 trajectory 仅在 `act`/`act_get` 后存在）。确定性 step 走 `page.goto`/
  `page.url`，**从不调引擎**，故**根本没有产物可归集**。RunReport 忠实反映「无产物」，不伪造内容。
- **判定不丢**：`result` 树仍含每个确定性 step 的 pass/fail/error + 时长（CI、退出码、status 汇总
  全程可用）。空的只是「人看的原生轨迹链接」，不是判定数据。
- 行为与含 AI step 的用例**一致**（都产有效 RunReport），产物差异**合理**（确定性 step 本就不产
  引擎报告）。验证 Midscene scope 级归集必须用含 AI 的用例——这不是 walkaround，是 Midscene
  报告天生 scope 级、且只在用 AI 时产生的客观事实。

**但这暴露一个上游缺口**（非本 ADR 范围）：确定性 step **不产任何可观测产物**——连「检查了哪个
URL、断言了什么」都不落痕（只有 pass/fail 进 result 树）。大量用确定性锚点的团队，其 RunReport
人看部分会长期空。这是「确定性 step 产物可观测性」问题，留待后续（见下「留口子」），本 ADR 的 RunReport
只负责归集**已有的**产物。

## 现在做 / 留口子

- **现在做（v1.0）**：本 ADR 上述全部决策均已实装（单测 + 两引擎真 e2e 覆盖）。
- **留口子不实现**：
  - **确定性 step 产物可观测性**：让 `@deterministic` handler 可选地产一个轻量产物（当时 URL / 截图 / 检查描述），使纯确定性用例的 RunReport 也有内容可看。判定真值在 result 树已够；产物可观测另开一轮（与 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md) 确定性 step 设计一并演进）。**与 [0036](./0036-deterministic-capability-discovery.md) 的划界**：0036 解决的是「**跑前**知道有哪些确定性锚点」（注册表自述 → `list-deterministic` / `plan` 派发标注），本口子要的是「**跑后**看见那一步实际做了什么」（运行期产物）——同源于确定性 step 的不可观测，但非同一件事，0036 落地后本口子照旧敞着。
  - 按 `kind` 的富渲染（`<video>`/`<iframe>`，皮层将来做）；trajectory 内部结构化提取。
  （注：store 读回面**已落地**——`RunStore.load_run_meta`/`load_run_state` + `ResultStore.load_job_result`/`load_all`，靠 `serialize` 完整重建，[0016](./0016-execution-architecture-core-lib-run-model.md)。）

## 重议

- 若 `jobs/*.json` 的绝对 `ref` 跨机器不可移植成为真实痛点（当前判定 CI 不解引用 ref、影响低）→ 重议是否需要某种真值层可移植机制（但不回退到 materialize 那种全量拷贝）。
- 若 CI/WebUI 消费 manifest 逼出更多结构化字段 → 扩 `report_index`（加字段，不改 `ReportRef` 三元组语义）。
