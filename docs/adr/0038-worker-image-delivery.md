# 0038. worker 镜像交付：基底、variant 与推送注册

> **Status:** Accepted（2026-09-09）—— 命令族（`push-worker` / `list-workers`；`delete-worker` 退 2 占位、留重议闸门）、`gherkai deploy` 四步、运行时显式 revision（`RunMeta.worker_task_defs` + STATE 顶层 `worker_task_def_arns`）、preflight variant 解析、runs 表 status GSI 与推进器 SSM 读、`tools/build_push_workers.py` 退役全部实装；**实测项 1–7 清零**（真账户：两引擎 base/自定义 variant 跑通、幂等/孤儿复用/并发 push、静默期回收与在跑 run 拦截、重推期间在跑 run 仍用旧 revision、兼容路径、升级演练；多平台镜像缺口定为已知边界、不补校验）。基底镜像随 [0037](./0037-distribution-and-packaging.md) 的 v1.4.0 首发进 GHCR，`gherkai deploy` 基底同步在真账户走通。[0033](./0033-iac-aws-backend-and-composition-wiring.md) 的镜像/task-def/ECR/权限表述已加历史注与权限登记。

## 背景与问题

[0037](./0037-distribution-and-packaging.md) 决策 5 定了 worker 镜像**两层分工**：维护者按版本发基底到 GHCR，使用方在本地叠自己的确定性 step 构建定制镜像。本 ADR 定**最后一层怎么交付到云端后端并被 run 使用**。

**当前（施工前）**：每个引擎一个镜像；部署方用 `tools/build_push_workers.py` 从整个 repo 构建、推自己私有 ECR 的 `{prefix}{engine}-worker:latest`；task-def 由 IaC 建、镜像栏焊死 `tag="latest"`；RunTask 只传 task-def 的 **family 名**（ECS 取该 family 最新 ACTIVE revision）；CLI 完全不知道也不能选跑哪个镜像；「更新 steps」= 改 repo 里的脚手架文件、整体重建、重推 `latest`，下次起 task 自然拉到。使用方 build 时必须带 `--platform linux/amd64`，漏给的后果是 Fargate **启动期** `exec format error`（[0033](./0033-iac-aws-backend-and-composition-wiring.md) 记的坑）。

**要解的问题**：
- **多套 step 集并存**：不同开发者/分支在同一个共享后端上各跑各的确定性 step 集而互不覆盖；跑时可选。单 tag cover 不了。
- **版本噩梦**：同一个 tag 名在不同人嘴里指不同内容。要让「用的是哪份」可见、可查、run 内一致。
- **所有权**：改共享后端用的镜像是一次部署变更，应归部署方；镜像**构建**是 developer 自己的容器工作，gherkai 不该拥有。默认画像 = developer 兼测试开发与部署方两角（同一台机器 build 完就推）；团队拆角色时权限边界要现成。
- **架构错误提前暴露**：`--platform` 漏给的错误不该拖到 Fargate 启动期才炸，应在推送前 fail-loud。**不支持 ARM64**（被拒方案，理由见下）。

**AWS 事实（决定形状，均已对照官方文档）**：RunTask 的容器 override 字段全集是 command / environment / environmentFiles / cpu / memory / memoryReservation / resourceRequirements / name，**不能换镜像**；镜像与 `runtimePlatform` 都写在 task-def **revision** 里，revision 是不可变快照、无继承；RunTask 可传 `family`（最新 ACTIVE）或 `family:N`（精确）；task-def 镜像栏支持 `repo@sha256:<digest>`；`DeregisterTaskDefinition` 把 revision 置 INACTIVE——**不影响在跑的 task，但不能再用它起新 task，且注销后最多 10 分钟内这条限制可能尚未生效**；`DeleteTaskDefinitions` 永久删除 INACTIVE revision（有关联 task 时先 DELETE_IN_PROGRESS）；task-def 类 IAM 动作（Register / List / Describe）**不支持资源级权限，只能 `Resource: "*"`**；ECR 仓库 tag 可变性默认 MUTABLE；Fargate ARM64 的不可用面**按 AZ**（官方明列 us-east-1 的 `use1-az3`）。

## 概念模型

| 概念 | 定义 | 载体 |
|---|---|---|
| **基底** | 维护者 CI 发布的镜像 `ghcr.io/zhiyanliu/gherkai-worker-<engine>:X.Y.Z`，linux/amd64 单架构，零使用方内容（[0037](./0037-distribution-and-packaging.md) 决策 5） | GHCR |
| **variant** | 一套具名的确定性 step 集 = 一个定制镜像；名字由开发者自取（`login`、`checkout-v2`）；基底同步进 ECR 的那份固定叫 `base` | 使用方私有 ECR，tag = `<CLI 版本>-<variant>` |
| **默认指针** | 提交时不给 `--worker-variant` 就用哪个 variant；部署级一个；deploy 初始化为 `base` | SSM |
| **revision** | 每个（引擎，variant）一个 task-def revision：从模板复制、镜像栏换成 `repo@sha256:<digest>`、以 tags 记血缘与退休时刻 | ECS task-def family `{prefix}{engine}-worker` |
| **模板 revision**（revision 的母本） | deploy 时 CDK 建出的那个 revision，承载 cpu / memory / task role / execution role / 日志组 / `runtimePlatform`（X86_64）等只有部署后才存在或全局固定的值；**镜像栏保留 `tag="latest"` 作占位**（CDK 必填；该 tag 在 ECR 里可以不存在）——它**永不被 RunTask**、只作复制母本；definition 缺字段时的兼容回落走默认指针（见「运行时与 preflight」节） | ECS；其 ARN 由 stack 资源写进 SSM |
| **架构** | 固定 linux/amd64；push-worker 推送前 `inspect` 校验，不匹配退 2 | 模板 revision 的 `runtimePlatform`，variant revision 原样复制 |

**tag 命名 = 单一真源、同时是单一校验点**：`gherkai_runtime.names.image_tag(version, variant)` → `<归一化版本>-<variant>`。PEP 440 的 `+`（本地段）与 `!`（epoch）不在 docker/ECR tag 字符集 `[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}` 内（`1.4.0.post3.dev0+28c1684` 直接 `docker tag` 报 `invalid reference format`，实测），函数把 `+`/`!` → `.`、返回前按正则校验、不匹配即抛。同处新增 `names.ecr_repo_name(prefix, engine)`（= `task_def_name`），收拢曾散在 `stack.py` 注释与（已退役的）`tools/build_push_workers.py` 内联副本里的「ECR repo 名复用 task-def family 名」规则。

