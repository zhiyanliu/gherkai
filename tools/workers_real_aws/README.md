# workers_real_aws：worker 镜像交付测试的真实账户装置

本目录的装置把 `deploy_aws/tests/test_workers.py` 的全部用例原样对一个真实 AWS 账户的 ECS、SSM、ECR、DynamoDB 执行，另带三条只在真实账户上执行的补充用例。用它核对的是清理与推送协议在真实服务上的行为：moto 不校验或与真实服务行为不同的地方（注册校验、删除之后的描述、`registeredAt`、读后可见性、限流）在单测里看不到。设计背景与已核到的结论见 [ADR 0038](../../docs/adr/0038-worker-image-delivery.md)「实测项」节 9、10。

| 文件 | 作用 |
|------|------|
| `harness.py` | 装置本体：载入原测试模块、替换夹具、注册适配、惰性建表、收尾与补充用例；`--sweep` 入口按令牌清扫残留。文件头写明机制与全部环境变量 |
| `conftest.py` | 配置校验（不合法时在收集之前以用法错误结束）、结果文件（每个用例各阶段的结果与观察，逐行写进 jsonl）、装置记下的问题（终端摘要单独列出、决定退出码，见下文「读结果」）与预期失败的判定入口（见下文「预期失败」） |
| `summarize.py` | 汇总结果文件 |

`harness.py` 不以 `test_` 开头，仓库的 pytest 配置（`testpaths` 不含 `tools/`）不会顺带收集它；在命令行上显式给出它的路径时 pytest 照常收集。

## 证据边界

装置对用例本身不做任何改动：断言、钩子壳（`HookedSsm` / `HookedEcs` / `HookedDdb`）、注入的时钟与容器引擎替身都原样沿用；`seed_backend` 换成一个只在执行期间做标记的包装（参数、返回值与异常原样，用来判别种子模板，见下文适配第 1 项）。唯一的例外是真实账户模式下把一条用例的一种特定错误判为预期失败（见下文「预期失败」）。由此带来的边界：

- **时钟是注入的**。用例的时钟以 2026-09-08 起算，最晚的一条到其后 30 天。真实 ECS 返回的 `registeredAt` 是真实的注册时刻，晚于注入的时钟，所以未经 `HookedEcs(registered_at=…)` 覆盖的 revision 永远不满足「注册时刻早于读映射时刻」，补打 `gherkai:retired-at` 在真实账户上只来自钩子覆盖。真实时钟下的补打与静默期不在本装置的覆盖范围内，要用真实命令在部署出的后端上核对。
- **交错由用例在同一进程里摆出**。钩子壳把另一方的写入插在被测代码两次调用之间；多方组合用例让推送与清理各在一个线程里，用事件把各方停在指定位置，任一时刻至多一方在发出调用。这验证的是被测代码在这些次序下的判定，不是真实并发的多个进程，也构造不出「写入已成功、但对另一方尚不可见」这类依赖服务端可见性延迟的交错；这类窗口只能由补充用例 c 的观察数字估计。
- **容器引擎是替身**：不真推镜像，注册出的 revision 引用的 digest 在仓库里不存在（注册不校验这一点），也不用 RunTask 拉起它。

装置对真实账户只做三处适配，都不改变被测代码发出的请求：

1. **给种子模板补执行角色**。种子模板是用例自己注册的，不是 CDK 合成的模板；真实 ECS 在注册时就拒绝「Fargate、镜像为 ECR 地址、不带执行角色」的任务定义（`ClientException`，moto 不查）。装置只在种子模板的注册请求缺 `executionRoleArn` 时补上使用者给出的角色。原用例不断言这个字段。
2. **调高种子模板不合法的 memory**。`seed_backend(aws, cpu="2048")` 的那几条重派生用例摆的是 cpu 2048 配 memory 2048，不是合法的 Fargate 组合，真实 ECS 拒绝注册；装置把 memory 调到该 cpu 的下限 4096。用例只断言 cpu，不断言 memory。
3. **DynamoDB 写后等待**。每次 DynamoDB 写操作返回之前等 `GKP_SETTLE` 秒（缺省 2，须为有限的非负数；moto 模式下恒为 0，取值照样校验）。状态分组索引只有最终一致读，写入之后立即读快照的用例在真实账户上会因索引尚未跟上而失败，这与被测协议无关（协议本身已按最终一致设计）；等待让这些用例检验的仍是协议判定。装置不借此检验 GSI 的一致性。

