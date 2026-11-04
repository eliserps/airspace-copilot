import { QueryClientProvider, type QueryClient } from "@tanstack/react-query";
import { RouterProvider } from "@tanstack/react-router";
import { I18nProvider } from "@/lib/i18n/provider";
import type { Locale } from "@/lib/i18n/strings";
import type { createAppRouter } from "./router";

export function App({
  router,
  queryClient,
  locale,
}: {
  router: ReturnType<typeof createAppRouter>;
  queryClient: QueryClient;
  locale?: Locale;
}) {
  return (
    <QueryClientProvider client={queryClient}>
      <I18nProvider {...(locale ? { initialLocale: locale } : {})}>
        <RouterProvider router={router} />
      </I18nProvider>
    </QueryClientProvider>
  );
}
