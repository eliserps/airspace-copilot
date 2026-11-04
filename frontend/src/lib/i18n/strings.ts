import { en } from "./locales/en";
import { pt } from "./locales/pt";

export type Locale = "en" | "pt";

export const STORAGE_KEY = "airspace-copilot:locale";

export const STRINGS: Record<Locale, Record<StringKey, string>> = { en, pt };

export type StringKey = keyof typeof en;
