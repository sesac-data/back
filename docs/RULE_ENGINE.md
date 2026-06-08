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

The existing evaluator handles only part of the policy condition surface. Expanding the engine requires tests for every newly supported condition type.

## Test Expectations

Each condition type needs at least:

- Passing case
- Failing case
- Missing input case
- Boundary value case where applicable
- Evidence preservation case when surfaced in output
