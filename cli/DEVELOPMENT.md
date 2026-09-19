# cli 包 —— contributor 文档

用户面文档有两处：同目录的 [`README.md`](./README.md)（发行包入口页，逐字上 PyPI）与 [`docs/user-guide/`](../docs/user-guide/README.md)（流程与选项细节的 owner）。本文件面向改动本包的 contributor，不进发行包。

发行名 `gherkai` / import 名 `gherkai_cli` / 命令 `gherkai`（ADR 0037 决策 2a「三名分离」）。

`core/` 是纯库（零引擎依赖、不访问文件系统）。**cli 是它的第一个前端**：解析参数 → 经产品本体
`gherkai_runtime.compose` 读 `.feature`、装配引擎与 Store adapter 注入给 core → 把 `RunResult` 渲染供人或 CI 消费。
WebUI 将来是另一个前端，**直接调 core、复用产品本体 `gherkai_runtime`（compose 等组合根逻辑所在的平级包 `runtime/`，ADR 0016「演进」节）**，不经本 cli。

设计见 [ADR 0016](../docs/adr/0016-execution-architecture-core-lib-run-model.md)（执行架构 / 组合根注入）；
无状态批量运行（`submit`/`status` 的「提交完就走 → 事件驱动推进 → 轮询收集」）见 [ADR 0034](../docs/adr/0034-detached-batch-reconciler.md)。

## 模块

```
cli/gherkai_cli/
├── __main__.py   ← argparse 前端：run/submit/status/explain/plan/list-engines/doctor/list-deterministic/deploy/destroy/skill（嵌套 `skill install`），外加两个内部隐藏子命令（靠不传 `help` + 收窄 subparsers 的 `metavar` 隐去，**别改用 `argparse.SUPPRESS`**——会以「==SUPPRESS==」漏进 `--help`，理由见 `__main__.py` 该处注释；由 submit 以 setsid fork 启动、不供用户直接调用）：`_reconcile`（local 后端 per-run 推进进程入口，ADR 0034）/ `_tunnel_watch`（cloud submit 的隧道守护进程入口，ADR 0035 决策 3）——解析 → 调 gherkai_runtime.compose/gherkai_core → 注入 RunPersistence 实时落库 → 调 render；定义退出码
├── deploy.py     ← deploy/destroy 的命令面 + 部署 provider 发现（entry point group `gherkai.deploy`）；**零 IaC 知识**、不 import aws_cdk（ADR 0037 决策 6）
├── render.py     ← 表层渲染：0024 事件 → 进度行；RunResult → 文本汇总 / JSON；RunState → status 视图；
│                    JobResult + evidence → explain 的文本/JSON（两形态同源，见模块内 explain 节的注释）
├── skill_install.py ← `gherkai skill install`：importlib.resources 定位包内 skills/gherkai/、整目录收敛 + `.gherkai-skill-version` 标记、`--print`（ADR 0043 决策三）
└── skills/gherkai/  ← 随 wheel 发行的 agent skill（SKILL.md + references/；hatchling 默认把包目录内非 .py 文件收进 sdist/wheel）。references/cli-json-contract.md **不手写**：
                     由 `tools/render_skill_contract.py` 从 docs/internals/cli-json-contract.md 确定性生成（ADR 0043 决策四）
```

组合根逻辑（compose/detached/names/tunnel/tunnel_host）位于平级的产品本体包 `runtime/gherkai_runtime/`，**不留在本包里**：Lambda 与 IaC 也要用它，留在前端里会迫使它们依赖 argparse 层（ADR 0016「演进」节）。cli 这个前端只剩 argparse 与标准 IO。

已安装多个部署 provider（当前只有 aws 一个）时 `--provider <名>` 必给；只安装一个时可省略；未安装任何 provider 时报「装 `gherkai[deploy-aws]`」并退 `2`。

**Node ≥ 22 是 `deploy` 的前置**（与 worker 的 `engines.node` 同一下限）：Python 版 CDK 是 jsii 绑定、import 时即启动
node 子进程，cdk CLI 本身也以 npm 包形式分发；PATH 上存在 `cdk` 即使用它，否则回退到 `npx -y aws-cdk@2`。

