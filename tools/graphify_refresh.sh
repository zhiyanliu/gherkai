#!/usr/bin/env bash
# graphify 知识图的 LLM 侧刷新：文档语义抽取 → 社区命名 → wiki。可重复执行；无变化时只花几次命名调用。
#
# 为何需要它：post-commit hook（`graphify hook install` 装的）只做 AST 代码重抽 + 重聚类，不调 LLM。于是
#   ① 文档改动（ADR / README / CLAUDE.md / guides…）不进图——它们要语义抽取；
#   ② 社区集合一变，hook 只能按枢纽节点起临时名（日志「renamed N community(ies) by their hub」）。
# 两项都要 LLM，须周期性手动补。本脚本固化那条命令序列，免得每次重新对齐命令与顺序。
#
# 顺序有意义：抽取会重聚类，命名与 wiki 必须排在最后一次抽取之后。
#   1. graphify . [--force]   增量语义抽取（Bedrock）。单遍后可能残留重复节点——零变化重跑仍报 Deduplicated/Pruned
#                              时再跑一遍，直到不再变（上限 3 遍）。
#   2. graphify label .       重聚类 + LLM 命名全部社区 + 重生成 GRAPH_REPORT.md（涵盖 cluster-only 的全部效果）。
#   3. graphify export wiki   graphify-out/wiki/（index + 每社区一篇），入库供 agent 导航。
#
# 后端 = AWS Bedrock，走标准凭证链。graphify 要求 AWS_PROFILE / AWS_REGION / AWS_DEFAULT_REGION 任一在 env 里
# （~/.aws/config 的 region 不算），缺则本脚本回落 `aws configure get region`，仍无则退 2。
# 各 GRAPHIFY_* 与 PYTHONHASHSEED 有默认值、env 可覆盖；PYTHONHASHSEED=0 与 post-commit hook 一致，钉死聚类随机性。
#
# 在别的机器（如有 Bedrock 凭证的开发跳板机）跑完再 rsync graphify-out/ 回来时，排除 .graphify_root——它存绝对路径，
# 带回会让本地 post-commit hook 重建失败（脚本启动时也会把它校正为当前仓库根）。操作细节见 DEVELOPMENT.md「知识图刷新」。
set -euo pipefail

usage() {
  cat <<'EOF'
用法：tools/graphify_refresh.sh [--force]

  --force     第一步改全量重抽（清理「已离开扫描范围但仍在盘上」的残留节点时用；费用按全仓文档量计）
  -h, --help  本说明

三步：graphify .（抽取到收敛）→ graphify label .（LLM 命名社区 + 重生成报告）→ graphify export wiki。
完整输出落 /tmp/graphify-refresh-<UTC 时间戳>.log，终端过滤掉 graphify 的已知噪声警告；结束打印规模、token 用量与待 commit 清单。
可覆盖的 env：AWS_REGION / AWS_PROFILE、PYTHONHASHSEED、GRAPHIFY_BEDROCK_MODEL、GRAPHIFY_MAX_OUTPUT_TOKENS、
GRAPHIFY_API_TIMEOUT、GRAPHIFY_LLM_TEMPERATURE（默认值见脚本）。
EOF
}

FORCE=0
for a in "$@"; do
  case "$a" in
    --force) FORCE=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "未知参数：$a" >&2; usage >&2; exit 2 ;;
  esac
done

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"

command -v graphify >/dev/null 2>&1 || { echo "错误：找不到 graphify（装法：uv tool install graphifyy）" >&2; exit 2; }

# ---- 后端前置：region env + 凭证可用 ----
if [[ -z "${AWS_PROFILE:-}${AWS_REGION:-}${AWS_DEFAULT_REGION:-}" ]]; then
  region=$(aws configure get region 2>/dev/null || true)
  if [[ -n "$region" ]]; then
    export AWS_REGION="$region"
    echo "AWS_REGION 未设，取 aws 配置里的 region：$region"
  else
    echo "错误：AWS_PROFILE / AWS_REGION / AWS_DEFAULT_REGION 都没有，graphify 选不到 bedrock 后端" >&2
    exit 2
  fi
fi
if command -v aws >/dev/null 2>&1 && ! aws sts get-caller-identity >/dev/null 2>&1; then
  echo "错误：AWS 凭证不可用（aws sts get-caller-identity 失败）——请在有 Bedrock 凭证的机器上跑" >&2
  exit 2
