from services.policy_combination_generator import (
    MAX_COMBINATION_CANDIDATES,
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

from test_requirement_detector import (
    test_missing_required_policy_creates_violation
)

from test_standardized_calculation_result import (
    test_monthly_fixed_result_has_standard_structure
)


def policy(
    policy_id,
    review_status="approved",
    rules=None
):

    return {
        "policy_id":
            policy_id,
        "policy_key":
            policy_id,
        "policy_name":
            f"{policy_id} Test Policy",
        "review_status":
            review_status,
        "combination_rules":
            rules or []
    }


def rule(
    rule_id,
    rule_type,
    target_policy_ids,
    reason="Source-backed combination rule reason.",
    evidence_snippets=None
):

    if evidence_snippets is None:

        evidence_snippets = [
            "Exact source evidence sentence."
        ]

    return {
        "rule_id":
            rule_id,
        "rule_type":
            rule_type,
        "target_policy_ids":
            target_policy_ids,
        "reason":
            reason,
        "evidence_snippets":
            evidence_snippets
    }


def valid_policy_ids(
    result
):

    return [
        combination["policy_ids"]
        for combination in result["valid_combinations"]
    ]


def rejected_by_ids(
    result,
    policy_ids
):

    for combination in result["rejected_combinations"]:

        if combination["policy_ids"] == policy_ids:

            return combination

    return None


def test_single_candidate_creates_one_combination():

    result = generate_valid_policy_combinations(
        [
            policy(
                "POLICY-A"
            )
        ]
    )

    assert result["errors"] == []
    assert valid_policy_ids(
        result
    ) == [
        [
            "POLICY-A"
        ]
    ]
    assert result["rejected_combinations"] == []


def test_three_non_conflicting_candidates_create_seven_combinations():

    result = generate_valid_policy_combinations(
        [
            policy(
                "POLICY-A"
            ),
            policy(
                "POLICY-B"
            ),
            policy(
                "POLICY-C"
            )
        ]
    )

    assert len(
        result["valid_combinations"]
    ) == 7
    assert result["rejected_combinations"] == []
    assert result["errors"] == []


def test_mutually_exclusive_pair_is_rejected():

    result = generate_valid_policy_combinations(
        [
            policy(
                "POLICY-A",
                rules=[
                    rule(
                        "CR-A-B",
                        "mutually_exclusive",
                        [
                            "POLICY-B"
                        ]
                    )
                ]
            ),
            policy(
                "POLICY-B"
            )
        ]
    )

    rejected = rejected_by_ids(
        result,
        [
            "POLICY-A",
            "POLICY-B"
        ]
    )

    assert rejected is not None
    assert rejected["reasons"][0]["type"] == "mutually_exclusive"
    assert [
        "POLICY-A",
        "POLICY-B"
    ] not in valid_policy_ids(
        result
    )


def test_required_policy_missing_rejects_singleton_but_pair_is_valid():

    result = generate_valid_policy_combinations(
        [
            policy(
                "POLICY-A"
            ),
            policy(
                "POLICY-C",
                rules=[
                    rule(
                        "CR-C-A",
                        "requires",
                        [
                            "POLICY-A"
                        ]
                    )
                ]
            )
        ]
    )

    rejected = rejected_by_ids(
        result,
        [
            "POLICY-C"
        ]
    )

    assert rejected is not None
    assert rejected["reasons"][0]["type"] == "requires"
    assert [
        "POLICY-A",
        "POLICY-C"
    ] in valid_policy_ids(
        result
    )


def test_combination_can_have_conflict_and_requires_reasons_together():

    result = generate_valid_policy_combinations(
        [
            policy(
                "POLICY-A",
                rules=[
                    rule(
                        "CR-A-B",
                        "mutually_exclusive",
                        [
                            "POLICY-B"
                        ]
                    )
                ]
            ),
            policy(
                "POLICY-B"
            ),
            policy(
                "POLICY-C",
                rules=[
                    rule(
                        "CR-C-D",
                        "requires",
                        [
                            "POLICY-D"
                        ]
                    )
                ]
            )
        ]
    )

    rejected = rejected_by_ids(
        result,
        [
            "POLICY-A",
            "POLICY-B",
            "POLICY-C"
        ]
    )

    reason_types = [
        reason["type"]
        for reason in rejected["reasons"]
    ]

    assert "mutually_exclusive" in reason_types
    assert "requires" in reason_types


def test_needs_review_policy_is_excluded_from_candidates():

    result = generate_valid_policy_combinations(
        [
            policy(
                "POLICY-A"
            ),
            policy(
                "POLICY-B",
                review_status="needs_review"
            )
        ]
    )

    assert valid_policy_ids(
        result
    ) == [
        [
            "POLICY-A"
        ]
    ]


def test_deprecated_policy_is_excluded_from_candidates():

    result = generate_valid_policy_combinations(
        [
            policy(
                "POLICY-A"
            ),
            policy(
                "POLICY-B",
                review_status="deprecated"
            )
        ]
    )

    assert valid_policy_ids(
        result
    ) == [
        [
            "POLICY-A"
        ]
    ]


def test_allowed_with_rule_does_not_affect_result():

    result = generate_valid_policy_combinations(
        [
            policy(
                "POLICY-A",
                rules=[
                    rule(
                        "CR-ALLOW",
                        "allowed_with",
                        [
                            "POLICY-B"
                        ]
                    )
                ]
            ),
            policy(
                "POLICY-B"
            )
        ]
    )

    assert len(
        result["valid_combinations"]
    ) == 3
    assert result["rejected_combinations"] == []
    assert result["errors"] == []


def test_duplicate_policy_id_returns_error():

    result = generate_valid_policy_combinations(
        [
            policy(
                "POLICY-A"
            ),
            policy(
                "POLICY-A"
            )
        ]
    )

    assert result["valid_combinations"] == []
    assert result["rejected_combinations"] == []
    assert result["errors"] == [
        {
            "field": "policy_id",
            "reason": "duplicate_policy_id",
            "details": {
                "policy_ids": [
                    "POLICY-A"
                ]
            }
        }
    ]


def test_empty_candidates_return_empty_valid_combinations():

    result = generate_valid_policy_combinations(
        []
    )

    assert result == {
        "valid_combinations": [],
        "rejected_combinations": [],
        "errors": []
    }


def test_candidate_count_above_guard_returns_error():

    result = generate_valid_policy_combinations(
        [
            policy(
                f"POLICY-{index:02d}"
            )
            for index in range(
                MAX_COMBINATION_CANDIDATES + 1
            )
        ]
    )

    assert result["valid_combinations"] == []
    assert result["rejected_combinations"] == []
    assert result["errors"][0] == {
        "field": "candidate_policies",
        "reason": "max_combination_candidates_exceeded",
        "details": {
            "max": MAX_COMBINATION_CANDIDATES,
            "actual": MAX_COMBINATION_CANDIDATES + 1
        }
    }


def test_result_order_is_deterministic():

    result = generate_valid_policy_combinations(
        [
            policy(
                "POLICY-C"
            ),
            policy(
                "POLICY-A"
            ),
            policy(
                "POLICY-B"
            )
        ]
    )

    assert valid_policy_ids(
        result
    ) == [
        [
            "POLICY-A"
        ],
        [
            "POLICY-B"
        ],
        [
            "POLICY-C"
        ],
        [
            "POLICY-A",
            "POLICY-B"
        ],
        [
            "POLICY-A",
            "POLICY-C"
        ],
        [
            "POLICY-B",
            "POLICY-C"
        ],
        [
            "POLICY-A",
            "POLICY-B",
            "POLICY-C"
        ]
    ]


def test_rejected_combination_preserves_evidence_snippets():

    evidence = [
        "Exact source evidence for rejection."
    ]

    result = generate_valid_policy_combinations(
        [
            policy(
                "POLICY-A",
                rules=[
                    rule(
                        "CR-A-B",
                        "mutually_exclusive",
                        [
                            "POLICY-B"
                        ],
                        evidence_snippets=evidence
                    )
                ]
            ),
            policy(
                "POLICY-B"
            )
        ]
    )

    rejected = rejected_by_ids(
        result,
        [
            "POLICY-A",
            "POLICY-B"
        ]
    )

    assert rejected["reasons"][0]["details"]["evidence_snippets"] == evidence


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

    test_single_candidate_creates_one_combination()
    test_three_non_conflicting_candidates_create_seven_combinations()
    test_mutually_exclusive_pair_is_rejected()
    test_required_policy_missing_rejects_singleton_but_pair_is_valid()
    test_combination_can_have_conflict_and_requires_reasons_together()
    test_needs_review_policy_is_excluded_from_candidates()
    test_deprecated_policy_is_excluded_from_candidates()
    test_allowed_with_rule_does_not_affect_result()
    test_duplicate_policy_id_returns_error()
    test_empty_candidates_return_empty_valid_combinations()
    test_candidate_count_above_guard_returns_error()
    test_result_order_is_deterministic()
    test_rejected_combination_preserves_evidence_snippets()
    test_existing_combination_rule_schema_regression()
    test_existing_mutually_exclusive_regression()
    test_existing_requires_regression()
    test_existing_monthly_fixed_regression()
    test_existing_period_tiered_regression()
    test_existing_conditional_bonus_regression()
    test_existing_standard_result_regression()
    print("test_policy_combination_generator passed")
