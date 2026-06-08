import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
APP_DIR = ROOT_DIR / "match_agent_v0.8" / "match_agent_v0.8"
SCENARIO_DIR = ROOT_DIR / "data" / "smoke_scenarios"
OUTPUT_DIR = ROOT_DIR / "output" / "smoke"
SCENARIOS = ["base", "bonus", "capped", "conflict", "requires"]

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from services.calculation_service import (  # noqa: E402
    calculate_base_policy_support,
    calculate_conditional_bonus_policy_support,
    get_support_calculation_type,
    normalize_policy_calculation_result,
)
from services.combination_amount_summarizer import (  # noqa: E402
    summarize_combination_amounts,
)
from services.policy_combination_generator import (  # noqa: E402
    generate_valid_policy_combinations,
)


def load_scenario(scenario):
    scenario_path = SCENARIO_DIR / f"{scenario}.json"

    with scenario_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def calculate_policy(policy, rule_input, requested_months):
    calculation_type = get_support_calculation_type(policy)

    if calculation_type == "conditional_bonus":
        return calculate_conditional_bonus_policy_support(
            policy,
            rule_input,
            requested_months,
        )

    return calculate_base_policy_support(
        policy,
        rule_input,
        requested_months,
    )


def run_scenario(scenario):
    errors = []

    try:
        fixture = load_scenario(scenario)
    except Exception as exc:
        result = {
            "scenario": scenario,
            "input": {},
            "candidate_policies": [],
            "standardized_policy_results": [],
            "valid_combinations": [],
            "rejected_combinations": [],
            "summarized_combinations": [],
            "errors": [
                {
                    "stage": "load_scenario",
                    "type": exc.__class__.__name__,
                    "message": str(exc),
                }
            ],
        }
        write_result(scenario, result)
        return result

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
            errors.append(
                {
                    "stage": "policy_calculation",
                    "policy_id": policy_id,
                    "type": exc.__class__.__name__,
                    "message": str(exc),
                }
            )

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

    result = {
        "scenario": scenario,
        "fixture_notice": fixture.get("fixture_notice"),
        "input": input_snapshot,
        "candidate_policies": candidate_policies,
        "standardized_policy_results": standardized_policy_results,
        "valid_combinations": valid_combinations,
        "rejected_combinations": rejected_combinations,
        "summarized_combinations": summary_result.get(
            "summarized_combinations",
            [],
        ),
        "errors": errors,
    }

    write_result(scenario, result)
    return result


def write_result(scenario, result):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{scenario}.json"

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run deterministic recommendation smoke scenarios."
    )
    parser.add_argument(
        "--scenario",
        choices=SCENARIOS,
        help="Run a single smoke scenario. If omitted, all scenarios run.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    scenarios = [args.scenario] if args.scenario else SCENARIOS
    results = [
        run_scenario(scenario)
        for scenario in scenarios
    ]

    payload = results[0] if args.scenario else results

    print(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
