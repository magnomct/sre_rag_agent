# Postmortem: Incidente de Esgotamento do Pool de Conexões Redis

## Metadata

| Campo           | Valor               |
|-----------------|---------------------|
| **Data**        | 2026-08-14          |
| **Severidade**  | SEV-2               |
| **Duração**     | 38 minutos          |
| **Autor**       | Carlos Magno Cordeiro |
| **Status**      | Final               |

## Resumo

Às 14:22 UTC, um aumento súbito de tráfego somado a conexões Redis que não eram liberadas adequadamente no endpoint de busca vetorial causou o esgotamento do limite `maxclients` (1000) do Redis. Todas as requisições subsequentes começaram a falhar com erro de conexão de cache e sofreram degradação de latência ao consultar o PostgreSQL em fallback.

## Impacto

- **Usuários afetados**: 32% dos usuários ativos durante a janela.
- **Requests com erro**: ~1.450 requisições com timeout HTTP 504 / 500.
- **Error budget consumido**: 14.8% do budget mensal de 30 dias.
- **Duração do impacto**: 38 minutos.

## Timeline (UTC)

| Hora  | Evento |
|-------|--------|
| 14:22 | Tráfego sobe de 80 rps para 350 rps. |
| 14:25 | Alerta `RedisTooManyConnections` dispara no Alertmanager. |
| 14:27 | Engenheiro de plantão dá ACK no PagerDuty e inicia investigação. |
| 14:32 | Diagnóstico confirma `connected_clients` em 1000/1000 no Redis. |
| 14:38 | Ação emergencial: `maxclients` elevado para 2500 via `redis-cli config set`. |
| 14:44 | A API volta a conseguir conexões; taxa de erro cai para 0%. |
| 15:00 | Monitoramento confirma estabilização total de latência P99 (< 450ms). |

## Root Cause (5 Whys)

1. **Por que** a API começou a dar timeouts e erros 500?
   - Porque as chamadas de verificação de cache no Redis estavam falhando com erro `max number of clients reached`.
2. **Por que** o número de clientes conectados atingiu o limite máximo de 1000?
   - Porque cada réplica da API estava abrindo novas conexões assíncronas por request sem utilizar um singleton pooling reutilizável.
3. **Por que** as conexões não eram fechadas?
   - Porque a inicialização do cliente Redis no `RAGEngine` instanciou conexões sob demanda sem gerenciador de contexto (`with`).
4. **Por que** isso não ocorreu em staging?
   - Porque os testes de carga de staging nunca superaram 50 conexões concorrentes simultâneas.
5. **Por que** o alerta não foi preditivo?
   - Porque o alerta só disparava com 95% de uso, deixando pouco tempo hábil antes do esgotamento.

## O que deu certo

- [x] O Alertmanager notificou o time em menos de 3 minutos do início da saturação.
- [x] O comando dinâmico `redis-cli config set maxclients` evitou a reinicialização catastrófica do Redis.
- [x] O fallback gracioso para o banco de dados evitou indisponibilidade de 100%.

## O que deu errado

- [x] Falta de connection pooling na classe `RAGEngine`.
- [x] Ausência de teste de saturação de conexões no pipeline de CI.

## Action Items

| # | Ação | Responsável | Prazo | Prioridade | Status |
|---|------|-------------|-------|------------|--------|
| 1 | Refatorar `RAGEngine` para utilizar connection pool compartilhado e reutilizável | Carlos Magno | 2026-08-16 | P1 | Concluído |
| 2 | Configurar alerta preventivo em 75% de `maxclients` no Prometheus | Equipe SRE | 2026-08-18 | P2 | Concluído |
| 3 | Adicionar teste de estresse de conexões no `scripts/load-test.sh` | Equipe SRE | 2026-08-20 | P2 | Concluído |
