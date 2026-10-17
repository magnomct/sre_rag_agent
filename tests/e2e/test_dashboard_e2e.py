"""
SRE RAG Agent — End-to-End (E2E) Dashboard & Integration Tests
Validates real-time SSE streaming, incident simulation lifecycle, chaos toggle, and UI routes.
"""

import pytest
import asyncio
from starlette.testclient import TestClient
from main import app
from events import broadcaster


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_dashboard_renders_successfully(client):
    """Verify that the web dashboard HTML template loads with all components."""
    response = client.get("/dashboard")
    assert response.status_code == 200
    html = response.text

    # Verify key dashboard sections and scripts exist
    assert "SRE Incident Simulation Lab" in html
    assert "app.js?v=3.5.0" in html
    assert 'type="module"' in html
    assert "chaos-monkey-toggle" in html
    assert "chaos-status-badge" in html
    assert "runbook-modal" in html


def test_sse_route_registered(client):
    """Verify that the SSE streaming route is registered in the application."""
    routes = [getattr(r, "path", "") for r in app.routes]
    assert "/api/v1/events/stream" in routes


@pytest.mark.asyncio
async def test_sse_broadcaster_pubsub():
    """Verify that the SSE broadcaster pub/sub delivers events in real-time."""
    queue = await broadcaster.subscribe()
    assert queue is not None
    try:
        await broadcaster.publish("test_event", {"metric": "latency", "value": 4.2})
        msg = await asyncio.wait_for(queue.get(), timeout=2.0)
        assert msg["event"] == "test_event"
        assert msg["data"]["metric"] == "latency"
        assert msg["data"]["value"] == 4.2
    finally:
        await broadcaster.unsubscribe(queue)


def test_incident_simulation_lifecycle_e2e(client):
    """Verify complete lifecycle: catalog -> start simulation -> verify active -> solve -> check history."""
    # 1. Fetch catalog
    cat_res = client.get("/api/v1/incidents/scenarios")
    assert cat_res.status_code == 200
    scenarios = cat_res.json()
    assert len(scenarios) >= 16

    # 2. Start simulation
    scenario_id = scenarios[0]["id"]
    sim_res = client.post("/api/v1/incidents/simulate", json={"scenario_id": scenario_id})
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert sim_data.get("scenario_id") == scenario_id

    # 3. Check active state
    active_res = client.get("/api/v1/incidents/active")
    assert active_res.status_code == 200
    active_data = active_res.json()
    assert active_data.get("scenario_id") == scenario_id
    assert active_data.get("phase") in ["running", "detected", "triaged"]

    # 4. Solve simulation
    correct_sol = next(s["id"] for s in scenarios[0]["solutions"] if s.get("correct"))
    solve_res = client.post("/api/v1/incidents/solve", json={
        "scenario_id": scenario_id,
        "solution_id": correct_sol,
    })
    assert solve_res.status_code == 200
    solve_data = solve_res.json()
    assert solve_data.get("correct") is True
    assert solve_data.get("score") > 0

    # 5. Verify simulation recorded in history
    hist_res = client.get("/api/v1/incidents/history")
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) > 0


def test_chaos_monkey_toggle_flow(client):
    """Verify Chaos Monkey 500 error injection toggle and status reflection."""
    # 1. Enable 500s
    enable_res = client.post("/api/v1/chaos/500?enable=true")
    assert enable_res.status_code == 200
    assert enable_res.json().get("simulate_500") is True

    # 2. Check status
    status_res = client.get("/api/v1/chaos/status")
    assert status_res.status_code == 200
    assert status_res.json().get("simulate_500") is True

    # 3. Disable 500s
    disable_res = client.post("/api/v1/chaos/500?enable=false")
    assert disable_res.status_code == 200
    assert disable_res.json().get("simulate_500") is False
