# Progress Log

## 2026-06-07

- Added harness documentation and task ledger files requested for Incentdoc v2.
- Added verification entry point at `scripts/verify.sh`.
- No product feature implementation was performed.
- No existing business logic was changed.
- No existing tests were deleted or weakened.
- `tasks/feature_list.json` marks harness documentation as `in_progress` until `scripts/verify.sh` is executed and passes.
- Verification attempt: `bash scripts/verify.sh` could not complete because the Windows environment has no default WSL distribution for `bash`.
- Manual harness checks completed: required files exist, `tasks/feature_list.json` is valid JSON, and 6 existing Python test files are present.
- Python test execution was not available because `pytest` is not installed in the current environment.
- Frontend build check passed with `npm.cmd run build`.

## 2026-06-07 Minimum Recommendation Flow

- Acceptance criteria checked before implementation: use one approved policy JSON fixture, one general-company mock, one employee and leave-event mock, code-based condition evaluation, code-based amount calculation, calculation-step output, evidence snippet propagation, and automatic tests.
- Selected feature: `policy-approval-gate`, because the minimum recommendation flow must first prove that only approved policy structures can enter calculation.
- Added `match_agent_v0.8/match_agent_v0.8/services/minimum_recommendation_flow.py`.
- Added `match_agent_v0.8/match_agent_v0.8/data/policy_json/approved_minimum_recommendation_fixture.json`.
- Added `match_agent_v0.8/match_agent_v0.8/test_minimum_recommendation_flow.py`.
- Updated `scripts/verify.sh` so environments without `pytest` still run available `test_*.py` files directly and skip only tests blocked by missing optional external dependencies.
- Updated `tasks/feature_list.json` status for `policy-approval-gate` to `passing` after verification passed.
- Test result: `python test_minimum_recommendation_flow.py` passed.
- Verification result: `bash scripts/verify.sh` passed when Git Bash was placed first in PATH. Existing DB-related tests were skipped because the current environment lacks `sqlalchemy`; non-DB tests and the new minimum recommendation flow test passed, and frontend build passed.
- Remaining issue: the default Windows `bash.exe` still points to WSL without a default distro, so this local environment needs Git Bash first in PATH to run `bash scripts/verify.sh`.

## 2026-06-07 Verification Reproducibility

- Scope: verification environment reproducibility only. No product feature or existing business logic was changed.
- Added `docs/DEVELOPMENT_SETUP.md` with Windows PowerShell, Git Bash, limited verification, and full verification instructions.
- Added `requirements-dev.txt` to declare development/test dependencies, including `pytest`, `SQLAlchemy`, and `psycopg2-binary`.
- Updated `scripts/verify.sh` to support `--limited` and `--full` modes.
- Added `scripts/verify.ps1` for native Windows PowerShell verification without relying on Windows `bash.exe` or WSL.
- Updated `tasks/feature_list.json` only for `harness-documentation`, changing it to `passing` after limited verification passed.
- Limited verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode limited` passed.
- Limited verification result: `C:\Program Files\Git\bin\bash.exe scripts/verify.sh --limited` passed.
- Full verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode full` failed as expected because `pytest` is not installed.
- Full verification result: `C:\Program Files\Git\bin\bash.exe scripts/verify.sh --full` failed as expected because `pytest` is not installed.
- DB-dependent tests skipped in limited mode: `test_db_connection.py`, `test_policy_load.py`, `test_recommendation_history_service.py`.
- Remaining issue: full verification still requires installing `requirements-dev.txt` dependencies and providing a reachable PostgreSQL database.

## 2026-06-07 Rule Engine Operator Validation

