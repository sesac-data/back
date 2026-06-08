def map_html_to_pdf(data):
    return {
        # 기본 정보
        "biz_name": data.get("biz_name"),
        "biz_no": data.get("biz_no"),
        "ceo_name": data.get("ceo_name"),
        "biz_type": data.get("biz_type"),
        "corp_no": data.get("corp_no"),
        "biz_manage_no": data.get("biz_manage_no"),
        "address": data.get("address"),

        # 피보험자
        "monthly_insurance_counts": data.get("monthly_insurance_counts", []),
        "avg_insurance_count": data.get("avg_insured"),

        # 매출
        "sales_period_from": data.get("sales_from"),
        "sales_period_to": data.get("sales_to"),
        "sales_amount": data.get("sales_amount"),
        "sales_converted": data.get("sales_amount"),
        "insurance_count": data.get("avg_insured"),

        # 체크박스
        "categories": data.get("categories", []),

        # 채용
        "hiring_plans": {
            "count": data.get("hire_total"),
            "in": data.get("hire_capital"),
            "not_in": data.get("hire_non_capital"),
            "time": data.get("work_time"),
            "type": data.get("hire_type"),
            "salary": data.get("salary")
        },

        # 선채용
        "pre_hired_info": {
            "name": data.get("pre_hire_name"),
            "date": data.get("pre_hire_date")
        } if data.get("pre_hire_check") else None,

        # 담당자
        "staff_dept": data.get("contact_dept"),
        "staff_name": data.get("contact_name"),
        "email": data.get("contact_email"),
        "staff_fax": ""
    }