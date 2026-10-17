/**
 * SRE RAG Agent — API Client Module (ESM)
 * Centralizes asynchronous HTTP requests with standardized headers, timeout, and error handling.
 */

export async function fetchAPI(endpoint, options = {}) {
  const defaultHeaders = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), options.timeout || 15000);

  const config = {
    ...options,
    headers: { ...defaultHeaders, ...options.headers },
    signal: controller.signal,
  };

  try {
    const response = await fetch(endpoint, config);
    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP Error ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error(`Request to ${endpoint} timed out.`);
    }
    throw err;
  }
}

export async function getIncidentsCatalog() {
  return fetchAPI('/api/v1/incidents/scenarios');
}

export async function startSimulation(scenarioId) {
  return fetchAPI('/api/v1/incidents/simulate', {
    method: 'POST',
    body: JSON.stringify({ scenario_id: scenarioId }),
  });
}

export async function solveSimulation(scenarioId, solutionId) {
  return fetchAPI('/api/v1/incidents/solve', {
    method: 'POST',
    body: JSON.stringify({ scenario_id: scenarioId, solution_id: solutionId }),
  });
}

export async function toggleChaos500(enable = true) {
  return fetchAPI(`/api/v1/chaos/500?enable=${enable}`, {
    method: 'POST',
  });
}

export async function queryRAG(question) {
  return fetchAPI('/api/v1/query', {
    method: 'POST',
    body: JSON.stringify({ question }),
  });
}

export async function getHistory() {
  return fetchAPI('/api/v1/history');
}
