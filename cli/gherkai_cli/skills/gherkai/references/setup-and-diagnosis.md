# 环境就位与排障

本文管「装、查、卡住了怎么办」。每条命令的全部选项以 `gherkai <命令> --help` 为准；报错都带「怎么办」，先照它说的做。

## 1 装什么

| 角色 | 装法 | 得到 |
|---|---|---|
| 只提交云端 run（不在本机跑） | `uv tool install gherkai` | 只要 CLI 本体，两个 worker 都不用装（worker 跑在云端）；代价是 `plan` 会打「标注降级」 |
| 本机跑 Nova Act（推荐起点） | `uv tool install 'gherkai[local]'` | CLI 与 Nova worker 在同一环境 |
| 本机跑 Midscene | `uv tool install gherkai` + `npm i -g @gherkai/worker-midscene`（Node ≥ 22） | CLI + Midscene worker |
| 本机两引擎都跑 | `uv tool install 'gherkai[local]'` + `npm i -g @gherkai/worker-midscene`（Node ≥ 22） | CLI + 两个 worker |
| 部署方 | `uv tool install 'gherkai[deploy-aws]'`（另需 Node ≥ 22、docker） | 多出 `gherkai deploy` / `gherkai destroy` |

升级：`uv tool upgrade gherkai`（安装时带的 extras 沿用）；Midscene worker 另 `npm i -g @gherkai/worker-midscene@<CLI 版本>`。worker 与 CLI 版本同号锁定。

## 2 CLI 怎么找 worker

- **Nova Act**：① 环境变量 `GHERKAI_WORKER_NOVAACT_CMD`（+ 可选 `GHERKAI_WORKER_NOVAACT_CWD`）显式指定 → ② 与 CLI 同一个 Python 环境 → ③ PATH 上的 `gherkai-worker-novaact` → ④ 三级都没有、CLI 是正式发行版、机器上有 uvx 时临时拉起同版本 worker。四级都没命中：local 档的 `run` / `submit` 与 `list-deterministic` 退 2 并打印装法（`submit` 也在提交前就拒）；`--backend cloud` 的 `run` / `submit` 不看本机 worker（它跑在云端容器里）；`plan` 不拦，只少了那个引擎的派发标注。
- **Midscene**：PATH 上的 `gherkai-worker-midscene`（`npm i -g` 的结果），或环境变量 `GHERKAI_WORKER_MIDSCENE_CMD`（+ 可选 `GHERKAI_WORKER_MIDSCENE_CWD`）显式覆写。**必须真装**，没有临时拉起的兜底。

`gherkai list-engines` 打出每个引擎的探测结果与来源，缺的那个原地给安装命令；`--json` 机读（`engine` / `available` / `cmd` / `source` / `hint`）。

## 3 `gherkai doctor` 怎么读

只读自检，不建会话、不调模型、不花钱。每行一个检查项：`✓` 过（「未查」的项也算过）、`✗` 必修项没过、`-` 可选能力缺失（如另一个引擎没装）。名字按段分组：

| 段 | 查什么 | 何时查 |
|---|---|---|
| `cli.*` | CLI 版本与 Python | 总是 |
| `engines.*` | 每个引擎的 worker 能否定位、至少一个可用 | 总是 |
| `steps.*` | steps 目录是否存在、每个引擎加载 steps 是否成功、几条 | 总是（`--steps-dir` 可改目录） |
| `aws.*` | region、凭证身份 | 给了 `--backend cloud` 或 `--prefix` |
| `backend.*` | 后端版本与 CLI 比对、资源齐全、报告前缀一致、默认 variant 与逐引擎镜像能否解析 | 同上 |
| `provider.*` | Node、cdk、容器引擎（部署方工具链） | 装了部署 extra 时 |

退出码：全过退 0；有**必修项**失败退 2（非必修项失败只标出不影响退出码）。`--json` 每项给 `section` / `name` / `ok` / `required` / `detail`，脚本按 `required && !ok` 找阻塞项。

## 4 凭证与 region

