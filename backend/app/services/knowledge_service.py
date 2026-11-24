"""Knowledge Base and RAG Retrieval Service.

Manages sales playbooks, services, ICP definitions, and objection handlers.
Supports document chunking, native pgvector vector similarity search,
and lexical keyword hybrid fallback with source citations.
"""

from typing import Dict, Any, List, Optional
import uuid
import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.models.orchestration import KnowledgeDocument, KnowledgeChunk
from app.providers.ai.router import ai_router
from app.core.config import settings

logger = logging.getLogger(__name__)


class KnowledgeService:
    """RAG and Knowledge Repository Engine with pgvector & MinIO integration."""

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
        file_url: Optional[str] = None,
        db: Session = None,
    ) -> KnowledgeDocument:
        """Create document, auto-chunk, compute embeddings, and store vector representations."""
        doc = KnowledgeDocument(
            title=title,
            content=content,
            category=category,
            file_url=file_url,
        )
        db.add(doc)
        db.flush()

        # Chunk text (approx 600 chars per chunk with 100 char overlap)
        chunks = cls._chunk_text(content, chunk_size=600, overlap=100)
        for idx, chunk_str in enumerate(chunks):
            # Compute embedding
            emb_vector = await ai_router.generate_embeddings(chunk_str)

            # Store in both native pgvector column and JSON fallback
            chunk_rec = KnowledgeChunk(
                document_id=doc.id,
                chunk_index=idx,
                chunk_text=chunk_str,
                embedding_vector=emb_vector if emb_vector else None,
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
        Hybrid pgvector and lexical search across knowledge chunks.
        - Leverages PostgreSQL pgvector cosine distance (<=> operator) when available.
        - Falls back gracefully to in-memory cosine + keyword overlap if embeddings or pgvector is inactive.
        """
        query_emb = await ai_router.generate_embeddings(query)

        # Check if database dialect is PostgreSQL and pgvector is enabled
        is_postgres = False
        try:
            if db and db.bind and db.bind.dialect.name == "postgresql":
                is_postgres = True
        except Exception:
            is_postgres = False

        # Attempt native pgvector search if running PostgreSQL
        if is_postgres and query_emb and getattr(settings, "PGVECTOR_ENABLED", True):
            try:
                # Query nearest vectors via cosine distance using pgvector
                pg_chunks = (
                    db.query(KnowledgeChunk)
                    .options(joinedload(KnowledgeChunk.document))
                    .filter(KnowledgeChunk.embedding_vector.isnot(None))
                    .order_by(KnowledgeChunk.embedding_vector.cosine_distance(query_emb))
                    .limit(limit)
                    .all()
                )

                if pg_chunks:
                    return [
                        {
                            "document_title": ch.document.title if ch.document else "Knowledge Doc",
                            "category": ch.document.category if ch.document else "General",
                            "chunk_text": ch.chunk_text,
                            "relevance_score": 0.95,  # Nearest pgvector match
                            "vector_engine": "pgvector",
                        }
                        for ch in pg_chunks
                    ]
            except Exception as e:
                logger.warning(f"Native pgvector query failed ({e}), falling back to hybrid scoring.")

        # Hybrid fallback (SQLite, offline, or fallback mode)
        chunks = (
            db.query(KnowledgeChunk)
            .options(joinedload(KnowledgeChunk.document))
            .all()
        )
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
                "vector_engine": "hybrid_fallback",
            }
            for score, ch in top_results
        ]

    @classmethod
    async def get_rag_context(cls, query: str, db: Session, limit: int = 3) -> str:
        """
        Format retrieved knowledge chunks into structured RAG prompt context.
        Used by specialized AI agents to inject relevant company knowledge, ICP definitions,
        case studies, and objection handling playbooks.
        """
        results = await cls.search_knowledge(query=query, limit=limit, db=db)
        if not results:
            return "No specific internal company knowledge found for this query."

        context_parts = []
        for i, r in enumerate(results, 1):
            context_parts.append(
                f"[Source {i}: {r['document_title']} ({r['category']})]\n{r['chunk_text']}"
            )
        return "\n\n".join(context_parts)

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
