import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from services.openai_policy_extraction_adapter import (
    OpenAIPolicyExtractionAdapter,
)
from services.policy_extraction_adapter import (
    PolicyExtractionAdapter,
    PolicyExtractionResult,
    parse_candidate_json,
)


ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )

from scripts.run_policy_extraction_llm_eval import (  # noqa: E402
    calculate_sha256,
    load_dataset_cases,
    resolve_prompt_path,
    run_batch,
    run_repeated_batches,
)


class FakeExtractionAdapter(
    PolicyExtractionAdapter
):

    def __init__(
        self,
        raw_responses,
    ):

        self.raw_responses = raw_responses

    def extract(
        self,
        request,
    ):

        raw_response = self.raw_responses[
            request.case_id
        ]
        parsed_candidate, parse_error = parse_candidate_json(
            raw_response
        )

        return PolicyExtractionResult(
            case_id=request.case_id,
            model=request.model,
            prompt_version=request.prompt_version,
            raw_response=raw_response,
            parsed_candidate=parsed_candidate,
            parse_error=parse_error,
            elapsed_ms=1,
            token_usage={
                "total_tokens":
                    10,
            },
        )


def sample_case(
    case_id="case-1"
):

    expected = {
        "policy_id":
            "POLICY-1",
        "policy_name":
            "Policy 1",
        "review_status":
            "needs_review",
        "evidence_snippets":
            [
                "source evidence",
            ],
        "support_items":
            [],
        "combination_rules":
            [],
    }

    return {
        "case_id":
            case_id,
        "source_text":
            "source evidence",
        "expected_policy":
            expected,
    }


def test_parse_candidate_json_success():

    parsed, error = parse_candidate_json(
        '{"review_status":"needs_review"}'
    )

    assert parsed == {
        "review_status":
            "needs_review"
    }
    assert error is None


def test_parse_candidate_json_failure():

    parsed, error = parse_candidate_json(
        "{not-json"
    )

    assert parsed is None
    assert error


def test_openai_adapter_requires_api_key():

    old_value = os.environ.pop(
        "OPENAI_API_KEY",
        None,
    )

    try:

        try:

            OpenAIPolicyExtractionAdapter()
            raised = False

        except ValueError as exc:

            raised = True
            assert "OPENAI_API_KEY is required" in str(
                exc
            )

        assert raised is True

    finally:

        if old_value is not None:

            os.environ[
                "OPENAI_API_KEY"
            ] = old_value


def test_run_batch_stores_candidate_and_evaluation_result():

    case = sample_case()
    raw_response = json.dumps(
        case[
            "expected_policy"
        ],
        ensure_ascii=False,
    )

    with tempfile.TemporaryDirectory() as tmp_dir:

        report = run_batch(
            FakeExtractionAdapter(
                {
                    "case-1":
                        raw_response,
                }
            ),
            [
                case,
            ],
            "Prompt {{SOURCE_TEXT}}",
            "test-model",
            "policy_extraction_v1",
            Path(
                tmp_dir
            ),
        )
        generated_path = (
            Path(
                tmp_dir
            )
            / "generated"
            / "test-model"
            / "case-1.json"
        )

        assert generated_path.exists()
        assert report["average_score"] == 100
        assert report["results"][0]["evaluator_score"] == 100
        assert report["results"][0]["parsed_candidate"]["review_status"] == "needs_review"


def test_run_batch_records_invalid_review_status_from_evaluator():

    case = sample_case()
    candidate = {
        **case[
            "expected_policy"
        ],
        "review_status":
            "approved",
    }

    with tempfile.TemporaryDirectory() as tmp_dir:

        report = run_batch(
            FakeExtractionAdapter(
                {
                    "case-1":
                        json.dumps(
                            candidate
                        ),
                }
            ),
            [
                case,
            ],
            "Prompt {{SOURCE_TEXT}}",
            "test-model",
            "policy_extraction_v1",
            Path(
                tmp_dir
            ),
        )

        error_types = {
            error[
                "error_type"
            ]
            for error in report["results"][0]["evaluator_errors"]
        }
        assert "invalid_review_status" in error_types


