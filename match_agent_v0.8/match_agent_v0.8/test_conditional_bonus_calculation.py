from services.calculation_service import (
    calculate_conditional_bonus_policy_support
)


def rule_input(
    company_size="small",
    has_replacement_worker=True
):

    return {
        "company": {
            "size": company_size,
            "has_replacement_worker": has_replacement_worker
        }
    }


def base_conditions(
    expected_company_size="small"
):

    return [
        {
            "condition_id":
                "base-company-size",
            "field":
                "company.size",
            "operator":
                "eq",
            "expected":
                expected_company_size,
            "evidence_snippets":
                [
                    "Small companies satisfy the base support condition."
                ]
        }
    ]


def bonus_conditions(
    expected=True
):

    return [
        {
            "condition_id":
                "bonus-replacement-worker",
            "field":
                "company.has_replacement_worker",
            "operator":
                "eq",
            "expected":
                expected,
            "evidence_snippets":
                [
                    "Replacement worker condition is required for bonus."
                ]
        }
    ]


def monthly_base_support():

    return {
        "calculation_type":
            "monthly_fixed",
        "monthly_amount":
            100000,
        "max_months":
            6,
        "evidence_snippets":
            [
                "Base support is 100000 per month."
            ]
    }


def conditional_bonus(
    monthly_amount=50000,
    max_months=3,
    expected_replacement_worker=True
):

    return {
        "benefit_id":
            "replacement-worker-bonus",
        "bonus_type":
            "replacement_worker",
        "calculation_type":
            "monthly_fixed",
        "conditions":
            bonus_conditions(
                expected_replacement_worker
            ),
        "monthly_amount":
            monthly_amount,
        "max_months":
            max_months,
        "evidence_snippets":
            [
                "Bonus pays 50000 per month when replacement worker condition is met."
            ]
    }


def conditional_bonus_policy(
    review_status="approved",
    base_support=None,
    bonuses=None,
    expected_company_size="small"
):

    if base_support is None:

        base_support = monthly_base_support()

    if bonuses is None:

        bonuses = [
            conditional_bonus()
        ]

    return {
        "policy_id":
            "policy-conditional-bonus-test-fixture",
        "policy_key":
            "policy-conditional-bonus-test-fixture",
        "policy_name":
            "Conditional Bonus Test Fixture Policy",
        "review_status":
            review_status,
        "evidence_snippets":
            [
                "Test fixture policy-level evidence."
            ],
        "support_items":
            [
                {
                    "support_type":
                        base_support.get(
                            "calculation_type"
                        ),
                    "conditions":
                        base_conditions(
                            expected_company_size
                        ),
                    "support":
                        base_support,
                    "conditional_bonuses":
                        bonuses,
                    "evidence_snippets":
                        [
                            "Test fixture support item evidence."
                        ]
                }
            ]
    }


def test_bonus_applies_and_is_added_to_base_amount():

    result = calculate_conditional_bonus_policy_support(
        conditional_bonus_policy(),
        rule_input(),
        requested_months=3
    )

    assert result["review_status"] == "approved"
    assert result["eligible"] is True
    assert result["status"] == "calculated"
    assert result["base_amount"] == 300000
    assert result["bonus_amount"] == 150000
    assert result["estimated_total_amount"] == 450000
    assert result["applied_bonuses"][0]["benefit_id"] == "replacement-worker-bonus"


def test_bonus_condition_failure_keeps_base_amount_only():

    result = calculate_conditional_bonus_policy_support(
        conditional_bonus_policy(),
        rule_input(has_replacement_worker=False),
        requested_months=3
    )

    assert result["eligible"] is True
    assert result["status"] == "calculated"
    assert result["base_amount"] == 300000
    assert result["bonus_amount"] == 0
    assert result["estimated_total_amount"] == 300000
    assert result["applied_bonuses"] == []
    assert result["skipped_bonuses"][0]["reason"] == "bonus_conditions_not_met"


def test_bonus_requested_months_shorter_than_max_months():

    result = calculate_conditional_bonus_policy_support(
        conditional_bonus_policy(
            bonuses=[
                conditional_bonus(max_months=5)
            ]
        ),
        rule_input(),
        requested_months=2
    )

    bonus = result["applied_bonuses"][0]

    assert bonus["requested_months"] == 2
    assert bonus["eligible_months"] == 2
    assert bonus["result"] == 100000


def test_bonus_requested_months_equal_max_months():

    result = calculate_conditional_bonus_policy_support(
        conditional_bonus_policy(
            bonuses=[
                conditional_bonus(max_months=3)
            ]
        ),
        rule_input(),
        requested_months=3
    )

    bonus = result["applied_bonuses"][0]

    assert bonus["eligible_months"] == 3
    assert bonus["result"] == 150000


