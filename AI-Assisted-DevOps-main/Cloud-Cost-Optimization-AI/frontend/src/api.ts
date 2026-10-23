const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
export const token = () => localStorage.getItem("token");
export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token()) headers.set("Authorization", `Bearer ${token()}`);
  const response = await fetch(`${API}${path}`, { ...options, headers });
  if (response.status === 401) { localStorage.removeItem("token"); window.location.href = "/login"; }
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.detail || "Request failed"); }
  return response.json();
}
export async function download(path: string, filename: string) {
  const response = await fetch(`${API}${path}`, { headers: { Authorization: `Bearer ${token()}` } });
  if (!response.ok) throw new Error("Download failed");
  const blob = await response.blob(); const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a"); anchor.href = url; anchor.download = filename; anchor.click(); URL.revokeObjectURL(url);
}
export const websocketUrl = (id: string) => `${(import.meta.env.VITE_WS_URL || "ws://localhost:8000")}/ws/progress/${id}?token=${encodeURIComponent(token() || "")}`;
