# Plano de Testes e Validação do Ambiente (v4.0)

> **Status:** Preparado e Pronto para Execução  
> **Versão Alvo:** SRE RAG Agent v4.0  
> **Data de Planejamento:** 21/10/2026  
> **Ambiente de Testes:** Local (WSL2 Ubuntu 24.04 / Docker Engine / Cluster Kind / PostgreSQL 15 pgvector)  
> **Regra de Execução:** *Planejado antecipadamente — aguardar autorização antes de iniciar as baterias de teste.*

---

## 1. Visão Geral e Objetivos de Validação

O objetivo deste plano é validar de forma metódica e reproduzível todos os componentes arquiteturais, camadas de resiliência, pipeline de busca híbrida, orquestração de caos no kernel e experiência do operador na versão **v4.0** do **SRE RAG Agent**.

### Escopo das Baterias de Teste:
1. **Infraestrutura & Containers:** Docker Compose multi-rede (`proxy_net` e `backend_net`), PostgreSQL 15 com extensão `pgvector`, Redis 7 e Nginx Reverse Proxy.
2. **Camada de Dados & pgvector:** Migrações Alembic, índices vetoriais HNSW e persistência de histórico.
3. **Pipeline de Busca Híbrida & FlashRank:** Recuperação densa (embeddings) + esparsa (BM25), fusão RRF ($k=60$) e re-ranking semântico com Cross-Encoder.
4. **Agente SRE Autônomo (OODA Loop):** Tool Calling assíncrono sandboxed, raciocínio reativo e streaming SSE via Web Terminal.
5. **Chaos Engineering Real (Kernel & Kind):** Injeção de estresse de memória (OOM Killer via `stress-ng`), cgroup CPU throttling, latência com `tc netem` e Dead Man's Switch (60s).
6. **War Room & Web Terminal:** Resolução na 1ª tentativa de comando, ausência de stack overflow, execução de comandos diagnósticos e badges v4.0.
7. **Observabilidade Tridimensional:** Métricas RED no Prometheus, logs correlacionados com `trace_id`/`span_id` no `structlog` e spans OpenTelemetry.
8. **DevSecOps & Hardening:** PSS Restricted no Helm, NetworkPolicies Zero-Trust e escaneamento de vulnerabilidades com Trivy.

---

## 2. Matriz de Pré-requisitos e Ferramentas

| Ferramenta | Versão Recomendada | Finalidade na Validação |
|---|---|---|
| **Docker Engine** | 24.0+ | Orquestração dos containers de aplicação, banco e proxy |
| **Docker Compose** | v2.20+ | Gerenciamento da pilha local multi-serviço |
| **Kind** / **Kubectl** | v0.22+ / v1.29+ | Cluster local Kubernetes para injeção de caos real e PSS |
| **Helm** | v3.14+ | Validação dos templates de charts, PSS e NetworkPolicies |
| **Python** | 3.12+ (venv ativo) | Execução do backend FastAPI e suite Pytest |
| **Trivy** | v0.50+ | Auditoria estática de vulnerabilidades e CVEs da imagem Docker |
| **Curl / JQ** | Nativos Linux | Inspeção rápida de endpoints HTTP, métricas e payloads JSON |

---

## 3. Roteiro de Testes Passo a Passo (Baterias 1 a 8)

### Bateria 1: Inicialização da Infraestrutura e Redes Isoladas
* **Objetivo:** Garantir que todos os containers subam saudáveis e que as redes de segurança estejam operacionais.
* **Comandos de Validação:**
  ```bash
  # 1.1 Iniciar a pilha local
  docker compose -f docker-compose.yml up -d

  # 1.2 Verificar status de saúde dos containers
  docker compose ps

  # 1.3 Validar isolamento da rede backend_net (deve ser internal: true)
  docker network inspect sre_rag_agent_backend_net | jq '.[0].Internal'
  # Esperado: true
  ```
* **Critério de Sucesso:** Containers `api`, `nginx_proxy`, `postgresql` e `redis` em estado `healthy` / `running`.

---

### Bateria 2: Banco de Dados, Migrações e pgvector HNSW
* **Objetivo:** Verificar se as migrações SQLAlchemy/Alembic foram aplicadas e se a extensão `pgvector` e o índice HNSW estão ativos.
* **Comandos de Validação:**
  ```bash
  # 2.1 Verificar extensão pgvector no PostgreSQL
  docker exec -it sre-rag-postgres psql -U app -d sre_db -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
  # Esperado: 1 linha (vector | 0.7.x ou superior)

  # 2.2 Verificar status das migrações Alembic
  PYTHONPATH=app ./app/.venv/bin/alembic current

  # 2.3 Verificar índice HNSW na tabela de vetores
  docker exec -it sre-rag-postgres psql -U app -d sre_db -c "\d sre_knowledge_vectors"
  # Esperado: Índice usando hnsw (embedding vector_cosine_ops)
  ```
