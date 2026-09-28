# SRE Production Lab — Best Practices

## 📋 Sumário

1. [Filosofia SRE](#filosofia-sre)
2. [SLI / SLO / Error Budget](#sli--slo--error-budget)
3. [Kubernetes Best Practices](#kubernetes-best-practices)
4. [Observabilidade (Prometheus + Grafana + Alertmanager)](#observabilidade)
5. [CI/CD com GitHub Actions](#cicd-com-github-actions)
6. [Docker Best Practices](#docker-best-practices)
7. [Helm Best Practices](#helm-best-practices)
8. [Terraform Best Practices](#terraform-best-practices)
9. [Incident Response](#incident-response)
10. [Segurança](#segurança)

---

## Filosofia SRE

### Princípios Fundamentais

- **Embracing Risk**: Defina quanto risco é aceitável (Error Budget). 100% de uptime não é o objetivo.
- **Toil Reduction**: Automatize trabalho repetitivo. Se faz manualmente mais de 2x, automatize.
- **Monitoring Distributed Systems**: USE (Utilization, Saturation, Errors) e RED (Rate, Errors, Duration).
- **Release Engineering**: Deploys devem ser frequentes, confiáveis e reversíveis.
- **Simplicity**: Prefira soluções simples. Complexidade é o inimigo da confiabilidade.

### Golden Signals (Os 4 Sinais Dourados)

| Sinal      | Descrição                                      | Exemplo de Métrica                |
|------------|------------------------------------------------|-----------------------------------|
| Latency    | Tempo para atender um request                  | `http_request_duration_seconds`   |
| Traffic    | Volume de requests no sistema                  | `http_requests_total`             |
| Errors     | Taxa de requests que falham                    | `http_requests_total{status=~"5.."}` |
| Saturation | Quão "cheio" o serviço está                    | CPU/Memory utilization            |

---

## SLI / SLO / Error Budget

### Definições

- **SLI (Service Level Indicator)**: Métrica quantitativa que mede a saúde do serviço.
  - Ex: "Proporção de requests HTTP com status < 500 e latência < 300ms"
- **SLO (Service Level Objective)**: Meta interna para o SLI.
  - Ex: "99.9% dos requests devem ter latência < 300ms em 30 dias"
- **SLA (Service Level Agreement)**: Contrato com o cliente (sempre mais relaxado que o SLO).
- **Error Budget**: `100% - SLO` = budget para inovar/falhar.

### SLOs deste Lab

| Serviço    | SLI                                    | SLO    | Window  |
|------------|----------------------------------------|--------|---------|
| API (RAG)  | Requests com status < 500              | 99.9%  | 30 dias |
| API (RAG)  | Latência p99 < 500ms                   | 99.5%  | 30 dias |
| PostgreSQL | Conexões ativas < 80% do max          | 99.9%  | 30 dias |
| Redis      | Hit rate > 80%                         | 99.0%  | 30 dias |

### Cálculo de Error Budget

```
SLO = 99.9%
Error Budget = 0.1%
Em 30 dias (43200 min):
  Budget = 43200 * 0.001 = 43.2 minutos de downtime permitido
```

### Políticas de Error Budget

- **Budget > 50%**: Deploy normal, feature flags liberadas
- **Budget 20-50%**: Deploys com cautela, rollback automático obrigatório
- **Budget < 20%**: Freeze de deploys, foco em reliability
- **Budget = 0%**: Apenas hotfixes de reliability

---

## Kubernetes Best Practices

### Resource Management

```yaml
# SEMPRE defina requests e limits
resources:
  requests:
    cpu: "100m"      # Garantido pelo scheduler
    memory: "128Mi"  # Garantido pelo scheduler
  limits:
    cpu: "500m"      # Máximo permitido (throttling)
    memory: "256Mi"  # Máximo permitido (OOMKill)
```

**Regra de ouro**: `limits.memory = 2x requests.memory`, `limits.cpu = 5x requests.cpu`

### Health Checks

```yaml
# Liveness: reinicia o container se falhar
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 10
  failureThreshold: 3

# Readiness: remove do Service se falhar
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 3

# Startup: para apps que demoram a iniciar
startupProbe:
  httpGet:
    path: /healthz
    port: 8080
  failureThreshold: 30
  periodSeconds: 10
```

### Pod Disruption Budgets

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: api-pdb
spec:
  minAvailable: 1  # Pelo menos 1 pod sempre disponível
  selector:
    matchLabels:
      app: sre-rag-api
```

### Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sre-rag-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Segurança de Pods

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
```

### Namespaces e Labels

```yaml
# Labels padronizadas
metadata:
  labels:
    app.kubernetes.io/name: sre-rag-api
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/component: backend
    app.kubernetes.io/part-of: sre-rag-lab
    app.kubernetes.io/managed-by: helm
    environment: production
    team: sre
```

---

## Observabilidade

### Três Pilares

1. **Metrics** (Prometheus): Dados numéricos agregados ao longo do tempo
2. **Logs** (stdout → agregador): Eventos discretos com contexto
3. **Traces** (OpenTelemetry): Caminho de um request através do sistema

### Prometheus — Regras de Ouro

- **Naming**: `<namespace>_<subsystem>_<name>_<unit>` (ex: `http_request_duration_seconds`)
- **Tipos de Métricas**:
  - `Counter`: Só cresce (requests totais, erros)
  - `Gauge`: Sobe e desce (temperatura, conexões ativas)
  - `Histogram`: Distribuição (latência com buckets)
  - `Summary`: Similar ao histogram, calcula quantis no client
- **Cardinalidade**: CUIDADO com labels de alta cardinalidade (user_id, request_id)

### PromQL Essencial para SRE

```promql
# Taxa de erros (Error Rate)
sum(rate(http_requests_total{status=~"5.."}[5m]))
/
sum(rate(http_requests_total[5m]))

# Latência p99
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Disponibilidade (Availability)
1 - (
  sum(rate(http_requests_total{status=~"5.."}[30d]))
  /
  sum(rate(http_requests_total[30d]))
)

# Error Budget Burn Rate
# Se burn_rate > 1, estamos queimando budget mais rápido que o esperado
(
  sum(rate(http_requests_total{status=~"5.."}[1h]))
  /
  sum(rate(http_requests_total[1h]))
) / (1 - 0.999)  # 0.999 = SLO
```

### Alertmanager — Severity Levels

| Severity | Ação                              | Tempo de Resposta | Notificação       |
|----------|-----------------------------------|-------------------|--------------------|
| critical | Acorda alguém, impacto no cliente | < 5 min           | PagerDuty/Telefone |
| warning  | Atenção em horário comercial      | < 30 min          | Slack              |
| info     | Investigar quando possível        | Próximo dia útil  | Email/Ticket       |

### Regras de Alerta — Best Practices

- **Alerte em sintomas, não em causas**: Alerte "latência alta", não "CPU alta"
- **Alerta acionável**: Todo alerta deve ter um runbook associado
- **Evite alert fatigue**: Menos alertas = mais atenção a cada um
- **Multi-window burn rate**: Use janelas de 1h e 6h para reduzir falsos positivos

---

## CI/CD com GitHub Actions

### Pipeline Stages

```
lint → test → security-scan → build → push → deploy-staging → smoke-test → deploy-prod
```

### Best Practices

- **Immutable tags**: Use SHA do commit, nunca `:latest` em produção
- **Rollback automático**: Se health check falhar pós-deploy, rollback automático
- **Canary/Blue-Green**: Deploys graduais para reduzir blast radius
- **Secrets**: Use GitHub Secrets + External Secret Operator (nunca hardcode)
- **Cache**: Cache de Docker layers e dependências para builds mais rápidos

### GitOps Flow

```
Developer → PR → Review → Merge → CI Build → Push Image → 
Update Helm Values → ArgoCD/Flux Sync → Kubernetes Apply
```

---

## Docker Best Practices

### Multi-stage Build

```dockerfile
# Stage 1: Build
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
USER 1000:1000
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8080/healthz || exit 1
CMD ["python", "main.py"]
```

### Regras

- **Imagens mínimas**: Use `slim` ou `distroless`
- **Non-root user**: NUNCA rode como root
- **Layer caching**: Copie `requirements.txt` antes do código
- **.dockerignore**: Exclua `.git`, `__pycache__`, `*.md`, `tests/`
- **Pin versions**: `python:3.12.4-slim`, não `python:3.12-slim`
- **Scan vulnerabilidades**: `trivy image <image>` no CI

---

## Helm Best Practices

### Estrutura de Chart

```
helm/sre-rag-api/
├── Chart.yaml          # Metadata do chart
├── values.yaml         # Valores default (staging)
├── values-prod.yaml    # Override para produção
├── templates/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── hpa.yaml
│   ├── pdb.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── serviceaccount.yaml
│   ├── servicemonitor.yaml  # Para Prometheus Operator
│   └── _helpers.tpl
└── tests/
    └── test-connection.yaml
```

### Regras

- **Sem secrets no values.yaml**: Use External Secrets ou Sealed Secrets
- **Variáveis de ambiente via ConfigMap**: Separação de config e código
- **Chart versionado**: Bumpe a versão do chart a cada mudança
- **Lint e template antes de aplicar**: `helm lint` + `helm template`

---

## Terraform Best Practices

### Estrutura

```
terraform/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── terraform.tfvars
│   └── prod/
│       ├── main.tf
│       ├── variables.tf
│       └── terraform.tfvars
├── modules/
│   ├── k8s-cluster/
│   ├── networking/
│   └── monitoring/
└── backend.tf        # Remote state (S3 + DynamoDB lock)
```

### Regras

- **Remote state**: NUNCA use state local em produção
- **State locking**: Use DynamoDB ou equivalente
- **Modules reutilizáveis**: DRY entre environments
- **Plan before apply**: Sempre `terraform plan` antes de `apply`
- **Drift detection**: CI job periódico para detectar mudanças manuais

---

## Incident Response

### Severidades

| SEV   | Impacto                              | Tempo de Resposta |
|-------|--------------------------------------|-------------------|
| SEV-1 | Serviço completamente down           | Imediato          |
| SEV-2 | Degradação significativa             | < 15 min          |
| SEV-3 | Impacto menor, workaround existe     | < 1 hora          |
| SEV-4 | Cosmético, sem impacto funcional     | Próximo sprint    |

### Fluxo de Incidente

```
Alerta Dispara → Acknowledge → Triage (Severity) → Mitigate → 
Communicate → Resolve → Postmortem (blameless)
```

### Postmortem Template

1. **Resumo**: O que aconteceu?
2. **Timeline**: Cronologia detalhada
3. **Impacto**: Quantos usuários/requests afetados
4. **Root Cause**: Por que aconteceu? (5 Whys)
5. **Action Items**: O que fazer para evitar recorrência
6. **Lições aprendidas**: O que funcionou bem, o que melhorar

---

## Segurança

### Defense in Depth

- **Network Policies**: Restringir comunicação entre pods
- **RBAC**: Princípio do menor privilégio
- **Pod Security Standards**: Restricted profile
- **Image Scanning**: Trivy/Snyk no CI pipeline
- **Secrets Management**: External Secrets Operator + HashiCorp Vault
- **mTLS**: Service mesh (Istio/Linkerd) para comunicação interna
- **Audit Logging**: Kubernetes audit logs habilitados

### Network Policy Exemplo

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-netpol
spec:
  podSelector:
    matchLabels:
      app: sre-rag-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: ingress-nginx
    ports:
    - port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgresql
    ports:
    - port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - port: 6379
```

---

## Checklist de Production Readiness

- [ ] Health checks (liveness, readiness, startup)
- [ ] Resource requests e limits definidos
- [ ] HPA configurado
- [ ] PDB configurado
- [ ] Métricas expostas (/metrics)
- [ ] Dashboards no Grafana
- [ ] Alertas configurados com runbooks
- [ ] SLOs definidos e monitorados
- [ ] CI/CD pipeline completo
- [ ] Rollback automático
- [ ] Network policies
- [ ] Secrets gerenciados externamente
- [ ] Logs estruturados (JSON)
- [ ] Graceful shutdown implementado
- [ ] Documentação atualizada
- [ ] Postmortem template disponível
