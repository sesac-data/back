import json
from pathlib import Path

from services.minimum_recommendation_flow import (
    run_minimum_recommendation_flow
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "data"
    / "policy_json"
    / "approved_minimum_recommendation_fixture.json"
)


def load_fixture():

    with FIXTURE_PATH.open(
        "r",
        encoding="utf-8"
    ) as fixture_file:

        return json.load(
            fixture_file
        )


def mock_general_company():

    return {
        "company": {
            "company_name": "Minimum Flow Company",
            "company_size": "30인 미만",
            "employee_count": 1,
            "systems": {
                "attendance_system": True
            },
            "labor_agreement": True,
            "contract_changed": True
        },
        "employees": []
    }


def mock_employee():

    return {
        "employee_id": "emp-001",
        "name": "Minimum Employee",
        "child_age": 5,
        "weekly_work_hours": 40
    }


def mock_leave_event():

    return {
        "leave_event_id": "leave-001",
        "leave_type": "childcare_flexible_start",
        "start_date": "2026-07-01",
        "end_date": "2027-06-30"
    }


def test_minimum_recommendation_flow_uses_approved_policy_fixture():

    result = run_minimum_recommendation_flow(
        load_fixture(),
        mock_general_company(),
        mock_employee(),
        mock_leave_event()
    )

    assert result["status"] == "eligible"
    assert result["eligible"] is True
    assert result["expected_amount"] == 3600000
    assert len(result["passed_conditions"]) == 5
    assert result["failed_conditions"] == []
    assert result["unsupported_conditions"] == []
    assert any(
        "expected_amount=3600000" in step
        for step in result["calculation_steps"]
    )
    assert result["evidence_snippets"]
    assert any(
        "30" in snippet
        for snippet in result["evidence_snippets"]
    )


def test_minimum_recommendation_flow_blocks_unapproved_policy():

    policy = load_fixture()
    policy["review_status"] = "needs_review"

    result = run_minimum_recommendation_flow(
        policy,
        mock_general_company(),
        mock_employee(),
        mock_leave_event()
    )

    assert result["status"] == "needs_review"
    assert result["eligible"] is False
    assert "not approved" in result["calculation_steps"][0]


if __name__ == "__main__":

    test_minimum_recommendation_flow_uses_approved_policy_fixture()
    test_minimum_recommendation_flow_blocks_unapproved_policy()
    print("test_minimum_recommendation_flow passed")
