/**
 * SRE Incident Simulation Dashboard — JavaScript
 * Handles simulation lifecycle, randomizing solutions, SRE KPI calculations,
 * interactive SVG charts, and responsive UI updates.
 */

// ── State ──────────────────────────────────────────────────
let activeScenarioId = null;
let elapsedInterval = null;
let pollingInterval = null;
let elapsedSeconds = 0;
let simulationStartTime = null;
let selectedSolution = null;

// ── Helpers ────────────────────────────────────────────────
function formatTime(seconds) {
  if (seconds === null || seconds === undefined || isNaN(seconds)) return '00:00';
  const sec = Math.max(0, Math.round(seconds));
  const m = Math.floor(sec / 60).toString().padStart(2, '0');
  const s = (sec % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

function severityClass(sev) {
  return `sev-${sev}`;
}

// ── Start Simulation ───────────────────────────────────────
async function startSimulation(scenarioId) {
  if (activeScenarioId) {
    alert('Já existe uma simulação ativa. Conclua ou cancele a simulação em andamento primeiro.');
    return;
  }

  try {
    const res = await fetch('/api/v1/incidents/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario_id: scenarioId })
    });

    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();

    activeScenarioId = scenarioId;
    simulationStartTime = Date.now();
    elapsedSeconds = 0;
    selectedSolution = null;

    // Update header status
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    if (statusDot) statusDot.classList.add('incident');
    if (statusText) statusText.textContent = 'Simulação Ativa (Incidente em Curso)';

    // Mark sidebar card as active
    document.querySelectorAll('.incident-card').forEach(card => {
      card.classList.remove('active');
      const btn = card.querySelector('.simulate-btn');
      if (btn) {
        btn.disabled = false;
        btn.textContent = '▶ Simular';
        btn.classList.remove('running');
      }
    });

    const activeCard = document.querySelector(`[data-scenario="${scenarioId}"]`);
    if (activeCard) {
      activeCard.classList.add('active');
      const btn = activeCard.querySelector('.simulate-btn');
      if (btn) {
        btn.disabled = true;
        btn.textContent = '⬤ Em execução...';
        btn.classList.add('running');
      }
    }

    // Render the active simulation panel
    renderSimulationPanel(scenarioId);

    // Start timers
    startElapsedTimer();
    startPolling();

    // Scroll to top of main content
    const mainContent = document.querySelector('.main-content');
    if (mainContent) mainContent.scrollTop = 0;

  } catch (err) {
    alert(`Erro ao iniciar simulação: ${err.message}`);
  }
}

// ── Timer & Polling ────────────────────────────────────────
function startElapsedTimer() {
  clearInterval(elapsedInterval);
  elapsedInterval = setInterval(() => {
    elapsedSeconds++;
    const display = document.getElementById('elapsed-display');
    if (display) display.textContent = formatTime(elapsedSeconds);
  }, 1000);
}

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
  }, 1500);
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
      const timeEl = document.getElementById('time-detected');
      if (timeEl) timeEl.textContent = formatTime(state.detection_at) + ' (MTTD ✓)';
    }
  }

  if (phase === 'investigating') {
    const dot = document.getElementById('dot-investigating');
    if (dot && !dot.classList.contains('done')) {
      dot.classList.remove('pending', 'active');
      dot.classList.add('done');
      dot.textContent = '✓';
      const timeEl = document.getElementById('time-investigating');
      if (timeEl) timeEl.textContent = formatTime(state.investigation_at) + ' — analise as soluções abaixo';
    }
    if (phaseLabel) phaseLabel.textContent = '🔍 SRE investigando a causa raiz — selecione a melhor mitigação:';
  } else if (phase === 'detected') {
    const dot = document.getElementById('dot-detected');
    if (dot && !dot.classList.contains('done')) {
      dot.classList.remove('pending');
      dot.classList.add('active');
    }
    if (phaseLabel) phaseLabel.textContent = '🚨 ALERTA! Prometheus detectou a anomalia (MTTD)';
  }
}