前两项只作用于种子模板：装置把 `seed_backend` 换成一个包装，它执行期间在调用它的线程里置一个线程局部的标记，注册请求到来时标记在场才算种子模板。这个判别不会误判：用例里的模板注册只出现在 `seed_backend` 里（用例另行注册的 revision 都经被测代码的复制函数），`seed_backend` 自己不调用被测代码，参与方线程看不到主线程的标记。被测代码的复制请求一律原样转发；装置另核对它们：复制的模板是本用例的种子模板时，装置给那个模板补过或调过的字段必须原样出现在复制请求里，否则记一行 `copy_request_mismatch`，该用例在收尾之后以收尾错误失败。装置因此不会替被测代码补回它漏带的模板字段。

前两项每发生一次在结果文件里记一行 `adaptation`，`GKP_ADAPT=0` 关闭这两项（用来确认真实 ECS 是否仍要求它们）。

此外两处是为让用例在真实账户上互不干扰：每条用例一个独立的资源名前缀 `gkp<令牌><三位序号>-`（family 名、SSM 路径、ECR 仓库名、runs 表名都由它拼出），绝不使用缺省前缀 `gherkai-`，免得碰到账户里同名的真实部署；runs 表惰性建立，只在用例第一次真正读写表时才建，多数不读写表的用例不必为建表等待。收尾总是尝试删除按本用例前缀拼出的 runs 表，不看客户端是否收到过建表的应答（建表请求被服务端接受、客户端随后超时或连接中断时，表已在建）：没有建表的用例因此多一次返回 `ResourceNotFoundException` 的 `DeleteTable`，不算失败。

## 前置

- 从仓库根执行，用仓库的 workspace venv（`uv sync` 之后的 `.venv`；`uv run` 与直接用 `.venv/bin/python` 等价）。
- 凭证：真实账户模式不设假凭证、不删 `AWS_PROFILE`，按 boto3 的常规解析链取凭证。region 由 `GKP_REGION` 给出，未设时取 `AWS_REGION` / `AWS_DEFAULT_REGION`，都没有时装置报错。
- 执行角色：真实账户模式必须显式给出 `GKP_EXEC_ROLE`，取一个已有的 ECS 任务执行角色的 ARN（例如已部署后端的执行角色，可用 `aws ecs describe-task-definition --task-definition <前缀>novaact-worker --query taskDefinition.executionRoleArn --output text` 取得），或取 `none` 表示不补角色（种子模板的注册预期被拒绝，几乎全部用例失败，只用于确认真实 ECS 的这项校验）。缺了它装置在收集之前以用法错误结束（退出码 4），不发出任何 AWS 请求；`GKP_SETTLE` 不是有限的非负数、`GKP_OBS_N` 不是正整数时同样如此（任何模式下都校验）。
- **装置在任何模式下都不调用 IAM**：不建、不删、不改任何角色。moto 模式下 `GKP_EXEC_ROLE` 缺省为 `auto`，用一个合成的 ARN 字符串（moto 不校验角色是否存在）。
- 所需权限，按装置与用例实际发出的 API 操作列出；它不是逐条核定过的最小 IAM 策略，个别操作在 IAM 里可能另需别的动作，遇到拒绝访问时按报错补授：
  - ECS：`RegisterTaskDefinition`、`DescribeTaskDefinition`、`ListTaskDefinitions`、`ListTaskDefinitionFamilies`（清扫用）、`TagResource`、`UntagResource`、`DeregisterTaskDefinition`、`DeleteTaskDefinitions`
  - SSM：`PutParameter`、`GetParameter`、`GetParametersByPath`、`DeleteParameter`、`DeleteParameters`、`DescribeParameters`（清扫用）
  - ECR：`CreateRepository`、`DeleteRepository`、`DescribeRepositories`（用例开始前的残留检查与清扫用）、`DescribeImages`、`PutImage`、`GetAuthorizationToken`
  - DynamoDB：`CreateTable`、`UpdateTable`、`DeleteTable`、`DescribeTable`、`ListTables`、`PutItem`、`UpdateItem`、`GetItem`、`Query`、`BatchWriteItem`
  - STS：`GetCallerIdentity`；IAM：对 `GKP_EXEC_ROLE` 所给角色的 `iam:PassRole`
