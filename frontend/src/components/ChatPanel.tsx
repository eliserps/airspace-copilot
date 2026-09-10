import { useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { AnimatePresence, motion } from "motion/react";
import { ShieldAlert, Send, Sparkles } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Markdown } from "@/components/Markdown";
import { LoadingState, ErrorState } from "@/components/StatePanels";
import { useI18n } from "@/lib/i18n-context";
import type { StringKey } from "@/lib/i18n-strings";

type Msg =
  | { id: string; role: "user"; text: string }
  | { id: string; role: "assistant"; text: string; flagged: boolean };

const SUGGESTION_KEYS: StringKey[] = ["copilot.suggest1", "copilot.suggest2", "copilot.suggest3"];

export function ChatPanel({ region }: { region: string }) {
  const { t } = useI18n();
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const ask = useMutation({
    mutationFn: (question: string) => api.ask(question),
    onSuccess: (res) =>
      setMessages((m) => [
        ...m,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: res.answer,
          flagged: Boolean(res.flagged),
        },
      ]),
  });

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, ask.isPending]);

  function send(question: string) {
    const q = question.trim();
    if (!q || ask.isPending) return;
    setMessages((m) => [...m, { id: crypto.randomUUID(), role: "user", text: q }]);
    setInput("");
    ask.mutate(q);
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
        {messages.length === 0 && !ask.isPending ? (
          <div className="flex flex-col items-start gap-3 py-6">
            <div className="flex items-center gap-2 text-primary">
              <Sparkles className="size-4" />
              <p className="label-caps text-primary">{t("copilot.standingBy")}</p>
            </div>
            <p className="text-sm text-muted-foreground">
              {t("copilot.ask")} <span className="font-mono text-foreground">{region}</span>.
            </p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTION_KEYS.map((key) => (
                <button
                  key={key}
                  onClick={() => send(t(key))}
                  className="rounded-full border border-border bg-secondary/60 px-3 py-1.5 text-xs text-secondary-foreground transition-all hover:-translate-y-0.5 hover:border-primary/60 hover:text-primary"
                >
                  {t(key)}
                </button>
              ))}
            </div>
          </div>
        ) : null}

        <div className="space-y-3">
          <AnimatePresence initial={false}>
            {messages.map((m) => (
              <motion.div
                key={m.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.22, ease: "easeOut" }}
                className={m.role === "user" ? "flex justify-end" : "flex justify-start"}
              >
                {m.role === "user" ? (
                  <p className="max-w-[85%] rounded-2xl rounded-br-sm bg-primary px-3.5 py-2 text-sm font-medium text-primary-foreground">
                    {m.text}
                  </p>
                ) : (
                  <div className="max-w-[92%] rounded-2xl rounded-bl-sm border border-border bg-surface/70 px-3.5 py-2.5">
                    {m.flagged ? (
                      <span className="mb-2 inline-flex items-center gap-1.5 rounded-full border border-warning/40 bg-warning/10 px-2 py-0.5 text-[11px] font-medium text-warning">
                        <ShieldAlert className="size-3" /> {t("copilot.flagged")}
                      </span>
                    ) : null}
                    <Markdown>{m.text}</Markdown>
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {ask.isPending ? <LoadingState label={t("copilot.thinking")} /> : null}
        {ask.isError ? (
          <ErrorState
            message={ask.error instanceof ApiError ? ask.error.message : t("copilot.failed")}
            onRetry={() => ask.reset()}
          />
        ) : null}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="flex items-center gap-2 border-t border-border p-3"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t("copilot.placeholder")}
          aria-label={t("copilot.placeholder")}
          className="min-w-0 flex-1 rounded-lg border border-input bg-background/60 px-3 py-2 text-sm text-foreground outline-none transition-shadow placeholder:text-muted-foreground focus:border-primary focus:shadow-glow"
        />
        <button
          type="submit"
          disabled={!input.trim() || ask.isPending}
          className="inline-flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground transition-transform hover:scale-105 disabled:opacity-40 disabled:hover:scale-100"
          aria-label={t("copilot.send")}
        >
          <Send className="size-4" />
        </button>
      </form>
    </div>
  );
}
