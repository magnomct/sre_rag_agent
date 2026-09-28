# Service Level Objectives (SLOs)

Este documento define as metas de confiabilidade (SLOs) estabelecidas para os microsserviços do **SRE Production Lab**. Estas métricas são fundamentais para equilibrar inovação com confiabilidade.

## SLOs Definidos

| Serviço | SLI (Indicador) | SLO (Objetivo) | Janela | Descrição |
|---------|-----------------|----------------|--------|-----------|
| **API RAG** | **Availability:** `% requests com HTTP < 500` | 99.9% | 30 dias | Alta disponibilidade para consultas do usuário. Permite ~43 minutos de indisponibilidade por mês. |
| **API RAG** | **Latency:** `% requests < 500ms` | 99.5% | 30 dias | Respostas rápidas para manter a experiência do usuário fluída. |
| **PostgreSQL** | **Capacity:** `% conexões ativas / max conexões` | < 80% | Instantâneo | Evita exaustão do pool de conexões (saturação). |
| **Redis** | **Performance:** `% cache hit rate` | > 80% | 30 dias | Garante que o cache está sendo efetivo para reduzir carga e latência. |

## Error Budget e Burn Rate

Com um SLO de **99.9%** para Disponibilidade em 30 dias:
- **Error Budget Total:** 0.1% das requisições (ou ~43.2 minutos de downtime contínuo).
- Adotamos o modelo de **Multi-window Burn Rate** do Google SRE Workbook para alertas.

### Alertas de Burn Rate

Alertas não são disparados por falhas isoladas, mas sim pelo consumo acelerado do Error Budget.

| Severidade | Burn Rate | Janela Analisada | Consumo do Budget | Ação Esperada |
|------------|-----------|------------------|-------------------|---------------|
| **CRITICAL** | `> 14.4x` | 1 hora | Consome 2% do budget de 30 dias em 1 hora | Investigação imediata. Pode acionar pager. (MTTD esperado: < 5 min) |
| **WARNING** | `> 6x` | 6 horas | Consome 5% do budget de 30 dias em 6 horas | Cria ticket/alerta no Slack para investigação no horário comercial. |

## Monitoramento PromQL (Recording Rules)

O Prometheus pre-computa os SLIs usando Recording Rules para otimizar os dashboards e alertas:

- Disponibilidade (1h): `sli:availability:ratio_rate1h`
- Burn Rate (1h): `slo:availability:burn_rate1h`

Se `slo:availability:burn_rate1h > 14.4` E `slo:availability:burn_rate6h > 6`, o Alertmanager emite um alerta **CRITICAL**.
