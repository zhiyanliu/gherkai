// step 级机读证据（ADR 0042 决策一/二）：step 边界把「问了引擎什么、引擎逐步看见/想了什么、结果与错误」
// 裁成 gherkai 自有 schema 的 `evidence.json`，挂 step_done 的 kind=evidence ref，供 `gherkai explain` 消费。
// 「act」在此指一次 AI 调用（Midscene 的一次 `ai*`），是本产物的结构词、不是 core 域模型字段。
//
// 四条硬约束，全部来自 ADR 0042：
// ① **SDK 耦合只住这一个模块**（决策六）：本模块自写「只含所读字段」的结构类型，**不从 @midscene/core
//    import 类型**——它不是本包声明依赖（只声明 @midscene/web）。逐字段容缺（读不到 → null / 空数组、
//    不抛），判别一律按**值**不按 SDK 的布尔标志。格式漂移在 fixture 测试里变红。
// ② **绝不读截图的 `.base64`**（决策一映射表）：SDK 每个 task 更新后即 flush 报告、把 base64 置空，之后
//    读它会对多 MB 的 report.html 做同步全文扫描且找不到即抛。改为引用 SDK 自己落盘的截图文件——agent
//    建时传 `persistExecutionDump: true`，SDK 把每张截图写成 `<run 目录>/report/screenshots/<id>.<扩展名>`，
//    evidence 只按 id + 扩展名拼路径，零解码零复制。
// ③ **截图 URI 不即时上传、字节也不等到 scope 末**（决策一「上传时机分两类」）：URI 用上传器同一 key 规则的
//    `refFor` 确定性算出写进 json；字节由调用方在 step_done **emit 之后**交上传器的后台队列（本模块把引用到
//    的截图本地路径一并回传，见 `StepEvidence.screenshots`），scope 末的整目录 flush 只兜漏网。理由：即时上传
//    是逐文件串行 PutObject 且套短超时，把 K × 票数次压在判定临界路径上会把已成的判定拖在网络上；而只靠
//    scope 末 flush，中断路径根本不 flush。`evidence.json` 自身相反——它的 ref 必须随 step_done 走，故经
//    `toReportRef` 即时传。
// ④ **对判定零影响**（决策二，这是对「step 内产物上传失败即抛」开的具名例外）：抽取 / 落盘 / 上传任一环
//    失败 → 一行日志、本 step 不带 evidence ref，step_done 的 status / votes / cost / message 照发。故对外
//    只暴露一个「绝不抛」的 `stepEvidenceRef`，调用方无需自己兜：裸放进 runStep 的 try 里，一次上传抖动
//    就会被 catch 分类成 network_error / engine_error，把已成的 passed 判定翻掉。
import * as crypto from "node:crypto";
import * as fs from "node:fs";
import * as path from "node:path";

/** evidence schema 版本（ADR 0042 决策六第 3 道防线：消费端据此判「不认识的版本」）。 */
export const EVIDENCE_SCHEMA_VERSION = 1;
/** step_done 上这条 ref 的 kind 与 label（ADR 0042 决策一；kind 本就是引擎自报的开放字符串）。 */
export const EVIDENCE_KIND = "evidence";
/** 引擎名（evidence 的 engine 字段；两引擎同形、各报自己的名）。 */
const ENGINE = "midscene";

// 截图上界（ADR 0042 决策一「截图策略（有上界）」）：**只有 screenshot 受限**，frames 的 thought / actions
// 全保留（文本很小）。单次 AI 调用的帧数由 SDK 默认步数上限封顶、再乘投票次数，不设上界时单个 failed Then
// 可达数十帧、按 100~200 KB/帧即 10 MB 量级。故 failed / error step 每个 act 最多 K 张（末帧、首个含
// thought 的帧、出错帧），每 step 总数再封 M 张；passed step 每 act 只留末帧一张。按截图 id 去重后计。
const MAX_SHOTS_PER_ACT = 3;
const MAX_SHOTS_PER_STEP = 12;
// 目录名里 scenario_id 转义部分的长度上限：文件系统单个路径分量有字节上限，而 scenario_id 含 feature 路径、
// 可以很长。截断只损可读性——不撞名由尾附的短哈希保证（见 scenarioKey）。
const KEY_SLUG_MAX = 80;

