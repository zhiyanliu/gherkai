# Skill Deploy Token Checks

> 12 nodes · cohesion 0.20

## Key Concepts

- **test_skill_deploy_tokens.py** (9 connections) — `deploy_aws/tests/test_skill_deploy_tokens.py`
- **_build()** (4 connections) — `deploy_aws/tests/test_skill_deploy_tokens.py`
- **_deploy_spans()** (4 connections) — `deploy_aws/tests/test_skill_deploy_tokens.py`
- **test_deploy_flags_are_attached_to_the_right_subverb()** (4 connections) — `deploy_aws/tests/test_skill_deploy_tokens.py`
- **_nodes()** (3 connections) — `deploy_aws/tests/test_skill_deploy_tokens.py`
- **ArgumentParser** (2 connections)
- **test_provider_only_flag_table_is_backed_by_the_real_parser()** (2 connections) — `deploy_aws/tests/test_skill_deploy_tokens.py`
- **agent skill 里 `deploy` / `destroy` 那批命令 token 对照 provider 的真 parser（ADR 0043…** (1 connections) — `deploy_aws/tests/test_skill_deploy_tokens.py`
- **`cli/tests` 那边对 `PROVIDER_ONLY_FLAGS` 里的裸 flag 放行（它 import 不到…** (1 connections) — `deploy_aws/tests/test_skill_deploy_tokens.py`
- **前端 + provider 拼出的真 parser。前端那半边逐条照 `cli/gherkai_cli/deploy.py` 的声明抄—— 只抄 flag…** (1 connections) — `deploy_aws/tests/test_skill_deploy_tokens.py`
- **子动词路径 → 该节点声明的 `--flag` 集（`()` 表示 `gherkai <verb>` 本身）。** (1 connections) — `deploy_aws/tests/test_skill_deploy_tokens.py`
- **`gherkai deploy [<子动词>] --flag` 逐对比对。父层给法合法（`deploy --prefix p push-worker …`），…** (1 connections) — `deploy_aws/tests/test_skill_deploy_tokens.py`

## Relationships

- [Skill Doc Flag Guardrails](Skill_Doc_Flag_Guardrails.md) (3 shared connections)
- [Deploy Provider Interface](Deploy_Provider_Interface.md) (2 shared connections)
- [Deploy CLI Doctor Checks](Deploy_CLI_Doctor_Checks.md) (1 shared connections)
- [Doc Scanning Rules](Doc_Scanning_Rules.md) (1 shared connections)

## Source Files

- `deploy_aws/tests/test_skill_deploy_tokens.py`

## Audit Trail

- EXTRACTED: 17 (85%)
- INFERRED: 3 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*