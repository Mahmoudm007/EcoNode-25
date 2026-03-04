import type { GraphEdge, GraphNode } from "../data/loader";

export interface AdjacencyEdge {
  to: string;
  length_m: number;
  hierarchy: string;
  bike_allowed: boolean;
  walk_allowed: boolean;
}

export type AdjacencyMap = Record<string, AdjacencyEdge[]>;

export function buildAdjacency(_nodes: GraphNode[], edges: GraphEdge[]): AdjacencyMap {
  const adjacency: AdjacencyMap = {};
  for (const edge of edges) {
    adjacency[edge.u] ??= [];
    adjacency[edge.v] ??= [];
    adjacency[edge.u].push({
      to: edge.v,
      length_m: edge.length_m,
      hierarchy: edge.hierarchy,
      bike_allowed: edge.bike_allowed,
      walk_allowed: edge.walk_allowed
    });
    adjacency[edge.v].push({
      to: edge.u,
      length_m: edge.length_m,
      hierarchy: edge.hierarchy,
      bike_allowed: edge.bike_allowed,
      walk_allowed: edge.walk_allowed
    });
  }
  return adjacency;
}
