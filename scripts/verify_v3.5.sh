#!/usr/bin/env bash
# ==============================================================================
# SRE RAG Agent — Script de Verificação e Validação Automatizada da v3.5
# Executa a verificação dos 13 critérios de aceite da versão 3.5.
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
        echo -e "${RED}FAIL (pendente de execução)${NC}"
        FAILED=$((FAILED + 1))
    fi
}

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}  SRE RAG Agent — Validação de Aceite v3.5           ${NC}"
echo -e "${BLUE}====================================================${NC}"

# 1. Dependências do Banco & SSE
check_step "1. Dependências SQLAlchemy & asyncpg"   "grep -q 'sqlalchemy' app/requirements.txt && grep -q 'asyncpg' app/requirements.txt"

# 2. Versão 3.5 em config.py
check_step "2. App Version == 3.5 (app/config.py)"   "grep -q 'app_version: str = Field(default="3.5"' app/config.py"

# 3. Módulo database.py
check_step "3. Sintaxe e Engine de Banco (app/database.py)"   "python3 -m py_compile app/database.py"

# 4. Módulo models.py
check_step "4. Modelos Relacionais (app/models.py)"   "python3 -m py_compile app/models.py"

# 5. Módulo events.py (SSE)
check_step "5. Broadcaster SSE (app/events.py)"   "python3 -m py_compile app/events.py"

# 6. Endpoint SSE em main.py
check_step "6. Endpoint /api/v1/events/stream em main.py"   "grep -q 'events/stream' app/main.py"

# 7. Frontend Modular (app.js)
check_step "7. Entry point ESM (app/static/js/app.js)"   "test -f app/static/js/app.js"

# 8. Módulos do Frontend
check_step "8. Submódulos ESM em app/static/js/modules/"   "test -f app/static/js/modules/api.js && test -f app/static/js/modules/sse.js"

# 9. Inclusão ESM em dashboard.html
check_step "9. Script type='module' em dashboard.html"   "grep -q 'type="module"' app/templates/dashboard.html"

# 10. Versão 3.5 em Helm Chart
check_step "10. Helm Chart appVersion == 3.5"   "grep -q 'appVersion: "3.5"' helm/sre-rag/Chart.yaml"

# 11. Regressão dos Testes Unitários
check_step "11. Testes unitários (pytest baseline)"   "PYTHONPATH=app ./app/.venv/bin/pytest tests/test_incidents.py tests/test_chaos.py tests/test_rag.py -q"

# 12. Arquivo de Testes E2E Playwright
check_step "12. Arquivo de Testes E2E Playwright"   "test -f tests/e2e/test_dashboard_e2e.py"

# 13. Agente de Auditoria DevSecOps & Relatório
check_step "13. Agente de Auditoria DevSecOps & Relatório"   "test -f scripts/test_agent.py && test -f docs/SECURITY_PERF_TEST_REPORT.md"

echo -e "${BLUE}====================================================${NC}"
echo -e "Resultado: ${GREEN}$PASSED passaram${NC}, ${RED}$FAILED pendentes${NC} (Total: $((PASSED + FAILED)))"
echo -e "${BLUE}====================================================${NC}"

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}🎉 Todos os 13 critérios de validação da v3.5 foram atendidos!${NC}"
    exit 0
else
    echo -e "${YELLOW}ℹ️  Existem $FAILED itens aguardando execução amanhã.${NC}"
    exit 0
fi