// ---- 本模块所读的 SDK 结构（自写、只含用到的字段，见文件头①）----

/** 截图对象：内存态是 SDK 的 ScreenshotItem（id / extension 是 getter），序列化态是只带 id / mimeType 的引用。 */
interface ShotLike { id?: string; extension?: string; mimeType?: string }
/** task 的动作录像项：只关心 timing（挑「动作后」那张）与其 screenshot。 */
interface RecorderLike { timing?: string; screenshot?: unknown }
/** 一个 ExecutionTask = evidence 的一个 frame。 */
interface TaskLike {
  type?: string;
  subType?: string;
  param?: unknown;
  thought?: string;
  output?: unknown;
  errorMessage?: string;
  status?: string;
  uiContext?: { screenshot?: unknown };
  recorder?: RecorderLike[];
}
/** 一个 execution = evidence 的一个 act（一次 `aiAct` / `aiBoolean` / `aiQuery`）。 */
interface ExecutionLike { name?: string; tasks?: TaskLike[] }

// ---- evidence 文档（schema 由 gherkai 定义，两引擎同形；键名/类型即契约，不承诺每次填满）----

export interface EvidenceFrame {
  /** 逐 frame URL 仅 Nova 有；Midscene 的 task 不带 URL → 恒 null（ADR 0042 映射表）。 */
  url: string | null;
  thought: string | null;
  /** args = 引擎原样透传的对象，内部键随 SDK、不属本契约。 */
  actions: Array<{ name: string; args: unknown }>;
  /** 只有被截图策略选中的 frame 非 null。 */
  screenshot: string | null;
}

export interface EvidenceAct {
  index: number;
  /** gherkai 交给引擎的指令（step 文本 + 多行参数）；**不取** execution.name——那是 SDK 展示名。 */
  prompt: string | null;
  /** 本次调用计入判定的那一票；null = 本 act 不是投票调用（When / Given 的动作）。 */
  vote: boolean | null;
  url: string | null;
  frames: EvidenceFrame[];
  /** 引擎原生返回值原样（末个 task 的 output）。仅供阅读，判票看 vote。 */
  result: unknown;
  error: string | null;
  /** Nova 的计费量；Midscene 恒 null（其 per-task timing 是另一种量、不混用）。 */
  time_worked_s: number | null;
}

export interface EvidenceDoc {
  schema_version: number;
  engine: string;
  scope_id: string;
  scenario_id: string;
  /** scenario 内 0 起的书写序号。 */
  step_index: number;
  step: { keyword: string; text: string };
  /** 与本 step 的 step_done 一致（冗余是为了文件自包含）。 */
  status: string;
  message: string | null;
  acts: EvidenceAct[];
}

// ---- 落点（ADR 0042 决策一「落哪、怎么传」）----

/** `scenario_id`（`<uri>:<行>[:<example 行>]`）→ 目录名。
 *
 *  **由 id 派生、绝不用显示名**（ADR 0042 决策一）：标题不唯一（同文件重名只靠 id 区分、`@scope` 又允许
 *  跨文件合并成一个 job），且产物目录按 run 共享、S3 key 按相对 run 目录镜像 → 同一 run 内所有 scope 共用
 *  这一命名空间。故派生必须确定性且不二次撞名：**分隔符转义 + 尾附 id 短哈希**；撞了 key 的表现是 evidence
 *  静默互相覆盖、消费端读到另一条 scenario 的 thought 且无从察觉。转义把 `/` `:` 等一律换 `_`（故 `a/b` 与
 *  `a:b` 的可读部分相同），截断亦同——两者都靠哈希兜住唯一性。
 */
