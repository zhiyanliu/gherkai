# gherkai agent skill 的评测资产（contributor 侧）

> 定位：迭代 `cli/gherkai_cli/skills/gherkai/` 这份 skill 用的开发期资产，**不随 skill 发行**、使用方接触不到。决策与理由见
> [ADR 0043](../../docs/adr/0043-agent-skill-for-driving-gherkai.md) 决策七；本文只讲怎么跑。

| 文件 | 是什么 |
|---|---|
| `evals.json` | 行为评测（skill-creator 的 `evals.json` schema）。缺省集只执行 `plan` / `explain` / `doctor` / `list-deterministic`，零条真 AWS；`opt_in: true` 的条目真跑 `run` / `submit`，维护者在自己的部署上按需跑 |
| `trigger-eval.json` | description 优化的触发查询集（20 条，含 Cucumber / Playwright / behave 这类 near-miss 负例），喂 skill-creator 的 `run_loop.py --eval-set` |
| `fixtures/<case>/` | 物化式 fixture = 一个「使用方项目」快照：`features/` `steps/` + 真跑录下的 `reports/<run_id>/`；绝对路径一律是占位符 `{{FIXTURE_ROOT}}` |
| `materialize.py` | 把 fixture 物化到仓库外的舞台（替占位符、生成 `bin/gherkai` shim、前置断言、完整性断言）；`--snapshot` 是逆操作、录 fixture 用 |

## 跑一轮

```bash
STAGE=$(python skills/gherkai-evals/materialize.py wiki-search)          # 舞台目录（仓库外）
# 两臂都在舞台里跑、cwd = 舞台、PATH 前置舞台 bin/，提示里只给舞台路径（with-skill 臂另给包内 skill 路径）：
#   with-skill： claude -p "<eval prompt>"  + 让它读 <repo>/cli/gherkai_cli/skills/gherkai/SKILL.md
#   baseline：   claude -p "<eval prompt>"  什么都不给
# 结果按 skill-creator 的布局落 skills/gherkai-workspace/iteration-N/eval-<id>/{with_skill,without_skill}/（已 gitignore）
```

前置：`<repo>/.venv/bin/gherkai` 存在（仓库根 `uv sync`）；要让 midscene 引擎在舞台里可查，先 `cd engines/midscene && npm run build`（shim 会注入 `GHERKAI_WORKER_MIDSCENE_CMD`）。舞台的 shim 把 AWS 相关环境变量清掉并指向空配置文件，所以本机段输出跨机器一致。评测提示与工具白名单禁止任何安装类操作。

description 优化（skill-creator 的循环，`--model` 传当前会话模型）：

```bash
cd <skill-creator 目录> && python -m scripts.run_loop --eval-set <repo>/skills/gherkai-evals/trigger-eval.json \
  --skill-path <repo>/cli/gherkai_cli/skills/gherkai --model <模型> --holdout 0.4 --results-dir <repo>/skills/gherkai-workspace/trigger
```

产出的 description 入库前要过 `cli/tests/test_skill.py` 的 ≤ 1024 字符护栏。

## 录一个 fixture

1. 在仓库外建项目目录，放 `features/` 与 `steps/`（可从 `fixtures/wiki-search/` 拷起点）。
2. **cwd = 该目录、feature 用相对路径**：`gherkai run features/x.feature --report-dir reports`（scope_id / scenario_id 与 `jobs/` 文件名都带这条路径，绝对路径进了文件名占位符救不了）。
3. `python skills/gherkai-evals/materialize.py --snapshot <该目录> <case>`：拷进 `fixtures/<case>`、绝对路径换占位符、删 `*.log`、截图裁成极小 PNG，并扫一遍不得再有绝对路径。
4. `python skills/gherkai-evals/materialize.py <case>` 物化一次，让完整性断言过（`explain --json` 无 `unreadable` / `unsupported_schema`、至少一条 evidence、截图文件都在）。

`.gitignore` 对 `fixtures/**` 开了反白名单（派生品规则会静默吞掉 `reports/` `*.log` `screenshots/`），密钥规则在其后重列；`cli/tests/test_skill.py` 用 `git check-ignore` 两向断言这两件事。
