import { motion } from "motion/react";
import { useRef, type KeyboardEvent, type ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/cn";

export type TabItem<T extends string> = {
  id: T;
  label: string;
  icon: LucideIcon;
  tone: string;
};

function tabId(id: string) {
  return `tab-${id}`;
}

function panelId(id: string) {
  return `panel-${id}`;
}

export function TabList<T extends string>({
  items,
  active,
  onChange,
  label,
}: {
  items: TabItem<T>[];
  active: T;
  onChange: (id: T) => void;
  label: string;
}) {
  const refs = useRef<(HTMLButtonElement | null)[]>([]);

  function onKeyDown(event: KeyboardEvent, index: number) {
    const last = items.length - 1;
    const next =
      event.key === "ArrowRight"
        ? index === last
          ? 0
          : index + 1
        : event.key === "ArrowLeft"
          ? index === 0
            ? last
            : index - 1
          : event.key === "Home"
            ? 0
            : event.key === "End"
              ? last
              : null;
    if (next === null) return;
    event.preventDefault();
    onChange(items[next]!.id);
    refs.current[next]?.focus();
  }

  return (
    <div
      role="tablist"
      aria-label={label}
      className="flex items-center gap-1 border-b border-border p-2"
    >
      {items.map((item, index) => {
        const Icon = item.icon;
        const selected = item.id === active;
        return (
          <button
            key={item.id}
            ref={(el) => {
              refs.current[index] = el;
            }}
            role="tab"
            id={tabId(item.id)}
            aria-selected={selected}
            aria-controls={panelId(item.id)}
            tabIndex={selected ? 0 : -1}
            onClick={() => onChange(item.id)}
            onKeyDown={(e) => onKeyDown(e, index)}
            className="relative flex flex-1 items-center justify-center gap-1.5 rounded-lg px-2 py-2 text-xs font-medium outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {selected ? (
              <motion.span
                layoutId="tab-pill"
                className="absolute inset-0 rounded-lg bg-secondary"
                transition={{ type: "spring", stiffness: 420, damping: 34 }}
              />
            ) : null}
            <Icon
              className={cn("relative size-3.5", selected ? item.tone : "text-muted-foreground")}
            />
            <span
              className={cn(
                "relative hidden sm:inline",
                selected ? "text-foreground" : "text-muted-foreground",
              )}
            >
              {item.label}
            </span>
          </button>
        );
      })}
    </div>
  );
}

export function TabPanel({
  id,
  active,
  keepMounted = false,
  children,
}: {
  id: string;
  active: boolean;
  keepMounted?: boolean;
  children: ReactNode;
}) {
  if (!active && !keepMounted) return null;
  return (
    <div
      role="tabpanel"
      id={panelId(id)}
      aria-labelledby={tabId(id)}
      hidden={!active}
      className="h-full min-h-0"
    >
      {children}
    </div>
  );
}
