const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const CSRF_KEY = "madani_csrf_token";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export function setCsrfToken(token: string) {
  if (typeof window !== "undefined") localStorage.setItem(CSRF_KEY, token);
}

export function clearCsrfToken() {
  if (typeof window !== "undefined") localStorage.removeItem(CSRF_KEY);
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = (init.method || "GET").toUpperCase();
  const headers = new Headers(init.headers || {});
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (!["GET", "HEAD", "OPTIONS"].includes(method) && typeof window !== "undefined") {
    const csrf = localStorage.getItem(CSRF_KEY);
    if (csrf) headers.set("X-CSRF-Token", csrf);
  }
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });
  if (response.status === 204) return undefined as T;
  const text = await response.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!response.ok) {
    const message = typeof data === "object" && data && "detail" in data ? JSON.stringify((data as { detail: unknown }).detail) : String(data || response.statusText);
    throw new ApiError(response.status, message);
  }
  return data as T;
}