- 走本机 AWS 默认凭证链：profile / 环境变量 / 实例角色皆可，`--profile` 或 `AWS_PROFILE` 选 profile。**不需要任何 API key**。
- **region 必须有出处**，按序解析：`--region` > `AWS_REGION` > `AWS_DEFAULT_REGION` > `--profile`（或 `AWS_PROFILE`）指的那个 profile 配置里的 region。四处都没有才报错；缺了不会替你兜一个 region。
- 该 region 下账号要能用：Nova Act 引擎 = Nova Act 服务与模型 nova-act-latest；Midscene 引擎 = Bedrock 模型 qwen.qwen3-vl-235b-a22b；两者都要 AgentCore Browser。`AccessDenied` / 模型不可用多半是 region 未开通模型或凭证缺这些权限。
- 本机 `run` / `submit` 也要 AWS 凭证（浏览器与模型在云端）；只有 `plan` / `list-engines` / `list-deterministic` / `doctor`（不带 cloud 参数）纯本地。

## 5 隧道（`--expose-local`）前置

要两样，缺哪样都是 `run` / `submit --expose-local` 在起隧道时失败，且 `doctor` 两样都不查（它不碰隧道）：

- **ngrok 可执行文件**装好且在 PATH 上（`ngrok version` 能跑；下载 https://ngrok.com/download ）。没装的报错点名找不到 ngrok 可执行文件。
- **ngrok 账号的 authtoken**（免费账号即够）：`ngrok config add-authtoken <token>` 写进 ngrok 自己的配置文件，或环境变量 `NGROK_AUTHTOKEN`，任一处即可。排障别只看环境变量在不在——配置文件里配过就够。

隧道由本机进程持有：`run` 是 CLI 进程，`submit` 是后台进程，本机须保持开机联网到 run 终态。

## 6 版本不一致（`--backend cloud` 退 2）

部署时后端记下自己的版本，每条 cloud 命令动资源前先比对：

- **CLI 比后端新 → 拒绝，退 2，没有强行放行的开关。** 出路：部署方 `gherkai deploy` 把后端升上来；或临时用与后端同版本的 CLI：`uvx --from 'gherkai==<后端版本>' gherkai …`，不动本机安装。
- CLI 比后端旧 → 只警告不拦，`uv tool upgrade gherkai` 跟上。
- 升级顺序：部署方先升 CLI、立刻 `gherkai deploy`，其他人再升自己的 CLI；中间窗口里提交被拒是预期。

## 7 症状 → 处置

| 你看到 | 多半是 | 怎么办 |
|---|---|---|
| 退 2，说某引擎 worker 未找到 | 没装或不在 PATH | 照打印的装法装；或设 `GHERKAI_WORKER_<ENGINE>_CMD` |
| `engine_error`，起 worker 失败 | worker 版本与 CLI 不一致 | 重装到同版本（第 1 节） |
| 启动即抱怨 region 未设 | `--region` / `AWS_REGION` / `AWS_DEFAULT_REGION` / profile 配置四处都没 region | 任选一处设上（第 4 节）；缺了不会自动兜一个 region |
| `AccessDenied` / 模型不可用 | region 未开通模型，或凭证缺 Bedrock / AgentCore 权限 | 换 region 或补权限（第 4 节） |
| Midscene import 你的 step 文件时 `SyntaxError` | 扩展名用了 `.ts` / `.js` | 改成 `.mts` / `.mjs` |
| `plan` / `run` 退 2 点名某个 steps 文件 | 该文件加载失败 | 修那个文件，不是 feature |
| 明明写了 `steps/` 却全走 AI | 目录没被读到或正则不匹配 | `list-deterministic --steps-dir …` 核对；对照 `example` 改 step 文本 |
| `status` / `explain` 退 2 说找不到 run（提示只提 `submit`） | 三个参数与**产生这个 run 的那条命令**（`run` 或 `submit`）不一致 | 照那条命令逐字对齐 `--backend` / `--report-dir` / `--prefix` |
| `--expose-local` 起隧道失败 | 没装 ngrok、或 authtoken 没配（配置文件与环境变量都没有）、或本机没外网 | 第 5 节 |
| 收窄参数退 2 并列出候选 | `--scope` / `--scenario` / `--tags` 筛成空集 | 从列出的候选里挑正确的值 |
| cloud 命令退 2 说 CLI 新于后端 | 版本不一致 | 第 6 节 |
| cloud 提交退 2 说 variant 没推过 | 某引擎缺该 `--worker-variant` | `gherkai deploy list-workers` 看有哪些；推它或换名（`references/cloud-backend.md`） |
| Nova 档下非英文页面断言判否 | 引擎语言面 | `references/engines.md` 第 1 节 |
| `plan` 打「标注降级」 | 某引擎 worker 不可用，只影响标注 | 不阻塞 plan；要标注就把那个 worker 装上 |
