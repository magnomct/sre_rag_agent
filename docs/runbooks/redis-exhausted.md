# Runbook: Redis Connection Pool Exhaustion

## Alert

`RedisTooManyConnections` / `RedisConnectionPoolExhausted`

## Severity

- **Major (SEV-2)**: O Redis atingiu 100% da sua capacidade máxima de conexões (`maxclients`), rejeitando novos clientes.

## Impact

A API não consegue ler nem escrever no cache Redis, gerando erros `redis.exceptions.ConnectionError: ERR max number of clients reached`. Consequentemente, todas as requisições caem como cache miss no PostgreSQL, elevando drasticamente a latência e consumindo o Error Budget.

## Diagnóstico

### 1. Inspecionar conexões ativas no Redis
```bash
kubectl exec -n sre-rag sts/redis-0 -- redis-cli info clients
```
Observe os campos:
- `connected_clients`: Número de clientes conectados.
- `blocked_clients`: Requisições em espera de conexão.
- `maxclients`: Limite absoluto configurado.

### 2. Verificar consultas no Prometheus
```promql
# Percentual de conexões ativas no Redis
redis_connected_clients / redis_config_maxclients * 100

# Erros de conexão na API
rate(redis_connection_errors_total[5m])
```

### 3. Analisar comportamento da API
Verifique se houve vazamento de conexões (connection leaks) em workers assíncronos ou conexões não reutilizadas na classe `RAGEngine` ([app/rag/engine.py]).

## Mitigação

### 1. Aumento emergencial de `maxclients`
Se o nó possui recursos de memória disponíveis, eleve o limite dinamicamente no Redis sem reinício:
```bash
kubectl exec -n sre-rag sts/redis-0 -- redis-cli config set maxclients 2000
```

### 2. Ajustar Connection Pooling na Aplicação
Revise a configuração do pool de conexões no deployment da API (`app-configmap.yaml` ou variáveis de ambiente):
```yaml
REDIS_MAX_CONNECTIONS: "50"
REDIS_TIMEOUT: "3"
```
Reaplique a configuração e realize um rollout ordenado:
```bash
kubectl rollout restart deployment/sre-rag-api -n sre-rag
```

> ⚠️ **Anti-Pattern**: Reiniciar abruptamente o pod do Redis descarta todos os dados da memória volátil e causa uma tempestade de requisições diretas (cache stampede) no PostgreSQL.

## Resolução

1. Confirme que o número de conexões retornou a um patamar saudável (< 70% do limite):
```bash
kubectl exec -n sre-rag sts/redis-0 -- redis-cli info clients | grep connected_clients
```
2. Valide que a taxa de acerto de cache (cache hit rate) voltou a subir:
```bash
curl -s http://localhost:8080/metrics | grep cache_hits_total
```

## Pós-Incidente

- [ ] Implementar Connection Pooling com encerramento garantido de conexões (context managers) na aplicação.
- [ ] Configurar alerta preditivo quando `connected_clients` ultrapassar 80% do `maxclients`.
