from copy import deepcopy
from typing import Any, Dict, Iterable, List, Optional, Set


ALLOWED_CALCULATION_TYPES = {
    "monthly_fixed",
    "period_tiered",
    "conditional_bonus",
    "cost_share",
}

ALLOWED_TOP_LEVEL_FIELDS = {
    "application_process",
    "approved_at",
    "approved_by",
    "combination_rules",
    "conditions",
    "evidence_snippets",
    "extraction_model",
    "policy_category",
    "policy_id",
    "policy_key",
    "policy_name",
    "prompt_version",
    "review_status",
    "risk_conditions",
    "source_document_id",
    "source_file",
    "source_url",
    "support_items",
    "support_limit",
    "unresolved_rules",
}

ALLOWED_SUPPORT_ITEM_FIELDS = {
    "applied_bonuses",
    "bonuses",
    "calculation_type",
    "cap_field",
    "conditions",
    "cost_field",
    "duplicate_allowed",
    "duplicate_disallowed",
    "evidence_snippets",
    "excluded_months_field",
    "important_conditions",
    "max_months",
    "max_support_amount",
    "monthly_amount",
    "monthly_cap_ratio",
    "monthly_exclusion",
    "required_documents",
    "required_systems",
    "support",
    "support_item_id",
    "support_ratio",
    "support_type",
    "target_conditions",
    "tiers",
    "yearly_amount",
    "yearly_max_amount",
}

ALLOWED_CONDITION_FIELDS = {
    "condition_id",
    "evidence_snippets",
    "expected",
    "field",
    "max",
    "min",
    "operator",
    "type",
    "unit",
    "value",
}

ALLOWED_CONDITION_GROUP_FIELDS = {
    "condition_group_id",
    "conditions",
    "evidence_snippets",
    "mode",
}

ALLOWED_CONDITION_GROUP_MODES = {
    "and",
    "or",
}

ALLOWED_SUPPORT_FIELDS = {
    "calculation_type",
    "cap_field",
    "cost_field",
    "evidence_snippets",
    "excluded_months_field",
    "max_duration_months",
    "max_months",
    "max_support_amount",
    "monthly_amount",
    "monthly_cap_ratio",
    "monthly_exclusion",
    "normalized_yearly_amount",
    "support_ratio",
    "tiers",
    "yearly_amount",
    "yearly_max_amount",
}

ALLOWED_TIER_FIELDS = {
    "end_month",
    "evidence_snippets",
    "monthly_amount",
    "start_month",
}

ALLOWED_BONUS_FIELDS = {
    "bonus_amount",
    "bonus_id",
    "conditions",
    "evidence_snippets",
    "max_months",
    "monthly_amount",
}

ALLOWED_RULE_FIELDS = {
    "evidence_snippets",
    "reason",
    "rule_id",
    "rule_type",
    "target_policy_ids",
}

ALLOWED_UNRESOLVED_RULE_FIELDS = {
    "description",
    "evidence_snippets",
    "rule_id",
    "rule_type",
}


