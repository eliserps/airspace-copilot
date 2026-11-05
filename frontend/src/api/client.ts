import createClient from "openapi-fetch";
import { API_BASE_URL } from "@/config";
import type { components, paths } from "./schema.gen";

export type Schemas = components["schemas"];
export type Aircraft = Schemas["Aircraft"];
export type AircraftMapResponse = Schemas["AircraftMapResponse"];
export type BriefingResponse = Schemas["BriefingResponse"];
export type WeatherResponse = Schemas["WeatherResponse"];
export type AskRequest = Schemas["AskRequest"];
export type ChatTurn = Schemas["ChatTurn"];
export type Lang = NonNullable<paths["/briefing"]["get"]["parameters"]["query"]>["lang"] & string;

export type ErrorDetails = Record<string, string | number>;

export class ApiError extends Error {
  status: number | undefined;
  code: string | undefined;
  details: ErrorDetails;

  constructor(message: string, status?: number, code?: string, details: ErrorDetails = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export const UNREACHABLE_CODE = "unreachable";

export function apiErrorFromBody(body: unknown, status?: number, fallback = ""): ApiError {
  const { error, message, ...rest } = (body ?? {}) as Record<string, unknown>;
  const details: ErrorDetails = {};
  for (const [key, value] of Object.entries(rest)) {
    if (typeof value === "string" || typeof value === "number") details[key] = value;
  }
  return new ApiError(
    typeof message === "string" && message ? message : fallback,
    status,
    typeof error === "string" ? error : undefined,
    details,
  );
}

const UNREACHABLE = "Could not reach the airspace API. Check your connection or API_BASE_URL.";

export const http = createClient<paths>({
  baseUrl: API_BASE_URL,
  fetch: (request) => globalThis.fetch(request),
});

export function toApiError(body: unknown, response: Response): ApiError {
  return apiErrorFromBody(
    body,
    response.status,
    `Request failed (${response.status} ${response.statusText || "error"})`,
  );
}

export async function unwrap<T>(
  request: Promise<{ data?: T; error?: unknown; response: Response }>,
): Promise<T> {
  let result: Awaited<typeof request>;
  try {
    result = await request;
  } catch {
    throw new ApiError(UNREACHABLE, undefined, UNREACHABLE_CODE);
  }
  if (result.error !== undefined || result.data === undefined) {
    throw toApiError(result.error, result.response);
  }
  return result.data;
}

export async function postStream(path: string, body: unknown, signal?: AbortSignal) {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify(body),
      signal: signal ?? null,
    });
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new ApiError(UNREACHABLE, undefined, UNREACHABLE_CODE);
  }
  if (!response.ok || !response.body) {
    const payload: unknown = await response.json().catch(() => undefined);
    throw toApiError(payload, response);
  }
  return response.body;
}
