# 文档健康度复盘第五轮 — 待批报告

> 类型: 待批报告（过程产物，批毕落改即删）。客观类 78 条 CONFIRMED 已落改（见同批 commit），另 2 条 code 注释另起 commit；本文只列**待人裁决**的主观类：提纯提案（红线复核 approve / approve_reduced 的 40 条）、主观发现 5 条、UNCERTAIN 1 条；末尾附全量具名提纯审计记录（41 份）与已驳回/已否决存档。

## 一、提纯提案待批（40 条；approve_reduced 的请按「复核缩小后的改法」落）

### CONTEXT.md

- **[P15] approve_reduced** · 原句：「区分：**「部署方」**装 `[deploy-aws]` 跑 deploy；**「提交方」**只装 `gherkai` 跑 run/submit，两者靠 SSM 版本戳做 skew 比对（见下「版本单旋钮」）。」
  - 提案改法：整句删掉，或压成一句指针：「部署方 / 提交者 见上『使用方角色』。」——角色定义与权限梯的单一事实源留在「使用方角色」，同时消掉「提交方」这个漂移拼法。
  - 复核缩小：不可整句删：CONTEXT.md:161「部署 provider」词条末句的后半「两者靠 SSM 版本戳做 skew 比对（见下「版本单旋钮」）」正是红线保护的「带指针的有意简短重述」——它在 provider 词条就地交代「为什么两侧版本必须对齐」并把权威指向 line 163「版本单旋钮」词条，删掉即断掉两词条间的桥梁；而「不装 `[deploy-aws]` 的一方只装 `gherkai` 就能跑 run/submit」是读 provider 安装面（extra 分装）的读者就地需要的边界事实，「使用方角色」的「提交者」词条只定义权限类别（「不是帽子，是权限类别…权限登记见 ADR 0033/0038」），并未讲安装面。真正的沉积有两处：①前半「「部署方」装 `[deploy-aws]` 跑 deploy」与同词条上文「经 CLI extra `[deploy-aws]` 装、只有部署方需要」零距离重复；②「提交方」是正名前…

- **[P16] approve_reduced** · 原句：「（ADR 0038，Accepted：`gherkai deploy push-worker` / `list-workers`、deploy 四步、运行时显式 revision、preflight variant 解析…」
  - 提案改法：括注收成「（ADR 0038。曾经的形态——`tools/build_push_workers.py` 全量 build、task-def 焊死 `latest`、RunTask 传 family——已退役。）」；功能面由正文承载，落地/实测状态交 ADR 0038 的 Status 头。
  - 复核缩小：「Accepted…真账户实测已清零」确是 ADR 0038 Status 头的镜像（docs/adr/0038-worker-image-delivery.md:3 已完整承载命令族/四步/实测 1–7 清零），CONTEXT 跟踪它=双真源，可删；「运行时显式 revision」「preflight variant 解析」也确在正文单点承载（157 行正文「运行时只用 definition 里解析好的显式 revision、永不用 family」；164 行「其后 preflight 再按本 run 引擎解析 worker variant」）。但提案「列举的四个功能面全在同一词条正文里展开」经真值核对为假：`grep -n 'list-workers\|四步' CONTEXT.md` 显示 **`list-workers` 与「deploy 四步」在整个 CONTEXT.md 只出现在这一句括注里**，正文没有任何承载。二者…

- **[P17] approve** · 原句：「（ADR 0037 决策 2；**三名分离已随发行重组落地**：`core/gherkai_core`＝`gherkai-core`、`runtime/gherkai_runtime`＝`gherkai-runtime`…」
  - 提案改法：压成事实行、去施工语：「（ADR 0037 决策 2。目录↔发行名：`core/gherkai_core`＝`gherkai-core`、`runtime/gherkai_runtime`＝`gherkai-runtime`、`cli/gherkai_cli`＝`gherkai`＋命令 `gherkai`、`engines/novaact/gherkai_worker_novaact`＝`gherkai-worker-novaact`、`deploy_aws/gherkai_deploy_aws`＝`gherkai…

- **[P18] approve_reduced** · 原句：「（ADR 0037 决策 7；**git tag 真源 + 兄弟包 `==` lockstep pin 已落地**——五个 Python 包均 dynamic version、由 `uv-dynamic-versioni…」
  - 提案改法：压成「（ADR 0037 决策 7；skew 三态实装 = `runtime/gherkai_runtime/compose.check_backend_skew`，三个 cloud 入口先于资源 preflight 过闸。）」——保住指针与次序不变量，删三处「已落地」及其对正文的复述。
  - 复核缩小：三处「已落地」是状态镜像（ADR 0037:3 已记「git tag 版本 + `==` lockstep…skew 三态」），且「`gherkai deploy` 写 SSM 版本戳」在正文（「部署 stack 的 SSM 版本戳（stack 资源、与部署事务同生死）」）与 161 行（「随 stack 写 SSM 供**三态比对**」）双点承载，可删。但缩小两处：①「run/submit/status 的 cloud 路径」不能降级成「三个 cloud 入口」——这三个入口名是可 grep 的精确指针，真值为 `cli/gherkai_cli/__main__.py:857`（`_submit_cloud`）/`1024`（`_status_cloud`）/`1228`（run），且「先于资源 preflight」是带 why 的次序不变量（同文件 757 行 docstring：「skew 的修复动作是部署方跑一次 `gh…

- **[P19] approve** · 原句：「第四级 fd 预演已做——uvx 穿透、保留给 novaact；npx 不穿透、midscene 无第四级。」
  - 提案改法：括注收成「（`repo_root()` 已整体退役，ADR 0037 决策 3。）」，第四级的存废与依据由正文 ④ 单点承载。

- **[P20] approve** · 原句：「（已落地，ADR 0037 决策 4；worker 包内的 `deterministic_steps.py` / `deterministic.steps.mts` 只留内建示例。）」
  - 提案改法：去掉「已落地」这类时态前缀（此处与第 161 行），括注只留决策指针 +「只留内建示例」的边界事实：「（ADR 0037 决策 4；worker 包内的 `deterministic_steps.py` / `deterministic.steps.mts` 只留内建示例。）」；落地与否交 ADR 0037 的 Status 头。

### docs/adr/0004-novaact-iam-auth-via-workflow.md

- **[P56] approve_reduced** · 原句：「注册可用 CLI 或 boto3（等价）： ``` aws nova-act create-workflow-definition --region us-east-1 --name "<name>" ``` **但已做…」
  - 提案改法：改成正述、去掉 fenced block 与「但…无需手动 CLI 前置」的转折：「definition 由 create-if-not-exists 的 `ensure_workflow_definition()` 自动建（见 `engines/novaact/gherkai_worker_novaact/lib/workflow_setup.py`）：首次建、之后探测到即跳过，幂等；worker（`run_scope.py`）与 spike 均已接入，无手动前置。boto3 的 `create_workflow…
  - 复核缩小：受保护要素核查基本过关：①「boto3 与 CLI 等价」这条使代码路径可行的依据被改写文保留；②「definition 必须已注册存在、否则 CreateWorkflowRun 报 ResourceNotFoundException(404)、且此时 IAM 已通过」的不变量在 0004 line 18，本提案不动；③fenced CLI 命令并非单一真值源——`docs/REFERENCES.md:41-42` 已存可复制的 `aws nova-act create-workflow-definition --region us-east-1 --name <name>` 并带 `ensure_workflow_definition()`/ADR 0004 指针，`engines/novaact/DEVELOPMENT.md:42` 也重述了等价性，故 ADR 内去 block 不丢操作逃生舱；④「但…」不是「曾/原/已被取…

- **[P57] approve_reduced** · 原句：「生产化时也可改由 IaC / 部署脚本统一管理。」
  - 提案改法：删掉该句，保留前半「本项目用的 definition 名：`spike-wikipedia-benchmark`。」；若确实想留这个口子，补成带闸门与代价的一条（如「若某天要跨账号预建/收紧 worker 的 create 权限，可改由 IaC 建 definition——代价是 worker 失去 create-if-not-exists 的自愈，首跑依赖部署顺序」），否则不留。
  - 复核缩小：该句确无 why/trade-off/闸门，且「生产化时」已成软性时代错位（deploy_aws 已存在、definition 仍由 worker 自建，grep 全 `docs/` 无任何文档/ADR 引用此句），不承载被拒方案（没给拒的理由）也不承载决策。但**直接删掉会抹掉唯一一处指向「definition 归属」这条真实设计轴的路标**——紧邻下一段（0004 line 27）正是为 worker 自建付代价（吞 `ConflictException`、并被 0028 line 30 当作「建连段可安全重放」的幂等依据），未来读者最容易问的「为什么不在 IaC 里预建、根本不要这场竞态？」需要一条带代价的答复护栏。缩小后的改法：保留「本项目用的 definition 名：`spike-wikipedia-benchmark`。」，把「也可」句替换为提案自己草的带闸门+代价那一版（如「若要跨账号预建 definition …

### docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md

- **[P60] approve_reduced** · 原句：「注：合格图片的成功视觉应答尚未实证，留待 spike。」
  - 提案改法：删掉该注；若要保住「端点侧 SigV4 已证绿」与「视觉通道」的证据分界，改成回指后节的一句：「（视觉应答在下节 spike 第 1 段坐实）」。
  - 复核缩小：承载的受保护要素是**证据边界**，不是纯待办：该注是对同一句「端点侧 SigV4 已证绿」的限定——0003 的证据只到「纯文本拿到 HTTP 200」＋「image_url 字段被端点接受」，删注后这句连同 line 17「消除了最低置信的承重假设」会被读成决策时视觉通道已验证，正撞 CLAUDE.md「绿≠对：识别结论的证据边界」。且本文刻意保留了完整的决策时层（line 20「剩余风险（spike 第一锤要坐实）」同为 spike 前口吻、同被 line 26「本 ADR 的承重未知已关闭」收口，提案不动它）——只删这一注会让同一层自相矛盾，说明它并非孤立陈旧物。真正是沉积的只有「留待 spike」这个施工待办措辞。缩小后的改法：保边界、只换措辞并加正向指针，如 line 16 末改为「注：0003 的证据止于文本应答与 image_url 字段被接受；合格图片的成功视觉应答由下节 spike 第 1 段坐实。」——不做…

### docs/adr/0011-agentcore-browser-system-default-vs-custom.md

- **[P62] approve** · 原句：「本会话已实测可 `start-browser-session` 起停。」
  - 提案改法：删去坐标前缀，改为「已实测可 `start-browser-session` 起停。」——实测事实与上文「（2026-06 本账号实查确认）」的时间/账号锚点全部原样保留，同条内「`list-browsers` 返回空 `[]` 是正常的」这条踩坑护栏不动。

### docs/adr/0016-execution-architecture-core-lib-run-model.md

- **[P21] approve** · 原句：「**当前实装态**标在各行右侧 ✅（本树各行皆已建，无未建项）：根 workspace 已建、core/ 已建、runtime/ 已抽出并改名（见下「演进」节）、cli/ 已建、engines/ 已迁、两个引擎 work…」
  - 提案改法：整句压成一句真值声明：「**本树是当前实装真值**（无未建项）。」；同时清掉树内各行的施工态标记 `✅ 已建` / `✅ 已迁` / 裸 `✅`（engines 两行的 `✅ worker：<path>` 只删 ✅、保留 worker 路径指针）。树后解释各目录 why 的 bullet（engines 平级、目录名用 engine、窄腰叫 core）与「三名分离」段一字不动。

