from typing import Dict, List


CALCULATED_STATUS = "calculated"


def get_policy_id(
    item: Dict
):

    return (
        item.get(
            "policy_id"
        )
        or item.get(
            "policy_key"
        )
    )


def build_error(
    field: str,
    reason: str,
    details=None
) -> Dict:

    return {
        "field":
            field,
        "reason":
            reason,
        "details":
            details
    }


def get_duplicate_policy_result_ids(
    standardized_policy_results: List[Dict]
) -> List[str]:

    seen_policy_ids = set()
    duplicate_policy_ids = set()

    for result in standardized_policy_results:

        policy_id = get_policy_id(
            result
        )

        if policy_id in seen_policy_ids:

            duplicate_policy_ids.add(
                policy_id
            )

        seen_policy_ids.add(
            policy_id
        )

    return sorted(
        duplicate_policy_ids
    )


def build_policy_result_index(
    standardized_policy_results: List[Dict]
) -> Dict:

    return {
        get_policy_id(
            result
        ):
            result
        for result in standardized_policy_results
    }


def build_policy_result_summary(
    policy_result: Dict
) -> Dict:

    return {
        "policy_id":
            policy_result.get(
                "policy_id"
            ),
        "policy_name":
            policy_result.get(
                "policy_name"
            ),
        "status":
            policy_result.get(
                "status"
            ),
        "base_amount":
            policy_result.get(
                "base_amount"
            ),
        "bonus_amount":
            policy_result.get(
                "bonus_amount"
            ),
        "estimated_total_amount":
            policy_result.get(
                "estimated_total_amount"
            ),
        "calculation_steps":
            policy_result.get(
                "calculation_steps",
                []
            ) or [],
        "evidence_snippets":
            policy_result.get(
                "evidence_snippets",
                []
            ) or []
    }


def append_unique_evidence(
    evidence: List[str],
    snippets: List[str]
):

    for snippet in snippets:

        if snippet not in evidence:

            evidence.append(
                snippet
            )


def build_rejection_reason(
    reason_type: str,
    policy_id: str,
    policy_result=None
) -> Dict:

    details = {
        "policy_id":
            policy_id
    }

    if policy_result is not None:

        details.update({
            "policy_name":
                policy_result.get(
                    "policy_name"
                ),
            "status":
                policy_result.get(
                    "status"
                ),
            "errors":
                policy_result.get(
                    "errors",
                    []
                ) or [],
            "calculation_steps":
                policy_result.get(
                    "calculation_steps",
                    []
                ) or [],
            "evidence_snippets":
                policy_result.get(
                    "evidence_snippets",
                    []
                ) or []
        })

    return {
        "type":
            reason_type,
        "details":
            details
    }


def get_combination_rejection_reasons(
    policy_ids: List[str],
    policy_result_index: Dict
) -> List[Dict]:

    reasons = []

    for policy_id in policy_ids:

        policy_result = policy_result_index.get(
            policy_id
        )

        if policy_result is None:

            reasons.append(
                build_rejection_reason(
                    "policy_result_missing",
                    policy_id
                )
            )

            continue

        status = policy_result.get(
            "status"
        )

        if status == "calculation_error":

            reasons.append(
                build_rejection_reason(
                    "calculation_error",
                    policy_id,
                    policy_result
                )
            )

            continue

        if status == "ineligible":

            reasons.append(
                build_rejection_reason(
                    "ineligible",
                    policy_id,
                    policy_result
                )
            )

            continue

        if status != CALCULATED_STATUS:

            reasons.append(
                build_rejection_reason(
                    "policy_not_calculated",
                    policy_id,
                    policy_result
                )
            )

            continue

        if policy_result.get(
            "estimated_total_amount"
        ) is None:

            reasons.append(
                build_rejection_reason(
                    "estimated_total_amount_missing",
                    policy_id,
                    policy_result
                )
            )

            continue

        if (
            policy_result.get(
                "base_amount"
            ) is None
            or policy_result.get(
                "bonus_amount"
            ) is None
        ):

            reasons.append(
                build_rejection_reason(
                    "amount_component_missing",
                    policy_id,
                    policy_result
                )
            )

    return reasons


def summarize_valid_combination(
    combination: Dict,
    policy_result_index: Dict
) -> Dict:

    policy_ids = combination.get(
        "policy_ids",
        []
    )

    policy_results = []
    total_base_amount = 0
    total_bonus_amount = 0
    total_subsidy_amount = 0
    calculation_steps = []
    evidence_snippets = []

    for policy_id in policy_ids:

        policy_result = policy_result_index[
            policy_id
        ]

        summary = build_policy_result_summary(
            policy_result
        )

        policy_results.append(
            summary
        )

        total_base_amount += policy_result.get(
            "base_amount"
        )
        total_bonus_amount += policy_result.get(
            "bonus_amount"
        )
        total_subsidy_amount += policy_result.get(
            "estimated_total_amount"
        )

        calculation_steps.append({
            "policy_id":
                policy_id,
            "calculation_steps":
                policy_result.get(
                    "calculation_steps",
                    []
                ) or []
        })

        append_unique_evidence(
            evidence_snippets,
            policy_result.get(
                "evidence_snippets",
                []
            ) or []
        )

    return {
        "policy_ids":
            policy_ids,
        "policy_results":
            policy_results,
        "total_base_amount":
            total_base_amount,
        "total_bonus_amount":
            total_bonus_amount,
        "total_subsidy_amount":
            total_subsidy_amount,
        "calculation_steps":
            calculation_steps,
        "evidence_snippets":
            evidence_snippets
    }


def summarize_combination_amounts(
    valid_combinations: List[Dict],
    standardized_policy_results: List[Dict]
) -> Dict:

    duplicate_policy_ids = get_duplicate_policy_result_ids(
        standardized_policy_results
    )

    if duplicate_policy_ids:

        return {
            "summarized_combinations":
                [],
            "rejected_combinations":
                [],
            "errors":
                [
                    build_error(
                        "policy_id",
                        "duplicate_policy_result",
                        {
                            "policy_ids":
                                duplicate_policy_ids
                        }
                    )
                ]
        }

    policy_result_index = build_policy_result_index(
        standardized_policy_results
    )

    summarized_combinations = []
    rejected_combinations = []

    for combination in valid_combinations:

        policy_ids = combination.get(
            "policy_ids",
            []
        )

        reasons = get_combination_rejection_reasons(
            policy_ids,
            policy_result_index
        )

        if reasons:

            rejected_combinations.append({
                "policy_ids":
                    policy_ids,
                "reasons":
                    reasons
            })

            continue

        summarized_combinations.append(
            summarize_valid_combination(
                combination,
                policy_result_index
            )
        )

    return {
        "summarized_combinations":
            summarized_combinations,
        "rejected_combinations":
            rejected_combinations,
        "errors":
            []
    }