def validate_policy_extraction_candidate(
    parsed_candidate: Optional[Dict[str, Any]],
    raw_text: str,
) -> Dict[str, Any]:
    """Validate an LLM extraction candidate without mutating it."""

    before = deepcopy(parsed_candidate)
    errors: List[Dict[str, Any]] = []

    if parsed_candidate is None:
        errors.append(
            _error(
                "missing_candidate",
                "$",
                "parsed_candidate is required.",
            )
        )
        return _result(
            errors,
            before,
            parsed_candidate,
        )

    if not isinstance(parsed_candidate, dict):
        errors.append(
            _error(
                "invalid_candidate_type",
                "$",
                "parsed_candidate must be an object.",
                actual=type(parsed_candidate).__name__,
            )
        )
        return _result(
            errors,
            before,
            parsed_candidate,
        )

    _check_unsupported_fields(
        parsed_candidate,
        ALLOWED_TOP_LEVEL_FIELDS,
        "$",
        errors,
    )

    if _is_blank(parsed_candidate.get("policy_id")):
        errors.append(
            _error(
                "missing_policy_id",
                "$.policy_id",
                "policy_id is required.",
                actual=parsed_candidate.get("policy_id"),
            )
        )

    if _is_blank(parsed_candidate.get("policy_name")):
        errors.append(
            _error(
                "missing_policy_name",
                "$.policy_name",
                "policy_name is required.",
                actual=parsed_candidate.get("policy_name"),
            )
        )

    if parsed_candidate.get("review_status") != "needs_review":
        errors.append(
            _error(
                "invalid_review_status",
                "$.review_status",
                "LLM candidates must remain review_status=needs_review.",
                actual=parsed_candidate.get("review_status"),
            )
        )

    _validate_evidence_list(
        parsed_candidate.get("evidence_snippets"),
        "$.evidence_snippets",
        raw_text,
        errors,
    )

    _validate_conditions(
        parsed_candidate.get("conditions"),
        "$.conditions",
        raw_text,
        errors,
        seen_condition_ids=set(),
    )
    _validate_conditions(
        parsed_candidate.get("risk_conditions"),
        "$.risk_conditions",
        raw_text,
        errors,
        seen_condition_ids=set(),
    )
    _validate_support_items(
        parsed_candidate.get("support_items"),
        raw_text,
        errors,
    )
    _validate_combination_rules(
        parsed_candidate.get("combination_rules"),
        raw_text,
        errors,
    )
    _validate_unresolved_rules(
        parsed_candidate.get("unresolved_rules"),
        raw_text,
        errors,
    )

    return _result(
        errors,
        before,
        parsed_candidate,
    )


def _validate_support_items(
    support_items: Any,
    raw_text: str,
    errors: List[Dict[str, Any]],
) -> None:

    if not isinstance(support_items, list) or not support_items:
        errors.append(
            _error(
                "missing_support_items",
                "$.support_items",
                "support_items must be a non-empty array.",
                actual=support_items,
            )
        )
        return

    seen_support_item_ids: Set[str] = set()
    seen_condition_ids: Set[str] = set()

    for index, item in enumerate(support_items):
        path = f"$.support_items[{index}]"

        if not isinstance(item, dict):
            errors.append(
                _error(
                    "invalid_support_item_type",
                    path,
                    "support item must be an object.",
                    actual=type(item).__name__,
                )
            )
            continue

        _check_unsupported_fields(
            item,
            ALLOWED_SUPPORT_ITEM_FIELDS,
            path,
            errors,
        )

        support_item_id = item.get("support_item_id")
        if _is_blank(support_item_id):
            errors.append(
                _error(
                    "missing_support_item_id",
                    f"{path}.support_item_id",
                    "support_item_id is required.",
                    actual=support_item_id,
                )
            )
        elif support_item_id in seen_support_item_ids:
            errors.append(
                _error(
                    "duplicate_support_item_id",
                    f"{path}.support_item_id",
                    "support_item_id must be unique.",
                    actual=support_item_id,
                )
            )
        else:
            seen_support_item_ids.add(support_item_id)

        _validate_evidence_list(
            item.get("evidence_snippets"),
            f"{path}.evidence_snippets",
            raw_text,
            errors,
        )
        _validate_conditions(
            item.get("conditions"),
            f"{path}.conditions",
            raw_text,
            errors,
            seen_condition_ids=seen_condition_ids,
        )

        support = item.get("support")
        if isinstance(support, dict):
            _validate_support_object(
                support,
                f"{path}.support",
                raw_text,
                errors,
            )
        else:
            _validate_flat_support_fields(
                item,
                path,
                raw_text,
                errors,
            )

        _validate_tiers(
            item.get("tiers"),
            f"{path}.tiers",
            raw_text,
            errors,
        )
        _validate_bonuses(
            item.get("bonuses") or item.get("applied_bonuses"),
            f"{path}.bonuses",
            raw_text,
            errors,
        )


