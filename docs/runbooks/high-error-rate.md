# Runbook: High Error Rate

## Alert

`SLOAvailabilityBurnRateCritical` / `SLOAvailabilityBurnRateWarning`

## Severity

- **Warning**: Burn rate > 6x (1h) AND > 3x (6h)
- **Critical**: Burn rate > 14.4x (1h) AND > 6x (6h)

## Impact

Error budget sendo consumido rapidamente. Usuários recebendo erros 5xx.

## Diagnóstico

### 1. Identificar a taxa de erros

```promql
# Error rate geral
sum(rate(http_requests_total{status_code=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100

# Error rate por endpoint
sum(rate(http_requests_total{status_code=~"5.."}[5m])) by (endpoint) / sum(rate(http_requests_total[5m])) by (endpoint) * 100

# Burn rate atual
slo:availability:burn_rate1h
```

### 2. Verificar status dos pods

```bash
# Pods em erro
kubectl get pods -n sre-rag -o wide

# Eventos recentes
kubectl get events -n sre-rag --sort-by='.lastTimestamp' | tail -20

# Logs de erro
kubectl logs -n sre-rag -l app.kubernetes.io/name=sre-rag-api --tail=200 --since=15m | jq 'select(.level == "error")'
```

### 3. Verificar dependências

```bash
# Health check completo
curl -s http://localhost:8080/api/v1/health/dependencies | jq

# PostgreSQL
kubectl exec -n sre-rag sts/postgresql-0 -- pg_isready

# Redis
kubectl exec -n sre-rag sts/redis-0 -- redis-cli ping
```

### 4. Verificar deploy recente

```bash
# Histórico de releases
helm history sre-rag -n sre-rag

# Último deploy
kubectl rollout history deployment/sre-rag-api -n sre-rag
```

## Mitigação

### Se causado por deploy recente

```bash
# Rollback imediato
helm rollback sre-rag -n sre-rag

# Verificar
kubectl rollout status deployment/sre-rag-api -n sre-rag
```

### Se causado por dependência (PostgreSQL/Redis)

```bash
# Reiniciar PostgreSQL
kubectl delete pod postgresql-0 -n sre-rag

# Reiniciar Redis
kubectl delete pod redis-0 -n sre-rag
```

### Se causado por sobrecarga

```bash
# Escalar
kubectl scale deployment sre-rag-api -n sre-rag --replicas=5

# Verificar HPA
kubectl get hpa -n sre-rag
```

## Resolução

Confirme que o burn rate voltou ao normal:

```promql
slo:availability:burn_rate1h < 1
```

## Pós-Incidente

- [ ] Documentar timeline do incidente
- [ ] Calcular impacto no error budget
- [ ] Criar postmortem se SEV-1 ou SEV-2
- [ ] Adicionar action items para prevenir recorrência
