# code-health 第 5 轮：待批报告

> 类型: 待批报告（批毕落改吸收即删；跨轮沿用靠落地提交的 `Code-Health-Records` trailer 取回）

方法真源 `docs/ai-eng/code-health-review.md`；骨架同姊妹任务的待批报告条。术语一律用 CONTEXT.md 规范名。

## ① 基线

- 锚点 = 第 4 轮落地提交 bb36eb4（2026-09-15）→ HEAD 8e54ee9（2026-09-20），88 个提交。上轮无 `Code-Health-Records`（trailer 本轮才加），上轮报告不可取回；上轮驳回清单只有 R14（见 ⑧）。
- 热力图（生产代码变更行数，多为术语与文案改名）：cli/__main__.py 499、runtime/compose.py 377、midscene run-scope.mts 262、deploy_aws cli.py 220、novaact run_scope.py 151、tools/build_diagrams.mjs 125（新）、workers.py 114、stack.py 98、release_notes.py 85、release.yml 76、pages.yml 35（新）。同期 ADR 变更前五：0037、0045（新）、0016、0038、0043。
- 测试基线：pytest 1395 passed / 3 skipped；Midscene 183 pass。
- 执行：19 片（10 片按模块耦合分、2 片跨包死码扫、3 片注释术语扫、发布链 1 片、tools 1 片、cli 与 deploy 各拆两片）+ 44 个验证代理，共 63 个代理；1 个验证代理因 API 安全策略误报中止（comment-terms-cli-deploy-tools#15 只剩单票）。
- 计数：发现 120 条——BUG 10（9 CONFIRMED / 1 REFUTED）、DEAD 7（5 CONFIRMED / 1 REFUTED / 1 low 未验）、VIOLATES_ADR 14（10 CONFIRMED / 2 REFUTED / 2 UNCERTAIN）、STALE_INEFFICIENT 89（含跨片重复报的同一处约 15 条）。去重后客观类落改约 75 处（含落地复核追加的 6 处）、待批 10 项裁定 + 13 项重构提案。落地后全套 pytest 1400 passed / 3 skipped（新增 5 条测试），Midscene 187 pass（新增 4 条），契约副本 `--check` 一致。

## ② 请裁定（每项带复盘方倾向，编号可一句话回）

