import { useState } from "react";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useI18n } from "@/lib/i18n/context";

export function ChatInput({
  disabled,
  onSend,
}: {
  disabled: boolean;
  onSend: (question: string) => void;
}) {
  const { t } = useI18n();
  const [value, setValue] = useState("");

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSend(value);
        setValue("");
      }}
      className="flex items-center gap-2 border-t border-border p-3"
    >
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={t("copilot.placeholder")}
        aria-label={t("copilot.placeholder")}
        maxLength={500}
        className="min-w-0 flex-1 rounded-lg border border-input bg-background/60 px-3 py-2 text-sm text-foreground outline-none transition-shadow placeholder:text-muted-foreground focus:border-primary focus:shadow-glow"
      />
      <Button
        type="submit"
        variant="primary"
        size="icon"
        disabled={!value.trim() || disabled}
        aria-label={t("copilot.send")}
        className="transition-transform hover:scale-105 disabled:hover:scale-100"
      >
        <Send className="size-4" aria-hidden />
      </Button>
    </form>
  );
}
