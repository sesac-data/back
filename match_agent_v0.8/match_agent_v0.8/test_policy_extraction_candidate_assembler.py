from copy import deepcopy

from services.db_builder_policy_document_loader import PolicyDocumentRecord
from services.policy_extraction_candidate_assembler import (
    assemble_policy_extraction_candidate,
)
from services.policy_extraction_candidate_validator import (
    validate_policy_extraction_candidate,
)


RAW_TEXT = "정책명 지원금입니다.\n월 300000원, 최대 12개월 지원합니다."


def document_record():

    return PolicyDocumentRecord(
        document_id="sample_document",
        source_file="incent_docs/sample_raw.txt",
        source_url="https://example.test/policy",
        raw_text=RAW_TEXT,
        metadata={
            "incent_key": "sample_policy",
            "url": "https://example.test/policy",
        },
    )


def raw_candidate():

    return {
        "policy_id": "",
        "policy_name": "정책명 지원금",
        "review_status": "needs_review",
        "source_document_id": "",
        "source_url": "",
        "source_file": "",
        "evidence_snippets": [
            "정책명 지원금입니다.",
        ],
        "support_items": [
            {
                "support_item_id": "SI-001",
                "calculation_type": "monthly_fixed",
                "monthly_amount": 300000,
                "max_months": 12,
                "evidence_snippets": [
                    "월 300000원,\n최대 12개월 지원합니다.",
                ],
            }
        ],
        "combination_rules": [],
        "unresolved_rules": [],
    }


def test_assembler_injects_policy_id_from_incent_key():

    candidate = raw_candidate()
    assembled = assemble_policy_extraction_candidate(
        candidate,
        document_record(),
    )

    assert assembled["policy_id"] == "sample_policy"
    assert candidate["policy_id"] == ""


def test_assembler_attaches_source_metadata():

    assembled = assemble_policy_extraction_candidate(
        raw_candidate(),
        document_record(),
    )

    assert assembled["source_document_id"] == "sample_document"
    assert assembled["source_url"] == "https://example.test/policy"
    assert assembled["source_file"] == "incent_docs/sample_raw.txt"


def test_assembler_preserves_existing_policy_id():

    candidate = raw_candidate()
    candidate["policy_id"] = "llm_policy_id"

    assembled = assemble_policy_extraction_candidate(
        candidate,
        document_record(),
    )

    assert assembled["policy_id"] == "llm_policy_id"


def test_assembler_does_not_mutate_raw_candidate():

    candidate = raw_candidate()
    before = deepcopy(
        candidate
    )

    assemble_policy_extraction_candidate(
        candidate,
        document_record(),
    )

    assert candidate == before


def test_assembled_candidate_passes_policy_id_and_normalized_evidence_gate():

    assembled = assemble_policy_extraction_candidate(
        raw_candidate(),
        document_record(),
    )

    result = validate_policy_extraction_candidate(
        assembled,
        RAW_TEXT,
    )

    assert result["passed"] is True


def test_missing_incent_key_still_reports_missing_policy_id():

    record = document_record()
    record.metadata = {}
    assembled = assemble_policy_extraction_candidate(
        raw_candidate(),
        record,
    )

    result = validate_policy_extraction_candidate(
        assembled,
        RAW_TEXT,
    )

    assert any(
        error["error_type"] == "missing_policy_id"
        for error in result["errors"]
    )


if __name__ == "__main__":

    test_assembler_injects_policy_id_from_incent_key()
    test_assembler_attaches_source_metadata()
    test_assembler_preserves_existing_policy_id()
    test_assembler_does_not_mutate_raw_candidate()
    test_assembled_candidate_passes_policy_id_and_normalized_evidence_gate()
    test_missing_incent_key_still_reports_missing_policy_id()
    print("test_policy_extraction_candidate_assembler passed")
