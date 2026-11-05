> 类型: 进度总纲

# 移动真机支持（1.5）：实施进度总纲

分支 `feat/v1.5-mobile-devices`。设计定稿在 ADR 0048 到 0053（2026-10-15）；本文只记实施阶段的现场：做到哪、下一步、还没写的文档。1.5 收尾后删除。

## 恢复现场

- 实施已完成：第 0 到 8 批（九个实施块：导航规则与注册面关键字声明、能力自述增键、core 会话事件与终结函数、目标模型与建会话前自检、配置文件与提交侧、确定性 step 多句柄注册、隧道令牌换 cookie、部署侧、Midscene 设备模块）与第 9 到 13 批（真机验收浮出的拍板项、边界与残余的真跑、评测集设备用例、靶向制造的边界真跑、journey 待项清理）全部闭合并 push、CI 绿（最后一批 2026-11-04）。设计期与实施期的结论都已内联进 ADR 0048 到 0053、按条改写的既有 ADR（Status 头带反向链）、CONTEXT.md 与各包 DEVELOPMENT.md；各批的改动面、护栏测试、同僚复核与真机验收的过程在 commit 历史里。
- 1.5 剩余，按 owner 定的顺序（2026-11-03）：① doc-health 复盘——**已完成**（第九轮，落地提交带 `Doc-Health-Round: 9` trailer，2026-11-05）；它移交 code-health 的 code 侧客观发现与「改 code、ADR 不动」的裁定在 journey 0018 → ② code-health 复盘（下文遗留项里标为 code-health 候选的两条与 journey 0018 在此处理）→ ③ owner 单独做用户文档（下文「documenting 清单」里仍未写的项、README、CHANGELOG 收口）与人读文本的措辞改写（口吻问题先单独讨论）。Appium 3 端点升级放发版后（ADR 0051 决策 3）。
- doc-health 第九轮留下两件待 owner 的事：task role 撤掉 `devicefarm:GetDevice` 后要用受限角色真跑一次云端设备 run（指定 ARN 与按系统版本、Android 与 iOS、网页与应用目标，两个 worker 日志组零 AccessDenied），核过后把 ADR 0033 权限表与 0051 实测依据里「受限角色的真跑核对待补」两句改成已核；零 scenario 的 feature 不加筛选时 `run` 判 passed 退 0（筛空时才以 2 拒绝），要不要在 plan / run 层拒绝零 job 的批，待 owner 定。
- 验证环境 vfy 保留（Device Farm 项目为重新部署后的新项目；验收期对照用的临时执行角色已删）。跳板机的操作要点与演练装置不入库。

## 遗留项

- 两侧错误文本归一化的分行与空白规则不完全对称（Python 的 splitlines / split 认 U+2028 等 Unicode 行列分隔符与 Unicode 空白，Midscene 只按 CR / LF 分行、按 JS 的空白折叠），`A\u2028B` 一侧得 `A`、一侧得 `A B`。既有的低优先级差异，属 code 层、不必进 ADR，code-health 候选。
- 契约页护栏按全页扁平键名核对（`cli/tests/test_cli_json_contract.py` 的 `_leaf_keys`），删掉 list-deterministic 节的 keywords 说明仍能过（既有设计限制），code-health 候选。
- 契约页护栏夹具没有覆盖设备形态：设备 job 的夹具没设 `target` 与 `device_request`（落到模型缺省的 desktop/web、`device_request` 为 None），`target.app` 与 `device_request` 的子键从没被真渲染器产出过；plan 的差集只传桌面 job、`devices` 渲染为空对象，各平台的 `arn` / `os_version` / `source` 子键没进差集。契约页字段说明本身是全的。code-health 候选。
- 策略文件不删除的前提仍需真实核实：ngrok agent 在隧道存活期是否会重读策略文件（`runtime/gherkai_runtime/tunnel.py` 的 `NgrokTunnel.start` 注释已点明，只靠单测证明不了）。
- **演示材料随 1.5 升级与增补**（`docs/presentations/value-method/`）：1.5 收尾后按 `tools/presentations/production.md` 的流程改口播、重配音、更新 manifest（含口播稿与讲者备注的 SHA-256）。随下一版一并改的角色词：口播稿与讲者备注里「编程 agent」改「AI agent」、「QA，也就是测试工程师」改「QA」（ADR 0040 的正名；v12 的定稿原文按文档护栏的定稿豁免规则不回溯改写）。

## documenting 清单（ADR 0048 到 0053 第 7 类内容的汇总）

2026-11-04 按页做过一次差集核对（每页一个核对者对照当前文档，判为没有的再全仓换关键词复核一次）：已写进当前文档的项已从本清单删除，下面只剩没写或写了一半的，每条写明缺什么、现有内容在哪。owner 做用户文档时以此为输入；是建独立设备页集中讲、还是维持分散只补缺口，届时拍板。

