#!/usr/bin/env bash
# Claude Code PostToolUse hook：派生文件同步（项目级，随仓库入库；.claude/settings.json 挂在 Edit / Write / MultiEdit / Bash 之后）。
#
# ① skill 契约副本（ADR 0043 决策四）：源 docs/internals/cli-json-contract.md 或渲染器 tools/render_skill_contract.py 改了，
#    副本 cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md 就会漂——这里用渲染器 --check 发现漂移即重渲染，
#    并经 hookSpecificOutput.additionalContext 告诉 agent（副本与源同 commit）。
# ② 文档图（ADR 0045 决策七）：docs/diagrams/<name>.json 比同名 .svg 新 → 只提醒跑 tools/build_diagrams.mjs，不自动跑
#    （重建要起 Chrome、20 秒量级，不该挂在每次工具调用上）。
#
# 为什么每次工具调用都跑、不按文件路径筛：检查本身 0.1 秒量级；Bash 里用脚本改文件的路径也能覆盖。
# 边界：只在 Claude Code 里生效；Codex / 人手编辑仍由 cli/tests/test_skill.py 与 cli/tests/test_user_docs.py 兜底。
# 永远 exit 0：这是同步与提醒，不阻断任何工具。
set -u
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0
export PATH="$PATH:$HOME/.local/bin"   # hook 进程的 PATH 未必含 uv 的安装目录
cat >/dev/null                          # 事件 JSON 用不上，读掉以免管道阻塞

notes=()

if [ -f tools/render_skill_contract.py ] && command -v uv >/dev/null 2>&1; then
  if ! uv run --quiet python tools/render_skill_contract.py --check >/dev/null 2>&1; then
    if out=$(uv run --quiet python tools/render_skill_contract.py 2>&1); then
      notes+=("skill 契约副本已按源重渲染（${out}）——副本 cli/gherkai_cli/skills/gherkai/references/cli-json-contract.md 与源同 commit。")
    else
      notes+=("skill 契约副本与源不同步，且自动重渲染失败：${out}")
    fi
  fi
fi

if [ -d docs/diagrams ]; then
  stale=$(python3 - <<'PY'
import glob, os
out = []
for j in sorted(glob.glob("docs/diagrams/*.json")):
    s = j[:-5] + ".svg"
    if not os.path.exists(s) or os.path.getmtime(j) > os.path.getmtime(s) + 1:
        out.append(os.path.basename(j))
print(" ".join(out))
PY
  )
  if [ -n "$stale" ]; then
    notes+=("文档图源比导出的 SVG 新：${stale}——跑 node tools/build_diagrams.mjs docs/diagrams/<name>.json 重出 SVG；已发布到 Pages 的图连 HTML 一起重新 git add。")
  fi
fi

if [ ${#notes[@]} -gt 0 ]; then
  python3 -c 'import json, sys; print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": " ".join(sys.argv[1:])}}, ensure_ascii=False))' "${notes[@]}"
fi
exit 0
