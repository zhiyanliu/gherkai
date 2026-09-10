"""Nova Act 薄 worker（ADR 0022/0024）：读入一个 scope 的 job JSON → 跑这个 scope → 吐 ADR 0024 事件到事件通道。

不含 BDD runner 装饰器：会话/act/投票/派发逻辑直接在本进程跑（ADR 0022 薄 worker）。
core 经 adapter 起本 worker（子进程 / Fargate 任务，ADR 0026 机制层），讲 ADR 0024 协议。

I/O 契约两态（判据一律是「注入了哪个 env」、非「是否 Fargate」，ADR 0016 红线）：
- job 入：stdin 首行 JSON | `JOB_S3_URI` 指针 + GetObject（见 `lib/job_source.py`）。
- events 出：`EVENTS_FD` 指定的 fd（无则回落 stdout，便于手动直跑调试）| `EVENTS_DDB_TABLE` PutItem 到
  events 表（见 `lib/event_sink.py`）。
- 确定性 step 定制入：env `GHERKAI_STEPS_DIR`（使用方的 `steps/` 目录，组合根解析后注入；见
  `user_steps.py` / ADR 0037 决策 4）。

三通道分离（ADR 0024）：协议事件只走上面那条事件通道；引擎 SDK 的进度噪声留 stdout；worker 自身诊断/日志走 stderr。

一生（ADR 0024）：
  读 job → 开 AgentCore 会话 → 按 scope 串行跑 scenarios（每 step 派发）→ 逐事件吐事件通道
  → scope_done → 退出。SIGTERM/SIGINT（ADR 0024 flag-only）：handler 只置 _stop 标志、绝不 raise；
  主流程在 act 边界安全点检测 → 正常 return 退出三层 with 释放会话（with 正常退出即触发 __exit__，
  不靠异常穿透——避免异步 raise 撞 playwright greenlet 切换区致死循环卡死；sync-over-greenlet + signal-raise 反模式，见 ADR 0024 被拒方案）。
  单 act 套 timeout=ACT_TIMEOUT_S 使 in-flight act 有界返回，标志位总能在有限时间被检测。

派发（优先级顺序，ADR 0022/0020/0024）：
  ① 确定性注册表命中（不投票、可复现，ADR 0022）——表 = 本包内建脚手架 `deterministic_steps.py`
     + 使用方 `GHERKAI_STEPS_DIR` 目录下的注册（ADR 0037 决策 4）
  ② step.text 含 URL 字面量（引号内 https?://）→ 内建确定性导航 go_to_url（不浪费 AI）
  ③ AI catch-all：keyword=Then → act_get(BOOL) + N 次投票（AI 断言，带 votes）；
     keyword=When / Given 且非 URL → act（AI 动作/前置动作，无 votes）

cost（ADR 0024）：Nova SDK 原生给 time_worked_s，worker 只报该原生量；core 合计、美元折算交消费者（不内置费率）。

跑（一般由组合根 spawn `[sys.executable, "-m", "gherkai_worker_novaact"]`，也可手动）：
  echo '<job json>' | AWS_REGION=us-east-1 uv run python -m gherkai_worker_novaact

进程形态（ADR 0037 决策 3）：本模块的 `main()` 就是包入口 `__main__:main` 与 console script
`gherkai-worker-novaact` 背后的同一个函数——worker 必须是**被直接 spawn 的那个进程**（EVENTS_FD 经
`pass_fds` 继承，中间加包装层会吞 fd3，ADR 0024）。
"""
from __future__ import annotations

import inspect
import json
import os
import re
import signal
import sys
import threading

from nova_act import NovaAct, AgentCoreBrowserSessionProvider, BOOL_SCHEMA, Workflow
from nova_act.types.workflow import set_current_workflow, get_current_workflow

from gherkai_worker_novaact.lib.workflow_setup import ensure_workflow_definition
from gherkai_worker_novaact.lib.constants import MODEL_ID, WORKFLOW_DEF  # 共享常量（单一真理源，与 spike 共用）
from gherkai_worker_novaact.lib.event_sink import EventSink  # 事件出口（ADR 0024 I/O 边缘可注入接口；fd 态 / DDB 态两态）
from gherkai_worker_novaact.lib.job_source import JobSource  # job 入口（同上）
from gherkai_worker_novaact.lib.artifact_upload import ArtifactUploader  # 产物 S3 上传（ADR 0029；无落点 env 时 no-op 报 file://）

# 确定性 step 注册表（ADR 0022）+ 内建脚手架锚点（同在本包内）。
# 先 import 注册机制（提供 @deterministic 装饰器），再 import 脚手架——脚手架顶层的
# @deterministic 在 import 时执行，把锚点登记进 _deterministic._REGISTRY。
# 使用方自己的 step 目录在 main() 里加载（本 import 之后 = 内建先注册，ADR 0037 决策 4）。
from gherkai_worker_novaact import deterministic as _deterministic
from gherkai_worker_novaact import deterministic_steps  # noqa: F401  仅为触发注册（其顶层 @deterministic 副作用）
from gherkai_worker_novaact.user_steps import EX_STEPS_LOAD, UserStepsError, load_user_steps

# region 不再硬编码兜底（ADR 0016 决策 C）：None 时不再抢在 profile config 前跑错区。**正常路径由组合根落实**——
# compose.resolve_region 把 `--region > AWS_REGION > AWS_DEFAULT_REGION > profile config` 落实成具体字符串、经 AWS_REGION
# env 注入 worker，故这里通常拿到具体 region。真无 region（全 miss）→ None → fail-loud：boto client 抛 NoRegionError；
# 尤其 AgentCore 那条路径（下方 AgentCoreBrowserSessionProvider）的 validate_region **不吃 profile config、要显式字符串**，
# region=None 起会话直接失败（实测报 BrowserAuthError: 'You must specify a region.'——文案/异常类随 SDK 版本可变、
# 别按类名断言）——这正是组合根须在注入前把 profile-region 落实成字符串的原因（别静默跑错区）。
REGION = os.environ.get("AWS_REGION")

# 停止标志（ADR 0024 flag-only 中断模型）：SIGTERM/SIGINT handler 只 set 它、绝不 raise——避免异步异常
# 落进 playwright greenlet 切换关键区致死循环卡死（sync-over-greenlet + signal-raise 反模式，见 ADR 0024 被拒方案）。主流程在 act 边界安全点检测、
# 正常 return 退出三层 with 释放会话（with 正常退出即触发 __exit__，不靠异常穿透）。模块级单例（对称 _uploader）。
_stop = threading.Event()
_stop_signum: int | None = None  # 触发协作停的信号号（handler 只记录；日志由安全点补打，见 _on_signal）

