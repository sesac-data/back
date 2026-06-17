# Policy Extraction Prompt v6

You are converting one childcare-related employer subsidy policy source text into one candidate structured policy JSON object.

Return JSON only. Do not include Markdown, comments, prose, or code fences.

This output is a review candidate. It is never an approved policy.

This prompt is policy-agnostic. Do not assume a fixed calculation type. Read the source and choose the structure that matches the source.

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

## Ignore Non-Policy Page Text

The source is a crawled government web page. Ignore text whose only purpose is site structure or contact, including:

- top and side navigation menus and repeated menu lists
- search boxes, hashtags, and banners
- breadcrumb links such as `신청하러 가기`, `홈으로`, `본문 바로가기`
- the address, copyright, and call-center footer

Extract policy facts only from the body sections such as 지원대상, 대상, 지원요건, 지원내용, 금액, 지원수준, 지원기간, 지원한도, 지급제한, 유의사항.

Do not turn menu labels or page titles into conditions or support items.

Always set `policy_name` from the main body heading near 지원대상 or 대상 (the policy title line, for example `육아휴직지원금, 육아기 근로시간 단축 지원금` or `대체인력 지원금`). Never leave `policy_name` empty.

## Use Only This Document

Use only this document's text. Do not import conditions, amounts, durations, or rules from other childcare policies you may know about. If a rule, condition, or amount is not stated in THIS document's text, do not create it. If you cannot copy exact evidence for a rule from THIS document, do not output that rule at all.

For example, only output a child-age condition such as `만 12세 이하 또는 초등학교 6학년 이하` when that exact phrase appears in THIS document. Many policies do not state a child-age limit; in that case do not add one.

## Calculation Type Selection

Each support item must declare exactly one `calculation_type`. Allowed values are only:

- `monthly_fixed`
- `period_tiered`
- `conditional_bonus`

Choose the type from the source, not from a fixed assumption. Use these decision rules.

### Use `monthly_fixed` when

The source pays one flat monthly amount for a single eligible group, with one maximum duration.

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

### Use `period_tiered` when

The source pays different monthly amounts for different month ranges of the SAME support, such as a higher amount for the first months and a lower amount afterward.

Signals: `첫 3개월`, `이후`, `최초 N개월`, `N개월까지 ... 이후`, a 특례 first-period rate plus a later rate.

Put each rate in one tier. Do not split one tiered support into multiple `monthly_fixed` items.

```json
{
  "support_item_id": "SI-001",
  "calculation_type": "period_tiered",
  "tiers": [
    {
      "start_month": 1,
      "end_month": 3,
      "monthly_amount": 1000000,
      "evidence_snippets": ["Exact source substring for the first-period rate"]
    },
    {
      "start_month": 4,
      "end_month": 12,
      "monthly_amount": 300000,
      "evidence_snippets": ["Exact source substring for the later rate"]
    }
  ],
  "conditions": [],
  "evidence_snippets": ["Exact source substring"]
}
```

Tier rules:

- `start_month` and `end_month` are inclusive month numbers and must not overlap or leave gaps.
- If the source gives a first-period rate and an "이후" rate but no explicit end month for the later tier, set the later tier `end_month` to the support's overall `max` duration when the source states one (for example a 연간총액 that implies 12 months). If no total duration is stated, leave the later tier `end_month` equal to the first tier when uncertain is not acceptable; instead move the unclear duration to `unresolved_rules` with `rule_type="schema_gap"`.

### Use `conditional_bonus` when

The source pays a base monthly amount, plus an EXTRA amount only when an additional condition holds, such as `추가지원`, `인센티브`, `추가로 지급`.

Model the base amount as the support item and the extra amount as a bonus. Do not emit the bonus as a separate standalone support item.

```json
{
  "support_item_id": "SI-001",
  "calculation_type": "conditional_bonus",
  "monthly_amount": 300000,
  "max_months": 12,
  "conditions": [],
  "bonuses": [
    {
      "bonus_id": "B-001",
      "monthly_amount": 100000,
      "max_months": 12,
      "conditions": [
        {
          "condition_id": "C-010",
          "field": "employee.is_male_parental_leave",
          "operator": "eq",
          "expected": true,
          "evidence_snippets": ["Exact source substring"]
        }
      ],
      "evidence_snippets": ["Exact source substring for the extra amount"]
    }
  ],
  "evidence_snippets": ["Exact source substring"]
}
```

### Shared support item rules

Every support item must include `support_item_id`, `calculation_type`, `conditions`, and `evidence_snippets`.