- **D1 Midscene 在途窗口兜底的判据多带 `pendingSessions.size === 0`**（run-scope.mts onSignal 的 inflightPending；BUG low，双票 CONFIRMED）。上一 attempt 有 Stop 失败的遗留会话时，「Start 已发 RPC、id 未返回」那一瞬不再被覆盖，与 ADR 0028「剩余仅那一瞬、由在途标记 + 短暂兜底等待覆盖」不符。**倾向**：去掉 `size === 0`、只看 `startInFlight`，同步接口注释并留一句反模式注释；代价只是退化路径多等 1.5 s（已计入 minGraceSeconds 的加数）。
- **D2 Nova 收尾排空超时日志的 `flush_follows=True` 分句承诺「剩余的改由收尾统一上传」**（run_scope.py `_drain_evidence_uploads`；VIOLATES 0039 文案不变量「不承诺收尾会再传、两引擎同形」，双票 CONFIRMED）。属 STALE ③ 形态：分句是第 4 轮落地提交引入的，ADR 那条不变量是紧随的文档提交写上的，两者从出生就不一致。**倾向**：改 ADR 0039 面一补例外「承诺只许出现在调用点已声明其后紧跟整目录 flush 的那条路径上」并内联判据（flush 不受 drain 放弃标志约束、evidence 落在 flush 根内），同时让 Midscene scope 末排空（run-scope.mts drainArtifactQueue → flushAndCleanup 那处）按同一分句写法对齐，恢复「两引擎同形」。若取「改 code 回无条件文案」，须连带删 `flush_follows` 参数与 test_evidence.py 两条分句测试。
- **D3 sdist 打包面改白名单**（release-chain#2，BUG high，CONFIRMED）。五个包的 sdist 靠 hatchling「项目根向上第一份 .gitignore」排除，而 core / cli / novaact 各有一份只列 venv 与缓存的包内 .gitignore，把根 .gitignore（含密钥段、`**/graphify-out/*`、skills-lock.json）整体挡住：本机 `uv build` 出的 core sdist 带进了未跟踪的 `core/graphify-out/`（65 个文件，本机现存的杂物目录，建议手工删除）、novaact sdist 带进 skills-lock.json；CI 干净 checkout 才恰好躲过，PyPI 上 1.4.3 无此问题。本轮已按 ADR 0037 落最小改法（exclude 补 tests / spikes，见 ③）。**倾向**：再进一步改显式白名单 `include = ["/<import 包>", "/README.md", "/LICENSE", "/pyproject.toml"]`（模式须带前导 `/` 锚定，实测不锚会漏进 core/tests/README.md）+ `ignore-vcs = true`，并在 `.github/scripts/check_dist_metadata.py` 加第五条断言「每个 sdist 顶层目录集 == 白名单」；要先定 novaact 的 Dockerfile 去留（现随 sdist 发出；按 ADR 0037 决策 5 / 0038 基础镜像由发布方 CI 从 checkout 构建、不从 sdist 取，可剔）。
- **D4 delete-worker 占位文案**（deploy_aws cli.py 约 304 行 description 与约 513 行 print；deploy-cli-workers#3 UNCERTAIN + comment-terms-cli-deploy-tools#15 单票 CONFIRMED）。两处逐字复述 ADR 0038 重议闸门那句「落地时套 push-worker 同一套清理语义（退休 tag + 静默期 + 运行中 run 引用检查）」。争点：「落地 / 语义」在别的用户面（`__main__.py` 三条提示与 user guide）是现行用法，单点判违规不自洽。**倾向**：只改义项外来的两个词——「落地时」→「将来提供时」、口语动词「套」→「沿用」，中间句改产品语言（同 user guide cloud-backend.md 的「退休满一段时间且没有未结束的 run 引用才真删」口径，不写死 1 小时、真源是 `workers.RETIRE_QUIET_PERIOD`），两处共用一个模块级常量；「清理语义」保留。
- **D5 trigger_eval 的宿主隔离**（skills/gherkai-evals/trigger_eval.py；tools-scripts#6，两票分裂）。视角 A：ADR 0043 决策七的「前置断言 + `--setting-sources project`」限定主语是行为评测两臂、触发率线另有「触发率的测法」条且已满足；视角 B：实测 `--setting-sources project` 仍能发现项目级 `.claude/skills/`，加上它安全。**倾向**：只加前置断言 `assert_no_installed_skill(Path(tempfile.gettempdir()))`（复用 materialize.py 现成函数、放在建临时项目之前），挡「有人 `skill install --global` 过」这一种污染；`--setting-sources project` 是测法改动，会让历史触发率读数（24/25）失去可比性，先回写 ADR 0043 决策七与验证节再加。
- **D6 注释与 docstring 层的「用户 / 使用者」→帽子名**（四片同报：core-domain-model#4、cli-render-deploy-skill#4、deploy-cli-workers#7、comment-terms-core-runtime#8；全仓生产 py 约 100 处、测试注释另约 13 处）。CONTEXT「使用方」条 `_Avoid_: 用户、使用者（限能指明帽子时）`，ADR 0045 决策六 / 八已把 code 注释归入人读层，故这批在规矩内属欠扫；上一轮术语传播（239e5a8）明确没纳入。**倾向**：单开一个批次做（纯文字、零回归），逐处判帽子——deploy 侧恒为「部署方」、写关键字的是「feature 作者」、改注册表的是「测试开发」、指不明的写「使用方」；操作系统用户义（跨用户 / 本用户 / 用户级目录）与固化复合词不动。
- **D7 test_conditional_writes 的 real_aws 承诺**（core-stores#3）。模块 docstring 第 4 行承诺「真 DDB 复验单列（test 末 real_aws）」，文件从建档起没有过 real_aws 用例。**倾向**：补两条 real_aws 用例（CAS 抢占只成功一次；同 HWM 的 stale 投影不把终态 job 刷回 running），需在跳板机对真 DDB 运行一次；若判「ADR 0034 地基实测已足、不进回归套」，则把第 4 行改成「真 DDB 上的条件写行为由 ADR 0034 地基实测坐实，本文件只跑 moto、不作真 DDB 复验」（ddb.py:166 的注释本轮已改成此口径）。
- **D8 FargateEngine 的 `artifact_s3` / `sdk_artifact_dir_env` 带 `None` 缺省**（core-exec-report#4，low）。cloud 下两者必注、漏传即静默丢产物（注释自陈实际运行暴露过一次），与同族不变量（0038 显式 revision）「必给关键字、漏传即在装配点炸」的口径不一致。**倾向**：改必给关键字（`artifact_s3` 仍容 None 表达显式不上传），唯一生产构造点 compose 不变，测试 helper 照传；低优先。
- **D10 用户文档与 skill 里 Run 义的「本批 / 整批 / 这一批 / 批次」**（落地复核时发现：docs/user-guide 六篇约 21 处、随包 skill 四篇约 10 处仍用退役说法；CONTEXT「Run 数据模型」条 `_Avoid_: 批次、一批`，但 `RETIRED_TERMS_WORDS` 没有任何「批」形态，故护栏零拦截）。本轮只改了与 code 文案逐字孪生的三处（running-and-results.md 的 `--fail-fast` 两句、skill 两处 `--tunnel-ttl` 的「本批各 job 预算之和」）。**倾向**：按 ADR 0045 决策八走一次传播——人读层全改成「这个 run / 本次运行」，清零后把「本批」「整批」「这一批」「批次」四形态加进 `RETIRED_TERMS_WORDS`（不加裸「一批」——「一批用例」是「一组」义、合法）；属 doc-health 面，可并入下一轮或单独一批。
- **D9 两个基础镜像 Dockerfile 的 `DEBIAN_FRONTEND=noninteractive`**（release-chain#5，DEAD medium，CONFIRMED）。两份 build 里零 apt / dpkg 命令（git 全史亦零），该变量只对 apt 有意义，且会随镜像 ENV 留给使用方定制层。**倾向**：两引擎同删（novaact 续行 ENV 改成两行；midscene 整行删）；若保留则补注释「基础镜像自身不装系统包，此项只为使用方定制层里可能的 apt 预留」。历史归因按「照抄 Debian 系样板、出生即无消费者」记，不是「曾装 chromium 系统库时代的残骸」。

