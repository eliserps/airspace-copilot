import { motion } from "motion/react";
import { ShieldAlert } from "lucide-react";
import { Markdown } from "@/components/ui/Markdown";
import { useI18n } from "@/lib/i18n/context";
import type { ChatMessage as Message } from "./useCopilotChat";

export function ChatMessage({ message }: { message: Message }) {
  const { t } = useI18n();
  return (
    <motion.li
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22, ease: "easeOut" }}
      className={message.role === "user" ? "flex justify-end" : "flex justify-start"}
    >
      {message.role === "user" ? (
        <p className="max-w-[85%] rounded-2xl rounded-br-sm bg-primary px-3.5 py-2 text-sm font-medium text-primary-foreground">
          {message.text}
        </p>
      ) : (
        <div className="max-w-[92%] rounded-2xl rounded-bl-sm border border-border bg-surface/70 px-3.5 py-2.5">
          {message.flagged ? (
            <span className="mb-2 inline-flex items-center gap-1.5 rounded-full border border-warning/40 bg-warning/10 px-2 py-0.5 text-[11px] font-medium text-warning">
              <ShieldAlert className="size-3" aria-hidden /> {t("copilot.flagged")}
            </span>
          ) : null}
          <Markdown>{message.text}</Markdown>
        </div>
      )}
    </motion.li>
  );
}
