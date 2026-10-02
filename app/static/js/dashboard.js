/**
 * SRE Incident Simulation Dashboard — JavaScript Controller v2.1
 * - Tab navigation (Simulação & Chaos Lab vs Métricas & Histórico SRE)
 * - Complete bilingual support (pt-BR / en-US) with dynamic live switching
 * - Chaos Monkey real-time telemetry, sessions tracking & audit trail
 * - Incident simulation lifecycle, Fisher-Yates shuffle & MTTR/MTTD analytics
 */

// ── i18n Dictionary ─────────────────────────────────────────
const TRANSLATIONS = {
  pt: {
    // Header & Navigation
    app_title: "SRE Incident Simulation Lab",
    app_subtitle: "RAG Agent · Kubernetes · Observability · Chaos & Incident Response",
    status_all_ok: "Todos os sistemas operacionais",
    status_degraded: "Degradação Ativa (Chaos Monkey HTTP 500)",
    status_sim_active: "Simulação Ativa (Incidente em Curso)",
    status_chaos_active: "Falhas HTTP 500 sendo injetadas",
    link_board: "Board →",
    tab_simulation: "Simulação & Chaos Lab",
    tab_history: "Painel de Histórico & Métricas",

    // Sidebar
    sidebar_title: "Cenários de Incidente",
    btn_simulate: "▶ Simular",
    btn_running: "⬤ Em execução...",

    // Empty State
    empty_title: "Nenhuma Simulação Ativa",
    empty_desc: "Escolha um cenário de incidente no painel lateral à esquerda<br>e clique em <strong>▶ Simular</strong> para iniciar a dinâmica de resposta.<br><br>A timeline de <strong>MTTD → Investigação → Mitigação (MTTR)</strong> será ativada,<br>junto com o seletor de soluções (as opções são embaralhadas aleatoriamente).",

    // Active Simulation
    btn_cancel_sim: "✕ Cancelar Simulação",
    sim_overview: "Contexto e Impacto do Incidente",
    sim_phase_waiting: "⏳ Simulação em andamento... Aguardando detecção",
    sim_phase_detected: "🚨 ALERTA! Prometheus detectou a anomalia (MTTD)",
    sim_phase_investigating: "🔍 SRE investigando a causa raiz — selecione a melhor mitigação:",
    sim_symptoms_label: "Sintomas & Telemetria Observada",
    sim_timeline_label: "Linha do Tempo Operacional",
    timeline_start: "Incidente Deflagrado",
    timeline_start_sub: "00:00 (Início da degradação)",
    timeline_detected: "MTTD — Detecção e Disparo de Alerta (Prometheus / Alertmanager)",
    timeline_investigating: "Investigação SRE (Triage & Análise de Logs/Traces)",
    timeline_investigating_sub: "analise as soluções abaixo",
    timeline_solved: "Mitigação & Resolução (MTTR)",
    timeline_solved_waiting: "Aguardando aplicação da solução...",
    sim_solutions_label: "Escolha a Solução de Mitigação",
    sim_solutions_hint: "(Opções embaralhadas aleatoriamente a cada simulação)",
    btn_apply_solution: "⚡ Aplicar Solução Selecionada",
    btn_applying: "⏳ Executando runbook de mitigação...",
    result_correct: "✅ Solução Correta!",
    result_incorrect: "❌ Solução Incorreta",
    result_mttd_label: "MTTD (Detecção)",
    result_mttr_label: "MTTR (Mitigação)",
    result_status_label: "Status Final",
    status_resolved: "RESOLVIDO",
    status_unresolved: "INCIDENTE ATIVO",
    phase_success: "✅ Incidente mitigado com sucesso! SLI/SLA restabelecidos.",
    phase_failure: "❌ Ação ineficaz — causa raiz não resolvida, o incidente persiste.",
    btn_view_in_history: "📊 Ver Análise no Histórico →",

    // Chaos Monkey
    chaos_btn_off: "Chaos Monkey: Off",
    chaos_btn_active: "Chaos Monkey: ATIVO (500)",
    chaos_btn_title_off: "Clique para ativar o Chaos Monkey (injeta HTTP 500 no workload da API)",
    chaos_btn_title_active: "Injeção de 500 ativa no workload! Clique para desativar.",
    chaos_section_title: "Chaos Monkey & Auditoria de Resiliência",
    chaos_section_sub: "Telemetria em tempo real, injeção de falhas no workload da API e trilha de auditoria para observabilidade SRE.",
    btn_refresh: "🔄 Atualizar",
    btn_clear_audit: "🗑️ Limpar Auditoria",
    chaos_kpi_state: "Estado do Injetor",
    chaos_badge_inactive: "Inativo",
    chaos_badge_active: "Ativo",
    chaos_main_state_normal: "NORMAL",
    chaos_main_state_500: "HTTP 500",
    chaos_dur_inactive: "Workload 100% Saudável",
    chaos_dur_running: "Em execução:",
    chaos_tag_healthy: "Workload Saudável",
    chaos_tag_failing: "⚠️ Falhas Injetadas no Workload",
    chaos_kpi_total: "Falhas Injetadas (Total)",
    chaos_kpi_total_sub: "Erros HTTP 500 no workload",
    chaos_kpi_session: "Sessão Atual / Recente",
    chaos_kpi_session_empty: "Nenhuma sessão ativa no momento",
    chaos_kpi_targets: "Alvos do Workload",
    chaos_kpi_targets_none: "Nenhum endpoint afetado",
    chaos_kpi_targets_waiting: "Aguardando requisições ao workload",
    terminal_title: "SRE Chaos Audit Stream",
    terminal_placeholder: "Nenhum evento registrado. Ative o Chaos Monkey ou envie uma query RAG para ver o stream.",
    sessions_title: "Histórico de Sessões de Caos",
    sessions_empty: "Nenhuma sessão registrada.",
    col_session_id: "#",
    col_start: "Início",
    col_duration: "Duração",
    col_faults: "Falhas",
    col_endpoints: "Endpoints",
    col_status: "Status",
    session_active: "Ativa",
    session_completed: "Concluída",
    chaos_toast_active_title: "Chaos Monkey Ativado!",
    chaos_toast_active_desc: "Injetando HTTP 500 no workload da API de inferência.",
    chaos_toast_inactive_title: "Chaos Monkey Desativado!",
    chaos_toast_inactive_desc: "Sessão finalizada e workload normalizado.",

    // History & SRE Analytics
    history_section_title: "Painel de Métricas & Histórico SRE",
    history_section_sub: "Estatísticas agregadas, taxa de assertividade e tempos médios de resolução (MTTR / MTTD)",
    btn_clear_history: "🗑️ Limpar Histórico",
    kpi_success_rate: "Taxa de Sucesso SRE",
    kpi_avg_mttd: "MTTD Médio (Detecção)",
    kpi_mttd_sub: "Tempo médio até alerta",
    kpi_avg_mttr: "MTTR Médio (Mitigação)",
    kpi_mttr_sub: "Tempo médio até mitigação",
    kpi_total_sims: "Simulações Realizadas",
    chart_distribution: "Distribuição de Resultados (Assertividade)",
    legend_correct: "Corretos",
    legend_incorrect: "Incorretos",
    chart_mttr_trend: "Performance Recente de MTTR (Últimas Simulações)",
    chart_avg_prefix: "Média:",
    chart_empty: "Aguardando dados de simulação...",
    table_th_num: "#",
    table_th_scenario: "Cenário de Incidente",
    table_th_severity: "Severidade",
    table_th_mttd: "MTTD",
    table_th_mttr: "MTTR",
    table_th_solution: "Solução Escolhida",
    table_th_result: "Resultado",
    table_empty: "Nenhuma simulação registrada. Selecione um cenário no painel lateral para iniciar o treino SRE.",
    table_loading: "Carregando histórico...",
    outcome_correct: "Correto",
    outcome_incorrect: "Incorreto",
    badge_waiting: "Aguardando",
    badge_no_data: "Sem dados",
    badge_excellent: "Excelente",
    badge_good: "Bom",
    badge_poor: "Precisa Melhorar",

    // Footer
    footer_app_name: "SRE Incident Lab",
    footer_author: "Autor:",
    footer_license: "Licença MIT",
  },

  en: {
    // Header & Navigation
    app_title: "SRE Incident Simulation Lab",
    app_subtitle: "RAG Agent · Kubernetes · Observability · Chaos & Incident Response",
    status_all_ok: "All systems operational",
    status_degraded: "Active Degradation (Chaos Monkey HTTP 500)",
    status_sim_active: "Active Simulation (Incident in Progress)",
    status_chaos_active: "HTTP 500 faults being injected",
    link_board: "Board →",
    tab_simulation: "Simulation & Chaos Lab",
    tab_history: "SRE History & Metrics Panel",

    // Sidebar
    sidebar_title: "Incident Scenarios",
    btn_simulate: "▶ Simulate",
    btn_running: "⬤ Running...",

    // Empty State
    empty_title: "No Active Simulation",
    empty_desc: "Select an incident scenario from the sidebar on the left<br>and click <strong>▶ Simulate</strong> to launch the response workflow.<br><br>The <strong>MTTD → Triage → Mitigation (MTTR)</strong> timeline will activate,<br>along with randomly shuffled remediation strategies.",

    // Active Simulation
    btn_cancel_sim: "✕ Cancel Simulation",
    sim_overview: "Incident Context & Impact",
    sim_phase_waiting: "⏳ Simulation in progress... Awaiting detection",
    sim_phase_detected: "🚨 ALERT! Prometheus detected the anomaly (MTTD)",
    sim_phase_investigating: "🔍 SRE investigating root cause — select the best mitigation:",
    sim_symptoms_label: "Observed Symptoms & Telemetry",
    sim_timeline_label: "Operational Timeline",
    timeline_start: "Incident Triggered",
    timeline_start_sub: "00:00 (Degradation start)",
    timeline_detected: "MTTD — Detection & Alerting (Prometheus / Alertmanager)",
    timeline_investigating: "SRE Triage & Root Cause Investigation",
    timeline_investigating_sub: "analyze the solutions below",
    timeline_solved: "Mitigation & Resolution (MTTR)",
    timeline_solved_waiting: "Awaiting mitigation strategy...",
    sim_solutions_label: "Select Mitigation Strategy",
    sim_solutions_hint: "(Options randomly shuffled on each simulation)",
    btn_apply_solution: "⚡ Apply Selected Solution",
    btn_applying: "⏳ Executing mitigation runbook...",
    result_correct: "✅ Correct Solution!",
    result_incorrect: "❌ Incorrect Solution",
    result_mttd_label: "MTTD (Detection)",
    result_mttr_label: "MTTR (Mitigation)",
    result_status_label: "Final Status",
    status_resolved: "RESOLVED",
    status_unresolved: "ACTIVE INCIDENT",
    phase_success: "✅ Incident successfully mitigated! SLI/SLA restored.",
    phase_failure: "❌ Ineffective action — root cause unresolved, incident persists.",
    btn_view_in_history: "📊 View Analysis in History Tab →",

    // Chaos Monkey
    chaos_btn_off: "Chaos Monkey: Off",
    chaos_btn_active: "Chaos Monkey: ACTIVE (500)",
    chaos_btn_title_off: "Click to activate Chaos Monkey (injects HTTP 500 faults into API workload)",
    chaos_btn_title_active: "HTTP 500 injection active on workload! Click to deactivate.",
    chaos_section_title: "Chaos Monkey & Resilience Audit",
    chaos_section_sub: "Real-time telemetry, API workload fault injection, and audit trail for SRE observability.",
    btn_refresh: "🔄 Refresh",
    btn_clear_audit: "🗑️ Clear Audit",
    chaos_kpi_state: "Injector State",
    chaos_badge_inactive: "Inactive",
    chaos_badge_active: "Active",
    chaos_main_state_normal: "NORMAL",
    chaos_main_state_500: "HTTP 500",
    chaos_dur_inactive: "Workload 100% Healthy",
    chaos_dur_running: "Running for:",
    chaos_tag_healthy: "Workload Healthy",
    chaos_tag_failing: "⚠️ Faults Injected in Workload",
    chaos_kpi_total: "Faults Injected (Total)",
    chaos_kpi_total_sub: "HTTP 500 workload errors",
    chaos_kpi_session: "Current / Recent Session",
    chaos_kpi_session_empty: "No active session at the moment",
    chaos_kpi_targets: "Workload Targets",
    chaos_kpi_targets_none: "No endpoints affected",
    chaos_kpi_targets_waiting: "Awaiting workload requests",
    terminal_title: "SRE Chaos Audit Stream",
    terminal_placeholder: "No events recorded. Activate Chaos Monkey or submit a RAG query to see the stream.",
    sessions_title: "Chaos Sessions History",
    sessions_empty: "No sessions recorded.",
    col_session_id: "#",
    col_start: "Started",
    col_duration: "Duration",
    col_faults: "Faults",
    col_endpoints: "Endpoints",
    col_status: "Status",
    session_active: "Active",
    session_completed: "Completed",
    chaos_toast_active_title: "Chaos Monkey Activated!",
    chaos_toast_active_desc: "Injecting HTTP 500 errors into API inference workload.",
    chaos_toast_inactive_title: "Chaos Monkey Deactivated!",
    chaos_toast_inactive_desc: "Session ended and workload normalized.",

    // History & SRE Analytics
    history_section_title: "SRE Metrics & History Dashboard",
    history_section_sub: "Aggregated statistics, accuracy rate, and average resolution times (MTTR / MTTD)",
    btn_clear_history: "🗑️ Clear History",
    kpi_success_rate: "SRE Success Rate",
    kpi_avg_mttd: "Average MTTD (Detection)",
    kpi_mttd_sub: "Average time to alert",
    kpi_avg_mttr: "Average MTTR (Mitigation)",
    kpi_mttr_sub: "Average time to mitigation",
    kpi_total_sims: "Simulations Completed",
    chart_distribution: "Outcome Distribution (Accuracy)",
    legend_correct: "Correct",
    legend_incorrect: "Incorrect",
    chart_mttr_trend: "Recent MTTR Performance (Latest Simulations)",
    chart_avg_prefix: "Average:",
    chart_empty: "Awaiting simulation data...",
    table_th_num: "#",
    table_th_scenario: "Incident Scenario",
    table_th_severity: "Severity",
    table_th_mttd: "MTTD",
    table_th_mttr: "MTTR",
    table_th_solution: "Chosen Solution",
    table_th_result: "Outcome",
    table_empty: "No simulations recorded. Select an incident scenario from the sidebar to begin SRE training.",
    table_loading: "Loading history...",
    outcome_correct: "Correct",
    outcome_incorrect: "Incorrect",
    badge_waiting: "Waiting",
    badge_no_data: "No data",
    badge_excellent: "Excellent",
    badge_good: "Good",
    badge_poor: "Needs Work",

    // Footer
    footer_app_name: "SRE Incident Lab",
    footer_author: "Author:",
    footer_license: "MIT License",
  }
};

