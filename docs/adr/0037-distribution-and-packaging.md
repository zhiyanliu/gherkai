# 0037. 分发与打包：PyPI 多包 workspace（uv-first）+ `gherkai deploy` 进 wheel

> **Status:** Partially-superseded-by 0045, 0051（范围 = ①决策 8 ④：changelog 真源移到根 `CHANGELOG.md`、发布链加 CHANGELOG gate，见 [0045](./0045-documentation-layering-and-placement.md) 决策五；②决策 6 的 context 闭集加 `device_farm_project`、provider 契约的退出码加 `1`（cdk 之前找回或建立项目遇到权限以外的错误；见 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 10），均为加法扩展；其余决策不变）。原文：Accepted（2026-09-08）。「背景与问题」「现状实测」两节是**施工前快照、历史叙述**。这一篇描述的设计有一部分尚未实装，code 跟上之前，实际行为以 code 为准。

## 背景与问题

**既有 ADR（0001-0036）没有一条讨论「这个工具怎么分发」**——这是真空，不是待推翻的旧决策。唯一擦边的挂钩点是 [0033](./0033-iac-aws-backend-and-composition-wiring.md)「留待」节里被显式 defer 的「build & push ECR 全自动 CI（需先定仓库托管 + CI 凭证方案）」；仓库托管现已确定（github.com/zhiyanliu/gherkai，公开），前置条件成立。

当前（施工前）唯一的安装路径 = clone repo，在 repo 内建**四套**隔离环境（`cd cli && uv sync`、`engines/novaact` 下 `uv sync`、`engines/midscene` 下 `npm install`、云端部署再到 `iac_aws_backend` 下 `uv sync`），从 `cli/` 目录 `uv run python -m cli …`。README 与各子工程 README 都只教这一条；`cli/pyproject.toml` 声明了 console script `gherkai`、`cli/README.md` 有一处 `pip install cli[aws]` 的口吻，但没有任何文档教用户走到「安装后」那一步，且这条路**当前走不通**（下）。

### 施工前现状实测（历史快照——本 ADR 的证据基座；下列每一条今已被决策 1-8 改变）

| 实测 | 结果 |
|---|---|
| `uv build` 出的 `cli-0.1.0` wheel 元数据 | `Requires-Dist: core` / `Requires-Dist: gherkai` **裸名**——`[tool.uv.sources]` 的 path/editable 源不进发布元数据（`--no-sources` 产出字节相同，不存在「安全构建 flag」） |
| 安装该 wheel | `× No solution found … there are no versions of core and gherkai==0.1.0 depends on core`——PyPI 上 `core` 名被一个 2011 年发布、**零文件**的僵尸包占着（version 1.0.1、无 summary、无 URL），我们永远拿不到这个名字，且对方随时可上传文件把「装不上」变成「装错包」 |
| 装进干净 venv 后跑 local | `gherkai/gherkai/compose.py` 的 `repo_root()` = `Path(__file__).resolve().parents[2]`、无任何 env/flag 覆写口（生产侧唯一调用点在 `cli/cli/__main__.py`）；venv 里它指向 `<venv>/lib/python3.13`，两个 worker cmd 指向不存在的 `engines/novaact/.venv/bin/python` 与 `engines/midscene/worker/run-scope.ts`。实跑：`plan` 成功但标注降级（只依赖 gherkin 解析，[0036](./0036-deterministic-capability-discovery.md) 决策 4 的 best-effort）、`list-deterministic` 退 2 带「运行环境未装」文案、`run` 每个 job 报 `engine_error: 起 worker 失败` |
| 装进干净 venv 后 `submit --backend cloud` | **不依赖 engines 目录**——submit 路径只做 preflight + 写 definition，根本不建 engine（`build_fargate_engines` 是 `run --backend cloud` 与 Lambda 侧的事，且只用 `gherkai.names` 命名规则）。`repo_root()` 的其余消费点有三处、都不在 engine 装配里：`_submit_local` 与 `--expose-local` 的 tunnel-watch 都把它作子进程 cwd；`load_feature` 用它派生 feature 的 uri（= `scenario_id`/`scope_id` 的前缀）——wheel 装法下 feature 不在其下、退用绝对路径，scope_id 形状随安装形态与 CWD 漂移。「wheel 用户能提交到已部署的云端、但跑不了 local」是当前代码的真实形状 |
| 顶层 import 包名碰撞（`core`/`cli`） | 与另一个同样带顶层 `core/` 的发行包同装：pip/uv **零告警**、两包文件合并进同一个 `site-packages/core/`、`__init__.py` 被静默覆盖；卸载对方时按其 RECORD 删掉 `core/__init__.py`，我们的包退化成隐式命名空间包、`from core import X` 半死不活。PyPA 明文：发行名与 import 名之间不强制任何关系 |
| 部署后端 | `iac_aws_backend/stack.py` 现场 `copytree` 仓库相对路径 `../lambdas`、`../core/core`、`../gherkai/gherkai` 拼 Lambda asset，再在 synth 时**联网**从 PyPI `uv pip install --target` 装 `gherkin-official`（boto3 靠 Lambda runtime 自带）；`cdk.json` 的 app 是 `uv run python app.py`；`cdk` CLI 不在任何 Python 依赖里、靠 npm 全局安装。IaC 工程假定自己躺在 monorepo 里 |
| 版本 | **五份** pyproject（`cli`/`core`/`gherkai` 三个发行包 + `engines/novaact`、`iac_aws_backend` 两个非包工程）全 `0.1.0`，`engines/midscene/package.json` 另写 `1.0.0`——六处手写版本、零真源；而 [0016](./0016-execution-architecture-core-lib-run-model.md) 版本切分已按 SemVer 宣布 v1.0-v1.3 完成，叙事完全脱钩 |
| 依赖共解 | `nova-act>=3.4.187.0` + `boto3>=1.34` + `gherkin-official>=31` + `aws-cdk-lib>=2.150` 一个 venv 内 `uv lock`：107 包**零冲突**——「worker 必须独立 venv」不是依赖冲突所迫 |

### 业界现状（2026，为选型提供的外部事实；一手来源登记在 [docs/ai-eng/REFERENCES.md](../ai-eng/REFERENCES.md)「发行与打包」节）

- **PyPI + uv 是事实默认**：uv 月下载量约为 pipx 的 28 倍（pypistats，2026-08 采样）；pipx 自己加了 uv backend；抽样的同类 Python CLI（harlequin / posting / llm 三个 README）均以 `uv tool install` 领头、pipx 作回落。PyPA 官方指南仍只写 pipx——官方与生态已分叉，本项目跟生态。
- **`uvx <name>` 把 `<name>` 同时当发行名与命令名解析**（实测：发行名 `gherkai-cli` + 命令 `gherkai` 时 `uvx gherkai` 直接失败）→ 用户敲的那个发行包必须叫 `gherkai`。
- **uv 不会把 path/workspace 依赖翻译成版本 pin**（astral-sh/uv#9811，`needs-design`、至今 open）；生产级绕法 = pydantic-ai 的形状：`uv-dynamic-versioning` 既从 git tag 算版本、又在 build 时经 hatch metadata hook 渲染 `pydantic-ai=={{ version }}`（`clai` 2.31.1 在 PyPI 上的元数据即 `Requires-Dist: pydantic-ai==2.31.1`）。
- **形态相同的工具如何分工**（CLI + 用户自部署后端 + worker 容器）：Chalice 把 IaC 塞进 wheel 变 `chalice deploy` 并留 `package --pkg-format cloudformation` 导出阀；Dagster「chart 版本 = 包版本，镜像 tag 缺省跟 chart」一个旋钮；Prefect 用一句操作规则替代兼容矩阵；**内容属于用户的镜像一律由用户构建**（Dagster user-code deployment / Prefect flow image），内容属于工具提供方的由工具提供方发布。
- **Homebrew core 门槛**：≥75 star 或 30 fork，且仓库 ≥30 天；本仓库不达。第三方 tap 是第二个发布面。

## 决策总览

| 交付物 | 通道 | 版本 | 谁构建 |
|---|---|---|---|
| `gherkai`（CLI；含随 wheel 带的 `gherkai_cli/skills/gherkai/` 包数据 = agent skill，[0043](./0043-agent-skill-for-driving-gherkai.md)） | PyPI，uv-first | git tag 派生（2b） | 发布方的 CI |
| `gherkai-runtime` / `gherkai-core` | PyPI，被 `==` 同版本 pin；CLI 用户不直接装（集成方按层直依赖，见 2a） | 同号 | 发布方的 CI |
| `gherkai-worker-novaact` | PyPI，经 CLI extra `[local]` 装进 **同一个** venv | 同号 | 发布方的 CI |
| `@gherkai/worker-midscene` | npm（scope `@gherkai`） | 同号 | 发布方的 CI |
| worker **基础镜像** ×2 | **GHCR**（与 repo 同屋檐），linux/amd64，immutable `:X.Y.Z` | 同号 | 发布方的 CI |
| worker **定制镜像**（基础镜像 + 使用方 steps，按 variant 多套并存） | 使用方私有 ECR；机制全在 [0038](./0038-worker-image-delivery.md) | 不带版本：tag 即变体名，worker 协议版本由镜像标注带着（决策 5、7） | 使用方本地 build，部署方 `gherkai deploy push-worker` 推送注册 |
| `gherkai-deploy-aws`（IaC + Lambda handler 源 + worker 镜像推送） | PyPI，经 CLI extra `[deploy-aws]`；命令 `gherkai deploy` / `destroy` 及 worker 镜像族（0038） | 同号 | 发布方的 CI |
| 上表之外的仓库目录（`features/` 示例、`tools/`、`docs/`、`graphify-out/`、根 `skills/` 的评测资产等） | 不分发 | — | — |

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

- **唯一硬约束：用户敲的发行名 = 命令名**（`uvx` 解析规则）→ CLI 发行包叫 `gherkai`，施工前的中间层 `gherkai` 让位改 `gherkai-runtime`。
- **import 包全部带 `gherkai_` 前缀**：`core`/`cli` 作顶层 import 名是静默合并/互删的碰撞源（见实测）；改名是机械 sweep（`from core.` → `from gherkai_core.`），随发行重组一次做完。
- **发行名带 `gherkai-` 前缀**：PyPI 无 scope，前缀是唯一命名空间手段；`gherkai-cli`、`gherkai-worker-midscene` 两个名字作**防混淆占位**（前者是用户最自然的误猜，后者防人以为 midscene worker 是 pip 包），永不发真内容。
- **多包而非单包**：集成方按层引用——未来 WebUI 只依赖 `gherkai-runtime`、第三方只解析 feature 就依赖 `gherkai-core`（零 boto3）、Lambda asset 只装 runtime。单发行包（三 import 包一 wheel）曾是备选（省掉 pin 机制），因「按层引用」这个真实需求被拒；pin 机制由 2b 解决后单包的唯一优势消失。
- **分层不动**：`gherkai_cli → gherkai_runtime → gherkai_core` 的依赖方向、窄腰红线、组合根注入（[0016](./0016-execution-architecture-core-lib-run-model.md)）全部保留，本 ADR 只动名字与打包边界。

### 2b. 版本：git tag 唯一真源，兄弟包 `==` 同版本 pin，不做兼容矩阵

- **git tag `vX.Y.Z` 是唯一版本真源**，pyproject / package.json 不再手写版本号（施工前的六处手写版本已作废）。构建后端 hatchling + `uv-dynamic-versioning`：`[tool.hatch.version] source = "uv-dynamic-versioning"` 派生版本；`[tool.hatch.metadata.hooks.uv-dynamic-versioning] dependencies = ["gherkai-runtime=={{ version }}"]` 在 build 时渲染精确 pin；`[tool.uv.sources] gherkai-runtime = { workspace = true }` 让本地开发走 path。三段与 pydantic-ai `clai` 的生产配置写法相同。
- **`[tool.uv-dynamic-versioning]` 三项显式钉死（style / strict / dirty），`metadata` 有意留默认**：`style = "pep440"`（上游文档对默认 style 自相矛盾，而纯发行版本的判据建立在 PEP 440 形态上）；`strict = true`（无 tag 时 build 失败，而非静默回落 `0.0.0`）；`dirty = true`（默认关；关着则 tag commit 上带未提交改动构建出的版本与正式发行版逐字节相同，基础镜像同步与定位链第四级用到的纯发行版本判据会把脏构建当成正式版）。**`metadata` 不显式开**：dunamai 默认 = 非 tag commit 或脏树才带 `+<sha>`/`+dirty`；显式 `metadata = true` 会让**干净 tag commit** 也算出 `1.4.0+<sha>`——发布 gate「版本==tag」必败、PyPI 拒收本地段版本，链路按那配置永远发不出去（真跑证实：五个 pyproject 曾这样配，对抗核验在真 clone + 真 tag 上抓出）。三种 git 状态实测：干净 tag → `1.4.0`；脏树 → `1.4.0+dirty`；离 tag N 提交 → `1.4.0.postN.dev0+<sha>`（默认 `bump=false`、commit 无前缀）——非纯净构建必带 `+`，纯发行版本的判据成立。
- **hook 的硬约束（实现者必读）**：启用该 metadata hook 的包，`dependencies` 与 `optional-dependencies` 必须**整体**搬进 hook 表、`[project]` 侧删除并声明 `dynamic = ["version", "dependencies", "optional-dependencies"]`——静态与动态不能共存，不含模板的条目也一起搬。只有 `gherkai-core` 与 `gherkai-worker-novaact`（两者都无兄弟包 pin）不需要依赖 hook、只 `dynamic = ["version"]`；`gherkai-deploy-aws` 没有 extras，只声明 `dynamic = ["version", "dependencies"]`。2c 的依赖表因此是**渲染后的等效依赖**，不是 pyproject 字面内容。
- **为何 `==` 不是 `>=`**：三个包是同一 repo 切出的切片，内部契约随时一起动；`>=` 会让 resolver 装出从未测过的混搭（`gherkai 1.5 + gherkai-core 1.4`）。`==` 让这种组合**在安装层就不存在**，兼容性问题被分发机制消灭而非靠文档管理。代价「每次全家一起发」在 monorepo 单 release train 下为零。
- **同 repo 所有 workspace 成员的版本从同一 git 状态派生**，天然同号：本地 dev 版本两侧一致、pin 自满足。**editable 安装的元数据版本是 `uv sync` 时算出的快照**，工作树之后再改、版本串不会自动变——凡从 `importlib.metadata` 读版本的地方（`--version`、版本戳、定位链第四级）都以此为限，contributor 在 dev 树上操作前先 `uv sync`。
- **npm 侧的版本真源同样是 git tag、但机制不同**：`package.json` 常驻占位 `"version": "0.0.0-dev"`，CI 发布时 `npm version X.Y.Z --no-git-tag-version` 写入 tag 版本再 publish；**非纯净版本永不发 npm**（只有 CI 从 tag 发），故不需要 PEP 440→semver 的转换件（release 形态 `X.Y.Z` 两边写法相同，`.dev`/`.post`/`+` 形态不是合法 semver、也不会到 npm）。contributor 本地态基础镜像 build 用 dev 树 `npm pack` 出的 `0.0.0-dev` tarball 即可——基础镜像内容由 tarball 决定、不由版本串决定。
- **代码内版本**经 `importlib.metadata.version("gherkai")` 读取，不复制；CLI 加 `--version`。
- **首发版本号接续 [0016](./0016-execution-architecture-core-lib-run-model.md) 的版本叙事、不倒回 0.x**：1.0 的稳定承诺是已做过的决策，公开发行从头计数是对叙事说谎。本 ADR 的完成线并入 0016 版本切分的 v1.4.0（与阅读理解层、AI skills 暴露同一完成线），PyPI 首发即 1.4.0。
- **不做兼容矩阵**：同类工具在 0.x/1.x 阶段无一维护矩阵。能不能一起工作由数据版本判断（决策 7）。

### 2c. extras 边界：`[aws]` 只在库层，CLI 上三个正交 extra

```
gherkai ──hard──▶ gherkai-runtime[aws]=={{v}} ──▶ gherkai-core[aws]=={{v}} ──▶ boto3
   │                    └──▶ boto3 + botocore（云端钩子直接 import）
   │                    └──▶ packaging + rich              └──▶ gherkin-official
   ├─[local]──────▶ gherkai-worker-novaact=={{v}} ──▶ nova-act + bedrock-agentcore + boto3 + botocore + urllib3
   ├─[deploy-aws]─▶ gherkai-deploy-aws=={{v}} ──▶ aws-cdk-lib + constructs + boto3 + packaging + gherkai-runtime[aws]=={{v}}
   └─[tunnel]─────▶ gherkai-runtime[tunnel]=={{v}} ──▶ ngrok（隧道的 SDK，runtime 的 tunnel.py 直接 import）
```

直接 import 就直接声明：`gherkai` 与 `gherkai-deploy-aws` 都直接 import core 的模型与 adapter，故各自也直接声明 `gherkai-core[aws]=={{v}}`，不靠 runtime 的同版本 pin 传递（图中略）。

| 包 | 硬依赖（渲染后等效） | extras |
|---|---|---|
| `gherkai-core` | `gherkin-official>=31.0.0` | `[aws]` = `boto3>=1.34`（DDB/S3 store、FargateEngine、CloudLauncher 等 adapter） |
| `gherkai-runtime` | `gherkai-core=={{ version }}`、**`packaging>=24`**（纯发行版本的判据；施工前 venv 里能 import 到纯属 pytest 的传递依赖，生产路径必须自己声明）、`rich>=13`（人读输出的表格与树，[0047](./0047-cli-human-readable-tables-with-rich.md)） | `[aws]` = `gherkai-core[aws]=={{ version }}`、`boto3>=1.34`、`botocore>=1.34`（compose 的云端钩子直接 import boto3 建 client、直接 import botocore 的 `ClientError` / `BotoCoreError`，直接 import 就直接声明、不靠 core 传递）；`[tunnel]` = `ngrok>=1.8.0`（ngrok 官方的 Python SDK，`tunnel.py` 直接 import；下限取实测的版本，[0035](./0035-local-app-testing-via-tunnel.md) 决策 1） |
| `gherkai`（CLI） | **`gherkai-runtime[aws]=={{ version }}`**、`gherkai-core[aws]=={{ version }}`（命令行直接 import core 的模型、序列化与 adapter，直接 import 就直接声明、不靠 runtime 传递） | `[local]` = `gherkai-worker-novaact=={{ version }}`；`[deploy-aws]` = `gherkai-deploy-aws=={{ version }}`；`[tunnel]` = `gherkai-runtime[tunnel]=={{ version }}` |
| `gherkai-deploy-aws` | `gherkai-runtime[aws]=={{ version }}`、`gherkai-core[aws]=={{ version }}`（Lambda handler 源直接 import core，Lambda asset 也从已安装的 core 复制）、`aws-cdk-lib>=2.150.0`、`constructs>=10`、`boto3>=1.34`、`packaging>=24`（deploy 命令直接 import boto3 建 client、直接 import packaging 校验版本戳的形态（PEP 440 版本或 `unknown`），直接 import 就直接声明） | 无 |
| `gherkai-worker-novaact` | `nova-act==3.4.187.0`（SDK 钉精确版本，[0042](./0042-step-evidence-and-explain.md) 决策六）、`bedrock-agentcore==1.22.0`（worker 直接用它的 `BrowserClient` 做会话的 Start / Stop，[0028](./0028-transient-network-ssl-resilience.md)「会话泄漏防护」；nova-act 对它只声明范围，故同样锁定精确版本）、**`boto3>=1.34`**、**`botocore>=1.34`**、**`urllib3>=2`**（worker 自己直接 import 这三个包：boto3 建 client，botocore 的 `Config` 配置三条 I/O 边缘的 client，botocore 的网络异常类型与 urllib3 的 `ProtocolError` 用于判定网络瞬时故障；直接 import 就直接声明、不靠 nova-act 或 boto3 传递；对 Playwright 私有错误类型的导入带 ImportError 回退、属可选探测，不在此列） | 无（**不依赖 gherkai-core**：worker 讲协议、零 core 依赖，[0024](./0024-worker-core-protocol.md)） |

- **CLI 硬依赖 boto3（反转 [0016](./0016-execution-architecture-core-lib-run-model.md)「cli `--backend {local,cloud}`」节 `build_cloud_stores` 条的「cli 主依赖不含 boto3，走 `cli[aws]→core[aws]` extra」）**：按用户画像过一遍，裸装 `gherkai` 时没有任何画像能跑起完整用法——提交 cloud run 要 boto3；local 跑 novaact 装 `[local]` 而 nova-act 自带 boto3；只剩「仅跑 midscene 的 local 用户」与「只 `plan`」两种边缘画像省下一次安装体积。而 `[aws]` 留在 CLI 上的摩擦落在头条用法：`uvx gherkai submit --backend cloud` 会因缺 boto3 失败、要改写成 `uvx --from 'gherkai[aws]' gherkai …`。**code 层不变量不动**：local 路径**绝不 import boto3**靠懒加载保证（`compose` 的 `_make_*` 钩子），与安装期是否装了 boto3 无关。
- **`[aws]` 保留在 core 与 runtime 层**：[0030](./0030-realtime-persistence-seam.md) 决定六守的本来就是「core 作为库可轻量 import、不被 boto3 绑死」，针对的是库消费者；库层保留 extra 完整兑现它。
- **`[local]` 存在且语义 = local 后端的 Python 侧 worker**（决策 3）；**不设** `[local]` 曾是备选（理由「worker 独立 venv、extras 够不到」），被「安装与拉起正交 + 共解实测」推翻。
- **`[deploy-aws]` 不叫 `[aws]`、不叫 `[deploy]`**：`[aws]` 会说谎——裸装已能用 AWS 后端，团队成员见 `[aws]` 必以为提交云端要装它、把 CDK 与 Node 依赖拉进机器；`[deploy]` 会关上 provider 那扇门（决策 6）。**`[deploy-aws]` 的语义 = 改云端环境所需**：供给后端（CDK）+ 变更后端用的 worker 镜像（[0038](./0038-worker-image-delivery.md) 的推送与注册都是云端写操作）；镜像**构建**是测试开发自己的容器工作、gherkai 不拥有。只提交 run 的人不需要装它。默认画像是一人兼测试开发与部署方两顶帽子、装它；团队拆角色时写 step 的人可不装、把本地镜像交给部署方。extras 名按 PEP 685 规范化，`deploy_aws` 等价。
- **`[tunnel]` 的语义 = 隧道暴露所需**（`--expose-local`，[0035](./0035-local-app-testing-via-tunnel.md)）：隧道建在宿主进程里，所用的 SDK（PyPI 上的包名 `ngrok`）由 runtime 的 `tunnel.py` 导入，按「直接 import 就直接声明」由 runtime 的 `[tunnel]` 声明，CLI 的 `[tunnel]` 只 pin 同版本的 `gherkai-runtime[tunnel]`；与 `[local]`、`[deploy-aws]` 正交，使用者装 `gherkai[tunnel]`；workspace 根的依赖同样带上它（`gherkai[local,deploy-aws,tunnel]`），contributor 的开发环境与 CI 一次 `uv sync` 即装上 SDK。SDK 只在给了 `--expose-local` 时导入（与本机路径不 import boto3 同一种懒加载），没给时装不装都没有影响；给了时 `run` 与 `submit` 共用的前置检查真正导入一次，能导入才算装好。被拒：只看包能否被找到、不导入——找得到却加载不了的安装（这种情形可以复现）会被放过，到起隧道时才失败，那时安装包已经上传、后台进程已经启动。缺了它时在哪一步查出、怎样报错，见 0035 决策 1「前置条件」与「启动失败的说法按原因分」两条。SDK 发行包的许可、依赖、要求的 Python 版本与预编译包的平台，实测见 0035 决策 1「实测依据」里「发行包」一条；它要求的 Python 版本在 2d 的下限之内。

### 2d. `requires-python >=3.13` 维持

uv 缺 Python 时自动下载托管 CPython，对 uv-first 受众近乎免费；pipx 默认不下载解释器，用户文档须写 `pipx install --python 3.13 --fetch-python missing gherkai` 作回落（现落在用户指南「开始使用」页的安装步骤；`--fetch-python missing` 只在**点名的**版本本地没有时才下载，不点名则用默认解释器、低于 3.13 即失败）；裸 `pip install` 在 3.13 以下解释器上失败是接受的边界，不为迎合它降下限。

## 决策 3：worker 运行时的交付——安装与拉起正交，四级定位链，`repo_root()` 全部消费点退役

**安装**（谁把 worker 放到机器上）与**拉起**（谁 spawn 它）是两件事。施工前二者被 `repo_root()` 绑死：cmd 直指 repo 内 `engines/novaact/.venv/bin/python` 与 `node --import tsx engines/midscene/worker/run-scope.ts`、cwd = 各引擎目录。

