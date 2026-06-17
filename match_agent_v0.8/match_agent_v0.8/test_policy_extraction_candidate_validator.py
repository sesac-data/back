from copy import deepcopy

from services.policy_extraction_candidate_validator import (
    validate_policy_extraction_candidate,
)


RAW_TEXT = (
    "정책명 지원금입니다. 월 300000원, 최대 12개월 지원합니다. "
    "대상 조건은 6개월 이상 근무입니다. 중복 수급은 제한됩니다."
)


def valid_candidate():

    return {
        "policy_id": "POLICY-001",
        "policy_name": "정책명 지원금",
        "review_status": "needs_review",
        "evidence_snippets": [
            "정책명 지원금입니다.",
        ],
        "support_items": [
            {
                "support_item_id": "SI-001",
                "calculation_type": "monthly_fixed",
                "monthly_amount": 300000,
                "max_months": 12,
                "conditions": [
                    {
                        "condition_id": "C-001",
                        "field": "employee.months_worked",
                        "operator": "gte",
                        "expected": 6,
                        "evidence_snippets": [
                            "대상 조건은 6개월 이상 근무입니다.",
                        ],
                    }
                ],
                "evidence_snippets": [
                    "월 300000원, 최대 12개월 지원합니다.",
                ],
            }
        ],
        "combination_rules": [
            {
                "rule_id": "CR-001",
                "rule_type": "mutually_exclusive",
                "target_policy_ids": [
                    "POLICY-OTHER",
                ],
                "reason": "중복 수급 제한",
                "evidence_snippets": [
                    "중복 수급은 제한됩니다.",
                ],
            }
        ],
        "unresolved_rules": [],
    }


def error_types(result):

    return {
        error["error_type"]
        for error in result["errors"]
    }


def test_valid_candidate_passes_without_mutation():

    candidate = valid_candidate()
    before = deepcopy(
        candidate
    )

    result = validate_policy_extraction_candidate(
        candidate,
        RAW_TEXT,
    )

    assert result["passed"] is True
    assert result["errors"] == []
    assert result["mutation_detected"] is False
    assert candidate == before


def test_current_v3_empty_policy_id_is_detected_without_injection():

    candidate = valid_candidate()
    candidate["policy_id"] = ""

    result = validate_policy_extraction_candidate(
        candidate,
        RAW_TEXT,
    )

    assert "missing_policy_id" in error_types(
        result
    )
    assert candidate["policy_id"] == ""


def test_monthly_amount_type_error_is_detected():

    candidate = valid_candidate()
    candidate["support_items"][0]["monthly_amount"] = "300000"

    result = validate_policy_extraction_candidate(
        candidate,
        RAW_TEXT,
    )

    assert "invalid_monthly_amount" in error_types(
        result
    )


def test_null_max_months_is_allowed_when_source_states_no_cap():

    candidate = valid_candidate()
    candidate["support_items"][0]["max_months"] = None

    result = validate_policy_extraction_candidate(
        candidate,
        RAW_TEXT,
    )

    assert "invalid_max_months" not in error_types(
        result
    )
    assert result["passed"] is True


def test_present_but_invalid_max_months_is_still_detected():

    candidate = valid_candidate()
    candidate["support_items"][0]["max_months"] = 0

    result = validate_policy_extraction_candidate(
        candidate,
        RAW_TEXT,
    )

    assert "invalid_max_months" in error_types(
        result
    )


def test_unsupported_calculation_type_is_detected():

    candidate = valid_candidate()
    candidate["support_items"][0]["calculation_type"] = "weekly_fixed"

    result = validate_policy_extraction_candidate(
        candidate,
        RAW_TEXT,
    )

    assert "unsupported_calculation_type" in error_types(
        result
    )


def test_unknown_policy_id_in_combination_rule_is_detected():

    candidate = valid_candidate()
    candidate["combination_rules"][0]["target_policy_ids"] = [
        "UNKNOWN_POLICY_ID",
    ]

    result = validate_policy_extraction_candidate(
        candidate,
        RAW_TEXT,
    )

    assert "unknown_policy_id" in error_types(
        result
    )


