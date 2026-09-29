"""
SRE Incident Simulation Engine
Manages incident scenarios, active simulations, and solution validation.
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
        "severity": "SEV-1",
        "category": "Availability",
        "icon": "💥",
        "description": "A taxa de erros HTTP 500 subiu de 0.1% para 45% em menos de 2 minutos. O SLO de disponibilidade está sendo violado. O Alertmanager disparou SLOAvailabilityBurnRateCritical.",
        "symptoms": [
            "Burn rate > 14.4x na janela de 1 hora",
            "Alertmanager: SLOAvailabilityBurnRateCritical FIRING",
            "Grafana: SLO gauge em vermelho (< 99.9%)",
            "HTTP 500 em todos os endpoints da API",
        ],
        "solutions": [
            {
                "id": "rollback",
                "label": "Executar rollback do Helm release (`helm rollback sre-rag`)",
                "correct": True,
                "explanation": "✅ Correto! O deploy mais recente introduziu um bug. O rollback restaura a versão anterior estável imediatamente, sendo a ação mais rápida para reduzir o MTTR.",
            },
            {
                "id": "scale-hpa",
                "label": "Escalar o HPA para mais réplicas (aumentar maxReplicas)",
                "correct": False,
                "explanation": "❌ Incorreto. Mais réplicas não resolvem um bug de código — cada nova réplica também retornaria 500. Isso apenas aumenta o custo sem mitigar o incidente.",
            },
            {
                "id": "restart-coredns",
                "label": "Reiniciar os pods do CoreDNS no cluster",
                "correct": False,
                "explanation": "❌ Incorreto. O DNS está funcionando normalmente. Os erros 500 são gerados pela aplicação, não por falha de resolução de nomes.",
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
        "severity": "SEV-2",
        "category": "Latency",
        "icon": "🐢",
        "description": "A latência P99 das requisições subiu para 4.2 segundos. O SLO de latência (99.5% das requests < 500ms) está sendo violado. Usuários relatam lentidão extrema.",
        "symptoms": [
            "P99 latency: 4200ms (SLO target: 500ms)",
            "CPU da API em 95% de utilização",
            "PostgreSQL: slow queries > 2s detectadas",
            "Redis cache hit rate caiu para 12%",
        ],
        "solutions": [
            {
                "id": "scale-hpa",
                "label": "Escalar HPA + investigar e otimizar queries lentas no PostgreSQL",
                "correct": True,
                "explanation": "✅ Correto! Escalar alivia a pressão de CPU imediatamente (mitiga) enquanto a investigação das slow queries resolve a causa raiz (corrige).",
            },
            {
                "id": "rollback",
                "label": "Fazer rollback do último deploy",
                "correct": False,
                "explanation": "❌ Incorreto. A latência é causada por volume de tráfego + queries não otimizadas, não por um bug recente de código. O rollback não resolveria.",
            },
            {
                "id": "restart-pods",
                "label": "Reiniciar todos os pods da API",
                "correct": False,
                "explanation": "❌ Incorreto. Reiniciar pods causaria downtime adicional. O problema está na camada de banco de dados e capacidade, não no estado dos pods.",
            },
        ],
        "runbook": "/docs/runbooks/high-latency",
        "detection_delay_seconds": 60,
        "investigation_delay_seconds": 120,
        "chaos_action": None,
    },
    "crashloopbackoff": {
        "id": "crashloopbackoff",
        "title": "Pod CrashLoopBackOff",
        "severity": "SEV-1",
        "category": "Reliability",
        "icon": "🔄",
        "description": "O pod da API está em CrashLoopBackOff após o último deploy. O Kubernetes tenta reiniciar o pod repetidamente sem sucesso. Serviço completamente indisponível.",
        "symptoms": [
            "kubectl get pods: STATUS = CrashLoopBackOff",
            "RESTARTS > 5 em menos de 10 minutos",
            "kubectl logs: KeyError: 'DATABASE_URL' — variável de ambiente ausente",
            "Readiness probe falhando — pod removido do Service",
        ],
        "solutions": [
            {
                "id": "fix-configmap",
                "label": "Verificar logs (`kubectl logs`), corrigir o ConfigMap/Secret com a variável faltante",
                "correct": True,
                "explanation": "✅ Correto! Os logs revelam a causa exata: variável de ambiente ausente. Corrigir o ConfigMap e fazer um novo rollout resolve o CrashLoop.",
            },
            {
                "id": "delete-pod",
                "label": "Deletar o pod manualmente para forçar recriação",
                "correct": False,
                "explanation": "❌ Incorreto. Deletar o pod não resolve — o Kubernetes irá recriar o pod com a mesma configuração defeituosa, mantendo o CrashLoop.",
            },
            {
                "id": "increase-memory",
                "label": "Aumentar os limits de memória no Deployment",
                "correct": False,
                "explanation": "❌ Incorreto. O crash é causado por configuração ausente (KeyError), não por OOM. Aumentar memória não afeta o problema.",
            },
        ],
        "runbook": "/docs/runbooks/high-error-rate",
        "detection_delay_seconds": 20,
        "investigation_delay_seconds": 60,
        "chaos_action": None,
    },
    "tls-expiring": {
        "id": "tls-expiring",
        "title": "Certificado TLS Expirando",
        "severity": "SEV-3",
        "category": "Security",
        "icon": "🔒",
        "description": "O certificado TLS do Ingress expira em 48 horas. Browsers já exibem aviso de segurança. Se não renovado, os usuários verão erro de conexão insegura.",
        "symptoms": [
            "Alerta: CertificateExpiringSoon (cert-manager)",
            "Certificate valid until: 48h",
            "Browser: NET::ERR_CERT_DATE_INVALID",
            "kubectl describe certificate: Status = False",
        ],
        "solutions": [
            {
                "id": "renew-cert",
                "label": "Forçar renovação do cert-manager: `kubectl annotate cert sre-rag-tls cert-manager.io/issuer-kind=ClusterIssuer`",
                "correct": True,
                "explanation": "✅ Correto! Forçar a renovação via annotation aciona o cert-manager para requisitar um novo certificado ao Let's Encrypt imediatamente.",
            },
            {
                "id": "restart-ingress",
                "label": "Reiniciar o Ingress Controller (nginx)",
                "correct": False,
                "explanation": "❌ Incorreto. Reiniciar o Ingress Controller não renova certificados — ele apenas recarrega a configuração existente com o cert expirado.",
            },
            {
                "id": "delete-secret",
                "label": "Deletar o Secret TLS para forçar recriação manual",
                "correct": False,
                "explanation": "❌ Incorreto. Deletar o Secret causa downtime imediato do HTTPS. O cert-manager pode recriar, mas o processo correto é via annotation de renovação.",
            },
        ],
        "runbook": "/docs",
        "detection_delay_seconds": 45,
        "investigation_delay_seconds": 90,
        "chaos_action": None,
    },
    "disk-pressure": {
        "id": "disk-pressure",
        "title": "Disk Pressure no Node",
        "severity": "SEV-2",
        "category": "Capacity",
        "icon": "💾",
        "description": "Um node do cluster está com DiskPressure. O kubelet começou a evictar pods para liberar espaço. Logs e imagens antigas acumuladas preenchem o disco.",
        "symptoms": [
            "kubectl describe node: Conditions = DiskPressure True",
            "Pods sendo evictados com reason: Evicted",
            "Node disk usage: 94% (threshold: 85%)",
            "Novos pods ficam em Pending no node afetado",
        ],
        "solutions": [
            {
                "id": "clean-drain",
                "label": "Limpar imagens/logs + `kubectl cordon` + `kubectl drain` para migrar pods",
                "correct": True,
                "explanation": "✅ Correto! Cordon impede novos pods no node. Drain migra os existentes. Limpeza de imagens não utilizadas (`docker system prune`) libera espaço imediatamente.",
            },
            {
                "id": "restart-node",
                "label": "Reiniciar o node via cloud provider",
                "correct": False,
                "explanation": "❌ Incorreto. Reiniciar sem limpeza apenas reinicia com o mesmo disco cheio. Pode causar downtime adicional durante o restart.",
            },
            {
                "id": "scale-cluster",
                "label": "Adicionar um novo node ao cluster imediatamente",
                "correct": False,
                "explanation": "❌ Parcialmente correto para urgência, mas não resolve o node atual com pressão. A ação correta combina cordon/drain com limpeza.",
            },
        ],
        "runbook": "/docs",
        "detection_delay_seconds": 50,
        "investigation_delay_seconds": 100,
        "chaos_action": None,
    },
    "redis-exhausted": {
        "id": "redis-exhausted",
        "title": "Redis Connection Pool Esgotado",
        "severity": "SEV-2",
        "category": "Saturation",
        "icon": "🔴",
        "description": "O Redis atingiu o limite de conexões simultâneas. A aplicação não consegue mais abrir novas conexões. Latência aumentando e timeouts sendo retornados.",
        "symptoms": [
            "Redis error: ERR max number of clients reached",
            "App logs: redis.exceptions.ConnectionError: Too many connections",
            "Connected clients: 500/500 (100%)",
            "Cache hit rate: 0% (conexões falhando)",
        ],
        "solutions": [
            {
                "id": "pool-config",
                "label": "Aumentar `maxclients` no Redis + revisar pool size na aplicação",
                "correct": True,
                "explanation": "✅ Correto! Aumentar maxclients no Redis config e ajustar o pool_size da aplicação para limitar conexões por instância resolve o esgotamento.",
            },
            {
                "id": "restart-redis",
                "label": "Reiniciar o pod do Redis para liberar conexões",
                "correct": False,
                "explanation": "❌ Perigoso. Reiniciar o Redis causa flush de dados em memória e interrupção do serviço de cache. As conexões voltariam a esgotar rapidamente.",
            },
            {
                "id": "disable-cache",
                "label": "Desabilitar o cache na aplicação temporariamente",
                "correct": False,
                "explanation": "❌ Paliativo. Desabilitar cache aumenta drasticamente a carga no PostgreSQL, podendo causar um incidente cascata de high latency.",
            },
        ],
        "runbook": "/docs",
        "detection_delay_seconds": 40,
        "investigation_delay_seconds": 80,
        "chaos_action": None,
    },
    "oom-kill": {
        "id": "oom-kill",
        "title": "OOM Kill em Pod da API",
        "severity": "SEV-1",
        "category": "Resources",
        "icon": "💀",
        "description": "O pod da API está sendo terminado pelo OOM Killer do kernel. Consumo de memória excedeu o limit configurado. Pods reiniciando constantemente sob carga.",
        "symptoms": [
            "kubectl describe pod: Reason = OOMKilled",
            "Last State: Terminated with exit code 137",
            "Memory usage: 512Mi/512Mi (100% do limit)",
            "Restarts aumentando progressivamente sob carga",
        ],
        "solutions": [
            {
                "id": "increase-memory",
                "label": "Aumentar `resources.limits.memory` no Helm values + investigar memory leak",
                "correct": True,
                "explanation": "✅ Correto! Aumentar o limit imediatamente mitiga o OOM Kill. Em paralelo, investigar se há memory leak na aplicação (profiling) resolve a causa raiz.",
            },
            {
                "id": "rollback",
                "label": "Fazer rollback para a versão anterior",
                "correct": False,
                "explanation": "❌ Pode não resolver. Se o problema é crescimento de tráfego, a versão anterior também sofreria OOM. Verificar se é leak de código novo antes de decidir.",
            },
            {
                "id": "hpa-scale",
                "label": "Escalar mais réplicas via HPA",
                "correct": False,
                "explanation": "❌ Incorreto. Mais réplicas com o mesmo limit vão sofrer OOM igualmente. O problema é o limit de memória insuficiente, não a quantidade de pods.",
            },
        ],
        "runbook": "/docs",
        "detection_delay_seconds": 25,
        "investigation_delay_seconds": 70,
        "chaos_action": None,
    },
    "dns-failure": {
        "id": "dns-failure",
        "title": "DNS Resolution Failure",
        "severity": "SEV-1",
        "category": "Network",
        "icon": "🌐",
        "description": "A aplicação não consegue resolver nomes de serviços internos. Conexões com PostgreSQL e Redis falhando por timeout. NetworkPolicy pode estar bloqueando o tráfego DNS.",
        "symptoms": [
            "App logs: socket.gaierror: [Errno -2] Name or service not known",
            "nslookup postgresql.sre-rag.svc.cluster.local: SERVFAIL",
            "CoreDNS pods em estado de alta utilização de CPU",
            "NetworkPolicy pode estar bloqueando porta 53/UDP",
        ],
        "solutions": [
            {
                "id": "coredns-netpol",
                "label": "Reiniciar CoreDNS pods + validar NetworkPolicy (permitir porta 53/UDP)",
                "correct": True,
                "explanation": "✅ Correto! Reiniciar o CoreDNS resolve falhas transitórias. Verificar a NetworkPolicy para garantir que a porta 53 (UDP/TCP) está liberada para o namespace.",
            },
            {
                "id": "restart-app",
                "label": "Reiniciar todos os pods da aplicação",
                "correct": False,
                "explanation": "❌ Incorreto. Reiniciar a aplicação não resolve falha no DNS. Os pods reiniciados tentarão resolver o mesmo nome e falharão igualmente.",
            },
            {
                "id": "use-ip",
                "label": "Substituir nomes de serviço por IPs estáticos nos ConfigMaps",
                "correct": False,
                "explanation": "❌ Perigoso e anti-pattern. IPs de pods/serviços no Kubernetes são dinâmicos. Usar IPs fixos causa falhas assim que os serviços são recriados.",
            },
        ],
        "runbook": "/docs",
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
    severity: str
    started_at: str
    solved_at: Optional[str]
    mttd_seconds: Optional[float]
    mttr_seconds: Optional[float]
    solution_chosen: Optional[str]
    correct: Optional[bool]
    explanation: Optional[str]


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
            severity=scenario["severity"],
            started_at=datetime.fromtimestamp(self.active.started_at).strftime("%H:%M:%S"),
            solved_at=datetime.now().strftime("%H:%M:%S"),
            mttd_seconds=mttd,
            mttr_seconds=round(elapsed, 1),
            solution_chosen=solution["label"],
            correct=solution["correct"],
            explanation=solution["explanation"],
        )

        self.history.insert(0, result)
        self._counter += 1
        self.active = None

        return result.model_dump()

    def cancel(self):
        self.active = None
        return {"status": "cancelled"}


# Singleton engine instance
simulation_engine = IncidentSimulationEngine()
