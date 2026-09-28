# Postmortem Template

## Metadata

| Campo           | Valor               |
|-----------------|---------------------|
| **Data**        | YYYY-MM-DD          |
| **Severidade**  | SEV-1 / SEV-2 / SEV-3 |
| **Duração**     | X minutos           |
| **Autor**       |                     |
| **Status**      | Draft / Final       |

## Resumo

> Escreva um resumo de 2-3 linhas do que aconteceu.

## Impacto

- **Usuários afetados**: X%
- **Requests com erro**: X
- **Error budget consumido**: X%
- **Duração do impacto**: X minutos

## Timeline (UTC)

| Hora  | Evento |
|-------|--------|
| HH:MM | Alerta disparou: `<nome do alerta>` |
| HH:MM | Engenheiro de plantão acknowledge |
| HH:MM | Diagnóstico inicial: `<causa provável>` |
| HH:MM | Mitigação aplicada: `<ação tomada>` |
| HH:MM | Serviço restaurado |
| HH:MM | Monitoramento confirma normalização |

## Root Cause (5 Whys)

1. **Por que** o serviço ficou indisponível?
   - Porque...
2. **Por que** isso aconteceu?
   - Porque...
3. **Por que** isso não foi prevenido?
   - Porque...
4. **Por que** o monitoramento não detectou antes?
   - Porque...
5. **Por que** a mitigação demorou X minutos?
   - Porque...

## O que deu certo

- [ ] Alerta disparou corretamente
- [ ] Runbook estava atualizado
- [ ] Rollback foi rápido
- [ ] Comunicação foi eficiente

## O que deu errado

- [ ] Detecção demorada
- [ ] Runbook incompleto
- [ ] Rollback manual necessário
- [ ] Falta de redundância

## Action Items

| # | Ação | Responsável | Prazo | Prioridade | Status |
|---|------|-------------|-------|------------|--------|
| 1 |      |             |       | P1/P2/P3   | TODO   |
| 2 |      |             |       |            | TODO   |
| 3 |      |             |       |            | TODO   |

## Lições Aprendidas

> Insights do incidente que devem ser compartilhados com o time.

---

**⚠️ Postmortems são blameless.** O objetivo é aprender e melhorar, não culpar indivíduos.