- **[P22] approve_reduced** · 原句：「**adapters 按 port 分子目录的目标布局**（多后端时不按后端混放）——下为**目标态**，当前实装更扁平（见图后说明）：」
  - 提案改法：改为「**adapters 按 port 分子目录**（多后端时不按后端混放）——下即当前实装：」，删「目标态」「当前实装更扁平」「（见图后说明）」。图后段去掉重复清单，压成「**当前实装**：四个 port 的 local adapter 均已建（方法签名以代码与上「按关注点拆 port」节的契约描述为准）。」——同段的「判定结果不再仅在内存，cli 跑完落 `<report-dir>/<run_id>/`…」与「**克制**：…**未发明** jobId/DDB 表/轮询续跑读取面那些字段…」（克制理由）原样保…
  - 复核缩小：表头部分成立、图后段那一刀过头。成立部分：`ls core/gherkai_core/adapters/` = _boto.py · cloud_launcher.py · event_log/ · fargate_engine.py · report_store/ · result_store/ · run_store/ · subprocess_engine.py，与树逐项一致，故「下为**目标态**，当前实装更扁平」是被实装填平后未删的旧描述层（STALE 现状陈述，非历史框定：无「曾/原/已被取代」框），「（见图后说明）」所指的图后段也确实不再解释「更扁平」——指针已失效。决策「不按后端混放」按提案保留。缩小处：图后段那句「**当前实装**：四个 port 的 local adapter **均已建**（`subprocess_engine.py` / `run_store/` / `result_store/` / `…

- **[P23] approve_reduced** · 原句：「- **G1/G2 声明语法已定**（ADR 0019）；其**调度实现**（scope 串/并行、会话共享、engine 冲突校验）已由核心库落地（[0025](./0025-plan-module-feature-t…」
  - 提案改法：压成一行纯指针：「- **G1/G2**：声明语法与调度实现均已落地——见上「G1/G2 解析前置」节。」
  - 复核缩小：重复判定成立，但压法削掉了应留的 ADR 直链。成立部分：L262 与 L256（「G1/G2 解析前置」节末条）确为同一事实的两份，L256 更全（「scope 分组 + engine/timeout 冲突校验见 0025（多值直接 `PlanError`），job 间并发/失败隔离/超时兜底见 0026；scope 内串行由 worker 消化」），L262 的括号枚举「scope 串/并行、会话共享、engine 冲突校验」是其严格子集且自带回指，删枚举不丢信息。缩小处：提案版只剩节内回指、把「（ADR 0019）」与 [0025]/[0026] 三个直链一并抹掉；ADR 供 AI 检索为主（约 80%），「现在做／现在不做」清单里每条都挂 ADR 直链是本节的既有形态（相邻两条分别挂 0022 / 0016 各节），单独把这条降级为「只指本文某节」会让按 ADR 编号检索这条结论的读者多绕一跳。缩小后的改法：「- **G…

### docs/adr/0017-cloud-execution-fargate-over-runtime.md

- **[P44] approve_reduced** · 原句：「> **已落地（v1.1 云端执行）**：Fargate/ECS 即 `--backend cloud` 的执行实态（`FargateEngine` + `iac_aws_backend/` CDK 工程，真部署真跑，见…」
  - 提案改法：首句压成回指，其余不动：「> **已落地（v1.1 云端执行）**：倾向已按 Status 头所述落地为实态。**A/B 实测未做**——直接按上「workload shape 是批处理」判据落地，故「诚实修正」里成本那条『孰优只能实测』至今未量化。上「翻盘条件」仍适用：shape 变成长驻服务时重估。下述原计划保留作决策史。」
  - 复核缩小：提案的事实前提有误：`git show 853d730 -- docs/adr/0017-cloud-execution-fargate-over-runtime.md` 显示该 commit 只新增了第 3 行 Status 头，第 33 行「已落地（v1.1 云端执行）」演进注更早就在——不是「同一层一起写入」，而是新 Status 头后来重述了旧注。且第 5 行括注「见 Status 头与下「何时坐实」的演进注」把该注列为落点，它紧贴第 35 行保留的「原计划」文本作防误读护栏，段内需要能自立；精确指针 0032/0033 在此处也有到位价值（按 A/B 实测未做/何时坐实 检索时仍能拿到实态出处）。确属沉积的只有与 Status 头逐字级重复的机制枚举。缩小后的改法：第 33 行首句压成「> **已落地（v1.1 云端执行）**：Fargate/ECS 即 `--backend cloud` 的执行实态（见 Status…

### docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md

- **[P38] approve_reduced**（**已随主观发现 [25] 落地**：第 20 行已压成结论 + 0022 指针 + 保留两条不变量，无需再动） · 原句：「脚手架文件本身迁入 `engines/*/worker/`、由 worker import 触发注册进注册表（锚点仍写在脚手架文件里，注册表只是收集机制）——锚点由测试开发维护、非 QA 预设，故不违背"QA 零预设"。」
  - 提案改法：把第 20 行「落地现状」条压成两句：①「脚手架现各内置一个演示/验证用 URL 锚点 `页面地址(?:精确)?匹配 "<正则>"`（`features/deterministic_anchor.feature` 实跑验证），取代当初『空脚手架、零具体锚点』的设想；锚点仍由测试开发维护，『QA 零预设』不破。」②保留「注册表现同时是能力自述面（0036：注册即暴露——description/example 必填、QA 可用 `list-deterministic` 主动查）：『主动查』不等于『预设措辞』，本条不变量…
  - 复核缩小：落点重述确属沉积（第 3 行 Status 头、第 18 行各写过一遍且都带 0022「迁移」指针），可压；但被引句里的括注「（锚点仍写在脚手架文件里，注册表只是收集机制）」是防误读护栏，不能随落点一起删——0022 的标题字面就是「确定性 step = worker 注册表」，这条括注正是 0022 第 82 行「实装偏差纠正」在 0020 侧的落点，唯一其它副本只在 Status 头（元信息层），正文读者读到第 20 行「落地现状」条时若无它，会以为锚点住在注册表里。缩小后的改法：①「脚手架现各内置一个演示/验证用 URL 锚点 `页面地址(?:精确)?匹配 "<正则>"`（`features/deterministic_anchor.feature` 实跑验证），取代当初『空脚手架、零具体锚点』的设想；**锚点仍写在脚手架文件里、注册表只是收集机制**（实装偏差纠正见 0022「迁移」条），锚点由测试开发维护，『QA 零预…

### docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md

- **[P35] approve_reduced** · 原句：「> **实现状态（v1.0 当前）**：下述 `@deterministic` 注册表**已落地**，两个引擎对称——Nova `engines/novaact/gherkai_worker_novaact/determ…」
  - 提案改法：删掉状态叙述与复述（「实现状态（v1.0 当前）」「已落地」「两个引擎对称」「先查注册表…未命中落 catch-all」「各有注册表单测背书」），把非重复的三样并进下文「扩展点 = 对应 worker 里的一张 step 注册表」条：两个 code 落点路径、命中后的状态映射（passed 无 votes / AssertionError→failed+assertion_failed / 其它→error）、冲突异常 `DeterministicConflict`；自引编号改成「见下『冲突规则自定』条」。
  - 复核缩小：提案指出的沉积只有一部分成立，整块删会带走受保护内容。不可删的部分（docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md 第 42 行）：①「未命中才落 ②内建 URL 导航 / ③AI catch-all」是本 ADR 内唯一提到内建 URL 导航这一级的地方——第 33 行只写「未命中 → 落到 catch-all → 走 AI」（两级），删掉后 0022 讲的派发链就与真值（三级，见 0024 第 114 行、0020 第 23-25 行）不符，属异质事实误判；②「脚手架现各注册一个真实 URL 锚点（页面地址匹配 "<正则>"）」是实装真值，且是第 46-60 行示例（用的是另一措辞 当前 URL 匹配）为示意而非实装的唯一校准，删掉会让读者把示例当注册现状；③「不投票、可复现」的『可复现』是确定性 step 的 why；④「实现状态（v1.0 当前）/ …

### docs/adr/0024-worker-core-protocol.md

- **[P26] approve** · 原句：「**仅余 Fargate 特有的真容器 grace/中断校准**（[0032](./0032-fargate-execution-environment.md)）」
  - 提案改法：删掉「仅余…校准」这半句；Fargate 特有问题的归属指针由段内其它 0032 引用已经给到。若日后确有未闭项，真源应留在 0032 自己的 Status/正文，不在本 ADR 复述进度。

- **[P27] approve_reduced** · 原句：「**产物落点半已实现**（[0029](./0029-engine-artifacts-to-s3.md) 的 `ArtifactUploader`，在 subprocess 预演环境已做、Fargate 忠实预演，[0…」
  - 提案改法：四处状态声明合成一处：小标题保留「（subprocess + S3/DDB 两态，对称 0029 的 ArtifactUploader）」，正文改为「上条把三条 I/O 边缘作同一决策钉死；job 入口 + 事件 sink 抽成 `JobSource` / `EventSink`（每引擎一个 Python + 一个 TS 模块，各语言各写、语义契约对称——同 ArtifactUploader 的结构约束），subprocess 态（读 stdin / 写 `EVENTS_FD`）与 Fargate 态（S3 `Ge…
  - 复核缩小：「半已实现 / 半对称落地 / 两态均已实装并接入 worker 主流程」三层措辞确是分期施工节奏、与小标题括注重复，可删；但提案给出的替换句顺带砸掉三处受保护要素：①「[0016] 决策 B」这个决策指针 + 「在 subprocess 预演环境已做、Fargate 忠实预演」（这是 0016 决策 B 的决策内容，非进度，0032 首段也据此不重述上传机制）；②「见下「远程传输演进」节的「job 入口/事件出口」表 + 「DynamoDB 作 events-out」契约」两个精确内部指针；③替换文本止于「并存」，未含「按有没有注入对应 env 分流（`JOB_S3_URI` / `EVENTS_DDB_TABLE`，判据是「注入了什么」非「在哪跑」，0016 红线）」这条不变量与 `run_scope.py`/`run-scope.ts` 均 `JobSource.from_env().read()` + `EventSin…

- **[P28] approve_reduced** · 原句：「**两个引擎的 reportRefs（kind=产物类型、粒度由挂载层级表达）**——Midscene 取 `agent.reportFile` 报 `kind=report` 于 `scope_done`（scope …」
  - 提案改法：把该项压成「两个引擎的 reportRefs（映射见上「字段语义·`reportRefs`」）——取值路径：Midscene `agent.reportFile`；Nova 设 `logs_directory` 持久化后取 `metadata.trajectory_file_path`；归集成 RunReport（0027）」，删掉重复的 kind/粒度/挂载层级三段描述。
  - 复核缩小：0024:254 该项确是可指针化的第二份规格（同一映射在 0024:112 已作事实源写全、67/74 行 jsonc 已示例），同列表其它项都用「机制见上「字段语义·`sessionId`」」的短句+指针形态，故压缩方向对；唯一增量（`agent.reportFile` / `logs_directory` / `metadata.trajectory_file_path`）提案已保留。但被删的加粗括注「kind=产物类型、粒度由挂载层级表达」是 0024:112 那条不变量（「粒度」由挂在哪级事件表达、不由 kind 表达）的简短重述——按「带指针的有意简短重述是设计」，正解是把它与新加的指针并存、而不是用指针换掉它。缩小后的改法：该项写成「**两个引擎的 reportRefs（kind=产物类型、粒度由挂载层级表达；映射详见上「字段语义·`reportRefs`」）**——取值路径：Midscene `agent.rep…

### docs/adr/0025-plan-module-feature-to-jobs.md

- **[P40] approve** · 原句：「- **现在做（v1.0）**：上述 `plan` 接口、parse（借 Compiler）、scope 分组 + engine 校验、id 派生、三档 Gherkin 特性、test cases。」
  - 提案改法：压成不需要逐条维护的表述：「- **现在做（v1.0）**：上文已描述的全部（接口、parse、scope/engine/timeout 解析、id 派生、三档 Gherkin 特性、test cases 护栏）。」，或更彻底：「- **现在做（v1.0）**：上述全部。」——把边界信息交给「留口子不实现」那条承担。

### docs/adr/0028-transient-network-ssl-resilience.md

- **[P34] approve** · 原句：「**注意**：这条分类不对称**不影响 step 短路**（[0031](./0031-job-lifecycle-states-and-severity.md) 决定六，现已实现）——短路判据锁 `status==er…」
  - 提案改法：留第 126 行那句全文（它紧邻短路判据定义），第 69 行的注意句压成指针 + 本地独有结论：「注意：这条不对称不影响 step 短路（判据见下「scope 内 step 级短路」条），只影响用户看到的 errorType 文案。」；同时把第 126 行的「下面记的」改成「上文『已知欠账』条」。

### docs/adr/0029-engine-artifacts-to-s3.md

- **[P46] approve_reduced** · 原句：「- **act 粒度即时抢传 / botocore retry vs grace / 中断韧性**（Fargate 特有）：这些是容器盘停即销毁逼出的」
  - 提案改法：从这条留口子里删掉「act 粒度即时抢传」这一项（连同「第一期是混合两级上传」的旧表述），只留仍属 Fargate 的「botocore retry vs grace / 中断韧性」并保留移交 0032 的指针；抢传的现状与归属由「上传时机」四级 +「定位澄清」条承载。
  - 复核缩小：「act 粒度即时抢传…移到 0032」不是旧层残留，而是与两处仍然生效的边界声明互锁的归属决策 + 交叉引用：0029 第 10 行「③ Fargate 执行环境特有（容器盘停即销毁的中断丢失、grace/stopTimeout、**即时上传粒度**）——见 0032」、Status 头「Fargate 执行环境特有的中断丢失/grace/即时上传见 0032」，以及 0032 自己的 Status 头「本 ADR 收…grace/stopTimeout 预算、**act 粒度即时上传**」。把这一项从留口子的移交清单里删掉，会让 0029 ③ 与 0032 头部单方面声明归属而此处失联，反而制造新的不一致；句尾「本地盘不销毁，不涉及」也是「为何第一期不涉及」的 why，不能连带删。 真正的沉积只有一处：括注里的第一期上传形态「混合两级上传（reportRef 实时 + 剩余 scope 末批量）」——同文件「上传时机」节（第…

- **[P47] approve_reduced** · 原句：「- **~~S3 上传错误的分类~~（第一期已定，见上）**：第一期=`engine_error`、不进重试域、可观测（不静默吞）。」
  - 提案改法：整条压成一行带指针的现状：「~~S3 上传错误的分类~~（第一期已定，见上「上传错误分类」条；诊断精度后续细分见 0032「上传失败处理」两层）」——删副本、把「待 Fargate」的悬空待定改成指向落点的指针。
  - 复核缩小：①（删「第一期=engine_error、不进重试域、可观测（不静默吞）」这行副本）必须驳回：它正是红线保护的「带指针的有意简短重述」——留口子清单的固定形制就是「划掉标题 +（已定，见上X）+ 一行结论摘要」，同节兄弟条（S3 key 命名条、materialize 条）全同此形，摘要让读者扫清单即知落点、不必跳转；且「第一期=…」自带期次框定，不是当下状态漂移。压成纯指针会破坏该索引形制并降信息密度。 ②（尾句「是否细分 network_error/进重试域待 Fargate（0032，与 grace 预算一起定）」）确属沉积：0032「Fargate 特有问题：处置结论」的「上传失败处理（已实现 ✅，两层）」已结掉——层1 S3 网络失败（ConnectTimeout/ReadTimeout/EndpointConnection/5xx/ConnectionError）判 network_error、仅诊断不触发重试，只 …

### docs/adr/0030-realtime-persistence-seam.md

- **[P30] approve** · 原句：「DDB 的并发一致性（Map<scope_id> 按 key 定位、条件更新）见下「决定六」（云端 adapter 落库形态，已实装）。」
  - 提案改法：第 11 行括注去掉状态戳，压成「见下「决定六」（云端 adapter 落库形态）」；第 7 行「（决定六，已实装）」压成「（见决定六）」。

### docs/adr/0033-iac-aws-backend-and-composition-wiring.md

- **[P12] approve_reduced** · 原句：「**本 ADR 正文的资源清单/命名契约/preflight 仍是当前实装态**；IaC 工程定位、「默认建新」、裸 `cdk deploy -c` 提法保留为**历史叙述**并带就地历史注（决策与资源清单/命名契约/p…」
  - 提案改法：删括注，句尾收在「…提法保留为**历史叙述**并带就地历史注。」
  - 复核缩小：重复部分成立，但括注不是逐字同义——它比句首多了「决策」二字，而这两个字承载消歧：Status 头开头声明「本 ADR 定 **IaC 工程定位/资源清单/命名契约/preflight** … 的稳定决策」，尾句却把「IaC 工程定位」列入保留为历史叙述的三项；括注的「决策与…是当前实装态」正是界定「只有形态/提法（独立工程、裸 cdk deploy -c、默认建新）是历史，决策本身仍立」。整块删括注会让「IaC 工程定位…保留为历史叙述」被读成决策失效，与同一 Status 头开头自相矛盾。缩小改法（把「决策」并入句首，再删括注，零信息损失）：句首改「**本 ADR 的决策与正文的资源清单/命名契约/preflight 仍是当前实装态**；IaC 工程定位、「默认建新」、裸 `cdk deploy -c` 提法保留为**历史叙述**并带就地历史注。」（其后「0038 部分待其翻牌」现已随 0038 Accepted 另需单独校…

- **[P14] approve_reduced** · 原句：「「资源清单」末段的编排机器权限清单按 0038「权限面增量」更新。」
  - 提案改法：删此句（前后「SSM 参数族加 `worker-template/*`…」与「资源清单/命名契约/container 名契约不动」两句照留）。
  - 复核缩小：不可整句删：docs/adr/0033-iac-aws-backend-and-composition-wiring.md 行 3 Status 头 0038 段是「0038 改了本 ADR 什么」的 delta 枚举，本句与同段「SSM 参数族加 `worker-template/*`…」「runs 表 STATE 顶层加 `worker_task_def_arns` + 稀疏 GSI」并列，是**异质累加的一项**而非重复——删掉即枚举缺项，读者从 Status 头再也看不到「权限面被 0038 加过增量」；且它与 0038 行 125 的对应句构成双向反向链（CLAUDE.md 要求取代关系双向记）。它与正文行 46 的关系是「Status 头摘要 vs 正文落点」两层，非零距离重复。真正的沉积只有祈使/未来式语气（「按…更新」读着像未兑现的待办）。缩小改法：只改语气为完成态，如「「资源清单」末段的编排机器权限清单已按 0…

### docs/adr/0034-detached-batch-reconciler.md

- **[P24] approve_reduced** · 原句：「**已全部实装、local+cloud 两路端到端真部署真跑通**（core `project`/`reconcile` + cli `submit`/`status`/`detached` + `lambdas/` 三…」
  - 提案改法：删掉逐模块清单，Status 头收成「> **Status:** Accepted —— **已全部实装、local+cloud 两路端到端真部署真跑通**（真实 AWS 账户/us-east-1 真跑：local submit→per-run 推进→passed，cloud submit→kicker 冷启动→事件驱动链→passed，含卡死救活真验）。纠正 [0016]…」，其后的纠正说明与「0016/0024/0026/0031 已同步标 Partially-superseded-by 本 ADR，0030 …
  - 复核缩小：「记账语气 + 已腐坏」诊断成立，但整段删丢了唯一的跨层落点索引，应改为校准。成立部分：`iac_aws_backend` 已改名 `deploy_aws/gherkai_deploy_aws`、`detached` 已迁 `runtime/gherkai_runtime/detached.py`（graphify 与 ls 均已核），该清单确是四层改动都没人校准的 STALE 现状陈述，且不承载 why/trade-off/不变量/被拒方案/决策，正文各机制节给的是更精确的符号与护栏（`reconcile.tick`、`core/tests/test_reconcile.py::test_launch_failure_does_not_wedge_run` 等）。缩小理由：整删后 0034 全文再无一处指出三 Lambda 与 Stream/EventBridge 的 code 归属（正文只以角色名「[kicker Lambd…

### docs/adr/0037-distribution-and-packaging.md

- **[P1] approve_reduced** · 原句：「## 落地次序与依赖（依赖关系，非进度追踪；本节编号只在本节内部使用，其它文档不引用它）  0. **占名**（无依赖，先做）。」
  - 提案改法：删除整节。删前核对三处已承接：①占名 → 决策 8 第 1 条；②contributor-README 弯路 → 被拒方案该条（指 0039）；③「期外/按需」两项 → 重议闸门第 2、5 条。若要留一句跨 ADR 血缘，只保「基底镜像 CI 必须在 worker 包发行之后（基底装的是已发行 worker 包）」这条因果，并入决策 5 基底镜像那段，不留步骤编号。
  - 复核缩小：整节删除会连带删掉两处全库唯一的内容，须先接住再删。①0037:223「期外/按需」里的 `--capabilities` 设计草图——「运行配置有效性 engine × browser 后端 × backend 走 worker 自述、非安装期 extras」三维 + 「[0036] 形态延伸」指针，**重议闸门第 2 条（0037:267）只有触发条件与「不回到安装期 extras 表达能力矩阵」，没有这三维、也没有 0036 指针**；提案说「完整重合」不成立，这属「不实现≠不设计」的 defer 设计，删=丢。②0037:219 的「metadata（license 文件进各包、`[project.urls]`）」——全库 grep 只此一处（决策 8 仅提 `[project.urls] Changelog`）。其余判据核验通过：步 0 复述决策 8「占名（先于一切）」（0037:174）；contributor-RE…

- **[P2] approve** · 原句：「## 对既有文档与 code 注释的影响（校准清单，翻 Accepted 时已逐条完成；括注是当时的到期点，路径名为当时的路径）」
  - 提案改法：压成一条历史句 + 一条护栏，其余删：①「发行重组/worker 交付/deploy 三层落地时，README·子 README·CONTEXT·guides 与 code 注释里的旧包名与旧调用示例已随各层校准（逐文件到期点见当时的 commit）」；②保留唯一有再犯价值的反模式并加指针——「用户可见错误文案里的旧 extra 名（`pip install core[aws]`）会教用户敲一个不存在的包，属最易漏的一类；规则与护栏见 [0039](./0039-user-facing-surfaces-no-in…

- **[P3] approve** · 原句：「- **midscene 的 `npx` 兜底拉起**：实测 npx 不把 EVENTS_FD 传给 node 子进程（该号上是 npm 自己的 FIFO、写即 EBADF），事件全丢；按「实测不过 → 降级为报错指引」…」
  - 提案改法：从重议闸门节删除本条，同时在被拒方案节补一条对应护栏（补上决策 3 那句「（被拒方案）」的落点）：「**进程包装层的 fd 转发补丁（为救 npx 兜底）**：多一层包装 = 多一处吞 fd/吞信号的地方（ADR 0024 三通道的反面教材）；npx 实测不穿透即降级为安装指引，midscene 无第四级（证据见决策 3 第 4 级）。」证据本体留在决策 3 与实测项 2，不再复述。

- **[P4] approve** · 原句：「- **不设 `[local]` / uvx 拉起作主路径**：同 venv 直调无包装层、离线、pin 锁死，三点全优；uvx 降为兜底且存废待实测。」
  - 提案改法：改末句为已定态，保留三点权衡：「……三点全优；uvx 降为兜底，fd 预演后仅 novaact 保留第四级（见决策 3 第 4 级）。」

### docs/adr/0038-worker-image-delivery.md

- **[P5] approve** · 原句：「## 对既有文档与 code 的影响（校准清单，Draft→Accepted 门槛的一部分）……- `tools/build_push_workers.py` 退役（其 ECR 登录序与命名规则收进 push-worke…」
  - 提案改法：整节压成一句完成态历史注（仿 0037 标题措辞），删四条 bullet 与四个（已完成）：「## 对既有文档与 code 的影响（校准清单，翻 Accepted 时已逐条完成；路径名为当时的路径）：`deploy_aws/README.md` 的 push-worker 流程改写、两个 `engines/*/Dockerfile` 的 `--platform` 注释补本 ADR 指针、CONTEXT 词条去施工标记、`tools/build_push_workers.py` 退役。」

- **[P6] approve_reduced** · 原句：「当前代码传 family（取最新 ACTIVE），多 variant 下任何一次 push 都会劫持默认——必须改。」
  - 提案改法：删该句，首条止于「**运行时只用 definition 里的显式 revision，永不用 family 取最新**。」；若要留血缘，改成用「曾」框住并指向护栏：「（迁移前的 IaC 传 family，理由见被拒方案『RunTask 传 family』条）」。
  - 复核缩小：「当前代码传 family」确已 STALE（code 真值：runtime/gherkai_runtime/compose.py:718-796 的 worker_task_defs「必给、无缺省」，FargateEngine 只收 revision_arn），且非「曾/原」框定，故必须动。但裸删会把 why「多 variant 下任何一次 push 都会劫持默认」从不变量条本地抹掉（该 why 只在文末被拒方案「RunTask 传 family」条另有一份，无指针相连）。缩小改法 = 采用提案自己给的第二方案，不做裸删：首条写成「**运行时只用 definition 里的显式 revision，永不用 family 取最新**（迁移前的 IaC 曾传 family，理由见下「被拒方案」的『RunTask 传 family』条）。」——过时现状断言与号令去掉、why 一跳可达、血缘用「曾」框住。首句一字不动（compose.p…

- **[P7] approve_reduced** · 原句：「5. `tools/build_push_workers.py` 退役；`deploy_aws/README.md`、Dockerfile 注释与 CONTEXT 校准。」
  - 提案改法：删整节；若按 0037 的 house style 保留骨架，至少删本条（步 5）与步 1 的迁移时序括注，并把标题改完成态（如「## 落地次序与依赖（依赖关系，非进度追踪；已全部落地，编号只在本节内部使用）」）。
  - 复核缩小：删整节被证伪两处：(1) 房屋风格反证——0037 同名节在 Accepted 状态下**保留**（docs/adr/0037-distribution-and-packaging.md:216「## 落地次序与依赖（依赖关系，非进度追踪；本节编号只在本节内部使用，其它文档不引用它）」+ 步 0–4 全留），本节标题也自陈「依赖关系，非进度追踪」，整删=删掉声明过的依赖设计；(2) 步 1 的括注「（可在 0037 之前先落：把当前 IaC 建的唯一 revision 当作解析结果，行为不变）」承载 why（为何提前落地行为中立=可安全解耦），且与 0037:219 步 3「运行时改显式 revision 等可先落」互为跨 ADR 一致陈述，删一半会造成两 ADR 对同一解耦事实不对称。缩小改法：**只改标题为完成态**、对齐 0037 措辞（如「## 落地次序与依赖（依赖关系，非进度追踪；已全部落地，本节编号只在本节内部使用，…

- **[P8] approve_reduced** · 原句：「实装次序细节：`--set-default` 落在与基底同步共享的推送路径之外，实际 = 写映射 → 退休旧 revision → 写指针 → 清理（两者无依赖）；registry host 取 `ecr:GetAuth…」
  - 提案改法：把次序并进步 8 正文直陈、去掉施工对照框与重复半句：「…输出 tag / digest / revision，以及「提交时用 `--worker-variant <名>`」。实际次序 = 写映射 → 退休旧 revision → 写指针 → 清理（后两者无依赖）；`--set-default` 不在与基底同步共享的推送路径上。」registry host 的 proxyEndpoint 说明只留在「权限面增量」一处。
  - 复核缩小：「实装次序细节…实际 =」的施工对照框可去、次序直陈正文可行，但提案的改法丢/改了两处：(1)「（权威、与 moto 同形）」中「与 moto 同形」在全 repo 别无载体（grep proxyEndpoint 只三处：本句、权限面增量、workers.py:508 docstring；后两处都只说「权威值/不需要 STS」），它是「moto 层测试为何对这条可信」的证据性理由，属 Accepted ADR 的自包含证据，不能随半句一起删——若要单点收拢，把它并进「权限面增量」：「其 `proxyEndpoint` 即 registry host（授权响应里的权威值、与 moto 同形），**不需要** `sts:GetCallerIdentity`」；(2) 不要把「（两者无依赖）」改写成「（后两者无依赖）」——原括注紧跟「`--set-default` 落在共享推送路径之外」，「两者」很可能指「写指针 vs 共享推送路径」…