// ── State ──────────────────────────────────────────────────
let currentLang = localStorage.getItem('sre_lab_lang') || 'pt';
let currentTab = 'simulation';
let activeScenarioId = null;
let elapsedInterval = null;
let pollingInterval = null;
let elapsedSeconds = 0;
let simulationStartTime = null;
let selectedSolution = null;
let cachedScenarios = null;
let isChaosMonkeyActive = false;
let chaosPollTimer = null;

// ── i18n Helpers ───────────────────────────────────────────
function t(key) {
  const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.pt;
  return dict[key] !== undefined ? dict[key] : (TRANSLATIONS.pt[key] || key);
}

function setLanguage(lang) {
  if (lang !== 'pt' && lang !== 'en') lang = 'pt';
  currentLang = lang;
  localStorage.setItem('sre_lab_lang', lang);

  // Update language buttons
  const btnPt = document.getElementById('lang-btn-pt');
  const btnEn = document.getElementById('lang-btn-en');
  if (btnPt && btnEn) {
    btnPt.classList.toggle('active', lang === 'pt');
    btnEn.classList.toggle('active', lang === 'en');
  }

  document.documentElement.lang = lang === 'pt' ? 'pt-BR' : 'en-US';

  // Apply all data-i18n attributes
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    el.innerHTML = t(key);
  });

  // Apply titles if any
  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    const key = el.getAttribute('data-i18n-title');
    el.setAttribute('title', t(key));
  });

  // Update dynamic elements
  updateSidebarLanguage();
  if (activeScenarioId) {
    renderSimulationPanel(activeScenarioId, false);
  }
  syncChaosState();
  refreshHistory();
}