## 从 checkout 运行

以下命令均从**仓库根**键入（feature 路径相对当前目录解析）：

```bash
uv sync                                            # 一次安装五个 workspace 成员：core/runtime/cli/engines/novaact/deploy_aws（editable，单一根 uv.lock）
(cd engines/midscene && npm ci && npm run build)   # midscene worker（Node 22）
export GHERKAI_WORKER_MIDSCENE_CMD="node $PWD/engines/midscene/dist/bin.mjs"   # dev 态指向本仓库的 worker

uv run gherkai plan features/wikipedia_generic.feature
uv run gherkai run  features/wikipedia_generic.feature          # 实际运行会产生 AWS 费用：模型调用 + AgentCore 会话

# cloud 后端需要先部署好（部署方执行一次，dev 环境各自部署一套即可）：
uv run gherkai deploy --prefix dev- --vpc default
uv run gherkai run features/wikipedia_generic.feature --backend cloud --prefix dev-
```

`--backend cloud` 的表 / 桶 / cluster / task-def / SSM 里的子网·安全组与 worker 镜像 variant 指针**全由 `gherkai deploy` 供给**，
手工建一张表和一个桶不足以支撑运行：启动 worker 前依次通过版本 skew 闸、资源 preflight（events 表 + cluster + 本 run 每个引擎的
task-def + 桶，落库时另加 runs 表）、variant 解析、子网/安全组解析，任一项缺失即退 `2`。资源名一律由 `--prefix` 拼接，
因此 `--prefix` 须与部署时一致；单独覆盖某个资源名或网络参数时才用 `run` 的六个单项覆盖 flag
（`--ddb-table`/`--s3-bucket`/`--events-table`/`--cluster`/`--subnet`/`--security-group`；`submit` 只收前两个，其余取部署侧写进
后端的值，三个 Lambda 无 flag、恒按 prefix 推导），逐项默认值与对应 SSM 参数见
[`docs/user-guide/configuration.md`](../docs/user-guide/configuration.md) 的「云端资源名与网络的单项覆盖」表。
使用者侧的部署与排错步骤见 [`docs/user-guide/cloud-backend.md`](../docs/user-guide/cloud-backend.md)。

> `core/tests/README.md` 的「一次性：建真表 + 真桶」只服务 core 集成测试（同一套表/桶 schema，但不足以支撑
> `--backend cloud`）。

## 运行测试

```bash
uv run pytest              # 仓库根：全部 workspace 成员
cd cli && uv run pytest -q # 只运行本包（cwd 决定收集范围）
```

本包 `tests/` 下有六份文档与文案护栏：`test_package_readmes.py`、`test_user_docs.py`、`test_release_notes.py`、`test_user_facing_messages.py`、`test_skill.py`、`test_cli_json_contract.py`；各自的覆盖范围见根 [`CONTRIBUTING.md`](../CONTRIBUTING.md)「测试」节的护栏表。

修改 `docs/internals/cli-json-contract.md` 后执行 `uv run python tools/render_skill_contract.py` 重新生成 skill 副本，否则 `test_skill.py` 的相等性断言会失败。

## 实时落库

`run` 并非等到运行结束才一次性落盘：`__main__` 注入 core 的 `RunPersistence`（组合根注入三个 Store adapter），
run 开始即写 definition 与初始全 pending 态，每个 scope 开始执行时写入 RUNNING、完成即落该 scope 判定真值，
最后 `finalize` 写总状态（commit point）。`--no-report` 时跳过整条落库（零落盘运行路径）。

落到哪由 `--backend` 决定：默认 `local`（文件落 `--report-dir`）；`--backend cloud` 让组合根改注入 DynamoDB/S3
adapter、复用同一条 `RunPersistence`，把状态落 DynamoDB、判定真值与报告落 S3（表/桶需预先建好，由 `gherkai deploy` 供给）。
未来 WebUI 复用同一套 `gherkai_runtime.compose` 装配，cli 这个前端的接线不变。

