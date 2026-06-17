"""Report policy JSON condition types/operators not handled by the rule engine.

Usage:
    python scripts/audit_condition_type_coverage.py
    python scripts/audit_condition_type_coverage.py --strict   # exit 1 if gaps

Read-only. Scans data/policy_json/*.json and writes a JSON report under
output/condition_coverage/.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
APP_DIR = ROOT_DIR / "match_agent_v0.8" / "match_agent_v0.8"
POLICY_JSON_DIR = APP_DIR / "data" / "policy_json"
OUTPUT_DIR = ROOT_DIR / "output" / "condition_coverage"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from services.condition_coverage_auditor import (  # noqa: E402
    audit_condition_coverage,
)


def load_policies(policy_dir: Path):
    policies = []
    for path in sorted(policy_dir.glob("*.json")):
        try:
            policies.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError as exc:
            print(f"WARN: skipping unparseable {path.name}: {exc}", file=sys.stderr)
    return policies


def main():
    parser = argparse.ArgumentParser(
        description="Audit policy JSON condition type/operator coverage."
    )
    parser.add_argument("--policy-dir", default=str(POLICY_JSON_DIR))
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 when unsupported types/operators are found.",
    )
    args = parser.parse_args()

    policies = load_policies(Path(args.policy_dir))
    report = audit_condition_coverage(policies)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / "condition-coverage-report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"policies scanned: {report['policy_count']}")
    print(f"supported types ({len(report['supported_types'])}): {report['supported_types']}")
    print(f"UNSUPPORTED types ({len(report['unsupported_types'])}):")
    for item in report["unsupported_types"]:
        print(f"  - {item['type']}  (used {item['count']}x in {item['policies']})")
    if report["unsupported_operators"]:
        print(f"UNSUPPORTED operators ({len(report['unsupported_operators'])}):")
        for item in report["unsupported_operators"]:
            print(f"  - {item['operator']}  (used {item['count']}x)")
    print(f"report written: {report_path}")

    if args.strict and report["has_gaps"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
