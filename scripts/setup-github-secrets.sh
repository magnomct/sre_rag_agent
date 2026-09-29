#!/usr/bin/env bash
# =============================================================
# setup-github-secrets.sh
# Configura todos os GitHub Secrets necessários para o projeto
# via `gh secret set` interativo (valores nunca ficam em logs).
#
# Uso: bash scripts/setup-github-secrets.sh
# Pré-requisito: gh auth login já executado
# =============================================================

set -euo pipefail

REPO="magnomct/sre_rag_agent"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}=== GitHub Secrets Setup — SRE RAG Agent ===${NC}"
echo -e "${YELLOW}Repositório: ${REPO}${NC}"
echo ""
echo "Cada secret será solicitado interativamente."
echo "Os valores NÃO aparecem na tela nem em logs."
echo "Pressione ENTER para pular um secret (mantém o valor existente)."
echo ""

# ── Helper ────────────────────────────────────────────────────
set_secret() {
    local name="$1"
    local description="$2"
    local env="${3:-}"

    echo -e "${CYAN}▶ ${name}${NC}"
    echo "  Descrição: ${description}"

    if [ -n "$env" ]; then
        echo "  Ambiente:  ${env}"
        gh secret set "$name" --repo "$REPO" --env "$env"
    else
        gh secret set "$name" --repo "$REPO"
    fi
    echo -e "  ${GREEN}✓ Configurado${NC}"
    echo ""
}

# ── Repositório (disponíveis em todos os workflows) ───────────
echo -e "${YELLOW}── Secrets de Repositório ────────────────────────────────${NC}"

set_secret "GHCR_TOKEN" \
    "Personal Access Token (PAT) com escopo 'write:packages' para push de imagens ao GHCR"

set_secret "OCI_TENANCY_OCID" \
    "OCID da Tenancy OCI (OCI Console → Profile → Tenancy)"

set_secret "OCI_USER_OCID" \
    "OCID do usuário OCI (OCI Console → Profile → User Settings)"

set_secret "OCI_FINGERPRINT" \
    "Fingerprint da chave API OCI (formato: xx:xx:xx:...)"

set_secret "OCI_PRIVATE_KEY" \
    "Conteúdo da chave privada OCI em base64: cat ~/.oci/oci_api_key.pem | base64 -w0"

set_secret "OCI_REGION" \
    "Região OCI (ex: sa-saopaulo-1)"

set_secret "OCI_COMPARTMENT_OCID" \
    "OCID do Compartment OCI (OCI Console → Identity → Compartments)"

# ── Ambiente: staging ─────────────────────────────────────────
echo -e "${YELLOW}── Secrets do Ambiente: staging ──────────────────────────${NC}"

set_secret "KUBECONFIG" \
    "kubeconfig do cluster de staging em base64: cat ~/.kube/config | base64 -w0" \
    "staging"

set_secret "POSTGRES_PASSWORD" \
    "Senha do PostgreSQL no ambiente de staging" \
    "staging"

set_secret "REDIS_PASSWORD" \
    "Senha do Redis no ambiente de staging (deixe vazio se sem autenticação)" \
    "staging"

# ── Ambiente: production ──────────────────────────────────────
echo -e "${YELLOW}── Secrets do Ambiente: production ───────────────────────${NC}"

set_secret "KUBECONFIG" \
    "kubeconfig do cluster de produção em base64: cat ~/.kube/config | base64 -w0" \
    "production"

set_secret "POSTGRES_PASSWORD" \
    "Senha forte do PostgreSQL em produção" \
    "production"

set_secret "REDIS_PASSWORD" \
    "Senha do Redis em produção" \
    "production"

set_secret "SLACK_WEBHOOK_URL" \
    "URL do Webhook do Slack para alertas de produção" \
    "production"

set_secret "PAGERDUTY_KEY" \
    "Service Key do PagerDuty para alertas críticos (SEV-1)" \
    "production"

# ── Resumo ────────────────────────────────────────────────────
echo -e "${GREEN}=== Configuração concluída! ===${NC}"
echo ""
echo "Secrets configurados. Verifique em:"
echo "  https://github.com/${REPO}/settings/secrets/actions"
echo ""
echo "Environments configurados:"
echo "  https://github.com/${REPO}/settings/environments"