- **Python 侧（novaact）：包化 + 装进 CLI 同一个 venv**（经 `[local]`），并声明 console script `gherkai-worker-novaact`（定位链第三级的 Python 侧供给方）。spawn cmd = `[sys.executable, "-m", "gherkai_worker_novaact"]`——**无包装层**（EVENTS_FD 经 `pass_fds` 直达，midscene 换 `--import tsx` 那次踩的「包装进程吞 fd3」坑在此路径不存在）、离线可用、版本由 `==` pin 与 CLI 锁死。「worker 独立 venv」的三条理由逐条审过：依赖隔离（共解实测通过，不成立）、双语言（只影响 midscene）、架构边界（worker 零 core 依赖靠代码纪律不靠 venv）——前提松动，同 venv 成立。
- **Node 侧（midscene）：npm 包 `@gherkai/worker-midscene`**，pip extras 够不到 Node 地盘。使用方 `npm i -g @gherkai/worker-midscene`（提供 bin `gherkai-worker-midscene`，即定位链第三级）；**midscene 无第四级兜底拉起**——npx 不把 EVENTS_FD 传给 node 子进程、事件全丢，理由见下「worker 定位链」第 4 级与「被拒方案」节『进程包装层的 fd 转发补丁（为救 npx 兜底）』条。**发布形态定死**：统一 ESM（`"type": "module"`、tsconfig 入库——包化前刻意不带 tsconfig、靠 tsx 运行期扩展名重写，包化后不再成立）、tsc 产 `dist/`、`engines.node >= 22`（与基础镜像 `node:22-slim` 同源）、bin 入口在进程内注册 `tsx/esm/api`（进程不再由 `node --import tsx` 启动）。**使用方 step 文件只认 `.mts` / `.mjs` 两个扩展**：tsx 的 ESM register **只对 ESM 生效**——`.mts`/`.mjs` 恒为 ESM，而 `.ts`/`.js` 的模块体系由离文件最近的 `package.json#type` 决定，使用方（Python CLI 用户，项目 = `features/` + `steps/`）目录多半根本没有 package.json、会落进 CJS 域，step 文件里的 `import` 直接 SyntaxError。收敛到与使用方目录无关的两个扩展（当前实现在收集阶段就按扩展名过滤——`.ts` / `.js` 文件根本不会被 import，使用者观察到的是**静默跳过**、清单里没有它，不是 SyntaxError），比要求使用方维护 package.json 或双注册 cjs/esm loader 都简单可靠（脚手架与文档统一用 `.mts`）。**运行时依赖必须从 `devDependencies` 挪到 `dependencies`**：包化前靠 `npm install` 全装才活（[0033](./0033-iac-aws-backend-and-composition-wiring.md) 记的「不能 `--production`」陷阱），作为被消费的 npm 包只会装 `dependencies`、不挪即崩；`tsx` 因此成为 runtime dependency。
- **worker 定位链**（组合根 `compose.build_engines` 解析，**取代 `repo_root()`**，dev 与分发**同一条链、不设 dev 模式特判**——分发后没有 repo，任何靠 repo 结构的隐式行为都是漂移面）：
  1. env `GHERKAI_WORKER_<ENGINE>_CMD`（`NOVAACT` / `MIDSCENE`，`shlex` 拆分）+ 可选配套 `GHERKAI_WORKER_<ENGINE>_CWD`——显式覆写，contributor 指向 repo 内源码、调试、自定义 worker 都走这里（cwd 配套存在的原因：`node --import tsx` 的裸 specifier `tsx` 按 cwd 上溯 `node_modules` 解析，实测在无关目录下直接 `Cannot find package 'tsx'`）；
  2. 同 venv 入口（Python 引擎）：`importlib.util.find_spec("gherkai_worker_novaact")` 命中 → `sys.executable -m …`；
  3. PATH 上的可执行 `gherkai-worker-novaact` / `gherkai-worker-midscene`（`shutil.which`）；
  4. 兜底拉起：`uvx gherkai-worker-novaact==<CLI 版本>`（**仅 novaact**；这里的发行版本是取哪一份 worker 包的缺省，不是兼容判断，决策 7「发行版本作为取哪一份的缺省」），**双条件**：①该版本是纯发行版（无 `.dev`/`.post`/本地段——非纯净版本按 2b 从不上 PyPI，拿它 uvx 只会解析失败，把「worker 没装」的清晰指引换成难懂的网络/解析错误）；②`uvx` 在 PATH。任一不成立即跳过本级、直接判 miss 报安装指引。**这不是「dev 模式特判」**：判据是版本串形态、与有没有 repo 无关（dev 树上 novaact 本来就在第二级命中，见下「contributor 代价点」）。fd 预演已做（本地 wheel/tarball 经 `uvx --from` / `npx -p` 拉起，父侧 pipe 与子进程里 EVENTS_FD 比 inode + 收事件）：**uvx 穿透**——子进程拿到同一条 pipe、事件到达、SIGTERM 也被 uvx 转发给子进程（uvx 是中间进程但不吞 fd、不吞信号）；**npx 不穿透**——node 子进程里 EVENTS_FD 号上是 npm 自己的另一条 FIFO、写即 EBADF、事件全丢。故 midscene **无第四级**，前三级全 miss 即报安装指引（`npm i -g @gherkai/worker-midscene`）；不引入进程包装层的 fd 转发补丁（被拒方案）。
- **miss 语义按调用点分叉，不在定位链里统一决定退出码**：定位链四级全 miss → 抛结构化异常（引擎名 + 该引擎的安装指引：novaact → `uv tool install 'gherkai[local]'`；midscene → `npm i -g @gherkai/worker-midscene` + Node ≥22），由调用点处置——`run`/`submit` 在 spawn 前退 2（不再进 job 级 `engine_error`）、`list-deterministic` 退 2、**`plan` 保持 [0036](./0036-deterministic-capability-discovery.md) 决策 4 的 best-effort 降级**（只丢该引擎标注 + stderr 警告，plan 本体照出）。
- **worker 不再有专属 cwd；`--no-report` = 真不生成产物**（本条只管本机后端 subprocess 的落点；云端后端落点由 `build_fargate_engines` 注 S3）：归集方式的产物经 `NOVA_LOGS_DIR` / `MIDSCENE_RUN_DIR` 落 `<report_dir>/<run_id>/` 绝对路径（compose 既有约束）。`--no-report` 方式**不注入落点**，并经 env `GHERKAI_NO_ARTIFACTS=1` 令 worker **不生成、不上报**引擎原生产物：Midscene 关 agent 的 `generateReport`、不提前上传 log、不带 report ref；Nova Act SDK 没有关闭 trajectory 的开关，此时不传 `logs_directory`、由 SDK 写进自己 `mkdtemp` 的临时目录（SDK 内部行为、不进项目），worker 不收集 trajectory、不带 summary、不发任何 reportRef；Midscene SDK 即便不出 report 也可能往 `./midscene_run`（相对 cwd）写 log/dump，`--no-report` 且无 `MIDSCENE_RUN_DIR` 时 worker 自己把它导到一次性临时目录。`--no-report` 只有 `run` 有，`run` 只有本机后端（[0016](./0016-execution-architecture-core-lib-run-model.md) 决策 A）。去掉专属 cwd 前，`--no-report` 方式的产物曾落引擎目录；曾一度改为「落系统临时目录、不清」，被否——`--no-report` 的含义就是不生成 report，用户不该在临时目录里收到一堆产物。
- **`repo_root()` 的另两类消费点一并退役**（否则 wheel 用户的行为随安装位置漂移）：①**子进程 cwd**——`_submit_local` 启动的后台推进进程与云端 `submit` 启动的隧道守护进程（tunnel-watch；各组合的隧道宿主见 [0035](./0035-local-app-testing-via-tunnel.md) 决策 3「三种组合的宿主与次序」）都改为继承提交进程的 CWD，启动时不把当前目录放进模块搜索路径（解释器的 `-P`）：这个当前目录是使用方的项目目录，不这样做时项目里与标准库或依赖同名的文件会先被导入；②**feature uri 基准**——`load_feature` 曾把路径相对 repo 算 uri（`scenario_id`/`scope_id` = `<uri>:<line>`），改为**用户给出的路径经规范化后原样**（相对给相对、绝对给绝对，不再相对任何「根」）。已知影响：scope_id 形状变化 → local report 目录名与 DDB 键随之；run 是短命数据、无跨版本读取需求，接受。
- **contributor 代价点（明示）**：dev 态 novaact 是 workspace 成员、editable 装进同 venv，定位链第二级直接命中；midscene 无已安装 npm 包，须走第一级 env 覆写（cmd + cwd 两个 env，可放 `.envrc` / uv env-file 一次配好），比包化前多一步。

## 决策 4：确定性 step 的定制面——`steps/` 目录约定 + env 注入，local/cloud 同一机制

确定性 step 注册表活在 worker 代码里、由使用方测试开发维护（[0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)/[0036](./0036-deterministic-capability-discovery.md)：`@deterministic(正则)` 装饰器，TS/Python 两份对称）。施工前「定制」= 直接改 repo 里的 `worker/deterministic_steps.py` / `worker/deterministic.steps.ts`（fork 模式；两引擎各只有一条生效的内建注册——页面地址匹配），在 clone-repo 分发下成立、在 PyPI 化后不成立——该落点由 [0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md) 决定 2 定、经 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)「迁移」条移入 `worker/`（本 ADR 对它的反转见下「对既有 ADR 的影响」）。**定制面必须先画清**——它同时决定基础镜像的切面（决策 5）与 local 分发形态（决策 3）。

