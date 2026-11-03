const _rawBase = (import.meta as unknown as { env: Record<string, string> }).env
  .VITE_API_URL || 'http://localhost:8000';
// Render's fromService gives a bare hostname (no scheme); the browser needs
// a full URL, so add https:// when no scheme is present.
export const API_BASE = _rawBase.includes('://') ? _rawBase : `https://${_rawBase}`;

export function getToken(): string | null {
  return localStorage.getItem('qs_token');
}

export function getUser(): { username: string; role: string } | null {
  const raw = localStorage.getItem('qs_user');
  return raw ? JSON.parse(raw) : null;
}

export function logout() {
  localStorage.removeItem('qs_token');
  localStorage.removeItem('qs_user');
  window.location.href = '/auth';
}

export async function api<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(opts.headers as Record<string, string> | undefined),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
  const text = await res.text();
  let data: unknown = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!res.ok) {
    const detail = (data as { detail?: string })?.detail || `Request failed (${res.status})`;
    throw new Error(detail);
  }
  return data as T;
}

export async function apiForm<T>(path: string, form: FormData): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { method: 'POST', headers, body: form });
  const text = await res.text();
  let data: unknown = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!res.ok) {
    const detail = (data as { detail?: string })?.detail || `Request failed (${res.status})`;
    throw new Error(detail);
  }
  return data as T;
}
