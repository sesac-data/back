from services.rule_engine_domain_adapter import (
    adapt_general_company_request_to_rule_engine,
    calculate_requested_months,
)


def base_payload():

    return {
        "company":
            {
                "size":
                    "small",
                "insured_employee_count":
                    26,
            },
        "employee":
            {
                "leave_type":
                    "parental_leave",
            },
        "leave_event":
            {
                "start_date":
                    "2026-07-01",
                "end_date":
                    "2026-10-31",
                "has_replacement_worker":
                    True,
            },
    }


def test_builds_rule_input_from_general_company_payload():

    result = adapt_general_company_request_to_rule_engine(
        base_payload()
    )

    assert result["rule_input"] == {
        "company":
            {
                "size":
                    "small",
                "has_replacement_worker":
                    True,
                "insured_employee_count":
                    26,
            },
        "employee":
            {
                "leave_type":
                    "parental_leave",
                "monthly_wage":
                    None,
            },
        "leave_event":
            {
                "type":
                    "parental_leave",
                "leave_type":
                    "parental_leave",
                "start_date":
                    "2026-07-01",
                "end_date":
                    "2026-10-31",
                "excluded_months":
                    None,
            },
        "replacement_worker":
            {
                "hire_date":
                    None,
                "employment_duration_days":
                    None,
            },
    }
    assert result["requested_months"] == 4
    assert result["errors"] == []


def test_leave_event_leave_type_overrides_employee_leave_type():

    payload = base_payload()
    payload["employee"]["leave_type"] = "other_leave"
    payload["leave_event"]["leave_type"] = "parental_leave"

    result = adapt_general_company_request_to_rule_engine(
        payload
    )

    assert result["rule_input"]["employee"]["leave_type"] == "parental_leave"


def test_company_replacement_worker_used_when_leave_event_missing():

    payload = base_payload()
    payload["company"]["has_replacement_worker"] = True
    del payload["leave_event"]["has_replacement_worker"]

    result = adapt_general_company_request_to_rule_engine(
        payload
    )

    assert result["rule_input"]["company"]["has_replacement_worker"] is True


def test_preserves_replacement_worker_and_leave_dates_in_rule_input():

    payload = base_payload()
    payload["replacement_worker"] = {
        "hire_date":
            "2026-05-01",
        "employment_duration_days":
            120,
    }

    result = adapt_general_company_request_to_rule_engine(
        payload
    )

    assert result["rule_input"]["replacement_worker"] == {
        "hire_date":
            "2026-05-01",
        "employment_duration_days":
            120,
    }
    assert result["rule_input"]["company"]["insured_employee_count"] == 26
    assert result["rule_input"]["leave_event"]["start_date"] == "2026-07-01"
    assert result["rule_input"]["leave_event"]["end_date"] == "2026-10-31"
    assert result["rule_input"]["leave_event"]["type"] == "parental_leave"


def test_requested_months_explicit_value_is_used():

    assert calculate_requested_months(
        {
            "requested_months":
                7,
            "start_date":
                "2026-07-01",
            "end_date":
                "2026-10-31",
        }
    ) == 7


def test_missing_dates_uses_demo_default_months():

    assert calculate_requested_months(
        {}
    ) == 4


def test_end_date_before_start_date_returns_error():

    payload = base_payload()
    payload["leave_event"]["start_date"] = "2026-10-31"
    payload["leave_event"]["end_date"] = "2026-07-01"

    result = adapt_general_company_request_to_rule_engine(
        payload
    )

    assert result["rule_input"] == {}
    assert result["requested_months"] is None
    assert result["errors"][0]["reason"] == "leave_event_end_date_before_start_date"


def test_non_positive_requested_months_returns_error():

    payload = base_payload()
    payload["leave_event"]["requested_months"] = 0

    result = adapt_general_company_request_to_rule_engine(
        payload
    )

    assert result["errors"][0]["reason"] == "requested_months_must_be_positive"


if __name__ == "__main__":

    test_builds_rule_input_from_general_company_payload()
    test_leave_event_leave_type_overrides_employee_leave_type()
    test_company_replacement_worker_used_when_leave_event_missing()
    test_preserves_replacement_worker_and_leave_dates_in_rule_input()
    test_requested_months_explicit_value_is_used()
    test_missing_dates_uses_demo_default_months()
    test_end_date_before_start_date_returns_error()
    test_non_positive_requested_months_returns_error()
    print("test_rule_engine_domain_adapter passed")