// ── Render Active Simulation Panel ─────────────────────────
function renderSimulationPanel(scenarioId) {
  const panels = document.getElementById('simulation-panels');
  const emptyState = document.getElementById('empty-state');

  if (emptyState) emptyState.style.display = 'none';
  if (!panels) return;

  panels.innerHTML = '<div style="padding:24px;color:var(--text-secondary)">Carregando cenário...</div>';

  fetch('/api/v1/incidents/scenarios')
    .then(r => r.json())
    .then(scenarios => {
      const scenario = scenarios.find(s => s.id === scenarioId);
      if (!scenario) return;

      // ── SOLUÇÃO DO ITEM 2: Embaralhamento de opções ──────────
      // Usamos o algoritmo Fisher-Yates para garantir que a opção
      // correta NUNCA seja sempre a primeira, tendo distribuição uniforme.
      const shuffledSolutions = [...scenario.solutions];
      for (let i = shuffledSolutions.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffledSolutions[i], shuffledSolutions[j]] = [shuffledSolutions[j], shuffledSolutions[i]];
      }

      const optionLetters = ['A', 'B', 'C', 'D', 'E'];

      panels.innerHTML = `
        <div class="simulation-panel visible" id="active-simulation">
          <div class="simulation-header">
            <div class="simulation-title">
              <span>${scenario.icon}</span>
              <span>${scenario.title}</span>
              <span class="severity-badge ${severityClass(scenario.severity)}">${scenario.severity}</span>
            </div>
            <button class="cancel-btn" onclick="cancelSimulation()">✕ Cancelar Simulação</button>
          </div>

          <!-- SOLUÇÃO DO ITEM 1: Descrição completa exibida sem truncamento -->
          <div class="simulation-overview-card">
            <div class="section-label">Contexto e Impacto do Incidente</div>
            <div class="simulation-full-description">${scenario.description}</div>
          </div>

          <div class="elapsed-timer" id="elapsed-display">00:00</div>
          <div class="phase-label" id="phase-label">⏳ Simulação em andamento... Aguardando detecção</div>

          <div class="section-label">Sintomas & Telemetria Observada</div>
          <ul class="symptoms-list">
            ${scenario.symptoms.map(s => `<li>⚠️ ${s}</li>`).join('')}
          </ul>

          <div class="section-label">Linha do Tempo Operacional</div>
          <div class="timeline" id="incident-timeline">
            <div class="timeline-item">
              <div class="timeline-dot done" id="dot-start">✓</div>
              <div class="timeline-content">
                <div class="timeline-step-name">Incidente Deflagrado</div>
                <div class="timeline-step-time" id="time-start">00:00 (Início da degradação)</div>
              </div>
            </div>
            <div class="timeline-item">
              <div class="timeline-dot pending" id="dot-detected">○</div>
              <div class="timeline-content">
                <div class="timeline-step-name">MTTD — Detecção e Disparo de Alerta (Prometheus / Alertmanager)</div>
                <div class="timeline-step-time" id="time-detected">estimado ~${formatTime(scenario.detection_delay_seconds)}</div>
              </div>
            </div>
            <div class="timeline-item">
              <div class="timeline-dot pending" id="dot-investigating">○</div>
              <div class="timeline-content">
                <div class="timeline-step-name">Investigação SRE (Triage & Análise de Logs/Traces)</div>
                <div class="timeline-step-time" id="time-investigating">estimado ~${formatTime(scenario.investigation_delay_seconds)}</div>
              </div>
            </div>
            <div class="timeline-item">
              <div class="timeline-dot pending" id="dot-solved">⭐</div>
              <div class="timeline-content">
                <div class="timeline-step-name">Mitigação & Resolução (MTTR)</div>
                <div class="timeline-step-time" id="time-solved">Aguardando aplicação da solução...</div>
              </div>
            </div>
          </div>

          <div class="section-label">
            Escolha a Solução de Mitigação
            <span class="hint">(Opções embaralhadas aleatoriamente a cada simulação)</span>
          </div>

          <div class="solutions-grid" id="solutions-grid">
            ${shuffledSolutions.map((sol, idx) => `
              <label class="solution-option" id="opt-${sol.id}" onclick="selectSolution('${sol.id}')">
                <input type="radio" name="solution" value="${sol.id}" id="radio-${sol.id}">
                <span class="solution-badge">${optionLetters[idx] || (idx + 1)}</span>
                <span class="solution-label">${sol.label}</span>
              </label>
            `).join('')}
          </div>

          <button class="apply-btn" id="apply-btn" disabled onclick="applySolution()">
            ⚡ Aplicar Solução Selecionada
          </button>

          <div class="result-banner" id="result-banner"></div>
        </div>
      `;
    })
    .catch(err => {
      panels.innerHTML = `<div style="padding:24px;color:var(--sev1)">Erro ao carregar cenário: ${err.message}</div>`;
    });
}

