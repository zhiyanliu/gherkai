# e2e_harness 使用说明（worker 端到端真跑验证）

> **读者：** 后续接手 worker 端到端验证的 AI tool（也含人）。**这是操作手册**——怎么调用、怎么判读结果、有哪些真跑陷阱。
> **机制原理**（harness 如何忠实复现 adapter spawn 环境、三通道、grace 测量）见 `e2e_harness.py` 顶部 docstring，不在此复述（单一事实源）。
> **相关设计：** ADR 0024（worker↔core 协议 / 终止契约 / grace / I/O 边缘可注入接口）、ADR 0029（产物→S3 / act·scenario 边界抢传 / 固有残余）、ADR 0032（Fargate 中断丢失量级 + 真容器 grace 校准）。

## 这是什么 / 什么时候用

`e2e_harness.py` 是 **opt-in 手动端到端验证脚本，不进 pytest 默认套件**。它真 spawn worker、真喂 job（stdin）、真收事件流（`EVENTS_FD`）、真开 AgentCore 会话、真写 S3——**烧真 AWS 钱、需网络+凭证、单次 ~1-2min**。它验的是**单测的 mock 覆盖不到、只能真跑**的那一层（对齐 CLAUDE.md「绿≠对：识别结论的证据边界」）：真 greenlet / 真会话 / 真进程退出码 / 真 grace 秒数 / 真事件流字节 / 真中断丢失量。

**中断只是它的能力之一**（`--interrupt`）——它同样能跑 `--interrupt none` 的 baseline 验「事件流端到端正常 + 三通道分离 + 零行为变化」（如 worker I/O 重构后的回归）。纯逻辑回归仍由各引擎单测覆盖（Nova `worker/test_*.py`、Midscene `worker/*.test.ts`、core `tests/test_subprocess_engine.py`）。

**用它的场景**：改了 worker 的中断路径 / 会话清理 / grace / 抢传 / 上传超时 / **job 入口·事件出口（I/O 边缘）**后，想真跑确认「承重假设没塌」。日常改逻辑先跑单测；只有涉及上面这些"只能真跑验证"的真实边界才动 harness。

## 前置条件

- **AWS 凭证 + region us-east-1**（default profile 即可）。
- **一个可写 S3 桶**，经环境变量 `HARNESS_S3_BUCKET` 传入（**勿硬编码**账号相关值）。跑完自行清理桶内 `harness/<run-id>/` 前缀（见下「清理」）。
- 用 **`core/.venv/bin/python`** 跑（harness 复用真实 `core.scope.plan` 生成 job，防手搓 JSON 漂移）。**cwd 与 `PYTHONPATH` 都不限**——harness 由 `__file__` 派生仓库根、自己把 `<repo>/core` 插进 `sys.path`，features/engines 路径也全由该根算出。
- 各引擎的 venv/node_modules 已就绪（harness 用 `engines/novaact/.venv/bin/python` / `node --import tsx` spawn worker）。

## 调用

```bash
# 下面用相对路径写，故从仓库根键入最省事（cwd 非必需，见「前置条件」）：
HARNESS_S3_BUCKET=<你的可写桶> core/.venv/bin/python tools/e2e_harness.py \
    --engine <novaact|midscene> \
    --feature <feature 名，不含 .feature 后缀> \
    --interrupt <none|connect|act|between|scenario|scope_end> \
    --run-id <本次唯一 id，作 S3 prefix + 本地临时目录名> \
    --grace-cap <秒，SIGKILL 兜底墙钟，默认 30>
```

参数：

| 参数          | 默认                   | 说明                                                                                 |
|---------------|------------------------|--------------------------------------------------------------------------------------|
| `--engine`    | `novaact`              | `novaact` / `midscene`                                                               |
| `--feature`   | `wikipedia_assertions` | `features/<名>.feature`，**不含后缀**                                                 |
| `--votes`     | `1`                    | AI 断言投票次数（ADR 0014）                                                            |
| `--interrupt` | `none`                 | 中断时机，见下表                                                                      |
| `--run-id`    | **必填**               | 本次唯一 id → S3 `harness/<run-id>/` + 本地 `$CLAUDE_JOB_DIR/harness-runs/<run-id>/` |
| `--grace-cap` | `30.0`                 | SIGTERM 后等这么久 worker 还没退 → 判 `hung=true` + SIGKILL 兜底                     |

### `--interrupt` 中断时机

| 值          | SIGTERM 落点                                        | 验什么                                                                                                                                                             |
|-------------|-----------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `none`      | 不中断（baseline）                                    | 正常完成路径：所有产物应进 S3、`n_lost=0`、删本地                                                                                                                     |
| `connect`   | 建连中（scope_started 前，2s 定时）                    | 会话建立中被杀：不泄漏、干净退                                                                                                                                       |
| `act`       | 第一个 act 跑一半（step_started 后 3s）               | act 中途中断：会话释放 + in-flight 产物处置                                                                                                                         |
| `between`   | 第一个 step_done 后                                 | step 边界中断：已完成 act 产物已抢传                                                                                                                                |
| `scenario`  | **第一个 scenario_done 后 3s、下一 scenario 运行中** | **scenario 边界抢传（Midscene log）**：已完成 scenario 的 log 应已进 S3。**需多 scenario 归一个 scope 的 feature**（见下「多 scenario 陷阱」），否则该时机不触发、成无效样本 |
| `scope_end` | 所有 scenario 完成、scope 末 flush 前                | flush 前中断：暴露"只 scope 末才传的剩余产物"残余（Nova summary / Midscene log）                                                                                      |

## 怎么判读报告

harness 结尾打印 `=== HARNESS_REPORT_JSON ===` + 一段 JSON。关键字段：

