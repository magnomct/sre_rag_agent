# =============================================================
# SRE RAG Agent — Makefile
# =============================================================

.PHONY: help build push deploy cluster-create cluster-delete port-forward \
        lint test setup slo-status load-test clean

CLUSTER_NAME  := sre-rag
NAMESPACE     := sre-rag
IMAGE         := sre-rag-api
TAG           := $(shell git rev-parse --short HEAD 2>/dev/null || echo "local")
REGISTRY      := ghcr.io/your-org

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---- Cluster ----
cluster-create: ## Create Kind cluster
	@bash scripts/setup-local.sh

cluster-delete: ## Delete Kind cluster
	kind delete cluster --name $(CLUSTER_NAME)

# ---- Build ----
build: ## Build Docker image
	docker build -t $(IMAGE):$(TAG) -f docker/Dockerfile ./app/
	docker tag $(IMAGE):$(TAG) $(IMAGE):latest

push: ## Push image to registry
	docker tag $(IMAGE):$(TAG) $(REGISTRY)/$(IMAGE):$(TAG)
	docker push $(REGISTRY)/$(IMAGE):$(TAG)

# ---- Deploy ----
deploy: ## Deploy to K8s (local)
	helm upgrade --install sre-rag ./helm/sre-rag/ \
		--namespace $(NAMESPACE) \
		--create-namespace \
		--set api.image.repository=$(IMAGE) \
		--set api.image.tag=$(TAG) \
		--set api.image.pullPolicy=Never \
		--wait

deploy-prod: ## Deploy to K8s (production)
	helm upgrade --install sre-rag ./helm/sre-rag/ \
		--namespace $(NAMESPACE) \
		-f helm/sre-rag/values.yaml \
		-f helm/sre-rag/values-prod.yaml \
		--set api.image.tag=$(TAG) \
		--wait

rollback: ## Rollback last Helm release
	helm rollback sre-rag -n $(NAMESPACE)

# ---- Access ----
port-forward: ## Port-forward all services
	@echo "Starting port-forwarding..."
	@kubectl port-forward -n $(NAMESPACE) svc/sre-rag-api 8080:80 &
	@kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090 &
	@kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80 &
	@kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-alertmanager 9093:9093 &
	@echo ""
	@echo "API:          http://localhost:8080"
	@echo "Prometheus:   http://localhost:9090"
	@echo "Grafana:      http://localhost:3000 (admin/admin)"
	@echo "Alertmanager: http://localhost:9093"

# ---- Quality ----
lint: ## Lint code and Helm chart
	cd app && ruff check . && ruff format --check .
	helm lint helm/sre-rag/

dev: ## Run API locally with uvicorn
	cd app && .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8080 --reload

test: ## Run unit tests
	PYTHONPATH=.:app ./app/.venv/bin/pytest tests/ -v

eval: ## Run SRE-Eval benchmark evaluation
	PYTHONPATH=.:app ./app/.venv/bin/python tests/eval/evaluator.py

helm-template: ## Dry-run Helm template
	helm template sre-rag helm/sre-rag/ --debug

# ---- Setup ----
setup: cluster-create ## Full local setup (alias)

# ---- Docker Compose (Lightweight) ----
compose-up: ## Start lightweight stack via Docker Compose
	docker compose up -d --build

compose-down: ## Stop lightweight stack
	docker compose down

# ---- Observability ----
slo-status: ## Check current SLO status
	@echo "=== Availability SLI (1h) ==="
	@kubectl exec -n monitoring deploy/monitoring-kube-prometheus-prometheus -- \
		promtool query instant http://localhost:9090 'sli:availability:ratio_rate1h' 2>/dev/null || \
		echo "  Run 'make port-forward' first, then: curl 'http://localhost:9090/api/v1/query?query=sli:availability:ratio_rate1h'"
	@echo ""
	@echo "=== Burn Rate (1h) ==="
	@echo "  curl 'http://localhost:9090/api/v1/query?query=slo:availability:burn_rate1h'"

load-test: ## Run load test
	@bash scripts/load-test.sh

# ---- Terraform ----
tf-init: ## Terraform init
	cd terraform && terraform init

tf-plan: ## Terraform plan
	cd terraform && terraform plan

tf-apply: ## Terraform apply
	cd terraform && terraform apply

# ---- Cleanup ----
clean: ## Remove all local resources
	-helm uninstall sre-rag -n $(NAMESPACE) 2>/dev/null
	-helm uninstall monitoring -n monitoring 2>/dev/null
	-kind delete cluster --name $(CLUSTER_NAME) 2>/dev/null
	-docker rmi $(IMAGE):$(TAG) $(IMAGE):latest 2>/dev/null
	@echo "Cleaned up!"