# 单 act 时间上界（ADR 0024「act 有界返回」）：给每个 act/act_get 设 timeout，到点 SDK 在 step 边界安全点抛
# 可 catch 的 ActTimeoutError（非 greenlet 切换区）——使 in-flight act 有界返回、标志位总能在有限时间被检测。
# 值：真跑标定的折中（够长不误杀正常 act、且 grace ≥ act_timeout+释放耗时，见 ADR 0028 grace 上调）。
ACT_TIMEOUT_S = int(os.environ.get("NOVA_ACT_TIMEOUT_S", "120"))  # SDK 允许 [2,1800]；默认 120s

# 产物上传器（ADR 0029 第一期）：从组合根注入的 env（ARTIFACT_S3_BUCKET/PREFIX）造——cloud 时上传 S3+删本地+
# 报 s3://，local/未注入时 no-op 报 file://。**惰性单例**（非 import 期构造）：from_env 对「半注入」fail-loud
# （ADR 0033），若在 import 期炸则零事件、连诊断都发不出（且测试收集期即崩）——推迟到首次使用（step 事件流
# 的 try 内），装配矛盾以 error 事件可见。worker 单进程单 run，单例语义不变。
_uploader_singleton: ArtifactUploader | None = None


def _get_uploader() -> ArtifactUploader:
    global _uploader_singleton
    if _uploader_singleton is None:
        _uploader_singleton = ArtifactUploader.from_env()
    return _uploader_singleton


_URL_IN_QUOTES = re.compile(r'"(https?://[^"]+)"')


class _DeterministicCtx:
    """传给确定性 handler 的上下文：暴露 Playwright `page`（精确 DOM/URL 查，不走 AI）。

    Nova 把底层 Playwright Page 暴露在 `nova.page`（spike 已验证）。handler 拿它做
    `ctx.page.url` / `ctx.page.locator(...)` 这类确定性判定。
    """

    def __init__(self, nova) -> None:
        self._nova = nova

    @property
    def page(self):
        return self._nova.page

# 事件 sink（ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一事件出口，抽进 lib/event_sink.py
# （对称 _uploader、可注入、可测；subprocess 态写 EVENTS_FD fd、无则回落 stdout 调试）。emit 作参数注入
# _run_step/_run_scenario（两个引擎统一打桩机制），不再是模块级函数——三通道分离/保序/中文由 EventSink 保。
# log（stderr 诊断）**不属那三条 I/O 边、不进 sink**（协议传输面 vs 诊断面物理隔离，ADR 0024），保模块级。
def log(msg: str) -> None:
    sys.stderr.write(f"{msg}\n")
    sys.stderr.flush()


def _on_signal(signum, frame):
    """SIGTERM/SIGINT 的 flag-only handler（ADR 0024 终止契约）：只置停止标志、**绝不 raise**。

    绝不 raise——避免异步异常落进 playwright greenlet 切换关键区致死循环卡死（sync-over-greenlet + signal-raise 反模式，见 ADR 0024 被拒方案）。
    主流程在 act 边界安全点检测 `_stop`、正常 return 退出三层 with 释放会话（with 正常退出即触发 __exit__，
    不靠异常穿透）。SIGTERM/SIGINT 共用（Ctrl-C 亦协作停）。
    **handler 内不做任何 I/O（含 stderr 日志）**：信号可能落在主线程正在 `sys.stderr.write` 的瞬间，handler 里再写
    stderr 会撞 Python BufferedWriter 的非重入锁——`RuntimeError: reentrant call inside <_io.BufferedWriter name='<stderr>'>`
    从 handler 抛出、直接把主流程打崩（rc=1）；worker 常态大量写诊断，这不是理论风险（CI runner 上真跑抓到）。
    故这里只记信号号 + 置标志，「收到信号」的日志由主流程在安全点补打（见 main 末尾与读 job 早退处）。
    **模块级函数（非 main 内闭包）**：只引用模块级 `_stop`/`_stop_signum`，提到模块级使 `test_interrupt_process.py`
    的 fixture worker 能 import 并装**这同一个真 handler**——回退 raise 模型时进程级测试真变红。
    """
    global _stop_signum
    _stop_signum = signum
    _stop.set()


def _cost_from_result(r) -> dict | None:
    """报 Nova SDK 原生量 time_worked_s（ADR 0024：engine 只报原生量，core 不算美元）。"""
    md = getattr(r, "metadata", None)
    if md is None:
        return None
    tw = getattr(md, "time_worked_s", None)
    if tw is None:
        return None
    return {"time_worked_s": tw}


def _collect_traj(r, sink: list[str]) -> None:
    """从 act/act_get 结果的 metadata 收集本次 act 的 trajectory **HTML** 路径（ADR 0027）。

    Nova 每次 act 出一对产物：`act_<id>_<prompt>_trajectory.json`（数据）+ `act_<id>_<prompt>.html`
    （人看的轨迹页）。metadata.trajectory_file_path 给的是 .json；归集索引要指向人能看的 .html，
    故从 json 路径推导 html（去 `_trajectory.json` 加 `.html`）。html 不存在则回退 json。
    收集进 sink（=本 step 的累积器）；step_done 边界报成 step 级 reportRefs（kind=trajectory，下沉，ADR 0027）。
    """
    if _no_artifacts():
        return  # --no-report：不收集、不上报（SDK 仍会写进自己的临时目录，那是 SDK 内部行为）
    md = getattr(r, "metadata", None)
    p = getattr(md, "trajectory_file_path", None) if md else None
    if not p:
        return
    p = str(p)
    if p.endswith("_trajectory.json"):
        html = p[: -len("_trajectory.json")] + ".html"
        if os.path.exists(html):
            p = html
    # 绝对化兜底：reportRef 是 file://<path>，相对路径会成坏 URI（host 被当成路径首段）且跨进程
    # cwd 歧义。SDK 通常已回绝对路径（cli 传绝对 NOVA_LOGS_DIR）；此处再 abspath 一道，防御相对漏网。
    sink.append(os.path.abspath(p))


def _no_artifacts() -> bool:
    """`--no-report` 档（组合根经 env `GHERKAI_NO_ARTIFACTS=1` 告知，ADR 0037 决策 3）：**不生成、不上报**引擎原生产物。
    Nova Act SDK 没有关闭 trajectory 的开关——不传 logs_directory 时它写进自己 mkdtemp 的临时目录，那是 SDK 内部
    行为、不进项目；本 worker 此时不收集 trajectory、不带 summary、不发任何 reportRef。"""
    return os.environ.get("GHERKAI_NO_ARTIFACTS") == "1"