export function scenarioKey(scenarioId: string): string {
  const slug = scenarioId
    .replace(/[^A-Za-z0-9._-]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, KEY_SLUG_MAX);
  const hash = crypto.createHash("sha1").update(scenarioId, "utf-8").digest("hex").slice(0, 8);
  return `${slug === "" ? "scenario" : slug}-${hash}`;
}

/** evidence.json 的落点：`<run 目录>/evidence/<scenario 键>/step-<n>/evidence.json`。
 *
 *  落在**引擎自己的产物目录**下（ADR 0042 决策一）：两引擎上传器的 S3 key 都相对各自 run 目录算，
 *  复用既有上传器（key 计算、幂等去重、scope 末整目录递归 flush）即可，不引入新的注入 env 与上传根。 */
export function evidenceFile(runDir: string, scenarioId: string, stepIndex: number): string {
  return path.join(runDir, "evidence", scenarioKey(scenarioId), `step-${stepIndex}`, "evidence.json");
}

/** SDK 落截图文件的目录（`persistExecutionDump: true` 时它每张写一个 `<id>.<扩展名>`，见文件头②）。 */
export function screenshotsDir(runDir: string): string {
  return path.join(runDir, "report", "screenshots");
}

// ---- 引擎映射（纯函数；ADR 0042 决策一映射表 Midscene 列）----

/** 截图文件扩展名。内存态的截图对象有 extension（jpeg / png）；序列化态只剩 mimeType，故按它回落——
 *  两条都对齐 SDK 自己的落盘命名规则，否则拼出的路径指向不存在的文件。 */
function extensionOf(shot: ShotLike): string {
  if (typeof shot.extension === "string" && shot.extension !== "") return shot.extension;
  return shot.mimeType === "image/png" ? "png" : "jpeg";
}

/** 本 frame 该引用哪张截图（ADR 0042 决策一映射表）：优先 recorder 里 `timing === "after-calling"` 的
 *  （动作**后**；只有每轮 plan 的末个 task 有），否则回落 `uiContext.screenshot`（动作**前**）。
 *  同一张截图会跨 task 共享（SDK 有复用缓存）→ 多个 frame 可指同一 uri，故上层按 id 去重。
 *  **只读 id 与扩展名，绝不读 `.base64`**（文件头②）。 */
function shotOf(task: TaskLike, shotsDir: string): { id: string; file: string } | null {
  const rec = (Array.isArray(task.recorder) ? task.recorder : [])
    .find((r) => r != null && r.timing === "after-calling" && r.screenshot != null);
  const shot = (rec?.screenshot ?? task.uiContext?.screenshot) as ShotLike | undefined;
  const id = shot?.id;
  if (shot == null || typeof id !== "string" || id === "") return null;
  return { id, file: path.join(shotsDir, `${id}.${extensionOf(shot)}`) };
}

/** frame.thought：真产物里 `Insight/Boolean` 带完整推理，`Planning/Plan`、`Action Space/*` 无此字段，
 *  `Planning/Locate` 带**空串**——空串等于「没有推理」，故按值判非空（否则「首个含 thought 的帧」会选中
 *  一个什么都没写的 Locate 帧）。 */
function thoughtOf(task: TaskLike): string | null {
  const own = nonEmpty(task.thought);
  if (own !== null) return own;
  // `Planning/Plan` 的推理不在 task.thought、而在 output.thought（真跑核出：Plan 的 output 形如
  // {actions, log, thought}）——不回落它，动作步的 frame 就全无推理可看（ADR 0042 决策一映射表）。
  const out = task.output;
  if (out && typeof out === "object" && !Array.isArray(out)) {
    return nonEmpty((out as { thought?: unknown }).thought);
  }
  return null;
}

/** 非空字符串才算「有推理」：空串 / 非字符串 / 缺失一律 null（按值判，ADR 0042 决策六第 1 道防线）。 */
function nonEmpty(v: unknown): string | null {
  return typeof v === "string" && v.trim() !== "" ? v : null;
}

/** frame.actions：`{name: "<type>/<subType>", args: param}`（如 `Planning/Plan`、`Action Space/Tap`）。
 *  两段都读不到 → 空数组（容缺，不造假名字）。 */
