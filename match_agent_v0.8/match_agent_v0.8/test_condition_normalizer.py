from services.condition_normalizer import (
    normalize_policy_conditions
)

from services.policy_validator import (
    has_validation_errors,
    validate_policy_json
)


def test_condition_normalizer():

    policy_json = {
        "policy_name":
            "condition normalizer test",
        "support_items": [
            {
                "support_type":
                    "test support",
                "target_conditions":
                    [
                        {
                            "type":
                                "business_operation_period_years",
                            "min":
                                1
                        }
                    ],
                "conditions":
                    [
                        {
                            "type":
                                "requires_time_tracking_system"
                        },
                        {
                            "type":
                                "company_employee_count",
                            "max":
                                29
                        },
                        {
                            "type":
                                "investment_cost_support_max",
                            "value":
                                2000000
                        }
                    ],
                "support":
                    {
                        "yearly_max_amount":
                            1
                    },
                "evidence_snippets":
                    [
                        "test evidence"
                    ]
            }
        ],
        "risk_conditions":
            []
    }

    normalized = normalize_policy_conditions(
        policy_json
    )

    conditions = (
        normalized["support_items"][0][
            "conditions"
        ]
    )

    assert conditions == [
        {
            "type":
                "requires_attendance_system",
            "value":
                True
        },
        {
            "type":
                "employee_count",
            "max":
                29,
            "min":
                None
        }
    ]

    support_item = normalized[
        "support_items"
    ][0]

    assert support_item[
        "support_calculation_notes"
    ][0]["type"] == "investment_cost_support_max"

    assert support_item[
        "important_conditions"
    ][0]["type"] == "business_operation_period_years"

    validation_result = validate_policy_json(
        normalized
    )

    assert not has_validation_errors(
        validation_result
    )


if __name__ == "__main__":

    test_condition_normalizer()

    print(
        "test_condition_normalizer passed"
    )
