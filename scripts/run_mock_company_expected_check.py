import argparse
import json
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
APP_DIR = ROOT_DIR / "match_agent_v0.8" / "match_agent_v0.8"
FIXTURES_DIR = (
    ROOT_DIR / "tests" / "fixtures" / "mock_company_cases"
)
DEFAULT_CASE_PATH = (
    FIXTURES_DIR / "04_hana_machine_expected.json"
)
DEFAULT_OUTPUT_PATH = (
    ROOT_DIR
    / "output"
    / "mock_company_case_checks"
    / "04_hana_machine_actual_vs_expected.json"
)

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from services.demo_recommendation_orchestrator import (  # noqa: E402
    run_demo_recommendation_pipeline,
)
import services.demo_recommendation_orchestrator as orchestrator  # noqa: E402
from services.approved_policy_loader import (  # noqa: E402
    load_approved_policies,
)


TEST_POLICY_FIXTURE_NAME = "hana_machine_replacement_workshare"


def collect_policy_ids_from_combinations(combinations):
    policy_ids = []

    for combination in combinations or []:
        for policy_id in combination.get("policy_ids", []) or []:
            if policy_id not in policy_ids:
                policy_ids.append(policy_id)

    return policy_ids


def collect_rejected_policy_ids(rejected_combinations):
    policy_ids = []

    for combination in rejected_combinations or []:
        for policy_id in combination.get("policy_ids", []) or []:
            if policy_id not in policy_ids:
                policy_ids.append(policy_id)

    return policy_ids


def build_comparison(case_path=DEFAULT_CASE_PATH):
    case_data = json.loads(
        Path(case_path).read_text(encoding="utf-8")
    )
    expected = case_data.get("expected_result", {})
    expected_primary = expected.get("primary_assertion", {})
    expected_comparison = expected.get(
        "expected_recommendation_comparison",
        {},
    )
    payload = case_data.get(
        "recommendation_engine_input_draft",
        {},
    )

    original_loader = orchestrator.load_approved_policies

    def test_policy_loader(
        source="demo_fixture"
    ):

        return load_approved_policies(
            source=source,
            fixture_name=TEST_POLICY_FIXTURE_NAME,
        )

    orchestrator.load_approved_policies = test_policy_loader

    try:

        actual = run_demo_recommendation_pipeline(payload)

    finally:

        orchestrator.load_approved_policies = original_loader
    recommended = actual.get("recommended_combination")
    alternatives = actual.get("alternative_combinations", [])
    rejected = actual.get("rejected_combinations", [])

    recommended_policy_ids = (
        recommended.get("policy_ids", [])
        if isinstance(recommended, dict)
        else []
    )
    alternative_policy_ids = collect_policy_ids_from_combinations(
        alternatives
    )
    rejected_policy_ids = collect_rejected_policy_ids(
        rejected
    )

    target_policy_id = expected_primary.get("policy_id")
    expected_reason_code = expected_primary.get(
        "expected_reason_code"
    )

    target_is_recommended = target_policy_id in recommended_policy_ids
    target_is_alternative = target_policy_id in alternative_policy_ids
    target_is_rejected = target_policy_id in rejected_policy_ids
    target_present_anywhere = (
        target_is_recommended
        or target_is_alternative
        or target_is_rejected
    )
    reason_code_present = any(
        expected_reason_code
        in json.dumps(item, ensure_ascii=False)
        for item in rejected
    )

    comparison_passed = (
        target_is_rejected
        and reason_code_present
        and not target_is_recommended
        and not target_is_alternative
    )

    return {
        "case_id": case_data.get("case_id"),
        "target_policy_id": target_policy_id,
        "expected": {
            "status": expected_primary.get("expected_status"),
            "reason_code": expected_reason_code,
            "expected_rejected_policy_ids": expected_comparison.get(
                "expected_rejected_policy_ids",
                [],
            ),
            "expected_amount": expected_comparison.get(
                "amount_assertion",
                {},
            ).get("replacement_workshare_support_expected_amount"),
        },
        "actual_summary": {
            "recommended_policy_ids": recommended_policy_ids,
            "alternative_policy_ids": alternative_policy_ids,
            "rejected_policy_ids": rejected_policy_ids,
            "errors": actual.get("errors", []),
            "meta": actual.get("meta", {}),
            "test_policy_fixture":
                TEST_POLICY_FIXTURE_NAME,
        },
        "comparison": {
            "passed": comparison_passed,
            "target_policy_present_anywhere": target_present_anywhere,
            "target_is_recommended": target_is_recommended,
            "target_is_alternative": target_is_alternative,
            "target_is_rejected": target_is_rejected,
            "expected_reason_code_present": reason_code_present,
            "actual_result_is_comparable": target_present_anywhere,
            "notes": [
                "This runner injects a test-only approved fixture containing replacement_workshare_support.",
                "The replacement hire-window condition is evaluated by the shared condition evaluator using a relative date expected value.",
                "No operating DB write, policy approval automation, frontend change, or source policy JSON mutation is performed.",
            ],
        },
        "actual_result": actual,
    }


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run actual-vs-expected comparison "
            "for a mock company case."
        ),
    )
    parser.add_argument(
        "--case",
        type=str,
        default=None,
        help=(
            "Path to expected JSON fixture. "
            "Defaults to 04_hana_machine_expected.json."
        ),
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help=(
            "Path for output JSON. "
            "Defaults to output/mock_company_case_checks/"
            "<case_id>_actual_vs_expected.json."
        ),
    )
    args = parser.parse_args()

    case_path = (
        Path(args.case) if args.case else DEFAULT_CASE_PATH
    )

    if args.output:
        output_path = Path(args.output)
    else:
        # Derive output path from case filename
        stem = case_path.stem.replace("_expected", "")
        output_path = (
            DEFAULT_OUTPUT_PATH.parent
            / f"{stem}_actual_vs_expected.json"
        )

    report = build_comparison(case_path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    output_path.write_text(
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
                "comparison_passed": report["comparison"]["passed"],
                "actual_result_is_comparable": report["comparison"][
                    "actual_result_is_comparable"
                ],
                "output_path": str(output_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