// ── Solution Selection ─────────────────────────────────────
function selectSolution(solutionId) {
  selectedSolution = solutionId;
  document.querySelectorAll('.solution-option').forEach(opt => opt.classList.remove('selected'));
  const selected = document.getElementById(`opt-${solutionId}`);
  if (selected) {
    selected.classList.add('selected');
    const radio = document.getElementById(`radio-${solutionId}`);
    if (radio) radio.checked = true;
  }
  const applyBtn = document.getElementById('apply-btn');
  if (applyBtn) applyBtn.disabled = false;
}

// ── Apply Solution ─────────────────────────────────────────
async function applySolution() {
  if (!selectedSolution || !activeScenarioId) return;

  const applyBtn = document.getElementById('apply-btn');
  if (applyBtn) {
    applyBtn.disabled = true;
    applyBtn.textContent = '⏳ Executando runbook de mitigação...';
  }

  try {
    const res = await fetch('/api/v1/incidents/solve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario_id: activeScenarioId, solution_id: selectedSolution })
    });

    const result = await res.json();

    // Disable all options and highlight chosen
    document.querySelectorAll('.solution-option').forEach(opt => {
      opt.classList.remove('selected');
      const radio = opt.querySelector('input');
      if (radio) radio.disabled = true;
    });

    const chosenOpt = document.getElementById(`opt-${selectedSolution}`);
    if (chosenOpt) {
      chosenOpt.classList.add(result.correct ? 'correct' : 'incorrect');
    }

    // Update timeline dot
    const solvedDot = document.getElementById('dot-solved');
    if (solvedDot) {
      solvedDot.classList.remove('pending');
      solvedDot.classList.add(result.correct ? 'done' : 'active');
      solvedDot.textContent = result.correct ? '✓' : '✕';
    }

    const solvedTime = document.getElementById('time-solved');
    if (solvedTime) {
      solvedTime.textContent = `MTTR Final: ${formatTime(result.mttr_seconds)} (${result.correct ? 'Mitigado com sucesso' : 'Falha na mitigação'})`;
    }

    // Show result banner
    const banner = document.getElementById('result-banner');
    if (banner) {
      banner.classList.remove('correct', 'incorrect');
      banner.classList.add(result.correct ? 'correct' : 'incorrect', 'visible');
      banner.innerHTML = `
        <div style="font-weight:700;font-size:0.95rem;display:flex;align-items:center;gap:8px">
          <span>${result.correct ? '✅ Solução Correta!' : '❌ Solução Incorreta'}</span>
        </div>
        <div class="result-explanation-text">${result.explanation}</div>
        <div class="result-metrics">
          <div class="result-metric">
            <div class="result-metric-label">MTTD (Detecção)</div>
            <div class="result-metric-value">${formatTime(result.mttd_seconds)}</div>
          </div>
          <div class="result-metric">
            <div class="result-metric-label">MTTR (Mitigação)</div>
            <div class="result-metric-value">${formatTime(result.mttr_seconds)}</div>
          </div>
          <div class="result-metric">
            <div class="result-metric-label">Status Final</div>
            <div class="result-metric-value">${result.correct ? 'RESOLVIDO' : 'INCIDENTE ATIVO'}</div>
          </div>
        </div>
      `;
    }

    // Update phase label
    const phaseLabel = document.getElementById('phase-label');
    if (phaseLabel) {
      phaseLabel.textContent = result.correct
        ? '✅ Incidente mitigado com sucesso! SLI/SLA restabelecidos.'
        : '❌ Ação ineficaz — causa raiz não resolvida, o incidente persiste.';
    }

    // Stop timers
    clearInterval(elapsedInterval);
    clearInterval(pollingInterval);

    // Reset status header & sidebar
    resetSidebar();

    // Refresh history and charts
    setTimeout(refreshHistory, 300);

  } catch (err) {
    alert(`Erro ao aplicar solução: ${err.message}`);
    if (applyBtn) {
      applyBtn.disabled = false;
      applyBtn.textContent = '⚡ Aplicar Solução Selecionada';
    }
  }
}

