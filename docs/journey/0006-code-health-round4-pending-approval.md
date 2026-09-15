# 代码健康度复盘第 4 轮 — 待批报告

> 类型: 待批报告（批毕落改吸收后删除）

锚点 `5d04676`（第 3 轮落地，2026-09-10）→ HEAD。热区 26 个生产文件 +2996/-230、一跳依赖 21 文件、冷区 38 文件全读。17 个审计分片 + 逐条独立证伪。

客观类：发现 94，进入验证 36 → CONFIRMED 33 / REFUTED 3 / UNCERTAIN 0；另 36 条过时注释/docstring 全部独立验证 CONFIRMED。两批已落地（第一批 32 条 + 第二批 36 条 + 跨组遗留），每组跑包测试全绿；全套 pytest / npm test 见提交说明。17 个分片对「code 大改、ADR 零改」的检查：无缺口。


## 一、请裁定

- **.github/workflows/ci.yml:8 `on.push.branches: [main]`（BUG，已确认）** — ci.yml 的两个自动触发面在本仓库都永不成立：`push: branches: [main]` 指向一个**不存在的分支**（远端只有六个 `feat/*` head，`origin/HEAD -> feat/v1.4-doc-skill`），而 `pull_request` 从未有过 PR。于是「全成员 pytest + midscene npm test + 打包元数据 smoke + 发布 gate 演练」这套推 tag 前的安全网只能靠 `workflow_dispatch` 手动跑（最后一次 2026-09-08），而 release.yml 里没有任何测试步骤——tag 一推就直发 PyPI/npm/GHCR/Release。
  - 复核员：亲自核到，发现的每条事实都成立，且比提交者写的更严重。

