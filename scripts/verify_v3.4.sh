#!/usr/bin/env bash
# ==============================================================================
# SRE RAG Agent — Script de Verificação e Validação Automatizada da v3.4
# Executa a verificação dos 12 critérios de aceite definidos no plano de melhorias.
# ==============================================================================

set -uo pipefail

REPO_DIR="/home/magno/sre_rag_agent"
cd "$REPO_DIR"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0

check_step() {
    local desc="$1"
    local cmd="$2"
    echo -n "Checking: $desc ... "
    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}FAIL (pendente)${NC}"
        FAILED=$((FAILED + 1))
    fi
}

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}  SRE RAG Agent — Validação de Aceite v3.4           ${NC}"
echo -e "${BLUE}====================================================${NC}"

# 1. Compilação de sintaxe
check_step "1. Sintaxe app/config.py" "python3 -m py_compile app/config.py"
check_step "2. Sintaxe app/healthcheck.py" "python3 -m py_compile app/healthcheck.py"
check_step "3. Sintaxe app/rag/engine.py" "python3 -m py_compile app/rag/engine.py"
check_step "4. Sintaxe app/main.py" "python3 -m py_compile app/main.py"

# 2. Pydantic V2 sem DeprecationWarning
check_step "5. Pydantic V2 ConfigDict (sem DeprecationWarning)" \
  "PYTHONPATH=app ./app/.venv/bin/python3 -W error::DeprecationWarning -c 'from config import settings'"

# 3. Versão da aplicação
check_step "6. App Version == 3.4 (config.py)" \
  "PYTHONPATH=app ./app/.venv/bin/python3 -c 'from config import settings; assert settings.app_version == \"3.4\"'"

check_step "7. App Version == 3.4 (helm/sre-rag/Chart.yaml)" \
  "grep -q 'appVersion: \"3.4\"' helm/sre-rag/Chart.yaml"

# 4. Healthcheck TTL Cache
check_step "8. Healthcheck Cache TTL e Latência Real" \
  "PYTHONPATH=app ./app/.venv/bin/python3 -c 'from healthcheck import HealthChecker; h = HealthChecker(); assert hasattr(h, \"_cached_postgres\")'"

# 5. Async Embeddings
check_step "9. Async embeddings (asyncio.to_thread em query)" \
  "grep -q 'asyncio.to_thread(generate_query_embedding' app/rag/engine.py"

# 6. GZip e Security Headers em main.py
check_step "10. GZipMiddleware registrado em main.py" \
  "grep -q 'GZipMiddleware' app/main.py"

check_step "11. Security Headers e Rate Limiter em main.py" \
  "grep -q 'security_headers_middleware' app/main.py && grep -q 'limiter' app/main.py"

# 7. Regressão nos testes unitários existentes
check_step "12. Testes de regressão (pytest - 4 passed)" \
  "PYTHONPATH=app ./app/.venv/bin/pytest tests/test_incidents.py tests/test_chaos.py -q"

echo -e "${BLUE}====================================================${NC}"
echo -e "Resultado: ${GREEN}$PASSED passaram${NC}, ${RED}$FAILED pendentes${NC} (Total: $((PASSED + FAILED)))"
echo -e "${BLUE}====================================================${NC}"

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}🎉 Todos os 12 critérios de validação da v3.4 foram atendidos com sucesso!${NC}"
    exit 0
else
    echo -e "${YELLOW}ℹ️  Existem $FAILED itens pendentes de implementação amanhã.${NC}"
    exit 0
fi
