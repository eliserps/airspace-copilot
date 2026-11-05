import { useCallback, useEffect, useRef, useState } from "react";
import type { RegionId } from "@/config";
import { ApiError, type ChatTurn } from "@/api/client";
import { askStream } from "@/api/copilot";

export type ChatMessage =
  | { id: string; role: "user"; text: string }
  | { id: string; role: "assistant"; text: string; flagged: boolean };

type Request = { question: string; region: RegionId; history: ChatTurn[] };

export const HISTORY_TURNS = 6;
export const MAX_TURN_CHARS = 2000;

export function toHistory(messages: ChatMessage[]): ChatTurn[] {
  return messages
    .slice(-HISTORY_TURNS)
    .map((m) => ({ role: m.role, content: m.text.slice(0, MAX_TURN_CHARS) }));
}

export function useCopilotChat(region: RegionId) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [pending, setPending] = useState(false);
  const [streamingId, setStreamingId] = useState<string | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const controller = useRef<AbortController | null>(null);
  const last = useRef<Request | null>(null);

  useEffect(() => () => controller.current?.abort(), []);

  const run = useCallback(async (request: Request) => {
    controller.current?.abort();
    const ctrl = new AbortController();
    controller.current = ctrl;
    const id = crypto.randomUUID();
    let flagged = false;
    let started = false;

    setError(null);
    setPending(true);
    try {
      for await (const event of askStream(request, ctrl.signal)) {
        if (event.type === "meta") flagged = event.flagged;
        else if (event.type === "error") throw event.error;
        else if (event.type === "delta") {
          const chunk = event.text;
          if (!started) {
            started = true;
            setStreamingId(id);
            setMessages((m) => [...m, { id, role: "assistant", text: chunk, flagged }]);
          } else {
            setMessages((m) =>
              m.map((msg) => (msg.id === id ? { ...msg, text: msg.text + chunk } : msg)),
            );
          }
        }
      }
    } catch (caught) {
      if (ctrl.signal.aborted) return;
      setMessages((m) => m.filter((msg) => msg.id !== id || msg.text.trim()));
      setError(caught instanceof ApiError ? caught : new ApiError(String(caught)));
    } finally {
      if (controller.current === ctrl) {
        setPending(false);
        setStreamingId(null);
      }
    }
  }, []);

  const send = useCallback(
    (question: string) => {
      const q = question.trim();
      if (!q || pending) return;
      last.current = { question: q, region, history: toHistory(messages) };
      setMessages((m) => [...m, { id: crypto.randomUUID(), role: "user", text: q }]);
      void run(last.current);
    },
    [messages, pending, region, run],
  );

  const retry = useCallback(() => {
    if (last.current && !pending) void run(last.current);
  }, [pending, run]);

  return { messages, pending, streamingId, error, send, retry };
}