- 令牌 `GKP_TOKEN`：1 到 12 位小写字母数字、必须以字母结尾（前缀里令牌与序号之间没有分隔符，以字母结尾才不会让一个令牌的清扫范围包含另一个令牌的资源）。同一个 shell 里连续执行的一组命令共用导出的那个令牌，换一轮执行换一个新令牌；不给时随机生成，记在结果文件的 `session_start` 一行。共用令牌的各条命令前缀序号都从 001 起、会用到相同的前缀：每条用例收尾时对自己的全部资源发起删除，下一条命令的用例开始前另查一次同前缀残留（两个 family 的 ACTIVE 与 INACTIVE revision、SSM 参数、两个 ECR 仓库、runs 表），有就先清掉并记 `residue`、让会话以非零退出码结束。收尾发起删除之后不等删完：已删除的 revision 处于 `DELETE_IN_PROGRESS`，不出现在 ACTIVE 与 INACTIVE 的列举里，残留检查看不到它们；runs 表在删完之前 `DescribeTable` 仍返回它（状态为 `DELETING`），两条命令间隔很短时下一条命令会看到同一前缀的表仍在删除中。这是正在完成的清理，不算残留：残留检查等它从 `DescribeTable` 里消失（每 2 秒查一次、至多 120 次，约 4 分钟），记一行 `waited_for_table_deletion`，不记 `residue`、不影响退出码；同时有其它残留时 `residue` 照记，其中表的那一项为 false。等了约 4 分钟仍没有删完时残留检查失败，记一条收尾失败（`teardown_failure`，step 为 `residue check`），会话以非零退出码结束。所以上一条命令正常收尾时，下一条命令不会出现 `residue`；出现 `residue` 说明此前有命令留下了资源。令牌还要取一个不会与账户里已有资源撞名的值：清扫按名字认资源（见下文「清扫残留」）。

## 执行命令

仓库 `pyproject.toml` 的 `addopts` 带 `-m 'not integration' --timeout=60`，装置在仓库内执行时会带上它们。装置的用例都不带 `integration` 标记，marker 过滤不会筛掉任何一条（收集结果为原文件的全部用例加 3 条补充用例）。`--timeout=60` 对 moto 模式够用；真实账户模式下建表与限流重试会超过 60 秒，命令里要显式给 `--timeout=1200`（命令行上后给的值覆盖 `addopts` 里的）作为挂死安全网。三条补充用例自带 `@pytest.mark.timeout`，以用例自带的值为准、不受命令行影响：a 为 4200 秒，b 为 600 秒，c 为 3000 秒。超时覆盖一条用例的全部阶段（含收尾），后果随 pytest-timeout 的方式而不同：signal 方式（macOS 与 Linux 的缺省）下超时以异常打断正在执行的那一步，落在收尾里时余下的清理不再执行、资源可能留在账户里，装置记一条「清理被中断」的问题；thread 方式下进程被直接终止，既不保证收尾，也不保证结果文件完整（最后一行可能只写了一半），装置来不及记下问题，pytest 也来不及为这条用例生成报告（`summarize.py` 从结果文件推出「收尾没有完成」「会话没有正常结束」与「结果文件最后一行没有完整写入」，见下文「读结果」）。出现过超时的执行，结束之后都应按「清扫残留」清扫一次。

**moto 自检**（不连 AWS；改了装置或测试文件之后先执行这两条）：

```bash
uv run pytest -q -p no:cacheprovider tools/workers_real_aws/harness.py
# 末行形如 N passed, 3 skipped：N 为原文件的用例数，补充用例在纯 moto 模式下跳过

GKP_FORCE_REAL_PATHS=1 uv run pytest -q -p no:cacheprovider tools/workers_real_aws/harness.py
# 末行形如 N+2 passed, 1 xfailed
```

