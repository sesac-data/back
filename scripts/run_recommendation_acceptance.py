import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
APP_DIR = ROOT_DIR / "match_agent_v0.8" / "match_agent_v0.8"
SCENARIO_DIR = ROOT_DIR / "data" / "acceptance_scenarios"
OUTPUT_DIR = ROOT_DIR / "output" / "verification"
REPORT_PATH = OUTPUT_DIR / "backend-report.json"
SCENARIOS = [
    "base",
    "bonus",
    "capped",
    "conflict",
    "requires",
    "employer_net_cost",
    "optimal_combination",
]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from scripts.run_recommendation_smoke import calculate_policy  # noqa: E402
from services.calculation_service import (  # noqa: E402
    normalize_policy_calculation_result,
)
from services.combination_amount_summarizer import (  # noqa: E402
    summarize_combination_amounts,
)
from services.employer_net_cost_calculator import (  # noqa: E402
    calculate_employer_net_costs,
)
from services.optimal_combination_selector import (  # noqa: E402
    select_optimal_combination,
)
from services.policy_combination_generator import (  # noqa: E402
    generate_valid_policy_combinations,
)


def normalize_policy_ids(items):
    return [
        list(item)
        for item in items
    ]


def as_expected_list(value):
    if isinstance(value, list):
        return value
    return [value]


def load_acceptance_scenario(scenario):
    path = SCENARIO_DIR / f"{scenario}.json"
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def execute_acceptance_fixture(fixture):
    errors = []
    input_snapshot = deepcopy(fixture.get("input", {}))
    candidate_policies = deepcopy(fixture.get("candidate_policies", []))
    rule_input = input_snapshot.get("rule_input", {})
    requested_months = input_snapshot.get("requested_months")
    standardized_policy_results = []

    for policy in candidate_policies:
        policy_id = policy.get("policy_id") or policy.get("policy_key")

        try:
            raw_result = calculate_policy(
                policy,
                rule_input,
                requested_months,
            )
            standardized_policy_results.append(
                normalize_policy_calculation_result(
                    policy,
                    raw_result,
                )
            )
        except Exception as exc:
            errors.append({
                "stage": "policy_calculation",
                "policy_id": policy_id,
                "type": exc.__class__.__name__,
                "message": str(exc),
            })

    try:
        combination_result = generate_valid_policy_combinations(
            candidate_policies
        )
    except Exception as exc:
        combination_result = {
            "valid_combinations": [],
            "rejected_combinations": [],
            "errors": [
                {
                    "stage": "generate_valid_policy_combinations",
                    "type": exc.__class__.__name__,
                    "message": str(exc),
                }
            ],
        }

    errors.extend(
        {
            "stage": "generate_valid_policy_combinations",
            **error,
        }
        for error in combination_result.get("errors", [])
    )

    valid_combinations = combination_result.get("valid_combinations", [])
    rejected_combinations = [
        {
            "stage": "policy_combination_generation",
            **combination,
        }
        for combination in combination_result.get("rejected_combinations", [])
    ]

    try:
        summary_result = summarize_combination_amounts(
            valid_combinations,
            standardized_policy_results,
        )
    except Exception as exc:
        summary_result = {
            "summarized_combinations": [],
            "rejected_combinations": [],
            "errors": [
                {
                    "stage": "summarize_combination_amounts",
                    "type": exc.__class__.__name__,
                    "message": str(exc),
                }
            ],
        }

    errors.extend(
        {
            "stage": "summarize_combination_amounts",
            **error,
        }
        for error in summary_result.get("errors", [])
    )

    rejected_combinations.extend(
        {
            "stage": "combination_amount_summarization",
            **combination,
        }
        for combination in summary_result.get("rejected_combinations", [])
    )

    employer_net_cost_result = (
        calculate_employer_net_costs(
            summary_result.get("summarized_combinations", []),
            input_snapshot.get("employer_cost_items", []),
        )
        if "employer_cost_items" in input_snapshot
        else None
    )

    optimal_combination_result = (
        select_optimal_combination(
            employer_net_cost_result.get("cost_calculated_combinations", []),
            rejected_combinations,
        )
        if employer_net_cost_result is not None
        else None
    )

    return {
        "scenario":
            fixture.get("scenario"),
        "fixture_notice":
            fixture.get("fixture_notice"),
        "input":
            input_snapshot,
        "candidate_policies":
            candidate_policies,
        "standardized_policy_results":
            standardized_policy_results,
        "valid_combinations":
            valid_combinations,
        "rejected_combinations":
            rejected_combinations,
        "summarized_combinations":
            summary_result.get("summarized_combinations", []),
        "employer_net_cost_result":
            employer_net_cost_result,
        "optimal_combination_result":
            optimal_combination_result,
        "errors":
            errors,
    }