// ── Cancel Simulation ──────────────────────────────────────
async function cancelSimulation() {
  if (!confirm('Deseja realmente cancelar a simulação atual?')) return;
  await fetch('/api/v1/incidents/cancel', { method: 'POST' });
  activeScenarioId = null;
  selectedSolution = null;
  clearInterval(elapsedInterval);
  clearInterval(pollingInterval);
  resetSidebar();
  const panels = document.getElementById('simulation-panels');
  if (panels) panels.innerHTML = '';
  const emptyState = document.getElementById('empty-state');
  if (emptyState) emptyState.style.display = 'flex';
}

function resetSidebar() {
  activeScenarioId = null;
  const statusDot = document.getElementById('status-dot');
  const statusText = document.getElementById('status-text');
  if (statusDot) statusDot.classList.remove('incident');
  if (statusText) statusText.textContent = 'Todos os sistemas operacionais';

  document.querySelectorAll('.incident-card').forEach(card => {
    card.classList.remove('active');
    const btn = card.querySelector('.simulate-btn');
    if (btn) {
      btn.disabled = false;
      btn.textContent = '▶ Simular';
      btn.classList.remove('running');
    }
  });
}

// ── Clear History ──────────────────────────────────────────
async function confirmClearHistory() {
  if (!confirm('Tem certeza de que deseja limpar todo o histórico de simulações?')) return;
  try {
    const res = await fetch('/api/v1/incidents/history/clear', { method: 'POST' });
    if (!res.ok) throw new Error(await res.text());
    await refreshHistory();
  } catch (err) {
    alert(`Erro ao limpar histórico: ${err.message}`);
  }
}

