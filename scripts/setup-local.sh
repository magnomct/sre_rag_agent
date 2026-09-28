#!/usr/bin/env bash
# =============================================================
# Setup Local Environment — Kind + Monitoring
# =============================================================

set -euo pipefail

CLUSTER_NAME="sre-rag"
NAMESPACE="sre-rag"

echo "============================================================="
echo "  SRE RAG Agent — Local Setup"
echo "============================================================="

# 1. Check prerequisites
echo "[1/6] Checking prerequisites..."
for cmd in docker kind kubectl helm; do
  if ! command -v $cmd &>/dev/null; then
    echo "ERROR: $cmd is not installed. Please install it first."
    exit 1
  fi
done
echo "  ✅ All prerequisites found"

# 2. Create Kind cluster
echo "[2/6] Creating Kind cluster..."
if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
  echo "  ⚠️  Cluster '${CLUSTER_NAME}' already exists, skipping creation"
else
  cat <<EOF | kind create cluster --name ${CLUSTER_NAME} --config -
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
    extraPortMappings:
      - containerPort: 80
        hostPort: 80
        protocol: TCP
      - containerPort: 443
        hostPort: 443
        protocol: TCP
  - role: worker
  - role: worker
EOF
  echo "  ✅ Kind cluster created"
fi

# 3. Build and load Docker image
echo "[3/6] Building Docker image..."
docker build -t sre-rag-api:local ./app/
kind load docker-image sre-rag-api:local --name ${CLUSTER_NAME}
echo "  ✅ Docker image loaded into Kind"

# 4. Install monitoring stack
echo "[4/6] Installing monitoring stack (kube-prometheus-stack)..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null || true
helm repo update
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set grafana.adminPassword=admin \
  --wait \
  --timeout 10m
echo "  ✅ Monitoring stack installed"

# 5. Deploy application
echo "[5/6] Deploying SRE RAG Agent..."
helm upgrade --install sre-rag ./helm/sre-rag/ \
  --namespace ${NAMESPACE} \
  --create-namespace \
  --set api.image.repository=sre-rag-api \
  --set api.image.tag=local \
  --set api.image.pullPolicy=Never \
  --wait \
  --timeout 5m
echo "  ✅ Application deployed"

# 6. Print access info
echo "[6/6] Setup complete!"
echo ""
echo "============================================================="
echo "  📍 Access your services:"
echo "============================================================="
echo ""
echo "  API:          kubectl port-forward -n ${NAMESPACE} svc/sre-rag-api 8080:80"
echo "  Prometheus:   kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090"
echo "  Grafana:      kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80"
echo "  Alertmanager: kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-alertmanager 9093:9093"
echo ""
echo "  Grafana credentials: admin / admin"
echo ""
echo "  Verify pods: kubectl get pods -n ${NAMESPACE}"
echo "============================================================="
