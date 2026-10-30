// 设备模块的读取点与依赖位置护栏（ADR 0052 决策 1、3、4、8；ADR 0051 决策 10）。运行：npx tsx --test src/device/read-points.test.mts。
//
// 用 TypeScript 编译器的语法树扫 src/ 下全部非测试源文件（测试文件不在扫描范围内），四条差集：
//   1. `mobile:` 命令字面量只出现在 device/adapters/ 下（决策 4）：看字符串、模板与正则字面量，注释不算；
//   2. Device Farm 客户端只在 device/session.mts 构造（决策 3）：`new DeviceFarmClient(...)` 与这个类的值导入都只在那里；
//   3. WebdriverIO（含它的 webdriver 与 @wdio/ 下的包）与 Device Farm SDK 的值导入只在 device/ 下（决策 3「设备模块动态加载」）：
//      静态 import、re-export、动态 import() 与 require 都算；`import type`、只含类型说明符的 import 与 `export type` 豁免，
//      它们在编译期擦除、运行期不加载（决策 8）；
//   4. 系统版本与机型字段只出现在读取点与显式豁免的声明里（决策 1、8）。读取点是 Appium 块的会话能力对象；豁免是不构成按版本或
//      机型适配分支的三类：设备选择的输入、协议载荷、句柄上下文的透传。豁免按声明逐处列出（文件里最近一层带名字的函数、方法、
//      类型或模块级常量），不按整个文件：同一文件里别的函数（例如设备接缝里选导航路线的那个）一处出现即红。豁免的声明里，除设备
//      选择的输入之外，读出的值只能原样透传，按白名单判：填进对象字段、数组或模板插值，作变量或字段的初值，以单独成句的赋值写进
//      变量或字段，作为返回值，或用 ?? 与 || 给缺省值；作条件判断真假、与 null / undefined 比较是存在性判断，也允许。括号、类型
//      断言、非空断言与赋值表达式不改变取值，穿过它们沿外层再判。其余写法都按适配分支报红，包括在它上面调方法、让它参与运算
//      （一元运算、算术、拼接、位运算、typeof）、与非空值比较、按它 switch 或用作 case 标签、用作下标、把它交给函数处理；先存进
//      变量、数组、对象或模板再判断照不出来，与不扫数字字面量同一个边界。决定适配行为的四块（驱动适配器、能力探测、界面实现、
//      命令守卫）不在豁免里。不扫数字字面量：坐标、超时与比例里的数字与版本号无法区分（被拒方案）。
//   另有一条结构差集：会话能力对象（`.capabilities`）只在 device/appium.mts 读取，读取点因此只有那一处（决策 1）。
// 每条都带正向对照：检测函数先在构造的源码片段上命中，真实文件里已知的出现也必须被检测到，每条豁免都必须仍有命中，防止检测
// 失效或豁免过期时差集空过。
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

// 系统版本与机型的字段名：会话能力对象（platformVersion、deviceName、deviceModel，Android 的 API 级别与厂商 deviceApiLevel、
// deviceManufacturer，含 appium: 前缀形态）、驱动的设备信息回报（apiVersion、manufacturer）、Device Farm 设备描述（os、model、
// modelId、manufacturer）与本包协议载荷（osVersion）。只认作属性名、对象键、解构键与整串字面量的出现，不认普通变量名
// （`import * as os from "node:os"` 的 os 是变量，不是字段）。
const VERSION_MODEL_FIELDS: ReadonlySet<string> = new Set([
  "platformVersion", "osVersion", "os", "model", "modelId", "deviceModel", "deviceName",
  "deviceApiLevel", "apiVersion", "deviceManufacturer", "manufacturer",
]);
// 多词、不会与别的含义撞名的字段另认大小写与分隔符的变体（platform_version、PLATFORM_VERSION、device-api-level 等）。
// 单词字段（os、model、manufacturer）与 modelId 只认原样：model_id 在本包里是模型服务的模型名，按变体认会误报。
const SPELLING_VARIANT_FIELDS: ReadonlyMap<string, string> = new Map(
  ["platformVersion", "osVersion", "deviceModel", "deviceName", "deviceApiLevel", "apiVersion", "deviceManufacturer"]
    .map((f) => [f.toLowerCase(), f]),
);