第二条在 moto 上走真实账户模式的代码路径：惰性建表、注册适配、复制请求的核对、预期失败的判定、收尾清扫与三条补充用例都执行一遍（写后等待为 0 秒）。那一个 xfail 是补充用例 a：moto 上索引一建即 `ACTIVE`，构造不出「索引仍在建立」的观察，用例按设计以 xfail 结束。两条都另由 `cli/tests/test_workers_real_aws.py` 守着：第一条（取一个非缺省 region）断言装置收集到的用例与直接执行测试文件的相同、全部通过；第二条取其中几条代表用例、`_Party` 自身的自测（不用 aws 夹具）与三条补充用例，断言收尾无失败、适配与惰性建表确实发生，不用 aws 夹具的用例不触发建表、适配与收尾。同一文件另在测试文件的临时副本里注入用例（复制请求那一条另在被测代码的副本里变异），核对下列情形都不会被装置吞掉，并如实出现在结果文件、终端摘要与 `summarize.py` 的输出里（见下文「读结果」）：断言失败与执行异常（含完整保存的长 traceback）、收尾失败、收尾被 signal 方式的超时打断、收尾被 thread 方式的超时连同进程一起终止（由 `summarize.py` 推出）、参与方线程残留（一直等待的一方，与在清理期间恢复执行、写入并结束的一方）、预期失败判定的边界（只有这条用例 call 阶段、`PutImage`、`InvalidParameterException` 的 `ClientError` 算预期失败：文字相同的其它异常、以它为起因的 `AssertionError`、setup 与 teardown 阶段的同一个错误、别的用例抛出的同一个错误都照常失败；给了 `--runxfail` 时不作判定）、被测代码的复制请求漏带模板的执行角色、只有 ECR 仓库或只有 INACTIVE revision 的同前缀残留、建表请求已被服务端接受而客户端收到连接错误（收尾仍删掉这张表）、用例建了名字不以本用例前缀开头的表（收尾不删它、记一条收尾失败）。注入与变异只存在于那份副本里，装置本身没有故障注入开关。另有几条只核对配置校验：真实账户模式缺执行角色、执行角色不合法或缺 region，与 `GKP_SETTLE`、`GKP_OBS_N` 取值不合法时，都在收集之前以用法错误结束。moto 上删表即刻生效、构造不出删除中的表，残留检查对它的处置另用替身 client 直接核对：表先处于 `DELETING`、随后消失时不算残留，只记 `waited_for_table_deletion`；同时有其它残留时 `residue` 照记、表的那一项为 false；表为 `ACTIVE`、`CREATING`、`UPDATING`、`ARCHIVING` 等其它状态时算残留；`DELETING` 一直不消失时，等满时限（每 2 秒查一次、至多 120 次）之后残留检查失败、记为收尾失败；`DescribeTable` 报「表不存在」以外的错误时（第一次读取或等待期间），残留检查同样失败、错误码如实记下。`summarize.py` 的推断另由同一文件里直接构造的结果文件核对：多次会话写进同一个文件时按会话各自判断、只有一次会话时输出不变、最后一行没有完整写入时照常汇总、被终止的会话留下的半行后面接着下一次会话的 `session_start` 时照常读入后者、缺换行而连在一起的完整对象都保留、没有写完的部分不是一个 JSON 对象的开头时报错；判断「是不是一个 JSON 对象没有写完的开头」的逻辑另对若干条合法记录的每一个截断位置与随机改坏的开头逐一核对。装置追加之前给末字节不是换行的结果文件补换行，也在那里核对。

**真实账户**（先在当前 shell 里导出五个变量，之后的命令都沿用）：

```bash
export GKP_MODE=real GKP_EXEC_ROLE=<执行角色 ARN> GKP_REGION=<region> GKP_TOKEN=<令牌> GKP_RESULTS=<结果文件路径>

# 冒烟（约 2 分钟）：先确认凭证、适配与收尾都正常，再清扫一次确认没有残留
uv run pytest -q -p no:cacheprovider --timeout=1200 tools/workers_real_aws/harness.py -k 'test_push_worker_happy_path or test_cleanup_deletes_after_quiet_period_when_unreferenced or test_cleanup_keeps_when_a_live_run_references_it or test_readiness_check_with_an_active_index_proceeds_to_one_snapshot or test_snapshot_sees_what_the_real_run_store_writes or test_realaws_cleanup_skips_when_the_runs_table_is_missing'

# 清理与推送的交错（实测项 9、10 涉及的分段用例）
uv run pytest -q -p no:cacheprovider --timeout=1200 tools/workers_real_aws/harness.py -k 'reread or final_check or skip_branch or readiness or snapshot or backfill or retired_at or reclaimed or deleted'

# 全量（含三条补充用例）；不含补充用例 a 时加 -k 'not index_is_creating'
uv run pytest -q -p no:cacheprovider --timeout=1200 tools/workers_real_aws/harness.py

# 补充用例单独执行
uv run pytest -q -p no:cacheprovider --timeout=1200 tools/workers_real_aws/harness.py -k index_is_creating        # a
uv run pytest -q -p no:cacheprovider --timeout=1200 tools/workers_real_aws/harness.py -k runs_table_is_missing    # b
uv run pytest -q -p no:cacheprovider --timeout=1200 tools/workers_real_aws/harness.py -k visibility_and_ordering  # c
```

导出的变量在这个 shell 里一直生效：之后要回到 moto 自检，先 `unset GKP_MODE GKP_EXEC_ROLE GKP_REGION GKP_TOKEN GKP_RESULTS`。