- Scope: implemented one Rule Engine operator validation feature only. No UI, DB structure, new policy, or product workflow was added.
- Read first: `AGENTS.md`, `docs/RULE_ENGINE.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Extended `match_agent_v0.8/match_agent_v0.8/services/condition_evaluator.py` with code-based operator condition evaluation while preserving the existing evaluator functions.
- Added `match_agent_v0.8/match_agent_v0.8/test_condition_operator_evaluator.py`.
- Supported operators: `eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `in`, `not_in`.
- Structured result fields include `eligible`, `passed_conditions`, `failed_conditions`, `condition_id`, `field`, `operator`, `expected`, `actual`, `reason`, and `evidence_snippets`.
- Test coverage includes all conditions passing, one failed condition, multiple failed conditions, unsupported operator, missing input field, null handling, and evidence snippet propagation.
- Test result: `python test_condition_operator_evaluator.py` passed.
- Verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode limited` passed.
- Updated `tasks/feature_list.json` by adding only `rule-engine-operator-validation` as `passing`.
- Remaining issue: limited verification still skips DB-dependent tests by design: `test_db_connection.py`, `test_policy_load.py`, `test_recommendation_history_service.py`.

## 2026-06-07 Monthly Fixed Amount Calculation

- Scope: implemented one support amount calculation feature only. No UI, API, DB structure, new policy, or duplicate-benefit optimization was added.
- Read first: `AGENTS.md`, `docs/POLICY_SCHEMA.md`, `docs/RULE_ENGINE.md`, `docs/RECOMMENDATION_RULES.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Extended `match_agent_v0.8/match_agent_v0.8/services/calculation_service.py` with `calculate_monthly_fixed_policy_support`.
- Reused the code-based operator evaluator via `evaluate_operator_conditions`.
- Reused the existing amount calculation path by routing `calculate_yearly_amount` monthly multiplication through `calculate_monthly_fixed_amount`.
- Added `match_agent_v0.8/match_agent_v0.8/test_monthly_fixed_calculation.py`.
- Calculation rule: only `approved` policies are calculated; failed conditions skip calculation; missing `monthly_amount` returns `calculation_error`; when policy max months are null, requested months are used without inferring a cap.
- Test coverage includes requested months shorter than, equal to, and greater than max months; ineligible policy skip; needs_review policy skip; null monthly amount error; null max months handling; evidence snippet propagation; and structured calculation step input/result checks.
- Test result: `python test_monthly_fixed_calculation.py` passed.
- Verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode limited` passed.
- Updated `tasks/feature_list.json` by adding only `monthly-fixed-amount-calculation` as `passing`.
- Remaining issue: limited verification still skips DB-dependent tests by design: `test_db_connection.py`, `test_policy_load.py`, `test_recommendation_history_service.py`.

## 2026-06-07 Period Tiered Amount Calculation

- Scope: implemented one support amount calculation feature only. No UI, API, DB structure, real policy addition, duplicate-benefit logic, conditional extra support, or combination optimization was added.
- Read first: `AGENTS.md`, `docs/POLICY_SCHEMA.md`, `docs/RULE_ENGINE.md`, `docs/RECOMMENDATION_RULES.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Checked policy review state fields. Active code and docs were using `approval_status`; the requested schema standard is now `review_status` with allowed values `needs_review`, `approved`, and `deprecated`.
- Updated docs and current harness fixtures/tests to use `review_status` for policy review state. Calculation result `status` remains a separate execution-result field.
- Extended `match_agent_v0.8/match_agent_v0.8/services/calculation_service.py` with shared calculation precondition helpers and `calculate_period_tiered_policy_support`.
- Reused the code-based operator evaluator via `evaluate_operator_conditions`.
- Reused `calculate_monthly_fixed_amount` for tier amount multiplication so monthly multiplication logic is not duplicated.
- Added `match_agent_v0.8/match_agent_v0.8/test_period_tiered_calculation.py`.
- Updated `match_agent_v0.8/match_agent_v0.8/test_monthly_fixed_calculation.py`, `match_agent_v0.8/match_agent_v0.8/test_minimum_recommendation_flow.py`, and `match_agent_v0.8/match_agent_v0.8/data/policy_json/approved_minimum_recommendation_fixture.json` for `review_status`.
- Calculation rule: only `review_status == approved` policies are calculated; failed conditions skip calculation; only tiers covered by requested months are applied; tier gaps, overlaps, reversed ranges, and missing tier monthly amounts return `calculation_error`; no missing tier, amount, or period is inferred.
- Test coverage includes first-tier-only duration, two-tier duration, duration exceeding all tiers, exact tier boundary, ineligible policy skip, needs_review policy skip, null tier monthly amount, reversed tier range, overlapping tiers, tier gaps, evidence propagation, and monthly_fixed regression.
- Test result: `python test_period_tiered_calculation.py` passed.
- Regression test result: `python test_monthly_fixed_calculation.py` passed.
- Verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode limited` passed.
- Git check: `git rev-parse --show-toplevel` failed at the workspace and app directories because this workspace is not a Git repository, so `git diff --check` was not applicable.
- Updated `tasks/feature_list.json` by adding only `period-tiered-amount-calculation` as `passing`.
- Remaining issue: limited verification still skips DB-dependent tests by design: `test_db_connection.py`, `test_policy_load.py`, `test_recommendation_history_service.py`.

## 2026-06-07 Conditional Bonus Amount Calculation

- Scope: implemented one support amount calculation feature only. No UI, API, DB structure, real policy addition, inter-policy duplicate-benefit logic, multi-policy combination generation, or employer net-cost optimization was added.
- Read first: `AGENTS.md`, `docs/POLICY_SCHEMA.md`, `docs/RULE_ENGINE.md`, `docs/RECOMMENDATION_RULES.md`, `docs/TEST_SCENARIOS.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Analyzed `match_agent_v0.8/match_agent_v0.8/services/calculation_service.py` before implementation and preserved existing `monthly_fixed` and `period_tiered` calculator behavior.
- Extended `match_agent_v0.8/match_agent_v0.8/services/calculation_service.py` with `calculate_conditional_bonus_policy_support`.
- Reused existing base calculators through `calculate_base_policy_support`, which delegates to `calculate_monthly_fixed_policy_support` or `calculate_period_tiered_policy_support`.
- Reused the code-based operator evaluator via `evaluate_operator_conditions` for bonus conditions.
- Reused `calculate_monthly_fixed_amount` for bonus monthly amount multiplication.
- Added `match_agent_v0.8/match_agent_v0.8/test_conditional_bonus_calculation.py` with test-only fixture data, not real policy data.
- Calculation rule: only `review_status == approved` policies are calculated; base support must calculate first; bonus calculation supports only `monthly_fixed`; failed bonus conditions are reported in `skipped_bonuses` without making the policy a calculation error; missing bonus `monthly_amount` returns `calculation_error`; missing bonus `max_months` uses requested months without inferring a cap.
- Test coverage includes applied bonus plus base amount, skipped bonus with base-only total, bonus requested months below/equal/above max months, null max months, null monthly amount error, needs_review gate, base condition failure skipping bonus, skipped bonus failed-condition reasons, separated base/bonus calculation steps, evidence propagation, and monthly_fixed/period_tiered regression.
- Test result: `python test_conditional_bonus_calculation.py` passed.
- Regression test result: `python test_monthly_fixed_calculation.py` passed.
- Regression test result: `python test_period_tiered_calculation.py` passed.
- Verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode limited` passed.
- Git check: `git rev-parse --show-toplevel` failed because this workspace is not a Git repository, so `git diff --check` was not applicable.
- Updated `tasks/feature_list.json` by adding only `conditional-bonus-amount-calculation` as `passing`.
- Remaining issue: limited verification still skips DB-dependent tests by design: `test_db_connection.py`, `test_policy_load.py`, `test_recommendation_history_service.py`.

## 2026-06-07 Standardized Policy Calculation Result

- Scope: implemented one result-standardization feature only. No UI, API, DB structure, real policy addition, duplicate-benefit conflict rules, multi-policy combination generation, or net-cost optimization was added.
- Read first: `AGENTS.md`, `docs/POLICY_SCHEMA.md`, `docs/RULE_ENGINE.md`, `docs/RECOMMENDATION_RULES.md`, `docs/TEST_SCENARIOS.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Analyzed `match_agent_v0.8/match_agent_v0.8/services/calculation_service.py` and the existing monthly_fixed, period_tiered, and conditional_bonus tests before implementation.
- Added `normalize_policy_calculation_result` and `validate_standard_calculation_result` to `match_agent_v0.8/match_agent_v0.8/services/calculation_service.py`.
- Reused existing calculation outputs and did not change amount formulas or existing calculator return contracts.
- Added `match_agent_v0.8/match_agent_v0.8/test_standardized_calculation_result.py`.
- Standard result fields: `policy_id`, `policy_name`, `review_status`, `eligible`, `status`, `calculation_type`, `base_amount`, `bonus_amount`, `estimated_total_amount`, `calculation_steps`, `passed_conditions`, `failed_conditions`, `applied_bonuses`, `skipped_bonuses`, `evidence_snippets`, and `errors`.
- Default rule: no-bonus policies return `bonus_amount=0`, `applied_bonuses=[]`, and `skipped_bonuses=[]`; absent condition lists become empty arrays; successful calculations return `errors=[]`; uncalculated base amounts are normalized to null instead of inferring zero.
- Test coverage includes standardized monthly_fixed, period_tiered, conditional_bonus applied, conditional_bonus skipped, ineligible, needs_review, calculation_error, no-bonus defaults, empty errors, evidence preservation, and conditional_bonus error with known base amount.
- Test result: `python test_standardized_calculation_result.py` passed.
- Regression test result: `python test_monthly_fixed_calculation.py` passed.
- Regression test result: `python test_period_tiered_calculation.py` passed.
- Regression test result: `python test_conditional_bonus_calculation.py` passed.
- Verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode limited` passed.
- Git check: `git rev-parse --show-toplevel` failed at the workspace and app directories because this workspace is not a Git repository, so `git diff --check` was not applicable.
- Updated `tasks/feature_list.json` by adding only `standardized-policy-calculation-result` as `passing`.
- Remaining issue: limited verification still skips DB-dependent tests by design: `test_db_connection.py`, `test_policy_load.py`, `test_recommendation_history_service.py`.

## 2026-06-07 Combination Rules Schema Validation

- Scope: implemented one schema validation feature only. No UI, API, DB structure, real policy addition, runtime policy conflict detection, multi-policy combination generation, total-support aggregation, or net-cost optimization was added.
- Read first: `AGENTS.md`, `docs/POLICY_SCHEMA.md`, `docs/RECOMMENDATION_RULES.md`, `docs/TEST_SCENARIOS.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Checked existing policy schema docs and `match_agent_v0.8/match_agent_v0.8/services/calculation_service.py`; existing calculation engine and standardized result structure were not changed.
- Added `match_agent_v0.8/match_agent_v0.8/services/combination_rule_validator.py`.
- Added `match_agent_v0.8/match_agent_v0.8/test_combination_rule_validator.py`.
- Updated `docs/POLICY_SCHEMA.md` with `combination_rules` structure and validation rules.
- Updated `docs/RECOMMENDATION_RULES.md` with rule type meanings and the current schema-validation-only scope.
- Updated `docs/TEST_SCENARIOS.md` with combination rule schema validation scenarios.
- Validator behavior: missing `combination_rules` normalizes to `[]`; allowed `rule_type` values are `mutually_exclusive`, `requires`, and `allowed_with`; invalid rules return structured errors with `rule_id`, `field`, and `reason`; evidence snippets are preserved without rewriting.
- Test coverage includes missing rules normalization, valid mutually_exclusive/requires/allowed_with rules, unsupported rule type, missing rule_id, empty target ids, self reference, duplicate target ids, missing reason, missing evidence snippets, mixed valid/invalid rules, and monthly_fixed/period_tiered/conditional_bonus/standard-result regression.
- Test result: `python test_combination_rule_validator.py` passed.
- Regression test result: `python test_monthly_fixed_calculation.py` passed.
- Regression test result: `python test_period_tiered_calculation.py` passed.
- Regression test result: `python test_conditional_bonus_calculation.py` passed.
- Regression test result: `python test_standardized_calculation_result.py` passed.
- Verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode limited` passed.
- Git check: `git rev-parse --show-toplevel` failed at the workspace and app directories because this workspace is not a Git repository, so `git diff --check` was not applicable.
- Updated `tasks/feature_list.json` by adding only `combination-rules-schema-validation` as `passing`.
- Remaining issue: limited verification still skips DB-dependent tests by design: `test_db_connection.py`, `test_policy_load.py`, `test_recommendation_history_service.py`.

## 2026-06-07 Mutually Exclusive Conflict Detection

- Scope: implemented one mutually_exclusive conflict detection feature only. No UI, API, DB structure, real policy addition, requires detection, allowed_with detection, combination generation, automatic exclusion, total-support aggregation, or net-cost optimization was added.
- Read first: `AGENTS.md`, `docs/POLICY_SCHEMA.md`, `docs/RECOMMENDATION_RULES.md`, `docs/TEST_SCENARIOS.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Analyzed `match_agent_v0.8/match_agent_v0.8/services/combination_rule_validator.py`, `match_agent_v0.8/match_agent_v0.8/services/calculation_service.py`, `match_agent_v0.8/match_agent_v0.8/test_combination_rule_validator.py`, and `match_agent_v0.8/match_agent_v0.8/test_standardized_calculation_result.py` before implementation.
- Added `match_agent_v0.8/match_agent_v0.8/services/mutual_exclusion_detector.py`.
- Added `match_agent_v0.8/match_agent_v0.8/test_mutual_exclusion_detector.py`.
- Updated `docs/RECOMMENDATION_RULES.md` with mutually_exclusive detection rules and non-goals.
- Updated `docs/TEST_SCENARIOS.md` with mutually_exclusive conflict detection scenarios.
- Detection rule: only `review_status == approved` candidate policies are considered; `validate_combination_rules` runs first; schema errors are returned separately; only `mutually_exclusive` rules are detected; requires and allowed_with are ignored; target policies absent from the candidate list do not create conflicts; evidence snippets are preserved.
- One-way declaration behavior: `A -> B` is sufficient to return a conflict when both A and B are approved candidates.
- Two-way declaration behavior: `A -> B` and `B -> A` are deduplicated into one conflict result.
- Test coverage includes no conflict, one-way conflict, two-way dedupe, multiple targets, absent target, needs_review exclusion, deprecated exclusion, ignored requires, ignored allowed_with, schema errors, evidence preservation, and combination schema/monthly_fixed/period_tiered/conditional_bonus/standard-result regression.
- Test result: `python test_mutual_exclusion_detector.py` passed.
- Regression test result: `python test_combination_rule_validator.py` passed.
- Regression test result: `python test_monthly_fixed_calculation.py` passed.
- Regression test result: `python test_period_tiered_calculation.py` passed.
- Regression test result: `python test_conditional_bonus_calculation.py` passed.
- Regression test result: `python test_standardized_calculation_result.py` passed.
- Verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode limited` passed.
- Git check: `git rev-parse --show-toplevel` failed at the workspace and app directories because this workspace is not a Git repository, so `git diff --check` was not applicable.
- Updated `tasks/feature_list.json` by adding only `mutually-exclusive-conflict-detection` as `passing`.
- Remaining issue: limited verification still skips DB-dependent tests by design: `test_db_connection.py`, `test_policy_load.py`, `test_recommendation_history_service.py`.

## 2026-06-07 Requires Policy Violation Detection

- Scope: implemented one requires policy violation detection feature only. No UI, API, DB structure, real policy addition, allowed_with detection, mutually_exclusive auto-exclusion, requires auto-addition, combination generation, total-support aggregation, or net-cost optimization was added.
- Read first: `AGENTS.md`, `docs/POLICY_SCHEMA.md`, `docs/RECOMMENDATION_RULES.md`, `docs/TEST_SCENARIOS.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Analyzed `match_agent_v0.8/match_agent_v0.8/services/combination_rule_validator.py`, `match_agent_v0.8/match_agent_v0.8/services/mutual_exclusion_detector.py`, `match_agent_v0.8/match_agent_v0.8/test_combination_rule_validator.py`, and `match_agent_v0.8/match_agent_v0.8/test_mutual_exclusion_detector.py` before implementation.
- Added `match_agent_v0.8/match_agent_v0.8/services/requirement_detector.py`.
- Added `match_agent_v0.8/match_agent_v0.8/test_requirement_detector.py`.
- Updated `docs/RECOMMENDATION_RULES.md` with requires detection semantics.
- Updated `docs/TEST_SCENARIOS.md` with requires detection scenarios.
- Detection rule: only `review_status == approved` candidate policies are considered; `validate_combination_rules` runs first; schema errors are returned separately; only `requires` rules are detected; mutually_exclusive and allowed_with are ignored; all `target_policy_ids` are required; non-approved target policies count as missing; evidence snippets are preserved.
- Multiple target handling: `target_policy_ids` is treated as an AND list. If any target is missing from the approved candidate list, the violation records `required_policy_ids` and only the missing IDs in `missing_policy_ids`. OR requirements and `requirement_mode` are not implemented.
- Test coverage includes no requires rules, present required policy, missing required policy, multiple required policies present, one missing required policy, needs_review target, deprecated target, absent source policy, ignored mutually_exclusive and allowed_with rules, schema errors, evidence preservation, and combination schema/mutually_exclusive/monthly_fixed/period_tiered/conditional_bonus/standard-result regression.
- Test result: `python test_requirement_detector.py` passed.
- Verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode limited` passed.
- Git check: `git rev-parse --show-toplevel` failed at the workspace and app directories because this workspace is not a Git repository, so `git diff --check` was not applicable.
- Updated `tasks/feature_list.json` by adding only `requires-policy-violation-detection` as `passing`.
- Remaining issue: limited verification still skips DB-dependent tests by design: `test_db_connection.py`, `test_policy_load.py`, `test_recommendation_history_service.py`.

## 2026-06-07 Valid Policy Combination Generation

- Scope: implemented one valid policy combination generation feature only. No UI, API, DB structure, real policy addition, combination total-support aggregation, employer net-cost calculation, optimal-combination recommendation, or allowed_with exception handling was added.
- Read first: `AGENTS.md`, `docs/POLICY_SCHEMA.md`, `docs/RECOMMENDATION_RULES.md`, `docs/TEST_SCENARIOS.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Analyzed `match_agent_v0.8/match_agent_v0.8/services/combination_rule_validator.py`, `match_agent_v0.8/match_agent_v0.8/services/mutual_exclusion_detector.py`, `match_agent_v0.8/match_agent_v0.8/services/requirement_detector.py`, `match_agent_v0.8/match_agent_v0.8/test_mutual_exclusion_detector.py`, and `match_agent_v0.8/match_agent_v0.8/test_requirement_detector.py` before implementation.
- Added `match_agent_v0.8/match_agent_v0.8/services/policy_combination_generator.py`.
- Added `match_agent_v0.8/match_agent_v0.8/test_policy_combination_generator.py`.
- Updated `docs/RECOMMENDATION_RULES.md` with policy-combination generation rules.
- Updated `docs/TEST_SCENARIOS.md` with policy-combination generation scenarios.
- Combination rule: only `review_status == approved` policies are candidates; empty combinations are not generated; all non-empty subsets are generated up to the safety guard; policy IDs and result ordering are deterministic; duplicate policy IDs return a structured error without merging.
- Detector reuse: each generated combination is checked with existing `detect_mutually_exclusive_conflicts` and `detect_required_policy_violations`. Conflicts and requires violations are recorded as rejection reasons with detector details and evidence snippets preserved.
- Safety guard: `MAX_COMBINATION_CANDIDATES = 12`; generation stops with `max_combination_candidates_exceeded` if approved candidates exceed the guard.
- Non-goals preserved: allowed_with does not affect output in this scope; policies are not auto-added or auto-removed; no amount calculation, total aggregation, optimal selection, or net-cost optimization is performed.
- Test coverage includes one candidate, three candidates yielding seven combinations, mutually_exclusive rejection, requires rejection and valid pair, simultaneous conflict and requires reasons, needs_review/deprecated exclusion, allowed_with no-op, duplicate policy IDs, empty candidates, safety guard, deterministic ordering, evidence preservation, and combination schema/mutually_exclusive/requires/monthly_fixed/period_tiered/conditional_bonus/standard-result regression.
- Test result: `python test_policy_combination_generator.py` passed.
- Verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode limited` passed.
- Updated `tasks/feature_list.json` by adding only `valid-policy-combination-generation` as `passing`.
- Remaining issue: limited verification still skips DB-dependent tests by design: `test_db_connection.py`, `test_policy_load.py`, `test_recommendation_history_service.py`.

## 2026-06-07 Valid Combination Amount Summarization

- Scope: implemented one valid-combination amount summarization feature only. No UI, API, DB structure, real policy addition, allowed_with exception handling, employer burden cost calculation, employer net-cost calculation, optimal-combination selection, or recommendation ranking was added.
- Read first: `AGENTS.md`, `docs/POLICY_SCHEMA.md`, `docs/RECOMMENDATION_RULES.md`, `docs/TEST_SCENARIOS.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Analyzed `match_agent_v0.8/match_agent_v0.8/services/calculation_service.py`, `match_agent_v0.8/match_agent_v0.8/services/policy_combination_generator.py`, `match_agent_v0.8/match_agent_v0.8/test_standardized_calculation_result.py`, and `match_agent_v0.8/match_agent_v0.8/test_policy_combination_generator.py` before implementation.
- Added `match_agent_v0.8/match_agent_v0.8/services/combination_amount_summarizer.py`.
- Added `match_agent_v0.8/match_agent_v0.8/test_combination_amount_summarizer.py`.
- Updated `docs/RECOMMENDATION_RULES.md` with valid-combination amount summarization rules.
- Updated `docs/TEST_SCENARIOS.md` with combination amount summarization scenarios.
- Summarization input: `valid_combinations` from `generate_valid_policy_combinations` and standardized policy calculation results from `normalize_policy_calculation_result`.
- Summarization rule: only combinations where every policy has `status == calculated` and non-null amount fields are summarized; missing, ineligible, calculation_error, non-calculated, or null-total policy results reject the combination with structured reasons.
- Amount rule: `total_subsidy_amount` sums only each policy's `estimated_total_amount`; `total_base_amount` sums `base_amount`; `total_bonus_amount` sums `bonus_amount`; null amount fields are not converted to zero.
- Conditional bonus handling: conditional bonus policies are not double counted because `bonus_amount` is reported separately while `total_subsidy_amount` uses the policy's already-inclusive `estimated_total_amount`.
- Preservation rule: policy-level `calculation_steps` and `evidence_snippets` are copied from standardized results and not regenerated.
- Test coverage includes single/two/three-policy totals, conditional_bonus non-duplication, separated base and bonus totals, calculation_error/ineligible/null-total/missing-result rejection, duplicate policy result errors, calculation step preservation, evidence preservation, deterministic ordering, and policy-combination/schema/mutually_exclusive/requires/monthly_fixed/period_tiered/conditional_bonus/standard-result regression.
- Test result: `python test_combination_amount_summarizer.py` passed.
- Verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode limited` passed.
- Updated `tasks/feature_list.json` by adding only `valid-combination-amount-summarization` as `passing`.
- Remaining issue: limited verification still skips DB-dependent tests by design: `test_db_connection.py`, `test_policy_load.py`, `test_recommendation_history_service.py`.

## 2026-06-07 Employer Net Cost Calculation

- Scope: implemented one employer net-cost calculation feature only. No UI, API, DB structure, real policy addition, allowed_with exception handling, optimal-combination selection, recommendation ranking, or automatic cost inference was added.
- Read first: `AGENTS.md`, `docs/POLICY_SCHEMA.md`, `docs/RECOMMENDATION_RULES.md`, `docs/TEST_SCENARIOS.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Analyzed `match_agent_v0.8/match_agent_v0.8/services/combination_amount_summarizer.py`, `match_agent_v0.8/match_agent_v0.8/test_combination_amount_summarizer.py`, and `docs/RECOMMENDATION_RULES.md` before implementation.
- Added `match_agent_v0.8/match_agent_v0.8/services/employer_net_cost_calculator.py`.
- Added `match_agent_v0.8/match_agent_v0.8/test_employer_net_cost_calculator.py`.
- Updated `docs/RECOMMENDATION_RULES.md` with employer net-cost calculation rules.
- Updated `docs/TEST_SCENARIOS.md` with employer net-cost scenarios.
- Calculation input: summarized combinations from `summarize_combination_amounts` and explicit `employer_cost_items`.
- Cost application rule: missing or empty `applies_to_policy_ids` applies to every summarized combination; one or more target policy IDs are treated as an AND condition; OR applicability is not implemented.
- Cost validation rule: missing `cost_id`, duplicate `cost_id`, null amount, non-numeric amount, and negative amount return structured errors and are not auto-corrected or converted to zero.
- Cost inference prevention: the calculator never generates cost items and never infers costs from policy text, employee data, subsidy amount, or policy category. If no cost items are provided, that explicit empty input yields `total_employer_cost = 0`.
- Formula: `total_employer_cost = sum(applied employer_cost_items.amount)` and `net_employer_cost = total_employer_cost - total_subsidy_amount`.
- Preservation rule: existing summarized combination fields, calculation steps, and evidence snippets are reused; `total_subsidy_amount` is not recalculated.
- Test coverage includes no-cost input, global cost items, policy-specific cost items, multi-policy AND costs, non-applicable costs, multiple cost sum, null/non-numeric/negative amounts, missing and duplicate cost IDs, missing applies-to normalization, negative net cost, and combination amount/policy combination/schema/mutually_exclusive/requires/monthly_fixed/period_tiered/conditional_bonus/standard-result regression.
- Test result: `python test_employer_net_cost_calculator.py` passed.
- Verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode limited` passed.
- Updated `tasks/feature_list.json` by adding only `employer-net-cost-calculation` as `passing`.
- Remaining issue: limited verification still skips DB-dependent tests by design: `test_db_connection.py`, `test_policy_load.py`, `test_recommendation_history_service.py`.

## 2026-06-07 General Company Recommendation Demo Screen

- Scope: implemented one team-sharing demo screen for general-company recommendation result comparison only. No full frontend renewal, signup, onboarding, labor-partner screen, document management, replacement-worker management, newsletter, DB structure change, employer net-cost display, optimal-combination selection, or recommendation ranking was added.
- Read first: `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/POLICY_SCHEMA.md`, `docs/RECOMMENDATION_RULES.md`, `docs/TEST_SCENARIOS.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Product spec note: requested `docs/product-specs/incentdoc-v2-user-flow-ia.md` was not present in this workspace; the available `product-specs/incentdoc-v2-user-flow-ia.md` was read instead.
- Frontend analysis: the app uses React 19, Vite 7, and `lucide-react`; routing is state-based inside `frontend/src/App.jsx` with no React Router; styling is global CSS in `frontend/src/styles.css`; no existing frontend API/fetch adapter pattern was found.
- Added demo route behavior for `/company/recommendation-demo` through the existing state-based view system with view key `recommendationDemo`.
- Updated `match_agent_v0.8/match_agent_v0.8/frontend/src/App.jsx` with the general-company demo screen, test input form, summary cards, valid combination list, rejected combination list, details panel, loading/error/empty states, mock-data indicator, money formatting, and `계산 불가` handling for null amounts.
- Updated `match_agent_v0.8/match_agent_v0.8/frontend/src/styles.css` with scoped demo screen styles using existing panel, metric-card, sidebar, and button patterns.
- Added `match_agent_v0.8/match_agent_v0.8/frontend/src/services/recommendationService.js` as the UI-facing service interface.
- Added `match_agent_v0.8/match_agent_v0.8/frontend/src/services/mockRecommendationAdapter.js` as the current adapter because no callable backend recommendation API endpoint or frontend API pattern exists yet.
- Added `match_agent_v0.8/match_agent_v0.8/test_frontend_recommendation_demo.py` to verify service-layer usage, valid/rejected mock result visibility, null amount display, evidence exposure, and absence of forbidden UI wording in frontend demo files.
- Updated `docs/ARCHITECTURE.md` with the frontend demo integration boundary and adapter-swap structure.
- Updated `docs/TEST_SCENARIOS.md` with demo screen verification scenarios.
- Data boundary: the frontend does not reimplement eligibility, amount, combination, net-cost, optimizer, or ranking logic. It only formats amounts and renders the combination amount summary-shaped response.
- UI wording rule: the screen uses comparison wording such as `육아휴직 지원금 조합 비교`, `지원금 조합 비교`, and `가장 높은 총지원금`; it does not present results as an optimal recommendation.
- Test result: `python test_frontend_recommendation_demo.py` passed.
- Frontend build result: `npm.cmd run build` in `match_agent_v0.8/match_agent_v0.8/frontend` passed.
- Verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode limited` passed.
- Git check: `git rev-parse --show-toplevel` failed because this workspace is not a Git repository, so `git diff --check` was not applicable.
- Updated `tasks/feature_list.json` by adding only `general-company-recommendation-demo-screen` as `passing`.
- Remaining issue: the demo uses mock data until a real recommendation API adapter exists; limited verification still skips DB-dependent tests by design: `test_db_connection.py`, `test_policy_load.py`, `test_recommendation_history_service.py`.

## 2026-06-08 Recommendation Smoke Runner

- Scope: added one backend recommendation smoke runner only. No frontend screen, mock adapter, API endpoint, DB structure, existing calculation logic, combination generation logic, or support formula was changed.
- Read first: `AGENTS.md`, `docs/POLICY_SCHEMA.md`, `docs/RULE_ENGINE.md`, `docs/RECOMMENDATION_RULES.md`, `docs/TEST_SCENARIOS.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Added `scripts/run_recommendation_smoke.py`.
- Added test-only smoke fixtures: `data/smoke_scenarios/base.json`, `data/smoke_scenarios/bonus.json`, `data/smoke_scenarios/capped.json`, `data/smoke_scenarios/conflict.json`, and `data/smoke_scenarios/requires.json`.
- Runner behavior: loads a scenario fixture, calls existing approved-policy calculation services in sequence, normalizes policy calculation results, generates valid/rejected policy combinations, summarizes valid combination amounts, prints JSON to the terminal, and writes `output/smoke/{scenario}.json`.
- Existing features reused: approved policy gate, condition evaluation, `monthly_fixed`, `period_tiered`, `conditional_bonus`, standardized policy calculation results, `mutually_exclusive` conflict rejection, `requires` violation rejection, valid policy combination generation, and combination total support summarization.
- Fixture boundary: every fixture includes `TEST FIXTURE ONLY` notice and does not represent real policy data.
- Smoke command result: `python scripts/run_recommendation_smoke.py --scenario base` passed and wrote `output/smoke/base.json`; total subsidy amount was `400000`.
- Smoke command result: `python scripts/run_recommendation_smoke.py --scenario bonus` passed and wrote `output/smoke/bonus.json`; period-tiered base was `3600000`, conditional bonus was `150000`, and total subsidy amount was `3750000`.
- Smoke command result: `python scripts/run_recommendation_smoke.py --scenario capped` passed and wrote `output/smoke/capped.json`; requested `9` months was capped to `6` eligible months and total subsidy amount was `600000`.
- Smoke command result: `python scripts/run_recommendation_smoke.py --scenario conflict` passed and wrote `output/smoke/conflict.json`; valid single-policy combinations were summarized at `400000` and `320000`, and the pair was rejected with `mutually_exclusive`.
- Smoke command result: `python scripts/run_recommendation_smoke.py --scenario requires` passed and wrote `output/smoke/requires.json`; no valid combination was produced and the dependent policy combination was rejected with `requires`.
- Smoke command result: `python scripts/run_recommendation_smoke.py` passed and wrote all five output JSON files.
- Output files confirmed: `output/smoke/base.json`, `output/smoke/bonus.json`, `output/smoke/capped.json`, `output/smoke/conflict.json`, and `output/smoke/requires.json`.
- Verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode limited` passed. It ran the limited Python test set and the frontend build successfully.
- Remaining issue: limited verification still skips DB-dependent tests by design: `test_db_connection.py`, `test_policy_load.py`, `test_recommendation_history_service.py`.

## 2026-06-08 Demo Acceptance Verification Harness

- Scope: added automatic verification harnesses only. No backend calculation formula, policy combination logic, frontend UI structure, API endpoint, database schema, or `mockRecommendationAdapter` display data was changed.
- Read first: `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/POLICY_SCHEMA.md`, `docs/RULE_ENGINE.md`, `docs/RECOMMENDATION_RULES.md`, `docs/TEST_SCENARIOS.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Existing E2E tool check: no Playwright/Cypress/E2E configuration existed in the frontend package before this work.
- Installed frontend dev dependency: `npm.cmd install -D @playwright/test`.
- Installed browser binary: `npx.cmd playwright install chromium`.
- Reason for dependency: the requested verification must load `/company/recommendation-demo` in a real browser, click the support-check button, assert visible UI output, verify forbidden wording is absent, and save a screenshot.
- Added backend acceptance fixtures: `data/acceptance_scenarios/base.json`, `data/acceptance_scenarios/bonus.json`, `data/acceptance_scenarios/capped.json`, `data/acceptance_scenarios/conflict.json`, and `data/acceptance_scenarios/requires.json`.
- Added backend acceptance runner: `scripts/run_recommendation_acceptance.py`. It uses the same existing services as the smoke runner and compares expected values with actual values for policy IDs, valid/rejected combination counts, amount totals, rejection codes, evidence snippets, and calculation steps.
- Added frontend E2E config and test: `match_agent_v0.8/match_agent_v0.8/frontend/playwright.config.js` and `match_agent_v0.8/match_agent_v0.8/frontend/e2e/recommendation-demo.spec.js`.
- Added report writer: `scripts/write_verification_report.py`, producing `output/verification/latest-report.md`.
- Updated `scripts/verify.ps1` and `scripts/verify.sh` with `demo` and `acceptance` modes while preserving existing `limited` and `full` behavior.
- Backend acceptance result: `python scripts/run_recommendation_acceptance.py` passed and wrote `output/verification/backend-report.json`.
- Backend scenario results: `base` total `400000`; `bonus` base `3600000`, bonus `150000`, total `3750000`; `capped` total `600000`; `conflict` valid totals `400000` and `320000` with one `mutually_exclusive` rejection; `requires` no valid summary with one `requires` rejection.
- Frontend build result: `npm.cmd run build` passed.
- Frontend E2E result: `npm.cmd run test:e2e` passed.
- Screenshot generated: `output/verification/frontend-screenshot.png`.
- Frontend JSON report generated: `output/verification/frontend-report.json`.
- Demo verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode demo` passed and wrote `output/verification/latest-report.md`.
- Remaining issue: limited verification still skips DB-dependent tests by design: `test_db_connection.py`, `test_policy_load.py`, `test_recommendation_history_service.py`.

## 2026-06-08 Employer Net Cost Acceptance Extension

- Scope: extended the existing employer net-cost calculation feature with acceptance verification only. No UI, API, DB structure, real policy data, allowed_with exception handling, optimal-combination selection, ranking, cost inference, existing policy calculation formula, existing standard result structure, existing combination generation, or existing amount summarization logic was changed.
- Read first: `AGENTS.md`, `docs/POLICY_SCHEMA.md`, `docs/RECOMMENDATION_RULES.md`, `docs/TEST_SCENARIOS.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Analyzed before change: `match_agent_v0.8/match_agent_v0.8/services/combination_amount_summarizer.py`, `match_agent_v0.8/match_agent_v0.8/test_combination_amount_summarizer.py`, `scripts/run_recommendation_acceptance.py`, `data/acceptance_scenarios`, `scripts/verify.ps1`, and `docs/RECOMMENDATION_RULES.md`.
- Existing implementation confirmed: `match_agent_v0.8/match_agent_v0.8/services/employer_net_cost_calculator.py` already provides `calculate_employer_net_costs(summarized_combinations, employer_cost_items)` and reuses summarized combinations without recalculating subsidy totals.
- Existing unit coverage confirmed: `match_agent_v0.8/match_agent_v0.8/test_employer_net_cost_calculator.py` covers no-cost input, global costs, policy-specific costs, multi-policy AND costs, non-applicable costs, multiple cost sum, invalid amounts, missing/duplicate cost IDs, missing applies-to normalization, negative net cost, and regression tests.
- Added `data/acceptance_scenarios/employer_net_cost.json` with test-only policies and explicit `employer_cost_items`.
- Updated `scripts/run_recommendation_acceptance.py` so scenarios with `input.employer_cost_items` call the existing net-cost calculator after `summarize_combination_amounts`.
- Acceptance now compares `total_employer_cost`, `net_employer_cost`, and applied cost item IDs in addition to existing subsidy and combination expectations.
- Acceptance result: `python scripts/run_recommendation_acceptance.py --scenario employer_net_cost` passed. Expected and actual employer costs were `[1000, 1700, 2200]`; net employer costs were `[600, 1380, 1480]`.
- Acceptance regression result: `python scripts/run_recommendation_acceptance.py` passed for `base`, `bonus`, `capped`, `conflict`, `requires`, and `employer_net_cost`.
- Documentation updated in `docs/RECOMMENDATION_RULES.md` and `docs/TEST_SCENARIOS.md`.
- Demo verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode demo` passed and wrote `output/verification/latest-report.md`.
- Limited verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode limited` passed.
- Git check: `git rev-parse --show-toplevel` failed because this workspace is not a Git repository, so `git diff --check` was skipped.
- Remaining issue: limited verification still skips DB-dependent tests by design: `test_db_connection.py`, `test_policy_load.py`, `test_recommendation_history_service.py`.

