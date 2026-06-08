from services.employer_net_cost_calculator import (
    calculate_employer_net_costs
)

from test_combination_amount_summarizer import (
    test_single_policy_combination_total_amount
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


def summarized_combination(
    policy_ids,
    total_subsidy_amount=1000
):

    return {
        "policy_ids":
            policy_ids,
        "policy_results":
            [
                {
                    "policy_id":
                        policy_id,
                    "policy_name":
                        f"{policy_id} Test Policy",
                    "status":
                        "calculated",
                    "base_amount":
                        total_subsidy_amount,
                    "bonus_amount":
                        0,
                    "estimated_total_amount":
                        total_subsidy_amount,
                    "calculation_steps":
                        [],
                    "evidence_snippets":
                        [
                            f"{policy_id} evidence."
                        ]
                }
                for policy_id in policy_ids
            ],
        "total_base_amount":
            total_subsidy_amount,
        "total_bonus_amount":
            0,
        "total_subsidy_amount":
            total_subsidy_amount,
        "calculation_steps":
            [
                {
                    "description":
                        "existing subsidy calculation",
                    "result":
                        total_subsidy_amount
                }
            ],
        "evidence_snippets":
            [
                "Existing evidence."
            ]
    }


def cost_item(
    cost_id="COST-001",
    amount=700,
    applies_to_policy_ids=None
):

    item = {
        "cost_id":
            cost_id,
        "cost_type":
            "replacement_worker_salary",
        "description":
            "Replacement worker salary",
        "amount":
            amount
    }

    if applies_to_policy_ids is not None:

        item[
            "applies_to_policy_ids"
        ] = applies_to_policy_ids

    return item


def first_combination(
    result
):

    return result[
        "cost_calculated_combinations"
    ][0]


def test_no_cost_items_calculates_zero_employer_cost():

    result = calculate_employer_net_costs(
        [
            summarized_combination(
                [
                    "POLICY-A"
                ],
                total_subsidy_amount=1000
            )
        ],
        []
    )

    combination = first_combination(
        result
    )

    assert combination["applied_cost_items"] == []
    assert combination["total_employer_cost"] == 0
    assert combination["net_employer_cost"] == -1000


def test_global_cost_item_applies_to_all_combinations():

    result = calculate_employer_net_costs(
        [
            summarized_combination(
                [
                    "POLICY-A"
                ],
                total_subsidy_amount=1000
            ),
            summarized_combination(
                [
                    "POLICY-B"
                ],
                total_subsidy_amount=2000
            )
        ],
        [
            cost_item(
                amount=700,
                applies_to_policy_ids=[]
            )
        ]
    )

    assert [
        combination["total_employer_cost"]
        for combination in result["cost_calculated_combinations"]
    ] == [
        700,
        700
    ]


def test_policy_specific_cost_item_applies_only_when_policy_present():

    result = calculate_employer_net_costs(
        [
            summarized_combination(
                [
                    "POLICY-A"
                ]
            ),
            summarized_combination(
                [
                    "POLICY-B"
                ]
            )
        ],
        [
            cost_item(
                amount=700,
                applies_to_policy_ids=[
                    "POLICY-B"
                ]
            )
        ]
    )

    assert result["cost_calculated_combinations"][0]["applied_cost_items"] == []
    assert result["cost_calculated_combinations"][1]["total_employer_cost"] == 700


def test_multi_policy_cost_item_uses_and_condition():

    result = calculate_employer_net_costs(
        [
            summarized_combination(
                [
                    "POLICY-A"
                ]
            ),
            summarized_combination(
                [
                    "POLICY-A",
                    "POLICY-B"
                ]
            )
        ],
        [
            cost_item(
                amount=700,
                applies_to_policy_ids=[
                    "POLICY-A",
                    "POLICY-B"
                ]
            )
        ]
    )

    assert result["cost_calculated_combinations"][0]["total_employer_cost"] == 0
    assert result["cost_calculated_combinations"][1]["total_employer_cost"] == 700


def test_cost_item_is_excluded_when_target_policy_absent():

    result = calculate_employer_net_costs(
        [
            summarized_combination(
                [
                    "POLICY-A"
                ]
            )
        ],
        [
            cost_item(
                amount=700,
                applies_to_policy_ids=[
                    "POLICY-B"
                ]
            )
        ]
    )

    assert first_combination(
        result
    )["applied_cost_items"] == []


def test_multiple_cost_items_are_summed():

    result = calculate_employer_net_costs(
        [
            summarized_combination(
                [
                    "POLICY-A"
                ],
                total_subsidy_amount=1000
            )
        ],
        [
            cost_item(
                cost_id="COST-001",
                amount=700
            ),
            cost_item(
                cost_id="COST-002",
                amount=500
            )
        ]
    )

    combination = first_combination(
        result
    )

    assert combination["total_employer_cost"] == 1200
    assert combination["net_employer_cost"] == 200


def test_null_amount_returns_error():

    result = calculate_employer_net_costs(
        [
            summarized_combination(
                [
                    "POLICY-A"
                ]
            )
        ],
        [
            cost_item(
                amount=None
            )
        ]
    )

    assert result["cost_calculated_combinations"] == []
    assert result["errors"][0]["reason"] == "amount_required"


def test_non_numeric_amount_returns_error():

    result = calculate_employer_net_costs(
        [
            summarized_combination(
                [
                    "POLICY-A"
                ]
            )
        ],
        [
            cost_item(
                amount="700"
            )
        ]
    )

    assert result["errors"][0]["reason"] == "amount_must_be_number"


def test_negative_amount_returns_error():

    result = calculate_employer_net_costs(
        [
            summarized_combination(
                [
                    "POLICY-A"
                ]
            )
        ],
        [
            cost_item(
                amount=-1
            )
        ]
    )

    assert result["errors"][0]["reason"] == "amount_must_not_be_negative"


def test_missing_cost_id_returns_error():

    item = cost_item()
    item[
        "cost_id"
    ] = ""

    result = calculate_employer_net_costs(
        [
            summarized_combination(
                [
                    "POLICY-A"
                ]
            )
        ],
        [
            item
        ]
    )

    assert result["errors"][0] == {
        "cost_id": "cost[0]",
        "field": "cost_id",
        "reason": "cost_id_required"
    }


def test_duplicate_cost_id_returns_error():

    result = calculate_employer_net_costs(
        [
            summarized_combination(
                [
                    "POLICY-A"
                ]
            )
        ],
        [
            cost_item(
                cost_id="COST-001"
            ),
            cost_item(
                cost_id="COST-001"
            )
        ]
    )

    assert result["errors"][0] == {
        "cost_id": "COST-001",
        "field": "cost_id",
        "reason": "duplicate_cost_id"
    }


def test_missing_applies_to_policy_ids_normalizes_to_empty_list():

    result = calculate_employer_net_costs(
        [
            summarized_combination(
                [
                    "POLICY-A"
                ]
            )
        ],
        [
            cost_item(
                amount=700,
                applies_to_policy_ids=None
            )
        ]
    )

    assert first_combination(
        result
    )["applied_cost_items"][0]["applies_to_policy_ids"] == []


def test_negative_net_employer_cost_is_allowed():

    result = calculate_employer_net_costs(
        [
            summarized_combination(
                [
                    "POLICY-A"
                ],
                total_subsidy_amount=1000
            )
        ],
        [
            cost_item(
                amount=100
            )
        ]
    )

    assert first_combination(
        result
    )["net_employer_cost"] == -900
    assert result["errors"] == []


def test_existing_combination_amount_summarizer_regression():

    test_single_policy_combination_total_amount()


def test_existing_policy_combination_generator_regression():

    test_three_non_conflicting_candidates_create_seven_combinations()


def test_existing_combination_schema_regression():

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

    test_no_cost_items_calculates_zero_employer_cost()
    test_global_cost_item_applies_to_all_combinations()
    test_policy_specific_cost_item_applies_only_when_policy_present()
    test_multi_policy_cost_item_uses_and_condition()
    test_cost_item_is_excluded_when_target_policy_absent()
    test_multiple_cost_items_are_summed()
    test_null_amount_returns_error()
    test_non_numeric_amount_returns_error()
    test_negative_amount_returns_error()
    test_missing_cost_id_returns_error()
    test_duplicate_cost_id_returns_error()
    test_missing_applies_to_policy_ids_normalizes_to_empty_list()
    test_negative_net_employer_cost_is_allowed()
    test_existing_combination_amount_summarizer_regression()
    test_existing_policy_combination_generator_regression()
    test_existing_combination_schema_regression()
    test_existing_mutually_exclusive_regression()
    test_existing_requires_regression()
    test_existing_monthly_fixed_regression()
    test_existing_period_tiered_regression()
    test_existing_conditional_bonus_regression()
    test_existing_standard_result_regression()
    print("test_employer_net_cost_calculator passed")
