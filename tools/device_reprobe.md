# device_reprobe 使用说明（Midscene 设备模块的真机重新探测）

> **读者：** 维护 Midscene 设备模块的 contributor（人与 AI agent）。**本文是操作手册**：前置、调用方式、输出与判读。
> **机制**（会话怎样建立、记录层加在哪、差集的口径）见 `device_reprobe.mts` 头注释，不在此复述。
> **相关设计：** ADR 0052（决策 4 驱动适配器与命令契约快照、决策 5 能力探测、决策 8 护栏与真机重新探测工具）、ADR 0051（远程访问会话的生命周期、终结与脱敏）。

## 定位与适用场景

两个驱动适配器（UiAutomator2、XCUITest）发出的命令由离线的命令契约快照锁定（`engines/midscene/src/device/adapters/fixtures/<适配器>.commands.json`，护栏是同目录的 `adapters.contract.test.mts`），能力探测的判据由假 driver 的真值表锁定。这两层只证明「适配器发出的是快照里的命令」，证明不了「真机现在还接受这些命令」：Device Farm 升级 Appium 服务端或驱动、升级 WebdriverIO 或 Midscene 之后，命令名、参数形态、上下文命名与控件树属性都可能变化，离线测试照样通过。

本工具在一台真机上建立一个远程访问会话，用与 worker 相同的设备侧接缝完成获取与能力探测，再逐个执行快照里的原语，把以下内容写成能力矩阵 `capability-matrix.json`：

- 能力探测的结论与逐项事实（上下文列表与网页上下文候选、坐标比例的两种来源、Appium 版本、前台应用）；
- 向模型注册的动作清单（设备 Agent 实际注册的动作名，核对返回键与主屏键是否按平台注册、没有 Swipe）；
- 每条快照用例在真机上的结果与发出的命令，以及与快照的差集；
- 真机控件树与控件树样例的属性差集。

**何时执行**：升级 `@midscene/core` / `@midscene/web` 或 `webdriverio`，或 Device Farm 的 Appium 服务端版本变化（`device-session.json` 记录的 Appium 版本与上一次不同）时，在真机验收矩阵之前，每个平台各执行一次（矩阵见 `engines/midscene/DEVELOPMENT.md`「真机验收矩阵」节）。改了本工具或快照的格式之后，先执行一次 `--offline`。

## 前置条件

- 在 `engines/midscene/` 下执行过 `npm ci`（工具经 `tsx` 直接加载设备模块的源码，不需要 `npm run build`）。
- AWS 凭证，在 us-west-2 上对目标 Device Farm 项目有 worker 所需的六个动作：`ListDevices`、`GetDevice`、`CreateRemoteAccessSession`、`GetRemoteAccessSession`、`StopRemoteAccessSession`、`ListRemoteAccessSessions`（资源形态见 ADR 0033 的权限表）。Device Farm 的区域固定为 us-west-2，与 `AWS_REGION` 无关。
- 一个 Device Farm 项目的 ARN：`gherkai deploy` 建立的那个（`gherkai doctor --backend cloud` 的 `backend.devices.project` 行），或本机后端用的项目。
- 应用目标另需：安装包已在 S3 里（例如由一次 `gherkai run` 上传到 `apps/<sha256>/` 下），凭证对它有读取与所在前缀的列举权限；`AWS_REGION` 设为桶所在的区域（S3 客户端按 SDK 惯例读它）。
- 不需要模型权限：工具不执行 AI 动作。

## 费用

一次执行建立一个远程访问会话，按设备分钟计费：取设备的等待（约 1 到 2.5 分钟）、原语执行、停止到 COMPLETED 的收尾（Android 约 1 分钟，iOS 最长约 2.5 分钟）都计入。工具在正常结束、获取失败、出错与收到 SIGINT / SIGTERM 时都会停止它建立的会话；会话名以 `gherkai:device-reprobe-` 开头，释放没能确认时到 Device Farm 控制台按这个名字核对，或用 `gherkai doctor --backend cloud` 的 `backend.devices.sessions` 行列出。

## 调用

