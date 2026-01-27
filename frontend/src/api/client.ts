const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8001";
console.log("API_BASE =", API_BASE);

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options?.headers || {}) },
    ...options,
  });
  if (!res.ok) throw new Error(await res.text());
  // some endpoints might return plain text later; for now JSON is expected
  return res.json();
}

export async function getSummary() {
  return request("/summary");
}

export async function getFutureForecast(store_id?: string, item_id?: string) {
  const usp = new URLSearchParams();
  if (store_id) usp.set("store_id", store_id);
  if (item_id) usp.set("item_id", item_id);
  return request(`/forecast/future?${usp.toString()}`);
}

export async function getRecs(kind: string, store_id?: string) {
  const usp = new URLSearchParams();
  if (store_id) usp.set("store_id", store_id);
  return request(`/recs/${kind}?${usp.toString()}`);
}

export async function runPipeline(endpoint: string, zip_path: string, max_series: number) {
  return request(`/pipeline/${endpoint}`, {
    method: "POST",
    body: JSON.stringify({ zip_path, max_series }),
  });
}

export async function chatAgent(payload: any) {
  return request("/agent/chat", { method: "POST", body: JSON.stringify(payload) });
}

export function downloadsUrl(path: string) {
  // path like "/downloads/xxx.csv"
  return `${API_BASE}${path}`;
}
