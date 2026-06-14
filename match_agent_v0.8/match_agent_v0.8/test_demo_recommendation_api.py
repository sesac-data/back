from services.demo_recommendation_orchestrator import (
    run_demo_recommendation_pipeline,
    validate_demo_recommendation_request,
)
import services.demo_recommendation_orchestrator as orchestrator


def demo_request(
    employer_cost_items=None,
    policy_source=None,
):

    request = {
        "company":
            {
                "company_name":
                    "Demo Company",
                "size":
                    "small",
            },
        "employee":
            {
                "employee_name":
                    "Demo Employee",
            },
        "leave_event":
            {
                "leave_type":
                    "parental_leave",
                "start_date":
                    "2026-07-01",
                "end_date":
                    "2026-10-31",
                "has_replacement_worker":
                    False,
            },
    }

    if employer_cost_items is not None:

        request[
            "employer_cost_items"
        ] = employer_cost_items

    if policy_source is not None:

        request[
            "policy_source"
        ] = policy_source

    return request


def explicit_cost_items():

    return [
        {
            "cost_id":
                "COST-GLOBAL-001",
            "cost_type":
                "administrative_cost",
            "description":
                "TEST FIXTURE explicit administrative cost",
            "amount":
                1000,
            "applies_to_policy_ids":
                [],
        },
        {
            "cost_id":
                "COST-POLICY-B-001",
            "cost_type":
                "replacement_worker_salary",
            "description":
                "TEST FIXTURE explicit replacement worker salary",
            "amount":
                700,
            "applies_to_policy_ids":
                [
                    "smoke-optimal-b"
                ],
        },
        {
            "cost_id":
                "COST-AND-001",
            "cost_type":
                "combined_operation_cost",
            "description":
                "TEST FIXTURE explicit cost only when A and B are both present",
            "amount":
                500,
            "applies_to_policy_ids":
                [
                    "smoke-optimal-a",
                    "smoke-optimal-b",
                ],
        },
    ]


def test_normal_request_returns_recommended_combination():

    result = run_demo_recommendation_pipeline(
        demo_request(
            explicit_cost_items()
        )
    )

    assert result["recommended_combination"]["policy_ids"] == [
        "smoke-optimal-a"
    ]
    assert result["errors"] == []


def test_lowest_net_cost_is_selected():

    result = run_demo_recommendation_pipeline(
        demo_request(
            explicit_cost_items()
        )
    )

    assert result["recommended_combination"]["net_employer_cost"] == 600


def test_highest_subsidy_combination_can_be_alternative():

    result = run_demo_recommendation_pipeline(
        demo_request(
            explicit_cost_items()
        )
    )

    assert result["recommended_combination"]["total_subsidy_amount"] == 400
    assert result["alternative_combinations"][-1]["policy_ids"] == [
        "smoke-optimal-a",
        "smoke-optimal-b",
    ]
    assert result["alternative_combinations"][-1]["total_subsidy_amount"] == 720


def test_invalid_request_schema_returns_errors():

    validation = validate_demo_recommendation_request(
        {
            "company": {},
            "employee": {},
        }
    )

    assert validation["valid"] is False
    assert validation["errors"][0]["field"] == "leave_event"


def test_missing_employer_cost_items_defaults_to_empty_list():

    result = run_demo_recommendation_pipeline(
        demo_request()
    )

    assert result["recommended_combination"]["net_employer_cost"] == -720
    assert result["errors"] == []


def test_empty_employer_cost_items_is_valid():

    result = run_demo_recommendation_pipeline(
        demo_request(
            []
        )
    )

    assert result["recommended_combination"]["net_employer_cost"] == -720
    assert result["errors"] == []


def test_meta_marks_demo_fixture():

    result = run_demo_recommendation_pipeline(
        demo_request(
            explicit_cost_items()
        )
    )

    assert result["meta"]["is_demo"] is True
    assert result["meta"]["data_source"] == "demo_fixture"
    assert result["meta"]["loaded_policy_count"] > 0
    assert result["meta"]["policy_source"]["data_source"] == "demo_fixture"
    assert result["meta"]["policy_source"]["is_demo"] is True
    assert result["meta"]["policy_source"]["fixture"] == "optimal_combination"


def test_policy_db_source_uses_requested_loader_source():

    original_loader = orchestrator.load_approved_policies
    observed_sources = []

    def fake_loader(
        source="demo_fixture"
    ):

        observed_sources.append(
            source
        )
        base_result = original_loader()

        return {
            "candidate_policies":
                base_result[
                    "candidate_policies"
                ],
            "policy_source":
                {
                    "data_source":
                        "policy_db",
                    "is_demo":
                        False,
                    "table":
                        "subsidy_policies",
                },
            "errors":
                [],
        }

    orchestrator.load_approved_policies = fake_loader

    try:

        result = run_demo_recommendation_pipeline(
            demo_request(
                explicit_cost_items(),
                policy_source="policy_db",
            )
        )

    finally:

        orchestrator.load_approved_policies = original_loader

    assert observed_sources == [
        "policy_db"
    ]
    assert result["meta"]["data_source"] == "policy_db"
    assert result["meta"]["is_demo"] is False
    assert result["meta"]["policy_source"]["table"] == "subsidy_policies"
    assert result["meta"]["loaded_policy_count"] > 0
    assert result["recommended_combination"]["policy_ids"] == [
        "smoke-optimal-a"
    ]


def test_policy_db_loader_error_does_not_fallback_to_fixture():

    original_loader = orchestrator.load_approved_policies

    def fake_loader(
        source="demo_fixture"
    ):

        return {
            "candidate_policies":
                [],
            "policy_source":
                {
                    "data_source":
                        source,
                    "is_demo":
                        False,
                    "table":
                        "subsidy_policies",
                },
            "errors":
                [
                    {
                        "field":
                            "policy_db",
                        "reason":
                            "approved_policy_not_found",
                    }
                ],
        }

    orchestrator.load_approved_policies = fake_loader

    try:

        result = run_demo_recommendation_pipeline(
            demo_request(
                explicit_cost_items(),
                policy_source="policy_db",
            )
        )

    finally:

        orchestrator.load_approved_policies = original_loader

    assert result["recommended_combination"] is None
    assert result["errors"][0]["reason"] == "approved_policy_not_found"
    assert result["meta"]["data_source"] == "policy_db"
    assert result["meta"]["loaded_policy_count"] == 0


def test_unsupported_policy_source_returns_schema_error():

    validation = validate_demo_recommendation_request(
        demo_request(
            explicit_cost_items(),
            policy_source="spreadsheet",
        )
    )

    assert validation["valid"] is False
    assert validation["errors"][0]["field"] == "policy_source"
    assert validation["errors"][0]["reason"] == "unsupported_policy_source"


if __name__ == "__main__":

    test_normal_request_returns_recommended_combination()
    test_lowest_net_cost_is_selected()
    test_highest_subsidy_combination_can_be_alternative()
    test_invalid_request_schema_returns_errors()
    test_missing_employer_cost_items_defaults_to_empty_list()
    test_empty_employer_cost_items_is_valid()
    test_meta_marks_demo_fixture()
    test_policy_db_source_uses_requested_loader_source()
    test_policy_db_loader_error_does_not_fallback_to_fixture()
    test_unsupported_policy_source_returns_schema_error()
    print("test_demo_recommendation_api passed")
