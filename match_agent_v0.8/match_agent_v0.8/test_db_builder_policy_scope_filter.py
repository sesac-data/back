import sys
from pathlib import Path

from services.db_builder_policy_document_loader import PolicyDocumentRecord


ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )

from scripts.run_policy_extraction_from_db_builder import (  # noqa: E402
    PARENTAL_SUPPORT_DOCUMENT_IDS,
    filter_parental_support_documents,
)


def make_document(
    document_id,
):

    return PolicyDocumentRecord(
        document_id=document_id,
        source_file=f"incent_docs/{document_id}_raw.txt",
        source_url=None,
        raw_text="policy source",
        metadata={
            "incent_key":
                document_id,
        },
    )


def test_parental_support_scope_includes_only_requested_policy_documents():

    documents = [
        make_document(
            "parental_leave_reduction_support"
        ),
        make_document(
            "replacement_workshare_support"
        ),
        make_document(
            "worklife_balance_45_support"
        ),
        make_document(
            "childcare_flexible_start_support"
        ),
        make_document(
            "working_hours_reduction_support"
        ),
        make_document(
            "flexible_work_incent"
        ),
        make_document(
            "flexible_work_system_support"
        ),
        make_document(
            "elders_employ_incent"
        ),
        make_document(
            "youth_hire_incent"
        ),
    ]

    filtered = filter_parental_support_documents(
        documents
    )

    assert [
        document.document_id
        for document in filtered
    ] == [
        "parental_leave_reduction_support",
        "replacement_workshare_support",
        "worklife_balance_45_support",
        "childcare_flexible_start_support",
        "working_hours_reduction_support",
        "flexible_work_incent",
        "flexible_work_system_support",
    ]


def test_scope_explicitly_excludes_elders_employ_incent():

    assert "elders_employ_incent" not in PARENTAL_SUPPORT_DOCUMENT_IDS


def test_scope_excludes_general_employment_incentives():

    excluded_document_ids = {
        "elders_employ_incent",
        "youth_hire_incent",
        "employ_promo_incent",
        "perm_conv_incent",
    }

    assert PARENTAL_SUPPORT_DOCUMENT_IDS.isdisjoint(
        excluded_document_ids
    )


def test_scope_includes_childcare_related_flexible_work_supports():

    included_document_ids = {
        "parental_leave_reduction_support",
        "replacement_workshare_support",
        "worklife_balance_45_support",
        "childcare_flexible_start_support",
        "working_hours_reduction_support",
        "flexible_work_incent",
        "flexible_work_system_support",
    }

    assert included_document_ids.issubset(
        PARENTAL_SUPPORT_DOCUMENT_IDS
    )


if __name__ == "__main__":

    test_parental_support_scope_includes_only_requested_policy_documents()
    test_scope_explicitly_excludes_elders_employ_incent()
    test_scope_excludes_general_employment_incentives()
    test_scope_includes_childcare_related_flexible_work_supports()
    print("test_db_builder_policy_scope_filter passed")
