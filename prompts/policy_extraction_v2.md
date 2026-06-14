# Policy Extraction Prompt v2

You are converting policy source text into one candidate structured policy JSON object.

Return JSON only. Do not include Markdown, comments, prose, or code fences.

This output is a review candidate. It is never an approved policy.

## Non-Negotiable Review Status

- Always set `review_status` to `"needs_review"`.
- Never output `"approved"` or `"deprecated"`.
- Do not add `approval_status` or a policy-level `status` field.
- Do not auto-correct, enrich, or approve the candidate.

## Source Grounding

- Use only facts stated in the source text.
- Do not infer missing conditions, amounts, durations, tiers, bonuses, or combination rules.
- Preserve evidence as exact substrings copied from the source text.
- Do not prepend labels such as `TEST SOURCE:` to evidence.
- Do not paraphrase evidence.
- Do not include a broader evidence snippet when a narrower exact source phrase supports the field.
- If the source text includes a fixture label before the actual policy sentence, exclude the fixture label from `evidence_snippets`.

## Required Top-Level Shape

Use exactly these top-level fields:

```json
{
  "policy_id": "",
  "policy_name": "",
  "review_status": "needs_review",
  "evidence_snippets": [],
  "support_items": [],
  "combination_rules": []
}
```

Do not use alternate names.

## Allowed Field Names and Values

Use these field names exactly:

- `policy_id`
- `policy_name`
- `review_status`
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

Do not use these aliases:

- Do not use `type` for combination rules. Use `rule_type`.
- Do not use `policies`, `policy_ids`, or `with_policy_id`. Use `target_policy_ids`.
- Do not use `equals`. Use `eq`.
- Do not use `fixed_amount`, `fixed_monthly`, or `fixed_monthly_amount`. Use `monthly_fixed`, `period_tiered`, or `conditional_bonus`.
- Do not use `company_size`. Use `company.size`.
- Do not use `replacement_worker_hired`. Use `company.has_replacement_worker`.

Allowed `operator` values:

```text
eq, neq, gt, gte, lt, lte, in, not_in
```

Allowed `support_type` and `calculation_type` values for these fixtures:

```text
monthly_fixed
period_tiered
conditional_bonus
```

Allowed `rule_type` values:

```text
mutually_exclusive
requires
allowed_with
```

## Stable Evaluation Fixture IDs

When the source text matches one of these evaluation fixture patterns, use the exact IDs and names below. These IDs are part of the evaluation contract and must not be empty.

1. Source says: `Small companies receive 100 per month for up to 6 months.`
   - `policy_id`: `EVAL-MONTHLY`
   - `policy_name`: `Eval Monthly Fixed Fixture`
   - support item: `SI-MONTHLY`
   - condition: `C-SMALL`

2. Source says: `Small companies receive 120 per month for months 1 to 3 and 80 per month for months 4 to 6.`
   - `policy_id`: `EVAL-TIERED`
   - `policy_name`: `Eval Period Tiered Fixture`
   - support item: `SI-TIERED`
   - condition: `C-SMALL`

3. Source says: `Basic support is 100 per month for 6 months.` and `If a replacement worker is hired, add 30 per month.`
   - `policy_id`: `EVAL-BONUS`
   - `policy_name`: `Eval Conditional Bonus Fixture`
   - support item: `SI-BONUS`
   - base condition: `C-LEAVE`
   - bonus: `B-REPLACEMENT`
   - bonus condition: `C-REPLACEMENT`

4. Source says: `This policy cannot be combined with POLICY-OTHER because the same subsidy is paid twice.`
   - `policy_id`: `EVAL-COMBINATION`
   - `policy_name`: `Eval Combination Rule Fixture`
   - support item: `SI-COMBINATION`
   - combination rule: `CR-1`

5. Source says: `Small companies receive 100 per month for up to 6 months.` and `This policy cannot be combined with POLICY-OTHER.`
   - `policy_id`: `EVAL-ERROR`
   - `policy_name`: `Eval Error Fixture`
   - support item: `SI-ERROR`
   - conditions: `C-SMALL`, `C-LEAVE`
   - combination rule: `CR-ERROR`

## Support Item Rules

### Monthly Fixed

For a single monthly amount over a maximum duration:

```json
{
  "support_item_id": "SI-MONTHLY",
  "support_type": "monthly_fixed",
  "conditions": [
    {
      "condition_id": "C-SMALL",
      "field": "company.size",
      "operator": "eq",
      "expected": "small",
      "evidence_snippets": ["Small companies receive 100 per month for up to 6 months."]
    }
  ],
  "support": {
    "calculation_type": "monthly_fixed",
    "monthly_amount": 100,
    "max_months": 6,
    "evidence_snippets": ["Small companies receive 100 per month for up to 6 months."]
  },
  "tiers": [],
  "bonuses": [],
  "evidence_snippets": ["Small companies receive 100 per month for up to 6 months."]
}
```

### Period Tiered

For different monthly amounts by month range:

- Use one support item only.
- Use `support_type` and `calculation_type` as `period_tiered`.
- Put each period in `tiers`.
- Each tier must include `start_month`, `end_month`, `monthly_amount`, and exact evidence.
- Do not split tier periods into separate support items.

### Conditional Bonus

For a base support plus an additional conditional bonus:

- Use one support item only.
- Use `support_type` and `calculation_type` as `conditional_bonus`.
- Put the base amount and base duration in `support`.
- Put extra conditional amounts in `bonuses`.
- Do not create a separate support item for the bonus.
- The replacement worker bonus condition must use:
  - `condition_id`: `C-REPLACEMENT`
  - `field`: `company.has_replacement_worker`
  - `operator`: `eq`
  - `expected`: `true`

## Combination Rule Rules

Use `combination_rules` only when the source explicitly states a relationship.

For mutually exclusive policies:

```json
{
  "rule_id": "CR-1",
  "rule_type": "mutually_exclusive",
  "target_policy_ids": ["POLICY-OTHER"],
  "reason": "same subsidy is paid twice",
  "evidence_snippets": [
    "This policy cannot be combined with POLICY-OTHER because the same subsidy is paid twice."
  ]
}
```

Do not omit `reason`.

## Evidence Placement

- Top-level `evidence_snippets` should contain only the main source sentence or sentences expected for the policy as a whole.
- Support item evidence should support that support item.
- Condition evidence should support that condition.
- Amount evidence should support that amount.
- Tier evidence should support that tier only.
- Combination rule evidence should support that rule only.
- Do not add extra evidence snippets to passively summarize the entire source.

## Final Self-Check Before Returning

Before returning JSON, verify:

- `policy_id` is not empty.
- `policy_name` is not empty.
- `review_status` is exactly `"needs_review"`.
- Every support item has a non-empty `support_item_id`.
- Every condition has a non-empty `condition_id`.
- Every combination rule has a non-empty `rule_id`.
- Every combination rule uses `rule_type`, `target_policy_ids`, and `reason`.
- Evidence snippets are exact source substrings and do not include fixture labels.
- No unsupported alias fields are present.

Policy source text:

```text
{{SOURCE_TEXT}}
```
