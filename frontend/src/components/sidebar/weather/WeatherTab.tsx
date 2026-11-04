import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ICAO, weatherQuery } from "@/api/weather";
import { EmptyState } from "@/components/ui/state/EmptyState";
import { ErrorState } from "@/components/ui/state/ErrorState";
import { SkeletonLines } from "@/components/ui/state/SkeletonLines";
import { useI18n } from "@/lib/i18n/context";
import { useErrorMessage } from "@/lib/i18n/useErrorMessage";
import { IcaoForm } from "./IcaoForm";
import { MetarReport } from "./MetarReport";

export function WeatherTab({ defaultIcao }: { defaultIcao: string }) {
  const { t, locale } = useI18n();
  const errorMessage = useErrorMessage();
  const [query, setQuery] = useState(defaultIcao);
  const [invalid, setInvalid] = useState(false);
  const q = useQuery(weatherQuery(query, locale));

  return (
    <div className="flex h-full min-h-0 flex-col">
      <IcaoForm
        defaultValue={defaultIcao}
        invalid={invalid}
        onInvalidChange={setInvalid}
        onSubmit={setQuery}
      />

      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        {invalid ? (
          <EmptyState label={t("weather.enterIcao")} hint={t("weather.invalidIcao")} />
        ) : !ICAO.test(query) ? (
          <EmptyState label={t("weather.enterIcao")} hint={t("weather.example")} />
        ) : q.isPending ? (
          <SkeletonLines rows={5} />
        ) : q.isError ? (
          <ErrorState
            message={errorMessage(q.error, "state.weatherUnavailable")}
            onRetry={() => void q.refetch()}
          />
        ) : !q.data.raw && !q.data.decoded ? (
          <EmptyState label={`${t("weather.noReport")} ${query}`} />
        ) : (
          <MetarReport raw={q.data.raw} decoded={q.data.decoded} />
        )}
      </div>
    </div>
  );
}
