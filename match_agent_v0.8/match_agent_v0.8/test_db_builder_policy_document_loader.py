import json
import tempfile
import zipfile
from pathlib import Path

import fitz

from services.db_builder_policy_document_loader import (
    attach_source_fields,
    load_policy_document_file,
    load_policy_documents,
)


def test_load_json_policy_document_uses_content_and_meta_url():

    with tempfile.TemporaryDirectory() as tmp_dir:

        root = Path(
            tmp_dir
        )
        document = root / "sample_raw.json"
        document.write_text(
            json.dumps(
                {
                    "content":
                        "JSON policy text"
                }
            ),
            encoding="utf-8",
        )
        (
            root / "sample_raw_meta.json"
        ).write_text(
            json.dumps(
                {
                    "url":
                        "https://example.test/policy"
                }
            ),
            encoding="utf-8",
        )

        record = load_policy_document_file(
            document
        )

        assert record.raw_text == "JSON policy text"
        assert record.source_url == "https://example.test/policy"
        assert record.document_id == "sample"


def test_load_pdf_policy_document_extracts_text():

    with tempfile.TemporaryDirectory() as tmp_dir:

        path = Path(
            tmp_dir
        ) / "policy.pdf"
        pdf = fitz.open()
        page = pdf.new_page()
        page.insert_text(
            (72, 72),
            "PDF policy text",
        )
        pdf.save(
            path
        )
        pdf.close()

        record = load_policy_document_file(
            path
        )

        assert "PDF policy text" in record.raw_text
        assert record.document_id == "policy"


def test_load_docx_policy_document_extracts_text():

    with tempfile.TemporaryDirectory() as tmp_dir:

        path = Path(
            tmp_dir
        ) / "policy.docx"
        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body><w:p><w:r><w:t>DOCX policy text</w:t></w:r></w:p></w:body>"
            "</w:document>"
        )

        with zipfile.ZipFile(
            path,
            "w",
        ) as archive:

            archive.writestr(
                "word/document.xml",
                xml,
            )

        record = load_policy_document_file(
            path
        )

        assert record.raw_text == "DOCX policy text"


def test_raw_text_missing_error():

    with tempfile.TemporaryDirectory() as tmp_dir:

        path = Path(
            tmp_dir
        ) / "empty.txt"
        path.write_text(
            "",
            encoding="utf-8",
        )

        try:

            load_policy_document_file(
                path
            )
            raised = False

        except ValueError as exc:

            raised = True
            assert "raw_text is empty" in str(
                exc
            )

        assert raised is True


def test_source_file_missing_error():

    try:

        load_policy_document_file(
            "missing-policy-source.txt"
        )
        raised = False

    except FileNotFoundError as exc:

        raised = True
        assert "source file not found" in str(
            exc
        )

    assert raised is True


def test_attach_source_fields_connects_source_without_changing_review_status():

    with tempfile.TemporaryDirectory() as tmp_dir:

        path = Path(
            tmp_dir
        ) / "policy.txt"
        path.write_text(
            "Policy text",
            encoding="utf-8",
        )
        (
            Path(
                tmp_dir
            )
            / "policy_meta.json"
        ).write_text(
            json.dumps(
                {
                    "source_url":
                        "https://example.test/source"
                }
            ),
            encoding="utf-8",
        )
        record = load_policy_document_file(
            path
        )
        candidate = attach_source_fields(
            {
                "review_status":
                    "needs_review",
                "policy_id":
                    "candidate",
            },
            record,
        )

        assert candidate["review_status"] == "needs_review"
        assert candidate["source_document_id"] == "policy"
        assert candidate["source_url"] == "https://example.test/source"
        assert candidate["source_file"] == str(
            path
        )


def test_load_policy_documents_skips_meta_json():

    with tempfile.TemporaryDirectory() as tmp_dir:

        root = Path(
            tmp_dir
        )
        (
            root / "sample_raw.txt"
        ).write_text(
            "Policy text",
            encoding="utf-8",
        )
        (
            root / "sample_meta.json"
        ).write_text(
            json.dumps(
                {
                    "content":
                        "metadata content"
                }
            ),
            encoding="utf-8",
        )

        records = load_policy_documents(
            root
        )

        assert [
            record.document_id
            for record in records
        ] == [
            "sample",
        ]


if __name__ == "__main__":

    test_load_json_policy_document_uses_content_and_meta_url()
    test_load_pdf_policy_document_extracts_text()
    test_load_docx_policy_document_extracts_text()
    test_raw_text_missing_error()
    test_source_file_missing_error()
    test_attach_source_fields_connects_source_without_changing_review_status()
    test_load_policy_documents_skips_meta_json()
    print("test_db_builder_policy_document_loader passed")