def _validate_support_object(
    support: Dict[str, Any],
    path: str,
    raw_text: str,
    errors: List[Dict[str, Any]],
) -> None:

    _check_unsupported_fields(
        support,
        ALLOWED_SUPPORT_FIELDS,
        path,
        errors,
    )
    _validate_flat_support_fields(
        support,
        path,
        raw_text,
        errors,
    )
    _validate_tiers(
        support.get("tiers"),
        f"{path}.tiers",
        raw_text,
        errors,
    )


def _validate_flat_support_fields(
    item: Dict[str, Any],
    path: str,
    raw_text: str,
    errors: List[Dict[str, Any]],
) -> None:

    calculation_type = item.get("calculation_type")

    if _is_blank(calculation_type):
        errors.append(
            _error(
                "missing_calculation_type",
                f"{path}.calculation_type",
                "calculation_type is required.",
                actual=calculation_type,
            )
        )
    elif calculation_type not in ALLOWED_CALCULATION_TYPES:
        errors.append(
            _error(
                "unsupported_calculation_type",
                f"{path}.calculation_type",
                "calculation_type is not supported.",
                actual=calculation_type,
            )
        )

    if calculation_type == "monthly_fixed":
        _validate_number(
            item.get("monthly_amount"),
            f"{path}.monthly_amount",
            "invalid_monthly_amount",
            errors,
        )
        max_months = (
            item.get("max_months")
            if "max_months" in item
            else item.get("max_duration_months")
        )
        # max_months may be null when the source states no duration cap.
        # The calculation engine uses requested months without inferring a cap,
        # so an absent value must not be flagged. Only validate when present.
        if max_months is not None:
            _validate_positive_integer(
                max_months,
                f"{path}.max_months",
                "invalid_max_months",
                errors,
            )

    if calculation_type == "cost_share":
        _validate_number(
            item.get("support_ratio"),
            f"{path}.support_ratio",
            "invalid_support_ratio",
            errors,
        )
        # max_support_amount is optional (no cap when absent); validate if present.
        if item.get("max_support_amount") is not None:
            _validate_number(
                item.get("max_support_amount"),
                f"{path}.max_support_amount",
                "invalid_max_support_amount",
                errors,
            )

    # monthly_exclusion is an optional boolean marker enabling per-month exclusion.
    if item.get("monthly_exclusion") is not None:
        if not isinstance(item.get("monthly_exclusion"), bool):
            errors.append(
                _error(
                    "invalid_monthly_exclusion",
                    f"{path}.monthly_exclusion",
                    "monthly_exclusion must be a boolean.",
                    actual=item.get("monthly_exclusion"),
                )
            )

    # monthly_cap_ratio is an optional per-wage monthly cap on any calc type.
    # When present it must be a number in (0, 1].
    if item.get("monthly_cap_ratio") is not None:
        monthly_cap_ratio = item.get("monthly_cap_ratio")
        if (
            not _is_number(monthly_cap_ratio)
            or monthly_cap_ratio <= 0
            or monthly_cap_ratio > 1
        ):
            errors.append(
                _error(
                    "invalid_monthly_cap_ratio",
                    f"{path}.monthly_cap_ratio",
                    "monthly_cap_ratio must be a number in (0, 1].",
                    actual=monthly_cap_ratio,
                )
            )

    _validate_evidence_list(
        item.get("evidence_snippets"),
        f"{path}.evidence_snippets",
        raw_text,
        errors,
    )


def _is_condition_group(
    item: Any,
) -> bool:

    return (
        isinstance(item, dict)
        and "conditions" in item
        and (
            "condition_group_id" in item
            or "mode" in item
        )
    )


