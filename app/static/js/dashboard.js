/**
 * SRE Incident Simulation Dashboard — JavaScript
 * Handles polling, timers, simulation flow, and UI updates.
 */

// ── State ──────────────────────────────────────────────────
let activeScenarioId = null;
let elapsedInterval = null;
let pollingInterval = null;
let elapsedSeconds = 0;
let simulationStartTime = null;

// ── Helpers ────────────────────────────────────────────────
function formatTime(seconds) {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0');
  const s = Math.floor(seconds % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

function severityClass(sev) {
  return `sev-${sev}`;
}

// ── Start Simulation ───────────────────────────────────────
async function startSimulation(scenarioId) {
  if (activeScenarioId) {
    showToast('Já existe uma simulação ativa. Cancele primeiro.', 'warning');
    return;
  }

  try {
    const res = await fetch(`/api/v1/incidents/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario_id: scenarioId })
    });

    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();

    activeScenarioId = scenarioId;
    simulationStartTime = Date.now();
    elapsedSeconds = 0;

    // Update header status
    document.getElementById('status-dot').classList.add('incident');
    document.getElementById('status-text').textContent = 'Incidente Ativo';

    // Mark sidebar card as active
    document.querySelectorAll('.incident-card').forEach(card => {
      card.classList.remove('active');
      card.querySelector('.simulate-btn').disabled = false;
      card.querySelector('.simulate-btn').textContent = '▶ Simular';
      card.querySelector('.simulate-btn').classList.remove('running');
    });
    const activeCard = document.querySelector(`[data-scenario="${scenarioId}"]`);
    if (activeCard) {
      activeCard.classList.add('active');
      activeCard.querySelector('.simulate-btn').disabled = true;
      activeCard.querySelector('.simulate-btn').textContent = '⬤ Em execução...';
      activeCard.querySelector('.simulate-btn').classList.add('running');
    }

    // Show simulation panel
    renderSimulationPanel(scenarioId);

    // Start timers
    startElapsedTimer();
    startPolling();

  } catch (err) {
    showToast(`Erro ao iniciar simulação: ${err.message}`, 'error');
  }
}

// ── Render Simulation Panel ────────────────────────────────
function renderSimulationPanel(scenarioId) {
  const panels = document.getElementById('simulation-panels');
  const emptyState = document.getElementById('empty-state');

  emptyState.style.display = 'none';
  panels.innerHTML = '';

  fetch(`/api/v1/incidents/scenarios`)
    .then(r => r.json())
    .then(scenarios => {
      const scenario = scenarios.find(s => s.id === scenarioId);
      if (!scenario) return;

      panels.innerHTML = `
        <div class="simulation-panel visible fade-in" id="active-simulation">
          <div class="simulation-header">
            <div class="simulation-title">
              <span>${scenario.icon}</span>
              <span>${scenario.title}</span>
              <span class="severity-badge ${severityClass(scenario.severity)}">${scenario.severity}</span>
            </div>
            <button class="cancel-btn" onclick="cancelSimulation()">✕ Cancelar</button>
          </div>

          <div class="elapsed-timer" id="elapsed-display">00:00</div>
          <div class="phase-label" id="phase-label">⏳ Incidente em progresso...</div>

          <div class="section-label">Sintomas Detectados</div>
          <ul class="symptoms-list">
            ${scenario.symptoms.map(s => `<li>⚠️ ${s}</li>`).join('')}
          </ul>

          <div class="section-label">Timeline do Incidente</div>
          <div class="timeline" id="incident-timeline">
            <div class="timeline-item">
              <div class="timeline-dot done" id="dot-start">✓</div>
              <div class="timeline-content">
                <div class="timeline-step-name">Incidente Iniciado</div>
                <div class="timeline-step-time" id="time-start">00:00</div>
              </div>
            </div>
            <div class="timeline-item">
              <div class="timeline-dot pending" id="dot-detected">○</div>
              <div class="timeline-content">
                <div class="timeline-step-name">MTTD — Detectado pelo Prometheus</div>
                <div class="timeline-step-time" id="time-detected">estimado ~${formatTime(scenario.detection_delay_seconds)}</div>
              </div>
            </div>
            <div class="timeline-item">
              <div class="timeline-dot pending" id="dot-investigating">○</div>
              <div class="timeline-content">
                <div class="timeline-step-name">SRE Investigando</div>
                <div class="timeline-step-time" id="time-investigating">estimado ~${formatTime(scenario.investigation_delay_seconds)}</div>
              </div>
            </div>
            <div class="timeline-item">
              <div class="timeline-dot pending" id="dot-solved">⭐</div>
              <div class="timeline-content">
                <div class="timeline-step-name">Mitigação — MTTR</div>
                <div class="timeline-step-time" id="time-solved">aguardando solução...</div>
              </div>
            </div>
          </div>

          <div class="section-label">Escolha a Solução Correta</div>
          <div class="solutions-grid" id="solutions-grid">
            ${scenario.solutions.map(sol => `
              <label class="solution-option" id="opt-${sol.id}">
                <input type="radio" name="solution" value="${sol.id}" onchange="selectSolution('${sol.id}')">
                <span class="solution-label">${sol.label}</span>
              </label>
            `).join('')}
          </div>

          <button class="apply-btn" id="apply-btn" onclick="applySolution()" disabled>
            🔧 Aplicar Solução
          </button>

          <div class="result-banner" id="result-banner"></div>
        </div>
      `;
    });
}

// ── Elapsed Timer ──────────────────────────────────────────
function startElapsedTimer() {
  clearInterval(elapsedInterval);
  elapsedInterval = setInterval(() => {
    elapsedSeconds = (Date.now() - simulationStartTime) / 1000;
    const display = document.getElementById('elapsed-display');
    if (display) display.textContent = formatTime(elapsedSeconds);
  }, 500);
}

// ── Polling Active State ───────────────────────────────────
function startPolling() {
  clearInterval(pollingInterval);
  pollingInterval = setInterval(async () => {
    if (!activeScenarioId) { clearInterval(pollingInterval); return; }

    try {
      const res = await fetch('/api/v1/incidents/active');
      if (!res.ok) return;
      const state = await res.json();

      updateTimeline(state);
    } catch (_) {}
  }, 2000);
}

function updateTimeline(state) {
  const phase = state.phase;
  const phaseLabel = document.getElementById('phase-label');

  if (phase === 'detected' || phase === 'investigating') {
    const dot = document.getElementById('dot-detected');
    if (dot && !dot.classList.contains('done')) {
      dot.classList.remove('pending', 'active');
      dot.classList.add('done');
      dot.textContent = '✓';
      document.getElementById('time-detected').textContent = formatTime(state.detection_at) + ' (MTTD ✓)';
    }
  }

  if (phase === 'investigating') {
    const dot = document.getElementById('dot-investigating');
    if (dot && !dot.classList.contains('done')) {
      dot.classList.remove('pending', 'active');
      dot.classList.add('done');
      dot.textContent = '✓';
      document.getElementById('time-investigating').textContent = formatTime(state.investigation_at) + ' — escolha a solução';
    }
    if (phaseLabel) phaseLabel.textContent = '🔍 SRE investigando — selecione a solução abaixo';
  } else if (phase === 'detected') {
    // pulse the detected dot
    const dot = document.getElementById('dot-detected');
    if (dot && !dot.classList.contains('done')) {
      dot.classList.remove('pending');
      dot.classList.add('active');
    }
    if (phaseLabel) phaseLabel.textContent = '🚨 ALERT! Prometheus detectou o incidente';
  }
}

// ── Solution Selection ─────────────────────────────────────
let selectedSolution = null;

function selectSolution(solutionId) {
  selectedSolution = solutionId;
  document.querySelectorAll('.solution-option').forEach(opt => opt.classList.remove('selected'));
  const selected = document.getElementById(`opt-${solutionId}`);
  if (selected) selected.classList.add('selected');
  const applyBtn = document.getElementById('apply-btn');
  if (applyBtn) applyBtn.disabled = false;
}

// ── Apply Solution ─────────────────────────────────────────
async function applySolution() {
  if (!selectedSolution || !activeScenarioId) return;

  const applyBtn = document.getElementById('apply-btn');
  if (applyBtn) { applyBtn.disabled = true; applyBtn.textContent = '⏳ Aplicando...'; }

  try {
    const res = await fetch('/api/v1/incidents/solve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario_id: activeScenarioId, solution_id: selectedSolution })
    });

    const result = await res.json();

    // Highlight correct/wrong options
    document.querySelectorAll('.solution-option').forEach(opt => {
      opt.classList.remove('selected');
      opt.querySelector('input').disabled = true;
    });

    const chosenOpt = document.getElementById(`opt-${selectedSolution}`);
    if (chosenOpt) {
      chosenOpt.classList.add(result.correct ? 'correct' : 'incorrect');
    }

    // Mark solved on timeline
    const solvedDot = document.getElementById('dot-solved');
    if (solvedDot) {
      solvedDot.classList.remove('pending');
      solvedDot.classList.add(result.correct ? 'done' : 'active');
      solvedDot.textContent = result.correct ? '✓' : '✕';
    }
    const solvedTime = document.getElementById('time-solved');
    if (solvedTime) solvedTime.textContent = `MTTR: ${formatTime(result.mttr_seconds)}`;

    // Show result banner
    const banner = document.getElementById('result-banner');
    if (banner) {
      banner.classList.add(result.correct ? 'correct' : 'incorrect', 'visible');
      banner.innerHTML = `
        <strong>${result.correct ? '✅ Solução Correta!' : '❌ Solução Incorreta'}</strong><br>
        ${result.explanation}
        <div class="result-metrics">
          <div class="result-metric">
            <div class="result-metric-label">MTTD</div>
            <div class="result-metric-value">${formatTime(result.mttd_seconds)}</div>
          </div>
          <div class="result-metric">
            <div class="result-metric-label">MTTR</div>
            <div class="result-metric-value">${formatTime(result.mttr_seconds)}</div>
          </div>
          <div class="result-metric">
            <div class="result-metric-label">Resultado</div>
            <div class="result-metric-value">${result.correct ? '✅' : '❌'}</div>
          </div>
        </div>
      `;
    }

    // Phase label
    const phaseLabel = document.getElementById('phase-label');
    if (phaseLabel) phaseLabel.textContent = result.correct ? '✅ Incidente mitigado! Serviço recuperado.' : '❌ Solução incorreta — incidente persiste.';

    // Stop timers
    clearInterval(elapsedInterval);
    clearInterval(pollingInterval);

    // Reset sidebar
    resetSidebar();

    // Refresh history table
    setTimeout(refreshHistory, 500);

  } catch (err) {
    showToast(`Erro: ${err.message}`, 'error');
  }
}

// ── Cancel Simulation ──────────────────────────────────────
async function cancelSimulation() {
  await fetch('/api/v1/incidents/cancel', { method: 'POST' });
  activeScenarioId = null;
  selectedSolution = null;
  clearInterval(elapsedInterval);
  clearInterval(pollingInterval);
  resetSidebar();
  document.getElementById('simulation-panels').innerHTML = '';
  document.getElementById('empty-state').style.display = 'flex';
}

function resetSidebar() {
  activeScenarioId = null;
  document.getElementById('status-dot').classList.remove('incident');
  document.getElementById('status-text').textContent = 'Todos os sistemas operacionais';
  document.querySelectorAll('.incident-card').forEach(card => {
    card.classList.remove('active');
    card.querySelector('.simulate-btn').disabled = false;
    card.querySelector('.simulate-btn').textContent = '▶ Simular';
    card.querySelector('.simulate-btn').classList.remove('running');
  });
}

// ── Refresh History Table ──────────────────────────────────
async function refreshHistory() {
  try {
    const res = await fetch('/api/v1/incidents/history');
    const history = await res.json();
    const container = document.getElementById('history-body');
    if (!container) return;

    if (history.length === 0) {
      container.innerHTML = `<tr><td colspan="6" class="history-empty">Nenhuma simulação realizada ainda. Clique em "▶ Simular" para começar.</td></tr>`;
      return;
    }

    container.innerHTML = history.map(item => `
      <tr>
        <td>${item.id}</td>
        <td class="scenario-name">${item.icon || ''} ${item.scenario_title}</td>
        <td><span class="severity-badge ${severityClass(item.severity)}">${item.severity}</span></td>
        <td>${formatTime(item.mttd_seconds ?? 0)}</td>
        <td>${formatTime(item.mttr_seconds ?? 0)}</td>
        <td class="${item.correct ? 'result-correct' : 'result-incorrect'}">${item.correct ? '✅ Correto' : '❌ Incorreto'}</td>
      </tr>
    `).join('');
  } catch (_) {}
}

// ── Toast Notification ─────────────────────────────────────
function showToast(message, type = 'info') {
  console.log(`[${type.toUpperCase()}] ${message}`);
}

// ── Init ───────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  refreshHistory();
});
