# services/recommendation_service.py

from typing import Dict, List

from services.policy_combination_rules import (
    CONFLICT_RULES
)


COMPANY_LEVEL_POLICY_KEYS = {
    "flexible_work_system_support"
}


# ─────────────────────────────────────
# 안전 숫자 변환
# ─────────────────────────────────────
def safe_number(value):

    if value is None:
        return 0

    try:
        return int(value)

    except Exception:
        return 0


# ─────────────────────────────────────
# 정책 충돌 여부 확인
# ─────────────────────────────────────
def is_conflicting_policy(

    selected_supports: List[Dict],
    new_support: Dict

) -> bool:

    new_policy_name = (
        new_support.get(
            "policy_name"
        )
    )

    duplicate_allowed = (
        new_support.get(
            "duplicate_allowed",
            []
        )
    )

    conflict_targets = (
        CONFLICT_RULES.get(
            new_policy_name,
            []
        )
    )

    for selected in selected_supports:

        selected_policy_name = (
            selected.get(
                "policy_name"
            )
        )

        # ─────────────────────
        # 중복 허용 정책
        # ─────────────────────
        if (
            selected_policy_name
            in duplicate_allowed
        ):

            continue

        # ─────────────────────
        # 충돌 정책
        # ─────────────────────
        if (
            selected_policy_name
            in conflict_targets
        ):

            return True

    return False


def get_policy_key(

    support: Dict
) -> str:

    return (
        support.get(
            "amount_normalization",
            {}
        ).get(
            "policy_key",
            ""
        )
    )


def is_company_level_support(

    support: Dict
) -> bool:

    return (
        get_policy_key(
            support
        )
        in
        COMPANY_LEVEL_POLICY_KEYS
    )


def keep_best_support_per_policy_key(

    supports: List[Dict]
) -> List[Dict]:

    best_by_key = {}

    for support in supports:

        policy_key = (
            get_policy_key(
                support
            )
            or
            support.get(
                "policy_name",
                "-"
            )
        )

        current = best_by_key.get(
            policy_key
        )

        if (
            current is None
            or safe_number(
                support.get(
                    "yearly_amount"
                )
            )
            >
            safe_number(
                current.get(
                    "yearly_amount"
                )
            )
        ):

            best_by_key[
                policy_key
            ] = support

    return list(
        best_by_key.values()
    )


# ─────────────────────────────────────
# 직원별 최고 지원금 선택
# ─────────────────────────────────────
def select_best_support_per_employee(

    employee_results: List[Dict]

):

    recommendations = []

    for result in employee_results:

        available_supports = result.get(
            "available_supports",
            []
        )

        if not available_supports:
            continue

        # ─────────────────────────
        # 지원금 기준 정렬
        # ─────────────────────────
        available_supports = [
            support
            for support in available_supports
            if (
                safe_number(
                    support.get(
                        "yearly_amount"
                    )
                )
                > 0
                and not is_company_level_support(
                    support
                )
            )
        ]

        available_supports = keep_best_support_per_policy_key(
            available_supports
        )

        sorted_supports = sorted(

            available_supports,

            key=lambda x: safe_number(
                x.get(
                    "yearly_amount"
                )
            ),

            reverse=True
        )

        selected_supports = []

        for support in sorted_supports:

            policy_name = support.get(
                "policy_name"
            )

            # 정책명 없는 경우 제외
            if not policy_name:
                continue

            # ─────────────────────
            # 충돌 정책 제외
            # ─────────────────────
            if is_conflicting_policy(

                selected_supports,
                support
            ):

                continue



            selected_supports.append(
                support
            )

        recommendations.append({

            "employee_name":
                result.get(
                    "employee_name"
                ),

            "selected_supports":
                selected_supports,

            "total_amount":
                calculate_employee_total_amount(
                    selected_supports
                )
        })

    return recommendations


# ─────────────────────────────────────
# 직원 총 지원금 계산
# ─────────────────────────────────────
def calculate_employee_total_amount(

    selected_supports: List[Dict]

):

    total = 0

    for support in selected_supports:

        total += safe_number(
            support.get(
                "yearly_amount"
            )
        )

    return total


# ─────────────────────────────────────
# 지원금 기준 정렬
# ─────────────────────────────────────
def sort_recommendations_by_amount(

    recommendations: List[Dict]

):

    return sorted(

        recommendations,

        key=lambda x: safe_number(
            x.get(
                "total_amount"
            )
        ),

        reverse=True
    )


# ─────────────────────────────────────
# 최대 지원 인원 선택
# ─────────────────────────────────────
def select_top_supported_employees(

    recommendations: List[Dict],
    max_people: int
):

    sorted_results = (
        sort_recommendations_by_amount(
            recommendations
        )
    )

    return sorted_results[:max_people]


# ─────────────────────────────────────
# 총 추천 지원금 계산
# ─────────────────────────────────────
def calculate_total_recommended_amount(

    selected_recommendations: List[Dict]
):

    total = 0

    for employee in selected_recommendations:

        total += safe_number(
            employee.get(
                "total_amount"
            )
        )

    return total


# ─────────────────────────────────────
# 전체 추천 생성
# ─────────────────────────────────────
def generate_recommendation_result(

    employee_results: List[Dict],
    max_supported_people: int
):

    recommendations = (
        select_best_support_per_employee(
            employee_results
        )
    )

    selected = (
        select_top_supported_employees(

            recommendations,
            max_supported_people
        )
    )

    total_amount = (
        calculate_total_recommended_amount(
            selected
        )
    )

    return {

        "selected_recommendations":
            selected,

        "total_expected_amount":
            total_amount,

        "max_supported_people":
            max_supported_people
    }