> `--backend cloud` 需要 boto3，**安装 CLI 即已包含**：发行包 `gherkai` 硬依赖 `gherkai-runtime[aws]`
> （已被 ADR 0037 决策 2c 反转：原为「cli 主依赖不含 boto3、cloud 走可选 extra」，库层 `gherkai-core[aws]` /
> `gherkai-runtime[aws]` extra 保留给库消费者）。code 层不变量不变：**local 路径绝不 import boto3**
> （惰性 import 收敛在 compose 的 `_make_*` 钩子内）。

### RunReport 内部

- `manifest.json` —— 薄信封（run_id 等）+ 报告产物的扁平清单（引擎原生产物 + 每个 AI step 的 gherkai evidence）。判定、时长、成本**不在此**：须以
  `run_id` 到 `ResultStore`（`jobs/*.json`）取判定真值；`index.html` 才含判定明细。
- `index.html` —— 判定明细树 + 每个报告产物（Midscene html / Nova trajectory / step evidence）一行链接，链接打开的是**原样**文件。
  RunReport 只索引与链接、**不解析融合**产物内容；新引擎上报任意 `kind` 都无需改动 core（ADR 0027）。
- index 链接指向产物**原位**（local 为相对链接：产物就在 `reports/<run_id>/` 树内、目录可整体移动；cloud 为 `s3://`）。

## plan 的实现细节

- 派发预期标注靠 worker 自述命中（ADR 0036）：启动本地**瞬时 worker 子进程**做 match 查询，零 AWS 零费用；
  引擎环境未安装则自动降级为无标注。
- 文本模式对 DataTable/DocString 多行参数只标注尺寸（`+dataTable(行×列)` / `+docString(N 行)`）以保持紧凑；
  核对参数**完整内容**须用 `--json`（携带 content/rows 全文）。
- `plan` 退出码 0=可运行 / 2=配置错（`PlanError`：uri 冲突 / 同 scope 多 engine 等）。

## 为何拆 `submit` / `status`

`run` 要求 CLI 全程在线（网断或关机即中止）；`submit` 提交完就走：local 由脱离 CLI 的 per-run 进程推进，
cloud 由云端 Lambda 事件驱动链推进（submit 机器无 ECS 写/执行权限，对 ECS 仅做 preflight 的只读探活，可立即关机）。
`status --wait` 是三个推进触发源之一（查询者到来即接力），保证「推进即使中断、也能被查询者续到底」（ADR 0034）。

`submit` **有意不接受** `--subnet`/`--security-group`：cloud submit 只写 runs 表、不访问 SSM/ECS，Fargate 网络由 IaC
注入 reconciler/kicker Lambda 的 env；在 `submit` 上声明这两个 flag 恒不生效。

cloud submit 的 `--max-concurrency` 受部署侧 cap 钳制（kicker/reconciler Lambda 的 env `MAX_CONCURRENCY`，
由 IaC 设定、当前为 8；task 计入部署方账单，故设一道上限）；声明值超上限时 preflight 提示「本 run 将按上限并行」、不拦截提交。
local 无此上限（worker 运行在提交者自己的机器、以自己的凭证计费）。

## 退出码分层的切分线

cloud 失败分层的切分线 = run 是否已真正开始执行：启动 worker 前的配置或可达性问题退 `2`，已开始执行之后的云端故障退 `1`。
`submit` 的退出码衡量「提交成功与否」，`status --wait` 衡量「该 run 的判定是否通过」：`run` 在一条命令里合并的
「提交 + 判定」由此被拆开（ADR 0034）。归码只有一处 helper，`_cmd_plan` 与 `_cmd_run` 共用：各写一份必然漂移。

**preflight 次序是有意如此：版本 skew → 资源存在性 → variant 解析。** skew 的修复动作（`gherkai deploy`）同时补齐
资源，也是重推镜像的前置；反过来先报「表不存在」或「variant 未推送」，只会导致一轮无效的 `--prefix` 排查或一轮无效的镜像推送。

## 版本 skew 六态（ADR 0037 决策 7）

