# 0037. 分发与打包：PyPI 多包 workspace（uv-first）+ `gherkai deploy` 进 wheel

> **Status:** Draft —— 决策已对齐；**施工态**：决策 1–4 已落地（发行重组、worker 交付），决策 6/7/8 已实装（`gherkai deploy`/`destroy` + provider 发现、skew 三态、CI 发布链文件、两态基底 Dockerfile），实测项 4（真账户 deploy）/ 5（真 tag 发布链）未清、PyPI 首发未落。**翻 Accepted 的门槛**：①下「实测项」清零；②发行重组 + PyPI 首发落地；③校准清单逐条完成——[0016](./0016-execution-architecture-core-lib-run-model.md) 布局图/`build_cloud_stores` 条 extra 表述、[0033](./0033-iac-aws-backend-and-composition-wiring.md) IaC/VPC 表述（两者 Status 头已反向链）、本 ADR 自身的现状快照（「背景与问题」「现状实测」表、决策 2a 表「当前」列改为历史表述）、以及下「对既有文档与 code 注释的影响」节列出的各项；④去掉 0016 Status 头与 0033 Status 头里**属于本 ADR 的那一处**「（Draft，决策已对齐、未实装）」标注（0033 头里 0038 的那一处由 0038 自己翻牌时去掉）。**worker 镜像的交付**（基底/variant/推送注册）是独立子系统，另立 [0038](./0038-worker-image-delivery.md)，本 ADR 只定两层分工与基底 registry、其余全部指向它。

## 背景与问题

**既有 ADR（0001–0036）没有一条讨论「这个工具怎么分发」**——这是真空，不是待推翻的旧决策。唯一擦边的挂钩点是 [0033](./0033-iac-aws-backend-and-composition-wiring.md)「留待」节里被显式 defer 的「build & push ECR 全自动 CI（需先定仓库托管 + CI 凭证方案）」；仓库托管现已确定（github.com/zhiyanliu/gherkai，公开），前置条件成立。

当前（施工前）唯一的安装路径 = clone repo，在 repo 内建**四套**隔离环境（`cd cli && uv sync`、`engines/novaact` 下 `uv sync`、`engines/midscene` 下 `npm install`、云端部署再到 `iac_aws_backend` 下 `uv sync`），从 `cli/` 目录 `uv run python -m cli …`。README 与各子工程 README 都只教这一条；`cli/pyproject.toml` 声明了 console script `gherkai`、`cli/README.md` 有一处 `pip install cli[aws]` 的口吻，但没有任何文档教用户走到「安装后」那一步，且这条路**当前走不通**（下）。

### 现状实测（本 ADR 的证据基座，均可复现；施工后成为历史快照）

| 实测 | 结果 |
|---|---|
| `uv build` 出的 `cli-0.1.0` wheel 元数据 | `Requires-Dist: core` / `Requires-Dist: gherkai` **裸名**——`[tool.uv.sources]` 的 path/editable 源不进发布元数据（`--no-sources` 产出字节相同，不存在「安全构建 flag」） |
| 安装该 wheel | `× No solution found … there are no versions of core and gherkai==0.1.0 depends on core`——PyPI 上 `core` 名被一个 2011 年发布、**零文件**的僵尸包占着（version 1.0.1、无 summary、无 URL），我们永远拿不到这个名字，且对方随时可上传文件把「装不上」变成「装错包」 |
| 装进干净 venv 后跑 local | `gherkai/gherkai/compose.py` 的 `repo_root()` = `Path(__file__).resolve().parents[2]`、无任何 env/flag 覆写口（生产侧唯一调用点在 `cli/cli/__main__.py`）；venv 里它指向 `<venv>/lib/python3.13`，两个 worker cmd 指向不存在的 `engines/novaact/.venv/bin/python` 与 `engines/midscene/worker/run-scope.ts`。实跑：`plan` 成功但标注降级（只依赖 gherkin 解析，[0036](./0036-deterministic-capability-discovery.md) 决策 4 的 best-effort）、`list-deterministic` 退 2 带「运行环境未装」文案、`run` 每个 job 报 `engine_error: 起 worker 失败` |
| 装进干净 venv 后 `submit --backend cloud` | **不依赖 engines 目录**——submit 路径只做 preflight + 写 definition，根本不建 engine（`build_fargate_engines` 是 `run --backend cloud` 与 Lambda 侧的事，且只用 `gherkai.names` 命名规则）。`repo_root()` 的其余消费点有三处、都不在 engine 装配里：`_submit_local` 与 `--expose-local` 的 tunnel-watch 都把它作子进程 cwd；`load_feature` 用它派生 feature 的 uri（= `scenario_id`/`scope_id` 的前缀）——wheel 装法下 feature 不在其下、退用绝对路径，scope_id 形状随安装形态与 CWD 漂移。「wheel 用户能提交到已部署的云端、但跑不了 local」是当前代码的真实形状 |
| 顶层 import 包名碰撞（`core`/`cli`） | 与另一个同样带顶层 `core/` 的发行包同装：pip/uv **零告警**、两包文件合并进同一个 `site-packages/core/`、`__init__.py` 被静默覆盖；卸载对方时按其 RECORD 删掉 `core/__init__.py`，我们的包退化成隐式命名空间包、`from core import X` 半死不活。PyPA 明文：发行名与 import 名之间不强制任何关系 |
| 部署后端 | `iac_aws_backend/stack.py` 现场 `copytree` 仓库相对路径 `../lambdas`、`../core/core`、`../gherkai/gherkai` 拼 Lambda asset，再在 synth 时**联网**从 PyPI `uv pip install --target` 装 `gherkin-official`（boto3 靠 Lambda runtime 自带）；`cdk.json` 的 app 是 `uv run python app.py`；`cdk` CLI 不在任何 Python 依赖里、靠 npm 全局安装。IaC 工程假定自己躺在 monorepo 里 |
| 版本 | **五份** pyproject（`cli`/`core`/`gherkai` 三个发行包 + `engines/novaact`、`iac_aws_backend` 两个非包工程）全 `0.1.0`，`engines/midscene/package.json` 另写 `1.0.0`——六处手写版本、零真源；而 [0016](./0016-execution-architecture-core-lib-run-model.md) 版本切分已按 SemVer 宣布 v1.0–v1.3 完成，叙事完全脱钩 |
| 依赖共解 | `nova-act>=3.4.187.0` + `boto3>=1.34` + `gherkin-official>=31` + `aws-cdk-lib>=2.150` 一个 venv 内 `uv lock`：107 包**零冲突**——「worker 必须独立 venv」不是依赖冲突所迫 |

### 业界现状（2026，为选型提供的外部事实；一手来源登记在 [docs/REFERENCES.md](../REFERENCES.md)「分发与打包」节）

- **PyPI + uv 是事实默认**：uv 月下载量约为 pipx 的 28 倍（pypistats，2026-08 采样）；pipx 自己加了 uv backend；抽样的同类 Python CLI（harlequin / posting / llm 三个 README）均以 `uv tool install` 领头、pipx 作回落。PyPA 官方指南仍只写 pipx——官方与生态已分叉，本项目跟生态。
- **`uvx <name>` 把 `<name>` 同时当发行名与命令名解析**（实测：发行名 `gherkai-cli` + 命令 `gherkai` 时 `uvx gherkai` 直接失败）→ 用户敲的那个发行包必须叫 `gherkai`。
- **uv 不会把 path/workspace 依赖翻译成版本 pin**（astral-sh/uv#9811，`needs-design`、至今 open）；生产级绕法 = pydantic-ai 的形状：`uv-dynamic-versioning` 既从 git tag 算版本、又在 build 时经 hatch metadata hook 渲染 `pydantic-ai=={{ version }}`（`clai` 2.31.1 在 PyPI 上的元数据即 `Requires-Dist: pydantic-ai==2.31.1`）。
- **同形工具的分工**（CLI + 用户自部署后端 + worker 容器）：Chalice 把 IaC 塞进 wheel 变 `chalice deploy` 并留 `package --pkg-format cloudformation` 导出阀；Dagster「chart 版本 = 包版本，镜像 tag 缺省跟 chart」一个旋钮；Prefect 用一句操作规则替代兼容矩阵；**内容属于用户的镜像一律由用户构建**（Dagster user-code deployment / Prefect flow image），内容属于维护者的由维护者发布。
- **Homebrew core 门槛**：≥75 star 或 30 fork，且仓库 ≥30 天；本仓库不达。第三方 tap 是第二个发布面。

## 决策总览

| 交付物 | 通道 | 版本 | 谁构建 |
|---|---|---|---|
| `gherkai`（CLI） | PyPI，uv-first | git tag，单一旋钮 | 维护者 CI |
| `gherkai-runtime` / `gherkai-core` | PyPI，被 `==` lockstep pin；CLI 用户不直接装（集成方按层直依赖，见 2a） | 同号 | 维护者 CI |
| `gherkai-worker-novaact` | PyPI，经 CLI extra `[local]` 装进 **同一个** venv | 同号 | 维护者 CI |
| `@gherkai/worker-midscene` | npm（scope `@gherkai`） | 同号 | 维护者 CI |
| worker **基底镜像** ×2 | **GHCR**（与 repo 同屋檐），linux/amd64，immutable `:X.Y.Z` | 同号 | 维护者 CI |
| worker **定制镜像**（基底 + 使用方 steps，按 variant 多套并存） | 使用方私有 ECR；机制全在 [0038](./0038-worker-image-delivery.md) | 跟 CLI | 使用方本地 build，部署方 `gherkai deploy push-worker` 推送注册 |
| `gherkai-deploy-aws`（IaC + Lambda handler 源 + worker 镜像推送） | PyPI，经 CLI extra `[deploy-aws]`；命令 `gherkai deploy` / `destroy` 及 worker 镜像族（0038） | 同号 | 维护者 CI |
| `features/`（示例）· `tools/` · `docs/` | 不分发 | — | — |

