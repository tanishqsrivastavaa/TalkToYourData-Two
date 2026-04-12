import anyio
import pytest

from backend.app.modules.common.text import sanitize_text
from backend.app.db.models import SourceType
from backend.app.modules.ingestion.parsers import PdfParser, PlainTextParser, UnsupportedDocumentError, infer_source_type


def test_binary_plaintext_upload_is_rejected() -> None:
    parser = PlainTextParser()

    with pytest.raises(UnsupportedDocumentError):
        anyio.run(parser.parse, b"abc\x00def", "archive.zip")


def test_supported_markdown_source_type_is_detected() -> None:
    source_type = infer_source_type("notes.md", "text/markdown")

    assert source_type == SourceType.markdown


def test_unsupported_zip_is_rejected() -> None:
    with pytest.raises(UnsupportedDocumentError):
        infer_source_type("archive.zip", "application/zip")


def test_sanitize_text_removes_nulls_and_surrogates() -> None:
    assert sanitize_text("alpha\x00beta\udcffgamma") == "alphabetagamma"


def test_binary_pdf_without_readable_text_is_rejected() -> None:
    parser = PdfParser()

    with pytest.raises(UnsupportedDocumentError):
        anyio.run(parser.parse, b"\x00\xff\xfe\x00", "scan.pdf")
