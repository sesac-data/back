# Test Scenarios

## Harness Verification

Run after every feature implementation:

```bash
scripts/verify.sh
```

The script is expected to check required harness files, validate task JSON, and run available existing tests without deleting or weakening them.

## Policy Schema Scenarios

- A structured policy without `evidence_snippets` for conditions is blocked from approval.
- A policy with unknown condition types remains `needs_review`.
- A policy with `review_status != approved` is not used by the rule engine.
- A policy amount field stays null when the source does not provide an amount.
- A policy duplicate rule stays `needs_review` when the source does not state compatibility.

## Policy Extraction Evaluation Scenarios

- The evaluator compares source text fixtures, human-written expected policy JSON, and assumed LLM candidate JSON without calling a live LLM API.
- Candidate JSON fixtures must stay `review_status = needs_review`.
- A complete candidate scores `100`.
- Missing conditions return `missing_condition`.
- Operator differences return `operator_mismatch`.
- Amount differences return `amount_mismatch`.
- Duration differences return `duration_mismatch`.
- Tier differences return `tier_mismatch`.
- Missing evidence returns `missing_evidence`.
- Missing combination rules return `missing_combination_rule`.
- A candidate with `review_status = approved` returns `invalid_review_status`.
- Array order differences alone are allowed.
- Conditions are compared by `condition_id`.
- Tiers are compared by `start_month` and `end_month`.
- Combination rules are compared by `rule_id`.
- Evidence snippets are compared as exact source-backed strings.
- The evaluator writes JSON and Markdown reports to `output/policy_extraction_eval/`.
- The evaluator does not change recommendation logic, Rule Engine logic, API behavior, DB schema, frontend UI, or candidate review status.
- The live LLM extraction batch runner requires `OPENAI_API_KEY`; if absent, it exits with a clear error and does not print the key.
- The live LLM extraction batch runner uses `POLICY_EXTRACTION_MODEL` and `POLICY_EXTRACTION_PROMPT_VERSION` when provided.
- The OpenAI adapter records `raw_response`, `parsed_candidate`, `parse_error`, `elapsed_ms`, and `token_usage`.
- JSON parse success and failure are both represented in per-case output records.
- Generated candidates are stored under `output/policy_extraction_eval/generated/` and are not saved to DB.
- Generated candidates are evaluated with the existing `policy_structure_evaluator`.
- If a generated candidate has `review_status = approved`, evaluation reports `invalid_review_status`; the runner does not correct it.
- The live LLM extraction runner supports repeated execution with `--runs`.
- If only `--prompt-version` is provided, the runner loads `prompts/{prompt_version}.md`.
- If `--prompt-path` is provided, that explicit path takes priority over prompt-version lookup.
- Run reports and summary reports record `prompt_file` and `prompt_sha256`.
- Repeated reports are stored under run_id-specific directories instead of overwriting previous run output.
- Summary reports include average, minimum, and maximum run scores, policy-level score spread, and repeated error-type counts.
- The real policy-source evaluation dataset uses `raw_text/`, `gold/`, and `metadata/` subdirectories.
- Real dataset raw text and gold JSON files must match by `case_id` file stem.
- Missing gold JSON returns a clear dataset validation error.
- Missing metadata JSON returns a clear dataset validation error.
- Metadata must include `case_id`, `policy_name`, `source_url`, `source_type`, `collected_at`, and `notes`.
- Real policy dataset reports are stored separately under `output/policy_extraction_real_eval/`.
- Real dataset generated candidates are not saved to Supabase, auto-approved, or auto-corrected.

## Rule Engine Scenarios

- Eligible employee passes all supported conditions.
- Ineligible employee returns failed conditions with reasons.
- Missing employee input returns failed or `needs_review`, not eligible.
- Unknown condition type returns `unsupported` or `needs_review`.
- Unapproved policy returns `needs_review` before condition evaluation.

## Amount Calculation Scenarios

- Monthly amount and duration produce yearly support amount.
- Explicit yearly max overrides monthly multiplication when policy says so.
- Null amount fields produce zero or `needs_review`, not inferred values.
- Company-level and employee-level amount fields are not mixed without explicit policy support.

## Recommendation Scenarios

- Employee receives only supports from approved policies.
- Duplicate-disallowed policies are not selected together.
- Duplicate-unknown policies are routed to `needs_review`.
- Highest total amount is selected only within conflict and limit constraints.
- Selected and skipped policies are both recorded for auditability.

## Combination Rule Schema Scenarios

- Missing `combination_rules` normalizes to an empty array.
- Valid `mutually_exclusive`, `requires`, and `allowed_with` rules pass schema validation.
- Unsupported `rule_type` returns a structured validation error.
- Missing `rule_id`, empty `target_policy_ids`, self references, duplicate targets, missing `reason`, and missing `evidence_snippets` each return structured validation errors.
- Mixed valid and invalid rules preserve valid normalized rules while returning rule-specific errors.
- Schema validation does not perform runtime conflict detection or policy-combination selection.

