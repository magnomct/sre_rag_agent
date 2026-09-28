# Resposta a Incidentes (Incident Response)

Este documento centraliza o fluxo de resposta a incidentes adotado pela equipe de SRE.

## Ciclo de Vida do Incidente

1. **Detecção (MTTD):** O Prometheus identifica a anomalia através de SLO Burn Rates e envia para o Alertmanager.
2. **Triagem (Triage):** O On-call SRE reconhece (Acks) o alerta e determina a severidade.
3. **Investigação:** Utilizando Grafana, Logs e ferramentas como `kubectl`, a causa raiz provável é identificada.
4. **Mitigação (MTTR):** Ações imediatas são tomadas para restaurar o serviço aos níveis do SLO (ex: Rollback de Helm release, expansão do HPA, bloqueio de tráfego, toggle de Feature Flag).
5. **Resolução:** O alerta é resolvido automaticamente pelo Alertmanager após o serviço estabilizar.
6. **Postmortem:** Análise *blameless* para evitar recorrência e gerar *Action Items*.

## Playbooks e Runbooks

Os procedimentos específicos de mitigação para cada cenário estão documentados na pasta `runbooks/`:

- [High Error Rate (Erros 5xx / Queda de Availability)](./runbooks/high-error-rate.md)
- [High Latency (P99 acima do SLO)](./runbooks/high-latency.md)

## Simulando um Incidente de Disponibilidade

Para comprovar a resiliência do sistema e o funcionamento do fluxo de SRE, o laboratório possui um mecanismo de **Chaos Engineering**.

### O Teste
1. **Ambiente Saudável:** A API e o cluster estão operacionais. O dashboard mostra Disponibilidade em ~100% e Burn Rate = 0.
2. **Injeção de Falha:**
   ```bash
   # Habilita o modo de falha simulando 500 Internal Server Errors
   curl -X POST "http://localhost:8080/api/v1/chaos/500?enable=true"
   ```
3. **Aumento de Erros e Detecção (MTTD):**
   - O endpoint da API começa a devolver HTTP 500 para todas as requisições (exceto `/healthz` e `/metrics`).
   - O Prometheus coleta as métricas e o SLI de disponibilidade despenca.
   - O Burn Rate de 1h salta para mais de 14.4x o permitido.
   - O Alerta `SLOAvailabilityBurnRateCritical` é disparado.
4. **Investigação e Mitigação (MTTR):**
   - O SRE verifica os painéis no Grafana e confirma que o tráfego está normal, mas a taxa de erro está alta (500s).
   - O runbook [High Error Rate](./runbooks/high-error-rate.md) sugere reverter mudanças ou alterar configurações de estado.
   - **Ação:** O Chaos mode é desligado via comando ou realiza-se um Rollback via Helm caso tenha sido uma release nova.
   ```bash
   curl -X POST "http://localhost:8080/api/v1/chaos/500?enable=false"
   ```
5. **Recuperação:** A API volta a processar requests com HTTP 200. O Burn rate diminui e os alertas se auto-resolvem (Resolved) no Alertmanager.
