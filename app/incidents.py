"""
SRE Incident Simulation Engine
Manages incident scenarios, active simulations, and solution validation with bilingual support (pt / en).
"""
import time
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

# ============================================================
# Scenario Definitions
# ============================================================
SCENARIOS = {
    "high-error-rate": {
        "id": "high-error-rate",
        "title": "High Error Rate (HTTP 500 Spike)",
        "title_en": "High Error Rate (HTTP 500 Spike)",
        "severity": "SEV-1",
        "category": "Disponibilidade",
        "category_en": "Availability",
        "icon": "💥",
        "description": "A taxa de erros HTTP 500 subiu de 0.1% para 45% em menos de 2 minutos. O SLO de disponibilidade está sendo violado. O Alertmanager disparou SLOAvailabilityBurnRateCritical.",
        "description_en": "The HTTP 500 error rate spiked from 0.1% to 45% in under 2 minutes. The availability SLO is currently violated. Alertmanager triggered SLOAvailabilityBurnRateCritical.",
        "symptoms": [
            "Burn rate > 14.4x na janela de 1 hora",
            "Alertmanager: SLOAvailabilityBurnRateCritical FIRING",
            "Grafana: SLO gauge em vermelho (< 99.9%)",
            "HTTP 500 em todos os endpoints da API",
        ],
        "symptoms_en": [
            "Burn rate > 14.4x in the 1-hour window",
            "Alertmanager: SLOAvailabilityBurnRateCritical FIRING",
            "Grafana: SLO gauge in red (< 99.9%)",
            "HTTP 500 across all API endpoints",
        ],
        "solutions": [
            {
                "id": "rollback",
                "label": "Executar rollback do Helm release (`helm rollback sre-rag`)",
                "label_en": "Perform Helm release rollback (`helm rollback sre-rag`)",
                "correct": True,
                "explanation": "✅ Correto! O deploy mais recente introduziu um bug. O rollback restaura a versão anterior estável imediatamente, sendo a ação mais rápida para reduzir o MTTR.",
                "explanation_en": "✅ Correct! The latest deployment introduced a breaking bug. Rollback immediately restores the previous stable version, providing the fastest MTTR reduction.",
            },
            {
                "id": "scale-hpa",
                "label": "Escalar o HPA para mais réplicas (aumentar maxReplicas)",
                "label_en": "Scale HPA to more replicas (increase maxReplicas)",
                "correct": False,
                "explanation": "❌ Incorreto. Mais réplicas não resolvem um bug de código — cada nova réplica também retornaria 500. Isso apenas aumenta o custo sem mitigar o incidente.",
                "explanation_en": "❌ Incorrect. Scaling replicas does not fix a software defect — every new replica will also return 500. It merely increases costs without mitigating the incident.",
            },
            {
                "id": "restart-coredns",
                "label": "Reiniciar os pods do CoreDNS no cluster",
                "label_en": "Restart CoreDNS pods in the cluster",
                "correct": False,
                "explanation": "❌ Incorreto. O DNS está funcionando normalmente. Os erros 500 são gerados pela aplicação, não por falha de resolução de nomes.",
                "explanation_en": "❌ Incorrect. DNS resolution is working properly. The 500 errors originate from application logic, not name resolution failures.",
            },
        ],
        "runbook": "/docs/runbooks/high-error-rate",
        "detection_delay_seconds": 35,
        "investigation_delay_seconds": 85,
        "chaos_action": "simulate_500",
    },
    "high-latency": {
        "id": "high-latency",
        "title": "High Latency (P99 > 2s)",
        "title_en": "High Latency (P99 > 2s)",
        "severity": "SEV-2",
        "category": "Latência",
        "category_en": "Latency",
        "icon": "🐢",
        "description": "A latência P99 das requisições subiu para 4.2 segundos. O SLO de latência (99.5% das requests < 500ms) está sendo violado. Usuários relatam lentidão extrema.",
        "description_en": "P99 request latency degraded to 4.2 seconds. The latency SLO (99.5% of requests < 500ms) is violated. Users report severe sluggishness.",
        "symptoms": [
            "P99 latency: 4200ms (SLO target: 500ms)",
            "CPU da API em 95% de utilização",
            "PostgreSQL: slow queries > 2s detectadas",
            "Redis cache hit rate caiu para 12%",
        ],
        "symptoms_en": [
            "P99 latency: 4200ms (SLO target: 500ms)",
            "API Pod CPU utilization at 95%",
            "PostgreSQL: slow queries > 2s detected",
            "Redis cache hit rate dropped to 12%",
        ],
        "solutions": [
            {
                "id": "scale-hpa",
                "label": "Escalar HPA + investigar e otimizar queries lentas no PostgreSQL",
                "label_en": "Scale HPA + investigate and optimize slow queries in PostgreSQL",
                "correct": True,
                "explanation": "✅ Correto! Escalar alivia a pressão de CPU imediatamente (mitiga) enquanto a investigação das slow queries resolve a causa raiz (corrige).",
                "explanation_en": "✅ Correct! Scaling relieves CPU saturation immediately (mitigation) while slow query analysis tackles the root cause (resolution).",
            },
            {
                "id": "rollback",
                "label": "Fazer rollback do último deploy",
                "label_en": "Rollback the last deployment",
                "correct": False,
                "explanation": "❌ Incorreto. A latência é causada por volume de tráfego + queries não otimizadas, não por um bug recente de código. O rollback não resolveria.",
                "explanation_en": "❌ Incorrect. The latency stems from traffic volume and unoptimized queries, not recent code changes. Rollback would not resolve it.",
            },
            {
                "id": "restart-pods",
                "label": "Reiniciar todos os pods da API",
                "label_en": "Restart all API pods",
                "correct": False,
                "explanation": "❌ Ineficaz. Reiniciar gera downtime temporário e cache frio sem resolver a pressão no banco.",
                "explanation_en": "❌ Ineffective. Restarting causes a brief outage and cold cache without resolving database pressure.",
            },
        ],
        "runbook": "/docs/runbooks/high-latency",
        "detection_delay_seconds": 45,
        "investigation_delay_seconds": 90,
        "chaos_action": None,
    },
    "crashloopbackoff": {
        "id": "crashloopbackoff",
        "title": "API CrashLoopBackOff",
        "title_en": "API CrashLoopBackOff",
        "severity": "SEV-1",
        "category": "Confiabilidade",
        "category_en": "Reliability",
        "icon": "🔄",
        "description": "Pods recém-implantados da API falham imediatamente na inicialização e entram em CrashLoopBackOff. As probes de readiness falham e nenhuma request é atendida.",
        "description_en": "Newly deployed API pods fail immediately upon startup and enter CrashLoopBackOff. Readiness probes fail and zero traffic is served.",
        "symptoms": [
            "kubectl get pods: sre-rag-api-* CrashLoopBackOff (restarts: 8)",
            "kubectl logs: KeyError: 'EMBEDDING_BATCH_SIZE' não encontrada no ambiente",
            "Zero endpoints no Service (Endpoints: <none>)",
            "HTTP 502 Bad Gateway no Ingress",
        ],
        "symptoms_en": [
            "kubectl get pods: sre-rag-api-* CrashLoopBackOff (restarts: 8)",
            "kubectl logs: KeyError: 'EMBEDDING_BATCH_SIZE' missing in environment",
            "Zero endpoints ready in Service (Endpoints: <none>)",
            "HTTP 502 Bad Gateway at ingress level",
        ],
        "solutions": [
            {
                "id": "fix-configmap",
                "label": "Adicionar EMBEDDING_BATCH_SIZE no ConfigMap/values e aplicar via Helm",
                "label_en": "Inject missing EMBEDDING_BATCH_SIZE in ConfigMap/values and redeploy",
                "correct": True,
                "explanation": "✅ Correto! A variável obrigatória ausente no ConfigMap impedia a inicialização da aplicação. Adicioná-la resolve a causa raiz imediatamente.",
                "explanation_en": "✅ Correct! Supplying the mandatory configuration variable satisfies startup validation and allows pods to enter Ready state.",
            },
            {
                "id": "rollback",
                "label": "Rollback imediato para a versão anterior via Helm",
                "label_en": "Immediate rollback to previous release tag via Helm",
                "correct": False,
                "explanation": "⚠️ Parcialmente aceitável como mitigação de emergência, mas corrigir a variável faltante no Helm values é mais rápido e preserva as novas features.",
                "explanation_en": "⚠️ Acceptable emergency workaround, but fixing the missing configuration parameter in Helm values addresses the real issue with zero delay.",
            },
            {
                "id": "disable-probes",
                "label": "Desativar livenessProbe e readinessProbe no deployment",
                "label_en": "Disable readiness and liveness probes in deployment spec",
                "correct": False,
                "explanation": "❌ Anti-pattern grave! Desativar probes faria o Kubernetes enviar tráfego para pods que estão crashando, piorando a experiência do usuário.",
                "explanation_en": "❌ Severe anti-pattern! Disabling probes routes traffic to crashing pods, exacerbating downstream customer impact.",
            },
        ],
        "runbook": "/docs/runbooks/crashloopbackoff",
        "detection_delay_seconds": 20,
        "investigation_delay_seconds": 60,
        "chaos_action": None,
    },
    "tls-expiring": {
        "id": "tls-expiring",
        "title": "Certificado TLS Próximo do Vencimento",
        "title_en": "TLS Certificate Expiring Soon",
        "severity": "SEV-3",
        "category": "Segurança",
        "category_en": "Security",
        "icon": "🔒",
        "description": "O certificado TLS do Ingress expira em menos de 48 horas. A renovação automática pelo cert-manager falhou devido a erro de validação do desafio ACME HTTP-01.",
        "description_en": "The ingress TLS certificate expires in under 48 hours. Cert-manager failed auto-renewal due to invalid ACME HTTP-01 challenge ingress routing.",
        "symptoms": [
            "Alertmanager: TLSCertificateExpiringSoon disparado (< 48h)",
            "Cert-manager logs: 404 Not Found no /.well-known/acme-challenge/*",
            "Navegadores começarão a exibir aviso de segurança em 48h",
            "Secret tls-cert não é atualizada há 88 dias",
        ],
        "symptoms_en": [
            "Alertmanager: TLSCertificateExpiringSoon firing (< 48h)",
            "Cert-manager logs: Error 404 on /.well-known/acme-challenge/*",
            "Client browsers displaying certificate expiration warnings",
            "Ingress secret tls-cert not updated for 88 days",
        ],
        "solutions": [
            {
                "id": "fix-acme-ingress",
                "label": "Corrigir rota do Ingress para o solver do cert-manager e forçar renovação",
                "label_en": "Fix ACME HTTP-01 ingress path + force certificate renewal",
                "correct": True,
                "explanation": "✅ Correto! O Ingress estava interceptando a rota de validação do ACME. Corrigir o roteamento permite que o Let's Encrypt renove o certificado com sucesso.",
                "explanation_en": "✅ Correct! Allowing ACME challenge routing permits Let's Encrypt validation and completes certificate renewal before expiration.",
            },
            {
                "id": "self-signed",
                "label": "Gerar certificado autoassinado temporário e substituir o secret",
                "label_en": "Generate temporary self-signed certificate and replace secret",
                "correct": False,
                "explanation": "❌ Inaceitável para produção. Certificados autoassinados causam erros de segurança graves para os usuários finais no navegador.",
                "explanation_en": "❌ Unacceptable for production. Causes browser security warnings and breaks HTTPS client trust.",
            },
            {
                "id": "disable-tls",
                "label": "Remover TLS do Ingress e operar apenas com HTTP na porta 80",
                "label_en": "Downgrade ingress to plaintext HTTP on port 80",
                "correct": False,
                "explanation": "❌ Violação grave de segurança. Tráfego não criptografado expõe dados de usuários a interceptação.",
                "explanation_en": "❌ Major security violation! Transmitting production traffic unencrypted is unacceptable.",
            },
        ],
        "runbook": "/docs/runbooks/tls-expiring",
        "detection_delay_seconds": 60,
        "investigation_delay_seconds": 120,
        "chaos_action": None,
    },
    "disk-pressure": {
        "id": "disk-pressure",
        "title": "DiskPressure em Node do Kubernetes",
        "severity": "SEV-2",
        "category": "Armazenamento",
        "category_en": "Storage",
        "icon": "💾",
        "description": "Um nó do cluster entrou em estado DiskPressure (> 85% de uso no disco raiz). O kubelet começou a evictar pods não críticos para proteger o sistema.",
        "description_en": "Worker node entered DiskPressure condition (root disk > 85%). Kubelet started evicting pods according to eviction threshold policies.",
        "symptoms": [
            "kubectl get nodes: Status = Ready,DiskPressure",
            "Kubelet: eviction manager threshold met on /var/lib/docker",
            "Pods secundários sendo evictados (Evicted); novos pods Pending",
            "Disco raiz do nó atingiu 88% de utilização",
        ],
        "symptoms_en": [
            "kubectl get nodes: Status = Ready,DiskPressure",
            "Eviction thresholds exceeded on /var/lib/docker or /var/lib/kubelet",
            "Non-critical batch pods evicted; pending pods accumulating",
            "Node filesystem utilization at 92%",
        ],
        "solutions": [
            {
                "id": "prune-images-logs",
                "label": "Executar crictl rmi --prune para remover imagens antigas + rotacionar logs",
                "label_en": "Purge dead container images via crictl rmi --prune + rotate node log files",
                "correct": True,
                "explanation": "✅ Correto! Limpar imagens de containers obsoletas e rotacionar logs de pods libera espaço imediatamente, removendo a condição DiskPressure do nó.",
                "explanation_en": "✅ Correct! Cleaning stale container images and rotating logs recovers disk space immediately and clears the DiskPressure taint.",
            },
            {
                "id": "delete-node",
                "label": "Deletar o nó do cluster imediatamente (`kubectl delete node`)",
                "label_en": "Drain and terminate the Kubernetes node immediately",
                "correct": False,
                "explanation": "⚠️ Drástico demais. A limpeza de disco é rápida e resolve o problema sem necessidade de reconfiguração de infraestrutura.",
                "explanation_en": "⚠️ Excessive for a simple disk cleanup. Can trigger cluster rescheduling pressure unnecessarily.",
            },
            {
                "id": "ignore-taint",
                "label": "Adicionar tolerations para DiskPressure em todos os pods",
                "label_en": "Add tolerations for DiskPressure on all application pods",
                "correct": False,
                "explanation": "❌ Perigoso. Se o disco atingir 100%, o nó inteiro trava e pode corromper o filesystem do sistema operacional.",
                "explanation_en": "❌ Dangerous. If the disk fills to 100%, the node kernel freezes and crashes, causing unrecoverable data loss.",
            },
        ],
        "runbook": "/docs/runbooks/disk-pressure",
        "detection_delay_seconds": 50,
        "investigation_delay_seconds": 100,
        "chaos_action": None,
    },
    "redis-exhausted": {
        "id": "redis-exhausted",
        "title": "Redis Connection Exhaustion",
        "title_en": "Redis Connection Pool Exhaustion",
        "severity": "SEV-1",
        "category": "Desempenho",
        "category_en": "Performance",
        "icon": "🔴",
        "description": "O Redis atingiu o limite de maxclients (10.000 conexões). Novas conexões da API falham com 'ERR max number of clients reached'. Consultas ao RAG falham por timeout de cache.",
        "description_en": "Redis maxclients limit reached (10,000 connections). Application threads hanging on connection timeouts, escalating response latency across all endpoints.",
        "symptoms": [
            "Redis INFO: connected_clients = 10000 (maxclients atingido)",
            "App logs: redis.exceptions.ConnectionError: Too many connections",
            "Muitas conexões em estado CLOSE_WAIT nos pods da API",
            "Latência de consulta subiu de 20ms para 5000ms (timeout)",
        ],
        "symptoms_en": [
            "Redis logs: ERR max number of clients reached (10000/10000)",
            "Application logs: redis.exceptions.ConnectionError: Too many connections",
            "TCP connections in CLOSE_WAIT state accumulating on API pods",
            "Cache latency spiking from 1ms to 5000ms (timeout)",
        ],
        "solutions": [
            {
                "id": "fix-connection-pool",
                "label": "Configurar ConnectionPool no cliente Redis com max_connections e timeout",
                "label_en": "Configure connection pool limits on API + enable Redis timeout idle clients",
                "correct": True,
                "explanation": "✅ Correto! A aplicação criava uma nova conexão por request sem pool. O ConnectionPool reutiliza conexões e limita o número máximo, eliminando o vazamento.",
                "explanation_en": "✅ Correct! Reusing connections with a bounded pool and timing out idle clients mitigates leak and keeps connection count well within safe thresholds.",
            },
            {
                "id": "restart-redis",
                "label": "Reiniciar o pod do Redis",
                "label_en": "Restart Redis StatefulSet pod",
                "correct": False,
                "explanation": "⚠️ Mitigação temporária. Reiniciar derruba as 10k conexões, mas a aplicação vai esgotá-las novamente em poucos minutos.",
                "explanation_en": "⚠️ Temporarily drops connections, but the leak will exhaust connections again within minutes.",
            },
            {
                "id": "disable-cache",
                "label": "Desativar o Redis e fazer todas as queries diretamente no PostgreSQL",
                "label_en": "Disable Redis cache completely and query PostgreSQL directly",
                "correct": False,
                "explanation": "❌ Transfere todo o tráfego para o banco relacional, sobrecarregando o PostgreSQL e gerando um incidente cascata ainda pior.",
                "explanation_en": "❌ Transfers all read load to PostgreSQL, inducing a cascade database collapse.",
            },
        ],
        "runbook": "/docs/runbooks/redis-exhausted",
        "detection_delay_seconds": 40,
        "investigation_delay_seconds": 80,
        "chaos_action": None,
    },
    "oom-kill": {
        "id": "oom-kill",
        "title": "OOM Kill em Pod da API",
        "title_en": "API Pod OOM Kill",
        "severity": "SEV-1",
        "category": "Recursos",
        "category_en": "Resources",
        "icon": "💀",
        "description": "O pod da API está sendo terminado pelo OOM Killer do kernel. Consumo de memória excedeu o limit configurado. Pods reiniciando constantemente sob carga.",
        "description_en": "API pod terminated by Linux kernel OOM Killer. Memory consumption exceeded the configured limit under peak workload.",
        "symptoms": [
            "kubectl describe pod: Reason = OOMKilled",
            "Last State: Terminated with exit code 137",
            "Memory usage: 512Mi/512Mi (100% do limit)",
            "Restarts aumentando progressivamente sob carga",
        ],
        "symptoms_en": [
            "kubectl describe pod: Reason = OOMKilled (exit code 137)",
            "Memory usage: 512Mi/512Mi (100% of configured limit)",
            "Repeated pod restarts under production traffic load",
            "Grafana container memory usage graph showing sharp linear ascent",
        ],
        "solutions": [
            {
                "id": "increase-memory",
                "label": "Aumentar `resources.limits.memory` no Helm values + investigar memory leak",
                "label_en": "Increase resources.limits.memory in Helm values + profile memory leak",
                "correct": True,
                "explanation": "✅ Correto! Aumentar o limit imediatamente mitiga o OOM Kill. Em paralelo, investigar se há memory leak na aplicação (profiling) resolve a causa raiz.",
                "explanation_en": "✅ Correct! Raising the memory limit immediately stabilizes the service while memory profiling addresses root cause leaks.",
            },
            {
                "id": "rollback",
                "label": "Fazer rollback para a versão anterior",
                "label_en": "Rollback to previous release tag",
                "correct": False,
                "explanation": "❌ Pode não resolver. Se o problema é crescimento de tráfego, a versão anterior também sofreria OOM. Verificar se é leak de código novo antes de decidir.",
                "explanation_en": "❌ If memory pressure is traffic-driven, the previous version will also OOM. Profile first before rollback.",
            },
            {
                "id": "hpa-scale",
                "label": "Escalar mais réplicas via HPA",
                "label_en": "Scale more replicas via HPA",
                "correct": False,
                "explanation": "❌ Incorreto. Mais réplicas com o mesmo limit vão sofrer OOM igualmente. O problema é o limit de memória insuficiente, não a quantidade de pods.",
                "explanation_en": "❌ Replicas sharing the same insufficient memory limit will all crash in parallel under load.",
            },
        ],
        "runbook": "/docs/runbooks/oom-kill",
        "detection_delay_seconds": 25,
        "investigation_delay_seconds": 70,
        "chaos_action": None,
    },
    "dns-failure": {
        "id": "dns-failure",
        "title": "DNS Resolution Failure",
        "title_en": "DNS Resolution Failure",
        "severity": "SEV-1",
        "category": "Rede",
        "category_en": "Network",
        "icon": "🌐",
        "description": "A aplicação não consegue resolver nomes de serviços internos. Conexões com PostgreSQL e Redis falhando por timeout. NetworkPolicy pode estar bloqueando o tráfego DNS.",
        "description_en": "The application cannot resolve internal Kubernetes service names. Connections to PostgreSQL and Redis timing out due to CoreDNS degradation.",
        "symptoms": [
            "App logs: socket.gaierror: [Errno -2] Name or service not known",
            "nslookup postgresql.sre-rag.svc.cluster.local: SERVFAIL",
            "CoreDNS pods em estado de alta utilização de CPU",
            "NetworkPolicy pode estar bloqueando porta 53/UDP",
        ],
        "symptoms_en": [
            "App logs: socket.gaierror: [Errno -2] Name or service not known",
            "nslookup postgresql.sre-rag.svc.cluster.local: SERVFAIL",
            "CoreDNS pods showing elevated CPU and dropped UDP packets",
            "NetworkPolicy potentially blocking port 53/UDP",
        ],
        "solutions": [
            {
                "id": "coredns-netpol",
                "label": "Reiniciar CoreDNS pods + validar NetworkPolicy (permitir porta 53/UDP)",
                "label_en": "Restart CoreDNS pods + verify NetworkPolicy allows egress port 53/UDP",
                "correct": True,
                "explanation": "✅ Correto! Reiniciar o CoreDNS resolve falhas transitórias. Verificar a NetworkPolicy para garantir que a porta 53 (UDP/TCP) está liberada para o namespace.",
                "explanation_en": "✅ Correct! Restarts stale CoreDNS pods and confirms NetworkPolicy does not drop DNS traffic on port 53.",
            },
            {
                "id": "restart-app",
                "label": "Reiniciar todos os pods da aplicação",
                "label_en": "Restart all application pods",
                "correct": False,
                "explanation": "❌ Incorreto. Reiniciar a aplicação não resolve falha no DNS. Os pods reiniciados tentarão resolver o mesmo nome e falharão igualmente.",
                "explanation_en": "❌ Ineffective. The root cause is cluster DNS; restarting application pods will just fail DNS resolution again.",
            },
            {
                "id": "use-ip",
                "label": "Substituir nomes de serviço por IPs estáticos nos ConfigMaps",
                "label_en": "Replace service hostnames with static cluster IPs",
                "correct": False,
                "explanation": "❌ Perigoso e anti-pattern. IPs de pods/serviços no Kubernetes são dinâmicos. Usar IPs fixos causa falhas assim que os serviços são recriados.",
                "explanation_en": "❌ Severe Kubernetes anti-pattern! Service and pod IPs are ephemeral and change upon recreation.",
            },
        ],
        "runbook": "/docs/runbooks/dns-failure",
        "detection_delay_seconds": 30,
        "investigation_delay_seconds": 75,
        "chaos_action": None,
    },
}


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


