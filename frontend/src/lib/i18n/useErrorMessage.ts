import { useCallback } from "react";
import { ApiError } from "@/api/client";
import { useI18n } from "./context";
import { en } from "./locales/en";
import type { StringKey } from "./strings";

function errorKey(code: string | undefined): StringKey | null {
  const key = `error.${code}`;
  return code && key in en ? (key as StringKey) : null;
}

export function useErrorMessage() {
  const { t } = useI18n();
  return useCallback(
    (error: unknown, fallback: StringKey): string => {
      if (!(error instanceof ApiError)) return t(fallback);
      const key = errorKey(error.code);
      if (key) return t(key, error.details);
      return error.message || t(fallback);
    },
    [t],
  );
}
