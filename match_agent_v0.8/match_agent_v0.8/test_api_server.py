from fastapi.testclient import TestClient

from api_server import app


client = TestClient(
    app
)


def demo_payload(
    policy_source="demo_fixture"
):

    return {
        "policy_source":
            policy_source,
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
        "employer_cost_items":
            [],
    }


def test_health_returns_ok():

    response = client.get(
        "/health"
    )

    assert response.status_code == 200
    assert response.json() == {
        "status":
            "ok"
    }


def test_demo_fixture_recommendation_post_returns_result():

    response = client.post(
        "/api/demo/recommendations/calculate",
        json=demo_payload(),
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["meta"]["data_source"] == "demo_fixture"
    assert payload["meta"]["loaded_policy_count"] > 0
    assert payload["recommended_combination"]["policy_ids"] == [
        "smoke-optimal-a",
        "smoke-optimal-b",
    ]


def test_policy_db_recommendation_post_returns_success_or_structured_error():

    response = client.post(
        "/api/demo/recommendations/calculate",
        json=demo_payload(
            "policy_db"
        ),
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["meta"]["data_source"] == "policy_db"
    assert payload["meta"]["is_demo"] is False
    assert "errors" in payload

    if payload["errors"]:

        error_reasons = {
            error.get(
                "reason"
            )
            for error in payload["errors"]
        }

        assert error_reasons & {
            "policy_db_connection_failed",
            "policy_db_table_not_found",
            "approved_policy_not_found",
            "policy_db_invalid_json",
            "policy_db_review_status_mismatch",
            "no_recommendation_candidates",
        }

    else:

        assert payload["meta"]["loaded_policy_count"] > 0
        assert payload["recommended_combination"] is not None


def test_unsupported_policy_source_returns_existing_error_structure():

    response = client.post(
        "/api/demo/recommendations/calculate",
        json=demo_payload(
            "spreadsheet"
        ),
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["recommended_combination"] is None
    assert payload["errors"][0]["field"] == "policy_source"
    assert payload["errors"][0]["reason"] == "unsupported_policy_source"


def test_local_dev_cors_origin_is_allowed():

    response = client.options(
        "/api/demo/recommendations/calculate",
        headers={
            "Origin":
                "http://127.0.0.1:5173",
            "Access-Control-Request-Method":
                "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers[
        "access-control-allow-origin"
    ] == "http://127.0.0.1:5173"


if __name__ == "__main__":

    test_health_returns_ok()
    test_demo_fixture_recommendation_post_returns_result()
    test_policy_db_recommendation_post_returns_success_or_structured_error()
    test_unsupported_policy_source_returns_existing_error_structure()
    test_local_dev_cors_origin_is_allowed()
    print("test_api_server passed")
