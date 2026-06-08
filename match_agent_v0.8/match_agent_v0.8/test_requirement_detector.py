from services.requirement_detector import (
    detect_required_policy_violations
)

from test_combination_rule_validator import (
    test_valid_requires_rule
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
    rule_type="requires",
    target_policy_ids=None,
    reason="This policy requires the target policy.",
    evidence_snippets=None
):

    if target_policy_ids is None:

        target_policy_ids = [
            "POLICY-B"
        ]

    if evidence_snippets is None:

        evidence_snippets = [
            "Source sentence says this policy requires the target policy."
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


def test_no_requires_rules():

    result = detect_required_policy_violations(
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
        "violations": [],
        "errors": []
    }


def test_required_policy_present_creates_no_violation():

    result = detect_required_policy_violations(
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
    assert result["violations"] == []
    assert result["errors"] == []


def test_missing_required_policy_creates_violation():

    result = detect_required_policy_violations(
        [
            policy(
                "POLICY-A",
                rules=[
                    rule(
                        "CR-A-B"
                    )
                ]
            )
        ]
    )

    assert result["valid"] is True
    assert result["violations"] == [
        {
            "rule_id": "CR-A-B",
            "rule_type": "requires",
            "source_policy_id": "POLICY-A",
            "required_policy_ids": [
                "POLICY-B"
            ],
            "missing_policy_ids": [
                "POLICY-B"
            ],
            "reason": "This policy requires the target policy.",
            "evidence_snippets": [
                "Source sentence says this policy requires the target policy."
            ]
        }
    ]


def test_multiple_required_policies_present_create_no_violation():

    result = detect_required_policy_violations(
        [
            policy(
                "POLICY-A",
                rules=[
                    rule(
                        "CR-A-BC",
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

    assert result["valid"] is True
    assert result["violations"] == []


def test_one_of_multiple_required_policies_missing():

    result = detect_required_policy_violations(
        [
            policy(
                "POLICY-A",
                rules=[
                    rule(
                        "CR-A-BC",
                        target_policy_ids=[
                            "POLICY-B",
                            "POLICY-C"
                        ]
                    )
                ]
            ),
            policy(
                "POLICY-B"
            )
        ]
    )

    assert result["valid"] is True
    assert result["violations"][0]["required_policy_ids"] == [
        "POLICY-B",
        "POLICY-C"
    ]
    assert result["violations"][0]["missing_policy_ids"] == [
        "POLICY-C"
    ]


def test_required_target_needs_review_counts_as_missing():

    result = detect_required_policy_violations(
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
                "POLICY-B",
                review_status="needs_review"
            )
        ]
    )

    assert result["valid"] is True
    assert result["violations"][0]["missing_policy_ids"] == [
        "POLICY-B"
    ]


def test_required_target_deprecated_counts_as_missing():

    result = detect_required_policy_violations(
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
                "POLICY-B",
                review_status="deprecated"
            )
        ]
    )

    assert result["valid"] is True
    assert result["violations"][0]["missing_policy_ids"] == [
        "POLICY-B"
    ]


def test_absent_source_policy_creates_no_violation():

    result = detect_required_policy_violations(
        [
            policy(
                "POLICY-B"
            )
        ]
    )

    assert result["valid"] is True
    assert result["violations"] == []


def test_mutually_exclusive_rule_is_ignored():

    result = detect_required_policy_violations(
        [
            policy(
                "POLICY-A",
                rules=[
                    rule(
                        "CR-ME",
                        rule_type="mutually_exclusive"
                    )
                ]
            )
        ]
    )

    assert result["valid"] is True
    assert result["violations"] == []


def test_allowed_with_rule_is_ignored():

    result = detect_required_policy_violations(
        [
            policy(
                "POLICY-A",
                rules=[
                    rule(
                        "CR-ALLOW",
                        rule_type="allowed_with"
                    )
                ]
            )
        ]
    )

    assert result["valid"] is True
    assert result["violations"] == []


def test_schema_error_is_returned_separately():

    result = detect_required_policy_violations(
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
    assert result["violations"] == []
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

    result = detect_required_policy_violations(
        [
            policy(
                "POLICY-A",
                rules=[
                    rule(
                        "CR-A-B",
                        evidence_snippets=evidence
                    )
                ]
            )
        ]
    )

    assert result["violations"][0]["evidence_snippets"] == evidence


def test_existing_combination_rule_schema_regression():

    test_valid_requires_rule()


def test_existing_mutually_exclusive_detector_regression():

    test_one_way_mutually_exclusive_rule_creates_conflict()


def test_existing_monthly_fixed_regression():

    test_requested_months_shorter_than_max_months()


def test_existing_period_tiered_regression():

    test_requested_months_span_two_tiers()


def test_existing_conditional_bonus_regression():

    test_bonus_applies_and_is_added_to_base_amount()


def test_existing_standard_result_regression():

    test_monthly_fixed_result_has_standard_structure()


if __name__ == "__main__":

    test_no_requires_rules()
    test_required_policy_present_creates_no_violation()
    test_missing_required_policy_creates_violation()
    test_multiple_required_policies_present_create_no_violation()
    test_one_of_multiple_required_policies_missing()
    test_required_target_needs_review_counts_as_missing()
    test_required_target_deprecated_counts_as_missing()
    test_absent_source_policy_creates_no_violation()
    test_mutually_exclusive_rule_is_ignored()
    test_allowed_with_rule_is_ignored()
    test_schema_error_is_returned_separately()
    test_evidence_snippets_are_preserved()
    test_existing_combination_rule_schema_regression()
    test_existing_mutually_exclusive_detector_regression()
    test_existing_monthly_fixed_regression()
    test_existing_period_tiered_regression()
    test_existing_conditional_bonus_regression()
    test_existing_standard_result_regression()
    print("test_requirement_detector passed")
