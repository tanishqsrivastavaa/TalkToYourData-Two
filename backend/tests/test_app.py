import os

import anyio
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["APP_ENV"] = "test"

from backend.app.main import app
from backend.app.db.session import engine


async def _reset_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


@pytest.fixture(autouse=True)
def reset_database() -> None:
    anyio.run(_reset_database)


def test_root_route() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Talk to Your Data API"}


def test_healthcheck_route() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_and_fetch_document() -> None:
    with TestClient(app) as client:
        upload_response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("notes.txt", b"Transformers use attention mechanisms.", "text/plain")},
        )

        assert upload_response.status_code == 202
        payload = upload_response.json()
        assert payload["status"] == "success"

        document_response = client.get(f"/api/v1/documents/{payload['document_id']}")

    assert document_response.status_code == 200
    document = document_response.json()
    assert document["filename"] == "notes.txt"
    assert document["status"] == "indexed"


def test_query_returns_grounded_sources_for_uploaded_document() -> None:
    with TestClient(app) as client:
        upload_response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("paper.txt", b"Transformers use attention for sequence modeling.", "text/plain")},
        )
        document_id = upload_response.json()["document_id"]

        query_response = client.post(
            "/api/v1/queries",
            json={
                "question": "What does the paper say about attention?",
                "document_ids": [document_id],
            },
        )

    assert query_response.status_code == 200
    payload = query_response.json()
    assert "attention" in payload["answer"].lower()
    assert payload["sources"]
    assert payload["planner"]["document_ids"] == [document_id]


def test_binary_pdf_upload_returns_client_error() -> None:
    with TestClient(app) as client:
        upload_response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("scan.pdf", b"\x00\xff\xfe\x00", "application/pdf")},
        )

    assert upload_response.status_code == 400
    assert "readable text" in upload_response.json()["detail"].lower()
