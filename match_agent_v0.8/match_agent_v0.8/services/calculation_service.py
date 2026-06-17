# services/calculation_service.py

from typing import Dict, List

from services.condition_evaluator import (
    MISSING,
    evaluate_conditions_with_groups,
    evaluate_operator_conditions,
    evaluate_policy_conditions,
    get_nested_value
)


APPROVED_STATUS = "approved"
REVIEW_STATUS_FIELD = "review_status"
MONTHLY_FIXED = "monthly_fixed"
PERIOD_TIERED = "period_tiered"
CONDITIONAL_BONUS = "conditional_bonus"
COST_SHARE = "cost_share"

# Explicit, overridable assumption used only when a policy declares a per-wage
# monthly cap but the actual wage is not provided in the input. The result then
# records an "assumed_wage_used" warning step; no amount is silently fabricated.
ASSUMED_DEFAULT_MONTHLY_WAGE = 3_000_000
DEFAULT_WAGE_FIELD = "employee.monthly_wage"

# Per-month exclusion ("해당월 부지급"): the count of non-payable months is a
# provided input. We never infer which/how many months are excluded from
# attendance data we do not have; a missing input means 0 excluded months.
DEFAULT_EXCLUDED_MONTHS_FIELD = "leave_event.excluded_months"
STANDARD_CALCULATION_RESULT_FIELDS = [
    "policy_id",
    "policy_name",
    "review_status",
    "eligible",
    "status",
    "calculation_type",
    "base_amount",
    "bonus_amount",
    "estimated_total_amount",
    "calculation_steps",
    "passed_conditions",
    "failed_conditions",
    "applied_bonuses",
    "skipped_bonuses",
    "evidence_snippets",
    "errors"
]


def calculate_monthly_fixed_amount(
    monthly_amount: int,
    eligible_months: int
) -> int:

    return monthly_amount * eligible_months


