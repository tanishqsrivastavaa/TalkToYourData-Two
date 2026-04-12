from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fastapi import status
from fastapi.exceptions import HTTPException

from backend.app.db.models import SourceType
from backend.app.modules.common.text import sanitize_metadata, sanitize_text


@dataclass(slots=True)
class ParsedDocument:
    text: str
    metadata: dict[str, str | int]


class BaseParser:
    supported_source_type: SourceType

    async def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        raise NotImplementedError


class UnsupportedDocumentError(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class PlainTextParser(BaseParser):
    supported_source_type = SourceType.txt

    async def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        if b"\x00" in file_bytes:
            raise UnsupportedDocumentError(
                "Unsupported binary document. Upload PDF, TXT, Markdown, or extracted webpage text.",
            )
        text = sanitize_text(file_bytes).strip()
        if not text:
            raise UnsupportedDocumentError("Document does not contain readable text.")
        return ParsedDocument(
            text=text,
            metadata=sanitize_metadata({"filename": filename}),
        )


class MarkdownParser(PlainTextParser):
    supported_source_type = SourceType.markdown


class PdfParser(BaseParser):
    supported_source_type = SourceType.pdf

    async def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        text = sanitize_text(file_bytes).strip()
        if not text:
            raise UnsupportedDocumentError("PDF does not contain readable text.")
        return ParsedDocument(
            text=text,
            metadata=sanitize_metadata({"filename": filename, "warning": "pdf parser fallback"}),
        )


def infer_source_type(filename: str, content_type: str | None) -> SourceType:
    suffix = Path(filename).suffix.lower()
    if suffix in {".zip", ".png", ".jpg", ".jpeg", ".gif", ".doc", ".docx"}:
        raise UnsupportedDocumentError(
            "Unsupported document type. Upload PDF, TXT, Markdown, or extracted webpage text.",
        )
    if suffix == ".pdf" or content_type == "application/pdf":
        return SourceType.pdf
    if suffix in {".md", ".markdown"} or content_type == "text/markdown":
        return SourceType.markdown
    return SourceType.txt


class ParserRegistry:
    def __init__(self) -> None:
        self._parsers = {
            SourceType.txt: PlainTextParser(),
            SourceType.markdown: MarkdownParser(),
            SourceType.pdf: PdfParser(),
        }

    def get(self, source_type: SourceType) -> BaseParser:
        return self._parsers[source_type]
