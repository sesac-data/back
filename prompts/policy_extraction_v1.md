# Policy Extraction Prompt v1

You are converting policy source text into a candidate structured policy JSON object.

Return JSON only. Do not include Markdown, comments, or explanations.

Rules:

- The output is a candidate for human review, not an approved policy.
- Always set `review_status` to `"needs_review"`.
- Do not set `review_status` to `"approved"`.
- Do not infer facts that are not explicitly supported by the source text.
- Preserve evidence as exact source snippets in `evidence_snippets`.
- If the source does not state a condition, amount, duration, tier, bonus, or combination rule, leave it absent or null rather than guessing.
- Keep arrays deterministic where possible, but do not invent IDs not needed for comparison.
- Use `condition_id` for each condition.
- Use `support_item_id` for each support item.
- Use `rule_id` for each combination rule.
- Use `start_month` and `end_month` for period tiers.
- Use `combination_rules` only when the source explicitly states a relationship such as mutually exclusive, requires, or allowed with.

Expected JSON shape:

```json
{
  "policy_id": "",
  "policy_name": "",
  "review_status": "needs_review",
  "evidence_snippets": [],
  "support_items": [
    {
      "support_item_id": "",
      "support_type": "",
      "conditions": [
        {
          "condition_id": "",
          "field": "",
          "operator": "",
          "expected": null,
          "evidence_snippets": []
        }
      ],
      "support": {
        "calculation_type": "",
        "monthly_amount": null,
        "max_months": null,
        "evidence_snippets": []
      },
      "tiers": [],
      "bonuses": [],
      "evidence_snippets": []
    }
  ],
  "combination_rules": []
}
```

Policy source text:

```text
{{SOURCE_TEXT}}
```
