# Runbook: Pod CrashLoopBackOff

## Alert

`KubePodCrashLooping` / `APIContainerRestartCritical`

## Severity

- **Critical (SEV-1)**: Pods principais da API em estado de reinício contínuo (`CrashLoopBackOff`), impossibilitando atendimento de requisições.

## Impact

Capacidade do serviço drasticamente reduzida ou total indisponibilidade (502 Bad Gateway / 503 Service Unavailable). Violação imediata do SLO de Disponibilidade.

## Diagnóstico

### 1. Inspecionar status dos pods
```bash
kubectl get pods -n sre-rag -l app.kubernetes.io/name=sre-rag-api -o wide
```
Verifique a coluna `STATUS` (ex: `CrashLoopBackOff`) e o contador `RESTARTS`.

### 2. Analisar histórico de terminação
```bash
kubectl describe pod -n sre-rag -l app.kubernetes.io/name=sre-rag-api | grep -A 8 "Last State:"
```
Procure por `Exit Code` (ex: 1 para erro de aplicação, 137 para OOM, 255 para erro de runtime).

### 3. Verificar logs do contêiner anterior
```bash
kubectl logs -n sre-rag -l app.kubernetes.io/name=sre-rag-api --previous --tail=100
```
Erros comuns:
- `KeyError: 'DATABASE_URL'` ou `ValidationError: field required`: Variável de ambiente ausente no ConfigMap ou Secret.
- `ConnectionRefusedError`: Dependência de inicialização inacessível.

### 4. Verificar integridade do ConfigMap e Secret
```bash
kubectl get configmap api-config -n sre-rag -o yaml
kubectl get secret api-secrets -n sre-rag -o yaml
```

## Mitigação

### Cenário A: Variável de ambiente ou Secret ausente/inválido
1. Edite ou reaplique o manifesto do ConfigMap/Secret com a chave necessária.
2. Force um novo rollout limpo:
```bash
kubectl rollout restart deployment/sre-rag-api -n sre-rag
```

### Cenário B: Falha introduzida pelo último deploy
Se o crash começou após uma atualização recente de código/imagem:
```bash
# Executar rollback imediato para a revisão estável
helm rollback sre-rag -n sre-rag

# Acompanhar o status do rollout
kubectl rollout status deployment/sre-rag-api -n sre-rag
```

> ⚠️ **Anti-Pattern**: Apenas executar `kubectl delete pod` não resolve o problema, pois o ReplicaSet criará uma nova réplica com a mesma configuração com falha.

## Resolução

1. Confirme que os pods atingiram o estado `Running` e passaram no Readiness Probe (`READY 1/1`):
```bash
kubectl get pods -n sre-rag -w
```
2. Valide o endpoint de saúde:
```bash
curl -i http://localhost:8080/healthz
```

## Pós-Incidente

- [ ] Adicionar validação de esquema no CI para garantir que todas as variáveis obrigatórias existam.
- [ ] Implementar pre-flight checks ou testes de inicialização no pipeline de CD.
- [ ] Documentar o postmortem caso o incidente tenha violado o Error Budget.
