import json
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
APP_DIR = ROOT_DIR / "match_agent_v0.8" / "match_agent_v0.8"
DEFAULT_CASE_PATH = (
    ROOT_DIR
    / "tests"
    / "fixtures"
    / "mock_company_cases"
    / "04_hana_machine_expected.json"
)
DEFAULT_OUTPUT_PATH = (
    ROOT_DIR
    / "output"
    / "mock_company_case_checks"
    / "04_hana_machine_input_schema_audit.json"
)

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from services.rule_engine_domain_adapter import (  # noqa: E402
    adapt_general_company_request_to_rule_engine,
)


REQUIRED_FOR_REPLACEMENT_WINDOW = [
    "replacement_worker.hire_date",
    "replacement_worker.employment_duration_days",
    "company.insured_employee_count",
    "leave_event.start_date",
    "leave_event.end_date",
    "leave_event.type",
]


def get_nested_value(payload, dotted_path):
    current = payload

    for part in dotted_path.split("."):
        if not isinstance(current, dict):
            return None
        if part not in current:
            return None
        current = current[part]

    return current


def build_readiness_report(case_path=DEFAULT_CASE_PATH):
    case_data = json.loads(
        Path(case_path).read_text(encoding="utf-8")
    )
    payload = case_data.get(
        "recommendation_engine_input_draft",
        {},
    )
    adapter_result = adapt_general_company_request_to_rule_engine(
        payload
    )
    rule_input = adapter_result.get("rule_input", {})

    field_status = []
    for field in REQUIRED_FOR_REPLACEMENT_WINDOW:
        payload_value = get_nested_value(payload, field)
        rule_input_value = get_nested_value(rule_input, field)
        field_status.append(
            {
                "field": field,
                "present_in_payload": payload_value is not None,
                "payload_value": payload_value,
                "present_in_rule_input": rule_input_value is not None,
                "rule_input_value": rule_input_value,
            }
        )

    missing_from_rule_input = [
        item["field"]
        for item in field_status
        if not item["present_in_rule_input"]
    ]
    can_validate_replacement_hire_window = not missing_from_rule_input

    return {
        "case_id": case_data.get("case_id"),
        "target_policy_id": case_data.get(
            "expected_result",
            {},
        )
        .get("primary_assertion", {})
        .get("policy_id"),
        "adapter_result": adapter_result,
        "required_field_status": field_status,
        "actual_result_generation_path": {
            "available_entrypoint": "services.demo_recommendation_orchestrator.run_demo_recommendation_pipeline(payload)",
            "payload_source": str(Path(case_path)),
            "actual_result_is_comparable_now": False,
            "reason": "The current rule_input preserves the fields needed for the replacement hire-window check, but the current demo_fixture policy source does not load replacement_workshare_support. The expected-result assertion cannot pass until an approved test policy source containing replacement_workshare_support is used and code-based replacement-window evaluation exists.",
        },
        "current_structure_feasibility": {
            "can_run_pipeline_with_payload": True,
            "can_validate_replacement_hire_window": can_validate_replacement_hire_window,
            "missing_from_rule_input": missing_from_rule_input,
        },
    }


def main():
    report = build_readiness_report()
    DEFAULT_OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    DEFAULT_OUTPUT_PATH.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "output_path": str(DEFAULT_OUTPUT_PATH),
                "can_run_pipeline_with_payload": report[
                    "current_structure_feasibility"
                ]["can_run_pipeline_with_payload"],
                "can_validate_replacement_hire_window": report[
                    "current_structure_feasibility"
                ]["can_validate_replacement_hire_window"],
                "missing_from_rule_input": report[
                    "current_structure_feasibility"
                ]["missing_from_rule_input"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
