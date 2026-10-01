"""
SRE RAG Agent — Chaos Engineering Management Module
Tracks chaos experiments, records fault injection events, maintains audit history,
and exposes structured logs and metrics for observability.
"""

import time
from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
import structlog
from metrics import CHAOS_INJECTIONS_TOTAL, CHAOS_ACTIVE_GAUGE

logger = structlog.get_logger()


class ChaosEvent(BaseModel):
    id: int
    timestamp: str
    event_type: str  # "ACTIVATED" | "DEACTIVATED" | "FAULT_INJECTED"
    fault_type: str  # "HTTP_500"
    endpoint: Optional[str] = None
    client_ip: Optional[str] = None
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ChaosSession(BaseModel):
    session_id: int
    started_at: str
    ended_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    fault_type: str
    injected_count: int = 0
    affected_endpoints: Dict[str, int] = Field(default_factory=dict)
    active: bool = True


class ChaosManager:
    """
    Manages chaos injection state, audit history, session metrics and structured logging.
    """

    def __init__(self, max_events: int = 200, max_sessions: int = 50):
        self.simulate_500: bool = False
        self.max_events = max_events
        self.max_sessions = max_sessions

        self._session_counter = 1
        self._event_counter = 1

        self.current_session: Optional[ChaosSession] = None
        self._session_start_time: Optional[float] = None

        self.sessions_history: List[ChaosSession] = []
        self.events_log: List[ChaosEvent] = []
        self.total_injections: int = 0

    def enable_500(self, source: str = "operator") -> dict:
        """Enable HTTP 500 error injection."""
        if self.simulate_500 and self.current_session:
            return self.get_status()

        self.simulate_500 = True
        self._session_start_time = time.time()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        session = ChaosSession(
            session_id=self._session_counter,
            started_at=now_str,
            fault_type="HTTP_500",
            active=True,
        )
        self.current_session = session
        self._session_counter += 1

        # Prometheus Metric
        CHAOS_ACTIVE_GAUGE.set(1)

        # Audit Event
        self._record_event(
            event_type="ACTIVATED",
            fault_type="HTTP_500",
            message=f"Chaos Monkey ATIVADO ({source}) — Injeção de HTTP 500 no workload",
            details={"session_id": session.session_id, "source": source},
        )

        logger.warning(
            "chaos_monkey_activated",
            session_id=session.session_id,
            fault_type="HTTP_500",
            source=source,
            timestamp=now_str,
        )

        return self.get_status()

    def disable_500(self, source: str = "operator") -> dict:
        """Disable HTTP 500 error injection and conclude active session."""
        if not self.simulate_500 and not self.current_session:
            return self.get_status()

        self.simulate_500 = False
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        duration = 0.0

        if self._session_start_time:
            duration = round(time.time() - self._session_start_time, 2)
            self._session_start_time = None

        # Prometheus Metric
        CHAOS_ACTIVE_GAUGE.set(0)

        injected_count = 0
        if self.current_session:
            self.current_session.ended_at = now_str
            self.current_session.duration_seconds = duration
            self.current_session.active = False
            injected_count = self.current_session.injected_count

            # Add to history
            self.sessions_history.insert(0, self.current_session)
            if len(self.sessions_history) > self.max_sessions:
                self.sessions_history.pop()

            self.current_session = None

        # Audit Event
        self._record_event(
            event_type="DEACTIVATED",
            fault_type="HTTP_500",
            message=f"Chaos Monkey DESATIVADO ({source}) — Duração: {duration}s, Falhas injetadas: {injected_count}",
            details={
                "duration_seconds": duration,
                "injected_count": injected_count,
                "source": source,
            },
        )

        logger.info(
            "chaos_monkey_deactivated",
            fault_type="HTTP_500",
            duration_seconds=duration,
            injected_count=injected_count,
            source=source,
            timestamp=now_str,
        )

        return self.get_status()

    def record_injection(
        self, endpoint: str, client_ip: str = "unknown", fault_type: str = "HTTP_500"
    ):
        """Record an individual request failure intercepted by the chaos monkey."""
        self.total_injections += 1

        if self.current_session:
            self.current_session.injected_count += 1
            self.current_session.affected_endpoints[endpoint] = (
                self.current_session.affected_endpoints.get(endpoint, 0) + 1
            )

        # Prometheus Metric
        CHAOS_INJECTIONS_TOTAL.labels(fault_type=fault_type, endpoint=endpoint).inc()

        # Audit Event
        self._record_event(
            event_type="FAULT_INJECTED",
            fault_type=fault_type,
            endpoint=endpoint,
            client_ip=client_ip,
            message=f"Falha {fault_type} injetada em {endpoint} (Client: {client_ip})",
        )

        # High-visibility structured SRE log
        logger.error(
            "chaos_fault_injected",
            fault=fault_type,
            endpoint=endpoint,
            client_ip=client_ip,
            total_session_injections=self.current_session.injected_count
            if self.current_session
            else 1,
        )

    def _record_event(
        self,
        event_type: str,
        fault_type: str,
        message: str,
        endpoint: Optional[str] = None,
        client_ip: Optional[str] = None,
        details: Optional[dict] = None,
    ):
        event = ChaosEvent(
            id=self._event_counter,
            timestamp=datetime.now().strftime("%H:%M:%S"),
            event_type=event_type,
            fault_type=fault_type,
            endpoint=endpoint,
            client_ip=client_ip,
            message=message,
            details=details or {},
        )
        self._event_counter += 1
        self.events_log.insert(0, event)
        if len(self.events_log) > self.max_events:
            self.events_log.pop()

    def get_status(self) -> dict:
        """Return current status and session telemetry."""
        elapsed = 0.0
        if self.simulate_500 and self._session_start_time:
            elapsed = round(time.time() - self._session_start_time, 1)

        return {
            "simulate_500": self.simulate_500,
            "active": self.simulate_500,
            "session": self.current_session.model_dump()
            if self.current_session
            else None,
            "active_duration_seconds": elapsed,
            "total_injections_all_time": self.total_injections,
            "recent_events_count": len(self.events_log),
        }

    def get_history(self) -> list[dict]:
        """Return list of past chaos sessions."""
        return [s.model_dump() for s in self.sessions_history]

    def get_events(self, limit: int = 50) -> list[dict]:
        """Return chronological audit log of events."""
        return [e.model_dump() for e in self.events_log[:limit]]

    def clear_history(self) -> dict:
        """Clear session history and events log."""
        self.sessions_history = []
        self.events_log = []
        self.total_injections = 0
        self._session_counter = 1
        self._event_counter = 1
        return {"status": "cleared"}


# Singleton instance
chaos_manager = ChaosManager()