- **[P9] approve_reduced** · 原句：「## 实测项（Draft → Accepted 前必清；「绿≠对」）……- **无凭证下已验的部分**（其余全待真账户）」
  - 提案改法：标题改完成态：「## 实测（**已清零**；「绿≠对」——每条都依赖 mock 之外的真实行为，证据内联于各条）」；末条前缀改「- **mock / 无凭证层的覆盖面**（真账户证据见上各条）：…」，删「其余全待真账户」。
  - 复核缩小：标题里的「实测项」三字不能改成「实测」：0037:232「细节见 [0038](./0038-worker-image-delivery.md) 实测项 1」与 0037:234「见 0038 实测项 5」以「实测项 N」形态跨 ADR 精确指过来，本 ADR Status 头也写「**实测项 1–7 清零**」，改名会削弱这条稳定锚点（属精确指针）。缩小改法 = 逐字照 0037:225 的 house style：「## 实测项（**已清零**；「绿≠对」——每条都依赖 mock 之外的真实行为，证据内联于各条）」。末条改「- **mock / 无凭证层的覆盖面**（真账户证据见上各条）：…」并删「其余全待真账户」approve——1–7 各条内联的真账户/真 docker/真 synth 证据一字不动，「无凭证下已验」的层次区分由新前缀承接，无 why/证据损失。

