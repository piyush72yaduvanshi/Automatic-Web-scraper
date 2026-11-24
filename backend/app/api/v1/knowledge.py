"""API endpoints for Knowledge Base & RAG."""

from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from app.core.database import get_db
from app.core.security import verify_api_key
from app.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/documents")
def list_documents(category: Optional[str] = None, db: Session = Depends(get_db)):
    """List knowledge base documents."""
    docs = KnowledgeService.list_documents(db, category)
    return [
        {
            "id": str(d.id),
            "title": d.title,
            "category": d.category,
            "chunks_count": len(d.chunks),
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ]


@router.post("/documents")
async def create_document(
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Add a document to the knowledge base with automatic chunking and embedding."""
    title = data.get("title")
    content = data.get("content")
    if not title or not content:
        raise HTTPException(status_code=400, detail="title and content are required")

    doc = await KnowledgeService.create_document(
        title=title,
        content=content,
        category=data.get("category", "SERVICE_OFFERING"),
        db=db,
    )
    return {"id": str(doc.id), "title": doc.title, "chunks_count": len(doc.chunks), "status": "created"}


@router.post("/search")
async def search_knowledge(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
):
    """Hybrid semantic vector and keyword search across stored knowledge chunks."""
    query = payload.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    limit = payload.get("limit", 5)

    results = await KnowledgeService.search_knowledge(query=query, limit=limit, db=db)
    return {"query": query, "results": results}

