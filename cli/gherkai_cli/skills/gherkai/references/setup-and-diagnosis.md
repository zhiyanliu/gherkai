# 环境就位与排障

本文管「装、查、卡住了怎么办」。每条命令的全部选项以 `gherkai <命令> --help` 为准；报错都带「怎么办」，先照它说的做。

## 1 装什么

| 角色 | 装法 | 得到 |
|---|---|---|
| 只提交云端 run（不在本机运行） | `uv tool install gherkai` | 只要 CLI 本体，两个 worker 都不用装（worker 运行在云端）；代价是 `plan` 会打「标注降级」 |
| 本机运行 Nova Act（推荐起点） | `uv tool install 'gherkai[local]'` | CLI 与 Nova worker 在同一环境 |
| 本机运行 Midscene | `uv tool install gherkai` + `npm i -g @gherkai/worker-midscene`（Node ≥ 22） | CLI + Midscene worker |
| 本机运行两个引擎 | `uv tool install 'gherkai[local]'` + `npm i -g @gherkai/worker-midscene`（Node ≥ 22） | CLI + 两个 worker |
| 部署方 | `uv tool install 'gherkai[deploy-aws]'`（另需 Node ≥ 22、docker） | 多出 `gherkai deploy` / `gherkai destroy` |

升级：`uv tool upgrade gherkai`（安装时带的 extras 沿用）；Midscene worker 另 `npm i -g @gherkai/worker-midscene@<CLI 版本>`。worker 与 CLI 版本同号锁定。

## 2 CLI 怎么找 worker

- **Nova Act**：① 环境变量 `GHERKAI_WORKER_NOVAACT_CMD`（+ 可选 `GHERKAI_WORKER_NOVAACT_CWD`）显式指定；② 与 CLI 同一个 Python 环境；③ PATH 上的 `gherkai-worker-novaact`；④ 三级都没有、CLI 是正式发行版、机器上有 uvx 时临时拉起同版本 worker。四级都没命中：local 后端的 `run` / `submit` 与 `list-deterministic` 以退出码 2 结束并打印装法（`submit` 也在提交前就拒）；`--backend cloud` 的 `run` / `submit` 不看本机 worker（它运行在云端容器里）；`plan` 不拦，只少了那个引擎的派发标注。
- **Midscene**：PATH 上的 `gherkai-worker-midscene`（`npm i -g` 的结果），或环境变量 `GHERKAI_WORKER_MIDSCENE_CMD`（+ 可选 `GHERKAI_WORKER_MIDSCENE_CWD`）显式覆写。**必须真装**，没有临时拉起的兜底。

`gherkai list-engines` 打出每个引擎的探测结果与来源，缺的那个原地给安装命令；`--json` 机读（`engine` / `available` / `cmd` / `cwd` / `source` / `hint`）。

## 3 `gherkai doctor` 怎么读

只读自检，不建会话、不调模型、不花钱。每行一个检查项：`✓` 过（「未查」的项也算过）、`✗` 必修项没过、`-` 可选能力缺失（如另一个引擎没装）。名字按段分组：

| 段 | 查什么 | 何时查 |
|---|---|---|
| `cli.*` | CLI 版本与 Python | 总是 |
| `engines.*` | 每个引擎的 worker 能否定位、至少一个可用、本机 worker 各自自报的模型 | 总是 |
| `steps.*` | steps 目录是否存在、每个引擎加载 steps 是否成功、几条 | 总是（`--steps-dir` 可改目录） |
| `aws.*` | region、凭证身份 | 给了 `--backend cloud` 或 `--prefix` |
| `backend.*` | 后端版本与 CLI 比对、资源齐全、报告前缀一致、默认 variant 与逐引擎镜像能否解析、本机 worker 自报的收尾宽限 vs 云端为它设的停止宽限（差距只标 `-`、不影响退出码） | 同上 |
| `provider.*` | Node、cdk、容器引擎（部署方工具链） | 装了部署 extra 时 |

退出码：全部通过为 0；有**必修项**失败为 2（非必修项失败只标出不影响退出码）。`--json` 每项给 `section` / `name` / `ok` / `required` / `detail`，脚本按 `required && !ok` 找阻塞项。

## 4 凭证与 region

