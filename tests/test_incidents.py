"""
Unit Tests for SRE Incident Simulator
"""

import pytest
from pathlib import Path
from incidents import SCENARIOS, simulation_engine

BASE_DIR = Path(__file__).resolve().parent.parent


def test_scenarios_have_existing_runbooks():
    """Verify that every scenario links to a runbook that actually exists on disk."""
    assert len(SCENARIOS) == 8
    
    for sc_id, sc in SCENARIOS.items():
        runbook_path_str = sc.get("runbook", "")
        assert runbook_path_str, f"Scenario {sc_id} is missing runbook link"
        
        # Verify markdown file exists on disk
        fname = runbook_path_str.replace("/docs/runbooks/", "") + ".md"
        full_path = BASE_DIR / "docs" / "runbooks" / fname
        assert full_path.is_file(), f"Runbook file not found on disk: {full_path}"


def test_simulation_lifecycle():
    """Verify start, active state, solve, and history recording."""
    engine = simulation_engine
    engine.cancel()
    engine.clear_history()

    # 1. Start simulation
    res = engine.start("crashloopbackoff")
    assert res.get("status") == "started"
    assert engine.active is not None

    # 2. Check active state
    state = engine.get_active_state()
    assert state is not None
    assert state["scenario_id"] == "crashloopbackoff"

    # 3. Solve with correct solution
    solve_res = engine.solve("crashloopbackoff", "fix-configmap")
    assert solve_res.get("correct") is True
    assert engine.active is None
    assert len(engine.history) == 1
    assert engine.history[0].scenario_id == "crashloopbackoff"