**tag 可变，replace 与否交给使用方**：重推同名 variant 直接放行、只在推送后打印「原 digest → 新 digest」。不设不可变仓库——bugfix 不想改 variant 名是正当需求，机制给到、用错不算产品欠缺。run 内一致性不靠 tag 靠 revision（下）。**护栏**：这条正确性依赖 ECR 保留被顶掉 tag 的 untagged 镜像（在跑 run 的旧 revision 按 digest 指着它），故 ECR 仓库**不设 untagged 过期的 lifecycle 规则**；代价是每次重推永久留一层 untagged 存储、随重推次数增长——记为已知运行期成本，回收与 `delete-worker` 同批设计（重议闸门）。

**定制镜像模板（唯一真源，[0037](./0037-distribution-and-packaging.md) 只指向此处）**：developer 自己 build，任何本地名字，gherkai 不拥有构建；**必须 `--platform linux/amd64`**（arm Mac 上尤其）：

```dockerfile
FROM ghcr.io/zhiyanliu/gherkai-worker-novaact:1.4.0
COPY steps/ /app/steps
ENV GHERKAI_STEPS_DIR=/app/steps
```

```
docker build --platform linux/amd64 -t acme-novaact:login .
```

## 命令族（全在 `gherkai-deploy-aws`，云端写操作归部署方）

- **`gherkai deploy push-worker <本地镜像> --engine <novaact|midscene> --variant <名> [--set-default]`**：推送一个本地镜像并注册为该引擎的一个 variant。一次一个引擎，两个引擎跑两次（两引擎镜像本就分别 build）。
- **`gherkai deploy list-workers`**：按 family 列 revision 并读 tags 与 SSM，输出各引擎当前版本的 variant、digest、推送时间、默认指针，以及已退休待清理与孤儿 revision。
- **`gherkai deploy delete-worker`**：留口子，落地时套同一套清理 pass 语义（退休 tag + 静默期 + 在跑 run 安全阀，见「不变量」）。
- **`gherkai deploy` 的 worker 镜像四步**：登记模板（随 cdk 事务）、同步基底为 `base`、初始化默认指针、重派生既有 variant（后三步在 cdk 之后）。
- **`push-worker` 与 `list-workers` 的前置**：先读 SSM `version` 戳与自身版本比对，**原样沿用** [0037](./0037-distribution-and-packaging.md) 决策 7 的三态——CLI **新于**后端 → 退 2 并指向「先 `gherkai deploy`，或用与后端同版本的 CLI（`uvx --from 'gherkai[deploy-aws]==X.Y.Z' gherkai deploy …`）」；CLI **旧于**后端 → 警告不拦；戳缺失 → 警告不拦；非纯净版本跳过；决策 7 不设放行口，此处同样没有。否则 CLI 跑在后端前面的人会把镜像静默推进一个没人解析的版本命名空间，而提交者的 preflight 提示又把他推回同一步、形成死循环。**`gherkai deploy` 的四步不做此前置**——deploy 本身就是改戳的动作（第 1 步随 cdk 事务写入新戳），前置在 cdk 前会把自己拦死、在 cdk 后恒真。
- **定制镜像的构建不在命令族里**：模板见上。

## `push-worker` 流程

1. **解析目标**：ECR repo = `names.ecr_repo_name(prefix, engine)`、tag = `names.image_tag(CLI 版本, variant)`；region/prefix 与 `gherkai deploy` 同一解析链；版本 skew 前置（上）。
2. **容器引擎 `inspect` 本地镜像**：取**存在**与**架构**；架构 ≠ linux/amd64 → 退 2，提示 `docker build --platform linux/amd64`——把 [0033](./0033-iac-aws-backend-and-composition-wiring.md) 记的启动期 `exec format error` 提前到推送前；本校验在**任何 ECR/ECS 调用之前**（步 1 的 skew 前置那一次 SSM 读除外）。**多平台本地镜像的缺口**：`docker image inspect` 把多平台镜像塌成本机平台的单视图——arm Mac 上得到 arm64、被拒；amd64 主机上「含 amd64 的多平台镜像」会通过（实测项 7）。**此时不取 digest**——本地 build 出来、没推过的镜像没有 registry digest，`inspect` 的 `RepoDigests` 为空，而 `.Id` 是 config digest、**不是** `repo@sha256:` 需要的 manifest digest（拿它注册 ECS 只校格式、RunTask 拉镜像时才 `manifest unknown`）。
3. **ECR 登录**：boto3 `ecr:GetAuthorizationToken` → 引擎 `login`。
4. **推送**：引擎 `tag` + `push`；**digest 的唯一来源 = 推送后对目标 ref 再 `inspect`，取 `RepoDigests` 中匹配本 ECR repo 的那一条**（基底同步路径先 `pull` 过 GHCR，`RepoDigests` 会有多条，不得取第一条）。目标 tag 若原已存在，此时打印「原 digest → 新 digest」。
5. **查重**：SSM 现映射的（模板 revision ARN、digest）二元组与本次一致 → 跳过注册；否则按血缘 tags 在 family 里找**本 variant** 同二元组的 ACTIVE 且未退休的 revision 复用（覆盖「上次中断在注册与写 SSM 之间」的孤儿）；找不到才注册。**限定同 variant**（真账户跑出来的坑）：variant B 的镜像 digest 恰与 A 相同时若复用 A 正在用的 revision，之后 A 换 digest 重推会把它退休、满静默期清掉，B 的映射悬空——每个 variant 自己一个 revision（ECR 层共享，只多一条 task-def），退休与清理才能按 variant 独立判。
6. **注册 revision**：`DescribeTaskDefinition`（模板，`include=["TAGS"]`）→ 剔除只读字段（`taskDefinitionArn` / `revision` / `status` / `requiresAttributes` / `compatibilities` / `registeredAt` / `registeredBy`）→ 镜像栏改 `repo@sha256:<digest>`，其余（含 `runtimePlatform`）原样 → `RegisterTaskDefinition`，**tags 记血缘**：`gherkai:variant`、`gherkai:version`、`gherkai:digest`、`gherkai:template`（模板 ARN）。
7. **写 SSM**：`worker-image/<engine>/<版本>-<variant>` = JSON（模板 revision ARN、revision ARN、digest、推送时间）；`--set-default` 时写默认指针，若该 variant 在其它引擎尚无镜像则**警告不拦**（「variant `X` 在 midscene 尚无镜像，用到该引擎的 run 会在 preflight 被拦」——与 preflight「按本 run 用到的引擎判」同一判据，单引擎团队不必凭空推另一引擎）。
8. **退休被替换的旧 revision**：给它打 tag `gherkai:retired-at=<时刻>`（**不在本次删除**），然后跑一次清理 pass（不变量）。输出 tag / digest / revision，以及「提交时用 `--worker-variant <名>`」。实装次序细节：`--set-default` 落在与基底同步共享的推送路径之外，实际 = 写映射 → 退休旧 revision → 写指针 → 清理（两者无依赖）；registry host 取 `ecr:GetAuthorizationToken` 的 `proxyEndpoint`（权威、与 moto 同形），不另调 STS。

