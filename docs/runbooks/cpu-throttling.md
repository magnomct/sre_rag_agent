# Runbook: Severe CFS CPU Throttling (Latência Fantasma)

## Alert
`ContainerHighCPUThrottling` (Throttling > 50% dos períodos)

## Severity
- **SEV-2**: Latência P99 degradada sem saturação visível de CPU.

## Impact
Requisições congelam por centenas de milissegundos devido a pausas forçadas pelo scheduler do Linux.

## Diagnóstico
```bash
# 1. Inspecionar estatísticas do CFS no cgroup
kubectl exec -it deployment/sre-rag-api -n sre-rag -- cat /sys/fs/cgroup/cpu.stat

# 2. PromQL para throttling
container_cpu_cfs_throttled_periods_total / container_cpu_cfs_periods_total * 100
```

## Mitigação
Remover o limite rígido de CPU (`limits.cpu=null`) mantendo requests adequados:
```bash
helm upgrade sre-rag ./helm/sre-rag --set api.resources.limits.cpu=null --reuse-values -n sre-rag
```

## Resolução
Confirmar queda da métrica de throttling para 0% e normalização da latência P99:
```promql
rate(container_cpu_cfs_throttled_seconds_total[5m]) < 0.01
```

## Prevenção
- Adotar a recomendação moderna do Kubernetes de não fixar CPU limits para workloads de microserviços.
- Dimensionar CPU requests com base no percentil 90 de consumo sob tráfego real.
