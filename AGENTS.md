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