## `gherkai deploy` 的 worker 镜像四步（第 1 步随 cdk 事务，后三步在 cdk 之后；全部幂等）

1. **登记模板**：各引擎 task-def revision 的 ARN 由 **stack 资源**（`ssm.StringParameter`，值取 CDK 内 `taskDefinition.taskDefinitionArn`——`AWS::ECS::TaskDefinition` 的 `Ref` 返回带 revision 的 ARN；CDK 更新 task-def 属性即替换出新 revision、参数值随之更新）写进 SSM `worker-template/<engine>`——与 0037 的 `version`/`vpc` 同理，随部署事务同生死、回滚不留错值，deploy 命令不事后 `put_parameter`。push-worker 永远从它复制，**不抄「最近一次」revision**——那可能是某个 variant 的、且模板改过后已过期。
2. **同步基底**：经容器引擎从 GHCR `pull` 当前版本基底、走 push-worker 同一条内部流程推成 `<版本>-base`、注册 revision。零 step 的团队部署完即可跑，不碰 docker build。**非纯发行版本（`.dev`/`.post`/本地段）跳过本步**并打明确警告——那些版本由 tag 之后的 commit 派生、GHCR 上不可能有对应基底（0037 决策 2b）；contributor 在 dev 树上部署是正常用法，硬失败只会逼人绕过命令手工推。第 3/4 步照常（默认指针仍初始化为 `base`；dev 版要能跑：本地 build 后 `push-worker … --variant base`）。容器引擎也只在本步探活——非纯版本不探，没装 docker 的机器上第 3/4 步照样收敛。
3. **初始化默认指针**：缺失 → `base`；存在 → **不动**（升级不重置，见「与版本升级的交互」）。
4. **重派生 + 清理**：对 SSM 里**当前版本**的每个 variant，若其记录的模板 ARN ≠ 新模板 → 用新模板 + 该 variant 已记录的 digest 重新注册 revision（血缘 tags 同上）、更新映射、旧 revision 打 `gherkai:retired-at`；相同则跳过。原因：revision 是不可变快照、无继承，deploy 调了 cpu 后旧 variant 会一直跑旧 cpu 直到有人重推；重派生让所有 variant 与模板同步而镜像一个字节不动。重派生**保留原 `pushed_at`**（记的是镜像推上去的时刻）；repo URI 从模板容器的镜像栏反推（模板即 `<repo-uri>:latest` 占位）——重派生不登录 registry。随后跑一次清理 pass（不变量）。

**四步的失败语义**：cdk 已成功而后三步任一失败 → 退 1，提示「stack 已生效；重跑 `gherkai deploy` 幂等收敛」；基底 pull 因 GHCR 上缺该版本镜像失败（[0037](./0037-distribution-and-packaging.md) 决策 8 承认的「PyPI 已发、镜像缺失」半发布态）→ 提示等镜像发布完成后再 `gherkai deploy`。

## 不变量

- **运行时只用 definition 里的显式 revision，永不用 family 取最新**。当前代码传 family（取最新 ACTIVE），多 variant 下任何一次 push 都会劫持默认——必须改。
- **revision 按 digest 引用镜像**，重推同名 variant 产生新 revision、在跑的 run 手里的旧 revision 不受影响；一个 run 内镜像固定。
- **幂等**：push-worker 与 deploy 四步的每一步先查再做，中断后重跑收敛。ECR push 天然幂等（同 digest 无操作）；`RegisterTaskDefinition` 不幂等，故以二元组查重、孤儿 revision 按血缘 tags 复用而非重复注册；ECR 登录令牌 12 小时有效、重跑重登；SSM 写是覆盖语义。
- **并发写者：最后写者赢，孤儿由对账回收**。SSM 无条件写，两人同时 push 同名 variant 会各注册一个 revision、后写者的映射赢；先写者的 revision 不在映射里也没被打退休 tag——**清理 pass 按 family 全量对账**（凡带血缘 tags、ACTIVE、不在 SSM **任何版本**的 `worker-image/*` 映射里的 revision 视作孤儿，视同退休、退休时刻取其 `registeredAt`；旧版本 variant 的 revision 仍在映射里、**不是**孤儿，其回收归 `delete-worker`），不只看映射。同一 variant 的并发 push 不建议但不禁止。
- **清理 pass = 静默期 + 在跑 run 安全阀，机会式执行、无定时任务**：pass 由 `push-worker` 末步与 `gherkai deploy` 第四步末各跑一次（将来 `delete-worker` 也跑）；列 family 全部 revision 读 tags，对已退休（`gherkai:retired-at`）或对账出的孤儿，只在**退休满 1 小时**（覆盖「提交侧 preflight 刚解析成 R、definition 尚未落库」的窗口与注销后最多 10 分钟的生效延迟）且**无未到终态的 run 引用**时才 `DeregisterTaskDefinition` + `DeleteTaskDefinitions`；有引用或未满静默期 → 留到下次 pass。长期无人 push/deploy 时退休 revision 会滞留，无害（ACTIVE 但无人引用）。引用判定的访问路径定死：run 用到的 revision ARN 在 `create_run` 时**同时写成 STATE item 的顶层属性 `worker_task_def_arns`**（同 [0034](./0034-detached-batch-reconciler.md) 的 `detached` 顶层标记先例），runs 表加一个按 `status` 的稀疏 GSI（只索引 STATE item），清理用 `Query` 非终态状态 + `contains` 过滤——不扫全表（runs 表 `RETAIN`、无 TTL、随历史单调增长，Scan 成本无上界）。detached run 逐 job 起 task，删早了剩余 job 全部起不来。ECS 侧稳态只留每个 variant 当前一个 revision。**实装细则**：孤儿判据要枚举 SSM **全部版本**的映射，枚举失败 → **整趟放弃清理**（当作「没有映射」会把每个在用 revision 都判成孤儿，而真实 `registeredAt` 是过去时刻、静默期拦不住 → 批量误删）；`registeredAt` 取不到时按「此刻退休」（本次必然未满静默期，宁滞留不早删）；孤儿复用不含已退休 revision（退休 = 已判下岗，重注册一个干净的更便宜）。**退休 ≠ 可删**：已打 `retired-at` 但仍被任何版本的某个 `worker-image/*` 映射引用的 revision 不删（历史上曾被另一 variant 共用的状态），直到映射也不再引用——与在跑 run 引用并列为安全阀。**已知盲区**：`run --backend cloud --no-report`（有意的逃生舱）不写 STATE item，其 revision 引用对安全阀不可见——这样一个跑超过 1 小时的 run 期间别重推同名 variant。
- **默认指针不自动重置**（含版本升级）：它记的是团队意图。
- **不判 steps 内容**：镜像里的 steps 是否最新由使用方管理；preflight 不比对镜像内 steps 与本地 steps——越权替使用方判断，且提交者（feature 作者、CI 机器）手头未必有 steps 目录、会被误拦。想区分就换 variant 名。

