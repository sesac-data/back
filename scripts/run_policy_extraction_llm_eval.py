import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
APP_DIR = ROOT_DIR / "match_agent_v0.8" / "match_agent_v0.8"
APP_ENV_PATH = APP_DIR / ".env"
DEFAULT_FIXTURE_DIR = ROOT_DIR / "data" / "policy_extraction_eval"
DEFAULT_PROMPT_PATH = ROOT_DIR / "prompts" / "policy_extraction_v1.md"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "output" / "policy_extraction_eval"
DEFAULT_REAL_OUTPUT_DIR = ROOT_DIR / "output" / "policy_extraction_real_eval"
DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_PROMPT_VERSION = "policy_extraction_v1"
REQUIRED_METADATA_FIELDS = [
    "case_id",
    "policy_name",
    "source_url",
    "source_type",
    "collected_at",
    "notes",
]


def load_app_env() -> None:

    dotenv_path = Path(
        os.environ.get(
            "INCENTDOC_DOTENV_PATH",
            str(
                APP_ENV_PATH
            ),
        )
    )
    load_dotenv(
        dotenv_path=dotenv_path,
        override=False,
    )

if str(APP_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(APP_DIR),
    )

from services.openai_policy_extraction_adapter import (  # noqa: E402
    OpenAIPolicyExtractionAdapter,
)
from services.policy_extraction_adapter import (  # noqa: E402
    PolicyExtractionRequest,
)
from services.policy_structure_evaluator import (  # noqa: E402
    evaluate_policy_structure,
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


def load_dataset_cases(
    dataset_dir: Path,
):

    raw_dir = dataset_dir / "raw_text"
    gold_dir = dataset_dir / "gold"
    metadata_dir = dataset_dir / "metadata"

    for required_dir in [
        raw_dir,
        gold_dir,
        metadata_dir,
    ]:

        if not required_dir.exists() or not required_dir.is_dir():

            raise ValueError(
                f"Dataset directory is missing required subdirectory: {required_dir}"
            )

    raw_paths = sorted(
        raw_dir.glob(
            "*.txt"
        )
    )

    if not raw_paths:

        raise ValueError(
            f"Dataset has no raw text files: {raw_dir}"
        )

    cases = []

    for raw_path in raw_paths:

        case_id = raw_path.stem
        gold_path = gold_dir / f"{case_id}.json"
        metadata_path = metadata_dir / f"{case_id}.json"

        if not gold_path.exists():

            raise ValueError(
                f"Gold JSON is missing for case '{case_id}': {gold_path}"
            )

        if not metadata_path.exists():

            raise ValueError(
                f"Metadata JSON is missing for case '{case_id}': {metadata_path}"
            )

        with metadata_path.open(
            "r",
            encoding="utf-8",
        ) as handle:

            metadata = json.load(
                handle
            )

        missing_metadata_fields = [
            field
            for field in REQUIRED_METADATA_FIELDS
            if field not in metadata
        ]

        if missing_metadata_fields:

            raise ValueError(
                "Metadata JSON is missing required fields for case '{case}': {fields}".format(
                    case=case_id,
                    fields=", ".join(
                        missing_metadata_fields
                    ),
                )
            )

        if metadata.get(
            "case_id"
        ) != case_id:

            raise ValueError(
                "Metadata case_id mismatch for case '{case}': expected '{case}', actual '{actual}'".format(
                    case=case_id,
                    actual=metadata.get(
                        "case_id"
                    ),
                )
            )

        with gold_path.open(
            "r",
            encoding="utf-8",
        ) as handle:

            gold_policy = json.load(
                handle
            )

        cases.append(
            {
                "case_id":
                    case_id,
                "source_text":
                    raw_path.read_text(
                        encoding="utf-8"
                    ),
                "expected_policy":
                    gold_policy,
                "metadata":
                    metadata,
                "fixture_path":
                    str(
                        raw_path
                    ),
                "gold_path":
                    str(
                        gold_path
                    ),
                "metadata_path":
                    str(
                        metadata_path
                    ),
            }
        )

    return cases


def build_prompt(
    prompt_template: str,
    source_text: str,
) -> str:

    return prompt_template.replace(
        "{{SOURCE_TEXT}}",
        source_text,
    )


def run_batch(
    adapter,
    cases,
    prompt_template: str,
    model: str,
    prompt_version: str,
    output_dir: Path,
    prompt_file: str = None,
    prompt_sha256: str = None,
    run_id: str = None,
):

    generated_dir = output_dir / "generated" / model
    generated_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = []

    for case in cases:

        request = PolicyExtractionRequest(
            case_id=case.get(
                "case_id"
            ),
            source_text=case.get(
                "source_text",
                "",
            ),
            prompt=build_prompt(
                prompt_template,
                case.get(
                    "source_text",
                    "",
                ),
            ),
            model=model,
            prompt_version=prompt_version,
        )
        extraction = adapter.extract(
            request
        )
        extraction_record = extraction.to_dict()
        evaluator_result = None

        if extraction.parsed_candidate is not None:

            evaluator_result = evaluate_policy_structure(
                case.get(
                    "source_text",
                    "",
                ),
                case.get(
                    "expected_policy",
                    {},
                ),
                extraction.parsed_candidate,
                case.get(
                    "case_id"
                ),
            )

        record = {
            **extraction_record,
            "fixture_path":
                case.get(
                    "fixture_path"
                ),
            "gold_path":
                case.get(
                    "gold_path"
                ),
            "metadata_path":
                case.get(
                    "metadata_path"
                ),
            "metadata":
                case.get(
                    "metadata"
                ),
            "generated_candidate_path":
                str(
                    generated_dir
                    / f"{case.get('case_id')}.json"
                ),
            "evaluator_score":
                evaluator_result.get(
                    "score"
                )
                if evaluator_result
                else 0,
            "evaluator_errors":
                evaluator_result.get(
                    "errors"
                )
                if evaluator_result
                else [
                    {
                        "error_type":
                            "parse_error",
                        "path":
                            "raw_response",
                        "expected":
                            "JSON object",
                        "actual":
                            extraction.parse_error,
                    }
                ],
            "evaluator_passed":
                evaluator_result.get(
                    "passed"
                )
                if evaluator_result
                else False,
        }
        results.append(
            record
        )

        _write_json(
            generated_dir
            / f"{case.get('case_id')}.json",
            {
                "case_id":
                    case.get(
                        "case_id"
                    ),
                "model":
                    model,
                "prompt_version":
                    prompt_version,
                "raw_response":
                    extraction.raw_response,
                "parsed_candidate":
                    extraction.parsed_candidate,
                "parse_error":
                    extraction.parse_error,
                "elapsed_ms":
                    extraction.elapsed_ms,
                "token_usage":
                    extraction.token_usage,
                "metadata":
                    case.get(
                        "metadata"
                    ),
                "gold_path":
                    case.get(
                        "gold_path"
                    ),
                "metadata_path":
                    case.get(
                        "metadata_path"
                    ),
                "evaluator_score":
                    record[
                        "evaluator_score"
                    ],
                "evaluator_errors":
                    record[
                        "evaluator_errors"
                    ],
            },
        )

    average_score = (
        round(
            sum(
                result.get(
                    "evaluator_score",
                    0,
                )
                for result in results
            )
            / len(
                results
            ),
            2,
        )
        if results
        else 0
    )

    return {
        "generated_at":
            datetime.now(
                timezone.utc
            ).isoformat(),
        "run_id":
            run_id,
        "model":
            model,
        "prompt_version":
            prompt_version,
        "prompt_file":
            prompt_file,
        "prompt_sha256":
            prompt_sha256,
        "case_count":
            len(
                results
            ),
        "average_score":
            average_score,
        "results":
            results,
    }


def resolve_prompt_path(
    prompt_version: str,
    prompt_path: str = None,
) -> Path:

    if prompt_path:

        return Path(
            prompt_path
        )

    version_path = ROOT_DIR / "prompts" / f"{prompt_version}.md"

    if version_path.exists():

        return version_path

    return DEFAULT_PROMPT_PATH


def calculate_sha256(
    path: Path,
) -> str:

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def make_run_id(
    index: int,
) -> str:

    return "{timestamp}-{index:02d}".format(
        timestamp=datetime.now(
            timezone.utc
        ).strftime(
            "%Y%m%dT%H%M%SZ"
        ),
        index=index,
    )


def run_repeated_batches(
    adapter_factory,
    cases,
    prompt_template: str,
    model: str,
    prompt_version: str,
    output_dir: Path,
    runs: int,
    prompt_file: str,
    prompt_sha256: str,
):

    run_reports = []

    for index in range(
        1,
        runs + 1,
    ):

        run_id = make_run_id(
            index
        )
        run_dir = output_dir / run_id
        run_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        report = run_batch(
            adapter_factory(),
            cases,
            prompt_template,
            model,
            prompt_version,
            run_dir,
            prompt_file=prompt_file,
            prompt_sha256=prompt_sha256,
            run_id=run_id,
        )

        json_path = run_dir / "model-comparison-report.json"
        markdown_path = run_dir / "model-comparison-report.md"
        _write_json(
            json_path,
            report,
        )
        markdown_path.write_text(
            render_markdown(
                report
            ),
            encoding="utf-8",
        )
        report[
            "json_report_path"
        ] = str(
            json_path
        )
        report[
            "markdown_report_path"
        ] = str(
            markdown_path
        )
        run_reports.append(
            report
        )

    return build_summary_report(
        run_reports,
        model,
        prompt_version,
        prompt_file,
        prompt_sha256,
        output_dir,
    )


def build_summary_report(
    run_reports,
    model: str,
    prompt_version: str,
    prompt_file: str,
    prompt_sha256: str,
    output_dir: Path,
):

    average_scores = [
        report.get(
            "average_score",
            0,
        )
        for report in run_reports
    ]
    policy_scores = {}
    error_type_counts = {}

    for report in run_reports:

        for result in report.get(
            "results",
            []
        ):

            case_id = result.get(
                "case_id"
            )
            policy_scores.setdefault(
                case_id,
                [],
            ).append(
                result.get(
                    "evaluator_score",
                    0,
                )
            )

            for error in result.get(
                "evaluator_errors",
                []
            ):

                error_type = error.get(
                    "error_type",
                    "unknown",
                )
                error_type_counts[
                    error_type
                ] = (
                    error_type_counts.get(
                        error_type,
                        0,
                    )
                    + 1
                )

    policy_score_summary = {}

    for case_id, scores in sorted(
        policy_scores.items()
    ):

        policy_score_summary[
            case_id
        ] = {
            "scores":
                scores,
            "average":
                round(
                    sum(
                        scores
                    )
                    / len(
                        scores
                    ),
                    2,
                )
                if scores
                else 0,
            "min":
                min(
                    scores
                )
                if scores
                else 0,
            "max":
                max(
                    scores
                )
                if scores
                else 0,
            "spread":
                round(
                    max(
                        scores
                    )
                    - min(
                        scores
                    ),
                    2,
                )
                if scores
                else 0,
        }

    return {
        "generated_at":
            datetime.now(
                timezone.utc
            ).isoformat(),
        "model":
            model,
        "prompt_version":
            prompt_version,
        "prompt_file":
            prompt_file,
        "prompt_sha256":
            prompt_sha256,
        "runs":
            len(
                run_reports
            ),
        "score_summary":
            {
                "average":
                    round(
                        sum(
                            average_scores
                        )
                        / len(
                            average_scores
                        ),
                        2,
                    )
                    if average_scores
                    else 0,
                "min":
                    min(
                        average_scores
                    )
                    if average_scores
                    else 0,
                "max":
                    max(
                        average_scores
                    )
                    if average_scores
                    else 0,
                "scores":
                    average_scores,
            },
        "policy_score_summary":
            policy_score_summary,
        "error_type_counts":
            dict(
                sorted(
                    error_type_counts.items()
                )
            ),
        "run_reports":
            [
                {
                    "run_id":
                        report.get(
                            "run_id"
                        ),
                    "average_score":
                        report.get(
                            "average_score"
                        ),
                    "json_report_path":
                        report.get(
                            "json_report_path"
                        ),
                    "markdown_report_path":
                        report.get(
                            "markdown_report_path"
                        ),
                }
                for report in run_reports
            ],
        "summary_json_path":
            str(
                output_dir / "summary-report.json"
            ),
        "summary_markdown_path":
            str(
                output_dir / "summary-report.md"
            ),
    }


def render_markdown(
    report
) -> str:

    lines = [
        "# Policy Extraction LLM Model Comparison",
        "",
        f"- Model: `{report.get('model')}`",
        f"- Prompt version: `{report.get('prompt_version')}`",
        f"- Case count: {report.get('case_count')}",
        f"- Average score: {report.get('average_score')}",
        "",
        "| Case | Score | Passed | Parse Error | Error Types |",
        "| --- | ---: | --- | --- | --- |",
    ]

    for result in report.get(
        "results",
        []
    ):

        error_types = sorted(
            {
                error.get(
                    "error_type"
                )
                for error in result.get(
                    "evaluator_errors",
                    []
                )
            }
        )
        lines.append(
            "| {case} | {score} | {passed} | {parse_error} | {errors} |".format(
                case=result.get(
                    "case_id"
                ),
                score=result.get(
                    "evaluator_score"
                ),
                passed=result.get(
                    "evaluator_passed"
                ),
                parse_error=result.get(
                    "parse_error"
                )
                or "-",
                errors=", ".join(
                    error_types
                )
                or "-",
            )
        )

    return "\n".join(
        lines
    ) + "\n"


def render_summary_markdown(
    summary,
) -> str:

    lines = [
        "# Policy Extraction LLM Repeated Evaluation Summary",
        "",
        f"- Model: `{summary.get('model')}`",
        f"- Prompt version: `{summary.get('prompt_version')}`",
        f"- Prompt file: `{summary.get('prompt_file')}`",
        f"- Prompt SHA-256: `{summary.get('prompt_sha256')}`",
        f"- Runs: {summary.get('runs')}",
        f"- Average score: {summary.get('score_summary', {}).get('average')}",
        f"- Min score: {summary.get('score_summary', {}).get('min')}",
        f"- Max score: {summary.get('score_summary', {}).get('max')}",
        "",
        "## Runs",
        "",
        "| Run ID | Average score | JSON report |",
        "| --- | ---: | --- |",
    ]

    for report in summary.get(
        "run_reports",
        []
    ):

        lines.append(
            "| {run_id} | {score} | `{path}` |".format(
                run_id=report.get(
                    "run_id"
                ),
                score=report.get(
                    "average_score"
                ),
                path=report.get(
                    "json_report_path"
                ),
            )
        )

    lines.extend(
        [
            "",
            "## Policy Score Variation",
            "",
            "| Case | Scores | Average | Min | Max | Spread |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )

    for case_id, details in summary.get(
        "policy_score_summary",
        {}
    ).items():

        lines.append(
            "| {case} | {scores} | {average} | {min_score} | {max_score} | {spread} |".format(
                case=case_id,
                scores=", ".join(
                    str(
                        score
                    )
                    for score in details.get(
                        "scores",
                        []
                    )
                ),
                average=details.get(
                    "average"
                ),
                min_score=details.get(
                    "min"
                ),
                max_score=details.get(
                    "max"
                ),
                spread=details.get(
                    "spread"
                ),
            )
        )

    lines.extend(
        [
            "",
            "## Repeated Error Type Counts",
            "",
            "| Error type | Count |",
            "| --- | ---: |",
        ]
    )

    for error_type, count in summary.get(
        "error_type_counts",
        {}
    ).items():

        lines.append(
            f"| {error_type} | {count} |"
        )

    return "\n".join(
        lines
    ) + "\n"


def main():

    load_app_env()

    parser = argparse.ArgumentParser(
        description="Run live OpenAI policy extraction and evaluate generated candidates."
    )
    parser.add_argument(
        "--fixture-dir",
        default=str(
            DEFAULT_FIXTURE_DIR
        ),
    )
    parser.add_argument(
        "--dataset",
        default=None,
        help="Optional dataset root with raw_text/, gold/, and metadata/ subdirectories.",
    )
    parser.add_argument(
        "--prompt-path",
        default=None,
    )
    parser.add_argument(
        "--output-dir",
        default=None,
    )
    parser.add_argument(
        "--model",
        default=os.environ.get(
            "POLICY_EXTRACTION_MODEL",
            DEFAULT_MODEL,
        ),
    )
    parser.add_argument(
        "--prompt-version",
        default=os.environ.get(
            "POLICY_EXTRACTION_PROMPT_VERSION",
            DEFAULT_PROMPT_VERSION,
        ),
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
    )
    args = parser.parse_args()

    if args.runs < 1:

        print(
            "ERROR: --runs must be 1 or greater.",
            file=sys.stderr,
        )
        return 2

    prompt_path = resolve_prompt_path(
        args.prompt_version,
        args.prompt_path,
    )
    prompt_file = str(
        prompt_path
    )
    prompt_sha256 = calculate_sha256(
        prompt_path
    )
    output_base_dir = (
        Path(
            args.output_dir
        )
        if args.output_dir
        else (
            DEFAULT_REAL_OUTPUT_DIR
            if args.dataset
            else DEFAULT_OUTPUT_DIR
        )
    )
    output_dir = (
        output_base_dir
        / args.prompt_version
    )
    try:

        cases = (
            load_dataset_cases(
                Path(
                    args.dataset
                )
            )
            if args.dataset
            else load_cases(
                Path(
                    args.fixture_dir
                )
            )
        )

    except (OSError, json.JSONDecodeError, ValueError) as exc:

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )
        error_report = {
            "status":
                "ERROR",
            "error":
                str(
                    exc
                ),
            "model":
                args.model,
            "prompt_version":
                args.prompt_version,
            "prompt_file":
                prompt_file,
            "prompt_sha256":
                prompt_sha256,
            "dataset":
                args.dataset,
            "runs":
                args.runs,
            "score_summary":
                {
                    "average":
                        0,
                    "min":
                        0,
                    "max":
                        0,
                    "scores":
                        [],
                },
            "policy_score_summary":
                {},
            "error_type_counts":
                {},
            "case_count":
                0,
            "average_score":
                0,
            "results":
                [],
        }
        _write_json(
            output_dir / "summary-report.json",
            error_report,
        )
        (
            output_dir / "summary-report.md"
        ).write_text(
            render_summary_markdown(
                error_report
            ),
            encoding="utf-8",
        )
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 2

    if not os.environ.get(
        "OPENAI_API_KEY"
    ):

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )
        error_report = {
            "status":
                "ERROR",
            "error":
                "OPENAI_API_KEY is required to run live policy extraction LLM evaluation.",
            "model":
                args.model,
            "prompt_version":
                args.prompt_version,
            "prompt_file":
                prompt_file,
            "prompt_sha256":
                prompt_sha256,
            "dataset":
                args.dataset,
            "runs":
                args.runs,
            "score_summary":
                {
                    "average":
                        0,
                    "min":
                        0,
                    "max":
                        0,
                    "scores":
                        [],
                },
            "policy_score_summary":
                {},
            "error_type_counts":
                {},
            "case_count":
                0,
            "average_score":
                0,
            "results":
                [],
        }
        _write_json(
            output_dir / "summary-report.json",
            error_report,
        )
        (
            output_dir / "summary-report.md"
        ).write_text(
            render_summary_markdown(
                error_report
            ),
            encoding="utf-8",
        )
        print(
            "ERROR: OPENAI_API_KEY is required to run live policy extraction LLM evaluation.",
            file=sys.stderr,
        )
        return 2

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    prompt_template = prompt_path.read_text(
        encoding="utf-8"
    )
    summary = run_repeated_batches(
        OpenAIPolicyExtractionAdapter,
        cases,
        prompt_template,
        args.model,
        args.prompt_version,
        output_dir,
        args.runs,
        prompt_file,
        prompt_sha256,
    )

    json_path = output_dir / "summary-report.json"
    markdown_path = output_dir / "summary-report.md"
    _write_json(
        json_path,
        summary,
    )
    markdown_path.write_text(
        render_summary_markdown(
            summary
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status":
                    "PASS",
                "model":
                    args.model,
                "prompt_version":
                    args.prompt_version,
                "runs":
                    args.runs,
                "prompt_file":
                    prompt_file,
                "prompt_sha256":
                    prompt_sha256,
                "average_score":
                    summary.get(
                        "score_summary",
                        {},
                    ).get(
                        "average"
                    ),
                "score_summary":
                    summary.get(
                        "score_summary"
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
    return 0


def _write_json(
    path: Path,
    payload,
):

    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
