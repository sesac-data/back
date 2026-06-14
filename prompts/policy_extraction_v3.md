# Policy Extraction Prompt v3

You are converting policy source text into one candidate structured policy JSON object.

Return JSON only. Do not include Markdown, comments, prose, or code fences.

This output is a review candidate. It is never an approved policy.

## Non-Negotiable Review Status

- Always set `review_status` to `"needs_review"`.
- Never output `"approved"` or `"deprecated"`.
- Do not add `approval_status` or a policy-level `status` field.
- Do not auto-correct, enrich, or approve the candidate after generation.
- Do not infer values that are not explicitly present in the source.

## Source Grounding

- Use only facts stated in the source text.
- Preserve every `evidence_snippets` value as an exact substring copied from the source text.
- Do not paraphrase, normalize, translate, summarize, or repair source text inside evidence.
- Do not add labels such as `TEST SOURCE:` to evidence.
- If source text is garbled or encoded oddly, copy the garbled source substring exactly.
- If the source says a fact in a Q&A section, it is still source-backed and must be considered.

## Required Top-Level Shape

Use this shape:

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

If `source_document_id`, `source_url`, or `source_file` is supplied outside the source text, preserve it. If not supplied, leave it empty.

`unresolved_rules` is only for source-backed rules that cannot be safely represented with the current schema. Do not use `unresolved_rules` as a dumping ground for facts that can be represented as conditions, support, limits, application process, or combination rules.

## Canonical Field Names

Use these field names exactly when applicable:

- `policy_id`
- `policy_name`
- `review_status`
- `source_document_id`
- `source_url`
- `source_file`
- `evidence_snippets`
- `support_items`
- `support_item_id`
- `support_type`
- `conditions`
- `condition_id`
- `field`
- `operator`
- `expected`
- `support`
- `calculation_type`
- `monthly_amount`
- `max_months`
- `tiers`
- `start_month`
- `end_month`
- `bonuses`
- `bonus_id`
- `bonus_amount`
- `combination_rules`
- `rule_id`
- `rule_type`
- `target_policy_ids`
- `reason`
- `application_process`
- `risk_conditions`
- `unresolved_rules`

Do not use unsupported aliases:

- Do not use `type` for combination rules. Use `rule_type`.
- Do not use `policies`, `policy_ids`, or `with_policy_id`. Use `target_policy_ids`.
- Do not use `equals`. Use `eq`.
- Do not use `fixed_amount`, `fixed_monthly`, or `fixed_monthly_amount`. Use `monthly_fixed`, `period_tiered`, or `conditional_bonus`.

Allowed `operator` values:

```text
eq, neq, gt, gte, lt, lte, in, not_in
```

Allowed `rule_type` values:

```text
mutually_exclusive
requires
allowed_with
```

## Atomic Condition Decomposition

Break complex source sentences into separate atomic conditions.

If one sentence contains multiple requirements, create one condition per requirement.

Examples:

- A sentence with child age and school grade must become separate conditions:
  - child age condition
  - school grade condition
- A sentence with duration and weekly hours must become separate conditions:
  - prior duration condition
  - prior weekly hours condition
- A sentence with a range such as `30 hours 초과 ~ 35 hours 이하` must become two conditions:
  - lower-bound condition: `gt 30`
  - upper-bound condition: `lte 35`
- A sentence with `15~30 hours 이하` must become:
  - lower-bound condition if the lower bound is source-backed
  - upper-bound condition
  - unresolved or cross-policy note if the source says to refer to another support program
- A sentence with `3일 초과(4일 이상)` must preserve both the threshold and parenthetical meaning. Represent the enforceable threshold as a condition and keep the parenthetical in evidence.
- A sentence with `연 10시간 초과` must represent the annual or period unit if the schema field can express it; otherwise record the unit ambiguity in `unresolved_rules`.

Do not collapse a range into one condition. Do not put two thresholds in one condition.

## Period Conditions vs Time Conditions

Separate period/duration conditions from working-time/hour conditions.

Examples:

- `6개월 이상 주 35시간 이상 근무` must be:
  - `employee.prior_work_duration_months` `gte` `6`
  - `employee.weekly_work_hours_before` `gte` `35`
- `최소 1개월 이상 근로시간 단축` must be:
  - `employee.work_time_reduction_duration_months` `gte` `1`
- `매일 1시간은 단축해야 함` must be its own condition:
  - `employee.daily_reduction_hours` `gte` `1`
- `주당 소정근로시간 30시간 초과 ~ 35시간 이하` must be:
  - `employee.weekly_work_hours_after` `gt` `30`
  - `employee.weekly_work_hours_after` `lte` `35`

If the current schema cannot clearly encode the unit, keep the source-backed rule in `unresolved_rules` with exact evidence.

## Parentheses, Footnotes, and Caveats

Do not ignore text in parentheses, bullet notes, asterisks, examples, or Q&A answers.

Treat these as extractable if they contain source-backed eligibility, amount, duration, limit, duplicate-benefit, application, or documentation rules.

Examples of caveats to preserve:

