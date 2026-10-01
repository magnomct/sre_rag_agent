# Runbook: Pod OOMKilled (Out of Memory)

## Alert

`KubePodOOMKilled` / `APIContainerOOMKilledCritical`

## Severity

- **Critical (SEV-1)**: Contêineres da API terminados repetidamente pelo OOM Killer do kernel do Linux (código de saída 137).

## Impact

Derrubada súbita de requisições ativas dos usuários, picos de erros HTTP 502/503 e instabilidade severa de disponibilidade.

## Diagnóstico

### 1. Verificar eventos de OOM nos pods
```bash
kubectl describe pod -n sre-rag -l app.kubernetes.io/name=sre-rag-api | grep -E "Reason:.*OOMKilled|Exit Code:.*137"
```

### 2. Inspecionar eventos do Kubernetes no namespace
```bash
kubectl get events -n sre-rag --sort-by='.lastTimestamp' | grep -i oom
```

### 3. Consultar métricas de consumo de memória no Prometheus
```promql
# Percentual de memória consumido em relação ao limit
container_memory_working_set_bytes{namespace="sre-rag",container="api"} / container_spec_memory_limit_bytes{namespace="sre-rag",container="api"} * 100
```

## Mitigação

### 1. Aumento emergencial dos Limits de Memória
Ajuste imediatamente os limites de recurso do Deployment da API no Helm:
```bash
helm upgrade --install sre-rag ./helm/sre-rag/ \
  --namespace sre-rag \
  --set api.resources.limits.memory=1024Mi \
  --set api.resources.requests.memory=512Mi \
  --reuse-values
```
Aguarde a substituição dos pods:
```bash
kubectl rollout status deployment/sre-rag-api -n sre-rag
```

### 2. Se causado por novo código com vazamento de memória (Memory Leak)
Se o OOM iniciou imediatamente após um deploy recente:
```bash
helm rollback sre-rag -n sre-rag
```

> ⚠️ **Anti-Pattern**: Escalar réplicas horizontais (HPA) não resolve OOM se cada réplica consome mais memória do que o limite permitido ou se há vazamento progressivo de memória por request.

## Resolução

1. Confirme que os novos pods estabilizaram sem reinícios:
```bash
kubectl get pods -n sre-rag -l app.kubernetes.io/name=sre-rag-api
```
2. Monitore o consumo de memória sob carga para assegurar que está contido abaixo de 75% do limit.

## Pós-Incidente

- [ ] Executar profilaxia de memória (memory profiler com `tracemalloc` ou `py-spy`) no código da API.
- [ ] Adequar os testes de carga no CI (`load-test.sh`) com monitoramento contínuo de curva de memória para barrar regressões.
