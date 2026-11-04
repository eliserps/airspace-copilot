import { queryOptions } from "@tanstack/react-query";
import type { RegionId } from "@/config";
import { http, unwrap, type Lang } from "@/api/client";

export function briefingQuery(region: RegionId, lang: Lang) {
  return queryOptions({
    queryKey: ["briefing", region, lang] as const,
    queryFn: ({ signal }) =>
      unwrap(http.GET("/briefing", { params: { query: { region, lang } }, signal })),
    staleTime: 5 * 60_000,
  });
}