async function updateSidebarLanguage() {
  if (!cachedScenarios) {
    try {
      const res = await fetch('/api/v1/incidents/scenarios');
      if (res.ok) cachedScenarios = await res.json();
    } catch (_) {
      return;
    }
  }
  if (!cachedScenarios) return;

  cachedScenarios.forEach(sc => {
    const card = document.querySelector(`[data-scenario="${sc.id}"]`);
    if (!card) return;

    const titleEl = card.querySelector('.incident-name');
    const catEl = card.querySelector('.incident-category');
    const descEl = card.querySelector('.incident-description');
    const btnEl = card.querySelector('.simulate-btn');

    if (titleEl) titleEl.textContent = (currentLang === 'en' && sc.title_en) ? sc.title_en : sc.title;
    if (catEl) catEl.innerHTML = `<span>📂</span> ${(currentLang === 'en' && sc.category_en) ? sc.category_en : sc.category}`;
    if (descEl) descEl.textContent = (currentLang === 'en' && sc.description_en) ? sc.description_en : sc.description;
    if (btnEl && !btnEl.classList.contains('running')) {
      btnEl.textContent = t('btn_simulate');
    }
  });

  const sidebarHeader = document.querySelector('.sidebar-header');
  if (sidebarHeader) {
    sidebarHeader.innerHTML = `<span>🎯</span> ${t('sidebar_title')} (${cachedScenarios.length})`;
  }
}

// ── Tab Navigation ─────────────────────────────────────────
function switchDashboardTab(tabName) {
  currentTab = tabName;
  const simTabBtn = document.getElementById('tab-btn-sim');
  const histTabBtn = document.getElementById('tab-btn-hist');
  const simView = document.getElementById('view-simulation');
  const histView = document.getElementById('view-history');

  if (tabName === 'history') {
    if (simTabBtn) { simTabBtn.classList.remove('active'); simTabBtn.setAttribute('aria-selected', 'false'); }
    if (histTabBtn) { histTabBtn.classList.add('active'); histTabBtn.setAttribute('aria-selected', 'true'); }
    if (simView) simView.style.display = 'none';
    if (histView) histView.style.display = 'block';
    refreshHistory();
    history.replaceState(null, null, '#history');
  } else {
    if (histTabBtn) { histTabBtn.classList.remove('active'); histTabBtn.setAttribute('aria-selected', 'false'); }
    if (simTabBtn) { simTabBtn.classList.add('active'); simTabBtn.setAttribute('aria-selected', 'true'); }
    if (histView) histView.style.display = 'none';
    if (simView) simView.style.display = 'block';
    history.replaceState(null, null, '#simulation');
  }
}

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

