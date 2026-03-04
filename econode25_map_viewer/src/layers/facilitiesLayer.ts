import { IconLayer } from "@deck.gl/layers";

import { iconUrlFor } from "../utils/icons";

export function createFacilitiesLayer(features: any[]) {
  return new IconLayer({
    id: "facilities-layer",
    data: features,
    pickable: true,
    sizeUnits: "pixels",
    getPosition: (feature: any) => feature.geometry.coordinates,
    getSize: 26,
    getIcon: (feature: any) => ({
      url: iconUrlFor(feature.properties.facility_type),
      width: 64,
      height: 64,
      anchorY: 32
    })
  });
}
