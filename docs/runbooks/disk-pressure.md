# Runbook: Node Disk Pressure

## Alert

`KubeNodeDiskPressure` / `NodeDiskUsageHigh`

## Severity

- **Major (SEV-2)**: Nó atingiu mais de 85% de uso de disco. O Kubelet iniciou evicção preventiva de pods.

## Impact

Pods podem ser evictados abruptamente (`Reason: Evicted`), novos pods não podem ser agendados no nó afetado e réplicas entram em estado `Pending`, causando aumento de latência e degradação de capacidade.

## Diagnóstico

### 1. Identificar os nós sob pressão
```bash
kubectl describe nodes | grep -A 6 "Conditions:"
kubectl get nodes -o custom-columns=NAME:.metadata.name,DISK_PRESSURE:.status.conditions[?\(@.type=="DiskPressure"\)].status
```

### 2. Identificar pods evictados
```bash
kubectl get pods -A -o wide | grep -E "Evicted|Pending"
```

### 3. Inspecionar partições e diretórios no nó
Conecte-se ao nó ou container privilegiado e inspecione:
```bash
df -h
du -sh /var/lib/containerd/* | sort -hr | head -10
du -sh /var/log/pods/* | sort -hr | head -10
```

## Mitigação

### 1. Aplicar Cordon no nó
Impeça que novos pods sejam agendados no nó enquanto a manutenção ocorre:
```bash
kubectl cordon <node-name>
```

### 2. Liberar espaço em disco
- **Limpar imagens e containers órfãos via containerd/crictl**:
```bash
crictl rmi --prune
```
- **Limpar arquivos de log acumulados**:
```bash
find /var/log/pods/ -name "*.log" -size +100M -exec truncate -s 0 {} \;
```

### 3. Drenar pods se necessária manutenção profunda
Se o nó precisar ser reciclado ou reformatado:
```bash
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data --force
```

### 4. Reabilitar o nó (Uncordon)
Após a normalização do disco (< 70% de utilização):
```bash
kubectl uncordon <node-name>
```

> ⚠️ **Anti-Pattern**: Reiniciar o nó na nuvem sem limpeza prévia apenas restarta o nó com o mesmo volume saturado, gerando novo DiskPressure em minutos.

## Resolução

1. Verifique que a condição `DiskPressure` no nó voltou a `False`:
```bash
kubectl get node <node-name> -o jsonpath='{.status.conditions[?(@.type=="DiskPressure")].status}'
```
2. Verifique que nenhum pod permanece no estado `Evicted` ou `Pending`.

## Pós-Incidente

- [ ] Ajustar retenção de log rotation no containerd (`max-size=50m`, `max-file=3`).
- [ ] Implementar cronjob de garbage collection de imagens não utilizadas.