function escapeHtml(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ── Start Simulation ───────────────────────────────────────
async function startSimulation(scenarioId) {
  if (activeScenarioId && activeScenarioId !== scenarioId) {
    alert(currentLang === 'en'
      ? 'A simulation is already in progress. Complete or cancel it first.'
      : 'Já existe uma simulação ativa. Conclua ou cancele a simulação em andamento primeiro.');
    return;
  }

  // Ensure we are on the simulation tab
  switchDashboardTab('simulation');

  try {
    const res = await fetch('/api/v1/incidents/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario_id: scenarioId })
    });

    if (!res.ok) throw new Error(await res.text());

    activeScenarioId = scenarioId;
    simulationStartTime = Date.now();
    elapsedSeconds = 0;
    selectedSolution = null;

    // Header status update
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    if (statusDot) statusDot.classList.add('incident');
    if (statusText) statusText.textContent = t('status_sim_active');

    // Update sidebar buttons
    document.querySelectorAll('.incident-card').forEach(card => {
      card.classList.remove('active');
      const btn = card.querySelector('.simulate-btn');
      if (btn) {
        btn.disabled = false;
        btn.textContent = t('btn_simulate');
        btn.classList.remove('running');
      }
    });

    const activeCard = document.querySelector(`[data-scenario="${scenarioId}"]`);
    if (activeCard) {
      activeCard.classList.add('active');
      const btn = activeCard.querySelector('.simulate-btn');
      if (btn) {
        btn.disabled = true;
        btn.textContent = t('btn_running');
        btn.classList.add('running');
      }
    }

    // Render active panel
    renderSimulationPanel(scenarioId, true);

    // Timers
    startElapsedTimer();
    startPolling();

    // Scroll to top of main content
    const mainContent = document.querySelector('.main-content');
    if (mainContent) mainContent.scrollTop = 0;

  } catch (err) {
    alert(`Erro ao iniciar simulação: ${err.message}`);
  }
}

// ── Timers & Polling ───────────────────────────────────────
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
      if (timeEl) timeEl.textContent = `${formatTime(state.investigation_at)} — ${t('timeline_investigating_sub')}`;
    }
    if (phaseLabel) phaseLabel.textContent = t('sim_phase_investigating');
  } else if (phase === 'detected') {
    const dot = document.getElementById('dot-detected');
    if (dot && !dot.classList.contains('done')) {
      dot.classList.remove('pending');
      dot.classList.add('active');
    }
    if (phaseLabel) phaseLabel.textContent = t('sim_phase_detected');
  }
}

// ── Render Simulation Panel ────────────────────────────────
function renderSimulationPanel(scenarioId, isNew = false) {
  const panels = document.getElementById('simulation-panels');
  const emptyState = document.getElementById('empty-state');

  if (emptyState) emptyState.style.display = 'none';
  if (!panels) return;

  fetch('/api/v1/incidents/scenarios')
    .then(r => r.json())
    .then(scenarios => {
      cachedScenarios = scenarios;
      const scenario = scenarios.find(s => s.id === scenarioId);
      if (!scenario) return;

      const title = (currentLang === 'en' && scenario.title_en) ? scenario.title_en : scenario.title;
      const desc = (currentLang === 'en' && scenario.description_en) ? scenario.description_en : scenario.description;
      const symptoms = (currentLang === 'en' && scenario.symptoms_en) ? scenario.symptoms_en : scenario.symptoms;

      // Fisher-Yates shuffle if new
      let solutions = [...scenario.solutions];
      if (isNew || !window._lastShuffledSolutions || window._lastScenarioId !== scenarioId) {
        for (let i = solutions.length - 1; i > 0; i--) {
          const j = Math.floor(Math.random() * (i + 1));
          [solutions[i], solutions[j]] = [solutions[j], solutions[i]];
        }
        window._lastShuffledSolutions = solutions;
        window._lastScenarioId = scenarioId;
      } else {
        solutions = window._lastShuffledSolutions;
      }

      const optionLetters = ['A', 'B', 'C', 'D', 'E'];

      panels.innerHTML = `
        <div class="simulation-panel visible" id="active-simulation">
          <div class="simulation-header">
            <div class="simulation-title">
              <span>${scenario.icon}</span>
              <span>${title}</span>
              <span class="severity-badge ${severityClass(scenario.severity)}">${scenario.severity}</span>
            </div>
            <button class="cancel-btn" onclick="cancelSimulation()">${t('btn_cancel_sim')}</button>
          </div>

          <div class="simulation-overview-card">
            <div class="section-label">${t('sim_overview')}</div>
            <div class="simulation-full-description">${desc}</div>
          </div>

          <div class="elapsed-timer" id="elapsed-display">${formatTime(elapsedSeconds)}</div>
          <div class="phase-label" id="phase-label">${t('sim_phase_waiting')}</div>

          <div class="section-label">${t('sim_symptoms_label')}</div>
          <ul class="symptoms-list">
            ${symptoms.map(s => `<li>⚠️ ${s}</li>`).join('')}
          </ul>

          <div class="section-label">${t('sim_timeline_label')}</div>
          <div class="timeline" id="incident-timeline">
            <div class="timeline-item">
              <div class="timeline-dot done" id="dot-start">✓</div>
              <div class="timeline-content">
                <div class="timeline-step-name">${t('timeline_start')}</div>
                <div class="timeline-step-time" id="time-start">${t('timeline_start_sub')}</div>
              </div>
            </div>
            <div class="timeline-item">
              <div class="timeline-dot pending" id="dot-detected">○</div>
              <div class="timeline-content">
                <div class="timeline-step-name">${t('timeline_detected')}</div>
                <div class="timeline-step-time" id="time-detected">~${formatTime(scenario.detection_delay_seconds)}</div>
              </div>
            </div>
            <div class="timeline-item">
              <div class="timeline-dot pending" id="dot-investigating">○</div>
              <div class="timeline-content">
                <div class="timeline-step-name">${t('timeline_investigating')}</div>
                <div class="timeline-step-time" id="time-investigating">~${formatTime(scenario.investigation_delay_seconds)}</div>
              </div>
            </div>
            <div class="timeline-item">
              <div class="timeline-dot pending" id="dot-solved">⭐</div>
              <div class="timeline-content">
                <div class="timeline-step-name">${t('timeline_solved')}</div>
                <div class="timeline-step-time" id="time-solved">${t('timeline_solved_waiting')}</div>
              </div>
            </div>
          </div>

          <div class="section-label">
            ${t('sim_solutions_label')}
            <span class="hint">${t('sim_solutions_hint')}</span>
          </div>

          <div class="solutions-grid" id="solutions-grid">
            ${solutions.map((sol, idx) => {
              const label = (currentLang === 'en' && sol.label_en) ? sol.label_en : sol.label;
              return `
                <label class="solution-option" id="opt-${sol.id}" onclick="selectSolution('${sol.id}')">
                  <input type="radio" name="solution" value="${sol.id}" id="radio-${sol.id}">
                  <span class="solution-badge">${optionLetters[idx] || (idx + 1)}</span>
                  <span class="solution-label">${label}</span>
                </label>
              `;
            }).join('')}
          </div>

          <button class="apply-btn" id="apply-btn" disabled onclick="applySolution()">
            ${t('btn_apply_solution')}
          </button>

          <div class="result-banner" id="result-banner"></div>
        </div>
      `;
    })
    .catch(err => {
      panels.innerHTML = `<div style="padding:24px;color:var(--sev1)">Error: ${err.message}</div>`;
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
    applyBtn.textContent = t('btn_applying');
  }

  try {
    const res = await fetch('/api/v1/incidents/solve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario_id: activeScenarioId, solution_id: selectedSolution })
    });

    const result = await res.json();

    document.querySelectorAll('.solution-option').forEach(opt => {
      opt.classList.remove('selected');
      const radio = opt.querySelector('input');
      if (radio) radio.disabled = true;
    });

    const chosenOpt = document.getElementById(`opt-${selectedSolution}`);
    if (chosenOpt) {
      chosenOpt.classList.add(result.correct ? 'correct' : 'incorrect');
    }

    const solvedDot = document.getElementById('dot-solved');
    if (solvedDot) {
      solvedDot.classList.remove('pending');
      solvedDot.classList.add(result.correct ? 'done' : 'active');
      solvedDot.textContent = result.correct ? '✓' : '✕';
    }

    const solvedTime = document.getElementById('time-solved');
    if (solvedTime) {
      const outcomeText = result.correct
        ? (currentLang === 'en' ? 'Successfully mitigated' : 'Mitigado com sucesso')
        : (currentLang === 'en' ? 'Mitigation failed' : 'Falha na mitigação');
      solvedTime.textContent = `MTTR: ${formatTime(result.mttr_seconds)} (${outcomeText})`;
    }

    const explanation = (currentLang === 'en' && result.explanation_en)
      ? result.explanation_en
      : result.explanation;

    const banner = document.getElementById('result-banner');
    if (banner) {
      banner.classList.remove('correct', 'incorrect');
      banner.classList.add(result.correct ? 'correct' : 'incorrect', 'visible');
      banner.innerHTML = `
        <div style="font-weight:700;font-size:0.95rem;display:flex;align-items:center;gap:8px">
          <span>${result.correct ? t('result_correct') : t('result_incorrect')}</span>
        </div>
        <div class="result-explanation-text">${explanation}</div>
        <div class="result-metrics">
          <div class="result-metric">
            <div class="result-metric-label">${t('result_mttd_label')}</div>
            <div class="result-metric-value">${formatTime(result.mttd_seconds)}</div>
          </div>
          <div class="result-metric">
            <div class="result-metric-label">${t('result_mttr_label')}</div>
            <div class="result-metric-value">${formatTime(result.mttr_seconds)}</div>
          </div>
          <div class="result-metric">
            <div class="result-metric-label">${t('result_status_label')}</div>
            <div class="result-metric-value">${result.correct ? t('status_resolved') : t('status_unresolved')}</div>
          </div>
        </div>
        <div>
          <button class="view-history-shortcut-btn" onclick="switchDashboardTab('history')">
            ${t('btn_view_in_history')}
          </button>
        </div>
      `;
    }

    const phaseLabel = document.getElementById('phase-label');
    if (phaseLabel) {
      phaseLabel.textContent = result.correct ? t('phase_success') : t('phase_failure');
    }

    clearInterval(elapsedInterval);
    clearInterval(pollingInterval);
    resetSidebar();

    setTimeout(refreshHistory, 300);

  } catch (err) {
    alert(`Erro: ${err.message}`);
    if (applyBtn) {
      applyBtn.disabled = false;
      applyBtn.textContent = t('btn_apply_solution');
    }
  }
}

