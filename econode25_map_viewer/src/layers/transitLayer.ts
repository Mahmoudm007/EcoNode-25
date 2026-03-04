import { ScatterplotLayer } from "@deck.gl/layers";

export function createTransitLayer(features: any[], categories: any) {
  return new ScatterplotLayer({
    id: "transit-layer",
    data: features,
    pickable: true,
    stroked: true,
    filled: true,
    radiusUnits: "pixels",
    lineWidthMinPixels: 1,
    getPosition: (feature: any) => feature.geometry.coordinates,
    getRadius: (feature: any) => (feature.properties.station_type === "central_station" ? 12 : 8),
    getFillColor: (feature: any) => {
      const color = categories.transit?.[feature.properties.station_type]?.color ?? [29, 53, 87];
      return [...color, 220];
    },
    getLineColor: [255, 255, 255, 220]
  });
}