八条决策展开如下。

## 决策 1：交付物按打包技术划分，worker 运行时是硬核

四类交付物、四种打包技术：**Python 包**（wheel）、**worker 运行时**（双形态：local = 宿主机上的 venv / `node_modules`；cloud = 容器内容物）、**worker 镜像**（docker）、**IaC**（要被执行的工程，不是库）。「通过 uv 分发」只覆盖第一类；**第二类是整个问题的硬核**——同一份 worker 代码要以两种形态交付，cloud 半已有容器这个答案（其交付机制在 [0038](./0038-worker-image-delivery.md)），local 半（多语言子进程环境）wheel 装不进去。决策 3 专门解它。

## 决策 2：Python 侧 = uv workspace 多包发布，PyPI + uv-first

### 2a. 三名分离：发行名 / import 名 / 命令名各自取，约束只有一条

| 发行名（PyPI） | import 包 | 角色 | 当前（施工前） |
|---|---|---|---|
| **`gherkai`** | `gherkai_cli` | CLI 皮，命令 `gherkai` | `cli` / `cli` |
| `gherkai-runtime` | `gherkai_runtime` | 产品本体 = 组合根共享层（含命名真源 `names`） | `gherkai` / `gherkai` |
| `gherkai-core` | `gherkai_core` | 窄腰 | `core` / `core` |
| `gherkai-worker-novaact` | `gherkai_worker_novaact` | Nova Act worker 运行时，console script `gherkai-worker-novaact` | `engines/novaact`（venv 规格，无 build-system） |
| `gherkai-deploy-aws` | `gherkai_deploy_aws` | AWS 后端供给（CDK + Lambda handler 源）+ worker 镜像推送注册（0038） | `iac_aws_backend/` + `lambdas/`（非包工程） |

- **唯一硬约束：用户敲的发行名 = 命令名**（`uvx` 解析规则）→ CLI 发行包叫 `gherkai`，当前的中间层 `gherkai` 让位改 `gherkai-runtime`。目标态文档里凡指命名真源模块一律写 `gherkai_runtime.names`（当前 `gherkai/gherkai/names.py`）。
- **import 包全部带 `gherkai_` 前缀**：`core`/`cli` 作顶层 import 名是静默合并/互删的碰撞源（见实测）；改名是机械 sweep（`from core.` → `from gherkai_core.`），随发行重组一次做完。
- **发行名带 `gherkai-` 前缀**：PyPI 无 scope，前缀是唯一命名空间手段；`gherkai-cli`、`gherkai-worker-midscene` 两个名字作**防混淆占位**（前者是用户最自然的误猜，后者防人以为 midscene worker 是 pip 包），永不发真内容。
- **多包而非单包**：集成方按层引用——未来 WebUI 只依赖 `gherkai-runtime`、第三方只解析 feature 就依赖 `gherkai-core`（零 boto3）、Lambda asset 只装 runtime。单发行包（三 import 包一 wheel）曾是备选（省掉 pin 机制），因「按层引用」这个真实需求被拒；pin 机制由 2b 解决后单包的唯一优势消失。
- **分层不动**：`gherkai_cli → gherkai_runtime → gherkai_core` 的依赖方向、窄腰红线、组合根注入（[0016](./0016-execution-architecture-core-lib-run-model.md)）全部保留，本 ADR 只动名字与打包边界。

### 2b. 版本：git tag 唯一真源，兄弟包 `==` lockstep pin，不做兼容矩阵

- **git tag `vX.Y.Z` 是唯一版本真源**，pyproject / package.json 不再手写版本号（当前六处手写版本作废）。构建后端 hatchling + `uv-dynamic-versioning`：`[tool.hatch.version] source = "uv-dynamic-versioning"` 派生版本；`[tool.hatch.metadata.hooks.uv-dynamic-versioning] dependencies = ["gherkai-runtime=={{ version }}"]` 在 build 时渲染精确 pin；`[tool.uv.sources] gherkai-runtime = { workspace = true }` 让本地开发走 path。三段与 pydantic-ai `clai` 的生产配置同形。
- **`[tool.uv-dynamic-versioning]` 三项显式钉死（style / strict / dirty），`metadata` 有意留默认**：`style = "pep440"`（上游文档对默认 style 自相矛盾，而镜像 tag 归一化与 skew 比较都建立在 PEP 440 形态上）；`strict = true`（无 tag 时 build 失败，而非静默回落 `0.0.0`）；`dirty = true`（默认关；关着则 tag commit 上带未提交改动构建出的版本与正式发行版逐字节相同，决策 7 的「非纯净版本跳过 skew 比较」不会触发）。**`metadata` 不显式开**：dunamai 默认 = 非 tag commit 或脏树才带 `+<sha>`/`+dirty`；显式 `metadata = true` 会让**干净 tag commit** 也算出 `1.4.0+<sha>`——发布 gate「版本==tag」必败、PyPI 拒收本地段版本，链路按那配置永远发不出去（真跑证实：五个 pyproject 曾这样配，对抗核验在真 clone + 真 tag 上抓出）。三种 git 状态实测：干净 tag → `1.4.0`；脏树 → `1.4.0+dirty`；离 tag N 提交 → `1.4.0.postN.dev0+<sha>`（默认 `bump=false`、commit 无前缀）——非纯净构建必带 `+`，决策 7 的判据成立。
- **hook 的硬约束（实现者必读）**：启用该 metadata hook 的包，`dependencies` 与 `optional-dependencies` 必须**整体**搬进 hook 表、`[project]` 侧删除并声明 `dynamic = ["version", "dependencies", "optional-dependencies"]`——静态与动态不能共存，不含模板的条目也一起搬。只有 `gherkai-core`（无兄弟 pin）不需要依赖 hook、只 `dynamic = ["version"]`。2c 的依赖表因此是**渲染后的等效依赖**，不是 pyproject 字面内容。
- **为何 `==` 不是 `>=`**：三个包是同一 repo 切出的切片，内部契约随时一起动；`>=` 会让 resolver 装出从未测过的混搭（`gherkai 1.5 + gherkai-core 1.4`）。`==` 让这种组合**在安装层就不存在**，兼容性问题被分发机制消灭而非靠文档管理。代价「每次全家一起发」在 monorepo 单 release train 下为零。
- **同 repo 所有 workspace 成员的版本从同一 git 状态派生**，天然同号：本地 dev 版本两侧一致、pin 自满足。dirty 状态下 `uv sync` 的解析行为列入实测项。**editable 安装的元数据版本是 `uv sync` 时算出的快照**，工作树之后再改、版本串不会自动变——凡从 `importlib.metadata` 读版本的地方（`--version`、镜像 tag 前缀、skew 比较）都以此为限，contributor 在 dev 树上操作前先 `uv sync`。
- **npm 侧的版本真源同样是 git tag、但机制不同**：`package.json` 常驻占位 `"version": "0.0.0-dev"`，CI 发布时 `npm version X.Y.Z --no-git-tag-version` 写入 tag 版本再 publish；**非纯净版本永不发 npm**（只有 CI 从 tag 发），故不需要 PEP 440→semver 的转换件（release 形态 `X.Y.Z` 两边同形，`.dev`/`.post`/`+` 形态不是合法 semver、也不会到 npm）。contributor 本地态基底 build 用 dev 树 `npm pack` 出的 `0.0.0-dev` tarball 即可——基底内容由 tarball 决定、不由版本串决定。
- **代码内版本**经 `importlib.metadata.version("gherkai")` 读取，不复制；CLI 加 `--version`（当前没有）。
- **首发版本号接续 [0016](./0016-execution-architecture-core-lib-run-model.md) 的版本叙事、不倒回 0.x**：1.0 的稳定承诺是已做过的决策，公开发行从头计数是对叙事说谎。本 ADR 的完成线并入 0016 版本切分的 v1.4.0（与阅读理解层、AI skills 暴露同一完成线），PyPI 首发即 1.4.0。
- **不做兼容矩阵**：同类工具在 0.x/1.x 阶段无一维护矩阵。替代物 = 版本单旋钮 + skew 检查（决策 7）。

### 2c. extras 边界：`[aws]` 只在库层，CLI 上两个正交 extra

```
gherkai ──hard──▶ gherkai-runtime[aws]=={{v}} ──▶ gherkai-core[aws]=={{v}} ──▶ boto3
   │                    └──▶ packaging                     └──▶ gherkin-official
   ├─[local]──────▶ gherkai-worker-novaact=={{v}} ──▶ nova-act + boto3
   └─[deploy-aws]─▶ gherkai-deploy-aws=={{v}} ──▶ aws-cdk-lib + constructs + gherkai-runtime[aws]=={{v}}
```

| 包 | 硬依赖（渲染后等效） | extras |
|---|---|---|
| `gherkai-core` | `gherkin-official>=31.0.0` | `[aws]` = `boto3>=1.34`（DDB/S3 store、FargateEngine、CloudLauncher 等 adapter） |
| `gherkai-runtime` | `gherkai-core=={{ version }}`、**`packaging>=24`**（preflight 的版本比较；当前 venv 里能 import 到纯属 pytest 的传递依赖，生产路径必须自己声明） | `[aws]` = `gherkai-core[aws]=={{ version }}` |
| `gherkai`（CLI） | **`gherkai-runtime[aws]=={{ version }}`** | `[local]` = `gherkai-worker-novaact=={{ version }}`；`[deploy-aws]` = `gherkai-deploy-aws=={{ version }}` |
| `gherkai-deploy-aws` | `gherkai-runtime[aws]=={{ version }}`、`aws-cdk-lib>=2.150.0`、`constructs>=10` | 无 |
| `gherkai-worker-novaact` | `nova-act>=3.4.187.0`、**`boto3>=1.34`**（worker 自己直接 import boto3，直接 import 就直接声明、不靠 nova-act 传递） | 无（**不依赖 gherkai-core**：worker 讲协议、零 core 依赖，[0024](./0024-worker-core-protocol.md)）；当前混在主依赖里的 pytest 挪去 dev group |

