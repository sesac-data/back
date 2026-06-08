from typing import Dict


ALLOWED_COMBINATION_RULE_TYPES = {
    "mutually_exclusive",
    "requires",
    "allowed_with"
}


def build_combination_rule_error(
    rule_id,
    field: str,
    reason: str
) -> Dict:

    return {
        "rule_id":
            rule_id,
        "field":
            field,
        "reason":
            reason
    }


def validate_combination_rules(
    policy_json: Dict
) -> Dict:

    policy_id = (
        policy_json.get(
            "policy_id"
        )
        or policy_json.get(
            "policy_key"
        )
    )

    combination_rules = policy_json.get(
        "combination_rules",
        []
    )

    normalized_rules = []
    errors = []

    for index, rule in enumerate(
        combination_rules
    ):

        rule_id = (
            rule.get(
                "rule_id"
            )
            if isinstance(
                rule,
                dict
            )
            else None
        )

        fallback_rule_id = (
            rule_id
            or f"rule[{index}]"
        )

        if not isinstance(
            rule,
            dict
        ):

            errors.append(
                build_combination_rule_error(
                    fallback_rule_id,
                    "rule",
                    "rule_must_be_object"
                )
            )

            continue

        normalized_rule = {
            "rule_id":
                rule.get(
                    "rule_id"
                ),
            "rule_type":
                rule.get(
                    "rule_type"
                ),
            "target_policy_ids":
                rule.get(
                    "target_policy_ids",
                    []
                ),
            "reason":
                rule.get(
                    "reason"
                ),
            "evidence_snippets":
                rule.get(
                    "evidence_snippets",
                    []
                )
        }

        normalized_rules.append(
            normalized_rule
        )

        if not rule.get(
            "rule_id"
        ):

            errors.append(
                build_combination_rule_error(
                    fallback_rule_id,
                    "rule_id",
                    "rule_id_required"
                )
            )

        rule_type = rule.get(
            "rule_type"
        )

        if rule_type not in ALLOWED_COMBINATION_RULE_TYPES:

            errors.append(
                build_combination_rule_error(
                    fallback_rule_id,
                    "rule_type",
                    "unsupported_rule_type"
                )
            )

        target_policy_ids = rule.get(
            "target_policy_ids",
            []
        )

        if (
            not isinstance(
                target_policy_ids,
                list
            )
            or not target_policy_ids
        ):

            errors.append(
                build_combination_rule_error(
                    fallback_rule_id,
                    "target_policy_ids",
                    "target_policy_ids_required"
                )
            )

        else:

            if policy_id in target_policy_ids:

                errors.append(
                    build_combination_rule_error(
                        fallback_rule_id,
                        "target_policy_ids",
                        "target_policy_ids_must_not_include_self"
                    )
                )

            seen_policy_ids = set()

            for target_policy_id in target_policy_ids:

                if target_policy_id in seen_policy_ids:

                    errors.append(
                        build_combination_rule_error(
                            fallback_rule_id,
                            "target_policy_ids",
                            "target_policy_ids_must_be_unique"
                        )
                    )

                    break

                seen_policy_ids.add(
                    target_policy_id
                )

        if not rule.get(
            "reason"
        ):

            errors.append(
                build_combination_rule_error(
                    fallback_rule_id,
                    "reason",
                    "reason_required"
                )
            )

        evidence_snippets = rule.get(
            "evidence_snippets",
            []
        )

        if (
            not isinstance(
                evidence_snippets,
                list
            )
            or not evidence_snippets
        ):

            errors.append(
                build_combination_rule_error(
                    fallback_rule_id,
                    "evidence_snippets",
                    "evidence_snippets_required"
                )
            )

    return {
        "valid":
            not errors,
        "normalized_rules":
            normalized_rules,
        "errors":
            errors
    }