def collect_evidence_snippets(
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


def get_policy_review_status(
    policy_json: Dict
):

    return policy_json.get(
        REVIEW_STATUS_FIELD
    )


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


def get_support_calculation_type(
    policy_json: Dict
):

    support_item = get_first_support_item(
        policy_json
    )

    support = support_item.get(
        "support",
        {}
    )

    if support_item.get(
        "conditional_bonuses"
    ):

        return CONDITIONAL_BONUS

    return support.get(
        "calculation_type",
        support_item.get(
            "support_type"
        )
    )


def collect_calculation_errors(
    result: Dict
) -> List[Dict]:

    if result.get(
        "status"
    ) != "calculation_error":

        return result.get(
            "errors",
            []
        ) or []

    errors = result.get(
        "errors",
        []
    ) or []

    if errors:

        return errors

    collected_errors = []

    for step in result.get(
        "calculation_steps",
        []
    ):

        reason = step.get(
            "reason"
        )

        if reason:

            collected_errors.append({
                "reason":
                    reason,
                "step":
                    step.get(
                        "step"
                    )
            })

    if collected_errors:

        return collected_errors

    return [
        {
            "reason":
                "calculation_error",
            "step":
                None
        }
    ]


def normalize_policy_calculation_result(
    policy_json: Dict,
    result: Dict
) -> Dict:

    status = result.get(
        "status"
    )

    raw_estimated_total_amount = result.get(
        "estimated_total_amount"
    )

    if "base_amount" in result:

        base_amount = result.get(
            "base_amount"
        )

    elif status == "calculated":

        base_amount = raw_estimated_total_amount

    else:

        base_amount = None

    if (
        status == "calculated"
        or "base_amount" in result
    ):

        estimated_total_amount = raw_estimated_total_amount

    else:

        estimated_total_amount = None

    normalized = {
        "policy_id":
            result.get(
                "policy_id",
                get_policy_id(
                    policy_json
                )
            ),

        "policy_name":
            result.get(
                "policy_name",
                policy_json.get(
                    "policy_name"
                )
            ),

        "review_status":
            result.get(
                "review_status",
                get_policy_review_status(
                    policy_json
                )
            ),

        "eligible":
            result.get(
                "eligible",
                False
            ),

        "status":
            status,

        "calculation_type":
            result.get(
                "calculation_type",
                get_support_calculation_type(
                    policy_json
                )
            ),

        "base_amount":
            base_amount,

        "bonus_amount":
            result.get(
                "bonus_amount",
                0
            ),

        "estimated_total_amount":
            estimated_total_amount,

        "calculation_steps":
            result.get(
                "calculation_steps",
                []
            ) or [],

        "passed_conditions":
            result.get(
                "passed_conditions",
                []
            ) or [],

        "failed_conditions":
            result.get(
                "failed_conditions",
                []
            ) or [],

        "applied_bonuses":
            result.get(
                "applied_bonuses",
                []
            ) or [],

        "skipped_bonuses":
            result.get(
                "skipped_bonuses",
                []
            ) or [],

        "evidence_snippets":
            result.get(
                "evidence_snippets",
                []
            ) or [],

        "errors":
            collect_calculation_errors(
                result
            )
    }

    return normalized


def validate_standard_calculation_result(
    result: Dict
) -> List[str]:

    missing_fields = []

    for field in STANDARD_CALCULATION_RESULT_FIELDS:

        if field not in result:

            missing_fields.append(
                field
            )

    return missing_fields


def build_calculation_result(
    policy_json: Dict,
    calculation_type: str,
    requested_months: int
) -> Dict:

    policy_id = (
        policy_json.get(
            "policy_id"
        )
        or policy_json.get(
            "policy_key"
        )
    )

    return {
        "policy_id":
            policy_id,

        "policy_name":
            policy_json.get(
                "policy_name"
            ),

        "eligible":
            False,

        "calculation_type":
            calculation_type,

        "requested_months":
            requested_months,

        "eligible_months":
            0,

        "estimated_total_amount":
            0,

        "calculation_steps":
            [],

        "evidence_snippets":
            []
    }


def get_first_support_item(
    policy_json: Dict
) -> Dict:

    support_items = policy_json.get(
        "support_items",
        []
    )

    if not support_items:

        return {}

    return support_items[0]


def append_unique_evidence(
    evidence: List[str],
    snippets: List[str]
):

    for snippet in snippets:

        if snippet not in evidence:

            evidence.append(
                snippet
            )


def collect_condition_evidence(
    condition_result: Dict
) -> List[str]:

    evidence = []

    for condition_result_item in (
        condition_result.get(
            "passed_conditions",
            []
        )
        + condition_result.get(
            "failed_conditions",
            []
        )
    ):

        append_unique_evidence(
            evidence,
            condition_result_item.get(
                "evidence_snippets",
                []
            )
        )

    # Condition groups (OR/AND) carry their own evidence and member evidence.
    for group in condition_result.get(
        "groups",
        []
    ):

        append_unique_evidence(
            evidence,
            group.get(
                "evidence_snippets",
                []
            )
        )

        for member in group.get(
            "member_results",
            []
        ):

            append_unique_evidence(
                evidence,
                member.get(
                    "evidence_snippets",
                    []
                )
            )

    return evidence


def build_policy_not_approved_result(
    base_result: Dict,
    review_status
) -> Dict:

    base_result.update({
        "status":
            "needs_review",
        "calculation_steps":
            [
                {
                    "step":
                        "review_status_gate",
                    "input":
                        review_status,
                    "result":
                        "skipped",
                    "reason":
                        "policy_not_approved"
                }
            ]
    })

    return base_result


def build_ineligible_result(
    base_result: Dict,
    condition_result: Dict,
    conditions: List[Dict],
    skipped_step: str
) -> Dict:

    base_result.update({
        "status":
            "ineligible",
        "passed_conditions":
            condition_result.get(
                "passed_conditions",
                []
            ),
        "failed_conditions":
            condition_result.get(
                "failed_conditions",
                []
            ),
        "calculation_steps":
            [
                {
                    "step":
                        "condition_evaluation",
                    "input":
                        {
                            "conditions":
                                conditions
                        },
                    "result":
                        "failed",
                    "reason":
                        "one_or_more_conditions_failed"
                },
                {
                    "step":
                        skipped_step,
                    "result":
                        "skipped",
                    "reason":
                        "policy_ineligible"
                }
            ]
    })

    return base_result


def prepare_approved_calculation(
    policy_json: Dict,
    rule_input: Dict,
    calculation_type: str,
    requested_months: int,
    skipped_step: str
):

    base_result = build_calculation_result(
        policy_json,
        calculation_type,
        requested_months
    )

    review_status = get_policy_review_status(
        policy_json
    )

    if review_status != APPROVED_STATUS:

        return (
            build_policy_not_approved_result(
                base_result,
                review_status
            ),
            None,
            None,
            None
        )

    support_item = get_first_support_item(
        policy_json
    )

    support = support_item.get(
        "support",
        {}
    )

    evidence = collect_evidence_snippets(
        policy_json,
        support_item,
        support
    )

    conditions = support_item.get(
        "conditions",
        []
    )

    condition_result = evaluate_conditions_with_groups(
        rule_input,
        conditions
    )

    append_unique_evidence(
        evidence,
        collect_condition_evidence(
            condition_result
        )
    )

    base_result[
        "evidence_snippets"
    ] = evidence

    if not condition_result.get(
        "eligible"
    ):

        return (
            build_ineligible_result(
                base_result,
                condition_result,
                conditions,
                skipped_step
            ),
            None,
            None,
            None
        )

    base_result.update({
        "eligible":
            True,
        "passed_conditions":
            condition_result.get(
                "passed_conditions",
                []
            ),
        "failed_conditions":
            []
    })

    return (
        None,
        base_result,
        support_item,
        support
    )

# ─────────────────────────────────────
# 연 지원금 자동 계산
# ─────────────────────────────────────
def calculate_yearly_amount(

    support_info: Dict

):

    normalized_yearly_amount = support_info.get(
        "normalized_yearly_amount"
    )

    if normalized_yearly_amount is not None:

        return normalized_yearly_amount

    yearly_amount = support_info.get(
        "yearly_max_amount"
    )

    monthly_amount = support_info.get(
        "monthly_amount"
    )

    max_duration_months = support_info.get(
        "max_duration_months"
    )

    # ─────────────────────────
    # 이미 연 지원금 존재
    # ─────────────────────────
    if yearly_amount is not None:

        return yearly_amount

    # ─────────────────────────
    # 월 지원금 기반 계산
    # ─────────────────────────
    if (
        monthly_amount is not None
        and max_duration_months is not None
    ):

        return calculate_monthly_fixed_amount(
            monthly_amount
            ,
            max_duration_months
        )

    # ─────────────────────────
    # 계산 불가
    # ─────────────────────────
    return 0


def apply_monthly_wage_cap(
    monthly_amount,
    support: Dict,
    rule_input: Dict,
    tier_index=None,
):
    """Cap a per-month amount at wage * monthly_cap_ratio.

    Returns (effective_monthly_amount, cap_step or None). The cap is applied only
    when the support declares a numeric monthly_cap_ratio; otherwise this is a
    no-op so existing policies are unchanged. When the wage input is missing, an
    explicit assumed wage is used and the step reason is "assumed_wage_used".
    """

    monthly_cap_ratio = support.get(
        "monthly_cap_ratio"
    )

    if not _is_number(monthly_cap_ratio):

        return monthly_amount, None

    cap_field = support.get(
        "cap_field",
        DEFAULT_WAGE_FIELD
    )

    wage = get_nested_value(
        rule_input,
        cap_field
    )

    if wage is MISSING or not _is_number(wage):

        wage_used = ASSUMED_DEFAULT_MONTHLY_WAGE
        assumed_wage = True

    else:

        wage_used = wage
        assumed_wage = False

    cap_amount = int(
        round(
            wage_used
            * monthly_cap_ratio
        )
    )

    if not _is_number(monthly_amount):

        effective_monthly_amount = monthly_amount

    else:

        effective_monthly_amount = min(
            monthly_amount,
            cap_amount
        )

    if assumed_wage:
        reason = "assumed_wage_used"
    elif (
        _is_number(monthly_amount)
        and monthly_amount <= cap_amount
    ):
        reason = "wage_cap_not_binding"
    else:
        reason = "wage_cap_applied"

    cap_step = {
        "step":
            "monthly_wage_cap",
        "input":
            {
                "policy_monthly_amount":
                    monthly_amount,
                "monthly_cap_ratio":
                    monthly_cap_ratio,
                "cap_field":
                    cap_field,
                "wage_used":
                    wage_used,
                "assumed_wage":
                    assumed_wage,
                "cap_amount":
                    cap_amount,
            },
        "result":
            effective_monthly_amount,
        "reason":
            reason,
    }

    if tier_index is not None:

        cap_step[
            "tier_index"
        ] = tier_index

    return effective_monthly_amount, cap_step


def apply_monthly_exclusion(
    eligible_months,
    support: Dict,
    rule_input: Dict,
):
    """Reduce eligible_months by the provided count of non-payable months.

    Returns (adjusted_eligible_months, exclusion_step or None). Active only when
    the support declares a truthy monthly_exclusion marker. The excluded-month
    count is read from input (excluded_months_field); a missing/invalid value
    means 0 excluded (no reduction) and is recorded as "no_exclusion_data" so
    reviewers can see no attendance data was supplied. Nothing is inferred.
    """

    if not support.get("monthly_exclusion"):

        return eligible_months, None

    excluded_field = support.get(
        "excluded_months_field",
        DEFAULT_EXCLUDED_MONTHS_FIELD
    )

    raw_excluded = get_nested_value(
        rule_input,
        excluded_field
    )

    if (
        raw_excluded is MISSING
        or not isinstance(raw_excluded, int)
        or isinstance(raw_excluded, bool)
        or raw_excluded < 0
    ):

        excluded_months = 0
        reason = "no_exclusion_data"

    else:

        excluded_months = raw_excluded
        reason = "monthly_exclusion_applied"

    adjusted_eligible_months = max(
        0,
        eligible_months - excluded_months
    )

    exclusion_step = {
        "step":
            "monthly_exclusion",
        "input":
            {
                "eligible_months":
                    eligible_months,
                "excluded_months_field":
                    excluded_field,
                "excluded_months":
                    excluded_months,
            },
        "result":
            adjusted_eligible_months,
        "reason":
            reason,
    }

    return adjusted_eligible_months, exclusion_step


def calculate_monthly_fixed_policy_support(
    policy_json: Dict,
    rule_input: Dict,
    requested_months: int
) -> Dict:

    skipped_result, base_result, support_item, support = (
        prepare_approved_calculation(
            policy_json,
            rule_input,
            MONTHLY_FIXED,
            requested_months,
            "monthly_fixed_calculation"
        )
    )

    if skipped_result is not None:

        skipped_result[
            "monthly_amount"
        ] = None

        return skipped_result

    monthly_amount = support.get(
        "monthly_amount"
    )

    conditions = support_item.get(
        "conditions",
        []
    )

    max_months = support.get(
        "max_months",
        support.get(
            "max_duration_months"
        )
    )

    base_result.update({
        "eligible":
            True,
        "monthly_amount":
            monthly_amount,
    })

    if monthly_amount is None:

        base_result.update({
            "status":
                "calculation_error",
            "eligible":
                False,
            "calculation_steps":
                [
                    {
                        "step":
                            "condition_evaluation",
                        "result":
                            "passed"
                    },
                    {
                        "step":
                            "monthly_amount_validation",
                        "input":
                            monthly_amount,
                        "result":
                            "failed",
                        "reason":
                            "monthly_amount_missing"
                    }
                ]
        })

        return base_result

    if max_months is None:

        eligible_months = requested_months
        duration_reason = "no_policy_max_months_defined"

    else:

        eligible_months = min(
            requested_months,
            max_months
        )
        duration_reason = "policy_max_months_applied"

    adjusted_eligible_months, exclusion_step = apply_monthly_exclusion(
        eligible_months,
        support,
        rule_input,
    )

    effective_monthly_amount, cap_step = apply_monthly_wage_cap(
        monthly_amount,
        support,
        rule_input,
    )

    estimated_total_amount = calculate_monthly_fixed_amount(
        effective_monthly_amount,
        adjusted_eligible_months
    )

    calculation_steps = [
        {
            "step":
                "condition_evaluation",
            "input":
                {
                    "conditions":
                        conditions
                },
            "result":
                "passed"
        },
        {
            "step":
                "eligible_months",
            "input":
                {
                    "requested_months":
                        requested_months,
                    "max_months":
                        max_months
                },
            "result":
                eligible_months,
            "reason":
                duration_reason
        },
    ]

    if exclusion_step is not None:

        calculation_steps.append(
            exclusion_step
        )

    if cap_step is not None:

        calculation_steps.append(
            cap_step
        )

    calculation_steps.append(
        {
            "step":
                "monthly_fixed_calculation",
            "input":
                {
                    "monthly_amount":
                        effective_monthly_amount,
                    "eligible_months":
                        adjusted_eligible_months
                },
            "result":
                estimated_total_amount
        }
    )

    base_result.update({
        "status":
            "calculated",
        "eligible_months":
            adjusted_eligible_months,
        "estimated_total_amount":
            estimated_total_amount,
        "calculation_steps":
            calculation_steps
    })

    return base_result


def build_tier_error_result(
    base_result: Dict,
    reason: str,
    tier=None
) -> Dict:

    step = {
        "step":
            "period_tier_validation",
        "result":
            "failed",
        "reason":
            reason
    }

    if tier is not None:

        step[
            "input"
        ] = tier

    base_result.update({
        "status":
            "calculation_error",
        "eligible":
            False,
        "eligible_months":
            0,
        "estimated_total_amount":
            0,
        "calculation_steps":
            [
                {
                    "step":
                        "condition_evaluation",
                    "result":
                        "passed"
                },
                step
            ]
    })

    return base_result


def validate_period_tiers(
    tiers: List[Dict]
):

    if not tiers:

        return (
            False,
            "tiers_missing",
            None
        )

    sorted_tiers = sorted(
        tiers,
        key=lambda tier: tier.get(
            "start_month",
            0
        )
    )

    previous_end_month = 0

    for index, tier in enumerate(
        sorted_tiers
    ):

        start_month = tier.get(
            "start_month"
        )

        end_month = tier.get(
            "end_month"
        )

        monthly_amount = tier.get(
            "monthly_amount"
        )

        if monthly_amount is None:

            return (
                False,
                "tier_monthly_amount_missing",
                tier
            )

        if (
            start_month is None
            or end_month is None
        ):

            return (
                False,
                "tier_month_range_missing",
                tier
            )

        if start_month > end_month:

            return (
                False,
                "tier_start_after_end",
                tier
            )

        if (
            index == 0
            and start_month != 1
        ):

            return (
                False,
                "tier_gap",
                tier
            )

        if start_month <= previous_end_month:

            return (
                False,
                "tier_overlap",
                tier
            )

        if start_month > previous_end_month + 1:

            return (
                False,
                "tier_gap",
                tier
            )

        previous_end_month = end_month

    return (
        True,
        None,
        sorted_tiers
    )


def calculate_period_tiered_policy_support(
    policy_json: Dict,
    rule_input: Dict,
    requested_months: int
) -> Dict:

    skipped_result, base_result, _, support = (
        prepare_approved_calculation(
            policy_json,
            rule_input,
            PERIOD_TIERED,
            requested_months,
            "period_tiered_calculation"
        )
    )

    if skipped_result is not None:

        return skipped_result

    tiers = support.get(
        "tiers",
        []
    )

    valid, reason, tier_result = validate_period_tiers(
        tiers
    )

    if not valid:

        return build_tier_error_result(
            base_result,
            reason,
            tier_result
        )

    sorted_tiers = tier_result
    calculation_steps = []
    estimated_total_amount = 0
    eligible_months = 0

    for tier_index, tier in enumerate(
        sorted_tiers
    ):

        start_month = tier.get(
            "start_month"
        )

        end_month = tier.get(
            "end_month"
        )

        if requested_months < start_month:

            continue

        applied_months = (
            min(
                requested_months,
                end_month
            )
            - start_month
            + 1
        )

        monthly_amount = tier.get(
            "monthly_amount"
        )

        effective_monthly_amount, cap_step = apply_monthly_wage_cap(
            monthly_amount,
            support,
            rule_input,
            tier_index=tier_index,
        )

        tier_amount = calculate_monthly_fixed_amount(
            effective_monthly_amount,
            applied_months
        )

        tier_evidence = tier.get(
            "evidence_snippets",
            []
        )

        append_unique_evidence(
            base_result[
                "evidence_snippets"
            ],
            tier_evidence
        )

        eligible_months += applied_months
        estimated_total_amount += tier_amount

        if cap_step is not None:

            calculation_steps.append(
                cap_step
            )

        calculation_steps.append({
            "tier_index":
                tier_index,
            "start_month":
                start_month,
            "end_month":
                end_month,
            "applied_months":
                applied_months,
            "monthly_amount":
                effective_monthly_amount,
            "result":
                tier_amount,
            "evidence_snippets":
                tier_evidence
        })

    base_result.update({
        "status":
            "calculated",
        "eligible":
            True,
        "eligible_months":
            eligible_months,
        "estimated_total_amount":
            estimated_total_amount,
        "calculation_steps":
            calculation_steps
    })

    return base_result


def _cost_share_error(
    base_result: Dict,
    reason: str,
    failed_input,
) -> Dict:

    base_result.update({
        "status":
            "calculation_error",
        "eligible":
            False,
        "estimated_total_amount":
            None,
        "calculation_steps":
            [
                {
                    "step":
                        "condition_evaluation",
                    "result":
                        "passed"
                },
                {
                    "step":
                        "cost_share_validation",
                    "input":
                        failed_input,
                    "result":
                        "failed",
                    "reason":
                        reason
                }
            ]
    })

    return base_result


def calculate_cost_share_policy_support(
    policy_json: Dict,
    rule_input: Dict,
    requested_months: int = 0
) -> Dict:
    """Cost-share support: min(actual_cost * support_ratio, max_support_amount).

    support_ratio and max_support_amount are source-backed policy values; the
    actual cost is a provided input (cost_field). No cost is inferred.
    """

    skipped_result, base_result, support_item, support = (
        prepare_approved_calculation(
            policy_json,
            rule_input,
            COST_SHARE,
            requested_months,
            "cost_share_calculation"
        )
    )

    if skipped_result is not None:

        skipped_result[
            "estimated_total_amount"
        ] = None

        return skipped_result

    support_ratio = support.get(
        "support_ratio"
    )
    max_support_amount = support.get(
        "max_support_amount"
    )
    cost_field = support.get(
        "cost_field",
        "company.investment_cost"
    )

    base_result.update({
        "eligible":
            True,
        "support_ratio":
            support_ratio,
        "max_support_amount":
            max_support_amount,
    })

    if not _is_number(support_ratio):

        return _cost_share_error(
            base_result,
            "support_ratio_invalid",
            support_ratio,
        )

    actual_cost = get_nested_value(
        rule_input,
        cost_field
    )

    if actual_cost is MISSING or not _is_number(actual_cost):

        return _cost_share_error(
            base_result,
            "cost_input_missing",
            {
                "cost_field":
                    cost_field,
                "actual_cost":
                    None
                    if actual_cost is MISSING
                    else actual_cost,
            },
        )

    raw_support_amount = actual_cost * support_ratio

    if _is_number(max_support_amount):

        capped_amount = min(
            raw_support_amount,
            max_support_amount
        )
        cap_applied = capped_amount < raw_support_amount

    else:

        capped_amount = raw_support_amount
        cap_applied = False

    estimated_total_amount = int(
        round(
            capped_amount
        )
    )

    base_result.update({
        "status":
            "calculated",
        "actual_cost":
            actual_cost,
        "estimated_total_amount":
            estimated_total_amount,
        "calculation_steps":
            [
                {
                    "step":
                        "condition_evaluation",
                    "input":
                        {
                            "conditions":
                                support_item.get(
                                    "conditions",
                                    []
                                )
                        },
                    "result":
                        "passed"
                },
                {
                    "step":
                        "cost_share_calculation",
                    "input":
                        {
                            "actual_cost":
                                actual_cost,
                            "support_ratio":
                                support_ratio,
                            "max_support_amount":
                                max_support_amount
                        },
                    "result":
                        estimated_total_amount,
                    "reason":
                        "max_support_amount_applied"
                        if cap_applied
                        else "support_ratio_applied"
                }
            ]
    })

    return base_result


def _is_number(
    value
) -> bool:

    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
    )