- **CLI 硬依赖 boto3（反转 [0016](./0016-execution-architecture-core-lib-run-model.md)「cli backend 选择」节 `build_cloud_stores` 条的「cli 主依赖不含 boto3，走 `cli[aws]→core[aws]` extra」）**：按用户画像过一遍，裸装 `gherkai` 时没有任何画像能跑起完整用法——提交 cloud run 要 boto3；local 跑 novaact 装 `[local]` 而 nova-act 自带 boto3；只剩「仅跑 midscene 的 local 用户」与「只 `plan`」两种边缘画像省下一次安装体积。而 `[aws]` 留在 CLI 上的摩擦落在头条用法：`uvx gherkai submit --backend cloud` 会因缺 boto3 失败、要改写成 `uvx --from 'gherkai[aws]' gherkai …`。**code 层不变量不动**：local 路径**绝不 import boto3**靠懒加载保证（`compose` 的 `_make_*` 钩子），与安装期是否装了 boto3 无关。
- **`[aws]` 保留在 core 与 runtime 层**：[0030](./0030-realtime-persistence-seam.md) 决定六守的本来就是「core 作为库可轻量 import、不被 boto3 绑死」，针对的是库消费者；库层保留 extra 完整兑现它。
- **`[local]` 存在且语义 = local 跑法的 Python 侧 worker**（决策 3）；**不设** `[local]` 曾是备选（理由「worker 独立 venv、extras 够不到」），被「安装与拉起正交 + 共解实测」推翻。
- **`[deploy-aws]` 不叫 `[aws]`、不叫 `[deploy]`**：`[aws]` 会说谎——裸装已能用 AWS 后端，团队成员见 `[aws]` 必以为提交云端要装它、把 CDK 与 Node 依赖拉进机器；`[deploy]` 会关上 provider 那扇门（决策 6）。**`[deploy-aws]` 的语义 = 改云端环境所需**：供给后端（CDK）+ 变更后端用的 worker 镜像（[0038](./0038-worker-image-delivery.md) 的推送与注册都是云端写操作）；镜像**构建**是 developer 自己的容器工作、gherkai 不拥有。只提交 run 的人不需要装它。默认画像是 developer 兼测试开发与部署方两角、装它；团队拆角色时写 step 的人可不装、把本地镜像交给部署方。extras 名按 PEP 685 规范化，`deploy_aws` 等价。

### 2d. `requires-python >=3.13` 维持

uv 缺 Python 时自动下载托管 CPython，对 uv-first 受众近乎免费；pipx 默认不下载解释器，README 须写 `pipx install --fetch-python missing gherkai` 作回落；裸 `pip install` 在 3.13 以下解释器上失败是接受的边界，不为迎合它降下限。

## 决策 3：worker 运行时的交付——安装与拉起正交，四级定位链，`repo_root()` 全部消费点退役

**安装**（谁把 worker 放到机器上）与**拉起**（谁 spawn 它）是两件事。当前二者被 `repo_root()` 绑死：cmd 直指 repo 内 `engines/novaact/.venv/bin/python` 与 `node --import tsx engines/midscene/worker/run-scope.ts`、cwd = 各引擎目录。

- **Python 侧（novaact）：包化 + 装进 CLI 同一个 venv**（经 `[local]`），并声明 console script `gherkai-worker-novaact`（定位链第三级的 Python 侧供给方）。spawn cmd = `[sys.executable, "-m", "gherkai_worker_novaact"]`——**无包装层**（EVENTS_FD 经 `pass_fds` 直达，midscene 换 `--import tsx` 那次踩的「包装进程吞 fd3」坑在此路径不存在）、离线可用、版本由 `==` pin 与 CLI 锁死。「worker 独立 venv」的三条理由逐条审过：依赖隔离（共解实测通过，不成立）、双语言（只影响 midscene）、架构边界（worker 零 core 依赖靠代码纪律不靠 venv）——前提松动，同 venv 成立。
- **Node 侧（midscene）：npm 包 `@gherkai/worker-midscene`**，pip extras 够不到 Node 地盘。使用方 `npm i -g @gherkai/worker-midscene`（提供 bin `gherkai-worker-midscene`），或由定位链第四级 npx 拉起。**发布形态定死**：统一 ESM（`"type": "module"`、tsconfig 入库——当前刻意不带 tsconfig、靠 tsx 运行期扩展名重写，包化后不再成立）、tsc 产 `dist/`、`engines.node >= 22`（与基底镜像 `node:22-slim` 同源）、bin 入口在进程内注册 `tsx/esm/api`（进程不再由 `node --import tsx` 启动）。**使用方 step 文件只认 `.mts` / `.mjs` 两个扩展**：tsx 的 ESM register **只对 ESM 生效**——`.mts`/`.mjs` 恒为 ESM，而 `.ts`/`.js` 的模块体系由离文件最近的 `package.json#type` 决定，使用方（Python CLI 用户，项目 = `features/` + `steps/`）目录多半根本没有 package.json、会落进 CJS 域，step 文件里的 `import` 直接 SyntaxError。收敛到与使用方目录无关的两个扩展，比要求使用方维护 package.json 或双注册 cjs/esm loader 都简单可靠（脚手架与文档统一用 `.mts`）。**运行时依赖必须从 `devDependencies` 挪到 `dependencies`**：当前靠 `npm install` 全装才活（[0033](./0033-iac-aws-backend-and-composition-wiring.md) 记的「不能 `--production`」陷阱），作为被消费的 npm 包只会装 `dependencies`、不挪即崩；`tsx` 因此成为 runtime dependency。
- **worker 定位链**（组合根 `compose.build_engines` 解析，**取代 `repo_root()`**，dev 与分发**同一条链、不设 dev 模式特判**——分发后没有 repo，任何靠 repo 结构的隐式行为都是漂移面）：
  1. env `GHERKAI_WORKER_<ENGINE>_CMD`（`NOVAACT` / `MIDSCENE`，`shlex` 拆分）+ 可选配套 `GHERKAI_WORKER_<ENGINE>_CWD`——显式覆写，contributor 指向 repo 内源码、调试、自定义 worker 都走这里（cwd 配套存在的原因：`node --import tsx` 的裸 specifier `tsx` 按 cwd 上溯 `node_modules` 解析，实测在无关目录下直接 `Cannot find package 'tsx'`）；
  2. 同 venv 入口（Python 引擎）：`importlib.util.find_spec("gherkai_worker_novaact")` 命中 → `sys.executable -m …`；
  3. PATH 上的可执行 `gherkai-worker-novaact` / `gherkai-worker-midscene`（`shutil.which`）；
  4. 兜底拉起：`uvx gherkai-worker-novaact==<CLI 版本>` / `npx -y @gherkai/worker-midscene@<CLI 版本>`——**条件项**：包装进程是否吞 fd3 须真跑预演；预演不过则此级降为「报错 + 安装指引」。
- **miss 语义按调用点分叉，不在定位链里统一退码**：定位链四级全 miss → 抛结构化异常（引擎名 + 该引擎的安装指引：novaact → `uv tool install 'gherkai[local]'`；midscene → `npm i -g @gherkai/worker-midscene` + Node ≥22），由调用点处置——`run`/`submit` 在 spawn 前退 2（不再进 job 级 `engine_error`）、`list-deterministic` 退 2、**`plan` 保持 [0036](./0036-deterministic-capability-discovery.md) 决策 4 的 best-effort 降级**（只丢该引擎标注 + stderr 警告，plan 本体照出）。
- **worker 不再有专属 cwd；`--no-report` = 真不生成产物**（本条只管 local subprocess 档的落点；cloud 档落点由 `build_fargate_engines` 注 S3）：归集档产物经 `NOVA_LOGS_DIR` / `MIDSCENE_RUN_DIR` 落 `<report_dir>/<run_id>/` 绝对路径（compose 既有约束）。`--no-report` 档**不注入落点**，并经 env `GHERKAI_NO_ARTIFACTS=1` 令 worker **不生成、不上报**引擎原生产物：Midscene 关 agent 的 `generateReport`、不抢传 log、不带 report ref；Nova Act SDK 没有关闭 trajectory 的开关，此时不传 `logs_directory`、由 SDK 写进自己 `mkdtemp` 的临时目录（SDK 内部行为、不进项目），worker 不收集 trajectory、不带 summary、不发任何 reportRef；Midscene SDK 即便不出 report 也可能往 `./midscene_run`（相对 cwd）写 log/dump，`--no-report` 且无 `MIDSCENE_RUN_DIR` 时 worker 自己把它导到一次性临时目录。cloud 档 `--no-report` 同样注 `GHERKAI_NO_ARTIFACTS`，于是也没有 S3 上传。去掉专属 cwd 前，`--no-report` 档产物曾落引擎目录；曾一度改为「落系统临时目录、不清」，被否——`--no-report` 的含义就是不生成 report，用户不该在临时目录里收到一堆产物。
- **`repo_root()` 的另两类消费点一并退役**（否则 wheel 用户的行为随安装位置漂移）：①**子进程 cwd**——`_submit_local` 的 per-run 进程与 `--expose-local` 的 tunnel-watch 都改为继承提交进程的 CWD；②**feature uri 基准**——`load_feature` 当前把路径相对 repo 算 uri（`scenario_id`/`scope_id` = `<uri>:<line>`），改为**用户给出的路径经规范化后原样**（相对给相对、绝对给绝对，不再相对任何「根」）。已知影响：scope_id 形状变化 → local report 目录名与 DDB 键随之；run 是短命数据、无跨版本读取需求，接受。
- **contributor 代价点（明示）**：dev 态 novaact 是 workspace 成员、editable 装进同 venv，定位链第二级直接命中；midscene 无已安装 npm 包，须走第一级 env 覆写（cmd + cwd 两个 env，可放 `.envrc` / uv env-file 一次配好），比当前多一步。

