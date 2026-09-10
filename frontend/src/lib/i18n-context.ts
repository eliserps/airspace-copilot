import { createContext, useContext } from "react";
import type { Locale, StringKey } from "./i18n-strings";

export type I18nValue = {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: StringKey) => string;
};

export const I18nContext = createContext<I18nValue | null>(null);

export function useI18n(): I18nValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used inside I18nProvider");
  return ctx;
}
