export const metersToFeet = (m: number) => m * 3.280839895;
export const msToKnots = (ms: number) => ms * 1.943844492;

const nf = (v: number, locale?: string) =>
  Math.round(v).toLocaleString(locale === "pt" ? "pt-BR" : "en-US");

export function formatAltitude(altitude_m: number | null | undefined, locale?: string): string {
  if (altitude_m == null || Number.isNaN(altitude_m)) return "—";
  return `${nf(metersToFeet(altitude_m), locale)} ft`;
}

export function formatSpeed(velocity_ms: number | null | undefined, locale?: string): string {
  if (velocity_ms == null || Number.isNaN(velocity_ms)) return "—";
  return `${nf(msToKnots(velocity_ms), locale)} kt`;
}

export function formatHeading(heading_deg: number | null | undefined): string {
  if (heading_deg == null || Number.isNaN(heading_deg)) return "—";
  return `${Math.round(heading_deg)}°`;
}
