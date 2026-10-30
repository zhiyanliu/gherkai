// 设备模块的读取点与依赖位置护栏（ADR 0052 决策 1、3、4、8；ADR 0051 决策 10）。运行：npx tsx --test src/device/read-points.test.mts。
//
// 用 TypeScript 编译器的语法树扫 src/ 下全部非测试源文件（测试文件不在扫描范围内），四条差集：
//   1. `mobile:` 命令字面量只出现在 device/adapters/ 下（决策 4）：看字符串、模板与正则字面量，注释不算；
//   2. Device Farm 客户端只在 device/session.mts 构造（决策 3）：`new DeviceFarmClient(...)` 与这个类的值导入都只在那里；
//   3. WebdriverIO（含它的 webdriver 与 @wdio/ 下的包）与 Device Farm SDK 的值导入只在 device/ 下（决策 3「设备模块动态加载」）：
//      静态 import、re-export、动态 import() 与 require 都算；`import type`、只含类型说明符的 import 与 `export type` 豁免，
//      它们在编译期擦除、运行期不加载（决策 8）；
//   4. 系统版本与机型字段只出现在读取点与显式豁免的文件里（决策 1、8）。读取点是 Appium 块的会话能力对象；豁免是不构成按版本或
//      机型适配分支的三类：设备选择的输入、协议载荷、句柄上下文的透传。决定适配行为的四块（驱动适配器、能力探测、界面实现、
//      命令守卫）不在豁免里，一处出现即红。不扫数字字面量：坐标、超时与比例里的数字与版本号无法区分（被拒方案）。
// 每条都带正向对照：检测函数先在构造的源码片段上命中，真实文件里已知的出现也必须被检测到，防止检测失效时差集空过。
import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import ts from "typescript";

const SRC = path.resolve(import.meta.dirname, "..");

/** src/ 下全部非测试的 .mts 源文件，路径相对 src、以 / 分隔。 */
function sourceFiles(): string[] {
  const out: string[] = [];
  const walk = (dir: string): void => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (entry.name.endsWith(".mts") && !entry.name.endsWith(".test.mts")) out.push(path.relative(SRC, full).split(path.sep).join("/"));
    }
  };
  walk(SRC);
  return out.sort();
}

