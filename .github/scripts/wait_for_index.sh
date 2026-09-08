#!/usr/bin/env bash
# 等某个包版本在索引上「可见」——基底镜像 build 依赖已发行包索引可见（ADR 0037 决策 8）。
#
# 为什么要等：上传成功 ≠ 立刻可装。PyPI / npm 的 simple index 与 registry 元数据都过 CDN，
# 上传返回 200 之后到 `pip install <name>==<版本>` 能解析到，中间有秒级到分钟级的传播窗口。
# 基底镜像的 CI 形态按版本装已发行的 worker 包（ADR 0037 决策 5「两态」），赶在窗口里 build
# 会以「no matching distribution」/「No matching version found」形式随机失败——那是一次
# 半发布态（PyPI 已发、镜像缺失），修起来要人工重跑镜像 job。等一下比重跑便宜。
#
# 用法：
#   wait_for_index.sh pypi gherkai-worker-novaact 1.4.0
#   wait_for_index.sh npm  @gherkai/worker-midscene 1.4.0
# 退 0 = 已可见；退 1 = 超时（调用方应视作失败，重跑本 job 即可继续）。

set -euo pipefail

kind="${1:?用法: wait_for_index.sh <pypi|npm> <name> <version>}"
name="${2:?缺 name}"
version="${3:?缺 version}"
attempts="${WAIT_ATTEMPTS:-30}"   # 30 × 10s = 5 分钟上限
interval="${WAIT_INTERVAL:-10}"

case "$kind" in
  pypi)
    # PEP 691 的 JSON simple API：拿的就是 uv/pip 解析时读的那张表（不是 /pypi/<name>/json 的
    # 项目元数据——后者与 simple index 的缓存不是同一份，早可见不代表装得到）。
    url="https://pypi.org/simple/${name}/"
    header='Accept: application/vnd.pypi.simple.v1+json'
    ;;
  npm)
    # registry 的 packument 按版本取：404 = 还没可见，200 = 该版本已在元数据里。
    url="https://registry.npmjs.org/${name//\//%2F}/${version}"
    header='Accept: application/json'
    ;;
  *)
    echo "::error::第一个参数只能是 pypi 或 npm，收到：$kind" >&2
    exit 2
    ;;
esac

for i in $(seq 1 "$attempts"); do
  body="$(curl -fsSL -H "$header" "$url" 2>/dev/null || true)"
  if [ -n "$body" ]; then
    case "$kind" in
      pypi)
        # 版本既出现在 PEP 700 的 versions 数组里，也出现在各产物文件名里；两者任一命中即算可见。
        if printf '%s' "$body" | grep -qF -- "\"${version}\"" || printf '%s' "$body" | grep -qF -- "-${version}-py3-none-any.whl"; then
          echo "::notice::${name}==${version} 已在 PyPI simple index 可见（第 ${i} 次探测）"
          exit 0
        fi
        ;;
      npm)
        if printf '%s' "$body" | grep -qF -- "\"version\":\"${version}\"" || printf '%s' "$body" | grep -qF -- "\"version\": \"${version}\""; then
          echo "::notice::${name}@${version} 已在 npm registry 可见（第 ${i} 次探测）"
          exit 0
        fi
        ;;
    esac
  fi
  echo "第 ${i}/${attempts} 次探测未见 ${name} ${version}，${interval}s 后重试…"
  sleep "$interval"
done

echo "::error::等 ${name} ${version} 在 ${kind} 索引上可见超时（${attempts} × ${interval}s）。上游发布 job 若已成功，重跑本 job 即可（对同一 tag 幂等，ADR 0037 决策 8）"
exit 1
