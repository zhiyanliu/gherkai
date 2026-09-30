# Skill Deploy Token Guardrail

> 9 nodes · cohesion 0.25

## Key Concepts

- **test_skill_deploy_tokens.py** (9 connections) — `deploy_aws/tests/test_skill_deploy_tokens.py`
- **_build()** (4 connections) — `deploy_aws/tests/test_skill_deploy_tokens.py`
- **_nodes()** (3 connections) — `deploy_aws/tests/test_skill_deploy_tokens.py`
- **ArgumentParser** (2 connections)
- **test_provider_only_flag_table_is_backed_by_the_real_parser()** (2 connections) — `deploy_aws/tests/test_skill_deploy_tokens.py`
- **agent skill 里 `deploy` / `destroy` 那批命令 token 对照 provider 的真 parser（ADR 0043…** (1 connections) — `deploy_aws/tests/test_skill_deploy_tokens.py`
- **`cli/tests` 那边对 `PROVIDER_ONLY_FLAGS` 里的裸 flag 放行（它 import 不到…** (1 connections) — `deploy_aws/tests/test_skill_deploy_tokens.py`
- **前端 + provider 拼出的真 parser。前端那半边逐条照 `cli/gherkai_cli/deploy.py` 的声明抄—— 只抄 flag…** (1 connections) — `deploy_aws/tests/test_skill_deploy_tokens.py`
- **子动词路径 → 该节点声明的 `--flag` 集（`()` 表示 `gherkai <verb>` 本身）。** (1 connections) — `deploy_aws/tests/test_skill_deploy_tokens.py`

## Relationships

- [AWS Deploy Provider](AWS_Deploy_Provider.md) (2 shared connections)
- [CLI Command Span Extraction](CLI_Command_Span_Extraction.md) (2 shared connections)
- [Deploy CLI Backend Helpers](Deploy_CLI_Backend_Helpers.md) (1 shared connections)
- [Doc Rules Scan Sources](Doc_Rules_Scan_Sources.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_skill_deploy_tokens.py`

## Audit Trail

- EXTRACTED: 15 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*