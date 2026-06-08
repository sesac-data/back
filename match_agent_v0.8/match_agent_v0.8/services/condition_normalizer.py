from copy import deepcopy
from typing import Any, Dict, List, Tuple

from services.condition_registry import (
    SUPPORTED_CONDITION_TYPES
)


CONDITION_TYPE_ALIASES = {
    "requires_time_tracking_system":
        "requires_attendance_system",
    "requires_work_time_tracking_system":
        "requires_attendance_system",
    "requires_work_time_management_system":
        "requires_attendance_system",
    "requires_attendance_management_system":
        "requires_attendance_system",
    "attendance_system":
        "requires_attendance_system",
    "time_tracking_system":
        "requires_attendance_system",
    "company_employee_count":
        "employee_count",
    "company_employee_size":
        "employee_count",
    "company_size_category":
        "company_size",
    "requires_remote_work_equipment":
        "requires_remote_work_system",
    "requires_remote_system":
        "requires_remote_work_system",
    "requires_groupware_system":
        "requires_groupware",
    "requires_labor_management_agreement":
        "requires_labor_agreement",
    "requires_collective_agreement":
        "requires_labor_agreement",
    "requires_replacement_employee":
        "requires_replacement_worker",
    "replacement_worker_required":
        "requires_replacement_worker",
    "working_hours_reduction":
        "working_hour_reduction",
    "working_hour_reduction_duration_months":
        "working_hour_reduction",
    "daily_work_hour_reduction":
        "working_hour_reduction",
    "minimum_duration_months":
        "working_hour_reduction",
    "new_hire_added":
        "new_hire_increase",
    "new_employee_increase":
        "new_hire_increase",
}


CONDITION_RELOCATION_TARGETS = {
    "application_process": {
        "application_within_months_after_conversion",
        "employment_program_completion",
        "employment_program_completion_period",
        "employment_program_exemption",
        "employment_program_exemption_job_registration_period",
        "facility_usage_period",
        "installation_after_application",
        "job_registration_institution",
        "job_registration_period",
        "requires_business_plan_submission",
        "requires_employment_center_approval",
    },
    "important_conditions": {
        "age_of_retirement_period",
        "business_operation_period_years",
        "company_type",
        "continuous_service_months",
        "contract_period",
        "elderly_employee_increase",
        "employee_age",
        "employment_insurance",
        "employment_insurance_period_years",
        "employment_maintenance_months",
        "employment_maintenance_period",
        "employment_type",
        "employment_type_after",
        "employment_type_before",
        "gender",
        "leave_duration_days",
        "monthly_average_wage",
        "monthly_overtime_hours",
        "nationality",
        "prior_employment_months",
        "remaining_retirement_period_years",
        "replacement_worker_employment_days",
        "requires_flexible_work制度",
        "unemployment_period",
        "weekly_work_hours_after_reduction",
    },
    "risk_conditions": {
        "excluded_employees",
        "excluded_employer_types",
    },
    "support_calculation_notes": {
        "employer_wage_compensation_amount",
        "investment_cost_support_max",
        "investment_cost_support_ratio",
        "management_system_usage_fee_support_1year",
        "management_system_usage_fee_support_2years",
        "monthly_wage_increase",
        "wage_after_conversion",
    },
}


def _get_relocation_target(

    condition_type: str
) -> str | None:

    for target, condition_types in CONDITION_RELOCATION_TARGETS.items():

        if condition_type in condition_types:

            return target

    return None


def _condition_to_note(

    condition: Dict
) -> Dict:

    note = deepcopy(
        condition
    )

    note[
        "source"
    ] = "condition_normalizer"

    return note


def _default_value_for(

    condition_type: str
) -> Any:

    if condition_type.startswith(
        "requires_"
    ):

        return True

    if condition_type in {
        "working_hour_reduction",
        "new_hire_increase"
    }:

        return True

    return None


def _ensure_required_fields(

    condition: Dict
) -> Tuple[Dict, List[str]]:

    normalized = deepcopy(
        condition
    )

    added_fields = []

    condition_type = normalized.get(
        "type"
    )

    if (
        condition_type
        not in
        SUPPORTED_CONDITION_TYPES
    ):

        return normalized, added_fields

    required_fields = (
        SUPPORTED_CONDITION_TYPES[
            condition_type
        ].get(
            "required_fields",
            []
        )
    )

    for field in required_fields:

        if field in normalized:

            continue

        if (
            field == "value"
            and "target" in normalized
        ):

            normalized[field] = normalized.get(
                "target"
            )

        else:

            normalized[field] = _default_value_for(
                condition_type
            )

        added_fields.append(
            field
        )

    return normalized, added_fields


def _normalize_condition_shape(

    condition: Dict
) -> Tuple[Dict, List[Dict]]:

    normalized = deepcopy(
        condition
    )

    logs = []

    if (
        normalized.get(
            "type"
        )
        == "company_size"
        and (
            normalized.get(
                "min"
            )
            is not None
            or normalized.get(
                "max"
            )
            is not None
        )
        and normalized.get(
            "value"
        )
        is None
    ):

        normalized[
            "type"
        ] = "employee_count"

        logs.append({
            "from":
                "company_size",
            "to":
                "employee_count",
            "action":
                "shape_based_type_alias"
        })

    return normalized, logs


