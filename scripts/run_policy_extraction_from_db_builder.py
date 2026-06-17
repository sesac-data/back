import argparse
import json
import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
APP_DIR = ROOT_DIR / "match_agent_v0.8" / "match_agent_v0.8"
DEFAULT_DOCS_ROOT = APP_DIR / "incent_docs"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "output" / "policy_extraction_from_db_builder"
DEFAULT_MODEL = "gpt-4.1"
DEFAULT_PROMPT_VERSION = "policy_extraction_v6"
PARENTAL_SUPPORT_DOCUMENT_IDS = {
    "childcare_flexible_start_support",
    "flexible_work_incent",
    "flexible_work_system_support",
    "parental_leave_reduction_support",
    "replacement_workshare_support",
    "worklife_balance_45_support",
    "working_hours_reduction_support",
}

if str(
    APP_DIR
) not in sys.path:

    sys.path.insert(
        0,
        str(
            APP_DIR
        ),
    )

if str(
    ROOT_DIR
) not in sys.path:

    sys.path.insert(
        0,
        str(
            ROOT_DIR
        ),
    )

from scripts.run_policy_extraction_llm_eval import (  # noqa: E402
    build_prompt,
    calculate_sha256,
    load_app_env,
    resolve_prompt_path,
)
from services.db_builder_policy_document_loader import (  # noqa: E402
    load_policy_documents,
)
from services.openai_policy_extraction_adapter import (  # noqa: E402
    OpenAIPolicyExtractionAdapter,
)
from services.policy_extraction_adapter import (  # noqa: E402
    PolicyExtractionRequest,
)
from services.policy_extraction_candidate_assembler import (  # noqa: E402
    assemble_policy_extraction_candidate,
)
from services.policy_extraction_candidate_validator import (  # noqa: E402
    validate_policy_extraction_candidate,
)
from services.policy_source_preprocessor import (  # noqa: E402
    preprocess_policy_source_text,
)


def run_extraction_from_documents(
    docs_root: Path,
    output_dir: Path,
    prompt_template: str,
    prompt_file: str,
    prompt_sha256: str,
    prompt_version: str,
    model: str,
    document_id: str = None,
    preprocess: bool = True,
    use_structured: bool = False,
):

    documents = load_policy_documents(
        docs_root
    )
    documents = filter_parental_support_documents(
        documents
    )

    if document_id:

        documents = [
            document
            for document in documents
            if document.document_id == document_id
        ]

    if not documents:

        raise ValueError(
            "No policy documents found for extraction."
        )

    adapter = OpenAIPolicyExtractionAdapter()
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = []

    for document in documents:

        # Prefer the table-structure-preserving source when requested and present.
        base_source, source_kind = _load_base_source(
            docs_root,
            document,
            use_structured,
        )

        # The cleaned source is used for BOTH the prompt and evidence validation
        # so the model and the validator reference the same canonical text.
        source_text = (
            preprocess_policy_source_text(base_source)
            if preprocess
            else base_source
        )

        extraction = adapter.extract(
            PolicyExtractionRequest(
                case_id=document.document_id,
                source_text=source_text,
                prompt=build_prompt(
                    prompt_template,
                    source_text,
                ),
                model=model,
                prompt_version=prompt_version,
            )
        )
        record = extraction.to_dict()
        raw_candidate = extraction.parsed_candidate
        assembled_candidate = assemble_policy_extraction_candidate(
            extraction.parsed_candidate,
            document,
        )
        candidate_validation_result = validate_policy_extraction_candidate(
            assembled_candidate,
            source_text,
        )

        output_record = {
            **record,
            "source_document_id":
                document.document_id,
            "source_url":
                document.source_url,
            "source_file":
                document.source_file,
            "metadata":
                document.metadata,
            "prompt_file":
                prompt_file,
            "prompt_sha256":
                prompt_sha256,
            "preprocessing":
                {
                    "enabled":
                        preprocess,
                    "source_kind":
                        source_kind,
                    "base_char_count":
                        len(
                            base_source
                        ),
                    "source_char_count":
                        len(
                            source_text
                        ),
                },
            "parsed_candidate":
                raw_candidate,
            "assembled_candidate":
                assembled_candidate,
            "candidate_validation_result":
                candidate_validation_result,
            "errors":
                [],
        }

        if extraction.parse_error:

            output_record[
                "errors"
            ].append(
                {
                    "error_type":
                        "parse_error",
                    "message":
                        extraction.parse_error,
                }
            )

        if (
            assembled_candidate is not None
            and assembled_candidate.get(
                "review_status"
            )
            != "needs_review"
        ):

            output_record[
                "errors"
            ].append(
                {
                    "error_type":
                        "invalid_review_status",
                    "message":
                        "Generated candidate must remain review_status=needs_review.",
                    "actual":
                        assembled_candidate.get(
                            "review_status"
                        ),
                }
            )

        output_path = output_dir / f"{document.document_id}.json"
        _write_json(
            output_path,
            output_record,
        )
        output_record[
            "output_path"
        ] = str(
            output_path
        )
        results.append(
            output_record
        )

    return results


