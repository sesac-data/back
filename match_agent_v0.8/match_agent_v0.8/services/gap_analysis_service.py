# services/gap_analysis_service.py

from typing import Dict, List

from services.condition_evaluator import (
    evaluate_condition
)


# ─────────────────────────────────────
# 연 지원금 계산
# ─────────────────────────────────────
def calculate_gap_yearly_amount(

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

    duration = support_info.get(
        "max_duration_months"
    )

    # 이미 연 지원금 존재
    if yearly_amount is not None:

        return yearly_amount

    # 월 지원금 기반 계산
    if (
        monthly_amount is not None
        and duration is not None
    ):

        return (
            monthly_amount
            * duration
        )

    return 0


# ─────────────────────────────────────
# condition → 사용자 메시지 변환
# ─────────────────────────────────────
def convert_condition_to_message(

    company_data: Dict,

    employee_data: Dict,

    condition_type: str,

    condition: Dict
):

    company = company_data.get(
        "company",
        {}
    )

    # ─────────────────────────
    # 직원 수 조건
    # ─────────────────────────
    if condition_type == "employee_count":

        current_count = company.get(
            "employee_count",
            0
        )

        required_count = condition.get(
            "min",
            0
        )

        gap = (
            required_count
            - current_count
        )

        if gap > 0:

            return (
                f"직원 {gap}명 "
                f"추가 채용 필요"
            )

        return (
            "직원 수 조건 충족 필요"
        )

    # ─────────────────────────
    # 기업 규모 조건
    # ─────────────────────────
    elif condition_type == "company_size":

        current_size = company.get(
            "company_size",
            "-"
        )

        target_size = condition.get(
            "target",
            "-"
        )

        return (

            f"현재 기업 규모: "
            f"{current_size} / "

            f"정책 대상: "
            f"{target_size}"
        )

    # ─────────────────────────
    # 자녀 나이 조건
    # ─────────────────────────
    elif condition_type == "child_age":

        max_age = condition.get(
            "max"
        )

        child_age = employee_data.get(
            "child_age"
        )

        if (
            child_age is not None
            and max_age is not None
        ):

            gap = (
                child_age
                - max_age
            )

            if gap > 0:

                return (
                    f"자녀 나이 "
                    f"{gap}세 초과"
                )

            return (
                f"자녀 나이 "
                f"{max_age}세 이하 필요"
            )

        return (
            "자녀 나이 조건 미충족"
        )

    # ─────────────────────────
    # 근로시간 조건
    # ─────────────────────────
    elif (
        condition_type
        == "weekly_work_hours"
    ):

        current_hours = (
            employee_data.get(
                "weekly_work_hours",
                0
            )
        )

        min_hours = condition.get(
            "min"
        )

        max_hours = condition.get(
            "max"
        )

        if (
            min_hours is not None
            and current_hours < min_hours
        ):

            gap = (
                min_hours
                - current_hours
            )

            return (
                f"주 근로시간 "
                f"{gap}시간 부족"
            )

        if (
            max_hours is not None
            and current_hours > max_hours
        ):

            gap = (
                current_hours
                - max_hours
            )

            return (
                f"주 근로시간 "
                f"{gap}시간 초과"
            )

        return (
            "근로시간 조건 미충족"
        )

    # ─────────────────────────
    # condition mapping
    # ─────────────────────────
    condition_map = {

        "requires_attendance_system":
            "근태관리 시스템 도입 필요",

        "requires_contract_change":
            "근로계약 변경 필요",

        "requires_labor_agreement":
            "노사합의 필요",

        "requires_replacement_worker":
            "대체인력 채용 필요",

        "requires_groupware":
            "그룹웨어 도입 필요",

        "requires_remote_work_system":
            "원격근무 시스템 도입 필요",

        "requires_vpn":
            "VPN 시스템 구축 필요",

        "requires_video_conference":
            "화상회의 시스템 구축 필요",

        "flexible_work_enabled":
            "유연근무제 도입 필요",

        "working_hour_reduction":
            "실근로시간 단축 제도 도입 필요",

        "new_hire_increase":
            "신규 채용 인원 증가 필요",

        "company_size":
            "기업 규모 조건 미충족"
    }

    return condition_map.get(

        condition_type,

        f"미충족 조건: {condition_type}"
    )


# ─────────────────────────────────────
# 추천 사유 생성
# ─────────────────────────────────────
def generate_gap_reason(

    employee_data: Dict,
    support_item: Dict

):

    reasons = []

    child_age = employee_data.get(
        "child_age"
    )

    weekly_hours = employee_data.get(
        "weekly_work_hours"
    )

    if child_age is not None:

        reasons.append(
            f"자녀 나이 "
            f"{child_age}세"
        )

    if weekly_hours is not None:

        reasons.append(
            f"주 "
            f"{weekly_hours}시간 근무"
        )

    support_type = support_item.get(
        "support_type",
        ""
    )

    if "유연근무" in support_type:

        reasons.append(
            "유연근무 활용 가능"
        )

    if "대체인력" in support_type:

        reasons.append(
            "대체인력 운영 가능"
        )

    return reasons


# ─────────────────────────────────────
# 단일 정책 부족 분석
# ─────────────────────────────────────
def analyze_policy_gap(

    company_data: Dict,
    employee_data: Dict,
    support_item: Dict

):

    conditions = support_item.get(
        "conditions",
        []
    )

    missing_conditions = []

    for condition in conditions:

        passed = evaluate_condition(

            company_data,
            employee_data,
            condition
        )

        if passed:
            continue

        condition_type = condition.get(
            "type"
        )

        readable_message = (
            convert_condition_to_message(

                company_data,

                employee_data,

                condition_type,

                condition
            )
        )

        missing_conditions.append(
            readable_message
        )

    # 조건 모두 충족
    if not missing_conditions:

        return None

    support_info = support_item.get(
        "support",
        {}
    )

    yearly_amount = (
        calculate_gap_yearly_amount(
            support_info
        )
    )

    return {

        "policy_name":
            support_item.get(
                "support_type",
                "-"
            ),

        "possible_yearly_amount":
            yearly_amount,

        "missing_conditions":
            missing_conditions,

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

        "recommend_reason":
            generate_gap_reason(

                employee_data,

                support_item
            )
    }


# ─────────────────────────────────────
# 직원 기준 gap analysis
# ─────────────────────────────────────
def analyze_employee_gap(

    company_data: Dict,
    employee_data: Dict,
    policy_json_list: List[Dict]

):

    gap_results = []

    for policy_json in policy_json_list:

        support_items = policy_json.get(
            "support_items",
            []
        )

        for support_item in support_items:

            result = analyze_policy_gap(

                company_data,
                employee_data,
                support_item
            )

            if result:

                gap_results.append(
                    result
                )

    # ─────────────────────────
    # 실행 가능 정책만 필터링
    # ─────────────────────────
    filtered_results = []

    for result in gap_results:

        missing_conditions = (
            result.get(
                "missing_conditions",
                []
            )
        )

        possible_amount = (
            result.get(
                "possible_yearly_amount",
                0
            ) or 0
        )

        policy_name = (
            result.get(
                "policy_name",
                ""
            )
        )

        # 육아/유연근무 관련만
        allowed_keywords = [

            "육아",

            "유연근무",

            "재택",

            "원격",

            "선택근무",

            "시차출퇴근",

            "근로시간 단축",

            "대체인력"
        ]

        if not any(

            keyword in policy_name

            for keyword in allowed_keywords
        ):

            continue

        # 조건 너무 많으면 제외
        if len(missing_conditions) > 2:

            continue

        # 지원금 너무 작으면 제외
        if possible_amount < 1000000:

            continue

        filtered_results.append(
            result
        )

    # ─────────────────────────
    # 지원금 기준 정렬
    # ─────────────────────────
    filtered_results = sorted(

        filtered_results,

        key=lambda x: (
            x.get(
                "possible_yearly_amount"
            ) or 0
        ),

        reverse=True
    )

    # ─────────────────────────
    # 동일 정책 제거
    # ─────────────────────────
    unique_results = []

    seen_policy_names = set()

    for result in filtered_results:

        policy_name = (
            result.get(
                "policy_name",
                ""
            )
        )

        if policy_name in seen_policy_names:

            continue

        seen_policy_names.add(
            policy_name
        )

        unique_results.append(
            result
        )

    # 상위 3개만
    return unique_results[:3]


# ─────────────────────────────────────
# 전체 직원 gap analysis
# ─────────────────────────────────────
def analyze_company_gap(

    company_data: Dict,
    employees: List[Dict],
    policy_json_list: List[Dict]

):

    results = []

    for employee in employees:

        employee_gap = (
            analyze_employee_gap(

                company_data,
                employee,
                policy_json_list
            )
        )

        results.append({

            "employee_name":
                employee.get(
                    "name",
                    "-"
                ),

            "gap_results":
                employee_gap
        })

    return results
