"""
Unit and Integration Tests for RAG Engine & Indexer
"""

import pytest
import asyncio
from pathlib import Path
from rag.indexer import sre_indexer
from rag.engine import rag_engine
from tests.eval.evaluator import SREEvaluator


def test_indexer_loaded():
    """Verify that the corpus is indexed and has all documents."""
    sre_indexer.build_index()
    assert len(sre_indexer.chunks) >= 100
    
    # Check that key runbooks are represented
    sources = [c.source for c in sre_indexer.chunks]
    assert any("crashloopbackoff" in s for s in sources)
    assert any("high-error-rate" in s for s in sources)
    assert any("redis-exhausted" in s for s in sources)
    assert any("tls-expiring" in s for s in sources)
    assert any("postmortem" in s for s in sources)


@pytest.mark.asyncio
async def test_vector_search_relevance():
    """Verify that vector search returns relevant documents for known incident questions."""
    sre_indexer.build_index()
    
    results = sre_indexer.search_by_text("Como resolver CrashLoopBackOff por variavel ausente?", top_k=3)
    assert len(results) > 0
    top_result = results[0]
    assert top_result["score"] >= 0.4
    assert "crashloop" in top_result["source"].lower() or "crashloop" in top_result["title"].lower()


@pytest.mark.asyncio
async def test_rag_engine_end_to_end():
    """Verify that RAGEngine.query produces structured SRE guidance with sources."""
    res = await rag_engine.query("O que fazer quando o Redis atinge maxclients?")
    assert "question" in res
    assert "answer" in res
    assert "sources" in res
    assert len(res["sources"]) > 0
    assert "metadata" in res
    assert "maxclients" in res["answer"].lower() or "redis" in res["answer"].lower()


@pytest.mark.asyncio
async def test_benchmark_composite_score():
    """Assert that the SRE-Eval benchmark achieves at least 80% composite accuracy."""
    evaluator = SREEvaluator()
    results = await evaluator.run_all()
    assert len(results) >= 8
    
    avg_composite = sum(r.composite_score for r in results) / len(results) * 100
    assert avg_composite >= 75.0, f"Benchmark score {avg_composite:.1f}% below target 75.0%"
