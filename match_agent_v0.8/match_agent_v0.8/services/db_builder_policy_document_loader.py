import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

import fitz


SUPPORTED_EXTENSIONS = {
    ".json",
    ".pdf",
    ".txt",
    ".md",
    ".docx",
}


@dataclass
class PolicyDocumentRecord:
    document_id: str
    source_file: str
    source_url: Optional[str]
    raw_text: str
    metadata: Dict[str, Any]

    def to_dict(
        self
    ) -> Dict[str, Any]:

        return {
            "document_id":
                self.document_id,
            "source_document_id":
                self.document_id,
            "source_file":
                self.source_file,
            "source_url":
                self.source_url,
            "raw_text":
                self.raw_text,
            "metadata":
                self.metadata,
        }


def load_policy_documents(
    docs_root,
) -> List[PolicyDocumentRecord]:

    root = Path(
        docs_root
    )

    if not root.exists():

        raise FileNotFoundError(
            f"source file or directory not found: {root}"
        )

    if root.is_file():

        return [
            load_policy_document_file(
                root
            )
        ]

    records = []

    for path in sorted(
        root.rglob(
            "*"
        )
    ):

        if not path.is_file():

            continue

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:

            continue

        if path.name.lower().endswith(
            "_meta.json"
        ):

            continue

        records.append(
            load_policy_document_file(
                path
            )
        )

    return records


def load_policy_document_file(
    source_file,
) -> PolicyDocumentRecord:

    path = Path(
        source_file
    )

    if not path.exists() or not path.is_file():

        raise FileNotFoundError(
            f"source file not found: {path}"
        )

    metadata = _load_sidecar_metadata(
        path
    )
    raw_text = extract_raw_text(
        path
    )

    if not raw_text.strip():

        raise ValueError(
            f"raw_text is empty: {path}"
        )

    document_id = _document_id_from_path(
        path
    )
    source_url = (
        metadata.get(
            "source_url"
        )
        or metadata.get(
            "url"
        )
    )

    return PolicyDocumentRecord(
        document_id=document_id,
        source_file=str(
            path
        ),
        source_url=source_url,
        raw_text=raw_text,
        metadata=metadata,
    )


def extract_raw_text(
    path,
) -> str:

    source_path = Path(
        path
    )
    extension = source_path.suffix.lower()

    if extension in {
        ".txt",
        ".md",
    }:

        return source_path.read_text(
            encoding="utf-8"
        )

    if extension == ".json":

        return _read_json_text(
            source_path
        )

    if extension == ".pdf":

        return _read_pdf_text(
            source_path
        )

    if extension == ".docx":

        return _read_docx_text(
            source_path
        )

    raise ValueError(
        f"unsupported source file extension: {extension}"
    )


def attach_source_fields(
    candidate: Optional[Dict[str, Any]],
    document: PolicyDocumentRecord,
) -> Optional[Dict[str, Any]]:

    if candidate is None:

        return None

    enriched = dict(
        candidate
    )
    enriched[
        "source_document_id"
    ] = document.document_id
    enriched[
        "source_url"
    ] = document.source_url
    enriched[
        "source_file"
    ] = document.source_file

    return enriched


def _read_json_text(
    path: Path,
) -> str:

    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:

        data = json.load(
            handle
        )

    if isinstance(
        data,
        dict,
    ) and isinstance(
        data.get(
            "content"
        ),
        str,
    ):

        return data[
            "content"
        ]

    return json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
    )


def _read_pdf_text(
    path: Path,
) -> str:

    with fitz.open(
        path
    ) as document:

        return "\n".join(
            page.get_text()
            for page in document
        )


def _read_docx_text(
    path: Path,
) -> str:

    paragraphs = []

    with zipfile.ZipFile(
        path
    ) as archive:

        with archive.open(
            "word/document.xml"
        ) as document_xml:

            root = ElementTree.fromstring(
                document_xml.read()
            )

    namespace = {
        "w":
            "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    }

    for paragraph in root.findall(
        ".//w:p",
        namespace,
    ):

        parts = [
            node.text
            for node in paragraph.findall(
                ".//w:t",
                namespace,
            )
            if node.text
        ]

        if parts:

            paragraphs.append(
                "".join(
                    parts
                )
            )

    return "\n".join(
        paragraphs
    )


def _load_sidecar_metadata(
    path: Path,
) -> Dict[str, Any]:

    metadata_path = _sidecar_metadata_path(
        path
    )

    if not metadata_path.exists():

        return {}

    with metadata_path.open(
        "r",
        encoding="utf-8",
    ) as handle:

        metadata = json.load(
            handle
        )

    if not isinstance(
        metadata,
        dict,
    ):

        return {}

    return metadata


def _sidecar_metadata_path(
    path: Path,
) -> Path:

    if path.name.endswith(
        "_raw.txt"
    ):

        return path.with_name(
            path.name.replace(
                "_raw.txt",
                "_meta.json",
            )
        )

    return path.with_name(
        f"{path.stem}_meta.json"
    )


def _document_id_from_path(
    path: Path,
) -> str:

    name = path.stem

    if name.endswith(
        "_raw"
    ):

        name = name[
            :-4
        ]

    return re.sub(
        r"[^A-Za-z0-9_.-]+",
        "_",
        name,
    ).strip(
        "_"
    )
