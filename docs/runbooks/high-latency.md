# Runbook: High Latency

## Alert

`SLOLatencyP99High` / `SLOLatencyP99Critical`

## Severity

- **Warning**: P99 > 500ms
- **Critical**: P99 > 2s

## Impact

Usuários experimentam lentidão na API. Queries RAG demoram mais que o esperado.

## Diagnóstico

### 1. Verificar as métricas de latência

```promql
# P99 por endpoint
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))

# Latência média
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

### 2. Verificar saturação de recursos

```bash
# CPU e Memory dos pods
kubectl top pods -n sre-rag

# Verificar throttling
kubectl describe pod <pod-name> -n sre-rag | grep -A5 "State"
```

### 3. Verificar dependências

```bash
# PostgreSQL
kubectl exec -n sre-rag deploy/sre-rag-api -- curl -s http://localhost:8080/api/v1/health/dependencies

# Verificar conexões do PostgreSQL
kubectl exec -n sre-rag sts/postgresql-0 -- psql -U sre_user -d sre_rag -c "SELECT count(*) FROM pg_stat_activity;"

# Redis latência
kubectl exec -n sre-rag sts/redis-0 -- redis-cli --latency
```

### 4. Verificar logs

```bash
kubectl logs -n sre-rag -l app.kubernetes.io/name=sre-rag-api --tail=100 --since=15m | jq '.duration_seconds > 1'
```

## Mitigação

### Curto prazo

1. **Escalar horizontalmente**:
   ```bash
   kubectl scale deployment sre-rag-api -n sre-rag --replicas=5
   ```

2. **Aumentar limites de CPU** (se throttling):
   ```bash
   kubectl patch deployment sre-rag-api -n sre-rag --patch '{"spec":{"template":{"spec":{"containers":[{"name":"api","resources":{"limits":{"cpu":"1000m"}}}]}}}}'
   ```

3. **Reiniciar pods problemáticos**:
   ```bash
   kubectl rollout restart deployment sre-rag-api -n sre-rag
   ```

### Longo prazo

- Otimizar queries lentas
- Implementar caching mais agressivo
- Revisar índices do PostgreSQL
- Considerar connection pooling (PgBouncer)

## Resolução

Confirme que a latência voltou ao normal:

```promql
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) < 0.5
```
