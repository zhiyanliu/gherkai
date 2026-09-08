# CI 与发布链（`.github/`）

> **定位**：本文件讲**怎么用、怎么一次性配好、怎么本地校验**。决策与理由的权威在
> [ADR 0037 决策 8「CI 发布链与占名」](../../docs/adr/0037-distribution-and-packaging.md)
> （版本单旋钮见其决策 2b/7，worker 镜像两层分工见 [ADR 0038](../../docs/adr/0038-worker-image-delivery.md)）；
> 冲突时以 ADR + workflow 文件本身为准，别在这里新立决策。

## 两条工作流

| 文件 | 触发 | 干什么 |
|---|---|---|
| `ci.yml` | push `main` / 所有 PR / 手动 | ① `uv sync --locked` + 根 `pytest`（全 workspace 成员，含 deploy_aws 的 CDK synth 测试）；② midscene `npm ci && npm run build && npm test`；③ `uv build --all-packages` smoke + 产物校验 |
| `release.yml` | push tag `v*` | gate（tag 形态 + 算出的版本==tag）→ ① PyPI → ② npm → ③ GHCR 基底镜像 → ④ GitHub Release |

发布是**一个动作**：`git tag vX.Y.Z && git push origin vX.Y.Z`。版本真源只有 git tag
（pyproject / package.json 里没有手写版本号），CI 从 tag 派生五个 wheel 的版本、npm 包版本、
镜像 tag、Release 名。

### `release.yml` 的 job 图与重跑语义

```
build（gate + uv build --all-packages + 产物校验 + 上传 artifact）
 ├─▶ pypi   （download artifact → attest-action 生成 PEP 740 → uv publish，OIDC 免密）
 ├─▶ npm    （npm version <tag> → npm ci → build → npm publish --provenance）
 │
 └─▶ images （needs: build + pypi + npm；matrix novaact/midscene → GHCR）
      └─▶ release（GitHub Release，作 changelog 锚点）
```

- **`images` 依赖 `pypi`/`npm` 且带「等索引可见」一步**：基底镜像的 CI 形态按版本装已发行的 worker 包
  （ADR 0037 决策 5「两态」），而上传成功 ≠ 立刻可装（索引过 CDN）。等待逻辑与完整理由在
  `.github/scripts/wait_for_index.sh` 的头注释里。
- **单独重跑 `images` 是「PyPI 已发、镜像缺失」半发布态的修复动作**（ADR 0037 决策 8）：对同一 tag 幂等，
  且**重跑旧版本不会动 `latest`**——`latest` 只在「本 tag 是全仓库版本序最大的**正式发行** tag」时才推。
- **`pypi` 可重跑**：`uv publish --check-url` 跳过已存在且逐字节相同的文件（内容不同则报错，不静默覆盖）。
- **`npm` 可重跑**：publish 前先 `npm view` 探一次，已发行就跳过（npm 不允许重发同版本）。
- **fork 不会误发**：`pypi` / `npm` 两个 job 带 `if: github.repository == 'zhiyanliu/gherkai'`。
- **只认正式发行 tag `vX.Y.Z`**：`v1.4.0rc1` 这类预发行在 gate 第一步就被拦——它是合法 PEP 440
  但不是合法 semver（npm 要 `1.4.0-rc.1`），而 ADR 0037 决策 2b 明确不做 PEP 440→semver 的转换件；
  放进来就会「PyPI 发成功、npm 挂在 `npm version` 上」。演练 tag 因此**别 push 到本仓库**（下节）。

## 一次性人工前置（可一遍做完）

### 1. PyPI 占名（先于一切）

七个名字各真传一版 `0.0.0` 占位 sdist——**pending publisher 不占名**（他人先注册即失效，ADR 0037 决策 8）。

现状（2026-09-08 核对 `https://pypi.org/pypi/<name>/json`）：**七名全部已占**（各一版 `0.0.0` 占位，owner `Zhi Yan Liu`）——
`gherkai` / `gherkai-runtime` / `gherkai-core` / `gherkai-worker-novaact` / `gherkai-deploy-aws`（真发行）、`gherkai-cli` / `gherkai-worker-midscene`（防混淆占位，永不发真内容）。

npm 侧已占：`@gherkai/worker-midscene@0.0.0` 与非 scoped 的 `gherkai@0.0.0`（maintainer `liuzhiyan`）。

### 2. PyPI trusted publisher × 5（只有真发行的五个需要）

对 `gherkai` / `gherkai-runtime` / `gherkai-core` / `gherkai-worker-novaact` / `gherkai-deploy-aws`
逐个进 *Manage project → Publishing*（项目还不存在时用 *Your account → Publishing* 建 pending publisher，
但见上：pending 不占名，占名要真传），填：

- Owner：`zhiyanliu`
- Repository name：`gherkai`
- Workflow name：`release.yml`
- Environment name：**留空**——`release.yml` 的 `pypi` job 没声明 `environment:`，这栏填了反而对不上、
  publish 被拒。（想加人工审批门就先给 job 加 `environment: pypi`、再在这里填同名，两边必须一致。）

两个防混淆占位名（`gherkai-cli` / `gherkai-worker-midscene`）**不配** publisher：它们永不由 CI 发布。

### 3. npm token → repo secret `NPM_TOKEN`

npmjs.com → *Access Tokens* → 建 **Automation** 类型 token（绕开 2FA 的交互，专给 CI），
存成仓库 secret，名字必须是 **`NPM_TOKEN`**（`release.yml` 的 `npm` job 按此名取）。

- token 权限需覆盖 `@gherkai` scope 的 publish。
- `--provenance` 还要求：仓库**公开**、`package.json` 的 `repository.url` 与实际仓库一致（已满足）、
  runner 是 GitHub 托管的（已满足）。
