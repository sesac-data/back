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
