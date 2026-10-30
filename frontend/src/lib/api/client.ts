// Thin fetch wrapper for the ECHO WorkforceOS backend.
// Token is persisted in a JS-readable cookie (`echo_token`) — never localStorage.

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

const TOKEN_COOKIE = "echo_token";
const TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 7; // 7 days

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

// ---------------------------------------------------------------------------
// Token helpers (cookie-backed, SSR-safe)
// ---------------------------------------------------------------------------

export function getToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(
    new RegExp(`(?:^|; )${TOKEN_COOKIE}=([^;]*)`)
  );
  return match ? decodeURIComponent(match[1]) : null;
}

export function setToken(token: string): void {
  if (typeof document === "undefined") return;
  document.cookie = `${TOKEN_COOKIE}=${encodeURIComponent(
    token
  )}; path=/; max-age=${TOKEN_MAX_AGE_SECONDS}; SameSite=Lax`;
}

export function clearToken(): void {
  if (typeof document === "undefined") return;
  document.cookie = `${TOKEN_COOKIE}=; path=/; max-age=0; SameSite=Lax`;
}

// ---------------------------------------------------------------------------
// Core fetch wrapper
// ---------------------------------------------------------------------------

export interface ApiFetchInit extends Omit<RequestInit, "body"> {
  body?: unknown;
  skipAuth?: boolean;
}

async function apiFetch<T>(path: string, init: ApiFetchInit = {}): Promise<T> {
  const { skipAuth, headers, body, ...rest } = init;

  const isFormData = typeof FormData !== "undefined" && body instanceof FormData;

  const finalHeaders = new Headers(headers);
  if (!isFormData && body !== undefined && body !== null) {
    if (!finalHeaders.has("Content-Type")) {
      finalHeaders.set("Content-Type", "application/json");
    }
  }
  if (!skipAuth) {
    const token = getToken();
    if (token) {
      finalHeaders.set("Authorization", `Bearer ${token}`);
    }
  }

  const finalBody: BodyInit | null | undefined = isFormData
    ? (body as FormData)
    : body !== undefined && body !== null
    ? JSON.stringify(body)
    : (body as null | undefined);

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: finalHeaders,
    body: finalBody,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");
  const payload = isJson ? await response.json().catch(() => null) : await response.text();

  if (!response.ok) {
    const detail =
      isJson && payload && typeof payload === "object" && "detail" in payload
        ? String((payload as { detail: unknown }).detail)
        : typeof payload === "string" && payload
        ? payload
        : response.statusText || "Request failed";
    throw new ApiError(response.status, detail);
  }

  return payload as T;
}

// ---------------------------------------------------------------------------
// Convenience wrappers
// ---------------------------------------------------------------------------

function buildQuery(params?: Record<string, unknown>): string {
  if (!params) return "";
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export const api = {
  get<T>(path: string, params?: Record<string, unknown>, init?: ApiFetchInit) {
    return apiFetch<T>(`${path}${buildQuery(params)}`, { ...init, method: "GET" });
  },
  post<T>(path: string, body?: ApiFetchInit["body"], init?: ApiFetchInit) {
    return apiFetch<T>(path, { ...init, method: "POST", body });
  },
  patch<T>(path: string, body?: ApiFetchInit["body"], init?: ApiFetchInit) {
    return apiFetch<T>(path, { ...init, method: "PATCH", body });
  },
  del<T>(path: string, init?: ApiFetchInit) {
    return apiFetch<T>(path, { ...init, method: "DELETE" });
  },
  upload<T>(path: string, formData: FormData, init?: ApiFetchInit) {
    return apiFetch<T>(path, { ...init, method: "POST", body: formData });
  },
};

export { apiFetch, buildQuery, API_BASE_URL };