def calculate_base_policy_support(
    policy_json: Dict,
    rule_input: Dict,
    requested_months: int
) -> Dict:

    support_item = get_first_support_item(
        policy_json
    )

    support = support_item.get(
        "support",
        {}
    )

    calculation_type = support.get(
        "calculation_type",
        support_item.get(
            "support_type"
        )
    )

    if calculation_type == MONTHLY_FIXED:

        return calculate_monthly_fixed_policy_support(
            policy_json,
            rule_input,
            requested_months
        )

    if calculation_type == PERIOD_TIERED:

        return calculate_period_tiered_policy_support(
            policy_json,
            rule_input,
            requested_months
        )

    if calculation_type == COST_SHARE:

        return calculate_cost_share_policy_support(
            policy_json,
            rule_input,
            requested_months
        )

    return {
        "policy_id":
            policy_json.get(
                "policy_id"
            )
            or policy_json.get(
                "policy_key"
            ),
        "policy_name":
            policy_json.get(
                "policy_name"
            ),
        "eligible":
            False,
        "status":
            "calculation_error",
        "calculation_type":
            calculation_type,
        "requested_months":
            requested_months,
        "eligible_months":
            0,
        "estimated_total_amount":
            0,
        "calculation_steps":
            [
                {
                    "step":
                        "base_calculation_type_validation",
                    "input":
                        calculation_type,
                    "result":
                        "failed",
                    "reason":
                        "unsupported_base_calculation_type"
                }
            ],
        "evidence_snippets":
            collect_evidence_snippets(
                policy_json,
                support_item,
                support
            )
    }


