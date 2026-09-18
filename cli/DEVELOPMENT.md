# cli 包 —— contributor 文档

用户面文档有两处：同目录的 [`README.md`](./README.md)（发行包入口页，逐字上 PyPI）与 [`docs/user-guide/`](../docs/user-guide/README.md)（流程与选项细节的 owner）。本文件给改这个包的人，不进发行包。

发行名 `gherkai` / import 名 `gherkai_cli` / 命令 `gherkai`（ADR 0037 决策 2a「三名分离」）。

`core/` 是纯库（零引擎依赖、不碰文件系统）。**cli 是它的第一张皮**：解析参数 → 经产品本体
`gherkai_runtime.compose` 读 `.feature`、装配引擎与 Store adapter 注入给 core → 把 `RunResult` 渲染给人或 CI 看。
WebUI 将来是另一张皮，**直接调 core、复用产品本体 `gherkai_runtime`（compose 等组合根逻辑所在的平级包 `runtime/`，ADR 0016「演进」节）**，不经本 cli。

设计见 [ADR 0016](../docs/adr/0016-execution-architecture-core-lib-run-model.md)（执行架构 / 组合根注入）；
无状态跑批（`submit`/`status` 的「提交完就走 → 事件驱动推进 → 轮询收集」）见 [ADR 0034](../docs/adr/0034-detached-batch-reconciler.md)。

## 模块

```
cli/gherkai_cli/
├── __main__.py   ← argparse 皮：run/submit/status/explain/plan/list-engines/doctor/list-deterministic/deploy/destroy/skill（嵌套 `skill install`），外加两个内部隐藏子命令（`argparse.SUPPRESS`、由 submit 以 setsid fork 拉起、非用户直接调）：`_reconcile`（local 档 per-run 推进进程入口，ADR 0034）/ `_tunnel_watch`（cloud submit 的隧道守护进程入口，ADR 0035 决策 3）——解析 → 调 gherkai_runtime.compose/gherkai_core → 注入 RunPersistence 实时落库 → 调 render；定义退出码
├── deploy.py     ← deploy/destroy 的命令面 + 部署 provider 发现（entry point group `gherkai.deploy`）；**零 IaC 知识**、不 import aws_cdk（ADR 0037 决策 6）
├── render.py     ← 表层渲染：0024 事件 → 进度行；RunResult → 文本汇总 / JSON；RunState → status 视图；
│                    JobResult + evidence → explain 的文本/JSON（两形态同源，见模块内 explain 节的注释）
├── skill_install.py ← `gherkai skill install`：importlib.resources 定位包内 skills/gherkai/、整目录收敛 + `.gherkai-skill-version` 标记、`--print`（ADR 0043 决策三）
└── skills/gherkai/  ← 随 wheel 发行的 agent skill（SKILL.md + references/；hatchling 默认把包目录内非 .py 文件收进 sdist/wheel）。references/cli-json-contract.md **不手写**：
                     由 `tools/render_skill_contract.py` 从 docs/internals/cli-json-contract.md 确定性生成（ADR 0043 决策四）
```

组合根逻辑（compose/detached/names/tunnel/tunnel_host）住在平级的产品本体包 `runtime/gherkai_runtime/`，**不留在本包里**：Lambda 与 IaC 也要用它，留在皮里会迫使它们依赖 argparse 层（ADR 0016「演进」节）。cli 这张皮只剩 argparse + 标准 IO。

装了多个部署 provider（当前只有 aws 一个）时 `--provider <名>` 必给；装一个时不必给；一个都没装则报「装 `gherkai[deploy-aws]`」并退 `2`。

**Node ≥ 22 是 `deploy` 的前置**（与 worker 的 `engines.node` 同一下限）：Python 版 CDK 是 jsii 绑定、import 即起
node 子进程，cdk CLI 本身也是 npm 物；PATH 上有 `cdk` 就用它，没有则 `npx -y aws-cdk@2` 兜底。

## 从 checkout 跑

下面都从**仓库根**键入（feature 路径相对当前目录解析）：