function parse(fileName: string, text: string): ts.SourceFile {
  return ts.createSourceFile(fileName, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
}

function readSource(rel: string): ts.SourceFile {
  return parse(rel, fs.readFileSync(path.join(SRC, rel), "utf-8"));
}

function visit(node: ts.Node, fn: (n: ts.Node) => void): void {
  fn(node);
  ts.forEachChild(node, (child) => visit(child, fn));
}

function lineOf(sf: ts.SourceFile, node: ts.Node): number {
  return sf.getLineAndCharacterOfPosition(node.getStart(sf)).line + 1;
}

interface Hit { line: number; what: string }

// ---- 1. mobile: 字面量 ----

const MOBILE_COMMAND = /mobile:/;

function mobileLiterals(sf: ts.SourceFile): Hit[] {
  const hits: Hit[] = [];
  visit(sf, (n) => {
    if (ts.isStringLiteralLike(n) || ts.isTemplateLiteralToken(n) || ts.isRegularExpressionLiteral(n)) {
      if (MOBILE_COMMAND.test(n.text)) hits.push({ line: lineOf(sf, n), what: n.text });
    }
  });
  return hits;
}

// ---- 2 与 3. 设备 SDK 的值导入与 Device Farm 客户端的构造 ----

const DEVICE_FARM_SDK = "@aws-sdk/client-device-farm";

function isDeviceSdk(specifier: string): boolean {
  const pkg = specifier.startsWith("@") ? specifier.split("/").slice(0, 2).join("/") : specifier.split("/")[0];
  return pkg === "webdriverio" || pkg === "webdriver" || pkg.startsWith("@wdio/") || pkg === DEVICE_FARM_SDK;
}

/** import 声明是否只引入类型（`import type`，或每个说明符都带 type 且没有缺省导入）。 */
function importIsTypeOnly(node: ts.ImportDeclaration): boolean {
  const clause = node.importClause;
  if (clause === undefined) return false;  // 只为副作用的 import 会在运行期加载
  if (clause.phaseModifier === ts.SyntaxKind.TypeKeyword) return true;
  if (clause.name !== undefined) return false;
  const bindings = clause.namedBindings;
  return bindings !== undefined && ts.isNamedImports(bindings) && bindings.elements.length > 0 && bindings.elements.every((e) => e.isTypeOnly);
}

function exportIsTypeOnly(node: ts.ExportDeclaration): boolean {
  if (node.isTypeOnly) return true;
  const clause = node.exportClause;
  return clause !== undefined && ts.isNamedExports(clause) && clause.elements.length > 0 && clause.elements.every((e) => e.isTypeOnly);
}

/** 运行期会加载设备 SDK 的 import / re-export / 动态 import() / require。 */
function deviceSdkValueImports(sf: ts.SourceFile): Hit[] {
  const hits: Hit[] = [];
  visit(sf, (n) => {
    if (ts.isImportDeclaration(n) && ts.isStringLiteral(n.moduleSpecifier)) {
      if (isDeviceSdk(n.moduleSpecifier.text) && !importIsTypeOnly(n)) hits.push({ line: lineOf(sf, n), what: n.moduleSpecifier.text });
    } else if (ts.isExportDeclaration(n) && n.moduleSpecifier !== undefined && ts.isStringLiteral(n.moduleSpecifier)) {
      if (isDeviceSdk(n.moduleSpecifier.text) && !exportIsTypeOnly(n)) hits.push({ line: lineOf(sf, n), what: n.moduleSpecifier.text });
    } else if (ts.isImportEqualsDeclaration(n) && ts.isExternalModuleReference(n.moduleReference)) {
      const expr = n.moduleReference.expression;
      if (ts.isStringLiteral(expr) && isDeviceSdk(expr.text) && !n.isTypeOnly) hits.push({ line: lineOf(sf, n), what: expr.text });
    } else if (ts.isCallExpression(n) && n.arguments.length > 0) {
      const callee = n.expression;
      const dynamic = callee.kind === ts.SyntaxKind.ImportKeyword || (ts.isIdentifier(callee) && callee.text === "require");
      const arg = n.arguments[0];
      if (dynamic && ts.isStringLiteralLike(arg) && isDeviceSdk(arg.text)) hits.push({ line: lineOf(sf, n), what: arg.text });
    }
  });
  return hits;
}

const DEVICE_FARM_CLIENT = "DeviceFarmClient";

/** `new DeviceFarmClient(...)`（含经命名空间的写法）与这个类的值导入（含改名导入）。 */
function deviceFarmClientSites(sf: ts.SourceFile): Hit[] {
  const hits: Hit[] = [];
  visit(sf, (n) => {
    if (ts.isNewExpression(n)) {
      const callee = n.expression;
      const name = ts.isIdentifier(callee) ? callee.text : ts.isPropertyAccessExpression(callee) ? callee.name.text : "";
      if (name === DEVICE_FARM_CLIENT) hits.push({ line: lineOf(sf, n), what: "new DeviceFarmClient" });
    } else if (ts.isImportSpecifier(n) && !n.isTypeOnly) {
      const decl = n.parent.parent.parent as ts.ImportDeclaration;
      const imported = (n.propertyName ?? n.name).text;
      if (imported === DEVICE_FARM_CLIENT && !importIsTypeOnly(decl)) hits.push({ line: lineOf(sf, n), what: `import ${imported}` });
    }
  });
  return hits;
}

// ---- 4. 系统版本与机型字段 ----

// 系统版本与机型的字段名：会话能力对象（platformVersion、deviceName、deviceModel，含 appium: 前缀形态）、Device Farm 设备描述
// （os、model、modelId）与本包协议载荷（osVersion）。只认作属性名、对象键、解构键与整串字面量的出现，不认普通变量名
// （`import * as os from "node:os"` 的 os 是变量，不是字段）。
const VERSION_MODEL_FIELDS = new Set(["platformVersion", "osVersion", "os", "model", "modelId", "deviceModel", "deviceName"]);

function fieldName(text: string): string | null {
  const bare = text.startsWith("appium:") ? text.slice("appium:".length) : text;
  return VERSION_MODEL_FIELDS.has(bare) ? bare : null;
}

function propertyNameText(name: ts.PropertyName | ts.BindingName | undefined): string | null {
  if (name === undefined) return null;
  if (ts.isIdentifier(name) || ts.isStringLiteralLike(name) || ts.isPrivateIdentifier(name)) return name.text;
  return null;
}

function versionModelMentions(sf: ts.SourceFile): Hit[] {
  const hits: Hit[] = [];
  const add = (n: ts.Node, text: string | null): void => {
    const field = text === null ? null : fieldName(text);
    if (field !== null) hits.push({ line: lineOf(sf, n), what: field });
  };
  visit(sf, (n) => {
    if (ts.isPropertyAccessExpression(n)) add(n, n.name.text);
    else if (ts.isElementAccessExpression(n) && ts.isStringLiteralLike(n.argumentExpression)) add(n, n.argumentExpression.text);
    else if (ts.isPropertySignature(n) || ts.isPropertyDeclaration(n) || ts.isPropertyAssignment(n) || ts.isMethodDeclaration(n)
      || ts.isMethodSignature(n) || ts.isGetAccessorDeclaration(n)) add(n, propertyNameText(n.name));
    else if (ts.isShorthandPropertyAssignment(n)) add(n, n.name.text);
    else if (ts.isBindingElement(n) && ts.isObjectBindingPattern(n.parent)) add(n, propertyNameText(n.propertyName ?? n.name));
    else if (ts.isStringLiteralLike(n) && !isKeyOfParent(n)) add(n, n.text);
  });
  return hits;
}

/** 字面量是否已作为属性名、下标或解构键被上面的分支计过（避免同一处计两次）。 */
function isKeyOfParent(n: ts.Node): boolean {
  const p = n.parent as ts.Node & { name?: ts.Node; propertyName?: ts.Node };
  return (ts.isElementAccessExpression(p) && p.argumentExpression === n) || p.name === n || p.propertyName === n;
}

/** 允许出现系统版本与机型字段的文件与理由（ADR 0052 决策 8 的读取点与三类豁免）。 */
const VERSION_MODEL_ALLOWED: ReadonlyMap<string, string> = new Map([
  ["device/appium.mts", "读取点：会话能力对象只在 Appium 块读取，读出的值只交给诊断与句柄上下文"],
  ["device/session.mts", "设备选择的输入：按设备列举结果的系统版本与机型筛选设备，并写进 session_opened.device"],
  ["device/device-session.mts", "协议载荷：session_opened 的 device 字段与 device-session.json"],
  ["lib/job-source.mts", "协议载荷：Job 设备请求里的 osVersion"],
  ["worker/deterministic.mts", "句柄上下文的类型透传：注册面对 webdriver 句柄 ctx.device 的类型声明"],
  ["device/surface.mts", "编排：端口类型声明、句柄上下文的值透传（ctx.device.osVersion）与就绪日志里的会话描述（session_opened.device 同一份载荷）"],
]);

/** 决定适配行为的四块（ADR 0052 决策 8）：它们不得进入上面的允许清单。 */
function isBehaviorModule(rel: string): boolean {
  return rel.startsWith("device/adapters/") || ["device/probe.mts", "device/interface.mts", "device/guard.mts"].includes(rel);
}

// ---- 正向对照 ----

test("检测函数在构造的片段上命中：mobile: 字面量", () => {
  const sf = parse("x.mts", [
    "// 注释里的 mobile: tap 不算",
    "/* mobile: swipe */",
    "const a = \"mobile: tap\";",
    "const b = `mobile: ${name}`;",
    "const c = /^mobile:/;",
    "const d = { mobile: true };",
    "call('mobile: deepLink', {});",
  ].join("\n"));
  assert.deepEqual(mobileLiterals(sf).map((h) => h.line), [3, 4, 5, 7]);
});

test("检测函数在构造的片段上命中：设备 SDK 的值导入，类型导入豁免", () => {
  const sf = parse("x.mts", [
    "import type { Browser } from \"webdriverio\";",
    "import { type Browser as B } from \"webdriverio\";",
    "import { remote } from \"webdriverio\";",
    "import \"webdriver\";",
    "import logger from \"@wdio/logger\";",
    "import { DeviceFarmClient } from \"@aws-sdk/client-device-farm\";",
    "export { attach } from \"webdriverio\";",
    "export type { Capabilities } from \"@wdio/types\";",
    "const m = await import(\"@aws-sdk/client-device-farm\");",
    "const r = require(\"webdriverio/build/node\");",
    "import { S3Client } from \"@aws-sdk/client-s3\";",
    "import { Agent } from \"@midscene/core/agent\";",
  ].join("\n"));
  assert.deepEqual(deviceSdkValueImports(sf).map((h) => h.line), [3, 4, 5, 6, 7, 9, 10]);
});

test("检测函数在构造的片段上命中：Device Farm 客户端的构造与值导入", () => {
  const sf = parse("x.mts", [
    "import type { DeviceFarmClient as T } from \"@aws-sdk/client-device-farm\";",
    "import { DeviceFarmClient as DF, ListDevicesCommand } from \"@aws-sdk/client-device-farm\";",
    "import * as sdk from \"@aws-sdk/client-device-farm\";",
    "const a = new sdk.DeviceFarmClient({});",
    "const b = new DeviceFarmClient({ region: \"us-west-2\" });",
    "const c = new ListDevicesCommand({});",
  ].join("\n"));
  assert.deepEqual(deviceFarmClientSites(sf).map((h) => h.line), [2, 4, 5]);
});

test("检测函数在构造的片段上命中：系统版本与机型字段，普通变量名不算", () => {
  const sf = parse("x.mts", [
    "import * as os from \"node:os\";",
    "const dir = os.tmpdir();",
    "const v = caps.platformVersion;",
    "const n = caps[\"appium:deviceName\"];",
    "interface D { osVersion: string }",
    "const p = { model: m };",
    "const { modelId } = device;",
    "const k = [\"os\"];",
    "if (device.os.startsWith(\"17\")) {}",
    "const platformVersion = 1;",
    "const ok = caps.platformName;",
  ].join("\n"));
  assert.deepEqual(versionModelMentions(sf).map((h) => [h.line, h.what]), [
    [3, "platformVersion"], [4, "deviceName"], [5, "osVersion"], [6, "model"], [7, "modelId"], [8, "os"], [9, "os"],
  ]);
});

// ---- 真实文件 ----

function scan(detect: (sf: ts.SourceFile) => Hit[]): Map<string, Hit[]> {
  const found = new Map<string, Hit[]>();
  for (const rel of sourceFiles()) {
    const hits = detect(readSource(rel));
    if (hits.length > 0) found.set(rel, hits);
  }
  return found;
}

function describeHits(found: Map<string, Hit[]>, files: string[]): string {
  return files.map((f) => `${f}: ${found.get(f)!.map((h) => `${h.line} 行 ${JSON.stringify(h.what)}`).join("，")}`).join("\n");
}

test("扫描面：src/ 下的源文件都被扫到，测试文件不在其中", () => {
  const files = sourceFiles();
  for (const known of ["bin.mts", "worker/run-scope.mts", "device/surface.mts", "device/interface.mts", "device/adapters/xcuitest.mts"]) {
    assert.ok(files.includes(known), `扫描面缺少 ${known}`);
  }
  assert.ok(files.every((f) => !f.endsWith(".test.mts")));
});

test("mobile: 命令字面量只出现在 device/adapters/ 下", () => {
  const found = scan(mobileLiterals);
  const outside = [...found.keys()].filter((f) => !f.startsWith("device/adapters/"));
  assert.deepEqual(outside, [], `适配器之外出现了 mobile: 命令（应改为调用适配器导出的函数或集合）：\n${describeHits(found, outside)}`);
  for (const adapter of ["device/adapters/uiautomator2.mts", "device/adapters/xcuitest.mts"]) {
    assert.ok(found.has(adapter), `正向对照：${adapter} 里应检测到 mobile: 命令`);
  }
});

test("Device Farm 客户端只在 device/session.mts 构造", () => {
  const found = scan(deviceFarmClientSites);
  const outside = [...found.keys()].filter((f) => f !== "device/session.mts");
  assert.deepEqual(outside, [], `session.mts 之外构造或导入了 Device Farm 客户端：\n${describeHits(found, outside)}`);
  assert.ok(found.has("device/session.mts"), "正向对照：device/session.mts 里应检测到 new DeviceFarmClient");
});

test("WebdriverIO 与 Device Farm SDK 的值导入只在 device/ 下", () => {
  const found = scan(deviceSdkValueImports);
  const outside = [...found.keys()].filter((f) => !f.startsWith("device/"));
  assert.deepEqual(outside, [], `设备模块之外在运行期加载了设备 SDK（类型请用 import type）：\n${describeHits(found, outside)}`);
  assert.ok(found.has("device/wdio-log.mts"), "正向对照：device/wdio-log.mts 的 @wdio/logger 值导入应被检测到");
  // deterministic.mts 的 `import type { Browser } from "webdriverio"` 是注册面的类型声明，必须被豁免而不是漏扫
  const deterministic = fs.readFileSync(path.join(SRC, "worker/deterministic.mts"), "utf-8");
  assert.match(deterministic, /import type \{[^}]*\} from "webdriverio"/);
});

test("系统版本与机型字段只出现在读取点与显式豁免的文件里", () => {
  const found = scan(versionModelMentions);
  const outside = [...found.keys()].filter((f) => !VERSION_MODEL_ALLOWED.has(f));
  assert.deepEqual(outside, [],
    `这些文件出现了系统版本或机型字段（只允许经会话能力对象的读取点进入诊断，不作适配分支）：\n${describeHits(found, outside)}`);
  const knownMentions = [
    "worker/deterministic.mts", "lib/job-source.mts", "device/device-session.mts", "device/appium.mts", "device/session.mts",
  ];
  for (const known of knownMentions) {
    assert.ok(found.has(known), `正向对照：${known} 里应检测到系统版本或机型字段`);
  }
  for (const allowed of VERSION_MODEL_ALLOWED.keys()) {
    assert.ok(!isBehaviorModule(allowed), `${allowed} 决定适配行为，不能列入豁免`);
  }
});
