-- TEST FIXTURE ONLY.
-- These rows are not real policy data and must not be represented as source-backed operating policy content.

INSERT INTO subsidy_policies (
  policy_id,
  policy_name,
  policy_version,
  review_status,
  is_active,
  policy_json
) VALUES
(
  'smoke-optimal-a',
  'Smoke Optimal Policy A Fixture',
  'test-2026-06-13',
  'approved',
  TRUE,
  '{
    "policy_id": "smoke-optimal-a",
    "policy_key": "smoke-optimal-a",
    "policy_name": "Smoke Optimal Policy A Fixture",
    "review_status": "approved",
    "evidence_snippets": [
      "TEST FIXTURE evidence: approved optimal policy A."
    ],
    "support_items": [
      {
        "support_type": "monthly_fixed",
        "conditions": [
          {
            "condition_id": "company-size-small",
            "field": "company.size",
            "operator": "eq",
            "expected": "small",
            "evidence_snippets": [
              "TEST FIXTURE evidence: small companies are eligible."
            ]
          }
        ],
        "support": {
          "calculation_type": "monthly_fixed",
          "monthly_amount": 100,
          "max_months": 6,
          "evidence_snippets": [
            "TEST FIXTURE evidence: policy A pays 100 per month."
          ]
        },
        "evidence_snippets": [
          "TEST FIXTURE evidence: policy A support item."
        ]
      }
    ],
    "combination_rules": []
  }'::jsonb
),
(
  'smoke-optimal-b',
  'Smoke Optimal Policy B Fixture',
  'test-2026-06-13',
  'approved',
  TRUE,
  '{
    "policy_id": "smoke-optimal-b",
    "policy_key": "smoke-optimal-b",
    "policy_name": "Smoke Optimal Policy B Fixture",
    "review_status": "approved",
    "evidence_snippets": [
      "TEST FIXTURE evidence: approved optimal policy B."
    ],
    "support_items": [
      {
        "support_type": "monthly_fixed",
        "conditions": [
          {
            "condition_id": "company-size-small",
            "field": "company.size",
            "operator": "eq",
            "expected": "small",
            "evidence_snippets": [
              "TEST FIXTURE evidence: small companies are eligible."
            ]
          }
        ],
        "support": {
          "calculation_type": "monthly_fixed",
          "monthly_amount": 80,
          "max_months": 6,
          "evidence_snippets": [
            "TEST FIXTURE evidence: policy B pays 80 per month."
          ]
        },
        "evidence_snippets": [
          "TEST FIXTURE evidence: policy B support item."
        ]
      }
    ],
    "combination_rules": []
  }'::jsonb
)
ON CONFLICT (policy_id, policy_version) DO UPDATE SET
  policy_name = EXCLUDED.policy_name,
  review_status = EXCLUDED.review_status,
  is_active = EXCLUDED.is_active,
  policy_json = EXCLUDED.policy_json,
  updated_at = NOW();
