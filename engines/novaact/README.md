# gherkai-worker-novaact

gherkai 的 **Nova Act 执行引擎**：把 `.feature` 里的每个 step 在**云端浏览器**（Amazon Bedrock AgentCore Browser）上真跑一遍——自然语言 step 交给 Amazon 的 `nova-act-latest` 模型看图操作，你自己写的确定性 step 用 Playwright 精确判定。

它是一个被 `gherkai` CLI 拉起并驱动的 **worker 进程**：日常你敲的是 `gherkai run` / `gherkai submit`，**不用直接调用本包的命令**。装上它 = 让 `gherkai` 能在本机用 novaact 引擎跑起来。

## 安装

```bash
uv tool install 'gherkai[local]'      # CLI 与本 worker 装进同一个环境（推荐）
```

CLI 按这个顺序找 worker，命中即用：① 环境变量 `GHERKAI_WORKER_NOVAACT_CMD`（+ 可选 `GHERKAI_WORKER_NOVAACT_CWD`）显式指定——给了就用它，自建或调试时用 → ② 与 CLI 同一个 Python 环境（上面那条装法的结果）→ ③ PATH 上的 `gherkai-worker-novaact` 命令 → ④ 前三级都没有、且 CLI 是正式发行版本、机器上有 `uvx` 时，临时拉起与 CLI 同版本的 `gherkai-worker-novaact`（本引擎独有）。worker 与 CLI 版本同号锁定；四级都没命中时 `gherkai run` / `gherkai list-deterministic` 退 2 并打印装法。

## AWS 前置

- **纯 IAM 鉴权**：走本机 AWS 默认凭证链（profile / 环境变量 / 实例角色皆可）。**不需要 `NOVA_ACT_API_KEY`**——本引擎不用 API key。
- **region 必须显式给**：`AWS_REGION`，或 `gherkai run --region <R>`；未设即报错，不猜默认 region。
- 该 region 下账号需可用：**Nova Act 服务**（`nova-act`）+ 模型 `nova-act-latest`，以及 **AgentCore Browser**（`bedrock-agentcore`）。浏览器跑在云端，本机**不需要装 Chromium**。
- Nova Act 的 workflow definition 由 worker **自动按需创建**（幂等，已存在即跳过），不必手工预建。

## 写确定性 step（`steps/*.py`）

自然语言 step 默认交给 AI；「必须精确、不容抖动」的判定（URL、关键 DOM……）写成确定性 step——命中即走你的函数，不问 AI、可复现。写在你**自己项目**的 `steps/` 目录里（不改本包文件）：

```python
# steps/login.py
from gherkai_worker_novaact.deterministic import deterministic


@deterministic(r'以 "(?P<user>[^"]+)" 登录',
               description="确定性填表登录（不走 AI）",
               example='Given 以 "alice" 登录')
def login(ctx, user):
    ctx.page.fill("#user", user)      # ctx.page 就是 Playwright 的 Page
    ctx.page.click("#submit")
```

- 签名 `handler(ctx, **groups)`：`groups` = 正则里的具名组 `(?P<name>...)`（无具名组则只收 `ctx`）；`ctx.page` 是 Playwright `Page`。
- `description` / `example` **必填**——它们就是 `gherkai list-deterministic` 与 `gherkai plan` 打给用例作者看的那两行，缺了启动即报错。
- 抛 `AssertionError` → 该 step 记 **failed**（断言没过）；抛其它异常 → 记 **error**。确定性 step 不投票。
- 目录**排序递归**遍历 `*.py`；跳过 `_*.py`（你自己的辅助模块，供相对 import 用）与 `test_*.py`（你自己的测试）。
- 本包内建一条示范锚点 `页面地址匹配 "<正则>"`，装上即可在 `.feature` 里直接写 `Then 页面地址匹配 "/wiki/OpenAI"`。

目录怎么告诉 CLI：`gherkai run --steps-dir ./steps`（`run` / `submit` / `plan` / `list-deterministic` 四处都有此选项），缺省 `./steps`。