```bash
uv sync                                            # 一次装齐五个 workspace 成员：core/runtime/cli/engines/novaact/deploy_aws（editable，单一根 uv.lock）
(cd engines/midscene && npm ci && npm run build)   # midscene worker（Node 22）
export GHERKAI_WORKER_MIDSCENE_CMD="node $PWD/engines/midscene/dist/bin.mjs"   # dev 态指向本仓库的 worker

uv run gherkai plan features/wikipedia_generic.feature
uv run gherkai run  features/wikipedia_generic.feature          # 真跑会产生 AWS 费用：模型调用 + AgentCore 会话

# cloud 档要先有部署好的后端（部署方做一次，dev 环境自己部一套即可）：
uv run gherkai deploy --prefix dev- --vpc default
uv run gherkai run features/wikipedia_generic.feature --backend cloud --prefix dev-
```

`--backend cloud` 的表 / 桶 / cluster / task-def / SSM 里的子网·安全组与 worker 镜像 variant 指针**全由 `gherkai deploy` 供给**，
手工建一张表加一个桶跑不起来：起 worker 前依次过版本 skew 闸、资源 preflight（events 表 + cluster + 本 run 每个引擎的
task-def + 桶，落库时另加 runs 表）、variant 解析、子网/安全组解析，任一项缺就退 `2`。名字统统由 `--prefix` 拼出，
所以 `--prefix` 要与部署时的一致；只想覆盖表名/桶名时才用 `--ddb-table` / `--s3-bucket`（其余资源仍按 prefix 推导）。
使用者侧的部署与排错步骤见 [`docs/user-guide/cloud-backend.md`](../docs/user-guide/cloud-backend.md)。

> `core/tests/README.md` 的「一次性：建真表 + 真桶」只服务 core 集成测试（同一套表/桶 schema，但不足以支撑
> `--backend cloud`）。

## 跑测试

```bash
uv run pytest              # 仓库根：全部 workspace 成员
cd cli && uv run pytest -q # 只跑本包（cwd 决定收集范围）
```

文档/文案护栏有六份住在本包的 `tests/`（全仓清单见根 [`CONTRIBUTING.md`](../CONTRIBUTING.md) 的「测试」节）：

- `test_package_readmes.py` —— 进包的 README = 发行包长描述（零 ADR/决策号/内部机制名、零相对链接、每个包目录一份 `DEVELOPMENT.md`；另守根 `README.md`、各包 pyproject/package.json 的 `description`——PyPI/npm 页顶 Summary——与 GitHub Release 正文的固定块）。
- `test_user_docs.py` —— 仓库内的用户文档（`docs/user-guide/**`、根 `README.md`、`CHANGELOG.md`）：零内部指代、相对链接可达、owner 表与目录两向差集。
- `test_release_notes.py` —— `.github/scripts/release_notes.py`：changelog 节的 gate 与 Release 正文渲染。
- `test_user_facing_messages.py` —— 产品面文案不带内部指代（扫五个生产包的 Python 字面量 + Midscene 的 `.mts` 源）。
- `test_skill.py` —— 随 wheel 发行的 agent skill（同一禁词表与相对链接正则，共享常量在 `cli/tests/_doc_rules.py`；另对照 argparse 真值、契约页键名、转换副本相等、目录白名单与形态上限）。
- `test_cli_json_contract.py` —— `--json` 的全部键名对照 `docs/internals/cli-json-contract.md`，文档漏键即红（`list-workers` 的样例要 moto，那部分在 `deploy_aws/tests/test_workers.py`）。

改了 `docs/internals/cli-json-contract.md` 后跑 `uv run python tools/render_skill_contract.py` 重生成 skill 副本，否则 `test_skill.py` 的相等性断言红。

## 实时落库

`run` 不是「跑完才一次性落盘」——`__main__` 注入 core 的 `RunPersistence`（组合根注入三个 Store adapter），
run 开始即写 definition + 初始全 pending 态，每个 scope 起跑刷 RUNNING、完成即落该 scope 判定真值，
最后 `finalize` 写总状态（commit point）。`--no-report` 时跳过整条落库（裸跑、零落盘逃生舱）。