fi

export PYTHONHASHSEED="${PYTHONHASHSEED:-0}"
export GRAPHIFY_BEDROCK_MODEL="${GRAPHIFY_BEDROCK_MODEL:-global.anthropic.claude-opus-5}"
export GRAPHIFY_MAX_OUTPUT_TOKENS="${GRAPHIFY_MAX_OUTPUT_TOKENS:-32768}"
export GRAPHIFY_API_TIMEOUT="${GRAPHIFY_API_TIMEOUT:-1800}"
export GRAPHIFY_LLM_TEMPERATURE="${GRAPHIFY_LLM_TEMPERATURE:-none}"

# ---- .graphify_root 校正（从别的机器 rsync 回来的会带对方的绝对路径）----
rootfile=graphify-out/.graphify_root
if [[ -f "$rootfile" ]] && [[ "$(cat "$rootfile")" != "$ROOT" ]]; then
  echo "校正 $rootfile：$(cat "$rootfile") → $ROOT"
  printf '%s' "$ROOT" > "$rootfile"
fi

LOG=/tmp/graphify-refresh-$(date -u +%Y%m%dT%H%M%SZ).log
: > "$LOG"
NOISE='RuntimeWarning: semantic cache skipped|^[[:space:]]*_scs\($'
echo "仓库根：$ROOT"
echo "完整日志：$LOG"
echo "env：AWS_REGION=${AWS_REGION:-} AWS_PROFILE=${AWS_PROFILE:-} PYTHONHASHSEED=$PYTHONHASHSEED GRAPHIFY_BEDROCK_MODEL=$GRAPHIFY_BEDROCK_MODEL GRAPHIFY_MAX_OUTPUT_TOKENS=$GRAPHIFY_MAX_OUTPUT_TOKENS GRAPHIFY_API_TIMEOUT=$GRAPHIFY_API_TIMEOUT GRAPHIFY_LLM_TEMPERATURE=$GRAPHIFY_LLM_TEMPERATURE"

# step <名称> <命令...>：全输出进 $LOG，终端过滤噪声；失败即退出（退出码 = graphify 的）
step() {
  local name=$1; shift
  echo
  echo "===== [$(date -u +%FT%TZ)] $name: $*"
  "$@" </dev/null 2>&1 | tee -a "$LOG" | { grep -Ev "$NOISE" || true; }
  local rc=${PIPESTATUS[0]}
  if (( rc != 0 )); then
    echo "===== $name 失败 rc=$rc（完整日志：$LOG）" >&2
    exit "$rc"
  fi
}

# ---- 1. 抽取到收敛 ----
extract_args=(.)
(( FORCE )) && extract_args+=(--force)
pass=1
max_pass=3
while :; do
  before=$(wc -l < "$LOG")
  step "抽取 第 $pass 遍" graphify "${extract_args[@]}" --backend bedrock
  seg=$(tail -n +"$((before + 1))" "$LOG")
  if grep -q '0 code, 0 docs, 0 papers, 0 images changed' <<<"$seg" \
     && ! grep -Eq 'Deduplicated [1-9]|Pruned [1-9]' <<<"$seg"; then
    echo "抽取已收敛（第 $pass 遍零变化、无去重）"
    break
  fi
  if (( pass >= max_pass )); then
    echo "警告：$max_pass 遍后抽取仍未收敛，继续后续步骤——请检查日志 $LOG" >&2
    break
  fi
  extract_args=(.)   # 第二遍起不再 --force
  pass=$((pass + 1))
done

# ---- 2. 重聚类 + LLM 命名 + 报告 ----
step "命名社区并重生成报告" graphify label . --backend bedrock

# ---- 3. wiki ----
step "导出 wiki" graphify export wiki

# ---- 汇总 ----
echo
echo "===== 汇总"
grep -E 'Graph: [0-9]+ nodes|Done - [0-9]+ communities|Wiki: [0-9]+ articles|tokens: ' "$LOG" | sed 's/^/  /'
echo "  待 commit（graphify-out/ 下的入库项）："
git status --short -- graphify-out/ 2>/dev/null | sed 's/^/  /' || true
echo "  例：git add graphify-out/graph.json graphify-out/GRAPH_REPORT.md graphify-out/manifest.json graphify-out/wiki && git commit"