* **Critério de Sucesso:** Extensão `vector` carregada e tabelas criadas sem erros de migração.

---

### Bateria 3: Endpoints de Saúde e Telemetria Golden Signals
* **Objetivo:** Validar a resposta dos healthchecks e exportação de métricas.
* **Comandos de Validação:**
  ```bash
  # 3.1 Health check da API
  curl -s http://localhost:8000/health | jq .
  # Esperado: {"status":"healthy","database":"connected","redis":"connected","version":"4.0"}

  # 3.2 Endpoint de métricas Prometheus
  curl -s http://localhost:8000/metrics | grep -E "http_requests_total|sre_slo_availability"

  # 3.3 Overview de telemetria e burn rate do Error Budget
  curl -s http://localhost:8000/api/v1/telemetry/overview | jq .
  # Esperado: Payload com latency_p99, error_rate, active_experiments e budget_burn_rate
  ```
* **Critério de Sucesso:** HTTP 200 em todos os endpoints com versão `4.0` refletida.

---

### Bateria 4: Busca Híbrida (Dense + BM25) com Re-ranking FlashRank
* **Objetivo:** Testar a recuperação de conhecimento combinando vetores densos e léxicos, medindo a latência do Cross-Encoder.
* **Comandos de Validação:**
  ```bash
  # 4.1 Consulta técnica com token exato (CrashLoopBackOff)
  curl -s -X POST http://localhost:8000/api/v1/query \
    -H "Content-Type: application/json" \
    -d '{"query": "Como resolver erro CrashLoopBackOff de Secret ausente?"}' | jq .

  # 4.2 Consulta semântica de latência
  curl -s -X POST http://localhost:8000/api/v1/query \
    -H "Content-Type: application/json" \
    -d '{"query": "Queda brusca de performance e pool de conexoes esgotado"}' | jq .
  ```
* **Critério de Sucesso:** Resultados com scores de fusão RRF e re-ranking semântico priorizando os runbooks exatos em menos de 100ms.

---

### Bateria 5: Agente SRE Autônomo (Ciclo OODA e Tool Calling)
* **Objetivo:** Avaliar o raciocínio em tempo real do agente SRE inspecionando o ambiente via loop OODA.
* **Comandos de Validação:**
  ```bash
  # 5.1 Disparo de investigação autônoma
  curl -s -X POST http://localhost:8000/api/v1/agent/diagnose \
    -H "Content-Type: application/json" \
    -d '{"query": "Inspecione a saude do cluster e anomalias de probes", "auto_mitigate": false}' | jq .

  # 5.2 Validação do stream de raciocínio SSE (em terminal separado)
  curl -N http://localhost:8000/api/v1/events/stream
  # Esperado: Eventos SSE com phases OBSERVE, ORIENT, DECIDE, ACT
  ```
* **Critério de Sucesso:** O agente executa as ferramentas com segurança (`query_prometheus`, `get_k8s_events`, `search_runbooks`) e emite o relatório de causa-raiz.

---

### Bateria 6: Validação da War Room & Web Terminal (Testes das Correções)
* **Objetivo:** Comprovar a eliminação do stack overflow e a resolução de comandos na primeira submissão.
* **Procedimento de Teste:**
  1. Acessar a interface web: `http://localhost:8000/` ou `http://localhost:80/`.
  2. Clicar na aba **💻 War Room (Terminal)**.
  3. Clicar em **🟢 Fácil** para sortear um cenário (ex: `missing-config-secret`).
  4. Clicar no botão **💡 Dica (0/2)** e verificar:
     - Dica textual é impressa sem erros.
     - Não ocorre a mensagem `[ERRO] Maximum call stack size exceeded`.
     - O terminal ancora suavemente na última linha.
  5. Digitar o comando exato no terminal e pressionar Enter:
     ```bash
     kubectl create secret generic sre-rag-secrets --from-literal=OPENAI_API_KEY=mock-key --from-literal=DATABASE_URL=postgres://app:secret@postgresql:5432/sre_db
     ```
  6. **Verificação Crucial:** O incidente deve ser reconhecido como resolvido `[SUCCESS]` **logo na primeira tentativa**, sem emitir `> Dica do Sistema: undefined`.
  7. Testar comando diagnóstico:
     ```bash
     kubectl get pods
     ```
     - Esperado: Tabela realista de pods em execução sem `NameError`.
  8. Verificar badges de versão no rodapé do Dashboard e no Board de Histórico: **devem exibir `v4.0`**.

