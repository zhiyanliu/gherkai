# gherkai agent skill 的评测资产（contributor 侧）

> 定位：迭代 `cli/gherkai_cli/skills/gherkai/` 这份 skill 用的开发期资产，**不随 skill 发行**、使用方接触不到。决策与理由见
> [ADR 0043](../../docs/adr/0043-agent-skill-for-driving-gherkai.md) 决策七；本文只讲怎么跑。

| 文件 | 是什么 |
|---|---|
| `evals.json` | 行为评测（skill-creator 的 `evals.json` schema）。缺省集只执行 `plan` / `explain` / `doctor` / `list-deterministic`，零条真 AWS；`opt_in: true` 的条目真跑 `run` / `submit`，维护者在自己的部署上按需跑 |
| `trigger-eval.json` | description 优化的触发查询集（25 条，含 Cucumber / Playwright / behave / pytest 这类 near-miss 负例与 4 条「项目里没有 .feature」的条目），喂 skill-creator 的 `run_loop.py --eval-set` |
| `fixtures/<case>/` | 物化式 fixture = 一个「使用方项目」快照：`features/` `steps/` + 真跑录下的 `reports/<run_id>/`；绝对路径一律是占位符 `{{FIXTURE_ROOT}}`。**fixture 里不写「答案」**（哪一步是刻意写错的、为什么会失败这类脚手架自述会随舞台一起交给被测 agent、变成泄题）——录制意图记在下面 |
| `fixtures/wiki-search/` | 英文维基、Nova Act 默认引擎的一次本机 run：第一条 scenario 的最后一步是刻意写错的事实断言（OpenAI 成立年份），录下带失败证据的 run；第二条不标 scope，演示 `<文件>:<行号>` 形态的 scope_id 与项目自写的确定性 step（两引擎成对） |
| `fixtures/job-failure/` | 一次本机 run：`@scope:deep-dive @timeout:20` 的长流程在第一个 AI 步里被墙钟掐停 → job 级 `error`（timeout）、零 step 记录（`has_step_records` 为假）；同一 feature 带 `Background`（展开为每条 scenario 的第 0 步）与 `Scenario Outline`（两行 Examples 各成一个 job、id 形如 `features/browse.feature:13:19`，都通过）。喂 job 级汇报模板、`record_missing` 读法、Outline / Background 的 id 与步号口径 |
| `fixtures/nova-zh/` | 中文维基词条页，同一组步骤分别标 `@engine:novaact` 与 `@engine:midscene`：同一条「词条首段提到了计算机或机器」断言在 Nova Act 上判否（0/1，英文 UI 支持范围之外的系统性判否）、在 Midscene 上通过。喂「非英文页面判否先排查引擎语言面」的诊断规则与三条出路 |
| `fixtures/many-scenarios/` | 纯文本、无 run：3 个 feature、12 条 scenario（含 Outline 展开）、9 个 job，部分带 `@smoke`。喂费用闸门（plan 的 job 数 = 会话数）、`--tags` 筛选与筛空退 2 列候选 |
| `fixtures/broken-steps/` | 纯文本、无 run：`steps/title.py` import 了不存在的模块 → `plan` / `run` / `submit` 整批拒跑退 2。喂「先修 steps 文件、不是怀疑 feature」 |
| `materialize.py` | 把 fixture 物化到仓库外的舞台（替占位符、生成 `bin/gherkai` shim、前置断言、隔离断言、完整性断言）；`--prepare-cli` 一次性把舞台要用的 CLI 备到仓库外（构建 wheel → 装进 `<dir>/venv` → 剥掉 wheel 自带的 skill → skill 拷到 `<dir>/skill/` → midscene 拷到 `<dir>/midscene/`）；`--snapshot` 是逆操作、录 fixture 用 |
| `run_evals.py` | 行为评测的驱动：每条 eval × 每臂 × `--runs` 次，各自一个独立舞台与独立 `claude -p` 进程，每次落 `transcript.json` / `tool_calls.json` / `timing.json` / `outputs/` |
| `trigger_eval.py` | 触发率的驱动：把 skill 装进临时项目的真实安装位（`.claude/skills/gherkai/`），对 `trigger-eval.json` 每条查询看 `Skill(gherkai)` 或读 SKILL.md 是否出现 |

## 跑一轮

