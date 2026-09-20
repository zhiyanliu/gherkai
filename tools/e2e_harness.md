# e2e_harness 使用说明（worker 端到端实际运行验证）

> **读者：** 后续接手 worker 端到端验证的 contributor 侧 AI agent（也含人）。**本文是操作手册**：调用方式、结果判读、实际运行陷阱。
> **机制原理**（harness 如何忠实复现 adapter spawn 环境、三通道、grace 测量）见 `e2e_harness.py` 顶部 docstring，不在此复述（单一事实源）。
> **相关设计：** ADR 0024（worker↔core 协议 / 协作式停止 / grace / I/O 边缘可注入接口）、ADR 0029（产物→S3 / act·scenario 边界的安全点提前上传 / 固有残余）、ADR 0032（Fargate 中断丢失量级 + 真容器 grace 校准）。

## 定位与适用场景

`e2e_harness.py` 是 **opt-in 手动端到端验证脚本，不进 pytest 默认套件**：它跨真实边界运行，因此**产生真实 AWS 费用、需网络+凭证、单次 ~1-2min**，验证的是**单测的 mock 覆盖不到、只能真实运行**的那一层（对齐 CLAUDE.md「绿≠对：识别结论的证据边界」）。具体覆盖哪几项真实行为见 `e2e_harness.py` 顶部 docstring。

**中断只是它的能力之一**（`--interrupt`）：`--interrupt none` 的 baseline 同样可运行，用于验证「事件流端到端正常 + 三通道分离 + 零行为变化」（如 worker I/O 重构后的回归）。纯逻辑回归仍由各引擎单测覆盖（Nova `engines/novaact/tests/test_*.py`、Midscene `engines/midscene/src/worker/*.test.mts`、`core/tests/test_subprocess_engine.py`）。

**适用场景**：改动 worker 的中断路径 / 会话清理 / grace / 安全点提前上传 / 上传超时 / **job 入口·事件出口（I/O 边缘）**后，实际运行确认承重假设仍成立；另可验**使用方确定性 step 目录在真 worker 下被加载**（`--steps-dir`，ADR 0037 决策 4——加载失败 worker 会降级成 AI step，单测照不出）。日常逻辑改动先运行单测；只有涉及上述「只能真实运行验证」的真实边界才动 harness。

## 前置条件

- **AWS 凭证 + region us-east-1**（default profile 即可）。
- **宿主 export 的 `GHERKAI_*` 一律不生效**：harness 与 adapter 同一起手式，组合根拥有的 worker env（`GHERKAI_STEPS_DIR` / `GHERKAI_NO_ARTIFACTS` / `GHERKAI_EXTRA_HTTP_HEADERS`）先被显式清空；只有 `--steps-dir`（或环境变量 `HARNESS_STEPS_DIR`）给的值会被显式注回。起手行会回显 `steps_dir=…`（`None` 表示已清空），据此确认注入生效。
- **一个可写 S3 桶**，经环境变量 `HARNESS_S3_BUCKET` 传入（**勿硬编码**账号相关值）。运行结束后自行清理桶内 `harness/<run-id>/` 前缀（见下「清理」）。
- 用**仓库根的 workspace venv** 运行（`uv run python …`，等价 `.venv/bin/python`）：harness 复用真实 `gherkai_core.scope.plan` 生成 job（避免手写 JSON 造成漂移），并复用 `gherkai_runtime.compose` 的 worker 定位链；根 `uv sync` 已把 `gherkai_core` 与 `gherkai_runtime` 都装成 editable（ADR 0037 决策 2）。**cwd 与 `PYTHONPATH` 都不限**，这由 editable 安装保证：harness 不改 `sys.path`，只由 `__file__` 派生仓库根推导 `features/` 路径。worker 路径不由它推导，见下条四级定位链。
- **worker 经四级定位链启动**（与 CLI 同一真源，ADR 0037 决策 3），harness 不按仓库布局拼接路径：novaact 随仓库根 `uv sync` 装进同一 workspace venv，即命中「同 venv `-m` 入口」，无需独立 venv；midscene 需先在 `engines/midscene/` 执行 `npm install && npm run build` 生成 `dist/bin.mjs`，再用 `GHERKAI_WORKER_MIDSCENE_CMD="node <仓库根绝对路径>/engines/midscene/dist/bin.mjs"` 显式覆写（第一级）。四级全 miss 抛 `WorkerNotFoundError`，并附安装指引。

## 调用

```bash
# 命令使用相对路径，且 uv run 须在 workspace 内，故从仓库根执行（harness 自身不依赖 cwd，见「前置条件」）：
HARNESS_S3_BUCKET=<你的可写桶> uv run python tools/e2e_harness.py \
    --engine <novaact|midscene> \
    --feature <feature 名，不含 .feature 后缀> \
    --interrupt <none|connect|act|between|scenario|scope_end> \
    --run-id <本次唯一 id，作 S3 prefix + 本地临时目录名> \
    --grace-cap <秒，SIGTERM 到 SIGKILL 的墙钟上限，默认 30> \
    --steps-dir <使用方确定性 step 目录，可选>
```

