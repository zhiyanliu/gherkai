# 会员中心（静态页）

纯静态页面，本机用 `python3 -m http.server 8080` 在 `app/` 目录起服务后访问 `http://localhost:8080/?points=<累计积分>`。需求在 `docs/requirements.md`；UI 用例用 gherkai 编写与运行，feature 放 `features/`、确定性 step 放 `steps/`（两个引擎成对）。
