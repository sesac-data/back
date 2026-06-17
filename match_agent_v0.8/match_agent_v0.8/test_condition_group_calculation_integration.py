from services.calculation_service import (
    calculate_monthly_fixed_policy_support,
)


def policy_with_or_group():
    # 만 12세 이하 또는 초등학교 6학년 이하 (OR group) gating a monthly_fixed support
    return {
        "policy_id": "policy-or-group",
        "policy_key": "policy-or-group",
        "policy_name": "OR Group Test Policy",
        "review_status": "approved",
        "evidence_snippets": ["Policy-level source sentence."],
        "support_items": [
            {
                "support_type": "monthly_fixed",
                "conditions": [
                    {
                        "condition_group_id": "CG-CHILD",
                        "mode": "or",
                        "conditions": [
                            {
                                "condition_id": "C-AGE",
                                "field": "employee.child_age",
                                "operator": "lte",
                                "expected": 12,
                                "evidence_snippets": ["만 12세 이하"],
                            },
                            {
                                "condition_id": "C-GRADE",
                                "field": "employee.child_school_grade",
                                "operator": "lte",
                                "expected": 6,
                                "evidence_snippets": ["초등학교 6학년 이하"],
                            },
                        ],
                        "evidence_snippets": ["만 12세 이하 또는 초등학교 6학년 이하"],
                    }
                ],
                "support": {
                    "calculation_type": "monthly_fixed",
                    "monthly_amount": 300000,
                    "max_months": 12,
                    "evidence_snippets": ["월 30만원"],
                },
                "evidence_snippets": ["support item evidence"],
            }
        ],
    }


def test_or_group_branch_passes_makes_policy_eligible():
    # child_age 14 fails, but child_school_grade 5 passes -> OR passes -> eligible
    result = calculate_monthly_fixed_policy_support(
        policy_with_or_group(),
        {"employee": {"child_age": 14, "child_school_grade": 5}},
        requested_months=3,
    )
    assert result["eligible"] is True
    assert result["estimated_total_amount"] == 900000


def test_or_group_all_branches_fail_makes_policy_ineligible():
    result = calculate_monthly_fixed_policy_support(
        policy_with_or_group(),
        {"employee": {"child_age": 14, "child_school_grade": 8}},
        requested_months=3,
    )
    assert result["eligible"] is False


def test_or_group_passes_with_one_branch_missing():
    # only child_age provided (<=12), grade missing -> OR still passes
    result = calculate_monthly_fixed_policy_support(
        policy_with_or_group(),
        {"employee": {"child_age": 10}},
        requested_months=3,
    )
    assert result["eligible"] is True


def test_or_group_evidence_is_collected_into_result():
    result = calculate_monthly_fixed_policy_support(
        policy_with_or_group(),
        {"employee": {"child_age": 10}},
        requested_months=3,
    )
    evidence = result.get("evidence_snippets", [])
    assert any("또는" in snippet for snippet in evidence)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("test_condition_group_calculation_integration passed")
