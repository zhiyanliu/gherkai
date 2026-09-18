# gherkai-worker-novaact

gherkai 的 Nova Act 执行引擎 worker：在云端浏览器（Amazon Bedrock AgentCore Browser）上执行 `.feature` 的每个 step——AI step 交给 Amazon Nova Act 模型看图操作与判定，确定性 step 走你自己写的 Playwright 函数。它由 `gherkai` 命令行按需拉起，**不必手动运行**；本机装上它，就是让 `gherkai` 能用 `novaact` 引擎执行测试。被测 UI 的支持范围是英文界面，非英文界面请用 Midscene 引擎。

## 安装

```bash
uv tool install 'gherkai[local]'   # 命令行与本 worker 装进同一环境，需 Python ≥ 3.13
```

## 最小用法：写一条确定性 step

确定性 step 写在你自己项目的 `steps/` 目录里，用 `gherkai run --steps-dir ./steps` 带上（缺省即 `./steps`）：

```python
# steps/login.py
from gherkai_worker_novaact.deterministic import deterministic


@deterministic(r'以 "(?P<user>[^"]+)" 登录',
               description="确定性填表登录",
               example='Given 以 "alice" 登录')
def login(ctx, user):
    ctx.page.fill("#user", user)      # ctx.page 是 Playwright 的 Page
    ctx.page.click("#submit")
```

用 `gherkai list-deterministic --engine novaact --steps-dir ./steps` 查当前注册了哪些。

## 文档

- 装什么、要哪些 AWS 前置、第一次怎么完整运行：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/getting-started.md
- 确定性 step 的完整写法与两侧对照：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/writing-deterministic-steps.md
- `.feature` 怎么写才能稳定运行：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/writing-features.md
- 模型、region、超时等环境变量与选项：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/configuration.md
- 报错了先看哪：https://github.com/zhiyanliu/gherkai/blob/HEAD/docs/user-guide/troubleshooting.md
- 每版变更：https://github.com/zhiyanliu/gherkai/blob/HEAD/CHANGELOG.md

项目主页与问题反馈：https://github.com/zhiyanliu/gherkai#readme
