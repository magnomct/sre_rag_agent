/**
 * SRE Incident Simulation Dashboard — JavaScript Controller v3.2
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
  const warroomTabBtn = document.getElementById('tab-btn-warroom');
  const conceptsTabBtn = document.getElementById('tab-btn-concepts');
  
  const simView = document.getElementById('view-simulation');
  const histView = document.getElementById('view-history');
  const warroomView = document.getElementById('view-warroom');
  const conceptsView = document.getElementById('view-concepts');

  // Remove active from all
  if (simTabBtn) { simTabBtn.classList.remove('active'); simTabBtn.setAttribute('aria-selected', 'false'); }
  if (histTabBtn) { histTabBtn.classList.remove('active'); histTabBtn.setAttribute('aria-selected', 'false'); }
  if (warroomTabBtn) { warroomTabBtn.classList.remove('active'); warroomTabBtn.setAttribute('aria-selected', 'false'); }
  if (conceptsTabBtn) { conceptsTabBtn.classList.remove('active'); conceptsTabBtn.setAttribute('aria-selected', 'false'); }
  
  if (simView) simView.style.display = 'none';
  if (histView) histView.style.display = 'none';
  if (warroomView) warroomView.style.display = 'none';
  if (conceptsView) conceptsView.style.display = 'none';

  const sidebar = document.querySelector('.sidebar');
  const mainContent = document.querySelector('.main-content');
  if (mainContent) mainContent.scrollTop = 0;

  if (tabName === 'history') {
    if (histTabBtn) { histTabBtn.classList.add('active'); histTabBtn.setAttribute('aria-selected', 'true'); }
    if (histView) histView.style.display = 'block';
    if (sidebar) sidebar.style.display = 'none';
    refreshHistory();
    history.replaceState(null, null, '#history');
  } else if (tabName === 'warroom') {
    if (warroomTabBtn) { warroomTabBtn.classList.add('active'); warroomTabBtn.setAttribute('aria-selected', 'true'); }
    if (warroomView) warroomView.style.display = 'block';
    if (sidebar) sidebar.style.display = 'none';
    history.replaceState(null, null, '#warroom');
  } else if (tabName === 'concepts') {
    if (conceptsTabBtn) { conceptsTabBtn.classList.add('active'); conceptsTabBtn.setAttribute('aria-selected', 'true'); }
    if (conceptsView) conceptsView.style.display = 'block';
    if (sidebar) sidebar.style.display = 'none';
    loadConceptsCatalog();
    history.replaceState(null, null, '#concepts');
  } else {
    // simulation
    if (simTabBtn) { simTabBtn.classList.add('active'); simTabBtn.setAttribute('aria-selected', 'true'); }
    if (simView) simView.style.display = 'block';
    if (sidebar) sidebar.style.display = '';
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
      <text x="250" y="48" text-anchor="middle" fill="#6e7681" font-size="12" font-family="'JetBrains Mono', monospace">
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
              fill="#c9d1d9" font-size="10.5" font-family="'JetBrains Mono', monospace">
          ${formatTime(val)}
        </text>
        <text x="${x + barWidth / 2}" y="${svgHeight - 2}" text-anchor="middle"
              fill="#6e7681" font-size="9.5" font-family="'JetBrains Mono', monospace">
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
        <td style="font-family:'JetBrains Mono',monospace;font-size:0.8rem;color:#58a6ff">${escapeHtml(epDisplay)}</td>
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
    toast.innerHTML = `<span style="font-size:1.3rem">🐒💥</span> <div><div>${t('chaos_toast_active_title')}</div><div style="font-size:0.84rem;font-weight:400;color:#e6edf3">${t('chaos_toast_active_desc')}</div></div>`;
  } else {
    toast.style.background = '#0e2a1b';
    toast.style.color = '#7ee787';
    toast.style.border = '1px solid #2ea043';
    toast.innerHTML = `<span style="font-size:1.3rem">✅</span> <div><div>${t('chaos_toast_inactive_title')}</div><div style="font-size:0.84rem;font-weight:400;color:#e6edf3">${t('chaos_toast_inactive_desc')}</div></div>`;
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

// --- New War Room Logic ---
let activeWarroomSimId = null;
let isWarroomResolved = false;
let warroomPlaylist = [];
let warroomPlayIdx = -1;
let warroomDifficulty = null;
let warroomHintsUsed = 0;
let warroomCurrentScore = 100;

async function startSimDifficulty(difficulty, excludeId) {
  warroomDifficulty = difficulty;
  
  // Build exclude list from current playlist
  let excludeList = [...warroomPlaylist];
  if (excludeId && !excludeList.includes(excludeId)) {
    excludeList.push(excludeId);
  }
  const excludeParam = excludeList.length > 0
    ? '?exclude=' + encodeURIComponent(excludeList.join(','))
    : '';

  try {
    const res = await fetch(`/api/v1/incidents/simulate/${difficulty}${excludeParam}`, { method: 'POST' });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(errText);
    }
    const scenario = await res.json();
    
    // Reset hints/score for new scenario
    warroomHintsUsed = 0;
    warroomCurrentScore = 100;

    // Truncate future if navigated back
    if (warroomPlayIdx < warroomPlaylist.length - 1) {
      warroomPlaylist = warroomPlaylist.slice(0, warroomPlayIdx + 1);
    }
    
    const wasAlreadyInPlaylist = warroomPlaylist.includes(scenario.id);
    warroomPlaylist.push(scenario.id);
    warroomPlayIdx = warroomPlaylist.length - 1;

    _renderWarroomScenario(scenario);

    if (wasAlreadyInPlaylist && warroomPlaylist.length > 1) {
      const term = document.getElementById('terminal-output');
      if (term) {
        term.innerHTML += `<div style="color:#3fb950; margin-top:8px; font-weight:bold;">[INFO] 🎉 Todos os cenários da dificuldade '${difficulty}' foram completados! Iniciando novo ciclo.</div>`;
        scrollTerminalToView();
      }
    }
  } catch (err) {
    alert('Falha ao iniciar simulação: ' + err.message);
  }
}

function scrollTerminalToView() {
  const term = document.getElementById('terminal-output');
  if (term) scrollTerminalToView();
  const inputEl = document.getElementById('terminal-input');
  if (inputEl) {
    inputEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}

function _renderWarroomScenario(scenario) {
  const simArea = document.getElementById('warroom-sim-area');
  const toolbar = document.getElementById('warroom-toolbar');
  const progressEl = document.getElementById('warroom-progress');
  const term = document.getElementById('terminal-output');
  const details = document.getElementById('warroom-details-panel');

  if (!simArea || !details || !term) return;

  simArea.style.display = 'block';
  if (toolbar) toolbar.style.display = 'flex';
  if (progressEl) progressEl.style.display = 'block';

  activeWarroomSimId = scenario.id;
  isWarroomResolved = false;

  const sev = scenario.severity || '';
  const sevColor = sev === 'SEV-1' ? '#f85149' : sev === 'SEV-2' ? '#d29922' : '#58a6ff';

  details.innerHTML = `
    <div style="border-left:4px solid ${sevColor}; padding:15px; background:var(--bg-card); border-radius:6px; margin-bottom:20px;">
      <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
        <span style="font-size:1.4rem;">${scenario.icon || '🚨'}</span>
        <h3 style="color:var(--text-primary); margin:0;">[${sev}] ${scenario.title}</h3>
      </div>
      <p style="color:var(--text-secondary); margin-bottom:10px; font-size:0.95rem;">${scenario.description}</p>
      <div style="background:var(--bg-primary); border-radius:5px; padding:10px; margin-top:8px;">
        <p style="color:#58a6ff; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:6px;">Sintomas</p>
        <ul style="margin:0; padding-left:20px; color:var(--text-secondary); font-size:0.88rem;">
          ${(scenario.symptoms || []).map(s => `<li>${s}</li>`).join('')}
        </ul>
      </div>
    </div>
  `;

  term.innerHTML = `
    <div style="color:#58a6ff;">SRE Incident Lab Web Terminal v3.2</div>
    <div style="color:#a371f7;">[SYSTEM] War Room ativada — incidente: <strong>${scenario.id}</strong></div>
    <div style="color:#d29922;">[INFO] Dificuldade: <strong>${warroomDifficulty || scenario.difficulty || 'n/a'}</strong> | Severidade: <strong>${sev}</strong></div>
    <div style="color:#8b949e; margin-top:6px;">[HINT] Digite o comando correto e pressione Enter para resolver o incidente.</div>
  `;

  const inputEl = document.getElementById('terminal-input');
  if(inputEl) {
    inputEl.value = '';
    inputEl.focus();
  }

  // Update prev/next button states
  const prevBtn = document.getElementById('wr-btn-prev');
  if (prevBtn) prevBtn.disabled = (warroomPlayIdx <= 0);
  
  _updateWarroomProgress();
}

function _updateWarroomProgress() {
  const lbl = document.getElementById('wp-text') || document.getElementById('wp-label-text');
  const bar = document.getElementById('wp-bar-fill');
  const scoreLbl = document.getElementById('wp-score') || document.getElementById('wp-score-text');
  
  const currentNum = warroomPlayIdx >= 0 ? warroomPlayIdx + 1 : 1;
  const totalNum = Math.max(warroomPlaylist.length, 1);

  if (lbl) {
    lbl.textContent = `Cenário ${currentNum} de ${totalNum}`;
  }
  if (bar) {
    const pct = Math.max(5, Math.min(100, (currentNum / totalNum) * 100));
    bar.style.width = pct + '%';
  }
  if (scoreLbl) {
    scoreLbl.innerHTML = `⭐ ${warroomCurrentScore} pts`;
  }
  
  const hintBtn = document.getElementById('wr-btn-hint');
  if (hintBtn) {
    hintBtn.innerHTML = `💡 Dica (${warroomHintsUsed}/2)`;
    hintBtn.disabled = (warroomHintsUsed >= 2);
  }
}

async function handleTerminalInput(event) {
  if (event.key === 'Enter') {
    const inputEl = document.getElementById('terminal-input');
    const cmd = inputEl.value.trim();
    if(!cmd) return;
    
    inputEl.value = '';
    const term = document.getElementById('terminal-output');
    
    const cmdLine = document.createElement('div');
    cmdLine.className = 'term-output-line term-output-cmd';
    cmdLine.textContent = `sre-admin@cluster:~$ ${cmd}`;
    term.appendChild(cmdLine);
    
    const scenarioId = activeWarroomSimId || (warroomPlaylist.length > 0 ? warroomPlaylist[warroomPlayIdx] : null);

    if (!scenarioId) {
      term.innerHTML += `<div class="term-output-error">Nenhuma simulação ativa. Escolha uma dificuldade acima.</div>`;
      scrollTerminalToView();
      return;
    }

    if (isWarroomResolved) {
      term.innerHTML += `<div style="color:#a371f7; margin-top:6px;">[INFO] Este incidente já foi resolvido com sucesso! Clique em '➡️ Próximo' para ir ao próximo desafio.</div>`;
      scrollTerminalToView();
      return;
    }

    try {
      const res = await fetch('/api/v1/incidents/solve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          scenario_id: scenarioId, 
          solution_id: cmd
        })
      });
      
      const data = await res.json();
      
      if (data.diagnostic) {
        term.innerHTML += `<div style="color:#79c0ff; font-family:monospace; white-space:pre-wrap; margin:8px 0; padding:10px; background:rgba(56,139,253,0.1); border-left:3px solid #58a6ff; border-radius:4px; line-height:1.45;">${data.output}</div>`;
      } else if (data.correct) {
        isWarroomResolved = true;
        term.innerHTML += `<div class="term-output-success">[SUCCESS] ${data.explanation}</div>`;
        term.innerHTML += `<div class="term-output-success" style="margin-top: 15px; color:#a371f7;">[SYSTEM] Incidente Resolvido! Clique no botão '➡️ Próximo' para avançar ao próximo desafio.</div>`;
        if (typeof fetchHistory === 'function') fetchHistory();
      } else {
        term.innerHTML += `<div class="term-output-error">bash: ${cmd}: command not found or not permitted</div>`;
        term.innerHTML += `<div class="term-output-error" style="opacity: 0.8; font-size: 0.85em;">> Dica do Sistema: ${data.explanation}</div>`;
      }
      
    } catch(err) {
      term.innerHTML += `<div class="term-output-error">Erro ao conectar com o servidor.</div>`;
    }
    scrollTerminalToView();
  }
}

async function warroomNext() {
  if (!warroomDifficulty) {
    alert("Inicie um cenário primeiro selecionando uma dificuldade.");
    return;
  }
  if (warroomPlayIdx < warroomPlaylist.length - 1) {
    warroomPlayIdx++;
    const scenarioId = warroomPlaylist[warroomPlayIdx];
    const res = await fetch(`/api/v1/incidents/scenario/${scenarioId}`);
    const scenario = await res.json();
    _renderWarroomScenario(scenario);
  } else {
    const currentId = warroomPlaylist[warroomPlayIdx] || activeWarroomSimId;
    await startSimDifficulty(warroomDifficulty, currentId);
  }
}

async function warroomPrev() {
  if (warroomPlayIdx <= 0) return;
  warroomPlayIdx--;
  const scenarioId = warroomPlaylist[warroomPlayIdx];
  const res = await fetch(`/api/v1/incidents/scenario/${scenarioId}`);
  const scenario = await res.json();
  _renderWarroomScenario(scenario);
}

function warroomClean() {
  const term = document.getElementById('terminal-output');
  if (term) term.innerHTML = `<div style="color:#6e7681; font-style:italic;">Terminal limpo.</div>`;
}

function warroomRestart() {
  if (!warroomDifficulty) return;
  if (!confirm("Tem certeza que deseja recomeçar a simulação? O progresso da sessão atual será perdido.")) return;
  
  warroomPlaylist = [];
  warroomPlayIdx = -1;
  activeWarroomSimId = null;
  isWarroomResolved = false;
  startSimDifficulty(warroomDifficulty);
}

async function warroomHint() {
  const scenarioId = activeWarroomSimId || (warroomPlaylist.length > 0 ? warroomPlaylist[warroomPlayIdx] : null);
  const term = document.getElementById('terminal-output');

  if (!scenarioId) {
    if (term) {
      term.innerHTML += `<div class="term-output-error">[INFO] Escolha uma dificuldade acima antes de solicitar dicas.</div>`;
      scrollTerminalToView();
    }
    return;
  }

  if (warroomHintsUsed >= 2) {
    if (term) {
      term.innerHTML += `<div style="color:#d29922; margin-top:8px;">[INFO] Todas as dicas (2/2) para este cenário já foram utilizadas.</div>`;
      scrollTerminalToView();
    }
    return;
  }

  try {
    const res = await fetch(`/api/v1/incidents/hint/${scenarioId}?index=${warroomHintsUsed}`);
    if (!res.ok) {
      const errJson = await res.json().catch(() => ({}));
      throw new Error(errJson.detail || 'Dica não disponível');
    }
    const data = await res.json();

    warroomHintsUsed++;
    warroomCurrentScore = data.score_after;

    if (term) {
      term.innerHTML += `
        <div style="border-top:1px dashed #30363d; margin-top:8px; padding-top:8px;">
          <div style="color:#f0c040; font-weight:bold;">[DICA ${warroomHintsUsed}/2] -20 pts → pontuação atual: ⭐ ${data.score_after} pts</div>
          <div style="color:#e6edf3; font-size:0.9rem; margin-top:4px;">${data.hint}</div>
        </div>
      `;
      scrollTerminalToView();
    }

    _updateWarroomProgress();
  } catch(err) {
    if (term) {
      term.innerHTML += `<div class="term-output-error">[ERRO] ${err.message}</div>`;
      scrollTerminalToView();
    }
  }
}

async function warroomReview() {
  const scenarioId = activeWarroomSimId || (warroomPlaylist.length > 0 ? warroomPlaylist[warroomPlayIdx] : null);
  const term = document.getElementById('terminal-output');

  if (!scenarioId) {
    if (term) {
      term.innerHTML += `<div class="term-output-error">[INFO] Nenhum cenário ativo para exibir revisão.</div>`;
      scrollTerminalToView();
    }
    return;
  }

  try {
    const res = await fetch(`/api/v1/incidents/review/${scenarioId}`);
    if (!res.ok) throw new Error('Revisão não disponível');
    const data = await res.json();

    if (term) {
      term.innerHTML += `
        <div style="border-top:1px dashed #30363d; margin-top:8px; padding-top:8px;">
          <div style="color:#58a6ff; font-weight:bold;">[GABARITO / REVISÃO DO CENÁRIO]</div>
          <div style="color:#3fb950; font-family:monospace; margin-top:4px; font-weight:bold;">$ ${data.command || data.correct_command || "(Nenhum comando associado)"}</div>
          <div style="color:var(--text-secondary); font-size:0.9rem; margin-top:4px;">${data.explanation}</div>
          <div style="margin-top:10px;">
            <button class="btn btn-secondary" onclick="openRunbookModal('${scenarioId}')" style="padding:5px 12px; font-size:0.82rem; cursor:pointer; display:inline-flex; align-items:center; gap:6px;">
              <span>📘</span> Ver Passo a Passo Completo (Runbook de 5 Fases)
            </button>
          </div>
        </div>
      `;
      scrollTerminalToView();
    }
  } catch(err) {
    if (term) {
      term.innerHTML += `<div class="term-output-error">[ERRO] ${err.message}</div>`;
      scrollTerminalToView();
    }
  }
}

// ── Theme Toggle Logic ─────────────────────────────────────────────
function applyTheme(theme) {
  const btn = document.getElementById('theme-toggle-btn');
  if (theme === 'light') {
    document.documentElement.classList.add('light-theme');
    if (btn) btn.innerText = '☀️';
  } else {
    document.documentElement.classList.remove('light-theme');
    if (btn) btn.innerText = '🌙';
  }
  localStorage.setItem('sre_theme', theme);
}

function toggleTheme() {
  const current = localStorage.getItem('sre_theme') || 'dark';
  applyTheme(current === 'dark' ? 'light' : 'dark');
}

document.addEventListener('DOMContentLoaded', () => {
  const savedTheme = localStorage.getItem('sre_theme') || 'dark';
  applyTheme(savedTheme);
});


// ============================================================
// Scenarios Catalog Filter (Tela Principal)
// ============================================================
function filterCatalogScenarios(diff) {
  const filterBtns = document.querySelectorAll('.catalog-difficulty-filters .filter-pill-btn');
  filterBtns.forEach(btn => {
    const text = btn.textContent.toLowerCase();
    if (diff === 'all' && text.includes('todos')) {
      btn.classList.add('active');
    } else if (diff !== 'all' && text.includes(diff)) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  const cards = document.querySelectorAll('.catalog-card');
  cards.forEach(card => {
    if (diff === 'all' || card.getAttribute('data-difficulty') === diff) {
      card.style.display = 'flex';
    } else {
      card.style.display = 'none';
    }
  });
}

// ============================================================
// Runbook Passo a Passo Modal Logic
// ============================================================
let currentModalScenario = null;
let currentRunbookStage = 'triage';

async function openRunbookModal(scenarioId) {
  try {
    const res = await fetch(`/api/v1/incidents/runbook/${scenarioId}`);
    if (!res.ok) throw new Error('Runbook não encontrado');
    const data = await res.json();
    currentModalScenario = data;

    // Header
    const iconEl = document.getElementById('rb-modal-icon');
    const titleEl = document.getElementById('rb-modal-title');
    const sevEl = document.getElementById('rb-modal-sev');
    const catEl = document.getElementById('rb-modal-cat');
    const diffEl = document.getElementById('rb-modal-diff');
    const cmdPrevEl = document.getElementById('rb-modal-cmd-preview');

    if (iconEl) iconEl.textContent = data.icon || '🚨';
    if (titleEl) titleEl.textContent = data.title;
    if (sevEl) {
      sevEl.textContent = data.severity;
      sevEl.className = `severity-badge sev-${data.severity}`;
    }
    if (catEl) catEl.textContent = `📂 ${data.category || 'Geral'}`;
    if (diffEl) diffEl.textContent = `Dificuldade: ${data.difficulty || 'medium'}`;
    if (cmdPrevEl) cmdPrevEl.textContent = data.command ? `Mitigação: $ ${data.command}` : '';

    // Switch to first stage
    switchRunbookStage('triage');

    // Open Modal
    const modal = document.getElementById('runbook-modal');
    if (modal) modal.style.display = 'flex';
  } catch(err) {
    alert(`Erro ao carregar runbook: ${err.message}`);
  }
}

function closeRunbookModal() {
  const modal = document.getElementById('runbook-modal');
  if (modal) modal.style.display = 'none';
}

function switchRunbookStage(stage) {
  currentRunbookStage = stage;
  const tabs = document.querySelectorAll('.rb-tab-btn');
  tabs.forEach(tab => {
    if (tab.id === `rb-tab-${stage}`) {
      tab.classList.add('active');
    } else {
      tab.classList.remove('active');
    }
  });

  const bodyEl = document.getElementById('rb-modal-body');
  if (!bodyEl || !currentModalScenario) return;

  const data = currentModalScenario;
  const rb = data.runbook_steps || {};
  const concepts = data.concepts || {};

  if (stage === 'triage') {
    const items = rb.triage || [
      'Verificar alertas ativos no Alertmanager.',
      'Consultar o dashboard de SLO e disponibilidade no Grafana.',
      'Identificar taxa de descarte ou queima de Error Budget.'
    ];
    bodyEl.innerHTML = `
      <div class="runbook-step-box">
        <h4 style="margin:0 0 12px; color:#f0f6fc; font-size:1.05rem; display:flex; align-items:center; gap:8px;">
          <span>🚨</span> Fase 1: Triagem & Alertas Prometheus
        </h4>
        <p style="color:#8b949e; font-size:0.88rem; margin-bottom:16px;">
          Identifique os primeiros sinais vitais, consulte as métricas de Golden Signals e confirme o escopo da violação do SLO.
        </p>
        <ul style="padding-left:22px; margin:0; line-height:1.7;">
          ${items.map(it => `<li style="margin-bottom:8px;">${escapeHtml(it)}</li>`).join('')}
        </ul>
      </div>
    `;
  } else if (stage === 'diagnosis') {
    const items = rb.diagnosis || [
      'kubectl get pods -n sre-rag -o wide',
      'kubectl describe pod <nome-do-pod>',
      'kubectl logs -l app=sre-rag-api --tail=50'
    ];
    bodyEl.innerHTML = `
      <div class="runbook-step-box">
        <h4 style="margin:0 0 12px; color:#f0f6fc; font-size:1.05rem; display:flex; align-items:center; gap:8px;">
          <span>🔍</span> Fase 2: Comandos de Diagnóstico & Triagem no Cluster
        </h4>
        <p style="color:#8b949e; font-size:0.88rem; margin-bottom:14px;">
          Execute os comandos abaixo para inspecionar os logs de aplicação, eventos de container e métricas de sistema:
        </p>
        ${items.map(it => `
          <div class="runbook-code-block">
            <code>${escapeHtml(it)}</code>
          </div>
        `).join('')}
      </div>
    `;
  } else if (stage === 'mitigation') {
    const mit = rb.mitigation || {};
    bodyEl.innerHTML = `
      <div class="runbook-step-box" style="border-left: 4px solid #3fb950;">
        <h4 style="margin:0 0 12px; color:#3fb950; font-size:1.05rem; display:flex; align-items:center; gap:8px;">
          <span>⚡</span> Fase 3: Mitigação Imediata (Estancar Impacto & Reduzir MTTR)
        </h4>
        <p style="margin:0 0 14px; font-weight:500; color:#e6edf3;">
          ${escapeHtml(mit.action || 'Executar comando de remediação rápida para reestabelecer o tráfego do usuário.')}
        </p>
        <div class="runbook-code-block" style="border-color:#238636; color:#56d364; font-size:0.95rem; font-weight:bold;">
          <code>$ ${escapeHtml(mit.command || data.command || '')}</code>
        </div>
        <div style="font-size:0.88rem; color:#8b949e; margin-top:14px; background:rgba(0,0,0,0.25); padding:10px 14px; border-radius:6px;">
          <strong style="color:#38bdf8;">Validação de Estabilidade:</strong> ${escapeHtml(mit.validation || 'Acompanhar retorno dos endpoints para HTTP 200 e normalização da latência.')}
        </div>
      </div>
    `;
  } else if (stage === 'root_cause') {
    const rc = rb.root_cause || {};
    bodyEl.innerHTML = `
      <div class="runbook-step-box">
        <h4 style="margin:0 0 14px; color:#f0f6fc; font-size:1.05rem; display:flex; align-items:center; gap:8px;">
          <span>🛠️</span> Fase 4: Análise de Causa Raiz & Correção Permanente
        </h4>
        <div style="margin-bottom:18px;">
          <strong style="color:#d2a8ff; font-size:0.92rem; text-transform:uppercase; letter-spacing:0.5px;">Causa Raiz Identificada:</strong>
          <p style="margin:6px 0 0; color:#c9d1d9; line-height:1.6;">
            ${escapeHtml(rc.analysis || data.explanation || 'Falha de configuração de recurso ou dependência não sincronizada.')}
          </p>
        </div>
        <div style="border-top:1px solid #30363d; padding-top:14px;">
          <strong style="color:#58a6ff; font-size:0.92rem; text-transform:uppercase; letter-spacing:0.5px;">Correção Definitiva no Repositório / GitOps:</strong>
          <p style="margin:6px 0 0; color:#c9d1d9; line-height:1.6;">
            ${escapeHtml(rc.permanent_fix || 'Atualizar manifesto no repositório de GitOps e submeter Pull Request com validações de CI/CD.')}
          </p>
        </div>
      </div>
    `;
  } else if (stage === 'prevention') {
    const prev = rb.prevention || [
      'Documentar timeline do incidente e publicar postmortem blameless.',
      'Ajustar thresholds de alertas no Alertmanager para detecção proativa.',
      'Executar teste de injeção de caos para certificar a resiliência contínua.'
    ];
    bodyEl.innerHTML = `
      <div class="runbook-step-box">
        <h4 style="margin:0 0 12px; color:#f0f6fc; font-size:1.05rem; display:flex; align-items:center; gap:8px;">
          <span>🛡️</span> Fase 5: Prevenção, Pós-Morte & Chaos Engineering
        </h4>
        <p style="color:#8b949e; font-size:0.88rem; margin-bottom:16px;">
          Lições aprendidas e ações contínuas para impedir a reincidência do problema em produção:
        </p>
        <ul style="padding-left:22px; margin:0; line-height:1.7;">
          ${prev.map(p => `<li style="margin-bottom:8px;">${escapeHtml(p)}</li>`).join('')}
        </ul>
      </div>
    `;
  } else if (stage === 'concepts') {
    bodyEl.innerHTML = `
      <div class="runbook-step-box">
        <h4 style="margin:0 0 10px; color:#38bdf8; font-size:1.05rem;">
          <span>📚</span> ${escapeHtml(concepts.resource_title || 'Recursos Envolvidos')}
        </h4>
        <div style="display:flex; gap:6px; flex-wrap:wrap; margin-bottom:14px;">
          ${(concepts.architecture_components || []).map(c => `<span class="concept-component-tag">${escapeHtml(c)}</span>`).join('')}
        </div>
        <p style="color:#c9d1d9; line-height:1.6; margin-bottom:16px;">
          ${escapeHtml(concepts.how_it_works || 'Componente arquitetural de infraestrutura e orquestração.')}
        </p>
        <h5 style="color:#f0f6fc; margin:16px 0 8px; font-size:0.95rem;">⭐ Melhores Práticas Recomendadas:</h5>
        <ul style="padding-left:22px; margin:0; line-height:1.6;">
          ${(concepts.best_practices || []).map(b => `<li style="margin-bottom:6px;">${escapeHtml(b)}</li>`).join('')}
        </ul>
      </div>
    `;
  }
}

function playCurrentModalScenario() {
  if (!currentModalScenario) return;
  const sid = currentModalScenario.scenario_id;
  closeRunbookModal();
  switchDashboardTab('warroom');
  warroomStartScenario(sid);
}

// ============================================================
// SRE Concepts Knowledge Base Logic (Aba de Conceitos)
// ============================================================
let cachedConceptsList = null;

async function loadConceptsCatalog() {
  const grid = document.getElementById('concepts-cards-grid');
  if (!grid) return;

  if (cachedConceptsList) {
    renderConceptsCards(cachedConceptsList);
    return;
  }

  try {
    grid.innerHTML = '<div style="color:#8b949e; font-size:0.95rem;">Carregando conceitos de SRE...</div>';
    const res = await fetch('/api/v1/incidents/concepts');
    if (!res.ok) throw new Error('Falha ao carregar conceitos');
    cachedConceptsList = await res.json();
    renderConceptsCards(cachedConceptsList);
  } catch(err) {
    grid.innerHTML = `<div class="term-output-error">Erro ao carregar conceitos: ${err.message}</div>`;
  }
}

function renderConceptsCards(concepts) {
  const grid = document.getElementById('concepts-cards-grid');
  if (!grid) return;

  if (concepts.length === 0) {
    grid.innerHTML = '<div style="color:#8b949e; grid-column:1/-1;">Nenhum conceito encontrado para este filtro.</div>';
    return;
  }

  grid.innerHTML = concepts.map(item => `
    <div class="concept-card" data-category="${escapeHtml(item.category)}" data-difficulty="${escapeHtml(item.difficulty)}">
      <div>
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
          <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-size:2rem;">${escapeHtml(item.icon)}</span>
            <div>
              <h3 style="margin:0; font-size:1.1rem; color:var(--text-primary);">${escapeHtml(item.resource_title || item.title)}</h3>
              <div style="font-size:0.78rem; color:#58a6ff; margin-top:2px;">Cenário: ${escapeHtml(item.title)}</div>
            </div>
          </div>
          <div style="display:flex; gap:6px;">
            <span class="severity-badge sev-${item.severity}">${item.severity}</span>
            <span class="difficulty-badge diff-${item.difficulty}" style="font-size:0.72rem; padding:2px 8px; border-radius:12px; font-weight:600; text-transform:uppercase;">${item.difficulty}</span>
          </div>
        </div>

        <!-- Tags de Componentes -->
        <div style="display:flex; gap:6px; flex-wrap:wrap; margin-bottom:14px;">
          ${(item.architecture_components || []).map(comp => `
            <span class="concept-component-tag">${escapeHtml(comp)}</span>
          `).join('')}
        </div>

        <!-- Como Funciona -->
        <div style="background:rgba(0,0,0,0.22); border-left:3px solid #38bdf8; padding:10px 14px; border-radius:0 6px 6px 0; margin-bottom:14px;">
          <div style="font-size:0.78rem; font-weight:600; color:#38bdf8; text-transform:uppercase; margin-bottom:4px;">🏗️ Mecanismo Interno</div>
          <p style="margin:0; font-size:0.85rem; color:var(--text-secondary); line-height:1.5;">${escapeHtml(item.how_it_works)}</p>
        </div>

        <!-- Melhores Práticas -->
        <div style="margin-bottom:14px;">
          <div style="font-size:0.78rem; font-weight:600; color:#3fb950; text-transform:uppercase; margin-bottom:6px;">⭐ Melhores Práticas SRE</div>
          <ul style="margin:0; padding-left:18px; font-size:0.83rem; color:var(--text-secondary); line-height:1.5;">
            ${(item.best_practices || []).slice(0, 2).map(bp => `<li style="margin-bottom:4px;">${escapeHtml(bp)}</li>`).join('')}
          </ul>
        </div>
      </div>

      <!-- Footer Ações -->
      <div style="display:flex; gap:8px; border-top:1px solid var(--border-color); padding-top:12px; margin-top:10px;">
        <button class="btn btn-secondary" onclick="openRunbookModal('${item.scenario_id}')" style="flex:1; padding:7px; font-size:0.82rem; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:6px;">
          <span>📘</span> Ver Runbook
        </button>
        <button class="btn btn-primary" onclick="jumpToWarroomScenario('${item.scenario_id}')" style="flex:1; padding:7px; font-size:0.82rem; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:6px;">
          <span>🚀</span> Praticar no Terminal
        </button>
      </div>
    </div>
  `).join('');
}

function filterConceptsCategory(cat) {
  const btns = document.querySelectorAll('.concepts-filter-bar .concept-filter-btn');
  btns.forEach(btn => {
    if ((cat === 'all' && btn.textContent.includes('Todos')) || btn.textContent.includes(cat)) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  if (!cachedConceptsList) return;
  if (cat === 'all') {
    renderConceptsCards(cachedConceptsList);
  } else {
    const filtered = cachedConceptsList.filter(c => c.category === cat);
    renderConceptsCards(filtered);
  }
}

function filterConcepts() {
  const query = (document.getElementById('concepts-search')?.value || '').toLowerCase().trim();
  if (!cachedConceptsList) return;

  if (!query) {
    renderConceptsCards(cachedConceptsList);
    return;
  }

  const filtered = cachedConceptsList.filter(c => {
    return c.title.toLowerCase().includes(query) ||
           (c.resource_title || '').toLowerCase().includes(query) ||
           (c.how_it_works || '').toLowerCase().includes(query) ||
           (c.architecture_components || []).some(comp => comp.toLowerCase().includes(query));
  });
  renderConceptsCards(filtered);
}

function jumpToWarroomScenario(scenarioId) {
  switchDashboardTab('warroom');
  warroomStartScenario(scenarioId);
}