def build_bonus_result_shell(
    policy_json: Dict,
    requested_months: int
) -> Dict:

    return {
        "policy_id":
            policy_json.get(
                "policy_id"
            )
            or policy_json.get(
                "policy_key"
            ),
        "policy_name":
            policy_json.get(
                "policy_name"
            ),
        "review_status":
            get_policy_review_status(
                policy_json
            ),
        "eligible":
            False,
        "status":
            "needs_review",
        "base_amount":
            0,
        "bonus_amount":
            0,
        "estimated_total_amount":
            0,
        "applied_bonuses":
            [],
        "skipped_bonuses":
            [],
        "calculation_steps":
            [],
        "evidence_snippets":
            collect_evidence_snippets(
                policy_json,
                get_first_support_item(
                    policy_json
                )
            ),
        "requested_months":
            requested_months
    }


def get_bonus_eligible_months(
    requested_months: int,
    bonus: Dict
) -> int:

    max_months = bonus.get(
        "max_months",
        bonus.get(
            "max_duration_months"
        )
    )

    if max_months is None:

        return requested_months

    return min(
        requested_months,
        max_months
    )


def calculate_conditional_bonus_policy_support(
    policy_json: Dict,
    rule_input: Dict,
    requested_months: int
) -> Dict:

    result = build_bonus_result_shell(
        policy_json,
        requested_months
    )

    if get_policy_review_status(
        policy_json
    ) != APPROVED_STATUS:

        result[
            "calculation_steps"
        ] = [
            {
                "step":
                    "review_status_gate",
                "input":
                    get_policy_review_status(
                        policy_json
                    ),
                "result":
                    "skipped",
                "reason":
                    "policy_not_approved"
            }
        ]

        return result

    base_result = calculate_base_policy_support(
        policy_json,
        rule_input,
        requested_months
    )

    append_unique_evidence(
        result[
            "evidence_snippets"
        ],
        base_result.get(
            "evidence_snippets",
            []
        )
    )

    result[
        "calculation_steps"
    ].append({
        "step":
            "base_support_calculation",
        "calculation_type":
            base_result.get(
                "calculation_type"
            ),
        "status":
            base_result.get(
                "status"
            ),
        "result":
            base_result.get(
                "estimated_total_amount",
                0
            ),
        "calculation_steps":
            base_result.get(
                "calculation_steps",
                []
            ),
        "evidence_snippets":
            base_result.get(
                "evidence_snippets",
                []
            )
    })

    if base_result.get(
        "status"
    ) != "calculated":

        result.update({
            "eligible":
                False,
            "status":
                base_result.get(
                    "status"
                ),
            "base_amount":
                0,
            "bonus_amount":
                0,
            "estimated_total_amount":
                0
        })

        result[
            "calculation_steps"
        ].append({
            "step":
                "conditional_bonus_calculation",
            "result":
                "skipped",
            "reason":
                "base_policy_not_calculated"
        })

        return result

    result[
        "base_amount"
    ] = base_result.get(
        "estimated_total_amount",
        0
    )

    support_item = get_first_support_item(
        policy_json
    )

    bonuses = support_item.get(
        "conditional_bonuses",
        []
    )

    bonus_amount = 0

    for bonus in bonuses:

        benefit_id = bonus.get(
            "benefit_id"
        )

        bonus_evidence = collect_evidence_snippets(
            bonus
        )

        condition_result = evaluate_conditions_with_groups(
            rule_input,
            bonus.get(
                "conditions",
                []
            )
        )

        append_unique_evidence(
            bonus_evidence,
            collect_condition_evidence(
                condition_result
            )
        )

        append_unique_evidence(
            result[
                "evidence_snippets"
            ],
            bonus_evidence
        )

        if not condition_result.get(
            "eligible"
        ):

            skipped_bonus = {
                "benefit_id":
                    benefit_id,
                "reason":
                    "bonus_conditions_not_met",
                "failed_conditions":
                    condition_result.get(
                        "failed_conditions",
                        []
                    ),
                "evidence_snippets":
                    bonus_evidence
            }

            result[
                "skipped_bonuses"
            ].append(
                skipped_bonus
            )

            result[
                "calculation_steps"
            ].append({
                "step":
                    "conditional_bonus",
                "benefit_id":
                    benefit_id,
                "result":
                    "skipped",
                "reason":
                    "bonus_conditions_not_met",
                "failed_conditions":
                    condition_result.get(
                        "failed_conditions",
                        []
                    ),
                "evidence_snippets":
                    bonus_evidence
            })

            continue

        calculation_type = bonus.get(
            "calculation_type"
        )

        if calculation_type != MONTHLY_FIXED:

            result.update({
                "eligible":
                    False,
                "status":
                    "calculation_error"
            })

            result[
                "calculation_steps"
            ].append({
                "step":
                    "conditional_bonus",
                "benefit_id":
                    benefit_id,
                "result":
                    "failed",
                "reason":
                    "unsupported_bonus_calculation_type",
                "evidence_snippets":
                    bonus_evidence
            })

            return result

        monthly_amount = bonus.get(
            "monthly_amount"
        )

        if monthly_amount is None:

            result.update({
                "eligible":
                    False,
                "status":
                    "calculation_error",
                "bonus_amount":
                    bonus_amount,
                "estimated_total_amount":
                    result[
                        "base_amount"
                    ] + bonus_amount
            })

            result[
                "calculation_steps"
            ].append({
                "step":
                    "conditional_bonus",
                "benefit_id":
                    benefit_id,
                "result":
                    "failed",
                "reason":
                    "bonus_monthly_amount_missing",
                "evidence_snippets":
                    bonus_evidence
            })

            return result

        eligible_months = get_bonus_eligible_months(
            requested_months,
            bonus
        )

        amount = calculate_monthly_fixed_amount(
            monthly_amount,
            eligible_months
        )

        applied_bonus = {
            "benefit_id":
                benefit_id,
            "calculation_type":
                calculation_type,
            "bonus_type":
                bonus.get(
                    "bonus_type"
                ),
            "requested_months":
                requested_months,
            "eligible_months":
                eligible_months,
            "monthly_amount":
                monthly_amount,
            "result":
                amount,
            "evidence_snippets":
                bonus_evidence
        }

        result[
            "applied_bonuses"
        ].append(
            applied_bonus
        )

        result[
            "calculation_steps"
        ].append({
            "step":
                "conditional_bonus",
            **applied_bonus
        })

        bonus_amount += amount

    result.update({
        "eligible":
            True,
        "status":
            "calculated",
        "bonus_amount":
            bonus_amount,
        "estimated_total_amount":
            result[
                "base_amount"
            ] + bonus_amount
    })

    return result