class ActiveSimulation(BaseModel):
    scenario_id: str
    started_at: float
    phase: str  # "running" | "detected" | "investigating" | "solved"
    chaos_active: bool


# ============================================================
# Simulation Engine
# ============================================================
class IncidentSimulationEngine:
    def __init__(self):
        self.active: Optional[ActiveSimulation] = None
        self.history: list[SimulationResult] = []
        self._counter = 1

    def start(self, scenario_id: str) -> dict:
        if scenario_id not in SCENARIOS:
            return {"error": f"Scenario '{scenario_id}' not found"}

        self.active = ActiveSimulation(
            scenario_id=scenario_id,
            started_at=time.time(),
            phase="running",
            chaos_active=SCENARIOS[scenario_id].get("chaos_action") == "simulate_500",
        )
        return {"status": "started", "scenario_id": scenario_id, "started_at": self.active.started_at}

    def get_active_state(self) -> Optional[dict]:
        if not self.active:
            return None

        scenario = SCENARIOS[self.active.scenario_id]
        elapsed = time.time() - self.active.started_at

        # Advance phase based on elapsed time
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
        }

    def solve(self, scenario_id: str, solution_id: str) -> dict:
        if not self.active or self.active.scenario_id != scenario_id:
            return {"error": "No matching active simulation"}

        scenario = SCENARIOS[scenario_id]
        solution = next((s for s in scenario["solutions"] if s["id"] == solution_id), None)
        if not solution:
            return {"error": "Invalid solution"}

        elapsed = time.time() - self.active.started_at
        mttd = scenario["detection_delay_seconds"]

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