## Mutually Exclusive Conflict Scenarios

- Approved policies with no `mutually_exclusive` relationship return no conflicts.
- A one-way `A -> B` declaration returns one conflict when both policies are approved candidates.
- A two-way `A -> B` and `B -> A` declaration still returns one conflict.
- One source policy may conflict with multiple approved target policies.
- Targets not present in the candidate list do not create conflicts.
- `needs_review` and `deprecated` policies are excluded from detection.
- `requires` and `allowed_with` rules are ignored by this detector.
- Schema errors are returned separately from conflicts.
- Evidence snippets are preserved in conflict results.
- Detection does not exclude policies, generate combinations, sum amounts, or optimize costs.

## Requires Rule Detection Scenarios

- Approved policies with no `requires` relationship return no violations.
- If `A` requires `B` and both are approved candidates, no violation is returned.
- If `A` requires `B` and `B` is missing from approved candidates, one violation is returned.
- If `A` requires `B` and `C`, both `B` and `C` must be approved candidates.
- If any required target is missing, only the missing policy IDs are reported.
- Required target policies with `review_status == "needs_review"` or `review_status == "deprecated"` count as missing.
- If the source policy is not an approved candidate, its `requires` rules are not evaluated.
- `mutually_exclusive` and `allowed_with` rules are ignored by this detector.
- Schema errors are returned separately from requirement violations.
- Evidence snippets are preserved in violation results.
- OR requirements and `requirement_mode` are not supported in the current scope.
- Detection does not add missing policies, generate combinations, exclude policies, sum amounts, or optimize costs.

## Policy Combination Generation Scenarios

- One approved candidate creates one non-empty combination.
- Three approved candidates with no conflicts or requirements create seven non-empty combinations.
- A combination containing a `mutually_exclusive` pair is rejected.
- If `C` requires `A`, `[C]` is rejected and `[A, C]` remains valid.
- A combination can include both `mutually_exclusive` and `requires` rejection reasons.
- `needs_review` and `deprecated` policies are excluded from combination candidates.
- `allowed_with` rules do not affect generation results in the current scope.
- Duplicate policy IDs return structured errors and are not merged.
- Empty candidate lists return empty valid and rejected combination lists.
- Candidate counts above `MAX_COMBINATION_CANDIDATES` return structured errors.
- Policy IDs inside combinations and result ordering remain deterministic.
- Rejected combinations preserve evidence snippets in their reasons.
- Generation does not calculate amounts, aggregate totals, choose an optimal combination, add policies, or remove policies automatically.

## Combination Amount Summarization Scenarios

- A single-policy valid combination returns that policy's total support amount.
- Two-policy and three-policy valid combinations sum each policy's `estimated_total_amount`.
- Conditional bonus policies are not double counted because bonus is already included in `estimated_total_amount`.
- `total_base_amount`, `total_bonus_amount`, and `total_subsidy_amount` are returned separately.
- Combinations containing `calculation_error`, `ineligible`, null `estimated_total_amount`, or missing policy results are rejected with structured reasons.
- Duplicate standardized policy results for the same `policy_id` return structured errors and are not merged.
- Calculation steps and evidence snippets are preserved from policy-level calculation results.
- Combination and policy-result ordering remains deterministic.
- Summarization does not calculate policy amounts again, choose an optimal combination, rank recommendations, or calculate employer net cost.

## Employer Net Cost Calculation Scenarios

- If no employer cost items are provided, `total_employer_cost` is `0` and net cost is calculated from existing subsidy totals.
- A cost item with empty `applies_to_policy_ids` applies to every summarized combination.
- A cost item with one target policy applies only to combinations containing that policy.
- A cost item with multiple target policies applies only when all listed policies are present.
- Cost items are excluded when target policies are not in a combination.
- Multiple applicable cost items are summed into `total_employer_cost`.
- Null, non-numeric, negative, missing-ID, and duplicate-ID cost items return structured errors.
- Missing `applies_to_policy_ids` normalizes to an empty list.
- Negative `net_employer_cost` is valid and does not create an error.
- Net-cost calculation reuses existing `total_subsidy_amount`, calculation steps, and evidence snippets.
- Net-cost calculation does not infer costs, choose an optimal combination, rank recommendations, or sort by amount.
- Acceptance scenario `employer_net_cost` uses test-only policies and explicit `employer_cost_items`.
- Acceptance verifies `total_subsidy_amount`, `total_employer_cost`, `net_employer_cost`, and applied cost item IDs for each summarized combination.

## Employer Net Cost Optimal Combination Selection Scenarios