function fieldName(text: string): string | null {
  const bare = text.startsWith("appium:") ? text.slice("appium:".length) : text;
  if (VERSION_MODEL_FIELDS.has(bare)) return bare;
  return SPELLING_VARIANT_FIELDS.get(bare.toLowerCase().replace(/[_-]/g, "")) ?? null;
}

function propertyNameText(name: ts.PropertyName | ts.BindingName | undefined): string | null {
  if (name === undefined) return null;
  if (ts.isIdentifier(name) || ts.isStringLiteralLike(name) || ts.isPrivateIdentifier(name)) return name.text;
  return null;
}

/** 一处字段出现：所在声明（scope）与读出的值的用法（use，只对读取类出现——属性访问与下标——给出；声明、对象键、解构键与
 *  字面量为 null）。 */
interface FieldHit extends Hit {
  scope: string;
  use: string | null;
}

function versionModelMentions(sf: ts.SourceFile): FieldHit[] {
  const hits: FieldHit[] = [];
  const add = (n: ts.Node, text: string | null, read: boolean): void => {
    const field = text === null ? null : fieldName(text);
    if (field !== null) hits.push({ line: lineOf(sf, n), what: field, scope: scopeOf(n), use: read ? valueUse(n) : null });
  };
  visit(sf, (n) => {
    if (ts.isPropertyAccessExpression(n)) add(n, n.name.text, true);
    else if (ts.isElementAccessExpression(n) && ts.isStringLiteralLike(n.argumentExpression)) add(n, n.argumentExpression.text, true);
    else if (ts.isPropertySignature(n) || ts.isPropertyDeclaration(n) || ts.isPropertyAssignment(n) || ts.isMethodDeclaration(n)
      || ts.isMethodSignature(n) || ts.isGetAccessorDeclaration(n)) add(n, propertyNameText(n.name), false);
    else if (ts.isShorthandPropertyAssignment(n)) add(n, n.name.text, false);
    else if (ts.isBindingElement(n) && ts.isObjectBindingPattern(n.parent)) add(n, propertyNameText(n.propertyName ?? n.name), false);
    else if (ts.isStringLiteralLike(n) && !isKeyOfParent(n)) add(n, n.text, false);
  });
  return hits;
}

/** 字面量是否已作为属性名、下标或解构键被上面的分支计过（避免同一处计两次）。 */
function isKeyOfParent(n: ts.Node): boolean {
  const p = n.parent;
  if (ts.isElementAccessExpression(p)) return p.argumentExpression === n;
  const keyed = p as ts.Node & { name?: ts.Node; propertyName?: ts.Node };
  return keyed.name === n || keyed.propertyName === n;
}

/** 一个节点所在的声明：由外到内各层带名字的类、接口、类型别名、枚举、函数、方法、构造器（记作 constructor）、访问器、类字段与
 *  模块级变量，以点连接；都不在其中时为 (module)。函数里的局部变量与箭头函数不单独成层。 */
function scopeOf(n: ts.Node): string {
  const names: string[] = [];
  for (let p = n.parent; p !== undefined; p = p.parent) {
    const name = scopeName(p);
    if (name !== null) names.unshift(name);
  }
  return names.length > 0 ? names.join(".") : "(module)";
}

