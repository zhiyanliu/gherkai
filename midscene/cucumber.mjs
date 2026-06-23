// cucumber-js 配置：加载根级共享 features/，step 实现用 TS（tsx 经 loader）。
// 跑：cd midscene && AWS_REGION=us-east-1 node_modules/.bin/cucumber-js -c cucumber.mjs
export default {
  // 共享 .feature 在 git 根的 features/（ADR 0005）；本配置在 midscene/，故 ../features
  paths: ["../features/**/*.feature"],
  import: ["bdd/steps/**/*.ts"],
  // tsx 在 Node 22 要用 --import（见运行命令的 NODE_OPTIONS），不能用废弃的 loader 字段
  format: ["progress"],
  // act + 10 断言较慢，放宽默认步骤超时由 step 内部控制
  publishQuiet: true,
};