def normalize_condition(

    condition: Dict,
    path: str
) -> Tuple[Dict, List[Dict]]:

    if not isinstance(
        condition,
        dict
    ):

        return condition, []

    normalized = deepcopy(
        condition
    )

    logs = []

    original_type = normalized.get(
        "type"
    )

    mapped_type = CONDITION_TYPE_ALIASES.get(
        original_type,
        original_type
    )

    if mapped_type != original_type:

        normalized["type"] = mapped_type

        logs.append({
            "path":
                path,
            "from":
                original_type,
            "to":
                mapped_type,
            "action":
                "type_alias"
        })

    normalized, shape_logs = _normalize_condition_shape(
        normalized
    )

    for log in shape_logs:

        logs.append({
            "path":
                path,
            **log
        })

    normalized, added_fields = _ensure_required_fields(
        normalized
    )

    for field in added_fields:

        logs.append({
            "path":
                path,
            "type":
                normalized.get(
                    "type"
                ),
            "field":
                field,
            "action":
                "add_required_field"
        })

    return normalized, logs


def _normalize_condition_list(

    conditions: List,
    path: str
) -> Tuple[List, List[Dict]]:

    normalized_conditions = []

    logs = []

    for index, condition in enumerate(
        conditions
    ):

        normalized, condition_logs = normalize_condition(
            condition,
            f"{path}[{index}]"
        )

        normalized_conditions.append(
            normalized
        )

        logs.extend(
            condition_logs
        )

    return normalized_conditions, logs


def _append_relocated_condition(

    policy_json: Dict,
    support_item: Dict | None,
    target: str,
    condition: Dict
) -> None:

    note = _condition_to_note(
        condition
    )

    if target == "risk_conditions":

        policy_json.setdefault(
            target,
            []
        ).append(
            note
        )

        return

    if support_item is None:

        policy_json.setdefault(
            "manual_review_conditions",
            []
        ).append(
            note
        )

        return

    support_item.setdefault(
        target,
        []
    ).append(
        note
    )


def _relocate_non_registry_conditions(

    policy_json: Dict
) -> List[Dict]:

    logs = []

    for item_index, support_item in enumerate(
        policy_json.get(
            "support_items",
            []
        )
    ):

        field_names = [
            "conditions",
            "target_conditions",
            "important_conditions"
        ]

        for field_name in field_names:

            condition_list = support_item.get(
                field_name,
                []
            )

            if not isinstance(
                condition_list,
                list
            ):

                continue

            kept_conditions = []

            for condition_index, condition in enumerate(
                condition_list
            ):

                if not isinstance(
                    condition,
                    dict
                ):

                    kept_conditions.append(
                        condition
                    )

                    continue

                if (
                    condition.get(
                        "source"
                    )
                    == "condition_normalizer"
                ):

                    kept_conditions.append(
                        condition
                    )

                    continue

                condition_type = condition.get(
                    "type"
                )

                if (
                    condition_type
                    in
                    SUPPORTED_CONDITION_TYPES
                    and
                    field_name == "conditions"
                ):

                    kept_conditions.append(
                        condition
                    )

                    continue

                target = (
                    _get_relocation_target(
                        condition_type
                    )
                    or
                    "manual_review_conditions"
                )

                _append_relocated_condition(
                    policy_json,
                    support_item,
                    target,
                    condition
                )

                logs.append({
                    "path":
                        (
                            f"support_items[{item_index}]"
                            f".{field_name}[{condition_index}]"
                        ),
                    "type":
                        condition_type,
                    "to":
                        target,
                    "action":
                        "relocate_non_registry_condition"
                })

            support_item[
                field_name
            ] = kept_conditions

    return logs


def normalize_policy_conditions(

    policy_json: Dict
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

        for field_name in [
            "conditions",
            "target_conditions",
            "important_conditions"
        ]:

            condition_list = support_item.get(
                field_name,
                []
            )

            if not isinstance(
                condition_list,
                list
            ):

                continue

            normalized_list, field_logs = _normalize_condition_list(
                condition_list,
                f"support_items[{item_index}].{field_name}"
            )

            support_item[field_name] = normalized_list

            logs.extend(
                field_logs
            )

    risk_conditions = normalized_policy.get(
        "risk_conditions",
        []
    )

    if isinstance(
        risk_conditions,
        list
    ):

        normalized_risks, risk_logs = _normalize_condition_list(
            risk_conditions,
            "risk_conditions"
        )

        normalized_policy["risk_conditions"] = normalized_risks

        logs.extend(
            risk_logs
        )

    logs.extend(
        _relocate_non_registry_conditions(
            normalized_policy
        )
    )

    normalized_policy[
        "condition_normalization_logs"
    ] = logs

    return normalized_policy
