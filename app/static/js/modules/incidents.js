/**
 * SRE RAG Agent — Incident Management Module (ESM)
 * Handles incident catalog display, active simulation lifecycle, and scoring.
 */

export function initIncidents() {
  console.log('[Incidents Module] Initialized');

  document.addEventListener('sre:incident_update', (e) => {
    const detail = e.detail;
    console.log('[Incidents Module] Real-time event received:', detail);

    if (detail.action === 'started') {
      const banner = document.getElementById('active-incident-banner');
      if (banner) banner.style.display = 'flex';
    } else if (detail.action === 'resolved') {
      const banner = document.getElementById('active-incident-banner');
      if (banner) banner.style.display = 'none';
    }
  });
}
