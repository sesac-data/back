from copy import deepcopy
from typing import Any, Dict, Optional

from services.db_builder_policy_document_loader import PolicyDocumentRecord


def assemble_policy_extraction_candidate(
    raw_candidate: Optional[Dict[str, Any]],
    document: PolicyDocumentRecord,
) -> Optional[Dict[str, Any]]:
    """Attach system-owned db_builder metadata without changing raw_candidate."""

    if raw_candidate is None:
        return None

    assembled = deepcopy(
        raw_candidate
    )
    incent_key = document.metadata.get(
        "incent_key"
    )

    if _is_blank(
        assembled.get(
            "policy_id"
        )
    ) and not _is_blank(
        incent_key
    ):
        assembled[
            "policy_id"
        ] = incent_key

    assembled[
        "source_document_id"
    ] = document.document_id
    assembled[
        "source_url"
    ] = document.source_url
    assembled[
        "source_file"
    ] = document.source_file

    return assembled


def _is_blank(
    value: Any,
) -> bool:

    return value is None or (
        isinstance(
            value,
            str,
        )
        and not value.strip()
    )
