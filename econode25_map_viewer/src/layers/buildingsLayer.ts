import { PolygonLayer } from "@deck.gl/layers";

import { getLandUseColor } from "../data/categories";

export function createBuildingsLayer(features: any[], categories: any) {
  return new PolygonLayer({
    id: "buildings-layer",
    data: features,
    pickable: true,
    extruded: true,
    wireframe: false,
    getPolygon: (feature: any) => feature.geometry.coordinates[0],
    getFillColor: (feature: any) => getLandUseColor(categories, feature.properties.landuse).map((value, index) => (index === 3 ? 210 : value)),
    getElevation: (feature: any) => feature.properties.height_m ?? 10,
    material: {
      ambient: 0.45,
      diffuse: 0.6,
      shininess: 28,
      specularColor: [255, 255, 255]
    }
  });
}
