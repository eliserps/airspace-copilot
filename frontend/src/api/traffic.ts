import { keepPreviousData, queryOptions, useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import type { RegionId } from "@/config";
import { http, unwrap } from "@/api/client";

export const trafficKeys = {
  all: ["aircraft"] as const,
  map: (region: RegionId) => [...trafficKeys.all, "map", region] as const,
};

export function aircraftMapQuery(region: RegionId, live: boolean) {
  return queryOptions({
    queryKey: trafficKeys.map(region),
    queryFn: ({ signal }) =>
      unwrap(http.GET("/aircraft/map", { params: { query: { region } }, signal })),
    refetchInterval: live ? 60_000 : false,
    staleTime: 45_000,
    placeholderData: keepPreviousData,
  });
}

export function useTraffic(region: RegionId, live: boolean) {
  const query = useQuery(aircraftMapQuery(region, live));
  const aircraft = useMemo(() => query.data?.aircraft ?? [], [query.data]);
  const stale = query.data?.stale === true || (query.isError && aircraft.length > 0);
  return { query, aircraft, stale };
}

export type Traffic = ReturnType<typeof useTraffic>;