## ③ 可直接改（CONFIRMED 客观类，本轮已落；按文件组）

每条 = 位置 · 类别 · 一句问题 · 改法。行号为复盘时行号。

**core**
- project.py:296 与 schedule.py:302 · VIOLATES 0039 · 用户可见的 JobResult.message 带 wire 事件名 `scope_done` 与归约行话「矛盾形态」 · 改为「worker 正常退出但没有报完这次运行的结果——按错误处理（详见 worker 日志）」，判据进紧邻注释，test_project.py 断言同步。
- schedule.py:197/228/235/271 · DEAD · `self_stopped` 只写不读（两个赋值点随即 return，271 行读到的恒 False） · 删变量、271 行只判 deadline，265 行与 test_lifecycle_states.py:224 的注释翻成机制表述；ADR 0031:38-41/181 与 internals/verdict-model.md:96 的同名引用随文档批改。
- schedule.py:206 · STALE 术语（用户可见） · 「fail-fast：批次已中止」 · 改「本次运行已中止」，test_report_store.py:395/399、cli/tests/test_render.py:251 引文同步；ADR 0031:17 引的是「背景」节里改名前的旧文案、属历史描述，不动。
- fargate_engine.py:303/375/348 · VIOLATES 0039 · 两条 warning 通篇协议行话（events 断号 / seq / 写者侧丢失 / 强一致读）且不说后果与处置；RuntimeError「连续 N 拍 / 按 error 收敛」 · 改说「本次报告里这部分执行明细会缺失 + 处置」（不承诺判定不受影响；_final_drain 带出 scope 标识），判据与「丢 scenario_done 判定可能偏乐观」的风险进注释。owner 若认为 core 协议级诊断属 contributor 面，正解是降 debug，不是维持行话。
- model.py:63 / wire.py:76 / features/wikipedia_robustness.feature:4 · STALE 术语 · 「种类A」 · →「判定抖动」。
- model.py:82 · STALE 术语 · 「框架不追单价表」自指 · →「gherkai 不追」。
- scope.py:113/134 · STALE 术语（一处用户可见） · 裸「墙钟预算」 · →「job 墙钟预算」。
- reconcile.py:57/122/127、adapters/_atomic.py:10、result_store/local.py:37、report_store/local.py:96、runtime detached.py:153、core/tests/test_reconcile.py:121、test_local_result_store_atomic.py:2 · STALE 术语 · 角色义「推进者」 · →「推进器」（比较式「取较推进者」不动，见 ⑤）。
- run_store/ddb.py:166 · STALE 悬空指针 · 「真 DDB 实测……见 test」而仓库无真 DDB 条件写测试 · 改指 ADR 0034 地基实测 + 说清单测是 moto 对拍。
- event_log/__init__.py:5、sqlite.py:48 · STALE 自相矛盾 · 包 docstring 把 events 表 PK 写成 scope_id · 改为「镜像 DDB 的单 PK 段 (scope_id, seq)，DDB 侧 PK=run_id#scope_id」。
- core/tests 十余处 docstring / 注释 · STALE 悬空指针 · 施工坐标 P2/P3/P3b/P4a/P4d、会话坐标 review #N / #1（ADR 0028） · 换成 ADR 节名或自明事件描述（test_reconcile / test_cloud_reconcile / test_project / test_sqlite_event_log / test_conditional_writes 第 1 行 / test_report_store / test_schedule / test_persist / test_subprocess_engine）。

**runtime**
- detached.py:25 · STALE 过时理由 · 「compose 要惰性 import 防环」而 compose 不 import detached、环不存在 · 注释改「叶子模块（零依赖）」；惰性 import 上提列入 ④。
- detached.py:82/262/9、tunnel_host.py:4 · STALE 术语与包名 · 「事件管道」「预检」「gherkai 层」 · →「事件通道」「run 存在性检查」「gherkai_runtime」。
- compose.py:752 · STALE 注释失真 · `_make_*` 钩子注释说「只供 cli 测试 monkeypatch」，实为四处跨包生产消费 · 改注释；改公开名列入 ④。
- runtime/tests/test_detached_launcher.py:1 · P3b → 「本机后端」。

