# services/policy_validator.py

from typing import Dict, List


# ─────────────────────────────────────
# 단일 support item 검증
# ─────────────────────────────────────
def validate_support_item(

    support_item: Dict

):

    errors = []

    warnings = []

    support_type = support_item.get(
        "support_type",
        "-"
    )

    support_info = support_item.get(
        "support",
        {}
    )

    conditions = support_item.get(
        "conditions",
        []
    )
    
    condition_groups = [
        (
            "conditions",
            conditions
        ),
        (
            "target_conditions",
            support_item.get(
                "target_conditions",
                []
            )
        ),
        (
            "important_conditions",
            support_item.get(
                "important_conditions",
                []
            )
        )
    ]

    for condition_field, condition_list in condition_groups:

        for condition in condition_list:

            if not isinstance(
                condition,
                dict
            ):

                continue

            if (
                condition.get(
                    "source"
                )
                == "condition_normalizer"
            ):

                continue

            condition_result = validate_condition(
                condition
            )

            errors.extend(
                [
                    f"{condition_field}: {error}"
                    for error in condition_result.get(
                        "errors",
                        []
                    )
                ]
            )

            warnings.extend(
                [
                    f"{condition_field}: {warning}"
                    for warning in condition_result.get(
                        "warnings",
                        []
                    )
                ]
            )
    
    evidence_snippets = support_item.get(
    "evidence_snippets",
    []
    
    )
    
    if not evidence_snippets:
        warnings.append(
            'evidence_snippets 없음'
        )

    # ─────────────────────────
    # support 정보 존재 여부
    # ─────────────────────────
    if not support_info:

        errors.append(
            "support 정보 없음"
        )

    # ─────────────────────────
    # 금액 검증
    # ─────────────────────────
    monthly_amount = support_info.get(
        "monthly_amount"
    )

    yearly_amount = support_info.get(
        "yearly_max_amount"
    )

    normalized_yearly_amount = support_info.get(
        "normalized_yearly_amount"
    )

    duration = support_info.get(
        "max_duration_months"
    )

    if (
        monthly_amount is not None
        and duration is not None
        and yearly_amount is not None
    ):

        calculated = (
            monthly_amount
            * duration
        )

        if calculated > yearly_amount:

            warnings.append(

                "monthly_amount × "
                "duration > yearly_amount"
            )

    # ─────────────────────────
    # support 금액 전부 없음
    # ─────────────────────────
    if (
        monthly_amount is None
        and yearly_amount is None
        and normalized_yearly_amount is None
    ):

        warnings.append(
            "지원금 정보 없음"
        )

    # ─────────────────────────
    # condition 검증
    # ─────────────────────────
    for condition in conditions:

        condition_type = condition.get(
            "type"
        )

        # ─────────────────────
        # child_age
        # ─────────────────────
        if condition_type == "child_age":

            if (
                condition.get("max")
                is None
            ):

                warnings.append(
                    "child_age max 없음"
                )

        # ─────────────────────
        # 근로시간
        # ─────────────────────
        elif (
            condition_type
            == "weekly_work_hours"
        ):

            min_hours = condition.get(
                "min"
            )

            max_hours = condition.get(
                "max"
            )

            if (
                min_hours is not None
                and max_hours is not None
                and min_hours > max_hours
            ):

                errors.append(
                    "weekly_work_hours "
                    "min > max"
                )

        # ─────────────────────
        # employee_count
        # ─────────────────────
        elif (
            condition_type
            == "employee_count"
        ):

            min_count = condition.get(
                "min"
            )

            max_count = condition.get(
                "max"
            )

            if (
                min_count is None
                and max_count is None
            ):

                warnings.append(
                    "employee_count "
                    "min 없음"
                )

        # ─────────────────────
        # company_size
        # ─────────────────────
        elif (
            condition_type
            == "company_size"
        ):

            target = condition.get(
                "value"
            )

            if target is None:

                warnings.append(
                    "company_size "
                    "target 없음"
                )

    return {

        "support_type":
            support_type,

        "errors":
            errors,

        "warnings":
            warnings
    }


