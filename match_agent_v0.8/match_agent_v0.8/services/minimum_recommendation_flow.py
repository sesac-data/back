from typing import Dict, List

from services.calculation_service import (
    calculate_yearly_amount
)

from services.condition_evaluator import (
    evaluate_condition
)

from services.condition_registry import (
    SUPPORTED_CONDITION_TYPES
)


APPROVED_STATUS = "approved"
REVIEW_STATUS_FIELD = "review_status"


def _collect_evidence(
    *items
) -> List[str]:

    evidence = []

    for item in items:

        if not isinstance(
            item,
            dict
        ):
            continue

        for snippet in item.get(
            "evidence_snippets",
            []
        ):

            if snippet not in evidence:

                evidence.append(
                    snippet
                )

    return evidence


def run_minimum_recommendation_flow(
    policy_json: Dict,
    company_data: Dict,
    employee_data: Dict,
    leave_data: Dict
) -> Dict:

    policy_key = policy_json.get(
        "policy_key"
    )

    if policy_json.get(
        REVIEW_STATUS_FIELD
    ) != APPROVED_STATUS:

        return {
            "policy_key": policy_key,
            "status": "needs_review",
            "eligible": False,
            "calculation_steps": [
                "Policy is not approved; recommendation calculation skipped."
            ],
            "evidence_snippets": []
        }

    support_items = policy_json.get(
        "support_items",
        []
    )

    if not support_items:

        return {
            "policy_key": policy_key,
            "status": "needs_review",
            "eligible": False,
            "calculation_steps": [
                "Approved policy has no support_items."
            ],
            "evidence_snippets": []
        }

    support_item = support_items[0]
    conditions = support_item.get(
        "conditions",
        []
    )

    passed_conditions = []
    failed_conditions = []
    unsupported_conditions = []
    evidence = _collect_evidence(
        support_item,
        support_item.get(
            "support",
            {}
        )
    )

    evaluation_input = dict(
        employee_data
    )

    evaluation_input[
        "leave_event"
    ] = leave_data

    for condition in conditions:

        condition_type = condition.get(
            "type"
        )

        condition_evidence = _collect_evidence(
            condition
        )

        for snippet in condition_evidence:

            if snippet not in evidence:

                evidence.append(
                    snippet
                )

        condition_result = {
            "type": condition_type,
            "condition": condition,
            "evidence_snippets": condition_evidence
        }

        if (
            condition_type
            not in SUPPORTED_CONDITION_TYPES
        ):

            unsupported_conditions.append(
                condition_result
            )

            continue

        if evaluate_condition(
            company_data,
            evaluation_input,
            condition
        ):

            passed_conditions.append(
                condition_result
            )

        else:

            failed_conditions.append(
                condition_result
            )

    if unsupported_conditions:

        return {
            "policy_key": policy_key,
            "policy_name": policy_json.get(
                "policy_name"
            ),
            "support_type": support_item.get(
                "support_type"
            ),
            "status": "unsupported",
            "eligible": False,
            "passed_conditions": passed_conditions,
            "failed_conditions": failed_conditions,
            "unsupported_conditions": unsupported_conditions,
            "expected_amount": 0,
            "calculation_steps": [
                "Unsupported condition type found; amount calculation skipped."
            ],
            "evidence_snippets": evidence
        }

    if failed_conditions:

        return {
            "policy_key": policy_key,
            "policy_name": policy_json.get(
                "policy_name"
            ),
            "support_type": support_item.get(
                "support_type"
            ),
            "status": "ineligible",
            "eligible": False,
            "passed_conditions": passed_conditions,
            "failed_conditions": failed_conditions,
            "unsupported_conditions": [],
            "expected_amount": 0,
            "calculation_steps": [
                "One or more conditions failed; amount calculation skipped."
            ],
            "evidence_snippets": evidence
        }

    support = support_item.get(
        "support",
        {}
    )

    expected_amount = calculate_yearly_amount(
        support
    )

    return {
        "policy_key": policy_key,
        "policy_name": policy_json.get(
            "policy_name"
        ),
        "support_type": support_item.get(
            "support_type"
        ),
        "status": "eligible",
        "eligible": True,
        "passed_conditions": passed_conditions,
        "failed_conditions": [],
        "unsupported_conditions": [],
        "expected_amount": expected_amount,
        "calculation_steps": [
            "Policy review_status is approved.",
            f"Evaluated {len(conditions)} supported conditions.",
            (
                "Calculated expected_amount with "
                "services.calculation_service.calculate_yearly_amount."
            ),
            f"expected_amount={expected_amount}"
        ],
        "evidence_snippets": evidence
    }
