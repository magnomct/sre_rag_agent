"""
SRE RAG Agent — End-to-End (E2E) & Integration Tests for v4.0
Validates Autonomous SRE OODA Agent, Real Chaos lifecycle, SLO Error Budget, and Hybrid Search.
"""

import pytest
from starlette.testclient import TestClient
from main import app
from rag.vector_store import hybrid_vector_store
from rag.embeddings import generate_query_embedding


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_agent_ooda_investigation_flow(client):
    """Verify autonomous SRE Agent executes the complete OODA loop with all 4 phases."""
    response = client.post(
        "/api/v1/agent/diagnose",
        json={
            "query": "Kubernetes worker pod crashed with CrashLoopBackOff and high P99 latency",
            "auto_mitigate": False,
        },
    )
    assert response.status_code == 200
    report = response.json()

    assert "incident" in report
    assert "root_cause" in report
    assert "remediation" in report
    assert report["status"] == "recommendation_ready"
    assert report["duration_seconds"] > 0

    # Validate all 4 OODA phases are present in the timeline
    steps = [item["step"] for item in report.get("timeline", [])]
    assert "OBSERVE" in steps
    assert "ORIENT" in steps
    assert "DECIDE" in steps
    assert "ACT" in steps


def test_real_chaos_orchestrator_lifecycle(client):
    """Verify real chaos lifecycle: inject cgroup OOM -> verify active -> emergency revert."""
    # 1. Inject cgroup OOM
    inject_res = client.post("/api/v1/chaos/real/cgroup-oom?target=api&limit_mb=128")
    assert inject_res.status_code == 200
    exp = inject_res.json()
    assert exp.get("type") == "CGROUP_MEMORY_PRESSURE"
    assert exp.get("status") == "active"

    # 2. Check active list
    list_res = client.get("/api/v1/chaos/real/active")
    assert list_res.status_code == 200
    active = list_res.json().get("active_experiments", [])
    assert len(active) >= 1

    # 3. Revert all
    revert_res = client.post("/api/v1/chaos/real/revert")
    assert revert_res.status_code == 200

    # 4. Confirm clean state
    list_res_after = client.get("/api/v1/chaos/real/active")
    assert list_res_after.status_code == 200
    assert len(list_res_after.json().get("active_experiments", [])) == 0


def test_slo_error_budget_metrics(client):
    """Verify dynamic calculation of SLO availability and remaining error budget."""
    response = client.get("/api/v1/slo/error-budget")
    assert response.status_code == 200
    data = response.json()

    assert data.get("slo_target_percentage") == 99.9
    assert "current_availability_percentage" in data
    assert "budget_consumed_percentage" in data
    assert "budget_remaining_percentage" in data
    assert data.get("status") in ["healthy", "warning", "critical"]


def test_hybrid_search_vector_store():
    """Verify 3-stage hybrid search returns relevant documents with RRF fusion."""
    query = "CrashLoopBackOff container killed with exit code 137 OOM"
    query_emb = generate_query_embedding(query)

    results = hybrid_vector_store.hybrid_search(query, query_emb, top_k=5, top_n=3)
    assert len(results) > 0
    top = results[0]
    assert "chunk" in top
    assert top["chunk"].title is not None
    assert top.get("score") is not None
