"""
SRE RAG Agent — Server-Sent Events (SSE) Broadcaster
Manages real-time event distribution to connected dashboard clients.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Set, Dict, Any, Optional
import structlog

logger = structlog.get_logger()


class EventBroadcaster:
    """In-memory Pub/Sub event broadcaster for Server-Sent Events."""

    def __init__(self):
        self._subscribers: Set[asyncio.Queue] = set()

    async def subscribe(self) -> asyncio.Queue:
        """Register a new client connection."""
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.add(q)
        logger.info("sse_client_subscribed", total_subscribers=len(self._subscribers))
        return q

    async def unsubscribe(self, q: asyncio.Queue) -> None:
        """Unregister a disconnected client."""
        self._subscribers.discard(q)
        logger.info("sse_client_unsubscribed", total_subscribers=len(self._subscribers))

    async def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish an event to all connected dashboard subscribers."""
        if not self._subscribers:
            return

        payload = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Non-blocking broadcast
        dead_queues = []
        for q in list(self._subscribers):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                dead_queues.append(q)

        for dq in dead_queues:
            self._subscribers.discard(dq)


# Global singleton broadcaster
broadcaster = EventBroadcaster()
