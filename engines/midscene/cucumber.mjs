// cucumber-js 配置：加载根级共享 features/，step 实现用 TS（tsx 经 loader）。
// 跑：cd midscene && AWS_REGION=us-east-1 node_modules/.bin/cucumber-js -c cucumber.mjs
// 用法约定（避免 cucumber 13 的 paths 合并坑）：
//   - 跑全部：node_modules/.bin/cucumber-js -c cucumber.mjs
//   - 跑子集：用 tag 过滤，**不要**再传 feature 路径参数（传路径会与下方 paths 合并、仍跑全部）。
//     例：... -c cucumber.mjs --tags "@engine:midscene"
//   多用例组织/跑批入口的正式形态留给核心库(C)，见 docs/adr/0016。
export default {
  // 共享 .feature 在 git 根的 features/（ADR 0005）；本配置在 engines/midscene/，故 ../../features
  paths: ["../../features/**/*.feature"],
  import: ["bdd/steps/**/*.ts"],
  // tsx 在 Node 22 要用 --import（见运行命令的 NODE_OPTIONS），不能用废弃的 loader 字段
  format: ["progress"],
  publishQuiet: true,
};
