from services.combination_amount_summarizer import (
    summarize_combination_amounts
)

from services.policy_combination_generator import (
    generate_valid_policy_combinations
)

from test_combination_rule_validator import (
    test_valid_mutually_exclusive_rule
)

from test_conditional_bonus_calculation import (
    test_bonus_applies_and_is_added_to_base_amount
)

from test_monthly_fixed_calculation import (
    test_requested_months_shorter_than_max_months
)

from test_mutual_exclusion_detector import (
    test_one_way_mutually_exclusive_rule_creates_conflict
)

from test_period_tiered_calculation import (
    test_requested_months_span_two_tiers
)

from test_policy_combination_generator import (
    test_three_non_conflicting_candidates_create_seven_combinations
)

from test_requirement_detector import (
    test_missing_required_policy_creates_violation
)

from test_standardized_calculation_result import (
    test_monthly_fixed_result_has_standard_structure
)


def policy(
    policy_id
):

    return {
        "policy_id":
            policy_id,
        "policy_key":
            policy_id,
        "policy_name":
            f"{policy_id} Test Policy",
        "review_status":
            "approved",
        "combination_rules":
            []
    }


def standardized_result(
    policy_id,
    status="calculated",
    base_amount=100,
    bonus_amount=0,
    estimated_total_amount=100,
    calculation_steps=None,
    evidence_snippets=None
):

    if calculation_steps is None:

        calculation_steps = [
            {
                "step": f"{policy_id}-calculation",
                "result": estimated_total_amount
            }
        ]

    if evidence_snippets is None:

        evidence_snippets = [
            f"{policy_id} exact evidence."
        ]

    return {
        "policy_id":
            policy_id,
        "policy_name":
            f"{policy_id} Test Policy",
        "review_status":
            "approved",
        "eligible":
            status == "calculated",
        "status":
            status,
        "calculation_type":
            "monthly_fixed",
        "base_amount":
            base_amount,
        "bonus_amount":
            bonus_amount,
        "estimated_total_amount":
            estimated_total_amount,
        "calculation_steps":
            calculation_steps,
        "passed_conditions":
            [],
        "failed_conditions":
            [],
        "applied_bonuses":
            [],
        "skipped_bonuses":
            [],
        "evidence_snippets":
            evidence_snippets,
        "errors":
            []
    }


def valid_combinations_for(
    policy_ids
):

    result = generate_valid_policy_combinations(
        [
            policy(
                policy_id
            )
            for policy_id in policy_ids
        ]
    )

    return result[
        "valid_combinations"
    ]


def summarized_by_ids(
    result,
    policy_ids
):

    for combination in result["summarized_combinations"]:

        if combination["policy_ids"] == policy_ids:

            return combination

    return None


def rejected_by_ids(
    result,
    policy_ids
):

    for combination in result["rejected_combinations"]:

        if combination["policy_ids"] == policy_ids:

            return combination

    return None


def test_single_policy_combination_total_amount():

    result = summarize_combination_amounts(
        valid_combinations_for(
            [
                "POLICY-A"
            ]
        ),
        [
            standardized_result(
                "POLICY-A",
                base_amount=100,
                estimated_total_amount=100
            )
        ]
    )

    combination = summarized_by_ids(
        result,
        [
            "POLICY-A"
        ]
    )

    assert combination["total_base_amount"] == 100
    assert combination["total_bonus_amount"] == 0
    assert combination["total_subsidy_amount"] == 100


def test_two_policy_combination_total_amount():

    result = summarize_combination_amounts(
        valid_combinations_for(
            [
                "POLICY-A",
                "POLICY-B"
            ]
        ),
        [
            standardized_result(
                "POLICY-A",
                base_amount=100,
                estimated_total_amount=100
            ),
            standardized_result(
                "POLICY-B",
                base_amount=200,
                estimated_total_amount=200
            )
        ]
    )

    combination = summarized_by_ids(
        result,
        [
            "POLICY-A",
            "POLICY-B"
        ]
    )

    assert combination["total_base_amount"] == 300
    assert combination["total_bonus_amount"] == 0
    assert combination["total_subsidy_amount"] == 300