// ── Cancel Simulation ──────────────────────────────────────
async function cancelSimulation() {
  const confirmMsg = currentLang === 'en'
    ? 'Are you sure you want to cancel the active simulation?'
    : 'Deseja realmente cancelar a simulação atual?';
  if (!confirm(confirmMsg)) return;

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
  if (statusText) statusText.textContent = isChaosMonkeyActive ? t('status_degraded') : t('status_all_ok');

  document.querySelectorAll('.incident-card').forEach(card => {
    card.classList.remove('active');
    const btn = card.querySelector('.simulate-btn');
    if (btn) {
      btn.disabled = false;
      btn.textContent = t('btn_simulate');
      btn.classList.remove('running');
    }
  });
}

// ── Clear History ──────────────────────────────────────────
async function confirmClearHistory() {
  const confirmMsg = currentLang === 'en'
    ? 'Are you sure you want to clear all simulation history records?'
    : 'Tem certeza de que deseja limpar todo o histórico de simulações?';
  if (!confirm(confirmMsg)) return;

  try {
    const res = await fetch('/api/v1/incidents/history/clear', { method: 'POST' });
    if (!res.ok) throw new Error(await res.text());
    await refreshHistory();
  } catch (err) {
    alert(`Erro ao limpar histórico: ${err.message}`);
  }
}