- `monthly_fixed` items must also include `monthly_amount` and `max_months`.
- `period_tiered` items must also include `tiers`.
- `conditional_bonus` items must also include `monthly_amount`, `max_months`, and `bonuses`.

Do not use calculation type aliases such as `fixed_amount`, `fixed_monthly`, `monthly`, `period`, `bonus`, or `support_type`.

Do not output duplicate `support_item_id` values.

When several distinct, independent supports exist in one policy (for example 육아휴직지원금 and 육아기 근로시간 단축 지원금 as separate amounts), create one support item each. When one support has tiers or a bonus, keep it as a single item using `period_tiered` or `conditional_bonus`.

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

Field naming guidance:

- weekly hours before reduction: `field="employee.weekly_work_hours_before"`
- weekly hours after reduction lower bound: `field="employee.weekly_work_hours_after"`, `operator="gt"`
- weekly hours after reduction upper bound: `field="employee.weekly_work_hours_after"`, `operator="lte"`
- daily reduced hours: `field="employee.daily_reduction_hours"`
- child age upper bound: `field="employee.child_age"`, `operator="lte"`
- child elementary school grade upper bound: `field="employee.child_school_grade"`, `operator="lte"`
- minimum use duration in days: `field="leave_event.duration_days"`, `operator="gte"`
- minimum use duration in months: `field="leave_event.duration_months"`, `operator="gte"`
- company is priority support enterprise: `field="company.is_priority_support_enterprise"`, `operator="eq"`, `expected=true`
- wage reduction prohibition: `field="company.prohibits_wage_reduction"`, `operator="eq"`, `expected=true`
- employment rule requirement: `field="company.has_work_rules_for_reduction"`, `operator="eq"`, `expected=true`
- electronic attendance management: `field="company.has_electronic_attendance_management"`, `operator="eq"`, `expected=true`

If a needed field is not in this list, create a clear, descriptive `field` name in the same `area.attribute` style. Do not invent a numeric value that is not in the source.

Break complex source sentences into separate atomic conditions. If one sentence contains multiple requirements, create one condition per requirement. Separate period conditions, weekly hour conditions, daily hour conditions, lower and upper bounds, boolean operational requirements, and parenthetical provisos.

`condition_id` values must be globally unique across the entire candidate JSON, including conditions inside bonuses and inside different support items. Assign condition IDs as one global increasing sequence such as `C-001`, `C-002`, `C-003`. If the same semantic condition repeats, create a new unique `condition_id` each time. Do not reuse an ID.

## Monthly Exclusion Rules

Do not encode monthly nonpayment or monthly exclusion rules as conditions. Do not output them as `risk_conditions`.

Rules such as:

- missing clock-in or clock-out records exceeding 3 days in the month
- 4 or more missing attendance record days in the month
- overtime exceeding a stated number of hours in the month
- any rule where the support is not paid only for that affected month

must be placed in `unresolved_rules` with `rule_type="monthly_exclusion_rule"`.

```json
{
  "rule_id": "UR-001",
  "rule_type": "monthly_exclusion_rule",
  "evidence_snippets": ["Exact source substring"]
}
```

Do not add `description`, `condition_type`, `value`, or `unit` to unresolved rules.

## Combination Rules

Use `combination_rules` only when the source clearly identifies the target policy id or target policy context well enough for a reviewer to map without guessing.

Never output `UNKNOWN_POLICY_ID` anywhere, including in `combination_rules.target_policy_ids`.

Never output an empty `combination_rules.target_policy_ids` array. If it would be empty, do not create the rule.

If a duplicate-benefit, overlapping-period, or shared-duration rule is source-backed but the target policy id is not clear, put it in `unresolved_rules` with `rule_type="ambiguous_target_policy"` instead of `combination_rules`.

Do not create a combination rule by guessing a target policy id. Do not output duplicate `rule_id` values.

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

Use `unresolved_rules` for genuine schema gaps such as headcount caps (`전년도 말일 고용보험 피보험자 수의 30%`), shared-duration caps (`사용기간을 합산하여 최대 1년`), OR conditions (`만 12세 이하 또는 초등학교 6학년 이하`), and monthly caps (`임금액의 80%를 초과할 수 없음`). Do not use it as a dumping ground for rules the normal schema can already represent.

## Evidence Rules

Every `evidence_snippets` value must be copied from the source text exactly.