def _validate_condition_group(
    group: Dict[str, Any],
    path: str,
    raw_text: str,
    errors: List[Dict[str, Any]],
    seen_condition_ids: Set[str],
) -> None:

    _check_unsupported_fields(
        group,
        ALLOWED_CONDITION_GROUP_FIELDS,
        path,
        errors,
    )

    if _is_blank(group.get("condition_group_id")):
        errors.append(
            _error(
                "missing_condition_group_id",
                f"{path}.condition_group_id",
                "condition_group_id is required.",
                actual=group.get("condition_group_id"),
            )
        )

    mode = group.get("mode")
    if mode not in ALLOWED_CONDITION_GROUP_MODES:
        errors.append(
            _error(
                "unsupported_condition_group_mode",
                f"{path}.mode",
                "mode must be 'and' or 'or'.",
                actual=mode,
            )
        )

    members = group.get("conditions")
    if not isinstance(members, list) or not members:
        errors.append(
            _error(
                "empty_condition_group",
                f"{path}.conditions",
                "condition group must contain at least one member condition.",
                actual=members,
            )
        )
    else:
        _validate_conditions(
            members,
            f"{path}.conditions",
            raw_text,
            errors,
            seen_condition_ids,
        )

    _validate_evidence_list(
        group.get("evidence_snippets"),
        f"{path}.evidence_snippets",
        raw_text,
        errors,
    )


def _validate_conditions(
    conditions: Any,
    path: str,
    raw_text: str,
    errors: List[Dict[str, Any]],
    seen_condition_ids: Set[str],
) -> None:

    if conditions is None:
        return

    if not isinstance(conditions, list):
        errors.append(
            _error(
                "invalid_conditions_type",
                path,
                "conditions must be an array when present.",
                actual=type(conditions).__name__,
            )
        )
        return

    for index, condition in enumerate(conditions):
        condition_path = f"{path}[{index}]"

        if not isinstance(condition, dict):
            errors.append(
                _error(
                    "invalid_condition_type",
                    condition_path,
                    "condition must be an object.",
                    actual=type(condition).__name__,
                )
            )
            continue

        if _is_condition_group(condition):
            _validate_condition_group(
                condition,
                condition_path,
                raw_text,
                errors,
                seen_condition_ids,
            )
            continue

        _check_unsupported_fields(
            condition,
            ALLOWED_CONDITION_FIELDS,
            condition_path,
            errors,
        )
        condition_id = condition.get("condition_id")

        if _is_blank(condition_id):
            errors.append(
                _error(
                    "missing_condition_id",
                    f"{condition_path}.condition_id",
                    "condition_id is required.",
                    actual=condition_id,
                )
            )
        elif condition_id in seen_condition_ids:
            errors.append(
                _error(
                    "duplicate_condition_id",
                    f"{condition_path}.condition_id",
                    "condition_id must be unique.",
                    actual=condition_id,
                )
            )
        else:
            seen_condition_ids.add(condition_id)

        _validate_evidence_list(
            condition.get("evidence_snippets"),
            f"{condition_path}.evidence_snippets",
            raw_text,
            errors,
        )


def _validate_tiers(
    tiers: Any,
    path: str,
    raw_text: str,
    errors: List[Dict[str, Any]],
) -> None:

    if tiers is None:
        return

    if not isinstance(tiers, list):
        errors.append(
            _error(
                "invalid_tiers_type",
                path,
                "tiers must be an array when present.",
                actual=type(tiers).__name__,
            )
        )
        return

    for index, tier in enumerate(tiers):
        tier_path = f"{path}[{index}]"

        if not isinstance(tier, dict):
            errors.append(
                _error(
                    "invalid_tier_type",
                    tier_path,
                    "tier must be an object.",
                    actual=type(tier).__name__,
                )
            )
            continue

        _check_unsupported_fields(
            tier,
            ALLOWED_TIER_FIELDS,
            tier_path,
            errors,
        )
        _validate_number(
            tier.get("monthly_amount"),
            f"{tier_path}.monthly_amount",
            "invalid_monthly_amount",
            errors,
        )
        _validate_evidence_list(
            tier.get("evidence_snippets"),
            f"{tier_path}.evidence_snippets",
            raw_text,
            errors,
        )


