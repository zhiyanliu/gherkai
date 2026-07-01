# RunReport：跨引擎归集索引（不融合原生产物内容）

兑现 [0016](./0016-execution-architecture-core-lib-run-model.md) 一直 deferred 的「报告统一」（原里程碑 M5）。本 ADR 定 **RunReport 的语义、形态与扩展性契约**，并落地 `ReportStore` 的 local adapter。

## 决定：RunReport = 归集索引，不是内容融合

两个引擎的**原生**报告形态根本不同且不可统一（[0010](./0010-spike-as-apples-to-apples-benchmark.md) / CONTEXT「报告产物模型」）：Midscene 出单个 `report.html`（scope 级），Nova 出多个 trajectory（act 级）；未来引擎可能是录屏、外部 URL、JSON trace。

**RunReport 不试图解析/重渲染这些产物**——那等于给每个引擎写一个 HTML 解析器，既脆又把 core 锁死到具体引擎。RunReport 是一份**跨引擎、跨产物的统一目录 + 导航入口**：

- **`manifest.json`** —— 机器可读（CI / WebUI 消费）：一次 run 的判定/时长/成本（复用 `RunResult`）+ 一份扁平的报告产物清单（每条指向哪个 scope·scenario、哪个引擎、什么 kind、产物在哪）。
- **`index.html`** —— 人可导航：一个最小的单文件入口，每个产物一行链接，点开看**原样的**原生产物。

原生产物保持原样（各引擎自己最懂怎么呈现），RunReport 只**索引/链接**它们。

> **允许 vs 禁止的边界（写死）**：core/ReportStore 对产物只允许「按字节拷贝/移动 + 算一个链接」；**禁止**解析、重写、抽截图、合并内容。「产物在哪、属于谁」是归集索引的本分；「产物里画了什么」是引擎的事。

## 扩展性契约：新引擎零改 core

头等约束。保证机制：

- **`ReportRef = {kind: str, ref: ResourceUri, label: str | None}`**（取代旧 `{granularity: Literal["scope","act"], path}`）：
  - `kind` —— **开放字符串**，引擎自报（`scope`/`act`/未来 `video`/`trace`/`har`…）。core/wire/schedule **永不读它的值、永不按它分支**。`scope`/`act` 降为文档化约定常量，非枚举。
  - `ref` —— **统一指针 `ResourceUri`**，不假定是本地文件。本地产物用 `file://` 前缀；未来可是 `s3://`/`https://`。core/ReportStore **不 stat、不 fetch、不打开** ref，只索引/链接。
  - `label` —— 可选人类可读锚文本；缺省由消费端回落 `kind`。worker 可全部不报。
- **铁律**：`core/model.py`、`core/wire.py`、`core/schedule.py` 对 `ReportRef` 永久是**不透明搬运**。任何「按 kind 选 `<video>`/`<iframe>`」之类的渲染分支**只允许出现在 cli / WebUI 皮层**，绝不写回 core。
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
    def write(self, run_id: str, result: RunResult, *, created_at: str = "", materialize: bool = False) -> ResourceUri:
        """从 RunResult 归集出 <report_root>/<run_id>/{manifest.json, index.html}，返回 index.html 的 ResourceUri。

        只读 result 的 report_refs + scope_id/scenario_id/engine/status/时长/成本 做**导航视图**；
        不读 votes/steps 细节、不拿 status 当 CI 判定源（判定真值在 RunResult/ResultStore）。
        """
```

- **返回 `ResourceUri` 而非 `Path`**（封版前收口）：`LocalReportStore` 回 `file://…/index.html`，未来 `S3ReportStore` 回 `s3://…/index.html`——**同一签名容两种落点**，否则 S3 adapter 被迫返回 `Path` 包 `s3://`（`Path` 会把 `s3://b/x` 折成 `s3:/b/x`，错）。`ResourceUri = NewType("ResourceUri", str)`（定义在 `core/model.py`）：把这个**本就存在于 `ReportRef.ref` 注释里**的约定提升成命名类型，统一「`ReportRef.ref` 与 `write` 返回值都是带 scheme 的资源指针」。比裸 `str` 多一层意图、又零运行时成本/零依赖（运行时即 `str`）。消费端（cli/WebUI）只当 URI 用、不 stat/open——cli 现把它原样放进 `artifacts.report_index` 并打成可点击的 `file://` 链接。
  - 实现注意：`LocalReportStore` 内 `index_path.resolve().as_uri()`——`as_uri()` 要求绝对路径，而 cli 默认 `--report-dir` 是相对的（`reports`），不 `resolve()` 会抛 `ValueError`。