def test_bonus_requested_months_exceed_max_months():

    result = calculate_conditional_bonus_policy_support(
        conditional_bonus_policy(
            bonuses=[
                conditional_bonus(max_months=3)
            ]
        ),
        rule_input(),
        requested_months=6
    )

    bonus = result["applied_bonuses"][0]

    assert bonus["requested_months"] == 6
    assert bonus["eligible_months"] == 3
    assert bonus["result"] == 150000


def test_bonus_null_max_months_uses_requested_months_without_inferred_cap():

    result = calculate_conditional_bonus_policy_support(
        conditional_bonus_policy(
            bonuses=[
                conditional_bonus(max_months=None)
            ]
        ),
        rule_input(),
        requested_months=5
    )

    bonus = result["applied_bonuses"][0]

    assert bonus["eligible_months"] == 5
    assert bonus["result"] == 250000


def test_bonus_null_monthly_amount_returns_calculation_error():

    result = calculate_conditional_bonus_policy_support(
        conditional_bonus_policy(
            bonuses=[
                conditional_bonus(monthly_amount=None)
            ]
        ),
        rule_input(),
        requested_months=3
    )

    assert result["eligible"] is False
    assert result["status"] == "calculation_error"
    assert result["base_amount"] == 300000
    assert result["bonus_amount"] == 0
    assert result["estimated_total_amount"] == 300000
    assert result["calculation_steps"][1]["reason"] == "bonus_monthly_amount_missing"


def test_needs_review_policy_is_not_calculated():

    result = calculate_conditional_bonus_policy_support(
        conditional_bonus_policy(review_status="needs_review"),
        rule_input(),
        requested_months=3
    )

    assert result["review_status"] == "needs_review"
    assert result["eligible"] is False
    assert result["status"] == "needs_review"
    assert result["base_amount"] == 0
    assert result["bonus_amount"] == 0
    assert result["calculation_steps"][0]["reason"] == "policy_not_approved"


def test_base_condition_failure_skips_bonus_calculation():

    result = calculate_conditional_bonus_policy_support(
        conditional_bonus_policy(),
        rule_input(company_size="large"),
        requested_months=3
    )

    assert result["eligible"] is False
    assert result["status"] == "ineligible"
    assert result["base_amount"] == 0
    assert result["bonus_amount"] == 0
    assert result["estimated_total_amount"] == 0
    assert result["applied_bonuses"] == []
    assert result["skipped_bonuses"] == []
    assert result["calculation_steps"][1]["reason"] == "base_policy_not_calculated"


def test_bonus_failure_reason_is_in_skipped_bonuses():

    result = calculate_conditional_bonus_policy_support(
        conditional_bonus_policy(),
        rule_input(has_replacement_worker=False),
        requested_months=3
    )

    skipped = result["skipped_bonuses"][0]

    assert skipped["benefit_id"] == "replacement-worker-bonus"
    assert skipped["reason"] == "bonus_conditions_not_met"
    assert skipped["failed_conditions"][0]["condition_id"] == "bonus-replacement-worker"
    assert skipped["failed_conditions"][0]["reason"] == "condition_not_met"


def test_calculation_steps_separate_base_and_bonus():

    result = calculate_conditional_bonus_policy_support(
        conditional_bonus_policy(),
        rule_input(),
        requested_months=3
    )

    assert result["calculation_steps"][0]["step"] == "base_support_calculation"
    assert result["calculation_steps"][0]["result"] == 300000
    assert result["calculation_steps"][1]["step"] == "conditional_bonus"
    assert result["calculation_steps"][1]["benefit_id"] == "replacement-worker-bonus"
    assert result["calculation_steps"][1]["result"] == 150000


def test_evidence_snippets_are_linked():

    result = calculate_conditional_bonus_policy_support(
        conditional_bonus_policy(),
        rule_input(),
        requested_months=3
    )

    assert "Test fixture policy-level evidence." in result["evidence_snippets"]
    assert "Base support is 100000 per month." in result["evidence_snippets"]
    assert "Small companies satisfy the base support condition." in result["evidence_snippets"]
    assert "Bonus pays 50000 per month when replacement worker condition is met." in result["evidence_snippets"]
    assert "Replacement worker condition is required for bonus." in result["evidence_snippets"]
    assert result["applied_bonuses"][0]["evidence_snippets"]
    assert result["calculation_steps"][1]["evidence_snippets"]


if __name__ == "__main__":

    test_bonus_applies_and_is_added_to_base_amount()
    test_bonus_condition_failure_keeps_base_amount_only()
    test_bonus_requested_months_shorter_than_max_months()
    test_bonus_requested_months_equal_max_months()
    test_bonus_requested_months_exceed_max_months()
    test_bonus_null_max_months_uses_requested_months_without_inferred_cap()
    test_bonus_null_monthly_amount_returns_calculation_error()
    test_needs_review_policy_is_not_calculated()
    test_base_condition_failure_skips_bonus_calculation()
    test_bonus_failure_reason_is_in_skipped_bonuses()
    test_calculation_steps_separate_base_and_bonus()
    test_evidence_snippets_are_linked()
    print("test_conditional_bonus_calculation passed")
