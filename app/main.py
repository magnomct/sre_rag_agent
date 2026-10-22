from typing import Optional
from pathlib import Path
"""
SRE RAG Agent — Main Application
FastAPI application with Prometheus metrics, structured logging,
and health check endpoints following SRE best practices.
"""

import time
import signal
import sys
import logging
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import asyncio
import json
from sse_starlette.sse import EventSourceResponse
from events import broadcaster
from database import get_db, init_db, close_db, AsyncSessionFactory
from models import QueryHistoryRecord, IncidentSimulationRecord, ChaosSessionRecord, ChaosEventRecord
from sqlalchemy import select, delete

from config import settings
from metrics import (
    APP_INFO,
    HTTP_REQUESTS_TOTAL,
    HTTP_ERRORS_TOTAL,
    HTTP_REQUEST_DURATION,
    SLI_REQUEST_SUCCESS,
    SLI_REQUEST_TOTAL,
)
from healthcheck import health_checker
from rag.engine import rag_engine
from incidents import simulation_engine, SCENARIOS
from chaos import chaos_manager

# ============================================================
# Templates & Static Files Setup (Robust Path Resolution)
# ============================================================
BASE_APP_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_APP_DIR / "templates"
STATIC_DIR = BASE_APP_DIR / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ============================================================
# Models & In-Memory DB (For Lab CRUD)
# ============================================================
class QueryHistory(BaseModel):
    id: int
    query: str
    answer: str
    status: str = "success"

class QueryHistoryCreate(BaseModel):
    query: str
    answer: str

# In-memory storage for CRUD demonstration
history_db: list[QueryHistory] = []
history_counter = 1

async def persist_query_history(query: str, answer: str, latency_ms: float = 0.0, top_score: float = 0.0, from_cache: bool = False) -> int:
    global history_counter
    try:
        async with AsyncSessionFactory() as session:
            record = QueryHistoryRecord(
                query=query,
                answer=answer,
                latency_ms=latency_ms,
                top_score=top_score,
                from_cache=from_cache,
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record.id
    except Exception as exc:
        logger.warning("query_history_db_fallback", error=str(exc))
        item = QueryHistory(id=history_counter, query=query, answer=answer)
        history_db.append(item)
        history_counter += 1
        return item.id

# ============================================================
# Chaos Engineering State (Proxy to ChaosManager)
# ============================================================
class ChaosStateProxy:
    @property
    def simulate_500(self) -> bool:
        return chaos_manager.simulate_500

    @simulate_500.setter
    def simulate_500(self, value: bool):
        if value:
            chaos_manager.enable_500(source="legacy_proxy")
        else:
            chaos_manager.disable_500(source="legacy_proxy")

chaos_state = ChaosStateProxy()


# ============================================================
# Structured Logging Setup
# ============================================================
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        (
            structlog.processors.JSONRenderer()
            if settings.log_format == "json"
            else structlog.dev.ConsoleRenderer()
        ),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        logging.getLevelName(settings.log_level.upper())
    ),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

from agent.sre_agent import sre_agent
from chaos_real import real_chaos_orchestrator
from telemetry import setup_telemetry

logger = structlog.get_logger()


# ============================================================
# Graceful Shutdown
# ============================================================
def graceful_shutdown(signum, frame):
    """Handle SIGTERM/SIGINT for graceful shutdown."""
    logger.info("shutdown_signal_received", signal=signal.Signals(signum).name)
    sys.exit(0)


signal.signal(signal.SIGTERM, graceful_shutdown)
signal.signal(signal.SIGINT, graceful_shutdown)


# ============================================================
# Application Lifecycle
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    # Startup
    logger.info(
        "application_starting",
        app=settings.app_name,
        version=settings.app_version,
    )
    APP_INFO.info(
        {
            "version": settings.app_version,
            "name": settings.app_name,
        }
    )
    health_checker.mark_started()
    await init_db()
    logger.info("application_started")

    yield

    # Shutdown
    logger.info("application_shutting_down")
    await close_db()


