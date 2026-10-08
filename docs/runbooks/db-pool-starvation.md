# Runbook: PostgreSQL Connection Pool Starvation & Idle Locks

## Alert
`PostgresTooManyConnections` / `PostgresTransactionIdleTooLong`

## Severity
- **SEV-1**: Falha geral de escrita e leitura no banco de dados.

## Impact
API retorna erros 500 por incapacidade de adquirir conexões no banco de dados.

## Diagnóstico
```bash
# 1. Consultar estado das conexões no PostgreSQL
kubectl exec -i sts/postgresql-0 -n sre-rag -- psql -U postgres -d sre_db -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# 2. Identificar conexões em idle in transaction há mais de 2 minutos
kubectl exec -i sts/postgresql-0 -n sre-rag -- psql -U postgres -d sre_db -c "SELECT pid, now() - state_change as duration, query FROM pg_stat_activity WHERE state = 'idle in transaction';"
```

## Mitigação
Finalizar as transações presas com `pg_terminate_backend`:
```bash
kubectl exec -i sts/postgresql-0 -n sre-rag -- psql -U postgres -d sre_db -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle in transaction' AND state_change < now() - INTERVAL '2 minutes';"
```

## Resolução
Verificar liberação de slots de conexão e restabelecimento das rotas da API:
```bash
curl -s http://localhost:8080/api/v1/health | jq
```

## Prevenção
- Implantar PgBouncer em modo transaction pooling.
- Configurar `idle_in_transaction_session_timeout = 30000` (30s) no `postgresql.conf`.
