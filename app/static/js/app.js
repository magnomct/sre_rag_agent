/**
 * SRE RAG Agent — Main Application Entry Point (ESM)
 * Orchestrates all modern submodules and attaches real-time SSE stream listeners.
 */

import { fetchAPI } from './modules/api.js';
import { initSSE } from './modules/sse.js';
import { initIncidents } from './modules/incidents.js';
import { initChaos } from './modules/chaos.js';
import { initTerminal } from './modules/terminal.js';
import { initCharts } from './modules/charts.js';

document.addEventListener('DOMContentLoaded', () => {
  console.log('[SRE RAG Agent v3.5] Modular ESM Dashboard Loaded.');

  // Initialize SSE streaming
  initSSE((eventType, payload) => {
    document.dispatchEvent(new CustomEvent(`sre:${eventType}`, { detail: payload }));
  });

  // Initialize domain modules
  initIncidents();
  initChaos();
  initTerminal();
  initCharts();
});
