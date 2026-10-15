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
