"""
SRE Incident Simulation Engine
Manages 16 incident scenarios, active simulations, diagnostic commands, 
step-by-step runbooks, and SRE architectural concepts with bilingual support (pt / en).
"""
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

SCENARIOS = {'high-error-rate': {'id': 'high-error-rate',
                     'title': 'High Error Rate (HTTP 500 Spike)',
                     'title_en': 'High Error Rate (HTTP 500 Spike)',
                     'severity': 'SEV-1',
                     'category': 'Disponibilidade',
                     'category_en': 'Availability',
                     'difficulty': 'easy',
                     'icon': '💥',
                     'description': 'A taxa de erros HTTP 500 subiu de 0.1% para 45% em menos de 2 minutos após um '
                                    'deploy de nova release. O SLO de disponibilidade está sendo violado gravemente.',
                     'description_en': 'HTTP 500 error rate spiked from 0.1% to 45% following a fresh release '
                                       'deployment. The availability SLO is critically violated.',
                     'symptoms': ['Burn rate > 14.4x na janela de 1 hora',
                                  'Alertmanager: SLOAvailabilityBurnRateCritical FIRING',
                                  'Grafana: SLO gauge em vermelho (< 99.9%)',
                                  'HTTP 500 em todos os endpoints principais da API'],
                     'symptoms_en': ['Burn rate > 14.4x in the 1-hour window',
                                     'Alertmanager: SLOAvailabilityBurnRateCritical FIRING',
                                     'Grafana: SLO gauge in red (< 99.9%)',
                                     'HTTP 500 across all core API endpoints'],
                     'hints': ['Execute `helm history sre-rag` para verificar quando ocorreu o último deploy e '
                               'comparar as revisões.',
                               'O deploy recente introduziu a falha. O comando mais rápido para restaurar o serviço é '
                               '`helm rollback sre-rag`.'],
                     'command': 'helm rollback sre-rag',
                     'solutions': [{'id': 'rollback',
                                    'label': 'Executar rollback do Helm release (`helm rollback sre-rag`)',
                                    'label_en': 'Perform Helm release rollback (`helm rollback sre-rag`)',
                                    'correct': True,
                                    'command': 'helm rollback sre-rag',
                                    'explanation': '✅ Correto! O deploy mais recente introduziu um bug crítico. O '
                                                   'rollback restaura a versão anterior estável imediatamente, sendo a '
                                                   'ação mais rápida para reduzir o MTTR.',
                                    'explanation_en': '✅ Correct! The latest deployment introduced a breaking bug. '
                                                      'Rollback immediately restores the previous stable release, '
                                                      'minimizing MTTR.'},
                                   {'id': 'scale-hpa',
                                    'label': 'Escalar o HPA para mais réplicas (aumentar maxReplicas)',
                                    'label_en': 'Scale HPA to more replicas (increase maxReplicas)',
                                    'correct': False,
                                    'command': 'kubectl scale deployment sre-rag-api --replicas=10',
                                    'explanation': '❌ Incorreto. Mais réplicas não resolvem um bug de código — cada '
                                                   'novo pod também retornará HTTP 500, consumindo recursos e gerando '
                                                   'custo sem mitigar a falha.',
                                    'explanation_en': '❌ Incorrect. Scaling does not resolve application code bugs — '
                                                      'each new pod will continue throwing 500 errors.'},
                                   {'id': 'restart-coredns',
                                    'label': 'Reiniciar os pods do CoreDNS no cluster',
                                    'label_en': 'Restart CoreDNS pods in the cluster',
                                    'correct': False,
                                    'command': 'kubectl rollout restart deployment/coredns -n kube-system',
                                    'explanation': '❌ Incorreto. O DNS está saudável. Os erros 500 são gerados pela '
                                                   'aplicação na camada HTTP, não por falha de resolução de nomes.',
                                    'explanation_en': '❌ Incorrect. DNS resolution is healthy; errors originate inside '
                                                      'application code.'}],
                     'runbook': '/docs/runbooks/high-error-rate',
                     'runbook_steps': {'triage': ['Verificar alerta Alertmanager: SLOAvailabilityBurnRateCritical.',
                                                  "Inspecionar Golden Signal 'Errors': "
                                                  "sum(rate(http_requests_total{status_code=~'5..'}[5m])) / "
                                                  'sum(rate(http_requests_total[5m])) * 100.',
                                                  'Checar timeline de deploys no canal de release ou Kubernetes '
                                                  'events.'],
                                       'diagnosis': ['helm history sre-rag (Revisão 2 implantada há 3 minutos com '
                                                     'status deployed).',
                                                     'kubectl logs -l app=sre-rag-api --tail=50 (Exceção não tratada '
                                                     'na rota /api/v1/query).',
                                                     'kubectl get pods -l app=sre-rag-api (Pods em Running mas '
                                                     'respondendo 500).'],
                                       'mitigation': {'action': 'Executar rollback imediato para a revisão estável '
                                                                'anterior.',
                                                      'command': 'helm rollback sre-rag',
                                                      'validation': 'Monitorar queda da taxa de erro para < 0.1% e '
                                                                    'retorno dos status 200 OK.'},
                                       'root_cause': {'analysis': 'A imagem da revisão 2 continha chamada a módulo '
                                                                  'inexistente no import da rota principal.',
                                                      'permanent_fix': 'Adicionar testes de fumaça (smoke tests) '
                                                                       'automatizados e canary deployment na pipeline '
                                                                       'de CI/CD.'},
                                       'prevention': ['Implementar Progressive Delivery com Argo Rollouts ou Flagger '
                                                      '(canary 10% -> 50% -> 100%).',
                                                      'Configurar rollback automático baseado em métricas Prometheus '
                                                      'no pipeline.']},
                     'concepts': {'resource_title': 'Gestão de Ciclo de Vida de Releases com Helm & Rollbacks',
                                  'architecture_components': ['Helm 3',
                                                              'Kubernetes Deployment Rollout',
                                                              'SLO Burn Rate'],
                                  'how_it_works': 'O Helm gerencia revisões armazenando manifestos como Secrets ou '
                                                  'ConfigMaps versionados. Quando um deploy quebra, o comando `helm '
                                                  'rollback` reaplica o manifesto da revisão anterior sem recompilar a '
                                                  'imagem, reduzindo o tempo de mitigação a segundos.',
                                  'best_practices': ['Princípio SRE: Mitigue primeiro (Rollback), investigue a causa '
                                                     'raiz depois (RCA).',
                                                     'Deploys imutáveis: cada versão de imagem deve possuir tag de '
                                                     "commit SHA exclusiva, nunca 'latest'.",
                                                     'Alertas de Burn Rate em múltiplas janelas (1h e 6h) para evitar '
                                                     'alertas espúrios e agir antes de esgotar o Error Budget.'],
                                  'golden_signals': ['Taxa de Erros HTTP (Error Rate %)',
                                                     'Error Budget Consumed (Burn Rate 1h e 6h)']},
                     'detection_delay_seconds': 35,
                     'investigation_delay_seconds': 85,
                     'chaos_action': 'simulate_500'},
 'oom-kill': {'id': 'oom-kill',
              'title': 'OOM Kill em Pod da API',
              'title_en': 'API Pod OOM Kill',
              'severity': 'SEV-1',
              'category': 'Recursos',
              'category_en': 'Resources',
              'difficulty': 'easy',
              'icon': '💀',
              'description': 'O pod da API é repetidamente encerrado pelo kernel do Linux com OOMKilled (Exit Code '
                             '137). O consumo de memória atingiu 100% do limite configurado sob tráfego.',
              'description_en': 'API pod terminated by Linux kernel OOM Killer with exit code 137. Memory usage '
                                'reached 100% of limits under load.',
              'symptoms': ['kubectl describe pod: Reason = OOMKilled, Exit Code: 137',
                           'Last State: Terminated with exit code 137',
                           'Memory usage: 512Mi/512Mi (100% do limit)',
                           'Restarts aumentando progressivamente sob carga'],
              'symptoms_en': ['kubectl describe pod: Reason = OOMKilled, Exit Code: 137',
                              'Last State: Terminated with exit code 137',
                              'Memory usage: 512Mi/512Mi (100% of configured limit)',
                              'Repeated restarts under incoming user workload'],
              'hints': ["Inspecione o pod com `kubectl describe pod` e procure pelo campo 'Last State: Terminated "
                        "(Reason: OOMKilled)'.",
                        'Aumente o limite de memória do container para 1024Mi via Helm: `helm upgrade sre-rag '
                        './helm/sre-rag --set api.resources.limits.memory=1024Mi`.'],
              'command': 'helm upgrade sre-rag ./helm/sre-rag --set api.resources.limits.memory=1024Mi',
              'solutions': [{'id': 'increase-memory',
                             'label': 'Aumentar `resources.limits.memory` no Helm values + investigar memory leak',
                             'label_en': 'Increase resources.limits.memory in Helm values + profile memory leak',
                             'correct': True,
                             'command': 'helm upgrade sre-rag ./helm/sre-rag --set api.resources.limits.memory=1024Mi',
                             'explanation': '✅ Correto! Aumentar o limit para 1024Mi alivia o estrangulamento de '
                                            'memória imediatamente, estabilizando o pod enquanto o perfil de uso é '
                                            'otimizado.',
                             'explanation_en': '✅ Correct! Raising memory limit immediately stabilizes the container '
                                               'while memory profiling investigates the leak.'},
                            {'id': 'rollback',
                             'label': 'Fazer rollback para a versão anterior',
                             'label_en': 'Rollback to previous release tag',
                             'correct': False,
                             'command': 'helm rollback sre-rag',
                             'explanation': '❌ Incorreto. O aumento de consumo é derivado de volume de dados sob '
                                            'carga; a versão anterior possui o mesmo limit e também cairia.',
                             'explanation_en': '❌ Incorrect. Memory pressure is driven by workload size; rolling back '
                                               'does not expand container headroom.'},
                            {'id': 'hpa-scale',
                             'label': 'Escalar mais réplicas via HPA',
                             'label_en': 'Scale more replicas via HPA',
                             'correct': False,
                             'command': 'kubectl scale deployment sre-rag-api --replicas=8',
                             'explanation': '❌ Ineficaz. Se uma requisição única consome mais de 512Mi, todos os pods '
                                            'novos continuarão morrendo simultaneamente sob carga.',
                             'explanation_en': '❌ Ineffective. If batch processing exceeds limits, every spawned '
                                               'replica will crash in parallel.'}],
              'runbook': '/docs/runbooks/oom-kill',
              'runbook_steps': {'triage': ['Alerta KubePodCrashLooping / ContainerOOMKilled disparado.',
                                           'Prometheus: container_memory_working_set_bytes atingindo '
                                           'container_spec_memory_limit_bytes.',
                                           'Pods com restarts repetidos (exit code 137).'],
                                'diagnosis': ['kubectl get pods -l app=sre-rag-api (Status: CrashLoopBackOff ou '
                                              'OOMKilled).',
                                              'kubectl describe pod <pod-name> (Reason: OOMKilled, Exit Code: 137).',
                                              'kubectl logs <pod-name> --previous (Última operação: processamento de '
                                              'grande batch de vetores).'],
                                'mitigation': {'action': 'Aumentar o limite de memória no Helm para 1024Mi.',
                                               'command': 'helm upgrade sre-rag ./helm/sre-rag --set '
                                                          'api.resources.limits.memory=1024Mi',
                                               'validation': 'kubectl get pods (Verificar se os pods permanecem em '
                                                             'Running sem novos restarts).'},
                                'root_cause': {'analysis': 'O modelo carregava o vocabulário inteiro em memória sem '
                                                           'chunking durante picos de consultas.',
                                               'permanent_fix': 'Implementar gerador paginado com yield para carregar '
                                                                'embeddings sob demanda.'},
                                'prevention': ["Configurar QoS Class 'Guaranteed' com requests == limits para pods de "
                                               'missão crítica.',
                                               'Alerta preditivo com PromQL predict_linear para projetar esgotamento '
                                               'de memória com 1 hora de antecedência.']},
              'concepts': {'resource_title': 'Linux Kernel OOM Killer & Kubernetes QoS Classes',
                           'architecture_components': ['Linux cgroups v2 memory.max',
                                                       'Kernel oom_score_adj',
                                                       'Kubernetes Pod QoS'],
                           'how_it_works': 'No Linux, o cgroup limita a quantidade de memória física e swap. Quando o '
                                           'processo excede `memory.max`, o kernel invoca o Out-Of-Memory Killer. O '
                                           'kernel atribui um score baseado no consumo e no `oom_score_adj` '
                                           'configurado pelo Kubelet (baseado no QoS: BestEffort, Burstable ou '
                                           'Guaranteed) e envia um sinal SIGKILL (137).',
                           'best_practices': ['Sempre monitore `container_memory_working_set_bytes` e não o '
                                              '`usage_bytes`, pois este último inclui page cache reutilizável.',
                                              'Evite superdimensionar memória sem necessidade, mas garanta margem de '
                                              '20-30% acima do pico normal.',
                                              'Para serviços de latência crítica, utilize QoS Guaranteed (requests == '
                                              'limits).'],
                           'golden_signals': ['Saturação de Memória (Memory Saturation %)',
                                              'Taxa de Reinícios de Containers (Container Restarts/min)']},
              'detection_delay_seconds': 25,
              'investigation_delay_seconds': 70,
              'chaos_action': None},
 'missing-config-secret': {'id': 'missing-config-secret',
                           'title': 'ConfigMap / Secret Ausente (CrashLoop)',
                           'title_en': 'Missing ConfigMap / Secret (CrashLoop)',
                           'severity': 'SEV-2',
                           'category': 'Confiabilidade',
                           'category_en': 'Reliability',
                           'difficulty': 'easy',
                           'icon': '🔑',
                           'description': "Os pods recém-criados falham imediatamente no bootstrap com 'KeyError: "
                                          "OPENAI_API_KEY'. O Secret 'sre-rag-secrets' não foi provisionado no "
                                          'namespace após o deploy do Helm.',
                           'description_en': "New pods crash instantly during bootstrap with 'KeyError: "
                                             "OPENAI_API_KEY'. Required Secret 'sre-rag-secrets' was not found in the "
                                             'target namespace.',
                           'symptoms': ['kubectl get pods: sre-rag-api-* CrashLoopBackOff',
                                        "kubectl logs: KeyError: 'OPENAI_API_KEY' not found in environment",
                                        'Zero pods prontos no deployment (0/2 READY)',
                                        "Eventos: Error: secret 'sre-rag-secrets' not found"],
                           'symptoms_en': ['kubectl get pods: sre-rag-api-* CrashLoopBackOff',
                                           "kubectl logs: KeyError: 'OPENAI_API_KEY' not found in environment",
                                           'Zero pods ready in deployment (0/2 READY)',
                                           "Events: Error: secret 'sre-rag-secrets' not found"],
                           'hints': ['Verifique os logs do pod com `kubectl logs` para identificar a variável de '
                                     'ambiente que gerou a exceção.',
                                     'Crie o secret ausente no namespace: `kubectl create secret generic '
                                     'sre-rag-secrets --from-literal=OPENAI_API_KEY=mock-key '
                                     '--from-literal=DATABASE_URL=postgres://app:secret@postgresql:5432/sre_db`.'],
                           'command': 'kubectl create secret generic sre-rag-secrets '
                                      '--from-literal=OPENAI_API_KEY=mock-key '
                                      '--from-literal=DATABASE_URL=postgres://app:secret@postgresql:5432/sre_db',
                           'solutions': [{'id': 'create-secret',
                                          'label': 'Criar o secret `sre-rag-secrets` com as credenciais necessárias',
                                          'label_en': 'Create secret `sre-rag-secrets` with mandatory application '
                                                      'credentials',
                                          'correct': True,
                                          'command': 'kubectl create secret generic sre-rag-secrets '
                                                     '--from-literal=OPENAI_API_KEY=mock-key '
                                                     '--from-literal=DATABASE_URL=postgres://app:secret@postgresql:5432/sre_db',
                                          'explanation': '✅ Correto! Provisionar o Secret com as chaves obrigatórias '
                                                         'satisfaz a inicialização do container, permitindo que a '
                                                         'aplicação suba com sucesso.',
                                          'explanation_en': '✅ Correct! Injecting the missing secret allows '
                                                            'application bootstrap validation to succeed.'},
                                         {'id': 'delete-deployment',
                                          'label': 'Deletar o deployment e recriá-lo',
                                          'label_en': 'Delete and recreate the deployment',
                                          'correct': False,
                                          'command': 'kubectl delete deployment sre-rag-api',
                                          'explanation': '❌ Incorreto. Deletar o deployment não resolve a falta do '
                                                         'secret — os novos pods continuarão falhando pelo mesmo '
                                                         'motivo.',
                                          'explanation_en': '❌ Incorrect. Recreating the deployment will still '
                                                            'encounter the missing Secret dependency.'},
                                         {'id': 'ignore-error',
                                          'label': 'Alterar o código para rodar sem autenticação',
                                          'label_en': 'Modify application code to bypass authentication',
                                          'correct': False,
                                          'command': 'kubectl set env deployment/sre-rag-api BYPASS_AUTH=true',
                                          'explanation': '❌ Violação de segurança. Não se deve desativar validações de '
                                                         'segurança para contornar falha de configuração de '
                                                         'infraestrutura.',
                                          'explanation_en': '❌ Major security violation! Bypassing authentication '
                                                            'compromises the entire system.'}],
                           'runbook': '/docs/runbooks/missing-config-secret',
                           'runbook_steps': {'triage': ['Alerta KubeContainerWaiting / PodCrashLoopBackOff no '
                                                        'Alertmanager.',
                                                        'Deployment com 0 de 2 réplicas prontas.',
                                                        'Endpoint da API indisponível (HTTP 502 Bad Gateway no '
                                                        'Ingress).'],
                                             'diagnosis': ['kubectl get pods -l app=sre-rag-api (CrashLoopBackOff).',
                                                           'kubectl logs -l app=sre-rag-api (KeyError: '
                                                           "'OPENAI_API_KEY' / 'DATABASE_URL').",
                                                           'kubectl get secrets (Confirmar ausência do secret '
                                                           "'sre-rag-secrets')."],
                                             'mitigation': {'action': 'Criar o secret genérico com as chaves '
                                                                      'esperadas.',
                                                            'command': 'kubectl create secret generic sre-rag-secrets '
                                                                       '--from-literal=OPENAI_API_KEY=mock-key '
                                                                       '--from-literal=DATABASE_URL=postgres://app:secret@postgresql:5432/sre_db',
                                                            'validation': 'kubectl rollout status '
                                                                          'deployment/sre-rag-api'},
                                             'root_cause': {'analysis': 'O pipeline de CI/CD aplicou o Helm release em '
                                                                        'um namespace novo sem disparar o job de '
                                                                        'sincronização do Vault/ExternalSecrets.',
                                                            'permanent_fix': 'Integrar o External Secrets Operator '
                                                                             '(ESO) para reconciliação automática de '
                                                                             'segredos.'},
                                             'prevention': ['Adicionar validação de schema JSON no Helm '
                                                            '(values.schema.json).',
                                                            'Configurar pre-install hooks de validação de dependências '
                                                            'no Helm.']},
                           'concepts': {'resource_title': 'Kubernetes Secrets Management & Injeção de Variáveis',
                                        'architecture_components': ['Kubernetes Secrets',
                                                                    'envFrom / SecretKeyRef',
                                                                    'External Secrets Operator'],
                                        'how_it_works': 'O Kubelet monta Secrets e ConfigMaps como variáveis de '
                                                        'ambiente ou volumes tmpfs antes de executar o container. Se '
                                                        'uma chave mapeada via `envFrom` ou `secretKeyRef` com '
                                                        '`optional: false` não existir, o Kubelet não consegue iniciar '
                                                        'o container ou a aplicação quebra em runtime ao acessar o '
                                                        'dicionário de ambiente.',
                                        'best_practices': ['Nunca commite segredos em texto puro em repositórios Git.',
                                                           'Use External Secrets Operator ou HashiCorp Vault Agent '
                                                           'Injector para sincronizar secrets automaticamente.',
                                                           'Configure liveness e startup probes de forma resiliente, '
                                                           'permitindo fallbacks gracioso quando dependências externas '
                                                           'falharem temporariamente.'],
                                        'golden_signals': ['Contagem de Pods Prontos (Ready Pods Ratio)',
                                                           'Taxa de Falhas de Inicialização (Container Startup '
                                                           'Failures)']},
                           'detection_delay_seconds': 20,
                           'investigation_delay_seconds': 55,
                           'chaos_action': None},
 'pod-pending-resources': {'id': 'pod-pending-resources',
                           'title': 'Pod em Estado Pending por Falta de CPU',
                           'title_en': 'Pod Stuck in Pending (Insufficient CPU)',
                           'severity': 'SEV-2',
                           'category': 'Capacidade',
                           'category_en': 'Capacity',
                           'difficulty': 'easy',
                           'icon': '⏳',
                           'description': "Novos pods da API estão presos indefinidamente no estado 'Pending'. O "
                                          "Kube-Scheduler reporta '0/3 nodes are available: 3 Insufficient cpu'. Os "
                                          'requests de CPU foram acidentalmente configurados com valor exorbitante '
                                          '(8000m por pod).',
                           'description_en': "New API pods stuck in 'Pending'. Kube-Scheduler events report '0/3 nodes "
                                             "are available: 3 Insufficient cpu' due to misconfigured 8000m requests.",
                           'symptoms': ['kubectl get pods: sre-rag-api-* Pending',
                                        'kubectl describe pod: 0/3 nodes are available: 3 Insufficient cpu',
                                        'HPA incapaz de escalar novos pods para absorver tráfego',
                                        'Alerta KubePodNotScheduled disparado há 10 minutos'],
                           'symptoms_en': ['kubectl get pods: sre-rag-api-* Pending',
                                           'kubectl describe pod: 0/3 nodes are available: 3 Insufficient cpu',
                                           'HPA unable to scale replicas to handle user traffic',
                                           'Alert KubePodNotScheduled firing for 10 minutes'],
                           'hints': ['Inspecione os eventos do pod com `kubectl describe pod` e procure pela mensagem '
                                     'do default-scheduler.',
                                     'Reduza os requests de CPU para 250m no Helm: `helm upgrade sre-rag '
                                     './helm/sre-rag --set api.resources.requests.cpu=250m`.'],
                           'command': 'helm upgrade sre-rag ./helm/sre-rag --set api.resources.requests.cpu=250m',
                           'solutions': [{'id': 'adjust-requests',
                                          'label': 'Reduzir `resources.requests.cpu` para 250m via Helm',
                                          'label_en': 'Lower resources.requests.cpu to 250m via Helm',
                                          'correct': True,
                                          'command': 'helm upgrade sre-rag ./helm/sre-rag --set '
                                                     'api.resources.requests.cpu=250m',
                                          'explanation': '✅ Correto! Ajustar os requests de CPU para o tamanho real da '
                                                         'aplicação (250m) permite que o Scheduler agende os pods nos '
                                                         'nós disponíveis imediatamente.',
                                          'explanation_en': '✅ Correct! Right-sizing CPU requests allows the '
                                                            'Kube-Scheduler to fit pods into existing cluster nodes.'},
                                         {'id': 'cordon-nodes',
                                          'label': 'Colocar os nós do cluster em manutenção (cordon)',
                                          'label_en': 'Cordon the cluster nodes',
                                          'correct': False,
                                          'command': 'kubectl cordon node-1 node-2 node-3',
                                          'explanation': '❌ Incorreto e danoso. Fazer cordon impede qualquer pod de '
                                                         'ser agendado nos nós, agravando a indisponibilidade.',
                                          'explanation_en': '❌ Disastrous. Cordoning nodes prevents scheduling on all '
                                                            'nodes entirely.'},
                                         {'id': 'restart-scheduler',
                                          'label': 'Reiniciar o kube-scheduler no control plane',
                                          'label_en': 'Restart kube-scheduler in control plane',
                                          'correct': False,
                                          'command': 'kubectl rollout restart deployment/kube-scheduler -n kube-system',
                                          'explanation': '❌ Incorreto. O scheduler está funcionando perfeitamente; ele '
                                                         'rejeita o agendamento porque a capacidade matemática '
                                                         'solicitada não cabe nos nós.',
                                          'explanation_en': '❌ Incorrect. The scheduler is acting properly by '
                                                            'enforcing resource limits.'}],
                           'runbook': '/docs/runbooks/pod-pending-resources',
                           'runbook_steps': {'triage': ['Alerta KubePodNotScheduled / HPAUnableToScale.',
                                                        "Pods presos em estado 'Pending' há mais de 5 minutos.",
                                                        'Capacidade do cluster com nós em alta alocação de requests.'],
                                             'diagnosis': ['kubectl get pods -l app=sre-rag-api (Status: Pending).',
                                                           'kubectl describe pod <pod-name> (Events: Warning '
                                                           'FailedScheduling: 0/3 nodes available: 3 Insufficient '
                                                           'cpu).',
                                                           "kubectl describe nodes | grep -A 8 'Allocated resources:' "
                                                           '(CPU Requests em 98% da capacidade).'],
                                             'mitigation': {'action': 'Corrigir os requests de CPU no Helm para o '
                                                                      'valor nominal de 250m.',
                                                            'command': 'helm upgrade sre-rag ./helm/sre-rag --set '
                                                                       'api.resources.requests.cpu=250m',
                                                            'validation': 'kubectl get pods (Verificar transição para '
                                                                          'Running em poucos segundos).'},
                                             'root_cause': {'analysis': 'Um erro de digitação no values.yaml colocou '
                                                                        '`cpu: 8000m` (8 núcleos) em vez de `cpu: '
                                                                        '250m`.',
                                                            'permanent_fix': 'Adicionar política de validação de '
                                                                             'admission controller (Kyverno / OPA '
                                                                             'Gatekeeper) limitando o teto de '
                                                                             'requests.'},
                                             'prevention': ['Configurar Cluster Autoscaler ou Karpenter para '
                                                            'provisionar nós dinamicamente caso a demanda seja '
                                                            'legítima.',
                                                            'Implantar LimitRanges no namespace para restringir '
                                                            'requests máximos permitidos por container.']},
                           'concepts': {'resource_title': 'Kube-Scheduler: Predicates, Priorities & Capacidade '
                                                          'Alocável',
                                        'architecture_components': ['Kube-Scheduler',
                                                                    'Node Allocatable',
                                                                    'Requests vs Limits'],
                                        'how_it_works': 'O Kube-Scheduler decide em qual nó cada pod será executado '
                                                        'através de duas fases: Filtragem (Predicates) e Pontuação '
                                                        '(Priorities). Na filtragem, o scheduler calcula a soma dos '
                                                        '`requests` dos pods já alocados. Se a capacidade '
                                                        '`Allocatable` do nó não suportar a soma, o nó é descartado. '
                                                        "Se nenhum nó passar, o pod permanece em 'Pending'.",
                                        'best_practices': ['Requests representam reserva garantida; Limits representam '
                                                           'o teto máximo de estouro.',
                                                           'Monitore a razão de alocação vs consumo real: use '
                                                           'ferramentas de right-sizing como Kubecost ou Goldilocks.',
                                                           'Nunca deixe pods de produção sem `resources.requests` '
                                                           'definidos.'],
                                        'golden_signals': ['Tempo em Estado Pending (Pod Scheduling Latency)',
                                                           'Alocação de CPU do Cluster (Node CPU Commit %)']},
                           'detection_delay_seconds': 20,
                           'investigation_delay_seconds': 60,
                           'chaos_action': None},
 'high-latency': {'id': 'high-latency',
                  'title': 'High Latency (P99 > 2s)',
                  'title_en': 'High Latency (P99 > 2s)',
                  'severity': 'SEV-2',
                  'category': 'Latência',
                  'category_en': 'Latency',
                  'difficulty': 'medium',
                  'icon': '🐢',
                  'description': 'A latência P99 das requisições subiu para 4.2 segundos. O SLO de latência (99.5% < '
                                 '500ms) está sendo violado. Usuários relatam lentidão extrema.',
                  'description_en': 'P99 request latency degraded to 4.2 seconds, violating the latency SLO target '
                                    '(99.5% < 500ms).',
                  'symptoms': ['P99 latency: 4200ms (SLO target: 500ms)',
                               'CPU da API em 95% de utilização',
                               'PostgreSQL: slow queries > 2s detectadas',
                               'Redis cache hit rate caiu para 12%'],
                  'symptoms_en': ['P99 latency: 4200ms (SLO target: 500ms)',
                                  'API Pod CPU utilization at 95%',
                                  'PostgreSQL: slow queries > 2s detected',
                                  'Redis cache hit rate dropped to 12%'],
                  'hints': ['Verifique o consumo de CPU dos pods com `kubectl top pods` para confirmar saturação.',
                            'Escale os pods da API via HPA para aliviar a carga: `kubectl scale hpa sre-rag-api '
                            '--min=5 --max=20`.'],
                  'command': 'kubectl scale hpa sre-rag-api --min=5 --max=20',
                  'solutions': [{'id': 'scale-hpa',
                                 'label': 'Escalar HPA + investigar e otimizar queries lentas no PostgreSQL',
                                 'label_en': 'Scale HPA + investigate and optimize slow queries in PostgreSQL',
                                 'correct': True,
                                 'command': 'kubectl scale hpa sre-rag-api --min=5 --max=20',
                                 'explanation': '✅ Correto! Escalar alivia a pressão de CPU imediatamente (mitigação '
                                                'rápida) enquanto a análise de slow queries investiga a causa raiz.',
                                 'explanation_en': '✅ Correct! Scaling relieves CPU saturation immediately while query '
                                                   'analysis targets root cause.'},
                                {'id': 'rollback',
                                 'label': 'Fazer rollback do último deploy',
                                 'label_en': 'Rollback the last deployment',
                                 'correct': False,
                                 'command': 'helm rollback sre-rag',
                                 'explanation': '❌ Incorreto. A latência é provocada por volume repentino de tráfego '
                                                'somado a queries sem índice, não por alteração de código recente.',
                                 'explanation_en': '❌ Incorrect. Latency is caused by traffic volume and query '
                                                   'saturation, not recent code changes.'},
                                {'id': 'restart-pods',
                                 'label': 'Reiniciar todos os pods da API',
                                 'label_en': 'Restart all API pods',
                                 'correct': False,
                                 'command': 'kubectl rollout restart deployment/sre-rag-api',
                                 'explanation': '❌ Ineficaz. Reiniciar derruba conexões ativas e esvazia caches '
                                                'quentes, gerando pico de latência ainda maior ao subir.',
                                 'explanation_en': '❌ Ineffective. Restarting drops active sessions and leaves cold '
                                                   'caches, compounding latency.'}],
                  'runbook': '/docs/runbooks/high-latency',
                  'runbook_steps': {'triage': ['Alerta SLOLatencyBurnRateCritical disparado.',
                                               'Grafana: P99 ultrapassa 4000ms na rota /api/v1/query.',
                                               'CPU dos pods da API em 95% de saturação constante.'],
                                    'diagnosis': ['kubectl top pods -l app=sre-rag-api (Pods operando no teto de CPU).',
                                                  "kubectl logs -l app=sre-rag-api | grep 'slow_query' (Consultas SQL "
                                                  'no postgres com tempo > 2000ms).',
                                                  'pg_stat_activity no banco identificando sequential scans na tabela '
                                                  'de documentos.'],
                                    'mitigation': {'action': 'Aumentar réplicas mínimas do HPA para distribuir a '
                                                             'concorrência de CPU.',
                                                   'command': 'kubectl scale hpa sre-rag-api --min=5 --max=20',
                                                   'validation': 'Monitorar queda do P99 para < 450ms no Grafana.'},
                                    'root_cause': {'analysis': 'Aumento de 300% de usuários simultâneos executando '
                                                               'busca semântica sem índice ivfflat/hnsw no pgvector.',
                                                   'permanent_fix': 'Criar índice HNSW vetorial no PostgreSQL e '
                                                                    'configurar cache de embeddings no Redis.'},
                                    'prevention': ['Definir alertas de slow queries no PostgreSQL '
                                                   '(log_min_duration_statement = 500ms).',
                                                   'Ajustar métrica de HPA baseada em requests por segundo (RPS) além '
                                                   'de CPU.']},
                  'concepts': {'resource_title': 'Horizontal Pod Autoscaler (HPA v2) & Saturação de CPU',
                               'architecture_components': ['Metrics Server',
                                                           'Kube-HPA-Controller',
                                                           'SLO Latency Percentiles'],
                               'how_it_works': 'O HPA consulta periodicamente a Metrics API (Metrics Server) '
                                               'calculando: `desiredReplicas = ceil[currentReplicas * '
                                               '(currentMetricValue / targetMetricValue)]`. Ao detectar CPU > 80%, o '
                                               'HPA dispara scale-up no Deployment. Escalar horizontalmente divide as '
                                               'conexões concorrentes, diminuindo o tempo de fila e a latência P99.',
                               'best_practices': ['Nunca monitore apenas a média de latência; os percentis P95 e P99 '
                                                  'revelam a experiência real dos clientes com piores tempos.',
                                                  'Mantenha réplicas suficientes prontas para evitar o atraso de '
                                                  'aquecimento do pod (cold start).',
                                                  'Configure readiness probes para impedir tráfego a pods '
                                                  'recém-criados antes de estarem 100% prontos.'],
                               'golden_signals': ['Latência P99 (Latency P99 ms)',
                                                  'Tráfego Concorrente (Requests/sec)']},
                  'detection_delay_seconds': 45,
                  'investigation_delay_seconds': 90,
                  'chaos_action': None},
 'crashloopbackoff': {'id': 'crashloopbackoff',
                      'title': 'Startup Probe Timeout (Modelo RAG Lento)',
                      'title_en': 'Startup Probe Timeout (Slow Model Loading)',
                      'severity': 'SEV-1',
                      'category': 'Confiabilidade',
                      'category_en': 'Reliability',
                      'difficulty': 'medium',
                      'icon': '🔄',
                      'description': 'Pods recém-implantados demoram 40s para carregar os pesos do modelo vetorial na '
                                     'inicialização, mas a startupProbe tem timeout agressivo de 10s. O Kubelet '
                                     'reinicia o pod em loop infinito.',
                      'description_en': 'New pods require 40s to initialize the local embedding model, but '
                                        'startupProbe has a strict 10s timeout, causing infinite restart loops.',
                      'symptoms': ['kubectl get pods: sre-rag-api-* CrashLoopBackOff (restarts: 6)',
                                   'kubectl describe pod: Startup probe failed: HTTP probe failed with statuscode: 503',
                                   'Zero endpoints no Service (Endpoints: <none>)',
                                   'HTTP 502 Bad Gateway no Ingress'],
                      'symptoms_en': ['kubectl get pods: sre-rag-api-* CrashLoopBackOff (restarts: 6)',
                                      'kubectl describe pod: Startup probe failed: HTTP probe failed with statuscode: '
                                      '503',
                                      'Zero endpoints ready in Service (Endpoints: <none>)',
                                      'HTTP 502 Bad Gateway at ingress level'],
                      'hints': ['Execute `kubectl describe pod` e inspecione a seção de Probes (Startup, Liveness, '
                                'Readiness).',
                                'Aumente o `failureThreshold` da startup probe para permitir até 60 segundos de boot: '
                                '`helm upgrade sre-rag ./helm/sre-rag --set api.probes.startup.failureThreshold=30`.'],
                      'command': 'helm upgrade sre-rag ./helm/sre-rag --set api.probes.startup.failureThreshold=30',
                      'solutions': [{'id': 'adjust-startup-probe',
                                     'label': 'Aumentar failureThreshold da startupProbe para 30 (permitindo 60s de '
                                              'inicialização)',
                                     'label_en': 'Increase startupProbe failureThreshold to 30 (permits 60s '
                                                 'initialization)',
                                     'correct': True,
                                     'command': 'helm upgrade sre-rag ./helm/sre-rag --set '
                                                'api.probes.startup.failureThreshold=30',
                                     'explanation': '✅ Correto! O startupProbe foi criado exatamente para proteger '
                                                    'aplicações de boot lento sem comprometer a rapidez da '
                                                    'livenessProbe em produção.',
                                     'explanation_en': '✅ Correct! Startup probes shield slow-initializing '
                                                       'applications while keeping liveness probes sensitive.'},
                                    {'id': 'disable-probes',
                                     'label': 'Desativar livenessProbe e readinessProbe no deployment',
                                     'label_en': 'Disable readiness and liveness probes in deployment spec',
                                     'correct': False,
                                     'command': 'kubectl patch deployment sre-rag-api --patch '
                                                '\'{"spec":{"template":{"spec":{"containers":[{"name":"api","livenessProbe":null}]}}}}\'',
                                     'explanation': '❌ Anti-pattern grave! Desativar probes remove a capacidade do '
                                                    'Kubernetes de substituir pods travados, piorando a '
                                                    'confiabilidade.',
                                     'explanation_en': '❌ Severe anti-pattern! Disabling probes routes traffic to dead '
                                                       'pods indefinitely.'},
                                    {'id': 'rollback',
                                     'label': 'Rollback imediato da release Helm',
                                     'label_en': 'Immediate rollback via Helm',
                                     'correct': False,
                                     'command': 'helm rollback sre-rag',
                                     'explanation': '⚠️ Ineficaz caso a versão anterior também utilize modelos locais '
                                                    'sem tempo de boot configurado.',
                                     'explanation_en': '⚠️ Ineffective if the prior release also lacks proper startup '
                                                       'probe timeouts.'}],
                      'runbook': '/docs/runbooks/crashloopbackoff',
                      'runbook_steps': {'triage': ['Alerta KubePodCrashLooping no cluster.',
                                                   'Rollout do Deployment travado (0/2 réplicas prontas).',
                                                   'Ingress reportando 502 Bad Gateway por ausência de endpoints.'],
                                        'diagnosis': ['kubectl get pods -l app=sre-rag-api (CrashLoopBackOff).',
                                                      'kubectl describe pod <nome-do-pod> (Warning Unhealthy: Startup '
                                                      'probe failed: HTTP probe failed with statuscode: 503).',
                                                      'kubectl logs <nome-do-pod> (Loading embedding weights: 65% '
                                                      'completo quando recebe SIGTERM).'],
                                        'mitigation': {'action': 'Aumentar o failureThreshold da startup probe para 30 '
                                                                 'no Helm.',
                                                       'command': 'helm upgrade sre-rag ./helm/sre-rag --set '
                                                                  'api.probes.startup.failureThreshold=30',
                                                       'validation': 'kubectl rollout status deployment/sre-rag-api'},
                                        'root_cause': {'analysis': 'Inclusão de modelo de machine learning maior sem '
                                                                   'ajuste correspondente no tempo de tolerância de '
                                                                   'boot.',
                                                       'permanent_fix': 'Aquecer cache de modelos em InitContainer ou '
                                                                        'usar volume compartilhado com pesos '
                                                                        'pré-carregados.'},
                                        'prevention': ['Sempre desacoplar startupProbe de livenessProbe em aplicações '
                                                       'que carregam dados pesados na inicialização.',
                                                       'Testes de carga de boot em pipeline de homologação antes de ir '
                                                       'para produção.']},
                      'concepts': {'resource_title': 'Kubernetes Health Checks: Startup vs Liveness vs Readiness '
                                                     'Probes',
                                   'architecture_components': ['Kubelet Health Monitor',
                                                               'HTTPGetAction',
                                                               'Pod Lifecycle States'],
                                   'how_it_works': 'O Kubelet executa três probes: A `startupProbe` desativa as outras '
                                                   'probes até que ela passe pela primeira vez, protegendo boots '
                                                   'demorados. A `livenessProbe` reinicia o container se ele travar em '
                                                   'deadlock. A `readinessProbe` remove o pod do Service (endpoints) '
                                                   'se ele estiver temporariamente sobrecarregado, sem matá-lo.',
                                   'best_practices': ['Nunca use liveness probe para verificar dependências externas '
                                                      '(como banco de dados fora do pod).',
                                                      'Use startup probe com failureThreshold generoso para evitar '
                                                      'CrashLoopBackOff desnecessário.',
                                                      'Readiness probes devem ser rápidas (< 1s) para responder '
                                                      'prontamente a variações de carga.'],
                                   'golden_signals': ['Disponibilidade de Endpoints (Ready Pods Count)',
                                                      'Tempo de Inicialização de Aplicação (Container Startup '
                                                      'Duration)']},
                      'detection_delay_seconds': 20,
                      'investigation_delay_seconds': 60,
                      'chaos_action': None},
 'ingress-503-endpoints': {'id': 'ingress-503-endpoints',
                           'title': '503 Service Unavailable (Service Selector Mismatch)',
                           'title_en': '503 Service Unavailable (Service Selector Mismatch)',
                           'severity': 'SEV-1',
                           'category': 'Rede',
                           'category_en': 'Network',
                           'difficulty': 'medium',
                           'icon': '🔌',
                           'description': 'O Ingress retorna HTTP 503 Service Unavailable para 100% dos usuários. O '
                                          'Service `sre-rag-api` está com `Endpoints: <none>` porque os labels dos '
                                          'pods foram alterados sem atualizar o selector do Service.',
                           'description_en': 'Ingress returns HTTP 503 to all users. The Service `sre-rag-api` has '
                                             'zero endpoints due to label selector mismatch.',
                           'symptoms': ['HTTP 503 Service Unavailable em todos os domínios externos',
                                        'kubectl get endpoints sre-rag-api: <none>',
                                        "Pods da API estão em 'Running (1/1)' e perfeitamente saudáveis",
                                        'Alertmanager: IngressEmptyEndpoints FIRING'],
                           'symptoms_en': ['HTTP 503 Service Unavailable on all public domains',
                                           'kubectl get endpoints sre-rag-api: <none>',
                                           'API pods are Running (1/1) and healthy internally',
                                           'Alertmanager: IngressEmptyEndpoints FIRING'],
                           'hints': ['Execute `kubectl get endpoints sre-rag-api` e compare os labels dos pods com o '
                                     'selector do serviço.',
                                     'Corrija o selector do Service para apontar para os labels dos pods: `kubectl set '
                                     'selector service sre-rag-api app.kubernetes.io/name=sre-rag-api`.'],
                           'command': 'kubectl set selector service sre-rag-api app.kubernetes.io/name=sre-rag-api',
                           'solutions': [{'id': 'fix-selector',
                                          'label': 'Corrigir selector do Service para '
                                                   '`app.kubernetes.io/name=sre-rag-api`',
                                          'label_en': 'Fix Service selector to match '
                                                      '`app.kubernetes.io/name=sre-rag-api`',
                                          'correct': True,
                                          'command': 'kubectl set selector service sre-rag-api '
                                                     'app.kubernetes.io/name=sre-rag-api',
                                          'explanation': '✅ Correto! O Service utiliza label selectors para encontrar '
                                                         'os pods. Alinhar o selector aos labels dos pods restaura os '
                                                         'endpoints imediatamente.',
                                          'explanation_en': '✅ Correct! Aligning label selectors allows the Kubernetes '
                                                            'controller to bind healthy pod IPs to Service endpoints.'},
                                         {'id': 'restart-ingress',
                                          'label': 'Reiniciar os pods do NGINX Ingress Controller',
                                          'label_en': 'Restart NGINX Ingress Controller pods',
                                          'correct': False,
                                          'command': 'kubectl rollout restart deployment/ingress-nginx-controller -n '
                                                     'ingress-nginx',
                                          'explanation': '❌ Ineficaz. O Ingress está funcionando; o erro 503 ocorre '
                                                         'porque o Service para o qual ele encaminha não possui nenhum '
                                                         'pod vinculado.',
                                          'explanation_en': '❌ Ineffective. The Ingress is healthy; it returns 503 '
                                                            'because the target Service has no endpoints.'},
                                         {'id': 'reboot-nodes',
                                          'label': 'Reiniciar os nós do cluster Kubernetes',
                                          'label_en': 'Reboot all Kubernetes nodes',
                                          'correct': False,
                                          'command': 'kubectl reboot nodes --all',
                                          'explanation': '❌ Absurdo e destrutivo. O problema é puramente um erro '
                                                         'lógico de configuração de label no Service.',
                                          'explanation_en': '❌ Destructive. The issue is a simple logical selector '
                                                            'mismatch.'}],
                           'runbook': '/docs/runbooks/ingress-503-endpoints',
                           'runbook_steps': {'triage': ['Alerta IngressHighHttp5xxRate e IngressEmptyEndpoints.',
                                                        'Usuários recebendo 503 Service Temporarily Unavailable.',
                                                        'Pods da aplicação exibem status Running 1/1.'],
                                             'diagnosis': ['kubectl get endpoints sre-rag-api (ENDPOINTS: <none>).',
                                                           "kubectl get svc sre-rag-api -o jsonpath='{.spec.selector}' "
                                                           '(app=sre-rag-api).',
                                                           'kubectl get pods --show-labels (Labels nos pods: '
                                                           'app.kubernetes.io/name=sre-rag-api).'],
                                             'mitigation': {'action': 'Atualizar o selector do serviço para coincidir '
                                                                      'com o label dos pods.',
                                                            'command': 'kubectl set selector service sre-rag-api '
                                                                       'app.kubernetes.io/name=sre-rag-api',
                                                            'validation': 'kubectl get endpoints sre-rag-api (IPs dos '
                                                                          'pods aparecem listados).'},
                                             'root_cause': {'analysis': 'Refatoração no Helm chart alterou templates '
                                                                        'de Pod para o padrão Kubernetes recomendado '
                                                                        'sem atualizar o Service correspondente.',
                                                            'permanent_fix': 'Adicionar teste automatizado de '
                                                                             'conformance de labels no linter do '
                                                                             'Helm.'},
                                             'prevention': ['Usar _helpers.tpl do Helm para manter labels e selectors '
                                                            'compartilhados de forma padronizada.',
                                                            'Testes end-to-end de fumaça na pipeline validando tráfego '
                                                            'real via Ingress.']},
                           'concepts': {'resource_title': 'Kubernetes Service Discovery, Endpoints & Ingress '
                                                          'Controller',
                                        'architecture_components': ['K8s Endpoints Controller',
                                                                    'CoreDNS',
                                                                    'NGINX Ingress Upstream'],
                                        'how_it_works': 'No Kubernetes, um `Service` atua como uma abstração lógica '
                                                        'para um grupo de Pods. O `EndpointSlice Controller` monitora '
                                                        'o cluster e, via reconciliação contínua, associa os IPs dos '
                                                        'pods saudáveis ao Service através do `spec.selector`. O '
                                                        'Ingress Controller sincroniza dinamicamente sua lista de '
                                                        'upstreams com esses endpoints. Se o selector não casar com os '
                                                        'labels dos pods, a lista fica vazia e o Ingress responde com '
                                                        '503.',
                                        'best_practices': ['Sempre padronize labels conforme os Kubernetes Recommended '
                                                           'Labels (`app.kubernetes.io/name`, '
                                                           '`app.kubernetes.io/instance`).',
                                                           'Monitore a métrica `kube_endpoint_address_available` para '
                                                           'detectar serviços vazios antes dos usuários.',
                                                           'Centralize a geração de labels em templates compartilhados '
                                                           '(`_helpers.tpl`).'],
                                        'golden_signals': ['Endpoints Saudáveis (Available Endpoints Count)',
                                                           'Taxa de HTTP 503 no Ingress (Ingress 503 Upstream Failure '
                                                           'Rate)']},
                           'detection_delay_seconds': 25,
                           'investigation_delay_seconds': 65,
                           'chaos_action': None},
 'hpa-flapping': {'id': 'hpa-flapping',
                  'title': 'HPA Flapping / Thrashing Contínuo',
                  'title_en': 'HPA Thrashing & Flapping Loop',
                  'severity': 'SEV-2',
                  'category': 'Escalabilidade',
                  'category_en': 'Scalability',
                  'difficulty': 'medium',
                  'icon': '📈',
                  'description': 'O Horizontal Pod Autoscaler está oscilando descontroladamente entre 2 e 15 pods a '
                                 'cada 3 minutos. Cada redução de escala sobrecarrega os pods remanescentes e força '
                                 'novo scale-up, gerando instabilidade.',
                  'description_en': 'HPA is oscillating aggressively between 2 and 15 replicas every 3 minutes due to '
                                    'missing scaleDown stabilization window.',
                  'symptoms': ['HPA réplicas pulando de 2 -> 15 -> 2 -> 15 ciclicamente',
                               'Latência intermitente com picos de 3000ms a cada scale-down',
                               'Conexões TCP sendo encerradas abruptamente durante desativação de pods',
                               'Alerta HPAFlappingWarning disparado'],
                  'symptoms_en': ['HPA replicas flapping cyclically from 2 -> 15 -> 2 -> 15',
                                  'Intermittent latency spikes up to 3000ms at every scale-down cycle',
                                  'Abrupt TCP drops during rapid pod terminations',
                                  'Alert HPAFlappingWarning FIRING'],
                  'hints': ['Inspecione o comportamento do HPA com `kubectl describe hpa sre-rag-api`.',
                            'Configure uma janela de estabilização de scale-down de 300 segundos: `kubectl patch hpa '
                            'sre-rag-api --patch '
                            '\'{"spec":{"behavior":{"scaleDown":{"stabilizationWindowSeconds":300}}}}\'`.'],
                  'command': 'kubectl patch hpa sre-rag-api --patch '
                             '\'{"spec":{"behavior":{"scaleDown":{"stabilizationWindowSeconds":300}}}}\'',
                  'solutions': [{'id': 'add-stabilization-window',
                                 'label': 'Adicionar stabilizationWindowSeconds de 300s no scaleDown do HPA',
                                 'label_en': 'Add stabilizationWindowSeconds (300s) to HPA scaleDown behavior',
                                 'correct': True,
                                 'command': 'kubectl patch hpa sre-rag-api --patch '
                                            '\'{"spec":{"behavior":{"scaleDown":{"stabilizationWindowSeconds":300}}}}\'',
                                 'explanation': '✅ Correto! A janela de estabilização impede que o HPA reduza réplicas '
                                                'precipitadamente, suavizando os ciclos e eliminando o flapping.',
                                 'explanation_en': '✅ Correct! The stabilization window suppresses rapid scale-down '
                                                   'decisions, stabilizing cluster state.'},
                                {'id': 'delete-hpa',
                                 'label': 'Deletar o HPA e deixar réplicas fixas em 2',
                                 'label_en': 'Delete HPA and freeze fixed replicas at 2',
                                 'correct': False,
                                 'command': 'kubectl delete hpa sre-rag-api',
                                 'explanation': '❌ Incorreto. Deletar o HPA deixa a aplicação vulnerável a picos de '
                                                'tráfego que causarão indisponibilidade completa.',
                                 'explanation_en': '❌ Incorrect. Deleting autoscaling leaves the service unprotected '
                                                   'against traffic spikes.'},
                                {'id': 'increase-target',
                                 'label': 'Mudar target de CPU para 99%',
                                 'label_en': 'Change CPU target to 99%',
                                 'correct': False,
                                 'command': 'kubectl autoscale deployment sre-rag-api --cpu-percent=99',
                                 'explanation': '❌ Perigoso. Target de 99% fará os pods operarem no limiar de '
                                                'estrangulamento antes de escalar, gerando alta latência.',
                                 'explanation_en': '❌ Dangerous. 99% CPU target delays scaling until pods are already '
                                                   'throttled.'}],
                  'runbook': '/docs/runbooks/hpa-flapping',
                  'runbook_steps': {'triage': ['Alerta HPAFlappingWarning e HighPodChurnRate.',
                                               'Gráfico do Grafana mostrando padrão dente-de-serra no número de '
                                               'réplicas.',
                                               'Picos de latência coincidentes com eventos de terminação de pods.'],
                                    'diagnosis': ['kubectl describe hpa sre-rag-api (Scaling events a cada 90 '
                                                  'segundos).',
                                                  "kubectl get events --sort-by='.lastTimestamp' | grep -i scaledown.",
                                                  'Falta do bloco `behavior.scaleDown.stabilizationWindowSeconds` no '
                                                  'manifesto.'],
                                    'mitigation': {'action': 'Aplicar patch configurando janela de estabilização de 5 '
                                                             'minutos.',
                                                   'command': 'kubectl patch hpa sre-rag-api --patch '
                                                              '\'{"spec":{"behavior":{"scaleDown":{"stabilizationWindowSeconds":300}}}}\'',
                                                   'validation': 'Monitorar estabilidade de réplicas ao longo de 15 '
                                                                 'minutos sem oscilação abrupta.'},
                                    'root_cause': {'analysis': 'Configuração padrão do HPA sem damping em workloads '
                                                               'com bursts rápidos de consultas vetoriais.',
                                                   'permanent_fix': 'Definir políticas de escala completas no Helm '
                                                                    'chart com taxas máximas de scaleDown.'},
                                    'prevention': ['Combinar métricas de CPU com métricas de negócio (RPS ou contagem '
                                                   'de conexões).',
                                                   'Implementar terminationGracePeriodSeconds adequado e preStop hooks '
                                                   'para drenar conexões antes do encerramento.']},
                  'concepts': {'resource_title': 'HPA v2 Behavior: Stabilization Windows & Rate Limiting de Escala',
                               'architecture_components': ['HPA Controller',
                                                           'ScaleDown Damping',
                                                           'preStop Hooks & Graceful Shutdown'],
                               'how_it_works': 'O autoscaler recalcula réplicas a cada '
                                               '`horizontal-pod-autoscaler-sync-period` (padrão 15s). Sem uma janela '
                                               'de estabilização (`stabilizationWindowSeconds`), um alívio momentâneo '
                                               'de CPU dispara o corte imediato de pods. Ao desligar réplicas, a carga '
                                               'remanescente satura os pods sobreviventes, disparando novo scale-up. A '
                                               'janela de estabilização calcula o valor máximo de réplicas '
                                               'recomendadas no período antes de executar o scale-down.',
                               'best_practices': ['Configure `stabilizationWindowSeconds: 300` (5 minutos) para '
                                                  'scaleDown em sistemas com tráfego oscilante.',
                                                  'Sempre combine HPA com `terminationGracePeriodSeconds` e `preStop: '
                                                  'sleep 10` para dar tempo aos Ingress controllers de desregistrar o '
                                                  'pod.',
                                                  'Adote Pod Disruption Budgets (PDB) para garantir réplicas mínimas '
                                                  'disponíveis durante manutenções.'],
                               'golden_signals': ['Taxa de Criação/Morte de Pods (Pod Churn Rate)',
                                                  'Variação de Réplicas (HPA Replicas Variance)']},
                  'detection_delay_seconds': 30,
                  'investigation_delay_seconds': 75,
                  'chaos_action': None},
 'tls-expiring': {'id': 'tls-expiring',
                  'title': 'Certificado TLS Próximo do Vencimento',
                  'title_en': 'TLS Certificate Expiring Soon',
                  'severity': 'SEV-3',
                  'category': 'Segurança',
                  'category_en': 'Security',
                  'difficulty': 'hard',
                  'icon': '🔒',
                  'description': 'O certificado TLS do Ingress expira em menos de 48 horas. A renovação automática '
                                 'pelo cert-manager falhou devido a falta de anotação do ClusterIssuer no Ingress.',
                  'description_en': 'Ingress TLS certificate expires in under 48 hours. Cert-manager auto-renewal '
                                    'stalled due to missing ClusterIssuer ingress annotations.',
                  'symptoms': ['Alertmanager: TLSCertificateExpiringSoon disparado (< 48h)',
                               'Secret tls-cert não é atualizada há 88 dias',
                               'Navegadores começarão a exibir aviso de segurança em 48h',
                               'kubectl get cert: Ready=False (IssuerNotFound)'],
                  'symptoms_en': ['Alertmanager: TLSCertificateExpiringSoon firing (< 48h)',
                                  'Secret tls-cert not renewed for 88 days',
                                  'User browsers facing security warning within 48h',
                                  'kubectl get cert: Ready=False (IssuerNotFound)'],
                  'hints': ['Inspecione o status do certificado com `kubectl get cert` e `kubectl describe '
                            'certificate`.',
                            "Aponte o Ingress para o ClusterIssuer do Let's Encrypt: `kubectl annotate ingress sre-rag "
                            'cert-manager.io/cluster-issuer=letsencrypt-prod --overwrite`.'],
                  'command': 'kubectl annotate ingress sre-rag cert-manager.io/cluster-issuer=letsencrypt-prod '
                             '--overwrite',
                  'solutions': [{'id': 'annotate-ingress',
                                 'label': 'Anotar o Ingress com `cert-manager.io/cluster-issuer=letsencrypt-prod`',
                                 'label_en': 'Annotate Ingress with `cert-manager.io/cluster-issuer=letsencrypt-prod`',
                                 'correct': True,
                                 'command': 'kubectl annotate ingress sre-rag '
                                            'cert-manager.io/cluster-issuer=letsencrypt-prod --overwrite',
                                 'explanation': '✅ Correto! O cert-manager detecta a anotação no Ingress, executa o '
                                                'challenge ACME HTTP-01 e renova o certificado TLS automaticamente.',
                                 'explanation_en': '✅ Correct! Ingress annotation triggers cert-manager ACME '
                                                   'validation and reissues the TLS certificate.'},
                                {'id': 'self-signed',
                                 'label': 'Substituir por certificado autoassinado temporário',
                                 'label_en': 'Replace with temporary self-signed certificate',
                                 'correct': False,
                                 'command': 'openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days '
                                            '365',
                                 'explanation': '❌ Inaceitável para produção. Certificados autoassinados provocam tela '
                                                'de alerta de segurança grave aos usuários finais.',
                                 'explanation_en': '❌ Production violation. Self-signed certificates produce browser '
                                                   'security warnings.'},
                                {'id': 'disable-tls',
                                 'label': 'Desativar TLS e usar apenas HTTP porta 80',
                                 'label_en': 'Disable TLS and run HTTP plain text on port 80',
                                 'correct': False,
                                 'command': 'kubectl patch ingress sre-rag --type json -p \'[{"op": "remove", "path": '
                                            '"/spec/tls"}]\'',
                                 'explanation': '❌ Violação grave de segurança e compliance. Tráfego em texto puro '
                                                'expõe senhas e dados dos usuários a interceptação.',
                                 'explanation_en': '❌ Severe compliance and security breach.'}],
                  'runbook': '/docs/runbooks/tls-expiring',
                  'runbook_steps': {'triage': ['Alerta TLSCertificateExpiringSoon (< 48 horas restantes).',
                                               'Dashboard de certificados TLS com status de renovação em erro.',
                                               'Validação de rota HTTPS acusando expiração iminente.'],
                                    'diagnosis': ['kubectl get cert -n sre-rag (Status: Ready=False, '
                                                  'Secret=sre-rag-tls-cert).',
                                                  'kubectl describe certificate sre-rag-tls-cert (Events: Issuer '
                                                  'letsencrypt-prod not found).',
                                                  'kubectl get ingress sre-rag -o yaml (Falta da anotação '
                                                  'cert-manager.io/cluster-issuer).'],
                                    'mitigation': {'action': 'Anotar o Ingress para acionar a renovação automática '
                                                             'pelo cert-manager.',
                                                   'command': 'kubectl annotate ingress sre-rag '
                                                              'cert-manager.io/cluster-issuer=letsencrypt-prod '
                                                              '--overwrite',
                                                   'validation': 'kubectl get certificate sre-rag-tls-cert -w '
                                                                 '(Aguardar Ready: True).'},
                                    'root_cause': {'analysis': 'Anotação de cluster-issuer foi omitida durante a '
                                                               'migração de ingress controllers.',
                                                   'permanent_fix': 'Fixar a anotação no template Helm do Ingress nos '
                                                                    'values padrões.'},
                                    'prevention': ['Alertas proativos com 30, 15 e 7 dias de antecedência para '
                                                   'renovação de TLS.',
                                                   'Monitoramento de métricas do cert-manager '
                                                   '(certmanager_certificate_expiration_timestamp_seconds).']},
                  'concepts': {'resource_title': 'Infraestrutura de Chaves Públicas (PKI), Cert-Manager & ACME '
                                                 'Challenges',
                               'architecture_components': ['Cert-Manager Controller',
                                                           'ACME HTTP-01 Solver',
                                                           "Let's Encrypt CA"],
                               'how_it_works': 'O cert-manager estende a API do Kubernetes via Custom Resource '
                                               'Definitions (CRDs). Ao detectar um Ingress anotado, o cert-manager '
                                               'cria recursos de `Certificate`, `CertificateRequest` e `Order`. Para '
                                               "validar a posse do domínio junto ao Let's Encrypt, ele cria um Pod "
                                               'temporário e regras no Ingress para responder o desafio ACME em '
                                               '`/.well-known/acme-challenge/*`. Após a validação, a CA assina o '
                                               'certificado que é gravado como Secret TLS.',
                               'best_practices': ['Nunca deixe a renovação para as últimas 48h; configure '
                                                  '`renewBefore: 720h` (30 dias antes).',
                                                  'Sempre utilize ClusterIssuers de staging para testes em homologação '
                                                  "para não atingir o rate limit do Let's Encrypt.",
                                                  'Monitore a validade de certificados usando blackbox exporter do '
                                                  'Prometheus.'],
                               'golden_signals': ['Dias Restantes de Validade TLS (Days Until Expiry)',
                                                  'Taxa de Sucesso de Desafios ACME (ACME Challenge Success Rate)']},
                  'detection_delay_seconds': 60,
                  'investigation_delay_seconds': 120,
                  'chaos_action': None},
 'disk-pressure': {'id': 'disk-pressure',
                   'title': 'DiskPressure em Node do Kubernetes',
                   'title_en': 'Node DiskPressure Eviction',
                   'severity': 'SEV-2',
                   'category': 'Armazenamento',
                   'category_en': 'Storage',
                   'difficulty': 'hard',
                   'icon': '💾',
                   'description': 'Um nó worker entrou em condição DiskPressure (> 85% de uso no disco raiz). O '
                                  'Kubelet começou a evictar pods não críticos para proteger o sistema operacional de '
                                  'um congelamento do kernel.',
                   'description_en': 'Worker node entered DiskPressure condition (> 85% disk utilization). Kubelet '
                                     'started evicting pods to protect kernel operation.',
                   'symptoms': ['kubectl get nodes: Status = Ready,DiskPressure',
                                'Kubelet: eviction manager threshold met on /var/lib/docker',
                                'Pods secundários sendo evictados (Evicted); novos pods Pending',
                                'Disco raiz do nó atingiu 88% de utilização'],
                   'symptoms_en': ['kubectl get nodes: Status = Ready,DiskPressure',
                                   'Kubelet: eviction threshold met on container filesystem',
                                   'Pods evicted; newly scheduled pods enter Pending state',
                                   'Root filesystem utilization at 88%'],
                   'hints': ['Verifique o estado dos nós do cluster com `kubectl get nodes` e inspecione as '
                             'Conditions.',
                             'Limpe imagens de container órfãs e logs acumulados no nó afetado: `crictl rmi --prune`.'],
                   'command': 'crictl rmi --prune',
                   'solutions': [{'id': 'prune-images-logs',
                                  'label': 'Executar `crictl rmi --prune` para remover imagens não utilizadas e '
                                           'liberar disco',
                                  'label_en': 'Run `crictl rmi --prune` to purge unused container images and recover '
                                              'disk',
                                  'correct': True,
                                  'command': 'crictl rmi --prune',
                                  'explanation': '✅ Correto! Limpar imagens de containers obsoletas e rotacionar logs '
                                                 'de pods libera espaço imediatamente, removendo a condição '
                                                 'DiskPressure do nó.',
                                  'explanation_en': '✅ Correct! Cleaning stale container images instantly recovers '
                                                    'disk space and clears the taint.'},
                                 {'id': 'delete-node',
                                  'label': 'Deletar o nó do cluster imediatamente (`kubectl delete node`)',
                                  'label_en': 'Delete node immediately from the cluster',
                                  'correct': False,
                                  'command': 'kubectl delete node node-1',
                                  'explanation': '⚠️ Drástico e desnecessário. A limpeza de disco é rápida e resolve o '
                                                 'problema sem forçar reagendamento em massa de pods.',
                                  'explanation_en': '⚠️ Excessive. Disk cleanup is fast and avoids cascading '
                                                    'rescheduling pressure.'},
                                 {'id': 'ignore-taint',
                                  'label': 'Adicionar tolerations para DiskPressure em todos os pods',
                                  'label_en': 'Add tolerations for DiskPressure to all application pods',
                                  'correct': False,
                                  'command': 'kubectl patch deployment sre-rag-api --patch '
                                             '\'{"spec":{"template":{"spec":{"tolerations":[{"key":"node.kubernetes.io/disk-pressure","operator":"Exists"}]}}}}\'',
                                  'explanation': '❌ Perigoso. Se o disco atingir 100%, o nó inteiro trava, o '
                                                 'filesystem pode corromper e o nó deixa de responder (NotReady).',
                                  'explanation_en': '❌ Dangerous. If disk fills to 100%, node kernel freezes and '
                                                    'filesystem corruption ensues.'}],
                   'runbook': '/docs/runbooks/disk-pressure',
                   'runbook_steps': {'triage': ['Alerta KubeNodeDiskPressure disparado no Prometheus.',
                                                "Pods com status 'Evicted' acumulando no namespace.",
                                                'Kubelet aplicando taint node.kubernetes.io/disk-pressure:NoSchedule.'],
                                     'diagnosis': ['kubectl get nodes (Condition: DiskPressure = True).',
                                                   'kubectl describe node <node-name> (Eviction threshold met on '
                                                   'rootfs /var/lib/containerd).',
                                                   'ssh no nó ou container debug: df -h /var/lib/docker (88% '
                                                   'ocupado).'],
                                     'mitigation': {'action': 'Executar limpeza de imagens não utilizadas pelo '
                                                              'container runtime.',
                                                    'command': 'crictl rmi --prune',
                                                    'validation': 'kubectl describe node <node-name> (Condition: '
                                                                  'DiskPressure = False).'},
                                     'root_cause': {'analysis': 'Acúmulo de imagens de builds temporários antigos sem '
                                                                'política de garbage collection agressiva no Kubelet.',
                                                    'permanent_fix': 'Configurar Kubelet flags '
                                                                     '`--image-gc-high-threshold=80` e '
                                                                     '`--image-gc-low-threshold=60`.'},
                                     'prevention': ['Monitorar espaço em disco dos nós com alerta de tendência '
                                                    'predict_linear em 6 horas.',
                                                    'Separar discos de dados persistentes (/var/lib/kubelet) do disco '
                                                    'do sistema operacional.']},
                   'concepts': {'resource_title': 'Kubelet Eviction Manager, Node Conditions & Image Garbage '
                                                  'Collection',
                                'architecture_components': ['Kubelet Eviction Manager',
                                                            'CRI (containerd / crictl)',
                                                            'DiskPressure Taints'],
                                'how_it_works': 'O Kubelet monitora periodicamente os limites de disco do nó. Quando o '
                                                'uso ultrapassa o threshold de evicção (padrão 85%), o Kubelet ativa a '
                                                'condição `DiskPressure` e aplica a taint '
                                                '`node.kubernetes.io/disk-pressure:NoSchedule`. Para recuperar espaço, '
                                                'o Kubelet tenta primeiro deletar imagens de containers não '
                                                'utilizadas. Se o espaço continuar crítico, o Eviction Manager encerra '
                                                'pods com base na classe de QoS até que o disco volte abaixo do limite '
                                                'seguro.',
                                'best_practices': ['Configure image garbage collection agressivo em ambientes com '
                                                   'pipelines de CI/CD contínuos.',
                                                   'Mantenha logs dos containers em partição separada ou encaminhe em '
                                                   'streaming para agente de logging (FluentBit / Vector).',
                                                   'Configure alertas de saturação de disco em 70% e 80% antes de '
                                                   'atingir o limite de evicção.'],
                                'golden_signals': ['Uso de Disco do Nó (Node Root Filesystem %)',
                                                   'Taxa de Evicção de Pods (Pod Eviction Rate)']},
                   'detection_delay_seconds': 50,
                   'investigation_delay_seconds': 100,
                   'chaos_action': None},
 'pvc-mount-deadlock': {'id': 'pvc-mount-deadlock',
                        'title': 'PVC Deadlock (Multi-Attach Error em RWO)',
                        'title_en': 'PVC Deadlock (Multi-Attach Error on RWO Volume)',
                        'severity': 'SEV-2',
                        'category': 'Armazenamento',
                        'category_en': 'Storage',
                        'difficulty': 'hard',
                        'icon': '🗄️',
                        'description': "O pod de persistência está preso em ContainerCreating com erro 'Multi-Attach "
                                       "error for volume: Volume is already exclusively attached to node-1'. O nó "
                                       'anterior travou mas o CSI driver não liberou o VolumeAttachment.',
                        'description_en': "Stateful pod stuck in ContainerCreating with 'Multi-Attach error for "
                                          "volume'. Stale node crashed and CSI driver failed to release the "
                                          'VolumeAttachment.',
                        'symptoms': ['kubectl get pods: sre-rag-db-0 ContainerCreating',
                                     'kubectl describe pod: Multi-Attach error for volume: Volume is already '
                                     'exclusively attached',
                                     'VolumeAttachment órfão impedindo montagem no novo nó',
                                     'Banco de dados indisponível, derrubando endpoints dependentes'],
                        'symptoms_en': ['kubectl get pods: sre-rag-db-0 ContainerCreating',
                                        'kubectl describe pod: Multi-Attach error for volume: Volume is already '
                                        'exclusively attached',
                                        'Stale VolumeAttachment blocking attach to the healthy node',
                                        'Database unavailable, impacting all reliant services'],
                        'hints': ['Inspecione os recursos de VolumeAttachment com `kubectl get volumeattachment`.',
                                  'Force a remoção do VolumeAttachment órfão: `kubectl delete volumeattachment '
                                  "$(kubectl get volumeattachment -o jsonpath='{.items[0].metadata.name}') --force`."],
                        'command': 'kubectl delete volumeattachment $(kubectl get volumeattachment -o '
                                   "jsonpath='{.items[0].metadata.name}') --force",
                        'solutions': [{'id': 'force-delete-attachment',
                                       'label': 'Deletar o VolumeAttachment órfão com flag `--force`',
                                       'label_en': 'Force-delete the stale VolumeAttachment resource',
                                       'correct': True,
                                       'command': 'kubectl delete volumeattachment $(kubectl get volumeattachment -o '
                                                  "jsonpath='{.items[0].metadata.name}') --force",
                                       'explanation': '✅ Correto! Deletar o VolumeAttachment órfão destrava o CSI '
                                                      'attach/detach controller, permitindo anexar o disco RWO com '
                                                      'segurança ao novo nó.',
                                       'explanation_en': '✅ Correct! Deleting the stuck VolumeAttachment unlocks the '
                                                         'CSI controller to mount the RWO volume onto the healthy '
                                                         'node.'},
                                      {'id': 'delete-pvc',
                                       'label': 'Deletar o PersistentVolumeClaim (`kubectl delete pvc`)',
                                       'label_en': 'Delete the PersistentVolumeClaim (`kubectl delete pvc`)',
                                       'correct': False,
                                       'command': 'kubectl delete pvc data-sre-rag-db-0',
                                       'explanation': '❌ Perigo crítico de perda de dados! Deletar o PVC pode apagar o '
                                                      'volume persistente subjacente e destruir o banco de dados.',
                                       'explanation_en': '❌ Extreme danger! Deleting PVC may destroy the underlying '
                                                         'storage and lose all data.'},
                                      {'id': 'change-access-mode',
                                       'label': 'Alterar o volume para ReadWriteMany sem suporte da nuvem',
                                       'label_en': 'Change access mode to ReadWriteMany without cloud support',
                                       'correct': False,
                                       'command': 'kubectl patch pv pv-data --patch '
                                                  '\'{"spec":{"accessModes":["ReadWriteMany"]}}\'',
                                       'explanation': '❌ Inválido. Block storages (EBS, Persistent Disk) não suportam '
                                                      'ReadWriteMany sem sistemas de arquivos de rede (NFS, CephFS).',
                                       'explanation_en': '❌ Invalid. Block storage providers do not natively support '
                                                         'ReadWriteMany.'}],
                        'runbook': '/docs/runbooks/pvc-mount-deadlock',
                        'runbook_steps': {'triage': ['Alerta VolumeAttachmentStuck / KubePodCrashWaiting.',
                                                     'Pod com volume persistente preso em ContainerCreating por > 10 '
                                                     'minutos.',
                                                     'Eventos FailedAttachVolume reportados pelo Kubelet.'],
                                          'diagnosis': ['kubectl get pods -l app=sre-rag-db (Status: '
                                                        'ContainerCreating).',
                                                        'kubectl describe pod sre-rag-db-0 (Multi-Attach error: Volume '
                                                        'is already exclusively attached to node-1).',
                                                        'kubectl get volumeattachment (Status do attachment preso em '
                                                        'Attached=true no nó offline).'],
                                          'mitigation': {'action': 'Deletar o recurso VolumeAttachment órfão com '
                                                                   '--force.',
                                                         'command': 'kubectl delete volumeattachment $(kubectl get '
                                                                    'volumeattachment -o '
                                                                    "jsonpath='{.items[0].metadata.name}') --force",
                                                         'validation': 'kubectl get pods (Verificar transição para '
                                                                       'Running em até 30 segundos).'},
                                          'root_cause': {'analysis': 'Falha de hardware no nó worker-1 fez o kubelet '
                                                                     'parar sem notificar o controller-manager sobre o '
                                                                     'desanexamento do volume EBS/GPD.',
                                                         'permanent_fix': 'Configurar node-fencing automático e '
                                                                          'atualizar os CSI drivers da nuvem para '
                                                                          'versões com timeout agressivo de detach.'},
                                          'prevention': ['Usar StorageClasses com `volumeBindingMode: '
                                                         'WaitForFirstConsumer`.',
                                                         'Testes de caos simulando parada forçada de nó com volumes '
                                                         'persistentes para validar recuperação automática.']},
                        'concepts': {'resource_title': 'Kubernetes Storage: CSI Drivers, VolumeAttachment & Modos de '
                                                       'Acesso RWO',
                                     'architecture_components': ['CSI Attach/Detach Controller',
                                                                 'VolumeAttachment CRD',
                                                                 'StorageClass Access Modes'],
                                     'how_it_works': 'Volumes `ReadWriteOnce (RWO)` só podem ser montados por um único '
                                                     'nó por vez para prevenir corrupção no filesystem. O `CSI '
                                                     'attach/detach controller` cria um objeto `VolumeAttachment` para '
                                                     'coordenar com a API do provedor de nuvem (ex: AWS EBS attach). '
                                                     'Se um nó morre de forma abrupta, o control plane mantém o lock '
                                                     'até o timeout de fencing para evitar split-brain no disco. O pod '
                                                     'no novo nó fica bloqueado até o release desse lock.',
                                     'best_practices': ['Sempre use StatefulSets para workloads que exigem '
                                                        'persistência com volumes dedicados.',
                                                        'Mantenha snapshots regulares dos Persistent Volumes via '
                                                        'VolumeSnapshot CRD.',
                                                        'Garanta que o CSI driver do cluster esteja atualizado com '
                                                        'suporte a force-detach seguro.'],
                                     'golden_signals': ['Tempo de Montagem de Volumes (Volume Attach Latency)',
                                                        'Falhas de Montagem de Armazenamento (Storage Mount Errors)']},
                        'detection_delay_seconds': 35,
                        'investigation_delay_seconds': 80,
                        'chaos_action': None},
 'cpu-throttling': {'id': 'cpu-throttling',
                    'title': 'Severe CFS CPU Throttling (Latência Fantasma)',
                    'title_en': 'Severe CFS CPU Throttling (Ghost Latency)',
                    'severity': 'SEV-2',
                    'category': 'Desempenho',
                    'category_en': 'Performance',
                    'difficulty': 'hard',
                    'icon': '⏱️',
                    'description': 'A latência da API subiu para 1.8s nos percentis P95 e P99, mas o uso médio de CPU '
                                   'exibido no Grafana é de apenas 28%. O Completely Fair Scheduler (CFS) do Linux '
                                   'está aplicando throttling de 80% nos ciclos de 100ms devido a um CPU limit rígido '
                                   'muito baixo (500m).',
                    'description_en': 'P99 latency spiked to 1.8s despite average CPU usage showing only 28%. Linux '
                                      'CFS is enforcing 80% quota throttling due to tight 500m CPU limits.',
                    'symptoms': ['P99 latency: 1800ms (SLO violado sob carga moderada)',
                                 'Uso médio de CPU do pod em apenas 28% nos dashboards',
                                 'cgroup cpu.stat: throttled_periods > 75% dos períodos',
                                 'Alertmanager: ContainerHighCPUThrottling FIRING'],
                    'symptoms_en': ['P99 latency: 1800ms (SLO violated under moderate load)',
                                    'Average CPU utilization shows merely 28% in dashboards',
                                    'cgroup cpu.stat: throttled_periods > 75% of periods',
                                    'Alertmanager: ContainerHighCPUThrottling FIRING'],
                    'hints': ['Inspecione as métricas de throttling no cgroup do container via `cat '
                              '/sys/fs/cgroup/cpu/cpu.stat`.',
                              'Remova o hard limit de CPU para eliminar o throttling do CFS: `helm upgrade sre-rag '
                              './helm/sre-rag --set api.resources.limits.cpu=null --reuse-values`.'],
                    'command': 'helm upgrade sre-rag ./helm/sre-rag --set api.resources.limits.cpu=null --reuse-values',
                    'solutions': [{'id': 'remove-cpu-limit',
                                   'label': 'Remover o hard limit de CPU (`limits.cpu=null`) mantendo requests '
                                            'adequados',
                                   'label_en': 'Remove hard CPU limit (`limits.cpu=null`) while keeping proper '
                                               'requests',
                                   'correct': True,
                                   'command': 'helm upgrade sre-rag ./helm/sre-rag --set api.resources.limits.cpu=null '
                                              '--reuse-values',
                                   'explanation': '✅ Correto! A recomendação moderna da comunidade de SRE e Kubernetes '
                                                  'é não fixar CPU limits para microsserviços sensíveis a latência, '
                                                  'permitindo bursts sem penalidade do CFS.',
                                   'explanation_en': '✅ Correct! Removing CPU limits eliminates CFS scheduler stalls '
                                                     'during multi-threaded bursts.'},
                                  {'id': 'double-replicas',
                                   'label': 'Dobrar as réplicas mantendo o mesmo CPU limit',
                                   'label_en': 'Double replicas while retaining strict CPU limit',
                                   'correct': False,
                                   'command': 'kubectl scale deployment sre-rag-api --replicas=6',
                                   'explanation': '❌ Ineficiente. Se threads individuais sofrem burst durante '
                                                  'processamento de requisição, o CFS estrangula o processo mesmo com '
                                                  'múltiplos pods ociosos.',
                                   'explanation_en': '❌ Inefficient. Multi-threaded bursts will still get throttled '
                                                     'per-pod regardless of replica count.'},
                                  {'id': 'lower-requests',
                                   'label': 'Diminuir os requests de CPU para 100m',
                                   'label_en': 'Lower CPU requests to 100m',
                                   'correct': False,
                                   'command': 'helm upgrade sre-rag ./helm/sre-rag --set '
                                              'api.resources.requests.cpu=100m',
                                   'explanation': '❌ Piora o problema. Reduzir requests enfraquece a garantia de '
                                                  'recursos concedida pelo Kube-Scheduler aos nós.',
                                   'explanation_en': '❌ Makes it worse by weakening resource scheduling guarantees.'}],
                    'runbook': '/docs/runbooks/cpu-throttling',
                    'runbook_steps': {'triage': ['Alerta ContainerHighCPUThrottling (> 50% dos períodos '
                                                 'estrangulados).',
                                                 'P99 de latência degradado enquanto métricas médias de CPU parecem '
                                                 'baixas.',
                                                 'Fila de requisições acumulando no proxy reverso.'],
                                      'diagnosis': ['kubectl top pods -l app=sre-rag-api (CPU média em 280m de 1000m).',
                                                    'cat /sys/fs/cgroup/cpu/cpu.stat (nr_throttled / nr_periods > '
                                                    '70%).',
                                                    'PromQL: sum(rate(container_cpu_cfs_throttled_seconds_total[5m])) '
                                                    'by (pod).'],
                                      'mitigation': {'action': 'Remover o limite rígido de CPU no Helm, mantendo os '
                                                               'requests intactos.',
                                                     'command': 'helm upgrade sre-rag ./helm/sre-rag --set '
                                                                'api.resources.limits.cpu=null --reuse-values',
                                                     'validation': 'Monitorar queda imediata de '
                                                                   'container_cpu_cfs_throttled_periods para zero.'},
                                      'root_cause': {'analysis': 'A aplicação utiliza pool multi-thread em '
                                                                 'Python/FastAPI. Em rajadas rápidas de 10ms, todas as '
                                                                 'threads disparam em paralelo, consumindo a cota de '
                                                                 '100ms do CFS e ficando congeladas pelo resto da '
                                                                 'janela.',
                                                     'permanent_fix': 'Adotar padrão No-CPU-Limits recomendado por '
                                                                      'engenheiros do Google e CERN para '
                                                                      'microsserviços.'},
                                      'prevention': ['Dashboard do Grafana monitorando expressamente métricas de CFS '
                                                     'Throttling em percentuais.',
                                                     'Configurar CPU requests dimensionados com base no percentil 95 '
                                                     'de carga.']},
                    'concepts': {'resource_title': 'Linux CFS (Completely Fair Scheduler), Cgroups & CPU Quotas',
                                 'architecture_components': ['Linux CFS Quota / Period',
                                                             'cgroup cpu.cfs_quota_us',
                                                             'CPU Limits vs Throttling'],
                                 'how_it_works': 'Ao definir `limits.cpu: 500m`, o Kubelet configura no cgroup do '
                                                 'container: `cpu.cfs_period_us = 100000` (100ms) e `cpu.cfs_quota_us '
                                                 '= 50000` (50ms). Se o container possui 4 threads ativas que consomem '
                                                 '15ms de CPU cada uma dentro de um período (total = 60ms), ele excede '
                                                 'a cota de 50ms antes da metade da janela. O kernel Linux congela '
                                                 'forçadamente todas as threads do container até o início da próxima '
                                                 "janela de 100ms, introduzindo 'latência fantasma'.",
                                 'best_practices': ['Considere remover `limits.cpu` (definir apenas `requests.cpu`) '
                                                    'para aplicações em linguagens com suporte a paralelismo/threads.',
                                                    'Se for obrigado por governança a usar CPU limits, dimensione o '
                                                    'limite com no mínimo 3x o valor do request.',
                                                    'Monitore `container_cpu_cfs_throttled_periods_total` para auditar '
                                                    'penalidades de escalonamento.'],
                                 'golden_signals': ['Percentual de CFS Throttling (CFS Throttled Periods %)',
                                                    'Latência de Processamento P99 (P99 Queue & Processing Latency)']},
                    'detection_delay_seconds': 40,
                    'investigation_delay_seconds': 85,
                    'chaos_action': None},
 'redis-exhausted': {'id': 'redis-exhausted',
                     'title': 'Redis Connection Exhaustion (maxclients 10k)',
                     'title_en': 'Redis Connection Pool Exhaustion',
                     'severity': 'SEV-1',
                     'category': 'Desempenho',
                     'category_en': 'Performance',
                     'difficulty': 'extreme',
                     'icon': '🔴',
                     'description': 'O Redis atingiu o limite de maxclients (10.000 conexões ativas). Novas conexões '
                                    "da API falham com 'ERR max number of clients reached'. Consultas ao RAG falham "
                                    'por timeout de cache.',
                     'description_en': 'Redis maxclients limit reached (10,000 connections). Application threads '
                                       'hanging on connection timeouts, escalating response latency across all '
                                       'endpoints.',
                     'symptoms': ['Redis INFO: connected_clients = 10000 (maxclients atingido)',
                                  'App logs: redis.exceptions.ConnectionError: Too many connections',
                                  'Muitas conexões em estado CLOSE_WAIT nos pods da API',
                                  'Latência de consulta subiu de 20ms para 5000ms (timeout)'],
                     'symptoms_en': ['Redis logs: ERR max number of clients reached (10000/10000)',
                                     'Application logs: redis.exceptions.ConnectionError: Too many connections',
                                     'TCP connections in CLOSE_WAIT state accumulating on API pods',
                                     'Cache latency spiking from 1ms to 5000ms (timeout)'],
                     'hints': ['Verifique o número de clientes conectados no Redis via `redis-cli info clients`.',
                               'Configure o ConnectionPool e timeout de ociosidade no deployment: `kubectl set env '
                               'deployment/sre-rag-api REDIS_MAX_CONNECTIONS=100 REDIS_TIMEOUT=30`.'],
                     'command': 'kubectl set env deployment/sre-rag-api REDIS_MAX_CONNECTIONS=100 REDIS_TIMEOUT=30',
                     'solutions': [{'id': 'fix-connection-pool',
                                    'label': 'Configurar ConnectionPool no cliente Redis com max_connections e timeout',
                                    'label_en': 'Configure connection pool limits on API + enable Redis timeout idle '
                                                'clients',
                                    'correct': True,
                                    'command': 'kubectl set env deployment/sre-rag-api REDIS_MAX_CONNECTIONS=100 '
                                               'REDIS_TIMEOUT=30',
                                    'explanation': '✅ Correto! A aplicação criava uma nova conexão TCP por request sem '
                                                   'pool. O ConnectionPool reutiliza conexões e limita o teto máximo, '
                                                   'eliminando o vazamento.',
                                    'explanation_en': '✅ Correct! Reusing connections with a bounded pool and timing '
                                                      'out idle clients mitigates leak completely.'},
                                   {'id': 'restart-redis',
                                    'label': 'Reiniciar o pod do Redis',
                                    'label_en': 'Restart Redis StatefulSet pod',
                                    'correct': False,
                                    'command': 'kubectl delete pod redis-0',
                                    'explanation': '⚠️ Mitigação temporária. Reiniciar derruba as 10k conexões, mas a '
                                                   'aplicação vazará conexões novamente em poucos minutos.',
                                    'explanation_en': '⚠️ Temporary workaround; connections will saturate again within '
                                                      'minutes.'},
                                   {'id': 'disable-cache',
                                    'label': 'Desativar o Redis e fazer todas as queries diretamente no PostgreSQL',
                                    'label_en': 'Disable Redis cache completely and query PostgreSQL directly',
                                    'correct': False,
                                    'command': 'kubectl set env deployment/sre-rag-api ENABLE_CACHE=false',
                                    'explanation': '❌ Transfere todo o tráfego de leitura para o banco relacional, '
                                                   'sobrecarregando o PostgreSQL e gerando um incidente cascata ainda '
                                                   'pior.',
                                    'explanation_en': '❌ Transfers all read load to PostgreSQL, inducing a cascade '
                                                      'database collapse.'}],
                     'runbook': '/docs/runbooks/redis-exhausted',
                     'runbook_steps': {'triage': ['Alerta RedisTooManyConnections (connected_clients >= 9900).',
                                                  'Aumento abrupto de erros 500 em endpoints dependentes de cache.',
                                                  'Latência de comunicação com Redis explodindo para 5000ms.'],
                                       'diagnosis': ['kubectl exec -it sts/redis-0 -- redis-cli info clients '
                                                     '(connected_clients: 10000).',
                                                     'netstat -an | grep 6379 (Milhares de sockets em estado '
                                                     'ESTABLISHED e CLOSE_WAIT).',
                                                     'Logs da aplicação: redis.exceptions.ConnectionError: ERR max '
                                                     'number of clients reached.'],
                                       'mitigation': {'action': 'Configurar variáveis de ambiente na API limitando '
                                                                'conexões simultâneas e ativando idle timeout.',
                                                      'command': 'kubectl set env deployment/sre-rag-api '
                                                                 'REDIS_MAX_CONNECTIONS=100 REDIS_TIMEOUT=30',
                                                      'validation': 'kubectl exec -it sts/redis-0 -- redis-cli info '
                                                                    'clients (connected_clients recua para < 300).'},
                                       'root_cause': {'analysis': 'Código criava `redis.Redis()` diretamente dentro da '
                                                                  'rota FastAPI sem usar singleton de '
                                                                  '`redis.ConnectionPool`.',
                                                      'permanent_fix': 'Refatorar o cliente de cache para usar injeção '
                                                                       'de dependência com pool estático '
                                                                       'reutilizável.'},
                                       'prevention': ['Configurar `timeout 60` e `tcp-keepalive 30` no `redis.conf`.',
                                                      'Implementar Circuit Breaker na aplicação para bypassar cache '
                                                      'sem travar requisições caso o Redis falhe.']},
                     'concepts': {'resource_title': 'Sockets TCP, Estados de Conexão & Padrão Connection Pool',
                                  'architecture_components': ['TCP Handshake & Sockets',
                                                              'Redis maxclients',
                                                              'Connection Pooling Pattern'],
                                  'how_it_works': 'Cada conexão TCP consome memória no servidor e um file descriptor '
                                                  'no kernel. Sem um pool de conexões, cada thread da API realiza o '
                                                  '3-way handshake para uma consulta rápida e abandona o socket. O '
                                                  'Redis atinge seu limite de segurança (`maxclients 10000`) e passa a '
                                                  'rejeitar novos handshakes, fazendo as threads da API travarem '
                                                  'aguardando resposta.',
                                  'best_practices': ['Sempre use instâncias singleton de ConnectionPool em frameworks '
                                                     'assíncronos.',
                                                     'Configure timeouts agressivos de conexão (connect_timeout=2s, '
                                                     'socket_timeout=3s).',
                                                     'Monitore a taxa de conexões ativas vs `maxclients` com alertas '
                                                     'em 80% de ocupação.'],
                                  'golden_signals': ['Clientes Conectados no Redis (Connected Clients Count)',
                                                     'Latência de Operação de Cache (Redis Ping Latency ms)']},
                     'detection_delay_seconds': 40,
                     'investigation_delay_seconds': 80,
                     'chaos_action': None},
 'dns-failure': {'id': 'dns-failure',
                 'title': 'DNS Resolution Failure (CoreDNS Timeout)',
                 'title_en': 'DNS Resolution Failure (CoreDNS Timeout)',
                 'severity': 'SEV-1',
                 'category': 'Rede',
                 'category_en': 'Network',
                 'difficulty': 'extreme',
                 'icon': '🌐',
                 'description': 'A aplicação não consegue resolver nomes de serviços internos (`postgresql`, `redis`). '
                                "Conexões falham com 'Name or service not known'. O CoreDNS travou com descarte "
                                'massivo de pacotes UDP.',
                 'description_en': 'Application cannot resolve internal cluster service names. CoreDNS is unresponsive '
                                   'and dropping UDP packets.',
                 'symptoms': ['App logs: socket.gaierror: [Errno -2] Name or service not known',
                              'nslookup postgresql.sre-rag.svc.cluster.local: SERVFAIL',
                              'CoreDNS pods em estado de alta utilização de CPU',
                              'NetworkPolicy pode estar bloqueando porta 53/UDP'],
                 'symptoms_en': ['App logs: socket.gaierror: [Errno -2] Name or service not known',
                                 'nslookup postgresql.sre-rag.svc.cluster.local: SERVFAIL',
                                 'CoreDNS pods showing elevated CPU and dropped UDP packets',
                                 'NetworkPolicy potentially blocking port 53/UDP'],
                 'hints': ['Teste a resolução de nomes de dentro do cluster com `nslookup '
                           'postgresql.sre-rag.svc.cluster.local`.',
                           'Reinicie os pods do CoreDNS no namespace kube-system: `kubectl rollout restart '
                           'deployment/coredns -n kube-system`.'],
                 'command': 'kubectl rollout restart deployment/coredns -n kube-system',
                 'solutions': [{'id': 'coredns-restart',
                                'label': 'Reiniciar CoreDNS pods (`kubectl rollout restart deployment/coredns -n '
                                         'kube-system`)',
                                'label_en': 'Restart CoreDNS deployment (`kubectl rollout restart deployment/coredns '
                                            '-n kube-system`)',
                                'correct': True,
                                'command': 'kubectl rollout restart deployment/coredns -n kube-system',
                                'explanation': '✅ Correto! O rollout restart recria os pods do CoreDNS, limpando '
                                               'conexões presas e restabelecendo a resolução de nomes interna '
                                               'imediatamente.',
                                'explanation_en': '✅ Correct! Restarting CoreDNS refreshes stale UDP sockets and '
                                                  'restores name resolution.'},
                               {'id': 'restart-app',
                                'label': 'Reiniciar todos os pods da aplicação',
                                'label_en': 'Restart all application pods',
                                'correct': False,
                                'command': 'kubectl rollout restart deployment/sre-rag-api',
                                'explanation': '❌ Incorreto. Reiniciar a aplicação não resolve falha de DNS do '
                                               'cluster. Os pods reiniciados falharão exatamente no mesmo ponto de '
                                               'lookup.',
                                'explanation_en': '❌ Ineffective. Application restart will fail again at the identical '
                                                  'DNS resolution step.'},
                               {'id': 'use-ip',
                                'label': 'Substituir nomes de serviço por IPs estáticos nos ConfigMaps',
                                'label_en': 'Replace service hostnames with static cluster IPs',
                                'correct': False,
                                'command': 'kubectl set env deployment/sre-rag-api DB_HOST=10.96.0.45',
                                'explanation': '❌ Anti-pattern gravíssimo. IPs de pods e serviços no Kubernetes são '
                                               'efêmeros. Usar IPs estáticos quebra a infraestrutura no próximo '
                                               'deploy.',
                                'explanation_en': '❌ Severe anti-pattern. Ephemeral cluster IPs will break permanently '
                                                  'on subsequent updates.'}],
                 'runbook': '/docs/runbooks/dns-failure',
                 'runbook_steps': {'triage': ['Alerta KubeDNSDown / CoreDNSErrorsHigh disparado.',
                                              "Múltiplos microsserviços falhando com 'Name or service not known'.",
                                              'Tráfego externo caindo por falhas de dependências internas.'],
                                   'diagnosis': ['kubectl run -it --rm test-dns --image=busybox -- nslookup '
                                                 'postgresql.sre-rag.svc.cluster.local (Retorna SERVFAIL).',
                                                 'kubectl get pods -n kube-system -l k8s-app=kube-dns (Verificar '
                                                 'status dos pods).',
                                                 'kubectl logs -n kube-system -l k8s-app=kube-dns (Erros de timeout e '
                                                 'i/o timeout na porta 53).'],
                                   'mitigation': {'action': 'Reiniciar o Deployment do CoreDNS para restaurar a pilha '
                                                            'de rede.',
                                                  'command': 'kubectl rollout restart deployment/coredns -n '
                                                             'kube-system',
                                                  'validation': 'kubectl run -it --rm test-dns --image=busybox -- '
                                                                'nslookup postgresql.sre-rag (Resolve com sucesso).'},
                                   'root_cause': {'analysis': 'Vazamento de descritores de sockets UDP no CoreDNS sob '
                                                              'alta concorrência de lookups sem cache local (NodeLocal '
                                                              'DNSCache).',
                                                  'permanent_fix': 'Implantar o NodeLocal DNSCache como DaemonSet em '
                                                                   'todos os nós.'},
                                   'prevention': ['Configurar autoscaling do CoreDNS baseado em nós e núcleos de CPU.',
                                                  'Ajustar opções de `ndots: 2` no `dnsConfig` dos pods para evitar '
                                                  'buscas recursivas excessivas.']},
                 'concepts': {'resource_title': 'Kubernetes Service DNS, CoreDNS Architecture & NodeLocal DNSCache',
                              'architecture_components': ['CoreDNS / Kube-DNS',
                                                          'iptables / IPVS Service Routing',
                                                          'NodeLocal DNSCache DaemonSet'],
                              'how_it_works': 'Cada Pod no cluster recebe `/etc/resolv.conf` apontando para o '
                                              'ClusterIP do CoreDNS com `options ndots:5`. Quando o pod consulta '
                                              '`postgresql`, o resolver tenta sequencialmente '
                                              '`postgresql.<namespace>.svc.cluster.local`, gerando até 5 requisições '
                                              'UDP na porta 53 para cada lookup. Sob carga, a conntrack table do Linux '
                                              'e os buffers UDP do CoreDNS sofrem saturação, descartando pacotes '
                                              'silenciosamente.',
                              'best_practices': ['Implante o NodeLocal DNSCache para atender lookups diretamente no '
                                                 'cache local do nó via interface dummy de loopback.',
                                                 'Use nomes de domínio totalmente qualificados (FQDN com ponto final, '
                                                 'ex: `postgresql.sre-rag.svc.cluster.local.`) para evitar buscas '
                                                 'desnecessárias do ndots.',
                                                 'Monitore a métrica `coredns_dns_request_duration_seconds` no '
                                                 'Prometheus.'],
                              'golden_signals': ['Latência de Resolução DNS (CoreDNS Lookup Duration ms)',
                                                 'Taxa de Erros SERVFAIL (DNS SERVFAIL Rate %)']},
                 'detection_delay_seconds': 30,
                 'investigation_delay_seconds': 75,
                 'chaos_action': None},
 'db-pool-starvation': {'id': 'db-pool-starvation',
                        'title': 'PostgreSQL Connection Pool Starvation & Idle Locks',
                        'title_en': 'PostgreSQL Connection Pool Starvation & Idle Locks',
                        'severity': 'SEV-1',
                        'category': 'Concorrência',
                        'category_en': 'Concurrency',
                        'difficulty': 'extreme',
                        'icon': '🐘',
                        'description': "A API retorna 'FATAL: remaining connection slots are reserved for "
                                       "non-replication superuser connections'. Há 100 conexões abertas no PostgreSQL, "
                                       "a maioria presas em 'idle in transaction' por falta de fechamento de blocos "
                                       'contextuais no código.',
                        'description_en': "API returns 'FATAL: remaining connection slots are reserved'. PostgreSQL "
                                          "saturated with 100 open connections stuck in 'idle in transaction'.",
                        'symptoms': ['PostgreSQL logs: FATAL: remaining connection slots are reserved',
                                     "pg_stat_activity: 95 conexões em 'idle in transaction' há mais de 10 min",
                                     'Novas requisições da API falham imediatamente com HTTP 500',
                                     'CPU do banco em 5%, mas capacidade de conexões em 100%'],
                        'symptoms_en': ['PostgreSQL logs: FATAL: remaining connection slots are reserved',
                                        "pg_stat_activity: 95 connections in 'idle in transaction' > 10m",
                                        'Incoming requests immediately reject with HTTP 500',
                                        'Database CPU at 5%, but connection capacity at 100%'],
                        'hints': ['Inspecione o estado das conexões no banco executando consulta em '
                                  '`pg_stat_activity`.',
                                  'Elimine as sessões presas em idle in transaction para liberar os slots: `kubectl '
                                  'exec -i sts/postgresql-0 -- psql -U postgres -d sre_db -c "SELECT '
                                  "pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle in transaction' "
                                  'AND state_change < now() - INTERVAL \'2 minutes\';"`.'],
                        'command': 'kubectl exec -i sts/postgresql-0 -- psql -U postgres -d sre_db -c "SELECT '
                                   "pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle in "
                                   'transaction\' AND state_change < now() - INTERVAL \'2 minutes\';"',
                        'solutions': [{'id': 'terminate-idle-tx',
                                       'label': 'Encerrar transações órfãs com `pg_terminate_backend` para liberar '
                                                'slots',
                                       'label_en': 'Terminate orphaned transactions via `pg_terminate_backend`',
                                       'correct': True,
                                       'command': 'kubectl exec -i sts/postgresql-0 -- psql -U postgres -d sre_db -c '
                                                  '"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state '
                                                  "= 'idle in transaction' AND state_change < now() - INTERVAL '2 "
                                                  'minutes\';"',
                                       'explanation': '✅ Correto! Finalizar as conexões zumbis presas em idle in '
                                                      'transaction libera os slots de conexão imediatamente sem '
                                                      'derrubar o banco de dados.',
                                       'explanation_en': '✅ Correct! Killing orphaned idle transactions instantly '
                                                         'reclaims connection slots without taking down the database.'},
                                      {'id': 'increase-max-connections',
                                       'label': 'Aumentar max_connections no postgresql.conf para 5000',
                                       'label_en': 'Increase max_connections to 5000 in postgresql.conf',
                                       'correct': False,
                                       'command': "kubectl exec -i sts/postgresql-0 -- psql -c 'ALTER SYSTEM SET "
                                                  "max_connections = 5000;'",
                                       'explanation': '❌ Desastroso. Cada conexão no PostgreSQL aloca memória dedicada '
                                                      'no Linux (work_mem + shared buffers). 5000 conexões causariam '
                                                      'OOM Kill no processo do banco.',
                                       'explanation_en': '❌ Dangerous. Each connection consumes private memory; 5000 '
                                                         'connections will trigger kernel OOM on PostgreSQL.'},
                                      {'id': 'drop-database',
                                       'label': 'Recriar o schema do banco de dados',
                                       'label_en': 'Recreate database schema',
                                       'correct': False,
                                       'command': 'kubectl exec -i sts/postgresql-0 -- dropdb sre_db',
                                       'explanation': '❌ Destrutivo! Apagar o banco acarreta perda irreversível de '
                                                      'dados de produção.',
                                       'explanation_en': '❌ Destructive. Results in complete data loss.'}],
                        'runbook': '/docs/runbooks/db-pool-starvation',
                        'runbook_steps': {'triage': ['Alerta PostgresTooManyConnections (> 95% do max_connections).',
                                                     'API lançando OperationalError: FATAL remaining connection slots.',
                                                     'Taxa de erro 500 em todas as rotas que realizam persistência.'],
                                          'diagnosis': ['psql -c "SELECT count(*), state FROM pg_stat_activity GROUP '
                                                        'BY state;" (95 em idle in transaction).',
                                                        'psql -c "SELECT pid, now() - state_change as duration, query '
                                                        'FROM pg_stat_activity WHERE state = \'idle in transaction\';"',
                                                        'Identificação de transação aberta sem COMMIT nem ROLLBACK.'],
                                          'mitigation': {'action': 'Executar pg_terminate_backend nas conexões ociosas '
                                                                   'há mais de 2 minutos.',
                                                         'command': 'kubectl exec -i sts/postgresql-0 -- psql -U '
                                                                    'postgres -d sre_db -c "SELECT '
                                                                    'pg_terminate_backend(pid) FROM pg_stat_activity '
                                                                    "WHERE state = 'idle in transaction' AND "
                                                                    'state_change < now() - INTERVAL \'2 minutes\';"',
                                                         'validation': 'curl -s http://localhost:8080/api/v1/health | '
                                                                       "jq .status (Retorna 'healthy')."},
                                          'root_cause': {'analysis': 'Uma rota de ingestão abria transação de escrita '
                                                                     'e fazia chamada HTTP externa para a API do '
                                                                     'OpenAI dentro do bloco transacional, segurando a '
                                                                     'conexão aberta por dezenas de segundos.',
                                                         'permanent_fix': 'Nunca realizar chamadas de rede ou IO '
                                                                          'externo dentro de transações de banco de '
                                                                          'dados.'},
                                          'prevention': ['Configurar `idle_in_transaction_session_timeout = 30000` '
                                                         '(30s) no `postgresql.conf`.',
                                                         'Implantar PgBouncer em modo transaction pooling na frente do '
                                                         'PostgreSQL.']},
                        'concepts': {'resource_title': 'PostgreSQL Process Architecture, MVCC & Transaction Pooling '
                                                       'com PgBouncer',
                                     'architecture_components': ['PostgreSQL Backend Processes',
                                                                 'pg_stat_activity',
                                                                 'PgBouncer Connection Pooler'],
                                     'how_it_works': 'Diferente de sistemas multithread, o PostgreSQL utiliza um '
                                                     'modelo baseado em processos (fork de processo para cada cliente '
                                                     'conectado). Cada conexão consome de 5 a 10MB de RAM. Quando uma '
                                                     'transação fica presa em `idle in transaction`, ela não apenas '
                                                     'retém um slot de conexão valioso, mas também impede o vacuum de '
                                                     'limpar tuplas mortas (MVCC dead tuples) e mantém table locks '
                                                     'ativos.',
                                     'best_practices': ['Sempre defina `idle_in_transaction_session_timeout` no '
                                                        'PostgreSQL para que o próprio banco mate conexões '
                                                        'abandonadas.',
                                                        'Utilize PgBouncer entre a aplicação e o banco para '
                                                        'multiplexar centenas de conexões da API em um pool enxuto de '
                                                        '20 conexões no PostgreSQL.',
                                                        'Mantenha transações atômicas e o mais curtas possível.'],
                                     'golden_signals': ['Uso de Slots de Conexão no Banco (Postgres Connection Usage '
                                                        '%)',
                                                        'Transações em Idle Longas (Max Idle-in-Transaction '
                                                        'Duration)']},
                        'detection_delay_seconds': 35,
                        'investigation_delay_seconds': 85,
                        'chaos_action': None},
 'split-brain-partition': {'id': 'split-brain-partition',
                           'title': 'CNI Network Partition & mTLS Handshake Failure',
                           'title_en': 'CNI Network Partition & mTLS Handshake Failure',
                           'severity': 'SEV-1',
                           'category': 'Rede',
                           'category_en': 'Network',
                           'difficulty': 'extreme',
                           'icon': '⚡',
                           'description': 'Comunicação entre a API no nó worker-1 e o PostgreSQL no nó worker-2 falha '
                                          "intermitentemente com 'Connection reset by peer' e falhas de mTLS no "
                                          'sidecar Envoy. O DaemonSet do Calico CNI travou no worker-2, deixando '
                                          'tabelas de rotas BGP dessincronizadas.',
                           'description_en': "Inter-node pod communication failing with 'Connection reset by peer' and "
                                             'mTLS handshake timeouts due to desynchronized Calico BGP mesh.',
                           'symptoms': ['Comunicação cross-node falhando com timeout e resets de conexão TCP',
                                        'Envoy sidecar logs: mTLS handshake failure: downstream connection termination',
                                        'Calico node no worker-2 em status Degradado / BGP peer down',
                                        'Alertmanager: CalicoBGPPeerDown FIRING'],
                           'symptoms_en': ['Cross-node pod communication dropping with TCP resets',
                                           'Envoy sidecar logs: mTLS handshake failure: downstream connection '
                                           'termination',
                                           'Calico node daemon on worker-2 degraded / BGP peer down',
                                           'Alertmanager: CalicoBGPPeerDown FIRING'],
                           'hints': ['Inspecione o status dos pods do CNI no namespace kube-system: `kubectl get pods '
                                     '-n kube-system -l k8s-app=calico-node`.',
                                     'Reinicie o DaemonSet do Calico para forçar a reconvergência das rotas de rede: '
                                     '`kubectl rollout restart daemonset/calico-node -n kube-system`.'],
                           'command': 'kubectl rollout restart daemonset/calico-node -n kube-system',
                           'solutions': [{'id': 'restart-cni',
                                          'label': 'Reiniciar o DaemonSet do CNI (`kubectl rollout restart '
                                                   'daemonset/calico-node -n kube-system`)',
                                          'label_en': 'Restart CNI DaemonSet (`kubectl rollout restart '
                                                      'daemonset/calico-node -n kube-system`)',
                                          'correct': True,
                                          'command': 'kubectl rollout restart daemonset/calico-node -n kube-system',
                                          'explanation': '✅ Correto! Reiniciar o agente CNI restaura as interfaces '
                                                         'virtuais veth, as regras de iptables/eBPF e a malha BGP '
                                                         'entre os nós do cluster.',
                                          'explanation_en': '✅ Correct! Restarting the CNI agent re-establishes veth '
                                                            'interfaces, iptables/eBPF rules, and BGP routing mesh '
                                                            'across worker nodes.'},
                                         {'id': 'disable-mtls',
                                          'label': 'Desativar criptografia mTLS em todo o cluster',
                                          'label_en': 'Disable mTLS encryption cluster-wide',
                                          'correct': False,
                                          'command': 'kubectl patch peerauthentication default -n sre-rag --type merge '
                                                     '-p \'{"spec":{"mtls":{"mode":"DISABLE"}}}\'',
                                          'explanation': '❌ Violação grave de segurança (Zero Trust). Além disso, não '
                                                         'resolve a falha, pois o problema é de camada de rede '
                                                         'física/roteamento do CNI.',
                                          'explanation_en': '❌ Security violation and ineffective; the underlying '
                                                            'failure is packet routing at CNI layer.'},
                                         {'id': 'reboot-cluster',
                                          'label': 'Desligar e religar todos os servidores físicos do cluster',
                                          'label_en': 'Power cycle all physical cluster servers',
                                          'correct': False,
                                          'command': 'shutdown -r now',
                                          'explanation': '❌ Ação desastrosa que causaria queda generalizada e '
                                                         'corrupção de quórum do etcd.',
                                          'explanation_en': '❌ Destructive. Triggers global outage and potential etcd '
                                                            'quorum corruption.'}],
                           'runbook': '/docs/runbooks/split-brain-partition',
                           'runbook_steps': {'triage': ['Alerta CalicoBGPPeerDown e MeshPeerAuthenticationFailed.',
                                                        'Pods no nó 1 não conseguem falar com pods no nó 2 (latência '
                                                        'infinita / timeout).',
                                                        'Logs do Envoy sidecar com falhas constantes de TLS '
                                                        'handshakes.'],
                                             'diagnosis': ['kubectl get pods -n kube-system -l k8s-app=calico-node -o '
                                                           'wide (Pod no worker-2 com restarts anormais).',
                                                           'kubectl exec -n kube-system daemonset/calico-node -- '
                                                           'calicoctl node status (Peer 10.0.1.20 state: Idle / '
                                                           'Non-established).',
                                                           'Traceroute inter-node identificando descarte de pacotes no '
                                                           'túnel VXLAN/IPIP.'],
                                             'mitigation': {'action': 'Reiniciar o DaemonSet do Calico para forçar '
                                                                      'reconciliação do mesh de rede.',
                                                            'command': 'kubectl rollout restart daemonset/calico-node '
                                                                       '-n kube-system',
                                                            'validation': 'kubectl rollout status '
                                                                          'daemonset/calico-node -n kube-system'},
                                             'root_cause': {'analysis': 'Um jitter transitório de rede causou '
                                                                        'descompasso no BGP peer do Calico e '
                                                                        'travamento do processo felix no nó worker-2.',
                                                            'permanent_fix': 'Habilitar BFD (Bidirectional Forwarding '
                                                                             'Detection) para detecção e convergência '
                                                                             'de rotas em submilisegundos.'},
                                             'prevention': ['Monitorar métricas de saúde da malha CNI '
                                                            '(calico_felix_cluster_num_host_endpoints).',
                                                            'Configurar testes de conectividade contínuos entre nós '
                                                            'com ferramentas como Kube-Ping.']},
                           'concepts': {'resource_title': 'Kubernetes CNI (Container Network Interface), BGP Mesh & '
                                                          'Service Mesh mTLS',
                                        'architecture_components': ['Calico Felix / BIRD BGP',
                                                                    'Overlay Network (VXLAN/IPIP)',
                                                                    'Envoy Proxy mTLS Handshake'],
                                        'how_it_works': 'O CNI é responsável por atribuir IPs aos Pods e programar a '
                                                        'tabela de roteamento do kernel Linux (via BGP, VXLAN ou '
                                                        'eBPF). Em clusters multi-nó, cada nó atua como um BGP peer '
                                                        'anunciando seus blocos de IPs de pods (/26) para os outros '
                                                        'nós. Se o daemon CNI trava em um nó, os outros nós perdem a '
                                                        'rota para aqueles pods. Requisições entre nós sofrem descarte '
                                                        'de pacotes, quebrando o handshake criptográfico mTLS dos '
                                                        'proxies Envoy.',
                                        'best_practices': ['Separe o tráfego de controle do CNI e do etcd em redes '
                                                           'físicas dedicadas ou VLANs priorizadas.',
                                                           'Monitore ativamente o status de peering BGP com alertas de '
                                                           'severidade crítica.',
                                                           'Utilize health checks rigorosos nos DaemonSets de rede '
                                                           'para que o Kubelet reinicie agentes travados prontamente.'],
                                        'golden_signals': ['Estado dos BGP Peers (BGP Peering Up/Down Count)',
                                                           'Perda de Pacotes Inter-Node (Cross-Node Packet Drop Rate '
                                                           '%)']},
                           'detection_delay_seconds': 45,
                           'investigation_delay_seconds': 95,
                           'chaos_action': None}}

