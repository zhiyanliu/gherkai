// 产物 S3 上传（Midscene worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。
//
// 由组合根注入的 S3 落点 env 驱动（ARTIFACT_S3_BUCKET + ARTIFACT_S3_PREFIX，跟 --backend cloud 走）——
// **未注入落点（local 路径；或手动直跑/脚手架没给这组 env）→ toReportRef 原样报 file://、不上传、不删**（零行为变化；
// 与 --no-report 正交——那管要不要渲染报告，不管产物上传落点）。worker 对"我在哪跑"无知，只认这组 env 有没有
// （ADR 0016 注入红线）。与 Nova 的 lib/artifact_upload.py 对称（各语言各写，ADR 0024）。
//
// S3 key 镜像本地 run 树（ADR 0029）：任一产物 key = <prefix><产物相对本地 run 目录的路径>，与 S3ReportStore/
// ResultStore 同 <prefix> 前缀。本地 run 目录 = 产物落点目录（MIDSCENE_RUN_DIR）的父级。key 确定性纯路径计算、
// 不依赖上传，故 toReportRef 可先算 s3:// ref 实时报出。
//
// 上传/删除策略（ADR 0029 混合两级 + 整目录，抗 SDK 升级）：
// - toReportRef(path)：reportRef 文件 → 实时上传（不删、记 uploaded）、报 s3://。失败抛（worker 可观测、
//   engine_error）——报告链接强保证。
// - flushAndCleanup(dir)：scope 末调。递归 walk 整个产物目录上传剩余文件（已实时传的跳过）——不按文件类型/名字挑
//   （整目录一股脑传，本地清理不损耗任何产物、不受 SDK 升级影响）。剩余上传失败吞掉；全部成功（实时+剩余）才
//   rmSync 整目录（本地零残留）；任一失败则整目录保留不删（产物不丢）。
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
import * as fs from "node:fs";
import * as path from "node:path";

// 单次 S3 上传超时（ADR 0029「上传必须套超时」）：远大于正常同区上传（亚秒~秒级）、且明显 < grace（worker
// 优雅停宽限，ADR 0024）——退化网络下上传挂到此即 abort、best-effort 放弃，不拖住退出。**grace 是 run 级、随
// 引擎组成变**：混引擎 run 取各引擎下限的 max（Nova 下限最大），midscene-only run 由组合根
// engine_min_grace("midscene")=MIDSCENE_GRACE_MIN_S 保证 > 本超时——**那两个下限的真值住 gherkai/gherkai/compose.py，
// 此处不复述数字**（曾漏设 midscene 下限 → 回落 ScheduleOpts 默认 grace < 本超时、致 worker 被 SIGKILL）。
const UPLOAD_TIMEOUT_MS = 10_000;

export class ArtifactUploader {
  private bucket: string | undefined;
  private prefix: string;
  private runDir: string | undefined; // 本地 run 树根（= MIDSCENE_RUN_DIR 父级），算相对 key 用
  private client: S3Client | undefined; // 惰性建（仅真上传时）
  private uploaded = new Set<string>(); // 已实时上传的绝对路径（flush 时跳过）
  private flushOk = true;               // 剩余批量是否全成功（任一失败 → 整目录不删）

  private constructor(bucket: string | undefined, prefix: string, runDir: string | undefined) {
    this.bucket = bucket;
    this.prefix = prefix;
    this.runDir = runDir;
  }

  // 从组合根注入的 env 造。无 ARTIFACT_S3_BUCKET → no-op uploader（报 file://）。
  static fromEnv(): ArtifactUploader {
    const bucket = process.env.ARTIFACT_S3_BUCKET || undefined;
    const prefix = process.env.ARTIFACT_S3_PREFIX ?? "";
    const runRoot = process.env.MIDSCENE_RUN_DIR;
    const runDir = runRoot ? path.dirname(path.resolve(runRoot)) : undefined;
    if (bucket !== undefined && runDir === undefined) {
      // fail-loud（对称 Nova artifact_upload.py）：注入了桶却没给 MIDSCENE_RUN_DIR = 组合根配置矛盾，
      // 静默 no-op 会让产物报 file:// 且随容器盘销毁必丢（ADR 0033「只注①不注②等于没上传」）。
      throw new Error(
        "ArtifactUploader：ARTIFACT_S3_BUCKET 已注入但缺 MIDSCENE_RUN_DIR（runDir 推不出）——组合根装配错误（ADR 0033）");
    }
    return new ArtifactUploader(bucket, prefix, runDir);
  }

  // 是否上传（注入了桶 + 有 runDir 算相对 key）。否则 no-op 报 file://。
  get enabled(): boolean {
    return this.bucket !== undefined && this.runDir !== undefined;
  }

