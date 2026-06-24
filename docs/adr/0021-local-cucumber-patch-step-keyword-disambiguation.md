# 本地 patch @cucumber/cucumber：按关键字消除 When/Then 同 pattern 歧义

为支撑 [0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md) 的「默认 AI = 无关键词 `When "{x}"` / `Then "{x}"`」设计，对第三方库 `@cucumber/cucumber` 打了一个**本地补丁**（patch-package）。本 ADR 记录其存在、原因、约束——**未文档化的第三方修改是维护陷阱,必须在此交代清楚**。

## 问题

cucumber-js 的 step 匹配**只按 pattern，不区分 Given/When/Then 关键字**（实测 `assemble_test_cases.js` 的 `matchesStepName` 仅用 `expression.match(text)`，不看 `keyword`）。因此 `When "{string}"` 与 `Then "{string}"` 是**同一个 pattern**，任何裸字符串 step 同时匹配两者 → **ambiguous**，跑批报错。

（对比：pytest-bdd **原生区分** `@when`/`@then`，Nova Act 侧无需补丁。这是又一处「双 runner 方言差异」。）

## 方案

`patches/@cucumber+cucumber+13.0.0.patch` 改 `assemble_test_cases.js` 的 `makeSteps`：先按 pattern 匹配，再按 `PickleStepType → GherkinStepKeyword` **收窄**：
```
__PICKLE_TYPE_TO_KEYWORD = { Context: 'Given', Action: 'When', Outcome: 'Then' }
```
- 仅当 pickle step 的 type 能映射出关键字、且 step definition 的 `keyword` 明确且不同时，才排除。

## 保守回退（关键，须知）

- pickle type 为 **`Unknown`（And/But 继承步）** 或 step def 无 keyword/为 `Unknown` 时 → **不收窄**，保持 vanilla 宽松匹配，避免误伤 `And`/`But`。
- 收窄后若**零匹配** → 回退到原匹配集合（不让收窄把本该匹配的 step 过滤光）。
- ⚠️ **代价**：这套保守策略也意味着「错误声明了关键字的 step」**不会被这个机制揪出**（它只在能明确区分时收窄）。可接受，但记录在案。

## 版本约束 & 升级

- `package.json` 必须**精确 pin** `"@cucumber/cucumber": "13.0.0"`（不是 `^13.0.0`）。否则升级到 13.0.x 后 patch-package **静默跳过**（找不到匹配版本）→ 无报错地退回 ambiguous 匹配。
- `postinstall: patch-package` 钩子使补丁在 `npm install` 后自动应用。
- 升级 cucumber 时：改版本号 → `cd midscene && npx patch-package @cucumber/cucumber` 重新生成 → 提交新 `.patch`。
- **验证补丁已生效**：`grep __PICKLE_TYPE_TO_KEYWORD node_modules/@cucumber/cucumber/lib/assemble/assemble_test_cases.js`（建议纳入 CI 的 postinstall 后置检查）。

## 重议

- 若 cucumber 未来原生支持按关键字区分 step，撤销本补丁。
- 若补丁维护负担超过收益（如频繁升级冲突），退路是回到带关键词的 step 措辞（如 `When 执行 "..."`），免补丁——见 [0020](./0020-step-phrasing-default-ai-deterministic-scaffold.md) 当时权衡。
