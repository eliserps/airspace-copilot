import { queryOptions } from "@tanstack/react-query";
import { http, unwrap, type Lang } from "@/api/client";

export const ICAO = /^[A-Z0-9]{4}$/;

export function weatherQuery(icao: string, lang: Lang) {
  return queryOptions({
    queryKey: ["weather", icao, lang] as const,
    queryFn: ({ signal }) =>
      unwrap(http.GET("/weather/{icao}", { params: { path: { icao }, query: { lang } }, signal })),
    enabled: ICAO.test(icao),
    staleTime: 15 * 60_000,
  });
}