- 走本机 AWS 默认凭证链：profile / 环境变量 / 实例角色皆可，`--profile` 或 `AWS_PROFILE` 选 profile。**不需要任何 API key**。
- **region 必须有出处**，按序解析：`--region` > `AWS_REGION` > `AWS_DEFAULT_REGION` > `--profile`（或 `AWS_PROFILE`）指的那个 profile 配置里的 region。四处都没有才报错；缺了不会替你兜一个 region。
- 该 region 下账号要能用这些服务：Nova Act 引擎需要 Nova Act 服务与模型 nova-act-v1.0（默认锁定；环境变量 NOVA_MODEL_ID 可换，`doctor` 会显示实际模型）；Midscene 引擎需要 Bedrock 模型 us.openai.gpt-5.6-terra（默认；环境变量 MIDSCENE_MODEL_ID 可换，`doctor` 会显示实际模型）；两者都要 AgentCore Browser。`AccessDenied` / 模型不可用多半是 region 未开通模型或凭证缺这些权限。
- 本机 `run` / `submit` 也要 AWS 凭证（浏览器与模型在云端）；只有 `plan` / `list-engines` / `list-deterministic` / `doctor`（不带 cloud 参数）纯本地。

## 5 隧道（`--expose-local`）：前置、写法、排障

**前置两样**，缺哪样都是 `run` / `submit --expose-local` 在起隧道时以退出码 2 结束，且 `doctor` 两样都不查（它不碰隧道）：

- **ngrok 可执行文件**装好且在 PATH 上（`ngrok version` 能正常执行；下载 https://ngrok.com/download ）。没装的报错点名找不到 ngrok 可执行文件。
- **ngrok 账号的 authtoken**（免费账号即够）：`ngrok config add-authtoken <token>` 写进 ngrok 自己的配置文件，或环境变量 `NGROK_AUTHTOKEN`，任一处即可。排障别只看环境变量在不在——配置文件里配过就够。取值在 ngrok 控制台的 **Your Authtoken** 页；**API Keys** 页的值起不了隧道，两者都是长随机串、肉眼分不出，填错的表现是「隧道未就绪」、报错附带的 ngrok 日志会点明鉴权原因。

**写法三条**，都是导航失败的常见来源：

- **选项值与 feature 里书写的地址逐字一致**。替换是前缀字符串匹配：`http://localhost:3000` 与 `http://127.0.0.1:3000` 互不匹配，大小写、端口都要一样；没匹配上就不替换，云端浏览器照着原地址导航、第一步就失败，而被测应用的日志里一条请求都不会有。端口不判边界：给 `http://localhost:3000` 会连带改坏 feature 里的 `http://localhost:30000`，先把端口写法区分开。
- **核对方法，改完给人一并写出来**：

  ```bash
  gherkai plan features/<x>.feature --expose-local http://127.0.0.1:3000   # 「注：」行回显你给的值；把它与打印出的 step 文本逐字对照
  ```

  `plan` 不检查 feature 里有没有这个地址，地址不匹配它照样以退出码 0 结束，所以对照只能靠眼睛：大小写、端口、localhost 与 127.0.0.1 都要一致。
- **一个 run 只能暴露一个地址**：重复给 `--expose-local` 不报错，只有最后一个生效，前面的地址不被替换。多个本机地址先收敛到同一个入口。
- **被测应用收到的 Host 头是隧道分配的 ngrok 域名**，不是 localhost。校验 Host 的开发服务器会在框架层拒绝：Vite 的 `server.allowedHosts`、Django 的 `ALLOWED_HOSTS`、Rails 的 host authorization 都要放行隧道域名；域名每个 run 一换，用通配写法（如 `.ngrok-free.app`）改动最小。症状是请求到了应用却返回 400 或「Blocked request / host not allowed」，本机直连正常。

**隧道的持有与拆除**：`run` 由前台 CLI 进程持有，命令结束或 Ctrl-C 即拆；`submit` 由本机后台进程持有，run 到终态即拆；`submit --backend cloud` 由本机守护进程持有，到终态或 `--tunnel-ttl` 到点即拆。三种都要求**本机保持开机联网到 run 终态**。用 kill 命令结束 CLI 不会拆隧道，要到进程列表里结束 ngrok。隧道断了不自动重连，受影响的 scenario 以导航失败告终，修好后重新运行。

**排障入口**：CLI 打的「隧道已建立」那行给出原始地址与替换后的公网地址（Host 放行要用它的域名）；`submit` 的隧道进程号记在 `<report-dir>/<run_id>/tunnel.json`；起隧道的完整日志在系统临时目录的 `gherkai-tunnel-*.log`，按修改时间取最新；`submit` 若打出「隧道已拆除」，这个 run 已经不可用，别再等它的结果，修好报错后重新提交。