def test_evidence_mismatch_is_detected():

    candidate = valid_candidate()
    candidate["support_items"][0]["evidence_snippets"] = [
        "원문에 없는 근거",
    ]

    result = validate_policy_extraction_candidate(
        candidate,
        RAW_TEXT,
    )

    assert "evidence_not_in_raw_text" in error_types(
        result
    )


def test_evidence_compare_allows_whitespace_and_newline_differences():

    candidate = valid_candidate()
    candidate["evidence_snippets"] = [
        "Policy source line.",
    ]
    candidate["support_items"][0]["evidence_snippets"] = [
        "Monthly amount\n300000 won",
    ]
    candidate["support_items"][0]["conditions"] = []
    candidate["combination_rules"] = []

    result = validate_policy_extraction_candidate(
        candidate,
        "Policy source line. Monthly amount 300000 won.",
    )

    assert "evidence_not_in_raw_text" not in error_types(
        result
    )


def test_empty_evidence_is_detected():

    candidate = valid_candidate()
    candidate["evidence_snippets"] = []

    result = validate_policy_extraction_candidate(
        candidate,
        RAW_TEXT,
    )

    assert "missing_evidence" in error_types(
        result
    )


def test_duplicate_support_condition_and_rule_ids_are_detected():

    candidate = valid_candidate()
    candidate["support_items"].append(
        deepcopy(
            candidate["support_items"][0]
        )
    )
    candidate["combination_rules"].append(
        deepcopy(
            candidate["combination_rules"][0]
        )
    )

    result = validate_policy_extraction_candidate(
        candidate,
        RAW_TEXT,
    )
    types = error_types(
        result
    )

    assert "duplicate_support_item_id" in types
    assert "duplicate_condition_id" in types
    assert "duplicate_rule_id" in types


def test_missing_target_policy_ids_is_detected():

    candidate = valid_candidate()
    candidate["combination_rules"][0]["target_policy_ids"] = []

    result = validate_policy_extraction_candidate(
        candidate,
        RAW_TEXT,
    )

    assert "missing_target_policy_ids" in error_types(
        result
    )


def test_invalid_review_status_is_detected():

    candidate = valid_candidate()
    candidate["review_status"] = "approved"

    result = validate_policy_extraction_candidate(
        candidate,
        RAW_TEXT,
    )

    assert "invalid_review_status" in error_types(
        result
    )


def test_unsupported_fields_are_reported():

    candidate = valid_candidate()
    candidate["unsupported_extra"] = True
    candidate["support_items"][0]["unsupported_extra"] = True

    result = validate_policy_extraction_candidate(
        candidate,
        RAW_TEXT,
    )
    unsupported_paths = [
        error["path"]
        for error in result["errors"]
        if error["error_type"] == "unsupported_field"
    ]

    assert "$.unsupported_extra" in unsupported_paths
    assert "$.support_items[0].unsupported_extra" in unsupported_paths


def test_unresolved_rules_must_remain_array():

    candidate = valid_candidate()
    candidate["unresolved_rules"] = {
        "rule_id": "UR-001",
    }

    result = validate_policy_extraction_candidate(
        candidate,
        RAW_TEXT,
    )

    assert "invalid_unresolved_rules" in error_types(
        result
    )


if __name__ == "__main__":

    test_valid_candidate_passes_without_mutation()
    test_current_v3_empty_policy_id_is_detected_without_injection()
    test_monthly_amount_type_error_is_detected()
    test_unsupported_calculation_type_is_detected()
    test_unknown_policy_id_in_combination_rule_is_detected()
    test_evidence_mismatch_is_detected()
    test_evidence_compare_allows_whitespace_and_newline_differences()
    test_empty_evidence_is_detected()
    test_duplicate_support_condition_and_rule_ids_are_detected()
    test_missing_target_policy_ids_is_detected()
    test_invalid_review_status_is_detected()
    test_unsupported_fields_are_reported()
    test_unresolved_rules_must_remain_array()
    print("test_policy_extraction_candidate_validator passed")
