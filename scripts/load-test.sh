#!/usr/bin/env bash
# =============================================================
# Load Test — Generate traffic for SLO validation
# Uses 'hey' or falls back to curl-based load
# =============================================================

set -euo pipefail

API_URL="${1:-http://localhost:8080}"
DURATION="${2:-60}"
CONCURRENCY="${3:-10}"
RPS="${4:-50}"

echo "============================================================="
echo "  SRE RAG Agent — Load Test"
echo "============================================================="
echo "  URL:         ${API_URL}"
echo "  Duration:    ${DURATION}s"
echo "  Concurrency: ${CONCURRENCY}"
echo "  Target RPS:  ${RPS}"
echo "============================================================="
echo ""

# Check if 'hey' is installed
if command -v hey &>/dev/null; then
  echo "Using 'hey' for load testing..."
  echo ""

  echo "--- Phase 1: Health Check Warm-up (10s) ---"
  hey -z 10s -c 5 -q 10 "${API_URL}/healthz" | tail -20
  echo ""

  echo "--- Phase 2: Normal Traffic (${DURATION}s) ---"
  hey -z "${DURATION}s" -c "${CONCURRENCY}" -q "${RPS}" \
    -m POST \
    -H "Content-Type: application/json" \
    -d '{"question": "What are SLO best practices?"}' \
    "${API_URL}/api/v1/query" | tail -30
  echo ""

  echo "--- Phase 3: Spike Test (10s at 5x load) ---"
  hey -z 10s -c $((CONCURRENCY * 5)) -q $((RPS * 5)) \
    -m POST \
    -H "Content-Type: application/json" \
    -d '{"question": "How to handle incidents?"}' \
    "${API_URL}/api/v1/query" | tail -20

else
  echo "'hey' not installed. Using curl-based load test..."
  echo "Install hey: go install github.com/rakyll/hey@latest"
  echo ""

  for i in $(seq 1 "${DURATION}"); do
    for j in $(seq 1 "${CONCURRENCY}"); do
      curl -s -o /dev/null -w "%{http_code}" \
        -X POST "${API_URL}/api/v1/query" \
        -H "Content-Type: application/json" \
        -d '{"question": "What are SLO best practices?"}' &
    done
    wait
    echo "Second ${i}/${DURATION} — ${CONCURRENCY} requests sent"
  done
fi

echo ""
echo "✅ Load test complete!"
echo ""
echo "Check metrics:"
echo "  Prometheus: http://localhost:9090/graph?g0.expr=rate(http_requests_total[5m])"
echo "  Grafana:    http://localhost:3000/d/sre-rag-overview"
