export function getTravelBinColor(categories: any, minutes: number | undefined): [number, number, number, number] {
  if (minutes === undefined || !Number.isFinite(minutes)) {
    return [220, 220, 220, 90];
  }
  const bin = categories.travel_time_bins.find((entry: any) => minutes <= entry.max_minutes);
  const color = (bin?.color ?? [220, 220, 220]) as [number, number, number];
  return [...color, 180];
}

export function getLandUseColor(categories: any, landuse: string): [number, number, number, number] {
  const color = categories.landuse?.[landuse]?.color ?? [210, 210, 210];
  return [...color, 120];
}