**cli**
- __main__.py:225 · STALE 文案与行为相反 · run --json help 说「不打进度」，进度实走 stderr、只有 --quiet 静音 · 改「标准输出只打机器可读 JSON（不打文本汇总；进度与诊断照常走标准错误，要一并静音再加 --quiet）」；user-guide running-and-results.md:98 同句随文档批改。
- __main__.py:384/385/386 · VIOLATES 0039 · help 带内部名 meta / RunState / DDB · 改产品语言（提交记录 / 这个 run 的运行态 + 产物落点 / 定位云端后端）。
- __main__.py:224/345/950/1248、323（submit help「提交一批 .feature」）、897（注释「全批 / 整批」） · STALE 术语（用户可见） · 「整批 / 本批 / 这一批 / 一批」 · → run；逐字孪生的 user-guide `--fail-fast` 两句与 skill 两处 `--tunnel-ttl` 说明同步。其余用户文档残留见 D10。
- __main__.py:885/922/1544/1161、cli/tests/test_main.py:71 · STALE 悬空指针 · 退出码指给 cli/README（已缩成入口页）与 ADR 0021（已被 0022 取代、不谈退出码）、旧命令名 `cli run` · 改指 ADR 0030 决定七与 user guide「退出码」节、`gherkai run`。
- __main__.py:1230/1232、cli/tests/test_tunnel_cli.py:233/271/316 · STALE 口头语与退役词 · 「烧钱」「整批 job」 · →「计费 / 产生 AWS 费用」「整个 run 的 job」；__main__.py:1174「S3/本地路径」→「产物指针」；__main__.py:1157 plan 冲突的 stderr 警告与 render.py:159 同措辞（「请测试开发收紧注册表里的匹配模式」），test_main.py 断言同步。
- render.py:218 · STALE docstring 漏口径 · 只说 --all 展开 passed，漏 --step 点名 · 补齐。
- render.py:159 · STALE 角色词（用户可见） · 「工程侧」 · →「测试开发」。
- deploy.py:105-106 · BUG 文案 · 冲突诊断把用户给的 flag 原样插进建议命令并统一说「看变更集」，对 --bootstrap 与 --synth-only 都错 · 改指代式表述，test_deploy_cmd.py 补尾句断言。
- cli/__init__.py:6-7 · STALE 包名 · 「平级包 gherkai」（现为本包发行名） · →「gherkai_runtime」。
- cli/tests/_doc_rules.py:4、test_package_readmes.py:1/59/64 · STALE 悬空条名 · CLAUDE.md「README / DEVELOPMENT 分层」条已改名；根 DEVELOPMENT.md 已改 CONTRIBUTING.md · 改指现行条名与文件名。

**deploy_aws**
- lambdas/reconciler.py:174-183 · BUG · 超时处置一次把两次 ListTasks 的全部 ARN 传给 DescribeTasks（硬上限 100）、ListTasks 未翻页 · 翻页 + 分批 + 找到即停，_FakeEcs 模拟真实约束补两条测试。
- lambdas/reconciler.py:439 · BUG · 防御性超时扫是 best-effort 双保险，却是 `_tick_runs` 里唯一没做失败隔离的调用，抛出即连坐同批其它 run · 包 try/except，产品语言日志，理由进注释，补测试。
- workers.py:672/905/867 · BUG · `--profile` 不存在时 make_aws 在 try 之外抛裸 traceback（NoRegionError 同形） · 加 `_connect` 钩子归退出码，test_workers.py 补用例。落地复核真跑发现更早一步同症：deploy_aws cli.py 的 `_resolve_target`（未给 region 时回落读 profile config，`Session(...)` 构造期即抛）在六个动作入口裸着，故加 `_resolve_target_or_report` 归口（bootstrap / push-worker / list-workers / `_run_cdk` / `_guard_vpc_spec` / `_worker_image_steps`），test_provider.py 补用例；改后三条命令真跑核过退 2 带诊断。
- workers.py:337 · DEAD · `_retire` 的 bool 返回值全仓无消费 · 改 -> None。
- workers.py:730 · VIOLATES 0039 · 「本命令住 gherkai-deploy-aws」分层行话 · 改「本命令来自部署包，随 gherkai[deploy-aws] extra 安装」。
- reconciler.py:316、exit_observer.py:87 · STALE 术语（Lambda 日志） · 「后台批次」 · →「提交到后台执行的 run」；docs/internals/execution-and-reconciliation.md:157/160 逐字引用该日志的两处随文档批同步。
- exit_observer.py:82、stack.py:663、tests/test_lambda_handlers.py:75 · STALE 术语 · 「本框架」 · →「gherkai」。
- stack.py:277-279 · STALE 过时理由 · cpu/memory 注释说容器内运行 chromium，实际浏览器在 AgentCore 云端 · 改真实理由。
- cli.py:4 · STALE 枚举失真 · 模块头 import 面清单漏 boto3 / container / workers / compose 的惰性 import · 改准。

**engines/novaact**
- run_scope.py:933/339 · STALE 注释与 code 不符 · 「三层 with 已退出」（实为两层，`with wf` 仍在栈上）；「与中断兜底提前上传并列」（Nova 无此机制，ADR 0032 明记） · 改准。
- lib/artifact_upload.py:278 · STALE 声明失真 · 「文案与 Midscene 上传器同形」已不真 · 改「同一判据」。
- user_steps.py:6 · 「用户的 CWD」→「使用方的 CWD」。
- tests/test_artifact_upload.py:259、tests/test_transient_network.py:96 · STALE 会话坐标 · 「锁住 C1 修复」「本次新加白名单」 · 翻成自明描述。
- Dockerfile:57 · STALE 指针 · 「ADR 0033 决策 C」（决策 C 在 0016） · 改与 midscene 侧同形。