function scopeName(p: ts.Node): string | null {
  if (ts.isConstructorDeclaration(p)) return "constructor";
  if (ts.isClassDeclaration(p) || ts.isInterfaceDeclaration(p) || ts.isTypeAliasDeclaration(p) || ts.isEnumDeclaration(p)
    || ts.isFunctionDeclaration(p) || ts.isMethodDeclaration(p) || ts.isGetAccessorDeclaration(p) || ts.isSetAccessorDeclaration(p)
    || ts.isPropertyDeclaration(p)) {
    return p.name !== undefined ? propertyNameText(p.name) ?? "(computed)" : "(anonymous)";
  }
  if (ts.isVariableDeclaration(p) && ts.isIdentifier(p.name) && ts.isSourceFile(p.parent.parent.parent)) return p.name.text;
  return null;
}

const COMPARISON_OPERATORS: ReadonlySet<ts.SyntaxKind> = new Set([
  ts.SyntaxKind.EqualsEqualsEqualsToken, ts.SyntaxKind.ExclamationEqualsEqualsToken, ts.SyntaxKind.EqualsEqualsToken,
  ts.SyntaxKind.ExclamationEqualsToken, ts.SyntaxKind.LessThanToken, ts.SyntaxKind.LessThanEqualsToken,
  ts.SyntaxKind.GreaterThanToken, ts.SyntaxKind.GreaterThanEqualsToken, ts.SyntaxKind.InKeyword, ts.SyntaxKind.InstanceOfKeyword,
]);

function isNullish(n: ts.Expression): boolean {
  let e = n;
  while (ts.isParenthesizedExpression(e)) e = e.expression;
  return e.kind === ts.SyntaxKind.NullKeyword || (ts.isIdentifier(e) && e.text === "undefined");
}

/** 结果就是某个操作数本身的二元运算：?? 与 || 给缺省值，&& 在左侧为真时取右侧。读出的值经它们原样流出，沿外层继续判。 */
const SELECTING_OPERATORS: ReadonlySet<ts.SyntaxKind> = new Set([
  ts.SyntaxKind.QuestionQuestionToken, ts.SyntaxKind.BarBarToken, ts.SyntaxKind.AmpersandAmpersandToken,
]);

/** 赋值：赋值表达式的值就是写入的值，沿外层继续判；单独成句时是透传。`=` 的左侧是写入目标，不是读取。 */
const ASSIGNMENT_OPERATORS: ReadonlySet<ts.SyntaxKind> = new Set([
  ts.SyntaxKind.EqualsToken, ts.SyntaxKind.QuestionQuestionEqualsToken, ts.SyntaxKind.BarBarEqualsToken,
  ts.SyntaxKind.AmpersandAmpersandEqualsToken,
]);

/** 读出的值是否被拿来做判断（返回用法的说明），还是原样透传（null）。按白名单判。沿着保持取值不变的外层向上找：括号、类型
 *  断言、非空断言、条件表达式的两个分支，??、|| 与 &&（结果就是某个操作数本身），以及赋值表达式（它的值就是写入的值）；
 *  `=` 左侧的出现是写入目标，不是读取。到达这些去处才算透传：对象字段的值、数组元素、不带标签的模板插值、变量或类字段的初值、
 *  返回值、箭头函数的表达式体、单独成句的赋值；作 if / while / for / 条件表达式的条件判断真假、与 null / undefined 比较是
 *  存在性判断，同样不算用法。其余去处都是用法：取属性或调方法、交给函数（含 new 与带标签的模板）、用作下标、参与运算（一元
 *  运算含 !、算术、拼接、位运算、算术与位运算的复合赋值、typeof）、与非空值比较、用作 switch 的判别式或 case 的标签，以及
 *  白名单之外的任何写法。 */
