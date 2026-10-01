# Postmortem: CrashLoopBackOff da API por Variável de Ambiente Ausente

## Metadata

| Campo           | Valor               |
|-----------------|---------------------|
| **Data**        | 2026-09-02          |
| **Severidade**  | SEV-1               |
| **Duração**     | 18 minutos          |
| **Autor**       | Carlos Magno Cordeiro |
| **Status**      | Final               |

## Resumo

Durante o deploy da versão v1.2.0 da API via Helm, uma nova variável de ambiente obrigatória (`EMBEDDING_BATCH_SIZE`) foi adicionada ao modelo Pydantic do `config.py`, porém não foi mapeada no `api-configmap.yaml`. Todos os pods da API entraram em estado `CrashLoopBackOff` imediatamente após o deploy, causando indisponibilidade total.

## Impacto

- **Usuários afetados**: 100% dos usuários externos durante 18 minutos.
- **Requests com erro**: ~2.800 requisições falhadas com HTTP 502 (Bad Gateway).
- **Error budget consumido**: 41.6% do budget mensal.
- **Duração do impacto**: 18 minutos.

## Timeline (UTC)

| Hora  | Evento |
|-------|--------|
| 10:04 | Deploy da versão v1.2.0 executado via CD. |
| 10:06 | Readiness probes falham e pods entram em CrashLoopBackOff. |
| 10:07 | Alerta `SLOAvailabilityBurnRateCritical` dispara no Alertmanager. |
| 10:08 | Engenheiro de plantão inspeciona logs: `KeyError: 'EMBEDDING_BATCH_SIZE'`. |
| 10:12 | Executado comando `helm rollback sre-rag` para a versão anterior estável. |
| 10:15 | Pods da versão anterior sobem com sucesso (`READY 1/1`). |
| 10:22 | Testes de fumaça confirmam recuperação total do serviço. |

## Root Cause (5 Whys)

1. **Por que** a API ficou fora do ar?
   - Porque os novos pods sofreram crash antes de passar pelo readiness probe.
2. **Por que** os pods sofreram crash?
   - Porque a inicialização do Pydantic lançou exceção de campo obrigatório ausente.
3. **Por que** a variável estava ausente?
   - Porque o commit adicionou a variável no código, mas o template do Helm não foi atualizado.
4. **Por que** o CI/CD não pegou o erro antes do deploy?
   - Porque os testes unitários do CI usavam mock do settings com valores default hardcoded.
5. **Por que** o rollout não abortou automaticamente?
   - Porque o Helm upgrade foi executado sem a flag `--wait --atomic`.

## O que deu certo

- [x] O comando `helm rollback` restaurou a versão anterior com rapidez e precisão.
- [x] O diagnóstico via `kubectl logs --previous` apontou a linha exata da falha em menos de 2 minutos.

## O que deu errado

- [x] O deploy não utilizou `--atomic` para rollback automático em caso de falha de rollout.
- [x] Testes de fumaça de helm template não validavam se todos os campos do Pydantic Settings estavam presentes no ConfigMap.

## Action Items

| # | Ação | Responsável | Prazo | Prioridade | Status |
|---|------|-------------|-------|------------|--------|
| 1 | Adicionar `--atomic --wait` no comando de deploy do CD e Makefile | Carlos Magno | 2026-09-03 | P1 | Concluído |
| 2 | Fornecer valores default defensivos no Pydantic `config.py` | Carlos Magno | 2026-09-04 | P1 | Concluído |
| 3 | Criar teste automatizado que compara campos do ConfigMap com o Settings | Equipe SRE | 2026-09-08 | P2 | Concluído |