```bash
cd engines/midscene

# 离线自检：不连设备，核对工具自身
node_modules/.bin/tsx ../../tools/device_reprobe.mts --offline

# Android 网页目标：先打开一个带输入框的测试页，点它获得焦点后执行输入类原语
AWS_REGION=us-west-2 node_modules/.bin/tsx ../../tools/device_reprobe.mts \
    --platform android --project-arn <项目 ARN> --os-version 14 \
    --url https://example.com/form --focus 540,900 --deep-link https://example.com/

# iOS 应用目标
AWS_REGION=<桶的区域> node_modules/.bin/tsx ../../tools/device_reprobe.mts \
    --platform ios --ui-kind app --project-arn <项目 ARN> --device-arn <设备 ARN> \
    --app-bucket <桶> --app-key apps/<sha256>/<文件名> --app-id <bundle id> --deep-link <应用能处理的地址>
```

| 选项 | 缺省 | 说明 |
|---|---|---|
| `--offline` | 关 | 离线自检，见下文同名一节；给了它其余选项都不读 |
| `--platform` | 必填 | `android` / `ios` |
| `--ui-kind` | `web` | `web` 测设备浏览器（Android 的 Chrome、iOS 的 Safari），`app` 测原生应用 |
| `--project-arn` | 环境变量 `GHERKAI_DEVICE_FARM_PROJECT_ARN` | Device Farm 项目 ARN |
| `--device-arn` / `--os-version` | 二选一 | 指定设备，或按系统版本族挑选（与 `gherkai.toml` 的 `[devices.<平台>]` 同一规则） |
| `--app-bucket` / `--app-key` / `--app-id` | 应用目标必填 | 安装包在 S3 的位置与包名或 bundle id |
| `--url` | 不打开 | 原语执行前经接缝的导航打开的地址：网页目标按探测结论在网页上下文打开、或交给系统浏览器，应用目标经 DeepLink 交给被测应用 |
| `--focus <x>,<y>` | 不执行输入类原语 | 截图像素坐标；每条输入类用例（输入、按键、清空）之前点一次这里，让输入框获得焦点 |
| `--deep-link` | 不执行 DeepLink 用例 | 替换快照里 DeepLink 用例的地址；应用标识换成本次目标的值，只执行与本次界面类型相符的那条用例 |
| `--billing-method` | `METERED` | `METERED` / `UNMETERED` |
| `--acquire-timeout-s` | `600` | 获取设备的等待上限（与 `gherkai.toml` 的 `acquire-timeout-s` 缺省值相同） |
| `--out` | 系统临时目录下新建 | 输出目录 |

快照用例的输入照原样执行：坐标、文本与上下文都取快照里的值（例如 iOS 用例按快照写的比例换算坐标，点击的位置与真机比例无关），这样发出的命令才能与快照逐条比对。所以 `--url` 给的页面应当允许在任意位置点击、长按、滚动而不离开测试范围，输入框能接受快照里的文本。用例的执行次序是输入类（紧跟聚焦）、手势、DeepLink、返回键、主屏键；主屏键会把被测对象切到后台，排在最后。

## 输出

`--out` 目录下：

```
capability-matrix.json                         能力矩阵（整份写盘前经脱敏）
device/device-reprobe-<哈希>/device-session.json 接缝写的 scope 诊断文件，与 worker 产出的同一份格式
device/device-reprobe-<哈希>/page-source/       接缝界面快照写下的原始控件树（脱敏、超过上限截断）
```

`capability-matrix.json` 的主要键：

| 键 | 内容 |
|---|---|
| `run_id`、`target`、`request` | 本次的运行编号（会话名的 run 段）、目标与设备请求 |
| `acquire` | `ready` 为 true 时带执行所用的会话 ARN；为 false 时带 `error_type` 与 `message`，与 worker 的执行前失败同一归因 |
| `automation_name`、`platform_version` | 会话回报的驱动名与系统版本 |
| `action_space` | 设备 Agent 向模型注册的动作名 |
| `probe.conclusion` | 能力探测的结论，与 `device-session.json` 的 `probe` 同源 |
| `probe.items` | 逐项事实，经生命周期通道读取（不经命令守卫）：`current_context`、`contexts`、`web_context_candidates`、`switch_to_native`；iOS 另有 `device_screen_info_scale`、`screenshot_long_edge`、`window_long_edge`、`page_source_scale`、`active_app_bundle_id`，Android 另有 `current_package`。`web_context_candidates` 与 `page_source_scale` 是由其它几项推出的值，其余每项是 `{value}` 或 `{error}` |
| `page` | `--url` 的打开结果与路线（`url` / `deep_link`） |
| `snapshot` | 接缝的界面快照（与失败 step 的证据同一条采集路径）：`url` / `url_missing`、`controls`、`page_source_path` 与 `page_source_truncated` |
| `page_source` | 真机控件树的控件数与它和控件树样例的属性差集 `diff` |
| `cases` | 每条快照用例：`status`（`ok` / `failed` / `skipped`）、跳过原因、失败原因与归类、发出的命令（`commands` 为与快照格式相同的树，`flat` 带每条命令的成败）、快照的命令（`expected`）、`matches_fixture` |
| `diff` | 与命令契约快照的差集，见下节 |
| `release`、`session_events` | 释放结果与本次发出的会话事件（每个会话恰一对，`release_failed` 为 true 表示有会话没能确认停止） |

