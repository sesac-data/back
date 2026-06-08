# pages/parental_page.py

import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(CURRENT_DIR)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import streamlit as st

from data.mock_data import (
    mock_company_data
)

from services.policy_extractor import (
    load_policy_json
)

from services.calculation_service import (
    calculate_employee_supports
)

from services.recommendation_service import (
    generate_recommendation_result
)

from services.gap_analysis_service import (
    analyze_company_gap
)


from services.recommendation_db_service import (
    save_recommendation_result
)

# ─────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────
_parental_page_config = dict(
    page_title="육아지원 지원금 추천",
    layout="wide"
)


# ─────────────────────────────────────
# 안전 숫자 처리
# ─────────────────────────────────────
def safe_number(value):

    if value is None:
        return 0

    try:
        return int(value)

    except Exception:
        return 0


def _format_amount_method(

    amount_normalization: dict
) -> str:

    method = amount_normalization.get(
        "method",
        "-"
    )

    duration_source = amount_normalization.get(
        "duration_source"
    )

    labels = {
        "yearly_max_amount":
            "연간 상한액 기준",
        "monthly_amount_x_duration":
            "월 지원액 x 적용 기간",
        "unavailable":
            "금액 산정 불가"
    }

    label = labels.get(
        method,
        method
    )

    if duration_source:

        return (
            f"{label} ({duration_source})"
        )

    return label


def _format_condition_note(

    condition
) -> str:

    if not isinstance(
        condition,
        dict
    ):

        return str(
            condition
        )

    parts = [
        str(
            condition.get(
                "type",
                "condition"
            )
        )
    ]

    for field in [
        "value",
        "min",
        "max"
    ]:

        value = condition.get(
            field
        )

        if value is not None:

            parts.append(
                f"{field}={value}"
            )

    return " / ".join(
        parts
    )


def _render_normalization_summary(

    policy_json_list: list[dict]
):

    condition_log_count = sum(
        len(
            policy.get(
                "condition_normalization_logs",
                []
            )
        )
        for policy in policy_json_list
    )

    amount_log_count = sum(
        len(
            policy.get(
                "amount_normalization_logs",
                []
            )
        )
        for policy in policy_json_list
    )

    with st.expander(
        "정책 정규화 적용 내역"
    ):

        col1, col2 = st.columns(2)

        col1.metric(
            "조건 정규화",
            condition_log_count
        )

        col2.metric(
            "금액 정규화",
            amount_log_count
        )

        st.caption(
            (
                "추천 계산 전 정책 조건과 지원금 금액을 "
                "표준 스키마로 정리한 결과입니다."
            )
        )

        preview_logs = []

        for policy in policy_json_list:

            preview_logs.extend(
                policy.get(
                    "condition_normalization_logs",
                    []
                )[:3]
            )

            preview_logs.extend(
                policy.get(
                    "amount_normalization_logs",
                    []
                )[:3]
            )

        if preview_logs:

            st.json(
                preview_logs[:10]
            )


