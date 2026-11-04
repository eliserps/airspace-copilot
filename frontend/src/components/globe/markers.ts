export const PLANE_SVG = `<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2.2c.62 0 1.12.86 1.12 1.92v4.3l7.3 4.3c.36.2.58.6.58 1.03v1.1c0 .3-.3.5-.58.4l-7.3-2.3v3.9l2.3 1.8c.2.15.3.38.3.62v1c0 .27-.26.46-.5.36L12 19.4l-3.22 1.2c-.25.1-.5-.09-.5-.36v-1c0-.24.1-.47.3-.62l2.3-1.8v-3.9l-7.3 2.3c-.29.1-.58-.1-.58-.4v-1.1c0-.43.22-.83.58-1.03l7.3-4.3v-4.3c0-1.06.5-1.92 1.12-1.92Z"/></svg>`;

export function altitudeBand(altitudeM: number | null): "low" | "mid" | "high" {
  if (altitudeM === null || altitudeM < 3000) return "low";
  if (altitudeM < 9000) return "mid";
  return "high";
}

export function sampleSpread<T extends { latitude: number; longitude: number }>(
  items: T[],
  max: number,
  cellDeg = 5,
): T[] {
  if (items.length <= max) return items;
  const cells = new Map<string, T[]>();
  for (const item of items) {
    const key = `${Math.floor(item.latitude / cellDeg)}:${Math.floor(item.longitude / cellDeg)}`;
    const cell = cells.get(key);
    if (cell) cell.push(item);
    else cells.set(key, [item]);
  }
  const buckets = [...cells.values()];
  const sample: T[] = [];
  for (let round = 0; sample.length < max; round++) {
    let took = false;
    for (const bucket of buckets) {
      if (round < bucket.length) {
        sample.push(bucket[round]!);
        took = true;
        if (sample.length === max) break;
      }
    }
    if (!took) break;
  }
  return sample;
}