- **[P10] approve** · 原句：「这期只实现 docker……**这一期 deploy 机器需要容器引擎**（同步基底要 pull / push；非纯发行版本跳过该步、不探活）；免容器引擎的 registry 直拷是重议闸门里的加法。」
  - 提案改法：「这期只实现 docker」→「只实现 docker（podman 经同一口子接入，见重议闸门）」；「**这一期 deploy 机器需要容器引擎**」→「**deploy 机器需要容器引擎**」，暂时性交给句尾已有的重议闸门指针。

- **[P11] approve** · 原句：「「资源清单」末段是编排机器权限的单一登记处，随本 ADR 落地去那里改，此处只列增量」
  - 提案改法：改完成态陈述：「[0033]「资源清单」末段是编排机器权限的单一登记处（已按下列增量改毕），此处只列增量；…」

### docs/adr/0040-consumer-role-model-and-terminology.md

- **[P51] approve** · 原句：「- 全仓「test engineer」→「测试开发」（已落）。」
  - 提案改法：删这一行；术语面落地状态由 Status 头承担。若想保留「术语改名是本 ADR 的产物」这一线索，可把它并进决策 1 表格「弃用 test engineer / test-engineer」那格的括注里，不再单列一条影响。

### docs/adr/0014-ai-first-assertions.md（单独 agent 审计，独立复核 approve_reduced）

- **[P66] approve_reduced** · 原句：「   - Midscene 取结构化全家族可选：`aiBoolean / aiNumber / aiString / aiQuery<T> / aiAsk`。」
  - 提案改法：裸 SDK 列举压成指针（同一列举在 REFERENCES.md 与 0010 ③ 各有更权威版本）。
  - 复核缩小：不整删，替换为「布尔之外的取结构化路径（取数/取串等）及两个引擎的对称映射与边界，见 [0018]；Midscene 该家族的 API 面与 .d.ts 位置见 [REFERENCES]」——须保留指向 0018 的正向指针（补 0014→0018 缺失的一环），不动 0014:16 的反模式句。

## 二、主观发现（5 条）——**已批、已落**（同批 commit）

- **[14] docs/adr/0013-cross-engine-sharing-boundary.md · BOUNDARY** · 「**唯一跨引擎共享的是 `features/`（Gherkin 用例文本）**，即 [0005](./0005-single-shared-feature-file.md) 的单一事实源。」
  - 问题：0013 自称是「什么该共享、什么不该」的固定判断处，但共享面清单只列 `features/`，未纳入 ADR 0037 决策 4 后新增的第二个跨引擎共享面——使用方项目的 `steps/` 目录（两引擎扫同一目录、正则成对）。未来读者拿 0013 回答「X 该不该跨引擎共享」会得到不完整的地图。
  - 建议：在「判断」节该句后补一句并给指针：「跨引擎共享的**框架代码**仍止于此；使用方侧另有一个跨引擎共享的**约定面**——项目 `steps/` 目录（两引擎扫同一目录、正则成对、文件各按扩展名分属引擎），见 [0037] 决策 4。」不改「引擎实现代码不跨引擎共享」的结论，也不动 Status 头。

- **[19] docs/adr/0014-ai-first-assertions.md · STALE** · 「待更难用例的抖动数据出来后细化，届时更新本 ADR，不另立。」
  - 问题：0014 的度量/未决段仍以「只有 1 个 AI 友好用例、更难用例数据未出」为现状，未吸收 0018 后来两批刁钻用例的实测（模糊判定投票稳过、措辞歧义可翻转判定），也无任何 0018 指针——两者引用是单向的（0018→0014）。
  - 建议：在「持续度量校准」或「未定」条加一句并挂指针：「模糊判定/负向/措辞歧义的首批数据已出（见 0018），暴露的主导风险是**措辞歧义**而非抖动率；N 缺省值与阈值仍待抖动量化数据」——保持「未定」结论不变、只补已知证据与交叉引用。

- **[25] docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md · REDUNDANCY** · 「**落地现状（[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md) 决定，非当初"空脚手架"）**：脚手架现由测试开发各内置**一个…」
  - 问题：0020 的「落地现状」与 0022 的「实现状态（v1.0 当前）」对同一套事实（脚手架落点 / 各一个 URL 锚点 / 注册机制 / 注册表兼能力自述面）做了两份完整叙述，且两份同向漂移到同一批死路径——单一事实源被复制成两处待维护。
  - 建议：0020 的「落地现状」压成一句结论 + 指针（如「落地形态与真实路径见 0022「实现状态」段」），只保留 0020 自己要守的不变量（QA 零预设仍成立、「主动查」≠「预设措辞」），把路径/锚点/注册机制的事实留给 0022 单点维护。

