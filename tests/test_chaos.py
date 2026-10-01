"""
Unit and integration tests for SRE Chaos Engineering management,
fault injection middleware, session tracking, audit logs, and metrics.
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from chaos import ChaosManager, chaos_manager


@pytest.fixture(autouse=True)
def reset_chaos_state():
    """Ensure fresh chaos manager state before and after each test."""
    chaos_manager.disable_500(source="test_teardown")
    chaos_manager.clear_history()
    yield
    chaos_manager.disable_500(source="test_teardown")
    chaos_manager.clear_history()


def test_chaos_manager_lifecycle():
    mgr = ChaosManager()
    assert mgr.simulate_500 is False
    assert mgr.get_status()["active"] is False

    # 1. Enable
    status = mgr.enable_500(source="pytest_suite")
    assert status["active"] is True
    assert status["simulate_500"] is True
    assert status["session"]["session_id"] == 1
    assert status["session"]["fault_type"] == "HTTP_500"

    # 2. Record injections
    mgr.record_injection(endpoint="/api/v1/query", client_ip="192.168.1.10")
    mgr.record_injection(endpoint="/api/v1/query", client_ip="192.168.1.11")
    mgr.record_injection(endpoint="/api/v1/other", client_ip="192.168.1.10")

    status = mgr.get_status()
    assert status["total_injections_all_time"] == 3
    assert status["session"]["injected_count"] == 3
    assert status["session"]["affected_endpoints"] == {
        "/api/v1/query": 2,
        "/api/v1/other": 1,
    }

    # 3. Disable
    status = mgr.disable_500(source="pytest_suite")
    assert status["active"] is False
    assert status["simulate_500"] is False
    assert status["session"] is None

    # 4. History and Events
    history = mgr.get_history()
    assert len(history) == 1
    session = history[0]
    assert session["session_id"] == 1
    assert session["injected_count"] == 3
    assert session["active"] is False
    assert session["duration_seconds"] >= 0.0

    events = mgr.get_events()
    assert len(events) >= 5  # ACTIVATED, 3x FAULT_INJECTED, DEACTIVATED
    event_types = [e["event_type"] for e in events]
    assert "ACTIVATED" in event_types
    assert "FAULT_INJECTED" in event_types
    assert "DEACTIVATED" in event_types

    # 5. Clear history
    clear_res = mgr.clear_history()
    assert clear_res["status"] == "cleared"
    assert len(mgr.get_history()) == 0
    assert len(mgr.get_events()) == 0


def test_chaos_middleware_isolation_and_audit():
    with TestClient(app) as client:
        # Initial status
        res = client.get("/api/v1/chaos/status")
        assert res.status_code == 200
        assert res.json()["simulate_500"] is False

        # Activate Chaos Monkey
        res = client.post("/api/v1/chaos/500?enable=true")
        assert res.status_code == 200
        assert res.json()["simulate_500"] is True

        # Workload endpoint MUST fail with HTTP 500
        res = client.post("/api/v1/query", json={"question": "Como resolver OOMKill?"})
        assert res.status_code == 500
        data = res.json()
        assert "Chaos Monkey injected 500" in data["error"]
        assert data["fault"] == "HTTP_500"
        assert data["endpoint"] == "/api/v1/query"

        # Control Plane & UI endpoints MUST remain alive (Exempt from chaos)
        res_dash = client.get("/dashboard")
        assert res_dash.status_code == 200

        res_board = client.get("/board")
        assert res_board.status_code == 200

        res_health = client.get("/healthz")
        assert res_health.status_code == 200

        res_chaos_status = client.get("/api/v1/chaos/status")
        assert res_chaos_status.status_code == 200

        # Check Audit Events
        res_events = client.get("/api/v1/chaos/events")
        assert res_events.status_code == 200
        events = res_events.json()
        assert any(e["event_type"] == "FAULT_INJECTED" and e["endpoint"] == "/api/v1/query" for e in events)

        # Deactivate Chaos Monkey
        res = client.post("/api/v1/chaos/500?enable=false")
        assert res.status_code == 200
        assert res.json()["simulate_500"] is False

        # Check Sessions History
        res_hist = client.get("/api/v1/chaos/history")
        assert res_hist.status_code == 200
        history = res_hist.json()
        assert len(history) == 1
        assert history[0]["injected_count"] >= 1
        assert "/api/v1/query" in history[0]["affected_endpoints"]