## 2026-06-08 Employer Net Cost Optimal Combination Selection

- Scope: implemented one optimal-combination selector based on existing employer net-cost results only. No UI, API, DB structure, real policy data, `allowed_with` exception handling, LLM explanation generation, frontend mock adapter change, policy amount formula change, combination generation change, amount summarization change, or employer net-cost recalculation was performed.
- Read first: `AGENTS.md`, `docs/POLICY_SCHEMA.md`, `docs/RECOMMENDATION_RULES.md`, `docs/TEST_SCENARIOS.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Analyzed before change: `match_agent_v0.8/match_agent_v0.8/services/employer_net_cost_calculator.py`, `match_agent_v0.8/match_agent_v0.8/test_employer_net_cost_calculator.py`, `scripts/run_recommendation_acceptance.py`, `data/acceptance_scenarios/employer_net_cost.json`, and `docs/RECOMMENDATION_RULES.md`.
- Added `match_agent_v0.8/match_agent_v0.8/services/optimal_combination_selector.py`.
- Added `match_agent_v0.8/match_agent_v0.8/test_optimal_combination_selector.py`.
- Added `data/acceptance_scenarios/optimal_combination.json` with test-only policy fixtures and explicit employer cost items.
- Updated `scripts/run_recommendation_acceptance.py` so scenarios with employer net-cost results can call `select_optimal_combination` and compare recommended policy IDs, recommended net employer cost, recommended total subsidy amount, and alternative policy IDs.
- Updated `docs/RECOMMENDATION_RULES.md` with selection boundaries, validation rules, fixed recommendation reasons, and deterministic tie-break order.
- Updated `docs/TEST_SCENARIOS.md` with optimal-combination selector scenarios and the `optimal_combination` backend acceptance scenario.
- Updated `tasks/feature_list.json` by adding only `employer-net-cost-optimal-combination-selection` as `passing` after verification passed.
- Selection input: `cost_calculated_combinations` from `calculate_employer_net_costs`; `rejected_combinations` are preserved but not used as candidates.
- Selection order: `net_employer_cost` ascending, `total_subsidy_amount` descending, included policy count ascending, then `policy_ids` lexicographic order.
- Recommendation reason rule: rank 1 uses `사업주 순비용이 가장 낮은 조합입니다.`; alternatives use `비교 가능한 대안 조합입니다.`; tie-breaks are recorded in `tie_break_applied` and appended to the reason.
- Test result: `python test_optimal_combination_selector.py` passed.
- Acceptance single scenario result: `python scripts\run_recommendation_acceptance.py --scenario optimal_combination` passed; recommended policy IDs were `["smoke-optimal-a"]`, recommended net employer cost was `600`, and the highest subsidy combination `["smoke-optimal-a", "smoke-optimal-b"]` remained an alternative because its net employer cost was `1480`.
- Acceptance regression result: `python scripts\run_recommendation_acceptance.py` passed for `base`, `bonus`, `capped`, `conflict`, `requires`, `employer_net_cost`, and `optimal_combination`.
- Demo verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode demo` passed and wrote `output/verification/latest-report.md`.
- Limited verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode limited` passed.
- Git check: `git diff --check` passed; Git reported only CRLF conversion warnings for touched text files.
- Remaining issue: limited verification still skips DB-dependent tests by design: `test_db_connection.py`, `test_policy_load.py`, `test_recommendation_history_service.py`.

## 2026-06-08 Demo Recommendation API Adapter

- Scope: implemented one minimal demo recommendation API and frontend API adapter only. No DB schema change, real policy DB connection, recommendation history storage, login, permissions, signup, onboarding, labor-partner screen, document management, `allowed_with` exception handling, production deployment behavior, existing calculation formula change, combination generation change, employer net-cost logic change, optimal selection logic change, or frontend mock adapter deletion was performed.
- Read first: `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/POLICY_SCHEMA.md`, `docs/RULE_ENGINE.md`, `docs/RECOMMENDATION_RULES.md`, `docs/TEST_SCENARIOS.md`, `docs/DEVELOPMENT_SETUP.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Existing API server structure analysis: no FastAPI, Flask, `APIRouter`, `@app.route`, uvicorn, or existing HTTP API server structure was found, so no API framework was added. A minimal local demo API server was implemented with Python standard library `http.server`.
- Added orchestration service: `match_agent_v0.8/match_agent_v0.8/services/demo_recommendation_orchestrator.py`.
- Added local API server entry point: `scripts/run_demo_recommendation_api.py`.
- Added backend API tests: `match_agent_v0.8/match_agent_v0.8/test_demo_recommendation_api.py`.
- Added frontend API adapter: `match_agent_v0.8/match_agent_v0.8/frontend/src/services/apiRecommendationAdapter.js`.
- Updated frontend adapter selection: `match_agent_v0.8/match_agent_v0.8/frontend/src/services/recommendationService.js` now defaults to mock and switches to API with `VITE_RECOMMENDATION_ADAPTER=api`.
- Updated demo screen: `match_agent_v0.8/match_agent_v0.8/frontend/src/App.jsx` displays `recommended_combination`, keeps alternative/rejected lists, shows API/mock adapter status, and shows `데모 정책 데이터 기준 결과입니다.` when API meta marks demo fixture data.
- Updated Playwright E2E: `match_agent_v0.8/match_agent_v0.8/frontend/e2e/recommendation-demo.spec.js` now supports both default mock and API adapter modes.
- Added frontend adapter tests: `match_agent_v0.8/match_agent_v0.8/test_api_recommendation_adapter.py`.
- Updated docs: `docs/ARCHITECTURE.md`, `docs/DEVELOPMENT_SETUP.md`, and `docs/TEST_SCENARIOS.md`.
- Updated `tasks/feature_list.json` by adding only `demo-recommendation-api-adapter` as `passing` after verification passed.
- API endpoint: `POST /api/demo/recommendations/calculate`.
- Request fields: `company`, `employee`, `leave_event`, and optional `employer_cost_items`.
- Response fields: `recommended_combination`, `alternative_combinations`, `rejected_combinations`, `errors`, and `meta`.
- Demo meta: `meta.data_source == "demo_fixture"` and `meta.is_demo == true`.
- API orchestration order: validate request, load test-only `optimal_combination` fixture, calculate approved policies, normalize policy calculation results, generate valid/rejected combinations, summarize combination amounts, calculate explicit employer net costs, select optimal combination, and return the result.
- Direct API server check result: started `python scripts\run_demo_recommendation_api.py`, posted to `http://127.0.0.1:8000/api/demo/recommendations/calculate`, and received `recommended_combination.policy_ids == ["smoke-optimal-a"]`, `net_employer_cost == 600`, `meta.is_demo == true`, and `meta.data_source == "demo_fixture"`.
- API adapter mode E2E result: started the demo API server, built the frontend with `VITE_RECOMMENDATION_ADAPTER=api` and `VITE_RECOMMENDATION_API_BASE_URL=http://127.0.0.1:8000`, then ran `npm.cmd run test:e2e`; Playwright passed.
- Backend acceptance result: `python scripts\run_recommendation_acceptance.py` passed for `base`, `bonus`, `capped`, `conflict`, `requires`, `employer_net_cost`, and `optimal_combination`.
- Demo verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode demo` passed and wrote `output/verification/latest-report.md`.
- Limited verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode limited` passed.
- Git check: `git diff --check` passed; Git reported only CRLF conversion warnings for touched text files.
- Remaining issue: this is demo-fixture-only API integration. It does not connect to the real policy database or store recommendation logs. Limited verification still skips DB-dependent tests by design: `test_db_connection.py`, `test_policy_load.py`, `test_recommendation_history_service.py`.