function actionsOf(task: TaskLike): Array<{ name: string; args: unknown }> {
  const name = [task.type, task.subType]
    .filter((s): s is string => typeof s === "string" && s !== "")
    .join("/");
  return name === "" ? [] : [{ name, args: task.param ?? null }];
}

/** 非空错误文本判据（按值，不按 SDK 标志）——同时是 act.error 与「出错帧」的**同一个**判据。 */
function errorTextOf(task: TaskLike): string | null {
  const m = task.errorMessage;
  return typeof m === "string" && m.trim() !== "" ? m : null;
}

/** 本 act 挑哪些 frame 配截图（ADR 0042 决策一截图策略）：
 *  - passed：末帧一张；
 *  - failed / error：末帧 + 首个含 thought 的帧 + 出错帧，按 frame 去重后取前 K。
 *  返回升序的 frame 下标（输出顺序稳定、可断言）。 */
function pickShotFrames(tasks: TaskLike[], status: string): number[] {
  if (tasks.length === 0) return [];
  const last = tasks.length - 1;
  if (status === "passed") return [last];
  const picks = [last];
  const withThought = tasks.findIndex((t) => thoughtOf(t) !== null);
  if (withThought >= 0) picks.push(withThought);
  const errored = tasks.findIndex((t) => errorTextOf(t) !== null);
  if (errored >= 0) picks.push(errored);
  return [...new Set(picks)].slice(0, MAX_SHOTS_PER_ACT).sort((a, b) => a - b);
}

export interface BuildEvidenceInput {
  scopeId: string;
  scenarioId: string;
  step: { index: number; keyword: string; text: string };
  status: string;
  message: string | null;
  /** 本 step 新增的 execution（按 step 起点的数组长度从 `agent.dump.executions` 切出）。 */
  executions: unknown[];
  /** worker 自己构造的指令串（同送给引擎的那个）；本 step 各 act 共用。 */
  prompt: string | null;
  /** 逐 act 的票；缺位 → null（非投票调用 / 该票没跑成）。 */
  votes: Array<boolean | null>;
  /** step 末取的 `page.url()`（worker 只取一次；同 step 各票之间页面通常不变）。 */
  url: string | null;
  /** 本 step 抛出的异常文本（`<name>: <message>`）；没有 → null。 */
  error: string | null;
  /** 产物落点根（= MIDSCENE_RUN_DIR），用于拼 SDK 已落盘的截图路径。 */
  runDir: string;
  /** 截图 URI：上传器「只算 ref 不上传」的方法（文件头③）。 */
  refFor: (localPath: string) => string;
}

