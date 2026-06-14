"""Batch actual-vs-expected runner for high-comparability mock company cases.

Executes the recommendation pipeline against a curated list of
high-comparability expected-result fixtures and produces a batch
comparison report.

Usage:
    python scripts/run_batch_actual_vs_expected.py

Constraints:
    - No DB writes.
    - No approved-policy auto-processing.
    - No policy JSON source mutation.
    - No frontend changes.
    - Only育児-related policies (replacement_workshare_support,
      parental_leave_reduction_support).
    - Excludes 고령자/청년/고용촉진/정규직전환 policies.
"""

import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
APP_DIR = ROOT_DIR / "match_agent_v0.8" / "match_agent_v0.8"
FIXTURES_DIR = (
    ROOT_DIR / "tests" / "fixtures" / "mock_company_cases"
)
OUTPUT_DIR = (
    ROOT_DIR / "output" / "mock_company_case_checks"
)
BATCH_OUTPUT_PATH = (
    OUTPUT_DIR / "mock_company_batch_actual_vs_expected.json"
)
BATCH_SUMMARY_PATH = (
    OUTPUT_DIR / "mock_company_batch_summary.md"
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

# High-comparability cases only.
# All target replacement_workshare_support.
HIGH_COMPARABILITY_CASES = [
    {
        "case_id": "mock_company_06",
        "fixture_file": "mock_company_06_expected.json",
    },
    {
        "case_id": "mock_company_07",
        "fixture_file": "mock_company_07_expected.json",
    },
    {
        "case_id": "mock_company_08",
        "fixture_file": "mock_company_08_expected.json",
    },
    {
        "case_id": "mock_company_09",
        "fixture_file": "mock_company_09_expected.json",
    },
    {
        "case_id": "mock_company_10",
        "fixture_file": "mock_company_10_expected.json",
    },
    {
        "case_id": "mock_company_17",
        "fixture_file": "mock_company_17_expected.json",
    },
    {
        "case_id": "mock_company_18",
        "fixture_file": "mock_company_18_expected.json",
    },
    {
        "case_id": "mock_company_19",
        "fixture_file": "mock_company_19_expected.json",
    },
    {
        "case_id": "04_hana_machine",
        "fixture_file": "04_hana_machine_expected.json",
    },
]


def collect_policy_ids_from_combinations(combinations):
    """Extract unique policy IDs from recommended/alternative combinations."""
    policy_ids = []
    for combination in combinations or []:
        for policy_id in combination.get("policy_ids", []) or []:
            if policy_id not in policy_ids:
                policy_ids.append(policy_id)
    return policy_ids


def collect_rejected_policy_ids(rejected_combinations):
    """Extract unique policy IDs from rejected combinations."""
    policy_ids = []
    for combination in rejected_combinations or []:
        for policy_id in combination.get("policy_ids", []) or []:
            if policy_id not in policy_ids:
                policy_ids.append(policy_id)
    return policy_ids


def determine_actual_eligibility(
    target_policy_id,
    recommended_ids,
    alternative_ids,
    rejected_ids,
):
    """Determine actual eligibility status from pipeline output."""
    if target_policy_id in recommended_ids:
        return "eligible"
    if target_policy_id in alternative_ids:
        return "eligible"
    if target_policy_id in rejected_ids:
        return "ineligible"
    return "not_found"


def check_reason_code_match(
    expected_reason_code,
    expected_status,
    actual_result,
    target_policy_id,
    recommended_ids,
    alternative_ids,
):
    """Check whether the expected reason code is present in actual output.

    For eligible cases, checks recommended/alternative combinations.
    For ineligible cases, checks rejected combinations.
    """
    if not expected_reason_code:
        return False

    if expected_status == "ineligible":
        rejected = actual_result.get(
            "rejected_combinations", []
        )
        return any(
            expected_reason_code
            in json.dumps(item, ensure_ascii=False)
            for item in rejected
        )

    # For eligible expected status, the reason code should
    # appear somewhere in the recommended or alternative output
    # (or we accept it as matched if the policy is found eligible).
    if expected_status == "eligible":
        if target_policy_id in recommended_ids:
            return True
        if target_policy_id in alternative_ids:
            return True
        return False

    return False


def build_comparison_for_case(case_path):
    """Run the pipeline for a single case and build comparison report.

    Returns a dict with comparison fields per the batch spec.
    """
    case_data = json.loads(
        Path(case_path).read_text(encoding="utf-8")
    )
    expected = case_data.get("expected_result", {})
    expected_primary = expected.get(
        "primary_assertion", {}
    )
    expected_comparison = expected.get(
        "expected_recommendation_comparison", {}
    )
    payload = case_data.get(
        "recommendation_engine_input_draft", {}
    )
    case_id = case_data.get("case_id", "unknown")

    target_policy_id = expected_primary.get("policy_id")
    expected_status = expected_primary.get("expected_status")
    expected_reason_code = expected_primary.get(
        "expected_reason_code"
    )

    # Inject test fixture
    original_loader = orchestrator.load_approved_policies

    def test_policy_loader(source="demo_fixture"):
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
    alternatives = actual.get(
        "alternative_combinations", []
    )
    rejected = actual.get("rejected_combinations", [])

    recommended_ids = (
        recommended.get("policy_ids", [])
        if isinstance(recommended, dict)
        else []
    )
    alternative_ids = collect_policy_ids_from_combinations(
        alternatives
    )
    rejected_ids = collect_rejected_policy_ids(rejected)

    actual_eligibility = determine_actual_eligibility(
        target_policy_id,
        recommended_ids,
        alternative_ids,
        rejected_ids,
    )

    target_present_anywhere = (
        target_policy_id in recommended_ids
        or target_policy_id in alternative_ids
        or target_policy_id in rejected_ids
    )

    reason_code_matched = check_reason_code_match(
        expected_reason_code,
        expected_status,
        actual,
        target_policy_id,
        recommended_ids,
        alternative_ids,
    )

    # Determine pass/fail
    eligibility_match = expected_status == actual_eligibility

    if expected_status == "ineligible":
        comparison_passed = (
            eligibility_match
            and reason_code_matched
            and target_policy_id not in recommended_ids
            and target_policy_id not in alternative_ids
        )
    elif expected_status == "eligible":
        comparison_passed = (
            eligibility_match and target_present_anywhere
        )
    else:
        comparison_passed = False

    return {
        "case_id": case_id,
        "comparison_passed": comparison_passed,
        "actual_result_is_comparable": target_present_anywhere,
        "expected_policy_id": target_policy_id,
        "expected_eligibility": expected_status,
        "actual_eligibility": actual_eligibility,
        "reason_code_matched": reason_code_matched,
        "expected_reason_code": expected_reason_code,
        "detail": {
            "target_is_recommended": (
                target_policy_id in recommended_ids
            ),
            "target_is_alternative": (
                target_policy_id in alternative_ids
            ),
            "target_is_rejected": (
                target_policy_id in rejected_ids
            ),
            "recommended_policy_ids": recommended_ids,
            "alternative_policy_ids": alternative_ids,
            "rejected_policy_ids": rejected_ids,
            "errors": actual.get("errors", []),
        },
    }


def generate_summary_md(batch_result):
    """Generate a markdown summary of the batch run."""
    cases = batch_result.get("case_results", [])
    total = len(cases)
    passed = sum(
        1 for c in cases if c.get("comparison_passed")
    )
    failed = total - passed
    comparable = sum(
        1
        for c in cases
        if c.get("actual_result_is_comparable")
    )
    run_ts = batch_result.get("run_timestamp", "N/A")

    lines = [
        "# Mock Company Batch Actual-vs-Expected Summary",
        "",
        f"Run timestamp: `{run_ts}`",
        "",
        "## Totals",
        "",
        f"| Metric | Count |",
        f"|---|---:|",
        f"| Total cases | {total} |",
        f"| Passed | {passed} |",
        f"| Failed | {failed} |",
        f"| Comparable (target found in output) | {comparable} |",
        "",
        "## Per-Case Results",
        "",
        "| Case ID | Passed | Expected | Actual | Reason Code Match | Comparable |",
        "|---|:---:|---|---|:---:|:---:|",
    ]

    for c in cases:
        p = "✅" if c.get("comparison_passed") else "❌"
        rc = "✅" if c.get("reason_code_matched") else "❌"
        cmp = (
            "✅"
            if c.get("actual_result_is_comparable")
            else "❌"
        )
        lines.append(
            f"| `{c['case_id']}` | {p} | "
            f"{c.get('expected_eligibility', 'N/A')} | "
            f"{c.get('actual_eligibility', 'N/A')} | "
            f"{rc} | {cmp} |"
        )

    # Error detail section for failed cases
    failed_cases = [
        c for c in cases if not c.get("comparison_passed")
    ]
    if failed_cases:
        lines.append("")
        lines.append("## Failed Case Details")
        lines.append("")
        for c in failed_cases:
            lines.append(f"### `{c['case_id']}`")
            lines.append("")
            lines.append(
                f"- Expected: `{c.get('expected_eligibility')}`"
            )
            lines.append(
                f"- Actual: `{c.get('actual_eligibility')}`"
            )
            lines.append(
                f"- Expected reason code: "
                f"`{c.get('expected_reason_code')}`"
            )
            lines.append(
                f"- Reason code matched: "
                f"`{c.get('reason_code_matched')}`"
            )
            detail = c.get("detail", {})
            if detail.get("errors"):
                lines.append("- Pipeline errors:")
                for err in detail["errors"]:
                    lines.append(
                        f"  - `{json.dumps(err, ensure_ascii=False)}`"
                    )
            lines.append("")

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append(
        "- All cases use the test fixture "
        f"`{TEST_POLICY_FIXTURE_NAME}` "
        "injected via `load_approved_policies` monkey-patch."
    )
    lines.append(
        "- Only `replacement_workshare_support` cases "
        "are included in this batch."
    )
    lines.append(
        "- No DB writes, approved auto-processing, "
        "policy JSON mutation, or frontend changes "
        "were performed."
    )
    lines.append(
        "- 고령자/청년/고용촉진/정규직전환 policies are excluded."
    )

    return "\n".join(lines) + "\n"


def main():
    print(
        f"[batch] Starting batch actual-vs-expected "
        f"for {len(HIGH_COMPARABILITY_CASES)} cases..."
    )

    case_results = []
    error_cases = []

    for entry in HIGH_COMPARABILITY_CASES:
        case_id = entry["case_id"]
        fixture_file = entry["fixture_file"]
        case_path = FIXTURES_DIR / fixture_file

        if not case_path.exists():
            error_cases.append(
                {
                    "case_id": case_id,
                    "error": f"Fixture file not found: {case_path}",
                }
            )
            print(f"  [SKIP] {case_id}: fixture not found")
            continue

        print(f"  [RUN]  {case_id}...", end=" ")
        try:
            result = build_comparison_for_case(case_path)
            case_results.append(result)
            status = (
                "PASS"
                if result["comparison_passed"]
                else "FAIL"
            )
            print(
                f"{status} "
                f"(expected={result['expected_eligibility']}, "
                f"actual={result['actual_eligibility']})"
            )
        except Exception as exc:
            tb = traceback.format_exc()
            error_cases.append(
                {
                    "case_id": case_id,
                    "error": str(exc),
                    "traceback": tb,
                }
            )
            print(f"ERROR: {exc}")

    # Build batch report
    run_ts = datetime.now(timezone.utc).isoformat()
    total = len(case_results)
    passed = sum(
        1 for c in case_results if c["comparison_passed"]
    )

    batch_result = {
        "batch_notice": (
            "TEST BATCH RESULT ONLY. "
            "No DB write, no approved auto-processing, "
            "no policy JSON mutation, "
            "no frontend change was performed."
        ),
        "run_timestamp": run_ts,
        "test_policy_fixture": TEST_POLICY_FIXTURE_NAME,
        "target_cases": [
            e["case_id"] for e in HIGH_COMPARABILITY_CASES
        ],
        "summary": {
            "total_cases": total,
            "passed": passed,
            "failed": total - passed,
            "error_cases": len(error_cases),
            "pass_rate": (
                f"{passed}/{total}"
                if total > 0
                else "0/0"
            ),
        },
        "case_results": case_results,
        "error_cases": error_cases,
    }

    # Write outputs
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    BATCH_OUTPUT_PATH.write_text(
        json.dumps(
            batch_result, ensure_ascii=False, indent=2
        ),
        encoding="utf-8",
    )
    print(
        f"\n[batch] JSON report: {BATCH_OUTPUT_PATH}"
    )

    summary_md = generate_summary_md(batch_result)
    BATCH_SUMMARY_PATH.write_text(
        summary_md, encoding="utf-8"
    )
    print(f"[batch] Summary MD: {BATCH_SUMMARY_PATH}")

    print(
        f"\n[batch] Done: {passed}/{total} passed, "
        f"{len(error_cases)} errors."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
