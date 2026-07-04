// 产物 S3 上传（Midscene worker，ADR 0029 第一期）：整目录上传 → 删本地 → reportRef 报 s3://。
//
// 由组合根注入的 S3 落点 env 驱动（ARTIFACT_S3_BUCKET + ARTIFACT_S3_PREFIX，跟 --backend cloud 走）——
// 未注入（local / --no-report）→ toReportRef 原样报 file://、不上传、不删（零行为变化）。worker 对"我在哪跑"
// 无知，只认这组 env 有没有（ADR 0016 注入红线）。与 Nova 的 lib/artifact_upload.py 对称（各语言各写，ADR 0024）。
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
    await this.client_().send(new PutObjectCommand({
      Bucket: this.bucket!, Key: this.keyFor(abs), Body: body,
      ContentType: abs.endsWith(".html") ? "text/html; charset=utf-8" : undefined,
    }));
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
