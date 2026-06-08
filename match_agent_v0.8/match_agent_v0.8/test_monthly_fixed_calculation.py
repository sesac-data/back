from services.calculation_service import (
    calculate_monthly_fixed_policy_support,
    calculate_yearly_amount
)


def approved_policy(
    monthly_amount=100000,
    max_months=6,
    review_status="approved",
    expected_company_size="small"
):

    return {
        "policy_id":
            "policy-monthly-fixed",
        "policy_key":
            "policy-monthly-fixed",
        "policy_name":
            "Monthly Fixed Test Policy",
        "review_status":
            review_status,
        "evidence_snippets":
            [
                "Policy-level source sentence."
            ],
        "support_items":
            [
                {
                    "support_type":
                        "monthly_fixed",
                    "conditions":
                        [
                            {
                                "condition_id":
                                    "company-size",
                                "field":
                                    "company.size",
                                "operator":
                                    "eq",
                                "expected":
                                    expected_company_size,
                                "evidence_snippets":
                                    [
                                        "Small companies are eligible."
                                    ]
                            }
                        ],
                    "support":
                        {
                            "calculation_type":
                                "monthly_fixed",
                            "monthly_amount":
                                monthly_amount,
                            "max_months":
                                max_months,
                            "evidence_snippets":
                                [
                                    "Support is 100000 per month."
                                ]
                        },
                    "evidence_snippets":
                        [
                            "Monthly fixed support item evidence."
                        ]
                }
            ]
    }


def rule_input(
    company_size="small"
):

    return {
        "company": {
            "size": company_size
        }
    }


def test_requested_months_shorter_than_max_months():

    result = calculate_monthly_fixed_policy_support(
        approved_policy(),
        rule_input(),
        requested_months=3
    )

    assert result["eligible"] is True
    assert result["calculation_type"] == "monthly_fixed"
    assert result["requested_months"] == 3
    assert result["eligible_months"] == 3
    assert result["monthly_amount"] == 100000
    assert result["estimated_total_amount"] == 300000


def test_requested_months_equal_max_months():

    result = calculate_monthly_fixed_policy_support(
        approved_policy(),
        rule_input(),
        requested_months=6
    )

    assert result["eligible_months"] == 6
    assert result["estimated_total_amount"] == 600000
    assert calculate_yearly_amount(
        {
            "monthly_amount": 100000,
            "max_duration_months": 6
        }
    ) == result["estimated_total_amount"]


def test_requested_months_exceed_max_months():

    result = calculate_monthly_fixed_policy_support(
        approved_policy(),
        rule_input(),
        requested_months=9
    )

    assert result["requested_months"] == 9
    assert result["eligible_months"] == 6
    assert result["estimated_total_amount"] == 600000


def test_ineligible_policy_is_not_calculated():

    result = calculate_monthly_fixed_policy_support(
        approved_policy(),
        rule_input(company_size="large"),
        requested_months=3
    )

    assert result["eligible"] is False
    assert result["status"] == "ineligible"
    assert result["eligible_months"] == 0
    assert result["estimated_total_amount"] == 0
    assert result["failed_conditions"][0]["condition_id"] == "company-size"
    assert result["calculation_steps"][1]["reason"] == "policy_ineligible"


def test_needs_review_policy_is_not_calculated():

    result = calculate_monthly_fixed_policy_support(
        approved_policy(review_status="needs_review"),
        rule_input(),
        requested_months=3
    )

    assert result["eligible"] is False
    assert result["status"] == "needs_review"
    assert result["estimated_total_amount"] == 0
    assert result["calculation_steps"][0]["reason"] == "policy_not_approved"


def test_missing_monthly_amount_returns_error():

    result = calculate_monthly_fixed_policy_support(
        approved_policy(monthly_amount=None),
        rule_input(),
        requested_months=3
    )

    assert result["eligible"] is False
    assert result["status"] == "calculation_error"
    assert result["estimated_total_amount"] == 0
    assert result["calculation_steps"][1]["reason"] == "monthly_amount_missing"


def test_null_max_months_uses_requested_months_without_inferred_cap():

    result = calculate_monthly_fixed_policy_support(
        approved_policy(max_months=None),
        rule_input(),
        requested_months=8
    )

    assert result["eligible"] is True
    assert result["eligible_months"] == 8
    assert result["estimated_total_amount"] == 800000
    assert result["calculation_steps"][1]["reason"] == "no_policy_max_months_defined"


def test_evidence_snippets_are_linked_to_calculation_result():

    result = calculate_monthly_fixed_policy_support(
        approved_policy(),
        rule_input(),
        requested_months=3
    )

    assert "Policy-level source sentence." in result["evidence_snippets"]
    assert "Small companies are eligible." in result["evidence_snippets"]
    assert "Support is 100000 per month." in result["evidence_snippets"]


def test_calculation_steps_include_inputs_and_results():

    result = calculate_monthly_fixed_policy_support(
        approved_policy(),
        rule_input(),
        requested_months=4
    )

    duration_step = result["calculation_steps"][1]
    amount_step = result["calculation_steps"][2]

    assert duration_step["step"] == "eligible_months"
    assert duration_step["input"] == {
        "requested_months": 4,
        "max_months": 6
    }
    assert duration_step["result"] == 4

    assert amount_step["step"] == "monthly_fixed_calculation"
    assert amount_step["input"] == {
        "monthly_amount": 100000,
        "eligible_months": 4
    }
    assert amount_step["result"] == 400000


if __name__ == "__main__":

    test_requested_months_shorter_than_max_months()
    test_requested_months_equal_max_months()
    test_requested_months_exceed_max_months()
    test_ineligible_policy_is_not_calculated()
    test_needs_review_policy_is_not_calculated()
    test_missing_monthly_amount_returns_error()
    test_null_max_months_uses_requested_months_without_inferred_cap()
    test_evidence_snippets_are_linked_to_calculation_result()
    test_calculation_steps_include_inputs_and_results()
    print("test_monthly_fixed_calculation passed")
