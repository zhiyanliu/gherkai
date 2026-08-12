// job 入口（Midscene worker，ADR 0024「I/O 边缘可注入接口」）：worker 主流程唯一的 job 读入口。
//
// 对称 Nova 的 lib/job_source.py（各语言各写、语义契约对称，ADR 0024）+ 对称本引擎 ArtifactUploader 结构骨架
// （fromEnv 唯一读 env、退化态是同类实例、外部 client 惰性建）。
//
// read() 返回**已解析的 job 对象**（非流/句柄）——否则「从哪读」漏进 worker 主流程，S3/stdin 两态就无法对
// 主流程同形。read 为 async（stdin 聚合本就 async + S3 态的 GetObject 也 async）。
// subprocess 态：读整个 stdin 到 EOF 再切首行 JSON（core 侧 job_to_line 写单行 + \n，ADR 0024）。
//
// 两态（ADR 0024）：subprocess 态读 stdin 首行 JSON；S3 态（JOB_S3_URI 指针 + GetObject，因 RunTask overrides
// 8192 上限塞不下含 feature 的 job）Fargate 化用。判据=有没有注入 JOB_S3_URI，非「是否 Fargate」（ADR 0016 红线）。
// **无「回落调试」分支**：stdin 本就是手动直跑入口，subprocess 态即调试态。
import { S3Client, GetObjectCommand } from "@aws-sdk/client-s3";

interface Job { scope: { id: string; name: string }; engine: string; scenarios: unknown[]; assertionVotes?: number }

export class JobSource {
  private uri: string | undefined;

  private constructor(uri: string | undefined) {
    // 私有构造只吃已解析值（对称 ArtifactUploader）：uri 为 undefined = subprocess 态（读 stdin）。
    this.uri = uri;
  }

  // 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 有 → S3 态（GetObject）；无 → stdin 态。
  static fromEnv(): JobSource {
    return new JobSource(process.env.JOB_S3_URI || undefined);
  }

  // 读并解析一个 job（返回对象，非流）。subprocess 态：读 stdin 到 EOF、切首行 JSON。
  // S3 态（Fargate 化）：JOB_S3_URI=s3://bucket/key → GetObject + 解析首行 JSON。不静默走 stdin（否则 Fargate
  // 无 stdin、会挂在 for await 上；判 uri 分流、fail-loud，对称 Nova）。
  // client 可注入（测试塞 fake、绕真 aws-sdk——对称 artifact-upload.test 的 mock 惯例）；不注入则生产内部 new。
  async read(client?: { send: (cmd: any, opts?: any) => Promise<any> }): Promise<Job> {
    if (this.uri !== undefined) return JobSource.readS3(this.uri, client);
    const chunks: Buffer[] = [];
    for await (const c of process.stdin) chunks.push(c as Buffer);
    return JSON.parse(Buffer.concat(chunks).toString("utf-8").split("\n")[0]);
  }

  // s3://bucket/key → GetObject → 首行 JSON。用已有 @aws-sdk/client-s3（对称 ArtifactUploader）。
  private static async readS3(uri: string, client?: { send: (cmd: any, opts?: any) => Promise<any> }): Promise<Job> {
    if (!uri.startsWith("s3://")) throw new Error(`JobSource: JOB_S3_URI 须为 s3:// URI，得到 ${uri}`);
    const rest = uri.slice("s3://".length);
    const slash = rest.indexOf("/");
    const bucket = rest.slice(0, slash);
    const key = rest.slice(slash + 1);
    const s3 = client ?? new S3Client({ region: process.env.AWS_REGION });
    const resp = await s3.send(new GetObjectCommand({ Bucket: bucket, Key: key }),
      { abortSignal: AbortSignal.timeout(10_000) });
    const text = await resp.Body!.transformToString("utf-8");
    return JSON.parse(text.split("\n")[0]);  // job 是单行 JSON（core job_to_line + \n）
  }
}