## 运行时与 preflight

- **选择进 definition**：`run/submit --backend cloud [--worker-variant <名>]`，缺省取默认指针；CLI 在 preflight 把 variant 解析成各引擎的 revision ARN，写进 definition——`RunMeta.worker_variant`（人读）与 `RunMeta.worker_task_defs`（引擎 → revision ARN），omit-when-None、local 档不写，沿用 `max_concurrency`/`extra_http_headers` 随 definition 走的惯例（[0034](./0034-detached-batch-reconciler.md)/[0035](./0035-local-app-testing-via-tunnel.md)）；同一批 ARN 同时写成 STATE 顶层属性（清理安全阀用）。云端推进器（kicker / reconciler）与同步 `run` 的 `FargateEngine` 一律照 definition 起 task。local 跑法忽略该 flag（直接读 steps 目录）。
- **读侧兼容口径**：definition 里**没有** `worker_task_defs` 的 run 有两个来源——引入本 ADR 的那次升级前提交、升级窗口内仍在跑的 run（deploy 换了推进器代码），以及旧 CLI 提交到新后端的 run（[0037](./0037-distribution-and-packaging.md) 决策 7「CLI 旧于后端 → 警告不拦」允许）→ 推进器在起 task 时读 SSM `worker-default` 与对应 `worker-image/<engine>/<后端版本>-<默认 variant>`，**按后端当前默认指针解析 revision**（推进器因此新增 SSM 读权限），并在日志点名走了兼容路径；**不**回落 family 最新 ACTIVE（那可能是别人的 variant，等于让在跑的 run 中途换 step 集），**也不**用模板 revision（其 `latest` 占位在从未推过 `latest` 的全新 prefix 上根本拉不到镜像，会拖到 Fargate 启动期才炸）。代价明示：引入本 ADR 的**那一次**升级里，在跑 run 的剩余 job 会从升级前的 `latest` 镜像换到新版本默认 variant（通常是 `base`，无使用方 steps）——一次性迁移事项，升级前先让在跑 run 收敛即可规避；此后所有 definition 都带字段，不再发生。 **实装注**：stack **不**把模板 ARN 注进推进器 env（0037 批次曾短暂注入 `WORKER_TEMPLATE_ARNS`，随本 ADR 实装撤除——宿主按被拒方案不得回落模板，留着只会诱人用）；推进器（reconciler/kicker 共用同一 `_build`）缺字段时经 `compose.resolve_default_worker_task_defs` 走默认指针、日志一行 `worker-compat:` 点名 variant/版本/引擎；**解析不出的 run 只跳过它自己**（`_tick_runs` 逐 run 隔离——events Stream 一个 batch 含多个 run，抛出去会让 ESM 重试后整批丢弃、别的 run 事件永久丢失；「默认 variant 在某引擎无映射」是 `--set-default` 只警告不拦下的合法稳态，不算罕见）。
- **preflight 只做存在性与一致性，不判内容**，位置在既有 preflight（表/桶/cluster/task-def/三 Lambda）与**版本 skew（[0037](./0037-distribution-and-packaging.md) 决策 7）之后**——skew 的修复动作（deploy）是镜像重推的前置，反过来会让用户白推一轮。对**本 run 用到的每个引擎**（对齐既有 task-def 判据「不探全注册表——没用到的引擎不该拦」）：请求的 variant 在 SSM 有**当前版本**（= 提交方 CLI 自身版本，与 push-worker 打 tag 用的同一个）的映射、revision ACTIVE、ECR 镜像（按 digest `describe-images`）存在——任一缺 → 退 2，**不回落默认**（回落是静默行为）；提示语按 skew 分叉：CLI 与后端同版本 → 「`gherkai deploy push-worker … --variant <名>`」；CLI 旧于后端（决策 7 只警告不拦的那一档）→ 「升级 CLI 到后端版本」，不引导去推一个旧版本 tag 的镜像；通过则打印各引擎解析到的 variant / digest。
- **一个 run 一个 variant 名**，跨引擎同名；某引擎缺该 variant 即上条的退 2。

## 多版本与多环境

**一个部署（一个 prefix）在任一时刻只有一个后端版本**：Lambda 代码、模板 revision、SSM 版本戳都是单份，本 ADR 与 0037 的版本单旋钮都建立在这个前提上；不做同一 prefix 内的双版本并行。variant 按版本隔离只是历史保留，不是旧版本在运行。**要多个版本并存（多人/多团队各用各的），用不同 prefix 部署成不同环境**——prefix 本就是全部云资源的命名空间（[0033](./0033-iac-aws-backend-and-composition-wiring.md)），CLI 经 `--prefix` 显式选择连哪个环境，这是现有机制、无新增设计；闲置成本近零（[0034](./0034-detached-batch-reconciler.md) 的事件驱动、无常驻），只多一份 ECR 存储。local 跑法无后端、无此问题：CLI 升级即全部升级（worker 经 `[local]` 装在同一 venv）。

