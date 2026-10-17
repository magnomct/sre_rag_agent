/**
 * SRE RAG Agent — Chaos Engineering Module (ESM)
 * Controls Chaos Monkey toggles, status badges, and blast radius visualizers.
 */

export function initChaos() {
  console.log('[Chaos Module] Initialized');

  document.addEventListener('sre:chaos_update', (e) => {
    const detail = e.detail;
    console.log('[Chaos Module] Real-time chaos status:', detail);

    const toggle = document.getElementById('chaos-500-toggle');
    const badge = document.getElementById('chaos-active-badge');

    if (detail && detail.active) {
      if (toggle) toggle.checked = true;
      if (badge) {
        badge.style.display = 'inline-flex';
        badge.textContent = 'CHAOS ACTIVE';
      }
    } else {
      if (toggle) toggle.checked = false;
      if (badge) {
        badge.style.display = 'none';
      }
    }
  });
}
