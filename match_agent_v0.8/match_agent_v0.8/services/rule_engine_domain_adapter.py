from datetime import date
from typing import Dict


DEFAULT_COMPANY_SIZE = "small"
DEFAULT_LEAVE_TYPE = "parental_leave"
DEFAULT_REQUESTED_MONTHS = 4


def build_error(
    field: str,
    reason: str,
    details=None
) -> Dict:

    return {
        "field":
            field,
        "reason":
            reason,
        "details":
            details,
    }


def parse_iso_date(
    raw_value
):

    if not raw_value:

        return None

    return date.fromisoformat(
        raw_value
    )


def calculate_requested_months(
    leave_event: Dict
) -> int:

    explicit_months = leave_event.get(
        "requested_months"
    )

    if explicit_months is not None:

        requested_months = int(
            explicit_months
        )

        if requested_months <= 0:

            raise ValueError(
                "requested_months_must_be_positive"
            )

        return requested_months

    start_date = parse_iso_date(
        leave_event.get(
            "start_date"
        )
    )
    end_date = parse_iso_date(
        leave_event.get(
            "end_date"
        )
    )

    if start_date is None or end_date is None:

        return DEFAULT_REQUESTED_MONTHS

    if end_date < start_date:

        raise ValueError(
            "leave_event_end_date_before_start_date"
        )

    return (
        (
            end_date.year
            - start_date.year
        )
        * 12
        + end_date.month
        - start_date.month
        + 1
    )


def get_has_replacement_worker(
    company: Dict,
    leave_event: Dict
) -> bool:

    if "has_replacement_worker" in leave_event:

        return bool(
            leave_event.get(
                "has_replacement_worker"
            )
        )

    return bool(
        company.get(
            "has_replacement_worker",
            False
        )
    )


def build_rule_input(
    company: Dict,
    employee: Dict,
    leave_event: Dict,
    replacement_worker: Dict = None,
) -> Dict:

    replacement_worker = replacement_worker or {}
    leave_type = leave_event.get(
        "leave_type",
        employee.get(
            "leave_type",
            DEFAULT_LEAVE_TYPE,
        ),
    )

    return {
        "company":
            {
                "size":
                    company.get(
                        "size",
                        DEFAULT_COMPANY_SIZE,
                    ),
                "has_replacement_worker":
                    get_has_replacement_worker(
                        company,
                        leave_event,
                    ),
                "insured_employee_count":
                    company.get(
                        "insured_employee_count"
                    ),
            },
        "employee":
            {
                "leave_type":
                    leave_type,
                "monthly_wage":
                    employee.get(
                        "monthly_wage"
                    ),
            },
        "leave_event":
            {
                "type":
                    leave_event.get(
                        "type",
                        leave_type,
                    ),
                "leave_type":
                    leave_type,
                "start_date":
                    leave_event.get(
                        "start_date"
                    ),
                "end_date":
                    leave_event.get(
                        "end_date"
                    ),
                "excluded_months":
                    leave_event.get(
                        "excluded_months"
                    ),
            },
        "replacement_worker":
            {
                "hire_date":
                    replacement_worker.get(
                        "hire_date"
                    ),
                "employment_duration_days":
                    replacement_worker.get(
                        "employment_duration_days"
                    ),
            },
    }


def adapt_general_company_request_to_rule_engine(
    payload: Dict
) -> Dict:

    company = payload.get(
        "company",
        {}
    )
    employee = payload.get(
        "employee",
        {}
    )
    leave_event = payload.get(
        "leave_event",
        {}
    )
    replacement_worker = payload.get(
        "replacement_worker",
        {}
    )

    try:

        requested_months = calculate_requested_months(
            leave_event
        )

    except Exception as exc:

        return {
            "rule_input":
                {},
            "requested_months":
                None,
            "errors":
                [
                    build_error(
                        "leave_event",
                        str(
                            exc
                        ),
                    )
                ],
        }

    return {
        "rule_input":
            build_rule_input(
                company,
                employee,
                leave_event,
                replacement_worker,
            ),
        "requested_months":
            requested_months,
        "errors":
            [],
    }