## 决策 4：确定性 step 的定制面——`steps/` 目录约定 + env 注入，local/cloud 同一机制

确定性 step 注册表活在 worker 代码里、由使用方测试开发维护（[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)/[0036](./0036-deterministic-capability-discovery.md)：`@deterministic(正则)` 装饰器，TS/Python 两份对称）。当前「定制」= 直接改 repo 里的 `worker/deterministic_steps.py` / `worker/deterministic.steps.ts`（fork 模式；两引擎各只有一条生效的内建注册——页面地址匹配），在 clone-repo 分发下成立、在 PyPI 化后不成立。**定制面必须先画清**——它同时决定基底镜像的切面（决策 5）与 local 分发形态（决策 3）。

- **约定 = 使用方项目内的 `steps/` 目录**（测试资产同处：使用方的「项目」= `features/` + `steps/`），**不相对 repo、不相对 worker**。`steps/` 是项目级注册表、不按 feature 分；两引擎扫同一目录、各取自己的扩展名（`login.py` 与 `login.mts` 成对、同一正则）。
- **解析在组合根、随 definition 持久化、worker 只认 env**：提交侧（`run`/`submit` 的 CLI 进程）按 `--steps-dir` flag > env `GHERKAI_STEPS_DIR` > 默认 `./steps`（相对**提交时** CWD，存在才用）解析成绝对路径，**写进 definition（`RunMeta.steps_dir`，omit-when-None，同 `extra_http_headers` 的 [0035](./0035-local-app-testing-via-tunnel.md) 先例与 `max_concurrency` 的 [0034](./0034-detached-batch-reconciler.md) 惯例）**；所有起 worker 的宿主（同步 `run`、local per-run 进程、`status --wait` 接力者）一律**从 definition 读回**、经 env `GHERKAI_STEPS_DIR` 注给 worker、不重解析 `./steps`——local 无状态跑批的三个宿主各自是组合根、CWD 各不相同（[0034](./0034-detached-batch-reconciler.md)），只有随 definition 走才对三者一致（这也是「用到哪套确定性 step」属于 run 定义、影响判定可复现性的自然归属）。约定逻辑不进 worker，worker 保持薄（[0016](./0016-execution-architecture-core-lib-run-model.md) 分层）。worker 定位链的 env 覆写同理对三宿主可见：per-run 进程继承提交进程 env，接力者用自己的 env。
- **worker 启动时加载该目录（两侧对称）**：novaact 按**排序**递归遍历 `*.py`（排除 `_*` 与 `test_*`），以合成包名（相对 steps 根的路径转模块名、挂在 worker 私有命名空间下，防与 `sys.modules` 撞名）import，文件顶层 `from gherkai_worker_novaact.deterministic import deterministic` 后的 `@deterministic` 副作用完成注册——与当前脚手架的注册机制**完全同一**（[0036](./0036-deterministic-capability-discovery.md) 决策 1 的 description/example 必填照守）；**steps 根不入 `sys.path`**（防使用方文件名遮蔽标准库/第三方包）。midscene 按排序递归动态 import `*.mts`/`*.mjs`（排除 `*.test.*`；扩展收敛理由见决策 3），文件写 `import { deterministic } from "@gherkai/worker-midscene"`。
- **midscene 裸 specifier 的解析是一条独立决策，不能靠 Node 默认解析**：Node 只沿 step 文件所在目录上溯 `node_modules`、不认全局根与 npx 缓存（实测），全局装/npx 形态下使用方 steps 必 `ERR_MODULE_NOT_FOUND`；cloud 镜像里恰好能解析（`/app/steps` 上溯命中 `/app/node_modules`）是巧合、不能当机制。**机制 = worker 注册 resolve hook（`module.register`）把该裸 specifier 映射到自身安装位置**，落点与不变量：①hook 是随 `dist/` 发布的独立入口文件（hook 跑在独立 loader 线程、不能是闭包），目标 URL 经 `register(spec, parent, { data })` 传入；②**目标 URL 必须是 worker 自身已加载的同一个 URL**——从 `import.meta.resolve("@gherkai/worker-midscene")` 派生、禁止用 cwd/argv 推算——否则 ESM 缓存按 URL 分裂出第二个模块实例，使用方的 `@deterministic` 注册进一张 worker 永远不读的表，全部 step **静默**落回 AI catch-all；③**fail-loud 兜底**：加载完某 step 文件后若它一条都没注册进 worker 侧注册表，立即报错退出（把「双实例」从静默降级变成显式失败）。hook 让 step 文件的写法与当前脚手架完全一致、与安装形态无关；若实测不稳则退到依赖注入形态（step 文件导出 `register(deterministic)`），记入重议闸门。
- **加载失败 fail-loud**：steps 目录内任一文件 import 失败（语法/导入错误）→ worker **立即以启动错误退出**（带文件名与异常），三个自述入口同样；**绝不静默跳过**——跳过等于把该文件里的确定性 step 静默换成 AI catch-all、run 可能「通过」，是本项目最忌的静默降级。**提交侧同样前置**：`run`/`submit` 在起任何 job 前、`plan` 在标注前，对本 run 用到的每个引擎以自述入口探一次（steps 目录已解析时）——worker 因 steps 加载失败而非零退出 → 三个命令一律**退 2**、转述 worker 的诊断；这与「worker 运行时 miss」的分叉不同（miss 在 `plan` 降级），因为 steps 加载失败是使用方代码错误，`plan` 若降级成「无标注」、`submit` 若「提交成功」后逐 job error，都是静默降级。
- **三个自述入口**（`--list-deterministic` / `--match-steps` / 未来 `--capabilities`）同样加载 steps 目录，故 `list-deterministic` 与 `plan` 标注反映使用方定制——[0036](./0036-deterministic-capability-discovery.md)「真值单一：清单从注册表代码生成」仍成立，注册表 = 内建脚手架 + 加载的使用方模块。
- **内建脚手架 step**留在 worker 包内作为内建；使用方 step 与内建撞 pattern 按 [0036](./0036-deterministic-capability-discovery.md) 既定 conflict 语义处理（`plan` 预检暴露；排序遍历保证 conflict 清单可复现），**不引入「使用方覆盖内建」的优先级规则**。
- **cloud 档：steps 烙进定制镜像**（模板见 [0038](./0038-worker-image-delivery.md)），`--backend cloud` 下 definition 里的 `steps_dir` 对云端 worker 无意义 → 提交侧不写该字段、给了 `--steps-dir` 则 preflight 警告不拦。镜像里的 steps 是否最新由使用方管理、preflight 不比对，规则与理由在 [0038](./0038-worker-image-delivery.md)「不变量」与「被拒方案」。基底镜像**零使用方内容**，正好支撑决策 5 的两层分工。

## 决策 5：worker 镜像两层分工——维护者 GHCR 基底 + 使用方定制层（机制见 0038）

worker 内容 = 框架脚手架 + 使用方确定性 step，属业界分类里的 **user-code image**，最后一层由使用方构建（Dagster user-code deployment / Prefect flow image 同理）；「维护者独占发布完整镜像、用户绝不自建」曾是备选，因抹掉定制面被拒。本 ADR 只定分工与基底通道：

- **基底镜像**（维护者 CI 发布）：`ghcr.io/zhiyanliu/gherkai-worker-novaact:X.Y.Z` / `…-midscene:X.Y.Z`，内容 = 同版本 worker 包 + SDK 运行时 + 协议层，**零使用方内容**；**linux/amd64 单架构**（ARM64 被拒，理由与将来的路在 [0038](./0038-worker-image-delivery.md)）；tag = immutable `X.Y.Z` + 移动 `latest`（只跟随最新 tag；文档一律 `FROM …:X.Y.Z`）。Dockerfile 两态（与 Lambda asset 同源）：CI 态按版本从 PyPI / npm 装已发行包；本地态经 `--build-arg` 指向本地 `uv build` wheel / `npm pack` tarball（dev 版不在 PyPI，contributor 才造得出基底）。
- **为什么 GHCR 而非 ECR Public / Docker Hub**：运行时拉的是使用方私有 ECR 里的镜像，GHCR 只在使用方 `docker build` 与 deploy 同步基底时各被拉一次，ECR Public 的免流量/免认证优势碰不到；Docker Hub 匿名限额是负项；GHCR 与 repo 同屋檐、`GITHUB_TOKEN` 推送零配置。
- **定制镜像由使用方在本地 build，gherkai 不拥有构建**：Dockerfile 模板（唯一真源）见 [0038](./0038-worker-image-delivery.md)「概念模型」节；必须 `--platform linux/amd64`，push-worker 推送前校验。**推送、注册、选择、清理、权限**全部在 [0038](./0038-worker-image-delivery.md)：variant 命名、默认指针、按（引擎，variant）注册 digest 引用的 task-def revision、`gherkai deploy push-worker` / `list-workers` / `delete-worker`、容器引擎口子、preflight 的 variant 解析。
- `tools/build_push_workers.py` 已随 0038 落地退役（`gherkai deploy push-worker` 取代）。

