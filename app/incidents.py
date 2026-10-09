"""
SRE Incident Simulation Engine
Manages 16 incident scenarios, active simulations, diagnostic commands, 
step-by-step runbooks, and SRE architectural concepts with bilingual support (pt / en).
"""
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

SCENARIOS = { 'cpu-throttling': { 'category': 'Desempenho',
                      'category_en': 'Performance',
                      'chaos_action': None,
                      'command': 'helm upgrade sre-rag ./helm/sre-rag --set api.resources.limits.cpu=null '
                                 '--reuse-values',
                      'concepts': { 'architecture_components': [ 'Linux CFS Quota / Period',
                                                                 'cgroup cpu.cfs_quota_us',
                                                                 'CPU Limits vs Throttling'],
                                    'best_practices': [ 'Considere remover `limits.cpu` (definir apenas '
                                                        '`requests.cpu`) para aplicações em linguagens com suporte a '
                                                        'paralelismo/threads.',
                                                        'Se for obrigado por governança a usar CPU limits, dimensione '
                                                        'o limite com no mínimo 3x o valor do request.',
                                                        'Monitore `container_cpu_cfs_throttled_periods_total` para '
                                                        'auditar penalidades de escalonamento.'],
                                    'best_practices_en': [ 'Monitor `container_cpu_cfs_throttled_periods_total / '
                                                           'container_cpu_cfs_periods_total` (target < 5%).',
                                                           'Avoid overly tight CPU limits on multi-threaded runtimes '
                                                           '(Go, Java, Node.js).',
                                                           'Consider disabling CPU limits and relying on CPU requests '
                                                           'with Guaranteed/Burstable QoS if cluster allows.'],
                                    'category_en': 'Performance',
                                    'golden_signals': [ 'Percentual de CFS Throttling (CFS Throttled Periods %)',
                                                        'Latência de Processamento P99 (P99 Queue & Processing '
                                                        'Latency)'],
                                    'golden_signals_en': [ 'CFS CPU Throttled Periods %',
                                                           'P99 Response Time Spike under Low CPU'],
                                    'how_it_works': 'Ao definir `limits.cpu: 500m`, o Kubelet configura no cgroup do '
                                                    'container: `cpu.cfs_period_us = 100000` (100ms) e '
                                                    '`cpu.cfs_quota_us = 50000` (50ms). Se o container possui 4 '
                                                    'threads ativas que consomem 15ms de CPU cada uma dentro de um '
                                                    'período (total = 60ms), ele excede a cota de 50ms antes da metade '
                                                    'da janela. O kernel Linux congela forçadamente todas as threads '
                                                    'do container até o início da próxima janela de 100ms, '
                                                    "introduzindo 'latência fantasma'.",
                                    'how_it_works_en': 'Linux CFS enforces container CPU limits using Completely Fair '
                                                       'Scheduler quotas. CPU limits are converted into '
                                                       '`cpu.cfs_quota_us` over a period `cpu.cfs_period_us` '
                                                       '(typically 100ms). If a multi-threaded application consumes '
                                                       'its allocated quota in the first 20ms of a 100ms period, the '
                                                       'kernel freezes (throttles) all threads for the remaining 80ms, '
                                                       'generating severe latency spikes even when node CPU is mostly '
                                                       'idle.',
                                    'resource_title': 'Linux CFS (Completely Fair Scheduler), Cgroups & CPU Quotas',
                                    'resource_title_en': 'Linux CFS (Completely Fair Scheduler), Cgroups & CPU Quotas'},
                      'description': 'A latência da API subiu para 1.8s nos percentis P95 e P99, mas o uso médio de '
                                     'CPU exibido no Grafana é de apenas 28%. O Completely Fair Scheduler (CFS) do '
                                     'Linux está aplicando throttling de 80% nos ciclos de 100ms devido a um CPU limit '
                                     'rígido muito baixo (500m).',
                      'description_en': 'P99 latency spiked to 1.8s despite average CPU usage showing only 28%. Linux '
                                        'CFS is enforcing 80% quota throttling due to tight 500m CPU limits.',
                      'detection_delay_seconds': 40,
                      'difficulty': 'hard',
                      'hints': [ { 'hint': 'Inspecione a métrica de container_cpu_cfs_throttled_periods_total.',
                                   'hint_en': 'Inspect container_cpu_cfs_throttled_periods_total metric.'},
                                 { 'hint': 'Aumente o limite de CPU para 2000m com kubectl set resources.',
                                   'hint_en': 'Increase CPU limits to 2000m using kubectl set resources.'}],
                      'icon': '⏱️',
                      'id': 'cpu-throttling',
                      'investigation_delay_seconds': 85,
                      'runbook': '/docs/runbooks/cpu-throttling',
                      'runbook_steps': { 'diagnosis': [ 'kubectl top pods -l app=sre-rag-api (CPU média em 280m de '
                                                        '1000m).',
                                                        'cat /sys/fs/cgroup/cpu/cpu.stat (nr_throttled / nr_periods > '
                                                        '70%).',
                                                        'PromQL: '
                                                        'sum(rate(container_cpu_cfs_throttled_seconds_total[5m])) by '
                                                        '(pod).'],
                                         'diagnosis_en': [ 'PromQL: '
                                                           'sum(rate(container_cpu_cfs_throttled_periods_total[5m])) / '
                                                           'sum(rate(container_cpu_cfs_periods_total[5m])) * 100 (> '
                                                           '40%).',
                                                           'kubectl top pod shows pod using 500m out of 500m limit.',
                                                           'Thread dumps show threads sleeping on CFS schedule waits.'],
                                         'mitigation': { 'action': 'Remover o limite rígido de CPU no Helm, mantendo '
                                                                   'os requests intactos.',
                                                         'command': 'helm upgrade sre-rag ./helm/sre-rag --set '
                                                                    'api.resources.limits.cpu=null --reuse-values',
                                                         'validation': 'Monitorar queda imediata de '
                                                                       'container_cpu_cfs_throttled_periods para '
                                                                       'zero.'},
                                         'mitigation_en': { 'action_en': 'Double CPU limits from 500m to 2000m to '
                                                                         'eliminate CFS bandwidth throttling.',
                                                            'command': 'kubectl set resources deployment sre-rag-api '
                                                                       '-c api --limits=cpu=2000m',
                                                            'validation_en': 'Throttling rate drops to 0% and P99 '
                                                                             'latency returns to baseline < 50ms.'},
                                         'prevention': [ 'Dashboard do Grafana monitorando expressamente métricas de '
                                                         'CFS Throttling em percentuais.',
                                                         'Configurar CPU requests dimensionados com base no percentil '
                                                         '95 de carga.'],
                                         'prevention_en': [ 'Alert whenever CPU throttling exceeds 10% for longer than '
                                                            '3 minutes.',
                                                            'Benchmark multi-threaded concurrency before sizing '
                                                            'container CPU limits.'],
                                         'root_cause': { 'analysis': 'A aplicação utiliza pool multi-thread em '
                                                                     'Python/FastAPI. Em rajadas rápidas de 10ms, '
                                                                     'todas as threads disparam em paralelo, '
                                                                     'consumindo a cota de 100ms do CFS e ficando '
                                                                     'congeladas pelo resto da janela.',
                                                         'permanent_fix': 'Adotar padrão No-CPU-Limits recomendado por '
                                                                          'engenheiros do Google e CERN para '
                                                                          'microsserviços.'},
                                         'root_cause_en': { 'analysis_en': 'Multi-threaded tokenization in '
                                                                           'sentence-transformers exhausted CFS quota '
                                                                           'in bursts.',
                                                            'permanent_fix_en': 'Set GOMAXPROCS / OMP_NUM_THREADS to '
                                                                                'match CPU quota or remove rigid CPU '
                                                                                'limits in production values.'},
                                         'triage': [ 'Alerta ContainerHighCPUThrottling (> 50% dos períodos '
                                                     'estrangulados).',
                                                     'P99 de latência degradado enquanto métricas médias de CPU '
                                                     'parecem baixas.',
                                                     'Fila de requisições acumulando no proxy reverso.'],
                                         'triage_en': [ 'Check alert: SevereCPUThrottling (>25% periods throttled).',
                                                        "Inspect Golden Signal 'Latency': P99 increases 10x while node "
                                                        'CPU utilization remains under 30%.',
                                                        'Verify container throttling metrics in Prometheus.']},
                      'severity': 'SEV-2',
                      'solutions': [ { 'command': 'helm upgrade sre-rag ./helm/sre-rag --set '
                                                  'api.resources.limits.cpu=null --reuse-values',
                                       'correct': True,
                                       'explanation': '✅ Correto! A recomendação moderna da comunidade de SRE e '
                                                      'Kubernetes é não fixar CPU limits para microsserviços sensíveis '
                                                      'a latência, permitindo bursts sem penalidade do CFS.',
                                       'explanation_en': '✅ Correct! Removing CPU limits eliminates CFS scheduler '
                                                         'stalls during multi-threaded bursts.',
                                       'id': 'remove-cpu-limit',
                                       'label': 'Remover o hard limit de CPU (`limits.cpu=null`) mantendo requests '
                                                'adequados',
                                       'label_en': 'Remove hard CPU limit (`limits.cpu=null`) while keeping proper '
                                                   'requests'},
                                     { 'command': 'kubectl scale deployment sre-rag-api --replicas=6',
                                       'correct': False,
                                       'explanation': '❌ Ineficiente. Se threads individuais sofrem burst durante '
                                                      'processamento de requisição, o CFS estrangula o processo mesmo '
                                                      'com múltiplos pods ociosos.',
                                       'explanation_en': '❌ Inefficient. Multi-threaded bursts will still get '
                                                         'throttled per-pod regardless of replica count.',
                                       'id': 'double-replicas',
                                       'label': 'Dobrar as réplicas mantendo o mesmo CPU limit',
                                       'label_en': 'Double replicas while retaining strict CPU limit'},
                                     { 'command': 'helm upgrade sre-rag ./helm/sre-rag --set '
                                                  'api.resources.requests.cpu=100m',
                                       'correct': False,
                                       'explanation': '❌ Piora o problema. Reduzir requests enfraquece a garantia de '
                                                      'recursos concedida pelo Kube-Scheduler aos nós.',
                                       'explanation_en': '❌ Makes it worse by weakening resource scheduling '
                                                         'guarantees.',
                                       'id': 'lower-requests',
                                       'label': 'Diminuir os requests de CPU para 100m',
                                       'label_en': 'Lower CPU requests to 100m'}],
                      'symptoms': [ 'P99 latency: 1800ms (SLO violado sob carga moderada)',
                                    'Uso médio de CPU do pod em apenas 28% nos dashboards',
                                    'cgroup cpu.stat: throttled_periods > 75% dos períodos',
                                    'Alertmanager: ContainerHighCPUThrottling FIRING'],
                      'symptoms_en': [ 'P99 latency: 1800ms (SLO violated under moderate load)',
                                       'Average CPU utilization shows merely 28% in dashboards',
                                       'cgroup cpu.stat: throttled_periods > 75% of periods',
                                       'Alertmanager: ContainerHighCPUThrottling FIRING'],
                      'title': 'Severe CFS CPU Throttling (Latência Fantasma)',
                      'title_en': 'Severe CFS CPU Throttling (Ghost Latency)'},
  'crashloopbackoff': { 'category': 'Confiabilidade',
                        'category_en': 'Reliability',
                        'chaos_action': None,
                        'command': 'helm upgrade sre-rag ./helm/sre-rag --set api.probes.startup.failureThreshold=30',
                        'concepts': { 'architecture_components': [ 'Kubelet Health Monitor',
                                                                   'HTTPGetAction',
                                                                   'Pod Lifecycle States'],
                                      'best_practices': [ 'Nunca use liveness probe para verificar dependências '
                                                          'externas (como banco de dados fora do pod).',
                                                          'Use startup probe com failureThreshold generoso para evitar '
                                                          'CrashLoopBackOff desnecessário.',
                                                          'Readiness probes devem ser rápidas (< 1s) para responder '
                                                          'prontamente a variações de carga.'],
                                      'best_practices_en': [ 'Always use a Startup Probe for apps with heavy '
                                                             'initialization (AI models, JVM, cache warming).',
                                                             'Do not point Liveness Probe to external dependencies '
                                                             '(e.g. database), only verify internal process liveness.',
                                                             'Readiness Probe should remove unready pods from Service '
                                                             'endpoints without killing the process.'],
                                      'category_en': 'Reliability',
                                      'golden_signals': [ 'Disponibilidade de Endpoints (Ready Pods Count)',
                                                          'Tempo de Inicialização de Aplicação (Container Startup '
                                                          'Duration)'],
                                      'golden_signals_en': ['Container Restarts Total', 'Pod Liveness Failure Count'],
                                      'how_it_works': 'O Kubelet executa três probes: A `startupProbe` desativa as '
                                                      'outras probes até que ela passe pela primeira vez, protegendo '
                                                      'boots demorados. A `livenessProbe` reinicia o container se ele '
                                                      'travar em deadlock. A `readinessProbe` remove o pod do Service '
                                                      '(endpoints) se ele estiver temporariamente sobrecarregado, sem '
                                                      'matá-lo.',
                                      'how_it_works_en': 'Kubelet executes probes via HTTP, TCP or Exec. The Startup '
                                                         'Probe protects slow-initializing workloads by disabling '
                                                         'Liveness and Readiness checks until it succeeds. If initial '
                                                         'model loading exceeds `initialDelaySeconds + '
                                                         '(failureThreshold * periodSeconds)`, Liveness probe kills '
                                                         'the pod, causing a continuous CrashLoopBackOff loop.',
                                      'resource_title': 'Kubernetes Health Checks: Startup vs Liveness vs Readiness '
                                                        'Probes',
                                      'resource_title_en': 'Kubernetes Health Checks: Startup vs Liveness vs Readiness '
                                                           'Probes'},
                        'description': 'Pods recém-implantados demoram 40s para carregar os pesos do modelo vetorial '
                                       'na inicialização, mas a startupProbe tem timeout agressivo de 10s. O Kubelet '
                                       'reinicia o pod em loop infinito.',
                        'description_en': 'New pods require 40s to initialize the local embedding model, but '
                                          'startupProbe has a strict 10s timeout, causing infinite restart loops.',
                        'detection_delay_seconds': 20,
                        'difficulty': 'medium',
                        'hints': [ { 'hint': 'Verifique o motivo das reinicializações com kubectl describe pod.',
                                     'hint_en': 'Check restart reasons using kubectl describe pod.'},
                                   { 'hint': 'Aumente o failureThreshold da StartupProbe usando kubectl patch.',
                                     'hint_en': 'Increase the failureThreshold of StartupProbe using kubectl patch.'}],
                        'icon': '🔄',
                        'id': 'crashloopbackoff',
                        'investigation_delay_seconds': 60,
                        'runbook': '/docs/runbooks/crashloopbackoff',
                        'runbook_steps': { 'diagnosis': [ 'kubectl get pods -l app=sre-rag-api (CrashLoopBackOff).',
                                                          'kubectl describe pod <nome-do-pod> (Warning Unhealthy: '
                                                          'Startup probe failed: HTTP probe failed with statuscode: '
                                                          '503).',
                                                          'kubectl logs <nome-do-pod> (Loading embedding weights: 65% '
                                                          'completo quando recebe SIGTERM).'],
                                           'diagnosis_en': [ 'kubectl describe pod (Liveness probe failed: HTTP probe '
                                                             'failed with statuscode: 503).',
                                                             'kubectl logs pod --previous (Model downloading/loading '
                                                             'interrupted by SIGKILL).',
                                                             'Check initialization duration: model load takes 45s, '
                                                             'probe timeout was 10s.'],
                                           'mitigation': { 'action': 'Aumentar o failureThreshold da startup probe '
                                                                     'para 30 no Helm.',
                                                           'command': 'helm upgrade sre-rag ./helm/sre-rag --set '
                                                                      'api.probes.startup.failureThreshold=30',
                                                           'validation': 'kubectl rollout status '
                                                                         'deployment/sre-rag-api'},
                                           'mitigation_en': { 'action_en': 'Adjust Startup Probe failureThreshold to '
                                                                           '30 (allowing up to 150s startup window).',
                                                              'command': 'kubectl patch deployment sre-rag-api '
                                                                         '--type=\'json\' -p=\'[{"op": "replace", '
                                                                         '"path": '
                                                                         '"/spec/template/spec/containers/0/startupProbe/failureThreshold", '
                                                                         '"value": 30}]\'',
                                                              'validation_en': 'Pod completes startup sequence and '
                                                                               'enters Running (Ready: 1/1) state.'},
                                           'prevention': [ 'Sempre desacoplar startupProbe de livenessProbe em '
                                                           'aplicações que carregam dados pesados na inicialização.',
                                                           'Testes de carga de boot em pipeline de homologação antes '
                                                           'de ir para produção.'],
                                           'prevention_en': [ 'Pre-bake ML model weights into container image or use '
                                                              'shared read-only persistent cache.',
                                                              'Separate initialization probes from runtime liveness '
                                                              'probes.'],
                                           'root_cause': { 'analysis': 'Inclusão de modelo de machine learning maior '
                                                                       'sem ajuste correspondente no tempo de '
                                                                       'tolerância de boot.',
                                                           'permanent_fix': 'Aquecer cache de modelos em InitContainer '
                                                                            'ou usar volume compartilhado com pesos '
                                                                            'pré-carregados.'},
                                           'root_cause_en': { 'analysis_en': 'Sentence-transformers model weight cache '
                                                                             'cold-start requires 45 seconds, '
                                                                             'exceeding probe allowance.',
                                                              'permanent_fix_en': 'Configure dedicated Startup Probe '
                                                                                  'with failureThreshold: 30 and bake '
                                                                                  'model weights into container '
                                                                                  'image.'},
                                           'triage': [ 'Alerta KubePodCrashLooping no cluster.',
                                                       'Rollout do Deployment travado (0/2 réplicas prontas).',
                                                       'Ingress reportando 502 Bad Gateway por ausência de endpoints.'],
                                           'triage_en': [ 'Check alert: KubePodCrashLooping.',
                                                          'Inspect pod status: CrashLoopBackOff with restart count '
                                                          'climbing.',
                                                          'Verify container termination reason: Liveness probe '
                                                          'failed.']},
                        'severity': 'SEV-1',
                        'solutions': [ { 'command': 'helm upgrade sre-rag ./helm/sre-rag --set '
                                                    'api.probes.startup.failureThreshold=30',
                                         'correct': True,
                                         'explanation': '✅ Correto! O startupProbe foi criado exatamente para proteger '
                                                        'aplicações de boot lento sem comprometer a rapidez da '
                                                        'livenessProbe em produção.',
                                         'explanation_en': '✅ Correct! Startup probes shield slow-initializing '
                                                           'applications while keeping liveness probes sensitive.',
                                         'id': 'adjust-startup-probe',
                                         'label': 'Aumentar failureThreshold da startupProbe para 30 (permitindo 60s '
                                                  'de inicialização)',
                                         'label_en': 'Increase startupProbe failureThreshold to 30 (permits 60s '
                                                     'initialization)'},
                                       { 'command': 'kubectl patch deployment sre-rag-api --patch '
                                                    '\'{"spec":{"template":{"spec":{"containers":[{"name":"api","livenessProbe":null}]}}}}\'',
                                         'correct': False,
                                         'explanation': '❌ Anti-pattern grave! Desativar probes remove a capacidade do '
                                                        'Kubernetes de substituir pods travados, piorando a '
                                                        'confiabilidade.',
                                         'explanation_en': '❌ Severe anti-pattern! Disabling probes routes traffic to '
                                                           'dead pods indefinitely.',
                                         'id': 'disable-probes',
                                         'label': 'Desativar livenessProbe e readinessProbe no deployment',
                                         'label_en': 'Disable readiness and liveness probes in deployment spec'},
                                       { 'command': 'helm rollback sre-rag',
                                         'correct': False,
                                         'explanation': '⚠️ Ineficaz caso a versão anterior também utilize modelos '
                                                        'locais sem tempo de boot configurado.',
                                         'explanation_en': '⚠️ Ineffective if the prior release also lacks proper '
                                                           'startup probe timeouts.',
                                         'id': 'rollback',
                                         'label': 'Rollback imediato da release Helm',
                                         'label_en': 'Immediate rollback via Helm'}],
                        'symptoms': [ 'kubectl get pods: sre-rag-api-* CrashLoopBackOff (restarts: 6)',
                                      'kubectl describe pod: Startup probe failed: HTTP probe failed with statuscode: '
                                      '503',
                                      'Zero endpoints no Service (Endpoints: <none>)',
                                      'HTTP 502 Bad Gateway no Ingress'],
                        'symptoms_en': [ 'kubectl get pods: sre-rag-api-* CrashLoopBackOff (restarts: 6)',
                                         'kubectl describe pod: Startup probe failed: HTTP probe failed with '
                                         'statuscode: 503',
                                         'Zero endpoints ready in Service (Endpoints: <none>)',
                                         'HTTP 502 Bad Gateway at ingress level'],
                        'title': 'Startup Probe Timeout (Modelo RAG Lento)',
                        'title_en': 'Startup Probe Timeout (Slow Model Loading)'},
  'db-pool-starvation': { 'category': 'Concorrência',
                          'category_en': 'Concurrency',
                          'chaos_action': None,
                          'command': 'kubectl exec -i sts/postgresql-0 -- psql -U postgres -d sre_db -c "SELECT '
                                     "pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle in "
                                     'transaction\' AND state_change < now() - INTERVAL \'2 minutes\';"',
                          'concepts': { 'architecture_components': [ 'PostgreSQL Backend Processes',
                                                                     'pg_stat_activity',
                                                                     'PgBouncer Connection Pooler'],
                                        'best_practices': [ 'Sempre defina `idle_in_transaction_session_timeout` no '
                                                            'PostgreSQL para que o próprio banco mate conexões '
                                                            'abandonadas.',
                                                            'Utilize PgBouncer entre a aplicação e o banco para '
                                                            'multiplexar centenas de conexões da API em um pool enxuto '
                                                            'de 20 conexões no PostgreSQL.',
                                                            'Mantenha transações atômicas e o mais curtas possível.'],
                                        'best_practices_en': [ 'Never connect directly from microservice pods to '
                                                               'PostgreSQL in high-throughput clusters; place '
                                                               'PgBouncer in front.',
                                                               'Use transaction-level pooling in PgBouncer to '
                                                               'multiplex thousands of client connections onto tens of '
                                                               'server backends.',
                                                               'Configure `idle_in_transaction_session_timeout = '
                                                               '60000` to terminate leaked transactions automatically.',
                                                               'Configure application connection pool min_idle and '
                                                               'max_overflow sensibly.'],
                                        'category_en': 'Concurrency',
                                        'golden_signals': [ 'Uso de Slots de Conexão no Banco (Postgres Connection '
                                                            'Usage %)',
                                                            'Transações em Idle Longas (Max Idle-in-Transaction '
                                                            'Duration)'],
                                        'golden_signals_en': [ 'PostgreSQL Active Connections / Max Connections %',
                                                               'Idle in Transaction Sessions Duration'],
                                        'how_it_works': 'Diferente de sistemas multithread, o PostgreSQL utiliza um '
                                                        'modelo baseado em processos (fork de processo para cada '
                                                        'cliente conectado). Cada conexão consome de 5 a 10MB de RAM. '
                                                        'Quando uma transação fica presa em `idle in transaction`, ela '
                                                        'não apenas retém um slot de conexão valioso, mas também '
                                                        'impede o vacuum de limpar tuplas mortas (MVCC dead tuples) e '
                                                        'mantém table locks ativos.',
                                        'how_it_works_en': 'PostgreSQL spawns a separate OS process for each client '
                                                           'connection (`backend process`), consuming 5-10MB of RAM '
                                                           'each. When application services scale out without a proxy '
                                                           'pool, connections exceed `max_connections` (default 100). '
                                                           'Long-running transactions or unclosed sessions stay in '
                                                           '`idle in transaction` state, holding locks and starving '
                                                           'incoming requests.',
                                        'resource_title': 'PostgreSQL Process Architecture, MVCC & Transaction Pooling '
                                                          'com PgBouncer',
                                        'resource_title_en': 'PostgreSQL Process Architecture, MVCC & Transaction '
                                                             'Pooling with PgBouncer'},
                          'description': "A API retorna 'FATAL: remaining connection slots are reserved for "
                                         "non-replication superuser connections'. Há 100 conexões abertas no "
                                         "PostgreSQL, a maioria presas em 'idle in transaction' por falta de "
                                         'fechamento de blocos contextuais no código.',
                          'description_en': "API returns 'FATAL: remaining connection slots are reserved'. PostgreSQL "
                                            "saturated with 100 open connections stuck in 'idle in transaction'.",
                          'detection_delay_seconds': 35,
                          'difficulty': 'extreme',
                          'hints': [ { 'hint': 'Verifique conexões em idle in transaction no PostgreSQL via '
                                               'pg_stat_activity.',
                                       'hint_en': 'Check idle in transaction connections in PostgreSQL via '
                                                  'pg_stat_activity.'},
                                     { 'hint': 'Finalize conexões presas usando pg_terminate_backend.',
                                       'hint_en': 'Terminate stuck connections using pg_terminate_backend.'}],
                          'icon': '🐘',
                          'id': 'db-pool-starvation',
                          'investigation_delay_seconds': 85,
                          'runbook': '/docs/runbooks/db-pool-starvation',
                          'runbook_steps': { 'diagnosis': [ 'psql -c "SELECT count(*), state FROM pg_stat_activity '
                                                            'GROUP BY state;" (95 em idle in transaction).',
                                                            'psql -c "SELECT pid, now() - state_change as duration, '
                                                            "query FROM pg_stat_activity WHERE state = 'idle in "
                                                            'transaction\';"',
                                                            'Identificação de transação aberta sem COMMIT nem '
                                                            'ROLLBACK.'],
                                             'diagnosis_en': [ 'psql: SELECT count(*), state FROM pg_stat_activity '
                                                               'GROUP BY state (95 sessions idle in transaction).',
                                                               'SELECT pid, now() - query_start AS duration, query '
                                                               "FROM pg_stat_activity WHERE state = 'idle in "
                                                               "transaction' ORDER BY duration DESC.",
                                                               'Check lock contention in pg_locks.'],
                                             'mitigation': { 'action': 'Executar pg_terminate_backend nas conexões '
                                                                       'ociosas há mais de 2 minutos.',
                                                             'command': 'kubectl exec -i sts/postgresql-0 -- psql -U '
                                                                        'postgres -d sre_db -c "SELECT '
                                                                        'pg_terminate_backend(pid) FROM '
                                                                        "pg_stat_activity WHERE state = 'idle in "
                                                                        "transaction' AND state_change < now() - "
                                                                        'INTERVAL \'2 minutes\';"',
                                                             'validation': 'curl -s '
                                                                           'http://localhost:8080/api/v1/health | jq '
                                                                           ".status (Retorna 'healthy')."},
                                             'mitigation_en': { 'action_en': 'Terminate idle in transaction sessions '
                                                                             'and reload configuration with higher '
                                                                             'temporary limit.',
                                                                'command': 'psql -c "SELECT pg_terminate_backend(pid) '
                                                                           "FROM pg_stat_activity WHERE state = 'idle "
                                                                           "in transaction' AND now() - state_change > "
                                                                           'interval \'1 minute\';"',
                                                                'validation_en': 'Active connection count drops to < '
                                                                                 '20 and API transactions succeed.'},
                                             'prevention': [ 'Configurar `idle_in_transaction_session_timeout = 30000` '
                                                             '(30s) no `postgresql.conf`.',
                                                             'Implantar PgBouncer em modo transaction pooling na '
                                                             'frente do PostgreSQL.'],
                                             'prevention_en': [ 'Deploy PgBouncer pooler in transaction pooling mode.',
                                                                'Monitor pg_stat_activity using '
                                                                'prometheus-postgres-exporter.'],
                                             'root_cause': { 'analysis': 'Uma rota de ingestão abria transação de '
                                                                         'escrita e fazia chamada HTTP externa para a '
                                                                         'API do OpenAI dentro do bloco transacional, '
                                                                         'segurando a conexão aberta por dezenas de '
                                                                         'segundos.',
                                                             'permanent_fix': 'Nunca realizar chamadas de rede ou IO '
                                                                              'externo dentro de transações de banco '
                                                                              'de dados.'},
                                             'root_cause_en': { 'analysis_en': 'Application worker failed to '
                                                                               'commit/rollback transactions on '
                                                                               'unhandled HTTP client disconnects.',
                                                                'permanent_fix_en': 'Set '
                                                                                    'idle_in_transaction_session_timeout '
                                                                                    "= '30s' in postgresql.conf and "
                                                                                    'deploy PgBouncer.'},
                                             'triage': [ 'Alerta PostgresTooManyConnections (> 95% do '
                                                         'max_connections).',
                                                         'API lançando OperationalError: FATAL remaining connection '
                                                         'slots.',
                                                         'Taxa de erro 500 em todas as rotas que realizam '
                                                         'persistência.'],
                                             'triage_en': [ 'Check alert: PostgresqlConnectionPoolStarvation.',
                                                            'Inspect API logs: OperationalError: FATAL: remaining '
                                                            'connection slots are reserved for non-replication '
                                                            'superuser connections.',
                                                            'Verify API database queries timing out.']},
                          'severity': 'SEV-1',
                          'solutions': [ { 'command': 'kubectl exec -i sts/postgresql-0 -- psql -U postgres -d sre_db '
                                                      '-c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity '
                                                      "WHERE state = 'idle in transaction' AND state_change < now() - "
                                                      'INTERVAL \'2 minutes\';"',
                                           'correct': True,
                                           'explanation': '✅ Correto! Finalizar as conexões zumbis presas em idle in '
                                                          'transaction libera os slots de conexão imediatamente sem '
                                                          'derrubar o banco de dados.',
                                           'explanation_en': '✅ Correct! Killing orphaned idle transactions instantly '
                                                             'reclaims connection slots without taking down the '
                                                             'database.',
                                           'id': 'terminate-idle-tx',
                                           'label': 'Encerrar transações órfãs com `pg_terminate_backend` para liberar '
                                                    'slots',
                                           'label_en': 'Terminate orphaned transactions via `pg_terminate_backend`'},
                                         { 'command': "kubectl exec -i sts/postgresql-0 -- psql -c 'ALTER SYSTEM SET "
                                                      "max_connections = 5000;'",
                                           'correct': False,
                                           'explanation': '❌ Desastroso. Cada conexão no PostgreSQL aloca memória '
                                                          'dedicada no Linux (work_mem + shared buffers). 5000 '
                                                          'conexões causariam OOM Kill no processo do banco.',
                                           'explanation_en': '❌ Dangerous. Each connection consumes private memory; '
                                                             '5000 connections will trigger kernel OOM on PostgreSQL.',
                                           'id': 'increase-max-connections',
                                           'label': 'Aumentar max_connections no postgresql.conf para 5000',
                                           'label_en': 'Increase max_connections to 5000 in postgresql.conf'},
                                         { 'command': 'kubectl exec -i sts/postgresql-0 -- dropdb sre_db',
                                           'correct': False,
                                           'explanation': '❌ Destrutivo! Apagar o banco acarreta perda irreversível de '
                                                          'dados de produção.',
                                           'explanation_en': '❌ Destructive. Results in complete data loss.',
                                           'id': 'drop-database',
                                           'label': 'Recriar o schema do banco de dados',
                                           'label_en': 'Recreate database schema'}],
                          'symptoms': [ 'PostgreSQL logs: FATAL: remaining connection slots are reserved',
                                        "pg_stat_activity: 95 conexões em 'idle in transaction' há mais de 10 min",
                                        'Novas requisições da API falham imediatamente com HTTP 500',
                                        'CPU do banco em 5%, mas capacidade de conexões em 100%'],
                          'symptoms_en': [ 'PostgreSQL logs: FATAL: remaining connection slots are reserved',
                                           "pg_stat_activity: 95 connections in 'idle in transaction' > 10m",
                                           'Incoming requests immediately reject with HTTP 500',
                                           'Database CPU at 5%, but connection capacity at 100%'],
                          'title': 'PostgreSQL Connection Pool Starvation & Idle Locks',
                          'title_en': 'PostgreSQL Connection Pool Starvation & Idle Locks'},
  'disk-pressure': { 'category': 'Armazenamento',
                     'category_en': 'Storage',
                     'chaos_action': None,
                     'command': 'crictl rmi --prune',
                     'concepts': { 'architecture_components': [ 'Kubelet Eviction Manager',
                                                                'CRI (containerd / crictl)',
                                                                'DiskPressure Taints'],
                                   'best_practices': [ 'Configure image garbage collection agressivo em ambientes com '
                                                       'pipelines de CI/CD contínuos.',
                                                       'Mantenha logs dos containers em partição separada ou encaminhe '
                                                       'em streaming para agente de logging (FluentBit / Vector).',
                                                       'Configure alertas de saturação de disco em 70% e 80% antes de '
                                                       'atingir o limite de evicção.'],
                                   'best_practices_en': [ 'Configure separate physical partitions/mount points for '
                                                          'container runtime images (`imagefs`) and root OS '
                                                          '(`nodefs`).',
                                                          'Set up crictl rmi / docker prune scheduled jobs or tune '
                                                          'Kubelet imageGCLowThresholdPercent to 70%.',
                                                          'Send node disk alerts at 75% utilization to remediate '
                                                          'before hard eviction at 90%.'],
                                   'category_en': 'Storage',
                                   'golden_signals': [ 'Uso de Disco do Nó (Node Root Filesystem %)',
                                                       'Taxa de Evicção de Pods (Pod Eviction Rate)'],
                                   'golden_signals_en': [ 'Node Root Filesystem Available %',
                                                          'Pod Eviction Count by Node'],
                                   'how_it_works': 'O Kubelet monitora periodicamente os limites de disco do nó. '
                                                   'Quando o uso ultrapassa o threshold de evicção (padrão 85%), o '
                                                   'Kubelet ativa a condição `DiskPressure` e aplica a taint '
                                                   '`node.kubernetes.io/disk-pressure:NoSchedule`. Para recuperar '
                                                   'espaço, o Kubelet tenta primeiro deletar imagens de containers não '
                                                   'utilizadas. Se o espaço continuar crítico, o Eviction Manager '
                                                   'encerra pods com base na classe de QoS até que o disco volte '
                                                   'abaixo do limite seguro.',
                                   'how_it_works_en': 'Kubelet monitors node root filesystem and imagefs. When '
                                                      'available disk drops below `imageGCHighThresholdPercent` '
                                                      '(default 85%), kubelet triggers Image GC. If disk falls below '
                                                      '`evictionHard: nodefs.available<10%`, kubelet sets '
                                                      'NodeCondition `DiskPressure=True`, stops scheduling new pods, '
                                                      'and begins evicting pods according to QoS classes.',
                                   'resource_title': 'Kubelet Eviction Manager, Node Conditions & Image Garbage '
                                                     'Collection',
                                   'resource_title_en': 'Kubelet Eviction Manager, Node Conditions & Image Garbage '
                                                        'Collection'},
                     'description': 'Um nó worker entrou em condição DiskPressure (> 85% de uso no disco raiz). O '
                                    'Kubelet começou a evictar pods não críticos para proteger o sistema operacional '
                                    'de um congelamento do kernel.',
                     'description_en': 'Worker node entered DiskPressure condition (> 85% disk utilization). Kubelet '
                                       'started evicting pods to protect kernel operation.',
                     'detection_delay_seconds': 50,
                     'difficulty': 'hard',
                     'hints': [ { 'hint': 'Verifique a condição dos nós com kubectl describe node.',
                                  'hint_en': 'Check node conditions using kubectl describe node.'},
                                { 'hint': 'Execute crictl rmi --prune no nó para limpar imagens não utilizadas.',
                                  'hint_en': 'Run crictl rmi --prune on the node to clean unused images.'}],
                     'icon': '💾',
                     'id': 'disk-pressure',
                     'investigation_delay_seconds': 100,
                     'runbook': '/docs/runbooks/disk-pressure',
                     'runbook_steps': { 'diagnosis': [ 'kubectl get nodes (Condition: DiskPressure = True).',
                                                       'kubectl describe node <node-name> (Eviction threshold met on '
                                                       'rootfs /var/lib/containerd).',
                                                       'ssh no nó ou container debug: df -h /var/lib/docker (88% '
                                                       'ocupado).'],
                                        'diagnosis_en': [ 'kubectl describe node <node> | grep -A 5 Conditions '
                                                          '(DiskPressure: True).',
                                                          'df -h on node shows /var/lib/containerd or /var/log at 96% '
                                                          'utilization.',
                                                          'Inspect container log files size under /var/log/pods.'],
                                        'mitigation': { 'action': 'Executar limpeza de imagens não utilizadas pelo '
                                                                  'container runtime.',
                                                        'command': 'crictl rmi --prune',
                                                        'validation': 'kubectl describe node <node-name> (Condition: '
                                                                      'DiskPressure = False).'},
                                        'mitigation_en': { 'action_en': 'Trigger container image and dangling layer '
                                                                        'cleanup via crictl on the node.',
                                                           'command': 'crictl rmi --prune',
                                                           'validation_en': 'Node disk usage drops to 60% and '
                                                                            'DiskPressure condition clears to False.'},
                                        'prevention': [ 'Monitorar espaço em disco dos nós com alerta de tendência '
                                                        'predict_linear em 6 horas.',
                                                        'Separar discos de dados persistentes (/var/lib/kubelet) do '
                                                        'disco do sistema operacional.'],
                                        'prevention_en': [ 'Deploy node-problem-detector with automatic remediation '
                                                           'daemonset.',
                                                           'Configure logrotate for container log directories.'],
                                        'root_cause': { 'analysis': 'Acúmulo de imagens de builds temporários antigos '
                                                                    'sem política de garbage collection agressiva no '
                                                                    'Kubelet.',
                                                        'permanent_fix': 'Configurar Kubelet flags '
                                                                         '`--image-gc-high-threshold=80` e '
                                                                         '`--image-gc-low-threshold=60`.'},
                                        'root_cause_en': { 'analysis_en': 'Old unused container images accumulated on '
                                                                          'node disk without garbage collection.',
                                                           'permanent_fix_en': 'Configure kubelet flags '
                                                                               '--image-gc-high-threshold=80 and '
                                                                               '--image-gc-low-threshold=65.'},
                                        'triage': [ 'Alerta KubeNodeDiskPressure disparado no Prometheus.',
                                                    "Pods com status 'Evicted' acumulando no namespace.",
                                                    'Kubelet aplicando taint '
                                                    'node.kubernetes.io/disk-pressure:NoSchedule.'],
                                        'triage_en': [ 'Check alert: KubeNodeDiskPressure.',
                                                       'Inspect node status: kubectl get nodes (Node status: '
                                                       'Ready,SchedulingDisabled,DiskPressure).',
                                                       'Verify pods being evicted with reason Evicted.']},
                     'severity': 'SEV-2',
                     'solutions': [ { 'command': 'crictl rmi --prune',
                                      'correct': True,
                                      'explanation': '✅ Correto! Limpar imagens de containers obsoletas e rotacionar '
                                                     'logs de pods libera espaço imediatamente, removendo a condição '
                                                     'DiskPressure do nó.',
                                      'explanation_en': '✅ Correct! Cleaning stale container images instantly recovers '
                                                        'disk space and clears the taint.',
                                      'id': 'prune-images-logs',
                                      'label': 'Executar `crictl rmi --prune` para remover imagens não utilizadas e '
                                               'liberar disco',
                                      'label_en': 'Run `crictl rmi --prune` to purge unused container images and '
                                                  'recover disk'},
                                    { 'command': 'kubectl delete node node-1',
                                      'correct': False,
                                      'explanation': '⚠️ Drástico e desnecessário. A limpeza de disco é rápida e '
                                                     'resolve o problema sem forçar reagendamento em massa de pods.',
                                      'explanation_en': '⚠️ Excessive. Disk cleanup is fast and avoids cascading '
                                                        'rescheduling pressure.',
                                      'id': 'delete-node',
                                      'label': 'Deletar o nó do cluster imediatamente (`kubectl delete node`)',
                                      'label_en': 'Delete node immediately from the cluster'},
                                    { 'command': 'kubectl patch deployment sre-rag-api --patch '
                                                 '\'{"spec":{"template":{"spec":{"tolerations":[{"key":"node.kubernetes.io/disk-pressure","operator":"Exists"}]}}}}\'',
                                      'correct': False,
                                      'explanation': '❌ Perigoso. Se o disco atingir 100%, o nó inteiro trava, o '
                                                     'filesystem pode corromper e o nó deixa de responder (NotReady).',
                                      'explanation_en': '❌ Dangerous. If disk fills to 100%, node kernel freezes and '
                                                        'filesystem corruption ensues.',
                                      'id': 'ignore-taint',
                                      'label': 'Adicionar tolerations para DiskPressure em todos os pods',
                                      'label_en': 'Add tolerations for DiskPressure to all application pods'}],
                     'symptoms': [ 'kubectl get nodes: Status = Ready,DiskPressure',
                                   'Kubelet: eviction manager threshold met on /var/lib/docker',
                                   'Pods secundários sendo evictados (Evicted); novos pods Pending',
                                   'Disco raiz do nó atingiu 88% de utilização'],
                     'symptoms_en': [ 'kubectl get nodes: Status = Ready,DiskPressure',
                                      'Kubelet: eviction threshold met on container filesystem',
                                      'Pods evicted; newly scheduled pods enter Pending state',
                                      'Root filesystem utilization at 88%'],
                     'title': 'DiskPressure em Node do Kubernetes',
                     'title_en': 'Node DiskPressure Eviction'},
  'dns-failure': { 'category': 'Rede',
                   'category_en': 'Network',
                   'chaos_action': None,
                   'command': 'kubectl rollout restart deployment/coredns -n kube-system',
                   'concepts': { 'architecture_components': [ 'CoreDNS / Kube-DNS',
                                                              'iptables / IPVS Service Routing',
                                                              'NodeLocal DNSCache DaemonSet'],
                                 'best_practices': [ 'Implante o NodeLocal DNSCache para atender lookups diretamente '
                                                     'no cache local do nó via interface dummy de loopback.',
                                                     'Use nomes de domínio totalmente qualificados (FQDN com ponto '
                                                     'final, ex: `postgresql.sre-rag.svc.cluster.local.`) para evitar '
                                                     'buscas desnecessárias do ndots.',
                                                     'Monitore a métrica `coredns_dns_request_duration_seconds` no '
                                                     'Prometheus.'],
                                 'best_practices_en': [ 'Deploy NodeLocal DNSCache to cache DNS queries locally on '
                                                        'each node via loopback IP.',
                                                        'Tune ndots:5 in resolv.conf or use fully qualified domain '
                                                        'names (ending with dot) to prevent search domain loop.',
                                                        'Autoscale CoreDNS using cluster-proportional-autoscaler based '
                                                        'on cluster node and core count.'],
                                 'category_en': 'Network',
                                 'golden_signals': [ 'Latência de Resolução DNS (CoreDNS Lookup Duration ms)',
                                                     'Taxa de Erros SERVFAIL (DNS SERVFAIL Rate %)'],
                                 'golden_signals_en': [ 'CoreDNS Request Duration P99',
                                                        'CoreDNS Response RCODE ServerFailure Rate'],
                                 'how_it_works': 'Cada Pod no cluster recebe `/etc/resolv.conf` apontando para o '
                                                 'ClusterIP do CoreDNS com `options ndots:5`. Quando o pod consulta '
                                                 '`postgresql`, o resolver tenta sequencialmente '
                                                 '`postgresql.<namespace>.svc.cluster.local`, gerando até 5 '
                                                 'requisições UDP na porta 53 para cada lookup. Sob carga, a conntrack '
                                                 'table do Linux e os buffers UDP do CoreDNS sofrem saturação, '
                                                 'descartando pacotes silenciosamente.',
                                 'how_it_works_en': 'Pods resolve domain names via `/etc/resolv.conf` pointing to '
                                                    'kube-dns ClusterIP. CoreDNS pods run as a deployment in '
                                                    '`kube-system`. If CoreDNS pods are under-provisioned, crash, or '
                                                    'hit single-threaded query capacity, DNS queries time out. '
                                                    'Standard glibc resolver retries 5 times with exponential backoff '
                                                    '(5s per search path), causing massive application request latency '
                                                    'and eventual timeouts.',
                                 'resource_title': 'Kubernetes Service DNS, CoreDNS Architecture & NodeLocal DNSCache',
                                 'resource_title_en': 'Kubernetes Service DNS, CoreDNS Architecture & NodeLocal '
                                                      'DNSCache'},
                   'description': 'A aplicação não consegue resolver nomes de serviços internos (`postgresql`, '
                                  "`redis`). Conexões falham com 'Name or service not known'. O CoreDNS travou com "
                                  'descarte massivo de pacotes UDP.',
                   'description_en': 'Application cannot resolve internal cluster service names. CoreDNS is '
                                     'unresponsive and dropping UDP packets.',
                   'detection_delay_seconds': 30,
                   'difficulty': 'extreme',
                   'hints': [ { 'hint': 'Inspecione os pods do CoreDNS no namespace kube-system.',
                                'hint_en': 'Inspect CoreDNS pods in the kube-system namespace.'},
                              { 'hint': 'Escale o CoreDNS para 4 réplicas e reinicie com kubectl rollout restart.',
                                'hint_en': 'Scale CoreDNS to 4 replicas and restart using kubectl rollout restart.'}],
                   'icon': '🌐',
                   'id': 'dns-failure',
                   'investigation_delay_seconds': 75,
                   'runbook': '/docs/runbooks/dns-failure',
                   'runbook_steps': { 'diagnosis': [ 'kubectl run -it --rm test-dns --image=busybox -- nslookup '
                                                     'postgresql.sre-rag.svc.cluster.local (Retorna SERVFAIL).',
                                                     'kubectl get pods -n kube-system -l k8s-app=kube-dns (Verificar '
                                                     'status dos pods).',
                                                     'kubectl logs -n kube-system -l k8s-app=kube-dns (Erros de '
                                                     'timeout e i/o timeout na porta 53).'],
                                      'diagnosis_en': [ 'kubectl get pods -n kube-system -l k8s-app=kube-dns (CoreDNS '
                                                        'pods crashing or running at 100% CPU).',
                                                        'kubectl logs -n kube-system -l k8s-app=kube-dns --tail=50 '
                                                        '(i/o timeout or read: connection refused).',
                                                        'dig @<kube-dns-ip> kubernetes.default.svc.cluster.local times '
                                                        'out.'],
                                      'mitigation': { 'action': 'Reiniciar o Deployment do CoreDNS para restaurar a '
                                                                'pilha de rede.',
                                                      'command': 'kubectl rollout restart deployment/coredns -n '
                                                                 'kube-system',
                                                      'validation': 'kubectl run -it --rm test-dns --image=busybox -- '
                                                                    'nslookup postgresql.sre-rag (Resolve com '
                                                                    'sucesso).'},
                                      'mitigation_en': { 'action_en': 'Scale CoreDNS deployment to 4 replicas and '
                                                                      'restart crashed pods.',
                                                         'command': 'kubectl scale deployment coredns -n kube-system '
                                                                    '--replicas=4 && kubectl rollout restart '
                                                                    'deployment coredns -n kube-system',
                                                         'validation_en': 'DNS lookups succeed within < 2ms across all '
                                                                          'nodes.'},
                                      'prevention': [ 'Configurar autoscaling do CoreDNS baseado em nós e núcleos de '
                                                      'CPU.',
                                                      'Ajustar opções de `ndots: 2` no `dnsConfig` dos pods para '
                                                      'evitar buscas recursivas excessivas.'],
                                      'prevention_en': [ 'Alert immediately if CoreDNS available replicas is less than '
                                                         '2.',
                                                         'Tune pod dnsConfig ndots parameter to reduce spurious DNS '
                                                         'search iterations.'],
                                      'root_cause': { 'analysis': 'Vazamento de descritores de sockets UDP no CoreDNS '
                                                                  'sob alta concorrência de lookups sem cache local '
                                                                  '(NodeLocal DNSCache).',
                                                      'permanent_fix': 'Implantar o NodeLocal DNSCache como DaemonSet '
                                                                       'em todos os nós.'},
                                      'root_cause_en': { 'analysis_en': 'CoreDNS deployment had only 1 replica which '
                                                                        'crashed under traffic spike.',
                                                         'permanent_fix_en': 'Configure '
                                                                             'cluster-proportional-autoscaler and '
                                                                             'enable NodeLocal DNSCache daemonset.'},
                                      'triage': [ 'Alerta KubeDNSDown / CoreDNSErrorsHigh disparado.',
                                                  "Múltiplos microsserviços falhando com 'Name or service not known'.",
                                                  'Tráfego externo caindo por falhas de dependências internas.'],
                                      'triage_en': [ 'Check alert: CoreDNSLatencyHigh or CoreDNSDown.',
                                                     'Inspect API logs: NameResolutionError: Temporary failure in name '
                                                     'resolution.',
                                                     'Verify outbound HTTP calls failing with DNS timeout.']},
                   'severity': 'SEV-1',
                   'solutions': [ { 'command': 'kubectl rollout restart deployment/coredns -n kube-system',
                                    'correct': True,
                                    'explanation': '✅ Correto! O rollout restart recria os pods do CoreDNS, limpando '
                                                   'conexões presas e restabelecendo a resolução de nomes interna '
                                                   'imediatamente.',
                                    'explanation_en': '✅ Correct! Restarting CoreDNS refreshes stale UDP sockets and '
                                                      'restores name resolution.',
                                    'id': 'coredns-restart',
                                    'label': 'Reiniciar CoreDNS pods (`kubectl rollout restart deployment/coredns -n '
                                             'kube-system`)',
                                    'label_en': 'Restart CoreDNS deployment (`kubectl rollout restart '
                                                'deployment/coredns -n kube-system`)'},
                                  { 'command': 'kubectl rollout restart deployment/sre-rag-api',
                                    'correct': False,
                                    'explanation': '❌ Incorreto. Reiniciar a aplicação não resolve falha de DNS do '
                                                   'cluster. Os pods reiniciados falharão exatamente no mesmo ponto de '
                                                   'lookup.',
                                    'explanation_en': '❌ Ineffective. Application restart will fail again at the '
                                                      'identical DNS resolution step.',
                                    'id': 'restart-app',
                                    'label': 'Reiniciar todos os pods da aplicação',
                                    'label_en': 'Restart all application pods'},
                                  { 'command': 'kubectl set env deployment/sre-rag-api DB_HOST=10.96.0.45',
                                    'correct': False,
                                    'explanation': '❌ Anti-pattern gravíssimo. IPs de pods e serviços no Kubernetes '
                                                   'são efêmeros. Usar IPs estáticos quebra a infraestrutura no '
                                                   'próximo deploy.',
                                    'explanation_en': '❌ Severe anti-pattern. Ephemeral cluster IPs will break '
                                                      'permanently on subsequent updates.',
                                    'id': 'use-ip',
                                    'label': 'Substituir nomes de serviço por IPs estáticos nos ConfigMaps',
                                    'label_en': 'Replace service hostnames with static cluster IPs'}],
                   'symptoms': [ 'App logs: socket.gaierror: [Errno -2] Name or service not known',
                                 'nslookup postgresql.sre-rag.svc.cluster.local: SERVFAIL',
                                 'CoreDNS pods em estado de alta utilização de CPU',
                                 'NetworkPolicy pode estar bloqueando porta 53/UDP'],
                   'symptoms_en': [ 'App logs: socket.gaierror: [Errno -2] Name or service not known',
                                    'nslookup postgresql.sre-rag.svc.cluster.local: SERVFAIL',
                                    'CoreDNS pods showing elevated CPU and dropped UDP packets',
                                    'NetworkPolicy potentially blocking port 53/UDP'],
                   'title': 'DNS Resolution Failure (CoreDNS Timeout)',
                   'title_en': 'DNS Resolution Failure (CoreDNS Timeout)'},
  'high-error-rate': { 'category': 'Disponibilidade',
                       'category_en': 'Availability',
                       'chaos_action': 'simulate_500',
                       'command': 'helm rollback sre-rag',
                       'concepts': { 'architecture_components': [ 'Helm 3',
                                                                  'Kubernetes Deployment Rollout',
                                                                  'SLO Burn Rate'],
                                     'best_practices': [ 'Princípio SRE: Mitigue primeiro (Rollback), investigue a '
                                                         'causa raiz depois (RCA).',
                                                         'Deploys imutáveis: cada versão de imagem deve possuir tag de '
                                                         "commit SHA exclusiva, nunca 'latest'.",
                                                         'Alertas de Burn Rate em múltiplas janelas (1h e 6h) para '
                                                         'evitar alertas espúrios e agir antes de esgotar o Error '
                                                         'Budget.'],
                                     'best_practices_en': [ 'SRE Principle: Mitigate first (Rollback), investigate '
                                                            'root cause later (RCA).',
                                                            'Immutable deployments: every container image must have a '
                                                            "unique commit SHA tag, never 'latest'.",
                                                            'Multi-window burn rate alerts (1h and 6h) to prevent '
                                                            'alert fatigue and act before exhausting Error Budget.'],
                                     'category_en': 'Availability',
                                     'golden_signals': [ 'Taxa de Erros HTTP (Error Rate %)',
                                                         'Error Budget Consumed (Burn Rate 1h e 6h)'],
                                     'golden_signals_en': [ 'HTTP Error Rate %',
                                                            'Error Budget Consumed (Burn Rate 1h and 6h)'],
                                     'how_it_works': 'O Helm gerencia revisões armazenando manifestos como Secrets ou '
                                                     'ConfigMaps versionados. Quando um deploy quebra, o comando `helm '
                                                     'rollback` reaplica o manifesto da revisão anterior sem '
                                                     'recompilar a imagem, reduzindo o tempo de mitigação a segundos.',
                                     'how_it_works_en': 'Helm manages application releases by storing versioned '
                                                        'manifests as Secrets or ConfigMaps. When a deployment fails, '
                                                        'the `helm rollback` command re-applies the previous revision '
                                                        'manifest without rebuilding images, cutting mitigation MTTR '
                                                        'down to seconds.',
                                     'resource_title': 'Gestão de Ciclo de Vida de Releases com Helm & Rollbacks',
                                     'resource_title_en': 'Release Lifecycle Management with Helm & Rollbacks'},
                       'description': 'A taxa de erros HTTP 500 subiu de 0.1% para 45% em menos de 2 minutos após um '
                                      'deploy de nova release. O SLO de disponibilidade está sendo violado gravemente.',
                       'description_en': 'HTTP 500 error rate spiked from 0.1% to 45% following a fresh release '
                                         'deployment. The availability SLO is critically violated.',
                       'detection_delay_seconds': 35,
                       'difficulty': 'easy',
                       'hints': [ { 'hint': 'Inspecione o histórico de revisões com `helm history sre-rag`.',
                                    'hint_en': 'Inspect release revision history with `helm history sre-rag`.'},
                                  { 'hint': 'Execute rollback para a revisão estável anterior.',
                                    'hint_en': 'Execute rollback to the previous stable release.'}],
                       'icon': '💥',
                       'id': 'high-error-rate',
                       'investigation_delay_seconds': 85,
                       'runbook': '/docs/runbooks/high-error-rate',
                       'runbook_steps': { 'diagnosis': [ 'helm history sre-rag (Revisão 2 implantada há 3 minutos com '
                                                         'status deployed).',
                                                         'kubectl logs -l app=sre-rag-api --tail=50 (Exceção não '
                                                         'tratada na rota /api/v1/query).',
                                                         'kubectl get pods -l app=sre-rag-api (Pods em Running mas '
                                                         'respondendo 500).'],
                                          'diagnosis_en': [ 'helm history sre-rag (Revision 2 deployed 3 minutes ago '
                                                            'with status deployed).',
                                                            'kubectl logs -l app=sre-rag-api --tail=50 (Unhandled '
                                                            'exception in /api/v1/query import).',
                                                            'kubectl get pods -l app=sre-rag-api (Pods in Running '
                                                            'state but serving HTTP 500).'],
                                          'mitigation': { 'action': 'Executar rollback imediato para a revisão estável '
                                                                    'anterior.',
                                                          'command': 'helm rollback sre-rag',
                                                          'validation': 'Monitorar queda da taxa de erro para < 0.1% e '
                                                                        'retorno dos status 200 OK.'},
                                          'mitigation_en': { 'action_en': 'Perform immediate rollback to the previous '
                                                                          'stable revision.',
                                                             'command': 'helm rollback sre-rag',
                                                             'validation_en': 'Monitor error rate dropping back to < '
                                                                              '0.1% and HTTP 200 responses returning.'},
                                          'prevention': [ 'Implementar Progressive Delivery com Argo Rollouts ou '
                                                          'Flagger (canary 10% -> 50% -> 100%).',
                                                          'Configurar rollback automático baseado em métricas '
                                                          'Prometheus no pipeline.'],
                                          'prevention_en': [ 'Implement Progressive Delivery using Argo Rollouts or '
                                                             'Flagger (canary 10% -> 50% -> 100%).',
                                                             'Configure automated rollback based on Prometheus metrics '
                                                             'in the pipeline.'],
                                          'root_cause': { 'analysis': 'A imagem da revisão 2 continha chamada a módulo '
                                                                      'inexistente no import da rota principal.',
                                                          'permanent_fix': 'Adicionar testes de fumaça (smoke tests) '
                                                                           'automatizados e canary deployment na '
                                                                           'pipeline de CI/CD.'},
                                          'root_cause_en': { 'analysis_en': 'Revision 2 container image contained an '
                                                                            'import call to a nonexistent module.',
                                                             'permanent_fix_en': 'Add automated smoke tests and canary '
                                                                                 'deployment verification to CI/CD '
                                                                                 'pipeline.'},
                                          'triage': [ 'Verificar alerta Alertmanager: SLOAvailabilityBurnRateCritical.',
                                                      "Inspecionar Golden Signal 'Errors': "
                                                      "sum(rate(http_requests_total{status_code=~'5..'}[5m])) / "
                                                      'sum(rate(http_requests_total[5m])) * 100.',
                                                      'Checar timeline de deploys no canal de release ou Kubernetes '
                                                      'events.'],
                                          'triage_en': [ 'Check Alertmanager alert: SLOAvailabilityBurnRateCritical.',
                                                         "Inspect Golden Signal 'Errors': "
                                                         "sum(rate(http_requests_total{status_code=~'5..'}[5m])) / "
                                                         'sum(rate(http_requests_total[5m])) * 100.',
                                                         'Inspect deployment timeline in release channel or Kubernetes '
                                                         'events.']},
                       'severity': 'SEV-1',
                       'solutions': [ { 'command': 'helm rollback sre-rag',
                                        'correct': True,
                                        'explanation': '✅ Correto! O deploy mais recente introduziu um bug crítico. O '
                                                       'rollback restaura a versão anterior estável imediatamente, '
                                                       'sendo a ação mais rápida para reduzir o MTTR.',
                                        'explanation_en': '✅ Correct! The latest deployment introduced a breaking bug. '
                                                          'Rollback immediately restores the previous stable release, '
                                                          'minimizing MTTR.',
                                        'id': 'rollback',
                                        'label': 'Executar rollback do Helm release (`helm rollback sre-rag`)',
                                        'label_en': 'Perform Helm release rollback (`helm rollback sre-rag`)'},
                                      { 'command': 'kubectl scale deployment sre-rag-api --replicas=10',
                                        'correct': False,
                                        'explanation': '❌ Incorreto. Mais réplicas não resolvem um bug de código — '
                                                       'cada novo pod também retornará HTTP 500, consumindo recursos e '
                                                       'gerando custo sem mitigar a falha.',
                                        'explanation_en': '❌ Incorrect. Scaling does not resolve application code bugs '
                                                          '— each new pod will continue throwing 500 errors.',
                                        'id': 'scale-hpa',
                                        'label': 'Escalar o HPA para mais réplicas (aumentar maxReplicas)',
                                        'label_en': 'Scale HPA to more replicas (increase maxReplicas)'},
                                      { 'command': 'kubectl rollout restart deployment/coredns -n kube-system',
                                        'correct': False,
                                        'explanation': '❌ Incorreto. O DNS está saudável. Os erros 500 são gerados '
                                                       'pela aplicação na camada HTTP, não por falha de resolução de '
                                                       'nomes.',
                                        'explanation_en': '❌ Incorrect. DNS resolution is healthy; errors originate '
                                                          'inside application code.',
                                        'id': 'restart-coredns',
                                        'label': 'Reiniciar os pods do CoreDNS no cluster',
                                        'label_en': 'Restart CoreDNS pods in the cluster'}],
                       'symptoms': [ 'Burn rate > 14.4x na janela de 1 hora',
                                     'Alertmanager: SLOAvailabilityBurnRateCritical FIRING',
                                     'Grafana: SLO gauge em vermelho (< 99.9%)',
                                     'HTTP 500 em todos os endpoints principais da API'],
                       'symptoms_en': [ 'Burn rate > 14.4x in the 1-hour window',
                                        'Alertmanager: SLOAvailabilityBurnRateCritical FIRING',
                                        'Grafana: SLO gauge in red (< 99.9%)',
                                        'HTTP 500 across all core API endpoints'],
                       'title': 'High Error Rate (HTTP 500 Spike)',
                       'title_en': 'High Error Rate (HTTP 500 Spike)'},
  'high-latency': { 'category': 'Latência',
                    'category_en': 'Latency',
                    'chaos_action': None,
                    'command': 'kubectl scale hpa sre-rag-api --min=5 --max=20',
                    'concepts': { 'architecture_components': [ 'Metrics Server',
                                                               'Kube-HPA-Controller',
                                                               'SLO Latency Percentiles'],
                                  'best_practices': [ 'Nunca monitore apenas a média de latência; os percentis P95 e '
                                                      'P99 revelam a experiência real dos clientes com piores tempos.',
                                                      'Mantenha réplicas suficientes prontas para evitar o atraso de '
                                                      'aquecimento do pod (cold start).',
                                                      'Configure readiness probes para impedir tráfego a pods '
                                                      'recém-criados antes de estarem 100% prontos.'],
                                  'best_practices_en': [ 'Never monitor average latency alone; P99 and P95 latency '
                                                         'reveal actual customer impact.',
                                                         'Maintain sufficient baseline replicas to absorb initial '
                                                         'spike while HPA spins up new pods.',
                                                         'Configure aggressive scale-up policy and conservative '
                                                         'scale-down stabilization window (300s).'],
                                  'category_en': 'Latency',
                                  'golden_signals': [ 'Latência P99 (Latency P99 ms)',
                                                      'Tráfego Concorrente (Requests/sec)'],
                                  'golden_signals_en': ['HTTP Request Latency P99 (ms)', 'CPU Utilization vs Target %'],
                                  'how_it_works': 'O HPA consulta periodicamente a Metrics API (Metrics Server) '
                                                  'calculando: `desiredReplicas = ceil[currentReplicas * '
                                                  '(currentMetricValue / targetMetricValue)]`. Ao detectar CPU > 80%, '
                                                  'o HPA dispara scale-up no Deployment. Escalar horizontalmente '
                                                  'divide as conexões concorrentes, diminuindo o tempo de fila e a '
                                                  'latência P99.',
                                  'how_it_works_en': 'HPA queries Metrics Server periodically (every 15s) and '
                                                     'calculates `desiredReplicas = ceil[currentReplicas * '
                                                     '(currentMetric / targetMetric)]`. When API traffic spikes, CPU '
                                                     'saturation leads to queuing. HPA triggers scale-out, '
                                                     'distributing concurrency and lowering latency.',
                                  'resource_title': 'Horizontal Pod Autoscaler (HPA v2) & Saturação de CPU',
                                  'resource_title_en': 'Horizontal Pod Autoscaler (HPA v2) & CPU Saturation'},
                    'description': 'A latência P99 das requisições subiu para 4.2 segundos. O SLO de latência (99.5% < '
                                   '500ms) está sendo violado. Usuários relatam lentidão extrema.',
                    'description_en': 'P99 request latency degraded to 4.2 seconds, violating the latency SLO target '
                                      '(99.5% < 500ms).',
                    'detection_delay_seconds': 45,
                    'difficulty': 'medium',
                    'hints': [ { 'hint': 'Inspecione o número atual de réplicas e a CPU dos pods.',
                                 'hint_en': 'Inspect current replica count and pod CPU utilization.'},
                               { 'hint': 'Escale o deployment para 5 réplicas com kubectl scale.',
                                 'hint_en': 'Scale the deployment to 5 replicas using kubectl scale.'}],
                    'icon': '🐢',
                    'id': 'high-latency',
                    'investigation_delay_seconds': 90,
                    'runbook': '/docs/runbooks/high-latency',
                    'runbook_steps': { 'diagnosis': [ 'kubectl top pods -l app=sre-rag-api (Pods operando no teto de '
                                                      'CPU).',
                                                      "kubectl logs -l app=sre-rag-api | grep 'slow_query' (Consultas "
                                                      'SQL no postgres com tempo > 2000ms).',
                                                      'pg_stat_activity no banco identificando sequential scans na '
                                                      'tabela de documentos.'],
                                       'diagnosis_en': [ 'kubectl get hpa (Replicas at max ceiling or HPA missing).',
                                                         'kubectl top pods (Pods running at 95% CPU, causing request '
                                                         'queuing).',
                                                         'kubectl get pods (Only 1 replica handling all incoming '
                                                         'traffic).'],
                                       'mitigation': { 'action': 'Aumentar réplicas mínimas do HPA para distribuir a '
                                                                 'concorrência de CPU.',
                                                       'command': 'kubectl scale hpa sre-rag-api --min=5 --max=20',
                                                       'validation': 'Monitorar queda do P99 para < 450ms no Grafana.'},
                                       'mitigation_en': { 'action_en': 'Scale deployment manually to 5 replicas to '
                                                                       'alleviate queue pressure immediately.',
                                                          'command': 'kubectl scale deployment sre-rag-api '
                                                                     '--replicas=5',
                                                          'validation_en': 'P99 latency drops below 200ms within 30 '
                                                                           'seconds.'},
                                       'prevention': [ 'Definir alertas de slow queries no PostgreSQL '
                                                       '(log_min_duration_statement = 500ms).',
                                                       'Ajustar métrica de HPA baseada em requests por segundo (RPS) '
                                                       'além de CPU.'],
                                       'prevention_en': [ 'Configure HPA v2 with custom metrics (requests per second) '
                                                          'in addition to CPU.',
                                                          'Implement synthetic canary probe alerting on P99 '
                                                          'degradation.'],
                                       'root_cause': { 'analysis': 'Aumento de 300% de usuários simultâneos executando '
                                                                   'busca semântica sem índice ivfflat/hnsw no '
                                                                   'pgvector.',
                                                       'permanent_fix': 'Criar índice HNSW vetorial no PostgreSQL e '
                                                                        'configurar cache de embeddings no Redis.'},
                                       'root_cause_en': { 'analysis_en': 'Traffic volume increased 400% during '
                                                                         'marketing campaign without HPA enabled.',
                                                          'permanent_fix_en': 'Deploy HPA v2 manifest targeting 65% '
                                                                              'CPU utilization with minReplicas: 3, '
                                                                              'maxReplicas: 10.'},
                                       'triage': [ 'Alerta SLOLatencyBurnRateCritical disparado.',
                                                   'Grafana: P99 ultrapassa 4000ms na rota /api/v1/query.',
                                                   'CPU dos pods da API em 95% de saturação constante.'],
                                       'triage_en': [ 'Check alert: HighLatencyP99 (P99 > 2.0s).',
                                                      "Inspect Golden Signal 'Latency': histogram_quantile(0.99, "
                                                      'sum(rate(http_request_duration_seconds_bucket[5m])) by (le)).',
                                                      'Inspect API Pod CPU utilization.']},
                    'severity': 'SEV-2',
                    'solutions': [ { 'command': 'kubectl scale hpa sre-rag-api --min=5 --max=20',
                                     'correct': True,
                                     'explanation': '✅ Correto! Escalar alivia a pressão de CPU imediatamente '
                                                    '(mitigação rápida) enquanto a análise de slow queries investiga a '
                                                    'causa raiz.',
                                     'explanation_en': '✅ Correct! Scaling relieves CPU saturation immediately while '
                                                       'query analysis targets root cause.',
                                     'id': 'scale-hpa',
                                     'label': 'Escalar HPA + investigar e otimizar queries lentas no PostgreSQL',
                                     'label_en': 'Scale HPA + investigate and optimize slow queries in PostgreSQL'},
                                   { 'command': 'helm rollback sre-rag',
                                     'correct': False,
                                     'explanation': '❌ Incorreto. A latência é provocada por volume repentino de '
                                                    'tráfego somado a queries sem índice, não por alteração de código '
                                                    'recente.',
                                     'explanation_en': '❌ Incorrect. Latency is caused by traffic volume and query '
                                                       'saturation, not recent code changes.',
                                     'id': 'rollback',
                                     'label': 'Fazer rollback do último deploy',
                                     'label_en': 'Rollback the last deployment'},
                                   { 'command': 'kubectl rollout restart deployment/sre-rag-api',
                                     'correct': False,
                                     'explanation': '❌ Ineficaz. Reiniciar derruba conexões ativas e esvazia caches '
                                                    'quentes, gerando pico de latência ainda maior ao subir.',
                                     'explanation_en': '❌ Ineffective. Restarting drops active sessions and leaves '
                                                       'cold caches, compounding latency.',
                                     'id': 'restart-pods',
                                     'label': 'Reiniciar todos os pods da API',
                                     'label_en': 'Restart all API pods'}],
                    'symptoms': [ 'P99 latency: 4200ms (SLO target: 500ms)',
                                  'CPU da API em 95% de utilização',
                                  'PostgreSQL: slow queries > 2s detectadas',
                                  'Redis cache hit rate caiu para 12%'],
                    'symptoms_en': [ 'P99 latency: 4200ms (SLO target: 500ms)',
                                     'API Pod CPU utilization at 95%',
                                     'PostgreSQL: slow queries > 2s detected',
                                     'Redis cache hit rate dropped to 12%'],
                    'title': 'High Latency (P99 > 2s)',
                    'title_en': 'High Latency (P99 > 2s)'},
  'hpa-flapping': { 'category': 'Escalabilidade',
                    'category_en': 'Scalability',
                    'chaos_action': None,
                    'command': 'kubectl patch hpa sre-rag-api --patch '
                               '\'{"spec":{"behavior":{"scaleDown":{"stabilizationWindowSeconds":300}}}}\'',
                    'concepts': { 'architecture_components': [ 'HPA Controller',
                                                               'ScaleDown Damping',
                                                               'preStop Hooks & Graceful Shutdown'],
                                  'best_practices': [ 'Configure `stabilizationWindowSeconds: 300` (5 minutos) para '
                                                      'scaleDown em sistemas com tráfego oscilante.',
                                                      'Sempre combine HPA com `terminationGracePeriodSeconds` e '
                                                      '`preStop: sleep 10` para dar tempo aos Ingress controllers de '
                                                      'desregistrar o pod.',
                                                      'Adote Pod Disruption Budgets (PDB) para garantir réplicas '
                                                      'mínimas disponíveis durante manutenções.'],
                                  'best_practices_en': [ 'Configure stabilizationWindowSeconds: 300 for scaleDown to '
                                                         'avoid premature pod terminations.',
                                                         'Scale up fast (percentage: 100% per 15s), scale down slow '
                                                         '(max pods: 1 per 60s).',
                                                         'Ensure readiness probes ensure traffic only hits warmed-up '
                                                         'pods to avoid false spikes.'],
                                  'category_en': 'Scalability',
                                  'golden_signals': [ 'Taxa de Criação/Morte de Pods (Pod Churn Rate)',
                                                      'Variação de Réplicas (HPA Replicas Variance)'],
                                  'golden_signals_en': [ 'HPA Scaling Events Frequency',
                                                         'Deployment Replicas Oscillation'],
                                  'how_it_works': 'O autoscaler recalcula réplicas a cada '
                                                  '`horizontal-pod-autoscaler-sync-period` (padrão 15s). Sem uma '
                                                  'janela de estabilização (`stabilizationWindowSeconds`), um alívio '
                                                  'momentâneo de CPU dispara o corte imediato de pods. Ao desligar '
                                                  'réplicas, a carga remanescente satura os pods sobreviventes, '
                                                  'disparando novo scale-up. A janela de estabilização calcula o valor '
                                                  'máximo de réplicas recomendadas no período antes de executar o '
                                                  'scale-down.',
                                  'how_it_works_en': 'HPA flapping (thrashing) occurs when pods scale up quickly, '
                                                     'diluting metric per pod and causing scale-down, which triggers '
                                                     'overload and scale-up again. HPA v2 solves this with '
                                                     '`behavior.scaleDown.stabilizationWindowSeconds` (evaluates '
                                                     'maximum metric over 300s window) and rate limits.',
                                  'resource_title': 'HPA v2 Behavior: Stabilization Windows & Rate Limiting de Escala',
                                  'resource_title_en': 'HPA v2 Behavior: Stabilization Windows & Scale Rate Limiting'},
                    'description': 'O Horizontal Pod Autoscaler está oscilando descontroladamente entre 2 e 15 pods a '
                                   'cada 3 minutos. Cada redução de escala sobrecarrega os pods remanescentes e força '
                                   'novo scale-up, gerando instabilidade.',
                    'description_en': 'HPA is oscillating aggressively between 2 and 15 replicas every 3 minutes due '
                                      'to missing scaleDown stabilization window.',
                    'detection_delay_seconds': 30,
                    'difficulty': 'medium',
                    'hints': [ { 'hint': 'Inspecione os eventos do HPA com kubectl describe hpa.',
                                 'hint_en': 'Inspect HPA events using kubectl describe hpa.'},
                               { 'hint': 'Configure stabilizationWindowSeconds: 300 no scaleDown via kubectl patch '
                                         'hpa.',
                                 'hint_en': 'Set stabilizationWindowSeconds: 300 under scaleDown via kubectl patch '
                                            'hpa.'}],
                    'icon': '📈',
                    'id': 'hpa-flapping',
                    'investigation_delay_seconds': 75,
                    'runbook': '/docs/runbooks/hpa-flapping',
                    'runbook_steps': { 'diagnosis': [ 'kubectl describe hpa sre-rag-api (Scaling events a cada 90 '
                                                      'segundos).',
                                                      "kubectl get events --sort-by='.lastTimestamp' | grep -i "
                                                      'scaledown.',
                                                      'Falta do bloco `behavior.scaleDown.stabilizationWindowSeconds` '
                                                      'no manifesto.'],
                                       'diagnosis_en': [ 'kubectl describe hpa (Events show continuous '
                                                         'SuccessfulRescale back and forth).',
                                                         'kubectl get hpa -o yaml (behavior block missing '
                                                         'stabilizationWindowSeconds).',
                                                         'Check scaleDown policy: terminating pods immediately upon '
                                                         'metric dip.'],
                                       'mitigation': { 'action': 'Aplicar patch configurando janela de estabilização '
                                                                 'de 5 minutos.',
                                                       'command': 'kubectl patch hpa sre-rag-api --patch '
                                                                  '\'{"spec":{"behavior":{"scaleDown":{"stabilizationWindowSeconds":300}}}}\'',
                                                       'validation': 'Monitorar estabilidade de réplicas ao longo de '
                                                                     '15 minutos sem oscilação abrupta.'},
                                       'mitigation_en': { 'action_en': 'Patch HPA behavior configuring a 300s '
                                                                       'scaleDown stabilization window.',
                                                          'command': 'kubectl patch hpa sre-rag-api --patch '
                                                                     '\'{"spec":{"behavior":{"scaleDown":{"stabilizationWindowSeconds":300}}}}\'',
                                                          'validation_en': 'Replicas stabilize at 4 pods and rescale '
                                                                           'flapping stops.'},
                                       'prevention': [ 'Combinar métricas de CPU com métricas de negócio (RPS ou '
                                                       'contagem de conexões).',
                                                       'Implementar terminationGracePeriodSeconds adequado e preStop '
                                                       'hooks para drenar conexões antes do encerramento.'],
                                       'prevention_en': [ 'Define conservative scaleDown policies across all '
                                                          'production HPAs.',
                                                          'Conduct game days simulating bursty traffic profiles.'],
                                       'root_cause': { 'analysis': 'Configuração padrão do HPA sem damping em '
                                                                   'workloads com bursts rápidos de consultas '
                                                                   'vetoriais.',
                                                       'permanent_fix': 'Definir políticas de escala completas no Helm '
                                                                        'chart com taxas máximas de scaleDown.'},
                                       'root_cause_en': { 'analysis_en': 'Default HPA v1 behavior lacked damping '
                                                                         'window for spiky batch workloads.',
                                                          'permanent_fix_en': 'Commit HPA v2 manifest with explicit '
                                                                              'scaleUp and scaleDown behavior '
                                                                              'policies.'},
                                       'triage': [ 'Alerta HPAFlappingWarning e HighPodChurnRate.',
                                                   'Gráfico do Grafana mostrando padrão dente-de-serra no número de '
                                                   'réplicas.',
                                                   'Picos de latência coincidentes com eventos de terminação de pods.'],
                                       'triage_en': [ 'Check alert: HPAFlappingDetected.',
                                                      'Inspect deployment replica count oscillating between 2 and 10 '
                                                      'every 2 minutes.',
                                                      'Verify customer latency instability during scale-down cycles.']},
                    'severity': 'SEV-2',
                    'solutions': [ { 'command': 'kubectl patch hpa sre-rag-api --patch '
                                                '\'{"spec":{"behavior":{"scaleDown":{"stabilizationWindowSeconds":300}}}}\'',
                                     'correct': True,
                                     'explanation': '✅ Correto! A janela de estabilização impede que o HPA reduza '
                                                    'réplicas precipitadamente, suavizando os ciclos e eliminando o '
                                                    'flapping.',
                                     'explanation_en': '✅ Correct! The stabilization window suppresses rapid '
                                                       'scale-down decisions, stabilizing cluster state.',
                                     'id': 'add-stabilization-window',
                                     'label': 'Adicionar stabilizationWindowSeconds de 300s no scaleDown do HPA',
                                     'label_en': 'Add stabilizationWindowSeconds (300s) to HPA scaleDown behavior'},
                                   { 'command': 'kubectl delete hpa sre-rag-api',
                                     'correct': False,
                                     'explanation': '❌ Incorreto. Deletar o HPA deixa a aplicação vulnerável a picos '
                                                    'de tráfego que causarão indisponibilidade completa.',
                                     'explanation_en': '❌ Incorrect. Deleting autoscaling leaves the service '
                                                       'unprotected against traffic spikes.',
                                     'id': 'delete-hpa',
                                     'label': 'Deletar o HPA e deixar réplicas fixas em 2',
                                     'label_en': 'Delete HPA and freeze fixed replicas at 2'},
                                   { 'command': 'kubectl autoscale deployment sre-rag-api --cpu-percent=99',
                                     'correct': False,
                                     'explanation': '❌ Perigoso. Target de 99% fará os pods operarem no limiar de '
                                                    'estrangulamento antes de escalar, gerando alta latência.',
                                     'explanation_en': '❌ Dangerous. 99% CPU target delays scaling until pods are '
                                                       'already throttled.',
                                     'id': 'increase-target',
                                     'label': 'Mudar target de CPU para 99%',
                                     'label_en': 'Change CPU target to 99%'}],
                    'symptoms': [ 'HPA réplicas pulando de 2 -> 15 -> 2 -> 15 ciclicamente',
                                  'Latência intermitente com picos de 3000ms a cada scale-down',
                                  'Conexões TCP sendo encerradas abruptamente durante desativação de pods',
                                  'Alerta HPAFlappingWarning disparado'],
                    'symptoms_en': [ 'HPA replicas flapping cyclically from 2 -> 15 -> 2 -> 15',
                                     'Intermittent latency spikes up to 3000ms at every scale-down cycle',
                                     'Abrupt TCP drops during rapid pod terminations',
                                     'Alert HPAFlappingWarning FIRING'],
                    'title': 'HPA Flapping / Thrashing Contínuo',
                    'title_en': 'HPA Thrashing & Flapping Loop'},
  'ingress-503-endpoints': { 'category': 'Rede',
                             'category_en': 'Network',
                             'chaos_action': None,
                             'command': 'kubectl set selector service sre-rag-api app.kubernetes.io/name=sre-rag-api',
                             'concepts': { 'architecture_components': [ 'K8s Endpoints Controller',
                                                                        'CoreDNS',
                                                                        'NGINX Ingress Upstream'],
                                           'best_practices': [ 'Sempre padronize labels conforme os Kubernetes '
                                                               'Recommended Labels (`app.kubernetes.io/name`, '
                                                               '`app.kubernetes.io/instance`).',
                                                               'Monitore a métrica `kube_endpoint_address_available` '
                                                               'para detectar serviços vazios antes dos usuários.',
                                                               'Centralize a geração de labels em templates '
                                                               'compartilhados (`_helpers.tpl`).'],
                                           'best_practices_en': [ 'Always check `kubectl get endpoints <svc>` when '
                                                                  'facing 502/503 from Ingress.',
                                                                  'Standardize labels across manifests using Helm '
                                                                  'templates (`app.kubernetes.io/name`).',
                                                                  'Set up validation webhooks (Kyverno/OPA) to prevent '
                                                                  'selector mismatches in CI/CD.'],
                                           'category_en': 'Network',
                                           'golden_signals': [ 'Endpoints Saudáveis (Available Endpoints Count)',
                                                               'Taxa de HTTP 503 no Ingress (Ingress 503 Upstream '
                                                               'Failure Rate)'],
                                           'golden_signals_en': [ 'Ingress 503 Status Rate',
                                                                  'Service Active Endpoints Count'],
                                           'how_it_works': 'No Kubernetes, um `Service` atua como uma abstração lógica '
                                                           'para um grupo de Pods. O `EndpointSlice Controller` '
                                                           'monitora o cluster e, via reconciliação contínua, associa '
                                                           'os IPs dos pods saudáveis ao Service através do '
                                                           '`spec.selector`. O Ingress Controller sincroniza '
                                                           'dinamicamente sua lista de upstreams com esses endpoints. '
                                                           'Se o selector não casar com os labels dos pods, a lista '
                                                           'fica vazia e o Ingress responde com 503.',
                                           'how_it_works_en': 'Kubernetes Service uses label selectors to match pods '
                                                              'and populate Endpoints/EndpointSlices. Ingress '
                                                              'Controller (NGINX) watches Endpoints directly. If the '
                                                              'Service selector has a typo (e.g., `app=sre-rag` '
                                                              'instead of `app=sre-rag-api`), Endpoints list is empty, '
                                                              'and Ingress returns 503 Service Unavailable '
                                                              'immediately.',
                                           'resource_title': 'Kubernetes Service Discovery, Endpoints & Ingress '
                                                             'Controller',
                                           'resource_title_en': 'Kubernetes Service Discovery, Endpoints & Ingress '
                                                                'Controller'},
                             'description': 'O Ingress retorna HTTP 503 Service Unavailable para 100% dos usuários. O '
                                            'Service `sre-rag-api` está com `Endpoints: <none>` porque os labels dos '
                                            'pods foram alterados sem atualizar o selector do Service.',
                             'description_en': 'Ingress returns HTTP 503 to all users. The Service `sre-rag-api` has '
                                               'zero endpoints due to label selector mismatch.',
                             'detection_delay_seconds': 25,
                             'difficulty': 'medium',
                             'hints': [ { 'hint': 'Verifique os endpoints do serviço com kubectl get endpoints.',
                                          'hint_en': 'Check service endpoints using kubectl get endpoints.'},
                                        { 'hint': 'Corrija o seletor do serviço com kubectl patch service.',
                                          'hint_en': 'Fix service selector using kubectl patch service.'}],
                             'icon': '🔌',
                             'id': 'ingress-503-endpoints',
                             'investigation_delay_seconds': 65,
                             'runbook': '/docs/runbooks/ingress-503-endpoints',
                             'runbook_steps': { 'diagnosis': [ 'kubectl get endpoints sre-rag-api (ENDPOINTS: <none>).',
                                                               'kubectl get svc sre-rag-api -o '
                                                               "jsonpath='{.spec.selector}' (app=sre-rag-api).",
                                                               'kubectl get pods --show-labels (Labels nos pods: '
                                                               'app.kubernetes.io/name=sre-rag-api).'],
                                                'diagnosis_en': [ 'kubectl get endpoints sre-rag-api (ENDPOINTS column '
                                                                  'shows <none>).',
                                                                  'kubectl get service sre-rag-api -o yaml (Selector '
                                                                  'shows app: sre-rag-backend).',
                                                                  'kubectl get pods --show-labels (Pods labeled with '
                                                                  'app=sre-rag-api).'],
                                                'mitigation': { 'action': 'Atualizar o selector do serviço para '
                                                                          'coincidir com o label dos pods.',
                                                                'command': 'kubectl set selector service sre-rag-api '
                                                                           'app.kubernetes.io/name=sre-rag-api',
                                                                'validation': 'kubectl get endpoints sre-rag-api (IPs '
                                                                              'dos pods aparecem listados).'},
                                                'mitigation_en': { 'action_en': 'Patch Service selector to match '
                                                                                'active pod labels (app: sre-rag-api).',
                                                                   'command': 'kubectl patch service sre-rag-api -p '
                                                                              '\'{"spec":{"selector":{"app":"sre-rag-api"}}}\'',
                                                                   'validation_en': 'Endpoints populate with pod IPs '
                                                                                    'immediately and Ingress returns '
                                                                                    '200 OK.'},
                                                'prevention': [ 'Usar _helpers.tpl do Helm para manter labels e '
                                                                'selectors compartilhados de forma padronizada.',
                                                                'Testes end-to-end de fumaça na pipeline validando '
                                                                'tráfego real via Ingress.'],
                                                'prevention_en': [ 'Run kube-score or pluto in CI pipeline to detect '
                                                                   'orphaned service selectors.',
                                                                   'Add automated integration tests verifying endpoint '
                                                                   'registration on deploy.'],
                                                'root_cause': { 'analysis': 'Refatoração no Helm chart alterou '
                                                                            'templates de Pod para o padrão Kubernetes '
                                                                            'recomendado sem atualizar o Service '
                                                                            'correspondente.',
                                                                'permanent_fix': 'Adicionar teste automatizado de '
                                                                                 'conformance de labels no linter do '
                                                                                 'Helm.'},
                                                'root_cause_en': { 'analysis_en': 'Helm values override in '
                                                                                  'values-prod.yaml changed selector '
                                                                                  'without updating deployment labels.',
                                                                   'permanent_fix_en': 'Unify label definitions using '
                                                                                       'standard Helm helper '
                                                                                       '_helpers.tpl.'},
                                                'triage': [ 'Alerta IngressHighHttp5xxRate e IngressEmptyEndpoints.',
                                                            'Usuários recebendo 503 Service Temporarily Unavailable.',
                                                            'Pods da aplicação exibem status Running 1/1.'],
                                                'triage_en': [ 'Check alert: IngressHigh503Rate.',
                                                               'Inspect Ingress logs: upstream backend returned 503 '
                                                               'Service Unavailable.',
                                                               'Verify service accessibility: curl returns 503.']},
                             'severity': 'SEV-1',
                             'solutions': [ { 'command': 'kubectl set selector service sre-rag-api '
                                                         'app.kubernetes.io/name=sre-rag-api',
                                              'correct': True,
                                              'explanation': '✅ Correto! O Service utiliza label selectors para '
                                                             'encontrar os pods. Alinhar o selector aos labels dos '
                                                             'pods restaura os endpoints imediatamente.',
                                              'explanation_en': '✅ Correct! Aligning label selectors allows the '
                                                                'Kubernetes controller to bind healthy pod IPs to '
                                                                'Service endpoints.',
                                              'id': 'fix-selector',
                                              'label': 'Corrigir selector do Service para '
                                                       '`app.kubernetes.io/name=sre-rag-api`',
                                              'label_en': 'Fix Service selector to match '
                                                          '`app.kubernetes.io/name=sre-rag-api`'},
                                            { 'command': 'kubectl rollout restart deployment/ingress-nginx-controller '
                                                         '-n ingress-nginx',
                                              'correct': False,
                                              'explanation': '❌ Ineficaz. O Ingress está funcionando; o erro 503 '
                                                             'ocorre porque o Service para o qual ele encaminha não '
                                                             'possui nenhum pod vinculado.',
                                              'explanation_en': '❌ Ineffective. The Ingress is healthy; it returns 503 '
                                                                'because the target Service has no endpoints.',
                                              'id': 'restart-ingress',
                                              'label': 'Reiniciar os pods do NGINX Ingress Controller',
                                              'label_en': 'Restart NGINX Ingress Controller pods'},
                                            { 'command': 'kubectl reboot nodes --all',
                                              'correct': False,
                                              'explanation': '❌ Absurdo e destrutivo. O problema é puramente um erro '
                                                             'lógico de configuração de label no Service.',
                                              'explanation_en': '❌ Destructive. The issue is a simple logical selector '
                                                                'mismatch.',
                                              'id': 'reboot-nodes',
                                              'label': 'Reiniciar os nós do cluster Kubernetes',
                                              'label_en': 'Reboot all Kubernetes nodes'}],
                             'symptoms': [ 'HTTP 503 Service Unavailable em todos os domínios externos',
                                           'kubectl get endpoints sre-rag-api: <none>',
                                           "Pods da API estão em 'Running (1/1)' e perfeitamente saudáveis",
                                           'Alertmanager: IngressEmptyEndpoints FIRING'],
                             'symptoms_en': [ 'HTTP 503 Service Unavailable on all public domains',
                                              'kubectl get endpoints sre-rag-api: <none>',
                                              'API pods are Running (1/1) and healthy internally',
                                              'Alertmanager: IngressEmptyEndpoints FIRING'],
                             'title': '503 Service Unavailable (Service Selector Mismatch)',
                             'title_en': '503 Service Unavailable (Service Selector Mismatch)'},
  'missing-config-secret': { 'category': 'Confiabilidade',
                             'category_en': 'Reliability',
                             'chaos_action': None,
                             'command': 'kubectl create secret generic sre-rag-secrets '
                                        '--from-literal=OPENAI_API_KEY=mock-key '
                                        '--from-literal=DATABASE_URL=postgres://app:secret@postgresql:5432/sre_db',
                             'concepts': { 'architecture_components': [ 'Kubernetes Secrets',
                                                                        'envFrom / SecretKeyRef',
                                                                        'External Secrets Operator'],
                                           'best_practices': [ 'Nunca commite segredos em texto puro em repositórios '
                                                               'Git.',
                                                               'Use External Secrets Operator ou HashiCorp Vault Agent '
                                                               'Injector para sincronizar secrets automaticamente.',
                                                               'Configure liveness e startup probes de forma '
                                                               'resiliente, permitindo fallbacks gracioso quando '
                                                               'dependências externas falharem temporariamente.'],
                                           'best_practices_en': [ 'Never commit plain-text secrets to Git '
                                                                  'repositories.',
                                                                  'Use External Secrets Operator or HashiCorp Vault '
                                                                  'Agent Injector to synchronize secrets '
                                                                  'automatically.',
                                                                  'Validate secret existence in pre-flight CI/CD '
                                                                  'deployment checks.'],
                                           'category_en': 'Reliability',
                                           'golden_signals': [ 'Contagem de Pods Prontos (Ready Pods Ratio)',
                                                               'Taxa de Falhas de Inicialização (Container Startup '
                                                               'Failures)'],
                                           'golden_signals_en': ['Container Restart Rate', 'KubePodNotReady Duration'],
                                           'how_it_works': 'O Kubelet monta Secrets e ConfigMaps como variáveis de '
                                                           'ambiente ou volumes tmpfs antes de executar o container. '
                                                           'Se uma chave mapeada via `envFrom` ou `secretKeyRef` com '
                                                           '`optional: false` não existir, o Kubelet não consegue '
                                                           'iniciar o container ou a aplicação quebra em runtime ao '
                                                           'acessar o dicionário de ambiente.',
                                           'how_it_works_en': 'Kubelet mounts Secrets and ConfigMaps as environment '
                                                              'variables or tmpfs volumes before launching the '
                                                              'container. If a key mapped via `envFrom` or '
                                                              '`secretKeyRef` (with `optional: false`) does not exist, '
                                                              'Kubernetes cannot start the container, causing '
                                                              'immediate crash on access.',
                                           'resource_title': 'Kubernetes Secrets Management & Injeção de Variáveis',
                                           'resource_title_en': 'Kubernetes Secrets Management & Variable Injection'},
                             'description': "Os pods recém-criados falham imediatamente no bootstrap com 'KeyError: "
                                            "OPENAI_API_KEY'. O Secret 'sre-rag-secrets' não foi provisionado no "
                                            'namespace após o deploy do Helm.',
                             'description_en': "New pods crash instantly during bootstrap with 'KeyError: "
                                               "OPENAI_API_KEY'. Required Secret 'sre-rag-secrets' was not found in "
                                               'the target namespace.',
                             'detection_delay_seconds': 20,
                             'difficulty': 'easy',
                             'hints': [ { 'hint': 'Inspecione os eventos do Pod com kubectl describe pod.',
                                          'hint_en': 'Inspect Pod events with kubectl describe pod.'},
                                        { 'hint': 'Crie o Secret genérico ausente chamado api-secret.',
                                          'hint_en': 'Create the missing generic Secret named api-secret.'}],
                             'icon': '🔑',
                             'id': 'missing-config-secret',
                             'investigation_delay_seconds': 55,
                             'runbook': '/docs/runbooks/missing-config-secret',
                             'runbook_steps': { 'diagnosis': [ 'kubectl get pods -l app=sre-rag-api '
                                                               '(CrashLoopBackOff).',
                                                               'kubectl logs -l app=sre-rag-api (KeyError: '
                                                               "'OPENAI_API_KEY' / 'DATABASE_URL').",
                                                               'kubectl get secrets (Confirmar ausência do secret '
                                                               "'sre-rag-secrets')."],
                                                'diagnosis_en': [ 'kubectl get pods (Pods failing to initialize).',
                                                                  "kubectl describe pod (Error: secret 'api-secret' "
                                                                  'not found).',
                                                                  'kubectl get secrets (Confirm secret is missing in '
                                                                  'namespace).'],
                                                'mitigation': { 'action': 'Criar o secret genérico com as chaves '
                                                                          'esperadas.',
                                                                'command': 'kubectl create secret generic '
                                                                           'sre-rag-secrets '
                                                                           '--from-literal=OPENAI_API_KEY=mock-key '
                                                                           '--from-literal=DATABASE_URL=postgres://app:secret@postgresql:5432/sre_db',
                                                                'validation': 'kubectl rollout status '
                                                                              'deployment/sre-rag-api'},
                                                'mitigation_en': { 'action_en': 'Create missing Secret with required '
                                                                                'dummy/staging credentials.',
                                                                   'command': 'kubectl create secret generic '
                                                                              'api-secret '
                                                                              '--from-literal=API_KEY=prod-sec-token-xyz',
                                                                   'validation_en': 'Pods transition immediately from '
                                                                                    'CreateContainerConfigError to '
                                                                                    'Running.'},
                                                'prevention': [ 'Adicionar validação de schema JSON no Helm '
                                                                '(values.schema.json).',
                                                                'Configurar pre-install hooks de validação de '
                                                                'dependências no Helm.'],
                                                'prevention_en': [ 'Enforce pre-deployment GitOps validation hook '
                                                                   'verifying all referenced secrets.',
                                                                   'Use optional: true for non-mandatory configuration '
                                                                   'values.'],
                                                'root_cause': { 'analysis': 'O pipeline de CI/CD aplicou o Helm '
                                                                            'release em um namespace novo sem disparar '
                                                                            'o job de sincronização do '
                                                                            'Vault/ExternalSecrets.',
                                                                'permanent_fix': 'Integrar o External Secrets Operator '
                                                                                 '(ESO) para reconciliação automática '
                                                                                 'de segredos.'},
                                                'root_cause_en': { 'analysis_en': 'Deploy pipeline executed helm '
                                                                                  'upgrade without running secret '
                                                                                  'provisioning job first.',
                                                                   'permanent_fix_en': 'Add SealedSecrets or '
                                                                                       'ExternalSecrets operator '
                                                                                       'manifest to GitOps '
                                                                                       'repository.'},
                                                'triage': [ 'Alerta KubeContainerWaiting / PodCrashLoopBackOff no '
                                                            'Alertmanager.',
                                                            'Deployment com 0 de 2 réplicas prontas.',
                                                            'Endpoint da API indisponível (HTTP 502 Bad Gateway no '
                                                            'Ingress).'],
                                                'triage_en': [ 'Check alert: KubeContainerWaiting '
                                                               '(CreateContainerConfigError).',
                                                               'Inspect pod state: Waiting with reason '
                                                               'CreateContainerConfigError.',
                                                               'Verify missing key notification in deployment '
                                                               'events.']},
                             'severity': 'SEV-2',
                             'solutions': [ { 'command': 'kubectl create secret generic sre-rag-secrets '
                                                         '--from-literal=OPENAI_API_KEY=mock-key '
                                                         '--from-literal=DATABASE_URL=postgres://app:secret@postgresql:5432/sre_db',
                                              'correct': True,
                                              'explanation': '✅ Correto! Provisionar o Secret com as chaves '
                                                             'obrigatórias satisfaz a inicialização do container, '
                                                             'permitindo que a aplicação suba com sucesso.',
                                              'explanation_en': '✅ Correct! Injecting the missing secret allows '
                                                                'application bootstrap validation to succeed.',
                                              'id': 'create-secret',
                                              'label': 'Criar o secret `sre-rag-secrets` com as credenciais '
                                                       'necessárias',
                                              'label_en': 'Create secret `sre-rag-secrets` with mandatory application '
                                                          'credentials'},
                                            { 'command': 'kubectl delete deployment sre-rag-api',
                                              'correct': False,
                                              'explanation': '❌ Incorreto. Deletar o deployment não resolve a falta do '
                                                             'secret — os novos pods continuarão falhando pelo mesmo '
                                                             'motivo.',
                                              'explanation_en': '❌ Incorrect. Recreating the deployment will still '
                                                                'encounter the missing Secret dependency.',
                                              'id': 'delete-deployment',
                                              'label': 'Deletar o deployment e recriá-lo',
                                              'label_en': 'Delete and recreate the deployment'},
                                            { 'command': 'kubectl set env deployment/sre-rag-api BYPASS_AUTH=true',
                                              'correct': False,
                                              'explanation': '❌ Violação de segurança. Não se deve desativar '
                                                             'validações de segurança para contornar falha de '
                                                             'configuração de infraestrutura.',
                                              'explanation_en': '❌ Major security violation! Bypassing authentication '
                                                                'compromises the entire system.',
                                              'id': 'ignore-error',
                                              'label': 'Alterar o código para rodar sem autenticação',
                                              'label_en': 'Modify application code to bypass authentication'}],
                             'symptoms': [ 'kubectl get pods: sre-rag-api-* CrashLoopBackOff',
                                           "kubectl logs: KeyError: 'OPENAI_API_KEY' not found in environment",
                                           'Zero pods prontos no deployment (0/2 READY)',
                                           "Eventos: Error: secret 'sre-rag-secrets' not found"],
                             'symptoms_en': [ 'kubectl get pods: sre-rag-api-* CrashLoopBackOff',
                                              "kubectl logs: KeyError: 'OPENAI_API_KEY' not found in environment",
                                              'Zero pods ready in deployment (0/2 READY)',
                                              "Events: Error: secret 'sre-rag-secrets' not found"],
                             'title': 'ConfigMap / Secret Ausente (CrashLoop)',
                             'title_en': 'Missing ConfigMap / Secret (CrashLoop)'},
  'oom-kill': { 'category': 'Recursos',
                'category_en': 'Resources',
                'chaos_action': None,
                'command': 'helm upgrade sre-rag ./helm/sre-rag --set api.resources.limits.memory=1024Mi',
                'concepts': { 'architecture_components': [ 'Linux cgroups v2 memory.max',
                                                           'Kernel oom_score_adj',
                                                           'Kubernetes Pod QoS'],
                              'best_practices': [ 'Sempre monitore `container_memory_working_set_bytes` e não o '
                                                  '`usage_bytes`, pois este último inclui page cache reutilizável.',
                                                  'Evite superdimensionar memória sem necessidade, mas garanta margem '
                                                  'de 20-30% acima do pico normal.',
                                                  'Para serviços de latência crítica, utilize QoS Guaranteed (requests '
                                                  '== limits).'],
                              'best_practices_en': [ 'Always monitor `container_memory_working_set_bytes` rather than '
                                                     '`usage_bytes`, as the latter includes reclaimable page cache.',
                                                     'Avoid unnecessary memory overcommit, but maintain a 20-30% '
                                                     'buffer above normal peak.',
                                                     'Set memory requests equal to limits for mission-critical '
                                                     'services to achieve Guaranteed QoS (`oom_score_adj -997`).'],
                              'category_en': 'Resources',
                              'golden_signals': [ 'Saturação de Memória (Memory Saturation %)',
                                                  'Taxa de Reinícios de Containers (Container Restarts/min)'],
                              'golden_signals_en': ['Memory Working Set vs Limit (Saturation)', 'Pod OOMKills Rate'],
                              'how_it_works': 'No Linux, o cgroup limita a quantidade de memória física e swap. Quando '
                                              'o processo excede `memory.max`, o kernel invoca o Out-Of-Memory Killer. '
                                              'O kernel atribui um score baseado no consumo e no `oom_score_adj` '
                                              'configurado pelo Kubelet (baseado no QoS: BestEffort, Burstable ou '
                                              'Guaranteed) e envia um sinal SIGKILL (137).',
                              'how_it_works_en': 'In Linux, cgroups limit physical memory and swap consumption. When a '
                                                 'process exceeds `memory.max`, the kernel invokes the Out-Of-Memory '
                                                 'Killer. The kernel assigns a score based on consumption and '
                                                 '`oom_score_adj` (configured by kubelet based on QoS: BestEffort, '
                                                 'Burstable or Guaranteed) and sends SIGKILL (137).',
                              'resource_title': 'Linux Kernel OOM Killer & Kubernetes QoS Classes',
                              'resource_title_en': 'Linux Kernel OOM Killer & Kubernetes QoS Classes'},
                'description': 'O pod da API é repetidamente encerrado pelo kernel do Linux com OOMKilled (Exit Code '
                               '137). O consumo de memória atingiu 100% do limite configurado sob tráfego.',
                'description_en': 'API pod terminated by Linux kernel OOM Killer with exit code 137. Memory usage '
                                  'reached 100% of limits under load.',
                'detection_delay_seconds': 25,
                'difficulty': 'easy',
                'hints': [ { 'hint': 'O contêiner foi morto com Exit Code 137 pelo kernel.',
                             'hint_en': 'The container was killed with Exit Code 137 by the Linux kernel.'},
                           { 'hint': 'Aumente o limite de memória para 1Gi usando kubectl set resources.',
                             'hint_en': 'Increase the memory limit to 1Gi using kubectl set resources.'}],
                'icon': '💀',
                'id': 'oom-kill',
                'investigation_delay_seconds': 70,
                'runbook': '/docs/runbooks/oom-kill',
                'runbook_steps': { 'diagnosis': [ 'kubectl get pods -l app=sre-rag-api (Status: CrashLoopBackOff ou '
                                                  'OOMKilled).',
                                                  'kubectl describe pod <pod-name> (Reason: OOMKilled, Exit Code: '
                                                  '137).',
                                                  'kubectl logs <pod-name> --previous (Última operação: processamento '
                                                  'de grande batch de vetores).'],
                                   'diagnosis_en': [ 'kubectl describe pod -l app=sre-rag-api (Last State: Terminated, '
                                                     'Reason: OOMKilled, Exit Code: 137).',
                                                     'kubectl top pods -l app=sre-rag-api (Memory consumption hitting '
                                                     '512Mi limit).',
                                                     "dmesg -T | grep -E -i 'oom|killed process' on the worker node."],
                                   'mitigation': { 'action': 'Aumentar o limite de memória no Helm para 1024Mi.',
                                                   'command': 'helm upgrade sre-rag ./helm/sre-rag --set '
                                                              'api.resources.limits.memory=1024Mi',
                                                   'validation': 'kubectl get pods (Verificar se os pods permanecem em '
                                                                 'Running sem novos restarts).'},
                                   'mitigation_en': { 'action_en': 'Increase memory limit and requests to 1Gi via '
                                                                   'deployment patch.',
                                                      'command': 'kubectl set resources deployment sre-rag-api -c api '
                                                                 '--limits=memory=1Gi --requests=memory=512Mi',
                                                      'validation_en': 'Verify pod restarts stop and memory stabilizes '
                                                                       'under 600Mi.'},
                                   'prevention': [ "Configurar QoS Class 'Guaranteed' com requests == limits para pods "
                                                   'de missão crítica.',
                                                   'Alerta preditivo com PromQL predict_linear para projetar '
                                                   'esgotamento de memória com 1 hora de antecedência.'],
                                   'prevention_en': [ 'Configure vertical pod autoscaler (VPA) in recommendation mode.',
                                                      'Add automated memory profiling to staging load test pipeline.'],
                                   'root_cause': { 'analysis': 'O modelo carregava o vocabulário inteiro em memória '
                                                               'sem chunking durante picos de consultas.',
                                                   'permanent_fix': 'Implementar gerador paginado com yield para '
                                                                    'carregar embeddings sob demanda.'},
                                   'root_cause_en': { 'analysis_en': 'Sentence-transformers model caching required '
                                                                     'more working set RAM than the 512Mi limit.',
                                                      'permanent_fix_en': 'Profile model memory footprint and update '
                                                                          'Helm values-prod.yaml with 1Gi memory '
                                                                          'limit.'},
                                   'triage': [ 'Alerta KubePodCrashLooping / ContainerOOMKilled disparado.',
                                               'Prometheus: container_memory_working_set_bytes atingindo '
                                               'container_spec_memory_limit_bytes.',
                                               'Pods com restarts repetidos (exit code 137).'],
                                   'triage_en': [ 'Verify Alertmanager alert: KubePodOOMKilled.',
                                                  'Inspect memory saturation: container_memory_working_set_bytes / '
                                                  "kube_pod_container_resource_limits{resource='memory'} * 100.",
                                                  'Confirm Pod termination reason: OOMKilled (Exit Code 137).']},
                'severity': 'SEV-1',
                'solutions': [ { 'command': 'helm upgrade sre-rag ./helm/sre-rag --set '
                                            'api.resources.limits.memory=1024Mi',
                                 'correct': True,
                                 'explanation': '✅ Correto! Aumentar o limit para 1024Mi alivia o estrangulamento de '
                                                'memória imediatamente, estabilizando o pod enquanto o perfil de uso é '
                                                'otimizado.',
                                 'explanation_en': '✅ Correct! Raising memory limit immediately stabilizes the '
                                                   'container while memory profiling investigates the leak.',
                                 'id': 'increase-memory',
                                 'label': 'Aumentar `resources.limits.memory` no Helm values + investigar memory leak',
                                 'label_en': 'Increase resources.limits.memory in Helm values + profile memory leak'},
                               { 'command': 'helm rollback sre-rag',
                                 'correct': False,
                                 'explanation': '❌ Incorreto. O aumento de consumo é derivado de volume de dados sob '
                                                'carga; a versão anterior possui o mesmo limit e também cairia.',
                                 'explanation_en': '❌ Incorrect. Memory pressure is driven by workload size; rolling '
                                                   'back does not expand container headroom.',
                                 'id': 'rollback',
                                 'label': 'Fazer rollback para a versão anterior',
                                 'label_en': 'Rollback to previous release tag'},
                               { 'command': 'kubectl scale deployment sre-rag-api --replicas=8',
                                 'correct': False,
                                 'explanation': '❌ Ineficaz. Se uma requisição única consome mais de 512Mi, todos os '
                                                'pods novos continuarão morrendo simultaneamente sob carga.',
                                 'explanation_en': '❌ Ineffective. If batch processing exceeds limits, every spawned '
                                                   'replica will crash in parallel.',
                                 'id': 'hpa-scale',
                                 'label': 'Escalar mais réplicas via HPA',
                                 'label_en': 'Scale more replicas via HPA'}],
                'symptoms': [ 'kubectl describe pod: Reason = OOMKilled, Exit Code: 137',
                              'Last State: Terminated with exit code 137',
                              'Memory usage: 512Mi/512Mi (100% do limit)',
                              'Restarts aumentando progressivamente sob carga'],
                'symptoms_en': [ 'kubectl describe pod: Reason = OOMKilled, Exit Code: 137',
                                 'Last State: Terminated with exit code 137',
                                 'Memory usage: 512Mi/512Mi (100% of configured limit)',
                                 'Repeated restarts under incoming user workload'],
                'title': 'OOM Kill em Pod da API',
                'title_en': 'API Pod OOM Kill'},
  'pod-pending-resources': { 'category': 'Capacidade',
                             'category_en': 'Capacity',
                             'chaos_action': None,
                             'command': 'helm upgrade sre-rag ./helm/sre-rag --set api.resources.requests.cpu=250m',
                             'concepts': { 'architecture_components': [ 'Kube-Scheduler',
                                                                        'Node Allocatable',
                                                                        'Requests vs Limits'],
                                           'best_practices': [ 'Requests representam reserva garantida; Limits '
                                                               'representam o teto máximo de estouro.',
                                                               'Monitore a razão de alocação vs consumo real: use '
                                                               'ferramentas de right-sizing como Kubecost ou '
                                                               'Goldilocks.',
                                                               'Nunca deixe pods de produção sem `resources.requests` '
                                                               'definidos.'],
                                           'best_practices_en': [ 'Requests represent guaranteed reservation; limits '
                                                                  'represent the burst ceiling.',
                                                                  'Monitor allocation ratio vs actual usage; '
                                                                  'right-size requests using Kubecost or Goldilocks.',
                                                                  'Deploy Cluster Autoscaler (CAS) or Karpenter to '
                                                                  'spin up nodes when pods are unschedulable.'],
                                           'category_en': 'Capacity',
                                           'golden_signals': [ 'Tempo em Estado Pending (Pod Scheduling Latency)',
                                                               'Alocação de CPU do Cluster (Node CPU Commit %)'],
                                           'golden_signals_en': [ 'Cluster CPU Allocatable Saturation %',
                                                                  'Pending Pod Count'],
                                           'how_it_works': 'O Kube-Scheduler decide em qual nó cada pod será executado '
                                                           'através de duas fases: Filtragem (Predicates) e Pontuação '
                                                           '(Priorities). Na filtragem, o scheduler calcula a soma dos '
                                                           '`requests` dos pods já alocados. Se a capacidade '
                                                           '`Allocatable` do nó não suportar a soma, o nó é '
                                                           'descartado. Se nenhum nó passar, o pod permanece em '
                                                           "'Pending'.",
                                           'how_it_works_en': 'Kube-Scheduler decides where each pod runs through a '
                                                              'two-phase cycle: Filtering (Predicates) and Scoring '
                                                              '(Priorities). In filtering, it sums pod requests '
                                                              'already assigned to a node; if Allocatable capacity '
                                                              'cannot accommodate the new request, the node is '
                                                              'eliminated. If no node passes, pod stays in Pending.',
                                           'resource_title': 'Kube-Scheduler: Predicates, Priorities & Capacidade '
                                                             'Alocável',
                                           'resource_title_en': 'Kube-Scheduler: Predicates, Priorities & Allocatable '
                                                                'Capacity'},
                             'description': "Novos pods da API estão presos indefinidamente no estado 'Pending'. O "
                                            "Kube-Scheduler reporta '0/3 nodes are available: 3 Insufficient cpu'. Os "
                                            'requests de CPU foram acidentalmente configurados com valor exorbitante '
                                            '(8000m por pod).',
                             'description_en': "New API pods stuck in 'Pending'. Kube-Scheduler events report '0/3 "
                                               "nodes are available: 3 Insufficient cpu' due to misconfigured 8000m "
                                               'requests.',
                             'detection_delay_seconds': 20,
                             'difficulty': 'easy',
                             'hints': [ { 'hint': 'Verifique a mensagem de FailedScheduling com kubectl describe pod.',
                                          'hint_en': 'Check FailedScheduling events using kubectl describe pod.'},
                                        { 'hint': 'Reduza a CPU request para 250m usando kubectl set resources.',
                                          'hint_en': 'Reduce CPU request to 250m using kubectl set resources.'}],
                             'icon': '⏳',
                             'id': 'pod-pending-resources',
                             'investigation_delay_seconds': 60,
                             'runbook': '/docs/runbooks/pod-pending-resources',
                             'runbook_steps': { 'diagnosis': [ 'kubectl get pods -l app=sre-rag-api (Status: Pending).',
                                                               'kubectl describe pod <pod-name> (Events: Warning '
                                                               'FailedScheduling: 0/3 nodes available: 3 Insufficient '
                                                               'cpu).',
                                                               "kubectl describe nodes | grep -A 8 'Allocated "
                                                               "resources:' (CPU Requests em 98% da capacidade)."],
                                                'diagnosis_en': [ 'kubectl describe pod (Warning: FailedScheduling: '
                                                                  'Insufficient cpu).',
                                                                  'kubectl top nodes (Check physical utilization vs '
                                                                  'requested allocation).',
                                                                  "kubectl describe nodes | grep -A 8 'Allocated "
                                                                  "resources' (Requests at 98%)."],
                                                'mitigation': { 'action': 'Corrigir os requests de CPU no Helm para o '
                                                                          'valor nominal de 250m.',
                                                                'command': 'helm upgrade sre-rag ./helm/sre-rag --set '
                                                                           'api.resources.requests.cpu=250m',
                                                                'validation': 'kubectl get pods (Verificar transição '
                                                                              'para Running em poucos segundos).'},
                                                'mitigation_en': { 'action_en': 'Adjust CPU requests down to 250m to '
                                                                                'fit within current node allocatable '
                                                                                'capacity.',
                                                                   'command': 'kubectl set resources deployment '
                                                                              'sre-rag-api -c api --requests=cpu=250m',
                                                                   'validation_en': 'Pod is scheduled immediately and '
                                                                                    'transitions to Running.'},
                                                'prevention': [ 'Configurar Cluster Autoscaler ou Karpenter para '
                                                                'provisionar nós dinamicamente caso a demanda seja '
                                                                'legítima.',
                                                                'Implantar LimitRanges no namespace para restringir '
                                                                'requests máximos permitidos por container.'],
                                                'prevention_en': [ 'Install Karpenter or Cluster Autoscaler for '
                                                                   'automatic capacity provisioning.',
                                                                   'Set up LimitRange in namespace to enforce sensible '
                                                                   'request boundaries.'],
                                                'root_cause': { 'analysis': 'Um erro de digitação no values.yaml '
                                                                            'colocou `cpu: 8000m` (8 núcleos) em vez '
                                                                            'de `cpu: 250m`.',
                                                                'permanent_fix': 'Adicionar política de validação de '
                                                                                 'admission controller (Kyverno / OPA '
                                                                                 'Gatekeeper) limitando o teto de '
                                                                                 'requests.'},
                                                'root_cause_en': { 'analysis_en': 'CPU request was overdimensioned to '
                                                                                  '4000m on nodes with only 2000m '
                                                                                  'allocatable.',
                                                                   'permanent_fix_en': 'Right-size requests in '
                                                                                       'values.yaml and configure '
                                                                                       'cluster autoscaling.'},
                                                'triage': [ 'Alerta KubePodNotScheduled / HPAUnableToScale.',
                                                            "Pods presos em estado 'Pending' há mais de 5 minutos.",
                                                            'Capacidade do cluster com nós em alta alocação de '
                                                            'requests.'],
                                                'triage_en': [ 'Check alert: KubePodPendingLongerThan5m.',
                                                               'Verify pod status: Pending (Phase: Pending).',
                                                               'Inspect scheduler events: 0/3 nodes available: '
                                                               'insufficient cpu.']},
                             'severity': 'SEV-2',
                             'solutions': [ { 'command': 'helm upgrade sre-rag ./helm/sre-rag --set '
                                                         'api.resources.requests.cpu=250m',
                                              'correct': True,
                                              'explanation': '✅ Correto! Ajustar os requests de CPU para o tamanho '
                                                             'real da aplicação (250m) permite que o Scheduler agende '
                                                             'os pods nos nós disponíveis imediatamente.',
                                              'explanation_en': '✅ Correct! Right-sizing CPU requests allows the '
                                                                'Kube-Scheduler to fit pods into existing cluster '
                                                                'nodes.',
                                              'id': 'adjust-requests',
                                              'label': 'Reduzir `resources.requests.cpu` para 250m via Helm',
                                              'label_en': 'Lower resources.requests.cpu to 250m via Helm'},
                                            { 'command': 'kubectl cordon node-1 node-2 node-3',
                                              'correct': False,
                                              'explanation': '❌ Incorreto e danoso. Fazer cordon impede qualquer pod '
                                                             'de ser agendado nos nós, agravando a indisponibilidade.',
                                              'explanation_en': '❌ Disastrous. Cordoning nodes prevents scheduling on '
                                                                'all nodes entirely.',
                                              'id': 'cordon-nodes',
                                              'label': 'Colocar os nós do cluster em manutenção (cordon)',
                                              'label_en': 'Cordon the cluster nodes'},
                                            { 'command': 'kubectl rollout restart deployment/kube-scheduler -n '
                                                         'kube-system',
                                              'correct': False,
                                              'explanation': '❌ Incorreto. O scheduler está funcionando perfeitamente; '
                                                             'ele rejeita o agendamento porque a capacidade matemática '
                                                             'solicitada não cabe nos nós.',
                                              'explanation_en': '❌ Incorrect. The scheduler is acting properly by '
                                                                'enforcing resource limits.',
                                              'id': 'restart-scheduler',
                                              'label': 'Reiniciar o kube-scheduler no control plane',
                                              'label_en': 'Restart kube-scheduler in control plane'}],
                             'symptoms': [ 'kubectl get pods: sre-rag-api-* Pending',
                                           'kubectl describe pod: 0/3 nodes are available: 3 Insufficient cpu',
                                           'HPA incapaz de escalar novos pods para absorver tráfego',
                                           'Alerta KubePodNotScheduled disparado há 10 minutos'],
                             'symptoms_en': [ 'kubectl get pods: sre-rag-api-* Pending',
                                              'kubectl describe pod: 0/3 nodes are available: 3 Insufficient cpu',
                                              'HPA unable to scale replicas to handle user traffic',
                                              'Alert KubePodNotScheduled firing for 10 minutes'],
                             'title': 'Pod em Estado Pending por Falta de CPU',
                             'title_en': 'Pod Stuck in Pending (Insufficient CPU)'},
  'pvc-mount-deadlock': { 'category': 'Armazenamento',
                          'category_en': 'Storage',
                          'chaos_action': None,
                          'command': 'kubectl delete volumeattachment $(kubectl get volumeattachment -o '
                                     "jsonpath='{.items[0].metadata.name}') --force",
                          'concepts': { 'architecture_components': [ 'CSI Attach/Detach Controller',
                                                                     'VolumeAttachment CRD',
                                                                     'StorageClass Access Modes'],
                                        'best_practices': [ 'Sempre use StatefulSets para workloads que exigem '
                                                            'persistência com volumes dedicados.',
                                                            'Mantenha snapshots regulares dos Persistent Volumes via '
                                                            'VolumeSnapshot CRD.',
                                                            'Garanta que o CSI driver do cluster esteja atualizado com '
                                                            'suporte a force-detach seguro.'],
                                        'best_practices_en': [ 'Use StatefulSets instead of Deployments for pods '
                                                               'requiring persistent RWO storage.',
                                                               'Ensure CSI drivers support volume health monitoring '
                                                               'and graceful detach timeouts.',
                                                               'Adopt ReadWriteMany (RWX) storage (NFS, CephFS, EFS) '
                                                               'when multiple replicas need shared access.'],
                                        'category_en': 'Storage',
                                        'golden_signals': [ 'Tempo de Montagem de Volumes (Volume Attach Latency)',
                                                            'Falhas de Montagem de Armazenamento (Storage Mount '
                                                            'Errors)'],
                                        'golden_signals_en': [ 'VolumeAttachment Detach Timeout Rate',
                                                               'Pod ContainerCreating Duration'],
                                        'how_it_works': 'Volumes `ReadWriteOnce (RWO)` só podem ser montados por um '
                                                        'único nó por vez para prevenir corrupção no filesystem. O '
                                                        '`CSI attach/detach controller` cria um objeto '
                                                        '`VolumeAttachment` para coordenar com a API do provedor de '
                                                        'nuvem (ex: AWS EBS attach). Se um nó morre de forma abrupta, '
                                                        'o control plane mantém o lock até o timeout de fencing para '
                                                        'evitar split-brain no disco. O pod no novo nó fica bloqueado '
                                                        'até o release desse lock.',
                                        'how_it_works_en': 'ReadWriteOnce (RWO) persistent volumes can only be '
                                                           'attached to a single node simultaneously. When a stateful '
                                                           'pod is deleted and rescheduled onto a different node while '
                                                           'the original node has not cleanly detached the volume (due '
                                                           'to network timeout or ungraceful termination), '
                                                           'attach-detach-controller fails with `Multi-Attach error '
                                                           'for volume`.',
                                        'resource_title': 'Kubernetes Storage: CSI Drivers, VolumeAttachment & Modos '
                                                          'de Acesso RWO',
                                        'resource_title_en': 'Kubernetes Storage: CSI Drivers, VolumeAttachment & RWO '
                                                             'Access Modes'},
                          'description': "O pod de persistência está preso em ContainerCreating com erro 'Multi-Attach "
                                         "error for volume: Volume is already exclusively attached to node-1'. O nó "
                                         'anterior travou mas o CSI driver não liberou o VolumeAttachment.',
                          'description_en': "Stateful pod stuck in ContainerCreating with 'Multi-Attach error for "
                                            "volume'. Stale node crashed and CSI driver failed to release the "
                                            'VolumeAttachment.',
                          'detection_delay_seconds': 35,
                          'difficulty': 'hard',
                          'hints': [ { 'hint': 'Verifique o erro de Multi-Attach nos eventos com kubectl describe pod.',
                                       'hint_en': 'Check Multi-Attach errors in events using kubectl describe pod.'},
                                     { 'hint': 'Delete o objeto volumeattachment órfão usando kubectl delete '
                                               'volumeattachment.',
                                       'hint_en': 'Delete the orphaned volumeattachment object using kubectl delete '
                                                  'volumeattachment.'}],
                          'icon': '🗄️',
                          'id': 'pvc-mount-deadlock',
                          'investigation_delay_seconds': 80,
                          'runbook': '/docs/runbooks/pvc-mount-deadlock',
                          'runbook_steps': { 'diagnosis': [ 'kubectl get pods -l app=sre-rag-db (Status: '
                                                            'ContainerCreating).',
                                                            'kubectl describe pod sre-rag-db-0 (Multi-Attach error: '
                                                            'Volume is already exclusively attached to node-1).',
                                                            'kubectl get volumeattachment (Status do attachment preso '
                                                            'em Attached=true no nó offline).'],
                                             'diagnosis_en': [ 'kubectl describe pod (Warning: Multi-Attach error for '
                                                               'volume pvc-xyz: Volume is already exclusively attached '
                                                               'to node-1).',
                                                               'kubectl get volumeattachment (Check stuck '
                                                               'volumeattachments).',
                                                               'Verify old node status and volume detachment state.'],
                                             'mitigation': { 'action': 'Deletar o recurso VolumeAttachment órfão com '
                                                                       '--force.',
                                                             'command': 'kubectl delete volumeattachment $(kubectl get '
                                                                        'volumeattachment -o '
                                                                        "jsonpath='{.items[0].metadata.name}') --force",
                                                             'validation': 'kubectl get pods (Verificar transição para '
                                                                           'Running em até 30 segundos).'},
                                             'mitigation_en': { 'action_en': 'Delete orphaned VolumeAttachment to '
                                                                             'release volume lock immediately.',
                                                                'command': 'kubectl delete volumeattachment '
                                                                           '<volumeattachment-id> --force '
                                                                           '--grace-period=0',
                                                                'validation_en': 'Volume attaches cleanly to target '
                                                                                 'node and pod transitions to '
                                                                                 'Running.'},
                                             'prevention': [ 'Usar StorageClasses com `volumeBindingMode: '
                                                             'WaitForFirstConsumer`.',
                                                             'Testes de caos simulando parada forçada de nó com '
                                                             'volumes persistentes para validar recuperação '
                                                             'automática.'],
                                             'prevention_en': [ 'Migrate stateful workloads to StatefulSets with '
                                                                'volumeClaimTemplates.',
                                                                'Configure storage provider automated volume '
                                                                'attachment self-healing.'],
                                             'root_cause': { 'analysis': 'Falha de hardware no nó worker-1 fez o '
                                                                         'kubelet parar sem notificar o '
                                                                         'controller-manager sobre o desanexamento do '
                                                                         'volume EBS/GPD.',
                                                             'permanent_fix': 'Configurar node-fencing automático e '
                                                                              'atualizar os CSI drivers da nuvem para '
                                                                              'versões com timeout agressivo de '
                                                                              'detach.'},
                                             'root_cause_en': { 'analysis_en': 'Worker node experienced ungraceful '
                                                                               'reboot while cloud disk detach call '
                                                                               'timed out.',
                                                                'permanent_fix_en': 'Configure non-graceful node '
                                                                                    'shutdown feature gate and tune '
                                                                                    'CSI attach-detach controller '
                                                                                    'timeouts.'},
                                             'triage': [ 'Alerta VolumeAttachmentStuck / KubePodCrashWaiting.',
                                                         'Pod com volume persistente preso em ContainerCreating por > '
                                                         '10 minutos.',
                                                         'Eventos FailedAttachVolume reportados pelo Kubelet.'],
                                             'triage_en': [ 'Check alert: KubePodContainerCreatingStuck (>5m).',
                                                            'Inspect pod events: Warning FailedAttachVolume.',
                                                            'Confirm pod status: ContainerCreating stuck on new '
                                                            'node.']},
                          'severity': 'SEV-2',
                          'solutions': [ { 'command': 'kubectl delete volumeattachment $(kubectl get volumeattachment '
                                                      "-o jsonpath='{.items[0].metadata.name}') --force",
                                           'correct': True,
                                           'explanation': '✅ Correto! Deletar o VolumeAttachment órfão destrava o CSI '
                                                          'attach/detach controller, permitindo anexar o disco RWO com '
                                                          'segurança ao novo nó.',
                                           'explanation_en': '✅ Correct! Deleting the stuck VolumeAttachment unlocks '
                                                             'the CSI controller to mount the RWO volume onto the '
                                                             'healthy node.',
                                           'id': 'force-delete-attachment',
                                           'label': 'Deletar o VolumeAttachment órfão com flag `--force`',
                                           'label_en': 'Force-delete the stale VolumeAttachment resource'},
                                         { 'command': 'kubectl delete pvc data-sre-rag-db-0',
                                           'correct': False,
                                           'explanation': '❌ Perigo crítico de perda de dados! Deletar o PVC pode '
                                                          'apagar o volume persistente subjacente e destruir o banco '
                                                          'de dados.',
                                           'explanation_en': '❌ Extreme danger! Deleting PVC may destroy the '
                                                             'underlying storage and lose all data.',
                                           'id': 'delete-pvc',
                                           'label': 'Deletar o PersistentVolumeClaim (`kubectl delete pvc`)',
                                           'label_en': 'Delete the PersistentVolumeClaim (`kubectl delete pvc`)'},
                                         { 'command': 'kubectl patch pv pv-data --patch '
                                                      '\'{"spec":{"accessModes":["ReadWriteMany"]}}\'',
                                           'correct': False,
                                           'explanation': '❌ Inválido. Block storages (EBS, Persistent Disk) não '
                                                          'suportam ReadWriteMany sem sistemas de arquivos de rede '
                                                          '(NFS, CephFS).',
                                           'explanation_en': '❌ Invalid. Block storage providers do not natively '
                                                             'support ReadWriteMany.',
                                           'id': 'change-access-mode',
                                           'label': 'Alterar o volume para ReadWriteMany sem suporte da nuvem',
                                           'label_en': 'Change access mode to ReadWriteMany without cloud support'}],
                          'symptoms': [ 'kubectl get pods: sre-rag-db-0 ContainerCreating',
                                        'kubectl describe pod: Multi-Attach error for volume: Volume is already '
                                        'exclusively attached',
                                        'VolumeAttachment órfão impedindo montagem no novo nó',
                                        'Banco de dados indisponível, derrubando endpoints dependentes'],
                          'symptoms_en': [ 'kubectl get pods: sre-rag-db-0 ContainerCreating',
                                           'kubectl describe pod: Multi-Attach error for volume: Volume is already '
                                           'exclusively attached',
                                           'Stale VolumeAttachment blocking attach to the healthy node',
                                           'Database unavailable, impacting all reliant services'],
                          'title': 'PVC Deadlock (Multi-Attach Error em RWO)',
                          'title_en': 'PVC Deadlock (Multi-Attach Error on RWO Volume)'},
  'redis-exhausted': { 'category': 'Desempenho',
                       'category_en': 'Performance',
                       'chaos_action': None,
                       'command': 'kubectl set env deployment/sre-rag-api REDIS_MAX_CONNECTIONS=100 REDIS_TIMEOUT=30',
                       'concepts': { 'architecture_components': [ 'TCP Handshake & Sockets',
                                                                  'Redis maxclients',
                                                                  'Connection Pooling Pattern'],
                                     'best_practices': [ 'Sempre use instâncias singleton de ConnectionPool em '
                                                         'frameworks assíncronos.',
                                                         'Configure timeouts agressivos de conexão '
                                                         '(connect_timeout=2s, socket_timeout=3s).',
                                                         'Monitore a taxa de conexões ativas vs `maxclients` com '
                                                         'alertas em 80% de ocupação.'],
                                     'best_practices_en': [ 'Always use singleton Connection Pools (e.g., redis-py '
                                                            'ConnectionPool, HikariCP, JedisPool) with bounded '
                                                            'max_connections.',
                                                            'Configure Redis `timeout 300` in redis.conf to reap idle '
                                                            'client connections automatically.',
                                                            'Monitor `connected_clients` vs `maxclients` and alert '
                                                            'when utilization exceeds 75%.'],
                                     'category_en': 'Performance',
                                     'golden_signals': [ 'Clientes Conectados no Redis (Connected Clients Count)',
                                                         'Latência de Operação de Cache (Redis Ping Latency ms)'],
                                     'golden_signals_en': [ 'Redis Connected Clients / Maxclients %',
                                                            'Rejected Connections Total'],
                                     'how_it_works': 'Cada conexão TCP consome memória no servidor e um file '
                                                     'descriptor no kernel. Sem um pool de conexões, cada thread da '
                                                     'API realiza o 3-way handshake para uma consulta rápida e '
                                                     'abandona o socket. O Redis atinge seu limite de segurança '
                                                     '(`maxclients 10000`) e passa a rejeitar novos handshakes, '
                                                     'fazendo as threads da API travarem aguardando resposta.',
                                     'how_it_works_en': 'Each Redis client connection requires an OS file descriptor '
                                                        'and memory buffer in the Redis event loop (epoll). When an '
                                                        'application fails to reuse connections and opens a new '
                                                        'connection per request without closing them, Redis hits '
                                                        '`maxclients` (default 10000). Redis then rejects any new TCP '
                                                        'handshake with `ERR max number of clients reached`, cascading '
                                                        'errors across all dependent microservices.',
                                     'resource_title': 'Sockets TCP, Estados de Conexão & Padrão Connection Pool',
                                     'resource_title_en': 'TCP Sockets, Connection States & Connection Pool Pattern'},
                       'description': 'O Redis atingiu o limite de maxclients (10.000 conexões ativas). Novas conexões '
                                      "da API falham com 'ERR max number of clients reached'. Consultas ao RAG falham "
                                      'por timeout de cache.',
                       'description_en': 'Redis maxclients limit reached (10,000 connections). Application threads '
                                         'hanging on connection timeouts, escalating response latency across all '
                                         'endpoints.',
                       'detection_delay_seconds': 40,
                       'difficulty': 'extreme',
                       'hints': [ { 'hint': 'Verifique o número de clientes conectados com redis-cli info clients.',
                                    'hint_en': 'Check connected client count using redis-cli info clients.'},
                                  { 'hint': 'Aumente maxclients e finalize conexões ociosas com redis-cli config set e '
                                            'client kill.',
                                    'hint_en': 'Increase maxclients and terminate idle connections using redis-cli '
                                               'config set and client kill.'}],
                       'icon': '🔴',
                       'id': 'redis-exhausted',
                       'investigation_delay_seconds': 80,
                       'runbook': '/docs/runbooks/redis-exhausted',
                       'runbook_steps': { 'diagnosis': [ 'kubectl exec -it sts/redis-0 -- redis-cli info clients '
                                                         '(connected_clients: 10000).',
                                                         'netstat -an | grep 6379 (Milhares de sockets em estado '
                                                         'ESTABLISHED e CLOSE_WAIT).',
                                                         'Logs da aplicação: redis.exceptions.ConnectionError: ERR max '
                                                         'number of clients reached.'],
                                          'diagnosis_en': [ 'redis-cli info clients (connected_clients: 10000, '
                                                            'blocked_clients: 240).',
                                                            'redis-cli client list (Thousands of connections idle in '
                                                            'TIME_WAIT / CLOSE_WAIT state).',
                                                            'Inspect application code: redis.Redis() instantiated per '
                                                            'incoming request instead of shared pool.'],
                                          'mitigation': { 'action': 'Configurar variáveis de ambiente na API limitando '
                                                                    'conexões simultâneas e ativando idle timeout.',
                                                          'command': 'kubectl set env deployment/sre-rag-api '
                                                                     'REDIS_MAX_CONNECTIONS=100 REDIS_TIMEOUT=30',
                                                          'validation': 'kubectl exec -it sts/redis-0 -- redis-cli '
                                                                        'info clients (connected_clients recua para < '
                                                                        '300).'},
                                          'mitigation_en': { 'action_en': 'Kill idle connections and temporarily '
                                                                          'increase maxclients to 20000 to restore '
                                                                          'service.',
                                                             'command': 'redis-cli config set maxclients 20000 && '
                                                                        'redis-cli client kill type normal',
                                                             'validation_en': 'Connected clients count drops and API '
                                                                              'requests resume connecting normally.'},
                                          'prevention': [ 'Configurar `timeout 60` e `tcp-keepalive 30` no '
                                                          '`redis.conf`.',
                                                          'Implementar Circuit Breaker na aplicação para bypassar '
                                                          'cache sem travar requisições caso o Redis falhe.'],
                                          'prevention_en': [ 'Configure server-side idle timeout: redis-cli config set '
                                                             'timeout 60.',
                                                             'Enforce connection pooling code reviews and static '
                                                             'analysis checks.'],
                                          'root_cause': { 'analysis': 'Código criava `redis.Redis()` diretamente '
                                                                      'dentro da rota FastAPI sem usar singleton de '
                                                                      '`redis.ConnectionPool`.',
                                                          'permanent_fix': 'Refatorar o cliente de cache para usar '
                                                                           'injeção de dependência com pool estático '
                                                                           'reutilizável.'},
                                          'root_cause_en': { 'analysis_en': 'Connection leak in background task '
                                                                            'handler opening connections without '
                                                                            'closing.',
                                                             'permanent_fix_en': 'Refactor application to use a global '
                                                                                 'singleton Redis connection pool with '
                                                                                 'max_connections=50.'},
                                          'triage': [ 'Alerta RedisTooManyConnections (connected_clients >= 9900).',
                                                      'Aumento abrupto de erros 500 em endpoints dependentes de cache.',
                                                      'Latência de comunicação com Redis explodindo para 5000ms.'],
                                          'triage_en': [ 'Check alert: RedisMaxClientsReached (connected_clients >= '
                                                         '10000).',
                                                         'Inspect API logs: RedisConnectionError: ERR max number of '
                                                         'clients reached.',
                                                         'Verify cache lookup failures causing 100% database '
                                                         'fallback.']},
                       'severity': 'SEV-1',
                       'solutions': [ { 'command': 'kubectl set env deployment/sre-rag-api REDIS_MAX_CONNECTIONS=100 '
                                                   'REDIS_TIMEOUT=30',
                                        'correct': True,
                                        'explanation': '✅ Correto! A aplicação criava uma nova conexão TCP por request '
                                                       'sem pool. O ConnectionPool reutiliza conexões e limita o teto '
                                                       'máximo, eliminando o vazamento.',
                                        'explanation_en': '✅ Correct! Reusing connections with a bounded pool and '
                                                          'timing out idle clients mitigates leak completely.',
                                        'id': 'fix-connection-pool',
                                        'label': 'Configurar ConnectionPool no cliente Redis com max_connections e '
                                                 'timeout',
                                        'label_en': 'Configure connection pool limits on API + enable Redis timeout '
                                                    'idle clients'},
                                      { 'command': 'kubectl delete pod redis-0',
                                        'correct': False,
                                        'explanation': '⚠️ Mitigação temporária. Reiniciar derruba as 10k conexões, '
                                                       'mas a aplicação vazará conexões novamente em poucos minutos.',
                                        'explanation_en': '⚠️ Temporary workaround; connections will saturate again '
                                                          'within minutes.',
                                        'id': 'restart-redis',
                                        'label': 'Reiniciar o pod do Redis',
                                        'label_en': 'Restart Redis StatefulSet pod'},
                                      { 'command': 'kubectl set env deployment/sre-rag-api ENABLE_CACHE=false',
                                        'correct': False,
                                        'explanation': '❌ Transfere todo o tráfego de leitura para o banco relacional, '
                                                       'sobrecarregando o PostgreSQL e gerando um incidente cascata '
                                                       'ainda pior.',
                                        'explanation_en': '❌ Transfers all read load to PostgreSQL, inducing a cascade '
                                                          'database collapse.',
                                        'id': 'disable-cache',
                                        'label': 'Desativar o Redis e fazer todas as queries diretamente no PostgreSQL',
                                        'label_en': 'Disable Redis cache completely and query PostgreSQL directly'}],
                       'symptoms': [ 'Redis INFO: connected_clients = 10000 (maxclients atingido)',
                                     'App logs: redis.exceptions.ConnectionError: Too many connections',
                                     'Muitas conexões em estado CLOSE_WAIT nos pods da API',
                                     'Latência de consulta subiu de 20ms para 5000ms (timeout)'],
                       'symptoms_en': [ 'Redis logs: ERR max number of clients reached (10000/10000)',
                                        'Application logs: redis.exceptions.ConnectionError: Too many connections',
                                        'TCP connections in CLOSE_WAIT state accumulating on API pods',
                                        'Cache latency spiking from 1ms to 5000ms (timeout)'],
                       'title': 'Redis Connection Exhaustion (maxclients 10k)',
                       'title_en': 'Redis Connection Pool Exhaustion'},
  'split-brain-partition': { 'category': 'Rede',
                             'category_en': 'Network',
                             'chaos_action': None,
                             'command': 'kubectl rollout restart daemonset/calico-node -n kube-system',
                             'concepts': { 'architecture_components': [ 'Calico Felix / BIRD BGP',
                                                                        'Overlay Network (VXLAN/IPIP)',
                                                                        'Envoy Proxy mTLS Handshake'],
                                           'best_practices': [ 'Separe o tráfego de controle do CNI e do etcd em redes '
                                                               'físicas dedicadas ou VLANs priorizadas.',
                                                               'Monitore ativamente o status de peering BGP com '
                                                               'alertas de severidade crítica.',
                                                               'Utilize health checks rigorosos nos DaemonSets de rede '
                                                               'para que o Kubelet reinicie agentes travados '
                                                               'prontamente.'],
                                           'best_practices_en': [ 'Monitor CNI agent daemonset health (`cilium-health` '
                                                                  'or `calicoctl node status`) on every node.',
                                                                  'Ensure cloud security groups allow bidirectional '
                                                                  'CNI tunnel traffic (UDP 4789/8472, BGP 179) between '
                                                                  'all worker nodes.',
                                                                  'Deploy synthetic full-mesh network connectivity '
                                                                  'probes (e.g. k8s-netperf) to detect routing '
                                                                  'blackholes.'],
                                           'category_en': 'Network',
                                           'golden_signals': [ 'Estado dos BGP Peers (BGP Peering Up/Down Count)',
                                                               'Perda de Pacotes Inter-Node (Cross-Node Packet Drop '
                                                               'Rate %)'],
                                           'golden_signals_en': [ 'Cross-Node Packet Drop Rate %',
                                                                  'CNI Peer Mesh Connectivity Status'],
                                           'how_it_works': 'O CNI é responsável por atribuir IPs aos Pods e programar '
                                                           'a tabela de roteamento do kernel Linux (via BGP, VXLAN ou '
                                                           'eBPF). Em clusters multi-nó, cada nó atua como um BGP peer '
                                                           'anunciando seus blocos de IPs de pods (/26) para os outros '
                                                           'nós. Se o daemon CNI trava em um nó, os outros nós perdem '
                                                           'a rota para aqueles pods. Requisições entre nós sofrem '
                                                           'descarte de pacotes, quebrando o handshake criptográfico '
                                                           'mTLS dos proxies Envoy.',
                                           'how_it_works_en': 'CNI plugins (Calico, Cilium, Flannel) establish overlay '
                                                              'or BGP routed networks across cluster worker nodes. If '
                                                              'node-to-node VXLAN (UDP 4789) or WireGuard/mTLS mesh '
                                                              'fails between two availability zones, pods on Node A '
                                                              'cannot route packets to pods on Node B. Mutual TLS '
                                                              'handshakes (Istio/Linkerd) time out, causing '
                                                              'split-brain partitions.',
                                           'resource_title': 'Kubernetes CNI (Container Network Interface), BGP Mesh & '
                                                             'Service Mesh mTLS',
                                           'resource_title_en': 'Kubernetes CNI (Container Network Interface), BGP '
                                                                'Mesh & Service Mesh mTLS'},
                             'description': 'Comunicação entre a API no nó worker-1 e o PostgreSQL no nó worker-2 '
                                            "falha intermitentemente com 'Connection reset by peer' e falhas de mTLS "
                                            'no sidecar Envoy. O DaemonSet do Calico CNI travou no worker-2, deixando '
                                            'tabelas de rotas BGP dessincronizadas.',
                             'description_en': "Inter-node pod communication failing with 'Connection reset by peer' "
                                               'and mTLS handshake timeouts due to desynchronized Calico BGP mesh.',
                             'detection_delay_seconds': 45,
                             'difficulty': 'extreme',
                             'hints': [ { 'hint': 'Inspecione os pods do CNI daemonset no namespace kube-system.',
                                          'hint_en': 'Inspect CNI daemonset pods in the kube-system namespace.'},
                                        { 'hint': 'Reinicie o daemonset do CNI com kubectl rollout restart daemonset.',
                                          'hint_en': 'Restart CNI daemonset using kubectl rollout restart daemonset.'}],
                             'icon': '⚡',
                             'id': 'split-brain-partition',
                             'investigation_delay_seconds': 95,
                             'runbook': '/docs/runbooks/split-brain-partition',
                             'runbook_steps': { 'diagnosis': [ 'kubectl get pods -n kube-system -l k8s-app=calico-node '
                                                               '-o wide (Pod no worker-2 com restarts anormais).',
                                                               'kubectl exec -n kube-system daemonset/calico-node -- '
                                                               'calicoctl node status (Peer 10.0.1.20 state: Idle / '
                                                               'Non-established).',
                                                               'Traceroute inter-node identificando descarte de '
                                                               'pacotes no túnel VXLAN/IPIP.'],
                                                'diagnosis_en': [ 'kubectl get pods -n kube-system -l '
                                                                  'k8s-app=canal/calico/cilium (Check CNI daemonset '
                                                                  'status).',
                                                                  'kubectl exec daemonset pod -- calicoctl node status '
                                                                  "(Peer connection to worker-2 shows 'Unreachable' / "
                                                                  "'BGP session down').",
                                                                  'Test node firewall / iptables rules: check if VXLAN '
                                                                  'UDP 4789 is blocked.'],
                                                'mitigation': { 'action': 'Reiniciar o DaemonSet do Calico para forçar '
                                                                          'reconciliação do mesh de rede.',
                                                                'command': 'kubectl rollout restart '
                                                                           'daemonset/calico-node -n kube-system',
                                                                'validation': 'kubectl rollout status '
                                                                              'daemonset/calico-node -n kube-system'},
                                                'mitigation_en': { 'action_en': 'Restart CNI agent pods to '
                                                                                're-establish routing mesh and flush '
                                                                                'stale iptables/eBPF maps.',
                                                                   'command': 'kubectl rollout restart daemonset -n '
                                                                              'kube-system calico-node || kubectl '
                                                                              'rollout restart daemonset -n '
                                                                              'kube-system cilium',
                                                                   'validation_en': 'BGP peer status returns to '
                                                                                    'Established and cross-node ping '
                                                                                    'latency normalizes.'},
                                                'prevention': [ 'Monitorar métricas de saúde da malha CNI '
                                                                '(calico_felix_cluster_num_host_endpoints).',
                                                                'Configurar testes de conectividade contínuos entre '
                                                                'nós com ferramentas como Kube-Ping.'],
                                                'prevention_en': [ 'Implement continuous cross-node network latency '
                                                                   'and connectivity probes.',
                                                                   'Tune node kernel sysctl networking parameters in '
                                                                   'AMI / base OS image.'],
                                                'root_cause': { 'analysis': 'Um jitter transitório de rede causou '
                                                                            'descompasso no BGP peer do Calico e '
                                                                            'travamento do processo felix no nó '
                                                                            'worker-2.',
                                                                'permanent_fix': 'Habilitar BFD (Bidirectional '
                                                                                 'Forwarding Detection) para detecção '
                                                                                 'e convergência de rotas em '
                                                                                 'submilisegundos.'},
                                                'root_cause_en': { 'analysis_en': 'Kernel connection tracking table '
                                                                                  'overflowed on worker node, dropping '
                                                                                  'VXLAN encapsulations.',
                                                                   'permanent_fix_en': 'Increase '
                                                                                       'net.netfilter.nf_conntrack_max '
                                                                                       'sysctl and configure automated '
                                                                                       'CNI node health alerting.'},
                                                'triage': [ 'Alerta CalicoBGPPeerDown e MeshPeerAuthenticationFailed.',
                                                            'Pods no nó 1 não conseguem falar com pods no nó 2 '
                                                            '(latência infinita / timeout).',
                                                            'Logs do Envoy sidecar com falhas constantes de TLS '
                                                            'handshakes.'],
                                                'triage_en': [ 'Check alert: CrossNodeConnectivityPartition.',
                                                               'Inspect inter-service communication: Pods on worker-1 '
                                                               'fail to connect to Pods on worker-2.',
                                                               'Verify curl timeouts between pods across nodes while '
                                                               'intra-node calls succeed.']},
                             'severity': 'SEV-1',
                             'solutions': [ { 'command': 'kubectl rollout restart daemonset/calico-node -n kube-system',
                                              'correct': True,
                                              'explanation': '✅ Correto! Reiniciar o agente CNI restaura as interfaces '
                                                             'virtuais veth, as regras de iptables/eBPF e a malha BGP '
                                                             'entre os nós do cluster.',
                                              'explanation_en': '✅ Correct! Restarting the CNI agent re-establishes '
                                                                'veth interfaces, iptables/eBPF rules, and BGP routing '
                                                                'mesh across worker nodes.',
                                              'id': 'restart-cni',
                                              'label': 'Reiniciar o DaemonSet do CNI (`kubectl rollout restart '
                                                       'daemonset/calico-node -n kube-system`)',
                                              'label_en': 'Restart CNI DaemonSet (`kubectl rollout restart '
                                                          'daemonset/calico-node -n kube-system`)'},
                                            { 'command': 'kubectl patch peerauthentication default -n sre-rag --type '
                                                         'merge -p \'{"spec":{"mtls":{"mode":"DISABLE"}}}\'',
                                              'correct': False,
                                              'explanation': '❌ Violação grave de segurança (Zero Trust). Além disso, '
                                                             'não resolve a falha, pois o problema é de camada de rede '
                                                             'física/roteamento do CNI.',
                                              'explanation_en': '❌ Security violation and ineffective; the underlying '
                                                                'failure is packet routing at CNI layer.',
                                              'id': 'disable-mtls',
                                              'label': 'Desativar criptografia mTLS em todo o cluster',
                                              'label_en': 'Disable mTLS encryption cluster-wide'},
                                            { 'command': 'shutdown -r now',
                                              'correct': False,
                                              'explanation': '❌ Ação desastrosa que causaria queda generalizada e '
                                                             'corrupção de quórum do etcd.',
                                              'explanation_en': '❌ Destructive. Triggers global outage and potential '
                                                                'etcd quorum corruption.',
                                              'id': 'reboot-cluster',
                                              'label': 'Desligar e religar todos os servidores físicos do cluster',
                                              'label_en': 'Power cycle all physical cluster servers'}],
                             'symptoms': [ 'Comunicação cross-node falhando com timeout e resets de conexão TCP',
                                           'Envoy sidecar logs: mTLS handshake failure: downstream connection '
                                           'termination',
                                           'Calico node no worker-2 em status Degradado / BGP peer down',
                                           'Alertmanager: CalicoBGPPeerDown FIRING'],
                             'symptoms_en': [ 'Cross-node pod communication dropping with TCP resets',
                                              'Envoy sidecar logs: mTLS handshake failure: downstream connection '
                                              'termination',
                                              'Calico node daemon on worker-2 degraded / BGP peer down',
                                              'Alertmanager: CalicoBGPPeerDown FIRING'],
                             'title': 'CNI Network Partition & mTLS Handshake Failure',
                             'title_en': 'CNI Network Partition & mTLS Handshake Failure'},
  'tls-expiring': { 'category': 'Segurança',
                    'category_en': 'Security',
                    'chaos_action': None,
                    'command': 'kubectl annotate ingress sre-rag cert-manager.io/cluster-issuer=letsencrypt-prod '
                               '--overwrite',
                    'concepts': { 'architecture_components': [ 'Cert-Manager Controller',
                                                               'ACME HTTP-01 Solver',
                                                               "Let's Encrypt CA"],
                                  'best_practices': [ 'Nunca deixe a renovação para as últimas 48h; configure '
                                                      '`renewBefore: 720h` (30 dias antes).',
                                                      'Sempre utilize ClusterIssuers de staging para testes em '
                                                      "homologação para não atingir o rate limit do Let's Encrypt.",
                                                      'Monitore a validade de certificados usando blackbox exporter do '
                                                      'Prometheus.'],
                                  'best_practices_en': [ 'Trigger renewal alerts at 30 days and 15 days before '
                                                         'expiration; never alert only at 24 hours.',
                                                         'Deploy cert-manager Prometheus metrics '
                                                         '(`certmanager_certificate_expiration_timestamp_seconds`).',
                                                         'Implement staging ACME issuer to test challenge workflows '
                                                         "without hitting Let's Encrypt rate limits."],
                                  'category_en': 'Security',
                                  'golden_signals': [ 'Dias Restantes de Validade TLS (Days Until Expiry)',
                                                      'Taxa de Sucesso de Desafios ACME (ACME Challenge Success Rate)'],
                                  'golden_signals_en': [ 'Days Until TLS Certificate Expiry',
                                                         'Cert-Manager Challenge Failures'],
                                  'how_it_works': 'O cert-manager estende a API do Kubernetes via Custom Resource '
                                                  'Definitions (CRDs). Ao detectar um Ingress anotado, o cert-manager '
                                                  'cria recursos de `Certificate`, `CertificateRequest` e `Order`. '
                                                  "Para validar a posse do domínio junto ao Let's Encrypt, ele cria um "
                                                  'Pod temporário e regras no Ingress para responder o desafio ACME em '
                                                  '`/.well-known/acme-challenge/*`. Após a validação, a CA assina o '
                                                  'certificado que é gravado como Secret TLS.',
                                  'how_it_works_en': 'Cert-manager automates X.509 certificate issuance in Kubernetes. '
                                                     'It watches Certificate resources, initiates ACME HTTP-01 or '
                                                     "DNS-01 challenges with Let's Encrypt, verifies domain control, "
                                                     'and stores the resulting TLS keypair in a Secret. If renewals '
                                                     'fail (e.g. Ingress routing challenge wrong), cert expires, '
                                                     'causing SSL handshake errors.',
                                  'resource_title': 'Infraestrutura de Chaves Públicas (PKI), Cert-Manager & ACME '
                                                    'Challenges',
                                  'resource_title_en': 'Public Key Infrastructure (PKI), Cert-Manager & ACME '
                                                       'Challenges'},
                    'description': 'O certificado TLS do Ingress expira em menos de 48 horas. A renovação automática '
                                   'pelo cert-manager falhou devido a falta de anotação do ClusterIssuer no Ingress.',
                    'description_en': 'Ingress TLS certificate expires in under 48 hours. Cert-manager auto-renewal '
                                      'stalled due to missing ClusterIssuer ingress annotations.',
                    'detection_delay_seconds': 60,
                    'difficulty': 'hard',
                    'hints': [ { 'hint': 'Verifique os certificados gerenciados com kubectl get certificate.',
                                 'hint_en': 'Check managed certificates using kubectl get certificate.'},
                               { 'hint': 'Force a renovação do certificado com cmctl renew ou kubectl patch '
                                         'certificate.',
                                 'hint_en': 'Force certificate renewal with cmctl renew or kubectl patch '
                                            'certificate.'}],
                    'icon': '🔒',
                    'id': 'tls-expiring',
                    'investigation_delay_seconds': 120,
                    'runbook': '/docs/runbooks/tls-expiring',
                    'runbook_steps': { 'diagnosis': [ 'kubectl get cert -n sre-rag (Status: Ready=False, '
                                                      'Secret=sre-rag-tls-cert).',
                                                      'kubectl describe certificate sre-rag-tls-cert (Events: Issuer '
                                                      'letsencrypt-prod not found).',
                                                      'kubectl get ingress sre-rag -o yaml (Falta da anotação '
                                                      'cert-manager.io/cluster-issuer).'],
                                       'diagnosis_en': [ 'kubectl get certificate (Status: Ready: False, Message: '
                                                         'Renewal failed).',
                                                         'kubectl describe certificaterequest (ACME HTTP-01 challenge '
                                                         'pending or failing).',
                                                         'kubectl get challenges (Challenge ingress route failing '
                                                         '404).'],
                                       'mitigation': { 'action': 'Anotar o Ingress para acionar a renovação automática '
                                                                 'pelo cert-manager.',
                                                       'command': 'kubectl annotate ingress sre-rag '
                                                                  'cert-manager.io/cluster-issuer=letsencrypt-prod '
                                                                  '--overwrite',
                                                       'validation': 'kubectl get certificate sre-rag-tls-cert -w '
                                                                     '(Aguardar Ready: True).'},
                                       'mitigation_en': { 'action_en': 'Renew certificate immediately via cert-manager '
                                                                       'CLI or trigger renew annotation.',
                                                          'command': 'cmctl renew sre-rag-tls-cert || kubectl patch '
                                                                     'certificate sre-rag-tls --type=merge -p '
                                                                     '\'{"spec":{"renewBefore":"720h"}}\'',
                                                          'validation_en': 'Certificate secret updates with new expiry '
                                                                           'date 90 days in the future.'},
                                       'prevention': [ 'Alertas proativos com 30, 15 e 7 dias de antecedência para '
                                                       'renovação de TLS.',
                                                       'Monitoramento de métricas do cert-manager '
                                                       '(certmanager_certificate_expiration_timestamp_seconds).'],
                                       'prevention_en': [ 'Monitor cert-manager renewal metrics via Grafana dashboard '
                                                          'with 30d alert threshold.',
                                                          'Automate end-to-end TLS handshake synthetic monitoring.'],
                                       'root_cause': { 'analysis': 'Anotação de cluster-issuer foi omitida durante a '
                                                                   'migração de ingress controllers.',
                                                       'permanent_fix': 'Fixar a anotação no template Helm do Ingress '
                                                                        'nos values padrões.'},
                                       'root_cause_en': { 'analysis_en': 'Ingress controller upgrade wiped the '
                                                                         '.well-known/acme-challenge ingress route.',
                                                          'permanent_fix_en': 'Configure ClusterIssuer with DNS-01 '
                                                                              'challenges via cloud DNS provider for '
                                                                              'robust renewals.'},
                                       'triage': [ 'Alerta TLSCertificateExpiringSoon (< 48 horas restantes).',
                                                   'Dashboard de certificados TLS com status de renovação em erro.',
                                                   'Validação de rota HTTPS acusando expiração iminente.'],
                                       'triage_en': [ 'Check alert: TLSCertificateExpiringSoon (Expires in < 48h).',
                                                      'Verify certificate validity: echo | openssl s_client '
                                                      '-servername api.domain -connect api.domain:443 2>/dev/null | '
                                                      'openssl x509 -noout -dates.',
                                                      'Confirm client browsers warning on expiration.']},
                    'severity': 'SEV-3',
                    'solutions': [ { 'command': 'kubectl annotate ingress sre-rag '
                                                'cert-manager.io/cluster-issuer=letsencrypt-prod --overwrite',
                                     'correct': True,
                                     'explanation': '✅ Correto! O cert-manager detecta a anotação no Ingress, executa '
                                                    'o challenge ACME HTTP-01 e renova o certificado TLS '
                                                    'automaticamente.',
                                     'explanation_en': '✅ Correct! Ingress annotation triggers cert-manager ACME '
                                                       'validation and reissues the TLS certificate.',
                                     'id': 'annotate-ingress',
                                     'label': 'Anotar o Ingress com `cert-manager.io/cluster-issuer=letsencrypt-prod`',
                                     'label_en': 'Annotate Ingress with '
                                                 '`cert-manager.io/cluster-issuer=letsencrypt-prod`'},
                                   { 'command': 'openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem '
                                                '-days 365',
                                     'correct': False,
                                     'explanation': '❌ Inaceitável para produção. Certificados autoassinados provocam '
                                                    'tela de alerta de segurança grave aos usuários finais.',
                                     'explanation_en': '❌ Production violation. Self-signed certificates produce '
                                                       'browser security warnings.',
                                     'id': 'self-signed',
                                     'label': 'Substituir por certificado autoassinado temporário',
                                     'label_en': 'Replace with temporary self-signed certificate'},
                                   { 'command': 'kubectl patch ingress sre-rag --type json -p \'[{"op": "remove", '
                                                '"path": "/spec/tls"}]\'',
                                     'correct': False,
                                     'explanation': '❌ Violação grave de segurança e compliance. Tráfego em texto puro '
                                                    'expõe senhas e dados dos usuários a interceptação.',
                                     'explanation_en': '❌ Severe compliance and security breach.',
                                     'id': 'disable-tls',
                                     'label': 'Desativar TLS e usar apenas HTTP porta 80',
                                     'label_en': 'Disable TLS and run HTTP plain text on port 80'}],
                    'symptoms': [ 'Alertmanager: TLSCertificateExpiringSoon disparado (< 48h)',
                                  'Secret tls-cert não é atualizada há 88 dias',
                                  'Navegadores começarão a exibir aviso de segurança em 48h',
                                  'kubectl get cert: Ready=False (IssuerNotFound)'],
                    'symptoms_en': [ 'Alertmanager: TLSCertificateExpiringSoon firing (< 48h)',
                                     'Secret tls-cert not renewed for 88 days',
                                     'User browsers facing security warning within 48h',
                                     'kubectl get cert: Ready=False (IssuerNotFound)'],
                    'title': 'Certificado TLS Próximo do Vencimento',
                    'title_en': 'TLS Certificate Expiring Soon'}}



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