def test_three_policy_combination_total_amount():

    result = summarize_combination_amounts(
        valid_combinations_for(
            [
                "POLICY-A",
                "POLICY-B",
                "POLICY-C"
            ]
        ),
        [
            standardized_result(
                "POLICY-A",
                base_amount=100,
                estimated_total_amount=100
            ),
            standardized_result(
                "POLICY-B",
                base_amount=200,
                estimated_total_amount=200
            ),
            standardized_result(
                "POLICY-C",
                base_amount=300,
                estimated_total_amount=300
            )
        ]
    )

    combination = summarized_by_ids(
        result,
        [
            "POLICY-A",
            "POLICY-B",
            "POLICY-C"
        ]
    )

    assert combination["total_base_amount"] == 600
    assert combination["total_bonus_amount"] == 0
    assert combination["total_subsidy_amount"] == 600


def test_conditional_bonus_is_not_double_counted():

    result = summarize_combination_amounts(
        valid_combinations_for(
            [
                "POLICY-BONUS"
            ]
        ),
        [
            standardized_result(
                "POLICY-BONUS",
                base_amount=100,
                bonus_amount=50,
                estimated_total_amount=150
            )
        ]
    )

    combination = summarized_by_ids(
        result,
        [
            "POLICY-BONUS"
        ]
    )

    assert combination["total_base_amount"] == 100
    assert combination["total_bonus_amount"] == 50
    assert combination["total_subsidy_amount"] == 150


def test_base_and_bonus_totals_are_separated():

    result = summarize_combination_amounts(
        valid_combinations_for(
            [
                "POLICY-A",
                "POLICY-B"
            ]
        ),
        [
            standardized_result(
                "POLICY-A",
                base_amount=100,
                bonus_amount=25,
                estimated_total_amount=125
            ),
            standardized_result(
                "POLICY-B",
                base_amount=200,
                bonus_amount=50,
                estimated_total_amount=250
            )
        ]
    )

    combination = summarized_by_ids(
        result,
        [
            "POLICY-A",
            "POLICY-B"
        ]
    )

    assert combination["total_base_amount"] == 300
    assert combination["total_bonus_amount"] == 75
    assert combination["total_subsidy_amount"] == 375


def test_calculation_error_policy_rejects_combination():

    result = summarize_combination_amounts(
        valid_combinations_for(
            [
                "POLICY-A"
            ]
        ),
        [
            standardized_result(
                "POLICY-A",
                status="calculation_error",
                base_amount=None,
                estimated_total_amount=None
            )
        ]
    )

    rejected = rejected_by_ids(
        result,
        [
            "POLICY-A"
        ]
    )

    assert rejected["reasons"][0]["type"] == "calculation_error"


def test_ineligible_policy_rejects_combination():

    result = summarize_combination_amounts(
        valid_combinations_for(
            [
                "POLICY-A"
            ]
        ),
        [
            standardized_result(
                "POLICY-A",
                status="ineligible",
                base_amount=None,
                estimated_total_amount=None
            )
        ]
    )

    rejected = rejected_by_ids(
        result,
        [
            "POLICY-A"
        ]
    )

    assert rejected["reasons"][0]["type"] == "ineligible"


def test_null_estimated_total_rejects_combination():

    result = summarize_combination_amounts(
        valid_combinations_for(
            [
                "POLICY-A"
            ]
        ),
        [
            standardized_result(
                "POLICY-A",
                estimated_total_amount=None
            )
        ]
    )

    rejected = rejected_by_ids(
        result,
        [
            "POLICY-A"
        ]
    )

    assert rejected["reasons"][0]["type"] == "estimated_total_amount_missing"


def test_missing_policy_result_rejects_combination():

    result = summarize_combination_amounts(
        valid_combinations_for(
            [
                "POLICY-A"
            ]
        ),
        []
    )

    rejected = rejected_by_ids(
        result,
        [
            "POLICY-A"
        ]
    )

    assert rejected["reasons"][0]["type"] == "policy_result_missing"


def test_duplicate_policy_result_returns_error():

    result = summarize_combination_amounts(
        valid_combinations_for(
            [
                "POLICY-A"
            ]
        ),
        [
            standardized_result(
                "POLICY-A"
            ),
            standardized_result(
                "POLICY-A"
            )
        ]
    )

    assert result["summarized_combinations"] == []
    assert result["rejected_combinations"] == []
    assert result["errors"] == [
        {
            "field": "policy_id",
            "reason": "duplicate_policy_result",
            "details": {
                "policy_ids": [
                    "POLICY-A"
                ]
            }
        }
    ]