def _traj_refs(step_traj: list[str]) -> list[dict]:
    """本 step 收集的 trajectory 路径 → step 级 reportRefs（kind=trajectory，ADR 0027 下沉）。

    一个 step 可能多次 act（尤其 N 票 AI 断言）→ 多个 trajectory；label 仅在多个时编号。空列表 → 空。
    ref 经 `_get_uploader().to_report_ref` 得：cloud 上传 S3+删本地报 `s3://`，local no-op 报 `file://`（ADR 0029）。
    """
    n = len(step_traj)
    return [
        {"kind": "trajectory", "ref": _get_uploader().to_report_ref(p),
         "label": (f"trajectory {i + 1}" if n > 1 else "trajectory")}
        for i, p in enumerate(step_traj)
    ]


def _attach_traj_refs(ev: dict, step_traj: list, *, protect_emit: bool = False) -> None:
    """把本 step 的 trajectory 挂上 step_done 事件：抢传配套 json（ADR 0029）+ reportRefs（ADR 0027 下沉）。

    三个 emit 点（Then 投票/When 动作/except 失败）共用一份（曾三处重复、各自漂移风险）。
    protect_emit=True（失败路径）：上传若是本次失败源，_traj_refs 重建会再抛——吞掉、只丢 reportRefs 链接，
    绝不让调用方的 engine_error step_done 事件发不出去（否则降级成裸 traceback，ADR 0029）。
    """
    if not step_traj:
        return
    try:
        _presend_act_siblings(step_traj)  # act 边界抢传配套 json（ADR 0029，为 Fargate 预演）
        ev["reportRefs"] = _traj_refs(step_traj)  # step 级 trajectory（ADR 0027 下沉）
    except Exception:  # noqa: BLE001
        if not protect_emit:
            raise
        # 失败路径：重建 ref 时 upload 再失败 → 跳过 reportRefs、事件照发


def _presend_act_siblings(step_traj: list[str]) -> None:
    """act 边界抢传（ADR 0029「act 边界抢传」，为 Fargate 预演）：在 step_done 安全点，把本 step 各 act 的
    配套 `_trajectory.json`（数据文件，非 reportRef 指向的 .html）也即时上传，**不等 scope 末 flush**。

    否则中断落在 flush 前时这些 json 随容器盘销毁而丢（Fargate；subprocess 下留本地盘、非真丢）。
    `step_traj` 存的是 .html 路径（`_collect_traj` 已把 json 推成 html）——此处反推配套 json 抢传。
    复用幂等 `to_report_ref`（distinct key、记 `_uploaded` → scope 末 flush 自动跳过、不重传）；
    no-op（local/未注入落点）时 `to_report_ref` 原样返回不上传。**best-effort：失败吞掉**——抢传是保险，
    报告链接强保证仍锚在 `_traj_refs`（.html 实时传，失败抛→可观测），不下放到抢传。
    """
    for html in step_traj:
        if not html.endswith(".html"):
            continue
        js = html[: -len(".html")] + "_trajectory.json"
        if os.path.exists(js):
            try:
                _get_uploader().to_report_ref(os.path.abspath(js))  # 幂等上传+记账；返回值丢弃（json 不进 reportRefs）
            except Exception as e:  # noqa: BLE001  抢传 best-effort，失败不打断 step
                log(f"act 边界抢传 json 失败（忽略、scope 末 flush 兜底）：{e}")