## 决策 6：部署 = `gherkai deploy`——命令 provider 中立，分发单元带 provider

「clone repo + `cdk deploy`」**不再是正式部署形态**（只是 contributor 的开发方式）：相对路径拼 asset、vpc context 坑外露、wheel 用户不可达。直接做 Chalice 模式：

- **IaC 进 wheel**：`gherkai-deploy-aws` 收编 `iac_aws_backend/`（stack / names 薄壳 / app）与 `lambdas/`（两个 handler 源，作 asset 原料——它们是 AWS Lambda 专属胶水、是 runtime 的「Lambda 入口皮」，住在 provider 包里比住在 runtime 里诚实）。`aws-cdk-lib` 只在这个包上，`[deploy-aws]` extra 隔离；`gherkai_cli` 经 entry point group `gherkai.deploy` **发现**已安装的 provider 包：零个 → 提示装 `gherkai[deploy-aws]`；一个 → 无需 `--provider`；多个 → 必给。**provider 契约**（entry point 指向的 `Provider` 类）= `name` / `add_arguments(parser)` / `deploy`·`destroy`·`diff`·`synth_only`·`bootstrap`（各收已解析的 argparse Namespace、返回进程退出码；`2` = 前置/校验失败，其余透传 cdk 的返回码）。CLI 皮**不 import `aws_cdk`/boto3**（`--help` 不付一次 node 启动，有测试守：真 provider 已装时 `aws_cdk`/`jsii`/`boto3` 都不入 `sys.modules`），只做发现、贴 flag、分派；worker 镜像族子动词由 provider 自加 subparser 并 `set_defaults(_deploy_verb=…)`，皮先看 `_deploy_verb`——0038 落地时皮一行不改。
- **命令面**：`gherkai deploy`（`--diff` 只呈变更集、`--synth-only DIR` 导出模板作 escape valve——不让 0.x 工具改自己生产账号的 reviewer 靶点；DIR 相对用户 cwd、命令钉成绝对路径再交 cdk——cdk 子进程的 cwd 是随后删除的临时工作目录，相对路径原样传会「退 0 且无产物」（真跑踩过）、`--bootstrap` = `cdk bootstrap aws://<account>/<region>`——**账户级动作、不合成 app、不需要 `--vpc`**（显式环境 + 不带 `--app` 时 cdk 不加载 app，真跑核过；带 `--app` 则即使给了显式环境也照样跑 app）；deploy 失败时中性提示「常见首次原因之一是未 bootstrap」、不改写 cdk 诊断）、`gherkai destroy`（`RETAIN` 语义见 [0033](./0033-iac-aws-backend-and-composition-wiring.md)）、worker 镜像族 `gherkai deploy push-worker` / `list-workers` / `delete-worker`（[0038](./0038-worker-image-delivery.md)）。
- **把裸 cdk 的坑封死在命令里，flag 面对齐 stack 与 app 的全部 context 旋钮**（当前恰四个：`prefix` / `vpc_id` / `use_default_vpc` / `stop_timeout`，映射为**三个 flag**）：`--prefix`（默认 `gherkai-`）、**`--vpc default|new|<vpc-id>` 必给、无隐式默认**（校验在**运行期**而非 argparse：deploy / diff / synth / destroy 缺档退 2，`--bootstrap` 不要它；一个 flag 吞掉 `vpc_id` + `use_default_vpc` 两个旋钮、三档与 [0033](./0033-iac-aws-backend-and-composition-wiring.md)「VPC 来源：三档」一一对应，`vpc-` 前缀值即复用现有 VPC；漏 context 合成「新建整套 VPC + 替换 WorkerSg」危险变更集是真踩过的坑，隐式默认 = 让用户重踩）、`--stop-timeout N`（grace 标定用）。provider 另声明 `--region` / `--profile`（AWS 概念、不归皮；prefix/region/profile 走与 run/submit **同一条**解析链 `compose.resolve_cloud_target`，部署侧与提交侧解析出的 prefix 恒等）；`--require-approval` / `--allow-vpc-change` 两层声明——皮给中立版（provider 缺席时帮助不残缺）、provider 再声明带 AWS 语义版（`choices` / 三态措辞），argparse `conflict_handler="resolve"` 令 provider 版生效。命令拼 context、在临时工作目录生成 `cdk.json`（app = `sys.executable -m gherkai_deploy_aws.app`；特性开关逐字沿用包化前 `cdk.json` 那一组——换一组即给已部署 stack 造无意义变更集，A/B 实测 IAM statement 32 vs 44 条），调 cdk CLI 执行（cwd = 该工作目录）。**CDK 环境查询缓存持久化**：`from_lookup`（`--vpc default|<id>`）写的 `cdk.context.json` 按 prefix 存在用户缓存目录（`$XDG_CACHE_HOME`/`~/.cache` 下 `gherkai/cdk-context/`），进一次性工作目录前放入、跑完存回，`--refresh-context` 丢弃重查——理由：一次性目录若每次空着进去，cdk 对缺失查询值会先用占位 VPC/子网**预合成一遍**再真查，aws-cdk-lib（≥2.26x 内建模板校验器）对那份占位模板报错、降级成 `[Warning] Template validation found issues` 打给用户（真部署抓到、全新目录 100% 复现、有缓存即消失），且每次多一轮查询 API；持久化 `cdk.context.json` 正是 CDK 自己的标准做法（它建议入库，我们的 wheel 用户没有可写源码树，故放用户缓存目录）。首次查询某 prefix 仍会看到那条 warning 一次。
- **VPC 档持久化比对，三态齐全**（只强制显式给值挡不住第二次 deploy 敲错档）：stack 把生效的 vpc 档写成 SSM 参数 `names.ssm_path(prefix, "vpc")`（stack 资源、与部署事务同生死；`new` 档存 `new:<所建 vpc-id>` 使其也可回溯核对）。`gherkai deploy` 在调 cdk 前读它：①stack 不存在（真首次部署）→ 放行；②**参数缺失且 stack 已存在**（本 ADR 之前部署的环境——当前所有已部署 stack 都没有此参数，而这恰是最危险的那一次 deploy）→ 退 2，要求先 `--diff` 核对变更集、再带 `--allow-vpc-change` 放行一次；③参数存在 → 与 `--vpc` 一致放行，不一致退 2（`--allow-vpc-change` 放行）。
- **deploy 的 worker 镜像四步**（登记 task-def 模板——随 cdk 事务；同步基底为 `base` variant、初始化默认指针、按新模板重派生既有 variant——cdk 之后）**全部由 [0038](./0038-worker-image-delivery.md) 规定**，本 ADR 只登记它们属于 `gherkai deploy` 的职责、且全部幂等。
- **Node 前置是硬事实**：Python CDK 的 `aws-cdk-lib` 是 jsii 绑定，import 即起 node 子进程；cdk CLI 本身也是 npm 物。`gherkai deploy` 要求 Node ≥22 在 PATH（与 worker 的 `engines.node` 同一下限，README 一处说清）；cdk CLI 用 PATH 上的 `cdk`，缺则 `npx -y aws-cdk@2`。对本受众（已在装 uv/Docker/AWS 凭证）可接受。**去 Node 路线**（CI 预合成模板 + boto3 驱动 CloudFormation）defer 非拒：vpc 三档 × prefix 的参数化要变 CloudFormation Parameters 组合管理，且 jsii 本身也要 Node、只省 cdk CLI 一层。**这一期 deploy 机器还需要容器引擎**（同步基底要 pull / push，0038）。
- **Lambda asset 来源**：handler 源（deploy-aws 包内）+ **从当前 venv 已安装的** `gherkai_runtime` / `gherkai_core` / `gherkin` / `packaging` / `typing_extensions` 五个 import 包复制（版本 = 运行中的 CLI，离线可行，dev 版也可；当前那次联网 `pip install gherkin-official` 随之消失）；boto3 由 Lambda runtime 自带。**传递依赖必须自己进清单**：`gherkin` 无条件 `from typing_extensions import …`，按名复制时它不会被捎带——摆放规则类单测全绿、真 asset 一 import 即 `ModuleNotFoundError`；故清单由一条「剥掉 site-packages 的子进程真 import 整个 asset」的测试守着（单文件模块 `typing_extensions.py` 与包目录两种形态都认）。asset 落一次性临时目录、经 env `LAMBDA_ASSET_DIR` 传给 app（不走 context，保住「flag 面 == context 旋钮全集」），wheel 装的包目录不被写。**不从 PyPI 拉同版本**（dev 版不在 PyPI 上，contributor 部署 dev 版会断）。
- **版本戳**：stack 把版本写成 SSM 参数 `names.ssm_path(prefix, "version")`（值经 context `-c version=<PEP 440 版本>` 由命令传入——值 = **CLI 自己的**发行版本，皮经 `args.version` 交给 provider、不让 provider 自报（editable 树里各包版本各自漂）；app 缺该 context 即 fail-fast、不回落（戳写错比缺失更坏）；**stack 资源而非命令事后 `put_parameter`**，使其与部署事务同生死、回滚不留错值；`gherkai destroy` 随 stack 删除、不 `RETAIN`），供决策 7 比对。落在已授的 `/{prefix}backend/*` 通配内，CLI 侧不新增 SSM 授权。
- **权限**：与当前一致，用本机凭证；IAM 变更审批走 cdk 的 `--require-approval` 透传；worker 镜像相关的权限增量见 [0038](./0038-worker-image-delivery.md)。

## 决策 7：版本单旋钮贯穿 + skew 检查（三态齐全）