- A single cost-calculated combination is selected as rank 1.
- Among multiple candidates, the combination with the lowest `net_employer_cost` is selected.
- A higher total subsidy amount is not selected when its `net_employer_cost` is higher.
- If `net_employer_cost` is tied, the higher `total_subsidy_amount` is selected.
- If `net_employer_cost` and `total_subsidy_amount` are tied, the combination with fewer policies is selected.
- If all major values are tied, lexicographic `policy_ids` string order is used.
- Negative `net_employer_cost` combinations remain valid candidates.
- Empty candidates return a structured `no_recommendation_candidates` error.
- Candidates with null `net_employer_cost`, null `total_subsidy_amount`, or missing/empty `policy_ids` are excluded with structured errors.
- Duplicate `policy_ids` combinations return structured errors and are not merged.
- `rejected_combinations` are preserved for auditability but are not recommendation candidates.
- Recommendation reasons are fixed code-based strings; no LLM explanation is generated.
- Selection reuses existing `calculation_steps` and `evidence_snippets` without recalculating amounts or costs.
- Acceptance scenario `optimal_combination` verifies that the lowest net-cost combination is selected even when another combination has a higher total subsidy amount.

## General Company Recommendation Demo Scenarios

- The demo screen is reachable at `/company/recommendation-demo` in the React/Vite app.
- The screen uses `recommendationService` instead of importing mock JSON directly into the component.
- The current adapter is mock-based until a callable backend recommendation API exists.
- The test input area displays company name, employee name, leave type, leave dates, replacement-worker status, and a support-check button.
- The result summary displays applicable combination count, rejected combination count, highest total subsidy amount, and calculation date.
- Valid combinations display policy IDs, base amount, bonus amount, total subsidy amount, included policy count, and detail access.
- Rejected combinations display policy IDs, rejection type, rejection reason, evidence snippets, and detail access.
- Detail output preserves policy-level `calculation_steps`, `passed_conditions`, `failed_conditions`, `applied_bonuses`, `skipped_bonuses`, and `evidence_snippets`.
- Null amount values are displayed as `계산 불가`, not `0원`.
- The UI must not contain "최적 추천" or "가장 유리한 조합" until optimizer/ranking logic is implemented.
- Frontend build and limited backend verification must pass after demo changes.

## Backend Acceptance Scenarios

- `base`: run test-only candidate policies through the existing approved-policy gate, condition evaluator, monthly_fixed calculator, standardized policy result normalizer, combination generator, and amount summarizer; expect one valid combination and total subsidy amount `400000`.
- `bonus`: run a test-only period_tiered policy with a conditional replacement-worker bonus; expect one valid combination, base amount `3600000`, bonus amount `150000`, and total subsidy amount `3750000`.
- `capped`: request more months than the test-only policy maximum duration; expect the existing monthly_fixed calculator to cap eligible months and return total subsidy amount `600000`.
- `conflict`: include mutually exclusive approved test-only policies; expect two valid single-policy combinations and one rejected pair with `mutually_exclusive`.
- `requires`: include a dependent approved test-only policy without its required policy; expect no summarized valid combinations and one rejected combination with `requires`.
- `employer_net_cost`: pass explicit cost items to the existing employer net-cost calculator after combination amount summarization; expect three cost-calculated combinations with total employer costs `[1000, 1700, 2200]` and net employer costs `[600, 1380, 1480]`.
- `optimal_combination`: pass explicit cost items through employer net-cost calculation, then select the lowest net-cost combination; expect `["smoke-optimal-a"]` to be recommended even though `["smoke-optimal-a", "smoke-optimal-b"]` has the highest total subsidy amount.
- Every acceptance scenario must compare expected and actual valid combination count, rejected combination count, policy IDs, rejected policy IDs, amount totals, and rejection/error codes.
- Every acceptance scenario must verify that evidence snippets and calculation steps are present in calculated or rejected outputs.
- Acceptance fixtures are test-only data and must not be treated as real policy source data.

## Frontend Recommendation Demo E2E Scenarios

- Visit `/company/recommendation-demo` through a browser automation runner.
- Verify the page title `육아휴직 지원금 조합 비교`.
- Verify the `지원금 확인` button exists and can be clicked.
- Verify visible summary labels for applicable combination count, rejected combination count, and highest total subsidy amount.
- Verify valid and rejected combination lists render.
- Verify details preserve `evidence_snippets`.
- Verify null amounts render as `계산 불가`.
- Verify the screen does not contain `최적 추천` or `가장 유리한 조합`.
- Save a screenshot to `output/verification/frontend-screenshot.png`.
- On failure, preserve Playwright screenshot and trace artifacts.

## Demo Recommendation API Integration Scenarios