# ─────────────────────────────────────
# policy json 전체 검증
# ─────────────────────────────────────
def validate_policy_json(

    policy_json: Dict

):

    validation_results = []

    policy_name = policy_json.get(
        "policy_name",
        "-"
    )

    support_items = policy_json.get(
        "support_items",
        []
    )

    # ─────────────────────────
    # support item 없음
    # ─────────────────────────
    if not support_items:

        validation_results.append({

            "policy_name":
                policy_name,

            "support_type":
                "-",

            "errors":
                ["support_items 없음"],

            "warnings":
                []
        })

        return validation_results

    # ─────────────────────────
    # support item별 검증
    # ─────────────────────────
    for support_item in support_items:

        result = validate_support_item(
            support_item
        )

        result["policy_name"] = (
            policy_name
        )

        validation_results.append(
            result
        )

    risk_errors = []

    risk_warnings = []

    for condition in policy_json.get(
        "risk_conditions",
        []
    ):

        if not isinstance(
            condition,
            dict
        ):

            continue

        if (
            condition.get(
                "source"
            )
            == "condition_normalizer"
        ):

            continue

        condition_result = validate_condition(
            condition
        )

        risk_errors.extend(
            condition_result.get(
                "errors",
                []
            )
        )

        risk_warnings.extend(
            condition_result.get(
                "warnings",
                []
            )
        )

    if (
        risk_errors
        or risk_warnings
    ):

        validation_results.append({

            "policy_name":
                policy_name,

            "support_type":
                "risk_conditions",

            "errors":
                risk_errors,

            "warnings":
                risk_warnings
        })

    return validation_results


# ─────────────────────────────────────
# validation 결과 출력
# ─────────────────────────────────────
def print_validation_result(

    validation_results: List[Dict]

):

    print("\n")

    print("=" * 40)
    print("POLICY VALIDATION RESULT")
    print("=" * 40)

    for result in validation_results:

        policy_name = result.get(
            "policy_name",
            "-"
        )

        support_type = result.get(
            "support_type",
            "-"
        )

        errors = result.get(
            "errors",
            []
        )

        warnings = result.get(
            "warnings",
            []
        )

        print("\n")

        print(
            f"[POLICY] "
            f"{policy_name}"
        )

        print(
            f"[SUPPORT] "
            f"{support_type}"
        )

        # ─────────────────────
        # errors
        # ─────────────────────
        if errors:

            print("[ERRORS]")

            for error in errors:

                print(
                    f" - {error}"
                )

        # ─────────────────────
        # warnings
        # ─────────────────────
        if warnings:

            print("[WARNINGS]")

            for warning in warnings:

                print(
                    f" - {warning}"
                )

        # ─────────────────────
        # 정상
        # ─────────────────────
        if (
            not errors
            and not warnings
        ):

            print(
                "정상"
            )

    print("\n")
    print("=" * 40)
    print("VALIDATION COMPLETE")
    print("=" * 40)
    
    
from services.condition_registry import (
    SUPPORTED_CONDITION_TYPES
)

# ─────────────────────────────────────
# condition 검증
# ─────────────────────────────────────
def _validate_condition_legacy(

    condition: dict
):

    warnings = []

    condition_type = condition.get(
        "type"
    )

    # ─────────────────────────
    # type 존재 여부
    # ─────────────────────────
    if not condition_type:

        warnings.append(
            "condition type 없음"
        )

        return warnings

    # ─────────────────────────
    # registry 미지원
    # ─────────────────────────
    if (

        condition_type

        not in

        SUPPORTED_CONDITION_TYPES
    ):

        warnings.append(

            f"지원하지 않는 "

            f"condition type: "

            f"{condition_type}"
        )

        return warnings

    # ─────────────────────────
    # required fields 확인
    # ─────────────────────────
    required_fields = (

        SUPPORTED_CONDITION_TYPES[
            condition_type
        ].get(
            "required_fields",
            []
        )
    )

    for field in required_fields:

        if field not in condition:

            warnings.append(

                f"{condition_type} "

                f"필수 field 없음: "

                f"{field}"
            )

    return warnings


def validate_condition(

    condition: dict
):

    errors = []

    warnings = []

    condition_type = condition.get(
        "type"
    )

    if not condition_type:

        errors.append(
            "condition type missing"
        )

        return {
            "errors":
                errors,

            "warnings":
                warnings
        }

    if (

        condition_type

        not in

        SUPPORTED_CONDITION_TYPES
    ):

        errors.append(
            f"unsupported condition type: {condition_type}"
        )

        return {
            "errors":
                errors,

            "warnings":
                warnings
        }

    required_fields = (

        SUPPORTED_CONDITION_TYPES[
            condition_type
        ].get(
            "required_fields",
            []
        )
    )

    for field in required_fields:

        if field not in condition:

            errors.append(
                f"{condition_type} "
                f"required field missing: "
                f"{field}"
            )

    return {
        "errors":
            errors,

        "warnings":
            warnings
    }


def has_validation_errors(

    validation_results: List[Dict]
) -> bool:

    return any(

        result.get(
            "errors"
        )

        for result in validation_results
    )