def _run_step(nova, scenario_id: str, step: dict, votes_n: int, sink: EventSink) -> str:
    """派发执行一个 step，吐 step_done 事件（带本 step 的 trajectory reportRefs），返回 status。

    sink：事件出口（ADR 0024 I/O 边缘可注入接口，参数注入使测试可注 fake）——本函数所有事件经 sink.emit 吐。

    votes_n：AI 断言（Then）投票次数（来自 job.assertionVotes，ADR 0014）；1=不抖动检测。
    trajectory 收集在**本 step 局部**（每次 AI act 一个），随该 step 的 step_done 报出 step 级 reportRefs
    （ADR 0027 下沉：act 挂到其所属 step，不再聚合到 scenario 级）。确定性命中/URL 导航步不调 act、无 trajectory。

    派发优先级（ADR 0022/0020/0024）：
      ① 确定性注册表命中（测试开发注册的精确 handler，不投票、可复现）
      ② 内建 URL 导航（step 含引号内 URL）
      ③ Then → AI 断言 + 投票 / When·Given → AI 动作（默认 catch-all）
    """
    idx = step["index"]
    keyword = step["keyword"]
    text = step["text"]
    step_traj: list[str] = []  # 本 step 的 trajectory 路径（act 逐个收进来）
    tw_total = 0.0  # 本 step 已真实计费的 time_worked_s 累计（多票逐票加；except 分支也要报——费用不随异常蒸发，ADR 0024）

    sink.emit({"type": "step_started", "scenarioId": scenario_id, "stepIndex": idx})  # step 时长起点
    try:
        # ① 确定性注册表（ADR 0022）：命中走精确 handler、不投票；AssertionError→failed，其它→error
        hit = _deterministic.match(text)
        if hit is not None:
            handler, groups = hit
            ctx = _DeterministicCtx(nova)
            try:
                ret = handler(ctx, **groups)
                if inspect.isawaitable(ret):
                    # Nova 引擎是同步 worker：async handler 的断言不会被执行（返回 coroutine 即静默判 passed）。
                    # 显式报错而非静默假阳性——确定性 handler 必须同步（与 Nova SDK 同步模型一致）。
                    raise TypeError(
                        f"确定性 handler 不能是 async（Nova 引擎同步执行）：{getattr(handler, '__name__', handler)!r}"
                    )
            except AssertionError as ae:
                sink.emit({
                    "type": "step_done", "scenarioId": scenario_id, "stepIndex": idx,
                    "status": "failed", "errorType": "assertion_failed",
                    "message": str(ae) or f"确定性断言未过：{text}",
                })
                return "failed"
            sink.emit({"type": "step_done", "scenarioId": scenario_id, "stepIndex": idx, "status": "passed"})
            return "passed"

        url_match = _URL_IN_QUOTES.search(text)
        if url_match:
            # ② 内建确定性导航（ADR 0020）：抽 URL 直接 go_to_url，不浪费 AI
            nova.go_to_url(url_match.group(1))
            sink.emit({"type": "step_done", "scenarioId": scenario_id, "stepIndex": idx, "status": "passed"})
            return "passed"

        if keyword == "Then":
            # AI 断言 + N 次投票（ADR 0014/0024）；votes_n=1 即单次判定（仍发 votes 标记这是 AI 断言）
            instruction = _instruction(text, step)  # 自然语言 + 多行参数（DataTable/DocString，ADR 0024）
            votes = []  # N 票 time_worked_s 逐票累加进 tw_total（修：原 last_cost 只算最后一票，votes>1 时欠计 (N-1)/N）
            for _ in range(votes_n):
                if _stop.is_set():
                    break  # 停止信号（ADR 0024 flag-only）：多票途中收到 → 不再投后续票
                # act 套 timeout（ADR 0024 act 有界返回）：到点抛 ActTimeoutError（可 catch、归 timeout）
                r = nova.act_get(instruction, BOOL_SCHEMA, timeout=ACT_TIMEOUT_S)
                votes.append(bool(r.matches_schema and r.parsed_response))
                c = _cost_from_result(r)  # 每票各自的原生量（Nova 每 act 独立报，对称累加而非覆盖）
                if c and c.get("time_worked_s") is not None:
                    tw_total += c["time_worked_s"]
                _collect_traj(r, step_traj)  # N 票各一个 trajectory，都挂本 step
            if len(votes) < votes_n:
                # 票没投满（只可能因循环顶 _stop 提前 break）→ **不 emit 带 verdict 的 step_done**：
                # 用部分票 + 完整 votes_n 分母算 passed 会把「外部中止」误标成确定的断言判定（如 1/3→failed、
                # 甚至 0/1），污染中止 run 的 RunReport。对齐 _run_scenario 停止语义「停止是外部中止、非执行事实、
                # worker 不越权标注」——直接 return，交上层安全点协作退出、未跑完的 step 由 core 按派生态处理。
                # **判据是票不完整、不是此刻 _stop**（ADR 0024「安全点丢弃没跑完的单元的判定，但不丢弃已成的
                # 执行事实」）：停止信号落在最后一票的 act 期间时该票已带回判定，verdict 与已真实发生的
                # time_worked_s 都是执行事实，照常 emit（对称 When/Given 分支）、再由上层安全点退出。
                return "aborted"
            yes = sum(votes)
            passed = yes > votes_n / 2
            ev = {
                "type": "step_done", "scenarioId": scenario_id, "stepIndex": idx,
                "status": "passed" if passed else "failed",
                "votes": {"yes": yes, "total": votes_n},
            }
            if tw_total > 0:
                ev["cost"] = {"time_worked_s": tw_total}  # 全 N 票合计
            _attach_traj_refs(ev, step_traj)
            if not passed:
                ev["errorType"] = "assertion_failed"
                ev["message"] = f"AI 断言未过多数票（{yes}/{votes_n}）：{text}"
            sink.emit(ev)
            return "passed" if passed else "failed"

        # When / Given（非 URL）→ AI 动作（无 votes）
        # act 套 timeout（ADR 0024 act 有界返回）：到点抛 ActTimeoutError（可 catch、归 timeout）
        r = nova.act(_instruction(text, step), timeout=ACT_TIMEOUT_S)
        _collect_traj(r, step_traj)
        ev = {"type": "step_done", "scenarioId": scenario_id, "stepIndex": idx, "status": "passed"}
        cost = _cost_from_result(r)
        if cost:
            ev["cost"] = cost
        _attach_traj_refs(ev, step_traj)
        sink.emit(ev)
        return "passed"

    except Exception as e:
        # 失败的 act 最需要看 trajectory——Nova 的 ActError 也带 metadata.trajectory_file_path
        # （SDK 在 finally 已写盘），同一 helper 收集（ADR 0027：失败 act 的产物不丢）。
        _collect_traj(e, step_traj)
        # 诊断分类细化（ADR 0028）：act 中途若是网络瞬时故障（CDP 闪断等），标 network_error 比笼统
        # engine_error 更准——便于排查"是网络抖动还是 AI 真出错"。**仅分类、不触发重试/恢复**：act 不幂等，
        # schedule 的 job 级重试要求「会话未起（零 step_done）」，而此处 step_started 早已 emit、saw_step=True，
        # 双条件 AND 天然不满足；且本失败走 step_done 事件流（非退出码 80），core 侧 is_network=False。
        # 故"act 中途恢复"仍是 defer（ADR 0028），这里只把失败原因记准。
        ev = {
            "type": "step_done", "scenarioId": scenario_id, "stepIndex": idx,
            "status": "error", "errorType": _classify_act_error(e), "message": f"{type(e).__name__}: {e}",
        }
        # 失败 act 的费用已经发生（ADR 0024「失败的 act 同样带 cost」）：SDK 异常对象同样带 metadata.time_worked_s，加上
        # 本 step 已投完的票；曾整块丢掉 → total_time_worked_s 对所有出错 step 系统性低报。
        c = _cost_from_result(e)
        tw = tw_total + float((c or {}).get("time_worked_s") or 0.0)
        if tw > 0:
            ev["cost"] = {"time_worked_s": tw}
        # 失败 act 的 trajectory 最该留（ADR 0027/0028）——protect_emit：上传再失败也绝不吞 engine_error 事件
        _attach_traj_refs(ev, step_traj, protect_emit=True)
        sink.emit(ev)
        return "error"


# 只剥 ASCII 空白（与 Midscene 的 unquote 同集合）——不用裸 strip()：Python strip 剥 U+001C-1F/U+0085
# 而 JS trim 不剥、却剥 U+FEFF(BOM)，两个引擎分叉（BOM 能穿透 gherkin 进 text）。显式同集合保对称。
_ASCII_WS = " \t\r\n\f\v"


def _unquote(text: str) -> str:
    """step 自然语言外层若整体被引号包裹（QA 写 When "搜索 X"），剥掉外引号喂引擎。"""
    t = text.strip(_ASCII_WS)
    if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
        return t[1:-1]
    return t


def _clean_cell(c: str) -> str:
    """单元格清洗（与 Midscene cleanCell 同一规则）：cell 内 | 与换行会破坏 markdown 表格行结构
    → | 转义成 \\|、换行压成空格，使每个 cell 仍占一格、表格结构忠实。"""
    return str(c).replace("|", "\\|").replace("\r\n", " ").replace("\r", " ").replace("\n", " ")


def _argument_text(arg: dict | None) -> str:
    """把 step 的多行参数（DataTable/DocString，ADR 0024/0025）拼成附加文本，接在 step 指令后喂 AI。

    - dataTable：rows（二维字符串数组）拼回 markdown 表格（| 分隔，还原 QA 在 .feature 写的样子，LLM 友好）。
    - docString：content 多行文本原样。
    两个引擎（Nova/Midscene）须同一拼法，保同一 feature 行为对称（ADR 0024）。
    注：rows 单元恒为字符串（core/wire 只发字符串）；_clean_cell 的 str() 仅防御，正常管线不可达非字符串。
    """
    if not arg:
        return ""
    kind = arg.get("kind")
    if kind == "dataTable":
        rows = arg.get("rows") or []
        if not rows:
            return ""
        return "\n".join("| " + " | ".join(_clean_cell(c) for c in row) + " |" for row in rows)
    if kind == "docString":
        return arg.get("content") or ""
    return ""