- **[74] cli/DEVELOPMENT.md · STALE** · 「`cli/tests/test_package_readmes.py` 是「包 README = 发行包长描述」的护栏（零 ADR/决策号/内部机制名、零相对链接、每个包目录一份 `DEVELOPME…」
  - 问题：对护栏覆盖面的描述窄于实际：该测试文件还守着根 README.md 与各包 pyproject/package.json 的 `description`（PyPI/npm 页顶 Summary），文档只列了三项中的包 README 侧。
  - 建议：括号内补一项：「另守根 `README.md` 与各包 pyproject/package.json 的 `description`（PyPI/npm 页顶 Summary）同样零内部指代」。

- **[94] docs/guides/execution-and-reconciliation.md · BOUNDARY** · 「cap 的 why：并发闸的是**worker（Fargate task）的并行数**（per-run 语义：单 run 内最多几个 job 并行），task 跑在部署方的 cluster、计入部署方…」
  - 问题：guide 正文越界复述决策理由：这段（连同紧随的「local 无 cap：……没有第二方需要保护」与「不拦提交……故退 2」的取舍）几乎逐句复制 ADR 0034 机制四的 why/trade-off，违反本文自己声明的「只讲 how、不复述 why，why 只给指针」，形成双源、日后各自漂移。
  - 建议：正文只留 how：「并发上限 = min(definition 的 `RunMeta.max_concurrency`, 部署侧 cap)；cap = reconciler/kicker Lambda env `MAX_CONCURRENCY`（IaC 设，当前 8）；local 无 cap；`submit --backend cloud` preflight 超 cap 只提示不拦（REPORT_DIR 不一致才退 2）」；把「为何 cap 归部署方 / local 为何无…

## 三、UNCERTAIN（1 条）——**已批、已落**（同批 commit）

- **[93] docs/doc-health-review.md** · 「覆盖范围：**全部项目文档**——不预设"只有某几类相关"，凡人/AI 会消费的项目 Markdown 都在内：」
  - 问题：覆盖范围清单对真值集做差集后漏两项：`docs/doc-health-review.md` 与 `docs/code-health-review.md` 自身（两份方法文档也是 AI 消费的项目 Markdown，且互为姊妹、与 `.claude/commands/` 摘要成对，最需要一致性校准），清单里无任何条目点到它们。
  - 建议：覆盖范围加一条：「`docs/doc-health-review.md` / `docs/code-health-review.md`（两份复盘方法文档自身：只查 DEADLINK / STALE / 内部矛盾 + 与 `.claude/commands/` 摘要一致性；方法内容本身是决策，不在复盘里改——与 CLAUDE.md 同款口径）」。
  - 验证意见：差集本身核实为真：`git ls-files '*.md'`（排 graphify-out/、node_modules/、docs/adr/）共 26 项，逐条比对第 47–56 行清单后，确只有 `docs/doc-health-review.md`、`docs/code-health-review.md` 无对应条目（README 8 个、DEVELOPMENT 6 个、CLAUDE.md、CONTEXT.md、docs/REFERENCES.md、docs/guides/*、SIGV4-FETCH-RECIP…

## 四、红线复核否决的提纯提案（26 条，存档不落改）

- [P13] docs/adr/0033-iac-aws-backend-and-composition-wiring.md · 「本 ADR 正文三处「默认建新」（资源清单条、VPC 节标题与其「为何默认建新」句）在 0037 实装后失效，「默认建新对增量 deploy…」 → 被引句承载「精确指针 + 失效范围界定」两项受保护要素，且指的是本 ADR 正文自身的节/条（合规指针形态，非会话上下文）。定位：docs/adr/0033-iac-aws-backend-and-composition-wiring.md 行 3 Status 头 0037 段内的「本 ADR 正文三处「默认建新」（资源清单条、VPC 节标题与其「为何默认建新」句）在 0037 实装后失效」。①…
- [P25] docs/adr/0024-worker-core-protocol.md · 「**传输选型已定 + adapter 已实装 + 组合根接线已落地**」 → 提案的改写文本与它自己承诺保留的受保护要素冲突，且删掉了两处受保护物。定位 0024 L175（「远程传输演进」节引文）：①**被拒方案护栏被压没**——原句「events-out 焊死到 DynamoDB events 表（worker PutItem / core Query 轮询，**非 SQS/MSK/CloudWatch**——见下「DynamoDB 作 events-out 传输」+ …
- [P29] docs/adr/0030-realtime-persistence-seam.md · 「- **决定七（cli 接线 cloud）— 已实装**：`--backend {local,cloud}` 组合根装配（两后端下沉 `co…」 → 「唯一新增的是『已实装』」不成立，第 215-216 行还压着四类受保护要素：①Accepted ADR 内联的自包含证据——0030:215「moto 全程 mock 单测、行为对拍 local——坐实「换后端 core 不动」」与 0030:216「真跑通 local↔cloud 端到端」，grep 全文仅此两处；而提案的搬入目标与 0030:175（决定六首段）自设边界正面冲突：「以下是各后…
- [P31] docs/adr/0030-realtime-persistence-seam.md · 「  - **`core/tests/test_stores.py`**：现用**位置下标** `state.jobs[0].scope_id…」 → 被误判的受保护要素（docs/adr/0030-realtime-persistence-seam.md 决定五，第 164-170 行）：①第 169 行（test_stores 位置下标 → TypeError）是第 164 行「含两个会静默出错的陷阱」中点名的第二个陷阱本体，且是消费侧不变量（RunState.jobs 只能按 scope_id 取、不能按位取）——属反模式/陷阱，删即抹掉护…
- [P32] docs/adr/0030-realtime-persistence-seam.md · 「> **本文出现的 `pending`/`running`/`skipped`/`aborted` 这些状态值，定义与 severity 归…」 → 被误判的受保护要素（docs/adr/0030-realtime-persistence-seam.md 第 12 行独立引用块）：它正是红线里点名保护的「带指针的有意简短重述」——一句话 + 指向 0031 的精确指针，形态刻意用引用块独立成层，声明的是单一事实源归属（状态值定义与 severity 归属全在 0031）＋本篇职责边界（只用不定义）。0030 全文（决定三/四/五、第 171 行…
- [P33] docs/adr/0028-transient-network-ssl-resilience.md · 「- **现在做（v1.0）**:上述两层重试、`network_error` 分类、退出码约定、白名单识别、会话泄漏防护、core job …」 → 被误判的受保护要素（docs/adr/0028-transient-network-ssl-resilience.md 第 111-113 行与第 129 行）：第 113 行是「现在做 / 留口子」这一节 in/out 对照的骨架句（v1.0 基线范围），与第 129 行「留口子不实现」构成范围决策的两半——它本身就是决策（哪些进 v1.0），并带「（v1.0）」的历史框定，删掉后第 129 行…
- [P36] docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md · 「> **状态**：本清单所列 v0.x BDD 入口层已按此物理删除（`bdd/` + `midscene/patches/` 连同 cuc…」 → 被误判要素：①精确指针「见下『迁移』」；②「确定性脚手架迁入 worker/」这一防误读护栏（脚手架不在删除之列、是搬迁）；③本 repo 的「决策 vs 实装」状态戳惯例。定位 docs/adr/0022 第 71 行，对照同文件第 42 行 `> **实现状态（v1.0 当前）**：…已落地…（`worker/` 下…，见下「迁移」）` —— 同一 ADR 内以引用块标注「决策已物理落地」是有…
- [P37] docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md · 「退役 bdd 时把它从 `bdd/` 移到 `worker/` 同目录（`novaact/worker/deterministic_step…」 → 被误判要素：历史框定 +（旧位置→新位置）迁移账本的精确指针。定位 docs/adr/0022 第 82 行，所在段落标题即 `**迁移（不删，改落 lib/ 或 worker/）**`，该段的功能就是逐项回答「v0.x `bdd/` 里的东西现在去哪了」——同段其余各项同构（`agentcore-sigv4.mts`、`workflow_setup.py` 落各引擎 `lib/`；`generi…
- [P39] docs/adr/0015-v1-positioning-smoke-not-regression.md · 「- **未点名不抓**（种类 B）：最左档定位的必然代价，接受。」 → 被误判要素：带指针的有意简短重述（权衡 + 决策）。定位 docs/adr/0015 第 36 行，「（种类 B）」本身即指向第 27 行节的术语指针，后半「最左档定位的必然代价，接受」是把第 30 行『v1.0 不解决，作为已知边界接受』与第 32 行『最左档定位的必然代价』压成一句的重述——正是红线里「带指针的简短重述是设计」的形态，也是本项目对 AI 读者的密度取向（在「已知边界」这个被检索…
- [P41] docs/adr/0025-plan-module-feature-to-jobs.md · 「- **keyword 判不出 = 拒绝猜（fail-fast，首轮 code-health 逼出）**：」 → 被误判的受保护要素 = 自包含血缘的事件描述（docs/adr/0025-plan-module-feature-to-jobs.md:79「首轮 code-health 逼出」）。CLAUDE.md 禁的是「只在当前对话/任务里成立的指代」（#1 修复 / 本轮那个 bug / WP3-A）——那类需外部上下文才能解引用；「首轮 code-health」是自明的事件描述（第一次代码健康度复盘），…
- [P42] docs/adr/0010-spike-as-apples-to-apples-benchmark.md · 「spike 阶段尚未固定（用例已验证通过即可），M2/M5 接入时应设 `logs_directory` 并 gitignore。」 → 被误判的受保护要素有三处，全在 docs/adr/0010-spike-as-apples-to-apples-benchmark.md:37 该尾句内：①历史框定 +why——「spike 阶段尚未固定（用例已验证通过即可）」是「当时」框定的 spike 范围判据（spike 的验收线只是用例跑通，故意不做持久化），属决策理由，红线「删决策理由 why / 历史框定不算 STALE」直接命中；本…
- [P43] docs/adr/0010-spike-as-apples-to-apples-benchmark.md · 「## 实测挖出的洞察（对 M5 报告统一关键）」 → 被误判的受保护要素 = 历史框定与 repo 级稳定术语，定位 docs/adr/0010-spike-as-apples-to-apples-benchmark.md:30（节标题）与 :35（弥合三条轴）。提案前提「M5 是悬空过程编号」被真值集证伪：CONTEXT.md:25 明确定义「里程碑（M1–M5 的工程推进）」为项目术语，且 repo 的既定惯例恰是「保留 M5 标签 + 加已落地…
- [P45] docs/adr/0019-feature-tags-scope-and-engine.md · 「### `@timeout:<N>`（job 墙钟预算——tag 体系的第三个成员，随 [0034](./0034-detached-bat…」 → 被误判的受保护要素 = 历史框定 +「为何它在这里」的骨架信息，定位 docs/adr/0019-feature-tags-scope-and-engine.md:10 标题括注。该 ADR 标题（:1）是「用 Gherkin tag 声明 scope 与 engine（G1/G2）」、开篇（:5）明说「声明**两类**配置元信息：会话作用域（scope，G1）与引擎选择（engine，G2）」、…
- [P48] docs/adr/0029-engine-artifacts-to-s3.md · 「- **~~S3 key 命名 ↔ `ResourceUri` `s3://` 形态~~（第一期已定，见上「第一期实现定论」）**：定为「S…」 → 被删的「定为「S3 key 镜像本地 run 树、与 report 同 `<prefix>/<run_id>/` 前缀、worker 报的 `s3://` ref 与上传 key 逐字一致」」承载两个受保护要素，且它本身并不 STALE（与「第一期实现定论」『S3 key 镜像本地 run 树』条逐点一致）：①「带指针的有意简短重述」——留口子索引的固定形制（划掉标题 + 见上指针 + 一行结论）…
- [P49] docs/adr/0032-fargate-execution-environment.md · 「**真 Fargate 校准（`stopTimeout`/grace 预算 + 中断抢传 + 干净退出）已完成**（4 次真跑，见下「真容器…」 → 提案要删的是整段（至「至此 Fargate 特有韧性 backlog 全部收敛」），而这段里至少三处受保护要素，压成一句「处置见下节」的导航句全部丢失：①**被拒方案带理由的简短重述**：「孤儿产物主动扫盘 reaper **经分析否决**（Fargate 下物理不成立——没传 S3 的残余随容器盘销毁、查 S3 捞不回，详见下「处置结论」孤儿 reaper 条）」——反模式/被拒方案 + 核心理…
- [P50] docs/adr/0032-fargate-execution-environment.md · 「## 最大风险：中断丢失在 Fargate 下严重升级（真做前头号待解）」 → 两部分都触红线。①标题括注「（真做前头号待解）」带时间框定（「真做**前**」=真跑落地之前，与「曾/原/当时」同族），读作历史定位成立，属「历史记录≠过时」保护面；且它是外部交叉引用的落点——0029「定位澄清」条写「为 **Fargate**（容器盘停即销毁、中断产物真丢，[0032] **头号待解项**）忠实预演」，删掉后该引用在 0032 内找不到对应措辞。②「**这是 SDK 调查比"能…
- [P52] docs/adr/0039-user-facing-surfaces-no-internal-references.md · 「- CLAUDE.md：代码纪律「产品面文案不带内部指代」与文档纪律「README / DEVELOPMENT 分层」两条压回规则 + 判据…」 → 被误判要素 = 精确指针 + 反向链登记，位于 docs/adr/0039-user-facing-surfaces-no-internal-references.md:70（「对既有文档与 code 的影响」节首条）。三点：①它比 Status 头（:3）更精确——Status 头只说「约定文件只留规则与指针」，此行登记的是「规则 + 判据 + 护栏 + 指向本 ADR」这一内容分工，提案自己承…
- [P53] docs/adr/0027-runreport-aggregation-index.md · 「- 行为与含 AI step 的用例**一致**（都产有效 RunReport），产物差异**合理**（确定性 step 本就不产」 → 被误判要素 = 关键不变量 + 反模式/防重复进坑护栏，位于 docs/adr/0027-runreport-aggregation-index.md:154-156（「纯确定性用例 → 空 report_index」节第三条）。①「行为与含 AI step 的用例一致（都产有效 RunReport）」是本节对空态的行为不变量：纯确定性 run 仍产出有效 RunReport、不退化成错误或缺失—…
- [P54] docs/adr/0013-cross-engine-sharing-boundary.md · 「**曾设想做成跨引擎共享层，实际落在核心库这一层**（下述三项各自的承载方式见本节末段）：」 → 被误判要素 = 精确指针（且承载纠偏功能），位于 docs/adr/0013-cross-engine-sharing-boundary.md:26 的括注「（下述三项各自的承载方式见本节末段）」。它不是「往下看」式噪声：本节末段（:31）的逐项映射是「报告归集=ReportStore/RunReport、会话生命周期=各 worker 内、跑批入口=核心调度+CLI」——其中「会话生命周期=各 …
- [P55] docs/adr/0013-cross-engine-sharing-boundary.md · 「即「跨引擎共享止于 `features/`」仍成立（worker 代码仍各属各引擎），公共设施落在**核心库**这一层、不靠跨引擎共享引擎代…」 → 被误判要素 = 让论证可跟随的骨架句 + 带框的有意重述（红线「有意重复≠冗余」），位于 docs/adr/0013-cross-engine-sharing-boundary.md:31 段末「即「跨引擎共享止于 features/」仍成立（worker 代码仍各属各引擎），公共设施落在核心库这一层、不靠跨引擎共享引擎代码。」。该段的论证链是「原前提（统一到一种语言）被 0023 证伪 → 承载…
- [P58] docs/adr/0001-scope-limited-to-english-ui.md · 「断言文本与页面文本的语言组合会放大抖动面。中文实测显示这条对 Midscene 的直白断言不成立（零抖动），只在刻意刁难的边缘题上出现（见下…」 → 被误判的受保护要素集中在 0001 line 16（「为什么这样划（按证据强度排）」第 3 条）：①**被证伪假设的护栏**——「断言文本与页面文本的语言组合会放大抖动面」＋「中文实测显示这条对 Midscene 的直白断言不成立（零抖动）」是「曾考虑过的假设 + 实测否掉」的完整成对记录，正是 CLAUDE.md「移除某方案时留一条『被拒+为什么』护栏，防未来重复进坑」保护的对象；提案对保留只给…
- [P59] docs/adr/0001-scope-limited-to-english-ui.md · 「- README 架构速览的范围句与「怎么写 `.feature`」节按引擎写语言支持与路由建议；两个引擎包的 README 各带一句语言支…」 → 两条被判为「施工流水」的「影响」条目经逐条对真值集核对**全部准确、且是精确指针**，删除即丢：①`README.md` 确有 `## 架构速览`（line 19，范围句在 line 49 按引擎写 Midscene 不限/Nova 限英文 + `@engine:midscene` 路由建议）与 `### 怎么写 .feature`（line 146）；两个引擎包 README 也确各带一句（`e…
- [P61] docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md · 「**剩余风险（spike 第一锤要坐实）**：」 → 被误判要素 = trade-off/风险评估骨架 + 历史框定，且「spike 第一锤」并非悬空坐标。定位 docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md：① 紧邻上一节末句「风险性质从「AWS 政策侧未知」变为「进程内 SigV4 fetch 接线是否字节级正确」——后者在我们掌控内」是本 ADR 选 SigV4 而非 bearer 的…
- [P63] docs/adr/0011-agentcore-browser-system-default-vs-custom.md · 「它适配的正是本 ADR「被测系统在内网/VPC」这一面，重议时从该结论起步而非从零调研。」 → 被误判要素 = 反模式护栏的段末有意收尾 + 对负向发现的适用性重申。定位 docs/adr/0011-agentcore-browser-system-default-vs-custom.md 末段：被删句紧跟在「但**够不到开发者笔记本**（Client VPN 对 IPv4 做 SNAT…），故在那里被缓作口子」这个负向结论之后——读者刚读到「那条路走不通」，极易顺推出「所以还得重新调研」，…
- [P64] docs/adr/0018-generic-steps-capability.md · 「**第一批 · 断言类（① 提取数据 + ⑤ 否定断言）—— 两个引擎对称通过**：」 → 事实前提被证伪：圈码清单在仓库内、是活的交叉引用，不是悬空过程编号。定位 features/wikipedia_robustness.feature:1「# v0.x 打磨 generic steps · 第二批：动作/判定的鲁棒性边界（② 多步骤复合动作 + ④ 模糊/主观判定）」，第 3-4 行进一步展开「② 一句话塞多步…」「④ 主观/无明确对错的断言…」，第 12 行注释「# ④ 模糊/主…
- [P65] docs/adr/0018-generic-steps-capability.md · 「## 刁钻用例暴露的边界（两批打磨）」 → 同 64 的事实前提问题：「第二批」不是只存在于本 ADR 的施工节奏残留，而是 in-repo 稳定物上的同名标签。定位 features/wikipedia_robustness.feature:1「v0.x 打磨 generic steps · **第二批**：动作/判定的鲁棒性边界」——该 feature 文件本身以「第二批」自我标识并长期存在于仓库；删掉 ADR 0018:27「（两批打…

## 五、对抗验证驳回的客观发现（8 条，存档）

- [7] docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md · 「注：合格图片的成功视觉应答尚未实证，留待 spike。」 → 两句都存在，但不构成未校准的自相矛盾：0008 是「决策当时 → 事后实测」结构的决策记录，该注位于「为什么这个选择更稳」的 spike 前叙述里，而同文件末尾有带日期的闭合节「## ✅ 已实测全通（2026-06-23，engines/midscene/spikes/）」，开篇即写「三段式自检全绿，本 ADR 的承重未知**已关闭**」，紧接第 1 段明确报「文本 "ok" + 视觉 "Red …
- [24] docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md · 「退役 bdd 时把它从 `bdd/` 移到 `worker/` 同目录（`novaact/worker/deterministic_step…」 → 被引原句是历史动作叙述、有意保留。0022 第 82 行整条以过去时框住：「**迁移（不删，改落 `lib/` 或 `worker/`）**…退役 bdd 时把它从 `bdd/` 移到 `worker/` 同目录（…）」，且它所在的「退役清单（B1 删除/作废的东西）」第 71 行也写「本清单所列 v0.x BDD 入口层已按此物理删除…确定性脚手架迁入 `worker/`」——记的是 B1 退役…
- [31] docs/adr/0016-execution-architecture-core-lib-run-model.md · 「组合根接线与 `iac_aws_backend` CDK 工程」 → 三点使原句在合理读法下仍为真、且提议改法引入新的不准确：①该行处于「版本切分（按完成线，非时间）」下的「**v1.1.0（云端执行）— ✅ 完成**」条、句首即「**已落地**」，是过去完成态的版本记录——v1.1.0 当时落地的工程确实叫 `iac_aws_backend/`；把它改成 `deploy_aws/` 会让 v1.1.0 的完成记录指向 v1.4（0037 决策 6）才存在的发行包目…
- [63] docs/adr/0037-distribution-and-packaging.md · 「「背景与问题」「现状实测」两节是**施工前快照、历史叙述**。」 → 逐条读了五处原句，全部已被自身句法框成施工前对照，不构成现状陈述：line 63「目标态文档里凡指命名真源模块**一律写** `gherkai_runtime.names`（当前 `gherkai/gherkai/names.py`）」——主句是目标态指令，且紧邻的 2a 表格列头就是「当前（施工前）」，本节内「当前」已被定义；line 77「CLI **加** `--version`（当前没有）…
- [70] DEVELOPMENT.md · 「+ adapters/{subprocess,fargate}_engine.py + adapters/cloud_launcher.py…」 → 文件确实存在（ls 核实 core/gherkai_core/adapters/_boto.py、adapters/run_store/arg_offload.py、engines/novaact/gherkai_worker_novaact/deterministic_steps.py、engines/midscene/src/{index,resolve-hook}.mts），但「树是穷举清单…
- [71] DEVELOPMENT.md · 「└── tools/                     ← 复用工具库（端到端真跑 / 跨真实边界验证 / 时序诊断 / 知识图刷新；…」 → 事实部分成立（git ls-files graphify-out = 236 个 tracked 文件），但根 DEVELOPMENT.md 的目录树是**精选导航树**、不是 tracked 顶层条目的完整枚举：git ls-files 的顶层还有 LICENSE、.gitignore、.gitattributes、.python-version 四个入库文件同样未列，且 `.claude/` …
- [87] CONTEXT.md · 「英文与中文各一组（`features/wikipedia_*.feature` / `features/wikipedia_zh.featu…」 → 两个支柱都不成立。①「glob 自我重叠」在合理读法下仍为真，且 `wikipedia_*.feature` 指英文探针组是本项目既有惯用简写——features/wikipedia_zh.feature 自己的头注就写「与英文探针 wikipedia_*.feature 同构」，即 code 侧真值集本身如此用词，读者不会把 zh 读进英文组（它被同句并列点名）。英文三文件（generic/as…
- [88] CONTEXT.md · 「_Avoid_: 把 spike 与里程碑（M1–M5 的工程推进）混用。」 → 原句在合理读法下仍为真，且「唯一一处」被证伪。该行是术语护栏（_Avoid_: 把 spike 与里程碑混用），语义内容 = spike ≠ 里程碑，这一区分至今成立；括注只是把「里程碑」指认为 M1–M5 这个系列，而 M1–M5 确曾是本项目的里程碑序列（ADR 0016:46 / 0027:5 的「原 M5」正说明它真实存在过），并非把版本切分说错。审计者的支撑「全仓仅此一处未框」不实：AD…

## 六、具名提纯审计记录（审计集 40 ADR + CONTEXT = 41 份）

沿用基线（自 ec12b4b 一字未动，记录见 `git show ec12b4b:docs/journey/0003-adr-density-baseline-audit.md`）：0007、0012、0021 三份判无。0014 基线漏审，本轮单独补审（见 P66 与已落改的首段 aiAssert 矛盾）。其余 37 份本轮层读：

### CONTEXT.md · proposal（6 提案）
- 层读：12 层（015585e..HEAD）：bf282de 立「推进器」词条；ad9fad7 +21 行——一次加 6 个 v1.4 词条，每条开头带「（设计已定、施工未启，ADR 0037/0038 Draft；当前是 X。）」施工态括注；7e1eca3 code 指针改发行重组后路径 + 把「三名分离」「版本单旋钮」两条括注翻成「已落地…待包化」；8bb961a 把「定位链」「steps 目录」两条括注翻「已落地」+ lib 路径改 src/lib；2750969 只改 _Avoid_ 里 --no-report 语义（GHERKAI_NO_ARTIFACTS）；e4d4baf +6/-3 新增「部署 provider」词条并给「版本单旋钮」括注再叠一条「skew 三态已落地」；e403f65 worker 镜像括注 → 「已落地…真账户实测待清」；90f7fa2 定位链第四级实测结论同时写进括注与正文 ④；4d557c5 wo…
- 附注：verdict=proposal。此处记「险成候选、按红线留下」的三处，以示未一刀切：① 「连锁失败读法」末句「历史：早期无 step 短路时，"error 后的 failed" 曾靠"按 status 顺序猜"加旁注（渲染层缓解）；现已升级为执行层短路 + 读 `shortcircuited` 精确判定」——「曾/现已升级」框定的旧世界，历史记录≠过时，不报；② 「骨架验证用例」里 82c0e8e 加的「英文与中文各一组（`features/wikipedia_*.feature` / `features/wikipedia_zh.feature`，后者兼作 UI 语言支持范围的测量夹具，ADR 0001）」——是稳定夹具指针而非施工流水，不报；③ 24943d8 新增的「使用方角色」六词条是单层新增、无括注叠加，逐句各自承载「帽子不是人」「执行与帽子正交」「提交者=权限类别不是帽子」等决策与边界，唯一与旧文重叠的部分已作为第 1 条 proposal 反向处理（删旧层、留新词条）。

### docs/adr/0001-scope-limited-to-english-ui.md · proposal（2 提案）
- 层读：窗口 015585e..HEAD 内仅 1 层：82c0e8e（ADR 0001 修订：按引擎划分）——整篇重写，标题/Status/「决策」节改按引擎划分，理由列表换腿，新增中文量化实测表 + 诊断表 + 「Nova Act 解除英文限定的条件（重议闸门）」+ 「影响」节，旧「扩到非英文 UI 的路径」三步清单被替换（其第 3 条换脑段整条搬进重议闸门）；随后整读当前 69 行全文。
- 附注：（提案见上）

### docs/adr/0002-midscene-not-driven-by-gpt55.md · none（0 提案）
- 层读：窗口 ec12b4b..HEAD 内仅 1 层：cab6a8e（ADR 0001 重写连带修漂移）——对本文件只在「次要理由」段插入一个带指针的括注（GPT-5 视觉弱项是 per-model 属性、非框架属性，见 0001「非英文的真实边界」）；随后整读当前 27 行全文。
- 判无依据：层读史实：窗口内唯一一层是句内插入一个带跨文档指针的定性括注，未在任何旧句上叠加、未留双层。最险成候选是 line 21 的「诚实存档（本 ADR 的判断反复）：Responses-only → 中途误判为"支持 chat-completions"（被假 200 骗）→ 实测纠正回 **不支持 chat-completions**。用户最初的"Responses-only"判断是对的。」——形状正是「先 X 后发现 Y 改回 Z」的判断节奏，但它承载受保护要素：同句尾的反模式「**只认响应 body，不认 HTTP 状态码**；web 核实 ≠ 账号实证」，而这条教训的证据锚就在紧上方 line 19（`bedrock-runtime` 裸 `/v1/chat/completions` 返回 `UnknownOperationException`——HTTP 200 但 body 是框架异常，「曾一度被误读为"通过"」），删掉箭头链教训就失去它反的那个具体假象；「曾一度被误读」本身是被框住的历史。其余各句皆为承重实证（400 原文、us-east-1 独有、Responses-only）或决策与出局理由（无 Response…

### docs/adr/0003-midscene-grounding-qwen3vl-bedrock.md · none（0 提案）
- 层读：区间 ec12b4b..HEAD 共 4 层，全部 git show 读差异（文件仅 23 行）：cab6a8e（0001 重写连带，改一处互链措辞）；3ae5d6d（+2 行，新增「待观察（上游代际）」段：官方标旧世代 + Bedrock 两区实查唯一 + 0009 约束下无升级路径 + 触发条件）；853d730（把原型期那句「后者尚未实证…是 spike 第一锤要坐实的」整句替换为「此后已端到端真验：wikipedia 10/10 零抖动，2026-06-23」，并把「未实测项」从「定位质量仅属推断」收窄成「量化基准（无 N 次抖动/精度数据）」+ 内联 0010 延迟实证，触发条件从「配置级（env 注入）」改为真值口径）；015585e（把「若 spike 实测定位质量不达标…」处置规则句从「待观察」段搬回「未实测项」段）。随后整读当前文 23 行。
- 判无依据：层读到的史实是两次都做了整句替换/整句移动、旧层零残留：853d730 把原型期的「视觉通道尚未实证」层就地换成「此后已端到端真验」并没有把旧句留在别处；015585e 把处置规则句从「待观察」段移到「未实测项」段，现文里该句确实只有一份（grep「不以离开 AWS 为出路」只命中「未实测项」段末）。整读后最险的候选是「**已在本账号实测（2026-06-22）**：用 IAM/SigV4 凭证向 `bedrock-runtime.us-west-2.amazonaws.com/openai/v1/chat/completions` 发真实请求…返回 HTTP 200」这一段，读着像「为什么是它」段「经实测发包确认…返回真实文本应答（HTTP 200）」的第二份；留它的受保护要素是 Accepted ADR 内联的自包含证据 + 前段没有的三条结论（模型访问已授予 / chat-completions 协议可用 / 本账号 region 可达）与凭证类型，紧接其后的「**鉴权方式**：上述实测走的是 SigV4」正是以它为锚展开的，删掉会让 0008 那条互链悬空。开头段「唯 qwen3-vl chat-completion…

### docs/adr/0004-novaact-iam-auth-via-workflow.md · proposal（2 提案）
- 层读：窗口 015585e..HEAD 内仅 1 层：8bb961a——对本文件只改一处路径 `engines/novaact/lib/workflow_setup.py` → `engines/novaact/gherkai_worker_novaact/lib/workflow_setup.py`；随后整读当前 29 行全文。
- 附注：（提案见上）

### docs/adr/0005-single-shared-feature-file.md · none（0 提案）
- 层读：7e1eca3（演进注里 core/parse.py → core/gherkai_core/parse.py）、8bb961a（同一行 engines/novaact/worker/run_scope.py → gherkia_worker_novaact/run_scope.py、midscene worker/run-scope.ts → src/worker/run-scope.mts）——区间内仅 2 层，且两层改的是同一行（第 15 行演进注）里的 code 指针，无内容增长、无后层覆盖前层的残留；随后整读当前 29 行全文。
- 判无依据：最险成候选是第 20 行「同一句自然语言 step 同时驱动了两个不同语言/不同大脑的引擎——本框架立身之本落地。」——它与第 9 行「本框架的立身之本就是「一套业务可读用例，两个 AI 引擎都能跑」」用词重合，读着像自我重复；留它的受保护要素：它是第 13 行「✅ 已实测（M2 起）」段的结论句，说明那次双 runner 加载实测「证明了什么」（把第 9 行的立论从主张变成已验证），属 Accepted ADR 内联的自包含证据，且整段被第 15 行演进注「下述「双 runner 各自加载」的 runner 层……已退役……下述 M2 实测是当时的验证脉络，保留。」显式历史框定。同理第 22-24 行「方言交集结论（本 ADR 预言的代价，已实证「可行但需注意」）」是对第 11 行 trade-off 的实证回填、第 26-29 行「M2 撞出的接线坑（固化备查）」是自包含实测细节且第 29 行自带「当时在 BDD fixture……该文件已随 BDD runner 退役删除……接线要求本身不变，现落在 worker 启动段」的取代框定——全部命中「历史记录≠过时」「实测证据不是沉积」。git 层也无叠加痕迹：区间 2 层…

### docs/adr/0006-form-a-two-subprojects-no-orchestrator.md · none（0 提案）
- 层读：窗口 ec12b4b..HEAD 内仅 1 层：40fe732（存量提纯落地）——对本文件删掉验证前的 hedge 旧层整条「⚠️ **重要不确定性（核实置信度 medium）**：…未验证——很可能是不同抽象层。不要据此认为…」，保留其下的「✅ 已实查证伪（见 0023）」定论；随后整读当前 20 行全文。
- 判无依据：层读史实：窗口内唯一一层就是把「未验证 hedge + 后来的证伪结论」这对双层压成单层（前层整条删、后层原样留），当前文里已无 hedge 残留。最险成候选是 line 12「工程形态 = 形态 A（两子工程并列），不是合成一个引擎、也不是单进程统一 runner。」——与标题、line 5 构成同一决策的三度陈述，但它是全文唯一点名两个被拒形态（合成一个引擎 / 单进程统一 runner）的句子，属被拒方案护栏；紧随的 line 13 也不重复，它给的是不上形态 B 的 why（复杂度不对等、收益不明、依赖尚未验证的断言哲学与链路全绿）。另一处 line 9 结尾「下述原决策脉络保留。」看似元话语，实为把 line 5「两套 Gherkin runner 各自加载、**不**设统一编排入口」框成历史的标记（0016/0022 已反转该立场），去掉则下文会被读成现状。

### docs/adr/0008-midscene-bedrock-auth-sigv4-selfsign.md · proposal（2 提案）
- 层读：窗口 ec12b4b..HEAD 内仅 1 层：40fe732（存量提纯落地）——对本文件删掉施工句「**第一个实验**：写好 SigV4 fetch 后，跑一次真实 Midscene `aiTap`/`aiAssert`（本地琐碎页面），一次绿灯即坐实自签接线全链路可用。」；随后整读当前 30 行全文。
- 附注：（提案见上）

### docs/adr/0009-maximize-aws-hard-constraint.md · none（0 提案）
- 层读：区间内仅 1 层：853d730（文档健康度复盘第四轮）——按 0009 自己「决定」段的登记要求，末尾新增整段「**已记录的例外**」（0035 ngrok，内联「SSM 方向相反 / IoT 两端 localproxy 不产公网 URL / AgentCore VPC 够不到笔记本」三条实查 + 例外面压到最小的四项边界），原有五段（硬前提、决定、已据此约束做出的选择、明确的非目标）逐字未动，纯追加、无覆盖残留。现文 17 行整读。
- 判无依据：最险成候选 = 第 12 行的整个括注「（注：gpt-5.5 的排除是另一回事——它在 Bedrock 内，但不支持 chat-completions，见 [0002](./0002-midscene-not-driven-by-gpt55.md)，与本 AWS 约束无关。）」：它挂在「已据此约束做出的选择」清单末条上，讲的却是一个**不属于**该清单的排除，形态上像离题旁白 + 对 0002 内容的完整重复。留它的受保护要素有两个、都在这句自身跨度内：① 反模式/防误读护栏——它是唯一一处阻止未来读者把 0002 的 gpt-5.5 排除算进「AWS 硬约束的战果」的句子，即防本约束被扩大解释（这条 ADR 的风险恰是过度归因，因为它是全项目选型的上位约束）；② 精确指针 [0002](./0002-midscene-not-driven-by-gpt55.md) 并给出真因「在 Bedrock 内、但不支持 chat-completions」，读者不必点开就能区分两类排除。次险 = 第 15 行例外条尾「例外面被压到最小：经可插拔 `TunnelProvider` 口子隔离、仅 `--expose-local` 显式启用…

### docs/adr/0010-spike-as-apples-to-apples-benchmark.md · proposal（2 提案）
- 层读：40fe732（删掉「## backfill 状态（spike 遗留项，v1.0 已落地）」整节 2 条 ✅ 已落地，替换成文末一行「spike→生产差异」）、853d730（「为什么值得记」里把「U2/U3 的「对标」要求」改成「项目立项时「两引擎须可对标」的需求」，去掉需求编号）——随后整读当前 41 行全文。
- 附注：（提案见上）

### docs/adr/0011-agentcore-browser-system-default-vs-custom.md · proposal（2 提案）
- 层读：区间内仅 1 层：015585e（doc-health 第四轮主观 18 项落地）——末尾新增整段「**VPC 模式的能力核查已做完，重议时先读、勿重做调研**」（前向指针到 0035「调研结论」③，内联 networkMode=VPC / vpcConfig 创建后不可改 / Client VPN SNAT 够不到笔记本），前 15 行逐字未动。故现文第 8 行属 ec12b4b 之前的基线层、区间内从未被触碰。现文 17 行整读。
- 附注：（提案见上）

### docs/adr/0013-cross-engine-sharing-boundary.md · proposal（2 提案）
- 层读：窗口 015585e..HEAD 内仅 1 层：8bb961a（阶段 2 worker 包化）——对本文件只改一处路径 `engines/midscene/lib/agentcore-sigv4.mts` → `src/lib/...`，无内容层增长；随后整读当前 35 行全文。
- 附注：（提案见上）

### docs/adr/0015-v1-positioning-smoke-not-regression.md · proposal（1 提案）
- 层读：38aa74e（术语规范化：行内 2 处「test engineer」→「测试开发」）、8bb961a（worker 包化后把确定性脚手架路径指针改真值 engines/novaact/gherkia_worker_novaact/... 与 engines/midscene/src/worker/...）——区间内 2 层都是单行原地替换，无内容叠加层；随后整读当前 49 行全文。
- 附注：（提案见上）

### docs/adr/0016-execution-architecture-core-lib-run-model.md · proposal（3 提案）
- 层读：区间 015585e..HEAD 共 6 层（先 --oneline/--stat 看层数与改幅，只对大改层 git show）：56d77d5（definition 行加 max_concurrency，2 行）；ad9fad7（Status 头加「0037 反转三处」+ 版本切分新增 v1.4.0 行，3 行）；7e1eca3（大改层，47 行：工程布局树按发行重组整树重画、新增「三个目录=三个发行包=三名分离」段、演进节加「命名注」、build_cloud_stores 条加反转标注、Status 头改「已校准」）；8bb961a（大改层，14 行：engines 子树按 novaact 包化/midscene ESM 重画 + run_scope 路径改 gherkai_worker_novaact / src/worker/*.mts）；e403f65（definition 行加 worker_variant/work…
- 附注：（verdict=proposal）逐条核过并有意留下的近候选：版本切分 v1.1.0 行末「曾是唯一剩项的**无状态跑批…已作为 v1.2 完成、真部署真跑通**（见下 v1.2.0 行 + 0034）」虽与紧邻的 v1.2.0 行重复，但候选跨度自身带「曾是唯一剩项」的历史框定（记录 v1.1 当时的剩项边界），按「历史框定不是过时」留；「现在不做」条的「**避免为想象中的云端预先盖机器。**（**已越过**：…）」是反模式护栏 + 纠正指针，留；演进节的「> **命名注**：本节沿用抽包当时的名字…」是 7e1eca3 有意加的历史换算注，留；决策 B 的 `build_engines` `artifact_s3` 形参删除段是「被拒方案+为什么」护栏，留。

### docs/adr/0017-cloud-execution-fargate-over-runtime.md · proposal（1 提案）
- 层读：40fe732（标题「## 诚实修正（grilling 挤掉的水分）」去掉括注「（grilling 挤掉的水分）」）、853d730（同一层做三件事：Status 头追加「倾向已落地为实态……」长句、开篇倾向句尾加「（此句为上云前的原始表述，保留作决策史……）」括注、「何时坐实」节前插一条 > 已落地演进注）——随后整读当前 35 行全文。
- 附注：（提案见上）

### docs/adr/0018-generic-steps-capability.md · proposal（2 提案）
- 层读：区间内仅 1 层：40fe732（存量提纯落地 31 条）——本文只改了 lead 一句，删「本 ADR 固化打磨出的能力清单、两个引擎对称映射、刁钻用例暴露的边界。」（与标题逐项重复的自述），正文各节（含「刁钻用例暴露的边界」两个批次小标题）逐字未动，即下列批次/圈码坐标是 ec12b4b 之前的基线层、迄今未进过任何提纯视野。现文 63 行整读；另 grep 全库确认「刁钻」只出现在本文第 27 行，0010 里的 ①②③ 是它自己关于报告产物的本地列表、与本文用例编号无关。
- 附注：（提案见上）

### docs/adr/0019-feature-tags-scope-and-engine.md · proposal（1 提案）
- 层读：d88f774（+4 行：新增「### `@timeout:<N>`」两条语义 + 「范围」节加「`@timeout:` 的实现落点」条）、853d730（「范围」节「语义已定」条补上 `@timeout:`、称「三个 tag」）——两层都是 @timeout 一条线的增补，前层内容未被后层覆盖、无旧描述残留；随后整读当前 71 行全文。
- 附注：（提案见上）

### docs/adr/0020-step-phrasing-default-ai-deterministic-scaffold.md · proposal（1 提案）
- 层读：区间内 2 层：24943d8（+2 行：角色边界节头加「角色正名与边界矩阵的单一真源现为 0040…本节保留当时的决策内容」指针）；38aa74e（5 行逐词替换：test engineer / test-engineer / Test engineer → 测试开发，含 Status 头）。沉积来自更早的「落地现状」追加层，整读当前文 40 行取证。
- 附注：（提案见上）

### docs/adr/0022-bdd-runner-retired-core-parses-thin-worker.md · proposal（3 提案）
- 层读：区间内 2 层，均单点替换：8bb961a（worker 包化，1 行——第 42 行「实现状态」块里的 code 落点 `engines/novaact/worker/deterministic.py` → `engines/novaact/gherkai_worker_novaact/deterministic.py`、midscene 侧同步）；38aa74e（术语 2 处：「教 test engineer 怎么加」→「教测试开发怎么加」、「test-engineer 角色」→「测试开发角色」）。沉积是此二层之前叠加的状态块与迁移段，整读当前文 93 行取证。
- 附注：（提案见上）

### docs/adr/0023-novaact-acting-python-locked-no-ts-core.md · none（0 提案）
- 层读：区间内仅 1 层：03ad86d（主观类 4 条落地）——本文只改 lead 一处，且该层本身即提纯动作：把伪逐字引用「『medium 置信、未验证』备用路径」改成概括「未验证备用路径」（因引号内表述已随 0006 提纯删除，逐字引用会变成假引用）。其余 37 行逐字未动。现文 38 行整读。
- 判无依据：最险成候选 = 第 26 行「`@aws-sdk/client-nova-act` 本 ADR 未独立核实成（npm 403、AWS v3 文档页空壳）；其存在记录于 [0006](./0006-form-a-two-subprojects-no-orchestrator.md)（含 `apiVersion 2025-08-22`、`endpointPrefix nova-act`），不是本 ADR 抓到的页面。」——句尾「不是本 ADR 抓到的页面」与句首「本 ADR 未独立核实成」同义，形态上是同一断言在一句里说两遍。留它的受保护要素：它是本 ADR **逐条标注证据归属/置信度**这套体系里的一环，且是该行唯一把 `apiVersion 2025-08-22`、`endpointPrefix nova-act` 这两个具体字段的出处判回 0006 的句子——删掉后「0006 的记录」与「本 ADR 的实查」界线只剩句首一处否定式表述，未来读者极易把这两个字段当成本 ADR 抓到的实锤（而本 ADR 的裁决 `NO-STILL-NEEDS-PYTHON` 标了「高置信」，误升级证据强度的代价正是它防的）；同族标注还有第 …

### docs/adr/0024-worker-core-protocol.md · proposal（4 提案）
- 层读：区间 015585e..HEAD 共 4 层，全部先看 --stat 再挑大改层 git show：731c407（+1 行，唯一实质内容层：新增「handler 内零 I/O」条，含 stderr BufferedWriter 非重入 + 首次 CI 真跑窄窗口证据 + 护栏测试）；7e1eca3（3 行，发行重组路径校准：core/core/adapters/fargate_engine.py→core/gherkai_core/…、core/wire.py→core/gherkai_core/wire.py，顺带把「core/schedule/wire/model」机械改成「core/gherkai_core/schedule/wire/model」）；4916589（4 处「烧钱」→费用/计费）；38aa74e（1 处「test engineer」→「测试开发」）。随后整读当前文 261 行，并对 175 / 191-1…
- 附注：（提案见上）

### docs/adr/0025-plan-module-feature-to-jobs.md · proposal（2 提案）
- 层读：542fe32（+1 行：step 顺序节加「keyword 判不出 = 拒绝猜」fail-fast 条）、853d730（+14 行：接口块加 timeoutS 字段注、新增「timeout 解析」节、test cases 补 2 条 timeout 项）、015585e（就地扩写 timeout 非法值那条为「非有限正数 / nan / inf」并同步 test cases 同一条）——三层都是同一条 timeout 线的原地增补/改写，后层覆盖前层同一行、无残句；随后整读当前 126 行全文。
- 附注：（提案见上）

### docs/adr/0026-schedule-module.md · none（0 提案）
- 层读：区间 015585e..HEAD 内只有 1 层：4916589（术语规范化，2 行：「真实烧钱」→「产生真实费用」、「永久占用并发槽位 + 烧钱」→「+ 持续计费」，已读 diff）。为判是否有叠加型旧层，另用 git log -S 定位：两处「⚠️」纠正注与 Status 头的 Partially-superseded 表述同出 b7228a1（ADR 0034 定稿、同批演进 5 条旧 ADR），一次落定；「治理旋钮 = 注入参数 + 保守默认（贯穿原则）」与「进程拓扑（澄清「几个地方」）」均出自 ae2002e（v1.0 schedule 设计落盘）原始层。然后整读当前 96 行全文。
- 判无依据：最险成候选 = 「## 治理旋钮 = 注入参数 + 保守默认（贯穿原则）」节：`maxConcurrency` / `failFast` / `gracePeriod` / `clock` 的「注入 + 保守默认」在上文已各说一遍（「并发上限」条「是**注入参数 + 保守默认**，不写死——本地全量可调高、配额紧可调低」、接口三条注入 bullet 的可测性理由），看着像第四遍复读。留它的受保护要素两条，都在这一节自己的跨度内：①它把散落的四个旋钮抽成一条命名的贯穿原则并挂指针「同 [0016] 组合根注入精神：策略由调用方（CLI/未来 WebUI）定，核心只认参数」——带指针的有意重述；②括注补了唯一的例外——「job 墙钟预算同守此精神、只是载体不同：由组合根按 tag/CLI 缺省解析定值后随 definition 进来，见上「超时兜底」」，正是第 27 行「**per-job 墙钟预算不在 `opts`**」的呼应，删掉就丢了「为什么偏这一个旋钮不在 opts」的骨架。史实层面本文也不是「后层覆盖前层却留残」型：0034 的纠正是 b7228a1 一次同批落的三处（Status 头 Partially-supers…

### docs/adr/0027-runreport-aggregation-index.md · proposal（1 提案）
- 层读：区间 015585e..HEAD 内只有 1 层：7e1eca3（发行重组后校准，3 处 code 路径指针改名：core/wire/schedule → core/gherkai_core/*、core/model.py → core/gherkai_core/model.py，叙事未动，已读 diff）。另用 git log -S 定位「这不是 walkaround」出自 8caac30（v1.0 RunReport 归集索引落地）原始层、非后层叠加。然后整读当前 174 行全文。
- 附注：verdict=proposal（低烈度，且据 git 层读该句自 8caac30 起未变、历经 40fe732 与 015585e 两轮提纯未被摘，故按密度重提而非当新发现）。附交代审过判留的：「但这暴露一个上游缺口（非本 ADR 范围）…大量用确定性锚点的团队，其 RunReport 人看部分会长期空」与留口子「确定性 step 产物可观测性」条看似一事两写，但前者给的是缺口的影响面（为何值得开口子）、后者给的是与 0036 的划界（跑前发现 vs 跑后可见），各承载不同要素，不动。

### docs/adr/0028-transient-network-ssl-resilience.md · proposal（2 提案）
- 层读：区间内 2 层，均逐词替换：7e1eca3（2 行：`core/wire.py` → `core/gherkai_core/wire.py`、`core/errors.py` → `core/gherkai_core/errors.py`）；4916589（2 行：「烧钱」→「持续计费」类措辞）。沉积来自此二层之前的多轮真跑追加（静默超时根治 / 血缘回传 / Midscene 两窗口 / step 短路都是后续轮次往「留口子」节里追加的），整读当前文 143 行取证。
- 附注：（提案见上）

### docs/adr/0029-engine-artifacts-to-s3.md · proposal（3 提案）
- 层读：区间 015585e..HEAD 内只有 1 层：7e1eca3（发行重组后校准，仅 2 处 code 路径指针 core/model.py→core/gherkai_core/model.py、compose.py→runtime/gherkai_runtime/compose.py，叙事未动，已读其 diff）。为定位「留口子」两条的年代，另用 git log -S 读了层位：「是否细分」出自 e0718d3（ADR 拆分建文，真 Fargate 之前）；「act 粒度即时抢传 / botocore retry vs grace / 中断韧性」出自 eafa48e（第一期上传落地，抢传尚未做）；抢传四级由 cd89d92 写入正文。然后整读当前 118 行全文。
- 附注：verdict=proposal。附交代两处审过但留下的：「固有残余（不救）」三细目（summary 154B / Midscene 当前 scenario log / act_*_traces.json 盲区）逐条带触发条件、评估过的补救与否决理由 + 「治本非再反推一个名字」的反模式，是被拒方案与自包含证据；「调查依据（SDK 源码逐行核实，2026-06…）」全节是带文件行号的事实锚点，属 Accepted ADR 内联证据，均不动。

### docs/adr/0030-realtime-persistence-seam.md · proposal（4 提案）
- 层读：区间内 2 层，均为逐词替换、不动结构：7e1eca3（16 行：`core/persist.py`/`core/ports.py`/`core/core/ports.py` 等 code 指针改 `core/gherkai_core/*`，`core[aws]` → `gherkai-core[aws]`）；4916589（4 行：「烧钱」→「持续计费」、「不烧引擎钱」→「不产生引擎费用」）。沉积由此二层之前的多轮叠加留下（决定六/七与 0034 落地的追加层），整读当前文 221 行取证。
- 附注：（提案见上）

### docs/adr/0031-job-lifecycle-states-and-severity.md · none（0 提案）
- 层读：区间 015585e..HEAD 共 3 层，全部 --stat + git show 看差异：7e1eca3（16 行，全在 touch points 段做路径校准 core/model.py→core/gherkai_core/model.py、cli/cli/*→cli/gherkai_cli/*，无一行加/改内容）；8bb961a（1 行，engines/novaact/worker/run_scope.py→engines/novaact/gherkai_worker_novaact/run_scope.py、midscene/worker/run-scope.ts→src/worker/run-scope.mts）；4916589（1 行「烧钱」改述）。随后整读当前文 196 行。
- 判无依据：区间内三层全是机械改名/术语替换（7e1eca3 的 16 行只动 touch points 的模块路径、8bb961a 只动两个 worker 文件名、4916589 只动一个词），零内容叠加，故本区间不可能留下「后层覆盖前层却没删」的残留。整读后最险的候选是决定六表格后的收尾句「两级都复用 `Status.SKIPPED` 表「没跑」，语义一致、只是层级不同；`shortcircuited` 布尔进一步标出 step 级「为什么没跑」」——留它是因为它承担表格给不出的功能：那张表只列两级的差（谁 skip / 有没有 StepResult / 承载形态），这句才说清「同一枚举值跨 job 级与 step 级是有意复用、不是撞名」，直接回接决定一「加进同一个 `Status` enum（而非新开 enum）」那条决策。次险的是「core 内态、不进 wire」在决定一、决定一·补、决定四、决定六出现四次，但四处各有不同承重：决定一说赋态处 + aborted 只活 job 级、决定一·补把 pending/running 也纳入同一约束、决定四是「0024 线协议不改」这个显式 no-op 决策 + 指回 0024 澄清条…

### docs/adr/0032-fargate-execution-environment.md · proposal（2 提案）
- 层读：区间 015585e..HEAD 内只有 1 层：4916589（术语规范化，1 行：「泄漏有上界、非无限烧钱」→「泄漏有上界、不会计费失控」，已读 diff）。为判「进度看板」段是否叠加层，另用 git log -S 定位并读差异：「Fargate 特有韧性 backlog」出自 3eed51e（reaper 否决），a20f88a（退化网络真验）又整段改写同一句（旧文「仍留待的只剩：上传幂等/可续传在退化网络下实测、孤儿产物恢复的主动扫盘实现」→ 新文删掉退化网络项、补「✅」）；「真做前头号待解」出自 e0718d3（ADR 拆分建文）。然后整读当前 75 行全文。
- 附注：verdict=proposal。附交代留下的近似候选：「实测覆盖边界（诚实声明）」一段（4 次真跑 act 均短、未撞上最坏长 act）读着像复述实测数据，但它承载的是证据边界与「结构性残余非被实测排除」的诚实声明（受保护的自包含证据 + 不变量适用面），不动；结论 3 的「适用面注记」（只在有人发停止时生效、三路推进器各自的发起者）同理是不变量适用面，不动。

### docs/adr/0033-iac-aws-backend-and-composition-wiring.md · proposal（3 提案）
- 层读：11 层（区间 015585e..HEAD）：3704fef/3e52fbe（vpc context 不入 state 护栏 + 去「现网」环境备注，各 1 行）→ ad9fad7（0037/0038 立 Draft，Status 头首次写入长「被取代面」枚举，含三处「默认建新」失效清单与「按 0038 权限面增量更新」两条前瞻校准指令）→ 7e1eca3（10 行：全篇 code 路径指针改新真值 core/gherkai_core、runtime/gherkai_runtime、cli/gherkai_cli）→ 8bb961a（8 行：镜像入口改 python -m / node dist/bin.mjs，novaact/midscene 源路径改包内）→ e4d4baf（18 行，最大层：定位节与资源清单 7. 就地加 0037 历史注、VPC 节加历史注块、部署方权限登记、iac README 指针改 deploy_a…
- 附注：（提案见上）

### docs/adr/0034-detached-batch-reconciler.md · proposal（1 提案）
- 层读：区间 015585e..HEAD 共 4 层，改幅均 ≤6 行（--stat 后逐层 git show 全读差异）：56d77d5（机制四整段替换——原「`max_concurrency` 的真源按档分层（实装现状）」一整段被「随 definition 走 + 推进器侧 cap」取代，并新增独立的「**曾反其道（决策反转记录）**」段承接旧决策与被证伪的假设）；bf282de（核心思想「reconciler（投影器 + 推进器）」句改为「reconciler 机制（投影 + 推进）」+ 三层消歧括注指 CONTEXT）；7e1eca3（Engine port 演进节的 code 指针 `core/ports.py` → `core/gherkai_core/ports.py`）；4916589（用语替换 3 处：烧部署方账单→计入部署方账单、无限烧钱→计费失控、空转烧钱→空转计费）。整读当前文 260 行。
- 附注：（verdict=proposal）本文密度极高，除 Status 头那层施工清单外逐段核过、有意留下：① 机制四那段的层读史实是「后层整段替换前层、零残留」——56d77d5 把旧的「真源按档分层（实装现状）」整段删除、旧决策以「**曾反其道（决策反转记录）**」独立段重述并写明被证伪的假设（「同一部署下各 run 无理由不同」被并行度随 scope 结构而异证伪），不是叠加括注；② 最险成候选是「## 四个关键机制（均已实装：机制二/三/四有地基实测支撑，机制一从 [0024] seq 不变量推导、独立键空间存取由单测覆盖 `test_sqlite_event_log`/`test_cloud_reconcile`）」——「均已实装」看着是施工态，但括号其余部分逐机制标出「真跑支撑 vs 推导+单测」的证据边界（绿≠对分流），删不得；③「**已补真验**：`status --wait` 接力 + Stream 丢投 → **已真验**（复现法与结果见「重议闸门」丢投条）…」同属证据边界且用指针避免复述；④「**exitCode 落值延迟兜底（防御性冗余）**…实测见下 H1/H2**（数字集中在地基实测节，不在此复述）」…

### docs/adr/0035-local-app-testing-via-tunnel.md · none（0 提案）
- 层读：区间内 2 层，均逐句整句替换、无残留：7e1eca3（发行重组校准：Status 头 + 决策 1 的 `gherkai/gherkai/tunnel*.py` → `runtime/gherkai_runtime/`，3 处路径，叙事不动）；56d77d5（并发打通：TTL「求和而非取 max」条整段重写，把被真实使用证伪的「cloud 并发恒 1」前提连同论证一起换成「对任何并发取值都是保守上界」；核查 grep「恒 1」「MAX_CONCURRENCY」在本文归零，旧前提无遗留句）。然后整读当前文 81 行。
- 判无依据：最险成候选 = 决策 1 第四条把 AWS 无等价物三条事实重列一遍：「ngrok 是 AWS 外的第三方 SaaS，但『开发机 → 云端浏览器』的入站通道在 AWS 内实查无等价物（SSM 端口转发方向相反；IoT Secure Tunneling 两端 localproxy、不产公网 URL；AgentCore Browser VPC 模式够不到开发者笔记本，已评估并缓——见调研结论③与被拒/被缓方案）」（第 35 行），与调研结论③④（第 22/24 行）字面重合。留它的受保护要素：同句开头「本项是对 0009『最大化用 AWS』的显式例外（按 0009 要求登记）」——登记条须在例外发生点自包含（不能只指调研节），且括注内已带「见调研结论③与被拒/被缓方案」精确指针，属带指针的有意简短重述。第二险 = 第 56 行「（曾是恒定 1h 且没有任何生产写入者：默认 job 预算 300s 下约 12 个 job 起就超。）」——「曾」框住的旧世界 + 内联量化反例，是「为什么不能拍常数」的证据。第三险 = 第 65 行「两 worker 各几行改动（URL 替换那半边才是 worker 零改动）」，看似施工工作量，实为对…

### docs/adr/0036-deterministic-capability-discovery.md · none（0 提案）
- 层读：区间 015585e..HEAD 共 2 层，均 1 行、--stat 即足：38aa74e（「test engineer」→「测试开发」）、4916589（「烧钱」→零费用/计费）。随后整读当前文 54 行；并从 015585e 的 commit 层读得知「plan 命中标注」是那一笔才纳编为决策 4 的。
- 判无依据：区间内只有两个一行术语层，零内容叠加、无施工节奏可残留。整读 54 行后最险的候选是 Status 头尾巴「清单查询（`list-deterministic`）与 plan 命中标注均已实现」——形似施工状态入头；留它是因为决策 4「plan 命中标注」是后来才纳编进本 ADR 的（015585e 层读可见），这句是全文唯一交代「决策 3 与决策 4 都是已落地范围、不是前向留口子」的地方，且点的是稳定 CLI 面 `list-deterministic` 而非施工步骤/批次。第二险是 0022「设计要点」节「匹配放 worker，不放核心」条的指针出现三次（决策 2 第三条、决策 4 引言、被拒方案「外置清单文件」），但三处各挂不同机制：dump 模式为何与该红线相容（core 只转述、不持有 pattern）、CLI 侧复刻匹配为何是该红线的漂移面（`(?<n>)` vs `(?P<n>)` 方言）、清单文件若被 CLI 用于匹配为何即违该红线——各自是带指针的简短重述，属有意重复。另 4 条「plan 命中标注」下的子弹全带 why 或契约校准（「plan 的承诺从「不起 worker」校准为「零 AWS、零花费、零副…

### docs/adr/0037-distribution-and-packaging.md · proposal（4 提案）
- 层读：共 16 层（015585e..HEAD）。ad9fad7：Draft 一次成形 267 行（全文骨架，含「落地次序」「校准清单」两节）。8bb961a 阶段 2 worker 交付（原地改 4 行）、2750969 --no-report 改口（2 行）、e4d4baf 阶段 4 deploy（16/15，整行替换 Status/2b/决策 6/决策 7）、2958c24 CI 发布链 + metadata=true 修正（16/15 的另一半 + 1 行）、a5bcd72 / 2720e20 / eed391e / 8322963 各 1–3 行把真跑证据内联进实测项、90f7fa2 fd 预演定第四级存废（只改 4 行：决策 3 第 4 级、落地次序「期外/按需」、实测项 2、重议闸门）、9a201ae npm trusted publishing（1 行）、3a82ef2 GHCR 首发 public 改口（2 行）、5…
- 附注：（提案见上）

### docs/adr/0038-worker-image-delivery.md · proposal（7 提案）
- 层读：12 层（区间 015585e..HEAD）。ad9fad7 建文（Draft，191 行：概念模型/命令族/push-worker 八步/deploy 四步/不变量/运行时与 preflight/权限面/被拒方案/实测项清单/落地次序/校准清单）；e4d4baf 1 行（记 WORKER_TEMPLATE_ARNS 接缝现状）；e403f65 实装层（19+/17-，原地替换：Status Draft→施工态、步 2 加多平台缺口、步 8 加「实装次序细节」、四步加 dev 版跳过基底/重派生保留 pushed_at、权限面加 ecr:DescribeImages 去 sts:GetCallerIdentity、容器引擎节由 tools/build_push_workers.py 改 container.py、校准清单四条打（已完成）、实测项 6 加证据 + 新增第 7 条）；eed391e 真账户抓修（步 5 限定同 var…
- 附注：verdict=proposal，不适用。

### docs/adr/0039-user-facing-surfaces-no-internal-references.md · proposal（1 提案）
- 层读：8b66ad5（区间内唯一层，72 行一次落盘：一条原则两个面、产品文案面范围与例外、README/DEVELOPMENT 四层表、两条护栏测试、代价与权衡、被拒方案、重议闸门、对既有文档与 code 的影响）。git log --oneline/--stat 确认区间内无第二层，无后层覆盖前层的叠加史；随后整读全文。
- 附注：verdict=proposal。附交代审过判留的三处：①「用户的判断（本 ADR 的起点，用户自己先改了一条 `compose.py` 文案）」是决策来源与触发事件的自包含描述（决定重议门槛），留；②「（曾因 TS 表更松漏掉一处「组合根装配错误」）」「两轮对抗核验都在这一档抓到过遗漏（runtime 页面整篇行话、`--grace` 漏标「仅 run」、定位链顺序写反）」是护栏为何长这样的内联证据，留；③「实装时顺带的原则性修正：Nova worker 的信号 handler 曾在 handler 内 `log()`…」带「曾」框定 + 交去 0024 的指针，属历史框定，留。

### docs/adr/0040-consumer-role-model-and-terminology.md · proposal（1 提案）
- 层读：24943d8（区间内唯一层，86 行一次落盘：四顶帽子与正名表、帽子不是人、跑法权限梯、边界矩阵、术语真源与立新角色门槛、代价、被拒方案、影响）。git log --oneline/--stat 确认区间内无第二层、无后续修补，故不存在「后层覆盖前层」的叠加史；随后整读全文。
- 附注：verdict=proposal。附交代两处审过判留的：①「用户补充的事实：本地开发时同一个人常在写被测应用代码与对应的 step 代码之间切换，build 完自己推——**角色重合是常态、不是例外**」——出处标注像起草期流水，但它标记了「这条是使用方给的领域事实、非推导所得」，直接决定决策 2 的重议门槛，属自包含的事实来源声明，留；②Status 头「README…与 CONTEXT.md…是本 ADR 的派生视图，改这里再改那里」与决策 5 第一条的重叠，我判为分工不同（Status 头是维护告示、决策 5 是「单一真源」这条决策本身），非副本，留。
