# services/condition_evaluator.py

from typing import Any, Dict, List


SUPPORTED_OPERATORS = {
    "eq",
    "neq",
    "gt",
    "gte",
    "lt",
    "lte",
    "in",
    "not_in"
}


MISSING = object()


def get_nested_value(
    data: Dict,
    field: str
):

    current = data

    for part in field.split("."):

        if not isinstance(
            current,
            dict
        ):

            return MISSING

        if part not in current:

            return MISSING

        current = current[part]

    return current


def compare_values(
    actual: Any,
    operator: str,
    expected: Any
) -> bool:

    if operator == "eq":
        return actual == expected

    if operator == "neq":
        return actual != expected

    if operator == "gt":
        return actual > expected

    if operator == "gte":
        return actual >= expected

    if operator == "lt":
        return actual < expected

    if operator == "lte":
        return actual <= expected

    if operator == "in":
        return actual in expected

    if operator == "not_in":
        return actual not in expected

    raise ValueError(
        f"Unsupported operator: {operator}"
    )


def build_condition_result(
    condition: Dict,
    actual: Any,
    reason: str
) -> Dict:

    return {
        "condition_id":
            condition.get(
                "condition_id"
            ),

        "field":
            condition.get(
                "field"
            ),

        "operator":
            condition.get(
                "operator"
            ),

        "expected":
            condition.get(
                "expected"
            ),

        "actual":
            actual,

        "reason":
            reason,

        "evidence_snippets":
            condition.get(
                "evidence_snippets",
                []
            )
    }


def evaluate_operator_condition(
    input_data: Dict,
    condition: Dict
) -> Dict:

    operator = condition.get(
        "operator"
    )

    field = condition.get(
        "field"
    )

    if operator not in SUPPORTED_OPERATORS:

        return build_condition_result(
            condition,
            None,
            "unsupported_operator"
        )

    if not field:

        return build_condition_result(
            condition,
            None,
            "missing_field_name"
        )

    actual = get_nested_value(
        input_data,
        field
    )

    if actual is MISSING:

        return build_condition_result(
            condition,
            None,
            "input_field_missing"
        )

    expected = condition.get(
        "expected"
    )

    try:

        passed = compare_values(
            actual,
            operator,
            expected
        )

    except TypeError:

        return build_condition_result(
            condition,
            actual,
            "comparison_type_error"
        )

    if passed:

        return build_condition_result(
            condition,
            actual,
            "passed"
        )

    if actual is None:

        return build_condition_result(
            condition,
            actual,
            "actual_is_null"
        )

    return build_condition_result(
        condition,
        actual,
        "condition_not_met"
    )


def evaluate_operator_conditions(
    input_data: Dict,
    conditions: List[Dict]
) -> Dict:

    passed_conditions = []
    failed_conditions = []

    for condition in conditions:

        result = evaluate_operator_condition(
            input_data,
            condition
        )

        if result.get(
            "reason"
        ) == "passed":

            passed_conditions.append(
                result
            )

        else:

            failed_conditions.append(
                result
            )

    return {
        "eligible":
            not failed_conditions,

        "passed_conditions":
            passed_conditions,

        "failed_conditions":
            failed_conditions
    }