def _instruction(text: str, step: dict) -> str:
    """喂 AI 的完整指令 = 去引号的 step 自然语言 + （可选）多行参数（ADR 0024：text(+argument) 一起喂引擎）。"""
    base = _unquote(text)
    extra = _argument_text(step.get("argument"))
    return f"{base}\n{extra}" if extra else base


def _run_scenario(nova, scenario_id: str, steps: list[dict], votes_n: int, sink: EventSink) -> list[str]:
    """scope 内串行跑一个 scenario 的 steps，上游 error 后**短路**后续 step（ADR 0031 决定六 / 0028）。

    短路：scenario 内一旦某 step `status==error`（导航 SSL 失败等），后续 step 不再调 AI——
    ① 节省费用（不再调用后续 AI 断言）；② 不在损坏环境（SSL 错误页）上跑出误导性假失败。被跳过的 step 发独立
    `step_skipped` 事件（非 step_done；core 据此本地赋 StepResult(SKIPPED, shortcircuited=True)）。
    判据锁 `status==error`（不看 error_type）——两个引擎对称、network/engine 错都触发。

    **短路只作用于本 scenario**（不跨 scenario：下一 scenario 可能导航到新页恢复，独立测试用例不该被牵连；
    跨 job 的中止是 fail-fast 的职责，两者正交，ADR 0031 决定六）。返回各步 status——被跳过步**不进** statuses，
    故不参与 _aggregate；scenario 判定由那个 error step 决定（与后面短路了几步无关）。
    """
    statuses: list[str] = []
    shortcircuit = False
    for st in steps:
        if _stop.is_set():
            break  # 停止信号（ADR 0024 flag-only）：不再跑后续 step，交上层协作式退出释放会话。
            # 不发 step_skipped（那是 error 短路的语义、表"因上游故障跳过"）；停止是外部中止、非执行事实，
            # 未跑的 step 由 core 侧按 aborted/pending 派生态处理（wire 不传，ADR 0031），worker 不越权标注。
        if shortcircuit:
            sink.emit({"type": "step_skipped", "scenarioId": scenario_id, "stepIndex": st["index"]})
            continue
        status = _run_step(nova, scenario_id, st, votes_n, sink)
        if status == "aborted":
            break  # step 被外部中止（投票途中收到 _stop）：不进 statuses、不参与 _aggregate，
            # 与循环顶 _stop 检查同语义（外部中止非执行事实）。下轮循环顶的 _stop 检查也会 break，这里提前收。
        statuses.append(status)
        if status == "error":
            shortcircuit = True  # 本 scenario 后续 step 短路（不跨 scenario）
    return statuses


def _aggregate(statuses: list[str]) -> str:
    if any(s == "error" for s in statuses):
        return "error"
    if any(s == "failed" for s in statuses):
        return "failed"
    return "passed"


def _emit_scenario_done_unless_stopped(sink: EventSink, scenario_id: str, statuses: list[str]) -> bool:
    """scenario 跑完后的 scenario_done 出口 + 中止护栏（模块级、供单测直驱）。

    返回 True＝中止（调用方应停止本 session、不再跑后续 scenario）。**中止时绝不 emit scenario_done**：
    scenario 中途收到 _stop 时 `_run_scenario` 返回**部分 statuses**，用它算判定会把没跑完的 scenario 标成
    确定 passed（假阳性——`_aggregate([])`/`_aggregate(["passed"])` 都 == "passed"），违反「停止是外部中止、
    非执行事实、worker 不越权标注」（ADR 0031/0024）；未完成 scenario 交 core 按派生态处理。对称 step 级投票
    中止（**票没投满**时不 emit 带 verdict 的 step_done）+ scenario 循环顶护栏（不发 step_skipped）。
    """
    if _stop.is_set():
        return True
    sink.emit({"type": "scenario_done", "scenarioId": scenario_id, "status": _aggregate(statuses)})
    return False


import socket
import ssl

# 网络专用退出码（ADR 0028）：与 core/gherkai_core/wire.py 的 EX_WORKER_NETWORK 同值（协议层单一事实源，两 Engine adapter 共用翻译）。
EX_WORKER_NETWORK = 80

# 建连重试参数（ADR 0028）：仅裹幂等的建连段，act 永不重试。退避手写（不用 botocore 内部 retry，
# 否则 SIGTERM 穿不透）；总退避预算 ~3.5s < schedule 默认 grace 5s。
_CONNECT_ATTEMPTS = 4
_BACKOFF_S = [0.5, 1.0, 2.0]  # attempt 失败后的退避：固定退避、不加 jitter（本地 smoke 单 worker、无雷群效应；
                              # 总预算 ~3.5s < grace，见上）


def _backoff_interrupted(attempt: int) -> bool:
    """建连重试的退避（ADR 0028 + 0024 flag-only）。返回 True=退避中收到停止信号（应停止重连）。

    用 `_stop.wait(backoff)` 而非 `time.sleep(backoff)`：SIGTERM/SIGINT handler `set` 标志后 wait 立即
    返回 True（flag-only 下 time.sleep 不被打断、会睡满，PEP 475）——使建连退避期间收到信号能即时协作停。
    抽成模块级函数供单测直驱（否则 test 只测 stdlib Event.wait、不碰本退避路径，是假绿）。
    """
    backoff = _BACKOFF_S[min(attempt, len(_BACKOFF_S) - 1)]
    return _stop.wait(backoff)


# boto ClientError 的瞬时/节流错误码集（ADR 0028）——**对齐 botocore 权威常量、借判据不借 API**：
# 以 TransientRetryableChecker._TRANSIENT_ERROR_CODES + ThrottledRetryableChecker._THROTTLED_ERROR_CODES
# 为基线，另**有意增补** ServiceUnavailable / ServiceUnavailableException（botocore 那两个常量集里没有——
# 它靠 _TRANSIENT_STATUS_CODES 的 503 兜；我们照抄了那组状态码，但服务端不带 HTTP 状态只给码时兜不住，故显式补）。
# AgentCore 起会话（start_browser_session）是 boto3 调用，服务端瞬时不可用/限流抛 ClientError（直接继承
# Exception、混着永久错），故按码细分、不整类当瞬时。内联这张稳定的码表而非硬构造 botocore RetryContext 去
# 调它的 is_retryable（那要请求栈内部对象、跨版本脆，且我们 catch 到的是被 Nova SDK 包两层的异常、没有 RetryContext）。
_BOTO_TRANSIENT_CODES = frozenset({
    "RequestTimeout", "RequestTimeoutException", "PriorRequestNotComplete",  # 瞬时
    "Throttling", "ThrottlingException", "ThrottledException", "RequestThrottledException",  # 节流
    "TooManyRequestsException", "ProvisionedThroughputExceededException", "TransactionInProgressException",
    "RequestLimitExceeded", "BandwidthLimitExceeded", "LimitExceededException", "RequestThrottled",
    "SlowDown", "EC2ThrottledException", "ServiceUnavailable", "ServiceUnavailableException",
})
_BOTO_TRANSIENT_STATUS = frozenset({500, 502, 503, 504})


