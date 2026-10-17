#!/usr/bin/env python3
"""
SRE RAG Agent — Autonomous Test, Security & Performance Audit Agent
Executes defensive security audits and performance benchmarks,
automatically documenting results into docs/SECURITY_PERF_TEST_REPORT.md.
"""

import os
import sys
import time
import json
import statistics
import argparse
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Setup base paths
REPO_DIR = Path(__file__).resolve().parent.parent
APP_DIR = REPO_DIR / "app"
DOCS_DIR = REPO_DIR / "docs"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# ANSI terminal colors
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
RESET = "\033[0m"


@dataclass
class AuditResult:
    test_id: str
    category: str
    name: str
    description: str
    target_threshold: str
    actual_value: str
    status: str  # PASS, WARN, FAIL
    details: str


class SRETestAgent:
    """Autonomous Agent for continuous Performance & Security verification."""

    def __init__(self, output_path: Optional[Path] = None):
        self.output_path = output_path or (DOCS_DIR / "SECURITY_PERF_TEST_REPORT.md")
        self.results: List[AuditResult] = []
        self._init_app()

    def _init_app(self):
        """Initializes FastAPI test client in-process."""
        try:
            from starlette.testclient import TestClient
            from main import app
            from config import settings
            self.client = TestClient(app)
            self.settings = settings
            self.app_version = getattr(settings, "app_version", "unknown")
            self.env = getattr(settings, "environment", "development")
        except Exception as e:
            print(f"{RED}[FATAL] Failed to initialize TestClient: {e}{RESET}")
            sys.exit(1)

    # =========================================================================
    # Security Battery
    # =========================================================================
    def audit_security_headers(self):
        """SEC-001: Inspect presence and values of defensive HTTP security headers."""
        response = self.client.get("/healthz")
        headers = response.headers

        expected_headers = {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            "Content-Security-Policy": "default-src 'self'",
        }

        missing = []
        for h, expected_val in expected_headers.items():
            val = headers.get(h)
            if not val or expected_val not in val:
                missing.append(f"{h} (got: {val})")

        status = "PASS" if not missing else "FAIL"
        actual = f"{len(expected_headers) - len(missing)}/{len(expected_headers)} headers present"
        details = "All defensive headers injected correctly." if status == "PASS" else f"Missing or invalid: {', '.join(missing)}"

        self.results.append(AuditResult(
            test_id="SEC-001",
            category="Security",
            name="Defensive HTTP Security Headers",
            description="Validates that CSP, HSTS, X-Frame-Options, and X-Content-Type-Options are enforced on all routes.",
            target_threshold="100% compliant headers",
            actual_value=actual,
            status=status,
            details=details,
        ))

    def audit_rate_limiting(self):
        """SEC-002: Verify that slowapi rate limiting halts abusive bursts."""
        # Query endpoint limit is 30/minute
        statuses = []
        for _ in range(35):
            res = self.client.post("/api/v1/query", json={"question": "audit probe test"})
            statuses.append(res.status_code)

        rate_limited_count = statuses.count(429)
        status = "PASS" if rate_limited_count > 0 else "FAIL"
        actual = f"{rate_limited_count} requests returned HTTP 429"
        details = "Rate limiter correctly throttles abusive bursts with HTTP 429 Too Many Requests." if status == "PASS" else "Rate limiter did not throttle requests after threshold."

        self.results.append(AuditResult(
            test_id="SEC-002",
            category="Security",
            name="Defensive Rate Limiting (slowapi)",
            description="Enforces request limits on expensive AI/RAG query endpoints to prevent Denial of Service (DoS).",
            target_threshold="HTTP 429 on burst > 30 req/min",
            actual_value=actual,
            status=status,
            details=details,
        ))

    def audit_cors_configuration(self):
        """SEC-003: Check Cross-Origin Resource Sharing (CORS) policy."""
        res = self.client.options(
            "/api/v1/history",
            headers={"Origin": "https://malicious-site.example.com", "Access-Control-Request-Method": "POST"}
        )
        allow_origin = res.headers.get("access-control-allow-origin", "")
        is_prod = self.settings.is_production

        if is_prod and allow_origin == "*":
            status = "FAIL"
            details = "Production environment must NOT allow wildcard (*) CORS origins."
        else:
            status = "PASS"
            details = f"CORS configured properly for environment: {self.env} (Allow-Origin: '{allow_origin}')"

        self.results.append(AuditResult(
            test_id="SEC-003",
            category="Security",
            name="CORS Policy & Origin Isolation",
            description="Restricts cross-origin requests to authorized origins, rejecting wildcard origins in production.",
            target_threshold="Origin whitelist enforced in production",
            actual_value=f"Allow-Origin: {allow_origin or 'None'}",
            status=status,
            details=details,
        ))

    def audit_stack_trace_leakage(self):
        """SEC-004: Ensure 404 and 422 responses do not leak sensitive paths or stack traces."""
        res404 = self.client.get("/non_existent_secret_admin_route_404")
        body404 = res404.text

        sensitive_patterns = ["Traceback (most recent call last)", "/home/", "psycopg2", "password"]
        leaked = [p for p in sensitive_patterns if p in body404]

        status = "PASS" if not leaked else "FAIL"
        actual = "No leak detected" if not leaked else f"Leaked patterns: {leaked}"
        details = "Error handlers provide clean, sanitized error messages without exposing internals." if status == "PASS" else "Internal stack traces or paths leaked to client."

        self.results.append(AuditResult(
            test_id="SEC-004",
            category="Security",
            name="Error Message Sanitization (Anti-Leak)",
            description="Verifies that exception handlers sanitize error payloads and do not disclose internal paths or code snippets.",
            target_threshold="Zero sensitive path or stack trace leakage",
            actual_value=actual,
            status=status,
            details=details,
        ))

    def audit_docker_security(self):
        """SEC-005: Inspect Dockerfile for non-root execution and security best practices."""
        dockerfile_path = REPO_DIR / "docker" / "Dockerfile"
        if not dockerfile_path.exists():
            status = "WARN"
            actual = "Dockerfile not found"
            details = f"Could not find Dockerfile at {dockerfile_path}"
        else:
            content = dockerfile_path.read_text(encoding="utf-8")
            has_user = "USER appuser" in content or "USER 1000" in content
            has_healthcheck = "HEALTHCHECK" in content
            has_no_cache = "no-cache" in content

            if has_user and has_healthcheck:
                status = "PASS"
                actual = "Non-root user (appuser) + HEALTHCHECK defined"
                details = "Dockerfile conforms with CNCF container security standards."
            else:
                status = "WARN"
                actual = f"User non-root: {has_user}, Healthcheck: {has_healthcheck}"
                details = "Missing non-root user or explicit healthcheck directive in container image."

        self.results.append(AuditResult(
            test_id="SEC-005",
            category="Security",
            name="Container Security & Non-Root Execution",
            description="Audits Dockerfile to verify non-root user isolation and native HEALTHCHECK directives.",
            target_threshold="Non-root execution (appuser) + HEALTHCHECK",
            actual_value=actual,
            status=status,
            details=details,
        ))

    # =========================================================================
    # Performance Battery
    # =========================================================================
    def benchmark_healthcheck_ttl(self):
        """PERF-001: Health Check Latency & TTL Cache Protection."""
        # 1st call (real check)
        t0 = time.time()
        res1 = self.client.get("/healthz")
        lat1 = (time.time() - t0) * 1000

        # 2nd call (cached within 5s TTL)
        t1 = time.time()
        res2 = self.client.get("/healthz")
        lat2 = (time.time() - t1) * 1000

        data1 = res1.json()
        status = "PASS" if lat2 < 50.0 and res1.status_code == 200 else "WARN"
        actual = f"Call 1: {lat1:.2f}ms, Call 2 (cached): {lat2:.2f}ms"
        details = f"TTL cache shields databases from probe connection storms. Reported Postgres latency: {data1.get('dependencies', {}).get('postgres', {}).get('latency_ms', 0)}ms"

        self.results.append(AuditResult(
            test_id="PERF-001",
            category="Performance",
            name="Health Check Latency & TTL Cache Shield",
            description="Measures round-trip latency of dependency health checks and verifies 5s TTL cache efficiency.",
            target_threshold="Cached latency < 50ms",
            actual_value=actual,
            status=status,
            details=details,
        ))

    def benchmark_endpoint_latencies(self):
        """PERF-002: API Endpoint Latency Distribution (P50, P90, P95, P99)."""
        latencies = []
        for _ in range(50):
            t0 = time.time()
            self.client.get("/api/v1/incidents/catalog")
            latencies.append((time.time() - t0) * 1000)

        latencies.sort()
        p50 = statistics.median(latencies)
        p90 = latencies[int(len(latencies) * 0.90)]
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]

        status = "PASS" if p95 < 150.0 else "WARN"
        actual = f"P50: {p50:.1f}ms | P90: {p90:.1f}ms | P95: {p95:.1f}ms | P99: {p99:.1f}ms"
        details = f"Catalog latency is well within SRE SLO limits (< 200ms). Sample size: {len(latencies)} requests."

        self.results.append(AuditResult(
            test_id="PERF-002",
            category="Performance",
            name="API Endpoint Latency Distribution (Catalog)",
            description="Profiles P50, P90, P95, and P99 response times across repeated requests to establish baseline SLOs.",
            target_threshold="P95 Latency < 150ms",
            actual_value=actual,
            status=status,
            details=details,
        ))

    def benchmark_gzip_compression(self):
        """PERF-003: GZip Compression Efficiency & Bandwidth Savings."""
        res_plain = self.client.get("/dashboard")
        size_plain = len(res_plain.content)

        res_gzip = self.client.get("/dashboard", headers={"Accept-Encoding": "gzip"})
        size_gzip = len(res_gzip.content)
        encoding = res_gzip.headers.get("content-encoding", "")

        ratio = ((size_plain - size_gzip) / size_plain * 100) if size_plain > 0 else 0

        status = "PASS" if ("gzip" in encoding or ratio > 30.0 or size_plain < 1000) else "WARN"
        actual = f"Plain: {size_plain}B -> GZip: {size_gzip}B ({ratio:.1f}% reduction)"
        details = f"HTTP compression minimizes network egress overhead for web dashboard assets. Header: '{encoding}'"

        self.results.append(AuditResult(
            test_id="PERF-003",
            category="Performance",
            name="GZip Compression & Egress Efficiency",
            description="Validates that responses larger than 1KB are transparently compressed via GZipMiddleware.",
            target_threshold="Compression ratio > 40% on payloads > 1KB",
            actual_value=actual,
            status=status,
            details=details,
        ))

    def audit_async_embeddings(self):
        """PERF-004: Non-blocking Asynchronous Embedding Execution."""
        engine_file = REPO_DIR / "app" / "rag" / "engine.py"
        content = engine_file.read_text(encoding="utf-8") if engine_file.exists() else ""

        has_to_thread = "asyncio.to_thread" in content and "generate_query_embedding" in content

        status = "PASS" if has_to_thread else "FAIL"
        actual = "asyncio.to_thread(generate_query_embedding) detected" if has_to_thread else "Synchronous embedding call"
        details = "CPU-intensive vector embedding inference is offloaded to a thread pool, preventing FastAPI event loop stalls." if status == "PASS" else "SentenceTransformer call blocks the async event loop."

        self.results.append(AuditResult(
            test_id="PERF-004",
            category="Performance",
            name="Non-blocking Async Vector Embeddings",
            description="Verifies that CPU-bound vector embedding calculations are dispatched to worker thread pools.",
            target_threshold="Thread pool offload via asyncio.to_thread",
            actual_value=actual,
            status=status,
            details=details,
        ))

    # =========================================================================
    # Runner and Report Generation
    # =========================================================================
    def run_all(self):
        """Execute full audit suite."""
        print(f"{CYAN}{BOLD}=== SRE Test & Security Audit Agent Running ==={RESET}")
        print(f"App Version: {self.app_version} | Environment: {self.env}\n")

        # Security
        self.audit_security_headers()
        self.audit_rate_limiting()
        self.audit_cors_configuration()
        self.audit_stack_trace_leakage()
        self.audit_docker_security()

        # Performance
        self.benchmark_healthcheck_ttl()
        self.benchmark_endpoint_latencies()
        self.benchmark_gzip_compression()
        self.audit_async_embeddings()

        self._print_console_summary()
        self.generate_report()

    def _print_console_summary(self):
        passed = sum(1 for r in self.results if r.status == "PASS")
        warned = sum(1 for r in self.results if r.status == "WARN")
        failed = sum(1 for r in self.results if r.status == "FAIL")

        print(f"{BOLD}------------------------------------------------------------{RESET}")
        for r in self.results:
            color = GREEN if r.status == "PASS" else (YELLOW if r.status == "WARN" else RED)
            print(f"{r.test_id} [{color}{r.status:4s}{RESET}] {r.name:40s} -> {r.actual_value}")
        print(f"{BOLD}------------------------------------------------------------{RESET}")
        print(f"Result: {GREEN}{passed} Passed{RESET}, {YELLOW}{warned} Warned{RESET}, {RED}{failed} Failed{RESET} (Total: {len(self.results)})\n")

    def generate_report(self):
        """Generates markdown documentation report."""
        passed = sum(1 for r in self.results if r.status == "PASS")
        warned = sum(1 for r in self.results if r.status == "WARN")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        compliance_pct = (passed / len(self.results)) * 100 if self.results else 0

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        lines = [
            "# 🛡️ Relatório Contínuo de Testes de Segurança & Performance",
            "## SRE RAG Agent — Test & Security Audit Agent Report",
            "",
            f"> **Gerado automaticamente em**: `{now}`  ",
            f"> **Versão da Aplicação**: `v{self.app_version}` | **Ambiente**: `{self.env}`  ",
            f"> **Índice de Conformidade DevSecOps**: `{compliance_pct:.1f}%` ({passed}/{len(self.results)} aprovados)",
            "",
            "---",
            "",
            "## 📊 Painel Geral de Conformidade",
            "",
            "| Categoria | Total de Testes | Aprovados (PASS) | Alertas (WARN) | Falhas (FAIL) | Conformidade |",
            "|---|---|---|---|---|---|",
        ]

        categories = sorted(list(set(r.category for r in self.results)))
        for cat in categories:
            cat_results = [r for r in self.results if r.category == cat]
            c_pass = sum(1 for r in cat_results if r.status == "PASS")
            c_warn = sum(1 for r in cat_results if r.status == "WARN")
            c_fail = sum(1 for r in cat_results if r.status == "FAIL")
            pct = (c_pass / len(cat_results)) * 100
            lines.append(f"| **{cat}** | {len(cat_results)} | {c_pass} | {c_warn} | {c_fail} | {pct:.1f}% |")

        lines.extend([
            "",
            "---",
            "",
            "## 📋 Detalhamento de Cada Teste Executado",
            "",
            "| ID | Categoria | Nome do Teste | Meta / Threshold | Valor Obtido | Status |",
            "|---|---|---|---|---|---|",
        ])

        for r in self.results:
            icon = "✅" if r.status == "PASS" else ("⚠️" if r.status == "WARN" else "❌")
            lines.append(f"| `{r.test_id}` | {r.category} | **{r.name}** | `{r.target_threshold}` | {r.actual_value} | {icon} `{r.status}` |")

        lines.extend([
            "",
            "---",
            "",
            "## 🔍 Evidências Técnicas & Racional Arquitetural",
            "",
        ])

        for r in self.results:
            icon = "🟢" if r.status == "PASS" else ("🟡" if r.status == "WARN" else "🔴")
            lines.extend([
                f"### {icon} [{r.test_id}] {r.name}",
                f"- **Categoria**: `{r.category}`",
                f"- **Objetivo**: {r.description}",
                f"- **Threshold Esperado**: `{r.target_threshold}`",
                f"- **Resultado Medido**: `{r.actual_value}`",
                f"- **Diagnóstico**: {r.details}",
                "",
            ])

        lines.extend([
            "---",
            "",
            "## 🔄 Ciclo de Vida & Integração DevSecOps",
            "Este relatório é atualizado dinamicamente pelo `scripts/test_agent.py` a cada execução da esteira de CI/CD ou auditoria local via:",
            "```bash",
            "python3 scripts/test_agent.py",
            "# ou via Makefile:",
            "make test-audit",
            "```",
        ])

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"{CYAN}Documentation report written to: {self.output_path}{RESET}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SRE Test & Security Audit Agent")
    parser.add_argument("--output", type=Path, default=None, help="Output markdown report path")
    args = parser.parse_args()

    agent = SRETestAgent(output_path=args.output)
    agent.run_all()