**安全一句要替人说出来**：隧道存活期间被测应用可从公网访问，gherkai 默认加 basic-auth、凭据每个 run 一换、由 ngrok 在边缘校验；凭据内嵌在替换后的地址里，会出现在任务文本、模型提示与报告中，报告按内部资料对待；只把测试实例接上隧道。

## 6 版本不一致（`--backend cloud` 退出码 2）

部署时后端记下自己的版本，每条 cloud 命令动资源前先比对：

- **CLI 比后端新时拒绝，以退出码 2 结束，没有强行放行的开关。** 出路：部署方 `gherkai deploy` 把后端升上来；或临时用与后端同版本的 CLI：`uvx --from 'gherkai==<后端版本>' gherkai …`，不动本机安装。
- CLI 比后端旧时只警告不拦，`uv tool upgrade gherkai` 跟上。
- 升级顺序：部署方先升 CLI、立刻 `gherkai deploy`，其他人再升自己的 CLI；中间窗口里提交被拒是预期。

## 7 症状与处置

| 你看到 | 多半是 | 怎么办 |
|---|---|---|
| 以退出码 2 结束，说某引擎 worker 未找到 | 没装或不在 PATH | 照打印的装法装；或设 `GHERKAI_WORKER_<ENGINE>_CMD` |
| `engine_error`，起 worker 失败 | worker 版本与 CLI 不一致 | 重装到同版本（第 1 节） |
| 启动即抱怨 region 未设 | `--region` / `AWS_REGION` / `AWS_DEFAULT_REGION` / profile 配置四处都没 region | 任选一处设上（第 4 节）；缺了不会自动兜一个 region |
| `AccessDenied` / 模型不可用 | region 未开通模型，或凭证缺 Bedrock / AgentCore 权限 | 换 region 或补权限（第 4 节） |
| Midscene 侧某个 step 文件里的 step 全走了 AI、`list-deterministic` 清单里也没有它，且没有任何报错 | 扩展名用了 `.ts` / `.js`（收集阶段按扩展名过滤，静默跳过、不 import） | 改成 `.mts` / `.mjs` |
| `plan` / `run` 以退出码 2 结束并点名某个 steps 文件 | 该文件加载失败 | 修那个文件，不是 feature |
| 明明写了 `steps/` 却全走 AI | 目录没被读到或正则不匹配 | `list-deterministic --steps-dir …` 核对；对照 `example` 改 step 文本 |
| `status` / `explain` 以退出码 2 结束、说找不到 run（提示只提 `submit`） | 三个参数与**产生这个 run 的那条命令**（`run` 或 `submit`）不一致 | 照那条命令逐字对齐 `--backend` / `--report-dir` / `--prefix` |
| `--expose-local` 起隧道失败 | 没装 ngrok、或 authtoken 没配（配置文件与环境变量都没有）、或填的是 API key、或本机没外网 | 第 5 节 |
| 隧道已建立，每条 scenario 第一步导航就失败，应用日志里没有请求 | 选项值与 feature 书写的地址不一致（localhost 对 `127.0.0.1`、端口、大小写），地址没被替换 | 第 5 节：`plan --expose-local` 回显与 step 文本逐字对照，改成一致 |
| 请求到了应用，页面返回 400 或「host not allowed」，本机直连正常 | 开发服务器校验 Host，拒绝了隧道域名 | 第 5 节：放行隧道域名（通配写法） |
| run 中途开始每条 scenario 都导航失败 | 隧道已拆：本机关机或断网，或 `--tunnel-ttl` 到点 | 保持开机联网；批量大时给更长的 `--tunnel-ttl` |
| 收窄参数以退出码 2 结束并列出候选 | `--scope` / `--scenario` / `--tags` 筛成空集 | 从列出的候选里挑正确的值 |
| cloud 命令以退出码 2 结束、说 CLI 新于后端 | 版本不一致 | 第 6 节 |
| cloud 提交以退出码 2 结束、说 variant 没推过 | 某引擎缺该 `--worker-variant` | `gherkai deploy list-workers` 看有哪些；推它或换名（`references/cloud-backend.md`） |
| Nova Act 引擎下非英文页面断言判否 | 引擎语言面 | `references/engines.md` 第 1 节 |
| `plan` 打「标注降级」 | 某引擎 worker 不可用，只影响标注 | 不阻塞 plan；要标注就把那个 worker 装上 |
