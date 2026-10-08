# Runbook: HPA Flapping / Thrashing Loop

## Alert
`HPAFlappingWarning` / `HPAMaxScaleReachedFrequent`

## Severity
- **SEV-2**: Variação agressiva no número de pods degradando a estabilidade da API.

## Impact
Ciclos constantes de inicialização e desligamento de pods geram perda de conexões e latência.

## Diagnóstico
```bash
# 1. Inspecionar histórico do HPA
kubectl describe hpa sre-rag-api -n sre-rag

# 2. Monitorar oscilação de réplicas
kubectl get hpa sre-rag-api -n sre-rag --watch
```

## Mitigação
Adicionar janela de estabilização de scale-down de 300 segundos:
```bash
kubectl patch hpa sre-rag-api -n sre-rag --patch '{"spec":{"behavior":{"scaleDown":{"stabilizationWindowSeconds":300}}}}'
```

## Resolução
Acompanhar estabilização do HPA durante janela de 10 minutos sem oscilação brusca.

## Prevenção
- Definir políticas de `scaleDown.policies` com taxa máxima de redução percentual por minuto.
- Utilizar métricas customizadas de negócio (ex: contagem de requests/segundo) além de CPU.
