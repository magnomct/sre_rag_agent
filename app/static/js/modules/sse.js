/**
 * SRE RAG Agent — Server-Sent Events (SSE) Client (ESM)
 * Establishes persistent real-time streaming with automatic exponential backoff reconnection.
 */

let eventSource = null;
let reconnectDelay = 1000;
const MAX_RECONNECT_DELAY = 30000;

export function initSSE(onEvent) {
  if (eventSource) {
    eventSource.close();
  }

  console.log('[SSE] Connecting to /api/v1/events/stream...');
  eventSource = new EventSource('/api/v1/events/stream');

  eventSource.onopen = () => {
    console.log('[SSE] Real-time stream connected.');
    reconnectDelay = 1000;
    const badge = document.getElementById('sse-status-badge');
    if (badge) {
      badge.textContent = '● LIVE SSE';
      badge.style.color = '#3fb950';
    }
  };

  eventSource.addEventListener('connected', (e) => {
    try {
      const data = JSON.parse(e.data);
      console.log('[SSE] Handshake received:', data);
      if (onEvent) onEvent('connected', data);
    } catch (err) {
      console.warn('[SSE] Error parsing connected event:', err);
    }
  });

  eventSource.addEventListener('incident_update', (e) => {
    try {
      const data = JSON.parse(e.data);
      console.log('[SSE] Incident event:', data);
      if (onEvent) onEvent('incident_update', data);
    } catch (err) {
      console.warn('[SSE] Error parsing incident event:', err);
    }
  });

  eventSource.addEventListener('chaos_update', (e) => {
    try {
      const data = JSON.parse(e.data);
      console.log('[SSE] Chaos event:', data);
      if (onEvent) onEvent('chaos_update', data);
    } catch (err) {
      console.warn('[SSE] Error parsing chaos event:', err);
    }
  });

  eventSource.addEventListener('rag_query', (e) => {
    try {
      const data = JSON.parse(e.data);
      console.log('[SSE] RAG Query event:', data);
      if (onEvent) onEvent('rag_query', data);
    } catch (err) {
      console.warn('[SSE] Error parsing rag query event:', err);
    }
  });

  eventSource.onerror = (err) => {
    console.warn(`[SSE] Connection error. Reconnecting in ${reconnectDelay}ms...`, err);
    const badge = document.getElementById('sse-status-badge');
    if (badge) {
      badge.textContent = '○ RECONNECTING...';
      badge.style.color = '#d29922';
    }

    eventSource.close();
    setTimeout(() => {
      reconnectDelay = Math.min(reconnectDelay * 2, MAX_RECONNECT_DELAY);
      initSSE(onEvent);
    }, reconnectDelay);
  };

  return eventSource;
}