## 2026-06-13 Rule Engine Domain Adapter

- Scope: implemented one general-company domain-to-rule-engine adapter only. No policy formula, policy combination generation, amount summarization, employer net-cost calculation, optimal selection, frontend mock adapter, API route shape, DB schema, recommendation history, login, onboarding, labor-partner flow, or real policy DB connection was changed.
- Read first: `AGENTS.md`, `docs/RULE_ENGINE.md`, `docs/ARCHITECTURE.md`, `tasks/feature_list.json`, and the current demo API orchestration/tests.
- Added `match_agent_v0.8/match_agent_v0.8/services/rule_engine_domain_adapter.py`.
- Added `match_agent_v0.8/match_agent_v0.8/test_rule_engine_domain_adapter.py`.
- Updated `match_agent_v0.8/match_agent_v0.8/services/demo_recommendation_orchestrator.py` to call `adapt_general_company_request_to_rule_engine` instead of building `rule_input` inline.
- Updated `docs/ARCHITECTURE.md`, `docs/RULE_ENGINE.md`, and `docs/TEST_SCENARIOS.md` with the adapter boundary and scenarios.
- Updated `tasks/feature_list.json` by converting `rule-engine-domain-adapter` from `not_started` to `passing`.
- Adapter input: API payload sections `company`, `employee`, and `leave_event`.
- Adapter output: `rule_input`, `requested_months`, and structured `errors`.
- Current mapping: `company.size`, `company.has_replacement_worker`, and `employee.leave_type`.
- Precedence rules: `leave_event.leave_type` overrides `employee.leave_type`; `leave_event.has_replacement_worker` overrides `company.has_replacement_worker`.
- Requested month rules: explicit positive `leave_event.requested_months` is used when present; otherwise inclusive `start_date` and `end_date` are converted to months; missing dates use the current demo default of `4`.
- Error rules: end date before start date and non-positive explicit requested months return structured errors.
- Test result: `python test_rule_engine_domain_adapter.py` passed.
- API regression result: `python test_demo_recommendation_api.py` passed.
- Backend acceptance result: `python scripts\run_recommendation_acceptance.py` passed.
- Demo verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode demo` passed and wrote `output/verification/latest-report.md`.
- Limited verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode limited` passed.
- Git check: `git diff --check` passed; Git reported only CRLF conversion warnings for touched text files.
- Remaining issue: the adapter currently covers the general-company demo request shape only. DB-dependent tests still skip in limited mode: `test_db_connection.py`, `test_policy_load.py`, `test_recommendation_history_service.py`.

## 2026-06-13 Approved Policy Loader Abstraction

- Scope: implemented one approved-policy loader boundary only. No calculation formula, combination generation, employer net-cost calculation, optimal selection, frontend UI, API route shape, DB schema, recommendation history, login, onboarding, labor-partner flow, or real policy DB connection was changed.
- Read first: `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/POLICY_SCHEMA.md`, `docs/RULE_ENGINE.md`, `docs/RECOMMENDATION_RULES.md`, `docs/TEST_SCENARIOS.md`, `docs/analysis/CURRENT_STATE.md`, `docs/analysis/GAP_ANALYSIS.md`, `docs/analysis/IMPLEMENTATION_ORDER.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Added `match_agent_v0.8/match_agent_v0.8/services/approved_policy_loader.py`.
- Added `match_agent_v0.8/match_agent_v0.8/test_approved_policy_loader.py`.
- Updated `match_agent_v0.8/match_agent_v0.8/services/demo_recommendation_orchestrator.py` to load candidate policies through `load_approved_policies()` instead of reading the demo fixture directly.
- Updated `match_agent_v0.8/match_agent_v0.8/test_demo_recommendation_api.py` to assert the `meta.policy_source` demo fixture boundary.
- Updated `docs/ARCHITECTURE.md`, `docs/POLICY_SCHEMA.md`, `docs/TEST_SCENARIOS.md`, and `docs/DEVELOPMENT_SETUP.md`.
- Updated `tasks/feature_list.json` by adding only `approved-policy-loader-abstraction` as `passing`.
- Current loader source: `demo_fixture` only.
- Current fixture: `data/acceptance_scenarios/optimal_combination.json`.
- Approval gate: only policies with `review_status == "approved"` are returned to recommendation orchestration.
- Structured loader errors: unsupported sources return `unsupported_policy_source`; missing fixtures return `demo_fixture_not_found`.
- Test result: `python test_approved_policy_loader.py` passed.
- API regression result: `python test_demo_recommendation_api.py` passed.
- Backend acceptance result: `python scripts\run_recommendation_acceptance.py` passed.
- Demo verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode demo` passed and wrote `output/verification/latest-report.md`.
- Limited verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode limited` passed.
- Git check: `git diff --check` passed; Git reported only CRLF conversion warnings for touched text files.
- Remaining issue: this loader still supports only the demo fixture source. A real approved-policy DB source is not implemented yet, and limited verification still skips DB-dependent tests: `test_db_connection.py`, `test_policy_load.py`, `test_recommendation_history_service.py`.

## 2026-06-13 Policy DB Source Placeholder

- Scope: added one safety placeholder for the future policy DB loader source only. No real DB connection, DB query, DB schema, policy calculation formula, combination generation, employer net-cost calculation, optimal selection, frontend UI, API route shape, recommendation history, login, onboarding, or labor-partner flow was changed.
- Read first: `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/POLICY_SCHEMA.md`, `docs/RECOMMENDATION_RULES.md`, `docs/TEST_SCENARIOS.md`, `tasks/feature_list.json`, and the existing approved policy loader/tests.
- Updated `match_agent_v0.8/match_agent_v0.8/services/approved_policy_loader.py` so `source="policy_db"` is recognized as a reserved future source and returns no policies with a structured `policy_db_source_not_configured` error.
- Kept unknown sources separate: unrecognized source names still return `unsupported_policy_source`.
- Updated `match_agent_v0.8/match_agent_v0.8/test_approved_policy_loader.py` with policy DB placeholder and unknown source coverage.
- Updated `docs/ARCHITECTURE.md`, `docs/POLICY_SCHEMA.md`, `docs/TEST_SCENARIOS.md`, and `docs/DEVELOPMENT_SETUP.md` to document that `policy_db` is reserved but not configured.
- Updated `tasks/feature_list.json` by adding only `policy-db-source-placeholder` as `passing`.
- Test result: `python test_approved_policy_loader.py` passed.
- API regression result: `python test_demo_recommendation_api.py` passed.
- Backend acceptance result: `python scripts\run_recommendation_acceptance.py` passed.
- Demo verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode demo` passed and wrote `output/verification/latest-report.md`.
- Limited verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode limited` passed.
- Git check: `git diff --check` passed; Git reported only CRLF conversion warnings for touched text files.
- Remaining issue: real approved-policy DB loading is still not implemented. Limited verification still skips DB-dependent tests: `test_db_connection.py`, `test_policy_load.py`, `test_recommendation_history_service.py`.

## 2026-06-13 Policy DB Approved Policy Loader

- Scope: implemented one `source="policy_db"` approved-policy loader feature only. No recommendation calculation formula, condition evaluator, combination generator, employer net-cost calculator, optimal selector, frontend UI, mock adapter, real policy registration, LLM extraction, admin review screen, recommendation history storage, or API route shape was changed.
- Read first: `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/POLICY_SCHEMA.md`, `docs/RULE_ENGINE.md`, `docs/RECOMMENDATION_RULES.md`, `docs/TEST_SCENARIOS.md`, `docs/DEVELOPMENT_SETUP.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Analyzed before change: `services/approved_policy_loader.py`, `test_approved_policy_loader.py`, `test_db_connection.py`, `test_policy_load.py`, `test_recommendation_history_service.py`, `services/demo_recommendation_orchestrator.py`, `database/db.py`, `database/models.py`, `database/crud.py`, `requirements-dev.txt`, and `.env.example`.
- Existing DB structure analysis: `incentives` and `policy_versions` already store policy metadata and versioned JSON, but they do not include an `is_active` column needed by this task. Added a minimal `subsidy_policies` migration for the requested approved+active loader path instead of altering existing tables.
- Added `database/migrations/001_create_subsidy_policies.sql`.
- Updated `match_agent_v0.8/match_agent_v0.8/services/approved_policy_loader.py` so `source="policy_db"` reads from PostgreSQL `subsidy_policies`.
- Policy DB environment variable: `INCENTDOC_POLICY_DB_URL`.
- Query condition: `review_status = 'approved'` and `is_active = TRUE`.
- Returned data: successful rows return `policy_json` objects unchanged to the existing recommendation engine.
- Review validation: DB column `review_status` must match `policy_json.review_status`; mismatches return `policy_db_review_status_mismatch` and are not corrected.
- Error codes implemented: `policy_db_connection_failed`, `policy_db_table_not_found`, `approved_policy_not_found`, `policy_db_invalid_json`, `policy_db_review_status_mismatch`, and existing `unsupported_policy_source`.
- Updated `match_agent_v0.8/match_agent_v0.8/test_approved_policy_loader.py` with fake-connection coverage for approved active loading, exclusion of `needs_review`, `deprecated`, and inactive rows, no approved result, connection failure, table missing, invalid JSON, review-status mismatch, unknown source, and demo fixture regression.
- Added optional real DB assertion in `test_approved_policy_loader.py`; it runs only when `INCENTDOC_RUN_POLICY_DB_INTEGRATION=true` and `INCENTDOC_POLICY_DB_URL` are configured.
- Updated `.env.example` with `INCENTDOC_POLICY_DB_URL` and `INCENTDOC_RUN_POLICY_DB_INTEGRATION`.
- Updated docs: `docs/ARCHITECTURE.md`, `docs/POLICY_SCHEMA.md`, `docs/TEST_SCENARIOS.md`, and `docs/DEVELOPMENT_SETUP.md`.
- Updated `tasks/feature_list.json` by adding only `policy-db-approved-policy-loader` as `passing`.
- Test result: `python test_approved_policy_loader.py` passed. Real DB integration assertion was skipped because `INCENTDOC_RUN_POLICY_DB_INTEGRATION` and `INCENTDOC_POLICY_DB_URL` were not configured in this session.
- API regression result: `python test_demo_recommendation_api.py` passed.
- Backend acceptance result: `python scripts\run_recommendation_acceptance.py` passed.
- Demo verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode demo` passed and wrote `output/verification/latest-report.md`.
- Limited verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode limited` passed.
- Full verification result: skipped because the current environment does not have `INCENTDOC_RUN_POLICY_DB_INTEGRATION=true` and `INCENTDOC_POLICY_DB_URL` configured for a dedicated test PostgreSQL database.
- Remaining issue: real DB integration was not exercised locally; apply `database/migrations/001_create_subsidy_policies.sql` to a dedicated test database and set the policy DB environment variables before running full DB verification.

