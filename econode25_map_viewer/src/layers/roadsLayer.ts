import { PathLayer } from "@deck.gl/layers";

import { roadInnerColor, withAlpha } from "../utils/colors";

const widthScale: Record<string, number> = {
  ring_arterial: 12,
  radial_arterial: 9,
  local_connector: 4
};

export function createRoadLayers(features: any[], categories: any) {
  const outline = new PathLayer({
    id: "roads-outline",
    data: features,
    pickable: true,
    widthUnits: "pixels",
    getPath: (feature: any) => feature.geometry.coordinates,
    getColor: (feature: any) => {
      const base = categories.roads?.[feature.properties.hierarchy]?.color ?? [60, 80, 100];
      return withAlpha(base.map((value: number) => Math.max(value - 28, 0)), 255);
    },
    getWidth: (feature: any) => (widthScale[feature.properties.hierarchy] ?? 4) + 2
  });
  const inner = new PathLayer({
    id: "roads-inner",
    data: features,
    pickable: true,
    widthUnits: "pixels",
    getPath: (feature: any) => feature.geometry.coordinates,
    getColor: (feature: any) => {
      const base = categories.roads?.[feature.properties.hierarchy]?.color ?? [80, 100, 120];
      return roadInnerColor(base);
    },
    getWidth: (feature: any) => widthScale[feature.properties.hierarchy] ?? 4
  });
  return [outline, inner];
}
