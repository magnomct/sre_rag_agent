# Runbook: 503 Service Unavailable (Service Selector Mismatch)

## Alert
`IngressHighHttp5xxRate` / `KubeServiceEmptyEndpoints`

## Severity
- **SEV-1**: Tráfego de borda recebendo HTTP 503 Service Unavailable.

## Impact
Todas as requisições de clientes externos falham na camada de roteamento.

## Diagnóstico
```bash
# 1. Verificar endpoints do Service
kubectl get endpoints sre-rag-api -n sre-rag

# 2. Comparar labels dos pods com o selector do Service
kubectl get pods -n sre-rag --show-labels
kubectl get svc sre-rag-api -n sre-rag -o jsonpath='{.spec.selector}'
```

## Mitigação
Corrigir o selector do Service para corresponder aos labels reais dos pods:
```bash
kubectl set selector service sre-rag-api app.kubernetes.io/name=sre-rag-api -n sre-rag
```

## Resolução
Verificar se os IPs dos pods aparecem imediatamente no Service Endpoints:
```bash
kubectl get endpoints sre-rag-api -n sre-rag
```

## Prevenção
- Padronizar labels usando o padrão oficial do Helm (`app.kubernetes.io/name`).
- Testes automatizados de integração na pipeline de CI/CD validando endpoints de serviço pós-deploy.