## SSM 参数与命名真源

| 参数（前缀 `/{prefix}backend/`） | 值 | 写者 |
|---|---|---|
| `worker-template/<engine>` | 模板 revision ARN | stack 资源（随 `gherkai deploy` 事务） |
| `worker-image/<engine>/<版本>-<variant>` | JSON：模板 revision ARN、revision ARN、digest、推送时间 | `push-worker`（含 deploy 的基底同步与重派生） |
| `worker-default` | 默认 variant 名（部署级一个） | deploy 初始化、`push-worker --set-default` |

退休时刻与血缘**不进 SSM**、以 task-def 的 tags 承载（`gherkai:variant` / `version` / `digest` / `template` / `retired-at`）——与 revision 同生死、不撑 SSM 标准参数 4KB 上限、清理对账只看一处。`version`、`vpc` 两个参数归 [0037](./0037-distribution-and-packaging.md)。全部落在 [0033](./0033-iac-aws-backend-and-composition-wiring.md) 已授的 `/{prefix}backend/*` 通配内。枚举用 `GetParametersByPath`（`Recursive=true`，单页最多 10 条须翻页）。variant **按版本隔离**：键含版本，旧版本的 variant 留在 ECR 与 SSM 作历史、不参与当前版本解析，`delete-worker` 落地后可清。

## 权限面增量

[0033](./0033-iac-aws-backend-and-composition-wiring.md)「资源清单」末段是编排机器权限的单一登记处，随本 ADR 落地去那里改，此处只列增量；**资源域按 0033「结构上只能 `*` 的动作诚实保留、单开 statement」的纪律标注**：

- **部署方**：ECR repo 域动作 `ecr:BatchCheckLayerAvailability` / `InitiateLayerUpload` / `UploadLayerPart` / `CompleteLayerUpload` / `PutImage` + **`ecr:DescribeImages`**（推送前读旧 digest 以打印「原 → 新」；限两个 `{prefix}{engine}-worker` repo ARN）；**只能 `*`** 的 `ecr:GetAuthorizationToken`（其 `proxyEndpoint` 即 registry host，**不需要** `sts:GetCallerIdentity`）、`ecs:RegisterTaskDefinition` / `ListTaskDefinitions` / `DescribeTaskDefinition`（task-def 类动作官方明文不支持资源级权限）、`ecs:TagResource`（注册时打血缘 tag、退休时打 `retired-at`）；`ecs:DeregisterTaskDefinition` / `DeleteTaskDefinitions` 按 SAR 的 resource types 逐条核后再定能否收窄；`iam:PassRole`（task / execution role，RegisterTaskDefinition 需要）；SSM `GetParameter`（点读模板/映射/默认指针）+ `PutParameter` + `GetParametersByPath`（`/{prefix}backend/*`）；runs 表 `dynamodb:Query` 供清理安全阀——**资源须含索引 ARN** `table/{prefix}runs/index/status-index`（只给表 ARN 查不了 GSI）。
- **提交者**：只读 `ecr:DescribeImages`（repo 域）、`ecs:DescribeTaskDefinition`（只能 `*`）；SSM 读落在已授通配内。
- **云端推进器**：`ecs:RunTask` 资源域须覆盖 family 全部 revision——当前 IaC 已按 `task-definition/{family}:*` 授权（reconciler 与 kicker 同源），**无增量**；新增 SSM `GetParameter` + `GetParametersByPath`（`/{prefix}backend/*`）供兼容回落读默认指针与映射（stack 已授，exit-observer 不授）。
- **写 step 的人不需要任何 AWS 写权限**（不推送时）：这是构建与推送解耦的直接收益。

## 容器引擎口子

只需五个动词：`inspect`（存在、架构；推送后再取 digest）、`tag`、`login`、`push`、`pull`。默认 docker，`--container-engine podman` / env `GHERKAI_CONTAINER_ENGINE` 切换（podman 同形子命令），这期只实现 docker。repo 内碰 docker 的只有 `gherkai_deploy_aws/container.py`（push-worker 与 deploy 的基底同步经它；密码只走 `--password-stdin`）与两个 Dockerfile，CLI / runtime / CDK 都不碰它。`--container-engine` 在 `deploy` 与 `push-worker` 上都收（deploy 的第 2 步也要它）；两类失败分开归码——名字不认 → 退 2（本地参数问题，先于 VPC 档比对）；装了但不可用 → cdk 前只警告、cdk 后退 1「stack 已生效、重跑幂等收敛」。**这一期 deploy 机器需要容器引擎**（同步基底要 pull / push；非纯发行版本跳过该步、不探活）；免容器引擎的 registry 直拷是重议闸门里的加法。

## 与版本升级的交互

[0037](./0037-distribution-and-packaging.md) 决策 7 的「升级即三步」中，本 ADR 负责第 ②③ 步的镜像半边：②`gherkai deploy` 同步新版本 `base`、登记新模板、对新版本已有的 variant 重派生（升级当下通常没有）；③团队有自定义 variant 或自定义默认的，从新版本基底重新 build 各引擎镜像、`push-worker` 推上去。**默认指针不重置**：它记的是 variant 名（如 `common`），新版本 `1.5.0-common` 未推之前 preflight 退 2、提示「默认 variant `common` 在 1.5.0 尚无镜像：`push-worker … --variant common`，或临时 `--worker-variant base`」；推上去即恢复，不必再 `--set-default`。升级窗口内**在跑的旧 run** 按「读侧兼容口径」处理（只在引入本 ADR 的那一次升级里会换到默认 variant，之后的升级不受影响）。

## 对既有 ADR 的影响

