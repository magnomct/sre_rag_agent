/**
 * SRE RAG Agent — Main Application Entry Point (ESM) (v4.0)
 * Orchestrates all modern submodules, autonomous OODA Agent, and attaches real-time SSE stream listeners.
 */

import { fetchAPI } from './modules/api.js';
import { initSSE } from './modules/sse.js';
import { initIncidents } from './modules/incidents.js';
import { initChaos } from './modules/chaos.js';
import { initTerminal } from './modules/terminal.js';
import { initCharts } from './modules/charts.js';
import { initAgentUI } from './modules/agent.js';

document.addEventListener('DOMContentLoaded', () => {
  console.log('[SRE RAG Agent v4.0] Advanced AI & Real Chaos Dashboard Loaded.');

  // Initialize SSE streaming
  initSSE((eventType, payload) => {
    document.dispatchEvent(new CustomEvent(`sre:${eventType}`, { detail: payload }));
  });

  // Initialize domain modules
  initIncidents();
  initChaos();
  initTerminal();
  initCharts();
  initAgentUI();
});