  private keyFor(localAbs: string): string {
    // 产物本地绝对路径 → S3 key（镜像 run 树：prefix + 相对 runDir 的 POSIX 路径）。
    const rel = path.relative(this.runDir!, path.resolve(localAbs));
    return `${this.prefix}${rel.split(path.sep).join("/")}`; // POSIX 分隔符（S3 key / URL 友好）
  }

  private client_(): S3Client {
    if (!this.client) this.client = new S3Client({ region: process.env.AWS_REGION });
    return this.client;
  }

  private async uploadOne(abs: string): Promise<void> {
    const body = fs.readFileSync(abs);
    // 套超时（ADR 0029「上传必须套超时」/ 退出时间有界护栏）：aws-sdk-js v3 默认无 request/socket 超时
    // （近乎无限），退化网络下 PutObject 会挂起、拖住 worker 退出（尤其 SIGTERM handler 内兜底抢传）→ 等
    // grace 耗尽被 SIGKILL 强杀 → 跳过会话清理 → 泄漏。用 Node 原生 AbortSignal.timeout（零依赖）硬性封顶：
    // 超时自动 abort 底层请求（比 Promise.race 更干净——race 只是不等、请求仍挂）。UPLOAD_TIMEOUT_MS « grace。
    await this.client_().send(
      new PutObjectCommand({
        Bucket: this.bucket!, Key: this.keyFor(abs), Body: body,
        ContentType: abs.endsWith(".html") ? "text/html; charset=utf-8" : undefined,
      }),
      { abortSignal: AbortSignal.timeout(UPLOAD_TIMEOUT_MS) },
    );
  }

  // reportRef 文件 → 实时上传（不删、记 uploaded）、报 s3://；no-op 时报 file://。
  // 失败原样抛（worker 记 engine_error、可观测）——报告链接强保证，不吞。no-op 裸拼 file://（与 Nova 对称、保旧行为）。
  async toReportRef(localPath: string): Promise<string> {
    if (!this.enabled) return `file://${localPath}`;
    const abs = path.resolve(localPath);
    // 幂等短路（对称 Nova）：已成功传过 → 直接返 s3:// ref、不重传（key 确定性可算）。防同一文件被多次引用时冗余 PutObject。
    if (this.uploaded.has(abs)) return `s3://${this.bucket}/${this.keyFor(abs)}`;
    await this.uploadOne(abs);            // 实时上传（失败抛 → 可观测、不删）
    this.uploaded.add(abs);               // 记下，flush 时跳过
    return `s3://${this.bucket}/${this.keyFor(abs)}`;
  }

  // act 边界抢传单文件快照（ADR 0029「act 边界抢传」，为 Fargate 预演）：供 worker 在每个 step_done 安全点
  // 反复抢传**增量增长的单份 report.html**（Midscene report 边跑边 append，中断落 destroy 前会整份丢）。
  // 与 toReportRef 三点区别（Midscene 单引擎增补、Nova 无需——见 ADR 0029 uploader 接口条）：
  //   ① **绕 uploaded 幂等守卫**：每次都真传（同 keyFor → S3 同 key overwrite），overwrite-latest 最新即最全；
  //   ② **不记 uploaded**：故 scope 末 toReportRef(reportFile) 仍传 destroy 后 finalize 的权威完整版、
  //      flushAndCleanup 仍按 uploaded 正确跳过——快照只是中途保险，不篡改两级上传账本；
  //   ③ **失败原样抛**（保 lib 纯净）——交调用方（worker）吞+log：抢传是 best-effort、不该打断 step 循环
  //      （对照 toReportRef 失败抛=报告链接强保证，语义相反）。
  // no-op（未注入落点）→ 直接返回，不碰盘、不产 ref（抢传不面向事件消费者，只求字节进 S3）。
  // **绝不复用 flushAndCleanup**：那个成功后 rmSync 删整目录，会误删正被 SDK 增量 append 的 report、打断在跑的 main。
  async snapshotReport(localPath: string): Promise<void> {
    if (!this.enabled) return;
    await this.uploadOne(path.resolve(localPath));  // 同 keyFor → overwrite；不查/不加 uploaded
  }

