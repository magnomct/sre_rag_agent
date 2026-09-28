"""
SRE RAG Agent — Health Check Module
Implements liveness, readiness, and startup probe endpoints.
"""

import time
import redis
import psycopg2
import structlog
from config import settings

logger = structlog.get_logger()


class HealthChecker:
    """Checks health of all dependencies."""

    def __init__(self):
        self._started = False
        self._start_time = time.time()

    def mark_started(self):
        """Mark application as fully started."""
        self._started = True

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self._start_time

    def check_postgres(self) -> dict:
        """Check PostgreSQL connectivity."""
        try:
            conn = psycopg2.connect(
                host=settings.postgres_host,
                port=settings.postgres_port,
                dbname=settings.postgres_db,
                user=settings.postgres_user,
                password=settings.postgres_password,
                connect_timeout=3,
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            return {"status": "healthy", "latency_ms": 0}
        except Exception as e:
            logger.error("postgres_health_check_failed", error=str(e))
            return {"status": "unhealthy", "error": str(e)}

    def check_redis(self) -> dict:
        """Check Redis connectivity."""
        try:
            client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password or None,
                socket_timeout=3,
            )
            start = time.time()
            client.ping()
            latency = (time.time() - start) * 1000
            client.close()
            return {"status": "healthy", "latency_ms": round(latency, 2)}
        except Exception as e:
            logger.error("redis_health_check_failed", error=str(e))
            return {"status": "unhealthy", "error": str(e)}

    def liveness(self) -> dict:
        """
        Liveness probe: Is the process alive?
        Should NOT check dependencies — only process health.
        """
        return {
            "status": "alive",
            "uptime_seconds": round(self.uptime_seconds, 2),
        }

    def readiness(self) -> dict:
        """
        Readiness probe: Can the service handle traffic?
        Checks all critical dependencies.
        """
        postgres = self.check_postgres()
        redis_check = self.check_redis()

        is_ready = (
            postgres["status"] == "healthy"
            and redis_check["status"] == "healthy"
            and self._started
        )

        return {
            "status": "ready" if is_ready else "not_ready",
            "checks": {
                "postgresql": postgres,
                "redis": redis_check,
                "app_started": self._started,
            },
        }

    def startup(self) -> dict:
        """
        Startup probe: Has the app finished initialization?
        """
        return {
            "status": "started" if self._started else "starting",
            "uptime_seconds": round(self.uptime_seconds, 2),
        }


# Singleton instance
health_checker = HealthChecker()