def _load_base_source(
    docs_root: Path,
    document,
    use_structured: bool,
):
    """Return (text, kind): the structured source when requested and present,
    otherwise the document's flattened raw_text."""

    if use_structured:

        structured_path = (
            docs_root
            / f"{document.document_id}_docs"
            / f"{document.document_id}_structured.txt"
        )

        if structured_path.exists():

            return (
                structured_path.read_text(
                    encoding="utf-8"
                ),
                "structured",
            )

    return document.raw_text, "raw"


def filter_parental_support_documents(
    documents,
):

    return [
        document
        for document in documents
        if document.document_id in PARENTAL_SUPPORT_DOCUMENT_IDS
    ]


def main():

    load_app_env()

    parser = argparse.ArgumentParser(
        description="Run policy extraction over documents collected by db_builder."
    )
    parser.add_argument(
        "--docs-root",
        default=str(
            DEFAULT_DOCS_ROOT
        ),
    )
    parser.add_argument(
        "--document-id",
        default=None,
    )
    parser.add_argument(
        "--output-dir",
        default=str(
            DEFAULT_OUTPUT_DIR
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
        "--prompt-path",
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
        "--no-preprocess",
        dest="preprocess",
        action="store_false",
        help="Send raw crawled text to the model instead of the cleaned policy body.",
    )
    parser.add_argument(
        "--use-structured",
        dest="use_structured",
        action="store_true",
        help="Use {incent_key}_structured.txt (table-preserving) instead of flattened raw text.",
    )
    parser.set_defaults(
        preprocess=True,
        use_structured=False,
    )
    args = parser.parse_args()

    prompt_path = resolve_prompt_path(
        args.prompt_version,
        args.prompt_path,
    )
    prompt_template = prompt_path.read_text(
        encoding="utf-8"
    )
    prompt_file = str(
        prompt_path
    )
    prompt_sha256 = calculate_sha256(
        prompt_path
    )

    if not os.environ.get(
        "OPENAI_API_KEY"
    ):

        print(
            "ERROR: OPENAI_API_KEY is required to run db_builder policy document extraction.",
            file=sys.stderr,
        )
        return 2

    try:

        results = run_extraction_from_documents(
            docs_root=Path(
                args.docs_root
            ),
            output_dir=Path(
                args.output_dir
            ),
            prompt_template=prompt_template,
            prompt_file=prompt_file,
            prompt_sha256=prompt_sha256,
            prompt_version=args.prompt_version,
            model=args.model,
            document_id=args.document_id,
            preprocess=args.preprocess,
            use_structured=args.use_structured,
        )

    except Exception as exc:

        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 2

    print(
        json.dumps(
            {
                "status":
                    "PASS",
                "model":
                    args.model,
                "prompt_version":
                    args.prompt_version,
                "prompt_file":
                    prompt_file,
                "prompt_sha256":
                    prompt_sha256,
                "document_count":
                    len(
                        results
                    ),
                "output_paths":
                    [
                        result.get(
                            "output_path"
                        )
                        for result in results
                    ],
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
