export interface LocalFeature {
  id: string;
  geometry: GeoJSON.Geometry;
  properties: Record<string, any>;
}

export interface GraphNode {
  node_id: string;
  x_m: number;
  y_m: number;
  lon: number;
  lat: number;
}

export interface GraphEdge {
  edge_id: string;
  u: string;
  v: string;
  length_m: number;
  hierarchy: string;
  bike_allowed: boolean;
  walk_allowed: boolean;
}

export interface LoadedScenario {
  scenario: string;
  seed: number;
  spec: Record<string, any>;
  categories: any;
  boundary: LocalFeature;
  parcels: LocalFeature[];
  roads: LocalFeature[];
  buildings: LocalFeature[];
  facilities: LocalFeature[];
  transitStations: LocalFeature[];
  graphNodes: GraphNode[];
  graphEdges: GraphEdge[];
  wgs84: Record<string, any>;
}

function parseCsv(text: string): Record<string, string>[] {
  const [headerLine, ...lines] = text.trim().split(/\r?\n/);
  const headers = headerLine.split(",");
  return lines.filter(Boolean).map((line) => {
    const values = line.split(",");
    return Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""]));
  });
}

function parseGraphNodes(text: string): GraphNode[] {
  return parseCsv(text).map((row) => ({
    node_id: row.node_id,
    x_m: Number(row.x_m),
    y_m: Number(row.y_m),
    lon: Number(row.lon),
    lat: Number(row.lat)
  }));
}

function parseGraphEdges(text: string): GraphEdge[] {
  return parseCsv(text).map((row) => ({
    edge_id: row.edge_id,
    u: row.u,
    v: row.v,
    length_m: Number(row.length_m),
    hierarchy: row.hierarchy,
    bike_allowed: row.bike_allowed === "True" || row.bike_allowed === "true",
    walk_allowed: row.walk_allowed === "True" || row.walk_allowed === "true"
  }));
}

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to load ${url}: ${response.status}`);
  }
  return (await response.json()) as T;
}

async function getText(url: string): Promise<string> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to load ${url}: ${response.status}`);
  }
  return response.text();
}

async function loadScenarioFromPrefix(prefix: string, scenario: string): Promise<LoadedScenario> {
  const [
    boundary,
    parcels,
    roads,
    buildings,
    facilities,
    transitStations,
    graphNodesText,
    graphEdgesText,
    categories,
    cityState,
    boundaryWgs84,
    parcelsWgs84,
    roadsWgs84,
    buildingsWgs84,
    facilitiesWgs84,
    stationsWgs84
  ] = await Promise.all([
    getJson<LocalFeature>(`${prefix}/data_localxy/boundary_local.json`),
    getJson<LocalFeature[]>(`${prefix}/data_localxy/parcels_local.json`),
    getJson<LocalFeature[]>(`${prefix}/data_localxy/roads_local.json`),
    getJson<LocalFeature[]>(`${prefix}/data_localxy/buildings_local.json`),
    getJson<LocalFeature[]>(`${prefix}/data_localxy/facilities_local.json`),
    getJson<LocalFeature[]>(`${prefix}/data_localxy/transit_stations_local.json`),
    getText(`${prefix}/network/graph_nodes.csv`),
    getText(`${prefix}/network/graph_edges.csv`),
    getJson<any>(`${prefix}/metadata/categories.json`),
    getJson<any>(`${prefix}/metadata/city_state.json`),
    getJson<any>(`${prefix}/data_wgs84/boundary.geojson`),
    getJson<any>(`${prefix}/data_wgs84/parcels.geojson`),
    getJson<any>(`${prefix}/data_wgs84/roads.geojson`),
    getJson<any>(`${prefix}/data_wgs84/buildings.geojson`),
    getJson<any>(`${prefix}/data_wgs84/facilities.geojson`),
    getJson<any>(`${prefix}/data_wgs84/transit_stations.geojson`)
  ]);

  return {
    scenario,
    seed: cityState.seed,
    spec: cityState.spec,
    categories,
    boundary,
    parcels,
    roads,
    buildings,
    facilities,
    transitStations,
    graphNodes: parseGraphNodes(graphNodesText),
    graphEdges: parseGraphEdges(graphEdgesText),
    wgs84: {
      boundary: boundaryWgs84,
      parcels: parcelsWgs84,
      roads: roadsWgs84,
      buildings: buildingsWgs84,
      facilities: facilitiesWgs84,
      transitStations: stationsWgs84
    }
  };
}

function candidateBaseUrls(baseUrl: string): string[] {
  const candidates = [baseUrl, "/outputs", `${window.location.origin}/outputs`]
    .map((value) => value.replace(/\/$/, ""))
    .filter(Boolean);
  return Array.from(new Set(candidates));
}

export async function loadScenarioData(baseUrl: string, scenario: string): Promise<LoadedScenario> {
  const errors: string[] = [];
  for (const candidate of candidateBaseUrls(baseUrl)) {
    const prefix = `${candidate}/${scenario}`;
    try {
      return await loadScenarioFromPrefix(prefix, scenario);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      errors.push(`${candidate}: ${message}`);
    }
  }
  throw new Error(
    `Failed to fetch scenario '${scenario}'. Tried: ${errors.join(" | ")}. ` +
      `Generate outputs with 'python -m econode25.run_all --scenario ${scenario} --seed 42' if needed.`
  );
}