# ─────────────────────────────────────
# support item 계산
# ─────────────────────────────────────
def evaluate_support_item(

    company_data: Dict,
    employee_data: Dict,
    support_item: Dict

):

    conditions = support_item.get(
        "conditions",
        []
    )

    # 조건 평가
    is_eligible = (
        evaluate_policy_conditions(

            company_data,
            employee_data,
            conditions
        )
    )

    # 조건 미충족
    if not is_eligible:

        return None

    support_info = support_item.get(
        "support",
        {}
    )

    yearly_amount = (
        calculate_yearly_amount(
            support_info
        )
    )

    monthly_amount = support_info.get(
        "monthly_amount",
        0
    ) or 0

    max_duration_months = (
        support_info.get(
            "max_duration_months",
            None
        )
    )

    normalized_duration_months = (
        support_info.get(
            "normalized_duration_months",
            max_duration_months
        )
    )

    return {

        "policy_name":
            support_item.get(
                "support_type"
            ),

        "eligible":
            True,

        "yearly_amount":
            yearly_amount,

        "monthly_amount":
            monthly_amount,

        "max_duration_months":
            max_duration_months,

        "normalized_duration_months":
            normalized_duration_months,

        "amount_normalization":
            support_info.get(
                "amount_normalization",
                {}
            ),

        "support_calculation_notes":
            support_item.get(
                "support_calculation_notes",
                []
            ),

        "application_process":
            support_item.get(
                "application_process",
                []
            ),

        "required_systems":
            support_item.get(
                "required_systems",
                []
            ),

        "required_documents":
            support_item.get(
                "required_documents",
                []
            ),

        "duplicate_allowed":
            support_item.get(
                "duplicate_allowed",
                []
            ),

        "important_conditions":
            support_item.get(
                "important_conditions",
                []
            ),

        "target_conditions":
            support_item.get(
                "target_conditions",
                []
            )
    }


