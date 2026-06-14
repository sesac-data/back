from typing import Dict, List


RECOMMENDED_REASON = "사업주 순비용이 가장 낮은 조합입니다."
ALTERNATIVE_REASON = "비교 가능한 대안 조합입니다."


def build_error(
    policy_ids,
    field: str,
    reason: str
) -> Dict:

    return {
        "policy_ids":
            policy_ids,
        "field":
            field,
        "reason":
            reason
    }


def policy_ids_key(
    policy_ids: List[str]
) -> str:

    return "|".join(
        policy_ids
    )


def get_duplicate_policy_id_keys(
    combinations: List[Dict]
) -> List[str]:

    seen_keys = set()
    duplicate_keys = set()

    for combination in combinations:

        policy_ids = combination.get(
            "policy_ids",
            []
        )

        if not policy_ids:
            continue

        key = policy_ids_key(
            policy_ids
        )

        if key in seen_keys:
            duplicate_keys.add(
                key
            )

        seen_keys.add(
            key
        )

    return sorted(
        duplicate_keys
    )


def validate_candidate(
    combination: Dict,
    duplicate_keys: List[str]
) -> List[Dict]:

    errors = []
    policy_ids = combination.get(
        "policy_ids"
    )

    if not policy_ids:

        errors.append(
            build_error(
                policy_ids or [],
                "policy_ids",
                "policy_ids_required"
            )
        )

        return errors

    if policy_ids_key(
        policy_ids
    ) in duplicate_keys:

        errors.append(
            build_error(
                policy_ids,
                "policy_ids",
                "duplicate_policy_ids_combination"
            )
        )

    if combination.get(
        "net_employer_cost"
    ) is None:

        errors.append(
            build_error(
                policy_ids,
                "net_employer_cost",
                "net_employer_cost_required"
            )
        )

    if combination.get(
        "total_subsidy_amount"
    ) is None:

        errors.append(
            build_error(
                policy_ids,
                "total_subsidy_amount",
                "total_subsidy_amount_required"
            )
        )

    return errors


def sort_key(
    combination: Dict
):

    policy_ids = combination.get(
        "policy_ids",
        []
    )

    return (
        combination.get(
            "net_employer_cost"
        ),
        -combination.get(
            "total_subsidy_amount"
        ),
        len(
            policy_ids
        ),
        policy_ids_key(
            policy_ids
        )
    )


def get_tie_breaks(
    selected: Dict,
    candidates: List[Dict]
) -> List[str]:

    tie_breaks = []
    selected_net_cost = selected.get(
        "net_employer_cost"
    )
    net_tied = [
        candidate
        for candidate in candidates
        if candidate.get(
            "net_employer_cost"
        ) == selected_net_cost
    ]

    if len(
        net_tied
    ) <= 1:

        return tie_breaks

    tie_breaks.append(
        "total_subsidy_amount_desc"
    )

    selected_subsidy = selected.get(
        "total_subsidy_amount"
    )
    subsidy_tied = [
        candidate
        for candidate in net_tied
        if candidate.get(
            "total_subsidy_amount"
        ) == selected_subsidy
    ]

    if len(
        subsidy_tied
    ) <= 1:

        return tie_breaks

    tie_breaks.append(
        "policy_count_asc"
    )

    selected_policy_count = len(
        selected.get(
            "policy_ids",
            []
        )
    )
    count_tied = [
        candidate
        for candidate in subsidy_tied
        if len(
            candidate.get(
                "policy_ids",
                []
            )
        ) == selected_policy_count
    ]

    if len(
        count_tied
    ) <= 1:

        return tie_breaks

    tie_breaks.append(
        "policy_ids_lexicographic"
    )

    return tie_breaks


def build_reason(
    base_reason: str,
    tie_breaks: List[str]
) -> str:

    if not tie_breaks:

        return base_reason

    return (
        base_reason
        + " Tie-break 기준: "
        + ", ".join(
            tie_breaks
        )
        + "."
    )


def build_ranked_combination(
    combination: Dict,
    rank: int,
    recommendation_reason: str,
    tie_breaks: List[str]
) -> Dict:

    return {
        "rank":
            rank,
        "policy_ids":
            combination.get(
                "policy_ids",
                []
            ),
        "policy_results":
            combination.get(
                "policy_results",
                []
            ),
        "total_base_amount":
            combination.get(
                "total_base_amount"
            ),
        "total_bonus_amount":
            combination.get(
                "total_bonus_amount"
            ),
        "total_subsidy_amount":
            combination.get(
                "total_subsidy_amount"
            ),
        "applied_cost_items":
            combination.get(
                "applied_cost_items",
                []
            ),
        "total_employer_cost":
            combination.get(
                "total_employer_cost"
            ),
        "net_employer_cost":
            combination.get(
                "net_employer_cost"
            ),
        "calculation_steps":
            combination.get(
                "calculation_steps",
                []
            ) or [],
        "evidence_snippets":
            combination.get(
                "evidence_snippets",
                []
            ) or [],
        "recommendation_reason":
            recommendation_reason,
        "tie_break_applied":
            tie_breaks
    }


def select_optimal_combination(
    cost_calculated_combinations: List[Dict],
    rejected_combinations=None
) -> Dict:

    if rejected_combinations is None:

        rejected_combinations = []

    duplicate_keys = get_duplicate_policy_id_keys(
        cost_calculated_combinations
    )
    errors = []
    valid_candidates = []

    for combination in cost_calculated_combinations:

        candidate_errors = validate_candidate(
            combination,
            duplicate_keys
        )

        if candidate_errors:

            errors.extend(
                candidate_errors
            )
            continue

        valid_candidates.append(
            combination
        )

    if not valid_candidates:

        errors.append(
            build_error(
                [],
                "cost_calculated_combinations",
                "no_recommendation_candidates"
            )
        )

        return {
            "recommended_combination":
                None,
            "alternative_combinations":
                [],
            "rejected_combinations":
                rejected_combinations,
            "errors":
                errors
        }

    ranked_candidates = sorted(
        valid_candidates,
        key=sort_key
    )
    selected = ranked_candidates[0]
    tie_breaks = get_tie_breaks(
        selected,
        ranked_candidates
    )

    recommended_combination = build_ranked_combination(
        selected,
        1,
        build_reason(
            RECOMMENDED_REASON,
            tie_breaks
        ),
        tie_breaks
    )

    alternative_combinations = [
        build_ranked_combination(
            combination,
            index + 2,
            build_reason(
                ALTERNATIVE_REASON,
                get_tie_breaks(
                    combination,
                    ranked_candidates
                )
            ),
            get_tie_breaks(
                combination,
                ranked_candidates
            )
        )
        for index, combination in enumerate(
            ranked_candidates[1:]
        )
    ]

    return {
        "recommended_combination":
            recommended_combination,
        "alternative_combinations":
            alternative_combinations,
        "rejected_combinations":
            rejected_combinations,
        "errors":
            errors
    }
