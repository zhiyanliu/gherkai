# 待办清单（静态页）

纯静态页面 `app/index.html`，本机用 `python3 -m http.server 8080` 在 `app/` 目录起服务后访问 `http://localhost:8080/`。删除一条待办后，页面底部出现「撤销」提示条 1.5 秒，点它可恢复；1.5 秒后提示条自动消失。UI 用例在 `features/`，确定性 step 在 `steps/`（两个引擎成对，判定逻辑在 `_checks` 模块，单测用真浏览器）。