冒烟之后看终端摘要与结果文件：终端摘要里不应出现「装置记下的问题」一节；结果文件里 `adaptation` 行应出现（`executionRoleArn`），`teardown` 行的 `failures` 应为 0，`lazy_table_built` 记建表秒数。想确认真实 ECS 是否仍要求两项注册适配，同一冒烟加 `GKP_ADAPT=0` 只执行 `test_push_worker_happy_path` 一次。

三条补充用例：

- **a**（`test_realaws_cleanup_skips_while_the_status_group_index_is_creating`）：给一张已有 300 个 STATE item、尚无状态分组索引的表发起建索引，在索引仍为 `CREATING` 时执行一趟清理，断言它跳过且不注销；等索引 `ACTIVE` 之后再执行一趟，断言它回收候选。两次读到的索引状态不都是 `CREATING` 时观察作废、以 xfail 结束（`index_creating_observation` 一行 `valid` 为 false，第一阶段的断言没有执行）。
- **b**（`test_realaws_cleanup_skips_when_the_runs_table_is_missing`）：runs 表不存在时清理跳过、不注销。
- **c**（`test_realaws_visibility_and_ordering_observations`）：只记数字、不断言。① `PutParameter` 成功之后另一个独立 client 的 `GetParametersByPath` 是否立刻读到；② `TagResource` 成功之后另一个独立 client 的 `DescribeTaskDefinition`（`include=["TAGS"]`）是否立刻读到；③ 同一连接 `TagResource` 紧接 `UntagResource` 之后，立刻读与隔 2 秒再读时 tag 是否都已不在，全部轮次之后再隔 10 秒读一次终态（次序倒置时 tag 会重新出现）；④ 本用例注册过的 revision 的描述是否都带 `registeredAt`。前三项每项重复 `GKP_OBS_N` 次（缺省 40，须为正整数）；第四项按本用例注册过的 revision 逐个描述一次。

## 耗时与费用

- moto 自检约十秒。
- 真实账户：冒烟约 2 分钟；全量约四十分钟，其中近 40 条用例会真实建表（每张十几秒），SSM `PutParameter` 与 ECS `RegisterTaskDefinition` 的默认配额较低、限流重试占去不少时间；补充用例 a 单条约二十分钟（主要在等索引 `ACTIVE`，曾实测约 17 分钟），代码里没有更紧的总上界：等索引 `ACTIVE` 至多 20 分钟、收尾删表遇到索引仍在建立时的重试至多约 25 分钟，两者可以累计，最终以用例自带的 4200 秒超时为界；c 约 3 到 5 分钟。
- 费用：用到的资源都按用量计费，没有常驻资源。ECS 任务定义与 SSM 标准参数不收费，ECR 仓库里没有镜像层，DynamoDB 表为按需计费、按请求计费。每条用例收尾时删掉自己的全部资源，执行结束后按下文「清扫残留」核对一次。

## 读结果

结果文件是 jsonl，每行一个对象，必有 `kind` 与 `ts`。路径取 `GKP_RESULTS`，未设时取系统临时目录下 `workers-real-aws-<UTC 时刻>-<进程号>.jsonl`；会话结束时终端摘要末尾打印「结果文件：…」。多次执行写同一个路径时逐行追加（上文「真实账户」导出 `GKP_RESULTS` 之后的各条命令即如此），`summarize.py` 按会话分开汇总这样的文件；要单独看某一次执行时给它一个新路径。

```bash
uv run python tools/workers_real_aws/summarize.py <结果文件> [--lines N]
```