**engines/midscene**
- run-scope.mts:427-429 · BUG · cleanup 重入守卫是布尔而非在途 promise：SIGTERM 落在正在运行的 cleanup 中时 handler 的 cleanup() 立即返回、process.exit 截断在途 StopBrowserSession，会话静默泄漏且退 0 · 抽可测的在途 promise 守卫（final 重入者等在途完成、仍有未释放会话则再跑一次 final，失败可观测），建连重试分支改 reset，补两条测试。
- run-scope.mts:657 · VIOLATES 0039 · 报告提前上传失败日志承诺「后面还会再试」（文案不变量明令不许） · 改「这份报告可能最终没能上传」，注释改陈述事实（停止信号路径有 interruptSnapshot 再传、网络耗尽与异常两条不 flush）。
- artifact-upload.mts:252、run-scope.mts:210/214、evidence.mts:420 · STALE 两引擎同物异名 · 「排障截图 / 排障证据」vs Nova「证据截图 / 本步证据」 · 对齐 Nova。
- run-scope.mts:10/16/298、deterministic.mts:11、deterministic.steps.mts:12/39、resolve-hook.mts:5-6、agentcore-sigv4.test.mts:89 · STALE 术语与过时理由 · 「不追 Qwen 单价」「裸定位链」「用户 / 使用者」「框架内建的那几条」（只有一条）、fork 时代的「取消注释并改成你的项目所需」 · 逐处改准。
- spikes/03、05 · STALE 与 ADR 0044 不符 · modelConfig 一半跟现值（GPT）一半钉旧开关 `MIDSCENE_USE_QWEN3_VL: "true"`，重跑即「GPT 模型 + qwen3-vl 适配器」 · 改 `MIDSCENE_MODEL_FAMILY: modelFamily()`；spikes/01 注释同步。

**tools / skills 评测脚本 / 发布链**
- tools/build_diagrams.mjs:107-110 · BUG · `--no-deliver` 下 SVG 从旧 HTML 导出却按当前 JSON 盖指纹，护栏「改了图源没重导」被伪造成绿 · 沿用旧 SVG 的指纹（内容判据，不用 mtime——git checkout 后 json 比 html 晚约 0.2 ms，用 mtime 会误杀合法重导）。
- tools/build_diagrams.mjs:58/61 · DEAD · 两个 export 无 import 方且模块顶层 `await main()` 使 import 必产生副作用 · 去掉 export；补 `--dir` 用法行。
- skills/gherkai-evals/materialize.py:134/165 · BUG · `--prepare-cli` 结尾 chmod -R a-w，重新准备时 rmtree 只读树必抛 PermissionError，脚本自己的「重新运行 --prepare-cli」提示走不通 · rmtree 前先 chmod u+w（抽 `_rmtree_prepared`）。
- skills/gherkai-evals/summarize_runs.py:29 · DEAD · `d["_run"]` 写后无读 · 删。
- skills/gherkai-evals/trigger_eval.py:10 · STALE docstring 与 ADR 0043 决策五相反 · 「没有 .feature 时只在用户明说 gherkai 才接管」 · 改为项目级信号规则。
- tools/e2e_harness.py:48 · STALE 不存在的 env · 读 `CLAUDE_JOB_DIR` 恒回落 /tmp · 直接 /tmp；tools/e2e_harness.md:42/107 随文档批改。
- tools/events_wallclock.py:7、tools/graphify_refresh.sh:5/20 · STALE 悬空指针 · `engines/*/lib/event_sink` 两引擎都不匹配、`guides` 目录已改 internals、根 DEVELOPMENT.md 已改 CONTRIBUTING.md · 改准。
- .github/scripts/release_notes.py:15、cli/tests/test_release_notes.py:3-4 · STALE 与发布链不符 · 「发布链用 uv run --no-project python」，Release 正文渲染步实用 runner python3 · 改准。
- 五份 pyproject `[tool.hatch.build.targets.sdist]` · VIOLATES 0037「测试与 spike 不进发行包」 · sdist 只排 DEVELOPMENT.md，PyPI 上 1.4.3 的 sdist 实含 tests/（core 28 个文件、novaact 18 + spikes 2） · exclude 补 tests（novaact 加 spikes），真构建核顶层；`.github/scripts/check_dist_metadata.py` 加断言 5「每个 sdist 顶层不含 tests / spikes」（对 `uv build --all-packages` 真产物退 0、对注入含 tests/ 的假 sdist 报错，两侧都验过）；白名单见 D3。
- tools/render_skill_contract.py FORBIDDEN_REWRITES · VIOLATES 0039 / 0043 决策六 · 随 wheel 发行的 skill 副本逐字带内部类型名 RunResult / RunState / RunReport · 登记三条改写、重渲染副本。

**已驳回（REFUTED，不落改）**
- cli-main#6 explain 带 scope_id 未命中时调 load_all 需 ListBucket：S3 语义下缺 ListBucket 时 GetObject 对不存在的 key 返 403 而非 404，`load_job_result` 在前一行就抛、1731 行不可达，失败场景不成立。可选尾巴（属文档精度，移交 doc-health）：ADR 0042 决策四「带 scope_id 只需 GetObject」宜补「对象不存在时 S3 需列举权限才返『不存在』」；1859 行诊断 extra 可改成无条件提列举权限。
- novaact-worker#1 `ensure_workflow_definition` 与 `CreateWorkflowRun` 在建连重试域之外：ADR 0028「留口子不实现」第 133 行逐字登记了此缺口并接受（「仍归 engine_error。已知小缺陷，可随真实失败样本扩充」），code 与 ADR 一致。要收口须先改 ADR（并把 `Workflow.__enter__` 的 CreateWorkflowRun 纳入幂等清单），再动 code。
- deploy-stack-lambdas#3 ListTasks 同传 startedBy 与 desiredStatus 会被拒：AWS 文档「must be the only filter」不是硬校验（同页把 cluster 也叫 filter），Airflow ECS reattach 与 MBTA 部署脚本都在用同一组合。可选：在 `_handle_timeout` 注释里记一句该组合合法（只写有证据的部分）。
- dead-sweep-python#3 `severity()` / `_STATUS_SEVERITY` 生产零调用：ADR 0031 决定二把它立为「绝不拿字符串比」这条红线的物化，docs/internals/verdict-model.md §4 已完整记录「约定而非计算引擎、单测锁定、新增终态两表同改」，属有据保留。可选（doc-health）：ADR 0031「重议 / 留口子」段「集中改一处即可」收紧为「数值定义集中在表、配色表须同批改」。

