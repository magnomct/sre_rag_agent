# Postmortem: Incidente de Disparo Crítico do Burn Rate de Disponibilidade

## Metadata

| Campo           | Valor               |
|-----------------|---------------------|
| **Data**        | 2026-09-27          |
| **Severidade**  | SEV-1               |
| **Duração**     | 6 minutos           |
| **Autor**       | SRE Team            |
| **Status**      | Final               |

## Resumo

Durante o processo de testes contínuos de resiliência, a API RAG sofreu uma interrupção em sua capacidade de servir respostas, passando a retornar erros 500 de forma sistemática. O alerta de `SLOAvailabilityBurnRateCritical` foi acionado pelo Prometheus e Alertmanager. O serviço foi normalizado após a reversão de uma feature flag instável através de uma operação de mitigação manual. O MTTR foi mantido dentro dos limites aceitáveis do Error Budget.

## Impacto

- **Usuários afetados:** 100% dos usuários durante a janela.
- **Requests com erro:** Aproximadamente 300 requisições simuladas falharam.
- **Error budget consumido:** Cerca de 0.5% do budget total de 30 dias foi consumido no período.
- **Duração do impacto:** 6 minutos.

## Timeline (UTC)

| Hora  | Evento |
|-------|--------|
| **02:30** | Teste de tráfego iniciado. Sistema estável. |
| **02:32** | Feature flag `simulate_500` ativada inadvertidamente no endpoint `/api/v1/chaos/500`. |
| **02:33** | API passa a responder requests com HTTP 500 (Internal Server Error). |
| **02:35** | **MTTD:** Prometheus avalia a regra `slo:availability:burn_rate1h > 14.4`. Alertmanager dispara notificação de `SLOAvailabilityBurnRateCritical`. |
| **02:36** | On-call SRE visualiza o dashboard Grafana "SRE RAG Agent - Overview" e identifica taxa de erro em 100%. Tráfego, rede e persistência parecem saudáveis. |
| **02:37** | SRE investiga logs: `Chaos Monkey injected 500 Internal Server Error`. |
| **02:38** | **Mitigação:** SRE desabilita o Chaos Monkey ativando a reversão (`enable=false`). |
| **02:39** | **MTTR:** Tráfego volta a responder 200 OK. Alertas entram em estado "Resolved". Fim do incidente. |

## Root Cause (5 Whys)

1. **Por que o serviço ficou indisponível devolvendo 500?**
   - Porque a rota no middleware HTTP começou a injetar erros deliberados.
2. **Por que a rota começou a injetar erros?**
   - Porque o estado global `chaos_state.simulate_500` foi ativado para `True`.
3. **Por que ele foi ativado em ambiente de produção/laboratório sem aviso prévio?**
   - Porque a API não tinha proteção ou autenticação no endpoint `/api/v1/chaos/500`, permitindo qualquer request ativá-lo remotamente.
4. **Por que o endpoint não tem proteção?**
   - Porque foi adicionado recentemente para testes de stress sem as devidas validações de ambiente (env protection).
5. **Por que isso passou no CI/CD?**
   - Porque a política de segurança de scanners ainda não checa regras estáticas (SAST) em endpoints novos baseados em `chaos_state`.

## O que deu certo

- [x] O framework de alertas **SLO-based** (Burn Rate) funcionou perfeitamente. Disparou rapidamente porque o budget estourou a métrica estrita de 14.4x (2% de budget).
- [x] Dashboards mostraram clareza imediata sobre latência (estável) vs taxa de erro (alta).
- [x] Logs estruturados apresentaram exatamente a origem ("Chaos Monkey injected..."), diminuindo o tempo de investigação.
- [x] MTTR (Mean Time to Recovery) de ~6 minutos, muito inferior ao SLA.

## O que deu errado

- [x] Inexistência de autorização (ex: RBAC ou token JWT) em um endpoint capaz de alterar estados críticos (Chaos).
- [x] O tráfego de usuários reais não foi desviado/cortado imediatamente (Poderíamos ter um circuit breaker).

## Action Items

| # | Ação | Responsável | Prazo | Prioridade | Status |
|---|------|-------------|-------|------------|--------|
| 1 | Adicionar autenticação (API Key / JWT) para todas as rotas `/api/v1/chaos/*`. | Squad Dev | Próximo Sprint | P1 | TODO |
| 2 | Habilitar Chaos Monkey apenas se `ENVIRONMENT=test` ou `staging`, mas bloquear execução em produção via código. | Squad Dev | Próximo Sprint | P2 | TODO |
| 3 | Criar alerta para avisar quando um endpoint de Chaos for ativado. | SRE Team | Próximo Sprint | P3 | TODO |

## Lições Aprendidas

A adoção de Multi-window Burn Rates do Google SRE prova o seu valor ao reduzir alertas falsos (flapping) e detectar problemas massivos em menos de 5 minutos, garantindo ação rápida antes que a SLA total do mês seja comprometida.
