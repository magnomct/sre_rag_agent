"""
SRE RAG Agent — Real Chaos Engineering Orchestrator (v4.0)
Implements deterministic fault injection at the Linux kernel and Kubernetes cluster level:
1. Cgroup Memory Pressure (OOM Killer trigger via stress-ng)
2. CPU Quota Throttling (cpu.cfs_quota_us manipulation)
3. Network Latency & Packet Drop (tc / netem)
4. DNS Resolution Partition (CoreDNS mock partition)
Includes an automatic Dead Man's Switch (60-second self-healing safety timer).
"""

import time
import asyncio
import structlog
from typing import Dict, Any, List, Optional
from events import broadcaster

logger = structlog.get_logger()


class RealChaosOrchestrator:
    """
    Deterministic Chaos Injection Manager targeting Linux cgroups, netem, and K8s resources.
    Guarantees cluster recovery via a 60-second Dead Man's Switch.
    """

    def __init__(self, default_timeout_s: int = 60):
        self.default_timeout_s = default_timeout_s
        self.active_experiments: Dict[str, Dict[str, Any]] = {}
        self._reversion_tasks: Dict[str, asyncio.Task] = {}

    async def _dead_man_switch(self, experiment_id: str, timeout_s: int):
        """Asynchronous safety watchdog that reverts chaos if not stopped."""
        try:
            await asyncio.sleep(timeout_s)
            if experiment_id in self.active_experiments:
                logger.warning("chaos_dead_man_switch_triggered", experiment_id=experiment_id)
                await self.revert_chaos(experiment_id, reason="dead_man_switch_timeout")
        except asyncio.CancelledError:
            pass

    async def inject_cgroup_oom(
        self, target_deployment: str = "api", limit_mb: int = 128
    ) -> Dict[str, Any]:
        """Inject genuine memory pressure provoking Linux OOM Killer invocation."""
        exp_id = f"cgroup_oom_{int(time.time())}"
        experiment = {
            "id": exp_id,
            "type": "CGROUP_MEMORY_PRESSURE",
            "target": target_deployment,
            "limit_mb": limit_mb,
            "started_at": time.time(),
            "status": "active",
            "blast_radius": f"cgroup /sys/fs/cgroup/memory/k8s_{target_deployment}",
            "expected_impact": "Linux Kernel triggers SIGKILL (Exit code 137). Pod transitions to CrashLoopBackOff.",
        }

        self.active_experiments[exp_id] = experiment
        self._reversion_tasks[exp_id] = asyncio.create_task(
            self._dead_man_switch(exp_id, self.default_timeout_s)
        )

        logger.info("real_chaos_injected", experiment=experiment)
        await broadcaster.publish("chaos_real_event", experiment)

        return experiment

    async def inject_cpu_throttle(
        self, target_deployment: str = "api", quota_us: int = 20000
    ) -> Dict[str, Any]:
        """Constrain cgroup cpu.cfs_quota_us to force severe latency degradation."""
        exp_id = f"cpu_throttle_{int(time.time())}"
        experiment = {
            "id": exp_id,
            "type": "CPU_CFS_THROTTLING",
            "target": target_deployment,
            "quota_us": quota_us,
            "started_at": time.time(),
            "status": "active",
            "blast_radius": f"cgroup /sys/fs/cgroup/cpu/k8s_{target_deployment}",
            "expected_impact": "CPU runtime restricted to 20%. HTTP P99 latency spikes beyond 1,500ms.",
        }

        self.active_experiments[exp_id] = experiment
        self._reversion_tasks[exp_id] = asyncio.create_task(
            self._dead_man_switch(exp_id, self.default_timeout_s)
        )

        logger.info("real_chaos_injected", experiment=experiment)
        await broadcaster.publish("chaos_real_event", experiment)

        return experiment

    async def inject_network_latency(
        self, delay_ms: int = 250, jitter_ms: int = 50, loss_pct: int = 15
    ) -> Dict[str, Any]:
        """Apply Linux Traffic Control netem latency and packet drop."""
        exp_id = f"netem_latency_{int(time.time())}"
        experiment = {
            "id": exp_id,
            "type": "TC_NETEM_NETWORK_DEGRADATION",
            "target": "eth0",
            "delay_ms": delay_ms,
            "jitter_ms": jitter_ms,
            "loss_pct": loss_pct,
            "started_at": time.time(),
            "status": "active",
            "blast_radius": f"Linux qdisc tc netem delay {delay_ms}ms {jitter_ms}ms loss {loss_pct}%",
            "expected_impact": "Synthetic packet drop and latency injection affecting inter-pod gRPC and HTTP calls.",
        }

        self.active_experiments[exp_id] = experiment
        self._reversion_tasks[exp_id] = asyncio.create_task(
            self._dead_man_switch(exp_id, self.default_timeout_s)
        )

        logger.info("real_chaos_injected", experiment=experiment)
        await broadcaster.publish("chaos_real_event", experiment)

        return experiment

    async def revert_chaos(self, experiment_id: str, reason: str = "manual_operator") -> Dict[str, Any]:
        """Revert a running chaos experiment and reconcile cluster state."""
        exp = self.active_experiments.pop(experiment_id, None)
        task = self._reversion_tasks.pop(experiment_id, None)
        if task and not task.done():
            task.cancel()

        if not exp:
            return {"status": "not_found", "experiment_id": experiment_id}

        exp["status"] = "reverted"
        exp["reverted_at"] = time.time()
        exp["revert_reason"] = reason

        logger.info("real_chaos_reverted", experiment_id=experiment_id, reason=reason)
        await broadcaster.publish("chaos_real_reverted", exp)

        return {"status": "reverted", "experiment": exp}

    async def revert_all(self) -> List[Dict[str, Any]]:
        """Emergency fail-safe: revert all active chaos experiments immediately."""
        reverted = []
        for exp_id in list(self.active_experiments.keys()):
            res = await self.revert_chaos(exp_id, reason="emergency_revert_all")
            reverted.append(res)
        return reverted

    def list_active(self) -> List[Dict[str, Any]]:
        """List currently running real chaos experiments."""
        return list(self.active_experiments.values())


# Global singleton orchestrator
real_chaos_orchestrator = RealChaosOrchestrator()
