from services.policy_structure_evaluator import (
    evaluate_policy_structure,
    render_markdown_report,
)


def base_expected_policy():

    return {
        "policy_id":
            "POLICY-EVAL",
        "policy_name":
            "Policy Eval Fixture",
        "review_status":
            "needs_review",
        "evidence_snippets":
            [
                "source says policy applies",
            ],
        "support_items":
            [
                {
                    "support_item_id":
                        "SI-1",
                    "support_type":
                        "monthly_fixed",
                    "conditions":
                        [
                            {
                                "condition_id":
                                    "C-1",
                                "field":
                                    "company.size",
                                "operator":
                                    "eq",
                                "expected":
                                    "small",
                                "evidence_snippets":
                                    [
                                        "source says small company",
                                    ],
                            },
                            {
                                "condition_id":
                                    "C-2",
                                "field":
                                    "employee.leave_type",
                                "operator":
                                    "eq",
                                "expected":
                                    "parental_leave",
                                "evidence_snippets":
                                    [
                                        "source says parental leave",
                                    ],
                            },
                        ],
                    "support":
                        {
                            "calculation_type":
                                "period_tiered",
                            "monthly_amount":
                                100,
                            "max_months":
                                12,
                            "evidence_snippets":
                                [
                                    "source says monthly 100 for 12 months",
                                ],
                        },
                    "tiers":
                        [
                            {
                                "start_month":
                                    1,
                                "end_month":
                                    6,
                                "monthly_amount":
                                    100,
                                "evidence_snippets":
                                    [
                                        "source says months 1 to 6",
                                    ],
                            },
                            {
                                "start_month":
                                    7,
                                "end_month":
                                    12,
                                "monthly_amount":
                                    80,
                                "evidence_snippets":
                                    [
                                        "source says months 7 to 12",
                                    ],
                            },
                        ],
                    "bonuses":
                        [
                            {
                                "bonus_id":
                                    "B-1",
                                "bonus_amount":
                                    50,
                                "evidence_snippets":
                                    [
                                        "source says replacement bonus",
                                    ],
                            }
                        ],
                    "evidence_snippets":
                        [
                            "source says support item",
                        ],
                }
            ],
        "combination_rules":
            [
                {
                    "rule_id":
                        "R-1",
                    "rule_type":
                        "mutually_exclusive",
                    "target_policy_ids":
                        [
                            "POLICY-X",
                        ],
                    "reason":
                        "same subsidy",
                    "evidence_snippets":
                        [
                            "source says cannot combine",
                        ],
                }
            ],
    }


def candidate_policy():

    return base_expected_policy()


def error_types(
    result
):

    return {
        error[
            "error_type"
        ]
        for error in result[
            "errors"
        ]
    }


def evaluate(
    candidate
):

    return evaluate_policy_structure(
        "TEST SOURCE TEXT",
        base_expected_policy(),
        candidate,
    )


def test_exact_candidate_scores_100():

    result = evaluate(
        candidate_policy()
    )

    assert result["passed"] is True
    assert result["score"] == 100
    assert result["errors"] == []


def test_missing_condition_is_reported():

    candidate = candidate_policy()
    candidate["support_items"][0]["conditions"] = [
        candidate["support_items"][0]["conditions"][0]
    ]

    result = evaluate(
        candidate
    )

    assert "missing_condition" in error_types(
        result
    )


def test_operator_error_is_reported():

    candidate = candidate_policy()
    candidate["support_items"][0]["conditions"][0]["operator"] = "gte"

    result = evaluate(
        candidate
    )

    assert "operator_mismatch" in error_types(
        result
    )


def test_amount_error_is_reported():

    candidate = candidate_policy()
    candidate["support_items"][0]["support"]["monthly_amount"] = 99

    result = evaluate(
        candidate
    )

    assert "amount_mismatch" in error_types(
        result
    )


def test_duration_error_is_reported():

    candidate = candidate_policy()
    candidate["support_items"][0]["support"]["max_months"] = 10

    result = evaluate(
        candidate
    )

    assert "duration_mismatch" in error_types(
        result
    )


def test_tier_error_is_reported():

    candidate = candidate_policy()
    candidate["support_items"][0]["tiers"][1]["start_month"] = 8

    result = evaluate(
        candidate
    )

    assert "tier_mismatch" in error_types(
        result
    )


def test_evidence_missing_is_reported():

    candidate = candidate_policy()
    candidate["support_items"][0]["evidence_snippets"] = []

    result = evaluate(
        candidate
    )

    assert "missing_evidence" in error_types(
        result
    )


def test_combination_rule_missing_is_reported():

    candidate = candidate_policy()
    candidate["combination_rules"] = []

    result = evaluate(
        candidate
    )

    assert "missing_combination_rule" in error_types(
        result
    )


def test_approved_candidate_is_blocked():

    candidate = candidate_policy()
    candidate["review_status"] = "approved"

    result = evaluate(
        candidate
    )

    assert result["passed"] is False
    assert "invalid_review_status" in error_types(
        result
    )


def test_array_order_changes_are_allowed():

    candidate = candidate_policy()
    candidate["support_items"][0]["conditions"] = list(
        reversed(
            candidate["support_items"][0]["conditions"]
        )
    )
    candidate["support_items"][0]["tiers"] = list(
        reversed(
            candidate["support_items"][0]["tiers"]
        )
    )

    result = evaluate(
        candidate
    )

    assert result["passed"] is True
    assert result["score"] == 100


def test_markdown_report_is_generated():

    result = evaluate(
        candidate_policy()
    )
    result["case_id"] = "unit"
    markdown = render_markdown_report(
        {
            "passed":
                True,
            "case_count":
                1,
            "average_score":
                100,
            "results":
                [
                    result
                ],
        }
    )

    assert "# Policy Extraction Evaluation Report" in markdown
    assert "| unit | True | 100" in markdown


if __name__ == "__main__":

    test_exact_candidate_scores_100()
    test_missing_condition_is_reported()
    test_operator_error_is_reported()
    test_amount_error_is_reported()
    test_duration_error_is_reported()
    test_tier_error_is_reported()
    test_evidence_missing_is_reported()
    test_combination_rule_missing_is_reported()
    test_approved_candidate_is_blocked()
    test_array_order_changes_are_allowed()
    test_markdown_report_is_generated()
    print("test_policy_structure_evaluator passed")