- FastAPI app object exists at `match_agent_v0.8/match_agent_v0.8/api_server.py` as `app`.
- `GET /health` returns HTTP 200 with `{"status": "ok"}`.
- Swagger UI is available through FastAPI at `/docs`.
- CORS allows only local Vite dev origins `http://127.0.0.1:5173` and `http://localhost:5173`.
- `POST /api/demo/recommendations/calculate` validates that `company`, `employee`, and `leave_event` are objects.
- Missing or empty `employer_cost_items` is accepted and treated as an explicit empty list.
- Missing `policy_source` defaults to `demo_fixture`.
- `policy_source` accepts only `demo_fixture` and `policy_db`; other values return `unsupported_policy_source`.
- The API loads policies through the approved policy loader.
- The approved policy loader supports the test-only `optimal_combination` demo fixture source.
- The approved policy loader supports `policy_db` when `INCENTDOC_POLICY_DB_URL` points to a test PostgreSQL database.
- When the API request uses `policy_source=policy_db`, orchestration calls the existing `policy_db` loader path.
- The approved policy loader returns only policies with `review_status == "approved"`.
- `policy_db` returns only rows where `review_status = approved` and `is_active = true`.
- `policy_db` excludes `needs_review`, `deprecated`, and inactive policies.
- `policy_db` returns `approved_policy_not_found` when no approved active policy exists.
- `policy_db` returns `policy_db_connection_failed` when the DB URL is missing or the connection cannot be opened.
- `policy_db` returns `policy_db_table_not_found` when `subsidy_policies` does not exist.
- `policy_db` returns `policy_db_invalid_json` when `policy_json` is not a JSON object.
- `policy_db` returns `policy_db_review_status_mismatch` when DB column `review_status` and `policy_json.review_status` differ.
- API `policy_db` loader errors are returned to the caller and must not fall back to `demo_fixture`.
- Unsupported policy sources return a structured `unsupported_policy_source` error.
- Missing demo fixtures return a structured `demo_fixture_not_found` error.
- The API calls the existing calculation, standardization, combination generation, amount summarization, employer net-cost, and optimal-combination selector services in sequence.
- The API returns `recommended_combination`, `alternative_combinations`, `rejected_combinations`, `errors`, and `meta`.
- `meta.data_source`, `meta.is_demo`, `meta.policy_source`, and `meta.loaded_policy_count` identify the active data boundary.
- `demo_fixture` responses use `meta.data_source = demo_fixture` and `meta.is_demo = true`.
- `policy_db` responses use `meta.data_source = policy_db` and include the loaded approved active policy count.
- The recommended combination is selected by lowest `net_employer_cost`, even when another combination has a higher total subsidy amount.
- The API adapter posts browser input to `/api/demo/recommendations/calculate`.
- The API adapter sends `policy_source` using `VITE_RECOMMENDATION_POLICY_SOURCE` or the default `demo_fixture`.
- The API adapter maps API results into the existing demo screen result shape without duplicating calculation logic.
- The recommendation service defaults to the mock adapter unless `VITE_RECOMMENDATION_ADAPTER=api` is set.
- The demo screen displays `데모 정책 데이터 기준 결과입니다.` for `demo_fixture` and `Supabase 테스트 정책 DB 기준 결과입니다.` for `policy_db`.
- Mock adapter behavior remains available and unchanged for default demo verification.
- API adapter mode can be verified by running the demo API server and Playwright E2E with `VITE_RECOMMENDATION_ADAPTER=api`.

## Rule Engine Domain Adapter Scenarios

- General-company API payload maps to `rule_input.company.size`, `rule_input.company.has_replacement_worker`, and `rule_input.employee.leave_type`.
- `leave_event.leave_type` overrides `employee.leave_type`.
- `leave_event.has_replacement_worker` overrides `company.has_replacement_worker`.
- Explicit positive `leave_event.requested_months` is used when provided.
- Missing leave dates use the current demo default requested months.
- Inclusive start/end leave dates produce the requested month count.
- End date before start date returns a structured error.
- Non-positive explicit requested months return a structured error.
- The adapter does not evaluate eligibility, calculate amounts, generate combinations, calculate costs, or select recommendations.

## General Company MVP Scenarios

- General company onboarding stores company and employee context.
- General company employee data is scoped only to that company.
- Employee management edits leave type, start date, and end date.
- General company recommendations use only that company's employees.

## Labor Partner MVP Scenarios

- Labor partner onboarding stores partner, first client, and client employee context.
- Client employee data is scoped only to the selected client.
- Labor partner recommendations use only selected client data.
- No labor partner data is automatically shared with a general company.

## Regression Scenarios

- Existing tests remain present.
- Existing tests are not skipped by deleting files or weakening assertions.
- Existing policy JSON fixtures remain loadable.
- Existing recommendation amount guard tests remain part of verification.