function valueUse(read: ts.Node): string | null {
  let node = read;
  for (;;) {
    const p = node.parent;
    if (ts.isParenthesizedExpression(p) || ts.isAsExpression(p) || ts.isNonNullExpression(p) || ts.isTypeAssertionExpression(p)
      || ts.isSatisfiesExpression(p) || (ts.isConditionalExpression(p) && p.condition !== node)) {
      node = p;
      continue;
    }
    if (ts.isBinaryExpression(p)) {
      const op = p.operatorToken.kind;
      if (SELECTING_OPERATORS.has(op)) {
        node = p;
        continue;
      }
      if (ASSIGNMENT_OPERATORS.has(op)) {
        // `=` 的左侧是写入目标；其余情况下赋值表达式的值就是读出的值，沿外层继续判
        if (op === ts.SyntaxKind.EqualsToken && p.left === node) return null;
        node = p;
        continue;
      }
      if (COMPARISON_OPERATORS.has(op)) return isNullish(p.left === node ? p.right : p.left) ? null : "与其他值比较";
      return "读出的值参与运算";
    }
    if (ts.isPrefixUnaryExpression(p) || ts.isPostfixUnaryExpression(p) || ts.isTypeOfExpression(p)) return "读出的值参与运算";
    if ((ts.isPropertyAccessExpression(p) || ts.isElementAccessExpression(p) || ts.isCallExpression(p) || ts.isNewExpression(p))
      && p.expression === node) return "在读出的值上取属性或调用方法";
    if (ts.isElementAccessExpression(p)) return "把读出的值用作下标";
    if (ts.isCallExpression(p) || ts.isNewExpression(p)) return "把读出的值交给函数处理";
    if (ts.isTemplateSpan(p)) return ts.isTaggedTemplateExpression(p.parent.parent) ? "把读出的值交给函数处理" : null;
    if (ts.isSwitchStatement(p)) return "按读出的值分支";
    if (ts.isCaseClause(p)) return "与其他值比较";
    if (isConditionOf(p, node) || isPassThroughSink(p, node)) return null;
    return "读出的值未原样透传";
  }
}

/** 作条件判断真假的位置：if、while、do、for 的条件与条件表达式的条件。 */
function isConditionOf(p: ts.Node, node: ts.Node): boolean {
  if (ts.isIfStatement(p) || ts.isWhileStatement(p) || ts.isDoStatement(p)) return p.expression === node;
  if (ts.isForStatement(p) || ts.isConditionalExpression(p)) return p.condition === node;
  return false;
}

/** 原样透传的去处：对象字段的值、数组元素、变量或类字段的初值、返回值、箭头函数的表达式体、单独成句的赋值。 */
function isPassThroughSink(p: ts.Node, node: ts.Node): boolean {
  if (ts.isExpressionStatement(p)) return ts.isBinaryExpression(node) && ASSIGNMENT_OPERATORS.has(node.operatorToken.kind);
  if (ts.isPropertyAssignment(p) || ts.isVariableDeclaration(p) || ts.isPropertyDeclaration(p)) return p.initializer === node;
  if (ts.isArrowFunction(p)) return p.body === node;
  return ts.isArrayLiteralExpression(p) || ts.isReturnStatement(p);
}

/** ADR 0052 决策 8 的读取点与三类豁免。 */
type ExemptionKind = "读取点" | "设备选择的输入" | "协议载荷" | "句柄上下文的透传";

interface Exemption {
  kind: ExemptionKind;
  why: string;
}

const exempt = (kind: ExemptionKind, why: string): Exemption => ({ kind, why });