- **约定 = 使用方项目内的 `steps/` 目录**（测试资产同处：使用方的「项目」= `features/` + `steps/`），**不相对 repo、不相对 worker**。`steps/` 是项目级注册表、不按 feature 分；两引擎扫同一目录、各取自己的扩展名（`login.py` 与 `login.mts` 成对、同一正则）。
- **解析在组合根、随 definition 持久化、worker 只认 env**：提交侧（`run`/`submit` 的 CLI 进程）按 `--steps-dir` flag > env `GHERKAI_STEPS_DIR` > 项目配置文件的 `steps-dir`（相对配置文件所在目录，[0053](./0053-project-config-file.md) 决策 2 加的一层）> 默认 `./steps`（相对**提交时** CWD，存在才用）解析成绝对路径，**这个值进 definition（`RunMeta.steps_dir`，必有键，无使用方 step 为 null，见决策 7；载体惯例同 `extra_http_headers` 的 [0035](./0035-local-app-testing-via-tunnel.md) 先例与 `max_concurrency` 的 [0034](./0034-detached-batch-reconciler.md)）**；起 worker 的宿主都用这次写下的那份 definition、不重解析 `./steps`：本机的两个宿主（前台 `run` 的进程、后台推进进程）用自己生成的那份，不从记录读回，经 env `GHERKAI_STEPS_DIR` 注给 worker；云端推进器从记录读回（云端的这个字段为 null，见本决策末条）。后台推进进程与提交它的 CLI 是各自的组合根（[0034](./0034-detached-batch-reconciler.md) local 一节），它生成 definition 所用的 steps 目录是 `submit` 解析好的值（绝对路径，没有使用方 step 时为空）、经标准输入交来，它自己不解析（不从记录读回的理由见 0034 local 一节的被拒方案）。「用到哪套确定性 step」属于 run 定义、影响判定可复现性，随 definition 走，起 worker 的是哪个进程都用同一套。约定逻辑不进 worker，worker 保持薄（[0016](./0016-execution-architecture-core-lib-run-model.md) 分层）。worker 定位链的 env 覆写同理对两个宿主可见：后台推进进程继承提交进程的 env。**组合根拥有的五个 worker env「有值显式注、无值显式清」**（`GHERKAI_STEPS_DIR` / `GHERKAI_NO_ARTIFACTS` / `GHERKAI_EXTRA_HTTP_HEADERS`（[0035](./0035-local-app-testing-via-tunnel.md) 决策 4）/ `GHERKAI_SESSION_WARMUP_URL`（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 13，与额外请求头同源于 definition、同一注入面）/ `RUN_ID`（本 run 的 id，起 worker 的宿主都持有，两个 worker 用它编码会话名的 run 段——设备远程访问会话名与桌面 `StartBrowserSession` 请求名，[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 3、4；注入路径见 [0024](./0024-worker-core-protocol.md)「run_id + scope_id 注入 worker」条））：宿主建注入 env 时先把这五键从继承的环境里抹掉、再按 definition 的值注——只做加法的注入会让宿主 shell 里的同名值越过 definition（definition 说「无使用方 step」也拦不住：宿主环境里 export 的 `GHERKAI_STEPS_DIR` 会让 worker 加载那个 step 目录、判定不可复现）。边界=**只清 gherkai 自有键**：`NOVA_LOGS_DIR` / `MIDSCENE_RUN_DIR` 是 SDK 旋钮，其「不给值」的契约就是回落 SDK 默认（SDK 默认本身含读自己那个 env），有意不清——被接受的代价：`--no-report` 方式下若宿主继承了 `MIDSCENE_RUN_DIR`，SDK 仍可能往那儿写 log/dump。云端后端不需要对称处理（RunTask overrides 是显式列举、容器无宿主 env 继承面）。
- **worker 启动时加载该目录（两侧对称）**：novaact 按**排序**递归遍历 `*.py`（排除 `_*` 与 `test_*`），以合成包名（相对 steps 根的路径转模块名、挂在 worker 私有命名空间下，防与 `sys.modules` 撞名）import，文件顶层 `from gherkai_worker_novaact.deterministic import deterministic` 后的 `@deterministic` 副作用完成注册——与当前脚手架的注册机制**完全同一**（[0036](./0036-deterministic-capability-discovery.md) 决策 1 的 description/example 必填照守）；**steps 根不入 `sys.path`**（防使用方文件名遮蔽标准库/第三方包）。midscene 按排序递归动态 import `*.mts`/`*.mjs`（排除 `_*` 与 `*.test.*`；扩展收敛理由见决策 3），文件写 `import { deterministic } from "@gherkai/worker-midscene"`。**两侧的 `_*` 排除必须同时在**：同一份 `steps/` 目录要能在两个引擎上承载同样的内容，且下条零注册守卫对每个被收集的文件开火——少了这条排除，使用方在 `steps/` 里放任何不注册 step 的辅助模块（页面对象、选择器常量、共享 helper）都会让该引擎的 worker 起不来，连带一种误报：辅助模块若排序在前先被自动加载、真正 import 它的 step 文件就会命中 ESM 缓存不再注册，守卫报到那个无辜的文件头上。**`_` 判在路径的任一段上**（两引擎同规则）：`_selectors.mts` 与 `_pages/selectors.mts` 都不自动加载，故辅助模块既可按文件前缀标、也可按目录分组，被排除的目录整棵不进收集——只判文件名时 `steps/_pages/` 这种自然写法会原样撞上零注册守卫（诊断还把人指向双实例，离真因极远）。**目录级排除同样必须两侧同时在**：只在一侧做，放进 `_pages/` 的注册文件会在一个引擎注册、在另一个引擎静默落回 AI——比两侧都起不来更坏。辅助模块被 step 文件相对 import 照旧生效（它只是不被自动加载）。**符号链接两侧同一规则**：名字筛选看链接自身的名字；指向文件的链接两侧都收进清单、按目标加载，指向目录的链接两侧都不进入；悬空链接只要名字通过筛选就收进清单、在加载时点名报错，名字通过筛选却指向目录的链接同样点名报错，都不静默跳过。理由与 `_*` 那条同源：只在一侧收，同一个文件就会在另一个引擎上静默落回 AI。
- **midscene 裸 specifier 的解析是一条独立决策，不能靠 Node 默认解析**：Node 只沿 step 文件所在目录上溯 `node_modules`、不认全局根与 npx 缓存（实测），全局装/npx 形态下使用方 steps 必 `ERR_MODULE_NOT_FOUND`；云镜像同样不能靠默认解析：基础镜像用 `npm install -g` 把 worker 装进全局根，定制层的 `/app/steps` 上溯找不到它；即使某种镜像布局让上溯恰好命中（如把 worker 用 `npm ci` 装进 `/app`，`/app/steps` 上溯命中 `/app/node_modules`），那也是巧合、不能当机制。**机制 = worker 注册 resolve hook（`module.register`）把该裸 specifier 映射到自身安装位置**，落点与不变量：①hook 是随 `dist/` 发布的独立入口文件（hook 跑在独立 loader 线程、不能是闭包），目标 URL 经 `register(spec, parent, { data })` 传入；②**目标 URL 必须是 worker 自身已加载的同一个 URL**——从 `import.meta.resolve("@gherkai/worker-midscene")` 派生、禁止用 cwd/argv 推算——否则 ESM 缓存按 URL 分裂出第二个模块实例，使用方的 `@deterministic` 注册进一张 worker 永远不读的表，全部 step **静默**落回 AI catch-all；③**fail-loud 兜底**：加载完某 step 文件后若它一条都没注册进 worker 侧注册表，立即报错退出（把「双实例」从静默降级变成显式失败）。hook 让 step 文件的写法与当前脚手架完全一致、与安装形态无关；若实测不稳则退到依赖注入形态（step 文件导出 `register(deterministic)`），记入重议闸门。**tsx 转译的另一处副作用（demo 项目真跑实测）**：esbuild 的 keepNames 把使用方 `.mts` 里的函数包成 `__name(fn, "fn")`，这样的函数经 `page.evaluate` / `waitForFunction` 进页面就抛 `ReferenceError: __name is not defined`；使用方本地单测（node 直接执行、无 tsx）照样绿，云端一运行全部记 error，属「绿≠对」的典型。机制 = worker 拿到 page 后在 context 级 `addInitScript` 并对当前文档 `evaluate` 一段字符串，给 `globalThis.__name` 预置恒等实现（传字符串而非函数，worker 自身同经 tsx 转译）；不改使用方写法、不要求传字符串。
- **加载失败 fail-loud**：steps 目录内任一文件 import 失败（语法/导入错误）→ worker **立即以启动错误退出**（带文件名与异常），能力自述与 match 查询两个入口同样；**目录已指定但不存在 / 不是目录同样 fail-loud**（两引擎一致——明确指了一个地方而那里没东西=配置错、不是「没定制」；对齐下「实测项」3 的「语法错/零注册/目录不存在三者 rc≠0 且点名文件」）；**绝不静默跳过**——跳过等于把该文件里的确定性 step 静默换成 AI catch-all、run 可能「通过」，是本项目最忌的静默降级。**提交侧同样前置**：`run`/`submit` 在起任何 job 前、`plan` 在标注前，对本 run 用到的每个引擎以自述入口**恒探一次**（同一份自述兼给 steps 加载结果、清单与 grace 下限，见 [0036](./0036-deterministic-capability-discovery.md)「5.」；无 steps 目录时该次探针退化成「worker 起得来、能自述」）——worker 因 steps 加载失败而非零退出 → 三个命令一律**退 2**、转述 worker 的诊断；这与「worker 运行时 miss」的分叉不同（miss 在 `plan` 降级），因为 steps 加载失败是使用方代码错误，`plan` 若降级成「无标注」、`submit` 若「提交成功」后逐 job error，都是静默降级。
- **worker 的两个非 job 入口**（能力自述 `--capabilities`、match 查询 `--match-steps`，见 [0036](./0036-deterministic-capability-discovery.md)「5.」/「4.」）同样加载 steps 目录，故 `list-deterministic`（取自述对象的 `deterministic_steps`）与 `plan` 标注反映使用方定制——[0036](./0036-deterministic-capability-discovery.md)「真值单一：清单从注册表代码生成」仍成立，注册表 = 内建脚手架 + 加载的使用方模块。
- **内建脚手架 step**留在 worker 包内作为内建；使用方 step 与内建撞 pattern 按 [0036](./0036-deterministic-capability-discovery.md) 既定 conflict 语义处理（`plan` 预检暴露；排序遍历保证 conflict 清单可复现），**不引入「使用方覆盖内建」的优先级规则**。
- **云端后端：steps 烙进定制镜像**（模板见 [0038](./0038-worker-image-delivery.md)），`--backend cloud` 下 definition 里的 `steps_dir` 对云端 worker 无意义 → 提交侧该字段写 null、给了 `--steps-dir` 则 preflight 警告不拦。镜像里的 steps 是否最新由使用方管理、preflight 不比对，规则与理由在 [0038](./0038-worker-image-delivery.md)「不变量」与「被拒方案」。基础镜像**零使用方内容**，正好支撑决策 5 的两层分工。

## 决策 5：worker 镜像两层分工——发布方 GHCR 基础镜像 + 使用方定制层（机制见 0038）

worker 内容 = 工具自身的脚手架 + 使用方确定性 step，属业界分类里的 **user-code image**，最后一层由使用方构建（Dagster user-code deployment / Prefect flow image 同理）；「发布方独占发布完整镜像、用户绝不自建」曾是备选，因抹掉定制面被拒。本 ADR 只定分工与基础镜像通道：

- **基础镜像**（发布方的 CI 发布）：`ghcr.io/zhiyanliu/gherkai-worker-novaact:X.Y.Z` / `…-midscene:X.Y.Z`，内容 = 同版本 worker 包 + SDK 运行时 + 协议层，**零使用方内容**；**linux/amd64 单架构**（ARM64 被拒，理由与将来的路在 [0038](./0038-worker-image-delivery.md)）；tag = immutable `X.Y.Z` + 移动 `latest`（只跟随最新 tag；文档一律 `FROM …:X.Y.Z`）。Dockerfile 两态（与 Lambda asset 同源，`--build-arg WORKER_SOURCE=` 选）：index 态按版本从 PyPI / npm 装已发行包，推往 GHCR 的那次构建用此态；local 态经 `--build-arg` 指向本地 `uv build` wheel / `npm pack` tarball（dev 版不在 PyPI，contributor 才造得出基础镜像），CI 与发布链的镜像 gate 也用此态。 **推往 GHCR 的基础镜像构建必须排在 worker 包发行之后**（index 态装的是已发行的 worker 包）；local 态的镜像 gate 在发布链上排在不可逆发布之前、在日常 CI 上每次运行，见决策 8「发布前镜像 gate」条。
  - **两个镜像标注**（镜像里 worker 的 worker 协议版本与能力，能力标注带着 worker 所属的引擎；键名、取值、放哪些键、必有键与读法见 [0038](./0038-worker-image-delivery.md)「概念模型」节下「镜像标注」段）：构建基础镜像时以构建参数接收两者（协议版本取自 core 的常量，决策 7），写成镜像标注。final stage 的冒烟执行 worker 的能力自述，核对两个标注与自述里的同名内容一致（协议版本标注对自述的 `schema_version`，能力标注的每个键对自述里的同名键，含 `engine`），不等或没给参数即构建失败；发布链推往 GHCR 的构建与发布前、日常 CI 的镜像 gate 都经这份 Dockerfile（决策 8），所以发出去的基础镜像的标注与 worker 自述一致。定制镜像经 FROM 继承两个标注。
- **为什么 GHCR 而非 ECR Public / Docker Hub**：运行时拉的是使用方私有 ECR 里的镜像，GHCR 只在使用方 `docker build` 与 deploy 同步基础镜像时各被拉一次，ECR Public 的免流量/免认证优势碰不到；Docker Hub 匿名限额是负项；GHCR 与 repo 同屋檐、`GITHUB_TOKEN` 推送零配置。（与 [0009](./0009-maximize-aws-hard-constraint.md)「最大化 AWS」的关系：GHCR 是发布通道、属其适用面之外，见 0009「适用面」句；不是例外。）
- **定制镜像由使用方在本地 build，gherkai 不拥有构建**：Dockerfile 模板（唯一真源）见 [0038](./0038-worker-image-delivery.md)「概念模型」节；必须 `--platform linux/amd64`，push-worker 推送前校验。**推送、注册、选择、清理、权限**全部在 [0038](./0038-worker-image-delivery.md)：variant 命名、默认指针、按（引擎，variant）注册 digest 引用的 task-def revision、`gherkai deploy push-worker` / `list-workers` / `delete-worker`、容器引擎口子、preflight 的 variant 解析。
- `tools/build_push_workers.py` 已随 0038 落地退役（`gherkai deploy push-worker` 取代）。

## 决策 6：部署 = `gherkai deploy`——命令 provider 中立，分发单元带 provider

「clone repo + `cdk deploy`」**不再是正式部署形态**（只是 contributor 的开发方式）：相对路径拼 asset、vpc context 坑外露、wheel 用户不可达。直接做 Chalice 模式：

- **IaC 进 wheel**：`gherkai-deploy-aws` 收编 `iac_aws_backend/`（stack / names 薄壳 / app）与 `lambdas/`（两个 handler 源，作 asset 原料——它们是 AWS Lambda 专属胶水、是 runtime 的「Lambda 入口皮」，住在 provider 包里比住在 runtime 里诚实）。`aws-cdk-lib` 只在这个包上，`[deploy-aws]` extra 隔离；`gherkai_cli` 经 entry point group `gherkai.deploy` **发现**已安装的 provider 包：零个 → 提示装 `gherkai[deploy-aws]`；一个 → 无需 `--provider`；多个 → 必给。**provider 契约**（entry point 指向的 `Provider` 类）= `name` / `add_arguments(parser)` / `deploy`·`destroy`·`diff`·`synth_only`·`bootstrap`（各收已解析的 argparse Namespace、返回进程退出码；`2` = 前置/校验失败，其余透传 cdk 的返回码（后续加法扩展：provider 自报 `1` 表示已改动或可能已改动账户的执行失败，排除原因之后重新运行即可收敛（原因是暂时的时直接重新运行），其一是 cdk 成功后 worker 镜像步骤失败，见 [0038](./0038-worker-image-delivery.md)「四步的失败语义」；其二是 deploy 在 cdk 之前找回或建立 Device Farm 项目遇到权限以外的错误，见 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 10））；另有**可选** `doctor(args) -> list[dict]`（每项 `{name, ok, detail}` + 可选 `required`（缺省 False）与可选 `skipped`（缺省 False，这一项没有执行检查时给 True）；收 `gherkai doctor` 的 Namespace、只读、**不返退出码**——退出码由入口按 required 项汇总，provider 缺席该方法则入口给一行「provider 未提供自检」并标未查，[0041](./0041-agent-facing-cli-affordances.md) 决策四）。CLI 皮**不 import `aws_cdk`/boto3**（`--help` 不付一次 node 启动，有测试守：真 provider 已装时 `aws_cdk`/`jsii`/`boto3` 都不入 `sys.modules`），只做发现、贴 flag、分派；worker 镜像族子动词由 provider 自加 subparser 并 `set_defaults(_deploy_verb=…)`，皮先看 `_deploy_verb`——0038 落地时皮一行不改；**子动词与 `--diff`/`--synth-only`/`--bootstrap` 同给 → 皮退 2**（子动词真写账户，不得静默盖过用户点名要的只读预览——那三个 flag 存在的意义就是「先看清再改账户」）。
- **命令面**：`gherkai deploy`（`--diff` 呈变更集，另把数据版本检查的读取与计数作为信息输出、不拦（决策 7「`deploy` 入口的检查」）、`--synth-only DIR` 导出模板作 escape valve：给部署方的 reviewer 留一个靶点，部署方审阅变更集之前，工具不改其生产账号；DIR 相对用户 cwd、命令钉成绝对路径再交 cdk——cdk 子进程的 cwd 是随后删除的临时工作目录，相对路径原样传会「退 0 且无产物」（真跑踩过）、`--bootstrap` = `cdk bootstrap aws://<account>/<region>`——**账户级动作、不合成 app、不需要 `--vpc`**（显式环境 + 不带 `--app` 时 cdk 不加载 app，真跑核过；带 `--app` 则即使给了显式环境也照样跑 app）；deploy 失败时中性提示「常见首次原因之一是未 bootstrap」、不改写 cdk 诊断）、`gherkai destroy`（`RETAIN` 语义见 [0033](./0033-iac-aws-backend-and-composition-wiring.md)）、worker 镜像族 `gherkai deploy push-worker` / `list-workers` / `delete-worker`（[0038](./0038-worker-image-delivery.md)）。
- **把裸 cdk 的坑封死在命令里，flag 面对齐 stack 与 app 的全部 context 旋钮**（**用户可拧的**恰四个：`prefix` / `vpc_id` / `use_default_vpc` / `stop_timeout`，映射为**三个 flag**；stack 另读两个由命令派生、**有意不给 flag** 的 context：`version` 按 CLI 自身发行版本派生，取不到时为 `unknown`——让用户敲版本戳等于给「戳写错」开口子，见下「版本戳」条；`device_farm_project` 是 Device Farm 项目 ARN——`deploy` 在调 cdk 之前找回或建立该项目，ARN 作为 context 交给 stack 写 SSM 参数；`diff` / `--synth-only` / `destroy` 不建立项目、只取 SSM 现值或「待建立」占位，读取 SSM 记录失败或记录不是合法的项目 ARN 都以退出码 2 结束（唯一例外是 `--synth-only` 在完全没有凭证时回落占位并警告，保住无凭证导出；`diff` 对 SSM 现值的项目核对与各分支退出码见 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 10）；app 对缺少或占位的 `device_farm_project` 不 fail-fast（这一点与 `version` 不同）——跳过 SSM 参数与 task role 的 Device Farm 授权；不给 flag 的理由与 `version` 相同：值由命令派生，手填只会多出写错的机会）：`--prefix`（默认 `gherkai-`）、**`--vpc default|new|<vpc-id>` 必给、无隐式默认**（校验在**运行期**而非 argparse：deploy / diff / synth / destroy 未给它退 2，`--bootstrap` 不要它；一个 flag 吞掉 `vpc_id` + `use_default_vpc` 两个旋钮、三种取值与 [0033](./0033-iac-aws-backend-and-composition-wiring.md)「VPC 来源：三种取值」一一对应，`vpc-` 前缀值即复用现有 VPC；漏 context 合成「新建整套 VPC + 替换 WorkerSg」危险变更集是真踩过的坑，隐式默认 = 让用户重踩）、`--stop-timeout N`（grace 标定用）。provider 另声明 `--region` / `--profile`（AWS 概念、不归皮；prefix/region/profile 在选项、环境变量、默认值三层走与 run/submit **同一条**解析链 `compose.resolve_cloud_target`，这三层上部署侧与提交侧的解析结果相同。后续加法扩展：`gherkai.toml` 里的 `[cloud]` 节 `prefix` 与 `[common]` 节 `region` / `profile` 只在运行侧生效，部署命令不读该文件（[0053](./0053-project-config-file.md) 决策 1），所以项目在配置文件里指定了 prefix 时，部署方要用 `--prefix` 或 `AWS_RESOURCE_PREFIX` 给出同一值；两侧不一致、且配置文件那个 prefix 下没有已部署的后端时，`submit` 的 preflight 以退出码 2 结束）；`--require-approval` / `--allow-vpc-change` / `--allow-data-version-change`（与 `--allow-vpc-change` 同一形态，用途见决策 7「`deploy` 入口的检查」）两层声明——皮给中立版（provider 缺席时帮助不残缺）、provider 再声明带 AWS 语义版（`choices` / 三态措辞），argparse `conflict_handler="resolve"` 令 provider 版生效。**两层都只贴 `deploy`**——`destroy` 不消费它们（不做 VPC 取值三态比对与数据版本检查、`cdk destroy` 不支持审批级别），provider 按 parser 的 `prog` 末段判、`prog` 认不出时仍贴（无 prog 的 parser 要拿得到全集，降级偏向不残缺）；被接受的代价 = `gherkai destroy --allow-vpc-change` / `--require-approval` 从静默忽略变 argparse 拒绝退 2。命令拼 context、在临时工作目录生成 `cdk.json`（app = `sys.executable -m gherkai_deploy_aws.app`；特性开关逐字沿用包化前 `cdk.json` 那一组——换一组即给已部署 stack 造无意义变更集，A/B 实测 IAM statement 32 vs 44 条），调 cdk CLI 执行（cwd = 该工作目录）。**CDK 环境查询缓存持久化**：`from_lookup`（`--vpc default|<id>`）写的 `cdk.context.json` 按 prefix 存在用户缓存目录（`$XDG_CACHE_HOME`/`~/.cache` 下 `gherkai/cdk-context/`），进一次性工作目录前放入、跑完存回，`--refresh-context` 丢弃重查——理由：一次性目录若每次空着进去，cdk 对缺失查询值会先用占位 VPC/子网**预合成一遍**再真查，aws-cdk-lib（≥2.26x 内建模板校验器）对那份占位模板报错、降级成 `[Warning] Template validation found issues` 打给用户（真部署抓到、全新目录 100% 复现、有缓存即消失），且每次多一轮查询 API；持久化 `cdk.context.json` 正是 CDK 自己的标准做法（它建议入库，我们的 wheel 用户没有可写源码树，故放用户缓存目录）。首次查询某 prefix 仍会看到那条 warning 一次。
- **VPC 取值持久化比对，三态齐全**（只强制显式给值挡不住第二次 deploy 敲错取值）：stack 把生效的 vpc 取值写成 SSM 参数 `ssm_path(prefix, VPC_KEY)`（stack 资源、与部署事务同生死；`new` 取值存 `new:<所建 vpc-id>` 使其也可回溯核对）。`gherkai deploy` 在调 cdk 前读它：①stack 不存在（真首次部署）→ 放行；②**参数缺失且 stack 已存在**（本 ADR 之前部署的环境——施工前所有已部署的 stack 都没有此参数，而这恰是最危险的那一次 deploy）→ 退 2，要求先 `--diff` 核对变更集、再带 `--allow-vpc-change` 放行一次；③参数存在 → 与 `--vpc` 一致放行，不一致退 2（`--allow-vpc-change` 放行）。
- **deploy 的 worker 镜像四步**（登记 task-def 模板——随 cdk 事务；同步基础镜像为 `base` variant、初始化默认指针、按新模板重派生既有 variant——cdk 之后；协议版本要变时同步的两个前提在 cdk 之前核，见决策 7「`deploy` 入口的检查」）**全部由 [0038](./0038-worker-image-delivery.md) 规定**，本 ADR 只登记它们属于 `gherkai deploy` 的职责、且全部幂等；cdk 之后的三步开头的数据版本比对见决策 7「`deploy` 入口的检查」末条。
- **Node 前置是硬事实**：Python CDK 的 `aws-cdk-lib` 是 jsii 绑定，import 即起 node 子进程；cdk CLI 本身也是 npm 物。`gherkai deploy` 要求 Node ≥22 在 PATH（与 worker 的 `engines.node` 同一下限，README 一处说清）；cdk CLI 用 PATH 上的 `cdk`，缺则 `npx -y aws-cdk@2`。**cdk 可定位性与 Node 同一级前置**：`deploy` / `bootstrap` / 内部 cdk 调用共用一个工具链闸、**排在任何 AWS 读之前**（工具链缺失不花网络、不要凭证）；由此「deploy 失败时中性提示『首次部署最常见的一种是环境未 bootstrap』」只出现在 cdk 真跑过的失败上——曾因 deploy 只查 Node 不查 cdk，缺 cdk 会在读过后端、比对过 VPC 取值之后退 2 并附上这条无效建议。对本受众（已在装 uv/Docker/AWS 凭证）可接受。**去 Node 路线**（CI 预合成模板 + boto3 驱动 CloudFormation）defer 非拒：vpc 三种取值 × prefix 的参数化要变 CloudFormation Parameters 组合管理，且 jsii 本身也要 Node、只省 cdk CLI 一层。**这一期 deploy 机器还需要容器引擎**（同步基础镜像要 pull / push，0038）。
- **Lambda asset 来源**：handler 源（deploy-aws 包内）+ **从当前 venv 已安装的** `gherkai_runtime` / `gherkai_core` / `gherkin` / `packaging` / `typing_extensions` 五个 import 包复制（版本 = 运行中的 CLI，离线可行，dev 版也可；包化前那次联网 `pip install gherkin-official` 随之消失）；boto3 由 Lambda runtime 自带。**传递依赖必须自己进清单**：`gherkin` 无条件 `from typing_extensions import …`，按名复制时它不会被捎带——摆放规则类单测全绿、真 asset 一 import 即 `ModuleNotFoundError`；故清单由一条「剥掉 site-packages 的子进程真 import 整个 asset」的测试守着（单文件模块 `typing_extensions.py` 与包目录两种形态都认）。asset 落一次性临时目录、经 env `GHERKAI_LAMBDA_ASSET_DIR`（`names.LAMBDA_ASSET_DIR_ENV`）传给 app（不走 context，保住「context 全集由三个 flag 派生的四个旋钮，加上命令自派生的 `version` 与 `device_farm_project` 构成」这条闭集，不让 asset 路径变成又一个隐式 context 旋钮），wheel 装的包目录不被写。**不从 PyPI 拉同版本**（dev 版不在 PyPI 上，contributor 部署 dev 版会断）。
- **版本戳**：stack 把发行版本写成 SSM 参数 `ssm_path(prefix, BACKEND_VERSION_KEY)`。值经 context `-c version=<PEP 440 版本或 unknown>` 由命令传入：命令传 **CLI 自己的**发行版本（皮经 `args.version` 交给 provider、不让 provider 自报），取不到时（例如直接从源码执行）传 `unknown`、stack 照写，各处显示为「未知」；不拿别的包的版本代替（editable 树里各包版本各自漂，代替的值是错的事实）；`deploy`、`--diff`、`--synth-only`、`destroy` 都不因取不到而拒绝，取不到时按非纯发行版本跳过基础镜像同步（决策 7「发行版本作为取哪一份的缺省」）。app 缺这个 context 即 fail-fast：命令总会传入一个值，缺它只会是绕过命令直接执行 app。**stack 资源而非命令事后 `put_parameter`**，使其与部署事务同生死、回滚不留错值；`gherkai destroy` 随 stack 删除、不 `RETAIN`。它只作事实：`doctor` 与 `list-workers` 的表头显示它，比不上时的说明与 `deploy` 的数据版本表引用它，用户文档以它作定制镜像模板 FROM 行的缺省（决策 7）。它声明依赖除数据版本参数之外的全部资源，紧挨在数据版本参数之前更新，使说明里一起读出的发行版本与数据版本出自同一次部署，只差两次资源更新之间那一段。落在已授的 `/{prefix}backend/*` 通配内，CLI 侧不新增 SSM 授权。
- **数据版本参数**：`ssm_path(prefix, DATA_VERSIONS_KEY)`，即 `/{prefix}backend/data-versions`，是 stack 资源（`StringParameter`）。值是 JSON 对象，键恰为 `run_record_format`、`worker_protocol`、`backend_interface`，值都是正整数，在合成时取自已安装的三个常量（决策 7「常量与持久化的键」）；参数的名字与这层最外层结构属跨版本不变的约定（决策 7「跨版本不变的约定」约定一）；Lambda asset 复制的是同一组已安装的包（上「Lambda asset 来源」条），所以参数的值与后端代码认的值出自同一处。不经 context、不设旗标。随部署事务写入、部署失败时随回滚改回、`destroy` 时随之删除，理由同上条。它声明依赖栈里其余全部资源（含版本戳参数、两条事件源映射、EventBridge 规则、任务定义模板与 `worker-template` 参数），在整次更新的末尾才变：读到新值时，栈里别的资源的更新都已发起、并已被 CloudFormation 报为完成。这不保证它们都已可用：表的索引在栈报完成时可能仍在建立（实测部署报完成时新索引仍为 `CREATING`，约十分钟后才转为 `ACTIVE`，[0030](./0030-realtime-persistence-seam.md) 决定六「改用状态分组索引的那次索引迁移的实测」），读索引的命令另按各自的就绪判据核对（[0041](./0041-agent-facing-cli-affordances.md) 决策七「索引就绪判据」）。代价是窗口有整次更新那么长（决策 7「部署进行中」）。依据：CloudFormation 按声明的依赖先后更新资源、前一个完成之后后一个才开始；这一点只在只含参数资源的临时栈上实测过，完整栈上待部署之后核（实测项 7）。后端代码不读这个参数，它认的值就是代码里的常量（被拒方案「后端各 Lambda 读这个参数作为自己的版本」）。读法与各情形的判读在决策 7「后端的三个值怎样读」；它同样落在 `/{prefix}backend/*` 通配内。
- **权限**：与包化前一致，用本机凭证；IAM 变更审批走 cdk 的 `--require-approval` 透传；worker 镜像相关的权限增量见 [0038](./0038-worker-image-delivery.md)。

## 决策 7：发行版本只作事实，能不能一起工作看数据版本

**版本真源**：一个 git tag 派生 wheel 版本（五个 Python 包同号）、npm 包版本（CI 写入 `package.json`）、基础镜像 tag、SSM 版本戳与 GitHub Release（CONTEXT「版本真源」）。命令行工具自己的发行版本按 `importlib.metadata.version("gherkai")` 取，由调用点传入、不缺省成 runtime 包的版本（editable 树里各包版本各自漂）；源码直接执行时取不到，值为空，显示为「未知」（[0043](./0043-agent-skill-for-driving-gherkai.md) 决策三的 skill 版本标记用同一取法）。

能不能一起工作由三个**数据版本**判断，各管一条边界：**run 记录格式版本**（一个 run 的全部记录）、**worker 协议版本**（worker 与它的执行方之间交换的内容）、**云端后端接口版本**（命令行工具与部署命令所依赖的已部署后端约定）。发行版本不参与任何兼容判断。

### 总则

1. **兼容判据**：同一个数据版本，两方的值相等才一起工作；只比是否相等，不比大小、不分方向。
   - 值是正整数，只增，不复用。run 记录格式版本的 0 表示没有这个号的记录（1.5 之前写出）；worker 协议版本不取 1（1.4 的能力自述把 1 用作它自己的格式号，含义不同）。
   - 提交记录里没有这个号读作 0；有而不是整数，按形态违约处理。后端的数据版本参数不存在或读不懂，后端一侧算作无值；无值与任何值都不相等。
   - 新版本不保留读旧值的分支。这条只管三个号管辖的内容；已部署后端的资源怎样换形态，按下「后端形态变更的迁移口径」。
2. **发行版本只作事实**：出现在比不上时的说明、`doctor`、`list-runs` 的版本列、`list-workers` 的表头与 `deploy` 的数据版本表里；另在几处作「要取一份东西时取哪一份」的缺省（下「发行版本作为取哪一份的缺省」）。它不参与任何判断，不要求使用者对齐它，也不因它拒绝任何操作：取不到时，要显示它的地方写「未知」，要按它取一份东西的地方按非纯发行版本处理。
3. **各号由谁把关**（写的是做法，不是保证）：
   - run 记录格式版本：凡读一个 run 的地方都按这个 run 记下的值判，即命令行工具的查看与处置、后端各入口的闸。云端 `submit` 拿本机的值与后端的比，是把后端的判断提前到写记录之前；部署进行中这个判断可能过时，那样写下的 run 由后端的闸按下「后端遇到别的格式写出的 run」处理。
   - worker 协议版本：本机执行之前，CLI 与本机 worker 比；云端提交之前，CLI 与后端比、所选镜像与后端比；推送镜像时，CLI 与后端比、镜像与 CLI 比（下「各入口比什么」）；后端的闸比 run 记下的值；worker 建会话之前核 job 行的值，是最后一道（[0024](./0024-worker-core-protocol.md)）；`explain` 补取事件之前，比 run 记下的值与 CLI 的。
   - 云端后端接口版本：命令行工具与部署命令在每条云端命令的开头比；它不记进 run 的记录，后端不按它判断，部署进行中比对过时、只有接口版本与后端不同的 run，后端照常推进（下「部署进行中」首条；被拒方案「run 的记录里另记写下它的命令行工具的云端后端接口版本，后端的闸三个值都比」条）。
4. **比不上时只陈述事实**：
   - 命令因数据版本比不上而结束时（云端命令开头、云端 `submit`、`push-worker` 与 `deploy` 的基础镜像同步比镜像的协议版本、按 run 的查看与等待、本机执行之前与 worker 的比对、`deploy` 在 cdk 之后的三步开头），说明写清哪一个号、两边各是什么值、取得到的两边的发行版本，末尾加一句固定的话「数据版本相同的两方才能一起使用。」（下称固定话）。
   - 写在逐项字段里的说明（`settle-runs` 的原因、job 的说明、后端写进运行态的原因、`explain` 的 `aborted_hint`）与命令照常往下的信息（`deploy` 的数据版本表）只写哪个号与两边的值，取得到写出版本的带上写出版本，不加固定话：固定话说的是命令为什么停下。
   - 不按情形说该升哪一边，不拼命令。怎样解决写在用户文档 `cloud-backend.md`「版本与升级」一节，终端里不说。

### 三个号各管什么

**归属看两头是谁**（下面各号的逐项内容是举例，不求列全；没有列出的东西，按它在哪两方之间归到相应的号）：
- **run 记录格式版本**：两头都是同一个 run 的读写方（任何版本的命令行工具、本机推进进程、云端推进器与退出观察者），内容是这个 run 自己的记录，范围是它在本机 run 目录里、在云端这个 run 的位置之内的形态：
  - 提交记录：本机 `run_meta.json`；云端的头、`meta_json` 与 jobs 对象（[0030](./0030-realtime-persistence-seam.md) 决定六「云端提交记录」条）；
  - 运行态，公共部分除外（下「跨版本不变的约定」约定三）；
  - 判定明细的内容，以及它在 run 位置之内的键；
  - 本机事件库的表结构与退出记录行；云端 events 表里的退出记录，含怎样认出它（[0034](./0034-detached-batch-reconciler.md) 机制一）；
  - 本机 run 目录的布局，运行态短锁的文件与协议，生命期锁在 run 目录改名之后的部分（暂存阶段的互斥属约定五：不变的是建 run 的一方从取到锁到改名完成持有的那把锁、清理方删之前取同一把锁并核对名字；改名之后别的一方怎样试拿、是否另加锁，随记录格式版本定）；
  - 运行定义记下的 worker 协议版本（`worker_protocol_version`，下「各入口比什么」）。

  号只记在提交记录里。
- **worker 协议版本**：一头是 worker（本机 worker 进程，或云端镜像里的 worker）：
  - job 行，云端 `jobs-in/` 对象；
  - 起 worker 时注入的环境变量的名字与含义：`RUN_ID`、`SCOPE_ID`、`JOB_S3_URI`、`EVENTS_DDB_TABLE`、`ARTIFACT_S3_BUCKET`、`ARTIFACT_S3_PREFIX`、`NOVA_LOGS_DIR`、`MIDSCENE_RUN_DIR`、`GHERKAI_STEPS_DIR`、`GHERKAI_NO_ARTIFACTS`、`GHERKAI_EXTRA_HTTP_HEADERS`、`GHERKAI_SESSION_WARMUP_URL`、`NOVA_ACT_TIMEOUT_S`、`AWS_REGION`、本机的 `EVENTS_FD`；镜像的启动约定（推进器不覆盖启动命令，只覆写环境变量）；
  - worker 事件的类型、键与封闭取值；云端 worker 直写的 events 条目（`pk` 里第一个 `#` 之后的部分、`seq`、`body`、`expires_at`）；
  - 能力自述与匹配查询的输入输出，能力标注 `gherkai.worker-capabilities` 的键（[0038](./0038-worker-image-delivery.md)「镜像标注」段）；引擎产物在 run 树下的子目录名；
  - 后端给 worker 的运行权限（task role 的权限集合）；worker 退出码的取值与含义。

  证据文件（`evidence.json`）自带格式号，由 `explain` 逐个文件核对（[0042](./0042-step-evidence-and-explain.md) 决策六），不归它。
- **云端后端接口版本**：一头是命令行工具或部署命令，另一头是已部署后端里不属于某一个 run 的东西：
  - 由前缀推出的资源名：runs 表、events 表、产物桶、三个 Lambda、两个任务定义族与同名的 ECR 仓库、容器名 `{engine}-worker`、引擎名集合；
  - runs 表状态分组索引的名字、键与投影；`worker_task_def_arns` 的含义（它是运行态的属性，又被索引投影、被部署命令的清理跨格式读取，改含义时与 run 记录格式版本一起加）；
  - events 表的键结构，以及 `explain` 按 `pk` 查询的方式；
  - 桶级的前缀与规则：`definitions/`；`apps/<sha256>/<原文件名>`、对象 tag `gherkai=app` 与按它过期的规则；Lambda 没有配置时报告前缀取 `reports`；一个 run 在报告前缀下的根；
  - 参数存储里数据版本参数之外的参数名与值的结构：`version`、`worker-default`、`worker-variant/<引擎>/<变体>`、`worker-template/<引擎>`、`device-farm-project`（不存在表示没有启用设备支持）；
  - 命令行工具经 `GetFunction` 读的两个推进 Lambda 的 `REPORT_DIR`、`MAX_CONCURRENCY`，以及它们缺席时的取值；
  - 部署命令依赖的任务定义模板形态、修订上血缘 tag 的含义、1 小时静默期；Device Farm 的区域常量与项目 ARN 的形态。
- **两头都占时按层分**：容器（表名、索引、前缀、参数名）归接口版本，worker 写的内容归协议版本，其余归记录格式版本。一次改动跨两层，两个号都加；判不清的按两个都加，并在登记里写明理由。
- **不归任何号**：
  - 读写两方都是后端、由同一次部署写出的约定：推进 Lambda 的其余环境变量、两条流映射的批大小与重试、EventBridge 规则。部署进行中新旧代码与新旧配置会交错（例如流映射引用 Lambda、按依赖在 Lambda 之后更新，推演，部署之后核，实测项 7），这类改动要在交错时都能工作。后端触发条件、索引与生命周期规则所依赖的属性与取值不在此列，各按它所在的记录归号：run 的记录里由 run 的写方写下的归记录格式版本（下「加号的纪律」第 3 问）；worker 直写的 events 条目里的归 worker 协议版本（`expires_at`，上）；安装包对象的 tag 归云端后端接口版本（`gherkai=app`，上）；属跨版本不变的约定的不改（`status_group`，下约定三）。后端跨部署的约定（定时触发的分组与名字，以及 kicker 作为还没到点的定时触发的目标）由新部署按迁移口径承接；kicker 的名字另归云端后端接口版本（上，命令行工具按名字读它），改名时两件事都要做。
  - 部署配置的取值：并发上限；报告前缀的取值（使用方以 `--report-dir` 给出，后端一侧没有部署入参、取缺省，[0033](./0033-iac-aws-backend-and-composition-wiring.md)「资源清单」12.）。
  - 对使用者发布的形状：报告页、manifest、各命令的 `--json`，按 [0041](./0041-agent-facing-cli-affordances.md) 决策五的加法兼容管。
  - 只有 `deploy`、`deploy --diff`、`destroy` 读的部署标记：stack 名、`vpc` 参数、Device Farm 项目名，由写出新形态的那一版 `deploy` 按迁移口径承接。理由：接口版本的作用是让持别的值的命令一开头就不执行，这些标记若归它，改它们就会挡住从来不读它们的 `submit` 与 `status`。
  - 跨版本不变的约定（下）。

**写读次序**：一个 run 的记录只由与它的 run 记录格式版本相同的写方写：建 run 的一方、过了闸的后端、值相同的处置方。读的一方先核提交记录里的值，再读其余记录。例外有两处：
- 后端以 error 变体结束别的格式写出的未结束 run，这一写只改公共部分（下「后端遇到别的格式写出的 run」）；之后的读者按约定读出公共部分，其余细节按自己的格式读，可能读不出。
- 退出观察者不读 runs 表、无从比对格式，按后端自己的格式写退出记录；数据版本不同时不保证对方读得出。

**本机专属的格式改动**：本机专属的非加法改动（本机事件库改列名、run 目录改名之后的生命期锁换协议等）同样给 run 记录格式版本加号；暂存阶段的互斥任何格式都不改（下「跨版本不变的约定」约定五）。后果落在云端：新命令行工具在后端重新部署之前不能做云端提交；`deploy` 读到未结束的 run 或数不出时默认不继续；升级之前的云端 run，新版本看不了细节。接受这种耦合：这类改动少见；把本机布局移出这个号等于永远不许非加法改动，另立第四个号与「三个号各管一条边界」相抵。

**常量与持久化的键**：
- run 记录格式版本：`RUN_RECORD_FORMAT_VERSION`（core 的 `serialize`，由 `DEFINITION_SCHEMA_VERSION` 改名）。
- worker 协议版本：`WORKER_PROTOCOL_VERSION`（core 的 `wire`，由 `PROTOCOL_SCHEMA_VERSION` 改名）；两个 worker 各有一个同值常量，测试把三者钉成相等。
- 云端后端接口版本：`BACKEND_INTERFACE_VERSION`（runtime 的命名真源 `names`）。
- ADR 不写具体数值。持久化的键名不改：提交记录里的 `schema_version`、自述里的 `schema_version`、job 行的 `schemaVersion`。
- 1.5 发行之前，开发期里对同一形态的修正不加号；每个值第一次随发行出现时的形态就是它的基线（下「加号的纪律」）。

**提交记录里另记的两项**：写出版本 `cli_version`（写出它的命令行工具的发行版本，**只记不比**，未装成包取不到时为 null；用途是让说明与 `list-runs` 的版本列能点名由哪个版本写出）与期限 `deadline_at`。云端提交记录的头（存放形态见 [0030](./0030-realtime-persistence-seam.md) 决定六「云端提交记录」条）把 `schema_version`、`cli_version`、`deadline_at` 再摊成顶层属性，值与 `meta_json` 里的同名键恒同；按 run 的比对用投影只读头的这几项、不取 jobs 对象（`explain` 比过之后另读整份定义，[0042](./0042-step-evidence-and-explain.md) 决策四「数据来源」段）。

### 后端的三个值怎样读

参数本身（名字、值的形态、由 stack 写、更新次序）在决策 6「数据版本参数」条。

- 命令行工具与部署命令都用 `ssm:GetParameter` 读这一个名字；云端命令一条命令只读一次，`submit` 用到的三个值都出自这一次；`deploy` 在 stack 已在时读两次、各用各的读数：入口检查一次（`deploy --diff` 只做这一次），cdk 之后的三步开头再读一次（下「`deploy` 入口的检查」里「cdk 之后的三步」一项）。
- 读到合法内容：得到三个值。读的一方要求键集恰为 `run_record_format`、`worker_protocol`、`backend_interface` 三个，多一个或少一个都按读不懂：以后给它加一个维度时，持旧版本的读方按读不懂结束，而不是忽略新键、照判三项相同。
- `ParameterNotFound`：后端无值（没有记下）。
- 读到了，但不是 JSON 对象、键集不恰为三个、或某个值不是正整数：后端无值（读不懂），说明带原值的前 200 个字节。
- 其余错误（凭证、权限、网络）：读取失败，以退出码 2 结束，说明点名这个参数；既不当作比不上，也不当作比得上。`deploy` 在 cdk 之后的那一次读取失败以退出码 1 结束（账户已改动，与后三步别的失败同一退出码）。
- **版本戳另读**：拿后端参数比的各项都比得上时不读；有一项比不上时另读一次放进说明。要显示后端发行版本的地方（`doctor`、`list-workers` 的表头、`deploy` 有不同时的数据版本表）同样另读一次。读到 `ParameterNotFound` 写「后端没有记下发行版本」，其余错误写「后端记下的发行版本读不出」，读到了写「后端记下的发行版本：X」，不写成「后端由 gherkai X 部署」（理由见下「说明的要点」表「读不到数据版本」一行）；结论与退出码不随这次读的结果变。
- **权限**：两个参数都在已授予的 `ssm:GetParameter`（`/{prefix}backend/*`）之内，不新增 IAM 动作。

### 各入口比什么

比较只在 runtime 的一处：取本方的三个值、按上节读后端、逐对比较并返回结构化的不合项（哪个号、本方的值、对方的值）、拼说明；说明只描述，判断只看不合项。按 run 判记录格式版本的各处（core 的读端、CLI 的查看与处置、后端的闸）拿读到的值与同一个常量比；这类说明（CLI 显示的、后端写进运行态的）在 core 一处拼出。

**次序**：`settle-runs` 与等待中的 `status --wait` 先装中断处理器，装上之后第一件事是比接口版本；其余云端命令开头第一件事就是比接口版本。两者都先于资源 preflight 与任何别的云端读，前缀或区域给错时在这一步结束、不先报资源不存在。不读 AWS 的入参校验在它之前（例如报告前缀与产物桶的保留前缀重叠，[0033](./0033-iac-aws-backend-and-composition-wiring.md)「资源清单」3.）。云端 `submit` 用同一次读到的值接着比记录格式版本与 CLI 自己的 worker 协议版本（都在资源 preflight 之前），变体解析之后比各用到引擎的镜像的协议版本、再按对应关系记录核对能力；这几项都在生成运行定义、起隧道、上传安装包之前。收发 job 的是后端与镜像，CLI 自己的协议版本也要与后端的相同，是因为能力对象的格式归 worker 协议版本，云端提交时解读所选镜像的能力对象的是 CLI（解读的前提见 [0038](./0038-worker-image-delivery.md)「镜像标注」段的「读出」一段）。`push-worker` 用同一次读到的值接着比 CLI 自己的 worker 协议版本，之后在推送之前比打好 tag 的目标引用上的协议版本标注与 CLI 的（0038「`push-worker` 流程」步 1、2）；三者相同才推送与登记，理由同上：推送时校验能力标注取值的是 CLI（不同时只打印提醒的做法被拒，见 0038 被拒方案「推送时协议版本不同不拦、只打印提醒」条）。

**运行定义记下 `worker_protocol_version`**（必有键）：本机写 CLI 自己的值（`run` 与 `submit` 已拿它与本机 worker 比过）；云端写后端的值，这时它也等于 CLI 自己的值与所选镜像的值（提交时三者已比过）。读它的是后端的闸与 `explain`。

| 入口 | 比的两边 | 比不上时 | 退出码 |
|---|---|---|---|
| 云端每条命令的开头：`submit`、`status`（含 `--wait`）、`explain`、`list-runs`、`settle-runs`、`deploy push-worker`、`deploy list-workers`（以后的 `delete-worker` 同样） | 接口版本：CLI 的常量与后端参数 | 另读一次版本戳放进说明（上「版本戳另读」），不读其余云端资源 | 2 |
| 云端 `submit` 另比三项 | 记录格式版本：CLI 的常量与后端参数；协议版本：CLI 的常量与后端参数；镜像的协议版本：所选变体在每个用到的引擎上的对应关系记录与后端参数 | 写任何记录、起隧道、上传安装包之前结束 | 2 |
| 查看：`status`、`explain`、等待中的 `status --wait`（两个后端） | 记录格式版本：这个 run 的提交记录与 CLI 的常量（不看后端现在的值） | 不显示、不等待 | 2 |
| `settle-runs`（两个后端） | 同上 | 跳过，`reason` 为 `other_version` | 不改变 |
| `list-runs`（两个后端） | 同上，只做标注 | 标出这一行的格式，只读公共部分 | 0 |
| `explain` 补取被中止 job 的事件 | 协议版本：这个 run 记下的值与 CLI 的常量 | 不补取，`aborted_hint` 给陈述事实的一句 | 不改变 |
| 本机 `run`、`submit`、`plan`、`list-deterministic` | 协议版本：CLI 的常量与本机 worker 的自述 | 执行之前结束 | 2 |
| `doctor` | 见下 | — | 有必修项失败为 2 |
| `deploy push-worker` 另比两项 | 协议版本：CLI 的常量与后端参数（开头）；打好 tag 的目标引用上的镜像标注与 CLI 的常量（推送之前） | 在推送与任何 ECS 调用之前结束 | 2（`deploy` 的基础镜像同步比后一项，开头那一项由 `deploy` 自己的检查与 cdk 之后的三步开头的比对承担；比不上时的退出码见 [0038](./0038-worker-image-delivery.md)「`gherkai deploy` 的 worker 镜像四步」第 2 步） |
| `deploy`、`deploy --diff` | 三个号：本次的常量与后端参数 | 见下「`deploy` 入口的检查」 | 同左 |
| `deploy` 在 cdk 之后的三步（[0038](./0038-worker-image-delivery.md) 四步里的后三步）开头 | 三个号：本次的常量与推送路径开头读到的后端参数 | 比不上或读取失败：给出两边的值或读取失败的说明，后三步都不做 | 1 |
| `--synth-only`、`--bootstrap`、`destroy` | 不比 | — | — |

**云端 `submit` 的各种组合**：

| 接口版本 | 记录格式版本 | CLI 的协议版本 | 所选镜像 | 结果 |
|---|---|---|---|---|
| 后端无值 | — | — | — | 退出码 2，给「读不到数据版本」或「读不懂」那一句（另读一次版本戳放进说明，上「版本戳另读」），不读其余云端资源 |
| 不同 | — | — | — | 退出码 2，给接口版本那一句 |
| 相同 | 不同 | — | — | 资源 preflight 之前退出码 2，给记录格式那一句 |
| 相同 | 相同 | 与后端不同 | — | 资源 preflight 之前退出码 2，给 CLI 的协议版本那一句 |
| 相同 | 相同 | 相同 | 某个用到的引擎上没有记录，或记录读不懂 | 变体解析之后退出码 2，给变体缺失的说明，带推送与改用另一个已推送的变体两条出路 |
| 相同 | 相同 | 相同 | 某个用到的引擎的协议版本与后端不同 | 变体解析之后退出码 2，每个引擎一句 |
| 相同 | 相同 | 相同 | 协议版本都相同，而某个用到的引擎的记录里的能力对象不合 CLI 自己的约定（解读之前的校验，[0038](./0038-worker-image-delivery.md)「运行时与 preflight」能力一项） | 退出码 2；不是数据版本不合，说明点名这个变体在这个引擎上的记录，写法见下「说明的要点」 |
| 相同 | 相同 | 相同 | 协议版本都相同，而记录里的能力不满足这个 run：用的是本机执行之前同一个能力判断，核对的各项见 [0038](./0038-worker-image-delivery.md)「运行时与 preflight」能力一项 | 退出码 2；不是数据版本不合，说明的写法见下「说明的要点」表之后「能力不满足」一段 |
| 相同 | 相同 | 相同 | 协议版本都相同，能力满足 | 照常提交，运行定义记下后端的协议版本 |

**说明的要点**（固定话只在一条说明末尾出现一次）：

| 情形 | 要点 |
|---|---|
| 接口版本不同 | 本机 gherkai 1.6.0 与这个云端后端（前缀 gherkai-，区域 us-east-1）的云端后端接口版本不同：本机 2，后端记下的是 1（后端记下的发行版本：1.5.2）。没有读写这个后端的任何 run 记录。（固定话） |
| 读不到数据版本 | 在 /gherkai-backend/data-versions 读不到这个后端记下的数据版本（后端记下的发行版本：1.4.9）。本机 gherkai 1.5.0 的云端后端接口版本是 1。（固定话）版本戳的两种情形分开写（同上「后端的三个值怎样读」里「版本戳另读」一项）：不存在时括号里写「这个前缀与区域下也没有记下发行版本」（数据版本参数也不在时不预设这里部署过后端，所以不用那一项里「后端没有记下发行版本」的写法），读取出错时写「后端记下的发行版本读不出」。只陈述读到的，不替它断定后端由哪个版本部署、是否部署过：版本戳先于数据版本参数更新，两者之间有一段只有版本戳是新值（决策 6「版本戳」） |
| 数据版本读不懂 | /gherkai-backend/data-versions 的内容读不懂：<原值的前 200 个字节>（后端记下的发行版本：1.5.2；本机 gherkai 1.6.0）。（固定话） |
| 提交：记录格式不同 | 本机 gherkai 1.6.0 写出的 run 记录格式版本是 4，这个后端记下的是 3（后端记下的发行版本：1.5.2）。没有写下任何记录。（固定话） |
| 提交：CLI 的协议版本不同 | 本机 gherkai 1.6.0 的 worker 协议版本是 3，这个后端记下的是 2（后端记下的发行版本：1.5.2）。没有写下任何记录。（固定话） |
| 提交：镜像的协议版本不同 | 变体 login 在 novaact 上的镜像的 worker 协议版本是 2，后端记下的是 3（后端记下的发行版本：1.6.0；这个镜像推送于 <时刻>）。没有写下任何记录。（固定话） |
| 提交：记录里的能力对象不合约定（协议版本相同，不是数据版本不合，不加固定话） | 变体 login 在 novaact 上的对应关系记录（/gherkai-backend/worker-variant/novaact/login）里的能力不合本机 gherkai 1.7.0 的 worker 协议版本 3 的约定：session_warmup（是否支持会话预热）不是布尔值。没有写下任何记录。 |
| 提交：变体缺失（不是数据版本不合，不加固定话） | 变体 common 在 novaact 上没有对应的镜像（参数存储里没有 /gherkai-backend/worker-variant/novaact/common）。请部署方用 gherkai deploy push-worker 推送这个变体，或改用另一个已推送的变体提交。 |
| 推送：协议版本不同 | 本机 gherkai 1.6.0 的 worker 协议版本是 3，这个后端记下的是 2（后端记下的发行版本：1.5.2）。没有推送这个镜像。（固定话）镜像与它们不同时写三方的值：镜像 acme-novaact:login 的 worker 协议版本是 2，本机 gherkai 1.6.0 是 3，这个后端记下的也是 3。没有推送这个镜像。（固定话） |
| 查看或等待：记录格式不同 | run <id> 的记录格式版本是 2（由 gherkai 1.5.3 写出），本机 gherkai 1.6.0 读写的是 3，没有读取它的其余记录。（固定话）由 1.4 写出的写「记录格式版本是 0（由 1.5 之前的 gherkai 写出，没有记下写出它的版本）」 |
| `settle-runs` 的原因列 | 记录格式版本 2（由 gherkai 1.5.3 写出），本机是 3；没有改动它 |
| 本机 worker 的协议版本不同 | 引擎 novaact 的 worker（python -m gherkai_worker_novaact）报出的 worker 协议版本是 1，本机 gherkai 1.5.0 是 2，没有用它执行。（固定话） |
| 本机 worker 的自述不合约定（协议版本相同，不是数据版本不合，不加固定话） | 引擎 novaact 的 worker 的能力自述不合 worker 协议版本 2 的约定：缺 targets（支持的测试目标）。没有用它执行。自述不是 JSON 对象、读不出协议版本时写「能力自述输出不是 JSON 对象，读不出它的 worker 协议版本」 |
| worker 拒绝 job（job 的说明） | 交给这个 worker 的 job 是 worker 协议版本 3，这个 worker 是 2，没有执行这个 job。 |
| worker 拒绝匹配查询的输入 | 匹配查询的输入不合这个 worker 的 worker 协议版本 2 的形态，没有回答。（匹配查询的输入不带协议版本，只能陈述这一边） |
| 后端写进运行态 | 四句原因的样例、截断与长度上界都在 [0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节说明表下的一段；run 级与被它结束的各 job 写同一句 |
| `explain` 不补取事件 | 这个 run 记下的 worker 协议版本是 2，本机是 3，被中止 job 的执行记录没有解读。 |
| `deploy` 在 cdk 之后比不上 | 后端现在记下的数据版本与本次部署的不同：run 记录格式版本 后端 5 · 本次 4（后端记下的发行版本：1.7.0）。本次没有同步基础镜像、没有初始化默认指针、没有重派生既有变体。（固定话） |

能力不满足（本机按 worker 的能力自述判断，云端按所选镜像的对应关系记录判断）不是数据版本不合，不适用总则 4：说明给出怎么办，不加固定话、不提发行版本，写法在各项能力的定义处（目标见 [0048](./0048-test-targets-device-and-ui-kind.md) 决策 4，会话预热见 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 13「能力与拒绝点」）。

**`--json` 下**：比不上时标准输出不给文档，标准错误给上表那一句，退出码 2（[0041](./0041-agent-facing-cli-affordances.md) 决策三，诊断写到标准错误）。`settle-runs` 在这个 run 的项里给 `outcome` `skipped`、`reason` `other_version`，不另加键。

**查看与处置的出口**：提交记录读得到而本身解析不了（不是合法的 JSON、顶层不是对象）或头的形态违约时，`status` 与 `explain` 同样以退出码 2 结束并说明这条提交记录读不出，与记录格式版本不同走同一个出口，不让解析异常的回溯出现在用户终端。两个处置入口不处置记录格式版本与本机不同的 run：等待中的 `status --wait` 在开始等待之前比，以上表那一句、退出码 2 结束；`settle-runs` 把它记为跳过，`reason` 为 `other_version`。理由：别的格式写出的记录不按本版本解释，更不用本版本的模型读改写它（被拒方案「跨格式时用本格式的读写方读写别的格式的运行态」）。提交记录不存在或内容不合法（含头的形态违约、记录格式版本不是整数）的不算别的格式写出，两个处置入口按期限读不出处理；等待中的 `status --wait` 处置之后的显示与不带 `--wait` 的 `status` 相同。取值与判定的次序见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策六、决策八。

**`doctor`**（这里只写比对规则；各行的归属、说明的内容与结构化字段见 [0041](./0041-agent-facing-cli-affordances.md) 决策四）：
- 云端：必修行 `backend.data_versions` 按云端提交要的条件比三对值，接口版本、记录格式版本与 CLI 的 worker 协议版本都与后端相同才通过；参数不存在或读不懂是查过、未通过，读参数失败时这一行失败。这一行没有通过（未通过或失败）时，其余云端各行不读、记为未查（[0041](./0041-agent-facing-cli-affordances.md) 决策四「哪些行算未查」）。镜像的协议版本另按引擎比：默认变体的逐引擎行比这个镜像记下的协议版本与后端的，不同时这个引擎算不可用（可选项）；相同时，解读记录里的能力对象之前按 CLI 自己的契约校验它，与本机读能力自述是同一处校验，不合约定时这个引擎同样算不可用（[0038](./0038-worker-image-delivery.md)「镜像标注」段「读出」）；聚合项「至少一个引擎可用」仍是必修。
- 本机：定位到了、协议版本与 CLI 不同的 worker，算这个引擎不可用（可选项）；聚合项「至少一个引擎可用」只计协议版本相同的引擎，两个都不可用即必修项失败。

**`list-runs`**（这里只写比对规则；行的形态、标注的文字、表格上方那一句与 `--json` 的键集见 [0041](./0041-agent-facing-cli-affordances.md) 决策七「人读形态」「机读形态」「写出版本的标记」）：按 run 比记录格式版本，只做标注、不拒绝任何一行；记录格式版本在每一行本来就读的提交记录头里，不多读。与本机格式不同的行与头读不到的行各自标出，标出格式的行只读运行态的公共部分。

**`explain`**：证据按证据文件自带的格式号核对，不归 worker 协议版本（[0042](./0042-step-evidence-and-explain.md) 决策六）。补取被中止 job 的事件之前比这个 run 记下的协议版本与 CLI 的（上表），不同时怎样显示见 [0042](./0042-step-evidence-and-explain.md) 决策七第 3 条。

### 加号的纪律

**加号判据（三个号共用）**：在改动的那一刻问：这次改动之后，另一头还持旧号的一方，或者还在途的旧东西（旧 run、旧 task、旧定时触发、旧镜像、旧记录），会不会读不懂、读错或做错？会就加相应的号；只是新代码要读在途的旧东西、而持旧号的一方不受影响时，也可以让新代码认旧形态。这是改动时的做法，本 ADR 不声称各号的归属与跨版本不变的约定列得完备。下面七问是这个判据的展开：一次改动不加号，当且仅当七问都答「不会」；任何一问答「会」或答不上，就加号。删去、改名、改类型、新增必有的部分，一律加号。七问的回答写进登记，作为这次改动的论证。

1. **忽略**：持旧号的读方忽略不认识的部分之后，得出的状态、判定、期限、要执行的动作，或它显示出的任何一项值，会不会与新读方不同？只是少显示这一项不算。
2. **缺席**：持新号的读方读旧写方写出的内容时，按登记的缺席含义读，会不会与旧写方实际的行为不符？
3. **维护**：持旧号的写方改写这份记录、原样带回它不认识的部分，记录会不会因此不再成立？有些属性要求每个写方每次都维护：派生值、写入序号、状态分组、被后端触发条件、索引或生命周期规则匹配的属性、被部署命令跨格式读取的属性。新增这样的属性、改它的维护规则、让触发条件、索引或生命周期规则改为依赖别的属性或取值，这一问都答「会」。
4. **转交**：经持旧号的中间方转交时，新加的部分会不会到不了接收方，接收方缺了它会不会判错？两个方向都问：后端把运行定义转成 job 行与环境变量交给 worker；后端把 worker 的事件投影成判定明细交给 CLI。后端只按自己的模型产出 job 行与环境变量，所以凡要到达 worker、或会改变后端推进与判定的运行定义新键，一律加号。
5. **含义**：已有部分的含义有没有变（单位、取值的意思、由谁写、何时写、指向的资源）？
6. **封闭集合**：有没有给封闭的取值集合加值：判定明细里 scenario 与 step 级的状态值、事件类型、step 参数的 kind、目标的 device 与 ui_kind、会话的 origin 与 release、自述与能力标注里 targets 的取值、运行定义与 job 行里的 engine、explain 解引用的产物 kind、读方据以分支的 errorType？（run 与 job 的状态取值不在此列，含判定明细里 job 级的状态：它原样进运行态。它们属跨版本不变的约定，任何格式都不改。）
7. **协议**：多条记录之间的先后、条件写的条件、锁与改名的协议，有没有变（例如云端建 run 先写头、再写运行态）？

典型归类：
- run 记录格式版本要加号：新增后端或 worker 要用的运行定义键；新增或改变每个写方都要维护的运行态属性；改变已有值的含义；改变判定明细在 run 位置之内的键；改变本机 run 目录布局，或运行态短锁与 run 目录改名之后的生命期锁的协议（暂存阶段的互斥不能改，约定五）；本机事件库改列名或加不可为空的列；改变后端触发条件所依赖的属性与取值。不用加号：只给 CLI 显示或说明用、旧读方忽略之后得出的值都相同的键；本机事件库加可为空的列。
- worker 协议版本要加号：job 行新增 worker 必须据以执行的键；新的事件类型；给封闭集合加值；改变注入的环境变量名；改变镜像的启动约定。不用加号：自述或能力标注新增 CLI 可以选用、缺席时有明确含义的键（[0049](./0049-worker-capabilities-targets-keys.md) 决策 1 是先例；能力标注里可省的键缺席读作不支持，必有键 `engine` 与 `targets` 缺席即不合约定、推送被拒（[0038](./0038-worker-image-delivery.md)「镜像标注」段），云端提交时按对应关系记录里记下的同一份内容判断，所以这一条在云端同样成立）；事件里新增只补充细节、经后端投影之后判定不变的键。
- 云端后端接口版本要加号：删去或改名参数、索引、前缀、Lambda、CLI 读的环境变量；改变参数值的结构；改变 `worker_task_def_arns` 的含义（记录格式版本同加）；改变 `apps/` 的保留天数；改变部署命令依赖的模板形态或血缘 tag 的含义；改变 events 表的键。不用加号：新增只给新版本命令读、缺席时有明确含义的参数或字段；新增索引而保留旧的；新增只给新版本命令用的前缀。
- 都不能改：跨版本不变的约定（下），含运行态的状态取值集合。

**读的一方**：
- **不认识的键**：结构字段的每一层都忽略。数据版本参数除外（键集恰为三个）。以键承载数据的位置不在此列：额外请求头里的头名、云端运行态里以 scope 标识为键的 `jobs` 等，键本身就是数据，多出一个就该照常交给 worker、或多出一个 job；这些位置登记在基线里（下「护栏」）。
- **缺席的键**：每个值的基线把键分成必有与可省。必有键缺席即违约，按读不出处理；可省键（无值时省去的键）缺席读作「没有值」；同一个值之内后加的键各自登记缺席含义，读的一方按登记读。判定轴上的键不拿「空」兜底：运行态缺 `jobs` 读不出（读成空会让结束写把 run 记成 passed）；判定明细缺 `scenarios` 是违约；提交记录的必有键必须在，可省键与登记的键按缺席含义读；Midscene 的 worker 对缺席的设备请求键在建会话之前按违约拒绝。
- **运行定义的必有键与 null**：不适用的值写 null，不省键。job 的 `target` 桌面也写 desktop/web，`device_request` 无值写 null；`timeout_s` 恒为有限正数、run 级的 `deadline_at` 恒为带时区的 ISO 时刻，两者没有「不适用」的情形，读端把 null 当作定义违约拒绝；run 级的隧道请求头、`max_concurrency`、`steps_dir`、`worker_variant` / `worker_task_defs`、`session_warmup_url`、`cli_version`、`worker_protocol_version` 同为必有键。
- **不认识的事件类型、封闭集合里的新值**拒绝：按第 6 问它们一出现就要加号，值相同的两方之间不会遇到；遇到了就是判错或缺陷，报错退出是对的。封闭集合在 code 里都是具名常量，解析与基线生成都引用它。
- **读的一方不改动记录**：本机事件库在读时不执行建表与库的设置。

**写的一方**：改写记录时原样保留不认识的部分；整条换成新内容不算改写。写入口从 code 的写调用逐一枚举（键值写、条件更新、对象写与复制、参数写、tag 写、SQLite 的写语句），逐个登记是「原样保留」还是「整条换新」并写明理由：
- 本机运行态：原样保留，顶层与 job 条目一级（按 scope_id）都带回读到的附加键，同名时以模型为准；job 条目的键集与 `RUN_STATE_KEYS` 在同一处登记。结束写只有按本格式的模型算出的一种：本机没有用到 error 变体的来路（下「后端遇到别的格式写出的 run」的「本机」条）。
- 云端运行态，按写入口分，都是原样保留：
  - 逐属性写（认领、投影、单条 job 的写）：不提及不认识的属性。
  - 整体替换 `jobs` 的写，即记下 job 终态的写与按本格式的模型算出的结束写（error 变体以外的各条来路）：读整份运行态，按本格式的模型算出要写下的运行态，把读到的条目里不在已知键集内的属性并进去，已知键不从读到的值并入（否则无值省去的键会被写回）；只对与本方记录格式版本相同的 run 用。
  - 只写公共部分的结束写，即 error 变体（运行定义不可用、别的格式写出的 run；同格式与别的格式写出的都走这一个入口）：不按本格式的模型解读运行态，不经按模型算终态的那一步；读到的条目原样复制，只把未结束条目的 `status` 改为 `error`、各写同一句 `message`，另改 run 级的状态、状态分组、结束时刻、说明与写入序号（[0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节）。
  - 两种结束写各是一个入口，不混用，条件相同：写入序号等于读到的值，且 run 未结束。云端运行态有这两个结束写入口，本机运行态只有按本格式的模型算出的那一个（上「本机运行态」一项）；error 变体的入口只在云端的存储上。存储一侧各自的步骤见 [0030](./0030-realtime-persistence-seam.md) 决定六，两种存储的落法见 [0030](./0030-realtime-persistence-seam.md) 决定四「改写运行态时原样保留不认识的部分」。
- 本机事件库只由建 run 的那个发行版本的进程写（前台 `run` 与后台推进进程），不要求保留；新加的列必须可以为空或带缺省值。
- 云端退出记录由观察者与超时处置以同一个键整条写入，登记为「整条换新」；给它加属性时，第 3 问要论证覆盖写不丢它。
- 提交记录与判定明细只写一次。
- 变体的对应关系记录：重派生是改写，先读、再改、再写，保留不认识的键与 `pushed_at`、`worker_protocol_version`、`capabilities`；推送换了镜像是整条换新（[0038](./0038-worker-image-delivery.md)）。
- 安装包对象刷新时整套替换对象 tag，登记为「整条换新」；新增被生命周期规则匹配的 tag 要加号（第 3 问）。

**发行前提**：每个值第一次随发行出现的那一版，必须已经带着上面的读写做法与下面的护栏，否则同一个值之下的后续加法都不安全。第一个带数据版本的发行版本 1.5.0 同样受这条约束。

**护栏**（不靠钉死键集：键集全等挡不住同一个值之内的加法，也不核加号的论证）：
- **形态快照**：每个号的每个值一份基线（放在 core 的测试目录下），由工具生成：用最小实例（可省字段全空）与最大实例（每个字段都填满）记下各种记录每一层的键、类型、必有还是可省，各封闭集合（取自具名常量），每个写方都要维护的属性，以键承载数据的位置（上「读的一方」），以及公共部分的形态。云端条目的属性集取各写入口执行之后的并集（写入序号与状态分组只出现在写表达式里）；协议版本的事件取两种语言的 worker 共用的样本；接口版本的基线取自命名真源与合成出的模板。有差异、而同一个提交里既没有加号也没有对应的登记，即失败；公共部分有任何差异即失败。
- **登记与缺席含义**：登记的每一项写明位置、缺席含义、七问的回答、一份样本与期望的读法。测试取当前写方写出的记录删去这一项，用当前读方读，结果必须等于登记的缺席含义；缺任何一个回答、或有一问答「会」，也失败。新值的登记从空开始。
- **读忽略**：基线列出的结构字段的每一层注入一个不认识的键，读出的判定结果与不注入时相同。比较的是读方据以判断与显示的值：状态、判定、期限、要执行的动作、能不能执行、支持哪些目标；原样带出记录内容的输出（`list-workers --json` 带出的 `capabilities`）带回注入的键是对的，不在比较之内。登记为以键承载数据的位置不注入，那里多出的键本来就该改变读出的结果。
- **写保留**：登记为「原样保留」的每个写入口，带着不认识的键执行一次（每个可变的结构层各放一个），之后键还在、值不变、无值省去的已知键没有被写回；code 里有写调用没有登记即失败。
- **已发行样本回放**：生成基线时那一版写方写出的记录、事件与 job 行，加每条登记的样本，各附期望的状态、判定与期限；当前读方读它们，结果必须等于期望。
- **簿记**：常量的当前值必须有基线；新值必须大于已有全部基线的值（日常测试）。已发行的基线、样本与登记不许改，由发布链守（决策 8「tag 触发全链」的 gate）。发行按版本号递增、一次只发一个版本：上一个 tag 发布完成之后才打下一个；打了而不发出的 tag（要改提交或换版本号重发）先删去。检查两步：本次 tag 的版本号必须大于仓库里其它每一个 `vX.Y.Z` tag，否则不发行；本次 tag 所在提交里的基线、样本与登记文件，对照版本号排在本次之前的最近一个 `vX.Y.Z` tag 里的同名文件，那个 tag 里有的本次必须有、且逐字节相同，否则不发行。受守的文件这样划分：每个值的基线与随它生成的样本各自成文件，一条登记连同它的样本与期望单独成一个文件，同一个值之内的加法只新增登记文件、不改已有文件。按这个发版次序，逐版对照即逐版传递，任一发行里的这些文件在之后的每个发行里都不变。给较旧的发行线补发（版本号小于已有的 tag）不支持，在第一步被拒（被拒方案「发布链对照每一个已发行 tag，以支持给较旧的发行线补发」条）。冻结点由 git tag 推出，不另记发行字段（发行版本的唯一真源是 git tag，2b）。第一个带这个值的发行发出之前，基线可以随开发期的修正重新生成。

**剩下的风险**：
- 机械可守的是形态、读忽略、写保留与已发行样本回放。「忽略这一项在语义上是否无害」「经后端转交时会不会丢」「含义变了而形态没变」只能靠登记里的论证与复核；测试只核论证给了、缺席含义与 code 相符。值相同而后端丢掉要到达 worker 的运行定义字段，属于第 4 问的漏判，worker 一侧的最后一道是 [0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 13「definition 完整性不变量」。
- 最小与最大两种实例照不出字段之间的成对约束：两项原本各自可省的字段改为必须同时出现时，全空与全满两个实例照样通过；这一类只靠登记里的论证（第 2、5 问）。
- 跨发行的互操作（装上一个发行版本的包来读写新记录）不测。
- 基线与登记都在仓库里，发行之前有意同时改两者就能绕过；护栏挡的是没有论证的改动，不防有意绕过。已发行的基线、样本与登记的改动要到下一次发行时才被拦下。
- 旧写方只原样带回新键、不按新规则维护它；凡要求每次都维护的键按第 3 问已归为要加号，剩下的是论证时漏判。

### `deploy` 入口的检查

- **位置**：本地前置检查（工具链、容器引擎、`--vpc`）与目标解析之后，VPC 取值三态比对之后，找回或建立 Device Farm 项目与调用 cdk 之前；只读，不改动账户。与 VPC 取值三态比对共用同一次读 stack；stack 不在即第一次部署，不做检查、不输出。
- **比较**：读数据版本参数（上「后端的三个值怎样读」；读取失败以退出码 2 结束、不改动账户），与本次的三个常量比。三个都相同：照常部署，不输出。有不同（含后端无值）：列出三行（这个号在后端的值与本次的值；参数不存在写「未记下」，读到了而读不懂写「读不懂」，原值的前 200 个字节放在随后那一句里，下「输出只陈述事实」）与两边的发行版本（后端一侧是版本戳读到的，同上「版本戳另读」），再数未结束的 run。
- **数未结束的 run**：只在后端有值、且接口版本与本次相同时数：按 `list-runs` 的索引就绪判据（[0041](./0041-agent-facing-cli-affordances.md) 决策七「索引就绪判据」）核对状态分组索引，再对 `live` 分组做 `Query`（`Select=COUNT`，翻页读完）。状态分组属于公共部分，别的格式写出、还没被结束的 run 同样在里面，不必逐个读头；计在内的还有记录读不出的 run。后端无值或接口版本也要变时，本次的 `deploy` 不认识后端表的形态，不去读，记为「数不出」：去读别的接口版本的表，就是让新版本保留读旧版本的分支。计数是最终一致的读，输出写「读到 N 个」、不写「没有」：读到 0 不证明没有未结束的 run，检查之前刚写下的 run 可能还没进索引。这样的 run 与检查之后才提交的 run 同类，由部署之后的后端按它的规则处理（下「部署进行中」）；不改成逐条强一致读（被拒方案「deploy 的计数改为强一致的逐条读」条）。读计数失败（权限、限流）以退出码 2 结束、不改动账户。
- **默认不继续**：有任何一个数据版本要变（含后端没有记下与读不懂），且读到的未结束 run 多于 0 或数不出，以退出码 2 结束、不改动账户；带上 `--allow-data-version-change` 再执行即部署，后端无值的两种情形（参数不存在、读不懂）同样认这个旗标。读到 0 时照常部署。读参数失败（凭证、权限、网络）不认这个旗标：带不带都以退出码 2 结束、不改动账户（上「比较」一项；读取失败既不当作比不上、也不当作比得上，上「后端的三个值怎样读」）。旗标与 `--allow-vpc-change` 同一形态，只贴在 `deploy` 上（决策 6）；不做交互确认（调用方常是 agent 与 CI）；不需要时给了不起作用。
- **基础镜像同步的前提**：协议版本要变（含后端没有记下与读不懂）、且本次会同步基础镜像（纯发行版本）时，这项检查放行之后（照常部署或带了旗标）、找回或建立 Device Farm 项目与调用 cdk 之前，核两项不改动账户的前提：容器引擎可用、两个引擎的基础镜像拉得到（这时拉下来并校验标注）；任一不成以退出码 2 结束、不改动账户，`--allow-data-version-change` 不放行，说明陈述事实。同步本身在 cdk 之后；做法、协议版本不变或首次部署时的处理与理由写全在 [0038](./0038-worker-image-delivery.md)「`gherkai deploy` 的 worker 镜像四步」第 2 步。
- **输出只陈述事实**：除默认不继续时那句固定的结尾外，输出陈述的只有这次命令读到的值、本次自己的值，与这次命令有没有改动账户。跟在三行之后，各一句：
  - 未结束的 run：读到几个就写几个，读到 0 个也写「读到 0 个」；数不出时写无法确认后端里有几个未结束的 run。只写这个数，不说这些 run 之后怎样：计数不读各 run 的数据版本，读到的 run 之后是照常执行完、被后端结束、还是由别的写方先写成终态，这次命令不知道（下「后端遇到别的格式写出的 run」）。
  - 后端没有记下数据版本：「这个后端没有记下数据版本」，附后端记下的发行版本（版本戳不存在写没有记下，读取出错写读不出），不替它断定由哪个版本部署、上一次部署是否完成（理由同上「说明的要点」表「读不到数据版本」一行）。后端记下的内容读不懂：「这个后端记下的数据版本读不懂」，附原值的前 200 个字节与后端记下的发行版本，不说它是不是 gherkai 写下的。
  - 凡默认不继续的情形，结尾都是同一句、不随情形变化：「本次没有改动账户。要继续部署，带 --allow-data-version-change 再执行。」不承诺带旗标之后的结果。
  - 不按情形预告部署之后的事（哪些 run 会被结束、哪些提交会被拒、哪些命令会出错、`base` 是哪一份镜像）：这些是各篇写明的规则，由用户文档 `cloud-backend.md`「版本与升级」一节与 `--allow-data-version-change` 的帮助文字按规则陈述，不由这次命令套到它读到的数上（被拒方案「`deploy` 的输出按情形预告部署之后的结果」条）。这次命令要做的事（核对容器引擎、拉取与同步基础镜像）做到那一步时各自输出，不在这里预告。cdk 失败时只给 cdk 的失败说明，不另加对 run 的推断。
- **接口版本要变时在执行的 run**：记录格式版本或协议版本也要变的，由后端的闸按下「后端遇到别的格式写出的 run」处理；两者都不变的，与部署进行期间写下、只有接口版本与后端不同的 run 同样处理（下「部署进行中」首条）。产品不另设处理：接口版本要变时一律数不出、默认不继续，部署方带旗标才会走到这一步。
- **`deploy --diff`**：做同样的读取与计数，把与 `deploy` 相同的三行、两边的发行版本与事实句（上「输出只陈述事实」各项）作为信息输出，不带默认不继续的那句结尾，不拦，不需要旗标，退出码按 cdk diff；不同步基础镜像，也不核上「基础镜像同步的前提」（[0038](./0038-worker-image-delivery.md)「`gherkai deploy` 的 worker 镜像四步」第 2 步）；读参数失败与读计数失败属于调用 cdk 之前的阶段，与它读 Device Farm 项目记录失败同样以退出码 2 结束（[0051](./0051-device-session-lifecycle-and-app-distribution.md) 决策 10）。`--synth-only` 不做这项检查，不输出这一项。
- **降级部署**用同一条规则，只比是否相等。降到 1.5 之前的发行版本时执行的是没有这项检查的旧代码，写进升级须知。
- **权限**不新增：这项检查用到的调用是读 stack 的 `cloudformation:DescribeStacks`（与 VPC 取值三态比对同一次）、读数据版本参数与版本戳的 `ssm:GetParameter`、索引就绪判据的 runs 表 `dynamodb:DescribeTable`、对 `live` 分组计数的索引上的 `dynamodb:Query`，部署方都已有，逐项登记在 [0033](./0033-iac-aws-backend-and-composition-wiring.md)「资源清单」末段的部署方一项（后两项的来由见 [0038](./0038-worker-image-delivery.md)「权限面增量」）。
- **cdk 之后的三步**（[0038](./0038-worker-image-delivery.md)「`gherkai deploy` 的 worker 镜像四步」里的后三步）走推送路径，开头读一次数据版本参数，与本次的三个常量比：cdk 成功之后参数就是本次的值，比得上；比不上时（通常是检查之后另有一次部署改了后端；说明只给两边的值、不断定原因）以退出码 1 结束（账户已改动，与后三步别的失败同一退出码），给出两边的值，后三步都不做（不同步基础镜像、不初始化默认指针、不重派生）：接着做会把与后端协议版本不同的镜像推成 `base`。这一次读取本身失败同样以退出码 1 结束、后三步都不做。认不出的是另一次部署在本次 cdk 之前完成、随即被本次覆盖（下「部署进行中」末条）。

输出样例（记录格式版本要变，后端有未结束的 run）：

```
后端记下的数据版本与本次的不同（后端记下的发行版本：1.5.2，本次是 gherkai 1.6.0）：
  数据版本              后端    本次
  run 记录格式版本      3       4
  worker 协议版本       2       2
  云端后端接口版本      1       1
后端里读到 3 个未结束的 run。
本次没有改动账户。要继续部署，带 --allow-data-version-change 再执行。
```

| stack | 后端的值 | 接口版本 | 未结束的 run | 结果 |
|---|---|---|---|---|
| 不在 | — | — | — | 照常部署，不输出 |
| 在 | 读取失败 | — | — | 退出码 2，读取失败的说明；带旗标同样如此 |
| 在 | 三个都与本次相同 | — | 不数 | 照常部署，不输出 |
| 在 | 读得出，有不同 | 相同 | 0 | 列出三行与读到 0 个，照常部署 |
| 在 | 读得出，有不同 | 相同 | 多于 0 | 列出三行与个数，退出码 2；带旗标即部署 |
| 在 | 读得出，有不同 | 相同 | 计数失败 | 列出三行，退出码 2；带旗标同样如此 |
| 在 | 读得出 | 不同 | 数不出 | 列出三行，说明无法确认，退出码 2；带旗标即部署 |
| 在 | 没有记下 | — | 数不出 | 列出三行与「没有记下」那一句，说明无法确认，退出码 2；带旗标即部署（对 1.4 部署的后端的后果见下「1.4 到 1.5」） |
| 在 | 读不懂 | — | 数不出 | 列出三行与「读不懂」那一句，说明无法确认，退出码 2；带旗标即部署 |
| 在 | 协议版本要变（含没有记下与读不懂） | — | 上面几行里照常部署或带了旗标 | 本次会同步基础镜像时，上「基础镜像同步的前提」有不成的：退出码 2、不调用 cdk，带旗标同样如此 |

### 部署进行中

部署是一段可以长到几分钟的窗口，不是一个时刻：
- 一条 `submit` 从比对到写下记录之间（资源检查、变体解析、补全运行定义、起隧道），比对时的值可能过时；写下的 run 与处理它的后端代码的记录格式版本或协议版本不同时，由后端的闸按下「后端遇到别的格式写出的 run」处理（保证的范围、前提与别的写方的先后都见那里）。只有接口版本不同时，后端不比接口版本（总则 3），照常推进这个 run；它能不能做完取决于这次接口改动有没有动到它用到的资源（表、前缀、容器名等），做不完的按后端已有的失败与到期规则结束（推演）。这一段可以到分钟级（上传安装包、起隧道，推演）。
- 参数之外的资源依次更新期间，参数仍是旧值，各 Lambda 在不同时刻换上新代码：持旧值的命令通过开头的比对；记录格式版本或协议版本变了时，先换上新代码的 Lambda 对这期间写下的旧格式 run 按下「后端遇到别的格式写出的 run」处理、不为它启动 task；接口版本变了时，持旧值的命令可能遇到已改的资源。参数更新之后，各命令按上「各入口比什么」拿新值比。
- runs 表流的事件源映射在这次部署里新建或更新时，那一刻写下的建 run 记录可能没有投递给 kicker：这样的 run 不被推进，期限加 300 秒之后由用户一侧的处置方结束（例外与边界写全在 [0054](./0054-run-deadline-lifetime-lock-and-settling.md)「边界与已知局限」里「其它局限」）。
- 更新失败回滚：参数与各 Lambda 改回的先后没有核到，两种先后下被结束的是不同的 run，其中有回滚完成之后的后端本来能执行的；回滚本身失败时参数与代码可以长期不一致，部署方按 CloudFormation 的做法恢复栈。
- 接受这些被结束的 run：使用者在 run 的说明里看得到原因，重新提交即可；按值的大小区分方向与「只比是否相等」相抵。不为窗口另设机制：命令一侧多读一次参数只能缩短窗口，关不上 Lambda 与参数之间那一段。
- 检查之后、真正更新之前又有人提交，或检查之前刚写下、还没进索引而没被数到的 run：与检查时已有的 run 一样，由部署之后的后端按它的规则处理，读到 0 而照常部署时部署方事先不知道它们（上「`deploy` 入口的检查」里「数未结束的 run」一项）；不设提交锁（它要所有提交方都遵守一套跨进程协议，而部署本身就要几分钟，这个窗口只能缩短、无法消除）；用户文档写部署之前通知团队暂停提交。
- 两位部署方几乎同时向同一个后端部署不同版本：接受为已知风险，用户文档写一个后端一次只由一位部署方部署；cdk 之后的三步开头的比对认得出另一次部署在本次 cdk 之后完成的一类。两次部署同时发起、cdk 遇到正在更新的 stack 时的表现没有核到。

### 后端遇到别的格式写出的 run

后端各入口先过同一道闸，分支、次序与读量在 [0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九「落实时，后端各入口先过同一道闸」一段写全。结论：先强一致读运行态，只读公共部分，不存在或已结束即清扫，公共部分读不出按损坏的记录只记日志；未结束的再读提交记录的头，头不在、格式版本不是整数或不是后端的（缺这个属性读作 0），以 error 变体结束、之后清扫，不取 jobs 对象；是后端的再按本格式读其余部分与整份运行定义，不可用（含运行定义记下的协议版本不是后端的）同样以 error 变体结束。读量与只有一种格式时相同：未结束的 run 本来就要读头，已结束的 run 不读头。别的格式写出的 run 不等到期限，第一次被带到就做这次结束写；它与别的写方的先后，见下「与别的写方的先后」。

- **保证的范围**：后端被带到一个别的格式写出（记录格式版本、或运行定义记下的 worker 协议版本与后端不同）、还没结束的 run 时，清扫它的 task（停掉这一次列得出的，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策九第 2 条）；以只写公共部分的结束写（下条 error 变体）把它记为已结束，同一次写里每个未结束的 job 都成为终态；数据版本与后端相同的其它 run 不受影响。与别的写方谁先把 run 写成终态，照下「与别的写方的先后」。产品做到的就是这三件（owner 认定），不保证这个 run 里各 job 的结果准确：已做完的 job 可能被记为 `error` 或没有结果，退出原因的归类可能不准，产物可能不完整（被拒方案「数据版本不同时连各 job 的结果也保证准确」）。
  - 前提是有调用把后端带到这个 run（没有调用带到的见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md)「边界与已知局限」里「其它局限」），并且那一次的结束写写成或读到 run 已结束：别的写方接连改动运行态、使这一次的条件写用尽重试时（[0030](./0030-realtime-persistence-seam.md) 决定六「重读的次数有上限」一项），这次调用失败、没有走到清扫，由之后带到它的调用重新读运行态：仍未结束则再做结束写，已结束则只清扫。降级与成功回滚的方向、记录格式版本与云端后端接口版本同时改变的那一版，不保证做到：这样的 run 可能一直显示未结束（没有 task 时不产生执行费用），此后数据版本要变的 `deploy` 读到它，要带旗标才继续。这类 run 多出自部署方带旗标继续、或提交与部署几乎同时（逐条见下「这类 run 的来路」）。
  - 命令行工具与本机一侧不另立保证：各入口比什么、`list-runs` 对别的格式写出的行只读公共部分、暂存目录的清理，各在原有的条文里（上「各入口比什么」，下「跨版本不变的约定」约定三、五）。
- **error 变体**是只写运行态的公共部分的那个结束写入口（上「加号的纪律」里「写的一方」），同格式与别的格式写出的 run 都用它，写法在 [0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节「运行定义不可用、或 run 由别的格式写出时」条；原因的四句见 0031 同一小节说明表下的一段，run 级与被它结束的各 job 写同一句。提交记录已不在而运行态还在（含云端头还在而 jobs 对象已不在，[0030](./0030-realtime-persistence-seam.md) 决定六「jobs 对象取不到时」）同样以它结束。
- **与别的写方的先后**（只在本条写全，别处引用本条）：后端对别的数据版本写出的未结束 run 做的是 error 变体的结束写与清扫（停掉它的 task）；这一写以写入序号等于读到的值、且 run 未结束为条件，任何格式里改运行态的每一次写也都以 run 未结束为条件、run 成为终态之后任何格式的写方都不写它（下「跨版本不变的约定」里「运行态的公共部分」的「对以后各个格式的约束」一项），所以 run 的终态以第一笔使它成为终态的写为准，后端不保证这个 run 记为 error。这条约束的是 1.5 起各个格式的写方（1.4 的前台云端执行不在其内，下「1.4 到 1.5」）。别的写方有两种：按这个 run 的格式读写它的命令行工具（记录格式版本与这个 run 的相同；只是运行定义记下的协议版本与后端不同的 run，与后端同一记录格式的命令行工具就是），期限加 300 秒之后可以按处置的规则结束它（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策六、七，未结束的 job 记 `aborted` 或 `skipped`）；部署更新之前已经过了闸的那次后端调用，按它自己的格式照常推进（认领、写 job 的终态）或做结束写。别的写方的写使 run 成为终态的，后端的条件写不成立，重读到已结束，只清扫，记录保持那一笔的结果；别的写方的写改了运行态而 run 仍未结束的（写入序号变了，如写了某个 job 的终态、认领），后端的条件写同样不成立，重读之后再做一次 error 变体：已是终态的 job 保持不动，只把仍未结束的记 `error`（error 变体只改状态为 `pending` 或 `running` 的条目，[0031](./0031-job-lifecycle-states-and-severity.md) 决定三「结束写」小节），所以 run 记为终态时它的 job 都已是终态。后端先写成时，别的写方的条件写不成立、读到已结束（处置方给 `already_finished`）。后端在第一次带到这个 run 时就写，多数情形下它记为 error。各种先后得出的都是真实发生的结束，不另协调，与两个处置方同时处置同一个 run 的取法相同（0054 决策八「处置的次序」）。
- **读取本身的失败**（网络、权限）不在其内，原样抛出、由之后的触发再读，不当作格式不合或运行定义不可用：免得把可以重试的故障永久记成 error。
- **run 级消息的边界**：原因写进运行态的 run 级 `message`，与终态同一次条件写落库；团队成员未必有 CloudWatch 的读权限，没有这一句 `status` 只看见 error 不知为何。说明是产品语言的整句、长度有界，只陈述事实；契约异常的原文只进推进器的日志（它带内部字段名与形状描述，是给 contributor 的）。run 级说明只由结束写写下，各来路的那一句见 0031 决定三「结束写」小节的说明表；job 级原因（判定、超时、中止、worker 退出）留在 job 上（判定明细与 `explain`）。不影响退出码（`status` 对 error 仍是 1）。
- **此后**：被后端以 error 变体结束的别的格式的 run，在后端是已结束、之后的事件只引起清扫；记录格式版本与它不同的 `list-runs` 按公共部分列为 error，带后端写下的原因，并标出记录格式（由别的写方先结束的，列出的是那一方写下的状态与说明，上「与别的写方的先后」）；能不能查看它只看这个 run 的记录格式版本与云端后端接口版本：记录格式版本与这个 run 的相同、接口版本与后端相同的 CLI 可以查看它，发行版本与写出它的不同也一样（公共部分是按约定写下的，其余部分仍是这个格式），`settle-runs` 给 `already_finished`；记录格式版本与这个 run 的不同的 CLI 查看以退出码 2 结束（上「各入口比什么」）。回滚或降级到写出它的版本之后，已被结束的照旧是已结束（任何格式的写都以 run 未结束为条件，约定三）；新版本建的、未结束的 run，回滚或降级之后的后端带到时按同一规则结束，这个方向不保证做到（上「保证的范围」）。
- **这类 run 的来路**：部署方在 `deploy` 明确选择继续；检查之前片刻有人提交、那个 run 还没进索引而没被数到（读到 0 而照常部署，上「`deploy` 入口的检查」里「数未结束的 run」一项）；部署的检查与真正更新之间有人提交；部署进行期间有人提交；部署失败回滚；1.5 之前的命令行工具在有人用它向这个后端推送过变体之后提交（下「1.4 到 1.5」）。
- **本机**：后台推进进程与前台 `run` 都是建 run 的那个发行版本，持着生命期锁，用自己生成的那份运行定义推进、不从记录读回（决策 4「解析在组合根」条），所以本机没有「推进方读到别的格式写出的 run」与「运行定义不可用」这两种情形；记录格式版本与它不同的处置方遇到它只给 `other_version`（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策八）。别的格式写出、还在执行的 run，本机由建它的那个发行版本的进程执行完，云端被升级之后的后端结束。差别来自推进它的一方不同：本机是建 run 的那个进程，云端是共享的、被升级了的后端。这是两种执行方式固有的差别（owner 认定）。
- **记录格式版本与接口版本同时变的那一版**：升级之前建的云端 run，持旧记录格式版本的命令行工具同时也持旧接口版本，在命令开头就被挡住；持新接口版本的也持新记录格式版本，在按 run 比对时被挡住。任何版本的命令行工具都看不了这些 run 的细节、也处置不了它们，产品不为这种情形另做处理：后端按本节处理其中未结束的（这一版不保证做到，上「保证的范围」）；新版本的 `list-runs` 照常按公共部分列出它们并标出格式（前提是这次接口改动没有动到它们所在的表与索引）；已结束的 run 的报告页不受影响，被后端结束的 run 没有报告；这两个值都要变的 `deploy` 数不出未结束的 run、默认不继续（上「`deploy` 入口的检查」）；升级之前建的 run 在这样的升级之后看不了细节、也处置不了，由用户文档 `cloud-backend.md`「版本与升级」一节陈述。

### 跨版本不变的约定

不归任何号管、任何版本都不改；改了其中一项，等于改了比对或跨格式处理的判法本身。各项在它的定义处另有一句指向本节的指针。

| 约定 | 各版本靠它做什么 | 改了会怎样 |
|---|---|---|
| 一、数据版本参数的名字（`/{prefix}backend/` 加 `data-versions`）与最外层结构：JSON 对象，键恰为三个，值是正整数 | 读出后端是第几版 | 改名或改结构，别的版本读不到或读不懂，按无值处理、一律比不上；若改成读得出而含义不同（键名不变、含义互换），比对给出错误的「相同」 |
| 二、一个 run 的记录格式版本记在哪里、怎样读：本机是 run 目录里 `run_meta.json` 顶层的整数 `schema_version`；云端是 runs 表主键为（run_id，`META`）的条目顶层的数值属性 `schema_version`；缺席读作 0，不是整数即形态违约。运行态的位置：本机 `run_state.json`，云端主键为（run_id，`STATE`）的条目 | 按 run 比记录格式版本；后端的闸认出别的格式 | 别的格式的 run 被认成提交记录不在或形态不对：照样被结束，原因说错；运行态的位置变了则认不出这个 run |
| 三、运行态的公共部分（见下） | 后端结束别的格式写出的 run；`list-runs` 列出别的格式的行；`deploy` 数未结束的 run；kicker 的流过滤与状态分组索引 | 读方读错状态或认不出已结束；跨格式的结束写写坏对方的记录；不写分组的写方让 run 对清单、清理与计数都不可见 |
| 四、后端认出一个 run 的方式：run_id 只含字母、数字与连字符（因而不含 `#`、不以点开头）、不超过 36 个字符、字典序即创建时间序、抗碰撞（各点的依据见 [0027](./0027-runreport-aggregation-index.md)「run_id：归集索引的主键」节）；events 条目 `pk` 里第一个 `#` 之前是 run_id；定时触发载荷以键 `run_id` 带出 run 标识；起 task 时贴的 `startedBy` 取 run_id（ECS 对它的字符集与长度有限制），所在 cluster 是 `{prefix}cluster` | 从旧后端起的 task、旧 worker 写的事件、旧部署建的定时触发里认出是哪个 run，才能结束或清扫它；`list-runs` 在新旧格式混存时按 run_id 排序 | run_id 带上 `startedBy` 不接受的字符或超长，task 起不来；清扫列不到旧的 task 却算作完成，卡住的 task 一直计费；清单取到的不是最近的 N 个 |
| 五、本机报告目录一级：以点开头的名字留给建 run 的暂存目录；暂存目录的命名形态，以及清理方凭名字形态与目录锁认它、不读内容的判法；暂存阶段的互斥：建 run 的一方以只读方式打开暂存目录、取排他的 `flock`，写完两个文件再原子改名成 run 标识，从取到锁到改名完成持有的是同一把锁（改名前后是同一次打开），清理方同样以只读方式打开、不阻塞地取排他的 `flock`，拿到之后核对名字仍指向打开的那个目录才删（[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策三） | 任何版本的 `settle-runs` 都清理暂存目录、不删任何版本正在建的 run，`list-runs` 都跳过以点开头的名字，它们不经记录格式版本 | 旧版本把新版本正在建 run 的暂存目录当作可删的删掉（例如换了锁的取法，旧版本的清理方拿得到新版本持有的暂存目录的锁），或把它当成 run 列出 |
| 六、worker 协议版本记在哪里：镜像标注 `gherkai.worker-protocol-version`（十进制正整数）；本机 worker 能力自述（`--capabilities` 输出的 JSON 对象）里的 `schema_version`；job 行里的 `schemaVersion` | 推送时读出镜像的值；本机读出 worker 的值；worker 核对 job，以「协议版本不合」而不是「形态违约」拒绝别的版本的 job | 改了位置，别的版本读不到：推送被拒、本机判为取不到、worker 拒绝 job，都是失败，但原因说错；改作别的含义，比对给出错误的结论 |
| 七、值只增不复用：run 记录格式版本的 0 表示没有这个号；worker 协议版本不取 1 | — | 复用一个值，两种不同的格式比较起来相等，静默读错 |

**运行态的公共部分**：
- run 与 job 的 `status`：字符串，取值集合固定为 `pending`、`running`、`passed`、`failed`、`error`、`aborted`、`skipped`。`pending` 与 `running` 表示未结束，其余表示已结束。任何格式都不新增、不改名、不改含义；要表达新的结束原因，用别的字段。理由：清单、计数、流过滤与索引都按状态取值与分组工作，取值集合一变就要每个版本都认得新值；这七个取值自有运行态以来没有变过。
- `started_at`、`ended_at`：ISO 8601 时刻字符串，无值省去。run 级 `message`：字符串，无值省去。
- `jobs`：本机是列表，每项带 `scope_id`、`status`，以及 `message`（字符串，无值省去）；云端是以 scope_id 为键的 Map，每项带 `status` 与同样的 `message`。
- 云端另有 `status_group`（由 run 级状态派生：未结束为 `live`，已结束取状态的值；分组的集合随状态取值固定）与写入序号 `write_seq`。两者由每个写方维护；读方判断 run 是否结束只看 run 级 `status`，`status_group` 只供索引查询，缺席不算公共部分读不出。`write_seq` 是数值，缺席读作 0；只写公共部分的结束写（error 变体）以它等于读到的值为条件，写成即加一。各写入口怎样加它、各带什么条件，只在 [0030](./0030-realtime-persistence-seam.md) 决定六「STATE item 带写入序号」条与 [0034](./0034-detached-batch-reconciler.md) 机制三②写全。
- 对以后各个格式的约束：只经 error 变体改过（上「后端遇到别的格式写出的 run」）、其余部分原样的记录，必须是这个格式合法、一致的记录。所以任何格式都不能在公共部分之外新增要随这几项一起维护的属性，也不能要求被记为 error 的 job 条目另带公共部分之外的属性。任何格式里，改运行态的每一次写都以 run 级状态仍未结束为条件（1.5 起的格式已是如此，[0054](./0054-run-deadline-lifetime-lock-and-settling.md) 决策五）：否则别的格式的写方可能把后端已以 error 变体结束的 run 写回未结束（上「后端遇到别的格式写出的 run」里「与别的写方的先后」）。任何格式里，未结束的 run 都至少有一个未结束的 job，run 的状态与各 job 的状态之间按 [0031](./0031-job-lifecycle-states-and-severity.md) 决定三的取法（run 是终态当且仅当全部 job 是终态）：否则只写公共部分的结束写会留下 job 全部结束而 run 被记为 `error` 的记录。任何格式的未结束运行态也都要给只写公共部分的结束写留足余量：这一写给每个未结束的 job 加一句说明，另写 run 级的状态、状态分组、结束时刻、说明与写入序号，写成之后的记录仍须在单条记录的大小上限之内，否则没有一方结束得了这个 run；当前格式的余量由 [0034](./0034-detached-batch-reconciler.md) 机制三②「条目大小」的论证给出（job 数与两个标识的上限见 [0025](./0025-plan-module-feature-to-jobs.md)「一个 run 的规模上限」）。
- 现有的格式已与这一形态相同，只是 1.4 写出的云端运行态没有 `status_group` 与 `write_seq`，按上面讲这两项的那一条读（`write_seq` 缺席读作 0，`status_group` 缺席不算公共部分读不出）：1.4 的命令行工具向 1.5 的后端提交的 run（下「1.4 到 1.5」），后端按 run 级 `status` 认出它未结束、以 error 变体结束，这次写补上两项。依据是 1.4.9 的序列化代码与云端运行态的写入代码；没有用 1.4.9 实际写出的记录执行 1.5 的 `list-runs` 与后端的闸。

**不在此列**：期限 `deadline_at`（只对同一格式的 run 读，别的格式写出的 run 第一次被带到就结束或清扫）；写出版本 `cli_version`（读不到时写「未知」）；定时触发载荷里 `run_id` 之外的部分、kicker 的名字与定时触发的分组（由新部署按迁移口径承接，保留到旧触发都已执行；kicker 的名字另归云端后端接口版本，上「三个号各管什么」里「不归任何号」一项）。

### 发行版本作为取哪一份的缺省

下面几处用发行版本决定要取一份东西时取哪一份。它们不判断能不能一起工作，不要求使用者对齐发行版本，也不因发行版本拒绝操作；取不到发行版本时，各处按非纯发行版本（带 `.dev`、`.post` 或本地段，决策 3 第 4 级）处理。

| 位置 | 取什么 |
|---|---|
| 本机 worker 定位链第四级 | 按 CLI 的发行版本经 uvx 拉起同版本的 worker 包；只在纯发行版本且 PATH 上有 uvx 时走这一级（决策 3） |
| 兄弟包之间的 `==` 同版本锁定 | 安装时取同版本的各包（2b） |
| `deploy` 同步基础镜像 | 从 GHCR 取执行它的那个发行版本的基础镜像；非纯发行版本或取不到时跳过，`base` 停在原来的镜像（[0038](./0038-worker-image-delivery.md)「`gherkai deploy` 的 worker 镜像四步」） |
| Lambda asset | 从当前环境已安装的包复制（决策 6） |
| 定制镜像模板的 FROM 行 | 缺省写后端记下的那个发行版本的基础镜像，那一份的协议版本通常与后端相同、不保证；真正的要求是镜像的协议版本与后端相同（例外与核对见 [0038](./0038-worker-image-delivery.md)「概念模型」节「定制镜像模板」） |
| `deploy` 的版本戳 | 写进执行它的发行版本，只作事实；取不到时写 `unknown`（决策 6「版本戳」） |

用户文档里比不上时的解法以同样的口径给出：要与后端一起工作，装上后端记下的那个发行版本，即得到相同的数据版本。

### 1.4 到 1.5

不做兼容，写进升级须知。新模型对 1.4 不需要任何特殊处理：1.4 的后端没有数据版本参数，1.4 写出的记录的记录格式版本读作 0，两者都落在总则 1。

| 情形 | 表现 |
|---|---|
| 1.5 的命令行工具对 1.4 部署的后端 | 全部云端命令开头读不到数据版本，以退出码 2 结束；`doctor` 的数据版本一行必修项失败 |
| 1.5 的 `deploy` 对 1.4 部署的后端 | 后端没有记下数据版本、数不出未结束的 run，默认不继续，输出陈述事实，结尾那一句点出旗标。不提供原地升级的路径（与 [0041](./0041-agent-facing-cli-affordances.md) 决策七「更早的索引形态」同一取舍），升级须知写用新前缀另建。带上旗标时检查放行、cdk 尝试原地更新：runs 表要在同一次更新里删去旧索引、建立状态分组索引，按 [0030](./0030-realtime-persistence-seam.md) 决定六与 0041 决策七记下的平台约束，这次更新预计失败并回滚（推演，没有核到） |
| 1.4 的命令行工具对用新前缀另建的 1.5 后端提交 | 没有人用 1.4 的 `push-worker` 向它推送过时：1.4 只比发行版本（旧于后端只警告），变体按 `worker-image/<引擎>/1.4.9-<变体>` 去找，新后端没有这个键，以退出码 2 结束、不写记录。有人用 1.4 推送过时（1.4 对新于自己的后端只警告，照常写 `worker-image/` 映射并在同一族里注册修订）：1.4 能解析到映射并写下 run，这个 run 的记录格式版本读作 0，由后端的闸以 error 变体结束；1.4 注册的修订不在任何对应关系记录里，1.5 的清理按孤儿回收（均为读 code 推演，资源检查是否通过没有核到） |
| 1.4 的前台云端执行（`run --backend cloud`，1.5 已删去这个入口）写下的 run | 上「与别的写方的先后」里「run 的终态以第一笔使它成为终态的写为准」约束的是按这一版的写条件写的各方；1.4 的前台云端执行自己建记录、在进程内推进，写条件只查 run 存在，不带写入序号与 run 未结束的条件。1.5 的后端碰到这样的 run 只有两种情形：部署方带旗标尝试原地更新 1.4 部署的后端的那段时间（上「1.5 的 `deploy` 对 1.4 部署的后端」一行），1.5 的代码处理到仍在执行的这种 run；有人用 1.4 的前台云端执行对用新前缀另建的 1.5 后端执行，这本就不受支持（同上「1.4 的命令行工具对用新前缀另建的 1.5 后端提交」一行）。这时 1.5 的后端带到它就以 error 变体结束它，之后旧进程仍可能改写它的 job 与 run 的状态（读 1.4.9 的 code 推演）。属不做兼容之内，产品不另做处理：升级须知写带旗标原地更新之前先确认没有这样的 run 在执行 |
| 1.4 留在本机的 run | `list-runs` 列出，版本「未知」、标「记录格式 0」，状态、时刻与 job 计数从公共部分读出；`status`、`explain`、`status --wait` 以退出码 2 结束；`settle-runs` 跳过（`other_version`） |
| 1.4 留在本机、没结束的 run | 1.4 不持生命期锁、没有 `settle-runs`，产品判断不了它的进程还在不在；确认没有 1.4 的进程在执行之后手工移走目录（报告与判定明细一并删去，移走之前 `index.html` 仍可打开） |
| 1.4 的命令行工具读 1.5 的记录 | 1.4 不比对格式，可能读错：`status` 显示 running，`status --wait` 会接着执行余下的 job（本机已执行验证），接力读 1.5 写的运行定义时旧反序列化丢掉 `target` 与 `device_request`、把设备 job 当桌面 job 派发；1.4 的 `status` / `explain` 读 1.5 的事件时忽略 `scope_done.status`，执行前失败、只有 scope 级 error 而没有 scenario 判定的 job 会被判为 PASSED（事件序列里带 `session_opened` / `session_closed` 时旧解析直接报错、不会静默误判，[0024](./0024-worker-core-protocol.md)「事件的读法」一段）。1.4 的读端无法追加检查，所以**同一报告目录混用 1.4 与 1.5 的命令行工具读写列为不受支持的组合** |

CHANGELOG 1.5 节的「升级须知」写下列条目，只写 1.4 到 1.5 之间看得见的变化，1.5 开发期内部的改动不写：
1. 1.5 的命令行工具不能操作由 1.4 部署的云端后端：所有云端命令都以退出码 2 结束，说明读不到这个后端记下的数据版本。
2. 1.4 部署的后端不提供原地升级到 1.5：用新的前缀部署 1.5 的后端；旧前缀的后端用 1.4 的 gherkai 拆除，表、桶与镜像仓库按用户文档「拆除与清理」一节手工删除。
3. 不要用 1.4 的 gherkai 对 1.5 的后端执行任何命令：1.4 不比对数据版本，显示与推送都可能不对，用它推送过变体之后提交的 run 会被后端结束。
4. 带 `--allow-data-version-change` 原地更新 1.4 部署的后端之前，先确认没有 1.4 的 `gherkai run --backend cloud` 在执行：更新期间 1.5 的后端可能结束这样的 run，之后 1.4 的进程仍可能改写它的记录。
5. 1.4 留在本机报告目录里的 run：1.5 的 `list-runs` 照常列出；`status`、`explain`、`status --wait` 以退出码 2 结束；`settle-runs` 跳过；还没结束的，确认没有 1.4 的 gherkai 进程在执行之后可以手工移走它的目录，移走之前目录里的 `index.html` 可以打开。
6. 同一个报告目录不要混用 1.4 与 1.5 的命令行工具读写。
7. 自定义的 worker 变体要用 1.5 的基础镜像重新构建，再用 1.5 的 `push-worker` 推送；ECR 里的 tag 就是变体名，不再带版本；`push-worker` 拒绝没有 worker 协议版本标注或能力标注的镜像（不是以 1.5 起的基础镜像为 FROM 构建的）。
8. `deploy list-workers --json` 删去顶层的 `version`；`variants[].tag` 的值是变体名；新增 `variants[]` 每项的 `worker_protocol_version` 与 `capabilities`，以及顶层的 `backend_worker_protocol_version`。`doctor`（含 `--json`）不再有 `backend.version` 一行，新增必修行 `backend.data_versions`。
9. 云端命令不再比较本机与后端的发行版本：1.4 的「本机新于后端即拒绝、旧于后端只警告」与附带的 uvx 命令都去掉；能不能一起使用由数据版本判断，不同时以退出码 2 结束，说明陈述两边的值。本机 worker 与命令行工具不一致、变体缺失时的说明同样改为陈述事实。
10. 降到 1.5 之前的发行版本部署时，执行的是没有数据版本检查的旧代码。

**操作规则：升级次序**（不是 Prefect 那句「先升 server」的直译：后端由部署方 CLI 的 `[deploy-aws]` extra 部署，被 `==` 钉在部署方 CLI 的发行版本上）：
- 数据版本没变时，各成员何时、按什么次序升级命令行工具都可以，不要求与后端同一发行版本；部署方 `gherkai deploy` 照常同步 `base` 并按新模板重派生既有变体（[0038](./0038-worker-image-delivery.md)「`gherkai deploy` 的 worker 镜像四步」）。
- 有数据版本要变的那一版按迁移口径的例外办（下「后端形态变更的迁移口径」末条「与数据版本的关系」）：升级须知写明影响与做法；`deploy` 默认不继续的条件见上「`deploy` 入口的检查」；协议版本变了时，记录里协议版本与后端不同的自定义变体在部署之后用新的基础镜像重建、用新的命令行工具推送：推送要求命令行工具、镜像与后端三者的协议版本相同，部署之前推不进（镜像构建归测试开发、推送归部署方，[0040](./0040-consumer-role-model-and-terminology.md) 决策 4；各 variant 在升级前后能不能用见 0038「与版本升级的交互」）。
- 比不上时怎样解决写在用户文档 `cloud-backend.md`「版本与升级」一节。

**后端形态变更的迁移口径**（长期规则；适用于一切变更使用方已部署的后端的数据形态的版本：表的键与索引、item 的属性形态、SSM 参数族的结构等，凡要对已有数据或已有资源做变换、新版本才能正确工作的变更）：
- **默认：先设计在线迁移**。使用方按上面的升级次序照常升级，升级期间不需要暂停提交与执行。迁移的中间形态由版本给出：写端先兼容新旧两种形态，读者在新形态就绪、存量数据都已就位之后才切换，旧形态在不再有依赖它的读者和写者之后才删除；每一步的设计都要写明并发写者在这一步成立的论证。
- **依据**：在组织里使用时，同一后端同时有多个写者（各成员的 CLI、云端推进器），没有谁能保证升级期间只有一个写者，也没有谁能让整个组织在部署时停用，并发写者是前提而不是例外。要求暂停的升级把协调成本加在使用方身上：通知全部成员、等在途 run 收尾、确认这段时间没有人提交，这份成本随使用方的规模增长、每个使用方各付一次；在线迁移的设计成本只由项目付一次。
- **例外：需要停服或暂停使用才能完成的升级**，只在两种情形下考虑：①在线迁移实在没有好办法——底层服务的约束使在线方案保证不了正确性，或只能以明显的设计异味换取（如为过渡期在产品里长期保留双写、双读的分支）；②投入产出比实在不足——投入（设计与验证的时间、过渡期的运行成本、方案带进设计的异味）明显超过它为使用方省下的协调成本。
- **例外的要求**：该版 CHANGELOG 的「升级须知」把这项升级放在最前，写明影响（哪些部署受影响、暂停期间哪些命令不可用、不照做的后果）与做法（暂停、迁移、恢复的步骤，或另建后端等替代做法）；对应的 ADR 写明三项：为何在线做不到或不值得、在线方案的轮廓（重议时可直接展开）、何时重议（例外的前提在什么条件下不再成立）。
- **与数据版本的关系**：同一个值之内按上「加号的纪律」所做的加法，新旧读写方可以并存而结果不变，正是默认一条里「写端先兼容新旧两种形态」那一步要的形态。值相同才兼容，所以任何一次加号都使持旧值的一方被明确拒绝：在线迁移里删去旧形态的那一版要给接口版本加号，它会把所有持旧值的命令行工具挡在外面，包括过渡期里已经只用新形态的版本，这一版按例外处理，写进该版升级须知的最前；别的加号同样是要协调的升级（记录格式版本加号：持旧值的命令行工具不能再向新后端提交，升级之前的 run 新版本看不了细节；协议版本加号：持旧值的命令行工具不能再向新后端提交与推送变体（只是协议版本变了、另外两个号都没变时也是：云端提交要求命令行工具的三个数据版本都与后端相同，推送要求命令行工具、镜像与后端的协议版本相同，上「各入口比什么」），记录里协议版本与后端不同的自定义变体要用新的基础镜像重建、用新的命令行工具推送；读到未结束的 run 或数不出时 `deploy` 默认不继续），按同一条要求写进升级须知。

## 决策 8：CI 发布链与占名

- **占名（先于一切）**：PyPI **七名** = 五个真发行（`gherkai` / `gherkai-runtime` / `gherkai-core` / `gherkai-worker-novaact` / `gherkai-deploy-aws`）+ 两个防混淆占位（`gherkai-cli` / `gherkai-worker-midscene`），各真传一版 `0.0.0` 占位 sdist（README 指向 repo）——**PyPI 的 pending publisher 不占名**（官方明文：他人先注册即失效），必须真传。npm：注册 `gherkai` 用户/组织独占 `@gherkai` scope（原生命名空间，不需逐名防御）+ 发 `@gherkai/worker-midscene@0.0.0` 占位；可选占非 scoped `gherkai`（品牌保护，防 `npx gherkai` 跑出别人的包）。PyPI PEP 541 与 npm 争议政策都只针对无意图占坑，带真实项目指向即可。
- **包 metadata 随发行重组一并落**：各包带 license 文件 + `[project.urls]`（含 Changelog）——PyPI 页面的信任面与导航面，属发行物、不属 CI。
- **tag 触发全链**（GitHub Actions，`v*`），**前置、顺序与失败语义**：前置 = checkout 必 `fetch-depth: 0`（**`fetch-tags: true` 不是替代品**：Dunamai 对浅仓库直接拒算——真跑报 "This is a shallow repository, so Dunamai may not produce the correct version"，`--depth 1` 后 `git fetch --tags` 让 tag 可见了照样同一个错，与 tag 可见性无关）；随后 **gate：tag 形态 `vX.Y.Z` + 断言算出的版本 == 触发 tag** 再往下走（[0045](./0045-documentation-layering-and-placement.md) 决策五另加一道 gate：本 tag 在 `CHANGELOG.md` 必须有非空节）。同在构建之前还有一道检查，守已发行的数据版本基线、样本与登记没有被改过，规则见决策 7「加号的纪律」护栏的「簿记」一项；理由：已发行的基线是同一个值之下后续加法的判据。**发布链只认 `vX.Y.Z`**：预发行 tag（`v1.4.0rc1`）是合法 PEP 440 却不是合法 semver（npm 要 `1.4.0-rc.1`），gate 第一步拦掉——放进来就是 PyPI 发成功、npm 挂在 `npm version` 上的半发布态；也顺带挡住演练 tag 误 push。日常 CI 另做 **gate 演练**（干净 checkout 打本地 tag `v99.0.0` → build → 校版本==tag），使「干净 tag 也带本地段」这类回归不必等到发布日才炸。① `uv build --all-packages` → `astral-sh/attest-action` 生成 PEP 740 attestation（**`uv publish` 自身不生成**，只上传已有的 `*.publish.attestation`；漏这步 = 静默发无证物件）→ `uv publish`（PyPI trusted publisher，OIDC 免密）；② npm 发布 build job 定稿的 tarball：`npm publish <tarball> --access public`，发布 job 内不重新构建（tarball 的产出见下「发布前镜像 gate」条；打包前的 **`npm ci && npm run build` 不可省**：`dist/` 不入库、package.json 无 prepack 钩子，漏 build 会打出空 `dist/` 的包、bin 直接失效，这一回归在镜像 gate 的冒烟上即可暴露）。npm 侧同样走 **trusted publishing**（包在 npmjs.com 登记本仓库 + `release.yml`，OIDC 换授权、provenance 自动附带、零 secret；runner 上需 npm ≥ 11.5.1，Node 22 自带 10.x 故多一步 `npm i -g npm@^11.5.1`）；③ 基础镜像 `docker/build-push-action`（linux/amd64，两态 Dockerfile 的 index 态：`--build-arg WORKER_VERSION=<X.Y.Z>` 从 PyPI/npm 装已发行的 worker 包，另以构建参数传入 worker 协议版本（取自 core 的常量）与能力对象，写成两个镜像标注，见决策 5）→ GHCR（`GITHUB_TOKEN`；首发 package 的可见性**实测随公开仓库为 public**、可匿名 pull——GitHub 文档写「默认 private」，首个 release 后核对一次即可，若为 private 才需人工改，否则 0038 的「deploy 同步基础镜像」匿名 pull 不到；docker attestation 关掉——开着会把镜像变成带 unknown/unknown 附属 manifest 的 index；这是对**基础镜像这份发布物**的约束：它要被 `gherkai deploy` 拉下来、重推进使用方的 ECR，同步路径已验的是单 manifest 单架构的形态（0038 实测项 6），带构建证明的索引在重推后的 digest 一致性没有核过，所以发布物保持单 manifest。它不是 push-worker 对使用方镜像的限制：本地引用是多平台索引时步 2 按内容判平台（0038 实测项 7））——**依赖 ①②已发行且索引可见**（带重试等待），且该 job 对已发行版本**可单独重跑**（对 `X.Y.Z` tag 幂等；**重跑旧版本时不推 `latest`**，`latest` 只跟随最新 tag），故「PyPI 已发、镜像缺失」的半发布态在索引传播、推送这类失败上有确定的修复动作；重新运行修不好的那几类回归（Dockerfile 结构、冒烟、包内容）由下条的发布前镜像 gate 挡在 ①② 之前；④ changelog 锚点 = 根 `CHANGELOG.md`（[0045](./0045-documentation-layering-and-placement.md) 决策五：各包 `[project.urls] Changelog` 指它、Release 正文由该版节 + 固定 footer 渲染）。TestPyPI 演练须配 `[[tool.uv.index]]` 的 `publish-url`，且 `uv publish --index` 要求 checkout 有 pyproject。
- **发布前镜像 gate（排在 ①② 这两个不可逆发布之前）**：PyPI 与 npm 的同一版本号都不能重发，而 ③ 的基础镜像构建排在两者之后——Dockerfile、冒烟或 worker 包内容一旦回归（如设备依赖误入 `devDependencies`，设备接缝的 import 冒烟随之失败），重新运行 ③ 用的仍是同一 commit 的同一份 Dockerfile 与同一份已发行包，只能另发新版本。故 build 与 ①② 之间设 `image-gate` job（matrix 两引擎，只构建、不推送），①② 都依赖它，任一引擎失败即不发布任何东西：两个基础镜像按 Dockerfile 的 local 态（决策 5「两态」）以 `--platform linux/amd64` 构建，final stage 的冒烟（`--capabilities` 与 midscene 设备接缝的 import）照常执行，并核对两个镜像标注与 worker 自述一致（决策 5「两个镜像标注」），所以 gate 照得出标注写错这一类回归。gate 失败时 PyPI、npm、GHCR 上都还没有这个版本。gate 单列 job、不并进 build job：两引擎并行构建、各自给出失败结果，build job 仍只负责产物定稿。
  - **gate 消费的就是将要发布的那一份产物**：novaact 装 build job 产出、① 将上传的同一个 wheel；midscene 的 tarball 同样在 build job 定稿——`npm version <X.Y.Z> --no-git-tag-version && npm ci && npm run build && npm pack`，以独立 artifact 上传（不混入 Python 产物目录，attest 与 `uv publish` 只处理 Python 产物），gate 安装它、② 发布它。打包排在 `uv build` 与产物校验之后：`npm version` 改写 `package.json`、工作树随之变脏，排在前面会让算出的 Python 版本带本地段、版本 gate 必然失败。被拒的做法是 gate 与发布各自构建一次 npm 包：两次构建各自通过，不能说明发出去的就是 gate 验过的那一份——与 build job「产物在此定稿、下游只搬不重建」是同一条理由。
  - **边界**：gate 不执行 Dockerfile 的 index 态安装分支（按版本从 PyPI / npm 安装），不验证索引可见性，也不推送 GHCR；第三方传递依赖在 gate 与 ③ 各解析一次，两态都不受 lock 约束（wheel 的依赖按元数据里的范围解析，npm 发行物不带 `package-lock.json`），不保证两次解析结果相同。gate 照得出的是 Dockerfile 结构、冒烟、包内容三类回归，恰是重新运行 ③ 修不好的那几类；索引传播与推送的失败仍在 ③ 才暴露，由单独重新运行 ③ 修复（GHCR 包可见性不会让 ③ 失败，按「tag 触发全链」条在首个 release 后人工核对）；index 态安装分支自身（一行按版本安装的命令）与两次解析之间的上游变化不在 gate 覆盖之内：前者命中时只能另发新版本，后者视上游是否修复，重新运行 ③ 或另发收紧依赖范围的新版本。
  - **日常 CI 设同一道 gate**：`ci.yml` 以日常构建的产物（打包元数据 smoke 的 wheel、midscene job 打出的 tarball）构建同样两个镜像（冒烟同样核对两个镜像标注），与 `release.yml` 共用同一份构建逻辑（`.github/scripts/image_gate.sh`，两条工作流的 `image-gate` job 都调用它）——与产物校验脚本、gate 演练同理，发布链上的 gate 不应是它第一次运行，回归要在日常提交上暴露，不留到发布日。**每次都运行、不按路径过滤**：镜像与 gate 的输入不止 `engines/` 下的 worker 源码、包配置、lock 文件与 Dockerfile，还有根 `pyproject.toml` 的 workspace 配置（决定 `uv build --all-packages` 产出哪些 wheel）、`.github/scripts/` 与 workflow 本身，过滤清单漏掉一项，这类回归就留到发布日才暴露；上游基础镜像的移动 tag 与第三方传递依赖的新版本不随任何提交出现，路径过滤看不到它们，每次都运行才能让上游变化在下一次提交上就暴露。代价是 CI 总时长多出 gate 自身的几分钟构建与上游镜像拉取（拉的是 ③ 同样拉取的两个上游镜像；日常 CI 由此多出对 Docker Hub 可用性的依赖，发布链的 ③ 本就依赖它）。
- **[0033](./0033-iac-aws-backend-and-composition-wiring.md) defer 条由此闭环**：托管 = GitHub；基础镜像去 GHCR 后 CI **不再需要 OIDC→AWS 的 ECR push**——那套 IaC/凭证方案整体不需要了。

## 工程布局（[0016](./0016-execution-architecture-core-lib-run-model.md) 布局图据此校准）

```
./
├── pyproject.toml          ← uv workspace 根：[tool.uv.workspace] members 五个 Python 包；根自身无发行物
├── core/                   ← dist gherkai-core   · import gherkai_core
├── runtime/                ← dist gherkai-runtime · import gherkai_runtime（原 gherkai/；目录改名避免 gherkai/gherkai_runtime/ 的歧义；names 含变体名校验、ecr_repo_name、BACKEND_INTERFACE_VERSION 与 DATA_VERSIONS_KEY，0038 与决策 7；数据版本模块（读取与比较，决策 7）
├── cli/                    ← dist gherkai        · import gherkai_cli · 命令 gherkai；gherkai_cli/skills/gherkai/ = 随 wheel 带的 agent skill（0043）
├── deploy_aws/             ← dist gherkai-deploy-aws · import gherkai_deploy_aws（stack.py / app.py / names.py / cli.py=Provider / workers.py + container.py = worker 镜像族命令与容器引擎口子（0038）/ lambdas/ 两个 handler 源作 asset 原料）
├── engines/
│   ├── novaact/            ← dist gherkai-worker-novaact · import gherkai_worker_novaact · console script 同名 · Dockerfile = 基础镜像（原 worker/ + lib/ 收进包）
│   └── midscene/           ← npm @gherkai/worker-midscene · Dockerfile = 基础镜像（ESM + tsc dist/，tsconfig 入库，tsx 留 dependency，resolve hook 随 dist/）
```

- 随包分发的只有各包源码目录与其 `pyproject.toml` / `package.json` 声明的内容；仓库其余目录（`features/`、`tools/`、`docs/`、`graphify-out/`、`skills/`、测试与 spike）都不进发行包（`tools/build_push_workers.py` 已随 [0038](./0038-worker-image-delivery.md) 退役；`skills/gherkai-evals/` = agent skill 评测资产，[0043](./0043-agent-skill-for-driving-gherkai.md)）。
- 一个目录 = 一个 workspace 成员 = 一个 lock（根 `uv.lock`），施工前五处各自的 `uv.lock` 已合一；`uv run gherkai …`、`uv run pytest`（根跑全部）、`uv build --package <name>`。**单 lock 要求全员依赖共解**（已实测通过）；将来某成员升版引入冲突时用 `tool.uv.conflicts` 声明或把该成员移出 workspace，不回退到多 lock。
- **contributor 体验净变好**：一次 `uv sync` 替代四处安装中的三处（midscene 仍 `npm install`）；console script 直接可用；部署与用户同一条 `uv run gherkai deploy --vpc default --prefix …`，context 坑对 contributor 也消失。代价见决策 3 末条。

## 对既有 ADR 的影响（反向链已落各 Status 头）

- **[0016](./0016-execution-architecture-core-lib-run-model.md)（Partially-superseded-by 本 ADR）**：反转「cli `--backend {local,cloud}`」节 `build_cloud_stores` 条的「cli 主依赖不含 boto3、走 `cli[aws]→core[aws]` extra」（CLI 发行包硬依赖 `gherkai-runtime[aws]`；库层 extra 保留）；「工程布局」树 `cli/` 行的「gherkai/core 作 path 依赖」→ uv workspace + build 时 `==` pin；工程布局的目录名/发行名/import 名重排；「数据模型」节 definition 行的 run 级字段枚举（已逐字段带 ADR 指针）已补 `steps_dir` → 本 ADR（扩展，属校准）。分层、窄腰、注入红线、决策 A/B/C **全部不动**。
- **[0033](./0033-iac-aws-backend-and-composition-wiring.md)（Partially-superseded-by 本 ADR 与 0038）**：本 ADR 取代的部分——`iac_aws_backend/` 独立工程 + 裸 `cdk deploy` → 包化进 `gherkai-deploy-aws`、经 `gherkai deploy`（`prefix`/`vpc_id`/`use_default_vpc`/`stop_timeout` 四个 context 旋钮升为三个 flag，能力不减，另加 SSM 取值比对）；Lambda asset 现场 copytree repo 相对路径 + 联网装 gherkin → 从已安装包取；「留待」CI 条闭环；SSM 参数族加 `version`、`vpc`、`data-versions`。镜像/task-def/ECR/权限相关的取代见 [0038](./0038-worker-image-delivery.md)。两个镜像的容器入口随 worker 包化改为 `python -m gherkai_worker_novaact` 与包 bin `gherkai-worker-midscene`（→ `dist/bin.mjs`，决策 3）；资源清单/命名契约不动；云端命令开头先比云端后端接口版本（决策 7；variant 解析那项归 0038）。
- **[0034](./0034-detached-batch-reconciler.md)（扩展、Status 不动）**：local 无状态批量运行的两个宿主（提交 CLI / 后台推进进程）各自是组合根，steps-dir 随 definition 走、worker 定位链对两者同一条、后台推进进程 cwd 改继承提交进程 CWD——沿用其「随 definition 走」的惯例，未改其任何机制。
- **[0035](./0035-local-app-testing-via-tunnel.md)（扩展、Status 不动）**：tunnel-watch 子进程曾以 `repo_root()` 作 cwd，已随定位链落地改为继承提交进程 CWD；`RunMeta.steps_dir` 沿用其 `extra_http_headers` 的「core 只搬运」惯例。
- **[0030](./0030-realtime-persistence-seam.md) 决定六**：库层 `[aws]` extra 原意完整保留，不动。
- **[0036](./0036-deterministic-capability-discovery.md)（扩展、Status 不动）**：注册表加载面扩展到使用方 `steps/` 目录，「真值单一」不变；`plan` 的 best-effort 降级契约由决策 3 的 miss 分叉显式保留。
- **[0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md)（Partially-superseded-by 本 ADR 与 0022）**：本 ADR 决策 4 再移确定性 step 的**定制面落点**——从「确定性 step 住在各引擎 worker 目录的脚手架文件里」改为「使用方项目的 `steps/` 目录，worker 启动时加载、`@deterministic` 注册机制与脚手架同一条」，worker 包内脚手架只承载内建导航这一条（那是发行包内容，改它等于 fork；曾内置的示范 step 已退役，示范进 `features/steps/` 模板），故「确定性 step 仍住脚手架文件」只对内建导航成立；「裸 `When/Then`→默认 AI；确定性=按需、QA 零代码」的核心语义与角色边界**不动**，落地机制层的转移见 [0022](./0022-bdd-runner-retired-core-parses-thin-worker.md)。
- **[0025](./0025-plan-module-feature-to-jobs.md)（扩展、Status 不动）**：feature uri 的基准从「相对 repo 根」改为「用户给出的路径规范化后原样」，`scenario_id`/`scope_id` 的拼法不变、只换前缀来源。
- **[0024](./0024-worker-core-protocol.md) / [0026](./0026-schedule-module.md)**：worker↔core 协议、`SubprocessEngine` 参数化 cmd 不动；只是 cmd 的**来源**从 `repo_root()` 变定位链。
- **[0009](./0009-maximize-aws-hard-constraint.md)**：`-aws` 后缀入名是「不用当前的命名把门关死」，**不是**对全栈 AWS 硬约束的反转——两个引擎本身绑在 AWS 服务上（Nova Act、Bedrock、AgentCore Browser），非 AWS 后端意味着引擎层也要重铺、距离很远。

## 对既有文档与 code 注释的影响

- 发行重组 / worker 交付 / deploy 三层落地时，README·子 README·CONTEXT·`docs/internals/`（原 `docs/guides/`）与 code 注释里的旧包名与旧调用示例已随各层校准。
- 唯一有再犯价值的反模式：用户可见错误文案里的旧 extra 名（`pip install core[aws]`）会教用户敲一个不存在的包，属最易漏的一类；规则与护栏见 [0039](./0039-user-facing-surfaces-no-internal-references.md)。

## 实测项（**除第 4 条末一项与第 6、7、8 条外全部已验**；残留四项：第 4 条末的 `destroy` 后同 prefix 重部署的冲突形态，待真账户；第 6 条 npm 以 tarball 发布时的 trusted publishing 与 provenance，待下一个正式 tag；第 7 条数据版本参数与版本戳在完整栈上的更新与回滚次序、各 Lambda 与事件源映射的更新先后、跨过更新的调用与各类记录由哪一份代码处理、只改映射过滤条件时有没有漏掉记录、受限角色下的云端命令，待部署之后核；第 8 条 `deploy` 对 `live` 分组计数的读量与最终一致的程度，待部署之后核。「绿≠对」——每条都依赖 mock 之外的真实行为，证据内联于各条）

1. `uv-dynamic-versioning` 在 workspace 内：三种 git 状态各算出什么版本、`=={{ version }}` 与 `uv sync`/`uv run` 的解析行为；hook 接管 dependencies 后 extras 的渲染正确。（**已验**：三项显式配置 + metadata 默认下，干净 tag → `X.Y.Z`、脏树 → `+dirty`、离 tag → `.postN.dev0+<sha>`；五个 wheel 的 `==` pin 与 extras 渲染正确、`uv sync` 解析通过；**`uv.lock` 对动态版本的 workspace 成员只记 `source = { editable = "<dir>" }`、不写版本串**，lock 不随 commit 漂移、任意 commit 上 `uv lock --check` 通过——CI 的 `uv sync --locked` 因此不会被逐提交变化的 dev 版本号打红；反例——显式 `metadata = true` 在干净 tag 上出 `+<sha>`，gate 失败。）
2. `sys.executable -m gherkai_worker_novaact` 下 EVENTS_FD `pass_fds` 继承与三通道分离真跑（**前半已验**：真管道经 `pass_fds` 收到 worker 写出的事件、中文不转义；`--match-steps` 挂起时 `pgrep -P` 无子进程，Python 与 midscene 的 `dist/bin.mjs`、全局装 bin 三种形态皆然）；`uvx`/`npx` 兜底路径的 fd 继承预演 → 定第四级存废（**已做**：uvx 穿透 fd3 + 转发 SIGTERM → novaact 保留；npx 不穿透 → midscene 第四级废弃，见决策 3 第 4 级）。
3. midscene 以**最终发布形态**（ESM dist + 运行期 `tsx/esm/api` 注册 + 随 dist 的 resolve hook）安装到 **repo 外干净目录**，变量维度 = 安装形态（全局装 / npx）× 使用方目录（无 package.json / `type=commonjs` / `type=module`）× 扩展（`.mts`/`.mjs`），验证使用方 step 能加载、裸 specifier 解析到 worker 自身同一 URL（注册进同一张表）、零注册 fail-loud 真触发——在 repo 内预演会被 repo 自己的 `node_modules` 掩盖成假绿。（**已验**：`npm pack` → `npm i -g --prefix <tmp>` 与 `npx --package <tgz>` 两形态，在无 `node_modules`/无 `package.json` 及 `type=commonjs`/`module` 的使用方目录下，`.mts`+`.mjs`（含子目录）均注册进同一张表；使用方目录另装一份副本时 hook 仍解析到运行中那一份；import 另一安装位置的 `dist/index.mjs` 触发双实例守卫退出；语法错/零注册/目录不存在三者 rc≠0 且点名文件。发布形态分支只有真跑证据，自动化测试只覆盖源码形态 bin。）
4. `gherkai deploy` 内嵌 cdk：`npx -y aws-cdk@2` 与 jsii 的 Node 版本兼容；asset 从 site-packages 复制后 Lambda 冷启动 import 正常（含 `packaging`）；SSM `version`/`vpc` 参数随 stack 事务写入、destroy 随删；VPC 取值三态（含「参数缺失 ∧ stack 已存在」的迁移情形）各一次真跑。（**无凭证下已验**：命令真调 `npx aws-cdk@2` 真合成——模板含 6 个 SSM 参数（version / vpc / worker-template×2 / subnets / security-groups）；asset 在剥掉 site-packages 的解释器里真 import 通过（抓出 `typing_extensions` 漏项）；`--synth-only` 相对路径导出、`--bootstrap` 不带 `--vpc` 直达凭证解析。**真账户已验**（独立 prefix、dev 版本）：`gherkai deploy --vpc default` 真部署成功（含四个新 SSM 参数、Lambda asset 真冷启动——推进器随后真起 task 并收敛 run），四步在 dev 版按设计跳过基础镜像同步、初始化默认指针；VPC 三态——参数存在且一致放行、`--vpc new` 不一致退 2 不动账户；两次 cloud run（单引擎 / 双引擎）passed。**追加已验**：对早于本机制的旧 stack `deploy --vpc default` 落「参数缺失 ∧ stack 存在」迁移情形退 2、不动账户；`gherkai destroy --yes` 真拆该 stack（SSM 参数随删、RETAIN 资源留待手清）。**待真账户**：`destroy` 后同 prefix 重部署的冲突形态。）
5. 完整 release 链一次真跑（TestPyPI 先行）：`fetch-depth: 0` + 版本==tag gate → attest-action → `uv publish` → npm provenance → 等索引可见后基础镜像进 GHCR，含镜像 job 对已发行版本单独重跑且不动 `latest`。（**推 tag 前已验**：两个 workflow YAML/actionlint 静态通过、gate 脚本正反例真跑、gate 演练在干净克隆通过；两态 Dockerfile 的 **local 态**在两种 builder 上真 build 通过（BuildKit 与**经典 builder** 各一台，`--platform linux/amd64`，novaact wheel / midscene tarball），`--list-deterministic` 冒烟通过（当时 worker 的清单入口；该 flag 后来并入 `--capabilities` 自述对象并删除，现行 Dockerfile 的冒烟改用 `--capabilities`，见 [0036](./0036-deterministic-capability-discovery.md) 决策 5）、包装进 site-packages / 全局 node_modules 不靠 PYTHONPATH；踩出两个真坑——① pip 不接受改名的 wheel 文件名（要保原名，故 local stage 整体 COPY context 再按名装）；② **经典 builder 会把未选中的 stage 也跑一遍**，「参数必须给」的守卫若写成硬失败会让未选中的那个先炸，故两 stage 各自容忍参数缺席、把关移到 final stage 的冒烟（漏 build-arg 在那里 fail-loud，实测无参数构建退 1）。**首个真 tag（v1.4.0，2026-09-08）已验全链**：推 tag 一次全绿——gate（tag 形态 + 版本==tag）→ `uv build --all-packages` → attest → `uv publish`（trusted publishing）五包 1.4.0 上 PyPI 且 integrity API 有 provenance → npm trusted publishing 发 `@gherkai/worker-midscene@1.4.0` 带 attestations → 等索引可见 → 两基础镜像 **index 态**从 PyPI/npm 装、推 GHCR `1.4.0` + `latest` → GitHub Release。干净缓存下 `uvx gherkai==1.4.0 --version`、`uvx --from 'gherkai[local]==1.4.0' gherkai list-engines`（novaact 命中同 venv 模块）、`npx -y @gherkai/worker-midscene@1.4.0 --list-deterministic` 全部可用。首跑前 CI 还照出两件真事：远端无任何 tag 时 `strict=true` 让 `uv sync`/`uv build` 直接失败（推 `v1.3.0` 锚点解决，锚点提交无 workflow 文件、不触发发布）；Nova worker 信号 handler 的 stderr 重入崩溃（见 [0024](./0024-worker-core-protocol.md) 终止契约）。）
6. npm 发布 build job 定稿的 tarball（决策 8 ②，`npm publish <tarball>`）时，trusted publishing 的 OIDC 授权交换照常完成、provenance 照常自动附带。（**待下一个正式 tag 发版时核对**：v1.4.x 各次正式发版都在包目录里执行 `npm publish`，第 5 条里 npm trusted publishing 发出带 attestations 的包这一证据只覆盖目录形态；改为发布定稿的 tarball 之后还没有正式发版证据，而 trusted publisher 只登记了 `release.yml`，日常 CI 换不到发布授权，这一形态只能在正式发版时验证。核对方式：①release 工作流 npm job 的日志里 publish 一步成功，并带签发 provenance、写入透明日志的提示；②npm 包页该版本带 provenance 标记（registry 侧的等价核对是 `npm view @gherkai/worker-midscene@<X.Y.Z> dist.attestations` 非空）。两半的失败形态不同：npm job 不配任何 token，OIDC 交换失败时没有可回落的授权，publish 直接报错，属显性失败；provenance 未附带时发布照样成功，只能从包页与 registry 记录看出，所以核对的重点在后一半。）
7. 数据版本参数与版本戳在完整栈上的更新次序（决策 6「数据版本参数」「版本戳」两条）：一次真实部署里版本戳参数与数据版本参数在各 Lambda、两条事件源映射与 EventBridge 规则之后相继更新；两条事件源映射晚于各自引用的 Lambda 更新（[0033](./0033-iac-aws-backend-and-composition-wiring.md) 资源清单 13）；记下两个推进 Lambda、退出观察者、两条映射与两个参数各在何时换上新值，部署期间留一笔已过旧代码的闸、跨过更新的调用，核对 STATE 的新建、使 run 成为终态的那次写与退出记录各由新旧哪一份代码处理（决策 7「三个号各管什么」里「不归任何号」与「写读次序」）；只改事件源映射过滤条件的一次更新前后各写下建 run 记录，记下哪些投递给了 kicker、更新期间有没有漏掉的（新建或更新映射可能漏掉记录，见 [0054](./0054-run-deadline-lifetime-lock-and-settling.md)「边界与已知局限」里「其它局限」）；一次注定失败、成功回滚的更新里，参数、各 Lambda 与两条映射改回的先后，以及同样跨过回滚的调用由哪一份代码处理；`destroy` 时两个参数随 stack 删除；按 [0033](./0033-iac-aws-backend-and-composition-wiring.md)「资源清单」末段编排进程角色一项里用户一侧各命令的授权（部署方与镜像交付之外的部分）、SSM 上只有 `ssm:GetParameter`（`/{prefix}backend/*`）的受限角色下，用户一侧的云端命令（`submit`、`status` 含 `--wait`、`explain`、`list-runs`、`settle-runs`、`doctor`）都能完成。（**待部署之后核**：按依赖先后更新只在只含参数资源的临时栈上实测过，事件源映射与 Lambda 的先后是按依赖推断的；回滚先后决定部署失败时被后端结束的是哪些 run，见决策 7「部署进行中」。）
8. `deploy` 在数据版本要变时对状态分组索引 `live` 分组的计数（决策 7「`deploy` 入口的检查」里「数未结束的 run」一项，索引见 [0030](./0030-realtime-persistence-seam.md) 决定六「runs 表只有一个 GSI」条）：真实的表上 `Select=COUNT` 翻页读完的读量；刚建与刚结束的 run 在计数里出现与消失的滞后（索引的读只有最终一致）。（**待部署之后核**。）
- `steps/` 定制面（决策 4）在发行版上的两条路（**已验**，v1.4.0）：**local** —— 干净机器 `uvx --from 'gherkai[local]==1.4.0'` + `npm i -g @gherkai/worker-midscene@1.4.0`，`list-deterministic --steps-dir steps` 两引擎都列出使用方的确定性 step、`plan` 给出「确定性」派发标注；**cloud** —— 使用方 step 烙进 variant 镜像（三行模板）、`--worker-variant` 提交后在 Fargate 里真按确定性 handler 判定（正例 passed、故意错的 failed），细节见 [0038](./0038-worker-image-delivery.md) 实测项 1。
- worker 镜像子系统的实测项在 [0038](./0038-worker-image-delivery.md)。

## 被拒方案（护栏，防未来重踩）

- **进程包装层的 fd 转发补丁（为救 npx 兜底）**：多一层包装 = 多一处吞 fd/吞信号的地方（ADR 0024 三通道的反面教材）；npx 实测不穿透即降级为安装指引，midscene 无第四级（证据见决策 3 第 4 级；npm 行为若变按同法重测）。
- **Homebrew tap / 单文件二进制（PyApp、PyInstaller、shiv、pex）**：受众（装 AWS 凭证与容器引擎的测试开发）能装 uv；homebrew-core 门槛不达、tap 是第二个发布面与 bottle 维护；二进制带不了双语言 worker 环境。用户需求出现再议。
- **单发行包（三 import 包一 wheel）**：省 pin 机制，但集成方无法按层引用（WebUI 只要 runtime、第三方只要 core）；pin 机制已由 dynamic-versioning hook 一处解决，单包唯一优势消失。
- **不设 `[local]` / uvx 拉起作主路径**：同 venv 直调无包装层、离线、pin 锁死，三点全优；uvx 降为兜底，fd 预演后仅 novaact 保留第四级（见决策 3 第 4 级）。
- **CLI 上保留 `[aws]`**：裸装无一画像完整可用，头条命令撞头条用法。
- **`[deploy-aws]` 命名为 `[aws]` 或 `[deploy]`**：前者说谎（裸装已能用 AWS）并把 CDK+Node 引向不需要的人；后者关 provider 门。
- **发布方独占发布完整 worker 镜像**：确定性 step 是使用方地盘，worker 是 user-code image。
- **ECR Public / Docker Hub 作基础镜像 registry**：运行时拉的是私有 ECR 定制镜像，ECR Public 的免流量/免认证优势碰不到；Docker Hub 匿名限额是负项。
- **IaC 单独 repo / 模板下载（Metaflow 式）**：第二 release train、第二版本号、硬编码值 bug 类（Dagster+ 模板硬编码 URL 致 EU 部署断）。
- **clone repo + 裸 `cdk deploy` 作正式部署形态**：相对路径、context 坑外露、wheel 用户不可达。
- **`--vpc` 只留 `default|new` 两个取值**：静默砍掉 [0033](./0033-iac-aws-backend-and-composition-wiring.md) 已定的 `vpc_id` 复用取值，且以该取值部署过的环境再 deploy 会合成危险变更集；三个取值齐全 + SSM 记录的三态比对。
- **`--vpc` 隐式默认**：漏 context 合成建新 VPC 的真踩坑，必给。
- **版本戳 / vpc 取值由命令事后 `put_parameter`**：部署回滚会留错值；改 stack 资源与事务同生死。
- **把包目录里的 contributor README 直接当 PyPI/npm 长描述**：v1.4.0 首发这么上去了；改为 README / DEVELOPMENT 分层——决策、理由与护栏见 [0039](./0039-user-facing-surfaces-no-internal-references.md)。
- **靠 `uv-dynamic-versioning` 默认配置区分 dev/release**：默认 `dirty=false`，tag commit 上的脏构建与正式版逐字节同名，纯发行版本判据失效；故 style/strict/dirty 三项显式钉死。**反向也被拒——显式 `metadata = true`**：干净 tag commit 也带 `+<sha>`，发布 gate 必败、PyPI 拒收（真跑证实）；metadata 用默认。
- **使用方 steps 允许 `.ts`/`.js`**：模块体系取决于使用方目录的 `package.json#type`，无 package.json 的裸目录落 CJS 域、tsx ESM register 不生效、`import` 直接 SyntaxError；收敛到 `.mts`/`.mjs`。
- **midscene 使用方 steps 靠 Node 默认解析找 `@gherkai/worker-midscene`**：全局装/npx 形态下必 `ERR_MODULE_NOT_FOUND`；resolve hook（或退到依赖注入）。
- **steps 文件加载失败静默跳过**：把确定性 step 静默换成 AI catch-all、run 可能假通过；fail-loud。
- **`--no-report` 方式的产物落系统临时目录（清或不清）**：两种都是「还是生成了、只是换个地方」，与 `--no-report` 的字面含义相悖；改为不注入落点 + 令 worker 不生成/不上报（能关的关、Nova SDK 关不掉的留在其自身临时目录）。RunResult 因无 reportRef 也不再打印任何产物路径。
- **feature uri 继续相对某个「根」**：分发后没有 repo 根，任何根都随安装位置/CWD 漂移；用用户给出的路径原样。
- **手写 `==` 版本 pin / release 脚本改写 pyproject**：双真源、易漂移；hook 渲染一处解决。
- **npm 逐名防御占位**：scope 是原生命名空间；空壳可被争议转让。
- **兼容矩阵**：能不能一起工作由三个数据版本的比对判断（决策 7）；无同类工具在此阶段维护矩阵。
- **处置方不比 run 记录格式版本，格式不同只当作期限读不出、处置照常**：它的前提是运行态跨格式稳定，而运行态除公共部分之外归记录格式版本；本版本解析不了时等待中的 `status --wait` 会一直等下去，解析得了时结束写按本版本的模型改写对方的记录（下「跨格式时用本格式的读写方读写别的格式的运行态」，决策 7「查看与处置的出口」）。
- **发行版本参与兼容判断**（CLI 新于后端拒绝、旧于后端警告、缺版本戳时只警告并为带设备目标或会话预热的 run 设例外、非纯发行版本跳过比较，以及附属的 `--allow-version-skew` 放行口）：它用「哪一方更新」代替「读不读得懂」，两个方向都会判错：格式没变时拦错，格式变了时放错；按发行版本挑镜像又把协议问题与变体问题搅在一起；放行口则让持别的格式的 CLI 照常写记录，后果不可知且静默。改为三个数据版本只比是否相等（决策 7「总则」）。
- **deploy 取不到自身发行版本时拒绝部署**：版本戳只作事实，记下「未知」是事实，拿别的包的版本代替才是错的事实；拒绝就是因发行版本拒绝操作（决策 6「版本戳」）。
- **只给记录与协议定版本，后端形态靠发行版本比对接住**：发行版本不参与比较时，新 CLI 依赖旧后端所没有的资源就没有东西接住它；所以另设云端后端接口版本。
- **任何形态变化都加号**：「格式不同但兼容」这一情形就不存在了，升级窗口只剩一个点；改为七问判定（决策 7「加号的纪律」）。
- **读的一方认当前与上一个格式版本**：每次加号都要带上一版的读法，测试矩阵翻倍，而且延伸不到 1.4。
- **三个值各存一个参数**：读一次变成读三次，三者不在同一次资源更新里改变，可能读到半新半旧的组合。
- **数据版本由 deploy 在 cdk 之后写入**：回滚时它不跟着回滚，留下与代码不符的值；改为 stack 资源（决策 6「数据版本参数」）。
- **后端各 Lambda 读这个参数作为自己的版本**：同一事实有了两个来源（代码里的常量与参数），部署窗口里两者不同时按参数判断就是错的。
- **数据版本参数的读方忽略不认识的键**：以后加一个维度时，旧读方照判三项相同，静默放行；改为键集恰为三个。
- **固定的那句话带上「发行版本不同不影响」**：不需要的承诺。
- **写记录之前紧挨着再读一次参数；长时间命令每次写之前再比**：记录格式与协议的保证在后端的闸，再读只缩短窗口，关不上 Lambda 到参数之间那一段；接口版本的窗口来自资源先于参数更新，命令一侧再读也关不上；多一个读取时机就多一套要维护的规则。
- **deploy 先建变更集、检查之后再执行**：两位部署方同时部署不同版本是要协调的操作，产品不为它另设协议。
- **跨格式时用本格式的读写方读写别的格式的运行态**：本格式的读方读别的格式可能读错；写方并回不认识的键会在记录里留下新旧两套状态，写出它的那个版本读到的仍是旧状态。公共部分使跨格式的读写按约定成立（决策 7「跨版本不变的约定」）。
- **把在途 run 依赖的后端资源（表名与键、桶、任务定义族、容器名等）都列进跨版本不变的约定**：冻结过多。
- **数据版本不同时连各 job 的结果也保证准确**（不比数据版本的各方所依赖的内部约定都列进跨版本不变的约定，例如怎样认出一条退出记录、退出观察者从 task 上认出 run 与 scope 的环境变量名、停止原因里的超时哨兵串）：这类 run 多出自部署方带旗标继续、或提交与部署几乎同时；要连 job 的结果也保证，这些内部约定都得永远不改，被举出一例补一例也列不全。产品对这类 run 做到的范围见决策 7「后端遇到别的格式写出的 run」里「保证的范围」。
- **把别的版本会用到的每一项细节都归给某个号或列为永远不改，并用登记与测试守住**：等于把工程里的所有细节都版本化，清单随被举出的反例一项项增长，也列不全。只给会随产品迭代而变、别的一方会读错的部分定版本：按边界定三个号的范围（决策 7「三个号各管什么」），改动的那一刻用一个判据判断要不要加号（决策 7「加号的纪律」开头）（owner 认定）。
- **在途 run 依赖的后端资源保留不住时，给 run 记录格式版本加号，好让 deploy 的计数与拦截生效**：一次没有改记录格式的升级会让全部历史 run 在新版本下看不了细节，还多出一条规则；改为任何一个数据版本要变、且有未结束的 run 或数不出时默认不继续。
- **云端提交只比镜像与后端、不比命令行工具自己的 worker 协议版本**：收发 job 的虽是后端与镜像，云端提交时解读所选镜像能力对象的却是命令行工具，能力对象的格式归 worker 协议版本，协议版本与之不同的工具会读错（例如新协议给 `targets` 加了取值），能力判断随之出错；所以命令行工具自己的值也比（决策 7「各入口比什么」）。只拿命令行工具的值代替镜像的值同样不取：自定义变体用别的基础镜像构建时两者可以不同。
- **run 的记录里另记写下它的命令行工具的云端后端接口版本，后端的闸三个值都比**（让只有接口版本与后端不同的 run 也由后端结束；owner 认定不做）：这样的 run 的记录格式与 worker 协议都没有变，后端读得懂、做得了，一律结束会把本来能做完的 run 也结束掉；入口已有一道，`deploy` 在接口版本要变时默认不继续，部署方带旗标明确选择继续才会留下这样的 run（决策 7「`deploy` 入口的检查」）。所以云端后端接口版本只在命令行工具与部署命令的入口比，后端照常推进这样的 run，做不完的按已有的失败与到期规则结束（决策 7 总则 3、「部署进行中」首条）。
- **推送与部署同步时执行镜像、问它的能力自述取协议版本与能力**：理由与备选的实测依据见 [0038](./0038-worker-image-delivery.md) 被拒方案同名条。
- **推送时协议版本不同不拦、只打印提醒**：理由见 [0038](./0038-worker-image-delivery.md) 被拒方案同名条；推送比哪几项见决策 7「各入口比什么」。
- **`deploy` 的输出按情形预告部署之后的结果**（记录格式版本或协议版本要变时说后端不再继续执行读到的未结束 run、部署进行期间提交的 run 可能被结束；协议版本要变时说哪些提交会被拒、本次将同步 `base`；接口版本要变时说旧值的命令可能出错）：每一句都是这次命令没有查证的推断，各有不符的情形。计数不读各 run 的数据版本，读到的 run 可能与部署之后的后端数据版本相同、照常执行完（先降级再升回之后留下的就是）；`deploy --diff` 输出同样的内容却不做同步；`base` 是哪一份镜像由映射的最后一次写决定。输出只留读到的值、本次自己的值与有没有改动账户，规则由用户文档陈述（owner 认定：比不上时只陈述事实与状态，不按情形替使用者判断；默认不继续时点出旗标的那句结尾不随情形变化）。
- **云端提交时不核对镜像的能力，由 worker 建会话之前自检**：理由见 [0038](./0038-worker-image-delivery.md) 被拒方案同名条。
- **worker 协议版本加号时 run 记录格式版本同时加号，后端只看后者**：省一个字段，但把两条边界绑在一起，协议一变旧 run 就不能用新 CLI 查看。
- **证据并进 worker 协议版本判断（explain 按 run 记下的协议版本决定解不解读证据）**：证据文件自带格式号、逐个文件自证；按 run 的协议版本判断，会在协议加号而证据格式没变时让 explain 白白不解读旧 run 的证据。
- **运行态的状态取值留给以后的格式扩展**（只许加表示已结束的取值，读到不认识的按已结束读、原样显示，云端落进一个兜底的分组）：清单、计数、流过滤与索引都按状态取值与分组工作，取值集合一变就要每个版本都认得新值，兜底分组又让云端与本机列出的范围各有一套规则；这七个取值自有运行态以来没有变过，要表达新的结束原因用别的字段（决策 7「运行态的公共部分」）。
- **deploy 交互式确认**：非交互的调用方（agent、CI）没有终端；改用与 `--allow-vpc-change` 同一形态的旗标。
- **deploy 数不出未结束的 run 时放行**：放过的恰恰是最危险的那一次。
- **deploy 的计数改为强一致的逐条读**（好让读到 0 即证明没有未结束的 run）：runs 表不许全表扫描（`RETAIN`、无 TTL、随历史增长），也没有别的强一致的列法；索引上读到 0 时漏掉的是检查之前刚写下、还没进索引的这一类 run，它与检查之后才提交的 run 同类，由部署之后的后端按它的规则处理（决策 7「`deploy` 入口的检查」「部署进行中」）。
- **deploy 保留读旧接口版本的表的读法**：等于新版本保留读旧版本的分支。
- **提交记录头的顶层属性集随格式版本固定，由测试绑定**：同一个值之内也要能加键；改为基线加登记（决策 7「加号的纪律」的护栏）。
- **只有 deploy 读的部署标记也归入接口版本**：改了它会挡住从来不读它的命令。
- **期限进入跨版本不变的约定**：别的格式写出的 run 第一次被带到就结束或清扫，期限只对同一格式的 run 读；定为不变只会白白冻结它。
- **已发行的基线靠基线文件里由发布流程写下的发行字段冻结**：发行版本的唯一真源是 git tag，另记一个字段是同一事实记两处，还要发布流程回写仓库；冻结点由 git tag 推出（决策 7「加号的纪律」护栏的「簿记」一项）。
- **发布链对照每一个已发行 tag，以支持给较旧的发行线补发**：只比双方都有的同名文件时，较旧的发行线后来补进的同号登记在较新的线发行时不被回放；要支持给较旧的发行线补发，得先定同号的基线、样本与登记在几条发行线之间怎样对照。产品只有一条发行线，只支持按版本号递增发行，版本号不递增的发行在入口被拒（owner 2026-11-25 认定）。
- **基础镜像只在不可逆发布之后第一次构建**：Dockerfile、冒烟与包内容的回归只能另发新版本修复，「半发布态可重新运行修复」随之落空；改为发布前的 local 态镜像 gate（决策 8）。同条的两个变体也被拒：gate 与发布各构建一次 npm 包（验过的不一定是发出去的）；日常 CI 的镜像 gate 按路径过滤（输入不止 `engines/`，清单漏一项即留到发布日才暴露；上游基础镜像与传递依赖的变化，路径过滤看不到）。
- **Lambda asset / 基础镜像只从 PyPI 拉同版本**：dev 版不在 PyPI，contributor 即断；asset 从已安装包复制、基础镜像 Dockerfile 留本地态。
- **boto3 驱动 CloudFormation 去 Node**：defer 非拒（见决策 6）。
- worker 镜像子系统的被拒方案（构建所有权、tag 命名、不可变 tag、family 取最新、强制 `--platform`、模板来源、指针重置、revision 删除时机等）在 [0038](./0038-worker-image-delivery.md)。

## 重议闸门

- 出现非 AWS 后端的真实需求 → 命令 `gherkai deploy` 的 provider 发现面已留，届时新增 `gherkai-deploy-<provider>` 包，本 ADR 不需改。
- 本地 browser 后端落地 → worker `--capabilities` 自述入口 + preflight/plan 消费（运行配置有效性 = engine × browser 后端 × backend 走 worker 自述、非安装期 extras，[0036](./0036-deterministic-capability-discovery.md) 形态延伸；不回到安装期 extras 表达能力矩阵）。
- midscene resolve hook 实测不稳 → 退到依赖注入形态（step 文件导出 `register(deterministic)`），Python 侧对称跟随以保两侧写法一致；Node 基线升到 ≥22.15 后可改用同步的 `module.registerHooks()`（Node 官方已在劝退异步 hook）。
- 去 Node 部署路线（CI 预合成模板 + boto3 驱动 CloudFormation）→ 有需求再评估参数化成本。
- 发布链守已发行基线的那道检查，在实际的发版方式之内被举出守不住的情形 → 删去这道检查，「已发行的基线、样本与登记不许改」只作为做法、靠复核（owner 2026-11-25 认定）；要给较旧的发行线补发 → 先定同号的基线、样本与登记在几条发行线之间怎样对照。
- 日常 CI 的镜像 gate 时长成为瓶颈 → 才考虑按路径过滤，且过滤清单必须覆盖决策 8「发布前镜像 gate」条列出的全部输入（`engines/` 下的 worker 源码、包配置、lock 文件与 Dockerfile，根 `pyproject.toml` 的 workspace 配置，`.github/scripts/`，workflow 本身），并接受上游基础镜像与传递依赖的变化推迟到下一次命中过滤的提交或发布时才暴露。