# ─────────────────────────────────────
# policy 전체 계산
# ─────────────────────────────────────
def calculate_policy_support(

    company_data: Dict,
    employee_data: Dict,
    policy_json: Dict

) -> List[Dict]:

    results = []

    support_items = policy_json.get(
        "support_items",
        []
    )

    for support_item in support_items:

        result = evaluate_support_item(

            company_data,
            employee_data,
            support_item
        )

        if result:

            results.append(result)

    return results


# ─────────────────────────────────────
# 여러 policy 계산
# ─────────────────────────────────────
def calculate_all_policy_supports(

    company_data: Dict,
    employee_data: Dict,
    policy_json_list: List[Dict]

) -> List[Dict]:

    all_results = []

    for policy_json in policy_json_list:

        policy_results = (
            calculate_policy_support(

                company_data,
                employee_data,
                policy_json
            )
        )

        all_results.extend(
            policy_results
        )

    return all_results


# ─────────────────────────────────────
# 가장 큰 지원금 선택
# ─────────────────────────────────────
def find_best_support(

    support_results: List[Dict]

):

    if not support_results:

        return None

    sorted_results = sorted(

        support_results,

        key=lambda x: (
            x.get(
                "yearly_amount"
            ) or 0
        ),

        reverse=True
    )

    return sorted_results[0]


# ─────────────────────────────────────
# 직원별 계산
# ─────────────────────────────────────
def calculate_employee_supports(

    company_data: Dict,
    employees: List[Dict],
    policy_json_list: List[Dict]

):

    employee_results = []

    for employee in employees:

        support_results = (
            calculate_all_policy_supports(

                company_data,
                employee,
                policy_json_list
            )
        )

        best_support = (
            find_best_support(
                support_results
            )
        )

        total_amount = (
            calculate_total_support_amount(
                support_results
            )
        )

        employee_results.append({

            "employee_name":
                employee.get(
                    "name"
                ),

            "employee_data":
                employee,

            "available_supports":
                support_results,

            "best_support":
                best_support,

            "total_support_amount":
                total_amount
        })

    return employee_results


# ─────────────────────────────────────
# 총 지원금 계산
# ─────────────────────────────────────
def calculate_total_support_amount(

    support_results: List[Dict]

) -> int:

    total = 0

    for result in support_results:

        total += (
            result.get(
                "yearly_amount"
            ) or 0
        )

    return total