def collect_rejection_codes(rejected_combinations):
    codes = []

    for combination in rejected_combinations:
        for reason in combination.get("reasons", []):
            code = reason.get("type")
            if code and code not in codes:
                codes.append(code)

    return sorted(codes)


def collect_amounts(summarized_combinations, field):
    return [
        combination.get(field)
        for combination in summarized_combinations
    ]


def collect_cost_amounts(cost_calculated_combinations, field):
    return [
        combination.get(field)
        for combination in cost_calculated_combinations
    ]


def collect_applied_cost_item_ids(cost_calculated_combinations):
    return [
        [
            cost_item.get("cost_id")
            for cost_item in combination.get("applied_cost_items", [])
        ]
        for combination in cost_calculated_combinations
    ]


def collect_alternative_policy_ids(optimal_combination_result):
    return [
        combination.get("policy_ids", [])
        for combination in optimal_combination_result.get(
            "alternative_combinations",
            [],
        )
    ]


def has_evidence_and_steps(result):
    for policy_result in result.get("standardized_policy_results", []):
        if not policy_result.get("evidence_snippets"):
            return False
        if not policy_result.get("calculation_steps"):
            return False

    for combination in result.get("summarized_combinations", []):
        if not combination.get("evidence_snippets"):
            return False
        if not combination.get("calculation_steps"):
            return False

    for combination in result.get("rejected_combinations", []):
        for reason in combination.get("reasons", []):
            details = reason.get("details", {})
            if not details.get("evidence_snippets"):
                return False

    return True


def has_cost_steps(result):
    employer_net_cost_result = result.get("employer_net_cost_result")

    if employer_net_cost_result is None:
        return True

    for combination in employer_net_cost_result.get(
        "cost_calculated_combinations",
        [],
    ):
        calculation_steps = combination.get("calculation_steps", [])
        if not calculation_steps:
            return False

        if not any(
            step.get("formula")
            == "net_employer_cost = total_employer_cost - total_subsidy_amount"
            for step in calculation_steps
        ):
            return False

    return True


def build_actual(result):
    summarized = result.get("summarized_combinations", [])
    rejected = result.get("rejected_combinations", [])

    actual = {
        "valid_combination_count":
            len(summarized),
        "rejected_combination_count":
            len(rejected),
        "expected_policy_ids":
            normalize_policy_ids(
                combination.get("policy_ids", [])
                for combination in summarized
            ),
        "expected_rejected_policy_ids":
            normalize_policy_ids(
                combination.get("policy_ids", [])
                for combination in rejected
            ),
        "total_base_amount":
            collect_amounts(
                summarized,
                "total_base_amount",
            ),
        "total_bonus_amount":
            collect_amounts(
                summarized,
                "total_bonus_amount",
            ),
        "total_subsidy_amount":
            collect_amounts(
                summarized,
                "total_subsidy_amount",
            ),
        "expected_error_codes":
            collect_rejection_codes(
                rejected
            ),
    }

    employer_net_cost_result = result.get(
        "employer_net_cost_result"
    )

    if employer_net_cost_result is not None:
        cost_calculated_combinations = employer_net_cost_result.get(
            "cost_calculated_combinations",
            [],
        )
        actual.update({
            "total_employer_cost":
                collect_cost_amounts(
                    cost_calculated_combinations,
                    "total_employer_cost",
                ),
            "net_employer_cost":
                collect_cost_amounts(
                    cost_calculated_combinations,
                    "net_employer_cost",
                ),
            "expected_applied_cost_item_ids":
                collect_applied_cost_item_ids(
                    cost_calculated_combinations
                ),
        })

    optimal_combination_result = result.get(
        "optimal_combination_result"
    )

    if optimal_combination_result is not None:
        recommended_combination = optimal_combination_result.get(
            "recommended_combination"
        ) or {}
        actual.update({
            "recommended_policy_ids":
                recommended_combination.get(
                    "policy_ids"
                ),
            "recommended_net_employer_cost":
                recommended_combination.get(
                    "net_employer_cost"
                ),
            "recommended_total_subsidy_amount":
                recommended_combination.get(
                    "total_subsidy_amount"
                ),
            "alternative_policy_ids":
                collect_alternative_policy_ids(
                    optimal_combination_result
                ),
        })

    return actual