## 2026-06-13 Policy Loader Test Environment Isolation

- Scope: fixed only `test_approved_policy_loader.py` environment variable isolation for the no-DB-URL error test. No loader logic, DB schema, recommendation calculation, frontend, or mock adapter code was changed.
- Root cause: `test_policy_db_connection_failed_without_url()` passed `db_url=""`, and the loader intentionally falls back to `INCENTDOC_POLICY_DB_URL` when the explicit URL is falsy. If the parent PowerShell session had that environment variable set, the test no longer represented the no-URL case.
- Added `temporary_env()` context manager to remove selected environment variables during a test and restore their previous values afterward.
- Isolated `INCENTDOC_POLICY_DB_URL` and `INCENTDOC_RUN_POLICY_DB_INTEGRATION` during `test_policy_db_connection_failed_without_url()`.
- Checked other policy DB error tests: they pass explicit non-empty `db_url` values and are not affected by external `INCENTDOC_POLICY_DB_URL`. The optional real DB integration test still runs only when `INCENTDOC_RUN_POLICY_DB_INTEGRATION=true`.
- Test result: `python test_approved_policy_loader.py` passed.
- Environment-set regression result: with `INCENTDOC_POLICY_DB_URL=postgresql://example-set-in-shell` and `INCENTDOC_RUN_POLICY_DB_INTEGRATION=false`, `python test_approved_policy_loader.py` passed.
- Git check: `git diff --check` passed; Git reported only CRLF conversion warnings for touched text files.
- Remaining issue: real DB integration is still intentionally gated behind `INCENTDOC_RUN_POLICY_DB_INTEGRATION=true` and was not executed in this fix.

## 2026-06-13 Demo API Policy Source Selection

- Scope: implemented only the minimal `policy_source` selection path for the existing demo recommendation API and frontend API adapter. No calculation formulas, rule engine behavior, combination generation, employer net-cost calculation, optimal selector, DB schema, frontend screen structure, or mock adapter data were changed.
- Read first: `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/POLICY_SCHEMA.md`, `docs/RECOMMENDATION_RULES.md`, `docs/TEST_SCENARIOS.md`, `docs/DEVELOPMENT_SETUP.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Updated `match_agent_v0.8/match_agent_v0.8/services/demo_recommendation_orchestrator.py` so request payloads may include `policy_source` with allowed values `demo_fixture` or `policy_db`; missing values default to `demo_fixture`.
- The API now passes the selected source into `load_approved_policies(source=...)`, returns `meta.data_source`, `meta.is_demo`, `meta.policy_source`, and `meta.loaded_policy_count`, and returns policy DB loader errors without falling back to fixtures.
- Updated `match_agent_v0.8/match_agent_v0.8/test_demo_recommendation_api.py` with demo fixture regression, fake policy DB success, policy DB error no-fallback, and unsupported source coverage.
- Updated `match_agent_v0.8/match_agent_v0.8/frontend/src/services/apiRecommendationAdapter.js` so API mode sends `policy_source` from input, `policySource`, or `VITE_RECOMMENDATION_POLICY_SOURCE`, defaulting to `demo_fixture`.
- Updated `match_agent_v0.8/match_agent_v0.8/frontend/src/App.jsx` to show `데모 정책 데이터 기준 결과입니다.` for demo fixture and `Supabase 테스트 정책 DB 기준 결과입니다.` for policy DB responses.
- Added `database/seeds/001_seed_subsidy_policies_test_fixtures.sql` with calculation-capable, test-only approved active rows for `smoke-optimal-a` and `smoke-optimal-b`.
- Updated `.env.example`, `docs/ARCHITECTURE.md`, `docs/DEVELOPMENT_SETUP.md`, and `docs/TEST_SCENARIOS.md`.
- Updated `tasks/feature_list.json` by adding only `demo-api-policy-source-selection` as `passing`.
- Direct test results: `python test_demo_recommendation_api.py` passed; `python test_api_recommendation_adapter.py` passed.
- Backend acceptance result: `python scripts\run_recommendation_acceptance.py` passed.
- Demo verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode demo` passed; frontend E2E passed and wrote `output/verification/latest-report.md`.
- Full verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode full` passed with 269 Python tests and frontend build.
- Policy DB direct check: this shell did not have `INCENTDOC_POLICY_DB_URL` configured, so live Supabase calculation was not executed. A `policy_source=policy_db` API orchestration call returned `policy_db_connection_failed` with `meta.data_source=policy_db`, `is_demo=false`, and `loaded_policy_count=0`, confirming no fixture fallback.
- Git check: `git diff --check` passed; Git reported only CRLF conversion warnings for touched text files.
- Remaining issue: to see real Supabase policy DB results in the browser, configure `INCENTDOC_POLICY_DB_URL`, apply `database/migrations/001_create_subsidy_policies.sql`, optionally apply `database/seeds/001_seed_subsidy_policies_test_fixtures.sql`, run the API server, and start the frontend with `VITE_RECOMMENDATION_ADAPTER=api` and `VITE_RECOMMENDATION_POLICY_SOURCE=policy_db`.

## 2026-06-13 FastAPI Demo Recommendation Server

- Scope: added only the minimal FastAPI HTTP server layer for the existing recommendation orchestration. No calculation formula, Rule Engine behavior, policy loading logic, combination generation, employer net-cost calculation, optimal selection, DB schema, frontend UI, or mock adapter code was changed.
- Read first: `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/DEVELOPMENT_SETUP.md`, `docs/TEST_SCENARIOS.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Added `match_agent_v0.8/match_agent_v0.8/api_server.py` with `app = FastAPI(title="Incentdoc Demo Recommendation API")`.
- Added `GET /health`, returning `{"status": "ok"}`.
- Added `POST /api/demo/recommendations/calculate`, passing the request JSON body directly into `run_demo_recommendation_pipeline(...)` and returning the orchestration result unchanged.
- Added local-only CORS origins: `http://127.0.0.1:5173` and `http://localhost:5173`.
- Replaced `scripts/run_demo_recommendation_api.py` with a uvicorn wrapper around `api_server:app`.
- Added `match_agent_v0.8/match_agent_v0.8/test_api_server.py` covering health, demo fixture POST, policy DB POST success-or-structured-error behavior, unsupported `policy_source`, and CORS.
- Updated `requirements-dev.txt` with `fastapi` and `uvicorn`; both were already available in the current environment.
- Updated docs: `docs/ARCHITECTURE.md`, `docs/DEVELOPMENT_SETUP.md`, and `docs/TEST_SCENARIOS.md`.
- Updated `tasks/feature_list.json` by adding only `fastapi-demo-recommendation-server` as `passing`.
- Direct test results: `python test_api_server.py` passed; `python test_demo_recommendation_api.py` passed.
- Backend acceptance result: `python scripts\run_recommendation_acceptance.py` passed.
- Actual HTTP check: started `python -m uvicorn api_server:app --host 127.0.0.1 --port 8000` from `match_agent_v0.8/match_agent_v0.8`; `GET /health` returned `{"status":"ok"}`.
- Actual demo fixture API check: `POST /api/demo/recommendations/calculate` returned `meta.data_source=demo_fixture` and recommended policy IDs `smoke-optimal-a,smoke-optimal-b`.
- Actual policy DB API check: `POST /api/demo/recommendations/calculate` with `policy_source=policy_db` returned `meta.data_source=policy_db` and a structured `policy_db_connection_failed` error in the direct HTTP check; during full pytest this environment also produced an existing `no_recommendation_candidates` structured error for policy DB data, so the API server test accepts either success or structured non-fixture policy DB errors.
- Full verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode full` passed with 274 Python tests and frontend build.
- Demo verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode demo` passed with frontend build, backend acceptance, Playwright E2E, and `output/verification/latest-report.md`.
- Git check: `git diff --check` passed; Git reported only CRLF conversion warnings for touched text files.
- Remaining issue: policy DB HTTP behavior depends on the configured test DB contents. To return a successful policy DB recommendation rather than a structured policy DB/no-candidate error, seed calculation-capable approved active test rows with `database/seeds/001_seed_subsidy_policies_test_fixtures.sql`.

## 2026-06-14 Policy Extraction Evaluation Harness

- Scope: added only an offline policy structure evaluation harness for assumed LLM extraction outputs. No live LLM API, recommendation engine, Rule Engine, API behavior, DB schema, frontend UI, policy loading, combination generation, net-cost calculation, or optimal selection code was changed.
- Read first: `AGENTS.md`, `docs/POLICY_SCHEMA.md`, `docs/TEST_SCENARIOS.md`, `tasks/feature_list.json`, and `tasks/progress.md`; also reviewed `docs/ARCHITECTURE.md` and `docs/DEVELOPMENT_SETUP.md` before documentation updates.
- Added `match_agent_v0.8/match_agent_v0.8/services/policy_structure_evaluator.py`.
- Added `match_agent_v0.8/match_agent_v0.8/test_policy_structure_evaluator.py`.
- Added `scripts/run_policy_extraction_eval.py`.
- Added five test-only fixtures under `data/policy_extraction_eval/`: `monthly_fixed`, `period_tiered`, `conditional_bonus`, `combination_rules`, and `error_candidate`.
- Candidate fixtures remain `review_status="needs_review"`; the evaluator reports `invalid_review_status` if a candidate is already `approved`.
- Evaluation rules: array order alone is ignored; conditions are compared by `condition_id`; tiers by `start_month` and `end_month`; combination rules by `rule_id`; evidence snippets are exact source-backed strings.
- Score rule: `score = passed_checks / total_checks * 100`; any structured error makes that policy result `passed=false`.
- Error types implemented: `missing_field`, `value_mismatch`, `type_mismatch`, `missing_condition`, `operator_mismatch`, `amount_mismatch`, `duration_mismatch`, `tier_mismatch`, `missing_evidence`, `missing_combination_rule`, and `invalid_review_status`.
- Generated reports: `output/policy_extraction_eval/latest-report.json` and `output/policy_extraction_eval/latest-report.md`.
- Evaluation run: `python scripts\run_policy_extraction_eval.py` passed, case count `5`, average score `89.47`. The intentional error fixture scored `47.37` and reported amount, duration, tier, condition, evidence, operator, and combination rule errors.
- Unit test result: `python test_policy_structure_evaluator.py` passed.
- Full verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode full` passed with `285 passed` and frontend build.
- Demo verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode demo` passed with frontend build, backend acceptance, Playwright E2E, and `output/verification/latest-report.md`.
- Git check: `git diff --check` passed; Git reported only CRLF conversion warnings for touched text files.
- Remaining issue: this harness only evaluates static fixtures. Live LLM extraction execution and prompt/model comparison are intentionally not connected yet.

## 2026-06-14 Live LLM Policy Extraction Evaluation