- **[0033](./0033-iac-aws-backend-and-composition-wiring.md)（Partially-superseded-by 本 ADR，与 0037 并列、各自独立翻牌）**：task-def 焊死 `tag="latest"` 且 RunTask 传 family → 每（引擎，variant）一个 digest 引用的 revision、RunTask 传显式 revision（模板 revision 保留 `latest` 占位、不再被正常 RunTask）；「必须 `--platform linux/amd64`」陷阱**保留**，但 push-worker 推送前校验架构、把失败从 Fargate 启动期提前到推送前；`tools/build_push_workers.py` → `gherkai deploy push-worker`；runs 表 STATE item 加顶层属性 `worker_task_def_arns` + 按 `status` 的稀疏 GSI；SSM 参数族加三类（`worker-template/<engine>`、`worker-image/<engine>/<tag>`、`worker-default`）；推进器 Lambda 加 SSM 读权限（兼容回落）；「资源清单」末段的编排机器权限清单按上「权限面增量」更新；preflight 加 variant 解析一项。ECR repo 命名（`{prefix}{engine}-worker`、`RETAIN`）、container 名契约、cluster/task-def family 名、`_worker_subnet_ids` 不动。
- **[0034](./0034-detached-batch-reconciler.md)（扩展、Status 不动）**：definition 加 `worker_variant` / `worker_task_defs`（沿用其「随 definition 走、宿主只读回」惯例），STATE 顶层加 `worker_task_def_arns`（沿用其 `detached` 顶层标记先例）；kicker/reconciler 的 CloudLauncher 起 task 改用 definition 里的 revision，缺失时按后端默认指针解析兼容。
- **[0016](./0016-execution-architecture-core-lib-run-model.md)（扩展、Status 不动）**：其「数据模型」节 definition 行的 run 级字段枚举（已逐字段带 ADR 指针）落地时补 `worker_variant` / `worker_task_defs` → 本 ADR。
- **[0037](./0037-distribution-and-packaging.md)**：其决策 5 只定两层分工与基底通道，机制、模板、被拒方案全部在本 ADR；两者 Status 独立翻牌。
- **[0032](./0032-fargate-execution-environment.md)**：grace / `stopTimeout` 等执行面韧性不动；模板 revision 携带它们、variant revision 复制它们。

## 对既有文档与 code 的影响（校准清单，Draft→Accepted 门槛的一部分）

- `deploy_aws/README.md`（收编前的 `iac_aws_backend/README.md`）的 `build_push_workers.py` 步骤、`latest` tag 描述 → 改为 push-worker 流程；`--platform` 注意事项保留、补「push-worker 会提前拦」。（**已完成**）
- `engines/*/Dockerfile` 的 `--platform linux/amd64` 注释 → 保留，补指向本 ADR。（**已完成**）
- `CONTEXT.md` 的「worker 镜像：基底 / variant / 默认指针」词条的「设计已定、施工未启」标记 → 去掉。（**已完成**）
- `tools/build_push_workers.py` 退役（其 ECR 登录序与命名规则收进 push-worker 与 `names.ecr_repo_name`）。（**已完成**）

## 落地次序与依赖（依赖关系，非进度追踪）

1. `names.image_tag` / `names.ecr_repo_name`（依赖 0037 的 runtime 包化）；`RunMeta.worker_variant` / `worker_task_defs` + STATE 顶层 `worker_task_def_arns` + `FargateEngine` / `CloudLauncher` 改显式 revision、缺失按默认指针解析（可在 0037 之前先落：把当前 IaC 建的唯一 revision 当作解析结果，行为不变）。
2. IaC：stack 写 `worker-template/<engine>` 参数、推进器 SSM 读权限、runs 表 status GSI。
3. `gherkai-deploy-aws` 内容器引擎口子（docker）、`push-worker`（八步 + 血缘/退休 tags + 清理 pass）、`list-workers`。
4. `gherkai deploy` 的 worker 镜像四步；preflight 的 variant 解析 + 严格退 2 + 打印；权限清单更新（依赖 0037 决策 8 的基底已在 GHCR）。
5. `tools/build_push_workers.py` 退役；`deploy_aws/README.md`、Dockerfile 注释与 CONTEXT 校准。

## 实测项（Draft → Accepted 前必清；「绿≠对」）