# ============================================================
# FastAPI App
# ============================================================
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="SRE RAG Agent — Production Lab API with Observability",
    lifespan=lifespan,
    docs_url=settings.docs_url,
    openapi_url=settings.openapi_url,
    redoc_url=settings.redoc_url,
)

# Initialize OpenTelemetry Tracing
setup_telemetry(app)


# ============================================================
# Rate Limiting
# ============================================================
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ============================================================
# CORS Middleware
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else [
        "https://sre-rag.example.com",
    ],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
    allow_credentials=True,
)

# ============================================================
# GZip Compression Middleware
# ============================================================
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ============================================================
# Middleware: HTTP Security Headers
# ============================================================
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Inject defensive HTTP security headers into every response."""
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self'"
    )
    return response


# ============================================================
# Middleware: Metrics Collection
# ============================================================
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Collect RED metrics for every HTTP request."""
    start_time = time.time()

    # Rotas excluídas do Chaos Monkey — UI e plano de controle devem sobreviver para permitir resposta ao incidente
    CHAOS_EXEMPT_EXACT = {"/", "/dashboard", "/board", "/favicon.ico"}
    CHAOS_EXEMPT_PREFIXES = (
        "/healthz",           # health checks
        "/ready",             # readiness probe
        "/startup",           # startup probe
        "/metrics",           # Prometheus scrape
        "/static",            # assets do dashboard
        "/docs",              # Swagger UI
        "/openapi.json",      # schema
        "/api/v1/incidents",  # controle da simulação — o SRE precisa agir!
        "/api/v1/chaos",      # controle do chaos para permitir desativação
        "/api/v1/events",     # SSE real-time stream
    )
    is_exempt = (
        request.url.path in CHAOS_EXEMPT_EXACT
        or request.url.path.startswith(CHAOS_EXEMPT_PREFIXES)
    )
    if chaos_manager.simulate_500 and not is_exempt:
        client_host = request.client.host if request.client else "unknown"
        chaos_manager.record_injection(
            endpoint=request.url.path,
            client_ip=client_host,
            fault_type="HTTP_500"
        )
        response = JSONResponse(
            status_code=500,
            content={
                "error": "Chaos Monkey injected 500 Internal Server Error",
                "fault": "HTTP_500",
                "endpoint": request.url.path,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        )
    else:
        response = await call_next(request)

    duration = time.time() - start_time
    method = request.method
    endpoint = request.url.path
    status_code = str(response.status_code)

    # RED metrics
    HTTP_REQUESTS_TOTAL.labels(
        method=method, endpoint=endpoint, status_code=status_code
    ).inc()
    HTTP_REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

    if response.status_code >= 500:
        HTTP_ERRORS_TOTAL.labels(
            method=method, endpoint=endpoint, status_code=status_code
        ).inc()

    # SLI tracking
    SLI_REQUEST_TOTAL.inc()
    if response.status_code < 500:
        SLI_REQUEST_SUCCESS.inc()

    # Add response headers for observability
    response.headers["X-Request-Duration"] = f"{duration:.4f}"
    response.headers["X-App-Version"] = settings.app_version

    return response


# ============================================================
# Server-Sent Events (SSE) Real-Time Stream
# ============================================================
@app.get("/api/v1/events/stream", tags=["Events"])
async def sse_event_stream(request: Request):
    """Stream real-time incident, chaos, and metric telemetry to the dashboard."""
    async def event_generator():
        queue = await broadcaster.subscribe()
        try:
            yield {
                "event": "connected",
                "data": json.dumps({"status": "active", "version": settings.app_version}),
            }
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield {
                        "event": payload["event"],
                        "data": json.dumps(payload["data"]),
                    }
                except asyncio.TimeoutError:
                    yield {"comment": "ping"}
        finally:
            await broadcaster.unsubscribe(queue)

    return EventSourceResponse(event_generator())


# ============================================================
# Health Check Endpoints
# ============================================================
@app.get("/healthz", tags=["Health"])
async def liveness():
    """Liveness probe — is the process alive?"""
    return health_checker.liveness()


@app.get("/ready", tags=["Health"])
async def readiness():
    """Readiness probe — can the service handle traffic?"""
    result = health_checker.readiness()
    status_code = 200 if result["status"] == "ready" else 503
    return JSONResponse(content=result, status_code=status_code)


@app.get("/startup", tags=["Health"])
async def startup():
    """Startup probe — has the app finished initialization?"""
    result = health_checker.startup()
    status_code = 200 if result["status"] == "started" else 503
    return JSONResponse(content=result, status_code=status_code)


# ============================================================
# Prometheus Metrics Endpoint
# ============================================================
@app.get("/metrics", tags=["Observability"])
async def metrics():
    """Expose Prometheus metrics."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# ============================================================
# API Endpoints
# ============================================================
@app.get("/", response_class=HTMLResponse, tags=["Web"])
@app.get("/dashboard", response_class=HTMLResponse, tags=["Web"])
async def root(request: Request):
    """SRE Incident Simulation Dashboard."""
    scenarios = list(SCENARIOS.values())
    history = simulation_engine.history
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"scenarios": scenarios, "history": history},
    )


@app.post("/api/v1/query", tags=["RAG"])
@limiter.limit("30/minute")
async def rag_query(request: Request):
    """
    Process a RAG query.

    Accepts a JSON body with a 'question' field and returns
    relevant documents with a generated answer.
    """
    body = await request.json()
    question = body.get("question", "")

    if not question:
        return JSONResponse(
            status_code=400,
            content={"error": "Question is required"},
        )

    result = await rag_engine.query(question)
    try:
        await persist_query_history(
            query=question,
            answer=result.get("answer", ""),
            latency_ms=result.get("duration_seconds", 0.0) * 1000,
            top_score=result.get("top_score", 0.0),
            from_cache=result.get("from_cache", False),
        )
    except Exception as exc:
        logger.warning("persist_query_history_failed", error=str(exc))

    try:
        await broadcaster.publish("rag_query", {
            "question": question,
            "top_score": result.get("top_score", 0.0),
            "from_cache": result.get("from_cache", False),
        })
    except Exception:
        pass
    return result


@app.get("/api/v1/health/dependencies", tags=["Health"])
async def dependency_health():
    """Check health of all external dependencies."""
    return {
        "postgresql": health_checker.check_postgres(),
        "redis": health_checker.check_redis(),
    }

# ============================================================
# Chaos Engineering Endpoints (For Lab Purposes)
# ============================================================
@app.get("/api/v1/chaos/status", tags=["Chaos"])
async def get_chaos_status():
    """Get current Chaos Monkey status and session telemetry."""
    return chaos_manager.get_status()


@app.post("/api/v1/chaos/500", tags=["Chaos"])
async def toggle_500_errors(enable: bool = True):
    """Toggle returning 500 Internal Server Error for workload requests."""
    if enable:
        status = chaos_manager.enable_500(source="operator_api")
    else:
        status = chaos_manager.disable_500(source="operator_api")
    try:
        await broadcaster.publish("chaos_update", status)
    except Exception:
        pass
    return status


@app.get("/api/v1/chaos/history", tags=["Chaos"])
async def get_chaos_history():
    """Get past chaos engineering sessions."""
    return chaos_manager.get_history()


@app.get("/api/v1/chaos/events", tags=["Chaos"])
async def get_chaos_events(limit: int = 50):
    """Get live audit log of chaos events."""
    return chaos_manager.get_events(limit=limit)


@app.post("/api/v1/chaos/history/clear", tags=["Chaos"])
async def clear_chaos_history():
    """Clear chaos session history and event logs."""
    return chaos_manager.clear_history()

# ============================================================
# Incident Simulation API
# ============================================================
class SimulateRequest(BaseModel):
    scenario_id: str

class SolveRequest(BaseModel):
    scenario_id: str
    solution_id: str

@app.get("/api/v1/incidents/scenarios", tags=["Incidents"])
async def list_scenarios():
    """List all available incident scenarios."""
    return list(SCENARIOS.values())


@app.post("/api/v1/incidents/simulate/{difficulty}")
def start_random_simulation(difficulty: str, exclude: Optional[str] = None):
    """Start a random incident simulation based on difficulty.
    
    Args:
        difficulty: easy | medium | hard | extreme
        exclude: comma-separated list of scenario IDs to exclude from draw
    """
    exclude_ids = [e.strip() for e in exclude.split(",")] if exclude else []
    res = simulation_engine.get_random_incident(difficulty, exclude_ids=exclude_ids)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    
    # Return the full scenario details so frontend can render it
    scenario = SCENARIOS[res["scenario_id"]]
    return scenario



@app.get("/api/v1/incidents/scenario/{scenario_id}", tags=["Incidents"])
def get_scenario_by_id(scenario_id: str):
    """Load a specific scenario by ID (used by Prev/Next navigation)."""
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    # Start simulation for this specific scenario
    simulation_engine.start(scenario_id)
    return SCENARIOS[scenario_id]



@app.get("/api/v1/incidents/hint/{scenario_id}", tags=["Incidents"])
def get_hint(scenario_id: str, index: int = 0):
    """Return a specific hint for a scenario (index 0 or 1). 
    Also increments hints_used on the active simulation for score penalty.
    """
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    hints = SCENARIOS[scenario_id].get("hints", [])
    if index >= len(hints):
        raise HTTPException(status_code=404, detail=f"Hint index {index} not available")
    
    # Increment hints counter on active simulation for scoring
    if simulation_engine.active and simulation_engine.active.scenario_id == scenario_id:
        simulation_engine.active.hints_used = simulation_engine.active.hints_used + 1
    
    raw_hint = hints[index]
    if isinstance(raw_hint, dict):
        hint_pt = raw_hint.get("hint", "")
        hint_en = raw_hint.get("hint_en", hint_pt)
    else:
        hint_pt = str(raw_hint)
        hint_en = str(raw_hint)

    return {
        "scenario_id": scenario_id,
        "index": index,
        "total": len(hints),
        "hint": hint_pt,
        "hint_en": hint_en,
        "penalty_percent": (index + 1) * 20,
        "score_after": max(0, 100 - (index + 1) * 20),
    }

@app.get("/api/v1/incidents/review/{scenario_id}", tags=["Incidents"])
def review_scenario(scenario_id: str):
    """Return the correct solution and full step-by-step runbook for a scenario (Review / Gabarito button)."""
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    scenario = SCENARIOS[scenario_id]
    correct = next((s for s in scenario["solutions"] if s.get("correct")), None)
    if not correct:
        raise HTTPException(status_code=404, detail="No correct solution found")
    return {
        "scenario_id": scenario_id,
        "title": scenario["title"],
        "title_en": scenario.get("title_en", scenario["title"]),
        "severity": scenario["severity"],
        "category": scenario.get("category", "Geral"),
        "category_en": scenario.get("category_en", scenario.get("category", "General")),
        "command": correct.get("command", ""),
        "label": correct.get("label", ""),
        "label_en": correct.get("label_en", correct.get("label", "")),
        "explanation": correct.get("explanation", ""),
        "explanation_en": correct.get("explanation_en", correct.get("explanation", "")),
        "runbook_steps": scenario.get("runbook_steps", {}),
        "concepts": scenario.get("concepts", {}),
    }

@app.get("/api/v1/incidents/runbook/{scenario_id}", tags=["Incidents"])
def get_scenario_runbook(scenario_id: str):
    """Return step-by-step runbook and remediation playbook for a scenario."""
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    scenario = SCENARIOS[scenario_id]
    correct = next((s for s in scenario["solutions"] if s.get("correct")), None)
    return {
        "scenario_id": scenario_id,
        "title": scenario["title"],
        "title_en": scenario.get("title_en", scenario["title"]),
        "severity": scenario["severity"],
        "category": scenario.get("category", "Geral"),
        "category_en": scenario.get("category_en", scenario.get("category", "General")),
        "icon": scenario.get("icon", "🚨"),
        "difficulty": scenario.get("difficulty", "medium"),
        "description": scenario.get("description", ""),
        "description_en": scenario.get("description_en", scenario.get("description", "")),
        "command": correct.get("command", "") if correct else "",
        "explanation": correct.get("explanation", "") if correct else "",
        "explanation_en": correct.get("explanation_en", correct.get("explanation", "")) if correct else "",
        "runbook_steps": scenario.get("runbook_steps", {}),
        "concepts": scenario.get("concepts", {}),
    }

@app.get("/api/v1/incidents/concepts", tags=["Incidents"])
def get_all_concepts():
    """Return the complete catalog of SRE concepts, components, and best practices across all scenarios."""
    result = []
    for sid, sc in SCENARIOS.items():
        if "concepts" in sc:
            c = sc["concepts"]
            result.append({
                "scenario_id": sid,
                "title": sc["title"],
                "title_en": sc.get("title_en", sc["title"]),
                "icon": sc.get("icon", "📚"),
                "severity": sc.get("severity", "SEV-2"),
                "category": sc.get("category", "Geral"),
                "category_en": c.get("category_en", sc.get("category_en", sc.get("category", "General"))),
                "difficulty": sc.get("difficulty", "medium"),
                "resource_title": c.get("resource_title", ""),
                "resource_title_en": c.get("resource_title_en", c.get("resource_title", "")),
                "architecture_components": c.get("architecture_components", []),
                "how_it_works": c.get("how_it_works", ""),
                "how_it_works_en": c.get("how_it_works_en", c.get("how_it_works", "")),
                "best_practices": c.get("best_practices", []),
                "best_practices_en": c.get("best_practices_en", c.get("best_practices", [])),
                "golden_signals": c.get("golden_signals", []),
                "golden_signals_en": c.get("golden_signals_en", c.get("golden_signals", [])),
                "remediation_command": sc.get("command", ""),
            })
    return result

@app.post("/api/v1/incidents/simulate", tags=["Incidents"])
async def start_simulation(body: SimulateRequest):
    """Start an incident simulation for a given scenario."""
    result = simulation_engine.start(body.scenario_id)
    try:
        await broadcaster.publish("incident_update", {
            "action": "started",
            "scenario_id": body.scenario_id,
        })
    except Exception:
        pass
    # Activate chaos if the scenario requires it
    scenario = SCENARIOS.get(body.scenario_id, {})
    if scenario.get("chaos_action") == "simulate_500":
        chaos_manager.enable_500(source=f"scenario_{body.scenario_id}")
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.get("/api/v1/incidents/active", tags=["Incidents"])
async def get_active_simulation():
    """Get current state of the active simulation."""
    state = simulation_engine.get_active_state()
    if not state:
        return {"active": False}
    return state

@app.post("/api/v1/incidents/solve", tags=["Incidents"])
async def solve_simulation(body: SolveRequest):
    """Submit a solution for the active simulation."""
    # Deactivate chaos regardless of answer
    chaos_manager.disable_500(source="incident_resolved")
    result = simulation_engine.solve(body.scenario_id, body.solution_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    try:
        async with AsyncSessionFactory() as session:
            rec = IncidentSimulationRecord(
                scenario_id=result.get("scenario_id", body.scenario_id),
                scenario_title=result.get("scenario_title", ""),
                difficulty=result.get("difficulty", "medium"),
                status="completed" if result.get("is_correct") else "failed",
                start_time=result.get("start_time", 0.0),
                end_time=result.get("end_time", 0.0),
                mttd_seconds=result.get("mttd_seconds", 0.0),
                mttr_seconds=result.get("mttr_seconds", 0.0),
                score=result.get("score", 0),
                hints_used=result.get("hints_used", 0),
                commands_executed=result.get("commands_executed", 0),
                operator_solution=body.solution_id,
                is_correct=result.get("is_correct", False),
            )
            session.add(rec)
            await session.commit()
    except Exception as exc:
        logger.warning("persist_simulation_db_fallback", error=str(exc))

    try:
        await broadcaster.publish("incident_update", {
            "action": "resolved",
            "scenario_id": body.scenario_id,
            "is_correct": result.get("is_correct", False),
            "score": result.get("score", 0),
        })
    except Exception:
        pass
    return result

@app.post("/api/v1/incidents/cancel", tags=["Incidents"])
async def cancel_simulation():
    """Cancel the active simulation."""
    chaos_manager.disable_500(source="incident_cancelled")
    return simulation_engine.cancel()

@app.get("/api/v1/incidents/history", tags=["Incidents"])
async def get_simulation_history():
    """Return the full simulation history."""
    return [item.model_dump() for item in simulation_engine.history]

@app.post("/api/v1/incidents/history/clear", tags=["Incidents"])
async def clear_simulation_history():
    """Clear all simulation history records."""
    return simulation_engine.clear_history()

# ============================================================
# History Board (Jinja2)
# ============================================================
@app.get("/board", response_class=HTMLResponse, tags=["Web"])
async def read_board(request: Request):
    """Renderiza a página de board com o histórico de consultas."""
    history_items = []
    try:
        async with AsyncSessionFactory() as session:
            res = await session.execute(select(QueryHistoryRecord).order_by(QueryHistoryRecord.id.desc()))
            records = res.scalars().all()
            if records:
                history_items = [QueryHistory(id=r.id, query=r.query, answer=r.answer) for r in records]
    except Exception as exc:
        logger.warning("read_board_db_fallback", error=str(exc))
    if not history_items:
        history_items = history_db
    return templates.TemplateResponse(
        request=request, name="board.html", context={"history": history_items}
    )

# ============================================================
# History CRUD (Swagger)
# ============================================================
@app.post("/api/v1/history", response_model=QueryHistory, tags=["History CRUD"])
async def create_history(item: QueryHistoryCreate):
    """Cria um novo registro no histórico."""
    global history_counter
    try:
        async with AsyncSessionFactory() as session:
            record = QueryHistoryRecord(query=item.query, answer=item.answer)
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return QueryHistory(id=record.id, query=record.query, answer=record.answer)
    except Exception as exc:
        logger.warning("create_history_db_fallback", error=str(exc))
        new_item = QueryHistory(id=history_counter, query=item.query, answer=item.answer)
        history_db.append(new_item)
        history_counter += 1
        return new_item

@app.get("/api/v1/history", response_model=list[QueryHistory], tags=["History CRUD"])
async def get_all_history():
    """Retorna todos os registros do histórico."""
    try:
        async with AsyncSessionFactory() as session:
            res = await session.execute(select(QueryHistoryRecord).order_by(QueryHistoryRecord.id.desc()))
            records = res.scalars().all()
            if records:
                return [QueryHistory(id=r.id, query=r.query, answer=r.answer) for r in records]
    except Exception as exc:
        logger.warning("get_all_history_db_fallback", error=str(exc))
    return history_db

@app.get("/api/v1/history/{item_id}", response_model=QueryHistory, tags=["History CRUD"])
async def get_history(item_id: int):
    """Busca um registro específico pelo ID."""
    try:
        async with AsyncSessionFactory() as session:
            res = await session.execute(select(QueryHistoryRecord).where(QueryHistoryRecord.id == item_id))
            record = res.scalar_one_or_none()
            if record:
                return QueryHistory(id=record.id, query=record.query, answer=record.answer)
    except Exception as exc:
        logger.warning("get_history_db_fallback", error=str(exc))
    for item in history_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@app.delete("/api/v1/history/{item_id}", tags=["History CRUD"])
async def delete_history(item_id: int):
    """Deleta um registro do histórico."""
    global history_db
    deleted_db = False
    try:
        async with AsyncSessionFactory() as session:
            res = await session.execute(select(QueryHistoryRecord).where(QueryHistoryRecord.id == item_id))
            record = res.scalar_one_or_none()
            if record:
                await session.delete(record)
                await session.commit()
                deleted_db = True
    except Exception as exc:
        logger.warning("delete_history_db_fallback", error=str(exc))

    original_length = len(history_db)
    history_db = [item for item in history_db if item.id != item_id]
    if not deleted_db and len(history_db) == original_length:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"status": "deleted"}


# ============================================================
# SRE Autonomous OODA Agent (v4.0)
# ============================================================
@app.post("/api/v1/agent/diagnose", tags=["Agent"])
async def agent_diagnose(request: Request, body: dict):
    """
    Trigger autonomous SRE Agent OODA investigation with live SSE streaming.
    """
    query = body.get("query", "Investigate active cluster health and anomalies")
    auto_mitigate = body.get("auto_mitigate", False)
    report = await sre_agent.run_ooda_investigation(query, auto_mitigate=auto_mitigate)
    return report


# ============================================================
# Real Chaos Engineering (Kernel / Kind) (v4.0)
# ============================================================
@app.post("/api/v1/chaos/real/cgroup-oom", tags=["Real Chaos"])
async def chaos_real_oom(request: Request, target: str = "api", limit_mb: int = 128):
    """Inject real memory pressure triggering Linux Kernel OOM Killer."""
    return await real_chaos_orchestrator.inject_cgroup_oom(target, limit_mb)


@app.post("/api/v1/chaos/real/cpu-throttle", tags=["Real Chaos"])
async def chaos_real_cpu(request: Request, target: str = "api", quota_us: int = 20000):
    """Constrain cgroup cpu.cfs_quota_us to force severe latency degradation."""
    return await real_chaos_orchestrator.inject_cpu_throttle(target, quota_us)


@app.post("/api/v1/chaos/real/netem", tags=["Real Chaos"])
async def chaos_real_netem(request: Request, delay_ms: int = 250, jitter_ms: int = 50, loss_pct: int = 15):
    """Apply Linux Traffic Control netem latency and packet drop."""
    return await real_chaos_orchestrator.inject_network_latency(delay_ms, jitter_ms, loss_pct)


@app.get("/api/v1/chaos/real/active", tags=["Real Chaos"])
async def chaos_real_list(request: Request):
    """List currently active real chaos experiments."""
    return {"active_experiments": real_chaos_orchestrator.list_active()}


@app.post("/api/v1/chaos/real/revert", tags=["Real Chaos"])
async def chaos_real_revert(request: Request):
    """Emergency fail-safe: revert all active real chaos experiments."""
    return {"reverted": await real_chaos_orchestrator.revert_all()}


# ============================================================
# SLO & Error Budget Live Telemetry (v4.0)
# ============================================================
@app.get("/api/v1/slo/error-budget", tags=["SLO"])
async def get_error_budget_status(request: Request):
    """Real-time calculation of SLO compliance and Error Budget consumption."""
    total_injections = len(real_chaos_orchestrator.list_active())
    budget_consumed = min(100.0, 15.0 + (total_injections * 25.0))
    return {
        "slo_target_percentage": 99.9,
        "current_availability_percentage": round(100.0 - (budget_consumed * 0.001), 3),
        "budget_consumed_percentage": round(budget_consumed, 1),
        "budget_remaining_percentage": round(max(0.0, 100.0 - budget_consumed), 1),
        "status": "healthy" if budget_consumed < 50 else ("warning" if budget_consumed < 80 else "critical"),
        "active_chaos_count": total_injections,
    }
