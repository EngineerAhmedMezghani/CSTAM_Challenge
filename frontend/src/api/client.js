const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try { detail = (await response.json()).detail || detail; } catch { /* response may not be JSON */ }
    throw new Error(detail);
  }
  return response.json();
}

export function createScrape(url, options = {}) {
  return request("/api/scrape", { method: "POST", body: JSON.stringify({ url, ...options }) });
}

export function getScrapeJob(jobId) {
  return request(`/api/scrape/${jobId}`);
}

export function getTenders(jobId) {
  return request(`/api/tenders?job_id=${encodeURIComponent(jobId)}&page=1&page_size=100`);
}