def _is_transient_client_error(e: BaseException) -> bool:
    """boto ClientError 是否服务端瞬时（按错误码/HTTP 状态码细分，ADR 0028）。非 ClientError 返回 False。"""
    try:
        from botocore.exceptions import ClientError
    except ImportError:
        return False
    if not isinstance(e, ClientError):
        return False
    resp = getattr(e, "response", None) or {}
    code = (resp.get("Error") or {}).get("Code")
    if code in _BOTO_TRANSIENT_CODES:
        return True
    status = (resp.get("ResponseMetadata") or {}).get("HTTPStatusCode")
    return status in _BOTO_TRANSIENT_STATUS  # 5xx（500/502/503/504）；4xx 客户端错/其余 → 永久


def _is_transient_network(e: BaseException, *, connecting: bool = False) -> bool:
    """是否网络/SSL 瞬时故障（可重试，ADR 0028）。

    白名单匹配**具体**瞬时类型，不用宽 OSError 兜底——ssl.SSLError 与 socket.gaierror 都继承 OSError，
    宽匹配会把永久错也当瞬时重试。gaierror 按 errno 细分：EAI_AGAIN(临时) 当瞬时、其余(EAI_NONAME 等永久) 否决
    （对齐 Midscene 的 EAI_AGAIN 白名单，保两个引擎对 DNS 临时抖动恢复力对称，ADR 0028）。
    boto `ClientError` 按错误码/HTTP 状态码细分（节流/5xx 瞬时、4xx/ValidationException 永久，见 _is_transient_client_error）。

    **遍历异常链**（__cause__/__context__）：Nova/boto SDK 常把底层瞬时错包成自有异常
    （AgentCore 会话建立失败 → BrowserAuthError ← ClientError，每层带 from），只看最外层会漏判——
    任一层命中白名单即判瞬时（用 id 集防环）。

    **connecting=True（仅建连阶段传，ADR 0028）**：额外把 Playwright `TargetClosedError`
    （`CDPSession.send: Target ... has been closed`）判瞬时。它是 CDP/websocket 连接被网络断掉后的
    **下游症状**异常——Playwright 把底层 socket 故障吞掉、只抛这个不继承 OSError/__cause__ 为 None 的“干净”异常，
    白名单无从穿透（真跑复现：会话已起、`with NovaAct.__enter__` 内撞网络断）。因它语义模糊
    （网络断/会话正常关/浏览器真崩同报一句），**只在建连阶段认**（scope_started 未 emit、act 无副作用、重试安全，
    是已有重试域的物理边界）；act 中途（connecting=False）不认，守“拿不准→不归 network”铁律。
    """
    transient: tuple[type[BaseException], ...] = (ssl.SSLError, ConnectionError, TimeoutError, socket.timeout)
    try:
        from botocore.exceptions import (
            EndpointConnectionError, ConnectionClosedError, ConnectTimeoutError, ReadTimeoutError,
        )
        transient += (EndpointConnectionError, ConnectionClosedError, ConnectTimeoutError, ReadTimeoutError)
    except ImportError:
        pass
    try:
        from urllib3.exceptions import ProtocolError
        transient += (ProtocolError,)
    except ImportError:
        pass
    _pw_closed_by_name = False
    if connecting:  # 建连阶段额外认 Playwright 连接被关（下游症状，见 docstring）
        # 精确匹配 TargetClosedError（不用其基类 Error——那会把参数错/协议错等永久错也当瞬时，违背不宽兜底）。
        # 私有路径 _impl._errors（sync_api 未顶层导出它）；导入失败则按类名兜底（防 SDK 版本挪位）。
        try:
            from playwright._impl._errors import TargetClosedError as _PWClosed
            transient += (_PWClosed,)
        except ImportError:
            _pw_closed_by_name = True

    seen: set[int] = set()
    cur: BaseException | None = e
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        if isinstance(cur, socket.gaierror):
            # DNS 解析失败：按 errno 细分（gaierror 同时覆盖临时与永久，不能一律否决）——
            # EAI_AGAIN(临时，可重试，对齐 Midscene 的 EAI_AGAIN 白名单) → 瞬时；其余(EAI_NONAME 等永久) 否决。
            return cur.args[0] == socket.EAI_AGAIN if cur.args else False
        if _is_transient_client_error(cur):  # boto ClientError 节流/5xx（AgentCore 起会话瞬时故障，ADR 0028）
            return True
        if isinstance(cur, transient):
            return True
        if _pw_closed_by_name and type(cur).__name__ == "TargetClosedError":
            # 按名兜底也须在**链内**判（真实包装链 TargetClosedError ← StartFailed ← BrowserAuthError，
            # 最外层不是它——曾只查最外层 e，兜底形同虚设：私有路径一挪位建连 CDP 断连即误判 engine_error 不重试）。
            return True
        cur = cur.__cause__ or cur.__context__
    return False


def _classify_act_error(e: BaseException) -> str:
    """把 act/act_get 中途异常映射到规范化 errorType（ADR 0024/0028）。优先级：
    网络瞬时 > Nova SDK 异常树（timeout/guardrail/…）> engine_error 兜底。
    **仅诊断分类、不影响重试/恢复**（act 不幂等，恢复仍 defer，ADR 0028）。
    Nova SDK 异常树现成且结构化（act_errors.py），把 timeout/guardrail 从笼统 engine_error 拆出，
    便于排查与未来按类型处置（ADR 0024「errorType 已实现但粗粒度，留待细化」的兑现）。"""
    if _is_transient_network(e):
        return "network_error"
    try:
        from nova_act.types.act_errors import (
            ActTimeoutError, ActGuardrailsError, ActStateGuardrailError,
        )
        timeout_types: tuple[type[BaseException], ...] = (ActTimeoutError,)
        guardrail_types: tuple[type[BaseException], ...] = (ActGuardrailsError, ActStateGuardrailError)
    except ImportError:
        return "engine_error"
    if isinstance(e, timeout_types):
        return "timeout"
    if isinstance(e, guardrail_types):
        return "guardrail"
    return "engine_error"  # 其余执行故障（含未细分的 ActError 子类）仍归 engine_error