- Preserve the source wording. Do not translate, summarize, repair, or normalize evidence text.
- Use only exact substrings that exist in the raw policy source text.
- Prefer short, single-line evidence snippets copied exactly from the source.
- Do not remove words, insert spaces, change punctuation, fix typos, or rewrite garbled text in evidence snippets.
- Do not change line breaks, spacing, special characters, parentheses, bullets, or middle dots.
- Do not drop a middle clause to make a cleaner sentence. Copy the full contiguous source line. For example, if the source line is `전면도입은 주당 실근로시간을 2시간 이상, 부분도입은 2시간 미만 단축하는 경우를 말합니다.`, copy the whole line; do not shorten it to `전면도입은 주당 실근로시간을 2시간 이상 단축하는 경우를 말합니다.`. If you only need part of it, copy a shorter exact prefix that ends at a real boundary, such as `전면도입은 주당 실근로시간을 2시간 이상`.

Table evidence is the most common failure. Follow these rules strictly:

- Copy only ONE short original cell fragment or ONE short contiguous row fragment per snippet.
- NEVER join multiple table rows or cells into one snippet.
- NEVER insert `\n` to glue separate lines together. If two pieces of text are on different source lines, they are different snippets.
- Do not combine an amount cell, a duration cell, and a condition cell from different rows into one evidence sentence.
- Do not rewrite table contents into a human-readable sentence.

When a table gives amounts that depend on a group (for example 피보험자수 30인 미만 / 30인 이상, or 육아휴직 / 육아기 근로시간 단축), copy only the single relevant cell as evidence, such as `30인 미만` or `140만원`.

Forbidden table-merge example (never produce evidence like this):

```text
육아휴직,\n출산전·후휴가\n유산·사산휴가\n30인 이상\n130만원
```

That string glues five separate source lines and is not a contiguous substring. Instead use one short cell fragment per snippet, or `[]` if uncertain.

If you are not certain a snippet is an exact raw-text substring, set that field's `evidence_snippets` to `[]`.

For `unresolved_rules`, combination rules, and Q&A-derived rules, evidence must also be short exact raw-text fragments only. If exact copying is uncertain, leave `evidence_snippets` as `[]`. Never paraphrase or reconstruct.

Do not generate sentences merely to fill evidence. Prioritize structurally valid output over filling evidence when exact source matching is uncertain. Empty `evidence_snippets` is better than non-substring evidence.

Every support item, tier, bonus, condition, combination rule, and unresolved rule must have evidence unless exact copying is uncertain, in which case use `[]`.

For top-level `evidence_snippets`, prefer one short exact substring copied directly from the source title or policy-name line. If you are not certain it is an exact raw-text substring, set top-level `evidence_snippets` to `[]`.

## Final Self-Check

Before returning JSON, verify:

- `review_status` is exactly `"needs_review"`.
- No `approval_status` or policy-level `status` field exists.
- No `risk_conditions` field exists.
- No `application_process`, `application_steps`, `required_documents`, `contact_info`, `faq`, or `qna` field exists.
- Every `support_items[*].calculation_type` is one of `monthly_fixed`, `period_tiered`, or `conditional_bonus`, and matches the source structure.
- A first-period-then-later amount uses one `period_tiered` item, not two `monthly_fixed` items.
- An extra `인센티브` or `추가지원` amount uses a `bonuses` entry on a `conditional_bonus` item, not a standalone support item.
- `period_tiered` items have non-overlapping, gap-free `tiers`.
- Every condition has only `condition_id`, `field`, `operator`, `expected`, and `evidence_snippets`.
- Every `condition_id` is globally unique across the whole candidate JSON, including inside bonuses.
- No condition contains `condition_type`, `value`, `unit`, `description`, or `risk_condition_id`.
- Monthly nonpayment rules are in `unresolved_rules` with `rule_type="monthly_exclusion_rule"`.
- No `UNKNOWN_POLICY_ID` exists anywhere.
- No `combination_rules[*].target_policy_ids` is empty. Ambiguous targets are in `unresolved_rules`.
- `source_document_id`, `source_url`, and `source_file` are empty unless present in source text.
- Every evidence snippet is an exact raw-text substring.
- No evidence snippet joins multiple table rows or uses `\n` to glue separate lines.
- No evidence snippet is a rewritten sentence, table summary, or merged multi-cell text.
- Empty `evidence_snippets` is used wherever exact copying is uncertain.
- No duplicate `support_item_id`, `condition_id`, `bonus_id`, or `rule_id` values exist.
- No value is inferred from outside the source.

Policy source text:

```text
{{SOURCE_TEXT}}
```
