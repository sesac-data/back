from services.mutual_exclusion_detector import (
    detect_mutually_exclusive_conflicts
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

from test_period_tiered_calculation import (
    test_requested_months_span_two_tiers
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
    rule_type="mutually_exclusive",
    target_policy_ids=None,
    reason="Cannot receive these policies together.",
    evidence_snippets=None
):

    if target_policy_ids is None:

        target_policy_ids = [
            "POLICY-B"
        ]

    if evidence_snippets is None:

        evidence_snippets = [
            "Source sentence says these policies cannot be combined."
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


def test_no_mutually_exclusive_relationships():

    result = detect_mutually_exclusive_conflicts(
        [
            policy(
                "POLICY-A"
            ),
            policy(
                "POLICY-B"
            )
        ]
    )

    assert result == {
        "valid": True,
        "conflicts": [],
        "errors": []
    }


def test_one_way_mutually_exclusive_rule_creates_conflict():

    result = detect_mutually_exclusive_conflicts(
        [
            policy(
                "POLICY-A",
                rules=[
                    rule(
                        "CR-A-B"
                    )
                ]
            ),
            policy(
                "POLICY-B"
            )
        ]
    )

    assert result["valid"] is True
    assert result["errors"] == []
    assert result["conflicts"] == [
        {
            "rule_id": "CR-A-B",
            "rule_type": "mutually_exclusive",
            "source_policy_id": "POLICY-A",
            "target_policy_id": "POLICY-B",
            "reason": "Cannot receive these policies together.",
            "evidence_snippets": [
                "Source sentence says these policies cannot be combined."
            ]
        }
    ]


def test_two_way_mutually_exclusive_rules_return_one_conflict():

    result = detect_mutually_exclusive_conflicts(
        [
            policy(
                "POLICY-A",
                rules=[
                    rule(
                        "CR-A-B",
                        target_policy_ids=[
                            "POLICY-B"
                        ]
                    )
                ]
            ),
            policy(
                "POLICY-B",
                rules=[
                    rule(
                        "CR-B-A",
                        target_policy_ids=[
                            "POLICY-A"
                        ]
                    )
                ]
            )
        ]
    )

    assert result["valid"] is True
    assert len(result["conflicts"]) == 1
    assert {
        result["conflicts"][0]["source_policy_id"],
        result["conflicts"][0]["target_policy_id"]
    } == {
        "POLICY-A",
        "POLICY-B"
    }


def test_one_policy_conflicts_with_multiple_targets():

    result = detect_mutually_exclusive_conflicts(
        [
            policy(
                "POLICY-A",
                rules=[
                    rule(
                        "CR-A-MULTI",
                        target_policy_ids=[
                            "POLICY-B",
                            "POLICY-C"
                        ]
                    )
                ]
            ),
            policy(
                "POLICY-B"
            ),
            policy(
                "POLICY-C"
            )
        ]
    )

    conflict_pairs = [
        (
            conflict["source_policy_id"],
            conflict["target_policy_id"]
        )
        for conflict in result["conflicts"]
    ]

    assert result["valid"] is True
    assert conflict_pairs == [
        (
            "POLICY-A",
            "POLICY-B"
        ),
        (
            "POLICY-A",
            "POLICY-C"
        )
    ]


def test_missing_target_policy_creates_no_conflict():

    result = detect_mutually_exclusive_conflicts(
        [
            policy(
                "POLICY-A",
                rules=[
                    rule(
                        "CR-A-B",
                        target_policy_ids=[
                            "POLICY-B"
                        ]
                    )
                ]
            )
        ]
    )

    assert result["valid"] is True
    assert result["conflicts"] == []


def test_needs_review_policy_is_excluded():

    result = detect_mutually_exclusive_conflicts(
        [
            policy(
                "POLICY-A",
                review_status="needs_review",
                rules=[
                    rule(
                        "CR-A-B"
                    )
                ]
            ),
            policy(
                "POLICY-B"
            )
        ]
    )

    assert result["valid"] is True
    assert result["conflicts"] == []


def test_deprecated_policy_is_excluded():

    result = detect_mutually_exclusive_conflicts(
        [
            policy(
                "POLICY-A",
                review_status="deprecated",
                rules=[
                    rule(
                        "CR-A-B"
                    )
                ]
            ),
            policy(
                "POLICY-B"
            )
        ]
    )

    assert result["valid"] is True
    assert result["conflicts"] == []


def test_requires_rule_is_ignored():

    result = detect_mutually_exclusive_conflicts(
        [
            policy(
                "POLICY-A",
                rules=[
                    rule(
                        "CR-REQ",
                        rule_type="requires"
                    )
                ]
            ),
            policy(
                "POLICY-B"
            )
        ]
    )

    assert result["valid"] is True
    assert result["conflicts"] == []


def test_allowed_with_rule_is_ignored():

    result = detect_mutually_exclusive_conflicts(
        [
            policy(
                "POLICY-A",
                rules=[
                    rule(
                        "CR-ALLOW",
                        rule_type="allowed_with"
                    )
                ]
            ),
            policy(
                "POLICY-B"
            )
        ]
    )

    assert result["valid"] is True
    assert result["conflicts"] == []


def test_schema_error_is_returned_separately():

    result = detect_mutually_exclusive_conflicts(
        [
            policy(
                "POLICY-A",
                rules=[
                    rule(
                        "CR-BAD",
                        target_policy_ids=[
                            "POLICY-A"
                        ]
                    )
                ]
            )
        ]
    )

    assert result["valid"] is False
    assert result["conflicts"] == []
    assert result["errors"] == [
        {
            "policy_id": "POLICY-A",
            "rule_id": "CR-BAD",
            "field": "target_policy_ids",
            "reason": "target_policy_ids_must_not_include_self"
        }
    ]


def test_evidence_snippets_are_preserved():

    evidence = [
        "Exact original policy evidence sentence."
    ]

    result = detect_mutually_exclusive_conflicts(
        [
            policy(
                "POLICY-A",
                rules=[
                    rule(
                        "CR-A-B",
                        evidence_snippets=evidence
                    )
                ]
            ),
            policy(
                "POLICY-B"
            )
        ]
    )

    assert result["conflicts"][0]["evidence_snippets"] == evidence


def test_existing_combination_rule_schema_regression():

    test_valid_mutually_exclusive_rule()


def test_existing_monthly_fixed_regression():

    test_requested_months_shorter_than_max_months()


def test_existing_period_tiered_regression():

    test_requested_months_span_two_tiers()


def test_existing_conditional_bonus_regression():

    test_bonus_applies_and_is_added_to_base_amount()


def test_existing_standard_result_regression():

    test_monthly_fixed_result_has_standard_structure()


if __name__ == "__main__":

    test_no_mutually_exclusive_relationships()
    test_one_way_mutually_exclusive_rule_creates_conflict()
    test_two_way_mutually_exclusive_rules_return_one_conflict()
    test_one_policy_conflicts_with_multiple_targets()
    test_missing_target_policy_creates_no_conflict()
    test_needs_review_policy_is_excluded()
    test_deprecated_policy_is_excluded()
    test_requires_rule_is_ignored()
    test_allowed_with_rule_is_ignored()
    test_schema_error_is_returned_separately()
    test_evidence_snippets_are_preserved()
    test_existing_combination_rule_schema_regression()
    test_existing_monthly_fixed_regression()
    test_existing_period_tiered_regression()
    test_existing_conditional_bonus_regression()
    test_existing_standard_result_regression()
    print("test_mutual_exclusion_detector passed")
