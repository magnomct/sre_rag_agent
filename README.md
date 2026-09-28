# SRE RAG Agent — Production Lab

## 🏗️ Arquitetura

```
GitHub
   ↓
GitHub Actions (CI/CD)
   ↓
Docker Build + Push (GHCR)
   ↓
Kubernetes (Kind/Minikube)
   ├── sre-rag-api (Python + RAG)
   ├── PostgreSQL (StatefulSet)
   └── Redis (StatefulSet)
        ↓
Prometheus → Grafana → Alertmanager
```

## 📁 Estrutura do Projeto

```
sre_rag_agent/
├── claude.md                    # Best practices SRE
├── README.md                    # Este arquivo
├── app/                         # Aplicação Python (API RAG)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── config.py
│   ├── metrics.py
│   ├── healthcheck.py
│   └── rag/
│       ├── __init__.py
│       ├── engine.py
│       └── embeddings.py
├── helm/                        # Helm Charts
│   └── sre-rag/
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── values-prod.yaml
│       └── templates/
│           ├── _helpers.tpl
│           ├── namespace.yaml
│           ├── api-deployment.yaml
│           ├── api-service.yaml
│           ├── api-hpa.yaml
│           ├── api-pdb.yaml
│           ├── api-configmap.yaml
│           ├── api-servicemonitor.yaml
│           ├── postgresql-statefulset.yaml
│           ├── postgresql-service.yaml
│           ├── redis-statefulset.yaml
│           ├── redis-service.yaml
│           └── network-policies.yaml
├── terraform/                   # Infraestrutura como Código
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── providers.tf
│   └── modules/
│       ├── k8s-cluster/
│       └── monitoring/
├── monitoring/                  # Observabilidade
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── rules/
│   │       ├── slo-rules.yml
│   │       └── alerts.yml
│   ├── grafana/
│   │   └── dashboards/
│   │       └── sre-overview.json
│   └── alertmanager/
│       └── alertmanager.yml
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
├── scripts/                     # Scripts auxiliares
│   ├── setup-local.sh
│   └── load-test.sh
├── docs/                        # Documentação
│   ├── runbooks/
│   │   ├── high-latency.md
│   │   └── high-error-rate.md
│   └── postmortem-template.md
├── .dockerignore
├── .gitignore
└── Makefile
```

## 🚀 Quick Start

```bash
# 1. Criar cluster local
make cluster-create

# 2. Build e deploy
make build deploy

# 3. Acessar serviços
make port-forward

# 4. Verificar SLOs
make slo-status
```

## 📊 SLOs Definidos

| Serviço | SLI | SLO | Window |
|---------|-----|-----|--------|
| API | Availability (status < 500) | 99.9% | 30d |
| API | Latência p99 < 500ms | 99.5% | 30d |
| PostgreSQL | Conexões < 80% max | 99.9% | 30d |
| Redis | Cache hit rate > 80% | 99.0% | 30d |

## 🔗 Links Úteis

- [Grafana Dashboard](http://localhost:3000)
- [Prometheus](http://localhost:9090)
- [API Docs](http://localhost:8080/docs)

## 📖 Referências

- [Google SRE Book](https://sre.google/sre-book/table-of-contents/)
- [Google SRE Workbook](https://sre.google/workbook/table-of-contents/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
