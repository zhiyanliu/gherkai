# Package README Guardrails

> 14 nodes · cohesion 0.15

## Key Concepts

- **test_package_readmes.py** (8 connections) — `cli/tests/test_package_readmes.py`
- **test_shipped_readme_is_for_users_only()** (3 connections) — `cli/tests/test_package_readmes.py`
- **Path** (2 connections)
- **_shipped_readmes()** (2 connections) — `cli/tests/test_package_readmes.py`
- **test_every_package_dir_has_a_development_md()** (2 connections) — `cli/tests/test_package_readmes.py`
- **test_github_release_body_is_for_users_only()** (2 connections) — `cli/tests/test_package_readmes.py`
- **test_package_summaries_are_for_users_only()** (2 connections) — `cli/tests/test_package_readmes.py`
- **test_root_readme_is_for_users_only()** (2 connections) — `cli/tests/test_package_readmes.py`
- **parametrize** (1 connections)
- **使用者向文档的护栏：根 README 与包 README（发行包长描述，逐字上 PyPI / npm 页面）、包 Summary（CLAUDE.md…** (1 connections) — `cli/tests/test_package_readmes.py`
- **contributor 内容有明确去处（不是被删掉）：根目录一份 CONTRIBUTING.md（GitHub 惯例名）、每个包目录各一份…** (1 connections) — `cli/tests/test_package_readmes.py`
- **根 README = 仓库首页、给使用者：不写 ADR 编号/决策号/内部机制名（目录结构、开发环境、测试、发布归根 CONTRIBUTING.md）。…** (1 connections) — `cli/tests/test_package_readmes.py`
- **pyproject `description` / package.json `description` = PyPI/npm 页顶的 Summary…** (1 connections) — `cli/tests/test_package_readmes.py`
- **GitHub Release 正文 = CHANGELOG.md 本版节 +…** (1 connections) — `cli/tests/test_package_readmes.py`

## Relationships

- [Doc Scanning Rules](Doc_Scanning_Rules.md) (1 shared connections)

## Source Files

- `cli/tests/test_package_readmes.py`

## Audit Trail

- EXTRACTED: 15 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*