新页：

- **设备主题页**（不存在，索引未登记）。@device / @app 写法、应用别名、设备选择、费用这四块的内容已分散写在 `writing-features.md`（tag 规则条）、`configuration.md`（`[devices]` 与 `[apps]`）、`faq.md`（真机与费用两问）、`running-and-results.md`（费用量级）、`engines.md`（计价公式）里；skill 的 `references/engines.md` 第 7 节有一个面向 agent 的集中版本。无论建不建独立页，下面这些点在用户文档里还没有：Android 上「应用未处理该地址」的情形（地址须是被测应用声明能处理的链接，否则记 `capability_unavailable`，改法是改地址或确认应用声明了该链接；`writing-features.md` 导航行只有笼统一句「无法送达时记 error」）；老设备不支持 DeepLink（如 iOS 15.8；结论在本会话内缓存，后续同类 step 不再调用）；国内消费级应用的线上包在公共真机上会自行退出、须提供关闭检测的测试包（现只在排障页作为 `precheck_failed` 的一种形态出现，没有作为事前限制写）；iOS 26 网页上下文不可用（现只有「设备不提供网页上下文」的通用表述，`writing-features.md` 推荐 iOS Safari 用 AI 断言核对落点但没说原因）；Compose 应用控件无标识、确定性 step 无法定位（任何用户文档都没有）。
- **docs/internals：设备会话与 Appium 适配的机理解读一篇**（会话获取、就绪、能力探测、预热、换台、释放与终结核对这条生命周期，加 Appium 接口适配与平台差异；权威指回 ADR 0051 / 0052），`docs/internals/README.md` 登记并在相关各篇的延伸阅读补指针。现有零散落点：`artifacts-and-evidence.md`（page-source 与 device-session.json 的落点、scope 键分目录）、`deterministic-step-lifecycle.md`（webdriver 句柄与设备接缝的 navigate）、`verdict-model.md`（四个 job 级错误类别）、`execution-and-reconciliation.md`（SessionOpened 置 RUNNING）。

既有用户文档的触点（按页列；每条只写缺的）：