参数：

| 参数          | 默认                   | 说明                                                                                 |
|---------------|------------------------|--------------------------------------------------------------------------------------|
| `--engine`    | `novaact`              | `novaact` / `midscene`                                                               |
| `--feature`   | `wikipedia_assertions` | `features/<名>.feature`，**不含后缀**                                                 |
| `--votes`     | `1`                    | AI 断言投票次数（ADR 0014）                                                            |
| `--interrupt` | `none`                 | 中断时机，见下表                                                                      |
| `--run-id`    | **必填**               | 本次唯一 id → S3 `harness/<run-id>/` + 本地 `/tmp/harness-runs/<run-id>/` |
| `--grace-cap` | `30.0`                 | SIGTERM 后超过该墙钟 worker 仍未退出 → 判 `hung=true` 并发 SIGKILL 强制终止          |
| `--steps-dir` | `HARNESS_STEPS_DIR` / 空 | 使用方确定性 step 目录（ADR 0037 决策 4），注给 worker 的绝对路径；不给则 worker 一侧无使用方 step；目录不存在直接报错退出 |

### `--interrupt` 中断时机

| 值          | SIGTERM 落点                                        | 验证目标                                                                                                                                                           |
|-------------|-----------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `none`      | 不中断（baseline）                                    | 正常完成路径：所有产物应进 S3、`n_lost=0`、删本地                                                                                                                     |
| `connect`   | 建连中（scope_started 前，2s 定时）                    | 会话建立过程中被终止：不泄漏会话、进程干净退出                                                                                                                       |
| `act`       | 第一个 act 执行中途（step_started 后 3s）             | act 中途中断：会话释放 + in-flight 产物处置                                                                                                                         |
| `between`   | 第一个 step_done 后                                 | step 边界中断：已完成 act 产物已提前上传                                                                                                                            |
| `scenario`  | **第一个 scenario_done 后 3s、下一 scenario 运行中** | **scenario 边界提前上传（Midscene log）**：已完成 scenario 的 log 应已进 S3。**需多 scenario 归一个 scope 的 feature**（见下「实际运行陷阱」第 1 条 `@scope:` 分组），否则该时机不触发，记为无效样本 |
| `scope_end` | 所有 scenario 完成、scope 末 flush 前                | flush 前中断：暴露「只在 scope 末上传的剩余产物」残余（Nova summary / Midscene log）                                                                                  |

## 报告判读

harness 结尾打印 `=== HARNESS_REPORT_JSON ===` + 一段 JSON。关键字段：

| 字段                         | 含义 / 判读方式                                                                                                      |
|------------------------------|----------------------------------------------------------------------------------------------------------------------|
| `hung`                       | **`true` 即失败**：worker SIGTERM 后 grace-cap 内没退、被 SIGKILL。中断正确性的首要红线                                 |
| `exit_code`                  | 正常/协作停止应 `0`；网络耗尽 `80`（`EX_WORKER_NETWORK`）；会话释放失败 `1`                                              |
| `grace_s`                    | SIGTERM→worker 退出实测秒数（`none` 时为 null）。应远小于 grace-cap                                                         |
| `sample_valid`               | **判读的第一个字段**。`false` 表示无效样本，两类：① 中断过早、盘与 S3 均为空（`n_lost=0` 源于无可丢失的文件，而非提前上传已保全）→ 换更晚时机重新运行；② 指定了 `--interrupt <时机>` 但该时机未触发、全程退化为 baseline（`kill_phase=null`；已知两条：`scenario` 时机遇到单 scenario scope、`connect` 的 2s 定时器发现建连已完成）→ 换时机，或换「多 scenario 归一个 `@scope`」的 feature 重新运行。属哪一类见 `sample_note` |
| `sample_note`                | 以自然语言说明 `sample_valid` 的判定依据与丢失量                                                                     |
| `lost_on_fargate` / `n_lost` | **盘上有、S3 无**的文件，即 Fargate 容器盘销毁时会真实丢失的部分；subprocess 下这些文件留在本地盘、**非真实丢失**       |
| `bytes_lost`                 | 同上字节数                                                                                                           |
| `disk_files` / `s3_files`    | 中断后盘上与 S3 上的文件清单（含 size）                                                                                |
| `scope_done_emitted`         | 中断路径应 `false`（不 emit scope_done、不走 flush）；正常完成 `true`                                                    |
| `kill_phase`                 | SIGTERM 实际落在哪个时机（`connect`/`act_midway`/`between_steps`/`after_scenario1`/`scope_end`）。**非空即信号已真实投递**（时机已触发但 worker 已先退出时不予记录，避免「有 phase 无投递」的假阳性）。`--interrupt none` 本就为 `null`；**指定了中断时机却为 `null`，表示本次未发出 SIGTERM**（该时机未触发或 worker 已先退出），此时任何丢失/提前上传结论都不成立 |
| `counts`                     | `step_started`/`step_done`/`scenario_done`/`n_scenarios`：核对中断落点是否如预期；`scenario` 时机要求 `n_scenarios>1`，否则该时机不触发（见下「实际运行陷阱」第 1 条 `@scope:` 分组） |

