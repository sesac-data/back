from services.calculation_service import (
    ASSUMED_DEFAULT_MONTHLY_WAGE,
    apply_monthly_wage_cap,
    calculate_monthly_fixed_policy_support,
    calculate_period_tiered_policy_support,
)


def monthly_fixed_policy(monthly_amount=1400000, monthly_cap_ratio=0.8, max_months=None):
    support = {
        "calculation_type": "monthly_fixed",
        "monthly_amount": monthly_amount,
        "evidence_snippets": ["월 지원액 근거"],
    }
    if monthly_cap_ratio is not None:
        support["monthly_cap_ratio"] = monthly_cap_ratio
    if max_months is not None:
        support["max_months"] = max_months
    return {
        "policy_id": "policy-wage-cap",
        "policy_key": "policy-wage-cap",
        "policy_name": "Wage Cap Test Policy",
        "review_status": "approved",
        "evidence_snippets": ["정책 근거"],
        "support_items": [
            {
                "support_type": "monthly_fixed",
                "conditions": [],
                "support": support,
                "evidence_snippets": ["support item 근거"],
            }
        ],
    }


def _cap_step(result):
    for step in result["calculation_steps"]:
        if step.get("step") == "monthly_wage_cap":
            return step
    return None


def test_cap_binding_uses_capped_monthly():
    result = calculate_monthly_fixed_policy_support(
        monthly_fixed_policy(monthly_amount=1400000, monthly_cap_ratio=0.8),
        {"employee": {"monthly_wage": 1000000}},
        requested_months=2,
    )
    # cap = 1,000,000 * 0.8 = 800,000 < 1,400,000 -> effective 800,000 * 2
    assert result["estimated_total_amount"] == 1600000
    step = _cap_step(result)
    assert step is not None
    assert step["reason"] == "wage_cap_applied"
    assert step["result"] == 800000
    assert step["input"]["assumed_wage"] is False


def test_cap_not_binding_keeps_amount():
    result = calculate_monthly_fixed_policy_support(
        monthly_fixed_policy(monthly_amount=300000, monthly_cap_ratio=0.8),
        {"employee": {"monthly_wage": 1000000}},
        requested_months=2,
    )
    # cap = 800,000 >= 300,000 -> unchanged
    assert result["estimated_total_amount"] == 600000
    assert _cap_step(result)["reason"] == "wage_cap_not_binding"


def test_missing_wage_uses_assumed_wage_with_warning():
    result = calculate_monthly_fixed_policy_support(
        monthly_fixed_policy(monthly_amount=5000000, monthly_cap_ratio=0.8),
        {"employee": {}},
        requested_months=1,
    )
    # assumed wage 3,000,000 * 0.8 = 2,400,000 < 5,000,000 -> capped to 2,400,000
    assert result["status"] == "calculated"
    assert result["estimated_total_amount"] == 2400000
    step = _cap_step(result)
    assert step["reason"] == "assumed_wage_used"
    assert step["input"]["assumed_wage"] is True
    assert step["input"]["wage_used"] == ASSUMED_DEFAULT_MONTHLY_WAGE


def test_no_cap_ratio_is_unchanged_no_cap_step():
    result = calculate_monthly_fixed_policy_support(
        monthly_fixed_policy(monthly_amount=1400000, monthly_cap_ratio=None),
        {"employee": {"monthly_wage": 1000000}},
        requested_months=2,
    )
    assert result["estimated_total_amount"] == 2800000
    assert _cap_step(result) is None


def period_tiered_policy(monthly_cap_ratio=0.8):
    return {
        "policy_id": "policy-tier-cap",
        "policy_key": "policy-tier-cap",
        "policy_name": "Tier Wage Cap Policy",
        "review_status": "approved",
        "evidence_snippets": ["정책 근거"],
        "support_items": [
            {
                "support_type": "period_tiered",
                "conditions": [],
                "support": {
                    "calculation_type": "period_tiered",
                    "monthly_cap_ratio": monthly_cap_ratio,
                    "tiers": [
                        {"start_month": 1, "end_month": 3, "monthly_amount": 1000000, "evidence_snippets": ["t1"]},
                        {"start_month": 4, "end_month": 12, "monthly_amount": 300000, "evidence_snippets": ["t2"]},
                    ],
                    "evidence_snippets": ["support 근거"],
                },
                "evidence_snippets": ["item 근거"],
            }
        ],
    }


def test_period_tiered_cap_applies_per_tier():
    result = calculate_period_tiered_policy_support(
        period_tiered_policy(monthly_cap_ratio=0.8),
        {"employee": {"monthly_wage": 1000000}},
        requested_months=4,
    )
    # cap 800,000: tier1 min(1,000,000,800,000)=800,000 x3 = 2,400,000;
    # tier2 min(300,000,800,000)=300,000 x1 = 300,000 -> total 2,700,000
    assert result["estimated_total_amount"] == 2700000
    assert result["eligible_months"] == 4
    cap_steps = [s for s in result["calculation_steps"] if s.get("step") == "monthly_wage_cap"]
    assert len(cap_steps) == 2


def test_helper_noop_without_ratio():
    effective, step = apply_monthly_wage_cap(
        1400000, {"calculation_type": "monthly_fixed"}, {"employee": {"monthly_wage": 1000000}}
    )
    assert effective == 1400000
    assert step is None


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("test_monthly_wage_cap passed")
