import { QueryClient } from "@tanstack/react-query";
import { createRouter } from "@tanstack/react-router";
import { routeTree } from "@/routeTree.gen";
import { ApiError } from "@/api/client";

function shouldRetry(failureCount: number, error: Error): boolean {
  if (error instanceof ApiError && error.status !== undefined && error.status < 500) {
    return false;
  }
  return failureCount < 2;
}

export function createQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { refetchOnWindowFocus: false, retry: shouldRetry } },
  });
}

export function createAppRouter() {
  return createRouter({ routeTree, scrollRestoration: true, defaultPreloadStaleTime: 0 });
}

declare module "@tanstack/react-router" {
  interface Register {
    router: ReturnType<typeof createAppRouter>;
  }
}
