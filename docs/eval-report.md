# 📊 Relatório de Avaliação SRE-Eval: RAG & Decisão Operacional

**Data da Avaliação:** 2026-10-26 23:03:34
**Modelo de Embeddings:** `all-MiniLM-L6-v2` (384-d)
**Total de Casos Avaliados:** `10`
**Classificação Geral:** **🥇 A (Aprovado)**

---

## 1. Resumo dos Indicadores Chave de Desempenho (KPIs)

| Métrica de Avaliação | Valor Médio | Meta de Confiabilidade | Status |
|---|---|---|---|
| **Hit Rate@K** (Relevância de Topo) | **100.0%** | ≥ 90.0% | ✅ Superada |
| **MRR** (Mean Reciprocal Rank) | **1.000** | ≥ 0.700 | ✅ Superada |
| **Context Precision** | **70.0%** | ≥ 50.0% | ✅ Superada |
| **Context Recall** | **75.0%** | ≥ 80.0% | ⚠️ Atenção |
| **Keyword Diagnostic Coverage** | **49.8%** | ≥ 75.0% | ⚠️ Atenção |
| **Action Safety Score** | **100.0%** | ≥ 95.0% | ✅ Superada |
| **SRE Composite Score** | **82.4/100** | ≥ 80.0/100 | ✅ Aprovado |

---

## 2. Detalhamento por Caso de Teste

| ID | Cenário / Tópico | Hit? | MRR | Precision | Keywords | Safety | Score | Top Fonte Recuperada |
|---|---|---|---|---|---|---|---|---|
| `tc-001-error-rate` | `high-error-rate` | ✅ | `1.00` | `40%` | `75%` | `100%` | **`91.2`** | `incident-response.md` |
| `tc-002-high-latency` | `high-latency` | ✅ | `1.00` | `80%` | `20%` | `100%` | **`72.0`** | `2026-09-20-high-latency-slow-query.md` |
| `tc-003-crashloop` | `crashloopbackoff` | ✅ | `1.00` | `100%` | `80%` | `100%` | **`93.0`** | `2026-09-02-api-crashloop-missing-env.md` |
| `tc-004-tls-expiring` | `tls-expiring` | ✅ | `1.00` | `100%` | `25%` | `100%` | **`73.8`** | `tls-expiring.md` |
| `tc-005-disk-pressure` | `disk-pressure` | ✅ | `1.00` | `100%` | `60%` | `100%` | **`86.0`** | `disk-pressure.md` |
| `tc-006-redis-exhausted` | `redis-exhausted` | ✅ | `1.00` | `100%` | `75%` | `100%` | **`91.2`** | `redis-exhausted.md` |
| `tc-007-oom-kill` | `oom-kill` | ✅ | `1.00` | `40%` | `40%` | `100%` | **`79.0`** | `oom-kill.md` |
| `tc-008-dns-failure` | `dns-failure` | ✅ | `1.00` | `60%` | `0%` | `100%` | **`65.0`** | `dns-failure.md` |
| `tc-009-slo-mwmbr` | `tc-009-slo-mwmbr` | ✅ | `1.00` | `40%` | `83%` | `100%` | **`94.2`** | `slo.md` |
| `tc-010-postmortem-culture` | `tc-010-postmortem-culture` | ✅ | `1.00` | `40%` | `40%` | `100%` | **`79.0`** | `incident-response.md` |

---

## 3. Conclusão da Avaliação Arquitetural
- O motor de recuperação semântica sobre os runbooks e postmortems recém-criados apresenta excelente capacidade de ranquear as mitigações corretas em 1º lugar.
- A síntese SRE protege o operador contra ações destrutivas (reiniciar pods ou apagar secrets) ao ressaltar advertências de anti-patterns explicitamente.
- O framework de avaliação agora pode ser executado a qualquer momento via `make eval` no pipeline de CI/CD para impedir regressões cognitivas no agente.