- `materialize=False`（默认）：不拷贝产物，`index.html` 的链接直接指向 `ref`（本地够用；v1.0 定位本地 smoke，[0015](./0015-v1-positioning-smoke-not-regression.md)）。
- `materialize=True`（opt-in）：把产物**拉进 report 让其自包含**——拷进 `<run_id>/artifacts/`、链接转相对路径 → 目录可整体搬走/发同事/CI 归档。
  - **默认不拷**是刻意的：本地跑时产物就在本机、手动查目录够用（[0016](./0016-execution-architecture-core-lib-run-model.md)「先散着」）。每 run 拷 N 个 MB 级 html + Nova 多个 trajectory 是纯磁盘放大、零收益——拷贝的价值只在搬运/归档时兑现，故 opt-in。

> **`ref` 由 worker 定、`materialize` 与 worker 产物放哪正交（关键边界，别混）**：
> - `ReportRef.ref` 指向**哪**是 **worker** 决定的——subprocess worker 产物落本地、报 `file://`；未来 Fargate worker **自己上传 S3**、报 `s3://`（[0029](./0029-fargate-engine-artifacts-to-s3.md)）。**ReportStore 不上传 worker 产物、不碰其持久化**（那是 per-worker by-design 的事，[0016](./0016-execution-architecture-core-lib-run-model.md)「worker⊥store」），只**不透明搬运**这个 ref。
> - `materialize` 是**正交的另一件事**：「要不要把产物拉进 report 让其自包含」。它随 ref 的 scheme 决定怎么拉：
>   - `file://` ref + materialize → **按字节拷**本地文件进 `artifacts/`（**当前唯一实装**）。
>   - `s3://` ref + materialize → **从 S3 下载**到 core 本地 `artifacts/`、ref 重指向本地（**尚未实现的扩展**——当前 materialize **只拷 `file://`**，`s3://`/`https://` ref 一律不动、报告直接引原 URI，见 `test_remote_ref_not_copied_even_when_materialize`）。
>   - materialize=False → 报告直接引 worker 报的 ref（`file://` 或 `s3://`），不拉。
> - 故 materialize **不会被「产物归位到 run 目录」抽空**：归位只改 subprocess 模式下本地产物落哪；materialize 管的是「产物是否进 report 自包含」，跨 worker 模式独立存在。
> - 以上是 **`LocalReportStore`** 的 materialize 语义（report 存本地）。**`S3ReportStore`** 的 materialize 目标语义（产物收拢进 `s3://…/<run_id>/artifacts/`、对称 Local）+ v1.1 第一版当 no-op 的取舍，见 [0029](./0029-fargate-engine-artifacts-to-s3.md)。
- `LocalReportStore` → 未来 `S3ReportStore` 只换「manifest+index 这些 **core 派生数据**落哪 / 返回的 URI scheme」，core 不动。（注意区分：`S3ReportStore` 是把 **RunReport 自身**（manifest/index.html）写到 S3，与「worker 把自己的产物上传 S3」是两回事。）
- **`write` 失败被隔离、不击穿已 commit 的 run**（实时写接缝，[0030](./0030-realtime-persistence-seam.md)）：RunReport 是**纯派生只读视图、可重建、永不作判定源**——故 `RunPersistence.finalize` 在 commit point（`finalize_run`，判定真值已落 ResultStore）之后才调 `ReportStore.write`，且把 write 的异常隔离（吞掉+留痕+返回 None），不让一个「可重建的报告」写失败把整个 run 拖成裸 traceback 退出、CI 拿不到判定输出。