# ─────────────────────────────────────
# 단일 condition 평가
# ─────────────────────────────────────
def evaluate_condition(
    company_data: Dict,
    employee_data: Dict,
    condition: Dict
) -> bool:

    condition_type = condition.get(
        "type"
    )

    # condition 자체가 비정상
    if not condition_type:

        return False

    # ─────────────────────────────
    # 자녀 나이 조건
    # ─────────────────────────────
    if condition_type == "child_age":

        child_age = employee_data.get(
            "child_age"
        )

        max_age = condition.get(
            "max"
        )

        min_age = condition.get(
            "min"
        )

        if child_age is None:
            return False

        if (
            min_age is not None
            and child_age < min_age
        ):
            return False

        if (
            max_age is not None
            and child_age > max_age
        ):
            return False

        return True

    # ─────────────────────────────
    # 주 근로시간 조건
    # ─────────────────────────────
    elif condition_type == "weekly_work_hours":

        weekly_hours = (
            employee_data.get(
                "weekly_work_hours"
            )
        )

        min_hours = condition.get(
            "min"
        )

        max_hours = condition.get(
            "max"
        )

        if weekly_hours is None:
            return False

        if (
            min_hours is not None
            and weekly_hours < min_hours
        ):
            return False

        if (
            max_hours is not None
            and weekly_hours > max_hours
        ):
            return False

        return True

    # ─────────────────────────────
    # 주 근무일수
    # ─────────────────────────────
    elif (
        condition_type
        == "weekly_working_days"
    ):

        weekly_days = (
            employee_data.get(
                "weekly_working_days"
            )
        )

        min_days = condition.get(
            "min"
        )

        max_days = condition.get(
            "max"
        )

        if weekly_days is None:
            return False

        if (
            min_days is not None
            and weekly_days < min_days
        ):
            return False

        if (
            max_days is not None
            and weekly_days > max_days
        ):
            return False

        return True

    # ─────────────────────────────
    # 근태관리 시스템 필요
    # ─────────────────────────────
    elif (
        condition_type
        == "employee_count"
    ):

        company = company_data.get(
            "company",
            {}
        )

        employee_count = company.get(
            "employee_count"
        )

        if employee_count is None:

            employee_count = len(
                company_data.get(
                    "employees",
                    []
                )
            )

        min_count = condition.get(
            "min"
        )

        max_count = condition.get(
            "max"
        )

        if (
            min_count is not None
            and employee_count < min_count
        ):

            return False

        if (
            max_count is not None
            and employee_count > max_count
        ):

            return False

        return True

    elif (
        condition_type
        == "company_size"
    ):

        company_size = (
            company_data.get(
                "company",
                {}
            ).get(
                "company_size"
            )
        )

        target_size = condition.get(
            "value"
        )

        if target_size is None:

            return True

        return company_size == target_size

    elif (
        condition_type
        == "requires_attendance_system"
    ):

        systems = (
            company_data.get(
                "company",
                {}
            ).get(
                "systems",
                {}
            )
        )

        return systems.get(
            "attendance_system",
            False
        )

    # ─────────────────────────────
    # 그룹웨어 필요
    # ─────────────────────────────
    elif (
        condition_type
        == "requires_groupware"
    ):

        systems = (
            company_data.get(
                "company",
                {}
            ).get(
                "systems",
                {}
            )
        )

        return systems.get(
            "groupware",
            False
        )

    # ─────────────────────────────
    # 원격근무 시스템 필요
    # ─────────────────────────────
    elif (
        condition_type
        == "requires_remote_work_system"
    ):

        systems = (
            company_data.get(
                "company",
                {}
            ).get(
                "systems",
                {}
            )
        )

        return systems.get(
            "remote_work_system",
            False
        )

    # ─────────────────────────────
    # VPN 필요
    # ─────────────────────────────
    elif (
        condition_type
        == "requires_vpn"
    ):

        systems = (
            company_data.get(
                "company",
                {}
            ).get(
                "systems",
                {}
            )
        )

        return systems.get(
            "vpn",
            False
        )

    # ─────────────────────────────
    # 화상회의 시스템 필요
    # ─────────────────────────────
    elif (
        condition_type
        == "requires_video_conference"
    ):

        systems = (
            company_data.get(
                "company",
                {}
            ).get(
                "systems",
                {}
            )
        )

        return systems.get(
            "video_conference_system",
            False
        )

    # ─────────────────────────────
    # 근로계약 변경 필요
    # ─────────────────────────────
    elif (
        condition_type
        == "requires_contract_change"
    ):

        return company_data.get(
            "company",
            {}
        ).get(
            "contract_changed",
            False
        )

    # ─────────────────────────────
    # 노사합의 필요
    # ─────────────────────────────
    elif (
        condition_type
        == "requires_labor_agreement"
    ):

        return company_data.get(
            "company",
            {}
        ).get(
            "labor_agreement",
            False
        )

    # ─────────────────────────────
    # 대체인력 필요
    # ─────────────────────────────
    elif (
        condition_type
        == "requires_replacement_worker"
    ):

        return company_data.get(
            "company",
            {}
        ).get(
            "replacement_worker_hired",
            False
        )

    # ─────────────────────────────
    # 유연근무 여부
    # ─────────────────────────────
    elif (
        condition_type
        == "flexible_work_enabled"
    ):

        return company_data.get(
            "company",
            {}
        ).get(
            "flexible_work_enabled",
            False
        )

    # ─────────────────────────────
    # 미지원 condition
    # ─────────────────────────────
    else:

        print(
            "[condition_evaluator] "
            f"지원하지 않는 "
            f"condition type: "
            f"{condition_type}"
        )

        return False


# ─────────────────────────────────────
# policy 전체 조건 평가
# ─────────────────────────────────────
def evaluate_policy_conditions(
    company_data: Dict,
    employee_data: Dict,
    conditions: list
) -> bool:

    for condition in conditions:

        result = evaluate_condition(

            company_data,
            employee_data,
            condition
        )

        if not result:

            return False

    return True