`summarize.py` 先给（阶段, 结果）的计数，紧接着是「需要处理」一节（装置记下的问题，逐条列出；另有装置来不及记下、由脚本从结果文件推出的三种：「会话没有正常结束」即某次会话的 `session_start` 之后没有它的 `session_finish`，「收尾没有完成」即真实账户模式的代码路径下用例有 `prefix` 一行、却没有同一用例同一前缀的 `teardown` 或 `teardown_interrupted` 一行，「结果文件最后一行没有完整写入」即最后一行末尾的一个对象只写了一半、脚本略去它并用之前的完整记录汇总（同一路径之后又有会话追加时，下一次会话的 `session_start` 紧接在这半行之后：装置追加之前先给末字节不是换行的文件补一个换行，`session_start` 因此在下一行开头，较早写出的结果文件里它与这半行同在一行；两种都列为「结果文件中途有一行没有完整写入」，脚本略去没有写完的部分、照常读入 `session_start`），三者都说明进程曾被直接终止、账户里可能留有资源）与各次会话的退出码，再逐条列出失败用例与失败信息末尾 N 行（更早的行只注明略去了几行；结果文件里保存的是完整的失败信息）、预期失败与跳过的原因、各观察行，最后给适配次数、建表次数与秒数范围、收尾次数与其中有失败的、被跳过的次数。`setup` 或 `teardown` 阶段出现 failed 说明夹具或收尾出了问题。结果文件里有多次会话时，记录按 `session_start` 分段，每次会话各自判断模式与收尾是否完成（纯 moto 会话不记 `teardown` 行，不会因另一次真实账户会话而被误报；后来的会话完成了同名用例，也不会遮掉较早会话没有完成的收尾），「需要处理」的各条与会话退出码都注明是第几个会话，「会话没有正常结束」另给出那次会话的令牌，供清扫使用；只有一次会话时不标会话序号。一行里缺换行而连在一起的几个完整对象都照常读入。没有写完的部分只在它确实是一个 JSON 对象的开头（逐字符判断再追加字符能否成为合法的 JSON）、且其后是文件末尾或紧接着下一次会话的 `session_start` 时才按上面两种处理；其它不是完整 JSON 对象的内容，脚本一律报错并指出行号，退出码为 1。

**装置记下的问题**与用例的通过与否无关，有五类：收尾里失败的一步（`teardown_failure`）、收尾被打断（`teardown_interrupted`，「清理被中断」：例如 signal 方式的超时落在收尾里，余下的清理没有执行）、用例开始前发现并清掉的同前缀残留（`residue`）、用例结束之后仍存活的参与方线程（`lingering_party_threads`）、被测代码的复制请求没有原样带着装置补进种子模板的字段（`copy_request_mismatch`）。前三类说明账户里可能留有资源或令牌被复用，第四类说明有一方在用例之外仍可能对账户发出调用，第五类说明被测代码复制模板时漏带了字段（该用例同时以收尾错误失败）。出现任何一类时：

- 终端摘要里单独列出「装置记下的问题」一节，真实账户模式下附上本次令牌的清扫命令；会话执行到最后时，末行的计数里另多出一项「装置问题」（会话被终止时没有这一项，以 `Exit:` 一行为准）。
- 用例全部通过时会话的退出码也为 1，不让「全部通过」掩盖它们；`session_finish` 一行的 `problems` 记各类的条数。
- 参与方线程残留时，装置在该条用例对账户的清理**之前**就查到并记下它，**跳过**这条用例的清理（`teardown` 一行带 `skipped`），会话随即终止（退出码 2，终端以 `Exit:` 一行说明原因），后续用例不再执行：残留的线程之后仍可能发出调用，可能在清理期间恢复执行、重新写入资源，清理与它竞争没有意义，也不能带着它执行下一条。这条用例的资源因此留在账户里；线程随进程退出一并结束，进程退出之后清扫。

失败的用例本身（断言失败、执行异常）照常由 pytest 记为 failed、会话退出码为 1；凡是 pytest 成功生成了报告的失败，结果文件里都带完整的失败信息。装置不改动这一点，唯一的例外是下文「预期失败」那一种。超时不一定有这样的报告：signal 方式下它作为异常打断正在执行的那一步，pytest 成功生成了报告时照常记为 failed（超时落在 pytest 生成报告的阶段时也可能没有失败报告，例如只有 setup 阶段的一行、会话退出码为 3），thread 方式下进程被直接终止，没有报告，也没有 `session_finish` 一行，见上文「执行命令」节关于超时的一段。

`kind` 的取值：