**「生成 RunReport」与「materialize 产物」是两个正交开关，默认值不同（刻意）**：
- **生成 RunReport = run 的应得产物，cli 默认开**。每次 run 都归集到 `<report-dir>/<run_id>/`
  （`--report-dir` 配落点，默认 `reports/`）；`--no-report` 是逃生舱（CI 只看退出码/JSON、或调试不想落盘）。
  理由：manifest+index 仅几 KB（不拷产物时），却给出「这次 run 结果在哪、各引擎报告在哪」的统一入口——
  一个跑完不知结果在哪的工具是不完整的，不该要用户记得加 flag。
- **materialize = 把产物拷成自包含目录，opt-in（默认关）**。它代价大（每 run 拷 MB 级 html + Nova
  多 trajectory），价值只在搬运/上云/发同事时兑现，故按需开。两者独立：默认「生成 index 但不拷产物」
  （index 链接指向产物原位）。

**默认（不 materialize）两个引擎产物都归位到 run 目录内——落点对称**：cli 经环境变量把两个 SDK 的产物
落点都设到 `reports/<run_id>/` 下（[0016](./0016-execution-architecture-core-lib-run-model.md) 组合根注入）：
- **Nova**：`NOVA_LOGS_DIR` → SDK `logs_directory`，trajectory 落 `reports/<run_id>/nova-trajectories/`。
- **Midscene**：`MIDSCENE_RUN_DIR` → SDK run 根目录，`report.html` 落 `reports/<run_id>/midscene-run/report/`。
  （SDK 用 `path.resolve(cwd, MIDSCENE_RUN_DIR)`，cli 传**绝对路径**避 worker cwd 歧义。）
- 故默认 RunReport 的产物**都在 `reports/<run_id>/` 树内**，index 的 `file://` 绝对链接本机可点、目录整体
  在本机可查。**唯一残留**：`file://` 是绝对路径，把 `reports/<run_id>/` 拷到**另一台机器**后链接会断——
  此时才需 `--materialize`（收进 `artifacts/`、转相对链接）。故 materialize 从「统一落点」降级为「跨机器/归档
  自包含」这个更窄的 opt-in（本地够用场景不付每 run 拷 MB 的代价，[0015](./0015-v1-positioning-smoke-not-regression.md)）。
- **归位的另一收益**：产物不再落相对 worker cwd 的固定 `midscene_run/`（每 run 覆盖、与 run 无关），
  而是 run 专属目录——为 v1.1 云端归集/上传（[0016](./0016-execution-architecture-core-lib-run-model.md) worker⊥store）铺路，两引擎落点对称、处理一致。

**职责边界（三 port 正交，[0016](./0016-execution-architecture-core-lib-run-model.md)）**：`RunStore`=控制面（definition `RunMeta` + 运行态 `RunState`：status/血缘）、`ResultStore`=数据面（判定真值唯一权威）、`ReportStore`=**纯派生只读导航视图**（可从 `RunResult` 完全重建、永不作 CI 判定源）。`ResultStore` 旧 docstring「RunReport 归集靠它」一句删除——归集职责移交 `ReportStore`。

## manifest.json 形态

**纯派生导航视图：薄信封 + 扁平 report_index，不内嵌 result 真值副本**。判定真值由 `ResultStore` 持有（数据面，每 job 落 `jobs/<scope_id>.json` / 未来对象存储），运行态/身份由 `RunStore` 持有（`run_meta.json` + `run_state.json` / 未来 DDB，[0016](./0016-execution-architecture-core-lib-run-model.md)）；manifest 靠 **`run_id` 软引用**那次 run——CI 要判定就拿 run_id 找 `ResultStore`。这样 report 是真·派生品（可删可重建、永不作判定源），无真值冗余、无一致性风险。

```jsonc
{
  "schema_version": 1,
  "run_id": "...",               // 软引用那次 run；完整判定真值在 ResultStore（jobs/*.json），按此 id 取
  "created_at": "...",           // 组合根生成的时间戳（字符串，由调用方传入）
  "report_index": [              // 扁平投影，便于 CI/WebUI 直接遍历
    { "scope_id": "...", "scenario_id": "..."|null, "engine": "...", "kind": "...",
      "ref": "...", "href": "...", "label": "..." }
  ]
}
```