## 判读

先看 `acquire.ready`：为 false 时没有执行任何原语，按 `error_type` 与 `message` 处置（与 worker 的执行前失败相同，例如 `precheck_failed` 的零候选设备、安装包缺失）。就绪之后看 `diff`：

| 字段 | 含义 | 处置 |
|---|---|---|
| `rejected` | 快照里的命令形态被真机拒绝（附用例与真机给的原因） | 先排除用例环境的原因（输入框没有获得焦点、`--deep-link` 的地址应用处理不了）；排除后即平台行为变了：按真机接受的写法改适配器、同步改快照，并回写 ADR 0052 决策 4 的映射表与实测依据 |
| `not_exercised` | 快照里的形态这次没有执行到（附原因：跳过、执行中途失败、执行成功但没有发出这一形态） | 补齐选项后再执行一次；全部执行到之前不算完成重新探测 |
| `unexpected` | 执行中发出了快照里没有的形态 | 适配器在真机应答下走了快照没覆盖的分支；补快照用例，或修适配器 |
| `mismatched_cases` | 执行成功、但归一后的命令序列与快照不同的用例 | 同上，逐条对照 `cases[].commands` 与 `expected` |
| `failed_cases` | 执行失败、却不是某条命令被拒的用例（命令守卫拒绝、适配器在发命令之前判定不提供） | 看 `error_type` 与 `error`；`capability_unavailable` 多半是这台设备本就不提供（例如 iOS 老版本不支持经系统打开地址），记进矩阵即可 |

再看两处探测相关的事实：

- `page_source.diff.missing_attributes` 非空、或 `fixture_root` 与 `device_root` 不同：控件摘要的抽取依赖的属性在真机控件树里不存在了，失败 step 的 `controls` 会变空。按真机控件树改适配器的抽取与控件树样例。
- `probe.items` 与 `probe.conclusion` 对照：刚建好的网页会话没有网页上下文候选（`web_context_candidates` 为空）而结论是「不提供」时，即真机验收矩阵里「刚建好、尚未导航的会话是否已有网页上下文候选」那一行的情形；iOS 的 `device_screen_info_scale` 与 `page_source_scale` 不一致时，坐标比例的回退依据需要复核（ADR 0052 决策 5）。

结论与证据回写 ADR 0052 对应的决策与「实测依据」节，快照与样例的改动和适配器的改动同一次提交。

## 离线自检（`--offline`）

不连设备、零 AWS 调用：用按快照应答的假 driver 重放两份快照的全部用例，经与真机执行相同的记录、归一与差集逻辑比对，再拿两份控件树样例各自与自身比较。结果打在标准输出（每份快照一段差集），全部为零差异时退出码为 0。它核对的是本工具，不是适配器：适配器与快照是否一致由 `adapters.contract.test.mts` 守。

## 退出码

| 退出码 | 含义 |
|---|---|
| 0 | 会话就绪，`diff` 的 `rejected`、`unexpected`、`mismatched_cases`、`failed_cases` 均为空，控件树属性无缺失，会话确认停止（`--offline`：零差异，含 `not_exercised` 为空）。真机方式的 `not_exercised` 不影响退出码，须另看 |
| 1 | 会话未就绪、差集不为空、会话中途丢失或释放未确认；矩阵照常写出 |
| 2 | 选项不合法 |
| 130 / 143 | 收到 SIGINT / SIGTERM，已按终结路径停止会话并写出已有的矩阵 |

## 类型检查

本工具不在 `tsc` 的编译范围内（`engines/midscene/tsconfig.json` 只含 `src/`），改设备模块的导出时同步改它，并在 `engines/midscene/` 下核对它仍能通过类型检查：

```bash
npx tsc --ignoreConfig --noEmit --module nodenext --moduleResolution nodenext --target es2022 --types node \
  --skipLibCheck --strict --exactOptionalPropertyTypes false --esModuleInterop ../../tools/device_reprobe.mts
```
