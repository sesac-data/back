# Policy Schema

## Core Rule

Policy schema data must describe only what is supported by the policy source. Do not infer missing conditions, amounts, durations, limits, or duplicate-benefit rules from general knowledge.

Every structured policy version used for recommendation calculation must be human-approved.

## LLM Role

The LLM may create candidate structured policy JSON from source text. The LLM output is not authoritative until reviewed and approved by a person.

Offline extraction evaluation fixtures compare candidate JSON against human-written expected JSON, but the candidate JSON must still use `review_status="needs_review"`. The evaluation harness may report scores and extraction errors, but it must not auto-fix fields, infer missing policy facts, or change the candidate to `approved`.

Live LLM extraction evaluation may call OpenAI through a dedicated adapter, but generated candidates remain review candidates. Generated JSON must not be saved to the policy DB and must not be promoted to `approved` by the batch script.

The LLM must preserve source-grounded evidence:

```json
{
  "evidence_snippets": [
    "Short source sentence copied from the policy document"
  ]
}
```

Each condition, amount, important limitation, and required document should be traceable to source text whenever possible.

## Approval State

Recommended policy lifecycle states:

```text
needs_review
approved
deprecated
```

Only `approved` policy versions are eligible for rule-engine and recommendation use.

Use `review_status` as the single policy review state field. Do not use `approval_status` or a policy-level `status` field for review state.

Runtime policy loading must preserve the same gate. The current demo API calls `services/approved_policy_loader.py`, which returns only policies with `review_status == "approved"` from the test-only demo fixture source. Unsupported sources and missing fixtures must return structured errors instead of silently falling back or widening the policy set.

`policy_db` loads approved policy JSON from PostgreSQL when `INCENTDOC_POLICY_DB_URL` is configured. It must query only approved and active rows and must not silently fall back to fixture data.

Minimum DB table:

```sql
CREATE TABLE subsidy_policies (
    id BIGSERIAL PRIMARY KEY,
    policy_id VARCHAR(100) NOT NULL,
    policy_name VARCHAR(255) NOT NULL,
    policy_version VARCHAR(50) NOT NULL,
    review_status VARCHAR(30) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    policy_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (policy_id, policy_version)
);
```

Runtime query conditions:

```text
review_status = 'approved'
is_active = TRUE
```

If `policy_json.review_status` exists and does not match the DB `review_status` column, the loader must return `policy_db_review_status_mismatch` and must not adjust the policy JSON.

## Minimum Policy Version Shape

```json
{
  "policy_key": "string",
  "policy_name": "string",
  "policy_category": "string",
  "source_url": "string",
  "source_document_id": "string",
  "review_status": "needs_review",
  "approved_by": null,
  "approved_at": null,
  "extraction_model": "string",
  "prompt_version": "string",
  "support_items": [
    {
      "support_type": "string",
      "target_conditions": ["string"],
      "conditions": [
        {
          "type": "string",
          "operator": "string",
          "value": null,
          "min": null,
          "max": null,
          "unit": "string",
          "evidence_snippets": ["string"]
        }
      ],
      "support": {
        "monthly_amount": null,
        "yearly_max_amount": null,
        "max_duration_months": null,
        "normalized_yearly_amount": null,
        "evidence_snippets": ["string"]
      },
      "required_systems": [],
      "required_documents": [],
      "duplicate_allowed": [],
      "duplicate_disallowed": [],
      "important_conditions": [],
      "evidence_snippets": []
    }
  ],
  "support_limit": {
    "max_people_ratio": null,
    "max_people_limit": null,
    "company_level_limit_amount": null,
    "evidence_snippets": []
  },
  "combination_rules": [],
  "application_process": [],
  "risk_conditions": []
}
```

## Combination Rules

`combination_rules` describes source-backed duplicate-benefit and policy-combination relationships. If the source policy does not state a combination rule, do not create or infer one.

```json
{
  "combination_rules": [
    {
      "rule_id": "CR-001",
      "rule_type": "mutually_exclusive",
      "target_policy_ids": ["POLICY-B"],
      "reason": "Source-backed reason text",
      "evidence_snippets": [
        "Exact source sentence supporting this rule"
      ]
    }
  ]
}
```

Allowed `rule_type` values:

- `mutually_exclusive`
- `requires`
- `allowed_with`

Validation rules:

- Missing `combination_rules` normalizes to an empty array.
- `rule_id` is required.
- `rule_type` must be one of the allowed values.
- `target_policy_ids` must include at least one policy id.
- `target_policy_ids` must not include the current policy id.
- `target_policy_ids` must not contain duplicates.
- `reason` is required.
- `evidence_snippets` is required and must not be empty.
- Evidence snippets must preserve source wording; do not summarize or generate them.

This schema only defines and validates rules. Runtime conflict checks, exclusion logic, and combination optimization are separate future code paths.

## Condition Type Discipline

Condition types must be selected from a registered list handled by the code-based rule engine. If extraction produces an unknown condition type, the policy must remain unapproved or the condition registry and tests must be updated.

Unknown condition types should never be silently ignored in approved recommendation calculation.

## Evidence Requirements

The following fields should carry evidence snippets:

- Eligibility conditions
- Amounts
- Durations
- Employee or company limits
- Duplicate-benefit rules
- Required documents
- Required systems
- Application deadlines or process steps

If source text does not provide evidence, the field must stay null or empty and be flagged for review.

## Extraction Evaluation Error Types

The offline policy structure evaluator can report:

- `missing_field`
- `value_mismatch`
- `type_mismatch`
- `missing_condition`
- `operator_mismatch`
- `amount_mismatch`
- `duration_mismatch`
- `tier_mismatch`
- `missing_evidence`
- `missing_combination_rule`
- `invalid_review_status`

Array order alone is not an extraction error. Conditions are compared by `condition_id`, tiers by `start_month` and `end_month`, and `combination_rules` by `rule_id`. Evidence snippets are compared as exact source-backed strings.