/** 允许出现系统版本与机型字段的声明与理由（ADR 0052 决策 8 的读取点与三类豁免），按文件分组、按声明逐处列出。 */
const VERSION_MODEL_ALLOWED: ReadonlyMap<string, ReadonlyMap<string, Exemption>> = new Map([
  ["device/appium.mts", new Map([
    ["SessionFacts", exempt("读取点", "会话回报的事实的类型：系统版本只进诊断与句柄上下文")],
    ["readSessionCapabilities", exempt("读取点", "会话能力对象的唯一读取点")],
    ["WdioAppiumSession", exempt("读取点", "会话对象上存放读出的系统版本的字段")],
    ["WdioAppiumSession.constructor", exempt("读取点", "建会话对象时经读取点读一次")],
  ])],
  ["device/session.mts", new Map([
    ["eligible", exempt("设备选择的输入", "静态过滤：设备描述须带系统版本")],
    ["Selection", exempt("设备选择的输入", "筛选结果的类型")],
    ["select", exempt("设备选择的输入", "按版本族筛选、按版本排序")],
    ["closestVersion", exempt("设备选择的输入", "零候选时给出最接近的可用版本")],
    ["DeviceFarmSessionBlock.resolve", exempt("设备选择的输入", "按设备请求解析设备，选中设备的机型与系统版本交给 session_opened.device")],
    ["DeviceFarmSessionBlock.deviceInfo", exempt("协议载荷", "session_opened 的 device 字段与 device-session.json 的设备描述")],
  ])],
  ["device/device-session.mts", new Map([
    ["SessionDeviceInfo", exempt("协议载荷", "session_opened 的 device 字段与 device-session.json 的设备描述的类型")],
  ])],
  ["device/surface.mts", new Map([
    ["DeviceChoice", exempt("协议载荷", "设备解析结果的类型：机型与系统版本只进 session_opened.device 与诊断")],
    ["AppiumSession", exempt("读取点", "端口类型上读取点结果的字段")],
    ["DeviceSurface.readyLogLine", exempt("协议载荷", "就绪日志里的设备描述，即 session_opened.device 的同一份载荷")],
    ["DeviceSurface.handlerCtx", exempt("句柄上下文的透传", "把读取点读到的系统版本原样填进句柄上下文的 ctx.device.osVersion")],
  ])],
  ["lib/job-source.mts", new Map([
    ["JobDeviceRequest", exempt("协议载荷", "Job 设备请求里的 osVersion")],
    ["JOB_KEYS", exempt("协议载荷", "Job 设备请求的已知键")],
  ])],
  ["worker/deterministic.mts", new Map([
    ["WebdriverDevice", exempt("句柄上下文的透传", "注册面对 webdriver 句柄 ctx.device 的类型声明")],
  ])],
]);

/** 决定适配行为的四块（ADR 0052 决策 8）：它们不得进入上面的允许清单。 */
function isBehaviorModule(rel: string): boolean {
  return rel.startsWith("device/adapters/") || ["device/probe.mts", "device/interface.mts", "device/guard.mts"].includes(rel);
}

/** 一个文件里不被允许的出现：所在声明不在豁免里，或在豁免的声明里却被拿来做判断（设备选择的输入除外）。 */
function disallowed(rel: string, hits: FieldHit[]): FieldHit[] {
  const allowed = VERSION_MODEL_ALLOWED.get(rel);
  return hits.filter((h) => {
    const exemption = allowed?.get(h.scope);
    if (exemption === undefined) return true;
    return exemption.kind !== "设备选择的输入" && h.use !== null;
  });
}

function describeFieldHits(rel: string, hits: FieldHit[]): string {
  return `${rel}: ${hits.map((h) => `${h.line} 行 ${JSON.stringify(h.what)}（${h.scope}${h.use === null ? "" : `，${h.use}`}）`).join("，")}`;
}

// ---- 会话能力对象 ----

/** 读会话能力对象：属性访问 `.capabilities`、下标 `["capabilities"]` 与解构键 capabilities。 */
function capabilitiesReads(sf: ts.SourceFile): Hit[] {
  const hits: Hit[] = [];
  visit(sf, (n) => {
    const read = (ts.isPropertyAccessExpression(n) && n.name.text === "capabilities")
      || (ts.isElementAccessExpression(n) && ts.isStringLiteralLike(n.argumentExpression) && n.argumentExpression.text === "capabilities")
      || (ts.isBindingElement(n) && ts.isObjectBindingPattern(n.parent) && propertyNameText(n.propertyName ?? n.name) === "capabilities");
    if (read) hits.push({ line: lineOf(sf, n), what: "capabilities" });
  });
  return hits;
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
    "const a = caps[\"appium:deviceApiLevel\"];",
    "const b = info.apiVersion + info.manufacturer;",
    "const c = { deviceManufacturer: x, platform_version: y };",
    "const d = process.env.PLATFORM_VERSION;",
    "const e = { model_id: \"nova\", modelName: m };",
  ].join("\n"));
  assert.deepEqual(versionModelMentions(sf).map((h) => [h.line, h.what]), [
    [3, "platformVersion"], [4, "deviceName"], [5, "osVersion"], [6, "model"], [7, "modelId"], [8, "os"], [9, "os"],
    [12, "deviceApiLevel"], [13, "apiVersion"], [13, "manufacturer"], [14, "deviceManufacturer"], [14, "platformVersion"],
    [15, "platformVersion"],
  ]);
});

