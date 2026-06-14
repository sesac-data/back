from services.optimal_combination_selector import (
    select_optimal_combination
)

from test_combination_amount_summarizer import (
    test_single_policy_combination_total_amount
)

from test_employer_net_cost_calculator import (
    test_multiple_cost_items_are_summed
)

from test_policy_combination_generator import (
    test_three_non_conflicting_candidates_create_seven_combinations
)


def cost_calculated_combination(
    policy_ids,
    total_subsidy_amount=1000,
    total_employer_cost=1500,
    net_employer_cost=500
):

    return {
        "policy_ids":
            policy_ids,
        "policy_results":
            [
                {
                    "policy_id":
                        policy_id,
                    "status":
                        "calculated",
                    "estimated_total_amount":
                        total_subsidy_amount
                }
                for policy_id in policy_ids
            ],
        "total_base_amount":
            total_subsidy_amount,
        "total_bonus_amount":
            0,
        "total_subsidy_amount":
            total_subsidy_amount,
        "applied_cost_items":
            [
                {
                    "cost_id":
                        "COST-001",
                    "cost_type":
                        "test_cost",
                    "description":
                        "Explicit test cost",
                    "amount":
                        total_employer_cost,
                    "applies_to_policy_ids":
                        []
                }
            ],
        "total_employer_cost":
            total_employer_cost,
        "net_employer_cost":
            net_employer_cost,
        "calculation_steps":
            [
                {
                    "description":
                        "existing net cost calculation"
                }
            ],
        "evidence_snippets":
            [
                "Existing evidence."
            ]
    }


def recommended_policy_ids(
    result
):

    return result[
        "recommended_combination"
    ][
        "policy_ids"
    ]


def test_single_candidate_is_selected():

    result = select_optimal_combination(
        [
            cost_calculated_combination(
                [
                    "POLICY-A"
                ]
            )
        ]
    )

    assert recommended_policy_ids(
        result
    ) == [
        "POLICY-A"
    ]
    assert result["recommended_combination"]["rank"] == 1
    assert result["alternative_combinations"] == []


def test_lowest_net_employer_cost_is_selected():

    result = select_optimal_combination(
        [
            cost_calculated_combination(
                [
                    "POLICY-A"
                ],
                net_employer_cost=700
            ),
            cost_calculated_combination(
                [
                    "POLICY-B"
                ],
                net_employer_cost=300
            )
        ]
    )

    assert recommended_policy_ids(
        result
    ) == [
        "POLICY-B"
    ]


def test_highest_subsidy_is_not_selected_when_net_cost_is_higher():

    result = select_optimal_combination(
        [
            cost_calculated_combination(
                [
                    "POLICY-A"
                ],
                total_subsidy_amount=500,
                net_employer_cost=100
            ),
            cost_calculated_combination(
                [
                    "POLICY-A",
                    "POLICY-B"
                ],
                total_subsidy_amount=2000,
                net_employer_cost=900
            )
        ]
    )

    assert recommended_policy_ids(
        result
    ) == [
        "POLICY-A"
    ]


def test_equal_net_cost_uses_higher_total_subsidy_tie_break():

    result = select_optimal_combination(
        [
            cost_calculated_combination(
                [
                    "POLICY-A"
                ],
                total_subsidy_amount=500,
                net_employer_cost=100
            ),
            cost_calculated_combination(
                [
                    "POLICY-B"
                ],
                total_subsidy_amount=700,
                net_employer_cost=100
            )
        ]
    )

    assert recommended_policy_ids(
        result
    ) == [
        "POLICY-B"
    ]
    assert result["recommended_combination"]["tie_break_applied"] == [
        "total_subsidy_amount_desc"
    ]


def test_equal_net_and_subsidy_uses_fewer_policies_tie_break():

    result = select_optimal_combination(
        [
            cost_calculated_combination(
                [
                    "POLICY-A",
                    "POLICY-B"
                ],
                total_subsidy_amount=700,
                net_employer_cost=100
            ),
            cost_calculated_combination(
                [
                    "POLICY-C"
                ],
                total_subsidy_amount=700,
                net_employer_cost=100
            )
        ]
    )

    assert recommended_policy_ids(
        result
    ) == [
        "POLICY-C"
    ]
    assert result["recommended_combination"]["tie_break_applied"] == [
        "total_subsidy_amount_desc",
        "policy_count_asc"
    ]


def test_all_major_values_equal_uses_policy_id_sort_tie_break():

    result = select_optimal_combination(
        [
            cost_calculated_combination(
                [
                    "POLICY-B"
                ],
                total_subsidy_amount=700,
                net_employer_cost=100
            ),
            cost_calculated_combination(
                [
                    "POLICY-A"
                ],
                total_subsidy_amount=700,
                net_employer_cost=100
            )
        ]
    )

    assert recommended_policy_ids(
        result
    ) == [
        "POLICY-A"
    ]
    assert result["recommended_combination"]["tie_break_applied"] == [
        "total_subsidy_amount_desc",
        "policy_count_asc",
        "policy_ids_lexicographic"
    ]


