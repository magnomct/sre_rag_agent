# Runbook: TLS Certificate Expiring Soon

## Alert

`CertificateExpiringSoon` / `TLSCertExpiringIn30Days`

## Severity

- **Warning (SEV-3)**: Certificado expira em menos de 15 dias.
- **Critical (SEV-2)**: Certificado expira em menos de 48 horas.

## Impact

Se o certificado expirar, clientes HTTPS (browsers, apps móveis, chamadas mTLS) exibirão avisos críticos de segurança (`NET::ERR_CERT_DATE_INVALID`) e abortarão conexões com erro 495 / SSL Handshake Failure.

## Diagnóstico

### 1. Inspecionar recurso Certificate e Issuer
```bash
kubectl get certificate -n sre-rag
kubectl describe certificate sre-rag-tls -n sre-rag
```
Verifique as condições: `Ready: False`, mensagens de erro em `Challenges` ou `Orders`.

### 2. Validar data de expiração no endpoint ativo
```bash
echo | openssl s_client -servername api.sre-rag.local -connect localhost:443 2>/dev/null | openssl x509 -noout -dates -issuer
```

### 3. Verificar logs do cert-manager
```bash
kubectl logs -n cert-manager -l app=cert-manager --tail=100
```
Procure por: erros de autenticação ACME HTTP-01/DNS-01, rate-limiting do Let's Encrypt ou ClusterIssuer mal configurado.

## Mitigação

### 1. Forçar renovação imediata do cert-manager
Acione a renovação manual sem interromper o serviço:
```bash
kubectl annotate certificate sre-rag-tls cert-manager.io/renew="true" --overwrite -n sre-rag
```

### 2. Verificar status do ClusterIssuer
```bash
kubectl get clusterissuer -o wide
kubectl describe clusterissuer letsencrypt-prod
```
Se houver falha de rota HTTP-01 no Ingress, verifique se a regra `/.well-known/acme-challenge` está liberada no Ingress Controller.

> ⚠️ **Anti-Pattern**: Deletar o Secret TLS diretamente antes da emissão do novo certificado provoca indisponibilidade imediata do HTTPS para todos os usuários.

## Resolução

1. Confirme que o certificado foi emitido com sucesso:
```bash
kubectl get certificate sre-rag-tls -n sre-rag -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'
```
2. Valide que a nova data de validade é superior a 30 dias:
```bash
echo | openssl s_client -servername api.sre-rag.local -connect localhost:443 2>/dev/null | openssl x509 -noout -enddate
```

## Pós-Incidente

- [ ] Ajustar o parâmetro `renewBefore` no recurso `Certificate` para renovar com 30 dias de antecedência (default padrão).
- [ ] Configurar alertas no Alertmanager com limiares em 30d (Info), 14d (Warning) e 48h (Critical).