| kind | 内容 |
|------|------|
| `session_start` / `session_finish` | 会话开始（`GKP_*` 环境变量、rootdir、ini 文件）与结束（最终的退出码、各类装置问题的条数） |
| `harness` | 模式、令牌、region、等待秒数、适配开关、执行角色取值、原模块的用例函数数与载入方式（应为 `AssertionRewritingHook`，失败信息与直接执行原文件相同） |
| `session_account` | 真实账户模式下的账号与生效的执行角色 |
| `prefix` | 用例与其资源名前缀的对应 |
| `test` | 用例各阶段的结果；失败带完整的失败信息（`longrepr`），跳过带原因，预期失败带 `xfail_reason` 与实际抛出的异常（`xfail_detail`） |
| `adaptation` | 一次种子模板的注册适配：family、revision、改了哪几项 |
| `copy_request_mismatch` | 被测代码的一次复制请求没有原样带着装置补进种子模板的字段：family、模板、字段与两边的取值 |
| `lazy_table_built` | 一次惰性建表与其耗时 |
| `teardown` / `teardown_failure` / `teardown_interrupted` | 每条用例的收尾（失败数、建表请求正常返回的表 `table_built`、发出过建表请求却没有收到应答的表 `table_create_unconfirmed`、只记下参数没有建的表、写次数；因参与方线程残留而跳过时带 `skipped`、失败数为空）、收尾里失败的一步、收尾被打断时停在哪一步与打断它的异常 |
| `residue` | 用例开始前发现并清掉的同前缀残留：ACTIVE 与 INACTIVE revision、SSM 参数、ECR 仓库、runs 表是否存在（删除中的表不算） |
| `waited_for_table_deletion` | 用例开始前的残留检查看到同前缀的 runs 表仍在删除中、等它删完：前缀、表名、等待秒数。不是装置问题 |
| `lingering_party_threads` | 用例结束之后仍存活的参与方线程（用例、线程名、清理是否因此跳过）；记下之后会话终止 |
| `step` / `index_creating_observation` / `index_became_active` / `index_active_pass` | 补充用例 a 的步骤与两趟清理的观察 |
| `table_missing_observation` | 补充用例 b 的观察 |
| `obs_ssm_put_then_by_path` / `obs_ecs_tag_then_describe_other_client` / `obs_ecs_tag_untag_then_read` / `obs_describe_registeredAt` | 补充用例 c 的 ① 到 ④ |
| `register_response_registeredAt` | 整个会话里注册响应带与不带 `registeredAt` 的次数 |
| `describe_lineage_registeredAt` | 整个会话里清理与推送经 `DescribeTaskDefinition`（`include=["TAGS"]`）读到的带血缘 tags 的 revision，按 ARN 去重后带与不带 `registeredAt` 的个数；计的是 ECS 的原始结果，在用例的 `HookedEcs` 覆盖之前 |

## 清扫残留

```bash
uv run python tools/workers_real_aws/harness.py --sweep <令牌> --region <region>
```

会话结束时终端摘要列出了「装置记下的问题」（收尾失败、清理被中断、同前缀残留、参与方线程残留或复制请求与模板不符）、`summarize.py` 的「需要处理」不为「无」、或执行中出现过超时时必须执行一次；没有问题时也建议在执行结束后核对一次。列出并删除名字形如 `gkp<令牌><三位以上序号>-` 的 task definition family（先注销再删除全部 revision）、SSM 参数、ECR 仓库（强制删除）与 DynamoDB 表；不碰 IAM，也不碰不匹配这个模式的任何资源。清扫按名字认资源、不认创建者：同一令牌前缀下的任何资源都会被删除，不论是不是本装置建的，所以令牌要取一个不会与账户里已有资源撞名的值。每条用例的收尾只删按自己前缀精确拼出的 family 名、SSM 路径、ECR 仓库名与 runs 表名，不做前缀模糊匹配；用例经 `aws.ddb` 另建的表只在名字以本用例前缀开头时一并删除，否则不删、记一条收尾失败。清扫有失败时退出码为 1 并逐项列出。表仍在建立（例如还在建索引）时删表请求被拒绝（`ResourceInUseException`）；对刚被收尾发起删除、仍在删除中的表再次删除，官方文档写的是不返回错误，真实账户上观察到过同一个 `ResourceInUseException`。收尾、用例开始前的残留清理与清扫遇到这个错误都按同一重试处理（`harness.py` 的 `_delete_table`）：真实账户上每 15 秒重试一次、至多约 25 分钟（1500 秒），重试时表已不存在即按已删除处理；moto 上不重试。收尾与残留清理重试耗尽时记一条收尾失败、这张表留给清扫；清扫重试耗尽时这张表列为失败，退出码为 1。

## 与 moto 不同的地方

### 预期失败

