# Runbook: DNS Resolution Failure

## Alert

`KubeDNSResolutionErrors` / `CoreDNSDown`

## Severity

- **Critical (SEV-1)**: Pods não conseguem resolver nomes internos (`postgresql.sre-rag.svc.cluster.local`) ou externos.

## Impact

Total quebra de comunicação entre microsserviços. A API não consegue localizar o banco de dados nem o Redis, gerando erros `socket.gaierror: [Errno -2] Name or service not known` e paralisação total do RAG.

## Diagnóstico

### 1. Testar resolução de dentro do pod da aplicação
```bash
kubectl exec -n sre-rag deploy/sre-rag-api -- nslookup postgresql.sre-rag.svc.cluster.local
kubectl exec -n sre-rag deploy/sre-rag-api -- nslookup redis.sre-rag.svc.cluster.local
```

### 2. Verificar saúde dos pods do CoreDNS
```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns -o wide
kubectl logs -n kube-system -l k8s-app=kube-dns --tail=100
```

### 3. Verificar regras de NetworkPolicy
Verifique se alguma NetworkPolicy foi aplicada sem liberar tráfego de saída (Egress) para a porta 53 (UDP e TCP):
```bash
kubectl get networkpolicies -n sre-rag -o yaml
```

## Mitigação

### 1. Se bloqueado por NetworkPolicy restritiva
Adicione a regra explícita permitindo tráfego de saída na porta 53 para o CoreDNS:
```yaml
egress:
  - ports:
      - protocol: UDP
        port: 53
      - protocol: TCP
        port: 53
```
Aplique a NetworkPolicy corrigida:
```bash
kubectl apply -f helm/sre-rag/templates/network-policies.yaml -n sre-rag
```

### 2. Se o CoreDNS estiver degradado ou travado
Execute o restart dos pods do CoreDNS:
```bash
kubectl rollout restart deployment/coredns -n kube-system
kubectl rollout status deployment/coredns -n kube-system
```

> ⚠️ **Anti-Pattern**: Configurar IPs estáticos hardcoded nos ConfigMaps ou código da aplicação. Os IPs de pods e serviços no Kubernetes são voláteis e causarão novas quebras catastróficas.

## Resolução

1. Execute um novo teste de resolução de nomes a partir do pod:
```bash
kubectl exec -n sre-rag deploy/sre-rag-api -- python3 -c "import socket; print('Resolved:', socket.gethostbyname('postgresql.sre-rag.svc.cluster.local'))"
```
2. Confirme que os logs da aplicação deixaram de reportar `socket.gaierror`.

## Pós-Incidente

- [ ] Incluir validação automatizada de DNS no healthcheck de startup da aplicação.
- [ ] Auditar NetworkPolicies em pipelines de CI antes de deploys em produção.
