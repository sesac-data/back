import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
APP_DIR = ROOT_DIR / "match_agent_v0.8" / "match_agent_v0.8"
DEFAULT_FIXTURE_DIR = ROOT_DIR / "data" / "policy_extraction_eval"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "output" / "policy_extraction_eval"

if str(APP_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(APP_DIR),
    )

from services.policy_structure_evaluator import (  # noqa: E402
    evaluate_policy_structure_cases,
    render_markdown_report,
)


def load_cases(
    fixture_dir: Path
):

    cases = []

    for path in sorted(
        fixture_dir.glob(
            "*.json"
        )
    ):

        with path.open(
            "r",
            encoding="utf-8",
        ) as handle:

            case = json.load(
                handle
            )
            case["fixture_path"] = str(
                path
            )
            cases.append(
                case
            )

    return cases


def main():

    parser = argparse.ArgumentParser(
        description="Evaluate test fixture policy extraction candidates."
    )
    parser.add_argument(
        "--fixture-dir",
        default=str(
            DEFAULT_FIXTURE_DIR
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=str(
            DEFAULT_OUTPUT_DIR
        ),
    )
    args = parser.parse_args()

    fixture_dir = Path(
        args.fixture_dir
    )
    output_dir = Path(
        args.output_dir
    )
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    cases = load_cases(
        fixture_dir
    )
    report = evaluate_policy_structure_cases(
        cases
    )
    report["generated_at"] = datetime.now(
        timezone.utc
    ).isoformat()
    report["fixture_dir"] = str(
        fixture_dir
    )
    report["notice"] = (
        "TEST FIXTURE ONLY. No live LLM API was called. "
        "Candidate policies remain review_status=needs_review."
    )

    json_path = output_dir / "latest-report.json"
    markdown_path = output_dir / "latest-report.md"

    json_path.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    markdown_path.write_text(
        render_markdown_report(
            report
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status":
                    "PASS",
                "case_count":
                    report.get(
                        "case_count"
                    ),
                "average_score":
                    report.get(
                        "average_score"
                    ),
                "json_report_path":
                    str(
                        json_path
                    ),
                "markdown_report_path":
                    str(
                        markdown_path
                    ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