### 判读要点（易误判处）

- **判读顺序：`sample_valid` 先于 `n_lost`**。`sample_valid=false` 时 `n_lost=0` 不具含义。此前已发生过误判：Midscene `act` 时机中断过早、盘上为空、`n_lost=0` 被读成「提前上传生效」，实为无效样本。
- **`n_lost=0` 不等于「零残余」**。harness 的 lost 判据是**文件名**层面的「盘有 S3 无」。若某文件名已在 S3（已被提前上传过），而盘上是更大的版本（其后又有 append），`n_lost` 记 0，但存在**字节级增量残余**。要量化提前上传实际已上传的数据量，需**逐文件对比 disk 与 S3 的 size**。scenario 提前上传的验证即以此坐实：scenario1 的 log 已进 S3，scenario2 的增量为 disk>S3。
- **验证「提前上传的因果」须交叉核对时序**：`kill_phase` 非空 + `scope_done_emitted=false` + worker stderr 出现 `signal received`/`session shutdown`，三者同时成立即表明确实走了中断退出路径；而 scope 末的整目录 flush 只在正常完成路径执行，中断路径在它之前已 return。据此才能证明 S3 里的产物只可能来自**边界提前上传**，而非退出路径一并上传。**「flush 日志」不构成判据**：两个 worker 的 scope 末 flush 成功时不输出任何日志（只有失败与补救提示中出现 flush 字样），因此「未见 flush 日志」对正常路径同样成立。

## 实际运行陷阱（实践中已遇到，需避开）

1. **plan 按 `@scope:` tag 分组，不是「一 feature 一 scope」**（ADR 0025）。未标 `@scope:` 的 scenario **各自独立成单 scenario scope**。harness 取**匹配 `--engine` 的第一个 job**（单引擎 feature 下即 `jobs[0]`；混引擎 feature 如 engine_routing 靠 `@engine:` tag 分引擎时，取本次 `--engine` 对应引擎的 job）作为验证对象。
   - **验 `scenario` 时机必须用多 scenario 归一个 scope 的 feature**，否则 `jobs[0]` 只有 1 个 scenario，`scenario` 时机的 `n_scen>1` 条件不满足，SIGTERM 不发出，本次退化为完整 baseline。
   - **现成可用的 feature**：`features/concurrency_and_scope.feature` 的 `@scope:browse`（2 个 scenario 共享会话，`jobs[0]`）。运行前可用 `gherkai_core.scope.plan` 确认 `jobs[0]` 的 scenario 数：
     ```bash
     uv run python -c "from gherkai_core.scope import plan,PlanConfig,FeatureSource; from pathlib import Path; f='features/concurrency_and_scope.feature'; print([len(j.scenarios) for j in plan([FeatureSource(uri=f,text=Path(f).read_text())],PlanConfig(default_engine='midscene',default_assertion_votes=1))])"
     ```
2. **wikipedia 的 SSL 环境问题（Nova 侧更易命中）**：某些网络下到 `www.wikipedia.org` 的 SSL 握手会挂起（`SSLEOFError`，Nova SDK 本地 strict cert verify）。**Midscene 走 AgentCore 云浏览器、不受本地 SSL 影响**；Nova SDK 在本地建 CDP 时可能命中。若 Nova 全场景 SSL 失败，先直连测握手确认属环境问题，可临时改用访问简单站点的 feature 规避。
3. **scenario 边界提前上传只有 Midscene 具备**（Nova 侧 `session_summary.json` 在 scenario 边界尚不存在，无可提前上传的对象，见 ADR 0029）。因此 Nova 的 `scenario` 时机无法验证 log 的提前上传。
4. **产生真实 AWS 费用**：AgentCore 会话 + 模型调用 + S3。质量优先，同时避免浪费：每个时机运行一次即可，不必穷举矩阵；用短 feature 控制成本。

## 清理（每次运行结束后）

harness 不自动清理 S3 桶。每个 run 在 `harness/<run-id>/` 前缀下留有对象，运行结束后执行：

```bash
AWS_REGION=us-east-1 uv run python -c "
import boto3
s3=boto3.client('s3',region_name='us-east-1')
b='<你的桶>'; p='harness/<run-id>/'
objs=s3.list_objects_v2(Bucket=b,Prefix=p).get('Contents',[])
if objs: s3.delete_objects(Bucket=b, Delete={'Objects':[{'Key':o['Key']} for o in objs]})
print('deleted', len(objs))
"
```

本地临时产物落 `/tmp/harness-runs/<run-id>/`（系统临时目录），用完自行删除。
