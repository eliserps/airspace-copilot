import { CloudSun, FileText, MessageSquare, Plane } from "lucide-react";
import type { TabItem } from "@/components/ui/Tabs";

export const TAB_IDS = ["copilot", "traffic", "briefing", "weather"] as const;
export type TabId = (typeof TAB_IDS)[number];

export const TABS: Omit<TabItem<TabId>, "label">[] = [
  { id: "copilot", icon: MessageSquare, tone: "text-violet" },
  { id: "traffic", icon: Plane, tone: "text-orange" },
  { id: "briefing", icon: FileText, tone: "text-yellow" },
  { id: "weather", icon: CloudSun, tone: "text-primary" },
];