一个 git tag 派生：wheel 版本（五个 Python 包同号）、npm 包版本（CI 写入 `package.json`）、基底镜像 tag、定制镜像 tag 的版本前缀（0038）、SSM 版本戳、GitHub Release。部署方升级只拧一个旋钮。

**preflight 比对 CLI 版本与 SSM 戳，三态**（用 `packaging.version.Version` 比较、**只比 release 段**；`packaging` 是 runtime 的新增硬依赖，见 2c）：
- 戳**缺失** = 本 ADR 之前部署的环境（当前所有已部署 stack 都没有此参数）→ **警告 + 提示跑一次 `gherkai deploy` 写入，不拦**——否则所有现存部署被 preflight 锁死。
- CLI **新于**后端 → 退 2，**不设放行口**。提示两条出路：部署方 `gherkai deploy` 升后端；或临时用与后端同版本的 CLI（`uvx --from 'gherkai==<后端版本>' gherkai …`，不动本机安装）。理由：新 CLI 写的 definition 结构由旧 Lambda runtime 读是真风险；放行口等于宣称支持混搭版本，与「不做兼容矩阵」相悖；contributor 的 dev 版本本就跳过检查、不需要它。
- CLI **旧于**后端 → 警告不拦。
- 任一侧是非纯净版本（含 `.dev`/`.post`/`+`）→ 跳过比较、警告一句（dev 距离逐提交前进，逐字比较会把每次都判成 skew）。2b 的 `dirty=true` + metadata 默认行为保证「非纯净构建一定带 `+`」，这条判据才可靠。
- **接线**：读戳 + 判定住产品本体（`compose.check_backend_skew`，WebUI/推进器同调、判据与措辞单点），三个 cloud 入口（`run`/`submit`/`status`）**先于资源 preflight** 调它（skew 的修复动作 `gherkai deploy` 同时把资源补齐，先报「表不存在」只会绕一圈）。`ParameterNotFound` → 戳缺失档；其它读失败（凭证/权限/网络）→ 退 2——block 无放行口，「读不到就放过」等于开了一个。比的是 **CLI 自己的**发行版本（`importlib.metadata.version("gherkai")`，必由调用点传入、不缺省成 runtime 包版本：editable 树里各包版本各自漂）；源码直跑取不到 → 跳过。

**操作规则（本架构下真实成立的形式，不是 Prefect 那句「先升 server」的直译）**：后端由 CLI 的 `[deploy-aws]` extra 部署、且被 `==` 钉在同版本，所以「先升后端再升 CLI」无法执行——真实次序是**升级即三步**：①`uv tool upgrade gherkai`；②立刻 `gherkai deploy`（新模板、同步新版本基底、重派生；中间窗口 preflight 会退 2，这是预期）；③团队有自定义 variant 或自定义默认的，从新版本基底重新 build 各引擎镜像、`push-worker` 推上去（默认指针不重置、推上去即恢复，细节见 [0038](./0038-worker-image-delivery.md)）。**非部署者**（团队里只提交 run 的人）等部署者做完三步再升自己的 CLI；部署者若不想动本机安装，可 `uvx --from 'gherkai[deploy-aws]==X.Y.Z' gherkai deploy` 先升后端。

## 决策 8：CI 发布链与占名

- **占名（先于一切）**：PyPI **七名** = 五个真发行（`gherkai` / `gherkai-runtime` / `gherkai-core` / `gherkai-worker-novaact` / `gherkai-deploy-aws`）+ 两个防混淆占位（`gherkai-cli` / `gherkai-worker-midscene`），各真传一版 `0.0.0` 占位 sdist（README 指向 repo）——**PyPI 的 pending publisher 不占名**（官方明文：他人先注册即失效），必须真传。npm：注册 `gherkai` 用户/组织独占 `@gherkai` scope（原生命名空间，不需逐名防御）+ 发 `@gherkai/worker-midscene@0.0.0` 占位；可选占非 scoped `gherkai`（品牌保护，防 `npx gherkai` 跑出别人的包）。PyPI PEP 541 与 npm 争议政策都只针对无意图占坑，带真实项目指向即可。
- **tag 触发全链**（GitHub Actions，`v*`），**前置、顺序与失败语义**：前置 = checkout 必 `fetch-depth: 0`（**`fetch-tags: true` 不是替代品**：Dunamai 对浅仓库直接拒算——真跑报 "This is a shallow repository, so Dunamai may not produce the correct version"，`--depth 1` 后 `git fetch --tags` 让 tag 可见了照样同一个错，与 tag 可见性无关）；随后 **gate：tag 形态 `vX.Y.Z` + 断言算出的版本 == 触发 tag** 再往下走。**发布链只认 `vX.Y.Z`**：预发行 tag（`v1.4.0rc1`）是合法 PEP 440 却不是合法 semver（npm 要 `1.4.0-rc.1`），gate 第一步拦掉——放进来就是 PyPI 发成功、npm 挂在 `npm version` 上的半发布态；也顺带挡住演练 tag 误 push。日常 CI 另做 **gate 演练**（干净 checkout 打本地 tag `v99.0.0` → build → 校版本==tag），使「干净 tag 也带本地段」这类回归不必等到发布日才炸。① `uv build --all-packages` → `astral-sh/attest-action` 生成 PEP 740 attestation（**`uv publish` 自身不生成**，只上传已有的 `*.publish.attestation`；漏这步 = 静默发无证物件）→ `uv publish`（PyPI trusted publisher，OIDC 免密）；② npm `npm version <X.Y.Z> --no-git-tag-version && npm ci && npm run build && npm publish --provenance --access public`（**`npm ci && npm run build` 不可省**：`dist/` 不入库、package.json 无 prepack 钩子，漏 build 会发出空 `dist/` 的包、bin 直接失效）；③ 基底镜像 `docker/build-push-action`（linux/amd64，两态 Dockerfile 的 index 态：`--build-arg WORKER_VERSION=<X.Y.Z>` 从 PyPI/npm 装已发行的 worker 包，见决策 5）→ GHCR（`GITHUB_TOKEN`；**首发的 package 默认 private**，须人工改一次 public，否则 0038 的「deploy 同步基底」匿名 pull 不到；docker attestation 关掉——开着会把镜像变成带 unknown/unknown 附属 manifest 的 index，0038 的 digest/架构校验路径要干净单 manifest）——**依赖 ①②已发行且索引可见**（带重试等待），且该 job 对已发行版本**可单独重跑**（对 `X.Y.Z` tag 幂等；**重跑旧版本时不推 `latest`**，`latest` 只跟随最新 tag），故「PyPI 已发、镜像缺失」的半发布态有确定的修复动作；④ GitHub Release 作 changelog 锚点（`[project.urls] Changelog` 指它）。TestPyPI 演练须配 `[[tool.uv.index]]` 的 `publish-url`，且 `uv publish --index` 要求 checkout 有 pyproject。
- **[0033](./0033-iac-aws-backend-and-composition-wiring.md) defer 条由此闭环**：托管 = GitHub；基底镜像去 GHCR 后 CI **不再需要 OIDC→AWS 的 ECR push**——那套 IaC/凭证方案整体不需要了。

## 工程布局（目标态；[0016](./0016-execution-architecture-core-lib-run-model.md) 布局图在发行重组实装后据此校准）

```
./
├── pyproject.toml          ← uv workspace 根：[tool.uv.workspace] members 五个 Python 包；根自身无发行物
├── core/                   ← dist gherkai-core   · import gherkai_core   （今 core/）
├── runtime/                ← dist gherkai-runtime · import gherkai_runtime（今 gherkai/；目录改名避免 gherkai/gherkai_runtime/ 的歧义；names 含 image_tag / ecr_repo_name，0038）
├── cli/                    ← dist gherkai        · import gherkai_cli · 命令 gherkai（今 cli/）
├── deploy_aws/             ← dist gherkai-deploy-aws · import gherkai_deploy_aws（stack.py / app.py / names.py / cli.py=Provider / lambdas/ 两个 handler 源作 asset 原料；worker 镜像族命令与容器引擎口子，0038）
├── engines/
│   ├── novaact/            ← dist gherkai-worker-novaact · import gherkai_worker_novaact · console script 同名 · Dockerfile = 基底镜像（今 worker/ + lib/ 收进包）
│   └── midscene/           ← npm @gherkai/worker-midscene · Dockerfile = 基底镜像（ESM + tsc dist/，tsconfig 入库，tsx 留 dependency，resolve hook 随 dist/）
├── features/ · tools/ · docs/   ← 不分发（tools/build_push_workers.py 已随 0038 退役）
```

- 一个目录 = 一个 workspace 成员 = 一个 lock（根 `uv.lock`），当前五处各自的 `uv.lock` 合一；`uv run gherkai …`、`uv run pytest`（根跑全部）、`uv build --package <name>`。**单 lock 要求全员依赖共解**（已实测通过）；将来某成员升版引入冲突时用 `tool.uv.conflicts` 声明或把该成员移出 workspace，不回退到多 lock。
- **contributor 体验净变好**：一次 `uv sync` 替代四处安装中的三处（midscene 仍 `npm install`）；console script 直接可用；部署与用户同一条 `uv run gherkai deploy --vpc default --prefix …`，context 坑对 contributor 也消失。代价见决策 3 末条。

## 对既有 ADR 的影响（反向链已落 Status 头，带「（Draft，决策已对齐、未实装）」标注、随本 ADR 翻 Accepted 时去掉）

