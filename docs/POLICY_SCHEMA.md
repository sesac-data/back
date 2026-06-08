# Policy Schema

## Core Rule

Policy schema data must describe only what is supported by the policy source. Do not infer missing conditions, amounts, durations, limits, or duplicate-benefit rules from general knowledge.

Every structured policy version used for recommendation calculation must be human-approved.

## LLM Role

The LLM may create candidate structured policy JSON from source text. The LLM output is not authoritative until reviewed and approved by a person.

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