// ── SOLUÇÃO DO ITEM 3: SRE Analytics, Gráficos e Percentuais ─
async function refreshHistory() {
  try {
    const res = await fetch('/api/v1/incidents/history');
    if (!res.ok) return;
    const history = await res.json();

    const total = history.length;
    const correctCount = history.filter(h => h.correct).length;
    const incorrectCount = total - correctCount;
    const successRate = total > 0 ? Math.round((correctCount / total) * 100) : 0;

    // Calcular MTTD e MTTR médios
    const avgMttd = total > 0
      ? (history.reduce((acc, h) => acc + (h.mttd_seconds || 0), 0) / total)
      : 0;
    const avgMttr = total > 0
      ? (history.reduce((acc, h) => acc + (h.mttr_seconds || 0), 0) / total)
      : 0;

    // Distribuição por severidade
    const sev1 = history.filter(h => h.severity === 'SEV-1').length;
    const sev2 = history.filter(h => h.severity === 'SEV-2').length;
    const sev3 = history.filter(h => h.severity === 'SEV-3').length;

    // ── 1. Atualizar KPI Cards ───────────────────────────────
    const rateEl = document.getElementById('kpi-success-rate');
    const subRateEl = document.getElementById('kpi-success-sub');
    const badgeRateEl = document.getElementById('kpi-badge-rate');
    const ratePathEl = document.getElementById('kpi-rate-path');

    if (rateEl) rateEl.textContent = `${successRate}%`;
    if (subRateEl) subRateEl.textContent = `${correctCount} corretos de ${total}`;

    if (badgeRateEl) {
      badgeRateEl.className = 'kpi-badge';
      if (total === 0) {
        badgeRateEl.textContent = 'Sem dados';
      } else if (successRate >= 80) {
        badgeRateEl.textContent = 'Alta Resiliência';
        badgeRateEl.classList.add('success');
      } else if (successRate >= 50) {
        badgeRateEl.textContent = 'Moderado';
        badgeRateEl.classList.add('warning');
      } else {
        badgeRateEl.textContent = 'Atenção';
      }
    }

    if (ratePathEl) {
      ratePathEl.setAttribute('stroke-dasharray', `${successRate}, 100`);
      ratePathEl.style.stroke = successRate >= 80 ? 'var(--green)' : (successRate >= 50 ? 'var(--sev2)' : 'var(--sev1)');
    }

    const avgMttdEl = document.getElementById('kpi-avg-mttd');
    if (avgMttdEl) avgMttdEl.textContent = formatTime(avgMttd);

    const avgMttrEl = document.getElementById('kpi-avg-mttr');
    if (avgMttrEl) avgMttrEl.textContent = formatTime(avgMttr);

    const mttrPillEl = document.getElementById('kpi-mttr-pill');
    if (mttrPillEl) {
      if (total > 0 && avgMttr <= 60) {
        mttrPillEl.textContent = 'Excelente (< 01:00)';
        mttrPillEl.style.color = 'var(--green)';
      } else if (total > 0) {
        mttrPillEl.textContent = 'Atenção (> 01:00)';
        mttrPillEl.style.color = 'var(--sev2)';
      } else {
        mttrPillEl.textContent = 'Meta < 01:00';
        mttrPillEl.style.color = 'var(--text-secondary)';
      }
    }

    const totalSimsEl = document.getElementById('kpi-total-sims');
    if (totalSimsEl) totalSimsEl.textContent = total;

    const sevBreakdownEl = document.getElementById('kpi-sev-breakdown');
    if (sevBreakdownEl) {
      sevBreakdownEl.textContent = `SEV-1: ${sev1} · SEV-2: ${sev2} · SEV-3: ${sev3}`;
    }

    // ── 2. Atualizar Gráfico de Barras de Assertividade ───────
    const greenBar = document.getElementById('ratio-green-bar');
    const redBar = document.getElementById('ratio-red-bar');
    const greenLabel = document.getElementById('ratio-green-label');
    const redLabel = document.getElementById('ratio-red-label');

    const greenPct = total > 0 ? (correctCount / total) * 100 : 0;
    const redPct = total > 0 ? (incorrectCount / total) * 100 : 0;

    if (greenBar) greenBar.style.width = `${greenPct}%`;
    if (redBar) redBar.style.width = `${redPct}%`;
    if (greenLabel) greenLabel.textContent = `${Math.round(greenPct)}% Corretos (${correctCount})`;
    if (redLabel) redLabel.textContent = `${Math.round(redPct)}% Incorretos (${incorrectCount})`;

    // ── 3. Atualizar Gráfico SVG de MTTR Recente ─────────────
    renderMttrChart(history, avgMttr);

    // ── 4. Atualizar Tabela de Histórico ─────────────────────
    const tbody = document.getElementById('history-body');
    if (!tbody) return;

    if (total === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" class="history-empty">
            Nenhuma simulação realizada ainda. Selecione um cenário no menu à esquerda e clique em "▶ Simular".
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = history.map(item => `
      <tr>
        <td style="font-weight:600;color:var(--text-muted)">#${item.id}</td>
        <td class="scenario-cell">
          <div class="scenario-title-inline">
            <span>${item.icon || '🚨'}</span>
            <span>${item.scenario_title}</span>
          </div>
        </td>
        <td>
          <span class="severity-badge ${severityClass(item.severity)}">${item.severity}</span>
        </td>
        <td>${formatTime(item.mttd_seconds ?? 0)}</td>
        <td>${formatTime(item.mttr_seconds ?? 0)}</td>
        <td class="solution-chosen-cell" title="${item.explanation || ''}">
          ${item.solution_chosen || '—'}
        </td>
        <td>
          <span class="result-badge ${item.correct ? 'correct' : 'incorrect'}">
            ${item.correct ? '✅ Correto' : '❌ Incorreto'}
          </span>
        </td>
      </tr>
    `).join('');

  } catch (err) {
    console.error('Erro ao atualizar histórico:', err);
  }
}

// ── Gráfico SVG Dinâmico de MTTR das Últimas Simulações ─────
function renderMttrChart(history, avgMttr) {
  const svg = document.getElementById('mttr-spark-chart');
  const avgLabel = document.getElementById('chart-avg-line-label');
  if (!svg) return;

  if (avgLabel) avgLabel.textContent = `Média: ${formatTime(avgMttr)}`;

  if (!history || history.length === 0) {
    svg.innerHTML = `
      <text x="50%" y="50%" text-anchor="middle" fill="#6e7681" font-size="12" font-family="Inter">
        Aguardando primeiras simulações para gerar gráfico de MTTR
      </text>
    `;
    return;
  }

  // Pegar as últimas 12 simulações (em ordem cronológica para o gráfico)
  const recent = [...history].slice(0, 12).reverse();
  const count = recent.length;

  const width = 500;
  const height = 85;
  const paddingBottom = 16;
  const chartHeight = height - paddingBottom;

  // Encontrar o maior MTTR para a escala (mínimo 30s)
  const maxMttr = Math.max(30, ...recent.map(r => r.mttr_seconds || 0));

  const barWidth = Math.min(28, (width - (count * 8)) / count);
  const gap = (width - (count * barWidth)) / (count + 1);

  let elements = '';

  // Linha de média horizontal
  if (avgMttr > 0 && avgMttr <= maxMttr) {
    const avgY = chartHeight - (avgMttr / maxMttr) * chartHeight;
    elements += `
      <line x1="0" y1="${avgY}" x2="${width}" y2="${avgY}" stroke="rgba(88,166,255,0.4)" stroke-dasharray="4,4" stroke-width="1" />
      <text x="${width - 4}" y="${Math.max(10, avgY - 3)}" text-anchor="end" fill="#58a6ff" font-size="9" font-family="JetBrains Mono">Média (${formatTime(avgMttr)})</text>
    `;
  }

  // Renderizar cada barra
  recent.forEach((item, index) => {
    const mttr = item.mttr_seconds || 0;
    const barHeight = Math.max(4, (mttr / maxMttr) * (chartHeight - 8));
    const x = gap + index * (barWidth + gap);
    const y = chartHeight - barHeight;
    const color = item.correct ? 'var(--green)' : 'var(--sev1)';

    elements += `
      <g class="chart-bar-group">
        <rect
          x="${x}"
          y="${y}"
          width="${barWidth}"
          height="${barHeight}"
          rx="4"
          fill="${color}"
          opacity="0.85"
        >
          <title>#${item.id} - ${item.scenario_title} | MTTR: ${formatTime(mttr)} (${item.correct ? 'Correto' : 'Incorreto'})</title>
        </rect>
        <text
          x="${x + barWidth / 2}"
          y="${height - 2}"
          text-anchor="middle"
          fill="#8b949e"
          font-size="9"
          font-family="JetBrains Mono"
        >#${item.id}</text>
      </g>
    `;
  });

  svg.innerHTML = elements;
}

// ── Inicialização ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  refreshHistory();
});