1. 使用方按模板 build 后 `push-worker`，自定义 variant 与 `base` 并存、各自跑通两引擎；arm Mac 上不带 `--platform` build 出的镜像被步 2 拒绝并给出提示；`--worker-variant` 对某引擎缺失时严格退 2；`--set-default` 在另一引擎缺失时只警告。（**真账户已验**（独立 prefix、dev 版本、本地态基底镜像作 `base`）：两引擎 `push-worker … --variant base` 真推 ECR → 推后取 digest → 注册 revision（`:2`）→ 写 SSM；`--worker-variant nope` 退 2 并给 push 提示；`--set-default probe2` 只警告 midscene 缺映射，随后不带 flag 的双引擎 submit 在 preflight 被 midscene 缺映射拦下退 2；恢复 `base` 后双引擎 run passed。**发行版基底亦已验**：v1.4.0 首发后用 `uvx gherkai==1.4.0` 提交双引擎 run，两 task 分别用 GHCR 同步来的 `1.4.0-base` revision（ECR 镜像 digest 与 GHCR manifest digest 逐字相同：midscene `sha256:8070fd…`、novaact `sha256:704aa0…`），exit 0、run passed。**自定义 variant 携带真实使用方 step 亦已验**（v1.4.0 发行版）：使用方项目 `steps/title_check.py` + `steps/title-check.mts` 注册同一条 `页面标题包含 "…"` 锚点，按三行模板 `FROM ghcr.io/…:1.4.0` + `COPY steps/` + `ENV GHERKAI_STEPS_DIR` 各 build 一个镜像、`push-worker --variant custom` ×2，`submit --worker-variant custom` 的三 scope run：novaact 与 midscene 正例各 passed、novaact 故意错的标题断言 **failed**（证明走的是确定性 handler 而非 AI 兜底），三个 task 用的正是 custom 的 revision、worker 均 exit 0。**待验**：arm Mac 真 build 的镜像被拒（本机真 docker 已用 arm64 镜像验过判据）。）
2. push-worker 幂等：在推送与注册之间、注册与写 SSM 之间人为中断后重跑收敛，孤儿 revision 按血缘 tags 被复用而非重复注册；两个终端并发 push 同名 variant 后 `list-workers` 标出孤儿、静默期后清理回收。（**真账户部分已验**：同镜像重推 → 「映射已是（当前模板，本 digest）→ 跳过注册」；同名 variant 换 digest 重推 → 打印「原 → 新 digest」、旧 revision 打 `retired-at`、`list-workers` 列为待清理；与 `base` 同 digest 的新 variant 注册自己的 revision、不复用 `base` 的（此处真跑抓出并修掉「跨 variant 复用」）；**中断重跑**（按血缘 tags 手工注册一个 variant 的 revision、不写 SSM 以模拟中断在注册与写 SSM 之间 → 重跑 push-worker 复用它、不重复注册）；**并发 push 同名 variant**（两进程不同 digest 同时推 → 各注册一个 revision、后写者映射赢，`list-workers` 把先写者标为孤儿）。**静默期回收已验**：退休满 1 小时的 revision 在下一次 push-worker 末尾被回收，同趟未满 1 小时的留着（见下 3）。）
3. 清理 pass：有在跑的 detached run 引用时被拦下、run 结束且静默期满后下次 pass 成功；「preflight 刚解析完立即 submit」的对抗用例不被清理打断；deploy 改 cpu 后重派生使既有 variant 的 revision 更新且旧 revision 被打 `retired-at`。（**真账户已验**：`gherkai deploy --stop-timeout 100` 只改模板 → 六个（引擎，variant）全部重派生到新 revision（继承 `stopTimeout=100`、镜像仍按原 digest、`pushed_at` 保留）、旧 revision 打 `retired-at`、默认指针不动；**静默期回收**：退休满 1 小时后的下一次 push-worker 末尾清理 pass 真回收了该 revision（`DeregisterTaskDefinition` + `DeleteTaskDefinitions`，AWS 侧随即 `DELETE_IN_PROGRESS`），同一趟里未满 1 小时的退休/孤儿 revision 全部留着。**在跑 run 拦截已验**：把一个已退休 3 小时的 revision 交给一条非终态 STATE（`worker_task_def_arns` 含它）引用，清理 pass 留下它（ECS 仍 ACTIVE）；把该 run 置终态后下一趟回收（`DELETE_IN_PROGRESS`）——GSI Query + `contains` 的安全阀在真 DynamoDB/ECS 上成立。「preflight 刚解析完立即 submit」的窗口由 1 小时静默期覆盖，未另做对抗。）
4. 重推同名 variant 期间在跑 run 的后续 job 仍用旧 revision；升级窗口内无 `worker_task_defs` 的旧 run 走默认指针兼容路径跑完（含全新 prefix 上旧 CLI 提交的 run）。（**真账户已验**兼容路径：手工写入一个**无** `worker_task_defs` 的旧形态 definition → kicker 日志 `worker-compat: … 按后端默认指针解析 variant='base'`、task 用默认指针当时的 revision、run passed。**重推期间在跑 run 的后续 job 仍用旧 revision已验**：3 个 scope `--max-concurrency 1` 串行 run 跑到第一段时重推同名 variant（digest 换、旧 revision 打退休 tag、新 revision 注册），随后的第二、第三段 task 仍用旧 revision（definition 钉死），run passed。）
5. 升级演练：CLI 升版后 deploy → 默认指针悬空的 preflight 提示 → push 同名 variant 后恢复，不需 `--set-default`；CLI 版本超前于后端时 push-worker 被 skew 前置拦下。（**真账户已验**（跳板机克隆打本地 tag 得纯 `1.4.0` CLI + 改写 SSM 版本戳模拟后端版本）：戳 1.3.0 → `list-workers`/`submit` 均 block 退 2、push-worker 侧多给带 `[deploy-aws]` extra 的 uvx 出路；戳 1.5.0 → warn 不拦；戳 1.4.0 → 静默放行、`1.4.0-base` 未推 → submit 退 2 点名 push；push 同名 `base` → submit 解析到新映射、run passed、默认指针未动。**真 `gherkai deploy` 写新版本戳 + 同步 GHCR 基底已验**：用发行版 `uvx --from 'gherkai[deploy-aws]==1.4.0' gherkai deploy` 把验证环境从 dev 版升到 1.4.0——SSM 戳变 `1.4.0`、两引擎从 GHCR 拉 `1.4.0` 基底推成 ECR `1.4.0-base` 并注册 revision、默认指针不动、无需重派生（新版本尚无其它 variant）；随后 `uvx gherkai==1.4.0 submit` 的 run 用新 revision 跑通。）
6. 本地未推送镜像的 `inspect` 确认 `RepoDigests` 为空，推送后取到的 digest 与 ECR `describe-images` 一致、注册的 revision 能被 RunTask 拉起。（**已验**：真 docker——未推送镜像 `RepoDigests` 空、`docker tag` 到 ECR ref 后仍空、arm64 镜像被步 2 拒；真账户——推后取到的 digest 被 `describe-images` 认（preflight 三环通过），kicker 起的 Fargate task 的 `taskDefinitionArn` 正是注册出的 `…-worker:2`（显式 revision、非 family 最新），两引擎 task 各 exit 0、run passed。）
7. 多平台本地镜像在 amd64 主机上被 `inspect` 塌成单平台视图而放行——**定为已知边界、不补 manifest 级校验**。实测：Docker 默认镜像存储（overlay2）**装不下多平台镜像**——`docker buildx build --platform linux/amd64,linux/arm64 --load` 直接报 `docker exporter does not currently support exporting manifest lists`，即缺口只存在于开了 containerd 镜像存储的机器。推演（未真跑 containerd 存储）：amd64 主机上含 amd64 的多平台镜像通过校验后 `docker push` 推的是 index，推后 `RepoDigests` 即 index digest，task-def 按它引用，ECS 从 index 选 amd64——**无安全问题**；arm 主机上 `inspect` 得 arm64 → 被拒（过严但安全，按文档只构 amd64 单平台即可）。
- **无凭证下已验的部分**（其余全待真账户）：真 synth 出的模板含 runs 表 `status-index`（INCLUDE `worker_task_def_arns`）、推进器 SSM 读策略、ECR 无 lifecycle、无模板 env；moto 验了八步幂等（二元组查重、孤儿复用、退休 tag）、清理两道闸（静默期 + GSI Query）、重派生、指针不重置、`--set-default` 只警告、skew 前置；**跨组件真互通**——真 `DdbRunStore.create_run` 写的 STATE 属性被真清理安全阀在真 GSI 形状上读到（含终态即不再引用、META 无顶层 status 的稀疏性），真 push 写的 SSM/ECS/ECR 三件套被提交侧与宿主侧两个 `resolve_*` 原样读回。

## 被拒方案（护栏，防未来重踩）