  // scenario 边界抢传诊断 log（ADR 0029「第四级：scenario 边界抢传」，Midscene 单引擎、为 Fargate 预演）：
  // 供 worker 在每个 scenario_done 安全点抢传该 scenario 期间**已在盘、尚未传**的 log/*.log——把 log 丢失窗口
  // 从「整个 run」收窄到「当前正在跑的 scenario」。log 边跑边 createWriteStream append 写（`<MIDSCENE_RUN_DIR>/log/`），
  // scenario 边界截至已完成 scenario 的字节已在盘、可抢。承 snapshotReport 的「绕 uploaded 幂等守卫 + 不记 uploaded」
  // （overwrite 同 key、让 scope 末 flush 仍传权威版并删本地），但**失败语义随多文件本质取 flushAndCleanup 那套**：
  // 逐文件 try/吞、继续下一个（非 snapshotReport 单文件的整体抛）——否则第一个失败的 log 会饿死本边界后续 log。
  // **绝不复用 flushAndCleanup**（那个 rmSync 删整目录、会误删在写的 report/log 流）。
  // **两条硬约束（退化网络护栏，ADR 0029）**：
  //   ① per-file mtime 去重：`seen`（absPath→mtimeMs，调用方持 scope 级）——log 单调增长，只传本 scenario 内真
  //      变过的 topic 文件，不重发未变 log（否则每边界把全部累积 log 重传、冗余随 run 线性涨）。传成功才记 seen
  //      （失败不记 → 下轮/scope 末 flush 重试）。
  //   ② 整次快照套总墙钟预算 `budgetMs`：单文件已被 uploadOne 的 AbortSignal.timeout 封顶，但 N 个 log 串行累加
  //      最坏 N×单文件超时、再 × scenario 数会拖垮 grace/延迟下一 scenario——超预算即停、放弃剩余（best-effort，
  //      scope 末 flush 兜底）。**budgetMs 是「不再发起新上传」的软界、非硬墙钟**：deadline 只在循环顶查，一个
  //      已通过检查、正在途的 uploadOne 仍会跑满其 AbortSignal.timeout，故实际墙钟上界 ≈ budgetMs + 单文件超时。
  // 两个已知的可接受局限（均有 scope 末 flush 兜底、无数据丢失，故不特治）：
  //   · **非递归 + 只传文件**：假定 SDK 把 log 平铺为 `log/*.log`（当前如此）；若未来 SDK 在 log/ 下建子目录，
  //     嵌套 log 在此被漏，靠 scope 末 flushAndCleanup（recursive）兜底传。
  //   · **永久失败的 log 每 scenario 边界都重试**：失败不记 seen（见下），若某 log 持续失败（非法 key/持续超时）
  //     则每边界重试它、浪费预算；但这是为 transient 失败重试的有意取舍（ADR 0028 主题），且 scope 末 flush 兜底。
  // no-op（未注入落点）→ 直接返回。log 目录不存在（还没产 log）→ 直接返回。
  async snapshotLogs(logDir: string, seen: Map<string, number>, budgetMs: number): Promise<void> {
    if (!this.enabled) return;
    if (!fs.existsSync(logDir)) return;
    const deadline = Date.now() + budgetMs;  // 总墙钟软界（worker 生产代码，Date.now 可用）；见 docstring②
    for (const ent of fs.readdirSync(logDir, { withFileTypes: true })) {  // 非递归：假定 log 平铺，见 docstring
      if (Date.now() >= deadline) break;  // 超预算 → 不再发起新上传（软界；在途的仍跑满自身超时）
      if (!ent.isFile()) continue;
      const abs = path.resolve(logDir, ent.name);
      let mt: number;
      try { mt = fs.statSync(abs).mtimeMs; } catch { continue; }  // stat 失败（文件正被删/换）→ 跳过
      if (seen.get(abs) === mt) continue;  // mtime 未变 → 去重跳过（不重发未变 log）
      try {
        await this.uploadOne(abs);  // overwrite 同 key（绕 uploaded、不记账）
        seen.set(abs, mt);          // 传成功才记（失败不记 → 下轮/scope 末 flush 重试）
      } catch {
        // 逐文件吞（对齐 flushAndCleanup 多文件语义）：某 log 传失败不该饿死本边界其余 log；不记 seen → 后续重试。
      }
    }
  }

  // scope 末：整目录递归上传剩余文件（跳过已实时传的）+ 全成功则 rmSync 整目录（ADR 0029）。
  // no-op → 直接返回（不碰本地）。剩余上传失败吞掉（报告链接不依赖它），但置 flushOk=false → 整目录不删。
  // 不按文件类型/名字挑——walk 整个目录、一股脑传，抗引擎 SDK 升级。
  async flushAndCleanup(artifactDir: string): Promise<void> {
    if (!this.enabled) return;
    if (!fs.existsSync(artifactDir)) return;
    const entries = fs.readdirSync(artifactDir, { recursive: true, withFileTypes: true }) as fs.Dirent[];
    for (const ent of entries) {
      if (!ent.isFile()) continue;
      // Node 的 recursive Dirent.parentPath（>=20）给出所在目录；拼回绝对路径
      const abs = path.resolve((ent as any).parentPath ?? (ent as any).path ?? artifactDir, ent.name);
      if (this.uploaded.has(abs)) continue; // reportRef 文件已实时传，跳过
      try {
        await this.uploadOne(abs);
      } catch {
        this.flushOk = false; // 剩余上传失败：吞掉（报告链接不依赖它），但标记 → 整目录不删
      }
    }
    if (this.flushOk) fs.rmSync(artifactDir, { recursive: true, force: true }); // 全成功 → 删整目录
  }
}
