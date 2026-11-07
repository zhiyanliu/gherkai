#!/usr/bin/env bash
# 发布前镜像 gate 的构建（ADR 0037 决策 8「发布前镜像 gate」）：用一份已经构建好的 worker 产物，按 Dockerfile 的
# local 态（ADR 0037 决策 5「两态」）以 linux/amd64 构建基础镜像，不推送。final stage 的冒烟（`--capabilities`，
# midscene 另有设备接缝模块的 import）在构建中执行，冒烟失败即构建失败、本脚本以非零退出。
# release.yml 与 ci.yml 的 image-gate job 调用的都是本脚本，两条工作流的 gate 由此共用同一份构建逻辑；
# 本地复现 gate 也用同一条命令。
#
# 用法：
#   image_gate.sh novaact  <产物目录>   # 目录里恰有一个 gherkai_worker_novaact-*.whl（uv build 的产物）
#   image_gate.sh midscene <产物目录>   # 目录里恰有一个 gherkai-worker-midscene-*.tgz（npm pack 的产物）
# 产物目录里可以有别的文件（发布链的 dist/ 里还有其它包的 wheel 与 sdist）：本脚本只把匹配的那一个产物拷进一个
# 临时目录作 build context，因为 local stage 会把整个 context COPY 进镜像构建。
# 镜像打本地 tag `gherkai-worker-<引擎>:gate`，便于本地复现后再 `docker run` 查看；CI 上不使用它。

set -euo pipefail

usage='用法: image_gate.sh <novaact|midscene> <产物目录>'
engine="${1:?$usage}"
src="${2:?$usage}"

case "$engine" in
  novaact)
    pattern='gherkai_worker_novaact-*.whl'
    build_arg='WORKER_WHEEL'
    ;;
  midscene)
    pattern='gherkai-worker-midscene-*.tgz'
    build_arg='WORKER_TARBALL'
    ;;
  *)
    echo "::error::第一个参数只能是 novaact 或 midscene，收到：${engine}" >&2
    exit 2
    ;;
esac

if [ ! -d "$src" ]; then
  echo "::error::产物目录不存在：${src}" >&2
  exit 2
fi

# 恰好一个匹配才往下构建：零个说明上游没产出，多个则无法判断哪一个是将要发布的那一份。
# 变量紧挨中文标点时一律加花括号：bash 会把多字节字符的字节并进变量名。
shopt -s nullglob
matches=("$src"/$pattern)
shopt -u nullglob
if [ "${#matches[@]}" -ne 1 ]; then
  echo "::error::${src} 里应恰有一个 ${pattern}，实际 ${#matches[@]} 个：${matches[*]:-（无）}" >&2
  exit 1
fi
artifact="${matches[0]}"
name="$(basename "$artifact")"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ctx="$(mktemp -d)"
trap 'rm -rf "$ctx"' EXIT
# 保留原文件名：pip 从 wheel 文件名解析发行名与版本，改名会被拒（见 engines/novaact/Dockerfile 的 local stage）。
cp "$artifact" "$ctx/$name"

echo "::notice::镜像 gate：${engine} 按 local 态构建，产物 ${name}"
docker build \
  --platform linux/amd64 \
  -f "$repo_root/engines/$engine/Dockerfile" \
  --build-arg WORKER_SOURCE=local \
  --build-arg "$build_arg=$name" \
  -t "gherkai-worker-$engine:gate" \
  "$ctx"
