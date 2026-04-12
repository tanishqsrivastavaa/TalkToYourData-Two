import anyio
import pytest

from backend.app.modules.ingestion.parsers import PlainTextParser, UnsupportedDocumentError, infer_source_type
from backend.app.db.models import SourceType


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