/** executions → evidence 文档（纯函数、无 IO；SDK 耦合的全部住此）。 */
export function buildEvidence(input: BuildEvidenceInput): EvidenceDoc {
  const shotsDir = screenshotsDir(input.runDir);
  // 截图预算：按截图 id 去重后计（同一张跨 task 共享 → 复引用不再占额度），整 step 封 M 张。
  const seen = new Map<string, string>();
  const acts: EvidenceAct[] = [];

  input.executions.forEach((raw, i) => {
    const exec = (raw ?? {}) as ExecutionLike;
    const tasks = Array.isArray(exec.tasks) ? exec.tasks.map((t) => (t ?? {}) as TaskLike) : [];
    const frames: EvidenceFrame[] = tasks.map((t) => ({
      url: null,
      thought: thoughtOf(t),
      actions: actionsOf(t),
      screenshot: null,
    }));
    for (const idx of pickShotFrames(tasks, input.status)) {
      const shot = shotOf(tasks[idx], shotsDir);
      if (shot === null) continue;
      const known = seen.get(shot.id);
      if (known !== undefined) {
        frames[idx].screenshot = known;  // 同一张已被引用过：复用同一 uri、不占额度
      } else if (seen.size < MAX_SHOTS_PER_STEP) {
        const uri = input.refFor(shot.file);
        seen.set(shot.id, uri);
        frames[idx].screenshot = uri;
      }
      // 预算耗尽 → 该 frame 的 screenshot 留 null（thought / actions 照留，文本不受限）
    }
    const lastTask = tasks[tasks.length - 1];
    const isLast = i === input.executions.length - 1;
    acts.push({
      index: i,
      prompt: input.prompt,
      vote: input.votes[i] ?? null,
      url: input.url,
      frames,
      result: lastTask?.output ?? null,
      // 首个非空 errorMessage；都没有则末个 act 兜住本 step 抛出的异常（抛的那一刻正在跑的就是它）
      error: tasks.map(errorTextOf).find((m) => m !== null) ?? (isLast ? input.error : null),
      time_worked_s: null,
    });
  });

  if (acts.length === 0 && input.error !== null) {
    // 抛错早于 SDK 记下任何 execution（如指令刚发出就断连）：仍留一条只带 error 的 act，否则「本 step
    // 调了 AI 且失败了」这一事实在证据里彻底不可见。frames 为空是 SDK 事实、不是抽取失败。
    acts.push({
      index: 0, prompt: input.prompt, vote: input.votes[0] ?? null, url: input.url,
      frames: [], result: null, error: input.error, time_worked_s: null,
    });
  }

  return {
    schema_version: EVIDENCE_SCHEMA_VERSION,
    engine: ENGINE,
    scope_id: input.scopeId,
    scenario_id: input.scenarioId,
    step_index: input.step.index,
    step: { keyword: input.step.keyword, text: input.step.text },
    status: input.status,
    message: input.message,
    acts,
  };
}

// ---- 落盘 + 上传（IO；失败交上层的 best-effort 兜，见文件头④）----

/** 上传器接口 = evidence 这条链要用到的三种上传时机（ADR 0042 决策一；`ArtifactUploader` 满足之）。
 *
 *  前两个由本模块调（都在 step 判定之后的临界路径上，故一个即时传小文件、一个只算 URI）；
 *  `enqueue` **由调用方在 step_done emit 之后调**、本模块自己不碰——入队早于 emit 就把「判定先出、字节后传」
 *  的顺序反了。三者列在同一个接口里是有意的：截图的 URI 与字节是一件事的两半，分两个接口声明必漂移。 */
export interface EvidenceUploader {
  /** 即时上传并返 ref（失败抛）——evidence.json 的 ref 必须随 step_done 走，故走它。 */
  toReportRef(localPath: string): Promise<string>;
  /** 只算 ref 不上传（截图字节随后入队）。 */
  refFor(localPath: string): string;
  /** 截图字节入后台队列（同步返回、绝不抛；FIFO 顺序传、失败重试一次）。 */
  enqueue(paths: string[]): void;
}

/** runStep 的 evidence 依赖（注入；undefined = 本 run 不产 evidence）。 */
export interface EvidenceHook {
  /** 产物落点根（= MIDSCENE_RUN_DIR，已 resolve）。 */
  runDir: string;
  scopeId: string;
  uploader: EvidenceUploader;
  /** worker 诊断输出（stderr）；缺省直接写 stderr。 */
  logFn?: (msg: string) => void;
}

/** 落盘 + 即时上传，返回 ref。失败原样抛——best-effort 由 `stepEvidenceRef` 统一兜（文件头④）。 */
export async function writeEvidence(
  doc: EvidenceDoc, runDir: string, uploader: EvidenceUploader,
): Promise<string> {
  const file = evidenceFile(runDir, doc.scenario_id, doc.step_index);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(doc, null, 2), "utf-8");
  return await uploader.toReportRef(file);
}

/** `agent.dump.executions` 的当前长度（step 起点记一次，step 末据它切出本 step 新增的 execution）。
 *
 *  **不用 `addDumpUpdateListener`**（ADR 0042 决策一映射表）：同一 execution 每加一个 task 就回调一次、
 *  需去重。读不到 / 抛 → 0（容缺：最坏是把之前 step 的 execution 也算进来，而不是让 step 挂掉）。
 *  **调用点在 runStep 的 try 之外**，故这里必须自己吞异常。 */
