from typing import Dict, List

from services.combination_rule_validator import (
    validate_combination_rules
)


APPROVED_STATUS = "approved"
REQUIRES = "requires"


def get_policy_id(
    policy_json: Dict
):

    return (
        policy_json.get(
            "policy_id"
        )
        or policy_json.get(
            "policy_key"
        )
    )


def detect_required_policy_violations(
    candidate_policies: List[Dict]
) -> Dict:

    approved_policies = [
        policy
        for policy in candidate_policies
        if policy.get(
            "review_status"
        ) == APPROVED_STATUS
    ]

    approved_policy_ids = {
        get_policy_id(
            policy
        )
        for policy in approved_policies
    }

    violations = []
    errors = []

    for policy in approved_policies:

        source_policy_id = get_policy_id(
            policy
        )

        validation_result = validate_combination_rules(
            policy
        )

        for error in validation_result.get(
            "errors",
            []
        ):

            errors.append({
                "policy_id":
                    source_policy_id,
                "rule_id":
                    error.get(
                        "rule_id"
                    ),
                "field":
                    error.get(
                        "field"
                    ),
                "reason":
                    error.get(
                        "reason"
                    )
            })

        if validation_result.get(
            "errors"
        ):

            continue

        for rule in validation_result.get(
            "normalized_rules",
            []
        ):

            if rule.get(
                "rule_type"
            ) != REQUIRES:

                continue

            required_policy_ids = rule.get(
                "target_policy_ids",
                []
            )

            missing_policy_ids = [
                policy_id
                for policy_id in required_policy_ids
                if policy_id not in approved_policy_ids
            ]

            if not missing_policy_ids:

                continue

            violations.append({
                "rule_id":
                    rule.get(
                        "rule_id"
                    ),
                "rule_type":
                    rule.get(
                        "rule_type"
                    ),
                "source_policy_id":
                    source_policy_id,
                "required_policy_ids":
                    required_policy_ids,
                "missing_policy_ids":
                    missing_policy_ids,
                "reason":
                    rule.get(
                        "reason"
                    ),
                "evidence_snippets":
                    rule.get(
                        "evidence_snippets",
                        []
                    )
            })

    return {
        "valid":
            not errors,
        "violations":
            violations,
        "errors":
            errors
    }