**1. `main` 分支不存在（ci.yml:8 的 push 面恒不成立）**：`git ls-remote --heads origin` = 六个 `refs/heads/feat/{v0.x-bdd-spike,v1.0-framework,v1.1-cloud,v1.2-detached-batch,v1.3-local-app,v1.4-doc-skill}`，无 main；`git symbolic-ref refs/remotes/origin/HEAD` = `refs/remotes/origin/feat/v1.4-doc-skill`。分支模型是「一个版本一个 feat/* 分支」，六个分支从 v0.x 到 v1.4 全程无 main，故这个 push 过滤在本仓库整个生命周期里从未匹配过任何一次 push。

**2. `pull_request` 面从未点火**：`gh pr list --state all` 为空。

**3. 四次 `ci` 运行全是 `workflow_dispatch`**：最后一次 34205587700（2026-09-08 08:38，success），同日另有三次 failure；零次 push / pull_request 触发。

**4. 比提交者说得更…
  - 建议：基本采纳原修法，三处收窄/补齐：

**① `.github/workflows/ci.yml:8` 改真值集**：`branches: ['**']`，保留行尾注释里「tag push 不进这里（branches 过滤已排除），发布链见 release.yml」这句——该不变量在 `'**'` 下仍成立（已核 GitHub 语义）。**别写当前默认分支名** `feat/v1.4-doc-skill`（每版换分支、必再漂）；`branches: ['feat/**']` 虽能编码分支模型，但下一次分支改名会重演同一个「静默变哑」失效，故仍取 `'**'`。**别删 `branches` 键**（裸 `on: push:` 会把 tag push 也拉进 ci，破坏 release.yml 独占）。

**② 文案漂移是三处、不是两处**：`ci.yml:3-5` 头注释（「日常提交就炸」现在才真成立）、`.github/workflows/README.md:12` 触发列、**外加 `DEVELOPMENT.md:135`**（原发现漏了这条，同写「push `main` / PR / 手动」）。

**③「发行必须过测试」保持不合并**（同意原发现）：往 release.yml 的 `build` 前加测试 job、让 pypi/npm `needs` 它，是对 ADR 0037 决策 8 的**新增决策**，要人拍板并显式改 ADR，不随本条顺手落。本条只恢复决策 8 已写明的那道前置防线。

**④ 一个已知小代价，建议接受而非加复杂度**：`branches: ['…


## 二、主观 / 重构类待批（未验证；批准后落地、各附测试）


### cli/gherkai_cli/__main__.py

- **R1** STALE_INEFFICIENT/high · :1313 `_render_status / _cmd_run 的产物三行` — 「报告 / 运行元信息 / 判定明细」三行在 status 与 run 两处逐字复制（连 `\n` 前缀与顿号分隔都一样），status 侧的 docstring 还把「与 run 同款」当口头约定维持——文案或键名一改就分叉。
  - 证据：1313-1315（_render_status 终态分支）与 1997-1999（_cmd_run 结束）是同一段三行；`grep -rn '报告: |运行元信息|判定明细: ' cli/ runtime/ deploy_aws/`（去 .md）只这 6 行。唯一差异：run 侧 report_index 键可能缺席（report 写失败被隔离）故用 `artifacts.get('report_index', '<报告写入失败…>')`，status 侧用 compose 给的约定落点、必有该键。_render_status docstring 自述「与 `run` 结束时同款三行（对标输出，S3/本地路径可直接复制）」。
  - 提议：抽一个 `_print_artifact_lines(locations: dict, *, report_index_fallback: str | None = None) -> None`（住 __main__ 或 render），内部打三行、缺 report_index 时用 fallback 文案；_render_status 传 locations、_cmd_run 传 artifacts + fallback。
  - 测试：cli/tests/test_main.py 与 test_backend_cloud.py 里断言这三行的用例（run 终态输出、status 终态输出、report 写失败回落文案）应全绿且不改断言；跑 cli/tests 全套。

- **R2** STALE_INEFFICIENT/medium · :1011 `_cmd_submit / _cmd_run 的共享前置` — run 与 submit 的前置序列（并发校验 → variant 校验 → _load_and_plan → plan 计数行 → steps_dir 解析 → local 档 worker preflight → RunMeta 组装）逐字重复约 15 行，连 --steps-dir 的 help 后缀都抄了两份——_load_and_plan 当初正是为「曾各手抄一份、会漂移」抽的，同一个理由在它外面这一圈仍成立。
  - 证据：submit 1006-1026 与 run 1692-1716 除注释外逐行同形：`_validate_max_concurrency`/`_validate_worker_variant` 两句 + `jobs = _load_and_plan(args)` + `_progress(f"plan: {len(jobs)} job(s)  (default_engine={args.default_engine})")` + `steps_dir = _resolve_steps_dir_for_backend(args)` + `if args.backend != "cloud": miss = _preflight_worker_runtimes(jobs, steps_dir)`；RunMeta 组装（1044-1048 与 1750-1753）六个字段同形。228 与 345 的 `--steps-dir` hel…
  - 提议：抽 `_plan_and_preflight(args) -> tuple[list, str | None] | int`（含四步：两个入口校验 → _load_and_plan + plan 计数行 → _resolve_steps_dir_for_backend → 非 cloud 档 _preflight_worker_runtimes；任一失败原样返回退出码）与 `_build_run_meta(args, jobs, steps_dir, tunnel_headers) -> RunMeta`；run 在其后插自己的 --grace 校验、submit 插 --tunnel-ttl 校验（两者都排在起隧道前，次序不变）。另把 228/345 的后缀提成 `_STEPS_DIR_HELP_SUBMIT_SIDE = _STEPS_DIR_HELP + "…"` 两处引用。
  - 测试：跑 cli/tests/test_main.py（含 run/submit 的退 2 次序用例：votes/并发/variant/steps-dir/preflight 各自的早拒断言）、test_backend_cloud.py、test_tunnel_cli.py（「早拒才真零副作用：隧道一次都没起」那批断言是这次抽取的真护栏）。

- **R3** STALE_INEFFICIENT/medium · :356 `_build_parser（submit 的 --events-table / --cluster）` — cloud submit 的 --events-table 与 --cluster 对这个 run 的执行零影响（云端推进器从自己的 Lambda env 取），它们唯一的作用是**改 preflight 探哪个资源**——给错值只会把「探针指错」伪装成「后端没部署」，与同处注释里「曾在此声明过两个从不生效的 flag，已删」的判据自相矛盾。
  - 证据：_submit_cloud 只用 target.events_table / target.cluster 喂 compose.preflight_cloud_resources（1233-1243），之后 `create_run` 只写 runs 表（ADR 0034）；真正起 task 的 deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py:160/278-279/319-320 读 `os.environ["CLUSTER"]` / `os.environ["EVENTS_TABLE"]`，与 definition 无关。preflight 失败文案（runtime/gherkai_runtime/compose.py:1287-1289 `_hint`）恒说「（用 --prefix=… 拼出）不存在——是 --prefix 配错、还是后端未部署」，而显式 --event…
  - 提议：二选一交人拍板：①删 submit 的 --events-table 与 --cluster（沿用 --subnet/--security-group 的先例，并在注释里补一行「为什么删」的护栏），cloud submit 的探针一律按 --prefix 推；②保留但让 preflight 的错误串区分名字来源（compose._hint 收一个「名字是显式给的还是 prefix 拼的」标记，显式给的改说「检查 --events-table/--cluster 的值」）。别两处都不动。
  - 测试：选①：cli/tests/test_backend_cloud.py 里凡给 submit 传 --events-table/--cluster 的用例改掉，并补一条「submit 不认这两个 flag（argparse 退 2）」，对齐现有的 --subnet/--security-group 护栏；选②：给 compose.preflight_cloud_resources 补一条「显式给名时…

- **R4** STALE_INEFFICIENT/medium · :827 `_load_and_plan（筛选分支的 everything）` — 筛选路径把全部 feature **再完整 parse 一遍**（Parser+Compiler 走第二趟）只为拿「本批全部候选 + tags + 总数」，而这份信息在第一趟里已经完整流过 `select` 谓词——`plan` 对每个 group 的每个成员都调过谓词（含最终被跳过的 group），谓词侧顺手收集即可，零额外解析。这是我这片（`plan` 的 select 接缝）在调用侧的重复计算。
  - 证据：cli/gherkai_cli/__main__.py:822（`jobs = plan(features, cfg, select=select)`）已在 core 内 `parse_feature` 全量解析；:826-827 又 `from gherkai_core.parse import parse_feature` / `everything = [p for f in features for p in parse_feature(f.uri, f.text)]`。core/gherkai_core/scope.py:178-180 证明谓词覆盖全量：`for key, members in groups.items(): picked = members if select is None else [m for m in members if select(m, key)]`——筛空的 group 也是先逐个调…
  - 提议：让 `_build_selector` 返回谓词 + 一个收集容器（或返回一个带 `.seen` 列表的小 callable），谓词每次被调时 `seen.append(p)`；`_load_and_plan` 用 `selector.seen` 替掉 `everything`，删掉第二趟 `parse_feature` 与那行 import。注意两点：候选列表顺序会从「文件书写序」变成「分组序」→ 打印前按 `(p.uri, p.scenario.id)` 排一下保持人读稳定；谓词带副作用要在 docstring 写明（这是本方案的代价，值不值得由人定，故标待批）。
  - 测试：cli/tests/test_main.py 里筛选相关用例（筛空退 2 并列候选 / 「筛选：N/M」一行 / --scope/--tags/--scenario 组合）；补一条断言候选列表顺序与去重（同一 scenario 只列一次）。改完跑 `uv run pytest cli/tests/test_main.py core/tests/test_plan.py`。


### cli/gherkai_cli/render.py

- **R5** STALE_INEFFICIENT/medium · :10 `from gherkai_core.serialize import _ref_to_dict` — cli 跨包 import 了 core 的**私有**符号 `_ref_to_dict`：复用单一序列化真源的意图对，但拿下划线名当接口用——core 侧改名/改签名时 cli 会静默崩，且给「私有可以被外部依赖」立了坏先例。
  - 证据：`grep -rn _ref_to_dict --include=*.py`：定义在 core/gherkai_core/serialize.py:108，core 内部三处调用（146/152/161），唯一外部消费者就是 cli/gherkai_cli/render.py:10 的 import 与 265/289 两处调用。`serialize.py` 的其余共享入口全是公开名（`job_to_dict` / `job_result_to_dict` / `run_state_to_dict` / `to_dict`），只有 ref 这一格是私有名。
  - 提议：在 core/gherkai_core/serialize.py 把 `_ref_to_dict` 改名为公开的 `ref_to_dict`（内部三处调用点同改），如需保留内部旧名可加一行 `_ref_to_dict = ref_to_dict` 过渡；render.py:10 改成 `from gherkai_core.serialize import ref_to_dict`，265/289 两处同改。若判定不值得动 core，则退一步：在 render.py 里注明「依赖 core 私有符号，core 侧改名须同改」并在 core 侧 docstring 标注「cli explain 依赖本函数」——但那是次优解。
  - 测试：改完跑 `uv run pytest core/tests/test_stores.py core/tests/test_report_store.py cli/tests/test_render.py cli/tests/test_cli_json_contract.py cli/tests/test_main.py -k explain`；`grep -rn '_ref_to_dict' --…

- **R6** STALE_INEFFICIENT/medium · :380 `_step_lines / render_text 的短路旁注字面量` — 「⚠ 因前置 step error 被跳过（未执行）」这句面向用户的话在同一个文件里内联了两份（run 文本 + explain 文本），第三份在 core 的报告页；而本文件已经把同类整句提示（`_NO_RECORD` / `_ABORTED_PARTIAL_HINT` / `_EVIDENCE_MISSING_TEXT`）都提成了模块常量——这一句漏了，且 guides 逐字引它，任一份漂移就是三处文案+文档不一致。
  - 证据：`grep -rn '因前置 step error 被跳过' --include=*.py`：cli/gherkai_cli/render.py:87（`render_text`，带前导两空格）、cli/gherkai_cli/render.py:380（`_step_lines`，无前导空格）、core/gherkai_core/adapters/report_store/local.py:283（index.html 的 `<span class="taint">`）。同文件第 200/203/204 行已为 `_NO_RECORD` / `_ABORTED_PARTIAL_HINT` / `_EVIDENCE_MISSING_TEXT` 建了常量。docs/guides/artifacts-and-evidence.md:96-98 的提示语对照表逐字引用这批句子。
  - 提议：在 render.py 的 explain 常量区（第 200 行附近）加 `_SHORTCIRCUIT_NOTE = "⚠ 因前置 step error 被跳过（未执行）"`，第 87 行改 `note = f"  {_SHORTCIRCUIT_NOTE}" if st.shortcircuited else ""`、第 380 行改 `bits.append(_SHORTCIRCUIT_NOTE)`。core 侧那份跨包、不强求合并（cli 不能被 core import），但在 core 的那行加一句注释指明「与 cli 渲染同款措辞，改一处要改两处」。
  - 测试：跑 `uv run pytest cli/tests/test_render.py cli/tests/test_main.py -k 'explain or run' core/tests/test_report_store.py`（这几处都有断言旁注原文的用例）。


### core/gherkai_core/adapters/report_store/local.py

- **R7** STALE_INEFFICIENT/medium · :259 `_render_index_html（job 行 err / step 行 serr 两处原因渲染）` — job 行与 step 行的「原因」渲染是同一套两分支逻辑抄了两遍，且已经漂移：job 分支在 message 为空时仍拼出一个吊着的冒号（`error_type: `），step 分支（本轮新加）把冒号做了条件化。该抽取的重复 + 已发生的分叉。
  - 证据：local.py:259-262 `if jr.error_type: err = f' <span class="err">{esc(jr.error_type)}: {esc(jr.message or "")}</span>' else: note 分支`；local.py:275-278 `if st.error_type: serr = f' <span class="err">{esc(st.error_type)}{(": " + esc(st.message)) if st.message else ""}</span>' else: note 分支`——同一意图、两种空 message 处置。当前 job 级 `error_type` 非空时 message 必有值（core/gherkai_core/schedule.py:205-302 与 project.py:277-293 每处都成对赋值），故吊冒号眼…
  - 提议：抽一个模块级私有助手 `_reason_html(error_type: str | None, message: str | None) -> str`：有 error_type → `' <span class="err">{esc(error_type)}{": " + esc(message) if message else ""}</span>'`；否则 message 非空 → `' <span class="note">{esc(message)}</span>'`；都空 → `''`。job 行与 step 行各调一次（替掉 259-262 与 275-278 两块），把「别再造第三种样式」那句注释移到助手 docstring 上。
  - 测试：`uv run pytest core/tests/test_report_store.py`（已有 test_index_html_step_reason_follows_job_style_and_has_no_orphan_css_class 与 test_index_shows_fail_fast_reason_in_neutral_note_not_error_red 直接钉这两种样式）…


### core/gherkai_core/adapters/report_store/s3.py

- **R8** STALE_INEFFICIENT/high · :24 `from ...report_store.local import SCHEMA_VERSION, _render_index_html, collect_report_index` — 跨模块 import 了下划线私有符号 `_render_index_html`，而同批被共享的另两个符号（`collect_report_index` / `SCHEMA_VERSION`）都是公开名——命名没跟消费者走。本轮 diff 里刚刚为同一原因把 `_local_path` 改名成公开 `local_path_from_uri`（因为出现了第二个消费者），同一判据没应用到渲染函数。
  - 证据：s3.py:24 `from gherkai_core.adapters.report_store.local import SCHEMA_VERSION, _render_index_html, collect_report_index`；local.py:31 `collect_report_index` 的 docstring 自称「**local/s3 共享的单一真理源**」（公开名），local.py:179 `_render_index_html` 同样被 s3 消费却仍私有名；`git diff 5d04676..HEAD -- core/gherkai_core/adapters/report_store/local.py` 显示 `_local_path` → `local_path_from_uri` 的改名理由写在新 docstring 里：「**公开小工具**（…第二个消费者…）」。
  - 提议：二选一（属重构、交人批）：①最小改动——`_render_index_html` 改名 `render_index_html`，改 s3.py 的 import 与 local.py 内 1 处调用（local.py:102），docstring 补一句「local/s3 共享的渲染真理源」；②更彻底——把 `SCHEMA_VERSION` / `collect_report_index` / `render_index_html` 三个共享物移到同包新模块（如 `report_store/_manifest.py`），local.py 与 s3.py 都从它 import，消除「s3 依赖 local 模块」这条方向可疑的依赖边。
  - 测试：`uv run pytest core/tests/test_report_store.py core/tests/test_s3_report_store.py`；若选方案②再跑 `uv run pytest core/tests runtime/tests cli/tests` 确认无 import 面漏改。


### deploy_aws/gherkai_deploy_aws/lambdas/reconciler.py

- **R9** STALE_INEFFICIENT/high · :290 `_build` — `_build` 手工重造了 `compose.build_cloud_stores` 已有的三 store + offloader 装配（同样的 prefix 规范化、同样共享一个 s3 client），并三次跨包调用 compose 的**私有** `_normalize_prefix`——与本文件自己声明的「组合根装配复用 compose 单一真源、不重造」原则相反，属该抽取的重复 + 私有 API 越界（交人批：真要合并需给 `build_cloud_stores` 加句柄注入参数）。
  - 证据：reconciler.py L288-309：`S3StepArgumentOffloader(s3, bucket, compose._normalize_prefix(report_dir))` / `DynamoDBRunStore(runs_table, arg_offloader=offloader)` / `S3ResultStore(s3, bucket, compose._normalize_prefix(report_dir))` / `S3ReportStore(s3, bucket, compose._normalize_prefix(report_dir))` —— 与 runtime/gherkai_runtime/compose.py L673-687 的 `build_cloud_stores` 逐行同构（`pfx = _normalize_prefix(prefix)`；`offloader = …
  - 提议：给 `compose.build_cloud_stores` 加可选句柄注入（`ddb_table=None, s3=None`，未给则走现有 `_make_*` 钩子，与 `build_fargate_engines` 已有的注入惯例同形），Lambda `_build` 改成 `run_store, result_store, report_store, _ = compose.build_cloud_stores(table=..., bucket=bucket, prefix=report_dir, region=region, ddb_table=runs_table, s3=s3)`，删掉 L288-309 的四行手工装配与三处 `compose._normalize_prefix` 调用。若评审倾向不动 `build_cloud_stores` 签名，最小改法 = 把 `_normalize_prefix` 改名为公开 `normalize_prefix`（compose 内四个调用点同改）并在 `_build` 里只算一次 `pfx`，至少去掉私有 API 越界与三次重复求值。
  - 测试：deploy_aws/tests/test_lambda_handlers.py（moto 装配路径，含 offload 正文还原的用例）、deploy_aws/tests/test_lambda_asset.py、core/tests/test_stores.py、core/tests/test_s3_report_store.py、runtime/tests/test_compose.py；改…


### deploy_aws/gherkai_deploy_aws/names.py

- **R10** STALE_INEFFICIENT/high · :51 `names.QWEN_MODEL_ID ↔ engines/midscene/src/lib/agentcore-sigv4.mts 的 MODEL` — `QWEN_MODEL_ID` 的注释把「须与 `engines/midscene/src/lib/agentcore-sigv4.mts` 的 `MODEL` 逐字一致」定成硬契约，但没有任何护栏钉住它：唯一相关的测试 `test_stack.py::test_task_role_resource_arns_narrowed` 只是把同一个字面量再抄一遍，只能防 Python 侧改动、照不出 TS 侧改名。跨语言不能共享常量，本仓库对这类两侧硬契约的既有解法是加对拍测试（如 TS 禁词扫描复用 Python 同一张 FORBIDDEN 表），此处缺这一环。
  - 证据：`names.py:51-56` 注释 +`QWEN_MODEL_ID = "qwen.qwen3-vl-235b-a22b"`；`stack.py:399` 把它 pin 进 `arn:aws:bedrock:*::foundation-model/{…}`；TS 侧 `engines/midscene/src/lib/agentcore-sigv4.mts:30` `export const MODEL = "qwen.qwen3-vl-235b-a22b"`（当前一致）。全仓 grep `qwen` 的测试命中只有 `deploy_aws/tests/test_stack.py:362` 的硬编码字面量断言，无一处读 `.mts`。
  - 提议：在 `deploy_aws/tests/test_stack.py` 加一条对拍：从仓库根读 `engines/midscene/src/lib/agentcore-sigv4.mts`，正则抽 `export const MODEL = "(...)"`，断言 == `names.QWEN_MODEL_ID`（读不到文件时 skip，保 wheel-only 场景不假红）；同时把 `test_task_role_resource_arns_narrowed` 里的硬编码 `qwen.qwen3-vl-235b-a22b` 改成引 `names.QWEN_MODEL_ID`，让字面量只剩 TS 与 names 两处、由新护栏钉住。属加测试的主观项，交人批。
  - 测试：`uv run pytest deploy_aws/tests/test_stack.py`；反转验证非假绿：临时把 `.mts` 的 `MODEL` 改成 `qwen.x` 跑一次应红，改回后绿。


### deploy_aws/gherkai_deploy_aws/workers.py

- **R11** STALE_INEFFICIENT/high · :895 `list_workers` — 注释宣称「全部版本的映射只枚举一次…两个引擎共用」，但函数实际把 `worker-image/*` 整棵树翻了 1 + 引擎数 次：`mapped` 一次，随后每个引擎的 `current_version_mappings` 各再一次（当前两引擎 = 3 次全量分页）。
  - 证据：workers.py:896 `mapped = {a for _e, _t, raw in _iter_image_params(aws.ssm, prefix) ...}`（第 1 次）；workers.py:900 在 `for engine in engines` 循环内 `current_version_mappings(aws.ssm, prefix=prefix, engine=engine, version=version)`，而 `current_version_mappings`（207-216）体内第一行就是 `for eng, tag, raw in _iter_image_params(ssm, prefix)`——同一棵树、同一个 prefix，逐引擎重走。`_iter_image_params`（168-188）自己的 docstring 点明「单页最多 10 条、**必须翻页**」，故每次全量走 …
  - 提议：把「枚举」与「筛选」分开：新增 `_mappings_from(params, *, engine: str, version: str) -> list[ImageMapping]`（就是 `current_version_mappings` 现有的 208-216 循环体，喂已物化的 `(engine, tag, raw)` 序列），`current_version_mappings` 退化成 `_mappings_from(list(_iter_image_params(ssm, prefix)), …)` 的薄壳（保持现有对外签名不变）。`list_workers` 改成 `params = list(_iter_image_params(aws.ssm, prefix))` 一次，`mapped` 与循环里的 `mappings = _mappings_from(params, engine=engine, version=version)` 共用它；`rederive_variants` 同法（在 `for engine in engines` 之前物化一次）。同时把 895 那行注释改准（说明它同时供 `mapped` 与各引擎筛选）。
  - 测试：`uv run pytest deploy_aws/tests -q`（`test_list_workers_json_shape`、`test_list_workers_json_keys_match_contract_doc`、`test_list_workers_says_when_the_default_pointer_is_missing`、`test_rederive_*` 覆盖行为不…

- **R12** STALE_INEFFICIENT/high · :801 `rederive_variants → _repo_uri_from_template` — `_repo_uri_from_template` 只依赖 (template_arn, engine)——两者都是外层 engine 循环的不变量——却被放在 per-mapping 内层循环里，于是每个待重派生的 variant 多打一次 `DescribeTaskDefinition(模板)`；而同一轮里 `_register_revision` 又 describe 同一个模板一次，等于每 variant 两次。
  - 证据：workers.py:796-804：`for engine in engines:` → `template_arn = _template_arn(...)` → `for mapping in current_version_mappings(...)` → `repo_uri = _repo_uri_from_template(aws.ecs, template_arn=template_arn, engine=engine)`（801，两个实参都在内层循环里恒定）→ `_register_revision(aws.ecs, template_arn=template_arn, …)`（802）。`_repo_uri_from_template`（819-835）体内第一行 `td, _ = _describe_revision(ecs, template_arn)`；`_register_revision`（309）体…
  - 提议：把 801 行提到内层 `for mapping ...` 之前（紧跟 797 的 `template_arn = _template_arn(...)`），即每个引擎算一次 `repo_uri`。更进一步（可选、同批）：让 `_register_revision` 接受可选的已 describe 的 `td`（或让 `rederive_variants` 复用同一次 `_describe_revision(template_arn)` 的结果），把每 variant 两次 describe 压成每引擎一次。
  - 测试：`uv run pytest deploy_aws/tests -q`（`test_rederive_uses_the_new_template_and_keeps_pushed_at`、`test_rederive_skips_when_template_arn_is_unchanged`、`test_workers.py:679` 一族覆盖）；若做第二步（复用 td），补一条用计数 fake …


### engines/midscene/src/lib/agentcore-sigv4.mts

- **R13** STALE_INEFFICIENT/medium · :30 `MODEL` — `MODEL` 的字面量被 deploy_aws 的 IAM 收窄 pin 死，names.py 的注释把「须与本文件逐字一致」写成不变量，但全仓没有任何护栏断言这两处相等——第三份副本还在 test_stack.py 里硬编码。改 MODEL 而忘了改 IAM，症状是使用方已部署后端里 Midscene 全部 job 报 InvokeModel AccessDenied，且本仓测试全绿。
  - 证据：engines/midscene/src/lib/agentcore-sigv4.mts:30 `export const MODEL = "qwen.qwen3-vl-235b-a22b";`；deploy_aws/gherkai_deploy_aws/names.py:51-56 `# QWEN_MODEL_ID …**须与 `engines/midscene/src/lib/agentcore-sigv4.mts` 的 `MODEL` 逐字一致**（Midscene InvokeModel 的 foundation-model ARN pin 到它）` + `QWEN_MODEL_ID = "qwen.qwen3-vl-235b-a22b"`；stack.py:399 `resources=[f"arn:aws:bedrock:*::foundation-model/{names.QWEN_MODEL_ID}"]`；第三份…
  - 提议：在 deploy_aws/tests/ 加一条护栏测试（如 test_provider.py 或新 test_model_id_pin.py）：读 `engines/midscene/src/lib/agentcore-sigv4.mts`，用 `re.search(r'export const MODEL = "([^"]+)"')` 取值，断言 `== names.QWEN_MODEL_ID`，失败信息点明「改 Midscene 模型必须同步 IAM pin，否则已部署后端 InvokeModel 被拒」；同时把 test_stack.py:362 的裸字面量换成 `names.QWEN_MODEL_ID` 插值，消掉第三份副本。names.py:51 的注释改为指向该护栏测试（把口头不变量降级为「由测试守」）。
  - 测试：新增上述护栏测试；跑 `uv run --project deploy_aws pytest deploy_aws/tests/`。临时把 .mts 里的 MODEL 改一个字符、确认新测试变红（防假绿），再改回。


### engines/midscene/src/worker/run-scope.mts

- **R14** STALE_INEFFICIENT/medium · :699 `runStep catch 分支的 message / act.error 构造` — Midscene 侧 `step_done.message` 与 evidence 的 `act.error` 用裸 `${name}: ${message}`——不折叠换行、不封顶；Nova 侧同一语义走 `_error_text`（取 `.message`、只留首个非空行、折空白、封顶 300 字）。Playwright/Midscene 异常的 `.message` 惯常是多行带 call log 的长文本，落进 `jobs/*.json`、报告页 step 行与 explain 的「原因」都是一条上千字符的行——正是 ADR 0042 在 Nova 侧真跑暴露后要治的那个症状，Midscene 侧没同步。
  - 证据：engines/midscene/src/worker/run-scope.mts:699 `message: `${(e as Error).name}: ${(e as Error).message}`` 与 :709 同一字符串作 evidence `act.error` 传入；对照 engines/novaact/gherkai_worker_novaact/run_scope.py:469 `"message": _error_text(e)`，`_error_text`（同文件 :713-726）「取 `.message` → 首个非空行 → `" ".join(split())` → `[:300]`」。下游只折不截：cli/gherkai_cli/render.py:43-45 `_one_line` = `" ".join(str(text).split())`（无长度上界），core/gherkai_core…
  - 提议：在 engines/midscene/src/worker/run-scope.mts 加一个与 Nova `_error_text` 同规则的小函数（如 `errorText(e)`：`name: ` + `message` 的首个非空行 + 折叠空白 + 截 300 字），catch 分支的 `message` 与传给 `emitWithEvidence` 的 `error` 都过它；evidence.mts 的 `errorTextOf`（:190-193，读 `task.errorMessage`）同样过一次同一规则，使 `act.error` 两侧同形。若判定「长文本该留全」，则应反过来放宽 Nova 并在 ADR 0042 映射表把「不封顶」写成两侧共同规则——不要留现在这种一侧治一侧不治的状态。属主观/口径类，交人批。
  - 测试：engines/midscene/src/worker/run-scope.test.mts 加一条：注入一个 `message` 含换行且超 300 字的异常，断言 `step_done.message` 为单行且长度有界；engines/midscene/src/worker/evidence.test.mts 对多行 `errorMessage` 的 fixture 加同形断言。跑 mids…


### engines/midscene/src/worker/user-steps.mts

- **R15** STALE_INEFFICIENT/medium · :26 `collectStepFiles / loadUserSteps 零注册守卫` — Midscene 的 steps/ 遍历没有「辅助模块」排除规则（只跳 `*.test.*`），而每个被收集的文件都要过零注册守卫——于是使用方在 steps/ 里放任何不注册 step 的模块（页面对象、选择器常量、共享 helper）都会让 worker 起不来；Nova 侧同一目录里 `_*.py` 是被明确支持的辅助模块。同一份 steps/ 目录在两个引擎上可承载的内容不对称，且 README 宣传的「测试开发写小函数拿页面对象查」在 Midscene 侧没有落脚处。
  - 证据：user-steps.mts:23-41 `const STEP_EXTS = [".mts", ".mjs"]` + `collectStepFiles` 只过滤 `/\.test\./`，无 `_` 前缀判断（`grep 'startsWith("_")' engines/midscene/src` 零命中）；user-steps.mts:75-81 对**每个**文件做 `if (size() === before) throw`。对比 user_steps.py:79-82 `_is_step_file`：`return not name.startswith("_") and not name.startswith("test_")`，docstring 写明「`_*`（辅助模块，供相对 import）」，engines/novaact/README.md:44 也对使用者写明「跳过 `_*.py`（你自己的辅助模块，…
  - 提议：两步，需人拍板取哪条：①（推荐、改动最小）给 `collectStepFiles` 加与 Nova 同形的排除——`if (e.name.startsWith("_")) continue;`，使 `_*.mts` / `_*.mjs` 成为「不自动加载、供其它 step 文件 import」的辅助模块面，与 Nova 的 `_*` 语义逐字对齐；同步改 engines/midscene/README.md:46 与 cli/gherkai_cli/skills/gherkai/references/engines.md:69 的遍历规则行（Midscene 那半句补「跳过 `_*`」），并在 ADR 0037 决策 4 的 midscene 那句里把排除集补成「排除 `_*` 与 `*.test.*`」。②若决定不加排除，则至少把零注册守卫的诊断文案（user-steps.mts:77-80）与 references/engines.md:82 补上第二种成因（「这个文件本身不注册 step——辅助模块请挪出 steps/ 目录」），别只指向双实例。
  - 测试：engines/midscene/src/worker/user-steps.test.mts 补两例：`steps/_helpers.mts`（零注册）被跳过、不触发守卫；`steps/_shared.mts` 注册 + `steps/a.mts` 仅 import 它时不报错。改 README/skill 后跑 `uv run --project cli pytest cli/tests/te…


### engines/novaact/gherkai_worker_novaact/deterministic.py

- **R16** STALE_INEFFICIENT/low · :14 `模块 docstring「handler 约定」` — Nova 侧 handler 必须是同步函数（run_scope 检出 awaitable 直接抛 TypeError），但这条硬约束没写进任何 handler 作者会读的契约文档：deterministic.py 的「handler 约定」只说签名与 failed/error 映射，deterministic_steps.py 又把读者指回它；Midscene 的同名契约反而明确允许 `Promise<void>`，随包发行的 skill 模板给的 Midscene 示例就是 async。写成对 step 的使用方最容易两侧都写 async，Nova 侧该 step 直接记 error。
  - 证据：deterministic.py:14-19「handler 约定：- 签名 `def handler(ctx, **groups)`…- 判定失败抛 `AssertionError` → step 记 **failed**；抛其它异常 → step 记 **error**。- 不投票」——无 async 条；run_scope.py:367-373 `ret = handler(ctx, **groups); if inspect.isawaitable(ret): … raise TypeError(f"确定性 handler 不能是 async（Nova 引擎同步执行）：…")`（该 TypeError 落进 except Exception → step 记 error）；deterministic_steps.py:146「handler 约定（见 `deterministic.py`）」；对侧 determinist…
  - 提议：在 deterministic.py:14 的「handler 约定」里加一条：「- **必须是同步函数**（Nova 引擎同步执行）：返回 awaitable 会被检出并抛 TypeError（该 step 记 error），断言不会被执行——需要异步的判定只能在 Midscene 侧写。」；同步在 cli/gherkai_cli/skills/gherkai/references/engines.md 第 66 行「签名」条补半句「Nova 的 handler 必须同步（`def`，不能 `async def`）；Midscene 可 async」，以及 engines/novaact/README.md 的确定性 step 规则列表补同一句。若判定该差异值得进 ADR，在 ADR 0022 或 0037 决策 4 的两侧对称条里加一句记录（同步/异步是引擎执行模型差异、不是可对齐项）。
  - 测试：engines/novaact/tests/test_run_step.py 补一例：注册一个 `async def` handler，断言该 step status == "error" 且 message 含「不能是 async」（现有 grep 显示无此覆盖）。改 skill/README 后跑 `uv run --project cli pytest cli/tests/test_skil…


### engines/novaact/gherkai_worker_novaact/lib/constants.py

- **R17** STALE_INEFFICIENT/medium · :6 `WORKFLOW_DEF` — WORKFLOW_DEF 仍是 spike 期名 `spike-wikipedia-benchmark`，而 docstring 给出的保留理由（「不把既有 definition 名下的历史 run 孤立掉」）只对维护者自己那个开发账户成立；包已发行后，每个使用方账户都会被 create-if-not-exists 建出一个叫 `spike-wikipedia-benchmark` 的 Nova Act workflow definition，使用方在自己 AWS 控制台看到的是别人 spike 阶段的名字。理由随分发形态失效，注释已过时。
  - 证据：constants.py:6-8 「注：WORKFLOW_DEF 值 'spike-wikipedia-benchmark' 沿用自 spike 阶段。技术上改名已可行…保留此名只为不把既有 definition 名下的历史 run 孤立掉。」；constants.py:13 `WORKFLOW_DEF = "spike-wikipedia-benchmark"`；run_scope.py:794 `ensure_workflow_definition(WORKFLOW_DEF, region=REGION, description="Nova Act worker")` —— 生产 worker 每个 scope 首跑就在**使用方**账户建它；stack.py:370-374 的 IAM 刻意用 `workflow-definition/*` 通配、不 pin 此名，说明改名在部署侧零成本。
  - 提议：交人定夺（改名会在使用方账户留下一个不再被引用的旧 definition，虽无副作用但要说清）：若改，把 constants.py:13 改成产品名（如 `gherkai-worker`），删掉 constants.py:6-8 那段已失效的保留理由，并同步 ADR 0004 第 23 行（记新名 + 一句「旧名 spike-wikipedia-benchmark 系 spike 期遗留，分发化后改产品名；改名无迁移成本，IAM 用 workflow-definition/* 通配」）；若不改，至少把 docstring 的理由改准——从「不孤立历史 run」改成「维护者开发账户里已有该名下的历史 run；使用方账户由 create-if-not-exists 自动建，名字对判定无影响」，别让未来读者以为这个理由对所有使用方成立。
  - 测试：改名则跑 `uv run --project engines/novaact pytest engines/novaact/tests/`（test_workflow_setup.py 传的是参数名、不依赖具体值；确认没有测试硬编码旧名：`grep -rn spike-wikipedia engines cli runtime deploy_aws`）；并在真账户做一次 `gherkai run …


### engines/novaact/gherkai_worker_novaact/run_scope.py

- **R18** STALE_INEFFICIENT/medium · :433 `_run_step 三个 step_done 出口（Then 投票 / When·Given 动作 / except 失败）` — 「产 evidence → 挂 ref → emit → 才入队」这个**顺序契约**在 Nova 侧被手写重复三遍（L433-435、L451-453、L483-485）；姊妹引擎已把同一契约收进单一出口 `emitWithEvidence`，Nova 缺这层结构保证——未来加第四个出口或调顺序时会漂。
  - 证据：run_scope.py:433-435 / 451-453 / 483-485三处逐字相同的 `shots = _attach_evidence(...); sink.emit(ev); _enqueue_evidence_shots(shots)`。同文件 `_attach_traj_refs` 的 docstring 已记下同类教训：「三个 emit 点（Then 投票/When 动作/except 失败）共用一份（曾三处重复、各自漂移风险）」——trajectory 已收口，evidence 又长出同形的三份。对照 `engines/midscene/src/worker/run-scope.mts:620-632` 的 `emitWithEvidence` 闭包（三条出口 L680/689/705 各调一次）。
  - 提议：抽 `_emit_step_done(sink, ev, *, scope_id, scenario_id, step, acts) -> None`：内部按序 `_attach_evidence` → `sink.emit(ev)` → `_enqueue_evidence_shots(shots)`，三个出口各替换成一行调用（`except` 分支仍在调用前 `acts.append(_act_record(...))`）；顺序契约与「emit 之后才入队」的理由集中到这一个 docstring，不再三处各写一遍。属重构类、待人批。
  - 测试：`cd engines/novaact && uv run pytest tests/test_run_step.py tests/test_evidence.py -q`——`test_screenshots_enqueued_only_after_step_done_emit`（断言 trace == emit, emit, enqueue）、`test_no_enqueue_when_ste…


### engines/novaact/gherkai_worker_novaact/user_steps.py

- **R19** DEAD/low · :85 `load_user_steps 返回值` — load_user_steps 的返回值（已加载文件列表）生产端一个消费点都没有——run_scope.main() 直接丢弃，也不打任何「已加载 N 个文件」的 stderr 行；Midscene 的对称函数用它打诊断行。使用方在 Nova 档下拿不到「steps 目录被读到了」的确认，两引擎诊断面不对称。
  - 证据：user_steps.py:85-86 `def load_user_steps(root: str | None) -> list[Path]:` /「返回实际加载的文件列表（排序后）」；run_scope.py:758 `load_user_steps(os.environ.get("GHERKAI_STEPS_DIR"))` —— 返回值未接、其后无 log；全仓 grep `load_user_steps` 的其余命中只在 engines/novaact/tests/test_user_steps.py（57/71/83 行等）。对比 user-steps.mts:83 `if (files.length > 0) logFn(\`worker: 已加载使用方 steps ${files.length} 个文件（${stepsDir}）\`);`，其 JSDoc 也写明返回值是「诊断用」。
  - 提议：两条选一，人批：①（对称化，推荐）run_scope.py:758 改成 `loaded = load_user_steps(...)`，成功分支后加 `if loaded: log(f"worker: 已加载使用方 steps {len(loaded)} 个文件（{os.environ['GHERKAI_STEPS_DIR']}）")`，与 Midscene 的 stderr 行逐字同形；②若判定这行日志是噪声，则删掉 Midscene 侧那行、并把 load_user_steps 的返回类型收成 `None`、docstring 去掉「返回实际加载的文件列表」（测试改断言注册表内容而非返回值）。别留现状（一侧有、一侧无、且返回值只有测试用）。
  - 测试：取 ① 则在 engines/novaact/tests/test_user_steps.py 补一例 capsys/capfd 断言该 stderr 行随文件数出现（未注入目录时不打）；跑 `uv run --project engines/novaact pytest engines/novaact/tests/test_user_steps.py`。取 ② 则改 engines/midsce…


### runtime/gherkai_runtime/compose.py

- **R20** STALE_INEFFICIENT/medium · :235 `_is_pure_release / is_pure_release` — 同一个函数长期挂两个名字：公开名 `is_pure_release` 只被 deploy_aws 用，模块内 2 处调用 + 3 处注释引用 + 5 处测试仍走私有旧名 `_is_pure_release`——grep 任一名都照不出全部使用点，是纯遗留别名、无技术必要。
  - 证据：compose.py:235 `_is_pure_release = is_pure_release  # 模块内旧名（定位链/skew 判据处仍用）；跨包（deploy 的基底同步）用公开名`。走旧名的调用点：compose.py:282（定位链第四级门槛）、937（`_release_cmp` 两次）；注释引用：248、922、960。测试全用旧名：runtime/tests/test_compose.py:160-164（`compose._is_pure_release(...)` ×5）。走公开名的跨包调用点：deploy_aws/gherkai_deploy_aws/workers.py:754、854、cli.py:358。`git log -S "_is_pure_release = is_pure_release"` → 别名随 e403f65（ADR 0038 落地、为让 deploy_aws 能跨包引用而把…
  - 提议：删 compose.py:235 整行；把 282、937（两处）的调用改为 `is_pure_release`，248、922、960 三处注释里的 `` `_is_pure_release` `` 改为 `` `is_pure_release` ``；runtime/tests/test_compose.py:160-164 五处改公开名。deploy_aws 侧三处调用点不动。
  - 测试：runtime/tests/test_compose.py（版本纯净判据组 + 定位链第四级组 + check_version_skew 组）、deploy_aws/tests/test_workers.py:613 附近（基底同步的 skew 判据）、deploy_aws/tests/test_provider.py:730 附近；无需新增测试（纯重命名，现有断言即覆盖）。


### runtime/gherkai_runtime/tunnel.py

- **R21** STALE_INEFFICIENT/medium · :97 `NgrokTunnel.start（Traffic Policy 临时文件 / policy_path）` — 承载本 run basic-auth 凭据的 policy 临时文件每 run 一个、永不删除，且没有任何「有意不删」的理由注释——与紧邻的 log 文件（显式写了为什么不删）形成不对称，读者无法判断这是决策还是遗漏；`policy_path: str | None = None` 的初始化从引入起就无人读，正是「本想删、没写删」留下的痕迹。
  - 证据：tunnel.py:97 `fd, policy_path = tempfile.mkstemp(prefix="gherkai-tunnel-policy-", suffix=".yml")`，写入的正文含 `f'            - "{auth}"'`（user:pass 明文）；文件在 100 行传给 `--traffic-policy-file` 后再无引用，模块内、以及全仓（`grep -rn "gherkai-tunnel-policy"`）都没有 unlink/remove。对照 79-80 行 log 文件的注释：「文件**有意不删**：隧道存活期 agent 一直在写，且它是唯一诊断通道（authtoken 缺失等 err 行在其中）」——policy 文件既非诊断通道、也不需要长期存在，却同样留着。85 行 `policy_path: str | None = None` 是死初始化：变量只在 `if…
  - 提议：先由人二选一，再落：A（推荐，最小）在 start() 里给 policy 文件补一条与 log 文件对称的理由注释，说明为何不删（ngrok agent 可能在存活期重读 policy；凭据随隧道拆除即成死凭据，mkstemp 权限 0600），同时把 `policy_path` 收成块内局部变量、删掉 85 行的死初始化。B（真清理）在拿到 URL 之后（153 行 return 前）与超时报错路径（139-152）各加一次 best-effort `Path(policy_path).unlink(missing_ok=True)`——但必须先真跑核实 ngrok agent 在隧道存活期不再重读该文件，否则会把边缘 basic-auth 拆掉（属「绿≠对」里必须真跑的那一类，别只靠单测）。无论选哪条，85 行的死初始化都删。
  - 测试：选 A：纯注释 + 局部变量收窄，跑 `uv run pytest runtime/tests/test_tunnel.py cli/tests/test_tunnel_cli.py`（`test_start_writes_traffic_policy_file` 类用例会钉 `--traffic-policy-file` 仍在 cmd 里）。选 B：先真跑一次 `gherkai run --ex…


### tools/e2e_harness.py

- **R22** STALE_INEFFICIENT/low · :43 `sys.path.insert(0, str(REPO / "core"))` — 包化后这行 sys.path 注入已是冗余残骸（harness 本就硬依赖同一 venv 里的 `gherkai_runtime`、而那个没有任何 path 注入），留着的副作用是把 repo 的 core 树顶到已安装 `gherkai-core` 之前——在非 workspace venv 里跑会静默混版本。
  - 证据：harness 只插 `<repo>/core`，却在 worker_cmd() 里 `from gherkai_runtime.compose import resolve_worker_cmd`（69 行，注释自陈「harness 与 CLI 同 venv」）、并在 run() 里 `from gherkai_runtime.names import ARTIFACT_SUBDIR`（104 行）——`<repo>/runtime` 从未进 sys.path，说明 harness 的真实前提就是「两个包都由 venv 提供」，那么 core 的那一插毫无必要。真值：根 pyproject.toml 的 `[tool.uv.workspace] members = ["core", "runtime", "cli", "engines/novaact", "deploy_aws"]` + `dependencies = ["g…
  - 提议：删 tools/e2e_harness.py:43 的 `sys.path.insert(0, str(REPO / "core"))`（`REPO` 仍要留——42 行它还被 build_job 的 `REPO / "features" / …` 用）。同批把 tools/e2e_harness.md「前置条件」那句改成「两个包都由仓库根 workspace venv 以 editable 提供（`uv sync`）；harness 不改 sys.path，只由 `__file__` 派生 features 目录」——该 md 是给人读的操作手册，属 doc 侧同批改动。
  - 测试：harness 不进 pytest。改完在仓库根 `uv run python tools/e2e_harness.py --help` 与一次 `--interrupt none` baseline 真跑确认 import 全通（`gherkai_core.scope` / `gherkai_core.wire` / `gherkai_runtime.compose` / `gherkai_ru…


## 二b、观察（复盘过程中浮出、未列为提案，供参考）

- 终态闸的新对偶用例钉的是「派生信号」这一读法；若把「有终态 job」理解为 RunState.jobs 字段里的终态，要真正区分需再造「run 级 running、某个 job 已终态」的多 job 种子（deploy_aws/tests/test_lambda_handlers.py）。
- Midscene run-scope.mts 两行上传失败日志在 main()/runScenario 的 catch 里、没提成可测函数，字面无单测钉住。
- 撞名检测判在筛选之前、收窄重跑也退 2，是有意代价，已记 ADR 0041 决策一并加测试钉住。

落地后逐 hunk 独立自审：10 组 / 136 hunk，意见 35 条（high 2 / medium 10 / low 23），code 侧 31 条已落（每组反转验证）、文档校准 38 处已落（ADR 0016/0025/0029/0030/0033/0034/0035/0037/0038/0039/0041/0042/0043、CONTEXT、三篇 guide、deploy_aws/README、engines/midscene/DEVELOPMENT、SKILL.md）。


## 三、对抗验证驳回（存档）

- BUG cli/gherkai_cli/__main__.py:1532 `_explain_emit` — 主张：给了 `scope_id` 但没找到时无条件 `load_all` 列候选 → cloud 档要 `s3:ListBucket`，与 ADR 0042 承诺的「带 scope_id 只需 GetObject」权限面相悖；而失败后的诊断又恰好在 `args.scope_id` 非空时抹掉「还需列举对象的权限」那半句，把真因盖掉。
  - 驳回：发现的两条后果链都不成立，且它的两半互相拆台。

事实核对（都亲自核到）：
1) ADR 0042 是 Accepted（头行「Status: Accepted（2026-09-11）」），决策四原文确实写「另需该桶 s3:GetObject…不带 scope_id 时还需 s3:ListBucket」。code 第 1532 行（/Users/lzy/workspace/yaozhou/cli/gherkai_cli/__main__.py）在 `jr is None` 时无条件 `load_all` 也是事实，与 1524-1525 行自己的 docstring 字面不符——但仅此而已，**无可观测错误**。
2) 后果①与①所依赖的 AWS 语义自相矛盾。发现自己引用的规则（主体缺 s3:ListBucket 时，GetObject 打不存在的 key 返 403 AccessDen…

- VIOLATES_ADR cli/gherkai_cli/__main__.py:660 `_cmd_doctor（steps 段）` — 主张：`--backend cloud` 下 `steps.dir` / `steps.load.<engine>` 仍按必修判，可 cloud 档的本机 steps 目录**根本不生效**（steps 烙在定制镜像里）——同一个 ADR 判据下 `engines.any` 已为 cloud 降级，steps 段没跟上：只提交 cloud 的人一个坏掉的本机 steps/ 就让 `doctor --ba…
  - 驳回：三条独立证据都指向「非违背 ADR」：①ADR 0041 决策四 steps 条（docs/adr/0041-agent-facing-cli-affordances.md:50，Status 只被 0043 部分取代、被反转的是决策五的 skill 子句，决策四仍作基线）逐字规定「显式给的目录不存在 = 必修失败」「有 steps 目录时（加载）必修」，且**同一 bullet 列表**的 engines 条（:49）明写了 cloud 降级——ADR 在同处能写例外而 steps 条选择不写，code（cli/gherkai_cli/__main__.py:645/660/662）实现的正是字面规格；发现是拿同节那句概括判据（「required 的判据 = 这次要跑的档真跑得起来吗」）去覆盖 itemized spec，属 rationale 压 spec 的误读，至多是 ADR 内部…

- BUG engines/midscene/src/worker/run-scope.mts:508 `main（agent.destroy 的 .catch）` — 主张：`await agent.destroy().catch(() => {})` 把 destroy 失败完全静默吞掉（连一行 stderr 都没有），紧接着就把可能未 finalize 的 report.html 当权威 `kind=report` ref 上传——报告坏了在任何日志里都看不见；同一文件其余每条 best-effort 路径都记一行诊断。
  - 驳回：表层事实为真，但撑起「BUG」定性的两条关键前提经核查不成立，且无任何路径产出错误结果。

一、`engines/midscene/src/worker/run-scope.mts:508` 确实是 `await agent.destroy().catch(() => {});`，无 log；509–518 随即 `uploader.toReportRef(agent.reportFile)` 并 push `{kind:"report"}`。这两点如实。

二、**「destroy 抛 ⇒ 报告可能停在半成品」在主要 reject 路径上是错的。** 读 SDK 真身 `engines/midscene/node_modules/@midscene/core/dist/es/agent/agent.mjs:608-621`：destroy 先把 `interface.destroy?.(…


## 四、已落地的客观项（按组）

- **G1-cli**：applied 6 / skipped 0；测试：uv run --quiet pytest -q -p no:cacheprovider cli/tests → 「278 passed in 14.33s」；另跑 uv run --quiet pytest -q -p no:cacheprovider cli/tests runtime/tests core/tes…
- **G2-novaact**：applied 2 / skipped 0；测试：export PATH=$HOME/.local/bin:$PATH; uv run --quiet pytest -q -p no:cacheprovider engines/novaact/tests → 「194 passed in 9.07s」。另跑护栏 uv run --quiet pytest -q -p …
- **G3-midscene**：applied 1 / skipped 0；测试：cd engines/midscene && npm run build --silent（tsc，declaration:true，退出码 0、无输出）；npm test --silent 结尾统计行原文：\n# tests 157\n# suites 0\n# pass 157\n# fail 0\n# cance…
- **G4-runtime-tools**：applied 4 / skipped 0；测试：1) `export PATH=$HOME/.local/bin:$PATH && uv run --quiet pytest -q -p no:cacheprovider runtime/tests` → `167 passed in 2.71s` 2) 同上但脏宿主 env（照出继承面的唯一跑法）：`GHERKAI…
- **G5-deploy-workers-cli**：applied 4 / skipped 0；测试：规定命令（仓库根，export PATH=$HOME/.local/bin:$PATH）：`uv run --quiet pytest -q -p no:cacheprovider deploy_aws/tests/test_workers.py deploy_aws/tests/test_cli.py deploy_…
- **G6-deploy-stack-lambdas**：applied 5 / skipped 2；测试：uv run --quiet pytest -q -p no:cacheprovider deploy_aws/tests -k "stack or reconciler or lambda or observer" → 「107 passed, 135 deselected in 7.23s」；另跑 uv run -…
  - 跳过 [3]：只落了 reconciler.py 的两条（revised_fix 的 1）与 2）），第 3）项「同批改 exit_observer.py:85」及 L181/L190 的顺手措辞未落——lambdas/exit_observer.py 不在本组允许改的文件清单里（范围只给 stack.py、lambdas/reconciler.py、deploy_aws/tests/）。后果：exit_observer.py:85 仍写「非 detached，同步 cloud run 自己观察退出」，与改后的 reconciler:298 措辞不再对齐，需另一组或后续批次补。
  - 跳过 [4]：只落了 revised_fix 的「最小替代形态」（在 reconciler.py 调用点包 try/except）。推荐形态（在 runtime/gherkai_runtime/compose.py 加宿主侧取数函数、两宿主共用，并同形改 runtime/gherkai_runtime/detached.py L152-153）跨出本组范围，未落；对称测试 runtime/tests/test_detached_launcher.py 同理未加。detached 宿主那半的同一缺陷仍在（commit 后可失败的强一致读裸穿），需交 runtime 组。
- **G7-core-parse-scope**：applied 3 / skipped 0；测试：uv run --quiet pytest -q -p no:cacheprovider core/tests -k "parse or scope or plan" → `81 passed, 280 deselected in 4.32s`；另跑全包 uv run --quiet pytest -q -p no:c…
- **G8-core-adapters**：applied 5 / skipped 0；测试：1) 清单指定命令：`uv run --quiet pytest -q -p no:cacheprovider core/tests -k "store or report or launcher or subprocess or ddb or result"` → `125 passed, 236 deselecte…
- **S1-cli**：applied 4 / skipped 0；测试：export PATH=$HOME/.local/bin:$PATH; uv run --quiet pytest -q -p no:cacheprovider cli/tests（仓库根）→ 结尾统计行原文：`278 passed in 12.91s`
- **S2-runtime**：applied 5 / skipped 1；测试：`export PATH=$HOME/.local/bin:$PATH; uv run --quiet pytest -q -p no:cacheprovider runtime/tests`（仓库根）→ 结尾统计行：`167 passed in 2.91s`。另跑产品面护栏 `uv run --quiet pytes…
  - 跳过 [4]：第一批已改掉：detached.py 该处现为 `# 拿不到退出码 → None（有退出记录却无码 → 投影判 ERROR，**不是**宽限态；ADR 0034 机制二「退出码缺失」条）`（工作区 diff 可见），与清单 [5] 末尾「同址发现的复核意见 ①」逐字一致、且该复核意见明写「工作区已是此文」。原缺陷（称宽限态/判 running）已不存在，按「quote 已被第一批改掉就按当前文字判、别重复改」不再改写成 [4] 那版四行块。
- **S3-deploy**：applied 4 / skipped 0；测试：命令：`export PATH=$HOME/.local/bin:$PATH; uv run --quiet pytest -q -p no:cacheprovider deploy_aws/tests`（仓库根）→ 结尾统计行原文：`240 passed, 2 skipped in 14.71s`。附加 B 要求的护…
- **S4-core**：applied 7 / skipped 1；测试：`export PATH=$HOME/.local/bin:$PATH; uv run --quiet pytest -q -p no:cacheprovider core/tests -k \"parse or scope or plan or project or wire or model or serializ…
  - 跳过 [2]：本条含三处同源注释，其中 ② core/gherkai_core/serialize.py:161 不在本组允许改动的文件集（project/wire/model/ports/parse.py）内，未动；①（wire.py:141）与 ③（project.py:96）已按 revised_fix 逐字落。serialize.py 未出现在任何其它分组清单里（`grep -ln serialize.py /tmp/dhr6/ch4_stale_fixes/*.md` 只命中 S4-core.md），故这条漂移目前无人认领，需操作者另行指派——原文仍为 `"report_refs": [_ref_…
- **S5-core-adapters**：applied 7 / skipped 1；测试：命令（仓库根，先 export PATH=$HOME/.local/bin:$PATH）：uv run --quiet pytest -q -p no:cacheprovider core/tests -k "store or report or launcher or subprocess or ddb or res…
  - 跳过 [5]：与 [7] 同址同文（三个存储子包 __init__.py 的「不 re-export」理由），两条 revised_fix 互斥。按 [7] 落地——它是专门针对这句理由的条目、覆盖三个包且给出了 import 路径示例与「四个子包口径不统一」的护栏提示，信息量严格覆盖 [5]。[5] 要修的事实错误（「避免包导入即拉 boto3」不成立）已由 [7] 的文本完全纠正。
- **S6-engines**：applied 4 / skipped 0；测试：命令一：`export PATH=$HOME/.local/bin:$PATH; uv run --quiet pytest -q -p no:cacheprovider engines/novaact/tests` → 结尾统计行原文：`194 passed in 9.10s`。命令二：`cd engines/mid…
