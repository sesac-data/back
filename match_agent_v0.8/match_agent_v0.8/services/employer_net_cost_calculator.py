from numbers import Number
from typing import Dict, List


def build_error(
    cost_id,
    field: str,
    reason: str
) -> Dict:

    return {
        "cost_id":
            cost_id,
        "field":
            field,
        "reason":
            reason
    }


def normalize_cost_item(
    cost_item: Dict
) -> Dict:

    return {
        "cost_id":
            cost_item.get(
                "cost_id"
            ),
        "cost_type":
            cost_item.get(
                "cost_type"
            ),
        "description":
            cost_item.get(
                "description"
            ),
        "amount":
            cost_item.get(
                "amount"
            ),
        "applies_to_policy_ids":
            cost_item.get(
                "applies_to_policy_ids",
                []
            ) or []
    }


def validate_employer_cost_items(
    employer_cost_items: List[Dict]
) -> List[Dict]:

    errors = []
    seen_cost_ids = set()

    for index, cost_item in enumerate(
        employer_cost_items
    ):

        cost_id = cost_item.get(
            "cost_id"
        )

        fallback_cost_id = (
            cost_id
            or f"cost[{index}]"
        )

        if not cost_id:

            errors.append(
                build_error(
                    fallback_cost_id,
                    "cost_id",
                    "cost_id_required"
                )
            )

        elif cost_id in seen_cost_ids:

            errors.append(
                build_error(
                    cost_id,
                    "cost_id",
                    "duplicate_cost_id"
                )
            )

        else:

            seen_cost_ids.add(
                cost_id
            )

        amount = cost_item.get(
            "amount"
        )

        if amount is None:

            errors.append(
                build_error(
                    fallback_cost_id,
                    "amount",
                    "amount_required"
                )
            )

            continue

        if (
            not isinstance(
                amount,
                Number
            )
            or isinstance(
                amount,
                bool
            )
        ):

            errors.append(
                build_error(
                    fallback_cost_id,
                    "amount",
                    "amount_must_be_number"
                )
            )

            continue

        if amount < 0:

            errors.append(
                build_error(
                    fallback_cost_id,
                    "amount",
                    "amount_must_not_be_negative"
                )
            )

    return errors


def cost_item_applies_to_combination(
    cost_item: Dict,
    policy_ids: List[str]
) -> bool:

    applies_to_policy_ids = cost_item.get(
        "applies_to_policy_ids",
        []
    )

    if not applies_to_policy_ids:

        return True

    policy_id_set = set(
        policy_ids
    )

    return all(
        policy_id in policy_id_set
        for policy_id in applies_to_policy_ids
    )


def build_cost_calculation_step(
    combination: Dict,
    applied_cost_items: List[Dict],
    total_employer_cost,
    net_employer_cost
) -> Dict:

    return {
        "description":
            "Calculate employer net cost from explicit employer cost items.",
        "formula":
            "net_employer_cost = total_employer_cost - total_subsidy_amount",
        "inputs":
            {
                "policy_ids":
                    combination.get(
                        "policy_ids",
                        []
                    ),
                "total_subsidy_amount":
                    combination.get(
                        "total_subsidy_amount"
                    ),
                "applied_cost_items":
                    applied_cost_items
            },
        "result":
            {
                "total_employer_cost":
                    total_employer_cost,
                "net_employer_cost":
                    net_employer_cost
            }
    }


def calculate_combination_net_cost(
    combination: Dict,
    normalized_cost_items: List[Dict]
) -> Dict:

    policy_ids = combination.get(
        "policy_ids",
        []
    )

    applied_cost_items = [
        cost_item
        for cost_item in normalized_cost_items
        if cost_item_applies_to_combination(
            cost_item,
            policy_ids
        )
    ]

    total_employer_cost = sum(
        cost_item.get(
            "amount"
        )
        for cost_item in applied_cost_items
    )

    total_subsidy_amount = combination.get(
        "total_subsidy_amount"
    )

    net_employer_cost = (
        total_employer_cost
        - total_subsidy_amount
    )

    calculation_steps = (
        combination.get(
            "calculation_steps",
            []
        ) or []
    ) + [
        build_cost_calculation_step(
            combination,
            applied_cost_items,
            total_employer_cost,
            net_employer_cost
        )
    ]

    return {
        "policy_ids":
            policy_ids,
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
            total_subsidy_amount,
        "applied_cost_items":
            applied_cost_items,
        "total_employer_cost":
            total_employer_cost,
        "net_employer_cost":
            net_employer_cost,
        "calculation_steps":
            calculation_steps,
        "evidence_snippets":
            combination.get(
                "evidence_snippets",
                []
            ) or []
    }


def calculate_employer_net_costs(
    summarized_combinations: List[Dict],
    employer_cost_items=None
) -> Dict:

    if employer_cost_items is None:

        employer_cost_items = []

    errors = validate_employer_cost_items(
        employer_cost_items
    )

    if errors:

        return {
            "cost_calculated_combinations":
                [],
            "rejected_combinations":
                [],
            "errors":
                errors
        }

    normalized_cost_items = [
        normalize_cost_item(
            cost_item
        )
        for cost_item in employer_cost_items
    ]

    cost_calculated_combinations = [
        calculate_combination_net_cost(
            combination,
            normalized_cost_items
        )
        for combination in summarized_combinations
    ]

    return {
        "cost_calculated_combinations":
            cost_calculated_combinations,
        "rejected_combinations":
            [],
        "errors":
            []
    }