- Scope: added only a live LLM extraction evaluation path over the existing policy extraction eval fixtures. No recommendation engine, Rule Engine, API behavior, DB schema, frontend UI, policy loader, combination generation, net-cost calculation, or optimal selector code was changed.
- Read first: `AGENTS.md`, `docs/POLICY_SCHEMA.md`, `docs/TEST_SCENARIOS.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Added `match_agent_v0.8/match_agent_v0.8/services/policy_extraction_adapter.py` for the adapter interface, result shape, and JSON parse helper.
- Added `match_agent_v0.8/match_agent_v0.8/services/openai_policy_extraction_adapter.py` as the single OpenAI adapter.
- Added `prompts/policy_extraction_v1.md`.
- Added `scripts/run_policy_extraction_llm_eval.py`.
- Added `match_agent_v0.8/match_agent_v0.8/test_policy_extraction_llm_eval.py`.
- Updated `.env.example` with `POLICY_EXTRACTION_MODEL` and `POLICY_EXTRACTION_PROMPT_VERSION`.
- Updated docs: `docs/ARCHITECTURE.md`, `docs/POLICY_SCHEMA.md`, `docs/TEST_SCENARIOS.md`, and `docs/DEVELOPMENT_SETUP.md`.
- Updated `tasks/feature_list.json` by adding only `live-llm-policy-extraction-evaluation` as `passing`.
- Environment variables: `OPENAI_API_KEY`, `POLICY_EXTRACTION_MODEL`, and `POLICY_EXTRACTION_PROMPT_VERSION`.
- Default model: `gpt-4.1-mini`.
- Default prompt version: `policy_extraction_v1`.
- Storage: generated candidates go under `output/policy_extraction_eval/generated/{model}/`; comparison reports go to `output/policy_extraction_eval/model-comparison-report.json` and `.md`.
- Stored execution fields: `case_id`, `model`, `prompt_version`, `raw_response`, `parsed_candidate`, `parse_error`, `elapsed_ms`, `token_usage`, `evaluator_score`, and `evaluator_errors`.
- Review status guard: generated candidates are not corrected or approved. If a candidate returns `review_status="approved"`, the existing evaluator reports `invalid_review_status`.
- API key handling: current shell has no `OPENAI_API_KEY`. Running `python scripts\run_policy_extraction_llm_eval.py` exited with code `2`, printed `OPENAI_API_KEY is required...`, did not print any key value, and wrote an ERROR model comparison report.
- Unit test result: `python test_policy_extraction_llm_eval.py` passed.
- Full verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode full` passed with `291 passed` and frontend build.
- Demo verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode demo` passed with frontend build, backend acceptance, Playwright E2E, and `output/verification/latest-report.md`.
- Git check: `git diff --check` passed; Git reported only CRLF conversion warnings for touched text files.
- Remaining issue: real OpenAI extraction scores were not produced in this environment because `OPENAI_API_KEY` is not configured. Set `OPENAI_API_KEY` and rerun `python scripts\run_policy_extraction_llm_eval.py` to generate per-policy scores.

## 2026-06-14 Policy Extraction Prompt v2 Analysis

- Scope: improved only the policy extraction prompt based on existing v1 LLM evaluation results. No recommendation engine, Rule Engine, API behavior, DB schema, frontend UI, evaluator criteria, expected fixtures, generated candidates, or approval state logic was changed.
- Read first: `AGENTS.md`, `docs/POLICY_SCHEMA.md`, and `tasks/progress.md`.
- Analyzed `output/policy_extraction_eval/model-comparison-report.json`, `prompts/policy_extraction_v1.md`, `data/policy_extraction_eval/`, and `docs/POLICY_SCHEMA.md`.
- v1 baseline result: average score `22.67` across 5 fixtures. Case scores were `monthly_fixed=40.0`, `period_tiered=20.0`, `conditional_bonus=20.0`, `combination_rules=16.67`, and `error_candidate=16.67`.
- v1 error frequencies: `value_mismatch=10`, `missing_field=5`, `missing_evidence=4`, and `missing_combination_rule=2`.
- Representative v1 failures: empty `policy_id` and `policy_name`, unstable support/rule IDs, unsupported schema aliases, incorrect nested structure for tiered and conditional bonus items, and non-exact evidence snippets with fixture labels.
- Added `prompts/policy_extraction_v2.md` while preserving `prompts/policy_extraction_v1.md`.
- v2 prompt changes: explicit fixture ID conventions, canonical field names, alias bans, exact evidence rules, one-item nesting for `period_tiered` and `conditional_bonus`, and strict `combination_rules` structure.
- v2 evaluation command attempted: `python scripts\run_policy_extraction_llm_eval.py --prompt-path prompts\policy_extraction_v2.md --prompt-version policy_extraction_v2 --output-dir output\policy_extraction_eval\v2-run`.
- v2 evaluation result: failed before model execution because `OPENAI_API_KEY` is not configured in the current shell. The failure was recorded at `output/policy_extraction_eval/v2-run/model-comparison-report.json`.
- Comparison reports written: `output/policy_extraction_eval/prompt-v1-v2-comparison-report.json` and `output/policy_extraction_eval/prompt-v1-v2-comparison-report.md`.
- Remaining issue: v2 average score, policy score deltas, and error-type decreases require rerunning the same five fixtures with `OPENAI_API_KEY` configured.

## 2026-06-14 LLM Extraction Repeated Evaluation Summary

- Scope: added only repeated live LLM policy extraction evaluation and comparison reporting. No recommendation engine, Rule Engine, API behavior, DB schema, frontend UI, evaluator criteria, expected fixtures, candidate auto-correction, or approval state logic was changed.
- Read first: `AGENTS.md` and `tasks/progress.md`.
- Updated `scripts/run_policy_extraction_llm_eval.py`.
- Updated `match_agent_v0.8/match_agent_v0.8/test_policy_extraction_llm_eval.py`.
- Added `--runs` so the same prompt can be executed multiple times and each run is saved under a separate run_id directory.
- Added automatic prompt path resolution: `--prompt-version policy_extraction_v2` resolves to `prompts/policy_extraction_v2.md` when `--prompt-path` is not provided.
- Kept explicit `--prompt-path` as the highest-priority prompt selector.
- Added `prompt_file` and `prompt_sha256` to run reports and summary reports.
- Added summary aggregation for average, minimum, and maximum run scores; policy-level score spread; and repeated error-type counts.
- New output structure: `output/policy_extraction_eval/{prompt_version}/{run_id}/`, `output/policy_extraction_eval/{prompt_version}/summary-report.json`, and `output/policy_extraction_eval/{prompt_version}/summary-report.md`.
- Unit test result: `python match_agent_v0.8\match_agent_v0.8\test_policy_extraction_llm_eval.py` passed.
- Repeated evaluation command attempted: `python scripts\run_policy_extraction_llm_eval.py --prompt-version policy_extraction_v2 --runs 3`.
- Repeated evaluation result in this shell: blocked before model execution because `OPENAI_API_KEY` is not configured. The error summary still recorded `prompt_file`, `prompt_sha256`, and `runs=3` at `output/policy_extraction_eval/policy_extraction_v2/summary-report.json`.
- Remaining issue: actual repeated score statistics require rerunning with `OPENAI_API_KEY` configured.

## 2026-06-14 Real Policy Extraction Evaluation Dataset Structure

- Scope: added only the dataset structure and runner selection path for real policy-source LLM extraction evaluation. No recommendation engine, Rule Engine, API behavior, DB schema, frontend UI, evaluator criteria, mock fixtures, candidate auto-correction, Supabase storage, or approval state logic was changed.
- Read first: `AGENTS.md`, `docs/POLICY_SCHEMA.md`, and `tasks/progress.md`.
- Added `data/policy_extraction_real_eval/README.md`.
- Added real evaluation dataset directories: `data/policy_extraction_real_eval/raw_text/`, `data/policy_extraction_real_eval/gold/`, and `data/policy_extraction_real_eval/metadata/`.
- Dataset convention: each case uses matching file stems across `raw_text/{case_id}.txt`, `gold/{case_id}.json`, and `metadata/{case_id}.json`.
- Metadata required fields: `case_id`, `policy_name`, `source_url`, `source_type`, `collected_at`, and `notes`.
- Updated `scripts/run_policy_extraction_llm_eval.py` with `--dataset` support.
- Real dataset output defaults to `output/policy_extraction_real_eval/{prompt_version}/`, keeping it separate from mock fixture reports.
- The runner validates dataset structure, missing gold JSON, missing metadata JSON, required metadata fields, and metadata `case_id` before any OpenAI call.
- Existing mock fixture evaluation remains available through the existing default path and `--fixture-dir`.
- Updated `match_agent_v0.8/match_agent_v0.8/test_policy_extraction_llm_eval.py` with dataset matching and missing-file validation coverage.
- Updated docs: `docs/DEVELOPMENT_SETUP.md` and `docs/TEST_SCENARIOS.md`.
- Updated `tasks/feature_list.json` by adding only `real-policy-extraction-evaluation-dataset` as `passing` after verification passed.
- Unit test result: `python match_agent_v0.8\match_agent_v0.8\test_policy_extraction_llm_eval.py` passed.
- Existing mock evaluation regression: `python scripts\run_policy_extraction_eval.py` passed with 5 cases and average score `89.47`.
- Real dataset command attempted: `python scripts\run_policy_extraction_llm_eval.py --dataset data\policy_extraction_real_eval --prompt-version policy_extraction_v2 --runs 5`.
- Real dataset command result: returned a clear dataset validation error because no real raw text files have been added yet. The error summary was written to `output/policy_extraction_real_eval/policy_extraction_v2/summary-report.json`.
- Remaining issue: add five actual policy source text files, matching human-written gold JSON files, and metadata JSON files before running live real-policy evaluation.

## 2026-06-14 DB Builder Policy Document Extraction Bridge

- Scope: connected documents collected by the existing `db_builder.py` storage structure to the existing live LLM policy extraction adapter only. No db_builder collection flow, analyzer, file_parser, mapping, writer_final, recommendation engine, API, DB schema, frontend, Supabase storage, approved promotion, candidate auto-correction, or evaluator criteria was changed.
- Read first: `AGENTS.md`, `model_설명.txt`, `docs/POLICY_SCHEMA.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Existing structure analysis: `config.py` defines `INCENT_DOCS_ROOT = match_agent_v0.8/match_agent_v0.8/incent_docs` and maps each `incent_key` to `incent_docs/{incent_key}_docs`.
- Existing `db_builder.py` crawl output: URL collection writes `{incent_key}_raw.txt` and `{incent_key}_meta.json`; meta JSON includes `incent_key`, `url`, `crawled_at`, and `content`.
- Existing manual-document behavior: `load_incent_text()` reads files already present in each docs folder and supports pdf, txt, and json; URL `"none"` requires manual files.
- Current `incent_docs` scan result: 12 readable policy documents were found, including crawled raw text files and `incent_field.pdf`.
- Added `match_agent_v0.8/match_agent_v0.8/services/db_builder_policy_document_loader.py`.
- Added `scripts/run_policy_extraction_from_db_builder.py`.
- Added `match_agent_v0.8/match_agent_v0.8/test_db_builder_policy_document_loader.py`.
- Supported input file formats: `.txt`, `.md`, `.json`, `.pdf`, and `.docx`.
- JSON extraction rule: use `content` when present; otherwise serialize the JSON object as source text.
- PDF extraction rule: reuse PyMuPDF text extraction, matching the existing `db_builder.py` dependency.
- DOCX extraction rule: read `word/document.xml` from the docx zip and extract paragraph text with the Python standard library.
- Source metadata rule: sidecar `{stem}_meta.json` or `{incent_key}_meta.json` supplies `url` or `source_url`; sidecar meta files are skipped as standalone extraction documents.
- Candidate source-linking fields: `source_document_id`, `source_url`, and `source_file`.
- Review-status handling: the loader attaches source fields without changing the candidate review status. The script records `invalid_review_status` if a generated candidate is not `needs_review`.
- Output path: `output/policy_extraction_from_db_builder/{document_id}.json`.
- Execution command: `python scripts\run_policy_extraction_from_db_builder.py`.
- Optional single-document command: `python scripts\run_policy_extraction_from_db_builder.py --document-id parental_leave_reduction_support`.
- Unit test result: `python match_agent_v0.8\match_agent_v0.8\test_db_builder_policy_document_loader.py` passed.
- Script no-key check: `python scripts\run_policy_extraction_from_db_builder.py --document-id parental_leave_reduction_support` returned a clear `OPENAI_API_KEY` required error without printing a key.
- Updated `tasks/feature_list.json` by adding only `db-builder-policy-document-extraction-bridge` as `passing` after verification passed.
- Remaining issue: actual LLM extraction from db_builder documents requires `OPENAI_API_KEY`; legacy `.doc` binary Word files are not supported.

## 2026-06-14 DB Builder LLM Candidate Validation Gate

- Scope: added only a schema validation gate for parsed LLM candidates produced from db_builder policy documents. No recommendation engine, API behavior, DB schema, frontend, candidate auto-correction, approved promotion, or system ID injection was changed.
- Read first: `AGENTS.md`, `model_설명.txt`, `docs/POLICY_SCHEMA.md`, and `tasks/progress.md`.
- Added `match_agent_v0.8/match_agent_v0.8/services/policy_extraction_candidate_validator.py`.
- Added `match_agent_v0.8/match_agent_v0.8/test_policy_extraction_candidate_validator.py`.
- Updated `scripts/run_policy_extraction_from_db_builder.py` so extraction output records include `candidate_validation_result` while preserving `parsed_candidate` unchanged.
- Validation rules include missing `policy_id`, missing `policy_name`, `review_status != needs_review`, missing `support_item_id`, unsupported `calculation_type`, invalid `monthly_fixed` amount/duration fields, empty evidence, evidence not found as a raw-text substring, `UNKNOWN_POLICY_ID`, empty `target_policy_ids`, duplicate `condition_id`, duplicate `support_item_id`, duplicate `rule_id`, invalid `unresolved_rules`, and unsupported fields.
- Current v3 db_builder candidate check: `output/policy_extraction_from_db_builder/childcare_flexible_start_support.json` failed validation with `missing_policy_id`, `evidence_not_in_raw_text`, `missing_calculation_type`, and `unknown_policy_id`.
- Unit test result: `python test_policy_extraction_candidate_validator.py` passed.
- Full verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode full` passed with 319 Python tests and frontend build.
- Git check: `git diff --check` passed; Git reported only CRLF conversion warnings for existing touched text files.
- Remaining issue: current v3 extraction still needs prompt/schema cleanup or human review before it can be considered structurally acceptable; validator intentionally does not inject a policy id from `incent_key`.

## 2026-06-14 Stage 1 - Candidate Assembler and Policy Extraction v4 Prompt

- Scope: implemented Stage 1 from `docs/incentdoc_backend_llm_roadmap.md` only. No frontend, analyzer, file_parser, mapping, writer_final, recommendation API contract, calculation formula, DB schema, migration, Supabase save, auto-approval, or LLM candidate auto-correction was changed.
- Read first: `AGENTS.md`, `model_설명.txt`, all files under `docs/`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Added `match_agent_v0.8/match_agent_v0.8/services/policy_extraction_candidate_assembler.py`.
- Added `match_agent_v0.8/match_agent_v0.8/test_policy_extraction_candidate_assembler.py`.
- Updated `match_agent_v0.8/match_agent_v0.8/services/policy_extraction_candidate_validator.py` so evidence comparison allows whitespace and line-break differences without changing the original `evidence_snippets` value.
- Updated `match_agent_v0.8/match_agent_v0.8/test_policy_extraction_candidate_validator.py` with whitespace-normalized evidence comparison coverage.
- Updated `scripts/run_policy_extraction_from_db_builder.py` to keep `parsed_candidate` as the raw LLM candidate, create a separate `assembled_candidate`, validate the assembled candidate, and default future db_builder extraction runs to `policy_extraction_v4`.
- Added `prompts/policy_extraction_v4.md` with stricter rules for mandatory `calculation_type`, no `UNKNOWN_POLICY_ID`, ambiguous target policies as `unresolved_rules`, no support item duplication, source-owned versus system-owned metadata separation, and `needs_review` preservation.
- Existing code reused: `services/db_builder_policy_document_loader.py`, `services/openai_policy_extraction_adapter.py`, `services/policy_extraction_adapter.py`, and the existing validation gate.
- Current v3 assembled candidate check: `missing_policy_id` is resolved by `incent_key` assembly, but the stored v3 output still reports `evidence_not_in_raw_text`, `missing_calculation_type`, and `unknown_policy_id`.
- Unit test result: `python test_policy_extraction_candidate_assembler.py` passed.
- Unit test result: `python test_policy_extraction_candidate_validator.py` passed.
- Full verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode full` passed with 326 Python tests and frontend build.
- Git check: `git diff --check` passed; Git reported only CRLF conversion warnings for existing touched text files.
- Remaining issue: `OPENAI_API_KEY` is not configured in this shell, so `python scripts\run_policy_extraction_from_db_builder.py --document-id childcare_flexible_start_support --prompt-path prompts\policy_extraction_v4.md --prompt-version policy_extraction_v4` cannot run. It exits with a clear `OPENAI_API_KEY is required` error and prints no key.
- Next Stage status: blocked. Stage 2 was not started because Stage 1's v4 live extraction completion check cannot be verified without `OPENAI_API_KEY`.

