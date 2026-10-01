# Postmortem: Alta Latência por Falta de Índice em Consultas Vetoriais

## Metadata

| Campo           | Valor               |
|-----------------|---------------------|
| **Data**        | 2026-09-20          |
| **Severidade**  | SEV-2               |
| **Duração**     | 52 minutos          |
| **Autor**       | Carlos Magno Cordeiro |
| **Status**      | Final               |

## Resumo

Um aumento no volume de documentos armazenados no banco de dados fez com que as buscas por similaridade vetorial sem índice HNSW/IVFFlat passassem a realizar varreduras sequenciais completas (Seq Scan). A latência P99 disparou de 180ms para 4.800ms, violando o SLO de latência.

## Impacto

- **Usuários afetados**: Aproximadamente 45% das buscas com degradação perceptível.
- **Requests acima do SLO**: 3.200 requisições com latência > 500ms.
- **Error budget consumido**: 23.5% do budget de latência.
- **Duração do impacto**: 52 minutos.

## Timeline (UTC)

| Hora  | Evento |
|-------|--------|
| 16:10 | Lote de 15.000 novos documentos ingerido na base. |
| 16:18 | Alerta `SLOLatencyBurnRateCritical` dispara no Alertmanager. |
| 16:22 | Plantonista identifica aumento de CPU no PostgreSQL e latência no endpoint `/api/v1/query`. |
| 16:30 | Análise do `pg_stat_activity` identifica queries lentas de cálculo de distância cosseno. |
| 16:42 | Criação concorrente de índice vetorial: `CREATE INDEX CONCURRENTLY ... USING hnsw`. |
| 16:55 | Índice finalizado; tempo de consulta cai instantaneamente de 4.8s para 12ms. |
| 17:02 | Latência P99 estabilizada abaixo de 200ms; incidente encerrado. |

## Root Cause (5 Whys)

1. **Por que** a latência P99 subiu para quase 5 segundos?
   - Porque as consultas de busca vetorial demoravam mais de 4 segundos para retornar.
2. **Por que** as buscas demoravam 4 segundos?
   - Porque a tabela de embeddings realizava Seq Scan comparando cada vetor sequencialmente.
3. **Por que** não havia índice vetorial?
   - Porque a tabela foi criada para o protótipo inicial com poucos documentos, onde Seq Scan era rápido.
4. **Por que** a ingestão de 15.000 documentos não incluiu aviso prévio à equipe de confiabilidade?
   - Porque o processo de ingestão não possuía validação de volumetria no ambiente de staging.
5. **Por que** o monitoramento não alertou antes do SLO estourar?
   - Porque a janela de alerta de latência utilizava amostragem de 10 minutos.

## O que deu certo

- [x] O comando `CREATE INDEX CONCURRENTLY` permitiu criar o índice sem travar leituras no banco.
- [x] As recording rules do Prometheus forneceram visibilidade imediata da quebra de SLO.

## O que deu errado

- [x] Ausência de índice HNSW definido nas migrações iniciais.
- [x] Falta de limiar de alerta antecipado para tempo de execução de queries no Postgres.

## Action Items

| # | Ação | Responsável | Prazo | Prioridade | Status |
|---|------|-------------|-------|------------|--------|
| 1 | Garantir índices HNSW em todas as tabelas vetoriais nas migrações | Carlos Magno | 2026-09-22 | P1 | Concluído |
| 2 | Configurar alerta para `pg_stat_activity` queries > 1000ms | Equipe SRE | 2026-09-25 | P2 | Concluído |
| 3 | Criar verificação no pipeline de ingestão que valida a presença de índices | Equipe SRE | 2026-09-28 | P2 | Concluído |
