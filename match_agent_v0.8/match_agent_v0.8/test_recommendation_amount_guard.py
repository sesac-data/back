from data.mock_data import (
    mock_company_data
)

from services.calculation_service import (
    calculate_employee_supports
)

from services.policy_extractor import (
    load_policy_json
)

from services.recommendation_service import (
    generate_recommendation_result
)


def test_recommendation_amount_guard():

    policy_keys = [
        "parental_leave_reduction_support",
        "replacement_workshare_support",
        "worklife_balance_45_support",
        "childcare_flexible_start_support",
        "working_hours_reduction_support",
        "flexible_work_incent",
        "flexible_work_system_support"
    ]

    policies = [
        load_policy_json(
            key
        )
        for key in policy_keys
    ]

    employee_results = calculate_employee_supports(
        mock_company_data,
        mock_company_data[
            "employees"
        ],
        policies
    )

    recommendation_result = generate_recommendation_result(
        employee_results,
        max_supported_people=5
    )

    for employee in recommendation_result.get(
        "selected_recommendations",
        []
    ):

        support_keys = [
            support.get(
                "amount_normalization",
                {}
            ).get(
                "policy_key"
            )
            for support in employee.get(
                "selected_supports",
                []
            )
        ]

        assert "flexible_work_system_support" not in support_keys

        assert len(support_keys) == len(
            set(
                support_keys
            )
        )

        assert employee[
            "total_amount"
        ] <= 22500000


if __name__ == "__main__":

    test_recommendation_amount_guard()

    print(
        "test_recommendation_amount_guard passed"
    )