## ④ 重构 / 主观提案（待批；每条附倾向）

- R1 runtime compose.py:44-52 删 names 的 re-export 薄壳：task_def_name 在 compose 内零使用，cli 与 reconciler 已直接 import names、同一表达式里混用两条路径；四处生产调用改指 `_names`，runtime/tests/test_compose.py 断言改指 names。**倾向做**（机械替换、无行为变化）；退一步只删 task_def_name 那一项。
- R2 compose.py `_make_ddb_table` / `_make_s3_client` / `_make_lambda_client` 改公开名：被 cli 与 tunnel_host 以私有名跨包消费。**倾向暂不改**（gherkai 与 gherkai-runtime 同版本 pin，无兼容风险；注释已改准）；若守「下划线 = 可随时改」的信号则一次改干净。
- R3 detached.py 四处函数内 `from gherkai_runtime import compose` 上提为模块顶层（环不存在，tunnel_host 已是顶层 import）。**倾向做**。
- R4 detached.py:254 与 compose.resolve_cloud_target 各写一份「profile = flag > AWS_PROFILE」：抽 `compose.resolve_aws_identity(region, profile)` 两处共用。**倾向做**。
- R5 tunnel.py:141-145 就绪超时路径自拼 os.kill(SIGTERM)，绕过唯一拆除面 `stop_tunnel(pid)`：改调 stop_tunnel。**倾向做**（三行变一行、零行为变化）。
- R6 deploy_aws cli.py `_stored_vpc_hint` 缺 --vpc 提示路径真打两次 AWS 读且用 botocore 默认超时与重试，网络不通时把参数错误拖成分钟级：给提示路径单独短超时句柄（connect 2 s / read 3 s / 不重试）。**倾向做**。
- R7 ci.yml python job 加 `actions/setup-node`（deploy_aws 的 CDK synth 测试经 jsii 起 node，现吃 runner 默认 Node）。**倾向加**（env 已有 NODE_VERSION）。
- R8 pages.yml deploy job 补 `contents: read`（checkout 现靠公开仓库匿名读，release.yml 四个 job 都显式给了）。**倾向补**。
- R9 tools/e2e_harness.py:119 env 用 `{**os.environ, …}` 纯加法、没有 adapter 的 `_scrubbed_environ` 那步 scrub，宿主 shell 的 GHERKAI_* 会直达 worker：复用 compose 的起手式（先把 `_scrubbed_environ` 提成公开接缝）。**倾向做**。
- R10 skills/gherkai-evals/materialize.py MACHINE_ROOT 与 cli/tests/test_skill.py ABSOLUTE_PATH 根集逐字重复：提进 `_doc_rules.py` 单源。**倾向抽取**；若不愿让评测脚本依赖 cli/tests，则加一条护栏断言两份相等。
- R11 midscene run-scope.mts:364 自述对象的 `schema_version` / `engine` 裸字面量：与 Nova 同形改具名常量（evidence.mts 导出 ENGINE）。**倾向做**。
- R12 schedule.py:84-105 `_heartbeat_wrap` 的 `try … finally: pass` 空结构：删掉、注释上移。**倾向删**；保留则首行改「有意为空」。
- R13 skills/gherkai-evals 五处「第三轮 eval 3 / eval 9 实测」轮次坐标：ADR 0043 验证节已把五轮逐条内联，**倾向保留编号 + 补「ADR 0043 验证节」锚点**；按红线严格执行则翻成自明事件描述。

## ⑤ 主观发现（口吻 / 已评估不动）

- core project.py:188/222、run_store/local.py:173/184「取较推进者」：比较式「更推进的那个态」、与 ADR 0034 原文同形，不是角色义退役名，**不动**（两片意见相左，取 comment-terms-core-runtime 的判法；术语 grep 时按「较推进者」排除即可）。
- compose.py:430 局部函数名 `_leg`：退役隐喻「腿」在标识符里的残留，但 ADR 0032/0033/0043/0044/0045 正文尚有 8 处「腿」、owner 上轮已定「腿 / 皮 两批不改」，**不动**。
- deploy_aws app.py:8「context 旋钮」在 ADR 0037 决策 6 的逐字引文内：**不动**（引文对原文；真要清应 ADR 与 code 同批走 doc-health）。
- cli-main：上轮驳回 R14 涉及的 `--scenario / --scope` 筛选谓词：本文件在热区但前提未变（仍是两趟 parse、谓词无状态），**不重提**。

