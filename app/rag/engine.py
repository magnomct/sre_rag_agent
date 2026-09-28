"""
SRE RAG Agent — RAG Engine Module
Core retrieval-augmented generation logic with caching and metrics.
"""

import json
import time
import hashlib
import structlog
import redis
from config import settings
from metrics import (
    RAG_QUERIES_TOTAL,
    RAG_QUERY_DURATION,
    RAG_DOCUMENTS_RETRIEVED,
    CACHE_HITS_TOTAL,
    CACHE_MISSES_TOTAL,
    DB_QUERY_DURATION,
)
from rag.embeddings import generate_query_embedding

logger = structlog.get_logger()


class RAGEngine:
    """
    RAG Engine — retrieves relevant documents and generates answers.
    Uses Redis for caching and PostgreSQL (pgvector) for vector search.
    """

    def __init__(self):
        self._redis_client = None
        self._cache_ttl = 3600  # 1 hour

    @property
    def redis_client(self):
        if self._redis_client is None:
            self._redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password or None,
                decode_responses=True,
                socket_timeout=5,
            )
        return self._redis_client

    def _cache_key(self, query: str) -> str:
        """Generate a deterministic cache key for a query."""
        return f"rag:query:{hashlib.sha256(query.encode()).hexdigest()[:16]}"

    def _get_cached_result(self, query: str) -> dict | None:
        """Try to get a cached result for a query."""
        try:
            key = self._cache_key(query)
            cached = self.redis_client.get(key)
            if cached:
                CACHE_HITS_TOTAL.inc()
                logger.debug("cache_hit", query=query[:50])
                return json.loads(cached)
            CACHE_MISSES_TOTAL.inc()
            return None
        except Exception as e:
            logger.warning("cache_read_error", error=str(e))
            CACHE_MISSES_TOTAL.inc()
            return None

    def _cache_result(self, query: str, result: dict):
        """Cache a query result."""
        try:
            key = self._cache_key(query)
            self.redis_client.setex(key, self._cache_ttl, json.dumps(result))
        except Exception as e:
            logger.warning("cache_write_error", error=str(e))

    def _retrieve_documents(self, query_embedding: list[float]) -> list[dict]:
        """
        Retrieve relevant documents from PostgreSQL using vector similarity.

        In production, this would query pgvector. For now, returns mock SRE documents.
        """
        # TODO: Implement pgvector search when PostgreSQL is ready
        # This mock data demonstrates the structure
        mock_documents = [
            {
                "id": "doc-001",
                "title": "SLO Best Practices",
                "content": "Service Level Objectives should be defined based on user experience...",
                "score": 0.92,
            },
            {
                "id": "doc-002",
                "title": "Incident Response Runbook",
                "content": "When an alert fires, first acknowledge it, then triage the severity...",
                "score": 0.87,
            },
            {
                "id": "doc-003",
                "title": "Kubernetes Troubleshooting",
                "content": "Check pod status with kubectl get pods, then describe for events...",
                "score": 0.83,
            },
        ]
        return mock_documents[: settings.top_k]

    async def query(self, question: str) -> dict:
        """
        Process a RAG query: embed → retrieve → generate answer.

        Args:
            question: User question string.

        Returns:
            Dict with answer, sources, and metadata.
        """
        start_time = time.time()

        try:
            # 1. Check cache
            cached = self._get_cached_result(question)
            if cached:
                RAG_QUERIES_TOTAL.labels(status="cache_hit").inc()
                cached["from_cache"] = True
                return cached

            # 2. Generate query embedding
            query_embedding = generate_query_embedding(question)

            # 3. Retrieve relevant documents
            with DB_QUERY_DURATION.labels(
                database="postgresql", operation="vector_search"
            ).time():
                documents = self._retrieve_documents(query_embedding)

            RAG_DOCUMENTS_RETRIEVED.observe(len(documents))

            # 4. Build result
            result = {
                "question": question,
                "answer": self._generate_answer(question, documents),
                "sources": documents,
                "metadata": {
                    "documents_retrieved": len(documents),
                    "model": settings.embedding_model,
                    "processing_time_seconds": round(time.time() - start_time, 4),
                },
                "from_cache": False,
            }

            # 5. Cache result
            self._cache_result(question, result)

            RAG_QUERIES_TOTAL.labels(status="success").inc()
            duration = time.time() - start_time
            RAG_QUERY_DURATION.observe(duration)

            logger.info(
                "rag_query_completed",
                question=question[:100],
                documents_found=len(documents),
                duration_seconds=round(duration, 4),
            )

            return result

        except Exception as e:
            RAG_QUERIES_TOTAL.labels(status="error").inc()
            duration = time.time() - start_time
            RAG_QUERY_DURATION.observe(duration)
            logger.error(
                "rag_query_failed",
                question=question[:100],
                error=str(e),
                duration_seconds=round(duration, 4),
            )
            raise

    def _generate_answer(self, question: str, documents: list[dict]) -> str:
        """
        Generate an answer from retrieved documents.
        In production, this would call an LLM. For now, returns a structured summary.
        """
        if not documents:
            return "No relevant documents found for your question."

        context = "\n".join(
            [f"- {doc['title']}: {doc['content']}" for doc in documents]
        )
        return (
            f"Based on {len(documents)} relevant documents:\n\n"
            f"{context}\n\n"
            f"(This is a mock response. In production, an LLM would synthesize this.)"
        )


# Singleton instance
rag_engine = RAGEngine()