- `report_index` 从内存 `RunResult` 树一次投影（含全部 report_refs，**不走逐条 append**）；`scenario_id=null` 表 scope 级 ref。
- 每条含 `ref`（原始不透明指针，原样保留）与 `href`（index.html 实际导航用的链接）：`materialize=False` 时 `href == ref`；`materialize=True` 时 `href` 是拷进 `artifacts/` 的相对路径（`ref` 仍留原值）。
- index.html 的 run 摘要（status/时长/成本/各 job 上色）**直接用内存 `RunResult`** 渲染，不从 manifest 读（manifest 已不含 result）。
- **manifest 不内嵌 `to_dict(result)`**（曾考虑、否决）：那会让派生视图承载判定真值副本（与 `ResultStore`/`RunStore` 冗余）；改为软引用 run_id 消除冗余。`serialize` 仍是单一序列化真理源（cli `--json` 与各 store 共用），只是不塞进 manifest。
- `to_dict` 含 `job.engine`、`scenario.report_refs`（序列化补齐项）。
- manifest **不冗余 status 当判定源**——`result` 里已有，CI 读 `result.status`，不读信封。

## index.html 形态

最小「带状态摘要的链接清单」：纯 Python 字符串拼装 + `html.escape()`，**无模板引擎、无外链 JS/CSS、单文件**（对齐 `wire.py`「手写映射、显式稳定」与 core「薄编排层无重型依赖」）。

- 顶部一行 run 摘要（run_id + 总 status + duration + 原生量成本）。
- 一个列表，每条 report_ref 一行：job.status 三态上色 + scope_id + engine + `[kind]` + 指向 `ref` 的 `<a>`（`label` 或回落 `kind` 作锚文本）。
- 三态上色用内联 `<style>`。
- **空态**：无任何 report_ref 时仍生成有效的「空报告」index.html（标注本次无原生产物），不报错。

## act 级 reportRef 的回传与归属（Nova 引擎补对称）

Nova trajectory 此前落系统临时目录（会被清理）、worker 不报。本轮一起补：

- Nova worker 设 `NovaAct(logs_directory=<run 专属持久目录>)`，act/act_get 的 trajectory 落到那里。
- worker 在 **`scenario_done`** 边界聚合本 scenario 的 act 产物，报 act 级 `ReportRef`（`kind="act"`，`ref=file://...`）——经 [0024](./0024-worker-core-protocol.md) `ScenarioDone.report_refs`（协议已支持）回传。
- 与 Midscene 的 scope 级（`scope_done.report_refs`）对称：两个引擎都报、kind 各异、core 不分支。

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
人看部分会长期空。这是「确定性 step 产物可观测性」问题，留待后续（见下「留口子」），本轮 RunReport
只负责归集**已有的**产物。

## 现在做 / 留口子

- **现在做（v1.0）**：上述 `ReportRef` 改造、`run_id`（归位进 `RunMeta` definition）+ 组合根生成、`JobResult` 经持有的 `Job` 取 `engine`、`ReportStore.write` 接口 + `LocalReportStore`（manifest + index，默认不 materialize）、**两引擎产物对称归位到 run 目录**（Nova `NOVA_LOGS_DIR`→trajectory、Midscene `MIDSCENE_RUN_DIR`→report.html）+ act 级 reportRefs、cli 默认生成 RunReport（`--no-report` 跳过、`--report-dir` 配落点、`--materialize` opt-in）、单测 + 两个引擎真 e2e。
- **留口子不实现**：
  - **确定性 step 产物可观测性**：让 `@deterministic` handler 可选地产一个轻量产物（当时 URL / 截图 / 检查描述），使纯确定性用例的 RunReport 也有内容可看。本轮判定真值在 result 树已够；产物可观测另开一轮（与 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md) 确定性 step 设计一并演进）。
  - `materialize` 的 S3 后端；按 `kind` 的富渲染（`<video>`/`<iframe>`，皮层将来做）；trajectory 内部结构化提取。
  （注：store 读回面**已落地**——`RunStore.load_run_meta`/`load_run_state` + `ResultStore.load_job_result`/`load_all`，靠 `serialize` 完整重建，[0016](./0016-execution-architecture-core-lib-run-model.md)。）

## 重议

- 若出现「报告必须自包含搬运」的硬需求成为默认 → 重议 `materialize` 默认值。
- 若 CI/WebUI 消费 manifest 逼出更多结构化字段 → 扩 `report_index`（加字段，不改 `ReportRef` 三元组语义）。
