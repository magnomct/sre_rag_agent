"""
SRE RAG Agent — Embedding Module
Handles text embedding generation using sentence-transformers.
"""

import time
import structlog
from sentence_transformers import SentenceTransformer
from config import settings
from metrics import RAG_EMBEDDING_DURATION

logger = structlog.get_logger()

# Lazy-loaded model singleton
_model = None


def get_model() -> SentenceTransformer:
    """Get or initialize the embedding model (singleton)."""
    global _model
    if _model is None:
        logger.info("loading_embedding_model", model=settings.embedding_model)
        start = time.time()
        _model = SentenceTransformer(settings.embedding_model)
        duration = time.time() - start
        logger.info(
            "embedding_model_loaded",
            model=settings.embedding_model,
            duration_seconds=round(duration, 2),
        )
    return _model


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors.
    """
    model = get_model()
    with RAG_EMBEDDING_DURATION.time():
        embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


def generate_query_embedding(query: str) -> list[float]:
    """
    Generate embedding for a single query.

    Args:
        query: Query string.

    Returns:
        Embedding vector.
    """
    return generate_embeddings([query])[0]
