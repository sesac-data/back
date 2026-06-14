# Policy Extraction Prompt v4

You are converting policy source text into one candidate structured policy JSON object.

Return JSON only. Do not include Markdown, comments, prose, or code fences.

This output is a review candidate. It is never an approved policy.

## System-Owned Metadata Boundary

The extraction model should extract only source-backed policy facts.

The application code will attach these system-owned fields after your response:

- `policy_id`
- `source_document_id`
- `source_url`
- `source_file`

If the source text does not explicitly contain a stable policy id, leave `policy_id` as an empty string. Do not invent a policy id. Do not use `UNKNOWN_POLICY_ID`.

Always keep `review_status` as `"needs_review"`.

## Required Top-Level Shape

Use exactly this top-level shape:

```json
{
  "policy_id": "",
  "policy_name": "",
  "review_status": "needs_review",
  "source_document_id": "",
  "source_url": "",
  "source_file": "",
  "evidence_snippets": [],
  "support_items": [],
  "combination_rules": [],
  "application_process": [],
  "risk_conditions": [],
  "unresolved_rules": []
}
```

Do not add unsupported top-level fields.

## Support Item Rules

Every support item must include `support_item_id`, `calculation_type`, amount or tier fields that match the calculation type, and `evidence_snippets`.

Allowed `calculation_type` values:

```text
monthly_fixed
period_tiered
conditional_bonus
```

Do not use aliases such as:

- `support_type` instead of `calculation_type`
- `monthly_amount` as a replacement for `calculation_type`
- `fixed_amount`
- `fixed_monthly`
- `fixed_monthly_amount`
- `monthly`
- `period`
- `bonus`

For a monthly fixed support item, use:

```json
{
  "support_item_id": "SI-001",
  "calculation_type": "monthly_fixed",
  "monthly_amount": 300000,
  "max_months": 12,
  "conditions": [],
  "evidence_snippets": ["Exact source substring"]
}
```

For a period-tiered support item, use one support item with `calculation_type="period_tiered"` and a `tiers` array. Do not duplicate support items for each tier.

For a conditional-bonus support item, use one support item with `calculation_type="conditional_bonus"`, base amount fields, and `bonuses`.

Do not output duplicate `support_item_id` values.

## Evidence Rules

Every `evidence_snippets` value must be copied from the source text.

Preserve the source wording. Do not translate, summarize, repair, or normalize the evidence text.

Small whitespace or line-break differences will be handled by the validation gate, but you should still copy evidence as closely as possible.

Every condition, amount, duration, combination rule, application step, risk condition, and unresolved rule must have evidence.

## Atomic Conditions

Break complex source sentences into separate atomic conditions.

If one sentence contains multiple requirements, create one condition per requirement.

Separate:

- period/duration conditions
- weekly hour conditions
- daily hour conditions
- lower and upper bounds
- boolean operational requirements

Examples:

- `6 months or more and 35 hours or more` becomes two conditions.
- `30 hours 초과 ~ 35 hours 이하` becomes `gt 30` and `lte 35`.
- `daily 1 hour reduction` becomes its own condition.
- wage reduction prohibition, employment rules, contract changes, and electronic attendance management each become separate boolean conditions when source-backed.

Allowed operators:

```text
eq, neq, gt, gte, lt, lte, in, not_in
```

Do not create duplicate `condition_id` values.

## Combination Rules

Use `combination_rules` only when the source clearly identifies the target policy id or target policy context well enough for a reviewer to map without guessing.

Never output `UNKNOWN_POLICY_ID` in `combination_rules.target_policy_ids`.

If a duplicate-benefit or overlapping-period rule is source-backed but the target policy id is not clear, put it in `unresolved_rules` with `rule_type="ambiguous_target_policy"` instead of `combination_rules`.

Example unresolved target:

```json
{
  "rule_id": "UR-001",
  "rule_type": "ambiguous_target_policy",
  "description": "The source states an overlapping-period duplicate-benefit limit, but the target policy id requires human mapping.",
  "evidence_snippets": ["Exact source substring"]
}
```

Do not output duplicate `rule_id` values.

## Unresolved Rules

Use `unresolved_rules` for source-backed rules that cannot be represented safely with the current schema.

Allowed useful `rule_type` examples:

```text
unsupported_or_condition
ambiguous_target_policy
complex_headcount_cap
shared_duration_cap
ambiguous_time_unit
monthly_exclusion_rule
unsupported_combination_rule
schema_gap
```

Each unresolved rule must include:

```json
{
  "rule_id": "UR-001",
  "rule_type": "schema_gap",
  "description": "What the source says and why it needs human review",
  "evidence_snippets": ["Exact source substring"]
}
```

Do not use `unresolved_rules` as a dumping ground. If the current schema can represent the rule as a support item, condition, combination rule, application process, or risk condition, use the normal field instead.

## Application Process and Risk Conditions

Application or submission facts belong in `application_process`.

Do not convert application steps into eligibility conditions unless the source explicitly states they are support requirements.

Rules such as unpaid months due to missing clock records or overtime above a threshold should be represented as `risk_conditions` if they can be encoded as conditions. If the time unit or monthly exclusion mechanics are unclear, place them in `unresolved_rules` with `rule_type="monthly_exclusion_rule"` or `rule_type="ambiguous_time_unit"`.

## Final Self-Check

Before returning JSON, verify:

- `review_status` is exactly `"needs_review"`.
- No `approval_status` or policy-level `status` field exists.
- `support_items[*].calculation_type` is present and one of the allowed values.
- No `UNKNOWN_POLICY_ID` exists anywhere.
- Ambiguous target policies are in `unresolved_rules`, not `combination_rules`.
- `source_document_id`, `source_url`, and `source_file` are empty unless present in source text.
- Every evidence snippet is source-backed.
- No duplicate `support_item_id`, `condition_id`, or `rule_id` values exist.
- No value is inferred from outside the source.

Policy source text:

```text
{{SOURCE_TEXT}}
```