test("检测函数在构造的片段上给出所在声明：类成员带类名，构造器记作 constructor，局部变量与箭头函数不单独成层", () => {
  const sf = parse("x.mts", [
    "interface Facts { osVersion: string }",
    "export function read(caps: any) { const v = caps.platformVersion; return v; }",
    "class S {",
    "  readonly platformVersion: string;",
    "  constructor(f: Facts) { this.platformVersion = f.osVersion; }",
    "  private line(): string { const pick = () => this.platformVersion; return pick(); }",
    "}",
    "const KEYS = [\"osVersion\"];",
    "function outer() { function inner(d: any) { return d.model; } return inner; }",
  ].join("\n"));
  assert.deepEqual(versionModelMentions(sf).map((h) => [h.line, h.scope]), [
    [1, "Facts"], [2, "read"], [4, "S"], [5, "S.constructor"], [5, "S.constructor"], [6, "S.line"], [8, "KEYS"], [9, "outer.inner"],
  ]);
});

test("检测函数在构造的片段上区分透传与用法：调方法、交给函数、与非空值比较、按值 switch 是用法，?? 缺省值、填字段、存在性判断是透传", () => {
  const sf = parse("x.mts", [
    "const a = { osVersion: s.platformVersion ?? \"\" };",
    "const b = [d.platform, d.model, d.osVersion].filter((v) => v).join(\" \");",
    "const c = `${d.model}`;",
    "this.platformVersion = f.platformVersion;",
    "const e = s.platformVersion !== null ? 1 : 0;",
    "const f = (s.platformVersion ?? \"\").startsWith(\"26\") ? 1 : 2;",
    "const g = Number(s.platformVersion) >= 16;",
    "const h = s.platformVersion === \"15.8\";",
    "const i = s.platformVersion?.split(\".\");",
    "if (s.osVersion) {}",
    "const j = (s.platformVersion as string) < \"16\";",
    "switch (s.platformVersion) { case \"26\": break; }",
    "switch (k) { case s.platformVersion: break; }",
  ].join("\n"));
  const reads = versionModelMentions(sf).filter((h) => ["platformVersion", "osVersion", "model"].includes(h.what) && h.use !== null);
  assert.deepEqual(reads.map((h) => [h.line, h.use]), [
    [6, "在读出的值上取属性或调用方法"], [7, "把读出的值交给函数处理"], [8, "与其他值比较"], [9, "在读出的值上取属性或调用方法"],
    [11, "与其他值比较"], [12, "按读出的值分支"], [13, "与其他值比较"],
  ]);
});