```bash
# 0) 一次性：把舞台要用的 CLI 备到仓库外（构建 wheel、建 venv、剥掉 wheel 自带的 skill、拷 midscene；要联网、几分钟）
python skills/gherkai-evals/materialize.py --prepare-cli                  # 缺省 /tmp/gherkai-eval-cli

# 1) 跑两臂：每条非 opt_in 的 eval × {with_skill, without_skill} × 3 次，各自一个独立舞台与独立 claude -p 进程
python skills/gherkai-evals/run_evals.py --iteration 3 --runs 3
#    结果（已 gitignore）：skills/gherkai-workspace/iteration-3/
#      eval-<id>-<slug>/eval_metadata.json
#      eval-<id>-<slug>/{with_skill,without_skill}/run-{1,2,3}/{transcript.json,tool_calls.json,timing.json,outputs/}

# 2) 评分：每个 run 目录喂一个 skill-creator agents/grader.md 的 grader，让它写回同目录的 grading.json

# 3) 聚合 + 出看板
cd <skill-creator 目录> && <repo>/.venv/bin/python -m scripts.aggregate_benchmark <repo>/skills/gherkai-workspace/iteration-3 --skill-name gherkai
<repo>/.venv/bin/python <skill-creator 目录>/eval-viewer/generate_review.py <repo>/skills/gherkai-workspace/iteration-3 --skill-name gherkai \
  --benchmark <repo>/skills/gherkai-workspace/iteration-3/benchmark.json --static <repo>/skills/gherkai-workspace/iteration-3/review.html
```

触发率单独一条线（description 优化用）：`python skills/gherkai-evals/trigger_eval.py --runs 3`。别用 skill-creator 自带的 `run_eval.py`（它走 `.claude/commands/`，在当前 Claude Code 上对本 skill 恒 0，原因见 ADR 0043 决策七）。

**舞台不许指向仓库**：`--prepare-cli` 把 CLI、midscene、skill 副本全放到仓库外的一个目录，shim 只 exec 那里；物化后有两条恒开的断言兜底（舞台里没有任何文件含仓库根路径、舞台里找不到 `SKILL.md`）。理由是首轮的教训：那时 shim 里写着 `exec <repo>/.venv/bin/gherkai`，baseline 顺着它读了 CLI 源码、根 README、退出码表，甚至 skill 自己的 references——148 次工具调用里 54 次触到仓库，两臂 delta 只能算下界。每次跑的 `timing.json` 里 `repo_touches` / `network_calls` / `skill_copy_touches` 就是这三条泄漏渠道的当场记账：非零先查污染，再谈通过率。

两臂的 `claude -p` 由 `run_evals.py` 统一配：`--setting-sources project`（切断宿主用户级设置：ultracode / 子代理 / 个人 skills）、`--disallowedTools Workflow Agent Task TodoWrite WebFetch WebSearch`（`-p` 会在后台子代理完成前返回；活网内容会把 eval 的事实基准喂给某一臂、还让结果不可重放）、固定 `--model`、`--output-format stream-json`（存工具调用流水，评分的过程断言只认它）；子进程 env 只剥会话嵌套变量，保留 Bedrock 鉴权与模型映射。with-skill 臂的提示只给 `<cli-dir>/skill/SKILL.md` 这条中立路径。

前置：`uv` 可用；`engines/midscene` 已 `npm ci && npm run build`（`--prepare-cli` 要拷它的 `dist/` + `package.json` + `node_modules/`，两臂的 midscene 侧才真能查）。舞台的 shim 把 AWS 相关环境变量清掉并指向空配置文件，所以本机段输出跨机器一致。评测提示与工具白名单禁止任何安装类操作。skill-creator 的脚本要用仓库 `.venv` 的 Python（系统 python3 版本过低）。改动 description 入库前要过 `cli/tests/test_skill.py` 的 ≤ 1024 字符护栏。

## 录一个 fixture

1. 在仓库外建项目目录，放 `features/` 与 `steps/`（可从 `fixtures/wiki-search/` 拷起点）。
2. **cwd = 该目录、feature 用相对路径**：`gherkai run features/x.feature --report-dir reports`（scope_id / scenario_id 与 `jobs/` 文件名都带这条路径，绝对路径进了文件名占位符救不了）。
3. `python skills/gherkai-evals/materialize.py --snapshot <该目录> <case>`：拷进 `fixtures/<case>`、绝对路径换占位符、删 `*.log`、截图裁成极小 PNG，并扫一遍不得再有绝对路径。
4. `python skills/gherkai-evals/materialize.py <case>` 物化一次，让完整性断言过（`explain --json` 无 `unreadable` / `unsupported_schema`、至少一条 evidence、截图文件都在）。

`.gitignore` 对 `fixtures/**` 开了反白名单（派生品规则会静默吞掉 `reports/` `*.log` `screenshots/`），密钥规则在其后重列；`cli/tests/test_skill.py` 用 `git check-ignore` 两向断言这两件事。
