const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export async function getJson(path) {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return response.json();
}