DIAGNOSTIC_COMMANDS = {'high-error-rate': {'helm history sre-rag': 'REVISION\tUPDATED                 \tSTATUS    \tCHART        \tAPP '
                                             'VERSION\tDESCRIPTION\n'
                                             '1       \tTue Oct  6 18:00:00 2026\tsuperseded\tsre-rag-0.1.0\t'
                                             '3.1        \tInstall complete\n'
                                             '2       \tTue Oct  6 20:15:30 2026\tdeployed  \tsre-rag-0.2.0\t'
                                             '3.2        \tRelease com bug (500 spike)\n'
                                             '\n'
                                             '💡 [DIAGNÓSTICO]: A revisão 2 introduziu a falha. Para reverter para a '
                                             'revisão 1 estável, execute:\n'
                                             '   helm rollback sre-rag',
                     'kubectl get pods': 'NAME                           READY   STATUS    RESTARTS   AGE\n'
                                         'sre-rag-api-7b89f5d6cb-9k8lx   1/1     Running   0          25m\n'
                                         'sre-rag-api-7b89f5d6cb-m42xq   1/1     Running   0          25m\n'
                                         'sre-rag-postgres-0             1/1     Running   0          2d\n'
                                         'sre-rag-redis-0                1/1     Running   0          2d',
                     'kubectl logs': '[ERROR] 2026-10-06 20:16:02 - Unhandled Exception in /api/v1/query: '
                                     "KeyError('EMBEDDING_BATCH_SIZE')\n"
                                     '[ERROR] 2026-10-06 20:16:05 - HTTP 500 Internal Server Error returned to '
                                     'ingress'},
 'oom-kill': {'kubectl describe pod': 'Name:           sre-rag-api-7d498bd6df-m72zq\n'
                                      'State:          Terminated\n'
                                      '  Reason:       OOMKilled\n'
                                      '  Exit Code:    137\n'
                                      'Limits:\n'
                                      '  memory:       512Mi\n'
                                      '\n'
                                      '💡 [DIAGNÓSTICO]: O container estourou o limite de 512Mi. Aumente os limites '
                                      'com:\n'
                                      '   helm upgrade sre-rag ./helm/sre-rag --set api.resources.limits.memory=1024Mi',
              'kubectl get pods': 'NAME                           READY   STATUS             RESTARTS   AGE\n'
                                  'sre-rag-api-7d498bd6df-m72zq   0/1     CrashLoopBackOff   4          12m'},
 'missing-config-secret': {'kubectl logs': 'Traceback (most recent call last):\n'
                                           "  File 'main.py', line 15, in <module>\n"
                                           "KeyError: 'OPENAI_API_KEY'\n"
                                           "FATAL: Mandatory Secret 'sre-rag-secrets' not found in namespace "
                                           "'sre-rag'.",
                           'kubectl get secrets': 'NAME                  TYPE     DATA   AGE\n'
                                                  'default-token-8jx2b   token    3      14d'},
 'pod-pending-resources': {'kubectl describe pod': 'Events:\n'
                                                   '  Type     Reason            Age   From               Message\n'
                                                   '  Warning  FailedScheduling  2m    default-scheduler  0/3 nodes '
                                                   'are available: 3 Insufficient cpu.\n'
                                                   'Pod spec requested resources.requests.cpu = 8000m (exceeds node '
                                                   'capacity).',
                           'kubectl get nodes': 'NAME      STATUS   ROLES    AGE   VERSION\n'
                                                'worker-1  Ready    <none>   30d   v1.29.2\n'
                                                'worker-2  Ready    <none>   30d   v1.29.2\n'
                                                'worker-3  Ready    <none>   30d   v1.29.2'},
 'high-latency': {'kubectl top pods': 'NAME                           CPU(cores)   MEMORY(bytes)\n'
                                      'sre-rag-api-7b89f5d6cb-9k8lx   950m         420Mi\n'
                                      'sre-rag-api-7b89f5d6cb-m42xq   980m         410Mi\n'
                                      '\n'
                                      '💡 [DIAGNÓSTICO]: CPU saturada em 95%+. Escale os pods via HPA:\n'
                                      '   kubectl scale hpa sre-rag-api --min=5 --max=20'},
 'crashloopbackoff': {'kubectl describe pod': 'State:          Waiting\n'
                                              '  Reason:       CrashLoopBackOff\n'
                                              'Events:\n'
                                              '  Warning  Unhealthy  40s  kubelet  Startup probe failed: HTTP probe '
                                              'failed with statuscode: 503\n'
                                              '  Warning  Killing    38s  kubelet  Container api failed startup probe, '
                                              'will be restarted'},
 'ingress-503-endpoints': {'kubectl get endpoints': 'NAME          ENDPOINTS   AGE\nsre-rag-api   <none>      25d',
                           'kubectl get pods --show-labels': 'NAME                           READY   STATUS    LABELS\n'
                                                             'sre-rag-api-7b89f5d6cb-9k8lx   1/1     Running   '
                                                             'app.kubernetes.io/name=sre-rag-api\n'
                                                             'sre-rag-api-7b89f5d6cb-m42xq   1/1     Running   '
                                                             'app.kubernetes.io/name=sre-rag-api'},
 'hpa-flapping': {'kubectl describe hpa': 'Reference:                               Deployment/sre-rag-api\n'
                                          'Metrics:                                 ( current / target )\n'
                                          '  resource cpu on pods:                  85% / 70%\n'
                                          'Min replicas:                            2\n'
                                          'Max replicas:                            20\n'
                                          'Events:\n'
                                          '  SuccessfulRescale  2m   hpa-controller  New size: 15; reason: cpu '
                                          'resource utilization above target\n'
                                          '  SuccessfulRescale  40s  hpa-controller  New size: 2; reason: All metrics '
                                          'below target (no stabilization window)'},
 'tls-expiring': {'kubectl get cert': 'NAME             READY   SECRET           AGE   EXPIRATION\n'
                                      'sre-rag-tls-cert False   sre-rag-tls-cert 90d   Expired in 36h\n'
                                      '\n'
                                      '💡 [DIAGNÓSTICO]: Anote o Ingress com o cluster-issuer correspondente:\n'
                                      '   kubectl annotate ingress sre-rag '
                                      'cert-manager.io/cluster-issuer=letsencrypt-prod --overwrite'},
 'disk-pressure': {'df -h': 'Filesystem      Size  Used Avail Use% Mounted on\n'
                            '/dev/sda1        50G   44G  3.5G  93% /var/lib/docker\n'
                            '\n'
                            '💡 [DIAGNÓSTICO]: Uso de disco acima de 85% dispara DiskPressure. Limpe imagens não '
                            'utilizadas com:\n'
                            '   crictl rmi --prune'},
 'pvc-mount-deadlock': {'kubectl get volumeattachment': 'NAME                                                               '
                                                        'ATTACHED   NODE       AGE\n'
                                                        'csi-789a4df56b2c89e102f3458901bca23de5f67a890b1c2d3e4f5a6b7c8d9e   '
                                                        'true       worker-1   12m\n'
                                                        'Warning: worker-1 is NotReady. Attachment is stuck '
                                                        'exclusively on offline node.',
                        'kubectl describe pod': 'Events:\n'
                                                '  Warning  FailedAttachVolume  2m  attachdetach-controller  '
                                                'Multi-Attach error for volume pv-data: Volume is already exclusively '
                                                'attached to worker-1'},
 'cpu-throttling': {'cat /sys/fs/cgroup/cpu/cpu.stat': 'nr_periods 14820\n'
                                                       'nr_throttled 11240\n'
                                                       'throttled_time 58920145290\n'
                                                       '\n'
                                                       '💡 [DIAGNÓSTICO]: Throttling atingiu 75.8% dos períodos de '
                                                       '100ms. Remova o hard limit com:\n'
                                                       '   helm upgrade sre-rag ./helm/sre-rag --set '
                                                       'api.resources.limits.cpu=null --reuse-values'},
 'redis-exhausted': {'redis-cli info clients': '# Clients\n'
                                               'connected_clients:10000\n'
                                               'maxclients:10000\n'
                                               'blocked_clients:482\n'
                                               '\n'
                                               '💡 [DIAGNÓSTICO]: Conexões esgotadas. Ajuste o pool com:\n'
                                               '   kubectl set env deployment/sre-rag-api REDIS_MAX_CONNECTIONS=100 '
                                               'REDIS_TIMEOUT=30'},
 'dns-failure': {'nslookup': 'Server:    10.96.0.10\n'
                             'Address:   10.96.0.10#53\n'
                             "** server can't find postgresql.sre-rag.svc.cluster.local: SERVFAIL\n"
                             '\n'
                             '💡 [DIAGNÓSTICO]: CoreDNS travado. Reinicie o deployment com:\n'
                             '   kubectl rollout restart deployment/coredns -n kube-system'},
 'db-pool-starvation': {'psql': ' state               | count\n'
                                '--------------------+-------\n'
                                ' idle in transaction|    95\n'
                                ' active             |     5\n'
                                '(total: 100/100 connections saturated)\n'
                                '\n'
                                '💡 [DIAGNÓSTICO]: 95 conexões presas em idle in transaction. Termine as conexões com '
                                'pg_terminate_backend.'},
 'split-brain-partition': {'kubectl get pods -n kube-system': 'NAME                READY   STATUS     RESTARTS   AGE\n'
                                                              'calico-node-9k8lx   1/1     Running    0          20d\n'
                                                              'calico-node-m42xq   0/1     Degraded   14         20d '
                                                              '(BGP peering failure)'}}