def test_resolve_prompt_path_uses_prompt_version_file():

    prompt_path = resolve_prompt_path(
        "policy_extraction_v2",
        None,
    )

    assert prompt_path.name == "policy_extraction_v2.md"


def test_resolve_prompt_path_prefers_explicit_prompt_path():

    with tempfile.TemporaryDirectory() as tmp_dir:

        prompt_path = Path(
            tmp_dir
        ) / "custom_prompt.md"
        prompt_path.write_text(
            "Custom {{SOURCE_TEXT}}",
            encoding="utf-8",
        )

        resolved = resolve_prompt_path(
            "policy_extraction_v2",
            str(
                prompt_path
            ),
        )

        assert resolved == prompt_path


def test_calculate_sha256_records_prompt_hash():

    with tempfile.TemporaryDirectory() as tmp_dir:

        prompt_path = Path(
            tmp_dir
        ) / "prompt.md"
        prompt_path.write_text(
            "abc",
            encoding="utf-8",
        )

        assert calculate_sha256(
            prompt_path
        ) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def write_dataset_case(
    dataset_dir,
    case_id="real-case-1",
    include_gold=True,
    include_metadata=True,
    metadata_overrides=None,
):

    dataset_path = Path(
        dataset_dir
    )
    raw_dir = dataset_path / "raw_text"
    gold_dir = dataset_path / "gold"
    metadata_dir = dataset_path / "metadata"

    raw_dir.mkdir(
        parents=True,
        exist_ok=True,
    )
    gold_dir.mkdir(
        parents=True,
        exist_ok=True,
    )
    metadata_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        raw_dir / f"{case_id}.txt"
    ).write_text(
        "Real policy source text.",
        encoding="utf-8",
    )

    if include_gold:

        (
            gold_dir / f"{case_id}.json"
        ).write_text(
            json.dumps(
                sample_case(
                    case_id
                )[
                    "expected_policy"
                ],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    if include_metadata:

        metadata = {
            "case_id":
                case_id,
            "policy_name":
                "Real Policy Fixture",
            "source_url":
                "https://example.test/policy",
            "source_type":
                "official_page",
            "collected_at":
                "2026-06-14",
            "notes":
                "Test-only metadata.",
        }

        if metadata_overrides:

            metadata.update(
                metadata_overrides
            )

        (
            metadata_dir / f"{case_id}.json"
        ).write_text(
            json.dumps(
                metadata,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )


def test_load_dataset_cases_matches_raw_gold_and_metadata():

    with tempfile.TemporaryDirectory() as tmp_dir:

        write_dataset_case(
            tmp_dir
        )

        cases = load_dataset_cases(
            Path(
                tmp_dir
            )
        )

        assert len(
            cases
        ) == 1
        assert cases[0]["case_id"] == "real-case-1"
        assert cases[0]["source_text"] == "Real policy source text."
        assert cases[0]["expected_policy"]["review_status"] == "needs_review"
        assert cases[0]["metadata"]["source_type"] == "official_page"
        assert cases[0]["gold_path"].endswith(
            "real-case-1.json"
        )


def test_load_dataset_cases_reports_missing_gold():

    with tempfile.TemporaryDirectory() as tmp_dir:

        write_dataset_case(
            tmp_dir,
            include_gold=False,
        )

        try:

            load_dataset_cases(
                Path(
                    tmp_dir
                )
            )
            raised = False

        except ValueError as exc:

            raised = True
            assert "Gold JSON is missing" in str(
                exc
            )

        assert raised is True


def test_load_dataset_cases_reports_missing_metadata():

    with tempfile.TemporaryDirectory() as tmp_dir:

        write_dataset_case(
            tmp_dir,
            include_metadata=False,
        )

        try:

            load_dataset_cases(
                Path(
                    tmp_dir
                )
            )
            raised = False

        except ValueError as exc:

            raised = True
            assert "Metadata JSON is missing" in str(
                exc
            )

        assert raised is True


def test_load_dataset_cases_reports_missing_metadata_field():

    with tempfile.TemporaryDirectory() as tmp_dir:

        write_dataset_case(
            tmp_dir,
            metadata_overrides={
                "source_url":
                    None,
            },
        )
        metadata_path = (
            Path(
                tmp_dir
            )
            / "metadata"
            / "real-case-1.json"
        )
        metadata = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )
        metadata.pop(
            "source_url"
        )
        metadata_path.write_text(
            json.dumps(
                metadata
            ),
            encoding="utf-8",
        )

        try:

            load_dataset_cases(
                Path(
                    tmp_dir
                )
            )
            raised = False

        except ValueError as exc:

            raised = True
            assert "Metadata JSON is missing required fields" in str(
                exc
            )

        assert raised is True


def test_run_repeated_batches_writes_run_reports_and_summary():

    case = sample_case()
    raw_response = json.dumps(
        case[
            "expected_policy"
        ],
        ensure_ascii=False,
    )

    with tempfile.TemporaryDirectory() as tmp_dir:

        summary = run_repeated_batches(
            lambda: FakeExtractionAdapter(
                {
                    "case-1":
                        raw_response,
                }
            ),
            [
                case,
            ],
            "Prompt {{SOURCE_TEXT}}",
            "test-model",
            "policy_extraction_v2",
            Path(
                tmp_dir
            ),
            3,
            "prompts/policy_extraction_v2.md",
            "abc123",
        )

        assert summary["runs"] == 3
        assert summary["prompt_file"] == "prompts/policy_extraction_v2.md"
        assert summary["prompt_sha256"] == "abc123"
        assert summary["score_summary"]["average"] == 100
        assert summary["score_summary"]["min"] == 100
        assert summary["score_summary"]["max"] == 100
        assert summary["policy_score_summary"]["case-1"]["spread"] == 0
        assert len(
            summary[
                "run_reports"
            ]
        ) == 3

        for run_report in summary["run_reports"]:

            assert Path(
                run_report[
                    "json_report_path"
                ]
            ).exists()


def test_run_repeated_batches_counts_repeated_error_types():

    case = sample_case()
    candidate = {
        **case[
            "expected_policy"
        ],
        "review_status":
            "approved",
    }

    with tempfile.TemporaryDirectory() as tmp_dir:

        summary = run_repeated_batches(
            lambda: FakeExtractionAdapter(
                {
                    "case-1":
                        json.dumps(
                            candidate
                        ),
                }
            ),
            [
                case,
            ],
            "Prompt {{SOURCE_TEXT}}",
            "test-model",
            "policy_extraction_v2",
            Path(
                tmp_dir
            ),
            3,
            "prompts/policy_extraction_v2.md",
            "abc123",
        )

        assert summary["error_type_counts"]["invalid_review_status"] == 3


def test_script_without_api_key_exits_with_clear_error():

    env = os.environ.copy()
    env.pop(
        "OPENAI_API_KEY",
        None,
    )
    env[
        "INCENTDOC_DOTENV_PATH"
    ] = str(
        Path(
            tempfile.gettempdir()
        )
        / "incentdoc-missing-test.env"
    )
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_policy_extraction_llm_eval.py",
        ],
        cwd=ROOT_DIR,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "OPENAI_API_KEY is required" in result.stderr


if __name__ == "__main__":

    test_parse_candidate_json_success()
    test_parse_candidate_json_failure()
    test_openai_adapter_requires_api_key()
    test_run_batch_stores_candidate_and_evaluation_result()
    test_run_batch_records_invalid_review_status_from_evaluator()
    test_resolve_prompt_path_uses_prompt_version_file()
    test_resolve_prompt_path_prefers_explicit_prompt_path()
    test_calculate_sha256_records_prompt_hash()
    test_load_dataset_cases_matches_raw_gold_and_metadata()
    test_load_dataset_cases_reports_missing_gold()
    test_load_dataset_cases_reports_missing_metadata()
    test_load_dataset_cases_reports_missing_metadata_field()
    test_run_repeated_batches_writes_run_reports_and_summary()
    test_run_repeated_batches_counts_repeated_error_types()
    test_script_without_api_key_exits_with_clear_error()
    print("test_policy_extraction_llm_eval passed")