test("检测函数在构造的片段上识别运算：一元运算、算术、拼接、位运算与 typeof 是用法，模板里直接插值是透传、插值里有运算是用法", () => {
  const sf = parse("x.mts", [
    "switch (+s.platformVersion!) { case 26: break; }",
    "switch (k) { case s.platformVersion + \"\": break; }",
    "const a = -(s.osVersion as any);",
    "const b = ~s.osVersion!;",
    "const c = !s.osVersion;",
    "const d = s.platformVersion * 1 + s.osVersion / 2;",
    "const e = s.platformVersion % 2 - s.osVersion ** 1;",
    "const f = (s.platformVersion | 0) << 1;",
    "const g = typeof s.platformVersion;",
    "v += s.osVersion;",
    "const h = `iOS ${s.platformVersion!} ${(s.model)}`;",
    "const i = `${s.platformVersion + 1}`;",
    "const j = s.osVersion as string;",
  ].join("\n"));
  const reads = versionModelMentions(sf).filter((h) => h.use !== null);
  assert.deepEqual(reads.map((h) => [h.line, h.what, h.use]), [
    [1, "platformVersion", "读出的值参与运算"], [2, "platformVersion", "读出的值参与运算"], [3, "osVersion", "读出的值参与运算"],
    [4, "osVersion", "读出的值参与运算"], [5, "osVersion", "读出的值参与运算"], [6, "platformVersion", "读出的值参与运算"],
    [6, "osVersion", "读出的值参与运算"], [7, "platformVersion", "读出的值参与运算"], [7, "osVersion", "读出的值参与运算"],
    [8, "platformVersion", "读出的值参与运算"], [9, "platformVersion", "读出的值参与运算"], [10, "osVersion", "读出的值参与运算"],
    [12, "platformVersion", "读出的值参与运算"],
  ]);
});

test("检测函数在构造的片段上按白名单判透传：用作下标、带标签的模板、遍历与白名单之外的写法是用法，&& 与赋值表达式的结果沿外层继续判", () => {
  const sf = parse("x.mts", [
    "const a = TABLE[s.platformVersion];",
    "const b = tag`${s.osVersion}`;",
    "for (const ch of s.osVersion) {}",
    "const c = (s.osVersion && s.model)?.length;",
    "const d = s.osVersion && s.model;",
    "const e = [s.platformVersion, s.model];",
    "function f() { return s.osVersion; }",
    "const g = () => s.platformVersion;",
    "class C { readonly v = s.platformVersion; }",
    "this.platformVersion ??= s.platformVersion;",
    "while (s.osVersion) {}",
    "const h = s.osVersion === undefined ? null : s.osVersion;",
    "switch (v = s.platformVersion) {}",
    "if ((v = s.platformVersion) === \"26\") {}",
    "(this.osVersion ??= s.osVersion).startsWith(\"1\");",
    "v = w = s.osVersion;",
    "const i = (v = s.model);",
    "this.model ||= s.model;",
    "(this.osVersion = s.osVersion).startsWith(\"1\");",
    "s.osVersion;",
  ].join("\n"));
  const reads = versionModelMentions(sf).filter((h) => h.use !== null);
  assert.deepEqual(reads.map((h) => [h.line, h.what, h.use]), [
    [1, "platformVersion", "把读出的值用作下标"], [2, "osVersion", "把读出的值交给函数处理"], [3, "osVersion", "读出的值未原样透传"],
    [4, "osVersion", "在读出的值上取属性或调用方法"], [4, "model", "在读出的值上取属性或调用方法"],
    [13, "platformVersion", "按读出的值分支"], [14, "platformVersion", "与其他值比较"],
    [15, "osVersion", "在读出的值上取属性或调用方法"], [15, "osVersion", "在读出的值上取属性或调用方法"],
    [19, "osVersion", "在读出的值上取属性或调用方法"], [20, "osVersion", "读出的值未原样透传"],
  ]);
});

/** 一个文件里按 scopeOf 的写法（以点连接的各层名字）找到的声明。 */
function declarationNamed(sf: ts.SourceFile, scope: string): ts.Node | undefined {
  let found: ts.Node | undefined;
  visit(sf, (n) => {
    const name = scopeName(n);
    if (found !== undefined || name === null) return;
    const outer = scopeOf(n);
    if ((outer === "(module)" ? name : `${outer}.${name}`) === scope) found = n;
  });
  return found;
}

/** 注入真实声明的非透传写法与期望的用法说明。 */
const INJECTED_MISUSES: ReadonlyArray<readonly [string, string]> = [
  ["switch (+s.platformVersion!) { case 26: break; }", "读出的值参与运算"],
  ["switch (k) { case s.platformVersion + \"\": break; }", "读出的值参与运算"],
  ["switch (v = s.platformVersion) {}", "按读出的值分支"],
  ["if ((v = s.platformVersion) === \"26\") {}", "与其他值比较"],
];