# ============================================================
# Simulation State Models
# ============================================================
class SimulationResult(BaseModel):
    id: int
    scenario_id: str
    scenario_title: str
    scenario_title_en: Optional[str] = None
    severity: str
    category: Optional[str] = "Geral"
    category_en: Optional[str] = "General"
    icon: Optional[str] = "🚨"
    started_at: str
    solved_at: Optional[str]
    mttd_seconds: Optional[float]
    mttr_seconds: Optional[float]
    solution_chosen: Optional[str]
    solution_chosen_en: Optional[str] = None
    correct: Optional[bool]
    explanation: Optional[str]
    explanation_en: Optional[str] = None
    hints_used: Optional[int] = 0
    score: Optional[int] = 100


class ActiveSimulation(BaseModel):
    scenario_id: str
    started_at: float
    phase: str  # "running" | "detected" | "investigating" | "solved"
    chaos_active: bool
    hints_used: int = 0


# ============================================================
# Simulation Engine
# ============================================================
class IncidentSimulationEngine:
    def __init__(self):
        self.active: Optional[ActiveSimulation] = None
        self.history: List[SimulationResult] = []
        self._counter = 1

    def start(self, scenario_id: str) -> dict:
        if scenario_id not in SCENARIOS:
            return {"error": f"Scenario '{scenario_id}' not found"}

        self.active = ActiveSimulation(
            scenario_id=scenario_id,
            started_at=time.time(),
            phase="running",
            chaos_active=SCENARIOS[scenario_id].get("chaos_action") == "simulate_500",
            hints_used=0,
        )
        return {
            "status": "started",
            "scenario_id": scenario_id,
            "started_at": self.active.started_at,
            "difficulty": SCENARIOS[scenario_id].get("difficulty", "medium"),
            "category": SCENARIOS[scenario_id].get("category", "Geral"),
        }

    def get_random_incident(self, difficulty: str = "all", exclude_ids: Optional[List[str]] = None) -> dict:
        import random
        exclude_ids = exclude_ids or []
        
        if difficulty == "all":
            pool = [sid for sid in SCENARIOS.keys() if sid not in exclude_ids]
        else:
            pool = [sid for sid, sc in SCENARIOS.items() if sc.get("difficulty") == difficulty and sid not in exclude_ids]
        
        if not pool:
            if difficulty == "all":
                pool = list(SCENARIOS.keys())
            else:
                pool = [sid for sid, sc in SCENARIOS.items() if sc.get("difficulty") == difficulty]
            
            if len(pool) > 1 and exclude_ids:
                pool = [sid for sid in pool if sid != exclude_ids[-1]]

        if not pool:
            return {"error": f"No scenarios found for difficulty '{difficulty}'"}

        chosen_id = random.choice(pool)
        self.start(chosen_id)
        return {"status": "started", "scenario_id": chosen_id}

    def get_active_state(self) -> Optional[dict]:
        if not self.active:
            return None

        scenario = SCENARIOS[self.active.scenario_id]
        elapsed = time.time() - self.active.started_at

        if elapsed >= scenario["investigation_delay_seconds"]:
            self.active.phase = "investigating"
        elif elapsed >= scenario["detection_delay_seconds"]:
            self.active.phase = "detected"

        return {
            "scenario_id": self.active.scenario_id,
            "phase": self.active.phase,
            "elapsed_seconds": round(elapsed, 1),
            "detection_at": scenario["detection_delay_seconds"],
            "investigation_at": scenario["investigation_delay_seconds"],
            "chaos_active": self.active.chaos_active,
            "hints_used": getattr(self.active, "hints_used", 0),
        }

    def solve(self, scenario_id: str, solution_id: str) -> dict:
        if not self.active or self.active.scenario_id != scenario_id:
            return {"error": "No matching active simulation"}

        scenario = SCENARIOS[scenario_id]
        solution = next((s for s in scenario["solutions"] if s["id"] == solution_id), None)
        
        if not solution:
            cmd_submitted = solution_id.strip()
            correct_sol = next((s for s in scenario["solutions"] if s["correct"]), None)
            
            if correct_sol and correct_sol.get("command") and cmd_submitted.lower() == correct_sol["command"].lower():
                solution = correct_sol
            else:
                diag_map = DIAGNOSTIC_COMMANDS.get(scenario_id, {})
                norm = cmd_submitted.lower()
                matched_output = None
                for d_cmd, d_out in diag_map.items():
                    if norm == d_cmd.lower() or norm.startswith(d_cmd.lower()):
                        matched_output = d_out
                        break
                
                if not matched_output:
                    if norm in ("help", "--help", "-h"):
                        matched_output = (
                            "Comandos Suportados:\n"
                            "  Diagnóstico : helm history, kubectl get pods, kubectl describe pod, kubectl logs, df -h, psql\n"
                            "  Mitigação   : Digite o comando de remediação correspondente (ex: helm rollback, etc.)\n"
                            "  Revisão     : Clique no botão '📖 Revisão' para ver o passo a passo completo."
                        )
                    elif norm in ("kubectl get pods", "kubectl get pod", "k get pods"):
                        matched_output = (
                            "NAME                           READY   STATUS    RESTARTS   AGE\n"
                            "sre-rag-api-7b89f5d6cb-9k8lx   1/1     Running   0          25m\n"
                            "sre-rag-api-7b89f5d6cb-m42xq   1/1     Running   0          25m"
                        )

                if matched_output:
                    return {
                        "diagnostic": True,
                        "correct": False,
                        "output": matched_output,
                        "explanation": "Comando de diagnóstico executado com sucesso."
                    }

                return {
                    "diagnostic": False,
                    "correct": False,
                    "explanation": f"Comando não reconhecido ou incorreto. Dica: Para mitigar este incidente, o comando correto é: `{correct_sol.get('command', 'indisponível')}`",
                    "explanation_en": "Command not recognized or incorrect."
                }

        elapsed = time.time() - self.active.started_at
        mttd = scenario["detection_delay_seconds"]

        hints_used = getattr(self.active, "hints_used", 0)
        score = max(0, 100 - hints_used * 20) if solution["correct"] else 0
        result = SimulationResult(
            id=self._counter,
            scenario_id=scenario_id,
            scenario_title=scenario["title"],
            scenario_title_en=scenario.get("title_en", scenario["title"]),
            severity=scenario["severity"],
            category=scenario.get("category", "Geral"),
            category_en=scenario.get("category_en", "General"),
            icon=scenario.get("icon", "🚨"),
            started_at=datetime.fromtimestamp(self.active.started_at).strftime("%H:%M:%S"),
            solved_at=datetime.now().strftime("%H:%M:%S"),
            mttd_seconds=mttd,
            mttr_seconds=round(elapsed, 1),
            solution_chosen=solution["label"],
            solution_chosen_en=solution.get("label_en", solution["label"]),
            correct=solution["correct"],
            explanation=solution["explanation"],
            explanation_en=solution.get("explanation_en", solution["explanation"]),
            hints_used=hints_used,
            score=score,
        )

        self.history.insert(0, result)
        self._counter += 1
        self.active = None

        return result.model_dump()

    def cancel(self):
        self.active = None
        return {"status": "cancelled"}

    def clear_history(self):
        self.history = []
        self._counter = 1
        return {"status": "cleared", "count": 0}


# Singleton engine instance
simulation_engine = IncidentSimulationEngine()