- `writing-features.md`：tag 表仍是三行，`@device` / `@app` 只在规则列表的一条里，要改成五行；缺省「不标 `@device` 就是桌面」没写明；拒绝情形没列（`@app` 标在桌面目标、`@device` 的值不是 android / ios、别名在 `[apps]` 里没有该平台的条目）；「标了 tag 就得给值」一句只列了 `@scope:` / `@engine:` / `@timeout:`；`@timeout` 只写了桌面缺省 300 秒，设备 scope 的缺省（获取预算加 900 秒）与下限（获取预算加 180 秒，低于以退出码 2 拒绝；`@timeout` 同受下限约束）现在只在 `running-and-results.md` 讲 `--default-job-timeout` 时提到；「按目标选写法」没有与「按引擎选写法」并列成节（落点核对的分写在「AI 断言怎么写才稳」一条里，不复位与 Background 重启在 tag 规则一条里）；「写完先自检」没提 plan 对目标的标注读法（job 行的 `target=`、表头的远程访问会话数、每个平台一行设备选择；`getting-started.md` 的示例输出含该字段但没解释）。
- `running-and-results.md`：「常用选项」没列 `--android-device-arn` / `--ios-device-arn` / `--device-farm-project-arn` / `--app-bucket` / `--config`、也没有指向设备选项的指针（语义在 `configuration.md` 选项总表里是全的）；`--default-job-timeout` 低于下限时的后果（开始执行前以退出码 2 拒绝）与 `@timeout` 同受下限约束没写；退出码表没点名设备缺项的 2（没指定设备、本机后端没给 Device Farm 项目或应用桶；排障页列了报错原文但没写退出码）；「结果在哪」没有会话列表（job 的 `sessions[]` 与文本汇总的「设备」「设备控制台」「设备占用时长」「设备占用时长合计」「未确认停止的会话」各行，整个用户指南都没有），设备占用时长与 `device_session` 链接分别在「费用量级」与 explain 节、本节没有指针。
- `getting-started.md`：「AWS 前置」整节没有 Device Farm——服务表没有这一行，「三项服务」的数目与 region 提示没写设备资源固定在 us-west-2，费用句没提设备分钟，没有指向 `cloud-backend.md` 的部署方权限与 deploy 建项目。
- `troubleshooting.md`：归因表里 `precheck_failed` / `acquire_timeout` / `session_lost` / `release_failed` 没标明是 job 级（只有 `capability_unavailable` 标了 step 级）；会话类错误在「引擎与判定」节的归因表里，「项目配置文件与设备目标」节只讲配置与设备选择类症状、没有会话类错误也没有交叉引用。
- `cloud-backend.md`：「团队成员需要的最小云端权限」不是三方表（提交者、部署方、worker），部署方的 Device Farm 权限只在「前置要求」且没写资源形态（`ListProjects` / `CreateProject` 用 `*`、`GetProject` 用项目 ARN），worker 任务角色的设备权限（`ListDevices`、`GetDevice`、`CreateRemoteAccessSession`、`GetRemoteAccessSession` 与 `StopRemoteAccessSession`、`ListRemoteAccessSessions`、`…:project:session` 字面量、`apps/` 读取）整页没有（只在 `running-and-results.md` 的本机后端权限表里），`run --backend cloud` 一级漏了设备增量；「费用」列费用来源时漏了设备分钟（只有一个指向运行页量级的链接）；「版本与升级」没直接写同一 report 目录混用 1.4 与 1.5 CLI 读写不受支持（只经指针）、开发版本混搭不在兼容承诺内（全部用户文档都没有）。
- `local-app-testing.md`：「限制」没写设备浏览器没有注入请求头的通道、只能靠服务商不弹警告页（服务商一旦改变行为，设备目标用隧道就得上付费层），也没写免费层每个策略至多 5 条规则（gherkai 用了 4 条）；同时「工作方式」一节「云端浏览器发出的请求恒带一个固定请求头 `ngrok-skip-browser-warning: 1`」只对桌面浏览器成立、设备浏览器不带（ADR 0035 决策 4），补「限制」时一起改。
- `writing-deterministic-steps.md`：材料规则与验收定位五点一条都没有（期望来自需求；材料只定位置；材料来源平铺——应用源码与测试标识、桌面开发者工具或 Playwright、Appium Inspector 或 WebDriver 客户端连 Device Farm 远程访问会话、已有运行的 evidence 控件摘要与控件树；agent 自行开远程访问会话须项目约定放行、无论成败都要停止会话；一条动作步只表达一屏之内的意图、跨多屏的长流程拆成多步；真机验收是验收不是单测）；测试分层缺设备侧（设备网页句柄的离线层：本机 WebdriverIO 加 Chrome for Testing 打开同一份材料页、与桌面句柄共用选择器表、显式固定缓存目录；真机验收层 `run --scope` 收窄到 Device Farm；可选的 Appium fake driver 层；handler 保持薄、判定抽纯函数）；原生应用先看控件有没有稳定标识、没有就写 AI 步。
- 索引与入口页：`docs/user-guide/README.md` 的 writing-features 行只列 `@engine` / `@scope` / `@timeout`，补 `@device` / `@app`（设备页若建则登记）；`engines/midscene/README.md` 没有设备支持一段，开头仍说只在云端浏览器上执行（可照搬 `docs/user-guide/engines.md` 的那句）；`deploy_aws/README.md` 只补了「Device Farm 项目」，缺部署凭证要有 us-west-2 的 Device Farm 权限（`ListProjects` / `GetProject` / `CreateProject`）与缺权限时部署照常完成、后端不启用设备支持的降级一句，destroy 保留的数据类资源列表也没列 Device Farm 项目。
- CHANGELOG 与 1.5 的 Release 正文：`[Unreleased]` 节已写设备支持的主体，还缺这些点：设备会话的录像与日志由 Device Farm 保留 400 天、驻留 us-west-2（现只在 destroy 一条提到项目连同录像保留）；以及 1.4.3 与 1.4.4 两节都有的「升级须知」小节（本节的升级动作散在各条里：CLI 与 worker 同版本、重新 `gherkai deploy`、导航步改为整句地址、同一报告目录不混用 1.4 与 1.5）。发版前收口。

其它读者的文档：

- skill：`references/deterministic-steps.md` 既没内联也没链到地址核对模板，带 `requires: ["web_context"]` 的 webdriver 条目只有文字描述没有示例代码（仓库 `features/steps/url_matches.mts` 有）；确定性 step 参考缺 ADR 0050 决策 4 的几条——材料只定位置的完整口径（控件树、截图、evidence 也只用来定位）、来源平铺、agent 自行开会话须约定放行且无论成败都停止会话、一屏一意图跨屏拆步、原生应用先看稳定标识；评测集缺「自写一条 webdriver 条目（含 uiKinds / devices / requires）」与「处置 `precheck_failed`」两题（现有的 26、28 复用重启应用模板，27 处置的是 `session_lost`）；`--config` 与 `GHERKAI_CONFIG`、定位顺序（`--config` > `GHERKAI_CONFIG` > 当前目录的 gherkai.toml、不向上查找、显式路径不存在退出码 2）、选项 > 环境变量 > 配置文件的通用优先序、哪些命令读它与提交时解析成具体值都没写，SKILL.md 第 7 节的 flag 表也没有 `--config` 与四个设备选项（可链到 `configuration.md`）。