def _validate_bonuses(
    bonuses: Any,
    path: str,
    raw_text: str,
    errors: List[Dict[str, Any]],
) -> None:

    if bonuses is None:
        return

    if not isinstance(bonuses, list):
        errors.append(
            _error(
                "invalid_bonuses_type",
                path,
                "bonuses must be an array when present.",
                actual=type(bonuses).__name__,
            )
        )
        return

    for index, bonus in enumerate(bonuses):
        bonus_path = f"{path}[{index}]"

        if not isinstance(bonus, dict):
            errors.append(
                _error(
                    "invalid_bonus_type",
                    bonus_path,
                    "bonus must be an object.",
                    actual=type(bonus).__name__,
                )
            )
            continue

        _check_unsupported_fields(
            bonus,
            ALLOWED_BONUS_FIELDS,
            bonus_path,
            errors,
        )
        _validate_evidence_list(
            bonus.get("evidence_snippets"),
            f"{bonus_path}.evidence_snippets",
            raw_text,
            errors,
        )
        _validate_conditions(
            bonus.get("conditions"),
            f"{bonus_path}.conditions",
            raw_text,
            errors,
            seen_condition_ids=set(),
        )


def _validate_combination_rules(
    rules: Any,
    raw_text: str,
    errors: List[Dict[str, Any]],
) -> None:

    if rules is None:
        return

    if not isinstance(rules, list):
        errors.append(
            _error(
                "invalid_combination_rules_type",
                "$.combination_rules",
                "combination_rules must be an array when present.",
                actual=type(rules).__name__,
            )
        )
        return

    seen_rule_ids: Set[str] = set()

    for index, rule in enumerate(rules):
        path = f"$.combination_rules[{index}]"

        if not isinstance(rule, dict):
            errors.append(
                _error(
                    "invalid_combination_rule_type",
                    path,
                    "combination rule must be an object.",
                    actual=type(rule).__name__,
                )
            )
            continue

        _check_unsupported_fields(
            rule,
            ALLOWED_RULE_FIELDS,
            path,
            errors,
        )
        rule_id = rule.get("rule_id")

        if _is_blank(rule_id):
            errors.append(
                _error(
                    "missing_rule_id",
                    f"{path}.rule_id",
                    "rule_id is required.",
                    actual=rule_id,
                )
            )
        elif rule_id in seen_rule_ids:
            errors.append(
                _error(
                    "duplicate_rule_id",
                    f"{path}.rule_id",
                    "rule_id must be unique.",
                    actual=rule_id,
                )
            )
        else:
            seen_rule_ids.add(rule_id)

        target_policy_ids = rule.get("target_policy_ids")
        if not isinstance(target_policy_ids, list) or not target_policy_ids:
            errors.append(
                _error(
                    "missing_target_policy_ids",
                    f"{path}.target_policy_ids",
                    "target_policy_ids must be a non-empty array.",
                    actual=target_policy_ids,
                )
            )
        else:
            for target_index, target_policy_id in enumerate(target_policy_ids):
                if _is_blank(target_policy_id):
                    errors.append(
                        _error(
                            "missing_target_policy_ids",
                            f"{path}.target_policy_ids[{target_index}]",
                            "target policy id must not be blank.",
                            actual=target_policy_id,
                        )
                    )
                elif target_policy_id == "UNKNOWN_POLICY_ID":
                    errors.append(
                        _error(
                            "unknown_policy_id",
                            f"{path}.target_policy_ids[{target_index}]",
                            "UNKNOWN_POLICY_ID is not allowed in combination rules.",
                            actual=target_policy_id,
                        )
                    )

        _validate_evidence_list(
            rule.get("evidence_snippets"),
            f"{path}.evidence_snippets",
            raw_text,
            errors,
        )