// ── SRE Analytics, Charts and KPI Calculations ─────────────
async function refreshHistory() {
  try {
    const res = await fetch('/api/v1/incidents/history');
    if (!res.ok) return;
    const history = await res.json();

    const total = history.length;
    const correctCount = history.filter(h => h.correct).length;
    const incorrectCount = total - correctCount;
    const successRate = total > 0 ? Math.round((correctCount / total) * 100) : 0;

    // Update tab badge count
    const tabBadge = document.getElementById('tab-history-badge');
    if (tabBadge) tabBadge.textContent = total;

    // MTTD and MTTR averages
    const avgMttd = total > 0
      ? (history.reduce((acc, h) => acc + (h.mttd_seconds || 0), 0) / total)
      : 0;
    const avgMttr = total > 0
      ? (history.reduce((acc, h) => acc + (h.mttr_seconds || 0), 0) / total)
      : 0;

    const sev1 = history.filter(h => h.severity === 'SEV-1').length;
    const sev2 = history.filter(h => h.severity === 'SEV-2').length;
    const sev3 = history.filter(h => h.severity === 'SEV-3').length;

    // 1. KPI Cards
    const rateEl = document.getElementById('kpi-success-rate');
    const subRateEl = document.getElementById('kpi-success-sub');
    const badgeRateEl = document.getElementById('kpi-badge-rate');
    const ratePathEl = document.getElementById('kpi-rate-path');

    if (rateEl) rateEl.textContent = `${successRate}%`;
    if (subRateEl) {
      subRateEl.textContent = currentLang === 'en'
        ? `${correctCount} correct of ${total}`
        : `${correctCount} corretos de ${total}`;
    }

    if (badgeRateEl) {
      badgeRateEl.className = 'kpi-badge';
      if (total === 0) {
        badgeRateEl.textContent = t('badge_no_data');
      } else if (successRate >= 80) {
        badgeRateEl.textContent = t('badge_excellent');
        badgeRateEl.classList.add('good');
      } else if (successRate >= 50) {
        badgeRateEl.textContent = t('badge_good');
        badgeRateEl.classList.add('warning');
      } else {
        badgeRateEl.textContent = t('badge_poor');
        badgeRateEl.classList.add('danger');
      }
    }

    if (ratePathEl) {
      ratePathEl.setAttribute('stroke-dasharray', `${successRate}, 100`);
      if (successRate >= 80) {
        ratePathEl.style.stroke = '#3fb950';
      } else if (successRate >= 50) {
        ratePathEl.style.stroke = '#d29922';
      } else {
        ratePathEl.style.stroke = '#f85149';
      }
    }

    const avgMttdEl = document.getElementById('kpi-avg-mttd');
    if (avgMttdEl) avgMttdEl.textContent = formatTime(avgMttd);

    const avgMttrEl = document.getElementById('kpi-avg-mttr');
    if (avgMttrEl) avgMttrEl.textContent = formatTime(avgMttr);

    const mttrPill = document.getElementById('kpi-mttr-pill');
    if (mttrPill) {
      if (avgMttr > 0 && avgMttr <= 60) {
        mttrPill.textContent = currentLang === 'en' ? 'Target Met (< 01:00)' : 'Meta Atingida (< 01:00)';
        mttrPill.style.color = '#3fb950';
      } else {
        mttrPill.textContent = currentLang === 'en' ? 'Target < 01:00' : 'Meta < 01:00';
        mttrPill.style.color = '';
      }
    }

    const totalSimsEl = document.getElementById('kpi-total-sims');
    if (totalSimsEl) totalSimsEl.textContent = total;

    const sevBreakdownEl = document.getElementById('kpi-sev-breakdown');
    if (sevBreakdownEl) {
      sevBreakdownEl.textContent = `SEV-1: ${sev1} · SEV-2: ${sev2} · SEV-3: ${sev3}`;
    }

    // 2. Charts
    renderRatioBar(correctCount, incorrectCount, total);
    renderMttrSparkline(history, avgMttr);

    // 3. Table
    renderHistoryTable(history);

  } catch (err) {
    console.error('Erro ao atualizar histórico:', err);
  }
}

function renderRatioBar(correct, incorrect, total) {
  const greenBar = document.getElementById('ratio-green-bar');
  const redBar = document.getElementById('ratio-red-bar');
  const greenLabel = document.getElementById('ratio-green-label');
  const redLabel = document.getElementById('ratio-red-label');

  if (!greenBar || !redBar) return;

  if (total === 0) {
    greenBar.style.width = '0%';
    redBar.style.width = '0%';
    if (greenLabel) greenLabel.textContent = `0% ${t('legend_correct')} (0)`;
    if (redLabel) redLabel.textContent = `0% ${t('legend_incorrect')} (0)`;
    return;
  }

  const greenPct = Math.round((correct / total) * 100);
  const redPct = 100 - greenPct;

  greenBar.style.width = `${greenPct}%`;
  redBar.style.width = `${redPct}%`;

  if (greenLabel) greenLabel.textContent = `${greenPct}% ${t('legend_correct')} (${correct})`;
  if (redLabel) redLabel.textContent = `${redPct}% ${t('legend_incorrect')} (${incorrect})`;
}

function renderMttrSparkline(history, avgMttr) {
  const svg = document.getElementById('mttr-spark-chart');
  const avgLabel = document.getElementById('chart-avg-line-label');
  if (!svg) return;

  if (avgLabel) avgLabel.textContent = `${t('chart_avg_prefix')} ${formatTime(avgMttr)}`;

  const recent = [...history].reverse().slice(-12);

  if (recent.length === 0) {
    svg.innerHTML = `
      <text x="250" y="48" text-anchor="middle" fill="#6e7681" font-size="11" font-family="'JetBrains Mono', monospace">
        ${t('chart_empty')}
      </text>
    `;
    return;
  }

  const maxMttr = Math.max(...recent.map(h => h.mttr_seconds || 0), 60);
  const svgWidth = 500;
  const svgHeight = 90;
  const paddingX = 30;
  const paddingY = 16;
  const chartW = svgWidth - paddingX * 2;
  const chartH = svgHeight - paddingY * 2;

  const avgY = svgHeight - paddingY - (avgMttr / maxMttr) * chartH;
  let elements = `
    <line x1="${paddingX}" y1="${avgY}" x2="${svgWidth - paddingX}" y2="${avgY}"
          stroke="#d29922" stroke-dasharray="4,4" stroke-width="1.2" opacity="0.7"/>
  `;

  const barWidth = Math.max(12, Math.min(28, (chartW / recent.length) - 8));
  const step = recent.length > 1 ? (chartW - barWidth) / (recent.length - 1) : 0;

  recent.forEach((item, idx) => {
    const val = item.mttr_seconds || 0;
    const h = Math.max(4, (val / maxMttr) * chartH);
    const x = recent.length === 1 ? (svgWidth / 2 - barWidth / 2) : paddingX + idx * step;
    const y = svgHeight - paddingY - h;
    const color = item.correct ? '#3fb950' : '#f85149';

    elements += `
      <g class="chart-bar-group">
        <title>#${item.id} - ${item.scenario_title} | MTTR: ${formatTime(val)}</title>
        <rect x="${x}" y="${y}" width="${barWidth}" height="${h}" rx="3"
              fill="${color}" opacity="0.85" />
        <text x="${x + barWidth / 2}" y="${y - 4}" text-anchor="middle"
              fill="#c9d1d9" font-size="9" font-family="'JetBrains Mono', monospace">
          ${formatTime(val)}
        </text>
        <text x="${x + barWidth / 2}" y="${svgHeight - 2}" text-anchor="middle"
              fill="#6e7681" font-size="8.5" font-family="'JetBrains Mono', monospace">
          #${item.id}
        </text>
      </g>
    `;
  });

  svg.innerHTML = elements;
}

