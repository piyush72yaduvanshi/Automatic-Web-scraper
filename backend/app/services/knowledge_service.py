"""Knowledge Base and RAG Retrieval Service.

Manages sales playbooks, services, ICP definitions, and objection handlers.
Supports document chunking, vector embedding search, and lexical keyword fallback search
with source citations.
"""

from typing import Dict, Any, List, Optional
import uuid
import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.orchestration import KnowledgeDocument, KnowledgeChunk
from app.providers.ai.router import ai_router

logger = logging.getLogger(__name__)


class KnowledgeService:
    """RAG and Knowledge Repository Engine."""

    @classmethod
    def list_documents(cls, db: Session, category: Optional[str] = None) -> List[KnowledgeDocument]:
        q = db.query(KnowledgeDocument)
        if category:
            q = q.filter(KnowledgeDocument.category == category)
        return q.order_by(desc(KnowledgeDocument.created_at)).all()

    @classmethod
    async def create_document(
        cls,
        title: str,
        content: str,
        category: str = "SERVICE_OFFERING",
        db: Session = None,
    ) -> KnowledgeDocument:
        """Create document, auto-chunk, and compute embeddings."""
        doc = KnowledgeDocument(
            title=title,
            content=content,
            category=category,
        )
        db.add(doc)
        db.flush()

        # Chunk text (approx 500 chars per chunk with 100 char overlap)
        chunks = cls._chunk_text(content, chunk_size=600, overlap=100)
        for idx, chunk_str in enumerate(chunks):
            # Compute embedding
            emb_vector = await ai_router.generate_embeddings(chunk_str)
            chunk_rec = KnowledgeChunk(
                document_id=doc.id,
                chunk_index=idx,
                chunk_text=chunk_str,
                embedding_json=json.dumps(emb_vector) if emb_vector else None,
                token_count=len(chunk_str.split()),
            )
            db.add(chunk_rec)

        db.commit()
        db.refresh(doc)
        return doc

    @classmethod
    def _chunk_text(cls, text: str, chunk_size: int = 600, overlap: int = 100) -> List[str]:
        if len(text) <= chunk_size:
            return [text]
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end == len(text):
                break
            start += chunk_size - overlap
        return chunks

    @classmethod
    async def search_knowledge(
        cls,
        query: str,
        limit: int = 5,
        db: Session = None,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid vector and lexical search across knowledge chunks.
        Never fails if embedding service is down; seamlessly falls back to keyword matching.
        """
        query_emb = await ai_router.generate_embeddings(query)
        chunks = db.query(KnowledgeChunk).all()
        if not chunks:
            return []

        scored_chunks = []
        q_words = set(query.lower().split())

        for ch in chunks:
            score = 0.0
            # 1. Vector cosine similarity if embedding is available
            if query_emb and ch.embedding_json:
                try:
                    c_vec = json.loads(ch.embedding_json)
                    score = cls._cosine_similarity(query_emb, c_vec)
                except Exception:
                    score = 0.0

            # 2. Lexical keyword overlap bonus
            ch_words = set(ch.chunk_text.lower().split())
            overlap = len(q_words.intersection(ch_words))
            score += (overlap / (len(q_words) or 1)) * 0.5

            scored_chunks.append((score, ch))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_results = scored_chunks[:limit]

        return [
            {
                "document_title": ch.document.title if ch.document else "Knowledge Doc",
                "category": ch.document.category if ch.document else "General",
                "chunk_text": ch.chunk_text,
                "relevance_score": round(score, 3),
            }
            for score, ch in top_results
        ]

    @classmethod
    def _cosine_similarity(cls, vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = sum(a * a for a in vec_a) ** 0.5
        norm_b = sum(b * b for b in vec_b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
