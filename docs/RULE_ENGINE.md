# Rule Engine

## Principle

Eligibility must be decided by deterministic code, not by an LLM.

The rule engine consumes:

- Approved policy JSON
- Company context
- Labor partner/client context where applicable
- Employee data
- Leave event data
- Required system/document state

The rule engine returns structured, explainable results.

## Responsibilities

The rule engine is responsible for:

- Evaluating policy conditions
- Reporting passed and failed conditions
- Reporting unknown or unsupported condition types
- Blocking unapproved policy versions
- Producing machine-readable eligibility results

The rule engine is not responsible for:

- Extracting source policy text
- Guessing missing conditions
- Choosing the final recommendation combination
- Calculating unsupported amount formulas by inference

## Required Output

```json
{
  "policy_key": "string",
  "policy_name": "string",
  "support_type": "string",
  "eligible": false,
  "status": "eligible | ineligible | needs_review | unsupported",
  "passed_conditions": [],
  "failed_conditions": [],
  "unsupported_conditions": [],
  "evidence_snippets": []
}
```

## Approved Policy Gate

Before evaluating a policy, the rule engine must check:

```text
policy.review_status == "approved"
```

If this is false, the engine returns `needs_review` and must not calculate eligibility or amount.

## Unknown Condition Handling

Unknown condition types are high risk.

Expected behavior:

- Draft policy: allow unknown condition types to remain visible for review.
- Approved policy: fail verification if unknown condition types exist.
- Runtime recommendation: return `unsupported` or `needs_review`; do not treat unknown conditions as passed.

## Current Code Mapping

Current candidate files:

- `services/condition_evaluator.py`
- `services/condition_registry.py`
- `services/calculation_service.py`
- `services/gap_analysis_service.py`
- `services/rule_engine_domain_adapter.py`

The existing evaluator handles only part of the policy condition surface. Expanding the engine requires tests for every newly supported condition type.

## Domain Adapter

`services/rule_engine_domain_adapter.py` converts general-company domain input into the rule-engine input shape.

Current adapter output:

```json
{
  "rule_input": {
    "company": {
      "size": "small",
      "has_replacement_worker": true
    },
    "employee": {
      "leave_type": "parental_leave"
    }
  },
  "requested_months": 4,
  "errors": []
}
```

Adapter responsibilities:

- Read `company`, `employee`, and `leave_event` sections from the API payload.
- Prefer `leave_event.leave_type` over `employee.leave_type`.
- Prefer `leave_event.has_replacement_worker` over `company.has_replacement_worker`.
- Calculate `requested_months` from explicit `requested_months` or inclusive leave dates.
- Return structured errors for invalid date ranges or non-positive explicit months.

Adapter non-goals:

- Do not evaluate policy eligibility.
- Do not calculate policy amounts.
- Do not infer policy source conditions.
- Do not generate combinations or recommendations.
- Do not connect to the database.

## Condition Groups (OR / AND)

Flat conditions are combined with AND. Some policies state OR requirements such as `만 12세 이하 또는 초등학교 6학년 이하`. These are expressed as a condition group:

```json
{
  "condition_group_id": "CG-001",
  "mode": "or",
  "conditions": [
    {"condition_id": "C-AGE", "field": "employee.child_age", "operator": "lte", "expected": 12, "evidence_snippets": ["만 12세 이하"]},
    {"condition_id": "C-GRADE", "field": "employee.child_school_grade", "operator": "lte", "expected": 6, "evidence_snippets": ["초등학교 6학년 이하"]}
  ],
  "evidence_snippets": ["만 12세 이하 또는 초등학교 6학년 이하"]
}
```

`services/condition_evaluator.py` provides:

- `evaluate_condition_group(input_data, group)`: an `or` group passes when any member passes; an `and` group passes when all members pass; empty groups and unsupported `mode` values do not pass.
- `evaluate_conditions_with_groups(input_data, conditions)`: evaluates a list that may mix flat operator conditions and groups. Flat conditions keep AND semantics; each group is one AND unit at the top level. With no groups present, the result matches `evaluate_operator_conditions`.

Member results are preserved in `member_results` for explainability. OR-group member failures are not reported as top-level `failed_conditions` because the group as a whole passed. The existing `evaluate_operator_conditions` is unchanged.

## Monthly Wage Cap

`services/calculation_service.py` provides `apply_monthly_wage_cap`, used by the `monthly_fixed` and `period_tiered` calculators. When a support item declares `monthly_cap_ratio`, the per-month amount is capped at `min(policy_monthly, wage * monthly_cap_ratio)` (wage read from `cap_field`, default `employee.monthly_wage`). A missing wage falls back to `ASSUMED_DEFAULT_MONTHLY_WAGE` with an `assumed_wage_used` step reason. Without `monthly_cap_ratio` the calculators are unchanged.

## Monthly Exclusion (해당월 부지급)

`services/calculation_service.py` provides `apply_monthly_exclusion`, used by the `monthly_fixed` calculator. When a support item declares `monthly_exclusion: true`, the engine reduces eligible months by a provided non-payable-month count (`excluded_months_field`, default `leave_event.excluded_months`): `adjusted = max(0, eligible_months - excluded_months)`. A missing count means 0 excluded (`no_exclusion_data` step reason); nothing is inferred. Without the marker the calculator is unchanged.

## Test Expectations

Each condition type needs at least:

- Passing case
- Failing case
- Missing input case
- Boundary value case where applicable
- Evidence preservation case when surfaced in output