def _validate_unresolved_rules(
    unresolved_rules: Any,
    raw_text: str,
    errors: List[Dict[str, Any]],
) -> None:

    if unresolved_rules is None:
        return

    if not isinstance(unresolved_rules, list):
        errors.append(
            _error(
                "invalid_unresolved_rules",
                "$.unresolved_rules",
                "unresolved_rules must remain a separate array.",
                actual=type(unresolved_rules).__name__,
            )
        )
        return

    for index, rule in enumerate(unresolved_rules):
        path = f"$.unresolved_rules[{index}]"

        if not isinstance(rule, dict):
            errors.append(
                _error(
                    "invalid_unresolved_rule_type",
                    path,
                    "unresolved rule must be an object.",
                    actual=type(rule).__name__,
                )
            )
            continue

        _check_unsupported_fields(
            rule,
            ALLOWED_UNRESOLVED_RULE_FIELDS,
            path,
            errors,
        )
        _validate_evidence_list(
            rule.get("evidence_snippets"),
            f"{path}.evidence_snippets",
            raw_text,
            errors,
        )


def _validate_evidence_list(
    snippets: Any,
    path: str,
    raw_text: str,
    errors: List[Dict[str, Any]],
) -> None:

    if not isinstance(snippets, list) or not snippets:
        errors.append(
            _error(
                "missing_evidence",
                path,
                "evidence_snippets must be a non-empty array.",
                actual=snippets,
            )
        )
        return

    for index, snippet in enumerate(snippets):
        snippet_path = f"{path}[{index}]"

        if _is_blank(snippet):
            errors.append(
                _error(
                    "missing_evidence",
                    snippet_path,
                    "evidence snippet must not be blank.",
                    actual=snippet,
                )
            )
            continue

        if isinstance(snippet, str) and not _is_evidence_match(
            snippet,
            raw_text,
        ):
            errors.append(
                _error(
                    "evidence_not_in_raw_text",
                    snippet_path,
                    "evidence snippet must be an exact substring of raw_text.",
                    actual=snippet,
                )
            )


def _check_unsupported_fields(
    payload: Dict[str, Any],
    allowed_fields: Iterable[str],
    path: str,
    errors: List[Dict[str, Any]],
) -> None:

    allowed = set(allowed_fields)

    for field_name in payload:
        if field_name not in allowed:
            errors.append(
                _error(
                    "unsupported_field",
                    f"{path}.{field_name}",
                    "Field is not supported by the candidate validation schema.",
                    actual=field_name,
                )
            )


def _validate_number(
    value: Any,
    path: str,
    error_type: str,
    errors: List[Dict[str, Any]],
) -> None:

    if not _is_number(value):
        errors.append(
            _error(
                error_type,
                path,
                "Value must be a number.",
                actual=value,
            )
        )


def _validate_positive_integer(
    value: Any,
    path: str,
    error_type: str,
    errors: List[Dict[str, Any]],
) -> None:

    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        errors.append(
            _error(
                error_type,
                path,
                "Value must be a positive integer.",
                actual=value,
            )
        )


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _is_evidence_match(
    snippet: str,
    raw_text: str,
) -> bool:

    if snippet in raw_text:
        return True

    normalized_snippet = _normalize_evidence_for_compare(
        snippet
    )
    normalized_raw_text = _normalize_evidence_for_compare(
        raw_text
    )

    return normalized_snippet in normalized_raw_text


def _normalize_evidence_for_compare(
    value: str,
) -> str:

    return " ".join(
        value.split()
    )


def _error(
    error_type: str,
    path: str,
    message: str,
    actual: Any = None,
) -> Dict[str, Any]:

    error = {
        "error_type": error_type,
        "path": path,
        "message": message,
    }

    if actual is not None:
        error["actual"] = actual

    return error


def _result(
    errors: List[Dict[str, Any]],
    before: Any,
    after: Any,
) -> Dict[str, Any]:

    mutation_detected = before != after

    if mutation_detected:
        errors.append(
            _error(
                "candidate_mutated",
                "$",
                "Validator must not mutate parsed_candidate.",
            )
        )

    return {
        "passed": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
        "mutation_detected": mutation_detected,
    }
