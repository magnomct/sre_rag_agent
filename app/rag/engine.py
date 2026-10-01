"""
SRE RAG Agent — RAG Engine Module
Core retrieval-augmented generation logic with caching, live vector retrieval and metrics.
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
from rag.indexer import sre_indexer

logger = structlog.get_logger()


class RAGEngine:
    """
    RAG Engine — retrieves relevant SRE documents from the vector index and generates answers.
    Uses Redis for caching and SRE Knowledge Indexer for semantic vector search.
    """

    def __init__(self):
        self._redis_client = None
        self._redis_disabled = False
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
                socket_timeout=3,
            )
        return self._redis_client

    def _cache_key(self, query: str) -> str:
        """Generate a deterministic cache key for a query."""
        return f"rag:query:{hashlib.sha256(query.encode()).hexdigest()[:16]}"

    def _get_cached_result(self, query: str) -> dict | None:
        """Try to get a cached result for a query."""
        if self._redis_disabled:
            return None
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
            self._redis_disabled = True
            logger.debug("redis_offline_disabled_caching", reason=str(e))
            CACHE_MISSES_TOTAL.inc()
            return None

    def _cache_result(self, query: str, result: dict):
        """Cache a query result."""
        if self._redis_disabled:
            return
        try:
            key = self._cache_key(query)
            self.redis_client.setex(key, self._cache_ttl, json.dumps(result))
        except Exception as e:
            logger.debug("cache_write_skipped", reason=str(e))

    def _retrieve_documents(self, query_embedding: list[float]) -> list[dict]:
        """
        Retrieve relevant SRE documents using cosine similarity over the corpus index.
        """
        # Vector search via SRE Knowledge Indexer (runbooks, postmortems, architecture)
        docs = sre_indexer.search(
            query_embedding,
            top_k=settings.top_k,
            min_score=0.15,
        )

        # Fallback if no docs match the minimum score threshold
        if not docs:
            logger.info("vector_search_low_score_fallback")
            docs = sre_indexer.search(query_embedding, top_k=settings.top_k, min_score=0.05)

        return docs

    async def query(self, question: str) -> dict:
        """
        Process a RAG query: embed → retrieve → synthesize SRE answer.

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
                database="vector_store", operation="vector_search"
            ).time():
                documents = self._retrieve_documents(query_embedding)

            RAG_DOCUMENTS_RETRIEVED.observe(len(documents))

            # 4. Synthesize SRE recommendation
            answer = self._generate_answer(question, documents)

            # 5. Build result
            result = {
                "question": question,
                "answer": answer,
                "sources": documents,
                "metadata": {
                    "documents_retrieved": len(documents),
                    "model": settings.embedding_model,
                    "top_score": documents[0]["score"] if documents else 0.0,
                    "processing_time_seconds": round(time.time() - start_time, 4),
                },
                "from_cache": False,
            }

            # 6. Cache result
            self._cache_result(question, result)

            RAG_QUERIES_TOTAL.labels(status="success").inc()
            duration = time.time() - start_time
            RAG_QUERY_DURATION.observe(duration)

            logger.info(
                "rag_query_completed",
                question=question[:100],
                documents_found=len(documents),
                top_source=documents[0]["source"] if documents else None,
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
        Synthesize an actionable SRE operational recommendation based on retrieved context.
        """
        if not documents:
            return (
                "⚠️ Não foram encontrados documentos com relevância suficiente na base de conhecimento SRE "
                "para formular um diagnóstico preciso. Verifique se a pergunta descreve sintomas específicos, "
                "nome de alertas (ex: SLOAvailabilityBurnRateCritical, KubePodCrashLooping) ou componente (Redis, Postgres, DNS)."
            )

        top_doc = documents[0]
        sources_summary = ", ".join([f"`{doc['title']}` ({doc['source']})" for doc in documents[:3]])

        # Build clean formatted SRE recommendation
        answer_parts = [
            f"### 🚨 Diagnóstico & Recomendação SRE",
            f"**Pergunta Analisada:** {question}",
            f"**Fontes Relevantes Identificadas:** {sources_summary}\n",
            "#### 📋 Contexto & Procedimento Operacional (Runbook):",
        ]

        for i, doc in enumerate(documents[:2], 1):
            category_icon = "📖 Runbook" if doc.get("category") == "runbook" else "📝 Postmortem"
            answer_parts.append(
                f"**[{i}] {category_icon}: {doc['title']}** (Relevância: `{int(doc.get('score', 0) * 100)}%`)\n"
                f"{doc['content']}\n"
            )

        answer_parts.extend([
            "#### 💡 Diretrizes de Ação para o Plantonista:",
            "- **Prioridade imediata:** Reduzir o MTTR aplicando a mitigação rápida descrita no runbook (ex: Rollback, Cordon/Drain ou aumento de limite).",
            "- **Investigação de Causa Raiz:** Inspecione logs (`kubectl logs --previous`) e métricas do Prometheus antes de alterar arquitetura.",
            "- **Anti-Pattern:** Evite reinicializações cegas de banco de dados ou deleção de pods sem identificar a causa da falha.",
        ])

        return "\n".join(answer_parts)


# Singleton instance
rag_engine = RAGEngine()
