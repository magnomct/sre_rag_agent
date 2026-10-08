# Runbook: Pod Stuck in Pending (Insufficient CPU)

## Alert
`KubePodPending` / `PodUnschedulable`

## Severity
- **SEV-2**: Pods incapazes de agendamento em nós de computação.

## Impact
Novos pods não são criados; deploy fica bloqueado e HPA não consegue atender pico de carga.

## Diagnóstico
```bash
# 1. Descrever o pod pendente
kubectl describe pod -l app=sre-rag-api | grep -A 5 Events:

# 2. Verificar capacidade alocável dos nós
kubectl describe nodes | grep -A 8 'Allocated resources:'
```

## Mitigação
Reduzir os `resources.requests.cpu` no Helm para caber na capacidade alocável do cluster:
```bash
helm upgrade sre-rag ./helm/sre-rag --set api.resources.requests.cpu=250m -n sre-rag
```

## Resolução
Confirmar que os pods foram agendados e estão em `Running`:
```bash
kubectl get pods -n sre-rag -o wide
```

## Prevenção
- Configurar Cluster Autoscaler / Karpenter para subir nós sob demanda.
- Definir ResourceQuotas e LimitRanges por namespace.
