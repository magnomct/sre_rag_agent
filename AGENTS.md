# Diretrizes e Regras de Desenvolvimento (SRE Incident Lab)

## 1. Validação de Sintaxe Frontend Obrigatória
- Sempre que modificar arquivos JavaScript (`app/static/js/dashboard.js` ou outros scripts), **valide a sintaxe imediatamente** usando `node -c <caminho_do_arquivo>` antes de finalizar a tarefa.
- Erros de sintaxe em scripts principais quebram silenciosamente os event listeners e a navegação por abas (`switchDashboardTab`) no navegador.

## 2. Escopo Estrito de Alterações de Interface
- Ao trabalhar em melhorias de interface, traduções (i18n), layouts ou textos, **limite as alterações estritamente aos arquivos de frontend** (`app/templates/dashboard.html`, `app/static/js/dashboard.js`, CSS e documentação).
- **Não crie scripts de teste de rotas backend** e **não altere arquivos de configuração de ambiente** (`.env`) a menos que explicitamente solicitado.

## 3. Gerenciamento de Dependências e Disco (WSL / Local)
- No ambiente local/WSL sem GPUs dedicadas, **evite instalar o pacote padrão do PyTorch**, pois ele baixa bibliotecas CUDA/cuDNN desnecessárias que inflam o `.venv` para ~6 GB.
- Sempre instale o wheel oficial de CPU:
  `pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu`
- Limpe rotineiramente os caches de build e downloads (`pip cache purge`, `.pytest_cache`, `__pycache__`) e remova scripts utilitários temporários para preservar espaço em disco.

## 4. Modo Autônomo e Apresentação de Resultados
- Quando o usuário ativar o modo `/goal` ou orientar para atuar de forma autônoma ("sem confirmar os tasks"), execute todas as inspeções e edições necessárias sem pedir confirmações passo a passo.
- Apresente um resumo claro e o diff final das alterações ao concluir a meta.

## 5. Segurança e Rate Limiting (v3.4)
- **Security Headers obrigatórios**: Todo middleware de segurança (`security_headers_middleware`) deve ser registrado **antes** do `metrics_middleware` em `app/main.py`. No FastAPI, middlewares são executados na ordem inversa do registro, portanto o security_headers_middleware registrado antes executa por último — garantindo que headers defensivos sejam injetados em todas as respostas, inclusive as geradas pelo chaos monkey.
- **Rate Limiting**: Ao adicionar novos endpoints custosos (CPU-bound ou I/O intensivo), aplique sempre o decorator `@limiter.limit("N/minute")` do `slowapi`. Consulte o endpoint `/api/v1/query` como referência.
- **CSP e inline scripts**: A política de `Content-Security-Policy` incluída na v3.4 usa `'unsafe-inline'` para scripts e estilos por compatibilidade com o dashboard vanilla JS. Em versões futuras com módulos ES (ESM), essa concessão deve ser removida via hash de conteúdo (`'sha256-...'`).

## 6. Pydantic e Configurações (v3.4)
- **Nunca use `class Config:` interno**: Toda nova `BaseSettings` deve usar `model_config = SettingsConfigDict(...)`. A sintaxe da `class Config` foi depreciada no Pydantic V2 e removida no V3.
- **Parâmetro `extra="ignore"`**: Sempre configure `extra="ignore"` no `SettingsConfigDict` para que variáveis de ambiente não mapeadas não causem falha de startup em containers que herdam variáveis do host ou do runtime de Kubernetes.

## 7. Health Checks e Connection Pools (v3.4)
- **Cache TTL obrigatório**: Qualquer novo método de verificação de dependência (`check_*`) em `app/healthcheck.py` deve implementar cache TTL de no mínimo 5s antes de abrir conexões externas. Isso previne connection storms causados pelas probes do kubelet sob carga.
- **Latência real**: Nunca retorne valores hardcoded como `"latency_ms": 0`. Meça sempre o round-trip real com `time.time()` antes e após a operação de saúde.

## 8. Agente Autônomo de Auditoria, Segurança & Performance (v3.5)
- **Execução Contínua**: O agente autônomo `scripts/test_agent.py` deve ser executado para auditar a conformidade de segurança e estabilidade de performance após qualquer alteração em endpoints, middlewares, banco de dados ou configurações:
  ```bash
  PYTHONPATH=app ./app/.venv/bin/python3 scripts/test_agent.py
  # ou via Makefile:
  make test-audit
  ```
- **Documentação Viva e Rastreabilidade**: O agente documenta automaticamente cada teste adicionado no relatório [`docs/SECURITY_PERF_TEST_REPORT.md`](docs/SECURITY_PERF_TEST_REPORT.md).
- **Adição de Novos Testes**:
  - Para testes de segurança: criar métodos `audit_<feature>()` no `SRETestAgent` registrando um `AuditResult` com categoria `"Security"`, threshold esperado e diagnóstico de mitigação.
  - Para testes de performance: criar métodos `benchmark_<feature>()` no `SRETestAgent` registrando um `AuditResult` com categoria `"Performance"`, percentis (P50, P90, P95, P99) e latência em milissegundos.
  - Nenhum endpoint novo deve entrar em produção sem cobertura correspondente no agente de testes.

## 9. Agente SRE Autônomo com Ciclo OODA, Busca Híbrida e Chaos Real (v4.0)
- **Ciclo OODA Formal**: Qualquer agente ou workflow de resolução autônoma de incidentes deve ser implementado no pacote `app/agent/` respeitando os 4 estágios formais (*Observe, Orient, Decide, Act*). Não execute ações de mitigação na infraestrutura sem antes consultar a telemetria ativa (`query_prometheus`, `get_k8s_events`) e correlacionar os sintomas com runbooks validados (`search_runbooks`).
- **Salvaguardas de Autonomia (Human-in-the-Loop)**: Mantenha por padrão `auto_mitigate: False` para diagnósticos interativos no War Room, permitindo que operadores humanos aprovem planos de remediação recomendados antes da aplicação em produção.
- **Busca Híbrida 3-Stage**: Para recuperação de documentação e runbooks técnicos em `app/rag/vector_store.py`, combine sempre busca densa (pgvector HNSW) com busca esparsa léxica (BM25Okapi) unificadas via Reciprocal Rank Fusion (RRF, $k=60$) e cross-encoder re-ranking (FlashRank). Nunca utilize busca puramente vetorial para incidentes com códigos de erro exatos (`exit code 137`, `OOMKilled`, sinais POSIX).
- **Dead Man's Switch Obrigatório em Chaos Engineering**: Todo experimento de injeção de falhas no nível de kernel ou rede em `app/chaos_real.py` deve conter um temporizador de reversão automática (Dead Man's Switch de 60 segundos), garantindo recuperação determinística caso ocorra perda de conectividade com o nó ou operador.
- **Rastreamento com OpenTelemetry**: Spans distribuídos devem ser criados com recursos semânticos padronizados (`service.name`, `service.version`) e todo log gerado pelo `structlog` deve ter o contexto de `trace_id` e `span_id` injetado pelo processador `inject_otel_context`.
- **Validação DevSecOps**: Manter conformidade estrita com o perfil **Pod Security Standards (PSS) Restricted** nos Helm charts (`readOnlyRootFilesystem: true`, não-root, drop de capabilities) e garantir **0 vulnerabilidades HIGH ou CRITICAL** nos escaneamentos do Trivy.