def test_calculation_steps_are_preserved():

    steps = [
        {
            "step": "source-calculation-step",
            "result": 100
        }
    ]

    result = summarize_combination_amounts(
        valid_combinations_for(
            [
                "POLICY-A"
            ]
        ),
        [
            standardized_result(
                "POLICY-A",
                calculation_steps=steps
            )
        ]
    )

    combination = summarized_by_ids(
        result,
        [
            "POLICY-A"
        ]
    )

    assert combination["policy_results"][0]["calculation_steps"] == steps
    assert combination["calculation_steps"][0]["calculation_steps"] == steps


def test_evidence_snippets_are_preserved():

    evidence = [
        "Exact source evidence sentence."
    ]

    result = summarize_combination_amounts(
        valid_combinations_for(
            [
                "POLICY-A"
            ]
        ),
        [
            standardized_result(
                "POLICY-A",
                evidence_snippets=evidence
            )
        ]
    )

    combination = summarized_by_ids(
        result,
        [
            "POLICY-A"
        ]
    )

    assert combination["policy_results"][0]["evidence_snippets"] == evidence
    assert combination["evidence_snippets"] == evidence


def test_combination_and_policy_result_order_is_deterministic():

    result = summarize_combination_amounts(
        valid_combinations_for(
            [
                "POLICY-C",
                "POLICY-A",
                "POLICY-B"
            ]
        ),
        [
            standardized_result(
                "POLICY-C",
                base_amount=300,
                estimated_total_amount=300
            ),
            standardized_result(
                "POLICY-A",
                base_amount=100,
                estimated_total_amount=100
            ),
            standardized_result(
                "POLICY-B",
                base_amount=200,
                estimated_total_amount=200
            )
        ]
    )

    policy_ids = [
        combination["policy_ids"]
        for combination in result["summarized_combinations"]
    ]

    assert policy_ids[0:3] == [
        [
            "POLICY-A"
        ],
        [
            "POLICY-B"
        ],
        [
            "POLICY-C"
        ]
    ]

    three_policy_combination = summarized_by_ids(
        result,
        [
            "POLICY-A",
            "POLICY-B",
            "POLICY-C"
        ]
    )

    assert [
        policy_result["policy_id"]
        for policy_result in three_policy_combination["policy_results"]
    ] == [
        "POLICY-A",
        "POLICY-B",
        "POLICY-C"
    ]


def test_existing_policy_combination_generator_regression():

    test_three_non_conflicting_candidates_create_seven_combinations()


def test_existing_combination_rule_schema_regression():

    test_valid_mutually_exclusive_rule()


def test_existing_mutually_exclusive_regression():

    test_one_way_mutually_exclusive_rule_creates_conflict()


def test_existing_requires_regression():

    test_missing_required_policy_creates_violation()


def test_existing_monthly_fixed_regression():

    test_requested_months_shorter_than_max_months()


def test_existing_period_tiered_regression():

    test_requested_months_span_two_tiers()


def test_existing_conditional_bonus_regression():

    test_bonus_applies_and_is_added_to_base_amount()


def test_existing_standard_result_regression():

    test_monthly_fixed_result_has_standard_structure()


if __name__ == "__main__":

    test_single_policy_combination_total_amount()
    test_two_policy_combination_total_amount()
    test_three_policy_combination_total_amount()
    test_conditional_bonus_is_not_double_counted()
    test_base_and_bonus_totals_are_separated()
    test_calculation_error_policy_rejects_combination()
    test_ineligible_policy_rejects_combination()
    test_null_estimated_total_rejects_combination()
    test_missing_policy_result_rejects_combination()
    test_duplicate_policy_result_returns_error()
    test_calculation_steps_are_preserved()
    test_evidence_snippets_are_preserved()
    test_combination_and_policy_result_order_is_deterministic()
    test_existing_policy_combination_generator_regression()
    test_existing_combination_rule_schema_regression()
    test_existing_mutually_exclusive_regression()
    test_existing_requires_regression()
    test_existing_monthly_fixed_regression()
    test_existing_period_tiered_regression()
    test_existing_conditional_bonus_regression()
    test_existing_standard_result_regression()
    print("test_combination_amount_summarizer passed")