- **gherkai 拥有定制镜像的构建（曾拟 `build-workers` 命令即时生成 Dockerfile、build、push 一体，且住 CLI 本体）**：镜像构建是 developer 自己的容器工作，gherkai 拥有它就得替所有构建方式与引擎负责；只保留三行模板，云端侧的推送与注册归部署方、归 `gherkai-deploy-aws`。
- **支持 ARM64 / 多架构基底、架构随 variant 走**：Fargate ARM64 的不可用面按 AZ（us-east-1 的 `use1-az3`），要按 ZoneId 排除子网、维护排除表、多架构 buildx、`--base-arch` 旋钮，换来约 20% 的 task 单价；复杂度不值，且使用方 build 仍需注意平台。固定 linux/amd64，push-worker 推送前校验把 `--platform` 漏给的错误提前 fail-loud。锁文件静态核查两侧依赖均有 linux/arm64 产物（Python 侧 playwright 等 18 个平台 wheel、Node 侧 esbuild/sharp），将来要省钱路是通的，见重议闸门。
- **preflight 校验 steps 漂移（steps 目录摘要作第二个 tag 或存 SSM 比对）**：越权替使用方判断内容；提交者手头未必有 steps 目录会被误拦；需要区分就换 variant 名。
- **variant 参数叫 `--tag`**：它只是 ECR tag 的后缀，与镜像 tag 混；`--variant` / `--worker-variant`。
- **push-worker 一次收两个引擎（`novaact=<img> midscene=<img>`）**：参数形式重、两引擎镜像本就分别 build；一次一个引擎、`<本地镜像>` 作唯一位置参数。
- **读基底 LABEL 校验镜像的基底版本**：唯一用途是防「旧基底 build 推成新版本 tag」，去掉后此错误在运行期以 worker 协议错误暴露，与「内容由使用方负责」一致；`inspect` 只用来取存在与架构。
- **推送前用本地 `inspect` 的 image Id 当 digest**：那是 config digest，不是 manifest digest，注册能过、RunTask 才 `manifest unknown`；digest 只在推送后取。
- **不可变 ECR tag（重推同名 variant 须先删）**：bugfix 不想改名是正当需求；replace 交给使用方，run 内一致性由 digest 引用的 revision 保证。
- **默认镜像 = 不带 variant 后缀的裸版本 tag，重推即覆盖**：会把 `base` 从映射里抹掉、退路只能重拉；默认改为指针，所有镜像都有 variant 名。
- **RunTask 传 family（取最新 ACTIVE revision）**：多 variant 下任何一次 push 都会劫持默认；一律显式 revision。缺失字段时也不回落 family，按默认指针解析。
- **缺字段时回落模板 revision（`latest` 占位）**：全新 prefix 从未推过 `latest`，RunTask 拉镜像直接失败、错误拖到 Fargate 启动期；按后端默认指针解析。
- **revision 按 tag 引用镜像**：重推同名 variant 会让在跑 run 的后续 job 换镜像；按 digest 引用。
- **push-worker 抄「最近一次」revision 作模板**：最近一次可能是某个 variant 的、且模板改过后已过期；永远从 deploy 登记的模板 revision 复制。
- **模板 revision ARN 由 deploy 命令事后 `put_parameter`**：回滚留错值；stack 资源随事务。
- **deploy 改模板后不重派生既有 variant**：旧 variant 会一直跑旧 cpu/配置直到有人重推，且无人会想起来；重派生按模板 ARN 判定是否需要、幂等。
- **升级时自动把默认指针重置回 `base`**：抹掉团队意图；不重置，preflight 提示指向 push 或临时 `--worker-variant base`。
- **重派生/重推后立即删旧 revision**：INACTIVE 不能再起新 task（且注销后最多 10 分钟才生效），detached run 逐 job 起 task 会断；先打退休 tag、静默期满且无在跑引用才删。
- **退休名单存 SSM 参数（JSON 列表）**：撑 4KB 标准参数上限（一轮连续推送即可撑爆）、与 revision 分家、对账要看两处；改为 revision 自身的 `gherkai:retired-at` tag。
- **清理靠定时任务**：多一个常驻资源与凭证面；机会式 pass 挂在 push-worker / deploy / delete-worker 上，滞留无害。
- **清理靠全表 Scan runs 表**：runs 表 `RETAIN`、无 TTL、无界增长；改 STATE 顶层属性 + status GSI 的 Query。
- **`--set-default` 硬要求 variant 在每个引擎都存在**：与 preflight「按本 run 用到的引擎判」矛盾，单引擎团队要凭空推另一引擎镜像；改警告。
- **variant 缺失时静默回落默认**：静默换 step 集与「不判内容」矛盾；严格退 2 带提示。
- **push-worker 不校版本 skew**：CLI 超前的人会把镜像推进无人解析的版本命名空间，提交者的提示又把人推回这一步；skew 三态前置。
- **同一 prefix 内双版本后端并行（蓝绿）**：Lambda / 模板 / 版本戳都是单份，版本单旋钮建立在此前提上；多版本用多 prefix。
- **镜像 tag 直接用 PEP 440 版本串**：`+`/`!` 非法；`names.image_tag` 归一化 + 正则校验。
- **task-def 指向 GHCR 直接拉基底、不进 ECR**：运行时依赖 GitHub 可用性、出网流量、匿名拉取限额；基底同步进使用方 ECR，运行时只拉自己账号的。
- **ECR 加 untagged 过期 lifecycle**：会静默删掉在跑 run 的旧 revision 按 digest 指着的镜像；回收与 `delete-worker` 同批设计。

## 重议闸门

- 免容器引擎的基底同步（registry 到 registry 直拷）→ deploy 机器不再需要 docker，零 step 团队零容器工具链；podman 等其它容器引擎经同一口子接入。
- `delete-worker` 落地：套退休 tag + 静默期 + 在跑 run 安全阀；顺带清旧版本 variant 的 ECR tag / untagged 层与 SSM 映射（届时才定 ECR 回收策略）。
- ARM64 / Graviton 省钱需求成真 → 多架构基底 + 按 ZoneId 排除不支持的 AZ + variant 架构属性，方案已知、依赖侧静态核查已过；届时再评估复杂度是否值。
- 出现「一个 run 内不同引擎用不同 variant」的真实需求 → `--worker-variant` 扩成 `engine=name` 形式，是加法。
- Node 端 `module.registerHooks()` / 其它与镜像无关的 worker 运行时演进归 [0037](./0037-distribution-and-packaging.md)。