- 可选的去 token 路线：npm 自己也支持 trusted publishing（OIDC），但要求 runner 上 npm ≥ 11.5.1
  （Node 22 自带的是 10.x），得多一步 `npm i -g npm@^11.5.1`。当前**没接**，接了可以删掉这个 secret。

### 4. GHCR：首次推送后把两个 package 改成 public

推 GHCR 用 `GITHUB_TOKEN`，**不需要任何 secret**；但**首次发布的 package 默认是 private**。
基底镜像要能被使用方的部署机匿名 `docker pull`（`gherkai deploy` 的「同步基底」一步，ADR 0038），
所以首个 release 跑完后进 *Packages → gherkai-worker-novaact / gherkai-worker-midscene →
Package settings → Change visibility → Public*（各一次，之后一直有效）。

### 5. 仓库本身必须是 public

npm provenance 的验证要求源仓库公开（ADR 0037 背景里的托管决定已是 public）。

## TestPyPI 演练（推正式 tag 之前排一次）

`uv publish` 认 `[[tool.uv.index]]` 里的 `publish-url`。**临时**加到根 `pyproject.toml`（演练完删掉，
别长期留在库里——它不是产品配置）：

```toml
[[tool.uv.index]]
name = "testpypi"
url = "https://test.pypi.org/simple/"
publish-url = "https://test.pypi.org/legacy/"
explicit = true
```

然后：

```bash
uv build --all-packages --out-dir dist
uv run --no-project python .github/scripts/check_dist_metadata.py --dist dist --expect-version 1.4.0
uv publish --index testpypi          # 本地跑要 TestPyPI token（UV_PUBLISH_TOKEN）；CI 里配 TestPyPI 的 trusted publisher
```

注意三条：

- **`uv publish --index <name>` 要求 checkout 里有 `pyproject.toml`**（它得读 `[[tool.uv.index]]`）——
  这就是 `release.yml` 的 `pypi` job 明明只上传产物、却仍带一步 checkout 的原因。
- **TestPyPI 是独立账号体系**，占名与 trusted publisher 都要在 test.pypi.org 上另配一遍。
- **本地构建出的版本是非纯净的**（形如 `1.3.0.post16.dev0+<sha>`，ADR 0037 决策 2b 把
  `dirty`/`metadata` 显式打开了），**PyPI 与 TestPyPI 都拒收带 `+` 本地段的版本**——真要演练上传，
  得站在一个干净的 tag commit 上。演练用的 tag **只打本地、不 push**（`git push` 上来就触发
  `release.yml` 往真 PyPI 发；即便被 gate 的形态检查拦下，也是一次没必要的红叉）。
  不打 tag 时用 `uv publish --dry-run` 走完除上传外的全部流程。

## 本地静态校验（不推 tag 也能查大部分）

```bash
# 1) YAML 能解析 + GitHub Actions 语义（表达式/上下文/needs 图/matrix 引用/常见 action 输入名）
#    actionlint 是一次性外部工具，别入库（见 CLAUDE.md「工作方式」：一次性脚本不进 tools/）
actionlint .github/workflows/*.yml

# 2) 产物校验脚本本身（发布链的 gate 与 CI smoke 共用同一份）
uv build --all-packages --out-dir dist
uv run --no-project python .github/scripts/check_dist_metadata.py --dist dist

# 3) 等索引脚本（拿任意已发行的包版本试；退 0 = 可见）
WAIT_ATTEMPTS=1 bash .github/scripts/wait_for_index.sh pypi packaging 24.2
WAIT_ATTEMPTS=1 bash .github/scripts/wait_for_index.sh npm @midscene/web 1.9.8
```

**只有推真 tag 才能验的**：trusted publishing 的 OIDC 交换、attestation 真的落到 PyPI 上、
npm provenance、GHCR 推送与包可见性、以及「等索引可见」在真实传播窗口下的表现。

## 两态基底 Dockerfile 的本地态 build（不发行也能验镜像）

CI 的 `images` job 用 index 态（按 tag 版本装已发行包）；发行前要验镜像内容，用 local 态喂本地产物——命令与 build-arg
见各 `engines/*/Dockerfile` 头注释（`uv build --package gherkai-worker-novaact` 出 wheel、`npm pack` 出 tarball，
`--build-arg WORKER_SOURCE=local`，context = 放产物的目录）。冒烟（不需要 AWS）：`docker run --rm --platform linux/amd64 <镜像> python -m gherkai_worker_novaact --list-deterministic` /
`… <镜像> gherkai-worker-midscene --list-deterministic`（要给完整命令：node 基底的 entrypoint 会把以 `-` 开头的首参当 node 选项）。index 态只能在首个正式发行后验（占位 `0.0.0` 是空包）。

## 维护

- **版本旋钮**在两个 workflow 的 `env:` 里（`UV_VERSION` / `PYTHON_VERSION` / `NODE_VERSION`），
  两边保持同值——发布路径与 CI 路径分叉了，CI 绿就不再代表发布链能跑。
  `UV_VERSION` 还有个下限：`uv publish` 上传 PEP 740 attestation 需 ≥ 0.9.12。
- **action 一律钉到精确 tag**（`astral-sh/setup-uv@v10.0.1` 这种），不用浮动大版本：
  `setup-uv` 从 v8 起就没再发浮动 `v8`/`v9`/`v10` tag，浮动写法在它身上直接解析失败；
  其余 action 有浮动 tag 也照钉，升级是有意动作。
- **`.github/scripts/` 是长期资产**（与 `tools/` 同性质）：改它守 CLAUDE.md 的代码/文档纪律，
  注释引 ADR 与稳定符号。
