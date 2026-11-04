import { useEffect, useRef } from "react";
import { AnimatePresence } from "motion/react";
import type { RegionId } from "@/config";
import { ErrorState } from "@/components/ui/state/ErrorState";
import { LoadingState } from "@/components/ui/state/LoadingState";
import { useI18n } from "@/lib/i18n/context";
import { useErrorMessage } from "@/lib/i18n/useErrorMessage";
import { ChatInput } from "./ChatInput";
import { ChatMessage } from "./ChatMessage";
import { CopilotWelcome } from "./CopilotWelcome";
import { useCopilotChat } from "./useCopilotChat";

export function CopilotTab({ regionId, regionLabel }: { regionId: RegionId; regionLabel: string }) {
  const { t } = useI18n();
  const errorMessage = useErrorMessage();
  const chat = useCopilotChat(regionId);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [chat.messages, chat.pending]);

  const waitingForFirstToken = chat.pending && chat.streamingId === null;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div
        ref={scrollRef}
        className="min-h-0 flex-1 overflow-y-auto px-4 py-4"
        aria-live="polite"
        aria-busy={chat.pending}
      >
        {chat.messages.length === 0 && !chat.pending ? (
          <CopilotWelcome regionLabel={regionLabel} onAsk={chat.send} />
        ) : null}

        <ul className="space-y-3">
          <AnimatePresence initial={false}>
            {chat.messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
          </AnimatePresence>
        </ul>

        {waitingForFirstToken ? <LoadingState label={t("copilot.thinking")} /> : null}
        {chat.error ? (
          <ErrorState message={errorMessage(chat.error, "copilot.failed")} onRetry={chat.retry} />
        ) : null}
      </div>

      <ChatInput disabled={chat.pending} onSend={chat.send} />
    </div>
  );
}
