# Runbook: PVC Deadlock (Multi-Attach Error em RWO)

## Alert
`VolumeAttachmentStuck` / `FailedMountError`

## Severity
- **SEV-2**: Pod com volume persistente incapaz de inicializar após reinício de nó.

## Impact
StatefulSet ou pod com PVC não inicia, mantendo aplicação fora do ar.

## Diagnóstico
```bash
# 1. Inspecionar eventos de montagem do pod
kubectl describe pod -l app=sre-rag-api | grep -i attach

# 2. Listar VolumeAttachments no cluster
kubectl get volumeattachment
```

## Mitigação
Forçar a deleção do VolumeAttachment órfão preso ao nó antigo:
```bash
kubectl delete volumeattachment $(kubectl get volumeattachment -o jsonpath='{.items[0].metadata.name}') --force
```

## Resolução
Verificar montagem bem-sucedida do PV no novo pod:
```bash
kubectl get pvc -n sre-rag
kubectl get pods -n sre-rag
```

## Prevenção
- Configurar StorageClasses modernas com suporte a CSI `volumeBindingMode: WaitForFirstConsumer`.
- Ajustar timeouts de node fencing e controller-manager volume detachment.