## 2026-06-14 Parental Leave Employer Support Scope

- Scope: narrowed future development and LLM extraction execution to employer subsidies directly related to parental leave and childcare working-time support. No db_builder document loading behavior, prompt schema, validator schema, assembler structure, recommendation formulas, Rule Engine behavior, DB schema, frontend, analyzer, file_parser, mapping, or writer_final code was changed.
- Included document IDs for LLM extraction execution: `childcare_flexible_start_support`, `parental_leave_reduction_support`, `replacement_workshare_support`, and `working_hours_reduction_support`.
- Excluded from analysis and LLM extraction execution: `elders_employ_incent`, `youth_hire_incent`, `employ_promo_incent`, `perm_conv_incent`, `flexible_work_incent`, `flexible_work_system_support`, and `worklife_balance_45_support`.
- Explicit decision: do not add 고령자 고용지원금 calculation types or Rule Engine extensions.
- Updated `scripts/run_policy_extraction_from_db_builder.py` so `load_policy_documents(...)` may still load all db_builder documents, but the extraction runner filters to parental-leave-related document IDs before any OpenAI adapter call.
- Added `match_agent_v0.8/match_agent_v0.8/test_db_builder_policy_scope_filter.py` to lock the included and excluded policy document IDs.
- Updated `tasks/feature_list.json` with `parental-leave-employer-support-scope` as `passing` after verification.
- Unit test result: `python test_db_builder_policy_scope_filter.py` passed.
- Full verification result: `powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode full` passed with 329 Python tests and frontend build.
- Git check: `git diff --check` passed; Git reported only CRLF conversion warnings for existing touched text files.
- Remaining issue: future prompt, validator, assembler, candidate storage, and recommendation work should optimize for parental leave employer subsidy combinations first.

## 2026-06-14 Childcare-Related Policy Scope Update and v5 Extraction Output Guard

- Scope update: expanded the LLM extraction execution scope from four directly parental-leave-related documents to seven childcare-related employer subsidy documents.
- Included document IDs: `parental_leave_reduction_support`, `replacement_workshare_support`, `worklife_balance_45_support`, `childcare_flexible_start_support`, `working_hours_reduction_support`, `flexible_work_incent`, and `flexible_work_system_support`.
- Excluded document IDs: `elders_employ_incent`, `youth_hire_incent`, `employ_promo_incent`, and `perm_conv_incent`.
- Updated `scripts/run_policy_extraction_from_db_builder.py` so the OpenAI extraction runner filters to the seven included childcare-related policy document IDs.
- Updated `match_agent_v0.8/match_agent_v0.8/test_db_builder_policy_scope_filter.py` and added root-level `test_db_builder_policy_scope_filter.py` so `python test_db_builder_policy_scope_filter.py` runs from the project root.
- Updated `prompts/policy_extraction_v5.md` to forbid non-calculation output fields: `application_process`, `application_steps`, `required_documents`, `contact_info`, `faq`, and `qna`.
- v5 extraction focus now remains on subsidy amount calculation, eligibility conditions, duplicate-benefit/combination rules, and monthly exclusion rules only.
- Unit test result: `python test_db_builder_policy_scope_filter.py` passed.
- LLM extraction result: `python scripts\run_policy_extraction_from_db_builder.py --document-id childcare_flexible_start_support --prompt-path prompts\policy_extraction_v5.md --prompt-version policy_extraction_v5` passed; candidate validation passed with `error_count=0` and no forbidden non-calculation fields.
- LLM extraction result: `python scripts\run_policy_extraction_from_db_builder.py --document-id working_hours_reduction_support --prompt-path prompts\policy_extraction_v5.md --prompt-version policy_extraction_v5` passed; candidate validation passed with `error_count=0` and no forbidden non-calculation fields.

## 2026-06-14 Mock Company 20-Case Expected Draft Inventory

- Scope: expanded mock company recommendation validation preparation from the existing Hana Machine case to all 20 mock company upload folders. No DB write, policy JSON source mutation, approval automation, recommendation engine logic change, or frontend change was performed.
- Added `scripts/build_mock_company_expected_cases.py`.
- The script scans `data/가상기업데이터_20개`, checks `기업특징.txt`, `사업자등록증.pdf`, and `직원명단.xlsx`, parses draft target policy and expected status from `기업특징.txt`, reads employee/leave/replacement fields from `직원명단.xlsx`, and writes expected-result draft fixtures under `tests/fixtures/mock_company_cases/`.
- Existing `tests/fixtures/mock_company_cases/04_hana_machine_expected.json` is preserved and not overwritten.
- Generated inventory: `output/mock_company_case_checks/mock_company_expected_case_inventory.json`.
- Updated `tasks/mock_company_test_plan.md` with the 20-case inventory summary.
- Execution result: `python scripts\build_mock_company_expected_cases.py` passed.
- Total company folders: 20.
- Expected-result draft generation success: 20.
- Hold count: 0.
- Policy case counts: `parental_leave_reduction_support=10`, `replacement_workshare_support=10`.
- Expected status counts: `eligible=10`, `ineligible=10`.
- Missing field top 5: `company.is_priority_support_enterprise=20`, `employee.child_age=10`, `employee.child_age_months=10`, `employee.child_school_grade=10`, `replacement_worker.hire_date=1`.
- High actual-vs-expected comparability cases: `mock_company_06`, `mock_company_07`, `mock_company_08`, `mock_company_09`, `mock_company_10`, `mock_company_17`, `mock_company_18`, `mock_company_19`, and `04_hana_machine`.
- Rule input expansion still needed for parental leave / working-hour reduction cases: preserve `company.is_priority_support_enterprise` and `leave_event.duration_days` for direct expected comparison.
- JSON validation check: all 20 `*_expected.json` fixtures and the inventory JSON parsed successfully.
- Git check: `git diff --check` passed with CRLF warnings only.

## 2026-06-14 Batch Actual-vs-Expected Runner

- Scope: added batch actual-vs-expected runner for high-comparability mock company cases only. No DB write, no approved auto-processing, no policy JSON source mutation, no frontend change, no recommendation engine logic modification.
- Read first: `AGENTS.md`, `tasks/mock_company_test_plan.md`, `output/mock_company_case_checks/mock_company_expected_case_inventory.json`.
- Created `scripts/run_batch_actual_vs_expected.py` for batch execution of 9 high-comparability cases targeting `replacement_workshare_support`.
- Extended `scripts/run_mock_company_expected_check.py` with `argparse` CLI support for `--case` and `--output` arguments, preserving backward compatibility with default 04_hana_machine case.
- Batch scope: 9 cases (`mock_company_06`–`mock_company_10`, `mock_company_17`–`mock_company_19`, `04_hana_machine`). All use test fixture `hana_machine_replacement_workshare` injected via `load_approved_policies` monkey-patch.
- 고령자/청년/고용촉진/정규직전환 policies are excluded.
- Batch execution result: `python scripts/run_batch_actual_vs_expected.py` completed with 0 errors.
- Summary: 5/9 passed, 4 failed, all 9 comparable (target policy found in output).
- Passed cases: `mock_company_06` (eligible), `mock_company_08` (eligible), `mock_company_10` (eligible), `mock_company_19` (ineligible), `04_hana_machine` (ineligible).
- Failed cases:
  - `mock_company_07`: expected eligible, actual ineligible. Possible condition boundary mismatch in expected-result draft.
  - `mock_company_09`: expected eligible, actual ineligible. Possible condition boundary mismatch in expected-result draft.
  - `mock_company_17`: expected ineligible with `replacement_worker_employment_duration_under_30_days`, actual ineligible with different reason code. Eligibility correct but reason-code mismatch.
  - `mock_company_18`: expected ineligible with `replacement_worker_employment_duration_under_30_days`, actual ineligible with different reason code. Eligibility correct but reason-code mismatch.
- Outputs written: `output/mock_company_case_checks/mock_company_batch_actual_vs_expected.json` and `output/mock_company_case_checks/mock_company_batch_summary.md`.
- Updated `tasks/mock_company_test_plan.md` with batch runner section, batch results table, and failure analysis.

## 2026-06-17 LLM Extraction Quality: Prompt v6 + Model Upgrade + Validator max_months Relaxation

- Scope: improved the LLM policy-source-to-JSON extraction quality only. No recommendation engine, Rule Engine, API behavior, DB schema, frontend, candidate auto-correction, or approved promotion was changed. Candidates remain `review_status=needs_review`.
- Read first: `AGENTS.md`, all `docs/`, `prompts/policy_extraction_v5.md`, `tasks/feature_list.json`, and `tasks/progress.md`.
- Trigger: live extraction over the 7 childcare-related documents showed two error classes. (1) Structural `evidence_not_in_raw_text` from the model gluing multiple table rows into one snippet. (2) Semantic flattening: `policy_extraction_v5` hardcodes `calculation_type="monthly_fixed"` for childcare, so every support item came out as `monthly_fixed` even when the source needed `period_tiered` (육아휴직 특례 첫 3개월 100만원 → 이후 30만원) or `conditional_bonus` (남성육아휴직/육아기단축 인센티브 +10만원). The schema validator could not catch this because it does not compare against gold, so it reported `passed=true` on semantically wrong output.
- Environment: installed `openai` and `PyMuPDF` into the active interpreter; created gitignored `match_agent_v0.8/match_agent_v0.8/.env` from `.env.example` with `POLICY_EXTRACTION_MODEL=gpt-4.1`.
- Added `prompts/policy_extraction_v6.md`: policy-agnostic (no per-policy `monthly_fixed` hardcoding); explicit `calculation_type` decision rules and shapes for `monthly_fixed` / `period_tiered` / `conditional_bonus`; navigation/footer/Q&A ignore rules; "use only this document" anti-cross-contamination rule; strengthened table-evidence rules forbidding `\n`-glued multi-row snippets and middle-clause dropping; mandatory `policy_name` from the body heading.
- Updated `match_agent_v0.8/match_agent_v0.8/services/policy_extraction_candidate_validator.py`: `max_months` for `monthly_fixed` is now optional. A null/absent value is allowed (the calculation engine already uses requested months without inferring a cap, e.g. replacement support has no source-stated duration cap); a present value must still be a positive integer. This removes false `invalid_max_months` errors without weakening existing assertions.
- Added tests in `match_agent_v0.8/match_agent_v0.8/test_policy_extraction_candidate_validator.py`: `test_null_max_months_is_allowed_when_source_states_no_cap` and `test_present_but_invalid_max_months_is_still_detected`.
- Updated `scripts/run_policy_extraction_from_db_builder.py` defaults: `DEFAULT_MODEL="gpt-4.1"`, `DEFAULT_PROMPT_VERSION="policy_extraction_v6"`.
- Live measurement over all 7 documents (`db_builder` source), validator error totals:
  - Baseline `policy_extraction_v5` + `gpt-4.1-mini`: 3/7 pass, 9 errors, every support item `monthly_fixed` (semantically wrong for parental/worklife).
  - `policy_extraction_v6` + `gpt-4.1` best run: 6/7 pass, 1 error; `parental_leave_reduction_support` correctly extracted as `period_tiered` + `conditional_bonus`.
- Known limitation: run-to-run nondeterminism at `temperature=0` is real and concentrated on `worklife_balance_45_support`, the most complex multi-dimension table. Across three runs that document flipped between `period_tiered` (0 errors) and `monthly_fixed` (1-4 errors). The residual `evidence_not_in_raw_text` cases are genuine multi-cell table-region snippets (headcount/support-limit rows) that have no contiguous raw substring; the model should leave evidence `[]` there but sometimes reconstructs it. The validator correctly flags these.
- Verification: `python test_policy_extraction_candidate_validator.py`, `test_policy_extraction_candidate_assembler.py`, `test_db_builder_policy_document_loader.py`, and `test_db_builder_policy_scope_filter.py` (app-dir and root) all passed. Full `scripts/verify.ps1 -Mode full/limited` was not run in this session because the sandbox blocks `-ExecutionPolicy Bypass`; the limited-mode test set was executed directly instead.
- Security note: `.env.example` contains a real-looking committed `OPENAI_API_KEY`. It should be rotated and replaced with a placeholder; the real key belongs in the gitignored `.env`.
- Next: optionally add a best-of-N extraction runner (run N times, keep the validator-passing candidate) to absorb nondeterminism on hard tables, and a per-document human-review gate before approval.