## ⑥ 各片覆盖记录（读了什么、怎么核的；详见 workflow 结果）

- core-domain-model：六文件逐行；model.py 全部 dataclass 字段与 errors.py 异常逐个 grep 消费者，无悬空字段；0031 七态 / severity 数值 / TERMINAL 集逐项对 ADR；0025 规划规则逐条对 scope.py；0022/0036 core 零 capability 分流逻辑。
- core-protocol-schedule：wire 7 个事件类型与两 worker 真 emit 字面量三方差集、字段级差集；model↔serialize 字段差集全对上；schedule / reconcile import 面无 boto3 / store / subprocess；ports 每方法有实现与调用点（ScenarioDone 的 reportRefs 是 0024 明写协议面，前向口子不报）。
- core-stores：0030 决定四～七、0034 机制一～四逐条对 local 与 ddb 两实装；DEAD 全仓 grep 有生产调用；_boto.require_boto3 六处与模块头清单相符。
- core-exec-report：0038 显式 revision（只原样传注入的 task_definition）、0024 终止契约与读一致性、0034 job timeout 武装、0029 键布局与 job-in tag 规则、0027+0042 渲染单源逐条核；无 reaper / materialize 残骸。
- runtime-compose：compose 与 names 全部顶层符号逐个 grep；core / runtime 全部 os.environ 只在组合根；0016 决策 B/C、0044 单槽与默认 id 不双写、0037 命名单源核过。
- runtime-detached-tunnel：三文件全部公开符号 grep（含 `_reconcile` / `_tunnel_watch` 隐藏子命令与 setsid fork 字符串装配）；0034 机制二 / 四与 status --wait 并存、0035 决策 1-3 对照。
- cli-main：2320 行分七段读完；AST 列 44 个私有符号 + 全部 add_argument dest 做悬空差集，零 dangling；AST 抽全部 help / print 字面量按内部词与标识符形态扫（只剩 meta / RunState / DDB）。
- cli-render-deploy-skill：跨包措辞双写只两份且逐字一致；0042 原因渲染口径一致；序列化真源全从 core；全部符号有调用点。
- novaact-worker：0024 事件配对与 _emit_step_done 单点、0042 evidence 字段逐字段、0029 上传四级、0032 grace 组成、0004 workflow、0036 steps 发现规则、0022 不碰 feature 逐条核；AST 121 个顶层符号全有引用。
- midscene-worker：14 文件 + package.json / tsconfig / Dockerfile 入口一致；协议顺序、派发四级、0028 重试常量与 Nova 逐项对拍、0029 四级上传、0042 evidence 全字段、grace 下限 31 s 算法、0044 family 推断表核过。
- deploy-stack-lambdas：**IAM 授权面用真 synth 导出全部 IAM 语句对 ADR 0033 资源清单与最小权限表逐条对账**，无缺无多给（exit-observer / reconciler / kicker / 两个 task role / job-in tag 权限归属）；0034 reconciler 两道语义闸与 timeout 三分支；模板数字（日志 14 天、stopTimeout 120、GSI）核过。
- deploy-cli-workers：真构 parser dump 命令面对 ADR 0037 决策 6 与 user guide 选项表，零差集；0038 八步次序与前置校验；全部符号 grep。
- release-chain：**真构建五个 sdist + 从 PyPI 下载 1.4.3 实物比对**；测试套差集（git ls-files tests/ vs testpaths vs ci.yml）无遗漏；依赖声明差集（三个 try/except 内的可选 import 不报）；package.json 与 src 双向一致。
- tools-scripts：脚本点名的 CLI flag / JSON 键 / 事件字段 / 表属性名逐条对 argparse、wire、names、event sink；render_skill_contract --check 真跑；graphify_refresh.sh 依赖的外部输出串对着已安装的 graphify 源码核。
- dead-sweep-python：55 个 .py、749 个 class/def（去 dunder 717）+ 383 个常量与字段，全仓文本引用扫并**把注释与 docstring 涂空后重扫**（首轮 67 个假阴性由此暴露）；生产零引用候选 5 个，4 个落红线（Provider entry point、@deterministic 注册、run_state_from_result 有 ADR 记录、serialize.from_dict round-trip 契约），1 个已报并被驳回。
- dead-sweep-ts：65 个 export 与非导出顶层函数逐个 grep，零引用 export 为零；只被测试引用的一批落红线；index.mts 的公开 API 由使用方 steps 文件消费。
- comment-terms-core-runtime：CONTEXT 75 词条 / 54 行 Avoid → 108 条真值 + COLLOQUIAL / RETIRED_TERMS 两表；70 文件 2907 条注释与 docstring 单元，**去空格归一化第二遍**抓到「种类A」；另义词逐类排除（worker 定位链 28、ngrok 19、fixture 23、主键 / key 102、重试 43、路径 171、锚点 5、同一批 11、取较推进者 4、轮次义 8）；COLLOQUIAL 与「档」「跑」在本片 0 命中。
- comment-terms-cli-deploy-tools：112 条真值；52 文件 2614 条单元，原始命中 418 条逐条判；用户可见字符串两轮 AST 扫（语义泄漏词表 + 五个生产包全部 >5 字符 def/class 名对撞），唯一真泄漏 RunState。
- comment-terms-engines：117 条真值；novaact 31 个 .py + midscene 22 个 .mts + 5 个 spike + 两个 Dockerfile；17 处高信号命中判掉 15 处另义；两引擎全部 log / throw 文案逐条做 0039 语义检查。