| 字段                         | 含义 / 怎么判                                                                                                        |
|------------------------------|----------------------------------------------------------------------------------------------------------------------|
| `hung`                       | **`true` = 失败**：worker SIGTERM 后 grace-cap 内没退、被 SIGKILL。中断正确性的头号红线                                 |
| `exit_code`                  | 正常/协作停止应 `0`；网络耗尽 `80`（`EX_WORKER_NETWORK`）；会话释放失败 `1`                                              |
| `grace_s`                    | SIGTERM→worker 退出实测秒数（`none` 时为 null）。应 « grace-cap                                                         |
| `sample_valid`               | **判读前先看这个**。`false` = 无效样本（中断太早、盘和 S3 都空，`n_lost=0` 是"没东西可丢"而非"抢传救回"）→ 换更晚时机重跑 |
| `sample_note`                | 人话解释 sample_valid + 丢失量                                                                                       |
| `lost_on_fargate` / `n_lost` | **盘上有、S3 无**的文件 = Fargate 容器盘销毁时会真丢的。subprocess 下这些留本地盘、**非真丢**                           |
| `bytes_lost`                 | 同上字节数                                                                                                           |
| `disk_files` / `s3_files`    | 中断后盘上 / S3 上各有什么（含 size）                                                                                  |
| `scope_done_emitted`         | 中断路径应 `false`（不 emit scope_done、不走 flush）；正常完成 `true`                                                    |

### 判读要点（易误判，务必照做）

- **先看 `sample_valid`，再看 `n_lost`**。`n_lost=0` 在 `sample_valid=false` 时毫无意义——历史踩过：Midscene `act` 时机中断太早、盘空、`n_lost=0` 被误读成"抢传生效"，实为无效样本。
- **`n_lost=0` 不等于"零残余"**。harness 的 lost 判据是**文件名**"盘有 S3 无"。若某文件名已在 S3（被早先抢传过）、但盘上是更大的版本（后续又 append 了），`n_lost` 记 0，但存在**字节级增量残余**。要验抢传"救了多少"，需**逐文件对比 disk vs S3 的 size**（scenario 抢传验证就是这么坐实的：scenario1 的 log 进了 S3，scenario2 的增量 disk>S3）。
- **验"抢传因果"要交叉核对时序**：`scope_done_emitted=false` + worker stderr 有 `signal received`/`session shutdown` 但**无 flush 日志** = 确实走了中断退出、没走 scope 末 flush。这样才能证明 S3 里的产物只可能来自**边界抢传**、而非退出路径顺带传的。

## 真跑陷阱（历史踩过，务必避开）

1. **plan 按 `@scope:` tag 分组，不是"一 feature 一 scope"**（ADR 0025）。未标 `@scope:` 的 scenario **各自独立成单 scenario scope**。harness 取**匹配 `--engine` 的第一个 job**（单引擎 feature 下即 `jobs[0]`；混引擎 feature 如 engine_routing 靠 `@engine:` tag 分引擎时，取本次 `--engine` 那个引擎的 job）作靶子。
   - **验 `scenario` 时机必须用多 scenario 归一个 scope 的 feature**，否则 `jobs[0]` 只有 1 个 scenario、`scenario` 时机的 `n_scen>1` 条件不满足、SIGTERM 不发出、跑成完整 baseline。
   - **现成可用**：`features/concurrency_and_scope.feature` 的 `@scope:browse`（2 个 scenario 共享会话，`jobs[0]`）。跑前可用 `core.scope.plan` 确认 `jobs[0]` 的 scenario 数：
     ```bash
     PYTHONPATH=core core/.venv/bin/python -c "from core.scope import plan,PlanConfig,FeatureSource; from pathlib import Path; f='features/concurrency_and_scope.feature'; print([len(j.scenarios) for j in plan([FeatureSource(uri=f,text=Path(f).read_text())],PlanConfig(default_engine='midscene',default_assertion_votes=1))])"
     ```
2. **wikipedia SSL 环境坑（Nova 尤甚）**：某些网络下到 `www.wikipedia.org` 的 SSL 握手会挂（`SSLEOFError`，Nova SDK 本地 strict cert verify）。**Midscene 走 AgentCore 云浏览器、不受本地 SSL 影响**；Nova SDK 在本地建 CDP 时可能撞。若 Nova 全场景 SSL 失败，先直连测握手确认是环境问题，可临时用简单站点 feature 绕。
3. **scenario 抢传只 Midscene 有**（Nova 侧 `session_summary.json` 在 scenario 边界不存在、无赔付对象——ADR 0029）。别期待 Nova 的 `scenario` 时机验出 log 抢传。
4. **烧真 AWS 钱**：AgentCore 会话 + 模型调用 + S3。质量优先但别乱烧——每个时机跑一次即可，别无脑刷矩阵。用短 feature 控成本。

## 清理（跑完必做）

harness 不自动清桶。每个 run 在 `harness/<run-id>/` 前缀下留对象，跑完清理：

```bash
AWS_REGION=us-east-1 core/.venv/bin/python -c "
import boto3
s3=boto3.client('s3',region_name='us-east-1')
b='<你的桶>'; p='harness/<run-id>/'
objs=s3.list_objects_v2(Bucket=b,Prefix=p).get('Contents',[])
if objs: s3.delete_objects(Bucket=b, Delete={'Objects':[{'Key':o['Key']} for o in objs]})
print('deleted', len(objs))
"
```

本地临时产物落 `$CLAUDE_JOB_DIR/harness-runs/<run-id>/`（或 `/tmp/harness-runs/`），随 job 目录清理，一般不用手动删。
