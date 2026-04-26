export const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";
export const DEMO_X402_PAYMENT = process.env.DEMO_X402_PAYMENT ?? "proof";

export interface BackendError {
  error: string;
  status: number;
  detail?: unknown;
}

export async function backendFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const url = `${BACKEND_URL.replace(/\/$/, "")}${path}`;
  return fetch(url, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });
}

export function humaniseStatus(status: number, raw?: string): string {
  switch (status) {
    case 400:
      return raw || "Request was rejected by the marketplace (validation).";
    case 402:
      return "Payment configuration missing on the server (x402 header).";
    case 404:
      return "Endpoint not found on the backend.";
    case 502:
      return "Settlement failed on Arc — check server logs for the underlying revert.";
    case 503:
      return "Backend is unreachable. Is FastAPI running on the configured port?";
    default:
      return raw || `Unexpected backend response (HTTP ${status}).`;
  }
}