test("真实文件里透传类豁免的声明注入非透传写法后报红：一元数值转换用作 switch 判别式、拼接结果用作 case 标签、赋值表达式的值用作 switch 判别式或与非空值比较", () => {
  const injected: string[] = [];
  for (const [rel, scopes] of VERSION_MODEL_ALLOWED) {
    const text = fs.readFileSync(path.join(SRC, rel), "utf-8");
    for (const [scope, exemption] of scopes) {
      if (exemption.kind === "设备选择的输入") continue;
      const decl = declarationNamed(parse(rel, text), scope);
      const body = decl !== undefined && ts.isFunctionLike(decl) ? (decl as ts.FunctionLikeDeclaration).body : undefined;
      if (body === undefined || !ts.isBlock(body)) continue;
      const at = body.getStart() + 1;
      for (const [mutation, use] of INJECTED_MISUSES) {
        const bad = disallowed(rel, versionModelMentions(parse(rel, `${text.slice(0, at)}\n${mutation}\n${text.slice(at)}`)));
        assert.deepEqual(bad.map((h) => [h.scope, h.use]), [[scope, use]], `${rel} 的 ${scope} 里注入 ${mutation} 应报红`);
      }
      injected.push(`${rel} ${scope}`);
    }
  }
  // 正向对照：注入面不能为空，句柄上下文的透传与就绪日志都在其中
  for (const known of ["device/surface.mts DeviceSurface.handlerCtx", "device/surface.mts DeviceSurface.readyLogLine"]) {
    assert.ok(injected.includes(known), `注入面缺少 ${known}`);
  }
});

test("检测函数在构造的片段上命中：读会话能力对象", () => {
  const sf = parse("x.mts", [
    "const a = client.capabilities;",
    "const b = client[\"capabilities\"];",
    "const { capabilities } = client;",
    "const { capabilities: caps } = client;",
    "const c = { capabilities };",
    "const d = { capabilities: requested };",
    "const e = client.requestedCapabilities;",
  ].join("\n"));
  assert.deepEqual(capabilitiesReads(sf).map((h) => h.line), [1, 2, 3, 4]);
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

test("系统版本与机型字段只出现在读取点与显式豁免的声明里，豁免的声明里只原样透传", () => {
  const found = scan(versionModelMentions) as Map<string, FieldHit[]>;
  const violations = [...found].map(([rel, hits]) => [rel, disallowed(rel, hits)] as const).filter(([, bad]) => bad.length > 0);
  assert.deepEqual(violations.map(([rel]) => rel), [],
    "这些地方出现了系统版本或机型字段（只允许经会话能力对象的读取点进入诊断与句柄上下文，不作适配分支；豁免按声明逐处列出）：\n"
      + violations.map(([rel, bad]) => describeFieldHits(rel, bad)).join("\n"));
  // 正向对照：每条豁免都必须仍有命中，豁免过期即红
  for (const [rel, scopes] of VERSION_MODEL_ALLOWED) {
    assert.ok(!isBehaviorModule(rel), `${rel} 决定适配行为，不能列入豁免`);
    const inFile = new Set((found.get(rel) ?? []).map((h) => h.scope));
    for (const scope of scopes.keys()) assert.ok(inFile.has(scope), `正向对照：${rel} 的 ${scope} 里应检测到系统版本或机型字段`);
  }
});

test("会话能力对象只在 device/appium.mts 读取", () => {
  const found = scan(capabilitiesReads);
  const outside = [...found.keys()].filter((f) => f !== "device/appium.mts");
  assert.deepEqual(outside, [], `Appium 块之外读了会话能力对象（应经 Appium 块读出的事实）：\n${describeHits(found, outside)}`);
  assert.ok(found.has("device/appium.mts"), "正向对照：device/appium.mts 里应检测到会话能力对象的读取");
});
