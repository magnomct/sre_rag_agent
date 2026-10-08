# Runbook: Missing ConfigMap / Secret

## Alert
`KubeContainerCrashLooping` / `PodCrashLoopBackOff`

## Severity
- **SEV-2**: Pod em falha contínua impedindo inicialização de réplicas saudáveis.

## Impact
Inicialização de pods interrompida por ausência de chaves de ambiente obrigatórias.

## Diagnóstico
```bash
# 1. Verificar logs do pod em crash
kubectl logs -l app=sre-rag-api --tail=50

# 2. Inspecionar secrets existentes
kubectl get secrets -n sre-rag

# 3. Verificar o manifesto do pod
kubectl get pod -l app=sre-rag-api -o yaml | grep -A 10 envFrom
```

## Mitigação
Criar o secret com as chaves obrigatórias exigidas pela aplicação:
```bash
kubectl create secret generic sre-rag-secrets --from-literal=OPENAI_API_KEY=mock-key --from-literal=DATABASE_URL=postgres://app:secret@postgresql:5432/sre_db -n sre-rag
```

## Resolução
Validar se o pod reinicia e atinge estado `Running (1/1)`:
```bash
kubectl rollout status deployment/sre-rag-api -n sre-rag
```

## Prevenção
- Utilizar Helm schema validation (`values.schema.json`).
- Implementar ExternalSecrets Operator ou HashiCorp Vault para injeção automática de credenciais.
