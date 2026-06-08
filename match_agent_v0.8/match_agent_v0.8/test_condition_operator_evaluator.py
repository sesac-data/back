from services.condition_evaluator import (
    evaluate_operator_conditions
)


def sample_input():

    return {
        "company": {
            "employee_count": 12,
            "industry": "IT",
            "region": "seoul"
        },
        "employee": {
            "age": 34,
            "child_age": 5,
            "weekly_work_hours": 35,
            "leave_type": "childcare",
            "nullable_value": None
        }
    }


def condition(
    condition_id,
    field,
    operator,
    expected,
    evidence
):

    return {
        "condition_id":
            condition_id,
        "field":
            field,
        "operator":
            operator,
        "expected":
            expected,
        "evidence_snippets":
            [
                evidence
            ]
    }


def test_all_conditions_pass():

    result = evaluate_operator_conditions(
        sample_input(),
        [
            condition(
                "c-eq",
                "employee.leave_type",
                "eq",
                "childcare",
                "leave evidence"
            ),
            condition(
                "c-neq",
                "company.industry",
                "neq",
                "finance",
                "industry evidence"
            ),
            condition(
                "c-gt",
                "company.employee_count",
                "gt",
                10,
                "count evidence"
            ),
            condition(
                "c-gte",
                "employee.weekly_work_hours",
                "gte",
                35,
                "hours evidence"
            ),
            condition(
                "c-lt",
                "employee.child_age",
                "lt",
                6,
                "child age evidence"
            ),
            condition(
                "c-lte",
                "employee.child_age",
                "lte",
                5,
                "child age max evidence"
            ),
            condition(
                "c-in",
                "company.region",
                "in",
                [
                    "seoul",
                    "busan"
                ],
                "region evidence"
            ),
            condition(
                "c-not-in",
                "company.industry",
                "not_in",
                [
                    "retail",
                    "manufacturing"
                ],
                "not in evidence"
            )
        ]
    )

    assert result["eligible"] is True
    assert len(result["passed_conditions"]) == 8
    assert result["failed_conditions"] == []


def test_single_condition_failure():

    result = evaluate_operator_conditions(
        sample_input(),
        [
            condition(
                "c-fail-one",
                "employee.child_age",
                "lte",
                3,
                "child age evidence"
            )
        ]
    )

    assert result["eligible"] is False
    assert result["passed_conditions"] == []
    assert result["failed_conditions"][0]["condition_id"] == "c-fail-one"
    assert result["failed_conditions"][0]["field"] == "employee.child_age"
    assert result["failed_conditions"][0]["operator"] == "lte"
    assert result["failed_conditions"][0]["expected"] == 3
    assert result["failed_conditions"][0]["actual"] == 5
    assert result["failed_conditions"][0]["reason"] == "condition_not_met"


def test_multiple_condition_failures():

    result = evaluate_operator_conditions(
        sample_input(),
        [
            condition(
                "c-fail-a",
                "company.employee_count",
                "lt",
                5,
                "count evidence"
            ),
            condition(
                "c-fail-b",
                "employee.leave_type",
                "eq",
                "maternity",
                "leave evidence"
            )
        ]
    )

    failed_ids = [
        item["condition_id"]
        for item in result["failed_conditions"]
    ]

    assert result["eligible"] is False
    assert failed_ids == [
        "c-fail-a",
        "c-fail-b"
    ]


def test_unsupported_operator():

    result = evaluate_operator_conditions(
        sample_input(),
        [
            condition(
                "c-unsupported",
                "employee.child_age",
                "between",
                [
                    1,
                    7
                ],
                "operator evidence"
            )
        ]
    )

    failure = result["failed_conditions"][0]

    assert result["eligible"] is False
    assert failure["condition_id"] == "c-unsupported"
    assert failure["reason"] == "unsupported_operator"


def test_missing_input_field():

    result = evaluate_operator_conditions(
        sample_input(),
        [
            condition(
                "c-missing",
                "employee.missing_value",
                "eq",
                "x",
                "missing evidence"
            )
        ]
    )

    failure = result["failed_conditions"][0]

    assert result["eligible"] is False
    assert failure["condition_id"] == "c-missing"
    assert failure["actual"] is None
    assert failure["reason"] == "input_field_missing"


def test_null_value_handling():

    result = evaluate_operator_conditions(
        sample_input(),
        [
            condition(
                "c-null-eq",
                "employee.nullable_value",
                "eq",
                None,
                "null evidence"
            ),
            condition(
                "c-null-fail",
                "employee.nullable_value",
                "gt",
                1,
                "null compare evidence"
            )
        ]
    )

    assert result["eligible"] is False
    assert result["passed_conditions"][0]["condition_id"] == "c-null-eq"
    assert result["passed_conditions"][0]["actual"] is None
    assert result["failed_conditions"][0]["condition_id"] == "c-null-fail"
    assert result["failed_conditions"][0]["reason"] == "comparison_type_error"


def test_evidence_snippets_are_linked():

    result = evaluate_operator_conditions(
        sample_input(),
        [
            condition(
                "c-evidence",
                "employee.weekly_work_hours",
                "gte",
                35,
                "weekly hours source sentence"
            )
        ]
    )

    passed = result["passed_conditions"][0]

    assert passed["condition_id"] == "c-evidence"
    assert passed["evidence_snippets"] == [
        "weekly hours source sentence"
    ]


if __name__ == "__main__":

    test_all_conditions_pass()
    test_single_condition_failure()
    test_multiple_condition_failures()
    test_unsupported_operator()
    test_missing_input_field()
    test_null_value_handling()
    test_evidence_snippets_are_linked()
    print("test_condition_operator_evaluator passed")

