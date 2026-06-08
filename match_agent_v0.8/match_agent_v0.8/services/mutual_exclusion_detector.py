from typing import Dict, List

from services.combination_rule_validator import (
    validate_combination_rules
)


APPROVED_STATUS = "approved"
MUTUALLY_EXCLUSIVE = "mutually_exclusive"


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


def build_conflict_key(
    source_policy_id: str,
    target_policy_id: str
):

    return tuple(
        sorted(
            [
                source_policy_id,
                target_policy_id
            ]
        )
    )


def detect_mutually_exclusive_conflicts(
    candidate_policies: List[Dict]
) -> Dict:

    approved_policies = [
        policy
        for policy in candidate_policies
        if policy.get(
            "review_status"
        ) == APPROVED_STATUS
    ]

    candidate_policy_ids = {
        get_policy_id(
            policy
        )
        for policy in approved_policies
    }

    conflicts = []
    errors = []
    seen_conflict_keys = set()

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
            ) != MUTUALLY_EXCLUSIVE:

                continue

            for target_policy_id in rule.get(
                "target_policy_ids",
                []
            ):

                if target_policy_id not in candidate_policy_ids:

                    continue

                conflict_key = build_conflict_key(
                    source_policy_id,
                    target_policy_id
                )

                if conflict_key in seen_conflict_keys:

                    continue

                seen_conflict_keys.add(
                    conflict_key
                )

                conflicts.append({
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
                    "target_policy_id":
                        target_policy_id,
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
        "conflicts":
            conflicts,
        "errors":
            errors
    }
