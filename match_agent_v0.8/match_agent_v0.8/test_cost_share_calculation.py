from services.calculation_service import (
    calculate_cost_share_policy_support,
    calculate_base_policy_support,
    normalize_policy_calculation_result,
)


def cost_share_policy(
    support_ratio=0.8,
    max_support_amount=10000000,
    cost_field="company.investment_cost",
    review_status="approved",
):
    return {
        "policy_id": "policy-cost-share",
        "policy_key": "policy-cost-share",
        "policy_name": "Cost Share Test Policy",
        "review_status": review_status,
        "evidence_snippets": ["투자비의 80%, 한도 1,000만원"],
        "support_items": [
            {
                "support_type": "cost_share",
                "conditions": [],
                "support": {
                    "calculation_type": "cost_share",
                    "support_ratio": support_ratio,
                    "max_support_amount": max_support_amount,
                    "cost_field": cost_field,
                    "evidence_snippets": ["투자비의 80%, 한도 1,000만원"],
                },
                "evidence_snippets": ["cost share support item evidence"],
            }
        ],
    }


def rule_input(investment_cost=5000000):
    return {"company": {"investment_cost": investment_cost}}


def test_ratio_applied_below_cap():
    result = calculate_cost_share_policy_support(
        cost_share_policy(),
        rule_input(investment_cost=5000000),
    )
    assert result["eligible"] is True
    assert result["status"] == "calculated"
    # 5,000,000 * 0.8 = 4,000,000 (< 10,000,000 cap)
    assert result["estimated_total_amount"] == 4000000


def test_cap_applied_when_exceeded():
    result = calculate_cost_share_policy_support(
        cost_share_policy(),
        rule_input(investment_cost=20000000),
    )
    # 20,000,000 * 0.8 = 16,000,000 -> capped to 10,000,000
    assert result["estimated_total_amount"] == 10000000
    cap_step = result["calculation_steps"][-1]
    assert cap_step["reason"] == "max_support_amount_applied"


def test_no_cap_when_max_absent():
    policy = cost_share_policy(max_support_amount=None)
    result = calculate_cost_share_policy_support(
        policy,
        rule_input(investment_cost=20000000),
    )
    # no cap inferred -> full 16,000,000
    assert result["estimated_total_amount"] == 16000000


def test_missing_cost_input_is_calculation_error_not_inferred():
    result = calculate_cost_share_policy_support(
        cost_share_policy(),
        {"company": {}},
    )
    assert result["status"] == "calculation_error"
    assert result["eligible"] is False
    assert result["estimated_total_amount"] is None
    assert result["calculation_steps"][-1]["reason"] == "cost_input_missing"


def test_invalid_support_ratio_is_calculation_error():
    result = calculate_cost_share_policy_support(
        cost_share_policy(support_ratio=None),
        rule_input(),
    )
    assert result["status"] == "calculation_error"
    assert result["calculation_steps"][-1]["reason"] == "support_ratio_invalid"


def test_needs_review_policy_is_not_calculated():
    result = calculate_cost_share_policy_support(
        cost_share_policy(review_status="needs_review"),
        rule_input(),
    )
    assert result["status"] == "needs_review"
    assert result["estimated_total_amount"] is None


def test_dispatched_via_calculate_base_policy_support():
    result = calculate_base_policy_support(
        cost_share_policy(),
        rule_input(investment_cost=5000000),
        requested_months=0,
    )
    assert result["calculation_type"] == "cost_share"
    assert result["estimated_total_amount"] == 4000000


def test_normalizes_into_standard_result():
    result = calculate_cost_share_policy_support(
        cost_share_policy(),
        rule_input(investment_cost=5000000),
    )
    normalized = normalize_policy_calculation_result(cost_share_policy(), result)
    assert normalized["status"] == "calculated"
    assert normalized["base_amount"] == 4000000
    assert normalized["estimated_total_amount"] == 4000000
    assert normalized["bonus_amount"] == 0


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("test_cost_share_calculation passed")
