# Runbook: CNI Network Partition & mTLS Handshake Failure

## Alert
`MeshPeerAuthenticationFailed` / `CalicoBGPPeerDown`

## Severity
- **SEV-1**: Falha de comunicação inter-pod e quebra de malha de serviço.

## Impact
Microsserviços não conseguem falar entre nós distintos; transações falham com timeout de rede.

## Diagnóstico
```bash
# 1. Verificar status dos pods de CNI nos nós
kubectl get pods -n kube-system -l k8s-app=calico-node -o wide

# 2. Inspecionar logs do DaemonSet de rede
kubectl logs -n kube-system -l k8s-app=calico-node --tail=100 | grep -i error
```

## Mitigação
Reiniciar o DaemonSet de rede para forçar ressincronização das rotas BGP e malha mTLS:
```bash
kubectl rollout restart daemonset/calico-node -n kube-system
```

## Resolução
Aguardar rollout completo e testar conectividade entre nós:
```bash
kubectl rollout status daemonset/calico-node -n kube-system
```

## Prevenção
- Configurar BFD (Bidirectional Forwarding Detection) para convergência rápida de falhas no CNI.
- Monitorar métricas de rotas BGP e latência de malha de rede entre zonas de disponibilidade.
