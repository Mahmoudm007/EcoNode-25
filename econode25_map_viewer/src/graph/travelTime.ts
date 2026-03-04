import type { LocalFeature, GraphNode } from "../data/loader";
import { KdTree } from "../data/kdTree";
import { buildAdjacency, type AdjacencyMap } from "./adjacency";
import { dijkstra } from "./dijkstra";

export interface TravelTimes {
  walk: Record<string, number>;
  bike: Record<string, number>;
}

export function buildNodeIndex(nodes: GraphNode[]): Record<string, GraphNode> {
  return Object.fromEntries(nodes.map((node) => [node.node_id, node]));
}

export function createSnapTree(nodes: GraphNode[]): KdTree {
  return new KdTree(nodes.map((node) => ({ id: node.node_id, x: node.x_m, y: node.y_m })));
}

export function computeTravelTimes(
  adjacency: AdjacencyMap,
  originNodeId: string,
  walkSpeedMps: number,
  bikeSpeedMps: number
): TravelTimes {
  return {
    walk: dijkstra(adjacency, originNodeId, (_from, _to, edge) =>
      edge.walk_allowed ? edge.length_m / walkSpeedMps / 60 : undefined
    ),
    bike: dijkstra(adjacency, originNodeId, (_from, _to, edge) =>
      edge.bike_allowed ? edge.length_m / bikeSpeedMps / 60 : undefined
    )
  };
}

export function snapFeatureToNode(feature: LocalFeature, snapTree: KdTree): string | undefined {
  if (feature.geometry.type !== "Point") {
    return undefined;
  }
  const [x, y] = feature.geometry.coordinates as [number, number];
  return snapTree.nearest(x, y)?.id;
}

export function parcelCentroid(geometry: GeoJSON.Geometry): [number, number] {
  if (geometry.type !== "Polygon") {
    return [0, 0];
  }
  const ring = geometry.coordinates[0] as [number, number][];
  let area2 = 0;
  let cx = 0;
  let cy = 0;
  for (let index = 0; index < ring.length - 1; index += 1) {
    const [x1, y1] = ring[index];
    const [x2, y2] = ring[index + 1];
    const cross = x1 * y2 - x2 * y1;
    area2 += cross;
    cx += (x1 + x2) * cross;
    cy += (y1 + y2) * cross;
  }
  const area = area2 / 2;
  if (!area) {
    return ring[0] ?? [0, 0];
  }
  return [cx / (6 * area), cy / (6 * area)];
}

export function snapParcelToNode(parcel: LocalFeature, snapTree: KdTree): string | undefined {
  const [x, y] = parcelCentroid(parcel.geometry);
  return snapTree.nearest(x, y)?.id;
}

export function makeAdjacency(nodes: GraphNode[], edges: any[]) {
  return buildAdjacency(nodes, edges);
}