- **[0016](./0016-execution-architecture-core-lib-run-model.md)（Partially-superseded-by 本 ADR）**：反转「cli backend 选择」节 `build_cloud_stores` 条的「cli 主依赖不含 boto3、走 `cli[aws]→core[aws]` extra」（CLI 发行包硬依赖 `gherkai-runtime[aws]`；库层 extra 保留）；「工程布局」树 `cli/` 行的「gherkai/core 作 path 依赖」→ uv workspace + build 时 `==` pin；工程布局的目录名/发行名/import 名重排；「数据模型」节 definition 行的 run 级字段枚举（已逐字段带 ADR 指针）落地时补 `steps_dir` → 本 ADR（扩展，属校准）。分层、窄腰、注入红线、决策 A/B/C **全部不动**。
- **[0033](./0033-iac-aws-backend-and-composition-wiring.md)（Partially-superseded-by 本 ADR 与 0038）**：本 ADR 取代的部分——`iac_aws_backend/` 独立工程 + 裸 `cdk deploy` → 包化进 `gherkai-deploy-aws`、经 `gherkai deploy`（`prefix`/`vpc_id`/`use_default_vpc`/`stop_timeout` 四个 context 旋钮升为三个 flag，能力不减，另加 SSM 档比对）；Lambda asset 现场 copytree repo 相对路径 + 联网装 gherkin → 从已安装包取；「留待」CI 条闭环；SSM 参数族加 `version`、`vpc`。镜像/task-def/ECR/权限相关的取代见 [0038](./0038-worker-image-delivery.md)。两个镜像的容器入口随 worker 包化改为 `python -m gherkai_worker_novaact` 与 `node dist/bin.mjs`（决策 3）；资源清单/命名契约不动；preflight 加版本 skew 一项（variant 解析那项归 0038）。
- **[0034](./0034-detached-batch-reconciler.md)（扩展、Status 不动）**：local 无状态跑批的三宿主（提交 CLI / per-run 进程 / `status --wait` 接力者）各自是组合根，steps-dir 随 definition 走、worker 定位链对三者同一条、per-run 进程 cwd 改继承提交进程 CWD——沿用其「随 definition 走」的惯例，未改其任何机制。
- **[0035](./0035-local-app-testing-via-tunnel.md)（扩展、Status 不动）**：tunnel-watch 子进程当前以 `repo_root()` 作 cwd，随定位链落地一并改继承提交进程 CWD；`RunMeta.steps_dir` 沿用其 `extra_http_headers` 的 omit-when-None 搬运惯例。
- **[0030](./0030-realtime-persistence-seam.md) 决定六**：库层 `[aws]` extra 原意完整保留，不动。
- **[0036](./0036-deterministic-capability-discovery.md)（扩展、Status 不动）**：注册表加载面扩展到使用方 `steps/` 目录，「真值单一」不变；`plan` 的 best-effort 降级契约由决策 3 的 miss 分叉显式保留。
- **[0025](./0025-plan-module-feature-to-jobs.md)（扩展、Status 不动）**：feature uri 的基准从「相对 repo 根」改为「用户给出的路径规范化后原样」，`scenario_id`/`scope_id` 的拼法不变、只换前缀来源。
- **[0024](./0024-worker-core-protocol.md) / [0026](./0026-schedule-module.md)**：worker↔core 协议、`SubprocessEngine` 参数化 cmd 不动；只是 cmd 的**来源**从 `repo_root()` 变定位链。
- **[0009](./0009-maximize-aws-hard-constraint.md)**：`-aws` 后缀入名是「不用当前的命名把门关死」，**不是**对全栈 AWS 硬约束的反转——两个引擎本身绑在 AWS 服务上（Nova Act、Bedrock、AgentCore Browser），非 AWS 后端意味着引擎层也要重铺、距离很远。

## 对既有文档与 code 注释的影响（校准清单，Draft→Accepted 门槛的一部分；各条到期点见括注）

- **README.md**：「首次安装：三个运行环境」节与**全部** `uv run python -m cli …` 调用示例 → `uvx gherkai …` / `uv tool install`（发行重组落地时）；「环境隔离：Python 依赖在 `engines/novaact/.venv`、不污染全局」条**被决策 3 反转**（worker 装进 CLI 同 venv；`[local]` 落地时）；目录树（布局落地时）；「boto3 走可选 `core[aws]`」句（发行重组落地时）；两处 `cdk deploy` 提法（`--backend` 说明与云端档示例）→ `gherkai deploy --vpc … --prefix …`（**已校准**）。
- **cli/README.md**（`uv sync --extra aws` / `pip install cli[aws]`）、**core/README.md**（`core[aws]`）、**gherkai/README.md**（`cd gherkai && uv sync`）→ 发行重组落地时。
- **iac_aws_backend/README.md**（`uv run cdk deploy -c …`、三档 context 写法）→ `gherkai deploy` 落地时（其 `build_push_workers.py` / `latest` tag 部分归 0038）；**engines/novaact/README.md**（`.venv/bin/python` 直跑）、**engines/midscene/README.md**（`node --import tsx` 直跑、依赖全在本地 `node_modules`、`.ts` 脚手架文件名）→ worker 交付落地时。
- **code 注释与用户可见文案**（判据 = `grep -rn 'core\[aws\]\|cli\[aws\]'` 全清，排除 `docs/adr/` 历史）：三份 pyproject 的 extras 说明注释（`cli`/`gherkai`/`core`）；`gherkai/gherkai/compose.py` 的 `build_cloud_stores` docstring（逐字是被 2c 反转的那句）；`core/core/adapters/_boto.py` 的报错文案（`pip install core[aws]`，**用户可见**，不改即教用户敲一个不存在的包）；三个云端 adapter（`run_store/ddb.py`、`report_store/s3.py`、`result_store/s3.py`）的 docstring；测试注释 `cli/tests/test_backend_cloud.py`、`gherkai/tests/test_compose.py`；`CONTEXT.md` 的「boto3 走可选依赖 `core[aws]`」句 → 发行重组落地时。**`CONTEXT.md` 描述 fork 模式定制的两句**（「确定性锚点…由 test engineer 在 `deterministic.steps` 脚手架里写」「在对应 worker 里登记 `(模式 → handler)`」）→ steps 目录约定落地时改为「在使用方 `steps/` 目录写」。**CONTEXT 新增词条**当前带「设计已定、施工未启」状态标记，各自随对应层落地去掉标记。
- **docs/guides/execution-and-reconciliation.md** 引用的模块路径（`core/schedule.py` 等）→ import 改名落地时。

## 落地次序与依赖（依赖关系，非进度追踪；本节编号只在本节内部使用，其它文档不引用它）

0. **占名**（无依赖，先做）。
1. **发行重组 + PyPI 首发**：workspace 化、三名改、dynamic versioning（三项配置显式钉死 + hook 的 dynamic 声明）、`packaging` 声明、metadata（license 文件进各包、`[project.urls]`、README 相对链接绝对化）、`--version`、`repo_root()` 三处非 engine 消费点退役（两个子进程 cwd、feature uri 基准）。首发即成立 `uvx gherkai submit --backend cloud`。
2. **worker 交付**（依赖 1）：novaact 包化（boto3 直接声明、pytest 挪 dev、console script）+ `[local]`；定位链取代 `repo_root()`（含 miss 分叉与 `--no-report` 临时绝对落点）；midscene npm 包（ESM/tsc/tsx 注册、依赖挪位、resolve hook 随 dist、`.mts` 脚手架）；`steps/` 目录约定 + `RunMeta.steps_dir`（local 半）。
3. **基底镜像 CI**（依赖 2，基底装的是 worker 包）：基底 Dockerfile 两态、CI 推 GHCR（linux/amd64）。worker 镜像的推送注册子系统按 [0038](./0038-worker-image-delivery.md) 自己的次序落地，其中只有「deploy 同步 GHCR 基底」一步依赖本步，运行时改显式 revision 等可先落。
4. **`gherkai deploy`**（依赖 1、3）：`gherkai-deploy-aws` 收编 IaC 与 handler、provider 发现、asset 从已安装包、三 flag（四旋钮）+ SSM `version`/`vpc` 两参数各三态 + skew 检查、CI release 全链一次真跑；其 worker 镜像尾部步骤随 0038 落地。
- **期外/按需**：定位链第四级存废（随实测）；worker `--capabilities` 自述入口（运行配置有效性 engine × browser 后端 × backend 走 worker 自述、非安装期 extras——等本地 browser 这类真实需求触发，[0036](./0036-deterministic-capability-discovery.md) 形态延伸）；去 Node 部署路线。

## 实测项（Draft → Accepted 前必清；「绿≠对」——每条都依赖 mock 之外的真实行为）

