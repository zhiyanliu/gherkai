// job 入口（Midscene worker，ADR 0024「I/O 边缘可注入接口」第一期）：worker 主流程唯一的 job 读入口。
//
// 对称 Nova 的 lib/job_source.py（各语言各写、语义契约对称，ADR 0024）+ 对称本腿 ArtifactUploader 结构骨架
// （fromEnv 唯一读 env、退化态是同类实例、外部 client 惰性建）。
//
// read() 返回**已解析的 job 对象**（非流/句柄）——否则「从哪读」漏进 worker 主流程，S3/stdin 两态就无法对
// 主流程同形。read 为 async（stdin 聚合本就 async + WP-Fargate 的 S3 GetObject 也 async）。
// subprocess 态：读整个 stdin 到 EOF 再切首行 JSON（core 侧 job_to_line 写单行 + \n，ADR 0024）。
//
// 第一期只实现 subprocess 态（读 stdin）；S3 态（JOB_S3_URI 指针 + GetObject，因 RunTask overrides 8192 上限
// 塞不下含 feature 的 job）属 WP-Fargate、本组件形状须能容纳但不实现（判据=有没有注入 JOB_S3_URI，非「是否
// Fargate」）。**无「回落调试」分支**：stdin 本就是手动直跑入口，subprocess 态即调试态。

interface Job { scope: { id: string; name: string }; engine: string; scenarios: unknown[]; assertionVotes?: number }

export class JobSource {
  private uri: string | undefined;

  private constructor(uri: string | undefined) {
    // 私有构造只吃已解析值（对称 ArtifactUploader）：uri 为 undefined = subprocess 态（读 stdin）。
    this.uri = uri;
  }

  // 从注入的 env 造（唯一读 env 处）。JOB_S3_URI 有 → S3 态（WP-Fargate，未实现）；无 → stdin 态。
  static fromEnv(): JobSource {
    return new JobSource(process.env.JOB_S3_URI || undefined);
  }

  // 读并解析一个 job（返回对象，非流）。subprocess 态：读 stdin 到 EOF、切首行 JSON。
  async read(): Promise<Job> {
    // S3 态（Fargate 化，未实现）：注入了 JOB_S3_URI 却跑到这 = 配置错，显式报错、不静默走 stdin（否则
    // Fargate 无 stdin、会挂在 for await 上）。实现时：惰性建 aws-sdk client + GetObject(this.uri) + parse。
    if (this.uri !== undefined) throw new Error(`JobSource: S3 态未实现（JOB_S3_URI=${this.uri}）——属 Fargate 化`);
    // subprocess 态：读 stdin 到 EOF、切首行 JSON。
    const chunks: Buffer[] = [];
    for await (const c of process.stdin) chunks.push(c as Buffer);
    return JSON.parse(Buffer.concat(chunks).toString("utf-8").split("\n")[0]);
  }
}