def compare_field(field, expected, actual):
    expected_value = expected.get(field)
    actual_value = actual.get(field)

    if field.startswith("total_") or field == "net_employer_cost":
        expected_value = as_expected_list(expected_value)

    if expected_value != actual_value:
        return {
            "field": field,
            "expected": expected_value,
            "actual": actual_value,
            "message": (
                f"{field} mismatch: expected {expected_value}, "
                f"actual {actual_value}"
            ),
        }

    return None


def run_acceptance_scenario(scenario):
    acceptance_fixture = load_acceptance_scenario(scenario)
    expected = acceptance_fixture.get("expected", {})

    result = execute_acceptance_fixture(
        acceptance_fixture
    )
    actual = build_actual(result)
    failures = []

    for field in [
        "valid_combination_count",
        "rejected_combination_count",
        "expected_policy_ids",
        "expected_rejected_policy_ids",
        "total_base_amount",
        "total_bonus_amount",
        "total_subsidy_amount",
        "expected_error_codes",
        "total_employer_cost",
        "net_employer_cost",
        "expected_applied_cost_item_ids",
        "recommended_policy_ids",
        "recommended_net_employer_cost",
        "recommended_total_subsidy_amount",
        "alternative_policy_ids",
    ]:
        if field not in expected:
            continue

        failure = compare_field(
            field,
            expected,
            actual,
        )

        if failure:
            failures.append(failure)

    if result.get("errors"):
        failures.append({
            "field": "errors",
            "expected": [],
            "actual": result.get("errors"),
            "message": "scenario returned unexpected errors",
        })

    employer_net_cost_result = result.get(
        "employer_net_cost_result"
    )

    if employer_net_cost_result and employer_net_cost_result.get("errors"):
        failures.append({
            "field": "employer_net_cost_result.errors",
            "expected": [],
            "actual": employer_net_cost_result.get("errors"),
            "message": "employer net cost calculation returned unexpected errors",
        })

    optimal_combination_result = result.get(
        "optimal_combination_result"
    )

    if optimal_combination_result and optimal_combination_result.get("errors"):
        failures.append({
            "field": "optimal_combination_result.errors",
            "expected": [],
            "actual": optimal_combination_result.get("errors"),
            "message": "optimal combination selection returned unexpected errors",
        })

    if not has_evidence_and_steps(result):
        failures.append({
            "field": "evidence_snippets/calculation_steps",
            "expected": "present",
            "actual": "missing",
            "message": "evidence_snippets or calculation_steps are missing",
        })

    if not has_cost_steps(result):
        failures.append({
            "field": "employer_net_cost_calculation_steps",
            "expected": "present",
            "actual": "missing",
            "message": "employer net cost calculation steps are missing",
        })

    return {
        "scenario":
            scenario,
        "status":
            "PASS" if not failures else "FAIL",
        "expected":
            deepcopy(expected),
        "actual":
            actual,
        "failures":
            failures,
    }


def write_report(report):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run backend recommendation acceptance checks."
    )
    parser.add_argument(
        "--scenario",
        choices=SCENARIOS,
        help="Run one acceptance scenario. If omitted, all scenarios run.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    scenarios = [args.scenario] if args.scenario else SCENARIOS
    scenario_reports = [
        run_acceptance_scenario(scenario)
        for scenario in scenarios
    ]
    failed = [
        item
        for item in scenario_reports
        if item["status"] != "PASS"
    ]
    report = {
        "status":
            "PASS" if not failed else "FAIL",
        "scenarios":
            scenario_reports,
        "report_path":
            str(REPORT_PATH),
    }

    write_report(report)
    print(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        )
    )

    if failed:
        for item in failed:
            for failure in item.get("failures", []):
                print(
                    f"[acceptance] {item['scenario']}: "
                    f"{failure['message']}",
                    file=sys.stderr,
                )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