function renderHistoryTable(history) {
  const tbody = document.getElementById('history-body');
  if (!tbody) return;

  if (history.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="history-empty">
          ${t('table_empty')}
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = history.map(item => {
    const badgeClass = item.correct ? 'badge-correct' : 'badge-incorrect';
    const badgeText = item.correct ? `✓ ${t('outcome_correct')}` : `✕ ${t('outcome_incorrect')}`;
    const title = (currentLang === 'en' && item.scenario_title_en) ? item.scenario_title_en : item.scenario_title;
    const solution = (currentLang === 'en' && item.solution_chosen_en) ? item.solution_chosen_en : item.solution_chosen;

    return `
      <tr>
        <td><strong>#${item.id}</strong></td>
        <td>
          <div class="table-scenario-cell">
            <span>${item.icon || '🚨'}</span>
            <span>${escapeHtml(title)}</span>
          </div>
        </td>
        <td><span class="severity-badge ${severityClass(item.severity)}">${item.severity}</span></td>
        <td><span class="mono-time">${formatTime(item.mttd_seconds)}</span></td>
        <td><span class="mono-time bold">${formatTime(item.mttr_seconds)}</span></td>
        <td class="solution-chosen-cell" title="${escapeHtml(solution || '')}">${escapeHtml(solution || '-')}</td>
        <td><span class="result-badge ${badgeClass}">${badgeText}</span></td>
      </tr>
    `;
  }).join('');
}

// ── Chaos Monkey Controller ───────────────────────────────
async function syncChaosState(manual = false) {
  try {
    const res = await fetch('/api/v1/chaos/status');
    if (!res.ok) return;
    const data = await res.json();
    applyChaosUI(data.simulate_500, data);

    await Promise.all([
      fetchChaosEvents(),
      fetchChaosHistory()
    ]);
  } catch (e) {
    console.warn('Chaos sync error:', e);
  }
}

function applyChaosUI(active, telemetry) {
  isChaosMonkeyActive = Boolean(active);
  const btn = document.getElementById('chaos-monkey-toggle');
  const txt = document.getElementById('chaos-btn-text');
  const dot = document.getElementById('status-dot');
  const statusTxt = document.getElementById('status-text');
  const liveIndicator = document.getElementById('chaos-live-indicator');

  if (btn && txt) {
    if (isChaosMonkeyActive) {
      btn.classList.add('active');
      btn.style.background = 'rgba(248, 81, 73, 0.18)';
      btn.style.borderColor = '#f85149';
      btn.style.color = '#ff7b72';
      txt.textContent = t('chaos_btn_active');
      btn.title = t('chaos_btn_title_active');
      if (dot && !activeScenarioId) {
        dot.style.background = '#f85149';
        dot.style.boxShadow = '0 0 10px #f85149';
      }
      if (statusTxt && !activeScenarioId) statusTxt.textContent = t('status_degraded');
    } else {
      btn.classList.remove('active');
      btn.style.background = 'rgba(255, 255, 255, 0.05)';
      btn.style.borderColor = '#30363d';
      btn.style.color = '#8b949e';
      txt.textContent = t('chaos_btn_off');
      btn.title = t('chaos_btn_title_off');
      if (dot && !activeScenarioId) {
        dot.style.background = '#3fb950';
        dot.style.boxShadow = '0 0 8px #3fb950';
      }
      if (statusTxt && !activeScenarioId) statusTxt.textContent = t('status_all_ok');
    }
  }

  if (liveIndicator) {
    if (isChaosMonkeyActive) {
      liveIndicator.classList.add('chaos-active');
      liveIndicator.innerHTML = `<span class="pulse-dot"></span> ${currentLang === 'en' ? 'INJECTING 500' : 'INJETANDO 500'}`;
    } else {
      liveIndicator.classList.remove('chaos-active');
      liveIndicator.innerHTML = '<span class="pulse-dot"></span> LIVE';
    }
  }

  if (telemetry) {
    const badge = document.getElementById('chaos-status-badge');
    const mainState = document.getElementById('chaos-main-state');
    const durSub = document.getElementById('chaos-duration-sub');
    const faultTag = document.getElementById('chaos-fault-tag');
    const totalInj = document.getElementById('chaos-total-injections');
    const sessInj = document.getElementById('chaos-session-injections');
    const sessSub = document.getElementById('chaos-session-sub');
    const sessIdPill = document.getElementById('chaos-session-id-pill');
    const epCount = document.getElementById('chaos-endpoints-count');
    const epList = document.getElementById('chaos-endpoints-list');

    if (totalInj) totalInj.textContent = telemetry.total_injections_all_time ?? 0;

    if (isChaosMonkeyActive) {
      if (badge) {
        badge.textContent = t('chaos_badge_active');
        badge.style.background = 'rgba(248,81,73,0.2)';
        badge.style.color = '#ff7b72';
      }
      if (mainState) {
        mainState.textContent = 'HTTP 500';
        mainState.style.color = '#ff7b72';
      }
      const secs = Math.round(telemetry.active_duration_seconds || 0);
      if (durSub) durSub.textContent = `${t('chaos_dur_running')} ${formatTime(secs)}`;
      if (faultTag) {
        faultTag.textContent = t('chaos_tag_failing');
        faultTag.style.background = 'rgba(248,81,73,0.15)';
        faultTag.style.color = '#ff7b72';
      }
    } else {
      if (badge) {
        badge.textContent = t('chaos_badge_inactive');
        badge.style.background = 'rgba(46,160,67,0.15)';
        badge.style.color = '#3fb950';
      }
      if (mainState) {
        mainState.textContent = t('chaos_main_state_normal');
        mainState.style.color = '#3fb950';
      }
      if (durSub) durSub.textContent = t('chaos_dur_inactive');
      if (faultTag) {
        faultTag.textContent = t('chaos_tag_healthy');
        faultTag.style.background = 'rgba(255,255,255,0.05)';
        faultTag.style.color = '#8b949e';
      }
    }

    if (telemetry.session) {
      if (sessInj) sessInj.textContent = telemetry.session.injected_count;
      if (sessSub) {
        sessSub.textContent = currentLang === 'en'
          ? `${telemetry.session.injected_count} faults in this session`
          : `${telemetry.session.injected_count} falhas nesta sessão`;
      }
      if (sessIdPill) {
        sessIdPill.textContent = currentLang === 'en'
          ? `Session #${telemetry.session.session_id}`
          : `Sessão #${telemetry.session.session_id}`;
      }

      const eps = telemetry.session.affected_endpoints || {};
      const keys = Object.keys(eps);
      if (epCount) epCount.textContent = keys.length;
      if (epList) {
        if (keys.length > 0) {
          epList.textContent = keys.map(k => `${k} (${eps[k]})`).join(', ');
        } else {
          epList.textContent = t('chaos_kpi_targets_waiting');
        }
      }
    } else {
      if (sessInj) sessInj.textContent = 0;
      if (sessSub) sessSub.textContent = t('chaos_kpi_session_empty');
      if (sessIdPill) sessIdPill.textContent = currentLang === 'en' ? 'Session #--' : 'Sessão #--';
      if (epCount) epCount.textContent = 0;
      if (epList) epList.textContent = t('chaos_kpi_targets_none');
    }
  }
}

async function fetchChaosEvents() {
  try {
    const res = await fetch('/api/v1/chaos/events?limit=40');
    if (!res.ok) return;
    const events = await res.json();
    renderChaosTerminal(events);
  } catch (e) {
    console.error('Error fetching chaos events:', e);
  }
}

function renderChaosTerminal(events) {
  const container = document.getElementById('chaos-terminal-body');
  const countBadge = document.getElementById('terminal-event-count');
  if (!container) return;

  if (countBadge) {
    countBadge.textContent = currentLang === 'en' ? `${events.length} events` : `${events.length} eventos`;
  }

  if (!events || events.length === 0) {
    container.innerHTML = `
      <div class="terminal-line placeholder">
        <span class="term-time">[--:--:--]</span>
        <span class="term-dim">${t('terminal_placeholder')}</span>
      </div>`;
    return;
  }

  container.innerHTML = events.map(e => {
    let badgeClass = 'activated';
    let badgeLabel = e.event_type;
    if (e.event_type === 'ACTIVATED') {
      badgeClass = 'activated';
      badgeLabel = currentLang === 'en' ? 'ACTIVATED' : 'ATIVADO';
    } else if (e.event_type === 'FAULT_INJECTED') {
      badgeClass = 'fault';
      badgeLabel = currentLang === 'en' ? '500 INJECTED' : '500 INJETADO';
    } else if (e.event_type === 'DEACTIVATED') {
      badgeClass = 'deactivated';
      badgeLabel = currentLang === 'en' ? 'DEACTIVATED' : 'DESATIVADO';
    }

    return `
      <div class="terminal-line">
        <span class="term-time">[${e.timestamp}]</span>
        <span class="term-badge ${badgeClass}">${badgeLabel}</span>
        <span class="term-msg">${escapeHtml(e.message)}</span>
      </div>
    `;
  }).join('');
}

async function fetchChaosHistory() {
  try {
    const res = await fetch('/api/v1/chaos/history');
    if (!res.ok) return;
    const history = await res.json();
    renderChaosSessions(history);
  } catch (e) {
    console.error('Error fetching chaos history:', e);
  }
}

function renderChaosSessions(sessions) {
  const tbody = document.getElementById('chaos-sessions-body');
  const countBadge = document.getElementById('sessions-count-badge');
  if (!tbody) return;

  if (countBadge) {
    countBadge.textContent = currentLang === 'en' ? `${sessions.length} sessions` : `${sessions.length} sessões`;
  }

  if (!sessions || sessions.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="history-empty">${t('sessions_empty')}</td></tr>`;
    return;
  }

  tbody.innerHTML = sessions.map(s => {
    const statusBadge = s.active
      ? `<span class="session-status-badge active">${t('session_active')}</span>`
      : `<span class="session-status-badge completed">${t('session_completed')}</span>`;

    const eps = s.affected_endpoints ? Object.keys(s.affected_endpoints) : [];
    const epDisplay = eps.length > 0 ? eps.map(k => `${k} (${s.affected_endpoints[k]})`).join(', ') : 'None';
    const durDisplay = s.duration_seconds != null ? `${s.duration_seconds}s` : '--';

    return `
      <tr>
        <td><strong>#${s.session_id}</strong></td>
        <td>${s.started_at}</td>
        <td>${durDisplay}</td>
        <td><strong style="color:${s.injected_count > 0 ? '#ff7b72' : '#8b949e'}">${s.injected_count}</strong></td>
        <td style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#58a6ff">${escapeHtml(epDisplay)}</td>
        <td>${statusBadge}</td>
      </tr>
    `;
  }).join('');
}

async function toggleChaosMonkey() {
  const target = !isChaosMonkeyActive;
  const btn = document.getElementById('chaos-monkey-toggle');
  if (btn) btn.style.opacity = '0.5';

  try {
    const res = await fetch('/api/v1/chaos/500?enable=' + target, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!res.ok) throw new Error('Status ' + res.status);
    const data = await res.json();
    applyChaosUI(data.simulate_500, data);
    renderChaosToast(data.simulate_500);
    await Promise.all([fetchChaosEvents(), fetchChaosHistory()]);
  } catch (err) {
    alert('Erro: ' + err.message);
  } finally {
    if (btn) btn.style.opacity = '1';
  }
}

async function confirmClearChaosHistory() {
  const confirmMsg = currentLang === 'en'
    ? 'Are you sure you want to clear all Chaos Monkey sessions and audit events?'
    : 'Deseja limpar todo o histórico de sessões e auditoria de eventos do Chaos Monkey?';
  if (!confirm(confirmMsg)) return;

  try {
    const res = await fetch('/api/v1/chaos/history/clear', { method: 'POST' });
    if (!res.ok) throw new Error('Failed to clear');
    await syncChaosState(true);
  } catch (e) {
    alert('Error: ' + e.message);
  }
}

function renderChaosToast(active) {
  const old = document.getElementById('chaos-toast-box');
  if (old) old.remove();

  const toast = document.createElement('div');
  toast.id = 'chaos-toast-box';
  toast.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:99999;padding:14px 22px;border-radius:10px;font-size:0.86rem;font-weight:600;display:flex;align-items:center;gap:12px;box-shadow:0 10px 35px rgba(0,0,0,0.7);transition:all 0.3s ease;';

  if (active) {
    toast.style.background = '#3d1214';
    toast.style.color = '#ff7b72';
    toast.style.border = '1px solid #f85149';
    toast.innerHTML = `<span style="font-size:1.3rem">🐒💥</span> <div><div>${t('chaos_toast_active_title')}</div><div style="font-size:0.75rem;font-weight:400;color:#e6edf3">${t('chaos_toast_active_desc')}</div></div>`;
  } else {
    toast.style.background = '#0e2a1b';
    toast.style.color = '#7ee787';
    toast.style.border = '1px solid #2ea043';
    toast.innerHTML = `<span style="font-size:1.3rem">✅</span> <div><div>${t('chaos_toast_inactive_title')}</div><div style="font-size:0.75rem;font-weight:400;color:#e6edf3">${t('chaos_toast_inactive_desc')}</div></div>`;
  }

  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(15px)';
    setTimeout(() => toast.remove(), 350);
  }, 4500);
}

// ── Polling & Lifecycle Initialization ──────────────────────
function startChaosPolling() {
  if (chaosPollTimer) clearInterval(chaosPollTimer);
  chaosPollTimer = setInterval(() => {
    syncChaosState();
  }, isChaosMonkeyActive ? 2000 : 5000);
}

document.addEventListener('DOMContentLoaded', () => {
  // Check URL hash for tab navigation
  if (window.location.hash === '#history') {
    switchDashboardTab('history');
  } else {
    switchDashboardTab('simulation');
  }

  // Initialize Language
  setLanguage(currentLang);

  // Initialize Chaos & Polling
  syncChaosState();
  startChaosPolling();
});
