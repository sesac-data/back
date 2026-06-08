from copy import deepcopy
from typing import Dict, Tuple


DEFAULT_DURATION_MONTHS_BY_POLICY_KEY = {
    "childcare_flexible_start_support":
        12,
    "elders_employ_incent":
        24,
    "employ_promo_incent":
        12,
    "flexible_work_incent":
        12,
    "flexible_work_system_support":
        12,
    "parental_leave_reduction_support":
        12,
    "perm_conv_incent":
        12,
    "replacement_workshare_support":
        12,
    "working_hours_reduction_support":
        12,
    "worklife_balance_45_support":
        12,
}


def _safe_number(

    value
) -> int | None:

    if value is None:

        return None

    try:

        return int(
            value
        )

    except Exception:

        return None


def _default_duration_months(

    policy_key: str | None
) -> Tuple[int, str]:

    if (
        policy_key
        and policy_key
        in DEFAULT_DURATION_MONTHS_BY_POLICY_KEY
    ):

        return (
            DEFAULT_DURATION_MONTHS_BY_POLICY_KEY[
                policy_key
            ],
            "policy_default"
        )

    return (
        12,
        "fallback_default"
    )


def normalize_support_amount(

    support_info: Dict,
    policy_key: str | None = None
) -> Tuple[Dict, Dict]:

    normalized = deepcopy(
        support_info or {}
    )

    yearly_amount = _safe_number(
        normalized.get(
            "yearly_max_amount"
        )
    )

    monthly_amount = _safe_number(
        normalized.get(
            "monthly_amount"
        )
    )

    max_duration_months = _safe_number(
        normalized.get(
            "max_duration_months"
        )
    )

    method = "unavailable"

    duration_source = None

    normalized_amount = 0

    if yearly_amount is not None:

        normalized_amount = yearly_amount

        method = "yearly_max_amount"

    elif monthly_amount is not None:

        duration = max_duration_months

        if duration is None:

            duration, duration_source = _default_duration_months(
                policy_key
            )

        else:

            duration_source = "max_duration_months"

        normalized_amount = (
            monthly_amount
            * duration
        )

        method = "monthly_amount_x_duration"

        normalized[
            "normalized_duration_months"
        ] = duration

    normalized[
        "normalized_yearly_amount"
    ] = normalized_amount

    normalized[
        "amount_normalization"
    ] = {
        "method":
            method,
        "duration_source":
            duration_source,
        "policy_key":
            policy_key
    }

    return normalized, {
        "method":
            method,
        "normalized_yearly_amount":
            normalized_amount,
        "duration_source":
            duration_source
    }


def normalize_policy_amounts(

    policy_json: Dict,
    policy_key: str | None = None
) -> Dict:

    normalized_policy = deepcopy(
        policy_json
    )

    logs = []

    for item_index, support_item in enumerate(
        normalized_policy.get(
            "support_items",
            []
        )
    ):

        support_info = support_item.get(
            "support",
            {}
        )

        normalized_support, log = normalize_support_amount(
            support_info,
            policy_key
        )

        support_item[
            "support"
        ] = normalized_support

        logs.append({
            "path":
                f"support_items[{item_index}].support",
            **log
        })

    normalized_policy[
        "amount_normalization_logs"
    ] = logs

    return normalized_policy