1. `uv-dynamic-versioning` 在 workspace 内：三种 git 状态各算出什么版本、`=={{ version }}` 与 `uv sync`/`uv run` 的解析行为；hook 接管 dependencies 后 extras 的渲染正确。（**已验**：三项显式配置 + metadata 默认下，干净 tag → `X.Y.Z`、脏树 → `+dirty`、离 tag → `.postN.dev0+<sha>`；五个 wheel 的 `==` pin 与 extras 渲染正确、`uv sync` 解析通过；反例——显式 `metadata = true` 在干净 tag 上出 `+<sha>`，gate 失败。）
2. `sys.executable -m gherkai_worker_novaact` 下 EVENTS_FD `pass_fds` 继承与三通道分离真跑（**前半已验**：真管道经 `pass_fds` 收到 worker 写出的事件、中文不转义；`--match-steps` 挂起时 `pgrep -P` 无子进程，Python 与 midscene 的 `dist/bin.mjs`、全局装 bin 三种形态皆然）；`uvx`/`npx` 兜底路径的 fd 继承预演 → 定第四级存废（**待做**，首发前）。
3. midscene 以**最终发布形态**（ESM dist + 运行期 `tsx/esm/api` 注册 + 随 dist 的 resolve hook）安装到 **repo 外干净目录**，变量维度 = 安装形态（全局装 / npx）× 使用方目录（无 package.json / `type=commonjs` / `type=module`）× 扩展（`.mts`/`.mjs`），验证使用方 step 能加载、裸 specifier 解析到 worker 自身同一 URL（注册进同一张表）、零注册 fail-loud 真触发——在 repo 内预演会被 repo 自己的 `node_modules` 掩盖成假绿。（**已验**：`npm pack` → `npm i -g --prefix <tmp>` 与 `npx --package <tgz>` 两形态，在无 `node_modules`/无 `package.json` 及 `type=commonjs`/`module` 的使用方目录下，`.mts`+`.mjs`（含子目录）均注册进同一张表；使用方目录另装一份副本时 hook 仍解析到运行中那一份；import 另一安装位置的 `dist/index.mjs` 触发双实例守卫退出；语法错/零注册/目录不存在三者 rc≠0 且点名文件。发布形态分支只有真跑证据，自动化测试只覆盖源码形态 bin。）
4. `gherkai deploy` 内嵌 cdk：`npx -y aws-cdk@2` 与 jsii 的 Node 版本兼容；asset 从 site-packages 复制后 Lambda 冷启动 import 正常（含 `packaging`）；SSM `version`/`vpc` 参数随 stack 事务写入、destroy 随删；VPC 档三态（含「参数缺失 ∧ stack 已存在」的迁移档）与 skew 三态各一次真跑。（**无凭证下已验**：命令真调 `npx aws-cdk@2` 真合成——模板含 6 个 SSM 参数（version / vpc / worker-template×2 / subnets / security-groups）；asset 在剥掉 site-packages 的解释器里真 import 通过（抓出 `typing_extensions` 漏项）；`--synth-only` 相对路径导出、`--bootstrap` 不带 `--vpc` 直达凭证解析。**真账户已验**（独立 prefix、dev 版本）：`gherkai deploy --vpc default` 真部署成功（含四个新 SSM 参数、Lambda asset 真冷启动——推进器随后真起 task 并收敛 run），四步在 dev 版按设计跳过基底同步、初始化默认指针；VPC 三态——参数存在且一致放行、`--vpc new` 不一致退 2 不动账户；skew——两侧同为非纯版本走「跳过比对」档；两次 cloud run（单引擎 / 双引擎）passed。**待真账户**：destroy 随删 SSM 参数、「参数缺失 ∧ stack 存在」迁移档（现网 stack 首次升级时会真跑到）、skew 的 block/warn 档（需两个纯发行版本）。）
5. 完整 release 链一次真跑（TestPyPI 先行）：`fetch-depth: 0` + 版本==tag gate → attest-action → `uv publish` → npm provenance → 等索引可见后基底进 GHCR，含镜像 job 对已发行版本单独重跑且不动 `latest`。（**推 tag 前已验**：两个 workflow YAML/actionlint 静态通过、gate 脚本正反例真跑、gate 演练在干净克隆通过；两态 Dockerfile 的 **local 态**在两种 builder 上真 build 通过（BuildKit 与**经典 builder** 各一台，`--platform linux/amd64`，novaact wheel / midscene tarball），`--list-deterministic` 冒烟通过、包装进 site-packages / 全局 node_modules 不靠 PYTHONPATH；踩出两个真坑——① pip 不接受改名的 wheel 文件名（要保原名，故 local stage 整体 COPY context 再按名装）；② **经典 builder 会把未选中的 stage 也跑一遍**，「参数必须给」的守卫若写成硬失败会让未选中的那个先炸，故两 stage 各自容忍参数缺席、把关移到 final stage 的冒烟（漏 build-arg 在那里 fail-loud，实测无参数构建退 1）。**index 态与 GHCR 推送只能在首个真 tag 后验**。）
- worker 镜像子系统的实测项在 [0038](./0038-worker-image-delivery.md)。

## 被拒方案（护栏，防未来重踩）

- **Homebrew tap / 单文件二进制（PyApp、PyInstaller、shiv、pex）**：受众（装 AWS 凭证、Docker 的开发/测试工程师）能装 uv；homebrew-core 门槛不达、tap 是第二个发布面与 bottle 维护；二进制带不了双语言 worker 环境。用户需求出现再议。
- **单发行包（三 import 包一 wheel）**：省 pin 机制，但集成方无法按层引用（WebUI 只要 runtime、第三方只要 core）；pin 机制已由 dynamic-versioning hook 一处解决，单包唯一优势消失。
- **不设 `[local]` / uvx 拉起作主路径**：同 venv 直调无包装层、离线、pin 锁死，三点全优；uvx 降为兜底且存废待实测。
- **CLI 上保留 `[aws]`**：裸装无一画像完整可用，头条命令撞头条用法。
- **`[deploy-aws]` 命名为 `[aws]` 或 `[deploy]`**：前者说谎（裸装已能用 AWS）并把 CDK+Node 引向不需要的人；后者关 provider 门。
- **维护者独占发布完整 worker 镜像**：确定性 step 是使用方地盘，worker 是 user-code image。
- **ECR Public / Docker Hub 作基底 registry**：运行时拉的是私有 ECR 定制镜像，ECR Public 的免流量/免认证优势碰不到；Docker Hub 匿名限额是负项。
- **IaC 单独 repo / 模板下载（Metaflow 式）**：第二 release train、第二版本号、硬编码值 bug 类（Dagster+ 模板硬编码 URL 致 EU 部署断）。
- **clone repo + 裸 `cdk deploy` 作正式部署形态**：相对路径、context 坑外露、wheel 用户不可达。
- **`--vpc` 只留 `default|new` 两档**：静默砍掉 [0033](./0033-iac-aws-backend-and-composition-wiring.md) 已定的 `vpc_id` 复用档，且以该档部署过的环境再 deploy 会合成危险变更集；三档齐全 + SSM 档三态比对。
- **`--vpc` 隐式默认**：漏 context 合成建新 VPC 的真踩坑，必给。
- **版本戳 / vpc 档由命令事后 `put_parameter`**：部署回滚会留错值；改 stack 资源与事务同生死。
- **靠 `uv-dynamic-versioning` 默认配置区分 dev/release**：默认 `dirty=false`，tag commit 上的脏构建与正式版逐字节同名，skew 跳过判据失效；故 style/strict/dirty 三项显式钉死。**反向也被拒——显式 `metadata = true`**：干净 tag commit 也带 `+<sha>`，发布 gate 必败、PyPI 拒收（真跑证实）；metadata 用默认。
- **使用方 steps 允许 `.ts`/`.js`**：模块体系取决于使用方目录的 `package.json#type`，无 package.json 的裸目录落 CJS 域、tsx ESM register 不生效、`import` 直接 SyntaxError；收敛到 `.mts`/`.mjs`。
- **midscene 使用方 steps 靠 Node 默认解析找 `@gherkai/worker-midscene`**：全局装/npx 形态下必 `ERR_MODULE_NOT_FOUND`；resolve hook（或退到依赖注入）。
- **steps 文件加载失败静默跳过**：把确定性 step 静默换成 AI catch-all、run 可能假通过；fail-loud。
- **`--no-report` 档产物落系统临时目录（清或不清）**：两种都是「还是生成了、只是换个地方」，与 `--no-report` 的字面含义相悖；改为不注入落点 + 令 worker 不生成/不上报（能关的关、Nova SDK 关不掉的留在其自身临时目录）。RunResult 因无 reportRef 也不再打印任何产物路径。
- **feature uri 继续相对某个「根」**：分发后没有 repo 根，任何根都随安装位置/CWD 漂移；用用户给出的路径原样。
- **手写 `==` 版本 pin / release 脚本改写 pyproject**：双真源、易漂移；hook 渲染一处解决。
- **npm 逐名防御占位**：scope 是原生命名空间；空壳可被争议转让。
- **兼容矩阵**：单旋钮 + skew 三态检查替代；无同类工具在此阶段维护矩阵。
- **skew 检查留 `--allow-version-skew` 放行口**：放行 = 让新 CLI 的 definition 进旧 Lambda，后果不可知且静默；uvx 按版本临时跑同版本 CLI 零成本，放行口没有真实需求，去掉后 push-worker 也不必再单独声明「不适用」。
- **Lambda asset / 基底镜像只从 PyPI 拉同版本**：dev 版不在 PyPI，contributor 即断；asset 从已安装包复制、基底 Dockerfile 留本地态。
- **boto3 驱动 CloudFormation 去 Node**：defer 非拒（见决策 6）。
- worker 镜像子系统的被拒方案（构建所有权、tag 命名、不可变 tag、family 取最新、强制 `--platform`、模板来源、指针重置、revision 删除时机等）在 [0038](./0038-worker-image-delivery.md)。

## 重议闸门

- 出现非 AWS 后端的真实需求 → 命令 `gherkai deploy` 的 provider 发现面已留，届时新增 `gherkai-deploy-<provider>` 包，本 ADR 不需改。
- 本地 browser 后端落地 → worker `--capabilities` 自述入口 + preflight/plan 消费（不回到安装期 extras 表达能力矩阵）。
- 定位链第四级实测不过 → 降级为报错指引，不引入进程包装层的 fd 转发补丁。
- midscene resolve hook 实测不稳 → 退到依赖注入形态（step 文件导出 `register(deterministic)`），Python 侧对称跟随以保两侧写法一致；Node 基线升到 ≥22.15 后可改用同步的 `module.registerHooks()`（Node 官方已在劝退异步 hook）。
- 去 Node 部署路线（CI 预合成模板 + boto3 驱动 CloudFormation）→ 有需求再评估参数化成本。
