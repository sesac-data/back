from services.calculation_service import (
    apply_monthly_exclusion,
    calculate_monthly_fixed_policy_support,
)


def policy(monthly_amount=300000, monthly_exclusion=True, monthly_cap_ratio=None):
    support = {
        "calculation_type": "monthly_fixed",
        "monthly_amount": monthly_amount,
        "evidence_snippets": ["월 지원액 근거"],
    }
    if monthly_exclusion:
        support["monthly_exclusion"] = True
    if monthly_cap_ratio is not None:
        support["monthly_cap_ratio"] = monthly_cap_ratio
    return {
        "policy_id": "policy-exclusion",
        "policy_key": "policy-exclusion",
        "policy_name": "Monthly Exclusion Test Policy",
        "review_status": "approved",
        "evidence_snippets": ["정책 근거"],
        "support_items": [
            {
                "support_type": "monthly_fixed",
                "conditions": [],
                "support": support,
                "evidence_snippets": ["해당월 부지급 근거"],
            }
        ],
    }


def _exclusion_step(result):
    for step in result["calculation_steps"]:
        if step.get("step") == "monthly_exclusion":
            return step
    return None


def test_excluded_months_reduce_eligible_months():
    result = calculate_monthly_fixed_policy_support(
        policy(monthly_amount=300000),
        {"leave_event": {"excluded_months": 2}},
        requested_months=6,
    )
    # 6 eligible - 2 excluded = 4 -> 300,000 * 4
    assert result["eligible_months"] == 4
    assert result["estimated_total_amount"] == 1200000
    step = _exclusion_step(result)
    assert step["reason"] == "monthly_exclusion_applied"
    assert step["input"]["excluded_months"] == 2


def test_missing_exclusion_data_pays_full_with_note():
    result = calculate_monthly_fixed_policy_support(
        policy(monthly_amount=300000),
        {"leave_event": {}},
        requested_months=6,
    )
    assert result["eligible_months"] == 6
    assert result["estimated_total_amount"] == 1800000
    assert _exclusion_step(result)["reason"] == "no_exclusion_data"


def test_excluded_exceeds_eligible_floors_at_zero():
    result = calculate_monthly_fixed_policy_support(
        policy(monthly_amount=300000),
        {"leave_event": {"excluded_months": 10}},
        requested_months=6,
    )
    assert result["eligible_months"] == 0
    assert result["estimated_total_amount"] == 0


def test_no_marker_is_unchanged_no_exclusion_step():
    result = calculate_monthly_fixed_policy_support(
        policy(monthly_amount=300000, monthly_exclusion=False),
        {"leave_event": {"excluded_months": 2}},
        requested_months=6,
    )
    assert result["eligible_months"] == 6
    assert result["estimated_total_amount"] == 1800000
    assert _exclusion_step(result) is None


def test_exclusion_combined_with_wage_cap():
    result = calculate_monthly_fixed_policy_support(
        policy(monthly_amount=1000000, monthly_cap_ratio=0.8),
        {"leave_event": {"excluded_months": 1}, "employee": {"monthly_wage": 500000}},
        requested_months=3,
    )
    # wage cap 500,000*0.8=400,000; months 3-1=2 -> 400,000 * 2 = 800,000
    assert result["estimated_total_amount"] == 800000
    assert result["eligible_months"] == 2


def test_helper_noop_without_marker():
    adjusted, step = apply_monthly_exclusion(
        6, {"calculation_type": "monthly_fixed"}, {"leave_event": {"excluded_months": 2}}
    )
    assert adjusted == 6
    assert step is None


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("test_monthly_exclusion passed")
