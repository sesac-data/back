from services.combination_rule_validator import (
    validate_combination_rules
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
    rules=None
):

    data = {
        "policy_id":
            "POLICY-A",
        "policy_key":
            "POLICY-A",
        "policy_name":
            "Combination Rule Test Policy"
    }

    if rules is not None:

        data[
            "combination_rules"
        ] = rules

    return data


def rule(
    rule_id="CR-001",
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
            "Source sentence says the policies cannot be combined."
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


def error_reasons(
    result
):

    return [
        error["reason"]
        for error in result["errors"]
    ]


def test_missing_combination_rules_normalizes_to_empty_list():

    result = validate_combination_rules(
        policy()
    )

    assert result["valid"] is True
    assert result["normalized_rules"] == []
    assert result["errors"] == []


def test_valid_mutually_exclusive_rule():

    result = validate_combination_rules(
        policy(
            [
                rule(
                    rule_type="mutually_exclusive"
                )
            ]
        )
    )

    assert result["valid"] is True
    assert result["normalized_rules"][0]["rule_type"] == "mutually_exclusive"
    assert result["normalized_rules"][0]["evidence_snippets"] == [
        "Source sentence says the policies cannot be combined."
    ]


def test_valid_requires_rule():

    result = validate_combination_rules(
        policy(
            [
                rule(
                    rule_id="CR-REQ",
                    rule_type="requires"
                )
            ]
        )
    )

    assert result["valid"] is True
    assert result["normalized_rules"][0]["rule_type"] == "requires"


def test_valid_allowed_with_rule():

    result = validate_combination_rules(
        policy(
            [
                rule(
                    rule_id="CR-ALLOW",
                    rule_type="allowed_with"
                )
            ]
        )
    )

    assert result["valid"] is True
    assert result["normalized_rules"][0]["rule_type"] == "allowed_with"


def test_unsupported_rule_type_returns_error():

    result = validate_combination_rules(
        policy(
            [
                rule(
                    rule_type="unknown"
                )
            ]
        )
    )

    assert result["valid"] is False
    assert result["errors"][0] == {
        "rule_id": "CR-001",
        "field": "rule_type",
        "reason": "unsupported_rule_type"
    }


def test_missing_rule_id_returns_error():

    result = validate_combination_rules(
        policy(
            [
                rule(
                    rule_id=""
                )
            ]
        )
    )

    assert result["valid"] is False
    assert result["errors"][0]["rule_id"] == "rule[0]"
    assert result["errors"][0]["field"] == "rule_id"
    assert result["errors"][0]["reason"] == "rule_id_required"


def test_empty_target_policy_ids_returns_error():

    result = validate_combination_rules(
        policy(
            [
                rule(
                    target_policy_ids=[]
                )
            ]
        )
    )

    assert result["valid"] is False
    assert "target_policy_ids_required" in error_reasons(
        result
    )


def test_self_reference_returns_error():

    result = validate_combination_rules(
        policy(
            [
                rule(
                    target_policy_ids=[
                        "POLICY-A"
                    ]
                )
            ]
        )
    )

    assert result["valid"] is False
    assert "target_policy_ids_must_not_include_self" in error_reasons(
        result
    )


def test_duplicate_target_policy_ids_return_error():

    result = validate_combination_rules(
        policy(
            [
                rule(
                    target_policy_ids=[
                        "POLICY-B",
                        "POLICY-B"
                    ]
                )
            ]
        )
    )

    assert result["valid"] is False
    assert "target_policy_ids_must_be_unique" in error_reasons(
        result
    )


def test_missing_reason_returns_error():

    result = validate_combination_rules(
        policy(
            [
                rule(
                    reason=""
                )
            ]
        )
    )

    assert result["valid"] is False
    assert "reason_required" in error_reasons(
        result
    )


def test_missing_evidence_snippets_returns_error():

    result = validate_combination_rules(
        policy(
            [
                rule(
                    evidence_snippets=[]
                )
            ]
        )
    )

    assert result["valid"] is False
    assert "evidence_snippets_required" in error_reasons(
        result
    )


def test_mixed_valid_and_invalid_rules_returns_structured_errors():

    result = validate_combination_rules(
        policy(
            [
                rule(
                    rule_id="CR-VALID",
                    rule_type="allowed_with"
                ),
                rule(
                    rule_id="CR-BAD",
                    rule_type="blocked_by",
                    reason=""
                )
            ]
        )
    )

    assert result["valid"] is False
    assert len(result["normalized_rules"]) == 2
    assert {
        "rule_id": "CR-BAD",
        "field": "rule_type",
        "reason": "unsupported_rule_type"
    } in result["errors"]
    assert {
        "rule_id": "CR-BAD",
        "field": "reason",
        "reason": "reason_required"
    } in result["errors"]


def test_existing_monthly_fixed_regression():

    test_requested_months_shorter_than_max_months()


def test_existing_period_tiered_regression():

    test_requested_months_span_two_tiers()


def test_existing_conditional_bonus_regression():

    test_bonus_applies_and_is_added_to_base_amount()


def test_existing_standard_result_regression():

    test_monthly_fixed_result_has_standard_structure()


if __name__ == "__main__":

    test_missing_combination_rules_normalizes_to_empty_list()
    test_valid_mutually_exclusive_rule()
    test_valid_requires_rule()
    test_valid_allowed_with_rule()
    test_unsupported_rule_type_returns_error()
    test_missing_rule_id_returns_error()
    test_empty_target_policy_ids_returns_error()
    test_self_reference_returns_error()
    test_duplicate_target_policy_ids_return_error()
    test_missing_reason_returns_error()
    test_missing_evidence_snippets_returns_error()
    test_mixed_valid_and_invalid_rules_returns_structured_errors()
    test_existing_monthly_fixed_regression()
    test_existing_period_tiered_regression()
    test_existing_conditional_bonus_regression()
    test_existing_standard_result_regression()
    print("test_combination_rule_validator passed")
