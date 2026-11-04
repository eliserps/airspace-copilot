import { createContext, useContext } from "react";
import type { Locale, StringKey } from "./strings";

export type Vars = Record<string, string | number>;

export type I18nValue = {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: StringKey, vars?: Vars) => string;
};

export const I18nContext = createContext<I18nValue | null>(null);

export function useI18n(): I18nValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used inside I18nProvider");
  return ctx;
}
