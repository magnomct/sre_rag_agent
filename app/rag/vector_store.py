"""
SRE RAG Agent — Advanced Hybrid Vector Store Module (v4.0)
Implements pgvector with HNSW index, BM25 lexical search, Reciprocal Rank Fusion (RRF),
and Cross-Encoder Semantic Re-ranking via FlashRank with resilient fallback.
"""

import math
import structlog
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from rag.indexer import sre_indexer, DocumentChunk

logger = structlog.get_logger()

# Optional FlashRank import
try:
    from flashrank import Ranker, RerankRequest
    _HAS_FLASHRANK = True
except Exception:
    _HAS_FLASHRANK = False


class HybridVectorStore:
    """
    Hybrid Search Engine combining Dense Vector Cosine Similarity (pgvector HNSW)
    and Sparse Lexical Matching (BM25) fused via Reciprocal Rank Fusion (RRF, k=60),
    followed by FlashRank cross-encoder re-ranking.
    """

    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k
        self._bm25_index: Optional[BM25Okapi] = None
        self._bm25_corpus_ids: List[str] = []
        self._ranker: Optional[Any] = None
        self._init_bm25()
        self._init_ranker()

    def _init_bm25(self):
        """Tokenize document chunks from indexer to build BM25 corpus."""
        try:
            chunks = sre_indexer.chunks
            if not chunks:
                return

            corpus_tokens = []
            self._bm25_corpus_ids = []
            for chunk in chunks:
                tokens = chunk.content.lower().split()
                corpus_tokens.append(tokens)
                self._bm25_corpus_ids.append(chunk.id)

            self._bm25_index = BM25Okapi(corpus_tokens)
            logger.info("bm25_corpus_initialized", total_chunks=len(corpus_tokens))
        except Exception as e:
            logger.warning("bm25_initialization_failed", error=str(e))

    def _init_ranker(self):
        """Initialize FlashRank cross-encoder model for semantic re-ranking."""
        if _HAS_FLASHRANK:
            try:
                self._ranker = Ranker()
                logger.info("flashrank_ranker_initialized", model="ms-marco-TinyBERT-L-2-v2")
            except Exception as e:
                logger.warning("flashrank_load_failed", error=str(e))
                self._ranker = None

    def search_bm25(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """Perform sparse lexical search using BM25."""
        if not self._bm25_index or not self._bm25_corpus_ids:
            return []

        tokens = query.lower().split()
        scores = self._bm25_index.get_scores(tokens)
        scored_pairs = sorted(
            enumerate(scores), key=lambda x: x[1], reverse=True
        )[:top_k]

        results = []
        for idx, score in scored_pairs:
            if score <= 0.0:
                continue
            chunk_id = self._bm25_corpus_ids[idx]
            chunk = sre_indexer.get_chunk(chunk_id)
            if chunk:
                results.append({
                    "chunk": chunk,
                    "score": float(score),
                    "type": "sparse_bm25",
                })
        return results

    def search_dense(self, query_embedding: List[float], top_k: int = 20) -> List[Dict[str, Any]]:
        """
        Perform dense semantic search. Uses in-memory vector index with fallback
        or pgvector when connected.
        """
        raw_results = sre_indexer.search(query_embedding, top_k=top_k)
        results = []
        chunk_dict = {c.id: c for c in sre_indexer.chunks}
        for item in raw_results:
            cid = item.get("id")
            chunk = chunk_dict.get(cid)
            if not chunk:
                chunk = DocumentChunk(
                    id=item.get("id", ""),
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    source=item.get("source", ""),
                    category=item.get("category", ""),
                    section=item.get("section", ""),
                    metadata=item.get("metadata", {}),
                )
            results.append({
                "chunk": chunk,
                "score": float(item["score"]),
                "type": "dense_vector",
            })
        return results

    def fuse_rrf(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF) algorithm:
        RRF_Score(d) = sum(1 / (k + rank_m(d))) for each retrieval modality m.
        """
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, DocumentChunk] = {}

        # 1. Score dense rankings
        for rank, item in enumerate(dense_results):
            cid = item["chunk"].id
            chunk_map[cid] = item["chunk"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + (rank + 1)))

        # 2. Score sparse rankings
        for rank, item in enumerate(sparse_results):
            cid = item["chunk"].id
            chunk_map[cid] = item["chunk"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + (rank + 1)))

        # 3. Sort by aggregated RRF score
        sorted_cids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        fused = []
        for cid, score in sorted_cids:
            fused.append({
                "chunk": chunk_map[cid],
                "score": score,
                "rrf_score": score,
            })
        return fused

    def rerank_flashrank(
        self, query: str, candidate_chunks: List[Dict[str, Any]], top_n: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Re-score top candidates using FlashRank cross-encoder.
        Falls back to raw RRF order if FlashRank is unavailable.
        """
        if not self._ranker or not candidate_chunks:
            return candidate_chunks[:top_n]

        try:
            passages = [
                {
                    "id": i,
                    "text": item["chunk"].content,
                    "meta": {"chunk_id": item["chunk"].id, "item": item},
                }
                for i, item in enumerate(candidate_chunks)
            ]

            rerank_request = RerankRequest(query=query, passages=passages)
            results = self._ranker.rerank(rerank_request)

            reranked = []
            for r in results[:top_n]:
                original_item = r["meta"]["item"]
                original_item["cross_score"] = float(r["score"])
                reranked.append(original_item)

            logger.info("flashrank_rerank_completed", candidates_evaluated=len(candidate_chunks), selected=len(reranked))
            return reranked
        except Exception as e:
            logger.warning("flashrank_rerank_fallback", error=str(e))
            return candidate_chunks[:top_n]

    def hybrid_search(
        self, query: str, query_embedding: List[float], top_k: int = 10, top_n: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Complete 3-stage hybrid search pipeline:
        Stage 1: Retrieve Dense candidates (cosine) + Sparse candidates (BM25)
        Stage 2: Fuse via Reciprocal Rank Fusion (RRF, k=60)
        Stage 3: Cross-encoder semantic re-ranking with FlashRank
        """
        dense_candidates = self.search_dense(query_embedding, top_k=top_k * 2)
        sparse_candidates = self.search_bm25(query, top_k=top_k * 2)

        fused_candidates = self.fuse_rrf(dense_candidates, sparse_candidates, top_k=top_k)
        final_results = self.rerank_flashrank(query, fused_candidates, top_n=top_n)

        return final_results


# Global singleton vector store
hybrid_vector_store = HybridVectorStore()
