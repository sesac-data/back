# Policy Extraction Prompt v5

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
  "unresolved_rules": []
}
```

Do not add unsupported top-level fields.

Never output `risk_conditions`.

Never output application, document, contact, FAQ, or Q&A fields such as:

- `application_process`
- `application_steps`
- `required_documents`
- `contact_info`
- `faq`
- `qna`

Application procedures, contact information, submitted documents, FAQ, and Q&A information are not used by the current recommendation calculation and must not be extracted.

Extract only:

- subsidy amount calculation
- eligibility conditions
- duplicate-benefit or combination rules
- monthly exclusion rules

## Support Item Rules For Childcare Flexible Start Support

For this policy, keep the support item as `calculation_type="monthly_fixed"`.

Every support item must include:

- `support_item_id`
- `calculation_type`
- `monthly_amount`
- `max_months`
- `conditions`
- `evidence_snippets`

Use this exact support item pattern:

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

Do not use calculation type aliases such as:

- `fixed_amount`
- `fixed_monthly`
- `fixed_monthly_amount`
- `monthly`
- `period`
- `bonus`
- `support_type`

Do not output duplicate `support_item_id` values.

## Condition Schema: Strict

All calculation conditions must use only this structure:

```json
{
  "condition_id": "C-001",
  "field": "employee.weekly_work_hours_before",
  "operator": "gte",
  "expected": 35,
  "evidence_snippets": ["Exact source substring"]
}
```

Allowed condition fields are only:

- `condition_id`
- `field`
- `operator`
- `expected`
- `evidence_snippets`

Never use these fields anywhere inside a condition:

- `condition_type`
- `value`
- `unit`
- `description`
- `risk_condition_id`

Allowed operators:

```text
eq, neq, gt, gte, lt, lte, in, not_in
```

Represent units in the `field` name, not in a `unit` field.

Examples:

- weekly hours before reduction: `field="employee.weekly_work_hours_before"`, `operator="gte"`, `expected=35`
- weekly hours after reduction lower bound: `field="employee.weekly_work_hours_after"`, `operator="gt"`, `expected=30`
- weekly hours after reduction upper bound: `field="employee.weekly_work_hours_after"`, `operator="lte"`, `expected=35`
- daily reduced hours: `field="employee.daily_reduction_hours"`, `operator="gte"`, `expected=1`
- child age upper bound: `field="employee.child_age"`, `operator="lte"`, `expected=12`
- child elementary school grade upper bound: `field="employee.child_school_grade"`, `operator="lte"`, `expected=6`
- minimum use duration: `field="leave_event.duration_months"`, `operator="gte"`, `expected=1`
- wage reduction prohibition: `field="company.prohibits_wage_reduction"`, `operator="eq"`, `expected=true`
- employment rule requirement: `field="company.has_work_rules_for_reduction"`, `operator="eq"`, `expected=true`
- electronic attendance management: `field="company.has_electronic_attendance_management"`, `operator="eq"`, `expected=true`
- contract change requirement: `field="company.has_contract_change"`, `operator="eq"`, `expected=true`

Break complex source sentences into separate atomic conditions.

If one sentence contains multiple requirements, create one condition per requirement.

Separate:

- period and duration conditions
- weekly hour conditions
- daily hour conditions
- lower and upper bounds
- boolean operational requirements
- parenthetical clauses and provisos

Do not create duplicate `condition_id` values.

`condition_id` values must be globally unique across the entire candidate JSON.

Even when conditions belong to different support items, never reuse a `condition_id`.

Assign condition IDs as one global increasing sequence, such as `C-001`, `C-002`, `C-003`, across all support items.

If the same semantic condition is repeated under multiple support items, create a new unique `condition_id` each time. Do not reuse the old ID.

## Monthly Exclusion Rules

Do not encode monthly nonpayment or monthly exclusion rules as conditions.

Do not output them as `risk_conditions`.

Rules such as:

- missing clock-in or clock-out records exceeding 3 days in the month
- 4 or more missing attendance record days in the month
- overtime exceeding 10 hours in the month
- any rule where the support is not paid only for that affected month

must be placed in `unresolved_rules` with `rule_type="monthly_exclusion_rule"`.

Use this structure:

```json
{
  "rule_id": "UR-001",
  "rule_type": "monthly_exclusion_rule",
  "evidence_snippets": ["Exact source substring"]
}
```

Do not add `description`, `condition_type`, `value`, or `unit` to unresolved monthly exclusion rules.

## Combination Rules

Use `combination_rules` only when the source clearly identifies the target policy id or target policy context well enough for a reviewer to map without guessing.

Never output `UNKNOWN_POLICY_ID` anywhere.

Never output `UNKNOWN_POLICY_ID` in `combination_rules.target_policy_ids`.

Never output an empty `combination_rules.target_policy_ids` array.

If `target_policy_ids` would be empty, do not create a `combination_rules` item.

If a duplicate-benefit, overlapping-period, or shared-duration rule is source-backed but the target policy id is not clear, put it in `unresolved_rules` with `rule_type="ambiguous_target_policy"` instead of `combination_rules`.

Do not create a combination rule by guessing a target policy id.

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
  "evidence_snippets": ["Exact source substring"]
}
```

Do not add `description` to unresolved rules.

Do not use `unresolved_rules` as a dumping ground. If the current schema can represent the rule as a support item, condition, or combination rule, use the normal field instead.

## Non-Calculation Content

Do not output application procedures, application steps, required documents, contact information, FAQ, or Q&A content.

Do not convert application steps into eligibility conditions unless the source explicitly states they are support requirements.

Ignore text whose only purpose is to explain how to apply, where to ask questions, what documents to submit, or general Q&A guidance.

## Evidence Rules

