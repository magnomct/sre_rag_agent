"""
SRE RAG Agent — Prometheus Metrics Module
Defines application-level metrics following RED and USE methodologies.
"""

from prometheus_client import Counter, Histogram, Gauge, Info


# ============================================================
# Application Info
# ============================================================
APP_INFO = Info("sre_rag_api", "SRE RAG API application information")

# ============================================================
# RED Metrics (Rate, Errors, Duration)
# ============================================================

# Rate: Total requests
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
)

# Errors: Total errors
HTTP_ERRORS_TOTAL = Counter(
    "http_errors_total",
    "Total number of HTTP errors (5xx)",
    ["method", "endpoint", "status_code"],
)

# Duration: Request latency
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# ============================================================
# RAG-Specific Metrics
# ============================================================

RAG_QUERIES_TOTAL = Counter(
    "rag_queries_total",
    "Total number of RAG queries",
    ["status"],  # success, error
)

RAG_QUERY_DURATION = Histogram(
    "rag_query_duration_seconds",
    "RAG query processing duration in seconds",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

RAG_DOCUMENTS_RETRIEVED = Histogram(
    "rag_documents_retrieved",
    "Number of documents retrieved per query",
    buckets=[1, 2, 3, 5, 10, 20],
)

RAG_EMBEDDING_DURATION = Histogram(
    "rag_embedding_duration_seconds",
    "Time to compute embeddings",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
)

# ============================================================
# Database Metrics
# ============================================================

DB_CONNECTIONS_ACTIVE = Gauge(
    "db_connections_active",
    "Number of active database connections",
    ["database"],  # postgresql, redis
)

DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["database", "operation"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
)

# ============================================================
# Cache Metrics (Redis)
# ============================================================

CACHE_HITS_TOTAL = Counter(
    "cache_hits_total",
    "Total number of cache hits",
)

CACHE_MISSES_TOTAL = Counter(
    "cache_misses_total",
    "Total number of cache misses",
)

# ============================================================
# SLI Metrics
# ============================================================

SLI_REQUEST_SUCCESS = Counter(
    "sli_request_success_total",
    "Total successful requests (status < 500) — used for availability SLI",
)

SLI_REQUEST_TOTAL = Counter(
    "sli_request_total",
    "Total requests — used for availability SLI",
)