## ⑦ 跨包扫记录

- 死码扫（Python 717 符号 / TS 65 导出）：真死码 5 处（`self_stopped` 写后不读、`_retire` 返回值、`d["_run"]` 悬空字段、build_diagrams 两个不可用的 export、`DEBIAN_FRONTEND` 无消费者），全部经独立 grep 复核。「只被测试引用」的生产符号按红线不报，清单在各片覆盖记录。
- 术语扫：三片合计约 8100 条注释与 docstring 单元；真命中 = 推进者 9、种类A 2、批次 / 后台批次 / 整批 6、框架自指 7、事件管道 1、裸墙钟预算 2、裸定位链 1、用户 / 使用者约 113（待 D6）、口头语「烧钱」3；悬空指针 = P 编号 11、review #N 7、C1 / 本次 2、journey / WP 0。COLLOQUIAL 表其余项与量词「档」在全部注释里 0 命中（上两轮清扫在注释层是干净的）。
- 护栏边界确认：注释与 docstring 不在 `_doc_rules.py` 两张表与 `test_user_facing_messages.py` 的任何扫描面内，本轮全部注释层命中都靠人读；用户可见字符串的语义泄漏（meta / RunState / 住 / 后面还会再试）都在正则外，正是 ADR 0039「靠 review」那一类。

## ⑧ 上轮驳回核对与移交接收

- 上轮驳回 R14（--scenario / --scope 谓词带副作用省第二趟 parse）：涉及文件 cli/__main__.py 在热区，重评后前提未变，沿用驳回、未重提。
- doc-health 第 7 轮移交的 VIOLATES_ADR：D1（推进 Lambda 缺 events 表 PutItem）已在 bda8c25 落地，本轮 IAM 对账确认无其余缺口；无新的待接收项。
- 本轮移交 doc-health（文档精度，不在 code-health 落）：ADR 0042 决策四「带 scope_id 只需 GetObject」补 S3 语义限定；ADR 0031「重议 / 留口子」段 severity 落点表述；ADR 0031:17（背景节）引的旧文案与旧状态是决策前的历史描述，是否加「原」字框定交 doc-health 判；ADR 0028 若要收 `ensure_workflow_definition` 口子先改「留口子不实现」条；ADR 0039 面一按 D2 结论补例外。随本轮 code 改动必须同步的文档（ADR 0031:38-41/181 的 `self_stopped` 引用、internals/verdict-model.md:96、user-guide running-and-results.md:98 的 `--json` 行、tools/e2e_harness.md:42/107、ADR 0024:120「Qwen token 单价」）已在文档批改掉。另发现 user-guide running-and-results.md:99 `--steps-dir` 行「整批拒绝运行」用了 Run 的退役说法「批」，与 CHANGELOG 已发行段以外的用户文档是否还有同类残留，交 doc-health。

## ⑨ 方法复盘草稿（落地提交说明用）

- 抓到真问题的规则：VIOLATES [0039] 正则外语义泄漏（6 条 CONFIRMED：meta / RunState / 住 / 后面还会再试 / scope_done / 协议行话 warning）；STALE 的「术语与口吻同查」维度（本轮新加，约 50 处注释层退役名与会话坐标，护栏照不出）；DEAD 全局扫（5 处，其中 `self_stopped` 与 `_retire` 返回值靠涂空注释后重扫）；发布链「失效步骤 / 与 pyproject 约定对不上」（sdist 带 tests，靠真构建 + PyPI 实物比对抓到）。
- 零命中但承担防误伤的规则：[0033/0034] IaC 授权面（首轮，真 synth 对账无缺）；[0037]/[0038]/[0016]/[0022]/[0024]/[0026]/[0027] 形态全部核过无违背。
- 误报形态（两条 REFUTED 同因）：finder 把 ADR「留口子不实现 / 已登记缺口」里接受的现状报成违背（0028 ensure_workflow_definition、0031 severity）。提议 R-a：VIOLATES 判前必读被引 ADR 的「留口子 / 不做 / 重议闸门」节，方法文档「【强制】每片对照相关 ADR」条加半句。
- 重复报：同一处退役名被 3～4 片各报一遍（推进者、种类A、批次）。提议 R-b：术语面只由专门的注释术语扫片负责，模块片只报术语之外的 STALE，减少合并成本。
- 落地机制（按文件归属 7 组并行 + 每组独立逐 hunk 复核 + 回修）本轮抓到 20 条复核意见（2 条 medium：`_resolve_target` 更早一步的同症漏口、reconciler 日志改了但 internals 逐字引用没跟；其余是新写注释的歧义、重复措辞、断言只有否定式），全部回修或登记，值得保留为默认形态。
- 执行卡点：一个验证代理被 API 安全策略误报中止（单票判定）；两条 BUG 的对抗验证靠真跑才定（rmtree 只读树、git checkout 后的 mtime 顺序、S3 GetObject 403/404 语义），「绿≠对」的真跑升级在验证层比在发现层更划算。