---

### Bateria 7: Chaos Engineering Real no Kernel & Kubernetes
* **Objetivo:** Testar a injeção controlada de falhas no cluster Kind e acionamento do Dead Man's Switch.
* **Comandos de Validação:**
  ```bash
  # 7.1 Injetar estresse de CPU (cgroup throttling)
  curl -s -X POST http://localhost:8000/api/v1/chaos/inject \
    -H "Content-Type: application/json" \
    -d '{"fault_type": "CPU_THROTTLE", "duration_seconds": 60}' | jq .

  # 7.2 Injetar pressão de memória simulando OOM Killer
  curl -s -X POST http://localhost:8000/api/v1/chaos/inject \
    -H "Content-Type: application/json" \
    -d '{"fault_type": "MEMORY_PRESSURE", "duration_seconds": 30}' | jq .

  # 7.3 Listar experimentos ativos
  curl -s http://localhost:8000/api/v1/chaos/experiments | jq .

  # 7.4 Aguardar 60 segundos e constatar a reversão automática (Dead Man Switch)
  sleep 65
  curl -s http://localhost:8000/api/v1/chaos/experiments | jq .
  # Esperado: [] (vazio, revertido com segurança)
  ```
* **Critério de Sucesso:** Falhas injetadas com blast radius controlado e reversão automática comprovada.

---

### Bateria 8: Segurança DevSecOps & Varredura Trivy
* **Objetivo:** Assegurar conformidade com políticas corporativas de segurança e ausência de CVEs críticas.
* **Comandos de Validação:**
  ```bash
  # 8.1 Validação de manifestos Helm com PSS Restricted
  helm template sre-rag helm/sre-rag/ | grep -A 8 "securityContext:"

  # 8.2 Escaneamento de vulnerabilidades da imagem Docker com Trivy
  trivy image --severity HIGH,CRITICAL carlosmagnogcs/sre-rag-api:4.0

  # 8.3 Execução do script automatizado de conformidade v4.0
  bash scripts/verify_v4.0.sh
  ```
* **Critério de Sucesso:** Zero vulnerabilidades críticas impeditivas e `verify_v4.0.sh` aprovado com 15/15 critérios atendidos.

---

## 4. Tabela de Verificação e Checklist de Execução

| # | Bateria de Teste | Componente Alvo | Resultado Esperado | Status |
|---|---|---|---|---|
| 1 | Orquestração Docker | `docker compose up -d` | 4 containers healthy, redes isoladas | ⏳ Pronto |
| 2 | Banco & Migrações | PostgreSQL + `pgvector` | Extensão ativa, Alembic em dia, índice HNSW | ⏳ Pronto |
| 3 | Healthchecks & Métricas | `/health`, `/metrics` | HTTP 200, RED metrics ativas, versão 4.0 | ⏳ Pronto |
| 4 | Busca Híbrida & RRF | `vector_store.py` | Recuperação dense+sparse + FlashRank < 30ms | ⏳ Pronto |
| 5 | Agente SRE OODA | `sre_agent.py` | Tool calling seguro, streaming SSE auditável | ⏳ Pronto |
| 6 | Terminal War Room | `dashboard.js` | Resolução no 1º envio, sem recursão, badges v4.0 | ⏳ Pronto |
| 7 | Chaos Real & Dead Man | `chaos_real.py` | OOM/CPU throttling com expiração em 60s | ⏳ Pronto |
| 8 | DevSecOps & Trivy | `sre-rag-api:4.0` | Scan Trivy aprovado, PSS Restricted validado | ⏳ Pronto |

---

## 5. Instruções Finais para Amanhã

> [!IMPORTANT]
> **Ordem de Execução Recomendada:**
> 1. Executar a **Bateria 1** e a **Bateria 2** para assegurar a fundação de infraestrutura e dados.
> 2. Abrir o navegador em `http://localhost:8000/` e validar interativamente a **Bateria 6 (War Room)** confirmando que o terminal aceita os comandos no primeiro envio.
> 3. Disparar a **Bateria 4 (RAG)** e a **Bateria 5 (Agente OODA)** para checar a inteligência autônoma.
> 4. Concluir com a **Bateria 7 (Caos Real)** e o scan do **Trivy (Bateria 8)**.