落哪由 `--backend` 定：默认 `local`（文件落 `--report-dir`）；`--backend cloud` 让组合根改注入 DynamoDB/S3
adapter、复用同一条 `RunPersistence`，把状态落 DynamoDB、判定真值与报告落 S3（表/桶需预先建好——由 `gherkai deploy` 供给）。
未来 WebUI 复用同一套 `gherkai_runtime.compose` 装配，cli 这张皮的接线不变。

> `--backend cloud` 需 boto3——**装 CLI 即已带**：发行包 `gherkai` 硬依赖 `gherkai-runtime[aws]`
> （已被 ADR 0037 决策 2c 反转：原为「cli 主依赖不含 boto3、cloud 走可选 extra」，库层 `gherkai-core[aws]` /
> `gherkai-runtime[aws]` extra 保留给库消费者）。code 层不变量不变：**local 路径绝不 import boto3**
> （惰性 import 收在 compose 的 `_make_*` 钩子里）。

### RunReport 内部

- `manifest.json` —— 薄信封（run_id 等）+ 报告产物的扁平清单（引擎原生产物 + 每个 AI step 的 gherkai evidence）。判定/时长/成本**不在此**——用
  `run_id` 到 `ResultStore`（`jobs/*.json`）取判定真值；`index.html` 才含判定明细。
- `index.html` —— 判定明细树 + 每个报告产物（Midscene html / Nova trajectory / step evidence）一行链接，点开看**原样**文件。
  RunReport 只索引/链接、**不解析融合**产物内容；新引擎报任意 `kind` 零改 core（ADR 0027）。
- index 链接指向产物**原位**（local 相对链接——产物就在 `reports/<run_id>/` 树内、目录可整体搬走；cloud 为 `s3://`）。

## plan 的实现细节

- 派发预期标注靠 worker 自述命中（ADR 0036）：起本地**瞬时 worker 子进程**做 match 查询，零 AWS 零花费；
  引擎环境未装则自动降级为无标注。
- 文本模式对 DataTable/DocString 多行参数只标注尺寸（`+dataTable(行×列)` / `+docString(N 行)`）保持紧凑；
  要核对参数**完整内容**用 `--json`（携带 content/rows 全文）。
- `plan` 退出码 0=可跑 / 2=配置错（`PlanError`：uri 冲突 / 同 scope 多 engine 等）。

## 为何拆 `submit` / `status`

`run` 要求 CLI 全程在线（网断/关机即中止）；`submit` 提交完就走——local 由脱离 CLI 的 per-run 进程推进、
cloud 由云端 Lambda 事件驱动链推进（submit 机器无 ECS 写/执行权限——仅 preflight 的只读探活，可立即关机）。
`status --wait` 是三个推进触发源之一（人来查即接力），保证「推进即使中断、也能被查询者续到底」（ADR 0034）。

`submit` **有意不收** `--subnet`/`--security-group`：cloud submit 只写 runs 表、不碰 SSM/ECS，Fargate 网络由 IaC
注给 reconciler/kicker Lambda 的 env——在 `submit` 上声明这两个 flag 恒不生效。

cloud submit 的 `--max-concurrency` 受部署侧 cap 钳制（kicker/reconciler Lambda 的 env `MAX_CONCURRENCY`，
IaC 设、当前 8——task 计入部署方账单，故留一道上限）；声明超上限时 preflight 提示「本 run 将按上限并行」、不拦提交。
local 无此上限（worker 跑在提交者自己的机器、以自己的凭证计费）。

## 退出码分层的切分线

cloud 失败分层的切分线 = run 是否已真正开跑：起 worker 前的配置/可达问题退 `2`，跑到一半的云端故障退 `1`。
`submit` 的退出码衡量「提交成功与否」、`status --wait` 衡量「这个 run 判定过没过」——`run` 一条命令里揉在一起的
「提交 + 判定」被拆开了（ADR 0034）。归码只有一处 helper，`_cmd_plan` 与 `_cmd_run` 共用：各写一份必漂。

**preflight 次序是刻意的：版本 skew → 资源存在性 → variant 解析。** skew 的修复动作（`gherkai deploy`）正好也把
资源补齐、也是重推镜像的前置；反过来先报「表不存在」或「variant 没推」只会让人白查一轮 `--prefix` / 白推一轮镜像。

