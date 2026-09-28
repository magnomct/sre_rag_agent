"""
SRE RAG Agent — Main Application
FastAPI application with Prometheus metrics, structured logging,
and health check endpoints following SRE best practices.
"""

import time
import signal
import sys
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
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
        structlog.get_level_from_name(settings.log_level)
    ),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

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
    logger.info("application_started")

    yield

    # Shutdown
    logger.info("application_shutting_down")


# ============================================================
# FastAPI App
# ============================================================
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="SRE RAG Agent — Production Lab API with Observability",
    lifespan=lifespan,
)


# ============================================================
# Middleware: Metrics Collection
# ============================================================
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Collect RED metrics for every HTTP request."""
    start_time = time.time()

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
@app.get("/", tags=["API"])
async def root():
    """Root endpoint — API information."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "metrics": "/metrics",
        "health": "/healthz",
    }


@app.post("/api/v1/query", tags=["RAG"])
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
    return result


@app.get("/api/v1/health/dependencies", tags=["Health"])
async def dependency_health():
    """Check health of all external dependencies."""
    return {
        "postgresql": health_checker.check_postgres(),
        "redis": health_checker.check_redis(),
    }