def test_negative_net_cost_is_valid_candidate():

    result = select_optimal_combination(
        [
            cost_calculated_combination(
                [
                    "POLICY-A"
                ],
                net_employer_cost=-500
            ),
            cost_calculated_combination(
                [
                    "POLICY-B"
                ],
                net_employer_cost=0
            )
        ]
    )

    assert recommended_policy_ids(
        result
    ) == [
        "POLICY-A"
    ]
    assert result["errors"] == []


def test_no_candidates_returns_error():

    result = select_optimal_combination(
        []
    )

    assert result["recommended_combination"] is None
    assert result["errors"][0]["reason"] == "no_recommendation_candidates"


def test_null_net_employer_cost_candidate_is_excluded():

    result = select_optimal_combination(
        [
            cost_calculated_combination(
                [
                    "POLICY-A"
                ],
                net_employer_cost=None
            ),
            cost_calculated_combination(
                [
                    "POLICY-B"
                ],
                net_employer_cost=10
            )
        ]
    )

    assert recommended_policy_ids(
        result
    ) == [
        "POLICY-B"
    ]
    assert result["errors"][0]["reason"] == "net_employer_cost_required"


def test_null_total_subsidy_amount_candidate_is_excluded():

    result = select_optimal_combination(
        [
            cost_calculated_combination(
                [
                    "POLICY-A"
                ],
                total_subsidy_amount=None
            ),
            cost_calculated_combination(
                [
                    "POLICY-B"
                ],
                total_subsidy_amount=100
            )
        ]
    )

    assert recommended_policy_ids(
        result
    ) == [
        "POLICY-B"
    ]
    assert result["errors"][0]["reason"] == "total_subsidy_amount_required"


def test_missing_or_empty_policy_ids_are_excluded():

    result = select_optimal_combination(
        [
            cost_calculated_combination(
                [],
            ),
            cost_calculated_combination(
                [
                    "POLICY-B"
                ]
            )
        ]
    )

    assert recommended_policy_ids(
        result
    ) == [
        "POLICY-B"
    ]
    assert result["errors"][0]["reason"] == "policy_ids_required"


def test_duplicate_policy_ids_combination_returns_error_without_merge():

    result = select_optimal_combination(
        [
            cost_calculated_combination(
                [
                    "POLICY-A"
                ]
            ),
            cost_calculated_combination(
                [
                    "POLICY-A"
                ]
            )
        ]
    )

    assert result["recommended_combination"] is None
    assert [
        error["reason"]
        for error in result["errors"]
    ] == [
        "duplicate_policy_ids_combination",
        "duplicate_policy_ids_combination",
        "no_recommendation_candidates"
    ]


def test_rejected_combinations_are_not_recommendation_candidates():

    rejected = [
        {
            "policy_ids":
                [
                    "POLICY-B"
                ],
            "reasons":
                [
                    {
                        "type":
                            "mutually_exclusive"
                    }
                ]
        }
    ]

    result = select_optimal_combination(
        [
            cost_calculated_combination(
                [
                    "POLICY-A"
                ],
                net_employer_cost=100
            )
        ],
        rejected
    )

    assert recommended_policy_ids(
        result
    ) == [
        "POLICY-A"
    ]
    assert result["rejected_combinations"] == rejected


def test_existing_employer_net_cost_regression():

    test_multiple_cost_items_are_summed()


def test_existing_combination_amount_summarizer_regression():

    test_single_policy_combination_total_amount()


def test_existing_policy_combination_generator_regression():

    test_three_non_conflicting_candidates_create_seven_combinations()


if __name__ == "__main__":

    test_single_candidate_is_selected()
    test_lowest_net_employer_cost_is_selected()
    test_highest_subsidy_is_not_selected_when_net_cost_is_higher()
    test_equal_net_cost_uses_higher_total_subsidy_tie_break()
    test_equal_net_and_subsidy_uses_fewer_policies_tie_break()
    test_all_major_values_equal_uses_policy_id_sort_tie_break()
    test_negative_net_cost_is_valid_candidate()
    test_no_candidates_returns_error()
    test_null_net_employer_cost_candidate_is_excluded()
    test_null_total_subsidy_amount_candidate_is_excluded()
    test_missing_or_empty_policy_ids_are_excluded()
    test_duplicate_policy_ids_combination_returns_error_without_merge()
    test_rejected_combinations_are_not_recommendation_candidates()
    test_existing_employer_net_cost_regression()
    test_existing_combination_amount_summarizer_regression()
    test_existing_policy_combination_generator_regression()
    print("test_optimal_combination_selector passed")