deploy 会把自身版本写成后端的版本戳；四个 cloud 入口（`run`/`submit`/`status`/`explain`）**先于资源预检与任何云端读**与它比对（`doctor --backend cloud` 另把它作为一个自检项读取）：

| 比对结果 | 行为 |
|---|---|
| 同版本 | 放行，不提示 |
| **CLI 新于后端** | 退 `2`，**无放行 flag** |
| CLI 旧于后端 | 警告不拦截（以 `uv tool upgrade gherkai` 升级即可） |
| 后端没有版本戳（早于本机制的部署） | 警告不拦截，并提示部署方执行一次 `gherkai deploy` 写入 |
| 任一侧是开发版（含 `.dev`/`.post`/`+`） | 跳过比对，输出一条警告（dev 版逐提交前进，逐字比对会把每次都判成 skew） |
| 取不到本机 CLI 版本（未以包形式安装、从源码直接运行） | 跳过比对，输出一条警告 |

**不设放行口是有意的**：放行等于让新 CLI 写入的任务定义被旧后端读取，后果不可知且静默；以
`uvx --from 'gherkai==<后端版本>' gherkai …` 按指定版本临时运行的成本为零。版本只有一处可调：`gherkai` 与后端被 `==`
约束在同一版本，不存在「先升后端再升 CLI」这种次序。

## VPC 档比对

`--vpc` **不给隐式默认、且生效的档记在后端并在每次 deploy 前比对**，两道缺一不可：只强制显式给值无法防止第二次
deploy 选错档，而漏档会合成「新建整套 VPC 并替换 worker 安全组」这类危险变更集（实际发生过）。
四种比对结果与各自的放行动作见 [`docs/user-guide/cloud-backend.md`](../docs/user-guide/cloud-backend.md)「VPC 三档」；
比对实现与状态常量在 `deploy_aws/gherkai_deploy_aws/cli.py`（`classify_vpc_state`），contributor 侧说明见
[`deploy_aws/DEVELOPMENT.md`](../deploy_aws/DEVELOPMENT.md)。

`--refresh-context` 丢弃本机缓存的 CDK 环境查询结果（VPC/子网/AZ）并重新查询；缓存位置与首次查询时的 CDK 警告见
同一页。

## 相关 ADR

- [0016](../docs/adr/0016-execution-architecture-core-lib-run-model.md) 执行架构 / 组合根注入 / `runtime` 抽包
- [0024](../docs/adr/0024-worker-core-protocol.md) worker↔core 协议（render 消费的事件）
- [0027](../docs/adr/0027-runreport-aggregation-index.md) RunReport 归集索引 / [0030](../docs/adr/0030-realtime-persistence-seam.md) 实时写接缝
- [0033](../docs/adr/0033-iac-aws-backend-and-composition-wiring.md) 云端资源清单与命名契约（`destroy` 后表/桶/ECR 是 RETAIN）
- [0034](../docs/adr/0034-detached-batch-reconciler.md) 无状态批量运行（submit/status、job timeout 两层声明与三路 enforce）
- [0035](../docs/adr/0035-local-app-testing-via-tunnel.md) `--expose-local` 隧道（凭据轮换、谁负责拆、TTL 算法）
- [0036](../docs/adr/0036-deterministic-capability-discovery.md) 确定性能力自述（`list-deterministic`、plan 标注）
- [0037](../docs/adr/0037-distribution-and-packaging.md) 分发与打包（三名分离 / worker 定位链 / `steps/` 约定 / deploy 进 wheel / 版本 skew）
- [0038](../docs/adr/0038-worker-image-delivery.md) worker 镜像交付（variant → 显式 task-def revision、被拒方案）
- [0042](../docs/adr/0042-step-evidence-and-explain.md) step 级机读证据与 `explain`（证据 schema、文本预算、只用 0/2 的退出码）
- [0043](../docs/adr/0043-agent-skill-for-driving-gherkai.md) agent skill（包内源文件随 wheel 发行、`skill install` 整目录收敛、契约页确定性转换副本、护栏与评测）
