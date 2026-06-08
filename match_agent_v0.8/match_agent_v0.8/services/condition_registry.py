# ─────────────────────────────────────
# 지원 condition registry
# ─────────────────────────────────────

SUPPORTED_CONDITION_TYPES = {

    # ─────────────────────────
    # 근로자 조건
    # ─────────────────────────
    "child_age": {

        "description":
            "자녀 나이 조건",

        "required_fields":
            ["max"]
    },

    "weekly_work_hours": {

        "description":
            "주 근로시간 조건",

        "required_fields":
            ["min", "max"]
    },

    "weekly_working_days": {

        "description":
            "주 근무일수 조건",

        "required_fields":
            ["max"]
    },

    # ─────────────────────────
    # 기업 조건
    # ─────────────────────────
    "employee_count": {

        "description":
            "직원 수 조건",

        "required_fields":
            ["min", "max"]
    },

    "company_size": {

        "description":
            "기업 규모 조건",

        "required_fields":
            ["value"]
    },

    # ─────────────────────────
    # 시스템 조건
    # ─────────────────────────
    "requires_attendance_system": {

        "description":
            "출퇴근 관리 시스템 필요",

        "required_fields":
            ["value"]
    },

    "requires_groupware": {

        "description":
            "그룹웨어 필요",

        "required_fields":
            ["value"]
    },

    "requires_remote_work_system": {

        "description":
            "원격근무 시스템 필요",

        "required_fields":
            ["value"]
    },

    # ─────────────────────────
    # 제도 도입 조건
    # ─────────────────────────
    "requires_contract_change": {

        "description":
            "근로계약 변경 필요",

        "required_fields":
            ["value"]
    },

    "requires_labor_agreement": {

        "description":
            "노사합의 필요",

        "required_fields":
            ["value"]
    },

    "requires_replacement_worker": {

        "description":
            "대체인력 필요",

        "required_fields":
            ["value"]
    },

    "working_hour_reduction": {

        "description":
            "근로시간 단축 여부",

        "required_fields":
            ["value"]
    },

    "new_hire_increase": {

        "description":
            "신규채용 증가 여부",

        "required_fields":
            ["value"]
    }
}