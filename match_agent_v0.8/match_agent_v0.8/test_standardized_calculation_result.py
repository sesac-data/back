from services.calculation_service import (
    calculate_conditional_bonus_policy_support,
    calculate_monthly_fixed_policy_support,
    calculate_period_tiered_policy_support,
    normalize_policy_calculation_result,
    validate_standard_calculation_result
)

from test_conditional_bonus_calculation import (
    conditional_bonus,
    conditional_bonus_policy,
    rule_input as bonus_rule_input
)

from test_monthly_fixed_calculation import (
    approved_policy as monthly_fixed_policy,
    rule_input as monthly_rule_input
)

from test_period_tiered_calculation import (
    period_tiered_policy,
    rule_input as period_rule_input
)


STANDARD_FIELDS = [
    "policy_id",
    "policy_name",
    "review_status",
    "eligible",
    "status",
    "calculation_type",
    "base_amount",
    "bonus_amount",
    "estimated_total_amount",
    "calculation_steps",
    "passed_conditions",
    "failed_conditions",
    "applied_bonuses",
    "skipped_bonuses",
    "evidence_snippets",
    "errors"
]


def assert_standard_shape(
    result
):

    assert validate_standard_calculation_result(
        result
    ) == []

    assert list(
        result.keys()
    ) == STANDARD_FIELDS


def normalize_monthly_fixed(
    policy,
    company_size="small",
    requested_months=3
):

    return normalize_policy_calculation_result(
        policy,
        calculate_monthly_fixed_policy_support(
            policy,
            monthly_rule_input(
                company_size=company_size
            ),
            requested_months=requested_months
        )
    )


def normalize_period_tiered(
    policy,
    company_size="small",
    requested_months=5
):

    return normalize_policy_calculation_result(
        policy,
        calculate_period_tiered_policy_support(
            policy,
            period_rule_input(
                company_size=company_size
            ),
            requested_months=requested_months
        )
    )


def normalize_conditional_bonus(
    policy,
    company_size="small",
    has_replacement_worker=True,
    requested_months=3
):

    return normalize_policy_calculation_result(
        policy,
        calculate_conditional_bonus_policy_support(
            policy,
            bonus_rule_input(
                company_size=company_size,
                has_replacement_worker=has_replacement_worker
            ),
            requested_months=requested_months
        )
    )


def test_monthly_fixed_result_has_standard_structure():

    result = normalize_monthly_fixed(
        monthly_fixed_policy()
    )

    assert_standard_shape(
        result
    )
    assert result["calculation_type"] == "monthly_fixed"
    assert result["base_amount"] == 300000
    assert result["bonus_amount"] == 0


def test_period_tiered_result_has_standard_structure():

    result = normalize_period_tiered(
        period_tiered_policy()
    )

    assert_standard_shape(
        result
    )
    assert result["calculation_type"] == "period_tiered"
    assert result["base_amount"] == 3600000
    assert result["bonus_amount"] == 0


def test_conditional_bonus_applied_result_has_standard_structure():

    result = normalize_conditional_bonus(
        conditional_bonus_policy()
    )

    assert_standard_shape(
        result
    )
    assert result["calculation_type"] == "conditional_bonus"
    assert result["base_amount"] == 300000
    assert result["bonus_amount"] == 150000
    assert result["applied_bonuses"]
    assert result["skipped_bonuses"] == []


def test_conditional_bonus_skipped_result_has_standard_structure():

    result = normalize_conditional_bonus(
        conditional_bonus_policy(),
        has_replacement_worker=False
    )

    assert_standard_shape(
        result
    )
    assert result["calculation_type"] == "conditional_bonus"
    assert result["base_amount"] == 300000
    assert result["bonus_amount"] == 0
    assert result["applied_bonuses"] == []
    assert result["skipped_bonuses"][0]["reason"] == "bonus_conditions_not_met"


def test_ineligible_result_has_standard_structure():

    result = normalize_monthly_fixed(
        monthly_fixed_policy(),
        company_size="large"
    )

    assert_standard_shape(
        result
    )
    assert result["eligible"] is False
    assert result["status"] == "ineligible"
    assert result["base_amount"] is None
    assert result["estimated_total_amount"] is None
    assert result["failed_conditions"]


def test_needs_review_result_has_standard_structure():

    result = normalize_monthly_fixed(
        monthly_fixed_policy(
            review_status="needs_review"
        )
    )

    assert_standard_shape(
        result
    )
    assert result["review_status"] == "needs_review"
    assert result["status"] == "needs_review"
    assert result["base_amount"] is None
    assert result["estimated_total_amount"] is None


def test_calculation_error_result_has_standard_structure():

    result = normalize_monthly_fixed(
        monthly_fixed_policy(
            monthly_amount=None
        )
    )

    assert_standard_shape(
        result
    )
    assert result["status"] == "calculation_error"
    assert result["base_amount"] is None
    assert result["estimated_total_amount"] is None
    assert result["errors"][0]["reason"] == "monthly_amount_missing"


def test_defaults_apply_when_policy_has_no_bonus():

    result = normalize_period_tiered(
        period_tiered_policy()
    )

    assert result["bonus_amount"] == 0
    assert result["applied_bonuses"] == []
    assert result["skipped_bonuses"] == []


def test_errors_default_to_empty_list_when_absent():

    result = normalize_monthly_fixed(
        monthly_fixed_policy()
    )

    assert result["errors"] == []


def test_evidence_snippets_are_preserved():

    result = normalize_conditional_bonus(
        conditional_bonus_policy()
    )

    assert "Test fixture policy-level evidence." in result["evidence_snippets"]
    assert "Base support is 100000 per month." in result["evidence_snippets"]
    assert (
        "Bonus pays 50000 per month when replacement worker condition is met."
        in result["evidence_snippets"]
    )


def test_conditional_bonus_error_keeps_known_base_amount():

    result = normalize_conditional_bonus(
        conditional_bonus_policy(
            bonuses=[
                conditional_bonus(
                    monthly_amount=None
                )
            ]
        )
    )

    assert result["status"] == "calculation_error"
    assert result["base_amount"] == 300000
    assert result["bonus_amount"] == 0
    assert result["estimated_total_amount"] == 300000
    assert result["errors"][0]["reason"] == "bonus_monthly_amount_missing"


if __name__ == "__main__":

    test_monthly_fixed_result_has_standard_structure()
    test_period_tiered_result_has_standard_structure()
    test_conditional_bonus_applied_result_has_standard_structure()
    test_conditional_bonus_skipped_result_has_standard_structure()
    test_ineligible_result_has_standard_structure()
    test_needs_review_result_has_standard_structure()
    test_calculation_error_result_has_standard_structure()
    test_defaults_apply_when_policy_has_no_bonus()
    test_errors_default_to_empty_list_when_absent()
    test_evidence_snippets_are_preserved()
    test_conditional_bonus_error_keeps_known_base_amount()
    print("test_standardized_calculation_result passed")
