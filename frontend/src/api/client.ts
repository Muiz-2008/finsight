// Thin typed fetch wrapper for the FinSight backend.
//
// Known limitation: the auth token is stored in localStorage for the scope of
// this project. That is vulnerable to XSS token theft in a production system;
// a httpOnly cookie + refresh-token flow would be the safer choice there.

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const TOKEN_KEY = "finsight_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

async function parseErrorDetail(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail)) {
      // FastAPI validation error shape
      return body.detail
        .map((d: { msg?: string }) => d.msg ?? JSON.stringify(d))
        .join("; ");
    }
    return res.statusText || `Request failed with status ${res.status}`;
  } catch {
    return res.statusText || `Request failed with status ${res.status}`;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  form?: URLSearchParams;
  isFormData?: boolean;
  skipAuth?: boolean;
}

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {};
  let body: BodyInit | undefined;

  if (opts.form) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    body = opts.form;
  } else if (opts.isFormData) {
    // Let the browser set the multipart boundary.
    body = opts.body as BodyInit;
  } else if (opts.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.body);
  }

  if (!opts.skipAuth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    method: opts.method ?? "GET",
    headers,
    body,
  });

  if (res.status === 401 && !opts.skipAuth) {
    clearToken();
    if (window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
    throw new ApiError(401, "Session expired. Please log in again.");
  }

  if (!res.ok) {
    const detail = await parseErrorDetail(res);
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;

  const text = await res.text();
  return text ? (JSON.parse(text) as T) : (undefined as T);
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  postForm: <T>(path: string, form: URLSearchParams) =>
    request<T>(path, { method: "POST", form, skipAuth: true }),
  postFormData: <T>(path: string, formData: FormData) =>
    request<T>(path, { method: "POST", body: formData, isFormData: true }),
};

export { API_URL };
