export type Position = [number, number];

const METERS_PER_DEG_LAT = 110540;

export function localXYToLonLat(centerLat: number, centerLon: number, xMeters: number, yMeters: number): Position {
  const lonScale = 111320 * Math.max(Math.cos((centerLat * Math.PI) / 180), 1e-6);
  return [centerLon + xMeters / lonScale, centerLat + yMeters / METERS_PER_DEG_LAT];
}

export function lonLatToLocalXY(centerLat: number, centerLon: number, lon: number, lat: number): Position {
  const lonScale = 111320 * Math.max(Math.cos((centerLat * Math.PI) / 180), 1e-6);
  return [(lon - centerLon) * lonScale, (lat - centerLat) * METERS_PER_DEG_LAT];
}

export function projectGeometry(
  geometry: GeoJSON.Geometry,
  centerLat: number,
  centerLon: number
): GeoJSON.Geometry {
  if (geometry.type === "Point") {
    const [x, y] = geometry.coordinates as [number, number];
    return { type: "Point", coordinates: localXYToLonLat(centerLat, centerLon, x, y) };
  }
  if (geometry.type === "LineString") {
    return {
      type: "LineString",
      coordinates: geometry.coordinates.map(([x, y]) => localXYToLonLat(centerLat, centerLon, x, y))
    };
  }
  if (geometry.type === "Polygon") {
    return {
      type: "Polygon",
      coordinates: geometry.coordinates.map((ring) =>
        ring.map(([x, y]) => localXYToLonLat(centerLat, centerLon, x, y))
      )
    };
  }
  return geometry;
}