# ─────────────────────────────────────
# 페이지
# ─────────────────────────────────────
def page_parental():

    st.title(
        "육아지원 지원금 추천 시스템"
    )

    st.caption(
        "사업주 대상 최적 지원금 조합 추천"
    )

    st.markdown("---")

    # ─────────────────────────────
    # 회사 정보
    # ─────────────────────────────
    st.subheader(
        "회사 정보"
    )

    company_info = (
        mock_company_data[
            "company"
        ]
    )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "기업명",
            company_info.get(
                "company_name",
                "-"
            )
        )

        st.metric(
            "업종",
            company_info.get(
                "industry",
                "-"
            )
        )

    with col2:

        st.metric(
            "기업 규모",
            company_info.get(
                "company_size",
                "-"
            )
        )

        st.metric(
            "직원 수",
            len(
                mock_company_data.get(
                    "employees",
                    []
                )
            )
        )

    st.markdown("---")

    # ─────────────────────────────
    # 직원 정보
    # ─────────────────────────────
    st.subheader(
        "직원 현황"
    )

    employees = (
        mock_company_data.get(
            "employees",
            []
        )
    )

    if not employees:

        st.warning(
            "직원 데이터가 없습니다."
        )

        return

    for employee in employees:

        st.markdown(

            f"""
            <div style="
                padding:20px;
                border-radius:14px;
                background-color:#F9FAFB;
                margin-bottom:18px;
                border:1px solid #E5E7EB;
            ">

            <h3 style="
                color:#111827;
                margin-bottom:12px;
            ">
            👤 {employee.get('name', '-')}
            </h3>

            <p style="color:#374151;">
            • 자녀 나이:
            {employee.get('child_age', '-')}
            </p>

            <p style="color:#374151;">
            • 주 근로시간:
            {employee.get('weekly_work_hours', '-')}
            </p>

            <p style="color:#374151;">
            • 근무 형태:
            {employee.get('work_type', '-')}
            </p>

            </div>
            """,

            unsafe_allow_html=True
        )

    st.markdown("---")

    # ─────────────────────────────
    # 추천 실행
    # ─────────────────────────────
    if st.button(
        "지원금 추천 실행",
        use_container_width=True
    ):

        with st.spinner(
            "정책 계산 중..."
        ):

            company_data = (
                mock_company_data
            )

            # ─────────────────────
            # policy json 로드
            # ─────────────────────
            policy_keys = [

                "parental_leave_reduction_support",

                "replacement_workshare_support",

                "worklife_balance_45_support",

                "childcare_flexible_start_support",

                "working_hours_reduction_support",

                "flexible_work_incent",

                "flexible_work_system_support"
            ]

            policy_json_list = []

            for key in policy_keys:

                try:

                    policy_json = (
                        load_policy_json(
                            key
                        )
                    )

                    policy_json_list.append(
                        policy_json
                    )

                except Exception as e:

                    st.warning(
                        f"{key} 로드 실패: {e}"
                    )

            # ─────────────────────
            # 직원별 계산
            # ─────────────────────
            _render_normalization_summary(
                policy_json_list
            )

            employee_results = (
                calculate_employee_supports(

                    company_data,
                    employees,
                    policy_json_list
                )
            )

            # ─────────────────────
            # 추천 생성
            # ─────────────────────
            recommendation_result = (
                generate_recommendation_result(

                    employee_results,

                    max_supported_people=5
                )
            )
            
            
            
            save_recommendation_result(

            company_data=mock_company_data,

            employee_data=employees,

            recommendation_result=recommendation_result
            )

            # ─────────────────────
            # gap analysis
            # ─────────────────────
            gap_analysis_result = (
                analyze_company_gap(

                    company_data,

                    employees,

                    policy_json_list
                )
            )

        st.success(
            "추천 계산 완료"
        )

        st.markdown("---")

        recommendations = (
            recommendation_result.get(
                "selected_recommendations",
                []
            )
        )

        total_amount = safe_number(
            recommendation_result.get(
                "total_expected_amount"
            )
        )

        # ─────────────────────────
        # KPI
        # ─────────────────────────
        total_systems = set()

        for employee in recommendations:

            supports = employee.get(
                "selected_supports",
                []
            )

            for support in supports:

                for system in support.get(
                    "required_systems",
                    []
                ):

                    total_systems.add(
                        system
                    )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "예상 총 지원금",
                f"{total_amount:,}원"
            )

        with col2:

            st.metric(
                "추천 직원 수",
                len(recommendations)
            )

        with col3:

            st.metric(
                "필요 시스템 수",
                len(total_systems)
            )

        st.markdown("---")

        # ─────────────────────────
        # 직원별 추천 결과
        # ─────────────────────────
        st.subheader(
            "직원별 추천 결과"
        )

        if not recommendations:

            st.warning(
                "추천 가능한 지원금이 없습니다."
            )

            return

        for employee in recommendations:

            employee_name = (
                employee.get(
                    "employee_name",
                    "-"
                )
            )

            total_employee_amount = (
                safe_number(
                    employee.get(
                        "total_amount"
                    )
                )
            )

            # ─────────────────────
            # 직원 카드
            # ─────────────────────
            st.markdown(

                f"""
                <div style="
                    padding:24px;
                    border-radius:16px;
                    background-color:#F9FAFB;
                    margin-bottom:24px;
                    border:1px solid #E5E7EB;
                    box-shadow:0 2px 6px rgba(0,0,0,0.05);
                ">

                <h2 style="
                    color:#111827;
                    margin-bottom:12px;
                ">
                👤 {employee_name}
                </h2>

                <p style="
                    font-size:18px;
                    color:#374151;
                    margin-bottom:0;
                ">
                총 예상 지원금:
                <b style="
                    color:#4F46E5;
                ">
                {total_employee_amount:,}원
                </b>
                </p>

                </div>
                """,

                unsafe_allow_html=True
            )

            supports = employee.get(
                "selected_supports",
                []
            )

            if not supports:

                st.info(
                    "추천 가능한 정책 없음"
                )

                continue

            # ─────────────────────
            # 정책 카드
            # ─────────────────────
            for support in supports:

                policy_name = (
                    support.get(
                        "policy_name",
                        "-"
                    )
                )

                yearly_amount = (
                    safe_number(
                        support.get(
                            "yearly_amount"
                        )
                    )
                )

                monthly_amount = (
                    safe_number(
                        support.get(
                            "monthly_amount"
                        )
                    )
                )

                normalized_duration_months = (
                    support.get(
                        "normalized_duration_months"
                    )
                )

                amount_method = _format_amount_method(
                    support.get(
                        "amount_normalization",
                        {}
                    )
                )

                st.markdown(

                    f"""
                    <div style="
                        padding:20px;
                        border-radius:14px;
                        background-color:white;
                        margin-bottom:20px;
                        border:1px solid #E5E7EB;
                        box-shadow:0 1px 4px rgba(0,0,0,0.04);
                    ">

                    <h4 style="
                        color:#111827;
                        margin-bottom:16px;
                    ">
                    📌 {policy_name}
                    </h4>

                    <div style="
                        display:flex;
                        gap:40px;
                        margin-bottom:12px;
                    ">

                    <div>
                    <div style="
                        font-size:13px;
                        color:#6B7280;
                    ">
                    예상 연 지원금
                    </div>

                    <div style="
                        font-size:22px;
                        font-weight:700;
                        color:#4F46E5;
                    ">
                    {yearly_amount:,}원
                    </div>
                    </div>

                    <div>
                    <div style="
                        font-size:13px;
                        color:#6B7280;
                    ">
                    예상 월 지원금
                    </div>

                    <div style="
                        font-size:18px;
                        font-weight:600;
                        color:#111827;
                    ">
                    {monthly_amount:,}원
                    </div>
                    </div>

                    </div>

                    </div>
                    """,

                    unsafe_allow_html=True
                )

                # ─────────────────
                # 필요 시스템
                # ─────────────────
                st.caption(
                    (
                        f"금액 산정 기준: {amount_method}"
                        + (
                            f" · 적용 기간: "
                            f"{normalized_duration_months}개월"
                            if normalized_duration_months
                            else ""
                        )
                    )
                )

                support_calculation_notes = (
                    support.get(
                        "support_calculation_notes",
                        []
                    )
                )

                if support_calculation_notes:

                    with st.expander(
                        "금액 산식 원문 근거"
                    ):

                        st.json(
                            support_calculation_notes
                        )

                required_systems = (
                    support.get(
                        "required_systems",
                        []
                    )
                )

                if required_systems:

                    st.markdown(
                        "##### 필요 시스템"
                    )

                    cols = st.columns(
                        min(
                            len(required_systems),
                            4
                        )
                    )

                    for idx, system in enumerate(
                        required_systems
                    ):

                        with cols[
                            idx % len(cols)
                        ]:

                            st.success(
                                system
                            )

                # ─────────────────
                # 필요 서류
                # ─────────────────
                required_documents = (
                    support.get(
                        "required_documents",
                        []
                    )
                )

                if required_documents:

                    st.markdown(
                        "##### 필요 서류"
                    )

                    for doc in (
                        required_documents
                    ):

                        st.write(
                            f"• {doc}"
                        )

                # ─────────────────
                # 중요 조건
                # ─────────────────
                important_conditions = (
                    support.get(
                        "important_conditions",
                        []
                    )
                )

                if important_conditions:

                    st.markdown(
                        "##### 주의 조건"
                    )

                    for condition in (
                        important_conditions
                    ):

                        st.warning(
                            _format_condition_note(
                                condition
                            )
                        )

        st.markdown("---")

        # ─────────────────────────
        # 추가 확보 가능 지원금
        # ─────────────────────────
        st.subheader(
            "추가 확보 가능 지원금"
        )

        if not gap_analysis_result:

            st.info(
                "추가 확보 가능한 지원금이 없습니다."
            )

        else:

            for employee_gap in gap_analysis_result:

                employee_name = (
                    employee_gap.get(
                        "employee_name",
                        "-"
                    )
                )

                gap_results = (
                    employee_gap.get(
                        "gap_results",
                        []
                    )
                )

                if not gap_results:
                    continue

                st.markdown(

                    f"""
                    <div style="
                        margin-top:20px;
                        margin-bottom:20px;
                    ">

                    <h3 style="
                        color:#111827;
                    ">
                    👤 {employee_name}
                    </h3>

                    </div>
                    """,

                    unsafe_allow_html=True
                )

                for gap in gap_results:

                    possible_amount = (
                        safe_number(
                            gap.get(
                                "possible_yearly_amount"
                            )
                        )
                    )

                    policy_name = (
                        gap.get(
                            "policy_name",
                            "-"
                        )
                    )

                    st.markdown(

                        f"""
                        <div style="
                            padding:20px;
                            border-radius:14px;
                            background-color:#FEF3C7;
                            margin-bottom:18px;
                            border:1px solid #FCD34D;
                        ">

                        <h4 style="
                            margin-bottom:12px;
                            color:#92400E;
                        ">
                        💡 {policy_name}
                        </h4>

                        <div style="
                            font-size:20px;
                            font-weight:700;
                            color:#B45309;
                            margin-bottom:14px;
                        ">
                        추가 확보 가능:
                        {possible_amount:,}원
                        </div>

                        </div>
                        """,

                        unsafe_allow_html=True
                    )

                    # ─────────────────────
                    # 부족 조건
                    # ─────────────────────
                    missing_conditions = (
                        gap.get(
                            "missing_conditions",
                            []
                        )
                    )

                    if missing_conditions:

                        st.markdown(
                            "##### 필요 조건"
                        )

                        for condition in (
                            missing_conditions
                        ):

                            st.warning(
                                condition
                            )

                    # ─────────────────────
                    # 필요 시스템
                    # ─────────────────────
                    required_systems = (
                        gap.get(
                            "required_systems",
                            []
                        )
                    )

                    if required_systems:

                        st.markdown(
                            "##### 필요 시스템"
                        )

                        cols = st.columns(
                            min(
                                len(required_systems),
                                4
                            )
                        )

                        for idx, system in enumerate(
                            required_systems
                        ):

                            with cols[
                                idx % len(cols)
                            ]:

                                st.info(
                                    system
                                )

                    # ─────────────────────
                    # 필요 서류
                    # ─────────────────────
                    required_documents = (
                        gap.get(
                            "required_documents",
                            []
                        )
                    )

                    if required_documents:

                        st.markdown(
                            "##### 필요 서류"
                        )

                        for doc in (
                            required_documents
                        ):

                            st.write(
                                f"• {doc}"
                            )

        st.markdown("---")

        # ─────────────────────────
        # 사업주 액션 플랜
        # ─────────────────────────
        st.subheader(
            "사업주 액션 플랜"
        )

        action_items = set()

        for employee in recommendations:

            supports = employee.get(
                "selected_supports",
                []
            )

            for support in supports:

                for system in support.get(
                    "required_systems",
                    []
                ):

                    action_items.add(
                        f"{system} 도입"
                    )

        if not action_items:

            st.info(
                "추가 조치가 필요하지 않습니다."
            )

        else:

            for item in action_items:

                st.write(
                    f"• {item}"
                )

        st.markdown("---")

        # ─────────────────────────
        # 디버깅용 결과
        # ─────────────────────────
        with st.expander(
            "전체 계산 결과 보기"
        ):

            st.json(
                recommendation_result
            )
