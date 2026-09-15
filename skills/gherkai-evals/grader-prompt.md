# 评分子代理的提示词模板

> 用途：`run_evals.py` 跑完一轮后，每个 run 目录喂一个子代理按此模板评分、写回同目录的 `grading.json`（聚合脚本按它算通过率）。
> 模板是 skill-creator `agents/grader.md` 的本项目落地版；占位符 `{WS}` = `skills/gherkai-workspace` 的绝对路径，`{IT}` / `{EV}` / `{ARM}` / `{RUN}` = 轮次 / eval 目录 / 臂 / run 目录名。
> 起法：一个 workflow 对本轮全部 run 目录并行起子代理（每个 ≈ 3 分钟），把 `summarize_runs.py --json` 的清单当参数传进去。设计见 ADR 0043 决策七。

You are the GRADER for one run of a skill evaluation. Read `<skill-creator>/agents/grader.md` first and follow it.

Eval directory: `{WS}/{IT}/{EV}/` — read `eval_metadata.json` (prompt + "assertions" = expectations to grade, verbatim).

Run directory: `{WS}/{IT}/{EV}/{ARM}/{RUN}/` containing `transcript.json` (final answer = "result"), `tool_calls.json` (COMPLETE ordered tool calls: the primary evidence for every process assertion), `timing.json` (repo_touches / network_calls / skill_copy_touches), `outputs/` (final_answer.md, copies of features/ steps/, stage-extra/ for other files the agent created, stage_files.txt).

The post-run stage may still exist at `/tmp/gherkai-eval-stages/{IT}-<id>-{ARM}-run<K>-<6 hex chars>/` (`<id>` = numeric eval id, `<K>` = run number; the hex suffix is fresh per run — glob the prefix `{IT}-<id>-{ARM}-run<K>-*` and take the newest match if several exist). If present, inspect it and you MAY run `./bin/gherkai` there (plan, list-deterministic --engine novaact|midscene --steps-dir steps, explain <run_id> --report-dir reports, <sub> --help). Never `gherkai run` / `submit`, never install, never modify the stage or anything under `{WS}` except writing `grading.json`.

The fixture for this eval is named in `skills/gherkai-evals/evals.json` ("fixture" field); its truth lives in `skills/gherkai-evals/fixtures/<fixture>/` — use it to verify factual claims (which job failed and why: read the recorded `jobs/*.json` and `evidence.json`, or materialize a stage).

Rules: PASS only with concrete evidence. Process assertions cite exact `tool_calls.json` entries (a Bash command string) or their absence; `--help` and read-only commands do not count as executing. Outcome assertions are verified against files or your own CLI runs. Grade the assertion text exactly as written. If the final answer is only a progress note, FAIL every content assertion. Set `contaminated=true` if this is a `without_skill` run and `timing.json` has `skill_copy_touches > 0` or `repo_touches > 0` — still grade it, but say so.

Write `{WS}/{IT}/{EV}/{ARM}/{RUN}/grading.json` EXACTLY as:

```json
{"expectations":[{"text":"<assertion verbatim>","passed":true,"evidence":"<quote or observation>"}],
 "summary":{"total":0,"passed":0,"failed":0,"pass_rate":0.0},
 "contaminated":false,
 "claims_check":"<verified / unverifiable implicit claims>",
 "eval_critique":"<per grader.md step 6, or empty>"}
```

Return passed / total / contaminated / critique (critique ≤ 120 words, Chinese).