### 用错了会怎样（一律响亮失败，绝不静默降级）

| 情况 | 表现 |
|---|---|
| 注册时缺 `description` / `example` | 启动即报错退出，点名那条 pattern |
| `steps/` 下某个文件 import 失败（语法错、缺依赖……） | 退 **2**，stderr 点名文件与异常——**不跳过**（跳过等于把确定性判定悄悄换回 AI，run 还可能「通过」） |
| `--steps-dir`（或 `GHERKAI_STEPS_DIR`）指的目录不存在 | 直接退 **2** 并说明：明确指了一个地方而那里没东西 = 配置错。（缺省的 `./steps` 不存在**不算错**——多数项目本就没有确定性 step） |
| 一个 step 文本命中多条 pattern | 该 step 记 error 并列出撞上的 pattern；`gherkai plan` 会提前把冲突暴露出来 |

## 查有哪些确定性 step

```bash
gherkai list-deterministic --engine novaact --steps-dir ./steps   # 人读清单（pattern + 说明 + 可抄的示例）
gherkai list-deterministic --engine novaact --json                # 机器可读
gherkai plan features/                                            # 每个 step 会走确定性还是 AI
```

两者都不建浏览器会话、不调模型，**不产生 AWS 费用**。

## 把 steps 带到云端

`--backend cloud` 时 worker 跑在 Fargate 容器里、读不到你本机的 `steps/`——把它烙进一个定制镜像（三行）：

```dockerfile
FROM ghcr.io/zhiyanliu/gherkai-worker-novaact:<你的 CLI 版本>
COPY steps/ /app/steps
ENV GHERKAI_STEPS_DIR=/app/steps
```

```bash
docker build --platform linux/amd64 -t acme-novaact:login .
```

> ⚠️ **必须 `--platform linux/amd64`**：在 arm Mac 上漏了会 build 出 arm64 镜像，容器**启动期** `exec format error` 挂死，现象离原因很远。

推送、选用（`--worker-variant`）与默认指针见部署方文档 https://github.com/zhiyanliu/gherkai/blob/HEAD/deploy_aws/README.md 。

## 报告与产物

Nova Act 每次 `act` / `act_get` 各出一份 trajectory HTML（截图 + 模型的判断轨迹）：

- `--backend local`：落 `reports/<run_id>/nova-trajectories/`，run 报告里带引用。
- `--backend cloud`：随 run 传到 S3，`gherkai status` 给出引用。
- `--no-report`：**不生成、不上报**引擎原生产物（引擎自己可能写的临时文件落一次性临时目录，不进你的工作目录）。

## 退出码与常见错误

日常看 CLI 的退出码即可；直接跑 worker 时：`0` 正常、`2` steps 目录/文件加载失败（见上表）、`80` 连云端浏览器的重试耗尽（网络或额度问题——换 region 或稍后重试）。

| 你看到 | 怎么办 |
|---|---|
| `engine_error: 起 worker 失败` | worker 没装或版本与 CLI 不一致：`uv tool install 'gherkai[local]'` |
| `AccessDenied` / `ValidationException` 提到 `nova-act` | 该 region 未开通 Nova Act，或凭证缺 `nova-act` / `bedrock-agentcore` 权限 |
| 启动即抱怨 region 未设 | 设 `AWS_REGION`（或给 `--region`）——本引擎不猜默认 region |
| 明明写了 `steps/` 却全走 AI | 确认 `--steps-dir` 指对，并用 `gherkai list-deterministic --steps-dir …` 看清单里有没有你那条 |

## 帮助

用法、装法与命令全景见项目主页 https://github.com/zhiyanliu/gherkai#readme ；问题请提 issue：https://github.com/zhiyanliu/gherkai/issues 。

设计文档（架构决策记录）见 https://github.com/zhiyanliu/gherkai/tree/HEAD/docs/adr 。