## 版本 skew 六态（ADR 0037 决策 7）

deploy 会把自己的版本写成后端的版本戳，四个 cloud 入口（`run`/`submit`/`status`/`explain`）**先于资源预检 / 任何云端读**比它（`doctor --backend cloud` 另把它当一个自检项读）：

| 比对结果 | 行为 |
|---|---|
| 同版本 | 放行、不打扰 |
| **CLI 新于后端** | 退 `2`，**没有放行 flag** |
| CLI 旧于后端 | 警告不拦（`uv tool upgrade gherkai` 跟上） |
| 后端没有版本戳（早于本机制的部署） | 警告不拦 + 提示部署方跑一次 `gherkai deploy` 写入 |
| 任一侧是开发版（含 `.dev`/`.post`/`+`） | 跳过比对、警告一句（dev 版逐提交前进，逐字比会把每次都判成 skew） |
| 取不到本机 CLI 版本（未以包形式安装、源码直跑） | 跳过比对、警告一句 |

**不设放行口是刻意的**：放行等于让新 CLI 写的任务定义进旧后端读，后果不可知且静默；用
`uvx --from 'gherkai==<后端版本>' gherkai …` 按版本临时跑零成本。版本是一个旋钮——`gherkai` 与后端被 `==`
钉在同版本，没有「先升后端再升 CLI」这种次序。

## VPC 档比对

`--vpc` **不给隐式默认、且生效的档记在后端并在每次 deploy 前比对**，两道一起才够：只强制显式给值挡不住「第二次
deploy 敲错档」，而漏档会合成「新建整套 VPC 并替换 worker 安全组」这类危险变更集——实际发生过。
四种比对结果与各自的放行动作见 [`docs/user-guide/cloud-backend.md`](../docs/user-guide/cloud-backend.md)「VPC 三档」；
比对实现与状态常量在 `deploy_aws/gherkai_deploy_aws/cli.py`（`classify_vpc_state`），contributor 侧说明见
[`deploy_aws/DEVELOPMENT.md`](../deploy_aws/DEVELOPMENT.md)。

`--refresh-context` 丢弃本机缓存的 CDK 环境查询结果（VPC/子网/AZ）重新查询，缓存位置与首次查询的那条 CDK 警告见
同一页。

## 相关 ADR

- [0016](../docs/adr/0016-execution-architecture-core-lib-run-model.md) 执行架构 / 组合根注入 / `runtime` 抽包
- [0024](../docs/adr/0024-worker-core-protocol.md) worker↔core 协议（render 消费的事件）
- [0027](../docs/adr/0027-runreport-aggregation-index.md) RunReport 归集索引 / [0030](../docs/adr/0030-realtime-persistence-seam.md) 实时写接缝
- [0033](../docs/adr/0033-iac-aws-backend-and-composition-wiring.md) 云端资源清单与命名契约（`destroy` 后表/桶/ECR 是 RETAIN）
- [0034](../docs/adr/0034-detached-batch-reconciler.md) 无状态跑批（submit/status、job timeout 两层声明与三路 enforce）
- [0035](../docs/adr/0035-local-app-testing-via-tunnel.md) `--expose-local` 隧道（凭据轮换、谁负责拆、TTL 算法）
- [0036](../docs/adr/0036-deterministic-capability-discovery.md) 确定性能力自述（`list-deterministic`、plan 标注）
- [0037](../docs/adr/0037-distribution-and-packaging.md) 分发与打包（三名分离 / worker 定位链 / `steps/` 约定 / deploy 进 wheel / 版本 skew）
- [0038](../docs/adr/0038-worker-image-delivery.md) worker 镜像交付（variant → 显式 task-def revision、被拒方案）
- [0042](../docs/adr/0042-step-evidence-and-explain.md) step 级机读证据与 `explain`（证据 schema、文本预算、只用 0/2 的退出码）
- [0043](../docs/adr/0043-agent-skill-for-driving-gherkai.md) agent skill（包内源文件随 wheel 发行、`skill install` 整目录收敛、契约页确定性转换副本、护栏与评测）
