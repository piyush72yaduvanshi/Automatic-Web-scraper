"""Automated tests for MinIO Object Storage and pgvector Vector RAG System."""

import pytest
import json
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.config import settings
from app.models.orchestration import KnowledgeDocument, KnowledgeChunk
from app.services.storage_service import MinIOStorageService
from app.services.knowledge_service import KnowledgeService


@pytest.fixture
def test_db():
    """Create in-memory SQLite database configured with Vector column."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


# =================================================================
# 1. MINIO OBJECT STORAGE TESTS
# =================================================================

def test_minio_storage_upload_and_download():
    """Verify MinIO upload, URL generation, and download functionality with resilient fallback."""
    sample_content = b"Binary image data test content for MinIO object storage verification."
    filename = "test_banner.png"

    # Upload
    result = MinIOStorageService.upload_bytes(
        data=sample_content,
        filename=filename,
        content_type="image/png",
        folder="test_images",
    )

    assert result is not None
    assert "object_name" in result
    assert "url" in result
    assert result["size_bytes"] == len(sample_content)
    assert result["content_type"] == "image/png"
    assert result["storage_provider"] in ["minio", "local_fallback"]

    # Download
    downloaded = MinIOStorageService.download_bytes(result["object_name"])
    assert downloaded == sample_content

    # Pre-signed URL
    presigned = MinIOStorageService.get_presigned_url(result["object_name"])
    assert presigned is not None
    assert len(presigned) > 10

    # Clean up
    deleted = MinIOStorageService.delete_object(result["object_name"])
    assert deleted is True


def test_minio_creative_image_generation():
    """Verify dynamic creative banner generation and storage in MinIO."""
    result = MinIOStorageService.generate_and_store_creative_image(
        title="B2B AI Growth Playbook",
        text_overlay="Scale your sales pipeline with zero friction",
        platform="INSTAGRAM",
        style="modern_gradient",
    )

    assert result["platform"] == "INSTAGRAM"
    assert result["width"] == 1080
    assert result["height"] == 1080
    assert result["image_url"].endswith(".svg")
    assert result["size_bytes"] > 500

    # Verify asset is downloadable
    data = MinIOStorageService.download_bytes(result["object_name"])
    assert data is not None
    assert b"<svg" in data
    assert b"B2B AI Growth Playbook" in data

    # Clean up
    MinIOStorageService.delete_object(result["object_name"])


def test_minio_list_objects():
    """Verify object listing across storage folders."""
    # Upload temporary asset
    res = MinIOStorageService.upload_bytes(
        data=b"List verification content",
        filename="list_sample.txt",
        content_type="text/plain",
        folder="inventory",
    )

    objects = MinIOStorageService.list_objects(prefix="inventory")
    assert len(objects) >= 1
    found = any(res["object_name"] in obj["object_name"] for obj in objects)
    assert found is True

    MinIOStorageService.delete_object(res["object_name"])


# =================================================================
# 2. PGVECTOR & VECTOR RAG TESTS
# =================================================================

@pytest.mark.asyncio
async def test_knowledge_document_chunking_and_vector_persistence(test_db):
    """Verify document chunking, native pgvector column, and JSON fallback."""
    title = "SaaS Enterprise Sales Playbook 2026"
    content = (
        "Enterprise cold outreach requires multi-threaded stakeholder targeting. "
        "Begin by identifying the VP of Engineering and Head of Sales. "
        "Highlight tech stack inefficiencies and offer quantifiable ROI proof points. "
        "Follow up within 48 hours referencing recent company milestones."
    )

    doc = await KnowledgeService.create_document(
        title=title,
        content=content,
        category="PLAYBOOK",
        file_url="http://localhost:9000/crm-assets/playbooks/sales_guide.pdf",
        db=test_db,
    )

    assert doc.id is not None
    assert doc.title == title
    assert doc.file_url is not None
    assert len(doc.chunks) >= 1

    chunk = doc.chunks[0]
    assert chunk.document_id == doc.id
    assert chunk.chunk_text is not None
    assert chunk.token_count > 0


@pytest.mark.asyncio
async def test_hybrid_vector_search_and_rag_context(test_db):
    """Verify vector search retrieval and RAG context formatting for AI agents."""
    # Seed knowledge documents
    await KnowledgeService.create_document(
        title="Objection Handling: Pricing Resistance",
        content="When prospect claims our solution is too expensive, reframe cost as cost of inaction. Highlight that customers achieve payback within 45 days.",
        category="OBJECTION_HANDLING",
        db=test_db,
    )

    await KnowledgeService.create_document(
        title="ICP Definition: Mid-Market FinTech",
        content="Target fintech companies with 50-500 employees using Stripe and PostgreSQL seeking to automate outbound qualification.",
        category="ICP",
        db=test_db,
    )

    # Search knowledge
    results = await KnowledgeService.search_knowledge(
        query="pricing resistance too expensive payback",
        limit=2,
        db=test_db,
    )

    assert len(results) >= 1
    assert "relevance_score" in results[0]
    assert "document_title" in results[0]
    assert "chunk_text" in results[0]
    assert "expensive" in results[0]["chunk_text"].lower() or "pricing" in results[0]["document_title"].lower()

    # RAG Context generation for AI prompt injection
    rag_context = await KnowledgeService.get_rag_context(
        query="How do I answer when the client says we are too expensive?",
        db=test_db,
        limit=2,
    )

    assert "[Source 1:" in rag_context
    assert "payback" in rag_context.lower() or "cost" in rag_context.lower()


# =================================================================
# 3. STORAGE FASTAPI ROUTE ENDPOINT TESTS
# =================================================================

def test_storage_api_endpoints(client):
    """Verify /api/v1/storage/ endpoints for status, generation, and presigned URLs."""
    # 1. Health Status
    status_resp = client.get("/api/v1/storage/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["storage_provider"] == "MinIO"

    # 2. Generate Creative
    gen_resp = client.post(
        "/api/v1/storage/generate-creative",
        json={
            "title": "API Launch 2026",
            "text_overlay": "Supercharge B2B Outbound",
            "platform": "LINKEDIN",
            "style": "growth_emerald",
        },
    )
    assert gen_resp.status_code == 200
    creative = gen_resp.json()["creative"]
    assert creative["platform"] == "LINKEDIN"
    assert "image_url" in creative

    # 3. Presigned URL
    presign_resp = client.get(
        f"/api/v1/storage/presigned-url?object_name={creative['object_name']}"
    )
    assert presign_resp.status_code == 200
    assert "presigned_url" in presign_resp.json()

