from itertools import combinations
from typing import Dict, List

from services.mutual_exclusion_detector import (
    detect_mutually_exclusive_conflicts
)
from services.requirement_detector import (
    detect_required_policy_violations
)


APPROVED_STATUS = "approved"
MAX_COMBINATION_CANDIDATES = 12


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


def get_duplicate_policy_ids(
    candidate_policies: List[Dict]
) -> List[str]:

    seen_policy_ids = set()
    duplicate_policy_ids = set()

    for policy in candidate_policies:

        policy_id = get_policy_id(
            policy
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


def normalize_approved_candidates(
    candidate_policies: List[Dict]
) -> List[Dict]:

    approved_policies = [
        policy
        for policy in candidate_policies
        if policy.get(
            "review_status"
        ) == APPROVED_STATUS
    ]

    return sorted(
        approved_policies,
        key=get_policy_id
    )


def build_combination_entry(
    policies: List[Dict]
) -> Dict:

    return {
        "policy_ids":
            [
                get_policy_id(
                    policy
                )
                for policy in policies
            ],
        "policies":
            policies
    }


def build_rejection_reasons(
    policies: List[Dict]
) -> List[Dict]:

    reasons = []

    conflict_result = detect_mutually_exclusive_conflicts(
        policies
    )

    for conflict in conflict_result.get(
        "conflicts",
        []
    ):

        reasons.append({
            "type":
                "mutually_exclusive",
            "details":
                conflict
        })

    requirement_result = detect_required_policy_violations(
        policies
    )

    for violation in requirement_result.get(
        "violations",
        []
    ):

        reasons.append({
            "type":
                "requires",
            "details":
                violation
        })

    return reasons


def generate_valid_policy_combinations(
    candidate_policies: List[Dict]
) -> Dict:

    duplicate_policy_ids = get_duplicate_policy_ids(
        candidate_policies
    )

    if duplicate_policy_ids:

        return {
            "valid_combinations":
                [],
            "rejected_combinations":
                [],
            "errors":
                [
                    build_error(
                        "policy_id",
                        "duplicate_policy_id",
                        {
                            "policy_ids":
                                duplicate_policy_ids
                        }
                    )
                ]
        }

    approved_policies = normalize_approved_candidates(
        candidate_policies
    )

    if len(
        approved_policies
    ) > MAX_COMBINATION_CANDIDATES:

        return {
            "valid_combinations":
                [],
            "rejected_combinations":
                [],
            "errors":
                [
                    build_error(
                        "candidate_policies",
                        "max_combination_candidates_exceeded",
                        {
                            "max":
                                MAX_COMBINATION_CANDIDATES,
                            "actual":
                                len(
                                    approved_policies
                                )
                        }
                    )
                ]
        }

    valid_combinations = []
    rejected_combinations = []

    for combination_size in range(
        1,
        len(
            approved_policies
        ) + 1
    ):

        for policies_tuple in combinations(
            approved_policies,
            combination_size
        ):

            policies = list(
                policies_tuple
            )

            combination_entry = build_combination_entry(
                policies
            )

            reasons = build_rejection_reasons(
                policies
            )

            if reasons:

                rejected_combinations.append({
                    "policy_ids":
                        combination_entry[
                            "policy_ids"
                        ],
                    "reasons":
                        reasons
                })

                continue

            valid_combinations.append(
                combination_entry
            )

    return {
        "valid_combinations":
            valid_combinations,
        "rejected_combinations":
            rejected_combinations,
        "errors":
            []
    }