Every `evidence_snippets` value must be copied from the source text.

Preserve the source wording. Do not translate, summarize, repair, or normalize the evidence text.

Prefer short, single-line evidence snippets copied exactly from the source.

Do not combine multiple distant source lines into one evidence snippet unless the combined text appears contiguously in the raw source.

Do not remove words, insert spaces, change punctuation, or rewrite garbled text in evidence snippets.

Use only exact substrings that exist in the raw policy source text.

Do not rewrite table contents into human-readable sentences.

Do not merge multiple table lines or cells into one new sentence.

Do not change line breaks, spacing, special characters, parentheses, bullets, middle dots, or garbled source characters.

When taking evidence from a table, copy only a short original cell fragment or a short contiguous row fragment. Do not summarize the whole table.

If you are not certain a snippet is an exact raw-text substring, set that field's `evidence_snippets` to `[]`.

For table-based evidence, if you cannot confidently copy an exact raw-text substring, leave `evidence_snippets` as `[]`.

For `unresolved_rules`, evidence must also be copied as short raw-text fragments only. Do not rewrite or explain the rule in evidence.

Never construct a new sentence for evidence.

For table-based policies, do not rewrite table conditions into human-readable sentences.

For table evidence, use only short exact cell fragments or short exact contiguous row fragments.

Do not combine amount, duration, and condition values from different table cells into a newly written sentence.

Never combine multiple cells or multiple rows to create one evidence sentence.

Do not combine source table amount, period, and condition cells into evidence unless those cells appear contiguously in the raw source text exactly as copied.

For unresolved rules, leave `evidence_snippets` empty if the exact raw substring is uncertain. Do not paraphrase the rule.

For Q&A text, do not summarize or rewrite question-and-answer content into a new sentence.

For unresolved rules derived from Q&A text, use only exact raw substrings. If exact copying is uncertain, set `evidence_snippets` to `[]`.

Do not generate sentences merely to fill evidence.

Prioritize structurally valid output over filling evidence when exact source matching is uncertain.

For `flexible_work_incent` 선택근무 conditions, do not use rewritten evidence such as:

- `선택근무 해당 월에 총 6시간 이상 단축하여야 함`
- `선택근무 해당 일에 변경전 1일 소정근로시간과 비교하여 1시간 이상 단축하여야 함`
- `선택근무는 8시간 미만으로 근무할 때 1시간 이상 단축하여 근무하여야 하며`

Use exact raw substrings only, such as:

- `해당 일에 변경전 1일 소정근로시간과 비교하여 1시간 이상 단축하여야 하며 해당 월에 총 6시간 이상 단축하여야 함`
- `(월 6시간 이상 단축, 단축일에 1시간 이상 단축)`
- `유연근무 장려금을 지원받기 위해서는 8시간 미만으로 근무할 때 1시간 이상 단축하여 근무하여야 하며, 단축된 총 시간의 합이 6시간 이상이어야 합니다.`

If these exact raw substrings cannot be copied with confidence, leave that condition's `evidence_snippets` as `[]` or move the rule to `unresolved_rules` with empty evidence.

Small whitespace or line-break differences may be handled by the validation gate, but you should still copy evidence as closely as possible.

Every support item, condition, combination rule, and unresolved rule must have evidence.

Top-level `evidence_snippets` must contain only short exact raw-text substrings.

For top-level `evidence_snippets`, prefer one short exact substring copied directly from the source title or policy-name line.

Only write top-level `evidence_snippets` when you are certain each snippet is an exact raw-text substring.

If you are not certain that any short title or policy-name substring is exact, set top-level `evidence_snippets` to `[]`.

Do not use policy summaries, rewritten sentences, normalized text, translated text, or semantically similar text as evidence.

If `support_items`, `conditions`, and `unresolved_rules` already have enough source-backed evidence, keep top-level `evidence_snippets` limited to a short exact title or policy-name substring only.

## Final Self-Check

Before returning JSON, verify:

- `review_status` is exactly `"needs_review"`.
- No `approval_status` or policy-level `status` field exists.
- No `risk_conditions` field exists.
- No `application_process`, `application_steps`, `required_documents`, `contact_info`, `faq`, or `qna` field exists.
- `support_items[*].calculation_type` is exactly `"monthly_fixed"` for this policy.
- `support_items[*].monthly_amount` and `support_items[*].max_months` are present when source-backed.
- Every condition has only `condition_id`, `field`, `operator`, `expected`, and `evidence_snippets`.
- Every `condition_id` is globally unique across the whole candidate JSON, not just inside one support item.
- No condition contains `condition_type`, `value`, `unit`, `description`, or `risk_condition_id`.
- Monthly nonpayment rules are in `unresolved_rules` with `rule_type="monthly_exclusion_rule"`.
- No `UNKNOWN_POLICY_ID` exists anywhere.
- No `combination_rules[*].target_policy_ids` is empty.
- Ambiguous target policies are in `unresolved_rules`, not `combination_rules`.
- `source_document_id`, `source_url`, and `source_file` are empty unless present in source text.
- Every evidence snippet is source-backed.
- Top-level `evidence_snippets` contains only short exact raw-text substrings, preferably the source title or policy-name line.
- No evidence snippet is a rewritten sentence, table summary, normalized sentence, or merged multi-cell text.
- Empty `evidence_snippets` is better than non-substring evidence when exact copying is uncertain.
- Table evidence uses only exact source cell or row fragments and never newly constructed sentences.
- Q&A evidence is never summarized or rewritten.
- Uncertain table or Q&A evidence is left as `[]` instead of invented.
- No duplicate `support_item_id`, `condition_id`, or `rule_id` values exist.
- No value is inferred from outside the source.

Policy source text:

```text
{{SOURCE_TEXT}}
```