## 2026-06-17 Gold (Ground-Truth) Semantic Evaluation Dataset Drafts — 7 Childcare Documents

- Scope: authored AI-drafted gold (human-grade answer-key) JSON for all 7 childcare-related employer subsidy documents, to enable semantic (not just structural) scoring of LLM extraction. No recommendation engine, Rule Engine, API, DB schema, frontend, prompt, or candidate auto-approval was changed. Gold files are evaluation-only and must not be promoted to `approved`.
- Motivation: the candidate validator only checks structure/evidence and reported `passed=true` on semantically wrong v5 output (everything flattened to monthly_fixed). Gold lets `services/policy_structure_evaluator.py` compare candidate JSON against a human-confirmed correct answer and surface value_mismatch/amount_mismatch/tier_mismatch/missing_condition errors.
- Added `data/policy_extraction_real_eval/GOLD_CONVENTIONS.md`: the modeling rulebook resolving the open D-1..D-8 decisions into provisional conventions (calculation_type selection; incentives as bonuses not standalone base items to avoid double-counting; child-age branching; yearly caps derived not duplicated; conditional/ambiguous combination rules and policy-level exclusion conditions routed to unresolved_rules or notes; evidence omitted from gold to focus on money/structure; stable semantic ids).
- Created the dataset triple plus review notes for each case under `data/policy_extraction_real_eval/{raw_text,gold,metadata,review_notes}/`:
  - `parental_leave_reduction_support` (authored directly): 3 items (period_tiered + monthly_fixed + conditional_bonus), 2 unresolved.
  - `childcare_flexible_start_support`: 1 monthly_fixed, 6 unresolved (OR child-age, 2 monthly exclusions, headcount cap, shared-duration cap, statutory overlap).
  - `flexible_work_incent`: 2 conditional_bonus (재택/원격, 시차/선택), 4 unresolved (childcare ×2 multiplier as schema_gap, headcount cap, overtime exclusion, duplicate-history).
  - `flexible_work_system_support`: 0 items by design (one-time %-of-cost infrastructure subsidy that none of the 3 calc types fit), 3 unresolved (80%/1,000만 cap, small-biz usage-fee cap, use-obligation/return).
  - `replacement_workshare_support`: 3 monthly_fixed (size×leave-type amounts 140/130/120만, max_months null since duration is variable), 4 unresolved (80%-of-wage cap, variable duration, employment-adjustment exclusion, 특례 duplicate restriction).
  - `working_hours_reduction_support`: 2 monthly_fixed (장려금 30만 + 임금보전금 20만), 3 unresolved (2 monthly exclusions, headcount cap).
  - `worklife_balance_45_support` (hardest): 4 conditional_bonus base grid (규모 2 × 도입유형 2, each with +10만 우대 bonus) + 2 monthly_fixed 신규채용 (60/80만), 5 unresolved (preferred-industry OR, implementation-type definition, 2 headcount caps, 300인 extended eligibility).
- Authoring method: 6 of the 7 golds were drafted by parallel subagents given GOLD_CONVENTIONS.md plus the parental exemplar, each reading its raw source text and correcting the v6 extraction; all outputs were then verified centrally.
- Verification performed centrally: all 7 dataset triples present; all gold JSON parse; every gold has `review_status="needs_review"` and a non-empty `policy_name`; calculation-type required fields present (monthly_fixed→monthly_amount, period_tiered→tiers, conditional_bonus→monthly_amount+bonuses); ids unique; unresolved rules well-formed. Critical anti-hallucination check passed: every monetary amount in every gold is traceable to its raw source text in 만원 form (no invented numbers).
- Status: these are AI DRAFTS pending human (ksm) sign-off. Each `review_notes/{case}.md` lists the open D items to confirm (notably: spanning/count-capped incentives, policy-level exclusion conditions, cross-policy duplicate restriction targets, and the worklife table interpretation). Do not use gold for scoring-as-truth or policy approval until verified.
- Known harness limitation recorded: `policy_structure_evaluator` matches support_items by `support_item_id`, so scoring live LLM output (which uses arbitrary SI-001.. ids) requires a content-based alignment adapter first (tiers already match by (start_month,end_month)). Demonstrated on parental: structural validator said passed/0 errors, gold semantic eval gave 75% after content alignment and pinpointed the incentive double-count (wrong calculation_type, missing bonus, missing conditions).

## 2026-06-17 Source Text Preprocessing (Boilerplate Removal) Before Extraction

- Scope: added a deterministic source-text preprocessor and wired it into the db_builder extraction runner only. No recommendation engine, Rule Engine, API, DB schema, frontend, calculation formula, gold dataset, or candidate auto-approval was changed. Candidates remain `review_status=needs_review`.
- Motivation: the crawled worklife.kr pages wrap the policy body in ~40-55% site chrome (navigation menus, search/hashtag banners, breadcrumb buttons, address/copyright footer). This noise distracts the model and is a source of non-policy evidence and run-to-run instability on the hardest tables.
- Added `match_agent_v0.8/match_agent_v0.8/services/policy_source_preprocessor.py` with `preprocess_policy_source_text(raw)`: (1) drops the navigation header up to and including the first `신청하러 가기`; (2) drops the footer from the first `30117`/Copyright/`Ministry Of Employment` anchor; (3) drops standalone navigation/button lines; (4) collapses whitespace runs and blank lines. It only removes chrome and normalizes whitespace; it never reorders, rewrites, merges, or invents body words, so any body evidence stays a (whitespace-normalized) substring of the cleaned text.
- Design decision: the footer cut uses `30117` (the address line present on every page), NOT the contact line `고객상담센터`, because on some pages (e.g. childcare) the 문의/고객상담센터 block sits mid-document before the Q&A; cutting there would drop source-backed Q&A rules. Verified the childcare Q&A 합산 rule survives.
- Added `match_agent_v0.8/match_agent_v0.8/test_policy_source_preprocessor.py` (header/footer removal, mid-page Q&A preservation, button-line drop, body-amount/content survival, whitespace collapse, evidence-substring stability, missing-anchor fallback).
- Wired into `scripts/run_policy_extraction_from_db_builder.py`: the cleaned text is used for BOTH the extraction prompt and the candidate evidence validation (same canonical source). Added `--no-preprocess` to disable (default on) and a `preprocessing` block in each output record (enabled flag, raw/source char counts).
- Pre-wiring safety check: across the 7 documents, every monetary amount in the golds survives in the cleaned text; the only previously-matching v6 evidence broken by cleaning is the 1-2 line intro/title summary that sits before `신청하러 가기` (the same facts recur in the body), so re-extraction cites body lines instead and produces no new errors.
- Live measurement (v6 + gpt-4.1), no-preprocess r3 vs preprocess: structural validator PASS 6/7 -> 7/7, total errors 1 -> 0, summed prompt tokens 46,927 -> 38,955 (about 17% reduction). Input characters reduced 37-55% per document.
- Stability: two preprocess runs both gave 7/7 PASS and 0 errors, and `worklife_balance_45_support` (which flipped between period_tiered/monthly_fixed and 0-4 errors across the no-preprocess runs) was identical across both preprocess runs. Preprocessing removed the structural error flipping.
- Honest limitation: preprocessing fixes evidence/structural errors and stabilizes output, but does NOT fix the deepest semantic flattening on the hardest multi-dimension table: `worklife_balance_45_support` is now stably `monthly_fixed x10`, whereas its gold is `conditional_bonus x4 + monthly_fixed x2`. The structural validator cannot detect this; only the gold semantic eval can. Closing that gap needs further prompt work on that table or human review.
- Verification: `test_policy_source_preprocessor.py`, `test_policy_extraction_candidate_validator.py`, `test_policy_extraction_candidate_assembler.py`, and `test_db_builder_policy_scope_filter.py` pass. Full `verify.ps1` was not run (sandbox blocks `-ExecutionPolicy Bypass`); affected tests were run directly.

## 2026-06-17 Table-Structure-Preserving Re-Crawl (root-cause experiment for the worklife table)

- Scope: added a structure-preserving HTML-to-text extractor, a re-crawl script, and an opt-in runner flag to use the result. No change to the existing crawler `db_builder.py`, recommendation engine, Rule Engine, API, DB schema, frontend, gold dataset, or candidate auto-approval.
- Root cause confirmed: `db_builder.py` stores `target.get_text(separator="\\n", strip=True)`, which discards `<table>` structure and flattens a 2D (row x column) grid into a 1D line sequence. The original HTML is not retained (only the flattened text in `_raw.txt` and `_meta.json` content), so recovering structure requires re-crawling.
- Added `match_agent_v0.8/match_agent_v0.8/services/html_table_extractor.py`: `extract_structured_text(html, css)` keeps non-table content as text but serializes each `<table>` as Markdown rows so each row stays a single contiguous line with its cells joined by `|`. Network-free (the script passes HTML in).
- Added `match_agent_v0.8/match_agent_v0.8/test_html_table_extractor.py` (table rows preserved as Markdown; size header + amount cells on one line; non-table text kept; selector scoping; missing-selector fallback). Passes.
- Added `scripts/recrawl_structured_source.py`: re-fetches the 7 in-scope source URLs (from each `_meta.json`, utf-8, `div.cont_wrap_area`) and writes a sibling `{incent_key}_structured.txt`. Non-destructive (never overwrites `_raw.txt`/`_meta.json`). All 7 re-crawled OK (e.g. worklife 11 table rows).
- Wired `scripts/run_policy_extraction_from_db_builder.py` with `--use-structured` (default off): when set, it loads `{incent_key}_structured.txt` as the base source if present (then still applies preprocessing), and records `preprocessing.source_kind`.
- The worklife table is now preserved as a readable Markdown grid (e.g. `| 지원 수준 | 50인 이상 우선지원 대상기업 | (부분도입) 1인당 월 20만원(1년) (전면도입) ... | 신규 채용인원 1인당 월 60만원(1년) |`), so the model can see the 규모 x 도입유형 x 우대 relationships that flattening destroyed.
- Honest measurement (v6 + gpt-4.1 + preprocessing), flattened vs structured over the 7 docs: structural validator went 7/7 pass / 0 errors (flat) to 6/7 pass / 1 error (structured). worklife shifted from `monthly_fixed x10` (flat) to `period_tiered x10` (structured), and gained 1 `evidence_not_in_raw_text` from the model copying a Markdown table row (the `|` separators) as evidence. Both flat and structured still differ from the worklife gold (`conditional_bonus x4 + monthly_fixed x2`). Other docs were stable (parental still period_tiered + monthly_fixed + conditional_bonus; flexible_work_incent shifted 3 -> 5 monthly_fixed items).
- Conclusion: structured crawling is the correct root-cause capability (it preserves the grid) and is now available behind `--use-structured`, but a single run did NOT clearly beat flat+preprocessing on these documents by the structural metric, and it introduced a Markdown-separator evidence failure mode. More importantly, the structural validator cannot tell which interpretation is semantically closer to the gold (it scores flat 7/7 > structured 6/7 while both mis-model worklife), so flat vs structured cannot be ranked without the gold content-aligned semantic scorer. That scorer (the previously noted option C) is now the critical missing measurement, not optional.
- Verification: `test_html_table_extractor.py`, `test_policy_source_preprocessor.py`, `test_policy_extraction_candidate_validator.py`, and `test_db_builder_policy_scope_filter.py` pass. Full `verify.ps1` not run (sandbox blocks `-ExecutionPolicy Bypass`).

## 2026-06-17 Gold Content-Aligned Semantic Scorer + Gold-Filling Guide

- Scope: added a content-aligned semantic scorer that compares extraction output against the draft gold dataset, plus a detailed human guide for filling/verifying gold. No recommendation engine, Rule Engine, API, DB schema, frontend, prompt, crawler, or candidate auto-approval was changed.
- Problem solved: `services.policy_structure_evaluator` matches support_items by `support_item_id` and conditions by `condition_id`, but live extraction uses arbitrary ids (SI-001, C-001) that never line up with the gold's meaningful ids (SI-LEAVE-INFANT, C-INFANT-AGE), so everything looked "missing". The structural validator also passed all 7 docs (7/7) while 4 of them semantically diverge from gold, so a semantic scorer was the missing measurement.
- Added `scripts/score_extraction_against_gold.py`: aligns each candidate to the gold by CONTENT (support_items by amount-set Jaccard + calculation_type; conditions by field/operator/expected), relabels the matched candidate ids to the gold ids, then runs the existing `evaluate_policy_structure`. Tiers already align by (start_month,end_month). Outputs a per-document score, item counts (gold/candidate/matched), and an error-type breakdown. `--output-dir` selects which extraction set to score.
- First scoring run over `output/v6_gpt41_preproc` (flat + preprocessing): childcare 97.9, working_hours 92.7, parental 79.2, flexible_work_incent 75.0, flexible_work_system 75.0, replacement 71.4, worklife 72.7; average 80.6. The ranking matches the table-complexity analysis: simple single-amount policies score high, complex tables (incentives, %-cost, multi-dimension grids) score low. Dominant error types are missing_condition and value_mismatch (calculation_type differences).
- Caveat recorded in the script and report: scores are against AI-DRAFT gold (pending human verification), and bonuses/unresolved_rules are compared coarsely, so scores locate divergence but are not a final grade.
- Added `data/policy_extraction_real_eval/HOW_TO_FILL_GOLD.md`: a detailed Korean guide covering the per-document workflow (read review_notes D-items -> read raw -> edit gold -> checklist -> score), the full JSON schema with field-by-field meaning, calculation_type selection rules, the incentive-as-bonus rule (avoid base double-counting), combination_rules vs unresolved_rules routing, what to intentionally omit (timing, application steps, derivable yearly caps, policy-level exclusion conditions, evidence), a pre-submit checklist, and how to run and read the scorer (including the meaning of each error type).
- Verification: the scorer ran successfully over all 7 documents; the four existing extraction/preprocessor tests still pass. Full `verify.ps1` not run (sandbox blocks `-ExecutionPolicy Bypass`).
- Next: human verification of the 7 draft golds using HOW_TO_FILL_GOLD.md, after which the scores become trustworthy and can objectively compare flat vs structured crawling and future prompt/model changes.
