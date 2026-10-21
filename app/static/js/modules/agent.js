/**
 * SRE RAG Agent — Autonomous SRE Agent ESM Frontend Module (v4.0)
 * Handles live OODA reasoning streaming, interactive diagnostic dispatch, and one-click remediation.
 */

import { fetchAPI } from './api.js';

export function initAgentUI() {
  const container = document.getElementById('agent-live-panel');
  if (!container) return;

  const btnDiagnose = document.getElementById('btn-agent-diagnose');
  const inputQuery = document.getElementById('agent-query-input');
  const streamTimeline = document.getElementById('agent-stream-timeline');

  // Listen for real-time SSE stream events dispatched from sse.js
  document.addEventListener('sre:agent_stream', (e) => {
    const payload = e.detail;
    renderOODAStep(payload, streamTimeline);
  });

  if (btnDiagnose && inputQuery) {
    btnDiagnose.addEventListener('click', async () => {
      const query = inputQuery.value.trim() || 'Investigate active cluster health and anomalies';
      btnDiagnose.disabled = true;
      btnDiagnose.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Investigando...';

      if (streamTimeline) {
        streamTimeline.innerHTML = '<div class="text-muted small py-2"><i class="fas fa-satellite-dish me-2 fa-spin text-info"></i>Iniciando ciclo OODA... Conectando à telemetria ao vivo...</div>';
      }

      try {
        const report = await fetchAPI('/api/v1/agent/diagnose', {
          method: 'POST',
          body: JSON.stringify({ query: query, auto_mitigate: false }),
        });
        renderFinalReport(report, streamTimeline);
      } catch (err) {
        if (streamTimeline) {
          streamTimeline.innerHTML += `<div class="alert alert-danger mt-2 py-1 px-2 small">Falha na investigação: ${err.message}</div>`;
        }
      } finally {
        btnDiagnose.disabled = false;
        btnDiagnose.innerHTML = '<i class="fas fa-robot me-1"></i> Iniciar Investigação OODA';
      }
    });
  }
}

function renderOODAStep(payload, container) {
  if (!container) return;

  const phaseColors = {
    OBSERVE: 'primary',
    ORIENT: 'info',
    DECIDE: 'warning',
    ACT: 'success',
  };

  const badgeColor = phaseColors[payload.phase] || 'secondary';
  const card = document.createElement('div');
  card.className = `card border-${badgeColor} bg-dark text-light mb-2 p-2 shadow-sm`;
  card.innerHTML = `
    <div class="d-flex align-items-center mb-1">
      <span class="badge bg-${badgeColor} me-2">${payload.phase}</span>
      <small class="text-muted">${new Date().toLocaleTimeString()}</small>
      ${payload.tool ? `<span class="badge bg-secondary ms-auto small">Tool: ${payload.tool}</span>` : ''}
    </div>
    <div class="small text-light">${payload.thought}</div>
  `;
  container.prepend(card);
}

function renderFinalReport(report, container) {
  if (!container) return;

  const summary = document.createElement('div');
  summary.className = 'alert alert-success border-success mt-3 py-2 px-3 small';
  summary.innerHTML = `
    <div class="fw-bold mb-1"><i class="fas fa-check-circle me-1"></i> Investigação OODA Concluída (${report.duration_seconds}s)</div>
    <div><strong>Causa Raiz:</strong> ${report.root_cause}</div>
    <div class="mt-1"><strong>Recomendação:</strong> <code>${report.remediation?.recommended_command || report.remediation?.action || 'Conforme runbook'}</code></div>
  `;
  container.prepend(summary);
}
