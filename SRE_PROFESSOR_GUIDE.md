# 🧑‍🏫 Guia de Estudo: Laboratório de Produção SRE & DevOps (v4.0)

Olá, engenheiro! Seja muito bem-vindo ao nosso **Guia Definitivo de Estudos e Testes de SRE**.

Este documento foi criado como uma aula particular e um livro de referência de bolso. Nele, explico detalhadamente cada arquitetura, cada decisão técnica e o **porquê** de cada linha de código que implementamos neste projeto.

Lembre-se do mantra fundamental de SRE:
> *"A esperança não é uma estratégia de confiabilidade."* — Livro de SRE do Google.  
> Ferramentas e tecnologias mudam; a disciplina de **redução de MTTD/MTTR, isolamento de falhas e automação resiliente** permanece.

---

## 📑 Índice do Guia

1. [A Filosofia SRE: Por que construímos este Laboratório?](#1-a-filosofia-sre-por-que-construímos-este-laboratório)
2. [O Dashboard de Simulação de Incidentes v3.2](#2-o-dashboard-de-simulação-de-incidentes-v32)
3. [Chaos Monkey 2.0: Engenharia do Caos de Produção (`app/chaos.py`)](#3-chaos-monkey-20-engenharia-do-caos-de-produção-appchaospy)
4. [O Motor RAG Semântico para Runbooks (`app/rag/`)](#4-o-motor-rag-semântico-para-runbooks-apprag)
5. [Segurança em Produção: O Risco do Swagger Exposto](#5-segurança-em-produção-o-risco-do-swagger-exposto)
6. [Infraestrutura Cloud & Kubernetes (`helm/`, `terraform-oci/`)](#6-infraestrutura-cloud--kubernetes-helm-terraform-oci)
7. [Roteiro Prático de Estudos & Comandos de Laboratório](#7-roteiro-prático-de-estudos--comandos-de-laboratório)
8. [War Room (Terminal Seguro) e Dificuldades Dinâmicas (v3.2)](#8-war-room-terminal-seguro-e-dificuldades-dinâmicas-v32)
9. [Arquitetura de Contêineres Segura e Otimização Docker (v3.2)](#9-arquitetura-de-contêineres-segura-e-otimização-docker-v32)
10. [O Catálogo de 16 Cenários, Runbooks em 5 Fases e a Base de Conceitos SRE (v3.3)](#10-o-catálogo-de-16-cenários-runbooks-em-5-fases-e-a-base-de-conceitos-sre-v33)
11. [Quick Wins & Hardening — A Fundação Técnica da v3.5](#11-quick-wins--hardening--a-fundação-técnica-da-v34)
12. [A Era dos Agentes Autônomos, Busca Híbrida e Chaos Real no Kernel (v4.0)](#12-a-era-dos-agentes-autônomos-busca-híbrida-e-chaos-real-no-kernel-v40)
13. [Conclusão do Professor](#13-conclusão-do-professor)

---

## 1. A Filosofia SRE: Por que construímos este Laboratório?

Em ambientes tradicionais de TI, os incidentes acontecem de surpresa, a equipe entra em pânico, o troubleshooting é caótico e o cliente final sofre.

Na Engenharia de Confiabilidade de Sites (SRE), nós adotamos uma postura ativa:
- **Game Days regulares:** Exercícios controlados onde injetamos falhas de propósito para testar a prontidão da equipe e a acurácia dos runbooks.
- **Métricas Chave de Resposta:**
  - **MTTD (*Mean Time To Detect*):** O tempo decorrido entre a falha começar e o sistema de alerta avisar o engenheiro on-call.
  - **MTTR (*Mean Time To Recovery*):** O tempo decorrido entre a detecção do problema e o restabelecimento do serviço em produção.
- **Postmortems sem Culpa (*Blameless Postmortems*):** Quando um incidente acontece, não procuramos pessoas culpadas; procuramos causas-raiz sistêmicas usando a técnica dos **5 Porquês**.

Este laboratório foi construído para que você pratique essas habilidades de forma segura na sua própria máquina, sem arriscar derrubar sistemas de clientes.

---

## 2. O Dashboard de Simulação de Incidentes v3.2

A interface web (`/dashboard`) é o centro de comando do nosso laboratório. Ela não é um mock estático: ela é acoplada a um motor de simulação assíncrono real no backend.

### 2.1 A Máquina de Estados (`app/incidents.py`)
No backend, o `IncidentSimulationEngine` implementa uma máquina de estados finitos:

```
[ Inativo ] ──(Iniciar)──▶ [ RUNNING ] ──(Delay MTTD)──▶ [ DETECTED ] ──▶ [ INVESTIGATING ] ──(Solução Correta)──▶ [ RESOLVED ]
```

- **Por que existe o `detection_delay_seconds`?**  
  Em produção, um alerta do Prometheus não dispara instantaneamente no primeiro segundo de erro. Ele precisa aguardar a janela de amostragem (`evaluation_interval` e regra `for: 1m` do Alertmanager) para evitar alertas falsos positivos gerados por instabilidades passageiras. Nosso motor simula exatamente esse atraso realista!
- **Embaralhamento Aleatório de Soluções:**  
  A cada nova simulação, as 4 opções de mitigação são embaralhadas aleatoriamente (`random.shuffle`). Isso impede que o estudante responda por memória visual mecânica (ex: "é sempre a opção B"), forçando a leitura atenta do diagnóstico e do runbook.

### 2.2 Arquitetura de Abas & Redução da Carga Cognitiva
Na versão 2.1, separamos o painel em duas abas principais:
1. `🎯 Simulação & Chaos Lab`: Área cirúrgica de operação. Contém o status em tempo real, sintomas do incidente, terminal do Chaos Monkey e opções de remediação.
2. `📊 Painel de Histórico & Métricas`: Área analítica. Contém KPIs agregados (MTTD, MTTR, Assertividade), gráfico Sparkline SVG de tendências e tabela de histórico postmortem.

**Por que essa decisão é importante para SRE?**  
Durante uma crise operacional (on-call de madrugada), sobrecarga de informação causa estresse e erros de julgamento. O operador precisa enxergar exclusivamente o incidente ativo, os logs e o botão de mitigação. A análise histórica de métricas é uma atividade de postmortem, que deve ficar em seu próprio espaço.

A navegação utiliza **Hash Routing** (`#simulation` / `#history`) com persistência instantânea no navegador, sem causar recarregamento de página.

### 2.3 Suporte Bilíngue Nativo (pt-BR / en-US)
SREs frequentemente trabalham em equipes multinacionais que operam em modelo *follow-the-sun* (passagem de bastão entre fusos horários). Ter a interface e os runbooks disponíveis tanto em Português quanto em Inglês é um requisito de plataformas corporativas modernas.  
O seletor no cabeçalho armazena a preferência em `localStorage` e atualiza instantaneamente todos os 8 cenários, diagnósticos de IA e métricas.

### 2.4 Tipografia e Acessibilidade Visual (v3.2.2)
Telas com micro-fontes (< 11px) causam cansaço visual e aumentam o risco de leitura incorreta de parâmetros críticos (ex: comandos `kubectl` e IDs de pods). A versão 2.1.2 elevou todas as fontes para a faixa de `0.80rem`–`0.96rem`, expandiu o espaçamento de linhas para `1.6` e corrigiu o vazamento horizontal de gráficos SVG.

---

## 3. Chaos Monkey 2.0: Engenharia do Caos de Produção (`app/chaos.py`)

A engenharia do caos não consiste em quebrar coisas aleatoriamente sem controle. O princípio número 1 do Chaos Engineering é o **Raio de Explosão Controlado (*Blast Radius*)**.

### 3.1 O Gerenciador `ChaosMonkeyManager`
Na versão anterior, tínhamos apenas um flag global rudimentar. Na v3.2, implementamos um gerenciador completo com as seguintes características:

- **Thread-Safety com Locks (`threading.Lock`):** O FastAPI atende requisições de forma concorrente em threads assíncronas. O uso de locks garante que ler ou modificar o estado do caos não gere condições de corrida (*race conditions*).
- **Auto-Reversão com Dead Man's Switch (`threading.Timer`):**  
  Toda injeção de caos possui uma duração configurável (ex: 60 segundos padrão). Ao término desse tempo, o timer dispara automaticamente a restauração do sistema (`deactivate()`).  
  *Por que isso é vital?* Se o engenheiro fechar a janela do navegador ou perder a conexão durante o teste, o sistema não ficará quebrado indefinidamente!
- **Probabilidade de Falha Configurável (`failure_rate`):**  
  Permite injetar falhas probabilísticas (ex: 50% das requisições falham). Isso simula cenários altamente traiçoeiros como *packet loss*, conexões instáveis e *flapping pods*.
- **Filtro de Endpoints Alvo (`target_endpoints`):**  
  Você pode direcionar o caos especificamente para uma rota (ex: `/api/v1/infer*`) sem atingir o restante da aplicação.

### 3.2 O Middleware de Isolamento do Plano de Controle
O middleware ASGI em `app/chaos.py` inspeciona cada requisição HTTP que chega à API.

**A Regra de Ouro do SRE:**  
> *"Nunca quebre o termômetro enquanto você aquece o paciente."*

Se o middleware retornasse HTTP 500 para **todas** as rotas indiscriminadamente:
- O endpoint de métricas do Prometheus (`/metrics`) falharia, e você não saberia que a taxa de erros subiu.
- As probes do Kubernetes (`/healthz` e `/ready`) falhariam, e o Kubelet mataria o pod antes que você pudesse testar o incidente.
- O próprio botão de desligar o Chaos Monkey no Dashboard falharia!

Por isso, nosso middleware contém uma lista expressa de exclusão:
```python
SAFE_PREFIXES = (
    "/healthz", "/ready", "/metrics", "/dashboard",
    "/board", "/static", "/api/v1/chaos",
    "/api/v1/incidents", "/api/v1/history"
)
```
Se a rota for de monitoramento ou controle, ela **sempre** passa limpa. Se for a API de inferência de negócio, o erro 500 é injetado com precisão cirúrgica.

### 3.3 Terminal de Auditoria em Tempo Real & Buffer Circular
Para evitar consumo descontrolado de memória RAM (Memory Leak), o histórico de logs do terminal utiliza uma estrutura de buffer circular com capacidade para 100 mensagens:
```python
self._audit_log = collections.deque(maxlen=100)
```
Cada evento registra timestamp ISO, tipo de ação (`ACTIVATED`, `INJECTED_500`, `DEACTIVATED`), endpoint afetado e IP de origem. A interface faz polling e renderiza esses eventos com estilo de terminal Unix no dashboard.

---

## 4. O Motor RAG Semântico para Runbooks (`app/rag/`)

Quando um alarme de PagerDuty toca, o maior desperdício de tempo do engenheiro é procurar o runbook certo em wikis desatualizadas.

### 4.1 Do "Grep" à Busca Semântica Vetorial
- **O problema da busca por texto puro (Lexical Search / Grep):**  
  Se o engenheiro busca por *"banco travando conexões"* e o runbook oficial foi intitulado *"PostgreSQL Connection Pool Saturation"*, a busca tradicional retorna zero resultados.
- **A solução com Embeddings Vetoriais:**  
  Utilizamos o modelo `sentence-transformers` (`all-MiniLM-L6-v2`) que mapeia frases em um espaço vetorial de 384 dimensões. Frases com o mesmo significado semântico ficam matematicamente próximas no espaço vetorial, permitindo que a busca encontre o documento correto instantaneamente.

### 4.2 Cache Persistente & Resiliência Offline
Para garantir inicialização ultrarrápida e independência de dependências externas, o indexador processa todos os runbooks em markdown (`docs/runbooks/`) e salva o índice vetorial compilado em disco (`app/rag/index_store.json`).  
Dessa forma, mesmo que o Redis caia ou a máquina esteja sem conexão com a internet, o SRE RAG Agent inicializa em menos de 2 segundos e executa buscas em ~20 milissegundos.

### 4.3 O Framework de Avaliação SRE (`tests/eval/`)
Para garantir a confiabilidade das respostas da IA, desenvolvemos um benchmark automatizado que calcula 4 métricas científicas:
- **Hit Rate@K (100%):** O runbook ideal está contido nos top K resultados retornados.
- **MRR (*Mean Reciprocal Rank*, 0.925):** Mede a posição do resultado ideal (se estiver em 1º lugar ganha nota 1.0; se estiver em 2º lugar ganha 0.5).
- **Context Precision (70%):** Avalia a densidade de informação relevante no contexto recuperado.
- **Safety Score (100%):** Verifica se o agente nunca recomenda comandos perigosos ou destrutivos sem avisos de segurança explícitos.

---

## 5. Segurança em Produção: O Risco do Swagger Exposto

No ambiente corporativo, a documentação Swagger/OpenAPI interativa (`/docs` e `/redoc`) é uma das ferramentas preferidas de desenvolvedores durante a criação de APIs. Porém, em **produção**, ela representa uma grave vulnerabilidade de segurança (DevSecOps).

### 5.1 Por que o Swagger em Produção é Perigoso?
1. **Enumeração Completa de Superfície de Ataque:**  
   O Swagger entrega em formato JSON limpo todas as rotas da sua aplicação, incluindo endpoints administrativos ou experimentais que deveriam ser privados.
2. **Vazamento de Esquemas de Dados (*Data Schemas*):**  
   Os modelos Pydantic geram o schema exato das tabelas e tipos de dados aceitos, facilitando ataques de injeção de payload e bypass de validação.
3. **Facilitação de Ataques de Negação de Serviço (DoS):**  
   O botão "Try it out" permite que qualquer pessoa dispare requisições diretamente contra seus servidores de produção a partir do próprio navegador.

### 5.2 A Nossa Solução de Endurecimento (Hardening)
No arquivo `app/main.py`, condicionamos a ativação do Swagger estritamente ao ambiente:

```python
docs_url = "/docs" if settings.ENVIRONMENT == "development" else None
redoc_url = "/redoc" if settings.ENVIRONMENT == "development" else None
openapi_url = "/openapi.json" if settings.ENVIRONMENT == "development" else None

app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url
)
```

Além disso, removemos qualquer botão público de acesso ao Swagger no cabeçalho do Dashboard principal, garantindo que o acesso a essa ferramenta seja restrito a ambientes locais de desenvolvimento.

---

## 6. Infraestrutura Cloud & Kubernetes (`helm/`, `terraform-oci/`)

### 6.1 Ingress Controller vs LoadBalancer
- **LoadBalancer Cloud Tradicional:** Cria uma instância de Load Balancer gerenciado na nuvem para cada serviço do Kubernetes. Se você tiver 10 microsserviços, a nuvem cobrará por 10 endereços IP públicos e 10 instâncias de balanceador.
- **Ingress Controller (NGINX / Traefik):** Utiliza um único balanceador e IP público na borda do cluster, roteando o tráfego internamente com base no `Host` HTTP ou no caminho da URL (ex: `/api` vs `/dashboard`). Isso reduz os custos de infraestrutura em até 90%.

### 6.2 Probes de Liveness vs Readiness: Qual a diferença?
- **Liveness Probe (`/healthz`):** Pergunta: *"O processo da aplicação ainda está vivo?"*  
  Se falhar, o Kubelet mata o pod e cria um pod novo. Use para destravar aplicações em deadlock.
- **Readiness Probe (`/ready`):** Pergunta: *"O pod está pronto para receber tráfego de clientes agora?"*  
  Se falhar, o Kubernetes **não** mata o pod; ele apenas remove temporariamente o pod da rota do `Service`. É ideal para momentos em que a aplicação está ocupada aquecendo cache ou o banco de dados está sobrecarregado.

---

## 7. Roteiro Prático de Estudos & Comandos de Laboratório

Para tirar o máximo proveito deste repositório nos seus estudos, siga este roteiro prático:

### Passo 1: Subir o Laboratório Localmente
Abra o seu terminal no diretório do projeto e execute:
```bash
# Iniciar o servidor com reload automático
make dev
```
Acesse o dashboard pelo navegador:  
👉 **[http://localhost:8080/dashboard](http://localhost:8080/dashboard)**

### Passo 2: Executar um Incidente de Simulação
1. No menu lateral esquerdo, selecione um cenário (ex: `High Error Rate (HTTP 500)` ou `Redis Memory Exhaustion`).
2. Clique em **"Iniciar Simulação"**.
3. Observe o cronômetro correndo e a timeline evoluindo de `running` para `detected`.
4. Leia atentamente a descrição do problema, os sintomas e o runbook sugerido.
5. Selecione a opção de remediação correta e clique em **"Aplicar Resolução"**.
6. Vá para a aba **"📊 Painel de Histórico & Métricas"** e analise como o seu MTTR foi calculado e adicionado ao gráfico!

### Passo 3: Testar o Chaos Monkey via Interface e via Terminal
1. Na aba `🎯 Simulação & Chaos Lab`, localize o card do **Chaos Monkey**.
2. Clique no botão de alternância **"Ativar Chaos Monkey"**.
3. Acompanhe as mensagens coloridas sendo impressas ao vivo no **Terminal SRE de Auditoria**.
4. Em outro terminal, teste fazer uma requisição na API de inferência para ver o HTTP 500 sendo injetado:
   ```bash
   curl -i http://localhost:8080/api/v1/infer -H "Content-Type: application/json" -d '{"query":"teste"}'
   ```
5. Agora teste a rota de healthcheck e veja que ela continua respondendo com sucesso 200:
   ```bash
   curl -i http://localhost:8080/healthz
   ```
   *(Isso comprova o isolamento do plano de controle!)*
6. Desative o Chaos Monkey e veja o log `[DESATIVADO]` no terminal.

### Passo 4: Executar a Suíte Completa de Testes Automatizados
Para comprovar que o backend e os algoritmos estão 100% saudáveis:
```bash
make test
```
*Deverá passar 8/8 testes cobrindo ciclo de vida do caos, isolamento de middleware, máquina de estados de incidentes e busca vetorial.*

### Passo 5: Rodar a Avaliação de Precisão do RAG (Eval)
```bash
python3 tests/eval/run_eval.py
```
*Gera o relatório analítico detalhado em `docs/eval-report.md` com as métricas de Hit Rate e MRR.*

### Passo 6: Desligar o Laboratório de Forma Limpa
Quando terminar seus estudos do dia:
```bash
make clean
```
*(Ou encerre o processo do uvicorn pressionando `Ctrl + C` no terminal).*

---

---

## 8. War Room (Terminal Seguro) e Dificuldades Dinâmicas (v3.2)

A versão 3.0 transformou a forma como o laboratório opera com a adição do **War Room (Terminal)**.

### 8.1. O Desafio de Executar Comandos de Usuário (Evitando RCE)
Construir um laboratório onde o usuário pode digitar qualquer comando (`helm`, `kubectl`) na interface web apresenta um risco enorme de **Remote Code Execution (RCE)** se simplesmente passarmos a string para o SO host.
* Como resolvemos? O terminal do War Room é um simulador blindado (Mock). Quando o usuário digita o comando, o frontend envia a string para o backend, que apenas **compara com um gabarito estático** configurado no `incidents.py`. Nenhuma execução real no sistema operacional ocorre. Isso permite uma experiência 100% autêntica na UI, com 0% de risco para a infraestrutura.

### 8.2. Abas Independentes e Estado Local
Mantivemos o Quiz original na aba "Simulação" para quem prefere múltipla escolha, e criamos a aba "War Room" para a digitação de comandos. Para não perder o estado da simulação ao trocar de aba, o roteamento passou a ser manipulado no Client-Side via classes do DOM, e o histórico de cenários (para os botões `Próximo/Anterior`) é armazenado num array JavaScript. O Backend permanece *Stateless* e veloz.

### 8.3. Dicas com Penalidade de Score e Sem Repetição
Implementamos o conceito clássico de simulador: 
* Sorteio aleatório, mas agora ele lembra (no array local) dos IDs que já caíram e passa isso para a API via `?exclude=...`, **garantindo zero repetição** até esgotar todos os cenários daquela dificuldade.
* O botão "Dica" (-20 pontos) foi adicionado para guiar alunos iniciantes, balanceando desafio técnico com aprendizagem amigável.

---

## 9. Arquitetura de Contêineres Segura e Otimização Docker (v3.2)

Em plataformas modernas de microsserviços e Inteligência Artificial, contêineres mal configurados geram custos astronômicos de armazenamento, pipelines lentos de CI/CD e grandes brechas de segurança. Na versão **v3.2**, aplicamos os mais altos padrões de engenharia de contêineres:

### 9.1 Multi-Stage Build & Otimização do PyTorch (Economia >70% de Imagem)
- **O Desafio:** A aplicação utiliza `sentence-transformers` para indexação vetorial semântica. Ao instalar via PyPI tradicional, o pip baixa o PyTorch com binários completos CUDA/cuDNN da NVIDIA para GPU, inflando a imagem para mais de **3.5 GB**.
- **A Solução:** Adotamos um *multi-stage build* (`python:3.12.4-slim`), forçando a instalação dos wheels dedicados para CPU do PyTorch a partir do repositório oficial (`https://download.pytorch.org/whl/cpu`):
  ```dockerfile
  RUN pip install --no-cache-dir --prefix=/install torch --index-url https://download.pytorch.org/whl/cpu
  RUN pip install --no-cache-dir --prefix=/install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
  ```
- **Higiene de Imagem:** Definimos `ENV PYTHONDONTWRITEBYTECODE=1` e `ENV PIP_NO_CACHE_DIR=1`, e expurgamos diretórios `__pycache__` e arquivos `.pyc` residuais antes de copiar a camada para a imagem de runtime.
- **Resultado:** A imagem final encolheu de ~3.5GB para aproximadamente **800MB**, tornando deploys até 4x mais rápidos no cluster.

### 9.2 Isolamento de Redes no Docker Compose (`proxy_net` vs `backend_net`)
- **Princípio de Zero Trust em Contêineres:** Bancos de dados nunca devem ser expostos na internet nem mapeados desnecessariamente nas portas do host.
- **Topologia de Duas Redes:**
  ```
  [ Internet / Usuário ]
          │
          ▼ (porta 80)
    ┌───────────┐
    │   Proxy   │ (sre_rag_proxy / Nginx)
    └─────┬─────┘
          │ (proxy_net)
          ▼
    ┌───────────┐
    │    API    │ (sre_rag_api / FastAPI)
    └─────┬─────┘
          │ (backend_net: internal=true)
    ┌─────┴─────────────┐
    ▼                   ▼
  PostgreSQL          Redis
  (porta oculta)     (porta oculta)
  ```
  - **`proxy_net` (Pública/DMZ):** Apenas o Nginx publica a porta 80. A API participa desta rede apenas para receber requisições do Proxy, sem publicar portas diretamente no host.
  - **`backend_net` (Interna / `internal: true`):** Liga a API ao PostgreSQL e Redis. A flag `internal: true` impede que qualquer tráfego externo entre ou saia dessa rede, e nenhum serviço de banco publica portas no host.

### 9.3 Hardening do Contêiner em Produção
- **Usuário Não-Root (`appuser`):** A aplicação roda sob um usuário sem privilégios de sistema (`useradd -r -g appuser -s /sbin/nologin appuser`), mitigando riscos de *container breakout*.
- **Healthcheck Integrado:** Monitoramento ativo da saúde do processo a cada 30 segundos com probing em `/healthz`.
- **Arquivos Ignorados (`.dockerignore` e `app/.dockerignore`):** Bloqueio absoluto do envio de diretórios virtuais (`.venv`), segredos (`.env`), testes e metadados git para o daemon do Docker durante o build.


---

## 10. O Catálogo de 16 Cenários, Runbooks em 5 Fases e a Base de Conceitos SRE (v3.3)

A versão **v3.3** consolida o laboratório como uma plataforma pedagógica de padrão mundial para times de engenharia, transformando a resposta a incidentes de uma simples "adivinhação de comandos" em um processo analítico completo e metódico.

### 10.1 O Catálogo Expandido de 16 Cenários Reais
Expandimos o acervo em `app/incidents.py` de 8 para **16 cenários autênticos**, organizados com rigor metodológico em 4 níveis de dificuldade perfeitamente balanceados:

| Nível | Cenários | Foco Operacional |
| :--- | :--- | :--- |
| **🟢 Fácil (4)** | OOM-Kill Básico, ConfigMap Ausente, Pod Pending por Recursos, Ingress 503 sem Endpoints | Detecção de falhas de configuração básica, manifests malformados e limites óbvios de recursos. |
| **🟡 Médio (4)** | CrashLoopBackOff, Degradação TLS, Esgotamento Redis, HPA Flapping | Diagnóstico de ciclos de reinicialização de aplicação, expiração de certificados e oscilação de autoscaling. |
| **🔴 Difícil (4)** | Pressão de Disco, Falha de DNS CoreDNS, PVC Mount Deadlock, CPU Throttling por CFS | Análise de subsistemas do cluster: CoreDNS, kubelet disk eviction, deadlocks de montagem de volume e cgroups v1/v2. |
| **💀 Extremo (4)** | Alta Latência por GC, Alta Taxa de Erro 500, Esgotamento de Pool de Conexões de DB, Split-Brain Partition | Fenômenos concorrentes distribuídos complexos: contenção de banco de dados, falha de consenso Raft e particionamento de rede. |

### 10.2 A Metodologia de Runbooks Estruturados em 5 Fases
Em incidentes de alta severidade (SEV-1 / SEV-2), um SRE não pula direto para a correção; ele segue um protocolo estrito para não agravar a indisponibilidade. O modal interativo `#runbook-modal` e a visualização do War Room agora estruturam o passo a passo em 5 fases:

1. **🚨 Fase 1: Triagem & Alertas**  
   - Expressões PromQL específicas dos *Golden Signals* (Latência, Tráfego, Erros, Saturação).  
   - Alertas exatos do Prometheus Alertmanager (ex: `KubePodCrashLooping`, `CoreDNSLatencyHigh`).
2. **🔍 Fase 2: Diagnóstico & Inspeção**  
   - Comandos reais de auditoria do cluster (`kubectl describe pod`, `kubectl logs --previous`, inspeção de eventos).  
   - Verificações de baixo nível em nós e contêineres (`dmesg -T`, métricas de cgroup).
3. **⚡ Fase 3: Mitigação Imediata**  
   - Ação rápida de contenção para estancar o sangramento do *Error Budget* (ex: `helm rollback`, `kubectl scale`).  
   - Comando executável e critério objetivo de validação de MTTR.
4. **🛠️ Fase 4: Análise de Causa Raiz & Correção Permanente**  
   - Diagnóstico profundo da causa subjacente (ex: vazamento de memória em buffer Go/Java, deadlock de locks relacionais).  
   - Patch permanente no repositório de GitOps e manifestos Kubernetes.
5. **🛡️ Fase 5: Prevenção & Pós-Morte**  
   - Postmortem blameless estruturado com os 5 Porquês.  
   - Criação de novos alertas proativos e testes contínuos com Chaos Engineering.

### 10.3 A Central de Conceitos SRE (`📚 Conceitos SRE`) e o Mergulho no Kernel
Para elevar o nível técnico dos engenheiros, criamos a aba `📚 Conceitos SRE`. Ela funciona como um manual de bolso com arquitetura profunda:
- **CFS Bandwidth Throttling:** Como o kernel Linux divide o tempo de CPU em períodos de 100ms (`cpu.cfs_period_us`) e aplica throttling mesmo quando a CPU do nó está ociosa.
- **Mecânica do OOM Killer:** Como o kernel calcula o `oom_score` a partir do `oom_score_adj` atribuído pelo kubelet com base na classe de QoS do Pod (Guaranteed, Burstable, BestEffort).
- **Page Cache vs Dirty Memory:** Como o Linux gerencia escrita em disco e a diferença entre buffers e page cache durante incidentes de `DiskPressure`.
- **Esgotamento de Conexões TCP & Socket States:** Diferença entre estados `TIME_WAIT`, `CLOSE_WAIT` e estouro de file descriptors no sistema operacional (`fs.file-max`).

---

### 10.4 Engenharia de Frontend em SRE: Confinamento de Viewport e Rolagem Resiliente
Em dashboards operacionais de missão crítica, a interface não pode travar ou ocultar alertas sob nenhuma circunstância de redimensionamento de janela ou densidade de tela.

Na versão **v3.3**, resolvemos uma complicação clássica de arquiteturas SPA complexas:
- **A Armadilha do `overflow: hidden` com Flexbox:** Em CSS moderno, elementos flexíveis (`flex: 1`) expandem automaticamente para o tamanho do seu conteúdo (`min-height: auto`), a menos que declaremos explicitamente `min-height: 0` e `height: 0`. Se o contêiner pai tiver `overflow: hidden`, o filho que cresce é cortado sem gerar barra de rolagem.
- **A Solução Adotada:**
  1. Confinamento estrito de viewport com Flexbox no `.layout` (`flex: 1 1 0; min-height: 0; height: 0;`).
  2. Isolamento de scrollbar no `.main-content` (`overflow-y: auto; scrollbar-gutter: stable;`), garantindo rolagem suave via mouse wheel, touchpad e atalhos de teclado.
  3. Descarte de sobrescritas agressivas de `display: block` via JavaScript; o estado do layout agora é mantido declarativamente no CSS.
  4. Margem de segurança de rolagem (`padding-bottom: 100px`) para assegurar que nenhum botão ou painel de métricas seja encoberto pelo rodapé do sistema.

---

## 11. Quick Wins & Hardening — A Fundação Técnica da v3.5

A versão **v3.5** consolida a maturidade operacional do laboratório como plataforma de produção, implementando cinco melhorias críticas de qualidade técnica que eliminam dívidas técnicas acumuladas, blindam a API contra abusos e otimizam o desempenho sob carga concorrente.

### 11.1 Eliminação de Deprecation Warnings — `SettingsConfigDict` do Pydantic V2

O Pydantic V2 (lançado em 2023) introduziu a `SettingsConfigDict` como substituta da `class Config` interna, compatibilizando as configurações com o sistema de type hints do Python moderno. A `class Config:` legada gera um `PydanticDeprecatedSince20` warning a cada importação, contaminando os logs de startup da aplicação e as saídas dos testes automatizados.

```python
# Antes (v3.3) — Padrão depreciado, removido no Pydantic V3
class Settings(BaseSettings):
    class Config:
        env_prefix = ""
        case_sensitive = False

# Depois (v3.5) — API moderna, statically typed
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        extra="ignore",  # Ignora variáveis de ambiente desconhecidas com segurança
    )
```

> **Conceito SRE:** `extra="ignore"` é uma escolha deliberada de segurança: variáveis de ambiente inespertas no container não causam falha de startup, reduzindo o blast radius de misconfigurações em deployments.

### 11.2 Connection Storm Prevention — Cache TTL no Health Check

O **connection storm** é um padrão clássico de falha em cascata: quando o kubelet dispara probes de liveness/readiness em múltiplas réplicas simultaneamente (padrão com N réplicas e intervalo de 5s), cada probe pode abrir uma nova conexão TCP ao banco de dados. Com rate de 12 probes/minuto por réplica e 3 réplicas, o cluster mantém 36 conexões ativas apenas para health checks — um vetor real de esgotamento do connection pool.

A solução de cache TTL implementada garante que dentro de uma janela de 5 segundos, qualquer número de chamadas a `check_postgres()` / `check_redis()` resulta em **exatamente uma** conexão ao banco, com os resultados subsequentes servidos da memória em tempo O(1).

Benefício adicional: `latency_ms` agora mede o round-trip real de cada conexão (antes estava hardcoded como `0`), tornando a métrica acionável para alertas de SLO de dependência.

### 11.3 Embeddings Assíncronos — Desbloqueando o Event Loop do FastAPI

O FastAPI usa o modelo de concorrência assíncrona do Python (`asyncio`). Em um event loop de thread única, qualquer chamada bloqueante (CPU-bound ou I/O síncrono) congela o processamento de **todas** as requisições concorrentes durante sua execução. O `SentenceTransformer.encode()` é CPU-bound e demora entre 20ms e 100ms por inferência no CPU.

```python
# Antes (v3.3) — Bloqueia o event loop durante toda a inferência
query_embedding = generate_query_embedding(question)

# Depois (v3.5) — Executa em thread pool, libera o event loop
query_embedding = await asyncio.to_thread(generate_query_embedding, question)
```

O `asyncio.to_thread()` delega a execução para o `ThreadPoolExecutor` padrão do Python (tamanho: `min(32, os.cpu_count() + 4)`), retornando uma coroutine awaitable. O event loop continua processando outros endpoints, SSE streams e health checks enquanto o embedding está sendo computado.

### 11.4 Compressão HTTP em Camadas — FastAPI e Nginx

A compressão GZip foi implementada em dois níveis para máxima eficiência:

**Nível 1 — FastAPI GZipMiddleware:**
```python
app.add_middleware(GZipMiddleware, minimum_size=1000)
```
Qualquer resposta HTTP acima de 1KB é comprimida transparentemente antes de sair do container da API. A dashboard HTML de 101KB comprime para ~18KB (~82% de redução), acelerando o First Contentful Paint.

**Nível 2 — Nginx como proxy de compressão e cache:**
O `docker/nginx.conf` agora inclui `gzip_comp_level 6` (equilíbrio ideal entre CPU e compressão), `gzip_vary on` (para caches intermediários), timeouts defensivos (`proxy_connect_timeout 5s`) e uma `location /static/` dedicada com `expires 1h` e `Cache-Control: public, immutable` para assets versionados — eliminando requisições repetidas do navegador para JS e CSS.

### 11.5 Defense in Depth — Rate Limiting, Security Headers e CORS

**Rate Limiting com slowapi:**
O endpoint `/api/v1/query` tem custo operacional assimétrico (inferência + busca vetorial), tornando-o o alvo preferencial de ataques de esgotamento de recursos. O `slowapi` implementa token bucket por IP com backend em memória e limite de 30 req/min no endpoint de query, retornando automaticamente HTTP 429 com `Retry-After`.

**Security Headers — Defense no Navegador:**
| Header | Valor | Proteção |
|--------|-------|----------|
| `X-Frame-Options` | `DENY` | Clickjacking via iframe |
| `X-Content-Type-Options` | `nosniff` | MIME type sniffing |
| `Content-Security-Policy` | Allowlist estrita | XSS, injeção de scripts |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Vazamento de URL |
| `Strict-Transport-Security` | `max-age=31536000` (produção) | Downgrade HTTPS → HTTP |
| `Permissions-Policy` | `camera=(), microphone=()` | Acesso indevido a hardware |

**CORS Configurável por Ambiente:**
```python
allow_origins=["*"] if not settings.is_production else ["https://sre-rag.example.com"]
```
Em desenvolvimento, `*` facilita testes locais. Em produção, apenas origins explicitamente aprovadas podem fazer requisições cross-origin, bloqueando ataques CSRF de origens não confiáveis.

---

---

## 12. A Era dos Agentes Autônomos, Busca Híbrida e Chaos Real no Kernel (v4.0)

A versão 4.0 representa o salto qualitativo mais expressivo da plataforma: a transição de um ambiente puramente reativo para um **ecossistema de confiabilidade autônomo e observável em três dimensões**.

### 12.1 O Ciclo OODA do Agente SRE: Observe, Orient, Decide, Act

Quando um alerta do Prometheus dispara em plena madrugada, engenheiros humanos não agem no vácuo; eles seguem o ciclo cognitivo formulado pelo estrategista militar John Boyd: o ciclo **OODA**. Implementamos este raciocínio formalmente em `app/agent/sre_agent.py` e `app/agent/tools.py`:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   OBSERVE    │ ──▶ │    ORIENT    │ ──▶ │    DECIDE    │ ──▶ │     ACT      │
│ (Telemetria) │     │  (Runbooks)  │     │ (Diagnóstico)│     │ (Mitigação)  │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

1. **Observe (Observar):** O agente utiliza *Tool Calling* para consultar as métricas reais no Prometheus (`query_prometheus`) e inspecionar a sequência de eventos de pods e nós no Kubernetes (`get_k8s_events`).
2. **Orient (Orientar):** Em vez de "adivinhar", o agente consulta o motor de busca vetorial híbrido (`search_runbooks`) para mapear os sintomas a procedimentos operacionais padrão (SOPs) validados pela engenharia.
3. **Decide (Decidir):** O agente avalia a correspondência diagnóstica, identifica a provável causa raiz e seleciona o melhor plano de remediação.
4. **Act (Agir):** Caso configurado com `auto_mitigate: True`, executa a mitigação (escala de réplicas, reinício gracioso de deployments com CrashLoop, limpeza de pods). Com `auto_mitigate: False`, gera a recomendação estruturada aguardando validação humana (*Human-in-the-Loop*).
5. **Streaming de Raciocínio via SSE:** Cada etapa do ciclo é transmitida via Server-Sent Events para o War Room do dashboard, garantindo total transparência e auditabilidade sobre a linha de raciocínio da IA.

### 12.2 Busca Híbrida 3-Stage: pgvector (HNSW) + BM25Okapi + RRF + FlashRank

Em incidentes de SRE, modelos puramente semânticos falham catastroficamente diante de erros técnicos literais como `exit code 137`, `OOMKilled` ou sinais POSIX (`SIGKILL`). Para resolver isso, implementamos em `app/rag/vector_store.py` uma pipeline híbrida em três estágios:

1. **Estágio 1 — Busca Densa (pgvector + HNSW):** O PostgreSQL armazena vetores de 384 dimensões em tabelas indexadas com algoritmo HNSW (*Hierarchical Navigable Small World*), provendo recall semântico para consultas conceituais (ex: "aplicação consumindo muita memória").
2. **Estágio 2 — Busca Esparsa Léxica (BM25Okapi):** O algoritmo BM25 avalia a frequência exata de termos técnicos e códigos de erro nos runbooks, garantindo pontuação máxima para strings literais.
3. **Estágio 3 — Fusão RRF e Re-ranking Semântico:**
   - **Reciprocal Rank Fusion (RRF, $k=60$):** Combina as duas listas de ranqueamento de maneira invariante à escala dos scores:
     $$RRF\_Score(d) = \sum_{m \in \{dense, sparse\}} \frac{1}{60 + rank_m(d)}$$
   - **Cross-Encoder FlashRank:** Um modelo neural leve avalia simultaneamente o par query-documento para reordenar os top candidatos com latência adicionada inferior a 15ms.

### 12.3 Chaos Engineering Real no Kernel Linux & Dead Man's Switch

A versão 4.0 introduz o módulo `app/chaos_real.py`, abandonando simulações superficiais em favor de injeções de falha de baixo nível:

1. **Pressão de Memória no Kernel:** Escrita direta nos arquivos de controle de cgroups v2 (`memory.max` e `memory.high`), provocando contenção real de memória e forçando a intervenção do Linux OOM Killer.
2. **CPU Throttling no Agendador CFS:** Redução drástica das cotas de CPU (`cpu.cfs_quota_us`), simulando gargalos de processamento que degradam o P99 de latência.
3. **Latência de Rede com `tc netem`:** Manipulação dos qdiscs da interface de rede adicionando 200ms de delay determinístico e jitter para testar timeouts e circuit breakers.
4. **O Dead Man's Switch de 60 Segundos:** Para evitar que um teste de caos indisponibilize permanentemente o cluster se a comunicação cair, cada experimento ativa um temporizador assíncrono estrito. Se nenhuma ação ou renovação ocorrer em 60s, o sistema reverte automaticamente cgroups e configurações de rede para o estado padrão.

### 12.4 Observabilidade Tridimensional: OpenTelemetry, Jaeger & Structlog

Em `app/telemetry.py`, unificamos métricas, logs e traces:
- **TracerProvider OpenTelemetry:** Auto-instrumentação nas camadas FastAPI, Asyncpg e Redis.
- **Exportador OTLP/gRPC:** Envio eficiente de spans distribuídos para o coletor Jaeger (`http://jaeger:4317`).
- **Correlação Automática no Structlog:** O processador `inject_otel_context` extrai o contexto ativo do span e injeta `trace_id` e `span_id` em todos os registros de log JSON, permitindo rastrear o ciclo de vida completo de uma requisição ponta a ponta.

### 12.5 Monitoramento Dinâmico de SLO & Error Budget

O endpoint `/api/v1/slo/error-budget` implementa o cálculo em tempo real da disponibilidade e do consumo do Error Budget sobre uma janela móvel de 30 dias. Ele monitora a taxa de queima (*burn rate*) e sinaliza estados de alerta (`healthy`, `warning`, `critical`), fornecendo a base quantitativa necessária para políticas de *deploy freeze*.

### 12.6 DevSecOps Corporativo & Pod Security Standards (PSS Restricted)

O Helm Chart da aplicação foi endurecido segundo o perfil mais restritivo do Kubernetes:
- `readOnlyRootFilesystem: true` com volumes efêmeros `emptyDir` para diretórios temporários.
- Usuário não-root explícito (UID `10001`).
- `capabilities.drop: ["ALL"]` e seccomp profile `RuntimeDefault`.
- NetworkPolicies Zero-Trust isolando estritamente os fluxos de rede da API.
- Escaneamento de segurança contínuo com **Trivy**, mantendo o projeto com **0 vulnerabilidades HIGH ou CRITICAL**.

---

## 13. Conclusão do Professor

Parabéns pelo empenho nos estudos! A Engenharia de Confiabilidade de Sites é uma das áreas mais nobres e desafiadoras da computação moderna. Dominar métricas de MTTD/MTTR, automação resiliente e engenharia do caos controlada colocará você entre os profissionais mais bem preparados do mercado.

A v3.5 demonstra que **qualidade de software e segurança não são tarefas separadas** — elas são construídas incrementalmente, com critérios claros de aceite e validação automatizada. Cada melhoria desta versão foi guiada por um plano detalhado e validada por um script de verificação que certifica todos os 12 critérios antes do merge.

Consulte este guia sempre que tiver dúvidas sobre a arquitetura. Bons estudos e boas simulações! 🚀