def main() -> int:
    # 使用方确定性 step 目录（ADR 0037 决策 4）：内建脚手架已在模块顶 import 期注册完，这里把使用方的叠上去。
    # 位置是**契约的一部分**：先于下面三条路径的任何一条（job 模式 / --list-deterministic / --match-steps），
    # 故自述入口报的注册表与真跑派发用的是同一张表（ADR 0036「真值单一」不因定制而破）。
    # worker 只认 env、不解析约定（`--steps-dir` / 默认 `./steps` / 写进 definition 全在组合根）。
    # 加载失败 fail-loud（绝不静默跳过——跳过 = 把确定性 step 静默换成 AI catch-all、run 可能假「通过」）。
    try:
        load_user_steps(os.environ.get("GHERKAI_STEPS_DIR"))
    except UserStepsError as e:
        log(f"worker: {e}")
        return EX_STEPS_LOAD

    # 自述模式（ADR 0036）：dump 确定性注册表即退——不建会话、不读 stdin、零费用。
    # 内建脚手架（模块顶 import 的副作用）+ 上面加载的使用方 step，此刻注册表即真值。
    if "--list-deterministic" in sys.argv:
        print(json.dumps(_deterministic.list_registry(), ensure_ascii=False))
        return 0
    # 批量 match 查询（ADR 0036 决策 4，plan 命中标注）：stdin 一行 JSON 数组（step 文本）→ stdout
    # 逐条命中结果。匹配语义留在 worker（CLI 零复刻）；同样不建会话、零 AWS。
    if "--match-steps" in sys.argv:
        texts = json.loads(sys.stdin.read())
        print(json.dumps(_deterministic.match_batch(texts), ensure_ascii=False))
        return 0

    # flag-only handler 装在 job 模式的首句（模块级 _on_signal，SIGTERM/SIGINT 共用，只置 _stop、绝不 raise，
    # ADR 0024）——必须先于 JobSource.read()：S3 态下 read 含一次网络往返，曾装在其后，窗口内 SIGTERM 走
    # 默认处置直接杀进程（非 0 退出）→ adapter 误归 engine_error（ADR 0024 已根治场景的残余窗口）。
    # （上面的 steps 加载在此之前、仍走默认处置：那段是纯本机文件 import、无会话无网络，被杀不泄漏也不误归因。）
    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)  # Ctrl-C 也走 flag-only（原走默认 KeyboardInterrupt 同样撞 greenlet）

    # I/O 边缘可注入接口（ADR 0024）：job 入口 / 事件出口从内联收进 lib 组件，subprocess 态=读 stdin / 写 EVENTS_FD。
    job = JobSource.from_env().read()
    if _stop.is_set():
        log(f"worker: signal {_stop_signum} received before job start, cooperative stop")
        return 0  # 读 job 期间已收停（对齐 _run_session 顶的检查）：零事件干净退，core 判 error 不误归因
    sink = EventSink.from_env()  # main 级单例（对称 _uploader）；作参数注入 _run_scenario/_run_step
    scope = job["scope"]
    scenarios = job["scenarios"]
    votes_n = int(job.get("assertionVotes", 1))  # AI 断言投票次数（ADR 0014/0024）；缺省 1
    session_id = None
    network_exhausted = False  # 建连重试耗尽（ADR 0028）：置位 + 正常退出 with → return EX_WORKER_NETWORK

    ensure_workflow_definition(WORKFLOW_DEF, region=REGION, description="Nova Act worker")
    wf = Workflow(model_id=MODEL_ID, boto_session_kwargs={"region_name": REGION}, workflow_definition_name=WORKFLOW_DEF)
    # 建连重试状态（ADR 0028）：started 一旦 True（scope_started 已 emit、会话已起），
    # 任何后续异常都不再当「可重试建连失败」——act 已可能跑、有副作用，绝不重试。
    started = False

    def _run_session() -> None:
        """建连 + 跑完所有 scenarios。建连段异常可被外层重试；scope_started emit 后不可。

        停止（_stop）在此协作式生效：scenario 循环顶检测 → 正常 return 出本函数 → `with NovaAct`/
        `with cdp_session` 正常退出触发 __exit__ 释放会话（ADR 0024 flag-only，不靠异常穿透）。
        """
        nonlocal session_id, started
        if _stop.is_set():
            return  # 建连前已收到停止信号（含建连早期 SIGTERM——Workflow() 构造期到达，见 ADR 0024）→ 干净退、不建连
        provider = AgentCoreBrowserSessionProvider(region=REGION)
        with provider.cdp_session() as (ws_url, headers):
            # logs_directory：trajectory 落到 run 专属持久目录（ADR 0027）。cli 经环境变量
            # NOVA_LOGS_DIR 传入 reports/<run_id>/nova-trajectories；无则用 SDK 默认临时目录
            # （会被系统清理）。Nova 的 validate_path 要求该目录**已存在**，故先 mkdir。
            logs_dir = None if _no_artifacts() else (os.environ.get("NOVA_LOGS_DIR") or None)
            if logs_dir:
                os.makedirs(logs_dir, exist_ok=True)
            with NovaAct(
                cdp_endpoint_url=ws_url, cdp_headers=headers, browser_auth=provider,
                starting_page="about:blank", logs_directory=logs_dir,
                # tty=False：worker 是 cli spawn 的子进程，stdout/stderr 是管道而非交互终端。
                # SDK 默认 tty=True 会喷逐帧刷新的思考动画（💭 . / 💭 .. / 🎬 …），在管道里成了刷屏噪声；
                # 关掉后输出干净的逐行日志（think/return/Approx. Time Worked 等有用行保留）。SDK 文档亦推荐非 tty 场景置 False。
                tty=False,
            ) as nova:
                # 额外请求头（ADR 0035，如 ngrok-skip-browser-warning）：组合根经 env 注入，context 级
                # 对所有请求（含 SDK 之后新开的 page）生效。纯 CDP 命令、无回调——不触碰 SDK 的
                # route/greenlet 面（nova.page 是 SDK 公开属性，_DeterministicCtx 同源用法）。
                extra_headers = os.environ.get("GHERKAI_EXTRA_HTTP_HEADERS")
                if extra_headers:
                    nova.page.context.set_extra_http_headers(json.loads(extra_headers))
                # 取真实 AgentCore 会话 id（血缘，进 RunStore，ADR 0016/0024）。
                session_id = nova.get_session_id()
                # session_id 随 scope_started 即回传（不只等 scope_done）——超时/SIGTERM 中途打断时
                # scope_done 不会 emit，但血缘已先随首事件落到 core（ADR 0028 观测缺口修复）。
                sink.emit({"type": "scope_started", "scopeId": scope["id"], "sessionId": session_id})  # 三级时长起点
                started = True  # 越过此点 = 会话已起、act 即将跑 → 退出建连重试域（ADR 0028）
                # scope 内串行跑 scenarios，共享同一会话（ADR 0019/0024）
                for sc in scenarios:
                    if _stop.is_set():
                        return  # 停止信号（ADR 0024 flag-only）：正常 return 出本函数 → with __exit__ 释放会话
                    sid = sc["id"]
                    sink.emit({"type": "scenario_started", "scenarioId": sid})
                    # trajectory 现由每个 _run_step 挂进各自 step_done 的 step 级 reportRefs（ADR 0027 下沉）——
                    # 不再在 scenario 级聚合；scenario_done 不带 reportRefs（协议字段保留、向后兼容）。
                    # scope 内 step 短路（上游 error 跳过后续、发 step_skipped，ADR 0031 决定六）在 _run_scenario 内。
                    statuses = _run_scenario(nova, sid, sc["steps"], votes_n, sink)
                    # scenario_done 出口 + 中止护栏（模块级 _emit_scenario_done_unless_stopped，供单测直驱）：
                    # 中途中止时不 emit（部分 statuses 会算出假 passed），返 True → 停本 session。
                    if _emit_scenario_done_unless_stopped(sink, sid, statuses):
                        return

    with wf:
        outer = get_current_workflow()
        set_current_workflow(wf)
        try:
            # 建连重试循环（ADR 0028）：仅裹建连段；scope_started 一 emit 即 started=True、跳出重试。
            # 每次 attempt 用全新 provider/cdp_session/NovaAct，with __exit__ 清掉本次部分建起的会话。
            for attempt in range(_CONNECT_ATTEMPTS):
                if _stop.is_set():
                    break  # 停止信号（ADR 0024 flag-only）：不再重试建连 → 干净退（下方按 _stop 返回 0）
                try:
                    _run_session()
                    break  # 成功（跑完，或 _run_session 内因 _stop 协作式 return）
                except Exception as e:  # noqa: BLE001  建连域异常（_run_session 内 with __exit__ 已清本次部分会话）
                    # connecting=True：本分支即建连域（started=True 时下句直接 raise，走不到判定），
                    # 故额外认 Playwright TargetClosedError（连接被网络断的下游症状，ADR 0028）。
                    if started or not _is_transient_network(e, connecting=True):
                        raise  # 会话已起 / 非瞬时网络错 → 不重试，原样冒泡
                    if attempt >= _CONNECT_ATTEMPTS - 1:
                        log(f"worker: 建连重试耗尽（{attempt + 1} 次），网络/SSL 瞬时故障：{e}")
                        network_exhausted = True  # 置位 + 跳出 → 正常退出 with 后 return EX_WORKER_NETWORK（不 raise 穿透）
                        break
                    log(f"worker: 建连失败（attempt {attempt + 1}），退避后重试：{e}")
                    # 手写退避（ADR 0028 + 0024 flag-only）：_backoff_interrupted 用 _stop.wait，收到信号即唤醒。
                    if _backoff_interrupted(attempt):
                        break  # 退避中收到停止信号 → 不再重连
        finally:
            set_current_workflow(outer)

    # 停止信号（ADR 0024 flag-only）：三层 with 已正常退出（__exit__ 释放了会话）。干净退、不吐 scope_done、不 flush。
    if _stop.is_set():
        log(f"worker: signal {_stop_signum} received, cooperative stop — session shutdown complete")
        return 0
    if network_exhausted:
        # 建连重试耗尽（ADR 0028）：with __exit__ 已清理。以网络专用退出码退出，core 据此记 network_error。不吐 scope_done。
        log("worker: connect retries exhausted, exiting with network code")
        return EX_WORKER_NETWORK

    # scope 级 reportRef：Nova SDK 落的 session_summary.json（session_id/time_worked_s/act_count 等）作
    # kind=summary（引擎特有富信息载体、非人看报告，经不透明指针给 agent，ADR 0027）。SDK 把它落在
    # NOVA_LOGS_DIR/<session_id>/session_summary.json（多拼一层 session_id 子目录），且仅 act_count>0 时写——
    # 故文件存在才带（纯确定性/零耗时 scope 不写）。用 os.environ 重取 base（logs_dir 是 _run_session 局部）。
    scope_refs: list[dict] = []
    base = None if _no_artifacts() else os.environ.get("NOVA_LOGS_DIR")
    if base and session_id:
        summary = os.path.abspath(os.path.join(base, session_id, "session_summary.json"))
        if os.path.exists(summary):
            # ref 经 uploader：cloud 上传 S3+删本地报 s3://，local no-op 报 file://（ADR 0029）。
            # **scope 级 summary 上传 best-effort：失败吞+log、不带 summary ref、不拖垮 scope_done**（ADR 0032）——
            # session_summary 是"锦上添花的数字汇总"（引擎特有富信息、非人看报告，ADR 0027），此刻 scope 判定
            # 已 emit 完，不该因它上传失败（多为 S3 网络瞬时）把已跑完的 scope 拖成裸 traceback/engine_error。
            # 对齐同文件抢传/flush 的 best-effort。**与 step 内 trajectory 的强保证不同**：trajectory 是判定现场
            # 证据（`to_report_ref` 失败抛、可观测）、summary 只是数字汇总，故此处降级、不动 to_report_ref 本身。
            try:
                scope_refs.append({"kind": "summary", "ref": _get_uploader().to_report_ref(summary), "label": "Nova session summary"})
            except Exception as e:  # noqa: BLE001
                log(f"scope 级 session summary 上传失败（best-effort、忽略、不带 summary ref）：{type(e).__name__}: {e}")
    ev = {"type": "scope_done", "scopeId": scope["id"], "sessionId": session_id}
    if scope_refs:
        ev["reportRefs"] = scope_refs
    sink.emit(ev)
    # scope 末：整目录 flush 剩余产物（trajectory .json / log 等，已实时传的 reportRef 文件跳过）+ 全成功删本地
    # （ADR 0029）。no-op（local/未注入落点）时直接返回、不碰本地。仅正常完成路径走到此；停止信号/网络耗尽的
    # 提前 return（见上）不 flush——中断产物保留本地（见 ADR 0028）。
    if base:
        _get_uploader().flush_and_cleanup(base)
    return 0


if __name__ == "__main__":
    sys.exit(main())
