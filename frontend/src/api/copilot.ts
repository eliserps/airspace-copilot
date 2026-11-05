import { apiErrorFromBody, postStream, type ApiError, type AskRequest } from "@/api/client";
import { readSse } from "@/lib/sse";

export type ToolActivity = { name: string; arguments: Record<string, unknown> };

export type ChatEvent =
  | { type: "meta"; flagged: boolean }
  | { type: "delta"; text: string }
  | ({ type: "tool" } & ToolActivity)
  | { type: "done" }
  | { type: "error"; error: ApiError };

export async function* askStream(
  body: AskRequest,
  signal?: AbortSignal,
): AsyncGenerator<ChatEvent> {
  const stream = await postStream("/ask/stream", body, signal);
  for await (const { event, data } of readSse(stream)) {
    const payload = JSON.parse(data) as Record<string, unknown>;
    if (event === "meta") yield { type: "meta", flagged: Boolean(payload["flagged"]) };
    else if (event === "delta") yield { type: "delta", text: String(payload["text"] ?? "") };
    else if (event === "tool") {
      const args = payload["arguments"];
      yield {
        type: "tool",
        name: String(payload["name"] ?? ""),
        arguments: args && typeof args === "object" ? (args as Record<string, unknown>) : {},
      };
    } else if (event === "done") yield { type: "done" };
    else if (event === "error") yield { type: "error", error: apiErrorFromBody(payload) };
  }
}
