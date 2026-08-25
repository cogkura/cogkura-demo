import type {
  ChatResponse,
  DemoStateResponse,
  EventRequest,
  EventResponse,
  ResetResponse,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_DEMO_API_URL?.replace(/\/$/, "") ??
  "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export function fetchDemoState(): Promise<DemoStateResponse> {
  return request<DemoStateResponse>("/api/demo");
}

export function sendChatMessage(message: string): Promise<ChatResponse> {
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export function sendEvent(payload: EventRequest): Promise<EventResponse> {
  return request<EventResponse>("/api/events", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function resetDemo(): Promise<ResetResponse> {
  return request<ResetResponse>("/api/reset", { method: "POST" });
}