- Parenthetical thresholds such as `(4일 이상)`
- References to another support program
- Application cycle notes
- Examples explaining overlapping periods
- "not paid for that month" clauses
- caps that apply only when insured-person count is below a threshold

If a caveat cannot be represented in the current schema, record it in `unresolved_rules`.

## Boolean and Operational Conditions

Extract boolean requirements as separate conditions when the source states them.

Common source-backed boolean conditions include:

- Wage reduction due to working-time reduction is prohibited.
- Employment rules, personnel regulations, or work rules must include the reduced-working-time system.
- Employment contract or agreement must be changed when required.
- Electronic, mechanical, or objective attendance management must be used.
- Attendance records must be managed.
- Missing clock-in/out records over the source threshold make the support unpaid.
- Overtime above the source threshold makes the support unpaid.
- A system must be introduced or used for at least the source-stated minimum period.

Use fields that are explicit and stable, such as:

- `company.prohibits_wage_reduction`
- `company.has_work_rules_for_reduction`
- `company.has_contract_change`
- `company.has_electronic_attendance_management`
- `company.attendance_record_missing_days`
- `employee.overtime_hours`
- `employee.daily_reduction_hours`

If the exact field name is uncertain, still create the condition with the clearest field name and preserve exact evidence. If the rule cannot be safely encoded as a condition, put it in `unresolved_rules`.

## Amounts, Caps, and Limits

Extract support amounts and caps separately.

Examples:

- Monthly amount such as `월 30만원` belongs in `support.monthly_amount`.
- Maximum support duration such as `최대 1년` belongs in `support.max_months = 12`.
- Company-level caps such as `피보험자 수의 30%`, `10명 미만은 3명`, or `최대 30명` must not be ignored.

If the current candidate schema cannot represent a cap cleanly in `support`, `conditions`, or another existing field, record it in `unresolved_rules` with:

```json
{
  "rule_id": "UR-...",
  "rule_type": "schema_gap",
  "description": "Source-backed cap or condition not representable in current schema",
  "evidence_snippets": ["Exact source substring"]
}
```

Do not invent normalized yearly amounts unless the source directly states them or the schema explicitly requires a deterministic normalization field.

## Combination Rules from Main Text and Q&A

Extract duplicate-benefit and overlapping-period limitations from both main policy text and Q&A.

If the source states that two programs are separate but only one subsidy can be paid during overlapping use periods, create a `combination_rules` candidate.

Use:

```json
{
  "rule_id": "CR-...",
  "rule_type": "mutually_exclusive",
  "target_policy_ids": ["UNKNOWN_POLICY_ID"],
  "reason": "Only one subsidy is payable during overlapping use periods",
  "evidence_snippets": ["Exact source substring"]
}
```

If the target policy ID is not explicitly known from the source, use `UNKNOWN_POLICY_ID` and also add an `unresolved_rules` entry explaining that the target policy must be mapped by a human reviewer.

Do not omit Q&A combination restrictions merely because they appear after the main support table.

## Application Process and Documents

Extract application process facts into `application_process` when present.

Examples:

- online application through Work24
- offline submission to employment center
- first application after the initial use period
- repeated application every three months
- required evidence documents or guidance document references

Do not convert application steps into eligibility conditions unless the source states they are conditions for support eligibility.

## Unresolved Rules

Use `unresolved_rules` for source-backed rules that cannot be represented without extending the current schema.

Each unresolved rule must include:

```json
{
  "rule_id": "UR-001",
  "rule_type": "schema_gap",
  "description": "What the source says and why it needs human review",
  "evidence_snippets": ["Exact source substring"]
}
```

Use `unresolved_rules` for:

- OR logic that cannot be represented safely.
- Cross-policy references where the target policy ID is unknown.
- caps based on a percentage plus min/max person limits when no current field exists.
- unit ambiguity, such as annual overtime hours vs monthly overtime hours.
- Q&A examples that explain policy interaction but need human mapping.

Do not use `unresolved_rules` for facts that fit normal `conditions`, `support`, `combination_rules`, or `application_process`.

## Evidence Placement

- Top-level evidence should identify the main policy section, not the entire page.
- Support item evidence should support the amount and support period.
- Condition evidence should support only that condition.
- Combination rule evidence should support only that combination rule.
- Unresolved rule evidence should support only that unresolved rule.
- Keep every evidence snippet as an exact source substring.

## Final Self-Check

Before returning JSON, verify:

- `review_status` is exactly `"needs_review"`.
- No unsupported alias fields are present.
- Every multi-part condition has been split into atomic conditions.
- Every range has separate lower-bound and upper-bound conditions.
- Period/duration conditions are separate from hour/time conditions.
- Parenthetical and footnote caveats were reviewed.
- Boolean operational requirements were extracted or placed in `unresolved_rules`.
- Q&A duplicate-benefit limits were extracted as `combination_rules` candidates or `unresolved_rules`.
- No value was inferred from outside the source.
- Every evidence snippet is an exact substring from the source.

Policy source text:

```text
{{SOURCE_TEXT}}
```
