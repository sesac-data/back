from services.calculation_service import (
    calculate_period_tiered_policy_support
)


def period_tiered_policy(
    tiers=None,
    review_status="approved",
    expected_company_size="small"
):

    if tiers is None:

        tiers = [
            {
                "start_month":
                    1,
                "end_month":
                    3,
                "monthly_amount":
                    1000000,
                "evidence_snippets":
                    [
                        "Months 1 through 3 pay 1000000 per month."
                    ]
            },
            {
                "start_month":
                    4,
                "end_month":
                    12,
                "monthly_amount":
                    300000,
                "evidence_snippets":
                    [
                        "Months 4 through 12 pay 300000 per month."
                    ]
            }
        ]

    return {
        "policy_id":
            "policy-period-tiered",
        "policy_key":
            "policy-period-tiered",
        "policy_name":
            "Period Tiered Test Policy",
        "review_status":
            review_status,
        "evidence_snippets":
            [
                "Policy-level tiered evidence."
            ],
        "support_items":
            [
                {
                    "support_type":
                        "period_tiered",
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
                                "period_tiered",
                            "tiers":
                                tiers,
                            "evidence_snippets":
                                [
                                    "Tiered support is defined by month."
                                ]
                        },
                    "evidence_snippets":
                        [
                            "Period tiered support item evidence."
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


def test_requested_months_end_inside_first_tier():

    result = calculate_period_tiered_policy_support(
        period_tiered_policy(),
        rule_input(),
        requested_months=2
    )

    assert result["eligible"] is True
    assert result["calculation_type"] == "period_tiered"
    assert result["requested_months"] == 2
    assert result["eligible_months"] == 2
    assert result["estimated_total_amount"] == 2000000
    assert len(result["calculation_steps"]) == 1
    assert result["calculation_steps"][0]["applied_months"] == 2
    assert result["calculation_steps"][0]["result"] == 2000000


def test_requested_months_span_two_tiers():

    result = calculate_period_tiered_policy_support(
        period_tiered_policy(),
        rule_input(),
        requested_months=5
    )

    assert result["eligible_months"] == 5
    assert result["estimated_total_amount"] == 3600000
    assert result["calculation_steps"][0]["applied_months"] == 3
    assert result["calculation_steps"][1]["applied_months"] == 2
    assert result["calculation_steps"][1]["result"] == 600000


def test_requested_months_exceed_all_tiers():

    result = calculate_period_tiered_policy_support(
        period_tiered_policy(),
        rule_input(),
        requested_months=15
    )

    assert result["eligible_months"] == 12
    assert result["estimated_total_amount"] == 5700000
    assert len(result["calculation_steps"]) == 2


def test_requested_months_match_tier_boundary():

    result = calculate_period_tiered_policy_support(
        period_tiered_policy(),
        rule_input(),
        requested_months=3
    )

    assert result["eligible_months"] == 3
    assert result["estimated_total_amount"] == 3000000
    assert len(result["calculation_steps"]) == 1
    assert result["calculation_steps"][0]["end_month"] == 3


def test_ineligible_policy_is_not_calculated():

    result = calculate_period_tiered_policy_support(
        period_tiered_policy(),
        rule_input(company_size="large"),
        requested_months=5
    )

    assert result["eligible"] is False
    assert result["status"] == "ineligible"
    assert result["estimated_total_amount"] == 0
    assert result["failed_conditions"][0]["condition_id"] == "company-size"
    assert result["calculation_steps"][1]["reason"] == "policy_ineligible"


def test_needs_review_policy_is_not_calculated():

    result = calculate_period_tiered_policy_support(
        period_tiered_policy(review_status="needs_review"),
        rule_input(),
        requested_months=5
    )

    assert result["eligible"] is False
    assert result["status"] == "needs_review"
    assert result["estimated_total_amount"] == 0
    assert result["calculation_steps"][0]["reason"] == "policy_not_approved"


def test_null_tier_monthly_amount_returns_error():

    result = calculate_period_tiered_policy_support(
        period_tiered_policy(
            tiers=[
                {
                    "start_month": 1,
                    "end_month": 3,
                    "monthly_amount": None,
                    "evidence_snippets": ["Missing amount evidence."]
                }
            ]
        ),
        rule_input(),
        requested_months=2
    )

    assert result["eligible"] is False
    assert result["status"] == "calculation_error"
    assert result["calculation_steps"][1]["reason"] == "tier_monthly_amount_missing"


def test_start_month_after_end_month_returns_error():

    result = calculate_period_tiered_policy_support(
        period_tiered_policy(
            tiers=[
                {
                    "start_month": 4,
                    "end_month": 3,
                    "monthly_amount": 1000000,
                    "evidence_snippets": ["Invalid range evidence."]
                }
            ]
        ),
        rule_input(),
        requested_months=2
    )

    assert result["status"] == "calculation_error"
    assert result["calculation_steps"][1]["reason"] == "tier_start_after_end"


def test_overlapping_tier_ranges_return_error():

    result = calculate_period_tiered_policy_support(
        period_tiered_policy(
            tiers=[
                {
                    "start_month": 1,
                    "end_month": 3,
                    "monthly_amount": 1000000,
                    "evidence_snippets": ["First tier evidence."]
                },
                {
                    "start_month": 3,
                    "end_month": 6,
                    "monthly_amount": 300000,
                    "evidence_snippets": ["Overlapping tier evidence."]
                }
            ]
        ),
        rule_input(),
        requested_months=5
    )

    assert result["status"] == "calculation_error"
    assert result["calculation_steps"][1]["reason"] == "tier_overlap"


def test_gap_between_tier_ranges_returns_error():

    result = calculate_period_tiered_policy_support(
        period_tiered_policy(
            tiers=[
                {
                    "start_month": 1,
                    "end_month": 3,
                    "monthly_amount": 1000000,
                    "evidence_snippets": ["First tier evidence."]
                },
                {
                    "start_month": 5,
                    "end_month": 12,
                    "monthly_amount": 300000,
                    "evidence_snippets": ["Gap tier evidence."]
                }
            ]
        ),
        rule_input(),
        requested_months=5
    )

    assert result["status"] == "calculation_error"
    assert result["calculation_steps"][1]["reason"] == "tier_gap"


def test_evidence_snippets_are_linked():

    result = calculate_period_tiered_policy_support(
        period_tiered_policy(),
        rule_input(),
        requested_months=5
    )

    assert "Policy-level tiered evidence." in result["evidence_snippets"]
    assert "Small companies are eligible." in result["evidence_snippets"]
    assert "Months 1 through 3 pay 1000000 per month." in result["evidence_snippets"]
    assert "Months 4 through 12 pay 300000 per month." in result["evidence_snippets"]
    assert result["calculation_steps"][0]["evidence_snippets"] == [
        "Months 1 through 3 pay 1000000 per month."
    ]


if __name__ == "__main__":

    test_requested_months_end_inside_first_tier()
    test_requested_months_span_two_tiers()
    test_requested_months_exceed_all_tiers()
    test_requested_months_match_tier_boundary()
    test_ineligible_policy_is_not_calculated()
    test_needs_review_policy_is_not_calculated()
    test_null_tier_monthly_amount_returns_error()
    test_start_month_after_end_month_returns_error()
    test_overlapping_tier_ranges_return_error()
    test_gap_between_tier_ranges_returns_error()
    test_evidence_snippets_are_linked()
    print("test_period_tiered_calculation passed")