- `test_repush_retires_the_replaced_revision_and_prints_digest_change`：用例用 `ecr.put_image` 往仓库放一份没有 layer 的手写 manifest（摆出「tag 原已存在」），真实 ECR 以 `InvalidParameterException` 拒绝，用例没有走到推送。它与清理和推送协议无关，无法在不改用例输入的前提下改成可执行；装置在真实账户模式下只把这一种失败判为预期失败：这条用例的 call 阶段、`PutImage` 操作、错误码 `InvalidParameterException` 的 `ClientError`。其它任何失败照常失败，包括 setup 阶段的错误（如凭证错误）、其它操作的 `ClientError`（如 `CreateRepository` 的 `AccessDeniedException`）与 `PutImage` 的其它错误码。setup 与 teardown 阶段抛出的同一个错误、文字相同的其它异常、以它为起因的 `AssertionError`、别的用例抛出的同一个错误也都照常失败。判定在 pytest 生成报告之后做（conftest 的 `pytest_runtest_makereport`），不用 xfail 标记；给了 pytest 的 `--runxfail` 时不作判定，这一种失败也照常报告，与 xfail 标记的用例相同；纯 moto 模式下不判定，`GKP_FORCE_REAL_PATHS=1` 时照样判定（moto 接受这份 manifest，这条用例在 moto 上照常通过），自检借此核对判定的边界。它要验的「同名 variant 换 digest 重推」由真实命令覆盖。

### 结果相同、分支不同

- **删除之后的描述**：真实 ECS 在 `DeleteTaskDefinitions` 之后的一段时间里描述仍成功、状态为 `DELETE_IN_PROGRESS`；moto 抛 `ClientException`。`test_new_revision_reclaimed_by_real_cleanup_passes_before_the_reread_is_registered_again` 里推送的再读在真实账户上走「描述成功、状态不是 ACTIVE」一支，moto 下走「`ClientException` 且列举里没有」一支，两支都重新注册，断言相同。用 `_Deleted` / `_UnlistedEcs` 摆删除的用例只注销、由钩子抛 `ClientException`，两边相同。原用例不在 moto 上删除之后再注册同一 family（moto 会重用编号），真实 ECS 不重用编号，不受影响。
- **`registeredAt`**：moto 的描述不带这个字段，真实 ECS 带真实时刻（见上「证据边界」）。`test_cleanup_does_not_backfill_when_registered_at_is_missing_or_not_before_reading[missing]` 在真实账户上实际走的是「不早于读映射时刻」一支（与 `[not_before_t1]` 同一支），两支的原因文字相同，用例照样通过；「取不到该字段」一支在真实账户上没有被覆盖。`list-workers` 的待清理条目在真实账户上带真实时刻、moto 下为空，相关用例只断言键集与前缀文字，不受影响。

### 依赖读后可见性的用例

下列用例在 moto 下读写立即可见；在真实账户上若对应的读落后于写，就会失败。这种失败本身就是要找的现象，不是装置的缺陷，先对照补充用例 c 的数字再判读。

- SSM 写映射紧接着另一轮 `GetParametersByPath`：各条 `test_reread_*` 与 `test_snapshot_query_failure_keeps_every_candidate_but_still_rereads_for_backfills`；`test_reread_keeps_a_mature_candidate_that_has_entered_a_mapping_and_removes_its_tag` 若失败在 `outcome.deleted == ()`，说明重读没看到刚写的映射、已被映射引用的成熟候选被注销，需要上报。凡是推送之后立刻清理或 `list-workers` 的用例同样依赖 SSM 的读后可见性。
- ECS 打 tag 或摘 tag 紧接着描述：`_retire_now(...)` 之后判定成熟的清理用例、`test_final_check_skips_a_candidate_that_changed_and_continues_with_the_others` 的 `rewritten` 与 `removed` 两例（钩子在最后核对的那次描述之前改 tag，描述读到旧值就会注销）、各条「摘掉 tag」的断言。
- ECS 注销紧接着描述其状态：`test_skip_branch_requires_the_mapped_revision_to_be_active`、`test_digest_change_does_not_tag_a_replaced_revision_that_is_no_longer_active`、`test_rederive_reregisters_when_the_mapped_revision_is_no_longer_active` 与上一条的 `inactive` 例。
- 注册之后立即出现在 ACTIVE 列举里：`_revisions(...)` 与 `set(ecs.registered) <= set(_revisions(...))` 一类断言。
- DynamoDB 状态分组索引（只有最终一致读）：`_put_state` 之后清理读快照的用例与几条快照用例。失败时先加大 `GKP_SETTLE`（如 5）再执行，仍失败再判读。

### 限流

SSM `PutParameter` 与 ECS `RegisterTaskDefinition` 的默认配额较低，装置的 client 用 adaptive 重试、至多 10 次。仍然耗尽时，被测的推送函数返回 2、输出里有 `AWS 调用失败：… Throttling…`，用例的断言因此失败，pytest 会话的退出码通常为 1；按环境问题处理，单独重新执行该条即可。
