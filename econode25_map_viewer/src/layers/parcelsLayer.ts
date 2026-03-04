import { PolygonLayer } from "@deck.gl/layers";

import { getLandUseColor, getTravelBinColor } from "../data/categories";

interface ParcelLayerArgs {
  features: any[];
  categories: any;
  displayMode: "landuse" | "travel";
  travelMinutesByParcel: Record<string, number>;
}

export function createParcelsLayer({ features, categories, displayMode, travelMinutesByParcel }: ParcelLayerArgs) {
  return new PolygonLayer({
    id: "parcels-layer",
    data: features,
    pickable: true,
    stroked: true,
    filled: true,
    wireframe: false,
    getPolygon: (feature: any) => feature.geometry.coordinates[0],
    getLineColor: [245, 247, 250, 80],
    getLineWidth: 1,
    lineWidthMinPixels: 1,
    getFillColor: (feature: any) => {
      if (displayMode === "travel") {
        return getTravelBinColor(categories, travelMinutesByParcel[feature.id]);
      }
      return getLandUseColor(categories, feature.properties.landuse);
    },
    updateTriggers: {
      getFillColor: [displayMode, travelMinutesByParcel]
    }
  });
}