export function executionsLength(agent: unknown): number {
  try {
    const execs = (agent as { dump?: { executions?: unknown[] } } | undefined)?.dump?.executions;
    return Array.isArray(execs) ? execs.length : 0;
  } catch {
    return 0;
  }
}

/** `stepEvidenceRef` 的产出。
 *
 *  `screenshots` = 本 step 的 evidence **真正引用到**的截图本地路径（URI 已算好写进 json、字节还没传）：
 *  调用方在 step_done emit 之后把它交给 `uploader.enqueue`（ADR 0042 决策一）。**在算 URI 的同一处收集**
 *  （见 `stepEvidenceRef` 里包装的 refFor），故「json 里引用了」与「入了队」不会因两处各挑一次而漂移。 */
export interface StepEvidence {
  ref: string;
  screenshots: string[];
}

export interface StepEvidenceInput {
  scenarioId: string;
  step: { index: number; keyword: string; text: string };
  /** 本 step 已判定的 status（与 step_done 一致）。 */
  status: string;
  message: string | null;
  /** 只读 `dump.executions`（结构类型，见文件头①）。 */
  agent: unknown;
  /** step 起点的 executions 长度（`executionsLength` 记的那个）。 */
  execFrom: number;
  /** 取调用结束时的页面 URL；取不到按 null 处理（页面可能已随异常关闭）。 */
  page: { url(): string } | undefined;
  prompt: string | null;
  votes: Array<boolean | null>;
  error: string | null;
}

/** step 判定已成之后产本 step 的 evidence，返回 ref（挂进 step_done）+ 引用到的截图路径（emit 后入队）；
 *  **绝不抛**（ADR 0042 决策二）。
 *
 *  跳过的两种情形：① 无 hook（`--no-report` 档 / 没给产物落点）；② 本 step 没调过 AI（确定性 step、
 *  URL 导航 step——既无新 execution 也无指令），这类 step 本就不产 evidence。
 *  失败 → 一行日志 + 返 null（本 step 不带 evidence ref、也不入队），判定与其余事件字段照发。 */
export async function stepEvidenceRef(
  hook: EvidenceHook | undefined, input: StepEvidenceInput,
): Promise<StepEvidence | null> {
  if (hook === undefined) return null;
  try {
    const all = (input.agent as { dump?: { executions?: unknown[] } } | undefined)?.dump?.executions;
    const executions = (Array.isArray(all) ? all : []).slice(input.execFrom);
    if (executions.length === 0 && input.prompt === null) return null;
    let url: string | null = null;
    try {
      url = input.page?.url() ?? null;
    } catch {
      url = null;  // 页面已关/CDP 断连：URL 缺了不影响其余证据
    }
    // 被引用的截图本地路径：**在算 URI 的同一处记**（refFor 只对真写进 json 的那几张调，截图预算/去重
    // 都已生效）——「引用了 ⇒ 入了队」由此成立，不必在外面照着策略再挑一遍。
    const screenshots: string[] = [];
    const doc = buildEvidence({
      scopeId: hook.scopeId,
      scenarioId: input.scenarioId,
      step: input.step,
      status: input.status,
      message: input.message,
      executions,
      prompt: input.prompt,
      votes: input.votes,
      url,
      error: input.error,
      runDir: hook.runDir,
      refFor: (p) => { screenshots.push(p); return hook.uploader.refFor(p); },
    });
    return { ref: await writeEvidence(doc, hook.runDir, hook.uploader), screenshots };
  } catch (e) {
    const logFn = hook.logFn ?? ((m: string) => process.stderr.write(m + "\n"));
    // 产品面一行：说清发生了什么 + 不影响什么 + 人能怎么办（原生报告还在）。设计判据留在本文件注释里。
    logFn(`worker: 本步的排障证据没能产出（已忽略，不影响本步判定结果；仍可看引擎原生报告）：${(e as Error).message}`);
    return null;
  }
}
